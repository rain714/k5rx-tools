from k5rx_jpn import protocol


def test_crc_xmodem_known_vector():
    assert protocol.crc16_ccitt(b"123456789") == 0x31C3


def test_frame_round_trip():
    payload = protocol.read_eeprom_request(0x1234, 0x40, 0xAABBCCDD)
    frame = protocol.encode_frame(payload)
    assert frame[:2] == b"\xAB\xCD"
    assert frame[-2:] == b"\xDC\xBA"
    assert protocol.decode_frame(frame) == payload


def test_payload_command_header():
    payload = protocol.session_request(0x11223344)
    decoded = protocol.decode_payload(payload)
    assert decoded.command_id == protocol.CMD_SESSION
    assert decoded.data == b"\x44\x33\x22\x11"
