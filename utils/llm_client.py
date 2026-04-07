from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:  # pragma: no cover - handled at runtime with clear error
    ChatGoogleGenerativeAI = None


logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / ".env"

print(f"🔍 正在尝试加载配置: {env_path}")
is_loaded = load_dotenv(dotenv_path=env_path, override=True)
if not is_loaded:
    print("⚠️ 警告: load_dotenv 返回 False，可能文件不存在或为空！")


DEFAULT_PRIMARY_PROVIDER = "google"
DEFAULT_FALLBACK_PROVIDER = "deepseek"
DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"
FAILOVER_TARGET_SECONDS = 2.0

_thread_state = threading.local()


class InvalidLLMResponseError(ValueError):
    """Raised when a model response is syntactically present but unusable for the task."""


def _mask_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:6]}...{api_key[-4:]}"


def _normalize_provider(provider: str | None) -> str:
    return (provider or "").strip().lower()


def _set_last_invocation(provider: str, model_name: str, *, fallback_used: bool, task_name: str):
    _thread_state.last_invocation = {
        "provider": provider,
        "model_name": model_name,
        "fallback_used": fallback_used,
        "task_name": task_name,
        "timestamp": time.time(),
    }


def clear_last_llm_invocation() -> None:
    _thread_state.last_invocation = None


def get_last_llm_invocation() -> dict[str, Any]:
    payload = getattr(_thread_state, "last_invocation", None)
    return dict(payload or {})


def validate_non_empty_response(response: Any) -> bool:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        content = " ".join(str(item) for item in content)
    return bool(str(content or "").strip())


def validate_markdown_table_response(response: Any) -> bool:
    content = getattr(response, "content", response)
    text = str(content or "").strip()
    if not text:
        return False
    has_timecode = bool(re.search(r"\[\d{2}:\d{2}-\d{2}:\d{2}\]", text))
    has_table = text.count("|") >= 8 and "|---" in text
    return has_timecode and has_table


def validate_json_response(response: Any) -> bool:
    content = getattr(response, "content", response)
    text = str(content or "").strip()
    if not text:
        return False

    fenced_match = re.search(r"```json\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    candidate = fenced_match.group(1) if fenced_match else None
    if not candidate:
        json_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        candidate = json_match.group(1) if json_match else None
    if not candidate:
        return False
    try:
        json.loads(candidate)
        return True
    except json.JSONDecodeError:
        return False


def _get_primary_provider() -> str:
    provider = _normalize_provider(os.getenv("LLM_PROVIDER"))
    if provider:
        return provider
    if os.getenv("GOOGLE_API_KEY"):
        return "google"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return DEFAULT_PRIMARY_PROVIDER


def _get_fallback_provider(primary_provider: str) -> str | None:
    configured = _normalize_provider(os.getenv("LLM_FALLBACK_PROVIDER"))
    if configured:
        return configured
    if primary_provider == "google" and os.getenv("DEEPSEEK_API_KEY"):
        return DEFAULT_FALLBACK_PROVIDER
    if primary_provider == "deepseek" and (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        return "google"
    return None


def _build_google_llm(temperature: float):
    if ChatGoogleGenerativeAI is None:
        raise ImportError(
            "缺少依赖 `langchain-google-genai`。请先安装 requirements.txt 中的新依赖。"
        )

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("未检测到 GOOGLE_API_KEY / GEMINI_API_KEY，请检查 .env 配置。")

    model_name = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL).strip() or DEFAULT_GOOGLE_MODEL
    print(f"🔑 [Google] 检测到 Key: {_mask_key(api_key)}")
    print(f"🤖 [Google] 当前模型: {model_name}")

    kwargs = {
        "model": model_name,
        "api_key": api_key,
        "temperature": temperature,
        "retries": 1,
        "request_timeout": 12,
    }
    if model_name.startswith("gemini-2.5"):
        kwargs["thinking_budget"] = 0

    return ChatGoogleGenerativeAI(**kwargs)


def _build_deepseek_llm(temperature: float):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未检测到 DEEPSEEK_API_KEY，请检查 .env 配置。")

    model_name = os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL
    print(f"🔑 [DeepSeek] 检测到 Key: {_mask_key(api_key)}")
    print(f"🤖 [DeepSeek] 当前模型: {model_name}")

    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com",
        temperature=temperature,
        timeout=60,
        max_retries=1,
    )


