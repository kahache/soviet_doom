"""Unit tests for the art foundation: tools/art/artlib.py and tools/art/palette.py.

`artlib` is the base of all three generators (gen_soviet_base, gen_lenin,
gen_shell), so a silent regression here reaches every pixel the player sees.
What is checked, and why each property matters:

  fbm / value_noise   tileable (the wrap edge is no stronger than the
                      texture's own interior features) and deterministic for
                      a seed - the whole "rebuild byte-for-byte from the
                      seed" promise of docs/art/TEXTURE-INDEX.md rests on it
  quantize            never invents a colour outside docs/art/palette.json
  ramp_colour         monotonic and clamped to [0,1]
  Overlay             composites alpha instead of replacing it, and
                      group()/end_group() paint the contour UNDER the fill
  tiling_seam_score   actually detects a deliberately non-tileable texture
  palette.py          the generated JSON is what the code produces, the ramp
                      index is consistent, and the 162 ratified colours are
                      frozen (ART-BIBLE "Palette")

Nothing here reads work/ (gitignored, absent in a clean clone and in CI):
every file this suite needs is written into a tempfile directory.

Run:  .venv/bin/python -m unittest tests.test_artlib -v
(The system python3 has no Pillow/numpy; those tests then skip, exactly as
tests/test_art.py does, and CI takes that path on purpose.)
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image, ImageFont  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

import palette as palette_mod  # noqa: E402  (stdlib only, always importable)

# The macOS system fonts artlib names. Absent on Linux: the few tests that
# rasterise text skip rather than fail, like the engine test in test_smoke.
HAVE_FONTS = all(Path(p).is_file() for p in
                 ("/System/Library/Fonts/Supplemental/Impact.ttf",
                  "/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf"))

# Palette v1, ratified by the CEO on 2026-10-12 and frozen by ART-BIBLE
# ("the 162 colours in use are frozen: later sets only *add* ramps in the
# reserved slots, never edit an existing colour"). The digest covers only
# those first 162 entries, so adding a tenth ramp does not break this test
# while re-tuning any ratified colour does.
PALETTE_V1_COUNT = 162
PALETTE_V1_SHA256 = "3c94bf22bf1a758af260bcc67006485c34d1e2123f6a8e434cf44651f7243515"
PALETTE_V1_RESERVED_SLOTS = 94


def _digest(colours) -> str:
    return hashlib.sha256(
        json.dumps([list(c) for c in colours], separators=(",", ":")).encode()
    ).hexdigest()


# ===========================================================================
# palette.py - what tests/test_art.py does NOT already cover
# (it covers: <=256 unique colours, ramps monotonic in the JSON, and
# build_palette()["colours"] == the JSON's colours. Everything below is the
# rest of the contract: the index, the ramp endpoints, the reserve, the
# freeze, and the serialisation path itself.)
# ===========================================================================
class PaletteStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pal = palette_mod.build_palette()
        cls.on_disk = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))

    def test_index_points_at_the_real_position_of_every_ramp(self):
        """index[name] = [first, last] must address the ramp's own colours
        inside the flat list: artlib.ramp() and the engine's palette share
        that numbering."""
        flat = self.pal["colours"]
        for ramp in self.pal["ramps"]:
            start, end = self.pal["index"][ramp["name"]]
            self.assertEqual(end - start + 1, len(ramp["colours"]), ramp["name"])
            self.assertEqual(flat[start:end + 1], ramp["colours"], ramp["name"])
        for extra in self.pal["extras"]:
            start, end = self.pal["index"][extra["name"]]
            self.assertEqual(start, end, extra["name"])
            self.assertEqual(flat[start], extra["rgb"], extra["name"])

    def test_ramp_endpoints_and_lengths_match_the_declaration(self):
        declared = {name: (dark, light, steps) for name, dark, light, steps, _ in palette_mod.RAMPS}
        self.assertEqual(len(self.pal["ramps"]), len(declared))
        for ramp in self.pal["ramps"]:
            dark, light, steps = declared[ramp["name"]]
            self.assertEqual(len(ramp["colours"]), steps, ramp["name"])
            self.assertEqual(tuple(ramp["colours"][0]), dark, ramp["name"])
            self.assertEqual(tuple(ramp["colours"][-1]), light, ramp["name"])

    def test_ramp_names_are_unique_and_every_ramp_has_a_rationale(self):
        names = [r["name"] for r in self.pal["ramps"]] + [e["name"] for e in self.pal["extras"]]
        self.assertEqual(len(names), len(set(names)))
        for ramp in self.pal["ramps"]:
            self.assertTrue(ramp["why"].strip(), ramp["name"])

    def test_every_ramp_channel_is_monotonic(self):
        """test_art checks monotonic *luminance*; a ramp can pass that while
        one channel wanders (a bevel then picks up a colour cast)."""
        for ramp in self.pal["ramps"]:
            for ch in range(3):
                values = [c[ch] for c in ramp["colours"]]
                self.assertEqual(values, sorted(values), f"{ramp['name']} channel {ch}")

    def test_lerp_gamma_hits_both_endpoints_exactly(self):
        for a, b in ((0, 255), (10, 212), (26, 228), (40, 248)):
            self.assertEqual(palette_mod._lerp_gamma(a, b, 0.0), a)
            self.assertEqual(palette_mod._lerp_gamma(a, b, 1.0), b)
            mids = [palette_mod._lerp_gamma(a, b, i / 32) for i in range(33)]
            self.assertEqual(mids, sorted(mids), (a, b))

    def test_reserved_slots_are_still_free(self):
        """ART-BIBLE: 162 colours in use, 94 of the 256 slots reserved for
        later sets (metro marble, mosaics, industrial rust) so that approved
        textures never have to be requantised."""
        self.assertEqual(self.pal["count"], PALETTE_V1_COUNT)
        self.assertEqual(self.pal["count"], len(self.pal["colours"]))
        free = palette_mod.MAX_COLOURS - self.pal["count"]
        self.assertEqual(free, PALETTE_V1_RESERVED_SLOTS)
        self.assertEqual(
            self.pal["count"],
            sum(steps for *_, steps, _ in palette_mod.RAMPS) + len(palette_mod.EXTRAS))

    def test_ratified_v1_colours_are_frozen(self):
        """Editing any of the 162 ratified colours silently requantises every
        approved texture. Adding a ramp appends and does not trip this."""
        self.assertGreaterEqual(len(self.pal["colours"]), PALETTE_V1_COUNT)
        self.assertEqual(_digest(self.pal["colours"][:PALETTE_V1_COUNT]), PALETTE_V1_SHA256)
        self.assertEqual(_digest(self.on_disk["colours"][:PALETTE_V1_COUNT]), PALETTE_V1_SHA256)

    def test_main_rewrites_the_committed_file_byte_for_byte(self):
        """test_art compares only the colour list; the whole file is the
        contract (ramp rationales, gamma, index, formatting), and this also
        exercises main()'s own serialisation path."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "palette.json"
            with mock.patch.object(palette_mod, "PALETTE_JSON", out), \
                    contextlib.redirect_stdout(io.StringIO()):
                palette_mod.main()
            self.assertEqual(out.read_bytes(), PALETTE_JSON.read_bytes())


