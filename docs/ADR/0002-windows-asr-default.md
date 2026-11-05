# ADR-0002: Windows default ASR is Qwen3-ASR

- Status: Accepted
- Date: 2026-11-05
- Supersedes part of: ADR-0001 (ASR primary)

## Context

ADR-0001 selected FireRedASR2-AED as the primary Chinese ASR because it has the best
Mandarin CER among open models (3.05% average vs 3.76% for Qwen3-ASR-1.7B in the
FireRedASR2S comparison).

AltVoice is a Windows desktop application. The FireRedASR2S README explicitly states that
its code has only been tested on Ubuntu 22.04; Windows behavior is untested. Packaging a
PyTorch research repository with custom CUDA dependencies, plus a 1.1B checkpoint, is a
larger delivery risk than the ~0.7-point CER gap.

## Decision

- **Default ASR on Windows:** Qwen3-ASR-1.7B via `qwen-asr` (Transformers backend).
  - 52 languages/dialects, 22 Chinese dialects, streaming support, Apache-2.0.
  - Windows-friendly PyTorch/Transformers stack.
  - `12gb-balanced`: Qwen3-ASR-1.7B + Qwen3-1.7B corrector + Index-Translate-9B Q4
    (~10.6 GB of weights).
- **Quality option:** FireRedASR2-AED remains a selectable engine for users with a tested
  Linux/WSL environment or a verified Windows setup.
- **Low-memory fallback:** Qwen3-ASR-0.6B in `12gb-safe`.
- **CPU fallback:** SenseVoice-Small via sherpa-onnx.

## Consequences

Positive:

- One Python/PyTorch stack for ASR and the desktop app; easier Windows packaging.
- Streaming and dialect support are available in the same engine.
- 12 GB profile has a credible memory budget.

Negative:

- Slightly higher Mandarin CER than FireRedASR2-AED on public benchmarks.
- FireRedASR2-AED adapter still needs a real Windows/Linux validation run.
- Qwen3-ASR-1.7B is larger than FireRedASR2-AED (3.6 GB vs 2.5 GB), leaving less KV headroom.

## Validation plan

Run the M0 bake-off with both engines on the same 50–100 Chinese recordings on the target
3070. If Qwen3-ASR-1.7B is within ~1 CER point of FireRed and starts reliably on Windows,
keep it as default. If FireRed is dramatically better and runs reliably, revisit this ADR.
