"""Qwen3-ASR adapter (qwen-asr package, transformers backend)."""

from __future__ import annotations

import os
import time
from pathlib import Path

from .base import ASREngine, ASRResult, EngineUnavailable

_QWEN_LANGUAGE_NAMES = {
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


class Qwen3ASREngine(ASREngine):
    name = "qwen3"

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cpu",
        model_name: str = "Qwen/Qwen3-ASR-1.7B",
        max_new_tokens: int = 256,
    ) -> None:
        self.model_path = model_path or os.environ.get("QWEN3_ASR_MODEL") or model_name
        # Respect the profile device: CPU tiers stay on CPU, GPU tiers use
        # CUDA when the packaged torch build supports it.
        self.device = "cuda" if str(device).startswith("cuda") else "cpu"
        self.max_new_tokens = int(max_new_tokens)
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        try:
            import torch
            from qwen_asr import Qwen3ASRModel
        except ImportError as exc:
            raise EngineUnavailable(
                "Qwen3-ASR is not importable. Install with: pip install 'altvoice[asr-qwen]'. "
                f"Details: {exc}"
            ) from exc

        if self.device.startswith("cuda") and not torch.cuda.is_available():
            # PyInstaller commonly ships CPU-only torch. Keep the app usable:
            # ASR falls back to CPU, while llama.cpp servers can still use GPU.
            self.device = "cpu"
        try:
            self._load_model(Qwen3ASRModel, torch)
        except Exception as exc:
            if self.device.startswith("cuda"):
                # Some newer GPUs/drivers fail inside the accelerator path.
                # Retry once on CPU before surfacing an error.
                self.device = "cpu"
                self._model = None
                try:
                    self._load_model(Qwen3ASRModel, torch)
                    return
                except Exception as cpu_exc:
                    raise EngineUnavailable(
                        f"failed to load Qwen3-ASR on CPU fallback: {cpu_exc}"
                    ) from cpu_exc
            raise EngineUnavailable(f"failed to load Qwen3-ASR: {exc}") from exc

    def _load_model(self, model_class, torch) -> None:
        dtype = torch.bfloat16 if self.device.startswith("cuda") else torch.float32
        device_map = "cuda:0" if self.device.startswith("cuda") else "cpu"
        self._model = model_class.from_pretrained(
            self.model_path,
            dtype=dtype,
            device_map=device_map,
            max_inference_batch_size=1,
            max_new_tokens=self.max_new_tokens,
        )

    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        self.load()
        assert self._model is not None
        lang_name = _QWEN_LANGUAGE_NAMES.get(language)
        from ..audio import ensure_wav16k, read_wav

        wav_path, temporary = ensure_wav16k(audio_path)
        start = time.perf_counter()
        try:
            samples, rate = read_wav(wav_path)
            # Pass a waveform tuple instead of a path: this avoids librosa's
            # numba-cached loaders inside a frozen PyInstaller app.
            try:
                results = self._model.transcribe(
                    audio=(samples, rate),
                    language=lang_name,
                    return_time_stamps=False,
                )
            except Exception:
                if not self.device.startswith("cuda"):
                    raise
                # A GPU that can load the checkpoint may still fail at kernel
                # launch (common with very new compute capabilities). Retry
                # the same utterance on CPU.
                self.device = "cpu"
                self._model = None
                self.load()
                assert self._model is not None
                results = self._model.transcribe(
                    audio=(samples, rate),
                    language=lang_name,
                    return_time_stamps=False,
                )
        except Exception as exc:
            raise EngineUnavailable(f"Qwen3-ASR transcription failed: {exc}") from exc
        finally:
            if temporary:
                try:
                    wav_path.unlink()
                except OSError:
                    pass
        elapsed = (time.perf_counter() - start) * 1000.0
        item = results[0] if results else None
        text = getattr(item, "text", "") if item is not None else ""
        detected = getattr(item, "language", None) if item is not None else None
        return ASRResult(
            text=text,
            language=detected or language,
            latency_ms=elapsed,
            engine=self.name,
        )

    def close(self) -> None:
        self._model = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

