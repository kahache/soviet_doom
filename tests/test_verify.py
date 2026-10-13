"""Tests for tools/verify.py, the two-level verification entry point.

What is worth testing here is the **decision**, not the plumbing: given a
list of changed files, does `auto` pick the level the CEO would pick, and
does it pick it for a reason it can state out loud? Everything else in the
tool is subprocess glue that the four underlying tools already test.

So the bulk of this file drives `decide()` with synthetic path lists:

  - the ladder itself (docs < fast < art < full) and that a mix takes the
    maximum, which is the rule that keeps a cheap level from hiding an
    expensive change;
  - the specific boundaries that cost something if they are wrong -
    `tools/build.py` is FULL while `tools/check_pk3.py` is FAST, and
    `tools/art/` is ART while `tools/` at large is FAST;
  - the engine-map shortcut: a change confined to src/maps/MAP02 boots
    MAP02 and not the whole set, but a ZScript change boots everything;
  - noise (.DS_Store, __pycache__, *.pyc) never raises the level, because
    an editor dropping must not open a GZDoom window;
  - the unknown path, which must land on FULL - the safe answer to "I do
    not recognise this" is the expensive one, never the cheap one.

The git porcelain parser gets its own class because renames are the case
everybody gets wrong (two NUL records for one change, and both paths count).

Run:  python3 -m unittest tests.test_verify -v
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import verify  # noqa: E402

L = verify.Level
MAPS = ("MAP01", "MAP02")


class LadderTests(unittest.TestCase):
    """The levels must nest, or `auto` taking the maximum is meaningless."""

    def test_levels_are_ordered_docs_fast_art_full(self):
        self.assertLess(L.DOCS, L.FAST)
        self.assertLess(L.FAST, L.ART)
        self.assertLess(L.ART, L.FULL)

    def test_each_plan_contains_the_one_below_it(self):
        docs, fast, art, full = (verify.plan_for(level) for level in L)
        self.assertEqual(
            (True, False, False, False, False, False),
            (docs.docs_check, docs.build, docs.check_pk3, docs.tests, docs.slow_art, docs.engine),
        )
        for plan in (fast, art, full):
            self.assertTrue(plan.docs_check and plan.build and plan.check_pk3 and plan.tests)
        self.assertFalse(fast.slow_art, "fast must skip the slow art generator runs")
        self.assertTrue(art.slow_art)
        self.assertTrue(full.slow_art)
        self.assertFalse(fast.engine, "fast must never open a window")
        self.assertFalse(art.engine, "art must never open a window")
        self.assertTrue(full.engine)

    def test_only_full_ever_starts_the_engine(self):
        for level in (L.DOCS, L.FAST, L.ART):
            self.assertFalse(verify.plan_for(level).engine, f"{level.label} opens a window")

    def test_engine_tests_env_is_off_unless_asked(self):
        self.assertFalse(verify.plan_for(L.FULL).engine_tests)
        self.assertTrue(verify.plan_for(L.FULL, engine_tests=True).engine_tests)


class ClassifyTests(unittest.TestCase):
    """One path in, one rule out. The boundaries are the interesting part."""

    def assertRule(self, path, rule_id, level):
        rule = verify.classify(path)
        self.assertEqual(rule_id, rule.id, f"{path} -> {rule.id}, expected {rule_id}")
        self.assertEqual(level, rule.level, f"{path} -> {rule.level.label}")

    def test_engine_sources_are_full(self):
        for path in ("src/zscript/sd/player.zs",
                     "src/zscript/weapons/ppsh.zs",
                     "src/lumps/MAPINFO",
                     "src/lumps/LANGUAGE",
                     "src/maps/MAP01/map.py"):
            self.assertRule(path, "engine-src", L.FULL)

    def test_the_packer_is_full_but_the_other_tools_are_not(self):
        self.assertRule("tools/build.py", "packer", L.FULL)
        self.assertRule("tools/sdbuild/pk3.py", "packer", L.FULL)
        self.assertRule("tools/sdbuild/udmf.py", "packer", L.FULL)
        # check_pk3 and smoke are validators: they cannot change what ships.
        self.assertRule("tools/check_pk3.py", "tooling", L.FAST)
        self.assertRule("tools/smoke.py", "tooling", L.FAST)
        self.assertRule("tools/verify.py", "tooling", L.FAST)

    def test_art_and_audio_stop_at_art(self):
        for path in ("assets/textures/soviet_base/SDSTAR1.png",
                     "assets/flats/soviet_base/SDFLR1.png",
                     "tools/art/gen_soviet_base.py",
                     "tools/art/artlib.py",
                     "tools/audio/gen_music.py"):
            self.assertRule(path, "art", L.ART)

    def test_tests_and_ci_are_fast(self):
        for path in ("tests/test_build.py", "tests/test_verify.py",
                     ".github/workflows/ci.yml", ".coveragerc", ".gitignore"):
            self.assertRule(path, "tooling", L.FAST)

    def test_documents_and_scratch_work_are_docs(self):
        for path in ("docs/PRD.md", "docs/ru/PRD.md", "docs/art/ART-BIBLE.md",
                     "docs/qa/GATE-REVIEWS.md", "work/art/sweep.png",
                     "README.md", "CLAUDE.md", "LICENSE.md",
                     ".claude/agents/qa-engineer.md"):
            self.assertRule(path, "docs", L.DOCS)

    def test_an_unknown_path_is_full_not_docs(self):
        """The cost of guessing low is a bug that ships; guessing high is 20s."""
        for path in ("Makefile", "setup.py", "vendor/thing.c", "iwads/freedoom2.wad"):
            self.assertRule(path, "unknown", L.FULL)

    def test_leading_dot_slash_is_tolerated(self):
        self.assertRule("./docs/PRD.md", "docs", L.DOCS)


class DecideTests(unittest.TestCase):
    def test_documentation_only_change_needs_no_build(self):
        decision = verify.decide(["docs/PRD.md", "docs/ru/PRD.md"], MAPS)
        self.assertEqual(L.DOCS, decision.level)
        self.assertEqual((), decision.maps)
        plan = verify.plan_for(decision.level, decision.maps)
        self.assertFalse(plan.build, "a documentation edit must not trigger a build")

    def test_art_change_builds_and_validates_but_never_boots_the_engine(self):
        decision = verify.decide(
            ["assets/textures/soviet_base/SDCONC2.png", "tools/art/gen_soviet_base.py"], MAPS)
        self.assertEqual(L.ART, decision.level)
        plan = verify.plan_for(decision.level, decision.maps)
        self.assertTrue(plan.build and plan.check_pk3 and plan.tests and plan.slow_art)
        self.assertFalse(plan.engine)

    def test_zscript_change_goes_full_with_every_map(self):
        decision = verify.decide(["src/zscript/weapons/rpg7.zs"], MAPS)
        self.assertEqual(L.FULL, decision.level)
        self.assertEqual(MAPS, decision.maps)

    def test_mixed_change_takes_the_highest_level(self):
        decision = verify.decide(
            ["docs/PRD.md", "tests/test_build.py", "assets/flats/soviet_base/SDFLR1.png",
             "src/lumps/MAPINFO"], MAPS)
        self.assertEqual(L.FULL, decision.level)

    def test_docs_plus_tests_is_fast_not_full(self):
        decision = verify.decide(["docs/PIPELINE.md", "tests/test_verify.py"], MAPS)
        self.assertEqual(L.FAST, decision.level)

    def test_docs_plus_art_is_art(self):
        decision = verify.decide(["docs/art/TEXTURE-INDEX.md", "assets/flats/x/SDFLR1.png"], MAPS)
        self.assertEqual(L.ART, decision.level)

    def test_nothing_changed_is_the_cheapest_level(self):
        self.assertEqual(L.DOCS, verify.decide([], MAPS).level)
        self.assertTrue(verify.decide([], MAPS).is_empty)

    def test_every_decision_carries_a_stated_reason(self):
        decision = verify.decide(["src/zscript/sd/player.zs", "docs/PRD.md"], MAPS)
        self.assertEqual(2, len(decision.reasons))
        # The rule that set the level is reported first.
        self.assertEqual(L.FULL, decision.reasons[0].rule.level)
        for reason in decision.reasons:
            self.assertTrue(reason.rule.why.strip(), f"{reason.rule.id} has no reason")
            self.assertGreater(len(reason.rule.why), 30, "a reason must be a sentence")

    def test_reason_counts_the_paths_it_speaks_for(self):
        decision = verify.decide(
            ["docs/a.md", "docs/b.md", "docs/c.md"], MAPS)
        self.assertEqual(1, len(decision.reasons))
        self.assertEqual(3, decision.reasons[0].count)
        self.assertEqual("docs/a.md", decision.reasons[0].example)


class NoiseTests(unittest.TestCase):
    """An editor dropping must never cost somebody a GZDoom window."""

    def test_ds_store_and_pycache_are_ignored(self):
        noisy = ["src/.DS_Store", "src/maps/.DS_Store",
                 "src/maps/MAP01/__pycache__/map.cpython-314.pyc",
                 "tools/art/__pycache__/artlib.cpython-314.pyc"]
        decision = verify.decide(noisy, MAPS)
        self.assertEqual(L.DOCS, decision.level)
        self.assertTrue(decision.is_empty)
        self.assertEqual(len(noisy), len(decision.ignored))

    def test_noise_does_not_hide_a_real_change(self):
        decision = verify.decide(["src/.DS_Store", "docs/PRD.md"], MAPS)
        self.assertEqual(L.DOCS, decision.level)
        self.assertEqual(("docs/PRD.md",), decision.paths)

    def test_noise_next_to_an_engine_change_still_goes_full(self):
        decision = verify.decide(["src/.DS_Store", "src/zscript/sd/ammo.zs"], MAPS)
        self.assertEqual(L.FULL, decision.level)


class EngineMapTests(unittest.TestCase):
    def test_a_change_confined_to_one_map_boots_only_that_map(self):
        decision = verify.decide(["src/maps/MAP02/map.py"], MAPS)
        self.assertEqual(L.FULL, decision.level)
        self.assertEqual(("MAP02",), decision.maps)

    def test_two_maps_boot_two_maps(self):
        decision = verify.decide(["src/maps/MAP01/map.py", "src/maps/MAP02/map.py"], MAPS)
        self.assertEqual(MAPS, decision.maps)

    def test_a_global_engine_change_boots_every_map(self):
        for path in ("src/lumps/MAPINFO", "src/zscript/sd/player.zs",
                     "tools/sdbuild/pk3.py", "tools/build.py"):
            decision = verify.decide([path, "src/maps/MAP02/map.py"], MAPS)
            self.assertEqual(MAPS, decision.maps, f"{path} must not be narrowed to one map")

    def test_an_unknown_path_boots_every_map(self):
        self.assertEqual(MAPS, verify.decide(["Makefile"], MAPS).maps)

    def test_maps_are_empty_below_full(self):
        self.assertEqual((), verify.decide(["assets/x/SDFLR1.png"], MAPS).maps)

    def test_discover_maps_finds_the_real_ones(self):
        found = verify.discover_maps()
        self.assertIn("MAP01", found, "src/maps/MAP01 exists in this repo")
        self.assertEqual(sorted(found), list(found), "map order must be stable")

    def test_discover_maps_ignores_non_map_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MAP01").mkdir()
            (root / "MAP07").mkdir()
            (root / "scratch").mkdir()
            (root / "__pycache__").mkdir()
            self.assertEqual(("MAP01", "MAP07"), verify.discover_maps(root))

    def test_discover_maps_on_a_missing_directory(self):
        self.assertEqual((), verify.discover_maps(Path("/nope/does/not/exist")))


class PorcelainTests(unittest.TestCase):
    """`git status --porcelain=v1 -z -uall` output, including the nasty bits."""

    def test_plain_modifications_and_untracked(self):
        data = " M docs/PRD.md\0?? tools/verify.py\0M  src/lumps/MAPINFO\0"
        self.assertEqual(
            ["docs/PRD.md", "tools/verify.py", "src/lumps/MAPINFO"],
            verify.parse_porcelain(data),
        )

    def test_a_rename_yields_both_sides(self):
        """-z writes the original path as its OWN record after the new one."""
        data = "R  docs/NEW.md\0docs/OLD.md\0 M README.md\0"
        self.assertEqual(
            ["docs/NEW.md", "docs/OLD.md", "README.md"],
            verify.parse_porcelain(data),
        )

    def test_a_copy_yields_both_sides(self):
        data = "C  docs/COPY.md\0docs/SRC.md\0"
        self.assertEqual(["docs/COPY.md", "docs/SRC.md"], verify.parse_porcelain(data))

    def test_deleted_files_still_count_as_changed(self):
        self.assertEqual(["src/zscript/gone.zs"],
                         verify.parse_porcelain(" D src/zscript/gone.zs\0"))

    def test_paths_with_spaces_survive(self):
        data = "?? work/art/a sweep sheet.png\0"
        self.assertEqual(["work/art/a sweep sheet.png"], verify.parse_porcelain(data))

    def test_empty_output_is_no_changes(self):
        self.assertEqual([], verify.parse_porcelain(""))
        self.assertEqual([], verify.parse_porcelain("\0\0"))

    def test_a_rename_of_a_zscript_file_still_reaches_full(self):
        paths = verify.parse_porcelain("R  src/zscript/b.zs\0src/zscript/a.zs\0")
        self.assertEqual(L.FULL, verify.decide(paths, MAPS).level)


class MirrorTests(unittest.TestCase):
    """D7: the one rule about documents that a script can actually check."""

    def test_mirror_path_both_ways(self):
        self.assertEqual("docs/ru/art/ART-BIBLE.md", verify.mirror_path("docs/art/ART-BIBLE.md"))
        self.assertEqual("docs/art/ART-BIBLE.md", verify.mirror_path("docs/ru/art/ART-BIBLE.md"))

    def test_root_documents_and_non_markdown_have_no_mirror_duty(self):
        for path in ("README.md", "CLAUDE.md", "src/lumps/MAPINFO",
                     "docs/art/palette.json", "work/notes.md"):
            self.assertIsNone(verify.mirror_path(path), path)

    def test_a_missing_mirror_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "A.md").write_text("x")
            self.assertEqual(["docs/A.md -> docs/ru/A.md"],
                             verify.mirror_gaps(["docs/A.md"], root))

    def test_a_present_mirror_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "ru").mkdir(parents=True)
            (root / "docs" / "A.md").write_text("x")
            (root / "docs" / "ru" / "A.md").write_text("x")
            self.assertEqual([], verify.mirror_gaps(["docs/A.md", "docs/ru/A.md"], root))

    def test_a_deleted_document_is_not_a_gap(self):
        """A path git reports as deleted no longer owes anybody a mirror."""
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual([], verify.mirror_gaps(["docs/GONE.md"], Path(tmp)))

    def test_changed_doc_without_mirror_fails_the_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "A.md").write_text("x")
            plan = verify.plan_for(L.DOCS, doc_paths=("docs/A.md",))
            result = verify.stage_docs(plan, root)
            self.assertFalse(result.ok)
            self.assertEqual(verify.EXIT_DOCS, result.exit_code)

    def test_whole_tree_scan_warns_instead_of_blocking(self):
        """Pre-existing mirror debt is reported loudly, not used to block
        an unrelated change; a mirror missing for a doc changed in THIS
        batch does block (test above)."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "A.md").write_text("x")
            result = verify.stage_docs(verify.plan_for(L.DOCS), root)
            self.assertTrue(result.ok)
            self.assertIn("WARN", result.note)


