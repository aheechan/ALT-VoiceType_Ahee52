"""ASR engine interfaces and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class EngineUnavailable(RuntimeError):
    """Raised when an optional ASR backend cannot be loaded."""


@dataclass
class ASRResult:
    text: str
    language: str | None = None
    confidence: float | None = None
    latency_ms: float | None = None
    engine: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.text = (self.text or "").strip()


class ASREngine(ABC):
    name: str = "base"

    @abstractmethod
    def load(self) -> None:
        """Load model weights. Must be idempotent."""

    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        """Transcribe a 16 kHz mono WAV file."""

    def close(self) -> None:
        """Release model resources. Safe to call multiple times."""

    def __enter__(self) -> "ASREngine":
        self.load()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

