"""Testable Alt hook decision logic, independent of Win32."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .gesture import Action, AltGestureDetector, KeyEvent

ALT_VKS = {0x12, 0xA4, 0xA5}  # VK_MENU, VK_LMENU, VK_RMENU


@dataclass
class HookDecision:
    suppress: bool = False
    start_timer: bool = False
    cancel_timer: bool = False


class AltHookLogic:
    """Translate key events into hook suppression and callbacks.

    The real hook passes every low-level event here. Injected events (our own
    Alt replay) are never suppressed, otherwise a short tap would disappear.
    """

    def __init__(
        self,
        threshold_ms: int = 280,
        replay_short_tap: bool = True,
        mode: str = "long_press",
        on_start: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        replay_alt_tap: Callable[[], None] | None = None,
        replay_alt_down: Callable[[], None] | None = None,
    ) -> None:
        self.mode = mode if mode in {"long_press", "toggle"} else "long_press"
        self.detector = AltGestureDetector(
            threshold_ms,
            replay_short_tap=replay_short_tap,
            mode=self.mode,
        )
        self.on_start = on_start or (lambda: None)
        self.on_stop = on_stop or (lambda: None)
        self.on_cancel = on_cancel or (lambda: None)
        self.replay_alt_tap = replay_alt_tap or (lambda: None)
        self.replay_alt_down = replay_alt_down or (lambda: None)
        self._pending_timer = False

    @property
    def state(self) -> str:
        return self.detector.state

    def handle_key(
        self,
        vk: int,
        down: bool,
        injected: bool,
        now_ms: float,
    ) -> HookDecision:
        if injected:
            return HookDecision()
        if vk in ALT_VKS:
            was_idle = self.detector.state == "idle"
            actions = self.detector.feed(KeyEvent("alt", down, now_ms))
            decision = HookDecision(suppress=True)
            if self.mode == "long_press" and down:
                if was_idle:
                    decision.start_timer = True
                    self._pending_timer = True
            elif self.mode == "long_press":
                decision.cancel_timer = True
                self._pending_timer = False
            self._dispatch(actions)
            return decision

        actions = self.detector.feed(KeyEvent("other", down, now_ms))
        decision = HookDecision(suppress=False, cancel_timer=self._pending_timer)
        self._pending_timer = False
        self._dispatch(actions)
        return decision

    def tick(self, now_ms: float) -> list[Action]:
        actions = self.detector.tick(now_ms)
        self._pending_timer = self.detector.state == "pending"
        self._dispatch(actions)
        return actions

    def _dispatch(self, actions: list[Action]) -> None:
        for action in actions:
            if action is Action.START_RECORDING:
                self.on_start()
            elif action is Action.STOP_RECORDING:
                self.on_stop()
            elif action is Action.CANCEL:
                self.on_cancel()
            elif action is Action.REPLAY_ALT_TAP:
                self.replay_alt_tap()
            elif action is Action.REPLAY_ALT_DOWN:
                self.replay_alt_down()

    def reset(self) -> None:
        self.detector.reset()
        self._pending_timer = False

