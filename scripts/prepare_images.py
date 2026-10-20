"""Check, download, resize and verify the image for each CSV row.

Saves images to output/images/<accession number>.jpg, sized to fit 1024x600.
Images already in output/images/ are not downloaded again.

Usage:  py scripts/prepare_images.py title
        py scripts/prepare_images.py year
"""
import csv
import io
import re
import sys
from pathlib import Path

from PIL import Image  # Pillow: the standard Python image library

from cma_api import download_file, fetch_artwork

# What differs between categories: the CSV file and the name of its API column.
CATEGORIES = {
    "title": ("data/title_questions.csv", "TITLE API"),
    "year": ("data/year_questions.csv", "YEAR API"),
}

if len(sys.argv) != 2 or sys.argv[1] not in CATEGORIES:
    raise SystemExit(f"Usage: py scripts/prepare_images.py <{' | '.join(CATEGORIES)}>")
CSV_PATH, API_COLUMN = CATEGORIES[sys.argv[1]]

IMAGES_DIR = Path("output/images")
MAX_SIZE = (1024, 600)  # the touchscreen's resolution

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

ok = 0
for line_no, row in enumerate(rows, start=2):
    artwork_id = re.search(r"/artworks/(\d+)", row[API_COLUMN]).group(1)
    artwork = fetch_artwork(artwork_id)  # from the cache, filled by the verify scripts
    accession = artwork["accession_number"]
    print(f"line {line_no} (id {artwork_id}, {accession}):")

    # --- 1. Check the API's image data ---
    if artwork["share_license_status"] != "CC0":
        print(f"  ❌ license is {artwork['share_license_status']!r}, not CC0")
        continue
    web_image = (artwork.get("images") or {}).get("web")
    if not web_image:
        print("  ❌ the API has no web image for this artwork")
        continue
    if row["Image"] != web_image["url"]:
        print(f"  ❌ CSV image URL differs from the API's:\n"
              f"     CSV: {row['Image']}\n     API: {web_image['url']}")
        continue

    # --- 2 & 3. Download and resize (skip if we already have it) ---
    out_file = IMAGES_DIR / f"{accession}.jpg"
    if not out_file.exists():
        image = Image.open(io.BytesIO(download_file(web_image["url"])))
        image = image.convert("RGB")      # JPEG can't store transparency etc.
        image.thumbnail(MAX_SIZE)         # shrink to fit the box, keep proportions, never enlarge
        image.save(out_file, "JPEG", quality=85)

    # --- 4. Verify the saved file really is a valid image ---
    with Image.open(out_file) as saved:
        saved.verify()  # raises an error if the file is broken
    with Image.open(out_file) as saved:
        width, height = saved.size
    size_kb = out_file.stat().st_size // 1024
    print(f"  ✅ {out_file}  {width}x{height}  {size_kb} KB")
    ok += 1

print(f"\n{ok} of {len(rows)} images are ready.")
