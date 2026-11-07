"""Make small copies of all JPG pictures for the touchscreen.

Reads the big pictures from the "data" folder
and saves small copies in the "resized" folder.

Needs Pillow:  py -m pip install pillow
Run:           py resize_images.py
"""
from pathlib import Path

from PIL import Image, ImageOps

INPUT_FOLDER = Path("data/PICTURESArtRecall")
OUTPUT_FOLDER = Path("output/images")
# half of a 1024x600 screen, because two pictures sit side by side
MAX_SIZE = (512, 600)

OUTPUT_FOLDER.mkdir(exist_ok=True)

for picture in INPUT_FOLDER.glob("*.jpg"):
    new_picture = OUTPUT_FOLDER / picture.name

    if new_picture.exists():
        print("Already done:", picture.name)
        continue

    img = Image.open(picture)
    img = ImageOps.exif_transpose(img)  # turn photos the right way up
    # make sure it can be saved as a normal JPG
    img = img.convert("RGB")
    img.thumbnail(MAX_SIZE)             # shrink it, keeping its shape
    img.save(new_picture, quality=85)

    print("Resized:", picture.name, "->", img.size)

print("Finished.")
