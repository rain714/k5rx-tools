# Architecture

## Scope

K5RX-JPN Tools is a monorepo containing two front ends over one documented RX_ONLY data model:

- Python CLI/library for local automation and file/radio workflows.
- Browser Memory Manager for interactive editing with Web Serial.

The firmware fork remains a separate repository. This repository is a companion toolset and may later support compatible schemas from other firmware projects.

## Stable contracts

The repository treats three specifications as the shared contracts between Python and Web implementations:

1. EEPROM Schema v2.
2. CSV format.
3. Normal-mode serial framing and EEPROM commands.

Python and Web do not share implementation source code. They are checked against the same specification and portable test vectors instead.

## Data flow

```text
Radio <-> Serial transport <-> RAW EEPROM image <-> Schema codec <-> Memory model <-> CSV/UI
```

The 8192-byte RAW EEPROM image is the lossless representation. CSV is intentionally lossy and human-editable.

## Python package

```text
src/k5rx_jpn/
  schema.py       constants and schema validation
  model.py        Memory/Bank model and RAW codec
  csvio.py        canonical CSV import/export
  protocol.py     serial frame codec and command builders
  radio.py        pyserial transport, EEPROM read/write/verify
  cli.py          argparse command surface
```

The initial CLI surface is:

```text
k5rx
  eeprom validate RAW
  eeprom inspect RAW
  eeprom diff OLD NEW
  csv export RAW CSV [--no-banks]
  csv import CSV --base RAW --output RAW [--no-banks]
  csv validate CSV
  radio info --port PORT
  radio read OUTPUT --port PORT
  radio write NEW --base OLD --port PORT
```

`radio write` requires a base RAW image. Only bytes that differ between base and new image are candidates for write, and every changed 8-byte block must be inside the explicit Memory/Bank allowlist. Adjacent blocks are coalesced up to 128 bytes and read back after every transaction.

## Web application

The current beta Memory Manager is initially published as a static app under `web/`. It retains the proven single-page behavior while the Python contracts and test vectors are established. A later refactor may split it into TypeScript modules without changing the user-facing data formats.

GitHub Pages is the intended deployment target because the app requires no server-side state and Web Serial requires HTTPS/localhost.

## Firmware flashing

Firmware flashing is deliberately separated from EEPROM management. It is not part of the initial stable CLI/API. A future `firmware` module may be added after protocol provenance, recovery behavior, and write guards are documented and tested independently.

## Versioning

The repository uses one tool version for Python and Web. EEPROM schema versions remain independent of tool versions.
