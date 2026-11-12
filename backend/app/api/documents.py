import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import AuditLog, DocumentExtractedRecord, DocumentUpload, Employee, User
from app.schemas.documents import DocumentPage, DocumentResponse, ReviewRecord, ReviewUpdate
from app.services.documents import (
    _attendance_values,
    _visitor_values,
    export_records,
    insert_approved_records,
    process_upload,
    retry_process_upload,
    save_upload,
    validate_extracted_record,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _document(document_id: int, db: Session) -> DocumentUpload:
    document = db.get(DocumentUpload, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile = File(...),
    register_type: str = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentUpload:
    return save_upload(file, register_type, db)


@router.get("", response_model=DocumentPage)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentPage:
    total = db.scalar(select(func.count()).select_from(DocumentUpload)) or 0
    items = db.scalars(
        select(DocumentUpload)
        .order_by(DocumentUpload.created_at.desc(), DocumentUpload.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return DocumentPage(items=items, total=total, page=page, page_size=page_size)


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentUpload:
    return process_upload(_document(document_id, db), db)


@router.post("/{document_id}/retry", response_model=DocumentResponse)
def retry_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentUpload:
    return retry_process_upload(_document(document_id, db), db)


@router.get("/{document_id}/review", response_model=list[ReviewRecord])
def review_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DocumentExtractedRecord]:
    _document(document_id, db)
    return list(db.scalars(select(DocumentExtractedRecord).where(
        DocumentExtractedRecord.document_id == document_id
    ).order_by(DocumentExtractedRecord.row_number)).all())


@router.put("/{document_id}/review/{record_id}", response_model=ReviewRecord)
def update_review_record(
    document_id: int,
    record_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DocumentExtractedRecord:
    document = _document(document_id, db)
    if document.status in {"Approved", "Completed"}:
        raise HTTPException(status_code=409, detail="Approved documents cannot be edited")
    record = db.scalar(select(DocumentExtractedRecord).where(
        DocumentExtractedRecord.id == record_id,
        DocumentExtractedRecord.document_id == document_id,
    ))
    if record is None:
        raise HTTPException(status_code=404, detail="Extracted record not found")
    if document.register_type == "attendance":
        try:
            data = json.loads(payload.extracted_data)
            employee_code = str(data.get("employee_code", "")).strip()
            employee_name = str(data.get("employee_name", "")).strip()
            employee = db.scalar(select(Employee).where(Employee.employee_code.ilike(employee_code)))
            if employee is not None and employee.full_name.casefold() != employee_name.casefold():
                raise ValueError("Employee name does not match the selected employee")
            _attendance_values(data, db)
            for field in ("in_time", "out_time"):
                value = data.get(field)
                if value and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?:\s?[AP]M)?", str(value).strip(), re.IGNORECASE):
                    raise ValueError(f"{field} must be a valid time")
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    elif document.register_type == "visitors":
        try:
            _visitor_values(json.loads(payload.extracted_data))
        except (json.JSONDecodeError, TypeError, ValueError) as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    record.extracted_data = payload.extracted_data
    record.status = payload.status
    record.validation_error = None
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{document_id}/review/{record_id}", status_code=204)
def delete_review_record(
    document_id: int,
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    document = _document(document_id, db)
    if document.status in {"Approved", "Completed", "Inserted"}:
        raise HTTPException(status_code=409, detail="Approved documents cannot be edited")
    record = db.scalar(select(DocumentExtractedRecord).where(
        DocumentExtractedRecord.id == record_id,
        DocumentExtractedRecord.document_id == document_id,
    ))
    if record is None:
        raise HTTPException(status_code=404, detail="Extracted record not found")
    db.delete(record)
    db.commit()


@router.post("/{document_id}/approve", response_model=DocumentResponse)
def approve_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Staff", "Manager", "Admin")),
) -> DocumentUpload:
    document = _document(document_id, db)
    records = db.scalars(select(DocumentExtractedRecord).where(
        DocumentExtractedRecord.document_id == document_id
    )).all()
    if not records:
        raise HTTPException(status_code=409, detail="No extracted records to approve")
    validation_errors = []
    for record in records:
        try:
            validate_extracted_record(document, record, db)
            record.status = "Approved"
        except HTTPException as error:
            validation_errors.append(f"Row {record.row_number}: {error.detail}")
    if validation_errors:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="; ".join(validation_errors),
        )
    document.approved_row_count = len(records)
    document.status = "Approved"
    db.add(AuditLog(
        user_id=current_user.id,
        action="approve",
        entity_type="document",
        entity_id=document.id,
        details=f"Approved {len(records)} extracted records",
    ))
    db.commit()
    db.refresh(document)
    return document


@router.post("/{document_id}/insert-approved", response_model=DocumentResponse)
def insert_approved(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Staff", "Manager", "Admin")),
) -> DocumentResponse:
    document = _document(document_id, db)
    records = list(db.scalars(select(DocumentExtractedRecord).where(
        DocumentExtractedRecord.document_id == document_id
    )).all())
    inserted = insert_approved_records(document, records, db)
    db.refresh(document)
    return DocumentResponse.model_validate(document).model_copy(
        update={"inserted_row_count": inserted}
    )


@router.get("/{document_id}/export")
def export_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    document = _document(document_id, db)
    return Response(
        content=export_records(document, db),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="document-{document.id}.xlsx"'},
    )
