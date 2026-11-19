"""Regression tests for the 0.1.1 bilingual/text-translator beta."""

from __future__ import annotations

import unittest

from altvoice.i18n import current_locale, set_locale, tr
from altvoice.textlang import detect_language


class TextLanguageTests(unittest.TestCase):
    def test_detects_chinese(self):
        self.assertEqual(detect_language("今天下午三点开会"), "zh")

    def test_detects_english(self):
        self.assertEqual(detect_language("Please send the report"), "en")

    def test_detects_japanese(self):
        self.assertEqual(detect_language("今日は会議があります"), "ja")


class RuntimeLocaleTests(unittest.TestCase):
    def tearDown(self):
        set_locale("zh")

    def test_english_ui_strings(self):
        set_locale("en")
        self.assertEqual(current_locale(), "en")
        self.assertEqual(tr("文本翻译器"), "Text translator")

    def test_chinese_ui_is_untranslated(self):
        set_locale("zh")
        self.assertEqual(tr("文本翻译器"), "文本翻译器")


if __name__ == "__main__":
    unittest.main()
