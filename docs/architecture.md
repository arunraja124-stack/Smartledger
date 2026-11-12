# SmartLedger architecture

## Runtime boundaries

- **React/Vite frontend**: authenticated user experience, register forms, review
  tables, charts, and file upload.
- **FastAPI backend**: authentication, validation, authorization, transactions,
  OCR orchestration, and Excel generation.
- **MySQL 8.0+**: normalized durable business data and processing history,
  accessed through SQLAlchemy and PyMySQL.
- **Filesystem/object storage boundary**: original uploaded images only; metadata
  and status remain in MySQL.

## Backend layering

Routers translate HTTP requests into Pydantic schemas and service calls.
Services own business rules and transaction boundaries. Repositories contain
database queries. SQLAlchemy models represent normalized tables and Alembic
migrations manage schema changes.

## Planned module boundaries

`auth`, `dashboard`, `employees`, `attendance`, `visitors`, `inventory`,
`purchases`, `sales`, `enquiries`, `documents`, `reports`, and `users`.
