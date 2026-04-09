from __future__ import annotations

from typing import Any

from backend.db import create_talent_profile, delete_talent_profile, list_talent_profiles, update_talent_profile
from backend.schemas import TalentMutationRequest


def get_talents() -> dict[str, Any]:
    items = list_talent_profiles()
    return {
        "items": items,
        "total": len(items),
    }


def create_talent(payload: TalentMutationRequest) -> dict[str, Any]:
    item = create_talent_profile(
        name=payload.name.strip(),
        platform=payload.platform.strip() or "未设置",
        email=payload.email.strip(),
        recent_video_link=payload.recent_video_link.strip(),
        notes=payload.notes.strip(),
        collaboration_progress=payload.collaboration_progress.strip() or "待沟通",
    )
    return {"item": item}


def update_talent(talent_id: int, payload: TalentMutationRequest) -> dict[str, Any]:
    item = update_talent_profile(
        talent_id=talent_id,
        name=payload.name.strip(),
        platform=payload.platform.strip() or "未设置",
        email=payload.email.strip(),
        recent_video_link=payload.recent_video_link.strip(),
        notes=payload.notes.strip(),
        collaboration_progress=payload.collaboration_progress.strip() or "待沟通",
    )
    if item is None:
        raise LookupError(f"达人 {talent_id} 不存在。")
    return {"item": item}


def remove_talent(talent_id: int) -> dict[str, Any]:
    deleted = delete_talent_profile(talent_id)
    if not deleted:
        raise LookupError(f"达人 {talent_id} 不存在。")
    return {"deleted": True, "id": talent_id}
