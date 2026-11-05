import unittest
from pathlib import Path

import numpy as np

from altvoice.audio import duration_s, read_wav, rms, trim_silence, write_wav
from tests.helpers import workspace_tempdir


def tone(seconds=0.5, rate=16000, freq=440.0, amp=0.3):
    t = np.arange(int(seconds * rate), dtype=np.float32) / rate
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


class AudioTests(unittest.TestCase):
    def test_wav_roundtrip(self):
        samples = tone()
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "test.wav"
            write_wav(path, samples, 16000)
            loaded, rate = read_wav(path)
            self.assertEqual(rate, 16000)
            self.assertEqual(len(loaded), len(samples))
            self.assertLess(float(np.max(np.abs(loaded - samples))), 1e-3)

    def test_trim_silence(self):
        silence = np.zeros(8000, dtype=np.float32)
        samples = np.concatenate([silence, tone(0.4), silence])
        trimmed = trim_silence(samples, 16000, threshold=0.01, padding_ms=50)
        self.assertGreater(len(trimmed), int(0.4 * 16000))
        self.assertLess(len(trimmed), len(samples))

    def test_trim_all_silence(self):
        trimmed = trim_silence(np.zeros(16000, dtype=np.float32), 16000)
        self.assertEqual(len(trimmed), 0)

    def test_duration_and_rms(self):
        samples = tone()
        self.assertAlmostEqual(duration_s(samples, 16000), 0.5, places=3)
        self.assertGreater(rms(samples), 0.1)

    def test_stereo_downmix(self):
        left = tone()
        right = np.zeros_like(left)
        stereo = np.stack([left, right], axis=1)
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "stereo.wav"
            import wave

            pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
            with wave.open(str(path), "wb") as handle:
                handle.setnchannels(2)
                handle.setsampwidth(2)
                handle.setframerate(16000)
                handle.writeframes(pcm.tobytes())
            loaded, rate = read_wav(path)
            self.assertEqual(rate, 16000)
            self.assertAlmostEqual(float(np.max(np.abs(loaded))), 0.15, places=2)


if __name__ == "__main__":
    unittest.main()
