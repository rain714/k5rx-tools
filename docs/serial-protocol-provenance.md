# Serial Protocol Provenance and Reference Policy

K5RX-JPN Tools is intended to be distributable under Apache License 2.0. This document records the source hierarchy used when implementing serial communication so that protocol facts are not confused with source-code provenance.

## Primary implementation source

The primary source for normal-mode EEPROM communication is the Apache-2.0 licensed F4HWN/DualTachyon firmware source used by the companion RX-only firmware fork.

Relevant firmware areas include:

- `app/uart.c`: frame markers, XOR table, session command, EEPROM read/write commands and replies.
- `driver/crc.c`: CRC-16/CCITT configuration.
- `driver/uart.c`: UART configuration.
- `eeprom-layout.h`: RX_ONLY EEPROM boundaries and factory/calibration protection.

The Python and Web clients are independent client-side implementations of those documented firmware interfaces.

## Permissive supplementary references

Permissively licensed projects may be used as secondary references after checking the applicable repository and file-level license at the time code is considered for reuse. Examples investigated during initial design include F4HWN K5Viewer, UV Studio, and the F4HWN V3 `tools/serialtool` family.

Secondary references are useful for serial-port discovery, UI/UX, recovery behavior, browser compatibility and cross-checking observed protocol behavior. They do not supersede the firmware implementation as the protocol authority for this project.

## GPL interoperability references

GPL implementations such as k5prog and CHIRP may be used for:

- interoperability testing,
- comparing wire behavior,
- independently confirming protocol facts,
- diagnosing device compatibility.

Their implementation code must not be copied, mechanically translated, or used as the structural basis of Apache-2.0 source in this repository.

## Development rule

When adding protocol functionality:

1. Identify the firmware-side command/layout implementing the behavior.
2. Document the wire contract in `docs/`.
3. Implement the Python/Web client from that contract.
4. Add a test vector or device test where practical.
5. If third-party source code is copied or adapted, record the exact file, revision, license and required attribution before merge.

This policy is engineering provenance guidance, not legal advice.