class ReferenceTests(unittest.TestCase):
    def test_a_dead_repo_path_in_a_document_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "A.md").write_text("see `tools/nope.py` for details\n")
            self.assertEqual(["docs/A.md: `tools/nope.py`"],
                             verify.broken_references(["docs/A.md"], root))

    def test_a_live_repo_path_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "tools").mkdir()
            (root / "tools" / "yes.py").write_text("")
            (root / "docs" / "A.md").write_text("see `tools/yes.py`\n")
            self.assertEqual([], verify.broken_references(["docs/A.md"], root))

    def test_shell_fragments_and_globs_are_not_treated_as_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "A.md").write_text(
                "run `python3 -m venv .venv` then `docs/ru/*.md` and `a/b`\n")
            self.assertEqual([], verify.broken_references(["docs/A.md"], root))

    def test_it_survives_the_real_docs_tree(self):
        """Every document in the repo, for crashes and for encoding.

        It deliberately does NOT assert an empty result: at the time this
        was written `docs/PIPELINE.md` cited `docs/ru/PIPELINE.md`, which
        does not exist (bug Q1), and that is a finding to report, not a
        reason for this suite to be red forever.
        """
        found = verify.broken_references(verify.all_docs(PROJECT_ROOT), PROJECT_ROOT)
        self.assertIsInstance(found, list)
        for entry in found:
            self.assertIn(": `", entry, "a finding must name the document and the path")


