from datetime import datetime

from app.schemas.common import ORMModel
from pydantic import BaseModel, Field


class DocumentResponse(ORMModel):
    id: int
    original_filename: str
    register_type: str
    status: str
    extracted_row_count: int
    approved_row_count: int
    processing_error: str | None
    created_at: datetime
    inserted_row_count: int = 0


class DocumentPage(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int


class ReviewRecord(ORMModel):
    id: int
    row_number: int
    extracted_data: str
    confidence: float | None
    validation_error: str | None
    status: str


class ReviewUpdate(BaseModel):
    extracted_data: str = Field(min_length=2)
    status: str = Field(default="Review Required", pattern="^(Review Required|Rejected)$")
