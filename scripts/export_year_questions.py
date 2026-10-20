"""Export the checked Year questions into the files the game reads.

Writes:
  output/questions_year.json  - the question bank for the Year category
  output/i18n/en.json         - adds the English text for "question.year"
Rows whose date spans several centuries are skipped with a warning.
Any other broken row stops the export (nothing is written).
"""
import csv
import json
import re
from pathlib import Path

from cma_api import fetch_artwork
from centuries import artwork_centuries

CSV_PATH = "data/year_questions.csv"
OUTPUT_DIR = Path("output")
QUESTION_KEY = "question.year"
ENGLISH_TEXT = "Which century was this artwork created?"


def make_context(artwork):
    """Artist (or culture if no artist) + date. Contains the answer: show AFTER answering."""
    if artwork["creators"]:
        who = artwork["creators"][0]["description"]
    else:
        who = ", ".join(artwork["culture"])
    return f"{who}, {artwork['creation_date']}"


with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

questions = []
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["YEAR API"]).group(1)
    artwork = fetch_artwork(artwork_id)
    options = [row[f"option {i}"] for i in range(1, 5)]
    image_path = f"images/{artwork['accession_number']}.jpg"
    earliest, latest = artwork_centuries(artwork)

    # A date spanning several centuries has no single answer: skip, don't stop.
    if earliest != latest:
        print(f"⚠️ line {line_no}: skipped, date {artwork['creation_date']!r}"
              f" spans {earliest} to {latest}")
        continue

    # Safety checks: refuse to export anything broken.
    if row["Correct"] != earliest:
        raise SystemExit(f"line {line_no}: CSV says {row['Correct']!r}, API says {earliest!r}")
    if row["Correct"] not in options:
        raise SystemExit(f"line {line_no}: answer {row['Correct']!r} is not an option")
    if not (OUTPUT_DIR / image_path).exists():
        raise SystemExit(f"line {line_no}: missing {image_path}, run prepare_images.py year first")

    questions.append({
        "id": f"year-{artwork_id}",
        "question_key": QUESTION_KEY,
        "image": image_path,
        "options": options,                         # kept in CSV order; the front-end shuffles
        "answer": row["Correct"],
        "artwork_title": artwork["title"],          # safe to show with the question
        "culture": ", ".join(artwork["culture"]),   # safe to show with the question
        "context": make_context(artwork),           # contains the date: show AFTER answering
    })

# Merge our text into en.json, so other categories' texts are kept.
en_path = OUTPUT_DIR / "i18n" / "en.json"
en_path.parent.mkdir(parents=True, exist_ok=True)
english = json.loads(en_path.read_text(encoding="utf-8")) if en_path.exists() else {}
english[QUESTION_KEY] = ENGLISH_TEXT

bank = {"category": "year", "questions": questions}
(OUTPUT_DIR / "questions_year.json").write_text(
    json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
en_path.write_text(json.dumps(english, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Exported {len(questions)} questions to output/questions_year.json")
