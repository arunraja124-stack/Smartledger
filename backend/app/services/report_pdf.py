from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    Paragraph,
)


def _value(value) -> str:
    return "" if value is None else str(value)


def pdf_report(report_type: str, rows: list) -> bytes:
    output = BytesIO()
    data = [
        {column.name: getattr(row, column.name) for column in row.__table__.columns}
        for row in rows
    ]
    columns = list(data[0]) if data else []
    table_data = [columns] + [[_value(item.get(column)) for column in columns] for item in data]
    page_size = landscape(A4) if len(columns) > 6 else A4
    document = SimpleDocTemplate(
        output,
        pagesize=page_size,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("SmartLedger", styles["Title"]),
        Paragraph(f"{report_type.replace('-', ' ').title()} Report", styles["Heading2"]),
        Spacer(1, 6 * mm),
    ]
    if columns:
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#123B52")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F9FC")]),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No records found for the selected filters.", styles["BodyText"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(12 * mm, 8 * mm, "SmartLedger")
        canvas.drawRightString(page_size[0] - 12 * mm, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()
