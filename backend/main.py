from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.database import ensure_database_schema
from backend.schemas import GenerateScriptRequest, ReviewScriptRequest, TalentMutationRequest
from backend.services.library import (
    get_library_health,
    list_library_documents,
    rebuild_library,
    upload_library_document,
)
from backend.services.scripts import generate_script, review_script, stream_generate_script, stream_review_script
from backend.services.streaming import stream_task
from backend.services.talents import create_talent, get_talents, remove_talent, update_talent
from backend.services.trends import explore_trends, stream_explore_trends


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


def _sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


@app.on_event("startup")
def startup_initialize_database() -> None:
    ensure_database_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/talents")
def talents_endpoint():
    try:
        return get_talents()
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/talents")
def create_talent_endpoint(payload: TalentMutationRequest):
    try:
        return create_talent(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.patch("/talents/{talent_id}")
def update_talent_endpoint(talent_id: int, payload: TalentMutationRequest):
    try:
        return update_talent(talent_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/talents/{talent_id}")
def delete_talent_endpoint(talent_id: int):
    try:
        return remove_talent(talent_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scripts/generate")
def generate_script_endpoint(payload: GenerateScriptRequest):
    try:
        return generate_script(payload)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scripts/generate/stream")
async def generate_script_stream_endpoint(request: Request, payload: GenerateScriptRequest):
    return StreamingResponse(
        stream_task(request=request, worker=lambda emit: stream_generate_script(payload, emit)),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@app.post("/scripts/review")
def review_script_endpoint(payload: ReviewScriptRequest):
    try:
        return review_script(payload)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/scripts/review/stream")
async def review_script_stream_endpoint(request: Request, payload: ReviewScriptRequest):
    return StreamingResponse(
        stream_task(request=request, worker=lambda emit: stream_review_script(payload, emit)),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@app.get("/trends")
def trends_endpoint(
    topic: str | None = None,
    target_country: str = "US",
    target_platform: str = "tiktok",
    distribution_mode: str = "branded_content",
    product_category: str = "general",
    target_languages: list[str] = Query(default=["English"]),
    refresh_videos: bool = False,
    refresh_industry: bool = False,
):
    try:
        return explore_trends(
            topic=topic,
            target_country=target_country,
            target_platform=target_platform,
            distribution_mode=distribution_mode,
            product_category=product_category,
            target_languages=target_languages,
            refresh_videos=refresh_videos,
            refresh_industry=refresh_industry,
        )
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/trends/stream")
async def trends_stream_endpoint(
    request: Request,
    topic: str | None = None,
    target_country: str = "US",
    target_platform: str = "tiktok",
    distribution_mode: str = "branded_content",
    product_category: str = "general",
    target_languages: list[str] = Query(default=["English"]),
    refresh_videos: bool = False,
    refresh_industry: bool = False,
):
    return StreamingResponse(
        stream_task(
            request=request,
            worker=lambda emit: stream_explore_trends(
                topic=topic,
                target_country=target_country,
                target_platform=target_platform,
                distribution_mode=distribution_mode,
                product_category=product_category,
                target_languages=target_languages,
                refresh_videos=refresh_videos,
                refresh_industry=refresh_industry,
                emit=emit,
            ),
        ),
        media_type="text/event-stream",
        headers=_sse_headers(),
    )


@app.get("/library/health")
def library_health_endpoint(initialize: bool = False):
    try:
        return get_library_health(initialize=initialize)
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/library/documents")
def library_documents_endpoint():
    try:
        return list_library_documents()
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/library/rebuild")
def library_rebuild_endpoint():
    try:
        return rebuild_library()
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/library/upload")
async def library_upload_endpoint(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("platform_policy"),
    market: str = Form("GLOBAL"),
    region: str = Form("GLOBAL"),
    platform: str = Form("all"),
    language: str = Form("en"),
    source_url: str = Form(""),
    notes: str = Form(""),
    priority: str = Form("P2"),
):
    try:
        content = await file.read()
        return upload_library_document(
            filename=file.filename or "upload.bin",
            content=content,
            title=title,
            category=category,
            market=market,
            region=region,
            platform=platform,
            language=language,
            source_url=source_url,
            notes=notes,
            priority=priority,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - exercised through integration runs
        raise HTTPException(status_code=500, detail=str(exc)) from exc
