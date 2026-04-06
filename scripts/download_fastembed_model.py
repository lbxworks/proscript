from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.compliance_store import EMBED_MODEL_NAME, Embedder, _prepare_fastembed_model_dir


def main() -> None:
    model_dir = _prepare_fastembed_model_dir(EMBED_MODEL_NAME)
    embedder = Embedder()
    vectors = embedder.embed(["hola mundo", "paid partnership with brand"])
    print(
        json.dumps(
            {
                "model_name": EMBED_MODEL_NAME,
                "model_dir": str(model_dir),
                "backend": embedder.backend_name,
                "vector_count": len(vectors),
                "dimension": len(vectors[0]) if vectors else 0,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
