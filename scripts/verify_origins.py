"""Check each Origin question's answer against the API's "culture" text.

Continent questions: the country found in "culture" must belong to the answer.
Country questions:   the answer must appear in "culture", and belong to the
                     row's Continent column.
Rows with empty options are reported as not ready. Only reports, never changes the CSV.
"""
import csv
import re

from cma_api import fetch_artwork
from origins import COUNTRY_TO_CONTINENT, continents_in

CSV_PATH = "data/origin_questions.csv"

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

ok = not_ready = 0
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["ORIGIN API"]).group(1)
    culture = ", ".join(fetch_artwork(artwork_id)["culture"])
    options = [row[f"option {i}"] for i in range(1, 5)]
    answer = row["Correct"]

    print(f"line {line_no} ({row['Type']}, id {artwork_id}): culture = {culture!r}")
    if not all(options):
        not_ready += 1
        print("  ⏳ not ready: options are empty")
        continue
    if answer not in options:
        print(f"  ❌ answer {answer!r} is not one of the options")
        continue

    if row["Type"] == "continent":
        found = continents_in(culture)
        if found == [answer]:
            ok += 1
            print(f"  ✅ {answer}")
        else:
            print(f"  ❌ answer is {answer!r}, culture points to {found or 'no known country'}")
    else:  # country question
        if answer not in COUNTRY_TO_CONTINENT:
            print(f"  ❌ {answer!r} is missing from the table in origins.py")
        elif answer.lower() not in culture.lower():
            print(f"  ❌ answer {answer!r} does not appear in the culture")
        elif COUNTRY_TO_CONTINENT[answer] != row["Continent"]:
            print(f"  ❌ {answer} is in {COUNTRY_TO_CONTINENT[answer]}, not {row['Continent']}")
        else:
            ok += 1
            print(f"  ✅ {answer}")

print(f"\n{ok} of {len(rows)} rows OK, {not_ready} not ready (empty options).")
