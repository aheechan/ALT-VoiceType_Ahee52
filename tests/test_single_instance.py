import os
import unittest
import uuid

from altvoice.single_instance import SingleInstance


@unittest.skipUnless(os.name == "nt", "Windows named mutex test")
class SingleInstanceTests(unittest.TestCase):
    def test_second_instance_is_rejected(self):
        name = f"Local\\ALT-VoiceTypeTest-{uuid.uuid4()}"
        first = SingleInstance(name)
        second = SingleInstance(name)
        try:
            self.assertTrue(first.acquired)
            self.assertFalse(second.acquired)
        finally:
            second.close()
            first.close()
        third = SingleInstance(name)
        try:
            self.assertTrue(third.acquired)
        finally:
            third.close()


if __name__ == "__main__":
    unittest.main()
