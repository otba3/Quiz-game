"""
Quick hardware test for the RC522 RFID reader.

A window appears on the Raspberry Pi screen.
When an RFID card is detected, the screen turns green
and displays "RFID WORKS!" together with the card UID.

Run:
    /usr/bin/python3 game/test_rfid_reader.py
"""

import tkinter as tk
import RPi.GPIO as GPIO
from mfrc522 import MFRC522


# RC522 RST pin
RST_PIN = 25

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

reader = MFRC522(pin_rst=RST_PIN)


# --------------------------------------------------
# WINDOW
# --------------------------------------------------

root = tk.Tk()

root.title("RFID Test")
root.configure(bg="#222222")

# Full screen on Raspberry Pi touchscreen
root.attributes("-fullscreen", True)


title = tk.Label(
    root,
    text="RFID READER TEST",
    font=("Arial", 40, "bold"),
    fg="white",
    bg="#222222"
)

title.pack(pady=(100, 30))


status_label = tk.Label(
    root,
    text="Tap your RFID card",
    font=("Arial", 32),
    fg="white",
    bg="#222222"
)

status_label.pack(pady=30)


uid_label = tk.Label(
    root,
    text="Waiting for card...",
    font=("Arial", 24),
    fg="#cccccc",
    bg="#222222"
)

uid_label.pack(pady=20)


help_label = tk.Label(
    root,
    text="Press ESC to exit",
    font=("Arial", 16),
    fg="#999999",
    bg="#222222"
)

help_label.pack(side="bottom", pady=30)


# --------------------------------------------------
# RFID CHECK
# --------------------------------------------------

last_card = None


def check_rfid():

    global last_card

    try:

        status, _ = reader.MFRC522_Request(
            reader.PICC_REQIDL
        )

        if status == reader.MI_OK:

            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:

                card_id = int.from_bytes(
                    bytes(uid[:4]),
                    "big"
                )

                if card_id != last_card:

                    last_card = card_id

                    print("RFID WORKS!")
                    print("Card UID:", card_id)

                    # Turn screen green
                    root.configure(bg="#159447")

                    title.configure(
                        text="RFID WORKS!",
                        bg="#159447"
                    )

                    status_label.configure(
                        text="CARD DETECTED",
                        bg="#159447"
                    )

                    uid_label.configure(
                        text=f"Card UID: {card_id}",
                        bg="#159447",
                        fg="white"
                    )

                    help_label.configure(
                        bg="#159447",
                        fg="white"
                    )

                    # Return to waiting screen after 3 seconds
                    root.after(
                        3000,
                        reset_screen
                    )

    except Exception as error:

        print("RFID ERROR:", error)

        root.configure(bg="#b3261e")

        title.configure(
            text="RFID ERROR",
            bg="#b3261e"
        )

        status_label.configure(
            text=str(error),
            bg="#b3261e"
        )

        uid_label.configure(
            text="Check the RC522 wiring",
            bg="#b3261e",
            fg="white"
        )

        help_label.configure(
            bg="#b3261e"
        )


    # Check again in 100 ms
    root.after(
        100,
        check_rfid
    )


def reset_screen():

    global last_card

    last_card = None

    root.configure(bg="#222222")

    title.configure(
        text="RFID READER TEST",
        bg="#222222"
    )

    status_label.configure(
        text="Tap your RFID card",
        bg="#222222"
    )

    uid_label.configure(
        text="Waiting for card...",
        bg="#222222",
        fg="#cccccc"
    )

    help_label.configure(
        bg="#222222",
        fg="#999999"
    )


# --------------------------------------------------
# EXIT
# --------------------------------------------------

def close_test(event=None):

    print("Closing RFID test...")

    GPIO.cleanup()

    root.destroy()


root.bind(
    "<Escape>",
    close_test
)

root.protocol(
    "WM_DELETE_WINDOW",
    close_test
)


# --------------------------------------------------
# START
# --------------------------------------------------

root.after(
    100,
    check_rfid
)

try:

    root.mainloop()

finally:

    GPIO.cleanup()
