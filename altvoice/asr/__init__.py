"""ASR engine registry."""

from __future__ import annotations

import importlib.util

from .base import ASREngine, ASRResult, EngineUnavailable
from .fake import FakeASR
from .firered import FireRedASREngine
from .qwen3 import Qwen3ASREngine
from .sherpa import SherpaASREngine

__all__ = [
    "ASREngine",
    "ASRResult",
    "EngineUnavailable",
    "FakeASR",
    "FireRedASREngine",
    "Qwen3ASREngine",
    "SherpaASREngine",
    "create_engine",
    "available_engines",
]

_ALIASES = {
    "fake": "fake",
    "none": "fake",
    "firered": "firered",
    "firered_asr": "firered",
    "fireredasr": "firered",
    "qwen3": "qwen3",
    "qwen3_asr": "qwen3",
    "qwen": "qwen3",
    "sherpa": "sherpa",
    "sherpa-onnx": "sherpa",
    "sensevoice": "sherpa",
}


def available_engines() -> dict[str, bool]:
    return {
        "firered": importlib.util.find_spec("fireredasr") is not None,
        "qwen3": importlib.util.find_spec("qwen_asr") is not None,
        "sherpa": importlib.util.find_spec("sherpa_onnx") is not None,
        "fake": True,
    }


def create_engine(
    name: str = "auto",
    model_path: str | None = None,
    device: str = "cuda",
    language: str = "zh",
    beam_size: int = 3,
) -> ASREngine:
    key = _ALIASES.get((name or "auto").strip().lower(), (name or "auto").strip().lower())
    if key == "auto":
        if importlib.util.find_spec("qwen_asr") is not None:
            key = "qwen3"
        elif (
            importlib.util.find_spec("fireredasr2s") is not None
            or importlib.util.find_spec("fireredasr") is not None
        ):
            key = "firered"
        elif model_path:
            key = "firered"
        elif importlib.util.find_spec("sherpa_onnx") is not None:
            key = "sherpa"
        else:
            raise EngineUnavailable(
                "no ASR backend installed. Choose one:\n"
                "  pip install 'altvoice[asr-qwen]'      # Qwen3-ASR\n"
                "  pip install 'altvoice[asr-sherpa]'    # sherpa-onnx CPU fallback\n"
                "  clone FireRedTeam/FireRedASR2S       # FireRedASR2-AED"
            )
    if key == "fake":
        return FakeASR()
    if key == "firered":
        return FireRedASREngine(model_path=model_path, device=device, beam_size=beam_size)
    if key == "qwen3":
        return Qwen3ASREngine(model_path=model_path, device=device)
    if key == "sherpa":
        return SherpaASREngine(model_path=model_path)
    raise ValueError(f"unknown ASR engine: {name!r}; known: {', '.join(_ALIASES)}")

