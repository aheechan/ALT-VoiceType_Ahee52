"""Test helpers that keep temporary files inside the workspace."""

from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def workspace_tempdir():
    base = Path(__file__).resolve().parent / "_tmp"
    base.mkdir(parents=True, exist_ok=True)
    # Do not use tempfile.mkdtemp here: on Windows it creates a mode-0700
    # directory that the harness sandbox cannot write into. mkdir inherits the
    # workspace ACL instead.
    path = base / f"tmp_{uuid.uuid4().hex[:10]}"
    path.mkdir(parents=False, exist_ok=False)
    try:
        yield str(path)
    finally:
        shutil.rmtree(path, ignore_errors=True)
