# Shared API contract
All requests and responses are JSON. One fixed fictional profile, `demo`. Errors: `{ "error": "Readable message" }` with 400, 404, or 503. No authentication.

- GET /health → `{status, storage}`
- POST /profiles `{goal, interests: string[], skills: string[]}` → `{profile}`. Updates preferences without resetting activity.
- GET /opportunities → `{profile: object|null, opportunities: [{id,title,organization,description,tags,kind,minutes,color,sample:true,matching_tags,saved}]}`. Matching tags use interests and skills, sorted by match count.
- GET /quests → `{quests: [{id,opportunity_id,title,description,steps:string[],points,minutes,difficulty,completed}]}`
- POST /saved `{opportunity_id}` → `{saved:true, opportunity_id}`. Idempotent.
- GET /saved → `{opportunities: [...]}`
- POST /completions `{quest_id}` → `{already_completed, points_earned, progress}`. Idempotent by profile and quest.
- GET /progress → `{points,completed_count,saved_count,completed_ids,activity:[{quest_id,title,points,completed_at}]}`

Mongo collections: profiles, opportunities, quests, activity. SQLite demo mode mirrors these documents locally. Saves and completions use deterministic unique activity IDs. Points are derived from completion records, never incremented separately.
