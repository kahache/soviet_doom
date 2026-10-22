"""tools/map_overview.py: the top-down overview PNGs drawn from a map's TEXTMAP.

Mostly a small synthetic map written here (two rooms, a pillar, a blue
locked door, an exit switch, a secret, a hurting floor, a start, a key and
two monsters of which only one is on skill 3), so every feature has a known
place; plus one real map (RANGE, the smallest) end to end through its
map.py, and the CLI writing a file. Checks: what the parser and the
analysis find, the even-odd fill (the pillar is a hole), the colours at
known pixels, the output size, and that two renders are byte-identical.
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import numpy  # noqa: F401
    from PIL import Image
    import map_overview as mo
    HAVE_DEPS = True
except ImportError:  # pragma: no cover - the venv has both
    HAVE_DEPS = False


def _udmf() -> str:
    """Room A (0..512 x 0..512, floor 0) with a 128 pillar hole, a 64-deep
    door sector D (tag 7, blue lock) to room B (576..1088, floor 64, secret,
    hurting). Exit switch on A's west wall."""
    verts = [
        (0, 0), (512, 0), (512, 512), (0, 512),            # 0-3 room A
        (192, 192), (320, 192), (320, 320), (192, 320),    # 4-7 pillar
        (576, 0), (576, 512),                              # 8-9 door/B shared
        (1088, 0), (1088, 512),                            # 10-11 room B
    ]
    sectors = [
        "heightfloor = 0; heightceiling = 128; texturefloor = \"F\"; textureceiling = \"C\"; lightlevel = 160;",
        "heightfloor = 0; heightceiling = 0; texturefloor = \"F\"; textureceiling = \"C\"; lightlevel = 160; id = 7;",
        "heightfloor = 64; heightceiling = 192; texturefloor = \"F\"; textureceiling = \"C\"; lightlevel = 160; "
        "special = 1024; damageamount = 5; damageinterval = 32;",
    ]
    sides: list[int] = []
    lines: list[str] = []

    def line(v1, v2, front, back=None, extra=""):
        sides.append(front)
        s = f"v1 = {v1}; v2 = {v2}; sidefront = {len(sides) - 1};"
        if back is not None:
            sides.append(back)
            s += f" sideback = {len(sides) - 1}; twosided = true;"
        lines.append(s + " " + extra)

    # room A, wound so the front faces in (right-hand side)
    line(0, 3, 0, extra="special = 243; playeruse = true;")    # west wall: exit
    line(3, 2, 0)
    line(1, 0, 0)
    # pillar: one-sided, front faces room A (outside the pillar)
    line(4, 5, 0)
    line(5, 6, 0)
    line(6, 7, 0)
    line(7, 4, 0)
    # A -> door (x=512), door -> B (x=576), with the locked door special
    line(2, 1, 0, 1, "special = 13; arg0 = 7; arg3 = 2; playeruse = true;")
    line(1, 8, 1)
    line(9, 2, 1)
    line(8, 9, 2, 1)
    # room B
    line(8, 10, 2)
    line(10, 11, 2)
    line(11, 9, 2)

    def thing(x, y, t, skills=(1, 2, 3, 4, 5), angle=0):
        flags = " ".join(f"skill{s} = true;" for s in skills)
        return f"thing {{ x = {x}.0; y = {y}.0; angle = {angle}; type = {t}; {flags} single = true; }}\n"

    out = ['namespace = "zdoom";\n']
    out.append(thing(64, 64, 1, angle=90))
    out.append(thing(448, 448, 5))                      # blue pass
    out.append(thing(832, 256, 3004, skills=(3, 4)))    # rifleman on skill 3
    out.append(thing(960, 256, 21106, skills=(4,)))     # general, skill 4 only
    out.append(thing(448, 64, 21004))                   # a weapon
    for x, y in verts:
        out.append(f"vertex {{ x = {x}.0; y = {y}.0; }}\n")
    for s in lines:
        out.append(f"linedef {{ {s} }}\n")
    for sec in sides:
        out.append(f'sidedef {{ sector = {sec}; texturemiddle = "W"; }}\n')
    for s in sectors:
        out.append(f"sector {{ {s} }}\n")
    return "".join(out)


TEXTMAP = _udmf() if HAVE_DEPS else ""


@unittest.skipUnless(HAVE_DEPS, "needs Pillow and numpy (the venv)")
class ParseAndAnalyseTests(unittest.TestCase):
    def setUp(self):
        self.m = mo.parse_textmap("// a comment\n" + TEXTMAP)
        self.f = mo.analyse(self.m)

    def test_parser_counts_and_types(self):
        self.assertEqual(len(self.m.vertices), 12)
        self.assertEqual(len(self.m.sectors), 3)
        self.assertEqual(len(self.m.linedefs), 14)
        self.assertEqual(len(self.m.things), 5)
        self.assertIs(self.m.linedefs[0]["playeruse"], True)
        self.assertEqual(self.m.sectors[2]["special"], 1024)

    def test_locked_door_takes_the_key_colour_and_the_exit_is_found(self):
        self.assertEqual(self.f.door_sectors, {1: "blue"})
        self.assertEqual(self.f.exit_lines, [(0, False)])
        # the door is worked from its own face, so it is no remote switch
        self.assertEqual(self.f.switch_lines, [])

    def test_secret_hazard_start_key_weapon(self):
        self.assertEqual(self.f.secret_sectors, [2])
        self.assertEqual(self.f.hazard_sectors, [2])
        self.assertEqual(self.f.start["type"], 1)
        self.assertEqual([c for _, c in self.f.keys], ["blue"])
        self.assertEqual(len(self.f.weapons), 1)

    def test_monsters_only_on_the_requested_skill(self):
        self.assertEqual([c.name for _, c in self.f.monsters], ["Reich rifleman"])
        on4 = mo.analyse(self.m, skill=4)
        self.assertEqual(sorted(c.name for _, c in on4.monsters), ["General (boss)", "Reich rifleman"])

    def test_remote_switch_is_reported(self):
        tm = TEXTMAP.replace("special = 243;", "special = 12; arg0 = 7;")
        f = mo.analyse(mo.parse_textmap(tm))
        self.assertIn((0, "door"), f.switch_lines)


