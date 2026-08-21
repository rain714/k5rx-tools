# K5RX-JPN CSV Format

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

New exports always use `record`. Imports also accept legacy `channel` as the first-column header.

## Memory rows

Memory rows use `M001` through `M400`. All 400 physical slots are required exactly once so spreadsheet editing cannot silently compact or renumber EEPROM slots.

Example:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
M002,TOWER,118.80000,AM,Wide,1,1,0,1
```

An empty slot has empty `name/frequency/modulation/bandwidth` fields and zero List/Bank fields.

## Optional Bank rows

Bank names can be carried without changing the header. Bank rows use `B1`..`B8`, use only `record` and `name`, and are placed before Memory rows when exported.

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

Other fields on a Bank row must be empty.

Export includes Bank rows by default; `--no-banks` omits them. Import applies detected Bank rows by default; `--no-banks` preserves the Bank names from the base RAW image.

## Field rules

- `name`: printable ASCII, maximum 10 bytes.
- `frequency`: MHz decimal, validated against firmware RX ranges.
- `modulation`: `FM`, `AM`, or `USB` (numeric 0..2 also accepted on import).
- `bandwidth`: `Wide` or `Narrow` (`W/N` or 0/1 also accepted on import).
- `list1..list3`: boolean values; `1/0`, `true/false`, `on/off`, `yes/no` are accepted.
- `bank`: integer 0..8; 0 means UNBANKED.

## Hidden record fields

CSV is not a lossless backup. It does not expose RX code/type, step, compander, or reserved record fields.

`csv import` therefore requires a `--base` RAW image. For each populated target Memory slot, import starts from that slot's existing 8-byte record and replaces only CSV-visible fields. If the base slot is erased, sensible defaults are initialized for hidden fields.

Use RAW backups, not CSV, when exact EEPROM restoration is required.