# ===========================================================================
# artlib - noise
# ===========================================================================
@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class NoiseTests(unittest.TestCase):
    """The noise must tile: every wall and flat of batch 1 is built on it,
    and a seam in the noise is a seam on every tiled surface of MAP01.

    'Tileable' is measured the way a player sees it: the jump across the
    wrap edge (last row against first row, last column against first column)
    must be no larger than the largest jump the texture already has inside
    itself. A non-tileable field fails that by an order of magnitude - see
    SeamMetricTests.test_detects_a_non_tileable_texture.
    """

    @staticmethod
    def _wrap_vs_interior(field):
        a = np.asarray(field, dtype=np.float64)
        rows = np.abs(np.diff(a, axis=0)).mean(axis=1)
        cols = np.abs(np.diff(a, axis=1)).mean(axis=0)
        return (float(np.abs(a[0] - a[-1]).mean()), float(rows.max()), float(rows.mean()),
                float(np.abs(a[:, 0] - a[:, -1]).mean()), float(cols.max()), float(cols.mean()))

    def _assert_tileable(self, field, label):
        wr, rmax, rmean, wc, cmax, cmean = self._wrap_vs_interior(field)
        self.assertLessEqual(wr, rmax, f"{label}: horizontal seam stronger than any interior row")
        self.assertLessEqual(wc, cmax, f"{label}: vertical seam stronger than any interior column")
        # and not merely under the maximum: the seam must be an ordinary
        # step, within 2x the average one.
        self.assertLessEqual(wr, 2.0 * rmean, f"{label}: horizontal seam {wr:.4f} vs mean {rmean:.4f}")
        self.assertLessEqual(wc, 2.0 * cmean, f"{label}: vertical seam {wc:.4f} vs mean {cmean:.4f}")

    def test_value_noise_tiles_in_both_axes(self):
        from artlib import value_noise
        for w, h, cx, cy in ((64, 64, 4, 4), (64, 128, 8, 4), (128, 128, 3, 7), (64, 64, 1, 1)):
            f = value_noise(w, h, cx, cy, np.random.default_rng(11))
            self._assert_tileable(f, f"value_noise {w}x{h} cells {cx}x{cy}")

    def test_value_noise_stays_in_the_unit_interval(self):
        from artlib import value_noise
        f = value_noise(96, 96, 6, 6, np.random.default_rng(3))
        self.assertGreaterEqual(f.min(), 0.0)
        self.assertLessEqual(f.max(), 1.0)

    def test_fbm_tiles_at_the_sizes_and_shapes_batch_1_uses(self):
        from artlib import fbm
        cases = [
            (64, 128, 4, 5, 0.55, 1.0),    # concrete()
            (64, 128, 8, 2, 0.5, 8.0),     # the vertical drip streaks
            (128, 128, 5, 3, 0.5, 1.0),    # plaque grime
            (64, 64, 2, 4, 0.5, 1.0),      # damp stain on the ceiling
            (64, 64, 12, 2, 0.5, 1.0),     # fine chip noise on steel
        ]
        for w, h, cells, octaves, persistence, aspect in cases:
            f = fbm(w, h, cells, octaves, np.random.default_rng(1977),
                    persistence=persistence, aspect=aspect)
            self._assert_tileable(f, f"fbm {w}x{h} cells={cells} oct={octaves} aspect={aspect}")

    def test_fbm_is_bounded_to_the_unit_interval(self):
        from artlib import fbm
        f = fbm(64, 64, 4, 5, np.random.default_rng(2))
        self.assertGreaterEqual(f.min(), 0.0)
        self.assertLessEqual(f.max(), 1.0)

    def test_fbm_is_deterministic_for_a_seed(self):
        from artlib import fbm
        a = fbm(64, 128, 4, 5, np.random.default_rng(1977))
        b = fbm(64, 128, 4, 5, np.random.default_rng(1977))
        self.assertTrue(np.array_equal(a, b))

    def test_fbm_differs_between_seeds(self):
        """Otherwise 'each texture derives its own seed' would be a lie and
        every wall of the set would carry the same blotches."""
        from artlib import fbm
        a = fbm(64, 64, 4, 4, np.random.default_rng(1978))
        b = fbm(64, 64, 4, 4, np.random.default_rng(1979))
        self.assertFalse(np.allclose(a, b))

    def test_grain_is_bounded_and_deterministic(self):
        from artlib import grain
        g = grain(64, 64, np.random.default_rng(5), 0.05)
        self.assertEqual(g.shape, (64, 64))
        self.assertLessEqual(np.abs(g).max(), 0.05)
        self.assertTrue(np.array_equal(g, grain(64, 64, np.random.default_rng(5), 0.05)))

    def test_smoothstep_endpoints_and_monotonicity(self):
        from artlib import smoothstep
        t = np.linspace(0, 1, 257)
        s = smoothstep(t)
        self.assertAlmostEqual(float(s[0]), 0.0)
        self.assertAlmostEqual(float(s[-1]), 1.0)
        self.assertTrue(np.all(np.diff(s) >= 0))


