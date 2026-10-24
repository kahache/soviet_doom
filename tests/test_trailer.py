"""Tests for the 60 s trailer tools (tools/trailer/, V3, D3, D132): everything
that can be checked without GZDoom (D26: capture.py's runs are the PM's).

Covered:
* shots.json and cards.json are valid: every shot, segment and card is
  well formed; the cut is ~60 s and counted in bars of the music (one bar of
  D_SDBS9A at 140 BPM is exactly 60 tics), each engine shot runs long enough
  after its roll for the segment that uses it;
* the brief's content is in the cut: the nine maps, every firearm (the
  RGD-5 with a fallback for a PK3 without it), the four bosses by their
  map things, the operations map and a medal (with still fallbacks);
* every card renders in every locale (EN, RU, CA) with glyphs the game's
  fonts have; map names come from LANGUAGE;
* the console sequences: under route.py's length limit, one roll each, the
  slate up for at least PREROLL_MIN_TICS, never the console `exit` (it
  quits GZDoom), `quit` last;
* the helper PK3 is tooling: it refuses src/, dist/ and assets/, carries
  route.py's handler plus the trailer camera, and names every class a shot
  spawns or hurts;
* capture.py refuses to launch with the engine gate shut, and --print runs
  without it; its FFmpeg command films the window's rectangle;
* edit.py finds the roll on a synthetic recording (the last magenta run);
* (geometry, slow: skipped at `verify.py fast`) every camera fits where it
  stands, every spawn lands where its body fits and in sight, every
  `look_at` subject is in sight and inside the view, every boss thing is
  where the shot expects it, on the maps built from src/maps/*/map.py.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRAILER_DIR = PROJECT_ROOT / "tools" / "trailer"
sys.path.insert(0, str(TRAILER_DIR))

import trailer_lib as tl  # noqa: E402
import capture  # noqa: E402

try:
    import numpy  # noqa: F401
    import PIL  # noqa: F401
    import edit  # noqa: E402
    HAVE_ART = True
except ImportError:  # the system python without the venv
    HAVE_ART = False

SLOW = os.environ.get("SD_SKIP_SLOW_ART") == "1"
TARGET_S, TOLERANCE_S = 60.0, 3.0
BOSS_THINGS = {21106: "MAP03", 21111: "MAP06", 21113: "MAP08", 21112: "MAP09"}
FIREARMS = ("SD_Tokarev", "SD_Izh", "SD_Ppsh", "SD_Akm", "SD_Rpg7", "SD_Roks3", "SD_HandKatyusha", "SD_Rgd5")


class ShotListTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tl.load_json(tl.SHOTS_JSON)
        cls.shots = tl.shots_by_id(cls.data)
        cls.names = tl.classes_used(cls.data)

    def test_valid(self):
        self.assertEqual(tl.validate_shots(self.data), [])

    def test_about_sixty_seconds(self):
        self.assertAlmostEqual(tl.total_seconds(self.data), TARGET_S, delta=TOLERANCE_S)

    def test_a_bar_is_sixty_tics(self):
        bar = tl.bar_seconds(self.data["music"]["main"])
        self.assertAlmostEqual(bar * tl.TICS_PER_SECOND, 60.0, places=6)

    def test_main_piece_is_covered_by_whole_bars(self):
        main = sum(s["bars"] for s in self.data["timeline"] if not s.get("intro"))
        self.assertEqual(main, 32)

    def test_engine_shots_run_long_enough(self):
        for start, end, seg in tl.timeline(self.data):
            shot = self.shots.get(seg.get("shot"))
            if shot and shot.kind == "engine":
                need = float(seg.get("from", 0)) + (end - start)
                self.assertLessEqual(need, tl.roll_tics(shot.data) / tl.TICS_PER_SECOND + 1e-6, seg)

    def test_every_map_appears(self):
        maps = {s.map for s in self.shots.values() if s.kind == "engine"}
        for n in range(1, 10):
            self.assertIn(f"MAP0{n}", maps)

    def test_every_firearm_is_fired(self):
        fired = set()
        for s in self.shots.values():
            if s.kind == "engine" and any(a.startswith("fire") for a in s.data["actions"]):
                fired.add(s.data.get("weapon"))
        self.assertEqual(set(FIREARMS) - fired, set())

    def test_v3_shots_have_fallbacks(self):
        for s in self.shots.values():
            if s.requires:
                self.assertIn("fallback", s.data, s.id)
                fb, notes = tl.resolve(s.data, available=set())
                self.assertTrue(fb, s.id)
                self.assertTrue(notes)
                self.assertNotIn("requires", fb)

    def test_resolve_keeps_a_shot_whose_classes_are_there(self):
        s = self.shots["S11"].data
        fb, notes = tl.resolve(s, available={"SD_Rgd5"})
        self.assertEqual(fb["weapon"], "SD_Rgd5")
        self.assertEqual(notes, [])

    def test_bosses_are_their_map_things(self):
        seen = {}
        for s in self.shots.values():
            if s.data.get("subject_thing"):
                ed = s.data["subject_thing"][0]
                seen[ed] = s.map
        self.assertEqual(seen, BOSS_THINGS)

    def test_ops_map_and_medal_are_composed_stills(self):
        """Filmed on 2026-10-25 the stats text covered the map for the whole
        shot (the console's +use cannot leave GZDoom 4.14's stats page), so
        both are composed from V3's own pictures and intermission script."""
        self.assertEqual(self.shots["S15"].data.get("opsmap"), "MAP08")
        self.assertEqual(self.shots["S16"].data.get("opsmap"), "MAP09")
        self.assertIn("SDAWCOU", self.shots["S16"].data["layers"][0]["image"])
        for sid in ("S15", "S16"):
            self.assertEqual(self.shots[sid].kind, "still")

    def test_calm_and_hold(self):
        cmds = tl.action_commands("spawn SD_Stormtrooper 224 0 hold", ["SD_Stormtrooper"])
        self.assertEqual(cmds[0], "netevent sdspawn 0 224 0 1")
        self.assertEqual(tl.action_commands("calm 500", [])[0], "netevent sdcalm 500")
        for bad in ("spawn SD_Stormtrooper 224 0 run", "calm 0", "calm x"):
            with self.assertRaises(tl.TrailerError):
                tl.parse_action(bad)
        for sid in ("S07", "S10", "S12", "S13", "S14"):
            self.assertTrue(any(a.startswith("calm ") for a in self.shots[sid].data["setup"]), sid)

    def test_sequences(self):
        for s in self.shots.values():
            if s.kind != "engine":
                continue
            for variant in [s.data] + ([dict(s.data, **s.data["fallback"])] if s.data.get("fallback") else []):
                if variant.get("kind", "engine") != "engine":
                    continue
                cmds = tl.shot_commands(variant, self.names)
                self.assertEqual(cmds.count("netevent sdroll"), 1, s.id)
                self.assertNotIn("exit", cmds, f"{s.id}: the console exit quits GZDoom")
                self.assertEqual(cmds[-1], "quit")
                self.assertEqual(cmds.count("quit"), 1)
                roll = cmds.index("netevent sdroll")
                pre = sum(int(c.split()[1]) for c in cmds[:roll] if c.startswith("wait "))
                self.assertGreaterEqual(pre, tl.PREROLL_MIN_TICS + tl.LOAD_TICS, s.id)
                tl.console_sequence(variant, self.names)   # under the limit, or raises

    def test_spawns_come_after_the_long_wait(self):
        cmds = tl.shot_commands(self.shots["S01"].data, self.names)
        first_spawn = next(i for i, c in enumerate(cmds) if c.startswith("netevent sdspawn"))
        tail = cmds[first_spawn:cmds.index("netevent sdroll")]
        waited = sum(int(c.split()[1]) for c in tail if c.startswith("wait "))
        self.assertLess(waited, tl.TICS_PER_SECOND)

    def test_bad_actions_are_refused(self):
        for bad in ("jump 3", "fire", "fire -2", "pan 10", "spawn SD_X", "run maybe", "wait x"):
            with self.assertRaises(tl.TrailerError, msg=bad):
                tl.parse_action(bad)

    def test_validation_catches_mistakes(self):
        broken = tl.load_json(tl.SHOTS_JSON)
        broken["shots"][1]["map"] = "MAP10"
        broken["timeline"][1]["bars"] = 40
        broken["timeline"][2]["cards"] = ["NO_SUCH_CARD"]
        errs = "\n".join(tl.validate_shots(broken))
        self.assertIn("MAP10", errs)
        self.assertIn("NO_SUCH_CARD", errs)
        self.assertIn("after the roll", errs)

    def test_engine_argv(self):
        shot = self.shots["S01"].data
        argv = tl.engine_argv(Path("gzdoom.exe"), Path("freedoom2.wad"), [Path("mod.pk3")], Path("h.pk3"),
                              Path("t.ini"), Path("l.log"), shot, self.names, (1280, 720), sound=False)
        self.assertEqual(argv[1:3], ["-config", "t.ini"])
        self.assertIn("-nosound", argv)
        self.assertLess(argv.index("mod.pk3"), argv.index("h.pk3"))
        i = argv.index("+screenblocks")
        self.assertEqual(argv[i + 1], "12")
        self.assertTrue(argv[-1].startswith("+wait"))


class CardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cards = tl.load_json(tl.CARDS_JSON)
        cls.strings = tl.language_strings()
        cls.data = tl.load_json(tl.SHOTS_JSON)

    def test_every_used_card_exists_in_every_locale(self):
        for cid, _a, _b in tl.card_windows(self.data):
            card = self.cards["cards"][cid]
            for loc in tl.LOCALES:
                lines = tl.card_lines(card, loc, self.strings)
                self.assertTrue(lines and all(lines), f"{cid} [{loc}]")

    def test_map_names_come_from_language(self):
        card = self.cards["cards"]["L_MAP06"]
        self.assertEqual(tl.card_lines(card, "ru", self.strings), [self.strings["ru"]["SD_MAP06_NAME"]])

    def test_every_glyph_exists(self):
        styles = self.cards["styles"]
        for cid, card in self.cards["cards"].items():
            font = styles[card["style"]]["font"]
            for loc in tl.LOCALES:
                for line in tl.card_lines(card, loc, self.strings):
                    text = line.replace("{version}", "V1.3").replace("{weapons}", "9")
                    self.assertEqual(tl.missing_glyphs(text, font), set(), f"{cid} [{loc}] {text!r}")
                if card.get("kicker"):
                    k = tl.card_lines({loc: [card["kicker"]]}, loc, self.strings)[0]
                    self.assertEqual(tl.missing_glyphs(k, styles["kicker"]["font"]), set(), cid)

    def test_end_card_names_the_download(self):
        for loc in tl.LOCALES:
            lines = tl.card_lines(self.cards["cards"]["E_END"], loc, self.strings)
            self.assertIn("GITHUB.COM/KAHACHE/SOVIET_DOOM", lines)
            self.assertIn("{version}", lines)

    def test_end_card_credits_engelbach(self):
        """D_SDINTL plays under the title: his sequence must be credited (MUSIC-RIGHTS 4.4)."""
        self.assertIn("D_SDINTL", self.data["music"]["intro"]["file"])
        credit = self.cards["cards"]["E_END"]["credit"]
        for loc in tl.LOCALES:
            self.assertIn("ENGELBACH", credit[loc])
            self.assertEqual(tl.missing_glyphs(credit[loc], self.cards["styles"]["credit"]["font"]), set())

    def test_end_card_runs_into_the_tail(self):
        end = [w for w in tl.card_windows(self.data) if w[0] == "E_END"][0]
        self.assertAlmostEqual(end[2], tl.total_seconds(self.data), places=6)

    @unittest.skipUnless(HAVE_ART, "needs the venv (numpy, Pillow)")
    def test_every_card_reads_for_a_second(self):
        for cid, a, b in tl.card_windows(self.data):
            fade = min(edit.CARD_FADE_S, (b - a) / 4)
            self.assertGreaterEqual(b - a - 2 * fade, 1.0, cid)

    def test_spanned_card(self):
        win = [w for w in tl.card_windows(self.data) if w[0] == "C_FEATURES"][0]
        bar = tl.bar_seconds(self.data["music"]["main"])
        self.assertAlmostEqual(win[2] - win[1], 2 * bar, places=6)


