from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path
import json
import random
import threading
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False


GAME_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GAME_DIR.parent
OUTPUT_DIR = PROJECT_DIR / "output"
IMAGE_DIR = OUTPUT_DIR / "images"
I18N_DIR = OUTPUT_DIR / "i18n"

QUESTIONS_PER_GAME = 6
ORIGIN_PER_TYPE = 3

GREEN_LED = 17
RED_LED = 27

QUESTION_FILES = {
    "title": "questions_title.json",
    "year": "questions_year.json",
    "medium": "questions_medium.json",
    "origin": "questions_origin.json"
}

app = Flask(__name__)


# Raspberry Pi LED setup
if GPIO_AVAILABLE:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_LED, GPIO.OUT)
    GPIO.setup(RED_LED, GPIO.OUT)

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def pick_questions(bank):
    questions = bank.get("questions", [])

    if bank.get("category") == "origin":

        continent_questions = [
            question
            for question in questions
            if question.get("type") == "continent"
        ]

        country_questions = [
            question
            for question in questions
            if question.get("type") == "country"
        ]

        selected = random.sample(
            continent_questions,
            min(
                ORIGIN_PER_TYPE,
                len(continent_questions)
            )
        )

        selected += random.sample(
            country_questions,
            min(
                ORIGIN_PER_TYPE,
                len(country_questions)
            )
        )

        random.shuffle(selected)

        return selected

    amount = min(
        QUESTIONS_PER_GAME,
        len(questions)
    )

    return random.sample(
        questions,
        amount
    )


def turn_off_leds():
    if not GPIO_AVAILABLE:
        return

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)


def flash_led(pin):
    if not GPIO_AVAILABLE:
        return

    turn_off_leds()

    GPIO.output(pin, GPIO.HIGH)

    time.sleep(1)

    GPIO.output(pin, GPIO.LOW)


# --------------------------
# MAIN TOUCHSCREEN PAGE
# --------------------------

@app.route("/")
def home():
    return render_template("index.html")


# --------------------------
# QUESTION API
# --------------------------

@app.route("/api/questions/<category>")
def get_questions(category):

    filename = QUESTION_FILES.get(category)

    if filename is None:
        return jsonify({
            "error": "Invalid category"
        }), 400

    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        return jsonify({
            "error": f"Missing file: {filename}"
        }), 404

    bank = load_json(file_path)

    questions = pick_questions(bank)

    return jsonify({
        "category": bank.get(
            "category",
            category
        ),
        "questions": questions
    })


# --------------------------
# LANGUAGE FILES
# --------------------------

@app.route("/api/translations/<language>")
def get_translations(language):

    file_path = I18N_DIR / f"{language}.json"

    if not file_path.exists():
        return jsonify({
            "error":
                f"Translation file not found: {language}.json"
        }), 404

    return jsonify(
        load_json(file_path)
    )


# --------------------------
# ARTWORK IMAGES
# --------------------------

@app.route("/quiz-images/<path:filename>")
def quiz_image(filename):

    return send_from_directory(
        IMAGE_DIR,
        filename
    )


# --------------------------
# LED CONTROL
# --------------------------

@app.route(
    "/api/led/<result>",
    methods=["POST"]
)
def control_led(result):

    if result == "correct":
        pin = GREEN_LED

    elif result == "wrong":
        pin = RED_LED

    else:
        return jsonify({
            "error": "Invalid result"
        }), 400

    # Run LED separately so the page
    # doesn't wait for the sleep().
    thread = threading.Thread(
        target=flash_led,
        args=(pin,),
        daemon=True
    )

    thread.start()

    return jsonify({
        "success": True,
        "result": result,
        "gpio_available": GPIO_AVAILABLE
    })


# --------------------------
# START SERVER
# --------------------------

if __name__ == "__main__":

    print()
    print("Starting Museum Q&A touchscreen...")
    print(f"Question folder: {OUTPUT_DIR}")
    print(f"Images folder: {IMAGE_DIR}")
    print(f"Raspberry Pi GPIO: {GPIO_AVAILABLE}")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )