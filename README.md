# OneThing
OneThing turns scrolling into a useful next step: choose interests and goals, explore opportunities, save one, complete a preparation quest, and track progress.

## Current integration

Recap distinguishes active generation from completed local fallbacks, including quota, credential, connection and response errors. Retryable failures offer a manual retry; quota failures enforce a 60-second cooldown. Successful Gemini stories are cached locally by selected period, completed history and model so reopening an unchanged recap does not request another story. The local story remains available when Gemini cannot respond.

The Progress tracker is now an interactive achievement atlas. Ten selectable regions contain 95 mountain pieces with distinct numbered badges; unlocking an achievement permanently reveals its mountain as explored and climbed. Select a piece to see its rule and progress. The badge journal supports region filters. Five requested but currently unreachable achievements were excluded (classes, job simulations, two resume-analyzer goals and ten distinct skills).

Optional completion logs record actual minutes and explicitly self-reported outcomes for effort, application, attendance and outreach achievements. Preparation quests never silently count as completed applications, certifications or attended events. Yearly recaps and Top Quests highlight cards support the new recap milestones alongside Lifetime and Monthly stories. View milestones use visible content, not background API fetches.

Progress includes 95 permanent achievement badges with distinct engraved emblems, unlock criteria, flavor text and completion progress. Recap offers Lifetime, a selected calendar month, or a selected year, plus separate Story and Badges views. The story focuses on archetype, signature move, quest highlights, a plot twist, the OneThing effect and a next step; charts and totals stay in Analytics. Monthly stories use every completed quest in that Pacific-calendar month, and the badge collection marks achievements earned that month. Daily micro-goals for the seven-day achievement are daily quests lasting at most five minutes.
The app now uses the **11,314-record curated catalog by default**, including 294 City of Irvine public trail segments, parks and sports facilities. Sources include Anteater, Coursera, The Muse, ZotSpot and Eventbrite. Cards are cached source records with original links and collection dates; availability and assistant-estimated categories/effort need verification at the source. Expired dated events are excluded from discovery. No collection runs at startup or during browsing.

The main feed filters on the server before pagination, loads 40 cards at a time, and supports Load more. Preferences cover up to ten interests, up to three goals, opportunity challenge and duration, location, commitment and opportunity type. Any selected interest, goal or skill may match within its group; difficulty, time and metadata choices remain alternatives within each group, with AND across groups. The UI label Internship maps to the catalog's software-internship goal. Near me requests browser location only when selected and checks known source coordinates within 25 km; unknown locations do not count as nearby. Denied location access returns a recoverable error. City coordinates represent approximate points, not validated trailheads or entrances.

Collected IDs now work with save/unsave, daily preparation quests, persistent points/streaks, activity analytics, and local resume suggestions. Quests are app-authored preparation actions: they do not certify completion of an external course, job, event or outdoor activity. Challenge and time filters match the stored full-opportunity difficulty and duration, including Multi-day. Preparation step size is independent, with its own estimated minutes and challenge shown on the quest. The UI and APIs enforce at most ten interests and three goals. Source facts remain in each card's personalization/source metadata. The 3+ hours filter uses the catalog duration bucket; longer preparation variants remain available through step size. Some filter combinations legitimately have no records.

The catalog is read from `backend/catalog/opportunities.json.gz` with checksum verification. `manifest.json` contains counts/options and `sample.json` is a small readable preview. Profiles, saves, and completions persist separately in SQLite or MongoDB. Existing sample saves/history remain readable; fictional records are labeled. Explicit sample mode uses the 87-entry `backend/seed.json` fixture.

## Run locally
Requires Python 3.10+ and Node.js 20.19+ (or 22.12+). From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
# On first setup only, if .env does not exist:
Copy-Item .env.example .env
.\.venv\Scripts\python.exe backend/app.py
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to Flask on port 5001. Sign in to the demo, choose preferences or skip, and browse the cached catalog. Initial catalog decoding takes a few seconds. Browsing requires no API credentials or upstream network access; following source links and browser location may require network access. Optionally set `GEMINI_API_KEY` in the ignored root `.env` to show a short Gemini-generated self-guided suggestion when no current catalog opportunity matches the selected interests/goals, and to generate the activity-based Wrapped recap. Recap prompts contain recorded completion summaries and the complete dated quest history for the selected period; profile fields and location are not sent. A local recap appears when Gemini is unavailable or the user has no completed quests.

On macOS/Linux use `.venv/bin/python`, `cp`, and normal shell syntax. Keep existing `.env` credentials when updating the project.

## Deploy (Render)
`render.yaml` defines one web service that builds `frontend/dist` and runs `gunicorn --chdir backend wsgi:app`. `backend/wsgi.py` serves the built frontend at `/` and the Flask API under `/api`, matching the Vite dev proxy. Set `MONGO_URI` (and optionally `GEMINI_API_KEY`) in the Render dashboard; without `MONGO_URI` the service falls back to SQLite on Render's ephemeral disk, so saves and progress reset on every redeploy or restart. Pushes to `main` redeploy automatically. Republishing the catalog means committing a new `backend/catalog/opportunities.json.gz`.

## Data and sample modes
`ONETHING_DATA_MODE=catalog` is the default. To use fictional sample mode for a run:

```powershell
$env:ONETHING_DATA_MODE = 'sample'
.\.venv\Scripts\python.exe backend/app.py
# Return to collected records before the next restart:
Remove-Item Env:ONETHING_DATA_MODE
```

An empty `MONGO_URI` uses persistent `backend/demo.sqlite3`. A configured MongoDB must be reachable. No account authentication is implemented: all sessions share the fictional Alex profile. Switching storage does not migrate state. Switching data modes preserves existing activity; it does not delete saved items or points. Startup never imports 11,254 records into the profile store or overwrites activity.

