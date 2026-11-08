"""faster-whisper ASR adapter (English edition)."""

from __future__ import annotations

import time

from .base import ASREngine, ASRResult, EngineUnavailable


def _patch_av() -> None:
    """PyAV 19 removed metadata_errors, which faster-whisper still passes."""
    try:
        import av

        if getattr(av, "_altvoice_compat", False):
            return
        original_open = av.open

        def compatible_open(*args, **kwargs):
            kwargs.pop("metadata_errors", None)
            return original_open(*args, **kwargs)

        av.open = compatible_open
        av._altvoice_compat = True
    except Exception:
        pass


class WhisperASREngine(ASREngine):
    name = "whisper"

    def __init__(
        self,
        model_path: str | None = None,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        self.model_path = model_path
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def load(self) -> None:
        if self._model is not None:
            return
        _patch_av()
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise EngineUnavailable(
                "faster-whisper is not installed. Install with: "
                "pip install faster-whisper"
            ) from exc
        if not self.model_path:
            raise EngineUnavailable("faster-whisper model path is not configured")
        try:
            self._model = WhisperModel(
                self.model_path,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as exc:
            raise EngineUnavailable(f"failed to load faster-whisper model: {exc}") from exc

    def transcribe(self, audio_path: str, language: str = "en") -> ASRResult:
        self.load()
        assert self._model is not None
        started = time.perf_counter()
        from ..audio import ensure_wav16k, read_wav

        wav_path, temporary = ensure_wav16k(audio_path)
        try:
            samples, _rate = read_wav(wav_path)
            segments, info = self._model.transcribe(
                samples,
                language=language or "en",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = "".join(segment.text for segment in segments).strip()
        except Exception as exc:
            raise EngineUnavailable(f"faster-whisper transcription failed: {exc}") from exc
        finally:
            if temporary:
                try:
                    wav_path.unlink()
                except OSError:
                    pass
        return ASRResult(
            text=text,
            language=getattr(info, "language", None) or language,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            engine=self.name,
        )

    def close(self) -> None:
        self._model = None
