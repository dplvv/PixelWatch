from app.api.routes.diffs import router as diffs_router
from app.api.routes.monitors import router as monitors_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.screenshots import router as screenshots_router

__all__ = ["monitors_router", "screenshots_router", "diffs_router", "notifications_router"]
