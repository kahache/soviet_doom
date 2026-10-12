"""Tests for tools/smoke.py — everything that can be checked without GZDoom.

Covered without the engine: log analysis against good and bad samples,
command-line construction, and the "gzdoom / IWAD not found" paths.
The one test that really launches GZDoom is skipped when it is not installed,
so the suite stays green on any machine.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import contextlib
import io
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import smoke  # noqa: E402

# A trimmed but faithful copy of the real G0 evidence log: it must parse
# cleanly, Vulkan vendor strings and the Freedoom banner included.
GOOD_LOG = """Log started: 2026-10-09 00:37:34
GZDoom version g4.14.2
W_Init: Init WADfiles.
adding /Applications/GZDoom.app/Contents/MacOS/gzdoom.pk3, 692 lumps
adding /Users/x/soviet_doom/iwads/freedoom2.wad, 3610 lumps
adding /Users/x/soviet_doom/dist/sovietdoom.pk3, 5 lumps
S_Init: Setting up sound.
Vulkan device: Intel(R) Iris(TM) Graphics 6100
Vulkan extensions: VK_KHR_16bit_storage VK_EXT_image_robustness VK_NV_glsl_shader
Max. texture size: 16384
G_ParseMapInfo: Load map definitions.
Texman.Init: Init texture manager.
LoadActors: Load actor definitions.
Adding dehacked patch freedoom2.wad:DEHACKED
Patch installed
===========================================================================
This is Freedoom, the free content first person shooter.

Freedoom is freely redistributable under the terms of the modified BSD
license. Check out the Freedoom website for more information:

    https://freedoom.github.io/
============================================================================
D_CheckNetGame: Checking network game status.
player 1 of 1 (1 nodes)

----------------------------------------

MAP01 - SD: Test Range

SOVIETDOOM loaded: map MAP01 (SD: Test Range)
Captured Screenshot_Doom_20261009_003742.png
"""

# One bad line per pattern we promise to catch. Key = expected pattern id.
BAD_LINES = {
    "script-error": 'Script error, "sovietdoom.pk3:MAPINFO" line 7: Unknown property \'lookup\'',
    "execution-stopped": "Execution could not continue.",
    "unknown-texture": "Unknown texture 'SDCONC9' in sidedef 12",
    "unknown-flat": "Unknown flat 'SDFLR9' in sector 3",
    "missing-sprite": "Missing sprite SDPLA0 for state SD_Soldier.Spawn",
    # The B1 message from G0, as the engine prints it on its own line.
    "unknown-property": "Unknown property 'lookup' found in episode definition",
    "unknown-other": "Unknown command 'sd_nonsense'",
    "bad-thing": "Bad syntax in TEXTURES line 4",
    "tried-to-find": "Could not find sound SD_ALARM",
    "generic-error": "Internal error in P_SetupLevel",
    "fatal": "Fatal error: out of memory",
}


class ScanGoodLogTests(unittest.TestCase):
    def setUp(self):
        self.report = smoke.scan_log(GOOD_LOG)

    def test_no_failures_on_a_clean_log(self):
        self.assertEqual(
            [], self.report.failures,
            "clean log flagged: " + "; ".join(h.line for h in self.report.failures),
        )

    def test_extracts_version_iwad_lumps_and_map(self):
        self.assertEqual("g4.14.2", self.report.version)
        self.assertTrue(self.report.iwad.endswith("freedoom2.wad"))
        self.assertEqual(5, self.report.mod_lumps)
        self.assertEqual(3, len(self.report.loaded))
        self.assertEqual("MAP01", self.report.map_entered)
        self.assertEqual("SD: Test Range", self.report.map_title)
        self.assertEqual("Screenshot_Doom_20261009_003742.png", self.report.screenshot_name)

    def test_vulkan_extension_dump_is_benign(self):
        line = "Vulkan extensions: VK_KHR_16bit_storage VK_NV_glsl_shader VK_EXT_error_thing"
        self.assertTrue(smoke.is_benign(line))
        self.assertEqual([], smoke.scan_log(line).failures)

    def test_missing_facts_are_reported_as_unknown_not_invented(self):
        report = smoke.scan_log("Log started: today\n")
        self.assertIsNone(report.version)
        self.assertIsNone(report.iwad)
        self.assertIsNone(report.map_entered)
        self.assertIsNone(report.mod_lumps)


class ScanBadLogTests(unittest.TestCase):
    def test_each_failure_pattern_fires(self):
        for pattern_id, bad in BAD_LINES.items():
            with self.subTest(pattern=pattern_id):
                report = smoke.scan_log(GOOD_LOG + bad + "\n")
                self.assertTrue(report.failures, f"{pattern_id} not caught: {bad}")
                self.assertIn(pattern_id, {h.pattern_id for h in report.failures})

    def test_generic_error_word_is_caught(self):
        report = smoke.scan_log("Internal error in P_SetupLevel\n")
        self.assertEqual(["generic-error"], [h.pattern_id for h in report.failures])

    def test_every_declared_pattern_has_a_sample(self):
        """No pattern may sit in the contract untested."""
        declared = {pid for pid, _rx, _why in smoke.LOG_FAILURE_PATTERNS}
        tested = set(BAD_LINES)
        self.assertEqual(set(), declared - tested, "patterns without a test sample")

    def test_fatal_pattern(self):
        report = smoke.scan_log("Segmentation fault\n")
        self.assertIn("fatal", {h.pattern_id for h in report.failures})

    def test_line_number_is_one_based_and_exact(self):
        text = "line one\nline two\nUnknown texture 'SDNOPE'\nline four\n"
        report = smoke.scan_log(text)
        self.assertEqual(1, len(report.failures))
        self.assertEqual(3, report.failures[0].lineno)
        self.assertIn("SDNOPE", report.failures[0].line)

    def test_a_line_is_reported_once_even_if_two_patterns_match(self):
        report = smoke.scan_log("Script error: Unknown property 'lookup'\n")
        self.assertEqual(1, len(report.failures))
        self.assertEqual("script-error", report.failures[0].pattern_id)

    def test_warnings_are_not_failures_unless_strict(self):
        text = "Warning: sector 3 has no tag\n"
        self.assertEqual([], smoke.scan_log(text).failures)
        self.assertEqual(1, len(smoke.scan_log(text).warnings))
        strict = smoke.scan_log(text, strict=True)
        self.assertEqual(1, len(strict.failures))
        self.assertEqual([], strict.warnings)

    @unittest.skipUnless(
        (PROJECT_ROOT / "docs/qa/evidence/2026-10-09_0037_F0_g0-gzdoom.log").is_file(),
        "G0 evidence log not present",
    )
    def test_real_g0_evidence_log_still_passes(self):
        """Regression guard: the log that passed G0 by hand must pass the tool."""
        path = PROJECT_ROOT / "docs/qa/evidence/2026-10-09_0037_F0_g0-gzdoom.log"
        report = smoke.scan_log(path.read_text(encoding="utf-8", errors="replace"))
        self.assertEqual(
            [], report.failures,
            "false positives on the G0 log: " + "; ".join(h.render() for h in report.failures),
        )
        self.assertEqual("g4.14.2", report.version)
        self.assertEqual("MAP01", report.map_entered)


class CommandLineTests(unittest.TestCase):
    def _cmd(self, **kw):
        defaults = dict(
            gzdoom=Path("/bin/gzdoom"),
            iwad=Path("/w/freedoom2.wad"),
            pk3=Path("/d/sovietdoom.pk3"),
            log=Path("/l/smoke.log"),
            shot_dir=Path("/l/shots"),
        )
        defaults.update(kw)
        return smoke.build_command(**defaults)

    def test_core_arguments_in_run_sh_order(self):
        cmd = self._cmd()
        self.assertEqual("/bin/gzdoom", cmd[0])
        # -config leads so the engine never reads or writes the user's own
        # gzdoom.ini: an automated -nosound run was enough to leave a
        # developer with a silent game (2026-10-13).
        self.assertEqual("-config", cmd[1])
        self.assertTrue(cmd[2].endswith("gzdoom-tooling.ini"), cmd[2])
        self.assertEqual(["-iwad", "/w/freedoom2.wad"], cmd[3:5])
        self.assertEqual(["-file", "/d/sovietdoom.pk3"], cmd[5:7])
        self.assertEqual(["+logfile", "/l/smoke.log"], cmd[7:9])
        self.assertIn("+map", cmd)
        self.assertEqual("MAP01", cmd[cmd.index("+map") + 1])

    def test_skill_omitted_by_default_and_present_when_asked(self):
        self.assertNotIn("-skill", self._cmd())
        cmd = self._cmd(skill=4)
        self.assertEqual("4", cmd[cmd.index("-skill") + 1])

    def test_quiet_window_and_no_sound_by_default(self):
        cmd = self._cmd()
        self.assertIn("-nosound", cmd)
        self.assertEqual("0", cmd[cmd.index("+vid_fullscreen") + 1])
        self.assertNotIn("-nosound", self._cmd(sound=True))

    def test_console_sequence_is_the_proven_one(self):
        self.assertEqual(
            "+wait 140; screenshot; wait 35; quit",
            smoke.console_sequence(140, 35, screenshot=True),
        )
        self.assertEqual("+wait 70; quit", smoke.console_sequence(70, 35, screenshot=False))
        self.assertIn("+wait 140; screenshot; wait 35; quit", self._cmd())

    def test_screenshot_dir_only_when_shooting(self):
        cmd = self._cmd()
        self.assertEqual("/l/shots", cmd[cmd.index("+screenshot_dir") + 1])
        self.assertNotIn("+screenshot_dir", self._cmd(screenshot=False))

    def test_custom_map_skill_and_extra_args(self):
        cmd = self._cmd(map_name="MAP02", skill=1, extra=["+vid_fps", "1"])
        self.assertEqual("MAP02", cmd[cmd.index("+map") + 1])
        self.assertEqual(["+vid_fps", "1"], cmd[-2:])

    def test_every_argument_is_a_string(self):
        for arg in self._cmd(skill=3):
            self.assertIsInstance(arg, str)


class FindGzdoomTests(unittest.TestCase):
    def test_explicit_path_that_does_not_exist_fails_with_code_2(self):
        with self.assertRaises(smoke.SmokeError) as ctx:
            smoke.find_gzdoom("/nope/gzdoom", env={})
        self.assertEqual(smoke.EXIT_NO_GZDOOM, ctx.exception.code)

    def test_env_var_is_honoured_and_validated(self):
        with self.assertRaises(smoke.SmokeError) as ctx:
            smoke.find_gzdoom(None, env={"GZDOOM": "/nope/gzdoom"})
        self.assertEqual(smoke.EXIT_NO_GZDOOM, ctx.exception.code)

    def test_explicit_executable_is_returned(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "gzdoom"
            fake.write_text("#!/bin/sh\n")
            fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
            self.assertEqual(fake, smoke.find_gzdoom(str(fake), env={}))

    def test_nothing_installed_anywhere_fails_with_advice(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.object(smoke, "gzdoom_candidates", return_value=[Path(tmp) / "nope"]):
            with self.assertRaises(smoke.SmokeError) as ctx:
                smoke.find_gzdoom(None, env={"PATH": tmp})
            self.assertEqual(smoke.EXIT_NO_GZDOOM, ctx.exception.code)
            self.assertIn("brew install", str(ctx.exception))


class FindIwadTests(unittest.TestCase):
    def test_explicit_missing_file_fails_with_code_3(self):
        with self.assertRaises(smoke.SmokeError) as ctx:
            smoke.find_iwad("/nope/doom2.wad", env={})
        self.assertEqual(smoke.EXIT_NO_IWAD, ctx.exception.code)

    def test_no_iwad_anywhere_fails_with_advice(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(smoke.SmokeError) as ctx:
                smoke.find_iwad(None, env={"HOME": tmp}, root=Path(tmp))
            self.assertEqual(smoke.EXIT_NO_IWAD, ctx.exception.code)
            self.assertIn("freedoom2.wad", str(ctx.exception))

    def test_freedoom_is_preferred_over_doom2(self):
        with tempfile.TemporaryDirectory() as tmp:
            iwads = Path(tmp) / "iwads"
            iwads.mkdir()
            (iwads / "doom2.wad").write_bytes(b"PWAD")
            (iwads / "freedoom2.wad").write_bytes(b"IWAD")
            found = smoke.find_iwad(None, env={"HOME": tmp}, root=Path(tmp))
            self.assertEqual("freedoom2.wad", found.name)

    def test_doomwaddir_is_searched(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as wads:
            (Path(wads) / "doom2.wad").write_bytes(b"IWAD")
            found = smoke.find_iwad(None, env={"HOME": tmp, "DOOMWADDIR": wads}, root=Path(tmp))
            self.assertEqual("doom2.wad", found.name)


class CliTests(unittest.TestCase):
    def test_list_patterns_exits_clean_and_prints_the_contract(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(smoke.EXIT_OK, smoke.main(["--list-patterns"]))
        for pattern_id, _rx, _why in smoke.LOG_FAILURE_PATTERNS:
            self.assertIn(pattern_id, out.getvalue())

    def test_missing_gzdoom_exits_2_without_building(self):
        with mock.patch.object(smoke, "run_build", side_effect=AssertionError("must not build")):
            self.assertEqual(smoke.EXIT_NO_GZDOOM, smoke.main(["--gzdoom", "/nope/gzdoom"]))

    def test_missing_iwad_exits_3_without_building(self):
        with mock.patch.object(smoke, "run_build", side_effect=AssertionError("must not build")), \
                mock.patch.object(smoke, "find_gzdoom", return_value=Path("/bin/echo")):
            self.assertEqual(smoke.EXIT_NO_IWAD, smoke.main(["--iwad", "/nope/doom2.wad"]))

    def test_parse_args_defaults(self):
        args = smoke.parse_args([])
        self.assertEqual("MAP01", args.map)
        self.assertIsNone(args.skill)
        self.assertFalse(args.keep_evidence)
        self.assertEqual(smoke.DEFAULT_TIMEOUT_S, args.timeout)

    def test_evidence_name_follows_the_project_convention(self):
        from datetime import datetime
        stem = smoke.evidence_stem("F3", "g3-map01-skill4", datetime(2026, 10, 12, 23, 5))
        self.assertEqual("2026-10-12_2305_F3_g3-map01-skill4", stem)

    def test_default_outputs_live_in_the_gitignored_logs_dir(self):
        """Without --keep-evidence nothing may land inside the repo's tracked tree."""
        self.assertEqual(PROJECT_ROOT / "logs", smoke.DEFAULT_LOG.parent)
        self.assertEqual(PROJECT_ROOT / "logs", smoke.DEFAULT_SHOT_DIR.parent)
        self.assertIn("logs/", (PROJECT_ROOT / ".gitignore").read_text())


