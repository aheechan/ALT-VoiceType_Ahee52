# Changelog

## 0.1.0 — first usable desktop build

### Dictation

- Global **Alt toggle** push-to-talk: press once to start, press again to stop.
- System-tray UI with a compact left-click panel (output language, preview,
  settings, history/setup). Chinese is the default output and acts as
  transcription without a separate mode.
- Text-free live audio-level monitor while recording.
- Clipboard-paste injection with Unicode `SendInput` fallback.
- Prompt optimized for short, label-free translation output: no “原文/译文”
  headers, lower token budget, temperature 0, stop sequences.
- **Focus guard**: remembers the foreground window at record start; copies to the
  clipboard instead of inserting into a different app.
- Preview dialog attempts to restore the original window before commit.
- **Single-instance mutex**: a second tray process exits with code 4 instead of
  installing another global hook.

### Recognition and language

- Qwen3-ASR-0.6B / 1.7B adapters, plus optional FireRedASR2 and sherpa-onnx
  SenseVoice engines.
- Context-aware Chinese correction through a local llama.cpp OpenAI-compatible
  server; strict JSON output and a Levenshtein edit-ratio guard.
- Index-Translate-2B/9B translation with daily/formal/casual styles, rolling
  context, glossary, and target-Chinese transcription mode.
- SQLite utterance history and glossary, seeded into the correction context.

### 12 GB baseline

- `12gb-balanced` (default): Qwen3-ASR-0.6B + Qwen3-1.7B Q8 + Index-Translate-9B
  Q4, about 9.1 GB of weights.
- `12gb-max`: Qwen3-ASR-1.7B in the same stack, about 11.2 GB.
- `12gb-safe`: 0.6B ASR + 1.7B + 2B translator, about 5.0 GB.
- `16gb-quality` / `24gb-quality`: 1.7B ASR + 4B corrector + 9B translator.
- `cpu-safe`: SenseVoice + rules + 2B translator.
- Automatic `nvidia-smi` VRAM detection and profile selection.

### Setup and distribution

- `altvoice setup`, `altvoice models`, `altvoice download` (Hugging Face),
  `altvoice health`, `altvoice audio --list`, `altvoice history`.
- First-run environment dialog with missing-file checks and a background
  “download missing models” button.
- PyInstaller one-folder app and per-user Inno Setup installer, including a
  working bundled Qwen3-ASR (torch/transformers) for offline use.
- `altvoice run --smoke N` startup self-check.
- Windows CI for core tests and offscreen UI smoke; manual build workflow that
  uploads the app and installer artifact.

### Known limitations

- Not yet verified on an RTX 3070 12 GB or with a real microphone in this
  development session; the current GPU is an RTX 3090 24 GB and has zero audio
  input devices.
- The installer is unsigned; double-click install/uninstall still needs a real
  interactive desktop test.
- True TSF IME integration is not implemented; this is a voice input assistant
  that pastes into the focused control.
- FireRedASR2S remains optional because upstream tests it on Ubuntu 22.04.
