"""A tiny terminal version of the quiz, to test the exported question bank.

It reads ONLY the files in output/ (like the real game will) and never
touches the CSV, the cache or the API.
"""
import json
import random
from pathlib import Path

# Find output/ relative to this file, so the game works from any folder.
OUTPUT_DIR = Path(__file__).parent.parent / "output"

with open(OUTPUT_DIR / "questions_title.json", encoding="utf-8") as f:
    bank = json.load(f)
with open(OUTPUT_DIR / "i18n" / "en.json", encoding="utf-8") as f:
    texts = json.load(f)  # translation key -> English sentence

QUESTIONS_PER_GAME = 4  # small number for testing; the real game uses 12

# random.sample picks N different questions in random order (no repeats).
questions = random.sample(bank["questions"], QUESTIONS_PER_GAME)
score = 0

for number, question in enumerate(questions, start=1):
    options = question["options"][:]  # [:] makes a copy, so we don't change the original
    random.shuffle(options)           # a new order every time

    print(f"\nQuestion {number} of {len(questions)}")
    print(texts[question["question_key"]])
    print("Image:", (OUTPUT_DIR / question["image"]).resolve())
    print("Created:", question["creation_date"], "|", "Culture:", question["culture"])
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")

    # Keep asking until the player types 1, 2, 3 or 4.
    choice = input("Your answer (1-4): ").strip()
    while choice not in ("1", "2", "3", "4"):
        choice = input("Please type 1, 2, 3 or 4: ").strip()

    if options[int(choice) - 1] == question["answer"]:
        score += 1
        print("Correct!")
    else:
        print("Wrong. The correct answer is:", question["answer"])

print(f"\nFinal score: {score} of {len(questions)}")
