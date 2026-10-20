"""tools/art/gemini_frames.py: the pure steps on synthetic images.

Needs no Gemini reference (they are gitignored, work/art/reference/): every
image here is built in the test. Covers the magenta key (no magenta-ish pixel
survives, JPEG-like noise included), the letterbox crop, the art-pixel grid
detection, the mode downsample, palette-only output, the flash split and the
grAb placement; the D79 helpers for the five remaining weapons (flash
halo, shrink and taper, bottom fill, stray-piece drop, banded sleeve) and
the WEAPONS table against the draft overlay's reserved names and the
states. Only GeneratedFramesTests reads work/ (skips without it), and
FreshBuildTests the Gemini sources (gitignored; skips without them, slow).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    import gemini_frames as gf
except ImportError:  # pragma: no cover - the art venv is missing
    gf = None

MAGENTA = (250, 1, 250)


def blocky(cells_w: int, cells_h: int, cell: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """A random-colour block image (cells of `cell` px) on magenta with a
    one-cell magenta border, plus its cell-level colours."""
    art = rng.integers(20, 200, (cells_h, cells_w, 3)).astype(np.uint8)
    art[..., 1] = np.maximum(art[..., 1], art[..., [0, 2]].min(axis=-1))   # nothing magenta-ish in the art
    big = np.repeat(np.repeat(art, cell, axis=0), cell, axis=1)
    out = np.empty((big.shape[0] + 2 * cell, big.shape[1] + 2 * cell, 3), np.uint8)
    out[:] = MAGENTA
    out[cell:-cell, cell:-cell] = big
    return out, art


@unittest.skipIf(gf is None, "numpy/Pillow not installed (art venv)")
class TestGeminiFrames(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(7)
        self.pal = gf.palette_rgb()

    def noisy(self, img: np.ndarray, amp: int = 12) -> np.ndarray:
        n = self.rng.integers(-amp, amp + 1, img.shape)
        return np.clip(img.astype(np.int32) + n, 0, 255).astype(np.uint8)

    def test_letterbox_cropped(self):
        img = np.full((40, 80, 3), 128, np.uint8)
        img[:, :10] = 3
        img[:, -12:] = 5
        out = gf.crop_letterbox(img)
        self.assertEqual(out.shape[1], 80 - 10 - 12 - 2 * 3)   # bars plus the ringing margin
        self.assertGreater(out.min(), 100)

    def test_magenta_key_leaves_no_magenta(self):
        img, _ = blocky(12, 9, 5, self.rng)
        # a blended rim: half magenta, half art, around the art
        img[4, 5:-5] = (img[5, 5:-5].astype(int) + MAGENTA) // 2
        img = self.noisy(img)
        alpha = gf.key_magenta(img)
        self.assertFalse(alpha[0].any())                       # the flat background is keyed
        self.assertTrue(alpha[10:-10, 10:-10].all())           # the art inside stays
        self.assertFalse((gf.magentaness(img)[alpha] > gf.PINK_PALETTE).any())   # no pink rim kept
        idx = gf.snap_palette(img, alpha, self.pal)
        kept = self.pal[idx[idx >= 0]]
        self.assertFalse((gf.magentaness(kept) > gf.PINK_PALETTE).any())

    def test_grid_detected(self):
        for cell in (4, 5):
            img, _ = blocky(30, 20, cell, self.rng)
            img = self.noisy(img, 6)
            alpha = gf.key_magenta(img)
            period, _, _ = gf.detect_grid(img, alpha)
            self.assertAlmostEqual(period, cell, delta=0.15, msg=f"cell {cell}")

    def test_downsample_recovers_cells_in_palette(self):
        cell = 5
        img, art = blocky(16, 10, cell, self.rng)
        img = self.noisy(img, 6)
        alpha = gf.key_magenta(img)
        idx = gf.snap_palette(img, alpha, self.pal)
        period, phx, phy = gf.detect_grid(img, alpha)
        small = gf.grid_downsample(idx, period, phx, phy, self.pal)
        op = small >= 0
        self.assertTrue(abs(small.shape[1] - (16 + 2)) <= 1 and abs(small.shape[0] - (10 + 2)) <= 1, small.shape)
        self.assertEqual(int(op.sum()), 16 * 10)
        clean = gf.snap_palette(art, np.ones(art.shape[:2], bool), self.pal)
        self.assertGreater((small[op] == clean.ravel()).mean() if op.sum() == clean.size else 0, 0.9)

    def test_output_palette_only_and_grab(self):
        idx = np.full((20, 30), gf.TRANSPARENT, np.int32)
        idx[5:15, 8:30] = self.rng.integers(0, len(self.pal), (10, 22))
        small = gf.extend_edges(gf.mode_resize(idx, 15, 10, self.pal), 4, 3)
        sub, grab = gf.crop_with_grab(small, 200, 120)
        rgba = gf.to_rgba(sub, self.pal)
        colours = {tuple(c) for c in self.pal.tolist()}
        self.assertTrue(all(tuple(c) in colours for c in rgba[rgba[..., 3] > 0][:, :3].tolist()))
        self.assertTrue(set(np.unique(rgba[..., 3]).tolist()) <= {0, 255})
        rows = np.flatnonzero((small >= 0).any(axis=1))
        cols = np.flatnonzero((small >= 0).any(axis=0))
        # hand_study.place: top-left = (-gx, WEAPONTOP - gy - BAR_LIFT)
        self.assertEqual((-grab[0], gf.WEAPONTOP - grab[1] - gf.BAR_LIFT), (200 + cols[0], 120 + rows[0]))
        self.assertTrue((small[:, -5] >= 0).any())   # the arm runs on to the right
        self.assertFalse((small[:, -1] >= 0).any())  # and has curved down out before the last column

    def test_arm_runs_on_as_a_plain_sleeve_and_curves_out(self):
        """2026-10-20: the extension repeats no column of the art (mirroring
        the edge read as a hairy log); skin and sleeve run on as a tube in
        the sleeve's ramp (the bottom row's colour), as tall as their cut so
        it hides it, a dark seam (the cuff) where it takes over, outline on
        top, and it drops monotonically out of the canvas before its last
        column."""
        olive = self.near((92, 71, 25))
        idx = np.full((30, 40), gf.TRANSPARENT, np.int32)
        skin = self.near((230, 170, 140))
        idx[10:30, 20:40] = skin                                          # a forearm cut by the right side
        idx[26:30, 20:40] = olive                                         # the sleeve enters from below
        out = gf.extend_edges(idx, 48, 6, tile=8, pal=self.pal)
        self.assertEqual(out.shape, (36, 88))
        self.assertTrue((out[:30, :40] == idx).all())                    # the art itself untouched
        ext = out[:, 40:]
        tops = [int(np.flatnonzero(c >= 0)[0]) if (c >= 0).any() else out.shape[0] for c in ext.T]
        self.assertEqual(tops, sorted(tops))                     # it only ever goes down
        self.assertEqual(tops[-1], out.shape[0])                 # gone before the last column
        self.assertEqual(tops[0], 10)                            # as tall as the cut: it hides it
        ramp = gf.sleeve_ramp(idx, self.pal, 8)
        self.assertEqual(ramp[2], olive)                         # mid tone = the sleeve's colour
        self.assertEqual(set(ext[ext >= 0].tolist()), set(ramp))  # only the sleeve's shades
        self.assertTrue((ext[10:, 0] == ramp[0]).all())          # the seam
        lum = self.pal[ramp].astype(int).sum(axis=1)
        self.assertLess(lum[0], lum[3])                          # outline darkest,
        self.assertLess(lum[3], lum[2])                          # then shadow < mid < light
        self.assertLess(lum[2], lum[1])
        col = ext[:, 10]
        t = int(np.flatnonzero(col >= 0)[0])
        self.assertEqual(col[t], ramp[0])                        # outline on the tube's top edge
        self.assertEqual(col[t + 1], ramp[1])

    def near(self, rgb) -> int:
        return int(np.argmin(((self.pal.astype(int) - rgb) ** 2).sum(axis=1)))

    def test_materials_by_ramp(self):
        olive = self.pal[self.near((92, 71, 25))]
        for rgb, kind in (((0, 0, 0), gf.OUTLINE), ((120, 120, 128), gf.METAL), ((40, 50, 90), gf.METAL),
                          ((92, 71, 25), gf.SLEEVE), ((124, 74, 36), gf.WOOD), ((97, 22, 19), gf.WOOD),
                          ((181, 108, 53), gf.WOOD), ((230, 170, 140), gf.SKIN)):
            self.assertEqual(gf.material(self.pal[self.near(rgb)], olive), kind, rgb)

    def test_mixed_wood_and_sleeve_edge_extends_only_the_sleeve(self):
        """The CEO, 2026-10-20: "has mezclado la manga con la culata". A
        stock (wood) above a sleeve, both cut by the right side: the sleeve
        tube starts at the sleeve's rows, never covers or replaces the wood;
        the stock runs on as a straight bar in its own wood ramp, in front,
        with a dark outline between the two, and both leave the canvas."""
        olive, wood, grain = self.near((92, 71, 25)), self.near((124, 74, 36)), self.near((97, 22, 19))
        idx = np.full((40, 40), gf.TRANSPARENT, np.int32)
        idx[8:22, 20:40] = wood
        idx[12:22:4, 20:40] = grain                                       # its grain
        idx[22, 20:40] = self.near((0, 0, 0))                             # its outline
        idx[23:40, 20:40] = olive                                         # the sleeve, below
        out = gf.extend_edges(idx, 48, 6, tile=8, pal=self.pal)
        self.assertTrue((out[:40, :40] == idx).all())
        s_ramp = gf.sleeve_ramp(idx, self.pal, 8)
        w_ramp = gf.wood_ramp(self.pal[wood], self.pal)
        self.assertTrue(set(s_ramp[1:]).isdisjoint(w_ramp))               # two ramps, two materials
        ext = out[:, 41:]                                                 # past the cap / seam column
        sleeve_px = np.isin(ext, s_ramp[1:])
        wood_px = np.isin(ext, w_ramp[1:])
        self.assertTrue(wood_px.any() and sleeve_px.any())
        self.assertFalse(np.isin(out[8:23, 40], s_ramp[1:]).any())        # the cut stock is not sleeve
        self.assertTrue((out[25:40, 40] == s_ramp[0]).all())             # the sleeve's seam, under the stock
        for c in range(ext.shape[1]):
            col = ext[:, c]
            w_rows, s_rows = np.flatnonzero(np.isin(col, w_ramp)), np.flatnonzero(sleeve_px[:, c])
            if len(w_rows) and len(s_rows):
                self.assertLess(w_rows.max(), s_rows.min(), c)            # the sleeve below the stock
                self.assertIn(col[w_rows.max()], (w_ramp[0], s_ramp[0]))   # a dark outline between them
        tops = [int(np.flatnonzero(np.isin(c, w_ramp))[0]) for c in ext.T if np.isin(c, w_ramp).any()]
        self.assertEqual(tops, sorted(tops))                              # the stock: straight, down
        self.assertLessEqual(tops[0] - 8, 3)                              # from where it left the art
        self.assertFalse((out[:, -1] >= 0).any())                         # all gone by the last column

    def test_arm_exits_left_only_when_cut_there(self):
        idx = np.full((20, 30), gf.TRANSPARENT, np.int32)
        idx[5:20, 10:25] = 1
        out, left = gf.arm_exits(idx, 16, 4)
        self.assertEqual((left, out.shape), (0, (24, 46)))       # touches neither side:
        self.assertFalse((out[:, 30:] >= 0).any())               # the new columns stay empty
        idx[5:20, 0:10] = 2
        out, left = gf.arm_exits(idx, 16, 4)
        self.assertEqual((left, out.shape), (16, (24, 62)))
        self.assertFalse((out[:, 0] >= 0).any())

    def test_visible_cuts(self):
        sub = np.full((40, 30), 1, np.int32)
        # top-left at screen (300, 140): the right border at x=329, above the bar
        grab = (-300, gf.WEAPONTOP - gf.BAR_LIFT - 140)
        self.assertGreater(gf.visible_cuts(sub, grab), 0)
        far = (-(gf.SCREEN_W + gf.WIDE_MARGIN + gf.BOB_X), grab[1])   # past the widest view
        self.assertEqual(gf.visible_cuts(sub[:, :1], far), 0)
        low = (-300, gf.WEAPONTOP - gf.BAR_LIFT - 190)                # wholly under the bar
        self.assertEqual(gf.visible_cuts(sub, low), 0)
        self.assertGreater(gf.visible_cuts(sub, (-300, gf.WEAPONTOP - 150)), 0)   # bar off: 150..190 shows

    def test_kick_is_up_and_right_and_small(self):
        dx, dy = gf.KICK
        self.assertTrue(1 <= dx <= 2 and -4 <= dy <= -3, gf.KICK)

    def test_flash_split(self):
        gun = int(np.argmin(self.pal.sum(axis=1)))                        # darkest: the gun
        warm = int(np.argmax(gf.flash_coloured(self.pal[None])[0] * self.pal.sum(axis=1)))
        a = np.full((20, 40), gf.TRANSPARENT, np.int32)
        a[10:13, 10:38] = gun                                             # a barrel
        b = gf.shift(a, 2, 1)                                             # recoil
        b[8:16, 4:12] = warm                                              # flash over the muzzle
        clean, flash, recoil = gf.split_flash(a, b, self.pal)
        self.assertEqual(recoil, (2, 1))
        self.assertFalse((clean == warm).any())
        self.assertTrue((clean[11:14, 12:40] == gun).all())               # barrel end restored
        self.assertEqual(int((flash >= 0).sum()), 64)

    # ---------------------------------------------- D79, the five weapons
    def near(self, rgb) -> int:
        return int(((self.pal - np.array(rgb)) ** 2).sum(axis=1).argmin())

    def test_flash_halo_takes_the_loose_sparks(self):
        gun = int(np.argmin(self.pal.sum(axis=1)))
        warm = int(np.argmax(gf.flash_coloured(self.pal[None])[0] * self.pal.sum(axis=1)))
        a = np.full((30, 40), gf.TRANSPARENT, np.int32)
        a[20:23, 10:38] = gun
        b = a.copy()
        b[17:25, 4:12] = warm
        b[12, 2] = b[10, 6] = gun                                         # sparks off the flash
        clean, flash, _ = gf.split_flash(a, b, self.pal)
        self.assertEqual(int((clean[8:14] >= 0).sum()), 2)                # the PPSh's split: they stay
        clean, flash, _ = gf.split_flash(a, b, self.pal, halo=6)
        self.assertFalse((clean[8:14] >= 0).any())
        self.assertTrue(flash[12, 2] >= 0 and flash[10, 6] >= 0)

    def test_shrink_flash_keeps_its_root(self):
        gun = np.full((30, 40), gf.TRANSPARENT, np.int32)
        gun[14:17, 20:40] = 1
        flash = np.full_like(gun, gf.TRANSPARENT)
        flash[8:23, 2:20] = 5                                             # root: column 19, rows 14-16
        half = gf.shrink_flash(flash, gun, 0.5, self.pal)
        cols = np.flatnonzero((half >= 0).any(axis=0))
        self.assertIn(int(cols[-1]), (18, 19))                            # still at the muzzle (rounding)
        self.assertLess(int((half >= 0).sum()), int((flash >= 0).sum()) // 3)
        self.assertTrue((gf.shrink_flash(flash, gun, 1.0, self.pal) == flash).all())

    def test_taper_cut_points_a_flame_cut_by_the_side(self):
        f = np.full((20, 40), gf.TRANSPARENT, np.int32)
        f[5:15, 0:30] = 3                                                 # a jet cut by the left side
        t = gf.taper_cut(f, length=14, gap=2)
        self.assertFalse((t[:, :2] >= 0).any())                           # nothing touches the side
        heights = [int((t[:, c] >= 0).sum()) for c in range(2, 15)]
        self.assertEqual(heights, sorted(heights))                        # widening away from the cut
        self.assertTrue((t[:, 14:] == f[:, 14:]).all())
        inner = np.full_like(f, gf.TRANSPARENT)
        inner[5:15, 5:30] = 3                                             # not cut: untouched
        self.assertTrue((gf.taper_cut(inner) == inner).all())

    def test_fill_bottom_closes_a_strip_under_the_arms(self):
        idx = np.full((30, 10), gf.TRANSPARENT, np.int32)
        idx[10:25, 2:8] = 4
        idx[24, 2:8] = 0                                                  # its bottom outline
        out = gf.fill_bottom(idx)
        self.assertTrue((out[24:, 2:8] == 4).all())
        far = np.full_like(idx, gf.TRANSPARENT)
        far[2:10, 2:8] = 4                                                # a floating thing: left alone
        self.assertTrue((gf.fill_bottom(far) == far).all())

    def test_drop_piece_removes_only_that_piece(self):
        idx = np.full((10, 20), gf.TRANSPARENT, np.int32)
        idx[2:8, 1:5] = 1
        idx[2:8, 10:15] = 2
        out = gf.drop_piece(idx, 3, 4)
        self.assertFalse((out[:, :6] >= 0).any())
        self.assertTrue((out[2:8, 10:15] == 2).all())
        with self.assertRaises(ValueError):
            gf.drop_piece(idx, 0, 0)

    def test_banded_sleeve_keeps_the_arms_thickness(self):
        olive = self.near((110, 104, 50))
        idx = np.full((40, 30), gf.TRANSPARENT, np.int32)
        idx[10:18, 5:] = olive                                            # an arm out through the side, mid-height
        full = gf.extend_edges(idx, 48, 6, tile=8, pal=self.pal)
        band = gf.extend_edges(idx, 48, 6, tile=8, pal=self.pal, band=True)
        col = 30 + 5
        self.assertGreater(int((full[:, col] >= 0).sum()), 20)           # the wedge down to the bottom
        self.assertLessEqual(int((band[:, col] >= 0).sum()), 8)          # a tube of the arm's 8 rows
        self.assertFalse((band[:, -1] >= 0).any())

    def test_straight_sleeve_follows_the_forearm(self):
        # D84: curve=False runs the banded tube on along the arm's own axis,
        # as thick as it leaves, with no bend down, out through the side.
        olive = self.near((110, 104, 50))
        idx = np.full((60, 30), gf.TRANSPARENT, np.int32)
        for c in range(30):                                               # a forearm falling 1 row per 3 columns
            idx[10 + c // 3:18 + c // 3, c] = olive
        out = gf.extend_edges(idx, 48, 6, tile=8, pal=self.pal, band=True, curve=False)
        tops, thick = [], set()
        for k in range(2, 49):
            rows = np.flatnonzero(out[:, 29 + k] >= 0)
            tops.append(int(rows[0]))
            thick.add(len(rows))
            self.assertEqual(int(rows[-1] - rows[0] + 1), len(rows))     # one solid run
        self.assertEqual(thick, {8})                                      # never wider
        slope = np.polyfit(range(len(tops)), tops, 1)[0]
        self.assertAlmostEqual(slope, 1 / 3, delta=0.05)                  # the forearm's own direction
        self.assertLessEqual(max(abs(np.diff(tops, 2))), 1)               # straight: no bend
        self.assertTrue((out[:, -1] >= 0).any())                          # it leaves through the side
        self.assertEqual(out[tops[-1], -1], out[tops[0], 29 + 2])         # its dark outline on top

    def test_weapons_use_the_overlays_reserved_names_and_the_states_letters(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import make_draft_overlay as mdo
        for key, w in gf.WEAPONS.items():
            swaps = [s for s in mdo.SWAPS if s.item == key]
            if not swaps:                                                 # installed (the PPSh)
                continue
            letters = {}
            for s in swaps:
                text = (mdo.ZS_ROOT / s.zs).read_text(encoding="utf-8")
                letters[s.draft] = set(mdo.state_letters(text, s.placeholder))
            lumps = [f.lump for f in w.frame_list()]
            self.assertEqual(len(lumps), len(set(lumps)), key)
            for f in w.frame_list():
                self.assertIn(f.lump[:4], letters, f"{key}: {f.lump} is not a name the overlay reserves")
                self.assertEqual(f.lump[5:], "0", f.lump)
                self.assertEqual(f.lump[:4], w.flash if f.flash else w.gun, f.lump)
                self.assertIn(f.src, w.files(), f.lump)
            for name in (w.gun, w.flash):                                 # every state frame drawn, no more
                if name:
                    have = {f.lump[4] for f in w.frame_list() if f.lump[:4] == name}
                    self.assertEqual(have, letters[name], f"{key} {name}")
            for _, mock in w.mock_list():
                self.assertTrue(set(mock) <= set(lumps), key)


NEW_WEAPONS = ("izh", "rpg7", "roks3", "katyusha", "ice_axe")


def _sources_present(key: str) -> bool:
    return all((gf.REF_DIR / f).is_file() for f in gf.WEAPONS[key].files().values())


@unittest.skipIf(gf is None, "numpy/Pillow not installed (art venv)")
class GeneratedFramesTests(unittest.TestCase):
    """The drafts in work/art/weapons/hand_G/<weapon>/ (gitignored): each
    lump present, palette-only hard alpha, a grAb, the ready frame's top at
    the weapon's target above the bar. Skips without work/."""

    def test_built_drafts(self):
        import hand_study as hs
        lut = {tuple(c) for c in gf.palette_rgb().tolist()}
        seen = 0
        for key in NEW_WEAPONS:
            w = gf.WEAPONS[key]
            folder = gf.OUT_ROOT / w.name
            if not folder.is_dir():
                continue
            seen += 1
            for f in w.frame_list():
                path = folder / f"{f.lump}.png"
                with self.subTest(lump=f.lump):
                    self.assertTrue(path.is_file(), path)
                    rgba, grab = hs.read_png_sprite(path)
                    self.assertIsNotNone(grab)
                    self.assertTrue(set(np.unique(rgba[..., 3]).tolist()) <= {0, 255})
                    self.assertTrue({tuple(c) for c in rgba[rgba[..., 3] > 0][:, :3].tolist()} <= lut)
            ready, grab = hs.read_png_sprite(folder / f"{w.frame_list()[0].lump}.png")
            target = round(gf.chgg_height() * w.height_mult)
            self.assertLessEqual(abs(hs.measure(ready, grab)["height"] - target), 2, key)
        if not seen:
            self.skipTest("work/art/weapons/hand_G drafts not present (CI has no work/)")


