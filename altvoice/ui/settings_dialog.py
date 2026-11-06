"""Settings dialog for the rolled-back compact tray UI."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from ..config import AppConfig
from ..models import PROFILE_LABELS, PROFILE_ORDER, PROFILES


class SettingsDialog(QDialog):
    profile_changed = Signal(str)

    def __init__(self, config: AppConfig, config_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("ALT-VoiceType · 设置")
        self.setMinimumWidth(430)
        self.setStyleSheet(
            "QDialog { background: #0A0A0A; color: #F2F2F2; }"
            "QLabel { color: #D8D8D8; }"
            "QComboBox { background: #181818; color: #F2F2F2; border: 1px solid #444444;"
            " border-radius: 6px; padding: 6px; min-height: 22px; }"
            "QCheckBox { color: #D8D8D8; }"
            "QPushButton { background: #F2F2F2; color: #0A0A0A; border: 0; padding: 6px 12px;"
            " border-radius: 6px; }"
        )
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.profile = QComboBox()
        for name in PROFILE_ORDER:
            info = PROFILES[name]
            self.profile.addItem(
                f"{PROFILE_LABELS[name]} — {info.get('description', '')}", name
            )
        index = self.profile.findData(config.profile)
        if index >= 0:
            self.profile.setCurrentIndex(index)
        form.addRow("模型档位", self.profile)
        self.preview = QCheckBox("识别后显示确认弹窗")
        self.preview.setChecked(config.ui.preview)
        form.addRow("插入", self.preview)
        layout.addLayout(form)
        note = QLabel("模型档位在下次启动时生效；确认弹窗开关立即生效。")
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

    def _apply(self) -> None:
        old_profile = self.config.profile
        profile = self.profile.currentData()
        self.config.profile = profile
        self.config.ui.preview = self.preview.isChecked()
        self.config.save(self.config_path)
        if profile != old_profile:
            self.profile_changed.emit(profile)
        self.accept()

