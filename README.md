# K5RX Tools

[English README](README.en.md)

**K5RX Tools** は、Quansheng UV-K5 / UV-K6 V1向け受信専用Firmware **K5RX** のMemory・Bank・EEPROMを管理するための補助ツールです。

K5RX Firmware: https://github.com/rain714/k5rx-firmware

主な利用方法は2つあります。

- **Web Memory Manager** — インストール不要。400 Memory / Bank / Scan Listをブラウザから編集できます。通常はこちらを推奨します。
- **CLI (`k5rx`)** — RAW/CSV変換、差分確認、Radio Read/Writeなどをコマンドラインで行いたい場合に使用します。

> [!IMPORTANT]
> K5RX Toolsは **K5RX EEPROM Schema v2専用** です。Stock Firmwareや通常のF4HWN EEPROMをそのまま編集するツールではありません。

## Web Memory Managerを使う

GitHub Pages公開後は、次のURLから利用できます。

**https://rain714.github.io/k5rx-tools/**

Web版はすべてブラウザ内で動作し、EEPROMやCSVをサーバーへ送信しません。RadioとはWeb Serialで直接通信します。

必要なもの:

- K5RX Firmwareを導入したUV-K5 / UV-K6 V1
- 通常のFirmware書込みに使用するUSBシリアルケーブル
- Web Serial対応ブラウザ（Chrome / Edge等）
- HTTPSで公開されたGitHub Pages、またはlocalhost

Radioは**Firmware書込みモードではなく通常起動**してください。

### 基本操作

1. **接続**を押してRadioを選択
2. EEPROM全体を自動Read
3. 最初に **RAW Backup** を保存
4. Memory / Bank / Scan Listを編集
5. **Radioへ書込**を押してDiffを確認
6. Backup済みであることを確認して **Write + Verify**

Write時には、編集開始後にRadio側のEEPROMが変わっていないか全体を再Readして確認します。変更されていた場合は古い内容で上書きせず停止します。

### Web版でできること

- M001〜M400の400 Memory編集
- Name / Frequency / FM-AM-USB / Wide-Narrow
- Scan List 1〜3
- Bank 1〜8 / Bank名
- Search / Filter
- Shift + clickによる範囲選択
- Move / Duplicate / Clear
- Bulk edit
- Undo / Redo
- CSV Import / Export
- 400 Memory入りCSV雛形生成
- RAW EEPROM Backup
- Write前Diff確認
- changed-block-only Write + Read-back Verify

詳細は [`docs/web-memory-manager.md`](docs/web-memory-manager.md) を参照してください。

## 最初にBackupしてください

K5RXではStock Firmware / F4HWNとは異なるEEPROM layoutを使用します。

K5RX Toolsで編集する前だけでなく、**K5RX Firmwareを初めて導入する前にも8192-byteのEEPROM全体をRAW形式でBackupし、そのファイルを保管することを推奨します。**

K5RX Toolsは安全のため次の制約を設けています。

- Schema v2でないEEPROMにはWriteしない
- Factory / Calibration領域 `0x1E00..0x1FFF` はWriteしない
- Memory record / name / Bank name以外への意図しない変更を拒否
- Write直前にRadio全体を再Readしてbaselineを確認
- transactionごとに書込み後Readしてbyte単位でVerify

これらは誤操作リスクを下げるための保護であり、USB切断・電源断・Hardware故障などすべての障害から復旧を保証するものではありません。元のRAW Backupは別途保管してください。

## Firmwareを書き込むツールではありません

K5RX Tools v0.1.0は**EEPROM / Memory管理用**です。Firmware flashing機能は含みません。

K5RX Firmwareの書込みは、K5RX Firmware Releaseにある `packed.bin` をF4HWN本家のWeb Flasher等から指定して行ってください。

## CLIを使う

Web UIではなく、RAW/CSVをファイルとして管理したい場合やautomation用途ではCLIを利用できます。

### 開発中Repositoryから実行

```bash
git clone https://github.com/rain714/k5rx-tools.git
cd k5rx-tools
uv sync
uv run k5rx --help
```

CLIのhelp/error messageはterminal環境での文字化けを避けるため英語を基本とします。

### 推奨ワークフロー

まずRadioからEEPROM全体をReadします。

```bash
uv run k5rx radio ports
uv run k5rx radio read backup.raw --port /dev/cu.usbserial-10
```

`backup.raw` をCSVへExportします。

```bash
uv run k5rx csv export backup.raw channels.csv
```

