import unittest

from altvoice.correct.guard import decide, edit_ratio, levenshtein
from altvoice.correct.prompts import build_correction_messages, parse_correction_response
from altvoice.translate.prompts import build_translation_messages, clean_translation


class GuardTests(unittest.TestCase):
    def test_levenshtein(self):
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("abc", ""), 3)
        self.assertEqual(levenshtein("你好", "你好"), 0)
        self.assertEqual(levenshtein("你好", "你号"), 1)

    def test_edit_ratio(self):
        self.assertEqual(edit_ratio("你好", "你好"), 0.0)
        self.assertAlmostEqual(edit_ratio("你好", "你号"), 0.5)

    def test_punctuation_only_is_allowed(self):
        decision = decide("你好世界", "你好，世界。")
        self.assertTrue(decision.accepted)

    def test_short_homophone_fix_is_allowed(self):
        decision = decide("你好", "您好")
        self.assertTrue(decision.accepted)

    def test_large_rewrite_is_rejected(self):
        decision = decide("今天下午三点开会", "明天上午十点我们讨论一下项目计划")
        self.assertFalse(decision.accepted)

    def test_empty_correction_is_rejected(self):
        self.assertFalse(decide("你好", "").accepted)


class PromptTests(unittest.TestCase):
    def test_correction_prompt_contains_context_and_glossary(self):
        messages = build_correction_messages(
            "王平中采用了碳纤维。",
            context=[{"source": "王平中", "corrected": "王平仲"}],
            glossary={"碳纤维": "carbon fiber"},
            scene="chat",
        )
        text = "\n".join(m["content"] for m in messages)
        self.assertIn("王平仲", text)
        self.assertIn("碳纤维", text)
        self.assertIn("JSON", text)
        self.assertIn("chat", text)

    def test_parse_fenced_json(self):
        response = '```json\n{"text":"你好，世界。","risk":0.1,"edits":[]}\n```'
        parsed = parse_correction_response(response, "你好世界")
        self.assertEqual(parsed["text"], "你好，世界。")
        self.assertFalse(parsed["parse_error"])
        self.assertAlmostEqual(parsed["risk"], 0.1)

    def test_parse_broken_json_falls_back(self):
        parsed = parse_correction_response("not json", "原文")
        self.assertEqual(parsed["text"], "原文")
        self.assertTrue(parsed["parse_error"])

    def test_translation_prompt_contains_style_and_target(self):
        messages = build_translation_messages(
            "我们今天下午三点开会，别迟到。",
            "en",
            context=[{"corrected": "你好", "translation": "Hello"}],
            style="live",
            glossary={"碳纤维": "carbon fiber"},
        )
        text = "\n".join(m["content"] for m in messages)
        self.assertIn("English", text)
        self.assertIn("直播", text)
        self.assertIn("carbon fiber", text)

    def test_clean_translation(self):
        self.assertEqual(clean_translation('"Hello"'), "Hello")
        self.assertEqual(clean_translation("译文：Hello"), "Hello")
        self.assertEqual(clean_translation("```\nHello\n```"), "Hello")
        self.assertEqual(clean_translation("原文：你好\n译文：Hello"), "Hello")
        self.assertEqual(clean_translation("Source: 你好\nTranslation: Hello"), "Hello")
        self.assertEqual(clean_translation("**译文：** Hello"), "Hello")


if __name__ == "__main__":
    unittest.main()
