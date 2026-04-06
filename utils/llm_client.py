from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:  # pragma: no cover - handled at runtime with clear error
    ChatGoogleGenerativeAI = None


current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
env_path = project_root / ".env"

print(f"🔍 正在尝试加载配置: {env_path}")
is_loaded = load_dotenv(dotenv_path=env_path, override=True)
if not is_loaded:
    print("⚠️ 警告: load_dotenv 返回 False，可能文件不存在或为空！")


DEFAULT_PROVIDER = "google"
DEFAULT_GOOGLE_MODEL = "gemini-2.5-flash"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"


def _mask_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 10:
        return "*" * len(api_key)
    return f"{api_key[:6]}...{api_key[-4:]}"


def _get_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    if os.getenv("GOOGLE_API_KEY"):
        return "google"
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    return DEFAULT_PROVIDER


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
        "retries": 2,
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
    )


def get_llm(temperature: float = 0.7):
    """
    获取配置好的 LLM 实例。

    优先级：
    1. `LLM_PROVIDER`
    2. 如果存在 `GOOGLE_API_KEY`，默认走 Google Gemini
    3. 否则回退到 DeepSeek
    """
    provider = _get_provider()
    print(f"🧠 当前 LLM Provider: {provider}")

    if provider == "google":
        return _build_google_llm(temperature)
    if provider == "deepseek":
        return _build_deepseek_llm(temperature)

    raise ValueError(f"不支持的 LLM_PROVIDER: {provider}")


if __name__ == "__main__":
    print("🔄 正在尝试连接当前默认 LLM...")
    try:
        llm = get_llm()
        response = llm.invoke("你好，请回复“系统连接成功”。")
        print(f"✅ 测试通过: {response.content}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
