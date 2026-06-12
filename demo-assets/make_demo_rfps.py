"""Generate the two synthetic demo RFP PDFs (realistic Pakistani public-procurement
style). These are the guaranteed-to-work demo documents; real downloaded tenders
can be demoed as stretch.

Doc 1 (Solar PV, Energy, PKR 280M)   -> engineered to land a GO decision.
Doc 2 (Road Rehab, Construction, PKR 1.8B) -> lands CONDITIONAL/NO-GO with gaps.
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
H2 = ParagraphStyle("H2x", parent=styles["Heading2"], spaceBefore=10)
BODY = ParagraphStyle("Bodyx", parent=styles["BodyText"], leading=15)
TITLE = ParagraphStyle("Titlex", parent=styles["Title"], alignment=TA_CENTER)


def table(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff6ff")]),
    ]))
    return t


def p(text, style=BODY):
    return Paragraph(text, style)


def build_solar() -> None:
    doc = SimpleDocTemplate(str(HERE / "RFP_Solar_PV_Hospitals.pdf"), pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    e = []
    e.append(Spacer(1, 60))
    e.append(p("GOVERNMENT OF PUNJAB<br/>ENERGY DEPARTMENT", TITLE))
    e.append(Spacer(1, 12))
    e.append(p("REQUEST FOR PROPOSALS (RFP)", TITLE))
    e.append(p("Design, Supply, Installation and Commissioning of Grid-Tied Solar PV "
               "Systems (5 MW Aggregate) at Twelve Public Hospitals", TITLE))
    e.append(Spacer(1, 24))
    e.append(p("RFP Reference No: ED/PROC/2026/RFP-117<br/>"
               "Issue Date: 1 June 2026<br/>"
               "Estimated Project Cost: PKR 280 Million<br/>"
               "Procurement Method: Single Stage – Two Envelope (PPRA Rules 2014)", TITLE))
    e.append(PageBreak())

    e.append(p("1. Background and Objectives", H1))
    e.append(p("The Energy Department, Government of Punjab, intends to reduce the grid "
               "electricity expenditure of public healthcare facilities by deploying "
               "grid-tied solar photovoltaic systems with an aggregate capacity of 5 MW "
               "across twelve district hospitals. The successful bidder shall design, "
               "supply, install, test and commission the systems, including net-metering "
               "approvals, and provide operations and maintenance services for a period "
               "of three (3) years from commissioning."))
    e.append(p("2. Scope of Work", H1))
    e.append(p("The scope includes: (a) site surveys and detailed engineering design for "
               "each hospital; (b) supply of Tier-1 solar PV modules, string inverters and "
               "mounting structures; (c) civil and electrical installation works; (d) SCADA-"
               "based remote monitoring with a central dashboard; (e) liaison with DISCOs "
               "for net-metering licenses; (f) training of hospital engineering staff; and "
               "(g) comprehensive O&M including performance guarantees for 3 years."))

    e.append(p("3. Eligibility and Mandatory Requirements", H1))
    e.append(p("Bidders failing any mandatory requirement shall be disqualified."))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must have successfully completed at least two (2) solar PV or "
               "renewable energy projects each of contract value not less than PKR 100 "
               "Million during the last seven (7) years."],
        ["M2", "The bidder must hold a valid ISO 9001 quality management certification."],
        ["M3", "The bidder must have prior experience working with federal or provincial "
               "government clients in Pakistan."],
        ["M4", "The bidder must submit a bid security of two percent (2%) of the bid price "
               "in the form of a bank guarantee from a scheduled bank."],
        ["M5", "The project manager assigned must hold a valid PMP certification with a "
               "minimum of eight (8) years of infrastructure project experience."],
        ["M6", "The bidder must be registered with the Federal Board of Revenue and provide "
               "an active taxpayer certificate."],
    ], widths=[1.2 * cm, 14.5 * cm]))

    e.append(p("4. Technical Requirements", H1))
    e.append(table([
        ["#", "Technical Requirement"],
        ["T1", "Solar PV modules shall be Tier-1, with a minimum module efficiency of 21% "
               "and a 25-year linear performance warranty."],
        ["T2", "The bidder should provide a SCADA or IoT-based remote monitoring solution "
               "with a centralized web dashboard covering all twelve sites."],
        ["T3", "The bidder should demonstrate in-house engineering capability for grid "
               "interconnection studies and protection coordination."],
        ["T4", "All electrical works shall comply with IEC 62548 and the Pakistan "
               "Electricity Code; installation teams should include licensed electricians."],
        ["T5", "The bidder should propose a preventive maintenance plan with quarterly site "
               "visits and a 48-hour fault-response commitment."],
        ["T6", "The bidder should describe its HSE policy and provide evidence of safe "
               "execution of works at operational healthcare facilities."],
        ["T7", "The bidder should provide a structured training and knowledge-transfer "
               "program for hospital engineering staff."],
        ["T8", "Experience integrating renewable energy systems with hospital or other "
               "critical infrastructure will be considered an advantage."],
    ], widths=[1.2 * cm, 14.5 * cm]))

    e.append(p("5. Evaluation Criteria", H1))
    e.append(p("Technical proposals will be evaluated out of 100 marks. Bidders scoring "
               "less than 70 marks in the technical evaluation shall not be considered "
               "for financial evaluation."))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant project experience and past performance", "30%"],
        ["Technical approach, methodology and work plan", "25%"],
        ["Key personnel qualifications and team composition", "15%"],
        ["Quality assurance, HSE and risk management", "15%"],
        ["Financial capability and certifications", "15%"],
    ], widths=[12 * cm, 3.7 * cm]))

    e.append(p("6. Key Dates and Submission", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Pre-bid meeting (Energy Department Committee Room, Lahore)", "18 June 2026, 11:00 AM"],
        ["Deadline for written queries", "24 June 2026"],
        ["Proposal submission deadline", "9 July 2026, 02:00 PM"],
        ["Technical bid opening", "9 July 2026, 02:30 PM"],
        ["Bid validity period", "120 days"],
    ], widths=[11 * cm, 4.7 * cm]))
    e.append(p("Proposals shall be submitted in two separate sealed envelopes marked "
               "\"Technical Proposal\" and \"Financial Proposal\", one original and two "
               "copies each, addressed to the Section Officer (Procurement), Energy "
               "Department, Government of Punjab, Lahore."))

    e.append(p("7. Required Proposal Sections", H1))
    e.append(p("Bidders must respond to each of the following sections: (Q1) Company "
               "profile and relevant experience; (Q2) Understanding of the assignment and "
               "proposed technical approach; (Q3) Detailed work plan and timeline; (Q4) "
               "Team composition with CVs of key personnel; (Q5) Quality assurance, HSE "
               "and risk management plans; (Q6) O&M and training methodology; (Q7) "
               "Certifications and statutory registrations."))
    doc.build(e)


def build_road() -> None:
    doc = SimpleDocTemplate(str(HERE / "RFP_District_Road_Rehabilitation.pdf"), pagesize=A4,
                            topMargin=2 * cm, bottomMargin=2 * cm)
    e = []
    e.append(Spacer(1, 60))
    e.append(p("GOVERNMENT OF KHYBER PAKHTUNKHWA<br/>COMMUNICATION & WORKS DEPARTMENT", TITLE))
    e.append(Spacer(1, 12))
    e.append(p("INVITATION FOR BIDS (TENDER)", TITLE))
    e.append(p("Rehabilitation and Widening of 64 km District Roads Package-IV "
               "(Including Three Bridges)", TITLE))
    e.append(Spacer(1, 24))
    e.append(p("Tender No: CW/KP/2026/PKG-IV-221<br/>"
               "Issue Date: 28 May 2026<br/>"
               "Estimated Cost: PKR 1,850 Million<br/>"
               "Procurement Method: National Competitive Bidding", TITLE))
    e.append(PageBreak())

    e.append(p("1. Project Description", H1))
    e.append(p("The Communication & Works Department invites sealed bids for the "
               "rehabilitation, widening and improvement of 64 kilometres of district "
               "roads under Package-IV, including reconstruction of three (3) reinforced "
               "concrete bridges of spans 40m, 65m and 110m, road-side drainage, "
               "retaining structures and road safety furniture. The construction period "
               "is twenty-four (24) months including two monsoon seasons."))

    e.append(p("2. Mandatory Eligibility Requirements", H1))
    e.append(table([
        ["#", "Mandatory Requirement"],
        ["M1", "The bidder must be registered with the Pakistan Engineering Council (PEC) "
               "in category C-A or C-1 with relevant specialization codes (CE01, CE02)."],
        ["M2", "The bidder must have completed at least three (3) road construction "
               "contracts each of value not less than PKR 700 Million in the last ten years."],
        ["M3", "The bidder must have completed at least one (1) bridge structure of span "
               "60 metres or greater as prime contractor."],
        ["M4", "Average annual construction turnover of at least PKR 1,500 Million over "
               "the last three audited financial years, supported by audited statements."],
        ["M5", "Bid security of PKR 37 Million (2%) in the form of CDR or bank guarantee."],
        ["M6", "The bidder must own or have assured access to a batching plant, asphalt "
               "plant and crusher within 50 km of the project corridor."],
        ["M7", "Valid ISO 14001 environmental management certification is required for "
               "works within the protected watershed zone."],
    ], widths=[1.2 * cm, 14.5 * cm]))

    e.append(p("3. Technical and Execution Requirements", H1))
    e.append(table([
        ["#", "Requirement"],
        ["T1", "The bidder should submit a detailed construction methodology covering "
               "earthworks, pavement layers, structures and traffic management."],
        ["T2", "The bidder should provide a CPM-based work program demonstrating "
               "completion within 24 months including monsoon contingencies."],
        ["T3", "Key staff shall include a Project Manager (PEC registered professional "
               "engineer, 15+ years), a Bridge Engineer (10+ years) and a Materials "
               "Engineer (10+ years)."],
        ["T4", "The bidder should describe its HSE management system; a documented "
               "zero-fatality record over the last five years is preferred."],
        ["T5", "The bidder should propose a quality control plan with on-site laboratory "
               "facilities for soils, aggregates, concrete and asphalt testing."],
        ["T6", "Experience executing road or bridge works for federal or provincial "
               "government clients will be evaluated favourably."],
    ], widths=[1.2 * cm, 14.5 * cm]))

    e.append(p("4. Evaluation Criteria", H1))
    e.append(table([
        ["Criterion", "Weight"],
        ["Relevant experience (roads and structures)", "35%"],
        ["Financial capability and turnover", "20%"],
        ["Construction methodology and work program", "20%"],
        ["Key personnel and equipment", "15%"],
        ["QA/QC, HSE and environmental compliance", "10%"],
    ], widths=[12 * cm, 3.7 * cm]))

    e.append(p("5. Key Dates", H1))
    e.append(table([
        ["Milestone", "Date"],
        ["Pre-bid site visit and meeting", "16 June 2026, 10:00 AM"],
        ["Bid submission deadline", "2 July 2026, 11:00 AM"],
        ["Bid opening", "2 July 2026, 11:30 AM"],
        ["Bid validity", "90 days"],
    ], widths=[11 * cm, 4.7 * cm]))
    e.append(p("Bids shall be submitted to the Office of the Superintending Engineer, "
               "C&W Circle, Peshawar, in sealed envelopes under the single stage one "
               "envelope procedure as per KPPRA Rules 2014."))
    doc.build(e)


if __name__ == "__main__":
    build_solar()
    build_road()
    print("Demo RFPs written:",
          [f.name for f in HERE.glob("RFP_*.pdf")])
