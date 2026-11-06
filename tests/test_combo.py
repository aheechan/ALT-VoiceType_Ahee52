import unittest

from altvoice.hotkey.combo import ComboHookLogic, parse_combo


class ComboTests(unittest.TestCase):
    def test_parse_alt_and_chords(self):
        self.assertEqual(parse_combo("alt").text, "alt")
        self.assertEqual(parse_combo("Alt+Q").text, "alt+q")
        self.assertEqual(parse_combo("alt+shift").text, "alt+shift")

    def test_requires_alt_and_one_main_key(self):
        with self.assertRaises(ValueError):
            parse_combo("q")
        with self.assertRaises(ValueError):
            parse_combo("ctrl+shift")

    def test_parse_left_and_right_alt(self):
        left = parse_combo("lalt+q")
        right = parse_combo("ralt+q")
        self.assertIn(0xA4, left.vks)
        self.assertNotIn(0xA5, left.vks)
        self.assertIn(0xA5, right.vks)
        self.assertNotIn(0xA4, right.vks)

    def test_left_alt_does_not_fire_on_right_alt(self):
        calls = []
        logic = ComboHookLogic(parse_combo("lalt+q"), lambda: calls.append(1))
        logic.handle_key(0xA5, True, False)
        logic.handle_key(0x51, True, False)
        self.assertEqual(calls, [])

    def test_chord_triggers_once(self):
        calls = []
        logic = ComboHookLogic(parse_combo("alt+q"), lambda: calls.append(1))
        self.assertFalse(logic.handle_key(0xA4, True, False).triggered)
        self.assertTrue(logic.handle_key(0x51, True, False).triggered)
        self.assertTrue(calls == [1])
        logic.handle_key(0x51, True, False)
        self.assertEqual(calls, [1])
        logic.handle_key(0x51, False, False)
        logic.handle_key(0xA4, False, False)
        self.assertFalse(logic.handle_key(0xA4, True, False).triggered)
        self.assertTrue(logic.handle_key(0x51, True, False).triggered)
        self.assertEqual(calls, [1, 1])

    def test_q_without_alt_passes(self):
        logic = ComboHookLogic(parse_combo("alt+q"), lambda: None)
        self.assertFalse(logic.handle_key(0x51, True, False).suppress)
