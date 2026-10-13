"""Contract of tools/art/gen_rig.py (F5, Reich rifleman 3D rig, D38).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  plan       BESTIARY §3's frame set: A-G at 8 rotations, H-U at rotation 0, 70 lumps
  rotation   Doom's rotation 3 shows his left side: forward turns to screen left
  rig        two-bone IK reaches its target with the bones' lengths; a rigid
             group transform moves a primitive's distance field with it
  gif        the lossless GIF writer keeps every colour
  core       the rifleman is a figure on tools/art/rig_core.py: his table is
             the core's base table plus band and gore (no id moved), his
             limbs carry limb and side labels, all 8 rotations are drawn

The render tests run under `tools/verify.py art`, not `fast` (each sprite is
a sphere trace of about two seconds; SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is a palette.json colour, alpha hard 0/255
  faction    no military_green on a Reich figure (ART-BIBLE §6.2)
  scale      the standing figure is Doom's 56-unit actor
  armband    the D12 accent is on the front view, and the flash on frame F
  floor      the corpse lies on the floor, low and wide
  seed       the same lump renders identically twice
"""

from __future__ import annotations

import json
import os
import re
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

SOURCE = ART_TOOLS / "gen_rig.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the rig renders")


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_rig
        cls.g = gen_rig

    def test_frame_plan_is_bestiary_3(self):
        plan = self.g.frame_plan()
        self.assertEqual(len(plan), 7 * 8 + 5 + 9)
        self.assertEqual(len(set(plan)), len(plan))
        for frame, rot in plan:
            name = self.g.lump_name(frame, rot)
            self.assertRegex(name, r"^SDRR[A-U][0-8]$")
            self.assertLessEqual(len(name), 8)
            self.assertEqual(rot == 0, frame in "HIJKLMNOPQRSTU", name)

    def test_rotation_3_shows_his_left_side(self):
        g = self.g
        fwd3 = g.yaw_matrix(3) @ g.V(0, 0, 1)       # his forward, seen at rotation 3
        left3 = g.yaw_matrix(3) @ g.V(1, 0, 0)      # his left, seen at rotation 3
        self.assertLess(fwd3[0], -0.99)             # he faces screen left
        self.assertGreater(left3[2], 0.99)          # his left side faces the camera
        self.assertTrue(np.allclose(g.yaw_matrix(1), np.eye(3)))
        self.assertTrue(np.allclose(g.yaw_matrix(0), np.eye(3)))   # rotation 0 drawn from the front

    def test_two_bone_reaches_with_bone_lengths(self):
        g = self.g
        root, target = g.V(0, 26, 0), g.V(3, 6, 4)          # 20.6 apart: in reach
        joint, end = g.two_bone(root, target, g.THIGH, g.SHIN, g.V(0, 0, 1))
        self.assertTrue(np.allclose(end, target, atol=1e-6))
        self.assertAlmostEqual(float(np.linalg.norm(joint - root)), g.THIGH, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(end - joint)), g.SHIN, places=6)
        self.assertGreater(joint[2], 0)            # the knee bends towards the pole

    def test_group_transform_moves_the_field(self):
        g = self.g
        prim = g.ellipsoid("coat", 0.5, (1, 2, 3), (2, 1, 1.5), grp="upper")
        pts = np.random.default_rng(0).uniform(-6, 6, (50, 3))
        before = prim.sd(pts)
        R, pivot, off = g.rot_z(37), g.V(1, 0, -2), g.V(4, 1, 0)
        g.transform([prim], {}, {"upper"}, R, pivot, off)
        moved = (pts - pivot) @ R.T + pivot + off
        self.assertTrue(np.allclose(prim.sd(moved), before, atol=1e-9))
        c, _ = prim.bound()
        self.assertTrue(np.allclose(c, R @ (g.V(1, 2, 3) - pivot) + pivot + off))

    def test_materials_extend_the_core(self):
        g = self.g
        core = g.core
        names = list(g.MATERIALS)
        self.assertEqual(names[:len(core.MATERIALS)], list(core.MATERIALS))
        self.assertEqual(names[len(core.MATERIALS):], ["band", "gore"])
        self.assertFalse(g.MATERIALS["band"].shift)         # the armband keeps its own red
        self.assertTrue(g.MATERIALS["gore"].shift)
        self.assertEqual({n for n, m in g.MATERIALS.items() if m.flat},
                         {"flash_out", "flash_in", "flash_core", "button"})
        self.assertEqual({n for n, m in g.MATERIALS.items() if m.cloth}, {"coat", "coat_dark", "helmet", "crest"})

    def test_limbs_are_labelled(self):
        g = self.g
        core = g.core
        for frame in "ADEH":
            P, _ = g.build_model(g.POSES[frame])
            for limb in ("leg", "arm"):
                self.assertTrue(core.select(P, limb=limb, side=core.LEFT), (frame, limb))
                self.assertTrue(core.select(P, limb=limb, side=core.RIGHT), (frame, limb))
            self.assertEqual({p.grp for p in core.select(P, limb="leg", side=core.LEFT)}, {"leg_l"})
            self.assertEqual({p.grp for p in core.select(P, limb="leg", side=core.RIGHT)}, {"leg_r"})
            band = core.select(P, tag="armband")
            self.assertEqual(len(band), 1)
            self.assertEqual(band[0].side, core.LEFT)                  # D12: his LEFT arm
        self.assertEqual(sorted({r for _, r in g.frame_plan() if r}), list(range(1, 9)))   # handed: no mirror

    def test_gif_is_lossless(self):
        g = self.g
        rng = np.random.default_rng(1)
        cols = np.array([(18, 16, 8), (108, 97, 64), (228, 52, 44), (147, 149, 152)], np.uint8)
        frames = [cols[rng.integers(0, 4, (8, 6))] for _ in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            path = g.save_gif(frames, [100, 100, 100], Path(tmp) / "t.gif")
            with Image.open(path) as im:
                for i, f in enumerate(frames):
                    im.seek(i)
                    self.assertTrue(np.array_equal(np.asarray(im.convert("RGB")), f))


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_rig
        cls.g = gen_rig
        cls.r = {k: gen_rig.render(*k) for k in (("A", 1), ("A", 3), ("F", 1), ("L", 0), ("U", 0))}
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        ramps = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
        cls.green = ramps["military_green"]
        cls.red = ramps["flag_red"]
        cls.flash = ramps["cream_yellow"] | ramps["hazard_yellow"]

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for k, rgba in self.r.items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, k)
            self.assertLessEqual(self.opaque(rgba), self.palette, k)

    def test_no_military_green(self):
        for k, rgba in self.r.items():
            self.assertFalse(self.opaque(rgba) & self.green, k)

    def test_scale_and_canvas(self):
        g = self.g
        a1 = self.r[("A", 1)]
        self.assertEqual(a1.shape, (g.STAND.h, g.STAND.w, 4))
        m = g.measure(a1)
        self.assertLessEqual(abs(m["height_px"] - g.DOOM_HEIGHT), 4)
        self.assertLessEqual(abs(m["lowest_row"] - g.STAND.foot_row), 1)
        self.assertEqual(self.r[("L", 0)].shape, (g.DEATH.h, g.DEATH.w, 4))

    def test_armband_and_flash(self):
        self.assertGreaterEqual(sum(1 for px in self.r[("A", 1)][..., :3].reshape(-1, 3)
                                    if tuple(px) in self.red), 12)
        self.assertTrue(self.opaque(self.r[("F", 1)]) & self.flash)
        self.assertFalse(self.opaque(self.r[("A", 1)]) & self.flash)

    def test_corpse_lies_on_the_floor(self):
        g = self.g
        m = g.measure(self.r[("L", 0)])
        self.assertLess(m["height_px"], 40)
        self.assertGreater(m["width_px"], m["height_px"])
        self.assertLessEqual(abs(m["lowest_row"] - g.DEATH.foot_row), 2)
        u = g.measure(self.r[("U", 0)])
        self.assertLessEqual(u["lowest_row"] - g.GIB.foot_row, 4)

    def test_deterministic(self):
        again = self.g.render("A", 3)
        self.assertTrue(np.array_equal(again, self.r[("A", 3)]))

    def test_grab_written(self):
        g = self.g
        with tempfile.TemporaryDirectory() as tmp:
            path = g.save_sprite(self.r[("L", 0)], Path(tmp) / "SDRRL0.png", g.DEATH)
            self.assertEqual(g.read_grab(path), (g.DEATH.cx, g.DEATH.foot_row - g.FEET_SINK))


if __name__ == "__main__":
    unittest.main()
