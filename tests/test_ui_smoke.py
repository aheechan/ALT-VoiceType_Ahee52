"""Offscreen Qt smoke tests.

Skipped when PySide6 is not installed. To run locally:

    pip install -e ".[ui]"
    $env:QT_QPA_PLATFORM="offscreen"
    python -m unittest tests.test_ui_smoke -v
"""

from __future__ import annotations

import importlib.util
import os
import time
import unittest
from pathlib import Path
from unittest import mock

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

    def test_setup_dialog_download_flow(self):
        from PySide6.QtWidgets import QMessageBox

        from altvoice.ui.setup_dialog import SetupDialog

        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            cfg.history.enabled = False
            report = check_health(cfg, "12gb-balanced")
            dialog = SetupDialog(report, cfg)
            dialog.show()
            self._events()

            def fake_download(_config, _profile, progress=None):
                if progress:
                    progress("fake download")
                return []

            with mock.patch(
                "altvoice.ui.setup_dialog.download_profile", side_effect=fake_download
            ) as download, mock.patch(
                "altvoice.ui.setup_dialog.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                dialog._start_download()
                for _ in range(100):
                    self._events()
                    if dialog.download_button.isEnabled():
                        break
                    time.sleep(0.01)
                self.assertTrue(download.called)
                self.assertTrue(dialog.download_button.isEnabled())
                self.assertIn("下载完成", dialog.status_label.text())
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

    def test_main_window_result_and_meter(self):
        from altvoice.ui.tray import MainWindow, TrayApp

        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            cfg = AppConfig()
            cfg.asr.engine = "fake"
            cfg.history.enabled = False
            cfg.save(path)
            tray = TrayApp(config_path=str(path))
            window = MainWindow(tray)
            try:
                window.show_panel()
                window.set_level(0.2)
                self.assertTrue(window.meter.isVisible())
                result = PipelineResult(
                    raw_text="你好",
                    corrected_text="你好",
                    translation="Hello",
                    target_lang="en",
                )
                window.show_result(result)
                self.assertTrue(window.result_frame.isVisible())
                window._copy_source()
                self.assertIn("已复制", window.source_copy.text())
                window.cancel_result()
                self.assertEqual(window.source_text.full_text(), "")
            finally:
                window.close()
                tray.controller.close()
                tray.tray.hide()

    def test_tray_panel_switches_to_transcription(self):
        from altvoice.ui.tray import TrayApp, TrayPanel

        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            cfg = AppConfig()
            cfg.asr.engine = "fake"
            cfg.history.enabled = False
            cfg.save(path)
            tray = TrayApp(config_path=str(path))
            panel = TrayPanel(tray)
            try:
                panel.show()
                self._events()
                index = panel.language.findData("zh")
                self.assertGreaterEqual(index, 0)
                panel.language.setCurrentIndex(index)
                self._events()
                self.assertEqual(tray.controller.target_lang, "zh")
                self.assertIn("直接转写", panel.mode_label.text())
            finally:
                panel.close()
                tray.controller.close()
                tray.tray.hide()


if __name__ == "__main__":
    unittest.main()
