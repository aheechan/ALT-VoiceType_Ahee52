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

SYSTEM_PROMPT = """你是目标语言的母语者，不是在翻译文件。

你的任务是把说话人的一句口语，变成目标语言里真人会说的话：
- 保留情绪、语气、停顿、犹豫、幽默和意图；
- 用日常表达，不要书面腔、不要翻译腔、不要“首先/其次/总之”；
- 不要解释、不要扩写、不要补充原文没有的信息；
- 人名、数字、代码、专有名词按原文或术语表；
- 只输出译文本身，不要引号，不要标签，不要 Markdown。"""


def _format_context(context: list[dict[str, str]] | None) -> str:
    if not context:
        return "（无）"
    lines: list[str] = []
    for item in context[-3:]:
        source = (item.get("corrected") or item.get("source") or "").strip()
        translation = (item.get("translation") or "").strip()
        if source and translation:
            lines.append(f"- 原文：{source}\n  译文：{translation}")
        elif source:
            lines.append(f"- 原文：{source}")
    return "\n".join(lines) if lines else "（无）"


def _format_glossary(glossary: dict[str, str] | None) -> str:
    if not glossary:
        return "（无）"
    return "\n".join(f"- {k} -> {v}" for k, v in list(glossary.items())[:80])


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
    user = f"""目标语言：{target}
风格：{style_text}
源语言：{source_lang}

【上文】
{_format_context(context)}

【术语表】
{_format_glossary(glossary)}

【当前口语】
{text}

只输出{target}译文。"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def clean_translation(text: str) -> str:
    result = (text or "").strip()
    if result.startswith("```") and result.endswith("```"):
        lines = result.splitlines()
        if len(lines) >= 3:
            result = "\n".join(lines[1:-1]).strip()
    for prefix in ("译文：", "译文:", "Translation:", "翻译："):
        if result.startswith(prefix):
            result = result[len(prefix) :].strip()
    return result.strip().strip('"').strip("“”").strip()
