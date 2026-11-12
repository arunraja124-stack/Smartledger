"""Allow attendance records without employee masters.

Revision ID: 0003_attendance_identity_snapshots
Revises: 0002_add_user_active_flag
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_attendance_snapshots"
down_revision = "0002_add_user_active_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("attendance")}
    if "employee_code" not in columns:
        op.add_column("attendance", sa.Column("employee_code", sa.String(length=50), nullable=True))
    if "employee_name" not in columns:
        op.add_column("attendance", sa.Column("employee_name", sa.String(length=150), nullable=True))
    inspector = sa.inspect(op.get_bind())
    employee_id_column = next(column for column in inspector.get_columns("attendance") if column["name"] == "employee_id")
    if employee_id_column["nullable"] is False:
        op.alter_column("attendance", "employee_id", existing_type=sa.Integer(), nullable=True)
    op.execute(
        """
        UPDATE attendance AS a
        INNER JOIN employees AS e ON e.id = a.employee_id
        SET a.employee_code = e.employee_code, a.employee_name = e.full_name
        """
    )
    inspector = sa.inspect(op.get_bind())
    for column in ("employee_code", "employee_name"):
        column_info = next(item for item in inspector.get_columns("attendance") if item["name"] == column)
        if column_info["nullable"]:
            op.alter_column(
                "attendance",
                column,
                existing_type=sa.String(length=50 if column == "employee_code" else 150),
                nullable=False,
            )
    if not any(item["name"] == "uq_attendance_code_date" for item in inspector.get_unique_constraints("attendance")):
        op.create_unique_constraint(
            "uq_attendance_code_date", "attendance", ["employee_code", "attendance_date"]
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if any(item["name"] == "uq_attendance_code_date" for item in inspector.get_unique_constraints("attendance")):
        op.drop_constraint("uq_attendance_code_date", "attendance", type_="unique")
    op.drop_column("attendance", "employee_name")
    op.drop_column("attendance", "employee_code")
    op.alter_column("attendance", "employee_id", existing_type=sa.Integer(), nullable=False)
