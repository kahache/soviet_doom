"""Tests for tools/audio/audition.py: the engine gate (D26).

The rest of the tool drives GZDoom and is verified by ear; what must never
regress is that it refuses to open a window unless SD_ALLOW_ENGINE=1, like
tools/smoke.py and tools/run.sh. Found 2026-10-13: the gate existed in those
two and not here, although --play and --render both start the engine.

Run:  python3 -m unittest tests.test_audition -v
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))

import audition  # noqa: E402


class EngineGateTests(unittest.TestCase):
    def test_gate_is_closed_without_the_variable(self):
        self.assertFalse(audition.engine_allowed({}))
        self.assertFalse(audition.engine_allowed({"SD_ALLOW_ENGINE": "0"}))
        self.assertFalse(audition.engine_allowed({"SD_ALLOW_ENGINE": "yes"}))

    def test_gate_opens_only_on_exactly_one(self):
        self.assertTrue(audition.engine_allowed({"SD_ALLOW_ENGINE": "1"}))

    def test_require_engine_refuses_before_looking_for_anything(self):
        env = {k: v for k, v in os.environ.items() if k != "SD_ALLOW_ENGINE"}
        with mock.patch.dict(os.environ, env, clear=True),                 mock.patch.object(audition, "find", side_effect=AssertionError("must not search")),                 contextlib.redirect_stderr(io.StringIO()) as err:
            with self.assertRaises(SystemExit) as ctx:
                audition.require_engine()
        self.assertEqual(audition.EXIT_ENGINE_BLOCKED, ctx.exception.code)
        self.assertIn("SD_ALLOW_ENGINE", err.getvalue())

    def test_play_and_render_both_pass_through_the_gate(self):
        """Both commands that start GZDoom must call require_engine first."""
        for name in ("cmd_play", "cmd_render"):
            with self.subTest(command=name):
                with mock.patch.object(audition, "require_engine",
                                       side_effect=SystemExit(audition.EXIT_ENGINE_BLOCKED)),                         mock.patch.object(audition, "pack", side_effect=AssertionError("packed before the gate")):
                    with self.assertRaises(SystemExit):
                        if name == "cmd_play":
                            audition.cmd_play("title")
                        else:
                            audition.cmd_render({})


if __name__ == "__main__":
    unittest.main()
