from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API for the SmartLedger digital register management system.",
    version="0.1.0",
    debug=False,
)

allowed_origins = {settings.frontend_origin.rstrip("/")}
if settings.environment.strip().lower() != "production":
    allowed_origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "smartledger-api"}
