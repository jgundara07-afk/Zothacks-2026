import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .database import Catalog
from .enrich import enrich
from .http import public_url
from .sources import anteater, coursera, muse, zotspot, eventbrite, irvine
from .relevance import inclusion


class Response:
    def __init__(self, data=None, text=""):
        self.data, self.text = data, text
        self.content = text.encode()

    def json(self):
        return self.data


class FakeFetcher:
    def __init__(self, responses):
        self.responses, self.urls = iter(responses), []

    def get(self, source, url, params=None, headers=None):
        self.urls.append((url, params))
        return next(self.responses), {"collected_at": "2026-10-17T00:00:00+00:00", "url": url}


class PipelineTests(unittest.TestCase):
    def test_requested_catalog_focus_excludes_uci_and_generic_courses(self):
        self.assertFalse(inclusion({'source':'anteater','kind':'Class','title':'Python programming'})[0])
        self.assertFalse(inclusion({'source':'coursera','kind':'Online course','title':'History of Medicine','description':'Improve your career, communication, and personal growth.'})[0])
        for title in ('Build websites with HTML5 and CSS3','Fundamentals of Investing','Python for Beginners'):
            self.assertTrue(inclusion({'source':'coursera','kind':'Online course','title':title})[0],title)

    def test_catalog_storage_excludes_unrelated_and_prunes_to_published_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            catalog = Catalog(Path(directory) / 'curated.sqlite3')
            facts = {"source": "test", "source_id": "1", "source_url": "https://example.org/1",
                     "kind": "Class", "title": "Python programming", "provenance": {"collected_at": "2026-10-17T00:00:00+00:00"}}
            first = enrich(facts)
            self.assertTrue(catalog.put(first))
            self.assertTrue(catalog.put(enrich({**facts, 'source_id':'2', 'source_url':'https://example.org/2'})))
            self.assertFalse(catalog.put(enrich({**facts, 'source_id':'3', 'source_url':'https://example.org/3', 'kind':'Job', 'title':'Physician'})))
            with self.assertRaises(ValueError):
                catalog.retain_ids([])
            with self.assertRaises(ValueError):
                catalog.retain_ids(['missing'])
            self.assertEqual(catalog.stats(),{'test':2})
            self.assertEqual(catalog.retain_ids([first['id']]),1)
            self.assertEqual(catalog.stats(),{'test':1})
            catalog.close()

    def test_relevance_curation_keeps_personal_benefit_and_rejects_unrelated_roles(self):
        self.assertEqual(inclusion({"kind": "Park", "title": "Quiet neighborhood green space"}),
                         (True, "personal_wellbeing_or_recreation"))
        self.assertFalse(inclusion({"kind": "Job", "title": "Family Medicine Physician", "description": "Patient care", "personalization": {"interests": ["Career Development"]}})[0])
        self.assertFalse(inclusion({"kind": "Job", "title": "Family Medicine Physician", "description": "Build software for clinics", "personalization": {"interests": ["Software Engineering"]}})[0])
        self.assertFalse(inclusion({"kind": "Class", "title": "20th Century Music", "description": "Music history", "personalization": {"interests": ["Productivity & Personal Growth"]}})[0])
        self.assertTrue(inclusion({"kind": "Internship", "title": "Machine Learning Engineer Intern", "description": "Build machine learning models"})[0])
        self.assertTrue(inclusion({"kind": "Campus event", "title": "Student club community garden shift"})[0])

    def test_irvine_places_exclude_parking_and_keep_source_geometry(self):
        fetcher = FakeFetcher([
            Response({"objectIds": [1]}), Response({"features": [{"attributes": {"OBJECTID": 1, "STREETNAME": "Test Trail", "MILES": 0.5}, "geometry": {"paths": [[[-117.8, 33.7], [-117.81, 33.71]]]}}]}),
            Response({"objectIds": [1, 2]}), Response({"features": [{"attributes": {"OBJECTID": 1, "Type": "Parking Lot", "FullName": "Parking"}}, {"attributes": {"OBJECTID": 2, "Type": "Soccer", "FullName": "Soccer 1"}}]}),
            Response({"objectIds": [1]}), Response({"features": [{"attributes": {"OBJECTID": 1, "NAME": "Test Park", "TRAIL": 1, "TENNIS": 1}}]}),
        ])
        rows = list(irvine(fetcher, 5))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["kind"], "Trail")
        self.assertAlmostEqual(rows[0]["coordinates"]["latitude"], 33.705)
        self.assertIn("TENNIS", rows[2]["amenities"])
        self.assertEqual(fetcher.urls[0][1]["where"], "CL=95")

    def test_course_pagination_estimates_and_persistence(self):
        fetcher = FakeFetcher([
            Response({"ok": True, "data": {"items": [{"id": "ICS1", "title": "Python", "courseLevel": "Lower Division"}], "nextCursor": "ICS1"}}),
            Response({"ok": True, "data": {"items": [], "nextCursor": None}}),
        ])
        facts = list(anteater(fetcher, 3))
        self.assertEqual(fetcher.urls[1][1]["cursor"], "ICS1")
        row = enrich(facts[0])
        self.assertIn("Coding", row["editorial"]["inferred_skills"])
        self.assertTrue(row["editorial"]["difficulty_is_estimate"])
        self.assertIsNone(row["duration"]["total_minutes"])
        # Anteater parsing remains testable, but UCI records are intentionally
        # excluded from active storage. Use a neutral fixture for deduplication.
        row = enrich({**facts[0], "source": "test"})
        with tempfile.TemporaryDirectory() as directory:
            catalog = Catalog(Path(directory) / "catalog.sqlite3")
            catalog.put(row)
            catalog.put(row)
            # Another upstream ID with the same canonical URL still counts once.
            catalog.put(enrich({**facts[0], "source": "test", "source_id": "alias"}))
            self.assertEqual(catalog.stats(), {"test": 1})
            output = Path(directory) / "catalog.json"
            catalog.export(output)
            self.assertEqual(len(json.loads(output.read_text())["opportunities"]), 1)
            catalog.close()

    def test_coursera_cursor_and_workload(self):
        fetcher = FakeFetcher([
            Response({"elements": [{"id": "one", "slug": "python", "name": "Python", "workload": "3 weeks"}], "paging": {"next": "1000"}}),
            Response({"elements": [], "paging": {}}),
        ])
        rows = list(coursera(fetcher, 3))
        self.assertEqual(fetcher.urls[1][1]["start"], "1000")
        self.assertEqual(enrich(rows[0])["duration"]["source_workload_text"], "3 weeks")

    def test_muse_keeps_actual_level_and_location(self):
        fetcher = FakeFetcher([Response({"results": [{"id": 1, "name": "Intern", "refs": {"landing_page": "https://example.org/job"}, "levels": [{"name": "Internship"}], "locations": [{"name": "Remote"}], "contents": "<p>Python</p>"}], "page_count": 1})])
        with patch.dict("os.environ", {"MUSE_CATEGORIES": "Software Engineering"}):
            row = list(muse(fetcher, 2))[0]
        self.assertEqual(row["kind"], "Internship")
        self.assertEqual(row["mode"], "Online")
        self.assertEqual(row["description"], "Python")

    def test_zotspot_uses_advertised_calendar_not_blocked_endpoint(self):
        calendar = "\r\n".join([
            "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:OneThing test", "BEGIN:VEVENT",
            "UID:test1", "SUMMARY:Career Workshop", "DTSTART:20261020T120000Z",
            "DTEND:20261020T130000Z", "URL:https://zotspot.uci.edu/rsvp?id=1",
            "DESCRIPTION:Prepare a question", "END:VEVENT", "END:VCALENDAR", ""])
        fetcher = FakeFetcher([
            Response(text="User-agent: *\nDisallow: /mobile_ws/v17/"),
            Response(text='<script>return "https://zotspot.uci.edu/ical/uci/ical_uci.ics";</script>'),
            Response(text=calendar),
        ])
        with patch.dict("os.environ", {"ZOTSPOT_DETAIL_URLS": ""}):
            rows = list(zotspot(fetcher, 10))
        self.assertEqual(rows[0]["title"], "Career Workshop")
        self.assertTrue(all("mobile_ws" not in url for url, _ in fetcher.urls))

    def test_eventbrite_requires_credentials_and_filters_private_events(self):
        with patch.dict("os.environ", {"EVENTBRITE_TOKEN": "", "EVENTBRITE_EVENT_IDS": "", "EVENTBRITE_ORGANIZATION_IDS": ""}):
            with self.assertRaisesRegex(RuntimeError, "Not configured"):
                list(eventbrite(FakeFetcher([]), 1))
        fetcher = FakeFetcher([Response({"id": "1", "listed": False, "status": "live"})])
        with patch.dict("os.environ", {"EVENTBRITE_TOKEN": "test", "EVENTBRITE_EVENT_IDS": "1", "EVENTBRITE_ORGANIZATION_IDS": ""}):
            self.assertEqual(list(eventbrite(fetcher, 1)), [])

    def test_secrets_removed_from_receipt_urls(self):
        self.assertEqual(public_url("https://example.org?api_key=secret&page=2&token=secret"), "https://example.org?page=2")

    def test_event_duration_and_invalid_editorial_override(self):
        facts = {"source": "zotspot", "source_id": "1", "source_url": "https://example.org/event",
                 "title": "Networking", "kind": "Campus event", "start": "2026-10-01T12:00:00+00:00",
                 "end": "2026-10-01T13:30:00+00:00", "provenance": {"collected_at": "2026-10-17T12:00:00+00:00"}}
        row = enrich(facts)
        self.assertEqual(row["duration"]["total_minutes"], 90)
        self.assertEqual(row["event_timing_at_collection"], "past")
        self.assertEqual(row["editorial"]["first_step_minutes"], 5)
        with self.assertRaisesRegex(ValueError, "difficulty"):
            enrich(facts, {row["id"]: {"reason": "test", "difficulty": "impossible"}})

    def test_eventbrite_discovers_organizations_and_keeps_public_events(self):
        fetcher = FakeFetcher([
            Response({"organizations": [{"id": "42"}], "pagination": {"has_more_items": False}}),
            Response({"events": [{"id": "1", "listed": True, "status": "live", "name": {"text": "Networking"}, "url": "https://example.org/event"}], "pagination": {"has_more_items": False}}),
        ])
        with patch.dict("os.environ", {"EVENTBRITE_TOKEN": "test", "EVENTBRITE_EVENT_IDS": "", "EVENTBRITE_ORGANIZATION_IDS": ""}):
            rows = list(eventbrite(fetcher, 2))
        self.assertEqual(len(rows), 1)
        self.assertIn("organizations/42/events", fetcher.urls[1][0])

    def test_muse_does_not_request_page_100(self):
        result = {"id": 1, "name": "Intern", "refs": {"landing_page": "https://example.org/job"}}
        fetcher = FakeFetcher([Response({"results": [result], "page_count": 999}) for _ in range(100)])
        with patch.dict("os.environ", {"MUSE_CATEGORIES": "Software Engineering"}):
            with self.assertRaisesRegex(RuntimeError, "pagination cap"):
                list(muse(fetcher, 101))
        self.assertEqual(max(params["page"] for _, params in fetcher.urls), 99)


if __name__ == "__main__":
    unittest.main()
