"""Add hybrid change detection signals

Revision ID: 20260514_0002
Revises: 20260514_0001
Create Date: 2026-05-14 00:20:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260514_0002"
down_revision = "20260514_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("screenshots", sa.Column("dom_hash", sa.String(length=64), nullable=True))
    op.add_column("screenshots", sa.Column("text_hash", sa.String(length=64), nullable=True))
    op.add_column("screenshots", sa.Column("text_length", sa.Integer(), nullable=True))
    op.add_column("screenshots", sa.Column("text_content", sa.Text(), nullable=True))

    op.add_column("visual_diffs", sa.Column("text_change_percent", sa.Float(), nullable=True))
    op.add_column(
        "visual_diffs",
        sa.Column(
            "hybrid_change_percent",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "visual_diffs",
        sa.Column(
            "dom_changed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.execute("UPDATE visual_diffs SET hybrid_change_percent = change_percent")


def downgrade() -> None:
    op.drop_column("visual_diffs", "dom_changed")
    op.drop_column("visual_diffs", "hybrid_change_percent")
    op.drop_column("visual_diffs", "text_change_percent")

    op.drop_column("screenshots", "text_content")
    op.drop_column("screenshots", "text_length")
    op.drop_column("screenshots", "text_hash")
    op.drop_column("screenshots", "dom_hash")