# ===========================================================================
# artlib - palette mapping
# ===========================================================================
@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class PaletteMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from artlib import load_palette
        cls.pal = {tuple(c) for c in load_palette()["colours"]}

    def _used(self, img):
        p = img.getpalette()
        return {tuple(p[i * 3:i * 3 + 3]) for i in set(img.get_flattened_data())}

    def test_quantize_never_returns_a_colour_outside_the_palette(self):
        """The hard guarantee: whatever is thrown at it - pure noise, a
        full-range gradient, saturated primaries, an image that is already
        indexed - what comes out is in docs/art/palette.json."""
        from artlib import quantize
        rng = np.random.default_rng(0)
        cases = {
            "uniform noise": rng.integers(0, 256, (48, 48, 3), dtype=np.uint8),
            "grey ramp": np.repeat(np.linspace(0, 255, 256, dtype=np.uint8)[None, :], 16, 0)[..., None].repeat(3, 2),
            "primaries": np.array([[(255, 0, 0), (0, 255, 0), (0, 0, 255),
                                    (255, 255, 0), (0, 255, 255), (255, 0, 255),
                                    (0, 0, 0), (255, 255, 255)]] * 8, dtype=np.uint8),
        }
        for label, arr in cases.items():
            img = quantize(Image.fromarray(arr, "RGB"))
            self.assertEqual(img.mode, "P", label)
            self.assertTrue(self._used(img) <= self.pal, f"{label}: {self._used(img) - self.pal}")

    def test_quantize_accepts_a_non_rgb_image(self):
        from artlib import quantize
        img = quantize(Image.new("RGBA", (8, 8), (200, 30, 30, 255)))
        self.assertEqual(img.mode, "P")
        self.assertTrue(self._used(img) <= self.pal)

    def test_quantize_keeps_palette_colours_essentially_unchanged(self):
        """A flat fill already chosen from the palette should survive the
        snap. Pillow's palette converter caches nearest-colour lookups at
        reduced precision, so a handful of entries land on a neighbour
        instead of themselves (QA bug ART-002, 4 of 162 under Pillow 12.3,
        worst case 5 per channel). Bounded here so a worse quantiser, or a
        palette with near-duplicate colours, is caught."""
        from artlib import quantize
        colours = sorted(self.pal)
        arr = np.array(colours, dtype=np.uint8).reshape(-1, 1, 3).repeat(4, axis=1)
        out = np.asarray(quantize(Image.fromarray(arr, "RGB")).convert("RGB"), dtype=int)
        src = arr.astype(int)
        exact = int((np.abs(out - src).sum(axis=2) == 0).sum() / arr.shape[1])
        self.assertGreaterEqual(exact, int(0.9 * len(colours)),
                                f"only {exact}/{len(colours)} palette colours survive quantise")
        self.assertLessEqual(int(np.abs(out - src).max()), 8,
                             "quantise moved a palette colour far from itself")

    def test_ramp_colour_is_monotonic_and_clamped(self):
        from artlib import ramp, ramp_colour
        for name in ("concrete_cold", "flag_red", "hazard_yellow", "steel_blue"):
            lum = [sum(ramp_colour(name, i / 64)) for i in range(65)]
            self.assertEqual(lum, sorted(lum), name)
            cols = ramp(name)
            self.assertEqual(ramp_colour(name, 0.0), cols[0], name)
            self.assertEqual(ramp_colour(name, 1.0), cols[-1], name)
            for below in (-0.001, -1.0, -1e9):
                self.assertEqual(ramp_colour(name, below), cols[0], name)
            for above in (1.001, 2.0, 1e9):
                self.assertEqual(ramp_colour(name, above), cols[-1], name)

    def test_ramp_colour_only_ever_returns_a_palette_colour(self):
        from artlib import load_palette, ramp_colour
        names = [r["name"] for r in load_palette()["ramps"]]
        for name in names:
            for i in range(0, 101):
                self.assertIn(ramp_colour(name, i / 100), self.pal, name)

    def test_unknown_ramp_name_raises(self):
        from artlib import ramp, ramp_colour
        with self.assertRaises(KeyError):
            ramp("soviet_mauve")
        with self.assertRaises(KeyError):
            ramp_colour("soviet_mauve", 0.5)

    def test_to_rgb_is_bounded_monotonic_and_clipped(self):
        from artlib import ramp, to_rgb
        field = np.linspace(-0.5, 1.5, 256).reshape(16, 16)
        out = to_rgb(field, "concrete_cold")
        self.assertEqual(out.shape, (16, 16, 3))
        self.assertEqual(out.dtype, np.uint8)
        cols = ramp("concrete_cold")
        self.assertEqual(tuple(out.reshape(-1, 3)[0]), cols[0])     # below 0 clipped
        self.assertEqual(tuple(out.reshape(-1, 3)[-1]), cols[-1])   # above 1 clipped
        lum = out.reshape(-1, 3).astype(int).sum(axis=1)
        self.assertTrue(np.all(np.diff(lum) >= 0))

    def test_shade_and_blend_clip_into_uint8(self):
        from artlib import blend, shade
        rgb = np.full((8, 8, 3), 200, dtype=np.uint8)
        self.assertEqual(shade(rgb, 10.0).max(), 255)
        self.assertEqual(shade(rgb, 0.0).max(), 0)
        field = np.linspace(0, 4, 64).reshape(8, 8)
        self.assertEqual(shade(rgb, field).dtype, np.uint8)
        self.assertTrue(np.array_equal(blend(rgb, (0, 0, 0), np.ones((8, 8))),
                                       np.zeros((8, 8, 3), dtype=np.uint8)))
        self.assertTrue(np.array_equal(blend(rgb, (0, 0, 0), np.zeros((8, 8))), rgb))
        # a mask outside [0,1] is clipped, not extrapolated
        self.assertTrue(np.array_equal(blend(rgb, (0, 0, 0), np.full((8, 8), 5.0)),
                                       np.zeros((8, 8, 3), dtype=np.uint8)))


