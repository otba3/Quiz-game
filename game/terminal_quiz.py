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
    "Medium": "questions_medium.json",
    "Geographic Origin": "questions_origin.json",
}
ORIGIN_PER_TYPE = 3  # an Origin game = 3 continent + 3 country questions


def pick_questions(bank):
    """Choose this game's questions. random.sample never picks one twice."""
    if bank["category"] == "origin":
        continent = [q for q in bank["questions"] if q["type"] == "continent"]
        country = [q for q in bank["questions"] if q["type"] == "country"]
        chosen = random.sample(continent, ORIGIN_PER_TYPE) + random.sample(country, ORIGIN_PER_TYPE)
        random.shuffle(chosen)  # mix the two types instead of 3 + 3 in a block
        return chosen
    return random.sample(bank["questions"], QUESTIONS_PER_GAME)


def hint_before_answer(question, category):
    """Extra info shown WITH the question. Must never give the answer away."""
    if category in ("year", "origin"):
        # Year: the date IS the answer, and titles/cultures often contain dates.
        # Origin: the culture names the country (e.g. "Japan, Edo period").
        return None
    return f"Created: {question['creation_date']} | Culture: {question['culture']}"


def display(text):
    """Capitalise only the first letter, for showing on screen.

    The data keeps the API's exact text (e.g. 'oil on canvas'); this only
    changes how it looks, so all options look alike. We don't use
    .capitalize(), because it also lowercases the rest ('Color' -> 'color').
    """
    return text[:1].upper() + text[1:]


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

questions = pick_questions(bank)
score = 0

for number, question in enumerate(questions, start=1):
    options = question["options"][:]  # [:] makes a copy, so we don't change the original
    random.shuffle(options)           # a new order every time

    print(f"\n{topic}: question {number} of {len(questions)}")
    # .format() fills placeholders like {continent}; texts without one are unchanged.
    print(texts[question["question_key"]].format(continent=question.get("continent", "")))
    print("Image:", (OUTPUT_DIR / question["image"]).resolve())
    hint = hint_before_answer(question, bank["category"])
    if hint:  # None means "no hint for this topic"
        print(hint)
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {display(option)}")

    choice = ask_number("Your answer (1-4): ", 4)
    if options[choice - 1] == question["answer"]:
        score += 1
        print("Correct!")
    else:
        print("Wrong. The correct answer is:", display(question["answer"]))
    if bank["category"] in ("year", "origin"):
        print("  ", question["context"])  # safe now that the player has answered

print(f"\nFinal score: {score} of {len(questions)}")
