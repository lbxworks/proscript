from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.compliance_store import ensure_qdrant_index, get_index_status


def main() -> None:
    result = ensure_qdrant_index(force_rebuild=True)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(get_index_status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
