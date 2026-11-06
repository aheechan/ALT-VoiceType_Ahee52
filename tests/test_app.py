import threading
import unittest
from pathlib import Path

import numpy as np

from altvoice.app import VoiceAppController
from altvoice.asr import FakeASR
from altvoice.config import AppConfig
from altvoice.correct import NullCorrector
from altvoice.history import HistoryStore
from altvoice.inject import NullInjector
from altvoice.pipeline import PipelineResult, VoicePipeline
from altvoice.translate.base import Translator
from tests.helpers import workspace_tempdir


class EchoTranslator(Translator):
    def translate(self, text, target_lang, context=None, style="daily", glossary=None, source_lang="zh"):
        return f"{target_lang}:{text}"


class FakeRecorder:
    def __init__(self, seconds=1.0):
        self.seconds = seconds
        self.started = threading.Event()

    def record_push_to_talk(self, stop_event, max_seconds):
        self.started.set()
        stop_event.wait(1.0)
        return np.full(int(16000 * self.seconds), 0.1, dtype=np.float32), 16000


class ControllerTests(unittest.TestCase):
    def _controller(self, preview=True, history_path=None):
        config = AppConfig()
        config.ui.preview = preview
        config.ui.focus_guard = False
        config.asr.engine = "fake"
        config.translator.target_language = "en"
        config.history.enabled = bool(history_path)
        if history_path:
            config.history.path = str(history_path)
        injector = NullInjector()
        pipeline = VoicePipeline(
            asr=FakeASR("你好，世界。"),
            corrector=NullCorrector(),
            translator=EchoTranslator(),
            injector=injector,
        )
        recorder = FakeRecorder()
        results = []
        event = threading.Event()

        def on_result(result):
            results.append(result)
            event.set()

        controller = VoiceAppController(
            config=config,
            pipeline=pipeline,
            recorder=recorder,
            temp_dir=str(Path(__file__).resolve().parent / "_tmp"),
            on_result=on_result,
        )
        return controller, recorder, results, event, injector

    def test_recording_always_pastes(self):
        with workspace_tempdir() as tmp:
            controller, recorder, results, event, injector = self._controller(preview=True)
            controller._temp_dir = tmp
            controller.start_recording()
            self.assertTrue(recorder.started.wait(1.0))
            controller.stop_recording()
            self.assertTrue(event.wait(3.0))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].output_text, "en:你好，世界。")
            self.assertTrue(results[0].injected)
            self.assertEqual(injector.last_text, "en:你好，世界。")

    def test_direct_insert_when_preview_off(self):
        with workspace_tempdir() as tmp:
            controller, recorder, results, event, injector = self._controller(preview=False)
            controller._temp_dir = tmp
            controller.start_recording()
            self.assertTrue(recorder.started.wait(1.0))
            controller.stop_recording()
            self.assertTrue(event.wait(3.0))
            self.assertTrue(results[0].injected)
            self.assertEqual(injector.last_text, "en:你好，世界。")

    def test_cancel_does_not_emit_result(self):
        with workspace_tempdir() as tmp:
            controller, recorder, results, event, _injector = self._controller()
            controller._temp_dir = tmp
            controller.start_recording()
            self.assertTrue(recorder.started.wait(1.0))
            controller.cancel_recording()
            self.assertFalse(event.wait(0.5))
            self.assertEqual(results, [])

    def test_transcribe_mode_targets_chinese(self):
        controller, _recorder, _results, _event, _injector = self._controller()
        controller.set_mode("transcribe")
        self.assertEqual(controller._effective_target(), "zh")

    def test_focus_guard_copies_instead_of_injecting(self):
        controller, _recorder, _results, _event, injector = self._controller(preview=True)
        controller.config.ui.focus_guard = True
        controller._target_hwnd = 111
        controller._foreground_window = lambda: 222  # type: ignore[method-assign]
        copied: list[str] = []
        controller._copy_to_clipboard = lambda text: copied.append(text)  # type: ignore[method-assign]
        result = PipelineResult(
            raw_text="你好",
            corrected_text="你好",
            translation="Hello",
            target_lang="en",
        )
        controller._deliver(result, "Hello")
        self.assertEqual(injector.last_text, "")
        self.assertEqual(copied, ["Hello"])
        self.assertFalse(result.injected)

    def test_history_persists_result(self):
        with workspace_tempdir() as tmp:
            history_path = Path(tmp) / "history.db"
            controller, recorder, _results, event, _injector = self._controller(
                history_path=history_path
            )
            controller._temp_dir = tmp
            controller.start_recording()
            self.assertTrue(recorder.started.wait(1.0))
            controller.stop_recording()
            self.assertTrue(event.wait(3.0))
            controller.close()
            with HistoryStore(history_path) as store:
                recent = store.recent(1)
            self.assertEqual(recent[0]["corrected"], "你好，世界。")
            self.assertEqual(recent[0]["translation"], "en:你好，世界。")

    def test_history_seeds_context(self):
        with workspace_tempdir() as tmp:
            history_path = Path(tmp) / "history.db"
            with HistoryStore(history_path) as store:
                store.add_utterance("上次说的话", "上次说的话。", "Last time.", "en", "zh")
            config = AppConfig()
            config.asr.engine = "fake"
            config.servers.enabled = False
            config.corrector.enabled = False
            config.translator.enabled = False
            config.history.path = str(history_path)
            controller = VoiceAppController(config=config, temp_dir=tmp)
            try:
                pipeline = controller.ensure_pipeline()
                self.assertEqual(len(pipeline.context), 1)
                self.assertEqual(pipeline.context.recent(1)[0]["corrected"], "上次说的话。")
            finally:
                controller.close()


if __name__ == "__main__":
    unittest.main()
