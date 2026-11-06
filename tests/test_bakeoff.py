import json
import unittest
from pathlib import Path

from tests.helpers import workspace_tempdir
from altvoice.bakeoff import (
    Case,
    character_error_rate,
    load_manifest,
    normalize_for_cer,
    run_engine,
    write_report,
)
from altvoice.audio import write_wav
import numpy as np


class CerTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize_for_cer("你好，世界！ Hello."), "你好世界hello")
        self.assertEqual(normalize_for_cer("  A B  "), "ab")

    def test_cer(self):
        self.assertEqual(character_error_rate("你好", "你好"), 0.0)
        self.assertAlmostEqual(character_error_rate("你好", "你号"), 0.5)
        self.assertIsNone(character_error_rate("", "你号"))

    def test_cer_ignores_punctuation(self):
        self.assertEqual(character_error_rate("你好，世界。", "你好世界"), 0.0)


class ManifestTests(unittest.TestCase):
    def test_load_jsonl(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            (root / "a.wav").write_bytes(b"")
            manifest = root / "m.jsonl"
            manifest.write_text(
                json.dumps({"id": "a", "audio": "a.wav", "reference": "你好"}) + "\n",
                encoding="utf-8",
            )
            cases = load_manifest(manifest)
            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0].case_id, "a")
            self.assertEqual(cases[0].audio, (root / "a.wav").resolve())
            self.assertEqual(cases[0].reference, "你好")

    def test_load_json_object(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            manifest = root / "m.json"
            manifest.write_text(
                json.dumps({"cases": [{"id": "b", "audio": "b.wav"}]}),
                encoding="utf-8",
            )
            cases = load_manifest(manifest)
            self.assertEqual(cases[0].case_id, "b")


class FakeEngineTests(unittest.TestCase):
    def test_run_fake_engine(self):
        with workspace_tempdir() as tmp:
            root = Path(tmp)
            audio = root / "a.wav"
            write_wav(audio, np.zeros(1600, dtype=np.float32), 16000)
            report = run_engine("fake", [Case("a", audio, "这是一条测试语音。")])
            self.assertTrue(report["loaded"])
            self.assertEqual(report["summary"]["total"], 1)
            self.assertEqual(report["summary"]["ok"], 1)
            self.assertEqual(report["summary"]["cer_mean"], 0.0)

    def test_write_report(self):
        with workspace_tempdir() as tmp:
            report = {
                "engines": {
                    "fake": {
                        "results": [
                            {"case_id": "a", "cer": 0.0, "latency_ms": 1.0, "error": "", "text": "你好"}
                        ]
                    }
                }
            }
            json_path, csv_path = write_report(report, tmp)
            self.assertTrue(json_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertIn("fake,a", csv_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
