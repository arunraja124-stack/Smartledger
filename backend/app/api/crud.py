from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models import (
    Attendance, CustomerEnquiry, Employee, Purchase, SparePart, SpareSale,
    Supplier, User, Visitor,
)
from app.schemas import (
    AttendanceCreate, AttendanceResponse, EmployeeCreate, EmployeeResponse,
    EnquiryCreate, EnquiryResponse, PurchaseCreate, PurchaseResponse,
    SparePartCreate, SparePartResponse, SpareSaleCreate, SpareSaleResponse,
    SupplierCreate, SupplierResponse, VisitorCreate, VisitorResponse, Page,
)

router = APIRouter(prefix="", tags=["registers"])


def _list(model: Any, db: Session, page: int, page_size: int):
    total = db.scalar(select(func.count()).select_from(model)) or 0
    items = db.scalars(
        select(model).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def _delete(model: Any, item_id: int, db: Session) -> None:
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(item)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Record is referenced by other data") from error


def _create(model: Any, payload: Any, db: Session):
    item = model(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid related record") from error
    return item


def _get(model: Any, item_id: int, db: Session):
    item = db.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return item


def _update(model: Any, item_id: int, payload: Any, db: Session):
    item = _get(model, item_id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    try:
        db.commit()
        db.refresh(item)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid related record") from error
    return item


@router.get("/employees", response_model=Page[EmployeeResponse])
def list_employees(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(Employee, db, page, page_size)
@router.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _create(Employee, payload, db)
@router.get("/employees/{item_id}", response_model=EmployeeResponse)
def get_employee(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(Employee, item_id, db)
@router.delete("/employees/{item_id}", status_code=204)
def delete_employee(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(Employee, item_id, db)
@router.put("/employees/{item_id}", response_model=EmployeeResponse)
def update_employee(item_id: int, payload: EmployeeCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _update(Employee, item_id, payload, db)

@router.get("/attendance", response_model=Page[AttendanceResponse])
def list_attendance(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(Attendance, db, page, page_size)
@router.post("/attendance", response_model=AttendanceResponse, status_code=201)
def create_attendance(payload: AttendanceCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    values = payload.model_dump()
    employee = db.get(Employee, values["employee_id"]) if values.get("employee_id") else None
    if employee:
        values["employee_code"] = employee.employee_code
        values["employee_name"] = employee.full_name
    return _create(Attendance, AttendanceCreate.model_validate(values), db)
@router.get("/attendance/{item_id}", response_model=AttendanceResponse)
def get_attendance(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(Attendance, item_id, db)
@router.delete("/attendance/{item_id}", status_code=204)
def delete_attendance(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(Attendance, item_id, db)
@router.put("/attendance/{item_id}", response_model=AttendanceResponse)
def update_attendance(item_id: int, payload: AttendanceCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    values = payload.model_dump()
    employee = db.get(Employee, values["employee_id"]) if values.get("employee_id") else None
    if employee:
        values["employee_code"] = employee.employee_code
        values["employee_name"] = employee.full_name
    return _update(Attendance, item_id, AttendanceCreate.model_validate(values), db)

@router.get("/visitors", response_model=Page[VisitorResponse])
def list_visitors(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(Visitor, db, page, page_size)
@router.post("/visitors", response_model=VisitorResponse, status_code=201)
def create_visitor(payload: VisitorCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _create(Visitor, payload, db)
@router.get("/visitors/{item_id}", response_model=VisitorResponse)
def get_visitor(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(Visitor, item_id, db)
@router.delete("/visitors/{item_id}", status_code=204)
def delete_visitor(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(Visitor, item_id, db)
@router.put("/visitors/{item_id}", response_model=VisitorResponse)
def update_visitor(item_id: int, payload: VisitorCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _update(Visitor, item_id, payload, db)

@router.get("/suppliers", response_model=Page[SupplierResponse])
def list_suppliers(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(Supplier, db, page, page_size)
@router.post("/suppliers", response_model=SupplierResponse, status_code=201)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _create(Supplier, payload, db)
@router.get("/suppliers/{item_id}", response_model=SupplierResponse)
def get_supplier(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(Supplier, item_id, db)
@router.delete("/suppliers/{item_id}", status_code=204)
def delete_supplier(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(Supplier, item_id, db)
@router.put("/suppliers/{item_id}", response_model=SupplierResponse)
def update_supplier(item_id: int, payload: SupplierCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _update(Supplier, item_id, payload, db)

@router.get("/spare-parts", response_model=Page[SparePartResponse])
def list_spare_parts(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(SparePart, db, page, page_size)
@router.post("/spare-parts", response_model=SparePartResponse, status_code=201)
def create_spare_part(payload: SparePartCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _create(SparePart, payload, db)
@router.get("/spare-parts/{item_id}", response_model=SparePartResponse)
def get_spare_part(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(SparePart, item_id, db)
@router.delete("/spare-parts/{item_id}", status_code=204)
def delete_spare_part(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(SparePart, item_id, db)
@router.put("/spare-parts/{item_id}", response_model=SparePartResponse)
def update_spare_part(item_id: int, payload: SparePartCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _update(SparePart, item_id, payload, db)

@router.get("/purchases", response_model=Page[PurchaseResponse])
def list_purchases(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(Purchase, db, page, page_size)
@router.post("/purchases", response_model=PurchaseResponse, status_code=201)
def create_purchase(payload: PurchaseCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    part = db.scalar(
        select(SparePart).where(SparePart.id == payload.spare_part_id).with_for_update()
    )
    if part is None:
        raise HTTPException(status_code=404, detail="Spare part not found")
    purchase = Purchase(**payload.model_dump())
    part.available_quantity += payload.quantity
    db.add(purchase)
    try:
        db.commit()
        db.refresh(purchase)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate or invalid purchase") from error
    return purchase
@router.get("/purchases/{item_id}", response_model=PurchaseResponse)
def get_purchase(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(Purchase, item_id, db)
@router.delete("/purchases/{item_id}", status_code=204)
def delete_purchase(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    purchase = _get(Purchase, item_id, db)
    part = db.scalar(select(SparePart).where(SparePart.id == purchase.spare_part_id).with_for_update())
    if part is None or part.available_quantity < purchase.quantity:
        raise HTTPException(status_code=409, detail="Stock cannot be reconciled for this purchase")
    part.available_quantity -= purchase.quantity
    db.delete(purchase)
    db.commit()
@router.put("/purchases/{item_id}", response_model=PurchaseResponse)
def update_purchase(item_id: int, payload: PurchaseCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    purchase = _get(Purchase, item_id, db)
    part_ids = {purchase.spare_part_id, payload.spare_part_id}
    parts = {
        part.id: part for part in db.scalars(
            select(SparePart).where(SparePart.id.in_(part_ids)).with_for_update()
        ).all()
    }
    if payload.spare_part_id not in parts:
        raise HTTPException(status_code=404, detail="Spare part not found")
    old_part = parts[purchase.spare_part_id]
    new_part = parts[payload.spare_part_id]
    if old_part.id == new_part.id:
        new_quantity = new_part.available_quantity - purchase.quantity + payload.quantity
        if new_quantity < 0:
            raise HTTPException(status_code=409, detail="Stock cannot become negative")
        new_part.available_quantity = new_quantity
    else:
        if old_part.available_quantity < purchase.quantity:
            raise HTTPException(status_code=409, detail="Stock cannot be reconciled for this purchase")
        old_part.available_quantity -= purchase.quantity
        new_part.available_quantity += payload.quantity
    for key, value in payload.model_dump().items():
        setattr(purchase, key, value)
    db.commit()
    db.refresh(purchase)
    return purchase

@router.get("/spare-sales", response_model=Page[SpareSaleResponse])
def list_spare_sales(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(SpareSale, db, page, page_size)
@router.post("/spare-sales", response_model=SpareSaleResponse, status_code=201)
def create_spare_sale(payload: SpareSaleCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    part = db.scalar(select(SparePart).where(SparePart.id == payload.spare_part_id).with_for_update())
    if part is None:
        raise HTTPException(status_code=404, detail="Spare part not found")
    if part.available_quantity < payload.quantity_sold:
        raise HTTPException(status_code=409, detail="Insufficient spare-part stock")
    part.available_quantity -= payload.quantity_sold
    sale = SpareSale(**payload.model_dump())
    db.add(sale)
    try:
        db.commit()
        db.refresh(sale)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Invalid spare sale") from error
    return sale
@router.get("/spare-sales/{item_id}", response_model=SpareSaleResponse)
def get_spare_sale(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(SpareSale, item_id, db)
@router.delete("/spare-sales/{item_id}", status_code=204)
def delete_spare_sale(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sale = _get(SpareSale, item_id, db)
    part = db.scalar(select(SparePart).where(SparePart.id == sale.spare_part_id).with_for_update())
    if part is None:
        raise HTTPException(status_code=404, detail="Spare part not found")
    part.available_quantity += sale.quantity_sold
    db.delete(sale)
    db.commit()
@router.put("/spare-sales/{item_id}", response_model=SpareSaleResponse)
def update_spare_sale(item_id: int, payload: SpareSaleCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    sale = _get(SpareSale, item_id, db)
    part_ids = {sale.spare_part_id, payload.spare_part_id}
    parts = {
        part.id: part for part in db.scalars(
            select(SparePart).where(SparePart.id.in_(part_ids)).with_for_update()
        ).all()
    }
    if payload.spare_part_id not in parts:
        raise HTTPException(status_code=404, detail="Spare part not found")
    old_part = parts[sale.spare_part_id]
    new_part = parts[payload.spare_part_id]
    if old_part.id == new_part.id:
        new_quantity = new_part.available_quantity + sale.quantity_sold - payload.quantity_sold
        if new_quantity < 0:
            raise HTTPException(status_code=409, detail="Insufficient spare-part stock")
        new_part.available_quantity = new_quantity
    else:
        new_part.available_quantity += 0
        if new_part.available_quantity < payload.quantity_sold:
            raise HTTPException(status_code=409, detail="Insufficient spare-part stock")
        old_part.available_quantity += sale.quantity_sold
        new_part.available_quantity -= payload.quantity_sold
    for key, value in payload.model_dump().items():
        setattr(sale, key, value)
    db.commit()
    db.refresh(sale)
    return sale

@router.get("/customer-enquiries", response_model=Page[EnquiryResponse])
def list_enquiries(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100), db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _list(CustomerEnquiry, db, page, page_size)
@router.post("/customer-enquiries", response_model=EnquiryResponse, status_code=201)
def create_enquiry(payload: EnquiryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _create(CustomerEnquiry, payload, db)
@router.get("/customer-enquiries/{item_id}", response_model=EnquiryResponse)
def get_enquiry(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _get(CustomerEnquiry, item_id, db)
@router.delete("/customer-enquiries/{item_id}", status_code=204)
def delete_enquiry(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)): _delete(CustomerEnquiry, item_id, db)
@router.put("/customer-enquiries/{item_id}", response_model=EnquiryResponse)
def update_enquiry(item_id: int, payload: EnquiryCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)): return _update(CustomerEnquiry, item_id, payload, db)
