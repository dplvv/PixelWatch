from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from math import ceil
from pathlib import Path

from PIL import Image
from playwright.sync_api import Playwright, sync_playwright
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.statuses import SCREENSHOT_STATUS_FAILED, SCREENSHOT_STATUS_SUCCESS
from app.models.page_monitor import PageMonitor
from app.models.screenshot import Screenshot

DEFAULT_VIEWPORT_WIDTH = 1366
DEFAULT_VIEWPORT_HEIGHT = 900
MAX_DIRECT_CAPTURE_WIDTH = 12_000
MAX_DIRECT_CAPTURE_HEIGHT = 16_000
TILE_VIEWPORT_WIDTH = 2_000
TILE_VIEWPORT_HEIGHT = 1_500
DOM_SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)
DOM_COMMENT_RE = re.compile(r"<!--.*?-->", flags=re.DOTALL)
DOM_DYNAMIC_ATTR_RE = re.compile(
    r'\s(data-[^=]*(?:time|timestamp|nonce|token|uuid)[^=]*|nonce)="[^"]*"',
    flags=re.IGNORECASE,
)
WHITESPACE_RE = re.compile(r"\s+")


@dataclass(slots=True)
class CaptureSnapshot:
    http_status: int | None
    dom_hash: str | None
    text_hash: str | None
    text_length: int | None
    text_content: str | None


def _build_screenshot_relative_path(page_monitor_id: int) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"screenshots/monitor_{page_monitor_id}_{stamp}.png"


def _hash_string(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_dom_html(html: str) -> str:
    without_scripts = DOM_SCRIPT_STYLE_RE.sub(" ", html)
    without_comments = DOM_COMMENT_RE.sub(" ", without_scripts)
    without_dynamic_attrs = DOM_DYNAMIC_ATTR_RE.sub("", without_comments)
    normalized = WHITESPACE_RE.sub(" ", without_dynamic_attrs).strip()
    return normalized


def _normalize_visible_text(text: str) -> str:
    return WHITESPACE_RE.sub(" ", text).strip()


def _capture_with_playwright(url: str, output_path: Path) -> CaptureSnapshot:
    with sync_playwright() as playwright:
        return _capture_with_browser(playwright, url, output_path)


def _get_full_page_dimensions(page) -> tuple[int, int]:
    dimensions = page.evaluate(
        """() => {
            const body = document.body;
            const html = document.documentElement;
            const width = Math.max(
                body ? body.scrollWidth : 0,
                body ? body.offsetWidth : 0,
                html ? html.clientWidth : 0,
                html ? html.scrollWidth : 0,
                html ? html.offsetWidth : 0,
                window.innerWidth || 0
            );
            const height = Math.max(
                body ? body.scrollHeight : 0,
                body ? body.offsetHeight : 0,
                html ? html.clientHeight : 0,
                html ? html.scrollHeight : 0,
                html ? html.offsetHeight : 0,
                window.innerHeight || 0
            );
            return { width, height };
        }"""
    )
    width = max(1, int(dimensions["width"]))
    height = max(1, int(dimensions["height"]))
    return width, height


def _scroll_to_load_lazy_content(page) -> None:
    last_height = 0
    for _ in range(8):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(350)
        _, current_height = _get_full_page_dimensions(page)
        if current_height <= last_height:
            break
        last_height = current_height

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(150)


def _capture_tiled_full_page(page, output_path: Path, full_width: int, full_height: int) -> None:
    viewport_width = min(TILE_VIEWPORT_WIDTH, full_width)
    viewport_height = min(TILE_VIEWPORT_HEIGHT, full_height)
    page.set_viewport_size({"width": viewport_width, "height": viewport_height})

    stitched = Image.new("RGB", (full_width, full_height), color=(255, 255, 255))
    columns = ceil(full_width / viewport_width)
    rows = ceil(full_height / viewport_height)

    for row in range(rows):
        y = row * viewport_height
        for column in range(columns):
            x = column * viewport_width
            page.evaluate("(coords) => window.scrollTo(coords.x, coords.y)", {"x": x, "y": y})
            page.wait_for_timeout(120)
            tile_bytes = page.screenshot(full_page=False)
            with Image.open(BytesIO(tile_bytes)) as tile:
                tile_image = tile.convert("RGB")
                tile_width, tile_height = tile_image.size
                crop_width = min(tile_width, full_width - x)
                crop_height = min(tile_height, full_height - y)
                stitched.paste(tile_image.crop((0, 0, crop_width, crop_height)), (x, y))

    stitched.save(output_path)


def _capture_with_browser(playwright: Playwright, url: str, output_path: Path) -> CaptureSnapshot:
    browser = playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    try:
        context = browser.new_context(
            viewport={"width": DEFAULT_VIEWPORT_WIDTH, "height": DEFAULT_VIEWPORT_HEIGHT}
        )
        try:
            page = context.new_page()
            response = page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=settings.screenshot_timeout_seconds * 1000,
            )

            # Для страниц с постоянными фоновыми запросами (например, Google Docs)
            # "networkidle" часто не наступает. Делаем мягкое ожидание: сначала load,
            # затем короткая попытка networkidle без фейла всей проверки.
            try:
                page.wait_for_load_state("load", timeout=10_000)
            except Exception:  # noqa: BLE001
                pass

            try:
                page.wait_for_load_state("networkidle", timeout=3_000)
            except Exception:  # noqa: BLE001
                pass

            _scroll_to_load_lazy_content(page)

            full_width, full_height = _get_full_page_dimensions(page)

            try:
                page.wait_for_load_state("networkidle", timeout=2_000)
            except Exception:  # noqa: BLE001
                pass

            if (
                full_width > MAX_DIRECT_CAPTURE_WIDTH
                or full_height > MAX_DIRECT_CAPTURE_HEIGHT
            ):
                _capture_tiled_full_page(page, output_path, full_width, full_height)
            else:
                target_width = max(DEFAULT_VIEWPORT_WIDTH, full_width)
                page.set_viewport_size(
                    {"width": target_width, "height": DEFAULT_VIEWPORT_HEIGHT}
                )
                page.screenshot(path=str(output_path), full_page=True)

            raw_html = page.content()
            raw_text = page.evaluate(
                "() => document.body ? (document.body.innerText || '') : ''"
            )
            normalized_dom = _normalize_dom_html(raw_html)
            normalized_text = _normalize_visible_text(raw_text)
            dom_hash = _hash_string(normalized_dom) if normalized_dom else None
            text_hash = _hash_string(normalized_text) if normalized_text else None
            text_length = len(normalized_text) if normalized_text else 0

            return CaptureSnapshot(
                http_status=response.status if response is not None else None,
                dom_hash=dom_hash,
                text_hash=text_hash,
                text_length=text_length,
                text_content=normalized_text or None,
            )
        finally:
            context.close()
    finally:
        browser.close()


