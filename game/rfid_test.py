from mfrc522 import MFRC522
import time

reader = MFRC522()

print("================================")
print(" Phone NFC Detection Test")
print(" RC522 Frequency: 13.56 MHz")
print("================================")
print()
print("Turn NFC ON on your phone.")
print("Hold the back of the phone near the RC522.")
print("Press Ctrl+C to stop.\n")

try:
    while True:

        # Look for an ISO 14443A device
        status, tag_type = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("NFC/RFID device detected!")

            # Try to get UID
            status, uid = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                uid_string = "-".join(str(x) for x in uid)

                print("UID:", uid_string)
                print("Frequency: 13.56 MHz")
                print("-----------------------------")

                time.sleep(2)

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nTest stopped.")