@unittest.skipIf(gf is None, "numpy/Pillow not installed (art venv)")
class FreshBuildTests(unittest.TestCase):
    """A fresh build from the Gemini sources: no cut edge shows at 16:9 and
    any bob, with the bar on or off (visible_cuts on each lump's canvas).
    Slow (tests/_tiers.py) and local: the sources never leave work/."""

    def test_no_visible_cut_on_any_lump(self):
        import tempfile
        ran = 0
        for key in NEW_WEAPONS:
            if not _sources_present(key):
                continue
            ran += 1
            with tempfile.TemporaryDirectory() as tmp:
                res = gf.build(gf.WEAPONS[key], out_dir=Path(tmp))
            for lump, fr in res["frames"].items():
                self.assertEqual(fr["cuts"], 0, f"{key} {lump}")
        if not ran:
            self.skipTest("Gemini sources not present (work/art/reference/ is gitignored)")

    def test_ice_axe_swing_is_the_ready_frame_turned(self):
        # D86: B, C and D are A turned as one rigid piece: the hand keeps
        # its size (no deformed wrist) and the forearm still reaches the
        # canvas bottom, never the side.
        if not _sources_present("ice_axe"):
            self.skipTest("Gemini sources not present (work/art/reference/ is gitignored)")
        import tempfile
        pal = gf.palette_rgb()
        with tempfile.TemporaryDirectory() as tmp:
            res = gf.build(gf.WEAPONS["ice_axe"], out_dir=Path(tmp))
        a = res["frames"]["SDAXA0"]["rgba"]
        sleeve = a[-1][a[-1, :, 3] > 0][-gf.EDGE_TILE:, :3]
        sleeve_rgb = pal[gf.nearest_colour(np.median(sleeve, axis=0), pal)]

        def skin(rgba):
            cols = rgba[rgba[..., 3] > 0][:, :3]
            return sum(gf.material(c, sleeve_rgb) == gf.SKIN for c in cols)
        hand = skin(a)
        self.assertGreater(hand, 200)
        for lump in ("SDAXB0", "SDAXC0", "SDAXD0"):
            fr = res["frames"][lump]["rgba"]
            with self.subTest(lump=lump):
                self.assertLess(abs(skin(fr) - hand) / hand, 0.06)          # same hand, turned
                self.assertTrue((fr[-1, :, 3] > 0).any())                    # the forearm reaches the bottom
                self.assertEqual(res["frames"][lump]["cuts"], 0)


