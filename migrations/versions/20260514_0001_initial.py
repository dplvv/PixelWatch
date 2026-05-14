"""Initial schema

Revision ID: 20260514_0001
Revises:
Create Date: 2026-05-14 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260514_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "page_monitors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("check_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=True),
        sa.Column("last_change_percent", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "screenshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_monitor_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=4096), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["page_monitor_id"], ["page_monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_screenshots_monitor_created", "screenshots", ["page_monitor_id", "created_at"])

    op.create_table(
        "visual_diffs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_monitor_id", sa.Integer(), nullable=False),
        sa.Column("old_screenshot_id", sa.Integer(), nullable=False),
        sa.Column("new_screenshot_id", sa.Integer(), nullable=False),
        sa.Column("diff_file_path", sa.String(length=4096), nullable=False),
        sa.Column("change_percent", sa.Float(), nullable=False),
        sa.Column("changed_pixels_count", sa.Integer(), nullable=False),
        sa.Column("total_pixels_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["new_screenshot_id"], ["screenshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["old_screenshot_id"], ["screenshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["page_monitor_id"], ["page_monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_visual_diffs_monitor_created", "visual_diffs", ["page_monitor_id", "created_at"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("page_monitor_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["page_monitor_id"], ["page_monitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_read_created", "notifications", ["is_read", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_visual_diffs_monitor_created", table_name="visual_diffs")
    op.drop_table("visual_diffs")
    op.drop_index("ix_screenshots_monitor_created", table_name="screenshots")
    op.drop_table("screenshots")
    op.drop_table("page_monitors")
