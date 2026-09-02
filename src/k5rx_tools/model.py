from __future__ import annotations

from dataclasses import dataclass

from . import schema

MODULATION_NAMES = {0: "FM", 1: "AM", 2: "USB"}
BANDWIDTH_NAMES = {0: "Wide", 1: "Narrow"}


@dataclass(frozen=True)
class Memory:
    index: int
    name: str
    frequency_raw: int | None
    modulation: int
    bandwidth: int
    list_mask: int
    bank: int
    rx_code_type: int
    rx_code: int
    compander: int
    step: int
    reserved: int
    raw_record: bytes

    @property
    def record_id(self) -> str:
        return f"M{self.index + 1:03d}"

    @property
    def frequency_mhz(self) -> float | None:
        return None if self.frequency_raw is None else self.frequency_raw / 100000.0

    @property
    def empty(self) -> bool:
        return self.frequency_raw is None and not self.name and self.list_mask == 0 and self.bank == 0 and all(b == 0xFF for b in self.raw_record)


@dataclass(frozen=True)
class Bank:
    bank_id: int
    name: str
    raw_record: bytes


def decode_ascii(data: bytes | bytearray | memoryview, *, trim_spaces: bool = False) -> str:
    chars: list[str] = []
    for b in data:
        if b in (0x00, 0xFF):
            break
        if not 0x20 <= b <= 0x7E:
            break
        chars.append(chr(b))
    text = "".join(chars)
    return text.rstrip() if trim_spaces else text


def encode_ascii(text: str, length: int, *, pad: int = 0x00) -> bytes:
    try:
        raw = text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise schema.ValidationError("names must use printable ASCII") from exc
    if len(raw) > length:
        raise schema.ValidationError(f"name exceeds {length} bytes")
    if any(b < 0x20 or b > 0x7E for b in raw):
        raise schema.ValidationError("names must use printable ASCII")
    return raw + bytes([pad]) * (length - len(raw))


def decode_memory(image: bytes | bytearray | memoryview, index: int) -> Memory:
    ro = schema.record_offset(index)
    no = schema.name_offset(index)
    raw = bytes(image[ro : ro + schema.CHANNEL_RECORD_SIZE])
    freq = raw[0] | (raw[1] << 8) | (raw[2] << 16) | ((raw[3] & 0x07) << 24)
    erased = all(b == 0xFF for b in raw)
    frequency_raw = None if erased or freq in (0, schema.FREQ_MASK) else freq
    attr = raw[6]
    return Memory(
        index=index,
        name=decode_ascii(image[no : no + schema.NAME_LENGTH]),
        frequency_raw=frequency_raw,
        modulation=0 if erased else raw[5] & 0x07,
        bandwidth=0 if erased else (raw[3] >> 5) & 0x01,
        list_mask=0 if erased else attr & 0x07,
        bank=0 if erased else (attr & 0x78) >> 3,
        rx_code_type=0 if erased else (raw[3] >> 3) & 0x03,
        rx_code=0 if erased else raw[4] & 0x7F,
        compander=0 if erased else (raw[3] >> 6) & 0x01,
        step=0 if erased else (raw[5] >> 3) & 0x1F,
        reserved=0xFF if erased else raw[7],
        raw_record=raw,
    )


def decode_bank(image: bytes | bytearray | memoryview, bank_id: int) -> Bank:
    off = schema.bank_offset(bank_id)
    raw = bytes(image[off : off + schema.BANK_RECORD_SIZE])
    name = decode_ascii(raw[: schema.NAME_LENGTH], trim_spaces=True)
    if not name:
        name = f"BANK{bank_id}"
    return Bank(bank_id=bank_id, name=name, raw_record=raw)


def all_memories(image: bytes | bytearray | memoryview) -> list[Memory]:
    schema.validate_image(image)
    return [decode_memory(image, i) for i in range(schema.CHANNEL_COUNT)]


def all_banks(image: bytes | bytearray | memoryview) -> list[Bank]:
    schema.validate_image(image)
    return [decode_bank(image, i) for i in range(1, schema.BANK_COUNT + 1)]


