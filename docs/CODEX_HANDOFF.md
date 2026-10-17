# OneThing 2.0 — Claude ⇄ Codex handoff

Branch: `onething-2.0` (2.0 work only; `main` keeps 1.0, tagged `v1.0`). Jatin relays feedback between Claude and Codex.

## Assessment at the start of 2.0 (Oct 17)

The app is visually strong and the journey runs end to end, but the **biggest obstacle to a winning demo was relevance**: catalog interest tags are broad, so a product/startups profile was shown data-engineering internships at engineering firms with the reason "Entrepreneurship & Startups, Writing", and a music/creative profile got sixteen near-identical "AI content creation" courses and no music. A judge picking their own interests would see that the feed doesn't understand them.

## Pass 1 — evidence-based relevance (backend)

**Changed**
- `backend/relevance.py` (new): looks for each chosen interest (plus close synonyms) in the opportunity's own title, organization and description. Tiers: **specific** (named in title/organization), **adjacent** (only in the description, or only via catalog tags), **general** (general/wellbeing tasks; never claimed as a match). Writes a one-line reason quoting the source, e.g. "A product manager internship at TikTok, matching your interest in Product management. It also fits your goal: Internship." Excludes same-word-different-meaning hits ("Commissioning & Startup" at a power plant ≠ a startup).
- `backend/services.py` `feed_page`: an opportunity that names the interest in its own text now qualifies even if untagged (goals stay strict); ranking uses the evidence score (tag overlap only breaks ties; roles/events get a small boost over courses); results interleave two specific to one adjacent and rotate across interests and kinds so one interest can't fill the feed. Each card carries `match_tier` and `match_reason`.
- Frontend: card shows a tier badge (Specific match / Related / General step) and a **Why this** line; the points chip says what finishing does ("+65 points · moves you up your map"); the detail sheet has a Why this panel. Removed a hard-coded default of two engineering interests that leaked into any profile whose saved interests weren't in the options list.
- `backend/test_relevance.py` (new): unit tests for tiers/reasons/false positives, plus product/startups and music/creative profile tests.

**Verified**: 36/36 backend tests pass; frontend builds; both profiles checked in the browser at 390px.

Product/startups top cards now: Product Management course · Santora Pitch Lab Grand Opening (ANTrepreneur Center) · TikTok PM Intern · Robinhood Ventures intern · Walmart Product Management intern …
Music/creative: AI Content Creation for Writers · Cinematic Storytelling · AI for Audio and Music · TikTok Creator internships · a UCI poetry event …

**Known limits**: the catalog has very few music opportunities (6 titles, mostly courses); the feed says so honestly via tiers rather than inventing matches. Synonym lists cover the most likely interests, not all 500.

**Codex review request (pass 1)**: Read `backend/relevance.py` and the `feed_page` changes in `backend/services.py`. (1) Any profile where the tiering gives a misleading "Specific match"? Try 3 profiles of your choice via `GET /opportunities?interests=…&goals=…`. (2) Is the 2-specific/1-adjacent interleave plus interest rotation defensible, or does it bury the best match? (3) Any regression in paging stability (offsets must stay deterministic)?
