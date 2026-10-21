"""Check that each Medium question's "Correct" answer is the API's technique text.

Only reports, never changes the CSV.
"""
import csv
import re

from cma_api import fetch_artwork

CSV_PATH = "data/medium_questions.csv"

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

exact = 0
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["TECHNIQUE API"]).group(1)
    technique = fetch_artwork(artwork_id)["technique"]
    options = [row[f"option {i}"] for i in range(1, 5)]

    print(f"line {line_no} (id {artwork_id}): API technique = {technique!r}")
    if row["Correct"] not in options:
        print(f"  ❌ your answer {row['Correct']!r} is not one of the options")
    elif row["Correct"] == technique:
        exact += 1
        print("  ✅ exact match")
    elif row["Correct"].lower() == technique.lower():  # .lower() ignores capitals
        print(f"  ⚠️ only capital letters differ: you wrote {row['Correct']!r}")
    else:
        print(f"  ❌ different: you wrote {row['Correct']!r}")

print(f"\n{exact} of {len(rows)} rows match the API exactly.")
