from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Sequence


DISCLOSURE_KEYWORDS = [
    "#ad",
    "#advertisement",
    "#sponsored",
    "#paidpartnership",
    "paid partnership",
    "sponsored by",
    "in partnership with",
    "ad:",
    "advertisement",
    "publicidad",
    "contenido de marca",
    "patrocinado",
    "parceria paga",
    "publi",
    "werbung",
    "anzeige",
    "sponsorisé",
    "محتوى برعاية",
    "إعلان",
]

ABSOLUTE_PATTERNS = [
    (r"\b(best|number one|#1|no\.?1|perfect|always|never|guaranteed|guarantee)\b", "absolute_claim"),
    (r"\b(100%|risk[- ]free|completely safe|zero risk|safest)\b", "absolute_claim"),
    (r"\b(miracle|instantly|immediately|overnight)\b", "unsupported_claim"),
    (r"\b(mejor|garantizado|perfecto|siempre|nunca)\b", "absolute_claim"),
    (r"\b(100%|sin riesgo|cura|milagro|instantáneamente)\b", "unsupported_claim"),
    (r"\b(melhor|garantido|perfeito|sempre|nunca)\b", "absolute_claim"),
    (r"\b(cura|milagre|instantaneamente)\b", "unsupported_claim"),
    (r"\b(meilleur|garanti|parfait|toujours|jamais)\b", "absolute_claim"),
    (r"\b(heil|wunder|sofort|garantiert)\b", "unsupported_claim"),
]

SENSITIVE_CLAIM_PATTERNS = [
    r"\b(cure|treat|heal|prevent|diagnose|weight loss|fat burn|anti[- ]aging|clinically proven)\b",
    r"\b(curar|tratar|prevenir|pérdida de peso|anti edad|clínicamente probado)\b",
    r"\b(curar|tratar|prevenir|perda de peso|anti idade|clinicamente comprovado)\b",
    r"\b(guérir|traiter|prévenir|perte de poids|anti[- ]âge)\b",
    r"\b(heilen|behandeln|vorbeugen|gewichtsverlust|klinisch bewiesen)\b",
    r"\b(يعالج|يشفي|يمنع|إنقاص الوزن|مثبت سريريًا)\b",
]


def _flatten_script_lines(script: str) -> List[str]:
    lines: List[str] = []
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if set(line) <= {"|", "-", " "}:
            continue
        if line.startswith("### "):
            continue
        if line.startswith("**") and line.endswith("**"):
            continue
        if "|" in line:
            cells = [cell.strip() for cell in line.split("|") if cell.strip()]
            lines.extend(cells)
            continue
        lines.append(line)
    return lines


def _find_excerpt(lines: Sequence[str], pattern: str) -> str:
    compiled = re.compile(pattern, flags=re.IGNORECASE)
    for line in lines:
        if compiled.search(line):
            return line
    return ""


def _citation_from_evidence(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_title": item.get("source_title", "Untitled source"),
        "country_code": item.get("country_code", "GLOBAL"),
        "page_num": item.get("page_num", ""),
        "heading_path": item.get("heading_path", ""),
        "block_id": item.get("block_id", ""),
        "source_url": item.get("source_url", ""),
    }


def _pick_citations(
    evidence: Sequence[Dict[str, Any]],
    *,
    source_categories: Iterable[str] | None = None,
    preferred_terms: Iterable[str] | None = None,
    max_count: int = 2,
) -> List[Dict[str, Any]]:
    category_set = {item.lower() for item in (source_categories or [])}
    preferred_terms_normalized = [term.lower() for term in (preferred_terms or []) if term]

    scored: List[tuple[int, Dict[str, Any]]] = []
    for item in evidence:
        score = int(item.get("score", 0))
        if category_set and str(item.get("source_category", "")).lower() in category_set:
            score += 15
        excerpt = str(item.get("excerpt", "")).lower()
        title = str(item.get("source_title", "")).lower()
        for term in preferred_terms_normalized:
            if term in excerpt or term in title:
                score += 8
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [_citation_from_evidence(item) for _, item in scored[:max_count]]


