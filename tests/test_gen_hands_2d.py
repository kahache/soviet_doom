"""Contract of tools/art/gen_hands_2d.py (F4, D52: the sergeant's hand drawn
in 2D pixel art, style E, on every weapon of the arsenal).

What is checked:

  no font      the module never rasterises text with a system font
  no edit      gen_weapon.draw_grip is swapped only inside handless() and
               is restored afterwards, even when the render raises; the
               module never writes gen_weapon.py
  freedoom     no Freedoom sprite is read outside the sheet builder
  letters      every held and flash frame each .zs shows is drawn, with
               the final names of MOD-SPEC 6.3; the flash is drawn for a
               held frame that exists; every drawn frame has a design per grip
  timeline     the game-speed animation follows the state machines: tics,
               A_GunFlash (also inside an action), A_ReFire, the IZh reload
  D52 poses    the TT-33 and PPSh-41 are raised from gen_weapon's poses
               (which stay as approved) until every hand's grip projects
               above the classic status bar; the TT kick is bigger
  axe          the ice axe has its own drawing per frame (the wrist turns),
               one of them the palm view
  palette      every opaque pixel is a palette.json colour, alpha is hard
  handless     the re-rendered weapon carries no hand material
  hand shows   every held frame has hand pixels above the status bar
  placement    held frames reach the bottom of the 320x200 weapon space,
               stay inside the authoring canvas, grAb follows Doom
  saving       the files land under their lump names with grAb and a
               metrics.json the draft overlay reads (hand E)
  sheet        the HTML embeds every frame key and resolves every image
  seed         the same frame renders identically twice

The renders (about 35 frames, twenty seconds) are skipped under
SD_SKIP_SLOW_ART, as verify.py fast sets it; the static checks always run.
"""

from __future__ import annotations

import ast
import html
import json
import os
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_hands_2d.py"
SLOW_SKIPPED = bool(os.environ.get("SD_SKIP_SLOW_ART"))
SCREEN_W, SCREEN_H = 320, 200
STATUSBAR_TOP = 168
WEAPONTOP = 32
MIN_HAND_ABOVE_BAR = 250        # px of hand above the classic bar, every held frame
GRIP_MARGIN = 10                # px: a raised grip's axis sits at least this far above the screen's bottom


