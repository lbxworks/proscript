from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

from backend.database import ensure_database_schema, session_scope
from backend.models import Script, TalentProfile, TrendSnapshot, User


def _stringify_datetime(value: datetime | None) -> str:
    return value.isoformat(sep=" ", timespec="seconds") if value is not None else ""


def _derive_style_prompt(name: str, notes: str) -> str:
    cleaned_notes = notes.strip()
    if cleaned_notes:
        return cleaned_notes
    return f"你是达人{name}，请基于达人定位输出自然、有辨识度的短视频脚本。"


def _user_to_dict(user: User) -> dict[str, Any]:
    return {
        "id": int(user.id),
        "name": str(user.name),
        "style_prompt": str(user.style_prompt or ""),
        "few_shot": str(user.few_shot or ""),
    }


def _talent_to_dict(profile: TalentProfile) -> dict[str, Any]:
    return {
        "id": int(profile.id),
        "user_id": int(profile.user_id) if profile.user_id is not None else None,
        "name": str(profile.name),
        "platform": str(profile.platform or ""),
        "email": str(profile.email or ""),
        "recent_video_link": str(profile.recent_video_link or ""),
        "notes": str(profile.notes or ""),
        "collaboration_progress": str(profile.collaboration_progress or ""),
        "updated_at": _stringify_datetime(profile.updated_at),
    }


def _create_user_from_talent(*, name: str, notes: str) -> User:
    return User(
        name=name,
        style_prompt=_derive_style_prompt(name, notes),
        few_shot="",
    )


def _sync_existing_talent_users(session) -> None:
    missing_user_profiles = session.scalars(
        select(TalentProfile).where(TalentProfile.user_id.is_(None)).order_by(TalentProfile.id)
    ).all()

    for profile in missing_user_profiles:
        user = _create_user_from_talent(name=profile.name, notes=profile.notes or "")
        session.add(user)
        session.flush()
        profile.user_id = user.id
        profile.updated_at = datetime.utcnow()


def _backfill_profiles_from_users(session) -> None:
    profile_count = session.scalar(select(func.count()).select_from(TalentProfile)) or 0
    if profile_count > 0:
        return

    users = session.scalars(select(User).order_by(User.id)).all()
    for user in users:
        profile = TalentProfile(
            id=user.id,
            user_id=user.id,
            name=user.name or f"达人 {user.id}",
            platform="未设置",
            email="",
            recent_video_link="",
            notes=(user.style_prompt or "").strip() or "从原 users 表同步，待补充达人备注。",
            collaboration_progress="待沟通",
        )
        session.add(profile)


def ensure_trend_snapshots_table() -> None:
    ensure_database_schema()


def fetch_trend_snapshot(module_name: str, scope_key: str) -> dict[str, Any] | None:
    ensure_database_schema()

    with session_scope() as session:
        row = session.get(TrendSnapshot, {"module_name": module_name, "scope_key": scope_key})
        if row is None:
            return None
        return {
            "module_name": str(row.module_name),
            "scope_key": str(row.scope_key),
            "filters": dict(row.filters_json or {}),
            "payload": dict(row.payload_json or {}),
            "updated_at": _stringify_datetime(row.updated_at),
        }


