"""Five source adapters. Iterators yield facts and provenance; no scheduling."""
import json
import os
import re
from collections import deque
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs, quote
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup
from icalendar import Calendar

from .http import USER_AGENT


def plain(value):
    return BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)


def record(source, source_id, title, url, kind, receipt, **facts):
    return {"source": source, "source_id": str(source_id), "title": plain(title),
            "source_url": url, "kind": kind, "provenance": receipt, **facts}


def anteater(fetcher, max_pages):
    cursor = None
    seen = set()
    for _ in range(max_pages):
        params = {"take": 100}
        if cursor:
            params["cursor"] = cursor
        headers = {"Authorization": f"Bearer {os.environ['ANTEATER_API_KEY']}"} if os.getenv("ANTEATER_API_KEY") else None
        response, receipt = fetcher.get("anteater", "https://anteaterapi.com/v2/rest/coursesCursor", params, headers)
        payload = response.json()
        if not payload.get("ok"):
            raise ValueError("Anteater returned ok=false")
        data = payload["data"]
        for row in data["items"]:
            yield record("anteater", row["id"], row["title"],
                         "https://anteaterapi.com/v2/rest/courses/" + quote(row["id"], safe=""),
                         "Class", receipt, organization="University of California, Irvine",
                         description=row.get("description", ""), location="UC Irvine",
                         mode=None, course_level=row.get("courseLevel"),
                         units={"min": row.get("minUnits"), "max": row.get("maxUnits")},
                         prerequisites=row.get("prerequisiteText"), restrictions=row.get("restriction"),
                         department=row.get("departmentName"), terms=row.get("terms", []),
                         availability="Catalog entry; current enrollment and schedule not checked",
                         attribution="Data from Anteater API (ICSSC): https://icssc.link/about-anteaterapi")
        cursor = data.get("nextCursor")
        if not cursor or cursor in seen:
            return
        seen.add(cursor)
    raise RuntimeError("Anteater page budget reached; collected records retained")


def muse(fetcher, max_pages):
    categories = [s.strip() for s in os.getenv("MUSE_CATEGORIES", "Software Engineering,Data and Analytics,Design and UX,Business Operations,Accounting and Finance,Advertising and Marketing,Science and Engineering,Project Management").split(",") if s.strip()]
    queue = deque((category, 0) for category in categories)
    truncated = False
    for _ in range(max_pages):
        if not queue:
            if truncated:
                raise RuntimeError("Muse category pagination cap reached; results are partial")
            return
        category, page = queue.popleft()
        params = {"page": page, "level": ["Entry Level", "Internship"], "category": category}
        if os.getenv("MUSE_API_KEY"):
            params["api_key"] = os.environ["MUSE_API_KEY"]
        response, receipt = fetcher.get("muse", "https://www.themuse.com/api/public/jobs", params)
        data = response.json()
        if data.get("timed_out"):
            raise RuntimeError("Muse reported a partial timed-out result; rerun manually")
        for row in data["results"]:
            levels = [level["name"] for level in row.get("levels", [])]
            locations = [location["name"] for location in row.get("locations", [])]
            yield record("muse", row["id"], row["name"], row["refs"]["landing_page"],
                         "Internship" if "Internship" in levels else "Job", receipt,
                         organization=row.get("company", {}).get("name"),
                         description=plain(row.get("contents")), location="; ".join(locations) or None,
                         mode="Online" if any("remote" in s.lower() for s in locations) else None,
                         levels=levels, categories=[c["name"] for c in row.get("categories", [])],
                         published_at=row.get("publication_date"),
                         availability="Listed by The Muse at collection; verify with employer")
        # Observed API behavior: page=100 is rejected even with a larger page_count.
        if data["results"] and page + 1 < min(data["page_count"], 100):
            queue.append((category, page + 1))
        elif data["results"] and page + 1 < data["page_count"]:
            truncated = True
    if queue or truncated:
        raise RuntimeError("Muse request budget reached; category snapshot is partial; collected records retained")


