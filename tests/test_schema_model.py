import pytest

from k5rx_jpn import model, schema


def test_blank_image_validates(blank_image):
    header = schema.validate_image(blank_image)
    assert header.version == 2
    assert header.channel_count == 400


def test_visible_update_preserves_hidden_fields(blank_image):
    image = bytearray(blank_image)
    ro = schema.record_offset(0)
    image[ro:ro+8] = bytes([0, 0, 0, 0x58, 0x55, (7 << 3) | 1, 0x80, 0xA5])
    model.update_memory_visible(
        image,
        0,
        name="TEST",
        frequency_raw=14_510_000,
        modulation=1,
        bandwidth=0,
        list_mask=3,
        bank=2,
    )
    mem = model.decode_memory(image, 0)
    assert mem.name == "TEST"
    assert mem.frequency_raw == 14_510_000
    assert mem.rx_code_type == 3
    assert mem.rx_code == 0x55
    assert mem.compander == 1
    assert mem.step == 7
    assert mem.reserved == 0xA5
    assert mem.list_mask == 3
    assert mem.bank == 2


def test_firmware_schema_v2_contract_constants():
    assert schema.MAGIC == 0x4B355258
    assert schema.SCHEMA_VERSION == 2
    assert schema.HEADER_SIZE == 16
    assert schema.CHANNEL_COUNT == 400
    assert schema.CHANNEL_BASE == 0x0010
    assert schema.CHANNEL_RECORD_SIZE == 8
    assert schema.NAME_BASE == 0x0C90
    assert schema.NAME_LENGTH == 10
    assert schema.BANK_COUNT == 8
    assert schema.BANK_BASE == 0x1D30
    assert schema.BANK_RECORD_SIZE == 16
    assert schema.FACTORY_BASE == 0x1E00


def test_firmware_channel_record_bit_layout(blank_image):
    image = bytearray(blank_image)
    ro = schema.record_offset(0)
    image[ro:ro+8] = bytes([
        0xB0, 0x67, 0xDD,  # 145.10000 MHz in 10 Hz units
        0x70,              # code type 2, narrow, RX compander flag
        0x17,              # RX code 23
        0x39,              # AM, step index 7
        0x1D,              # scan lists 1+3, bank 3
        0x00,
    ])

    mem = model.decode_memory(image, 0)
    assert mem.frequency_raw == 14_510_000
    assert mem.rx_code_type == 2
    assert mem.rx_code == 23
    assert mem.bandwidth == 1
    assert mem.compander == 1
    assert mem.modulation == 1
    assert mem.step == 7
    assert mem.list_mask == 5
    assert mem.bank == 3


def test_write_allowlist_rejects_settings(blank_image):
    changed = bytearray(blank_image)
    changed[0x1CB0] ^= 1
    with pytest.raises(schema.ValidationError):
        schema.assert_safe_change(blank_image, bytes(changed))


def test_frequency_gap_rejected():
    assert schema.frequency_allowed(62_999_999)
    assert not schema.frequency_allowed(63_000_000)
    assert not schema.frequency_allowed(83_999_999)
    assert schema.frequency_allowed(84_000_000)
    assert schema.frequency_allowed(130_000_000)
    assert not schema.frequency_allowed(130_000_001)
