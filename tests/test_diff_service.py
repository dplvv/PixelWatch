from __future__ import annotations

from PIL import Image

from app.services.diff_service import (
    compute_hybrid_change_percent,
    compute_text_change_percent,
    compute_visual_difference,
)


def test_compare_identical_images_returns_zero_diff():
    left = Image.new("RGB", (32, 32), color=(255, 255, 255))
    right = Image.new("RGB", (32, 32), color=(255, 255, 255))

    result = compute_visual_difference(left, right, threshold=25)

    assert result.changed_pixels_count == 0
    assert result.total_pixels_count == 1024
    assert result.change_percent == 0.0


def test_compare_different_images_detects_changes():
    left = Image.new("RGB", (20, 20), color=(255, 255, 255))
    right = Image.new("RGB", (20, 20), color=(0, 0, 0))

    result = compute_visual_difference(left, right, threshold=25)

    assert result.changed_pixels_count == 400
    assert result.total_pixels_count == 400
    assert result.change_percent == 100.0


def test_compare_identical_text_returns_zero_diff():
    result = compute_text_change_percent("hello world", "hello world")
    assert result == 0.0


def test_hybrid_score_uses_visual_text_and_dom_signals():
    hybrid = compute_hybrid_change_percent(
        visual_change_percent=2.0,
        text_change_percent=10.0,
        dom_changed=True,
    )

    assert hybrid > 2.0
    assert hybrid <= 100.0