def coursera(fetcher, max_pages):
    start = "0"
    seen = set()
    for _ in range(max_pages):
        response, receipt = fetcher.get("coursera", "https://api.coursera.org/api/courses.v1", {
            "limit": 1000, "start": start,
            "fields": "description,workload,primaryLanguages,partnerIds"})
        data = response.json()
        for row in data["elements"]:
            yield record("coursera", row["id"], row["name"],
                         "https://www.coursera.org/learn/" + quote(row["slug"], safe=""),
                         "Online course", receipt, organization="Coursera (see course page for provider)",
                         description=plain(row.get("description")), mode="Online", location=None,
                         workload=row.get("workload"), languages=row.get("primaryLanguages", []),
                         partner_ids=row.get("partnerIds", []), course_type=row.get("courseType"),
                         availability="Catalog entry; enrollment, price and certificate availability not checked")
        start = data.get("paging", {}).get("next")
        if start is None or str(start) in seen or not data["elements"]:
            return
        seen.add(str(start))
    raise RuntimeError("Coursera page budget reached; collected records retained")


def eventbrite(fetcher, max_pages):
    token = os.getenv("EVENTBRITE_TOKEN")
    organizations = [x.strip() for x in os.getenv("EVENTBRITE_ORGANIZATION_IDS", "").split(",") if x.strip()]
    events = [x.strip() for x in os.getenv("EVENTBRITE_EVENT_IDS", "").split(",") if x.strip()]
    if not token:
        raise RuntimeError("Not configured: EVENTBRITE_TOKEN required; public search retired")
    headers = {"Authorization": f"Bearer {token}"}
    if not organizations and not events:
        continuation = None
        for _ in range(max_pages):
            params = {"continuation": continuation} if continuation else None
            response, _ = fetcher.get("eventbrite", "https://www.eventbriteapi.com/v3/users/me/organizations/", params, headers)
            payload = response.json()
            organizations.extend(str(org["id"]) for org in payload.get("organizations", []))
            paging = payload.get("pagination", {})
            if not paging.get("has_more_items"):
                break
            next_cursor = paging.get("continuation")
            if not next_cursor or next_cursor == continuation:
                raise RuntimeError("Eventbrite organization pagination did not advance")
            continuation = next_cursor
        else:
            raise RuntimeError("Eventbrite organization discovery page budget reached")
        if not organizations:
            # Account tokens can retrieve explicit public events without owning an organization.
            seeds = json.loads((Path(__file__).parent / "eventbrite_seeds.json").read_text(encoding="utf-8"))
            events = seeds["event_ids"]
            if not events:
                raise RuntimeError("No accessible organizations or seeded public event IDs")
    endpoints = [(f"organizations/{quote(org, safe='')}/events/", True) for org in organizations]
    endpoints += [(f"events/{quote(event, safe='')}/", False) for event in events]
    for path, paginated in endpoints:
        continuation = None
        for _ in range(max_pages):
            params = {"expand": "venue,organizer"}
            if continuation:
                params["continuation"] = continuation
            response, receipt = fetcher.get("eventbrite", "https://www.eventbriteapi.com/v3/" + path, params, headers)
            data = response.json()
            for row in data.get("events", []) if paginated else [data]:
                # Do not expose draft/private events available through an account token.
                if not row.get("listed") or row.get("status") != "live":
                    continue
                venue = row.get("venue") or {}
                yield record("eventbrite", row["id"], row["name"]["text"], row["url"], "Networking event", receipt,
                             description=(row.get("description") or {}).get("text", ""),
                             organization=(row.get("organizer") or {}).get("name"),
                             mode="Online" if row.get("online_event") else "Local",
                             location=venue.get("address", {}).get("localized_address_display"),
                             start=row.get("start"), end=row.get("end"),
                             is_free=row.get("is_free"), category_id=row.get("category_id"),
                             ticket_availability=row.get("ticket_availability"),
                             availability="Public live event at collection; check registration and eligibility")
            paging = data.get("pagination", {})
            if not paginated or not paging.get("has_more_items"):
                break
            next_cursor = paging.get("continuation")
            if not next_cursor or next_cursor == continuation:
                raise RuntimeError("Eventbrite pagination did not advance")
            continuation = next_cursor
        else:
            raise RuntimeError("Eventbrite page budget reached; collected records retained")


