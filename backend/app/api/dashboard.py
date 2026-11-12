from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import (
    Attendance,
    CustomerEnquiry,
    Employee,
    Purchase,
    SparePart,
    SpareSale,
    Supplier,
    User,
    Visitor,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    today = date.today()
    present = db.scalar(select(func.count()).where(Attendance.attendance_date == today, Attendance.status == "Present")) or 0
    absent = db.scalar(select(func.count()).where(Attendance.attendance_date == today, Attendance.status == "Absent")) or 0
    low_stock = db.scalar(select(func.count()).where(SparePart.available_quantity <= SparePart.minimum_stock_level)) or 0
    return {
        "total_employees": db.scalar(select(func.count()).select_from(Employee)) or 0,
        "present_today": present,
        "absent_today": absent,
        "total_visitors": db.scalar(select(func.count()).select_from(Visitor)) or 0,
        "total_suppliers": db.scalar(select(func.count()).select_from(Supplier)) or 0,
        "total_spare_parts": db.scalar(select(func.count()).select_from(SparePart)) or 0,
        "low_stock_items": low_stock,
        "total_purchases": db.scalar(select(func.coalesce(func.sum(Purchase.total_amount), 0))) or 0,
        "total_sales": db.scalar(select(func.coalesce(func.sum(SpareSale.total_amount), 0))) or 0,
        "customer_enquiries": db.scalar(select(func.count()).select_from(CustomerEnquiry)) or 0,
    }


@router.get("/attendance")
def attendance_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.execute(
        select(Attendance.attendance_date, Attendance.status, func.count())
        .group_by(Attendance.attendance_date, Attendance.status)
        .order_by(Attendance.attendance_date)
    ).all()
    return [{"date": row[0], "status": row[1], "count": row[2]} for row in rows]


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    purchase_total = db.scalar(select(func.coalesce(func.sum(Purchase.total_amount), 0))) or 0
    sales_total = db.scalar(select(func.coalesce(func.sum(SpareSale.total_amount), 0))) or 0
    enquiries = db.execute(
        select(CustomerEnquiry.status, func.count()).group_by(CustomerEnquiry.status)
    ).all()
    return {
        "purchase_total": purchase_total,
        "sales_total": sales_total,
        "enquiries_by_status": [{"status": row[0], "count": row[1]} for row in enquiries],
    }


@router.get("/low-stock")
def low_stock(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(
        select(SparePart).where(SparePart.available_quantity <= SparePart.minimum_stock_level)
    ).all()
