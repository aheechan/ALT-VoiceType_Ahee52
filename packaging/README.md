# Packaging

AltVoice is a Windows desktop app. The installer uses a PyInstaller one-folder build plus
Inno Setup. **Model weights are not bundled**; they stay in
`%LOCALAPPDATA%\AltVoice\models` and are managed by `python -m altvoice setup` /
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
pip install -e ".[ui,audio]" "pyinstaller>=6.6"
pyinstaller --clean --noconfirm packaging\altvoice.spec
ISCC packaging\installer.iss
```

Outputs:

- `dist\AltVoice\AltVoice.exe` — one-folder app
- `dist\installer\AltVoice-Setup-0.1.0.exe` — per-user installer

## First-run setup

Before launching the app on a new machine:

```powershell
python -m altvoice setup --profile 12gb-balanced
python -m altvoice models --profile 12gb-balanced --commands
```

The setup command writes `%APPDATA%\AltVoice\config.json` with the expected model paths
and prints missing-file checks. Download the models, then launch `AltVoice.exe`.

## Notes

- The PyInstaller spec does **not** include model weights; the installer stays small.
- Code signing is not configured. A signed build reduces SmartScreen/antivirus friction
  caused by the global keyboard hook.
- The build is not tested in this sandbox because PySide6 and PyInstaller are not
  installed here; CI has a manual build workflow.
- Do not run the local llama.cpp servers on `0.0.0.0`; they have no authentication.
