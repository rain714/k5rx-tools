from __future__ import annotations

from dataclasses import dataclass
import struct

EEPROM_SIZE = 0x2000
FACTORY_BASE = 0x1E00
MAGIC = 0x4B355258
SCHEMA_VERSION = 2
HEADER_SIZE = 16
CHANNEL_COUNT = 400
CHANNEL_BASE = 0x0010
CHANNEL_RECORD_SIZE = 8
CHANNEL_END = CHANNEL_BASE + CHANNEL_COUNT * CHANNEL_RECORD_SIZE
NAME_BASE = CHANNEL_END
NAME_LENGTH = 10
NAME_END = NAME_BASE + CHANNEL_COUNT * NAME_LENGTH
BANK_COUNT = 8
BANK_BASE = 0x1D30
BANK_RECORD_SIZE = 16
BANK_END = BANK_BASE + BANK_COUNT * BANK_RECORD_SIZE
READ_BLOCK = 0x80
WRITE_BLOCK = 8
FREQ_MASK = 0x07FFFFFF
RX_RANGES = ((1_800_000, 63_000_000), (84_000_000, 130_000_000))


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class Header:
    magic: int
    version: int
    header_size: int
    caps: int
    mutable_end: int
    channel_count: int
    record_size: int
    name_length: int
    bank_count: int


def parse_header(image: bytes | bytearray | memoryview) -> Header:
    if len(image) < HEADER_SIZE:
        raise ValidationError(f"EEPROM image is too short: {len(image)} bytes")
    return Header(
        magic=struct.unpack_from("<I", image, 0)[0],
        version=image[4],
        header_size=image[5],
        caps=struct.unpack_from("<H", image, 6)[0],
        mutable_end=struct.unpack_from("<H", image, 8)[0],
        channel_count=struct.unpack_from("<H", image, 10)[0],
        record_size=image[12],
        name_length=image[13],
        bank_count=image[14],
    )


def validate_image(image: bytes | bytearray | memoryview) -> Header:
    if len(image) != EEPROM_SIZE:
        raise ValidationError(f"EEPROM image must be {EEPROM_SIZE} bytes; got {len(image)}")
    h = parse_header(image)
    expected = {
        "magic": MAGIC,
        "version": SCHEMA_VERSION,
        "header_size": HEADER_SIZE,
        "mutable_end": FACTORY_BASE,
        "channel_count": CHANNEL_COUNT,
        "record_size": CHANNEL_RECORD_SIZE,
        "name_length": NAME_LENGTH,
        "bank_count": BANK_COUNT,
    }
    for field, want in expected.items():
        got = getattr(h, field)
        if got != want:
            if field == "magic":
                raise ValidationError(f"bad EEPROM magic: 0x{got:08X} (expected 0x{want:08X})")
            raise ValidationError(f"unexpected {field}: {got} (expected {want})")
    return h


def frequency_allowed(raw_10hz: int) -> bool:
    return any(lo <= raw_10hz < hi for lo, hi in RX_RANGES[:1]) or RX_RANGES[1][0] <= raw_10hz <= RX_RANGES[1][1]


def record_offset(index: int) -> int:
    if not 0 <= index < CHANNEL_COUNT:
        raise IndexError(index)
    return CHANNEL_BASE + index * CHANNEL_RECORD_SIZE


def name_offset(index: int) -> int:
    if not 0 <= index < CHANNEL_COUNT:
        raise IndexError(index)
    return NAME_BASE + index * NAME_LENGTH


def bank_offset(bank_id: int) -> int:
    if not 1 <= bank_id <= BANK_COUNT:
        raise IndexError(bank_id)
    return BANK_BASE + (bank_id - 1) * BANK_RECORD_SIZE


def allowed_write_block(offset: int) -> bool:
    if offset % WRITE_BLOCK:
        return False
    in_memory = CHANNEL_BASE <= offset and offset + WRITE_BLOCK <= NAME_END
    in_bank = BANK_BASE <= offset and offset + WRITE_BLOCK <= BANK_END
    return in_memory or in_bank


def changed_blocks(before: bytes, after: bytes) -> list[int]:
    validate_image(before)
    validate_image(after)
    return [
        off
        for off in range(0, FACTORY_BASE, WRITE_BLOCK)
        if before[off : off + WRITE_BLOCK] != after[off : off + WRITE_BLOCK]
    ]


def assert_safe_change(before: bytes, after: bytes) -> list[int]:
    blocks = changed_blocks(before, after)
    unsafe = [off for off in blocks if not allowed_write_block(off)]
    if unsafe:
        formatted = ", ".join(f"0x{x:04X}" for x in unsafe[:16])
        more = " ..." if len(unsafe) > 16 else ""
        raise ValidationError(f"changes outside Memory/Bank write allowlist: {formatted}{more}")
    if before[FACTORY_BASE:] != after[FACTORY_BASE:]:
        raise ValidationError("factory/calibration region differs")
    return blocks


def coalesce_blocks(blocks: list[int], max_size: int = READ_BLOCK) -> list[tuple[int, int]]:
    if not blocks:
        return []
    out: list[tuple[int, int]] = []
    start = prev = blocks[0]
    for off in blocks[1:]:
        contiguous = off == prev + WRITE_BLOCK
        fits = off + WRITE_BLOCK - start <= max_size
        if contiguous and fits:
            prev = off
            continue
        out.append((start, prev + WRITE_BLOCK))
        start = prev = off
    out.append((start, prev + WRITE_BLOCK))
    return out
