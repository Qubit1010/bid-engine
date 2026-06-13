"""Generate one simple, clean RFP PDF to use as pipeline input.

A short, well-formed software-development tender that fits the seeded company
profile (TechnoCore Engineering: IT-first, holds ISO 9001/27001/CMMI L3) so a
live run produces a sensible, mostly-compliant result.
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

HERE = Path(__file__).parent
styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1r", parent=styles["Heading1"], spaceBefore=14)
BODY = ParagraphStyle("Bodyr", parent=styles["BodyText"], leading=15)
TITLE = ParagraphStyle("Titler", parent=styles["Title"], alignment=TA_CENTER)
CELL = ParagraphStyle("Cellr", parent=styles["BodyText"], fontSize=9, leading=12)
CELL_HEAD = ParagraphStyle("CellHeadr", parent=CELL, textColor=colors.white,
                           fontName="Helvetica-Bold")

REQ_WIDTHS = [1.2 * cm, 15.3 * cm]
TWO_COL = [11.5 * cm, 5.0 * cm]


def _cellify(data):
    out = []
    for ri, row in enumerate(data):
        out.append([Paragraph(c, CELL_HEAD if ri == 0 else CELL) if isinstance(c, str) else c
                    for c in row])
    return out


def table(data, widths=None):
    t = Table(_cellify(data), colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#609966")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f8ee")]),
    ]))
    return t


def p(text, style=BODY):
    return Paragraph(text, style)


def build() -> None:
    doc = SimpleDocTemplate(str(HERE / "RFP_Corporate_Website_Portal.pdf"), pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    e = [Spacer(1, 50)]
    e.append(p("STATE LIFE INSURANCE CORPORATION OF PAKISTAN", TITLE))
    e.append(Spacer(1, 10))
    e.append(p("REQUEST FOR PROPOSAL (RFP)", TITLE))
    e.append(p("Design, Development and One-Year Support of a Corporate Website and "
               "Customer Self-Service Portal", TITLE))
    e.append(Spacer(1, 20))
    e.append(p("RFP Reference No: SLIC/IT/2026/RFP-018<br/>"
               "Issue Date: 5 June 2026<br/>"
               "Estimated Project Cost: PKR 25 Million<br/>"
               "Procurement Method: Single Stage Two Envelope (PPRA Rules 2014)", TITLE))
    e.append(PageBreak())

    e.append(p("1. Introduction", H1))
    e.append(p("State Life Insurance Corporation of Pakistan invites proposals from eligible "
               "software firms for the design, development, deployment and one (1) year of "
               "support of a modern corporate website and an integrated customer self-service "
               "portal. The portal shall allow policyholders to view policies, download "
               "documents, raise service requests and make online premium payments."))

    e.append(p("2. Scope of Work", H1))
    e.append(p("The scope includes: (a) UX/UI design and a responsive, accessible front end; "
               "(b) a content-managed corporate website; (c) a secure customer portal with "
               "authentication and role-based access; (d) integration with the existing core "
               "policy system via REST APIs; (e) an online payment gateway integration; "
               "(f) deployment to the Corporation's cloud environment; and (g) one year of "
               "warranty support with defined response times."))

    e.append(p("3. Mandatory Eligibility Requirements", H1))
    e.append(p("Proposals failing any mandatory requirement shall be rejected."))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must hold a valid ISO 9001 quality management certification."],
        ["M2", "The bidder must hold a valid ISO 27001 information security certification."],
        ["M3", "The bidder must have completed at least three (3) web or software development "
               "projects, each of value not less than PKR 5 Million, in the last five years."],
        ["M4", "The bidder must be registered with the Federal Board of Revenue and hold "
               "active taxpayer (ATL) status."],
        ["M5", "The bidder must furnish bid security of two percent (2%) of the quoted price "
               "as a bank guarantee or CDR from a scheduled bank."],
    ], widths=REQ_WIDTHS))

    e.append(p("4. Technical Requirements", H1))
    e.append(table([
        ["#", "Technical Requirement"],
        ["T1", "The proposed solution should use a modern, maintainable web stack and provide "
               "a content management system for non-technical staff."],
        ["T2", "The portal should support secure authentication, role-based access control "
               "and an audit trail of user actions."],
        ["T3", "The bidder should integrate the existing core policy system through documented "
               "REST APIs and a tested payment gateway."],
        ["T4", "The solution should be responsive across desktop and mobile and meet WCAG 2.1 "
               "AA accessibility guidelines."],
        ["T5", "The bidder should provide a one-year support plan with a helpdesk and a "
               "defined response time for critical issues."],
        ["T6", "The bidder should provide user training and complete technical documentation "
               "at handover."],
    ], widths=REQ_WIDTHS))

    e.append(p("5. Evaluation Criteria", H1))
    e.append(p("Technical proposals will be scored out of 100; bidders scoring below 70 will "
               "not proceed to financial evaluation."))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant web / software development experience", "30%"],
        ["Technical solution and approach", "30%"],
        ["Team qualifications", "20%"],
        ["Financial proposal", "20%"],
    ], widths=TWO_COL))

    e.append(p("6. Key Dates and Submission", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Last date for written queries", "18 June 2026"],
        ["Proposal submission deadline", "30 June 2026, 03:00 PM"],
        ["Technical bid opening", "30 June 2026, 03:30 PM"],
        ["Bid validity period", "90 days"],
    ], widths=TWO_COL))
    e.append(p("Proposals shall be submitted in two sealed envelopes marked \"Technical\" and "
               "\"Financial\", one original and one copy each, addressed to the Chief Manager "
               "(IT), State Life Insurance Corporation, Principal Office, Karachi."))

    e.append(p("7. Required Proposal Sections", H1))
    e.append(p("Bidders must respond to: (Q1) Company profile and relevant experience; "
               "(Q2) Understanding of requirements and proposed solution; (Q3) Project plan "
               "and timeline; (Q4) Team and CVs; (Q5) Support and maintenance plan."))
    doc.build(e)


if __name__ == "__main__":
    build()
    f = HERE / "RFP_Corporate_Website_Portal.pdf"
    print(f"RFP written: {f.name}  ({f.stat().st_size // 1024} KB)")
