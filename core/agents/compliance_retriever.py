from __future__ import annotations

from core.compliance_kb import retrieve_evidence


def run_compliance_retriever(state: dict) -> dict:
    print("📚 [Agent] Compliance Retriever — Looking up local policy, law, and brand evidence...")

    query_text = "\n".join(
        [
            str(state.get("topic", "")),
            str(state.get("final_script", "")),
            str(state.get("style_prompt", "")),
            str(state.get("product_category", "")),
        ]
    )

    scope = {
        "target_country": state.get("target_country", "US"),
        "target_region_pack": state.get("target_region_pack", "GLOBAL"),
        "target_platform": state.get("target_platform", "tiktok"),
        "distribution_mode": state.get("distribution_mode", "branded_content"),
        "product_category": state.get("product_category", "general"),
        "brand_id": state.get("brand_id", "default"),
    }

    retrieved_evidence = retrieve_evidence(query_text=query_text, scope=scope, limit=6)
    print(f"   📎 Retrieved evidence blocks: {len(retrieved_evidence)}")

    return {
        "retrieved_evidence": retrieved_evidence,
        "evidence_count": len(retrieved_evidence),
    }
