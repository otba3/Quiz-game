"""Export the checked Medium questions into the files the game reads.

Writes:
  output/questions_medium.json  - the question bank for the Medium category
  output/i18n/en.json           - adds the English text for "question.medium"
Stops with an error (and writes nothing) if any question is broken.
"""
import csv
import json
import re
from pathlib import Path

from cma_api import fetch_artwork

CSV_PATH = "data/medium_questions.csv"
OUTPUT_DIR = Path("output")
QUESTION_KEY = "question.medium"
ENGLISH_TEXT = "What medium was used to create this artwork?"


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
    artwork_id = re.search(r"/artworks/(\d+)", row["TECHNIQUE API"]).group(1)
    artwork = fetch_artwork(artwork_id)
    options = [row[f"option {i}"] for i in range(1, 5)]
    image_path = f"images/{artwork['accession_number']}.jpg"

    # Safety checks: refuse to export anything broken.
    if row["Correct"] != artwork["technique"]:
        raise SystemExit(f"line {line_no}: CSV says {row['Correct']!r},"
                         f" API says {artwork['technique']!r}")
    if row["Correct"] not in options:
        raise SystemExit(f"line {line_no}: answer {row['Correct']!r} is not an option")
    if not (OUTPUT_DIR / image_path).exists():
        raise SystemExit(f"line {line_no}: missing {image_path}, run prepare_images.py medium first")

    questions.append({
        "id": f"medium-{artwork_id}",
        "question_key": QUESTION_KEY,
        "image": image_path,
        "options": options,                         # kept in CSV order; the front-end shuffles
        "answer": row["Correct"],                   # the API's exact text; the game capitalises it
        "context": make_context(artwork),
        "creation_date": artwork["creation_date"],
        "culture": ", ".join(artwork["culture"]),
    })

# Merge our text into en.json, so other categories' texts are kept.
en_path = OUTPUT_DIR / "i18n" / "en.json"
en_path.parent.mkdir(parents=True, exist_ok=True)
english = json.loads(en_path.read_text(encoding="utf-8")) if en_path.exists() else {}
english[QUESTION_KEY] = ENGLISH_TEXT

bank = {"category": "medium", "questions": questions}
(OUTPUT_DIR / "questions_medium.json").write_text(
    json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
en_path.write_text(json.dumps(english, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Exported {len(questions)} questions to output/questions_medium.json")
