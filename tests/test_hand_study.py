"""tools/art/hand_study.py (D55): screen placement, patch decoding, hand proportions."""

from __future__ import annotations

import os
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

    def test_round2_hand_body_about_the_longest_finger(self):
        # CEO, round 2: the hand body ~ the longest finger, wider than the wrist
        for cfg in hs.ROUND2.values():
            ratio = hs.HAND_BODY_MM * cfg["palm"] / hs.middle_finger_mm()
            self.assertGreater(ratio, 0.9)
            self.assertLess(ratio, 1.2)
        self.assertGreater(hs.PALM_BREADTH_MM, hs.WRIST_BREADTH_MM * 1.3)

    def test_round2_forearm_tapers_to_the_wrist(self):
        arm = hs.forearm_chain((0.0, 0.0), 19.0, 38.0, 10.0)
        radii = [r for _, _, r in arm]
        self.assertEqual(radii[0], 19.0)
        self.assertGreater(max(radii), 1.8 * radii[0])
        self.assertEqual(radii, sorted(radii))

    @unittest.skipUnless(hs is not None and hs.IWAD.is_file(), "Freedoom IWAD not in iwads/")
    def test_round3_freedoom_hands_lose_the_pistol_and_take_our_colours(self):
        lumps, pal = hs.read_wad()
        spr, _, masks = hs.freedoom_hands(lumps, pal)
        self.assertGreater(int(masks["gun"].sum()), 300)
        skin = {tuple(c) for c in hs.ramp_cols(hs.R3_SKIN)}
        coloured = {tuple(c) for c in spr[masks["skin"], :3]}
        self.assertTrue(coloured <= skin | {tuple(hs.ramp_cols(hs.R3_SKIN)[0])})
        fist, _ = hs.freedoom_fist(lumps, pal)
        self.assertEqual(fist.shape[1], hs.decode_patch(lumps[hs.R3_FIST], pal)[0].shape[1] + hs.R3_FIST_PAD)

    @unittest.skipUnless(hs is not None and hs.IWAD.is_file(), "Freedoom IWAD not in iwads/")
    def test_fist_sleeve_never_touches_skin(self):
        lumps, pal = hs.read_wad()
        fist, _ = hs.freedoom_fist(lumps, pal)
        green = {tuple(c) for c in hs.ramp_cols(hs.R3_SLEEVE)}
        skin = {tuple(c) for c in hs.ramp_cols(hs.R3_SKIN)[1:]}
        rgb = [[tuple(px) for px in row] for row in fist[..., :3]]
        for y in range(1, fist.shape[0]):
            for x in range(fist.shape[1]):
                if fist[y, x, 3] and rgb[y][x] in green and fist[y - 1, x, 3]:
                    self.assertNotIn(rgb[y - 1][x], skin - green, (x, y))

    @unittest.skipUnless(hs is not None and hs.IWAD.is_file(), "Freedoom IWAD not in iwads/")
    def test_tt33_on_freedoom_hands_at_pisg_height_and_centred(self):
        frames = hs.build_tt33_fd()
        a = frames["SDTTA0"]
        m = hs.measure(a["sprite"], a["offsets"])
        lumps, pal = hs.read_wad()
        pisg, off = hs.decode_patch(lumps["PISGA0"], pal)
        ref = hs.measure(pisg, off)
        self.assertLessEqual(abs(m["height"] - ref["height"]), 0.1 * ref["height"])
        centre = (m["bbox"][0] + m["bbox"][2]) / 2
        self.assertLess(abs(centre - hs.SCREEN_W / 2), 20)
        for name in ("SDTTA0", "SDTTB0", "SDTTC0", "SDTFA0"):
            _, grab = hs.read_png_sprite(hs.TT_OUT_DIR / f"{name}.png")
            self.assertEqual(tuple(grab), tuple(frames[name]["offsets"]))

    def test_four_variants_H1_to_H4(self):
        self.assertEqual(list(hs.VARIANTS), ["H1", "H2", "H3", "H4"])


slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"), "SD_SKIP_SLOW_ART is set: skipping a render")


