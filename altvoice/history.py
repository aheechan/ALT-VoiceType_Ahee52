"""SQLite history and glossary persistence.

The in-memory ContextStore is enough for a single dictation session. This store
keeps recent utterances and user terminology across restarts so the corrector
and translator can carry context, names and preferences forward. It is local
only and can be disabled in config.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from .config import default_config_dir


def default_history_path() -> Path:
    return default_config_dir() / "history.db"


class HistoryStore:
    def __init__(
        self,
        path: str | Path | None = None,
        retention_days: int = 7,
        max_entries: int = 500,
    ) -> None:
        self.path = Path(path) if path else default_history_path()
        self.retention_days = max(1, int(retention_days))
        self.max_entries = max(50, int(max_entries))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self.prune()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS utterances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    app TEXT NOT NULL DEFAULT '',
                    scene TEXT NOT NULL DEFAULT 'daily',
                    source TEXT NOT NULL,
                    corrected TEXT NOT NULL,
                    translation TEXT NOT NULL DEFAULT '',
                    target_lang TEXT NOT NULL DEFAULT '',
                    source_lang TEXT NOT NULL DEFAULT 'zh'
                );
                CREATE INDEX IF NOT EXISTS idx_utterances_ts ON utterances(ts);
                CREATE TABLE IF NOT EXISTS glossary (
                    source TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    updated REAL NOT NULL
                );
                """
            )

    def add_utterance(
        self,
        source: str,
        corrected: str,
        translation: str = "",
        target_lang: str = "",
        source_lang: str = "zh",
        app: str = "",
        scene: str = "daily",
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO utterances "
                "(ts, app, scene, source, corrected, translation, target_lang, source_lang) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    time.time(),
                    app or "",
                    scene or "daily",
                    source or "",
                    corrected or "",
                    translation or "",
                    target_lang or "",
                    source_lang or "zh",
                ),
            )
        self.prune()

    def recent(self, n: int = 5, app: str | None = None) -> list[dict[str, str]]:
        n = max(1, min(100, int(n)))
        with self._lock:
            if app:
                rows = self._conn.execute(
                    "SELECT * FROM utterances WHERE app = ? ORDER BY id DESC LIMIT ?",
                    (app, n),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM utterances ORDER BY id DESC LIMIT ?", (n,)
                ).fetchall()
        return [
            {
                "source": row["source"],
                "corrected": row["corrected"],
                "translation": row["translation"],
                "app": row["app"],
                "scene": row["scene"],
                "target_lang": row["target_lang"],
            }
            for row in reversed(rows)
        ]

    def set_glossary(self, glossary: dict[str, str]) -> None:
        now = time.time()
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM glossary")
            self._conn.executemany(
                "INSERT INTO glossary (source, target, updated) VALUES (?, ?, ?)",
                [(str(k).strip(), str(v).strip(), now) for k, v in glossary.items() if str(k).strip()],
            )

    def get_glossary(self) -> dict[str, str]:
        with self._lock:
            rows = self._conn.execute("SELECT source, target FROM glossary").fetchall()
        return {row["source"]: row["target"] for row in rows}

    def learn_term(self, source: str, target: str) -> None:
        source = (source or "").strip()
        target = (target or "").strip()
        if not source or not target or source == target:
            return
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO glossary (source, target, updated) VALUES (?, ?, ?) "
                "ON CONFLICT(source) DO UPDATE SET target=excluded.target, updated=excluded.updated",
                (source, target, time.time()),
            )

    def prune(self) -> None:
        """Keep only recent, bounded utterance rows."""
        cutoff = time.time() - self.retention_days * 86400
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM utterances WHERE ts < ?", (cutoff,))
            self._conn.execute(
                "DELETE FROM utterances WHERE id NOT IN "
                "(SELECT id FROM utterances ORDER BY id DESC LIMIT ?)",
                (self.max_entries,),
            )

    def clear(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM utterances")
            self._conn.execute("DELETE FROM glossary")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def __enter__(self) -> "HistoryStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

