import unittest
from unittest import mock

from altvoice.cli import main


class CliEntrypointTests(unittest.TestCase):
    def test_no_arguments_starts_tray(self):
        with mock.patch("altvoice.cli.cmd_run", return_value=7) as run:
            self.assertEqual(main([]), 7)
        args = run.call_args.args[0]
        self.assertEqual(args.command, "run")
        self.assertEqual(args.smoke, 0.0)


if __name__ == "__main__":
    unittest.main()