@unittest.skipIf(gf is None, "numpy/Pillow not installed (art venv)")
class SwingTests(unittest.TestCase):
    """rotsprite and swing on synthetic art (D86)."""

    def test_rotsprite_keeps_palette_and_area(self):
        idx = np.full((40, 40), gf.TRANSPARENT, np.int32)
        idx[10:30, 16:24] = 5
        idx[10:12, 16:24] = 9
        out = gf.rotsprite(idx, 30, (20, 20))
        self.assertTrue(set(np.unique(out).tolist()) <= {gf.TRANSPARENT, 5, 9})
        self.assertLess(abs(int((out >= 0).sum()) - 160) / 160, 0.1)
        self.assertTrue((gf.rotsprite(idx, 0, (20, 20)) == idx).all())

    def test_swing_runs_the_forearm_on_to_the_bottom(self):
        idx = np.full((40, 40), gf.TRANSPARENT, np.int32)
        idx[5:12, 8:14] = 7                                               # the hand
        for r in range(12, 40):                                           # a forearm leaving the bottom
            idx[r, 10 + (r - 12) // 2:16 + (r - 12) // 2] = 3
        a, b, slope = gf.bottom_pieces(idx)[0]
        self.assertAlmostEqual(slope, 0.5, delta=0.1)
        out = gf.swing(idx, 35, gf.forearm_pivot(idx, 20), 20, 60, lift=8)
        self.assertEqual(out.shape, (40, 80))
        self.assertTrue((out[-1] == 3).any())                             # still reaches the bottom
        self.assertLess(abs(int((out == 7).sum()) - 42) / 42, 0.15)       # the hand intact

if __name__ == "__main__":
    unittest.main()
