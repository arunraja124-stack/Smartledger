from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.database import get_db
from app.models import SparePart, User
from app.services.reports import REPORTS, inventory_workbook, report_rows, workbook
from app.services.report_pdf import pdf_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_type}")
def report(
    report_type: str,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    if report_type not in REPORTS and report_type != "inventory":
        raise HTTPException(status_code=404, detail="Report type not found")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")
    if report_type == "inventory":
        return list(db.scalars(select(SparePart).order_by(SparePart.part_name)).all())
    return report_rows(report_type, start_date, end_date, db)


@router.get("/{report_type}/export")
def report_export(
    report_type: str,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    if report_type == "inventory":
        content = inventory_workbook(db)
    elif report_type in REPORTS:
        if start_date and end_date and start_date > end_date:
            raise HTTPException(status_code=422, detail="start_date must be before end_date")
        content = workbook(report_rows(report_type, start_date, end_date, db), report_type)
    else:
        raise HTTPException(status_code=404, detail="Report type not found")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{report_type}.xlsx"'},
    )


@router.get("/{report_type}/pdf")
def report_pdf(
    report_type: str,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Admin")),
):
    if report_type not in REPORTS and report_type != "inventory":
        raise HTTPException(status_code=404, detail="Report type not found")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")
    rows = (
        report_rows(report_type, start_date, end_date, db)
        if report_type in REPORTS
        else list(db.scalars(select(SparePart).order_by(SparePart.part_name)).all())
    )
    return Response(
        content=pdf_report(report_type, rows),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{report_type}.pdf"'},
    )
