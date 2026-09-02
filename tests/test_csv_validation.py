from pathlib import Path

import pytest

from k5rx_tools import csvio, schema


HEADER = "record,name,frequency,modulation,bandwidth,list1,list2,list3,bank"


def _write_400(path: Path, first: str) -> None:
    rows = [HEADER, first]
    rows.extend(f"M{i:03d},,,, ,0,0,0,0" for i in range(2, 401))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_csv_validate_checks_visible_frequency(tmp_path: Path):
    path = tmp_path / "bad.csv"
    _write_400(path, "M001,BAD,700.00000,FM,Wide,0,0,0,0")
    with pytest.raises(schema.ValidationError, match="unsupported RX frequency"):
        csvio.inspect(path)


def test_csv_validate_rejects_metadata_without_frequency(tmp_path: Path):
    path = tmp_path / "bad.csv"
    _write_400(path, "M001,NAME,,, ,0,0,0,0")
    with pytest.raises(schema.ValidationError, match="frequency is required"):
        csvio.inspect(path)
