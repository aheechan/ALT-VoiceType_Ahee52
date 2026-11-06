"""Model location checks and download command generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig
from .models import ModelSpec, profile_models


@dataclass
class ModelLocation:
    role: str
    key: str
    display_name: str
    path: Path
    kind: str
    repo: str
    filename: str
    exists: bool


def model_path(config: AppConfig, spec: ModelSpec) -> Path:
    base = Path(config.models_dir) / spec.key
    if spec.kind == "file" and spec.filename:
        return base / spec.filename
    return base


def _exists(path: Path, kind: str) -> bool:
    if kind == "none":
        return True
    if kind == "dir":
        return path.is_dir() and any(path.iterdir())
    return path.is_file()


def locations(config: AppConfig, profile: str) -> list[ModelLocation]:
    base = Path(config.models_dir)
    result: list[ModelLocation] = []
    for role, spec in profile_models(profile).items():
        path = base / spec.key
        if spec.kind == "file" and spec.filename:
            path = path / spec.filename
        result.append(
            ModelLocation(
                role=role,
                key=spec.key,
                display_name=spec.display_name,
                path=path,
                kind=spec.kind,
                repo=spec.repo,
                filename=spec.filename,
                exists=_exists(path, spec.kind),
            )
        )
    return result


def download_commands(config: AppConfig, profile: str) -> list[str]:
    commands: list[str] = []
    for _role, spec in profile_models(profile).items():
        if not spec.repo or spec.kind == "none":
            continue
        path = model_path(config, spec)
        if spec.kind == "dir":
            commands.append(
                f'modelscope download --model {spec.repo} --local_dir "{path}"'
            )
        else:
            commands.append(
                f'huggingface-cli download {spec.repo} --include "*{spec.filename}" '
                f'--local-dir "{path.parent}"'
            )
    return commands


def all_present(config: AppConfig, profile: str) -> bool:
    return all(item.exists for item in locations(config, profile))
