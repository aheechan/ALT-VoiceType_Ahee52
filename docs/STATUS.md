# Status

## Done (M0 scaffold)

- Local git repository initialized on `main`.
- Product plan, architecture, ADR, model catalog, UX and bake-off guide.
- 12 GB-first VRAM profiles:
  - `12gb-balanced`: FireRedASR2-AED + Qwen3-1.7B + Index-Translate-9B (~9.5 GB of weights).
  - `12gb-safe`: Qwen3-ASR-0.6B + Qwen3-1.7B + Index-Translate-2B (~4.4 GB).
  - `16gb-quality` / `24gb-quality`: 4B corrector + 9B translator.
  - `cpu-safe`: SenseVoice + rules + 2B translator.
- ASR adapters: FireRedASR2, Qwen3-ASR, sherpa-onnx/SenseVoice, fake.
- Context correction prompt + diff guard + glossary/context store.
- Natural translation prompt with style presets and context pairs.
- Windows clipboard / SendInput injection primitives.
- Alt gesture state machine (long-press, short-tap replay, combo cancel).
- ASR bake-off harness with CER, latency, JSON/CSV reports.
- CLI: `doctor`, `profiles`, `bakeoff`, `transcribe`, `translate`.
- 42 unit tests passing without GPU or model weights.

## Next (needs assets)

1. Install at least one ASR backend (Qwen3-ASR is the easiest) and download a model.
2. Record 50–100 short Chinese utterances and create `benchmarks/asr_manifest.jsonl`.
3. Run the bake-off and pick the primary/fallback engine for the actual 3070.
4. M1: Windows low-level Alt hook, tray UI, microphone capture, preview overlay,
   end-to-end insertion.

## Open questions

- Is speech input only Chinese, or also English/Japanese source audio? The MVP
  assumes Chinese source; Qwen3-ASR can add multilingual source later.
- Which target languages after the initial six?
- Should the app ship as open source (Apache-2.0) or remain private?