def zotspot(fetcher, max_pages):
    base = "https://zotspot.uci.edu"
    response, _ = fetcher.get("zotspot", base + "/robots.txt")
    robots = RobotFileParser()
    robots.parse(response.text.splitlines())

    def allowed_get(url):
        if urlsplit(url).netloc != "zotspot.uci.edu" or not robots.can_fetch(USER_AGENT, url):
            raise RuntimeError("ZotSpot URL excluded by domain or robots policy")
        return fetcher.get("zotspot", url)

    response, receipt = allowed_get(base + "/events")
    soup = BeautifulSoup(response.text, "html.parser")
    # Scrape the publicly advertised export, never the disallowed mobile_ws endpoints.
    match = re.search(r'https://zotspot\.uci\.edu/ical/[^\s\"\'<>]+\.ics', response.text)
    if not match:
        raise RuntimeError("ZotSpot public calendar link not found; page layout may have changed")
    response, calendar_receipt = allowed_get(match.group(0))
    calendar = Calendar.from_ical(response.content)
    for event in calendar.walk("VEVENT"):
        url = str(event.get("URL") or event.get("CONTACT") or "")
        if not url.startswith(base):
            url = base + "/events"
        url = url.split("#")[0]
        organizer = event.get("ORGANIZER")
        organization = str(organizer.params.get("CN", "UC Irvine")) if organizer else "UC Irvine"
        def date_value(key):
            value = event.get(key)
            return value.dt.isoformat() if value is not None else None
        location = plain(event.get("LOCATION")) or None
        yield record("zotspot", event.get("UID") or url, event.get("SUMMARY"), url,
                     "Campus event", calendar_receipt, organization=organization,
                     description=plain(event.get("DESCRIPTION")), location=location,
                     mode="Online" if location and "online" in location.lower() else None,
                     start=date_value("DTSTART"), end=date_value("DTEND"),
                     availability="Public calendar listing; verify date, eligibility and registration",
                     collection_method="Calendar export discovered by scraping /events")

    # Optional detail URLs supplied explicitly or discovered in public HTML. Bounded, no login.
    urls = {urljoin(base, a.get("href", "")) for a in soup.select("a[href]")
            if "rsvp_boot?id=" in a.get("href", "")}
    urls.update(x.strip() for x in os.getenv("ZOTSPOT_DETAIL_URLS", "").split(",") if x.strip())
    for url in sorted(urls)[:max_pages]:
        response, receipt = allowed_get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        heading = soup.find("h1")
        if not heading:
            continue
        title = heading.get_text(" ", strip=True)
        if not title or "sign in" in title.lower():
            continue
        # Restrict to event description; never collect attendee/member/contact lists.
        description = soup.select_one('[itemprop="description"], #event_details, .event-description')
        yield record("zotspot", "detail-" + parse_qs(urlsplit(url).query).get("id", [url])[0],
                     title, url, "Campus event", receipt, organization="UC Irvine",
                     description=description.get_text(" ", strip=True) if description else "",
                     location=None, mode=None, availability="Public event page; verify details at source",
                     collection_method="Public event HTML")


