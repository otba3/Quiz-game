"""Check each CSV row's options against the artwork's real title from the API.

Reports, per row: which option exactly matches the real title, or the
closest option when nothing matches exactly. Fixes nothing.
"""
import csv
import difflib
import re

from cma_api import fetch_artwork

CSV_PATH = "data/title_questions.csv"

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))  # each row becomes a dict: {"Question": ..., ...}

exact = 0
for line_no, row in enumerate(rows, start=2):
    # Pull the number out of ".../api/artworks/157218?fields=title"
    match = re.search(r"/artworks/(\d+)", row["TITLE API"])
    if not match:
        print(f"line {line_no}: ❌ can't find an artwork id in {row['TITLE API']!r}")
        continue
    artwork_id = match.group(1)

    real_title = fetch_artwork(artwork_id)["title"]
    options = [row[f"option {i}"] for i in range(1, 5)]

    print(f"line {line_no} (id {artwork_id}): real title = {real_title!r}")
    if real_title in options:
        exact += 1
        print(f"  ✅ exact match: option {options.index(real_title) + 1}")
    else:
        # difflib gives a similarity score from 0.0 (nothing alike) to 1.0 (identical)
        scores = [difflib.SequenceMatcher(None, real_title, o).ratio() for o in options]
        best = scores.index(max(scores))
        label = "⚠️ near match" if scores[best] >= 0.8 else "❌ no match"
        print(f"  {label}: closest is option {best + 1} {options[best]!r}"
              f" (similarity {scores[best]:.2f})")

print(f"\n{exact} of {len(rows)} rows have an exact match.")
