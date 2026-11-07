"""Local conversation context and glossary."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Utterance:
    source: str
    corrected: str
    translation: str = ""
    app: str = ""
    scene: str = "daily"
    timestamp: float = 0.0


@dataclass
class ContextStore:
    max_utterances: int = 10
    glossary: dict[str, str] = field(default_factory=dict)
    app: str = ""
    scene: str = "daily"
    _utterances: deque[Utterance] = field(default_factory=lambda: deque(maxlen=10))

    def __post_init__(self) -> None:
        self._utterances = deque(self._utterances, maxlen=self.max_utterances)

    def add(
        self,
        source: str,
        corrected: str,
        translation: str = "",
        app: str | None = None,
        scene: str | None = None,
        timestamp: float = 0.0,
    ) -> None:
        self._utterances.append(
            Utterance(
                source=source,
                corrected=corrected,
                translation=translation,
                app=app if app is not None else self.app,
                scene=scene if scene is not None else self.scene,
                timestamp=timestamp,
            )
        )

    def recent(self, n: int = 5) -> list[dict[str, str]]:
        items = list(self._utterances)[-n:]
        return [
            {
                "source": u.source,
                "corrected": u.corrected,
                "translation": u.translation,
                "app": u.app,
                "scene": u.scene,
            }
            for u in items
        ]

    def set_glossary(self, glossary: dict[str, str]) -> None:
        self.glossary = {str(k): str(v) for k, v in glossary.items() if k}

    def learn_term(self, source: str, target: str) -> None:
        source = (source or "").strip()
        target = (target or "").strip()
        if source and target and source != target:
            self.glossary[source] = target

    def clear(self) -> None:
        self._utterances.clear()

    def __len__(self) -> int:
        return len(self._utterances)

