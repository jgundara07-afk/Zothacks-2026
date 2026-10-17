# OneThing — ZotHacks build brief

## Product vision
**OneThing** is a productive scrolling app that uses gamification to reward and promote continuous career progress. Turn browsing into small, achievable actions: discover an opportunity, take a baby step, complete a quest, and see progress compound.

Business mottos: **1% everyday**, **Take baby steps**, **Productive scrolling**, and **Continuous opportunity feed**.

This brief describes the target product, not a claim that every feature already exists. Build on the existing demo and prioritize a complete working journey.

## Essential features
- **Continuous opportunity feed:** Gather local and online career opportunities through external APIs and web scraping, normalize them into a shared catalog, and browse them with incremental loading. Distinguish live-source records, cached records, and fictional samples; show honest loading and end-of-feed states.
- **Goal and skill filters:** Filter and recommend opportunities using career goals, interests, and skills. Explain recommendations through matching tags and skills an opportunity helps develop.
- **Quest difficulty filters:** Offer game-like effort levels such as Lazy, Easy, Hard, and Challenging. Show estimated time, prerequisites, and actionable steps.
- **Gamified quests and rewards:** Turn opportunities into quests with checklists, points, milestones, and rewards. Prevent duplicate completion and duplicate point awards.
- **Daily micro goals:** Offer manageable daily quests aligned with the student's goals and available effort. Persist completion and distinguish daily steps from longer-term opportunities.
- **Resume gap recommendations:** Accept resume content, compare it with stated goals and opportunity skill tags, identify potential gaps, and recommend relevant opportunities. Explain suggestions without inventing credentials or presenting inferred gaps as verified facts. Use a fictional resume in the demo; do not log or commit resume content.
- **Opportunity and progress analytics:** Summarize opportunities by source, skills, and difficulty, alongside saves, completions, points, and skills practiced. Distinguish available feed data from actual user activity.
- **Spotify Wrapped-style results:** Create a colorful, personalized recap of completed quests, skills practiced, milestones, and next steps. Target AI-powered narrative generation grounded in activity. Include a deterministic local fallback so the demo needs no AI API; label fallback summaries accurately rather than claiming they were AI-generated.

## Sources and data gathering
Opportunity categories: **classes, clubs, online certifications, local events, networking, job simulations, and internships**. Support local/online location or delivery-mode filters where the data provides those fields.

Use **external opportunity APIs and web scraping** as the target data sources. Prefer documented APIs where available; add source-specific scrapers for public opportunity pages that permit automated collection. Select and document actual providers during implementation rather than assuming an integration already exists. Cover the categories above with stable IDs, titles, descriptions, source categories, goal/skill tags, location or delivery mode, estimated effort, and linked quests/rewards.

Build gathering behind backend source adapters, separate from parsing and normalization. Keep raw responses or page snapshots in ignored local storage with source URL, provider, collection time, content hash, and fetch status. Normalize validated records into the catalog, deduplicate by source ID or canonical URL, track deadlines and last successful collection, and retain provenance. Use Anteater API for classes, The Muse for jobs/internships, Eventbrite for authorized networking events, Coursera for online courses, and public ZotSpot pages/advertised calendar exports for campus events. Keep this pipeline in `opportunity_data/` and invoke it manually. Do not implement automatic refreshing, scheduled jobs, or collection on app startup or feed requests. Serve stored records so upstream delays do not block scrolling. Label assistant-authored difficulty and first-step duration estimates separately from source facts; do not invent missing deadlines or qualifications.

Use timeouts, bounded retries with backoff, provider rate limits, and caching. Scrapers must respect site terms and robots directives; do not bypass login, paywalls, CAPTCHAs, or access controls. Keep API keys server-side in `.env`. Document source setup, refresh commands, and failure behavior. Tests should use recorded or synthetic fixtures rather than depend on live services.

Retain the curated dummy document and canonical `backend/seed.json` fixture as an explicit offline demo mode. Clearly label fictional samples and cached/stale records; never silently present fallback samples as live results. Real records should link to their source and show collection freshness without implying guaranteed availability, credentials, or career outcomes. Live gathering requires internet and any provider credentials; offline sample mode must remain usable without them. Use fictional resume content in demonstrations and keep social imports out of scope.

## Design and interaction
- **Current art direction:** cinematic, analog black-and-white photography with visible grain, misty depth, halftone accents, warm off-white content surfaces, deep charcoal, and a restrained burnt-red accent. Avoid brutalist UI, generic stock imagery, literal fantasy motifs, and sticky-note styling.
- **First-screen composition:** use `design/references/iris-halftone-signin-reference.png` and `design/ONBOARDING_FLOW.md` as the primary references. Lead with a distinctive ghosted photograph at the top/background; keep the sign-up/log-in controls crisp and readable in a calm foreground panel. Adapt the composition for mobile.
- Every quest/task card needs a relevant aesthetic editorial photograph with a consistent crop and readable text. Use original or properly licensed images; reference screenshots are not app assets.
- Progress and reward visuals should support the photography-first system; avoid a literal mountain-climbing UI unless it clearly improves the working user journey.
- A responsive scrolling feed with loading, empty, error, and end-of-feed states.
- Keyboard navigation, visible focus, accessible contrast, and reduced-motion alternatives to climbing and reward animations.
- Visual references live in `design/references/`, with notes in `design/references/README.md` and `design/notes.md`. Check them before frontend design work. For visual changes, use `/one-thing-visual-pass` to compare screenshots against the chosen composition.

