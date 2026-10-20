# Project: Museum Quiz Game, Data Pipeline (Python) — LEARNING MODE

## How I want you to work (IMPORTANT)
This is a learning project. My goal is NOT just to get a working app; it's to
understand how to build this kind of system so I can build similar ones later.
So:
- Do NOT build the whole pipeline in one go. Work in small steps, one concept
  at a time, and stop after each step so I can read, run, and understand it.
- Before writing code for a step, explain in plain language what we're about to
  do and why, and what alternatives exist.
- Keep each step small enough that I can read all of the code in a few minutes.
  Prefer simple, readable code over clever or heavily abstracted code.
- After each step, give me a short summary: what the code does, the key concepts
  involved (e.g. pagination, caching, filtering), and one thing I could
  experiment with myself.
- Explain any library or pattern you introduce the first time it appears.
- Ask me before making design decisions; don't silently decide for me.
- Don't add features I didn't ask for (no extra categories, no front-end, no
  over-engineering). We're only doing the step I've currently asked for.

## Project context
A touchscreen quiz game for museum and exhibition visitors, running on a
Raspberry Pi with a small touchscreen, using the Cleveland Museum of Art (CMA)
Open Access API (https://openaccess-api.clevelandart.org).

Visitor flow: select language -> select category -> answer 12 questions ->
final score. Immediate feedback after each answer, the correct answer is shown
when wrong, and artwork images are shown with questions.

Categories: Artwork Title, Year of Creation, Geographic Origin
(continent + country/culture), Medium. Each category has 12 questions per
playthrough, and the bank must hold enough questions (24+) for two playthroughs
without repeats, so a replay shows new questions.

## Architecture decisions
- Python builds the data; a separate front-end (not started, stack TBD) runs
  the game.
- The game reads ONLY a local, pre-built question bank (JSON + images). No CMA
  API calls during gameplay.
- Venue internet is unknown, so the game must work fully offline.
- I write the questions by hand; the Python pipeline validates and packages them.
- Question text is stored as translation keys (English first) so more languages
  can be added later. Artwork titles are never translated.
- Only use open access (CC0) artworks that have a usable image.
- Be polite to the API (small delay between requests) and cache responses
  locally so re-runs don't hit the API again.


## Phases
- [ ] Phase 1: Artwork Title (current)
- [ ] Phase 2: Year of Creation (not started, I'll add the questions)
- [ ] Phase 3: Geographic Origin (not started)
- [ ] Phase 4: Medium (not started)
- [ ] Phase 5: Front-end and Raspberry Pi kiosk setup (not started)
  - The front-end must shuffle the options each time a question is shown
    (the JSON keeps the CSV order; the answer is stored as text, not position).


---

## Phase 1: Artwork Title

### Input
I have already designed the questions by hand, in data/title_questions.csv:
Question | Image | TITLE API | option 1 | option 2 | option 3 | option 4
- "TITLE API" is a CMA API URL like
  https://openaccess-api.clevelandart.org/api/artworks/157218?fields=title
  The number is the artwork id, and the title it returns is the CORRECT answer.
- The other options are distractors I wrote.
- "Image" is a CMA image URL.

### Goal
Turn my CSV into a clean, validated, offline-ready question bank for the Title
category: a questions JSON file plus locally saved, resized images.

### Steps (one at a time, wait for me after each)
1. Read the CSV and show me the parsed rows. Show me any data problems (see
   below); don't fix them silently.
2. Explore ONE artwork in the API with me: show the real JSON response and
   explain the fields (title, images, id, accession number, license/share
   status, etc.).
3. For each row, fetch the real title from the "TITLE API" URL and mark which
   option matches it exactly. Report mismatches (spelling, whitespace, etc.).
4. Validate the images: check from the API's image data that each artwork has a
   usable image and that my image URL is correct. Download the images, resize
   them for a small touchscreen (suggest a sensible max size), and verify each
   file opens.
5. Decide the JSON schema together, then export the question bank (question
   text key, image path, options, correct answer, optional context line from
   real metadata such as artist or culture).
6. Add simple tests for the validation logic, and explain what each test checks.

### Data problems I suspect (verify, don't assume)
- Some image URLs look malformed (e.g. "..._wejpg" instead of "..._web.jpg").
- One option contains a "✅" marker that must not end up in the data.
- At least one row has an empty option (only 3 options).
- Stray leading/trailing spaces in some cells.
- I have 11 questions but need at least 12 per playthrough, ideally 24+. Tell
  me how many more I need and help me think about how to choose additional
  artworks (I'll write them myself).
- My invented distractors may be shorter/cleaner than real CMA titles, which
  makes the correct answer easy to spot. Help me check this and suggest
  improvements (e.g. using real titles of similar artworks as distractors).