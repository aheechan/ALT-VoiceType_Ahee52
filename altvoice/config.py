"""Core configuration and language metadata for ALT-VoiceType."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints

# Languages shown in the tray. The list is intentionally short for v0.1; the
# translation model itself supports more, and adding a code here is enough.
LANGUAGES: dict[str, str] = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "ru": "Русский",
    "pt": "Português",
    "it": "Italiano",
    "ar": "العربية",
    "vi": "Tiếng Việt",
    "th": "ไทย",
    "id": "Bahasa Indonesia",
    "tr": "Türkçe",
}

TARGET_LANGUAGES: list[str] = [
    "zh", "en", "ja", "ko", "es", "fr", "de", "ru", "pt", "it", "ar", "vi", "th", "id", "tr"
]

LANGUAGE_NAMES_EN: dict[str, str] = {
    "zh": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "pt": "Portuguese",
    "it": "Italian",
    "ar": "Arabic",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "tr": "Turkish",
}

LANGUAGE_ALIASES: dict[str, str] = {
    "cn": "zh",
    "zh-cn": "zh",
    "zh_cn": "zh",
    "chinese": "zh",
    "mandarin": "zh",
    "中文": "zh",
    "汉语": "zh",
    "普通话": "zh",
    "english": "en",
    "英文": "en",
    "日语": "ja",
    "日文": "ja",
    "日本語": "ja",
    "japanese": "ja",
    "韩语": "ko",
    "korean": "ko",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "russian": "ru",
    "portuguese": "pt",
    "italian": "it",
    "arabic": "ar",
    "vietnamese": "vi",
    "thai": "th",
    "indonesian": "id",
    "turkish": "tr",
}


def normalize_language(code: str | None) -> str:
    """Return a stable two-letter language code, or an empty string."""
    if not code:
        return ""
    raw = str(code).strip().lower()
    if raw in LANGUAGES:
        return raw
    return LANGUAGE_ALIASES.get(raw, raw)


def language_display(code: str) -> str:
    code = normalize_language(code)
    return LANGUAGES.get(code, code or "unknown")


def language_prompt_name(code: str) -> str:
    code = normalize_language(code)
    en = LANGUAGE_NAMES_EN.get(code, code)
    zh = LANGUAGES.get(code, code)
    if en == zh:
        return en
    return f"{en} ({zh})"


def default_config_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "ALT-VoiceType"
    return Path.home() / ".config" / "altvoice"


def default_models_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        return Path(base) / "ALT-VoiceType" / "models"
    return Path.home() / ".local" / "share" / "altvoice" / "models"


def default_config_path() -> Path:
    return default_config_dir() / "config.json"


@dataclass
class HotkeyConfig:
    mode: str = "toggle_alt"  # toggle_alt | long_press_alt
    combo: str = "lalt"  # e.g. lalt, ralt, lalt+q, alt+ctrl+space
    threshold_ms: int = 280
    key: str = "alt"
    replay_short_tap: bool = True


@dataclass
class AudioConfig:
    samplerate: int = 16000
    channels: int = 1
    device: str | None = None
    max_seconds: float = 30.0
    trim_silence: bool = True
    silence_threshold: float = 0.012
    padding_ms: int = 120


@dataclass
class ASRConfig:
    engine: str = "auto"  # auto | firered | qwen3 | sherpa | fake
    model_path: str | None = None
    device: str = "cuda"
    language: str = "zh"
    beam_size: int = 3


@dataclass
class CorrectorConfig:
    enabled: bool = True
    base_url: str = "http://127.0.0.1:8091/v1"
    model: str = "qwen3-1.7b-instruct"
    api_key: str = "EMPTY"
    timeout_s: float = 20.0
    max_edit_ratio: float = 0.25
    max_tokens: int = 512
    model_path: str | None = None
    autostart: bool = True


@dataclass
class TranslatorConfig:
    enabled: bool = True
    base_url: str = "http://127.0.0.1:8092/v1"
    model: str = "Index-Translate-9B"
    api_key: str = "EMPTY"
    timeout_s: float = 45.0
    target_language: str = "zh"
    style: str = "daily"
    max_tokens: int = 384
    model_path: str | None = None
    autostart: bool = True


@dataclass
class ServerConfig:
    enabled: bool = True
    binary: str = "llama-server"
    host: str = "127.0.0.1"
    startup_timeout_s: float = 90.0
    log_dir: str | None = None
    extra_args: list[str] = field(default_factory=list)
    context_size: int = 4096
    gpu_layers: int = 99


@dataclass
class InjectionConfig:
    method: str = "clipboard"  # clipboard | sendinput | copy
    restore_clipboard: bool = True
    paste_delay_ms: int = 80


@dataclass
class UIConfig:
    preview: bool = False
    start_minimized: bool = True
    focus_guard: bool = True


@dataclass
class HistoryConfig:
    enabled: bool = True
    path: str | None = None


def _nested_from_dict(cls: type, data: dict[str, Any]) -> Any:
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        hint = hints.get(f.name, f.type)
        if is_dataclass(hint) and isinstance(value, dict):
            kwargs[f.name] = _nested_from_dict(hint, value)  # type: ignore[arg-type]
        else:
            kwargs[f.name] = value
    return cls(**kwargs)


@dataclass
class AppConfig:
    profile: str = "auto"
    models_dir: str = field(default_factory=lambda: str(default_models_dir()))
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    corrector: CorrectorConfig = field(default_factory=CorrectorConfig)
    translator: TranslatorConfig = field(default_factory=TranslatorConfig)
    servers: ServerConfig = field(default_factory=ServerConfig)
    injection: InjectionConfig = field(default_factory=InjectionConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return _nested_from_dict(cls, data)

    def validate(self) -> None:
        self.profile = self.profile or "auto"
        self.asr.language = normalize_language(self.asr.language) or "zh"
        self.translator.target_language = (
            normalize_language(self.translator.target_language) or "zh"
        )
        if self.translator.target_language not in LANGUAGES:
            raise ValueError(
                f"unknown target language: {self.translator.target_language!r}; "
                f"known: {', '.join(TARGET_LANGUAGES)}"
            )
        if self.injection.method not in {"clipboard", "sendinput", "copy"}:
            raise ValueError("injection.method must be clipboard, sendinput, or copy")
        if self.hotkey.threshold_ms < 80:
            raise ValueError("hotkey.threshold_ms is too small (minimum 80 ms)")
        from .hotkey.combo import parse_combo

        try:
            self.hotkey.combo = parse_combo(self.hotkey.combo).text
        except ValueError as exc:
            raise ValueError(f"invalid hotkey.combo: {exc}") from exc

    def save(self, path: str | Path | None = None) -> Path:
        target = Path(path) if path else default_config_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(target)
        return target

    @classmethod
    def load(cls, path: str | Path | None = None) -> "AppConfig":
        target = Path(path) if path else default_config_path()
        if not target.exists():
            cfg = cls()
            cfg.validate()
            return cfg
        data = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"config root must be an object: {target}")
        cfg = cls.from_dict(data)
        cfg.validate()
        return cfg


def load_config(path: str | Path | None = None) -> AppConfig:
    return AppConfig.load(path)

