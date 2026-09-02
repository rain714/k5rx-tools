from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

from . import __version__, csvio, model, radio, schema


def _read_raw(path: Path) -> bytes:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise schema.ValidationError(f"cannot read {path}: {exc}") from exc
    schema.validate_image(data)
    return data


def _write_raw(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _progress(kind: str, done: int, total: int) -> None:
    pct = 100 if total == 0 else round(done * 100 / total)
    label = "Reading" if kind == "read" else "Writing/verify"
    print(f"\r{label}: {pct:3d}%", end="", file=sys.stderr, flush=True)
    if done >= total:
        print(file=sys.stderr)


def cmd_eeprom_validate(args: argparse.Namespace) -> int:
    image = _read_raw(args.raw)
    header = schema.validate_image(image)
    errors = model.validate_memories(image)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 2
    print("OK")
    print(f"schema={header.version} channels={header.channel_count} banks={header.bank_count}")
    print(f"sha256={hashlib.sha256(image).hexdigest()}")
    return 0


def cmd_eeprom_inspect(args: argparse.Namespace) -> int:
    image = _read_raw(args.raw)
    header = schema.parse_header(image)
    memories = model.all_memories(image)
    banks = model.all_banks(image)
    used = [m for m in memories if m.frequency_raw is not None]
    print(f"magic=0x{header.magic:08X} schema={header.version} mutable_end=0x{header.mutable_end:04X}")
    print(f"memories={len(memories)} used={len(used)} empty={len(memories) - len(used)} banks={len(banks)}")
    print("banks:")
    for bank in banks:
        count = sum(1 for m in used if m.bank == bank.bank_id)
        print(f"  B{bank.bank_id}: {bank.name} ({count} memories)")
    if args.memories:
        print("memories:")
        for memory in used:
            print("  " + model.describe_memory(memory))
    return 0


def cmd_eeprom_diff(args: argparse.Namespace) -> int:
    before = _read_raw(args.before)
    after = _read_raw(args.after)
    blocks = schema.changed_blocks(before, after)
    unsafe = [off for off in blocks if not schema.allowed_write_block(off)]
    changed_memories = [
        i
        for i in range(schema.CHANNEL_COUNT)
        if before[schema.record_offset(i) : schema.record_offset(i) + schema.CHANNEL_RECORD_SIZE]
        != after[schema.record_offset(i) : schema.record_offset(i) + schema.CHANNEL_RECORD_SIZE]
        or before[schema.name_offset(i) : schema.name_offset(i) + schema.NAME_LENGTH]
        != after[schema.name_offset(i) : schema.name_offset(i) + schema.NAME_LENGTH]
    ]
    changed_banks = [
        i
        for i in range(1, schema.BANK_COUNT + 1)
        if before[schema.bank_offset(i) : schema.bank_offset(i) + schema.BANK_RECORD_SIZE]
        != after[schema.bank_offset(i) : schema.bank_offset(i) + schema.BANK_RECORD_SIZE]
    ]
    print(f"changed_blocks={len(blocks)} changed_memories={len(changed_memories)} changed_banks={len(changed_banks)}")
    for i in changed_memories:
        a, b = model.decode_memory(before, i), model.decode_memory(after, i)
        print(f"{a.record_id}: {model.describe_memory(a)} -> {model.describe_memory(b)}")
    for bank_id in changed_banks:
        a, b = model.decode_bank(before, bank_id), model.decode_bank(after, bank_id)
        print(f"B{bank_id}: {a.name} -> {b.name}")
    if unsafe:
        print("unsafe blocks: " + ", ".join(f"0x{x:04X}" for x in unsafe))
        return 2
    return 0


def cmd_csv_validate(args: argparse.Namespace) -> int:
    info = csvio.inspect(args.csv)
    print(f"OK memories={info.memory_rows} bank_rows={info.bank_rows}")
    return 0


def cmd_csv_template(args: argparse.Namespace) -> int:
    csvio.write_template(args.csv, include_banks=not args.no_banks)
    print(f"output={args.csv} memories=400 banks={'0' if args.no_banks else '8'}")
    print("Next: edit the CSV, then run 'k5rx csv validate <file.csv>'.")
    print("To apply it, first create a fresh RAW backup with 'k5rx radio read backup.raw --port <PORT>'.")
    return 0


def cmd_csv_export(args: argparse.Namespace) -> int:
    image = _read_raw(args.raw)
    csvio.export_csv(image, args.csv, include_banks=not args.no_banks)
    print(f"output={args.csv} memories=400 banks={'0' if args.no_banks else '8'}")
    return 0


def cmd_csv_import(args: argparse.Namespace) -> int:
    if not args.base.is_file():
        raise schema.ValidationError(
            f"--base RAW not found: {args.base}. "
            "Create a fresh baseline first with 'k5rx radio read backup.raw --port <PORT>', "
            "then pass that file with --base."
        )
    base = _read_raw(args.base)
    updated = csvio.import_csv(args.csv, base, import_banks=not args.no_banks)
    schema.assert_safe_change(base, updated)
    _write_raw(args.output, updated)
    blocks = schema.changed_blocks(base, updated)
    print(f"output={args.output} changed_blocks={len(blocks)} sha256={hashlib.sha256(updated).hexdigest()}")
    print(f"Next: review with 'k5rx eeprom diff {args.base} {args.output}'.")
    print(f"Then write with 'k5rx radio write {args.output} --base {args.base} --port <PORT>'.")
    return 0


def cmd_radio_ports(_args: argparse.Namespace) -> int:
    ports = radio.available_ports()
    if not ports:
        print("No serial ports found")
    for device, description in ports:
        print(f"{device}\t{description}")
    return 0


def cmd_radio_info(args: argparse.Namespace) -> int:
    with radio.K5Radio(args.port) as dev:
        print(f"port={args.port}")
        print(f"version={dev.version}")
        print(f"session=0x{dev.session_id:08X}")
    return 0


def cmd_radio_read(args: argparse.Namespace) -> int:
    with radio.K5Radio(args.port) as dev:
        print(f"Connected: {dev.version}", file=sys.stderr)
        image = dev.read_all(_progress)
    schema.validate_image(image)
    _write_raw(args.output, image)
    print(f"output={args.output} bytes={len(image)} sha256={hashlib.sha256(image).hexdigest()}")
    print(f"Use this file as --base when importing CSV or writing an edited RAW image: {args.output}")
    return 0


def cmd_radio_write(args: argparse.Namespace) -> int:
    if not args.base.is_file():
        raise schema.ValidationError(
            f"--base RAW not found: {args.base}. "
            "Create a fresh baseline first with 'k5rx radio read backup.raw --port <PORT>'."
        )
    base = _read_raw(args.base)
    updated = _read_raw(args.raw)
    blocks = schema.assert_safe_change(base, updated)
    errors = model.validate_memories(updated)
    if errors:
        raise schema.ValidationError("new EEPROM image is invalid:\n" + "\n".join(errors[:20]))
    if not blocks:
        print("No changes")
        return 0
    print(f"planned_changed_blocks={len(blocks)}", file=sys.stderr)
    if not args.yes:
        if not sys.stdin.isatty():
            raise schema.ValidationError("radio write requires --yes when stdin is not interactive")
        answer = input("Type WRITE to continue with EEPROM write: ").strip()
        if answer != "WRITE":
            print("Cancelled", file=sys.stderr)
            return 1
    with radio.K5Radio(args.port) as dev:
        print(f"Connected: {dev.version}", file=sys.stderr)
        chunks = dev.write_image(updated, base_image=base, progress=_progress)
    print(f"OK verified_transactions={chunks} changed_blocks={len(blocks)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="k5rx", description="K5RX RX-only EEPROM and radio tools")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    top = parser.add_subparsers(dest="group", required=True)

    eeprom = top.add_parser("eeprom", help="RAW EEPROM image operations")
    esub = eeprom.add_subparsers(dest="command", required=True)
    p = esub.add_parser("validate", help="validate RX_ONLY Schema v2 RAW image")
    p.add_argument("raw", type=Path)
    p.set_defaults(func=cmd_eeprom_validate)
    p = esub.add_parser("inspect", help="show RAW image summary")
    p.add_argument("raw", type=Path)
    p.add_argument("--memories", action="store_true", help="also print populated Memory slots")
    p.set_defaults(func=cmd_eeprom_inspect)
    p = esub.add_parser("diff", help="compare two RAW images")
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.set_defaults(func=cmd_eeprom_diff)

    csvp = top.add_parser("csv", help="CSV template/import/export/validation")
    csub = csvp.add_subparsers(dest="command", required=True)
    p = csub.add_parser("template", help="create a canonical CSV with all 400 required Memory rows")
    p.add_argument("csv", type=Path, help="output CSV path")
    p.add_argument("--no-banks", action="store_true", help="omit B1..B8 Bank-name rows")
    p.set_defaults(func=cmd_csv_template)
    p = csub.add_parser("validate", help="validate canonical CSV structure")
    p.add_argument("csv", type=Path)
    p.set_defaults(func=cmd_csv_validate)
    p = csub.add_parser("export", help="export RAW EEPROM to CSV")
    p.add_argument("raw", type=Path)
    p.add_argument("csv", type=Path)
    p.add_argument("--no-banks", action="store_true", help="omit B1..B8 Bank-name rows")
    p.set_defaults(func=cmd_csv_export)
    p = csub.add_parser(
        "import",
        help="apply CSV visible fields to a base RAW image",
        description=(
            "Apply a complete 400-Memory CSV to a lossless RAW baseline. "
            "The baseline preserves fields that are intentionally absent from CSV."
        ),
        epilog=(
            "Typical workflow: k5rx radio read backup.raw --port <PORT>; "
            "k5rx csv import channels.csv --base backup.raw --output updated.raw; "
            "k5rx eeprom diff backup.raw updated.raw"
        ),
    )
    p.add_argument("csv", type=Path)
    p.add_argument(
        "--base",
        required=True,
        type=Path,
        help="fresh lossless RAW backup, normally created by 'k5rx radio read backup.raw --port <PORT>'",
    )
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--no-banks", action="store_true", help="ignore B1..B8 rows and preserve base Bank names")
    p.set_defaults(func=cmd_csv_import)

    rp = top.add_parser("radio", help="normal-mode radio EEPROM operations")
    rsub = rp.add_subparsers(dest="command", required=True)
    p = rsub.add_parser("ports", help="list serial ports")
    p.set_defaults(func=cmd_radio_ports)
    p = rsub.add_parser("info", help="open a normal-mode session and show firmware version")
    p.add_argument("--port", required=True)
    p.set_defaults(func=cmd_radio_info)
    p = rsub.add_parser("read", help="read full 8192-byte EEPROM to RAW")
    p.add_argument("output", type=Path)
    p.add_argument("--port", required=True)
    p.set_defaults(func=cmd_radio_read)
    p = rsub.add_parser(
        "write",
        help="write safe differences from base RAW and verify each transaction",
        description=(
            "Write only safe changed EEPROM regions. Before writing, the radio is re-read and must still "
            "match --base byte-for-byte; every write transaction is then read back and verified."
        ),
        epilog=(
            "Create --base immediately before editing with: "
            "k5rx radio read backup.raw --port <PORT>"
        ),
    )
    p.add_argument("raw", type=Path, help="new RAW image")
    p.add_argument(
        "--base",
        required=True,
        type=Path,
        help="fresh RAW backup created by 'k5rx radio read backup.raw --port <PORT>'",
    )
    p.add_argument("--port", required=True)
    p.add_argument("--yes", action="store_true", help="skip interactive WRITE confirmation; intended for automation")
    p.set_defaults(func=cmd_radio_write)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (schema.ValidationError, radio.RadioError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
