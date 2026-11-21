FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ENVIRONMENT=production \
    TESSERACT_CMD=/usr/bin/tesseract \
    DATABASE_SSL_CA=/app/certs/tidb-ca.pem \
    DOCUMENT_STORAGE_BACKEND=s3 \
    OBJECT_STORAGE_REGION=auto \
    UPLOAD_DIR=/tmp/smartledger-uploads

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgomp1 \
        libglib2.0-0 \
        libgl1 \
        tesseract-ocr \
        tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt


COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts
COPY certs ./certs

RUN groupadd --system smartledger \
    && useradd --system --gid smartledger --home-dir /app --shell /usr/sbin/nologin smartledger \
    && mkdir -p /tmp/smartledger-uploads \
    && chown -R smartledger:smartledger /app /tmp/smartledger-uploads

USER smartledger
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]