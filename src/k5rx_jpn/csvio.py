from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from . import model, schema

FIELDS = ["record", "name", "frequency", "modulation", "bandwidth", "list1", "list2", "list3", "bank"]


@dataclass(frozen=True)
class CsvInfo:
    memory_rows: int
    bank_rows: int


def _truthy(value: object) -> bool:
    text = str(value or "").strip().lower()
    if text in {"1", "true", "on", "yes"}:
        return True
    if text in {"0", "false", "off", "no", ""}:
        return False
    raise schema.ValidationError(f"invalid boolean value: {value!r}")


def _parse_modulation(value: object) -> int:
    text = str(value or "").strip().upper()
    lookup = {"FM": 0, "AM": 1, "USB": 2, "0": 0, "1": 1, "2": 2}
    if text not in lookup:
        raise schema.ValidationError(f"invalid modulation: {value!r}")
    return lookup[text]


def _parse_bandwidth(value: object) -> int:
    text = str(value or "").strip().lower()
    lookup = {"wide": 0, "w": 0, "0": 0, "narrow": 1, "n": 1, "1": 1}
    if text not in lookup:
        raise schema.ValidationError(f"invalid bandwidth: {value!r}")
    return lookup[text]


def _parse_frequency(value: object) -> int:
    text = str(value or "").strip()
    try:
        mhz = float(text)
    except ValueError as exc:
        raise schema.ValidationError(f"invalid frequency: {value!r}") from exc
    raw = round(mhz * 100000.0)
    if not schema.frequency_allowed(raw):
        raise schema.ValidationError(f"unsupported RX frequency: {mhz:.5f} MHz")
    return raw


def _normalized_reader(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            raise schema.ValidationError("CSV has no header")
        fieldnames = [x.strip().lower() for x in reader.fieldnames]
        if "record" not in fieldnames and "channel" in fieldnames:
            fieldnames[fieldnames.index("channel")] = "record"
        missing = [x for x in FIELDS if x not in fieldnames]
        if missing:
            raise schema.ValidationError(f"missing CSV column(s): {', '.join(missing)}")
        rows: list[dict[str, str]] = []
        for raw in reader:
            normalized: dict[str, str] = {}
            for original, normalized_name in zip(reader.fieldnames, fieldnames, strict=True):
                normalized[normalized_name] = raw.get(original, "") or ""
            if any(value.strip() for value in normalized.values()):
                rows.append(normalized)
    return fieldnames, rows


def inspect(path: Path) -> CsvInfo:
    _, rows = _normalized_reader(path)
    memories: set[int] = set()
    banks: set[int] = set()
    for row in rows:
        rid = row["record"].strip().upper()
        if rid.startswith("B") and rid[1:].isdigit():
            bank_id = int(rid[1:])
            if not 1 <= bank_id <= schema.BANK_COUNT:
                raise schema.ValidationError(f"invalid Bank record: {rid}")
            if bank_id in banks:
                raise schema.ValidationError(f"duplicate Bank record: B{bank_id}")
            extras = [row[k].strip() for k in FIELDS[2:]]
            if any(extras):
                raise schema.ValidationError(f"B{bank_id}: Bank row may only use record and name")
            model.encode_ascii(row["name"], schema.NAME_LENGTH, pad=0x20)
            banks.add(bank_id)
            continue
        if rid.startswith("M"):
            number = rid[1:]
        else:
            number = rid
        if not number.isdigit():
            raise schema.ValidationError(f"invalid record identifier: {rid!r}")
        channel = int(number)
        if not 1 <= channel <= schema.CHANNEL_COUNT:
            raise schema.ValidationError(f"Memory out of range: {rid}")
        if channel in memories:
            raise schema.ValidationError(f"duplicate Memory record: M{channel:03d}")
        memories.add(channel)
    if len(memories) != schema.CHANNEL_COUNT:
        raise schema.ValidationError(f"CSV must contain all 400 physical Memory slots; found {len(memories)}")
    return CsvInfo(memory_rows=len(memories), bank_rows=len(banks))


def export_csv(image: bytes, path: Path, *, include_banks: bool = True) -> None:
    schema.validate_image(image)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\r\n")
        writer.writeheader()
        if include_banks:
            for b in model.all_banks(image):
                writer.writerow({"record": f"B{b.bank_id}", "name": b.name})
        for m in model.all_memories(image):
            if m.frequency_raw is None:
                writer.writerow({
                    "record": m.record_id,
                    "name": "",
                    "frequency": "",
                    "modulation": "",
                    "bandwidth": "",
                    "list1": 0,
                    "list2": 0,
                    "list3": 0,
                    "bank": 0,
                })
                continue
            writer.writerow({
                "record": m.record_id,
                "name": m.name,
                "frequency": f"{m.frequency_mhz:.5f}",
                "modulation": model.MODULATION_NAMES.get(m.modulation, str(m.modulation)),
                "bandwidth": model.BANDWIDTH_NAMES.get(m.bandwidth, str(m.bandwidth)),
                "list1": 1 if m.list_mask & 1 else 0,
                "list2": 1 if m.list_mask & 2 else 0,
                "list3": 1 if m.list_mask & 4 else 0,
                "bank": m.bank,
            })


def import_csv(path: Path, base_image: bytes, *, import_banks: bool = True) -> bytes:
    schema.validate_image(base_image)
    info = inspect(path)
    _, source_rows = _normalized_reader(path)
    memories: dict[int, dict[str, str]] = {}
    banks: dict[int, str] = {}
    for row in source_rows:
        rid = row["record"].strip().upper()
        if rid.startswith("B"):
            banks[int(rid[1:])] = row["name"]
        else:
            channel = int(rid[1:] if rid.startswith("M") else rid)
            memories[channel - 1] = row

    out = bytearray(base_image)
    for index in range(schema.CHANNEL_COUNT):
        row = memories[index]
        rid = f"M{index + 1:03d}"
        name = row["name"]
        freq_text = row["frequency"].strip()
        l1 = _truthy(row["list1"])
        l2 = _truthy(row["list2"])
        l3 = _truthy(row["list3"])
        bank_text = row["bank"].strip() or "0"
        try:
            bank = int(bank_text, 10)
        except ValueError as exc:
            raise schema.ValidationError(f"{rid}: invalid Bank {bank_text!r}") from exc
        if not 0 <= bank <= schema.BANK_COUNT:
            raise schema.ValidationError(f"{rid}: Bank must be 0..8")
        model.encode_ascii(name, schema.NAME_LENGTH)
        if not freq_text:
            if name or l1 or l2 or l3 or bank:
                raise schema.ValidationError(f"{rid}: frequency is required when other fields are set")
            model.clear_memory(out, index)
            continue
        frequency_raw = _parse_frequency(freq_text)
        modulation = _parse_modulation(row["modulation"])
        bandwidth = _parse_bandwidth(row["bandwidth"])
        list_mask = (1 if l1 else 0) | (2 if l2 else 0) | (4 if l3 else 0)
        model.update_memory_visible(
            out,
            index,
            name=name,
            frequency_raw=frequency_raw,
            modulation=modulation,
            bandwidth=bandwidth,
            list_mask=list_mask,
            bank=bank,
        )
    if import_banks:
        for bank_id, name in banks.items():
            model.update_bank_name(out, bank_id, name)

    errors = model.validate_memories(out)
    if errors:
        raise schema.ValidationError("CSV produced invalid EEPROM:\n" + "\n".join(errors[:20]))
    if info.bank_rows == 0 and import_banks:
        # Explicitly harmless; retained for clear semantics in callers.
        pass
    return bytes(out)
