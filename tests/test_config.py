import json
import unittest
from pathlib import Path

from tests.helpers import workspace_tempdir
from altvoice.config import (
    AppConfig,
    LANGUAGES,
    language_display,
    language_prompt_name,
    normalize_language,
)
from altvoice.models import (
    PROFILES,
    estimate_vram,
    profile_models,
    select_profile,
)


class ConfigTests(unittest.TestCase):
    def test_language_normalization(self):
        self.assertEqual(normalize_language("Chinese"), "zh")
        self.assertEqual(normalize_language("zh-CN"), "zh")
        self.assertEqual(normalize_language("日本語"), "ja")
        self.assertEqual(language_display("en"), "English")
        self.assertIn("Chinese", language_prompt_name("zh"))

    def test_default_config_validates(self):
        cfg = AppConfig()
        cfg.validate()
        self.assertEqual(cfg.profile, "auto")
        self.assertEqual(cfg.asr.language, "zh")
        self.assertIn(cfg.translator.target_language, LANGUAGES)

    def test_config_roundtrip(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "config.json"
            cfg = AppConfig()
            cfg.translator.target_language = "ja"
            cfg.translator.style = "live"
            cfg.hotkey.threshold_ms = 320
            cfg.save(path)
            loaded = AppConfig.load(path)
            self.assertEqual(loaded.translator.target_language, "ja")
            self.assertEqual(loaded.translator.style, "live")
            self.assertEqual(loaded.hotkey.threshold_ms, 320)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["asr"]["engine"], "auto")

    def test_invalid_target_language(self):
        cfg = AppConfig()
        cfg.translator.target_language = "xx"
        with self.assertRaises(ValueError):
            cfg.validate()

    def test_invalid_injection_method(self):
        cfg = AppConfig()
        cfg.injection.method = "telepathy"
        with self.assertRaises(ValueError):
            cfg.validate()


class ProfileTests(unittest.TestCase):
    def test_auto_profile_selection(self):
        self.assertEqual(select_profile(12.0), "12gb-balanced")
        self.assertEqual(select_profile(8.0), "12gb-safe")
        self.assertEqual(select_profile(4.0), "cpu-safe")
        self.assertEqual(select_profile(16.0), "12gb-max")
        self.assertEqual(select_profile(24.0), "12gb-max")
        self.assertEqual(select_profile(None), "cpu-safe")
        self.assertEqual(select_profile(12.0, "12gb-safe"), "12gb-safe")

    def test_12gb_profile_fits(self):
        self.assertLess(estimate_vram("12gb-balanced"), 10.0)
        models = profile_models("12gb-balanced")
        self.assertEqual(models["asr"].key, "qwen3_asr_0_6b")
        self.assertEqual(models["translator"].key, "index_translate_2b_q4")
        self.assertLess(estimate_vram("12gb-max"), 12.0)

    def test_all_profiles_have_three_roles(self):
        for name in PROFILES:
            models = profile_models(name)
            self.assertEqual(set(models), {"asr", "corrector", "translator"})

    def test_unknown_profile(self):
        with self.assertRaises(ValueError):
            select_profile(12.0, "nope")


if __name__ == "__main__":
    unittest.main()
