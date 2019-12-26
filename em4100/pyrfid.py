#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyRfid
Copyright (C) 2015 Philipp Meisberger <team@pm-codeworks.de>
All rights reserved.

"""

import serial
import logging
import os
import struct

class PyRfid(object):
    """
    A python written library for an 125kHz RFID reader using the EM4100 protocol.

    Flag for RFID connection start.
    @var hex RFID_STARTCODE

    Flag for RFID connection end.
    @var hex RFID_ENDCODE

    UART serial connection via PySerial.
    @var Serial __serial

    Holds the complete tag after reading.
    @var string __rawTag
    """

    RFID_STARTCODE = 0x02
    RFID_ENDCODE = 0x03
    __serial = None
    __rawTag = None

    def __init__(self, port = '/dev/ttyUSB0', baudRate = 9600):
        """
        Constructor

        @param string port
        @param integer baudRate
        """

        ## Validates port
        if ( os.path.exists(port) == False ):
            raise Exception('The RFID sensor port "' + port + '" was not found!')

        ## Initializes connection
        self.__serial = serial.Serial(port = port, baudrate = baudRate, bytesize = serial.EIGHTBITS, timeout = 1)
        self.tagValue = None

    def __del__(self):
        """
        Destructor

        """

        ## Closes connection if established
        if ( ( self.__serial != None ) and ( self.__serial.isOpen() == True ) ):
            self.__serial.close()

    def __read(self):
        """
        Reads the complete tag and returns status.

        @return boolean
        """

        self.__rawTag = None
        rawTag = ''
        calculatedChecksum = 0
        receivedPacketData = []
        index = 0

        while ( True ):

            ## Reads on byte
            receivedFragment = self.__serial.read()

            ## Collects RFID data
            if ( len(receivedFragment) != 0 ):

                ## Start and stop bytes are string encoded and must be byte encoded
                if ( ( index == 0 ) or ( index == 13 ) ):
                    receivedFragment = struct.unpack('@B', receivedFragment)[0]
                else:

                    rawTag += str(struct.unpack('@B', receivedFragment)[0])
                    try:
                        receivedFragment = int(receivedFragment, 16)
                    except ValueError:
                        receivedFragment = struct.unpack('@B', receivedFragment)[0]
                        rawTag = ''
                        self.__rawTag = None
                        calculatedChecksum = 0
                        receivedPacketData = []
                        index = 0
                        if receivedFragment != PyRfid.RFID_STARTCODE:
                            # Some trash was coming in (e.g. sync signal, let's reset)
                            logging.warning("Resetting rfid read to assume we are at the begining")
                            continue

                        logging.warning("Start code encoutnered reseting to start state")

                ## Collects RFID data (hexadecimal)
                receivedPacketData.append(receivedFragment)
                index += 1

            ## Packet completly received
            if ( index == 14 ):

                ## Checks for invalid packet data
                if ( ( receivedPacketData[0] != self.RFID_STARTCODE ) or ( receivedPacketData[13] != self.RFID_ENDCODE ) ):
                    raise Exception('Invalid start or stop bytes!')

                ## Calculates packet checksum
                for i in range(1, 11, 2):
                    byte = receivedPacketData[i] << 4
                    byte = byte | receivedPacketData[i+1]
                    calculatedChecksum = calculatedChecksum ^ byte

                ## Gets received packet checksum
                receivedChecksum = receivedPacketData[11] << 4
                receivedChecksum = receivedChecksum | receivedPacketData[12]

                ## Checks for wrong checksum
                if ( calculatedChecksum != receivedChecksum ):
                    raise Exception('Calculated checksum is wrong!')
                
                tagValue = 0
                for i in range(3, 11):
                    tagValue = tagValue << 4
                    tagValue = tagValue | receivedPacketData[i]

                self.tagValue = tagValue

                ## Sets complete tag for other methods
                self.__rawTag = rawTag

                return True

    @property
    def serial(self):
        return self.__serial

    def readTag(self):
        """
        Reads the complete raw tag.

        @return boolean
        """

        try:
            while ( self.__read() != True ):
                pass

        except KeyboardInterrupt:
            return False

        return True

    @property
    def rawTag(self):
        """
        Returns read raw tag in hexadecimal format "1A2B345C67" without checksum.

        @return string (10 bytes)
        """

        return self.__rawTag[0:10]

    @property
    def tagType(self):
        """
        Returns type of read tag (first 4 bytes).

        @return hex (4 bytes)
        """

        if ( self.__rawTag != None ):
            return hex(int(self.__rawTag[0:4], 16))

        return None

    @property
    def tagTypeFloat(self):
        """
        Returns type of read tag (first 2 bytes).

        @return hex (2 bytes)
        """

        if ( self.__rawTag != None ):
            return hex(int(self.__rawTag[0:2], 16))

        return None

    @property
    def tagId(self):
        """
        Returns ID of read tag in decimal format "0001234567".

        @return string (10 chars)
        """

        if ( self.__rawTag != None ):

            ## Length of ID is 10 anyway
            return '%010i' % int(self.__rawTag[4:10], 16)

        return None

    @property
    def tagIdFloat(self):
        """
        Returns ID of read tag in float format "123,45678".

        @return string (9 chars)
        """

        if ( self.__rawTag != None ):
            pre = float.fromhex(self.__rawTag[2:6])
            post = float.fromhex(self.__rawTag[6:10]) / 100000
            tag = pre + post
            return str(tag)

        return None

    @property
    def tagChecksum(self):
        """
        Returns checksum of read tag (last 2 bytes).

        @return hex (2 bytes)
        """

        if ( self.__rawTag != None ):
            return hex(int(self.__rawTag[10:12], 16))

        return None
