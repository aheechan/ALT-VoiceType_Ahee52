import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from altvoice.correct.llm import LLMCorrector
from altvoice.translate.translator import IndexTranslateTranslator


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = json.dumps(
            {"choices": [{"message": {"content": self.server.response_text}}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class _Server:
    def __init__(self, response_text: str):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.httpd.response_text = response_text
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return f"http://127.0.0.1:{self.port}/v1"

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)


class LLMClientTests(unittest.TestCase):
    def test_corrector_http(self):
        payload = json.dumps({"text": "你好，世界。", "risk": 0.1, "edits": []})
        with _Server(payload) as base_url:
            corrector = LLMCorrector(base_url=base_url, model="fake", timeout_s=5)
            result = corrector.correct("你好世界")
            self.assertEqual(result.text, "你好，世界。")
            self.assertTrue(result.accepted)
            self.assertAlmostEqual(result.risk, 0.1)

    def test_translator_http(self):
        with _Server("Hello, world.") as base_url:
            translator = IndexTranslateTranslator(base_url=base_url, model="fake")
            result = translator.translate("你好，世界。", target_lang="en")
            self.assertEqual(result, "Hello, world.")

    def test_translator_skips_chinese_target(self):
        translator = IndexTranslateTranslator(base_url="http://127.0.0.1:1/v1", model="fake")
        self.assertEqual(translator.translate("你好", target_lang="zh"), "你好")


if __name__ == "__main__":
    unittest.main()
