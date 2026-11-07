"""Module entry point, also used by the PyInstaller windowed build."""

from __future__ import annotations

import os
import sys
import tempfile


def _ensure_streams() -> None:
    """Windowed executables have no stdout/stderr; give print() somewhere to go."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    try:
        handle = open(
            os.path.join(tempfile.gettempdir(), "altvoice-boot.log"),
            "a",
            encoding="utf-8",
        )
    except OSError:
        handle = open(os.devnull, "w", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = handle
    if sys.stderr is None:
        sys.stderr = handle


_ensure_streams()

from altvoice.cli import main  # noqa: E402

raise SystemExit(main())

