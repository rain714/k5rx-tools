from pathlib import Path

from k5rx_jpn import csvio


def test_template_contains_all_memories_and_banks(tmp_path: Path):
    path = tmp_path / "template.csv"
    csvio.write_template(path)
    info = csvio.inspect(path)
    assert info.memory_rows == 400
    assert info.bank_rows == 8
    text = path.read_text(encoding="utf-8")
    assert "B1,BANK1" in text
    assert "M001,,,,,0,0,0,0" in text
    assert "M400,,,,,0,0,0,0" in text


def test_template_can_omit_bank_rows(tmp_path: Path):
    path = tmp_path / "template.csv"
    csvio.write_template(path, include_banks=False)
    info = csvio.inspect(path)
    assert info.memory_rows == 400
    assert info.bank_rows == 0
