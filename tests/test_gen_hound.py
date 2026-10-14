"""Contract of tools/art/gen_hound.py (F5, the Reich hound as a German shepherd, D48).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  cells      3-4 cells, unique keys, the recommended one among them, the
             BESTIARY sprite name, the frame plan (gallop A-D, bite E-G at
             rotations 1, 3, 5)
  materials  each cell's table is a COPY of rig_core's: no base id moves,
             rig_core.MATERIALS is untouched; no military_green anywhere;
             flag_red only inside the mouth (BESTIARY §6, D48)
  breed      the anatomy D48 asks for, measured on the posed skeleton and
             primitives: the withers above the sacrum (sloping top line),
             the hind paw behind the hip (angulation), the ears the highest
             point and erect, the head ahead of the withers, the tail hung
             below the croup, a black saddle and a collar with a steel tag;
             the graft only on cell D, symmetric (mirror mode stays valid)
  canvas     the axis is centred (mirror mode)

The render tests run under `tools/verify.py art`, not `fast`
(SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is a palette.json v1 colour, alpha hard 0/255
  height     side and front under BESTIARY §6's 40 px
  red        no red pixel in a gallop frame; the open mouth may show some
  brown      the profile is mostly tan (it reads brown) with a black saddle
  mirror     rotation 7 is rotation 3 flipped, exactly
  seed       the same sprite renders identically twice

The full set of cell A (D50), cheap tier:

  plan       every frame letter reich_hound.zs names is drawn: A-H at 1-5
             (mirror mode), I-N at rotation 0, 46 lumps with Doom's names
             (SDHNA2A8 ...), SDHN as MOD-SPEC 6.3 reserves it; no XDeath;
             the GIFs' timing is the actor's tics
  blood mats blood and pool are flag_red 0-5 and black only (D49)

and slow tier (SD_SKIP_SLOW_ART skips it, `verify.py art` runs it):

  corpse     THE CEO'S RULE: N lies on its side with the whole body on the
             floor: chest, croup, neck, head, tail and the four paws each
             within LYING_MAX of it, nothing higher than LYING_TOP, the
             supports spread LYING_SPAN along the body, the spine level and
             its up axis horizontal, every leg loosely bent (not stiff, not
             folded), in a pool that grew from L (the Legion's first L0 was
             rejected for resting on a shoulder)
  renders    palette and hard alpha, heights, the mirror pair, blood only
             in flag_red 0-5 and black and abundant in N, the corpse a low
             horizontal shape; the PNGs in full_A/ when they exist
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

SOURCE = ART_TOOLS / "gen_hound.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the German shepherd renders")


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
        import rig_core
        cls.base_before = list(rig_core.MATERIALS)
        import gen_hound
        cls.g, cls.core = gen_hound, rig_core

    def model(self, key="A", frame="C"):
        return self.g.gsd_model(self.g.CELL[key], frame)

    def test_cells_and_plan(self):
        g = self.g
        self.assertTrue(3 <= len(g.CELLS) <= 4)
        self.assertEqual(len(g.CELL), len(g.CELLS))
        self.assertIn(g.RECOMMENDED, g.CELL)
        self.assertEqual(g.SPRITE, "SDHN")
        plan = g.frame_plan()
        self.assertEqual({f for f, _ in plan}, set("ABCDEFG"))
        self.assertEqual({r for _, r in plan}, {1, 3, 5})

    def test_materials_are_a_copy(self):
        g, core = self.g, self.core
        self.assertEqual(list(core.MATERIALS), self.base_before)
        for c in g.CELLS:
            table = g.materials_for(c)
            self.assertEqual(list(table)[:len(self.base_before)], self.base_before)
            for name in ("tan", "cream", *g.FIXED_MATERIALS):
                self.assertIn(name, table)
        self.assertEqual(list(core.MATERIALS), self.base_before)

    def test_faction_colours(self):
        g = self.g
        for c in g.CELLS:
            table = g.materials_for(c)
            used = {p.mat for f in ("C", "F") for p in g.gsd_model(c, f)}
            for name in used:
                self.assertNotIn("military_green", table[name].ramps, name)
                if "flag_red" in table[name].ramps:
                    self.assertIn(name, g.RED_MATERIALS)

    def test_red_only_when_the_mouth_is_open(self):
        for f in "ABCD":
            self.assertFalse([p for p in self.model("A", f) if p.mat == "mouth"], f)
        self.assertTrue([p for p in self.model("A", "F") if p.mat == "mouth"])

    def test_breed_skeleton(self):
        g, core = self.g, self.core
        rigs = [core.pose_quadruped(g.GSD_BUILD, core.QuadPose("A", "gallop", k / 8)) for k in range(8)]
        # over a stride (the gallop pitches the body) the withers ride above the sacrum
        withers_y = np.mean([q.spine[-1][1] for q in rigs])
        sacrum_y = np.mean([q.spine[0][1] for q in rigs])
        self.assertGreater(withers_y, sacrum_y + 2.0, "the top line slopes down to the croup")
        for leg in ("hl", "hr"):
            # over a whole stride the hind paw works behind the hip: the breed's angulation
            paw_z = np.mean([q.legs[leg][3][2] for q in rigs])
            hip_z = np.mean([q.legs[leg][0][2] for q in rigs])
            self.assertLess(paw_z, hip_z - 2.0, "angulation: the hind paw behind the hip")

    def test_breed_shapes(self):
        P = self.model("A", "C")
        def top(p):
            c, r = p.bound()
            return c[1] + r
        ears = [p for p in P if p.kind == "cappedcone" and p.grp == "head"]
        self.assertEqual(len(ears), 2)
        for e in ears:
            axis = e.xm @ e.rot @ np.array([0.0, 1.0, 0.0])
            self.assertGreater(axis[1], 0.7, "erect: the ear points up")
        head_z = max(p.bound()[0][2] for p in P if p.grp == "head")
        body_z = max(p.bound()[0][2] for p in P if p.grp == "body")
        self.assertGreater(head_z, body_z)
        tail = [p for p in P if p.grp == "tail"]
        self.assertTrue(tail)
        tip = min(tail, key=lambda p: p.bound()[0][2])
        croup = [p for p in P if p.grp == "body"]
        self.assertLess(tip.bound()[0][2], min(p.bound()[0][2] for p in croup))
        self.assertTrue(any(p.mat == "saddle" and p.grp == "body" for p in P), "the black blanket")
        self.assertTrue([p for p in P if p.tag == "collar"])
        self.assertTrue([p for p in P if p.tag == "tag" and p.mat == "steel"])
        self.assertLess(max(top(p) for p in P), self.g.MAX_H + 2)

    def test_graft_only_on_d_and_symmetric(self):
        g = self.g
        for c in g.CELLS:
            P = g.gsd_model(c, "C")
            scars = [p for p in P if p.mat == "scar"]
            self.assertEqual(bool(scars), c.graft, c.key)
            if c.graft:
                xs = sorted(round(float(p.bound()[0][0]), 1) for p in scars)
                self.assertEqual(xs, sorted(-x for x in xs), "graft symmetric about the axis")

    def test_canvas_axis_centred(self):
        self.assertEqual(self.g.CV.cx * 2, self.g.CV.w)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("SD_SKIP_SLOW_ART"):
            raise unittest.SkipTest("SD_SKIP_SLOW_ART is set")
        import gen_hound
        cls.g = gen_hound
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        rec = gen_hound.CELL[gen_hound.RECOMMENDED]
        cls.spr = {(f, r): gen_hound.render(rec, f, r) for f, r in (("C", 3), ("A", 1), ("F", 3))}

    @staticmethod
    def opaque(rgba):
        a = rgba[..., 3] > 0
        return {tuple(int(v) for v in c) for c in rgba[..., :3][a]}

    @staticmethod
    def height(rgba):
        ys = np.nonzero(rgba[..., 3] > 0)[0]
        return int(ys.max() - ys.min() + 1)

    @slow
    def test_palette_and_hard_alpha(self):
        for k, rgba in self.spr.items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, k)
            self.assertLessEqual(self.opaque(rgba), self.palette, k)

    @slow
    def test_height(self):
        self.assertLess(self.height(self.spr[("C", 3)]), self.g.MAX_H)
        self.assertLess(self.height(self.spr[("A", 1)]), self.g.MAX_H)

    @slow
    def test_red_only_in_the_mouth(self):
        import rig_core as core
        red = set(core.ramp("flag_red"))
        self.assertFalse(self.opaque(self.spr[("C", 3)]) & red)
        self.assertFalse(self.opaque(self.spr[("A", 1)]) & red)
        bite = self.spr[("F", 3)]
        a = bite[..., 3] > 0
        n_red = sum(1 for c in bite[..., :3][a] if tuple(int(v) for v in c) in red)
        self.assertLess(n_red / a.sum(), 0.03)

    @slow
    def test_reads_brown_with_a_black_saddle(self):
        m = self.g.metrics_for(self.g.CELL[self.g.RECOMMENDED],
                               {**self.spr, ("A", 1): self.spr[("A", 1)]})
        self.assertGreater(m["tan_share"], 0.5)
        self.assertGreater(m["saddle_share"], 0.15)

    @slow
    def test_mirror_and_seed(self):
        g = self.g
        rec = g.CELL[g.RECOMMENDED]
        again = g.render(rec, "C", 3)
        self.assertTrue(np.array_equal(again, self.spr[("C", 3)]))
        seven = g.render(rec, "C", 7)
        self.assertTrue(np.array_equal(seven, self.spr[("C", 3)][:, ::-1]))


ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "reich_hound.zs"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
RELAXED_BEND = 25.0             # degrees: a relaxed leg bends this much somewhere; the death throe's
                                # stiff legs, let fall the same way, bend 14-21


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullSetPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_hound
        import rig_core
        cls.g, cls.core = gen_hound, rig_core

    def test_sweep_model_has_no_blood(self):
        # gsd_model builds through dog() now; the sweep's frames carry no blood
        for f in ("C", "F"):
            P = self.g.gsd_model(self.g.CELL["A"], f)
            self.assertFalse([p for p in P if p.mat in self.g.BLOOD_MATERIALS], f)

    def test_every_letter_of_the_actor_is_drawn(self):
        g = self.g
        states = g.zs_states(ZS)
        for label in ("Spawn", "See", "Melee", "Pain", "Death"):
            self.assertIn(label, states)
        used = {f for seq in states.values() for f, _ in seq}
        self.assertEqual(used, {f for f, _ in g.full_plan()})
        self.assertNotIn("XDeath", states, "no gib: BESTIARY 6")
        self.assertEqual([f for f, _ in states["Death"]], list(g.DEATH_FRAMES))
        self.assertEqual({f for f, _ in states["Pain"]}, set(g.PAIN_FRAMES))

    def test_plan_and_lump_names(self):
        g = self.g
        plan = g.full_plan()
        self.assertEqual(len(plan), 46)                       # BESTIARY 6's total
        for f, r in plan:
            self.assertIn(r, (0,) if f in g.DEATH_FRAMES else (1, 2, 3, 4, 5), f)
        names = {g.full_lump(f, r) for f, r in plan}
        self.assertEqual(len(names), 46)
        for n in ("SDHNA1", "SDHNA2A8", "SDHNA3A7", "SDHNA4A6", "SDHNA5", "SDHNH3H7", "SDHNI0", "SDHNN0"):
            self.assertIn(n, names)
        self.assertTrue(all(len(n) <= 8 and re.fullmatch(r"[A-Z0-9]+", n) for n in names))
        self.assertIn("| `SD_ReichHound` | `SDHN` |", MOD_SPEC.read_text(encoding="utf-8"))
        self.assertEqual(g.DEATH_CV.cx * 2, g.DEATH_CV.w)

    def test_gif_runs_follow_the_tics(self):
        g = self.g
        states = g.zs_states(ZS)
        self.assertEqual(g._gif_runs(states["See"]), [("A", 4), ("B", 4), ("C", 4), ("D", 4)])  # AABBCCDD 2
        self.assertEqual(g._gif_runs(states["Death"])[-1], ("N", -1))

    def test_blood_materials_are_dark_red(self):
        g, core = self.g, self.core
        allowed = set(core.ramp(g.BLOOD_RAMP)[:g.BLOOD_MAX_INDEX + 1]) | {(0, 0, 0)}
        table = g.full_materials()
        for name in g.BLOOD_MATERIALS:
            self.assertLessEqual(set(table[name].colours()), allowed, name)
            self.assertEqual(table[name].ramps, {"flag_red"})
        base = list(g.materials_for(g.FULL_CELL))
        self.assertEqual(list(table)[:len(base)], base)
        self.assertEqual(g.FULL_CELL.key, "A")                # D50


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class CorpseTests(unittest.TestCase):
    """The CEO's rule for every corpse: lying naturally, on its side, the
    whole body on the floor, the legs relaxed, the head down, in a pool."""

    @classmethod
    def setUpClass(cls):
        if os.environ.get("SD_SKIP_SLOW_ART"):
            raise unittest.SkipTest("SD_SKIP_SLOW_ART is set")
        import gen_hound
        cls.g = gen_hound
        cls.P, cls.anchors = gen_hound.death_model("N")
        cls.m = gen_hound.corpse_metrics("N")

    def test_every_part_rests_on_the_floor(self):
        g = self.g
        for part in ("chest", "croup", "neck", "head", "tail", "paw_fore_right", "paw_fore_left",
                     "paw_hind_right", "paw_hind_left"):
            self.assertIn(part, self.m["lowest"])
            y = self.m["lowest"][part]
            self.assertLessEqual(y, g.LYING_MAX, f"{part} is {y} units off the floor: propped up")
            self.assertGreaterEqual(y, -g.LYING_MAX, f"{part} sinks {y} units into the floor")

    def test_nothing_propped_up(self):
        g = self.g
        self.assertLess(self.m["top"], g.LYING_TOP, "a part stands up off the body")
        self.assertGreaterEqual(self.m["span"], g.LYING_SPAN, "the supports bunch up: it rests on one point")
        self.assertLess(self.anchors["nose"][1], 3.0, "the head lies on the floor")

    def test_on_its_side_with_a_level_spine(self):
        self.assertLess(abs(self.m["back_up"]), 0.1, "the spine's up axis lies level: on its side")
        self.assertLess(self.m["spine_drop"], 1.5, "withers and sacrum at one height")

    def test_legs_relaxed(self):
        for leg, bends in self.m["legs"].items():
            self.assertTrue(all(b <= 100.0 for b in bends), f"{leg} folded hard: {bends}")
            self.assertTrue(any(b >= RELAXED_BEND for b in bends), f"{leg} stiff, not relaxed: {bends}")

    def test_in_a_pool_that_grew(self):
        g = self.g

        def pool_of(frame):
            _, a = g.death_model(frame)
            return [p for p in g.death_blood(frame, a) if p.grp == "pool"]

        pool_n = [p for p in g.death_blood("N", self.anchors) if p.grp == "pool"]
        self.assertTrue(pool_n)
        self.assertTrue(all(abs(p.bound()[0][1]) < 1.0 for p in pool_n), "the pool is on the floor")
        body_x = [p.bound()[0][0] for p in self.P if p.grp == "body"]
        main = max(pool_n, key=lambda p: float(p.r[0]))
        self.assertTrue(min(body_x) <= main.a[0] <= max(body_x), "the pool lies under the body")
        self.assertFalse(pool_of("K"))
        self.assertLess(max(float(p.r[0]) for p in pool_of("L")), float(main.r[0]))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullSetRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("SD_SKIP_SLOW_ART"):
            raise unittest.SkipTest("SD_SKIP_SLOW_ART is set")
        import gen_hound
        import rig_core
        cls.g, cls.core = gen_hound, rig_core
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}
        cls.spr = {k: gen_hound.render_full(*k) for k in (("H", 1), ("H", 3), ("A", 2), ("D", 4), ("I", 0))}
        cls.n = gen_hound.render_full_layers("N", 0)

    @staticmethod
    def height(rgba):
        ys = np.nonzero(rgba[..., 3] > 0)[0]
        return int(ys.max() - ys.min() + 1)

    def colours(self, rgba, sel=None):
        a = rgba[..., 3] > 0 if sel is None else sel
        return {tuple(int(v) for v in c) for c in rgba[..., :3][a]}

    @slow
    def test_palette_and_hard_alpha(self):
        for k, rgba in {**self.spr, ("N", 0): self.n.rgba}.items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, k)
            self.assertLessEqual(self.colours(rgba), self.palette, k)

    @slow
    def test_heights(self):
        for k in (("H", 1), ("H", 3), ("A", 2)):
            self.assertLess(self.height(self.spr[k]), self.g.MAX_H, k)

    @slow
    def test_mirror_pair(self):
        self.assertTrue(np.array_equal(self.g.render_full("H", 7), self.spr[("H", 3)][:, ::-1]))

    @slow
    def test_blood_dark_red_and_abundant(self):
        g, core = self.g, self.core
        ids = core.material_ids(g.full_materials())
        sel = np.isin(self.n.mat, [ids["blood"], ids["pool"]])
        allowed = set(core.ramp("flag_red")[:g.BLOOD_MAX_INDEX + 1]) | {(0, 0, 0)}
        self.assertLessEqual(self.colours(self.n.rgba, sel), allowed)
        self.assertGreater(sel.sum() / (self.n.mat >= 0).sum(), 0.25, "D49: abundant blood")

    @slow
    def test_corpse_reads_low_and_long(self):
        ids = self.core.material_ids(self.g.full_materials())
        body = (self.n.mat >= 0) & ~np.isin(self.n.mat, [ids["blood"], ids["pool"]])
        ys, xs = np.nonzero(body)
        h, w = int(np.ptp(ys)) + 1, int(np.ptp(xs)) + 1
        self.assertLess(h, 26)
        self.assertGreater(w, 2.5 * h, "lying across, not standing")

    @slow
    def test_files_on_disk(self):
        g, core = self.g, self.core
        if not g.FULL_DIR.is_dir():
            self.skipTest("full_A/ not built (run gen_hound.py --full)")
        for f, r in g.full_plan():
            path = g.FULL_DIR / f"{g.full_lump(f, r)}.png"
            self.assertTrue(path.is_file(), path.name)
            self.assertEqual(core.read_grab(path), core.grab_offsets(g.full_canvas(f)), path.name)
            with Image.open(path) as im:
                rgba = np.asarray(im.convert("RGBA"))
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, path.name)
            self.assertLessEqual(self.colours(rgba), self.palette, path.name)


if __name__ == "__main__":
    unittest.main()
