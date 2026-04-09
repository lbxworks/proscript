from __future__ import annotations

from pathlib import Path
from typing import Any

from core.compliance_kb import get_knowledge_index_status, initialize_knowledge_runtime


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_ROOT = PROJECT_ROOT / "data" / "knowledge_base"


def get_library_health(*, initialize: bool = False) -> dict[str, Any]:
    runtime_status = (
        initialize_knowledge_runtime(force_rebuild=False)
        if initialize
        else get_knowledge_index_status()
    )
    return {
        **runtime_status,
        "knowledge_base_root": str(KNOWLEDGE_BASE_ROOT),
        "raw_root": str(KNOWLEDGE_BASE_ROOT / "raw"),
        "processed_root": str(KNOWLEDGE_BASE_ROOT / "processed"),
    }
