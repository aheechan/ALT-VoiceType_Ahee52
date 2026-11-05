"""Fake ASR engine for tests, dry runs and pipeline development."""

from __future__ import annotations

import os

from .base import ASREngine, ASRResult


class FakeASR(ASREngine):
    name = "fake"

    def __init__(self, text: str | None = None) -> None:
        self._text = text

    def load(self) -> None:
        return None

    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        text = self._text
        if text is None:
            text = os.environ.get("ALTVOICE_FAKE_ASR_TEXT", "这是一条测试语音。")
        return ASRResult(text=text, language=language, confidence=1.0, engine=self.name)
