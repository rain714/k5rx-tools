from __future__ import annotations

import struct

import pytest

from k5rx_tools import model, schema


def make_image() -> bytes:
    image = bytearray(b"\xFF" * schema.EEPROM_SIZE)
    struct.pack_into("<I", image, 0, schema.MAGIC)
    image[4] = schema.SCHEMA_VERSION
    image[5] = schema.HEADER_SIZE
    struct.pack_into("<H", image, 6, 0x0003)
    struct.pack_into("<H", image, 8, schema.FACTORY_BASE)
    struct.pack_into("<H", image, 10, schema.CHANNEL_COUNT)
    image[12] = schema.CHANNEL_RECORD_SIZE
    image[13] = schema.NAME_LENGTH
    image[14] = schema.BANK_COUNT
    image[15] = 0
    for bank_id in range(1, schema.BANK_COUNT + 1):
        model.update_bank_name(image, bank_id, f"BANK{bank_id}")
    return bytes(image)


@pytest.fixture
def blank_image() -> bytes:
    return make_image()
