# Progress data handoff

`progress.json` is a point-in-time snapshot of the shared fictional demo profile. It contains recorded activity, not generated extra completions. It is safe for frontend development without a running API; it does not update automatically.

Refresh from the repository root:

```sh
.venv/bin/python backend/export_progress.py
# Optional analytics anchor, without changing the demo clock:
.venv/bin/python backend/export_progress.py --date 2026-10-17
```

For live data use the existing single frontend API client:

```js
const data = await api.progressData({date: '2026-10-17'});
// Or import the static snapshot from frontend/src:
// import data from '../../data/progress.json';
```

Both return the same schema (`schema_version: 1`):

| Field | Frontend use |
| --- | --- |
| `progress` | Lifetime points, completed/saved counts, streak, best streak, active-today state, current demo date, demo-clock metadata, completion IDs and full activity history |
| `climb` | Mountain, level, fraction up the mountain, next milestone, points to next milestone |
| `calendar` | Sorted active dates and completion counts; missing dates are inactive |
| `analytics.week` | Monday–Sunday daily bars and selected-week totals/counters |
| `analytics.month` | One bar per day and selected-month totals/counters |
| `analytics.year` | Monthly bars and selected-year totals/counters |
| `recap` | Lifetime analytics, top skill/category, estimated minutes, active days |
| `view_date`, `timezone`, `generated_at` | Analytics anchor, Pacific calendar boundaries, snapshot timestamp |

Each analytics block has `series`, `completed_count`, `points`, `active_days`, `estimated_minutes`, `categories`, `skills`, and `difficulties`. Donut percentages are each counter divided by the sum of its chart's counters. Skills can overlap. Round only for display and handle a zero denominator with an empty state. `start` is inclusive and `end` exclusive. The nested `progress` object in analytics remains lifetime data; use the block's own totals for period statistics.

For later integration: map the fields above into components, preserve activity IDs as list keys, and refetch after saving/unsaving, quest completion, or changing the demo date. Request a different `date` when navigating analytics periods. Do not write this JSON back over the database or append its records into live activity: that would replay an old snapshot. Existing mutation routes remain the source of truth and protect daily quest duplicates. Existing Progress UI endpoints remain compatible; adopting this combined payload is optional.
