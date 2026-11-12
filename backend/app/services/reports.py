from datetime import date
from io import BytesIO

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import (
    Attendance,
    CustomerEnquiry,
    Purchase,
    SparePart,
    SpareSale,
    Supplier,
    Visitor,
)

REPORTS = {
    "attendance": (Attendance, Attendance.attendance_date),
    "visitors": (Visitor, Visitor.entry_date),
    "purchases": (Purchase, Purchase.purchase_date),
    "spare-sales": (SpareSale, SpareSale.sale_date),
    "suppliers": (Supplier, Supplier.created_at),
    "spare-parts": (SparePart, SparePart.created_at),
    "customer-enquiries": (CustomerEnquiry, CustomerEnquiry.enquiry_date),
}


def report_rows(report_type: str, start_date: date | None, end_date: date | None, db: Session):
    model, date_column = REPORTS[report_type]
    query: Select = select(model)
    if start_date:
        query = query.where(date_column >= start_date)
    if end_date:
        query = query.where(date_column <= end_date)
    return db.scalars(query.order_by(date_column)).all()


def workbook(rows: list, report_type: str) -> bytes:
    data = [
        {column.name: getattr(row, column.name) for column in row.__table__.columns}
        for row in rows
    ]
    frame = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=report_type[:31])
        worksheet = writer.book[report_type[:31]]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
        for index, column in enumerate(frame.columns, start=1):
            values = [str(column)] + [str(value) for value in frame[column].tolist()]
            worksheet.column_dimensions[get_column_letter(index)].width = min(
                max(len(value) for value in values) + 2, 40
            )
    return output.getvalue()


def inventory_workbook(db: Session) -> bytes:
    rows = db.scalars(select(SparePart).order_by(SparePart.part_name)).all()
    return workbook(rows, "inventory")
