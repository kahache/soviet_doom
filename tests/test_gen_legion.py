"""Contract of tools/art/gen_legion.py (F5, Liberty Legion trooper: the D35
design sweep and, since D48, cell C's full frame set).

Two tiers. The cheap tests always run (no rendering):

  no font    the generator never rasterises text with a system font
  ramp       the flesh ramp is palette v2's official flesh_pink (D45), read
             from palette.json, and identical to the sweep's candidate
             (palette.py's rule on the sweep's endpoints): 16 colours, none in
             v1, at v2's slots
  cells      six cells, A is the brief, every lump name fits Doom's 8 chars
  flag       the D12 flag stamp is 7x5 and mirrors so the canton leads
  core       the trooper is a figure on tools/art/rig_core.py: the ramp is
             registered there, lit() keeps the pink, chrome is a material
             shading, the flag is a core insignia
  full set   (D48) BESTIARY §4 / MOD-SPEC §6.3: SDLT A-G at 8 rotations,
             H-U at 0, 70 lumps; every frame letter legion_trooper.zs plays
             exists, its tics are the GIFs' tics; the full set's A and F are
             the sweep's cell C poses; limbs labelled
  blood      (D48, D49) the deaths bleed dark red: flag_red 0-5 and black on
             their own table (no id moved), A-G never bleed; the burst, the
             splats, the stain, the pool growing K -> L, the gib's jets,
             chunks (chrome shards among them) and pool; splats stay inside
             the canvas

The render tests run under `tools/verify.py art`, not `fast` (each sprite
is a sphere trace of a few seconds; SD_SKIP_SLOW_ART skips them):

  palette    every opaque pixel is palette v1 or flesh_pink, hard alpha
  faction    no military_green (the world's), no khaki_olive (the Reich's);
             the only flag_red is the flag; the body is LIGHTER than concrete
  scale      the standing figure is Doom's 56-unit actor
  flash      frame F carries the muzzle flash
  seed       the same sprite renders identically twice
  full set   A1 is the sweep's cell C pixel for pixel (and the PNG on disk,
             when present); every lump is palette v2 with hard alpha; A-G
             keep the faction contract; the dead (L) and the gibbed (U) carry
             a lot of dark red and lie on the floor; the edges are clear
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
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_legion.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the Legion renders")


def palette_ramps() -> dict:
    pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
    return pal, {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)

    def test_palette_json_is_not_written(self):
        code = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("PALETTE_JSON", code)
        self.assertIsNone(re.search(r"palette\.json[^\n]*write", code))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class CheapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_legion
        cls.g = gen_legion

    def test_flesh_ramp_is_palette_v2_and_the_candidate(self):
        g = self.g
        pal, _ = palette_ramps()
        ramp = g.flesh_ramp()
        official = [tuple(c) for c in next(r for r in pal["added_ramps"] if r["name"] == "flesh_pink")["colours"]]
        self.assertEqual(ramp, official)                        # read from palette.json, not built here
        self.assertEqual(ramp, g.candidate_ramp())              # the sweep's candidate, colour for colour
        self.assertEqual(ramp, g.palgen.ramp_colours("flesh_pink"))
        lo, hi = pal["added_index"]["flesh_pink"]
        self.assertEqual([tuple(c) for c in pal["colours_v2"][lo:hi + 1]], ramp)
        self.assertEqual(g.palette_v2()[lo:hi + 1], ramp)
        self.assertEqual(len(ramp), 16)
        self.assertEqual(ramp[0], g.FLESH_DARK)
        self.assertEqual(ramp[-1], g.FLESH_LIGHT)
        lum = [0.299 * r + 0.587 * gg + 0.114 * b for r, gg, b in ramp]
        self.assertEqual(lum, sorted(lum))                      # darkest first, like every ramp
        v1 = {tuple(c) for c in pal["colours"]}
        self.assertFalse(set(ramp) & v1)
        self.assertLessEqual(len(v1) + len(set(ramp)), 256)
        for r, gg, b in ramp[4:]:
            self.assertGreater(r, b)                            # flesh, not grey or blue

    def test_cells_and_names(self):
        g = self.g
        self.assertEqual([c.key for c in g.CELLS], list("ABCDEF"))
        a = g.CELL["A"]
        self.assertEqual((a.face, a.torso, a.shoulders), ("smooth", "cuirass", "pauldron"))
        self.assertIn(g.RECOMMENDED, g.CELL)
        for c in g.CELLS:
            for frame, rot in g.VIEWS:
                lump = g.lump_name(c, frame, rot).replace(f"_{c.key}_", "")
                self.assertRegex(lump, r"^SDLT[A-U][0-8]$")
                self.assertLessEqual(len(lump), 8)

    def test_on_the_core(self):
        g = self.g
        core = g.core
        self.assertEqual(core.ramp(g.FLESH), g.flesh_ramp())
        self.assertEqual(g.MATERIALS["flesh"].colours()[0], g.flesh_ramp()[3])
        self.assertEqual(g.MATERIALS["chrome"].shading, "chrome")
        self.assertEqual(g.FLAG_INSIGNIA.size, (7, 5))
        self.assertTrue(g.FLAG_INSIGNIA.mirror_facing_right)
        pink = g.flesh_ramp()[12]
        img = np.zeros((2, 2, 3), np.uint8)
        img[:] = pink
        self.assertEqual(tuple(int(v) for v in g.lit(img, g.flat.LIGHT_FULL)[0, 0]), pink)   # not re-quantised to v1

    def test_flag_mirrors_canton_first(self):
        g = self.g
        self.assertEqual({len(r) for r in g.FLAG}, {7})
        self.assertEqual(len(g.FLAG), 5)
        blue = g.artlib.ramp("steel_blue")[3]
        plain = {(i, j): c for i, j, c in g.flag_pixels(False)}
        mirror = {(i, j): c for i, j, c in g.flag_pixels(True)}
        self.assertEqual(plain[(0, 0)], blue)
        self.assertEqual(mirror[(6, 0)], blue)
        for (i, j), c in plain.items():
            self.assertEqual(mirror[(6 - i, j)], c)


ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "legion_trooper.zs"
MODSPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
STATE_LINE = re.compile(r"^\s*(SPOS|SDLT)\s+([A-Z]+)\s+(-?\d+)", re.M)


def zs_states() -> dict[str, list[tuple[str, int]]]:
    """legion_trooper.zs's states: label -> [(frame letters, tics)], for the
    trooper's sprite whatever it is named today (SPOS, or SDLT after the swap)."""
    out: dict[str, list[tuple[str, int]]] = {}
    label = None
    for line in ZS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(\w+):\s*$", line)
        if m:
            label = m.group(1)
            continue
        m = STATE_LINE.match(line)
        if m and label:
            out.setdefault(label, []).append((m.group(2), int(m.group(3))))
    return out


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullSetTests(unittest.TestCase):
    """D48: cell C's whole frame set (no rendering)."""

    @classmethod
    def setUpClass(cls):
        import gen_legion
        cls.g = gen_legion

    def test_plan_is_bestiary_4(self):
        g = self.g
        plan = g.full_plan()
        self.assertEqual(len(plan), 7 * 8 + 5 + 9)
        self.assertEqual(len(set(plan)), len(plan))
        for frame, rot in plan:
            name = g.full_lump(frame, rot)
            self.assertRegex(name, r"^SDLT[A-U][0-8]$")
            self.assertLessEqual(len(name), 8)
            self.assertEqual(rot == 0, frame in "HIJKLMNOPQRSTU", name)
        self.assertEqual(sorted({r for _, r in plan if r}), list(range(1, 9)))   # handed: no mirrored pairs

    def test_lump_is_reserved_in_mod_spec(self):
        row = next(line for line in MODSPEC.read_text(encoding="utf-8").splitlines()
                   if line.startswith("| `SD_LegionTrooper` |") and "A–G (8)" in line)
        self.assertIn(f"`{self.g.SPRITE}`", row)

    def test_every_zs_frame_is_drawn_at_its_tics(self):
        g = self.g
        states = zs_states()
        drawn = {f for f, _ in g.full_plan()}
        for label, lines in states.items():
            for letters, _ in lines:
                self.assertLessEqual(set(letters), drawn, label)
        self.assertEqual({t for _, t in states["See"]}, {g.WALK_TICS})
        self.assertEqual([t for _, t in states["Missile"]], list(g.ATTACK_TICS[1:]))
        self.assertEqual([t for _, t in states["Pain"]], list(g.PAIN_TICS[1:3]))
        death = states["Death"]
        self.assertEqual({t for _, t in death[:-1]}, {g.DEATH_TICS[1]})
        self.assertEqual(death[-1], ("L", -1))
        xdeath = states["XDeath"]
        self.assertEqual({t for _, t in xdeath[:-1]}, {g.GIB_TICS[1]})
        self.assertEqual(xdeath[-1], ("U", -1))
        self.assertEqual("".join(f for f, _ in xdeath), g.GIB_FRAMES)

    def test_a_and_f_are_the_sweeps_cell_c(self):
        g = self.g
        self.assertEqual(g.FULL_CELL, g.CELL["C"])
        for f in "AF":
            full, sweep = g.FULL_POSES[f], g.POSES[f]
            self.assertEqual((full.foot_l, full.foot_r, full.bob, full.carry, full.flash, full.canvas),
                             (sweep.foot_l, sweep.foot_r, sweep.bob, sweep.carry, sweep.flash, sweep.canvas), f)
            self.assertEqual((full.lean, full.head_pitch, full.roll, full.gun_tilt), (0.0, 0.0, 0.0, 0.0), f)
        e = g.FULL_POSES["E"]
        self.assertFalse(e.flash)
        self.assertEqual((e.foot_l, e.carry, e.canvas), (g.POSES["F"].foot_l, "aim", g.AIM))

    def test_limbs_are_labelled(self):
        g = self.g
        core = g.core
        for frame in "ADGH":
            P, _ = g.build_model(g.FULL_CELL, g.FULL_POSES[frame])
            for limb in ("leg", "arm"):
                self.assertTrue(core.select(P, limb=limb, side=core.LEFT), (frame, limb))
                self.assertTrue(core.select(P, limb=limb, side=core.RIGHT), (frame, limb))
            self.assertEqual({p.grp for p in core.select(P, limb="leg", side=core.LEFT)}, {"leg_l"})
            self.assertEqual(len(core.select(P, tag="patch")), 1)

    def test_the_fall_lies_on_the_floor(self):
        g = self.g
        P, _ = g.build_model(g.FULL_CELL, g.FULL_POSES["L"])
        body = [p for p in P if p.grp != "gun"]
        self.assertAlmostEqual(g.core.lowest_y(body), 0.0, delta=0.1)
        torso = next(p for p in P if p.tag == "torso")
        self.assertLess(float(torso.bound()[0][1]), 22.0)      # on his side, propped by the pads (35 upright)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class BloodTests(unittest.TestCase):
    """D48, D49: much blood in the deaths, dark red (no rendering)."""

    @classmethod
    def setUpClass(cls):
        import gen_legion
        cls.g = gen_legion

    def test_blood_table_keeps_ids_and_is_dark_red(self):
        g = self.g
        names = list(g.MATERIALS_BLOOD)
        self.assertEqual(names[:len(g.MATERIALS)], list(g.MATERIALS))     # no id moved
        self.assertEqual(names[len(g.MATERIALS):], ["gore", "blood", "pool"])
        self.assertNotIn("blood", g.MATERIALS)                             # the sweep's table is untouched
        flag = g.core.ramp("flag_red")
        self.assertEqual(g.blood_colours(), {tuple(c) for c in flag[:g.BLOOD_MAX_INDEX + 1]})
        reds = g.blood_colours() | {(0, 0, 0)}
        for name in ("blood", "pool", "gore"):
            self.assertEqual(g.MATERIALS_BLOOD[name].ramps, {"flag_red"}, name)
            self.assertLessEqual(set(g.MATERIALS_BLOOD[name].colours()), reds, name)
        flag_reds = {g.artlib.ramp(n)[k] for n, k in g.FLAG_COLOURS.values() if n == "flag_red"}
        self.assertTrue(flag_reds)
        self.assertFalse(flag_reds & g.blood_colours())                    # the flag stays brighter
        self.assertTrue(g.MATERIALS_BLOOD["blood"].flat)                   # no rim: a drop stays red

    def test_walk_aim_fire_pain_do_not_bleed(self):
        g = self.g
        for frame in "ABCDEFG":
            prims, _, table = g.build_frame(frame)
            self.assertIs(table, g.MATERIALS, frame)
            self.assertFalse({p.mat for p in prims} & {"blood", "pool", "gore"}, frame)

    def test_death_bleeds_and_the_pool_grows(self):
        g = self.g
        groups = {}
        for frame in "HIJKL":
            prims, _, table = g.build_frame(frame)
            self.assertIs(table, g.MATERIALS_BLOOD)
            groups[frame] = prims
        spray = lambda f: [p for p in groups[f] if p.grp == "spray"]  # noqa: E731
        splat = lambda f: [p for p in groups[f] if p.grp == "splat"]  # noqa: E731
        area = lambda f: sum(p.r[0] * p.r[2] for p in groups[f] if p.grp == "pool")  # noqa: E731
        self.assertGreaterEqual(len(spray("H")), g.N_SPRAY)
        self.assertFalse(splat("H"))
        self.assertGreater(len(splat("L")), g.N_SPRAY // 2)
        self.assertEqual(area("H") + area("I") + area("J"), 0)
        self.assertGreater(area("K"), 0)
        self.assertGreater(area("L"), 2 * area("K"))
        for f in "HIJKL":                                                    # the stain soaks wider
            stain = max(p.r[0] for p in groups[f] if p.grp == "blood" and p.kind == "ellipsoid")
            self.assertAlmostEqual(stain, g.STAIN_R[f])

    def test_gib_bursts_jets_and_pools(self):
        g = self.g
        for frame in "MPU":
            prims, _, table = g.build_frame(frame)
            self.assertIs(table, g.MATERIALS_BLOOD)
            self.assertGreater(len([p for p in prims if p.mat == "blood"]), g.N_GIB_SPRAY - 1, frame)
        p, _ = g.build_gib("P")
        chunks = [q for q in p if q.grp == "chunk"]
        self.assertEqual(len(chunks), g.N_CHUNKS)
        self.assertIn("chrome", {q.mat for q in chunks})                     # shards of the cuirass
        jet = [q for q in p if q.grp == "spray" and q.bound()[0][1] > g.WAIST_Y]
        self.assertGreater(len(jet), 10)
        self.assertFalse([q for q in p if q.tag == "patch"])                 # the flag went with the chunks
        u, _ = g.build_gib("U")
        self.assertTrue([q for q in u if q.grp == "pool"])
        helmet = [q for q in u if q.grp == "helmet"]
        self.assertAlmostEqual(g.core.lowest_y(helmet), 0.0, delta=0.1)    # the M1 lies on the floor

    def test_droplet_lands_as_a_splat_inside_the_canvas(self):
        g = self.g
        flying = g.droplet(g.core.V(0, 30, 0), g.core.V(10.0, 20.0, 0.0), 0.05, 1.0)
        landed = g.droplet(g.core.V(0, 30, 0), g.core.V(10.0, 20.0, 0.0), 2.0, 1.0)
        far = g.droplet(g.core.V(0, 30, 0), g.core.V(-200.0, 20.0, 200.0), 2.0, 1.0)
        self.assertEqual((flying.grp, landed.grp), ("spray", "splat"))
        self.assertLess(landed.r[1], 0.5)
        self.assertEqual((far.a[0], far.a[2]), (-g.SPRAY_X, g.SPRAY_Z))


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_legion
        g = cls.g = gen_legion
        cls.idle = g.render(g.CELL["A"], "A", 1)
        cls.fire = g.render(g.CELL[g.RECOMMENDED], "F", 1)
        pal, ramps = palette_ramps()
        cls.allowed = {tuple(c) for c in pal["colours"]} | set(g.flesh_ramp())
        cls.ramps = ramps

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_palette_and_hard_alpha(self):
        for rgba in (self.idle, self.fire):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertLessEqual(self.opaque(rgba), self.allowed)

    def test_faction_contract(self):
        for rgba in (self.idle, self.fire):
            cols = self.opaque(rgba)
            self.assertFalse(cols & self.ramps["military_green"])
            self.assertFalse(cols & self.ramps["khaki_olive"])
            self.assertTrue(cols & set(self.g.flesh_ramp()))
        red = self.ramps["flag_red"]
        flag_red = {self.g.artlib.ramp(n)[k] for n, k in self.g.FLAG_COLOURS.values()} & red
        self.assertTrue(self.opaque(self.idle) & flag_red)      # the D12 flag is on the front view

    def test_lighter_than_concrete(self):
        g = self.g
        m = g.measure(self.idle)
        concrete = float(g.flat.luma(g.wall_rgb("SDCONC1")).mean())
        self.assertGreater(m["mass_luma"], concrete + 20)       # BESTIARY §2.1: the light faction
        self.assertGreater(m["body_luma"], concrete)

    def test_scale_and_canvas(self):
        g = self.g
        self.assertEqual(self.idle.shape, (g.STAND.h, g.STAND.w, 4))
        self.assertLessEqual(abs(g.measure(self.idle)["height_px"] - g.DOOM_HEIGHT), 4)

    def test_fire_has_flash(self):
        cols = self.opaque(self.fire)
        self.assertTrue(cols & (self.ramps["cream_yellow"] | self.ramps["hazard_yellow"]))
        self.assertFalse(self.opaque(self.idle) & self.ramps["hazard_yellow"])

    def test_deterministic(self):
        again = self.g.render(self.g.CELL["A"], "A", 1)
        self.assertTrue(np.array_equal(again, self.idle))


MIN_RED_DEAD = 150      # px of blood red on the dead (L) and the gibbed (U): the rifleman's D48 bar
POOL_BELOW_SOLE = 5     # px: a floor pool lies in front of the body, below the sole line


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class FullRenderTests(unittest.TestCase):
    """D48: cell C's full set, a few lumps rendered."""

    @classmethod
    def setUpClass(cls):
        import gen_legion
        g = cls.g = gen_legion
        cls.r = {k: g.render_full(*k) for k in (("A", 1), ("C", 3), ("G", 5), ("F", 7), ("L", 0), ("U", 0))}
        pal, ramps = palette_ramps()
        cls.v2 = {tuple(c) for c in pal["colours_v2"]}
        cls.ramps = ramps

    def opaque(self, rgba):
        return {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}

    def test_a1_is_the_sweeps_cell_c(self):
        g = self.g
        self.assertTrue(np.array_equal(self.r[("A", 1)], g.render(g.CELL["C"], "A", 1)))
        path = g.OUT_DIR / f"{g.lump_name(g.CELL['C'], 'A', 1)}.png"
        if path.is_file():                  # work/ is gitignored: absent in CI
            with Image.open(path) as im:
                self.assertTrue(np.array_equal(np.asarray(im.convert("RGBA")), self.r[("A", 1)]))

    def test_palette_v2_and_hard_alpha(self):
        for k, rgba in self.r.items():
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, k)
            self.assertLessEqual(self.opaque(rgba), self.v2, k)

    def test_faction_contract_while_alive(self):
        g = self.g
        for k in (("A", 1), ("C", 3), ("G", 5), ("F", 7)):
            cols = self.opaque(self.r[k])
            self.assertFalse(cols & self.ramps["military_green"], k)
            self.assertFalse(cols & self.ramps["khaki_olive"], k)
            self.assertFalse(cols & g.blood_colours() - {g.core.ramp("flag_red")[5]}, k)   # no blood while alive
        for k in (("L", 0), ("U", 0)):
            self.assertFalse(self.opaque(self.r[k]) & self.ramps["military_green"], k)

    def test_the_dead_bleed_dark_red_and_lie_on_the_floor(self):
        g = self.g
        for k, cv in ((("L", 0), g.DEATH), (("U", 0), g.GIB)):
            rgba = self.r[k]
            self.assertEqual(rgba.shape, (cv.h, cv.w, 4), k)
            self.assertGreaterEqual(g.red_pixels(rgba), MIN_RED_DEAD, k)
            m = g.measure_full(rgba)
            self.assertLess(m["height_px"], 40, k)
            self.assertGreater(m["width_px"], m["height_px"], k)
            self.assertLessEqual(abs(m["lowest_row"] - cv.foot_row), POOL_BELOW_SOLE, k)

    def test_scale(self):
        g = self.g
        for k in (("A", 1), ("C", 3)):
            m = g.measure_full(self.r[k])
            self.assertLessEqual(abs(m["height_px"] - g.DOOM_HEIGHT), 4, k)
            self.assertLessEqual(abs(m["lowest_row"] - g.STAND.foot_row), 1, k)

    def test_deterministic_with_grab(self):
        g = self.g
        self.assertTrue(np.array_equal(g.render_full("L", 0), self.r[("L", 0)]))
        with tempfile.TemporaryDirectory() as tmp:
            path = g.save_sprite(self.r[("U", 0)], Path(tmp) / "SDLTU0.png", g.GIB)
            self.assertEqual(g.core.read_grab(path), (g.GIB.cx, g.GIB.foot_row - g.FEET_SINK))


if __name__ == "__main__":
    unittest.main()