CSVを編集後、検証します。

```bash
uv run k5rx csv validate channels.csv
```

CSVの変更を元RAWへ反映します。

```bash
uv run k5rx csv import channels.csv \
  --base backup.raw \
  --output updated.raw
```

CSVにはCTCSS/DCS、Step、Compander等のhidden fieldを含めないため、`--base` を使って元RAWの値を保持します。

差分を確認します。

```bash
uv run k5rx eeprom diff backup.raw updated.raw
```

問題なければRadioへWriteします。

```bash
uv run k5rx radio write updated.raw \
  --base backup.raw \
  --port /dev/cu.usbserial-10
```

通常のWriteでは確認のため `WRITE` の入力を要求します。`--yes` はautomation向けで、通常操作では推奨しません。

詳しいCLI操作とエラー時の復旧方法: [`docs/cli.md`](docs/cli.md)

## CSVを新規作成する

RadioからExportせず、新しいMemory一覧を作成する場合は400 Memory入りtemplateを生成できます。

```bash
uv run k5rx csv template channels.csv
```

生成順:

```text
header
B1 ... B8
M001 ... M400
```

Bank名をCSVで管理しない場合:

```bash
uv run k5rx csv template channels.csv --no-banks
```

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

例:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

Memoryは `M001`〜`M400`、Bank名は `B1`〜`B8` です。Import互換のため旧header `channel` も受け付けますが、新規Exportは `record` を使用します。

詳細: [`docs/csv-format.md`](docs/csv-format.md)

## RAW EEPROMを調べる

```bash
# Schema / Memory validation
uv run k5rx eeprom validate backup.raw

# EEPROM概要
uv run k5rx eeprom inspect backup.raw

# 使用中Memoryも表示
uv run k5rx eeprom inspect backup.raw --memories

# RAW同士の差分
uv run k5rx eeprom diff before.raw after.raw
```

## 対応範囲

初回リリース `v0.1.0` の対象:

- K5RX Firmware
- EEPROM Schema v2
- 400 Memory
- Scan List 1〜3
- 8 Banks
- UV-K5 / UV-K6 V1系（K5RX Firmware対応機種）

K5RX以外のFirmwareとのEEPROM互換性は前提としていません。

## Privacy

Web Memory Managerはstatic HTMLで、backend APIを持ちません。

- EEPROM Read/WriteはPCとRadio間のWeb Serial通信
- RAW BackupはブラウザからローカルへDownload
- CSV Importもブラウザ内で処理
- EEPROM / CSV内容をK5RX Toolsのserverへuploadしない

## GitHub Pages

`web/` はdependency-freeのstatic Web applicationです。RepositoryではGitHub ActionsからそのままGitHub Pagesへdeployします。

ローカル確認:

```bash
python3 -m http.server 8000 --directory web
```

`http://localhost:8000/` を開いてください。

Web UIは日本語をprimary languageとしています。将来UIを分割する段階でi18n対応を検討します。

## Documentation

- [Documentation index](docs/README.md)
- [CLI](docs/cli.md)
- [Web Memory Manager](docs/web-memory-manager.md)
- [CSV format](docs/csv-format.md)
- [EEPROM Schema v2](docs/eeprom-schema-v2.md)
- [Serial protocol](docs/serial-protocol.md)
- [Architecture](docs/architecture.md)

## 開発 / Test

```bash
make all
uv run --extra dev pytest
uv build
```

GitHub ActionsではPython 3.11 / 3.12 / 3.13のtest、package build、Web JavaScript syntax check、GitHub Pages deploymentを行います。

Repository構成:

```text
src/k5rx_tools/    Python library / CLI
web/               Web Memory Manager
docs/              EEPROM / CSV / protocol documentation
tests/             regression tests
testdata/          portable test vectors / examples
.github/workflows/ CI / GitHub Pages
```

## Serial protocolの由来

通常起動時のSerial protocol実装は、Apache-2.0で公開されているF4HWN / DualTachyon Firmware sourceと実機仕様を一次資料とした独立実装です。GPLのk5prog / CHIRPはinteroperability確認の参照には利用しますが、このRepositoryの実装sourceとしてコードをコピー・翻案しない方針です。

詳細: [`docs/serial-protocol-provenance.md`](docs/serial-protocol-provenance.md)

## License

K5RX Toolsは **Apache License 2.0** で公開します。詳細は [`LICENSE`](LICENSE) を参照してください。
