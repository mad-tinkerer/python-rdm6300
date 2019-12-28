import time

from mock import patch, Mock
from unittest import TestCase

from rdm6300.reader import CardData, Reader, BaseReader

VALID_CARDS = ['67003B51C6CB', '67003BA86C98', '67003BA86793']
INVALID_CARDS = ['', '68003B51C6CB', '68003B51C6CBDA', 'SomeThingCrappyÚTFŐ']
CARD_DATA = {
    # Valid cards
    '67003B51C6CB': CardData(value=3887558, checksum=203, is_valid=True, type=103),
    '67003BA86C98': CardData(value=3909740, checksum=152, is_valid=True, type=103),
    '67003BA86793': CardData(value=3909735, checksum=147, is_valid=True, type=103),
    # Invalid cards
    '': None,
    '68003B51C6CB': CardData(value=3887558, checksum=203, is_valid=False, type=104),   # Invalid checksum
    '68003B51C6CBDA': None,   # Too long
    'SomeThingCrappyÚTFŐ': None,    # unicode (ascii > 128) and non hex digits are tolerated
}


class MockSerial(object):
    def __init__(self, data, delay=None):
        self.data = data
        self.pos = 0
        self.delay = delay
        self.is_open = True

    def close(self):
        self.is_open = False

    def read(self):
        if self.delay:
            time.sleep(self.delay)

        if self.pos >= len(self.data):
            return None
        else:
            ret_val = self.data[self.pos]
            self.pos += 1
            return bytes([ret_val])


class HeartbeatTestClass(BaseReader):
    def __init__(self):
        super().__init__(heartbeat_interval=0.2)
        self.events = []

    def card_inserted(self, card):
        self.events.append('inserted')

    def invalid_card(self, card):
        self.events.append('invalid')

    def card_removed(self, card):
        self.events.append('removed')
        self.stop()


def _assemble_bitstream(card_data):
    rv = bytearray()

    for card_string in card_data:
        rv.append(Reader._RFID_STARTCODE)
        rv.extend(card_string.encode())
        rv.append(Reader._RFID_ENDCODE)

    return rv


class BaseReaderTestCase(TestCase):
    @staticmethod
    def _string_to_fragment(string):
        try:
            return [int(ch, 16) for ch in string]
        except ValueError:
            return []

    @patch('rdm6300.reader.Serial')
    def test_card_data_processor(self, serial_mock):
        serial_mock.return_value = None
        reader = BaseReader(None)

        for key, value in CARD_DATA.items():
            fragment = self._string_to_fragment(key)
            data = reader._parse_fragment(fragment)
            self.assertEqual(data, value)

    @patch('rdm6300.reader.Serial')
    def test_card_reader_heartbeat(self, serial_mock):
        test_data = _assemble_bitstream([
            VALID_CARDS[0],
            VALID_CARDS[0],
            VALID_CARDS[0]])
        mock_serial = MockSerial(test_data, delay=0.01)
        serial_mock.return_value = mock_serial

        r = HeartbeatTestClass()
        start_time = time.time()
        r.start()

        self.assertEqual(mock_serial.pos, len(mock_serial.data))
        # Let's make sure that we are not cheating on the time
        self.assertTrue(time.time() - start_time > 0.5)
        self.assertEqual(r.events, ['inserted', 'removed'])


class ReaderTestCase(TestCase):
    @patch('rdm6300.reader.Serial')
    def test_card_reader(self, serial_mock):
        test_data = _assemble_bitstream([
            VALID_CARDS[0], VALID_CARDS[1], VALID_CARDS[2],
            INVALID_CARDS[1],  # invalid checksum -> skip
            INVALID_CARDS[2],  # invalid length -> skip
            VALID_CARDS[0],
            INVALID_CARDS[3],  # utf and non-hex data -> skip
            VALID_CARDS[0]])

        # The test data is missing the start data flag, just to simulate a partial stream
        test_data = VALID_CARDS[0].encode() + test_data
        serial_mock.return_value = MockSerial(test_data)

        r = Reader('whatever')
        self.assertTrue(r.serial.is_open)

        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[0]])
        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[0]])
        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[1]])
        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[2]])
        # Note invalid card is skipped
        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[0]])
        # Note: the very invalid card is skipped too
        self.assertEqual(r.read(), CARD_DATA[VALID_CARDS[0]])
        self.assertIsNone(r.read(timeout=0.5))
        r.close()

        self.assertFalse(r.serial.is_open)
        self.assertTrue(r.quit_reader)

    @patch('rdm6300.reader.Serial')
    def test_card_reader_timeout(self, serial_mock):
        test_data = _assemble_bitstream([
            VALID_CARDS[0], VALID_CARDS[1]])
        serial_mock.return_value = MockSerial(test_data, delay=0.01)

        r = Reader('whatever')

        # Reader cannot read 14 bytes when there's a 10ms delay on each byte
        # with a timeout of 100ms
        self.assertIsNone(r.read(timeout=0.1))

        # But the next read should return the correct card id
        self.assertEqual(r.read(timeout=0.1), CARD_DATA[VALID_CARDS[0]])
        self.assertEqual(r.read(timeout=0.2), CARD_DATA[VALID_CARDS[1]])
        self.assertIsNone(r.read(timeout=0.2))
