# K5RX Tools

[English README](README.en.md)

K5RX Tools は、Quansheng UV-K5/K6 V1 系の **日本向け受信専用（RX-only）Firmware** を管理するためのツール群です。現在は F4HWN ベースの RX_ONLY EEPROM Schema v2 を対象としています。

同じEEPROM仕様を、用途に応じて2つの形で提供します。

- **CLI (`k5rx`)** — Python / pyserial ベース。RadioのRead/Write、RAW/CSV変換、検証、差分確認を行います。
- **Web Memory Manager** — Web Serialを使用する400 Memory対応ブラウザツール。GitHub Pagesでの公開を想定しています。

## 最初に理解しておくこと

このツールでは、8192-byteの `.raw` EEPROM imageを**完全なバックアップ形式**として扱います。

CSVはExcel等で編集しやすい形式ですが、CTCSS/DCS、Step、Companderなど通常画面に出さないfieldを意図的に含みません。そのため、CSVからRAWを作る際は、hidden fieldを保持するための元RAW（`--base`）が必要です。

安全性のため、Radio Writeでは次を必須としています。

- EEPROM Schema不一致ならWriteしない。
- Factory/Calibration領域 `0x1E00..0x1FFF` は絶対にWriteしない。
- Memory record/name と Bank name以外の意図しない変更を拒否する。
- Write直前にRadio全体を再Readし、`--base` と完全一致することを確認する。
- 通常のCLI Writeでは `WRITE` と明示入力する。
- 各Write transaction後に同じ範囲をReadし、byte単位でVerifyする。

## インストール / 実行

開発中のrepositoryから実行する場合:

```bash
uv sync
uv run k5rx --help
```

PyPI公開後は、インストールせず一時実行できます。

```bash
uvx k5rx-tools --help
```

CLI自身のhelp/error messageは、terminal文字コードによる問題を避けるため**英語**を基本とします。

具体的な操作手順と典型errorからの復旧方法は [`docs/cli.md`](docs/cli.md) にまとめています。Document一覧は [`docs/README.md`](docs/README.md) を参照してください。

## CSVを新規作成する

CSVはM001〜M400の全400 Memory rowが必須です。手作業で400行を作る必要はなく、templateを生成できます。

```bash
uv run k5rx csv template channels.csv
```

デフォルトでは次の順で生成します。

```text
header
B1 ... B8
M001 ... M400
```

Bank rowの初期名称は `BANK1`〜`BANK8` です。Bank nameをCSVで管理しない場合:

```bash
uv run k5rx csv template channels.csv --no-banks
```

編集後は、Radioへ反映する前にCSV単体で検証できます。

```bash
uv run k5rx csv validate channels.csv
```

## 推奨ワークフロー: Radio → CSV編集 → Radio

### 1. Radioから新しいRAW backupを取得

RadioはFirmware書込みモードではなく、通常起動してください。

まずportを確認できます。

```bash
uv run k5rx radio ports
```

次にEEPROM全体をReadします。

```bash
uv run k5rx radio read backup.raw --port /dev/cu.usbserial-10
```

この `backup.raw` が、この編集作業の**baseline**になります。CSV importとRadio writeの両方で使用するため、そのまま保持してください。

### 2. RAWをCSVへExport

```bash
uv run k5rx csv export backup.raw channels.csv
```

CSVをExcelやテキストエディタで編集します。

```bash
uv run k5rx csv validate channels.csv
```

### 3. CSVをRAWへ反映

```bash
uv run k5rx csv import channels.csv \
  --base backup.raw \
  --output updated.raw
```

`--base backup.raw` は、CSVに存在しないhidden fieldを保持するために必要です。

### 4. 差分確認

```bash
uv run k5rx eeprom diff backup.raw updated.raw
```

想定したMemory/Bankのみが変更されていることを確認します。

### 5. RadioへWrite + Verify

```bash
uv run k5rx radio write updated.raw \
  --base backup.raw \
  --port /dev/cu.usbserial-10
```

Write直前にRadioを再Readします。Radioが `backup.raw` 取得後に別のツール等で変更されていた場合は、上書きせず停止します。その場合は、再度

```bash
uv run k5rx radio read backup-new.raw --port /dev/cu.usbserial-10
```

で新しいbaselineを取得し、そのRAWを使ってCSV変更を再適用してください。

`--yes` は対話確認を省略するautomation向けoptionです。通常操作では使用しないことを推奨します。

## RAWのみを扱う

```bash
# Schema / Memory validation
uv run k5rx eeprom validate backup.raw

# 概要表示
uv run k5rx eeprom inspect backup.raw

# 使用中Memoryも表示
uv run k5rx eeprom inspect backup.raw --memories

# RAW同士の差分
uv run k5rx eeprom diff before.raw after.raw
```

## CSV仕様

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

Memoryは `M001`〜`M400`、Bank name definitionは `B1`〜`B8` を使用します。

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

Import時のみ、旧形式との互換性のため先頭列名 `channel` も受け付けます。新規Exportは常に `record` です。

詳細: [`docs/csv-format.md`](docs/csv-format.md)

## Web Memory Manager

`web/index.html` はbackend不要のstatic Web applicationです。

- RadioとはWeb Serialで直接通信します。
- RAW/CSV内容をserverへuploadしません。
- Chrome / Edge + HTTPS または localhost を主対象とします。
- CLIと同じく、Factory/Calibration write guard、baseline再確認、read-back verifyを行います。

ローカル実行:

```bash
python3 -m http.server 8000 --directory web
```

その後 `http://localhost:8000/` を開きます。

GitHub Actionsから `web/` をそのままGitHub Pagesへdeployできる構成です。

Web UIはJPN向けのため、**初期版は日本語をprimary language**とします。将来UIをTypeScript等へ分割する際に文字列resourceを分離し、英語等へ切り替えられるi18n構成へ移行する方針です。

詳細: [`docs/web-memory-manager.md`](docs/web-memory-manager.md)

## 開発 / Test

```bash
# 軽量なsyntax/smoke check
make all

# Python regression tests
uv run --extra dev pytest

# Python package build
uv build
```

GitHub ActionsではPython 3.11 / 3.12 / 3.13のtest、Web JavaScript syntax check、GitHub Pages deployを行う構成です。

## Repository構成

```text
src/k5rx_tools/    Python library / CLI
web/               Web Memory Manager
docs/              EEPROM / CSV / protocol / design document
tests/             regression tests
testdata/          portable test vectors / examples
.github/workflows/ CI / GitHub Pages
```

初期設計上の判断は [`docs/decisions.md`](docs/decisions.md) に記録しています。

## Serial protocolの由来 / License

K5RX Toolsは **Apache License 2.0** で公開します。

通常起動時のSerial protocol実装は、Apache-2.0で公開されているF4HWN/DualTachyon Firmware sourceと実機仕様を一次資料とした独立実装です。GPLのk5prog/CHIRPはinteroperability確認には利用できますが、このrepositoryの実装sourceとしてコードをコピー・翻案しない方針です。

詳細: [`docs/serial-protocol-provenance.md`](docs/serial-protocol-provenance.md)

## Firmware書込み

Firmware flashingは初期版には含めません。

EEPROM編集とは失敗時のrecover手順・boot mode・安全性が異なるため、将来別module/workflowとして実装します。permissive licenseの参照実装、失敗時挙動、実機testを整理してから追加する方針です。

## License

Apache-2.0. [`LICENSE`](LICENSE) を参照してください。
