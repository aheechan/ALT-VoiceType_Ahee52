"""Text injection interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod


class InjectionError(RuntimeError):
    """Raised when text cannot be inserted into the focused application."""


class Injector(ABC):
    @abstractmethod
    def inject(self, text: str) -> None:
        """Insert text into the focused control."""


class NullInjector(Injector):
    """Records text instead of injecting it; useful for tests and dry runs."""

    def __init__(self) -> None:
        self.last_text = ""

    def inject(self, text: str) -> None:
        self.last_text = text

