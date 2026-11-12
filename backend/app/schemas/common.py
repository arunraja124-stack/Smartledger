from datetime import date, datetime
from decimal import Decimal
import re
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="Staff", pattern="^(Admin|Staff)$")
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Full name is required")
        return value

class UserAdminUpdate(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    role: str | None = Field(default=None, pattern="^(Admin|Staff)$")
    is_active: bool | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Full name is required")
        return value


class PasswordReset(BaseModel):
    password: str | None = Field(default=None, min_length=8, max_length=128)


class TemporaryPassword(BaseModel):
    temporary_password: str


class UserResponse(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmployeeBase(BaseModel):
    employee_code: str = Field(min_length=1, max_length=50)
    full_name: str = Field(min_length=1, max_length=150)
    department: str | None = None
    designation: str | None = None
    branch: str | None = None
    contact_number: str | None = None
    joining_date: date | None = None
    employment_status: str = "Active"


class EmployeeCreate(EmployeeBase): pass
class EmployeeUpdate(EmployeeBase): pass
class EmployeeResponse(EmployeeBase, ORMModel):
    id: int
    created_at: datetime


class AttendanceCreate(BaseModel):
    employee_id: int | None = None
    employee_code: str = Field(min_length=1, max_length=50)
    employee_name: str = Field(min_length=1, max_length=150)
    attendance_date: date
    status: str = Field(pattern="^(Present|Absent|Leave|Half Day)$")
    in_time: str | None = None
    out_time: str | None = None
    remarks: str | None = None


class AttendanceResponse(AttendanceCreate, ORMModel):
    id: int
    created_at: datetime


class VisitorCreate(BaseModel):
    visitor_name: str = Field(min_length=1, max_length=150)
    contact_number: str | None = None
    company: str | None = None
    purpose: str | None = None
    person_to_meet: str | None = None
    entry_date: date
    entry_time: str | None = None
    exit_time: str | None = None
    remarks: str | None = None


class VisitorResponse(VisitorCreate, ORMModel):
    id: int
    created_at: datetime


class SupplierCreate(BaseModel):
    supplier_name: str = Field(min_length=1, max_length=150)
    contact_number: str | None = None
    email: str | None = None


class SupplierResponse(SupplierCreate, ORMModel):
    id: int
    created_at: datetime


class SparePartCreate(BaseModel):
    part_code: str = Field(min_length=1, max_length=50)
    part_name: str = Field(min_length=1, max_length=150)
    category: str | None = None
    description: str | None = None
    available_quantity: int = Field(default=0, ge=0)
    unit_price: Decimal = Field(default=0, ge=0)
    supplier_id: int | None = None
    minimum_stock_level: int = Field(default=0, ge=0)


class SparePartResponse(SparePartCreate, ORMModel):
    id: int
    created_at: datetime


class PurchaseCreate(BaseModel):
    supplier_id: int
    spare_part_id: int
    invoice_number: str = Field(min_length=1, max_length=100)
    purchase_date: date
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    payment_status: str = "Pending"


class PurchaseResponse(PurchaseCreate, ORMModel):
    id: int
    created_at: datetime


class SpareSaleCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    spare_part_id: int
    quantity_sold: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    total_amount: Decimal = Field(ge=0)
    sale_date: date
    technician_name: str | None = None
    remarks: str | None = None


class SpareSaleResponse(SpareSaleCreate, ORMModel):
    id: int
    created_at: datetime


class EnquiryCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    phone_number: str | None = None
    email: str | None = None
    subject: str = Field(min_length=1, max_length=200)
    description: str | None = None
    enquiry_date: date
    assigned_employee_id: int | None = None
    status: str = Field(default="New", pattern="^(New|In Progress|Follow-up|Converted|Closed)$")
    remarks: str | None = None


class EnquiryResponse(EnquiryCreate, ORMModel):
    id: int
    created_at: datetime
