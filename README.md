# SmartLedger

SmartLedger is an AI-assisted digital register management system for attendance,
visitors, inventory, supplier purchases, service spare sales, and customer
enquiries.

## Current status

The repository currently contains the initial project architecture and runtime
configuration and the MySQL 8.0+ database layer. Tesseract OCR must be
available before the OCR phase can be executed. Live database migration remains
pending until valid local MySQL credentials are configured.

## Planned structure

```text
backend/
  app/
    api/          FastAPI routers
    core/         settings, security, and shared dependencies
    models/       SQLAlchemy ORM models
    schemas/      Pydantic request/response schemas
    services/     business logic, OCR, and exports
    repositories/ persistence queries
    utils/        shared helpers
    main.py       FastAPI application
  tests/
frontend/
  src/
    components/
    context/
    layouts/
    pages/
    services/
    App.jsx
docs/
```

## Windows development commands

### Backend

```powershell
py -3.11 -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The backend exposes a health endpoint at `http://127.0.0.1:8000/health` and
OpenAPI documentation at `http://127.0.0.1:8000/docs`.

## Environment configuration

Copy `backend\.env.example` to `backend\.env` and set a MySQL connection
string and a private JWT secret before enabling authenticated APIs. Never commit
real credentials.

The default SQLAlchemy URL uses the PyMySQL driver:

```text
mysql+pymysql://smartledger_user:<password>@localhost:3306/smartledger_db
```

The connection pool defaults to five persistent connections, up to ten
overflow connections, `pool_pre_ping` health checks, and a 30-minute recycle
interval. Adjust these values in `backend\.env` for the deployment size.

Create the development database and user in MySQL 8.0+ before running Alembic:

```sql
CREATE DATABASE smartledger_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER 'smartledger_user'@'localhost' IDENTIFIED BY 'change-me';
GRANT ALL PRIVILEGES ON smartledger_db.* TO 'smartledger_user'@'localhost';
FLUSH PRIVILEGES;
```

Then run:

```powershell
cd D:\SmartLedger\backend
alembic current
alembic upgrade head
python -m scripts.verify_mysql
```

The verification script performs read-only checks for the MySQL connection,
database name/version, SQLAlchemy session creation, all expected tables, and
foreign-key metadata. It never resets or deletes database objects.

## Backend API

Start the API from the project root:

```powershell
uvicorn app.main:app --reload --app-dir backend
```

Swagger documentation is available at `http://127.0.0.1:8000/docs`.
Authenticated register routes use a Bearer JWT returned by
`POST /api/auth/login`. Admin-only user administration is available under
`/api/users`; dashboard endpoints are under `/api/dashboard`; reports and
Excel exports are under `/api/reports`; PDF exports use the matching
`/api/reports/{report_type}/pdf` endpoint. Supported report types include
attendance, visitors, suppliers, spare-parts, purchases, spare-sales,
customer-enquiries, and inventory. Exports contain permanent database records
only; OCR review payloads are not exported as business data.

Document processing requires Tesseract. Configure `TESSERACT_CMD` in
`backend\.env` when it is not on PATH. The standard Windows installation path
is `C:\Program Files\Tesseract-OCR\tesseract.exe`. If the executable is
unavailable, the OCR endpoint returns an explicit `503` error rather than
pretending extraction succeeded.

## Required external software

- MySQL Server 8.0 or newer, with `mysql.exe` available to the PowerShell session
- Tesseract OCR, with `tesseract.exe` available to the PowerShell session
- Python 3.11+
- Node.js 20+

## Deployment preparation

Deployment configuration and the current readiness audit are documented in
[`docs/deployment-readiness.md`](docs/deployment-readiness.md). The backend can
be built with `backend/Dockerfile`; `render.yaml` is configured for a Render
Free preview service with automatic deploys disabled. The frontend has Vercel
SPA route fallback configured in `frontend/vercel.json`.

Production startup requires a private random `JWT_SECRET_KEY`, a remote
TLS-verified `DATABASE_URL`, an HTTPS `FRONTEND_ORIGIN`, and private S3-compatible
object storage settings. Keep these values in the hosting provider's secret
environment settings, never in Git. Render Free filesystems are ephemeral, so
the local upload directory is not suitable for persistent production uploads.

The included `backend/scripts/copy_existing_uploads_to_s3.py` can copy all local
OCR images to an approved private S3-compatible bucket and verify their
contents. It does not modify database records or delete local files. Do not run
it until the destination account, costs, and transfer of existing documents
are approved.
