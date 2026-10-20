"""A tiny terminal version of the quiz, to test the exported question banks.

It reads ONLY the files in output/ (like the real game will) and never
touches the CSV, the cache or the API.
"""
import json
import random
from pathlib import Path

# Find output/ relative to this file, so the game works from any folder.
OUTPUT_DIR = Path(__file__).parent.parent / "output"
QUESTIONS_PER_GAME = 4  # small number for testing; the real game uses 12

# The topics the player can choose: menu name -> question bank file.
TOPICS = {
    "Artwork Title": "questions_title.json",
    "Year of Creation": "questions_year.json",
}


def hint_before_answer(question, category):
    """Extra info shown WITH the question. Must never give the answer away."""
    if category == "year":
        # The date IS the answer, and titles/cultures often contain dates
        # (e.g. "Safavid period (1501-1722)"), so show nothing extra.
        return None
    return f"Created: {question['creation_date']} | Culture: {question['culture']}"


def ask_number(prompt, highest):
    """Keep asking until the player types a number from 1 to highest."""
    choice = input(prompt).strip()
    while not (choice.isdigit() and 1 <= int(choice) <= highest):
        choice = input(f"Please type a number from 1 to {highest}: ").strip()
    return int(choice)


with open(OUTPUT_DIR / "i18n" / "en.json", encoding="utf-8") as f:
    texts = json.load(f)  # translation key -> English sentence

# --- Topic menu ---
topic_names = list(TOPICS)
print("Choose a topic:")
for i, name in enumerate(topic_names, start=1):
    print(f"  {i}. {name}")
topic = topic_names[ask_number("Your choice: ", len(topic_names)) - 1]

with open(OUTPUT_DIR / TOPICS[topic], encoding="utf-8") as f:
    bank = json.load(f)

# random.sample picks N different questions in random order (no repeats).
questions = random.sample(bank["questions"], QUESTIONS_PER_GAME)
score = 0

for number, question in enumerate(questions, start=1):
    options = question["options"][:]  # [:] makes a copy, so we don't change the original
    random.shuffle(options)           # a new order every time

    print(f"\n{topic}: question {number} of {len(questions)}")
    print(texts[question["question_key"]])
    print("Image:", (OUTPUT_DIR / question["image"]).resolve())
    hint = hint_before_answer(question, bank["category"])
    if hint:  # None means "no hint for this topic"
        print(hint)
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")

    choice = ask_number("Your answer (1-4): ", 4)
    if options[choice - 1] == question["answer"]:
        score += 1
        print("Correct!")
    else:
        print("Wrong. The correct answer is:", question["answer"])
    if bank["category"] == "year":
        print("  ", question["context"])  # the date, now that the player has answered

print(f"\nFinal score: {score} of {len(questions)}")
