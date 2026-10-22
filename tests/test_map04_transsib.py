"""MAP04 «Транссиб» / Trans-Siberian, the Sverdlovsk yard, v1 (docs/levels/MAP04-transsib.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map03_factory.py, whose harness this repeats (one file per
map, so a change to one map's model cannot move another's):

* structure: every sector closed and clockwise, no duplicate vertex, no step
  up higher than a stair step unless it is a drop with a way back;
* only approved, packed textures; door leaves one tile; the locks in their
  keys' trims;
* the progression model: manual doors and push panels open whenever the
  player can stand at them; then, one round at a time, every switch, every
  locked door whose key is reachable, and every PICKUP special whose key is
  reachable (the red key drops the gondolas' sides: Floor_LowerToLowest, a
  lift in the model). Everything reachable at the end, the exit only in the
  last round, no trap at any stage, the secrets never needed;
* the key grammar: each lock seen before its key, each key seen from where
  its room is entered, each key's place in its lock's colour of light;
* the switches: real faces, one-shot, each in sight of what it opens;
* the population: the bestiary's numbers, monsters per skill and nested, both
  factions where the design puts them, every body with room to stand; the
  weapons on the route, consumables scaled down, G3-8's ammunition margin on
  every skill and at every stage, health on skill 4;
* three secrets, each a comparison (a niche in shadow), each with its way
  back, none needed for the exit.

Run:  python -m unittest tests.test_map04_transsib -v
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

# Imported as a module, not by name, so its TestCases are not collected twice.
import test_udmf as udmf_tests  # noqa: E402

parse_textmap = udmf_tests.parse_textmap
MAX_STEP_UP = udmf_tests.MAX_STEP_UP       # 24
PLAYER_HEIGHT = udmf_tests.PLAYER_HEIGHT   # 56
VIEW_HEIGHT = udmf_tests.VIEW_HEIGHT       # 41

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4
DOOR_TILE = 128
SIGHT_STEP = 4
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}
KEY_SPRITE_MID = 8

ASSETS = PROJECT_ROOT / "assets"
MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
MONSTER_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters"
PLAYER_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "player.zs"

SKILLS = (2, 3, 4)
DOOM_MONSTERS = {3004, 9, 3001, 3002, 3005, 69, 3003, 16, 7, 65, 64, 66, 67, 68, 71, 84, 58, 3006}
CLASS_FILES = {
    "SD_ReichRifleman": "reich_rifleman.zs",
    "SD_LegionTrooper": "legion_trooper.zs",
    "SD_Stormtrooper": "stormtrooper.zs",
    "SD_ReichHound": "reich_hound.zs",
    "SD_Doughboy": "doughboy.zs",
    "SD_Panzermensch": "panzermensch.zs",
    "SD_PanzermenschSchwer": "panzermensch_schwer.zs",
}
CLASS_PARENT = {"SD_PanzermenschSchwer": "SD_Panzermensch"}
# G3-8, MAP03's ruler: what each kill costs in IZh shells.
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8,
                  "SD_PanzermenschSchwer": 16}
G3_8_MARGIN = 1.35
SHELLS_GIVEN = {2008: 4, 2049: 20, 21003: 8}
ROUNDS_GIVEN = {2007: 10, 2048: 50, 21004: 35}
ROCKETS_GIVEN = {2010: 1, 2046: 5, 21005: 2}
CELLS_GIVEN = {2047: 20, 17: 100, 21006: 40}
ROUNDS_PER_SHELL = 10
SHELLS_PER_ROCKET = 2
SHELLS_PER_CELL = 0.25
IZH_AVERAGE = 80
PPSH_AVERAGE = 8
RPG_AVERAGE = 135
ROKS_AVERAGE = 18


def _load_map04():
    path = PROJECT_ROOT / "src" / "maps" / "MAP04" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP04_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


def _class_facts(name: str) -> dict:
    text = (MONSTER_ZS / CLASS_FILES[name]).read_text(encoding="utf-8")
    facts = {k: int(v) for k, v in
             re.findall(r"const\s+SD_\w+?_(RADIUS|HEIGHT|HEALTH)\s*=\s*(\d+)", text)}
    faction = re.search(r"SD_Monster\.Faction\s+SD_FACTION_(\w+)", text)
    if faction:
        facts["FACTION"] = faction.group(1)
    parent = CLASS_PARENT.get(name)
    if parent:
        for key, value in _class_facts(parent).items():
            facts.setdefault(key, value)
    return facts


def _doomednums() -> dict[int, str]:
    text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
    block = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S).group(1)
    return {int(n): c for n, c in re.findall(r"(\d+)\s*=\s*(\w+)", block)}


class Map04Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map04()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_tunnel"]
        cls.doors = defaultdict(set)
        cls.lifts = defaultdict(set)
        for i, s in enumerate(cls.sectors):
            if s.get("id") in cls.m.LIFT_TAGS:
                cls.lifts[s["id"]].add(i)
            elif s.get("id") and s["heightceiling"] == s["heightfloor"]:
                cls.doors[s["id"]].add(i)
        cls.door_sectors = set().union(*cls.doors.values())
        cls.lift_sectors = set().union(*cls.lifts.values())
        cls.neighbours = defaultdict(set)
        for ld in cls.lines:
            if "sideback" in ld:
                a, b = cls._pair(ld)
                cls.neighbours[a].add(b)
                cls.neighbours[b].add(a)
        cls.vertical = []
        for ld in cls.lines:
            a, b = cls.verts[ld["v1"]], cls.verts[ld["v2"]]
            if a["x"] == b["x"]:
                cls.vertical.append((a["x"], a["y"], b["y"], ld))
        cls.props = {i for name, i in cls.plan.items() if name.startswith(cls.m.PROP_PREFIX)}
        cls.unwalkable = cls.props | cls.door_sectors | cls.lift_sectors
        cls.monster_numbers = set(cls.m.MONSTER_CLASSES)
        cls.body, cls.hit_points, cls.faction = {}, {}, {}
        for ednum, name in cls.m.MONSTER_CLASSES.items():
            facts = _class_facts(name)
            cls.body[ednum] = (facts["RADIUS"], facts["HEIGHT"])
            cls.hit_points[ednum] = facts["HEALTH"]
            cls.faction[ednum] = facts["FACTION"]

    # --- helpers ----------------------------------------------------------
    @classmethod
    def _pair(cls, ld):
        return (cls.sides[ld["sidefront"]]["sector"], cls.sides[ld["sideback"]]["sector"])

    def front(self, ld):
        return self.sides[ld["sidefront"]]["sector"]

    def sector_at(self, x, y):
        x, y = x + 0.125, y + 0.25
        best = None
        for lx, y1, y2, ld in self.vertical:
            if lx <= x or not (min(y1, y2) < y < max(y1, y2)):
                continue
            if best is None or lx < best[0]:
                best = (lx, y1, y2, ld)
        if best is None:
            return None
        _, y1, y2, ld = best
        if y2 < y1:
            return self.sides[ld["sidefront"]]["sector"]
        return self.sides[ld["sideback"]]["sector"] if "sideback" in ld else None

    def heights(self, open_tags):
        """(floor, ceiling) per sector with `open_tags` worked: a door's
        ceiling rises to its lowest neighbour's less 4, a lift's floor drops
        to its lowest neighbour's (Floor_LowerToLowest)."""
        out = []
        for i, s in enumerate(self.sectors):
            floor, ceiling = s["heightfloor"], s["heightceiling"]
            if i in self.door_sectors and s["id"] in open_tags:
                ceiling = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                           - DOOR_OPENS_BELOW_CEILING)
            if i in self.lift_sectors and s["id"] in open_tags:
                floor = min(self.sectors[n]["heightfloor"] for n in self.neighbours[i])
            out.append((floor, ceiling))
        return out

    def adjacency(self, open_tags):
        h = self.heights(open_tags)
        adj = defaultdict(set)
        for ld in self.lines:
            if "sideback" not in ld or ld.get("blocking"):
                continue
            a, b = self._pair(ld)
            for src, dst in ((a, b), (b, a)):
                (fs, fc), (ts, tc) = h[src], h[dst]
                if min(fc, tc) - max(fs, ts) < PLAYER_HEIGHT:
                    continue
                if ts - fs > MAX_STEP_UP:
                    continue
                adj[src].add(dst)
        return adj

    @staticmethod
    def flood(adj, start):
        seen, stack = {start}, [start]
        while stack:
            for nxt in adj[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    @staticmethod
    def reverse(adj):
        rev = defaultdict(set)
        for src, dsts in adj.items():
            for dst in dsts:
                rev[dst].add(src)
        return rev

    def reachable(self, open_tags):
        return self.flood(self.adjacency(open_tags), self.start)

    def key_things(self):
        return [t for t in self.things if t["type"] in KEY_NUMBERS]

    def key_sectors(self):
        return {self.m.KEY_LOCKS[t["type"]]: self.sector_at(t["x"], t["y"]) for t in self.key_things()}

    def pickup_specials(self):
        """[(tag, sector)] for every pickup whose special acts on a tag."""
        return [(t["arg0"], self.sector_at(t["x"], t["y"])) for t in self.things
                if t["type"] not in self.monster_numbers and t.get("special")]

    def progression(self):
        """Play the map as a player can (MAP03's model, plus pickups): manual
        doors and push panels open whenever he can stand at their line;
        then, one round at a time, every switch and locked door he can reach
        and work, and every pickup special whose thing he can reach.
        Returns one (open tags, reachable sectors, locks held) per round."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        keys = self.key_sectors()
        pickups = self.pickup_specials()
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = {lock for lock, sector in keys.items() if sector in reach}
            free = set()
            gated = {tag for tag, sector in pickups if sector in reach}
            for ld in uses:
                stand = {self.front(ld)}
                if "sideback" in ld:
                    stand.add(self.sides[ld["sideback"]]["sector"])
                if not stand & reach:
                    continue
                tag = ld["arg0"]
                if ld["special"] == self.m.SPECIAL_DOOR_LOCKED_RAISE:
                    if ld["arg3"] in held:
                        gated.add(tag)
                elif "sideback" in ld:
                    free.add(tag)
                else:
                    gated.add(tag)
            if free - opened:
                opened |= free
                continue
            rounds.append((frozenset(opened), reach, frozenset(held)))
            if not gated - opened:
                return rounds
            opened |= gated

    def named(self, *names):
        return {self.plan[n] for n in names}

    def exit_line(self):
        exits = [ld for ld in self.lines if ld.get("special") == SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        return exits[0]

    def line_points(self, ld):
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        return (a["x"], a["y"]), (b["x"], b["y"])

    def blocked(self, eye, target, open_tags=frozenset()):
        (x0, y0, z0), (x1, y1, z1) = eye, target
        h = self.heights(set(open_tags))
        n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
        for k in range(1, n):
            t = k / n
            x, y, z = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
            s = self.sector_at(x, y)
            if s is None:
                return (round(x), round(y), round(z), "void")
            floor, ceiling = h[s]
            if not floor < z < ceiling:
                return (round(x), round(y), round(z), self.zone_of[s])
        return None

    def eye(self, x, y, zone):
        return (x, y, self.sectors[self.plan[zone]]["heightfloor"] + VIEW_HEIGHT)

    def key_target(self, spot, zone):
        return (spot[0], spot[1], self.sectors[self.plan[zone]]["heightfloor"] + KEY_SPRITE_MID)

    def things_of(self, numbers):
        return [t for t in self.things if t["type"] in numbers]

    @staticmethod
    def on(skill, things):
        return [t for t in things if t[f"skill{skill}"]]

    def monsters(self):
        return self.things_of(self.monster_numbers)

    def one_sided_textures(self, sector):
        out = Counter()
        for ld in self.lines:
            if "sideback" in ld or self.front(ld) != sector:
                continue
            (ax, ay), (bx, by) = self.line_points(ld)
            out[self.sides[ld["sidefront"]].get("texturemiddle")] += abs(bx - ax) + abs(by - ay)
        return out

    # --- structure ----------------------------------------------------------
    def test_every_sector_is_closed_and_clockwise(self):
        loops = udmf_tests.sector_loops(self.blocks)
        self.assertEqual(set(range(len(self.sectors))), set(loops))
        for sector, edges in loops.items():
            out_deg, in_deg = defaultdict(int), defaultdict(int)
            for a, b in edges:
                out_deg[a] += 1
                in_deg[b] += 1
            self.assertEqual(dict(out_deg), dict(in_deg), self.zone_of[sector])
            self.assertLess(udmf_tests.signed_area(self.blocks, edges), 0, self.zone_of[sector])

    def test_no_duplicate_vertices(self):
        points = [(v["x"], v["y"]) for v in self.verts]
        self.assertEqual(len(points), len(set(points)))

    def test_every_sector_survived_the_painter(self):
        loops = udmf_tests.sector_loops(self.blocks)
        for name, index in self.plan.items():
            self.assertTrue(loops.get(index), f"{name} was painted out of existence")

    def test_no_step_is_higher_than_a_stair_step_unless_it_is_a_drop(self):
        every = set().union(*(r[0] for r in self.progression()))
        h = self.heights(every)
        for a, dsts in self.adjacency(every).items():
            for b in dsts:
                rise = h[b][0] - h[a][0]
                self.assertLessEqual(rise, self.m.STEP, f"{self.zone_of[a]} -> {self.zone_of[b]}")

    def test_the_map_is_the_size_of_the_episode_ones(self):
        """MAP02 is 3552 x 1552, MAP03 3776 x 2144: this one in that range."""
        xs = [v["x"] for v in self.verts]
        ys = [v["y"] for v in self.verts]
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        self.assertLessEqual(width * height, 1.5 * 3776 * 2144)
        self.assertGreaterEqual(width * height, 3552 * 1552)

    # --- textures -----------------------------------------------------------
    def test_every_texture_is_approved_and_packed(self):
        walls = set(self.m.WALL_TEXTURES)
        flats = set(self.m.FLAT_TEXTURES)
        for i, sd in enumerate(self.sides):
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                name = sd.get(key, "-")
                if name != "-":
                    self.assertIn(name, walls, f"sidedef {i}.{key}")
        for i, s in enumerate(self.sectors):
            self.assertIn(s["texturefloor"], flats, f"sector {self.zone_of[i]}")
            self.assertIn(s["textureceiling"], flats | set(self.m.BUILTIN_FLATS), f"sector {self.zone_of[i]}")
        for name in walls | flats:
            self.assertTrue(_packed(name), f"{name} is not in assets/")

    def test_every_listed_texture_is_used(self):
        used = set()
        for sd in self.sides:
            used |= {sd.get(k) for k in ("texturetop", "texturemiddle", "texturebottom")}
        for s in self.sectors:
            used |= {s["texturefloor"], s["textureceiling"]}
        for name in set(self.m.WALL_TEXTURES) | set(self.m.FLAT_TEXTURES):
            self.assertIn(name, used, name)

    def test_every_door_leaf_is_one_tile(self):
        faces = Counter()
        for i, ld in enumerate(self.lines):
            if "sideback" not in ld:
                continue
            a, b = self._pair(ld)
            for room, door, side in ((a, b, ld["sidefront"]), (b, a, ld["sideback"])):
                if door not in self.door_sectors:
                    continue
                leaf = self.sides[side].get("texturetop")
                if leaf not in self.m.DOOR_LEAVES:
                    continue
                faces[leaf] += 1
                (ax, ay), (bx, by) = self.line_points(ld)
                self.assertEqual(DOOR_TILE, abs(bx - ax) + abs(by - ay), f"linedef {i}")
                drop = self.sectors[room]["heightceiling"] - self.sectors[door]["heightfloor"]
                self.assertEqual(DOOR_TILE, drop, f"linedef {i}: leaf of {self.zone_of[door]}")
        self.assertEqual({self.m.DOOR: 6, self.m.DOOR_YELLOW: 2, self.m.DOOR_RED: 2}, dict(faces),
                         "D1, D2 and the hatch, the two locks, two faces each")

    def test_each_locked_door_wears_its_keys_trim(self):
        m = self.m
        for tag, leaf in ((m.TAG_YELLOW_DOOR, m.DOOR_YELLOW), (m.TAG_RED_DOOR, m.DOOR_RED)):
            for ld in self.lines:
                if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE and ld["arg0"] == tag:
                    self.assertEqual(leaf, self.sides[ld["sidefront"]].get("texturetop"))

    def test_star_plaques_frame_the_yellow_door_only(self):
        m = self.m
        found = [ld for ld in self.lines
                 if m.STAR in (self.sides[ld["sidefront"]].get("texturemiddle"),)]
        self.assertEqual(2, len(found))
        portal = self.plan["z2_yellow_portal"]
        for ld in found:
            self.assertEqual(portal, self.front(ld))
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.TILE, abs(bx - ax) + abs(by - ay))

    def test_the_trains_flank_is_armour_and_the_platform_is_a_station(self):
        m = self.m
        platform = self.one_sided_textures(self.plan["z6_platform"])
        coping = self.one_sided_textures(self.plan["z6_coping"])
        self.assertGreaterEqual(coping[m.ARMOUR] + platform[m.ARMOUR], 1024, "the armoured train alongside")
        _y, x1, x2 = m.TRAIN_FLANK
        self.assertEqual(0, (x2 - x1) % m.ARMOUR_WIDTH, "whole plates along the flank")
        self.assertGreater(platform[m.STATION], 0)
        for zone in ("z7_engine", "z7_gun", "z7_troop", "z7_couple_1", "z7_couple_2"):
            self.assertLessEqual(set(self.one_sided_textures(self.plan[zone])), {m.ARMOUR, m.ARMOUR_STAR}, zone)
        self.assertEqual({m.CAB_FRONT, m.CAB_SIDE}, set(self.one_sided_textures(self.plan["z7_cab"])),
                         "the locomotive's cab from inside (section 7.2, round 2)")
        self.assertIn(m.ARMOUR_STAR, self.one_sided_textures(self.plan["z6_balcony"]),
                      "the star the platform sees")
        self.assertEqual(m.FLOOR_COPING, self.sectors[self.plan["z6_coping"]]["texturefloor"])

    def test_each_star_is_one_panel_one_tile_high_and_alone(self):
        """SDARMR1 is a panel, not a fill: every face exactly one tile wide
        on a wall exactly one tile high (never stacked), no two touching."""
        m = self.m
        stars = [ld for ld in self.lines
                 if self.sides[ld["sidefront"]].get("texturemiddle") == m.ARMOUR_STAR]
        self.assertEqual(len(m.STAR_PANELS), len(stars))
        ends = Counter()
        for ld in stars:
            self.assertNotIn("sideback", ld)
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.TILE, abs(bx - ax) + abs(by - ay))
            self.assertEqual(0, self.sides[ld["sidefront"]].get("offsetx", 0) % m.ARMOUR_WIDTH,
                             "the star starts on a plate seam")
            s = self.sectors[self.front(ld)]
            self.assertEqual(m.TILE, s["heightceiling"] - s["heightfloor"], self.zone_of[self.front(ld)])
            ends.update((ld["v1"], ld["v2"]))
        self.assertEqual(1, max(ends.values()), "two stars side by side")

    def wagon_faces(self, rect, car_sectors):
        """{y: [(start, end, u at start, sidedef)]} along a car's two long
        sides, each piece as the yard sees it, ordered from the viewer's left."""
        x1, y1, x2, y2 = rect
        faces = {}
        for y in (y1, y2):
            pieces = []
            for ld in self.lines:
                if "sideback" not in ld:
                    continue
                (ax, ay), (bx, by) = self.line_points(ld)
                if not (ay == by == y and x1 <= min(ax, bx) and max(ax, bx) <= x2):
                    continue
                # The front side reads its texture from v1 to v2, the back from v2 to v1.
                for key, start, end in (("sidefront", ax, bx), ("sideback", bx, ax)):
                    sd = self.sides[ld[key]]
                    if sd["sector"] not in car_sectors:
                        pieces.append((start, end, sd.get("offsetx", 0), sd))
            faces[y] = sorted(pieces, key=lambda p: p[0] if p[1] > p[0] else -p[0])
        return faces

    def test_wagon_sides_run_whole_and_continuous(self):
        """Each car's side is one run of its texture, however the painter
        split the line (the gondolas' dropping sides): it starts on a post
        (SDWAGN1) or centres the tank's two tiles (SDTANK1), runs on without
        a jump, and is lifted so the underframe stands on the ground; a
        boxcar ends on the tile's seam, so the rake reads as cars."""
        m = self.m
        cars = [(rect[:4], {self.plan[name]}, rect[5]) for name, rect in m.WAGONS.items()
                if rect[5] in (m.WAGON_SIDE, m.TANK_SIDE)]
        roofs = {self.plan[f"z2_roof_{n}"] for n in range(1, len(m.ROOFS) + 1)}
        cars += [((x1, m.ROW_3[0], x2, m.ROW_3[1]), roofs, m.WAGON_SIDE) for x1, x2 in m.ROOFS]
        cars += [(shell, {self.plan[f"prop_{name[3:]}_shell"], self.plan[name], self.plan[f"{name}_side"]},
                  m.WAGON_SIDE) for name, (shell, _bed, _side) in m.GONDOLAS.items()]
        self.assertEqual(8, len(cars), "a boxcar, a tank wagon, four boxcars in the rake, two gondolas")
        for rect, car_sectors, texture in cars:
            base = m.WAGON_OFFSET_X if texture == m.WAGON_SIDE else m.TANK_OFFSET_X
            for y, pieces in self.wagon_faces(rect, car_sectors).items():
                self.assertTrue(pieces, (rect, y))
                self.assertEqual(base, pieces[0][2], f"{rect} y {y}: the run's start")
                for (s0, e0, u0, sd), nxt in zip(pieces, pieces[1:] + [None]):
                    self.assertEqual(texture, sd.get("texturebottom"), (rect, y))
                    self.assertEqual(m.WAGON_OFFSET_Y, sd.get("offsety", 0), (rect, y))
                    if nxt:
                        self.assertEqual((u0 + abs(e0 - s0)) % m.WAGON_TILE, nxt[2], f"{rect} y {y}: a jump")
                if texture == m.WAGON_SIDE:
                    self.assertEqual(0, (base + rect[2] - rect[0]) % m.WAGON_TILE, f"{rect}: ends on the seam")
        x1, _y1, x2, _y2, _h, side = m.WAGONS["prop_wagon_2a"]
        self.assertEqual(m.TANK_SIDE, side, "a tank wagon in the second row")
        self.assertEqual(m.WAGON_TILE - m.TANK_OFFSET_X, (m.TANK_OFFSET_X + x2 - x1) % m.WAGON_TILE,
                         "the tank's two whole tiles centred")

    def test_the_wagons_are_wagons(self):
        """Boxcars, the rake and the gondolas in the goods wagon's side, the
        tank wagon, the flatcars a crate high; the roofs plate."""
        m = self.m
        for name, (*_rect, height, side) in m.WAGONS.items():
            s = self.sectors[self.plan[name]]
            self.assertEqual(height, s["heightfloor"], name)
        for n in range(1, len(m.ROOFS) + 1):
            s = self.sectors[self.plan[f"z2_roof_{n}"]]
            self.assertEqual((m.WAGON, m.WAGON_ROOF, 90.0),
                             (s["heightfloor"], s["texturefloor"], s.get("rotationfloor")))
        flank = [ld for ld in self.lines if "sideback" in ld
                 and self.plan["z2_yard"] in self._pair(ld)
                 and self.plan["z2_roof_2"] in self._pair(ld)]
        self.assertTrue(flank)
        for ld in flank:
            yard_side = ld["sidefront"] if self.front(ld) == self.plan["z2_yard"] else ld["sideback"]
            self.assertEqual(m.WAGON_SIDE, self.sides[yard_side].get("texturebottom"))

    def test_the_signals_are_single_use(self):
        """D107: SDSIGL1 only as a signal on its own, never a mosaic: every
        face one span of 64 at most, one tile high at most (never stacked),
        no two faces touching; one face per signal, on a pillar in the yard
        that stays cover (a prop)."""
        m = self.m
        parts = ("texturetop", "texturemiddle", "texturebottom")
        faces = [ld for ld in self.lines
                 if m.SIGNAL in {self.sides[ld[k]].get(t) for k in ("sidefront", "sideback") if k in ld
                                 for t in parts}]
        self.assertEqual(len(m.SIGNALS), len(faces))
        ends = Counter()
        for ld in faces:
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertLessEqual(abs(bx - ax) + abs(by - ay), m.SIGNAL_WIDTH)
            if "sideback" in ld:
                a, b = (self.sectors[s] for s in self._pair(ld))
                self.assertLessEqual(abs(a["heightfloor"] - b["heightfloor"]), m.TILE, "stacked")
                self.assertEqual(a["heightceiling"], b["heightceiling"], "a second face above")
            else:
                s = self.sectors[self.front(ld)]
                self.assertLessEqual(s["heightceiling"] - s["heightfloor"], m.TILE, "stacked")
            ends.update((ld["v1"], ld["v2"]))
        self.assertEqual(1, max(ends.values()), "two signal faces touching")
        for name, (x1, y1, x2, y2), _face in m.SIGNALS:
            self.assertTrue(name.startswith(m.PROP_PREFIX))
            pillar = self.plan[name]
            self.assertEqual(pillar, self.sector_at((x1 + x2) // 2, (y1 + y2) // 2))
            self.assertEqual(m.GROUND + m.SIGNAL_PILLAR, self.sectors[pillar]["heightfloor"])
            self.assertIn(self.plan["z2_yard"], self.neighbours[pillar])

    def test_the_railway_set_dresses_the_yard_and_the_roundhouse(self):
        m = self.m

        def sector(name):
            return self.sectors[self.plan[name]]

        self.assertEqual(m.BALLAST, sector("z2_yard")["texturefloor"])
        for name in ("z2_rails_main", "z2_rails_north", "z5_rails_road", "z5_rails_stall",
                     "z5_bridge_track_w", "z5_bridge_track_e"):
            s = sector(name)
            self.assertEqual((m.TRACK, 90.0), (s["texturefloor"], s.get("rotationfloor")), name)
        self.assertEqual(m.RAILS, sector("z1_tunnel_rails")["texturefloor"], "the tunnel's metro bed")
        # Every track strip is one tile of the 64 grid across: one track, never
        # a rail of the next tile.
        ys = defaultdict(set)
        for ld in self.lines:
            for key in ("sidefront", "sideback"):
                if key in ld:
                    ys[self.sides[ld[key]]["sector"]] |= {self.verts[ld["v1"]]["y"], self.verts[ld["v2"]]["y"]}
        for i, s in enumerate(self.sectors):
            if s["texturefloor"] in (m.TRACK, m.RAILS):
                self.assertEqual(64, max(ys[i]) - min(ys[i]), self.zone_of[i])
                self.assertEqual(0, min(ys[i]) % 64, self.zone_of[i])
        self.assertEqual(m.DECK, sector("z5_bridge")["texturefloor"])
        for name in m.STALLS:
            self.assertEqual(m.BALLAST, sector(name)["texturefloor"], name)
        for name in ("z5_hall", "z5_road", "z5_stall_1", "z5_stall_2", "z5_stall_3"):
            self.assertIn(m.ROUNDHOUSE_BRICK, self.one_sided_textures(self.plan[name]), name)
        self.assertNotIn(m.ROUNDHOUSE_BRICK, self.one_sided_textures(self.plan["z2_yard"]))
        gates = [ld for ld in self.lines if "sideback" not in ld
                 and self.sides[ld["sidefront"]].get("texturemiddle") == m.GOODS_GATE]
        self.assertEqual(len(m.GOODS_GATES), len(gates))
        for ld in gates:
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.TILE, abs(bx - ax) + abs(by - ay))
            s = self.sectors[self.front(ld)]
            self.assertEqual(m.TILE, s["heightceiling"] - s["heightfloor"], "one whole gate")
            self.assertIn(self.plan["z2_yard"], self.neighbours[self.front(ld)])

    # --- round 2 (D113): the sky and the Railway set's second batch ---------
    def test_the_night_sky_is_over_the_yard_only(self):
        """F_SKY1 over the yard and everything standing in it (wagons, roofs,
        the ramp, the signals), the signal box's window band and its porch;
        never over a roofed room, a door or a recess cut into the yard's
        walls (a recess under the sky would lose the wall above it)."""
        m = self.m
        sky = {self.zone_of[i] for i, s in enumerate(self.sectors) if s["textureceiling"] == m.SKY}
        for zone in ("z2_yard", "z2_rails_main", "z2_rails_north", "z2_roof_1", "z2_ramp_1",
                     "prop_wagon_1a", "prop_signal_main", "z2_gondola_1", "z2_gondola_1_side",
                     "prop_cabin_sills", "z3_step"):
            self.assertIn(zone, sky)
        for zone in sky:
            self.assertTrue(zone.startswith(("z2_", "prop_", "z3_step")), zone)
            self.assertNotIn(self.plan[zone], self.door_sectors, zone)
            self.assertFalse(zone.startswith(("z2_goods_gate", "z2_flag", "z2_poster", "z2_yellow",
                                              "z2_red")), zone)
        for zone in ("z3_cabin", "z3_frame", "z1_mouth", "z2_goods_gate_1", "z2_flag_s", "z2_poster_lenin"):
            self.assertNotIn(zone, sky)

    def test_the_wagons_wear_their_roofs_and_the_gondolas_their_floors(self):
        """SDWROF1 on every car's top seen from the roofs (boxcars, the
        rake, the tank, the gondolas' rims and dropping sides), its walkway
        turned along the car; SDGOND1 on the gondolas' beds, turned the same
        way and panned 16 both ways, so the flaps' 32 grid meets the bed's
        edges (which lie 16 off it)."""
        m = self.m
        roofs = [f"z2_roof_{n}" for n in range(1, len(m.ROOFS) + 1)]
        roofs += [n for n, r in m.WAGONS.items() if r[4] == m.WAGON]
        for name in m.GONDOLAS:
            roofs += [f"prop_{name[3:]}_shell", f"{name}_side"]
            bed = self.sectors[self.plan[name]]
            self.assertEqual((m.GONDOLA_BED, 90.0), (bed["texturefloor"], bed.get("rotationfloor")), name)
            x1, y1, _x2, _y2 = m.GONDOLAS[name][1]
            for key, edge in (("xpanningfloor", x1), ("ypanningfloor", y1)):
                self.assertEqual(m.GONDOLA_PAN, bed.get(key), (name, key))
                self.assertEqual(m.GONDOLA_PAN, edge % 32, (name, key, "the bed's edge, 16 off the flaps"))
        for name in roofs:
            s = self.sectors[self.plan[name]]
            self.assertEqual((m.WAGON_ROOF, 90.0), (s["texturefloor"], s.get("rotationfloor")), name)
        self.assertEqual(len(m.ROOFS) + 2 + 2 * len(m.GONDOLAS), len(roofs))

    def test_the_lever_frame_is_one_whole_frame(self):
        """SDLEVR1 on the frame's top, one flat tile exactly (64 x 64, 32 off
        the grid both ways, panned 32); SDLEVR2 on its 16-high front and
        ends towards the cabin, rows 45-60 (the brass plates and the bed)."""
        m = self.m
        x1, y1, x2, y2 = m.LEVER_FRAME_RECT
        self.assertEqual((64, 64), (x2 - x1, y2 - y1))
        frame = self.sectors[self.plan["z3_frame"]]
        self.assertEqual((m.LEVER_TOP, m.LEVER_ROTATION), (frame["texturefloor"], frame.get("rotationfloor")))
        for key, edge in (("xpanningfloor", x1), ("ypanningfloor", y1)):
            self.assertEqual(m.LEVER_PAN, frame.get(key))
            self.assertEqual(m.LEVER_PAN, edge % 64)
        self.assertEqual(m.STEP, m.LEVER_FRAME - m.CABIN, "the front is 16 high")
        faces = 0
        for ld in self.lines:
            if "sideback" not in ld or set(self._pair(ld)) != self.named("z3_frame", "z3_cabin"):
                continue
            key = "sidefront" if self.front(ld) == self.plan["z3_cabin"] else "sideback"
            self.assertEqual(m.LEVER_FRONT, self.sides[ld[key]].get("texturebottom"))
            self.assertEqual(m.LEVER_FRONT_ROW, self.sides[ld[key]].get("offsety", 0))
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(64, abs(bx - ax) + abs(by - ay), "one whole frame a face")
            faces += 1
        self.assertEqual(3, faces, "the front and both ends; the back is the window's wall")

    def test_the_cab_is_a_steam_cab_from_inside(self):
        """SDCAB1 once, as one tile across the cab's 128 front: the exit's
        niche cut into its middle, its two pieces continuing the one tile
        (columns 0-31 and 96-127); SDCAB2 on the sides, whole tiles."""
        m = self.m
        fx, fy1, fy2 = m.CAB_FRONT_WALL
        self.assertEqual(m.TILE, fy2 - fy1)
        fronts = [ld for ld in self.lines if "sideback" not in ld
                  and self.sides[ld["sidefront"]].get("texturemiddle") == m.CAB_FRONT]
        self.assertEqual(2, len(fronts))
        columns = set()
        for ld in fronts:
            self.assertEqual(self.plan["z7_cab"], self.front(ld))
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(fx, ax)
            self.assertEqual(fx, bx)
            start = self.sides[ld["sidefront"]].get("offsetx", 0)
            columns.add((start, start + abs(by - ay)))
        self.assertEqual({(0, 32), (96, 128)}, columns, "one backhead, its middle the exit's niche")
        cab = self.sectors[self.plan["z7_cab"]]
        self.assertEqual(m.TILE, cab["heightceiling"] - cab["heightfloor"])
        for ld in self.lines:
            if "sideback" in ld or self.front(ld) != self.plan["z7_cab"]:
                continue
            if self.sides[ld["sidefront"]].get("texturemiddle") == m.CAB_SIDE:
                (ax, ay), (bx, by) = self.line_points(ld)
                self.assertEqual(0, (abs(bx - ax) + abs(by - ay)) % 64)
                self.assertEqual(0, min(ax, bx) % 64, "whole tiles from the grid")

    def test_the_signal_box_is_glazed_from_the_yard(self):
        """SDSBOX1 in every window of the box: the middle texture of each
        line between the window band and the open air, on the open air's
        side only, row 8 at the window head (offsety_mid), whole panes on the
        64 grid; the line blocks the monsters' sight (the glass is opaque)."""
        m = self.m
        sills = self.plan["prop_cabin_sills"]
        glazed = 0
        for ld in self.lines:
            for key, other in (("sidefront", "sideback"), ("sideback", "sidefront")):
                if key not in ld or self.sides[ld[key]].get("texturemiddle") != m.BOX_GLAZING:
                    continue
                self.assertIn(other, ld)
                self.assertEqual(sills, self.sides[ld[other]]["sector"])
                self.assertEqual("-", self.sides[ld[other]].get("texturemiddle", "-"), "from inside, the yard")
                self.assertEqual(m.BOX_GLAZING_ROW, self.sides[ld[key]].get("offsety_mid"))
                self.assertEqual(0, self.sides[ld[key]].get("offsetx", 0))
                self.assertTrue(ld.get("blocksight"))
                (ax, ay), (bx, by) = self.line_points(ld)
                self.assertEqual(0, (abs(bx - ax) + abs(by - ay)) % m.GLAZING_WIDTH)
                self.assertEqual(0, min(ax, bx) % 64 if ay == by else min(ay, by) % 64)
                band = self.sectors[sills]
                self.assertEqual(64 - 2 * m.BOX_GLAZING_ROW, band["heightceiling"] - band["heightfloor"])
                glazed += abs(bx - ax) + abs(by - ay)
        x1, y1, x2, y2 = m.CABIN_OUTER
        step = m.CABIN_STEP[3] - m.CABIN_STEP[1]
        self.assertEqual(2 * (x2 - x1) + 2 * (y2 - y1) - step, glazed, "every window, all round but the porch")

    def test_the_station_board_hangs_over_the_platforms_edge(self):
        """SDSTAN1 once: the middle texture of one line exactly 256 long, the
        platform's edge, on the platform's side, pegged to the canopy (256
        down to 192, over every head) and read from the red door."""
        m = self.m
        boards = [(ld, key) for ld in self.lines for key in ("sidefront", "sideback")
                  if key in ld and self.sides[ld[key]].get("texturemiddle") == m.STATION_BOARD]
        self.assertEqual(1, len(boards))
        ld, key = boards[0]
        self.assertEqual(self.plan["z6_platform"], self.sides[ld[key]]["sector"])
        (ax, ay), (bx, by) = self.line_points(ld)
        self.assertEqual((m.COPING_EDGE_Y, m.COPING_EDGE_Y), (ay, by))
        self.assertEqual(m.STATION_BOARD_X, (min(ax, bx), max(ax, bx)))
        self.assertEqual(m.STATION_BOARD_SIZE[0], abs(bx - ax))
        self.assertEqual(0, self.sides[ld[key]].get("offsetx", 0))
        self.assertFalse(ld.get("blocking"))
        platform = self.sectors[self.plan["z6_platform"]]
        under = self.sectors[self.plan["z6_coping_board"]]
        self.assertEqual(platform["heightceiling"], under["heightceiling"])
        foot = platform["heightceiling"] - m.STATION_BOARD_SIZE[1]
        tallest = max(height for _radius, height in self.body.values())
        self.assertGreater(foot - platform["heightfloor"], tallest, "over every head")
        coping = self.sectors[self.plan["z6_coping"]]
        for field in ("heightfloor", "texturefloor", "rotationfloor", "lightlevel"):
            self.assertEqual(coping.get(field), under.get(field), field)
        for spot in ((2700, 2300), (1600, 2200)):
            eye = self.eye(*spot, "z6_platform")
            for x in (2080, 2176, 2272):
                self.assertIsNone(self.blocked(eye, (x, m.COPING_EDGE_Y, foot + 32)), f"{spot}: board x {x}")

    def test_middle_textures_are_only_the_glazing_and_the_board(self):
        m = self.m
        for ld in self.lines:
            for key in ("sidefront", "sideback"):
                if key not in ld:
                    continue
                mid = self.sides[ld[key]].get("texturemiddle", "-")
                if "sideback" in ld:
                    self.assertIn(mid, ("-",) + m.MIDDLE_TEXTURES)
                else:
                    self.assertNotIn(mid, m.MIDDLE_TEXTURES)

    def test_the_stalls_wear_their_road_doors(self):
        """SDRHDR1 on stall 2's back and on S2's panel in stall 3 (the same
        face: the clue is the shadow), each one whole tile."""
        m = self.m
        stalls = self.named("z5_stall_2", "z5_stall_3")
        faces = [(ld, key) for ld in self.lines for key in ("sidefront", "sideback")
                 if key in ld and self.sides[ld[key]]["sector"] in stalls
                 and m.STALL_DOORS in (self.sides[ld[key]].get("texturemiddle"),
                                       self.sides[ld[key]].get("texturetop"))]
        rooms = {self.sides[ld[key]]["sector"] for ld, key in faces}
        self.assertLessEqual(self.named("z5_stall_2", "z5_stall_3"), rooms)
        for ld, _key in faces:
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.TILE, abs(bx - ax) + abs(by - ay))
        for name in ("z5_stall_2", "z5_stall_3"):
            s = self.sectors[self.plan[name]]
            self.assertEqual(m.TILE, s["heightceiling"] - s["heightfloor"], name)

    def test_the_flags_of_both_factions(self):
        m = self.m
        counts = Counter(self.sides[ld["sidefront"]].get("texturemiddle") for ld in self.lines
                         if "sideback" not in ld)
        self.assertEqual(3, counts[m.FLAG_REICH], "two at the tunnel's mouth, one on the platform")
        self.assertEqual(2, counts[m.FLAG_LEGION], "one in the warehouse, one on the platform")

    # --- light --------------------------------------------------------------
    def test_every_light_is_in_range(self):
        for i, s in enumerate(self.sectors):
            self.assertGreaterEqual(s["lightlevel"], self.m.LIGHT_MIN, self.zone_of[i])
            self.assertLessEqual(s["lightlevel"], self.m.LIGHT_MAX, self.zone_of[i])

    def test_the_beacon_light_is_spent_on_locks_keys_and_exit_only(self):
        beacons = {self.zone_of[i] for i, s in enumerate(self.sectors)
                   if s["lightlevel"] == self.m.LIGHT_BEACON}
        self.assertEqual(set(self.m.BEACON_ZONES), beacons)
        self.assertIn(self.front(self.exit_line()), self.named(*self.m.BEACON_ZONES))
        for sector in self.key_sectors().values():
            self.assertIn(self.zone_of[sector], beacons)

    def test_each_key_lies_in_its_locks_colour(self):
        m = self.m
        keys = self.key_sectors()
        colours = set()
        for lock, portal in m.LOCK_PORTALS.items():
            colour = self.sectors[self.plan[portal]].get("lightcolor")
            self.assertIsNotNone(colour, portal)
            self.assertEqual(colour, self.sectors[keys[lock]].get("lightcolor"), f"lock {lock}")
            colours.add(colour)
            wearing = {self.zone_of[i] for i, s in enumerate(self.sectors)
                       if s.get("lightcolor") == colour}
            same = defaultdict(set)
            for a, ns in self.neighbours.items():
                same[a] = {b for b in ns if self.sectors[b].get("lightcolor") == colour}
            key_room = {self.zone_of[i] for i in self.flood(same, keys[lock])}
            self.assertEqual({portal} | key_room, wearing, "one patch round the key, one at the lock")
        self.assertEqual(2, len(colours))

    # --- scope -------------------------------------------------------------
    def test_the_start_and_the_keys_are_on_every_skill(self):
        m = self.m
        for ed in (m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_RED_CARD):
            found = self.things_of({ed})
            self.assertEqual(1, len(found), ed)
            for skill in range(1, 6):
                self.assertTrue(found[0][f"skill{skill}"], f"thing {ed} missing on skill {skill}")
            self.assertTrue(found[0]["single"])

    def test_the_only_special_sectors_are_the_three_secrets(self):
        m = self.m
        special = {self.zone_of[i]: s["special"] for i, s in enumerate(self.sectors) if s.get("special")}
        self.assertEqual({zone: m.SECTOR_SPECIAL_SECRET for zone in m.SECRET_ZONES}, special)
        self.assertFalse([i for i, s in enumerate(self.sectors) if s.get("damageamount")])

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.progression()[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         sorted(self.zone_of[i] for i in unreachable ^ self.props))

    def test_the_exit_is_reached_and_only_in_the_last_round(self):
        rounds = self.progression()
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z7_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        self.assertIn(exit_sector, rounds[-1][1], "the exit is never reached")
        for opened, reach, _ in rounds[:-1]:
            self.assertNotIn(exit_sector, reach, f"exit reached with only {sorted(opened)}")
        niche = self.sectors[exit_sector]
        self.assertEqual(self.m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])

    def test_no_trap_at_any_stage(self):
        for opened, reach, _held in self.progression():
            back = self.flood(self.reverse(self.adjacency(opened)), self.start)
            stranded = sorted(self.zone_of[i] for i in reach - back)
            self.assertEqual([], stranded, f"with tags {sorted(opened)} open")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        opened, reach, _ = self.progression()[-1]
        onward = self.flood(self.reverse(self.adjacency(opened)), self.front(self.exit_line()))
        self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward))

    def test_the_drops_are_left_by_stairs(self):
        """The roofs, the pit and the tunnel are left by their stairs:
        dropping is free, and each has its way back up."""
        adj = self.adjacency(set().union(*(r[0] for r in self.progression())))
        yard, roof = self.plan["z2_yard"], self.plan["z2_roof_2"]
        self.assertIn(yard, adj[roof], "a roof drops to the yard")
        self.assertNotIn(roof, adj[yard])
        chain = ["z2_yard"] + [f"z2_ramp_{n}" for n in range(5, 0, -1)] + ["z2_roof_4"]
        for low, high in zip(chain, chain[1:]):
            self.assertIn(self.plan[high], adj[self.plan[low]], f"{low} -> {high}")
        for pit, stairs in (("z5_pit_s", ("z5_pit_s_3", "z5_pit_s_2", "z5_pit_s_1", "z5_hall")),
                            ("z5_pit_n", ("z5_pit_n_3", "z5_pit_n_2", "z5_pit_n_1", "z5_hall"))):
            self.assertIn(self.plan[pit], adj[self.plan["z5_bridge"]], f"bridge -> {pit}")
            self.assertNotIn(self.plan["z5_bridge"], adj[self.plan[pit]])
            path = (pit,) + stairs
            for low, high in zip(path, path[1:]):
                self.assertIn(self.plan[high], adj[self.plan[low]], f"{low} -> {high}")
        path = ("z1_tunnel", "z1_stair_1", "z1_stair_2", "z1_stair_3", "z1_mouth", "z2_yard")
        for low, high in zip(path, path[1:]):
            self.assertIn(self.plan[high], adj[self.plan[low]], f"{low} -> {high}")

    def test_the_route_is_the_designed_one(self):
        """Four rounds: the roofs and the yellow key; the yellow door (the
        warehouse, the roundhouse, the red key and SW-A); the red door, the
        road gate and the gondolas; SW-B and the train."""
        m = self.m
        rounds = self.progression()
        self.assertEqual(4, len(rounds))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3) = rounds
        self.assertEqual({m.TAG_S1_PANEL}, set(o0), "only S1's panel before any key")
        self.assertEqual({m.LOCK_YELLOW_CARD}, set(h0), "the yellow key with no switch and no key")
        self.assertIn(self.plan["z3_frame"], r0)
        behind_yellow = self.named("z4_hall", "z4_passage", "z5_hall", "z5_hub", "z5_bridge")
        self.assertFalse(behind_yellow & r0)
        self.assertEqual({m.TAG_YELLOW_DOOR, m.TAG_D1_ROUNDHOUSE, m.TAG_D2_OFFICE,
                          m.TAG_S2_PANEL, m.TAG_S3_PANEL}, set(o1 - o0))
        self.assertTrue(behind_yellow <= r1)
        self.assertEqual({m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD}, set(h1))
        platform = self.named("z6_vestibule", "z6_platform", "z6_office", "z6_balcony")
        self.assertFalse(platform & r1, "the platform is behind the red door")
        self.assertEqual({m.TAG_RED_DOOR, m.TAG_SHUTTER, m.TAG_GONDOLAS}, set(o2 - o1))
        self.assertTrue(platform <= r2)
        self.assertNotIn(self.plan["z7_troop"], r2, "the train is shut until SW-B")
        self.assertEqual({m.TAG_HATCH}, set(o3 - o2))
        self.assertTrue(self.named("z7_troop", "z7_gun", "z7_cab") <= r3)

    def test_the_road_gate_is_a_shortcut_never_the_only_way(self):
        m = self.m
        every = set().union(*(r[0] for r in self.progression())) - {m.TAG_SHUTTER}
        self.assertIn(self.plan["z7_exit_niche"], self.reachable(every))

    def test_no_secret_and_no_gondola_is_needed(self):
        m = self.m
        every = set().union(*(r[0] for r in self.progression()))
        critical = every - {m.TAG_S1_PANEL, m.TAG_S2_PANEL, m.TAG_S3_PANEL, m.TAG_GONDOLAS,
                            m.TAG_SHUTTER}
        self.assertIn(self.plan["z7_exit_niche"], self.reachable(critical))

    # --- the keys ------------------------------------------------------------
    def test_one_yellow_and_one_red_key_on_the_route_outside_any_secret(self):
        m = self.m
        self.assertEqual(sorted([m.ED_YELLOW_CARD, m.ED_RED_CARD]),
                         sorted(t["type"] for t in self.key_things()))
        for t in self.key_things():
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[m.KEY_ZONES[t["type"]]], where)
            self.assertFalse(self.sectors[where].get("special"))

    def test_each_key_lies_alone_on_its_pedestal(self):
        for sector in self.key_sectors().values():
            here = [t for t in self.things if self.sector_at(t["x"], t["y"]) == sector]
            self.assertEqual(1, len(here), self.zone_of[sector])

    def test_the_locked_doors_open_with_their_keys_and_stay_open(self):
        m = self.m
        locked = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE]
        self.assertEqual(4, len(locked), "two doors, both faces")
        expected = {m.TAG_YELLOW_DOOR: (m.LOCK_YELLOW_CARD, "yellow_door"),
                    m.TAG_RED_DOOR: (m.LOCK_RED_CARD, "red_door")}
        for ld in locked:
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0), tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.sides[ld["sideback"]]["sector"])

    def test_the_yellow_door_is_seen_from_the_tunnels_mouth(self):
        """The first view of the yard: the yellow lock, lit, in its south
        wall, past the end of the first row of wagons."""
        eye = self.eye(3888, 1184, "z1_mouth")
        for x in (2512, 2560, 2608):
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (x, 769, z)), f"yellow door x {x} z {z}")

    def test_the_signal_box_glows_over_the_wagons_from_the_mouth(self):
        """Its yellow windows are seen over the second row from the mouth."""
        eye = self.eye(3888, 1184, "z1_mouth")
        for x in (2128, 2208):
            self.assertIsNone(self.blocked(eye, (x, 1490, 192)), f"window at x {x}")
        self.assertEqual(self.m.YELLOW, self.sectors[self.plan["prop_cabin_sills"]].get("lightcolor"))

    def test_the_red_door_is_seen_from_the_roofs_before_the_red_key(self):
        """The rake's roofs (round 0) look down on the red lock in the
        north wall."""
        eye = self.eye(2752, 1640, "z2_roof_2")
        for x in (2704, 2752, 2800):
            for z in (16, 64, 112):
                self.assertIsNone(self.blocked(eye, (x, 1919, z)), f"red door x {x} z {z}")
        self.assertIn(self.plan["z2_roof_2"], self.progression()[0][1])

    def test_the_yellow_key_is_seen_along_the_roofs(self):
        """MAP02's lesson (D58): from the rake's roofs, through the signal
        box's door, the key on its lit lever frame."""
        target = self.key_target(self.m.YELLOW_KEY_SPOT, "z3_frame")
        for x in (2400, 2560, 2900):
            self.assertIsNone(self.blocked(self.eye(x, 1600, f"z2_roof_{1 if x < 2624 else 2}"
                                                    if x < 2944 else "z2_roof_3"), target), f"x {x}")

    def test_the_red_key_is_seen_on_entering_the_roundhouse(self):
        target = self.key_target(self.m.RED_KEY_SPOT, "z5_hub")
        self.assertIsNone(self.blocked(self.eye(1632, 512, "z5_porch"), target))
        self.assertIsNone(self.blocked(self.eye(1560, 512, "z5_hall"), target))

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        m = self.m
        views = ((self.eye(2400, 1600, "z2_roof_1"), m.YELLOW_KEY_SPOT),
                 (self.eye(1632, 512, "z5_porch"), m.RED_KEY_SPOT))
        for (x0, y0, _z), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"{t['type']} at ({t['x']}, {t['y']})")

    def test_the_signal_box_is_reached_by_the_roofs_only(self):
        """Its windows are 32 over its floor and 160 over the yard: the one
        way in is the step from the rake's west roof."""
        adj = self.adjacency(set())
        cabin = self.named("z3_cabin", "z3_frame", "z3_step")
        into = {a for a, dsts in adj.items() for b in dsts if b in cabin and a not in cabin}
        self.assertEqual(self.named("z2_roof_1"), into)

    # --- switches --------------------------------------------------------------
    def switch_lines(self):
        return [ld for ld in self.lines if "sideback" not in ld
                and ld.get("special") == SPECIAL_DOOR_OPEN]

    def test_every_switch_is_a_real_face_drawn_once_and_one_shot(self):
        m = self.m
        switches = self.switch_lines() + [self.exit_line()]
        faces = [self.sides[ld["sidefront"]].get("texturemiddle") for ld in switches]
        self.assertEqual(3, len(switches))
        self.assertEqual(len(faces), len(set(faces)), "one variant per switch")
        for ld, face in zip(switches, faces):
            self.assertIn(face, m.SWITCH_FACES)
            self.assertTrue(_packed(face.replace("SDSW1", "SDSW2")), f"{face}'s ON twin")
            self.assertTrue(ld.get("playeruse"))
            self.assertFalse(ld.get("repeatspecial"), "a switch stays on")
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.SWITCH_WIDTH, abs(bx - ax) + abs(by - ay))
            s = self.sectors[self.front(ld)]
            self.assertEqual(m.SWITCH_HEIGHT, s["heightceiling"] - s["heightfloor"])
        self.assertEqual(m.EXIT_FACE, self.sides[self.exit_line()["sidefront"]]["texturemiddle"])

    def test_each_switch_opens_what_the_design_says(self):
        m = self.m
        found = {ld["arg0"]: self.front(ld) for ld in self.switch_lines()}
        self.assertEqual({m.TAG_SHUTTER: self.plan["z5_swa_niche"],
                          m.TAG_HATCH: self.plan["z6_office"]}, found)
        self.assertEqual(self.named("shutter"), self.doors[m.TAG_SHUTTER])
        self.assertEqual(self.named("z7_hatch"), self.doors[m.TAG_HATCH])

    def test_sw_a_stands_beside_the_road_gate(self):
        """In the road's own wall: pressed, it shows the gate rising."""
        sw_a = [ld for ld in self.switch_lines() if ld["arg0"] == self.m.TAG_SHUTTER][0]
        (ax, ay), (bx, by) = self.line_points(sw_a)
        self.assertLessEqual(math.dist(((ax + bx) / 2, (ay + by) / 2), (1776, 1184)), 128)
        eye = self.eye((ax + bx) // 2, ay - 32, "z5_road")
        for y in (1136, 1184, 1232):
            self.assertIsNone(self.blocked(eye, (1759, y, 64)), f"gate y {y}")

    def test_the_road_gate_is_wall_from_the_yard(self):
        """MAP02's SH, MAP03's shutter: from the yard it wears the yard's
        brick, a wall until SW-A opens it; no special on either face."""
        m = self.m
        shutter = self.plan["shutter"]
        for ld in self.lines:
            if "sideback" in ld and shutter in self._pair(ld):
                self.assertFalse(ld.get("special"))
                yard_side = [s for s in (ld["sidefront"], ld["sideback"])
                             if self.sides[s]["sector"] == self.plan["z2_rails_main"]
                             or self.sides[s]["sector"] == self.plan["z2_yard"]]
                for side in yard_side:
                    self.assertEqual(m.BRICK, self.sides[side].get("texturetop"))

    def test_the_hatch_is_seen_from_sw_b(self):
        """SW-B in the stationmaster's office looks out at the train's rear
        hatch across the platform: the press shows what it opened."""
        eye = self.eye(3072, 2000, "z6_office")
        for y in (2480, 2528, 2560):
            self.assertIsNone(self.blocked(eye, (2305, y, 112)), f"hatch y {y}")

    def test_the_exit_is_seen_through_the_open_hatch(self):
        eye = self.eye(2400, 2528, "z6_balcony")
        opened = {self.m.TAG_HATCH}
        for z in (96, 128, 160):
            self.assertIsNone(self.blocked(eye, (625, 2528, z), opened), f"z {z}")

    # --- doors -----------------------------------------------------------------
    def test_every_door_opens_tall_enough(self):
        for index in sorted(self.door_sectors):
            s = self.sectors[index]
            opened = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[index])
                      - DOOR_OPENS_BELOW_CEILING)
            self.assertGreaterEqual(opened - s["heightfloor"], PLAYER_HEIGHT, self.zone_of[index])

    def test_no_press_can_consume_a_gate(self):
        for i, ld in enumerate(self.lines):
            special = ld.get("special")
            if special not in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE,
                               self.m.SPECIAL_DOOR_LOCKED_RAISE):
                continue
            if "sideback" in ld:
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
            else:
                self.assertEqual(SPECIAL_DOOR_OPEN, special, f"linedef {i}")

    # --- the gondolas: the red key's counter-attack ---------------------------------
    def test_the_red_key_drops_the_gondolas_sides(self):
        """The red key carries Floor_LowerToLowest on a tag no line carries;
        the tag is the two gondolas' sides, each a wagon-side panel a boxcar
        high in a wagon's shell, facing the main track; once lowered, each gondola
        opens onto the yard by a step."""
        m = self.m
        key = self.things_of({m.ED_RED_CARD})[0]
        self.assertEqual((m.SPECIAL_FLOOR_LOWER_TO_LOWEST, m.TAG_GONDOLAS, m.FLOOR_SPEED),
                         (key["special"], key["arg0"], key["arg1"]))
        self.assertFalse([ld for ld in self.lines if ld.get("special") and ld.get("arg0") == m.TAG_GONDOLAS])
        self.assertEqual(self.named(*(f"{n}_side" for n in m.GONDOLAS)), self.lifts[m.TAG_GONDOLAS])
        shut, opened = self.adjacency(set()), self.adjacency({m.TAG_GONDOLAS})
        yard = self.flood(self.adjacency({m.TAG_GONDOLAS}), self.plan["z2_yard"])
        for name in m.GONDOLAS:
            bed, side = self.plan[name], self.plan[f"{name}_side"]
            self.assertEqual(m.WAGON_SIDE, self.sides[[ld for ld in self.lines if "sideback" in ld and
                                                 side in self._pair(ld)][0]["sidefront"]].get("texturebottom"))
            self.assertNotIn(side, shut[bed], f"{name} is shut until the key")
            self.assertIn(side, opened[bed], f"{name} opens")
            self.assertIn(bed, yard)
        rounds = self.progression()
        first = next(k for k, (o, _r, _h) in enumerate(rounds) if m.TAG_GONDOLAS in o)
        self.assertIn(self.plan["z5_hub"], rounds[first - 1][1], "the key is reached first")
        for name in m.GONDOLAS:
            self.assertNotIn(self.plan[name], rounds[first - 1][1], f"{name} open early")

    def test_every_gondola_holds_a_fight_on_every_skill(self):
        m = self.m
        for name in m.GONDOLAS:
            for skill in SKILLS:
                inside = [t for t in self.on(skill, self.monsters())
                          if self.sector_at(t["x"], t["y"]) == self.plan[name]]
                self.assertTrue(inside, f"{name} is empty on skill {skill}")

    # --- population --------------------------------------------------------
    def test_every_thing_stands_in_the_zone_its_table_names(self):
        m = self.m
        rows = ([(z, k, x, y) for z, k, x, y, *_ in m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in m.ITEMS + m.SECRET_ITEMS])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is in {self.zone_of.get(self.sector_at(x, y))}")

    def test_the_monsters_are_the_bestiarys_own_numbers_in_mapinfo(self):
        assigned = _doomednums()
        for ednum, name in self.m.MONSTER_CLASSES.items():
            self.assertEqual(name, assigned.get(ednum), ednum)
        for ednum in self.m.ROUTE_WEAPONS + self.m.SECRET_WEAPONS:
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertEqual(set(self.m.MONSTER_CLASSES), {t["type"] for t in self.monsters()},
                         "every class but the General, who fell at Tankograd")

    def test_every_monster_has_room_for_its_body(self):
        for t in self.monsters():
            radius, height = self.body[t["type"]]
            x, y = t["x"], t["y"]
            under = {self.sector_at(x + dx, y + dy) for dx in (-radius, radius) for dy in (-radius, radius)}
            under.add(self.sector_at(x, y))
            where = f"{t['type']} at ({x}, {y})"
            self.assertNotIn(None, under, f"{where} is in a wall")
            self.assertFalse(under & self.unwalkable,
                             f"{where} overlaps {[self.zone_of[s] for s in under & self.unwalkable]}")
            floors = [self.sectors[s]["heightfloor"] for s in under]
            ceils = [self.sectors[s]["heightceiling"] for s in under]
            self.assertLessEqual(max(floors) - min(floors), MAX_STEP_UP, where)
            self.assertGreaterEqual(min(ceils) - max(floors), height, where)

    def test_no_two_monsters_start_inside_each_other(self):
        bodies = self.monsters()
        for i, a in enumerate(bodies):
            for b in bodies[i + 1:]:
                reach = self.body[a["type"]][0] + self.body[b["type"]][0]
                apart = abs(a["x"] - b["x"]) >= reach or abs(a["y"] - b["y"]) >= reach
                self.assertTrue(apart, f"{a['type']} at ({a['x']}, {a['y']}) and "
                                       f"{b['type']} at ({b['x']}, {b['y']})")

    def test_every_pickup_can_be_picked_up(self):
        reach = self.progression()[-1][1]
        for t in self.things:
            if t["type"] in self.monster_numbers or t["type"] == self.m.ED_PLAYER1_START:
                continue
            s = self.sector_at(t["x"], t["y"])
            where = f"thing {t['type']} at ({t['x']}, {t['y']})"
            self.assertIsNotNone(s, f"{where} is in a wall")
            self.assertNotIn(s, self.unwalkable, f"{where} on {self.zone_of[s]}")
            self.assertIn(s, reach, f"{where} in {self.zone_of[s]}")

    def test_skill_flags_come_in_doom_pairs_and_nothing_is_on_no_skill(self):
        for t in self.things:
            self.assertTrue(any(t[f"skill{n}"] for n in range(1, 6)), t)
            self.assertEqual(t["skill1"], t["skill2"], t)
            self.assertEqual(t["skill4"], t["skill5"], t)

    def test_monsters_per_skill_and_nested(self):
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    def test_the_tables_factions_are_the_classes_own(self):
        m = self.m
        for kind, ednum in m.MONSTER_KINDS.items():
            faction = self.faction[ednum]
            if kind in m.REICH:
                self.assertEqual("REICH", faction, kind)
            elif kind in m.LEGION:
                self.assertEqual("LEGION", faction, kind)
            else:
                self.assertEqual("BOTH", faction, kind)

    def test_both_factions_hold_the_map_where_the_design_puts_them(self):
        """The Reich the tunnel, the yard and the roundhouse; the Legion the
        signal box and the warehouse; both on the platform and in the train
        on every skill. The gondolas are the counter-attack, mixed."""
        m = self.m
        seen = defaultdict(set)
        for zone, kind, *_ in m.MONSTERS:
            if zone.startswith(m.GONDOLA_PREFIX):
                continue
            faction = self.faction[m.MONSTER_KINDS[kind]]
            if zone.startswith(m.LEGION_GROUND):
                self.assertNotEqual("REICH", faction, f"{kind} in {zone}")
                seen["legion"].add(faction)
            elif zone.startswith(m.REICH_GROUND):
                self.assertNotEqual("LEGION", faction, f"{kind} in {zone}")
                seen["reich"].add(faction)
            else:
                self.assertTrue(zone.startswith(m.BOTH_GROUND), zone)
        self.assertIn("LEGION", seen["legion"])
        self.assertIn("REICH", seen["reich"])
        platform = self.named("z6_platform")
        for skill in SKILLS:
            here = {self.faction[t["type"]] for t in self.on(skill, self.monsters())
                    if self.sector_at(t["x"], t["y"]) in platform}
            self.assertTrue({"LEGION", "REICH"} <= here, f"skill {skill}: {here}")

    def test_the_intensity_rises(self):
        """Ritmo creciente: the hit points met in each round of the route
        grow round on round on every skill, the platform's the heaviest."""
        rounds = self.progression()
        for skill in SKILLS:
            seen, per_round = set(), []
            for _opened, reach, _held in rounds:
                new = reach - seen
                per_round.append(sum(self.hit_points[t["type"]] for t in self.on(skill, self.monsters())
                                     if self.sector_at(t["x"], t["y"]) in new))
                seen = reach
            self.assertLess(per_round[0], per_round[1], f"skill {skill}: {per_round}")
            self.assertLess(per_round[1], per_round[2], f"skill {skill}: {per_round}")

    def test_the_heavies(self):
        """A Panzermensch on the platform on every skill, one by the
        turntable from medium up, one in the gun wagon on hard; the heavy
        Panzermensch on the platform on hard only; Doughboys in the
        warehouse and on the platform."""
        m = self.m
        pz = self.things_of({m.ED_PANZERMENSCH})
        self.assertEqual({2: 1, 3: 2, 4: 3}, {s: len(self.on(s, pz)) for s in SKILLS})
        every = [t for t in pz if t["skill2"]]
        self.assertEqual(self.plan["z6_platform"], self.sector_at(every[0]["x"], every[0]["y"]))
        heavy = self.things_of({m.ED_PANZER_HEAVY})
        self.assertEqual({2: 0, 3: 0, 4: 1}, {s: len(self.on(s, heavy)) for s in SKILLS})
        self.assertEqual(self.named("z6_platform"), {self.sector_at(t["x"], t["y"]) for t in heavy})
        db = self.things_of({m.ED_DOUGHBOY})
        self.assertEqual(self.named("z4_hall", "z6_platform"),
                         {self.sector_at(t["x"], t["y"]) for t in db if t["skill2"]})

    def test_the_weapons_are_on_every_skill_on_the_route(self):
        """Pistol start (episode 2 opens here): the IZh in the tunnel before
        the first fight, the PPSh in the warehouse office, the RPG-7 at the
        roundhouse's door before any Panzermensch; the ROKS-3 in S2 only."""
        m = self.m
        rounds = self.progression()
        for ednum, zone, stage in ((m.ED_IZH, "z1_tunnel", 0), (m.ED_PPSH, "z4_office", 1),
                                   (m.ED_RPG7, "z5_hall", 1), (m.ED_ROKS3, "s2_store", 1)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertIn(where, rounds[stage][1], f"weapon {ednum} not reached by round {stage}")
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82, 21007}))
        izh = self.things_of({m.ED_IZH})[0]
        self.assertGreater(izh["x"], max(t["x"] for t in self.monsters()), "before the first fight")
        rpg = self.things_of({m.ED_RPG7})[0]
        porch = (1632, 512)
        for t in self.things_of({m.ED_PANZERMENSCH}):
            if self.sector_at(t["x"], t["y"]) in self.named("z5_hall", "z5_rails_stall"):
                self.assertLess(math.dist(porch, (rpg["x"], rpg["y"])), math.dist(porch, (t["x"], t["y"])))

    def test_consumables_scale_down(self):
        m = self.m
        fixed = (self.monster_numbers | set(m.ROUTE_WEAPONS) | set(m.SECRET_WEAPONS)
                 | {m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_RED_CARD})
        for kind in {t["type"] for t in self.things} - fixed:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]]
                   for t in self.on(skill, self.monsters()))

    def on_route(self, things):
        off = self.named(*self.m.SECRET_ZONES)
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in off]

    def ammo_placed(self, skill):
        placed = self.on_route(self.on(skill, self.things))
        return sum(SHELLS_GIVEN.get(t["type"], 0)
                   + ROUNDS_GIVEN.get(t["type"], 0) / ROUNDS_PER_SHELL
                   + ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                   + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL for t in placed)

    def test_g3_8_the_ammo_budget(self):
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            self.assertGreaterEqual(have, G3_8_MARGIN * need, f"skill {skill}: {have} for {need}")
        self.assertLess(self.ammo_placed(4), 3 * self.ammo_needed(4))

    def start_rounds(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        rounds = self.progression()
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = self.start_rounds() * PPSH_AVERAGE
            for stage, (_opened, reach, _held) in enumerate(rounds):
                here = [t for t in self.on_route(self.on(skill, self.things))
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                hp_so_far += sum(self.hit_points.get(t["type"], 0) for t in here)
                damage += sum(SHELLS_GIVEN.get(t["type"], 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(t["type"], 0) * PPSH_AVERAGE
                              + ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE
                              + CELLS_GIVEN.get(t["type"], 0) * ROKS_AVERAGE for t in here)
                self.assertGreaterEqual(damage, G3_8_MARGIN * hp_so_far, f"skill {skill}, stage {stage}")
                seen = reach

    def test_health_and_armour_on_skill_4(self):
        m = self.m
        found = Counter(t["type"] for t in self.on_route(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 7)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(0, found[m.ED_BLUE_ARMOR], "the heavy vest is S3's")

    # --- the secrets -----------------------------------------------------------
    def panel_lines(self, tag):
        return [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_OPEN and ld["arg0"] == tag]

    def test_three_secrets_each_opened_by_a_push_panel_with_a_way_back(self):
        m = self.m
        rounds = self.progression()
        for zone, tag, panel, niche, stage in (
                ("s1_store", m.TAG_S1_PANEL, "s1_panel", "z1_niche_2", 0),
                ("s2_store", m.TAG_S2_PANEL, "s2_panel", "z5_stall_3", 1),
                ("s3_store", m.TAG_S3_PANEL, "s3_panel", "s3_niche", 1)):
            lines = self.panel_lines(tag)
            self.assertEqual(2, len(lines), f"{zone}: both faces of the panel")
            self.assertIn(self.plan[niche], {self.front(ld) for ld in lines})
            for ld in lines:
                self.assertEqual(self.plan[panel], self.sides[ld["sideback"]]["sector"])
                self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial") and ld.get("secret"))
            store = self.plan[zone]
            self.assertTrue(self.sectors[store]["special"] & m.SECTOR_SPECIAL_SECRET)
            self.assertIn(store, rounds[stage][1], f"{zone} by round {stage}")
            if stage:
                self.assertNotIn(store, rounds[stage - 1][1])
            shut = set().union(*(r[0] for r in rounds)) - {tag}
            self.assertNotIn(store, self.reachable(shut), f"{zone} is entered by its panel only")
            self.assertIn(self.start, self.flood(self.adjacency(rounds[stage][0]), store),
                          f"a way back from {zone}")

    def test_each_secrets_clue_is_a_comparison_in_shadow(self):
        """MAP01's rule, a comparison and never a sign: the cable box is the
        one niche of three in shadow, its back a different panel; the dark
        stall's gate is the gate of its lit twin; the crate set back is
        darker than its row."""
        m = self.m
        niches = [self.plan[f"z1_niche_{n}"] for n in range(1, 4)]
        lights = [self.sectors[s]["lightlevel"] for s in niches]
        self.assertEqual(lights[0], lights[2])
        self.assertLess(lights[1], lights[0])
        back_y = m.S1_PANEL[1]
        for n, (x1, x2) in enumerate(m.TUNNEL_NICHES):
            if n == m.S1_NICHE_INDEX:
                continue
            backs = [ld for ld in self.lines if "sideback" not in ld and self.front(ld) == niches[n]
                     and {p[1] for p in self.line_points(ld)} == {back_y}]
            self.assertEqual([m.TUNNEL_WALL], [self.sides[ld["sidefront"]].get("texturemiddle")
                                               for ld in backs], f"niche {n + 1}'s back")
        panel_face = [ld for ld in self.panel_lines(m.TAG_S1_PANEL) if self.front(ld) == niches[1]][0]
        self.assertEqual(m.CONCRETE, self.sides[panel_face["sidefront"]]["texturetop"])
        lit, dark = self.plan["z5_stall_2"], self.plan["z5_stall_3"]
        self.assertEqual(128, self.one_sided_textures(lit)[m.STALL_DOORS])
        gate_face = [ld for ld in self.panel_lines(m.TAG_S2_PANEL) if self.front(ld) == dark][0]
        self.assertEqual(m.STALL_DOORS, self.sides[gate_face["sidefront"]]["texturetop"])
        self.assertLess(self.sectors[dark]["lightlevel"], self.sectors[lit]["lightlevel"])
        hall = self.plan["z4_hall"]
        self.assertEqual(3 * m.CRATE_WIDTH, self.one_sided_textures(hall)[m.CRATE],
                         "three crates flush with the wall, the fourth set back")
        self.assertLess(self.sectors[self.plan["s3_niche"]]["lightlevel"], self.sectors[hall]["lightlevel"])

    def test_the_secrets_hold_their_rewards_on_every_skill(self):
        m = self.m
        for zone in m.SECRET_ZONES:
            for skill in SKILLS:
                here = [t for t in self.on(skill, self.things)
                        if self.sector_at(t["x"], t["y"]) == self.plan[zone]]
                self.assertTrue(here, f"{zone} empty on skill {skill}")
                self.assertFalse([t for t in here if t["type"] in self.monster_numbers])
        s2 = {t["type"] for t in self.things if self.sector_at(t["x"], t["y"]) == self.plan["s2_store"]}
        self.assertIn(m.ED_ROKS3, s2)


if __name__ == "__main__":
    unittest.main()
