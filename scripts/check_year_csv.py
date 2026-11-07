"""Read the Year questions CSV and report problems. Changes nothing.

Run:  py scripts/check_year_csv.py
"""
import csv
from pathlib import Path

CSV_FILE = "data/Baghdad Modern Art Group Exhibition-Checklist.csv"
# where the pictures named in the CSV are
PICTURE_FOLDER = Path("resized")

# How many options and pictures each type of question needs
RULES = {
    "which_year":     {"options": 4, "pictures": 1},
    "older":       {"options": 2, "pictures": 2},
    "in_year":     {"options": 2, "pictures": 2},
    "not_in_year": {"options": 2, "pictures": 2},
}

file = open(CSV_FILE, encoding="utf-8-sig", newline="")
all_rows = list(csv.reader(file))  # each row is a list of cells
file.close()

# The header has empty cells and a repeated name ("File of Option"),
# so we find each column by its position. Lowercase + strip = no case or space problems.
header = [cell.strip().lower() for cell in all_rows[0]]
rows = []
for row in all_rows[1:]:
    if any(value.strip() for value in row):
        rows.append(row)
print("Header:", header)

QUESTION = header.index("questions")
ANSWER = header.index("answer")
OPTIONS = [header.index(f"option {i}") for i in range(1, 5)]
TYPE = header.index("type")

# Art info: the named column, then 3 unnamed ones: artist, title, date
ART_1 = header.index("art info answer")
ART_2 = header.index("art info option")

# "File of Option" appears twice: the first is for artwork 1, the second for artwork 2
FILES = [i for i, name in enumerate(header) if name == "file of option"]


def cell(row, position):
    """The cell's text without spaces, or "" if the row is too short."""
    if position < len(row):
        return row[position].strip()
    return ""


def art_info(row, start):
    return {
        "info": cell(row, start),
        "artist": cell(row, start + 1),
        "title": cell(row, start + 2),
        "date": cell(row, start + 3),
    }


problems = []

for line, row in enumerate(rows, start=2):  # line 1 is the header
    question_type = cell(row, TYPE).lower()
    answer = cell(row, ANSWER)

    # Keep only the cells that are not empty
    options = [cell(row, i) for i in OPTIONS if cell(row, i)]
    pictures = [cell(row, i) for i in FILES if cell(row, i)]

    print(f"Line {line} [{question_type}] {cell(row, QUESTION)}")
    print("   options:  ", options)
    print("   answer:   ", answer)
    print("   pictures: ", pictures)
    print("   artwork 1:", art_info(row, ART_1))
    print("   artwork 2:", art_info(row, ART_2))

    if question_type not in RULES:
        problems.append(f"Line {line}: unknown type '{question_type}'")
        continue

    needed = RULES[question_type]
    if len(options) != needed["options"]:
        problems.append(
            f"Line {line}: has {len(options)} options, needs {needed['options']}")
    if len(pictures) != needed["pictures"]:
        problems.append(
            f"Line {line}: has {len(pictures)} pictures, needs {needed['pictures']}")
    if answer.lower() not in [option.lower() for option in options]:
        problems.append(f"Line {line}: the answer is not one of the options")
    for name in pictures:
        if not (PICTURE_FOLDER / name).exists():
            problems.append(f"Line {line}: picture not found: {name}")

print()
print(len(rows), "questions read.")
print(len(problems), "problem(s) found:")
for problem in problems:
    print("  -", problem)
