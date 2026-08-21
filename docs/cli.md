# CLI利用ガイド

K5RX-JPN CLIのprimary commandは`k5rx`です。

開発repository内では:

```bash
uv run k5rx --help
```

PyPI公開後は:

```bash
uvx k5rx-jpn --help
```

CLIのhelp/error/output自体はterminal encoding互換性を優先して英語で表示します。このdocumentでは典型的な操作を日本語で説明します。

## Serial portを確認

```bash
k5rx radio ports
```

macOS例:

```text
/dev/cu.usbserial-10
```

RadioはFirmware flashing modeではなく通常起動してください。

## RAW backupを取得

```bash
k5rx radio read backup.raw --port /dev/cu.usbserial-10
```

このRAWは単なる一時fileではなく、その編集作業の**baseline**です。

CSV importとRadio writeで同じfileを`--base`として指定します。

## CSVをRadioから作る

```bash
k5rx csv export backup.raw channels.csv
```

Bank nameを含めない場合:

```bash
k5rx csv export backup.raw channels.csv --no-banks
```

## CSVを空のtemplateから作る

```bash
k5rx csv template channels.csv
```

生成内容:

```text
B1 ... B8
M001 ... M400
```

Bank rowを不要にする場合:

```bash
k5rx csv template channels.csv --no-banks
```

## CSV validation

```bash
k5rx csv validate channels.csv
```

CSVはM001〜M400を全件必要とします。行不足errorが出た場合は、既存CSVへ手作業で不足行を追加するより`csv template`から作り直すことを推奨します。

## CSVをRAWへ反映

```bash
k5rx csv import channels.csv \
  --base backup.raw \
  --output updated.raw
```

`--base`はhidden fieldを保持するために必要です。

`backup.raw`がない場合は、先に:

```bash
k5rx radio read backup.raw --port <PORT>
```

を実行してください。

Bank rowがCSVに存在していても現在のBank nameを保持したい場合:

```bash
k5rx csv import channels.csv \
  --base backup.raw \
  --output updated.raw \
  --no-banks
```

## 差分確認

```bash
k5rx eeprom diff backup.raw updated.raw
```

Radioへ書く前に必ず意図したMemory/Bankのみが変更されていることを確認することを推奨します。

## RadioへWrite

```bash
k5rx radio write updated.raw \
  --base backup.raw \
  --port /dev/cu.usbserial-10
```

通常は次の確認が出ます。

```text
Type WRITE to continue with EEPROM write:
```

`WRITE`以外を入力すると中止します。

`--yes`はCIや明示的なautomation向けです。通常の手操作では使用しないことを推奨します。

## `radio no longer matches --base image` が出た場合

これは安全機能です。

`backup.raw`を取得した後にRadio EEPROMが変化しています。別ツールで変更した、Radio側の操作でEEPROMが更新された、古いbaselineを使用した、などが考えられます。

そのまま強制上書きせず、次の順でやり直してください。

```bash
k5rx radio read backup-new.raw --port <PORT>
k5rx csv import channels.csv --base backup-new.raw --output updated-new.raw
k5rx eeprom diff backup-new.raw updated-new.raw
k5rx radio write updated-new.raw --base backup-new.raw --port <PORT>
```

## `CSV must contain all 400 physical Memory slots` が出た場合

```bash
k5rx csv template new-channels.csv
```

でcanonical templateを生成し、必要な内容を移してください。

## RAW検証

```bash
k5rx eeprom validate backup.raw
k5rx eeprom inspect backup.raw
k5rx eeprom inspect backup.raw --memories
```

Schema mismatchの場合は、そのRAWを現在のSchema v2用writerへ使用しないでください。
