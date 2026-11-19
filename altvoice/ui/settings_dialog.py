"""Settings dialog for the compact tray UI."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from ..config import AppConfig
from ..i18n import is_english
from ..hotkey.combo import parse_combo
from ..models import PROFILE_LABELS, PROFILE_ORDER, PROFILES
from .english import translate_widget_tree


class HotkeyEdit(QLineEdit):
    """Click, then press any key combination. The combination is recorded."""

    _NAMED = {
        Qt.Key.Key_Space: "space",
        Qt.Key.Key_Tab: "tab",
        Qt.Key.Key_Return: "enter",
        Qt.Key.Key_Enter: "enter",
        Qt.Key.Key_Escape: "esc",
        Qt.Key.Key_Backspace: "backspace",
        Qt.Key.Key_Delete: "delete",
        Qt.Key.Key_Insert: "insert",
        Qt.Key.Key_Home: "home",
        Qt.Key.Key_End: "end",
        Qt.Key.Key_PageUp: "pageup",
        Qt.Key.Key_PageDown: "pagedown",
        Qt.Key.Key_Left: "left",
        Qt.Key.Key_Up: "up",
        Qt.Key.Key_Right: "right",
        Qt.Key.Key_Down: "down",
        Qt.Key.Key_Minus: "minus",
        Qt.Key.Key_Equal: "equal",
        Qt.Key.Key_Comma: "comma",
        Qt.Key.Key_Period: "period",
        Qt.Key.Key_Slash: "slash",
        Qt.Key.Key_Backslash: "backslash",
        Qt.Key.Key_Semicolon: "semicolon",
        Qt.Key.Key_Apostrophe: "quote",
        Qt.Key.Key_BracketLeft: "bracketleft",
        Qt.Key.Key_BracketRight: "bracketright",
        Qt.Key.Key_QuoteLeft: "backtick",
    }
    for _i in range(1, 25):
        _NAMED[getattr(Qt.Key, f"Key_F{_i}")] = f"f{_i}"

    def __init__(self, combo: str, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setPlaceholderText("点击后按下任意组合键")
        self.setText(combo)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API
        key = event.key()
        modifiers = event.modifiers()
        parts: list[str] = []
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            parts.append("ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            parts.append("shift")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            parts.append("alt")
        if modifiers & Qt.KeyboardModifier.MetaModifier:
            parts.append("win")

        modifier_keys = {
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        }
        if key in modifier_keys:
            if not parts:
                native = int(event.nativeVirtualKey())
                if native == 0xA4:
                    parts = ["lalt"]
                elif native == 0xA5:
                    parts = ["ralt"]
            if parts:
                self.setText("+".join(parts))
            event.accept()
            return

        name = self._NAMED.get(key)
        if not name:
            text = event.text().lower()
            if len(text) == 1 and text.isalnum():
                name = text
        if not name:
            event.ignore()
            return
        parts.append(name)
        self.setText("+".join(parts))
        event.accept()


class SettingsDialog(QDialog):
    profile_changed = Signal(str)
    hotkey_changed = Signal(str)
    always_on_top_changed = Signal(bool)

    def __init__(self, config: AppConfig, config_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle(
            "ALT-VoiceType English · Settings"
            if is_english()
            else "ALT-VoiceType · 设置"
        )
        self.setMinimumWidth(430)
        self.setStyleSheet(
            "QDialog { background: #0A0A0A; color: #F2F2F2; }"
            "QLabel { color: #D8D8D8; }"
            "QComboBox, QLineEdit { background: #181818; color: #F2F2F2;"
            " border: 1px solid #444444; border-radius: 6px; padding: 6px;"
            " min-height: 22px; }"
            "QPushButton { background: #F2F2F2; color: #0A0A0A; border: 0;"
            " padding: 6px 12px; border-radius: 6px; }"
        )
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.profile = QComboBox()
        for name in PROFILE_ORDER:
            info = PROFILES[name]
            description = info.get("description_en") if is_english() else info.get("description", "")
            self.profile.addItem(f"{PROFILE_LABELS[name]} — {description}", name)
        index = self.profile.findData(config.profile)
        if index >= 0:
            self.profile.setCurrentIndex(index)
        form.addRow("Model tier" if is_english() else "模型档位", self.profile)

        self.hotkey = HotkeyEdit(config.hotkey.combo)
        form.addRow("Recording hotkey" if is_english() else "录音快捷键", self.hotkey)

        self.always_on_top = QCheckBox(
            "Keep main window always on top"
            if is_english()
            else "主界面始终置顶"
        )
        self.always_on_top.setChecked(bool(config.ui.always_on_top))
        form.addRow("", self.always_on_top)
        layout.addLayout(form)

        note = QLabel(
            "Click the hotkey field, then press any key combination.\n"
            "Supported: Ctrl / Shift / Alt / Win, letters, digits, F1–F24,\n"
            "arrows, space, punctuation, and modifier-only combinations.\n"
            "The main window always-on-top setting is saved immediately."
            if is_english()
            else "点击快捷键输入框后，直接按下任意组合键即可设定。\n"
            "支持 Ctrl / Shift / Alt / Win、字母、数字、F1–F24、方向键、\n"
            "空格、标点，以及仅由修饰键组成的组合。\n"
            "“主界面始终置顶”会立即生效。"
        )
        note.setStyleSheet("color: #8b93a1; font-size: 12px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        layout.addWidget(buttons)
        translate_widget_tree(self)

    def _apply(self) -> None:
        old_profile = self.config.profile
        old_combo = self.config.hotkey.combo
        old_on_top = bool(self.config.ui.always_on_top)
        profile = self.profile.currentData()
        try:
            combo = parse_combo(self.hotkey.text()).text
        except ValueError as exc:
            QMessageBox.warning(
                self, "Invalid hotkey" if is_english() else "快捷键无效", str(exc)
            )
            return
        self.config.profile = profile
        self.config.hotkey.combo = combo
        self.config.ui.always_on_top = self.always_on_top.isChecked()
        self.hotkey.setText(combo)
        self.config.save(self.config_path)
        if combo != old_combo:
            self.hotkey_changed.emit(combo)
        if profile != old_profile:
            self.profile_changed.emit(profile)
        if self.config.ui.always_on_top != old_on_top:
            self.always_on_top_changed.emit(self.config.ui.always_on_top)
        self.accept()
