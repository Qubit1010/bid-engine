"""Render pitch/project-proposal.md into a branded PDF with reportlab.

Lightweight markdown renderer covering the constructs used in the proposal:
headings (#, ##, ###), pipe tables (cells wrap), fenced code blocks, bullet
lists, bold (**...**), inline `code`, and horizontal rules.

Run:  python pitch/build_proposal_pdf.py     (from projects/bid-engine/)
"""
from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (HRFlowable, ListFlowable, ListItem, Paragraph,
                                Preformatted, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

HERE = Path(__file__).parent
SRC = HERE / "project-proposal.md"
OUT = HERE / "project-proposal.pdf"

# brand palette
GREEN = colors.HexColor("#609966")
DARK = colors.HexColor("#243524")
DARKGREEN = colors.HexColor("#3a5a40")
SAGE_BG = colors.HexColor("#eef3e4")
ROW_BG = colors.HexColor("#f4f8ee")
BORDER = colors.HexColor("#c9d6ba")
MUTED = colors.HexColor("#56654f")

AVAIL = A4[0] - 4 * cm  # 2cm margins each side

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Title"], textColor=DARKGREEN, fontSize=22,
                    spaceAfter=4, leading=26, alignment=0)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], textColor=DARKGREEN, fontSize=14,
                    spaceBefore=16, spaceAfter=6, leading=18)
H3 = ParagraphStyle("H3", parent=ss["Heading3"], textColor=GREEN, fontSize=11.5,
                    spaceBefore=10, spaceAfter=4, leading=15)
BODY = ParagraphStyle("Body", parent=ss["BodyText"], textColor=DARK, fontSize=10,
                      leading=15, spaceAfter=6)
CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8.8, leading=11.5, spaceAfter=0)
CELL_HEAD = ParagraphStyle("CellHead", parent=CELL, textColor=colors.white,
                           fontName="Helvetica-Bold")
BULLET = ParagraphStyle("Bullet", parent=BODY, spaceAfter=3)
SUBTITLE = ParagraphStyle("Sub", parent=BODY, textColor=MUTED, fontSize=11,
                          spaceAfter=2)


def inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier" size="8.5">\1</font>', text)
    return text


def parse_blocks(md: str):
    lines = md.split("\n")
    blocks, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            i += 1
            continue
        if ln.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            blocks.append(("code", "\n".join(code)))
        elif ln.startswith("### "):
            blocks.append(("h3", ln[4:])); i += 1
        elif ln.startswith("## "):
            blocks.append(("h2", ln[3:])); i += 1
        elif ln.startswith("# "):
            blocks.append(("h1", ln[2:])); i += 1
        elif ln.strip() == "---":
            blocks.append(("hr", None)); i += 1
        elif ln.lstrip().startswith("|"):
            tbl = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                tbl.append(lines[i]); i += 1
            blocks.append(("table", tbl))
        elif ln.lstrip().startswith("- "):
            items = []
            while i < len(lines) and lines[i].lstrip().startswith("- "):
                items.append(lines[i].lstrip()[2:]); i += 1
            blocks.append(("ul", items))
        else:
            para = [ln]; i += 1
            while (i < len(lines) and lines[i].strip() != ""
                   and not lines[i].startswith(("#", "|", "```", "---"))
                   and not lines[i].lstrip().startswith("- ")):
                para.append(lines[i]); i += 1
            blocks.append(("p", " ".join(para)))
    return blocks


def render_table(tbl_lines):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in tbl_lines]
    if len(rows) >= 2 and all(set(c) <= set("-: ") and "-" in c for c in rows[1]):
        header, body = rows[0], rows[2:]
    else:
        header, body = rows[0], rows[1:]
    ncol = len(header)
    maxlens = [max((len(r[ci]) for r in rows if ci < len(r)), default=1) for ci in range(ncol)]
    total = sum(maxlens) or 1
    widths = [max(0.12, ml / total) * AVAIL for ml in maxlens]
    s = sum(widths)
    widths = [w / s * AVAIL for w in widths]

    data = [[Paragraph(inline(c), CELL_HEAD) for c in header]]
    for r in body:
        data.append([Paragraph(inline(c), CELL) for c in (r + [""] * (ncol - len(r)))])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_BG]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def code_box(text: str):
    pre = Preformatted(text, ParagraphStyle("Code", fontName="Courier", fontSize=7.6,
                                            leading=9.5, textColor=DARK))
    t = Table([[pre]], colWidths=[AVAIL])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SAGE_BG),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def build():
    blocks = parse_blocks(SRC.read_text(encoding="utf-8"))
    story = []
    for i, (kind, payload) in enumerate(blocks):
        if kind == "h1":
            story.append(Paragraph(inline(payload), H1))
            story.append(HRFlowable(width="100%", thickness=2, color=GREEN,
                                    spaceBefore=4, spaceAfter=10))
        elif kind == "h2":
            story.append(Paragraph(inline(payload), H2))
            story.append(HRFlowable(width="100%", thickness=0.6, color=BORDER, spaceAfter=6))
        elif kind == "h3":
            story.append(Paragraph(inline(payload), H3))
        elif kind == "p":
            # the two lines right under the H1 are the subtitle
            style = SUBTITLE if i in (1, 2) else BODY
            story.append(Paragraph(inline(payload), style))
        elif kind == "ul":
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(it), BULLET), leftIndent=10) for it in payload],
                bulletType="bullet", bulletColor=GREEN, bulletFontSize=6,
                leftIndent=12, spaceAfter=6,
            ))
        elif kind == "table":
            story.append(render_table(payload))
            story.append(Spacer(1, 8))
        elif kind == "code":
            story.append(code_box(payload))
            story.append(Spacer(1, 8))
        elif kind == "hr":
            story.append(Spacer(1, 2))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(2 * cm, 1.2 * cm, "BidSense Project Proposal · CUST Hackathon 2026")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, topMargin=2 * cm,
                            bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
                            title="BidSense Project Proposal")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF written -> {OUT}  ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build()
