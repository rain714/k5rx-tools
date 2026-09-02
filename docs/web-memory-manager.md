# Web Memory Manager

`web/index.html` はK5RX Toolsの初期public browser applicationです。

## 配布方式

初期版はdependency-freeのstatic HTMLとして管理します。npm buildを必要とせず、GitHub Pagesから`web/`をそのまま公開できます。

主な対応環境:

- Web Serial対応のChrome / Edge
- HTTPS（GitHub Pages等）またはlocalhost secure context
- RadioはFirmware flash modeではなく通常起動

EEPROM / RAW / CSV / Serial dataをbackendへuploadしません。

## 基本ワークフロー

```text
接続
→ EEPROM全体を自動Read
→ Schema v2 validation
→ Memory / List / Bank編集
→ 必要に応じてCSV Import/Export
→ RAW backup保存
→ Diff確認
→ Write + Verify
```

Write直前にはRadio EEPROM全体を再Readし、編集開始時のbaselineと完全一致することを要求します。他ツールや別操作でRadio側が変更されていた場合、古いbrowser working copyから上書きしません。

## 現在の機能

- Web Serial connect/disconnect
- 接続直後の自動Read / 手動Read
- Schema v2 validation
- full RAW backup download
- M001〜M400の全physical slot表示
- Name / Frequency / FM-AM-USB / Wide-Narrow / List 1-3 / Bank
- B1〜B8 Bank name編集
- filter / search
- Shift range selection
- Move / Duplicate / Clear
- Bulk edit
- Undo / Redo（30 snapshot）
- canonical CSV Import/Export（B1〜B8 optional）
- Added / Modified / Cleared表示
- Write前のhuman-readable diff
- RAW backup確認
- changed-block-only write
- contiguous最大128-byte transaction
- transactionごとのread-back verify
- stale baseline protection
- unsaved changeがある場合のpage離脱警告

## Language / i18n

K5RX Toolsは日本向け利用をprimary targetとするため、初期Web UIは日本語をprimaryとします。

ただしv0.1ではsingle HTMLという単純さを優先し、i18n frameworkは導入しません。将来TypeScript/Vite等へ分割する際に、UI文字列をdictionary/resourceへ分離し、日本語/英語等を切り替えられる構成へ移行します。

Serial protocol、CSV、EEPROM safety contractは言語切替によって変化させません。

## Source管理方針

現状の機能規模では、1 HTMLの方がdeploy/reviewしやすく、runtime dependencyもありません。

詳細editorや複数画面などが増えた段階でTypeScript/Viteへ分割するのが適切です。そのrefactorでも`docs/`で定義したCSV / EEPROM / Serial / safety contractは維持します。
