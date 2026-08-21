# Test data

portableなregression fixtureを置くdirectoryです。

初期Python testでは、physical radioから取得したRAW dumpをrepositoryへcommitせず、deterministicなSchema v2 synthetic EEPROM imageをtest内で生成します。

目的:

- device固有EEPROM/Calibration dataの意図しない公開を避ける
- expected layoutをtest code上で明示する
- testを再現可能にする

将来のfixture候補:

- known Memory/Bankを持つsynthetic `.raw`
- canonical CSV export
- malformed header/CSV sample
- user/device secretを含まないnormal-mode serial frame

physical radioから取得したRAW backupを公開fixtureとしてcommitする場合は、device固有情報・user固有情報を公開して問題ないことを事前に確認してください。
