from __future__ import annotations

from dataclasses import dataclass
import secrets
import struct

XOR_KEY = bytes([0x16, 0x6C, 0x14, 0xE6, 0x2E, 0x91, 0x0D, 0x40, 0x21, 0x35, 0xD5, 0x40, 0x13, 0x03, 0xE9, 0x80])
FRAME_HEAD = b"\xAB\xCD"
FRAME_TAIL = b"\xDC\xBA"

CMD_SESSION = 0x0514
REPLY_SESSION = 0x0515
CMD_READ_EEPROM = 0x051B
REPLY_READ_EEPROM = 0x051C
CMD_WRITE_EEPROM = 0x051D
REPLY_WRITE_EEPROM = 0x051E


class ProtocolError(RuntimeError):
    pass


@dataclass(frozen=True)
class Payload:
    command_id: int
    data: bytes


def crc16_ccitt(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc <<= 1
            if crc & 0x10000:
                crc ^= 0x1021
            crc &= 0xFFFF
    return crc


def xor_bytes(data: bytes) -> bytes:
    return bytes(b ^ XOR_KEY[i % len(XOR_KEY)] for i, b in enumerate(data))


def encode_payload(command_id: int, data: bytes = b"") -> bytes:
    return struct.pack("<HH", command_id, len(data)) + data


def decode_payload(payload: bytes) -> Payload:
    if len(payload) < 4:
        raise ProtocolError("short command payload")
    command_id, size = struct.unpack_from("<HH", payload)
    if size + 4 != len(payload):
        raise ProtocolError(f"payload size mismatch: header={size}, actual={len(payload) - 4}")
    return Payload(command_id=command_id, data=payload[4:])


def encode_frame(payload: bytes) -> bytes:
    crc = struct.pack("<H", crc16_ccitt(payload))
    encoded = xor_bytes(payload + crc)
    return FRAME_HEAD + struct.pack("<H", len(payload)) + encoded + FRAME_TAIL


def decode_frame(frame: bytes, *, allow_ffff_crc: bool = True) -> bytes:
    if len(frame) < 8 or frame[:2] != FRAME_HEAD or frame[-2:] != FRAME_TAIL:
        raise ProtocolError("invalid frame markers")
    size = struct.unpack_from("<H", frame, 2)[0]
    if len(frame) != size + 8:
        raise ProtocolError(f"frame size mismatch: header={size}, actual={len(frame) - 8}")
    decoded = xor_bytes(frame[4:-2])
    payload, crc_bytes = decoded[:-2], decoded[-2:]
    received = struct.unpack("<H", crc_bytes)[0]
    calculated = crc16_ccitt(payload)
    if received != calculated and not (allow_ffff_crc and received == 0xFFFF):
        raise ProtocolError(f"CRC mismatch: received=0x{received:04X} calculated=0x{calculated:04X}")
    return payload


def new_session_id() -> int:
    return secrets.randbits(32)


def session_request(session_id: int) -> bytes:
    return encode_payload(CMD_SESSION, struct.pack("<I", session_id))


def read_eeprom_request(offset: int, size: int, session_id: int) -> bytes:
    if not 0 <= offset <= 0xFFFF:
        raise ValueError("offset out of range")
    if not 1 <= size <= 0x80:
        raise ValueError("size must be 1..128")
    return encode_payload(CMD_READ_EEPROM, struct.pack("<HBBI", offset, size, 0, session_id))


def write_eeprom_request(offset: int, data: bytes, session_id: int, *, allow_password: bool = True) -> bytes:
    if not 0 <= offset <= 0xFFFF:
        raise ValueError("offset out of range")
    if not data or len(data) > 0x80:
        raise ValueError("write size must be 1..128")
    return encode_payload(CMD_WRITE_EEPROM, struct.pack("<HBBI", offset, len(data), 1 if allow_password else 0, session_id) + data)


def parse_session_reply(payload: bytes) -> str:
    decoded = decode_payload(payload)
    if decoded.command_id != REPLY_SESSION:
        raise ProtocolError(f"unexpected session reply 0x{decoded.command_id:04X}")
    version = decoded.data[:16].split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
    return version or "(unknown)"


def parse_read_reply(payload: bytes, expected_offset: int, expected_size: int) -> bytes:
    decoded = decode_payload(payload)
    if decoded.command_id != REPLY_READ_EEPROM:
        raise ProtocolError(f"unexpected EEPROM read reply 0x{decoded.command_id:04X}")
    if len(decoded.data) < 4:
        raise ProtocolError("short EEPROM read reply")
    offset, size, _padding = struct.unpack_from("<HBB", decoded.data)
    if offset != expected_offset or size != expected_size:
        raise ProtocolError(
            f"EEPROM read mismatch: got offset=0x{offset:04X} size={size}, expected 0x{expected_offset:04X}/{expected_size}"
        )
    data = decoded.data[4:]
    if len(data) < expected_size:
        raise ProtocolError("short EEPROM read data")
    return data[:expected_size]


def parse_write_reply(payload: bytes, expected_offset: int) -> None:
    decoded = decode_payload(payload)
    if decoded.command_id != REPLY_WRITE_EEPROM:
        raise ProtocolError(f"unexpected EEPROM write reply 0x{decoded.command_id:04X}")
    if len(decoded.data) < 2:
        raise ProtocolError("short EEPROM write reply")
    offset = struct.unpack_from("<H", decoded.data)[0]
    if offset != expected_offset:
        raise ProtocolError(f"EEPROM write ACK offset 0x{offset:04X} != 0x{expected_offset:04X}")
