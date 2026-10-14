"""Contract of tools/art/gen_storm.py (F5, Stormtrooper and Reich hound sweeps, D35).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  cells      4-5 cells per enemy, unique keys, the BESTIARY sprite names
  rig        the new materials are appended to a COPY of gen_rig's table:
             no id moves and gen_rig's own table is untouched; the right
             arm is removed by its label (limb, side), and the label agrees
             with the old position rule (x < 0)
  faction    no military_green in either enemy; no flag_red on the hound
             outside its forbidden list (BESTIARY §6: no red at all)
  leg        the three-segment hind leg keeps its bone lengths and puts the
             knee forward and the hock behind the paw
  gallop     the hound on rig_core's quadruped skeleton: four labelled legs,
             no red, the head ahead of the withers, the axis centred

The render tests run under `tools/verify.py art`, not `fast`
(SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is a palette.json colour, alpha hard 0/255
  storm      Doom's 56-unit actor; the recommended cell's Legion share from
             the front is under BESTIARY §5's 25 %
  hound      a horizontal bar under 40 px tall, no red pixel, a black
             bottom edge (BESTIARY §10 rule 4)
  gallop     the proof frame is a low bar with a paw on the floor; rotation 7
             in mirror mode is rotation 3 flipped
  seed       the same sprite renders identically twice

The full set of cell E (D48), cheap:

  plan       SDHS A-H at 8 rotations and I-U at rotation 0 (MOD-SPEC §6.3),
             SDBL A-E at 0, the proposed claw V-W outside the contract
  zscript    every frame letter stormtrooper.zs names is drawn, and the
             GIFs' tics are read from it
  blood      D49's dark red, the rifleman's materials: flag_red 0-5 over
             black, darker than the armband; not counted as Legion
  models     no military_green, the graft labelled, pools in the corpse

and rendered (slow):

  identity   frame A1 without the talons is the sweep's cell E, pixel for pixel
  palette    death, gib and bolt frames: palette colours, hard alpha
  gore       the corpse and the gib carry a lot of blood
  bolt       centred on its offsets, brighter than the wall it is added to
"""

from __future__ import annotations

import json
import os
import re
import sys
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

