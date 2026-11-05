"""Settings dialog for the rolled-back compact tray UI."""

from __future__ import annotations

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
from ..models import PROFILES


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, config_path: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self.config_path = config_path
        self.setWindowTitle("AltVoice · 设置")
        self.setMinimumWidth(430)
        self.setStyleSheet(
            "QDialog { background: #1f2329; color: #e8eaed; }"
            "QLabel { color: #c6ccd6; }"
            "QComboBox { background: #2a2f37; color: #eef2f8; border: 1px solid #3a404a;"
            " border-radius: 6px; padding: 6px; min-height: 22px; }"
            "QCheckBox { color: #c6ccd6; }"
            "QPushButton { background: #2d7ff9; color: white; border: 0; padding: 6px 12px;"
            " border-radius: 6px; }"
        )
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.profile = QComboBox()
        for name, info in PROFILES.items():
            self.profile.addItem(f"{name} — {info.get('description', '')}", name)
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
        self.config.profile = self.profile.currentData()
        self.config.ui.preview = self.preview.isChecked()
        self.config.save(self.config_path)
        self.accept()
