#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2020 Mad Tinkerer Me <mad.tinkerer.me@gmail.com>
Copyright (C) 2015 Philipp Meisberger <team@pm-codeworks.de>
All rights reserved.

"""

from serial import Serial, EIGHTBITS
import logging
import os
import time
import struct

from collections import namedtuple


class CardData(namedtuple('CardData', ['value', 'checksum', 'type', 'is_valid'])):
    pass


class BaseReader(object):
    """
    A python written library for an 125kHz RFID reader using the EM4100 protocol.

    Flag for RFID connection start.
    @var hex RFID_STARTCODE

    Flag for RFID connection end.
    @var hex RFID_ENDCODE

    UART serial connection via PySerial.
    @var Serial serial

    Holds the complete tag after reading.
    @var string __rawTag
    """

    RFID_STARTCODE = 0x02
    RFID_ENDCODE = 0x03

    def __init__(self, port='/dev/ttyS0', heartbeat_interval=0.5):
        self.quit_reader = False
        self.port = port
        self.serial = Serial(port=port, baudrate=9600, bytesize=EIGHTBITS, timeout=0.1)
        self.last_read_at = None
        self.card = None
        self.current_fragment = []
        self.heartbeat_interval = heartbeat_interval

    def close(self):
        if self.serial and self.serial.is_open:
            self.serial.close()

        self.stop_read()

    def stop_read(self):
        self.quit_reader = True

    def start(self):
        self._read()

    def _read(self):
        self.quit_reader = False
        while not self.quit_reader:
            received_bytes = self.serial.read()
            if received_bytes and len(received_bytes) > 0:
                recieved_byte = received_bytes[0]
                assert len(received_bytes) == 1

                if recieved_byte == BaseReader.RFID_STARTCODE:
                    if len(self.current_fragment) > 0:
                        self._process_fragment(self.current_fragment)
                        self.current_fragment = []
                elif recieved_byte == BaseReader.RFID_ENDCODE:
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
        pass

    def card_removed(self, card):
        pass

    def invalid_card(self, card):
        logging.warning("[{port}] invalid card detected {card}".format(port=self.port, card=card))

    def tick(self):
        pass


class Reader(BaseReader):
    def __init__(self, port):
        # TODO: six
        super().__init__(port, heartbeat_interval=None)
        self.successful_read_deadline = None

    def start(self):
        raise RuntimeError("Simple reader does not support start method")

    def read(self, timeout=None):
        self.card = None
        if timeout:
            self.successful_read_deadline = time.time() + timeout
        else:
            self.successful_read_deadline = None

        self._read()
        return self.card

    def card_inserted(self, card):
        self.stop_read()

    def tick(self):
        if self.successful_read_deadline and time.time() > self.successful_read_deadline:
            self.stop_read()


"""
TODO: Expected behavior

# Simple
reader = em4100.Reader('/dev/ttyS0')
tag = reader.read(timeout=15.0)

#event driven
class MyReader(em4100.BaseReader):
    def __init__(self):
        super().__init__('/dev/ttyS0')

    def card_inserted(self, card)
        pass

    def card_removed(self, card):
        pass

    def invalid_card(self, card):
        pass

    def tick(self):
        pass

"""
