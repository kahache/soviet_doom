"""Behaviour tests for tools/art/gen_switch.py (batch 2, the eight switches).

What the generator promises (its docstring, docs/art/TEXTURE-INDEX.md
"batch 2, switches", ART-BIBLE §5-§7) and where it is checked here:

  seeds          BATCH_SEED 2077 + offset (A 1 .. D 4): seeds 2078-2081,
                 as the index records                       SeedAndLumaTests
  armature       a flat dark recess border that sits on concrete AND on
                 steel; a bevel lit top-left               PlateTests
  identity       variant D's hazard chevrons, painted in BOTH states
                                                           ChevronTests
  state          "only the switch moves, never the panel": both states
                 from one seed, differing only inside the moving parts
                 (and the glow the lit lamp spills)        VariantStateTests
  measurements   host lumas 147 / 101, "six or more is a lamp", B the
                 strongest far read and A the weakest      MeasureTests
  regression     the approved SDSW1x/SDSW2x in assets/ are reproduced
                 byte for byte outside the painted «ПУСК» (Impact
                 rasterises differently per machine, ART-BIBLE §7)
                                                           ApprovedSwitchTests
  main()         4 x 2 switches, 16 context and 16 far views, indexed,
                 the EN + RU sweep sheets and the manifest  MainRunTests

D27: nothing is written to work/ or assets/. Builders run in memory; the one
main() run has OUT_DIR, SHEET_DIR and MANIFEST redirected to a temp
directory, and the test checks that work/art/batch2/switch/ was not touched.

Run:  .venv/Scripts/python.exe -m unittest tests.test_cov_gen_switch -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    import artlib
    HAVE_ART = artlib.FONTS_PRESENT
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_ART = False

if HAVE_ART:
    import gen_switch as gen

art = unittest.skipUnless(HAVE_ART, "Pillow/numpy or the system fonts (Impact) not available")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the full generator run")

ASSET_DIR = PROJECT_ROOT / "assets" / "textures" / "soviet_base"

# Seeds as docs/art/TEXTURE-INDEX.md records them (written out, not imported).
INDEX_SEEDS = {"A": 2078, "B": 2079, "C": 2080, "D": 2081}

# Engine role names on install (TEXTURE-INDEX: "1 = off, 2 = on, variant
# letter last").
def asset_for(vid: str, on: bool) -> Path:
    return ASSET_DIR / f"SDSW{2 if on else 1}{vid}.png"


def build(vid: str, on: bool):
    return gen.VARIANTS[vid][0](on, gen.rng_for(vid))


def no_glow():
    return mock.patch.object(gen, "glow", lambda rgb, *a, **k: rgb)


@art
class SeedAndLumaTests(unittest.TestCase):
    def test_seeds_are_the_ones_the_index_records(self):
        for vid, seed in INDEX_SEEDS.items():
            with self.subTest(variant=vid):
                self.assertEqual(gen.BATCH_SEED + gen.SEED_OFFSET[vid], seed)
                a = gen.rng_for(vid).integers(0, 1 << 30, 8)
                b = np.random.default_rng(seed).integers(0, 1 << 30, 8)
                self.assertTrue(np.array_equal(a, b))

    def test_no_seed_collides_with_batch_1(self):
        """Own seed space, far from gen_soviet_base's 1977 + 1..12."""
        seeds = {gen.BATCH_SEED + o for o in gen.SEED_OFFSET.values()}
        self.assertFalse(seeds & set(range(1977 + 1, 1977 + 13)))

    def test_luma_is_rec601(self):
        px = np.array([[[255, 255, 255], [0, 0, 0], [255, 0, 0], [0, 255, 0], [0, 0, 255]]], np.uint8)
        np.testing.assert_allclose(gen.luma(px)[0], [255.0, 0.0, 76.245, 149.685, 29.07])

    def test_the_four_variants_and_the_recommendation(self):
        self.assertEqual(gen.VARIANT_IDS, ("A", "B", "C", "D"))
        self.assertEqual(set(gen.VARIANTS), set(gen.VARIANT_IDS))
        self.assertEqual(gen.RECOMMENDED, "D")
        self.assertEqual((gen.W, gen.H), (64, 128))


@art
class PlateTests(unittest.TestCase):
    def setUp(self):
        self.rgb = gen.plate(gen.rng_for("A"))
        self.r = gen.RECESS

    def test_shape(self):
        self.assertEqual(self.rgb.shape, (gen.H, gen.W, 3))
        self.assertEqual(self.rgb.dtype, np.uint8)

    def test_the_border_is_one_flat_recess_colour(self):
        r = self.r
        border = np.ones((gen.H, gen.W), bool)
        border[r:-r, r:-r] = False
        colours = {tuple(c) for c in self.rgb[border]}
        self.assertEqual(colours, {artlib.ramp_colour("concrete_cold", gen.RECESS_TONE)})

    def test_the_panel_is_lit_from_the_top_left(self):
        r, b = self.r, gen.BEVEL
        L = gen.luma(self.rgb)
        top = L[r:r + b, r + b:-r - b].mean()
        bottom = L[-r - b:-r, r + b:-r - b].mean()
        left = L[r + b:-r - b, r:r + b].mean()
        right = L[r + b:-r - b, -r - b:-r].mean()
        self.assertGreater(top, bottom)
        self.assertGreater(left, right)

    def test_the_panel_is_a_dark_mass(self):
        """"panel: dark (steel_blue low, luma ~60)": below both host walls."""
        r, b = self.r, gen.BEVEL
        inner = gen.luma(self.rgb)[r + b:-r - b, r + b:-r - b].mean()
        self.assertTrue(45 < inner < 80, inner)


