"""Small web server for the Raspberry Pi kiosk.

It serves the touchscreen game (game/web/) and the artwork images (output/),
and lights 3 RGB LEDs green/red, one per answer in turn.
A web page can't control the Pi's GPIO pins itself; this server does it for it.

Start:  py game/app.py   then open http://localhost:5000
"""
import base64
from io import BytesIO
import os
import secrets
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
import qrcode

from visitor_score_storage import (
    create_table,
    create_purchase_point_claim,
    get_points_balance,
    get_points_history,
    get_leaderboard,
    PurchaseReferenceAlreadyUsed,
    save_game_feedback,
    save_score,
    visitor_label,
)

try:
    import RPi.GPIO as GPIO
    from mfrc522 import MFRC522
    GPIO_AVAILABLE = True
except ImportError:  # not on a Raspberry Pi (e.g. testing on a laptop): no LEDs, no card reader
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

# RC522 card reader RST wire: GPIO 25 (pin 22). LED 3 green moved to GPIO 16 to free it.
RFID_RST_PIN = 25
CARD_WAIT_SECONDS = 20  # how long the end screen waits for a card tap
FAKE_CARD_UID = 1234567890  # used on a laptop without a reader, so the screens can be tested

# static_folder + static_url_path="" means: game/web/css/style.css is served at /css/style.css
app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


# Raspberry Pi LED setup
if GPIO_AVAILABLE:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in ALL_PINS:
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
    reader = MFRC522(pin_rst=RFID_RST_PIN)

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


@app.route("/cashier")
def cashier():
    return send_from_directory(WEB_DIR, "cashier.html")


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
# RFID CARD: SAVE SCORE
# --------------------------

def wait_for_card(seconds):
    """Return the UID of the first card tapped within `seconds`, or None if no card came."""
    if not GPIO_AVAILABLE:
        time.sleep(2)  # laptop: pretend a card was tapped
        return FAKE_CARD_UID
    end_time = time.time() + seconds
    while time.time() < end_time:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)  # is a card near?
        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()  # read its UID
            if status == reader.MI_OK:
                return int.from_bytes(bytes(uid[:4]), "big")
        time.sleep(0.1)
    return None


# The end screen sends the category, score, and IDs of correctly answered
# questions; a card tap saves the result and daily leaderboard points.
@app.route("/api/card/save", methods=["POST"])
def save_card_score():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or data.get("category") not in ("year", "origin"):
        return jsonify({"error": "Invalid category"}), 400
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

    card_uid = wait_for_card(CARD_WAIT_SECONDS)
    if card_uid is None:
        return jsonify({"saved": False})  # nobody tapped in time
    result = save_score(
        card_uid, data["category"], data["score"], correct_question_ids
    )
    return jsonify({
        "saved": True,
        **result,
        "visitor": visitor_label(card_uid),
        "points_balance": get_points_balance(card_uid),
        "points_history": get_points_history(card_uid),
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


# --------------------------
# PURCHASE POINTS: ONE-TIME QR CLAIMS
# --------------------------

def purchase_staff_error():
    """Return an auth error for staff-only purchase-points operations, if any."""
    staff_token = os.environ.get("PURCHASE_POINTS_STAFF_TOKEN")
    if not staff_token:
        return jsonify({"error": "Purchase points staff access is not configured"}), 503
    supplied_token = request.headers.get("X-Staff-Token", "")
    if not secrets.compare_digest(supplied_token, staff_token):
        return jsonify({"error": "Staff authorization required"}), 401
    return None


def amount_to_minor_units(value):
    """Convert a JSON QAR amount to exact dirhams without accepting fractions."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("amount_qar must be a positive amount with at most 2 decimals")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(
            "amount_qar must be a positive amount with at most 2 decimals"
        ) from error
    minor_units = amount * 100
    if (
        not amount.is_finite()
        or amount <= 0
        or minor_units != minor_units.to_integral_value()
        or minor_units > Decimal(2**63 - 1)
    ):
        raise ValueError("amount_qar must be a positive amount with at most 2 decimals")
    return int(minor_units)


@app.route("/api/purchase/earn", methods=["POST"])
def earn_purchase_points_route():
    auth_error = purchase_staff_error()
    if auth_error:
        return auth_error
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    if data.get("paid") is not True:
        return jsonify({"error": "Payment must be confirmed before issuing points"}), 400
    purchase_reference = data.get("purchase_reference")
    if not isinstance(purchase_reference, str):
        return jsonify({"error": "purchase_reference is required"}), 400
    try:
        amount_minor = amount_to_minor_units(data.get("amount_qar"))
        result = create_purchase_point_claim(amount_minor, purchase_reference)
    except PurchaseReferenceAlreadyUsed as error:
        return jsonify({"error": str(error)}), 409
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if result["claim_code"]:
        qr = qrcode.make(result["claim_code"])
        image = BytesIO()
        qr.save(image, format="PNG")
        result["qr_image"] = (
            "data:image/png;base64,"
            + base64.b64encode(image.getvalue()).decode("ascii")
        )
    return jsonify({"saved": True, **result}), 200


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