class TimeoutTests(unittest.TestCase):
    def test_a_hanging_process_is_killed_and_reported(self):
        result = smoke.run_engine(["/bin/sh", "-c", "sleep 30"], timeout_s=0.5)
        self.assertTrue(result.timed_out)
        self.assertIsNone(result.returncode)

    def test_a_normal_process_is_not_reported_as_timed_out(self):
        result = smoke.run_engine(["/bin/sh", "-c", "exit 0"], timeout_s=20)
        self.assertFalse(result.timed_out)
        self.assertEqual(0, result.returncode)

    def test_engine_failure_is_surfaced(self):
        result = smoke.run_engine(["/bin/sh", "-c", "exit 3"], timeout_s=20)
        self.assertEqual(3, result.returncode)


def _gzdoom_installed() -> bool:
    try:
        smoke.find_gzdoom()
        smoke.find_iwad()
        return True
    except smoke.SmokeError:
        return False


@unittest.skipUnless(_gzdoom_installed(), "GZDoom and/or an IWAD are not installed here")
@unittest.skipUnless(os.environ.get("SD_ENGINE_TESTS"), "set SD_ENGINE_TESTS=1 to run the real engine")
class EngineTests(unittest.TestCase):
    """Really launches GZDoom. Slow; opt-in via SD_ENGINE_TESTS=1."""

    def test_smoke_run_passes_on_the_current_pk3(self):
        self.assertEqual(smoke.EXIT_OK, smoke.main(["--map", "MAP01", "--wait", "70"]))


if __name__ == "__main__":
    unittest.main()