# ===========================================================================
# artlib - vector overlays
# ===========================================================================
@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class OverlayTests(unittest.TestCase):
    """Overlay exists because Pillow's ImageDraw *replaces* RGBA pixels
    instead of blending them. Every primitive goes on its own layer and is
    alpha-composited; these tests are what proves that is still true."""

    def setUp(self):
        self.black = np.zeros((32, 32, 3), dtype=np.uint8)

    def test_half_transparent_fill_blends_with_the_ground(self):
        from artlib import Overlay
        ov = Overlay(32, 32)
        ov.rect(0, 0, 32, 32, fill=(255, 0, 0, 128))
        out = ov.composite(self.black)
        self.assertEqual(tuple(out[16, 16]), (128, 0, 0))

    def test_a_transparent_shape_does_not_punch_a_hole(self):
        """The bug the class was written to avoid: drawing a (0,0,0,0) fill
        straight onto the canvas would erase what is underneath."""
        from artlib import Overlay
        ov = Overlay(32, 32)
        ov.rect(0, 0, 32, 32, fill=(255, 255, 255, 255))
        ov.rect(8, 8, 24, 24, fill=(0, 0, 0, 0))
        out = ov.composite(self.black)
        self.assertEqual(tuple(out[16, 16]), (255, 255, 255))

    def test_stacked_primitives_blend_in_order(self):
        from artlib import Overlay
        ov = Overlay(32, 32)
        ov.rect(0, 0, 32, 32, fill=(255, 0, 0, 255))
        ov.rect(0, 0, 32, 32, fill=(0, 0, 255, 128))
        r, g, b = (int(v) for v in ov.composite(self.black)[16, 16])
        self.assertLess(abs(r - 127), 2)
        self.assertEqual(g, 0)
        self.assertLess(abs(b - 128), 2)

    def test_composite_leaves_untouched_pixels_alone(self):
        from artlib import Overlay
        base = np.full((32, 32, 3), 90, dtype=np.uint8)
        ov = Overlay(32, 32)
        ov.rect(10, 10, 14, 14, fill=(255, 255, 255, 255))
        out = ov.composite(base)
        self.assertEqual(tuple(out[0, 0]), (90, 90, 90))
        self.assertEqual(tuple(out[12, 12]), (255, 255, 255))

    def test_group_outline_is_painted_under_the_fill(self):
        """end_group() dilates the group's alpha and paints the contour
        first, then stamps the group on top: the fill must survive intact
        and the contour must only show outside it. This is what keeps the
        hammer readable against the sickle in SDSTAR1."""
        from artlib import Overlay
        ov = Overlay(32, 32)
        g = ov.group(outline=(255, 0, 0), outline_width=2.0)
        g.rect(10, 10, 22, 22, fill=(0, 255, 0, 255))
        ov.end_group(g)
        out = ov.composite(self.black)
        self.assertEqual(tuple(out[16, 16]), (0, 255, 0), "fill overwritten by its own outline")
        self.assertEqual(tuple(out[16, 11]), (0, 255, 0), "fill eaten from the inside")
        for x in (8, 9):
            self.assertEqual(tuple(out[16, x]), (255, 0, 0), f"no contour at x={x}")
        self.assertEqual(tuple(out[16, 4]), (0, 0, 0), "contour wider than asked")

    def test_group_without_outline_draws_only_the_fill(self):
        from artlib import Overlay
        ov = Overlay(32, 32)
        g = ov.group()
        g.rect(10, 10, 22, 22, fill=(0, 255, 0, 255))
        ov.end_group(g)
        out = ov.composite(self.black)
        self.assertEqual(tuple(out[16, 16]), (0, 255, 0))
        self.assertEqual(tuple(out[16, 8]), (0, 0, 0))

    def test_group_outline_width_scales_with_the_argument(self):
        from artlib import Overlay

        def reach(width):
            ov = Overlay(32, 32)
            g = ov.group(outline=(255, 0, 0), outline_width=width)
            g.rect(12, 12, 20, 20, fill=(0, 255, 0, 255))
            ov.end_group(g)
            out = ov.composite(np.zeros((32, 32, 3), dtype=np.uint8))
            row = out[16, :12, 0]
            return int(12 - np.nonzero(row)[0].min())

        self.assertLess(reach(1.0), reach(3.0))

    def test_star_points_is_a_regular_five_pointed_star(self):
        from artlib import star_points
        pts = star_points(10, 10, 5)
        self.assertEqual(len(pts), 10)
        radii = [float(np.hypot(x - 10, y - 10)) for x, y in pts]
        for outer in radii[0::2]:
            self.assertAlmostEqual(outer, 5.0, places=6)
        for inner in radii[1::2]:
            self.assertAlmostEqual(inner, 5 * 0.382, places=6)
        self.assertAlmostEqual(pts[0][0], 10.0, places=6)   # first point straight up
        self.assertLess(pts[0][1], 10.0)

    @unittest.skipUnless(HAVE_FONTS, "macOS system fonts not present")
    def test_text_shrinks_until_it_fits_max_width(self):
        from artlib import Overlay
        ov = Overlay(64, 32)
        asked = 24
        used = ov.text(32, 16, "СЛАВА СОВЕТСКОЙ", asked, (255, 255, 255, 255), max_width=40)
        self.assertLess(used, asked)
        self.assertGreater(used, 0)
        drawn = np.asarray(ov.img)[..., 3] > 0
        xs = np.nonzero(drawn.any(axis=0))[0] / ov.s
        self.assertLessEqual(float(xs.max() - xs.min()), 42.0)

    @unittest.skipUnless(HAVE_FONTS, "macOS system fonts not present")
    def test_text_without_max_width_keeps_the_size_asked(self):
        from artlib import Overlay
        ov = Overlay(64, 32)
        self.assertEqual(ov.text(32, 16, "7", 20, (255, 255, 255, 255)), 20)


