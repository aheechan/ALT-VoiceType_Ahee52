import unittest
from pathlib import Path

from altvoice.history import HistoryStore
from tests.helpers import workspace_tempdir


class HistoryTests(unittest.TestCase):
    def test_utterances_and_glossary(self):
        with workspace_tempdir() as tmp:
            path = Path(tmp) / "history.db"
            with HistoryStore(path) as store:
                store.add_utterance("你好", "你好。", "Hello.", "en", "zh")
                store.add_utterance("世界", "世界。", "World.", "en", "zh")
                recent = store.recent(2)
                self.assertEqual([item["corrected"] for item in recent], ["你好。", "世界。"])
                self.assertEqual(recent[-1]["translation"], "World.")
                store.learn_term("碳纤维", "carbon fiber")
                self.assertEqual(store.get_glossary()["碳纤维"], "carbon fiber")
            with HistoryStore(path) as reopened:
                self.assertEqual(len(reopened.recent(10)), 2)
                self.assertEqual(reopened.get_glossary()["碳纤维"], "carbon fiber")
                reopened.clear()
                self.assertEqual(reopened.recent(10), [])
                self.assertEqual(reopened.get_glossary(), {})

    def test_learn_term_ignores_identity(self):
        with workspace_tempdir() as tmp:
            with HistoryStore(Path(tmp) / "h.db") as store:
                store.learn_term("abc", "abc")
                self.assertEqual(store.get_glossary(), {})


if __name__ == "__main__":
    unittest.main()
