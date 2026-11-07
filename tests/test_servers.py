import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from altvoice.config import AppConfig
from altvoice.servers import (
    LlamaServer,
    ServerError,
    ServerManager,
    ServerSpec,
    resolve_binary,
)


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/v1/models":
            body = json.dumps({"object": "list", "data": [{"id": "test"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class ServerSpecTests(unittest.TestCase):
    def test_resolve_python(self):
        self.assertEqual(resolve_binary(sys.executable), sys.executable)

    def test_resolve_missing(self):
        self.assertEqual(resolve_binary("definitely-not-a-real-binary-xyz"), "")

    def test_command(self):
        spec = ServerSpec(
            name="corrector",
            binary="llama-server",
            model_path="C:/models/corrector.gguf",
            host="127.0.0.1",
            port=8091,
            alias="qwen3-1.7b-instruct",
            context_size=4096,
            gpu_layers=99,
            extra_args=["--no-webui"],
        )
        command = spec.command()
        self.assertEqual(command[0], "llama-server")
        self.assertIn("-m", command)
        self.assertIn("C:/models/corrector.gguf", command)
        self.assertIn("--port", command)
        self.assertIn("8091", command)
        self.assertIn("--alias", command)
        self.assertIn("-ngl", command)
        self.assertIn("99", command)
        self.assertIn("--no-webui", command)

    def test_health_url(self):
        spec = ServerSpec("x", "b", "m", "0.0.0.0", 9000, "a")
        self.assertEqual(spec.health_url(), "http://127.0.0.1:9000/v1/models")


class ManagerConfigTests(unittest.TestCase):
    def _config(self):
        cfg = AppConfig()
        cfg.corrector.model_path = "C:/models/corrector.gguf"
        cfg.translator.model_path = "C:/models/translator.gguf"
        cfg.corrector.base_url = "http://127.0.0.1:8091/v1"
        cfg.translator.base_url = "http://127.0.0.1:8092/v1"
        return cfg

    def test_from_config_creates_two_servers(self):
        manager = ServerManager.from_config(self._config(), profile="12gb-balanced")
        self.assertEqual(len(manager.servers), 2)
        names = {s.spec.name for s in manager.servers}
        self.assertEqual(names, {"corrector", "translator"})
        self.assertEqual(manager.servers[0].spec.gpu_layers, 99)

    def test_cpu_profile_uses_zero_gpu_layers(self):
        manager = ServerManager.from_config(self._config(), profile="cpu-safe")
        for server in manager.servers:
            self.assertEqual(server.spec.gpu_layers, 0)

    def test_autostart_false_is_skipped(self):
        cfg = self._config()
        cfg.translator.autostart = False
        manager = ServerManager.from_config(cfg)
        self.assertEqual(len(manager.servers), 1)

    def test_remote_base_url_is_not_started(self):
        cfg = self._config()
        cfg.translator.base_url = "https://api.example.com/v1"
        manager = ServerManager.from_config(cfg)
        self.assertEqual(len(manager.servers), 1)

    def test_disabled_servers(self):
        cfg = self._config()
        cfg.servers.enabled = False
        manager = ServerManager.from_config(cfg)
        self.assertEqual(manager.servers, [])


class HealthTests(unittest.TestCase):
    def test_is_ready_against_local_http(self):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            spec = ServerSpec("x", "b", "m", "127.0.0.1", port, "a")
            self.assertTrue(LlamaServer(spec).is_ready())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_is_ready_false_for_closed_port(self):
        spec = ServerSpec("x", "b", "m", "127.0.0.1", 9, "a")
        self.assertFalse(LlamaServer(spec).is_ready(timeout_s=0.2))

    def test_missing_model_raises(self):
        spec = ServerSpec("x", "llama-server", "Z:/does/not/exist.gguf", "127.0.0.1", 9, "a")
        with self.assertRaises(ServerError):
            LlamaServer(spec).start()


class FakeServer:
    def __init__(self, ready=False, fail=False):
        self.spec = ServerSpec("fake", "b", "m", "127.0.0.1", 1, "a")
        self.ready = ready
        self.fail = fail
        self.started = False

    def is_ready(self):
        return self.ready

    def start(self):
        if self.fail:
            raise ServerError("boom")
        self.started = True

    def wait_ready(self, timeout_s=90.0):
        return None

    def probe(self, timeout_s=15.0):
        return None

    def stop(self):
        self.started = False


class ManagerRunTests(unittest.TestCase):
    def test_start_all_reuses_ready_and_reports_errors(self):
        running = FakeServer(ready=True)
        failing = FakeServer(fail=True)
        manager = ServerManager([running, failing])  # type: ignore[list-item]
        errors = manager.start_all()
        self.assertEqual(len(errors), 1)
        self.assertIn("boom", errors[0])
        self.assertFalse(running.started)

    def test_stop_all(self):
        fake = FakeServer()
        fake.started = True
        manager = ServerManager([fake])  # type: ignore[list-item]
        manager.stop_all()
        self.assertFalse(fake.started)


if __name__ == "__main__":
    unittest.main()
