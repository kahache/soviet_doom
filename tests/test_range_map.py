"""The practice range for players: map RANGE, MAP02 until D62 (D41; design
docs/levels/RANGE-practice-range.md).

Owner: `level-designer`. `tests/test_practice_range.py` (`mod-engineer`'s)
pins how the range is reached and left in MAPINFO and MENUDEF; this file
pins the map itself, read back from the generated TEXTMAP like
`tests/test_map01.py`:

* the exit: one Exit_Normal switch, pressed (not walked over), reached
  from the start with no door opened, wearing MAP01's exit face whole;
* the bestiary gallery, reachable on foot through one manual door that
  opens from both rooms; sealed while that door is shut;
* no softlock: every sector reached, and a way back from each;
* every pickup and every enemy on floor the player can reach;
* the gallery stays blind to the hall even with the door open (an
  `ambush` monster that hears a shot still wakes if it sees the shooter),
  and its row faces away from where the player comes in;
* M2d: every texture and flat is our own packed lump, none an IWAD name
  (the M2 audit's check, also run against freedoom2.wad where present).

Run:  python3 -m unittest tests.test_range_map -v
"""

from __future__ import annotations

import importlib.util
import math
import struct
import sys
import unittest
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import check_pk3  # noqa: E402
import test_udmf as udmf_tests  # noqa: E402  (as a module: see test_map01)

parse_textmap = udmf_tests.parse_textmap
MAX_STEP_UP = udmf_tests.MAX_STEP_UP
PLAYER_HEIGHT = udmf_tests.PLAYER_HEIGHT
USE_RANGE = udmf_tests.USE_RANGE
SPECIAL_DOOR_RAISE = udmf_tests.SPECIAL_DOOR_RAISE
SPECIAL_EXIT_NORMAL = udmf_tests.SPECIAL_EXIT_NORMAL
PLAYER_RADIUS = 16
DOOR_GAP = 4              # Door_Raise stops 4 under the lowest neighbouring ceiling
# Heights a monster's eye and a player's body are sampled at for the sight
# test: from a hound's low eye to over a General's head, and from a
# player's knee to over his head.
EYE_HEIGHTS = (32, 48, 72, 96)
BODY_HEIGHTS = (8, 32, 56)
HALL_SAMPLE = 64          # the hall is sampled on this grid for the sight test
RANGE_SOURCE = PROJECT_ROOT / "src" / "maps" / "RANGE" / "map.py"
ASSETS = PROJECT_ROOT / "assets"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
FREEDOOM = PROJECT_ROOT / "iwads" / "freedoom2.wad"
WAD_HEADER = struct.Struct("<4sii")
WAD_ENTRY = struct.Struct("<ii8s")
MAPTEXTURE_NAME = 8       # a TEXTURE1 entry starts with its 8-byte name


def _lump_name(raw: bytes) -> str:
    return raw.split(b"\0", 1)[0].decode("ascii", "replace").upper()


def _iwad_names(blob: bytes) -> tuple[set[str], set[str]]:
    """({TEXTURE1/TEXTURE2 names}, {flats between F_START and F_END}) of an
    IWAD, read the way the M2 audit read freedoom2.wad."""
    _, count, table = WAD_HEADER.unpack_from(blob, 0)
    walls: set[str] = set()
    flats: set[str] = set()
    in_flats = False
    for i in range(count):
        pos, size, raw = WAD_ENTRY.unpack_from(blob, table + i * WAD_ENTRY.size)
        name = _lump_name(raw)
        if name in ("TEXTURE1", "TEXTURE2"):
            (n,) = struct.unpack_from("<i", blob, pos)
            for k in range(n):
                (off,) = struct.unpack_from("<i", blob, pos + 4 + 4 * k)
                walls.add(_lump_name(blob[pos + off:pos + off + MAPTEXTURE_NAME]))
        elif name in ("F_START", "FF_START"):
            in_flats = True
        elif name in ("F_END", "FF_END"):
            in_flats = False
        elif in_flats and size:
            flats.add(name)
    return walls, flats


