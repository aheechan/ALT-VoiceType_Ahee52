ALT-VoiceType English 0.1.0
===========================

Offline English voice input for Windows.

This package is a separate edition from the Chinese ALT-VoiceType build:

  - Product: ALT-VoiceType English
  - Executable: ALT-VoiceType-EN.exe
  - Data/logs: %APPDATA%\ALT-VoiceType-EN
  - Models: <install directory>\models
  - AppId: separate from the Chinese build

Download all files into one folder:

  ALT-VoiceType-EN-Setup-0.1.0.exe
  ALT-VoiceType-EN-Setup-0.1.0-1.bin
  ALT-VoiceType-EN-Setup-0.1.0-2.bin
  ALT-VoiceType-EN-Setup-0.1.0-3.bin
  SHA256SUMS.txt

Run ALT-VoiceType-EN-Setup-0.1.0.exe. The installer shows a directory chooser.

Fixed models
------------
  ASR:         faster-whisper small.en (English-only, CPU)
  Correction:  Qwen3-1.7B-Abliterated Q4
  Translation: Index-Translate-2B Q4

Runtime
-------
The package includes a CUDA llama.cpp runtime in:

  <install>\llama

It is used for correction and translation. The English ASR itself runs on CPU
through faster-whisper.

Features
--------
- English input by default
- English output by default
- English UI and settings
- 20/45/120 second input tiers
- ESC cancels recording
- 0.39 s recording tail
- Arabic-number normalization
- Copy buttons in the result panels
- Resizable main window
- Local history retention: 7 days / 500 entries

Install size
------------
Download: about 3.57 GB
Installed: about 5.6 GB

Logs
----
%APPDATA%\ALT-VoiceType-EN\logs\app.log
%APPDATA%\ALT-VoiceType-EN\logs\corrector.log
%APPDATA%\ALT-VoiceType-EN\logs\translator.log

The installer is unsigned, so Windows may show "Unknown publisher".
