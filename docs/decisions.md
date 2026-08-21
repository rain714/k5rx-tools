# 初期設計上の判断

K5RX-JPN Toolsの初期公開に向けて採用した判断を記録します。初回public release前であれば比較的容易に変更できるものも含みます。

## Repository / Naming

- Project family: **K5RX-JPN Tools**
- Repository: `uv-k5-rx-jpn-tools`
- Python distribution: `k5rx-jpn`
- Primary CLI command: `k5rx`
- `k5rx-jpn` も明示的aliasとしてinstall
- FirmwareはF4HWN forkの別repositoryとして管理

## Language

- JPN向けprojectのためREADMEとuser-facing documentは**日本語をprimary**とする。
- `README.en.md` をEnglish entry pointとして用意する。
- CLI help/error/outputはterminal encoding問題を避けるため英語を基本とする。
- Web UIは初期版では日本語primary。
- WebをTypeScript等へ分割する段階で表示文字列をresource化し、English等を追加できるi18n構成へ移行する。
- v0.1で無理にi18n frameworkを入れず、single static HTMLという配布上の単純さを優先する。

## License / Provenance

- Project license: Apache-2.0
- normal-mode Serial protocolの一次資料: Apache-2.0のF4HWN/DualTachyon Firmware source
- GPLのk5prog/CHIRPはinteroperability referenceのみに使用し、実装sourceとしてコピー・翻案しない

## Python

- Minimum Python: 3.11
- `pyproject.toml` + Hatchling
- `uv`を推奨runner/package workflowとする
- Runtime dependencyはpyserialのみ
- CLI parserは標準libraryのargparse
- pytestはdevelopment dependency

## EEPROM / CSV

- 8192-byte RAW EEPROM imageをlossless source of truthとする
- 初期版はRX_ONLY Schema v2のみ対応
- CSVはM001〜M400を各1回ずつ必須とする
- canonical先頭列は`record`、旧`channel`はImportのみ互換受付
- B1〜B8 Bank-name rowはoptionalだがExport/Importではdefault ON
- `k5rx csv template`で全400 Memory rowを含むcanonical templateを生成できる
- templateはdefaultでB1〜B8を含み、初期名称はBANK1〜BANK8
- Bank nameを保持したい場合は`--no-banks`を利用できる
- CLI CSV importではhidden field保持のため`--base` RAWを必須とする
- Memory toolからのWriteはMemory/name領域とBank領域のみallowlistする

## Radio Write Safety

- CLI writeでは`--base`を必須とする
- Write直前にRadio EEPROM全体をReadし、`--base`とbyte-for-byte一致することを要求する
- 通常のinteractive writeでは`WRITE`入力を必須とする
- automationのみ明示的に`--yes`を使用できる
- changed 8-byte blockを最大128 byteにcoalesceする
- transactionごとにread-back verifyする
- Factory/Calibration `0x1E00..0x1FFF`は絶対にWriteしない
- CLI help/errorは、可能な限り次に実行すべきcommandを具体的に示す

## Web

- 初期public Web appはdependency-freeの`web/index.html` 1ファイル
- backend不要。GitHub Pagesをhosted formとして想定
- Chrome/Edge Web Serial + HTTPS/localhostをprimary targetとする
- CLIと同じbaseline check / allowlist / read-back verifyを採用
- Undo/Redoは最大30 EEPROM snapshot
- TypeScript/Vite分割は複雑性が増してから行う
- i18nもその分割時に表示文字列resourceを独立させて導入する

## Firmware Flashing

- 初期stable tool surfaceには含めない
- EEPROMとはfailure/recovery modelが異なるため、別module/workflowとして追加する
- permissive licenseの参照実装、recovery behavior、実機testを整理してから実装する

## Test Data

- 初期testはphysical radio dumpを公開せずsynthetic EEPROM imageを生成して使用する
- 実機dumpをfixtureとして公開する場合はdevice/user固有情報が含まれないか明示的reviewを行う
