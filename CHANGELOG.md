# Changelog

## 0.1.0 - Unreleased

K5RX-JPN Tools初期実装。

- Apache-2.0 project / Serial protocol provenance policy
- RX_ONLY EEPROM Schema v2 codec / validation
- canonical RAW/CSV変換、B1〜B8 Bank row対応
- 400 Memory + Bankを生成する`csv template`
- Python `k5rx` CLIによるEEPROM inspect/diff/CSV/Radio Read/Write/Verify
- stale baseline protection、explicit WRITE confirmation
- CLI help/errorから次の推奨commandを案内
- static Web Serial Memory Manager
- Web版CSV雛形生成、400 slot、Bank/List、bulk edit、Undo/Redo、RAW backup、Write + Verify
- 日本語primary README/document/Web UI + English README
- GitHub ActionsによるPython test/package build、Web JavaScript syntax check、GitHub Pages deployment
