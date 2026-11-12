"""Create initial SmartLedger schema.

Revision ID: 0001_initial_schema
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="Staff"),
        *_timestamps(),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_code", sa.String(50), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("department", sa.String(100)),
        sa.Column("designation", sa.String(100)),
        sa.Column("branch", sa.String(100)),
        sa.Column("contact_number", sa.String(30)),
        sa.Column("joining_date", sa.Date()),
        sa.Column("employment_status", sa.String(30), nullable=False, server_default="Active"),
        *_timestamps(),
        sa.UniqueConstraint("employee_code", name="uq_employees_employee_code"),
    )
    op.create_index("ix_employees_name", "employees", ["full_name"])
    op.create_index("ix_employees_branch", "employees", ["branch"])

    op.create_table(
        "visitors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visitor_name", sa.String(150), nullable=False),
        sa.Column("contact_number", sa.String(30)),
        sa.Column("company", sa.String(150)),
        sa.Column("purpose", sa.Text()),
        sa.Column("person_to_meet", sa.String(150)),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("entry_time", sa.String(10)),
        sa.Column("exit_time", sa.String(10)),
        sa.Column("remarks", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_visitors_entry_date", "visitors", ["entry_date"])

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_name", sa.String(150), nullable=False),
        sa.Column("contact_number", sa.String(30)),
        sa.Column("email", sa.String(255)),
        *_timestamps(),
        sa.UniqueConstraint("supplier_name", name="uq_suppliers_supplier_name"),
    )
    op.create_table(
        "spare_parts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("part_code", sa.String(50), nullable=False),
        sa.Column("part_name", sa.String(150), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("description", sa.Text()),
        sa.Column("available_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="SET NULL")),
        sa.Column("minimum_stock_level", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("part_code", name="uq_spare_parts_part_code"),
        sa.CheckConstraint("available_quantity >= 0", name="ck_spare_parts_quantity_nonnegative"),
        sa.CheckConstraint("minimum_stock_level >= 0", name="ck_spare_parts_minimum_nonnegative"),
    )
    op.create_index("ix_spare_parts_category", "spare_parts", ["category"])

    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("in_time", sa.String(10)),
        sa.Column("out_time", sa.String(10)),
        sa.Column("remarks", sa.Text()),
        *_timestamps(),
        sa.UniqueConstraint("employee_id", "attendance_date", name="uq_attendance_employee_date"),
    )
    op.create_index("ix_attendance_date", "attendance", ["attendance_date"])
    op.create_index("ix_attendance_status", "attendance", ["status"])

    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("spare_part_id", sa.Integer(), sa.ForeignKey("spare_parts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("payment_status", sa.String(30), nullable=False, server_default="Pending"),
        *_timestamps(),
        sa.UniqueConstraint("supplier_id", "invoice_number", name="uq_purchases_supplier_invoice"),
        sa.CheckConstraint("quantity > 0", name="ck_purchases_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_purchases_unit_price_nonnegative"),
        sa.CheckConstraint("total_amount >= 0", name="ck_purchases_total_nonnegative"),
    )
    op.create_index("ix_purchases_date", "purchases", ["purchase_date"])

    op.create_table(
        "spare_sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(150), nullable=False),
        sa.Column("spare_part_id", sa.Integer(), sa.ForeignKey("spare_parts.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity_sold", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("technician_name", sa.String(150)),
        sa.Column("remarks", sa.Text()),
        *_timestamps(),
        sa.CheckConstraint("quantity_sold > 0", name="ck_spare_sales_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_spare_sales_unit_price_nonnegative"),
        sa.CheckConstraint("total_amount >= 0", name="ck_spare_sales_total_nonnegative"),
    )
    op.create_index("ix_spare_sales_date", "spare_sales", ["sale_date"])

    op.create_table(
        "customer_enquiries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(150), nullable=False),
        sa.Column("phone_number", sa.String(30)),
        sa.Column("email", sa.String(255)),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("enquiry_date", sa.Date(), nullable=False),
        sa.Column("assigned_employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(30), nullable=False, server_default="New"),
        sa.Column("remarks", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_customer_enquiries_status", "customer_enquiries", ["status"])

    op.create_table(
        "document_uploads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("register_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Uploaded"),
        sa.Column("extracted_row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_error", sa.Text()),
        *_timestamps(),
        sa.UniqueConstraint("stored_filename", name="uq_document_uploads_stored_filename"),
    )
    op.create_index("ix_document_uploads_status", "document_uploads", ["status"])
    op.create_index("ix_document_uploads_register_type", "document_uploads", ["register_type"])

    op.create_table(
        "document_extracted_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("document_uploads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("extracted_data", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 2)),
        sa.Column("validation_error", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False, server_default="Review Required"),
        *_timestamps(),
    )
    op.create_index("ix_document_records_status", "document_extracted_records", ["status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.Integer()),
        sa.Column("details", sa.Text()),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("document_extracted_records")
    op.drop_table("document_uploads")
    op.drop_table("customer_enquiries")
    op.drop_table("spare_sales")
    op.drop_table("purchases")
    op.drop_table("attendance")
    op.drop_table("spare_parts")
    op.drop_table("suppliers")
    op.drop_table("visitors")
    op.drop_table("employees")
    op.drop_table("users")
