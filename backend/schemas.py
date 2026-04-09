from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateScriptRequest(BaseModel):
    user_id: int
    topic: str = Field(min_length=1)
    target_languages: list[str] = Field(default_factory=lambda: ["English"])
    video_duration: str = "60s (Immersive)"
    target_platform: str = "tiktok"
    target_country: str = "US"
    distribution_mode: str = "branded_content"
    product_category: str = "general"
    brand_id: str = "default"
    creativity: float = 0.8
    persist_result: bool = True


class ReviewScriptRequest(BaseModel):
    script: str = Field(min_length=1)
    topic: str | None = None
    user_id: int | None = None
    style_prompt: str | None = None
    target_languages: list[str] = Field(default_factory=lambda: ["English"])
    target_platform: str = "tiktok"
    target_country: str = "US"
    distribution_mode: str = "branded_content"
    product_category: str = "general"
    brand_id: str = "default"
