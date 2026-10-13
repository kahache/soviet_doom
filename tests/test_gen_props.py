"""Layout and size contract of tools/art/gen_props.py (batch 3, crates and
lockers for MAP01 v2, request A5).

Cheap on purpose: the full generator (sweep, contexts, sheets) never runs
here. What is checked:

  sizes      every piece sits on the 64 grid and is a multiple of 8
             (ART-BIBLE §2); flats are 64x64
  layout     stencil marks lie inside their clear region and touch no
             batten, strap, latch or brace; locker elements are stacked
             with a declared gap (the lesson of switch variant A)
  no font    the generator never rasterises text with a system font, so
             its lumps are byte-identical on the Mac and on Windows
             (CLAUDE.md, "Text-bearing assets do not reproduce")
  seed       one cell, built twice, is identical (TEXTURE-INDEX records
             script + seed as the origin)
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np  # noqa: F401
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False


def overlaps(a, b) -> bool:
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inside(a, b) -> bool:
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


class NoFontTests(unittest.TestCase):
    def test_generator_uses_no_system_font(self):
        src = (ART_TOOLS / "gen_props.py").read_text(encoding="utf-8")
        code = re.sub(r'""".*?"""', "", src, flags=re.S)          # docstrings may talk about fonts
        for banned in ("ImageFont", "FONT_POSTER", "FONT_SMALL", ".text(", "truetype"):
            self.assertNotIn(banned, code, banned)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy + Pillow (project venv)")
class PropsLayoutTests(unittest.TestCase):
    def setUp(self):
        import gen_props
        self.g = gen_props

    def test_pieces_sit_on_the_grid(self):
        g = self.g
        sizes = {p.row: (p.w, p.h, p.kind) for p in g.PIECES}
        self.assertEqual(sizes, {"R1": (64, 64, "wall"), "R2": (128, 64, "wall"),
                                 "R3": (64, 64, "flat"), "R4": (64, 128, "wall")})
        for p in g.PIECES:
            self.assertEqual(p.w % g.GRID, 0, p.row)
            self.assertEqual(p.h % 8, 0, p.row)
            self.assertLessEqual(len(p.lump), 8)
            self.assertTrue(p.lump.startswith("SD") and p.lump.isupper(), p.lump)

    def test_crate_stencils_are_clear_of_the_structure(self):
        g = self.g
        for row in ("R1", "R2", "R3"):
            p = g.PIECE[row]
            for vid in g.VARIANT_IDS:
                lay = g.crate_layout(row, vid)
                blockers = lay["battens"] + lay["straps"] + lay["metal"]
                marks = [r for _, r in lay["stencil"]]
                self.assertTrue(marks, f"{row}-{vid} has no mark")
                for kind, r in lay["stencil"]:
                    self.assertTrue(inside(r, (0, 0, p.w, p.h)), f"{row}-{vid} {kind} {r}")
                    h, w = g.stencil_mask(kind).shape
                    self.assertEqual((r[2] - r[0], r[3] - r[1]), (w, h), f"{row}-{vid} {kind}")
                    for b in blockers:
                        self.assertFalse(overlaps(r, b), f"{row}-{vid} {kind} {r} hits {b}")
                    if lay["brace"] is not None:
                        band = g.brace_mask((p.h, p.w), lay["brace"], g.BRACE_W + 2)
                        self.assertFalse(band[r[1]:r[3], r[0]:r[2]].any(), f"{row}-{vid} {kind} on the brace")
                for i, a in enumerate(marks):
                    for b in marks[i + 1:]:
                        self.assertFalse(overlaps(a, b), f"{row}-{vid} marks touch")

    def test_locker_elements_never_touch(self):
        g = self.g
        for vid in g.VARIANT_IDS:
            lay = g.locker_layout(vid)
            rows = sorted(lay["rows"].items(), key=lambda kv: kv[1][0])
            for (n0, (_, end)), (n1, (start, _)) in zip(rows, rows[1:]):
                self.assertGreaterEqual(start - end, g.LOCKER_MIN_GAP, f"{vid}: {n0} -> {n1}")
            self.assertEqual(rows[-1][1][1], g.PIECE["R4"].h)
            for (plate, (kind, mark)), (dx0, dx1) in zip(lay["plates"], lay["doors"]):
                self.assertTrue(inside(mark, plate), f"{vid} {kind}")
                self.assertTrue(plate[0] > dx0 and plate[2] < dx1, f"{vid} plate leaves its door")

    def test_one_cell_is_deterministic_and_sized(self):
        g = self.g
        a, b = g.build("R1", "C"), g.build("R1", "C")
        self.assertEqual(a.shape, (64, 64, 3))
        self.assertTrue((a == b).all())
        self.assertEqual(g.build("R4", "D").shape, (128, 64, 3))

    def test_seeds_are_unique_and_clear_of_earlier_batches(self):
        g = self.g
        seeds = [g.seed_of(p.row, v) for p in g.PIECES for v in g.VARIANT_IDS]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertTrue(all(s > 2077 + 4 for s in seeds))   # batch 1 is 1977+, switches 2077+1..4


if __name__ == "__main__":
    unittest.main()
