"""Safe starts: no monster sees the player where a map begins.

Owner: `level-designer`. The PM's engine pass of 2026-10-22 14:13 (skill 3,
no god mode) found MAP07's player down from 100 % to 3 % health in about
1.3 s: Legion troopers a few metres from the Il-14 had a clear line to
`PLAYER_START` and fired on the first tic. The route runs never saw it
(their helper clears blockers and plays in god mode). Doom's grammar is the
opposite: the room you wake in is safe, or the first enemy is far off, and
you take the first shot.

The rule, for every map of the campaign and the range, on skills 2, 3 and
4: no monster placed for that skill has a line of sight to the start zone
(the player start and the points around it a step away) within
SAFE_START_DISTANCE map units. A monster farther than that may see the
start; Doom's own MAP01 does the same with its first zombies. The one
exception, MAP01's dorm (the alarm, approved and shipped in v1.0), is
listed by name in APPROVED_EXCEPTIONS with its reason.

Fixed under this rule on 2026-10-22: MAP04 (the tunnel mouth's picket),
MAP05 (the station's picket), MAP06 (the hall's first rifleman), MAP07 (the
runway's picket, the PM's finding) and MAP08 (the pier's trooper); MAP02,
MAP03, MAP09 and the range already passed. Each map's design document says
where its first enemies stand now.

The line of sight is Doom's own test (P_CheckSight), written out on the
generated TEXTMAP so no map grades itself: from the monster's eye (3/4 of
its height above its feet, its feet on its sector's floor plus the thing's
height) to the player's body (his floor to his floor + 56). Every linedef the
2D trace crosses is walked in order: a one-sided line or a `blocksight`
line stops it, a two-sided line narrows the window of slopes to its opening
(the higher floor, the lower ceiling; a shut door is an opening of 0), and
the sight is lost when the window closes. Things never block sight (Doom's
rule), and neither does a monster's facing nor the AMBUSH flag: an ambusher
still wakes on sight, and a monster with its back turned turns at the
first shot, so neither makes a start safe.

Run:  python3 -m unittest tests.test_safe_starts -v
      python3 tests/test_safe_starts.py      # the report, map by map
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import test_udmf as udmf_tests  # noqa: E402  (as a module: no TestCase collected twice)

parse_textmap = udmf_tests.parse_textmap
PLAYER_HEIGHT = udmf_tests.PLAYER_HEIGHT   # 56

MAPS = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09", "RANGE")
SKILLS = (2, 3, 4)
ED_PLAYER1_START = 1

# The rule. 768 units is three seconds of a Legion trooper's walk and
# further than a shotgun's pellets group (Doom's spread of 5.6 degrees puts
# them ~75 units apart at 768): far enough to look, aim and take cover.
SAFE_START_DISTANCE = 768
# The start zone: the start and the points one step (32 units, a player's
# radius and a half) around it, so a monster that sees the start's next
# square is caught too.
START_ZONE_STEP = 32
START_ZONE = ((0, 0), (START_ZONE_STEP, 0), (-START_ZONE_STEP, 0),
              (0, START_ZONE_STEP), (0, -START_ZONE_STEP))
EYE_FRACTION = 0.75        # GZDoom: sight starts at Z + Height - Height / 4

MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
MONSTER_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters"


def _load(name: str):
    path = PROJECT_ROOT / "src" / "maps" / name / "map.py"
    spec = importlib.util.spec_from_file_location(f"sdmap_{name}_safe_starts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def monster_heights() -> dict[int, tuple[str, int]]:
    """{DoomEdNum: (class, height)} for every monster number MAPINFO gives,
    our sub-range and the Doom number each class replaces (both spawn ours)."""
    text = MAPINFO.read_text(encoding="utf-8")
    block = re.search(r"DoomEdNums\s*\{(.*?)\n\}", text, re.S).group(1)
    heights = {}
    for path in MONSTER_ZS.glob("*.zs"):
        source = path.read_text(encoding="utf-8")
        cls = re.search(r"^\s*class\s+(SD_\w+)", source, re.M)
        height = re.search(r"const\s+SD_\w+_HEIGHT\s*=\s*(\d+)", source)
        if cls and height:
            heights[cls.group(1)] = int(height.group(1))
    out = {}
    for line in block.splitlines():
        m = re.match(r"\s*(\d+)\s*=\s*(SD_\w+)\s*(?://\s*replaces\s+\w+\s*\((\d+)\))?", line)
        if not m or m.group(2) not in heights:
            continue
        entry = (m.group(2), heights[m.group(2)])
        out[int(m.group(1))] = entry
        if m.group(3):
            out[int(m.group(3))] = entry
    return out


class Geometry:
    """A map's TEXTMAP read back: sectors, lines, things, and Doom's sight."""

    def __init__(self, textmap: str):
        blocks = parse_textmap(textmap)
        self.sectors = blocks["sector"]
        self.sides = blocks["sidedef"]
        self.verts = blocks["vertex"]
        self.things = blocks["thing"]
        self.lines = []
        for ld in blocks["linedef"]:
            a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
            front = self.sides[ld["sidefront"]]["sector"]
            back = self.sides[ld["sideback"]]["sector"] if "sideback" in ld else None
            self.lines.append(((a["x"], a["y"]), (b["x"], b["y"]), front, back,
                               bool(ld.get("blocksight"))))

    def sector_at(self, x: float, y: float):
        """The sector holding (x, y): the nearest line a ray east of the point
        crosses, and which side of it the point is on (front is right of
        v1 -> v2). The point is nudged off the grid so it never lies on a
        vertex or a line."""
        x, y = x + 0.125, y + 0.25
        best = None
        for (x1, y1), (x2, y2), front, back, _ in self.lines:
            if (y1 > y) == (y2 > y):
                continue
            cx = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if cx <= x or (best is not None and cx >= best[0]):
                continue
            right = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1) < 0
            best = (cx, front if right else back)
        return None if best is None else best[1]

    def floor_at(self, x: float, y: float):
        s = self.sector_at(x, y)
        return None if s is None else self.sectors[s]["heightfloor"]

    def sight(self, eye, foot, top) -> bool:
        """Doom's P_CheckSight from `eye` (x, y, z) to a body at (x, y)
        standing from `foot` to `top`."""
        (x0, y0, z0), (x1, y1) = eye[:3], eye[3:]
        dx, dy = x1 - x0, y1 - y0
        crossings = []
        for (ax, ay), (bx, by), front, back, blocksight in self.lines:
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex
            if den == 0:
                continue                      # parallel: never crossed
            t = ((ax - x0) * ey - (ay - y0) * ex) / den
            u = ((ax - x0) * dy - (ay - y0) * dx) / den
            if 0 < t < 1 and 0 <= u <= 1:
                crossings.append((t, front, back, blocksight))
        crossings.sort(key=lambda c: c[0])
        top_slope, bottom_slope = top - z0, foot - z0
        for t, front, back, blocksight in crossings:
            if back is None or blocksight:
                return False
            f, b = self.sectors[front], self.sectors[back]
            open_top = min(f["heightceiling"], b["heightceiling"])
            open_bottom = max(f["heightfloor"], b["heightfloor"])
            if open_bottom >= open_top:
                return False
            if f["heightfloor"] != b["heightfloor"]:
                bottom_slope = max(bottom_slope, (open_bottom - z0) / t)
            if f["heightceiling"] != b["heightceiling"]:
                top_slope = min(top_slope, (open_top - z0) / t)
            if top_slope <= bottom_slope:
                return False
        return True


def start_threats(name: str, skills=SKILLS, distance=SAFE_START_DISTANCE):
    """[(skill, class, x, y, distance to the start, start-zone point seen)]
    for every monster within `distance` that sees the start zone."""
    m = _load(name)
    geo = Geometry(m.build_textmap().render())
    heights = monster_heights()
    starts = [t for t in geo.things if t["type"] == ED_PLAYER1_START]
    assert len(starts) == 1, f"{name}: {len(starts)} player 1 starts"
    sx, sy = starts[0]["x"], starts[0]["y"]
    zone = []
    for ox, oy in START_ZONE:
        floor = geo.floor_at(sx + ox, sy + oy)
        if floor is not None:
            zone.append((sx + ox, sy + oy, floor))
    out = []
    for t in geo.things:
        if t["type"] not in heights:
            continue
        cls, height = heights[t["type"]]
        floor = geo.floor_at(t["x"], t["y"])
        if floor is None:
            continue
        z = floor + t.get("height", 0) + height * EYE_FRACTION
        for skill in skills:
            if not t.get(f"skill{skill}"):
                continue
            for px, py, pfloor in zone:
                d = math.dist((t["x"], t["y"]), (px, py))
                if d >= distance:
                    continue
                if geo.sight((t["x"], t["y"], z, px, py), pfloor, pfloor + PLAYER_HEIGHT):
                    out.append((skill, cls, t["x"], t["y"], round(math.dist((t["x"], t["y"]), (sx, sy))),
                                (px - sx, py - sy)))
                    break
    return out


# The one approved exception: MAP01's dorm. Its design is the alarm (design
# document section 7, round 1: "alarm, confusion, three bodies and two
# enemies"): the Reich is already in the barracks, 311-366 from the bed, two
# riflemen on skill 2, three on 3, four on 4, the bunks low cover. Played,
# approved and shipped in v1.0 (G6 PASS); riflemen are the weakest hitscan
# (20 HP, one 3..15 round an attack) and the TT-33 drops each in a shot or
# two, so it is not clearly unfair and stays as designed. Listed by place
# and class so any other monster that sees MAP01's start still fails.
APPROVED_EXCEPTIONS = {
    "MAP01": {(416, 400, "SD_ReichRifleman"), (592, 240, "SD_ReichRifleman"),
              (192, 400, "SD_ReichRifleman"), (560, 192, "SD_ReichRifleman")},
}


class SafeStartTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.threats = {name: start_threats(name) for name in MAPS}

    def test_the_rule_is_doom_scale(self):
        self.assertGreaterEqual(SAFE_START_DISTANCE, 512)
        self.assertLessEqual(SAFE_START_DISTANCE, 1024)

    def test_every_monster_number_has_a_body(self):
        heights = monster_heights()
        for doom, ours in ((3004, 21100), (9, 21101), (3001, 21102), (3002, 21103),
                           (3005, 21104), (69, 21105), (16, 21106), (3003, 21107)):
            self.assertEqual(heights[doom], heights[ours], doom)
        self.assertEqual(("SD_LegionTrooper", 56), heights[9])

    def test_the_sight_model_sees_and_is_blocked(self):
        """Doom's sight on a toy plan: a wall, a step, a shut door, a pane."""
        geo = Geometry.__new__(Geometry)
        geo.sectors = [{"heightfloor": 0, "heightceiling": 128},
                       {"heightfloor": 64, "heightceiling": 128},
                       {"heightfloor": 0, "heightceiling": 0}]
        geo.lines = [((0, -64), (0, 64), 0, None, False),         # a wall, x 0
                     ((256, -512), (256, 512), 0, 1, False),       # a 64 step up, x 256
                     ((-200, -64), (-200, 64), 0, 2, False),       # a shut door, x -200
                     ((300, 600), (300, 700), 0, 0, True),         # a blocksight pane
                     ((300, 800), (300, 900), 0, 0, False)]        # the same, see-through
        self.assertFalse(geo.sight((-128, 0, 42, 128, 0), 0, 56), "through a wall")
        self.assertTrue(geo.sight((-128, 128, 42, 128, 128), 0, 56), "past the wall's end")
        self.assertTrue(geo.sight((128, 100, 42, 280, 100), 64, 120), "up onto the step")
        self.assertTrue(geo.sight((280, 100, 106, 128, 100), 0, 56), "down off the step")
        self.assertFalse(geo.sight((-300, 0, 42, -100, 0), 0, 56), "through a shut door")
        self.assertFalse(geo.sight((128, 650, 42, 400, 650), 0, 56), "through a blocksight pane")
        self.assertTrue(geo.sight((128, 850, 42, 400, 850), 0, 56), "through an open line")

    def test_no_monster_sees_the_start_up_close(self):
        for name in MAPS:
            with self.subTest(map=name):
                allowed = APPROVED_EXCEPTIONS.get(name, set())
                found = [row for row in self.threats[name] if (row[2], row[3], row[1]) not in allowed]
                self.assertEqual([], found,
                                 f"{name}: monsters that see the start within {SAFE_START_DISTANCE}")

    def test_the_exceptions_are_still_there_and_only_riflemen(self):
        """An exception that no longer sees the start is struck off the list."""
        for name, allowed in APPROVED_EXCEPTIONS.items():
            seen = {(row[2], row[3], row[1]) for row in self.threats[name]}
            self.assertEqual(allowed, seen & allowed, name)
            self.assertEqual({"SD_ReichRifleman"}, {cls for _, _, cls in allowed}, name)


if __name__ == "__main__":
    for map_name in MAPS:
        found = start_threats(map_name)
        print(f"{map_name}: {'clear' if not found else ''}")
        for row in found:
            print("   skill %d  %-22s at (%s, %s)  %4d from the start, sees offset %s" % row)
