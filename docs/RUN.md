# Running ALT-VoiceType (M1 preview)

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
pip install -e ".[asr-qwen,download]"     # ASR + model downloader
# or follow docs/MODELS.md for FireRedASR2S

python -m altvoice models --profile 12gb-balanced --commands
```

`models` prints the expected local paths and download commands. It does not download
anything by itself; verify file names on the upstream repository.

## 2. Start the local correction/translation servers

ALT-VoiceType can start `llama-server` itself. In `config.json`, set:

```json
"corrector": {"model_path": "C:/.../Qwen3-1.7B-Instruct-Q4_K_M.gguf", "autostart": true},
"translator": {"model_path": "C:/.../Index-Translate-9B-Q4_K_M.gguf", "autostart": true},
"servers": {"binary": "llama-server", "context_size": 4096, "gpu_layers": 99}
```

The tray starts both servers in the background, waits for `/v1/models`, and stops them
on exit. If a server is already running on the port, it is reused and not killed.
`python -m altvoice servers --command` prints the exact commands.

Manual fallback:

```powershell
# Correction model, port 8091
llama-server -m Qwen3-1.7B-Instruct-Q4_K_M.gguf --port 8091 --host 127.0.0.1

# Translation model, port 8092
llama-server -m Index-Translate-9B-Q4_K_M.gguf --port 8092 --host 127.0.0.1
```

If you only want Chinese dictation, leave the translator server off and set
`translator.enabled=false` or use transcribe mode in the tray.

## 3. Configure ASR

Create the config with the expected model paths:

```powershell
python -m altvoice setup --profile 12gb-balanced
pip install -e ".[download]"
python -m altvoice download --profile 12gb-balanced
```

Then edit `%APPDATA%\ALT-VoiceType\config.json` if needed:

- `asr.engine`: `qwen3` (Windows default) or `firered` (optional quality engine)
- `asr.model_path`: local model directory. Leave empty for Qwen3-ASR's default checkpoint;
  set a path for FireRedASR2-AED or a downloaded Qwen3-ASR directory.
- `asr.device`: `cuda`

Run `python -m altvoice health` for a one-shot readiness check. `python -m altvoice doctor`
shows more environment detail.

## 4. Start the tray

```powershell
python -m altvoice run
# start the tray, wait 3 seconds, then exit (startup smoke test)
python -m altvoice run --smoke 3
```

Behavior:

- Press Alt once to start; a small text-free audio level monitor appears.
- Press Alt again to stop: ASR → correction → translation → direct paste at the caret.
- The panel's “显示确认弹窗（关闭则直接粘贴）” toggle enables an optional preview dialog.
- Chinese is the default output and means transcription; no separate mode.
- Short Alt taps are no longer replayed in toggle mode.
- Only one ALT-VoiceType instance runs per session; a second launch exits with code 4.
- Focus guard: if the active window changes while recording, ALT-VoiceType copies the
  result to the clipboard instead of inserting into the wrong app.
- Left-click opens the compact panel; use the Settings button there or right-click
  the tray icon for language/preview settings.

## Current limitations

- The tray and dialogs pass offscreen UI tests; a full interactive Alt-to-insert test
  still needs a real desktop with a microphone.
- This development session has no microphone input device (`altvoice audio --list`
  shows none), so the microphone path is untested.
- PyInstaller/Inno Setup builds exist, but this harness cannot launch the windowed
  installer for an install/uninstall test.
- The first recording can take several seconds while the ASR model loads; the tray
  warms up the ASR pipeline in the background at startup.
- Use `python -m altvoice download --profile ...` for models, or configure
  `servers.autostart` after downloading manually.
- Do not expose the local LLM servers on `0.0.0.0`; they have no authentication.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Tray UI unavailable` | `pip install -e ".[ui]"` |
| `SetWindowsHookExW failed` | Run the app in the interactive desktop session, not a service |
| `no input device(s)` | `python -m altvoice audio --list`; check Windows microphone privacy settings |
| `microphone capture failed` | Check Windows microphone permission and `audio.device` |
| `ASR unavailable` | Install a backend and set `asr.model_path` |
| Alt menu flashes | Increase `hotkey.threshold_ms`; report the app for testing |
| Nothing inserted | Try `injection.method: "sendinput"` or use preview/copy |
