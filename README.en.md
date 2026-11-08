# ALT-VoiceType_Ahee52

**English** | [中文](README.md)

![ALT-VoiceType](altvoice/assets/logo.png)

**Fully offline voice input for Windows: Chinese ASR, context-aware correction, and natural multilingual translation.**

Press the hotkey, speak, press it again. Everything runs locally and the result is pasted at the current caret position.

> Author: **Ahee52**  
> Status: 0.1.0 preview  
> Current package: **CPU ASR + bundled CUDA llama.cpp**  
> Config/logs: `%APPDATA%\ALT-VoiceType`  
> Installed models: `<install>\models`  
> Source models: `%LOCALAPPDATA%\ALT-VoiceType\models`

---

## Choose an edition

| | Chinese edition | English edition |
|---|---|---|
| Product | ALT-VoiceType | ALT-VoiceType English |
| Default input | Chinese | English |
| Default output | Chinese | English |
| ASR | Qwen3-ASR-0.6B | faster-whisper small.en |
| Installer | about 4.42 GB | about 3.57 GB |
| Installed | about 6.0 GB | about 5.6 GB |
| Data | `%APPDATA%\ALT-VoiceType` | `%APPDATA%\ALT-VoiceType-EN` |
| Release | `v0.1.0-zh` | `v0.1.0-en` |

Downloads:

- Chinese edition: <https://github.com/aheechan/ALT-VoiceType_Ahee52/releases/tag/v0.1.0-zh>
- English edition: <https://github.com/aheechan/ALT-VoiceType_Ahee52/releases/tag/v0.1.0-en>

Both editions can be installed side by side.

Full upload walkthrough: [docs/UPLOAD-BILINGUAL.md](docs/UPLOAD-BILINGUAL.md).

---

## What is this repository?

A runnable Windows voice-input project, not just an installer download page.

```text
altvoice/          ASR, correction, translation, hotkeys, injection, UI
tests/             105 unit/UI tests
packaging/         PyInstaller + Inno Setup
scripts/           helper scripts
docs/              architecture, deployment, upload guide
benchmarks/        ASR benchmark manifests
```

You can use the installer, run from source, modify the pipeline, or contribute CUDA/English/minority-language support.

---

## Two ways to use it

| Route | For | Requires |
|---|---|---|
| **Installer** | End users | Download 4.42 GB of split files |
| **Source** | Developers / explorers | Python, models, microphone |

---

## Author's trade-off: why CPU ASR

The author explored the faster **CUDA + PyTorch** route but did not ship it in the current package:

1. **Size** — CUDA PyTorch adds about 2.5–3.5 GB installed, 1.5–2.5 GB to the installer.
2. **GPU/driver differences** — RTX 20/30/40/50 need different CUDA levels; RTX 50 (Blackwell) needs CUDA 12.8+.
3. **Machine differences** — Toolkit, driver, DLL, and PATH conflicts make CUDA less reproducible.

Current package:

```text
ASR: CPU + Torch
Correction/translation: bundled CUDA llama.cpp
```

This is a deliberate choice for **reliability, reproducibility, and size**, not a claim that CUDA cannot be faster.

**The community is encouraged to build a CUDA + PyTorch edition.** The ASR adapter, device configuration, and model-service layer expose extension points.

---

## Fixed models and three tiers

| Role | Model | Size |
|---|---|---:|
| ASR | Qwen3-ASR-0.6B | 1.75 GB |
| Correction | Qwen3-1.7B-Abliterated Q4 | 1.03 GB |
| Translation | Index-Translate-2B Q4 | 1.22 GB |
| **Total** | | **4.00 GB** |

| Tier | Duration | Resource | Notes |
|---|---:|---|---|
| **eco** | 20 s | CPU | Lowest resource |
| **standard** | 45 s | GPU target | Default |
| **extended** | 120 s | GPU target | Long dictation |

In the current CPU-ASR package, `standard`/`extended` use GPU for correction/translation; ASR remains CPU.

---

## English edition

The English edition is a separate product with its own installer and data dir:

