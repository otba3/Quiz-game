"""Small web server for the Raspberry Pi kiosk.

It serves the touchscreen game (game/web/) and the artwork images (output/),
and lights 3 RGB LEDs green/red, one per answer in turn.
A web page can't control the Pi's GPIO pins itself; this server does it for it.

Start:  py game/app.py   then open http://localhost:5000
"""
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from visitor_score_storage import (
    create_table,
    get_or_create_account_identity,
    get_points_balance,
    get_points_history,
    get_leaderboard,
    save_game_feedback,
    save_score,
    visitor_label,
)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:  # not on a Raspberry Pi (e.g. testing on a laptop): no LEDs
    GPIO_AVAILABLE = False


GAME_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GAME_DIR.parent
WEB_DIR = GAME_DIR / "web"          # the touchscreen game (your design)
OUTPUT_DIR = PROJECT_DIR / "output"  # question bank + images
LEADERBOARD_DEMO_MODE = os.environ.get(
    "LEADERBOARD_DEMO_MODE", "true"
).strip().lower() in ("1", "true", "yes", "on")
DEMO_LEADERBOARD_SCORES = {
    "daily": (11, 9, 7, 5, 3),
    "monthly": (60, 50, 40, 30, 20),
}

# One (red, green) pair of GPIO pins per RGB LED.
# Answer 1 lights LED 1, answer 2 LED 2, answer 3 LED 3, answer 4 LED 1 again...
LEDS = [
    (27, 17),  # LED 1: red = GPIO 27 (pin 13), green = GPIO 17 (pin 11)
    (22, 23),  # LED 2: red = GPIO 22 (pin 15), green = GPIO 23 (pin 16)
    (24, 16),  # LED 3: red = GPIO 24 (pin 18), green = GPIO 16 (pin 36)
]
ALL_PINS = [pin for pair in LEDS for pin in pair]

# static_folder + static_url_path="" means: game/web/css/style.css is served at /css/style.css
app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


# Raspberry Pi LED setup
if GPIO_AVAILABLE:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in ALL_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

create_table()  # make sure data/visitor_scores.db has its table

def set_led(slot, result):
    """Light LED number `slot` (0, 1 or 2) green or red. It stays on."""
    if not GPIO_AVAILABLE:
        return
    red_pin, green_pin = LEDS[slot]
    GPIO.output(red_pin, GPIO.HIGH if result == "wrong" else GPIO.LOW)
    GPIO.output(green_pin, GPIO.HIGH if result == "correct" else GPIO.LOW)


def clear_leds():
    """Switch all LEDs off, e.g. when a new game starts."""
    if not GPIO_AVAILABLE:
        return
    for pin in ALL_PINS:
        GPIO.output(pin, GPIO.LOW)


# --------------------------
# MAIN TOUCHSCREEN PAGE
# --------------------------

@app.route("/")
def home():
    return send_from_directory(WEB_DIR, "index.html")


# --------------------------
# ARTWORK IMAGES
# --------------------------

# app.js loads images from "../../output/images/...", which the browser
# turns into "/output/images/..." when the page comes from this server.
@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


# --------------------------
# LED CONTROL
# --------------------------

@app.route("/api/led/<int:slot>/<result>", methods=["POST"])
def control_led(slot, result):
    if result not in ("correct", "wrong") or not 0 <= slot < len(LEDS):
        return jsonify({"error": "Invalid LED or result"}), 400
    set_led(slot, result)
    return jsonify({"success": True, "slot": slot, "result": result,
                    "gpio_available": GPIO_AVAILABLE})


@app.route("/api/led/clear", methods=["POST"])
def clear_led_route():
    clear_leds()
    return jsonify({"success": True, "gpio_available": GPIO_AVAILABLE})


# --------------------------
# ACCOUNT CODE: SAVE SCORE
# --------------------------

@app.route("/api/account/save", methods=["POST"])
def save_account_score():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("category") not in ("year", "origin"):
        return jsonify({"error": "Invalid category"}), 400
    account_code = data.get("account_code")
    if not isinstance(account_code, str):
        return jsonify({"error": "Account code is required"}), 400
    if type(data.get("score")) is not int or data["score"] < 0:
        return jsonify({"error": "Invalid score"}), 400
    correct_question_ids = data.get("correct_question_ids")
    if (
        not isinstance(correct_question_ids, list)
        or len(correct_question_ids) > 12
        or len(correct_question_ids) != data["score"]
        or any(
            not isinstance(question_id, str)
            or not question_id
            or len(question_id) > 200
            for question_id in correct_question_ids
        )
        or len(set(correct_question_ids)) != len(correct_question_ids)
    ):
        return jsonify({"error": "Invalid correct question IDs"}), 400

    try:
        account_identity = get_or_create_account_identity(account_code)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    result = save_score(
        account_identity, data["category"], data["score"], correct_question_ids
    )
    return jsonify({
        "saved": True,
        **result,
        "visitor": visitor_label(account_identity),
        "points_balance": get_points_balance(account_identity),
        "points_history": get_points_history(account_identity),
    })


@app.route("/api/leaderboard")
def leaderboard():
    category = request.args.get("category")
    period = request.args.get("period")
    if category not in ("year", "origin"):
        return jsonify({"error": "Invalid category"}), 400
    if period not in ("daily", "monthly"):
        return jsonify({"error": "Invalid leaderboard period"}), 400
    entries = list(get_leaderboard(category, period))
    if LEADERBOARD_DEMO_MODE:
        entries.extend(
            {
                "player": f"Demo Visitor {number}",
                "score": score,
            }
            for number, score in enumerate(
                DEMO_LEADERBOARD_SCORES[period], start=1
            )
        )
        entries.sort(key=lambda entry: (-entry["score"], entry["player"]))
    return jsonify({
        "category": category,
        "period": period,
        "entries": entries,
    })


@app.route("/api/feedback", methods=["POST"])
def save_feedback():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    category = data.get("category")
    score = data.get("score")
    rating = data.get("rating")
    language = data.get("language")
    score_saved = data.get("score_saved")
    duration_seconds = data.get("duration_seconds")
    if category not in ("year", "origin"):
        return jsonify({"error": "Invalid category"}), 400
    if type(score) is not int or score < 0:
        return jsonify({"error": "Invalid score"}), 400
    if type(rating) is not int or not 1 <= rating <= 5:
        return jsonify({"error": "Rating must be between 1 and 5"}), 400
    if language not in ("en", "ar"):
        return jsonify({"error": "Invalid language"}), 400
    if type(score_saved) is not bool:
        return jsonify({"error": "score_saved must be a boolean"}), 400
    if type(duration_seconds) is not int or duration_seconds < 0:
        return jsonify({"error": "Invalid duration"}), 400

    feedback = save_game_feedback(
        category, score, rating, language, score_saved, duration_seconds,
    )
    return jsonify({"saved": True, **feedback}), 201


# Retired endpoints from the old QR/cashier flow. Keep them explicit so they
# return a clean 404 instead of Flask's generic 405 on unknown methods.
@app.route("/cashier", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def retired_cashier_endpoint():
    return jsonify({"error": "Not found"}), 404


@app.route("/api/purchase/earn", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def retired_purchase_endpoint():
    return jsonify({"error": "Not found"}), 404


@app.route("/api/card/save", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def retired_rfid_endpoint():
    return jsonify({"error": "Not found"}), 404


# --------------------------
# START SERVER
# --------------------------

if __name__ == "__main__":

    print()
    print("Starting Museum Q&A touchscreen...")
    print(f"Game folder: {WEB_DIR}")
    print(f"Question folder: {OUTPUT_DIR}")
    print(f"Raspberry Pi GPIO: {GPIO_AVAILABLE}")
    print()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,  # debug=True would let anyone on the network run code on the Pi
        use_reloader=False
    )
