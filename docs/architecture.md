# K5RX Tools アーキテクチャ

## 目的

K5RX Toolsは、RX_ONLY EEPROM Schemaを共通仕様として、CLIとWebの2つの提供形態を同一repositoryで管理します。

```text
                RX_ONLY Schema v2
                       │
          ┌────────────┴────────────┐
          │                         │
     Python CLI                 Web App
          │                         │
   pyserial / files           Web Serial / files
          │                         │
          └──────── RAW / CSV ──────┘
```

Firmware本体はF4HWN forkの別repositoryとし、Tools repositoryはFirmware source treeから独立してreleaseできる構成にします。

## 正本となるデータ形式

### RAW

8192-byte EEPROM imageをlossless source of truthとします。

RAWにはMemory以外の設定やhidden field、Factory/Calibration領域も含まれるため、backup/recovery用途ではCSVではなくRAWを使用します。

### CSV

CSVは人間が編集するための交換形式です。

- M001〜M400を必須とする
- B1〜B8 Bank name rowはoptional
- hidden fieldは含めない
- Import時はbase RAWからhidden fieldを保持する

## Python module

```text
src/k5rx_tools/
├── schema.py      EEPROM layout / validation / write allowlist
├── model.py       Memory / Bank codec
├── csvio.py       CSV template / import / export / validation
├── protocol.py    normal-mode serial framing / command codec
├── radio.py       pyserial transport / read / write / verify
└── cli.py         argparse CLI
```

Runtime dependencyはpyserialのみとし、CLI frameworkは導入しません。

## Web

初期版は`web/index.html`のsingle static applicationです。

理由:

- backend不要
- npm build不要
- GitHub Pagesへそのままdeploy可能
- 現在の機能規模では1ファイルでもreview可能

将来、詳細editorや複数画面などで複雑化した段階でTypeScript/Vite等へ分割します。その際にUI stringもresource化してi18n対応します。

## Shared contract

PythonとWebでsource code自体を共有することは目的にしません。代わりに次を共通contractとします。

- EEPROM Schema document
- CSV format document
- Serial protocol document
- safety invariant
- test vector / regression test

PythonとJavaScriptで同じRAW/CSVを扱ったときに同じ意味になることを重要視します。

## Write safety

CLI/Web双方で次を守ります。

1. Schema mismatchを拒否
2. dirty blockを8-byte単位で抽出
3. Memory/nameとBank以外のdirty blockを拒否
4. Factory/Calibration `0x1E00..0x1FFF`を絶対にWriteしない
5. Write直前にRadio全体を再Readし、editing baselineと一致することを確認
6. contiguous blockを最大128-byte transactionへまとめる
7. transactionごとにread-back verify

速度よりこのinvariantを優先します。

## Distribution

### CLI

Python distribution name: `k5rx-tools`

```bash
uvx k5rx-tools --help
```

Primary commandは`k5rx`です。

### Web

`web/`をGitHub Pagesへdeployします。

### CI

- Python 3.11 / 3.12 / 3.13 pytest
- package build
- Web JavaScript syntax check
- GitHub Pages deployment

## Firmware flashing

EEPROM managementとはfailure/recovery modelが異なるため、初期stable surfaceには含めません。将来`firmware` moduleとして独立したsafety testとprovenanceを持たせます。

## Versioning

Python CLIとWebは同じTools versionを使用します。EEPROM Schema versionはTools versionとは独立して管理します。
