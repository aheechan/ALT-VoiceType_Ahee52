import io
import unittest
from pathlib import Path

from altvoice.config import AppConfig
from altvoice.setup_wizard import build_config, run_setup
from tests.helpers import workspace_tempdir


class SetupTests(unittest.TestCase):
    def test_build_12gb_config(self):
        with workspace_tempdir() as tmp:
            cfg = build_config("12gb-balanced", tmp, "ja")
            self.assertEqual(cfg.profile, "12gb-balanced")
            self.assertEqual(cfg.asr.engine, "qwen3")
            self.assertIn("qwen3_asr_0_6b", cfg.asr.model_path or "")
            self.assertTrue(cfg.corrector.enabled)
            self.assertTrue(cfg.corrector.autostart)
            self.assertTrue(cfg.corrector.model_path.endswith("Qwen3-1.7B-abliterated-v2.i1-Q4_K_M.gguf"))
            self.assertTrue(cfg.translator.model_path.endswith("Index-Translate-2B.Q4_K_M.gguf"))
            self.assertEqual(cfg.translator.target_language, "ja")

    def test_cpu_safe_disables_corrector(self):
        cfg = build_config("cpu-safe", "Z:/models")
        self.assertEqual(cfg.asr.engine, "sherpa")
        self.assertFalse(cfg.corrector.enabled)
        self.assertFalse(cfg.corrector.autostart)

    def test_run_setup_writes_config(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            code = run_setup(
                profile="12gb-balanced",
                models_dir=tmp,
                config_path=path,
                show_commands=False,
                out=io.StringIO(),
            )
            self.assertEqual(code, 0)
            self.assertTrue(path.exists())
            loaded = AppConfig.load(path)
            self.assertEqual(loaded.asr.engine, "qwen3")

    def test_run_setup_refuses_overwrite(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text("{}", encoding="utf-8")
            code = run_setup(config_path=path, show_commands=False, out=io.StringIO())
            self.assertEqual(code, 2)

    def test_print_only_does_not_write(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            code = run_setup(
                config_path=path,
                print_only=True,
                show_commands=False,
                out=io.StringIO(),
            )
            self.assertEqual(code, 0)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
