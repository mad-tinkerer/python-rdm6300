#!/usr/bin/env python

import rdm6300

class Reader(rdm6300.BaseReader):
    def card_inserted(self, card):
        print(f"card inserted {card}")

    def card_removed(self, card):
        print(f"card removed {card}")

    def invalid_card(self, card):
        print(f"invalid card {card}")

r = Reader('/dev/ttyS0')
r.start()