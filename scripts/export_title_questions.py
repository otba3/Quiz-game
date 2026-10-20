"""Export the checked Title questions into the files the game reads.

Writes:
  output/questions_title.json  - the question bank for the Title category
  output/i18n/en.json          - English text for the translation keys
Stops with an error (and writes nothing) if any question is broken.
"""
import csv
import json
import re
from pathlib import Path

from cma_api import fetch_artwork

CSV_PATH = "data/title_questions.csv"
OUTPUT_DIR = Path("output")
QUESTION_KEY = "question.title"
ENGLISH_TEXT = {QUESTION_KEY: "What is the title of this artwork?"}


def make_context(artwork):
    """Artist (or culture if no artist) + date, e.g. 'France, c. 1500'."""
    if artwork["creators"]:
        who = artwork["creators"][0]["description"]
    else:
        who = ", ".join(artwork["culture"])
    return f"{who}, {artwork['creation_date']}"


with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

questions = []
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["TITLE API"]).group(1)
    artwork = fetch_artwork(artwork_id)
    options = [row[f"option {i}"] for i in range(1, 5)]
    image_path = f"images/{artwork['accession_number']}.jpg"

    # Safety checks: refuse to export anything broken.
    if artwork["title"] not in options:
        raise SystemExit(f"line {line_no}: real title {artwork['title']!r} is not an option")
    if not (OUTPUT_DIR / image_path).exists():
        raise SystemExit(f"line {line_no}: missing {image_path}, run prepare_images.py first")

    questions.append({
        "id": f"title-{artwork_id}",
        "question_key": QUESTION_KEY,
        "image": image_path,
        "options": options,           # kept in CSV order; the front-end shuffles
        "answer": artwork["title"],
        "context": make_context(artwork),
        "creation_date": artwork["creation_date"],   # e.g. "c. 1800s"
        "culture": ", ".join(artwork["culture"]),    # the API gives a list, we join it
    })

# Merge our text into en.json, so other categories' texts are kept.
en_path = OUTPUT_DIR / "i18n" / "en.json"
en_path.parent.mkdir(parents=True, exist_ok=True)
english = json.loads(en_path.read_text(encoding="utf-8")) if en_path.exists() else {}
english.update(ENGLISH_TEXT)

bank = {"category": "title", "questions": questions}
(OUTPUT_DIR / "questions_title.json").write_text(
    json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
en_path.write_text(json.dumps(english, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Exported {len(questions)} questions to output/questions_title.json")