SOURCE = ART_TOOLS / "gen_storm.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the storm and hound renders")


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class CheapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_rig
        cls.before = list(gen_rig.MATERIALS)     # the rifleman's table before this import
        import gen_storm
        import rig_core
        cls.rig, cls.g, cls.core = gen_rig, gen_storm, rig_core

    def test_cells(self):
        g = self.g
        for cells in (g.STORM_CELLS, g.HOUND_CELLS):
            self.assertTrue(4 <= len(cells) <= 5)
            self.assertEqual(len({c.key for c in cells}), len(cells))
        self.assertIn(g.STORM_RECOMMENDED, g.STORM)
        self.assertIn(g.HOUND_RECOMMENDED, g.HOUND)
        self.assertEqual((g.STORM_SPRITE, g.HOUND_SPRITE), ("SDHS", "SDHN"))
        self.assertRegex(g.lump(g.STORM_SPRITE, "A", "G", 1), r"^SDHS_A_G1$")

    def test_registration_appends_only(self):
        rig, g, core = self.rig, self.g, self.core
        self.assertEqual(list(rig.MATERIALS), self.before)          # gen_rig's own table is untouched
        ids = core.material_ids(g.MATERIALS)
        for i, name in enumerate(self.before):
            self.assertEqual(ids[name], i, name)
        for name, mat in g.NEW_MATERIALS.items():
            self.assertIs(g.MATERIALS[name], mat)
            self.assertFalse(mat.shift, name)                        # each keeps its own value
        flat_new = {n for n, m in g.MATERIALS.items() if m.flat} - set(rig.MATERIALS)
        self.assertEqual(flat_new, {"bolt_out", "bolt_core", "bolt_dim", "bolt_core_dim",
                                    "blood", "pool"})
        n = len(g.MATERIALS)
        g.register_materials()                   # idempotent
        self.assertEqual(len(g.MATERIALS), n)

    def test_right_arm_removed_by_label(self):
        g, core = self.g, self.core
        cell = g.STORM["A"]
        p = self.rig.Pose("A", "storm", **g.STORM_FEET, bob=g.STORM_BOB, carry="free", stride=0.3,
                          head_pitch=cell.hunch * 0.7, hand_l=(9.6, 27.2, 3.4), hand_r=(-9.0, 27.0, 3.0),
                          rifle_at=((-10.0, 20.0, 4.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), canvas=g.STORM_CV)
        full, _ = self.rig.build_model(p)
        right = core.select(full, limb="arm", side=core.RIGHT)
        left = core.select(full, limb="arm", side=core.LEFT)
        self.assertTrue(right and left)
        # the label agrees with the position rule the first sweep used
        by_position = {id(q) for q in full if q.grp == "arm" and q.bound()[0][0] < 0}
        self.assertEqual(by_position, {id(q) for q in right})
        kept, _ = g._rifleman_body(cell, "idle")
        self.assertFalse(core.select(kept, limb="arm", side=core.RIGHT))
        self.assertEqual(len(core.select(kept, limb="arm", side=core.LEFT)), len(left))
        self.assertTrue(core.select(kept, tag="armband"))          # his Reich arm keeps the armband

    def _ramps(self, prims):
        return set().union(*(self.g.MATERIALS[p.mat].ramps for p in prims))

    def test_faction_colours(self):
        g = self.g
        for c in g.STORM_CELLS:
            for pose in ("idle", "attack"):
                self.assertNotIn("military_green", self._ramps(g.storm_model(c, pose)), c.key)
        for c in g.HOUND_CELLS:
            for pose in ("idle", "bite"):
                ramps = self._ramps(g.hound_model(c, pose))
                self.assertNotIn("military_green", ramps, c.key)
                self.assertNotIn("flag_red", ramps, c.key)

    def test_hind_leg(self):
        g = self.g
        hip, paw = g.V(3, 20.5, -17), g.V(3, g.PAW_Y, -19.5)
        knee, hock, end = g.three_bone_hind(hip, paw)
        self.assertAlmostEqual(float(np.linalg.norm(knee - hip)), g.HIND_FEMUR, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(hock - knee)), g.HIND_TIBIA, places=6)
        self.assertTrue(np.allclose(end, paw))
        self.assertGreater(knee[2], hip[2] - 1e-9)       # the knee points forward
        self.assertLess(hock[2], paw[2])                 # the hock sits behind the paw

    def test_gallop_model(self):
        g, core = self.g, self.core
        cell = g.HOUND[g.HOUND_RECOMMENDED]
        for f, ph in g.GALLOP_FRAMES.items():
            pose = core.QuadPose(f, "gallop", ph)
            P = g.hound_gallop_model(cell, pose)
            for limb, n in (("foreleg", 3), ("hindleg", 4)):
                for side in (core.LEFT, core.RIGHT):
                    legs = core.select(P, limb=limb, side=side)
                    self.assertEqual(len(legs), n, (f, limb, side))
                    self.assertTrue(all(np.sign(q.bound()[0][0]) == side for q in legs), (f, limb, side))
            ramps = self._ramps(P)
            self.assertNotIn("flag_red", ramps)
            self.assertNotIn("military_green", ramps)
            withers = core.pose_quadruped(g.GALLOP_BUILD, pose).spine[-1]
            head = core.select(P, grp="head")
            self.assertGreater(min(q.bound()[0][2] for q in head), withers[2])     # the head leads
        self.assertEqual(g.GALLOP_CV.cx * 2, g.GALLOP_CV.w)                   # mirror mode needs the axis centred


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_storm
        cls.g = gen_storm
        cls.storm, cls.storm_mat = gen_storm.render_storm(gen_storm.STORM_RECOMMENDED, "A", 1)
        cls.hound, _ = gen_storm.render_hound(gen_storm.HOUND_RECOMMENDED, "A", 3)
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        ramps = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
        cls.red, cls.green = ramps["flag_red"], ramps["military_green"]

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for rgba in (self.storm, self.hound):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.palette)
            self.assertFalse(self.opaque(rgba) & self.green)

    def test_storm_scale_and_legion_share(self):
        g = self.g
        self.assertEqual(self.storm.shape, (g.STORM_CV.h, g.STORM_CV.w, 4))
        m = g.measure(self.storm)
        self.assertLessEqual(abs(m["height_px"] - g.rig.DOOM_HEIGHT), 4)
        self.assertLessEqual(g.legion_fraction(self.storm_mat), g.LEGION_MAX)
        self.assertGreater(g.legion_fraction(self.storm_mat), 0.05)     # the graft is there

    def test_hound_is_a_low_bar_without_red(self):
        g = self.g
        m = g.measure(self.hound)
        self.assertLess(m["height_px"], g.HOUND_MAX_H)
        self.assertGreater(m["width_px"], 1.5 * m["height_px"])
        self.assertLessEqual(abs(m["lowest_row"] - g.HOUND_CV.foot_row), 1)
        self.assertFalse(self.opaque(self.hound) & self.red)
        self.assertGreater(g.belly_black_share(self.hound), 0.5)

    def test_deterministic(self):
        again, _ = self.g.render_hound(self.g.HOUND_RECOMMENDED, "A", 3)
        self.assertTrue(np.array_equal(again, self.hound))

    def test_gallop_proof_frame_and_mirror(self):
        g = self.g
        core = g.core
        cell = g.HOUND[g.HOUND_RECOMMENDED]
        pose = core.QuadPose("C", "gallop", g.GALLOP_FRAMES["C"])
        turn = core.render_rotations(lambda: g.hound_gallop_model(cell, pose), g.GALLOP_CV, (3, 7), mirror=True,
                                     materials=g.MATERIALS, seed=g.SEED, value_shift=g.rig.VALUE_SHIFT)
        m = g.measure(turn[3])
        self.assertLess(m["height_px"], g.HOUND_MAX_H)
        self.assertGreater(m["width_px"], 1.5 * m["height_px"])
        self.assertLessEqual(abs(m["lowest_row"] - g.GALLOP_CV.foot_row), 1)   # a paw on the floor
        self.assertTrue(np.array_equal(turn[7], turn[3][:, ::-1]))
        self.assertLessEqual(self.opaque(turn[3]), self.palette)
        self.assertFalse(self.opaque(turn[3]) & self.red)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullSetCheapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_storm
        import rig_core
        cls.g, cls.core = gen_storm, rig_core

    def test_plan_matches_the_contract(self):
        g = self.g
        plan = g.full_plan()
        self.assertEqual(len(plan), 8 * 8 + 13)
        for f, r in plan:
            self.assertEqual(r != 0, f in "ABCDEFGH", (f, r))
            name = g.full_lump(f, r)
            self.assertRegex(name, r"^SDHS[A-U][0-8]$")
        self.assertEqual({f for f, _ in plan}, set("ABCDEFGHIJKLMNOPQRSTU"))
        self.assertEqual({f for f, _ in g.melee_plan()}, {"V", "W"})
        self.assertFalse(set(g.melee_plan()) & set(plan))
        self.assertEqual([g.full_lump(f, 0, g.BOLT_SPRITE) for f in g.BOLT_FRAMES],
                         ["SDBLA0", "SDBLB0", "SDBLC0", "SDBLD0", "SDBLE0"])
        self.assertEqual(g.grab(g.BOLT_CV), (g.BOLT_CV.w // 2, g.BOLT_CV.h // 2))   # centred, as BAL1
        self.assertEqual(g.FULL_DIR, g.STORM_DIR / "full_E")                       # the sweep's files stay put

    def test_frames_match_the_zscript(self):
        g = self.g
        tics = g.zscript_tics()
        used = set().union(*(set(v) for v in tics.values()))
        self.assertLessEqual(used, {f for f, _ in g.full_plan()})
        self.assertEqual(set(tics["See"]), set("ABCD"))
        self.assertEqual(set(tics["Missile"]), set("EFG"))
        self.assertEqual(tics["Melee"], tics["Missile"])          # one state: the claw has no frames of its own
        self.assertEqual(set(tics["Pain"]), {"H"})
        self.assertEqual(set(tics["Death"]), set("IJKLM"))
        self.assertEqual(set(tics["XDeath"]), set("NOPQRSTU"))

    def test_blood_is_d49_dark_red(self):
        g = self.g
        red = g.core.ramp("flag_red")
        for name in ("blood", "pool"):
            mat = g.MATERIALS[name]
            self.assertEqual(mat.ramps, {g.BLOOD_RAMP}, name)                       # "rojo oscuro, nada de oliva"
            self.assertLessEqual(set(mat.colours()), set(red[:g.BLOOD_MAX_INDEX + 1]) | {(0, 0, 0)}, name)
            self.assertTrue(mat.flat, name)                                          # no rim: a drop stays red
            self.assertNotIn(name, g.LEGION_MATERIALS | g.BOLT_MATERIALS)
        self.assertLess(max(g.MATERIALS["pool"].colours()), max(g.MATERIALS["blood"].colours()))  # pools darker
        self.assertIn(g.zscript_blood_color(), set(red))     # the engine's hit puffs are on the same red ramp

    def _ramps(self, prims):
        return set().union(*(self.g.MATERIALS[p.mat].ramps for p in prims))

    def test_models(self):
        g, core = self.g, self.core
        for f in "ADGHV":
            P = g.full_prims(f)
            self.assertNotIn("military_green", self._ramps(P), f)
            self.assertTrue(core.select(P, limb="graft", side=core.RIGHT), f)
            self.assertTrue(core.select(P, tag="armband"), f)          # his Reich arm keeps it
        talons = [q for q in g.full_prims("A") if q.mat == "bone"]
        self.assertEqual(len(talons), 3)
        corpse = g.full_prims("M")
        self.assertNotIn("military_green", self._ramps(corpse))
        self.assertGreaterEqual(len([q for q in corpse if q.grp == "pool"]), 4)
        self.assertGreaterEqual(len([q for q in corpse if q.mat == "blood"]), 40)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullSetRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from dataclasses import replace
        import gen_storm
        g = cls.g = gen_storm
        P, _ = g.storm_full_model(replace(g.STORM_POSES["A"], claws=False))
        cls.a1_plain, _ = g.render_prims(P, 1, g.STORM_CV)
        cls.sweep_e, _ = g.render_storm(g.FULL_KEY, "A", 1)
        cls.a3, cls.a3_mat = g.render_full("A", 3)
        cls.m0, cls.m0_mat = g.render_full("M", 0)
        cls.u0, cls.u0_mat = g.render_full("U", 0)
        cls.bolt = g.render_bolt("A")
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        ramps = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
        cls.green = ramps["military_green"]

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_frame_a_is_the_sweeps_cell(self):
        self.assertTrue(np.array_equal(self.a1_plain, self.sweep_e))

    def test_palette_and_hard_alpha(self):
        for rgba in (self.a3, self.m0, self.u0, self.bolt):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.palette)
            self.assertFalse(self.opaque(rgba) & self.green)

    def test_standing_scale(self):
        g = self.g
        m = g.measure(self.a3)
        self.assertLessEqual(abs(m["lowest_row"] - g.STORM_CV.foot_row), 1)
        self.assertLessEqual(abs(m["height_px"] - g.rig.DOOM_HEIGHT), 8)    # the bare skull is lower than a helmet

    def test_much_blood(self):
        g = self.g
        self.assertGreater(g.blood_share(self.m0_mat), 0.15)
        self.assertGreater(g.blood_share(self.u0_mat), 0.15)
        m = g.measure(self.m0)
        self.assertLess(m["height_px"], 40)                               # he lies down

    def test_bolt(self):
        g = self.g
        a = self.bolt[..., 3] > 0
        ys, xs = np.nonzero(a)
        cx, cy = g.grab(g.BOLT_CV)
        self.assertLessEqual(abs(xs.mean() - cx), 2.0)
        self.assertLessEqual(abs(ys.mean() - cy), 2.0)
        self.assertGreater(float(g.flat.luma(self.bolt[..., :3])[a].mean()), 120)


if __name__ == "__main__":
    unittest.main()
