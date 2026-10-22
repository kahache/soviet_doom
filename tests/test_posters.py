"""The approved posters on every map (CEO, 2026-10-22).

«reutiliza cuadros, mételos en niveles anteriores y en los nuevos el de
Lenin y Stalin, que esos posters puedan aparecer en cualquier nivel».

Owner: `level-designer`. Every campaign map (MAP01-MAP06) and the practice
range declare the same small contract in their `map.py`:

* `POSTERS`: every picture on the map, `(name, texture, axis, coord, lo,
  hi)`, the segment one `GridMap.style_h`/`style_v` call paints;
* `POSTER_SLOTS_MARX_ENGELS`: the two or three names in `POSTERS` kept for
  the Marx-Engels poster `SDPOSTR4` (in preparation: not a lump yet). Until
  it exists each slot wears the Lenin or Stalin it is listed with;
* `MARX_ENGELS`: `None` today. Setting it to "SDPOSTR4" is the one-line swap
  that puts the new poster in every slot of that map;
* `poster_faces()`: `POSTERS` with the slots resolved.

What is checked, read back from the generated TEXTMAP:

* each map shows at least one approved poster, Lenin or Stalin among them,
  between two and five pictures besides the slots (no wallpapering);
* MAP04-MAP06, the new episode, show both Lenin and Stalin;
* every picture is whole: one one-sided line exactly the poster's width,
  in a sector exactly the poster's height, pegged to the floor and at
  offset 0 (MAP01's rule, tests/test_udmf.py);
* the Marx-Engels slots exist and the swap moves them, and only them.

Run:  python -m unittest tests.test_posters -v
"""

from __future__ import annotations

import importlib.util
import re
import sys
import types
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
MARX_ENGELS = "SDPOSTR4"      # in preparation; assumed the twin of Lenin and Stalin
# docs/art/TEXTURE-INDEX.md: width x height of each approved picture.
POSTER_SIZE = {LENIN: (128, 256), MURAL: (128, 128), STALIN: (128, 256),
               MARX_ENGELS: (128, 256)}
APPROVED = (LENIN, MURAL, STALIN)
PORTRAITS = (LENIN, STALIN)

CAMPAIGN = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06")
MAPS = CAMPAIGN + ("RANGE",)
NEW_EPISODE = ("MAP04", "MAP05", "MAP06")
PICTURES_MIN, PICTURES_MAX = 2, 5
SLOTS_MIN, SLOTS_MAX = 2, 3


def _load(name: str):
    path = PROJECT_ROOT / "src" / "maps" / name / "map.py"
    spec = importlib.util.spec_from_file_location(f"sdmap_{name}_posters_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SWAP_LINE = re.compile(r"^MARX_ENGELS(: str \| None)? = None\b.*$", re.M)


def _load_swapped(name: str):
    """The map with its one Marx-Engels line changed, nothing else: the
    swap the art-director's approval of SDPOSTR4 will make."""
    path = PROJECT_ROOT / "src" / "maps" / name / "map.py"
    source = path.read_text(encoding="utf-8")
    lines = SWAP_LINE.findall(source)
    if len(lines) != 1:
        raise AssertionError(f"{name}: {len(lines)} MARX_ENGELS = None lines, not one")
    module = types.ModuleType(f"sdmap_{name}_swapped_test")
    module.__file__ = str(path)
    exec(compile(SWAP_LINE.sub(f'MARX_ENGELS = "{MARX_ENGELS}"', source), str(path), "exec"),
         module.__dict__)
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
        self.assertIsNone(m.MARX_ENGELS, "SDPOSTR4 is not approved yet: the slots wear stand-ins")
        self.assertEqual(len(m.POSTERS), len(m.poster_faces()))

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

    def test_the_marx_engels_slots_exist(self):
        m = self.m
        slots = m.POSTER_SLOTS_MARX_ENGELS
        self.assertGreaterEqual(len(slots), SLOTS_MIN)
        self.assertLessEqual(len(slots), SLOTS_MAX)
        faces = {p[0]: p for p in m.poster_faces()}
        for name in slots:
            self.assertIn(name, faces, f"slot {name} is not in POSTERS")
            # Stand-ins are portraits: the slot is already 128x256, the size
            # SDPOSTR4 is commissioned at.
            self.assertIn(faces[name][1], PORTRAITS, f"slot {name} stands in with {faces[name][1]}")

    def test_the_swap_is_one_line(self):
        """MARX_ENGELS = "SDPOSTR4" puts the new poster in every slot and
        moves nothing else."""
        before = self.blocks
        m = _load_swapped(self.MAP)
        self.assertEqual(MARX_ENGELS, m.MARX_ENGELS)
        after = parse_textmap(m.build_textmap().render())
        slots = set(m.POSTER_SLOTS_MARX_ENGELS)
        for name, texture, axis, coord, lo, hi in m.poster_faces():
            ((_, side),) = _faces_on(after, axis, coord, lo, hi)
            self.assertEqual(MARX_ENGELS if name in slots else texture, side["texturemiddle"], name)
        self.assertIn(MARX_ENGELS, m.WALL_TEXTURES, "the swapped map would not list SDPOSTR4")
        changed = [i for i, (x, y) in enumerate(zip(before["sidedef"], after["sidedef"])) if x != y]
        self.assertEqual(len(slots), len(changed))
        self.assertEqual(before["linedef"], after["linedef"])
        self.assertEqual(before["sector"], after["sector"])


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
    def test_lenin_and_stalin_both_hang_in_every_episode(self):
        worn = {name: {p[1] for p in _load(name).poster_faces()} for name in MAPS}
        for episode in (("MAP01", "MAP02", "MAP03"), NEW_EPISODE):
            seen = set().union(*(worn[n] for n in episode))
            self.assertTrue({LENIN, STALIN} <= seen, f"{episode}: {sorted(seen)}")


if __name__ == "__main__":
    unittest.main()
