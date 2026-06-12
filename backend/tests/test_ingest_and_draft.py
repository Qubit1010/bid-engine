"""Document parsing + draft citation contract."""
from pathlib import Path

import pytest

from draft.generator import CITATION_RE
from ingest.parser import parse_document

DEMO = Path(__file__).resolve().parents[2] / "demo-assets"


@pytest.mark.skipif(not (DEMO / "RFP_Solar_PV_Hospitals.pdf").exists(),
                    reason="demo asset missing")
def test_parse_solar_demo_pdf():
    doc = parse_document(DEMO / "RFP_Solar_PV_Hospitals.pdf")
    assert doc["num_pages"] >= 3
    full = " ".join(p["text"] for p in doc["pages"])
    assert "ISO 9001" in full and "Solar" in full
    assert all({"page", "text"} <= set(p.keys()) for p in doc["pages"])


def test_citation_regex_matches_cap_and_profile():
    text = ("We delivered similar systems [CAP-032] and hold ISO 9001 [CO-PROFILE]; "
            "see also [CAP-008].")
    assert sorted(set(CITATION_RE.findall(text))) == ["CAP-008", "CAP-032", "CO-PROFILE"]


def test_citation_regex_rejects_fabricated_ids():
    assert CITATION_RE.findall("[CAP-9999] [CAPX-001] [PROFILE]") == []


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        parse_document(Path("not_a_tender.txt"))
