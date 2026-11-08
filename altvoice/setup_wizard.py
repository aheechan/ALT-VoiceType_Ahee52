"""First-run configuration builder.

This is deliberately non-interactive: the installer or the user runs
``python -m altvoice setup --profile 12gb-balanced`` and gets a valid config with
the expected local model paths. Download commands are printed for the missing
files; weights are never bundled with the app.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import AppConfig, default_config_path, normalize_language
from .model_store import download_commands, locations, model_path
from .models import PROFILES, profile_models

_ASR_ENGINE = {
    "qwen3_asr_1_7b": "qwen3",
    "qwen3_asr_0_6b": "qwen3",
    "firered_asr_aed": "firered",
    "sensevoice_small": "sherpa",
    "faster_whisper_small_en": "faster_whisper",
}


def build_config(
    profile: str = "12gb-balanced",
    models_dir: str | Path | None = None,
    target_language: str = "zh",
) -> AppConfig:
    cfg = AppConfig()
    cfg.profile = profile
    if models_dir:
        cfg.models_dir = str(models_dir)
    models = profile_models(profile)
    profile_info = PROFILES[profile]
    cfg.audio.max_seconds = float(profile_info.get("duration_s", "30"))
    cfg.servers.gpu_layers = 0 if profile == "12gb-safe" else 99
    cfg.asr.device = "cpu" if profile == "12gb-safe" else "cuda"

    asr_spec = models["asr"]
    cfg.asr.engine = _ASR_ENGINE.get(asr_spec.key, "auto")
    if asr_spec.kind == "dir":
        cfg.asr.model_path = str(model_path(cfg, asr_spec))

    corrector_spec = models["corrector"]
    if corrector_spec.kind == "none":
        cfg.corrector.enabled = False
        cfg.corrector.autostart = False
        cfg.corrector.model_path = None
    else:
        cfg.corrector.enabled = True
        cfg.corrector.autostart = True
        cfg.corrector.model_path = str(model_path(cfg, corrector_spec))

    translator_spec = models["translator"]
    cfg.translator.model_path = str(model_path(cfg, translator_spec))
    if translator_spec.key == "qwen3_4b_abliterated_q4":
        cfg.translator.model = "qwen3-4b-abliterated"
    cfg.translator.autostart = True
    cfg.translator.target_language = normalize_language(target_language) or "zh"
    cfg.validate()
    return cfg


def run_setup(
    profile: str = "12gb-balanced",
    models_dir: str | Path | None = None,
    target_language: str = "en",
    config_path: str | Path | None = None,
    force: bool = False,
    print_only: bool = False,
    show_commands: bool = True,
    out=None,
) -> int:
    import sys

    out = out or sys.stdout
    path = Path(config_path) if config_path else default_config_path()
    if path.exists() and not force and not print_only:
        print(f"Config already exists: {path}\nUse --force to overwrite.", file=out)
        return 2
    cfg = build_config(profile, models_dir, target_language)
    if print_only:
        print(json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2), file=out)
        return 0
    cfg.save(path)
    print(f"Wrote config: {path}", file=out)
    print(f"Profile:      {profile}", file=out)
    for item in locations(cfg, profile):
        mark = "OK" if item.exists else "MISSING"
        print(f"  [{mark:7}] {item.role:10} {item.path}", file=out)
    if show_commands:
        missing = [item for item in locations(cfg, profile) if not item.exists]
        if missing:
            print("\nDownload commands (verify file names upstream):", file=out)
            for command in download_commands(cfg, profile):
                print(command, file=out)
    return 0

