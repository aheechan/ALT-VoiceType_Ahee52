"""Single-instance guard for the tray application."""

from __future__ import annotations

import ctypes
import os

ERROR_ALREADY_EXISTS = 183


class SingleInstance:
    """A session-local named mutex on Windows; a lock file elsewhere."""

    def __init__(self, name: str = "Local\\ALT-VoiceType-SingleInstance") -> None:
        self.name = name
        self.acquired = False
        self._handle = None
        self._file = None
        if os.name == "nt":
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
            kernel32.CreateMutexW.restype = ctypes.c_void_p
            kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel32.CloseHandle.restype = ctypes.c_bool
            self._kernel32 = kernel32
            handle = kernel32.CreateMutexW(None, False, name)
            if not handle:
                raise OSError("CreateMutexW failed")
            if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
                kernel32.CloseHandle(handle)
                self.acquired = False
            else:
                self._handle = handle
                self.acquired = True
        else:
            import fcntl
            import tempfile

            path = os.path.join(tempfile.gettempdir(), "altvoice.lock")
            self._file = open(path, "w")
            try:
                fcntl.flock(self._file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.acquired = True
            except OSError:
                self.acquired = False

    def close(self) -> None:
        if self._handle is not None:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None
        if self._file is not None:
            self._file.close()
            self._file = None
        self.acquired = False

    def __enter__(self) -> "SingleInstance":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

