# OneThing — frontend onboarding build brief

This is the current screen-by-screen direction for the first-run experience. Build on the existing React/Vite app and preserve its working feed and API contract. The fuller research and source links are in [`../design/ONBOARDING_RESEARCH_AND_FLOW.md`](../design/ONBOARDING_RESEARCH_AND_FLOW.md).

## Visual anchor

View [`../design/references/iris-halftone-signin-reference.png`](../design/references/iris-halftone-signin-reference.png) before editing. Borrow its **composition**, not its logo or subject: a distinctive ghosted black-and-white photograph high in the frame/background; a calm, precise foreground panel; a restrained halftone-treated image; excellent negative space and legible controls. On mobile, let the photo-led upper portion fade naturally into the controls below. The mood is cinematic, analog, grainy, dark, and interesting without brutalist UI. Keep one restrained burnt-red accent. Use original or properly licensed imagery in the app; screenshots in `design/references/` are design references, not assets to ship.

Keep the same photographic scene through the welcome and story, shifting crop or contrast subtly as the user advances. The first quest photo then takes over during the reveal. Respect reduced-motion preferences.

## Flow: six screens, then the real feed

| Step | Screen and exact intent | Primary action |
| --- | --- | --- |
| 0 | **Welcome / entry.** Brand mark `ONE THING`; headline **“A place to start.”** Use the Iris photo-and-panel composition. Show a clear secondary log-in path only if real authentication exists. The current demo has no auth, so offer a working guest path rather than a fake sign-in form. | **Get started** |
| 1 | **Problem.** Same ghosted photograph, reframed. Two short beats: **“The internet gives you endless possibilities.”** then **“It rarely gives you a starting point.”** Avoid guilt, fabricated numbers, or claiming to know the user. | **Show me another way** |
| 2 | **Promise.** One beautiful example quest card demonstrates the product: **“One useful thing, small enough to start today.”** Show a category, estimated time, and concrete first action. If it uses fictional seed data, label it as a sample. | **Find mine** |
| 3 | **Goal.** **“What are you moving toward?”** Single-select the existing values: `Explore my interests`, `Build my skills`, `Make an impact`. Give each a short plain-language explanation. | **Continue** |
| 4 | **Interests.** **“What draws you in?”** Choose at least one of the existing interests. Include a compact **“What could you bring or practice?”** choice for at least one existing skill, because the current profile API requires both. Use photo tiles or restrained editorial rows rather than a crowded chip wall. | **Continue** |
| 5 | **Preferences.** **“What can today hold?”** Choose a small 2-minute or bigger 10–20-minute step. Offer online/nearby only where matching feed data exists. Keep mood in the daily feed check-in, where it can change tomorrow. | **Show my one thing** |
| 6 | **Reveal → feed.** **“Start here.”** Show one matched quest with a relevant photo, why it fits the selections, its time, source/sample label, and first real action. On activation, carry that *same card* into the top of the actual scrolling feed while navigation and other cards appear. No dead-end “all set” page. | **Explore the feed** |

Back and Skip must remain available through the story. Keep selections when navigating Back. Aim for about 45–60 seconds from entry to first quest; shorten transitions if they make the demo feel slow.

## Connect to what already works

- The current app persists `goal`, `interests`, and `skills` through its profile route. Keep these existing values and validation.
- Daily `mood` and `effort` use the check-in route. Save the effort choice there if it is collected during onboarding; leave mood for the daily check-in unless the API requires it.
- Delivery mode is currently a feed filter, not a permanent profile field. Apply a chosen mode to that filter without claiming it was saved as a profile preference.
- Match the first quest using the real feed/matching data. If using offline fixtures, label them as samples. Do not invent a personalized result or a functional sign-up flow.
- Every quest/task card in the feed should eventually have a relevant aesthetic editorial photograph, consistent crop and grain, readable overlay, and useful source/action text. Prefer a small curated set for the demo over random imagery.

## Definition of done for this hackathon

The opening looks intentional at narrow phone and desktop widths; each choice is keyboard-accessible; Back works; the profile values persist; the reveal leads into a working feed; saving and starting a quest still work; sample/live labels are honest; `npm run build` succeeds. Capture screenshots of the welcome screen and first feed card at both widths and compare them with the Iris composition before calling the UI finished.
