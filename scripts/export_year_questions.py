"""Export the Year questions CSV into the files the game reads.

Writes:
  output/questions_year.json  - the question bank for the Year category
  output/i18n/en.json         - adds the English question texts
Run check_year_csv.py first. Any problem stops the export (nothing is written).
The resized pictures must already be in output/images/ (same file names).

Run:  py scripts/export_year_questions.py
"""
import csv
import json
import re
from pathlib import Path

CSV_FILE = "data/Baghdad Modern Art Group Exhibition-Checklist.csv"
OUTPUT_DIR = Path("output")

# One translation key per question type
QUESTION_KEYS = {
    "which_year":  "question.year.which_year",
    "older":       "question.year.older",
    "in_year":     "question.year.in_year",
    "not_in_year": "question.year.not_in_year",
}

# Arabic question texts (the CSV only has English). DRAFT: have a native speaker check them.
ARABIC_TEXTS = {
    "question.year.which_year":  "في أي سنة صُنع هذا العمل الفني؟",
    "question.year.older":       "أي العملين أقدم؟",
    "question.year.in_year":     "أي عمل صُنع في عام {year}؟",
    "question.year.not_in_year": "أي عمل لم يُصنع في عام {year}؟",
}

# --- Read the CSV (same way as check_year_csv.py) ---
file = open(CSV_FILE, encoding="utf-8-sig", newline="")
all_rows = list(csv.reader(file))
file.close()

header = [cell.strip().lower() for cell in all_rows[0]]
rows = []
for row in all_rows[1:]:
    if any(value.strip() for value in row):
        rows.append(row)

QUESTION = header.index("questions")
ANSWER = header.index("answer")
OPTIONS = [header.index(f"option {i}") for i in range(1, 5)]
TYPE = header.index("type")
ART_1 = header.index("art info answer")   # the correct artwork
# the other artwork (2-picture questions only)
ART_2 = header.index("art info option")
FILES = [i for i, name in enumerate(header) if name == "file of option"]


def cell(row, position):
    if position < len(row):
        return row[position].strip()
    return ""


def split_languages(text):
    """'The Herd / القطيع' -> {"en": "The Herd", "ar": "القطيع"}.

    Everything before the first Arabic letter is English, the rest is Arabic.
    The Arabic letters are the Unicode range \\u0600-\\u06FF.
    """
    first_arabic = re.search(r"[؀-ۿ]", text)
    if not first_arabic:
        return {"en": text, "ar": ""}  # no Arabic: the game falls back to English
    english = text[:first_arabic.start()].strip(" /-|–,")  # remove the separator
    arabic = text[first_arabic.start():].strip()
    return {"en": english, "ar": arabic}


def artwork(row, art_column, file_column):
    """Title and date are shown AFTER answering (the date gives the answer away)."""
    return {
        "file": cell(row, file_column),
        "artist": split_languages(cell(row, art_column + 1)),
        "title": split_languages(cell(row, art_column + 2)),
        "date": split_languages(cell(row, art_column + 3)),
    }


def stop(line, message):
    raise SystemExit(f"Line {line}: {message}. Nothing was exported.")


# --- Build the questions ---
questions = []
english = {}  # translation key -> English text
count_per_type = {}

for line, row in enumerate(rows, start=2):
    question_type = cell(row, TYPE).lower()
    if question_type not in QUESTION_KEYS:
        stop(line, f"unknown type '{question_type}'")
    key = QUESTION_KEYS[question_type]

    # Take the year out of the text: "made in 1850?" -> "made in {year}?"
    text = cell(row, QUESTION)
    values = {}
    if question_type in ("in_year", "not_in_year"):
        found = re.search(r"\d{3,4}", text)
        if not found:
            stop(line, "no year found in the question text")
        values["year"] = found.group()
        text = text.replace(found.group(), "{year}")

    # All questions of one type must share the same English text
    if key in english and english[key] != text:
        stop(line, f"text differs from the other '{question_type}' questions:\n"
             f"   '{text}'\n   '{english[key]}'")
    english[key] = text

    options = [cell(row, i) for i in OPTIONS if cell(row, i)]
    answer = cell(row, ANSWER)
    # Use the option's own spelling, so the answer matches it exactly
    matching = [option for option in options if option.lower() ==
                answer.lower()]
    if not matching:
        stop(line, f"answer '{answer}' is not one of the options")

    if question_type == "which_year":
        artworks = [artwork(row, ART_1, FILES[0])]
    else:
        artworks = [artwork(row, ART_1, FILES[0]),
                    artwork(row, ART_2, FILES[1])]
        # For 2 pictures the options ARE the pictures: use the file names.
        # The first file (next to "Art Info Answer") is the correct one.
        options = [art["file"] for art in artworks]
        matching = [artworks[0]["file"]]

    for art in artworks:
        if not (OUTPUT_DIR / "images" / art["file"]).exists():
            stop(
                line, f"missing output/images/{art['file']}, run resize_images.py first")

    count_per_type[question_type] = count_per_type.get(question_type, 0) + 1
    questions.append({
        "id": f"year-{question_type}-{count_per_type[question_type]}",
        "type": question_type,
        "question_key": key,
        "question_values": values,
        "images": ["images/" + art["file"] for art in artworks],
        "options": options,        # CSV order; the front-end shuffles
        "answer": matching[0],
        "artworks": artworks,      # artworks[0] is always the correct one
    })

# --- Write the files ---
en_path = OUTPUT_DIR / "i18n" / "en.json"
# creates output/ and output/i18n/ if missing
en_path.parent.mkdir(parents=True, exist_ok=True)
all_english = json.loads(en_path.read_text(
    encoding="utf-8")) if en_path.exists() else {}
all_english.update(english)  # keep the other texts, add/replace ours
en_path.write_text(json.dumps(all_english, indent=2,
                   ensure_ascii=False), encoding="utf-8")

# Same for Arabic
ar_path = OUTPUT_DIR / "i18n" / "ar.json"
all_arabic = json.loads(ar_path.read_text(
    encoding="utf-8")) if ar_path.exists() else {}
all_arabic.update(ARABIC_TEXTS)
ar_path.write_text(json.dumps(all_arabic, indent=2,
                   ensure_ascii=False), encoding="utf-8")

bank = {"category": "year", "questions": questions}
(OUTPUT_DIR / "questions_year.json").write_text(
    json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Exported {len(questions)} questions to output/questions_year.json")
print("Per type:", count_per_type)
