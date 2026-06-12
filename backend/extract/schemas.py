"""Pydantic schemas — the single source of truth for the extracted RFP profile."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from core import config


class Requirement(BaseModel):
    text: str
    category: str = "General"
    mandatory: bool = False
    source_page: Optional[int] = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("requirement text too short")
        return v


class EvaluationCriterion(BaseModel):
    name: str
    weight_pct: Optional[float] = Field(None, ge=0, le=100)
    description: str = ""


class Deadline(BaseModel):
    label: str
    date: Optional[str] = None  # ISO yyyy-mm-dd where parseable
    raw: str = ""
    source_page: Optional[int] = None


class QAItem(BaseModel):
    question: str
    section: str = ""
    source_page: Optional[int] = None


class RFPProfile(BaseModel):
    title: str = "Untitled RFP"
    issuer: str = ""
    sector: str = "IT Services"
    summary: str = ""
    budget_raw: str = ""
    budget_pkr_m: Optional[float] = None
    submission_deadline: Optional[str] = None
    deadlines: list[Deadline] = []
    criteria: list[EvaluationCriterion] = []
    qa_items: list[QAItem] = []
    submission_instructions: str = ""

    @field_validator("sector")
    @classmethod
    def sector_known(cls, v: str) -> str:
        return v if v in config.SECTORS else "IT Services"


class MatchResult(BaseModel):
    status: Literal["PASS", "PARTIAL", "GAP"]
    confidence: float = Field(ge=0, le=1)
    rationale: str = ""
    used_cap_ids: list[str] = []
