# One Thing
A ZotHacks demo that turns scrolling into one useful step: choose interests and skills, discover a fictional opportunity, save it, complete a small quest, and watch your mountain climb grow.

## Project updates
The current demo includes a vertical discovery feed; goal, skill, location, type, and difficulty filters; daily mood/effort check-ins; daily micro quests and streaks; save/unsave; persistent points; mountain-climb rewards; a keyword-based resume lab; activity analytics; and a four-slide, template-based recap. The sections below describe these implemented features and their limits.

The updated [build brief](CLAUDE.md) now calls for **external opportunity APIs and permitted web scraping**, replacing the earlier dummy-document-only sourcing plan. Planned work includes backend source adapters, raw response/page capture, parsing and normalization, deduplication, scheduled refreshes, provenance and freshness labels, caching, and graceful source failures. API credentials will remain server-side, and an explicitly labeled offline sample mode will remain available.

**This update changes the documentation, not the running data pipeline.** API collectors, scrapers, and live-source refreshes are not implemented yet; the current app still uses `backend/seed.json`. The existing recap is template-based, not AI-generated. Live-source setup instructions and provider credentials will be documented when integrations are added.

## Run locally
Requires Node.js 20.19+ (or 22.12+) and Python 3.10+.

From this directory:
```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp .env.example .env
.venv/bin/python backend/app.py
```
In a second terminal:
```sh
cd frontend
npm install
npm run dev
```
Open http://127.0.0.1:5173. Vite proxies `/api` to Flask on port 5001. No runtime internet access, keys, external APIs, login, or remote fonts are needed. Dependencies require internet for initial installation.

## Storage
With an empty `MONGO_URI`, the app automatically uses persistent SQLite at `backend/demo.sqlite3`. It mirrors the four document collections and supports the entire demo offline. This is an explicit demo adapter, not an in-memory mock.

For MongoDB, set `MONGO_URI` in the ignored root `.env` to your local or hosted MongoDB URI, optionally set `MONGO_DB=one_thing`, and restart Flask. PyMongo uses `profiles`, `opportunities`, `quests`, and `activity`; MongoDB `_id` uniquely protects each save and quest completion. A configured but unavailable MongoDB fails startup instead of silently changing storage. Do not commit `.env`. The health endpoint identifies the selected adapter. Local and Mongo storage are separate; switching does not migrate state.

`backend/seed.json` is the canonical fictional seed. Startup inserts missing records without resetting activity. One shared fictional profile, Alex, is used across all browser sessions. Preference updates preserve progress. Scores are computed from immutable completion records, so retries cannot add points twice.

For a fresh local demo, stop Flask and rename `backend/demo.sqlite3` to a backup filename, then restart. A new database and fictional seed will be created. Do not reset a Mongo database containing data you need.

## Two-minute demo
1. On first visit, choose a goal, at least one interest, and one skill. Select **Find my one thing**.
2. Read the matching tags and clearly labeled sample opportunities. Save a card using its bookmark, or select **Give it a go** to save and open a quest.
3. Do the quest steps offline, check each step, and select **I did my one thing**. Celebrate the points.
4. Open **My progress** to see the mountain, totals, and completed quest history.
5. Complete a different quest. Design plus coding earns 125 points. Reopening a completed quest disables completion; API retries also award zero extra points.
6. Refresh: preferences, saves, and completions remain. Visit **Saved things** to find your saved items. Click a filled bookmark to unsave an opportunity; your completed quests and earned points remain.

The demo uses self-reported completion, not evidence uploads. Difficulty and estimated time are shown in each quest. No live listings are implied. Analytics and a four-slide colorful recap are available from My progress and My recap.

## Validation
```sh
.venv/bin/python -m unittest discover -s backend -v
cd frontend
npm run build
```
The backend journey test uses a temporary database to verify a fresh profile, tag explanations, validation errors, save prerequisites, missing IDs, two quests counted once each, and persistence after reopening storage.

Verified locally: production build, backend journey checks, and browser save → checklist → reward → persisted progress. Responsive layouts, keyboard focus indicators, modal focus trapping, Escape handling, and reduced-motion support are implemented. MongoDB integration needs a running MongoDB instance for live verification. This local development demo is not configured as a public multi-user deployment.

API request/response contract: [docs/API.md](docs/API.md).

## Daily discovery
Discover is a vertical, scroll-snapping feed: swipe, scroll, or focus the feed and use keyboard scrolling to explore one opportunity at a time. Bookmarks toggle save/unsave. All cards are fictional samples.

The daily check-in records mood and desired effort, and can be changed during the day. Small offers 2-minute practices; big offers 10–20 minute quests. Daily practices can be completed once per quest per day using a fresh action or idea. Original quests remain once-only.

A streak requires completing a quest, not merely opening the app or checking in. Days use America/Los_Angeles time. Multiple quests on one day count as one streak day; a full missed day resets the current streak while preserving points and the best streak. The tests cover midnight boundaries, repeat completion, missed days, and persisted check-ins.

## Career tools and feed filters
The seed document includes 11 fictional opportunities spanning classes, clubs, certifications, local events, networking, job simulations, and internship preparation. The vertical feed has a finite sample catalog, a next button, and a return-to-start button. It does not fetch live listings or pretend to provide an infinite external source.

Filter by interest, goal, skill, Local/Online, type, or quest difficulty. Lazy offers a 2-minute micro goal; Easy, Hard, and Challenging provide increasingly involved daily practice. An explicit difficulty selection takes precedence over the check-in pace; Reset filters restores the daily pace.

Resume lab accepts pasted text or a plain .txt file. For PDFs or Word, paste the text. It matches recognized keywords to three fictional role templates and links missing keyword areas to sample opportunities. The raw text is not stored and never sent to an external AI service. Missing keywords do not establish actual skill gaps. Use fictional resume text with this shared demo profile.

My progress shows seven-day completions, estimated practice time, skill tags, and opportunity categories. My recap turns the same real completion totals into four colorful, manually navigable slides. This is an offline template-based recap, not an AI-generated assessment. Mountain progress and the completion reward animate with reduced-motion support.