class HelperTests(unittest.TestCase):
    def test_refuses_the_mod_trees(self):
        for root in ("src", "dist", "assets"):
            with self.assertRaises(tl.TrailerError):
                tl.write_helper_pk3(["SD_General"], PROJECT_ROOT / root / "x.pk3")

    def test_contents(self):
        names = tl.classes_used(tl.load_json(tl.SHOTS_JSON))
        with tempfile.TemporaryDirectory() as d:
            out = tl.write_helper_pk3(names, Path(d) / "h.pk3")
            with zipfile.ZipFile(out) as zf:
                z = zf.read("zscript.txt").decode()
                mi = zf.read("MAPINFO").decode()
        self.assertEqual(z.count('version "'), 1)
        for cls in ("SDRouteHelper", "SDRouteState", "SDTrailerHelper"):
            self.assertIn(f"class {cls}", z)
            self.assertIn(f'"{cls}"', mi)
        for n in names:
            self.assertIn(f'"{n}"', z)
        for event in ("sdroll", "sdview", "sdpan", "sdtilt", "sdspawn", "sdthurt"):
            self.assertIn(f'"{event}"', z)


class CaptureTests(unittest.TestCase):
    def test_gate_shut(self):
        env = {k: v for k, v in os.environ.items() if k != "SD_ALLOW_ENGINE"}
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(capture.subprocess, "Popen") as popen, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(capture.main(["--shots", "S01", "--no-build"]), capture.EXIT_BLOCKED)
            popen.assert_not_called()

    def test_print_needs_no_engine(self):
        env = {k: v for k, v in os.environ.items() if k != "SD_ALLOW_ENGINE"}
        out = io.StringIO()
        with mock.patch.dict(os.environ, env, clear=True), \
                mock.patch.object(capture.subprocess, "Popen") as popen, contextlib.redirect_stdout(out):
            self.assertEqual(capture.main(["--print", "--shots", "S01", "S15"]), 0)
            popen.assert_not_called()
        self.assertIn("gdigrab", out.getvalue())
        self.assertIn("netevent sdroll", out.getvalue())

    def test_ffmpeg_command(self):
        cmd = capture.ffmpeg_command(Path("ffmpeg"), (320, 180, 1280, 720), 60, Path("o.mkv"), None)
        self.assertIn("gdigrab", cmd)
        self.assertEqual(cmd[cmd.index("-offset_x") + 1], "320")
        self.assertEqual(cmd[cmd.index("-video_size") + 1], "1280x720")
        self.assertNotIn("dshow", cmd)
        cmd = capture.ffmpeg_command(Path("ffmpeg"), (0, 0, 1280, 720), 60, Path("o.mkv"), "What U Hear")
        self.assertIn("audio=What U Hear", cmd)


