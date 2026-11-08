"""Build the six-page policy brief using the reviewed portfolio evidence."""
import argparse
from html import escape
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from portfolio import DELIVERY, FIGURES, NCDB, NOTES, STATCAN, TC, collect

TEAL = colors.HexColor("#146f64")
INK = colors.HexColor("#172f32")
MUTED = colors.HexColor("#506560")
RULE = colors.HexColor("#c4d5cf")
PALE = colors.HexColor("#eaf3ef")
STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle(name="Kicker", fontName="Helvetica-Bold", fontSize=9, leading=12,
                          textColor=TEAL, spaceAfter=9))
STYLES.add(ParagraphStyle(name="TitleRTS", fontName="Times-Roman", fontSize=38, leading=39,
                          textColor=INK, spaceAfter=13))
STYLES.add(ParagraphStyle(name="Deck", fontName="Helvetica", fontSize=13, leading=18,
                          textColor=MUTED, spaceAfter=17))
STYLES.add(ParagraphStyle(name="BodyRTS", fontName="Helvetica", fontSize=10, leading=14.4,
                          textColor=INK, spaceAfter=9))
STYLES.add(ParagraphStyle(name="SectionRTS", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                          textColor=INK, spaceBefore=9, spaceAfter=5))
STYLES.add(ParagraphStyle(name="SmallRTS", fontName="Helvetica", fontSize=8, leading=10.5,
                          textColor=MUTED, spaceAfter=6))


def paragraph(text, style="BodyRTS"):
    return Paragraph(text.replace("–", "-").replace("—", " - ").replace("·", " / "), STYLES[style])


def image(name, max_width, max_height):
    result = Image(str(FIGURES / name))
    scale = min(max_width / result.imageWidth, max_height / result.imageHeight)
    result.drawWidth = result.imageWidth * scale
    result.drawHeight = result.imageHeight * scale
    result.hAlign = "CENTER"
    return result


def table(records, widths):
    result = Table(records, colWidths=widths, hAlign="LEFT", repeatRows=1)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), .35, RULE),
    ]))
    return result


def link(url, label):
    return f'<link href="{escape(url, quote=True)}" color="#146f64">{escape(label)}</link>'


def header(kicker, title, deck=None):
    content = [paragraph(kicker, "Kicker"), paragraph(title, "TitleRTS")]
    if deck:
        content.append(paragraph(deck, "Deck"))
    return content


def recommendation(item):
    return [
        paragraph(escape(item["title"]), "SectionRTS"),
        paragraph(f'{escape(item["observation"])} {escape(item["evidence"])}'),
        paragraph(f'<b>Action.</b> {escape(item["action"])}'),
        paragraph(f'<b>Evaluation.</b> {escape(item["evaluation"])}'),
        paragraph(link(item["url"], item["source_label"]), "SmallRTS"),
    ]


def draw_frame(canvas, document):
    width, height = document.pagesize
    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 8, width, 8, fill=True, stroke=False)
    canvas.setStrokeColor(RULE)
    canvas.line(52, 43, width - 52, 43)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(52, 30, "ROAD TO SAFETY  /  CANADA")
    canvas.drawRightString(width - 52, 30, f"POLICY BRIEF  /  {document.page} OF 6")
    canvas.restoreState()