# ===========================================================================
# artlib - the seam metric itself
# ===========================================================================
@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class SeamMetricTests(unittest.TestCase):
    """tiling_seam_score is the number the preview sheet shows the CEO. It is
    only worth showing if it reacts to a real seam, so it is checked against
    textures whose tileability is known by construction."""

    def test_flat_colour_has_no_seam(self):
        from artlib import tiling_seam_score
        self.assertEqual(tiling_seam_score(np.full((64, 64, 3), 120, dtype=np.uint8)), 0.0)

    def test_a_periodic_pattern_scores_at_most_one(self):
        from artlib import tiling_seam_score
        xs = np.arange(64)
        wave = ((np.sin(2 * np.pi * xs / 64) * 0.5 + 0.5) * 255).astype(np.uint8)
        img = np.repeat(wave[None, :], 64, 0)[..., None].repeat(3, 2)
        self.assertLessEqual(tiling_seam_score(img), 1.0)

    def test_detects_a_non_tileable_texture(self):
        """A full-range linear gradient is the canonical broken tile: inside
        it every step is 4 levels, across the wrap it is 255."""
        from artlib import tiling_seam_score
        ramp_x = np.linspace(0, 255, 64).astype(np.uint8)
        img = np.repeat(ramp_x[None, :], 64, 0)[..., None].repeat(3, 2)
        self.assertGreater(tiling_seam_score(img), 10.0)
        self.assertGreater(tiling_seam_score(img.transpose(1, 0, 2)), 10.0)

    def test_detects_tileable_noise_that_was_cropped(self):
        """The realistic way a texture stops tiling: noise generated at one
        size and cut down to another. The wrap edge then shows a jump the
        interior never has."""
        from artlib import fbm, tiling_seam_score, to_rgb
        native = to_rgb(fbm(64, 64, 4, 5, np.random.default_rng(5)), "concrete_cold")
        cropped = to_rgb(fbm(128, 128, 4, 5, np.random.default_rng(5))[:64, :64], "concrete_cold")
        self.assertLessEqual(tiling_seam_score(native), 1.0)
        self.assertGreater(tiling_seam_score(cropped), 3.0)
        self.assertGreater(tiling_seam_score(cropped), 5 * tiling_seam_score(native))


