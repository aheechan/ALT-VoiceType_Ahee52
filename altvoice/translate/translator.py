"""Index-Translate backed translator."""

from __future__ import annotations

from ..config import normalize_language
from ..llm.client import ChatClient, LLMError
from .base import TranslationError, Translator
from .prompts import build_translation_messages, clean_translation


class IndexTranslateTranslator(Translator):
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8092/v1",
        model: str = "Index-Translate-9B",
        api_key: str = "EMPTY",
        timeout_s: float = 45.0,
        max_tokens: int = 384,
    ) -> None:
        self.client = ChatClient(
            base_url=base_url,
            model=model,
            api_key=api_key,
            timeout_s=timeout_s,
        )
        self.max_tokens = int(max_tokens)

    def translate(
        self,
        text: str,
        target_lang: str,
        context: list[dict[str, str]] | None = None,
        style: str = "daily",
        glossary: dict[str, str] | None = None,
        source_lang: str = "zh",
    ) -> str:
        source = (text or "").strip()
        target = normalize_language(target_lang)
        if not source:
            return ""
        if not target or target == normalize_language(source_lang) or target == "zh":
            return source
        messages = build_translation_messages(
            source,
            target,
            context=context,
            style=style,
            glossary=glossary,
            source_lang=source_lang,
        )
        try:
            response = self.client.chat(
                messages,
                temperature=0.0,
                max_tokens=self.max_tokens,
                retries=1,
                stop=["\n原文", "\n译文", "\nTranslation:", "\nSource:"],
            )
        except LLMError as exc:
            raise TranslationError(f"translation failed: {exc}") from exc
        result = clean_translation(response)
        if not result:
            raise TranslationError("translation model returned an empty result")
        return result

    def close(self) -> None:
        return None