@unittest.skipIf(hs is None, "art tooling (numpy, Pillow) not installed")
@unittest.skipUnless(hs is not None and hs.IWAD.is_file(), "Freedoom IWAD not in iwads/")
class FreedoomWeaponsTest(unittest.TestCase):
    """N4 (D63): the weapons after the TT-33, in Freedoom's hands, one by one."""

    def test_bare_fist_is_pungc0_alone(self):
        lumps, pal = hs.read_wad()
        bare, off, ring = hs.freedoom_fist_bare(lumps, pal)
        src, _ = hs.decode_patch(lumps[hs.R3_FIST], pal)
        self.assertTrue(((bare[..., 3] > 0)[:, hs.R3_FIST_PAD:] == (src[..., 3] > 0)).all())
        self.assertFalse((bare[:, :hs.R3_FIST_PAD, 3] > 0).any())
        self.assertEqual(off, hs.freedoom_fist(lumps, pal)[1])
        self.assertTrue(hs.R3_FIST_GRIP[0] <= ring[1] < hs.R3_FIST_GRIP[1])

    def test_axe_letters_come_from_the_zs(self):
        # PUNG until D88 installed the Gemini ice axe as SDAX: the same letters
        self.assertEqual(hs.zs_held_letters(hs.AXE_FD_ZS, hs.AXE_FD_PLACEHOLDER), "")
        self.assertEqual(hs.zs_held_letters(hs.AXE_FD_ZS, hs.AXE_FD_SPRITE), "ABCD")

    @slow
    def test_axe_in_a_gripping_hand_at_pisg_height(self):
        frames = hs.build_axe_fd()
        self.assertEqual(sorted(frames), ["SDAXA0", "SDAXB0", "SDAXC0", "SDAXD0"])
        lumps, pal = hs.read_wad()
        pisg, off = hs.decode_patch(lumps["PISGA0"], pal)
        ref = hs.measure(pisg, off)
        a = frames["SDAXA0"]
        m = hs.measure(a["sprite"], a["offsets"])
        self.assertLessEqual(abs(m["height"] - ref["height"]), 0.1 * ref["height"])
        self.assertLess(abs((m["bbox"][0] + m["bbox"][2]) / 2 - hs.SCREEN_W / 2), 20)
        ours = {tuple(c) for c in hs.ramp_cols(hs.R3_SKIN) + hs.ramp_cols(hs.R3_SLEEVE)}
        fist = hs.build_axe_fd("fist", out_dir=None)
        for name, f in frames.items():
            # the hand is drawn last, in our skin and sleeve only, and the axe is round 1's
            spr, (lx, ty) = f["sprite"], f["offsets"]
            hand = f["hand"]
            hx, hy = f["hand_xy"]
            x0, y0 = hx + lx, hy - (hs.WEAPONTOP - ty)
            sub = spr[y0:y0 + hand.shape[0], x0:x0 + hand.shape[1]]
            mask = hand[..., 3] > 0
            self.assertTrue((sub[mask] == hand[mask]).all(), name)
            self.assertTrue({tuple(c) for c in hand[mask, :3]} <= ours, name)
            self.assertEqual(f["head_y"], fist[name]["head_y"], name)
            _, grab = hs.read_png_sprite(hs.AXE_FD_OUT_DIR / f"{name}.png")
            self.assertEqual(tuple(grab), tuple(f["offsets"]), name)

    @slow
    def test_round1_fist_stays_untouched(self):
        lumps, pal = hs.read_wad()
        bare, _, _ = hs.freedoom_fist_bare(lumps, pal)
        for name, f in hs.build_axe_fd("fist", out_dir=None).items():
            spr, (lx, ty) = f["sprite"], f["offsets"]
            fx, fy = f["pose"].fist
            x0, y0 = fx + lx, fy - (hs.WEAPONTOP - ty)
            sub = spr[y0:y0 + bare.shape[0], x0:x0 + bare.shape[1]]
            mask = bare[..., 3] > 0
            self.assertTrue((sub[mask] == bare[mask]).all(), name)

    def test_rotsprite_keeps_the_palette_and_the_pivot(self):
        img = np.zeros((9, 5, 4), np.uint8)
        img[:, 2] = (200, 100, 50, 255)
        img[4, :] = (10, 20, 30, 255)
        out, piv = hs.rotsprite(img, 90.0, 1.0, (2, 4))
        cols = {tuple(c) for c in out[out[..., 3] > 0][:, :3]}
        self.assertTrue(cols <= {(200, 100, 50), (10, 20, 30)})
        self.assertEqual(out.shape[:2], (5, 9))              # a quarter turn swaps the sides
        self.assertEqual(tuple(out[piv[1], piv[0], :3]), (10, 20, 30))

if __name__ == "__main__":
    unittest.main()
