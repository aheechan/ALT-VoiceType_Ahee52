"""Qt tray and preview UI for AltVoice."""

from __future__ import annotations

import os
import sys

from ..app import VoiceAppController
from ..config import LANGUAGES, TARGET_LANGUAGES

try:
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
    from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPen, QPixmap
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QHBoxLayout,
        QLabel,
        QMenu,
        QPushButton,
        QSystemTrayIcon,
        QTextEdit,
        QVBoxLayout,
    )
    from PySide6.QtGui import QCursor
except ImportError as exc:  # pragma: no cover - depends on optional extra
    raise SystemExit(
        "The tray UI needs PySide6. Install with: pip install 'altvoice[ui]'"
    ) from exc

from ..hotkey.windows import HotkeyError, WindowsAltHook
from ..health import HealthReport, check_health
from ..pipeline import PipelineResult
from .history_dialog import HistoryDialog
from .setup_dialog import SetupDialog


def _make_icon(color: str = "#2d7ff9") -> QIcon:
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
        self.setWindowTitle("AltVoice · 确认插入")
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


class TrayApp(QObject):
    status_changed = Signal(str)
    result_ready = Signal(object)
    error_raised = Signal(str)

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__()
        self.controller = VoiceAppController(
            config_path=config_path,
            on_status=self.status_changed.emit,
            on_result=self.result_ready.emit,
            on_error=self.error_raised.emit,
        )
        self.hotkey = WindowsAltHook(
            threshold_ms=self.controller.config.hotkey.threshold_ms,
            on_start=self.controller.start_recording,
            on_stop=self.controller.stop_recording,
            on_cancel=self.controller.cancel_recording,
        )
        self.tray = QSystemTrayIcon(_make_icon())
        self.tray.setToolTip("AltVoice · 长按 Alt 说话")
        self._setup_dialog: SetupDialog | None = None
        self._history_dialog: HistoryDialog | None = None
        self.menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.status_changed.connect(self._set_status)
        self.error_raised.connect(self._show_error)
        self.result_ready.connect(self._on_result)

    def _build_menu(self) -> None:
        header = self.menu.addAction("AltVoice")
        header.setEnabled(False)
        self.menu.addSeparator()

        language_menu = self.menu.addMenu("目标语言")
        self.language_group = QActionGroup(self)
        self.language_group.setExclusive(True)
        for code in TARGET_LANGUAGES:
            action = QAction(f"{LANGUAGES[code]}  ({code})", self)
            action.setCheckable(True)
            action.setData(code)
            action.setChecked(code == self.controller.target_lang)
            action.triggered.connect(lambda _checked=False, c=code: self.controller.set_target_lang(c))
            self.language_group.addAction(action)
            language_menu.addAction(action)

        mode_menu = self.menu.addMenu("模式")
        self.translate_action = QAction("翻译并输入", self)
        self.translate_action.setCheckable(True)
        self.translate_action.setChecked(True)
        self.transcribe_action = QAction("中文转写", self)
        self.transcribe_action.setCheckable(True)
        group = QActionGroup(self)
        group.setExclusive(True)
        group.addAction(self.translate_action)
        group.addAction(self.transcribe_action)
        self.translate_action.triggered.connect(lambda: self.controller.set_mode("translate"))
        self.transcribe_action.triggered.connect(lambda: self.controller.set_mode("transcribe"))
        mode_menu.addAction(self.translate_action)
        mode_menu.addAction(self.transcribe_action)

        self.preview_action = QAction("插入前预览", self)
        self.preview_action.setCheckable(True)
        self.preview_action.setChecked(self.controller.config.ui.preview)
        self.preview_action.toggled.connect(self._set_preview)
        self.menu.addAction(self.preview_action)

        self.menu.addSeparator()
        history_action = self.menu.addAction("历史与术语…")
        history_action.triggered.connect(self._show_history)
        health_action = self.menu.addAction("环境检查…")
        health_action.triggered.connect(self._show_setup)
        settings = self.menu.addAction("配置文件位置…")
        settings.triggered.connect(self._show_config)
        quit_action = self.menu.addAction("退出")
        quit_action.triggered.connect(self.stop)

    def start(self) -> None:
        self.tray.show()
        report = check_health(self.controller.config, self.controller.profile)
        if report.config_ready:
            self.controller.warm_up()
        if not report.ready:
            QTimer.singleShot(350, lambda: self._show_setup(report))
        try:
            self.hotkey.start()
        except HotkeyError as exc:
            self._show_error(str(exc))
            self.tray.setToolTip("AltVoice · 热键不可用")

    def stop(self) -> None:
        try:
            self.hotkey.stop()
        finally:
            if self._setup_dialog is not None:
                self._setup_dialog.close()
                self._setup_dialog = None
            if self._history_dialog is not None:
                self._history_dialog.close()
                self._history_dialog = None
            self.controller.close()
            self.tray.hide()
            QApplication.instance().quit()

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

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.controller.toggle_recording()

    def _on_result(self, result: PipelineResult) -> None:
        if not self.controller.config.ui.preview:
            self._set_status("已插入")
            return
        dialog = PreviewDialog(result)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.controller.restore_target_focus()
            self.controller.commit(result, dialog.text())
        else:
            self._set_status("已取消")

    def _set_status(self, message: str) -> None:
        self.tray.setToolTip(f"AltVoice · {message}")

    def _show_error(self, message: str) -> None:
        self.tray.showMessage("AltVoice", message, QSystemTrayIcon.MessageIcon.Warning, 6000)
        self.tray.setToolTip(f"AltVoice · 错误：{message}")

    def _set_preview(self, enabled: bool) -> None:
        self.controller.config.ui.preview = bool(enabled)
        self.controller.config.save()

    def _show_config(self) -> None:
        from ..config import default_config_path

        path = default_config_path()
        self.tray.showMessage(
            "AltVoice",
            f"配置文件：{path}",
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )
        try:
            if os.name == "nt":
                os.startfile(str(path.parent))  # type: ignore[attr-defined]
        except OSError:
            pass


def run_tray(config_path: str | None = None) -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("System tray is not available in this session.", file=sys.stderr)
        return 3
    tray = TrayApp(config_path)
    tray.start()
    return int(app.exec())
