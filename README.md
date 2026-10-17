# One Thing
A ZotHacks demo that turns scrolling into one useful step: choose interests and skills, discover a fictional opportunity, save it, complete a small quest, and watch your mountain climb grow.

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
6. Refresh: preferences, saves, and completions remain. Visit **Saved things** to find your saved items.

The demo uses self-reported completion, not evidence uploads. Difficulty and estimated time are shown in each quest. No live listings are implied. Analytics and a Wrapped recap were left out to prioritize the complete core journey.

## Validation
```sh
.venv/bin/python -m unittest discover -s backend -v
cd frontend
npm run build
```
The backend journey test uses a temporary database to verify a fresh profile, tag explanations, validation errors, save prerequisites, missing IDs, two quests counted once each, and persistence after reopening storage.

Verified locally: production build, backend journey checks, and browser save → checklist → reward → persisted progress. Responsive layouts, keyboard focus indicators, modal focus trapping, Escape handling, and reduced-motion support are implemented. MongoDB integration needs a running MongoDB instance for live verification. This local development demo is not configured as a public multi-user deployment.

API request/response contract: [docs/API.md](docs/API.md).
