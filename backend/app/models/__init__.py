from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (Index("ix_users_role", "role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="Staff")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Employee(TimestampMixin, Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("employee_code", name="uq_employees_employee_code"),
        Index("ix_employees_name", "full_name"),
        Index("ix_employees_branch", "branch"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(50))
    full_name: Mapped[str] = mapped_column(String(150))
    department: Mapped[str | None] = mapped_column(String(100))
    designation: Mapped[str | None] = mapped_column(String(100))
    branch: Mapped[str | None] = mapped_column(String(100))
    contact_number: Mapped[str | None] = mapped_column(String(30))
    joining_date: Mapped[date | None] = mapped_column(Date)
    employment_status: Mapped[str] = mapped_column(String(30), default="Active")
    attendance: Mapped[list["Attendance"]] = relationship(back_populates="employee")
    enquiries: Mapped[list["CustomerEnquiry"]] = relationship(back_populates="assigned_employee")


class Attendance(TimestampMixin, Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
        UniqueConstraint("employee_code", "attendance_date", name="uq_attendance_code_date"),
        Index("ix_attendance_date", "attendance_date"),
        Index("ix_attendance_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))
    employee_code: Mapped[str] = mapped_column(String(50))
    employee_name: Mapped[str] = mapped_column(String(150))
    attendance_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))
    in_time: Mapped[str | None] = mapped_column(String(10))
    out_time: Mapped[str | None] = mapped_column(String(10))
    remarks: Mapped[str | None] = mapped_column(Text)
    employee: Mapped[Employee | None] = relationship(back_populates="attendance")


class Visitor(TimestampMixin, Base):
    __tablename__ = "visitors"
    __table_args__ = (Index("ix_visitors_entry_date", "entry_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    visitor_name: Mapped[str] = mapped_column(String(150))
    contact_number: Mapped[str | None] = mapped_column(String(30))
    company: Mapped[str | None] = mapped_column(String(150))
    purpose: Mapped[str | None] = mapped_column(Text)
    person_to_meet: Mapped[str | None] = mapped_column(String(150))
    entry_date: Mapped[date] = mapped_column(Date)
    entry_time: Mapped[str | None] = mapped_column(String(10))
    exit_time: Mapped[str | None] = mapped_column(String(10))
    remarks: Mapped[str | None] = mapped_column(Text)


class Supplier(TimestampMixin, Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(150), unique=True)
    contact_number: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="supplier")
    spare_parts: Mapped[list["SparePart"]] = relationship(back_populates="supplier")


class SparePart(TimestampMixin, Base):
    __tablename__ = "spare_parts"
    __table_args__ = (
        UniqueConstraint("part_code", name="uq_spare_parts_part_code"),
        Index("ix_spare_parts_category", "category"),
        CheckConstraint("available_quantity >= 0", name="ck_spare_parts_quantity_nonnegative"),
        CheckConstraint("minimum_stock_level >= 0", name="ck_spare_parts_minimum_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    part_code: Mapped[str] = mapped_column(String(50))
    part_name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"))
    minimum_stock_level: Mapped[int] = mapped_column(Integer, default=0)
    supplier: Mapped[Supplier | None] = relationship(back_populates="spare_parts")
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="spare_part")
    sales: Mapped[list["SpareSale"]] = relationship(back_populates="spare_part")


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"
    __table_args__ = (
        UniqueConstraint("supplier_id", "invoice_number", name="uq_purchases_supplier_invoice"),
        Index("ix_purchases_date", "purchase_date"),
        CheckConstraint("quantity > 0", name="ck_purchases_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_purchases_unit_price_nonnegative"),
        CheckConstraint("total_amount >= 0", name="ck_purchases_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="RESTRICT"))
    spare_part_id: Mapped[int] = mapped_column(ForeignKey("spare_parts.id", ondelete="RESTRICT"))
    invoice_number: Mapped[str] = mapped_column(String(100))
    purchase_date: Mapped[date] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_status: Mapped[str] = mapped_column(String(30), default="Pending")
    supplier: Mapped[Supplier] = relationship(back_populates="purchases")
    spare_part: Mapped[SparePart] = relationship(back_populates="purchases")


class SpareSale(TimestampMixin, Base):
    __tablename__ = "spare_sales"
    __table_args__ = (
        Index("ix_spare_sales_date", "sale_date"),
        CheckConstraint("quantity_sold > 0", name="ck_spare_sales_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_spare_sales_unit_price_nonnegative"),
        CheckConstraint("total_amount >= 0", name="ck_spare_sales_total_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    spare_part_id: Mapped[int] = mapped_column(ForeignKey("spare_parts.id", ondelete="RESTRICT"))
    quantity_sold: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    sale_date: Mapped[date] = mapped_column(Date)
    technician_name: Mapped[str | None] = mapped_column(String(150))
    remarks: Mapped[str | None] = mapped_column(Text)
    spare_part: Mapped[SparePart] = relationship(back_populates="sales")


class CustomerEnquiry(TimestampMixin, Base):
    __tablename__ = "customer_enquiries"
    __table_args__ = (Index("ix_customer_enquiries_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    phone_number: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    enquiry_date: Mapped[date] = mapped_column(Date)
    assigned_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(30), default="New")
    remarks: Mapped[str | None] = mapped_column(Text)
    assigned_employee: Mapped[Employee | None] = relationship(back_populates="enquiries")


class DocumentUpload(TimestampMixin, Base):
    __tablename__ = "document_uploads"
    __table_args__ = (
        Index("ix_document_uploads_status", "status"),
        Index("ix_document_uploads_register_type", "register_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    register_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="Uploaded")
    extracted_row_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_row_count: Mapped[int] = mapped_column(Integer, default=0)
    processing_error: Mapped[str | None] = mapped_column(Text)
    extracted_records: Mapped[list["DocumentExtractedRecord"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentExtractedRecord(TimestampMixin, Base):
    __tablename__ = "document_extracted_records"
    __table_args__ = (Index("ix_document_records_status", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document_uploads.id", ondelete="CASCADE")
    )
    row_number: Mapped[int] = mapped_column(Integer)
    extracted_data: Mapped[str] = mapped_column(Text)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    validation_error: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Review Required")
    document: Mapped[DocumentUpload] = relationship(back_populates="extracted_records")


class AuditLog(TimestampMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(100))
    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
