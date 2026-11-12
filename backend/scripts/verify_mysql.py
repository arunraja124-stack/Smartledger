from __future__ import annotations

import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal, engine

EXPECTED_TABLES = {
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


def main() -> int:
    print("SmartLedger MySQL connectivity verification")
    try:
        with engine.connect() as connection:
            database, version = connection.execute(
                text("SELECT DATABASE(), VERSION()")
            ).one()
            print(f"PASS: connected to database '{database}'")
            print(f"PASS: MySQL version {version}")

            inspector = inspect(connection)
            actual_tables = set(inspector.get_table_names())
            missing_tables = EXPECTED_TABLES - actual_tables
            if missing_tables:
                print(f"FAIL: missing tables: {', '.join(sorted(missing_tables))}")
                return 1
            print(f"PASS: all {len(EXPECTED_TABLES)} expected tables exist")

            foreign_key_count = sum(
                len(inspector.get_foreign_keys(table_name))
                for table_name in EXPECTED_TABLES
            )
            print(f"PASS: inspected {foreign_key_count} foreign keys")

        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
            print("PASS: SQLAlchemy session query succeeded")
    except SQLAlchemyError as error:
        print(f"FAIL: MySQL verification error: {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
