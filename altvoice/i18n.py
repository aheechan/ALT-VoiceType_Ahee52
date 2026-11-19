"""Runtime UI language table (Chinese / English)."""

from __future__ import annotations

_LOCALE = "zh"

EN = {
    "ALT-VoiceType": "ALT-VoiceType English",
    "加载中…": "Loading…",
    "加载中...": "Loading…",
    "加载完毕": "Ready",
    "加载完毕，可以开始输入": "Ready to dictate",
    "预热中…": "Warming up…",
    "预热模型": "Warm up models",
    "已预热 · 重新预热": "Warmed up · Warm again",
    "预热 ASR…": "Warming up ASR…",
    "录音中…再按 Alt 结束": "Recording… press Alt again to stop",
    "录音中…松开 Alt 结束": "Recording… release Alt to stop",
    "录音中": "Recording",
    "收尾 0.39 秒…": "Finishing (0.39 s)…",
    "识别中…": "Transcribing…",
    "纠错中…": "Correcting…",
    "翻译中…": "Translating…",
    "已粘贴": "Pasted",
    "结果已复制到剪贴板": "Result copied to clipboard",
    "已取消": "Cancelled",
    "已取消录音": "Recording cancelled",
    "设置": "Settings",
    "历史": "History",
    "环境": "Environment",
    "日志": "Logs",
    "退出": "Quit",
    "输入语言": "Input language",
    "输出语言": "Output language",
    "中文（固定）": "Chinese (fixed)",
    "识别文字": "Recognized text",
    "转译文字": "Translated text",
    "复制识别文字": "Copy recognized text",
    "复制转译文字": "Copy translated text",
    "无内容": "Nothing to copy",
    "已复制 ✓": "Copied ✓",
    "取消": "Cancel",
    "插入": "Insert",
    "打开控制面板…": "Open control panel…",
    "历史与术语…": "History & glossary…",
    "环境检查…": "Health check…",
    "查看日志…": "View logs…",
    "设置…": "Settings…",
    "配置文件位置…": "Config file location…",
    "模型档位": "Model tier",
    "录音快捷键": "Recording hotkey",
    "保存": "Apply",
    "快捷键无效": "Invalid hotkey",
    "快捷键设置失败": "Failed to set hotkey",
    "中文 → 中文 · 直接转写": "Chinese → Chinese · transcription only",
    "中文 → 中文 · 直接转写，不翻译": "Chinese → Chinese · transcription only",
    "识别后显示确认弹窗": "Show confirmation window",
    "识别显示确认弹窗": "Show result window",
    "权限": "Permissions",
    "确认": "OK",
    "中文": "Chinese",
    "英文": "English",
    "EN": "EN",
    "文本翻译器": "Text translator",
    "隐藏翻译器": "Hide translator",
    "文本输入窗": "Text input",
    "文本翻译": "Translation",
    "粘贴文本": "Paste text",
    "自动识别语言": "Auto-detect language",
}


def current_locale() -> str:
    return "en" if _LOCALE == "en" else "zh"


def set_locale(locale: str) -> None:
    global _LOCALE
    _LOCALE = "en" if str(locale).lower().startswith("en") else "zh"


def is_english() -> bool:
    return _LOCALE == "en"


def tr(text: str) -> str:
    if not isinstance(text, str) or not is_english():
        return text
    return EN.get(text, text)
