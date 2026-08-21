# Serial Protocolの由来 / 参照方針

K5RX-JPN ToolsをApache License 2.0で公開できるように、Serial communication実装のsource hierarchyを明示します。

目的は、**protocol上の事実**と**特定source codeの著作物としての由来**を混同しないことです。

## Primary implementation source

normal-mode EEPROM communicationの一次資料は、companion RX-only Firmware forkがベースとするApache-2.0のF4HWN/DualTachyon Firmware sourceです。

主な該当箇所:

- `app/uart.c`: frame marker、XOR table、session、EEPROM Read/Write command/reply
- `driver/crc.c`: CRC-16/CCITT設定
- `driver/uart.c`: UART設定
- `eeprom-layout.h`: RX_ONLY EEPROM boundary、Factory/Calibration protection

Python/Web clientは、これらFirmware側interfaceを仕様として読み取り、client側で独立実装します。

## Permissive licenseの補助参照

permissive licenseのprojectは、実際にreuseする時点でrepository/file単位のlicenseを確認した上で補助参照にできます。

初期調査で候補となった例:

- F4HWN K5Viewer
- UV Studio
- F4HWN V3 `tools/serialtool`

これらは、port discovery、UI/UX、recovery behavior、browser compatibility、wire behaviorのcross-check等の参考にできます。

ただし、このprojectでprotocol authorityとなるのはFirmware implementationです。

## GPL implementationの扱い

k5progやCHIRP等のGPL implementationは次の用途に限定して参照できます。

- interoperability test
- wire behavior比較
- protocol factの独立確認
- device compatibility調査

それらのimplementation codeを、このApache-2.0 repositoryへコピー、機械的翻訳、構造をそのまま移植することは行いません。

## 新しいprotocol機能を追加する際のrule

1. behaviorを実装しているFirmware側command/layoutを確認する
2. `docs/`へwire contractを記述する
3. そのcontractからPython/Web clientを実装する
4. 可能ならtest vectorまたは実機testを追加する
5. third-party sourceをコピー/改変する場合は、merge前にexact file/revision/license/attributionを記録する

このdocumentはengineering上のprovenance管理方針であり、法的助言ではありません。