@unittest.skipUnless(HAVE_ART, "needs the venv (numpy, Pillow)")
class EditTests(unittest.TestCase):
    def test_roll_is_the_end_of_the_last_slate(self):
        import numpy as np
        f = np.zeros((10, 18, 32, 3), np.uint8)
        f[2:6] = tl.SLATE_RGB
        mask = edit.slate_mask(f)
        self.assertEqual(list(mask[:7]), [False, False, True, True, True, True, False])
        self.assertEqual(edit.roll_index(mask), 6)
        self.assertIsNone(edit.roll_index(edit.slate_mask(np.zeros((5, 18, 32, 3), np.uint8))))

    def test_render_line_is_the_font_scaled(self):
        img = edit.render_line("СССР", "bigfont", 3)
        self.assertEqual(img.height, 36)
        with self.assertRaises(tl.TrailerError):
            edit.render_line("一", "bigfont", 1)


@unittest.skipIf(SLOW, "geometry: builds nine maps (art and full tiers)")
class GeometryTests(unittest.TestCase):
    def test_every_shot_against_its_map(self):
        self.assertEqual(tl.check_geometry(tl.load_json(tl.SHOTS_JSON)), [])

    def test_the_check_catches_a_monster_on_the_lens(self):
        """The first cut's Red Square: a Panzermensch 32 units from the camera."""
        data = tl.load_json(tl.SHOTS_JSON)
        s07 = [s for s in data["shots"] if s["id"] == "S07"][0]
        data["shots"] = [dict(s07, setup=[])]
        errs = " | ".join(tl.check_geometry(data))
        self.assertIn("thing 21105 at (2450, 2000) is 32 units", errs)

    def test_the_check_catches_a_camera_in_a_wall(self):
        data = tl.load_json(tl.SHOTS_JSON)
        data["shots"] = [dict(s, warp=[-500, -500]) for s in data["shots"] if s["id"] == "S01"]
        self.assertTrue(tl.check_geometry(data))


if __name__ == "__main__":
    unittest.main()
