# Changelog

## 0.1.0 - Unreleased

K5RX Tools初期実装。

- Apache-2.0 project / Serial protocol provenance policy
- RX_ONLY EEPROM Schema v2 codec / validation
- canonical RAW/CSV変換、B1〜B8 Bank row対応
- 400 Memory + Bankを生成する`csv template`
- Python `k5rx` CLIによるEEPROM inspect/diff/CSV/Radio Read/Write/Verify
- stale baseline protection、explicit WRITE confirmation
- CLI help/errorから次の推奨commandを案内
- static Web Serial Memory Manager
- Web版CSV雛形生成、400 slot、Bank/List、bulk edit、Undo/Redo、RAW backup、Write + Verify
- Web版のstale baseline protection、Factory/Calibration write guard、human-readable Diff
- release向けWeb UI/UX整理、進捗表示、折り畳みprotocol log、CSV説明dialog
- 初見利用者向けの日本語primary README + English README
- GitHub ActionsによるPython test/package build、Web JavaScript syntax check、GitHub Pages deployment
