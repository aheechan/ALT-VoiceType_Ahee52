# Architecture

## 1. Runtime view

```text
┌──────────────────────────────────────────────────────────────────┐
│ PySide6 tray / overlay / settings                                │
│  - target language, mode, scene, history, model status           │
└───────────────▲───────────────────────────────┬──────────────────┘
                │ Qt signals                    │ commands
┌───────────────┴───────────────────────────────▼──────────────────┐
│ VoicePipeline                                                     │
│  capture -> VAD -> ASR -> correct -> translate -> inject         │
│  owns ContextStore, glossary, cancellation token                  │
└───────┬───────────────┬──────────────────┬───────────────┬───────┘
        │               │                  │               │
┌───────▼──────┐ ┌──────▼───────┐ ┌────────▼──────┐ ┌──────▼──────┐
│ audio        │ │ ASR engine   │ │ corrector     │ │ translator  │
│ sounddevice  │ │ FireRed /    │ │ Qwen3 + guard │ │ Index-      │
│ WAV / VAD    │ │ Qwen3 / sherpa│ │               │ │ Translate   │
└──────────────┘ └──────────────┘ └───────────────┘ └─────────────┘
        │               │                  │               │
        └───────────────┴──────────┬───────┴───────────────┘
                                   │
                         ┌─────────▼──────────┐
                         │ local model files   │
                         │ %LOCALAPPDATA%/...  │
                         └────────────────────┘
```

The MVP runs in one process for simplicity, with each heavy engine behind an adapter. If a model
crashes or leaks VRAM, the adapter can be moved to a worker process later without changing the
pipeline API.

## 2. Threading and latency

- UI thread: tray, overlay, settings only.
- Capture thread: `sounddevice` callback appends 20 ms frames to a queue.
- Worker thread: VAD/trim → ASR → correct → translate → inject.
- One utterance at a time; a new `Alt` press cancels the previous job.
- Model loading is lazy and guarded by a lock. Loading shows a tray status.
- Target: 5 s speech → text inserted in ≤2 s on RTX 3070.

## 3. Model lifecycle

- `ModelManager` reads the active profile from `config.json`.
- `ensure(role)` loads the configured model if not resident; `release(role)` frees it.
- On CUDA OOM: unload the translator, retry with the 2B model if configured; otherwise surface a
  clear tray error.
- Idle unload after 5 minutes is configurable. ASR stays resident during a session.

## 4. Context model

`ContextStore` is a per-app ring buffer:

```json
{
  "app": "WeChat",
  "scene": "chat",
  "utterances": [
    {"source": "...", "corrected": "...", "translation": "...", "ts": 0}
  ],
  "glossary": {"碳纤维": "carbon fiber"}
}
```

- Short-term: last 10 utterances, used by the corrector and translator.
- Long-term: glossary, names, product terms, style preference.
- Persistence: optional SQLite history; default local, no network.
- Privacy: raw audio is never persisted by default; history can be disabled or encrypted.

## 5. ASR adapters

| Adapter | Package | Input | Notes |
|---|---|---|---|
| `qwen3` | `qwen-asr` | path / ndarray | **Windows default**, 0.6B/1.7B, streaming, 22 dialects |
| `firered` | `fireredasr2s` / FireRedASR2S repo | 16 kHz WAV | optional quality engine, 1.1B AED, up to 60 s, GPU |
| `sherpa` | `sherpa-onnx` | 16 kHz samples | CPU fallback, SenseVoice/Paraformer |
| `none` | — | — | tests and dry runs |

Every adapter returns `ASRResult(text, language, confidence, latency_ms, raw)`. Adapters must not
raise on missing optional dependencies at import time; they raise `EngineUnavailable` on `load()`.

## 6. Correction and translation

Both use an OpenAI-compatible local endpoint (llama.cpp server, vLLM, or SGLang). This keeps the
pipeline independent of the inference runtime and makes it easy to test with a fake HTTP server.

- `LLMCorrector`: builds a strict JSON prompt, calls the endpoint at temperature 0, parses
  `{text, edits, risk}`, and applies a diff guard.
- `IndexTranslateTranslator`: builds a whole-utterance prompt with context and style, calls the
  endpoint, strips thinking blocks, and returns plain text.
- `OpenAICompatClient`: stdlib `urllib`, timeout, optional API key, no retries on 4xx, one retry
  on 5xx/timeout.

## 7. Injection

`WindowsClipboardInjector`:

1. Read and remember the current text clipboard (if any).
2. Set the clipboard to the result.
3. Send `Ctrl+V` via `SendInput`.
4. Restore the previous clipboard after a short delay or on next injection.

`WindowsUnicodeInjector` sends `KEYEVENTF_UNICODE` characters directly for apps where clipboard
paste is undesirable. Both fail closed with `InjectionError`; the caller shows the preview so the
user can copy manually.

## 8. Packaging

- PyInstaller one-folder; Qt plugins and model downloader included.
- Models live under `%LOCALAPPDATA%\ALT-VoiceType\models`, not in the installer.
- Inno Setup creates Start Menu/desktop shortcuts and optional autostart.
- Code signing is recommended to reduce SmartScreen/AV false positives from the keyboard hook.
- The app never downloads code at runtime; model files are verified by SHA256 from a manifest.
