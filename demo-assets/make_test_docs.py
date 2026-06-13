"""Generate three FRESH, uncached test documents — one per document type
(RFQ, RFP, Tender) — for live end-to-end testing against the real pipeline.

These are NOT part of the locked offline-replay demo trio (solar/HMIS/road);
they are deliberately uncached so a live run exercises extraction, matching,
the win model and drafting on documents the engine has never seen. They are
engineered against the seeded company profile (TechnoCore Engineering: IT-first,
holds ISO 9001/27001/CMMI L3, PKR 900M turnover, NO PEC reg / NO ISO 14001) to
land a clean GO / CONDITIONAL_GO / NO_GO spread:

  RFQ_Campus_Network_Upgrade.pdf       Network Design   -> expected GO
  RFP_Managed_Cybersecurity_SOC.pdf    Cybersecurity    -> expected CONDITIONAL_GO
                                       (one closable gap: turnover < PKR 1,200M)
  Tender_Safe_City_Surveillance.pdf    Civil+IT works   -> expected NO_GO
                                       (PEC reg, ISO 14001, turnover, plant — all absent)

Fixes the table-overflow bug in the original generator: ReportLab does NOT wrap
plain-string table cells, so long requirement text ran off the page. Every cell
is wrapped in a Paragraph flowable so it wraps inside its column.
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
H1 = ParagraphStyle("H1x", parent=styles["Heading1"], spaceBefore=14)
BODY = ParagraphStyle("Bodyx", parent=styles["BodyText"], leading=15)
TITLE = ParagraphStyle("Titlex", parent=styles["Title"], alignment=TA_CENTER)
# cell styles — wrapping cells is the fix for the overflow bug
CELL = ParagraphStyle("Cellx", parent=styles["BodyText"], fontSize=9, leading=12,
                      spaceBefore=0, spaceAfter=0)
CELL_HEAD = ParagraphStyle("CellHeadx", parent=CELL, textColor=colors.white,
                           fontName="Helvetica-Bold")

# usable width with 2cm side margins on A4 (21cm) = 17cm
REQ_WIDTHS = [1.2 * cm, 15.3 * cm]
TWO_COL = [11.5 * cm, 5.0 * cm]


def _cellify(data):
    """Wrap every string cell in a Paragraph so text wraps inside the column."""
    out = []
    for ri, row in enumerate(data):
        out.append([
            Paragraph(c, CELL_HEAD if ri == 0 else CELL) if isinstance(c, str) else c
            for c in row
        ])
    return out


def table(data, widths=None):
    t = Table(_cellify(data), colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff6ff")]),
    ]))
    return t


def p(text, style=BODY):
    return Paragraph(text, style)


def _doc(filename):
    return SimpleDocTemplate(str(HERE / filename), pagesize=A4,
                             topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)


# --------------------------------------------------------------------------- #
# 1. RFQ  — Network Design — expected GO
# --------------------------------------------------------------------------- #
def build_rfq() -> None:
    doc = _doc("RFQ_Campus_Network_Upgrade.pdf")
    e = [Spacer(1, 50)]
    e.append(p("PUNJAB INFORMATION TECHNOLOGY BOARD", TITLE))
    e.append(Spacer(1, 10))
    e.append(p("REQUEST FOR QUOTATION (RFQ)", TITLE))
    e.append(p("Supply, Installation and Configuration of Enterprise Network and "
               "Data-Centre Infrastructure across Six Regional Offices", TITLE))
    e.append(Spacer(1, 20))
    e.append(p("RFQ Reference No: PITB/PROC/2026/RFQ-244<br/>"
               "Issue Date: 4 June 2026<br/>"
               "Estimated Value: PKR 85 Million<br/>"
               "Procurement Method: Request for Quotation (PPRA Rule 40)", TITLE))
    e.append(PageBreak())

    e.append(p("1. Purpose", H1))
    e.append(p("The Punjab Information Technology Board (PITB) invites quotations from "
               "eligible firms for the supply, installation, configuration and "
               "commissioning of enterprise-grade network and data-centre infrastructure "
               "across six regional offices, including core and access switching, "
               "next-generation firewalls, structured cabling and a centralised network "
               "management system, with one (1) year of on-site warranty support."))

    e.append(p("2. Scope of Supply", H1))
    e.append(p("The scope includes: (a) supply of OEM-certified core and access switches, "
               "routers and next-generation firewalls; (b) rack-mounted server and storage "
               "nodes for two data-centre sites; (c) structured cabling and fibre backbone "
               "between floors; (d) configuration of VLANs, routing, high availability and "
               "centralised monitoring; (e) knowledge transfer to the in-house IT team; and "
               "(f) one year of warranty and on-site support with a 24x7 helpdesk."))

    e.append(p("3. Mandatory Eligibility Requirements", H1))
    e.append(p("Quotations failing any mandatory requirement shall be rejected."))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must hold a valid ISO 27001 information security management "
               "certification."],
        ["M2", "The bidder must hold a valid ISO 9001 quality management certification."],
        ["M3", "The bidder must have completed at least two (2) enterprise network or "
               "data-centre projects, each of value not less than PKR 30 Million, during "
               "the last five (5) years."],
        ["M4", "The bidder must be registered with the Federal Board of Revenue and hold "
               "active taxpayer (ATL) status."],
        ["M5", "The bidder must furnish a bid security of two percent (2%) of the quoted "
               "price in the form of a bank guarantee or CDR from a scheduled bank."],
    ], widths=REQ_WIDTHS))

    e.append(p("4. Technical Requirements", H1))
    e.append(table([
        ["#", "Technical Requirement"],
        ["T1", "All active equipment shall be from a single OEM with the bidder holding a "
               "valid partner or reseller authorisation; the bidder should provide OEM "
               "certifications for the assigned engineers."],
        ["T2", "The bidder should propose a redundant core design with no single point of "
               "failure and demonstrate a documented high-availability methodology."],
        ["T3", "The bidder should provide a centralised network monitoring and management "
               "platform with alerting and reporting dashboards."],
        ["T4", "The bidder should commit to a 24x7 helpdesk with a four (4) hour on-site "
               "response time for critical incidents during the warranty period."],
        ["T5", "The bidder should provide a structured knowledge-transfer and training "
               "programme for the PITB network operations team."],
    ], widths=REQ_WIDTHS))

    e.append(p("5. Evaluation Criteria", H1))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant network / data-centre project experience", "30%"],
        ["Technical compliance of proposed equipment", "30%"],
        ["Support, warranty and SLA commitments", "20%"],
        ["Financial quotation", "20%"],
    ], widths=TWO_COL))

    e.append(p("6. Key Dates and Submission", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Last date for written queries", "16 June 2026"],
        ["Quotation submission deadline", "26 June 2026, 03:00 PM"],
        ["Quotation opening", "26 June 2026, 03:30 PM"],
        ["Quotation validity period", "90 days"],
    ], widths=TWO_COL))
    e.append(p("Quotations shall be submitted in a single sealed envelope, one original "
               "and one copy, addressed to the Director (Procurement), Punjab Information "
               "Technology Board, Arfa Software Technology Park, Lahore."))
    doc.build(e)


# --------------------------------------------------------------------------- #
# 2. RFP  — Cybersecurity SOC — expected CONDITIONAL_GO (turnover gap)
# --------------------------------------------------------------------------- #
def build_rfp() -> None:
    doc = _doc("RFP_Managed_Cybersecurity_SOC.pdf")
    e = [Spacer(1, 50)]
    e.append(p("GOVERNMENT OF PAKISTAN<br/>MINISTRY OF INFORMATION TECHNOLOGY "
               "&amp; TELECOMMUNICATION", TITLE))
    e.append(Spacer(1, 10))
    e.append(p("REQUEST FOR PROPOSALS (RFP)", TITLE))
    e.append(p("Establishment and Operation of a 24x7 Security Operations Centre (SOC) "
               "and Managed Detection &amp; Response Services for Three Years", TITLE))
    e.append(Spacer(1, 20))
    e.append(p("RFP Reference No: MOITT/PROC/2026/RFP-061<br/>"
               "Issue Date: 30 May 2026<br/>"
               "Estimated Project Cost: PKR 150 Million<br/>"
               "Procurement Method: Single Stage – Two Envelope (PPRA Rules 2014)", TITLE))
    e.append(PageBreak())

    e.append(p("1. Background and Objectives", H1))
    e.append(p("The Ministry of Information Technology & Telecommunication intends to "
               "establish and operate a centralised 24x7 Security Operations Centre to "
               "provide continuous monitoring, threat detection and incident response "
               "across its data centres and connected federal entities. The successful "
               "bidder shall deploy a SIEM platform, staff a tiered analyst team and "
               "deliver managed detection and response services for a period of three (3) "
               "years, extendable on performance."))

    e.append(p("2. Scope of Work", H1))
    e.append(p("The scope includes: (a) design and stand-up of the SOC with a SIEM and "
               "SOAR platform; (b) 24x7 tiered monitoring (L1/L2/L3) with defined SLAs; "
               "(c) threat intelligence integration and proactive threat hunting; (d) "
               "incident response runbooks and forensic readiness; (e) periodic "
               "vulnerability assessment and reporting; and (f) knowledge transfer and "
               "capacity building of ministry security staff."))

    e.append(p("3. Mandatory Eligibility Requirements", H1))
    e.append(p("Bidders failing any mandatory requirement shall be disqualified."))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must hold a valid ISO 27001 information security management "
               "certification."],
        ["M2", "The bidder must have delivered at least three (3) cybersecurity or SOC "
               "engagements for government or financial-sector clients during the last "
               "five (5) years."],
        ["M3", "The bidder must demonstrate an average annual turnover of at least PKR "
               "1,200 Million over the last three (3) audited financial years, supported "
               "by audited financial statements."],
        ["M4", "The proposed SOC team must include certified security professionals "
               "(CISSP, GIAC or equivalent) covering all three monitoring tiers."],
        ["M5", "The bidder must furnish a bid security of two percent (2%) of the bid "
               "price in the form of a bank guarantee from a scheduled bank."],
    ], widths=REQ_WIDTHS))

    e.append(p("4. Technical Requirements", H1))
    e.append(table([
        ["#", "Technical Requirement"],
        ["T1", "The bidder should propose a SIEM and SOAR architecture with stated event "
               "ingestion capacity, retention and high-availability design."],
        ["T2", "The bidder should provide a tiered staffing model with 24x7 coverage and "
               "defined detection and response SLAs (time to detect, time to respond)."],
        ["T3", "The bidder should describe its threat-intelligence sources and proactive "
               "threat-hunting methodology."],
        ["T4", "The bidder should provide documented incident-response runbooks and a "
               "forensic-readiness approach aligned to a recognised framework."],
        ["T5", "The bidder should propose a knowledge-transfer and capacity-building plan "
               "for ministry staff over the contract term."],
        ["T6", "Prior experience operating a SOC for critical national or financial "
               "infrastructure will be evaluated favourably."],
    ], widths=REQ_WIDTHS))

    e.append(p("5. Evaluation Criteria", H1))
    e.append(p("Technical proposals will be scored out of 100. Bidders scoring less than "
               "70 marks shall not proceed to financial evaluation."))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant SOC / cybersecurity experience and references", "30%"],
        ["Technical solution and architecture", "25%"],
        ["Team qualifications and certifications", "20%"],
        ["Financial capability and stability", "10%"],
        ["Financial proposal", "15%"],
    ], widths=TWO_COL))

    e.append(p("6. Key Dates and Submission", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Pre-bid meeting (MoITT Committee Room, Islamabad)", "17 June 2026, 11:00 AM"],
        ["Deadline for written queries", "23 June 2026"],
        ["Proposal submission deadline", "8 July 2026, 02:00 PM"],
        ["Technical bid opening", "8 July 2026, 02:30 PM"],
        ["Bid validity period", "120 days"],
    ], widths=TWO_COL))
    e.append(p("Proposals shall be submitted in two separate sealed envelopes marked "
               "\"Technical Proposal\" and \"Financial Proposal\", one original and two "
               "copies each, addressed to the Section Officer (Procurement), Ministry of "
               "IT & Telecommunication, Islamabad."))

    e.append(p("7. Required Proposal Sections", H1))
    e.append(p("Bidders must respond to each of the following: (Q1) Company profile and "
               "relevant SOC experience; (Q2) Understanding of the assignment and proposed "
               "technical solution; (Q3) Staffing model and SLAs; (Q4) Threat intelligence "
               "and incident response methodology; (Q5) Implementation plan and timeline; "
               "(Q6) Certifications and statutory registrations."))
    doc.build(e)


# --------------------------------------------------------------------------- #
# 3. Tender — Safe-City civil + IT works — expected NO_GO
# --------------------------------------------------------------------------- #
def build_tender() -> None:
    doc = _doc("Tender_Safe_City_Surveillance.pdf")
    e = [Spacer(1, 50)]
    e.append(p("CAPITAL DEVELOPMENT AUTHORITY<br/>ISLAMABAD", TITLE))
    e.append(Spacer(1, 10))
    e.append(p("INVITATION FOR BIDS (TENDER)", TITLE))
    e.append(p("Design, Supply, Installation and Civil Works for a City-Wide Safe-City "
               "CCTV Surveillance Network and Command &amp; Control Centre", TITLE))
    e.append(Spacer(1, 20))
    e.append(p("Tender No: CDA/SC/2026/IFB-309<br/>"
               "Issue Date: 27 May 2026<br/>"
               "Estimated Cost: PKR 2,200 Million<br/>"
               "Procurement Method: Single Stage – Two Envelope (PPRA Rules 2014)", TITLE))
    e.append(PageBreak())

    e.append(p("1. Project Description", H1))
    e.append(p("The Capital Development Authority invites sealed bids for the design, "
               "supply, installation and associated civil works of a city-wide safe-city "
               "surveillance network comprising approximately 1,200 cameras, pole "
               "foundations, underground fibre ducting, a redundant fibre backbone, and a "
               "central command and control centre with a video wall and analytics. The "
               "works include both information-technology integration and substantial "
               "civil and electrical works, to be completed within eighteen (18) months."))

    e.append(p("2. Mandatory Eligibility Requirements", H1))
    e.append(p("Bidders failing any mandatory requirement shall be disqualified."))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must be registered with the Pakistan Engineering Council (PEC) "
               "in category C-B or higher with relevant electrical and civil works "
               "specialisation codes."],
        ["M2", "The bidder must hold a valid ISO 14001 environmental management "
               "certification covering civil construction activities."],
        ["M3", "The bidder must demonstrate an average annual turnover of at least PKR "
               "2,500 Million over the last three (3) audited financial years."],
        ["M4", "The bidder must have completed at least one (1) safe-city, surveillance "
               "or integrated security project of value not less than PKR 1,500 Million as "
               "prime contractor."],
        ["M5", "The bidder must own or have assured access to civil trenching machinery, "
               "boring equipment and pole-installation plant within 50 km of Islamabad."],
        ["M6", "The bidder must hold a valid ISO 27001 information security management "
               "certification for the command-and-control data systems."],
        ["M7", "The bidder must furnish a bid security of PKR 44 Million (2%) in the form "
               "of a CDR or bank guarantee."],
    ], widths=REQ_WIDTHS))

    e.append(p("3. Technical and Execution Requirements", H1))
    e.append(table([
        ["#", "Requirement"],
        ["T1", "The bidder should submit a detailed methodology covering camera "
               "deployment, civil works, fibre ducting and command-centre integration."],
        ["T2", "The bidder should provide a CPM-based work programme demonstrating "
               "completion within 18 months, including civil-works contingencies."],
        ["T3", "Key staff shall include a Project Manager (PEC-registered professional "
               "engineer, 15+ years), a Civil Works Lead and a Network/Security Lead."],
        ["T4", "The bidder should propose a video-analytics platform with face and "
               "licence-plate recognition and a redundant storage architecture."],
        ["T5", "The bidder should describe its HSE management system for civil works on "
               "live public roads, including a traffic-management plan."],
    ], widths=REQ_WIDTHS))

    e.append(p("4. Evaluation Criteria", H1))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant safe-city / integrated works experience", "30%"],
        ["Financial capability and turnover", "20%"],
        ["Construction and integration methodology", "20%"],
        ["Key personnel, plant and equipment", "20%"],
        ["HSE and environmental compliance", "10%"],
    ], widths=TWO_COL))

    e.append(p("5. Key Dates", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Pre-bid site visit and meeting", "16 June 2026, 10:00 AM"],
        ["Bid submission deadline", "3 July 2026, 11:00 AM"],
        ["Technical bid opening", "3 July 2026, 11:30 AM"],
        ["Bid validity period", "90 days"],
    ], widths=TWO_COL))
    e.append(p("Bids shall be submitted in two separate sealed envelopes to the Director "
               "(Procurement), Capital Development Authority, Islamabad, under the single "
               "stage two envelope procedure as per PPRA Rules 2014."))
    doc.build(e)


if __name__ == "__main__":
    build_rfq()
    build_rfp()
    build_tender()
    print("Test documents written:")
    for f in sorted(HERE.glob("RFQ_*.pdf")) + sorted(HERE.glob("RFP_Managed_*.pdf")) \
            + sorted(HERE.glob("Tender_*.pdf")):
        print(f"  {f.name}  ({f.stat().st_size // 1024} KB)")
