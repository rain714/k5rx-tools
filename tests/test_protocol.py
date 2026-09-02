from k5rx_tools import protocol


def test_crc_xmodem_known_vector():
    assert protocol.crc16_ccitt(b"123456789") == 0x31C3


def test_frame_round_trip():
    payload = protocol.read_eeprom_request(0x1234, 0x40, 0xAABBCCDD)
    frame = protocol.encode_frame(payload)
    assert frame[:2] == b"\xAB\xCD"
    assert frame[-2:] == b"\xDC\xBA"
    assert protocol.decode_frame(frame) == payload


def test_reply_frame_allows_firmware_ffff_crc_padding():
    payload = protocol.encode_payload(protocol.REPLY_WRITE_EEPROM, b"\x30\x1d")
    encoded = protocol.xor_bytes(payload + b"\xFF\xFF")
    frame = protocol.FRAME_HEAD + len(payload).to_bytes(2, "little") + encoded + protocol.FRAME_TAIL
    assert protocol.decode_frame(frame) == payload


def test_payload_command_header():
    payload = protocol.session_request(0x11223344)
    decoded = protocol.decode_payload(payload)
    assert decoded.command_id == protocol.CMD_SESSION
    assert decoded.data == b"\x44\x33\x22\x11"


def test_read_request_wire_layout():
    payload = protocol.read_eeprom_request(0x0E80, 0x80, 0x6457396A)
    assert payload == bytes.fromhex("1B050800800E80006A395764")
