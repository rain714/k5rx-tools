# K5RX-JPN Tools

K5RX-JPN Tools is a companion toolset for the Japanese-oriented RX-only firmware based on F4HWN for the Quansheng UV-K5/K6 V1 family.

The project provides the same RX_ONLY EEPROM model through two interfaces:

- **CLI (`k5rx`)** — local Python tools for radio EEPROM read/write, RAW/CSV conversion, inspection and validation.
- **Web Memory Manager** — browser-based 400-memory editor using Web Serial, intended to be deployable as a static GitHub Pages site.

The current implementation targets **RX_ONLY EEPROM Schema v2** only.

## Safety model

The tool treats the full 8192-byte `.raw` EEPROM image as the lossless backup format. CSV is a human-editable interchange format and intentionally exposes only the fields managed by the normal Memory Manager UI.

The EEPROM writer follows these invariants:

- Schema mismatch blocks write operations.
- Factory/calibration `0x1E00..0x1FFF` is never writable.
- Normal memory-tool writes are allowlisted to Memory records/names and Bank names.
- Radio writes are followed by read-back verification.
- CSV import never silently compacts or renumbers physical slots M001..M400.
- Hidden per-memory record fields are preserved when CSV updates an already-populated slot.

## Quick start

Development:

```bash
uv sync
uv run k5rx --help
```

Once published as a Python package:

```bash
uvx k5rx-jpn --help
```

Examples:

```bash
# Validate and inspect a RAW backup
uv run k5rx eeprom validate backup.raw
uv run k5rx eeprom inspect backup.raw

# RAW -> CSV
uv run k5rx csv export backup.raw channels.csv

# CSV -> RAW while preserving hidden fields from the base image
uv run k5rx csv import channels.csv --base backup.raw --output updated.raw

# Read the complete EEPROM from a normally booted radio
uv run k5rx radio read backup.raw --port /dev/cu.usbserial-10

# Write only allowed changed regions and verify them
uv run k5rx radio write updated.raw --base backup.raw --port /dev/cu.usbserial-10
```

## CSV format

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

Memory rows use `M001`..`M400`. Optional Bank-name rows use `B1`..`B8` and appear before Memory rows:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

For backward compatibility, import also accepts `channel` as the first-column header.

See [`docs/csv-format.md`](docs/csv-format.md).

## Web app

The Web Memory Manager is under `web/`. It runs entirely in the browser. EEPROM/CSV data is not uploaded to a backend.

Web Serial requires a compatible browser and secure context. Chrome/Edge over HTTPS or localhost are the primary supported environments.

## Project layout

```text
src/k5rx_jpn/     Python library and CLI
web/              browser Memory Manager
docs/             format/protocol/architecture specifications
tests/            Python regression tests
testdata/         portable test vectors and examples
.github/workflows CI and GitHub Pages deployment
```

## Protocol provenance and licensing

K5RX-JPN Tools is licensed under **Apache License 2.0**.

The normal-mode serial protocol implementation is based on the Apache-2.0 licensed F4HWN/DualTachyon firmware source and documented device behavior. GPL implementations such as k5prog and CHIRP may be used for interoperability comparison but are not implementation sources for this repository.

See [`docs/serial-protocol-provenance.md`](docs/serial-protocol-provenance.md).

## Firmware flashing

Firmware flashing is intentionally **not part of the initial stable CLI surface**. EEPROM editing and firmware flashing have different failure modes and safety requirements. The architecture reserves a separate `firmware` module for a future implementation after permissively licensed reference behavior and recovery handling are fully documented.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
