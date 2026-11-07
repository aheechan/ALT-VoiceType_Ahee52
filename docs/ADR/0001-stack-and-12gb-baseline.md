# ADR-0001: Stack and 12 GB baseline

> **Update:** the ASR-primary part of this ADR is superseded by
> [ADR-0002](0002-windows-asr-default.md). Qwen3-ASR-1.7B is the Windows default;
> FireRedASR2-AED remains an optional quality engine.

- Status: Accepted
- Date: 2026-11-05
- Deciders: ALT-VoiceType project

## Context

The product is an offline Windows voice input assistant. The baseline GPU is an RTX 3070 with
12 GB VRAM, scaling up to 16/24 GB. It must support Chinese speech-to-text, context-aware
correction, and natural translation into multiple languages, including Chinese output.

The main constraints are:

1. Chinese ASR accuracy is the first priority; English-centric models are not acceptable defaults.
2. Everything must run locally after model installation.
3. 12 GB must be enough for the default profile; 24 GB should improve quality, not be required.
4. The app must feel like an input method: low latency, tray-resident, global hotkey.
5. Commercial licensing must be clear.

## Decision

- **Language/runtime:** Python 3.11/3.12.
- **UI:** PySide6 (LGPL). Avoid PyQt (GPL/commercial) for a distributable app.
- **ASR primary:** FireRedASR2-AED 1.1B, FP16, Apache-2.0. It has the strongest Mandarin CER tier
  and fits the 12 GB budget.
- **ASR alternates:** Qwen3-ASR-1.7B/0.6B (streaming/dialects) and sherpa-onnx + SenseVoice-Small
  (CPU fallback).
- **Corrector:** Qwen3-1.7B-Instruct Q8 for the 12 GB profile; Qwen3-4B Q4 for 16 GB+.
- **Translator:** Index-Translate-9B Q4 for 12 GB+; Index-Translate-2B Q4 for safe/CPU profiles.
- **Inference runtime:** llama.cpp OpenAI-compatible server for correction and translation;
  PyTorch (FireRed) or qwen-asr for ASR, isolated behind adapters.
- **Injection:** clipboard paste first, SendInput Unicode fallback. TSF is explicitly deferred.
- **Hotkey:** low-level keyboard hook with a long-press gesture; short taps are replayed to the app.

## Consequences

Positive:

- 12 GB profile fits: ~9.1 GB of weights + ~2 GB runtime/KV cache.
- All core models are Apache-2.0 or permissive; the code can be Apache-2.0.
- The OpenAI-compatible boundary keeps the app independent of vLLM/SGLang/llama.cpp internals.
- CPU fallback is possible with sherpa-onnx and the 2B translator.

Negative / risks:

- FireRedASR has no streaming and needs a GPU; the MVP is release-to-text, not live partial text.
- PyTorch packaging is large; a CPU-only build will use sherpa-onnx instead.
- A low-level keyboard hook can trigger antivirus heuristics and needs careful Alt/Alt+Tab testing.
- Index-Translate weights are hosted separately; their license must be verified before
  redistribution, even though the repository code is Apache-2.0.

## Rejected alternatives

- **Whisper large-v3 as primary:** Chinese CER and meeting-scene robustness are materially worse.
- **Index-Translate-Omni as ASR:** Chinese CER 13–19%, not suitable for dictation.
- **Electron/Tauri UI:** extra runtime and IPC complexity for a tray app; PySide6 is faster to ship.
- **True TSF IME in v0.1:** COM registration, composition and candidate UI would add weeks before
  the core quality is validated.
- **35B-A3B translator:** text gains over 9B are small; 70 GB VRAM breaks the 12 GB baseline.