def _build_provider_llm(provider: str, temperature: float):
    normalized = _normalize_provider(provider)
    if normalized == "google":
        llm = _build_google_llm(temperature)
        model_name = os.getenv("GOOGLE_MODEL", DEFAULT_GOOGLE_MODEL).strip() or DEFAULT_GOOGLE_MODEL
        return llm, model_name
    if normalized == "deepseek":
        llm = _build_deepseek_llm(temperature)
        model_name = os.getenv("DEEPSEEK_MODEL", DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL
        return llm, model_name
    raise ValueError(f"不支持的 provider: {provider}")


class ResilientLLM:
    def __init__(
        self,
        *,
        temperature: float,
        task_name: str = "general",
        validator: Callable[[Any], bool] | None = None,
    ):
        self.temperature = temperature
        self.task_name = task_name
        self.validator = validator or validate_non_empty_response
        self.primary_provider = _get_primary_provider()
        self.fallback_provider = _get_fallback_provider(self.primary_provider)

    def _validate_response(self, response: Any, provider: str):
        if not self.validator(response):
            raise InvalidLLMResponseError(
                f"{provider} returned an invalid response for task `{self.task_name}`."
            )

    def invoke(self, messages: Any, *args, **kwargs):
        clear_last_llm_invocation()

        primary_started = time.monotonic()
        primary_exc: Exception | None = None

        try:
            primary_llm, primary_model = _build_provider_llm(self.primary_provider, self.temperature)
            response = primary_llm.invoke(messages, *args, **kwargs)
            self._validate_response(response, self.primary_provider)
            _set_last_invocation(
                self.primary_provider,
                primary_model,
                fallback_used=False,
                task_name=self.task_name,
            )
            return response
        except Exception as exc:
            primary_exc = exc
            elapsed = time.monotonic() - primary_started
            logger.info(
                "[INFO] Primary LLM failed: provider=%s task=%s elapsed=%.2fs reason=%s",
                self.primary_provider,
                self.task_name,
                elapsed,
                exc,
            )
            if not self.fallback_provider:
                raise

            logger.info(
                "[INFO] Fallback triggered: %s -> %s | task=%s | elapsed=%.2fs | target<=%.1fs",
                self.primary_provider.title(),
                self.fallback_provider.title(),
                self.task_name,
                elapsed,
                FAILOVER_TARGET_SECONDS,
            )

        fallback_llm, fallback_model = _build_provider_llm(self.fallback_provider, self.temperature)
        response = fallback_llm.invoke(messages, *args, **kwargs)
        self._validate_response(response, self.fallback_provider)
        _set_last_invocation(
            self.fallback_provider,
            fallback_model,
            fallback_used=True,
            task_name=self.task_name,
        )
        return response


def get_llm(
    temperature: float = 0.7,
    *,
    task_name: str = "general",
    validator: Callable[[Any], bool] | None = None,
):
    """
    返回带有主从切换能力的 LLM 包装器。

    默认策略：
    1. 优先 Google
    2. Google 失败时自动回退到 DeepSeek
    """
    primary = _get_primary_provider()
    fallback = _get_fallback_provider(primary)
    print(f"🧠 当前 LLM 策略: primary={primary} fallback={fallback or 'none'}")
    return ResilientLLM(
        temperature=temperature,
        task_name=task_name,
        validator=validator,
    )


if __name__ == "__main__":
    print("🔄 正在尝试连接当前默认 LLM...")
    try:
        llm = get_llm(task_name="connectivity_check")
        response = llm.invoke("你好，请回复“系统连接成功”。")
        print(f"✅ 测试通过: {response.content}")
        print(f"ℹ️ 最终使用模型: {get_last_llm_invocation()}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