The missing/corrupt catalog fails startup with a clear file/checksum error; there is no silent sample fallback. After a manual refresh, restart Flask to load the new catalog.

## Manual collection
The separate `opportunity_data/` package gathers, normalizes and categorizes public-source data. Raw snapshots and the collector SQLite database remain ignored locally. API keys stay in ignored `.env`. Collection is manual only:

```powershell
.\.venv\Scripts\python.exe -m pip install -r opportunity_data/requirements.txt
.\.venv\Scripts\python.exe -m opportunity_data.collect --export
.\.venv\Scripts\python.exe -m opportunity_data.refine --export
.\.venv\Scripts\python.exe -m opportunity_data.export_app
.\.venv\Scripts\python.exe -m opportunity_data.audit
```

See [collector setup and source limitations](opportunity_data/README.md), [core API](docs/API.md), and [raw catalog search API](docs/CATALOG_API.md). Source access and completeness vary; the catalog is a cached collection, not guaranteed current inventory. Classification uses evidence rules and labeled estimates; unsupported goals remain empty.

## Verify

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
.\.venv\Scripts\python.exe -m unittest opportunity_data.test_pipeline opportunity_data.test_personalization -v
cd frontend
node --test tests/*.test.js
npm run build
```

Tests use temporary profile storage and the bundled catalog, without calling upstream providers. They cover both explicit sample mode and collected-mode pagination, combined filters, save prerequisites, duplicate reward protection, Pacific daily rollover, persistence, analytics, resume suggestions and nearby queries. MongoDB requires a live instance for its own integration check.

## Project layout
- `backend/app.py`: application factory, default data mode and API registration.
- `backend/program_catalog.py`: collected cards and preparation-quest adapter.
- `backend/services.py`: preferences, filtering/ranking, saved records and progress.
- `backend/catalog/`: portable collected data and checksum/coverage manifest.
- `backend/store.py`: persistent profile/activity adapter (SQLite or MongoDB).
- `backend/routes/`: profile, feed/quests/saves, progress/analytics, PDF/text resume endpoints.
- `backend/seed.json`: explicit fictional sample fixture.
- `frontend/src/App.jsx`, `api.js`: app flow, paginated feed and shared API client.
- `frontend/src/components/`, `pages/`, `styles/`: reusable UI, screens and styling.
- `shared/preferences.json`: current UI choice labels.
- `opportunity_data/`: manually invoked collectors, taxonomy, enrichment/export and audits.
- `design/references/`: art direction references, not app assets.

The existing phone-width UI, sign-in placeholder, preference checklist, list/image toggle, streak calendar, climb rewards and template recap are retained. Resume Lab has been removed from the app navigation and screens. This remains a shared local hackathon demo rather than a public multi-user service.

## Automatic feed pagination
Discover loads the next API page automatically when the bottom of the image feed or text-only list approaches the viewport. Requests are serialized, appended cards are deduplicated by stable opportunity ID, and a filter change invalidates older responses. Scrolling stays in place while cards are appended. A load-more button remains as an accessible/manual fallback, failures show a retry action, and an explicit end message appears when `has_more` is false. Saved items keep their existing list behavior.

### Demo dates and analytics
In Progress, use the Demo time machine date picker or Next demo day, then complete a saved daily quest. Dates persist across refreshes and daily duplicates count once per quest per simulated day. Use real today resets the clock without deleting history. Catalog availability still uses real time. Set `ONETHING_DEMO_TOOLS=0` to disable date changes. This is a shared fictional demo profile, not an authenticated production feature.

Analytics supports Weekly (Monday–Sunday), Monthly (daily bars fitted to the screen), and Yearly views, with period navigation. Donut charts show opportunity categories, challenges, and skill-tag shares for the selected period. Skills can overlap; percentages are rounded. Recap and the mountain retain lifetime totals.

### Catalog effort and filter update

Collected opportunities now carry five-level difficulty estimates with evidence, source/estimated duration ranges, experience, cost, prerequisite and schedule metadata. Discovery accepts any selected interest, goal or skill within each group, supports explicit metadata filters and a maximum total time, and treats unknown details explicitly. Full source activities and preparation quests remain separate. Rebuild the stored app catalog manually with `python -m opportunity_data.refine --export` followed by `python -m opportunity_data.export_app`; no automatic data refreshing is enabled. See [the data package](opportunity_data/README.md#effort-and-strict-filtering-update) for limitations and provenance.

The current catalog excludes all UCI/Anteater classes and retains 9,275 focused online courses, 941 internships, 122 jobs, 616 campus events, 294 Irvine recreation places and 6 networking events (11,254 total). Online courses require a direct checklist-topic match in their title, preventing incidental description text or fallback tags from qualifying them.

Expanded interest choices: 462 unique options from the supplied 12 subject categories, plus the original grouped choices, searchable by name/category. Startup keeps photographic selection tiles; filter editing supports searchable checkboxes. Interests allow ten selections, goals three. Granular catalog tags use title/amenity evidence, so subjects without current opportunities can return no results under strict matching. Existing interests retain their original stored labels.

When discovery has no available interest/goal matches, it can show clearly labeled neutral alternatives: parks or self-development courses. These still respect the remaining filters, and no expired records or invented opportunities are introduced. Preferences are preserved; the app does not silently reset them.

The catalog now also includes 60 user-supplied self-guided general tasks (`opportunity_data/general_tasks.json`), for 11,314 total items. They lead neutral fallback results and are mixed in at up to one after seven personalized results, subject to the same non-topic filters. Tasks use their real action steps and daily completion rewards; they are labeled authored content rather than cached external listings.
