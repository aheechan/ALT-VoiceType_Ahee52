import unittest

from altvoice.asr import FakeASR
from altvoice.correct import NullCorrector
from altvoice.inject import NullInjector
from altvoice.pipeline import VoicePipeline
from altvoice.translate.base import TranslationError, Translator


class EchoTranslator(Translator):
    def __init__(self):
        self.calls = 0

    def translate(self, text, target_lang, context=None, style="daily", glossary=None, source_lang="zh"):
        self.calls += 1
        return f"{target_lang}:{text}"


class FailingTranslator(Translator):
    def translate(self, text, target_lang, context=None, style="daily", glossary=None, source_lang="zh"):
        raise TranslationError("offline")


class PipelineTests(unittest.TestCase):
    def test_chinese_target_skips_translation(self):
        translator = EchoTranslator()
        injector = NullInjector()
        pipeline = VoicePipeline(
            asr=FakeASR("你好，世界。"),
            corrector=NullCorrector(),
            translator=translator,
            injector=injector,
        )
        result = pipeline.process_audio("ignored.wav", target_lang="zh")
        self.assertEqual(result.corrected_text, "你好，世界。")
        self.assertEqual(result.translation, "你好，世界。")
        self.assertEqual(translator.calls, 0)
        self.assertEqual(injector.last_text, "你好，世界。")
        self.assertTrue(result.injected)
        self.assertEqual(len(pipeline.context), 1)

    def test_english_target_translates(self):
        translator = EchoTranslator()
        injector = NullInjector()
        pipeline = VoicePipeline(
            asr=FakeASR("你好"),
            corrector=NullCorrector(),
            translator=translator,
            injector=injector,
        )
        result = pipeline.process_audio("ignored.wav", target_lang="en")
        self.assertEqual(result.translation, "en:你好")
        self.assertEqual(translator.calls, 1)
        self.assertEqual(injector.last_text, "en:你好")

    def test_translation_failure_falls_back_to_source(self):
        pipeline = VoicePipeline(
            asr=FakeASR("你好"),
            corrector=NullCorrector(),
            translator=FailingTranslator(),
            injector=NullInjector(),
        )
        result = pipeline.process_text("你好", target_lang="en")
        self.assertEqual(result.translation, "你好")
        self.assertIn("offline", result.error)

    def test_no_injection(self):
        injector = NullInjector()
        pipeline = VoicePipeline(
            asr=FakeASR("你好"),
            corrector=NullCorrector(),
            translator=EchoTranslator(),
            injector=injector,
        )
        result = pipeline.process_text("你好", target_lang="zh", inject=False)
        self.assertFalse(result.injected)
        self.assertEqual(injector.last_text, "")

    def test_context_grows_and_is_bounded(self):
        pipeline = VoicePipeline(
            asr=FakeASR("x"),
            corrector=NullCorrector(),
            translator=EchoTranslator(),
            injector=NullInjector(),
        )
        for i in range(15):
            pipeline.process_text(f"第{i}句", target_lang="zh", inject=False)
        self.assertEqual(len(pipeline.context), 10)
        self.assertEqual(pipeline.context.recent(1)[0]["corrected"], "第14句")


if __name__ == "__main__":
    unittest.main()
