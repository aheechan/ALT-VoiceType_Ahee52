"""Diff guard for ASR correction.

The corrector is allowed to fix recognition errors, not rewrite the speaker.
A simple character edit-distance cap catches the common failure mode where an
LLM "improves" a sentence instead of correcting it.
"""

from __future__ import annotations

from dataclasses import dataclass


def levenshtein(a: str, b: str) -> int:
    """Character-level Levenshtein distance (iterative, O(len(a)*len(b)))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            substitute = previous[j - 1] + (ca != cb)
            current.append(min(insert, delete, substitute))
        previous = current
    return previous[-1]


def edit_ratio(original: str, corrected: str) -> float:
    if not original:
        return 0.0 if not corrected else 1.0
    return levenshtein(original, corrected) / max(1, len(original))


@dataclass
class CorrectionDecision:
    accepted: bool
    ratio: float
    reason: str = ""


def _without_punctuation(text: str) -> str:
    return "".join(ch for ch in text if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def decide(
    original: str,
    corrected: str,
    max_edit_ratio: float = 0.25,
    max_length_ratio: float = 1.8,
) -> CorrectionDecision:
    original = (original or "").strip()
    corrected = (corrected or "").strip()
    if not corrected:
        return CorrectionDecision(False, 1.0, "empty correction")
    if corrected == original:
        return CorrectionDecision(True, 0.0, "")
    # Adding punctuation or changing whitespace is always allowed.
    if _without_punctuation(corrected) == _without_punctuation(original):
        return CorrectionDecision(True, 0.0, "")
    ratio = edit_ratio(original, corrected)
    # Short Chinese utterances have very few characters; a 25% cap would reject
    # a single legitimate homophone fix. Allow at least two character edits.
    max_edits = max(2, int(len(_without_punctuation(original)) * max_edit_ratio))
    if levenshtein(original, corrected) > max_edits:
        return CorrectionDecision(False, ratio, f"edit ratio {ratio:.2f} exceeds limit")
    if len(corrected) > max(1, len(original)) * max_length_ratio:
        return CorrectionDecision(False, ratio, "correction grows the text too much")
    if len(corrected) < len(original) * 0.5:
        return CorrectionDecision(False, ratio, "correction drops too much text")
    return CorrectionDecision(True, ratio, "")
