"""MAP08 «Североморск» / Severomorsk, v1 (docs/levels/MAP08-severomorsk.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map05_dam.py, whose model of play it repeats:

* structure: every sector closed and clockwise, no duplicate vertex, no step
  up over 16; every level of the base walked (water, quays, deck, galleries,
  the reactor hall down in the rock);
* only approved, packed textures (F_SKY1 is the engine's sky marker); the
  "Naval" set (D113) worn: each piece the art-director drew as itself, each
  never drawn on the nearest installed lump; the living rock on the walls
  and overhead, the waterline on the quays, the hull aligned to the water
  and the deck, the kerbs to the water, the crane lattice on both faces;
* everything is reachable and the exit is reached playing the map's own
  doors, switches and its THREE keys (blue, yellow, red) in order; no trap
  at any stage; the shortcut (SW-B) and the three secrets are never needed;
* the key grammar (D58): each lock seen before its key, each key seen from
  where its place is entered, each key's place in its lock's colour of
  light; the switches real faces, one-shot, each in sight of what it opens;
* the base: the fjord seen and never entered, the dock's water harmless with
  steps out, the boat boarded from both quays and entered only by its hatch,
  its fin's star once on each face, the boom across the mouth impassable;
* the population: monsters per skill and nested, both factions where the
  design puts them, every body with room, the closets on their locks; the
  weapons on the route, health and armour scaled down, the ammunition
  following the monsters (D119): inside G3-8's band on every skill, at the
  skill's floor at every stage, shells at most 35 % with the drops, each
  pool after its weapon and the newest leading, fuel sparing;
* the three secrets: a push panel each, a clue that is a comparison, a way
  back; the Hand Katyusha in S3;
* V3's pickup events (D120's A2 and A3; tests/_pickup_events_e3.py): the
  blue key brings the torpedo-loading cradle down, the yellow key sinks the
  torpedo magazine's wall; each hidden until it fires, warned by a
  flickering lamp, never needed, never a trap.

Run:  python3 -m unittest tests.test_map08_severomorsk -v
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
import _pickup_events_e3 as pickup_events  # noqa: E402

parse_textmap = udmf_tests.parse_textmap
MAX_STEP_UP = udmf_tests.MAX_STEP_UP       # 24
PLAYER_HEIGHT = udmf_tests.PLAYER_HEIGHT   # 56
VIEW_HEIGHT = udmf_tests.VIEW_HEIGHT       # 41

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4
SIGHT_STEP = 4
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}
KEY_SPRITE_MID = 8
SMALLEST_BODY = 56      # the shortest monster and the player: nothing enters an opening lower
FLYING_ROOM = 256       # a Doughboy floats where the room is at least this high

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
    "SD_LegionGunner": "legion_gunner.zs",
    "SD_LibertyColossus": "liberty_colossus.zs",
    "SD_ChromeGeneral": "chrome_general.zs",
}
CLASS_PARENT = {"SD_PanzermenschSchwer": "SD_Panzermensch", "SD_ChromeGeneral": "SD_LibertyColossus"}
# G3-8 as MAP01-MAP05 measure it: each kill in IZh shells, heavy weapons
# converted at the ruler's ~62.5 HP a shell (MAP03's test, unchanged).
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8,
                  "SD_PanzermenschSchwer": 16, "SD_LegionGunner": 2,
                  "SD_LibertyColossus": 48, "SD_ChromeGeneral": 48}
# D116: the gunner's 80 HP is two shells (one barrel kills him half the
# time); the Liberty Colossus's 3000 is 48 (D119; his 4500 was 72), and so
# is the Chrome Marshal's, the colossus variant in his place since D123.
# D119 (docs/engine/BALANCE.md section 8, the CEO's playtest: "siempre sale
# de sobras"): G3-8 is a band per skill, not a floor - the route's ammunition
# over what killing every monster takes; shells at most 35 % of the route's
# damage with the drops, each pool after its weapon and the newest leading,
# fuel sparingly; the AKM's rounds ahead of the PPSh's.
G3_8_BANDS = {2: (1.5, 2.0), 3: (1.3, 1.6), 4: (1.2, 1.45)}
SHELL_SHARE_MAX = 0.35
FUEL_SHARE_MAX = 0.15
# BALANCE 8.3: drops, in shell-equivalents, count in the shell share only: a
# Legion trooper's IZh 2 shells (D119), a rifleman's clip 5 rounds, a gunner's
# 15 AKM rounds.
DROPPED_SHELLS = {"SD_LegionTrooper": 2}
DROPS = {"SD_LegionTrooper": 2, "SD_ReichRifleman": 0.5, "SD_LegionGunner": 15 / (80 / 12)}
NEWEST_SHARE_MIN = 0.40     # BALANCE 8.4.2
ROCKET_SHARE_MAX = 0.30     # BALANCE 8.4.2, the PM's amendment: PG-7V a strong second outside a boss's stage
BOSS_CLASSES = ("SD_LibertyColossus", "SD_ChromeGeneral", "SD_Consortium")
PRE_D119_STOCK_SKILL_4 = 342.0   # the route's shell-equivalents on skill 4 before D119
PRE_D119_AMMO_PICKUPS = {2: 49, 3: 44, 4: 35}   # the route's, before D119 (skills 2 / 3 / 4)
SHELLS_GIVEN = {2008: 4, 2049: 20, 21003: 8}
ROUNDS_GIVEN = {2007: 10, 2048: 50, 21004: 35}
ROCKETS_GIVEN = {2010: 1, 2046: 5, 21005: 2}
CELLS_GIVEN = {2047: 20, 17: 100, 21006: 40}
# V3 A4, the RGD-5 (BALANCE 8.1): a grenade counts 1.25 shell-equivalents
# (its 100 blast at the centre over the IZh's 80), the pouch (the weapon)
# 2, a loose one 1, the crate 4. Counted in the band (8.2) and in the shell
# share's whole (8.3) only: the stage readiness, the newest weapon's lead
# (8.4.2) and the boss's stage (8.4.3) leave grenades out, as BALANCE says
# (the bosses take no splash).
GRENADES_GIVEN = {21009: 2, 21021: 1, 21022: 4}
SHELLS_PER_GRENADE = 1.25
AKM_ROUNDS_GIVEN = {21020: 30, 21008: 30}   # a magazine; the rifle comes with one (D116)
AKM_AVERAGE = 12                             # 6 x random(1,3) a round (BALANCE slot 4b)
AKM_ROUNDS_PER_SHELL = 80 / AKM_AVERAGE      # an IZh barrel's 80
ROUNDS_PER_SHELL = 10
SHELLS_PER_ROCKET = 2
SHELLS_PER_CELL = 13.5 / 80                  # D119: the ROKS-3's 13.5 a unit of fuel over a barrel's 80
IZH_AVERAGE = 80
PPSH_AVERAGE = 8
RPG_AVERAGE = 135
ROKS_AVERAGE = 13.5                          # D119: 3 x random(1,8) a jet (was 18; BALANCE slot 6)
POOLS = {"shells": (SHELLS_GIVEN, IZH_AVERAGE), "ppsh": (ROUNDS_GIVEN, PPSH_AVERAGE),
         "akm": (AKM_ROUNDS_GIVEN, AKM_AVERAGE), "rockets": (ROCKETS_GIVEN, RPG_AVERAGE),
         "fuel": (CELLS_GIVEN, ROKS_AVERAGE)}
# The same pools in G3-8's shell-equivalents (BALANCE 8.1), and the pool each
# route weapon opens (8.4.1); the TT-33's Clip is open from the start.
SHELL_EQUIVALENTS = {"shells": (SHELLS_GIVEN, 1), "ppsh": (ROUNDS_GIVEN, 1 / ROUNDS_PER_SHELL),
                     "akm": (AKM_ROUNDS_GIVEN, 1 / AKM_ROUNDS_PER_SHELL),
                     "rockets": (ROCKETS_GIVEN, SHELLS_PER_ROCKET), "fuel": (CELLS_GIVEN, SHELLS_PER_CELL)}
WEAPON_POOL = {21003: "shells", 21004: "ppsh", 21008: "akm", 21005: "rockets", 21006: "fuel"}


def _load_map08():
    path = PROJECT_ROOT / "src" / "maps" / "MAP08" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP08_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


def _class_facts(name: str) -> dict:
    """RADIUS, HEIGHT, HEALTH and FACTION of a bestiary class, from its file:
    the FIRST constant of each (the colossus's file also declares a stomp's
    radius further down)."""
    text = (MONSTER_ZS / CLASS_FILES[name]).read_text(encoding="utf-8")
    facts = {}
    for k, v in re.findall(r"const\s+SD_\w+?_(RADIUS|HEIGHT|HEALTH)\s*=\s*(\d+)", text):
        facts.setdefault(k, int(v))
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


class Map08Test(pickup_events.PickupEventChecks, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map08()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_pier"]
        cls.doors = defaultdict(set)
        movers = pickup_events.floor_movers(cls.m)   # a sinking wall is shut like a door, but sinks
        for i, s in enumerate(cls.sectors):
            if s.get("id") and s["heightceiling"] == s["heightfloor"] and s["id"] not in movers:
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
        cls.rounds = cls("test_every_light_is_in_range")._progression()
        cls.every_tag = set().union(*(r[0] for r in cls.rounds))

    # --- helpers ----------------------------------------------------------
    @classmethod
    def _pair(cls, ld):
        return (cls.sides[ld["sidefront"]]["sector"], cls.sides[ld["sideback"]]["sector"])

    def front(self, ld):
        return self.sides[ld["sidefront"]]["sector"]

    def back(self, ld):
        return self.sides[ld["sideback"]]["sector"] if "sideback" in ld else None

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
        return pickup_events.apply_moves(out, self.sectors, self.neighbours, self.plan, self.m, open_tags)

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

    def _progression(self):
        """Play the map as a player can (MAP03's model): manual doors and push
        panels open whenever he can stand at their line; then, one round at a
        time, every switch and locked door he can now reach and work (a
        locked door only once the sector of ITS key is reachable). V3: a
        pickup's special fires as soon as its thing is reachable, in the same
        round (he is standing on it)."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        keys = self.key_sectors()
        pickups = [(tag, self.sector_at(*spot))
                   for tag, spot in pickup_events.pickup_tags(self.things, self.monster_numbers)]
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = {lock for lock, sector in keys.items() if sector in reach}
            free, gated = set(), set()
            free |= {tag for tag, sector in pickups if sector in reach}
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

    def exit_sector(self):
        return self.front(self.exit_line())

    def line_points(self, ld):
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        return (a["x"], a["y"]), (b["x"], b["y"])

    def length(self, ld):
        (ax, ay), (bx, by) = self.line_points(ld)
        return abs(bx - ax) + abs(by - ay)

    def blocked(self, eye, target, open_tags=frozenset()):
        """Sample the 3D segment; any sample in the void or outside its
        sector's floor..ceiling blocks the view."""
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
            out[self.sides[ld["sidefront"]].get("texturemiddle")] += self.length(ld)
        return out

    def first_round_with(self, sector):
        return next(k for k, r in enumerate(self.rounds) if sector in r[1])

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
        h = self.heights(self.every_tag)
        for a, dsts in self.adjacency(self.every_tag).items():
            for b in dsts:
                self.assertLessEqual(h[b][0] - h[a][0], self.m.STEP, f"{self.zone_of[a]} -> {self.zone_of[b]}")

    def test_the_base_is_walked_on_every_level(self):
        """The water (-64), the quays (0), the deck (+32), the galleries and
        the crane (+128, +192), the reactor hall down in the rock (-128) and
        its lid (+64): 320 from the bottom of the base to its top."""
        m = self.m
        reach = self.rounds[-1][1]
        floors = {self.sectors[i]["heightfloor"] for i in reach}
        for level in (m.REACTOR, m.BASIN, m.GROUND, m.DECK, m.LID, m.GANTRY, m.CRANE):
            self.assertIn(level, floors)
        self.assertEqual(320, m.CRANE - m.REACTOR)

    def test_the_extent_is_map05s(self):
        """The brief: «tamaño como MAP05». MAP05 is 4576 x 2304 and 150
        sectors; this map stays within 1.5 times its area and sectors."""
        xs = [v["x"] for v in self.verts]
        ys = [v["y"] for v in self.verts]
        area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        self.assertLessEqual(area, 1.5 * 4576 * 2304)
        self.assertLessEqual(len(self.sectors), 1.5 * 150)

    # --- textures -----------------------------------------------------------
    def test_every_texture_is_approved_and_packed(self):
        m = self.m
        used = set()
        for sd in self.sides:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                if sd.get(key) and sd[key] != "-":
                    used.add(sd[key])
        for s in self.sectors:
            used.add(s["texturefloor"])
            used.add(s["textureceiling"])
        used -= set(m.BUILTIN_FLATS)
        for name in sorted(used):
            self.assertTrue(_packed(name), f"{name} is not in assets/")
        self.assertLessEqual(used, set(m.WALL_TEXTURES) | set(m.FLAT_TEXTURES))

    def test_the_naval_set_is_worn(self):
        """D113: every naval piece the design asked for is worn as itself
        where the art-director drew it, on the nearest installed lump where
        not; and every lump NAVAL_SET names is on the map. A pending name
        that turns up packed says so (wear it)."""
        m = self.m
        worn_on_map = self.textures_used()
        for proposed, worn in m.NAVAL_SET.items():
            self.assertTrue(_packed(worn), worn)
            if _packed(proposed):
                self.assertEqual(proposed, worn, f"{proposed} exists: wear it (NAVAL_SET)")
            else:
                self.assertNotEqual(proposed, worn, proposed)
            self.assertIn(worn, worn_on_map, proposed)
        for proposed in m.PENDING_TEXTURES:
            self.assertFalse(_packed(proposed), f"{proposed} exists now: wear it")
        # The rest of the set and its neighbours, each somewhere on the map.
        for lump in (m.ROCK_CEIL, m.DECK_RUBBER, m.DECK_HATCH, m.PIER_EDGE, m.NAVAL_PANEL, m.CRANE_LATTICE,
                     m.CAB_FRONT, m.CAB_SIDE, m.DAM_WET, m.WATER):
            self.assertIn(lump, worn_on_map, lump)
        self.assertNotIn("SDDAM1", worn_on_map, "the stand-in for the rock is gone")
        self.assertNotIn("SDARMR1", worn_on_map, "the fin wears its number, not the star")

    def textures_used(self):
        used = set()
        for sd in self.sides:
            for key in ("texturetop", "texturemiddle", "texturebottom"):
                if sd.get(key) and sd[key] != "-":
                    used.add(sd[key])
        for s in self.sectors:
            used |= {s["texturefloor"], s["textureceiling"]}
        return used

    def drawn(self, side_key, ld):
        """[(part, the height the engine pegs it to)] of one side of a line,
        as the map's own drawn_parts reads it."""
        side = ld[side_key]
        other = ld.get("sideback" if side_key == "sidefront" else "sidefront")
        s = self.sectors[self.sides[side]["sector"]]
        if other is None:
            return [("texturemiddle", s["heightfloor"] if ld.get("dontpegbottom") else s["heightceiling"])]
        o = self.sectors[self.sides[other]["sector"]]
        parts = []
        if o["heightfloor"] > s["heightfloor"]:
            parts.append(("texturebottom", s["heightceiling"] if ld.get("dontpegbottom") else o["heightfloor"]))
        if o["heightceiling"] < s["heightceiling"] and not (
                s["textureceiling"] == self.m.SKY and o["textureceiling"] == self.m.SKY):
            parts.append(("texturetop", s["heightceiling"] if ld.get("dontpegtop") else o["heightceiling"]))
        return parts

    def column(self, ld, side_key):
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        if side_key == "sideback":
            a, b = b, a
        if a["y"] == b["y"]:
            return int(a["x"]) if b["x"] > a["x"] else -int(a["x"])
        return int(a["y"]) if b["y"] > a["y"] else -int(a["y"])

    def faces_of(self, texture, sectors=None):
        """(line, side key, part, peg height) of every drawn face wearing `texture`."""
        out = []
        for ld in self.lines:
            for key in ("sidefront", "sideback"):
                if key not in ld or (sectors is not None and self.sides[ld[key]]["sector"] not in sectors):
                    continue
                for part, ref in self.drawn(key, ld):
                    if self.sides[ld[key]].get(part) == texture:
                        out.append((ld, key, part, ref))
        return out

    def test_the_base_is_cut_into_living_rock(self):
        """SDROCK1 on the cliffs, the dock, the tunnels and the reactor hall,
        SDROCK2 overhead wherever the base is roofed by the rock; aligned to
        one grid from the ground, so a wall split by a corner shows no seam."""
        m = self.m
        for zone in ("z2_yard", "z3_south_quay", "z3_north_quay", "z3_basin", "z7_tunnel_w", "z7_tunnel_e",
                     "z8_hall", "z9_tunnel", "z11_passage_w", "z11_passage_e"):
            walls = self.one_sided_textures(self.plan[zone])
            self.assertEqual(m.ROCK, walls.most_common(1)[0][0], zone)
        for zone in ("z3_south_quay", "z3_basin", "z3_gallery", "z4_deck", "prop_z4_fin", "z7_tunnel_e",
                     "z8_hall", "z8_lid", "z9_tunnel", "z11_passage_w", "closet_z7_a"):
            self.assertEqual(m.ROCK_CEIL, self.sectors[self.plan[zone]]["textureceiling"], zone)
        for name, index in self.plan.items():
            if name.startswith(m.ROCK_ROOFED):
                self.assertNotEqual(m.CEIL_CONCRETE, self.sectors[index]["textureceiling"], name)
        faces = self.faces_of(m.ROCK)
        self.assertGreater(len(faces), 100)
        for ld, key, _part, ref in faces:
            side = self.sides[ld[key]]
            self.assertEqual((m.GROUND - ref) % m.WALL_TILE, side.get("offsety", 0))
            self.assertEqual(self.column(ld, key) % m.LUMP_WIDTH[m.ROCK], side.get("offsetx", 0))

    def test_the_quays_wear_the_waterline(self):
        """Every face rising out of the dock's water or the fjord onto a quay,
        the pier or a step is SDDAM2, its foot on the water; the hull and the
        boom keep their own."""
        m = self.m
        water = {self.plan["z3_basin"], self.plan["prop_z1_fjord"]}
        faces = self.faces_of(m.DAM_WET)
        self.assertTrue(faces)
        seen = set()
        for ld, key, part, ref in faces:
            self.assertEqual("texturebottom", part)
            self.assertEqual((m.BASIN - ref) % m.WALL_TILE, self.sides[ld[key]].get("offsety", 0))
            other = self.sides[ld["sideback" if key == "sidefront" else "sidefront"]]["sector"]
            seen.add(self.zone_of[other])
        for bank in ("z3_south_quay", "z3_north_quay", "z1_pier", "z1_kerb_w", "z3_kerb_s", "z3_kerb_n",
                     "z3_steps_s1_1", "z3_steps_n2_1"):
            self.assertIn(bank, seen)
        for ld, key, part, _ref in self.faces_of(m.HULL, water):
            self.assertEqual("texturebottom", part)

    def test_the_hull_is_aligned_to_the_water_and_the_deck(self):
        """SDHULL1 world-aligned along the boat; from the water its foot on
        the water (the flooding holes just above it), from the deck, the
        gangways and the stern its top on the deck: the fin one whole tile."""
        m = self.m
        basin = {self.plan["z3_basin"]}
        topside = {self.plan[n] for n in ("z4_deck", "z4_stern", "z4_escape_hatch", *m.GANGWAYS)}
        low = self.faces_of(m.HULL, basin)
        high = self.faces_of(m.HULL, topside)
        self.assertTrue(low and high)
        for faces, base in ((low, m.BASIN), (high, m.DECK)):
            for ld, key, _part, ref in faces:
                side = self.sides[ld[key]]
                self.assertEqual((base - ref) % m.WALL_TILE, side.get("offsety", 0))
                self.assertEqual(self.column(ld, key) % m.LUMP_WIDTH[m.HULL], side.get("offsetx", 0))
        fin = self.sectors[self.plan["prop_z4_fin"]]
        self.assertEqual(m.DECK_RUBBER, self.sectors[self.plan["z4_deck"]]["texturefloor"])
        self.assertEqual(m.DECK_RUBBER, fin["texturefloor"])
        hatch = self.sectors[self.plan["z4_escape_hatch"]]
        self.assertEqual(m.DECK_HATCH, hatch["texturefloor"])
        self.assertEqual(m.HATCH_PANNING, hatch.get("ypanningfloor"))
        x1, y1, x2, y2 = m.ESCAPE_HATCH
        self.assertEqual((m.HULL_Y[0] + m.HULL_Y[1]) / 2, (y1 + y2) / 2, "on the hull's axis")
        self.assertEqual(0, x1 % m.FLAT_TILE)
        self.assertEqual(m.FLAT_TILE, x2 - x1)
        self.assertEqual(m.FLAT_TILE, y2 - y1)
        self.assertEqual(m.FLAT_TILE // 2, y1 % m.FLAT_TILE, "half a tile of panning centres it")
        # The covered berth's face either side of D3 is rock, not hull to the roof.
        deck = self.plan["z4_deck"]
        self.assertNotIn(m.HULL, self.one_sided_textures(deck))

    def test_the_kerbs_face_the_water(self):
        """SDPIER1 on the pier's and the quays' edges, one tile deep and on the
        flat grid, flush with the ground, each touching the water on the side
        its rotation turns the kerb to; the steps and the gangways break them."""
        m = self.m
        kerbs = {name: (rect, water) for name, (rect, water) in m.PIER_KERBS.items()}
        for name, ((ky1, ky2), water) in m.QUAY_KERBS.items():
            kerbs[name] = ((m.KERB_X[0][0], ky1, m.KERB_X[-1][1], ky2), water)
        wet = {self.plan["z3_basin"], self.plan["prop_z1_fjord"]}
        for name, ((x1, y1, x2, y2), water) in kerbs.items():
            s = self.sectors[self.plan[name]]
            self.assertEqual(m.PIER_EDGE, s["texturefloor"], name)
            self.assertEqual(m.GROUND, s["heightfloor"], name)
            self.assertEqual(m.KERB_ROTATION[water], s.get("rotationfloor", 0.0), name)
            deep = (x2 - x1) if water == "west" else (y2 - y1)
            self.assertEqual(m.FLAT_TILE, deep, name)
            edge = {"west": ("v", x1), "south": ("h", y1), "north": ("h", y2)}[water]
            far = {"west": ("v", x2), "south": ("h", y2), "north": ("h", y1)}[water]
            for (axis, c) in (edge, far):
                self.assertEqual(0, c % m.FLAT_TILE, name)
            touching = [ld for ld in self.lines if "sideback" in ld and self.plan[name] in self._pair(ld)
                        and set(self._pair(ld)) & wet]
            self.assertTrue(touching, name)
            on_edge = off_edge = 0
            for ld in touching:
                (ax, ay), (bx, by) = self.line_points(ld)
                if (edge[0] == "v" and ax == bx == edge[1]) or (edge[0] == "h" and ay == by == edge[1]):
                    on_edge += self.length(ld)
                else:
                    off_edge += self.length(ld)    # the pier's corner tile only
            self.assertGreater(on_edge, off_edge, name)
            self.assertLessEqual(off_edge, m.FLAT_TILE, name)
        for (sx1, sx2) in m.BASIN_STEPS_X + (m.GANGWAYS["z4_gangway_s"][::2],):
            for kx1, kx2 in m.KERB_X:
                self.assertTrue(kx2 <= sx1 or sx2 <= kx1, "a step or a gangway lands on a kerb")

    def test_the_cranes_lattice_hangs_on_both_faces(self):
        """SDCRAN1, masked: on both faces of the outer crane's deck edges and
        of the dock's crane gallery, standing one tile tall on the high floor
        (lower-unpegged), world-aligned, a railing nobody walks through; and
        no other line hangs anything in mid-air."""
        m = self.m
        hung = [ld for ld in self.lines if "sideback" in ld and m.CRANE_LATTICE in
                (self.sides[ld["sidefront"]].get("texturemiddle"), self.sides[ld["sideback"]].get("texturemiddle"))]
        self.assertGreaterEqual(sum(self.length(ld) for ld in hung),
                                sum(hi - lo for _a, _c, lo, hi in m.LATTICES))
        highs = set()
        for ld in hung:
            self.assertTrue(ld.get("blocking"))
            self.assertTrue(ld.get("dontpegbottom"))
            for key in ("sidefront", "sideback"):
                side = self.sides[ld[key]]
                self.assertEqual(m.CRANE_LATTICE, side.get("texturemiddle"))
                self.assertEqual(self.column(ld, key) % m.LUMP_WIDTH[m.CRANE_LATTICE], side.get("offsetx", 0))
                self.assertEqual(0, side.get("offsety", 0))
            a, b = self._pair(ld)
            high = max(self.sectors[a]["heightfloor"], self.sectors[b]["heightfloor"])
            highs.add(high)
            room = min(self.sectors[a]["heightceiling"], self.sectors[b]["heightceiling"]) - high
            self.assertGreaterEqual(room, m.TILE, "the lattice stands whole")
        self.assertEqual({m.CRANE}, highs)
        for ld in self.lines:
            for key in ("sidefront", "sideback"):
                if key in ld and "sideback" in ld:
                    self.assertIn(self.sides[ld[key]].get("texturemiddle", "-"), ("-",) + m.MIDDLE_TEXTURES)
        tower = [ld for ld in self.lines if "sideback" not in ld and self.front(ld) == self.plan["z1_pier"]
                 and self.sides[ld["sidefront"]].get("texturemiddle") == m.RUST]
        self.assertEqual(2, len(tower), "the crane's tower from the pier is sheet, not rock")

    def test_the_containers_are_whole(self):
        """SDCONT1 on every container's flank: one tile high, every face a
        whole number of containers, from the tile's start."""
        m = self.m
        for n in range(1, len(m.CONTAINERS) + 1):
            box = self.plan[f"prop_z2_container_{n}"]
            self.assertEqual(m.TILE, self.sectors[box]["heightfloor"] - m.GROUND)
            faces = [ld for ld in self.lines if "sideback" in ld and box in self._pair(ld)]
            self.assertEqual(4, len(faces), n)
            for ld in faces:
                key = "sidefront" if self.front(ld) != box else "sideback"
                self.assertEqual(m.CONTAINER_SIDE, self.sides[ld[key]]["texturebottom"])
                self.assertEqual(0, self.length(ld) % m.TILE)
                self.assertEqual(0, self.sides[ld[key]].get("offsetx", 0))

    def test_the_sky_is_over_the_outdoors_only(self):
        m = self.m
        sky = {self.zone_of[i] for i, s in enumerate(self.sectors) if s["textureceiling"] == m.SKY}
        for zone in ("z1_pier", "z2_yard", "z1_crane_deck", "z2_rails", "prop_z1_fjord"):
            self.assertIn(zone, sky)
        for zone in sky:
            self.assertTrue(zone.startswith(("z1_", "z2_", "prop_z1_", "prop_z2_", "prop_z3_mouth")), zone)
            self.assertNotIn(self.plan[zone], self.door_sectors)
        for zone in ("z3_south_quay", "z3_basin", "z4_deck", "z8_hall", "z10_bay"):
            self.assertNotIn(zone, sky, "the base is cut into the rock")

    def test_the_fjord_is_seen_and_never_entered(self):
        """The fjord is water under a low sky: its opening over the pier and
        the mouth is lower than any body, so nobody walks, falls or flies
        into it; the eye sees it (the opening is above the pier's floor)."""
        m = self.m
        fjord = self.plan["prop_z1_fjord"]
        f = self.sectors[fjord]
        self.assertEqual(m.WATER, f["texturefloor"])
        for n in self.neighbours[fjord] - self.props:
            s = self.sectors[n]
            opening = min(f["heightceiling"], s["heightceiling"]) - max(f["heightfloor"], s["heightfloor"])
            self.assertLess(opening, SMALLEST_BODY, self.zone_of[n])
            if n == self.start or self.zone_of[n].startswith("z1_kerb"):
                self.assertGreater(opening, 0, "the pier and its kerbs must see the water")
        self.assertNotIn(fjord, self.rounds[-1][1])

    def test_the_boom_closes_the_pens_mouth(self):
        m = self.m
        boom = self.plan["prop_z3_boom"]
        lines = [ld for ld in self.lines if "sideback" in ld and boom in self._pair(ld)]
        self.assertTrue(lines)
        for ld in lines:
            self.assertTrue(ld.get("blocking"), self.zone_of[next(iter(set(self._pair(ld)) - {boom}))])
        self.assertNotIn(self.plan["prop_z3_mouth"], self.rounds[-1][1])

    def test_the_fins_number_is_whole_once_on_each_face(self):
        """SDHULL2's «471» once on each long face of the fin, exactly one tile
        high over the deck and one tile long, from the tile's start (never
        stacked, never cut)."""
        m = self.m
        fin = self.sectors[self.plan["prop_z4_fin"]]
        self.assertEqual(m.TILE, fin["heightfloor"] - m.DECK)
        numbers = [ld for ld in self.lines if "sideback" in ld
                   and any(self.sides[s].get("texturebottom") == m.HULL_NUMBER
                           for s in (ld["sidefront"], ld["sideback"]))]
        self.assertEqual(2, len(numbers))
        for ld in numbers:
            self.assertEqual(m.TILE, self.length(ld))
            key = "sidefront" if self.front(ld) == self.plan["z4_deck"] else "sideback"
            self.assertEqual(self.plan["z4_deck"], self.sides[ld[key]]["sector"])
            self.assertEqual(0, self.sides[ld[key]].get("offsetx", 0))
            self.assertEqual(0, self.sides[ld[key]].get("offsety", 0))

    def test_the_boat_is_entered_by_its_hatch_only(self):
        """The inside of the boat (z4_trunk ... z4_torpedo) touches the dock
        only through D3: every other line around it is a wall, so nothing
        of the pen shows inside and nothing of the inside shows outside."""
        inside = {i for n, i in self.plan.items() if n.startswith(("z4_trunk", "z4_passage", "z4_control",
                                                                       "z4_swa", "z4_torpedo", "z4_tray",
                                                                       "prop_z4_rack", "shutter_wt"))}
        allowed = inside | self.named("d3_hatch")
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a, b = self._pair(ld)
            if a in inside or b in inside:
                self.assertTrue({a, b} <= allowed, f"{self.zone_of[a]} | {self.zone_of[b]}")

    def test_the_control_room_wears_its_panels_and_the_bow_its_tubes(self):
        m = self.m
        control = self.one_sided_textures(self.plan["z4_control"])
        self.assertGreaterEqual(control[m.NAVAL_PANEL], 2 * (m.CONTROL[2] - m.CONTROL[0]))
        self.assertEqual(0, (m.CONTROL[2] - m.CONTROL[0]) % m.TILE, "whole panels")
        torpedo = self.one_sided_textures(self.plan["z4_torpedo"])
        self.assertEqual(m.TORPEDO[3] - m.TORPEDO[1], torpedo[m.TUBBING])
        room = self.sectors[self.plan["z4_control"]]
        self.assertEqual(m.TILE, room["heightceiling"] - room["heightfloor"], "the boards are one tile")

    def test_the_dormitory_is_one_locker_high(self):
        m = self.m
        dorm = self.sectors[self.plan["z6_dorm"]]
        self.assertEqual(m.TILE, dorm["heightceiling"] - dorm["heightfloor"])
        self.assertGreater(self.one_sided_textures(self.plan["z6_dorm"])[m.LOCKER], 0)

    def test_every_door_leaf_is_whole(self):
        """A door's leaf is the upper texture of its faces: each lock and
        manual door is one tile wide (128), the watertight door half."""
        m = self.m
        for tag in (m.TAG_D1_PEN, m.TAG_D2_BARRACKS, m.TAG_D3_HATCH, m.TAG_BLUE_DOOR,
                    m.TAG_YELLOW_DOOR, m.TAG_RED_GATE):
            faces = [ld for ld in self.lines if ld.get("arg0") == tag and ld.get("special") in
                     (SPECIAL_DOOR_RAISE, m.SPECIAL_DOOR_LOCKED_RAISE)]
            self.assertEqual(2, len(faces), tag)
            for ld in faces:
                self.assertEqual(m.TILE, self.length(ld), tag)
                self.assertIn(self.sides[ld["sidefront"]]["texturetop"], m.DOOR_LEAVES)
        self.assertEqual(m.DOOR_BLUE, self._leaf(m.TAG_BLUE_DOOR))
        self.assertEqual(m.DOOR_YELLOW, self._leaf(m.TAG_YELLOW_DOOR))
        self.assertEqual(m.DOOR_RED, self._leaf(m.TAG_RED_GATE))
        hatch = [ld for ld in self.lines if ld.get("arg0") == m.TAG_D3_HATCH and ld.get("special") == SPECIAL_DOOR_RAISE]
        for ld in hatch:
            self.assertEqual(m.BULKHEAD_DOOR, self.sides[ld["sidefront"]]["texturetop"], "D3 is the round door")

    def _leaf(self, tag):
        ld = next(ld for ld in self.lines if ld.get("arg0") == tag
                  and ld.get("special") == self.m.SPECIAL_DOOR_LOCKED_RAISE)
        return self.sides[ld["sidefront"]]["texturetop"]

    def test_every_door_from_the_open_has_a_roofed_porch(self):
        """A door's leaf hangs from the lower ceiling on either side: every
        door, lock and closet that faces the sky or the dock's 448 has a
        porch or a portal in front of it, so the leaf is one door high, not
        a wall of steel up to the roof. Closets in the cliff wear the cliff."""
        m = self.m
        for tag in (m.TAG_D1_PEN, m.TAG_D2_BARRACKS, m.TAG_D3_HATCH, m.TAG_BLUE_DOOR,
                    m.TAG_YELLOW_DOOR, m.TAG_RED_GATE):
            faces = [ld for ld in self.lines if ld.get("arg0") == tag and "sideback" in ld
                     and ld.get("special") in (SPECIAL_DOOR_RAISE, m.SPECIAL_DOOR_LOCKED_RAISE)]
            for ld in faces:
                room = self.sectors[self.front(ld)]
                self.assertLessEqual(room["heightceiling"] - room["heightfloor"], m.TILE,
                                     self.zone_of[self.front(ld)])

    def test_the_flags_hang_side_by_side_by_the_train(self):
        m = self.m
        faces = [self.sides[ld["sidefront"]].get("texturemiddle") for ld in self.lines if "sideback" not in ld
                 and self.front(ld) in self.named(*(f"z10_flag_{t.lower()}" for t in m.BAY_FLAGS))]
        self.assertIn(m.FLAG_USSR_1, faces)
        self.assertIn(m.FLAG_USSR_2, faces)

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
            self.assertEqual(colour, self.sectors[keys[lock]].get("lightcolor"), f"the key of lock {lock}")
            colours.add(colour)
            wearing = {self.zone_of[i] for i, s in enumerate(self.sectors) if s.get("lightcolor") == colour}
            self.assertEqual({portal, self.zone_of[keys[lock]]}, wearing,
                             "one patch of colour on the key's place, one at the lock")
        self.assertEqual(3, len(colours))

    # --- scope -------------------------------------------------------------
    def test_the_start_and_the_keys_are_on_every_skill(self):
        m = self.m
        for ed in (m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_BLUE_CARD, m.ED_RED_CARD):
            found = self.things_of({ed})
            self.assertEqual(1, len(found), ed)
            for skill in range(1, 6):
                self.assertTrue(found[0][f"skill{skill}"], f"thing {ed} missing on skill {skill}")
            self.assertTrue(found[0]["single"])

    def test_the_only_special_sectors_are_the_secrets(self):
        """The dock's water does not hurt (the brief: «daño nulo o leve»): a
        still dock, and the player wades out by the steps."""
        m = self.m
        special = {self.zone_of[i]: s["special"] for i, s in enumerate(self.sectors) if s.get("special")}
        want = {zone: m.SECTOR_SPECIAL_SECRET for zone in m.SECRET_ZONES}
        # V3: the events' warning lamps.
        want.update({e.lamp: m.SECTOR_SPECIAL_LIGHT_FLICKER for e in m.PICKUP_EVENTS})
        self.assertEqual(want, special)
        self.assertFalse([i for i, s in enumerate(self.sectors) if s.get("damageamount")])

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.rounds[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         sorted(self.zone_of[i] for i in unreachable ^ self.props))

    def test_the_exit_is_reached_and_only_in_the_last_round(self):
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z10_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        self.assertIn(exit_sector, self.rounds[-1][1])
        for opened, reach, _ in self.rounds[:-1]:
            self.assertNotIn(exit_sector, reach, f"exit reached with only {sorted(opened)}")
        niche = self.sectors[exit_sector]
        self.assertEqual(self.m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])

    def test_no_trap_at_any_stage(self):
        for opened, reach, _held in self.rounds:
            back = self.flood(self.reverse(self.adjacency(opened)), self.start)
            stranded = sorted(self.zone_of[i] for i in reach - back)
            self.assertEqual([], stranded, f"with tags {sorted(opened)} open")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        opened, reach, _ = self.rounds[-1]
        onward = self.flood(self.reverse(self.adjacency(opened)), self.front(self.exit_line()))
        self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward))

    def test_the_route_is_the_designed_one(self):
        """Five rounds: (0) the pier, the yard, the barracks, the dock, the
        boat up to its control room; (1) SW-A, the torpedo room and the blue
        key; (2) the blue door, the workshops, the yellow key; (3) the yellow
        door, the tunnel, the reactor and the red key, SW-B's passage; (4) the
        red gate and SW-B, the rail tunnel, the bay, the exit."""
        m = self.m
        self.assertEqual(5, len(self.rounds))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3), (o4, r4, h4) = self.rounds
        self.assertEqual({m.TAG_D1_PEN, m.TAG_D2_BARRACKS, m.TAG_D3_HATCH, m.TAG_S1_PANEL,
                          m.TAG_S2_PANEL, m.TAG_S3_PANEL}, set(o0))
        self.assertEqual(set(), set(h0))
        self.assertTrue(self.named("z2_yard", "z6_mess", "z3_north_quay", "z4_deck", "z4_control",
                                   "z1_crane_deck") <= r0)
        self.assertNotIn(self.plan["z4_torpedo"], r0, "the torpedo room is behind the watertight door")
        self.assertEqual({m.TAG_WT_SHUTTER, m.TAG_TORPEDO_LIFT}, set(o1 - o0), "V3: the blue key's cradle")
        self.assertEqual({m.LOCK_BLUE_CARD}, set(h1))
        self.assertNotIn(self.plan["z5_workshop"], r1)
        self.assertEqual({m.TAG_BLUE_DOOR, m.TAG_MAGAZINE}, set(o2 - o1), "V3: the yellow key's magazine")
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD}, set(h2))
        self.assertNotIn(self.plan["z8_hall"], r2)
        self.assertEqual({m.TAG_YELLOW_DOOR}, set(o3 - o2))
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD}, set(h3))
        self.assertTrue(self.named("z8_lid", "z11_passage_w") <= r3)
        self.assertNotIn(self.plan["z9_tunnel"], r3, "the rail tunnel is behind the red gate")
        self.assertEqual({m.TAG_RED_GATE, m.TAG_BARRACKS_SHUTTER}, set(o4 - o3))
        self.assertTrue(self.named("z9_tunnel", "z10_bay", "z10_cab") <= r4)

    def test_the_shortcut_is_not_needed(self):
        """SW-B's shutter puts the reactor's passage in the barracks, a door
        from the yard; without it the way back is the long one, up the rock
        tunnel, across the dock and through D1."""
        m = self.m
        self.assertIn(self.front(self.exit_line()), self.reachable(self.every_tag - {m.TAG_BARRACKS_SHUTTER}))

    def test_no_secret_is_needed(self):
        m = self.m
        critical = self.every_tag - {m.TAG_S1_PANEL, m.TAG_S2_PANEL, m.TAG_S3_PANEL}
        self.assertIn(self.front(self.exit_line()), self.reachable(critical))

    def test_every_climb_is_a_stair_walked_both_ways(self):
        """No lift (MAP01 section 4): the crane, the dock's gallery, the
        workshop's gantry, the reactor's lid, the tunnel and the passage down
        into the rock are steps of 16 the player walks both ways."""
        m = self.m
        adj = self.adjacency(self.every_tag)
        chains = (
            ["z1_pier"] + [f"z1_crane_stair_{n}" for n in range(1, m.CRANE_STAIR_STEPS + 1)] + ["z1_crane_deck"],
            ["z3_south_quay"] + [f"z3_gallery_stair_{n}" for n in range(1, m.GALLERY_STAIR_STEPS + 1)]
            + ["z3_gallery"],
            ["z5_workshop"] + [f"z5_gantry_stair_{n}" for n in range(1, m.GANTRY_STAIR_STEPS + 1)] + ["z5_gantry"],
            ["z8_hall"] + [f"z8_lid_stair_{n}" for n in range(1, m.LID_STAIR_STEPS + 1)] + ["z8_landing"],
            ["z7_tunnel_w"] + [f"z7_step_{n}" for n in range(1, m.TUNNEL_STEPS + 1)] + ["z7_tunnel_e"],
            ["z11_passage_w"] + [f"z11_passage_step_{n}" for n in range(1, m.PASSAGE_STEPS + 1)]
            + ["z11_passage_e"],
            ["z3_south_quay", "z4_gangway_s", "z4_deck", "z4_gangway_n", "z3_north_quay"],
        )
        for chain in chains:
            for a, b in zip(chain, chain[1:]):
                fa = self.sectors[self.plan[a]]["heightfloor"]
                fb = self.sectors[self.plan[b]]["heightfloor"]
                self.assertEqual(self.m.STEP, abs(fa - fb), f"{a} -> {b}")
                self.assertIn(self.plan[b], adj[self.plan[a]], f"{a} -> {b}")
                self.assertIn(self.plan[a], adj[self.plan[b]], f"{b} -> {a}")
        self.assertIn(self.plan["z8_lid"], adj[self.plan["z8_landing"]])

    def test_the_boat_is_boarded_from_both_quays(self):
        """The deck is the crossing: the gangways from both quays meet on it,
        the fin stands on it, D3 opens off it."""
        r0 = self.rounds[0][1]
        adj = self.adjacency(set())
        north = self.flood(adj, self.plan["z3_south_quay"])
        self.assertIn(self.plan["z3_north_quay"], north)
        cut = {a: {b for b in dsts if b != self.plan["z3_basin"] and not self.zone_of[b].startswith("z3_steps")}
               for a, dsts in adj.items()}
        dry = self.flood(defaultdict(set, cut), self.plan["z3_south_quay"])
        self.assertIn(self.plan["z3_north_quay"], dry, "across the deck without wading")
        self.assertIn(self.plan["z4_deck"], r0)

    def test_the_docks_water_is_no_trap(self):
        """64 down from either quay, three steps of 16 out on both quays at
        two places; nothing to pick up in it; a way back from it."""
        m = self.m
        basin = self.plan["z3_basin"]
        adj = self.adjacency(self.every_tag)
        for quay in ("z3_south_quay", "z3_north_quay"):
            self.assertIn(basin, adj[self.plan[quay]], f"{quay}: dropping in is free")
            self.assertNotIn(self.plan[quay], adj[basin], f"{quay}: 64 up is not a step")
        for k in range(1, len(m.BASIN_STEPS_X) + 1):
            for bank, quay in (("s", "z3_south_quay"), ("n", "z3_north_quay")):
                chain = ["z3_basin"] + [f"z3_steps_{bank}{k}_{n}" for n in (1, 2, 3)] + [quay]
                for a, b in zip(chain, chain[1:]):
                    self.assertIn(self.plan[b], adj[self.plan[a]], f"{a} -> {b}")
        self.assertIn(basin, adj[self.plan["z4_deck"]], "off the deck into the water")
        self.assertFalse([t for t in self.things if t["type"] not in self.monster_numbers
                          and self.sector_at(t["x"], t["y"]) == basin])
        self.assertIn(self.start, self.flood(adj, basin), "a way back from the water")

    # --- the keys ------------------------------------------------------------
    def test_three_keys_on_the_route_outside_any_secret(self):
        m = self.m
        self.assertEqual(sorted([m.ED_BLUE_CARD, m.ED_YELLOW_CARD, m.ED_RED_CARD]),
                         sorted(t["type"] for t in self.key_things()))
        for t in self.key_things():
            sector = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[m.KEY_ZONES[t["type"]]], sector)
            self.assertFalse(self.sectors[sector].get("special"))

    def test_each_key_lies_alone_on_its_lit_place(self):
        for sector in self.key_sectors().values():
            here = [t for t in self.things if self.sector_at(t["x"], t["y"]) == sector]
            self.assertEqual(1, len(here), self.zone_of[sector])

    def test_the_locked_doors_open_with_their_keys_and_stay_open(self):
        m = self.m
        locked = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE]
        self.assertEqual(6, len(locked), "three doors, both faces")
        expected = {m.TAG_BLUE_DOOR: (m.LOCK_BLUE_CARD, "z13_blue_door"),
                    m.TAG_YELLOW_DOOR: (m.LOCK_YELLOW_CARD, "z13_yellow_door"),
                    m.TAG_RED_GATE: (m.LOCK_RED_CARD, "z13_red_gate")}
        for ld in locked:
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0), tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.back(ld))

    def test_the_red_gate_is_seen_from_the_start(self):
        """The first thing the player sees across the yard is the lock he
        will leave by: the rail tunnel's gate, lit red, at the end of the
        track."""
        m = self.m
        eye = self.eye(*m.PLAYER_START, "z1_pier")
        for y in (320, 352, 384):
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (m.RED_GATE[0] - 1, y, z)), f"y {y} z {z}")

    def test_the_blue_and_yellow_doors_are_seen_across_the_basin(self):
        """From the south quay, where D1 brings him in, the player sees both
        locks of the dock's north side across the water: the blue door west
        of the fin, the yellow door east of it."""
        m = self.m
        eye = self.eye(2400, 1696, "z3_south_quay")
        targets = (((m.BLUE_DOOR[0] + m.BLUE_DOOR[2]) / 2, m.BLUE_DOOR[1] - 1),
                   (m.YELLOW_DOOR[0] - 1, (m.YELLOW_DOOR[1] + m.YELLOW_DOOR[3]) / 2))
        for target in targets:
            for z in (48, 96):
                self.assertIsNone(self.blocked(eye, (*target, z)), f"{target} z {z}")

    def test_each_key_is_seen_from_where_its_place_is_entered(self):
        m = self.m
        views = ((self.eye(m.PASSAGE_FWD[2] - 16, 1984, "z4_passage_fwd"), m.BLUE_KEY_SPOT, "z4_tray"),
                 (self.eye(m.STORE[0] + 32, 2640, "z5_store"), m.YELLOW_KEY_SPOT, "z5_cart"),
                 (self.eye(4560, 1696, "z8_landing"), m.RED_KEY_SPOT, "z8_lid"))
        for eye, spot, zone in views:
            target = (*spot, self.sectors[self.plan[zone]]["heightfloor"] + KEY_SPRITE_MID)
            self.assertIsNone(self.blocked(eye, target), zone)

    def test_the_reactors_lid_glows_from_both_ways_in(self):
        """The red key's place is the reactor's lid, 192 over the hall's
        floor: from either way into the hall the lid's red-lit face shows."""
        m = self.m
        lid_face_z = m.REACTOR + 96
        for eye, target in ((self.eye(4384, 2272, "z7_tunnel_e"), (4736, m.VESSEL[3] + 1, lid_face_z)),
                            (self.eye(4384, 960, "z11_passage_e"), (4736, m.VESSEL[1] - 1, lid_face_z))):
            self.assertIsNone(self.blocked(eye, target), eye)

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        m = self.m
        views = (((m.PASSAGE_FWD[2] - 16, 1984), m.BLUE_KEY_SPOT),
                 ((m.STORE[0] + 32, 2640), m.YELLOW_KEY_SPOT),
                 ((4560, 1696), m.RED_KEY_SPOT),
                 (m.PLAYER_START, (m.RED_GATE[0], 352)))
        for (x0, y0), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"{t['type']} at ({t['x']}, {t['y']}) on ({x0}, {y0}) -> ({x1}, {y1})")

    def test_each_lock_is_seen_before_its_key(self):
        """Doom's grammar: all three locks are on round 0's ground (the red
        gate from the start, the blue and yellow doors from the dock); the
        keys come in rounds 1, 2 and 3."""
        m = self.m
        for portal in m.LOCK_PORTALS.values():
            self.assertEqual(0, self.first_round_with(self.plan[portal]), portal)
        self.assertEqual([1, 2, 3], [self.first_round_with(self.plan[m.KEY_ZONES[ed]])
                                     for ed in (m.ED_BLUE_CARD, m.ED_YELLOW_CARD, m.ED_RED_CARD)])

    # --- switches --------------------------------------------------------------
    def switch_lines(self):
        return [ld for ld in self.lines if "sideback" not in ld and ld.get("special") == SPECIAL_DOOR_OPEN]

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
            self.assertEqual(m.SWITCH_WIDTH, self.length(ld))
            s = self.sectors[self.front(ld)]
            self.assertEqual(m.SWITCH_HEIGHT, s["heightceiling"] - s["heightfloor"])
        self.assertEqual(m.EXIT_FACE, self.sides[self.exit_line()["sidefront"]]["texturemiddle"])

    def test_each_switch_opens_what_the_design_says(self):
        m = self.m
        found = {ld["arg0"]: self.front(ld) for ld in self.switch_lines()}
        self.assertEqual({m.TAG_WT_SHUTTER: self.plan["z4_swa_niche"],
                          m.TAG_BARRACKS_SHUTTER: self.plan["z11_swb_niche"]}, found)
        self.assertEqual(self.named("shutter_wt"), self.doors[m.TAG_WT_SHUTTER])
        self.assertEqual(self.named("shutter_barracks"), self.doors[m.TAG_BARRACKS_SHUTTER])

    def test_each_switch_is_in_sight_of_its_shutter(self):
        m = self.m
        for niche, eye_xy, target_xy in (("z4_swa_niche", (3680, 2080), (m.WT_SHUTTER[0] - 1, 1984)),
                                         ("z11_swb_niche", (3664, 1008), (m.BARRACKS_SHUTTER[2] + 1, 960))):
            room = self.sector_at(*eye_xy)
            eye = (*eye_xy, self.sectors[room]["heightfloor"] + VIEW_HEIGHT)
            self.assertIsNone(self.blocked(eye, (*target_xy, self.sectors[room]["heightfloor"] + 64)), niche)

    def test_the_barracks_shutter_is_wall_from_the_barracks(self):
        """The shortcut is found from behind (MAP05's station shutter): from
        the corridor it wears the corridor's concrete and has no special."""
        m = self.m
        face = [ld for ld in self.lines if "sideback" in ld
                and set(self._pair(ld)) == self.named("shutter_barracks", "z6_corridor")]
        self.assertEqual(1, len(face))
        ld = face[0]
        side = ld["sidefront"] if self.front(ld) == self.plan["z6_corridor"] else ld["sideback"]
        self.assertEqual(m.CONCRETE, self.sides[side]["texturetop"])
        self.assertFalse(ld.get("special"))

    def test_the_closets_are_wall_until_they_open(self):
        m = self.m
        for name in (*m.YARD_CLOSETS, *m.TUNNEL_CLOSETS):
            door = self.plan[f"{name}_door"]
            faces = [ld for ld in self.lines if "sideback" in ld and door in self._pair(ld)
                     and self.plan[name] not in self._pair(ld)]
            self.assertEqual(1, len(faces), name)
            ld = faces[0]
            side = ld["sidefront"] if self.front(ld) != door else ld["sideback"]
            self.assertNotIn(self.sides[side]["texturetop"], m.DOOR_LEAVES + (m.STEEL,), name)
            self.assertFalse(ld.get("special"), name)

    def test_the_exit_is_in_the_locomotives_cab(self):
        """The regulator in the cab: the cab is the locomotive's inside,
        boarded by its step from the bay, one tile high, the backhead
        (SDCAB1, its middle) on its south wall facing the door and the cab's
        sides (SDCAB2, a whole window on the back wall) on the rest; the exit
        is seen from the cab's door."""
        m = self.m
        cab = self.plan["z10_cab"]
        self.assertEqual(cab, self.sector_at(*((m.CAB_DOOR[0] + m.CAB_DOOR[2]) / 2, m.CAB_DOOR[1] + 8)))
        adj = self.adjacency(self.every_tag)
        self.assertIn(cab, adj[self.plan["z10_cab_step"]])
        self.assertIn(self.plan["z10_cab_step"], adj[self.plan["z10_bay"]])
        desk = [ld for ld in self.lines if "sideback" in ld and cab in self._pair(ld)
                and self.line_points(ld)[0][1] == self.line_points(ld)[1][1] == m.CAB[1]]
        self.assertTrue(desk)
        for ld in desk:
            key = "sidefront" if self.front(ld) == cab else "sideback"
            self.assertEqual(m.CAB_FRONT, self.sides[ld[key]]["texturebottom"])
            margin = (m.TILE - (m.CAB[2] - m.CAB[0])) // 2
            self.assertEqual(margin, self.sides[ld[key]].get("offsetx", 0), "the backhead's middle")
        walls = Counter()
        for ld in self.lines:
            if "sideback" not in ld or self.plan["prop_z10_loco"] not in self._pair(ld):
                continue
            for key in ("sidefront", "sideback"):
                if self.sides[ld[key]]["sector"] in (cab, self.plan["z10_exit_niche"]):
                    walls[self.sides[ld[key]]["texturebottom"]] += self.length(ld)
        self.assertEqual({m.CAB_FRONT, m.CAB_SIDE}, set(walls))
        back = [ld for ld in self.lines if "sideback" in ld and cab in self._pair(ld)
                and self.line_points(ld)[0][0] == self.line_points(ld)[1][0] == m.CAB[0]]
        self.assertEqual(1, len(back))
        key = "sidefront" if self.front(back[0]) == cab else "sideback"
        side = self.sides[back[0][key]]
        self.assertEqual(m.CAB_SIDE, side["texturebottom"])
        window = m.LUMP_WIDTH[m.CAB_SIDE]
        margin = (m.CAB[3] - m.CAB[1] - window) // 2
        self.assertEqual(window - margin, side.get("offsetx", 0), "one whole window in the middle")
        loco = self.sectors[self.plan["prop_z10_loco"]]
        self.assertEqual(loco["heightfloor"], self.sectors[cab]["heightceiling"], "the cab is closed")
        niche = self.sectors[self.plan["z10_exit_niche"]]
        for z in (32, 64, 96):
            target = (m.EXIT_NICHE[2] - 1, 352, niche["heightfloor"] + z)
            self.assertIsNone(self.blocked(self.eye(4416, 392, "z10_cab"), target), f"z {z}")

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
            if special not in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE):
                continue
            if "sideback" in ld:
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
            else:
                self.assertEqual(SPECIAL_DOOR_OPEN, special, f"linedef {i}")

    def test_no_opening_admits_the_panzermensch_but_not_the_heavy(self):
        """D67: no two-sided opening 64..71 high anywhere a heavy might walk
        (tests/test_panzermensch_sprites.py checks every map that places him)."""
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a, b = (self.sectors[s] for s in self._pair(ld))
            opening = min(a["heightceiling"], b["heightceiling"]) - max(a["heightfloor"], b["heightfloor"])
            self.assertFalse(64 <= opening < 72, f"{self.zone_of[self._pair(ld)[0]]} | "
                                                  f"{self.zone_of[self._pair(ld)[1]]}: {opening}")

    # --- population --------------------------------------------------------------
    def test_every_thing_stands_in_the_zone_its_table_names(self):
        m = self.m
        rows = ([(z, k, x, y) for z, k, x, y, *_ in m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in m.ITEMS + m.SECRET_ITEMS + m.AMMO])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is in {self.zone_of.get(self.sector_at(x, y))}")

    def test_the_monsters_are_the_bestiarys_own_numbers_in_mapinfo(self):
        assigned = _doomednums()
        for ednum, name in self.m.MONSTER_CLASSES.items():
            self.assertEqual(name, assigned.get(ednum), ednum)
        for ednum in self.m.ROUTE_WEAPONS + (self.m.ED_HAND_KATYUSHA,):
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertEqual(set(self.m.MONSTER_CLASSES), {t["type"] for t in self.monsters()})
        self.assertNotIn(21106, {t["type"] for t in self.things}, "the General is not here")

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

    def test_skill_flags_come_in_doom_pairs_and_nothing_is_on_no_skill(self):
        for t in self.things:
            self.assertTrue(any(t[f"skill{n}"] for n in range(1, 6)), t)
            self.assertEqual(t["skill1"], t["skill2"], t)
            self.assertEqual(t["skill4"], t["skill5"], t)

    def test_monsters_per_skill_and_nested(self):
        """Design section 9: a step above MAP05's 31 / 46 / 60."""
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for skill, n in counts.items():
            self.assertGreater(n, {2: 31, 3: 46, 4: 60}[skill])
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    # The route's beats, in the order it plays them (design section 6).
    BEATS = (("approach", ("z1_", "z2_", "z6_")), ("dock", ("z3_", "z4_")), ("workshops", ("z5_",)),
             ("reactor", ("closet_z7", "z7_", "z8_", "z11_")), ("bay", ("closet_z2", "z9_", "z10_")))

    def test_the_intensity_rises(self):
        """Ritmo creciente, in hit points met: each third of the route weighs
        more than the one before (the approach; the dock, the boat and the
        workshops; the reactor and the bay), on every skill, and the bay is
        the heaviest beat of all."""
        m = self.m
        for skill in SKILLS:
            beat = {name: 0 for name, _ in self.BEATS}
            for zone, kind, _x, _y, _a, tier in m.MONSTERS:
                if tier > skill:
                    continue
                name = next(n for n, prefixes in self.BEATS if zone.startswith(prefixes))
                beat[name] += self.hit_points[m.MONSTER_KINDS[kind]]
            v = [beat[n] for n, _ in self.BEATS]
            thirds = (v[0], v[1] + v[2], v[3] + v[4])
            self.assertLess(thirds[0], thirds[1], f"skill {skill}: {beat}")
            self.assertLess(thirds[1], thirds[2], f"skill {skill}: {beat}")
            self.assertEqual(max(v), beat["bay"], f"skill {skill}: {beat}")

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

    def test_both_factions_hold_the_base_where_the_design_says(self):
        """The Legion came by sea: pier, yard, dock, boat, barracks. The
        Reich came by rail: workshops, tunnel, reactor, passage. Both guard
        the rail tunnel and the bay. Hybrids anywhere; closets counter-attack."""
        m = self.m
        seen = defaultdict(set)
        for zone, kind, *_ in m.MONSTERS:
            faction = self.faction[m.MONSTER_KINDS[kind]]
            if zone.startswith(m.CLOSET_PREFIX):
                continue
            if zone.startswith(m.LEGION_GROUND):
                self.assertNotEqual("REICH", faction, f"{kind} in {zone}")
                seen["legion"].add(faction)
            elif zone.startswith(m.REICH_GROUND):
                self.assertNotEqual("LEGION", faction, f"{kind} in {zone}")
                seen["reich"].add(faction)
            else:
                self.assertTrue(zone.startswith(m.BOTH_GROUND), zone)
                seen["both"].add(faction)
        self.assertIn("LEGION", seen["legion"])
        self.assertIn("REICH", seen["reich"])
        self.assertTrue({"LEGION", "REICH"} <= seen["both"])

    def test_both_factions_hold_the_bay_on_every_skill(self):
        bay = self.plan["z10_bay"]
        for skill in SKILLS:
            here = [t for t in self.on(skill, self.monsters()) if self.sector_at(t["x"], t["y"]) == bay]
            self.assertTrue({"LEGION", "REICH"} <= {self.faction[t["type"]] for t in here}, skill)

    def test_the_heavies(self):
        """A Panzermensch in the workshops, the reactor hall and the bay on
        every skill; the heavy in the reactor hall and the bay from skill 3;
        Doughboys only where the room is high enough to float: the yard
        (sky), the dock (448) and the bay (320)."""
        m = self.m
        pz = self.things_of({m.ED_PANZERMENSCH})
        self.assertEqual({2: 3, 3: 3, 4: 3}, {s: len(self.on(s, pz)) for s in SKILLS})
        every = {self.zone_of[self.sector_at(t["x"], t["y"])] for t in pz if t["skill2"]}
        self.assertEqual({"z5_workshop", "z8_hall", "z10_bay"}, every)
        heavy = self.things_of({m.ED_PANZER_HEAVY})
        self.assertEqual({2: 0, 3: 2, 4: 2}, {s: len(self.on(s, heavy)) for s in SKILLS})
        self.assertEqual(self.named("z8_hall", "z10_bay"), {self.sector_at(t["x"], t["y"]) for t in heavy})
        for t in self.things_of({m.ED_DOUGHBOY}):
            s = self.sectors[self.sector_at(t["x"], t["y"])]
            self.assertGreaterEqual(s["heightceiling"] - s["heightfloor"], FLYING_ROOM, t)

    def test_every_closet_holds_a_fight_and_opens_with_its_lock(self):
        m = self.m
        for names, tag in ((m.TUNNEL_CLOSETS, m.TAG_YELLOW_DOOR), (m.YARD_CLOSETS, m.TAG_RED_GATE)):
            for name in names:
                door = self.plan[f"{name}_door"]
                self.assertEqual(tag, self.sectors[door]["id"], name)
                inside = [t for t in self.on(2, self.monsters()) if self.sector_at(t["x"], t["y"]) == self.plan[name]]
                self.assertTrue(inside, f"{name} is empty on skill 2")
                first = next(k for k, (opened, _r, _h) in enumerate(self.rounds) if tag in opened)
                self.assertNotIn(self.plan[name], self.rounds[first - 1][1], f"{name} open early")
                self.assertIn(self.plan[name], self.rounds[first][1], f"{name} never opens")
        self.assertEqual(self.named("z13_yellow_door", "closet_z7_a_door", "closet_z7_b_door"),
                         self.doors[m.TAG_YELLOW_DOOR])
        self.assertEqual(self.named("z13_red_gate", "closet_z2_e_door", "closet_z2_n_door"),
                         self.doors[m.TAG_RED_GATE])

    def test_the_weapons_are_on_every_skill_on_the_route(self):
        """Pistol start (MAP07 may leave him with anything): the IZh on the
        pier, the PPSh in the barracks, the RPG-7 on the dock's gallery, the
        ROKS-3 in the torpedo store; each once, on every skill, never in a
        secret."""
        m = self.m
        for ednum, zone, stage in ((m.ED_IZH, "z1_pier", 0), (m.ED_PPSH, "z6_hall", 0),
                                   (m.ED_AKM, "z3_gallery", 0),
                                   (m.ED_RPG7, "z3_gallery", 0), (m.ED_ROKS3, "z5_store", 2)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertFalse(self.sectors[where].get("special"))
            self.assertIn(where, self.rounds[stage][1])
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}))

    def test_the_rpg_is_met_before_the_first_panzermensch(self):
        """The RPG-7 lies in round 0; the first Panzermensch stands in the
        workshops, round 2."""
        m = self.m
        rpg = self.things_of({m.ED_RPG7})[0]
        self.assertEqual(0, self.first_round_with(self.sector_at(rpg["x"], rpg["y"])))
        for t in self.things_of({m.ED_PANZERMENSCH, m.ED_PANZER_HEAVY}):
            self.assertGreaterEqual(self.first_round_with(self.sector_at(t["x"], t["y"])), 2)

    def test_consumables_scale_down(self):
        m = self.m
        fixed = (self.monster_numbers | set(m.ROUTE_WEAPONS)
                 | {m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_BLUE_CARD, m.ED_RED_CARD})
        fixed |= {ednum for _z, ednum, *_ in m.AMMO}     # D119: ammunition scales with the monsters
        for kind in {t["type"] for t in self.things} - fixed:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]] for t in self.on(skill, self.monsters()))

    def on_route(self, things):
        off = self.named(*self.m.SECRET_ZONES)
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in off]

    def ammo_placed(self, skill):
        placed = self.on_route(self.on(skill, self.things))
        return sum(SHELLS_GIVEN.get(t["type"], 0)
                   + ROUNDS_GIVEN.get(t["type"], 0) / ROUNDS_PER_SHELL
                   + AKM_ROUNDS_GIVEN.get(t["type"], 0) / AKM_ROUNDS_PER_SHELL
                   + ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                   + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL
                   + GRENADES_GIVEN.get(t["type"], 0) * SHELLS_PER_GRENADE for t in placed)

    def test_g3_8_the_ammo_budget(self):
        """D119: on every skill, ammunition on the route is inside that
        skill's G3-8 band of what killing every monster takes (1.5-2.0 /
        1.3-1.6 / 1.2-1.45 on skills 2 / 3 / 4). No drop and no secret
        counted."""
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            low, high = G3_8_BANDS[skill]
            self.assertGreaterEqual(have, low * need, f"skill {skill}: {have} for {need}")
            self.assertLessEqual(have, high * need, f"skill {skill}: {have} for {need}")

    def start_rounds(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        """At every round of the route, the damage placed so far plus the
        starting rounds is at least the floor of the skill's G3-8 band times
        the hit points met (D119: no stage under the minimum)."""
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = self.start_rounds() * PPSH_AVERAGE
            for stage, (_opened, reach, _held) in enumerate(self.rounds):
                here = [t for t in self.on_route(self.on(skill, self.things))
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                hp_so_far += sum(self.hit_points.get(t["type"], 0) for t in here)
                damage += sum(SHELLS_GIVEN.get(t["type"], 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(t["type"], 0) * PPSH_AVERAGE
                              + AKM_ROUNDS_GIVEN.get(t["type"], 0) * AKM_AVERAGE
                              + ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE
                              + CELLS_GIVEN.get(t["type"], 0) * ROKS_AVERAGE for t in here)
                self.assertGreaterEqual(damage, G3_8_BANDS[skill][0] * hp_so_far, f"skill {skill}, stage {stage}")
                seen = reach

    def test_the_gunners_three_four_five_by_skill_by_cover(self):
        """D116: the Legion's machine-gunners, 3 / 4 / 5 on skills 2 / 3 / 4,
        never in a closet, each with something to stand behind within 128
        (a prop, a wall or a step)."""
        m = self.m
        gunners = self.things_of({m.ED_GUNNER})
        self.assertEqual({2: 3, 3: 4, 4: 5}, {s: len(self.on(s, gunners)) for s in SKILLS})
        for t in gunners:
            here = self.sector_at(t["x"], t["y"])
            zone = self.zone_of[here]
            self.assertFalse(zone.startswith(m.CLOSET_PREFIX), zone)
            near = {self.sector_at(t["x"] + dx, t["y"] + dy)
                    for dx in range(-128, 129, 32) for dy in range(-128, 129, 32)}
            stepped = any(self.sectors[s]["heightfloor"] != self.sectors[here]["heightfloor"]
                          for s in near if s is not None)
            self.assertTrue(None in near or near & self.unwalkable or stepped,
                            f"gunner at ({t['x']}, {t['y']}) in {zone}: nothing to stand behind")

    def test_the_ammunition_follows_the_monsters_and_is_cut(self):
        """D119: the route's ammunition is map.py's AMMO, apart from ITEMS,
        and appears from its lowest skill tier up, like the monsters it pays
        for: a harder skill never holds fewer pickups, skills 2 and 3 hold
        fewer than before D119 and skill 4 less (D116's 4 / 3 / 2 magazines are gone with
        the scaling down)."""
        m = self.m
        ammo = {ednum for _z, ednum, *_ in m.AMMO}
        self.assertTrue(all(lowest in SKILLS for *_, lowest in m.AMMO))
        self.assertFalse(ammo & {ednum for _z, ednum, *_ in m.ITEMS}, "ammunition left in ITEMS")
        n = {s: sum(t["type"] in ammo for t in self.on_route(self.on(s, self.things))) for s in SKILLS}
        self.assertLessEqual(n[2], n[3])
        self.assertLessEqual(n[3], n[4])
        for skill in (2, 3):
            self.assertLess(n[skill], PRE_D119_AMMO_PICKUPS[skill], f"skill {skill}")
        # Skill 4 was already the leanest, and the AKM, which leads every
        # stage since the PM's amendment, comes 30 rounds a pickup: there the
        # cut is in the stock, not the count.
        self.assertLess(self.ammo_placed(4), PRE_D119_STOCK_SKILL_4)

    def damage_by_pool(self, skill):
        placed = self.on_route(self.on(skill, self.things))
        return {pool: sum(given.get(t["type"], 0) * average for t in placed)
                for pool, (given, average) in POOLS.items()}

    def test_shells_at_most_35_percent_with_the_drops(self):
        """BALANCE 8.3 (D119, "siempre acabas con la escopeta"): on every
        skill, the shells placed on the route (the IZh's own 8 counted) plus
        the troopers' dropped IZhs are at most 35 % of everything placed plus
        every drop, in shell-equivalents."""
        m = self.m
        for skill in SKILLS:
            placed = self.on_route(self.on(skill, self.things))
            classes = [m.MONSTER_CLASSES[t["type"]] for t in self.on(skill, self.monsters())]
            shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed) + sum(DROPPED_SHELLS.get(c, 0) for c in classes)
            everything = sum(self.stage_pools(skill)[-1][0].values()) + sum(DROPS.get(c, 0) for c in classes)
            self.assertLessEqual(shells, SHELL_SHARE_MAX * everything, f"skill {skill}: {shells} of {everything}")

    def stage_pools(self, skill):
        """Per stage of the route, cumulative: the shell-equivalents placed so
        far by pool, the route weapons met so far (in ROUTE_WEAPONS' order
        within a stage), whether a Legion gunner (whose drop is AKM rounds)
        stands in reach, and the stage's own shell-equivalents and average
        damage by pool."""
        placed = self.on_route(self.on(skill, self.things))
        gunners = [t for t in self.on(skill, self.monsters()) if t["type"] == self.m.ED_GUNNER]
        total = dict.fromkeys(SHELL_EQUIVALENTS, 0)
        seen, met, out = set(), [], []
        for _opened, reach, _held in self.rounds:
            here = [t for t in placed if self.sector_at(t["x"], t["y"]) in reach - seen]
            met += sorted((t["type"] for t in here if t["type"] in WEAPON_POOL), key=self.m.ROUTE_WEAPONS.index)
            own = {pool: sum(given.get(t["type"], 0) * per for t in here)
                   for pool, (given, per) in SHELL_EQUIVALENTS.items()}
            total = {pool: total[pool] + own[pool] for pool in total}
            gunner = any(self.sector_at(t["x"], t["y"]) in reach for t in gunners)
            damage = {pool: sum(given.get(t["type"], 0) * average for t in here)
                      for pool, (given, average) in POOLS.items()}
            out.append((total, list(met), gunner, own, damage))
            seen = reach
        return out

    def boss_stages(self, skill):
        """The stages holding a boss or a mini-boss placed on this skill."""
        where = [self.sector_at(t["x"], t["y"]) for t in self.on(skill, self.monsters())
                 if self.m.MONSTER_CLASSES[t["type"]] in BOSS_CLASSES]
        return {next(k for k, r in enumerate(self.rounds) if w in r[1]) for w in where}

    def test_each_pool_after_its_weapon_and_the_bullets_lead(self):
        """BALANCE 8.4.1-2 with the PM's amendment (D119: one weapon must not
        carry the game, the shotgun not swapped for the rocket launcher): in
        each stage a pool is placed only once its weapon has been met (the
        Clip from the start, AKM rounds from the AKM or the first gunner).
        Outside a boss's or a mini-boss's stage, PG-7V are at most 30 % of
        the stage's damage and the newest bullet weapon's pool (the AKM's
        once it is met, else the PPSh's) has the largest share of the
        stage's non-shell ammunition, at least 40 %; fuel never needs to
        lead. In the boss's stage the PG-7V may lead instead."""
        for skill in SKILLS:
            bosses = self.boss_stages(skill)
            for stage, (_total, met, gunner, own, damage) in enumerate(self.stage_pools(skill)):
                open_pools = {"ppsh"} | {WEAPON_POOL[w] for w in met} | ({"akm"} if gunner else set())
                for pool, amount in own.items():
                    self.assertTrue(amount == 0 or pool in open_pools, f"skill {skill}, stage {stage}: {pool} early")
                rest = {pool: amount for pool, amount in own.items() if pool != "shells"}
                if not sum(rest.values()):
                    continue
                leads = {"akm" if self.m.ED_AKM in met else "ppsh"}
                if stage in bosses:
                    leads.add("rockets")
                else:
                    self.assertLessEqual(damage["rockets"], ROCKET_SHARE_MAX * sum(damage.values()),
                                         f"skill {skill}, stage {stage}: {damage}")
                top = max(rest.values())
                self.assertTrue(any(rest[p] == top and rest[p] >= NEWEST_SHARE_MIN * sum(rest.values())
                                    for p in leads), f"skill {skill}, stage {stage}: {rest}, {leads} lead")
    def test_fuel_sparing_and_the_akm_ahead_of_the_ppsh(self):
        """D119, the PM's brief: fuel at most 15 % of the route's damage on
        every skill (the ROKS-3 is toned down), and the AKM, the newest gun
        of slot 4, carries more than the PPSh."""
        for skill in SKILLS:
            damage = self.damage_by_pool(skill)
            total = sum(damage.values())
            self.assertLessEqual(damage["fuel"], FUEL_SHARE_MAX * total, f"skill {skill}: {damage}")
            self.assertGreater(damage["akm"], damage["ppsh"], f"skill {skill}: {damage}")

    def test_the_boss_is_the_heavy_weapons_job(self):
        """BALANCE 8.4.3 (D119): in the boss's stage, PG-7V and fuel placed
        there cover at least its shells (the Chrome Marshal's 48). (8.4.3's second half, every
        monster but the boss on shells and rounds alone at the skill's floor,
        is not tested: with 8.3's 35 % and 8.4.2's rockets leading it cannot
        hold under the band's ceiling; flagged to the PM.)"""
        m = self.m
        boss_number = m.ED_CHROME_GENERAL
        boss = SHELLS_TO_KILL[m.MONSTER_CLASSES[boss_number]]
        for skill in (3, 4):
            spot = [t for t in self.on(skill, self.monsters()) if t["type"] == boss_number][0]
            where = self.sector_at(spot["x"], spot["y"])
            stage = next(k for k, r in enumerate(self.rounds) if where in r[1])
            own = self.stage_pools(skill)[stage][3]
            self.assertGreaterEqual(own["rockets"] + own["fuel"], boss, f"skill {skill}: {own}")
    def test_the_chrome_marshal_holds_the_bay_on_skills_3_and_4(self):
        """D116: the Liberty Colossus as the bay's mini-boss, since D123 the
        Chrome Marshal in his place (the colossus's body, behaviour and 3000
        HP in the General's chrome; the statue went to MAP06 alone): skills 3
        and 4 only, at the colossus's spot, (4352, 512) facing west, under
        the bay's roof with room for his 110, and the bay and the
        rail tunnel carry rockets and fuel for him: a third of his hit points
        (3000 since D119) in the two alone on skills 3 and 4 (he takes no
        blast). D119: and no more than the fight there takes - the two's
        stock inside the skill's G3-8 band of the Marshal and the monsters
        around him."""
        m = self.m
        colossi = self.things_of({m.ED_CHROME_GENERAL})
        self.assertEqual({2: 0, 3: 1, 4: 1}, {s: len(self.on(s, colossi)) for s in SKILLS})
        self.assertEqual({(t["x"], t["y"], t["angle"]) for t in colossi}, {(4352, 512, 180)})
        self.assertNotIn(21111, {t["type"] for t in self.things}, "D123: the statue is MAP06's alone")
        self.assertEqual(m.MONSTER_CLASSES[m.ED_CHROME_GENERAL], "SD_ChromeGeneral")
        bay = self.named("z10_bay", "z9_tunnel", "z9_rails", "z9_refuge_1", "z9_refuge_2", "z10_rails")
        self.assertEqual({self.plan["z10_bay"]}, {self.sector_at(t["x"], t["y"]) for t in colossi})
        hp = self.hit_points[m.ED_CHROME_GENERAL]
        self.assertEqual(hp, 3000)
        for skill in (3, 4):
            here = [t for t in self.on(skill, self.things) if self.sector_at(t["x"], t["y"]) in bay]
            heavy = sum(ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE
                        + CELLS_GIVEN.get(t["type"], 0) * ROKS_AVERAGE for t in here)
            self.assertGreaterEqual(3 * heavy, hp, f"skill {skill}: {heavy}")
            stock = sum(given.get(t["type"], 0) * average for t in here for given, average in POOLS.values())
            bill = sum(self.hit_points.get(t["type"], 0) for t in here if t["type"] in self.monster_numbers)
            low, high = G3_8_BANDS[skill]
            self.assertGreaterEqual(stock, low * bill, f"skill {skill}: {stock} for {bill}")
            self.assertLessEqual(stock, high * bill, f"skill {skill}: {stock} for {bill}")

    def test_health_and_armour_on_skill_4(self):
        m = self.m
        found = Counter(t["type"] for t in self.on_route(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 12)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        self.assertEqual(3, self.first_round_with(self.sector_at(vest["x"], vest["y"])),
                         "the heavy vest before the yard's closets and the bay")

    # --- secrets -------------------------------------------------------------------
    def panel_lines(self, tag):
        return [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_OPEN and ld["arg0"] == tag]

    def test_three_secrets_each_a_push_panel_with_a_way_back(self):
        m = self.m
        adj = self.adjacency(self.every_tag)
        for tag, panel, store in ((m.TAG_S1_PANEL, "s1_panel", "s1_store"),
                                  (m.TAG_S2_PANEL, "s2_panel", "s2_store"),
                                  (m.TAG_S3_PANEL, "s3_panel", "s3_cab")):
            lines = self.panel_lines(tag)
            self.assertEqual(2, len(lines), panel)
            for ld in lines:
                self.assertEqual(self.plan[panel], self.back(ld))
                self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial") and ld.get("secret"), panel)
            self.assertEqual(0, self.first_round_with(self.plan[store]), store)
            self.assertNotIn(self.plan[store], self.reachable(self.every_tag - {tag}), f"{store} without its panel")
            self.assertIn(self.start, self.flood(adj, self.plan[store]), f"a way back from {store}")
            self.assertTrue(self.sectors[self.plan[store]]["special"] & m.SECTOR_SPECIAL_SECRET)

    def test_the_first_two_clues_are_a_stretch_set_back_in_shadow(self):
        """MAP01's rule, a comparison and never a sign: S1 is the one stretch
        of the yard's east cliff that stands 16 back, darker than the yard,
        its panel the cliff itself; S2 is the one locker of the dormitory's
        row that stands back in shadow, its panel a locker."""
        m = self.m
        for niche, panel, room, face in (("s1_niche", "s1_panel", "z2_yard", m.ROCK),
                                         ("s2_niche", "s2_panel", "z6_dorm", m.LOCKER)):
            n = self.sectors[self.plan[niche]]
            self.assertLess(n["lightlevel"], self.sectors[self.plan[room]]["lightlevel"], niche)
            self.assertIn(self.plan[room], self.neighbours[self.plan[niche]])
            faces = [ld for ld in self.panel_lines(self.sectors[self.plan[panel]]["id"])
                     if self.front(ld) == self.plan[niche]]
            self.assertEqual(1, len(faces))
            self.assertEqual(face, self.sides[faces[0]["sidefront"]]["texturetop"])
            self.assertEqual(m.NICHE_DEPTH, min(abs(a - b) for a, b in (
                (getattr(m, f"{niche.upper()}")[0], getattr(m, f"{niche.upper()}")[2]),
                (getattr(m, f"{niche.upper()}")[1], getattr(m, f"{niche.upper()}")[3]))))

    def test_the_third_clue_is_the_cranes_shut_cab(self):
        """The crane on the pier has a stair and a deck; its cab is shut by a
        corrugated gate, which is S3's panel."""
        m = self.m
        face = [ld for ld in self.panel_lines(m.TAG_S3_PANEL) if self.front(ld) == self.plan["z1_crane_deck"]]
        self.assertEqual(1, len(face))
        self.assertEqual(m.ROAD_GATE, self.sides[face[0]["sidefront"]]["texturetop"])

    def test_s3_holds_the_hand_katyusha_for_the_bay(self):
        m = self.m
        found = self.things_of({m.ED_HAND_KATYUSHA})
        self.assertEqual(1, len(found))
        t = found[0]
        self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)))
        self.assertEqual(self.plan["s3_cab"], self.sector_at(t["x"], t["y"]))
        self.assertEqual("SD_HandKatyusha", _doomednums().get(m.ED_HAND_KATYUSHA))
        cells = [c for c in self.things_of({m.ED_CELL}) if self.sector_at(c["x"], c["y"]) == self.plan["s3_cab"]]
        self.assertGreaterEqual(len(cells) * 20, 40, "one more volley's fuel beside it")


if __name__ == "__main__":
    unittest.main()
