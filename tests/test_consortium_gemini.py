"""tools/art/consortium_gemini.py and gemini_enemy's CONSORTIUM spec (the
Consortium, SDCN, Episode 3's final boss; pending the CEO's OK).

Needs no Gemini sheet (gitignored, work/art/reference/enemies/gemini/, D77):
the repair steps run on small synthetic views drawn here. Covers the
materials (the Reich's grey-green, the Legion's pink, olive, chrome, glows,
flames, the armband), the far side's exchange of the halves (flesh by
luminance, the helmets in their rows, the armband become a chrome bracer),
the canonical mirror (about the box, or about a body axis with the arms
kept), the repairs (drop, recolour, hue, paste, the knot made whole, the
rocket dropped with the smoke kept, the graft registered), the scale with the
Breach's squash, the composed sheet, the spec (95 lumps, every rotation its
own picture, never a mirror), the install patch as the documented swap plus
the two state edits, and the real build in work/ when it exists (the Reich
armband on the viewer's right in the front view, none in rotations 6-8).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))
sys.path.insert(0, str(ROOT / "tests"))

try:
    import numpy as np
    from PIL import Image
    import consortium_gemini as cg
    import gemini_enemy as ge
except ImportError:  # pragma: no cover - the art venv is missing
    cg = None

REICH = (123, 141, 127)
REICH_DARK = (79, 95, 88)
LEGION = (169, 80, 107)
M1 = (108, 117, 84)
RACK = (66, 69, 56)
CHROME = (171, 189, 206)
RED = (185, 9, 9)
FIELD = (240, 240, 236)
GLOW = (90, 160, 250)
FLAME = (250, 160, 40)
CABLE = (31, 31, 31)
ACTOR = ROOT / "src" / "zscript" / "monsters" / "consortium.zs"


def canvas(h: int = 120, w: int = 160) -> "cg.View":
    return cg.View(np.zeros((h, w + 2 * cg.PAD, 3), np.uint8), np.zeros((h, w + 2 * cg.PAD), bool))


def fill(v, x0, y0, x1, y1, col):
    """A box in sheet pixels (the padded canvas' x + PAD)."""
    v.rgb[y0:y1, x0 + cg.PAD:x1 + cg.PAD] = col
    v.mask[y0:y1, x0 + cg.PAD:x1 + cg.PAD] = True


def body(reich_left_on_sheet: bool = True) -> "cg.View":
    """A crude two-halved front view as Gemini draws it: helmets, the two
    halves of a torso, an arm each side, a knot of cables under the belt."""
    v = canvas()
    a, b = (REICH, LEGION) if reich_left_on_sheet else (LEGION, REICH)
    fill(v, 50, 0, 70, 12, REICH_DARK if reich_left_on_sheet else M1)      # helmets
    fill(v, 72, 0, 92, 12, M1 if reich_left_on_sheet else REICH_DARK)
    fill(v, 50, 12, 70, 20, a)                                           # faces
    fill(v, 72, 12, 92, 20, b)
    fill(v, 45, 20, 70, 60, a)                                           # torso halves
    fill(v, 70, 20, 95, 60, b)
    fill(v, 30, 22, 45, 70, a)                                           # arms
    fill(v, 95, 22, 110, 70, b)
    fill(v, 30, 30, 45, 36, RED)                                         # the armband, on the Reich arm
    fill(v, 34, 31, 41, 35, FIELD)
    fill(v, 45, 60, 95, 110, CABLE)                                      # the knot
    return v


def x_of(v, colour) -> float:
    sel = v.mask & np.all(v.rgb == np.array(colour, np.uint8), axis=-1)
    return float(np.nonzero(sel)[1].mean()) - cg.PAD


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class MaterialTests(unittest.TestCase):
    def test_classes(self):
        px = np.array([[REICH, REICH_DARK, LEGION, M1, RACK, CHROME, RED, FIELD, GLOW, FLAME, CABLE]], np.uint8)
        m = cg.materials(px)
        expect = ("green", "green", "pink", "olive", "olive", "chrome", "red", "white", "glow", "fire", None)
        for i, cls in enumerate(expect):
            got = [k for k, a in m.items() if a[0, i]]
            self.assertEqual(got, [cls] if cls else [], (i, px[0, i]))

    def test_ramp_by_luminance_keeps_the_shading(self):
        rgb = np.array([[(60, 30, 40), (120, 60, 80), (200, 120, 150), (240, 180, 200)] * 10], np.uint8)
        r = cg.Ramp.of(rgb, np.ones(rgb.shape[:2], bool))
        lum = np.array([50.0, 150.0])
        out = r.at_lum(lum)
        np.testing.assert_allclose(cg.luminance(out), lum, atol=12)
        self.assertTrue(np.all(out[:, 0] > out[:, 1]))     # still pink

    def test_gradient_ends(self):
        g = cg.gradient(cg.FIRE_RAMP)
        lo, hi = g.at(np.array([0.0])), g.at(np.array([1.0]))
        self.assertLess(cg.luminance(lo)[0], cg.luminance(hi)[0])


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class SwapTests(unittest.TestCase):
    def setUp(self):
        cg._RAMPS.clear()
        ref = body()
        R = {"gflesh": (REICH,), "pink": (LEGION,), "stahl": (REICH_DARK,), "m1": (M1,), "rack": (RACK,),
             "chrome": (CHROME,)}
        for k, (c,) in R.items():   # a ramp of one colour in four shades
            px = np.array([[tuple(int(v * s) for v in c) for s in (0.6, 0.8, 1.0, 1.15)] * 8], np.uint8)
            cg._RAMPS[k] = cg.Ramp.of(px, np.ones(px.shape[:2], bool))
        cg._RAMPS.update({"fire": cg.gradient(cg.FIRE_RAMP), "blue": cg.gradient(cg.BLUE_RAMP),
                          "lamp": cg.gradient(cg.LAMP_RAMP), "dark": cg.gradient(cg.DARK_RAMP)})
        self.v = ref

    def tearDown(self):
        cg._RAMPS.clear()

    def test_the_halves_trade_materials(self):
        out = cg.swap_halves(self.v, cg.HELMET_ROWS // 3)
        m = cg.materials(out.rgb)
        torso_a = (slice(30, 50), slice(50 + cg.PAD, 65 + cg.PAD))   # was the Reich's flesh
        torso_b = (slice(30, 50), slice(75 + cg.PAD, 90 + cg.PAD))   # was the Legion's
        self.assertGreater(m["pink"][torso_a].mean(), 0.9)
        self.assertGreater(m["green"][torso_b].mean(), 0.9)
        helm_a = (slice(1, 10), slice(52 + cg.PAD, 68 + cg.PAD))
        self.assertGreater(m["olive"][helm_a].mean(), 0.9)          # the SS helmet's place: the M1's olive
        band = (slice(30, 36), slice(30 + cg.PAD, 45 + cg.PAD))
        self.assertEqual(int((m["red"] | m["white"])[band].sum()), 0)   # no armband on the Legion's side
        self.assertTrue(np.array_equal(out.mask, self.v.mask))

    def test_the_rack_becomes_chrome(self):
        fill(self.v, 30, 50, 45, 70, RACK)
        out = cg.swap_halves(self.v, 4)
        self.assertGreater(cg.materials(out.rgb)["chrome"][55:70, 30 + cg.PAD:45 + cg.PAD].mean(), 0.8)


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class CanonicalTests(unittest.TestCase):
    def test_mirror_puts_the_reich_on_the_viewers_right(self):
        v = body()
        self.assertLess(x_of(v, RED), x_of(v, CABLE))
        c = cg.canonical(v)
        self.assertGreater(x_of(c, RED), x_of(c, CABLE))
        self.assertEqual(c.box(), v.box())                   # about the box's centre: the box stays

    def test_kept_polygons_stay(self):
        v = body()
        fill(v, 100, 22, 110, 30, FLAME)                     # a flash at the Legion hand, right on the sheet
        key = ("synthetic", 0)
        cg.KEEP[key] = (70, (cg.rect(98, 20, 112, 32),))
        try:
            c = cg.canonical(v, key)
        finally:
            del cg.KEEP[key]
        self.assertGreater(x_of(c, FLAME), 98)               # the arm's flash did not move
        self.assertGreater(x_of(c, RED), 70)                 # the body did


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class RepairTests(unittest.TestCase):
    def test_drop_and_recolour(self):
        v = body()
        cg.op_drop(v, cg.rect(95, 22, 110, 70))
        self.assertFalse(v.mask[40, 100 + cg.PAD])
        cg._RAMPS.clear()
        try:
            px = np.array([[tuple(int(x * s) for x in RACK) for s in (0.6, 0.8, 1.0, 1.2)] * 8], np.uint8)
            cg._RAMPS["rack"] = cg.Ramp.of(px, np.ones(px.shape[:2], bool))
            px = np.array([[tuple(int(x * s) for x in CHROME) for s in (0.6, 0.8, 1.0, 1.1)] * 8], np.uint8)
            cg._RAMPS["chrome"] = cg.Ramp.of(px, np.ones(px.shape[:2], bool))
            fill(v, 30, 50, 45, 70, CHROME)
            cg.op_recolour(v, cg.rect(28, 48, 47, 72), "chrome", "chrome", "rack")
            self.assertGreater(cg.materials(v.rgb)["olive"][55:68, 32 + cg.PAD:43 + cg.PAD].mean(), 0.9)
        finally:
            cg._RAMPS.clear()

    def test_hue_turns_a_glow_into_fire(self):
        v = body()
        fill(v, 100, 40, 108, 48, GLOW)
        cg._RAMPS.clear()
        cg._RAMPS["fire"] = cg.gradient(cg.FIRE_RAMP)
        try:
            cg.op_hue(v, cg.rect(98, 38, 110, 50), "fire")
        finally:
            cg._RAMPS.clear()
        m = cg.materials(v.rgb)
        self.assertFalse(m["glow"][40:48, 100 + cg.PAD:108 + cg.PAD].any())
        self.assertTrue(np.all(v.rgb[44, 104 + cg.PAD, 0] > v.rgb[44, 104 + cg.PAD, 2]))

    def test_knot_fill_closes_a_hole_inside_the_hull_only(self):
        v = body()
        cg.op_drop(v, cg.rect(45, 70, 60, 100))              # an arm hung over the knot's left
        cg.op_knot_fill(v, 60, ((0, 8), (0, -8), (15, 0)))
        self.assertTrue(v.mask[85, 50 + cg.PAD])
        self.assertFalse(v.mask[85, 30 + cg.PAD])            # outside the knot stays background

    def test_drop_bright_keeps_the_smoke(self):
        v = body()
        fill(v, 50, 90, 56, 100, (215, 205, 190))            # a rocket's body over the knot
        fill(v, 50, 100, 56, 104, FLAME)
        cg.op_drop_bright(v, cg.rect(48, 88, 58, 106), 100)
        self.assertFalse(v.mask[95, 52 + cg.PAD] or v.mask[102, 52 + cg.PAD])
        self.assertTrue(v.mask[95, 47 + cg.PAD])

    def test_graft_registers_and_fills_holes_only(self):
        src = body()
        dst = canvas()
        dst.rgb[:, 3:] = src.rgb[:, :-3]                     # the same body three columns right
        dst.mask[:, 3:] = src.mask[:, :-3]
        cg.op_drop(dst, cg.rect(98, 22, 113, 70))
        dx, dy = cg.op_graft(dst, src, cg.rect(95, 22, 110, 70), (0, 0), (20, 60), True, 4)
        self.assertEqual((dx, dy), (3, 0))
        self.assertTrue(dst.mask[40, 100 + cg.PAD])

    def test_lower_takes_the_rows_under_the_cut(self):
        v = body()
        other = body()
        other.rgb[60:110, cg.PAD + 45:cg.PAD + 95] = (60, 60, 58)
        cg.op_lower(v, other, 60, (0, 0))
        self.assertTrue(np.all(v.rgb[80, 70 + cg.PAD] == (60, 60, 58)))
        self.assertTrue(np.all(v.rgb[40, 60 + cg.PAD] == REICH))


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class ScaleComposeTests(unittest.TestCase):
    def test_squash_compresses_only_under_the_belt(self):
        v = body()
        rgb, m = cg.scaled(v, 1.0, (60, 0.5))
        self.assertEqual(m.shape[0], 60 + 25)
        rgb2, m2 = cg.scaled(v, 2.0)
        self.assertEqual(m2.shape, (220, 160))

    def test_defringe_greys_magenta_in_the_knot_only(self):
        rgb = np.zeros((20, 4, 3), np.uint8)
        rgb[:] = (130, 40, 130)                              # Gemini's magenta between cables / a pink shadow
        out = cg.defringe(rgb, np.ones((20, 4), bool))
        self.assertTrue(np.all(out[:10] == rgb[:10]))        # above the belt: the flesh's shading kept
        self.assertTrue(np.all(out[15, :, 0] == out[15, :, 2]))   # under it: neutral grey

    def test_compose_parts_figures(self):
        pics = [cg.scaled(body(), 1.0) for _ in range(8)]
        img = cg.compose(pics)
        fg = ge.key_background(img, ge.estimate_background(img))
        self.assertEqual(len(ge.figures(fg, 8)), 8)


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class TableTests(unittest.TestCase):
    def test_repairs_name_real_views_and_ops(self):
        ops = {"drop", "recolour", "hue", "lower", "paste", "fill", "fill_shift", "knot_fill", "drop_bright",
               "graft", "gen"}
        for (key, view), seq in list(cg.REPAIRS.items()) + list(cg.REPAIRS_POST.items()):
            self.assertIn(key, cg.SOURCES)
            self.assertLess(view, cg.SOURCES[key][1])
            for op in seq:
                self.assertIn(op[0], ops, (key, view))
                if op[0] in ("lower", "graft", "paste"):
                    self.assertIn(op[1], cg.SOURCES)
        for (key, view) in cg.KEEP:
            self.assertIn(key, cg.SOURCES)
        for key, view in cg.REPAIR_NOTES:
            self.assertIn((key, view), cg.REPAIRS)
        for name, (key, view, crop, prompt) in cg.GEN.items():
            self.assertTrue(any(op[0] == "gen" and op[1] == name for op in cg.REPAIRS[(key, view)]))
        self.assertNotIn("assets", str(cg.GEN_DIR).replace("\\", "/").split("/work/")[-1])

    def test_letters_cover_the_doc(self):
        self.assertEqual(set(cg.LETTERS) | set(cg.DERIVED_LETTERS), set("QRABCEFGHS"))
        self.assertEqual(cg.FAR_FROM, (cg.BACK34, cg.PROFILE, cg.Q34))


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class SpecTests(unittest.TestCase):
    def test_names_and_no_mirror(self):
        spec = ge.PENDING["consortium"]
        names = ge.lump_names(spec)
        self.assertEqual(len(names), 95)                     # design doc section 5
        for n in names:
            self.assertRegex(n, r"^SDCN[A-S][0-8]$")
        src = ge.lump_sources(spec)
        self.assertFalse(any(s[2] for s in src.values()), "a mirrored rotation")
        for L in spec.rotated:
            for r in (6, 7, 8):
                self.assertEqual(src[f"SDCN{L}{r}"][1], r - 1)
        self.assertEqual((spec.symbol, spec.symbol_fields), ("warp", "white"))
        self.assertEqual(spec.target_height, ge.CONSORTIUM_HEIGHT)
        self.assertNotIn("consortium", ge.ENEMIES)

    def test_every_letter_the_actor_will_show(self):
        text = ACTOR.read_text(encoding="utf-8")
        done = cg.installed_actor(text) if "PROVISIONAL-D116" in text else text
        letters = set()
        for m in re.finditer(r"^\s*SDCN\s+([A-Z]+)\s", done, re.M):
            letters |= set(m.group(1))
        spec = ge.PENDING["consortium"]
        self.assertEqual(letters, set(spec.rotated) | set(spec.single))


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class InstallTests(unittest.TestCase):
    def test_installed_actor_is_the_documented_swap_plus_the_state_edits(self):
        text = ACTOR.read_text(encoding="utf-8")
        if "PROVISIONAL-D116" not in text:
            self.skipTest("already installed")
        import _p4_mod as p4
        swapped, pairs = p4.apply_documented_swap(text)
        self.assertEqual(pairs, [("SDPS", "SDCN")])
        done = cg.installed_actor(text)
        self.assertNotIn("PROVISIONAL", done)
        code = p4.strip_comments(done)
        self.assertNotIn("SDPS", code)
        self.assertNotIn("Translation", code)
        self.assertNotRegex(code, r"\bScale\b")
        self.assertIn("SDCN QR 10 A_Look;", done)
        self.assertRegex(done, r"SDCN Q 6 A_SD_ConsortiumChase;\s+SDCN R 6 A_SD_ConsortiumChase;")
        self.assertRegex(done, r"Breach:\s+SDCN S 10 A_SD_ConsortiumBreach;[^\n]*\n\s+SDCN S 10;")

        def lines(t):
            return [l.strip() for l in p4.strip_comments(t).splitlines() if l.strip()]
        diff = [(a, b) for a, b in zip(lines(swapped), lines(done)) if a != b]
        self.assertEqual(len(lines(swapped)), len(lines(done)))
        self.assertEqual(len(diff), 6)                       # Spawn, the 0-tic See, Q, R and the two S


@unittest.skipIf(cg is None, "art venv (numpy, Pillow) missing")
class BuiltSetTests(unittest.TestCase):
    """The real build in work/ (gitignored), if it exists."""
    FOLDER = ge.OUT_ROOT / "consortium" if cg is not None else None

    def setUp(self):
        if not (self.FOLDER / "SDCNQ1.png").is_file():
            self.skipTest("work/art/enemies_gemini/consortium/ not built")

    def _px(self, lump):
        with Image.open(self.FOLDER / f"{lump}.png") as im:
            return np.asarray(im.convert("RGBA")).astype(int)

    def test_the_set_and_its_height(self):
        names = sorted(p.stem for p in self.FOLDER.glob("SDCN*.png"))
        self.assertEqual(names, ge.lump_names(ge.PENDING["consortium"]))
        a = self._px("SDCNQ1")[..., 3] > 0
        ys = np.flatnonzero(a.any(axis=1))
        self.assertLessEqual(abs((ys[-1] - ys[0] + 1) - ge.CONSORTIUM_HEIGHT), 1)

    def test_the_reich_armband_is_on_the_viewers_right_in_front_and_absent_on_the_far_side(self):
        for L in "QBE":
            px = self._px(f"SDCN{L}1")
            red = (px[..., 3] > 0) & (px[..., 0] > 120) & (px[..., 1] < 50) & (px[..., 2] < 50)
            self.assertGreater(int(red.sum()), 3, L)
            left = ge.read_grab(self.FOLDER / f"SDCN{L}1.png")[0]
            self.assertGreater(float(np.nonzero(red)[1].mean()), left, L)
            for r in (6, 7):
                px = self._px(f"SDCN{L}{r}")
                red = (px[..., 3] > 0) & (px[..., 0] > 120) & (px[..., 1] < 50) & (px[..., 2] < 50)
                self.assertLess(int(red.sum()), 6, f"{L}{r}")


if __name__ == "__main__":
    unittest.main()