def clear_memory(image: bytearray, index: int) -> None:
    ro = schema.record_offset(index)
    no = schema.name_offset(index)
    image[ro : ro + schema.CHANNEL_RECORD_SIZE] = b"\xFF" * schema.CHANNEL_RECORD_SIZE
    image[no : no + schema.NAME_LENGTH] = b"\x00" * schema.NAME_LENGTH


def update_memory_visible(
    image: bytearray,
    index: int,
    *,
    name: str,
    frequency_raw: int,
    modulation: int,
    bandwidth: int,
    list_mask: int,
    bank: int,
) -> None:
    if not schema.frequency_allowed(frequency_raw):
        raise schema.ValidationError(f"M{index + 1:03d}: unsupported RX frequency {frequency_raw / 100000.0:.5f} MHz")
    if modulation not in MODULATION_NAMES:
        raise schema.ValidationError(f"M{index + 1:03d}: modulation must be FM/AM/USB")
    if bandwidth not in BANDWIDTH_NAMES:
        raise schema.ValidationError(f"M{index + 1:03d}: bandwidth must be Wide/Narrow")
    if not 0 <= list_mask <= 7:
        raise schema.ValidationError(f"M{index + 1:03d}: list mask must be 0..7")
    if not 0 <= bank <= schema.BANK_COUNT:
        raise schema.ValidationError(f"M{index + 1:03d}: bank must be 0..8")

    ro = schema.record_offset(index)
    no = schema.name_offset(index)
    rec = bytearray(image[ro : ro + schema.CHANNEL_RECORD_SIZE])
    if all(b == 0xFF for b in rec):
        rec = bytearray(schema.CHANNEL_RECORD_SIZE)
        rec[5] = 4 << 3  # default step index used by the firmware/web beta

    rec[0] = frequency_raw & 0xFF
    rec[1] = (frequency_raw >> 8) & 0xFF
    rec[2] = (frequency_raw >> 16) & 0xFF
    rec[3] = (rec[3] & 0xF8) | ((frequency_raw >> 24) & 0x07)
    rec[3] = (rec[3] & ~0x20) | ((bandwidth & 1) << 5)
    rec[5] = (rec[5] & 0xF8) | (modulation & 0x07)
    rec[6] = (rec[6] & 0x80) | (list_mask & 0x07) | ((bank << 3) & 0x78)
    image[ro : ro + schema.CHANNEL_RECORD_SIZE] = rec
    image[no : no + schema.NAME_LENGTH] = encode_ascii(name, schema.NAME_LENGTH)


def update_bank_name(image: bytearray, bank_id: int, name: str) -> None:
    off = schema.bank_offset(bank_id)
    image[off : off + schema.NAME_LENGTH] = encode_ascii(name, schema.NAME_LENGTH, pad=0x20)


def validate_memories(image: bytes | bytearray | memoryview) -> list[str]:
    schema.validate_image(image)
    errors: list[str] = []
    for i in range(schema.CHANNEL_COUNT):
        m = decode_memory(image, i)
        has_metadata = bool(m.name or m.list_mask or m.bank)
        if m.frequency_raw is None:
            if has_metadata:
                errors.append(f"{m.record_id}: frequency is required")
            continue
        if not schema.frequency_allowed(m.frequency_raw):
            errors.append(f"{m.record_id}: unsupported RX frequency {m.frequency_mhz:.5f} MHz")
        if m.modulation not in MODULATION_NAMES:
            errors.append(f"{m.record_id}: unsupported modulation {m.modulation}")
        if not 0 <= m.bank <= schema.BANK_COUNT:
            errors.append(f"{m.record_id}: invalid Bank {m.bank}")
    return errors


def describe_memory(m: Memory) -> str:
    if m.frequency_raw is None:
        return f"{m.record_id} EMPTY"
    lists = "+".join(f"L{i}" for i in range(1, 4) if m.list_mask & (1 << (i - 1))) or "NoList"
    return (
        f"{m.record_id} {m.name or '(no name)'} {m.frequency_mhz:.5f} "
        f"{MODULATION_NAMES.get(m.modulation, f'MOD{m.modulation}')} "
        f"{BANDWIDTH_NAMES.get(m.bandwidth, '?')} {lists} Bank={m.bank}"
    )