class CliTests(unittest.TestCase):
    def _run(self, argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = verify.main(argv)
        return code, buffer.getvalue()

    def test_explain_runs_nothing_and_says_so(self):
        code, out = self._run(["auto", "--files", "src/zscript/sd/player.zs", "--explain"])
        self.assertEqual(verify.EXIT_OK, code)
        self.assertIn("nothing was run", out)
        self.assertIn("full", out)
        self.assertIn("only GZDoom parses ZScript", out)

    def test_explain_on_a_documentation_change_promises_no_build(self):
        code, out = self._run(["auto", "--files", "docs/PRD.md", "docs/ru/PRD.md", "--explain"])
        self.assertEqual(verify.EXIT_OK, code)
        self.assertIn("plan: docs", out)
        self.assertNotIn("build", out)
        self.assertNotIn("smoke", out)

    def test_explain_names_the_maps_it_would_boot(self):
        code, out = self._run(["auto", "--files", "src/maps/MAP02/map.py", "--explain"])
        self.assertEqual(verify.EXIT_OK, code)
        self.assertIn("smoke MAP02", out)
        self.assertNotIn("MAP01", out)

    def test_explain_for_an_explicit_level_needs_no_git(self):
        code, out = self._run(["fast", "--explain"])
        self.assertEqual(verify.EXIT_OK, code)
        self.assertIn("plan: fast", out)
        self.assertNotIn("smoke", out)

    def test_auto_explains_before_it_decides(self):
        """The decision line must come before the plan line, so a reader
        sees the evidence before the verdict."""
        _code, out = self._run(["auto", "--files", "tests/test_verify.py", "--explain"])
        self.assertLess(out.index("auto:"), out.index("plan:"))

    def test_an_unknown_level_is_a_usage_error(self):
        # argparse writes its usage to stderr; swallow it so a passing
        # suite stays readable.
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            verify.parse_args(["turbo"])
        self.assertEqual(verify.EXIT_USAGE, ctx.exception.code)

    def test_explicit_maps_override_the_decision(self):
        _code, out = self._run(
            ["auto", "--files", "src/zscript/sd/player.zs", "--maps", "map01", "--explain"])
        self.assertIn("smoke MAP01", out)
        self.assertNotIn("MAP02", out)


class ExitCodeTests(unittest.TestCase):
    def test_every_stage_has_its_own_code(self):
        codes = [verify.EXIT_DOCS, verify.EXIT_BUILD, verify.EXIT_CHECK_PK3,
                 verify.EXIT_TESTS, verify.EXIT_ENGINE]
        self.assertEqual(len(codes), len(set(codes)), "stage exit codes collide")
        self.assertNotIn(verify.EXIT_OK, codes)
        self.assertNotIn(verify.EXIT_USAGE, codes)
        self.assertNotIn(verify.EXIT_NO_GIT, codes)

    def test_stage_codes_are_above_the_shell_reserved_range(self):
        for code in (verify.EXIT_DOCS, verify.EXIT_BUILD, verify.EXIT_CHECK_PK3,
                     verify.EXIT_TESTS, verify.EXIT_ENGINE):
            self.assertGreater(code, 3)
            self.assertLess(code, 126, "126+ belongs to the shell")


class StageFailureTests(unittest.TestCase):
    """A verification tool that tracebacks is worse than no tool."""

    def test_a_missing_interpreter_is_a_red_stage_not_a_traceback(self):
        result = verify.stage_build("/nope/does/not/exist/python")
        self.assertFalse(result.ok)
        self.assertEqual(verify.EXIT_BUILD, result.exit_code)
        self.assertIn("could not run", result.output)

    def test_a_failing_stage_does_not_claim_it_produced_output(self):
        """`build FAIL ... dist/sovietdoom.pk3` read as if the PK3 existed."""
        result = verify.stage_build("/nope/does/not/exist/python")
        self.assertNotIn("dist/sovietdoom.pk3", result.note)
        self.assertIn("exit", result.note)

    def test_run_reports_oserror_as_exit_127(self):
        code, out, _secs = verify._run(["/nope/does/not/exist"])
        self.assertEqual(127, code)
        self.assertIn("No such file", out)


class SmokeWindowTests(unittest.TestCase):
    """tools/smoke.py was changed for the window; guard what was verified."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(PROJECT_ROOT / "tools"))
        import smoke  # noqa: PLC0415
        cls.smoke = smoke

    def _cmd(self, **kw):
        defaults = dict(
            gzdoom=Path("/bin/gzdoom"), iwad=Path("/w/freedoom2.wad"),
            pk3=Path("/d/sovietdoom.pk3"), log=Path("/l/smoke.log"),
            shot_dir=Path("/l/shots"),
        )
        defaults.update(kw)
        return self.smoke.build_command(**defaults)

    def test_the_window_is_small_and_windowed_by_default(self):
        cmd = self._cmd()
        self.assertEqual("0", cmd[cmd.index("+vid_fullscreen") + 1])
        self.assertEqual(str(self.smoke.SMOKE_WINDOW_W), cmd[cmd.index("+win_w") + 1])
        self.assertEqual(str(self.smoke.SMOKE_WINDOW_H), cmd[cmd.index("+win_h") + 1])

    def test_the_engine_does_not_pause_when_it_loses_focus(self):
        """GZDoom steals focus on macOS and no flag stops it; the least we
        can do is let the run finish when the user clicks away, instead of
        hanging on `wait N` until the smoke timeout kills it."""
        cmd = self._cmd()
        self.assertEqual("0", cmd[cmd.index("+i_pauseinbackground") + 1])

    def test_native_window_leaves_the_engine_geometry_alone(self):
        cmd = self._cmd(window=None)
        self.assertNotIn("+win_w", cmd)
        self.assertNotIn("+win_h", cmd)
        self.assertIn("+i_pauseinbackground", cmd)

    def test_window_argument_parsing(self):
        self.assertEqual((640, 400), self.smoke.parse_window("640x400"))
        self.assertEqual((640, 400), self.smoke.parse_window(" 640 X 400 "))
        self.assertIsNone(self.smoke.parse_window("native"))

    def test_a_bad_window_argument_is_a_usage_error(self):
        import argparse  # noqa: PLC0415
        with self.assertRaises(argparse.ArgumentTypeError):
            self.smoke.parse_window("huge")

    def test_extra_args_still_come_last(self):
        """verify.py and the four-greens habit both append engine args."""
        cmd = self._cmd(extra=["+vid_fps", "1"])
        self.assertEqual(["+vid_fps", "1"], cmd[-2:])


class PipelineDocTests(unittest.TestCase):
    """docs/PIPELINE.md stage 5 is the contract this tool implements."""

    @classmethod
    def setUpClass(cls):
        path = PROJECT_ROOT / "docs" / "PIPELINE.md"
        if not path.is_file():
            raise unittest.SkipTest("docs/PIPELINE.md is absent")
        cls.text = path.read_text(encoding="utf-8")

    def test_stage_five_names_both_levels(self):
        self.assertIn("tools/verify.py fast", self.text)
        self.assertIn("tools/verify.py full", self.text)
        self.assertIn("tools/verify.py auto", self.text)

    def test_every_rule_in_the_tool_is_documented(self):
        for rule in verify.RULES:
            for prefix in rule.prefixes:
                self.assertIn(prefix, self.text,
                              f"rule '{rule.id}' matches {prefix} but PIPELINE.md never says so")

    def test_the_readme_points_at_the_tool(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("tools/verify.py", readme)


if __name__ == "__main__":
    unittest.main()
