# Packaging

ALT-VoiceType is a Windows desktop app. The installer uses a PyInstaller one-folder build plus
Inno Setup. **Model weights are not bundled**; they stay in
`%LOCALAPPDATA%\ALT-VoiceType\models` and are managed by `python -m altvoice setup` /
`python -m altvoice models`.

## Prerequisites

- Windows 10/11 x64
- Python 3.11/3.12
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`ISCC.exe` on PATH) for the installer
- PySide6 and sounddevice for the interactive app

## Build

From the repository root:

```powershell
.\scripts\build_windows.ps1
```

Or manually:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
pip install -e ".[ui,audio,asr-qwen,download]" "pyinstaller>=6.6"
pyinstaller --clean --noconfirm packaging\altvoice.spec
ISCC packaging\installer.iss
```

Outputs:

- `dist\ALT-VoiceType\ALT-VoiceType.exe` — one-folder app
- `dist\installer\ALT-VoiceType-Setup-0.1.0.exe` — per-user installer

## First-run setup

Before launching the app on a new machine:

```powershell
python -m altvoice setup --profile 12gb-balanced
python -m altvoice models --profile 12gb-balanced --commands
```

The setup command writes `%APPDATA%\ALT-VoiceType\config.json` with the expected model paths
and prints missing-file checks. Download the models, then launch `ALT-VoiceType.exe`.

## Notes

- The PyInstaller spec does **not** include model weights; the installer stays small.
- Code signing is not configured. A signed build reduces SmartScreen/antivirus friction
  caused by the global keyboard hook.
- The PyInstaller one-folder build was verified with PyInstaller 6.22.3 + PySide6 6.12.
  With `asr-qwen`/torch bundled it is ~1.37 GB unpacked and ~341 MB as an installer;
  without the ASR extra it is much smaller but cannot transcribe offline. A console
  debug build was used to verify packaged Qwen3-ASR inference.
- Inno Setup 6.7.3 compiled `ALT-VoiceType-Setup-0.1.0.exe`; the installer is unsigned and
  its silent install still needs a real desktop test.
- To package a custom build directory, pass `/DSourceDir=...` to ISCC.
- Do not run the local llama.cpp servers on `0.0.0.0`; they have no authentication.

