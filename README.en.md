# ALT-VoiceType_Ahee52

**English** | [中文](README.md)

![ALT-VoiceType](altvoice/assets/logo.png)

**Fully offline voice input for Windows: Chinese ASR, context-aware correction, and natural multilingual translation.**

Press the hotkey, speak, press it again. Recognition, correction, and translation run locally, and the result is pasted at the current caret position. No cloud API is required.

> Author: **Ahee52**  
> Status: 0.1.0 preview  
> Current package: **CPU ASR + bundled CUDA llama.cpp**  
> Data: `%APPDATA%\ALT-VoiceType`  
> Models: `<install directory>\models`

---

## Why the current build is CPU + Torch

The author has explored the faster CUDA + PyTorch option, but it is not part of the current release because of practical constraints:

1. **Package size**  
   CUDA PyTorch adds roughly 2.5–3.5 GB installed and 1.5–2.5 GB to the installer.

2. **GPU and driver differences**  
   RTX 20/30/40/50 generations need different CUDA levels. Blackwell (RTX 50) needs CUDA 12.8+, and older drivers must be updated.

3. **Machine-to-machine differences**  
   CUDA Toolkit versions, drivers, DLL conflicts, and PATH settings all affect reliability. The CPU build is easier to reproduce and run.

The current release therefore uses:

```text
CPU + Torch
```

This is a deliberate trade-off in favor of **reliability, reproducibility, and package size**, not a claim that CUDA cannot be faster.

