"""Regex NER validators/normalizers for dates, PKR amounts and percentages.

These run AFTER LLM extraction to validate and normalize entity values, and
also as an independent scan over the raw text so missed deadlines/amounts are
still surfaced (belt and suspenders).
"""
import re
from datetime import datetime

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
MONTHS.update({m[:3].lower(): i for m, i in
               [(k.capitalize(), v) for k, v in MONTHS.items()]})

DATE_PATTERNS = [
    # 2026-06-13 / 2026/06/13
    (re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"), "ymd"),
    # 13-06-2026 / 13/06/2026
    (re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{4})\b"), "dmy"),
    # 13 June 2026 / 13th June, 2026
    (re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9}),?\s+(\d{4})\b"), "dMy"),
    # June 13, 2026
    (re.compile(r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b"), "Mdy"),
]


def normalize_date(raw: str) -> str | None:
    """Best-effort: return ISO yyyy-mm-dd from a messy date string."""
    if not raw:
        return None
    raw = raw.strip()
    for pattern, kind in DATE_PATTERNS:
        m = pattern.search(raw)
        if not m:
            continue
        try:
            if kind == "ymd":
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
            elif kind == "dmy":
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            elif kind == "dMy":
                d, y = int(m.group(1)), int(m.group(3))
                mo = MONTHS.get(m.group(2).lower()[:3])
            else:  # Mdy
                d, y = int(m.group(2)), int(m.group(3))
                mo = MONTHS.get(m.group(1).lower()[:3])
            if not mo:
                continue
            return datetime(y, mo, d).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


AMOUNT_RE = re.compile(
    r"(?:PKR|Rs\.?|Rupees)\s*([\d,]+(?:\.\d+)?)\s*(billion|million|crore|lakh|lac|B|M)?",
    re.IGNORECASE,
)


def normalize_pkr_millions(raw: str) -> float | None:
    """'PKR 22M', 'Rs. 45 million', 'PKR 1.2 billion', 'Rs 5 crore' -> millions."""
    if not raw:
        return None
    m = AMOUNT_RE.search(raw)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "").lower()
    if unit in ("billion", "b"):
        return num * 1000
    if unit == "crore":
        return num * 10
    if unit in ("lakh", "lac"):
        return num * 0.1
    if unit in ("million", "m"):
        return num
    # bare number: assume plain rupees
    return num / 1_000_000


DEADLINE_HINT_RE = re.compile(
    r"(deadline|submission|due date|closing date|last date|submit(?:ted)? by|"
    r"pre-?bid|bid opening|validity)", re.IGNORECASE)


def scan_deadlines(pages: list[dict]) -> list[dict]:
    """Scan raw text for deadline-looking lines the LLM might have missed."""
    found = []
    seen: set[str] = set()
    for p in pages:
        for line in p["text"].splitlines():
            if not DEADLINE_HINT_RE.search(line):
                continue
            iso = normalize_date(line)
            if iso and iso not in seen:
                seen.add(iso)
                found.append({
                    "label": line.strip()[:80],
                    "date": iso,
                    "raw": line.strip()[:160],
                    "source_page": p["page"],
                })
    return found


PCT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")


def extract_percentages(text: str) -> list[float]:
    return [float(m) for m in PCT_RE.findall(text) if float(m) <= 100]
