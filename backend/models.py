from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    style_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    few_shot: Mapped[str | None] = mapped_column(Text, nullable=True)

    talent_profile: Mapped["TalentProfile | None"] = relationship(back_populates="user", uselist=False)
    scripts: Mapped[list["Script"]] = relationship(back_populates="user")


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[str | None] = mapped_column(Text, nullable=True)
    creativity: Mapped[float | None] = mapped_column(nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="scripts")


class TalentProfile(Base):
    __tablename__ = "talent_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(Text, nullable=False, default="未设置", server_default="未设置")
    email: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    recent_video_link: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    collaboration_progress: Mapped[str] = mapped_column(Text, nullable=False, default="待沟通", server_default="待沟通")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=True)

    user: Mapped[User | None] = relationship(back_populates="talent_profile")


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    module_name: Mapped[str] = mapped_column(String(120), primary_key=True)
    scope_key: Mapped[str] = mapped_column(Text, primary_key=True)
    filters_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), nullable=True)
