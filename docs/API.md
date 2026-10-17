# Shared API contract
All requests and responses are JSON. One fixed fictional profile, `demo`. Errors: `{ "error": "Readable message" }` with 400, 404, or 503. No authentication.

- GET /health → `{status, storage}`
- POST /profiles `{goal, interests: string[], skills: string[]}` → `{profile}`. Updates preferences without resetting activity.
- GET /opportunities → `{profile: object|null, opportunities: [{id,title,organization,description,tags,kind,minutes,color,sample:true,matching_tags,saved}]}`. Matching tags use interests and skills, sorted by match count.
- GET /quests → `{quests: [{id,opportunity_id,title,description,steps:string[],points,minutes,difficulty,completed}]}`
- POST /saved `{opportunity_id}` → `{saved:true, opportunity_id}`. Idempotent.
- DELETE /saved `{opportunity_id}` → `{saved:false, opportunity_id}`. Idempotent; removes only the bookmark and preserves completed quests and points. Requires a profile; unknown opportunity IDs return 404.
- GET /saved → `{opportunities: [...]}`
- POST /completions `{quest_id}` → `{already_completed, points_earned, progress}`. Idempotent by profile and quest.
- GET /progress → `{points,completed_count,saved_count,completed_ids,activity:[{quest_id,title,points,completed_at}]}`

Mongo collections: profiles, opportunities, quests, activity. SQLite demo mode mirrors these documents locally. Saves and completions use deterministic unique activity IDs. Points are derived from completion records, never incremented separately.

## Daily pace and streaks
- GET /checkins → `{checkin: object|null, date: "YYYY-MM-DD", timezone: "America/Los_Angeles"}`.
- POST /checkins `{mood: "Low"|"Okay"|"Good", effort: "small"|"big"}` → `{checkin}`. One updatable check-in per Pacific calendar day in `activity`; requires a profile. A check-in alone does not earn points or a streak.
- GET /opportunities also returns `checkin`. With a check-in, cards include `effort`, `suggested_quest_id`, and the selected quest's `minutes`. Existing interest/skill tag ranking remains.
- Daily quests include `daily:true` and `effort`. `completed` means completed today for these quests. They can earn points once per quest per Pacific day; original quests remain once-only. Each daily practice asks for a fresh idea or action.
- GET /progress additionally returns `streak`, `longest_streak`, `active_today`, `today`, and `timezone`. A streak counts consecutive calendar days with at least one quest completion. Yesterday's streak remains available until today's end; a full missed day resets the current streak. All earned points remain.

## Career exploration
- Seed JSON now contains 11 fictional opportunities, including a class, club, certification, local event, networking exercise, job simulation, and internship preparation. Fields include `mode` (Local/Online), `goals`, and `skills`. These are sample exercises, never live listings or application links. Startup synchronizes seed definitions without resetting user activity.
- Each opportunity has four daily quest variants: Lazy (2 minutes/15 points), Easy (10–20 minutes/40–75 points), Hard (30 minutes/100 points), Challenging (45 minutes/150 points). Difficulty, type, mode, goal, skill, interest, and resume-gap filters are applied by the frontend to this local catalog. Explicit difficulty overrides check-in pace until filters reset.
- POST /resume-analysis `{text: string, role: "Software developer"|"Product designer"|"Community organizer"}` → `{role, found_skills, gaps, recommendations:[{opportunity_id,skills}], method}`. Text must contain 1–30,000 nonblank characters. Text is used only for the response and not persisted. Uses local keyword matching against fictional role templates, not AI or a proficiency assessment.
- GET /analytics → `{progress, categories, skills, difficulties, estimated_minutes, active_days, week:[{date,count,points}], top_skill, top_category, method}`. Counts derive from completion records. Estimated minutes derive from seed quest durations; they are not tracked time. The seven-day window uses Pacific dates.
- The four-slide recap is generated in the frontend from /analytics, using local templates. No AI API is called.
