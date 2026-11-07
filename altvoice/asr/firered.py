"""FireRedASR2 adapter.

Supports both the current FireRedASR2S Python API and the older FireRedASR v1
API. FireRedASR2-AED is the primary 12 GB Chinese engine: 1.1B parameters,
Apache-2.0, 60 s input limit, strong Mandarin and dialect accuracy.

Current API (FireRedASR2S)::

    from fireredasr2s.fireredasr2 import FireRedAsr2, FireRedAsr2Config
    cfg = FireRedAsr2Config(use_gpu=True, beam_size=3, ...)
    model = FireRedAsr2.from_pretrained("aed", model_dir, cfg)
    results = model.transcribe([uttid], [wav])

Older API (FireRedASR v1)::

    from fireredasr.models.fireredasr import FireRedAsr
    model = FireRedAsr.from_pretrained("aed", model_dir)
    results = model.transcribe([uttid], [wav], {...})
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


def _extract_confidence(item: object) -> float | None:
    if isinstance(item, dict):
        value = item.get("confidence")
        if isinstance(value, (int, float)):
            return float(value)
    return None


class FireRedASREngine(ASREngine):
    name = "firered"

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cuda",
        beam_size: int = 3,
        use_half: bool = False,
    ) -> None:
        self.model_path = model_path or os.environ.get("FIRERED_ASR_MODEL")
        self.device = device
        self.beam_size = int(beam_size)
        self.use_half = bool(use_half)
        self._model = None
        self._api = ""

    def _load_v2(self) -> bool:
        module_name = os.environ.get("ALTVOICE_FIRERED_MODULE", "fireredasr2s.fireredasr2")
        class_name = os.environ.get("ALTVOICE_FIRERED_CLASS", "FireRedAsr2")
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        config_cls = getattr(module, "FireRedAsr2Config", None)
        assert config_cls is not None
        config = config_cls(
            use_gpu=self.device.startswith("cuda"),
            use_half=self.use_half,
            beam_size=self.beam_size,
            nbest=1,
            decode_max_len=0,
            softmax_smoothing=1.25,
            aed_length_penalty=0.6,
            eos_penalty=1.0,
            return_timestamp=False,
        )
        self._model = cls.from_pretrained("aed", self.model_path, config)
        self._api = "v2"
        return True

    def _load_v1(self) -> bool:
        from fireredasr.models.fireredasr import FireRedAsr  # type: ignore[import-not-found]

        self._model = FireRedAsr.from_pretrained("aed", self.model_path)
        self._api = "v1"
        return True

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

        errors: list[str] = []
        for loader in (self._load_v2, self._load_v1):
            try:
                if loader():
                    return
            except Exception as exc:
                errors.append(f"{loader.__name__}: {exc}")
        raise EngineUnavailable(
            "FireRedASR is not importable or failed to load. Clone FireRedTeam/FireRedASR2S, "
            "install its requirements, and set PYTHONPATH to the repository root "
            "(or set ALTVOICE_FIRERED_MODULE/ALTVOICE_FIRERED_CLASS).\n"
            + "\n".join(errors)
        )

    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        self.load()
        assert self._model is not None
        uttid = f"altvoice-{uuid.uuid4().hex[:8]}"
        start = time.perf_counter()
        try:
            if self._api == "v2":
                results = self._model.transcribe([uttid], [str(audio_path)])
            else:
                results = self._model.transcribe(
                    [uttid],
                    [str(audio_path)],
                    {
                        "use_gpu": 1 if self.device.startswith("cuda") else 0,
                        "beam_size": self.beam_size,
                        "nbest": 1,
                        "decode_max_len": 0,
                        "softmax_smoothing": 1.25,
                        "aed_length_penalty": 0.6,
                        "eos_penalty": 1.0,
                    },
                )
        except Exception as exc:
            raise EngineUnavailable(f"FireRedASR transcription failed: {exc}") from exc
        elapsed = (time.perf_counter() - start) * 1000.0
        item = results[0] if isinstance(results, (list, tuple)) and results else results
        raw = item if isinstance(item, dict) else {"result": item}
        return ASRResult(
            text=_extract_text(item),
            language=language,
            confidence=_extract_confidence(item),
            latency_ms=elapsed,
            engine=self.name,
            raw=raw if isinstance(raw, dict) else {},
        )

    def close(self) -> None:
        self._model = None
        self._api = ""
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

