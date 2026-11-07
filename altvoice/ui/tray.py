"""Qt tray and preview UI for ALT-VoiceType."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..app import VoiceAppController
from ..config import LANGUAGES, TARGET_LANGUAGES, default_config_dir, default_config_path

try:
    from PySide6.QtCore import QObject, QRect, Qt, QTimer, Signal
    from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QHBoxLayout,
        QLabel,
        QMenu,
        QPushButton,
        QSystemTrayIcon,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from PySide6.QtGui import QCursor
except ImportError as exc:  # pragma: no cover - depends on optional extra
    raise SystemExit(
        "The tray UI needs PySide6. Install with: pip install 'altvoice[ui]'"
    ) from exc

from ..hotkey.windows import HotkeyError, WindowsAltHook
from ..health import HealthReport, check_health
from ..pipeline import PipelineResult
from ..single_instance import SingleInstance
from .history_dialog import HistoryDialog
from .settings_dialog import SettingsDialog
from .setup_dialog import SetupDialog


def _ui_logger() -> logging.Logger:
    logger = logging.getLogger("altvoice.ui")
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    try:
        log_dir = default_config_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        pass
    return logger


def _make_icon(color: str = "#0A0A0A") -> QIcon:
    asset = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
    if asset.exists():
        return QIcon(str(asset))
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(
        QPen(
            Qt.GlobalColor.white,
            4,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(Qt.BrushStyle.NoBrush)
    # Simple microphone glyph: capsule, arc, stand.
    painter.drawRoundedRect(25, 15, 14, 24, 7, 7)
    painter.drawArc(19, 26, 26, 24, 200 * 16, 140 * 16)
    painter.drawLine(32, 48, 32, 54)
    painter.drawLine(25, 54, 39, 54)
    painter.end()
    return QIcon(pixmap)


class _Editor(QTextEdit):
    def keyPressEvent(self, event):  # noqa: N802 - Qt API
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            window = self.window()
            if hasattr(window, "accept"):
                window.accept()
            return
        super().keyPressEvent(event)


class PreviewDialog(QDialog):
    def __init__(self, result: PipelineResult, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ALT-VoiceType · 确认插入")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setMinimumWidth(560)
        self.setStyleSheet(
            "QDialog { background: #1f2329; color: #e8eaed; border: 1px solid #3a404a; }"
            "QLabel { color: #aeb4bf; }"
            "QTextEdit { background: #2a2f37; color: #f2f4f7; border: 1px solid #3a404a;"
            " border-radius: 6px; padding: 8px; font-size: 15px; }"
            "QPushButton { background: #2d7ff9; color: white; border: 0; padding: 7px 16px;"
            " border-radius: 6px; }"
            "QPushButton#cancel { background: #3a404a; }"
        )

        layout = QVBoxLayout(self)
        source_label = QLabel("原文")
        layout.addWidget(source_label)
        source = QTextEdit()
        source.setPlainText(result.raw_text)
        source.setReadOnly(True)
        source.setFixedHeight(60)
        layout.addWidget(source)

        result_label = QLabel("翻译" if result.target_lang != "zh" else "文本")
        layout.addWidget(result_label)
        self.editor = _Editor()
        self.editor.setPlainText(result.output_text)
        self.editor.setFixedHeight(96)
        layout.addWidget(self.editor)

        buttons = QHBoxLayout()
        hint = QLabel("Enter 插入 · Shift+Enter 换行 · Esc 取消")
        hint.setStyleSheet("color: #8b93a1; font-size: 12px;")
        buttons.addWidget(hint)
        buttons.addStretch(1)
        cancel = QPushButton("取消")
        cancel.setObjectName("cancel")
        cancel.clicked.connect(self.reject)
        insert = QPushButton("插入")
        insert.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(insert)
        layout.addLayout(buttons)

    def text(self) -> str:
        return self.editor.toPlainText().strip()

    def showEvent(self, event):  # noqa: N802 - Qt API
        super().showEvent(event)
        cursor = QCursor.pos()
        screen = self.screen().availableGeometry() if self.screen() else None
        x, y = cursor.x() - self.width() // 2, cursor.y() + 18
        if screen is not None:
            x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
            y = max(screen.top() + 8, min(y, screen.bottom() - self.height() - 8))
        self.move(x, y)


class TrayPanel(QWidget):
    """Compact control panel opened from the tray icon."""

    def __init__(self, tray: "TrayApp") -> None:
        super().__init__(
            None,
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool,
        )
        self._tray = tray
        self.setWindowTitle("ALT-VoiceType")
        self.setFixedWidth(360)
        self.setStyleSheet(
            "QWidget#panel { background: #1f2329; border: 1px solid #3a404a;"
            " border-radius: 10px; }"
            "QLabel { color: #c6ccd6; }"
            "QLabel#title { color: #f2f4f7; font-size: 17px; font-weight: 600; }"
            "QLabel#hint { color: #8b93a1; font-size: 12px; }"
            "QLabel#mode { color: #9ec5ff; font-size: 12px; }"
            "QComboBox { background: #2a2f37; color: #eef2f8; border: 1px solid #3a404a;"
            " border-radius: 6px; padding: 6px 8px; min-height: 22px; }"
            "QComboBox QAbstractItemView { background: #2a2f37; color: #eef2f8;"
            " selection-background-color: #2d7ff9; }"
            "QCheckBox { color: #c6ccd6; spacing: 7px; }"
            "QPushButton { background: #2d7ff9; color: white; border: 0;"
            " padding: 6px 10px; border-radius: 6px; }"
            "QPushButton#secondary { background: #3a404a; }"
        )

        box = QWidget(self)
        box.setObjectName("panel")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)

        title_row = QHBoxLayout()
        title = QLabel("ALT-VoiceType")
        title.setObjectName("title")
        title_row.addWidget(title)
        title_row.addStretch(1)
        hint = QLabel("长按 Alt 说话")
        hint.setObjectName("hint")
        title_row.addWidget(hint)
        layout.addLayout(title_row)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("输入语言"))
        input_value = QLabel("中文（固定）")
        input_value.setStyleSheet("color: #f2f4f7;")
        input_row.addWidget(input_value)
        input_row.addStretch(1)
        layout.addLayout(input_row)

        layout.addWidget(QLabel("输出语言"))
        self.language = QComboBox()
        for code in TARGET_LANGUAGES:
            self.language.addItem(f"{LANGUAGES[code]}  ({code})", code)
        self._select_language(tray.controller.target_lang)
        self.language.currentIndexChanged.connect(self._language_changed)
        layout.addWidget(self.language)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("mode")
        layout.addWidget(self.mode_label)

        self.preview = QCheckBox("显示确认弹窗（关闭则直接粘贴）")
        self.preview.setChecked(tray.controller.config.ui.preview)
        self.preview.toggled.connect(self._preview_changed)
        layout.addWidget(self.preview)

        buttons = QHBoxLayout()
        history = QPushButton("历史")
        history.setObjectName("secondary")
        history.clicked.connect(tray._show_history)
        setup = QPushButton("环境")
        setup.setObjectName("secondary")
        setup.clicked.connect(tray._show_setup)
        settings_button = QPushButton("设置")
        settings_button.setObjectName("secondary")
        settings_button.clicked.connect(lambda: tray._show_settings())
        log_button = QPushButton("日志")
        log_button.setObjectName("secondary")
        log_button.clicked.connect(lambda: tray._show_log())
        quit_button = QPushButton("退出")
        quit_button.setObjectName("secondary")
        quit_button.clicked.connect(lambda: tray.stop())
        buttons.addWidget(history)
        buttons.addWidget(setup)
        buttons.addWidget(settings_button)
        buttons.addWidget(log_button)
        buttons.addStretch(1)
        buttons.addWidget(quit_button)
        layout.addLayout(buttons)

        self.refresh()

    def _select_language(self, code: str) -> None:
        index = self.language.findData(code)
        if index < 0:
            index = 0
        self.language.blockSignals(True)
        self.language.setCurrentIndex(index)
        self.language.blockSignals(False)

    def _language_changed(self, _index: int) -> None:
        code = self.language.currentData()
        self._tray._set_target_lang(code)
        self.refresh()

    def _preview_changed(self, checked: bool) -> None:
        self._tray._set_preview(checked)

    def refresh(self) -> None:
        code = self._tray.controller.target_lang
        self._select_language(code)
        self.preview.setChecked(self._tray.controller.config.ui.preview)
        if code == "zh":
            self.mode_label.setText("中文 → 中文 · 直接转写，不翻译")
        else:
            self.mode_label.setText(f"中文 → {LANGUAGES.get(code, code)} · 翻译并插入")

    def popup(self) -> None:
        self.refresh()
        self.adjustSize()
        cursor = QCursor.pos()
        screen = self.screen().availableGeometry() if self.screen() else None
        x = cursor.x() - self.width() + 12
        y = cursor.y() - self.height() - 12
        if screen is not None:
            x = max(screen.left() + 8, min(x, screen.right() - self.width() - 8))
            y = max(screen.top() + 8, min(y, screen.bottom() - self.height() - 8))
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()


class AudioMonitor(QWidget):
    """A tiny, text-free live input-level visualizer."""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFixedSize(168, 46)
        self.level = 0.0
        self._decay = QTimer(self)
        self._decay.setInterval(33)
        self._decay.timeout.connect(self._decay_level)

    def set_level(self, level: float) -> None:
        self.level = min(1.0, max(0.0, float(level) * 24.0))
        self.update()

    def _decay_level(self) -> None:
        self.level *= 0.84
        if self.level < 0.01:
            self.level = 0.0
        self.update()

    def show_at_corner(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 18, screen.bottom() - self.height() - 18)
        self.show()
        self.raise_()
        self._decay.start()

    def hide_monitor(self) -> None:
        self._decay.stop()
        self.level = 0.0
        self.hide()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(21, 24, 29, 235))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        bars = 20
        gap = 4
        bar_w = max(2, (self.width() - 20 - gap * (bars - 1)) // bars)
        base = self.height() - 10
        center = bars // 2
        for i in range(bars):
            distance = abs(i - center) / center
            factor = 0.45 + 0.55 * (1.0 - distance)
            h = 4 + int(24 * self.level * factor)
            x = 10 + i * (bar_w + gap)
            painter.setBrush(QColor(87, 155, 255) if i % 2 else QColor(126, 92, 255))
            painter.drawRoundedRect(x, base - h, bar_w, h, 2, 2)
        painter.end()


class LevelMeter(QWidget):
    """Integrated audio level meter; no recording text."""

    def __init__(self) -> None:
        super().__init__()
        self.setFixedHeight(42)
        self.level = 0.0
        self.active = True
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._decay)

    def set_level(self, level: float) -> None:
        self.level = min(1.0, max(0.0, float(level) * 24.0))
        self.update()

    def set_tail(self) -> None:
        self.active = False
        self.level = 0.0
        self.update()

    def set_active(self) -> None:
        self.active = True
        self._timer.start()

    def _decay(self) -> None:
        self.level *= 0.86
        if self.level < 0.01:
            self.level = 0.0
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 - Qt API
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(24, 24, 24))
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 6, 6)
        bars = 32
        gap = 3
        bar_w = max(2, (self.width() - 16 - gap * (bars - 1)) // bars)
        base = self.height() - 7
        center = bars // 2
        for i in range(bars):
            distance = abs(i - center) / center
            factor = 0.35 + 0.65 * (1.0 - distance)
            h = 3 + int(25 * self.level * factor)
            x = 8 + i * (bar_w + gap)
            color = QColor(240, 240, 240) if self.active else QColor(90, 90, 90)
            painter.setBrush(color)
            painter.drawRoundedRect(x, base - h, bar_w, h, 2, 2)
        painter.end()


class TypingEdit(QTextEdit):
    """Read-only display that reveals text with a short typing animation."""

    def __init__(self, height: int = 76) -> None:
        super().__init__()
        self.setReadOnly(True)
        self.setFixedHeight(height)
        self._full = ""
        self._pos = 0
        self._timer = QTimer(self)
        self._timer.setInterval(12)
        self._timer.timeout.connect(self._type_more)

    def full_text(self) -> str:
        return self._full

    def set_typed(self, text: str) -> None:
        self._timer.stop()
        self._full = text or ""
        self._pos = 0
        self.clear()
        if not self._full:
            return
        self._timer.start()

    def _type_more(self) -> None:
        if self._pos >= len(self._full):
            self._timer.stop()
            return
        chunk = self._full[self._pos : self._pos + 2]
        self._pos += len(chunk)
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.insertPlainText(chunk)


class MainWindow(QWidget):
    """Draggable main window: controls, inline result confirmation, meter."""

    def __init__(self, tray: "TrayApp") -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._tray = tray
        self._placed = False
        self._drag = None
        self._resize_mode = ""
        self._resize_origin = None
        self._resize_geometry = None
        self._result = None
        self.setWindowTitle("ALT-VoiceType")
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setStyleSheet(
            "QWidget#main { background: #0A0A0A; border: 1px solid #3A3A3A;"
            " border-radius: 12px; }"
            "QLabel { color: #D8D8D8; }"
            "QLabel#title { color: #FFFFFF; font-size: 18px; font-weight: 700; }"
            "QLabel#status { color: #A8A8A8; font-size: 12px; }"
            "QLabel#mode { color: #FFFFFF; font-size: 12px; }"
            "QComboBox { background: #181818; color: #F2F2F2; border: 1px solid #444444;"
            " border-radius: 6px; padding: 6px 8px; min-height: 22px; }"
            "QComboBox QAbstractItemView { background: #181818; color: #F2F2F2;"
            " selection-background-color: #F2F2F2; selection-color: #0A0A0A; }"
            "QCheckBox { color: #D8D8D8; spacing: 7px; }"
            "QTextEdit { background: #151515; color: #FFFFFF; border: 1px solid #444444;"
            " border-radius: 6px; padding: 7px; }"
            "QPushButton { background: #F2F2F2; color: #0A0A0A; border: 0;"
            " padding: 6px 10px; border-radius: 6px; }"
            "QPushButton#secondary { background: #2A2A2A; color: #F2F2F2; }"
        )

        box = QWidget(self)
        box.setObjectName("main")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(box)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("ALT-VoiceType")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch(1)
        hide_button = QPushButton("—")
        hide_button.setObjectName("secondary")
        hide_button.setFixedWidth(32)
        hide_button.clicked.connect(self.hide)
        header.addWidget(hide_button)
        layout.addLayout(header)

        self.status = QLabel("加载中…")
        self.status.setObjectName("status")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.warm_button = QPushButton("预热模型")
        self.warm_button.setObjectName("warm")
        self.warm_button.setMinimumHeight(32)
        self.warm_button.clicked.connect(self._tray._warm_up)
        layout.addWidget(self.warm_button)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("输入语言"))
        input_value = QLabel("中文（固定）")
        input_value.setStyleSheet("color: #FFFFFF;")
        input_row.addWidget(input_value)
        input_row.addStretch(1)
        layout.addLayout(input_row)

        layout.addWidget(QLabel("输出语言"))
        self.language = QComboBox()
        for code in TARGET_LANGUAGES:
            self.language.addItem(f"{LANGUAGES[code]}  ({code})", code)
        self.language.currentIndexChanged.connect(self._language_changed)
        layout.addWidget(self.language)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("mode")
        layout.addWidget(self.mode_label)

        self.result_frame = QWidget()
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(0, 4, 0, 2)
        result_layout.addWidget(QLabel("识别文字"))
        self.source_text = TypingEdit(72)
        result_layout.addWidget(self.source_text)
        source_buttons = QHBoxLayout()
        self.source_copy = QPushButton("复制识别文字")
        self.source_copy.setObjectName("secondary")
        self.source_copy.clicked.connect(self._copy_source)
        source_buttons.addStretch(1)
        source_buttons.addWidget(self.source_copy)
        result_layout.addLayout(source_buttons)

        result_layout.addWidget(QLabel("转译文字"))
        self.result_text = TypingEdit(72)
        result_layout.addWidget(self.result_text)
        result_buttons = QHBoxLayout()
        self.result_copy = QPushButton("复制转译文字")
        self.result_copy.setObjectName("secondary")
        self.result_copy.clicked.connect(self._copy_result)
        result_buttons.addStretch(1)
        result_buttons.addWidget(self.result_copy)
        result_layout.addLayout(result_buttons)
        layout.addWidget(self.result_frame)

        self.meter = LevelMeter()
        layout.addWidget(self.meter)

        footer = QHBoxLayout()
        settings = QPushButton("设置")
        settings.setObjectName("secondary")
        settings.clicked.connect(self._tray._show_settings)
        footer.addWidget(settings)
        footer.addStretch(1)
        layout.addLayout(footer)

        self.refresh()
        self.adjustSize()
        self._min_height = self.sizeHint().height()
        self.setMinimumSize(440, self._min_height)
        self.resize(440, self._min_height)

    def _select_language(self, code: str) -> None:
        index = self.language.findData(code)
        if index < 0:
            index = 0
        self.language.blockSignals(True)
        self.language.setCurrentIndex(index)
        self.language.blockSignals(False)

    def _language_changed(self, _index: int) -> None:
        self._tray._set_target_lang(self.language.currentData())
        self.refresh()

    def _copy_source(self) -> None:
        self._copy_button(self.source_copy, "复制识别文字", self.source_text.full_text())

    def _copy_result(self) -> None:
        self._copy_button(self.result_copy, "复制转译文字", self.result_text.full_text())

    def _copy_button(self, button: QPushButton, label: str, text: str) -> None:
        if not text.strip():
            button.setText("无内容")
        else:
            QApplication.clipboard().setText(text)
            button.setText("已复制 ✓")
        button.setEnabled(False)
        QTimer.singleShot(
            1200,
            lambda: (button.setText(label), button.setEnabled(True)),
        )

    def refresh(self) -> None:
        code = self._tray.controller.target_lang
        self._select_language(code)
        if code == "zh":
            self.mode_label.setText("中文 → 中文 · 直接转写")
        else:
            self.mode_label.setText(f"中文 → {LANGUAGES.get(code, code)} · 翻译")
        self.set_status(self._tray.controller_status)

    def show_panel(self, activate: bool = True) -> None:
        self.refresh()
        if not self._placed:
            screen = QApplication.primaryScreen().availableGeometry()
            self.adjustSize()
            self.move(screen.right() - self.width() - 24, screen.top() + 80)
            self._placed = True
        self.show()
        if activate:
            self.raise_()
            self.activateWindow()

    def set_status(self, text: str) -> None:
        self.status.setText(text)
        if "加载完毕" in text or "就绪" in text:
            self.warm_button.setEnabled(True)
            self.warm_button.setText("已预热 · 重新预热")
        elif any(word in text for word in ("加载", "预热", "切换")):
            self.warm_button.setEnabled(False)
            self.warm_button.setText("预热中…")
        elif "已粘贴" in text:
            self.warm_button.setEnabled(True)
            self.warm_button.setText("已预热 · 重新预热")
        else:
            self.warm_button.setEnabled(True)

    def set_level(self, level: float) -> None:
        self.meter.set_active()
        self.meter.set_level(level)

    def set_tail(self) -> None:
        self.meter.set_tail()
        self.status.setText("收尾 0.39 秒…")

    def show_result(self, result) -> None:
        self._result = result
        self.source_text.set_typed(result.raw_text or result.corrected_text)
        self.result_text.set_typed(result.output_text)
        self.refresh()
        self.show_panel(activate=False)

    def clear_result(self) -> None:
        self._result = None
        self.source_text.set_typed("")
        self.result_text.set_typed("")

    def cancel_result(self) -> None:
        self.clear_result()
        self.set_status("已取消")

    def accept_result(self) -> None:
        if self._result is None:
            return
        result = self._result
        text = self.result_text.full_text().strip()
        self.clear_result()
        self._tray._accept_result(result, text)

    def _resize_hit(self, pos) -> str:
        margin = 8
        left = pos.x() <= margin
        right = pos.x() >= self.width() - margin
        top = pos.y() <= margin
        bottom = pos.y() >= self.height() - margin
        return (
            ("t" if top else "b" if bottom else "")
            + ("l" if left else "r" if right else "")
        )

    def mousePressEvent(self, event):  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton:
            mode = self._resize_hit(event.position().toPoint())
            if mode:
                self._resize_mode = mode
                self._resize_origin = event.globalPosition().toPoint()
                self._resize_geometry = self.geometry()
                return
            self._drag = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802 - Qt API
        if self._resize_mode and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._resize_origin
            geo = QRect(self._resize_geometry)
            if "l" in self._resize_mode:
                geo.setLeft(min(geo.left() + delta.x(), geo.right() - self.minimumWidth()))
            if "r" in self._resize_mode:
                geo.setRight(max(geo.right() + delta.x(), geo.left() + self.minimumWidth()))
            if "t" in self._resize_mode:
                geo.setTop(min(geo.top() + delta.y(), geo.bottom() - self.minimumHeight()))
            if "b" in self._resize_mode:
                geo.setBottom(max(geo.bottom() + delta.y(), geo.top() + self.minimumHeight()))
            self.setGeometry(geo)
            return
        if self._drag is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802 - Qt API
        self._drag = None
        self._resize_mode = ""
        self._resize_origin = None
        self._resize_geometry = None
        super().mouseReleaseEvent(event)


class TrayApp(QObject):
    status_changed = Signal(str)
    result_ready = Signal(object)
    error_raised = Signal(str)
    audio_level = Signal(float)

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__()
        self._log = _ui_logger()
        self._log.info("starting tray config=%s", config_path or "default")
        self.controller = VoiceAppController(
            config_path=config_path or str(default_config_path()),
            on_status=self.status_changed.emit,
            on_result=self.result_ready.emit,
            on_error=self.error_raised.emit,
            on_audio_level=self.audio_level.emit,
        )
        self.hotkey = self._make_hotkey()
        self.tray = QSystemTrayIcon(_make_icon())
        self.tray.setToolTip(f"ALT-VoiceType · {self.controller.config.hotkey.combo} 开始/停止")
        self._setup_dialog: SetupDialog | None = None
        self._history_dialog: HistoryDialog | None = None
        self._settings_dialog: SettingsDialog | None = None
        self._panel: TrayPanel | None = None
        self._main: MainWindow | None = None
        self._monitor: AudioMonitor | None = None
        self.controller_status = "加载中…"
        self._stopped = False
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.status_changed.connect(self._set_status)
        self.error_raised.connect(self._show_error)
        self.result_ready.connect(self._on_result)
        self.audio_level.connect(self._on_audio_level)

    def _make_hotkey(self) -> WindowsAltHook:
        return WindowsAltHook(
            threshold_ms=self.controller.config.hotkey.threshold_ms,
            mode=self.controller.config.hotkey.mode,
            combo=self.controller.config.hotkey.combo,
            on_start=self.controller.start_recording,
            on_stop=self._request_stop,
            on_cancel=self.controller.cancel_recording,
            on_toggle=self._toggle_recording,
            on_escape=self._cancel_if_recording,
        )

    def _build_menu(self) -> None:
        header = self.menu.addAction("ALT-VoiceType")
        header.setEnabled(False)
        self.menu.addSeparator()

        panel_action = self.menu.addAction("打开控制面板…")
        panel_action.triggered.connect(self._show_panel)
        self.menu.addSeparator()

        language_menu = self.menu.addMenu("输出语言")
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        for code in TARGET_LANGUAGES:
            action = QAction(f"{LANGUAGES[code]}  ({code})", self)
            action.setCheckable(True)
            action.setData(code)
            action.setChecked(code == self.controller.target_lang)
            action.triggered.connect(
                lambda _checked=False, c=code: self._set_target_lang(c)
            )
            self.language_group.addAction(action)
            language_menu.addAction(action)

        self.menu.addSeparator()
        history_action = self.menu.addAction("历史与术语…")
        history_action.triggered.connect(self._show_history)
        health_action = self.menu.addAction("环境检查…")
        health_action.triggered.connect(self._show_setup)
        log_action = self.menu.addAction("查看日志…")
        log_action.triggered.connect(lambda: self._show_log())
        settings_action = self.menu.addAction("设置…")
        settings_action.triggered.connect(lambda: self._show_settings())
        settings = self.menu.addAction("配置文件位置…")
        settings.triggered.connect(self._show_config)
        quit_action = self.menu.addAction("退出")
        quit_action.triggered.connect(self.stop)

    def start(self) -> None:
        self._log.info("tray starting")
        self.tray.show()
        QTimer.singleShot(0, lambda: self._show_panel(auto=True))
        report = check_health(self.controller.config, self.controller.profile)
        if report.config_ready:
            self.controller.warm_up()
        if not report.ready:
            QTimer.singleShot(350, lambda: self._show_setup(report))
        try:
            self.hotkey.start()
        except HotkeyError as exc:
            self._show_error(str(exc))
            self.tray.setToolTip("ALT-VoiceType · 热键不可用")

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        self._log.info("tray stopping")
        try:
            self.hotkey.stop()
        finally:
            if self._setup_dialog is not None:
                self._setup_dialog.close()
                self._setup_dialog = None
            if self._history_dialog is not None:
                self._history_dialog.close()
                self._history_dialog = None
            if self._settings_dialog is not None:
                self._settings_dialog.close()
                self._settings_dialog = None
            if self._panel is not None:
                self._panel.close()
                self._panel = None
            if self._main is not None:
                self._main.close()
                self._main = None
            if self._monitor is not None:
                self._monitor.hide_monitor()
                self._monitor.close()
                self._monitor = None
            self.controller.close()
            self.tray.hide()
            QApplication.instance().quit()

    def _show_settings(self) -> None:
        if self._settings_dialog is not None:
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return
        dialog = SettingsDialog(self.controller.config)
        dialog.profile_changed.connect(self._reload_profile)
        dialog.hotkey_changed.connect(self._apply_hotkey)
        dialog.finished.connect(lambda _code=0: self._clear_settings())
        self._settings_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _clear_settings(self) -> None:
        dialog = self._settings_dialog
        self._settings_dialog = None
        if dialog is not None:
            dialog.deleteLater()
        if self._panel is not None:
            self._panel.refresh()
        if self._main is not None:
            self._main.refresh()

    def _reload_profile(self, profile: str) -> None:
        self.controller_status = f"切换 {profile}：清理旧模型…"
        if self._main is not None:
            self._main.set_status(self.controller_status)
        self.controller.reload_profile(profile)
        if self._main is not None:
            self._main.refresh()

    def _apply_hotkey(self, combo: str) -> None:
        try:
            self.hotkey.stop()
        except Exception:
            pass
        try:
            self.hotkey = self._make_hotkey()
            self.hotkey.start()
            self.tray.setToolTip(f"ALT-VoiceType · {combo} 开始/停止")
            self._set_status(f"快捷键已生效：{combo}")
        except HotkeyError as exc:
            self._show_error(f"快捷键设置失败：{exc}")

    def _show_history(self, *_args) -> None:
        if self.controller.history is None:
            self._show_error("历史记录未启用，检查 config.json 的 history.enabled")
            return
        if self._history_dialog is not None:
            self._history_dialog.raise_()
            self._history_dialog.activateWindow()
            return
        dialog = HistoryDialog(self.controller.history)
        dialog.finished.connect(lambda _code=0: self._clear_history_dialog())
        self._history_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _clear_history_dialog(self) -> None:
        dialog = self._history_dialog
        self._history_dialog = None
        if dialog is not None:
            dialog.deleteLater()

    def _show_setup(self, report: HealthReport | None = None, *_args) -> None:
        if self._setup_dialog is not None:
            self._setup_dialog.raise_()
            self._setup_dialog.activateWindow()
            return
        if not isinstance(report, HealthReport):
            report = check_health(self.controller.config, self.controller.profile)
        dialog = SetupDialog(report, self.controller.config)
        dialog.recheck_requested.connect(self._recheck_setup)
        dialog.finished.connect(lambda _code=0: self._clear_setup())
        self._setup_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _clear_setup(self) -> None:
        dialog = self._setup_dialog
        self._setup_dialog = None
        if dialog is not None:
            dialog.deleteLater()

    def _recheck_setup(self) -> None:
        dialog = self._setup_dialog
        if dialog is not None:
            dialog.close()
        self._clear_setup()
        report = check_health(self.controller.config, self.controller.profile)
        if report.config_ready:
            self.controller.warm_up()
        self._show_setup(report)

    def _show_panel(self, auto: bool = False) -> None:
        if self._main is None:
            self._main = MainWindow(self)
        self._main.show_panel(activate=not auto)

    def _toggle_recording(self) -> None:
        if self.controller.recording:
            self._request_stop()
        else:
            self.controller.start_recording()

    def _cancel_if_recording(self) -> bool:
        if not self.controller.recording:
            return False
        self.controller.cancel_recording()
        self._set_status("已取消录音")
        if self._main is not None:
            self._main.set_status("已取消录音")
            self._main.meter.set_tail()
        return True

    def _request_stop(self) -> None:
        if self._main is None:
            self._main = MainWindow(self)
        self._main.show_panel(activate=False)
        self._main.set_tail()
        self.controller.stop_recording(delay_s=0.39)

    def _warm_up(self) -> None:
        if self._main is not None:
            self._main.set_status("预热中…")
        if self.controller._pipeline is not None:
            self._set_status("加载完毕，可以开始输入")
            return
        self.controller.warm_up()
        if self._main is not None:
            self._main.show_panel()

    def _accept_result(self, result: PipelineResult, text: str) -> None:
        self.controller.restore_target_focus()
        self.controller.commit(result, text)

    def _set_target_lang(self, code: str) -> None:
        self.controller.set_target_lang(code)
        for action in self.language_group.actions():
            if action.data() == self.controller.target_lang:
                action.setChecked(True)
                break
        if self._main is not None:
            self._main.refresh()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_panel()

    def _on_result(self, result: PipelineResult) -> None:
        self._log.info(
            "result target=%s error=%r injected=%s",
            result.target_lang,
            result.error,
            result.injected,
        )
        if self._main is None:
            self._main = MainWindow(self)
        self._main.show_result(result)
        self._set_status("已粘贴" if result.injected else "结果已复制到剪贴板")

    def _on_audio_level(self, level: float) -> None:
        if self._main is None:
            self._main = MainWindow(self)
            self._main.show_panel(activate=False)
        self._main.set_level(level)

    def _set_status(self, message: str) -> None:
        self.controller_status = message
        self.tray.setToolTip(f"ALT-VoiceType · {message}")
        if "录音中" in message:
            if self._main is None:
                self._main = MainWindow(self)
            self._main.set_status(message)
            self._main.show_panel(activate=False)
            self._main.meter.set_active()
        elif self._main is not None:
            self._main.set_status(message)
            if "收尾" in message:
                self._main.set_tail()

    def _show_error(self, message: str) -> None:
        self._log.error("%s", message)
        self.controller_status = f"错误：{message}"
        if self._main is not None:
            self._main.set_status(self.controller_status)
        self.tray.showMessage("ALT-VoiceType", message, QSystemTrayIcon.MessageIcon.Warning, 6000)
        self.tray.setToolTip(f"ALT-VoiceType · 错误：{message}")

    def _set_preview(self, enabled: bool) -> None:
        self.controller.config.ui.preview = bool(enabled)
        self.controller.config.save()
        if self._main is not None:
            self._main.refresh()

    def _show_log(self) -> None:
        path = default_config_dir() / "logs" / "app.log"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            else:
                self.tray.showMessage(
                    "ALT-VoiceType",
                    f"日志文件：{path}",
                    QSystemTrayIcon.MessageIcon.Information,
                    5000,
                )
        except OSError as exc:
            self._show_error(f"无法打开日志：{exc}")

    def _show_config(self) -> None:
        from ..config import default_config_path

        path = default_config_path()
        self.tray.showMessage(
            "ALT-VoiceType",
            f"配置文件：{path}",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )
        try:
            if os.name == "nt":
                os.startfile(str(path.parent))  # type: ignore[attr-defined]
        except OSError:
            pass


def run_tray(config_path: str | None = None, smoke_seconds: float = 0.0) -> int:
    guard = SingleInstance()
    if not guard.acquired:
        print("ALT-VoiceType is already running.", file=sys.stderr)
        return 4
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        app.setWindowIcon(_make_icon())
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("System tray is not available in this session.", file=sys.stderr)
            return 3
        tray = TrayApp(config_path)
        tray.start()
        if smoke_seconds > 0:
            QTimer.singleShot(int(smoke_seconds * 1000), app.quit)
        code = int(app.exec())
        tray.stop()
        return code
    finally:
        guard.close()


