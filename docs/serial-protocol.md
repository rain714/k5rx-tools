# Normal-mode Serial Protocol

K5RX-JPN Toolsが通常起動中のRadioとEEPROM通信するために使用するprotocol仕様です。

## Transport

- 38400 baud
- 8 data bits
- 1 stop bit
- parityなし
- flow controlなし

## Frame

```text
AB CD
LEN_LO LEN_HI
PAYLOAD...
CRC_LO CRC_HI
DC BA
```

PAYLOADとCRC byteは次の16-byte tableを繰り返してXOR obfuscationします。

```text
16 6C 14 E6 2E 91 0D 40 21 35 D5 40 13 03 E9 80
```

CRCはinitial value 0、polynomial `0x1021` のCRC-16/CCITT（一般にXMODEMと呼ばれる形）です。

## Command payload header

decode後のpayload先頭はlittle-endian uint16 x 2です。

```text
command_id, data_size
```

例えばcommand `0x0514`、data size 4の場合はbyte列として:

```text
14 05 04 00
```

となります。

## Session (`0x0514`)

Request data:

```text
uint32 session_id
```

Firmware source上ではwall-clock timestampそのものではなくsession identifierとして扱われます。

K5RX-JPN Toolsは接続ごとにrandom 32-bit valueを生成し、そのsession内のRead/Writeで同じ値を使用します。

Expected reply: `0x0515`

replyにはFirmware version/stateが含まれます。

## Read EEPROM (`0x051B`)

Request data:

```text
uint16 offset
uint8  size
uint8  padding
uint32 session_id
```

K5RX-JPN Toolsが使用する最大transfer sizeは`0x80` byteです。

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

Memory tool側では8-byte alignmentを要求し、隣接する許可済みchanged blockを最大128 byteまでまとめます。

Expected reply: `0x051E`

replyにはwritten offsetが含まれます。

各Write requestの後、同じoffset/sizeをReadし、byte-for-byteでVerifyします。

## Tool側Write allowlist

Firmware protocol自体が扱える領域より、K5RX-JPN Memory ToolのWrite policyを意図的に狭くします。

```text
0x0010..0x1C2F  Memory records / names
0x1D30..0x1DAF  Bank table
```

`0x1E00..0x1FFF` Factory/Calibrationは絶対にWriteしません。

## 仕様の由来

このnormal-mode protocolは、Apache-2.0のF4HWN/DualTachyon Firmware implementation、主として`app/uart.c`と`driver/crc.c`、および互換実機挙動を一次資料として整理しています。

詳細は[`serial-protocol-provenance.md`](serial-protocol-provenance.md)を参照してください。
