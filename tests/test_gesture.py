import unittest

from altvoice.hotkey.gesture import Action, AltGestureDetector, KeyEvent


class GestureTests(unittest.TestCase):
    def setUp(self):
        self.detector = AltGestureDetector(threshold_ms=280)

    def test_short_tap_replays_alt(self):
        self.assertEqual(self.detector.feed(KeyEvent("alt", True, 0)), [])
        self.assertEqual(self.detector.tick(100), [])
        self.assertEqual(
            self.detector.feed(KeyEvent("alt", False, 120)),
            [Action.REPLAY_ALT_TAP],
        )
        self.assertEqual(self.detector.state, "idle")

    def test_long_press_starts_and_stops(self):
        self.assertEqual(self.detector.feed(KeyEvent("alt", True, 0)), [])
        self.assertEqual(self.detector.tick(279), [])
        self.assertEqual(self.detector.tick(280), [Action.START_RECORDING])
        self.assertEqual(self.detector.state, "recording")
        self.assertEqual(
            self.detector.feed(KeyEvent("alt", False, 700)),
            [Action.STOP_RECORDING],
        )

    def test_other_key_cancels_pending_and_replays_alt(self):
        self.detector.feed(KeyEvent("alt", True, 0))
        actions = self.detector.feed(KeyEvent("tab", True, 100))
        self.assertEqual(actions, [Action.CANCEL, Action.REPLAY_ALT_DOWN])
        self.assertEqual(self.detector.state, "idle")

    def test_other_key_cancels_recording(self):
        self.detector.feed(KeyEvent("alt", True, 0))
        self.detector.tick(300)
        actions = self.detector.feed(KeyEvent("escape", True, 400))
        self.assertEqual(actions, [Action.CANCEL])
        self.assertEqual(self.detector.state, "idle")

    def test_auto_repeat_is_ignored(self):
        self.detector.feed(KeyEvent("alt", True, 0))
        self.detector.feed(KeyEvent("alt", True, 30))
        self.detector.tick(300)
        self.assertEqual(self.detector.state, "recording")
        self.assertEqual(self.detector.feed(KeyEvent("alt", True, 320)), [])

    def test_toggle_mode_starts_and_stops_on_each_press(self):
        detector = AltGestureDetector(threshold_ms=280, mode="toggle")
        self.assertEqual(detector.feed(KeyEvent("alt", True, 0)), [Action.START_RECORDING])
        self.assertEqual(detector.feed(KeyEvent("alt", False, 50)), [])
        self.assertEqual(detector.state, "recording")
        self.assertEqual(detector.feed(KeyEvent("alt", True, 1000)), [Action.STOP_RECORDING])
        self.assertEqual(detector.state, "idle")


if __name__ == "__main__":
    unittest.main()
