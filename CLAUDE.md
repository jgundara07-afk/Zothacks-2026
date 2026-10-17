# One Thing — ZotHacks build brief

Build from scratch during ZotHacks. Prioritize one complete demo journey.

## What we are building
**One Thing** turns unproductive scrolling into one useful step daily. A student chooses a goal, interests, and skills; browses opportunities; saves one; completes a small quest; earns points; and sees progress. Explain recommendations using matching tags. Label sample opportunities clearly; do not imply live listings. The demo must work without external APIs. Stretch: difficulty levels, analytics, and a Spotify Wrapped-style recap. Skip social imports, scraping, and chatbots.

## Stack and shared contract
React + Vite frontend; Python + Flask REST API; MongoDB via PyMongo. Keep `MONGO_URI` in `.env`, never Git. Keep seed JSON and one frontend API client. Collections: `profiles`, `opportunities`, `quests`, `activity`. Agree on request/response JSON before coding in parallel. Routes: `GET /health`, `GET /opportunities`, `GET /quests`, `GET /saved`, `GET /progress`, `POST /profiles`, `POST /saved`, `POST /completions`. Use one demo profile; no login. Return clear errors.

## Phases: frontend / backend / proof
1. **Foundation:** App shell, responsive layout, analog/sticky-note visual system / Flask health route, Mongo connection, seed data / Both servers run; browser loads.
2. **Core loop:** Onboarding, opportunity cards, save action, quest screen / Profile, feed, saved, completion routes / Fresh user completes the journey; refresh preserves it.
3. **Progress:** Mountain-climb view, points, reward moment / Progress totals and duplicate-completion protection / Two quests count once each; saved item remains.
4. **Finish:** Empty/error states, keyboard access, demo polish / Stable seed and README setup steps / Frontend build, backend smoke checks, and full browser walkthrough pass.

Integrate at every phase. Fix broken checks before expanding scope. Keep the demo profile and sample data fictional.
