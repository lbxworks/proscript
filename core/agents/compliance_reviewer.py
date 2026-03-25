from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from core.prompts import SYSTEM_PROMPT_COMPLIANCE_REVIEWER
from utils.llm_client import get_llm


def _extract_json_object(text: str) -> Dict[str, Any]:
    fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    json_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    raise ValueError("No JSON object found in model response")


def _fallback_report(state: dict, reason: str) -> Dict[str, Any]:
    return {
        "overall_status": "insufficient_evidence",
        "overall_risk": "medium",
        "headline": "Compliance review needs more local evidence",
        "overall_commentary": reason,
        "closing_note": "Add scoped knowledge base files under data/knowledge_base before relying on this output.",
        "issues": [
            {
                "excerpt": state.get("topic", "") or "No excerpt available",
                "risk_level": "medium",
                "issue_type": "missing_local_evidence",
                "reason": reason,
                "suggested_fix": "Import local law, platform policy, or brand brief files for the selected market and rerun review.",
                "citations": [],
            }
        ],
    }


def _compact_evidence(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        return "No scoped evidence was found."

    lines = []
    for index, item in enumerate(evidence, start=1):
        heading = item.get("heading_path") or "N/A"
        source_url = item.get("source_url") or "local-file"
        lines.append(
            f"[{index}] {item.get('source_title', 'Untitled')} | "
            f"type={item.get('source_type', 'policy')} | "
            f"country={item.get('country_code', 'GLOBAL')} | "
            f"platform={item.get('platform', 'all') or 'all'} | "
            f"mode={item.get('distribution_mode', 'all') or 'all'} | "
            f"page={item.get('page_num', 'N/A')} | "
            f"heading={heading} | "
            f"url={source_url}\n"
            f"Excerpt: {item.get('excerpt', '')}"
        )
    return "\n\n".join(lines)


def run_compliance_reviewer(state: dict) -> dict:
    print("🛡️ [Agent] Compliance Reviewer — Auditing script risk and drafting suggestions...")

    final_script = state.get("final_script", "")
    retrieved_evidence = state.get("retrieved_evidence", []) or []

    if not final_script.strip():
        report = _fallback_report(state, "The script generator did not produce any content to review.")
        return {"compliance_report": report}

    if not retrieved_evidence:
        report = _fallback_report(
            state,
            "No local or scoped knowledge base evidence matched the selected country, platform, and distribution mode.",
        )
        return {"compliance_report": report}

    formatted_system_prompt = SYSTEM_PROMPT_COMPLIANCE_REVIEWER.format(
        target_country=state.get("target_country", "US"),
        target_region_pack=state.get("target_region_pack", "GLOBAL"),
        target_platform=state.get("target_platform", "tiktok"),
        distribution_mode=state.get("distribution_mode", "branded_content"),
        product_category=state.get("product_category", "general"),
        brand_id=state.get("brand_id", "default"),
        style_prompt=state.get("style_prompt", "No brand style profile provided."),
    )

    user_prompt = f"""Review the following generated marketing script using ONLY the scoped evidence.

SCRIPT TO REVIEW:
{final_script}

SCOPED EVIDENCE:
{_compact_evidence(retrieved_evidence)}

Return strict JSON only.
"""

    try:
        llm = get_llm(temperature=0.2)
        response = llm.invoke(
            [
                SystemMessage(content=formatted_system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        compliance_report = _extract_json_object(response.content)
    except Exception as exc:
        print(f"❌ [Compliance Reviewer] Review failed: {exc}")
        compliance_report = _fallback_report(
            state,
            "The compliance reviewer could not return structured JSON. Please inspect model output or retry.",
        )

    return {"compliance_report": compliance_report}
