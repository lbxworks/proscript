from __future__ import annotations

from typing import Any

from backend.db import fetch_user_profile, save_script_record
from backend.schemas import GenerateScriptRequest, ReviewScriptRequest
from core.agents.compliance_retriever import run_compliance_retriever
from core.agents.compliance_reviewer import run_compliance_reviewer
from core.agents.compliance_rewriter import run_compliance_rewriter
from core.agents.compliance_rule_engine import run_compliance_rule_engine
from core.agents.compliance_scope_resolver import run_compliance_scope_resolver
from core.workflow import build_workflow


def generate_script(payload: GenerateScriptRequest) -> dict[str, Any]:
    initial_state = {
        "user_id": payload.user_id,
        "topic": payload.topic,
        "target_languages": payload.target_languages,
        "video_duration": payload.video_duration,
        "target_platform": payload.target_platform,
        "target_country": payload.target_country,
        "distribution_mode": payload.distribution_mode,
        "product_category": payload.product_category,
        "brand_id": payload.brand_id,
        "creativity": payload.creativity,
    }

    final_state = build_workflow().invoke(initial_state)

    saved_record_id = None
    if payload.persist_result:
        saved_record_id = save_script_record(
            user_id=payload.user_id,
            topic=payload.topic,
            platform=payload.target_platform,
            duration=payload.video_duration,
            creativity=payload.creativity,
            language=", ".join(payload.target_languages) if payload.target_languages else "English",
            content=str(final_state.get("final_script", "") or ""),
        )

    return {
        "initial_state": initial_state,
        "final_state": final_state,
        "saved_record_id": saved_record_id,
    }


def review_script(payload: ReviewScriptRequest) -> dict[str, Any]:
    user_profile = fetch_user_profile(payload.user_id) if payload.user_id is not None else None
    style_prompt = payload.style_prompt or (user_profile or {}).get("style_prompt") or "默认客观风格"
    few_shot = (user_profile or {}).get("few_shot", "") if user_profile else ""
    normalized_topic = payload.topic or str(payload.script.splitlines()[0]).strip() or "Script Review"

    state: dict[str, Any] = {
        "user_id": payload.user_id or 0,
        "topic": normalized_topic,
        "target_languages": payload.target_languages,
        "target_platform": payload.target_platform,
        "target_country": payload.target_country,
        "distribution_mode": payload.distribution_mode,
        "product_category": payload.product_category,
        "brand_id": payload.brand_id,
        "style_prompt": style_prompt,
        "few_shot": few_shot,
        "final_script": payload.script,
    }

    for step in (
        run_compliance_scope_resolver,
        run_compliance_retriever,
        run_compliance_rule_engine,
        run_compliance_reviewer,
        run_compliance_rewriter,
    ):
        state.update(step(state))

    return {
        "initial_state": {
            "topic": normalized_topic,
            "target_languages": payload.target_languages,
            "target_platform": payload.target_platform,
            "target_country": payload.target_country,
            "distribution_mode": payload.distribution_mode,
            "product_category": payload.product_category,
            "brand_id": payload.brand_id,
            "user_id": payload.user_id,
        },
        "final_state": state,
    }
