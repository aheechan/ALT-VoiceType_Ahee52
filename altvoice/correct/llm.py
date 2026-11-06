"""LLM-backed Chinese ASR correction."""

from __future__ import annotations

from ..llm.client import ChatClient, LLMError
from .base import CorrectionResult, Corrector
from .guard import decide
from .prompts import build_correction_messages, parse_correction_response


class LLMCorrector(Corrector):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8091/v1",
        model: str = "qwen3-1.7b-instruct",
        api_key: str = "EMPTY",
        timeout_s: float = 20.0,
        max_edit_ratio: float = 0.25,
        max_tokens: int = 512,
    ) -> None:
        self.client = ChatClient(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_s=timeout_s,
        )
        self.max_edit_ratio = float(max_edit_ratio)
        self.max_tokens = int(max_tokens)

    def correct(
        self,
        text: str,
        context: list[dict[str, str]] | None = None,
        glossary: dict[str, str] | None = None,
        scene: str = "daily",
    ) -> CorrectionResult:
        original = (text or "").strip()
        if not original:
            return CorrectionResult(text="", raw_text="", accepted=True)
        messages = build_correction_messages(original, context, glossary, scene)
        try:
            response = self.client.chat(
                messages,
                temperature=0.0,
                max_tokens=self.max_tokens,
                retries=1,
            )
        except LLMError as exc:
            # Fail open: a correction outage must not block dictation.
            return CorrectionResult(
                text=original,
                raw_text=original,
                risk=1.0,
                accepted=False,
                reason=f"corrector unavailable: {exc}",
            )

        parsed = parse_correction_response(response, original)
        candidate = parsed["text"]
        decision = decide(original, candidate, max_edit_ratio=self.max_edit_ratio)
        if not decision.accepted:
            return CorrectionResult(
                text=original,
                raw_text=original,
                risk=max(parsed.get("risk", 0.0), 0.5),
                accepted=False,
                reason=decision.reason,
                edits=parsed.get("edits", []),
            )
        return CorrectionResult(
            text=candidate,
            raw_text=original,
            risk=float(parsed.get("risk", 0.0)),
            accepted=True,
            reason="",
            edits=parsed.get("edits", []),
        )

    def close(self) -> None:
        return None
