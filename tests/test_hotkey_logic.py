import unittest

from altvoice.hotkey.logic import AltHookLogic


class HookLogicTests(unittest.TestCase):
    def _logic(self, **kwargs):
        self.calls = {"start": 0, "stop": 0, "cancel": 0, "tap": 0, "down": 0}

        def bump(name):
            def inner():
                self.calls[name] += 1

            return inner

        return AltHookLogic(
            threshold_ms=280,
            on_start=bump("start"),
            on_stop=bump("stop"),
            on_cancel=bump("cancel"),
            replay_alt_tap=bump("tap"),
            replay_alt_down=bump("down"),
            **kwargs,
        )

    def test_short_tap_replays(self):
        logic = self._logic()
        first = logic.handle_key(0x12, True, False, 0)
        self.assertTrue(first.suppress)
        self.assertTrue(first.start_timer)
        second = logic.handle_key(0x12, False, False, 100)
        self.assertTrue(second.suppress)
        self.assertTrue(second.cancel_timer)
        self.assertEqual(self.calls["tap"], 1)
        self.assertEqual(self.calls["start"], 0)

    def test_long_press_starts_and_stops(self):
        logic = self._logic()
        logic.handle_key(0x12, True, False, 0)
        logic.tick(300)
        self.assertEqual(self.calls["start"], 1)
        logic.handle_key(0x12, False, False, 500)
        self.assertEqual(self.calls["stop"], 1)

    def test_toggle_mode_starts_and_stops_on_presses(self):
        logic = self._logic(mode="toggle")
        self.assertTrue(logic.handle_key(0x12, True, False, 0).suppress)
        self.assertEqual(self.calls["start"], 1)
        logic.handle_key(0x12, False, False, 80)
        self.assertEqual(self.calls["stop"], 0)
        logic.handle_key(0x12, True, False, 1200)
        self.assertEqual(self.calls["stop"], 1)

    def test_combo_cancels_and_replays_modifier(self):
        logic = self._logic()
        logic.handle_key(0x12, True, False, 0)
        decision = logic.handle_key(0x09, True, False, 100)  # Tab
        self.assertFalse(decision.suppress)
        self.assertTrue(decision.cancel_timer)
        self.assertEqual(self.calls["cancel"], 1)
        self.assertEqual(self.calls["down"], 1)

    def test_injected_events_are_passed_through(self):
        logic = self._logic()
        decision = logic.handle_key(0x12, True, True, 0)
        self.assertFalse(decision.suppress)
        self.assertFalse(decision.start_timer)

    def test_auto_repeat_does_not_restart_timer(self):
        logic = self._logic()
        first = logic.handle_key(0x12, True, False, 0)
        second = logic.handle_key(0x12, True, False, 30)
        self.assertTrue(first.start_timer)
        self.assertFalse(second.start_timer)
        self.assertTrue(second.suppress)


if __name__ == "__main__":
    unittest.main()
