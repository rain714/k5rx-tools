# K5RX Tools

[日本語 README](README.md)

K5RX Tools is a companion toolset for the Japanese-oriented RX-only firmware based on F4HWN for the Quansheng UV-K5/K6 V1 family.

It provides the same RX_ONLY EEPROM model through two interfaces:

- **CLI (`k5rx`)** — Python tools for radio EEPROM read/write, RAW/CSV conversion, inspection and validation.
- **Web Memory Manager** — a browser-based 400-memory editor using Web Serial and deployable as a static GitHub Pages site.

The initial release targets **RX_ONLY EEPROM Schema v2**.

## Quick start

```bash
uv sync
uv run k5rx --help
```

After publication to PyPI:

```bash
uvx k5rx-tools --help
```

Create a complete editable CSV template:

```bash
uv run k5rx csv template channels.csv
```

The template contains B1..B8 followed by every required physical Memory slot M001..M400. Use `--no-banks` to omit Bank-name rows.

Typical safe workflow:

```bash
# 1. Read a fresh lossless baseline
uv run k5rx radio read backup.raw --port /dev/cu.usbserial-10

# 2. Export/edit CSV, or start from a template
uv run k5rx csv export backup.raw channels.csv
# edit channels.csv
uv run k5rx csv validate channels.csv

# 3. Apply visible CSV fields to the RAW baseline
uv run k5rx csv import channels.csv --base backup.raw --output updated.raw

# 4. Review
uv run k5rx eeprom diff backup.raw updated.raw

# 5. Write safe differences and verify
uv run k5rx radio write updated.raw --base backup.raw --port /dev/cu.usbserial-10
```

`--base` is important: CSV intentionally omits several hidden per-memory fields. The base RAW preserves those fields. Immediately before writing, the CLI re-reads the full radio EEPROM and refuses to continue unless it still matches `--base` byte-for-byte.

## Safety model

- Schema mismatch blocks writes.
- Factory/calibration `0x1E00..0x1FFF` is never writable.
- Normal writes are restricted to Memory records/names and Bank names.
- CLI writes require explicit `WRITE` confirmation unless automation opts into `--yes`.
- Every write transaction is read back and verified.
- CSV always contains all physical slots M001..M400 exactly once.
- Hidden record fields are preserved when CSV updates an existing slot.

## CSV format

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

Optional Bank rows precede Memory rows:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

Import accepts legacy `channel` as the first-column header for compatibility.

## Web app

`web/index.html` runs entirely in the browser. EEPROM/CSV data is not uploaded to a backend. Web Serial requires a compatible secure-context browser; Chrome/Edge over HTTPS or localhost are the primary targets.

Local use:

```bash
python3 -m http.server 8000 --directory web
```

Then open `http://localhost:8000/`.

## Development

```bash
make all
uv run --extra dev pytest
uv build
```

CI runs Python tests on 3.11, 3.12 and 3.13, checks Web JavaScript syntax, and can deploy `web/` to GitHub Pages.

## Protocol provenance and license

K5RX Tools is licensed under Apache-2.0. The normal-mode serial implementation is based on the Apache-2.0 F4HWN/DualTachyon firmware source and documented device behavior. GPL implementations such as k5prog and CHIRP are interoperability references only and are not implementation sources for this repository.

Firmware flashing is intentionally deferred from the initial stable CLI surface and will be treated as a separate safety/recovery workflow.
