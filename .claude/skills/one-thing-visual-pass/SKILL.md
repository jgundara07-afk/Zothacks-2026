---
name: one-thing-visual-pass
description: Use for OneThing frontend design or visual review, especially onboarding, sign-in, and photo-led quest cards. Compare the running app with the Iris reference and fix visible differences.
---

# OneThing visual pass

1. Read `design/ONBOARDING_FLOW.md`, `design/references/README.md`, and view `design/references/iris-halftone-signin-reference.png`. Identify the photographic composition, negative space, halftone use, and clear form controls. Treat reference screenshots as inspiration, not app assets.
2. Inspect the current React/Vite frontend and preserve working flows and API contracts. Implement only the smallest coherent visual slice requested.
3. Run the app and capture screenshots at narrow mobile and desktop widths, using available browser tools. Review the first screen and at least one quest/task card. Check image crop, text contrast, form legibility, consistent photo treatment, overflow, focus states, and reduced motion. Compare against the reference, list the three largest mismatches, then fix them. Repeat once.
4. Run `npm run build` from `frontend/`. Do not claim visual verification if a browser or screenshot tool was unavailable.
5. Report what changed, the screenshots/viewport sizes checked, build result, and any remaining visual gap. Do not commit or push unless asked.
