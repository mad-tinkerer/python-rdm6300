# Module `rdm6300`
 
## Sub-modules

* [rdm6300.reader](#rdm6300.reader)
    
# Module `rdm6300.reader`

A python written library for an 125kHz RFID reader using the EM4100 protocol.

Copyright (C) 2020 Mad Tinkerer Me <mad.tinkerer.me@gmail.com>

All rights reserved.
 
## Classes
    
### Class `BaseReader`

> `class BaseReader(port='/dev/ttyS0', heartbeat_interval=0.5)`


Base class for event driven read operations.

*port* is a device (or anything accepted by PySerial) that is used to read data from.

*heartbeat_interval* specified the amount to wait without a card read to consider the card
    removed. (rdm6300 sends the detected card's ID reglurary to indicate that that card is till
    present)

Set *heartbeat_interval* to *None* to disable this behavior.

If you wish to use this class in your code please make sure that the *card_inserted*, *card_removed*
and *invalid_card* methods are implemented.

#### Descendants

* [rdm6300.reader.Reader](#rdm6300.reader.Reader)
* [rdm6300.test_reader.HeartbeatTestClass](#rdm6300.test_reader.HeartbeatTestClass)
    
#### Methods
    
##### Method `card_inserted`
    
> `def card_inserted(self, card)`

This method is called after a new *valid* card has been detected.

The method will be called only once for a card (so the code handels deduplication).

*card* contains the CardData for the current card.

**Tip:&ensp;Override this method in a subclass to have your own event handler logic:** 
    
##### Method `card_removed`

> `def card_removed(self, card)`

This method is called if the currently inserted card has not been seen since {self.heartbeat_interval}

**Tip:&ensp;Override this method in a subclass to have your own event handler logic.:** 
    
##### Method `close`
    
> `def close(self)`

Stop processing the card input and close the serial port

##### Method `invalid_card`
    
> `def invalid_card(self, card)`

This method is called if the currently inserted card has invalid checksum.

Please note that there's no deduplication logic here, so this might be called multiple
times for the same card.

**Tip:&ensp;Override this method in a subclass to have your own event handler logic.:** 
    
##### Method `start`
    
> `def start(self)`

Start the event loop for reading RFID cards, to control the loop please check the
 *card_inserted*, *card_removed*, *invalid_card* and *tick* methods.

##### Method `stop`
    
> `def stop(self)`


Stop the currently running read activity and signal that *start* should return ASAP
    
##### Method `tick`

> `def tick(self)`

This method is called every 100ms for custom processing code. If you need to check
other sources please use this method to put your code into.

**Tip:&ensp;Override this method in a subclass to have your own event handler logic.:** 
    
### Class `CardData`

> `class CardData(*args, **kwargs)`

CardData(value, checksum, type, is_valid)

Represents a card read event coming from the RFID reader.

**Note:&ensp;Please make sure that you are checking the is_valid flag to ensure that the id returned has proper checksum.:** 
    
#### Instance variables

##### Variable `checksum`

[int] The checksum received from the card.
    
##### Variable `is_valid`

[bool] Was the read valid (e.g. did the checksum match).

##### Variable `type`

[int] The type field for the rfid card (1st byte).
    
##### Variable `value`

[int] The card's identifier (printed on the rfid card).

### Class `Reader`

> `class Reader(port)`

Reader is a convinience wrapper for the RFID reader that can be used
to read rfid tags without writing the custom event handler methods.

*port* is a device (or anything accepted by PySerial) that is used to read data from.
    
#### Ancestors (in MRO)

* [rdm6300.reader.BaseReader](#rdm6300.reader.BaseReader)
    
#### Methods

##### Method `read`

> `def read(self, timeout=None)`

Try reading the next card id from the reader.

If timeout is set to a positive (float) value then if no card is read in that amount of time,
the call will return None.

If timeout is None the call will block until a valid card has been read or the stop() method
is called on the object.

returns: [CardData] if the read was successful or None if timeout occured

**Warning:&ensp;The call only returns valid card data and ignores cards with invalid checksums.:** 
