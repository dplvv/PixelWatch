from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.web.routes import router as web_router

app = FastAPI(
    title="PixelWatch",
    description="Сервис мониторинга визуальных изменений сайтов",
    version="0.1.0",
)

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "web" / "static")),
    name="static",
)
app.mount(
    "/storage",
    StaticFiles(directory=str(settings.storage_dir)),
    name="storage",
)

app.include_router(web_router)
app.include_router(api_router)


@app.get("/health", tags=["Сервис"])
def healthcheck() -> dict[str, str]:
    return {"status": "готово"}


@app.on_event("startup")
def setup_storage_dirs() -> None:
    settings.screenshots_dir.mkdir(parents=True, exist_ok=True)
    settings.diffs_dir.mkdir(parents=True, exist_ok=True)