@art
class ChevronTests(unittest.TestCase):
    def test_band_is_two_colours_and_nothing_else_moves(self):
        base = np.full((gen.H, gen.W, 3), 77, np.uint8)
        out = gen.chevrons(base)
        r, cw = gen.RECESS, gen.CHEVRON_W
        band = np.zeros((gen.H, gen.W), bool)
        band[r:-r, r:r + cw] = band[r:-r, -r - cw:-r] = True
        band[r:r + cw, r:-r] = band[-r - cw:-r, r:-r] = True
        light = artlib.ramp_colour("hazard_yellow", gen.CHEVRON_LIGHT)
        dark = artlib.ramp_colour("concrete_cold", gen.CHEVRON_DARK)
        self.assertEqual({tuple(c) for c in out[band]}, {light, dark})
        self.assertTrue((out[~band] == 77).all(), "the chevrons spilled outside their band")
        share = np.all(out[band] == np.array(light), axis=1).mean()
        expected = (gen.CHEVRON_PITCH // 2) / gen.CHEVRON_PITCH
        self.assertAlmostEqual(share, expected, delta=0.05)

    def test_variant_d_wears_them_in_both_states(self):
        r, cw = gen.RECESS, gen.CHEVRON_W
        light = np.array(artlib.ramp_colour("hazard_yellow", gen.CHEVRON_LIGHT))
        with no_glow():
            for on in (False, True):
                rgb = build("D", on)
                with self.subTest(on=on):
                    # the left band, below the corner bolts
                    strip = rgb[30:100, r:r + cw]
                    self.assertGreater(np.all(strip == light, axis=2).mean(), 0.35)


@art
class GlowTests(unittest.TestCase):
    def setUp(self):
        self.base = np.full((gen.H, gen.W, 3), 60, np.uint8)

    def test_zero_gain_changes_nothing(self):
        self.assertTrue(np.array_equal(gen.glow(self.base, 32, 64, gain=0.0), self.base))

    def test_it_brightens_most_at_the_lamp_and_fades_with_distance(self):
        out = gen.luma(gen.glow(self.base, 32, 64)) - gen.luma(self.base)
        self.assertGreater(out[64, 32], 0)
        self.assertEqual(out.max(), out[64, 32])
        row = out[64, 32:]
        self.assertTrue((np.diff(row) <= 1e-9).all(), "the glow does not fade with distance")
        self.assertAlmostEqual(out[0, 0], 0.0, delta=1.0)


@art
class ContextAndFarTests(unittest.TestCase):
    def test_context_is_host_switch_host(self):
        sw = np.full((gen.H, gen.W, 3), 9, np.uint8)
        for host in gen.HOSTS:
            with self.subTest(host=host):
                ctx = gen.context(sw, host)
                self.assertEqual(ctx.shape, (gen.H, gen.W * gen.CONTEXT_TILES, 3))
                self.assertTrue(np.array_equal(ctx[:, gen.W:2 * gen.W], sw))
                wall = gen.host_rgb(host)
                self.assertTrue(np.array_equal(ctx[:, :gen.W], wall[:gen.H]))
                self.assertTrue(np.array_equal(ctx[:, 2 * gen.W:], wall[:gen.H]))

    def test_far_view_is_a_point_sample_to_16_px_tall(self):
        """Not a smooth thumbnail: every far pixel is one source pixel, the
        centre of its 8x8 block, so no colour is invented."""
        rgb = np.random.default_rng(3).integers(0, 256, (gen.H, gen.W * 3, 3), dtype=np.uint8)
        f = gen.far(rgb)
        d = gen.FAR_DIVISOR
        self.assertEqual(d, 8)
        self.assertEqual(f.shape, (gen.H // d, gen.W * 3 // d, 3))
        self.assertEqual(f.shape[0], 16)
        self.assertTrue(np.array_equal(f, rgb[d // 2::d, d // 2::d]))


# The parts each variant moves between states (x0, y0, x1, y1), from the
# generator's own layout constants; the 1-px fringe is the antialiasing.
def moving_boxes(vid: str) -> list[tuple[float, float, float, float]]:
    if vid == "A":
        return [gen.VAR_A_BOARD,
                (gen.VAR_A_LAMP[0] - gen.VAR_A_LAMP[2] - gen.BEZEL_W, gen.VAR_A_LAMP[1] - gen.VAR_A_LAMP[2] - gen.BEZEL_W,
                 gen.VAR_A_LAMP[0] + gen.VAR_A_LAMP[2] + gen.BEZEL_W, gen.VAR_A_LAMP[1] + gen.VAR_A_LAMP[2] + gen.BEZEL_W)]
    if vid == "B":
        (cx, cy), r = gen.VAR_B_CENTER, gen.VAR_B_R
        return [(cx - r, cy - r, cx + r, cy + r)]
    if vid == "C":
        cx, cy, r = gen.VAR_C_LENS
        return [gen.VAR_C_SLOT, (cx - r, cy - r, cx + r, cy + r)]
    x0, y0, x1, y1 = gen.VAR_D_LENS
    return [gen.VAR_D_SLOT, (x0, y0, x1, y1)]


@art
class VariantStateTests(unittest.TestCase):
    def test_every_state_is_one_wall_segment(self):
        for vid in gen.VARIANT_IDS:
            for on in (False, True):
                with self.subTest(variant=vid, on=on):
                    rgb = build(vid, on)
                    self.assertEqual(rgb.shape, (gen.H, gen.W, 3))
                    self.assertEqual(rgb.dtype, np.uint8)

    def test_builds_are_deterministic(self):
        for vid in gen.VARIANT_IDS:
            with self.subTest(variant=vid):
                self.assertTrue(np.array_equal(build(vid, True), build(vid, True)))

    def test_on_is_brighter_than_off(self):
        for vid in gen.VARIANT_IDS:
            with self.subTest(variant=vid):
                self.assertGreater(gen.luma(build(vid, True)).mean(), gen.luma(build(vid, False)).mean())

    def test_only_the_switch_moves_never_the_panel(self):
        """With the lamp's glow taken out, every pixel that differs between
        the two states lies inside the parts that move."""
        fringe = 1
        with no_glow():
            for vid in gen.VARIANT_IDS:
                with self.subTest(variant=vid):
                    diff = np.any(build(vid, False) != build(vid, True), axis=2)
                    self.assertTrue(diff.any(), "the two states are identical")
                    allowed = np.zeros_like(diff)
                    for x0, y0, x1, y1 in moving_boxes(vid):
                        allowed[max(0, int(y0) - fringe):int(np.ceil(y1)) + fringe + 1,
                                max(0, int(x0) - fringe):int(np.ceil(x1)) + fringe + 1] = True
                    ys, xs = np.nonzero(diff & ~allowed)
                    self.assertEqual(len(ys), 0, f"panel pixels changed at {list(zip(xs[:5], ys[:5]))}")

    def test_variant_a_layout_guard_refuses_overlaps(self):
        """The generator refuses to import if board, word and lamp touch."""
        gen._check_var_a_layout()  # the shipped layout passes
        with mock.patch.object(gen, "VAR_A_STENCIL_Y", gen.VAR_A_LAMP[1] - 4):
            with self.assertRaisesRegex(ValueError, "stencil ends at .* lamp starts at"):
                gen._check_var_a_layout()
        with mock.patch.object(gen, "VAR_A_LAMP", (32, gen.H - 4, 6)):
            with self.assertRaisesRegex(ValueError, "plate border"):
                gen._check_var_a_layout()


@art
class MeasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = {v: gen.measure(build(v, False), build(v, True)) for v in gen.VARIANT_IDS}

    def test_a_uniform_jump_is_measured_everywhere(self):
        off = np.full((gen.H, gen.W, 3), 50, np.uint8)
        on = np.full((gen.H, gen.W, 3), 150, np.uint8)
        m = gen.measure(off, on)
        self.assertEqual(m["state_delta_mean"], 100.0)
        self.assertEqual((m["state_far_mean"], m["state_far_max"]), (100.0, 100.0))
        self.assertEqual(m["far_px_total"], (gen.H // 8) * (gen.W // 8))
        self.assertEqual(m["lit_far_px"], m["far_px_total"])
        self.assertEqual(m["vs_SDCONC1"], round(abs(50 - m["host_luma_SDCONC1"]), 1))
        self.assertEqual(gen.measure(off, off)["lit_far_px"], 0)

    def test_host_lumas_are_the_documented_147_and_101(self):
        m = self.m["A"]
        self.assertAlmostEqual(m["host_luma_SDCONC1"], 147, delta=1.0)
        self.assertAlmostEqual(m["host_luma_SDSTEL1"], 101, delta=1.0)

    def test_every_variant_lights_a_lamp_not_a_glint(self):
        """"One or two pixels is a glint; six or more is a lamp." """
        for vid, m in self.m.items():
            with self.subTest(variant=vid):
                self.assertGreaterEqual(m["lit_far_px"], 6)

    def test_b_reads_strongest_from_far_and_a_weakest(self):
        """The sheet's recommendation text: B "the strongest far read", A
        "the weakest at distance"."""
        far = {v: m["state_far_mean"] for v, m in self.m.items()}
        self.assertEqual(max(far, key=far.get), "B")
        self.assertEqual(min(far, key=far.get), "A")

    def test_b_c_d_are_darker_than_both_walls_when_dead(self):
        """The dark-mass rule; A is the documented exception ("the board is
        light in both states")."""
        for vid in ("B", "C", "D"):
            m = self.m[vid]
            with self.subTest(variant=vid):
                self.assertLess(m["mean_luma_off"], m["host_luma_SDSTEL1"])
                self.assertLess(m["mean_luma_off"], m["host_luma_SDCONC1"])
        self.assertGreater(self.m["A"]["mean_luma_off"], self.m["A"]["host_luma_SDSTEL1"])


STENCIL_Y = {"A": "VAR_A_STENCIL_Y", "B": "VAR_B_STENCIL_Y", "C": "VAR_C_STENCIL_Y", "D": "VAR_D_STENCIL_Y"}


@art
class ApprovedSwitchTests(unittest.TestCase):
    """The eight approved switches in assets/ were rendered on the Mac. The
    generator must still reproduce them exactly everywhere except the
    painted word, the only part a different machine's Impact may move
    (ART-BIBLE §7). Built and quantised in memory: nothing is written."""

    def stencil_box(self, vid: str) -> np.ndarray:
        cy = getattr(gen, STENCIL_Y[vid])
        half = gen.STENCIL_SIZE // 2 + 1
        margin = gen.RECESS + 4                     # stencil()'s max_width margin
        box = np.zeros((gen.H, gen.W), bool)
        box[cy - half:cy + half + 1, margin:gen.W - margin] = True
        return box

    def test_generator_matches_the_approved_lumps_outside_the_word(self):
        for vid in gen.VARIANT_IDS:
            for on in (False, True):
                path = asset_for(vid, on)
                with self.subTest(lump=path.stem):
                    self.assertTrue(path.is_file(), path)
                    q = artlib.quantize(Image.fromarray(build(vid, on), "RGB"))
                    got = np.asarray(q.convert("RGB"))
                    with Image.open(path) as im:
                        self.assertEqual(im.size, (gen.W, gen.H))
                        self.assertEqual(im.mode, "P")
                        want = np.asarray(im.convert("RGB"))
                    diff = np.any(got != want, axis=2)
                    ys, xs = np.nonzero(diff & ~self.stencil_box(vid))
                    self.assertEqual(len(ys), 0,
                                     f"{diff.sum()} px differ, {len(ys)} outside the «ПУСК» box, "
                                     f"e.g. {list(zip(xs[:5].tolist(), ys[:5].tolist()))}")


@art
@slow
class MainRunTests(unittest.TestCase):
    """One full main() into a temp directory."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.out_dir = cls.tmp / "switch"
        real = gen.OUT_DIR
        cls.before = {p.name: p.stat().st_mtime_ns for p in real.iterdir()} if real.is_dir() else {}
        out = io.StringIO()
        with mock.patch.object(gen, "OUT_DIR", cls.out_dir), \
                mock.patch.object(gen, "SHEET_DIR", cls.tmp), \
                mock.patch.object(gen, "MANIFEST", cls.out_dir / "manifest.json"), \
                contextlib.redirect_stdout(out):
            gen.main()
        cls.printed = out.getvalue()
        cls.after = {p.name: p.stat().st_mtime_ns for p in real.iterdir()} if real.is_dir() else {}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_nothing_was_written_to_work(self):
        self.assertEqual(self.before, self.after)

    def test_every_view_is_written_indexed_at_its_size(self):
        cw = gen.W * gen.CONTEXT_TILES
        expected = {}
        for vid in gen.VARIANT_IDS:
            for state in ("off", "on"):
                expected[f"SDSWT_{vid}_{state}.png"] = (gen.W, gen.H)
                for host in gen.HOSTS:
                    expected[f"CTX_{vid}_{host}_{state}.png"] = (cw, gen.H)
                    expected[f"FAR_{vid}_{host}_{state}.png"] = (cw // 8, gen.H // 8)
        self.assertEqual(len(expected), 8 + 16 + 16)
        for name, size in expected.items():
            with self.subTest(file=name):
                with Image.open(self.out_dir / name) as im:
                    self.assertEqual(im.size, size)
                    self.assertEqual(im.mode, "P")

    def test_main_writes_what_the_builders_build(self):
        with Image.open(self.out_dir / "SDSWT_D_on.png") as im:
            written = np.asarray(im.convert("RGB"))
        q = np.asarray(artlib.quantize(Image.fromarray(build("D", True), "RGB")).convert("RGB"))
        self.assertTrue(np.array_equal(written, q))

    def test_manifest_records_the_sweep(self):
        m = json.loads((self.out_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual((m["batch"], m["phase"], m["item"]), (2, "F2", "switch"))
        self.assertEqual(m["script"], "tools/art/gen_switch.py")
        self.assertEqual(m["batch_seed"], 2077)
        self.assertEqual(m["seed_offset"], {"A": 1, "B": 2, "C": 3, "D": 4})
        self.assertEqual(m["size"], [64, 128])
        self.assertEqual(m["hosts"], ["SDCONC1", "SDSTEL1"])
        self.assertEqual(m["far_divisor"], 8)
        self.assertEqual(m["recommended"], "D")
        self.assertEqual(set(m["variants"]), {"A", "B", "C", "D"})
        for vid, v in m["variants"].items():
            with self.subTest(variant=vid):
                self.assertEqual(v["metrics"], gen.measure(build(vid, False), build(vid, True)))
                self.assertTrue(v["description_en"] and v["description_ru"])

    def test_both_sweep_sheets_are_written(self):
        en = list(self.tmp.glob("*_F2_batch2-switch-sweep.html"))
        ru = list((self.tmp / "ru").glob("*_F2_batch2-switch-sweep.html"))
        self.assertEqual((len(en), len(ru)), (1, 1))
        self.assertEqual(en[0].name, ru[0].name)
        for page, lang in ((en[0], "en"), (ru[0], "ru")):
            text = page.read_text(encoding="utf-8")
            with self.subTest(lang=lang):
                self.assertIn(f'<html lang="{lang}">', text)
                self.assertEqual(text.count('class="card rec"'), 1, "exactly one recommended card")
                self.assertIn(gen.LABELS[lang]["recommended"], text)
                for vid in gen.VARIANT_IDS:
                    self.assertIn(f"{vid} — SDSWT1 / SDSWT2", text)
                self.assertNotIn("http://", text)
        self.assertIn("sheet EN:", self.printed)
        for vid in gen.VARIANT_IDS:
            self.assertRegex(self.printed, rf"(?m)^{vid}  vs concrete")

    def test_flr1_before_after_follows_the_batch1_render(self):
        """BUG-ART-001's before/after section exists only when work/ holds
        the batch-1 SDFLR1 render (gitignored, absent on a clean clone)."""
        render = PROJECT_ROOT / "work" / "art" / "batch1" / "soviet_base" / "SDFLR1.png"
        tile = self.out_dir / "FLR1_tile2x2.png"
        en = next(self.tmp.glob("*_F2_batch2-switch-sweep.html")).read_text(encoding="utf-8")
        if render.is_file():
            with Image.open(tile) as im:
                self.assertEqual(im.size, (128, 128))
            self.assertIn(gen.LABELS["en"]["sec_bug"], en)
        else:
            self.assertFalse(tile.exists())
            self.assertNotIn(gen.LABELS["en"]["sec_bug"], en)


if __name__ == "__main__":
    unittest.main()
