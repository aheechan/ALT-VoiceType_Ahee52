# Status

## Done

### M0 scaffold

- Local git repository initialized on `main`.
- Product plan, architecture, ADR, model catalog, UX, run guide and bake-off guide.
- 12 GB-first VRAM profiles:
  - `12gb-balanced`: Qwen3-ASR-1.7B + Qwen3-1.7B + Index-Translate-9B (~10.6 GB of weights).
  - `12gb-safe`: Qwen3-ASR-0.6B + Qwen3-1.7B + Index-Translate-2B (~4.4 GB).
  - `16gb-quality` / `24gb-quality`: Qwen3-ASR-1.7B + 4B corrector + 9B translator (~11.9 GB).
  - `cpu-safe`: SenseVoice + rules + 2B translator.
- Windows default ASR is Qwen3-ASR (ADR-0002); FireRedASR2-AED remains an optional quality engine.
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
- `llama-server` supervision (`servers.py`): auto-start with model paths, health
  checks, reuse of already-running servers, shutdown on exit, log files.
- `model_store.py` + `python -m altvoice models`: expected paths, missing-file
  checks and download commands.
- `setup_wizard.py` + `python -m altvoice setup`: first-run config with profile,
  model paths and download instructions.
- `health.py` + `python -m altvoice health`: one-shot readiness check for models,
  ASR engine, microphone and PySide6.
- Tray first-run/environment dialog: missing paths, copy download commands,
  open model folder, recheck.
- History/glossary persistence in SQLite (`history.py`), seeded into the
  controller's context; `python -m altvoice history [--clear]`.
- Tray "历史与术语…" dialog: recent utterances, glossary edit/delete,
  clear-all with confirmation.
- `python -m altvoice servers --command`.
- Packaging: PyInstaller spec, Inno Setup script, `scripts/build_windows.ps1`.
  PyInstaller 6.22.3 one-folder build succeeds (~147 MB) with PySide6 bundled.
  Inno Setup 6.7.3 compiles `dist/installer/AltVoice-Setup-0.1.0.exe` (~41 MB).
- GitHub Actions: Windows CI tests and a manual Windows build workflow.
- 86 unit tests total; 83 run without PySide6, 3 UI smoke tests run when
  PySide6 is available (`QT_QPA_PLATFORM=offscreen`).

Verified in this session:

- `python -m altvoice doctor` / `profiles`.
- Hook install + uninstall in the interactive Windows session.
- PySide6 6.12 offscreen smoke test: setup dialog, history dialog, preview
  dialog, tray menu and generated icon all construct successfully.
- Real desktop tray smoke: `TrayApp` starts, tray icon visible, global Alt hook
  running, and clean shutdown after 1.5 s (fake ASR/model stubs).
- PyInstaller 6.22.3 produces the one-folder app; Inno Setup compiles the
  installer. Launching the windowed exe/installer is still manual because the
  harness blocks GUI process startup.
- Real Qwen3-ASR-0.6B CPU smoke test on the public Chinese sample:
  transcription `甚至出现交易几乎停滞的情况。`, ~1.9 s (CPU, cached model).
  The adapter and full pipeline both work end to end.
- Local OpenAI-compatible correction/translation HTTP path tested against an
  in-process mock server (prompt, JSON parsing, diff guard, target-zh skip).
- `llama-server` installed via winget; `resolve_binary()` finds the winget
  package directory when the alias is not on PATH.
- `scripts/asr_smoke.py` reproduces the ASR check without committing weights.
- `python -m altvoice run` fails gracefully with a clear PySide6 message when the UI
  extra is missing.

## Next (needs assets / interactive desktop)

1. Install PySide6 and launch the tray on the real desktop; test Alt+Tab, Alt menu,
   and clipboard insertion in Notepad/Chrome/Word/WeChat/VS Code.
2. Install at least one ASR backend (Qwen3-ASR is easiest) and download a model.
3. Record 50–100 short Chinese utterances and create `benchmarks/asr_manifest.jsonl`.
4. Run the bake-off and pick the primary/fallback engine for the actual 3070.
5. Add installer, model downloader and first-run setup wizard.

## Open questions

- Is speech input only Chinese, or also English/Japanese source audio? The MVP
  assumes Chinese source; Qwen3-ASR can add multilingual source later.
- Which target languages after the initial six?
- Should the app ship as open source (Apache-2.0) or remain private?
