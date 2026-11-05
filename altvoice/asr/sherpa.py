"""sherpa-onnx adapter for SenseVoice / Paraformer CPU fallback."""

from __future__ import annotations

import os
import time
from pathlib import Path

from .base import ASREngine, ASRResult, EngineUnavailable


def _find_model_files(model_path: str | None) -> tuple[Path, Path] | None:
    if not model_path:
        model_path = os.environ.get("SHERPA_ASR_MODEL")
    if not model_path:
        return None
    root = Path(model_path)
    if root.is_file():
        model = root
        tokens = root.with_name("tokens.txt")
        return (model, tokens) if tokens.exists() else None
    candidates = [
        root / "model.int8.onnx",
        root / "model.onnx",
        root / "sensevoice.int8.onnx",
        root / "sensevoice.onnx",
    ]
    for model in candidates:
        tokens = model.with_name("tokens.txt")
        if model.exists() and tokens.exists():
            return model, tokens
    return None


class SherpaASREngine(ASREngine):
    name = "sherpa"

    def __init__(self, model_path: str | None = None, num_threads: int = 2) -> None:
        self.model_path = model_path
        self.num_threads = int(num_threads)
        self._recognizer = None

    def load(self) -> None:
        if self._recognizer is not None:
            return
        try:
            import sherpa_onnx
        except ImportError as exc:
            raise EngineUnavailable(
                "sherpa-onnx is not installed. Install with: pip install 'altvoice[asr-sherpa]'"
            ) from exc
        files = _find_model_files(self.model_path)
        if files is None:
            raise EngineUnavailable(
                "sherpa-onnx model files not found. Set SHERPA_ASR_MODEL to a directory "
                "containing model.int8.onnx and tokens.txt."
            )
        model, tokens = files
        try:
            self._recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=str(model),
                tokens=str(tokens),
                num_threads=self.num_threads,
                use_itn=True,
                debug=False,
            )
        except Exception as exc:
            raise EngineUnavailable(f"failed to load sherpa-onnx model: {exc}") from exc

    def transcribe(self, audio_path: str, language: str = "zh") -> ASRResult:
        self.load()
        assert self._recognizer is not None
        from ..audio import ensure_wav16k, read_wav

        wav_path, temporary = ensure_wav16k(audio_path)
        try:
            samples, rate = read_wav(wav_path)
            if rate != 16000:
                raise EngineUnavailable(f"sherpa-onnx expects 16 kHz audio, got {rate}")
            start = time.perf_counter()
            stream = self._recognizer.create_stream()
            stream.accept_waveform(16000, samples)
            self._recognizer.decode_stream(stream)
            text = stream.result.text
            elapsed = (time.perf_counter() - start) * 1000.0
        finally:
            if temporary:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
        return ASRResult(text=text, language=language, latency_ms=elapsed, engine=self.name)

    def close(self) -> None:
        self._recognizer = None
