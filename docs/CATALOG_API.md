# Collected catalog search API

These read-only routes expose `backend/catalog/opportunities.json.gz`, also used by the default core program. Vite proxies `/api/catalog/...` to Flask `/catalog/...`. A missing export returns 503 with the generation command; validation errors return 400. Use the core `/opportunities`, `/saved`, `/quests` and `/completions` routes for the integrated app lifecycle; see `docs/API.md`. Reading a catalog card alone does not create activity.

`GET /catalog/options` returns the exact versioned checklist from `opportunity_data/taxonomy.json`: 15 interests, 10 goals, five challenge levels (including Medium), seven time buckets, four location preferences, three commitment choices, and `max_selected_interests: 3`, `max_selected_goals: 3`.

`GET /catalog/opportunities` accepts:

| Parameter | Meaning |
| --- | --- |
| `q` | Case-insensitive search; all whitespace-separated words must appear in title, card description, organization, kind or location. Max 300 characters. |
| `interests` | Repeat for multiple exact interest labels. |
| `goals` | Repeat for up to three distinct exact goal labels. |
| `challenge_levels` | Repeat for Lazy, Easy, Medium, Hard or Challenging. |
| `time_buckets` | Repeat for exact labels returned by `/catalog/options`. |
| `locations` | Repeat for Online / Remote, Near me, On campus or In-person events. |
| `commitment` | One exact commitment label; A mix of both accepts either commitment type. |
| `scope` | `opportunity` (default), `first_step`, or `micro_step`; determines which time, challenge and commitment fields are filtered. |
| `lat`, `lon`, `radius_km` | Required coordinates when selecting Near me. Radius defaults to 25 km; range greater than 0 through 500. No IP geolocation or assumed user location. |
| `source`, `kind` | Optional exact source or opportunity-kind filter. |
| `include_past` | `false` by default; `true` includes historical events. |
| `offset`, `limit` | Offset defaults to 0; page size defaults to 20 and is limited to 1–100. |

Selections are **OR within a group and AND between groups**. Goal relevance is inferred; choosing a goal does not promise that an opportunity achieves it. Some records have no defensible match to any of the ten goals and keep `goals: []` rather than inventing relevance.

Response: `opportunities`, `total`, `offset`, `limit`, `scope`, and `facets`. Each card includes `match` identifying the time/challenge/commitment scope actually used and, when calculable, distance in kilometers. Facets count matching records, rather than the entire unfiltered catalog. Labels are exact; read them from the options route rather than retyping punctuation.

## Time and challenge scopes

- `opportunity` uses estimated/source-reported full opportunity duration and difficulty. Classes and employment are generally Multi-day. A short course may also use that bucket when source workload cannot be reliably parsed; this is explicitly marked estimated.
- `first_step` uses the suggested preparation action and its estimated minutes/difficulty.
- `micro_step` offers a two-minute source-review/planning action labeled Lazy and Under 5 min. This does not mean the actual course, job or trail takes two minutes.

Time intervals are half-open to avoid overlaps: Under 5 is `[0,5)`, 5–15 is `[5,15)`, 15–30 is `[15,30)`, 30–60 is `[30,60)`, 1–3 hours is `[60,180)`, 3+ hours is `[180,1440)`. Multi-day applies at 1,440 minutes or for an explicitly multi-day planning assumption. Actual elapsed event duration comes from source start/end; original course workload text is preserved.

Challenge, inferred interests/goals/skills and visit-duration assumptions are editorial estimates with evidence/basis fields. Most records use an authored rule set, not individual human review. A broad Productivity & Personal Growth fallback is explicitly flagged when no specific checklist topic is supported. This ensures every record has a valid classification without relabeling unrelated subjects as technical opportunities.

The quick-task commitment label means one session or the selected preparation action; scheduled events may require waiting, registration or payment and are not guaranteed immediately available. Long-term applies to classes, jobs, internships and other multi-day plans.

## Location and availability

Online/remote labels use source mode or explicit remote locations. On campus includes UCI catalog classes as an institutional context (class delivery still requires verification), plus events with explicit campus venue text. A ZotSpot listing with a hidden/private venue is not automatically labeled On campus or In-person events. Near me uses coordinates only; unknown locations are excluded, not silently treated as nearby. City GIS coordinates are approximate representative points, not validated entrances/trailheads. A municipal park, mapped trail segment or sports facility is a place, not an invented scheduled activity. Check official access, hours, closures, reservations and physical suitability.

Past-event status is evaluated when the export is built. Listings without an end date remain `verify_at_source`; collection timestamps remain visible, including older records retained from earlier snapshots. This is a manually refreshed catalog, not a live availability service.

## PowerShell example

```powershell
Invoke-RestMethod http://127.0.0.1:5001/catalog/options
Invoke-RestMethod 'http://127.0.0.1:5001/catalog/opportunities?source=irvine&limit=5'
Invoke-RestMethod 'http://127.0.0.1:5001/catalog/opportunities?scope=micro_step&challenge_levels=Lazy&limit=5'
Invoke-RestMethod 'http://127.0.0.1:5001/catalog/opportunities?locations=Near%20me&lat=33.7&lon=-117.8&radius_km=10&limit=5'
```
