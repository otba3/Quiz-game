"""Check that each Year question's "Correct" century agrees with the CMA API.

The century rules live in centuries.py (shared with the export script).
Only reports, never changes the CSV.
"""
import csv
import re

from cma_api import fetch_artwork
from centuries import artwork_centuries

CSV_PATH = "data/year_questions.csv"

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

ok = 0
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row["YEAR API"]).group(1)
    artwork = fetch_artwork(artwork_id)
    earliest, latest = artwork_centuries(artwork)

    print(
        f"line {line_no} (id {artwork_id}): creation_date = {artwork['creation_date']!r}")
    if earliest != latest:
        print(f"  ⚠️ date crosses centuries ({earliest} to {latest}), you decide."
              f" CSV says {row['Correct']!r}")
    elif earliest == row["Correct"]:
        ok += 1
        print(f"  ✅ {row['Correct']}")
    else:
        print(
            f"  ❌ CSV says {row['Correct']!r}, but the API date is in the {earliest}")

print(f"\n{ok} of {len(rows)} rows agree with the API.")
