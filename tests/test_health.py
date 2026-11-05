import unittest
from pathlib import Path

from altvoice.config import AppConfig
from altvoice.health import check_health, format_report
from altvoice.model_store import locations
from tests.helpers import workspace_tempdir


class HealthTests(unittest.TestCase):
    def test_missing_models_report(self):
        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            report = check_health(cfg, "12gb-balanced")
            self.assertFalse(report.models_ready)
            self.assertFalse(report.config_ready)
            text = format_report(report, config=cfg)
            self.assertIn("MISSING", text)
            self.assertIn("Download commands", text)

    def test_all_models_and_fake_engine_config_ready(self):
        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            cfg.asr.engine = "fake"
            for item in locations(cfg, "12gb-balanced"):
                if item.kind == "dir":
                    item.path.mkdir(parents=True, exist_ok=True)
                    (item.path / "config.json").write_text("{}", encoding="utf-8")
                elif item.kind == "file":
                    item.path.parent.mkdir(parents=True, exist_ok=True)
                    item.path.write_bytes(b"gguf")
            report = check_health(cfg, "12gb-balanced")
            self.assertTrue(report.models_ready)
            self.assertTrue(report.asr_ready)
            self.assertTrue(report.config_ready)
            # The test environment has no microphone/PySide6.
            self.assertFalse(report.ready)

    def test_unknown_engine_not_ready(self):
        cfg = AppConfig()
        cfg.asr.engine = "does-not-exist"
        report = check_health(cfg, "cpu-safe")
        self.assertFalse(report.asr_ready)


if __name__ == "__main__":
    unittest.main()
