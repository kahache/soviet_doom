"""tools/art/gemini_frames.py: the pure steps on synthetic images.

Needs no Gemini reference (they are gitignored, work/art/reference/): every
image here is built in the test. Covers the magenta key (no magenta-ish pixel
survives, JPEG-like noise included), the letterbox crop, the art-pixel grid
detection, the mode downsample, palette-only output, the flash split and the
grAb placement.
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
        self.assertTrue((small[:, -1] >= 0).any())   # the smear reaches the new right edge

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


if __name__ == "__main__":
    unittest.main()
