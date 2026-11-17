"""Make small copies of all JPG pictures for the touchscreen.

Reads JPG files from data/PICTURESArtRecall and saves resized copies in
output/images. Run from the repository root.

Install dependencies: python3 -m pip install -r requirements.txt
Run:                  python3 scripts/resize_images.py
"""
import csv
from pathlib import Path

from PIL import Image, ImageOps

INPUT_FOLDER = Path("data/PICTURESArtRecall")
OUTPUT_FOLDER = Path("output/images")
# Year questions show two images side by side; Context questions show one.
YEAR_MAX_SIZE = (512, 600)
CONTEXT_MAX_SIZE = (1024, 600)

with open("data/context_questions.csv", encoding="utf-8-sig", newline="") as file:
    CONTEXT_IMAGES = {
        row["Image file name"].strip() for row in csv.DictReader(file)
    }

OUTPUT_FOLDER.mkdir(exist_ok=True)

for picture in INPUT_FOLDER.glob("*.jpg"):
    new_picture = OUTPUT_FOLDER / picture.name

    is_context_image = picture.name in CONTEXT_IMAGES
    if new_picture.exists() and not is_context_image:
        print("Already done:", picture.name)
        continue

    img = Image.open(picture)
    img = ImageOps.exif_transpose(img)  # turn photos the right way up
    # make sure it can be saved as a normal JPG
    img = img.convert("RGB")
    max_size = CONTEXT_MAX_SIZE if is_context_image else YEAR_MAX_SIZE
    img.thumbnail(max_size)              # shrink it, keeping its shape
    img.save(new_picture, quality=85)

    print("Resized:", picture.name, "->", img.size)

print("Finished.")
