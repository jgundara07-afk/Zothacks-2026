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

## Resume checklist
- Inspect `git status --short` in this repo before edits.
- Finish the remaining steps, updating this file as work progresses.
- Run focused frontend tests, frontend build, and a browser walk-through of Progress and mountain selection. Check reduced-motion behavior if practical.
- Report results and any limitations; no commit or push unless asked.