# ===========================================================================
# artlib - saving
# ===========================================================================
@unittest.skipUnless(HAVE_IMAGING, "Pillow/numpy not available in this interpreter")
class SaveIndexedTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _field(self, w=64, h=64):
        from artlib import fbm, to_rgb
        return to_rgb(fbm(w, h, 4, 4, np.random.default_rng(1977)), "concrete_cold")

    def test_writes_an_indexed_png_inside_the_palette(self):
        from artlib import load_palette, save_indexed
        pal = {tuple(c) for c in load_palette()["colours"]}
        out = self.tmp / "deep" / "SDTEST1.png"
        img = save_indexed(self._field(), out)
        self.assertTrue(out.is_file())
        self.assertEqual(img.mode, "P")
        with Image.open(out) as reread:
            self.assertEqual(reread.mode, "P")
            self.assertEqual(reread.size, (64, 64))
            p = reread.getpalette()
            used = {tuple(p[i * 3:i * 3 + 3]) for i in set(reread.get_flattened_data())}
            self.assertTrue(used <= pal, used - pal)

    def test_the_written_bytes_are_reproducible(self):
        from artlib import save_indexed
        a, b = self.tmp / "a.png", self.tmp / "b.png"
        save_indexed(self._field(), a)
        save_indexed(self._field(), b)
        self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_rejects_dimensions_off_the_doom_grid(self):
        """ART-BIBLE §2: every lump is a multiple of 8. Caught at save time,
        not by GZDoom at load time."""
        from artlib import save_indexed
        bad = np.zeros((60, 64, 3), dtype=np.uint8)
        with self.assertRaises(AssertionError):
            save_indexed(bad, self.tmp / "bad.png")
        self.assertFalse((self.tmp / "bad.png").exists())


if __name__ == "__main__":
    unittest.main()
