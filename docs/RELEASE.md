# Release checklist

## 1. Build the app

```powershell
cd altvoice
python -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
pip install -e ".[ui,audio,asr-qwen,download]" "pyinstaller>=6.6"
python -m PyInstaller --noconfirm --workpath build packaging\altvoice.spec
```

The one-folder output is `dist\ALT-VoiceType` (about 1.37 GB with torch/qwen-asr).

## 2. Build the installer

```powershell
ISCC packaging\installer.iss
```

The installer is written to `dist\installer\ALT-VoiceType-Setup-0.1.0.exe` (about
341 MB). It is per-user and unsigned.

## 3. Startup smoke test (from source)

On a real interactive desktop:

```powershell
python -m altvoice run --smoke 3
```

Expected exit code: `0`. A second simultaneous instance must exit with code `4`.

## 4. Packaged ASR smoke test (console debug build)

Build a console variant to verify bundled Qwen3-ASR without guessing from a
windowed process:

```powershell
$spec = Get-Content packaging\altvoice.spec -Raw
$spec = $spec -replace 'name="ALT-VoiceType"', 'name="ALT-VoiceTypeDebug"'
$spec = $spec -replace 'console=False', 'console=True'
Set-Content packaging\altvoice-debug.spec $spec
python -m PyInstaller --noconfirm --workpath build-debug --distpath dist-debug packaging\altvoice-debug.spec
.\dist-debug\ALT-VoiceTypeDebug\ALT-VoiceTypeDebug.exe doctor
.\dist-debug\ALT-VoiceTypeDebug\ALT-VoiceTypeDebug.exe transcribe benchmarks\audio\asr_zh.wav --engine qwen3 --model-path Qwen/Qwen3-ASR-0.6B --device cpu --json
```

The last command must return JSON with `"text": "甚至出现交易几乎停滞的情况。"`
(or equivalent Chinese text) and a latency in milliseconds.

## 5. Install test on a real desktop

1. Double-click `ALT-VoiceType-Setup-0.1.0.exe`.
2. Install for the current user.
3. Launch ALT-VoiceType from the Start menu.
4. Confirm the tray icon, Alt long-press, preview, insert, and quit.
5. Run the uninstaller and confirm the process, tray icon, and hook are gone.
6. Reinstall over the old version to confirm the upgrade path.

## 6. 12 GB validation

On an RTX 3070 12 GB:

```powershell
python -m altvoice --config %APPDATA%\ALT-VoiceType\config.json profiles
python -m altvoice --config %APPDATA%\ALT-VoiceType\config.json run
```

Record peak VRAM (`nvidia-smi`) and ASR/correction/translation latency. If
`12gb-max` is tight, keep the default `12gb-balanced` and close GPU apps.

## 7. Microphone validation

```powershell
python -m altvoice audio --list
python -m altvoice audio --seconds 3 --out mic-test.wav
```

Then hold Alt, speak a Chinese sentence, release, and verify the preview and
insertion. Test with at least one non-Chinese target language and with preview
disabled.
