"""FireRedASR2 adapter.

FireRedASR2S ships an AED 1.1B model with strong Mandarin accuracy and a
60-second input limit. The import path follows the upstream Python example:

    from fireredasr.models.fireredasr import FireRedAsr
    model = FireRedAsr.from_pretrained("aed", model_dir)
    model.transcribe([uttid], [wav], {"use_gpu": 1, ...})

If your FireRedASR2S checkout exposes a different module path, set
``ALTVOICE_FIRERED_MODULE`` / ``ALTVOICE_FIRERED_CLASS`` or use the CLI wrapper
until the adapter is updated.
"""

from __future__ import annotations

import importlib
import os
import time
import uuid
from pathlib import Path

from .base import ASREngine, ASRResult, EngineUnavailable


def _extract_text(item: object) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "rec_text", "transcription", "result"):
            value = item.get(key)
            if isinstance(value, str):
                return value
    for attr in ("text", "rec_text", "transcription"):
        value = getattr(item, attr, None)
        if isinstance(value, str):
            return value
    return ""


class FireRedASREngine(ASREngine):
    name = "firered"

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cuda",
        beam_size: int = 3,
    ) -> None:
        self.model_path = model_path or os.environ.get("FIRERED_ASR_MODEL")
        self.device = device
        self.beam_size = int(beam_size)
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        if not self.model_path:
            raise EngineUnavailable(
                "FireRedASR model path is not set. Download FireRedASR2-AED and set "
                "FIRERED_ASR_MODEL or asr.model_path."
            )
        if not Path(self.model_path).exists():
            raise EngineUnavailable(f"FireRedASR model path does not exist: {self.model_path}")

        module_name = os.environ.get("ALTVOICE_FIRERED_MODULE", "fireredasr.models.fireredasr")
        class_name = os.environ.get("ALTVOICE_FIRERED_CLASS", "FireRedAsr")
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            raise EngineUnavailable(
                "FireRedASR is not importable. Clone FireRedTeam/FireRedASR2S, install its "
                "requirements, and make its package importable (or set ALTVOICE_FIRERED_MODULE)."
            ) from exc

        try:
            self._model = cls.from_pretrained("aed", self.model_path)
        except Exception as exc:  # model loading can fail for many reasons
            raise EngineUnavailable(f"failed to load FireRedASR: {exc}") from exc

    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        self.load()
        assert self._model is not None
        uttid = f"altvoice-{uuid.uuid4().hex[:8]}"
        opts = {
            "use_gpu": 1 if self.device.startswith("cuda") else 0,
            "beam_size": self.beam_size,
            "nbest": 1,
            "decode_max_len": 0,
            "softmax_smoothing": 1.25,
            "aed_length_penalty": 0.6,
            "eos_penalty": 1.0,
        }
        start = time.perf_counter()
        try:
            results = self._model.transcribe([uttid], [str(audio_path)], opts)
        except Exception as exc:
            raise EngineUnavailable(f"FireRedASR transcription failed: {exc}") from exc
        elapsed = (time.perf_counter() - start) * 1000.0
        item = results[0] if isinstance(results, (list, tuple)) and results else results
        text = _extract_text(item)
        raw = item if isinstance(item, dict) else {"result": item}
        return ASRResult(
            text=text,
            language=language,
            latency_ms=elapsed,
            engine=self.name,
            raw=raw if isinstance(raw, dict) else {},
        )

    def close(self) -> None:
        self._model = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
