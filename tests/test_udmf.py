"""Tests for the UDMF builder and for the MAP01 floor plan it produces.

Owner: `level-designer`. Two halves, on purpose:

* `Udmf*Test` / `GridMap*Test` exercise `tools/sdbuild/udmf.py` - the block
  rendering, and the rectangle painter that turns a floor plan into correctly
  wound, correctly split linedefs.
* `Map01*Test` is a regression harness over the *generated map itself*: it
  re-derives the connectivity of `src/maps/MAP01/map.py` from the TEXTMAP and
  asserts the properties the design document promises - no unreachable room,
  no one-way trap, the gate order, every door tall enough to walk through.
  These are the static half of criterion G3-6 in
  `docs/levels/MAP01-zarya-7.md` section 11, run on every commit instead of
  once by hand.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from sdbuild.udmf import (  # noqa: E402
    SECTOR_SPECIAL_LIGHT_FLICKER,
    SECTOR_SPECIAL_SECRET,
    SPECIAL_DOOR_OPEN,
    SPECIAL_DOOR_RAISE,
    SPECIAL_EXIT_NORMAL,
    GridMap,
    LineStyle,
    Linedef,
    Sector,
    Sidedef,
    TextMap,
    Thing,
    door_open_style,
    door_raise_style,
    exit_switch_style,
    skill_tier,
    switch_door_open_style,
)

WALL = "STARTAN2"
FLOOR = "FLOOR4_8"
CEILING = "CEIL3_5"

# Doom player metrics; the numbers the reachability model is built on.
MAX_STEP_UP = 24     # the tallest floor change a player walks up unaided
PLAYER_HEIGHT = 56   # the shortest gap a player fits through
VIEW_HEIGHT = 41     # the player's eye above his floor (Doom's 41)
USE_RANGE = 64       # how far a player can reach a line to press it


# --- TEXTMAP parsing -------------------------------------------------------

RE_BLOCK = re.compile(r"^(\w+)\s*\{(.*?)\}", re.S | re.M)
RE_FIELD = re.compile(r"(\w+)\s*=\s*([^;]+);")


def parse_textmap(text: str) -> dict[str, list[dict]]:
    """Parse a TEXTMAP into {blockkind: [ {field: value}, ... ]}."""
    out: dict[str, list[dict]] = defaultdict(list)
    for kind, body in RE_BLOCK.findall(text):
        fields: dict[str, object] = {}
        for key, raw in RE_FIELD.findall(body):
            raw = raw.strip()
            if raw in ("true", "false"):
                fields[key] = raw == "true"
            elif raw.startswith('"'):
                fields[key] = raw[1:-1]
            else:
                fields[key] = float(raw) if "." in raw else int(raw)
        out[kind].append(fields)
    return out


def sector_loops(blocks) -> dict[int, list[tuple[int, int]]]:
    """For each sector, the directed edges that walk its own boundary.

    A front side walks v1 -> v2; the back side of the same line walks it the
    other way. A watertight sector therefore has in-degree == out-degree at
    every vertex, and its signed area is negative (clockwise with y up, which
    is what puts the interior on the front side of every line).
    """
    edges: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for ld in blocks["linedef"]:
        front = blocks["sidedef"][ld["sidefront"]]["sector"]
        edges[front].append((ld["v1"], ld["v2"]))
        if "sideback" in ld:
            back = blocks["sidedef"][ld["sideback"]]["sector"]
            edges[back].append((ld["v2"], ld["v1"]))
    return edges


def signed_area(blocks, edges) -> float:
    total = 0.0
    for a, b in edges:
        pa, pb = blocks["vertex"][a], blocks["vertex"][b]
        total += pa["x"] * pb["y"] - pb["x"] * pa["y"]
    return total / 2.0


# --- the block classes -----------------------------------------------------


class UdmfBlockTest(unittest.TestCase):
    def test_linedef_without_special_writes_no_args(self):
        text = Linedef(v1=0, v2=1, sidefront=0, blocking=True).to_udmf()
        self.assertIn("blocking = true;", text)
        self.assertNotIn("arg0", text)
        self.assertNotIn("special", text)
        self.assertNotIn("sideback", text)

    def test_linedef_with_special_writes_all_five_args(self):
        text = Linedef(
            v1=0, v2=1, sidefront=0, sideback=1,
            special=SPECIAL_DOOR_RAISE, arg0=7, arg1=16, arg2=150,
            flags=("twosided", "playeruse", "repeatspecial"),
        ).to_udmf()
        self.assertIn(f"special = {SPECIAL_DOOR_RAISE};", text)
        for i, value in enumerate((7, 16, 150, 0, 0)):
            self.assertIn(f"arg{i} = {value};", text)
        for flag in ("twosided", "playeruse", "repeatspecial"):
            self.assertIn(f"{flag} = true;", text)

    def test_unknown_linedef_flag_is_a_build_error(self):
        # A misspelt flag must fail loudly: the engine would just ignore it.
        with self.assertRaises(ValueError):
            Linedef(v1=0, v2=1, sidefront=0, flags=("playerusse",))
        with self.assertRaises(ValueError):
            LineStyle(flags=("twoosided",))

    def test_sector_id_and_special(self):
        text = Sector(FLOOR, CEILING, identifier=10, special=1024).to_udmf()
        self.assertIn("id = 10;", text)
        self.assertIn("special = 1024;", text)
        self.assertNotIn("id = 0;", Sector(FLOOR, CEILING).to_udmf())

    def test_vertex_reuse(self):
        tm = TextMap()
        a = tm.vertex(64, 64)
        b = tm.vertex(64, 64)
        c = tm.vertex(64, 65)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(2, len(tm.vertices))

    def test_add_room_rect_is_a_closed_clockwise_room(self):
        tm = TextMap()
        tm.add_room_rect(0, 0, 512, 512, Sector(FLOOR, CEILING), WALL)
        blocks = parse_textmap(tm.render())
        self.assertEqual(1, len(blocks["sector"]))
        self.assertEqual(4, len(blocks["vertex"]))
        self.assertEqual(4, len(blocks["linedef"]))
        for ld in blocks["linedef"]:
            self.assertTrue(ld["blocking"])
            self.assertNotIn("sideback", ld)
        self.assertLess(signed_area(blocks, sector_loops(blocks)[0]), 0)

    def test_add_room_rect_rejects_a_degenerate_rectangle(self):
        with self.assertRaises(ValueError):
            TextMap().add_room_rect(0, 0, 0, 512, Sector(FLOOR, CEILING), WALL)


class SkillTest(unittest.TestCase):
    """Per-skill things (v3): Doom's three spawn tiers on UDMF's five flags."""

    def test_skill_tiers_follow_dooms_pairs(self):
        self.assertEqual((1, 2, 3, 4, 5), skill_tier())
        self.assertEqual((3, 4, 5), skill_tier(3), "a monster from medium up")
        self.assertEqual((4, 5), skill_tier(4), "a monster on hard only")
        self.assertEqual((1, 2, 3), skill_tier(highest=3), "a consumable up to medium")
        self.assertEqual((1, 2), skill_tier(highest=2), "a consumable on easy only")
        for bad in ((5, None), (1, None), (4, 3)):
            with self.assertRaises(ValueError):
                skill_tier(*bad)

    def test_thing_on_skills_writes_exactly_those_flags(self):
        text = Thing.on_skills(64, 64, 3004, skill_tier(3), angle=90).to_udmf()
        for n in (1, 2):
            self.assertIn(f"skill{n} = false;", text)
        for n in (3, 4, 5):
            self.assertIn(f"skill{n} = true;", text)
        self.assertIn("angle = 90;", text)
        self.assertIn("single = true;", text)
        with self.assertRaises(ValueError):
            Thing.on_skills(0, 0, 1, ())
        with self.assertRaises(ValueError):
            Thing.on_skills(0, 0, 1, (6,))


# --- the painter -----------------------------------------------------------


def painted(rects_by_sector, styles=(), sectors=None):
    """Build a TextMap from {sector: [rects]} and return its parsed blocks."""
    tm = TextMap()
    g = GridMap(tm, wall=WALL)
    for i, rects in enumerate(rects_by_sector):
        spec = sectors[i] if sectors else Sector(FLOOR, CEILING)
        index = tm.add_sector(spec)
        g.paint_all(index, rects)
    for axis, coord, lo, hi, style in styles:
        (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)
    g.build()
    return parse_textmap(tm.render())


class GridMapTest(unittest.TestCase):
    def test_single_room_is_four_walls(self):
        blocks = painted([[(0, 0, 256, 256)]])
        self.assertEqual(4, len(blocks["linedef"]))
        self.assertEqual(4, len(blocks["vertex"]))
        for ld in blocks["linedef"]:
            self.assertTrue(ld["blocking"])

    def test_two_rooms_sharing_a_whole_wall(self):
        # 6 outer walls + 1 two-sided line between them.
        blocks = painted([[(0, 0, 256, 256)], [(256, 0, 512, 256)]])
        two_sided = [ld for ld in blocks["linedef"] if "sideback" in ld]
        self.assertEqual(1, len(two_sided))
        self.assertTrue(two_sided[0]["twosided"])
        self.assertNotIn("blocking", two_sided[0])
        self.assertEqual(7, len(blocks["linedef"]))

    def test_partial_overlap_is_split_into_wall_opening_wall(self):
        # The right room only covers the middle third of the left room's wall:
        # the shared x must become wall / two-sided / wall, not one long line.
        blocks = painted([[(0, 0, 256, 384)], [(256, 128, 512, 256)]])
        on_seam = []
        for ld in blocks["linedef"]:
            a, b = blocks["vertex"][ld["v1"]], blocks["vertex"][ld["v2"]]
            if a["x"] == b["x"] == 256:
                on_seam.append((min(a["y"], b["y"]), max(a["y"], b["y"]), "sideback" in ld))
        self.assertEqual(
            [(0, 128, False), (128, 256, True), (256, 384, False)], sorted(on_seam)
        )

    def test_one_sector_painted_as_two_rects_has_no_internal_line(self):
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        s = tm.add_sector(Sector(FLOOR, CEILING))
        g.paint(s, 0, 0, 256, 256)
        g.paint(s, 256, 0, 512, 256)
        g.build()
        blocks = parse_textmap(tm.render())
        self.assertEqual(0, len([ld for ld in blocks["linedef"] if "sideback" in ld]))
        # And the four collinear outer segments merged back into four walls.
        self.assertEqual(4, len(blocks["linedef"]))

    def test_painting_is_last_wins(self):
        # The second sector is painted inside the first and takes those cells.
        blocks = painted([[(0, 0, 512, 512)], [(128, 128, 384, 384)]])
        inner = [ld for ld in blocks["linedef"] if "sideback" in ld]
        self.assertEqual(4, len(inner), "the inner island needs four shared lines")
        self.assertEqual(8, len(blocks["linedef"]))

    def test_every_sector_boundary_is_clockwise(self):
        blocks = painted([
            [(0, 0, 512, 512)],
            [(128, 128, 384, 384)],
            [(512, 0, 640, 128)],
        ])
        loops = sector_loops(blocks)
        for index in range(len(blocks["sector"])):
            self.assertLess(signed_area(blocks, loops[index]), 0, f"sector {index}")

    def test_every_sector_boundary_is_closed(self):
        blocks = painted([
            [(0, 0, 512, 512)],
            [(512, 128, 768, 256)],
            [(256, 512, 384, 640)],
        ])
        for index, edges in sector_loops(blocks).items():
            out_deg: dict[int, int] = defaultdict(int)
            in_deg: dict[int, int] = defaultdict(int)
            for a, b in edges:
                out_deg[a] += 1
                in_deg[b] += 1
            for vertex in set(out_deg) | set(in_deg):
                self.assertEqual(out_deg[vertex], in_deg[vertex],
                                 f"sector {index} is not closed at vertex {vertex}")

    def test_style_lands_only_on_its_own_segment(self):
        style = LineStyle(special=SPECIAL_DOOR_OPEN, args=(5, 16, 0, 0, 0),
                          flags=("playeruse",))
        blocks = painted(
            [[(0, 0, 256, 384)], [(256, 0, 512, 384)]],
            styles=[("v", 256, 128, 256, style)],
        )
        specials = [ld for ld in blocks["linedef"] if ld.get("special")]
        self.assertEqual(1, len(specials))
        a, b = blocks["vertex"][specials[0]["v1"]], blocks["vertex"][specials[0]["v2"]]
        self.assertEqual({128.0, 256.0}, {a["y"], b["y"]})
        self.assertEqual(5, specials[0]["arg0"])
        # The seam is now three lines: the styled one plus a wall either side.
        seam = [ld for ld in blocks["linedef"]
                if blocks["vertex"][ld["v1"]]["x"] == blocks["vertex"][ld["v2"]]["x"] == 256]
        self.assertEqual(3, len(seam))

    def test_back_sector_pins_the_winding_on_both_sides_of_a_door(self):
        """The reason doors work from both rooms.

        ZDoom fires a `playeruse` special only from the FRONT side of a
        line. A door sector sits between two rooms, so without pinning, one
        of its two lines would face into the door and be dead on that side.
        """
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        west = tm.add_sector(Sector(FLOOR, CEILING))
        door = tm.add_sector(Sector(FLOOR, CEILING, heightceiling=0, identifier=1))
        east = tm.add_sector(Sector(FLOOR, CEILING))
        g.paint(west, 0, 0, 256, 128)
        g.paint(door, 256, 0, 320, 128)
        g.paint(east, 320, 0, 576, 128)
        style = door_raise_style(1, door)
        g.style_v(256, 0, 128, style)
        g.style_v(320, 0, 128, style)
        g.build()
        blocks = parse_textmap(tm.render())
        specials = [ld for ld in blocks["linedef"] if ld.get("special")]
        self.assertEqual(2, len(specials))
        for ld in specials:
            front = blocks["sidedef"][ld["sidefront"]]["sector"]
            back = blocks["sidedef"][ld["sideback"]]["sector"]
            self.assertEqual(door, back, "the door sector must be the BACK side")
            self.assertIn(front, (west, east))
            self.assertTrue(ld["playeruse"])
            self.assertTrue(ld["repeatspecial"])

    def test_back_sector_not_on_the_segment_is_an_error(self):
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        a = tm.add_sector(Sector(FLOOR, CEILING))
        b = tm.add_sector(Sector(FLOOR, CEILING))
        g.paint(a, 0, 0, 256, 128)
        g.paint(b, 256, 0, 512, 128)
        g.style_v(256, 0, 128, LineStyle(special=SPECIAL_DOOR_OPEN, back_sector=99))
        with self.assertRaises(ValueError):
            g.build()

    def test_degenerate_input_is_rejected(self):
        g = GridMap(TextMap(), wall=WALL)
        with self.assertRaises(ValueError):
            g.paint(0, 10, 10, 10, 20)
        with self.assertRaises(ValueError):
            g.style_v(0, 10, 10, LineStyle())
        with self.assertRaises(ValueError):
            g.style_h(0, 20, 10, LineStyle())

    def test_floor_pegging_is_for_walls_not_for_flanks(self):
        """`dontpegbottom` stacks a WALL's middle texture from the floor. On
        a two-sided line it would hang the lower texture - a raised floor's
        flank - from this room's ceiling instead, and cut a crate or the
        catwalk's face in half. So by default only one-sided lines get it.
        """
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        room = tm.add_sector(Sector(FLOOR, CEILING, heightceiling=104))
        box = tm.add_sector(Sector(FLOOR, CEILING, heightfloor=64, heightceiling=104))
        g.paint(room, 0, 0, 256, 256)
        g.paint(box, 64, 64, 128, 128)
        g.build()
        blocks = parse_textmap(tm.render())
        for ld in blocks["linedef"]:
            if "sideback" in ld:
                self.assertNotIn("dontpegbottom", ld, "a flank hung from the ceiling")
            else:
                self.assertTrue(ld["dontpegbottom"], "a wall not pegged to the floor")

    def test_carve_makes_a_column_of_void(self):
        """`carve` (v3) is how a column is made: the cells leave the room,
        and every edge round them is a one-sided wall OF THE ROOM, wound
        clockwise like any other, so the room is a sector with a hole."""
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        room = tm.add_sector(Sector(FLOOR, CEILING))
        g.paint(room, 0, 0, 256, 256)
        g.carve(96, 96, 160, 160)
        g.build()
        blocks = parse_textmap(tm.render())
        self.assertEqual(8, len(blocks["linedef"]), "4 outer walls + 4 column faces")
        for ld in blocks["linedef"]:
            self.assertNotIn("sideback", ld)
            self.assertTrue(ld["blocking"])
            self.assertEqual(room, blocks["sidedef"][ld["sidefront"]]["sector"])
        edges = sector_loops(blocks)[room]
        out_deg, in_deg = defaultdict(int), defaultdict(int)
        for a, b in edges:
            out_deg[a] += 1
            in_deg[b] += 1
        self.assertEqual(dict(out_deg), dict(in_deg), "the room leaks round its column")
        # Signed area: the room minus the column.
        self.assertEqual(-(256 * 256 - 64 * 64), signed_area(blocks, edges))
        with self.assertRaises(ValueError):
            g.carve(10, 10, 10, 20)

    def test_carve_is_last_wins_like_paint(self):
        """A column carved through a raised platform splits it; a sector
        painted over a carve fills it back in."""
        tm = TextMap()
        g = GridMap(tm, wall=WALL)
        room = tm.add_sector(Sector(FLOOR, CEILING))
        g.paint(room, 0, 0, 256, 256)
        g.carve(0, 0, 256, 256)
        g.paint(room, 0, 0, 128, 128)
        g.build()
        blocks = parse_textmap(tm.render())
        self.assertEqual(4, len(blocks["linedef"]))

    def test_the_first_registered_style_wins(self):
        """The rule index (v3, for speed) keeps the painter's contract: of
        two styles covering the same segment, the one registered first."""
        first, second = LineStyle(texture="FIRST"), LineStyle(texture="SECOND")
        blocks = painted([[(0, 0, 256, 256)]],
                         styles=[("v", 0, 0, 256, first), ("v", 0, 0, 256, second),
                                 ("v", 0, 64, 128, second)])
        textures = {blocks["sidedef"][ld["sidefront"]]["texturemiddle"] for ld in blocks["linedef"]
                    if blocks["vertex"][ld["v1"]]["x"] == blocks["vertex"][ld["v2"]]["x"] == 0}
        self.assertEqual({"FIRST"}, textures)

    def test_a_gate_switch_can_be_one_shot_and_carry_a_light_tag(self):
        style = switch_door_open_style(10, lighttag=30, repeatable=False)
        self.assertEqual((10, 16, 30, 0, 0), style.args, "Door_Open (tag, speed, lighttag)")
        self.assertEqual(("playeruse",), style.flags)
        self.assertIn("repeatspecial", switch_door_open_style(10).flags)

    def test_ready_made_styles_carry_the_documented_specials(self):
        self.assertEqual(SPECIAL_DOOR_RAISE, door_raise_style(1, 0).special)
        self.assertEqual(SPECIAL_DOOR_OPEN, door_open_style(1, 0).special)
        self.assertEqual(SPECIAL_DOOR_OPEN, switch_door_open_style(1).special)
        self.assertEqual(SPECIAL_EXIT_NORMAL, exit_switch_style().special)
        # A switch is on a one-sided wall: it must not pin a back sector.
        self.assertIsNone(switch_door_open_style(1).back_sector)
        self.assertIsNone(exit_switch_style().back_sector)
        # Everything that gates progress must be repeatable (design section 4).
        for style in (door_raise_style(1, 0), door_open_style(1, 0), switch_door_open_style(1)):
            self.assertIn("repeatspecial", style.flags)


# --- MAP01 ------------------------------------------------------------------


def _load_map01():
    path = PROJECT_ROOT / "src" / "maps" / "MAP01" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP01_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Map01Test(unittest.TestCase):
    """Static playability checks on the generated MAP01 (G3-1, G3-6, v0 row)."""

    @classmethod
    def setUpClass(cls):
        cls.map01 = _load_map01()
        textmap, cls.plan = cls.map01.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        # A door is a tagged sector that is closed (ceiling on its floor).
        # Since v2 a tag can also name a light (TAG_LIGHT_GATE_POWER), and
        # those sectors are rooms, not doors. Since v3 one tag can name
        # several doors (D4 and the fuel-bay ambush panels share SW-A's tag;
        # D5 and the wave-2 closets share SW-B's), so it maps to a set.
        cls.doors = defaultdict(set)
        for i, s in enumerate(cls.sectors):
            if s.get("id") and s["heightceiling"] == s["heightfloor"]:
                cls.doors[s["id"]].add(i)
        cls.doors = dict(cls.doors)
        cls.door_sectors = set().union(*cls.doors.values())
        cls.zone_of = {index: name for name, index in cls.plan.items()}
        cls.start = cls.plan["z1_dorm"]
        cls.neighbours = defaultdict(set)
        for ld in cls.lines:
            if "sideback" in ld:
                a = cls.sides[ld["sidefront"]]["sector"]
                b = cls.sides[ld["sideback"]]["sector"]
                cls.neighbours[a].add(b)
                cls.neighbours[b].add(a)

    # --- the model --------------------------------------------------------
    def _heights(self, open_tags):
        """Floor/ceiling of every sector with `open_tags`' doors risen.

        ZDoom raises a door to (lowest neighbouring ceiling - 4).
        """
        out = []
        for i, s in enumerate(self.sectors):
            ceiling = s["heightceiling"]
            if s.get("id") in open_tags and i in self.door_sectors:
                ceiling = min(self.sectors[n]["heightceiling"] for n in self.neighbours[i]) - 4
            out.append((s["heightfloor"], ceiling))
        return out

    def _reachable(self, open_tags):
        heights = self._heights(open_tags)
        adjacency = defaultdict(set)
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a = self.sides[ld["sidefront"]]["sector"]
            b = self.sides[ld["sideback"]]["sector"]
            for src, dst in ((a, b), (b, a)):
                (fs, fc), (ts, tc) = heights[src], heights[dst]
                if min(fc, tc) - max(fs, ts) < PLAYER_HEIGHT:
                    continue          # cannot fit through the gap
                if ts - fs > MAX_STEP_UP:
                    continue          # cannot climb it; dropping down is free
                adjacency[src].add(dst)
        seen = {self.start}
        stack = [self.start]
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen, adjacency

    # --- structure --------------------------------------------------------
    def test_no_duplicate_vertices(self):
        points = [(v["x"], v["y"]) for v in self.blocks["vertex"]]
        self.assertEqual(len(points), len(set(points)))

    def test_no_degenerate_or_duplicate_linedefs(self):
        seen = set()
        for i, ld in enumerate(self.lines):
            self.assertNotEqual(ld["v1"], ld["v2"], f"linedef {i} has zero length")
            key = frozenset((ld["v1"], ld["v2"]))
            self.assertNotIn(key, seen, f"linedef {i} duplicates another")
            seen.add(key)

    def test_every_sector_is_closed_and_clockwise(self):
        loops = sector_loops(self.blocks)
        for index in range(len(self.sectors)):
            edges = loops.get(index)
            self.assertTrue(edges, f"sector {index} has no sides")
            out_deg: dict[int, int] = defaultdict(int)
            in_deg: dict[int, int] = defaultdict(int)
            for a, b in edges:
                out_deg[a] += 1
                in_deg[b] += 1
            for vertex in set(out_deg) | set(in_deg):
                self.assertEqual(out_deg[vertex], in_deg[vertex],
                                 f"sector {index} leaks at vertex {vertex}")
            self.assertLess(signed_area(self.blocks, edges), 0, f"sector {index}")

    def test_sidedness_flags_match_the_geometry(self):
        for i, ld in enumerate(self.lines):
            if "sideback" in ld:
                self.assertTrue(ld.get("twosided"), f"linedef {i}")
                self.assertFalse(ld.get("blocking"), f"linedef {i} blocks a passage")
            else:
                self.assertTrue(ld.get("blocking"), f"linedef {i} is a one-sided gap")

    # --- the v1 contract --------------------------------------------------
    def test_every_texture_name_is_an_approved_one(self):
        """Criterion G3-3, statically: no IWAD texture survives v1.

        The two tuples at the foot of `map.py` are the map's whole material
        list, and every one of them is a lump of the approved "Soviet base"
        batch in docs/art/TEXTURE-INDEX.md. A typo here is an `Unknown
        texture` in the engine log, which is criterion G3-2.
        """
        m = self.map01
        for i, s in enumerate(self.sectors):
            self.assertIn(s["texturefloor"], m.FLAT_TEXTURES, f"sector {i} floor")
            self.assertIn(s["textureceiling"], m.FLAT_TEXTURES, f"sector {i} ceiling")
        for i, side in enumerate(self.sides):
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                self.assertIn(side[key], m.WALL_TEXTURES + ("-",), f"sidedef {i} {key}")

    # --- the v2 light (design section 6 table, section 16) ---------------
    def test_every_light_is_in_the_designed_range(self):
        m = self.map01
        for i, s in enumerate(self.sectors):
            self.assertGreaterEqual(s["lightlevel"], m.LIGHT_MIN, self.zone_of.get(i))
            self.assertLessEqual(s["lightlevel"], m.LIGHT_MAX, self.zone_of.get(i))

    def test_the_light_table(self):
        """The values of design section 6 as pinned in v2, zone by zone."""
        m = self.map01
        wanted = {
            "z1_dorm": m.LIGHT_DORM, "z2_washroom": m.LIGHT_WASHROOM,
            "s1_locker": m.LIGHT_SECRET, "z3_corridor": m.LIGHT_CORRIDOR,
            "z4_komnata": m.LIGHT_KOMNATA, "z4_mural": m.LIGHT_MURAL,
            "z5_service": m.LIGHT_SERVICE, "z5_flicker": m.LIGHT_FLICKER,
            "z5b_guard": m.LIGHT_GUARD, "z6_hangar": m.LIGHT_HANGAR,
            "lane_b_cross": m.LIGHT_WEST_BAY, "lane_b_spur": m.LIGHT_WEST_BAY,
            "fuel_passage": m.LIGHT_BEACON, "fuel_window": m.LIGHT_BEACON,
            "z7_switch_alcove": m.LIGHT_SWITCH_READY,
            "z7_fuel_bay": m.LIGHT_FUEL_BAY, "s3_sump": m.LIGHT_SECRET,
            "z6b_catwalk": m.LIGHT_CATWALK, "z9_booth": m.LIGHT_BOOTH_DARK,
            "booth_window": m.LIGHT_BOOTH_LIT, "d4_recess": m.LIGHT_GATE_DEAD,
            "z8_airlock": m.LIGHT_AIRLOCK, "z10_exit": m.LIGHT_EXIT,
            "z10_exit_niche": m.LIGHT_EXIT_SWITCH,
        }
        found = {zone: self.sectors[self.plan[zone]]["lightlevel"] for zone in wanted}
        self.assertEqual(wanted, found)
        # The curve of section 6: brighter towards the hangar, then darker
        # towards the exit, and the exit room the darkest place on the route.
        self.assertLess(m.LIGHT_CORRIDOR, m.LIGHT_HANGAR)
        self.assertLess(m.LIGHT_EXIT, m.LIGHT_AIRLOCK)
        self.assertEqual(m.LIGHT_MIN, m.LIGHT_EXIT)

    def test_every_lamp_is_one_panel_exactly_one_step_over_its_room(self):
        m = self.map01
        lamps = [name for name in self.plan if name.startswith("lamp_")]
        self.assertEqual(24, len(lamps), "3 dorm, 2 corridor, 3 komnata, 1 service, "
                                         "11 hangar, 2 catwalk, 1 fuel bay, 1 airlock")
        verts = self.blocks["vertex"]
        for name in lamps:
            room = name[len("lamp_"):].rsplit("_", 1)[0]
            lamp, home = self.sectors[self.plan[name]], self.sectors[self.plan[room]]
            self.assertEqual(home["lightlevel"] + m.LAMP_STEP, lamp["lightlevel"], name)
            self.assertEqual(m.CEIL_LAMP, lamp["textureceiling"], name)
            self.assertEqual((home["heightfloor"], home["heightceiling"]),
                             (lamp["heightfloor"], lamp["heightceiling"]), name)
            # One 64x64 panel, and nothing around it but its own room.
            self.assertEqual({self.plan[room]}, self.neighbours[self.plan[name]], name)
            xs = {verts[ld[k]]["x"] for ld in self.lines for k in ("v1", "v2")
                  if self.plan[name] in self._sides_of(ld)}
            self.assertEqual(64, max(xs) - min(xs), name)

    def _sides_of(self, ld):
        out = {self.sides[ld["sidefront"]]["sector"]}
        if "sideback" in ld:
            out.add(self.sides[ld["sideback"]]["sector"])
        return out

    def test_192_is_kept_for_the_hangar_lamps_and_the_beacons(self):
        """The top value means "go here"; spent anywhere else it means nothing."""
        allowed = {"fuel_passage", "fuel_window", "d4"}
        for i, s in enumerate(self.sectors):
            if s["lightlevel"] == self.map01.LIGHT_MAX:
                name = self.zone_of[i]
                self.assertTrue(name in allowed or name.startswith("lamp_z6_hangar_"), name)

    def test_the_red_wall_leads_into_shadow_and_ends_in_light(self):
        """The v1 playtest, as light: the fuel-bay mouth must be the brightest
        floor on the hangar's west side, at the end of a darker strip."""
        m = self.map01
        mouth = self.sectors[self.plan["fuel_passage"]]["lightlevel"]
        for zone in ("lane_b_cross", "lane_b_spur", "z6_hangar", "z7_fuel_bay"):
            self.assertGreaterEqual(mouth - self.sectors[self.plan[zone]]["lightlevel"],
                                    m.LAMP_STEP, zone)
        self.assertGreaterEqual(mouth - m.LIGHT_WEST_BAY, 3 * m.LAMP_STEP)

    def test_one_flickering_section_in_the_service_corridor(self):
        flicker = [i for i, s in enumerate(self.sectors)
                   if s.get("special") == SECTOR_SPECIAL_LIGHT_FLICKER]
        self.assertEqual([self.plan["z5_flicker"]], flicker)
        # dLight_Flicker swings between the sector's own light and its
        # darkest neighbour's: there must be a swing worth seeing.
        own = self.sectors[flicker[0]]["lightlevel"]
        darkest = min(self.sectors[n]["lightlevel"] for n in self.neighbours[flicker[0]])
        self.assertGreaterEqual(own - darkest, 2 * self.map01.LAMP_STEP)

    def test_sw_a_turns_the_gate_and_the_booth_on(self):
        """Door_Open's light tag: as the door rises, each sector carrying the
        tag goes to the light of its BRIGHTEST neighbour (Boom's
        EV_LightTurnOnPartway, NOT VERIFIED in engine - design section 16).
        That rule, applied to the plan, is what the player is promised."""
        m = self.map01
        tagged = {i for i, s in enumerate(self.sectors)
                  if s.get("id") == m.TAG_LIGHT_GATE_POWER}
        self.assertEqual({self.plan["z7_switch_alcove"], self.plan["d4_recess"],
                          self.plan["z9_booth"]}, tagged)
        after = {i: max(self.sectors[n]["lightlevel"] for n in self.neighbours[i])
                 for i in tagged}
        recess, booth = self.plan["d4_recess"], self.plan["z9_booth"]
        alcove = self.plan["z7_switch_alcove"]
        # The switch's own lamp: before, the brightest spot in the bay; after,
        # a step brighter still - the change in front of the player's eyes.
        self.assertEqual(m.LIGHT_SWITCH_READY, self.sectors[alcove]["lightlevel"])
        self.assertGreater(m.LIGHT_SWITCH_READY, m.LIGHT_FUEL_BAY + 2 * m.LAMP_STEP)
        self.assertEqual(m.LIGHT_BEACON, after[alcove], "the switch's lamp does not come up")
        self.assertGreaterEqual(after[alcove] - m.LIGHT_SWITCH_READY, 2 * m.LAMP_STEP)
        self.assertEqual(m.LIGHT_GATE_DEAD, self.sectors[recess]["lightlevel"])
        self.assertEqual(m.LIGHT_BEACON, after[recess], "the gate does not light up")
        self.assertEqual(m.LIGHT_BOOTH_DARK, self.sectors[booth]["lightlevel"])
        self.assertEqual(m.LIGHT_BOOTH_LIT, after[booth], "the booth does not light up")
        # A change the eye cannot miss: at least five lamp steps on the gate.
        self.assertGreaterEqual(after[recess] - self.sectors[recess]["lightlevel"],
                                5 * m.LAMP_STEP)

    def test_the_three_secrets_are_flagged(self):
        flagged = {i for i, s in enumerate(self.sectors)
                   if s.get("special", 0) & SECTOR_SPECIAL_SECRET}
        self.assertEqual({self.plan["s1_locker"], self.plan["s2_closet"],
                          self.plan["s3_sump"]}, flagged)
        reachable, _ = self._reachable(set(self.doors))
        self.assertLessEqual(flagged, reachable, "a secret nobody can enter")

    def test_every_sector_survived_the_painter(self):
        """A rectangle painted over by a later one leaves a sector with no
        sides: it builds, it passes check_pk3, and it is invisible in game.
        D5's recess was exactly that until the lift room was painted first.
        """
        used = {side["sector"] for side in self.sides}
        missing = sorted(set(range(len(self.sectors))) - used)
        self.assertEqual([], missing, f"sectors painted out of existence: {missing}")

    def _seen_from(self, zone):
        """Every texture a player standing in `zone` can have drawn at him.

        That is the sidedefs BELONGING to the zone - and, by the painter's
        rule, a two-sided one of those wears the material of the sector
        across the line, because what it draws is that sector's structure:
        the flank of its raised floor, or the lintel under its lower
        ceiling.
        """
        index = self.plan[zone]
        out = set()
        for side in self.sides:
            if side["sector"] != index:
                continue
            out.update(v for k, v in side.items()
                       if k.startswith("texture") and v != "-")
        return out

    def test_a_raised_structure_shows_its_own_flank_to_the_room(self):
        """From the hangar floor the cradle and the catwalk must be plate.

        This is the rule that decides what a room is MADE of as opposed to
        what it is painted: the 128-unit face under the catwalk belongs to
        the catwalk, not to the concrete wall behind it, and it was grey in
        the first v1 build because the painter dressed it in the hangar's
        own material.
        """
        m = self.map01
        for island in ("z6a_cradle", "z6b_catwalk"):
            target = self.plan[island]
            faces = [self.sides[ld["sidefront"]]["texturebottom"]
                     for ld in self.lines
                     if "sideback" in ld
                     and self.sides[ld["sidefront"]]["sector"] == self.plan["z6_hangar"]
                     and self.sides[ld["sideback"]]["sector"] == target]
            self.assertTrue(faces, f"{island} does not touch the hangar floor")
            self.assertEqual({m.STEEL}, set(faces), f"{island}'s flank is not plate")

    def test_each_zone_is_made_of_what_the_design_says_it_is(self):
        m = self.map01
        self.assertIn(m.STEEL, self._seen_from("z7_fuel_bay"))
        self.assertIn(m.CONC, self._seen_from("z6_hangar"))
        self.assertIn(m.STRIPE, self._seen_from("fuel_passage"))

    def test_the_red_route_is_unbroken_from_the_barracks_to_the_fuel_bay(self):
        """The v0 playtest finding, as a test.

        The CEO could not find the way on from the hangar floor. The map's
        answer is a single marking the player has been following since the
        barracks: it must exist in EVERY zone of the route, and above all on
        the hangar's west wall and the lintel of the fuel-bay mouth, which
        are the two surfaces that have to carry him across the room nothing
        else explains.
        """
        m = self.map01
        for zone in ("z3_corridor", "z4_komnata", "z5_service",
                     "lane_b_cross", "lane_b_spur", "fuel_passage",
                     # ...and the hangar itself, where the only red is the
                     # frame around the shut gate and the lintel over the
                     # mouth that answers it.
                     "z6_hangar"):
            self.assertIn(m.STRIPE, self._seen_from(zone),
                          f"the red route does not reach {zone}")

    def test_the_yellow_lane_forks_at_the_foot_of_the_entry_stair(self):
        """Two ways on out of the hangar, both marked on the floor.

        Lane A runs east to the gate, lane B north-west to the fuel bay, and
        both touch the bottom step, so the fork is under the player's feet
        the moment he arrives instead of being something he has to find.
        """
        m = self.map01
        bottom_step = self.plan["step_down_3"]
        for lane in ("lane_a_spur", "lane_b_cross"):
            index = self.plan[lane]
            self.assertEqual(m.LANE, self.sectors[index]["texturefloor"])
            self.assertIn(bottom_step, self.neighbours[index],
                          f"{lane} does not start at the bottom step")
        # ...and each lane ends where it promises to.
        self.assertIn(self.plan["d4_recess"], self.neighbours[self.plan["lane_a_cross"]])
        self.assertIn(self.plan["fuel_passage"], self.neighbours[self.plan["lane_b_spur"]])

    def test_every_door_leaf_is_exactly_one_tile_of_the_door_texture(self):
        """`SDDOOR1` is 128x128 and tiles; a leaf taller than 128 reads as
        patterned wall, which is what sent the CEO for IDCLIP in v0. So no
        room that faces a door may be more than 128 above the door's floor -
        that is what every recess sector in the map is for.
        """
        m = self.map01
        for ld in self.lines:
            faces = [self.sides[ld["sidefront"]]]
            if "sideback" in ld:
                faces.append(self.sides[ld["sideback"]])
            if not any(f["texturetop"] == m.DOOR for f in faces):
                continue
            leaf = self.sides[ld["sidefront"]]["sector"]
            back = self.sides[ld["sideback"]]["sector"]
            door_floor = min(self.sectors[leaf]["heightfloor"],
                             self.sectors[back]["heightfloor"])
            for side in (leaf, back):
                height = self.sectors[side]["heightceiling"] - door_floor
                self.assertLessEqual(height, m.DOOR_LEAF_HEIGHT,
                                     f"sector {side} gives the leaf {height} units to fill")

    def test_the_pictures_fit_their_walls_exactly(self):
        """Each poster appears once, whole, with no offset. A 128x256 Lenin
        needs a 256-high room and a 128-long line; anything else crops him.
        """
        m = self.map01
        wanted = {m.PLAQUE: (128, 128), m.MURAL: (128, 128), m.LENIN: (128, 256)}
        verts = self.blocks["vertex"]
        found = {}
        for ld in self.lines:
            side = self.sides[ld["sidefront"]]
            if side["texturemiddle"] not in wanted:
                continue
            a, b = verts[ld["v1"]], verts[ld["v2"]]
            length = abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])
            sector = self.sectors[side["sector"]]
            height = sector["heightceiling"] - sector["heightfloor"]
            found[side["texturemiddle"]] = (length, height)
            self.assertTrue(ld.get("dontpegbottom"),
                            "a poster must be pegged to the floor or it drifts")
        self.assertEqual(wanted, found)

    # --- the switches (v1 playtest: "una puerta que no hace ningun ruido") --
    def _switch_lines(self):
        """Every one-sided line carrying a special: SW-A, SW-B and the exit."""
        return [ld for ld in self.lines if ld.get("special") and "sideback" not in ld]

    def test_every_switch_wears_a_real_switch_face(self):
        """The finding of the v1 walk: SW-A wore SDDOOR1, made no sound and
        did not change, so the CEO took it for a broken door. A switch is now
        a switch: one of the approved SDSW1x faces, one per switch, each its
        own variant, and no door leaf on any one-sided line at all."""
        m = self.map01
        self.assertFalse(hasattr(m, "SWITCH_PLACEHOLDER"), "the stand-in is back")
        faces = [self.sides[ld["sidefront"]]["texturemiddle"] for ld in self._switch_lines()]
        self.assertEqual(3, len(faces))
        self.assertEqual(sorted(m.SWITCH_FACES), sorted(faces))
        self.assertEqual(3, len(set(faces)), "two switches share a variant")
        for face in faces:
            self.assertRegex(face, r"^SDSW1[A-D]$")
            twin = PROJECT_ROOT / "assets" / "textures" / "soviet_base" / f"SDSW2{face[-1]}.png"
            self.assertTrue(twin.is_file(), f"{face} has no ON face to flip to")
        for i, ld in enumerate(self.lines):
            if "sideback" not in ld:
                self.assertNotEqual(m.DOOR, self.sides[ld["sidefront"]]["texturemiddle"],
                                    f"linedef {i}: SDDOOR1 on a wall is a door that never opens")

    def test_every_switch_face_appears_once_whole(self):
        """64 of line on 128 of wall: the face is drawn once, never tiled -
        v1's SW-A tiled one and a half times on a 192 wall."""
        m = self.map01
        verts = self.blocks["vertex"]
        for ld in self._switch_lines():
            a, b = verts[ld["v1"]], verts[ld["v2"]]
            length = abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])
            sector = self.sectors[self.sides[ld["sidefront"]]["sector"]]
            self.assertEqual(m.SWITCH_WIDTH, length)
            self.assertEqual(m.SWITCH_HEIGHT, sector["heightceiling"] - sector["heightfloor"])

    def test_sw_a_opens_d4_and_stays_on(self):
        """SW-A's tag is D4's, its light tag is the gate's power light, and it
        is one-shot so its face stays on SDSW2A instead of popping back."""
        m = self.map01
        sw_a = [ld for ld in self._switch_lines() if ld.get("special") == SPECIAL_DOOR_OPEN
                and ld["arg0"] == m.TAG_D4_HANGAR_AIRLOCK]
        self.assertEqual(1, len(sw_a))
        sw_a = sw_a[0]
        self.assertEqual(m.SW_A_FACE, self.sides[sw_a["sidefront"]]["texturemiddle"])
        self.assertIn(self.plan["d4"], self.doors[sw_a["arg0"]], "SW-A's tag is not D4's")
        self.assertEqual(m.TAG_LIGHT_GATE_POWER, sw_a["arg2"])
        self.assertTrue(sw_a["playeruse"])
        self.assertNotIn("repeatspecial", sw_a)

    def test_the_marker_texture_is_only_on_pressable_surfaces(self):
        """`SDDOOR1` must never leak onto a wall.

        Every sidedef wearing it belongs either to a line with a use-special
        (a switch, a manual door, a secret panel) or to one of the two leaves
        a switch opens remotely. Anywhere else it would be a lie about what
        the player can press.
        """
        m = self.map01
        remote = {self.plan["d4"], self.plan["d5"]}
        for ld in self.lines:
            faces = [self.sides[ld["sidefront"]]]
            if "sideback" in ld:
                faces.append(self.sides[ld["sideback"]])
            marked = any(f[k] == m.PRESSABLE
                         for f in faces
                         for k in ("texturetop", "texturemiddle", "texturebottom"))
            if not marked:
                continue
            touches_remote = any(f["sector"] in remote for f in faces)
            self.assertTrue(ld.get("playeruse") or touches_remote,
                            "SDDOOR1 on a surface the player cannot press")

    def test_the_whole_plan_is_there(self):
        # Every room, stair, door and switch of the design's section 3 table.
        # The v3 sector count, and the density target it answers, are
        # tests/test_map01.py's. Here: the doors and the specials.
        self.assertEqual(9, len(self.doors), "6 door tags + 3 secret panels")
        self.assertEqual(9 + 6, len(self.door_sectors), "+ 6 monster-closet panels")
        specials = defaultdict(int)
        for ld in self.lines:
            if ld.get("special"):
                specials[ld["special"]] += 1
        self.assertEqual(8, specials[SPECIAL_DOOR_RAISE], "4 manual doors, 2 lines each")
        # 3 panels x 2 + SW-A + SW-B, plus 2: since v3 the drain that is S3's
        # clue runs up to S3's panel and splits its bay-side line in three
        # (bay / drain / bay), each piece carrying the panel's special.
        self.assertEqual(10, specials[SPECIAL_DOOR_OPEN], "3 panels x2 + SW-A + SW-B + 2")
        self.assertEqual(1, specials[SPECIAL_EXIT_NORMAL])

    def test_no_press_can_consume_a_gate(self):
        """Every door and panel line is repeatable. The two gate switches are
        one-shot on purpose (so they stay ON), which is safe only because
        what they fire is Door_Open: open and stay open, nothing closes it."""
        for i, ld in enumerate(self.lines):
            if ld.get("special") not in (SPECIAL_DOOR_RAISE, SPECIAL_DOOR_OPEN):
                continue
            self.assertTrue(ld.get("playeruse"), f"linedef {i}")
            if "sideback" in ld:
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
            else:
                self.assertEqual(SPECIAL_DOOR_OPEN, ld["special"],
                                 f"linedef {i}: a one-shot switch must open for good")

    def test_every_door_opens_tall_enough_to_walk_through(self):
        for index in sorted(self.door_sectors):
            tag = self.sectors[index]["id"]
            s = self.sectors[index]
            opened = min(self.sectors[n]["heightceiling"] for n in self.neighbours[index]) - 4
            clearance = opened - s["heightfloor"]
            self.assertGreaterEqual(clearance, PLAYER_HEIGHT,
                                    f"door tag {tag} only opens to {clearance} units")

    # --- no softlock (G3-6) ----------------------------------------------
    def test_every_sector_is_reachable_except_the_window(self):
        reachable, _ = self._reachable(set(self.doors))
        unreachable = set(range(len(self.sectors))) - reachable
        # The windows (a sill is a window, not a step; S2's slit), the crates
        # (64 and 128 high) and the furniture (32) are the sectors nobody is
        # meant to stand in. Anything else showing up here is a room the
        # player cannot get to.
        m = self.map01
        props = {i for name, i in self.plan.items()
                 if name in m.WINDOWS or name.startswith(m.PROP_PREFIXES)}
        self.assertEqual(3 + 9 + 13, len(props), "3 windows, 9 crates; 6 bunks, "
                                                 "3 tables, 3 basins and a lectern")
        self.assertEqual(props, unreachable,
                         f"unexpected: {sorted(self.zone_of[i] for i in unreachable ^ props)}")

    def test_nothing_is_a_one_way_trap(self):
        reachable, adjacency = self._reachable(set(self.doors))
        reverse = defaultdict(set)
        for src, dsts in adjacency.items():
            for dst in dsts:
                reverse[dst].add(src)
        seen = {self.start}
        stack = [self.start]
        while stack:
            for nxt in reverse[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        stranded = sorted(reachable - seen)
        self.assertEqual([], stranded, f"no way back to the start from {stranded}")

    def test_the_gate_order_is_the_designed_one(self):
        m = self.map01
        manual = {m.TAG_D1_DORM_WASHROOM, m.TAG_D2_DORM_CORRIDOR,
                  m.TAG_D3_KOMNATA_SERVICE, m.TAG_D6_CATWALK_BOOTH,
                  m.TAG_S1_LOCKER_PANEL, m.TAG_S2_CATWALK_PANEL, m.TAG_S3_SUMP_PANEL}
        sealed, _ = self._reachable(set())
        dorm = {self.plan[n] for n in ("z1_dorm", "lamp_z1_dorm_1", "lamp_z1_dorm_2",
                                       "lamp_z1_dorm_3", "shovel_rack", "frame_d1_dorm",
                                       "frame_d2_dorm")}
        self.assertEqual(dorm, sealed, "the dorm must be sealed by D1 and D2")

        before_switches, _ = self._reachable(manual)
        after_sw_a, _ = self._reachable(manual | {m.TAG_D4_HANGAR_AIRLOCK})
        after_sw_b, _ = self._reachable(manual | {m.TAG_D4_HANGAR_AIRLOCK,
                                                  m.TAG_D5_AIRLOCK_EXIT})

        # SW-A and SW-B are both reachable without any switch being thrown:
        # the design's rule is that the locked thing is always seen first.
        self.assertLess(len(before_switches), len(after_sw_a))
        self.assertLess(len(after_sw_a), len(after_sw_b))
        # D4 and the airlock arrive with SW-A - and, since v3, the three
        # fuel-bay closets its press springs; D5, its recess and the lift
        # with SW-B, and the three hangar closets of wave 2. Both recesses
        # on the hangar side are open ground and are therefore already in
        # `before_switches`: the gate is SEEN long before it is opened.
        def named(*names):
            return {self.plan[n] for n in names}
        closets = lambda *ids: named(*(f"closet_{c}{s}" for c in ids for s in ("", "_door")))
        self.assertEqual(named("d4", "z8_airlock", "lamp_z8_airlock_1", "airlock_niche_n",
                               "airlock_niche_s", "frame_d5_airlock") | closets("a1", "a2", "a3"),
                         after_sw_a - before_switches)
        self.assertEqual(named("d5", "d5_recess", "z10_exit", "z10_exit_niche", "z10_lift",
                               "lenin_halo", "lenin_light") | closets("w1", "w2", "e1"),
                         after_sw_b - after_sw_a)
        self.assertIn(self.plan["d4_recess"], before_switches,
                      "the shut gate must be walked up to before SW-A is found")

    def test_the_exit_is_reachable_and_in_the_lift_room(self):
        reachable, _ = self._reachable(set(self.doors))
        exits = [ld for ld in self.lines if ld.get("special") == SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_sector = self.sides[exits[0]["sidefront"]]["sector"]
        self.assertEqual(self.plan["z10_exit_niche"], exit_sector,
                         "the exit switch must be in its niche in the lift room")
        self.assertEqual({self.plan["z10_exit"]}, self.neighbours[exit_sector])
        self.assertIn(exit_sector, reachable, "the exit switch cannot be reached")
        self.assertNotIn("sideback", exits[0], "the exit switch is a one-sided wall")

    def test_the_two_switches_are_in_the_rooms_the_design_puts_them_in(self):
        m = self.map01
        # SW-A is in its alcove, which opens only into the fuel bay (and
        # through a window onto the hangar): the player still has to go IN.
        wanted = {
            m.TAG_D4_HANGAR_AIRLOCK: self.plan["z7_switch_alcove"],   # SW-A
            m.TAG_D5_AIRLOCK_EXIT: self.plan["z9_booth"],             # SW-B
        }
        walkable = {n for n in self.neighbours[self.plan["z7_switch_alcove"]]
                    if self.zone_of[n] not in m.WINDOWS}
        self.assertEqual({self.plan["z7_fuel_bay"]}, walkable)
        found = {}
        for ld in self.lines:
            if ld.get("special") == SPECIAL_DOOR_OPEN and "sideback" not in ld:
                found[ld["arg0"]] = self.sides[ld["sidefront"]]["sector"]
        self.assertEqual(wanted, found)

    # --- sight lines: the v1 playtest's answer, measured --------------------
    def _blockers(self, eye, eye_z, target, target_z):
        """The linedefs that stop a line of sight, Doom-style.

        A one-sided line always blocks. A two-sided line blocks unless the
        ray, at the height it has where it crosses, passes through the gap
        between the higher of the two floors and the lower of the two
        ceilings (a closed door has no gap). Returns the zone names on the
        blocking lines, empty when the target is in view.
        """
        verts = self.blocks["vertex"]
        (px, py), (tx, ty) = eye, target
        dx, dy = tx - px, ty - py
        out = []
        for ld in self.lines:
            a, b = verts[ld["v1"]], verts[ld["v2"]]
            ex, ey = b["x"] - a["x"], b["y"] - a["y"]
            denom = dx * ey - dy * ex
            if denom == 0:
                continue
            t = ((a["x"] - px) * ey - (a["y"] - py) * ex) / denom
            u = ((a["x"] - px) * dy - (a["y"] - py) * dx) / denom
            if not (0 < t < 1 and 0 <= u <= 1):
                continue
            names = sorted(self.zone_of[s] for s in self._sides_of(ld))
            if "sideback" not in ld:
                out.append(names)
                continue
            f = self.sectors[self.sides[ld["sidefront"]]["sector"]]
            k = self.sectors[self.sides[ld["sideback"]]["sector"]]
            z = eye_z + t * (target_z - eye_z)
            if not (max(f["heightfloor"], k["heightfloor"]) < z
                    < min(f["heightceiling"], k["heightceiling"])):
                out.append(names)
        return out

    def _eye(self, zone):
        return self.sectors[self.plan[zone]]["heightfloor"] + VIEW_HEIGHT

    def test_from_sw_a_the_player_sees_d4(self):
        """Standing within reach of SW-A, the player sees the gate it opens:
        through the alcove's window, over the cradle, into D4's recess. Three
        heights on the leaf, from the middle to the top of the door."""
        m = self.map01
        eye = (1416, 1624)    # in the alcove, 56 from SW-A's line (x 1472)
        self.assertLessEqual(1472 - eye[0], USE_RANGE)
        leaf_x = 2680         # just in front of D4's leaf, inside the recess
        for y in (608, 672, 736):
            for z in (40, 64, 88):
                self.assertEqual([], self._blockers(eye, self._eye("z7_switch_alcove"),
                                                    (leaf_x, y), z),
                                 f"D4 at y {y}, z {z} is hidden from SW-A")
        # Before SW-A, D4 is shut: the same line aimed THROUGH the leaf into
        # the airlock is blocked by it - the player sees a door, not a room.
        self.assertTrue(self._blockers(eye, self._eye("z7_switch_alcove"), (2800, 672), 40))
        self.assertEqual(m.TAG_D4_HANGAR_AIRLOCK, self.sectors[self.plan["d4"]]["id"])

    def test_from_the_hangar_the_player_sees_the_switch(self):
        """Walking up the red wall, or standing on the bottom step, the lit
        switch shows through the window beside the mouth."""
        face = (1470, 1632)   # on SW-A's face, 2 units in front of it
        floor = self.sectors[self.plan["z7_switch_alcove"]]["heightfloor"]
        for zone, eye in (("lane_b_spur", (1216, 1400)),
                          ("lane_b_cross", (1300, 1300)),
                          ("step_down_3", (1336, 1152))):
            for z in (floor + 64, floor + 96, floor + 120):
                self.assertEqual([], self._blockers(eye, self._eye(zone), face, z),
                                 f"SW-A at z {z} is hidden from {zone}")

    def test_from_the_bottom_step_the_player_sees_into_the_mouth(self):
        """The v0 and v1 finding, kept as a sight line: from the bottom of
        the entry stair the fuel-bay mouth is in plain view."""
        for target in ((1184, 1640), (1248, 1640), (1216, 1700)):
            self.assertEqual([], self._blockers((1336, 1152), self._eye("step_down_3"),
                                                target, 40))

    # --- props ----------------------------------------------------------------
    def test_every_crate_face_is_whole_crates(self):
        """A crate side wears the face that fits its length - SDCRAT2 on 128,
        SDCRAT1 on 64 - its height is whole crates, and its lid is SDCRTOP1.
        Faces are not floor-pegged, so they hang from the crate's top edge
        and a crate under a low ceiling (the guard post) is not cut."""
        m = self.map01
        verts = self.blocks["vertex"]
        crates = {i for name, i in self.plan.items() if name.startswith(m.PROP_PREFIX)}
        faces = 0
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            sides = [self.sides[ld["sidefront"]], self.sides[ld["sideback"]]]
            low, high = sorted(sides, key=lambda sd: self.sectors[sd["sector"]]["heightfloor"])
            if high["sector"] not in crates:
                continue
            faces += 1
            a, b = verts[ld["v1"]], verts[ld["v2"]]
            length = abs(a["x"] - b["x"]) + abs(a["y"] - b["y"])
            rise = (self.sectors[high["sector"]]["heightfloor"]
                    - self.sectors[low["sector"]]["heightfloor"])
            self.assertEqual({64: m.CRATE_FACE, 128: m.CRATE_LONG}[length],
                             low["texturebottom"])
            self.assertEqual(0, rise % 64, "a crate face that is not whole crates")
            self.assertNotIn("dontpegbottom", ld)
        self.assertEqual(1 + 4 + 3 + 4 + 4 + 4 + 3 * 4, faces, "v2's six + v3's three singles")
        for i in crates:
            self.assertEqual(m.CRATE_TOP, self.sectors[i]["texturefloor"])

    def test_the_dorm_lockers_stand_on_a_wall_their_own_height(self):
        m = self.map01
        verts = self.blocks["vertex"]
        lockers = [ld for ld in self.lines
                   if self.sides[ld["sidefront"]]["texturemiddle"] == m.LOCKER]
        self.assertEqual(1, len(lockers))
        side = self.sides[lockers[0]["sidefront"]]
        self.assertEqual(self.plan["z1_dorm"], side["sector"])
        dorm = self.sectors[side["sector"]]
        self.assertEqual(128, dorm["heightceiling"] - dorm["heightfloor"])
        a, b = verts[lockers[0]["v1"]], verts[lockers[0]["v2"]]
        self.assertEqual(0, (abs(a["y"] - b["y"]) + abs(a["x"] - b["x"])) % 64)

    def test_switch_targets_exist(self):
        """Every tag a switch names must be a sector that exists."""
        tags = {s["id"] for s in self.sectors if s.get("id")}
        for ld in self.lines:
            if ld.get("special") in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE):
                self.assertIn(ld["arg0"], tags, f"special targets unknown tag {ld['arg0']}")


if __name__ == "__main__":
    unittest.main()
