from __future__ import annotations

from backend.db import fetch_user_profile


def run_profiler(state: dict) -> dict:
    print("🤖 [Agent] Profiler 执行中: 正在分析达人风格...")
    user_id = state.get("user_id")
    user_profile = fetch_user_profile(int(user_id)) if user_id else None

    if user_profile:
        style_prompt = str(user_profile.get("style_prompt") or "")
        few_shot = str(user_profile.get("few_shot") or "")
    else:
        style_prompt, few_shot = "默认客观风格", ""
        print("⚠️ 警告: 未找到该达人，使用默认风格")

    return {"style_prompt": style_prompt, "few_shot": few_shot}
