# Interaction design (v0.1)

## Alt gesture

Default: **long-press left Alt for 280 ms** to start, release to finish.

- Short tap: replayed to the application, so normal Alt menu behavior is preserved.
- Alt+Tab / Alt+F4: if another key is pressed before the threshold, cancel voice mode and replay
  the original Alt down event so the combination works.
- Configurable alternatives: right Alt, double-tap Alt, `Ctrl+Alt+Space`.
- `Esc` cancels an in-flight recording or pending insertion.
- Audio cue on start/stop; tray icon turns red; a small waveform overlay appears.

This gesture needs dedicated testing for stuck modifiers and menu flicker. It is a P0 risk.

## Tray menu

```text
ALT-VoiceType
  ● 中文 (Chinese)
  ○ English
  ○ 日本語
  ○ 한국어
  ○ Español
  ○ Français
  ○ Deutsch
  ---
  Mode: Translate
  Scene: Daily
  ---
  Preview before insert   [on]
  History                 [on]
  Settings...
  Quit
```

Left-click the tray icon: start/stop recording. Right-click: menu above. The tray tooltip shows
the active profile and model status (`ASR ready`, `Translator loading`, `OOM: using 2B`).

## Preview bubble

```text
┌──────────────────────────────────────────────┐
│ 原文  我们今天下午三点开会，别迟到。          │
│ 译文  Let's meet at 3 p.m. today — don't be late. │
│                                              │
│ Enter 插入   Tab 切换   Esc 取消   Ctrl+Z 撤销 │
└──────────────────────────────────────────────┘
```

- Default: show preview for the first N days / until the user trusts the setup; then allow
  "direct insert" mode.
- Low-confidence ASR or high-risk correction: always preview.
- User edits are captured as glossary candidates.
- The bubble is frameless, always-on-top, positioned near the caret or the tray.

## Modes

- **Transcribe:** insert corrected Chinese text.
- **Translate:** insert the target-language translation; Chinese target skips translation.
- **Copy only:** put the result on the clipboard, no injection.
- **Preview:** show the bubble and wait for confirmation.

## Scenes / styles

| Scene | Translation style |
|---|---|
| Daily | colloquial, natural, keep interjections |
| Live / streaming | energetic, short, spoken rhythm |
| Business | polite, concise, professional but not stiff |
| Game | character voice, slang, short lines |
| Subtitle | compact, readable, preserve meaning over literal wording |

## Error states

- **No microphone:** tray notification + settings link.
- **ASR model missing:** show model manager with the required download.
- **OOM:** automatically unload the translator; retry with 2B if configured; explain in tray.
- **Injection blocked:** keep the preview open and copy to clipboard; suggest running as admin or
  using clipboard mode.
- **Network:** never required at runtime; model downloads are explicit and resumable.

