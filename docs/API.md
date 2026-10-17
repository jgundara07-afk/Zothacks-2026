# OneThing app API
All requests and responses are JSON except PDF uploads. Vite proxies `/api/...` to Flask. One shared fictional profile (`demo`), no authentication. Errors use `{ "error": "Readable message" }` and HTTP 400/404/413/503.

## Default collected mode
`ONETHING_DATA_MODE=catalog` reads the bundled, checksum-validated `backend/catalog/opportunities.json.gz`. It does not contact providers or overwrite profile/activity storage. Missing or corrupt files fail startup instead of silently substituting samples. Restart Flask after a manual export. Set `ONETHING_DATA_MODE=sample` for the explicit fictional fixture; that mode retains the original unpaginated feed contract for regression/demo use.

- `GET /health`: `{status, storage, data_mode, catalog_records}`.
- `GET /opportunities`: `{profile, checkin, opportunities, quests, total, offset, limit, has_more, data_mode, kinds}`. Default page size 40, maximum 100. Filtering happens before pagination. Each card includes a stable collected ID, `sample:false`, source URL/provider, collection time, availability, original source facts and personalization estimates. `saved`, `matching_tags`, and a matching `suggested_quest_id` are added for the app. The page embeds its quests so details and filters use the same records.

Feed filters (repeat list parameters; OR within groups, AND between groups):

| Parameter | Meaning |
| --- | --- |
| `interests`, `goals` | Exact UI labels in `shared/preferences.json`; at most three interests and three goals. `Internship` maps to the catalog software-internship goal. |
| `challenges`, `time` | Match `personalization.challenge_levels` and `personalization.time_buckets` of the full opportunity. Preparation step size remains independent. |
| `locations` | Online / Remote, On campus, In-person events, Near me. |
| `commitment` | Full opportunity commitment; A mix of both accepts either. |
| `step_size` | Any, Small, Medium, Big; selects a preparation variant. |
| `kind`, `skills` | Repeated source opportunity types or skill labels. |
| `q` | Space-separated text terms in title/description/organization/location. |
| `lat`, `lon`, `radius_km` | Near me requires finite coordinates. Default radius 25 km; maximum 500. Unknown source coordinates are excluded. |
| `offset`, `limit` | Nonnegative offset; limit 1-100. |

Normal time buckets are disjoint: under 5, [5,15), [15,30), [30,60), [60,180), and 180+ minutes. They describe the full opportunity, using source durations or labeled planning estimates. Full opportunity duration and inferred/source facts stay in `personalization.duration`. Multi-day is a planning category for the larger opportunity. Near me comes from distance to approximate City GIS points, not a claim about a trailhead or accessibility. The browser asks for location only when selected; denied access requires choosing another location or allowing access.

Past source events are excluded from discovery using export status and parseable source end dates at request time. Unknown availability remains explicitly unverified. Schools, providers and employers determine eligibility, deadlines and access; read the original source.

## Profiles and daily pace
- `POST /profiles`: `{goals: string[], interests: string[], skills: string[], preferences:{challenges:[],time:[],locations:[],commitment}}` returns `{profile}`. Up to three supported interests and three supported goals; excess selections return HTTP 400. Legacy singular `goal` and legacy interest tags remain accepted. Updates do not reset activity. Internship labels normalize on load/save. Both selection counters stop at three in the UI; old larger stored selections prefill the first three for review. All choice groups may be empty; existing skill validation still requires a nonempty skill list.
- `GET /checkins`: `{checkin, date, timezone}`.
- `POST /checkins`: `{mood:"Low"|"Okay"|"Good",effort:"small"|"medium"|"big"}`. One updatable Pacific-day check-in, requires a profile. A check-in alone earns no points. With no explicit size/time/challenge filter the daily effort is a preference for selecting a quest.

## Saves, quests and rewards
- `POST /saved` / `DELETE /saved`: `{opportunity_id}` returns `{saved, opportunity_id}`. Requires a profile; unknown IDs return 404. Save and unsave are idempotent. Existing sample IDs in persistent storage remain resolvable, but are never mixed into collected discovery.
- `GET /saved`: `{opportunities, quests}` for all bookmarks, independent of current discovery filters and date. Allows viewing a saved event after it ends; its source metadata remains visible.
- `GET /quests`: `{quests}` for saved opportunities in collected mode. Repeat `opportunity_id` to request up to 100 specific opportunities. Sample mode without IDs retains all fixture quests.
- Each collected quest has a deterministic ID (`<opportunity-id>::small|medium|big|hard|challenging|project`), `opportunity_id`, title, description, checklist `steps`, minutes, exact `time_bucket`, difficulty, size, effort, server-defined points, `daily:true`, `estimated:true`, `quest_type:"preparation"`, and `completed` for today. Generated actions cover source review, planning and preparation deliverables. They never imply completion of a source opportunity, enrollment, application, visit or physical route.
- `POST /completions`: `{quest_id}` returns `{already_completed, points_earned, progress}`. Requires a profile and saved opportunity. Rewards are calculated by the server; retries award zero extra points. Daily preparation quests can earn once per quest per Pacific day using a fresh action. Legacy fixture quests keep their once-only/daily behavior.
- `GET /progress`: points, saved/completed counts, completed IDs, activity, current/best streak, `active_today`, `today`, timezone. One or more completions on a Pacific calendar day count as one streak day.
- `GET /analytics`: progress, category/skill/difficulty counts, estimated preparation minutes, seven-day activity, top category/skill. Reads the same collected opportunity and quest IDs as the completion routes; totals reflect recorded activity, not browsing.

Profiles and activity use MongoDB when configured or local SQLite otherwise. Atomic unique activity IDs protect rewards. The catalog file is immutable during browsing; saves/completions live in the separate store. Existing progress and bookmarks survive mode switches and restarts.

## Resume suggestions
- `POST /resume-analysis`: `{text,role}`. Text must contain 1-30,000 nonblank characters; roles are Software developer, Product designer, Community organizer.
- `POST /resume-analysis/pdf`: multipart `file` and `role`. Maximum 5 MB, 20 pages, 30,000 extracted characters, 2 MB uncompressed page stream. No OCR; protected/corrupt/scanned PDFs return a clear error.
- Returns `{role,found_skills,gaps,recommendations,method}`. Suggestions reference up to 100 matching, nonexpired collected opportunities in default mode. This is local keyword matching against fictional role templates; missing words are exploration prompts, not assessed skill deficits. Raw resume text/files are neither stored nor sent to external AI.

The lower-level read-only `/catalog/options` and `/catalog/opportunities` API preserves the canonical data taxonomy and explicit full/first/micro-step scopes; see [CATALOG_API.md](CATALOG_API.md).
