# OneThing onboarding: reference set and buildable flow

The visual anchor is `references/iris-halftone-signin-reference.png`. Use the references for specific ideas, not their branding, copy, or assets.

## Five references

1. **Iris sign-in reference (local)** — `references/iris-halftone-signin-reference.png`. Borrow the precise foreground form over a ghosted atmospheric photograph, with a separate halftone image on the panel. This is the composition to beat for the first screen.
2. **AURA — Feel Alive Again** — https://apps.apple.com/us/app/aura-feel-alive-again/id6738584485 . Borrow the dark, image-led, emotionally charged presentation of small actions. The App Store images are marketing screenshots, not a verified capture of its current first-run flow.
3. **Opal onboarding** — https://www.lazyweb.com/flow/opal/onboarding . Borrow the short pain-to-possibility sequence and one question at a time. Avoid invented statistics or guilt-heavy copy; the problem here is paralysis from endless possibilities, not screen time itself.
4. **Stoic onboarding** — https://screensdesign.com/showcase/journal-mental-health-stoic . Borrow the transition from a brief personalization quiz straight into the first real action. Do not strand the user on a generic “all set” screen.
5. **Cosmos onboarding** — https://screensdesign.com/apps/cosmos-curated-inspiration/ . Its captured flow moves from welcome and account entry to interest categories, feed creation, and visual discovery. Borrow the handoff from choices into an image-led feed; it is a functional reference, not the monochrome art direction.

## Proposed sequence (about 45–60 seconds to first quest)

**0. Opening / account entry.** The Iris composition: ghosted full-bleed black-and-white photograph high in the frame; quiet off-white panel; halftone image opposite the controls on desktop. Mark `ONE THING`. Line: **“A place to start.”** Primary **Get started**; secondary **Log in** only if real authentication exists. The current demo has no auth, so use **Continue as guest** rather than a fake sign-in button. Let the photo fade into the controls on mobile.

**1. The problem.** Keep the same photograph, reframed. Large line: **“The internet gives you endless possibilities.”** Advance to **“It rarely gives you a starting point.”** This can be two short beats in one screen, not two forms. CTA **Show me another way**. Skip and Back remain visible. No unsupported claims about the user.

**2. The promise.** Show one beautiful example quest photograph and a concrete micro-action. Line: **“One useful thing, small enough to start today.”** Sample card shows category, estimated time, and first action; visibly mark fictional demo content as sample. CTA **Find mine**. This teaches the product before asking questions.

**3. Goal (parameter 1).** **“What are you moving toward?”** Single-select the existing three API values: Explore my interests / Build my skills / Make an impact. Editorial photo header, large readable rows, one-line explanations. Selection immediately advances or enables Continue.

**4. Interests (parameter 2).** **“What draws you in?”** Choose at least one existing interest. Below, a compact **“What could you bring or practice?”** group captures at least one existing skill, as the API currently requires. Use selected photo tiles or clean annotated rows; avoid a wall of chips.

**5. Preferences (parameter 3).** **“What can today hold?”** Choose small (2-minute) or bigger (10–20-minute) effort, plus Anywhere / Online / Nearby if the feed has matching data. Save effort through the existing check-in route and apply delivery mode as a feed filter. Ask mood later in the daily feed check-in rather than freezing a daily state into permanent onboarding.

**6. Reveal → actual feed.** A single matched quest card appears: **“Start here.”** Show a plain-language reason tied to the selected goal/interests/skills, the real first step, and source/sample label. **Explore the feed** transitions into the existing scrolling feed with this card at the top; keep the card’s photograph and typography consistent so it feels like the same scene opening outward. Preserve Save, filters, and quest action. Do not claim personalization if match logic has not run.

## Build notes

- The existing app persists `goal`, `interests`, and `skills`; the daily check-in persists `mood` and `effort`; delivery mode is currently a feed filter. Preserve these contracts.
- Keep a single photographic language across onboarding and every quest/task card: relevant editorial image, 3:4 or 4:5 crop, controlled grain, deep shadow with detail, legible text treatment. Reference screenshots are not licensed app assets.
- Animate the background subtly, with reduced-motion fallback. Every step must work with keyboard, Back, refresh, and narrow mobile width.
- Prioritize the opening, three choices, and the first-card-to-feed transition. If time is short, cut animation complexity before cutting the working feed.
