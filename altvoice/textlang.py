"""Very small text-language detector for the text translator panel."""

from __future__ import annotations

import re

_RANGES = (
    ("ja", r"[\u3040-\u30ff]"),
    ("ko", r"[\uac00-\ud7af]"),
    ("zh", r"[\u4e00-\u9fff]"),
    ("ru", r"[\u0400-\u04ff]"),
    ("ar", r"[\u0600-\u06ff]"),
    ("th", r"[\u0e00-\u0e7f]"),
    ("hi", r"[\u0900-\u097f]"),
)


def detect_language(text: str) -> str:
    value = text or ""
    for code, pattern in _RANGES:
        if re.search(pattern, value):
            return code
    if re.search(r"[A-Za-z]", value):
        return "en"
    return "en"
