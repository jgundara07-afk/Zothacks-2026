# Manual opportunity gathering and parsing

This package gathers source data, parses it into a common schema, adds explicitly labeled OneThing estimates, and creates a separate opportunity database. **Nothing runs on app startup, on a timer, or in response to browsing the feed.** Run the CLI explicitly whenever a new collection is wanted.

## Collected snapshot — October 17, 2026

| Source | Unique records |
| --- | ---: |
| Anteater classes | 9,299 |
| Coursera online courses | 24,990 |
| Muse jobs and internships | 7,261 |
| ZotSpot campus events | 1,053 |
| Eventbrite local networking/career events | 11 |
| City of Irvine parks, trail segments and sports facilities | 294 |
| **Total** | **42,908** |

See [the consolidated audit](reports/collection-summary.json). The Anteater catalog was exhausted, with seven untitled entries excluded. Coursera pagination was exhausted. ZotSpot covers the public calendar export, including 541 past events and 512 upcoming/in-progress events as of collection. Eventbrite covers 11 public event IDs discovered manually; no organizations were accessible to the supplied account. Muse combines retained earlier records with refreshed category queries, deduplicated into 7,261 listings; category pagination is capped by the provider. City records include 162 mapped public-trail segments, 63 parks and 69 sports facilities; parking/concert features are excluded. These are snapshots, not a promise that every opportunity is currently available.

## App-readable personalization export

Every published catalog record has `personalization` using the exact [checklist labels](taxonomy.json), including Medium. App export applies the versioned relevance policy in `relevance.py`: it removes courses without a supported topic, generic unrelated jobs/internships, and events without an evident benefit. Parks, trails, and sports facilities are retained as personal wellbeing/recreation activities. The source SQLite catalog remains intact as a local review archive. Run these explicit commands after collecting:

```powershell
.\.venv\Scripts\python.exe -m opportunity_data.refine --export
.\.venv\Scripts\python.exe -m opportunity_data.export_app
```

This generates `backend/catalog/opportunities.json.gz` (portable compressed JSON, no external database needed to read it) and `backend/catalog/manifest.json` (included/excluded counts, exclusion reasons, checksum, options, coverage, fallback counts). Kept records are validated and the artifact is fully read back before publication. The generated file is inside the project and is not ignored by Git. The much larger raw/local datasets remain ignored. No commit or upload is performed by these commands.

The Flask app provides read-only `/catalog/options` and `/catalog/opportunities` search/filter routes over this file. See [the API contract](../docs/CATALOG_API.md) and [reader usage](../backend/catalog/README.md). The default core app now uses the same export for discovery, saves, daily preparation quests, resume suggestions and analytics. Explicit sample mode remains available. Source opportunity completion is distinct from self-reported preparation.

Topics and goal relevance use evidence-based editorial rules. When no specific interest is supported, a labeled broad personal-growth fallback is used. An unrelated subject can have no matching checklist goal. Unknown eligibility, venue details and full duration are not invented. Filtering can target full opportunities, first steps, or two-minute micro steps, so Lazy/Under 5 min never implies an entire internship can be completed in two minutes. Near me is calculated from supplied user coordinates and only records with source coordinates can match it.

