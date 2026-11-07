# ALT-VoiceType_Ahee52

**English** | [中文](README.md)

![ALT-VoiceType](altvoice/assets/logo.png)

**Fully offline voice input for Windows: Chinese ASR, context-aware correction, and natural multilingual translation.**

Press the hotkey, speak, press it again. Recognition, correction, and translation all run locally, and the result is pasted directly at the current caret position. No cloud API is used.

> **Status: 0.1.0 preview.** This repository contains the application source, model profiles, Windows hotkey/injection layer, PySide6 UI, packaging scripts, and tests. The model weights are distributed only through the full offline installer, not in this repository.

---

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Four model tiers](#four-model-tiers)
- [Full offline installer](#full-offline-installer)
- [Lite installer](#lite-installer)
- [Manual non-uncensored models](#manual-non-uncensored-models)
- [Run from source](#run-from-source)
- [Hotkeys](#hotkeys)
- [Project layout](#project-layout)
- [Privacy and license](#privacy-and-license)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Fully offline** — ASR, correction, and translation run on the local machine.
- **Chinese-first ASR** — Qwen3-ASR handles Mandarin, accents, and mixed Chinese/English speech.
- **Context-aware correction** — a 1.7B corrector plus deterministic guards reduces homophone, punctuation, and name errors.
- **Local translation** — Index-Translate 2B / Qwen3-4B produces natural Chinese-to-English/Japanese/Korean output.
- **Direct insertion** — the result is pasted at the last caret position; no manual copy/paste.
- **Two result panels** — recognized text and translated text, each with its own copy button and “Copied” feedback.
- **Draggable main window** — black/white frameless window, shown by default, without stealing input focus.
- **Live level meter** — the waveform is shown while recording; after the second hotkey press it turns gray, but capture continues for **2 seconds** so trailing speech is not cut off.
- **Warm-up button** — explicit model warm-up with live loading/ready status.
- **Configurable hotkey** — left Alt, right Alt, or left/right Alt plus any key; Alt is not exclusively grabbed, so `Alt+Tab` and similar shortcuts still work.
- **Offline installer options** — a full five-model bundle, or a lite installer with manual model downloads.

## How it works

```text
Global keyboard hook
   │  lalt / ralt / lalt+q / ralt+space ...
   ▼
Audio capture thread
   │  sounddevice, 20 ms frames
   ▼
VAD / silence trimming
   │
   ▼
ASR (Qwen3-ASR)
   │  speech → raw text
   ▼
Correction (Qwen3-1.7B + guards)
   │  homophones, punctuation, glossary, context
   ▼
Translation (Index-Translate 2B/4B)
   │  Chinese → target language; skipped when target is Chinese
   ▼
Windows text injection
   │  restore the previous caret, then paste
   ▼
Main window panels (recognized / translated)
```

Design notes:

- Recording, ASR, correction, and translation run on worker threads; the UI only displays state.
- The main window is shown with a non-activating flag, so automatic updates do not steal focus from the target input box.
- Only the non-Alt main key of a triggered chord is swallowed; Alt itself is passed through.
- After the second hotkey press, audio keeps recording for 2 seconds before the worker stops.
- Switching a model tier stops the old local servers first, then loads and warms the new profile.
- Local models are served by `llama.cpp` and `qwen-asr`; no remote inference API is required.

## Four model tiers

The full installer contains five model files, combined into four selectable tiers:

| Tier | ASR | Correction | Translation | Intended use |
|---|---|---|---|---|
| **safe** | Qwen3-ASR-0.6B | Qwen3-1.7B Abliterated | Index-Translate-2B | 12 GB VRAM, speed first |
| **balanced** | Qwen3-ASR-0.6B | Qwen3-1.7B Abliterated | Qwen3-4B Abliterated | 12 GB, better translation |
| **12gb-max** | Qwen3-ASR-1.7B Uncensored | Qwen3-1.7B Abliterated | Index-Translate-2B | 12 GB, better ASR |
| **16gb-quality** | Qwen3-ASR-1.7B Uncensored | Qwen3-1.7B Abliterated | Qwen3-4B Abliterated | 16 GB+, quality first |

> **Uncensored-model notice**
>
> The 1.7B Uncensored ASR, 1.7B Abliterated corrector, and 4B Abliterated translator are distributed **only inside the full offline installer**.
> This repository and the manual-download section below provide only **non-uncensored standard models**. No standalone links for the uncensored variants are provided.

## Full offline installer

### Files

The release page contains:

```text
ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-1.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-2.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-3.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-4.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-5.bin
ALT-VoiceType_Ahee52-Full-Setup-0.1.0-6.bin
SHA256SUMS.txt
```

Each `.bin` is under 1.8 GB to stay below the GitHub Release 2 GB per-file limit.

### Steps

1. Download the **exe and all six bin files** into the same folder.
2. Do not rename them, and do not download only the exe.
3. Run `ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe`.
4. Follow the wizard; the installer reads the matching bin files automatically.
5. Start `ALT-VoiceType` and wait for “loaded, ready to type”.
6. On first use, click **Warm up models** and wait for completion.

### Requirements

- Windows 10/11 x64
- NVIDIA GPU with 12 GB+ VRAM recommended; CPU works but is slower
- Installed size: about **12.1 GB**
- Download size: about **9.43 GB**
- At least **25 GB** free disk during installation (installer + installed files)
- A microphone (3.5 mm or USB)

### Verify

```powershell
certutil -hashfile ALT-VoiceType_Ahee52-Full-Setup-0.1.0.exe SHA256
```

Expected hashes for every slice are in `SHA256SUMS.txt`.

## Lite installer

The lite installer is about **341 MB** and contains the application only:

```text
ALT-VoiceType_Ahee52-Setup-0.1.0.exe
```

On first launch it checks for models. Missing models can be downloaded by the setup dialog or manually using the next section.

Use the lite installer when:

- you already have the model files;
- you want to choose only the models you need;
- disk space is limited.

## Manual non-uncensored models

The files below are the **standard, non-uncensored** models. The uncensored variants are not listed here.

Model root:

```text
%LOCALAPPDATA%\ALT-VoiceType\models
```

PowerShell shorthand:

```powershell
$m = "$env:LOCALAPPDATA\ALT-VoiceType\models"
```

### 1. ASR: Qwen3-ASR-0.6B

Hugging Face:

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

Destination:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_asr_0_6b
```

Download:

```powershell
huggingface-cli download Qwen/Qwen3-ASR-0.6B `
  --local-dir "$env:LOCALAPPDATA\ALT-VoiceType\models\qwen3_asr_0_6b"
```

This is the standard ASR used by **safe** and **balanced**.

### 2. ASR: Qwen3-ASR-1.7B (standard)

Hugging Face:

<https://huggingface.co/Qwen/Qwen3-ASR-1.7B>

Destination:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_asr_1_7b
```

Download:

```powershell
huggingface-cli download Qwen/Qwen3-ASR-1.7B `
  --local-dir "$env:LOCALAPPDATA%\ALT-VoiceType\models\qwen3_asr_1_7b"
```

This is the non-uncensored alternative for the ASR used by `12gb-max` and `16gb-quality`. Point `asr.model_path` at this directory to use it.

### 3. Correction: Qwen3-1.7B-Instruct Q8

Hugging Face:

<https://huggingface.co/Qwen/Qwen3-1.7B-GGUF>

Filename:

```text
Qwen3-1.7B-Q8_0.gguf
```

Destination:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_1_7b_instruct_q4\Qwen3-1.7B-Q8_0.gguf
```

Download:

```powershell
huggingface-cli download Qwen/Qwen3-1.7B-GGUF `
  --include "*Qwen3-1.7B-Q8_0.gguf" `
  --local-dir "$env:LOCALAPPDATA%\ALT-VoiceType\models\qwen3_1_7b_instruct_q4"
```

### 4. Translation: Index-Translate-2B Q4

Hugging Face:

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

Filename:

```text
Index-Translate-2B.Q4_K_M.gguf
```

Destination:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\index_translate_2b_q4\Index-Translate-2B.Q4_K_M.gguf
```

Download:

```powershell
huggingface-cli download IndexTeam/Index-Translate-2B-GGUF `
  --include "*Index-Translate-2B.Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA%\ALT-VoiceType\models\index_translate_2b_q4"
```

### 5. Translation: Qwen3-4B-Instruct Q4 (standard)

Hugging Face:

<https://huggingface.co/Qwen/Qwen3-4B-GGUF>

Filename:

```text
Qwen3-4B-Q4_K_M.gguf
```

Destination:

```text
%LOCALAPPDATA%\ALT-VoiceType\models\qwen3_4b_instruct_q4\Qwen3-4B-Q4_K_M.gguf
```

Download:

```powershell
huggingface-cli download Qwen/Qwen3-4B-GGUF `
  --include "*Qwen3-4B-Q4_K_M.gguf" `
  --local-dir "$env:LOCALAPPDATA%\ALT-VoiceType\models\qwen3_4b_instruct_q4"
```

This is the non-uncensored alternative for the 4B translator used by `balanced` and `16gb-quality`.

### Configure standard models

Edit:

```text
%APPDATA%\ALT-VoiceType\config.json
```

Point these fields at the downloaded files:

```json
{
  "asr": {
    "model_path": "C:\\Users\\<you>\\AppData\\Local\\ALT-VoiceType\\models\\qwen3_asr_0_6b"
  },
  "corrector": {
    "model_path": "C:\\Users\\<you>\\AppData\\Local\\ALT-VoiceType\\models\\qwen3_1_7b_instruct_q4\\Qwen3-1.7B-Q8_0.gguf"
  },
  "translator": {
    "model_path": "C:\\Users\\<you>\\AppData\\Local\\ALT-VoiceType\\models\\index_translate_2b_q4\\Index-Translate-2B.Q4_K_M.gguf"
  }
}
```

The bundled tier presets point at the uncensored paths. After manually switching to standard models, do not switch tiers again in Settings, or the paths will be reset.

### Slow Hugging Face access

If direct Hugging Face downloads are slow:

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
```

The download commands remain the same.

## Run from source

Requirements:

- Windows 10/11 x64
- Python 3.11 or 3.12
- Optional NVIDIA driver; CPU is supported but slower
- A microphone

```powershell
git clone https://github.com/<your-name>/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-qwen,download]"
```

Run:

```powershell
altvoice run
```

Environment check only:

```powershell
altvoice health
```

Configuration is stored in `%APPDATA%\ALT-VoiceType\config.json`; models are read from `%LOCALAPPDATA%\ALT-VoiceType\models`.

## Hotkeys

Default:

```text
Left Alt (lalt)
```

Configurable in Settings:

```text
lalt
ralt
lalt+q
ralt+space
lalt+shift
alt+q
```

- Left and right Alt are distinguished.
- Alt is not exclusively grabbed; `Alt+Tab`, `Alt+F4`, and other system shortcuts still work.
- Only the main non-Alt key of a firing chord is suppressed.
- Changes apply immediately after saving.

## Project layout

```text
altvoice/
  asr/             ASR adapters (Qwen3-ASR, Sherpa fallback)
  correct/         corrector, prompts, guards
  translate/       translation prompts, client, cleanup
  llm/             OpenAI-compatible local llama.cpp client
  hotkey/          global hook, left/right Alt chords
  inject/          Windows text injection and focus restore
  ui/              PySide6 tray, main window, settings, history
  audio.py         microphone capture and level callback
  pipeline.py      ASR → correction → translation → injection
  app.py           controller, recording state machine, 2 s tail
  models.py        model catalog and four tiers
  servers.py       llama.cpp server supervision

packaging/         PyInstaller spec, Inno Setup installers, bundle script
tests/             unit tests and UI smoke tests
docs/              architecture, models, running, release docs
```

## Privacy and license

- Offline by default; raw audio is not persisted.
- Optional local SQLite history can be disabled or cleared.
- Code is **Apache-2.0**.
- Model weights are not part of this repository; each model follows its upstream license.
- The uncensored models included in the full offline installer are distributed only with that installer; this repository does not provide standalone links.

## Troubleshooting

### Installer cannot find a slice

Keep the exe and `-1.bin` through `-6.bin` in the **same folder**. Do not rename them, and avoid names such as `.bin.txt` or `(1)`.

### SmartScreen says “Unknown publisher”

The installer is currently unsigned. Use “More info → Run anyway”, or verify the file with `SHA256SUMS.txt`.

### The hotkey does nothing

Check that Settings uses `lalt` or `ralt`, and that another application is not already using the chord. Confirm the model is warmed up.

### Recognition is slow

- Make sure the app is using the GPU, not CPU.
- `12gb-max` / `16gb-quality` use the 1.7B ASR, which is much slower on CPU.
- Click **Warm up models** before dictating.
- Close other GPU-heavy applications.

### Text is not pasted

Some games and elevated windows block synthetic input. Run the app at the same privilege level as the target window, and use a target that supports Ctrl+V.

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows


