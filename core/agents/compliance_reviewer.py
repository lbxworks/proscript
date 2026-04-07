from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Sequence

from langchain_core.messages import HumanMessage, SystemMessage

from core.prompts import SYSTEM_PROMPT_COMPLIANCE_REVIEWER
from utils.llm_client import get_llm, validate_json_response


ALLOWED_STATUSES = {"approved", "needs_revision", "insufficient_evidence"}
ALLOWED_RISKS = {"low", "medium", "high"}
RISK_ORDER = {"low": 1, "medium": 2, "high": 3}


def _extract_json_object(text: str) -> Dict[str, Any]:
    fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    json_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if json_match:
        return json.loads(json_match.group(1))

    raise ValueError("No JSON object found in model response")


def _risk_from_issues(issues: Sequence[Dict[str, Any]]) -> str:
    highest = "low"
    for issue in issues:
        risk = str(issue.get("risk_level", "low")).lower()
        if RISK_ORDER.get(risk, 0) > RISK_ORDER.get(highest, 0):
            highest = risk
    return highest


def _fallback_report(state: dict, reason: str, rule_issues: Sequence[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    issues = list(rule_issues or [])
    if not issues:
        issues = [
            {
                "excerpt": state.get("topic", "") or "No excerpt available",
                "risk_level": "medium",
                "issue_type": "missing_local_evidence",
                "reason": reason,
                "suggested_fix": "Import local law, platform policy, or brand brief files for the selected market and rerun review.",
                "citations": [],
            }
        ]

    return {
        "overall_status": "insufficient_evidence",
        "overall_risk": _risk_from_issues(issues),
        "headline": "Compliance review needs more scoped evidence",
        "overall_commentary": reason,
        "closing_note": "The system kept deterministic rule hits, but you should treat this review as incomplete until more local evidence is indexed.",
        "issues": issues,
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
            f"category={item.get('source_category', 'policy')} | "
            f"type={item.get('source_type', 'policy')} | "
            f"country={item.get('country_code', 'GLOBAL')} | "
            f"platform={item.get('platform', 'all') or 'all'} | "
            f"mode={item.get('distribution_mode', 'all') or 'all'} | "
            f"heading={heading} | "
            f"block={item.get('block_id', 'N/A')} | "
            f"url={source_url}\n"
            f"Excerpt: {item.get('excerpt', '')}"
        )
    return "\n\n".join(lines)


def _normalize_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
    risk_level = str(issue.get("risk_level", "medium")).lower()
    if risk_level not in ALLOWED_RISKS:
        risk_level = "medium"

    citations = []
    for item in issue.get("citations", []) or []:
        citations.append(
            {
                "source_title": item.get("source_title", "Untitled source"),
                "country_code": item.get("country_code", "GLOBAL"),
                "page_num": item.get("page_num", ""),
                "heading_path": item.get("heading_path", ""),
                "block_id": item.get("block_id", ""),
                "source_url": item.get("source_url", ""),
            }
        )

    return {
        "excerpt": issue.get("excerpt", "No excerpt available"),
        "risk_level": risk_level,
        "issue_type": issue.get("issue_type", "local_law"),
        "reason": issue.get("reason", "No reason provided."),
        "suggested_fix": issue.get("suggested_fix", "Revise the wording to make the claim safer and more specific."),
        "citations": citations,
    }


def _merge_issues(primary: Sequence[Dict[str, Any]], secondary: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    seen = set()
    for issue in list(primary) + list(secondary):
        normalized = _normalize_issue(issue)
        key = (normalized["issue_type"], normalized["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(normalized)
    return merged


def _normalize_report(report: Dict[str, Any], rule_issues: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_issues = _merge_issues(report.get("issues", []) or [], rule_issues)
    overall_status = str(report.get("overall_status", "needs_revision")).lower()
    if overall_status not in ALLOWED_STATUSES:
        overall_status = "needs_revision"

    if normalized_issues and overall_status == "approved":
        overall_status = "needs_revision"
    if not normalized_issues and overall_status == "needs_revision":
        overall_status = "approved"

    overall_risk = str(report.get("overall_risk", _risk_from_issues(normalized_issues))).lower()
    if overall_risk not in ALLOWED_RISKS:
        overall_risk = _risk_from_issues(normalized_issues)

    return {
        "overall_status": overall_status,
        "overall_risk": overall_risk,
        "headline": report.get("headline", "Compliance review"),
        "overall_commentary": report.get("overall_commentary", "The script was checked against the scoped compliance evidence and rule engine."),
        "closing_note": report.get("closing_note", "Review the flagged excerpts and apply the suggested revisions before creator delivery."),
        "issues": normalized_issues,
    }


def run_compliance_reviewer(state: dict) -> dict:
    print("🛡️ [Agent] Compliance Reviewer — Synthesizing Qdrant evidence and rule hits into a final report...")

    final_script = str(state.get("final_script", "") or "")
    retrieved_evidence = state.get("retrieved_evidence", []) or []
    rule_issues = state.get("rule_issues", []) or []

    if not final_script.strip():
        report = _fallback_report(state, "The script generator did not produce any content to review.", rule_issues)
        return {"compliance_report": report}

    if not retrieved_evidence:
        report = _fallback_report(
            state,
            "No local or scoped knowledge base evidence matched the selected country, platform, and distribution mode.",
            rule_issues,
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

    user_prompt = f"""Review the following generated marketing script using ONLY the scoped evidence and deterministic rule hits.

SCRIPT TO REVIEW:
{final_script}

RULE HITS:
{json.dumps(rule_issues, ensure_ascii=False, indent=2)}

SCOPED EVIDENCE:
{_compact_evidence(retrieved_evidence)}

Return strict JSON only.
"""

    try:
        llm = get_llm(
            temperature=0.2,
            task_name="compliance_reviewer",
            validator=validate_json_response,
        )
        response = llm.invoke(
            [
                SystemMessage(content=formatted_system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        compliance_report = _extract_json_object(response.content)
        compliance_report = _normalize_report(compliance_report, rule_issues)
    except Exception as exc:
        print(f"❌ [Compliance Reviewer] Review failed: {exc}")
        compliance_report = _fallback_report(
            state,
            "The compliance reviewer could not return structured JSON. The deterministic rule engine findings are preserved below.",
            rule_issues,
        )

    return {"compliance_report": compliance_report}
