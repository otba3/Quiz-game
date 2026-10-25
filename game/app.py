"""Small web server for the Raspberry Pi kiosk.

It serves the touchscreen game (game/web/) and the artwork images (output/),
and lights 3 RGB LEDs green/red, one per answer in turn.
A web page can't control the Pi's GPIO pins itself; this server does it for it.

Start:  py game/app.py   then open http://localhost:5000
"""
import time
from flask import Flask, jsonify, request, send_from_directory
from pathlib import Path

from visitor_score_storage import create_table, get_scores, save_score

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


# The end screen sends {"category": "title", "score": 7}; we wait for a card,
# then save the score under that card and reply with its first-ever score.
@app.route("/api/card/save", methods=["POST"])
def save_card_score():
    data = request.get_json()
    card_uid = wait_for_card(CARD_WAIT_SECONDS)
    if card_uid is None:
        return jsonify({"saved": False})  # nobody tapped in time
    attempt = save_score(card_uid, data["category"], data["score"])
    first_score = get_scores(card_uid, data["category"])[0]  # this category only
    return jsonify({"saved": True, "attempt": attempt, "first_score": first_score})


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
