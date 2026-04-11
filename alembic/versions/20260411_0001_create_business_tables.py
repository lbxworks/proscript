"""create business tables

Revision ID: 20260411_0001
Revises:
Create Date: 2026-04-11 18:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260411_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("style_prompt", sa.Text(), nullable=False),
        sa.Column("few_shot", sa.Text(), nullable=True),
    )

    op.create_table(
        "trend_snapshots",
        sa.Column("module_name", sa.String(length=120), nullable=False),
        sa.Column("scope_key", sa.Text(), nullable=False),
        sa.Column("filters_json", sa.JSON(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("module_name", "scope_key"),
    )

    op.create_table(
        "scripts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=True),
        sa.Column("duration", sa.Text(), nullable=True),
        sa.Column("creativity", sa.Float(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "talent_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False, server_default=sa.text("'未设置'")),
        sa.Column("email", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("recent_video_link", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("notes", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("collaboration_progress", sa.Text(), nullable=False, server_default=sa.text("'待沟通'")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("talent_profiles")
    op.drop_table("scripts")
    op.drop_table("trend_snapshots")
    op.drop_table("users")
