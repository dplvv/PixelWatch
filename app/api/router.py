from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.diffs import router as diffs_router
from app.api.routes.monitors import router as monitors_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.screenshots import router as screenshots_router

api_router = APIRouter()
api_router.include_router(monitors_router)
api_router.include_router(screenshots_router)
api_router.include_router(diffs_router)
api_router.include_router(notifications_router)
