# Status

## Done

### M0 scaffold

- Local git repository initialized on `main`.
- Product plan, architecture, ADR, model catalog, UX, run guide and bake-off guide.
- 12 GB-first VRAM profiles:
  - `12gb-balanced`: FireRedASR2-AED + Qwen3-1.7B + Index-Translate-9B (~9.5 GB of weights).
  - `12gb-safe`: Qwen3-ASR-0.6B + Qwen3-1.7B + Index-Translate-2B (~4.4 GB).
  - `16gb-quality` / `24gb-quality`: 4B corrector + 9B translator.
  - `cpu-safe`: SenseVoice + rules + 2B translator.
- ASR adapters: FireRedASR2, Qwen3-ASR, sherpa-onnx/SenseVoice, fake.
- Context correction prompt + diff guard + glossary/context store.
- Natural translation prompt with style presets and context pairs.
- Windows clipboard / SendInput injection primitives.
- ASR bake-off harness with CER, latency, JSON/CSV reports.
- CLI: `doctor`, `profiles`, `bakeoff`, `transcribe`, `translate`.

### M1 preview

- Windows low-level Alt hook (`hotkey/windows.py`) with:
  - long-press start / release stop;
  - short-tap replay to preserve Alt menus;
  - Alt+key combination cancel and modifier replay;
  - injected-event pass-through to avoid self-triggering.
- Testable hook logic (`hotkey/logic.py`).
- `VoiceAppController`: lazy ASR load, microphone recording, VAD trim, pipeline,
  preview-or-direct insert, cancel, target language/mode.
- PySide6 tray: language menu, translate/Chinese-transcribe modes, preview toggle,
  preview dialog, clipboard insertion.
- `python -m altvoice run`.
- 51 unit tests passing without GPU, microphone or model weights.

Verified in this session:

- `python -m altvoice doctor` / `profiles`.
- Hook install + uninstall in the interactive Windows session.
- `python -m altvoice run` fails gracefully with a clear PySide6 message when the UI
  extra is missing.

## Next (needs assets / interactive desktop)

1. Install PySide6 and launch the tray on the real desktop; test Alt+Tab, Alt menu,
   and clipboard insertion in Notepad/Chrome/Word/WeChat/VS Code.
2. Install at least one ASR backend (Qwen3-ASR is easiest) and download a model.
3. Record 50–100 short Chinese utterances and create `benchmarks/asr_manifest.jsonl`.
4. Run the bake-off and pick the primary/fallback engine for the actual 3070.
5. Add installer/model downloader and model-server supervision.

## Open questions

- Is speech input only Chinese, or also English/Japanese source audio? The MVP
  assumes Chinese source; Qwen3-ASR can add multilingual source later.
- Which target languages after the initial six?
- Should the app ship as open source (Apache-2.0) or remain private?
