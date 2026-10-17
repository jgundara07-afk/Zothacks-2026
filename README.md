# One Thing
A ZotHacks demo that turns scrolling into one useful step: choose interests and skills, discover a fictional opportunity, save it, complete a small quest, and watch your mountain climb grow.

## Project updates
The current demo includes a vertical discovery feed; goal, skill, location, type, and difficulty filters; daily mood/effort check-ins; daily micro quests and streaks; save/unsave; persistent points; mountain-climb rewards; a keyword-based resume lab; activity analytics; and a four-slide, template-based recap. The sections below describe these implemented features and their limits.

The updated [build brief](CLAUDE.md) calls for **external opportunity APIs and permitted web scraping**, replacing the earlier dummy-document-only sourcing plan. The standalone collector now implements source adapters, raw capture, parsing, normalization, deduplication and provenance. Collection is invoked manually; automatic/scheduled refreshing is not implemented. Credentials stay server-side and the fictional offline demo remains available.

The standalone [manual opportunity collector](opportunity_data/README.md) gathers Anteater, Muse, Coursera, ZotSpot, Eventbrite and official City of Irvine parks/trails/sports data. Its app-readable export lives at `backend/catalog/opportunities.json.gz`, with counts, checksum and exact checklist options in `backend/catalog/manifest.json`. The Flask app exposes read-only `/catalog/options` and `/catalog/opportunities` routes for text search, interests, up to three goals, challenge (including Medium), time, location and commitment filters. See [the catalog API contract](docs/CATALOG_API.md). The existing UI/save/completion journey still uses `backend/seed.json`; collected cards are available for future integration without overwriting demo progress. The recap remains template-based.

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
On Windows, use `.venv\Scripts\pip` and `.venv\Scripts\python` instead of `.venv/bin/...`, and `copy` instead of `cp`.

Open http://127.0.0.1:5173. Vite proxies `/api` to Flask on port 5001. No runtime internet access, keys, external APIs, login, or remote fonts are needed. Dependencies require internet for initial installation.

## Project layout
```
backend/
  app.py              Flask app: loads the seed, error handlers, /health, registers the route modules
  store.py            Storage: MongoDB when MONGO_URI is set, otherwise local SQLite
  services.py         Shared logic: profile, activity, check-in, streaks/progress, personalized feed
  routes/             One file per feature: profile.py (profile + check-ins), feed.py (opportunities,
                      quests, saves), progress.py (progress, analytics, completions), resume.py
  seed.json           Canonical fictional sample data
  test_app.py         Backend journey tests
frontend/src/
  main.jsx            Starts the app
  App.jsx             Shared state and API calls; picks which page to show
  api.js              The single API client
  constants.js        Option lists (goals, skills, filters, nav items) and card icons
  pages/              One file per sidebar page (Discover + Saved share OpportunitiesPage.jsx)
  components/         Reusable pieces: OpportunityCard, MountainClimb, DailyCheckin, Analytics, ...
    layout/           Sidebar, Header, Footer, PageIntro, RightColumn
    modals/           Onboarding, Quest, Reward popups
  hooks/ utils/       Popup focus handling; feed filtering helpers
  styles/             index.css imports the rest in order. tokens.css holds shared fonts and colors;
                      the other files match the areas of the app (layout, feed, modals, recap, ...)
frontend/public/photos/
                      Hero and opening photos (original or properly licensed only). opening-mist.jpg is
                      StockSnap VQRELAZLLZ "Fog Mountains" (CC0); opening-halftone.png is made from it.
frontend/src/assets/  world-topo.svg: original generated topographic texture
design/
  references/         Visual references for the frontend, with notes in design/notes.md
docs/API.md           Request/response contract
```
New data source adapters (APIs and scrapers) will go in their own backend folder when they are added.

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

The daily check-in records mood and desired effort, and can be changed during the day. Small means notice or jot an idea, Medium means practice or draft, and Big means build, test, or go deeper. These sizes describe the next action, not the duration of an internship or course. Daily practices can be completed once per quest per day using a fresh action or idea. Original quests remain once-only.

A streak requires completing a quest, not merely opening the app or checking in. Days use America/Los_Angeles time. Multiple quests on one day count as one streak day; a full missed day resets the current streak while preserving points and the best streak. The tests cover midnight boundaries, repeat completion, missed days, and persisted check-ins.

## Career tools and feed filters
The seed document includes 81 specific fictional opportunities spanning classes, clubs, certifications, local events, networking, job simulations, and internship preparation. The vertical feed has a finite sample catalog, a next button, and a return-to-start button. It does not fetch live listings or pretend to provide an infinite external source.

Filter by interest, goal, skill, Local/Online, type, or step size (Small, Medium, Big). An explicit size selection takes precedence over the check-in; Reset filters restores the daily size. Internal difficulty levels and estimated durations remain available to scoring and analytics, but size labels drive the browsing experience.

Resume Lab accepts a PDF upload, pasted text, or a plain .txt file. PDFs must be under 5 MB, have no more than 20 pages, and contain selectable text. Password-protected, corrupt, oversized, and scanned/image-only PDFs return clear errors; OCR is not included. For Word, paste the text. It matches recognized keywords to three fictional role templates and links missing keyword areas to sample opportunities. The raw text is not stored and never sent to an external AI service. Missing keywords do not establish actual skill gaps. Use fictional resume text with this shared demo profile.

