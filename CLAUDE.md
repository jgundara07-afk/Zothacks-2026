# OneThing — ZotHacks build brief

## Product vision
**OneThing** is a productive scrolling app that uses gamification to reward and promote continuous career progress. Turn browsing into small, achievable actions: discover an opportunity, take a baby step, complete a quest, and see progress compound.

Business mottos: **1% everyday**, **Take baby steps**, **Productive scrolling**, and **Continuous opportunity feed**.

This brief describes the target product, not a claim that every feature already exists. Build on the existing demo and prioritize a complete working journey.

## Essential features
- **Continuous opportunity feed:** Browse local and online career opportunities with incremental loading. Show a clear end-of-sample state; do not imply that finite dummy data is live or unlimited.
- **Goal and skill filters:** Filter and recommend opportunities using career goals, interests, and skills. Explain recommendations through matching tags and skills an opportunity helps develop.
- **Quest difficulty filters:** Offer game-like effort levels such as Lazy, Easy, Hard, and Challenging. Show estimated time, prerequisites, and actionable steps.
- **Gamified quests and rewards:** Turn opportunities into quests with checklists, points, milestones, and rewards. Prevent duplicate completion and duplicate point awards.
- **Daily micro goals:** Offer manageable daily quests aligned with the student's goals and available effort. Persist completion and distinguish daily steps from longer-term opportunities.
- **Resume gap recommendations:** Accept resume content, compare it with stated goals and opportunity skill tags, identify potential gaps, and recommend relevant opportunities. Explain suggestions without inventing credentials or presenting inferred gaps as verified facts. Use a fictional resume in the demo; do not log or commit resume content.
- **Opportunity and progress analytics:** Summarize opportunities by source, skills, and difficulty, alongside saves, completions, points, and skills practiced. Distinguish available feed data from actual user activity.
- **Spotify Wrapped-style results:** Create a colorful, personalized recap of completed quests, skills practiced, milestones, and next steps. Target AI-powered narrative generation grounded in activity. Include a deterministic local fallback so the demo needs no AI API; label fallback summaries accurately rather than claiming they were AI-generated.

## Sources and hackathon data
Opportunity categories: **classes, clubs, online certifications, local events, networking, job simulations, and internships**. Support local/online location or delivery-mode filters where the data provides those fields.

For this hackathon, rely on a curated **dummy document**, not external opportunity APIs. Keep a versioned fictional source document and a canonical structured seed JSON fixture derived from it. Include representative categories and difficulty levels, stable IDs, titles, descriptions, source categories, goal/skill tags, location or delivery mode, estimated effort, and linked quests/rewards.

Clearly label opportunities, providers, events, resumes, and other demo records as fictional samples. Do not imply live availability, real applications, real credentials, or verified career outcomes. No scraping, social imports, or external data integrations are required. The complete demo must work without runtime internet access or API keys. Live sources and optional AI services can be added later behind adapters.

## Design and interaction
- Mountain-climbing progress tracker with a completion animation that advances the climb when a quest is finished.
- A unique analog/digital visual system: sticky notes, paper textures, and handwritten accents paired with clear controls and readable typography.
- Colorful Spotify Wrapped-inspired rewards, analytics, and recap screens within a cohesive design.
- A responsive scrolling feed with loading, empty, error, and end-of-feed states.
- Keyboard navigation, visible focus, accessible contrast, and reduced-motion alternatives to climbing and reward animations.

## Stack and shared contract
React + Vite frontend; Python + Flask REST API; MongoDB via PyMongo. Preserve the existing persistent SQLite demo adapter when `MONGO_URI` is empty so local setup requires no database service. Keep `MONGO_URI` and optional service secrets in the ignored root `.env`, never Git. Keep one frontend API client and canonical seed JSON.

Core collections: `profiles`, `opportunities`, `quests`, `activity`. Extend the model as needed for daily quest assignments, resume-derived skill summaries, and recap metadata. Use one fictional demo profile; no login. Persist preferences, saves, completions, and progress across refreshes and restarts.

Preserve existing routes: `GET /health`, `GET /opportunities`, `GET /quests`, `GET /saved`, `GET /progress`, `POST /profiles`, `POST /saved`, and `POST /completions`. The frontend uses Vite's `/api` proxy during local development.

Extend the contract for pagination, category/location/difficulty/goal/skill filters, daily quests, resume gap recommendations, analytics, and recap generation as features are implemented. Document request/response JSON in `docs/API.md` before connecting new frontend behavior. Do not describe planned endpoints as implemented. Return clear validation and service errors, calculate rewards on the server, and keep completion retries idempotent.

## Delivery phases and proof
1. **Foundation and data:** Preserve working local startup and the app shell; establish the dummy source document, representative seed, and shared contract. Proof: both servers run, the browser loads, and no runtime external service is required.
2. **Productive scrolling:** Deliver onboarding, an incrementally loaded sample feed, filters, recommendation explanations, and saves. Proof: filters behave consistently and sample limits are clear.
3. **Daily quests and rewards:** Connect opportunities to difficulty-based quests, daily micro goals, checklists, points, and mountain-climb rewards. Proof: a fresh user completes the journey; two different quests count once each; saves and progress survive refresh and restart.
4. **Resume recommendations:** Add resume input, transparent gap suggestions, and related sample opportunities. Proof: a fictional resume produces explainable suggestions and invalid input has a recovery path.
5. **Analytics and recap:** Add opportunity breakdowns, personal activity analytics, and colorful Wrapped-style results. Proof: totals match recorded activity, empty states work, and a personalized local recap works without an AI service.
6. **Finish:** Polish responsive layouts, accessibility, animation alternatives, errors, and README setup steps. Proof: frontend build, backend journey checks, and a full browser walkthrough pass.

Integrate at every phase. Fix broken checks before expanding scope. Keep sample data explicit and recommendations grounded in available data.
