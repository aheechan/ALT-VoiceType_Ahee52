"""Audio helpers: WAV I/O, silence trimming and optional microphone capture."""

from __future__ import annotations

import contextlib
import math
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np


class AudioError(RuntimeError):
    """Raised when audio cannot be decoded or captured."""


def read_wav(path: str | Path) -> tuple[np.ndarray, int]:
    """Read a PCM WAV file as mono float32 in [-1, 1]."""
    path = Path(path)
    try:
        with wave.open(str(path), "rb") as handle:
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            rate = handle.getframerate()
            frames = handle.readframes(handle.getnframes())
    except (wave.Error, OSError) as exc:
        raise AudioError(f"cannot read WAV {path}: {exc}") from exc

    if width == 1:
        data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif width == 2:
        data = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    elif width == 4:
        data = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise AudioError(f"unsupported WAV sample width: {width}")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data.astype(np.float32), rate


def write_wav(path: str | Path, samples: np.ndarray, samplerate: int) -> Path:
    """Write mono float32 samples as 16-bit PCM WAV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(int(samplerate))
        handle.writeframes(pcm.tobytes())
    return path


def duration_s(samples: np.ndarray, samplerate: int) -> float:
    if samplerate <= 0:
        return 0.0
    return float(len(samples)) / float(samplerate)


def trim_silence(
    samples: np.ndarray,
    samplerate: int,
    threshold: float = 0.012,
    padding_ms: int = 120,
    frame_ms: int = 20,
) -> np.ndarray:
    """Trim leading/trailing low-energy audio, keeping a little padding.

    This is intentionally simple and dependency-free. The production path can
    swap in Silero/FSMN VAD behind the same interface.
    """
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    if samples.size == 0:
        return samples
    frame = max(1, int(samplerate * frame_ms / 1000))
    usable = (samples.size // frame) * frame
    if usable == 0:
        return samples
    frames = samples[:usable].reshape(-1, frame)
    rms = np.sqrt(np.mean(frames * frames, axis=1) + 1e-12)
    active = np.where(rms >= threshold)[0]
    if active.size == 0:
        return samples[:0]
    start = max(0, active[0] * frame - int(samplerate * padding_ms / 1000))
    end = min(samples.size, (active[-1] + 1) * frame + int(samplerate * padding_ms / 1000))
    return samples[start:end]


def normalize_peak(samples: np.ndarray, target: float = 0.95) -> np.ndarray:
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    peak = float(np.max(np.abs(samples))) if samples.size else 0.0
    if peak < 1e-7:
        return samples
    return (samples * (target / peak)).astype(np.float32)


def convert_to_wav16k(src: str | Path, dst: str | Path | None = None) -> Path:
    """Convert any ffmpeg-supported audio file to 16 kHz mono PCM WAV."""
    src = Path(src)
    if dst is None:
        dst = src.with_suffix(".16k.wav")
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise AudioError("ffmpeg is required to convert non-WAV audio")
    proc = subprocess.run(
        [ffmpeg, "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "16000", "-f", "wav", str(dst)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AudioError(f"ffmpeg failed for {src}: {proc.stderr[-400:]}")
    return dst


def ensure_wav16k(path: str | Path) -> tuple[Path, bool]:
    """Return a 16 kHz WAV path and whether it is a temporary file."""
    path = Path(path)
    if path.suffix.lower() == ".wav":
        try:
            samples, rate = read_wav(path)
            if rate == 16000:
                return path, False
        except AudioError:
            pass
    fd, name = tempfile.mkstemp(prefix="altvoice_", suffix=".16k.wav")
    os.close(fd)
    out = Path(name)
    return convert_to_wav16k(path, out), True


@contextlib.contextmanager
def temporary_wav(samples: np.ndarray, samplerate: int):
    fd, name = tempfile.mkstemp(prefix="altvoice_", suffix=".wav")
    os.close(fd)
    try:
        write_wav(name, samples, samplerate)
        yield Path(name)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(name)


class AudioRecorder:
    """Thin sounddevice wrapper; imported lazily so the core stays testable."""

    def __init__(
        self,
        samplerate: int = 16000,
        channels: int = 1,
        device: str | int | None = None,
        on_level=None,
    ) -> None:
        self.samplerate = int(samplerate)
        self.channels = int(channels)
        self.device = device
        self.on_level = on_level

    def _sd(self):
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioError("microphone capture requires: pip install 'altvoice[audio]'") from exc
        return sd

    def record(self, max_seconds: float = 30.0) -> tuple[np.ndarray, int]:
        sd = self._sd()
        frames = max(1, int(self.samplerate * max_seconds))
        try:
            data = sd.rec(
                frames,
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                device=self.device,
            )
            sd.wait()
        except Exception as exc:  # sounddevice raises PortAudioError
            raise AudioError(f"microphone capture failed: {exc}") from exc
        samples = np.asarray(data, dtype=np.float32)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        if self.channels == 1:
            samples = samples.reshape(-1)
        return samples, self.samplerate

    def record_push_to_talk(self, stop_event, max_seconds: float = 30.0) -> tuple[np.ndarray, int]:
        """Record until stop_event is set, up to max_seconds."""
        sd = self._sd()
        chunks: list[np.ndarray] = []

        def callback(indata, _frames, _time, status):  # pragma: no cover - hardware path
            if status:
                pass
            chunks.append(indata.copy())
            if self.on_level is not None:
                try:
                    mono = np.asarray(indata, dtype=np.float32)
                    if mono.ndim > 1:
                        mono = mono.mean(axis=1)
                    self.on_level(rms(mono))
                except Exception:
                    pass

        try:
            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
                device=self.device,
                callback=callback,
            ):
                while not stop_event.is_set() and sum(len(c) for c in chunks) < self.samplerate * max_seconds:
                    sd.sleep(20)
        except Exception as exc:
            raise AudioError(f"microphone capture failed: {exc}") from exc
        if not chunks:
            return np.zeros(0, dtype=np.float32), self.samplerate
        samples = np.concatenate(chunks, axis=0)
        if samples.ndim > 1:
            samples = samples.mean(axis=1)
        return samples.astype(np.float32), self.samplerate


def rms(samples: np.ndarray) -> float:
    if len(samples) == 0:
        return 0.0
    return float(math.sqrt(float(np.mean(np.square(samples))) + 1e-12))

