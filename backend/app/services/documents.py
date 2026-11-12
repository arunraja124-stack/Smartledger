import json
import re
from difflib import SequenceMatcher
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict
from pathlib import Path

import cv2
import pandas as pd
import pytesseract
from fastapi import HTTPException, UploadFile
from openpyxl.styles import Font
from pytesseract import Output
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import (
    Attendance,
    CustomerEnquiry,
    DocumentExtractedRecord,
    DocumentUpload,
    Employee,
    Purchase,
    SparePart,
    SpareSale,
    Supplier,
    Visitor,
)
from app.schemas import (
    AttendanceCreate,
    EmployeeCreate,
    EnquiryCreate,
    PurchaseCreate,
    SparePartCreate,
    SpareSaleCreate,
    SupplierCreate,
    VisitorCreate,
)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _upload_dir() -> Path:
    configured = Path(get_settings().upload_dir)
    if configured.is_absolute():
        return configured
    return Path(__file__).resolve().parents[3] / configured


def save_upload(upload: UploadFile, register_type: str, db: Session) -> DocumentUpload:
    if register_type not in REGISTER_SCHEMAS:
        raise HTTPException(status_code=422, detail="Unsupported target register")
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only JPG, JPEG, and PNG files are supported")
    content = upload.file.read()
    settings = get_settings()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit")
    upload_dir = _upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{__import__('uuid').uuid4().hex}{extension}"
    (upload_dir / stored_name).write_bytes(content)
    document = DocumentUpload(
        original_filename=upload.filename or stored_name,
        stored_filename=stored_name,
        register_type=register_type,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def process_upload(document: DocumentUpload, db: Session) -> DocumentUpload:
    if document.status in {"Review Required", "Approved", "Completed", "Inserted"}:
        raise HTTPException(status_code=409, detail="Document has already been processed")
    try:
        extracted = _run_ocr(document)
    except HTTPException:
        document.status = "Failed"
        db.commit()
        raise
    _save_extracted_records(document, extracted, db)
    return document


def retry_process_upload(document: DocumentUpload, db: Session) -> DocumentUpload:
    if document.register_type != "purchases":
        raise HTTPException(status_code=422, detail="Retry OCR is currently supported for purchases only")
    existing_records = list(document.extracted_records)
    if not existing_records or any(record.status == "Inserted" for record in existing_records):
        raise HTTPException(
            status_code=409,
            detail="This document is not an eligible legacy purchase OCR result",
        )
    if not all(_is_legacy_raw_record(record) for record in existing_records):
        raise HTTPException(
            status_code=409,
            detail="Retry is available only for legacy unstructured purchase records",
        )
    try:
        extracted = _run_ocr(document)
    except HTTPException as error:
        document.processing_error = error.detail
        db.commit()
        raise
    for record in existing_records:
        db.delete(record)
    db.flush()
    _save_extracted_records(document, extracted, db)
    return document


def _run_ocr(document: DocumentUpload) -> list[dict]:
    settings = get_settings()
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    path = _upload_dir() / document.stored_filename
    image = cv2.imread(str(path))
    if image is None:
        document.status = "Failed"
        document.processing_error = "Uploaded image could not be decoded"
        raise HTTPException(status_code=422, detail=document.processing_error)
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        data = pytesseract.image_to_data(
            scaled,
            config="--psm 4",
            output_type=Output.DICT,
        )
        text = pytesseract.image_to_string(scaled, config="--psm 4")
    except pytesseract.TesseractNotFoundError as error:
        document.status = "Failed"
        document.processing_error = "Tesseract OCR is not installed or is not available on PATH"
        raise HTTPException(status_code=503, detail=document.processing_error) from error
    if document.register_type == "purchases":
        extracted = _extract_purchase_records(_deskew_image(image))
    elif document.register_type == "attendance":
        extracted = _extract_attendance_records(scaled, data)
    elif document.register_type == "visitors":
        # PSM 4 finds the handwritten rows reliably; PSM 6 recognizes the
        # multi-word column headings more consistently.
        visitor_headers = pytesseract.image_to_data(
            scaled,
            config="--psm 6",
            output_type=Output.DICT,
        )
        extracted = _extract_visitor_records(scaled, data, visitor_headers)
    else:
        extracted = _extract_text_records(text, data)
    if document.register_type in {"purchases", "attendance", "visitors"} and not extracted:
        error = (
            f"{document.register_type.title()} OCR did not produce any structured rows. "
            "Check the image and retry."
        )
        raise HTTPException(status_code=422, detail=error)
    return extracted


def _is_legacy_raw_record(record: DocumentExtractedRecord) -> bool:
    try:
        data = json.loads(record.extracted_data)
    except json.JSONDecodeError:
        return False
    return set(data) == {"raw_text"} and bool(data["raw_text"].strip())


def _save_extracted_records(
    document: DocumentUpload, extracted: list[dict], db: Session
) -> None:
    for row_number, item in enumerate(extracted, start=1):
        record = DocumentExtractedRecord(
            document_id=document.id,
            row_number=row_number,
            extracted_data=json.dumps(item["data"]),
            confidence=item["confidence"],
            status="Review Required",
        )
        db.add(record)
    document.extracted_row_count = len(extracted)
    document.processing_error = None
    document.status = "Review Required"
    db.commit()
    db.refresh(document)


def _extract_text_records(text: str, data: dict) -> list[dict]:
    line_confidences: dict[str, list[float]] = {}
    for index, value in enumerate(data.get("text", [])):
        value = value.strip()
        if not value:
            continue
        try:
            confidence = float(data["conf"][index])
        except (KeyError, TypeError, ValueError):
            continue
        if confidence >= 0:
            key = "-".join(
                str(data.get(field, [""])[index])
                for field in ("block_num", "par_num", "line_num")
            )
            line_confidences.setdefault(key, []).append(confidence)
    ordered_confidences = [
        sum(values) / len(values) for values in line_confidences.values() if values
    ]
    result = []
    for line_number, line in enumerate(
        (line.strip() for line in text.splitlines()), start=1
    ):
        if not line:
            continue
        confidence = ordered_confidences[line_number - 1] if line_number <= len(ordered_confidences) else None
        result.append({
            "data": {"raw_text": line},
            "confidence": round(confidence, 2) if confidence is not None else None,
        })
    return result


def _attendance_words(data: dict) -> list[dict]:
    words = []
    for index, value in enumerate(data.get("text", [])):
        text = str(value).strip()
        if not text:
            continue
        try:
            confidence = float(data["conf"][index])
        except (KeyError, TypeError, ValueError):
            confidence = -1
        if confidence < 0:
            continue
        words.append({
            "text": text,
            "x": int(data["left"][index]),
            "y": int(data["top"][index]),
            "w": int(data["width"][index]),
            "h": int(data["height"][index]),
            "confidence": confidence,
        })
    return words


def _normalise_employee_code(value: str, row_number: int) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", value.upper())
    compact = compact.replace("O", "0").replace("I", "1").replace("L", "1")
    match = re.search(r"EMP(\d{1,3})", compact)
    if match:
        return f"EMP{int(match.group(1)):03d}"
    return f"EMP{row_number:03d}"


def _normalise_attendance_date(value: str, default_month: int | None = None) -> str | None:
    value = re.sub(r"\s+", "", value.upper()).replace("O", "0").replace("I", "1").replace("L", "1").replace("!", "1")
    match = re.search(r"(\d{1,3})[-/.](\d{1,2})[-/.](\d{4})", value)
    if not match:
        return None
    try:
        day = match.group(1)
        if len(day) == 3 and day.startswith("0"):
            day = day[:2]
        month = default_month or int(match.group(2))
        return date(int(match.group(3)), month, int(day)).isoformat()
    except ValueError:
        return None


def _normalise_time(value: str) -> str | None:
    value = re.sub(r"[^0-9APM:. ]", " ", value.upper())
    match = re.search(r"(\d{1,2})[:.](\d{2})\s*([AP]M)?", value)
    if not match:
        return None
    hour, minute, meridiem = int(match.group(1)), int(match.group(2)), match.group(3)
    if meridiem:
        return f"{hour:02d}:{minute:02d} {meridiem}"
    return f"{hour:02d}:{minute:02d}"


def _normalise_attendance_name(value: str) -> str:
    tokens = []
    for token in value.split():
        cleaned = token.strip("|,.;:'\"")
        if not cleaned or cleaned.isdigit():
            continue
        normalised = cleaned.replace("1s", "S").replace("l5", "S")
        if normalised.lower() in {"is", "1s", "l5"}:
            normalised = "S"
        tokens.append(normalised)
    return " ".join(tokens)


def _extract_attendance_records(image, ocr_data: dict) -> list[dict]:
    words = _attendance_words(ocr_data)
    status_words = [
        word for word in words
        if word["text"].lower() in {"present", "absent", "half"}
    ]
    rows = []
    month_names = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    default_month = next(
        (month_names[word["text"].lower()[:3]] for word in words if word["text"].lower()[:3] in month_names),
        None,
    )
    for status_word in status_words:
        center_y = status_word["y"] + status_word["h"] // 2
        if any(abs(center_y - row["y"]) < 35 for row in rows):
            continue
        row_words = [
            word for word in words
            if abs((word["y"] + word["h"] // 2) - center_y) <= 68
        ]
        status = status_word["text"].title()
        if status == "Half":
            status = "Half Day"
        elif status == "Present":
            status = "Present"
        else:
            status = "Absent"
        rows.append({"y": center_y, "words": row_words, "status": status})
    rows.sort(key=lambda row: row["y"])
    if not rows:
        return []

    column_centers = {
        "employee_code": 340,
        "name": 850,
        "date": 1320,
        "status": 1680,
        "in_time": 2040,
        "out_time": 2400,
        "remarks": 2780,
    }
    records = []
    for row_number, row in enumerate(rows, start=1):
        row_words = row["words"]
        width = image.shape[1]
        boundaries = [
            0,
            int(width * 0.19),
            int(width * 0.40),
            int(width * 0.51),
            int(width * 0.64),
            int(width * 0.73),
            int(width * 0.85),
            width,
        ]

        def between(left: int, right: int) -> list[str]:
            return [
                word["text"] for word in row_words
                if left <= word["x"] + word["w"] // 2 < right
            ]
        columns = {
            key: between(boundaries[index], boundaries[index + 1])
            for index, key in enumerate(column_centers)
        }
        code_text = " ".join(columns["employee_code"]).strip()
        name = _normalise_attendance_name(" ".join(columns["name"]))
        attendance_date = next(
            (parsed for value in columns["date"] if (parsed := _normalise_attendance_date(value, default_month))),
            None,
        )
        in_time = _normalise_time(" ".join(columns["in_time"]))
        out_time = _normalise_time(" ".join(columns["out_time"]))
        remarks = " ".join(columns["remarks"]).strip() or None
        if not name or any(token in name.lower() for token in ("summary", "present", "absent", "half day")):
            continue
        confidence_values = [word["confidence"] for word in row_words]
        records.append({
            "data": {
                "employee_code": _normalise_employee_code(code_text, row_number),
                "employee_name": name,
                "attendance_date": attendance_date,
                "status": row["status"],
                "in_time": in_time,
                "out_time": out_time,
                "remarks": remarks,
                "original_ocr_text": " ".join(word["text"] for word in row_words),
                "extraction_warnings": (
                    ["Employee code was normalized from OCR"]
                    if not re.search(r"EMP\d{1,3}", code_text.upper().replace("O", "0"))
                    else []
                ),
            },
            "confidence": round(sum(confidence_values) / len(confidence_values), 2)
            if confidence_values else None,
        })
    return records


_VISITOR_COLUMNS = {
    "visitor_name": ("visitor", "name"),
    "organization": ("organization", "company", "organisation"),
    "purpose": ("purpose", "reason"),
    "contact_number": ("contact", "phone", "mobile"),
    "time_in": ("time", "arrival", "in"),
    "time_out": ("time", "departure", "out", "exit"),
}


def _visitor_column_key(text: str) -> str | None:
    normalized = re.sub(r"[^a-z ]", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return None
    tokens = set(normalized.split())
    # Check the directional word before the generic "time" token. OCR often
    # returns "Time" and "Out" as separate boxes, or the whole phrase as one.
    if tokens & {"out", "exit", "departure"}:
        return "time_out"
    if tokens & {"in", "im", "arrival"}:
        return "time_in"
    if tokens & {"visitor", "name"}:
        return "visitor_name"
    if tokens & {"organization", "organisation", "company"}:
        return "organization"
    if tokens & {"purpose", "reason"}:
        return "purpose"
    if tokens & {"contact", "phone", "mobile"}:
        return "contact_number"
    return None


def _visitor_header_centers(words: list[dict], image) -> tuple[dict[str, int], int]:
    """Find field centers from header phrases, including split OCR words."""
    header_words = [
        word for word in words
        if word["y"] + word["h"] / 2 < image.shape[0] * 0.36
        and (
            _visitor_column_key(word["text"]) is not None
            or re.sub(r"[^a-z0-9]", "", word["text"].lower()) == "time"
        )
    ]
    # The page title also contains "Visitors"; do not let it pull the name
    # column toward the left edge of the table.
    title_words = [
        word for word in words
        if word["y"] + word["h"] / 2 < image.shape[0] * 0.16
        and re.search(r"register", word["text"], re.IGNORECASE)
    ]
    header_words = [
        word for word in header_words
        if not (
            _visitor_column_key(word["text"]) == "visitor_name"
            and any(abs((word["y"] + word["h"] / 2) - (title["y"] + title["h"] / 2)) < 80 for title in title_words)
        )
    ]
    centers: dict[str, list[int]] = defaultdict(list)
    consumed: set[int] = set()

    # A lone "Time" has no direction. Pair it with the nearby In/Out token so
    # phrases split into separate OCR boxes still anchor the right column.
    for index, word in enumerate(header_words):
        token = re.sub(r"[^a-z0-9]", "", word["text"].lower())
        if token != "time":
            continue
        candidates = []
        for other_index, other in enumerate(header_words):
            if other_index == index:
                continue
            other_token = re.sub(r"[^a-z0-9]", "", other["text"].lower())
            key = (
                "time_in" if other_token in {"in", "im", "1n", "arrival"}
                else "time_out" if other_token in {"out", "exit", "departure"}
                else None
            )
            dx = abs((word["x"] + word["w"] / 2) - (other["x"] + other["w"] / 2))
            dy = abs((word["y"] + word["h"] / 2) - (other["y"] + other["h"] / 2))
            if key and dx <= image.shape[1] * 0.12 and dy <= max(100, image.shape[0] * 0.08):
                candidates.append((dx + dy, key, other_index, other))
        if candidates:
            _, key, other_index, other = min(candidates, key=lambda item: item[0])
            centers[key].append(round(
                (word["x"] + word["w"] / 2 + other["x"] + other["w"] / 2) / 2
            ))
            consumed.update((index, other_index))

    for index, word in enumerate(header_words):
        if index in consumed:
            continue
        key = _visitor_column_key(word["text"])
        if key:
            centers[key].append(word["x"] + word["w"] // 2)

    # Keep adjacent non-data headings as geometric anchors. They help bound
    # the first and last visitor fields without treating dates/signatures as
    # extracted business values.
    for word in words:
        if word["y"] + word["h"] / 2 >= image.shape[0] * 0.36:
            continue
        tokens = set(re.sub(r"[^a-z ]", " ", word["text"].lower()).split())
        if "date" in tokens:
            centers["_date_column"].append(word["x"] + word["w"] // 2)
        if "signature" in tokens or (
            word["y"] + word["h"] / 2 < image.shape[0] * 0.16
            and word["x"] + word["w"] / 2 > image.shape[1] * 0.85
            and _visitor_column_key(word["text"]) is None
        ):
            centers["_signature_column"].append(word["x"] + word["w"] // 2)

    result = {key: sum(values) // len(values) for key, values in centers.items() if values}
    # "Organization / Purpose" is often written as a two-line merged header.
    # Treat the shared column as purpose, which is the populated business value.
    if "organization" in result and "purpose" in result:
        if abs(result["organization"] - result["purpose"]) < image.shape[1] * 0.06:
            result.pop("organization")
    header_y = max(
        (word["y"] + word["h"] // 2 for word in header_words),
        default=int(image.shape[0] * 0.2),
    )
    return result, header_y


def _normalise_visitor_contact(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    if len(digits) < 7:
        return None
    if len(digits) == 10:
        return f"{digits[:5]} {digits[5:]}"
    return re.sub(r"\s+", " ", value).strip()


def _normalise_visitor_date(value: str) -> str | None:
    match = re.search(r"(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2,4})", value)
    if not match:
        return None
    year = int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return date(year, int(match.group(2)), int(match.group(1))).isoformat()
    except ValueError:
        return None


def _visitor_words(data: dict) -> list[dict]:
    return _attendance_words(data)


def _extract_visitor_records(image, ocr_data: dict, header_ocr_data: dict | None = None) -> list[dict]:
    """Rebuild visitor rows from OCR coordinates instead of returning OCR lines."""
    words = _visitor_words(ocr_data)
    if not words:
        return []

    register_date = next(
        (parsed for word in words if (parsed := _normalise_visitor_date(word["text"]))),
        None,
    )
    header_words = _visitor_words(header_ocr_data) if header_ocr_data else words
    detected_centers, header_y = _visitor_header_centers(header_words, image)

    width = image.shape[1]
    centers = detected_centers
    if not set(centers).intersection(_VISITOR_COLUMNS):
        return []
    ordered_columns = sorted(centers, key=centers.get)
    if len(ordered_columns) < 2:
        return []
    boundaries = []
    for left, right in zip(ordered_columns, ordered_columns[1:]):
        boundaries.append((centers[left] + centers[right]) // 2)
    boundaries.insert(0, max(0, centers[ordered_columns[0]] - (boundaries[0] - centers[ordered_columns[0]])))
    boundaries.append(min(width, centers[ordered_columns[-1]] + (centers[ordered_columns[-1]] - boundaries[-1])))
    column_bounds = {
        key: (boundaries[index], boundaries[index + 1])
        for index, key in enumerate(ordered_columns)
    }

    row_words = [
        word for word in words
        if (word["y"] + word["h"] // 2) > header_y + max(20, int(image.shape[0] * 0.025))
        and _normalise_visitor_date(word["text"]) is None
    ]
    row_words.sort(key=lambda word: word["y"] + word["h"] // 2)
    median_height = sorted(word["h"] for word in row_words)[len(row_words) // 2] if row_words else 20
    # OCR boxes can be tall on handwritten pages. A 1.5x tolerance merges
    # adjacent ruled rows; keep the threshold below one median text height.
    row_tolerance = max(18, median_height * 0.75)
    rows: list[list[dict]] = []
    row_centers: list[float] = []
    for word in row_words:
        center_y = word["y"] + word["h"] / 2
        nearest = next(
            (index for index, row_y in enumerate(row_centers) if abs(center_y - row_y) <= row_tolerance),
            None,
        )
        if nearest is None:
            rows.append([word])
            row_centers.append(center_y)
        else:
            rows[nearest].append(word)
            row_centers[nearest] = sum(item["y"] + item["h"] / 2 for item in rows[nearest]) / len(rows[nearest])

    records = []
    ordered_rows = sorted(rows, key=lambda group: min(word["y"] for word in group))
    row_y_centers = [
        sorted(word["y"] + word["h"] / 2 for word in row)[len(row) // 2]
        for row in ordered_rows
    ]
    for row_index, row in enumerate(ordered_rows):
        columns: dict[str, list[str]] = {key: [] for key in _VISITOR_COLUMNS}
        for word in sorted(row, key=lambda item: item["x"]):
            center_x = word["x"] + word["w"] // 2
            key = next((name for name, (left, right) in column_bounds.items() if left <= center_x < right), None)
            if key in columns:
                columns[key].append(word["text"])
        name = " ".join(columns["visitor_name"]).strip(" |,.;:")
        purpose = " ".join(columns["purpose"]).strip(" |,.;:")
        contact = _normalise_visitor_contact(" ".join(columns["contact_number"]))
        time_in = _normalise_time(" ".join(columns["time_in"]))
        time_out = _normalise_time(" ".join(columns["time_out"]))
        organization = " ".join(columns["organization"]).strip(" |,.;:") or None

        if isinstance(image, __import__("numpy").ndarray):
            center_y = row_y_centers[row_index]
            gaps = []
            if row_index:
                gaps.append(center_y - row_y_centers[row_index - 1])
            if row_index + 1 < len(row_y_centers):
                gaps.append(row_y_centers[row_index + 1] - center_y)
            half_height = max(30, int(min(gaps or [image.shape[0] * 0.12]) * 0.58))
            row_crop = image[max(0, int(center_y - half_height)):min(image.shape[0], int(center_y + half_height)), :]
            if row_crop.size:
                row_data = pytesseract.image_to_data(row_crop, config="--psm 6", output_type=Output.DICT)
                row_columns: dict[str, list[str]] = {key: [] for key in _VISITOR_COLUMNS}
                for word in _visitor_words(row_data):
                    center_x = word["x"] + word["w"] // 2
                    key = next((name for name, (left, right) in column_bounds.items() if left <= center_x < right), None)
                    if key in row_columns:
                        row_columns[key].append(word["text"])
                row_name = " ".join(row_columns["visitor_name"]).strip(" |,.;:")
                row_purpose = " ".join(row_columns["purpose"]).strip(" |,.;:")
                row_contact = _normalise_visitor_contact(" ".join(row_columns["contact_number"]))
                row_time_in = _normalise_time(" ".join(row_columns["time_in"]))
                row_time_out = _normalise_time(" ".join(row_columns["time_out"]))
                name = row_name or name
                purpose = row_purpose or purpose
                contact = row_contact or contact
                time_in = row_time_in or time_in
                time_out = row_time_out or time_out
        if len(name.strip()) < 3 or not any((purpose, contact, time_in, time_out)):
            continue
        if not re.search(r"[A-Za-z]{2,}", name):
            continue
        if any(token in name.casefold() for token in ("visitor", "name", "register", "date", "page")):
            continue

        if isinstance(image, __import__("numpy").ndarray):
            row_center = row_y_centers[row_index]
            row_top = 0 if row_index == 0 else int((row_y_centers[row_index - 1] + row_center) / 2)
            row_bottom = image.shape[0] if row_index == len(row_y_centers) - 1 else int((row_center + row_y_centers[row_index + 1]) / 2)
            for field in ("visitor_name", "purpose", "contact_number", "time_in", "time_out"):
                if field not in detected_centers:
                    continue
                current = {
                    "visitor_name": name,
                    "purpose": purpose,
                    "contact_number": contact,
                    "time_in": time_in,
                    "time_out": time_out,
                }[field]
                if current:
                    continue
                left, right = column_bounds[field]
                crop = image[max(0, row_top + 4):min(image.shape[0], row_bottom - 4), max(0, left + 4):min(image.shape[1], right - 4)]
                if crop.size == 0:
                    continue
                crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                recovered = pytesseract.image_to_string(crop, config="--psm 7").strip()
                if field == "contact_number":
                    contact = _normalise_visitor_contact(recovered)
                elif field == "time_in":
                    time_in = _normalise_time(recovered)
                elif field == "time_out":
                    time_out = _normalise_time(recovered)
                elif field == "visitor_name" and re.search(r"[A-Za-z]", recovered):
                    name = recovered.strip(" |,.;:")
                elif field == "purpose" and re.search(r"[A-Za-z]", recovered):
                    purpose = recovered.strip(" |,.;:")
        confidence_values = [word["confidence"] for word in row if word["confidence"] >= 0]
        records.append({
            "data": {
                "visit_date": register_date,
                "visitor_name": name,
                "organization": organization,
                "purpose": purpose or None,
                "contact_number": contact,
                "time_in": time_in,
                "time_out": time_out,
                "signature": None,
            },
            "confidence": round(sum(confidence_values) / len(confidence_values), 2) if confidence_values else None,
        })
    return records


def _ocr_cell(
    image, x1: int, y1: int, x2: int, y2: int, config: str = "--psm 7"
) -> tuple[str, float | None]:
    crop = image[max(0, y1 + 8):max(0, y2 - 8), max(0, x1 + 8):max(0, x2 - 8)]
    if crop.size == 0:
        return "", None
    crop = cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    cell_data = pytesseract.image_to_data(crop, config=config, output_type=Output.DICT)
    words = []
    confidences = []
    for index, value in enumerate(cell_data.get("text", [])):
        value = value.strip()
        if not value:
            continue
        words.append(value)
        try:
            confidence = float(cell_data["conf"][index])
        except (KeyError, TypeError, ValueError):
            continue
        if confidence >= 0:
            confidences.append(confidence)
    return " ".join(words), (
        sum(confidences) / len(confidences) if confidences else None
    )


def _deskew_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    points = cv2.findNonZero(binary)
    if points is None:
        return image
    angle = cv2.minAreaRect(points)[-1]
    if angle < -45:
        angle += 90
    if abs(angle) < 0.5 or abs(angle) > 15:
        return image
    height, width = image.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
    return cv2.warpAffine(
        image, matrix, (width, height), borderValue=(255, 255, 255)
    )


def _table_boundaries(image) -> tuple[list[int], list[int]]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)[1]
    height, width = gray.shape
    horizontal = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (max(40, width // 20), 1)),
    )
    vertical = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(40, height // 15))),
    )

    def positions(mask, minimum_size, axis):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        values = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if axis == "x" and w > 20:
                continue
            if (h if axis == "x" else w) >= minimum_size:
                values.append(x if axis == "x" else y)
        values.sort()
        merged = []
        for value in values:
            if not merged or value - merged[-1] > 12:
                merged.append(value)
        return merged

    ys = positions(horizontal, width // 3, "y")
    xs = positions(vertical, height // 4, "x")
    if xs and xs[0] > 20:
        xs.insert(0, 0)
    if xs and xs[-1] < width - 20:
        xs.append(width - 1)
    return xs, ys


def _normalise_invoice(value: str) -> str:
    match = re.search(r"p\s*c\s*h\s*[^0-9a-z]*([0-9oOlIi]{3,})", value, re.IGNORECASE)
    if not match:
        return value.replace(" ", "")
    number = match.group(1).translate(str.maketrans({
        "o": "0", "O": "0", "l": "1", "L": "1", "i": "1", "I": "1",
    }))
    return f"PCH-{number}"


def _money(value: str) -> Decimal | None:
    cleaned = re.sub(r"[^0-9.]", "", value)
    if cleaned.count(".") > 1:
        first, *rest = cleaned.split(".")
        cleaned = first + "." + "".join(rest)
    try:
        parsed = Decimal(cleaned) if cleaned else None
        return parsed if parsed and parsed > 0 else None
    except InvalidOperation:
        return None


def _normalise_purchase_text(value: str) -> str:
    value = re.sub(r"^[^A-Za-z0-9]+", "", value)
    return re.sub(r"\bPl\s+ug\b", "Plug", value, flags=re.IGNORECASE)


def _purchase_date(image) -> str | None:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(
        cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC),
        config="--psm 11",
    )
    match = re.search(r"\b(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})\b", text)
    if not match:
        return None
    try:
        return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
    except ValueError:
        return None


def _extract_purchase_records_grid(image) -> list[dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    xs, ys = _table_boundaries(image)
    date_value = _purchase_date(image)
    records = []
    if len(xs) >= 8 and len(ys) >= 7:
        for row in range(1, len(ys) - 1):
            cells = [
                _ocr_cell(
                    gray, xs[column], ys[row], xs[column + 1], ys[row + 1],
                    "--psm 6" if column in (2, 3) else "--psm 7",
                )
                for column in range(7)
            ]
            invoice = _normalise_invoice(cells[1][0])
            if not re.fullmatch(r"PCH-\d{3,}", invoice, re.IGNORECASE):
                continue
            quantity_match = re.search(r"\d+", cells[4][0])
            if not quantity_match:
                quantity_fallback = _ocr_cell(
                    gray, xs[4], ys[row], xs[5], ys[row + 1], "--psm 13"
                )[0]
                quantity_match = re.search(r"\d+", quantity_fallback)
            quantity = int(quantity_match.group()) if quantity_match else None
            unit_price = _money(cells[5][0])
            total_amount = _money(cells[6][0])
            if quantity and unit_price is not None and total_amount is not None:
                if abs(unit_price * quantity - total_amount) > Decimal("0.02"):
                    total_amount = (unit_price * quantity).quantize(Decimal("0.01"))
            elif quantity and total_amount is not None:
                derived_unit = (total_amount / quantity).quantize(Decimal("0.01"))
                if unit_price is None or abs(unit_price * quantity - total_amount) > Decimal("0.02"):
                    unit_price = derived_unit
            if quantity and unit_price is not None and (
                total_amount is None or abs(unit_price * quantity - total_amount) > Decimal("0.02")
            ):
                total_amount = (unit_price * quantity).quantize(Decimal("0.01"))
            values = {
                "invoice_number": invoice.upper(),
                "supplier_name": _normalise_purchase_text(cells[2][0]).replace("farts", "Parts"),
                "spare_part": _normalise_purchase_text(cells[3][0]),
                "quantity": quantity,
                "unit_price": str(unit_price) if unit_price is not None else None,
                "total_amount": str(total_amount) if total_amount is not None else None,
                "purchase_date": date_value,
                "payment_status": "Pending",
                "original_ocr_text": " ".join(cell[0] for cell in cells[1:]),
                "field_confidence": {
                    field: round(cells[index][1], 2) if cells[index][1] is not None else None
                    for field, index in (
                        ("invoice_number", 1),
                        ("supplier_name", 2),
                        ("spare_part", 3),
                        ("quantity", 4),
                        ("unit_price", 5),
                        ("total_amount", 6),
                    )
                },
            }
            confidence_values = [value for _, value in cells[1:] if value is not None]
            records.append({
                "data": values,
                "confidence": round(sum(confidence_values) / len(confidence_values), 2)
                if confidence_values else None,
            })
    return records


_HEADER_ALIASES = {
    "invoice_number": ("invoice", "bill", "voucher", "invoice no", "bill no"),
    "supplier_name": ("supplier", "vendor", "party", "supplier name", "vendor name"),
    "spare_part": ("item", "product", "spare", "part", "description"),
    "quantity": ("qty", "quantity", "units"),
    "unit_price": ("rate", "unit price", "price", "unit cost"),
    "total_amount": ("amount", "total", "net amount", "total amount", "value"),
    "purchase_date": ("date", "bill date", "purchase date"),
}
_HEADER_WORDS = {
    word
    for aliases in _HEADER_ALIASES.values()
    for alias in aliases
    for word in alias.split()
}


def _normalise_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _ocr_words(image) -> list[dict]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    data = pytesseract.image_to_data(scaled, config="--psm 4", output_type=Output.DICT)
    words = []
    for index, value in enumerate(data.get("text", [])):
        value = value.strip()
        if not value:
            continue
        try:
            confidence = float(data["conf"][index])
            x, y, width, height = (
                int(data[field][index]) for field in ("left", "top", "width", "height")
            )
        except (KeyError, TypeError, ValueError):
            continue
        if confidence < 0:
            continue
        words.append({
            "text": value,
            "normalized": _normalise_token(value),
            "x": (x + width / 2) / 2,
            "left": x / 2,
            "right": (x + width) / 2,
            "y": (y + height / 2) / 2,
            "confidence": confidence,
            "bottom": (y + height) / 2,
        })
    return words


def _header_columns(words: list[dict]) -> tuple[dict[str, float], float | None]:
    def field_for_token(token: str) -> str | None:
        exact = [
            field for field, aliases in _HEADER_ALIASES.items()
            if token in {_normalise_token(alias.split()[0]) for alias in aliases}
        ]
        if exact:
            return exact[0]
        best_field = None
        best_score = 0.0
        for field, aliases in _HEADER_ALIASES.items():
            for alias in aliases:
                candidate = _normalise_token(alias.split()[0])
                if len(token) >= 4:
                    score = SequenceMatcher(None, token, candidate).ratio()
                    if score > best_score:
                        best_field, best_score = field, score
        return best_field if best_score >= 0.62 else None

    candidates = [
        word for word in words
        if word["normalized"] in _HEADER_WORDS
        or field_for_token(word["normalized"]) is not None
    ]
    clusters: list[list[dict]] = []
    for word in sorted(candidates, key=lambda item: item["y"]):
        cluster = next(
            (group for group in clusters if abs(group[0]["y"] - word["y"]) <= 55),
            None,
        )
        if cluster is None:
            clusters.append([word])
        else:
            cluster.append(word)
    best: list[dict] = []
    for cluster in clusters:
        fields = {}
        for word in cluster:
            field = field_for_token(word["normalized"])
            if re.search(r"qty|quant", word["text"], re.IGNORECASE):
                fields.setdefault("quantity", word)
            if field:
                fields.setdefault(field, word)
            for field in (field,) if field else ():
                fields.setdefault(field, word)
        if len(fields) > len(best):
            best = list(fields.values())
    columns = {}
    for word in best:
        field = field_for_token(word["normalized"])
        if field:
            columns.setdefault(field, word["x"])
        if re.search(r"qty|quant", word["text"], re.IGNORECASE):
            columns["quantity"] = word["right"]
        if re.search(r"part.*qty", word["text"], re.IGNORECASE):
            columns["spare_part"] = word["left"]
    return columns, (max(word["y"] for word in best) if best else None)


def _row_groups(words: list[dict], header_y: float) -> list[list[dict]]:
    invoice_words = [
        word for word in words
        if word["y"] > header_y
        and re.search(r"(?:pch|pch-|bill|inv|invoice)", word["normalized"], re.IGNORECASE)
    ]
    groups: list[list[dict]] = []
    for invoice in sorted(invoice_words, key=lambda item: item["y"]):
        group = next(
            (existing for existing in groups if abs(existing[0]["y"] - invoice["y"]) <= 45),
            None,
        )
        if group is None:
            groups.append([invoice])
        else:
            group.append(invoice)
    return groups


def _field_for_x(x: float, columns: dict[str, float]) -> str | None:
    ordered = sorted(columns.items(), key=lambda item: item[1])
    if not ordered:
        return None
    distances = [abs(x - position) for _, position in ordered]
    return ordered[distances.index(min(distances))][0]


def _extract_purchase_records_dynamic(image) -> list[dict]:
    words = _ocr_words(image)
    columns, header_y = _header_columns(words)
    required = {"invoice_number", "supplier_name", "spare_part", "quantity", "unit_price", "total_amount"}
    if header_y is None or not required.issubset(columns):
        return []
    groups = _row_groups(words, header_y)
    if not groups:
        return []
    records = []
    for group in groups:
        center_y = sum(word["y"] for word in group) / len(group)
        row_words = [
            word for word in words
            if header_y < word["y"] < center_y + 45
            and abs(word["y"] - center_y) <= 45
        ]
        values: dict[str, list[dict]] = defaultdict(list)
        for word in row_words:
            field = _field_for_x(word["x"], columns)
            if field:
                values[field].append(word)
        invoice_text = " ".join(word["text"] for word in values["invoice_number"])
        invoice = _normalise_invoice(invoice_text)
        if not re.fullmatch(r"PCH-\d{3,}", invoice, re.IGNORECASE):
            continue
        quantity_text = " ".join(word["text"] for word in values["quantity"])
        quantity_match = re.search(r"\d+", quantity_text)
        quantity = int(quantity_match.group()) if quantity_match else None
        unit_price = _money(" ".join(word["text"] for word in values["unit_price"]))
        total_amount = _money(" ".join(word["text"] for word in values["total_amount"]))
        if quantity and unit_price is not None and total_amount is not None:
            if abs(unit_price * quantity - total_amount) > Decimal("0.02"):
                total_amount = (unit_price * quantity).quantize(Decimal("0.01"))
        supplier = _normalise_purchase_text(" ".join(word["text"] for word in values["supplier_name"]))
        spare_part = _normalise_purchase_text(" ".join(word["text"] for word in values["spare_part"]))
        row_confidences = [word["confidence"] for word in row_words]
        fields_confidence = {
            field: round(sum(word["confidence"] for word in field_words) / len(field_words), 2)
            if field_words else None
            for field, field_words in values.items()
        }
        records.append({
            "data": {
                "invoice_number": invoice.upper(),
                "supplier_name": supplier,
                "spare_part": spare_part,
                "quantity": quantity,
                "unit_price": str(unit_price) if unit_price is not None else None,
                "total_amount": str(total_amount) if total_amount is not None else None,
                "purchase_date": _purchase_date(image),
                "payment_status": "Pending",
                "original_ocr_text": " ".join(word["text"] for word in row_words),
                "field_confidence": fields_confidence,
            },
            "confidence": round(sum(row_confidences) / len(row_confidences), 2)
            if row_confidences else None,
        })
    return _finalize_purchase_records(records)


def _finalize_purchase_records(records: list[dict]) -> list[dict]:
    invoices = [
        item["data"].get("invoice_number")
        for item in records
        if item["data"].get("invoice_number")
    ]
    for item in records:
        data = item["data"]
        warnings = []
        for field in ("invoice_number", "supplier_name", "spare_part", "quantity", "unit_price", "total_amount"):
            if data.get(field) in (None, ""):
                warnings.append(f"Missing {field.replace('_', ' ')}")
        if data.get("invoice_number") in invoices and invoices.count(data["invoice_number"]) > 1:
            warnings.append("Duplicate invoice number detected")
        if data.get("quantity") and data.get("unit_price") and data.get("total_amount"):
            expected = (Decimal(str(data["quantity"])) * Decimal(str(data["unit_price"]))).quantize(Decimal("0.01"))
            if abs(expected - Decimal(str(data["total_amount"]))) > Decimal("0.02"):
                warnings.append("Quantity multiplied by unit price does not match total amount")
        if not re.fullmatch(r"PCH-\d{3,}", str(data.get("invoice_number", "")), re.IGNORECASE):
            warnings.append("Invoice number is uncertain")
        data["extraction_warnings"] = warnings
    return records


def _extract_purchase_records(image) -> list[dict]:
    grid = _extract_purchase_records_grid(image)
    dynamic = _extract_purchase_records_dynamic(image)
    valid_dynamic = [
        item for item in dynamic
        if item["data"].get("supplier_name")
        and item["data"].get("spare_part")
        and item["data"].get("invoice_number")
    ]
    if not grid or len(valid_dynamic) >= len(grid):
        return _finalize_purchase_records(valid_dynamic)
    return _finalize_purchase_records(grid)


def export_records(document: DocumentUpload, db: Session) -> bytes:
    records = db.scalars(
        select(DocumentExtractedRecord)
        .where(DocumentExtractedRecord.document_id == document.id)
        .order_by(DocumentExtractedRecord.row_number)
    ).all()
    rows = []
    for record in records:
        try:
            data = json.loads(record.extracted_data)
        except json.JSONDecodeError:
            data = {"raw_text": record.extracted_data}
        if document.register_type == "purchases":
            data = {
                key: value for key, value in data.items()
                if key not in {"original_ocr_text", "field_confidence", "extraction_warnings"}
            }
        rows.append(data)
    frame = pd.DataFrame(rows or [{"raw_text": ""}])
    output = __import__("io").BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Extracted Records")
        worksheet = writer.book["Extracted Records"]
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
    return output.getvalue()


REGISTER_MODELS = {
    "employees": Employee,
    "attendance": Attendance,
    "visitors": Visitor,
    "suppliers": Supplier,
    "spare_parts": SparePart,
    "purchases": Purchase,
    "spare_sales": SpareSale,
    "customer_enquiries": CustomerEnquiry,
}
REGISTER_SCHEMAS = {
    "employees": EmployeeCreate,
    "attendance": AttendanceCreate,
    "visitors": VisitorCreate,
    "suppliers": SupplierCreate,
    "spare_parts": SparePartCreate,
    "purchases": PurchaseCreate,
    "spare_sales": SpareSaleCreate,
    "customer_enquiries": EnquiryCreate,
}


def insert_approved_records(document: DocumentUpload, records: list[DocumentExtractedRecord], db: Session) -> int:
    model = REGISTER_MODELS.get(document.register_type)
    schema = REGISTER_SCHEMAS.get(document.register_type)
    if model is None or schema is None:
        raise HTTPException(status_code=422, detail="Unsupported target register")
    if document.status in {"Completed", "Inserted"} or records and all(record.status == "Inserted" for record in records):
        return 0
    if any(record.status == "Inserted" for record in records):
        raise HTTPException(status_code=409, detail="Document has partially inserted records and requires administrative review")

    pending: list[tuple[DocumentExtractedRecord, dict]] = []
    for record in records:
        if record.status != "Approved":
            raise HTTPException(status_code=409, detail="All records must be approved before insertion")
        try:
            data = json.loads(record.extracted_data)
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=422, detail=f"Record {record.row_number} is not valid JSON") from error
        try:
            if document.register_type == "purchases":
                values = _purchase_values(data, db)
            elif document.register_type == "attendance":
                values = _attendance_values(data, db)
            elif document.register_type == "visitors":
                values = _visitor_values(data)
            else:
                values = schema.model_validate(data).model_dump()
        except ValueError as error:
            record.validation_error = str(error)
            raise HTTPException(
                status_code=422,
                detail=f"Record {record.row_number} failed validation: {error}",
            ) from error
        duplicate = _find_duplicate(model, values, db)
        if duplicate:
            raise HTTPException(status_code=409, detail=f"Record {record.row_number} already exists")
        duplicate_pending = any(
            all(existing_values.get(key) == values.get(key) for key in keys)
            for _, existing_values in pending
        ) if (keys := {
            Purchase: ("supplier_id", "invoice_number"),
            Visitor: ("visitor_name", "entry_date", "entry_time"),
        }.get(model)) else False
        if duplicate_pending:
            raise HTTPException(status_code=409, detail=f"Record {record.row_number} duplicates another approved row")
        pending.append((record, values))

    inserted = 0
    try:
        for record, values in pending:
            if document.register_type == "purchases":
                part = db.scalar(
                    select(SparePart).where(SparePart.id == values["spare_part_id"]).with_for_update()
                )
                if part is None:
                    raise HTTPException(status_code=422, detail=f"Record {record.row_number} spare part not found")
                part.available_quantity += values["quantity"]
            db.add(model(**values))
            record.status = "Inserted"
            inserted += 1
        document.status = "Inserted"
        document.approved_row_count = inserted
        db.commit()
    except (HTTPException, IntegrityError):
        db.rollback()
        raise
    return inserted


def _purchase_values(data: dict, db: Session) -> dict:
    supplier_name = str(data.get("supplier_name", "")).strip()
    spare_part_name = str(data.get("spare_part", data.get("spare_part_name", ""))).strip()
    if not supplier_name or not spare_part_name:
        raise ValueError("supplier_name and spare_part are required")
    if not data.get("purchase_date"):
        raise ValueError(
            "purchase_date is required before approval; enter the purchase date manually"
        )
    supplier = db.scalar(
        select(Supplier).where(func.lower(Supplier.supplier_name) == supplier_name.lower())
    )
    spare_part = db.scalar(
        select(SparePart).where(func.lower(SparePart.part_name) == spare_part_name.lower())
    )
    missing_master_data = []
    if supplier is None:
        missing_master_data.append(f"supplier '{supplier_name}'")
    if spare_part is None:
        missing_master_data.append(f"spare part '{spare_part_name}'")
    if missing_master_data:
        raise ValueError(
            "Missing master data: " + ", ".join(missing_master_data) +
            ". Create the required master records before approval."
        )
    values = dict(data)
    values["supplier_id"] = supplier.id
    values["spare_part_id"] = spare_part.id
    values.pop("supplier_name", None)
    values.pop("spare_part", None)
    values.pop("spare_part_name", None)
    purchase = PurchaseCreate.model_validate(values)
    if purchase.quantity * purchase.unit_price != purchase.total_amount:
        raise ValueError("quantity multiplied by unit_price must equal total_amount")
    return purchase.model_dump()


def _attendance_values(data: dict, db: Session) -> dict:
    employee_code = str(data.get("employee_code", "")).strip()
    employee_name = str(data.get("employee_name", "")).strip()
    if not employee_code:
        raise ValueError("employee_code is required")
    if not employee_name:
        raise ValueError("employee_name is required")
    employee = db.scalar(
        select(Employee).where(func.lower(Employee.employee_code) == employee_code.lower())
    )
    values = dict(data)
    values["employee_id"] = employee.id if employee else None
    values["employee_code"] = employee.employee_code if employee else employee_code
    values["employee_name"] = employee.full_name if employee else employee_name
    values.pop("original_ocr_text", None)
    values.pop("extraction_warnings", None)
    return AttendanceCreate.model_validate(values).model_dump()


def _visitor_values(data: dict) -> dict:
    values = dict(data)
    values["entry_date"] = values.get("entry_date") or values.get("visit_date")
    values["company"] = values.get("company") or values.get("organization")
    values["entry_time"] = values.get("entry_time") or values.get("time_in")
    values["exit_time"] = values.get("exit_time") or values.get("time_out")
    for field in ("visit_date", "organization", "time_in", "time_out", "signature", "confidence"):
        values.pop(field, None)
    return VisitorCreate.model_validate(values).model_dump()


def validate_extracted_record(document: DocumentUpload, record: DocumentExtractedRecord, db: Session) -> None:
    try:
        data = json.loads(record.extracted_data)
        if document.register_type == "purchases":
            _purchase_values(data, db)
        elif document.register_type == "attendance":
            _attendance_values(data, db)
        elif document.register_type == "visitors":
            _visitor_values(data)
        else:
            REGISTER_SCHEMAS[document.register_type].model_validate(data)
    except (KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
        record.validation_error = str(error)
        raise HTTPException(
            status_code=422,
            detail=f"Record {record.row_number} failed validation: {error}",
        ) from error


def _find_duplicate(model, values: dict, db: Session):
    keys = {
        Employee: ("employee_code",),
        Attendance: ("employee_code", "attendance_date"),
        Supplier: ("supplier_name",),
        SparePart: ("part_code",),
        Purchase: ("supplier_id", "invoice_number"),
        Visitor: ("visitor_name", "entry_date", "entry_time"),
    }.get(model)
    if not keys or any(key not in values for key in keys):
        return None
    return db.scalar(select(model).where(*(getattr(model, key) == values[key] for key in keys)))
