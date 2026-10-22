"""MAP09 Tunguska, episode 3's last map, v1 (docs/levels/MAP09-tunguska.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map06_red_square.py (whose helpers this file repeats, so each
map's tests stay one file). The contract:

* structure: every sector closed and clockwise, no duplicate vertex, no step
  up higher than a stair step; the campaign's biggest map;
* only approved, packed textures (and the engine's sky marker F_SKY1); every
  picture, board, flag, signal and door leaf one whole tile; the three locks
  wear their key's look;
* the open air: every outdoor zone has the sky, every closed sky block (the
  roofs) is a prop; the fallen trunks lie away from the crater, seen over and
  not climbed; the standing forest's trunks are columns of void;
* the molten pits hurt and are one step deep: walked out of;
* everything is reachable playing the map's own doors, its THREE keys in
  order, the red key's pickup (the works' closets) and the boss's death (the
  bunker's gate); no trap at any stage; the exit only after the boss dies;
* the key grammar (D58): each lock seen before its key, each key seen from
  where the player comes, in its lock's colour of light, alone on its spot,
  and no monster between;
* three secrets, none needed, each with a way back; the Hand Katyusha in S2;
* the population: per skill and nested, on the bestiary's MAPINFO numbers,
  with room for every body, factions where the design puts them, the boss at
  MAP09_BOSS_SPOT; weapons on the route, consumables scaled down, G3-8's
  ammunition margin on every skill and at every stage, health on skill 4.

Run:  python3 -m unittest tests.test_map09_tunguska -v
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
DOOR_OPENS_BELOW_CEILING = 4    # ZDoom raises a door to lowest neighbour ceiling - 4
SIGHT_STEP = 4
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}
KEY_SPRITE_MID = 8
SKY_FLAT = "F_SKY1"

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
    "SD_General": "general.zs",
    "SD_PanzermenschSchwer": "panzermensch_schwer.zs",
}
CLASS_PARENT = {"SD_PanzermenschSchwer": "SD_Panzermensch"}
# G3-8 as MAP03 measures it (tests/test_map03_factory.py): kills in IZh shells.
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8,
                  "SD_PanzermenschSchwer": 16, "SD_General": 48}
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


# MAP06's extent (docs/levels/MAP06-red-square.md section 3): the campaign's
# largest map before this one.
MAP06_EXTENT = 5552 * 4928
# Where the key grammar is checked from: the station's yard by the laboratory's
# door, the laboratory's vestibule, the forest's edge in the works, the
# refinery's yellow porch.
YARD_VIEW = (2208, 1344)
LAB_VIEW = (2016, 1408)
EDGE_VIEW = (2816, 4416)
PORCH_VIEW = (5520, 4736)


def _load_map09():
    path = PROJECT_ROOT / "src" / "maps" / "MAP09" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP09_test", path)
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


class Map09Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map09()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_platform"]
        cls.doors = defaultdict(set)
        for i, s in enumerate(cls.sectors):
            if s.get("id") and s["heightceiling"] == s["heightfloor"]:
                cls.doors[s["id"]].add(i)
        cls.door_sectors = set().union(*cls.doors.values())
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
        cls.unwalkable = cls.props | cls.door_sectors
        cls.monster_numbers = set(cls.m.MONSTER_CLASSES)
        cls.body, cls.hit_points, cls.faction = {}, {}, {}
        for ednum, name in cls.m.MONSTER_CLASSES.items():
            facts = _class_facts(name)
            cls.body[ednum] = (facts["RADIUS"], facts["HEIGHT"])
            cls.hit_points[ednum] = facts["HEALTH"]
            cls.faction[ednum] = facts["FACTION"]
        cls.rounds = cls().progression_of(kills=True)   # a bare instance: the model asserts nothing

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
        out = []
        for i, s in enumerate(self.sectors):
            ceiling = s["heightceiling"]
            if i in self.door_sectors and s["id"] in open_tags:
                ceiling = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                           - DOOR_OPENS_BELOW_CEILING)
            out.append((s["heightfloor"], ceiling))
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

    def thing_specials(self, numbers):
        """[(tag, sector)] for every thing of `numbers` carrying Door_Open."""
        return [(t["arg0"], self.sector_at(t["x"], t["y"])) for t in self.things
                if t["type"] in numbers and t.get("special") == SPECIAL_DOOR_OPEN]

    def progression_of(self, kills=True):
        """Play the map as a player can (MAP03's model): free doors open
        whenever reached; then, one round at a time, every switch and locked
        door he can work (a lock once ITS key's sector is reachable), every
        key's pickup special once the key is reachable and, with `kills`,
        every monster's death special once the monster is reachable."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        keys = self.key_sectors()
        pickups = self.thing_specials(KEY_NUMBERS)
        deaths = self.thing_specials(self.monster_numbers) if kills else []
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = {lock for lock, sector in keys.items() if sector in reach}
            free, gated = set(), set()
            gated |= {tag for tag, sector in pickups + deaths if sector in reach}
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

    def round_of(self, sector):
        return next(k for k, (_o, reach, _h) in enumerate(self.rounds) if sector in reach)

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

    def test_no_step_is_higher_than_a_stair_step(self):
        every = set().union(*(r[0] for r in self.rounds))
        h = self.heights(every)
        for a, dsts in self.adjacency(every).items():
            for b in dsts:
                self.assertLessEqual(h[b][0] - h[a][0], self.m.STEP, f"{self.zone_of[a]} -> {self.zone_of[b]}")

    def test_it_is_the_biggest_map_of_the_campaign(self):
        """D112: the campaign's last map is larger than MAP06 (5552 x 4928)."""
        xs = [v["x"] for v in self.verts]
        ys = [v["y"] for v in self.verts]
        self.assertGreater((max(xs) - min(xs)) * (max(ys) - min(ys)), MAP06_EXTENT)

    # --- textures -----------------------------------------------------------
    def test_every_texture_is_approved_and_packed(self):
        walls, flats = set(self.m.WALL_TEXTURES), set(self.m.FLAT_TEXTURES)
        used_walls = {sd[part] for sd in self.sides
                      for part in ("texturetop", "texturemiddle", "texturebottom")
                      if sd.get(part) not in (None, "-")}
        used_flats = {s[k] for s in self.sectors for k in ("texturefloor", "textureceiling")}
        self.assertEqual(set(), used_walls - walls)
        self.assertEqual(set(), used_flats - flats)
        for name in (walls | flats) - {SKY_FLAT}:
            self.assertTrue(_packed(name), f"{name} is not an installed asset")
        self.assertFalse([n for n in walls | flats if n != SKY_FLAT and not n.startswith("SD")],
                         "an IWAD texture")

    def faces_of(self, texture):
        """[(height of the face, zone)] for every drawn face wearing `texture`:
        a wall's middle, or the flank of a neighbour's raised floor as far as
        this side's ceiling lets it show."""
        out = []
        for ld in self.lines:
            sides = [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else [])
            for side in sides:
                sd = self.sides[side]
                s = self.sectors[sd["sector"]]
                if s["heightfloor"] == s["heightceiling"]:
                    continue    # a closed door, panel or block: its face is its neighbours' flank
                zone = self.zone_of[sd["sector"]]
                if "sideback" not in ld and sd.get("texturemiddle") == texture:
                    out.append((s["heightceiling"] - s["heightfloor"], zone))
                elif "sideback" in ld and sd.get("texturebottom") == texture:
                    other = self.sectors[self.sides[ld["sideback"] if side == ld["sidefront"]
                                                    else ld["sidefront"]]["sector"]]
                    if other["heightfloor"] > s["heightfloor"]:
                        top = min(other["heightfloor"], s["heightceiling"])
                        out.append((top - s["heightfloor"], zone))
        return out

    def test_every_door_leaf_and_picture_is_one_whole_tile(self):
        """Each door opens one tile high; each board, flag, signal, locker,
        turbine, armour plate and the towers' cores is exactly one tile high
        where it shows; the portal's field is exactly two."""
        m = self.m
        for tag, sectors in self.doors.items():
            for i in sectors:
                s = self.sectors[i]
                lowest = min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                self.assertEqual(m.DOOR_HEIGHT, lowest - s["heightfloor"], self.zone_of[i])
        for texture in (m.CONTROL, m.FLAG_REICH, m.FLAG_LEGION, m.SIGNAL, m.LOCKER, m.TURBINE,
                        m.ARMOUR_STAR, m.WAGON):
            faces = self.faces_of(texture)
            self.assertTrue(faces, texture)
            if texture == m.WAGON:
                # The goods wagon is one tile; the logs, huts and treeline
                # are other heights of the same planking.
                self.assertIn((m.TILE_SIZE, "z1_ballast"), faces)
                continue
            for height, zone in faces:
                self.assertEqual(m.TILE_SIZE, height, f"{texture} on {zone}")
        portal = Counter(height for height, _ in self.faces_of(m.PORTAL))
        self.assertEqual({m.TILE_SIZE, 2 * m.TILE_SIZE}, set(portal), "the cores one tile, the field two")

    def test_the_signal_is_used_once(self):
        """D107: SDSIGL1 is single use, one 64 span on a post, never tiled."""
        m = self.m
        parts = ("texturetop", "texturemiddle", "texturebottom")
        worn = [ld for ld in self.lines
                if any(m.SIGNAL in [self.sides[ld[s]].get(p) for p in parts]
                       for s in ("sidefront", "sideback") if s in ld)]
        self.assertEqual(1, len(worn))
        (a, b) = self.line_points(worn[0])
        self.assertEqual(64, abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def test_each_lock_wears_its_keys_look(self):
        m = self.m
        leaf = {m.TAG_BLUE_DOOR: m.DOOR, m.TAG_YELLOW_DOOR: m.DOOR_YELLOW, m.TAG_RED_DOOR: m.DOOR_RED}
        for ld in self.lines:
            if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE:
                self.assertEqual(leaf[ld["arg0"]], self.sides[ld["sidefront"]]["texturetop"])

    def test_the_outdoors_has_the_sky_and_every_sky_block_is_a_prop(self):
        for name in ("z1_ballast", "z1_yard", "z1_platform", "z2_taiga", "z3_yard", "z4_forest",
                     "z5_works", "z7_rim", "z8_floor"):
            self.assertEqual(SKY_FLAT, self.sectors[self.plan[name]]["textureceiling"], name)
        for i, s in enumerate(self.sectors):
            if s["textureceiling"] == SKY_FLAT and s["heightceiling"] == s["heightfloor"]:
                self.assertIn(i, self.props, self.zone_of[i])
                self.assertFalse(s.get("id"), self.zone_of[i])

    def test_the_fallen_trunks_lie_away_from_the_crater(self):
        """The 1908 blast laid the taiga flat, every trunk pointing away from
        the epicentre: each log's long axis is the one nearest its bearing
        from CRATER_CENTRE; each is a prop LOG high, over a step and under the
        eye, so the player walks round it and sees over it."""
        m = self.m
        self.assertLess(MAX_STEP_UP, m.LOG)
        self.assertLess(m.LOG, VIEW_HEIGHT)
        cx, cy = m.CRATER_CENTRE
        ways = Counter()
        for n, (x, y, length) in enumerate(m.LOGS, start=1):
            name = f"prop_z2_log_{n}"
            self.assertEqual(m.LOG, self.sectors[self.plan[name]]["heightfloor"], name)
            bearing = math.degrees(math.atan2(y - cy, x - cx)) % 180
            axis = {"ew": 0, "ne": 45, "ns": 90, "se": 135}[m.log_direction(x, y)]
            self.assertLessEqual(min(abs(bearing - axis), 180 - abs(bearing - axis)), 22.5, name)
            rects = m.log_rects(x, y, length)
            xs = [r[0] for r in rects] + [r[2] for r in rects]
            ys = [r[1] for r in rects] + [r[3] for r in rects]
            span = max(max(xs) - min(xs), max(ys) - min(ys))
            self.assertGreaterEqual(span, length * 0.6, name)
            self.assertEqual(self.plan[name], self.sector_at(x, y), f"{name}: its middle is its own")
            ways[m.log_direction(x, y)] += 1
        self.assertTrue({"ns", "ne", "se"} <= set(ways), ways)

    def test_the_standing_forest_is_columns_of_void(self):
        m = self.m
        trunks = m.trunk_spots()
        self.assertGreaterEqual(len(trunks), 40)
        forest = self.plan["z4_forest"]
        for x, y in trunks:
            self.assertIsNone(self.sector_at(x, y), (x, y))
            self.assertEqual(forest, self.sector_at(x + m.TRUNK // 2 + 8, y), (x, y))
        cx1, cy1, cx2, cy2 = m.CLEARING
        self.assertEqual(forest, self.sector_at((cx1 + cx2) // 2, (cy1 + cy2) // 2))

    def test_the_molten_pits_hurt_and_are_walked_out_of(self):
        m = self.m
        hurting = [i for i, s in enumerate(self.sectors) if s.get("damageamount")]
        self.assertEqual(len(m.WORKS_LAVA) + len(m.CRATER_LAVA) + 1, len(hurting))
        for i in hurting:
            s = self.sectors[i]
            zone = self.zone_of[i]
            self.assertEqual((m.LAVA_DAMAGE, m.LAVA_DAMAGE_INTERVAL, m.MOLTEN),
                             (s["damageamount"], s["damageinterval"], s["texturefloor"]), zone)
            walkable = [n for n in self.neighbours[i] if n not in self.unwalkable]
            self.assertTrue(walkable, zone)
            for n in walkable:
                self.assertEqual(m.STEP, self.sectors[n]["heightfloor"] - s["heightfloor"],
                                 f"{zone} -> {self.zone_of[n]}")

    def test_the_portal_stands_at_the_crater_centre(self):
        m = self.m
        self.assertEqual(self.plan["prop_z8_portal"], self.sector_at(*m.CRATER_CENTRE))
        s = self.sectors[self.plan["z8_floor"]]
        self.assertEqual(m.CRATER_FLOOR, s["heightfloor"])
        self.assertEqual(-m.STEP * (m.TERRACES + 1), m.CRATER_FLOOR)

    # --- light -----------------------------------------------------------------
    def test_every_light_is_in_range(self):
        for i, s in enumerate(self.sectors):
            self.assertTrue(self.m.LIGHT_MIN <= s["lightlevel"] <= self.m.LIGHT_MAX, self.zone_of[i])

    def test_the_beacon_light_is_spent_on_locks_keys_and_exit_only(self):
        beacons = {self.zone_of[i] for i, s in enumerate(self.sectors) if s["lightlevel"] == self.m.LIGHT_BEACON}
        self.assertEqual(set(self.m.BEACON_ZONES), beacons)

    def test_each_key_lies_in_its_locks_colour(self):
        m = self.m
        colour = {m.LOCK_BLUE_CARD: m.BLUE, m.LOCK_YELLOW_CARD: m.YELLOW, m.LOCK_RED_CARD: m.RED}
        coloured = defaultdict(set)
        for i, s in enumerate(self.sectors):
            if "lightcolor" in s:
                coloured[s["lightcolor"]].add(self.zone_of[i])
        for lock, sector in self.key_sectors().items():
            self.assertIn(self.zone_of[sector], coloured[colour[lock]])
            self.assertIn(m.LOCK_PORTALS[lock], coloured[colour[lock]])
        self.assertEqual(set(colour.values()), set(coloured))

    # --- reachability and no softlock --------------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.rounds[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         sorted(self.zone_of[i] for i in unreachable ^ self.props))

    def test_the_route_is_the_designed_one(self):
        """Five rounds: the railhead, the taiga and the station (the blue
        key); the blue gate (the forest, the works, the yellow key); the
        yellow door (the refinery, the red key); the red gate with the
        closets the red key sprang (the crater); the boss's death (the
        bunker)."""
        m = self.m
        r = self.rounds
        self.assertEqual(5, len(r))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3), (o4, r4, h4) = r
        self.assertEqual({m.TAG_S1_PANEL, m.TAG_S2_PANEL}, set(o0), "the panels open whether found or not")
        self.assertEqual({m.LOCK_BLUE_CARD}, set(h0))
        self.assertFalse(self.named("z4_forest") & r0, "the forest is behind the blue gate")
        self.assertEqual({m.TAG_BLUE_DOOR, m.TAG_S3_PANEL}, set(o1 - o0))
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD}, set(h1))
        self.assertTrue(self.named("z4_forest", "z5_works", "z5_key_top") <= r1)
        self.assertFalse(self.named("z6_refinery") & r1)
        self.assertEqual({m.TAG_YELLOW_DOOR}, set(o2 - o1))
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD}, set(h2))
        self.assertFalse(self.named("z7_rim", "closet_z5_w", "closet_z5_e") & r2)
        self.assertEqual({m.TAG_RED_DOOR, m.TAG_AMBUSH}, set(o3 - o2))
        self.assertTrue(self.named("z7_rim", "z8_floor", "closet_z5_w", "closet_z5_e") <= r3)
        self.assertFalse(self.named(*m.EXIT_ZONES) & r3, "the exit is behind the boss's gate")
        self.assertEqual({m.TAG_BOSS_EXIT}, set(o4 - o3))
        self.assertTrue(self.named(*m.EXIT_ZONES) <= r4)

    def test_the_exit_is_reached_only_after_the_boss_dies(self):
        m = self.m
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z9_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        alive = self.progression_of(kills=False)
        self.assertNotIn(exit_sector, alive[-1][1], "the exit without killing the boss")
        self.assertIn(exit_sector, self.rounds[-1][1])
        niche = self.sectors[exit_sector]
        self.assertEqual(m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])
        self.assertEqual(m.EXIT_FACE, self.sides[self.exit_line()["sidefront"]]["texturemiddle"])

    def test_no_line_opens_the_bosss_gate_or_the_closets(self):
        m = self.m
        for ld in self.lines:
            if ld.get("special"):
                self.assertNotIn(ld.get("arg0"), (m.TAG_BOSS_EXIT, m.TAG_AMBUSH), ld)
        gate = self.plan["z9_gate"]
        faces = [ld for ld in self.lines if "sideback" in ld and gate in self._pair(ld)]
        self.assertEqual(2, len(faces))
        for ld in faces:
            self.assertEqual(m.GATE, self.sides[ld["sidefront"]]["texturetop"])

    def test_no_trap_at_any_stage(self):
        for kills in (False, True):
            for opened, reach, _held in self.progression_of(kills):
                back = self.flood(self.reverse(self.adjacency(opened)), self.start)
                stranded = sorted(self.zone_of[i] for i in reach - back)
                self.assertEqual([], stranded, f"with tags {sorted(opened)} open, kills={kills}")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        opened, reach, _ = self.rounds[-1]
        onward = self.flood(self.reverse(self.adjacency(opened)), self.front(self.exit_line()))
        self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward))

    def test_no_secret_is_needed(self):
        m = self.m
        every = set().union(*(r[0] for r in self.rounds))
        critical = every - set(m.SECRET_PANEL_TAGS)
        self.assertIn(self.plan["z9_exit_niche"], self.reachable(critical))

    # --- the keys ------------------------------------------------------------
    def test_three_keys_on_the_route_outside_any_secret_each_alone(self):
        m = self.m
        self.assertEqual(sorted(m.KEY_LOCKS), sorted(t["type"] for t in self.key_things()))
        for t in self.key_things():
            sector = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[m.KEY_ZONES[t["type"]]], sector)
            self.assertFalse(self.sectors[sector].get("special"))
            here = [u for u in self.things if self.sector_at(u["x"], u["y"]) == sector]
            self.assertEqual(1, len(here), self.zone_of[sector])
            for skill in range(1, 6):
                self.assertTrue(t[f"skill{skill}"])

    def test_the_locked_doors_open_with_their_keys_and_stay_open(self):
        m = self.m
        locked = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE]
        self.assertEqual(6, len(locked), "three doors, both faces")
        expected = {m.TAG_BLUE_DOOR: (m.LOCK_BLUE_CARD, "z4_blue_door"),
                    m.TAG_YELLOW_DOOR: (m.LOCK_YELLOW_CARD, "z6_yellow_door"),
                    m.TAG_RED_DOOR: (m.LOCK_RED_CARD, "z7_red_door")}
        for ld in locked:
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0), tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.sides[ld["sideback"]]["sector"])

    def gate_seen(self, eye, points, what):
        for x, y in points:
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (x, y, z)), f"{what}: ({x}, {y}) z {z}")

    def test_the_blue_gate_is_seen_from_the_yard_before_the_laboratory(self):
        m = self.m
        bx1, bx2 = m.BLUE_GATE_X
        y = m.FENCE_Y[0] + 31
        self.gate_seen(self.eye(*YARD_VIEW, "z3_yard"), [(x, y) for x in (bx1 + 32, bx1 + 64, bx2 - 32)],
                       "the blue gate")
        self.assertEqual(0, self.round_of(self.sector_at(*YARD_VIEW)))

    def test_the_blue_key_is_seen_from_the_laboratorys_door(self):
        target = self.key_target(self.m.BLUE_KEY_SPOT, "z3_key_bench")
        self.assertIsNone(self.blocked(self.eye(*LAB_VIEW, "z3_lab_vest"), target))

    def test_the_works_show_both_locks_and_the_yellow_key_from_the_forests_edge(self):
        """Stepping out of the forest: the red gate in the crater's wall, the
        refinery's yellow door and the yellow key on the derrick, at once."""
        m = self.m
        eye = self.eye(*EDGE_VIEW, "z5_edge")
        rx1, rx2 = m.RED_GATE_X
        self.gate_seen(eye, [(x, m.CONTAINMENT_Y[1] - 1) for x in (rx1 + 32, rx1 + 64, rx2 - 32)],
                       "the red gate")
        yy1, yy2 = m.YELLOW_DOOR_Y
        self.gate_seen(eye, [(m.REFINERY_WALL_X[0] + 31, y) for y in (yy1 + 32, yy1 + 64, yy2 - 32)],
                       "the yellow door")
        self.assertIsNone(self.blocked(eye, self.key_target(m.YELLOW_KEY_SPOT, "z5_key_top")))
        self.assertEqual(1, self.round_of(self.sector_at(*EDGE_VIEW)))

    def test_the_red_key_is_seen_from_the_yellow_door(self):
        target = self.key_target(self.m.RED_KEY_SPOT, "z6_key_dais")
        self.assertIsNone(self.blocked(self.eye(*PORCH_VIEW, "z6_yellow_porch"), target))

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        m = self.m
        views = ((LAB_VIEW, m.BLUE_KEY_SPOT), (EDGE_VIEW, m.YELLOW_KEY_SPOT), (PORCH_VIEW, m.RED_KEY_SPOT))
        for (x0, y0), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"monster {t['type']} at ({t['x']}, {t['y']}) "
                                             f"on the view to {(x1, y1)}")

    def test_the_exit_is_seen_from_the_bunkers_gate(self):
        m = self.m
        x = (m.EXIT_NICHE[0] + m.EXIT_NICHE[2]) // 2
        eye = self.eye(x, m.CRATER[1] - 16, "z9_exit_porch")
        self.assertIsNone(self.blocked(eye, (x, m.EXIT_NICHE[1] + 1, 64), {m.TAG_BOSS_EXIT}))

    def test_every_door_opens_tall_enough(self):
        every = set().union(*(r[0] for r in self.rounds))
        h = self.heights(every)
        for i in self.door_sectors:
            self.assertGreaterEqual(h[i][1] - h[i][0], PLAYER_HEIGHT, self.zone_of[i])

    # --- the boss and the ambush ---------------------------------------------------
    def test_the_boss_stands_at_his_named_spot_on_every_skill(self):
        m = self.m
        ed = m.MONSTER_KINDS[m.BOSS_KIND]
        bosses = self.things_of({ed})
        self.assertEqual(1, len(bosses))
        b = bosses[0]
        self.assertEqual(m.MAP09_BOSS_SPOT, (b["x"], b["y"]))
        self.assertTrue(all(b[f"skill{n}"] for n in range(1, 6)))
        special, args = m.BOSS_DEATH_SPECIAL
        self.assertEqual((SPECIAL_DOOR_OPEN, m.TAG_BOSS_EXIT), (special, args[0]))
        self.assertEqual((special,) + args[:2], (b["special"], b["arg0"], b["arg1"]))
        self.assertEqual("z8_floor", self.zone_of[self.sector_at(b["x"], b["y"])])
        self.assertEqual(max(self.hit_points.values()), self.hit_points[ed], "the strongest thing here")
        self.assertEqual([(m.TAG_BOSS_EXIT, self.sector_at(b["x"], b["y"]))],
                         self.thing_specials(self.monster_numbers), "one death special, his")

    def test_the_crater_is_his_size(self):
        """He never has to pass a door to fight: the crater's sky is far over
        him and its terraces and floor are open."""
        m = self.m
        height = self.body[m.MONSTER_KINDS[m.BOSS_KIND]][1]
        self.assertGreater(m.CRATER_SKY + m.CRATER_FLOOR, 3 * height)
        x1, y1, x2, y2 = m.CRATER
        self.assertGreaterEqual(min(x2 - x1, y2 - y1), 2048)

    def test_the_red_key_springs_the_works_closets(self):
        m = self.m
        red = self.things_of({m.ED_RED_CARD})[0]
        self.assertEqual((SPECIAL_DOOR_OPEN, m.TAG_AMBUSH), (red["special"], red["arg0"]))
        closets = [n for n in self.plan if n.startswith(m.CLOSET_PREFIX) and not n.endswith("_door")]
        self.assertEqual(2, len(closets))
        for name in closets:
            door = self.plan[f"{name}_door"]
            self.assertEqual(m.TAG_AMBUSH, self.sectors[door]["id"])
            self.assertIn(self.plan["z5_works"], self.neighbours[door])
            self.assertTrue([t for t in self.on(2, self.monsters())
                             if self.sector_at(t["x"], t["y"]) == self.plan[name]], f"{name} empty on 2")
            self.assertEqual(3, self.round_of(self.plan[name]))

    # --- secrets ---------------------------------------------------------------
    def test_three_secrets_each_behind_a_push_panel_with_a_way_back(self):
        m = self.m
        special = {self.zone_of[i] for i, s in enumerate(self.sectors) if s.get("special")}
        self.assertEqual(set(m.SECRET_ZONES), special)
        for i, s in enumerate(self.sectors):
            if s.get("special"):
                self.assertEqual(m.SECTOR_SPECIAL_SECRET, s["special"])
        panels = [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_OPEN and "sideback" in ld]
        self.assertEqual(6, len(panels), "three panels, both faces")
        for ld in panels:
            self.assertTrue(ld.get("secret") and ld.get("playeruse") and ld.get("repeatspecial"))
            self.assertIn(ld["arg0"], m.SECRET_PANEL_TAGS)
        self.assertEqual(0, self.round_of(self.plan["s1_store"]))
        self.assertEqual(0, self.round_of(self.plan["s2_store"]))
        self.assertEqual(1, self.round_of(self.plan["s3_store"]))

    def test_s2_holds_the_hand_katyusha_and_nothing_else_does(self):
        m = self.m
        found = self.things_of({m.ED_HAND_KATYUSHA})
        self.assertEqual(1, len(found))
        self.assertEqual(self.plan["s2_store"], self.sector_at(found[0]["x"], found[0]["y"]))
        self.assertTrue(all(found[0][f"skill{n}"] for n in range(1, 6)))

    def row_faces(self, axis, coord, lo, hi):
        """{(lo, hi): middle texture} of the one-sided lines on a wall run."""
        out = {}
        for ld in self.lines:
            if "sideback" in ld:
                continue
            (x1, y1), (x2, y2) = self.line_points(ld)
            if axis == "h" and y1 == y2 == coord and lo <= min(x1, x2) and max(x1, x2) <= hi:
                out[(min(x1, x2), max(x1, x2))] = self.sides[ld["sidefront"]].get("texturemiddle")
            if axis == "v" and x1 == x2 == coord and lo <= min(y1, y2) and max(y1, y2) <= hi:
                out[(min(y1, y2), max(y1, y2))] = self.sides[ld["sidefront"]].get("texturemiddle")
        return out

    def test_each_clue_is_a_comparison_in_shadow(self):
        """MAP01's rule: a clue is a comparison, never a sign. Each panel is
        the odd one of a row of the same thing (lockers, boards, recesses),
        set back and in shadow."""
        m = self.m
        for niche in ("s1_niche", "s2_niche", "s3_niche"):
            self.assertEqual(m.LIGHT_CLUE, self.sectors[self.plan[niche]]["lightlevel"], niche)
        # S1: two lockers either side of the niche, the panel a locker too.
        lockers = [sd for sd in self.sides if sd.get("texturebottom") == m.LOCKER
                   or sd.get("texturetop") == m.LOCKER]
        self.assertTrue(lockers)
        # S2: two boards on the room's wall, the panel a board too.
        boards = self.row_faces("h", m.BOARDS_Y, m.BOARDS_X[0], m.BOARDS_X[-1])
        self.assertEqual(2, sum(1 for t in boards.values() if t == m.CONTROL))
        # S3: three recesses 16 deep, the fourth (the niche) 32.
        recesses = [n for n in self.plan if n.startswith("z5_recess_")]
        self.assertEqual(3, len(recesses))
        x1, y1, x2, y2 = m.S3_X[0], m.WORKS_NORTH, m.S3_X[1], m.WORKS_NORTH + 2 * m.NICHE_DEPTH
        self.assertEqual(self.plan["s3_niche"], self.sector_at((x1 + x2) // 2, y2 - 8))
        for name in recesses:
            x = int(name.rsplit("_", 1)[1])
            self.assertEqual(self.plan[name], self.sector_at(x + 64, m.WORKS_NORTH + 8))
            self.assertIsNone(self.sector_at(x + 64, m.WORKS_NORTH + m.NICHE_DEPTH + 8))

    # --- population ------------------------------------------------------------
    def test_every_thing_stands_in_the_zone_its_table_names(self):
        m = self.m
        rows = ([(z, k, x, y) for z, k, x, y, *_ in m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in m.ITEMS + m.SECRET_ITEMS])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is in {self.zone_of.get(self.sector_at(x, y))}")

    def test_the_monsters_are_the_bestiarys_own_numbers_in_mapinfo(self):
        text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        block = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S).group(1)
        assigned = {int(n): c for n, c in re.findall(r"(\d+)\s*=\s*(\w+)", block)}
        for ednum, name in self.m.MONSTER_CLASSES.items():
            self.assertEqual(name, assigned.get(ednum), ednum)
        for ednum in self.m.ROUTE_WEAPONS + (self.m.ED_HAND_KATYUSHA,):
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertEqual(set(self.m.MONSTER_CLASSES), {t["type"] for t in self.monsters()},
                         "every class of the bestiary fights at the campaign's end")

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
            hurting = [self.zone_of[s] for s in under if self.sectors[s].get("damageamount")]
            self.assertFalse(hurting, f"{where} starts in molten metal")

    def test_no_two_monsters_start_inside_each_other(self):
        bodies = self.monsters()
        for i, a in enumerate(bodies):
            for b in bodies[i + 1:]:
                reach = self.body[a["type"]][0] + self.body[b["type"]][0]
                apart = abs(a["x"] - b["x"]) >= reach or abs(a["y"] - b["y"]) >= reach
                self.assertTrue(apart, f"{a['type']} at ({a['x']}, {a['y']}) and {b['type']} at ({b['x']}, {b['y']})")

    def test_every_pickup_can_be_picked_up(self):
        reach = self.rounds[-1][1]
        for t in self.things:
            if t["type"] in self.monster_numbers or t["type"] == self.m.ED_PLAYER1_START:
                continue
            s = self.sector_at(t["x"], t["y"])
            where = f"thing {t['type']} at ({t['x']}, {t['y']})"
            self.assertIsNotNone(s, f"{where} is in a wall")
            self.assertNotIn(s, self.unwalkable, f"{where} on {self.zone_of[s]}")
            self.assertIn(s, reach, f"{where} in {self.zone_of[s]}")
            self.assertFalse(self.sectors[s].get("damageamount"), f"{where} in molten metal")

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
        self.assertGreater(counts[4], 96, "harder than Red Square (96 on skill 4)")

    def test_the_tables_factions_are_the_classes_own(self):
        m = self.m
        for kind, ednum in m.MONSTER_KINDS.items():
            faction = self.faction[ednum]
            expected = "REICH" if kind in m.REICH else "LEGION" if kind in m.LEGION else "BOTH"
            self.assertEqual(expected, faction, kind)

    def test_each_faction_holds_its_ground_and_both_guard_the_boss(self):
        m = self.m
        for zone, kind, *_ in m.MONSTERS:
            faction = self.faction[m.MONSTER_KINDS[kind]]
            if zone.startswith(m.REICH_GROUND):
                self.assertNotEqual("LEGION", faction, f"{kind} in {zone}")
            elif zone.startswith(m.LEGION_GROUND):
                self.assertNotEqual("REICH", faction, f"{kind} in {zone}")
            else:
                self.assertTrue(zone.startswith(m.BOTH_GROUND), zone)
        crater = {i for n, i in self.plan.items() if n.startswith("z8_")}
        for skill in SKILLS:
            here = {self.faction[t["type"]] for t in self.on(skill, self.monsters())
                    if self.sector_at(t["x"], t["y"]) in crater}
            self.assertTrue({"LEGION", "REICH"} <= here, f"skill {skill}: {here}")

    def test_the_weapons_are_on_every_skill_on_the_route_in_order(self):
        m = self.m
        for ednum, zone, stage in ((m.ED_IZH, "z1_halt", 0), (m.ED_PPSH, "z3_izba_a", 0),
                                   (m.ED_RPG7, "z4_forest", 1), (m.ED_ROKS3, "z5_edge", 1)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertEqual(stage, self.round_of(where), ednum)
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}))

    def test_consumables_scale_down(self):
        m = self.m
        fixed = (self.monster_numbers | set(m.ROUTE_WEAPONS) | set(m.KEY_LOCKS)
                 | {m.ED_PLAYER1_START, m.ED_HAND_KATYUSHA})
        for kind in {t["type"] for t in self.things} - fixed:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]] for t in self.on(skill, self.monsters()))

    def on_route(self, things):
        off = self.named(*self.m.SECRET_ZONES)
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in off]

    def ammo_placed(self, skill, heavy=True):
        placed = self.on_route(self.on(skill, self.things))
        return sum(SHELLS_GIVEN.get(t["type"], 0) + ROUNDS_GIVEN.get(t["type"], 0) / ROUNDS_PER_SHELL
                   + heavy * (ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                              + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL) for t in placed)

    def test_g3_8_the_ammo_budget(self):
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            self.assertGreaterEqual(have, G3_8_MARGIN * need, f"skill {skill}: {have} for {need}")
        self.assertLess(self.ammo_placed(4), 3 * self.ammo_needed(4))

    def test_the_budget_holds_without_the_heavy_weapons_but_for_the_boss(self):
        boss = SHELLS_TO_KILL[self.m.MONSTER_CLASSES[self.m.MONSTER_KINDS[self.m.BOSS_KIND]]]
        for skill in SKILLS:
            need = self.ammo_needed(skill) - boss
            self.assertGreaterEqual(self.ammo_placed(skill, heavy=False), G3_8_MARGIN * need, f"skill {skill}")

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        start = int(found.group(1))
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = start * PPSH_AVERAGE
            for stage, (_opened, reach, _held) in enumerate(self.rounds):
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
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 14)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        self.assertEqual(3, self.round_of(self.sector_at(vest["x"], vest["y"])), "before the boss")


if __name__ == "__main__":
    unittest.main()
