"""Runtime English UI translation for the English edition.

The Chinese edition is untouched.  For the English build we translate the
small set of user-visible Qt strings at the widget boundary, which keeps the
two editions on one code path.
"""

from __future__ import annotations

import re

from ..edition import is_english

EN = {
    "加载中…": "Loading…",
    "加载中...": "Loading…",
    "预热中…": "Warming up…",
    "预热 ASR…": "Warming up ASR…",
    "预热模型": "Warm up models",
    "已预热 · 重新预热": "Warmed up · Warm again",
    "录音中…再按 Alt 结束": "Recording… press Alt again to stop",
    "录音中…松开 Alt 结束": "Recording… release Alt to stop",
    "收尾 0.39 秒…": "Finishing (0.39 s)…",
    "识别中…": "Transcribing…",
    "纠错中…": "Correcting…",
    "翻译中…": "Translating…",
    "加载完毕，可以开始输入": "Ready to dictate",
    "已粘贴": "Pasted",
    "结果已复制到剪贴板": "Result copied to clipboard",
    "已取消": "Cancelled",
    "已取消录音": "Recording cancelled",
    "识别文字": "Recognized text",
    "转译文字": "Translated text",
    "复制识别文字": "Copy recognized text",
    "复制转译文字": "Copy translated text",
    "无内容": "Nothing to copy",
    "已复制 ✓": "Copied ✓",
    "输入语言": "Input language",
    "输出语言": "Output language",
    "中文（固定）": "English (fixed)",
    "设置": "Settings",
    "历史": "History",
    "环境": "Environment",
    "日志": "Logs",
    "退出": "Quit",
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
    "取消": "Cancel",
    "插入": "Insert",
    "确认": "OK",
}


def tr(text: str) -> str:
    if not is_english() or not isinstance(text, str):
        return text
    if text in EN:
        return EN[text]
    result = text
    if result.startswith("错误："):
        result = "Error: " + result[3:]
    if result.startswith("输出语言："):
        result = "Output language: " + result[5:]
    if result.startswith("加载 ASR"):
        result = "Loading ASR" + result[6:]
    if result.startswith("切换 "):
        result = "Switching " + result[3:]
    result = result.replace("开始/停止", "start/stop")
    result = result.replace("中文 → 中文", "English → English")
    result = result.replace("中文（固定）", "English (fixed)")
    result = result.replace("中文 →", "English →")
    result = result.replace(" · 翻译并插入", " · translate and insert")
    result = result.replace(" · 翻译", " · translate")
    result = result.replace(" · 直接转写，不翻译", " · transcription only")
    result = result.replace(" · 直接转写", " · transcription only")
    result = re.sub(r"收尾 ([0-9.]+) 秒…", r"Finishing (\1 s)…", result)
    if result.startswith("English → English"):
        result = "English → English · transcription only"
    if "ALT-VoiceType" in result and "English" not in result:
        result = result.replace("ALT-VoiceType", "ALT-VoiceType English")
    return result


def install_qt_english() -> None:
    """Patch Qt setters once, before the tray UI is constructed."""
    if not is_english():
        return
    try:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QPushButton, QSystemTrayIcon, QWidget
    except Exception:
        return

    def patch(cls, name):
        original = getattr(cls, name)

        def wrapper(self, text, *args, **kwargs):
            return original(self, tr(text), *args, **kwargs)

        setattr(cls, name, wrapper)

    patch(QLabel, "setText")
    patch(QPushButton, "setText")
    patch(QCheckBox, "setText")
    patch(QAction, "setText")
    patch(QWidget, "setWindowTitle")
    patch(QSystemTrayIcon, "setToolTip")
    original_add = QComboBox.addItem

    def add_item(self, text, *args, **kwargs):
        return original_add(self, tr(text), *args, **kwargs)

    QComboBox.addItem = add_item

def translate_widget_tree(root) -> None:
    """Translate labels, buttons, combo items and actions after construction."""
    if not is_english():
        return
    try:
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton
    except Exception:
        return
    for cls in (QLabel, QPushButton, QCheckBox):
        for widget in root.findChildren(cls):
            text = widget.text()
            if text:
                widget.setText(tr(text))
    for edit in root.findChildren(QLineEdit):
        text = edit.placeholderText()
        if text:
            edit.setPlaceholderText(tr(text))
    for combo in root.findChildren(QComboBox):
        for i in range(combo.count()):
            combo.setItemText(i, tr(combo.itemText(i)))
    for action in root.findChildren(QAction):
        text = action.text()
        if text:
            action.setText(tr(text))
