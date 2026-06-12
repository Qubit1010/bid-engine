"""One-time converter: hackathon sample Excel -> bid_history.csv + capability_library.csv.

Uses only the stdlib (zipfile + XML) so it runs anywhere without openpyxl.
"""
import csv
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
T = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def read_sheets(path: str) -> dict[str, list[list[str]]]:
    z = zipfile.ZipFile(path)
    sst = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("m:si", NS):
            sst.append("".join(t.text or "" for t in si.iter(T)))

    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {rel.get("Id"): rel.get("Target") for rel in rels}

    sheets: dict[str, list[list[str]]] = {}
    for sheet in wb.find("m:sheets", NS):
        name = sheet.get("name")
        target = relmap[sheet.get(RID)]
        if not target.startswith("xl/"):
            target = "xl/" + target
        ws = ET.fromstring(z.read(target))
        rows = []
        for row in ws.find("m:sheetData", NS).findall("m:row", NS):
            vals = []
            for c in row.findall("m:c", NS):
                v = c.find("m:v", NS)
                val = v.text if v is not None else ""
                if c.get("t") == "s" and val != "":
                    val = sst[int(val)]
                vals.append(str(val).strip())
            rows.append(vals)
        sheets[name] = rows
    return sheets


def write_csv(rows: list[list[str]], header_marker: str, out: Path) -> int:
    """Rows before the header row (title rows) are dropped."""
    start = next(i for i, r in enumerate(rows) if r and r[0] == header_marker)
    header = rows[start]
    data = [r for r in rows[start + 1 :] if any(cell for cell in r)]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in data:
            w.writerow(r + [""] * (len(header) - len(r)))
    return len(data)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else (
        "../../../../references/CUST-Hackathon/Problem#1_Sample_Datasets (TEKROWE).xlsx"
    )
    here = Path(__file__).parent
    sheets = read_sheets(str((here / src).resolve()) if not Path(src).is_absolute() else src)
    for name, rows in sheets.items():
        if "Bid History" in name:
            n = write_csv(rows, "Bid ID", here / "bid_history.csv")
            print(f"bid_history.csv: {n} rows")
        elif "Capability" in name:
            n = write_csv(rows, "Cap ID", here / "capability_library.csv")
            print(f"capability_library.csv: {n} rows")
