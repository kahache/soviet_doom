"""The approved posters on every map (CEO, 2026-10-22).

«reutiliza cuadros, mételos en niveles anteriores y en los nuevos el de
Lenin y Stalin, que esos posters puedan aparecer en cualquier nivel».

Owner: `level-designer`. Every campaign map (MAP01-MAP09) and the practice
range declare the same small contract in their `map.py`:

* `POSTERS`: every picture on the map, `(name, texture, axis, coord, lo,
  hi)`, the segment one `GridMap.style_h`/`style_v` call paints;
* `POSTER_SLOTS_MARX_ENGELS`: the two names in `POSTERS` that carry the
  Marx-Engels pair (D117, 2026-10-22), Marx's slot first: `SDPOSTR4` Marx
  «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» and `SDPOSTR5` Engels «СОЕДИНЯЙТЕСЬ!»;
* `MARX_ENGELS`: the pair, `("SDPOSTR4", "SDPOSTR5")`, in the slots' order;
* `poster_faces()`: every picture as painted (`POSTERS` itself since D117).

What is checked, read back from the generated TEXTMAP:

* each map shows at least one approved poster, Lenin or Stalin among them,
  between two and five pictures besides the pair (no wallpapering);
* MAP04-MAP06, the second episode, show both Lenin and Stalin;
* every picture is whole: one one-sided line exactly the poster's width,
  in a sector exactly the poster's height, pegged to the floor and at
  offset 0 (MAP01's rule, tests/test_udmf.py);
* every map hangs the pair, Marx once and Engels once, in the two slots
  (PAIR names them); where the two share a wall, Marx is on the left as the
  wall is seen from the room (from v1 to v2 along the front side), so the
  two bands read the Manifesto's line left to right.

Run:  python -m unittest tests.test_posters -v
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import test_udmf as udmf_tests  # noqa: E402

parse_textmap = udmf_tests.parse_textmap

LENIN = "SDPOSTR1"
MURAL = "SDPOSTR2"
STALIN = "SDPOSTR3"
MARX = "SDPOSTR4"             # D117: Marx, «ПРОЛЕТАРИИ / ВСЕХ СТРАН,»
ENGELS = "SDPOSTR5"           # D117: Engels, «СОЕДИНЯЙТЕСЬ!», mirrored to look at Marx
MARX_ENGELS = (MARX, ENGELS)
# docs/art/TEXTURE-INDEX.md: width x height of each approved picture.
POSTER_SIZE = {LENIN: (128, 256), MURAL: (128, 128), STALIN: (128, 256),
               MARX: (128, 256), ENGELS: (128, 256)}
APPROVED = (LENIN, MURAL, STALIN, MARX, ENGELS)
PORTRAITS = (LENIN, STALIN)

CAMPAIGN = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06")
MAPS = CAMPAIGN + ("RANGE",)
NEW_EPISODE = ("MAP04", "MAP05", "MAP06")
PICTURES_MIN, PICTURES_MAX = 2, 5
# Where the pair hangs (D117), (Marx's slot, Engels's slot); each map's
# design document (docs/levels/, its posters section) says why.
PAIR = {
    "MAP01": ("hangar_north_slot", "exit_east_slot"),      # the hangar first, the way out last
    "MAP02": ("shelter_east_slot", "shelter_south_slot"),  # Engels round the corner, to Marx's right
    "MAP03": ("dock_slot_n", "hall_slot_s"),               # the dock first, the hall after
    "MAP04": ("warehouse_west", "roundhouse_south"),       # the warehouse first, the roundhouse after
    "MAP05": ("z5_catwalk_w", "z5_catwalk_e"),             # one wall, either side of the yellow door
    "MAP06": ("gum_north_slot", "courtyard_slot"),         # the GUM first, the Kremlin last
    "MAP07": ("z6_slot_e", "z6_slot_w"),                   # one wall, the south one: east is left
    "MAP08": ("z3_slot_w", "z3_slot_e"),                   # one wall, either side of the blue door
    "MAP09": ("lab_hall_slot_n", "lab_hall_slot_s"),       # facing walls; Marx beside Lenin
    "RANGE": ("gallery_west_slot", "gallery_east_slot"),   # end walls; west is left from the passage
}
SAME_WALL = {"MAP05", "MAP07", "MAP08"}


def _load(name: str):
    path = PROJECT_ROOT / "src" / "maps" / name / "map.py"
    spec = importlib.util.spec_from_file_location(f"sdmap_{name}_posters_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _faces_on(blocks, axis: str, coord: int, lo: int, hi: int) -> list[tuple[dict, dict]]:
    """(linedef, front sidedef) of every one-sided line inside the segment."""
    verts = blocks["vertex"]
    out = []
    for ld in blocks["linedef"]:
        if "sideback" in ld:
            continue
        a, b = verts[ld["v1"]], verts[ld["v2"]]
        if axis == "h":
            on = a["y"] == b["y"] == coord and lo <= min(a["x"], b["x"]) and max(a["x"], b["x"]) <= hi
        else:
            on = a["x"] == b["x"] == coord and lo <= min(a["y"], b["y"]) and max(a["y"], b["y"]) <= hi
        if on:
            out.append((ld, blocks["sidedef"][ld["sidefront"]]))
    return out


class _PosterCase:
    MAP: str = ""

    @classmethod
    def setUpClass(cls):
        cls.m = _load(cls.MAP)
        cls.blocks = parse_textmap(cls.m.build_textmap().render())

    def test_the_contract_is_declared(self):
        m = self.m
        for name in ("POSTERS", "POSTER_SLOTS_MARX_ENGELS", "MARX_ENGELS", "poster_faces"):
            self.assertTrue(hasattr(m, name), f"{self.MAP} has no {name}")
        names = [p[0] for p in m.POSTERS]
        self.assertEqual(len(names), len(set(names)), "two posters share a name")
        self.assertEqual(MARX_ENGELS, tuple(m.MARX_ENGELS))
        self.assertEqual(tuple(m.POSTERS), tuple(m.poster_faces()))

    def test_the_map_shows_approved_posters_without_wallpapering(self):
        m = self.m
        slots = set(m.POSTER_SLOTS_MARX_ENGELS)
        pictures = [p for p in m.poster_faces() if p[0] not in slots]
        for name, texture, *_ in m.poster_faces():
            self.assertIn(texture, APPROVED, f"{name} wears {texture}")
        self.assertGreaterEqual(len(pictures), PICTURES_MIN)
        self.assertLessEqual(len(pictures), PICTURES_MAX)
        self.assertTrue(any(p[1] in PORTRAITS for p in pictures), "no Lenin and no Stalin")
        if self.MAP in NEW_EPISODE:
            worn = {p[1] for p in pictures}
            self.assertIn(LENIN, worn, "the new episode shows Lenin")
            self.assertIn(STALIN, worn, "the new episode shows Stalin")

    def test_every_picture_is_whole(self):
        """One line exactly the poster's width, in a sector exactly its
        height, pegged to the floor, at offset 0: nothing stretched, cut or
        tiled."""
        sectors = self.blocks["sector"]
        verts = self.blocks["vertex"]
        used = {sd.get("texturemiddle") for sd in self.blocks["sidedef"]}
        for name, texture, axis, coord, lo, hi in self.m.poster_faces():
            width, height = POSTER_SIZE[texture]
            with self.subTest(poster=name):
                self.assertEqual(width, hi - lo, "the segment is not one poster wide")
                faces = _faces_on(self.blocks, axis, coord, lo, hi)
                self.assertEqual(1, len(faces), f"{len(faces)} lines on the segment, not one")
                ld, side = faces[0]
                self.assertEqual(texture, side["texturemiddle"])
                a, b = verts[ld["v1"]], verts[ld["v2"]]
                self.assertEqual(width, abs(a["x"] - b["x"]) + abs(a["y"] - b["y"]))
                s = sectors[side["sector"]]
                self.assertEqual(height, s["heightceiling"] - s["heightfloor"],
                                 "the wall is not the poster's height")
                self.assertTrue(ld.get("dontpegbottom"), "a poster must be pegged to the floor")
                self.assertEqual(0, side.get("offsetx", 0))
                self.assertEqual(0, side.get("offsety", 0))
        self.assertTrue(used & set(APPROVED), "no approved poster reaches the TEXTMAP")

    def test_the_pair_hangs_in_the_two_slots(self):
        """Marx once and Engels once, each in its slot (PAIR), nowhere else,
        and both listed among the map's wall textures."""
        m = self.m
        self.assertEqual(PAIR[self.MAP], tuple(m.POSTER_SLOTS_MARX_ENGELS))
        faces = {p[0]: p for p in m.poster_faces()}
        for name, texture in zip(m.POSTER_SLOTS_MARX_ENGELS, MARX_ENGELS):
            self.assertIn(name, faces, f"slot {name} is not in POSTERS")
            self.assertEqual(texture, faces[name][1], name)
        worn = [p[1] for p in m.poster_faces()]
        self.assertEqual((1, 1), (worn.count(MARX), worn.count(ENGELS)))
        for texture in MARX_ENGELS:
            self.assertIn(texture, m.WALL_TEXTURES)
        on_lines = [sd.get("texturemiddle") for sd in self.blocks["sidedef"]]
        self.assertEqual((1, 1), (on_lines.count(MARX), on_lines.count(ENGELS)),
                         "the TEXTMAP does not carry the pair exactly once")

    def test_marx_is_on_the_left_where_the_two_share_a_wall(self):
        """Seen from the room, a one-sided line runs from v1 on the left to v2
        on the right (its front side is the room). On a shared wall Marx's
        line comes first along that direction."""
        verts = self.blocks["vertex"]
        faces = {p[0]: p for p in self.m.poster_faces()}
        (_, _, ax_m, co_m, lo_m, hi_m), (_, _, ax_e, co_e, lo_e, hi_e) = (
            faces[n] for n in self.m.POSTER_SLOTS_MARX_ENGELS)
        same_wall = (ax_m, co_m) == (ax_e, co_e)
        self.assertEqual(self.MAP in SAME_WALL, same_wall, "SAME_WALL is out of date")
        if not same_wall:
            return
        ((ld_m, _),) = _faces_on(self.blocks, ax_m, co_m, lo_m, hi_m)
        ((ld_e, _),) = _faces_on(self.blocks, ax_e, co_e, lo_e, hi_e)

        def run(ld):
            a, b = verts[ld["v1"]], verts[ld["v2"]]
            return (b["x"] - a["x"], b["y"] - a["y"]), ((a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2)

        (dx, dy), mid_m = run(ld_m)
        (ex, ey), mid_e = run(ld_e)
        self.assertGreater(dx * ex + dy * ey, 0, "the two lines face different ways")
        self.assertLess(dx * mid_m[0] + dy * mid_m[1], dx * mid_e[0] + dy * mid_e[1],
                        "Engels hangs left of Marx")


class Map01Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP01"


class Map02Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP02"


class Map03Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP03"


class Map04Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP04"


class Map05Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP05"


class Map06Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP06"


class RangePosters(_PosterCase, unittest.TestCase):
    MAP = "RANGE"


# --- MAP07 Novaya Zemlya (episode 3, D112; owner level-designer) -----------
class Map07Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP07"

    def test_episode_3_opens_with_lenin_and_stalin(self):
        worn = {p[1] for p in self.m.poster_faces() if p[0] not in self.m.POSTER_SLOTS_MARX_ENGELS}
        self.assertTrue({LENIN, STALIN} <= worn, sorted(worn))



# --- MAP08 Severomorsk (episode 3, D112; level-designer's block) -------------
class Map08Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP08"

    def test_episode_3s_base_shows_lenin_and_stalin(self):
        slots = set(self.m.POSTER_SLOTS_MARX_ENGELS)
        worn = {p[1] for p in self.m.poster_faces() if p[0] not in slots}
        self.assertTrue({LENIN, STALIN} <= worn, sorted(worn))

# --- MAP09 Tunguska (episode 3, D112; level-designer's block) ----------------
class Map09Posters(_PosterCase, unittest.TestCase):
    MAP = "MAP09"

    def test_the_research_station_shows_lenin_stalin_and_the_mural(self):
        slots = set(self.m.POSTER_SLOTS_MARX_ENGELS)
        worn = {p[1] for p in self.m.poster_faces() if p[0] not in slots}
        self.assertEqual({LENIN, STALIN, MURAL}, worn)
        self.assertTrue(all(p[0].startswith("lab_") for p in self.m.POSTERS), "all in the laboratory")


class CampaignPosters(unittest.TestCase):
    def test_every_map_and_the_range_hang_the_pair(self):
        self.assertEqual(set(PAIR), set(MAPS) | {"MAP07", "MAP08", "MAP09"})
    def test_lenin_and_stalin_both_hang_in_every_episode(self):
        worn = {name: {p[1] for p in _load(name).poster_faces()} for name in MAPS}
        for episode in (("MAP01", "MAP02", "MAP03"), NEW_EPISODE):
            seen = set().union(*(worn[n] for n in episode))
            self.assertTrue({LENIN, STALIN} <= seen, f"{episode}: {sorted(seen)}")


if __name__ == "__main__":
    unittest.main()
