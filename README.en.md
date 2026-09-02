# K5RX Tools

[日本語 README](README.md)

**K5RX Tools** is a companion toolset for the receive-focused **K5RX firmware** for Quansheng UV-K5 / UV-K6 V1 radios.

K5RX firmware: https://github.com/rain714/k5rx-firmware

For most users, the **Web Memory Manager** is the recommended interface. The Python CLI is available for file-based RAW/CSV workflows, inspection, automation, and scripted radio access.

> [!IMPORTANT]
> K5RX Tools targets **K5RX EEPROM Schema v2**. It is not a generic editor for stock or regular F4HWN EEPROM layouts.

## Web Memory Manager

After GitHub Pages is enabled, the Web app is available at:

**https://rain714.github.io/k5rx-tools/**

The app runs entirely in the browser and communicates with the radio directly through Web Serial. EEPROM and CSV contents are not uploaded to a K5RX Tools backend.

Typical workflow:

1. Start the radio normally, not in firmware flashing mode.
2. Connect from a Web Serial capable browser such as Chrome or Edge.
3. Read the EEPROM and save a full RAW backup.
4. Edit Memory, Scan List and Bank settings.
5. Review the diff.
6. Write and verify the changed blocks.

The Web app supports 400 Memory slots, Scan Lists 1-3, eight Banks, bulk edit, Undo/Redo, CSV Import/Export, CSV template generation, RAW backup, stale-baseline protection, and per-transaction read-back verification.

## Back up the EEPROM first

K5RX uses an EEPROM layout that differs from stock firmware and regular F4HWN. Keep a full 8192-byte RAW EEPROM backup, especially before first migrating to K5RX.

Write safety rules include:

- Reject non-Schema-v2 EEPROMs.
- Never write factory/calibration `0x1E00..0x1FFF`.
- Reject unexpected changes outside Memory records/names and Bank names.
- Re-read the full radio before writing and require the baseline to match.
- Read back and verify every write transaction byte-for-byte.

These checks reduce risk but do not guarantee recovery from cable disconnects, power loss, or hardware failure. Keep the original RAW backup separately.

## Not a firmware flasher

K5RX Tools v0.1.0 manages EEPROM/Memory data. It does not flash firmware.

To install K5RX firmware, use the `packed.bin` from a K5RX firmware release with a compatible F4HWN Web Flasher workflow.

## CLI

From the repository:

```bash
git clone https://github.com/rain714/k5rx-tools.git
cd k5rx-tools
uv sync
uv run k5rx --help
```

Typical safe workflow:

```bash
uv run k5rx radio read backup.raw --port /dev/cu.usbserial-10
uv run k5rx csv export backup.raw channels.csv
# edit channels.csv
uv run k5rx csv validate channels.csv
uv run k5rx csv import channels.csv --base backup.raw --output updated.raw
uv run k5rx eeprom diff backup.raw updated.raw
uv run k5rx radio write updated.raw --base backup.raw --port /dev/cu.usbserial-10
```

`--base` preserves hidden per-memory fields that are intentionally omitted from CSV and also acts as the stale-write baseline.

CLI help and errors are primarily in English to avoid terminal encoding issues.

## CSV format

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

Optional Bank rows precede all 400 Memory rows:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

Generate a complete template with:

```bash
uv run k5rx csv template channels.csv
```

## Local Web use

```bash
python3 -m http.server 8000 --directory web
```

Then open `http://localhost:8000/`.

## Documentation

See [`docs/README.md`](docs/README.md) for the documentation index, including CLI usage, Web Memory Manager behavior, CSV format, EEPROM Schema v2, serial protocol and architecture.

## Development

```bash
make all
uv run --extra dev pytest
uv build
```

CI tests Python 3.11 / 3.12 / 3.13, builds the package, validates the inline Web JavaScript, and deploys `web/` through GitHub Pages.

## Protocol provenance and license

K5RX Tools is licensed under **Apache License 2.0**. The normal-mode serial protocol implementation is independently implemented from Apache-2.0 F4HWN / DualTachyon firmware source and documented device behavior. GPL projects such as k5prog and CHIRP are interoperability references only, not implementation sources for this repository.
