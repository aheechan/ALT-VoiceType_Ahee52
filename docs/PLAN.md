# ALT-VoiceType development plan

Status: M0 (selection and scaffold). Updated 2026-11-05.

## 1. Product definition

ALT-VoiceType is an offline Windows voice input assistant:

- Global hotkey: hold `Alt` to record, release to transcribe.
- System tray: target language, mode (transcribe / translate / copy), scene preset, settings.
- Chinese speech is the primary input; output can be Chinese text or a translation.
- Context-aware correction: rolling utterances + glossary + scene, minimal edits only.
- Natural translation: whole-utterance, context-aware, style-controlled; not word-by-word.
- Fully local runtime after models are installed.

**Non-goals for v0.1:** macOS/Linux, TSF IME, streaming partial text, TTS/voice cloning,
cloud sync, accounts, 150-language UI.

## 2. Baseline hardware and profiles

The baseline is an RTX 3070 (12 GB); profiles scale upward to 16 GB and 24 GB. The application
detects VRAM at startup (`nvidia-smi`), picks a profile, and lets the user override it.

| Profile | ASR | Corrector | Translator | Est. weights |
|---|---|---|---|---:|
| `12gb-balanced` | Qwen3-ASR-0.6B (~1.5 GB) | Qwen3-1.7B Q8 (~1.9 GB) | Index-Translate-9B Q4 (~5.7 GB) | ~9.1 GB |
| `12gb-max` | Qwen3-ASR-1.7B BF16 (~3.6 GB) | Qwen3-1.7B Q8 (~1.9 GB) | Index-Translate-9B Q4 (~5.7 GB) | ~11.2 GB |
| `12gb-safe` | Qwen3-ASR-0.6B (~1.5 GB) | Qwen3-1.7B Q8 (~1.9 GB) | Index-Translate-2B Q4 (~1.6 GB) | ~5.0 GB |
| `16gb-quality` | Qwen3-ASR-1.7B (~3.6 GB) | Qwen3-4B Q4 (~2.6 GB) | Index-Translate-9B Q4 (~5.7 GB) | ~11.9 GB |
| `24gb-quality` | Qwen3-ASR-1.7B (~3.6 GB) | Qwen3-4B Q4 (~2.6 GB) | Index-Translate-9B Q4 (~5.7 GB) | ~11.9 GB |
| `cpu-safe` | SenseVoice-Small (~0.3 GB) | rules only | Index-Translate-2B Q4 (~1.6 GB) | ~2.1 GB |

`12gb-balanced` keeps ~3 GB for KV cache, CUDA context and the desktop. `12gb-max` uses the
1.7B ASR but is tight; close background GPU apps. If the translator cannot fit, it is
lazy-loaded after ASR or swapped to the 2B model.

## 3. Technology choices

| Layer | Choice | Why |
|---|---|---|
| UI | PySide6 (LGPL) | Native tray/overlay on Windows; permissive linking |
| Hotkey | Win32 low-level keyboard hook | Need Alt down/up and long-press discrimination, not just a registered combo |
| Audio | `sounddevice` + 16 kHz mono + Silero/energy VAD | Low-latency capture; simple WAV path for tests |
| ASR primary | Qwen3-ASR-1.7B | Windows-friendly PyTorch/qwen-asr, 52 languages/dialects, 22 Chinese dialects |
| ASR quality option | FireRedASR2-AED 1.1B | Best Mandarin CER tier, Apache-2.0; upstream tested on Ubuntu only |
| Corrector | Qwen3-1.7B/4B-Instruct Q4 via llama.cpp | Minimal-edit Chinese correction at low latency |
| Translator | Index-Translate-9B Q4 via llama.cpp | Chinese-centric, 150 languages, offline |
| Injection | Clipboard paste + SendInput Unicode | Works in most apps; TSF deferred |
| Packaging | PyInstaller one-folder + Inno Setup | Large models stay outside the installer |

### Why Qwen3-ASR is the Windows default

FireRedASR2-AED has the best Mandarin CER in the FireRedASR2S comparison (3.05% vs 3.76% for
Qwen3-ASR-1.7B), but the upstream FireRedASR2S repository explicitly says its code has only been
tested on Ubuntu 22.04. ALT-VoiceType targets Windows 10/11, so the default is Qwen3-ASR-1.7B:
native PyTorch/Transformers, `qwen-asr`, 22 Chinese dialects, streaming support, Apache-2.0.
FireRedASR2-AED stays selectable as a quality option for users who can run it (WSL/Linux or a
tested Windows setup).

### Why not Whisper as the primary ASR

Whisper-large-v3 is roughly 5.1% CER on AISHELL-1 and 18.9% on WenetSpeech meeting in FireRedASR's
comparison, versus ~0.6% and ~4.8% for FireRedASR-AED. Whisper remains an optional multilingual
engine, not the Chinese default.

