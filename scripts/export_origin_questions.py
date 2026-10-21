"""Export the checked Origin questions into the files the game reads.

Writes:
  output/questions_origin.json  - continent AND country questions, each with a "type"
  output/i18n/en.json           - adds the English texts for both question types
Rows with empty options are skipped with a warning (not finished yet).
Any other broken row stops the export (nothing is written).
"""
import csv
import json
import re
from pathlib import Path

from cma_api import fetch_artwork
from origins import COUNTRY_TO_CONTINENT, continents_in

CSV_PATH = "data/origin_questions.csv"
OUTPUT_DIR = Path("output")
ENGLISH_TEXT = {
    "question.continent": "Which continent does this artwork come from?",
    # {continent} is a placeholder: the game fills in e.g. "Europe".
    "question.country": "Which country in {continent} is this artwork?",
}


def make_context(artwork):
    """Artist (or culture if no artist) + date. Can name the place: show AFTER answering."""
    if artwork["creators"]:
        who = artwork["creators"][0]["description"]
    else:
        who = ", ".join(artwork["culture"])
    return f"{who}, {artwork['creation_date']}"


with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

questions = []
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["ORIGIN API"]).group(1)
    artwork = fetch_artwork(artwork_id)
    culture = ", ".join(artwork["culture"])
    options = [row[f"option {i}"] for i in range(1, 5)]
    answer = row["Correct"]
    image_path = f"images/{artwork['accession_number']}.jpg"

    if not all(options):
        print(f"⚠️ line {line_no}: skipped, options are empty")
        continue

    # Safety checks: refuse to export anything broken (same rules as verify_origins.py).
    if answer not in options:
        raise SystemExit(f"line {line_no}: answer {answer!r} is not an option")
    if row["Type"] == "continent" and continents_in(culture) != [answer]:
        raise SystemExit(f"line {line_no}: answer {answer!r}, culture {culture!r}")
    if row["Type"] == "country" and (answer.lower() not in culture.lower()
                                     or COUNTRY_TO_CONTINENT.get(answer) != row["Continent"]):
        raise SystemExit(f"line {line_no}: answer {answer!r} doesn't fit {culture!r}")
    if not (OUTPUT_DIR / image_path).exists():
        raise SystemExit(f"line {line_no}: missing {image_path}, run prepare_images.py origin first")

    question = {
        "id": f"origin-{artwork_id}",
        "type": row["Type"],                       # "continent" or "country"
        "question_key": f"question.{row['Type']}",
        "image": image_path,
        "options": options,                        # kept in CSV order; the front-end shuffles
        "answer": answer,
        "context": make_context(artwork),          # can name the place: show AFTER answering
    }
    if row["Type"] == "country":
        question["continent"] = row["Continent"]   # fills {continent} in the question text
    questions.append(question)

# Merge our texts into en.json, so other categories' texts are kept.
en_path = OUTPUT_DIR / "i18n" / "en.json"
en_path.parent.mkdir(parents=True, exist_ok=True)
english = json.loads(en_path.read_text(encoding="utf-8")) if en_path.exists() else {}
english.update(ENGLISH_TEXT)

bank = {"category": "origin", "questions": questions}
(OUTPUT_DIR / "questions_origin.json").write_text(
    json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")
en_path.write_text(json.dumps(english, indent=2, ensure_ascii=False), encoding="utf-8")

counts = {t: sum(q["type"] == t for q in questions) for t in ("continent", "country")}
print(f"Exported {len(questions)} questions to output/questions_origin.json {counts}")
