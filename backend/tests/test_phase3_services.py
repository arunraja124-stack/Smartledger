import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Base,
    Attendance,
    DocumentExtractedRecord,
    DocumentUpload,
    Employee,
    Purchase,
    SparePart,
    Supplier,
    Visitor,
)
from app.services.documents import _extract_attendance_records, _extract_visitor_records, insert_approved_records
from app.services.reports import workbook


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_approved_supplier_record_is_typed_and_inserted(db: Session) -> None:
    document = DocumentUpload(
        original_filename="test.png",
        stored_filename="test.png",
        register_type="suppliers",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    record = DocumentExtractedRecord(
        document_id=document.id,
        row_number=1,
        extracted_data=json.dumps({"supplier_name": "Typed Supplier"}),
        status="Approved",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    assert insert_approved_records(document, [record], db) == 1
    assert db.query(Supplier).filter_by(supplier_name="Typed Supplier").one()
    assert record.status == "Inserted"


def test_report_workbook_is_an_excel_file() -> None:
    content = workbook([], "attendance")

    assert content[:2] == b"PK"


def test_purchase_insertion_is_idempotent_and_updates_stock_once(db: Session) -> None:
    supplier = Supplier(supplier_name="OCR Supplier")
    part = SparePart(part_code="OCR-1", part_name="OCR Part", available_quantity=2)
    document = DocumentUpload(
        original_filename="purchase.png",
        stored_filename="purchase.png",
        register_type="purchases",
    )
    db.add_all([supplier, part, document])
    db.commit()
    db.refresh(document)
    record = DocumentExtractedRecord(
        document_id=document.id,
        row_number=1,
        extracted_data=json.dumps({
            "invoice_number": "PCH-1",
            "supplier_name": "OCR Supplier",
            "spare_part": "OCR Part",
            "purchase_date": "2026-11-02",
            "quantity": 3,
            "unit_price": "10.00",
            "total_amount": "30.00",
            "payment_status": "Pending",
        }),
        status="Approved",
    )
    db.add(record)
    db.commit()

    assert insert_approved_records(document, [record], db) == 1
    assert insert_approved_records(document, [record], db) == 0
    assert db.query(Purchase).count() == 1
    assert db.get(SparePart, part.id).available_quantity == 5


def test_purchase_batch_validation_does_not_partially_insert(db: Session) -> None:
    supplier = Supplier(supplier_name="Batch Supplier")
    part = SparePart(part_code="BATCH-1", part_name="Batch Part", available_quantity=0)
    document = DocumentUpload(
        original_filename="batch.png",
        stored_filename="batch.png",
        register_type="purchases",
    )
    db.add_all([supplier, part, document])
    db.commit()
    db.refresh(document)
    records = [
        DocumentExtractedRecord(
            document_id=document.id,
            row_number=1,
            extracted_data=json.dumps({
                "invoice_number": "PCH-VALID",
                "supplier_name": "Batch Supplier",
                "spare_part": "Batch Part",
                "purchase_date": "2026-11-02",
                "quantity": 1,
                "unit_price": "10.00",
                "total_amount": "10.00",
            }),
            status="Approved",
        ),
        DocumentExtractedRecord(
            document_id=document.id,
            row_number=2,
            extracted_data=json.dumps({
                "invoice_number": "PCH-INVALID",
                "supplier_name": "Batch Supplier",
                "spare_part": "Batch Part",
                "purchase_date": "2026-11-02",
                "quantity": 2,
                "unit_price": "10.00",
                "total_amount": "1.00",
            }),
            status="Approved",
        ),
    ]
    db.add_all(records)
    db.commit()

    with pytest.raises(Exception):
        insert_approved_records(document, records, db)
    assert db.query(Purchase).count() == 0
    assert db.get(SparePart, part.id).available_quantity == 0


def test_attendance_fixture_extracts_ten_structured_rows() -> None:
    import cv2
    import pytesseract
    from pytesseract import Output

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    image = cv2.imread("uploads/6ead46651c134b67938fe02e8da3063c.png")
    assert image is not None
    scaled = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    data = pytesseract.image_to_data(
        cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY),
        config="--psm 4",
        output_type=Output.DICT,
    )
    records = _extract_attendance_records(scaled, data)
    assert len(records) == 10
    extracted = [record["data"] for record in records]
    assert [record["employee_code"] for record in extracted] == [
        f"EMP{index:03d}" for index in range(1, 11)
    ]
    assert sum(record["status"] == "Present" for record in extracted) == 7
    assert sum(record["status"] == "Absent" for record in extracted) == 2
    assert sum(record["status"] == "Half Day" for record in extracted) == 1


def test_attendance_insertion_resolves_employee_and_is_idempotent(db: Session) -> None:
    employee = Employee(employee_code="EMP001", full_name="Arun Raja N")
    document = DocumentUpload(
        original_filename="attendance.png",
        stored_filename="attendance.png",
        register_type="attendance",
    )
    db.add_all([employee, document])
    db.commit()
    db.refresh(document)
    record = DocumentExtractedRecord(
        document_id=document.id,
        row_number=1,
        extracted_data=json.dumps({
            "employee_code": "EMP001",
            "employee_name": "Arun Raja N",
            "attendance_date": "2026-10-01",
            "status": "Present",
            "in_time": "09:00 AM",
            "out_time": "06:00 PM",
            "remarks": None,
        }),
        status="Approved",
    )
    db.add(record)
    db.commit()

    assert insert_approved_records(document, [record], db) == 1
    assert insert_approved_records(document, [record], db) == 0
    assert db.query(Attendance).count() == 1


def test_attendance_insertion_keeps_identity_snapshot_without_employee(db: Session) -> None:
    document = DocumentUpload(
        original_filename="attendance.png",
        stored_filename="attendance.png",
        register_type="attendance",
        status="Approved",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    record = DocumentExtractedRecord(
        document_id=document.id,
        row_number=1,
        extracted_data=json.dumps({
            "employee_code": "EMP999",
            "employee_name": "Imported Worker",
            "attendance_date": "2026-10-01",
            "status": "Absent",
            "in_time": None,
            "out_time": None,
            "remarks": "Leave",
        }),
        status="Approved",
    )
    db.add(record)
    db.commit()

    assert insert_approved_records(document, [record], db) == 1
    saved = db.query(Attendance).one()
    assert saved.employee_id is None
    assert saved.employee_code == "EMP999"
    assert saved.employee_name == "Imported Worker"
    assert insert_approved_records(document, [record], db) == 0


def test_visitor_extractor_reconstructs_five_structured_rows() -> None:
    headers = [
        ("Visitor Name", 100), ("Organization", 350), ("Purpose", 600),
        ("Contact Number", 850), ("Time In", 1080), ("Time Out", 1240),
    ]
    expected = [
        ("R. Karthik", "Supplier Meeting", "98430 11256", "09:25 AM", "10:10 AM"),
        ("S. Meena", "Service Enquiry", "97918 66532", "10:05 AM", "10:40 AM"),
        ("V. Prakash", "Purchase Discussion", "96005 44321", "11:20 AM", "12:05 PM"),
        ("D. Rajesh", "Spare Parts Inquiry", "99421 77890", "12:30 PM", "01:10 PM"),
        ("N. Divya", "Project Discussion", "93607 55411", "02:15 PM", "03:00 PM"),
    ]
    text = ["14/11/2025"] + [header for header, _ in headers]
    left = [30] + [x for _, x in headers]
    top = [20] + [20] * len(headers)
    for row_index, row in enumerate(expected, start=1):
        values = [row[0], "", row[1], row[2], row[3], row[4]]
        for value, x in zip(values, [100, 350, 600, 850, 1080, 1240]):
            text.append(value)
            left.append(x)
            top.append(100 + row_index * 60)
    data = {
        "text": text,
        "conf": ["95"] * len(text),
        "left": left,
        "top": top,
        "width": [max(10, len(value) * 8) for value in text],
        "height": [20] * len(text),
    }
    records = _extract_visitor_records(type("Image", (), {"shape": (500, 1400)})(), data)
    assert len(records) == 5
    assert [record["data"]["visitor_name"] for record in records] == [row[0] for row in expected]
    assert [record["data"]["purpose"] for record in records] == [row[1] for row in expected]
    assert [record["data"]["contact_number"] for record in records] == [row[2] for row in expected]
    assert [record["data"]["time_in"] for record in records] == [row[3] for row in expected]
    assert [record["data"]["time_out"] for record in records] == [row[4] for row in expected]
    assert all(record["data"]["visit_date"] == "2025-11-14" for record in records)


def test_visitor_insertion_maps_review_fields_and_is_idempotent(db: Session) -> None:
    document = DocumentUpload(
        original_filename="visitors.png",
        stored_filename="visitors.png",
        register_type="visitors",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    record = DocumentExtractedRecord(
        document_id=document.id,
        row_number=1,
        extracted_data=json.dumps({
            "visitor_name": "R. Karthik",
            "visit_date": "2025-11-14",
            "organization": None,
            "purpose": "Supplier Meeting",
            "contact_number": "98430 11256",
            "time_in": "09:25 AM",
            "time_out": "10:10 AM",
        }),
        status="Approved",
    )
    db.add(record)
    db.commit()

    assert insert_approved_records(document, [record], db) == 1
    assert insert_approved_records(document, [record], db) == 0
    saved = db.query(Visitor).one()
    assert saved.visitor_name == "R. Karthik"
    assert saved.entry_date.isoformat() == "2025-11-14"
    assert saved.contact_number == "98430 11256"