```text
Product: ALT-VoiceType English
Installer: ALT-VoiceType-EN-Setup-0.1.0.exe
Data: %APPDATA%\ALT-VoiceType-EN
ASR: faster-whisper small.en (English-only, CPU)
Correction/translation: Qwen3-1.7B + Index-Translate-2B
```

Installer: about **3.57 GB**; installed: about **5.6 GB**.

- English input by default
- English output by default
- English main window, settings, and tray menu
- Separate AppId, shortcut, history, and logs
- Can coexist with the Chinese edition
- Separate release: `v0.1.0-en`

Source build:

```powershell
$env:ALT_VOICE_EDITION = "en"
python -m altvoice run
```

## Installer

Download into one folder:

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

Run the exe. The installer shows a **directory chooser**, so the user can select C/D/E.

Measured:

```text
Installer: about 4.42 GB
Installed: about 6.0 GB
Peak disk: about 14 GB
```

Includes the app, three models, and a bundled CUDA `llama.cpp` runtime.

---

## Run from source

Requirements: Windows 10/11 x64, Python 3.11/3.12, Git, microphone.

```powershell
git clone https://github.com/aheechan/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-whisper,download]"

python -m altvoice setup --profile 12gb-balanced
python -m altvoice health
python -m altvoice run
```

Source models are read from:

```text
%LOCALAPPDATA%\ALT-VoiceType\models
```

Config:

```text
%APPDATA%\ALT-VoiceType\config.json
```

Logs:

```text
%APPDATA%\ALT-VoiceType\logs
```

### Models

ASR, Qwen3-ASR-0.6B:

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

```powershell
huggingface-cli download Qwen/Qwen3-ASR-0.6B `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType\models\qwen3_asr_0_6b"
```

Translation, Index-Translate-2B:

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

```powershell
huggingface-cli download IndexTeam/Index-Translate-2B-GGUF `
  --include "*Index-Translate-2B.Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType\models\index_translate_2b_q4"
```

Correction, Qwen3-1.7B-Abliterated Q4:

<https://huggingface.co/mradermacher/Qwen3-1.7B-abliterated-v2-i1-GGUF>

Place it in:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_1_7b_abliterated_q4
```

### English edition models

The English edition uses its own model directory:

```text
%LOCALAPPDATA%\ALT-VoiceType-EN\models
```

| Role | Model | Destination |
|---|---|---|
| ASR | faster-whisper small.en | `faster_whisper_small_en` |
| Correction | Qwen3-1.7B-Abliterated Q4 | `qwen3_1_7b_abliterated_q4` |
| Translation | Index-Translate-2B Q4 | `index_translate_2b_q4` |

faster-whisper:

<https://huggingface.co/Systran/faster-whisper-small.en>

```powershell
huggingface-cli download Systran/faster-whisper-small.en `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType-EN\models\faster_whisper_small_en"
```

Source English run:

```powershell
$env:ALT_VOICE_EDITION = "en"
pip install -e ".[ui,audio,asr-whisper,download]"
python -m altvoice setup --profile 12gb-balanced
python -m altvoice health
python -m altvoice run
```

`health` should report:

```text
whisper    available
Requested ASR: whisper
```

Source users also need `llama-server.exe`:

```powershell
winget install ggml.llamacpp
```

The installer already includes a CUDA runtime.

### Build both editions

Chinese app and installer:

```powershell
$env:ALT_VOICE_EDITION = "zh"
$env:PYTHONPATH = ".pylibs"
python -m PyInstaller --noconfirm --workpath build --distpath dist packaging/altvoice.spec

$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  packaging\installer-bundle.iss
```

English app and installer:

```powershell
$env:ALT_VOICE_EDITION = "en"
$env:PYTHONPATH = ".pylibs;.whisperlibs"
python -m PyInstaller --noconfirm --workpath build-en --distpath dist-en packaging/altvoice-en.spec

& $iscc "/DSourceDir=$PWD\dist-en\ALT-VoiceType-EN" `
  "/DModelsDir=D:\ALT-VoiceType\models" `
  "/DLlamaDir=D:\llama.cpp" `
  "/DWhisperModelDir=$env:LOCALAPPDATA\ALT-VoiceType-EN\models" `
  packaging\installer-en.iss
```

