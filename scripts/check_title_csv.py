"""Step 1: read the Title questions CSV and REPORT data problems (no fixing)."""
import csv

CSV_PATH = "data/title_questions.csv"

# "utf-8-sig" = UTF-8, but drops the hidden BOM marker Excel adds at the start.
with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = list(reader)

print("Header:", header)
print(f"{len(rows)} data rows\n")

for line_no, row in enumerate(rows, start=2):  # line 1 is the header
    print(f"--- CSV line {line_no}: {len(row)} cells ---")
    for name, value in zip(header, row):
        print(f"  {name:10} | {value!r}")  # !r shows quotes, so spaces are visible
    for extra in row[len(header):]:
        print(f"  {'EXTRA':10} | {extra!r}")

    # --- Problem checks ---
    problems = []
    if len(row) != len(header):
        problems.append(f"has {len(row)} cells, expected {len(header)} (unquoted comma?)")
    if not row[1].endswith("_web.jpg"):
        problems.append(f"image URL doesn't end in _web.jpg: {row[1]}")
    for i, cell in enumerate(row):
        if cell != cell.strip():
            problems.append(f"cell {i} has leading/trailing spaces: {cell!r}")
        if cell.strip() == "":
            problems.append(f"cell {i} is empty")
        # The question text and URLs ("?fields=") legitimately contain '?'
        if "?" in cell and i != 0 and not cell.startswith("http"):
            problems.append(f"cell {i} has a '?' (lost emoji marker?): {cell!r}")
    for p in problems:
        print("  PROBLEM:", p)
    print()
