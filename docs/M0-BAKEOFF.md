# M0: ASR bake-off

The goal is to choose the primary and fallback ASR engines with **your own recordings**, not with
leaderboard numbers alone. The harness measures character error rate (CER), latency, and peak
memory for each engine on the same audio.

## 1. Build a local test set

Record 50–100 short utterances (2–10 s) covering:

- quiet room, laptop mic, headset;
- fast speech, hesitation, repeated words;
- names, product terms, numbers, dates;
- Chinese/English code-switching;
- at least 10 noisy samples (café, keyboard, fan).

Put WAV files under `benchmarks/audio/` (gitignored) and create a JSONL manifest:

```json
{"id":"u001","audio":"benchmarks/audio/u001.wav","reference":"我们今天下午三点开会，别迟到。","language":"zh","tags":["quiet","meeting"]}
{"id":"u002","audio":"benchmarks/audio/u002.wav","reference":"把这份合同发给王律师。","language":"zh","tags":["name"]}
```

See `benchmarks/asr_manifest.example.jsonl` for a template. References must be human-corrected
ground truth, not another model's output.

## 2. Install candidate engines

```powershell
# Qwen3-ASR (easiest)
pip install -e ".[asr-qwen]"

# sherpa-onnx CPU fallback
pip install -e ".[asr-sherpa]"

# FireRedASR2S: clone the repo and install its requirements, then set
#   $env:FIRERED_ASR_MODEL="C:\models\FireRedASR2-AED"
```

## 3. Run

```powershell
python -m altvoice bakeoff --manifest benchmarks/asr_manifest.jsonl --engine firered
python -m altvoice bakeoff --manifest benchmarks/asr_manifest.jsonl --engine qwen3
python -m altvoice bakeoff --manifest benchmarks/asr_manifest.jsonl --engine sherpa
python -m altvoice bakeoff --manifest benchmarks/asr_manifest.jsonl --engine all --out benchmarks/results
```

The report contains per-utterance text, CER, latency and errors, plus a summary JSON. Invalid or
missing references are skipped for CER but still measured for latency.

## 4. Decision rule

Pick the primary engine with:

1. CER within 1 absolute point of the best;
2. p95 latency ≤1.5 s for 5 s audio on the target GPU;
3. VRAM ≤ the profile budget;
4. acceptable license.

Fallback must run on CPU (sherpa-onnx + SenseVoice) or fit in the `12gb-safe` profile.

Expected outcome on a 3070 12 GB:

- FireRedASR2-AED: best CER, ~2.5 GB, no streaming.
- Qwen3-ASR-1.7B: slightly higher CER, streaming/dialects, ~3.6 GB.
- Qwen3-ASR-0.6B: fastest, safe fallback.
- sherpa-onnx + SenseVoice: CPU fallback, lower accuracy.

Do not delete the losing engine: keep it selectable in settings, because microphone/domain
differences can change the ranking.

