"""Hugging Face model download helper for first-run setup."""

from __future__ import annotations

from typing import Callable

from .config import AppConfig
from .model_store import locations
from .models import profile_models


def download_profile(
    config: AppConfig,
    profile: str,
    progress: Callable[[str], None] | None = None,
) -> list[str]:
    """Download missing Hugging Face artifacts; returns a list of errors.

    ModelScope-only packages (SenseVoice) are reported but not downloaded here.
    Downloads are resumable through huggingface_hub's cache.
    """
    say = progress or (lambda _msg: None)
    missing = [item for item in locations(config, profile) if not item.exists]
    if not missing:
        say("All model files are already present.")
        return []

    try:
        from huggingface_hub import hf_hub_download, snapshot_download
    except ImportError:
        return ["huggingface_hub is not installed; pip install 'altvoice[download]'"]

    errors: list[str] = []
    specs = profile_models(profile)
    for item in missing:
        spec = specs[item.role]
        if spec.kind == "none":
            continue
        if not spec.repo:
            continue
        if spec.key == "sensevoice_small":
            errors.append(
                "SenseVoice-Small is ModelScope-only; use the sherpa-onnx bundle from "
                "docs/MODELS.md."
            )
            continue
        say(f"downloading {spec.display_name} -> {item.path}")
        try:
            if spec.kind == "dir":
                snapshot_download(
                    repo_id=spec.repo,
                    local_dir=str(item.path),
                )
            else:
                hf_hub_download(
                    repo_id=spec.repo,
                    filename=spec.filename,
                    local_dir=str(item.path.parent),
                )
        except Exception as exc:
            errors.append(f"{spec.display_name}: {exc}")
    return errors

