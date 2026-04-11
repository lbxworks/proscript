from __future__ import annotations

import queue
import threading
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from typing import Any

from fastapi import Request


EmitCallback = Callable[[str, dict[str, Any]], None]


class ProgressStepError(Exception):
    def __init__(
        self,
        *,
        step: str,
        message: str,
        error_type: str = "workflow_error",
    ) -> None:
        super().__init__(message)
        self.step = step
        self.message = message
        self.error_type = error_type


def format_sse(event: str, data: dict[str, Any]) -> str:
    import json

    payload = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


async def stream_task(
    *,
    request: Request,
    worker: Callable[[EmitCallback], dict[str, Any]],
) -> AsyncIterator[str]:
    event_queue: queue.Queue[tuple[str, dict[str, Any]] | None] = queue.Queue()

    def emit(event: str, payload: dict[str, Any]) -> None:
        event_queue.put((event, payload))

    def run_worker() -> None:
        try:
            result = worker(emit)
            emit("complete", {"result": result})
        except ProgressStepError as exc:
            emit(
                "error",
                {
                    "step": exc.step,
                    "status": "error",
                    "error_type": exc.error_type,
                    "message": exc.message,
                },
            )
        except Exception:
            emit(
                "error",
                {
                    "step": "system",
                    "status": "error",
                    "error_type": "workflow_error",
                    "message": "流程中断了，请稍后重新开始。",
                },
            )
        finally:
            event_queue.put(None)

    threading.Thread(target=run_worker, daemon=True).start()

    while True:
        if await request.is_disconnected():
            break

        try:
            item = event_queue.get(timeout=15)
        except queue.Empty:
            heartbeat_at = datetime.now(timezone.utc).isoformat()
            yield format_sse("heartbeat", {"timestamp": heartbeat_at})
            continue

        if item is None:
            break

        event, payload = item
        yield format_sse(event, payload)
