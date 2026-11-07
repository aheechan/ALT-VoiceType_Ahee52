"""Injection package."""

from __future__ import annotations

import os

from .base import InjectionError, Injector, NullInjector

__all__ = ["InjectionError", "Injector", "NullInjector", "get_injector"]


def get_injector(method: str = "clipboard", restore_clipboard: bool = True):
    """Return a platform injector. Non-Windows falls back to a null injector."""
    if os.name != "nt":
        return NullInjector()
    from .windows import WindowsClipboardInjector, WindowsUnicodeInjector

    if method == "sendinput":
        return WindowsUnicodeInjector()
    return WindowsClipboardInjector(
        restore_clipboard=restore_clipboard,
        method=method,
    )

