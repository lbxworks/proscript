from __future__ import annotations

from time import perf_counter
from typing import Any

from backend.db import fetch_user_profile, save_script_record
from backend.schemas import GenerateScriptRequest, ReviewScriptRequest
from backend.services.streaming import EmitCallback, ProgressStepError
from core.agents.compliance_retriever import run_compliance_retriever
from core.agents.compliance_reviewer import run_compliance_reviewer
from core.agents.compliance_rewriter import run_compliance_rewriter
from core.agents.compliance_rule_engine import run_compliance_rule_engine
from core.agents.compliance_scope_resolver import run_compliance_scope_resolver
from core.agents.profiler import run_profiler
from core.agents.trend_hunter import run_trend_hunter
from core.agents.writer import run_writer
from core.script_cleanup import sanitize_script_markdown


def _emit_progress(
    emit: EmitCallback | None,
    *,
    step: str,
    status: str,
    message: str,
    duration_ms: int | None = None,
) -> None:
    if emit is None:
        return

    payload: dict[str, Any] = {
        "step": step,
        "status": status,
        "message": message,
    }
    if duration_ms is not None:
        payload["duration_ms"] = duration_ms
    emit("progress", payload)


def _friendly_workflow_error(step: str, exc: Exception) -> ProgressStepError:
    text = str(exc).lower()

    if step == "trend_hunter":
        return ProgressStepError(
            step=step,
            error_type="search_timeout",
            message="网络数据源暂时开小差了，Villy 本次没有捕获到热点。",
        )

    if step in {"script_writer", "rewriter", "compliance_fix"} and any(
        keyword in text for keyword in ("rate", "429", "timeout", "api", "quota", "connection")
    ):
        return ProgressStepError(
            step=step,
            error_type="llm_busy",
            message="当前 AI 服务繁忙，Villy 暂时排不上队了。",
        )

    if step in {"compliance", "compliance_scan"}:
        return ProgressStepError(
            step=step,
            error_type="compliance_blocked",
            message="为了保护你的账号安全，系统拦截了本次内容，请先调整需求后再试。",
        )

    return ProgressStepError(
        step=step,
        error_type="workflow_error",
        message="这一步暂时没有顺利完成，我们可以稍后再试一次。",
    )


def _run_step(
    *,
    state: dict[str, Any],
    step: str,
    active_message: str,
    completed_message: str,
    worker,
    emit: EmitCallback | None = None,
) -> None:
    _emit_progress(emit, step=step, status="active", message=active_message)
    started_at = perf_counter()
    try:
        state.update(worker(state))
    except Exception as exc:
        raise _friendly_workflow_error(step, exc) from exc
    duration_ms = int((perf_counter() - started_at) * 1000)
    _emit_progress(
        emit,
        step=step,
        status="completed",
        message=completed_message,
        duration_ms=duration_ms,
    )


