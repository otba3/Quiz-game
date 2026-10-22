"""Quick hardware test for the 3 RGB LEDs: red, green, red, lit one after another.

Each LED stays on once it is lit, so at the end you see red - green - red.
Uses the same pins as app.py (BCM numbering).
Run on the Raspberry Pi:  python3 game/test_rgb_led.py
Stop early with Ctrl+C.
"""
import time

import RPi.GPIO as GPIO

# One (red pin, green pin) pair per LED, same as LEDS in app.py.
LEDS = [(27, 17), (22, 23), (24, 25)]

# The colour each LED should show, in the order they light up.
PATTERN = ["red", "green", "red"]

# Common cathode (long leg to GND): HIGH = on.
# Common anode   (long leg to 3.3V): LOW = on. If the colours look inverted, flip this.
COMMON_ANODE = False

ON = GPIO.LOW if COMMON_ANODE else GPIO.HIGH
OFF = GPIO.HIGH if COMMON_ANODE else GPIO.LOW

GPIO.setmode(GPIO.BCM)
for red_pin, green_pin in LEDS:
    GPIO.setup(red_pin, GPIO.OUT, initial=OFF)
    GPIO.setup(green_pin, GPIO.OUT, initial=OFF)

try:
    for number, ((red_pin, green_pin), colour) in enumerate(zip(LEDS, PATTERN), start=1):
        pin = red_pin if colour == "red" else green_pin
        print(f"LED {number}: {colour} on")
        GPIO.output(pin, ON)  # no OFF afterwards: it stays lit
        time.sleep(1)
    print("All three are on. Press Enter to switch them off.")
    input()
finally:
    GPIO.cleanup()  # always release the pins, even after Ctrl+C or an error
