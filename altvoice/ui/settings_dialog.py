"""Settings dialog for the compact tray UI."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
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
from ..edition import is_english
from ..hotkey.combo import parse_combo
from ..models import PROFILE_LABELS, PROFILE_ORDER, PROFILES
from .english import translate_widget_tree


class SettingsDialog(QDialog):
    profile_changed = Signal(str)
    hotkey_changed = Signal(str)

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
            "QComboBox { background: #181818; color: #F2F2F2; border: 1px solid #444444;"
            " border-radius: 6px; padding: 6px; min-height: 22px; }"
            "QLineEdit { background: #181818; color: #F2F2F2; border: 1px solid #444444;"
            " border-radius: 6px; padding: 6px; min-height: 22px; }"
            "QPushButton { background: #F2F2F2; color: #0A0A0A; border: 0; padding: 6px 12px;"
            " border-radius: 6px; }"
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
        self.hotkey = QLineEdit(config.hotkey.combo)
        self.hotkey.setPlaceholderText(
            "lalt or lalt+q, ralt+space, alt+shift"
            if is_english()
            else "lalt 或 lalt+q、ralt+space、alt+shift"
        )
        form.addRow("Recording hotkey" if is_english() else "录音快捷键", self.hotkey)
        layout.addLayout(form)
        note = QLabel(
            "Hotkey: lalt (left Alt), ralt (right Alt), or either Alt plus any key.\n"
            "Changes apply immediately; Alt is not captured globally.\n"
            "Changing the model tier stops the old models and warms the new ones."
            if is_english()
            else "快捷键支持 lalt（左 Alt）、ralt（右 Alt），或左/右 Alt + 任意按键；\n"
            "点击保存后立即生效。Alt 组合键不会被独占，Alt+Tab 等系统快捷键仍可用。\n"
            "切换模型档位会立即停止旧模型并重新预热新模型。"
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
        self.hotkey.setText(combo)
        self.config.save(self.config_path)
        if combo != old_combo:
            self.hotkey_changed.emit(combo)
        if profile != old_profile:
            self.profile_changed.emit(profile)
        self.accept()
