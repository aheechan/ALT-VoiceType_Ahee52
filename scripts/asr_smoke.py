"""Real-ASR smoke test for a downloaded Qwen3-ASR checkpoint.

Example (from the repository root, with qwen-asr installed):

    python scripts/asr_smoke.py --model Qwen/Qwen3-ASR-0.6B --device cpu

The script downloads a short public Chinese sample if no --audio is given.
Model weights are cached by huggingface_hub, not stored in git.
"""

from __future__ import annotations

import argparse
from pathlib import Path

SAMPLE_URL = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-ASR-Repo/asr_zh.wav"


def ensure_sample(path: Path) -> Path:
    if path.exists():
        return path
    import requests

    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(SAMPLE_URL, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-ASR-0.6B")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--audio", default="benchmarks/audio/asr_zh.wav")
    args = parser.parse_args()

    from altvoice.asr.qwen3 import Qwen3ASREngine

    audio = ensure_sample(Path(args.audio))
    engine = Qwen3ASREngine(model_path=args.model, device=args.device)
    result = engine.transcribe(str(audio), language="zh")
    print(f"audio:   {audio}")
    print(f"model:   {args.model}")
    print(f"device:  {args.device}")
    print(f"text:    {result.text}")
    print(f"lang:    {result.language}")
    print(f"latency: {result.latency_ms:.0f} ms")
    engine.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
