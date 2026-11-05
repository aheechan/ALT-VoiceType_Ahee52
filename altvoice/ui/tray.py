"""Qt tray and preview UI for AltVoice."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from ..app import VoiceAppController
from ..config import LANGUAGES, TARGET_LANGUAGES, default_config_dir, default_config_path

try:
    from PySide6.QtCore import QObject, Qt, QTimer, Signal
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
        self.setWindowTitle("AltVoice")
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
        title = QLabel("AltVoice")
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

        self.preview = QCheckBox("插入前预览")
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
        quit_button = QPushButton("退出")
        quit_button.setObjectName("secondary")
        quit_button.clicked.connect(lambda: tray.stop())
        buttons.addWidget(history)
        buttons.addWidget(setup)
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


class TrayApp(QObject):
    status_changed = Signal(str)
    result_ready = Signal(object)
    error_raised = Signal(str)

    def __init__(self, config_path: str | None = None) -> None:
        super().__init__()
        self._log = _ui_logger()
        self._log.info("starting tray config=%s", config_path or "default")
        self.controller = VoiceAppController(
            config_path=config_path or str(default_config_path()),
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
        self._panel: TrayPanel | None = None
        self._stopped = False
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
        self._log.info("tray starting")
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
            if self._panel is not None:
                self._panel.close()
                self._panel = None
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

    def _show_panel(self) -> None:
        if self._panel is None:
            self._panel = TrayPanel(self)
        self._panel.popup()

    def _set_target_lang(self, code: str) -> None:
        self.controller.set_target_lang(code)
        for action in self.language_group.actions():
            if action.data() == self.controller.target_lang:
                action.setChecked(True)
                break
        if self._panel is not None:
            self._panel.refresh()

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._show_panel()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.controller.toggle_recording()

    def _on_result(self, result: PipelineResult) -> None:
        self._log.info(
            "result target=%s error=%r injected=%s",
            result.target_lang,
            result.error,
            result.injected,
        )
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
        self._log.error("%s", message)
        self.tray.showMessage("AltVoice", message, QSystemTrayIcon.MessageIcon.Warning, 6000)
        self.tray.setToolTip(f"AltVoice · 错误：{message}")

    def _set_preview(self, enabled: bool) -> None:
        self.controller.config.ui.preview = bool(enabled)
        self.controller.config.save()
        if self._panel is not None:
            self._panel.refresh()

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


def run_tray(config_path: str | None = None, smoke_seconds: float = 0.0) -> int:
    guard = SingleInstance()
    if not guard.acquired:
        print("AltVoice is already running.", file=sys.stderr)
        return 4
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
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
