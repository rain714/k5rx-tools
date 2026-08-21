# RX_ONLY EEPROM Schema v2

## Header

```text
0x0000 uint32 magic       0x4B355258 ("K5RX")
0x0004 uint8  version     2
0x0005 uint8  header_size 16
0x0006 uint16 caps
0x0008 uint16 mutable_end 0x1E00
0x000A uint16 channels    400
0x000C uint8  record_size 8
0x000D uint8  name_length 10
0x000E uint8  bank_count  8
```

## Layout

```text
0x0000..0x000F  header
0x0010..0x0C8F  400 x 8-byte Memory records
0x0C90..0x1C2F  400 x 10-byte Memory names
0x1C30..0x1CAF  VFO state
0x1CB0..0x1CEF  RX-only settings
0x1CF0..0x1D2F  FM radio
0x1D30..0x1DAF  8 x 16-byte Bank records
0x1DB0..0x1DCF  welcome strings
0x1DD0..0x1DD7  build options
0x1DD8..0x1DFF  reserved
0x1E00..0x1FFF  factory/calibration
```

Factory/calibration is never writable by K5RX-JPN memory tools.

## Memory record

```text
byte 0..2       frequency low 24 bits (10 Hz units)
byte 3 bit0..2  frequency high 3 bits
       bit3..4  RX code type
       bit5     bandwidth (0 Wide, 1 Narrow)
       bit6     compander
byte 4          RX code (low 7 bits)
byte 5 bit0..2  modulation (0 FM, 1 AM, 2 USB)
       bit3..7  step index
byte 6 bit0..2  Scan List 1..3 mask
       bit3..6  Bank ID (0 unbanked, 1..8 Bank)
byte 7          reserved
```

An erased record is eight `0xFF` bytes. The normal UI/CSV does not expose RX code, code type, step, compander or reserved bits; those bytes/bits are preserved when updating an existing slot.

## Frequency validation

Wide-RX firmware accepts:

```text
18 MHz <= f < 630 MHz
840 MHz <= f <= 1300 MHz
```

The gap from 630 MHz through below 840 MHz is rejected.

## Bank record

There are eight 16-byte Bank records at `0x1D30`. The first ten bytes store the printable-ASCII Bank name. Memory Manager updates only these ten name bytes and preserves the remaining six bytes.
