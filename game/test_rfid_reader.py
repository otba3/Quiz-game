"""Quick hardware test for the RC522 RFID reader: tap a card, see its UID.

The UID is a unique number built into every card at the factory.
We only read it (nothing is written to the card); later it becomes the
anonymous visitor ID that links a visitor's two quiz scores.
Run on the Raspberry Pi:  python3 game/test_rfid_reader.py
Stop with Ctrl+C.
"""
import time

import RPi.GPIO as GPIO
from mfrc522 import MFRC522

# RST is on GPIO 5, because the library default (GPIO 25) is used by an LED.
RST_PIN = 25

GPIO.setmode(GPIO.BCM)  # set BCM first so the library uses the same numbering as app.py
reader = MFRC522(pin_rst=RST_PIN)

print("Tap a card on the reader... (Ctrl+C to stop)")
try:
    while True:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)  # is a card near?
        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()  # read its UID
            if status == reader.MI_OK:
                # uid is a list of 5 bytes (4 UID bytes + 1 checksum); join the 4 into one number
                card_id = int.from_bytes(bytes(uid[:4]), "big")
                print("Card UID:", card_id)
                time.sleep(1)  # pause so one tap isn't printed many times
        time.sleep(0.1)
finally:
    GPIO.cleanup()  # always release the pins, even after Ctrl+C or an error
