"""Contract of tools/art/gen_general.py (F5, backlog N12: the General's design
sweep, D71's CD turnaround and D72's full set: see the classes' docstrings).

Cheap tests (no rendering, always run):

  no font     the generator never rasterises text, never writes palette.json
              and never writes under assets/; the contact sheet's letters
              come from its own GLYPHS table
  cells       five cells, A is the brief; every other cell differs from A in
              exactly one dimension; views are rotations 1, 3, 5 and the
              firing frame F; the lump names fit Doom's 8
  table       the material table is a COPY of the Legion trooper's
              (gen_legion): every approved id is where it was, the approved
              table is untouched
  faction     no material uses the Reich's khaki_olive or the world's
              military_green (ART-BIBLE §6.2); the flags are the only
              saturated red (§6.3)
  insignia    the pennant carries the mod's one drawing of the D12 symbol
              (gen_enemy.ARMBAND) and the trooper's US flag, unmirrored; the
              cloak's disc has the same handedness as the armband
  scale       the canvas holds his 100-unit actor; the grAb is the body axis

Render tests (`tools/verify.py art`; SD_SKIP_SLOW_ART skips them):

  palette     every opaque pixel is a palette v2 colour, hard alpha
  faction     the rendered colours keep the contract above; flesh_pink shows
  size        he is drawn to his actor (90-100 px), far taller than the
              56-unit infantry and the approved Panzermensch
  value       he is a light figure, brighter than the approved Panzermensch
              (BESTIARY §9: bright; §8: the brute is the darkest mass)
  insignia    both flags show on the pennants from the front
  seed        the same sprite renders identically twice
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

SOURCE = ART_TOOLS / "gen_general.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the General's renders")


def ramp_sets() -> dict[str, set]:
    """Every ramp of palette v1 and v2 (v2's added ramps through palette.py)."""
    import palette as palgen
    pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
    out = {r["name"]: {tuple(c) for c in r["colours"]} for r in pal["ramps"]}
    for name in ("flesh_pink", "marble_red", "mosaic_cobalt", "mosaic_gold"):
        out.setdefault(name, {tuple(c) for c in palgen.ramp_colours(name)})
    return out


class NoFontTests(unittest.TestCase):
    def test_no_system_font_and_no_palette_write(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(", r"ImageDraw"):
            self.assertIsNone(re.search(pattern, code), pattern)
        self.assertNotIn("palette.json\").write", code)
        # assets/ is read (approved sprites, MAP03's walls), never written
        self.assertNotRegex(code, r"ASSETS\s*/[^\n]*\.(save|write_text|write_bytes)\(")


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_enemy
        import gen_general
        import gen_legion
        cls.g, cls.legion, cls.enemy = gen_general, gen_legion, gen_enemy

    def test_cells_and_views(self):
        g = self.g
        self.assertEqual([c.key for c in g.CELLS], list("ABCDE"))
        a = g.CELLS[0]
        self.assertTrue(a.title.startswith("Brief"))
        self.assertEqual((a.face, a.weapon, a.flags, a.chest), ("plate", "revolver", "pennants", "cuirass"))
        for c in g.CELLS[1:]:
            diff = [f for f in ("face", "weapon", "flags", "chest") if getattr(c, f) != getattr(a, f)]
            self.assertEqual(len(diff), 1, c.key)
        self.assertEqual([r for _, r in g.VIEWS], [1, 3, 5, 1])
        self.assertEqual(g.VIEWS[-1][0], "F")           # general.zs: CYBR F fires (A_SD_GeneralShot)
        self.assertTrue(g.POSES["F"].fire)
        for f, r in g.VIEWS:
            self.assertLessEqual(len(f"{g.SPRITE}{f}{r}"), 8)
        self.assertEqual(g.SPRITE, "SDGN")
        self.assertIn(g.RECOMMENDED, "ABCDE")
        for name in ("VERDICT", "HONEST", "CEO_ASK"):
            self.assertTrue(getattr(g, name), name)
        self.assertLessEqual(set(c.key for c in g.CELLS), set(g.GLYPHS))

    def test_the_actor_is_read_from_the_class(self):
        zs = (PROJECT_ROOT / "src" / "zscript" / "monsters" / "general.zs").read_text(encoding="utf-8")
        self.assertIn(f"SD_GENERAL_HEIGHT     = {self.g.ACTOR_HEIGHT};", zs)
        self.assertIn(f"SD_GENERAL_RADIUS     = {self.g.ACTOR_RADIUS};", zs)

    def test_table_is_a_copy_with_ids_kept(self):
        g, base = self.g, self.legion.MATERIALS
        self.assertIsNot(g.GN_MATERIALS, base)
        self.assertEqual(list(g.GN_MATERIALS)[:len(base)], list(base))
        for name in base:
            self.assertEqual(g.GN_MATERIALS[name], base[name])
        for name in g.GN_NEW:
            self.assertNotIn(name, base)

    def test_faction_materials(self):
        g = self.g
        for name, mat in g.GN_MATERIALS.items():
            self.assertFalse(mat.ramps & g.FORBIDDEN_RAMPS, name)
        red = {n for n, m in g.GN_NEW.items() if "flag_red" in m.ramps}
        self.assertEqual(red, {"pennant_red"})          # the flags and nothing else (ART-BIBLE §6.3)

    def test_pennants_carry_the_mods_insignia(self):
        g = self.g
        self.assertEqual(g.PENNANT_REICH[:7], self.enemy.ARMBAND)
        self.assertEqual(g.PENNANT_US[:len(self.legion.FLAG)], self.legion.FLAG)
        for pat in (g.PENNANT_REICH, g.PENNANT_US, g.CLOAK_DISC, g.CANTON_STARS):
            self.assertEqual(len({len(r) for r in pat}), 1)
            self.assertTrue(set("".join(pat)) <= set(g.STAMP_COLOURS) | {"_"})
        tags = {i.tag for i in g.PENNANT_INSIGNIA}
        self.assertEqual(tags, {"pen_reich", "pen_us"})

    def test_cloak_disc_has_the_armbands_handedness(self):
        disc = self.g.CLOAK_DISC
        arm = [r[1:6] for r in self.enemy.ARMBAND[1:6]]          # the 5x5 symbol inside the band
        sym = [r[2:9] for r in disc[2:9]]                         # the 7x7 symbol inside the disc
        # same arms: the top row runs right from the centre, the bottom row left
        self.assertEqual(arm[0][0], "K")
        self.assertEqual(sym[0][0], "K")
        self.assertTrue(all(c == "K" for c in sym[0][3:]) and all(c == "K" for c in arm[0][2:]))
        self.assertTrue(all(c == "K" for c in sym[6][:4]) and all(c == "K" for c in arm[4][:3]))

    def test_canvas_and_grab(self):
        g = self.g
        gx, gy = g.grab()
        self.assertEqual(gx * 2, g.CV.w)
        self.assertGreater(g.CV.foot_row, g.ACTOR_HEIGHT)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class CDContractTests(unittest.TestCase):
    """D71: CD is C with D's cloak, fitted inside his front silhouette."""

    @classmethod
    def setUpClass(cls):
        import gen_general
        cls.g = gen_general

    def test_cd_is_c_plus_the_cloak(self):
        g = self.g
        c, cd = g.CELL["C"], g.CD
        self.assertEqual((cd.face, cd.weapon, cd.chest), (c.face, c.weapon, c.chest))
        self.assertEqual(cd.flags, "both")
        self.assertNotIn(cd, g.CELLS)                    # the sweep's five cells are unchanged
        tags = {i.tag for i in g.insignia_for(cd)}
        self.assertEqual(tags, {"pen_reich", "pen_us", "cape_reich", "canton"})
        prims, _ = g.model(cd, "A")
        groups = {p.grp for p in prims}
        self.assertTrue({"pen_l", "pen_r", "cape"} <= groups)

    def test_fitted_cloak_stays_inside_the_body(self):
        """Every cloak part's clips keep it inside the coat's (below the
        waist) or the cuirass's (above) width less CD_TRIM, between the
        hem and the pauldrons."""
        g = self.g
        self.assertGreater(g.CD_CAPE_Y0, g.HEM_Y)
        self.assertLess(g.CD_CAPE_Y1, g.SHOULDER[1])
        lower, upper = g.fitted_segments()
        for seg, y0, y1, width in ((lower, g.CD_CAPE_Y0, g.CD_CAPE_WAIST, g.coat_front),
                                   (upper, g.CD_CAPE_WAIST, g.CD_CAPE_Y1, None)):
            for y in np.linspace(y0, y1, 9):
                if width is None:
                    r = g.TORSO_R0 + (g.TORSO_R1 - g.TORSO_R0) * (y - g.WAIST_Y) / (g.CHEST_Y - g.WAIST_Y)
                else:
                    r = g.HEM_R + (g.TORSO_R0 + 1.2 - g.HEM_R) * (y - g.HEM_Y) / (g.WAIST_Y + 1.0 - g.HEM_Y)
                for x in (r - g.CD_TRIM + 0.05, -(r - g.CD_TRIM + 0.05)):
                    p = np.array([x, y, -10.0])
                    self.assertTrue(any(n @ p > off for n, off in seg), (y, x))   # outside: clipped


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class CDRenderTests(unittest.TestCase):
    """D71: from the front CD is C; from the back the cloak is there."""

    @classmethod
    def setUpClass(cls):
        import gen_general as g
        cls.g = g
        cls.front, cls.front_cloak = g.render_cd("A", 1)
        cls.fire, cls.fire_cloak = g.render_cd("F", 1)
        cls.back, cls.back_cloak = g.render_cd("A", 5)
        cls.c_front = g.render("C", "A", 1)
        cls.c_fire = g.render("C", "F", 1)

    def test_front_is_c(self):
        g = self.g
        self.assertEqual(self.front_cloak, 0)
        self.assertEqual(self.fire_cloak, 0)
        for cd, c in ((self.front, self.c_front), (self.fire, self.c_fire)):
            np.testing.assert_array_equal(cd[..., 3] > 0, c[..., 3] > 0)        # the same silhouette
            self.assertEqual(g.silhouette_width(cd), g.silhouette_width(c))
            self.assertLessEqual(int((cd != c).any(axis=-1).sum()), 12)        # shading only (AO by the hidden cloak)

    def test_back_shows_both_flags(self):
        g = self.g
        self.assertGreater(self.back_cloak, 800)
        r = ramp_sets()
        a = self.back[..., 3] > 0
        cols = {tuple(int(v) for v in p) for p in self.back[..., :3][a]}
        self.assertTrue(cols & r["flag_red"])
        self.assertIn((0, 0, 0), cols)
        self.assertIn(tuple(g.core.ramp("plaster_warm")[13]), cols)            # the disc
        self.assertIn(tuple(g.core.ramp("plaster_warm")[15]), cols)            # the canton's stars

    def test_deterministic(self):
        np.testing.assert_array_equal(self.g.render_cd("A", 1)[0], self.front)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_general as g
        import gen_heavy
        cls.g = g
        cls.front = g.render(g.RECOMMENDED, "A", 1)
        cls.fire = g.render(g.RECOMMENDED, "F", 1)
        cls.brief = g.render("A", "A", 1)
        cls.ramps = ramp_sets()
        cls.pm = gen_heavy.approved("SDPMA1", "panzermensch")

    def colours(self, rgba):
        a = rgba[..., 3] > 0
        return {tuple(int(v) for v in p) for p in rgba[..., :3][a]}

    def test_palette_v2_and_hard_alpha(self):
        v2 = set(self.g.heavy.palette_v2())
        for rgba in (self.front, self.fire, self.brief):
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
            self.assertTrue(self.colours(rgba) <= v2)

    def test_faction_colours(self):
        r = self.ramps
        for rgba in (self.front, self.fire, self.brief):
            cols = self.colours(rgba)
            self.assertFalse(cols & (r["khaki_olive"] | r["military_green"]))
            self.assertTrue(cols & r["flesh_pink"])
            self.assertTrue(cols & r["steel_blue"])
            self.assertTrue(cols & r["hazard_yellow"])

    def test_size(self):
        m = self.g.measure(self.front)
        self.assertGreaterEqual(m["height_px"], 90)
        self.assertLessEqual(m["height_px"], self.g.ACTOR_HEIGHT)
        if self.pm:
            pa = self.pm[0][..., 3] > 0
            self.assertGreater(m["height_px"], int(np.ptp(np.nonzero(pa)[0])) + 15)

    def test_value(self):
        m = self.g.measure(self.front)
        if self.pm:
            a = self.pm[0][..., 3] > 0
            pm_luma = float(self.g.flat.luma(self.pm[0][..., :3])[a].mean())
            self.assertGreater(m["body_luma"], pm_luma + 40)

    def test_flags_from_the_front(self):
        r = self.ramps
        cols = self.colours(self.brief)
        self.assertIn((0, 0, 0), cols)
        self.assertTrue(cols & r["flag_red"])
        self.assertIn(tuple(self.g.core.ramp("steel_blue")[3]), cols)       # the canton

    def test_seed(self):
        np.testing.assert_array_equal(self.g.render(self.g.RECOMMENDED, "A", 1), self.front)


# ---------------------------------------------------------------- the full set (D72)
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class FullSetContractTests(unittest.TestCase):
    """D72: CD's full set. The letters come from general.zs (Summon's
    borrowed E F become Q R, as the file says); 81 SDGN lumps, 5 SDGL."""

    @classmethod
    def setUpClass(cls):
        import gen_general
        cls.g = gen_general

    def test_frames_come_from_the_zs(self):
        g = self.g
        zs = g.GENERAL_ZS.read_text(encoding="utf-8")
        # The Summon swap the plan applies, installed by D73 (it was the
        # comment "final art: SDGN Q" / "R" on the borrowed CYBR E F lines).
        self.assertRegex(zs, r"\bSDGN Q 15 Bright A_SD_GeneralSummon;")
        self.assertRegex(zs, r"\bSDGN R 15;")
        self.assertEqual(g.full_frames(), ("ABCDEFGQR", "HIJKLMNOP"))
        self.assertNotIn("XDeath", g.zs_states())          # no gib
        plan = g.full_plan()
        self.assertEqual(len(plan), 81)
        names = [g.full_lump(f, r) for f, r in plan]
        self.assertEqual(len(set(names)), 81)
        self.assertTrue(all(len(x) <= 8 for x in names))
        rotated, death = g.full_frames()
        for f in rotated:                                  # handed: 8 drawn rotations, no mirrored pairs
            self.assertEqual(sorted(r for h, r in plan if h == f), list(range(1, 9)))
        for f in death:
            self.assertEqual([r for h, r in plan if h == f], [0])
        self.assertEqual(set(g.FULL_POSES), set(rotated))
        self.assertEqual(set(g.FALLS), set(death))
        self.assertEqual(g.zs_states()["Summon"], [("Q", 15), ("R", 15)])

    def test_shell_has_its_own_sprite(self):
        g = self.g
        zs = g.SHELL_ZS.read_text(encoding="utf-8")
        st = g.hound.zs_states(g.SHELL_ZS)
        self.assertEqual(len(st["Spawn"]), 2)              # A B in flight
        self.assertEqual(len(st["Death"]), 3)              # the burst: SDGL C D E
        self.assertIn("RenderStyle \"Add\"", zs)
        self.assertEqual(g.SHELL_FRAMES, "ABCDE")
        self.assertEqual(g.core.grab_offsets(g.SHELL_CV), (g.SHELL_CV.w // 2, g.SHELL_CV.h // 2))

    def test_sprite_names_are_free(self):
        """SDGN and SDGL are the General's in the docs and nobody else's; in
        assets/ a lump of that name can only be this set's own render."""
        g = self.g
        for name in (g.SPRITE, g.SHELL_SPRITE):
            self.assertTrue(re.fullmatch(r"SD[A-Z]{2}", name))
            reserved = set()
            for doc in ("docs/engine/BESTIARY.md", "docs/engine/MOD-SPEC.md"):
                for line in (PROJECT_ROOT / doc).read_text(encoding="utf-8").splitlines():
                    if "General" not in line and name not in line:
                        reserved |= set(re.findall(r"\bSD[A-Z]{2}\b", line))
            self.assertNotIn(name, reserved)
            if not (g.FULL_DIR / name).is_dir():
                continue    # a clean checkout has no gitignored work/: the identity half needs it
            for png in (PROJECT_ROOT / "assets").rglob(f"{name}*.png"):
                ours = g.FULL_DIR / name / png.name
                self.assertTrue(ours.is_file(), png)
                self.assertEqual(png.read_bytes(), ours.read_bytes(), png)

    def test_full_poses_keep_the_approved_ones(self):
        g = self.g
        self.assertIs(g.FULL_POSES["A"], g.POSES["A"])     # the turnaround's A and F, as approved
        self.assertIs(g.FULL_POSES["F"], g.POSES["F"])
        self.assertFalse(g.FULL_POSES["E"].fire)
        for f in "BCDEGQR":
            self.assertFalse(g.FULL_POSES[f].fire, f)
            self.assertFalse(g.FULL_POSES[f].no_cap, f)

    def test_blood_is_dark_red(self):
        g = self.g
        for name in ("blood", "pool"):
            m = g.GN_FULL_MATERIALS[name]
            self.assertEqual(m.ramps, {"flag_red"})
            self.assertTrue(m.flat)
            self.assertLessEqual(max(s[2] for s in m.spans if s[0] == "flag_red"), 5)
        for name in g.GN_BLOOD:
            self.assertFalse(g.GN_FULL_MATERIALS[name].ramps & g.FORBIDDEN_RAMPS)

    def test_the_dead_are_built_to_lie(self):
        g = self.g
        for f in "KLMNOP":                                 # down: the cloak spread, the coat collapsed
            pose = g.FALLS[f].pose
            self.assertTrue(pose.spread and pose.coat_flat and pose.no_cap and pose.no_sgun, f)
            self.assertEqual(g.FALLS[f].cap, "floor")
            self.assertEqual(g.FALLS[f].gun, "floor")
        self.assertEqual(g.FALLS["P"].settle, g.SETTLE_ALL)
        self.assertEqual(g.FALLS["P"].pool, 1.0)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class FullSetRenderTests(unittest.TestCase):
    """D72, rendered: the corpse lies flat; no living frame shows the cloak
    from the front; the lumps on disk are palette v2 with their grAb, and
    the approved turnaround's views are its pixels."""

    @classmethod
    def setUpClass(cls):
        import gen_general as g
        cls.g = g
        cls.corpse = g.corpse_metrics("P")

    def test_corpse_lies_flat(self):
        g, c = self.g, self.corpse
        for part, y in c["lowest"].items():
            self.assertLessEqual(abs(y), g.LYING_MAX, part)
        self.assertLess(c["top"], g.LYING_TOP)
        self.assertGreaterEqual(c["span"], g.LYING_SPAN)
        self.assertGreater(c["across"], 0.9)               # lying across the screen
        self.assertLess(c["loose_top"], 14.0)              # the cap and the gun lie, nothing stands up
        self.assertGreater(c["loose_lowest"], -0.5)

    def test_no_cloak_from_the_front(self):
        g = self.g
        for f in g.full_frames()[0]:
            prims = g.full_prims(f)
            lay = g.render_full_layers(f, 1, prims)
            self.assertEqual(g.cloak_pixels(lay, prims[0]), 0, f)

    def test_shell(self):
        g = self.g
        v2 = set(g.heavy.palette_v2())
        for f in g.SHELL_FRAMES:
            rgba = g.render_shell(f)
            a = rgba[..., 3] > 0
            self.assertTrue(a.any(), f)
            self.assertTrue({tuple(int(v) for v in p) for p in rgba[..., :3][a]} <= v2, f)
        np.testing.assert_array_equal(g.render_shell("A"), g.render_shell("A"))

    def test_lumps_on_disk(self):
        g = self.g
        d = g.FULL_DIR / g.SPRITE
        if not (d / "SDGNA1.png").is_file():
            self.skipTest("the full set is not rendered on this machine (work/ is gitignored)")
        v2 = set(g.heavy.palette_v2())
        for f, r in g.full_plan():
            path = d / f"{g.full_lump(f, r)}.png"
            rgba = np.asarray(Image.open(path).convert("RGBA"))
            self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255}, path)
            a = rgba[..., 3] > 0
            self.assertTrue({tuple(int(v) for v in p) for p in rgba[..., :3][a]} <= v2, path)
            self.assertEqual(g.core.read_grab(path), g.grab() if f in g.FULL_POSES else
                             g.core.grab_offsets(g.DEATH_CV), path)
        spr = g.load_full()
        ident = g.full_identity(spr)
        self.assertTrue(all(v is not False for v in ident.values()), ident)


if __name__ == "__main__":
    unittest.main()
