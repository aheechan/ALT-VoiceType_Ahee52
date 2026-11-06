"""Prompt construction and tolerant parsing for ASR correction."""

from __future__ import annotations

import json
import re
from typing import Any

SYSTEM_PROMPT = """你是中文语音转写校对器。你的任务不是润色，而是修正语音识别错误。

只允许修改：
1. 同音字、近音字、错别字；
2. 明显的断句和标点错误；
3. 重复词、口吃、无意义语气词；
4. 人名、地名、产品名、术语的写法（优先使用【术语表】）；
5. 中英文混说时的明显识别错误。

严禁：
- 改变原意、增加原文没有的信息；
- 扩写、缩写、总结、解释；
- 改变说话人的语气和风格；
- 把口语改成书面语。

如果无法确定，保留原文。输出必须是合法 JSON：
{"text": "校对后的文本", "risk": 0.0, "edits": [{"from": "错", "to": "对", "reason": "同音字"}]}
risk 取 0 到 1；不确定时给高风险。"""


def _format_context(context: list[dict[str, str]] | None) -> str:
    if not context:
        return "（无）"
    lines: list[str] = []
    for item in context[-6:]:
        source = (item.get("source") or "").strip()
        corrected = (item.get("corrected") or "").strip()
        if source and corrected and source != corrected:
            lines.append(f"- 原文：{source}\n  校对：{corrected}")
        elif corrected:
            lines.append(f"- {corrected}")
    return "\n".join(lines) if lines else "（无）"


def _format_glossary(glossary: dict[str, str] | None) -> str:
    if not glossary:
        return "（无）"
    return "\n".join(f"- {k} -> {v}" for k, v in list(glossary.items())[:80])


def build_correction_messages(
    text: str,
    context: list[dict[str, str]] | None = None,
    glossary: dict[str, str] | None = None,
    scene: str = "daily",
) -> list[dict[str, str]]:
    user = f"""场景：{scene}

【最近上下文】
{_format_context(context)}

【术语表】
{_format_glossary(glossary)}

【当前 ASR 原文】
{text}

请只修正识别错误，输出 JSON。"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def parse_correction_response(response: str, original: str) -> dict[str, Any]:
    """Parse the model JSON, tolerating code fences and surrounding prose."""
    raw = (response or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    data: Any = None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                data = None
    if not isinstance(data, dict):
        return {"text": original, "risk": 1.0, "edits": [], "parse_error": True}
    text = data.get("text") or data.get("corrected") or original
    try:
        risk = float(data.get("risk", 0.0))
    except (TypeError, ValueError):
        risk = 1.0
    edits = data.get("edits") or []
    if not isinstance(edits, list):
        edits = []
    return {
        "text": str(text).strip() or original,
        "risk": max(0.0, min(1.0, risk)),
        "edits": [e for e in edits if isinstance(e, dict)],
        "parse_error": False,
    }
