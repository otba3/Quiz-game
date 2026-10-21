"""Small web server for the Raspberry Pi kiosk.

It serves the touchscreen game (game/web/) and the artwork images (output/),
and switches the green/red LEDs when the game reports an answer.
A web page can't control the Pi's GPIO pins itself; this server does it for it.

Start:  py game/app.py   then open http://localhost:5000
"""
from flask import Flask, jsonify, send_from_directory
from pathlib import Path
import threading
import time

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:  # not on a Raspberry Pi (e.g. testing on a laptop): no LEDs
    GPIO_AVAILABLE = False


GAME_DIR = Path(__file__).resolve().parent
PROJECT_DIR = GAME_DIR.parent
WEB_DIR = GAME_DIR / "web"          # the touchscreen game (your design)
OUTPUT_DIR = PROJECT_DIR / "output"  # question bank + images

GREEN_LED = 17
RED_LED = 27

# static_folder + static_url_path="" means: game/web/css/style.css is served at /css/style.css
app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")


# Raspberry Pi LED setup
if GPIO_AVAILABLE:
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(GREEN_LED, GPIO.OUT)
    GPIO.setup(RED_LED, GPIO.OUT)

    GPIO.output(GREEN_LED, GPIO.LOW)
    GPIO.output(RED_LED, GPIO.LOW)


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
