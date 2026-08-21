# Normal-mode Serial Protocol

Status: implementation specification for K5RX-JPN Tools.

## Transport

- 38400 baud
- 8 data bits
- 1 stop bit
- no parity
- no flow control

## Frame

```text
AB CD
LEN_LO LEN_HI
PAYLOAD...
CRC_LO CRC_HI
DC BA
```

The payload and CRC bytes are XOR-obfuscated using the repeating 16-byte table:

```text
16 6C 14 E6 2E 91 0D 40 21 35 D5 40 13 03 E9 80
```

CRC is CRC-16/CCITT with initial value 0 and polynomial 0x1021 (the commonly named XMODEM form).

## Command payload header

The decoded payload starts with two little-endian 16-bit values:

```text
command_id, data_size
```

The byte representation therefore appears as, for example, `14 05 04 00` for command `0x0514` with four data bytes.

## Session (`0x0514`)

Request data:

```text
uint32 session_id
```

The value is a session identifier rather than a wall-clock timestamp. Clients generate a fresh random 32-bit value per connection and reuse it for EEPROM read/write commands in that session.

Expected reply: `0x0515`, including firmware version/state.

## Read EEPROM (`0x051B`)

Request data:

```text
uint16 offset
uint8  size
uint8  padding
uint32 session_id
```

Maximum supported transfer size used by this project: `0x80` bytes.

Expected reply `0x051C` data:

```text
uint16 offset
uint8  size
uint8  padding
uint8  data[size]
```

## Write EEPROM (`0x051D`)

Request data:

```text
uint16 offset
uint8  size
bool   allow_password
uint32 session_id
uint8  data[size]
```

K5RX-JPN Tools writes aligned 8-byte blocks and coalesces adjacent allowed blocks up to 128 bytes per request.

Expected reply: `0x051E`, containing the written offset.

Every write request is followed by an EEPROM read of the same range and byte-for-byte verification.

## Tool write allowlist

The Memory Manager intentionally has a narrower write policy than the firmware protocol itself:

```text
0x0010..0x1C2F  Memory records and names
0x1D30..0x1DAF  Bank table
```

`0x1E00..0x1FFF` is factory/calibration data and is never writable.

## Source of specification

The normal-mode protocol above is derived from the Apache-2.0 firmware implementation, principally F4HWN/DualTachyon `app/uart.c` and `driver/crc.c`, plus observed compatible device behavior. See `serial-protocol-provenance.md`.
