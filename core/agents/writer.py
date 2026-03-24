# core/agents/writer.py
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm_client import get_llm
from core.prompts import SYSTEM_PROMPT_WRITER


def run_writer(state: dict) -> dict:
    print("🎬 [Agent] Script Writer — Generating Sequence of Multi-Language Scripts...")

    # Extract all context and configuration from state
    topic           = state.get("topic", "")
    style_prompt    = state.get("style_prompt", "Professional, cinematic style")
    trend_data      = state.get("trend_data", "No trend data available")
    video_duration  = state.get("video_duration", "60s (Immersive)")
    target_platform = state.get("target_platform", "TikTok")
    creativity      = state.get("creativity", 0.7)

    # Dynamic target languages: read exactly what user selected, in order
    target_languages = state.get("target_languages", ["English"])
    if not target_languages:
        target_languages = ["English"]
    
    target_languages_str = ", ".join(target_languages)
    language_count = len(target_languages)
    
    # Build dynamic phase instructions
    language_instructions = ""
    for i, lang in enumerate(target_languages):
        language_instructions += f"  - **Phase {i+1}**: Draft the full script table in **{lang}**.\n"
    
    print(f"   📝 Language target order: {target_languages_str}")

    # Format the system prompt with all required variables
    formatted_system_prompt = SYSTEM_PROMPT_WRITER.format(
        topic=topic,
        style_prompt=style_prompt,
        trend_data=trend_data,
        target_platform=target_platform,
        video_duration=video_duration,
        target_languages=target_languages_str,
        language_count=language_count,
        language_instructions=language_instructions,
    )

    user_prompt = f"""Generate a complete professional shooting script for the following video:

**Topic**: {topic}
**Platform**: {target_platform}
**Duration**: {video_duration}

IMPORTANT: You MUST output {language_count} complete versions in EXACT sequence:
{language_instructions}

All {language_count} tables must have identical Time Codes, Scene numbers, and technical details.
Translate the table column headers into the respective target language for each version.
Use the creator style profile and trend intelligence already embedded in your system context.
Output the full sequence of Markdown shooting scripts now. Do NOT skip any scenes or languages!
"""

    try:
        llm = get_llm(temperature=creativity)
        messages = [
            SystemMessage(content=formatted_system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        final_script = response.content
        print(f"✅ [Writer Agent] Multi-language script sequence generated ({language_count} languages).")
    except Exception as e:
        print(f"❌ [Writer Agent] LLM generation failed: {e}")
        final_script = f"**Script Generation Failed**\n\nError: `{e}`"

    return {"final_script": final_script}