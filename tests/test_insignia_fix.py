"""tools/art/insignia_fix.py (V3, 2026-10-27): each faction's insignia on the same arm in every rotation.

Pure functions on synthetic arrays (no Gemini sheet needed): the rotation geometry (which arm a mark is
on, which arm a rotation shows), the plan (erase, move to the other arm whole or as its edge, convert
in place, leave a hidden arm alone), the repaint (the fill stays inside the silhouette, a paste never
leaves it), the finders (a band, a flag, a cape stripe that is neither), the hook in gemini_enemy (off
by default), and the install script's edit of the Chrome Marshal (every state on SDCM, none on SDGN).
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    import gemini_enemy as ge
    import insignia_fix as fx
except ImportError:   # CI's stdlib-only interpreter
    fx = None

L, R = "L", "R"


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class GeometryTests(unittest.TestCase):
    def test_front_and_back_by_side(self):
        self.assertEqual(fx.arm_of(1, +10), L)     # facing us: his left arm is on the viewer's right
        self.assertEqual(fx.arm_of(1, -10), R)
        self.assertEqual(fx.arm_of(5, -10), L)     # his back: his left arm on the viewer's left
        self.assertEqual(fx.arm_of(5, +10), R)

    def test_three_quarter_views_mirror_each_other(self):
        for r, m in ((2, 8), (4, 6)):
            for dx in (-30, 30):
                a = fx.arm_of(r, dx, 100)
                self.assertNotEqual(fx.arm_of(m, -dx, 100), a)   # the mirror puts the mark on the other arm
                self.assertEqual(fx.arm_of(m, dx, 100), a)       # the same side of the axis: the same arm

    def test_a_profile_shows_its_near_arm(self):
        self.assertEqual(fx.arm_of(3, 40), L)
        self.assertEqual(fx.arm_of(7, -40), R)
        self.assertEqual(fx.arm_of(3, 40, forward=True), R)   # the aiming rifleman: the far arm reaches forward
        self.assertTrue(fx.visible(3, L) and not fx.visible(3, R))
        self.assertTrue(fx.visible(7, R) and not fx.visible(7, L))
        self.assertTrue(fx.visible(2, R) and fx.visible(1, R))

    def test_near_slack_in_a_three_quarter_view(self):
        self.assertEqual(fx.arm_of(2, -5, 100), L)       # just past the axis: still the near arm
        self.assertEqual(fx.arm_of(2, -40, 100), R)

    def test_far_arm_of_a_three_quarter_view(self):
        self.assertTrue(fx.is_far(6, L) and fx.is_far(8, L) and fx.is_far(2, R) and fx.is_far(4, R))
        self.assertFalse(fx.is_far(6, R) or fx.is_far(1, L) or fx.is_far(7, L))

    def test_the_rule(self):
        self.assertEqual(fx.RULE["rifleman"], {fx.REICH: L})
        self.assertEqual(fx.RULE["legion"], {fx.US: R})
        self.assertEqual(fx.RULE["general"], {fx.REICH: L, fx.US: R})
        self.assertNotIn(fx.REICH, fx.RULE["marshal"])          # D123: a Legion boss wears no armband
        self.assertEqual(fx.REPLACE["marshal"], {fx.REICH: fx.US})


def mark(kind, cx, cy=10.0, shape=(40, 60)):
    region = np.zeros(shape, bool)
    region[int(cy) - 2:int(cy) + 2, int(cx) - 2:int(cx) + 2] = True
    return fx._mark(kind, region)


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class PlanTests(unittest.TestCase):
    AX = 30.0

    def ops(self, enemy, rot, marks):
        return [(o.what, o.kind, o.far) for o in fx.plan(enemy, rot, marks, self.AX, width=60).ops]

    def test_a_right_mark_is_left_alone(self):
        self.assertEqual(self.ops("rifleman", 1, [mark(fx.REICH, 45)]), [])

    def test_mirrored_three_quarter_moves_to_the_far_arm_edge(self):
        # rotation 6: the band on the viewer's right is his right arm; it goes to his (far) left arm
        got = self.ops("rifleman", 6, [mark(fx.REICH, 45)])
        self.assertEqual(got, [("erase", fx.REICH, False), ("move", fx.REICH, True)])
        op = fx.plan("rifleman", 6, [mark(fx.REICH, 45)], self.AX, width=60).ops[1]
        self.assertAlmostEqual(op.at[1], 2 * self.AX - 44.5, places=3)      # the mirror place about the axis

    def test_a_mirrored_profile_only_erases(self):
        self.assertEqual(self.ops("rifleman", 7, [mark(fx.REICH, 20)]), [("erase", fx.REICH, False)])

    def test_the_legion_moves_to_the_near_arm_whole(self):
        # rotation 6: a flag on the viewer's left is his left arm; his right arm is the near one
        self.assertEqual(self.ops("legion", 6, [mark(fx.US, 12)]), [("erase", fx.US, False), ("move", fx.US, False)])

    def test_the_general_swaps_in_place(self):
        self.assertEqual(self.ops("general", 1, [mark(fx.US, 45)]), [("convert", fx.REICH, False)])
        self.assertEqual(self.ops("general", 8, [mark(fx.REICH, 15)]), [("convert", fx.US, False)])
        self.assertEqual(self.ops("general", 7, [mark(fx.US, 20)]), [])

    def test_the_marshal_turns_every_armband_into_the_flag(self):
        for rot, cx in ((1, 45), (2, 45), (5, 15), (0, 30)):
            self.assertEqual(self.ops("marshal", rot, [mark(fx.REICH, cx)]), [("convert", fx.US, False)])

    def test_no_second_band_on_an_arm_that_has_one(self):
        # Gemini drew a band on each arm (the Panzermensch's fire): the wrong one only goes
        got = self.ops("panzer", 1, [mark(fx.REICH, 45), mark(fx.REICH, 15)])
        self.assertEqual(got, [("erase", fx.REICH, False)])


def figure(shape=(100, 60), colour=(110, 100, 70)):
    rgb = np.zeros(shape + (3,), np.uint8)
    rgb[:] = colour
    mask = np.zeros(shape, bool)
    mask[4:96, 10:50] = True
    return rgb, mask


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class RepaintTests(unittest.TestCase):
    def test_erase_refills_from_the_sleeve_and_nothing_else_moves(self):
        rgb, mask = figure()
        rgb[15:22, 30:40] = (190, 20, 20)
        rgb[17:20, 33:37] = (240, 235, 230)            # the field
        region = np.zeros_like(mask)
        region[15:22, 30:40] = True
        out = fx.erase(rgb, mask, region)
        self.assertFalse((fx.red_loose(out) & mask).any())
        far = ~ge._dilate(region, fx.ERASE_REACH + fx.ERASE_GROW + 1)
        self.assertTrue((out[far] == rgb[far]).all())
        self.assertTrue(np.abs(out[18, 35].astype(int) - (110, 100, 70)).max() < 12)

    def test_paste_stays_inside_the_silhouette(self):
        rgb, mask = figure()
        p = fx.Patch(np.full((6, 30, 3), (200, 10, 10), np.uint8), np.ones((6, 30), bool))
        out, done = fx.paste(rgb, mask, p, 20, 50)
        self.assertFalse((done & ~mask).any())
        self.assertTrue(done.any())
        self.assertTrue((out[~mask] == rgb[~mask]).all())

    def test_a_far_sliver_keeps_the_outer_side_and_no_field(self):
        p = fx.Patch(np.full((6, 10, 3), (200, 10, 10), np.uint8), np.ones((6, 10), bool))
        p.rgb[2:4, 3:7] = (245, 240, 235)
        s = fx.sliver(p, +1)
        self.assertFalse(s.mask[:, :10 - round(10 * fx.SLIVER)].any())
        self.assertTrue(s.mask[:, -1].all())
        self.assertFalse(ge.white_mask(s.rgb, fx.FIELD_WHITE)[s.mask].any())

    def test_window_box_follows_the_mirror(self):
        _rgb, mask = figure()
        a = fx.window_box(mask, (0.0, 0.25, 0.25, 0.5), False)
        b = fx.window_box(mask, (0.0, 0.25, 0.25, 0.5), True)
        self.assertEqual(a[1], 10)
        self.assertEqual(b[3], 50)
        self.assertEqual((a[0], a[2]), (b[0], b[2]))


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class FinderTests(unittest.TestCase):
    def test_a_band_with_its_field(self):
        rgb, mask = figure()
        rgb[40:48, 38:46] = (180, 15, 15)
        rgb[42:46, 40:44] = (235, 230, 225)
        ms = fx.find_marks(rgb, mask)
        self.assertEqual([m.kind for m in ms], [fx.REICH])
        self.assertTrue(ms[0].region[43, 41])

    def test_a_flag(self):
        rgb, mask = figure(colour=(180, 182, 186))
        rgb[40:44, 36:40] = (50, 60, 150)               # canton
        for y in range(40, 48, 2):
            rgb[y, 40:46] = (190, 30, 30)               # stripes
        ms = fx.find_marks(rgb, mask)
        self.assertEqual([m.kind for m in ms], [fx.US])

    def test_a_tall_stripe_is_a_cape_not_a_band(self):
        rgb, mask = figure()
        rgb[5:35, 20:24] = (190, 20, 20)
        rgb[5:35, 24:27] = (240, 238, 236)
        self.assertEqual(fx.find_marks(rgb, mask), [])

    def test_the_legion_ignores_red_and_white(self):
        rgb, mask = figure()
        rgb[14:22, 38:46] = (180, 15, 15)
        rgb[16:20, 40:44] = (235, 230, 225)
        self.assertEqual(fx.marks_of("legion", ("turn", 0, False, False), rgb, mask, 1), [])


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class HookTests(unittest.TestCase):
    def test_no_retouch_by_default(self):
        import inspect
        self.assertIsNone(inspect.signature(ge.build).parameters["retouch"].default)
        self.assertIsNone(inspect.signature(ge.source_picture).parameters["retouch"].default)

    def test_the_hook_runs_after_the_mirror_inside_the_mask(self):
        rgb, mask = figure()
        rgb[:, :30] = (10, 200, 10)
        cut = ge.Cut(rgb, mask, "front", False, 0)
        seen = {}

        def retouch(key, r, m):
            seen["key"], seen["left"] = key, tuple(r[20, 15])
            return r
        ge.source_picture(cut, mirror=True, retouch=retouch, key=("turn", 0, True, False))
        self.assertEqual(seen["key"], ("turn", 0, True, False))
        self.assertEqual(seen["left"], (110, 100, 70))     # mirrored before the hook
        plain = ge.source_picture(cut, mirror=True)[0]
        self.assertTrue((plain == ge.source_picture(cut, mirror=True, retouch=lambda k, r, m: r)[0]).all())

    def test_retouch_of_keeps_an_untouched_picture(self):
        rgb, mask = figure()
        self.assertIs(fx.retouch_of({})(("x", 0, False, False), rgb, mask), rgb)


@unittest.skipIf(fx is None, "art venv (numpy, Pillow) missing")
class InstallTests(unittest.TestCase):
    def test_the_marshal_edit_moves_every_state_to_sdcm(self):
        text = (ROOT / "src" / "zscript" / "monsters" / "chrome_general.zs").read_text(encoding="utf-8")
        cmd = re.search(r"sed -i -E 's/(.+?)/(.+?)/' src/zscript/monsters/chrome_general\.zs", fx.INSTALL_TAIL)
        self.assertIsNotNone(cmd)
        pat = cmd.group(1).replace("\\t", "\t")
        rep = cmd.group(2).replace("\\1", "\\g<1>")
        out = re.sub(pat, rep, text, flags=re.M)
        states = [ln for ln in out.splitlines() if re.match(r"^\t+SD[A-Z]{2} ", ln)]
        self.assertTrue(states)
        self.assertTrue(all(ln.strip().startswith("SDCM ") for ln in states))
        self.assertIn("SDGN", out)                 # the comment block keeps the history

    def test_the_script_copies_only_what_changed(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            work = Path(d)
            (work / "art" / "insignia_fix").mkdir(parents=True)
            reports = [{"enemy": "rifleman", "sprite": "SDRR", "folder": "rifleman", "changed": ["SDRRA6"]},
                       {"enemy": "storm", "sprite": "SDHS", "folder": "storm", "changed": []}]
            text = fx.install_script(work, reports).read_text(encoding="utf-8")
        self.assertIn('cp "$HERE/lumps/rifleman/"SDRR*.png assets/sprites/rifleman/', text)
        self.assertNotIn("SDHS", text)
        self.assertIn("CHROME_SPRITE", text)
        self.assertIn("docs/art/LICENSES.md", text)
        self.assertTrue(text.startswith("#!/usr/bin/env bash"))

    def test_every_marshal_lump_gets_a_licence_row(self):
        lumps = [f"SDCM{f}{r}" for f in "AB" for r in range(1, 9)] + ["SDCMH0"]
        text = fx.licenses_section([{"enemy": "marshal", "sprite": "SDCM", "folder": "chrome_marshal", "changed": lumps},
                                    {"enemy": "general", "sprite": "SDGN", "folder": "general", "changed": ["SDGNA1"]}])
        for lu in lumps:
            self.assertIn(f"`{lu}`", text)
        self.assertIn("`SDGN` (1 lumps)", text)


if __name__ == "__main__":
    unittest.main()
