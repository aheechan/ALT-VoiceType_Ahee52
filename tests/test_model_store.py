import unittest
from pathlib import Path

from altvoice.config import AppConfig
from altvoice.model_store import all_present, download_commands, locations, model_path
from altvoice.models import MODEL_CATALOG
from tests.helpers import workspace_tempdir


class ModelStoreTests(unittest.TestCase):
    def test_paths_and_commands(self):
        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            items = locations(cfg, "12gb-balanced")
            self.assertEqual(len(items), 3)
            roles = {item.role for item in items}
            self.assertEqual(roles, {"asr", "corrector", "translator"})
            self.assertFalse(all_present(cfg, "12gb-balanced"))
            commands = download_commands(cfg, "12gb-balanced")
            joined = "\n".join(commands)
            self.assertIn("Qwen/Qwen3-ASR-0.6B", joined)
            self.assertIn("IndexTeam/Index-Translate-2B-GGUF", joined)

    def test_exists_for_dir_and_file(self):
        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            asr = MODEL_CATALOG["qwen3_asr_0_6b"]
            asr_path = model_path(cfg, asr)
            asr_path.mkdir(parents=True)
            (asr_path / "config.json").write_text("{}", encoding="utf-8")
            corrector = MODEL_CATALOG["qwen3_1_7b_abliterated_q4"]
            corrector_path = model_path(cfg, corrector)
            corrector_path.parent.mkdir(parents=True, exist_ok=True)
            corrector_path.write_bytes(b"gguf")
            items = {item.key: item for item in locations(cfg, "12gb-balanced")}
            self.assertTrue(items["qwen3_asr_0_6b"].exists)
            self.assertTrue(items["qwen3_1_7b_abliterated_q4"].exists)
            self.assertFalse(items["index_translate_2b_q4"].exists)

    def test_none_kind_is_present(self):
        cfg = AppConfig()
        cfg.models_dir = "Z:/does/not/exist"
        items = {item.key: item for item in locations(cfg, "cpu-safe")}
        self.assertTrue(items["rules_only"].exists)


if __name__ == "__main__":
    unittest.main()