class StaticTests(unittest.TestCase):
    def setUp(self):
        self.code = SOURCE.read_text(encoding="utf-8")

    def test_no_system_font(self):
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, self.code), pattern)

    def test_freedoom_only_on_the_sheet(self):
        tree = ast.parse(self.code)
        callers = set()
        for fn in ast.walk(tree):
            if isinstance(fn, ast.FunctionDef):
                for node in ast.walk(fn):
                    if isinstance(node, ast.Attribute) and node.attr in ("freedoom_sprite", "iwad_lumps"):
                        callers.add(fn.name)
        self.assertLessEqual(callers, {"build_sheet"})

    def test_gen_weapon_is_imported_not_written(self):
        self.assertNotRegex(self.code, r"gen_weapon\.py['\"]\s*\)\.write|open\([^)]*gen_weapon")

    def test_nothing_goes_to_assets(self):
        self.assertNotIn('"assets"', self.code)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class ContractTests(unittest.TestCase):
    """Cheap: state machines, names, designs, poses; no full render."""

    @classmethod
    def setUpClass(cls):
        import gen_hands_2d as h
        import gen_weapon as gw
        cls.h, cls.gw = h, gw
        cls.spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")

    def test_draw_grip_restored(self):
        original = self.gw.draw_grip
        with self.h.handless():
            self.assertIsNot(self.gw.draw_grip, original)
        self.assertIs(self.gw.draw_grip, original)
        with self.assertRaises(RuntimeError):
            with self.h.handless():
                raise RuntimeError("boom")
        self.assertIs(self.gw.draw_grip, original)

    def test_the_whole_arsenal(self):
        self.assertEqual(set(self.h.ARMS), {"ice_axe", "tt33", "izh", "ppsh", "rpg7", "roks3", "katyusha"})
        self.assertEqual(set(self.h.WEAPON_ORDER), set(self.h.ARMS))

    def test_every_zs_frame_has_a_pose_and_a_design(self):
        for key, arm in self.h.ARMS.items():
            held, flash = self.h.zs_letters(arm)
            with self.subTest(weapon=key):
                self.assertTrue(held)
                self.assertLessEqual(held, {p.frame for p in arm.poses})
                self.assertLessEqual(held | set(arm.extra), set(arm.designs))
                self.assertLessEqual(flash, set(arm.flash_on))
                self.assertLessEqual({arm.flash_on[c] for c in flash}, held)

    def test_letters_agree_with_gen_weapon(self):
        """gen_weapon's own reading of the five later weapons' .zs."""
        for key, gkey in (("tt33", "tt33"), ("izh", "izh"), ("rpg7", "rpg7"), ("roks3", "roks3"),
                          ("katyusha", "katyusha")):
            with self.subTest(weapon=key):
                self.assertEqual(self.h.zs_letters(self.h.ARMS[key]), tuple(self.gw.zs_letters(self.gw.WEAPONS[gkey])))

    def test_names_are_the_contract(self):
        rows = {"ice_axe": "| Ice axe", "tt33": "| TT-33", "izh": "| IZh-58", "ppsh": "| PPSh-41",
                "rpg7": "| RPG-7", "roks3": "| ROKS-3", "katyusha": "| Hand Katyusha"}
        for key, prefix in rows.items():
            arm = self.h.ARMS[key]
            row = next(ln for ln in self.spec.splitlines() if ln.startswith(prefix))
            with self.subTest(weapon=key):
                self.assertIn(f"`{arm.sprite}`", row)
                if arm.flash_sprite:
                    self.assertIn(f"`{arm.flash_sprite}`", row)

    def test_katyusha_is_variant_b(self):
        self.assertEqual(self.h.HK_VARIANT_2D, "B")         # D51
        self.assertIn(self.h.HK_VARIANT_2D, self.gw.HK3_VARIANT)

    @unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: this one renders the 3D weapons")
    def test_designs_match_the_grips(self):
        style = self.gw.HAND[self.h.STYLE_KEY]
        for key, arm in self.h.ARMS.items():
            for pose in arm.poses:
                if pose.frame not in arm.designs:
                    continue
                with self.subTest(weapon=key, frame=pose.frame):
                    with self.h.handless() as grips:
                        arm.render(style, pose)
                    self.assertEqual(len(grips), len(arm.designs[pose.frame]))

    def test_axe_draws_each_frame(self):
        """The wrist turns: every frame of the swing has its own drawing, and
        the raised frame shows the fist from its fingers."""
        d = self.h.AXE_DESIGNS
        self.assertEqual(len(set(d.values())), len(d))
        self.assertEqual(d["B"][0].view, "palm")
        rolls = [d[c][0].roll for c in "BCD"]
        self.assertTrue(any(r > 0 for r in rolls) and any(r < 0 for r in rolls), rolls)

    def test_d52_poses_raised_from_the_approved_ones(self):
        for mine, approved in ((self.h.TT_POSES_2D, self.gw.TT_POSES), (self.h.PPSH_POSES_2D, self.gw.PPSH_POSES)):
            for a, b in zip(mine, approved):
                self.assertEqual(a.frame, b.frame)
                self.assertLess(a.origin[1], b.origin[1])      # up on the screen
        # gen_weapon's own (approved) TT-33 pose is untouched
        self.assertEqual(self.gw.TT_POSES[0].origin, (7.0, 7.0, 20.0))

    @unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: this one renders the 3D weapons")
    def test_d52_grips_on_screen(self):
        """Every grip of the raised TT-33 and PPSh-41 (the shaft's axis, the
        middle of the fist) projects on screen, GRIP_MARGIN px above its
        bottom edge and inside the 320 columns, so the fist round it clears
        the status bar; in the approved poses the TT-33's grip (y 201) and the
        PPSh's right grip (y 278) were under the screen."""
        style = self.gw.HAND[self.h.STYLE_KEY]
        for key in ("tt33", "ppsh"):
            arm = self.h.ARMS[key]
            for pose in arm.poses:
                with self.h.handless() as grips:
                    arm.render(style, pose)
                for g in grips:
                    with self.subTest(weapon=key, frame=pose.frame, side=g.side):
                        self.assertTrue(0 <= g.at[0] < SCREEN_W and 0 <= g.at[1] < SCREEN_H - GRIP_MARGIN, g.at)
        with self.h.handless() as grips:
            self.gw.render_ppsh_frame(style, self.gw.PPSH_POSES[0])
        self.assertGreater(max(g.at[1] for g in grips), SCREEN_H)   # the approved pose: a hand off screen

    def test_tt_kick_exaggerated(self):
        elev = lambda p: -self.gw.unit(p.bore)[1]
        for c in (1, 2):
            self.assertGreater(elev(self.h.TT_POSES_2D[c]) - elev(self.h.TT_POSES_2D[0]),
                               elev(self.gw.TT_POSES[c]) - elev(self.gw.TT_POSES[0]))

    @unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: this one renders the 3D weapons")
    def test_slide_reprojects(self):
        style = self.gw.HAND[self.h.STYLE_KEY]
        with self.h.handless() as grips:
            self.gw.render_rpg7_frame(style, self.gw.RPG_POSES[0])
        g = grips[0]
        far = g.slid(10.0)
        self.assertLess(far.s, g.s)                 # further along the tube, further from the eye
        self.assertIs(g.slid(0.0), g)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class TimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_hands_2d as h
        cls.h = h

    def tl(self, key, shots=None):
        return self.h.fire_timeline(self.h.ARMS[key], shots)

    def test_tt33(self):
        # A4, B0 GunFlash, B6, C3, B3 ReFire (shown on the last shot only), then rest
        runs = self.tl("tt33", 1)
        self.assertEqual(sum(t for _, _, t in runs), 4 + 6 + 3 + 3 + self.h.READY_TICS)
        self.assertEqual(sum(t for _, f, t in runs if f == "A"), 5)          # PISF A 5
        self.assertEqual(runs[1][:2], ("B", "A"))
        two = self.tl("tt33", 2)
        self.assertEqual(sum(t for _, _, t in two), 2 * (4 + 6 + 3) + 3 + self.h.READY_TICS)

    def test_flash_from_inside_an_action(self):
        """The IZh calls A_GunFlash inside A_SD_FireIzh; the reload runs D C B A."""
        runs = self.tl("izh", 2)
        self.assertEqual(sum(1 for _, f, _ in runs if f == "A"), 2)
        held = "".join(h for h, _, _ in runs)
        self.assertIn("DCBA", held)

    def test_katyusha_flash(self):
        runs = self.tl("katyusha")
        self.assertEqual([(h, f, t) for h, f, t in runs if f], [("B", "A", 11), ("B", "B", 6)])

    def test_axe_swing(self):
        held = [h for h, _, _ in self.tl("ice_axe")]
        self.assertEqual(held, list("BCDCBA"))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
@unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: skipping the 2D-hand renders")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_hands_2d as h
        import gen_weapon as gw
        cls.h, cls.gw = h, gw
        cls.out = h.render_all()
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def rows(self, flash: bool):
        return [r for rows in self.out.values() for r in rows if r.flash == flash]

    def colours(self, rgba) -> set:
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_every_zs_frame_drawn_with_its_final_name(self):
        for key, rows in self.out.items():
            arm = self.h.ARMS[key]
            held, flash = self.h.zs_letters(arm)
            lumps = {r.lump for r in rows}
            with self.subTest(weapon=key):
                self.assertLessEqual({f"{arm.sprite}{c}0" for c in held}, lumps)
                self.assertLessEqual({f"{arm.flash_sprite}{c}0" for c in flash}, lumps)
                for r in rows:
                    self.assertRegex(r.lump, r"^SD[A-Z]{2}[A-Z]0$")
                    self.assertRegex(r.key, rf"^({arm.label}|{arm.flash_label})-\d+$")

    def test_palette_and_hard_alpha(self):
        for r in self.rows(False) + self.rows(True):
            with self.subTest(frame=r.key):
                self.assertTrue(set(np.unique(r.frame.rgba[..., 3])) <= {0, 255})
                self.assertLessEqual(self.colours(r.frame.rgba), self.palette)

    def test_handless_has_no_hand(self):
        hand_mats = {self.gw.MAT_ID[m] for m in self.h.HAND_MATERIALS}
        for r in self.rows(False):
            with self.subTest(frame=r.key):
                self.assertFalse(set(np.unique(r.bare.mat).tolist()) & hand_mats)

    def test_hand_shows_above_the_bar(self):
        for r in self.rows(False):
            with self.subTest(frame=r.key):
                self.assertGreater(r.hand_above_bar, MIN_HAND_ABOVE_BAR)

    def test_style_e_forearm(self):
        f = next(r.frame for r in self.out["ice_axe"] if r.letter == "A")
        got = self.colours(f.rgba)
        for mat in ("sleeve_field", "tel_white", "tel_blue", "glove_brown"):
            with self.subTest(material=mat):
                self.assertTrue(got & set(self.gw.MATERIALS[mat].colours()), mat)

    def test_placement(self):
        for r in self.rows(False):
            f = r.frame
            with self.subTest(frame=r.key):
                self.assertTrue(f.hud)
                self.assertGreaterEqual(f.top + f.rgba.shape[0], SCREEN_H)
                self.assertLess(f.top, STATUSBAR_TOP)
                self.assertLess(f.rgba.shape[1], self.gw.CANVAS_W - 8)
                lo, to = f.offsets()
                self.assertEqual(f.left, -lo)
                self.assertEqual(f.top, WEAPONTOP - to)

    def test_flash_on_screen(self):
        flat = {self.gw.MAT_ID[n] for n in self.gw.FLAT}
        for r in self.rows(True):
            f = r.frame
            with self.subTest(frame=r.key):
                used = set(np.unique(f.mat[f.rgba[..., 3] > 0]).tolist())
                self.assertLessEqual(used, flat)
                cx, cy = f.left + f.rgba.shape[1] / 2, f.top + f.rgba.shape[0] / 2
                self.assertTrue(0 <= cx < SCREEN_W and 0 <= cy < STATUSBAR_TOP, (cx, cy))

    def test_seed(self):
        r = next(r for r in self.out["tt33"] if r.letter == "A")
        again = self.h.render_2d("tt33", self.h.TT_POSES_2D[0])[0]
        self.assertTrue(np.array_equal(r.frame.rgba, again.rgba))
        self.assertEqual((r.frame.left, r.frame.top), (again.left, again.top))

    def test_save_for_the_overlay(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self.h.save_all(self.out, out)
            for key, rows in self.out.items():
                folder = out / key
                with self.subTest(weapon=key):
                    m = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
                    self.assertEqual(m["_state_machine"]["hand"], "E")
                    for r in rows:
                        data = (folder / f"{r.lump}.png").read_bytes()
                        i = data.index(b"grAb")
                        self.assertLess(i, data.index(b"IDAT"))
                        self.assertEqual(struct.unpack(">ii", data[i + 4:i + 12]), r.frame.offsets())
                        self.assertIn(r.lump, m)
            self.assertTrue((out / "katyusha" / "SDHPA0.png").is_file())
            self.assertTrue((out / "metrics.json").is_file())

    def test_sheet(self):
        with tempfile.TemporaryDirectory() as d:
            sub = {k: self.out[k] for k in ("ice_axe", "tt33")}
            path = self.h.build_sheet(sub, "2026-01-01_0000", self.h.SELF_ASSESSMENT, Path(d))
            text = path.read_text(encoding="utf-8")
        for r in sub["ice_axe"] + sub["tt33"]:
            self.assertIn(f">{r.key} <", text)
        refs = set(re.findall(r'data-ref="(i\d+)"', text))
        table = set(re.findall(r'"(i\d+)":"data:image/png;base64,', text))
        self.assertTrue(refs and refs <= table)
        for m in re.finditer(r'data-frames="([^"]*)" data-seq="([^"]*)"', text):
            frames = json.loads(html.unescape(m.group(1)))
            seq = json.loads(html.unescape(m.group(2)))
            self.assertLessEqual(set(frames), table)
            self.assertTrue(all(0 <= s[0] < len(frames) and s[2] > 0 for s in seq))
        self.assertNotIn("http", re.sub(r'data:image/png;base64,[A-Za-z0-9+/=]+', "", text).replace(
            "http://www.w3.org", ""))


if __name__ == "__main__":
    unittest.main()
