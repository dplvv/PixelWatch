from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher

from PIL import Image, ImageChops
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.page_monitor import PageMonitor
from app.models.screenshot import Screenshot
from app.models.visual_diff import VisualDiff

VISUAL_WEIGHT = 0.65
TEXT_WEIGHT = 0.30
DOM_WEIGHT = 0.05
MIN_NOISE_PERCENT = 0.03


@dataclass(slots=True)
class DiffResult:
    changed_pixels_count: int
    total_pixels_count: int
    change_percent: float
    mask: Image.Image
    old_image: Image.Image
    new_image: Image.Image


def compute_visual_difference(
    old_image: Image.Image,
    new_image: Image.Image,
    threshold: int,
) -> DiffResult:
    left = old_image.convert("RGB")
    right = new_image.convert("RGB")

    if left.size != right.size:
        right = right.resize(left.size, Image.Resampling.LANCZOS)

    diff = ImageChops.difference(left, right)
    grayscale_diff = diff.convert("L")
    mask = grayscale_diff.point(lambda px: 255 if px > threshold else 0)

    changed_pixels_count = sum(1 for pixel in mask.getdata() if pixel)
    total_pixels_count = mask.width * mask.height
    change_percent = 0.0

    if total_pixels_count > 0:
        change_percent = round((changed_pixels_count / total_pixels_count) * 100, 4)

    return DiffResult(
        changed_pixels_count=changed_pixels_count,
        total_pixels_count=total_pixels_count,
        change_percent=change_percent,
        mask=mask,
        old_image=left,
        new_image=right,
    )


def _build_diff_relative_path(page_monitor_id: int) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"diffs/diff_{page_monitor_id}_{stamp}.png"


def _build_diff_visual(mask: Image.Image, new_image: Image.Image) -> Image.Image:
    base = new_image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 0, 0, 0))
    overlay.putalpha(mask.point(lambda px: 170 if px else 0))
    return Image.alpha_composite(base, overlay)


def compute_text_change_percent(old_text: str | None, new_text: str | None) -> float | None:
    if old_text is None or new_text is None:
        return None

    if not old_text and not new_text:
        return 0.0

    ratio = SequenceMatcher(a=old_text, b=new_text).ratio()
    return round((1 - ratio) * 100, 4)


def compute_hybrid_change_percent(
    visual_change_percent: float,
    text_change_percent: float | None,
    dom_changed: bool,
) -> float:
    text_component = (
        text_change_percent
        if text_change_percent is not None
        else visual_change_percent
    )
    dom_component = 100.0 if dom_changed else 0.0

    if (
        visual_change_percent < MIN_NOISE_PERCENT
        and text_component < MIN_NOISE_PERCENT
        and not dom_changed
    ):
        return 0.0

    hybrid = (
        (visual_change_percent * VISUAL_WEIGHT)
        + (text_component * TEXT_WEIGHT)
        + (dom_component * DOM_WEIGHT)
    )
    return round(min(max(hybrid, 0.0), 100.0), 4)


def create_visual_diff(
    db: Session,
    monitor: PageMonitor,
    old_screenshot: Screenshot,
    new_screenshot: Screenshot,
) -> VisualDiff | None:
    if not old_screenshot.file_path or not new_screenshot.file_path:
        return None

    old_path = settings.storage_dir / old_screenshot.file_path
    new_path = settings.storage_dir / new_screenshot.file_path

    if not old_path.exists() or not new_path.exists():
        return None

    with Image.open(old_path) as old_image, Image.open(new_path) as new_image:
        result = compute_visual_difference(old_image, new_image, settings.visual_diff_threshold)
        diff_visual = _build_diff_visual(result.mask, result.new_image)

    dom_changed = (
        bool(old_screenshot.dom_hash)
        and bool(new_screenshot.dom_hash)
        and old_screenshot.dom_hash != new_screenshot.dom_hash
    )
    text_change_percent = compute_text_change_percent(
        old_screenshot.text_content,
        new_screenshot.text_content,
    )
    hybrid_change_percent = compute_hybrid_change_percent(
        visual_change_percent=result.change_percent,
        text_change_percent=text_change_percent,
        dom_changed=dom_changed,
    )

    relative_path = _build_diff_relative_path(monitor.id)
    absolute_path = settings.storage_dir / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    diff_visual.save(absolute_path)

    visual_diff = VisualDiff(
        page_monitor_id=monitor.id,
        old_screenshot_id=old_screenshot.id,
        new_screenshot_id=new_screenshot.id,
        diff_file_path=relative_path,
        change_percent=result.change_percent,
        text_change_percent=text_change_percent,
        hybrid_change_percent=hybrid_change_percent,
        dom_changed=dom_changed,
        changed_pixels_count=result.changed_pixels_count,
        total_pixels_count=result.total_pixels_count,
    )
    db.add(visual_diff)
    db.flush()
    db.refresh(visual_diff)
    return visual_diff
