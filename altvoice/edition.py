"""Build-time product editions (Chinese and English)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Edition:
    code: str
    app_name: str
    data_dir_name: str
    input_language: str
    default_target: str
    asr_engine: str
    asr_model_dir: str
    english_ui: bool = False


ZH = Edition(
    code="zh",
    app_name="ALT-VoiceType",
    data_dir_name="ALT-VoiceType",
    input_language="zh",
    default_target="zh",
    asr_engine="qwen3",
    asr_model_dir="qwen3_asr_0_6b",
)
EN = Edition(
    code="en",
    app_name="ALT-VoiceType English",
    data_dir_name="ALT-VoiceType-EN",
    input_language="en",
    default_target="en",
    asr_engine="faster_whisper",
    asr_model_dir="faster_whisper_small_en",
    english_ui=True,
)


def current_edition() -> Edition:
    env = os.environ.get("ALT_VOICE_EDITION", "").strip().lower()
    if env in ("en", "english", "en-us"):
        return EN
    if env in ("zh", "chinese", "zh-cn"):
        return ZH
    executable = os.path.basename(sys.executable).lower()
    if "english" in executable or "voice-type-en" in executable or executable.startswith("alt-voicetype-en"):
        return EN
    return ZH


def is_english() -> bool:
    return current_edition().english_ui
