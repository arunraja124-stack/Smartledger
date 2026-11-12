# SmartLedger deployment readiness

Audit date: 2026-11-12

## Local project and database

- Frontend: React 18 / Vite; production build command is `npm run build` from `frontend`.
- Backend: FastAPI application `app.main:app`; health route is `/health`.
- The local database connected read-only as MySQL 9.6.0. It has 12 application tables, the Alembic version table, 8 foreign keys, and current revision `0003_attendance_snapshots`.
- A timestamped `mysqldump` and JSON manifest with table row counts were created in the operating system temporary directory. They are outside Git. The local database was not modified.
- No cloud import or production migration has been run. Validate a cloud import against an isolated cluster before considering a production cutover.

## Deployment files prepared

- `backend/Dockerfile` installs Tesseract and English data, CA certificates, application dependencies, and starts Uvicorn on the platform `PORT` without reload.
- `backend/.dockerignore` excludes environment files, local uploads, backups, logs, caches, tests, and virtual environments from the image build context.
- `render.yaml` describes the `smartledger-api` Docker web service on Render Free, with automatic deploys disabled and no secrets embedded.
- Production settings require a long private JWT secret, remote database credentials and CA bundle, an HTTPS frontend origin, and S3-compatible object storage credentials. Production startup rejects missing or placeholder settings.
- The backend can keep OCR files in a private S3-compatible bucket; local development retains local filesystem storage. `backend/scripts/copy_existing_uploads_to_s3.py` copies and verifies every local image, including files without a database row, without deleting local files or changing database rows. It has not been run against a cloud bucket.
- `frontend/vercel.json` provides SPA route fallback. The frontend only uses its localhost API fallback in Vite development mode; production expects `VITE_API_BASE_URL` to be configured.

## Provider constraints and compatibility

- Render Free web services sleep after 15 minutes idle, can take about a minute to wake, and have ephemeral local filesystems. The current allowance is 750 free instance hours per workspace per month, and Render may suspend a Free service for unusually high outbound traffic to external databases or object storage. This deployment therefore requires external object storage for durable OCR files. Render's free-plan documentation says Free instances are intended for preview/hobby workloads, not production.
- Vercel Hobby is free for personal, noncommercial use only. Confirm the intended use is eligible before using that plan; otherwise Vercel requires a paid plan.
- TiDB Cloud Starter currently offers 5 GiB row storage and 50 million request units monthly for each of the first five MySQL-compatible instances, with no card required to start. Its documented compatibility target is common MySQL 5.7 and 8.0 features. The source is MySQL 9.6. Foreign keys are generally available from TiDB 8.5, but the application still needs an isolated import and read-only compatibility test before any data migration.
- Cloudflare R2 includes 10 GB-month of Standard storage, 1 million Class A operations, 10 million Class B operations, and free egress each month. Creating an R2 subscription requires a dashboard checkout flow; usage above included quotas can be billed. No account or bucket has been created.

## Environment and tests

Required Render values include `DATABASE_URL`, `DATABASE_SSL_CA`, `JWT_SECRET_KEY`, `FRONTEND_ORIGIN`, and the `OBJECT_STORAGE_*` values. Vercel requires `VITE_API_BASE_URL` set to the actual backend URL ending in `/api`.

The local Docker executable and Docker CLI are unavailable, so the container could not be built or started locally. Render, Vercel, TiDB Cloud, and Cloudflare account integrations are not connected in this environment. Deployment URLs and cloud health checks are therefore not yet available.

The backend suite passed 25 tests using isolated SQLite databases. The frontend production build succeeded with a placeholder HTTPS API URL, rejected localhost as its production API URL, and produced assets without a localhost API host. The build reports Vite's existing large JavaScript chunk advisory.
