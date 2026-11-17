"""Export the checked Context questions into the files the game reads.

The artwork images must first be resized from data/PICTURESArtRecall into
output/images/ with scripts/resize_images.py.
"""
import csv
import json
from pathlib import Path


CSV_PATH = Path("data/context_questions.csv")
OUTPUT_DIR = Path("output")
QUESTION_KEY = "question.context"
ARABIC_TEXT = "ما سياق هذا العمل الفني؟"


def write_json(path, value):
    with path.open("w", encoding="utf-8") as file:
        file.write(json.dumps(value, indent=2, ensure_ascii=False))


with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
    rows = list(csv.DictReader(file))

if not rows:
    raise SystemExit(f"No Context questions found in {CSV_PATH}")

questions = []
question_text = None
for line_no, row in enumerate(rows, start=2):
    text = row["Question"].strip()
    answer = row["Answer"].strip()
    image_name = row["Image file name"].strip()
    options = [row[f"option {number}"].strip() for number in range(1, 5)]

    if not text or not answer or not image_name or not all(options):
        raise SystemExit(f"line {line_no}: question, answer, image, and options are required")
    if question_text is not None and text != question_text:
        raise SystemExit(f"line {line_no}: question text differs from the other rows")
    question_text = text
    if len({option.casefold() for option in options}) != len(options):
        raise SystemExit(f"line {line_no}: options must be unique")

    matching = [option for option in options if option.casefold() == answer.casefold()]
    if not matching:
        raise SystemExit(f"line {line_no}: answer {answer!r} is not an option")
    if (
        Path(image_name).name != image_name
        or "/" in image_name
        or "\\" in image_name
        or Path(image_name).suffix.lower() != ".jpg"
    ):
        raise SystemExit(f"line {line_no}: invalid image filename {image_name!r}")

    image_path = f"images/{image_name}"
    if not (OUTPUT_DIR / image_path).is_file():
        raise SystemExit(
            f"line {line_no}: missing output/{image_path}; "
            "check data/PICTURESArtRecall and run scripts/resize_images.py"
        )

    questions.append({
        "id": f"context-{line_no - 1}",
        "question_key": QUESTION_KEY,
        "image": image_path,
        "options": options,
        "answer": matching[0],
    })

en_path = OUTPUT_DIR / "i18n" / "en.json"
ar_path = OUTPUT_DIR / "i18n" / "ar.json"
english = json.loads(en_path.read_text(encoding="utf-8")) if en_path.exists() else {}
arabic = json.loads(ar_path.read_text(encoding="utf-8")) if ar_path.exists() else {}
english[QUESTION_KEY] = question_text
arabic[QUESTION_KEY] = ARABIC_TEXT

en_path.parent.mkdir(parents=True, exist_ok=True)
write_json(en_path, english)
write_json(ar_path, arabic)

bank = {"category": "context", "questions": questions}
write_json(OUTPUT_DIR / "questions_context.json", bank)
print(f"Exported {len(questions)} questions to output/questions_context.json")
