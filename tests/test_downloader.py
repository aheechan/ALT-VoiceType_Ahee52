import unittest

from altvoice.config import AppConfig
from altvoice.downloader import download_profile
from altvoice.model_store import locations
from tests.helpers import workspace_tempdir


class DownloaderTests(unittest.TestCase):
    def test_all_present_returns_no_errors(self):
        with workspace_tempdir() as tmp:
            cfg = AppConfig()
            cfg.models_dir = tmp
            for item in locations(cfg, "12gb-balanced"):
                if item.kind == "dir":
                    item.path.mkdir(parents=True, exist_ok=True)
                    (item.path / "config.json").write_text("{}", encoding="utf-8")
                elif item.kind == "file":
                    item.path.parent.mkdir(parents=True, exist_ok=True)
                    item.path.write_bytes(b"gguf")
            self.assertEqual(download_profile(cfg, "12gb-balanced"), [])


if __name__ == "__main__":
    unittest.main()
