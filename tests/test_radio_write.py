from __future__ import annotations

import pytest

from k5rx_jpn import model, radio, schema


class FakeRadio:
    def __init__(self, current: bytes):
        self.current = bytearray(current)
        self.writes: list[tuple[int, bytes]] = []

    def read_all(self, progress=None) -> bytes:
        if progress:
            progress("read", schema.EEPROM_SIZE, schema.EEPROM_SIZE)
        return bytes(self.current)

    def write_eeprom(self, offset: int, data: bytes) -> None:
        self.writes.append((offset, bytes(data)))
        self.current[offset : offset + len(data)] = data

    def read_eeprom(self, offset: int, size: int) -> bytes:
        return bytes(self.current[offset : offset + size])


def _write_image(fake: FakeRadio, new: bytes, base: bytes) -> int:
    # Exercise K5Radio's implementation against a transport-free fake object.
    return radio.K5Radio.write_image(fake, new, base_image=base)


def test_write_image_writes_only_allowlisted_changes(blank_image: bytes):
    updated = bytearray(blank_image)
    model.update_memory_visible(
        updated,
        0,
        name="AIR",
        frequency_raw=11_810_000,
        modulation=1,
        bandwidth=0,
        list_mask=1,
        bank=1,
    )
    fake = FakeRadio(blank_image)
    count = _write_image(fake, bytes(updated), blank_image)
    assert count >= 1
    assert bytes(fake.current) == bytes(updated)
    assert fake.writes
    for offset, data in fake.writes:
        assert offset % 8 == 0
        assert len(data) % 8 == 0
        assert len(data) <= 128
        for block in range(offset, offset + len(data), 8):
            assert schema.allowed_write_block(block)


def test_write_image_rejects_stale_base(blank_image: bytes):
    updated = bytearray(blank_image)
    model.update_bank_name(updated, 1, "AIR")
    radio_now = bytearray(blank_image)
    radio_now[schema.BANK_BASE + 16] ^= 1
    fake = FakeRadio(bytes(radio_now))
    with pytest.raises(radio.RadioError, match="no longer matches --base"):
        _write_image(fake, bytes(updated), blank_image)
    assert fake.writes == []