Outputs:

```text
dist\installer
dist\installer-en
```

Full upload walkthrough:

[docs/UPLOAD-BILINGUAL.md](docs/UPLOAD-BILINGUAL.md)

---

## How it works

```text
Global hook
→ Audio capture
→ VAD / trim
→ ASR (Qwen3-ASR-0.6B)
→ Correction (Qwen3-1.7B-Abliterated)
→ Number normalization
→ Translation (Index-Translate-2B)
→ Windows text injection
→ Two-panel UI
```

- Background threads for all heavy work.
- Automatic window updates do not steal focus.
- Alt is not exclusively grabbed.
- 0.39 s recording tail.
- ESC cancels recording.
- Local `qwen-asr` / `llama.cpp`; no cloud API.

---

## Cache and automatic cleanup

| Data | Location | Lifetime |
|---|---|---|
| Recording buffer | process memory | released after recognition/cancel |
| Temporary WAV | `%TEMP%\altvoice_*.wav` | deleted after processing; stale >1h removed on startup |
| History | `%APPDATA%\ALT-VoiceType\history.db` | 7 days / 500 entries, auto-pruned |
| Session context | process memory | gone on exit |
| Logs | `%APPDATA%\ALT-VoiceType\logs` | no full transcripts |
| Models | `<install>\models` | removed with uninstall |

Clear history manually:

```powershell
Remove-Item "$env:APPDATA\ALT-VoiceType\history.db"
```

---

## CUDA extension

Current package does **not** include CUDA PyTorch; ASR is CPU.

Recommended:

```text
PyTorch 2.8 + cu128
CUDA 12.8
NVIDIA driver 570+
```

A cu128 build can cover:

```text
RTX 20  sm_75
RTX 30  sm_86
RTX 40  sm_89
RTX 50  sm_120
```

Estimated increase: +2.5–3.5 GB installed, +1.5–2.5 GB installer.

Ship as a separate installer:

```text
ALT-VoiceType-CUDA-Setup-0.1.0.exe
```

---

## Hotkeys and ESC

Default: `lalt`.

Configurable: `lalt`, `ralt`, `lalt+q`, `ralt+space`, `alt+shift`.

While recording:

```text
ESC → cancel this recording
```

No recognition, insertion, or history entry after cancel.

---

## Development, tests, packaging

```powershell
python -m unittest discover -s tests
```

Current: **105 tests OK**.

```powershell
$env:PYTHONPATH = ".pylibs"
python -m PyInstaller --noconfirm --workpath build --distpath dist packaging/altvoice.spec
```

```powershell
$iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
& $iscc "/DSourceDir=$PWD\dist\ALT-VoiceType" `
  "/DModelsDir=$PWD\models" `
  "/DLlamaDir=C:\path\to\llama.cpp" `
  packaging\installer-bundle.iss
```

Manual GitHub upload:

[docs/UPLOAD-MANUAL.md](docs/UPLOAD-MANUAL.md)

---

## Troubleshooting

### Translation always Chinese

Check:

```text
%APPDATA%\ALT-VoiceType\logs\translator.log
```

Common causes: missing `llama-server`, GPU initialization failure, or the model returning only `reasoning_content`.

The installer bundles CUDA `llama-server` and uses:

```text
--reasoning off
```

### Alt does nothing

Check the configured hotkey, wait for “loaded”, inspect `app.log`.

### Slow recognition

CPU ASR loads slowly on first use; click **Warm up models** and observe the 20/45/120 s limits.

### Unknown publisher

The installer is unsigned. Use “More info → Run anyway” or verify with `SHA256SUMS.txt`.

---

## Contribute

Open-source and offline-first. Contributions welcome:

- CUDA + PyTorch acceleration
- English and minority-language input
- Correction rules and number normalization
- Smaller packaging
- RTX 20/30/40/50 testing
- UI, docs, translations

**Help people across the world communicate without barriers.**

---

## License

- Code: **Apache-2.0**
- Model weights are not stored in Git
- Follow each upstream model license

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows
