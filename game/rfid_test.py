#!/usr/bin/python3

from mfrc522 import SimpleMFRC522
import time

reader = SimpleMFRC522()

print("RFID Test")
print("Reader frequency: 13.56 MHz")
print("Place a card/tag near the reader...")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        card_id, text = reader.read()

        print("-------------------------")
        print("Card detected!")
        print("Card ID:", card_id)
        print("Data:", text.strip())
        print("-------------------------")

        # Prevent the same card from being instantly read repeatedly
        time.sleep(1)

except KeyboardInterrupt:
    print("\nRFID test stopped.")
