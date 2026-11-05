"""Windows clipboard and SendInput text injection.

The clipboard path is the default because it works in the widest range of
applications. SendInput Unicode is a fallback for apps where clipboard paste is
undesirable. Both are deliberately small, fail-closed primitives; a real TSF
IME comes later.
"""

from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes

from .base import InjectionError, Injector

IS_WINDOWS = os.name == "nt"

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_RETURN = 0x0D
VK_V = 0x56

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
    user32.SendInput.restype = wintypes.UINT
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.restype = wintypes.HGLOBAL


def _require_windows() -> None:
    if not IS_WINDOWS:
        raise InjectionError("Windows text injection is only available on Windows")


def _open_clipboard(retries: int = 8) -> bool:
    for _ in range(retries):
        if user32.OpenClipboard(None):
            return True
        time.sleep(0.02)
    return False


def get_foreground_window() -> int:
    _require_windows()
    return int(user32.GetForegroundWindow() or 0)


def set_foreground_window(hwnd: int) -> bool:
    _require_windows()
    if not hwnd:
        return False
    return bool(user32.SetForegroundWindow(int(hwnd)))


def get_clipboard_text() -> str | None:
    _require_windows()
    if not _open_clipboard():
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return None
        try:
            return ctypes.wstring_at(pointer)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text: str) -> None:
    _require_windows()
    data = (text or "").encode("utf-16-le") + b"\x00\x00"
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        raise InjectionError("GlobalAlloc failed for clipboard data")
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        kernel32.GlobalFree(handle)
        raise InjectionError("GlobalLock failed for clipboard data")
    try:
        ctypes.memmove(pointer, data, len(data))
    finally:
        kernel32.GlobalUnlock(handle)
    if not _open_clipboard():
        kernel32.GlobalFree(handle)
        raise InjectionError("cannot open clipboard (another application may hold it)")
    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            kernel32.GlobalFree(handle)
            raise InjectionError("SetClipboardData failed")
        # The system owns the handle after a successful SetClipboardData.
    finally:
        user32.CloseClipboard()


def _send_input(inputs: list[INPUT]) -> None:
    _require_windows()
    array = (INPUT * len(inputs))(*inputs)
    sent = user32.SendInput(len(inputs), array, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise InjectionError(f"SendInput sent {sent}/{len(inputs)} events")


def _key_event(vk: int, up: bool = False) -> INPUT:
    item = INPUT(type=INPUT_KEYBOARD)
    item.u.ki.wVk = vk
    item.u.ki.wScan = 0
    item.u.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
    item.u.ki.time = 0
    item.u.ki.dwExtraInfo = 0
    return item


def send_ctrl_v() -> None:
    _send_input(
        [
            _key_event(VK_CONTROL),
            _key_event(VK_V),
            _key_event(VK_V, up=True),
            _key_event(VK_CONTROL, up=True),
        ]
    )


def send_alt_down() -> None:
    _send_input([_key_event(VK_MENU)])


def send_alt_up() -> None:
    _send_input([_key_event(VK_MENU, up=True)])


def send_alt_tap() -> None:
    send_alt_down()
    time.sleep(0.03)
    send_alt_up()


def _unicode_event(unit: int, up: bool = False) -> INPUT:
    item = INPUT(type=INPUT_KEYBOARD)
    item.u.ki.wVk = 0
    item.u.ki.wScan = unit
    item.u.ki.dwFlags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if up else 0)
    item.u.ki.time = 0
    item.u.ki.dwExtraInfo = 0
    return item


def send_unicode_text(text: str) -> None:
    """Send arbitrary Unicode via KEYEVENTF_UNICODE, one UTF-16 unit at a time."""
    _require_windows()
    encoded = text.encode("utf-16-le")
    units = [int.from_bytes(encoded[i : i + 2], "little") for i in range(0, len(encoded), 2)]
    for unit in units:
        if unit in (0x0A, 0x0D):
            _send_input([_key_event(VK_RETURN), _key_event(VK_RETURN, up=True)])
        else:
            _send_input([_unicode_event(unit), _unicode_event(unit, up=True)])


class WindowsClipboardInjector(Injector):
    def __init__(
        self,
        restore_clipboard: bool = True,
        paste_delay_ms: int = 80,
        method: str = "clipboard",
    ) -> None:
        self.restore_clipboard = bool(restore_clipboard)
        self.paste_delay_s = max(0, int(paste_delay_ms)) / 1000.0
        self.method = method

    def inject(self, text: str) -> None:
        _require_windows()
        text = text or ""
        if not text:
            return
        if self.method == "sendinput":
            send_unicode_text(text)
            return
        if self.method == "copy":
            set_clipboard_text(text)
            return

        previous = get_clipboard_text() if self.restore_clipboard else None
        set_clipboard_text(text)
        try:
            time.sleep(self.paste_delay_s)
            send_ctrl_v()
            # Give the target application time to read the clipboard before restoring.
            time.sleep(0.25 if self.restore_clipboard else 0.05)
        finally:
            if self.restore_clipboard and previous is not None:
                try:
                    set_clipboard_text(previous)
                except InjectionError:
                    pass


class WindowsUnicodeInjector(Injector):
    def inject(self, text: str) -> None:
        send_unicode_text(text)
