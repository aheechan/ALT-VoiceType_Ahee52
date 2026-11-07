"""Environment and model readiness checks shared by CLI and tray UI."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field

from .config import AppConfig
from .model_store import ModelLocation, download_commands, locations
from .models import detect_vram_gb, select_profile


@dataclass
class HealthReport:
    profile: str
    models_dir: str
    vram_gb: float | None
    ffmpeg: str | None
    models: list[ModelLocation]
    asr_engines: dict[str, bool]
    microphone_available: bool
    microphone_inputs: int
    ui_available: bool
    server_count: int = 0
    server_ready: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def missing_models(self) -> list[ModelLocation]:
        return [item for item in self.models if not item.exists]

    @property
    def models_ready(self) -> bool:
        return not self.missing_models

    @property
    def asr_engine(self) -> str:
        return self.asr_engines.get("_requested", "auto")

    @property
    def asr_ready(self) -> bool:
        if self.asr_engine in ("auto", ""):
            return any(
                self.asr_engines.get(name, False)
                for name in ("firered", "qwen3", "sherpa", "fake")
            )
        return bool(self.asr_engines.get(self.asr_engine, False))

    @property
    def ready(self) -> bool:
        return (
            self.models_ready
            and self.asr_ready
            and self.microphone_available
            and self.ui_available
        )

    @property
    def config_ready(self) -> bool:
        return self.models_ready and self.asr_ready


def check_health(
    config: AppConfig,
    profile: str | None = None,
    check_servers: bool = False,
) -> HealthReport:
    from .asr import available_engines

    active = profile or select_profile(detect_vram_gb(), config.profile)
    engines = available_engines()
    engines["_requested"] = (config.asr.engine or "auto").strip().lower()
    items = locations(config, active)
    server_count = 0
    server_ready = 0
    notes: list[str] = []
    if check_servers:
        from .servers import ServerManager

        manager = ServerManager.from_config(config, active)
        server_count = len(manager.servers)
        for server in manager.servers:
            if server.is_ready(timeout_s=0.5):
                server_ready += 1
    if not config.asr.model_path and engines["_requested"] in ("qwen3", "auto"):
        notes.append("Qwen3-ASR will download its default checkpoint on first load if missing.")
    microphone_inputs = 0
    if importlib.util.find_spec("sounddevice") is not None:
        try:
            import sounddevice as sd

            microphone_inputs = sum(
                1 for device in sd.query_devices() if device.get("max_input_channels", 0) > 0
            )
        except Exception as exc:
            notes.append(f"microphone query failed: {exc}")
    if importlib.util.find_spec("sounddevice") is not None and microphone_inputs == 0:
        notes.append("sounddevice is installed, but no microphone input device was found.")
    return HealthReport(
        profile=active,
        models_dir=str(config.models_dir),
        vram_gb=detect_vram_gb(),
        ffmpeg=shutil.which("ffmpeg"),
        models=items,
        asr_engines=engines,
        microphone_available=microphone_inputs > 0,
        microphone_inputs=microphone_inputs,
        ui_available=importlib.util.find_spec("PySide6") is not None,
        server_count=server_count,
        server_ready=server_ready,
        notes=notes,
    )


def format_report(
    report: HealthReport,
    config: AppConfig | None = None,
    show_commands: bool = True,
) -> str:
    lines: list[str] = [
        f"Profile: {report.profile}",
        f"VRAM: {f'{report.vram_gb:.1f} GB' if report.vram_gb else 'not detected'}",
        f"ffmpeg: {report.ffmpeg or 'NOT FOUND'}",
        f"Microphone (sounddevice): {'yes' if report.microphone_available else 'no'} "
        f"({report.microphone_inputs} input device(s))",
        f"Tray UI (PySide6): {'yes' if report.ui_available else 'no'}",
        "",
        "Models:",
    ]
    for item in report.models:
        lines.append(
            f"  [{'OK' if item.exists else 'MISSING':7}] {item.role:10} {item.path}"
        )
    lines.append("")
    lines.append("ASR engines:")
    for name in ("firered", "qwen3", "sherpa", "fake"):
        lines.append(
            f"  {name:10} {'available' if report.asr_engines.get(name) else 'not installed'}"
        )
    lines.append(f"Requested ASR: {report.asr_engine}")
    if report.server_count:
        lines.append(f"Model servers: {report.server_ready}/{report.server_count} ready")
    if report.notes:
        lines.append("")
        lines.extend(f"Note: {note}" for note in report.notes)
    if config is not None and report.missing_models and show_commands:
        lines.append("")
        lines.append("Download commands (verify file names upstream):")
        lines.extend(download_commands(config, report.profile))
    return "\n".join(lines)

