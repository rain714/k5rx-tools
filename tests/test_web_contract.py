from pathlib import Path


def test_static_web_app_contains_safety_contracts():
    html = (Path(__file__).parents[1] / "web" / "index.html").read_text(encoding="utf-8")
    assert "K5RX Memory Manager" in html
    assert "FACTORY:0x1E00" in html
    assert "function allowed(o)" in html
    assert "Baseline確認" in html
    assert "Write + Verify" in html
    assert "record,name,frequency,modulation,bandwidth,list1,list2,list3,bank" in html
    assert "function templateCsv" in html
    assert "CSV雛形" in html
    assert "beforeunload" in html
