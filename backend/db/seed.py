"""Seed the SQLite DB from the hackathon CSVs and precompute capability embeddings."""
import csv
import re
from pathlib import Path

from core import config
from db import database


def parse_pkr_millions(value: str) -> float | None:
    """'PKR 22M' / 'PKR 1.2B' / 'Rs. 45 million' -> millions of PKR."""
    if not value:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)\s*(B|M|billion|million)?", value, re.IGNORECASE)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    unit = (m.group(2) or "M").upper()
    if unit.startswith("B"):
        return num * 1000
    return num


def seed_capabilities(csv_path: Path | None = None) -> int:
    csv_path = csv_path or (config.DATA_DIR / "capability_library.csv")
    with csv_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with database.connect() as conn:
        conn.execute("DELETE FROM capabilities")
        for r in rows:
            conn.execute(
                "INSERT INTO capabilities (cap_id, domain, summary, certification,"
                " year_completed, contract_value, contract_value_m, duration_months, client_type)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    r["Cap ID"], r["Domain"], r["Project Summary"], r["Certification"],
                    int(r["Year Completed"]) if r["Year Completed"] else None,
                    r["Contract Value"], parse_pkr_millions(r["Contract Value"]),
                    int(r["Duration (months)"]) if r["Duration (months)"] else None,
                    r["Client Type"],
                ),
            )
    return len(rows)


def main() -> None:
    database.init_db()
    n = seed_capabilities()
    print(f"Seeded {n} capability records")

    from rag.embeddings import build_capability_index
    space = build_capability_index()
    print(f"Capability embedding index built (space: {space})")


if __name__ == "__main__":
    main()
