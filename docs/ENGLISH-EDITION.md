# English edition

The English edition is a separate installer and release. It does not share
AppId, install directory, data directory, logs, or history with the Chinese
edition.

## Files

```text
ALT-VoiceType-EN-Setup-0.1.0.exe
ALT-VoiceType-EN-Setup-0.1.0-1.bin
ALT-VoiceType-EN-Setup-0.1.0-2.bin
ALT-VoiceType-EN-Setup-0.1.0-3.bin
SHA256SUMS.txt
README-EN.txt
```

## GitHub release

Create a separate release tag:

```text
v0.1.0-en
```

Upload the six files above as release assets. Do not commit them to Git.

## Runtime

```text
Product: ALT-VoiceType English
Executable: ALT-VoiceType-EN.exe
Data: %APPDATA%\ALT-VoiceType-EN
Models: <install>\models
ASR: faster-whisper small.en (English-only, CPU)
Correction/translation: bundled CUDA llama.cpp
```

The Chinese release remains `v0.1.0-zh` / `ALT-VoiceType-Setup-0.1.0`.