My progress shows seven-day completions, estimated practice time, skill tags, and opportunity categories. My recap turns the same real completion totals into four colorful, manually navigable slides. This is an offline template-based recap, not an AI-generated assessment. Mountain progress and the completion reward animate with reduced-motion support.

## Phone-style browsing
The app now uses a single phone-width view on desktop and fills narrow screens, with navigation anchored at the bottom. Each fresh page load opens a mood/effort/goal/interests/skills checklist before browsing. Choose opportunity types for this visit or leave them unchecked to explore all samples. Existing profile preferences prefill the checklist. **Skip for now** opens the feed without creating or updating a mood check-in; a new demo profile uses the default fictional preferences. Without an existing check-in, skipped browsing defaults to Small steps.

Discover shows the opportunity description above an illustrated image. Tap the card or activate it with Enter/Space to view details; opening details does not save automatically. Bookmark buttons toggle saves separately. Open my quest from the details sheet saves the opportunity if necessary and shows its checklist. The old Give it a go button is removed.

The bottom pace control reopens the daily plan. Filters live in a bottom sheet, including difficulty, location, goal, skill, interest, and opportunity type. Saved items, progress/mountain, resume tools, and recap remain available through the bottom navigation. Original local SVG illustrations are bundled in `frontend/public/illustrations/`; they need no external image service.

## Expanded sample catalog and PDF reading
See [the sample catalog](docs/sample-catalog.md) for all 81 specific fictional entries. There are at least ten samples in each major category: internships, clubs, classes, certifications, local events, networking, and job simulations. Details include the fictional host, local/online location, sample commitment, prerequisites, and a topic-specific deliverable. Daily Small, Medium, and Big quests are tailored to each new opportunity. Existing IDs remain stable so saves and completed quests survive the update. Equally matched items are interleaved by category for feed variety.

PDF extraction uses pypdf on the local Flask backend. The file is processed in memory and not saved in the database or to disk by the application. Analysis uses the same local keyword matcher as pasted text; no AI API is called. Install updated backend requirements and restart Flask to enable PDF uploads and load the expanded seed.

## Requested filters and text-only list
Onboarding and the bottom Filters sheet now share all fifteen requested interests, ten career goals (choose up to three), five challenge levels, seven time windows, four location choices, and three commitment preferences. Selections persist through the profile API. Topic/goal/location selections match catalog metadata; challenge/time selections choose an actual matching quest, and impossible combinations show an empty state. Near me refers to fictional Irvine-area samples and does not request GPS. Multi-day describes the longer opportunity, while the other time windows describe the first quest.

Six more fictional samples cover AI/ML, hackathons, hiking, sports, investing, and productivity, bringing the catalog to 87. The Small/Medium/Big first-step selector remains available alongside the expanded challenge choices.

Use **List** in the bottom toolbar to hide feed images and view a compact, scrollable sheet of opportunities. Use **Images** to return to the visual feed. Both views open the same detail sheets, use the same filters, and share save/unsave actions. The view preference is remembered locally across reloads.

Filter checks: `node --test frontend/tests/filtering.test.js`.

The latest opening checklist removes the energy question, first-step-size question, opportunity-type checklist, and Skills you bring section. It now presents only the requested interests, goals, challenge, time, location, and commitment groups. The internship goal is labeled Internship and covers all sample internship fields. Existing legacy software-internship goal selections migrate to that label when loaded. Opening submission saves preferences without recording a mood check-in.

## Streak calendar
Tap the flame/streak in the header or the streak in My progress to open the calendar. Completed quest days are green, days without recorded completions are gray, today is outlined, and future days are disabled. Choose a past day to inspect its completed quests and points; browse earlier months or return to today. Dates use the backend's Pacific timezone, matching streak calculation. Calendar history comes from persisted completion records; opening the app or saving an opportunity does not create a completion.

Calendar and filter checks: `node --test frontend/tests/*.test.js`.

## Demo sign-in screen
A fresh page load now opens a sign-in screen before the preference checklist. Sign in to demo continues as the shared fictional Alex profile; it does not authenticate credentials, create a private account, or isolate user data. The displayed alex@example.com address is read-only demo content. Flow: demo sign-in → preferences (or Skip for now) → opportunity feed. Real account authentication remains unimplemented.

## Animated climb and milestones
The climber follows the actual SVG trail using its path length as points increase, and a gold stroke shows traveled distance. Each 100 points unlocks the next level with a milestone banner, flag/sparkle animation, and a short confetti burst in the completion reward. Each 500 points reaches a summit; later points advance on the next numbered mountain. The reward screen animates from the pre-completion points to the authoritative server total. Reduced-motion users receive the final position and milestone text without motion or confetti. Math and milestone checks run with `node --test frontend/tests/*.test.js`.

## Integrated repository layout
The mobile experience now uses the shared `frontend/src/App.jsx` entry, feature components under `frontend/src/components/`, Resume/Recap pages under `frontend/src/pages/`, and `styles/mobile.css` selected by `styles/index.css`. The previously added desktop components and styles remain in the repository. Flask routes remain split across `backend/routes/`, with shared reads in `backend/services.py` and storage in `backend/store.py`.

The upstream collected catalog and its taxonomy, adapters, manifests, `/catalog/options` and `/catalog/opportunities` endpoints are preserved unchanged. The mobile demo continues to use the explicitly fictional seed and its separate preference vocabulary; the real catalog has not been silently substituted into save/quest flows. Design references and the data-gathering tools are retained.