def capture_screenshot(db: Session, monitor: PageMonitor) -> Screenshot:
    relative_path = _build_screenshot_relative_path(monitor.id)
    absolute_path = settings.storage_dir / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        snapshot = _capture_with_playwright(monitor.url, absolute_path)
        with Image.open(absolute_path) as image:
            width, height = image.size

        screenshot = Screenshot(
            page_monitor_id=monitor.id,
            file_path=relative_path,
            width=width,
            height=height,
            status=SCREENSHOT_STATUS_SUCCESS,
            http_status=snapshot.http_status,
            dom_hash=snapshot.dom_hash,
            text_hash=snapshot.text_hash,
            text_length=snapshot.text_length,
            text_content=snapshot.text_content,
        )
    except Exception as exc:  # noqa: BLE001
        if absolute_path.exists():
            absolute_path.unlink(missing_ok=True)
        screenshot = Screenshot(
            page_monitor_id=monitor.id,
            file_path=None,
            width=None,
            height=None,
            status=SCREENSHOT_STATUS_FAILED,
            error_message=str(exc),
            http_status=None,
            dom_hash=None,
            text_hash=None,
            text_length=None,
            text_content=None,
        )

    db.add(screenshot)
    db.flush()
    db.refresh(screenshot)
    return screenshot


def get_previous_success_screenshot(
    db: Session,
    monitor_id: int,
    exclude_screenshot_id: int | None = None,
) -> Screenshot | None:
    stmt = select(Screenshot).where(
        Screenshot.page_monitor_id == monitor_id,
        Screenshot.status == SCREENSHOT_STATUS_SUCCESS,
        Screenshot.file_path.is_not(None),
    )

    if exclude_screenshot_id is not None:
        stmt = stmt.where(Screenshot.id != exclude_screenshot_id)

    stmt = stmt.order_by(desc(Screenshot.created_at), desc(Screenshot.id)).limit(1)
    return db.scalars(stmt).first()
