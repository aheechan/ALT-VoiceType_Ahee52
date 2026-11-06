"""Prompt construction for natural, context-aware translation."""

from __future__ import annotations

from ..config import language_prompt_name

STYLE_PRESETS: dict[str, str] = {
    "daily": (
        "日常口语。像朋友聊天一样自然，保留语气词、停顿和情绪；"
        "不要书面腔，不要翻译腔，不要总结。"
    ),
    "live": (
        "直播/短视频口播。句子短、节奏快、有能量，保留主播的语气和互动感；"
        "不要像新闻稿。"
    ),
    "business": (
        "商务沟通。礼貌、清楚、简洁，但不僵硬；不要堆砌套话，不要过度正式。"
    ),
    "game": (
        "游戏角色台词。符合角色语气，短句优先，允许口语和俚语；"
        "不要解释设定。"
    ),
    "subtitle": (
        "字幕。表达清楚、可读性优先，长度尽量紧凑；"
        "保留原意和情绪，不要逐字硬译。"
    ),
}

SYSTEM_PROMPT = """你是口译员，不是在翻译文件。把用户的中文口语翻成目标语言，只输出译文本身。
不要输出原文、标题、标签、解释、引号或 Markdown。译文要自然、口语化，保留情绪、语气和停顿。"""


def _format_context(context: list[dict[str, str]] | None) -> str:
    if not context:
        return ""
    lines: list[str] = []
    for item in context[-2:]:
        source = (item.get("corrected") or item.get("source") or "").strip()
        translation = (item.get("translation") or "").strip()
        if source and translation:
            lines.append(f"{source} => {translation}")
        elif source:
            lines.append(source)
    return "\n".join(lines)


def _format_glossary(glossary: dict[str, str] | None) -> str:
    if not glossary:
        return ""
    return "\n".join(f"{k} => {v}" for k, v in list(glossary.items())[:80])


def build_translation_messages(
    text: str,
    target_lang: str,
    context: list[dict[str, str]] | None = None,
    style: str = "daily",
    glossary: dict[str, str] | None = None,
    source_lang: str = "zh",
) -> list[dict[str, str]]:
    style_text = STYLE_PRESETS.get(style, STYLE_PRESETS["daily"])
    target = language_prompt_name(target_lang)
    parts = [
        f"目标语言：{target}",
        f"风格：{style_text}",
    ]
    glossary_text = _format_glossary(glossary)
    if glossary_text:
        parts.append(f"术语：\n{glossary_text}")
    parts.append(f"原文：\n{text}")
    parts.append("只输出译文，不要输出“原文”或“译文”标题。")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def clean_translation(text: str) -> str:
    import re

    result = (text or "").strip()
    if result.startswith("```") and result.endswith("```"):
        lines = result.splitlines()
        if len(lines) >= 3:
            result = "\n".join(lines[1:-1]).strip()
    # Models sometimes echo "原文：...\n译文：..." despite the instruction.
    for marker in ("译文：", "译文:", "Translation:", "翻译：", "Output:"):
        if marker in result:
            result = result.rsplit(marker, 1)[-1].strip()
    result = re.sub(
        r"^\s*(?:\*\*)?\s*(?:原文|译文|翻译|Translation|Source|Target|Output)\s*[:：]\s*(?:\*\*)?\s*",
        "",
        result,
        flags=re.IGNORECASE,
    )
    result = re.sub(r"</?(?:source|target|context|glossary)>", "", result, flags=re.IGNORECASE)
    return result.strip().strip("*").strip('"').strip("“”").strip()
