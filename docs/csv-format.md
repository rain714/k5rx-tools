# K5RX-JPN CSV仕様

CSVは、Memory Managerで扱う項目をExcelやテキストエディタで編集するための**人間向け交換形式**です。完全なEEPROM backupではありません。

## Template生成

Memory rowはM001〜M400の全400件が必須です。新規作成時はtemplate commandを使用できます。

```bash
k5rx csv template channels.csv
```

デフォルトではB1〜B8 Bank rowも含みます。BankをCSVで管理しない場合:

```bash
k5rx csv template channels.csv --no-banks
```

## Header

Canonical header:

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
```

新規Exportは常に `record` を使用します。Importのみ旧形式互換として先頭列 `channel` も受け付けます。

## Memory row

Memory rowの`record`は `M001`〜`M400` です。

全400 physical slotを**それぞれ1回ずつ**含める必要があります。これによりspreadsheet編集時の意図しない詰め替え・renumberを防ぎます。

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
M002,TOWER,118.80000,AM,Wide,1,1,0,1
```

空Memoryは `name/frequency/modulation/bandwidth` を空欄、List/Bankを0とします。

## Bank row

Bank nameはheaderを変更せず同じCSVへ格納できます。

```csv
record,name,frequency,modulation,bandwidth,list1,list2,list3,bank
B1,AIR,,,,,,,
B2,LOCAL,,,,,,,
M001,HANEDA,118.10000,AM,Wide,1,0,0,1
```

- `record`: `B1`〜`B8`
- `name`: Bank name
- その他の列: 必ず空欄

Export/templateはデフォルトでBank rowを含みます。`--no-banks`で省略できます。

Import時もBank rowをデフォルトで反映します。`--no-banks`を指定すると、`--base` RAWに存在する現在のBank nameを保持します。

TemplateのBank初期値は `BANK1`〜`BANK8` です。実際のBank nameへ編集するか、Bank nameを変更したくない場合はtemplate生成/Importで `--no-banks` を使用してください。

## Field rule

- `name`: printable ASCII、最大10 byte
- `frequency`: MHz decimal。FirmwareのRX可能rangeでvalidation
- `modulation`: `FM` / `AM` / `USB`。Importでは0/1/2も受付
- `bandwidth`: `Wide` / `Narrow`。ImportではW/N、0/1も受付
- `list1..list3`: `1/0`, `true/false`, `on/off`, `yes/no`
- `bank`: 0〜8。0はUNBANKED

## Hidden fieldと`--base`

CSVは次のようなfieldを含みません。

- RX code / code type
- Step
- Compander
- reserved bits

したがってCLIの `csv import` では、元の完全なEEPROM imageを `--base` として指定する必要があります。

推奨手順:

```bash
k5rx radio read backup.raw --port <PORT>
k5rx csv export backup.raw channels.csv
# edit channels.csv
k5rx csv import channels.csv --base backup.raw --output updated.raw
```

既存Memoryを更新する場合、Importは同じphysical slotの8-byte recordをbaseとしてCSVにあるfieldだけを変更します。空slotへ新規Memoryを入れる場合のみhidden fieldを安全なdefaultで初期化します。

正確なEEPROM復元にはCSVではなく`.raw` backupを使用してください。
