"""Minimal OpenAI-compatible chat client using only the standard library."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    """Raised for local LLM transport or response errors."""


def strip_thinking(text: str) -> str:
    """Drop a leading thinking block if a model ignores enable_thinking=False."""
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    text = text.strip()
    if text.startswith("<think>"):
        text = text[len("<think>") :].strip()
    return text


@dataclass
class ChatClient:
    base_url: str
    model: str
    api_key: str = "EMPTY"
    timeout_s: float = 30.0
    enable_thinking: bool = False

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        if self.base_url.endswith("/v1"):
            self._endpoint = self.base_url + "/chat/completions"
        else:
            self._endpoint = self.base_url + "/v1/chat/completions"

    def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.0,
        max_tokens: int = 512,
        retries: int = 1,
        stop: list[str] | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "stream": False,
            "chat_template_kwargs": {"enable_thinking": bool(self.enable_thinking)},
        }
        if stop:
            payload["stop"] = list(stop)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AltVoice/0.1",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_error: Exception | None = None
        for attempt in range(retries + 1):
            request = urllib.request.Request(
                self._endpoint, data=data, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                    body = response.read().decode("utf-8", errors="replace")
                return self._parse_content(body)
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                if 400 <= exc.code < 500:
                    raise LLMError(f"LLM HTTP {exc.code}: {detail}") from exc
                last_error = LLMError(f"LLM HTTP {exc.code}: {detail}")
            except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
                last_error = LLMError(f"LLM connection failed: {exc}")
            if attempt < retries:
                time.sleep(0.4 * (attempt + 1))
        raise last_error or LLMError("LLM request failed")

    @staticmethod
    def _parse_content(body: str) -> str:
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM returned non-JSON: {body[:300]}") from exc
        choices = data.get("choices") or []
        if not choices:
            raise LLMError(f"LLM returned no choices: {body[:300]}")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        if not isinstance(content, str):
            raise LLMError("LLM message.content is not text")
        return strip_thinking(content)
