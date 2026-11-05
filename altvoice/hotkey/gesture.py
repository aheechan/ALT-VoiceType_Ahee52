"""Pure Alt gesture state machine.

The Windows hook is intentionally thin: all timing and suppression decisions
live here so they can be tested without a keyboard or a message loop.

States:
    IDLE -> (Alt down) -> PENDING -> (threshold) -> RECORDING -> (Alt up) -> IDLE
                           |                          |
                           +-- (Alt up, short) ------> REPLAY_ALT_TAP
                           +-- (other key) ----------> CANCEL + REPLAY_ALT_DOWN
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Action(str, Enum):
    START_RECORDING = "start_recording"
    STOP_RECORDING = "stop_recording"
    REPLAY_ALT_TAP = "replay_alt_tap"
    REPLAY_ALT_DOWN = "replay_alt_down"
    CANCEL = "cancel"


@dataclass(frozen=True)
class KeyEvent:
    key: str
    down: bool
    timestamp_ms: float


def _is_alt(key: str) -> bool:
    return key.lower() in {"alt", "lalt", "ralt", "altgr", "menu"}


class AltGestureDetector:
    def __init__(
        self,
        threshold_ms: int = 280,
        replay_short_tap: bool = True,
        mode: str = "long_press",
    ) -> None:
        self.threshold_ms = max(80, int(threshold_ms))
        self.replay_short_tap = bool(replay_short_tap)
        self.mode = mode if mode in {"long_press", "toggle"} else "long_press"
        self._state = "idle"
        self._alt_down_at = 0.0

    @property
    def state(self) -> str:
        return self._state

    def feed(self, event: KeyEvent) -> list[Action]:
        actions: list[Action] = []
        if _is_alt(event.key):
            if self.mode == "toggle":
                if event.down:
                    if self._state == "idle":
                        self._state = "recording"
                        actions.append(Action.START_RECORDING)
                    elif self._state == "recording":
                        self._state = "idle"
                        actions.append(Action.STOP_RECORDING)
                return actions
            if event.down:
                if self._state == "idle":
                    self._state = "pending"
                    self._alt_down_at = event.timestamp_ms
                # Auto-repeat while pending is ignored.
                return actions
            # Alt up
            if self._state == "pending":
                self._state = "idle"
                if self.replay_short_tap:
                    actions.append(Action.REPLAY_ALT_TAP)
            elif self._state == "recording":
                self._state = "idle"
                actions.append(Action.STOP_RECORDING)
            return actions

        # A non-Alt key.
        if self._state == "pending":
            self._state = "idle"
            actions.append(Action.CANCEL)
            actions.append(Action.REPLAY_ALT_DOWN)
        elif self._state == "recording":
            self._state = "idle"
            actions.append(Action.CANCEL)
        return actions

    def tick(self, now_ms: float) -> list[Action]:
        if self.mode == "long_press" and self._state == "pending" and now_ms - self._alt_down_at >= self.threshold_ms:
            self._state = "recording"
            return [Action.START_RECORDING]
        return []

    def reset(self) -> None:
        self._state = "idle"
        self._alt_down_at = 0.0