@unittest.skipUnless(HAVE_DEPS, "needs Pillow and numpy (the venv)")
class FillAndColourTests(unittest.TestCase):
    SCALE = 0.25

    def setUp(self):
        self.m = mo.parse_textmap(TEXTMAP)
        x0, _, x1, y1 = mo.bounds(self.m)
        self.view = mo.View(x0, y1, self.SCALE, 0, 0)
        _, y0, _, _ = mo.bounds(self.m)
        self.w = int((x1 - x0) * self.SCALE) + 1
        self.h = int((y1 - y0) * self.SCALE) + 1

    def at(self, arr, x, y):
        px, py = self.view.px(x, y)
        return arr[int(py), int(px)]

    def test_even_odd_fill_leaves_the_pillar_and_the_void_empty(self):
        lab = mo.sector_labels(self.m, self.view, self.w, self.h)
        self.assertEqual(self.at(lab, 100, 100), 0)
        self.assertEqual(self.at(lab, 256, 256), -1)     # pillar
        self.assertEqual(self.at(lab, 544, 256), 1)      # door
        self.assertEqual(self.at(lab, 800, 400), 2)
        self.assertEqual(self.at(lab, -40, -40), -1)     # padding

    def test_colours_at_known_places(self):
        img = mo.draw_map(self.m, mo.analyse(self.m), self.w, self.h, self.view, mo.FULL)
        arr = numpy.asarray(img)
        self.assertEqual(tuple(self.at(arr, 544, 300)), mo.KEY_COLOURS["blue"])
        self.assertEqual(tuple(self.at(arr, 100, 400)), mo.RAMP[0])        # lowest floor
        self.assertEqual(tuple(self.at(arr, 64, 70)), mo.START)            # arrow body

    def test_ramp_ends_and_floor_ranking(self):
        heights, colours = mo.floor_colours(self.m)
        self.assertEqual(heights, [0, 64])
        self.assertEqual(colours[0], mo.RAMP[0])
        self.assertEqual(colours[64], mo.RAMP[-1])

    def test_pick_scale_walks_the_ladder(self):
        self.assertEqual(mo.pick_scale(1000, 1000, 2000, 1500), 1 / 2)
        self.assertEqual(mo.pick_scale(7000, 5500, 2000, 1500), 1 / 4)
        self.assertEqual(mo.scale_label(1 / 8), "1 px = 8 units")


@unittest.skipUnless(HAVE_DEPS, "needs Pillow and numpy (the venv)")
class RenderTests(unittest.TestCase):
    def test_overview_size_and_determinism(self):
        a = mo.render_overview(TEXTMAP, "TEST", "Synthetic")
        b = mo.render_overview(TEXTMAP, "TEST", "Synthetic")
        self.assertEqual(a.mode, "RGB")
        # 1216 x 640 units (bounds + 64 pad) fit at 1/2 -> 608 x 320 map area
        self.assertEqual(a.width, 3 * mo.COL_W + 2 * mo.MARGIN)
        self.assertGreater(a.height, 320 + mo.HEADER_H)
        buf_a, buf_b = io.BytesIO(), io.BytesIO()
        a.save(buf_a, "PNG")
        b.save(buf_b, "PNG")
        self.assertEqual(buf_a.getvalue(), buf_b.getvalue())

    def test_campaign_sheet_has_a_fixed_frame(self):
        img = mo.render_campaign({"MAP01": TEXTMAP, "RANGE": TEXTMAP})
        cell_w = mo.TILE_W + 24
        right_w = max(mo.TILE_W, 2 * mo.COL_W) + 24
        self.assertEqual(img.width, mo.MARGIN + 30 + 3 * cell_w + right_w + mo.MARGIN)
        self.assertEqual(img.height, mo.HEADER_H + 3 * (mo.TILE_H + 64) + mo.MARGIN)

    def test_range_end_to_end_from_its_map_script(self):
        tm = mo.load_textmap("RANGE")
        feats = mo.analyse(mo.parse_textmap(tm))
        self.assertIsNotNone(feats.start)
        self.assertTrue(feats.exit_lines)
        self.assertTrue(feats.monsters)
        img = mo.render_overview(tm, "RANGE", "Training Ground", "src/maps/RANGE/map.py")
        self.assertLessEqual(img.width, mo.MAX_MAP_W + 2 * mo.MARGIN)

    def test_cli_writes_a_png_from_a_textmap_file(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "TEST.txt"
            src.write_text(TEXTMAP, encoding="ascii")
            out = Path(d) / "out.png"
            with unittest.mock.patch("sys.stdout", new=io.StringIO()):
                self.assertEqual(mo.main(["--textmap", str(src), "--out", str(out)]), 0)
            with Image.open(out) as im:
                self.assertEqual(im.format, "PNG")

    def test_map_names_come_from_language(self):
        en, ru = mo.map_names("MAP05")
        self.assertEqual(en, "Volga Dam")
        self.assertTrue(ru)


if __name__ == "__main__":
    unittest.main()