def _build_generate_initial_state(payload: GenerateScriptRequest) -> dict[str, Any]:
    return {
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


def _finalize_generate_result(
    *,
    payload: GenerateScriptRequest,
    initial_state: dict[str, Any],
    final_state: dict[str, Any],
) -> dict[str, Any]:
    final_state["final_script"] = sanitize_script_markdown(final_state.get("final_script", ""))
    final_state["approved_script"] = sanitize_script_markdown(final_state.get("approved_script", ""))

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


def _run_generate_workflow(
    payload: GenerateScriptRequest,
    *,
    emit: EmitCallback | None = None,
) -> dict[str, Any]:
    initial_state = _build_generate_initial_state(payload)
    state = dict(initial_state)

    _run_step(
        state=state,
        step="profiler",
        active_message="正在扫描社交网络用户习惯...",
        completed_message="受众画像分析完成。",
        worker=run_profiler,
        emit=emit,
    )
    _run_step(
        state=state,
        step="trend_hunter",
        active_message="正在追踪近期热点与创作方向...",
        completed_message="热点脉络已整理完成。",
        worker=run_trend_hunter,
        emit=emit,
    )
    _run_step(
        state=state,
        step="script_writer",
        active_message="正在组织脚本结构与镜头语言...",
        completed_message="脚本初稿已经写好。",
        worker=run_writer,
        emit=emit,
    )
    state["final_script"] = sanitize_script_markdown(state.get("final_script", ""))

    def compliance_worker(current_state: dict[str, Any]) -> dict[str, Any]:
        next_state = dict(current_state)
        for step_fn in (
            run_compliance_scope_resolver,
            run_compliance_retriever,
            run_compliance_rule_engine,
            run_compliance_reviewer,
        ):
            next_state.update(step_fn(next_state))
        return next_state

    _run_step(
        state=state,
        step="compliance",
        active_message="正在执行全球平台合规审查...",
        completed_message="合规风险扫描完成。",
        worker=compliance_worker,
        emit=emit,
    )
    _run_step(
        state=state,
        step="rewriter",
        active_message="正在打磨最终交付版本...",
        completed_message="最终定稿已生成。",
        worker=run_compliance_rewriter,
        emit=emit,
    )
    state["approved_script"] = sanitize_script_markdown(state.get("approved_script", ""))

    return _finalize_generate_result(payload=payload, initial_state=initial_state, final_state=state)


def _build_review_state(payload: ReviewScriptRequest) -> tuple[dict[str, Any], dict[str, Any]]:
    cleaned_script = sanitize_script_markdown(payload.script)
    user_profile = fetch_user_profile(payload.user_id) if payload.user_id is not None else None
    style_prompt = payload.style_prompt or (user_profile or {}).get("style_prompt") or "默认客观风格"
    few_shot = (user_profile or {}).get("few_shot", "") if user_profile else ""
    normalized_topic = payload.topic or str(cleaned_script.splitlines()[0]).strip() or "Script Review"

    initial_state = {
        "topic": normalized_topic,
        "target_languages": payload.target_languages,
        "target_platform": payload.target_platform,
        "target_country": payload.target_country,
        "distribution_mode": payload.distribution_mode,
        "product_category": payload.product_category,
        "brand_id": payload.brand_id,
        "user_id": payload.user_id,
    }
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
        "final_script": cleaned_script,
    }
    return initial_state, state


def _run_review_workflow(
    payload: ReviewScriptRequest,
    *,
    emit: EmitCallback | None = None,
) -> dict[str, Any]:
    initial_state, state = _build_review_state(payload)

    def compliance_scan_worker(current_state: dict[str, Any]) -> dict[str, Any]:
        next_state = dict(current_state)
        for step_fn in (
            run_compliance_scope_resolver,
            run_compliance_retriever,
            run_compliance_rule_engine,
            run_compliance_reviewer,
        ):
            next_state.update(step_fn(next_state))
        return next_state

    _run_step(
        state=state,
        step="compliance_scan",
        active_message="正在定位法规、知识库和平台红线...",
        completed_message="合规扫描与问题诊断完成。",
        worker=compliance_scan_worker,
        emit=emit,
    )
    _run_step(
        state=state,
        step="compliance_fix",
        active_message="正在修正风险表达并生成建议稿...",
        completed_message="建议修订稿已生成。",
        worker=run_compliance_rewriter,
        emit=emit,
    )

    state["final_script"] = sanitize_script_markdown(state.get("final_script", ""))
    state["approved_script"] = sanitize_script_markdown(state.get("approved_script", ""))
    return {
        "initial_state": initial_state,
        "final_state": state,
    }


def generate_script(payload: GenerateScriptRequest) -> dict[str, Any]:
    return _run_generate_workflow(payload)


def review_script(payload: ReviewScriptRequest) -> dict[str, Any]:
    return _run_review_workflow(payload)


def stream_generate_script(payload: GenerateScriptRequest, emit: EmitCallback) -> dict[str, Any]:
    return _run_generate_workflow(payload, emit=emit)


def stream_review_script(payload: ReviewScriptRequest, emit: EmitCallback) -> dict[str, Any]:
    return _run_review_workflow(payload, emit=emit)
