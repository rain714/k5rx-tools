from pathlib import Path

from k5rx_tools import csvio, model, schema


def test_csv_round_trip_and_bank_rows(tmp_path: Path, blank_image: bytes):
    image = bytearray(blank_image)
    model.update_bank_name(image, 1, "AIR")
    model.update_memory_visible(
        image,
        0,
        name="HANEDA",
        frequency_raw=11_810_000,
        modulation=1,
        bandwidth=0,
        list_mask=1,
        bank=1,
    )
    csv_path = tmp_path / "channels.csv"
    csvio.export_csv(bytes(image), csv_path, include_banks=True)
    text = csv_path.read_text(encoding="utf-8")
    assert text.startswith("record,name,frequency,modulation,bandwidth,list1,list2,list3,bank\n") or text.startswith("record,name,frequency,modulation,bandwidth,list1,list2,list3,bank\r\n")
    assert "B1,AIR" in text
    assert "M001,HANEDA,118.10000,AM,Wide,1,0,0,1" in text
    info = csvio.inspect(csv_path)
    assert info.memory_rows == 400
    assert info.bank_rows == 8
    imported = csvio.import_csv(csv_path, blank_image)
    m = model.decode_memory(imported, 0)
    assert m.name == "HANEDA"
    assert m.frequency_raw == 11_810_000
    assert m.bank == 1
    assert model.decode_bank(imported, 1).name == "AIR"


def test_csv_import_preserves_hidden_record_fields(tmp_path: Path, blank_image: bytes):
    base = bytearray(blank_image)
    ro = schema.record_offset(0)
    base[ro:ro+8] = bytes([0x20, 0x4E, 0xDD, 0x58, 0x55, (7 << 3), 0x80, 0xA5])
    model.update_memory_visible(base, 0, name="OLD", frequency_raw=14_500_000, modulation=0, bandwidth=0, list_mask=0, bank=0)
    csv_path = tmp_path / "channels.csv"
    csvio.export_csv(bytes(base), csv_path)
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("M001,"):
            lines[i] = "M001,NEW,145.10000,FM,Narrow,1,1,0,2"
            break
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    imported = csvio.import_csv(csv_path, bytes(base))
    m = model.decode_memory(imported, 0)
    assert m.name == "NEW"
    assert m.rx_code_type == 3
    assert m.rx_code == 0x55
    assert m.compander == 1
    assert m.step == 7
    assert m.reserved == 0xA5
    assert m.bank == 2
    assert m.list_mask == 3
