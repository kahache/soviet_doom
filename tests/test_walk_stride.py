"""tools/art/walk_stride.py (D127): the hand-derived walk strides of the
Legion gunner (SDLG) and the Liberty Colossus (SDLC).

Pure functions on synthetic arrays (no Gemini sheet needed): a lifted piece
moves and leaves the background behind, the rest of the sheet is untouched;
the torso alignment finds the shift and keeps the lump contract (left = half
the width, one canvas per frame letter, MOD-SPEC 6.3); the gemini_enemy.py
patch still applies to the GUNNER and COLOSSUS blocks it was measured on.
"""
import ast
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "art"))

try:
    import numpy as np
    from PIL import Image
    import gemini_enemy as ge
    import walk_stride as ws
except ImportError:   # CI's stdlib-only interpreter
    ws = None


@unittest.skipIf(ws is None, "art venv (numpy, Pillow) missing")
class DeriveTests(unittest.TestCase):
    BG = (250, 5, 250)

    def sheet(self):
        rgb = np.zeros((60, 40, 3), np.uint8)
        rgb[:] = self.BG
        rgb[5:30, 10:30] = (200, 200, 200)     # body
        rgb[30:55, 12:18] = (40, 40, 40)       # left leg
        rgb[30:55, 22:28] = (90, 90, 90)       # right leg
        fig = (rgb != self.BG).any(axis=-1)
        return rgb, fig

    def test_lifted_piece_moves_and_leaves_background(self):
        rgb, fig = self.sheet()
        view = ws.View((ws.Piece(ws._box(10, 40, 19, 59), (("shift", 0, -6),), z=1),))
        out, changed = ws.derive_frame(rgb, [fig], np.array(self.BG, float), (view,))
        self.assertTrue((out[49:55, 12:18] == self.BG).all())            # the boot's old rows: background
        self.assertTrue((out[34:49, 12:18] == (40, 40, 40)).all())       # the leg, 6 rows up
        np.testing.assert_array_equal(out[:, 20:], rgb[:, 20:])          # the other leg and the rest: untouched
        self.assertTrue(changed[50, 14] and not changed[10, 25])

    def test_piece_under_the_body_does_not_cover_it(self):
        rgb, fig = self.sheet()
        view = ws.View((ws.Piece(ws._box(10, 30, 19, 59), (("shift", 0, -10),), z=-1),))
        out, _ = ws.derive_frame(rgb, [fig], np.array(self.BG, float), (view,))
        self.assertTrue((out[20:30, 12:18] == (200, 200, 200)).all())    # the body stays on top

    def test_shear_slides_rows_under_y0(self):
        lay = Image.fromarray(np.full((10, 10, 4), 255, np.uint8), "RGBA")
        a = np.asarray(ws._apply(lay, (("shear", 0.5, 4),)))
        self.assertEqual(int(a[4, :, 3].argmax()), 0)
        self.assertEqual(int(a[8, :, 3].argmax()), 2)                     # 4 rows under y0: 2 px right

    def test_stride_specs_cover_five_views(self):
        for name, st in ws.STRIDES.items():
            self.assertEqual(set(st.frames), {"A", "C"}, name)
            for letter, views in st.frames.items():
                self.assertEqual(len(views), 5, f"{name} {letter}")
                for v in views:
                    for p in v.pieces:
                        for x, y in p.poly:
                            self.assertTrue(0 <= x <= 1024 and 0 <= y <= 572, f"{name} {letter} {p.poly}")


@unittest.skipIf(ws is None, "art venv (numpy, Pillow) missing")
class AlignTests(unittest.TestCase):
    @staticmethod
    def sprite(dx):
        a = np.zeros((40, 30, 4), np.uint8)
        a[2:20, 8 + dx:22 + dx] = (200, 200, 200, 255)   # torso
        a[20:36, 10:20] = (40, 40, 40, 255)               # legs, where the axis is
        return a

    def test_torso_shift_finds_the_offset(self):
        b = self.sprite(0)
        a = self.sprite(3)
        self.assertEqual(ws.torso_shift(a, (15, 31), b, (15, 31)), -3)

    def test_align_keeps_the_lump_contract(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for letter, dx in (("A", 2), ("B", 0), ("C", -2)):
                for r in "12345678":
                    ge.save_sprite(self.sprite(dx), (15, 31), d / f"SDXX{letter}{r}.png")
            shifts = ws.align_letters(d, "SDXX")
            self.assertEqual(shifts["SDXXA1"], -2)
            self.assertEqual(shifts["SDXXC5"], 2)
            for letter in "AC":
                seen = set()
                for r in "12345678":
                    p = d / f"SDXX{letter}{r}.png"
                    with Image.open(p) as im:
                        w = im.width
                    gx, gy = ge.read_grab(p)
                    self.assertEqual(gx, w // 2)
                    seen.add((w, gx, gy))
                self.assertEqual(len(seen), 1, letter)


@unittest.skipIf(ws is None, "art venv (numpy, Pillow) missing")
class PatchTests(unittest.TestCase):
    def test_spec_patch_applies_or_is_applied(self):
        text = ws.GE_PATH.read_text(encoding="utf-8")
        if "gem_gunner_strideA.png" in text:
            self.skipTest("gemini_enemy.py already reads the stride sheets (patch applied)")
        new = ws.patched_spec_text(text)
        ast.parse(new)
        self.assertIn('"A": Rotated("strideA")', new)
        self.assertNotIn("COLOSSUS_SWAY", new)

    def test_stride_spec_reads_the_stride_sheets(self):
        for name in ws.STRIDES:
            spec = ws.stride_spec(name)
            self.assertNotIn("walkL", spec.sheets)
            self.assertEqual(spec.sheets["strideA"].file, ws.stride_name(name, "A"))
            self.assertEqual(spec.rotated["C"].sheet, "strideC")
            self.assertEqual(spec.rotated["A"].tilt, 0.0)
            self.assertEqual(sorted(spec.rotated), sorted(ge.PENDING[name].rotated))


if __name__ == "__main__":
    unittest.main()
