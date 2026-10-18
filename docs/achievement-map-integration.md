# Achievement map integration work log

## Goal
Use the v2 parchment mountain and moving checkmark as the visible map for v1's permanent, activity-backed achievements. A mountain represents one achievement; the checkmark position must use that achievement's `progress / target`, and reach the summit when it unlocks. Keep the point climb in the quest reward where it still explains points.

## Starting state (2026-10-17)
- The v2 `Atlas.jsx` and CSS were copied into v1 but are uncommitted. It currently shows point-based chapters. Its animated `Climb.jsx` still uses `progress.points` and 100-point milestones.
- v1's `MountainMap.jsx` shows 95 achievements in selectable regions, but `App.jsx` hides it in a collapsed badge journal below the v2 map. The two views are unrelated.
- The API already returns each badge's `id`, `name`, `number`, `region`, `criteria`, `progress`, `target`, `unlocked`, and `earned_at` in `/progress`.
- The existing working tree also has interest-form styling and two screenshots from the preceding request. Preserve these edits. Do not push without a request.

## Steps
1. Inspected `Atlas`, `Climb`, `MountainMap`, achievement catalog and API shape. Chosen approach: extend the v2 climb to accept an achievement while retaining its point mode for reward UI; place the achievement mountain selector in the same visible atlas. Selecting a mountain drives the animated climb and its detail view.
2. Added `frontend/src/utils/achievementMap.js` for a clamped achievement fraction and a sensible featured mountain. The first unfinished mountain with meaningful progress is featured; otherwise the most recently earned mountain, then the first unfinished mountain.
3. Extended the existing v2 `Climb.jsx` with optional achievement mode. In Progress, its animated marker and filled trail use the selected badge's `progress / target`; unlocked badges reach the peak. Its point mode still powers the quest reward modal.
4. Changed `Atlas.jsx` to show the climb and v1 region-based `MountainMap` in one visible map. Selecting a mountain updates the climb and opens its details. Newly earned badges become the selected mountain. Removed the duplicate hidden MountainMap from the badge journal, which still contains the badge collection.
5. Added active-mountain styling and a visible focus outline. Verification pending.
6. Added streak-loss descent after the follow-up request: the animated trail marker stays at the achievement's saved fraction through the next day, then descends 25% of that height for each missed day. At five days since the last completed quest it reaches the valley. Completing a quest restores its position. The badge's stored progress and unlocked state remain unchanged; the UI labels the route as temporary momentum.
7. Increased filter label contrast and made the sticky Reset/Apply action bar span the entire sheet width with readable button text. Verification pending.
8. Verified in the running v1 browser on a 1280 × 720 desktop viewport with its 480px phone shell: Progress showed Base Camp Alpha at 835/1000 stored progress and the animated checkmark at 21% trail momentum after four idle days. The achievement selector opened The 1% Club (2/7 progress), and returning to the map changed the climb to that mountain. Filters showed dark, readable labels and an edge-to-edge bottom action bar. Captured `docs/demo-achievement-map.png` and `docs/demo-filter-contrast-footer.png`.
9. Focused unit tests and the frontend production build passed. The unit test covers one missed day, first descent at two days, valley after five days, and recovery after completing a quest. Final full frontend check and Git sync pending.
10. Fetched GitHub and fast-forwarded from `c45d758` to `636f1d4`, preserving a safety stash named `Achievement momentum and filter footer before upstream sync`. The upstream map removed the period ledger. Resolved the Atlas overlap by keeping that leaner map and adding only the new momentum calculation. Recheck and push pending.
11. After resolving the overlap: 23 frontend tests and 58 backend tests passed, the frontend production build passed, and `git diff --check` was clean. Reloaded the merged UI and reconfirmed the 21% descent, permanent 835/1000 achievement progress, region map, readable filter labels, and edge-to-edge actions. Replaced both screenshots with post-merge captures.
12. Restarted the local v1 Flask server on port 5001 with the pulled backend code; `/health` returned `status: ok`, SQLite storage, and 11,314 catalog records. The v1 Vite frontend remains on port 5173.
13. Re-fetched GitHub, confirmed `origin/main` was an ancestor of local `main`, then committed the implementation as `a4bc4e2` and pushed it successfully. Local `HEAD` and `origin/main` both resolved to `a4bc4e2`; the working tree was clean. GitHub reported a repository redirect to `spencertamashiro/Zothacks-2026`, but accepted the push through the existing origin URL.

## Resume checklist
- Inspect `git status --short` in this repo before edits.
- Finish the remaining steps, updating this file as work progresses.
- Run focused frontend tests, frontend build, and a browser walk-through of Progress and mountain selection. Check reduced-motion behavior if practical.
- Report results and any limitations; no commit or push unless asked.
