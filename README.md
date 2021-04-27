# Using the RDM6300 RFID reader from python

The project is primarly geared towards using the RDM6300 with a Raspberry PI and Python 3.

The unit tests are passing with Python 2, so it should work (tm), but I am using python3 for
developing the module.

In theory the module should be working with anything that is compatible with the EM4100 wire
protocol.

Please note that wiring the RDM6300 to an RPI is not entierly trivial (either it will not work, or
you are risking frying your PI), so before tring this out please make sure you had read my blog
post on this: https://mad-tinkerer-me.medium.com/rfid-with-raspberry-pi-on-the-cheap-766ae0b6c97e

The reader code has almost 100% unit test coverage, so the code should be quite stable.

If you don't want to go over the whole blog post, then here's the wiring diagram for the project:

![Wiring the RDM 6300](https://raw.githubusercontent.com/mad-tinkerer/python-rdm6300/master/docs/rdm6400-wiring_bb.png "Wiring the RDM 6300")

Note: the resistors are matching resistors, preferrably something around 1-2 kOhms


Please see the API documentation [here](API.md)

# Usage (Easy mode)

Assuming that you had wired the RDM6300 correctly you can execute the following to create a working
environment:

```
$ virtualenv -p python3 virtualenv
$ . virtualenv/bin/activate
$ pip install rdm6300
```

Afterwards you can use this code to start reading with the RFID reader (examples/simple.py):
```
import rdm6300

reader = rdm6300.Reader('/dev/ttyS0')
print("Please insert an RFID card")
while True:
    card = reader.read()
    if card:
        print(f"[{card.value}] read card {card}")
```

# Usage (Real life scenario)

see examples/complex.py

```
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

```
# Credits

The code is a rewrite of the library pyrfid: https://www.pm-codeworks.de/pyrfid.html