## Run from the repository root (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m pip install -r opportunity_data/requirements.txt
.\.venv\Scripts\python.exe -m opportunity_data.collect --export
```

Default output, ignored by Git:

- `data/opportunities.sqlite3`: persistent normalized catalog, indexed by source, with unique source IDs and source URLs.
- `data/opportunities.json`: portable `{ "opportunities": [...] }` export when `--export` is supplied.
- `data/raw/<run-id>/`: original response bytes and a `receipts.jsonl` manifest with URL, HTTP status, UTC collection time, SHA-256, and local snapshot path. Credentials are removed from receipt URLs and authorization headers are never recorded.
- `data/latest_run.json`: per-source counts, errors, completeness, selection, and request count. Run history is also stored in the database's `runs` table.

The default Flask program adapts this export through `backend/program_catalog.py`. Source labels, current-detail links, and estimated preparation quests remain distinct from source facts. Profiles and activity persist in their existing store; this collector never overwrites them. `ONETHING_DATA_MODE=sample` uses the fictional fixture explicitly.

## Sources

| Source | Collection method | Scope and limitations |
| --- | --- | --- |
| [Anteater API](https://anteaterapi.com/reference) | `/v2/rest/coursesCursor`, 100 records/page | Complete course catalog if the page budget allows; catalog presence does not establish current enrollment availability. Attribution: [Data from Anteater API, ICSSC](https://icssc.link/about-anteaterapi). |
| [The Muse](https://www.themuse.com/developers/api/v2) | `/api/public/jobs`, 20 records/page | Entry Level and Internship filters, round-robin across eight career categories; 400 category-page requests by default. The API rejects page 100, so each category stops before that boundary. Large upstream catalog means this is a bounded snapshot, not all jobs worldwide. Override categories with `MUSE_CATEGORIES`. Optional `MUSE_API_KEY` in root `.env`; register the application with The Muse before broader use. |
| [Coursera](https://api.coursera.org/api/courses.v1?limit=1) | Public `courses.v1` catalog, 1,000 records/page | Follow `paging.next` until exhausted or the page budget is reached. This legacy endpoint was verified with live requests; it may change independently of Coursera's partner APIs. Partner IDs and reported workload are preserved; enrollment, provider names, price and certificate availability are not invented. |
| [ZotSpot](https://zotspot.uci.edu/events) | Scrape public `/events` HTML to discover its advertised calendar export; parse ICS events | Uses the public `/ical/uci/ical_uci.ics` export. The page's dynamic `/mobile_ws/v17/` listing endpoint is disallowed by robots and is not requested. Calendar includes past and future events. Optional public detail-page URLs can be supplied through `ZOTSPOT_DETAIL_URLS`. Never signs in or gathers attendee lists. |
| [Eventbrite](https://www.eventbrite.com/platform/new/api) | Authorized organization event lists or explicit event IDs | Requires `EVENTBRITE_TOKEN`. Optionally set comma-separated `EVENTBRITE_ORGANIZATION_IDS` or `EVENTBRITE_EVENT_IDS` in root `.env`. Without IDs, discover accessible organizations; if there are none, use the 11 manually discovered local public IDs in `eventbrite_seeds.json`. Retired public event search is not used. Only listed, live events are retained; private/draft events are excluded. No token means an explicit unavailable result, not fabricated networking events. |
| [City of Irvine GIS](https://gis.cityofirvine.org/arcgis/rest/services/Parks/MapServer) | ArcGIS REST ID queries followed by feature batches for trails (layer 1), sports facilities (3), parks (4) | Public API; no key required. Only CL=95 public-trail features are requested; parking/concert features are excluded from sports. Geometry provides approximate representative coordinates, not validated access points. Full routes, difficulty, access, reservations and opening hours are not supplied by this GIS service. |

No credentials should be pasted into commands or checked into Git. The root `.env.example` lists optional configuration. Each source failure is isolated; successfully gathered records survive and source errors appear in the run report. Existing records remain when a source fails, so inspect collection timestamps before treating them as current. This collector does not expire old records or refresh anything automatically.

The Muse adapter reads `MUSE_API_KEY` on the next manual run. `COURSERA_API_KEY` is reserved for an authenticated Coursera integration; the current public `courses.v1` collector does not send it. An authenticated adapter needs the specific Coursera API product and its documented authentication flow before using that credential.

## Editorial estimates and unknown fields

`enrich.py` contains an assistant-authored rubric, versioned as `one-thing-editorial-v1`. It derives suggested skill tags from keywords, estimates difficulty from catalog level/type/title, and proposes a small preparation quest. These live under `editorial`, with the author, basis, and explicit estimate flags. The estimates are repeatable; this does **not** mean a human reviewed every source record.

First-step estimates: classes 15 minutes, online courses 10 minutes, job/internship preparation 20 minutes, event preparation 5 minutes. These refer only to reading requirements, choosing a lesson, drafting a resume bullet, or preparing a question. They are never claimed to be the duration of completing the actual opportunity.

Source workload text, dates, units, prerequisites, restrictions, levels, and location remain separate source facts. Event duration is calculated from source start/end timestamps when possible, and past events are labeled relative to collection time. Unknown total duration, delivery mode, deadlines, price, or eligibility remain unknown. Historical events and catalog entries are retained for breadth; inspect source dates and links before recommending attendance or enrollment.

Six source entries have individually reviewed suggestions in `editorial_overrides.json`; the rest use the documented rubric. To refine individual entries, add entries keyed by normalized opportunity ID to that file, then run the offline refinement command below. Allowed fields are `difficulty`, `first_step_minutes`, `suggested_first_step`, and `inferred_skills`; a `reason` is required. Example:

```json
{
  "source-<stable-hash>": {
    "difficulty": "Hard",
    "first_step_minutes": 15,
    "reason": "Reviewed prerequisites; first step is comparing them with current skills."
  }
}
```

## Controls and verification

```powershell
# Fetch one source only; explicit manual rerun, not a scheduled refresh.
.\.venv\Scripts\python.exe -m opportunity_data.collect --sources zotspot --export
# Smaller development run; reaching a page limit is reported as partial.
.\.venv\Scripts\python.exe -m opportunity_data.collect --sources muse --muse-pages 2 --export
# Offline parser/database tests; no real API calls.
.\.venv\Scripts\python.exe -m unittest opportunity_data.test_pipeline -v
# Reapply the latest editorial rules to stored source facts, with no network requests.
.\.venv\Scripts\python.exe -m opportunity_data.refine --export
# Audit database integrity, record fields and JSON export; consolidate source reports.
.\.venv\Scripts\python.exe -m opportunity_data.audit
```

`--max-pages` defaults to 500 per source; `--muse-pages` defaults to 400 (at most 8,000 rows before deduplication). Collection is sequential with a minimum 0.25-second request interval, connection/read timeouts, and bounded retries. Long rate-limit pauses stop that source for a later manual run. Adjust `--delay` upward for stricter provider limits. Do not increase request budgets beyond provider limits. The scraper checks robots directives before requesting pages or the advertised export.

Code layout: `http.py` handles gathering/raw snapshots; `sources.py` handles source schemas and pagination; `enrich.py` adds editorial suggestions; `database.py` handles persistence/deduplication/export; `collect.py` orchestrates the explicit one-time command. No cron jobs, background refresh services, or application hooks are installed.
