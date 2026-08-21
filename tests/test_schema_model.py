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
