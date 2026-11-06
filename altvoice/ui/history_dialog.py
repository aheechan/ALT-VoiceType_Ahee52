"""History and glossary viewer/editor."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from ..history import HistoryStore


class HistoryDialog(QDialog):
    def __init__(self, store: HistoryStore, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("ALT-VoiceType · 历史与术语")
        self.resize(760, 580)
        self.setStyleSheet(
            "QDialog { background: #1f2329; color: #e8eaed; }"
            "QLabel { color: #c6ccd6; }"
            "QListWidget, QTableWidget, QLineEdit { background: #15181d; color: #dfe5ee;"
            " border: 1px solid #3a404a; border-radius: 6px; }"
            "QPushButton { background: #2d7ff9; color: white; border: 0; padding: 6px 12px;"
            " border-radius: 6px; }"
            "QPushButton#secondary { background: #3a404a; }"
            "QHeaderView::section { background: #2a2f37; color: #c6ccd6; padding: 4px; }"
        )

        layout = QVBoxLayout(self)
        title = QLabel("最近识别")
        title.setStyleSheet("font-size: 16px; font-weight: 600; color: #f2f4f7;")
        layout.addWidget(title)

        self.list = QListWidget()
        layout.addWidget(self.list, 1)

        action_row = QHBoxLayout()
        refresh = QPushButton("刷新")
        refresh.setObjectName("secondary")
        refresh.clicked.connect(self.refresh)
        clear = QPushButton("清空历史与术语")
        clear.setObjectName("secondary")
        clear.clicked.connect(self._clear)
        action_row.addWidget(refresh)
        action_row.addWidget(clear)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        glossary_title = QLabel("术语表")
        glossary_title.setStyleSheet(
            "font-size: 16px; font-weight: 600; color: #f2f4f7; margin-top: 8px;"
        )
        layout.addWidget(glossary_title)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["原文 / 术语", "译文 / 替换"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

        add_row = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("术语，例如 碳纤维")
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("译文，例如 carbon fiber")
        add = QPushButton("添加")
        add.clicked.connect(self._add_term)
        remove = QPushButton("删除选中")
        remove.setObjectName("secondary")
        remove.clicked.connect(self._remove_term)
        save = QPushButton("保存术语表")
        save.clicked.connect(self._save_glossary)
        add_row.addWidget(self.source_input)
        add_row.addWidget(self.target_input)
        add_row.addWidget(add)
        add_row.addWidget(remove)
        add_row.addWidget(save)
        layout.addLayout(add_row)

        close = QPushButton("关闭")
        close.setObjectName("secondary")
        close.clicked.connect(self.accept)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        bottom.addWidget(close)
        layout.addLayout(bottom)

        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        for item in self.store.recent(50):
            translation = item.get("translation") or ""
            text = item.get("corrected") or item.get("source") or ""
            if translation and translation != text:
                text = f"{text}  →  {translation}"
            self.list.addItem(text)
        glossary = self.store.get_glossary()
        self.table.setRowCount(0)
        for source, target in glossary.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(source))
            self.table.setItem(row, 1, QTableWidgetItem(target))

    def _add_term(self) -> None:
        source = self.source_input.text().strip()
        target = self.target_input.text().strip()
        if not source or not target:
            return
        self.store.learn_term(source, target)
        self.source_input.clear()
        self.target_input.clear()
        self.refresh()

    def _remove_term(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        self.table.removeRow(row)

    def _save_glossary(self) -> None:
        glossary: dict[str, str] = {}
        for row in range(self.table.rowCount()):
            source_item = self.table.item(row, 0)
            target_item = self.table.item(row, 1)
            source = source_item.text().strip() if source_item else ""
            target = target_item.text().strip() if target_item else ""
            if source and target:
                glossary[source] = target
        self.store.set_glossary(glossary)
        self.refresh()

    def _clear(self) -> None:
        answer = QMessageBox.question(
            self,
            "ALT-VoiceType",
            "清空全部本地历史和术语表？此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.store.clear()
            self.refresh()

