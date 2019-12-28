#!/usr/bin/env python

import rdm6300

reader = rdm6300.Reader('/dev/ttyS0')
print("Please insert an RFID card")
while True:
    card = reader.read()
    if card:
        print(f"[{card.value}] read card {card}")