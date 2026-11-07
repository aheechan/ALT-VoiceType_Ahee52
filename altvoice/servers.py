"""Local llama.cpp server supervision.

ALT-VoiceType talks to OpenAI-compatible endpoints. This module optionally starts
``llama-server`` for the corrector and translator, waits for ``/v1/models`` and
stops only the processes it started. If a server is already running, it is
reused rather than killed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .config import AppConfig, default_config_dir


class ServerError(RuntimeError):
    """Raised when a local model server cannot be started or becomes healthy."""


def bundled_llama_server() -> str:
    """Return the llama-server shipped next to a frozen executable, if any."""
    if not getattr(sys, "frozen", False):
        return ""
    candidate = Path(sys.executable).resolve().parent / "llama" / "llama-server.exe"
    return str(candidate) if candidate.is_file() else ""


def resolve_binary(binary: str) -> str:
    """Resolve llama-server from PATH, a bundled runtime, or winget."""
    if not binary:
        return ""
    bundled = bundled_llama_server()
    if bundled:
        return bundled
    candidate = Path(binary)
    if candidate.is_file():
        return str(candidate)
    found = shutil.which(binary)
    if found:
        return found
    if os.name == "nt" and candidate.name.lower() in ("llama-server", "llama-server.exe"):
        local = os.environ.get("LOCALAPPDATA")
        if local:
            packages = Path(local) / "Microsoft" / "WinGet" / "Packages"
            if packages.is_dir():
                for path in packages.glob("ggml.llamacpp_*/llama-server.exe"):
                    if path.is_file():
                        return str(path)
    return ""


@dataclass
class ServerSpec:
    name: str
    binary: str
    model_path: str
    host: str
    port: int
    alias: str
    context_size: int = 4096
    gpu_layers: int = 99
    extra_args: list[str] = field(default_factory=list)
    log_dir: str | None = None

    def command(self) -> list[str]:
        return [
            self.binary,
            "-m",
            self.model_path,
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--alias",
            self.alias,
            "-c",
            str(self.context_size),
            "-ngl",
            str(self.gpu_layers),
            *self.extra_args,
        ]

    def health_url(self) -> str:
        host = "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host
        return f"http://{host}:{self.port}/v1/models"

    def log_path(self) -> Path:
        base = Path(self.log_dir) if self.log_dir else default_config_dir() / "logs"
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{self.name}.log"


class LlamaServer:
    def __init__(self, spec: ServerSpec) -> None:
        self.spec = spec
        self._process: subprocess.Popen | None = None
        self._log_handle = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def is_ready(self, timeout_s: float = 1.0) -> bool:
        try:
            with urllib.request.urlopen(self.spec.health_url(), timeout=timeout_s) as response:
                if response.status != 200:
                    return False
                body = response.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            return isinstance(data, dict) and isinstance(data.get("data"), list)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
            return False

    def start(self) -> bool:
        """Start the server. Returns True when a new process was launched."""
        if self.is_ready():
            return False
        if self.running:
            return False
        if not Path(self.spec.model_path).exists():
            raise ServerError(
                f"{self.spec.name}: model path does not exist: {self.spec.model_path}"
            )
        binary = resolve_binary(self.spec.binary)
        if not binary:
            raise ServerError(
                f"{self.spec.name}: cannot find '{self.spec.binary}'. Install llama.cpp "
                "(`winget install ggml.llamacpp`) or set servers.binary to the full path."
            )
        log_path = self.spec.log_path()
        self._log_handle = log_path.open("a", encoding="utf-8", errors="replace")
        self._log_handle.write(f"\n--- start {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        self._log_handle.flush()
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        command = self.spec.command()
        command[0] = binary
        try:
            self._process = subprocess.Popen(
                command,
                stdout=self._log_handle,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=flags,
            )
        except OSError as exc:
            raise ServerError(f"{self.spec.name}: failed to launch: {exc}") from exc
        return True

    def wait_ready(self, timeout_s: float = 90.0) -> None:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.is_ready():
                return
            if self._process is not None and self._process.poll() is not None:
                raise ServerError(
                    f"{self.spec.name}: process exited with {self._process.returncode}; "
                    f"see {self.spec.log_path()}"
                )
            time.sleep(0.5)
        raise ServerError(
            f"{self.spec.name}: not ready after {timeout_s:.0f}s; see {self.spec.log_path()}"
        )

    def probe(self, timeout_s: float = 25.0) -> None:
        """Run one tiny completion to catch a server that is up but cannot infer.

        Some newer GPU/driver combinations expose a healthy HTTP endpoint while
        the accelerator path still hangs. A real request is the only reliable
        check before handing the server to the dictation pipeline.
        """
        payload = json.dumps(
            {
                "model": self.spec.alias,
                "messages": [{"role": "user", "content": "ok"}],
                "temperature": 0.0,
                "max_tokens": 1,
                "stream": False,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            self.spec.health_url().replace("/models", "/chat/completions"),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_s) as response:
                body = response.read().decode("utf-8", errors="replace")
                if response.status != 200:
                    raise ServerError(f"{self.spec.name}: probe returned {response.status}")
            data = json.loads(body)
            if not isinstance(data.get("choices"), list):
                raise ServerError(f"{self.spec.name}: probe response has no choices")
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise ServerError(f"{self.spec.name}: inference probe failed: {exc}") from exc

    def stop(self) -> None:
        process = self._process
        self._process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    pass
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None


class ServerManager:
    def __init__(self, servers: list[LlamaServer] | None = None) -> None:
        self.servers = servers or []
        self.failed: set[str] = set()

    @classmethod
    def from_config(cls, config: AppConfig, profile: str | None = None) -> "ServerManager":
        if not config.servers.enabled:
            return cls([])
        active_profile = profile or config.profile
        specs: list[ServerSpec] = []
        for name, cfg, default_port in (
            ("corrector", config.corrector, 8091),
            ("translator", config.translator, 8092),
        ):
            if not cfg.enabled or not cfg.autostart or not cfg.model_path:
                continue
            parsed = urlparse(cfg.base_url)
            if parsed.hostname not in ("127.0.0.1", "localhost", "::1", None):
                continue
            port = parsed.port or default_port
            extra_args = list(config.servers.extra_args)
            if "--reasoning" not in extra_args:
                # Qwen3 templates may otherwise put everything in
                # message.reasoning_content and leave message.content empty.
                extra_args += ["--reasoning", "off"]
            specs.append(
                ServerSpec(
                    name=name,
                    binary=config.servers.binary,
                    model_path=cfg.model_path,
                    host=config.servers.host,
                    port=port,
                    alias=cfg.model,
                    context_size=config.servers.context_size,
                    gpu_layers=0 if active_profile == "cpu-safe" else config.servers.gpu_layers,
                    extra_args=extra_args,
                    log_dir=config.servers.log_dir,
                )
            )
        return cls([LlamaServer(spec) for spec in specs])

    def start_all(self, on_status=None) -> list[str]:
        status = on_status or (lambda _msg: None)
        errors: list[str] = []
        self.failed.clear()
        for server in self.servers:
            try:
                if server.is_ready():
                    status(f"{server.spec.name} 服务已在运行")
                else:
                    status(f"启动 {server.spec.name} 模型服务…")
                    server.start()
                    server.wait_ready(timeout_s=30.0)
                server.probe(timeout_s=15.0)
                status(f"{server.spec.name} 服务就绪")
            except Exception as exc:
                errors.append(str(exc))
                self.failed.add(server.spec.name)
        return errors

    def stop_all(self) -> None:
        for server in self.servers:
            try:
                server.stop()
            except Exception:
                pass

