"""Translation interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TranslationError(RuntimeError):
    """Raised when the local translation model cannot be reached."""


class Translator(ABC):
    @abstractmethod
    def translate(
        self,
        text: str,
        target_lang: str,
        context: list[dict[str, str]] | None = None,
        style: str = "daily",
        glossary: dict[str, str] | None = None,
        source_lang: str = "zh",
    ) -> str:
        """Translate one utterance and return plain target text."""

    def close(self) -> None:
        return None


class NullTranslator(Translator):
    def translate(
        self,
        text: str,
        target_lang: str,
        context: list[dict[str, str]] | None = None,
        style: str = "daily",
        glossary: dict[str, str] | None = None,
        source_lang: str = "zh",
    ) -> str:
        return text

