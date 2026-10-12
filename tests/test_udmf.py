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
    switch_door_open_style,
)

WALL = "STARTAN2"
FLOOR = "FLOOR4_8"
CEILING = "CEIL3_5"

# Doom player metrics; the numbers the reachability model is built on.
MAX_STEP_UP = 24     # the tallest floor change a player walks up unaided
PLAYER_HEIGHT = 56   # the shortest gap a player fits through


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
        cls.doors = {s["id"]: i for i, s in enumerate(cls.sectors) if s.get("id")}
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
            if s.get("id") in open_tags:
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

    # --- the v0 contract --------------------------------------------------
    def test_v0_is_one_texture_and_flat_light(self):
        m = self.map01
        for s in self.sectors:
            self.assertEqual(m.FLOOR, s["texturefloor"])
            self.assertEqual(m.CEILING, s["textureceiling"])
            self.assertEqual(m.LIGHT, s["lightlevel"])
        for side in self.sides:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                self.assertIn(side[key], (m.WALL, m.PRESSABLE, "-"))

    def test_the_marker_texture_is_only_on_pressable_surfaces(self):
        """`SDDOOR1` is the v0 exception; it must never leak onto a wall.

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

    def test_only_thing_is_the_player_start(self):
        things = self.blocks["thing"]
        self.assertEqual(1, len(things), "v0 has no enemies and no items")
        self.assertEqual(self.map01.ED_PLAYER1_START, things[0]["type"])
        for flag in ("skill1", "skill2", "skill3", "skill4", "skill5", "single", "coop", "dm"):
            self.assertTrue(things[0][flag])

    def test_the_whole_plan_is_there(self):
        # Every room, stair, door and switch of the design's section 3 table.
        self.assertEqual(44, len(self.sectors))
        self.assertEqual(9, len(self.doors), "6 doors + 3 secret panels")
        specials = defaultdict(int)
        for ld in self.lines:
            if ld.get("special"):
                specials[ld["special"]] += 1
        self.assertEqual(8, specials[SPECIAL_DOOR_RAISE], "4 manual doors, 2 lines each")
        self.assertEqual(8, specials[SPECIAL_DOOR_OPEN], "3 panels x2 + SW-A + SW-B")
        self.assertEqual(1, specials[SPECIAL_EXIT_NORMAL])

    def test_every_switch_and_door_line_is_repeatable(self):
        """A mis-timed or repeated press can never consume a gate."""
        for i, ld in enumerate(self.lines):
            if ld.get("special") in (SPECIAL_DOOR_RAISE, SPECIAL_DOOR_OPEN):
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
                self.assertTrue(ld.get("playeruse"), f"linedef {i}")

    def test_every_door_opens_tall_enough_to_walk_through(self):
        for tag, index in self.doors.items():
            s = self.sectors[index]
            opened = min(self.sectors[n]["heightceiling"] for n in self.neighbours[index]) - 4
            clearance = opened - s["heightfloor"]
            self.assertGreaterEqual(clearance, PLAYER_HEIGHT,
                                    f"door tag {tag} only opens to {clearance} units")

    # --- no softlock (G3-6) ----------------------------------------------
    def test_every_sector_is_reachable_except_the_window(self):
        reachable, _ = self._reachable(set(self.doors))
        unreachable = set(range(len(self.sectors))) - reachable
        # The booth window is a window: its sill is 32 above the booth floor,
        # so no player can climb into it. It is the single sector of MAP01
        # nobody can stand in, and that is deliberate - anything else showing
        # up here is a room the player cannot get to.
        self.assertEqual({self.plan["booth_window"]}, unreachable,
                         f"unexpected unreachable sectors: {sorted(unreachable)}")

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
        self.assertEqual({self.start}, sealed, "the dorm must be sealed by D1 and D2")

        before_switches, _ = self._reachable(manual)
        after_sw_a, _ = self._reachable(manual | {m.TAG_D4_HANGAR_AIRLOCK})
        after_sw_b, _ = self._reachable(manual | {m.TAG_D4_HANGAR_AIRLOCK,
                                                  m.TAG_D5_AIRLOCK_EXIT})

        # SW-A and SW-B are both reachable without any switch being thrown:
        # the design's rule is that the locked thing is always seen first.
        self.assertLess(len(before_switches), len(after_sw_a))
        self.assertLess(len(after_sw_a), len(after_sw_b))
        # D4 and the airlock arrive with SW-A; D5 and the lift with SW-B.
        self.assertEqual(2, len(after_sw_a - before_switches))
        self.assertEqual(2, len(after_sw_b - after_sw_a))

    def test_the_exit_is_reachable_and_in_the_lift_room(self):
        reachable, _ = self._reachable(set(self.doors))
        exits = [ld for ld in self.lines if ld.get("special") == SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_sector = self.sides[exits[0]["sidefront"]]["sector"]
        self.assertEqual(self.plan["z10_exit"], exit_sector,
                         "the exit switch must be on a wall of the lift room")
        self.assertIn(exit_sector, reachable, "the exit switch cannot be reached")
        self.assertNotIn("sideback", exits[0], "the exit switch is a one-sided wall")

    def test_the_two_switches_are_in_the_rooms_the_design_puts_them_in(self):
        m = self.map01
        wanted = {
            m.TAG_D4_HANGAR_AIRLOCK: self.plan["z7_fuel_bay"],   # SW-A
            m.TAG_D5_AIRLOCK_EXIT: self.plan["z9_booth"],        # SW-B
        }
        found = {}
        for ld in self.lines:
            if ld.get("special") == SPECIAL_DOOR_OPEN and "sideback" not in ld:
                found[ld["arg0"]] = self.sides[ld["sidefront"]]["sector"]
        self.assertEqual(wanted, found)

    def test_switch_targets_exist(self):
        """Every tag a switch names must be a sector that exists."""
        tags = {s["id"] for s in self.sectors if s.get("id")}
        for ld in self.lines:
            if ld.get("special") in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE):
                self.assertIn(ld["arg0"], tags, f"special targets unknown tag {ld['arg0']}")


if __name__ == "__main__":
    unittest.main()
