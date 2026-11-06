# Status

## Done

### M0 scaffold

- Local git repository initialized on `main`.
- Product plan, architecture, ADR, model catalog, UX, run guide and bake-off guide.
- 12 GB-first VRAM profiles:
  - `12gb-balanced`: Qwen3-ASR-0.6B + Qwen3-1.7B Q8 + Index-Translate-9B (~9.1 GB).
  - `12gb-max`: Qwen3-ASR-1.7B + Qwen3-1.7B Q8 + Index-Translate-9B (~11.2 GB).
  - `12gb-safe`: Qwen3-ASR-0.6B + Qwen3-1.7B Q8 + Index-Translate-2B (~5.0 GB).
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
  - toggle mode: press once to start, press again to stop;
  - legacy long-press mode available in config;
  - Alt+key combination cancel and modifier replay;
  - injected-event pass-through to avoid self-triggering.
- Testable hook logic (`hotkey/logic.py`).
- `VoiceAppController`: lazy ASR load, microphone recording, VAD trim, pipeline,
  direct paste by default, optional preview, cancel, audio level callbacks.
- PySide6 tray: compact panel, language picker, settings button, text-free live
  audio monitor, optional preview dialog, clipboard insertion.
- `python -m altvoice run`.
- `llama-server` supervision (`servers.py`): auto-start with model paths, health
  checks, reuse of already-running servers, shutdown on exit, log files.
- `model_store.py` + `python -m altvoice models`: expected paths, missing-file
  checks and download commands.
- `setup_wizard.py` + `python -m altvoice setup`: first-run config with profile,
  model paths and download instructions.
- `downloader.py` + `python -m altvoice download`: Hugging Face resumable model
  download for a profile (Qwen3-ASR/Qwen3/Index-Translate).
- `health.py` + `python -m altvoice health`: one-shot readiness check for models,
  ASR engine, microphone and PySide6.
- `python -m altvoice audio --list` / `--seconds` / `--out`: microphone
  diagnostics and test recording.
- Tray first-run/environment dialog: missing paths, download-missing-models
  button (background thread), copy commands, open model folder, recheck.
- Compact tray panel (left-click): fixed Chinese input, output-language picker,
  automatic transcription when output is Chinese, preview toggle, settings/
  history/setup/log/quit.
- Text-free live audio-level monitor while recording.
- Default output language is Chinese; `zh` skips translation and acts as
  transcription without a separate mode selection.
- History/glossary persistence in SQLite (`history.py`), seeded into the
  controller's context; `python -m altvoice history [--clear]`.
- Tray "历史与术语…" dialog: recent utterances, glossary edit/delete,
  clear-all with confirmation.
- `python -m altvoice servers --command`.
- Single-instance named mutex: a second `run` exits with code 4 instead of
  installing a second keyboard hook.
- Packaging: PyInstaller spec, Inno Setup script, `scripts/build_windows.ps1`.
  PyInstaller 6.22.3 one-folder build succeeds (~1.37 GB with `asr-qwen`/torch).
  Inno Setup 6.7.3 compiles `dist/installer/ALT-VoiceType-Setup-0.1.0.exe` (~341 MB).
- GitHub Actions: Windows core tests, offscreen UI smoke tests, and a manual
  build workflow that produces the PyInstaller app + Inno installer artifact.
- 95 unit tests total; 89 run without PySide6, 6 UI smoke tests run when
  PySide6 is available (`QT_QPA_PLATFORM=offscreen`).

Verified in this session:

- `python -m altvoice doctor` / `profiles`.
- Hook install + uninstall in the interactive Windows session.
- PySide6 6.12 offscreen smoke test: setup dialog, history dialog, preview
  dialog, tray menu and generated icon all construct successfully.
- Real desktop tray smoke: `TrayApp` starts, tray icon visible, global Alt hook
  running, and clean shutdown after 1.5 s (fake ASR/model stubs).
- `python -m altvoice run --smoke 2` starts the tray and exits 0 after two
  seconds in the real desktop session.
- Focus guard: the controller records the foreground window at recording start;
  if focus changed before insertion, it copies to the clipboard instead of
  injecting into the wrong application (`ui.focus_guard`). The preview dialog
  attempts to refocus that window before `commit()`.
- PyInstaller 6.22.3 produces the one-folder app; Inno Setup compiles the
  installer. Launching the windowed exe/installer is still manual because the
  harness blocks GUI process startup.
- The packaged **console debug build** actually transcribes the Chinese sample
  with bundled qwen-asr: `甚至出现交易几乎停滞的情况。`, ~1.4 s CPU. This
  required bundling transformers submodules and stubbing optional Japanese
  tokenizer imports.
- Real Qwen3-ASR-0.6B CPU smoke test on the public Chinese sample:
  transcription `甚至出现交易几乎停滞的情况。`, ~1.9 s (CPU, cached model).
  The adapter and full pipeline both work end to end.
- Real Index-Translate-2B and 9B GGUF servers tested with llama.cpp. 9B output is
  natural (`We’ve got a meeting at three this afternoon—don’t be late!`), latency
  ~0.2–0.5 s per short sentence on the 3090.
- Full real pipeline: Qwen3-ASR-0.6B → Qwen3-1.7B correction → Index-Translate-9B
  produced `There were even times when trading pretty much came to a standstill.`
- `ServerManager.start_all()` auto-started real Qwen3-1.7B and
  Index-Translate-2B llama.cpp servers, waited for `/v1/models`, and stopped them
  cleanly.
- `VoiceAppController` end-to-end with a file recorder (real ASR → real correction
  → real 9B translation → commit) produced
  `Transactions even almost came to a standstill.` and injected it through the
  test injector.
- GPU observation: 9B + 1.7B servers plus the desktop are heavy on 12 GB. Default
  `12gb-balanced` now uses Qwen3-ASR-0.6B (~9.1 GB weights); `12gb-max` keeps the
  1.7B ASR (~11.2 GB) for users who close background GPU apps.
- Local OpenAI-compatible correction/translation HTTP path tested against an
  in-process mock server (prompt, JSON parsing, diff guard, target-zh skip).
- Clipboard set/get/restore verified with real Unicode text. `altvoice health` now
  counts actual input devices; this session has 0, so the mic → ASR path still
  needs a real user machine. SendInput works at the OS level but safely directing
  it to a controlled window is still a desktop test.
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
