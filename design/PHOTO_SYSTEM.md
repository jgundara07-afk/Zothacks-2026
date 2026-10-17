# OneThing photographic direction

## North star

Use `references/analog-scene-green-red-car.jpg` for its **scene**, not its car or colors: a candid place with foreground, middle distance, and background; tactile film grain; imperfect, lived-in detail; a striking subject that feels discovered rather than posed. Color and monochrome may coexist. The image's current crop is not a model for the UI. Preserve a clear focal point and room for type.

Every opportunity or quest photo should depict a plausible moment related to its action. A beautiful but unrelated photo weakens the product. Keep the treatment editorial and atmospheric, never a glossy stock handshake, literal fantasy quest, or repeated generic landscape.

## Source and curate

For the hackathon, hand-pick one opening hero and 8–12 images for the first visible opportunities/quests. Start with team-owned photographs where usable, then select from individual Unsplash or Pexels photo pages. Search for scenes, not abstract moods: `35mm student workshop`, `film grain desk at night`, `analog street conversation`, `grainy campus building`, `documentary making music`, `cinematic public transit`, `film photo library table`. Favor images with environmental context, layered depth, natural imperfection, and intentional negative space. Reject watermarks, embedded text, obvious logos, awkward crops, and subjects unrelated to the card.

Record for every shipped image: local filename, source page URL, photographer, source license, card/hero use, and focal point. Keep source files local under `frontend/public/images/opportunities/` so the demo does not depend on third-party image servers. References in `design/references/` are inspiration only unless separately licensed for app use. Do not use AURA or Teenage Engineering screenshots as app assets.

## Make the collection feel like one world

- Favor documentary/editorial scenes over isolated objects. Vary subject and distance so adjacent cards do not look repetitive.
- Apply one restrained treatment to all selected photos: coherent contrast and black point, slightly muted highlights, subtle grain, and a gentle dark gradient only where text overlaps. Grain should be visible at card size without crushing the image. Do not force every image to the same hue.
- Choose a focal point for each image. Use `object-fit: cover` and per-image `object-position`; do not center-crop everything. Review mobile cards, desktop cards, and the opening hero separately. Use a dedicated mobile crop for the opening hero if the desktop crop loses the subject.
- Keep text readable on a solid panel or controlled gradient; preserve accessible contrast. Provide useful alt text when the scene conveys content, empty alt when it is purely decorative.
- If a quest lacks a good matching photo, use a curated category image with similar meaning. Do not fetch a random live image per card.

## Demo image map

Use this as a visual brief, not a claim that images are already sourced:

| Quest/opportunity theme | Scene to look for |
| --- | --- |
| Find a friction / observe | candid street, transit stop, or study space with something to notice |
| Sketch a tool / build | hands sketching at a desk, workshop, maker space |
| Greener choice / compost | real urban green space, garden, or hands doing practical work |
| Write a story / kindness | notebook, small group, letter, or intimate conversation |
| Networking / coffee chat | café table or two people in an authentic setting |
| Product, design, or internship | studio desk, prototype, team workspace, or city office exterior |

## Acceptance pass

At 390px and desktop width, open the welcome screen and first 8–12 feed cards. Check that the focal subject survives cropping, the photos relate to the card titles, adjacent images differ enough to scan, text remains readable, and no missing image causes a broken card. Fix the offending photo or focal point before expanding the catalog.
