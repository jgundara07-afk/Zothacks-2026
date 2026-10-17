import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from backend.catalog_reader import CatalogReader, load_catalog
from opportunity_data.database import Catalog
from opportunity_data.enrich import enrich
from opportunity_data.export_app import project, publish, validate
from opportunity_data.personalize import TAXONOMY, bucket
from datetime import datetime, timezone


def example(**changes):
    facts = {"source": "coursera", "source_id": "python", "source_url": "https://example.org/python",
             "title": "Python web development", "description": "Build a project using Flask and machine learning.",
             "organization": "Example", "kind": "Online course", "mode": "Online",
             "provenance": {"collected_at": "2026-10-17T00:00:00+00:00"}, **changes}
    return project(enrich(facts), datetime(2026, 10, 17, tzinfo=timezone.utc))


class PersonalizationTests(unittest.TestCase):
    def test_exact_checklist_and_evidence(self):
        row = example()
        validate(row)
        p = row["personalization"]
        self.assertIn("Web & App Development", p["interests"])
        self.assertIn("AI & Machine Learning", p["interests"])
        self.assertIn("Build a strong project portfolio", p["goals"])
        self.assertEqual(p["location_preferences"], ["Online / Remote"])
        self.assertNotIn("Near me", p["location_preferences"])
        self.assertEqual(p["micro_step"]["time_bucket"], "Under 5 min")

    def test_unrelated_subject_is_not_invented_as_technical(self):
        row = example(title="Ancient Greek poetry", description="A study of classical poetry.")
        self.assertEqual(row["personalization"]["interests"], ["Productivity & Personal Growth"])
        self.assertEqual(row["personalization"]["goals"], [])
        self.assertTrue(row["personalization"]["classification"]["fallback"])

    def test_ai_abbreviation_and_job_club_false_positive(self):
        ai = example(title="Ethical AI with Gemini", description="A guided exercise.")
        self.assertIn("AI & Machine Learning", ai["personalization"]["interests"])
        french = example(title="Poésie", description="J'ai lu ce texte.")
        self.assertNotIn("AI & Machine Learning", french["personalization"]["interests"])
        job = example(source="muse", kind="Job", title="Software engineer", description="Build software at a shopping club.")
        self.assertNotIn("Join a technical club or organization", job["goals"])

    def test_unknown_or_off_campus_event_is_not_tagged_on_campus(self):
        event = example(source="zotspot", kind="Campus event", mode=None,
                        location="Private Location (sign in to display)", title="Restoration day", description="Hosted by UC Irvine.")
        self.assertNotIn("On campus", event["personalization"]["location_preferences"])
        self.assertNotIn("In-person events", event["personalization"]["location_preferences"])
        event = example(source="eventbrite", kind="Networking event", mode="Local", location="UCI Student Center")
        self.assertIn("On campus", event["personalization"]["location_preferences"])
        self.assertIn("In-person events", event["personalization"]["location_preferences"])

    def test_time_boundaries_and_real_workload(self):
        self.assertEqual([bucket(n) for n in (2, 5, 15, 30, 60, 180, 1440)], TAXONOMY["time_buckets"])
        row = example(workload="1 hour 30 minutes")
        self.assertEqual(row["personalization"]["duration"]["minutes"], 90)
        self.assertFalse(row["personalization"]["duration"]["estimated"])

    def test_scope_filters_do_not_confuse_course_and_micro_step(self):
        reader = CatalogReader([example()], TAXONOMY)
        self.assertEqual(reader.query(time_buckets=["Under 5 min"])["total"], 0)
        result = reader.query(time_buckets=["Under 5 min"], challenge_levels=["Lazy"], scope="micro_step")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["opportunities"][0]["match"]["scope"], "micro_step")
        self.assertEqual(reader.query(commitment="A mix of both")["total"], 1)

    def test_and_between_groups_or_within_group_and_pagination(self):
        reader = CatalogReader([example(), example(source_id="other", title="Basketball", description="Sports practice")], TAXONOMY)
        self.assertEqual(reader.query(interests=["Software Engineering", "Sports"])["total"], 2)
        self.assertEqual(reader.query(interests=["Sports"], goals=["Build a strong project portfolio"])["total"], 0)
        self.assertEqual(len(reader.query(offset=1, limit=1)["opportunities"]), 1)
        self.assertEqual(reader.query(q="Python Flask")["total"], 1)

    def test_nearby_uses_coordinates_and_unknown_does_not_match(self):
        row = example(source="irvine", kind="Trail", title="A trail", description="Mapped trail", mode="Local",
                      coordinates={"latitude": 33.7, "longitude": -117.8})
        reader = CatalogReader([row, example()], TAXONOMY)
        with self.assertRaisesRegex(ValueError, "requires"):
            reader.query(locations=["Near me"])
        self.assertEqual(reader.query(locations=["Near me"], lat=33.7, lon=-117.8, radius_km=1)["total"], 1)
        self.assertEqual(reader.query(locations=["Near me"], lat=0, lon=0, radius_km=1)["total"], 0)
        with self.assertRaises(ValueError):
            reader.query(lat=float("nan"), lon=0)

    def test_past_events_and_goal_limit(self):
        row = example(kind="Campus event", start="2026-10-01T12:00:00+00:00", end="2026-10-01T13:00:00+00:00")
        reader = CatalogReader([row], TAXONOMY)
        self.assertEqual(reader.query()["total"], 0)
        self.assertEqual(reader.query(include_past=True)["total"], 1)
        with self.assertRaisesRegex(ValueError, "up to 3"):
            reader.query(goals=TAXONOMY["goals"][:4])
        with self.assertRaisesRegex(ValueError, "Unknown"):
            reader.query(challenge_levels=["Impossible"])

    def test_portable_export_readback_checksum_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = Catalog(root / "test.sqlite3")
            catalog.put(enrich({"source": "test", "source_id": "1", "source_url": "https://example.org/1",
                                "title": "Python", "kind": "Online course", "provenance": {"collected_at": "2026-10-17T00:00:00+00:00"}}))
            catalog.close()
            manifest = publish(root / "test.sqlite3", root / "app")
            data = root / "app" / "opportunities.json.gz"
            self.assertEqual(hashlib.sha256(data.read_bytes()).hexdigest(), manifest["sha256"])
            with gzip.open(data, "rt", encoding="utf-8") as stream:
                self.assertEqual(len(json.load(stream)["opportunities"]), 1)
            self.assertEqual(load_catalog(root / "app").query()["total"], 1)
            # Cached reader must not retain a handle that prevents Windows cleanup.
            data.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "checksum"):
                load_catalog(root / "app")

    def test_flask_catalog_contract_and_invalid_filters(self):
        from unittest.mock import patch
        from backend.app import create_app, Store
        reader = CatalogReader([example()], TAXONOMY)
        with tempfile.TemporaryDirectory() as directory, patch("backend.catalog_routes.load_catalog", return_value=reader):
            client = create_app(Store(path=str(Path(directory) / "demo.sqlite3"))).test_client()
            self.assertEqual(client.get("/catalog/options").json["max_selected_goals"], 3)
            response = client.get("/catalog/opportunities", query_string={"scope": "micro_step", "challenge_levels": "Lazy"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["total"], 1)
            self.assertEqual(client.get("/catalog/opportunities?challenge_level=Lazy").status_code, 400)
            self.assertEqual(client.get("/catalog/opportunities?limit=0").status_code, 400)
            self.assertEqual(client.get("/catalog/opportunities?locations=Near%20me").status_code, 400)
            self.assertEqual(client.get("/catalog/opportunities?include_past=maybe").status_code, 400)


if __name__ == "__main__":
    unittest.main()