def upsert_trend_snapshot(
    *,
    module_name: str,
    scope_key: str,
    filters: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    ensure_database_schema()

    with session_scope() as session:
        row = session.get(TrendSnapshot, {"module_name": module_name, "scope_key": scope_key})
        if row is None:
            row = TrendSnapshot(
                module_name=module_name,
                scope_key=scope_key,
                filters_json=filters,
                payload_json=payload,
            )
            session.add(row)
        else:
            row.filters_json = filters
            row.payload_json = payload
            row.updated_at = datetime.utcnow()
        session.flush()

        return {
            "module_name": module_name,
            "scope_key": scope_key,
            "filters": filters,
            "payload": payload,
            "updated_at": _stringify_datetime(row.updated_at),
        }


def ensure_talent_profiles_table() -> None:
    ensure_database_schema()

    with session_scope() as session:
        _backfill_profiles_from_users(session)
        _sync_existing_talent_users(session)


def list_talent_profiles() -> list[dict[str, Any]]:
    ensure_talent_profiles_table()

    with session_scope() as session:
        items = session.scalars(select(TalentProfile).order_by(TalentProfile.id)).all()
        return [_talent_to_dict(item) for item in items]


def create_talent_profile(
    *,
    name: str,
    platform: str,
    email: str,
    recent_video_link: str,
    notes: str,
    collaboration_progress: str,
) -> dict[str, Any]:
    ensure_talent_profiles_table()

    with session_scope() as session:
        user = _create_user_from_talent(name=name, notes=notes)
        session.add(user)
        session.flush()

        profile = TalentProfile(
            user_id=user.id,
            name=name,
            platform=platform,
            email=email,
            recent_video_link=recent_video_link,
            notes=notes,
            collaboration_progress=collaboration_progress,
        )
        session.add(profile)
        session.flush()
        return _talent_to_dict(profile)


def update_talent_profile(
    *,
    talent_id: int,
    name: str,
    platform: str,
    email: str,
    recent_video_link: str,
    notes: str,
    collaboration_progress: str,
) -> dict[str, Any] | None:
    ensure_talent_profiles_table()

    with session_scope() as session:
        profile = session.get(TalentProfile, talent_id)
        if profile is None:
            return None

        if profile.user_id is None:
            user = _create_user_from_talent(name=name, notes=notes)
            session.add(user)
            session.flush()
            profile.user_id = user.id
        else:
            user = session.get(User, profile.user_id)
            if user is None:
                user = _create_user_from_talent(name=name, notes=notes)
                session.add(user)
                session.flush()
                profile.user_id = user.id
            else:
                user.name = name
                user.style_prompt = _derive_style_prompt(name, notes)

        profile.name = name
        profile.platform = platform
        profile.email = email
        profile.recent_video_link = recent_video_link
        profile.notes = notes
        profile.collaboration_progress = collaboration_progress
        profile.updated_at = datetime.utcnow()
        session.flush()
        return _talent_to_dict(profile)


def delete_talent_profile(talent_id: int) -> bool:
    ensure_talent_profiles_table()

    with session_scope() as session:
        profile = session.get(TalentProfile, talent_id)
        if profile is None:
            return False

        user_id = profile.user_id
        if user_id is not None:
            session.execute(
                update(Script).where(Script.user_id == user_id).values(user_id=None)
            )

        session.delete(profile)

        if user_id is not None:
            user = session.get(User, user_id)
            if user is not None:
                session.delete(user)

        return True


def fetch_user_profile(user_id: int) -> dict[str, Any] | None:
    ensure_database_schema()

    try:
        with session_scope() as session:
            user = session.get(User, user_id)
            return _user_to_dict(user) if user is not None else None
    except SQLAlchemyError:
        return None


def list_users_for_legacy_ui() -> list[tuple[int, str, str]]:
    ensure_database_schema()

    try:
        with session_scope() as session:
            users = session.scalars(select(User).order_by(User.id)).all()
            return [(int(user.id), str(user.name), str(user.style_prompt or "")) for user in users]
    except SQLAlchemyError:
        return []


def save_script_record(
    *,
    user_id: int | None,
    topic: str,
    platform: str,
    duration: str,
    creativity: float,
    language: str,
    content: str,
) -> int | None:
    ensure_database_schema()

    try:
        with session_scope() as session:
            record = Script(
                user_id=user_id,
                topic=topic,
                platform=platform,
                duration=duration,
                creativity=creativity,
                language=language,
                content=content,
            )
            session.add(record)
            session.flush()
            return int(record.id)
    except SQLAlchemyError:
        return None