def irvine(fetcher, max_pages):
    """Official City GIS resources; these are places, not invented scheduled events."""
    base = "https://gis.cityofirvine.org/arcgis/rest/services/Parks/MapServer"
    layers = [(1, "Trail", "CL=95"), (3, "Sports facility", "1=1"), (4, "Park", "1=1")]
    requests_used = 0
    for layer, kind, where in layers:
        endpoint = f"{base}/{layer}/query"
        response, _ = fetcher.get("irvine", endpoint, {"f": "json", "where": where, "returnIdsOnly": "true"})
        data = response.json()
        if "error" in data:
            raise RuntimeError(f"Irvine layer {layer} rejected the ID query")
        ids = sorted(data.get("objectIds") or [])
        for offset in range(0, len(ids), 500):
            if requests_used >= max_pages:
                raise RuntimeError("Irvine page budget reached; records retained")
            response, receipt = fetcher.get("irvine", endpoint, {
                "f": "json", "objectIds": ",".join(map(str, ids[offset:offset + 500])),
                "outFields": "*", "returnGeometry": "true", "outSR": 4326})
            requests_used += 1
            data = response.json()
            if "error" in data or data.get("exceededTransferLimit"):
                raise RuntimeError(f"Irvine layer {layer} response incomplete; reduce batch size")
            for feature in data.get("features", []):
                attrs = feature["attributes"]
                if kind == "Sports facility" and attrs.get("Type") not in {"Tennis", "Soccer", "Baseball", "Volleyball", "Softball", "Basketball", "Ice Rink"}:
                    continue  # Parking lots and concert venues are not sports opportunities.
                name = attrs.get("STREETNAME") if kind == "Trail" else attrs.get("FullName") if kind == "Sports facility" else attrs.get("NAME")
                # Some municipal polygons have no public-facing name; retain an honest fallback.
                name = name or f"Irvine {kind.lower()} (GIS feature {attrs['OBJECTID']})"
                amenity_keys = ("SOCCER", "TENNIS", "BASKETBALL", "VOLLEYBALL", "BASEBALL", "FITNESS", "TRAIL", "POOL", "Pickleball", "Badminton", "BallFields", "DISCGOLF")
                amenities = [key for key in amenity_keys if str(attrs.get(key) or "").strip().lower() not in {"", "0", "no", "none"}]
                if attrs.get("Type"):
                    amenities.append(str(attrs["Type"]))
                geometry = feature.get("geometry") or {}
                groups = geometry.get("paths") or geometry.get("rings") or []
                points = [point for group in groups for point in group]
                coordinates = None
                if points:
                    coordinates = {"latitude": sum(p[1] for p in points) / len(points),
                                   "longitude": sum(p[0] for p in points) / len(points),
                                   "basis": "Approximate representative point of source geometry; not an entrance or trailhead"}
                title = name if kind != "Sports facility" else f"Great Park — {name}"
                description = f"City of Irvine GIS {kind.lower()} resource: {title}."
                if amenities:
                    description += " Listed facilities: " + ", ".join(amenities) + "."
                if kind == "Trail":
                    description += " This is a mapped trail segment, not a complete recommended hiking route."
                yield record("irvine", f"{layer}:{attrs['OBJECTID']}", title,
                             endpoint + f"?f=pjson&objectIds={attrs['OBJECTID']}&outFields=*", kind, receipt,
                             organization="City of Irvine", description=description,
                             location=attrs.get("ADDRESS") or "Irvine, CA", city="Irvine",
                             mode="Local", coordinates=coordinates, amenities=amenities,
                             official_website=attrs.get("ParkURL"), miles=attrs.get("MILES"),
                             gis_layer=layer, gis_object_id=attrs["OBJECTID"], resource_type="place",
                             source_open_flag=attrs.get("FLAG"),
                             availability="Mapped place, not a scheduled event; verify access, hours, closures and reservations",
                             attribution="City of Irvine GIS / Parks MapServer")


ADAPTERS = {"anteater": anteater, "muse": muse, "eventbrite": eventbrite,
            "coursera": coursera, "zotspot": zotspot, "irvine": irvine}