def _load_range():
    spec = importlib.util.spec_from_file_location("sdmap_RANGE_test", RANGE_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RangeMapTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_range()
        textmap, cls.plan = cls.m.build_plan()
        blocks = parse_textmap(textmap.render())
        cls.sectors = blocks["sector"]
        cls.lines = blocks["linedef"]
        cls.sides = blocks["sidedef"]
        cls.verts = blocks["vertex"]
        cls.things = blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.doors = {i for i, s in enumerate(cls.sectors)
                     if s.get("id") and s["heightceiling"] == s["heightfloor"]}
        cls.neighbours = defaultdict(set)
        for ld in cls.lines:
            if "sideback" in ld:
                a, b = cls.sector_of(ld, "sidefront"), cls.sector_of(ld, "sideback")
                cls.neighbours[a].add(b)
                cls.neighbours[b].add(a)
        start = [t for t in cls.things if t["type"] == cls.m.ED_PLAYER1_START]
        assert len(start) == 1, "RANGE needs exactly one player start"
        cls.start_thing = start[0]
        cls.start = cls.sector_at(start[0]["x"], start[0]["y"])

    # --- helpers ----------------------------------------------------------
    @classmethod
    def sector_of(cls, ld, side):
        return cls.sides[ld[side]]["sector"]

    @classmethod
    def sector_at(cls, x, y):
        """The engine's way: the nearest vertical line east of the point."""
        y = y + 0.25
        best = None
        for ld in cls.lines:
            a, b = cls.verts[ld["v1"]], cls.verts[ld["v2"]]
            if a["x"] != b["x"] or a["x"] <= x or not (min(a["y"], b["y"]) < y < max(a["y"], b["y"])):
                continue
            if best is None or a["x"] < best[0]:
                best = (a["x"], a["y"], b["y"], ld)
        if best is None:
            return None
        _, y1, y2, ld = best
        if y2 < y1:
            return cls.sector_of(ld, "sidefront")
        return cls.sector_of(ld, "sideback") if "sideback" in ld else None

    def heights(self, open_doors):
        out = []
        for i, s in enumerate(self.sectors):
            ceiling = s["heightceiling"]
            if i in open_doors:
                ceiling = min(self.sectors[n]["heightceiling"] for n in self.neighbours[i]) - DOOR_GAP
            out.append((s["heightfloor"], ceiling))
        return out

    def reachable(self, open_doors):
        heights = self.heights(open_doors)
        adjacency = defaultdict(set)
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a, b = self.sector_of(ld, "sidefront"), self.sector_of(ld, "sideback")
            for src, dst in ((a, b), (b, a)):
                (fs, fc), (ts, tc) = heights[src], heights[dst]
                if min(fc, tc) - max(fs, ts) >= PLAYER_HEIGHT and ts - fs <= MAX_STEP_UP:
                    adjacency[src].add(dst)
        seen, stack = {self.start}, [self.start]
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen, adjacency

    def progression(self):
        """Open every door whose line the player can stand at, until nothing
        new opens. Returns the doors opened and the sectors reached."""
        opened = set()
        while True:
            reach, _ = self.reachable(opened)
            more = set()
            for ld in self.lines:
                if not (ld.get("playeruse") and ld.get("special") == SPECIAL_DOOR_RAISE):
                    continue
                stand = {self.sector_of(ld, "sidefront")}
                if "sideback" in ld:
                    stand.add(self.sector_of(ld, "sideback"))
                if stand & reach:
                    more |= {d for d in self.doors if self.sectors[d]["id"] == ld["arg0"]}
            if more <= opened:
                return opened, reach
            opened |= more

    def exit_lines(self):
        return [ld for ld in self.lines if ld.get("special") == SPECIAL_EXIT_NORMAL]

    def line_length(self, ld):
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        return math.hypot(b["x"] - a["x"], b["y"] - a["y"])

    def blockers(self, eye, eye_z, target, target_z, heights):
        """The lines that stop a line of sight (the method of test_udmf)."""
        (px, py), (tx, ty) = eye, target
        dx, dy = tx - px, ty - py
        out = []
        for ld in self.lines:
            a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
            ex, ey = b["x"] - a["x"], b["y"] - a["y"]
            denom = dx * ey - dy * ex
            if denom == 0:
                continue
            t = ((a["x"] - px) * ey - (a["y"] - py) * ex) / denom
            u = ((a["x"] - px) * dy - (a["y"] - py) * dx) / denom
            if not (0 < t < 1 and 0 <= u <= 1):
                continue
            if "sideback" not in ld:
                out.append(ld)
                continue
            (ff, fc), (kf, kc) = (heights[self.sector_of(ld, "sidefront")],
                                  heights[self.sector_of(ld, "sideback")])
            z = eye_z + t * (target_z - eye_z)
            if not (max(ff, kf) < z < min(fc, kc)):
                out.append(ld)
        return out

    # --- the exit -----------------------------------------------------------
    def test_one_exit_switch_reached_from_the_start_with_no_door(self):
        """D41: the range had no exit; the player left through the menu. Now
        one Exit_Normal line, pressed, not crossed (a range is not left by
        stepping in the wrong place), on a one-sided wall of a sector the
        player reaches from the start with every door shut."""
        exits = self.exit_lines()
        self.assertEqual(1, len(exits))
        ld = exits[0]
        self.assertTrue(ld.get("playeruse"))
        self.assertFalse(ld.get("playercross") or ld.get("impact") or ld.get("monsteruse"))
        self.assertNotIn("sideback", ld, "the exit switch is a wall, not a passage")
        sealed, _ = self.reachable(set())
        self.assertIn(self.sector_of(ld, "sidefront"), sealed)

    def test_the_exit_is_behind_the_player_start_and_within_a_short_walk(self):
        """Turn round and it is there: the switch's middle is within the
        hall's first stretch, on the start's row, and pressable from the
        hall without entering the alcove (the alcove is one press deep)."""
        ld = self.exit_lines()[0]
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        mid = ((a["x"] + b["x"]) / 2, (a["y"] + b["y"]) / 2)
        start = (self.start_thing["x"], self.start_thing["y"])
        self.assertEqual(start[1], mid[1], "the exit is not on the start's row")
        self.assertLess(mid[0], start[0], "the exit is not behind the start")
        hall_x1 = self.m.HALL[0]
        self.assertLessEqual(hall_x1 + PLAYER_RADIUS - mid[0], USE_RANGE,
                             "not pressable from the hall's edge")

    def test_the_exit_switch_wears_map01s_exit_face_whole(self):
        ld = self.exit_lines()[0]
        side = self.sides[ld["sidefront"]]
        self.assertEqual(self.m.EXIT_TEXTURE, side["texturemiddle"])
        self.assertEqual(self.m.SWITCH_WIDTH, self.line_length(ld))
        alcove = self.sectors[self.sector_of(ld, "sidefront")]
        self.assertEqual(self.m.SWITCH_HEIGHT, alcove["heightceiling"] - alcove["heightfloor"])
        hall = self.sectors[self.plan["hall"]]
        self.assertGreater(alcove["lightlevel"], hall["lightlevel"], "the way out is not lit")

    # --- the gallery, on foot ----------------------------------------------
    def test_the_gallery_is_reached_on_foot_through_its_door(self):
        """D41 v1: the gallery was connected to nothing (console only). With
        every door shut the player has the hall and the exit; opening what
        the map offers from there reaches every sector, the gallery too."""
        sealed, _ = self.reachable(set())
        self.assertEqual({self.plan["hall"], self.plan["exit_alcove"]}, sealed)
        opened, reach = self.progression()
        self.assertEqual({self.plan["gallery_door"]}, opened)
        self.assertEqual(set(range(len(self.sectors))), reach)

    def test_the_gallery_door_opens_from_both_rooms_and_closes_again(self):
        """Both faces carry Door_Raise on the door's tag, each wound with
        the door behind it (ZDoom fires a use special from the FRONT only),
        and the leaf is one SDDOOR1 tile wide."""
        door = self.plan["gallery_door"]
        faces = [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_RAISE]
        self.assertEqual(2, len(faces))
        rooms = set()
        for ld in faces:
            self.assertEqual(self.sectors[door]["id"], ld["arg0"])
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            self.assertEqual(door, self.sector_of(ld, "sideback"))
            rooms.add(self.sector_of(ld, "sidefront"))
            self.assertEqual(self.m.DOOR_TEXTURE, self.sides[ld["sidefront"]]["texturetop"])
            self.assertEqual(self.m.PASSAGE_WIDTH, self.line_length(ld))
        self.assertEqual({self.plan["hall"], self.plan["gallery_passage"]}, rooms)
        floor, ceiling = self.heights({door})[door]
        self.assertGreaterEqual(ceiling - floor, PLAYER_HEIGHT)

    def test_nothing_is_a_one_way_trap(self):
        opened, reach = self.progression()
        _, adjacency = self.reachable(opened)
        reverse = defaultdict(set)
        for src, dsts in adjacency.items():
            for dst in dsts:
                reverse[dst].add(src)
        back, stack = {self.start}, [self.start]
        while stack:
            for nxt in reverse[stack.pop()]:
                if nxt not in back:
                    back.add(nxt)
                    stack.append(nxt)
        self.assertEqual(set(), reach - back, "no way back to the start")

    def test_every_thing_stands_on_floor_the_player_reaches(self):
        """Every pickup, target and gallery enemy is in a reachable sector,
        never in the door; the bestiary row stays in the gallery."""
        _, reach = self.progression()
        for t in self.things:
            s = self.sector_at(t["x"], t["y"])
            where = f"thing {t['type']} at ({t['x']}, {t['y']})"
            self.assertIsNotNone(s, f"{where} is in a wall")
            self.assertIn(s, reach, where)
            self.assertNotIn(s, self.doors, where)
            if t["type"] in self.m.GALLERY_ROW:
                self.assertEqual(self.plan["gallery"], s, where)

    def test_the_passage_comes_out_behind_the_row(self):
        """The row faces the far wall and the passage's mouth is behind it,
        so a player walking in finds them asleep and chooses his first
        target; and the console's warp still lands at that mouth."""
        mouth_x1, _, mouth_x2, mouth_y = self.m.LEG_NORTH
        arrival = self.m.GALLERY_ARRIVAL
        self.assertEqual(self.plan["gallery"], self.sector_at(*arrival))
        self.assertTrue(mouth_x1 < arrival[0] < mouth_x2)
        for t in self.things:
            if t["type"] not in self.m.GALLERY_ROW:
                continue
            self.assertTrue(t.get("ambush"), t["type"])
            facing = math.radians(t["angle"])
            to_mouth = ((mouth_x1 + mouth_x2) / 2 - t["x"], mouth_y - t["y"])
            self.assertLess(math.cos(facing) * to_mouth[0] + math.sin(facing) * to_mouth[1], 0,
                            f"{t['type']} faces the passage")

    def test_the_gallery_cannot_see_into_the_hall_with_the_door_open(self):
        """The F5 gallery shared no line with the hall so that nothing fired
        there reached it. With a door, sound now does while the door is
        open; a deaf (`ambush`) monster that hears a shot still wakes if it
        can see the shooter, so the passage bends: from no gallery enemy's
        eye is any point of the hall in view, the door wide open."""
        heights = self.heights({self.plan["gallery_door"]})
        x1, y1, x2, y2 = self.m.HALL
        hall_points = [(x, y) for x in range(x1 + HALL_SAMPLE // 2, x2, HALL_SAMPLE)
                       for y in range(y1 + HALL_SAMPLE // 2, y2, HALL_SAMPLE)]
        # ...and the doorway itself, where a player stands to open it.
        dx1, dy1, dx2, _ = self.m.GALLERY_DOOR
        hall_points += [(x, dy1 - PLAYER_RADIUS) for x in range(dx1, dx2 + 1, 16)]
        for t in self.things:
            if t["type"] not in self.m.GALLERY_ROW:
                continue
            eye = (t["x"], t["y"])
            for target in hall_points:
                for ez in EYE_HEIGHTS:
                    for tz in BODY_HEIGHTS:
                        self.assertTrue(self.blockers(eye, ez, target, tz, heights),
                                        f"{t['type']} at {eye} sees the hall at {target}")

    # --- textures -----------------------------------------------------------
    def used_names(self):
        """({wall texture names}, {flat names}) the TEXTMAP actually wears."""
        walls = {side.get(k, "-") for side in self.sides
                 for k in ("texturetop", "texturemiddle", "texturebottom")} - {"-"}
        flats = ({s["texturefloor"] for s in self.sectors}
                 | {s["textureceiling"] for s in self.sectors})
        return walls, flats

    def test_every_name_is_in_the_maps_lists(self):
        walls, flats = self.used_names()
        self.assertLessEqual(walls, set(self.m.WALL_TEXTURES))
        self.assertLessEqual(flats, set(self.m.FLAT_TEXTURES))

    def test_no_iwad_texture_or_flat_every_name_is_ours(self):
        """M2d (the M2 audit's item A4, docs/qa/2026-10-14_2357_M2-freedoom-audit.md
        section 5): the range wore Freedoom's STARTAN2, FLOOR4_8 and CEIL3_5.
        Now every wall texture and flat it names is one of our own packed
        lumps under assets/, and none is an IWAD asset declared in MOD-SPEC
        section 5 (the list check_pk3 lets a map borrow from the IWAD)."""
        walls, flats = self.used_names()
        for name in sorted(walls):
            self.assertTrue(any(ASSETS.glob(f"textures/*/{name}.png")),
                            f"wall {name} is not in assets/textures/")
        for name in sorted(flats):
            self.assertTrue(any(ASSETS.glob(f"flats/*/{name}.png")),
                            f"flat {name} is not in assets/flats/")
        declared = check_pk3.iwad_assets_from_spec(MOD_SPEC)
        self.assertIn("STARTAN2", declared, "MOD-SPEC 5 was not read: the check below would be empty")
        self.assertEqual(set(), (walls | flats) & declared)

    def test_no_name_resolves_in_freedoom(self):
        """The audit's own check, against the IWAD itself: no wall texture
        the range names is in freedoom2.wad's TEXTURE1/TEXTURE2, and no flat
        lies between its F_START and F_END. iwads/ is never committed, so
        the test skips where the IWAD is absent (CI)."""
        if not FREEDOOM.is_file():
            self.skipTest("iwads/freedoom2.wad not present")
        iwad_walls, iwad_flats = _iwad_names(FREEDOOM.read_bytes())
        self.assertIn("STARTAN2", iwad_walls, "the IWAD's textures were not read")
        self.assertIn("FLOOR4_8", iwad_flats, "the IWAD's flats were not read")
        walls, flats = self.used_names()
        self.assertEqual(set(), walls & iwad_walls, "IWAD wall textures in RANGE")
        self.assertEqual(set(), flats & iwad_flats, "IWAD flats in RANGE")

    def test_room_walls_sit_on_the_64_grid(self):
        """Every one-sided room wall is offset so its 64-wide panels meet
        the map's 64 grid: a run that starts off it (the hall's west wall at
        y 416, north of the exit alcove) still ends on a whole panel in the
        corner. Every other face keeps offset 0 (the switch is seen whole)."""
        m = self.m
        for i, ld in enumerate(self.lines):
            for side_key in ("sidefront", "sideback"):
                if side_key not in ld:
                    continue
                side = self.sides[ld[side_key]]
                offset = side.get("offsetx", 0)
                if "sideback" in ld or side.get("texturemiddle") not in m.ALIGNED_TEXTURES:
                    self.assertEqual(0, offset, f"linedef {i} {side_key}")
                    continue
                a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
                along = a["x"] if a["y"] == b["y"] else a["y"]
                forward = (b["x"] - a["x"]) + (b["y"] - a["y"]) > 0
                start = (along if forward else -along) - offset
                self.assertEqual(0, start % m.PANEL_WIDTH, f"linedef {i} {side['texturemiddle']}")

    def test_the_signs_only_where_the_player_presses(self):
        """The door leaf and the exit switch, the faces MAP01 taught as
        "press here", appear only on the door and in the exit alcove, and
        the lamp panel lights only the exit. (SDSTEL1, the door's track, is
        also the passage's plate since M2d, as MAP01's airlock is steel.)"""
        m = self.m
        signs = {m.DOOR_TEXTURE, m.EXIT_TEXTURE}
        allowed = {self.plan["gallery_door"], self.plan["exit_alcove"]}
        lamps = {i for i, s in enumerate(self.sectors)
                 if m.LAMP_FLAT in (s["texturefloor"], s["textureceiling"])}
        self.assertEqual({self.plan["exit_alcove"]}, lamps)
        for ld in self.lines:
            touching = {self.sector_of(ld, "sidefront")}
            if "sideback" in ld:
                touching.add(self.sector_of(ld, "sideback"))
            for side_key in ("sidefront", "sideback"):
                if side_key not in ld:
                    continue
                side = self.sides[ld[side_key]]
                used = {side.get(k) for k in ("texturetop", "texturemiddle", "texturebottom")}
                if used & signs:
                    self.assertTrue(touching & allowed, f"a sign on {sorted(self.zone_of[s] for s in touching)}")


if __name__ == "__main__":
    unittest.main()
