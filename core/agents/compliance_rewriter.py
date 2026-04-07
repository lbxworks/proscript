from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, SystemMessage

from core.prompts import SYSTEM_PROMPT_COMPLIANCE_REWRITER
from utils.llm_client import get_llm, validate_markdown_table_response


def run_compliance_rewriter(state: dict) -> dict:
    print("✍️ [Agent] Compliance Rewriter — Producing a safer revision when the review flags issues...")

    final_script = str(state.get("final_script", "") or "")
    report = state.get("compliance_report", {}) or {}
    issues = report.get("issues", []) or []
    overall_status = str(report.get("overall_status", "needs_revision")).lower()

    if not final_script.strip():
        return {"approved_script": ""}

    if overall_status in {"approved", "insufficient_evidence"} or not issues:
        return {"approved_script": final_script}

    user_prompt = f"""Rewrite the original script so it addresses the flagged issues while preserving:
- the existing markdown layout
- the multilingual order
- the time-code structure
- the scene count and pacing

ORIGINAL SCRIPT:
{final_script}

ISSUES TO FIX:
{json.dumps(issues, ensure_ascii=False, indent=2)}

Return the revised markdown script only.
"""

    try:
        llm = get_llm(
            temperature=0.2,
            task_name="compliance_rewriter",
            validator=validate_markdown_table_response,
        )
        response = llm.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT_COMPLIANCE_REWRITER),
                HumanMessage(content=user_prompt),
            ]
        )
        approved_script = str(response.content).strip() or final_script
    except Exception as exc:
        print(f"❌ [Compliance Rewriter] Rewrite failed: {exc}")
        approved_script = final_script

    return {"approved_script": approved_script}
