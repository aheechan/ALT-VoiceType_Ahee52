"""Correction interfaces and result types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CorrectionResult:
    text: str
    raw_text: str = ""
    risk: float = 0.0
    accepted: bool = True
    reason: str = ""
    edits: list[dict[str, str]] = field(default_factory=list)

    @property
    def edited(self) -> bool:
        return self.text.strip() != self.raw_text.strip()


class Corrector(ABC):
    @abstractmethod
    def correct(
        self,
        text: str,
        context: list[dict[str, str]] | None = None,
        glossary: dict[str, str] | None = None,
        scene: str = "daily",
    ) -> CorrectionResult:
        """Return a minimally corrected version of ``text``."""

    def close(self) -> None:
        return None


class NullCorrector(Corrector):
    def correct(
        self,
        text: str,
        context: list[dict[str, str]] | None = None,
        glossary: dict[str, str] | None = None,
        scene: str = "daily",
    ) -> CorrectionResult:
        return CorrectionResult(text=text, raw_text=text, accepted=True)

