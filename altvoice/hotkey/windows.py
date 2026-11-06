"""Global Alt hook for Windows.

A low-level keyboard hook buffers Alt events so a long press can become
push-to-talk without stealing normal Alt-menu behavior. Short taps are replayed;
Alt+key combinations cancel voice mode and replay the modifier.
"""

from __future__ import annotations

import ctypes
import os
import threading
import time
from ctypes import wintypes

from .logic import AltHookLogic

IS_WINDOWS = os.name == "nt"

WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012
LLKHF_INJECTED = 0x10
ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class HotkeyError(RuntimeError):
    """Raised when the global hook cannot be installed."""


if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    HHOOK = ctypes.c_void_p

    user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
    user32.SetWindowsHookExW.restype = HHOOK
    user32.CallNextHookEx.argtypes = [HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
    user32.CallNextHookEx.restype = ctypes.c_ssize_t
    user32.UnhookWindowsHookEx.argtypes = [HHOOK]
    user32.UnhookWindowsHookEx.restype = wintypes.BOOL
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = wintypes.BOOL
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.TranslateMessage.restype = wintypes.BOOL
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = ctypes.c_ssize_t
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostThreadMessageW.restype = wintypes.BOOL
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD


class WindowsAltHook:
    def __init__(
        self,
        threshold_ms: int = 280,
        mode: str = "toggle_alt",
        combo: str = "alt",
        on_start=None,
        on_stop=None,
        on_cancel=None,
        on_toggle=None,
    ) -> None:
        if not IS_WINDOWS:
            raise HotkeyError("the global Alt hook is only available on Windows")
        self.threshold_ms = max(80, int(threshold_ms))
        self.mode = mode
        self.combo = combo
        self._on_start = on_start or (lambda: None)
        self._on_stop = on_stop or (lambda: None)
        self._on_cancel = on_cancel or (lambda: None)
        self._on_toggle = on_toggle or (lambda: None)
        self._lock = threading.RLock()
        self._combo_logic = None
        if mode == "toggle_alt":
            from .combo import ComboHookLogic, parse_combo

            self._combo_logic = ComboHookLogic(parse_combo(combo), self._toggle_recording)
            self._logic = None
        else:
            self._logic = AltHookLogic(
                threshold_ms=self.threshold_ms,
                mode="long_press",
                on_start=self._start_recording,
                on_stop=self._stop_recording,
                on_cancel=self._cancel_recording,
                replay_alt_tap=self._replay_alt_tap,
                replay_alt_down=self._replay_alt_down,
            )
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._hook = None
        self._ready = threading.Event()
        self._error: str = ""
        self._running = False
        self._timer: threading.Timer | None = None
        self._proc_ref = None

    @property
    def running(self) -> bool:
        return self._running

    def start(self, timeout_s: float = 3.0) -> None:
        if self._running:
            return
        self._thread = threading.Thread(target=self._run, name="altvoice-hotkey", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout_s):
            raise HotkeyError("timed out installing the global Alt hook")
        if self._error:
            raise HotkeyError(self._error)

    def stop(self) -> None:
        self._running = False
        self._cancel_timer()
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._thread = None
        self._thread_id = 0

    def _run(self) -> None:
        try:
            self._thread_id = int(kernel32.GetCurrentThreadId())
            module = kernel32.GetModuleHandleW(None)
            self._proc_ref = HOOKPROC(self._callback)
            self._hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._proc_ref, module, 0)
            if not self._hook:
                error = ctypes.get_last_error()
                self._error = f"SetWindowsHookExW failed (WinError {error})"
                self._ready.set()
                return
            self._running = True
            self._ready.set()
            message = wintypes.MSG()
            while self._running:
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result == 0 or result == -1:
                    break
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        except Exception as exc:  # hook thread must never crash the app
            self._error = f"hotkey thread failed: {exc}"
            self._ready.set()
        finally:
            if self._hook:
                user32.UnhookWindowsHookEx(self._hook)
                self._hook = None
            self._running = False

    def _callback(self, n_code: int, w_param: int, l_param: int) -> int:
        try:
            if n_code == HC_ACTION and w_param in (WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP):
                kb = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                down = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
                injected = bool(kb.flags & LLKHF_INJECTED)
                with self._lock:
                    if self._combo_logic is not None:
                        decision = self._combo_logic.handle_key(
                            int(kb.vkCode), down, injected
                        )
                    else:
                        decision = self._logic.handle_key(
                            int(kb.vkCode),
                            down,
                            injected,
                            time.monotonic() * 1000.0,
                        )
                if self._combo_logic is not None:
                    if decision.suppress:
                        return 1
                else:
                    if decision.start_timer:
                        self._schedule_timer()
                    elif decision.cancel_timer:
                        self._cancel_timer()
                    if decision.suppress:
                        return 1
        except Exception:
            # Never let a Python exception break the user's keyboard.
            pass
        return user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _schedule_timer(self) -> None:
        self._cancel_timer()
        self._timer = threading.Timer(self.threshold_ms / 1000.0, self._on_timer)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self) -> None:
        timer = self._timer
        self._timer = None
        if timer is not None:
            timer.cancel()

    def _on_timer(self) -> None:
        with self._lock:
            if self._logic is not None:
                self._logic.tick(time.monotonic() * 1000.0)

    def _dispatch(self, callback) -> None:
        try:
            callback()
        except Exception:
            pass

    def _toggle_recording(self) -> None:
        self._dispatch(self._on_toggle)

    def _start_recording(self) -> None:
        self._dispatch(self._on_start)

    def _stop_recording(self) -> None:
        self._dispatch(self._on_stop)

    def _cancel_recording(self) -> None:
        self._dispatch(self._on_cancel)

    def _replay_alt_tap(self) -> None:
        from ..inject.windows import send_alt_tap

        self._dispatch(send_alt_tap)

    def _replay_alt_down(self) -> None:
        from ..inject.windows import send_alt_down

        self._dispatch(send_alt_down)
