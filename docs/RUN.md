# Running AltVoice (M1 preview)

The M1 code path is now in the repository: global Alt hook, controller, system tray,
preview dialog and clipboard insertion. It is a **preview**, not a release build.

## 1. Install the desktop extras

```powershell
cd altvoice
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[ui,audio]"
```

`ui` installs PySide6; `audio` installs sounddevice. A GPU ASR backend is separate:

```powershell
pip install -e ".[asr-qwen]"     # easiest
# or follow docs/MODELS.md for FireRedASR2S
```

## 2. Start the local correction/translation servers

AltVoice expects OpenAI-compatible endpoints. Example with llama.cpp:

```powershell
# Correction model, port 8091
llama-server -m Qwen3-1.7B-Instruct-Q4_K_M.gguf --port 8091 --host 127.0.0.1

# Translation model, port 8092
llama-server -m Index-Translate-9B-Q4_K_M.gguf --port 8092 --host 127.0.0.1
```

If you only want Chinese dictation, leave the translator server off and set
`translator.enabled=false` or use transcribe mode in the tray.

## 3. Configure ASR

Copy `config.example.json` to `%APPDATA%\AltVoice\config.json` and set:

- `asr.engine`: `firered` or `qwen3`
- `asr.model_path`: local model directory (FireRed) or leave empty for the
  `qwen-asr` default checkpoint
- `asr.device`: `cuda`

Run `python -m altvoice doctor` to see what is detected.

## 4. Start the tray

```powershell
python -m altvoice run
```

Behavior:

- Long-press left Alt for ~280 ms; the tray tooltip changes to “录音中”.
- Release: ASR → correction → translation → preview dialog.
- Enter inserts, Shift+Enter adds a newline, Esc cancels.
- Short Alt taps are replayed to the active application.
- Left-click the tray icon toggles recording; right-click selects target language,
  mode (translate / Chinese transcribe), and preview.

## Current limitations

- PySide6 is not installed in the development sandbox used for M0, so the tray itself
  has not been launched here. The hook was installed/uninstalled successfully, and the
  controller/gesture logic is covered by unit tests.
- Microphone capture and text injection need a real interactive Windows session.
- No installer/model downloader yet; models are started manually.
- The first recording can take several seconds while the ASR model loads.
- Do not expose the local LLM servers on `0.0.0.0`; they have no authentication.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Tray UI unavailable` | `pip install -e ".[ui]"` |
| `SetWindowsHookExW failed` | Run the app in the interactive desktop session, not a service |
| `microphone capture failed` | Check Windows microphone permission and `audio.device` |
| `ASR unavailable` | Install a backend and set `asr.model_path` |
| Alt menu flashes | Increase `hotkey.threshold_ms`; report the app for testing |
| Nothing inserted | Try `injection.method: "sendinput"` or use preview/copy |
