"""Pydantic schemas: the single source of truth must reject bad LLM output."""
import pytest
from pydantic import ValidationError

from extract.schemas import MatchResult, Requirement, RFPProfile


def test_requirement_rejects_too_short_text():
    with pytest.raises(ValidationError):
        Requirement(text="short")


def test_requirement_defaults():
    r = Requirement(text="The bidder must hold ISO 9001 certification.")
    assert r.mandatory is False and r.category == "General"


def test_profile_unknown_sector_falls_back():
    p = RFPProfile(sector="Underwater Basket Weaving")
    assert p.sector == "IT Services"


def test_profile_known_sector_kept():
    assert RFPProfile(sector="Energy").sector == "Energy"


def test_match_result_rejects_bad_status():
    with pytest.raises(ValidationError):
        MatchResult(status="MAYBE", confidence=0.5)


def test_match_result_rejects_out_of_range_confidence():
    with pytest.raises(ValidationError):
        MatchResult(status="PASS", confidence=1.5)
