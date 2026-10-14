"""tools/art/hand_study.py (D55): screen placement, patch decoding, hand proportions."""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parents[1] / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    import hand_study as hs
except ImportError:  # pragma: no cover - art tooling not installed
    hs = None


def tiny_patch(w: int, h: int, left: int, top: int) -> bytes:
    """A Doom picture: every column one opaque post of colour 1."""
    head = struct.pack("<hhhh", w, h, left, top)
    col = bytes([0, h, 0]) + bytes([1] * h) + bytes([0, 255])
    first = 8 + 4 * w
    offs = struct.pack(f"<{w}i", *[first + i * len(col) for i in range(w)])
    return head + offs + col * w


@unittest.skipIf(hs is None, "art tooling (numpy, Pillow) not installed")
class HandStudyTest(unittest.TestCase):
    def test_status_bar_lifts_the_weapon_16_px(self):
        spr = np.zeros((10, 10, 4), np.uint8)
        self.assertEqual(hs.place(spr, (-125, -97), bar=False), (125, 129))
        self.assertEqual(hs.place(spr, (-125, -97), bar=True), (125, 113))

    def test_decode_and_measure(self):
        pal = np.zeros((256, 3), np.uint8)
        img, off = hs.decode_patch(tiny_patch(4, 60, -100, -120), pal)
        self.assertEqual(off, (-100, -120))
        self.assertTrue((img[..., 3] == 255).all())
        m = hs.measure(img, off)
        self.assertEqual(m["top"], 32 + 120 - 16)
        self.assertEqual(m["height"], hs.VIEW_H - m["top"])
        self.assertEqual(m["area"], 4 * m["height"])

    def test_target_scale_lands_on_reference(self):
        t = hs.target_for({"height": 80, "area": 4000}, {"height": 40, "area": 1000})
        self.assertEqual(t["scale"], 0.5)
        self.assertEqual(t["band_px"], [36, 44])
        self.assertEqual(t["area_after"], 1000)

    def test_fingers_are_at_least_four_to_one(self):
        for g in ("index", "middle", "ring", "little"):
            self.assertGreaterEqual(hs.finger_ratio(g), hs.MIN_FINGER_RATIO, g)
        self.assertGreater(hs.PALM_BREADTH_MM, hs.PALM_MM)   # palm wider than long

    def test_four_variants_H1_to_H4(self):
        self.assertEqual(list(hs.VARIANTS), ["H1", "H2", "H3", "H4"])


if __name__ == "__main__":
    unittest.main()
