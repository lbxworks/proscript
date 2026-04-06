from __future__ import annotations

from core.compliance_rules import evaluate_rules


def run_compliance_rule_engine(state: dict) -> dict:
    print("🧪 [Agent] Compliance Rule Engine — Running deterministic checks for disclosure and risky claims...")

    retrieved_evidence = state.get("retrieved_evidence", []) or []
    rule_issues = evaluate_rules(state, retrieved_evidence)
    print(f"   🔍 Rule hits: {len(rule_issues)}")

    return {"rule_issues": rule_issues}