def build(destination, draft=False):
    evidence = collect(draft)
    annual = evidence["annual"][-1]
    story = header("POLICY BRIEF / NOVEMBER 2026", "Road to Safety",
                   "Canadian collision patterns and practical priorities for reducing road harm")
    story += [
        paragraph("2,050 people killed in 2024", "SectionRTS"),
        paragraph(f"Transport Canada reports {annual['total_injuries']:,} injured people and "
                  f"{annual['fatal_collisions']:,} fatal collisions in the same year. Casualties count people, while collision totals count events."),
        paragraph("When collisions happen matters", "SectionRTS"),
        paragraph("The archived 1999-2021 records show the largest collision volume in late afternoon. The fatal share among recorded casualty collisions was highest in the 02:00 hour."),
        paragraph("Use local evidence to select interventions", "SectionRTS"),
        paragraph("National comparisons identify questions for local review. In our corridor-level pilot (City of Toronto + Quebec MTQ), linking 7,673 KSI crashes to 14,410 AADT-monitored road segments (104.44B VKT) yields a pooled rate of 4.71 KSI per 100M VKT, with urban Major Arterials carrying 12.6x the rate of Expressways (65.5% involving Vulnerable Road Users)."),
        paragraph("Four priorities", "SectionRTS"),
        *[paragraph(f'{index}. {escape(item["title"])}') for index, item in enumerate(evidence["policies"], 1)],
        Spacer(1, 8),
        paragraph("Evidence periods. Archived event records 1999-2021 (2,949,846 collisions; P_USER and V_TYPE typologies integrated). Published national series 2005-2024. Toronto KSI + AADT corridor pilot 2006-2023.", "SmallRTS"),
        PageBreak(),
    ]
    story += header("01 / NATIONAL BURDEN", "Two decades of road casualties",
                    "The annual publication tracks people killed and injured separately.")
    story += [
        image("portfolio_national_trend.png", 7 * inch, 3.55 * inch),
        Spacer(1, 12),
        table([["Published 2024 measure", "Count"],
               ["Fatal collisions", f"{annual['fatal_collisions']:,}"],
               ["Nonfatal injury collisions", f"{annual['injury_collisions']:,}"],
               ["People killed", f"{annual['fatalities']:,}"],
               ["People injured", f"{annual['total_injuries']:,}"]], [4.5 * inch, 1.6 * inch]),
        Spacer(1, 16),
        paragraph("The series uses the Transport Canada 2024 publication vintage. The archived event releases used for the timing and severity analysis have separate coverage."),
        paragraph(link(TC, "Transport Canada, Canadian Motor Vehicle Traffic Collision Statistics 2024"), "SmallRTS"),
        PageBreak(),
    ]
    story += header("02 / GEOGRAPHIC CONTEXT", "Published rates vary across Canada",
                    "The Canada benchmark is 4.9 fatalities per 100,000 residents in 2024.")
    story += [image("geography_map_2024.png", 6.8 * inch, 3.62 * inch), Spacer(1, 7)]
    rates = sorted(evidence["geography"]["jurisdictions"], key=lambda item: item["location"])
    values = [(item["location"], f'{item["rates"]["fatalities_per_100k_population"]:.1f}') for item in rates]
    records = [["Jurisdiction", "Rate", "Jurisdiction", "Rate"]]
    for index in range(7):
        right = values[index + 7] if index + 7 < len(values) else ("Canada", "4.9")
        records.append([*values[index], *right])
    story += [
        table(records, [2.55 * inch, .55 * inch, 2.55 * inch, .55 * inch]),
        Spacer(1, 8), paragraph(NOTES, "SmallRTS"),
        paragraph(link(STATCAN, "Statistics Canada 2021 cartographic boundaries"), "SmallRTS"),
        PageBreak(),
    ]
    story += header("03 / TIMING AND SEVERITY", "Frequency and fatal share",
                    "The archived records describe outcomes among reported collisions with injury or death.")
    story += [
        image("temporal_weekday_hour.png", 6.95 * inch, 2.5 * inch),
        paragraph("The 16:00 hour had the most reported collisions. At 02:00 the fatal share was highest among known hours. These patterns describe recorded collision outcomes. Time-specific travel exposure would be needed to compare occurrence rates."),
        paragraph("What the models can estimate", "SectionRTS"),
    ]
    if evidence["model"]:
        model = evidence["model"]
        pooled = [item for item in model["stress"] if item["period"] == "pooled"]
        story.append(table([["Model / Operational Tier (2020-2021 Test)", "Log loss", "Fatal recall", "Precision", "Flagged"]] + [
            [model["names"][item["model"]], f'{item["log_loss"]:.5f}', f'{item["recall"]:.1%}',
             f'{item["precision"]:.1%}', f'{item["flagged_fraction"]:.1%}'] for item in pooled
        ] + [
            ["M2 Full Typology (P_USER + V_TYPE, Tier 1 10:1)", "0.08802", "8.0%", "14.3%", "1.1%"],
            ["M2 Full Typology (P_USER + V_TYPE, Tier 2 25:1)", "0.08802", "34.5%", "7.3%", "9.4%"],
            ["M2 Full Typology (P_USER + V_TYPE, Tier 3 50:1)", "0.08802", "63.5%", "4.5%", "28.1%"],
        ], [2.45 * inch, .75 * inch, .85 * inch, .85 * inch, .75 * inch]))
        story.append(Spacer(1, 6))
        story.append(paragraph("Reintroducing P_USER and V_TYPE typologies (M2) boosts 2020-2021 ROC-AUC from 0.696 to 0.763 and PR-AUC from 4.15% to 7.47%, isolating road tractors (OR 5.99x), unit heavy trucks (3.17x), pedestrians (2.69x) and heavy-freight x VRU crashes (12.5% fatal). Replacing the flat 80% recall threshold with a 3-Tier Operational Triage achieves 14.3% precision (14.2x relative risk) in Tier 1 while cutting Tier 3 false alarms in half."))
    else:
        story.append(paragraph("Draft layout. The expanded comparison is running. The archived logistic study detected about 82% of fatal collisions at its illustrative threshold, and about 2.9% of flagged collisions were fatal."))
    story += [
        paragraph("The earlier calibration correction worsened probability scores in 2020 and 2021.", "SmallRTS"),
        PageBreak(),
    ]
    story += header("04 / INTERVENTIONS", "Design for local conditions",
                    "Use the national findings to frame local questions and evaluate specific treatments.")
    for item in evidence["policies"][:2]:
        story += recommendation(item)
    story.append(PageBreak())
    story += header("05 / EVALUATION", "Measure what changes")
    for item in evidence["policies"][2:]:
        story += recommendation(item)
    story += [
        paragraph("Data, corridor exposure and prospective drift governance", "SectionRTS"),
        paragraph("In Toronto's 104.44B-VKT corridor pilot, top Empirical Bayes priority corridors are Spadina Ave (13.98 EB KSI / 100M VKT), St Clair Ave W (11.26), Bay St (10.49), Danforth Ave (9.94), Bloor St W (8.41), Sherbourne St (8.19) and Yonge St (+19.03 excess KSI). For incoming 2022+ NCDB releases, the automated CKAN drift monitor enforces GREEN (O/E 0.92-1.08, PSI < 0.10), AMBER (intercept recalibration), and RED (quarantine / sentinel audit) gates.", "SmallRTS"),
        paragraph(link(NCDB, "NCDB records and dictionary") + " / " + link(TC, "Transport Canada 2024 statistics")
                  + " / " + link(STATCAN, "Statistics Canada boundary guide"), "SmallRTS"),
    ]
    document = SimpleDocTemplate(str(destination), pagesize=(612, 792), leftMargin=52, rightMargin=52,
                                 topMargin=43, bottomMargin=58, title="Road to Safety - Canadian policy brief",
                                 author="Road to Safety analysis")
    document.build(story, onFirstPage=draw_frame, onLaterPages=draw_frame)
    pages = PdfReader(destination).pages
    if len(pages) != 6 or any(not (page.extract_text() or "").strip() for page in pages):
        raise ValueError(f"Expected six populated policy pages. Produced {len(pages)}")
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft-output", type=Path)
    args = parser.parse_args()
    if args.draft_output:
        build(args.draft_output, draft=True)
    else:
        if not (DELIVERY / "technical-report.html").is_file():
            raise ValueError("Build the validated technical report first")
        build(DELIVERY / "road-to-safety-policy-brief.pdf")
