from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import GenerateScriptRequest, ReviewScriptRequest
from backend.services.library import get_library_health
from backend.services.scripts import generate_script, review_script
from backend.services.trends import explore_trends


app = FastAPI(
    title="Pro-Script AI Backend",
    version="0.1.0",
    description="Backend service interfaces extracted from the original Streamlit app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scripts/generate")
def generate_script_endpoint(payload: GenerateScriptRequest):
    try:
        return generate_script(payload)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scripts/review")
def review_script_endpoint(payload: ReviewScriptRequest):
    try:
        return review_script(payload)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/trends")
def trends_endpoint(
    topic: str | None = None,
    target_country: str = "US",
    target_platform: str = "tiktok",
    distribution_mode: str = "branded_content",
    product_category: str = "general",
    target_languages: list[str] = Query(default=["English"]),
):
    try:
        return explore_trends(
            topic=topic,
            target_country=target_country,
            target_platform=target_platform,
            distribution_mode=distribution_mode,
            product_category=product_category,
            target_languages=target_languages,
        )
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/library/health")
def library_health_endpoint(initialize: bool = False):
    try:
        return get_library_health(initialize=initialize)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc
