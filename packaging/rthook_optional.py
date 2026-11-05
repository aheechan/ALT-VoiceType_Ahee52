"""Runtime stubs for optional Japanese tokenizer dependencies of qwen-asr.

qwen_asr imports its forced-aligner module at package import time, which pulls
nagisa -> a training-only mecab_system_eval dependency. AltVoice does not use
forced alignment, so a small tokenizer stub is enough to let the ASR model load
in the frozen app.
"""

from __future__ import annotations

import os
import sys
import types

# Frozen apps have no source locator for numba's librosa cache. Disabling JIT is
# slower but reliable for the short audio buffers used by dictation.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")


def _install() -> None:
    if "nagisa" not in sys.modules:
        nagisa = types.ModuleType("nagisa")

        def tagging(text):
            return types.SimpleNamespace(words=list(text or ""))

        nagisa.tagging = tagging
        nagisa.wakati = lambda text: list(text or "")
        sys.modules["nagisa"] = nagisa
    if "mecab_system_eval" not in sys.modules:
        sys.modules["mecab_system_eval"] = types.ModuleType("mecab_system_eval")


_install()
