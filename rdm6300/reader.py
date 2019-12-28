#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A python written library for an 125kHz RFID reader using the EM4100 protocol.

Copyright (C) 2020 Mad Tinkerer Me <mad.tinkerer.me@gmail.com>

All rights reserved.
"""

from serial import Serial, EIGHTBITS
import logging
import os
import time
import struct

from collections import namedtuple

__pdoc__ = {}
CardData = namedtuple('CardData', ['value', 'checksum', 'type', 'is_valid'])
__pdoc__['CardData'] = """CardData(value, checksum, type, is_valid)

Represents a card read event coming from the RFID reader.

.. note:: Please make sure that you are checking the is_valid flag to ensure that the id returned has proper checksum.
"""
__pdoc__['CardData.value'] = "[int] The card's identifier (printed on the rfid card)."
__pdoc__['CardData.is_valid'] = "[bool] Was the read valid (e.g. did the checksum match)."
__pdoc__['CardData.checksum'] = "[int] The checksum received from the card."
__pdoc__['CardData.type'] = "[int] The type field for the rfid card (1st byte)."

class BaseReader(object):
    """
    Base class for event driven read operations.

    *port* is a device (or anything accepted by PySerial) that is used to read data from.

    *heartbeat_interval* specified the amount to wait without a card read to consider the card
        removed. (rdm6300 sends the detected card's ID reglurary to indicate that that card is till
        present)

    Set *heartbeat_interval* to *None* to disable this behavior.

    If you wish to use this class in your code please make sure that the *card_inserted*, *card_removed*
    and *invalid_card* methods are implemented.
    """

    _RFID_STARTCODE = 0x02
    _RFID_ENDCODE = 0x03

    def __init__(self, port='/dev/ttyS0', heartbeat_interval=0.5):
        self.quit_reader = False
        self.port = port
        self.serial = Serial(port=port, baudrate=9600, bytesize=EIGHTBITS, timeout=0.1)
        self.last_read_at = None
        self.card = None
        self.current_fragment = []
        self.heartbeat_interval = heartbeat_interval

    def close(self):
        """ Stop processing the card input and close the serial port """
        if self.serial and self.serial.is_open:
            self.serial.close()

        self.stop()

    def stop(self):
        """ Stop the currently running read activity and signal that *start* should return ASAP """
        self.quit_reader = True

    def start(self):
        """
        Start the event loop for reading RFID cards, to control the loop please check the
         *card_inserted*, *card_removed*, *invalid_card* and *tick* methods.
        """
        self._read()

    def _read(self):
        self.quit_reader = False
        while not self.quit_reader:
            received_bytes = self.serial.read()
            if received_bytes and len(received_bytes) > 0:
                recieved_byte = received_bytes[0]
                assert len(received_bytes) == 1

                if recieved_byte == BaseReader._RFID_STARTCODE:
                    if len(self.current_fragment) > 0:
                        self._process_fragment(self.current_fragment)
                        self.current_fragment = []
                elif recieved_byte == BaseReader._RFID_ENDCODE:
                    if len(self.current_fragment) > 0:
                        self._process_fragment(self.current_fragment)
                        self.current_fragment = []
                else:
                    try:
                        fragment = int(received_bytes.decode('ascii'), 16)
                        self.current_fragment.append(fragment)

                    except ValueError:
                        logging.warning("[{port}] got trash resetting rfid read to assume we are at the begining".format(port=self.port))
                        self.current_fragment = []

            self._process_heartbeat()
            self.tick()

    @staticmethod
    def _fragment_to_int(fragment, bits_per_item=4):
        value = 0
        for item in fragment:
            value = value << bits_per_item
            value = value | item

        return value

    @staticmethod
    def _parse_fragment(read_fragment):
        if len(read_fragment) != 12:
            return None

        # Calculates packet checksum
        calculatedChecksum = 0
        for i in range(0, 10, 2):
            byte = read_fragment[i] << 4
            byte = byte | read_fragment[i + 1]
            calculatedChecksum = calculatedChecksum ^ byte

        # Gets received packet checksum
        receivedChecksum = BaseReader._fragment_to_int(read_fragment[10:12])

        card_data = CardData(
            value=BaseReader._fragment_to_int(read_fragment[2:10]),
            checksum=receivedChecksum,
            is_valid=receivedChecksum == calculatedChecksum,
            type=BaseReader._fragment_to_int(read_fragment[0:2]))

        return card_data

    def _process_fragment(self, read_fragment):
        new_fragment = self._parse_fragment(read_fragment)

        if not new_fragment:
            return None

        if not new_fragment.is_valid:
            self.last_read_at = time.time()
            self.invalid_card(new_fragment)
            return

        self.last_read_at = time.time()
        if new_fragment != self.card:
            self.card = new_fragment
            self.card_inserted(new_fragment)

    def _process_heartbeat(self):
        if self.last_read_at:
            if self.heartbeat_interval and time.time() - self.last_read_at > self.heartbeat_interval:
                self.card_removed(self.card)
                self.card = None
                self.last_read_at = None

    # Default event handlers can be overriden
    def card_inserted(self, card):
        """
        This method is called after a new *valid* card has been detected.

        The method will be called only once for a card (so the code handels deduplication).

        *card* contains the CardData for the current card.

        .. tip:: Override this method in a subclass to have your own event handler logic
        """
        pass

    def card_removed(self, card):
        """
        This method is called if the currently inserted card has not been seen since {self.heartbeat_interval}

        .. tip:: Override this method in a subclass to have your own event handler logic.
        """
        pass

    def invalid_card(self, card):
        """
        This method is called if the currently inserted card has invalid checksum.

        Please note that there's no deduplication logic here, so this might be called multiple
        times for the same card.

        .. tip:: Override this method in a subclass to have your own event handler logic.
        """
        logging.warning("[{port}] invalid card detected {card}".format(port=self.port, card=card))

    def tick(self):
        """
        This method is called every 100ms for custom processing code. If you need to check
        other sources please use this method to put your code into.

        .. tip:: Override this method in a subclass to have your own event handler logic.
        """
        pass


class Reader(BaseReader):
    """ Reader is a convinience wrapper for the RFID reader that can be used
    to read rfid tags without writing the custom event handler methods.

    *port* is a device (or anything accepted by PySerial) that is used to read data from.
    """

    def __init__(self, port):
        super().__init__(port, heartbeat_interval=None)
        self.successful_read_deadline = None

    def start(self):
        raise RuntimeError("Simple reader does not support start method")

    def read(self, timeout=None):
        """ Try reading the next card id from the reader.

        If timeout is set to a positive (float) value then if no card is read in that amount of time,
        the call will return None.

        If timeout is None the call will block until a valid card has been read or the stop() method
        is called on the object.

        returns: [CardData] if the read was successful or None if timeout occured

        .. warning:: The call only returns valid card data and ignores cards with invalid checksums.

        """
        self.card = None
        if timeout:
            self.successful_read_deadline = time.time() + timeout
        else:
            self.successful_read_deadline = None

        self._read()
        return self.card

    def card_inserted(self, card):
        self.stop()

    def tick(self):
        if self.successful_read_deadline and time.time() > self.successful_read_deadline:
            self.stop()