**The community is encouraged to build a CUDA + PyTorch accelerated edition.**  
The ASR adapter, model-service layer, and device configuration already expose extension points; see [CUDA extension](#cuda-extension).

---

## Features

- **Fully offline** — ASR, correction, and translation run locally.
- **Chinese input by default** — the current ASR input language is fixed to Chinese.
- **Multilingual output** — English, Japanese, Korean, Spanish, French, German, Russian, Portuguese, Italian, Arabic, Vietnamese, Thai, Indonesian, Turkish, and more.
- **Context-aware correction** — Qwen3-1.7B-Abliterated handles homophones, punctuation, terminology, and number normalization.
- **Direct insertion** — pastes at the previous caret position.
- **Two result panels** — recognized text and translated text, each with a copy button and “Copied” feedback.
- **Draggable and resizable** — the current size is the minimum; drag any corner or edge.
- **Live level meter** — waveform while recording; turns gray after the stop hotkey.
- **0.39 s tail** — capture continues briefly to preserve trailing speech.
- **ESC cancels recording** — discard the current utterance without recognition, insertion, or history.
- **Configurable hotkey** — left/right Alt alone or with any key; Alt is not exclusively grabbed.
- **Model warm-up** — explicit button and live status.
- **Number normalization** — Chinese numerals become Arabic digits: 二零二五 → 2025, 三千五百 → 3500, 百分之三十 → 30%.

---

## Input language

The current input language is Chinese:

```text
audio → Chinese ASR → Chinese correction → target-language translation
```

To support English input, adjust:

1. the ASR language parameter in `altvoice/pipeline.py`;
2. `ASRConfig.language` in `altvoice/config.py`;
3. the ASR model/prompt for English;
4. the correction prompt’s source-language description.

Contributions for more source languages are very welcome.

---

## Three resource tiers

Only three models are used. The tiers differ in duration limit and resource policy:

| Tier | Duration | Resource | Notes |
|---|---:|---|---|
| **eco** | 20 s | CPU | Lowest resource use |
| **standard** | 45 s | GPU (target) | Correction/translation on GPU; ASR is CPU in the current CPU package |
| **extended** | 120 s | GPU (target) | Longer dictation |

### Fixed models

| Role | Model | Size |
|---|---|---:|
| ASR | Qwen3-ASR-0.6B | 1.75 GB |
| Correction | Qwen3-1.7B-Abliterated Q4 | 1.03 GB |
| Translation | Index-Translate-2B Q4 | 1.22 GB |
| **Total** | | **4.00 GB** |

Models install to:

```text
<install directory>\models
```

The complete installation is about **6.0 GB**.

---

## How it works

```text
Global keyboard hook
   │  lalt / ralt / lalt+q ...
   ▼
Audio capture
   │  sounddevice, 20 ms frames
   ▼
VAD / silence trim
   ▼
ASR (Qwen3-ASR-0.6B, CPU)
   ▼
Correction (Qwen3-1.7B-Abliterated)
   ▼
Number normalization
   ▼
Translation (Index-Translate-2B)
   ▼
Windows text injection
   ▼
Two-panel main window
```

- All heavy work runs on background threads.
- Automatic window updates do not steal focus.
- Only the non-Alt main key of a firing chord is swallowed.
- Recording has a 0.39 s tail.
- ESC cancels the current recording.
- Models are served by local `qwen-asr` / `llama.cpp`.

---

## Full offline installer

### Files

```text
ALT-VoiceType-Setup-0.1.0.exe
ALT-VoiceType-Setup-0.1.0-1.bin
ALT-VoiceType-Setup-0.1.0-2.bin
ALT-VoiceType-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-GitHub.txt
```

Each `.bin` is under 1.8 GB to stay below GitHub’s 2 GB per-release-asset limit.

### Steps

1. Download the exe and all three bins into the same folder.
2. Do not rename them; do not download only the exe.
3. Run `ALT-VoiceType-Setup-0.1.0.exe`.
4. The installer finds the slices automatically.
5. Start `ALT-VoiceType`.
6. Wait for “loaded, ready to type”.
7. Click **Warm up models** on first use.

### Measured sizes

Author’s local test:

```text
Download: about 4.42 GB
Installed: about 6.0 GB
Peak disk during install: about 14 GB
```

Models: 4.00 GB. Application: about 1.37 GB.

---

## Cache and automatic cleanup

| Data | Location | Lifetime |
|---|---|---|
| Recording buffer | process memory | released after recognition or cancel |
| Temporary WAV | `%TEMP%\altvoice_*.wav` | deleted after processing; stale files older than 1 hour removed on startup |
| History | `%APPDATA%\ALT-VoiceType\history.db` | 7 days / 500 entries by default, auto-pruned |
| Session context | process memory | gone on exit |
| Logs | `%APPDATA%\ALT-VoiceType\logs` | status/errors only, no full transcript |
| Models | `<install>\models` | not automatically deleted; removed with the installation |

You can clear history manually:

```text
%APPDATA%\ALT-VoiceType\history.db
```

---

## CUDA extension

The current package is CPU + Torch and does **not** include CUDA PyTorch.

Recommended CUDA direction:

```text
PyTorch 2.8 + cu128
CUDA 12.8
NVIDIA driver 570+
```

One cu128 build can cover:

```text
RTX 20  sm_75
RTX 30  sm_86
RTX 40  sm_89
RTX 50  sm_120
```

Requirements: a recent driver, a wheel containing the target architecture, and CUDA 12.8+ for Blackwell.

Estimated increase:

```text
Installed: +2.5–3.5 GB
Installer: +1.5–2.5 GB
```

CUDA should ship as a separate installer:

```text
ALT-VoiceType-CUDA-Setup-0.1.0.exe
```

---

## Run from source

```powershell
git clone https://github.com/aheechan/ALT-VoiceType_Ahee52.git
cd ALT-VoiceType_Ahee52

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -e ".[ui,audio,asr-qwen,download]"
altvoice run
```

Health check:

```powershell
altvoice health
```

---

## Hotkeys

Default:

```text
Left Alt (lalt)
```

Configurable:

```text
lalt
ralt
lalt+q
ralt+space
alt+shift
```

While recording:

```text
ESC → cancel this recording
```

---

## Data sources and license

- Code: **Apache-2.0**
- ASR: Qwen3-ASR-0.6B
- Correction: Qwen3-1.7B-Abliterated Q4
- Translation: Index-Translate-2B Q4
- Model weights are not stored in Git; the full installer bundles the three models.
- Follow each upstream model license.

Qwen3-ASR-0.6B:

<https://huggingface.co/Qwen/Qwen3-ASR-0.6B>

Index-Translate-2B:

<https://huggingface.co/IndexTeam/Index-Translate-2B-GGUF>

> The abliterated correction model is distributed only in the full installer; no standalone link is provided here.

---

## Contribute

This is an open-source, offline-first voice input project. The author has made a pragmatic trade-off between **stability, size, and response speed**, and it can still improve.

Welcome contributions:

- CUDA + PyTorch acceleration
- English and minority-language input
- Correction rules and number normalization
- Smaller packaging
- Windows compatibility testing (RTX 20/30/40/50)
- UI, docs, and translations

If this project is useful to you, open an Issue, send a PR, or share it with someone who needs it.

**Help people across the world communicate without barriers.**

---

## Manual GitHub upload

Upload source to the Git repository and installers to **Releases** — never commit the binaries.

Step-by-step guide:

[docs/UPLOAD-MANUAL.md](docs/UPLOAD-MANUAL.md)

---

**ALT-VoiceType_Ahee52** · offline voice input for Windows