## Stack and shared contract
React + Vite frontend; Python + Flask REST API; MongoDB via PyMongo. Follow the folder layout in the README's "Project layout" section: new pages go in `frontend/src/pages/`, reusable UI in `frontend/src/components/`, styles in the matching `frontend/src/styles/` area file with shared fonts/colors in `tokens.css`, and new API routes in a `backend/routes/` module registered in `app.py`. Preserve the existing persistent SQLite demo adapter when `MONGO_URI` is empty so local setup requires no database service. Keep `MONGO_URI` and optional service secrets in the ignored root `.env`, never Git. Keep one frontend API client and canonical seed JSON.

Core collections: `profiles`, `opportunities`, `quests`, `activity`. Extend the model as needed for source configuration, gathering runs, provenance, daily quest assignments, resume-derived skill summaries, and recap metadata. Use one fictional demo profile; no login. Persist preferences, saves, completions, and progress across refreshes and restarts.

Preserve existing routes: `GET /health`, `GET /opportunities`, `GET /quests`, `GET /saved`, `GET /progress`, `POST /profiles`, `POST /saved`, and `POST /completions`. The frontend uses Vite's `/api` proxy during local development.

Extend the contract for pagination, category/location/difficulty/goal/skill filters, daily quests, resume gap recommendations, analytics, and recap generation as features are implemented. Document request/response JSON in `docs/API.md` before connecting new frontend behavior. Do not describe planned endpoints as implemented. Return clear validation and service errors, calculate rewards on the server, and keep completion retries idempotent.

## Delivery phases and proof
1. **Foundation and data gathering:** Preserve local startup and the app shell; establish API and permitted scraping adapters, raw capture, normalization, deduplication, provenance, and the shared contract. Retain representative offline fixtures. Proof: configured sources populate the catalog, failures preserve cached data, and offline sample mode works without external services.
2. **Productive scrolling:** Deliver onboarding, an incrementally loaded catalog, filters, recommendation explanations, and saves. Proof: filters behave consistently, source/freshness labels are accurate, and sample limits are clear.
3. **Daily quests and rewards:** Connect opportunities to difficulty-based quests, daily micro goals, checklists, points, and mountain-climb rewards. Proof: a fresh user completes the journey; two different quests count once each; saves and progress survive refresh and restart.
4. **Resume recommendations:** Add resume input, transparent gap suggestions, and related sample opportunities. Proof: a fictional resume produces explainable suggestions and invalid input has a recovery path.
5. **Analytics and recap:** Add opportunity breakdowns, personal activity analytics, and colorful Wrapped-style results. Proof: totals match recorded activity, empty states work, and a personalized local recap works without an AI service.
6. **Finish:** Polish responsive layouts, accessibility, animation alternatives, errors, and README setup steps. Proof: frontend build, backend journey checks, and a full browser walkthrough pass.

Integrate at every phase. Fix broken checks before expanding scope. Keep sample data explicit and recommendations grounded in available data.

## Git workflow
Before every commit, fetch the latest remote changes and ensure the current branch includes the latest changes from its upstream branch. If no upstream is configured, identify the intended remote branch before proceeding. Fast-forward when possible; otherwise integrate the remote changes and resolve conflicts before committing. Preserve uncommitted work while syncing, and never discard teammates' changes or force-push to bypass divergence. Verify the branch is up to date and run checks appropriate to the integrated changes before creating the commit.

## Personalization data contract
Use the exact labels in `opportunity_data/taxonomy.json` for interests, goals (up to three user selections), Lazy/Easy/Medium/Hard/Challenging, time buckets, location preferences and commitment. The manually collected dataset includes City of Irvine GIS parks, public-trail segments and actual sports facilities; exclude parking lots and unrelated venues. Municipal places must not be presented as scheduled events or complete hiking routes. Export validated collected cards to `backend/catalog/opportunities.json.gz` and a checksum/coverage manifest. Keep classifications and missing-field estimates labeled with evidence, preserve source facts, and do not force unrelated records into technical topics or unsupported goals. Distinguish full-opportunity duration from preparation and two-minute micro steps. Calculate Near me from user coordinates and available source coordinates; do not infer the user's location. Read-only `/catalog` routes expose this file separately until the UI and save/quest lifecycle are deliberately integrated. No automatic refresh or replacement of the fictional seed is implied.