def _issue(
    *,
    excerpt: str,
    risk_level: str,
    issue_type: str,
    reason: str,
    suggested_fix: str,
    citations: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "excerpt": excerpt or "No exact excerpt available",
        "risk_level": risk_level,
        "issue_type": issue_type,
        "reason": reason,
        "suggested_fix": suggested_fix,
        "citations": list(citations),
    }


def evaluate_rules(state: Dict[str, Any], evidence: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    final_script = str(state.get("final_script", "") or "")
    distribution_mode = str(state.get("distribution_mode", "branded_content")).lower()
    product_category = str(state.get("product_category", "general")).lower()
    target_platform = str(state.get("target_platform", "tiktok")).lower()

    lines = _flatten_script_lines(final_script)
    lowered_script = final_script.lower()
    issues: List[Dict[str, Any]] = []

    if distribution_mode in {"branded_content", "paid_ads"}:
        has_disclosure = any(keyword in lowered_script for keyword in DISCLOSURE_KEYWORDS)
        if not has_disclosure:
            disclosure_hint = {
                "tiktok": "Add a clear paid partnership disclosure in the opening hook and caption, such as `Paid partnership with <brand>` or `#ad`.",
                "instagram": "Use a clear `Paid partnership` disclosure in the reel and caption before product claims.",
                "youtube": "Include an on-screen sponsorship disclosure and a clear paid promotion label in the script.",
                "x": "Add a clear ad or sponsorship disclosure before the promotional claim appears.",
                "reddit": "Add an explicit sponsorship disclosure and confirm the community allows promotional posts before publishing.",
                "discord": "Add a clear sponsor disclosure and avoid dropping undisclosed ads into community channels.",
            }.get(target_platform, "Add a clear sponsorship disclosure before the promotional claim appears.")

            issues.append(
                _issue(
                    excerpt=lines[0] if lines else "No excerpt available",
                    risk_level="high" if distribution_mode == "paid_ads" else "medium",
                    issue_type="disclosure",
                    reason="The draft looks promotional but does not include a visible sponsorship or branded-content disclosure.",
                    suggested_fix=disclosure_hint,
                    citations=_pick_citations(
                        evidence,
                        source_categories={"platform_policy", "market_law"},
                        preferred_terms=["disclosure", "advertising", "branded content", "paid partnership"],
                    ),
                )
            )

    for pattern, issue_type in ABSOLUTE_PATTERNS:
        excerpt = _find_excerpt(lines, pattern)
        if not excerpt:
            continue
        issues.append(
            _issue(
                excerpt=excerpt,
                risk_level="high" if issue_type == "unsupported_claim" else "medium",
                issue_type="unsupported_claim" if issue_type == "unsupported_claim" else "local_law",
                reason="This line uses absolute or certainty-heavy language that often needs stronger substantiation or softer wording in ad copy.",
                suggested_fix="Replace the absolute wording with measured, supportable language and keep the claim tied to verifiable product facts.",
                citations=_pick_citations(
                    evidence,
                    source_categories={"market_law"},
                    preferred_terms=["misleading", "deceptive", "advertising", "commercial practice"],
                ),
            )
        )

    if product_category in {"health_supplement", "beauty", "food_beverage"}:
        for pattern in SENSITIVE_CLAIM_PATTERNS:
            excerpt = _find_excerpt(lines, pattern)
            if not excerpt:
                continue
            issues.append(
                _issue(
                    excerpt=excerpt,
                    risk_level="high",
                    issue_type="unsupported_claim",
                    reason="This looks like a health, efficacy, or treatment claim for a sensitive product category and usually requires strong evidence plus careful wording.",
                    suggested_fix="Remove the medical or therapeutic promise unless you have market-specific substantiation. Reframe it as a softer user benefit or product description.",
                    citations=_pick_citations(
                        evidence,
                        source_categories={"market_law"},
                        preferred_terms=["misleading", "health", "safety", "claims"],
                    ),
                )
            )

    deduped: List[Dict[str, Any]] = []
    seen = set()
    for issue in issues:
        key = (issue["issue_type"], issue["excerpt"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
