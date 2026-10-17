# One Thing — opening experience proposal

## Creative direction

Make the first minute feel like an art-directed publication about motion and possibility, with quiet game mechanics underneath. The reference images live in [`references/README.md`](references/README.md). AURA supplies the dark, emotionally charged image-plus-type composition; Teenage Engineering supplies monochrome, film-like photography, negative space, and precise details. Borrow principles, not assets or branding.

Use **one original/licensed black-and-white 35mm-style photograph** throughout the opening: an anonymous figure moving through an urban passage toward natural light, with generous negative space for text. Keep it fixed behind all steps, softened and ghosted by a charcoal gradient. As the user advances, pan the photo subtly and gradually lift its contrast; do not swap backgrounds between screens. A fine burnt-red line advances with the user. This is a sign of progress, not a literal map or fantasy quest.

Palette: charcoal `#111111`, warm paper `#EAE5DA`, muted ink `#A9A49B`, burnt red `#A23532`. Use a bold contemporary sans for instructions and an elegant italic serif only for one emphasized word per headline. Paper texture belongs on content panels, not across every pixel. Buttons and selection states must remain unmistakable.

## Screen sequence (aim: 40 seconds to first opportunity)

1. **Opening — pause the scroll.** Wide photo, almost invisible behind black. Small mark: `ONE THING / 001`. Headline: **“You don't need a five-year plan.”** Italic second line: **“Just one thing worth doing next.”** Supporting line: “Tell us what matters to you. We'll find a small place to begin.” Primary CTA: **Find my next move**. On desktop, text sits left and the figure is right; on mobile, keep the figure high and text in a solid gradient at the bottom.
2. **Direction — choose a purpose.** Same photograph, shifted slightly to expose the route ahead. Heading: **“What are you moving toward?”** Present the existing three goal values as large single-select editorial rows: `Explore my interests`, `Build my skills`, `Make an impact`. A short line under each explains the choice. Advance after selection or use a clear Continue button; keep Back visible.
3. **Identity — select signals.** Photo remains behind a warm-paper panel. Heading: **“What draws you in?”** Interest chips use the existing values: Design, Technology, Community, Sustainability, Arts. Below: **“What can you bring?”** with Writing, Coding, Research, Design. Require at least one of each, as the current API does. Make selected chips feel like red annotations on a page, not game loot.
4. **Pace — make it possible today.** Heading: **“What can today hold?”** Ask the existing mood choice (`Low`, `Okay`, `Good`) and effort choice (`small` 2-minute step; `big` 10–20-minute step). Copy: “A small step counts.” The photograph is now the clearest it has been, still subdued enough for text contrast.
5. **Reveal — one concrete action.** The red line completes; the photograph becomes the low-contrast backdrop to a single opportunity card from the actual feed. Heading: **“Start here.”** Show why it matches the selections, estimated first-step time, and one real action. Keep the fictional sample label visible in offline demo mode. CTA: **See my first step**. This leads directly to the working opportunity flow.

## Behavior and finish

- Keep the photo layer mounted across transitions; animate content and background position with restrained 300–450 ms easing. Respect `prefers-reduced-motion` with simple cuts.
- Save the existing profile values and check-in through their existing API paths. Do not invent a personalized match; use the feed's real matching data or label the choice as a sample.
- Keep state while going Back; support keyboard focus and visible selection, high contrast, and phone cropping. No autoplay sound.
- For the demo, prioritize a flawless opening-to-first-action journey over extra onboarding questions or decorative animations.
