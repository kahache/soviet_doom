"""Contract of tools/art/gen_weapon.py (F4: the sergeant's hand, D39; the
ice axe, D40; the PPSh-41).

Cheap on purpose: renders a handful of frames, never a sheet. What is checked:

  palette    every opaque pixel is a palette.json colour, alpha is hard 0/255
  D39        hand and sleeve are apart in value in the recommended style
             (the CEO's note: "mismo color de piel y manos")
  telnyashka the recommended style shows both stripe colours at the wrist
             (a round cap once swallowed them: open-ended tubes)
  placement  a HUD frame reaches the bottom of the 320x200 weapon space, so
             no cut edge floats on screen, and its grAb offsets follow
             Doom's arithmetic (left = -leftoffset, top = 32 - topoffset)
  seed       the same frame renders identically twice
  no font    the generator never rasterises text with a system font
"""

from __future__ import annotations

import json
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
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_weapon.py"
MIN_HAND_SLEEVE_GAP = 20        # luma; the bare hand A measures ~7, the complaint


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class HandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        cls.style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.idle = gen_weapon.render_axe_frame(cls.style, gen_weapon.AXE_POSE["A"])
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def assert_palette(self, rgba):
        self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
        opaque = {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}
        self.assertLessEqual(opaque, self.palette)

    def test_palette_and_hard_alpha(self):
        self.assert_palette(self.idle.rgba)

    def test_hand_and_sleeve_apart(self):
        m = self.g.hand_metrics(self.style, self.idle)
        self.assertGreaterEqual(m["hand_sleeve_gap"], MIN_HAND_SLEEVE_GAP, m)

    def test_telnyashka_shows_both_stripes(self):
        if not self.style.telnyashka:
            self.skipTest("the recommended style has no telnyashka")
        mats = set(np.unique(self.idle.mat).tolist())
        for name in ("tel_white", "tel_blue"):
            self.assertIn(self.g.MAT_ID[name], mats, name)

    def test_reaches_the_bottom_of_the_screen(self):
        f = self.idle
        self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H)
        self.assertLess(f.top, self.g.STATUSBAR_TOP)       # something shows above the bar

    def test_offsets_follow_doom(self):
        f = self.idle
        lo, to = f.offsets()
        self.assertEqual(-lo, f.left)
        self.assertEqual(self.g.WEAPONTOP - to, f.top)
        with tempfile.TemporaryDirectory() as d:
            path = self.g.save_sprite(f, Path(d) / "X.png")
            data = path.read_bytes()
            i = data.index(b"grAb")
            self.assertEqual(struct.unpack(">ii", data[i + 4:i + 12]), (lo, to))
            with Image.open(path) as im:
                self.assertEqual(im.mode, "RGBA")

    def test_kit_renders(self):
        for which in ("grip", "trigger", "support"):
            self.assert_palette(self.g.render_kit(self.style, which).rgba)

    def test_deterministic(self):
        again = self.g.render_axe_frame(self.style, self.g.AXE_POSE["A"])
        self.assertTrue(np.array_equal(again.rgba, self.idle.rgba))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class IceAxeTests(unittest.TestCase):
    """D40: the ice axe's five held frames and its pickup."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.frames = {p.frame: gen_weapon.render_axe_frame(style, p) for p in gen_weapon.AXE_POSES}
        cls.pickups = {o.key: gen_weapon.render_axe_pickup(o.key) for o in gen_weapon.PICKUP_OPTIONS}
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def test_five_frames_like_the_slot_they_fill(self):
        # MOD-SPEC 6.3: the slot-1 weapon has five held frames, A-E
        self.assertEqual(sorted(self.frames), list("ABCDE"))

    def test_palette_and_hard_alpha(self):
        for f in (*self.frames.values(), *self.pickups.values()):
            self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
            opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
            self.assertLessEqual(opaque, self.palette)

    def test_every_held_frame_reaches_the_bottom(self):
        for k, f in self.frames.items():
            self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H, k)

    def test_the_head_is_on_screen_at_rest(self):
        f = self.frames["A"]
        steel = np.nonzero(f.mat == self.g.MAT_ID["steel"])
        self.assertTrue(steel[0].size > 0)
        top = f.top + int(steel[0].min())
        self.assertTrue(0 <= top < self.g.SCREEN_CY, top)

    def test_pickup_stands_on_the_floor(self):
        for k, f in self.pickups.items():
            lo, to = f.offsets()
            h, w = f.rgba.shape[:2]
            self.assertLessEqual(abs(lo - w // 2), 1, k)
            self.assertTrue(h - self.g.PLANT_SINK <= to <= h + 1, (k, to, h))

    def test_pickup_is_pickup_sized(self):
        # Freedoom's chainsaw is 47x19; an ice axe pickup in the same range
        f = self.pickups[self.g.RECOMMENDED_PICKUP]
        self.assertLessEqual(max(f.rgba.shape[:2]), 64)
        self.assertGreaterEqual(max(f.rgba.shape[:2]), 32)

    def test_names_are_the_contract(self):
        """MOD-SPEC 6.3's ice-axe row (the mod-engineer's D40 rename) names
        the lumps this generator writes."""
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        row = next(ln for ln in spec.splitlines() if ln.startswith("| Ice axe"))
        self.assertIn(f"`{self.g.AXE_SPRITE}` A–E", row)
        self.assertIn(f"`{self.g.AXE_PICKUP}` A", row)

@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class PpshTests(unittest.TestCase):
    """The PPSh-41: two held frames, two flash frames, the pickup."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.held, cls.flash = {}, {}
        for pose in gen_weapon.PPSH_POSES:
            f, muzzle = gen_weapon.render_ppsh_frame(style, pose)
            cls.held[pose.frame] = (f, muzzle)
            cls.flash[pose.frame] = gen_weapon.render_ppsh_flash(pose.frame, muzzle)
        cls.pickup = gen_weapon.render_ppsh_pickup()
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def frames(self):
        return [f for f, _ in self.held.values()] + list(self.flash.values()) + [self.pickup]

    def test_palette_and_hard_alpha(self):
        for f in self.frames():
            self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
            opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
            self.assertLessEqual(opaque, self.palette)

    def test_held_frames_reach_the_bottom(self):
        for k, (f, _) in self.held.items():
            self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H, k)

    def test_flash_sits_on_the_muzzle(self):
        for k, (f, (mx, my)) in self.held.items():
            fl = self.flash[k]
            self.assertTrue(fl.left <= mx <= fl.left + fl.rgba.shape[1], k)
            self.assertTrue(fl.top <= my <= fl.top + fl.rgba.shape[0], k)
            # and the muzzle is on screen, above the status bar
            self.assertTrue(0 <= mx < self.g.SCREEN_W and 0 <= my < self.g.STATUSBAR_TOP, (k, mx, my))

    def test_flash_is_flash_only(self):
        flat = {self.g.MAT_ID[n] for n in self.g.FLAT}
        for k, fl in self.flash.items():
            used = set(np.unique(fl.mat[fl.rgba[..., 3] > 0]).tolist())
            self.assertLessEqual(used, flat, k)

    def test_names_are_the_contract(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        row = next(ln for ln in spec.splitlines() if ln.startswith("| PPSh-41"))
        for name in (self.g.PPSH_SPRITE, self.g.PPSH_FLASH, self.g.PPSH_PICKUP):
            self.assertIn(f"`{name}`", row)

    def test_pickup_stands_on_the_floor(self):
        lo, to = self.pickup.offsets()
        h, w = self.pickup.rgba.shape[:2]
        self.assertLessEqual(abs(lo - w // 2), 1)
        self.assertEqual(to, h)


if __name__ == "__main__":
    unittest.main()
