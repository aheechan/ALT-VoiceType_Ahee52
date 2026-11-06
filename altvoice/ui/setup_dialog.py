"""First-run / environment-check dialog."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..config import AppConfig
from ..downloader import download_profile
from ..health import HealthReport, format_report
from ..model_store import download_commands


class SetupDialog(QDialog):
    recheck_requested = Signal()
    download_progress = Signal(str)
    download_finished = Signal(list)

    def __init__(self, report: HealthReport, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.report = report
        self.config = config
        self.setWindowTitle("ALT-VoiceType · 环境检查")
        self.resize(760, 560)
        self.setStyleSheet(
            "QDialog { background: #1f2329; color: #e8eaed; }"
            "QLabel { color: #c6ccd6; }"
            "QTextEdit { background: #15181d; color: #dfe5ee; border: 1px solid #3a404a;"
            " border-radius: 6px; padding: 10px; font-family: Consolas, monospace; }"
            "QPushButton { background: #2d7ff9; color: white; border: 0; padding: 7px 14px;"
            " border-radius: 6px; }"
            "QPushButton#secondary { background: #3a404a; }"
        )

        layout = QVBoxLayout(self)
        title = QLabel("ALT-VoiceType 尚未就绪" if not report.ready else "ALT-VoiceType 已就绪")
        title.setStyleSheet("font-size: 18px; font-weight: 600; color: #f2f4f7;")
        layout.addWidget(title)

        if report.ready:
            summary = "模型、麦克风、托盘依赖均已检测到。"
        elif report.config_ready:
            summary = "模型已就绪，但麦克风或 PySide6 仍缺失。"
        else:
            summary = "缺少模型或 ASR 引擎。按下面的路径放置模型，或运行下载命令。"
        subtitle = QLabel(summary)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #8b93a1; font-size: 12px;")
        layout.addWidget(self.status_label)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(format_report(report, config=config))
        layout.addWidget(self.text, 1)

        buttons = QHBoxLayout()
        self.download_button = QPushButton("下载缺失模型")
        self.download_button.setEnabled(bool(report.missing_models))
        self.download_button.clicked.connect(self._start_download)
        copy_button = QPushButton("复制下载命令")
        copy_button.setObjectName("secondary")
        copy_button.clicked.connect(self._copy_commands)
        folder_button = QPushButton("打开模型目录")
        folder_button.setObjectName("secondary")
        folder_button.clicked.connect(self._open_models)
        recheck_button = QPushButton("重新检查")
        recheck_button.setObjectName("secondary")
        recheck_button.clicked.connect(self.recheck_requested.emit)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(self.download_button)
        buttons.addWidget(copy_button)
        buttons.addWidget(folder_button)
        buttons.addWidget(recheck_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.download_progress.connect(self._on_download_progress)
        self.download_finished.connect(self._on_download_finished)

    def _start_download(self) -> None:
        missing = self.report.missing_models
        if not missing:
            return
        answer = QMessageBox.question(
            self,
            "ALT-VoiceType",
            f"将下载 {len(missing)} 个缺失模型（可能数 GB）。继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.download_button.setEnabled(False)
        self.download_button.setText("下载中…")
        self.status_label.setText("开始下载，请保持网络连接…")

        def worker() -> None:
            errors = download_profile(
                self.config,
                self.report.profile,
                progress=self.download_progress.emit,
            )
            self.download_finished.emit(errors)

        threading.Thread(target=worker, name="altvoice-download", daemon=True).start()

    def _on_download_progress(self, message: str) -> None:
        self.status_label.setText(message)

    def _on_download_finished(self, errors: list[str]) -> None:
        self.download_button.setEnabled(True)
        self.download_button.setText("下载缺失模型")
        if errors:
            self.status_label.setText("部分模型下载失败。")
            QMessageBox.warning(self, "ALT-VoiceType", "\n".join(errors[:5]))
            return
        self.status_label.setText("下载完成，正在重新检查…")
        self.recheck_requested.emit()

    def _copy_commands(self) -> None:
        commands = download_commands(self.config, self.report.profile)
        QGuiApplication.clipboard().setText("\n".join(commands))

    def _open_models(self) -> None:
        path = Path(self.config.models_dir)
        path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

