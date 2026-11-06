"""Parse and detect user-configured Alt hotkey chords."""

from __future__ import annotations

from dataclasses import dataclass

MODIFIER_VKS = {
    "lalt": {0xA4},
    "ralt": {0xA5},
    "alt": {0x12, 0xA4, 0xA5},
    "ctrl": {0x11, 0xA2, 0xA3},
    "shift": {0x10, 0xA0, 0xA1},
    "win": {0x5B, 0x5C},
}
MODIFIER_ORDER = ["lalt", "ralt", "alt", "ctrl", "shift", "win"]
NAMED_VKS = {
    "space": 0x20,
    "tab": 0x09,
    "enter": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}
for _i in range(1, 13):
    NAMED_VKS[f"f{_i}"] = 0x6F + _i
for _ch in "abcdefghijklmnopqrstuvwxyz":
    NAMED_VKS[_ch] = ord(_ch.upper())
for _ch in "0123456789":
    NAMED_VKS[_ch] = ord(_ch)


@dataclass(frozen=True)
class HotkeyCombo:
    text: str
    modifiers: frozenset[str]
    key: str
    vks: frozenset[int]
    groups: tuple[frozenset[int], ...] = ()


def parse_combo(text: str) -> HotkeyCombo:
    raw = (text or "").strip().lower().replace(" ", "")
    if not raw:
        raise ValueError("快捷键不能为空")
    parts = [part for part in raw.split("+") if part]
    modifiers: set[str] = set()
    key = ""
    for part in parts:
        if part in MODIFIER_VKS:
            modifiers.add(part)
        elif part in NAMED_VKS:
            if key:
                raise ValueError("只能设置一个主按键")
            key = part
        else:
            raise ValueError(f"不支持的按键：{part}")
    if "alt" not in modifiers and not ({"lalt", "ralt"} & modifiers):
        raise ValueError("快捷键必须包含左 Alt 或右 Alt")
    vks: set[int] = set()
    groups: list[frozenset[int]] = []
    for modifier in modifiers:
        group = frozenset(MODIFIER_VKS[modifier])
        groups.append(group)
        vks.update(group)
    if key:
        group = frozenset({NAMED_VKS[key]})
        groups.append(group)
        vks.update(group)
    canonical = "+".join([*sorted(modifiers, key=lambda m: MODIFIER_ORDER.index(m)), *([key] if key else [])])
    return HotkeyCombo(canonical, frozenset(modifiers), key, frozenset(vks), tuple(groups))


@dataclass
class ComboDecision:
    suppress: bool = False
    triggered: bool = False


class ComboHookLogic:
    """Toggle once when the full chord is pressed.

    Alt keys are never swallowed: system shortcuts such as Alt+Tab keep
    working. Only the non-Alt main key of a chord is suppressed when it
    actually fires the recorder.
    """

    def __init__(self, combo: HotkeyCombo, on_toggle) -> None:
        self.combo = combo
        self.on_toggle = on_toggle
        self._pressed: set[int] = set()
        self._triggered = False
        self._main_vks = {NAMED_VKS[combo.key]} if combo.key else set()
        if "alt" in combo.modifiers:
            self._alt_keys = set(MODIFIER_VKS["alt"])
        elif "lalt" in combo.modifiers:
            self._alt_keys = set(MODIFIER_VKS["lalt"])
        elif "ralt" in combo.modifiers:
            self._alt_keys = set(MODIFIER_VKS["ralt"])
        else:
            self._alt_keys = set()

    def handle_key(self, vk: int, down: bool, injected: bool) -> ComboDecision:
        if injected:
            return ComboDecision()
        if vk not in self.combo.vks:
            return ComboDecision()
        alt_down = any(v in self._pressed for v in self._alt_keys)
        if not alt_down and not self._triggered and vk not in self._alt_keys:
            # A main key or secondary modifier pressed on its own should pass
            # through normally; only the Alt chord is ours.
            return ComboDecision()
        if down:
            self._pressed.add(vk)
            fired = False
            complete = all(any(v in self._pressed for v in group) for group in self.combo.groups)
            if not self._triggered and complete:
                self._triggered = True
                fired = True
                self.on_toggle()
            return ComboDecision(suppress=vk in self._main_vks, triggered=fired)
        self._pressed.discard(vk)
        if not (self.combo.vks & self._pressed):
            self._triggered = False
        return ComboDecision(suppress=vk in self._main_vks and self._triggered)
