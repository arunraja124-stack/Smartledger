from app.models import Base


def test_expected_tables_are_declared() -> None:
    expected = {
        "users",
        "employees",
        "attendance",
        "visitors",
        "suppliers",
        "spare_parts",
        "purchases",
        "spare_sales",
        "customer_enquiries",
        "document_uploads",
        "document_extracted_records",
        "audit_logs",
    }

    assert expected == set(Base.metadata.tables)


def test_attendance_has_duplicate_prevention_constraint() -> None:
    table = Base.metadata.tables["attendance"]

    assert any(
        constraint.name == "uq_attendance_employee_date"
        for constraint in table.constraints
    )


def test_foreign_keys_are_declared() -> None:
    table = Base.metadata.tables["attendance"]

    assert {foreign_key.target_fullname for foreign_key in table.foreign_keys} == {
        "employees.id"
    }
