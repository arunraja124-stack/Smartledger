from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.crud import router as crud_router
from app.api.documents import router as documents_router
from app.api.admin import router as admin_router
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router

router = APIRouter(prefix="/api")


@router.get("/status", tags=["system"])
def api_status() -> dict[str, str]:
    return {"status": "ok", "service": "smartledger-api"}


router.include_router(auth_router)
router.include_router(crud_router)
router.include_router(documents_router)
router.include_router(admin_router)
router.include_router(dashboard_router)
router.include_router(reports_router)
