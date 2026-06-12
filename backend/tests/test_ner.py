"""NER normalizers: dates, PKR amounts, percentages."""
from extract.ner import extract_percentages, normalize_date, normalize_pkr_millions


def test_date_dd_month_yyyy():
    assert normalize_date("15 July 2026") == "2026-07-15"


def test_date_month_dd_yyyy():
    assert normalize_date("July 15, 2026") == "2026-07-15"


def test_date_iso_passthrough():
    assert normalize_date("2026-07-15") == "2026-07-15"


def test_date_slashed():
    assert normalize_date("15/07/2026") == "2026-07-15"


def test_date_garbage_returns_none():
    assert normalize_date("next Tuesday-ish") is None


def test_pkr_millions():
    assert normalize_pkr_millions("PKR 280 Million") == 280.0


def test_pkr_billions():
    assert normalize_pkr_millions("PKR 1.85 Billion") == 1850.0


def test_pkr_crore():
    assert normalize_pkr_millions("Rs. 5 crore") == 50.0


def test_pkr_lakh():
    assert normalize_pkr_millions("Rs 20 lakh") == 2.0


def test_pkr_none_for_no_amount():
    assert normalize_pkr_millions("as per BOQ") is None


def test_percent_extraction():
    out = extract_percentages("bid security of 2% and retention of 10 %")
    assert 2.0 in out and 10.0 in out
