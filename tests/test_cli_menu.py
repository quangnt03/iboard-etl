"""Unit tests for CLI menu wiring.

Keyword arguments:
None."""

import unittest

from scripts.cli import build_parser, get_menu_actions, main


class TestCliMenu(unittest.TestCase):
    """Unit tests for the interactive CLI menu.

Keyword arguments:
None."""

    def test_menu_actions_exist(self) -> None:
        """Ensure menu registry is constructed.

Keyword arguments:
self -- The self."""
        actions = get_menu_actions()
        self.assertGreaterEqual(len(actions), 3)
        keys = {action.key for action in actions}
        self.assertIn("1", keys)
        self.assertIn("5", keys)

    def test_main_help_exits(self) -> None:
        """Ensure --help exits cleanly.

Keyword arguments:
self -- The self."""
        with self.assertRaises(SystemExit) as context:
            main(["--help"])
        self.assertEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
