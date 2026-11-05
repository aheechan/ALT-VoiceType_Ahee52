"""Offscreen Qt smoke tests.

Skipped when PySide6 is not installed. To run locally:

    pip install -e ".[ui]"
    $env:QT_QPA_PLATFORM="offscreen"
    python -m unittest tests.test_ui_smoke -v
"""

from __future__ import annotations

import importlib.util
import os
import unittest
from pathlib import Path

HAS_PYSIDE6 = importlib.util.find_spec("PySide6") is not None
if HAS_PYSIDE6:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from altvoice.config import AppConfig
from altvoice.health import check_health
from altvoice.history import HistoryStore
from altvoice.pipeline import PipelineResult
from tests.helpers import workspace_tempdir


@unittest.skipUnless(HAS_PYSIDE6, "PySide6 is not installed")
class UiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        cls.app = QApplication.instance() or QApplication([])

    def _events(self):
        self.app.processEvents()

    def test_setup_dialog(self):
        from altvoice.ui.setup_dialog import SetupDialog

        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            cfg.history.enabled = False
            report = check_health(cfg, "12gb-balanced")
            dialog = SetupDialog(report, cfg)
            dialog.show()
            self._events()
            self.assertTrue(dialog.isVisible())
            self.assertIn("环境检查", dialog.windowTitle())
            dialog._copy_commands()
            dialog.close()

    def test_history_dialog_and_preview(self):
        from altvoice.ui.history_dialog import HistoryDialog
        from altvoice.ui.tray import PreviewDialog

        with workspace_tempdir() as tmp:
            store = HistoryStore(Path(tmp) / "history.db")
            store.add_utterance("你好", "你好。", "Hello.", "en")
            dialog = HistoryDialog(store)
            dialog.show()
            self._events()
            self.assertEqual(dialog.list.count(), 1)
            dialog.close()
            store.close()

            result = PipelineResult(
                raw_text="你好",
                corrected_text="你好。",
                translation="Hello.",
                target_lang="en",
                source_lang="zh",
                engine="fake",
            )
            preview = PreviewDialog(result)
            preview.show()
            self._events()
            self.assertEqual(preview.text(), "Hello.")
            preview.close()

    def test_tray_menu_and_icon(self):
        from altvoice.ui.tray import TrayApp, _make_icon

        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            cfg = AppConfig()
            cfg.asr.engine = "fake"
            cfg.history.enabled = False
            cfg.save(path)
            tray = TrayApp(config_path=str(path))
            try:
                self.assertTrue(tray.menu.actions())
                self.assertFalse(_make_icon().isNull())
            finally:
                tray.controller.close()
                tray.tray.hide()


if __name__ == "__main__":
    unittest.main()
