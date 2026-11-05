# AltVoice

**Offline Windows voice input with context-aware Chinese ASR and natural multilingual translation.**

AltVoice is a system-tray voice input assistant: hold `Alt`, speak, release, and the corrected
text (or its translation) is inserted into the focused application. Everything runs locally.

> **Status: M1 preview.** The repository contains the architecture, model profiles,
> ASR adapters, correction/translation prompt layer, Windows text-injection primitives,
> the global Alt hook, controller, tray/preview UI and the ASR bake-off harness.
> PySide6, a microphone and model weights are required to run the interactive app;
> see [docs/RUN.md](docs/RUN.md).

## Target hardware

| Profile | VRAM | ASR | Corrector | Translator |
|---|---:|---|---|---|
| `12gb-balanced` **(default baseline)** | 12 GB | Qwen3-ASR-0.6B | Qwen3-1.7B-Instruct Q8 | Index-Translate-9B Q4 |
| `12gb-max` | 12 GB | Qwen3-ASR-1.7B BF16 | Qwen3-1.7B Q8 | Index-Translate-9B Q4 |
| `12gb-safe` | 12 GB | Qwen3-ASR-0.6B | Qwen3-1.7B Q8 | Index-Translate-2B Q4 |
| `16gb-quality` | 16 GB | Qwen3-ASR-1.7B BF16 | Qwen3-4B-Instruct Q4 | Index-Translate-9B Q4 |
| `24gb-quality` | 24 GB | Qwen3-ASR-1.7B BF16 | Qwen3-4B-Instruct Q4 | Index-Translate-9B Q4 |
| `cpu-safe` | CPU | SenseVoice-Small (sherpa-onnx) | rules only | Index-Translate-2B Q4 (~2.1 GB total) |

`12gb-balanced` is tuned for an RTX 3070 12 GB (~9.1 GB of weights); `12gb-max` uses the
1.7B ASR and is tight (~11.2 GB), best with background GPU apps closed. Qwen3-ASR is the
Windows default because FireRedASR2S is only tested on Ubuntu 22.04 upstream; FireRedASR2-AED
remains an optional quality engine if you can run it.

## Quick start (development)

```powershell
# Python 3.11 or 3.12
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

python -m altvoice doctor
python -m altvoice profiles
python -m altvoice setup --profile 12gb-balanced
python -m altvoice models --profile 12gb-balanced --commands
python -m altvoice download --profile 12gb-balanced
python -m altvoice health
python -m altvoice audio --list
python -m altvoice history --limit 5

# ASR bake-off: compare engines on your own recordings
python -m altvoice bakeoff --manifest benchmarks/asr_manifest.example.jsonl --dry-run

# Unit tests do not need a GPU or model weights
python -m unittest discover -s tests -v

# Interactive tray (needs the ui/audio extras and an ASR model)
python -m altvoice run
```

Optional runtime dependencies are intentionally split so the core can be tested on a clean machine:

```powershell
pip install -e ".[audio]"       # microphone capture
pip install -e ".[asr-qwen]"    # Qwen3-ASR via qwen-asr
pip install -e ".[asr-sherpa]"  # CPU fallback via sherpa-onnx
pip install -e ".[download]"   # huggingface_hub + hf_xet model downloader
pip install -e ".[llm]"         # local OpenAI-compatible clients
pip install -e ".[ui]"          # PySide6 tray (M1)
```

## Design principles

1. **Local first.** No cloud calls at runtime; audio is deleted after transcription.
2. **ASR alone is not enough.** A context-aware corrector fixes homophones, names, punctuation
   and disfluencies without rewriting the speaker's meaning.
3. **Natural translation is a product problem.** Whole-utterance translation, rolling context,
   style presets and human evaluation, not just a bigger model.
4. **12 GB is the baseline.** Every model choice has a measured VRAM budget and a fallback.
5. **The MVP is a voice input assistant, not a TSF IME.** True IME integration (composition,
   candidate window, language bar) is a later phase.

## Repository layout

```text
altvoice/
├─ altvoice/                 # Python package
│  ├─ asr/                   # FireRedASR / Qwen3-ASR / sherpa-onnx adapters
│  ├─ correct/               # context correction prompt + diff guard
│  ├─ translate/             # Index-Translate prompt + client
│  ├─ inject/                # Windows clipboard / SendInput
│  ├─ hotkey/                # Alt gesture state machine (M1 hook)
│  ├─ llm/                   # OpenAI-compatible local client
│  ├─ audio.py               # WAV I/O, silence trimming, capture
│  ├─ config.py              # JSON config + languages
│  ├─ models.py              # model catalog + VRAM profiles
│  ├─ pipeline.py            # ASR -> correct -> translate -> inject
│  ├─ bakeoff.py             # M0 CER/latency harness
│  └─ cli.py                 # `python -m altvoice`
├─ benchmarks/               # manifest example + local audio (gitignored)
├─ docs/                     # PLAN / ARCHITECTURE / ADR / MODELS / UX
├─ tests/                    # stdlib unittest, no GPU required
└─ pyproject.toml
```

## Documentation

- [Status and next steps](docs/STATUS.md)
- [Development plan](docs/PLAN.md)
- [Architecture](docs/ARCHITECTURE.md)
- [ADR-0001: stack and 12 GB baseline](docs/ADR/0001-stack-and-12gb-baseline.md)
- [ADR-0002: Windows default ASR](docs/ADR/0002-windows-asr-default.md)
- [Models and licenses](docs/MODELS.md)
- [Interaction design](docs/UX.md)
- [M0 ASR bake-off](docs/M0-BAKEOFF.md)
- [Running the M1 tray preview](docs/RUN.md)
- [Packaging and Windows installer](packaging/README.md)

## Licenses

AltVoice code is Apache-2.0. Model weights are **not** included; each model keeps its own license.
See [docs/MODELS.md](docs/MODELS.md) before redistribution or commercial use.