### Why not Index-Translate-Omni for ASR

Its Chinese ASR CER is in the 13–19% range, far behind a dedicated Chinese ASR. ALT-VoiceType uses
Index-Translate only for text translation.

## 4. Pipeline

```text
Alt long-press
  -> capture 16 kHz mono
  -> trim silence / VAD
  -> ASR (Qwen3-ASR-1.7B; optional FireRedASR2-AED)
  -> punctuation (model built-in or CT-punc)
  -> context corrector (Qwen3 + glossary + recent utterances)
  -> translator (Index-Translate-9B; skipped when target is Chinese)
  -> preview / clipboard-or-SendInput injection
  -> optional local history
```

### Context correction rules

- Correct only homophones, typos, punctuation, repeated words, names and terminology.
- Never add facts, never summarize, never change tone.
- Guard: if edit distance > 25% or the model reports high risk, force preview.
- Learn from user edits in the preview: add accepted terms to the glossary.
- Context: last 5–10 finalized utterances, current app title, scene preset, user glossary.

### Natural translation rules

- Translate the whole utterance, with the previous 2–3 source/translation pairs.
- Preserve emotion, sentence fragments, interjections, humor and intent.
- Use everyday target-language phrasing; forbid explanations and expansions.
- Style presets: daily, live/streaming, business, game, subtitle.
- Evaluate with human raters; if prompt iteration is not enough, train a LoRA on user data later.

## 5. Interaction

- **Long-press Alt (280 ms)** to record; release to finish. Short taps still reach the app.
- If another key is pressed while Alt is held, cancel voice mode and replay the combination.
- `Esc` cancels; tray icon turns red; a small waveform overlay appears near the bottom.
- Default insertion: preview bubble with the corrected text and translation; `Enter` inserts,
  `Esc` cancels, `Ctrl+Z` undoes. Low-confidence results always preview.
- Tray right-click: target language, mode, scene, settings, history, quit.
- Per-app target language profiles are a v1.1 feature.

## 6. Milestones

| Phase | Duration | Deliverable | Exit criteria |
|---|---|---|---|
| M0 | 2–3 days | Repo, docs, ASR bake-off harness, 100-utterance local set | Pick primary/fallback engine from measured CER + latency |
| M1 | 5–7 days | Alt hook, capture, ASR, tray, clipboard injection, Chinese mode | Stable insertion in Notepad/Chrome/Word/WeChat/VS Code |
| M2 | 5–7 days | Corrector, glossary, rolling context, preview, undo | Relative CER ↓ ≥25%, over-correction ≤2% |
| M3 | 5–7 days | Index-Translate-9B, 6 target languages, style presets | Naturalness ≥4/5, meaning ≥4.5/5 |
| M4 | 3–5 days | Installer, model downloader, autostart, logs, compatibility matrix | Offline run; top-10 apps ≥98% insertion |
| M5 | 3–5 days | Beta with 3–5 users, fixes, docs | No P0 for one week; tag v0.1.0 |

One full-time developer: ~4–6 weeks. Part-time: ~8–10 weeks.

## 7. Evaluation

**ASR:** 100 real utterances (quiet/noisy, fast speech, names, terms, code-switching); CER,
punctuation F1, latency, VRAM. Target: CER ≤5% clean, ≤10% noisy.

**Correction:** relative CER reduction ≥25%; over-correction ≤2%; latency ≤0.8 s.

**Translation:** 50 utterances × 3 languages; human 5-point naturalness/meaning/emotion; blind
A/B against DeepL/GPT; target naturalness ≥4/5.

**End-to-end:** 5 s utterance → inserted text ≤2 s on RTX 3070; top-10 app insertion ≥98%;
zero outbound network requests; 8-hour stability.

## 8. Risks

| Risk | Mitigation |
|---|---|
| Alt conflicts with menus/Alt+Tab | Long-press threshold, replay short taps, cancel on combos, configurable key |
| Injection blocked in elevated/game apps | Clipboard first, SendInput fallback, compatibility matrix, TSF later |
| Corrector rewrites meaning | Minimal-edit prompt, diff guard, risk score, preview |
| Translation still stiff | Context + style presets + human eval; optional LoRA |
| 12 GB OOM | 9B Q4, lazy load, 2B fallback, unload idle models |
| Packaging size / AV false positives | One-folder installer, external models, code signing |
| Model licenses | Apache/MIT components; verify Index-Translate weights; NOTICE file |

## 9. Git workflow

- `main` is stable; feature branches `feat/m0-...`, `feat/m1-...`.
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- Tag releases `v0.1.0`; keep model weights out of git.
- GitHub remote requires a repository created by the account owner and a scoped credential;
  local development does not.

