"""MAP09 Tunguska, episode 3's last map, v1 (docs/levels/MAP09-tunguska.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map06_red_square.py (whose helpers this file repeats, so each
map's tests stay one file). The contract:

* structure: every sector closed and clockwise, no duplicate vertex, no step
  up higher than a stair step; the campaign's biggest map;
* only approved, packed textures (and the engine's sky marker F_SKY1); every
  picture, board, flag, signal and door leaf one whole tile; the three locks
  wear their key's look; the episode's "Taiga/Alien" set where the design
  puts it (D113), the stand-ins gone, every face of it on the world's grid,
  each glyph plate whole, the portal framed, the locomotive's cab whole;
* the open air: every outdoor zone has the sky, every closed sky block (the
  roofs) is a prop; the fallen trunks lie away from the crater, seen over and
  not climbed; the standing forest's trunks are columns of void;
* the pits hurt (acid in the works and the crater, molten metal in the
  refinery) and are one step deep: walked out of;
* everything is reachable playing the map's own doors, its THREE keys in
  order, the red key's pickup (the works' closets) and the boss's death (the
  bunker's gate); no trap at any stage; the exit only after the boss dies;
* the key grammar (D58): each lock seen before its key, each key seen from
  where the player comes, in its lock's colour of light, alone on its spot,
  and no monster between;
* three secrets, none needed, each with a way back; the Hand Katyusha in S2;
* the population: per skill and nested, on the bestiary's MAPINFO numbers,
  with room for every body, factions where the design puts them, the boss
  (the Consortium since D116) at MAP09_BOSS_SPOT with the portal at its back,
  the Legion's gunners three, four and five by skill; weapons on the route
  (the AKM after the PPSh), health and armour scaled down, the ammunition
  following the monsters (D119): inside G3-8's band on every skill, at the
  skill's floor at every stage (the boss's servants in the bill), shells at
  most 35 % with the drops, each pool after its weapon and the newest
  leading, fuel sparing; the crater's own stock for the boss and inside the
  band; health on skill 4;
* V3's pickup events (D120's A2 and A3; tests/_pickup_events_e3.py): the
  blue key opens the laboratory's quarantine room, the yellow key brings the
  works' cargo lift down, the red key opens the works' closets (v1's, now
  with lamps); each hidden until it fires, warned by a flickering lamp,
  never needed, never a trap.

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
import _pickup_events_e3 as pickup_events  # noqa: E402

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
    "SD_PanzermenschSchwer": "panzermensch_schwer.zs",
    "SD_LegionGunner": "legion_gunner.zs",
    "SD_Consortium": "consortium.zs",
}
CLASS_PARENT = {"SD_PanzermenschSchwer": "SD_Panzermensch"}
# G3-8 as MAP03 measures it (tests/test_map03_factory.py): kills in IZh shells,
# at the ruler's ~62.5 HP a shell (the General's 3000 was 48). D116: the
# gunner's 80 is two (one barrel kills him half the time). D119: the
# Consortium's 4000 is 64 (its 9000 was 144).
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8,
                  "SD_PanzermenschSchwer": 16, "SD_LegionGunner": 2, "SD_Consortium": 64}
# The Consortium's servants, added to its bill (H; its design, section 3-4.4).
# At 9000 HP a long fight's worth was four rooted pairs, the Breach's wave and
# five free pairs. D119 brings it to 4000 with the Breach still at half (2000
# a phase, 44 % of the old 4500), and the portal calls on every 4th attack
# rooted and every 3rd free, so the fight calls about half as often: two
# rooted pairs (rifleman and trooper, 50 HP a pair), the Breach's wave of four
# (600, unchanged) and two free pairs (hound and trooper, 180 a pair).
SERVANT_HIT_POINTS = 2 * 50 + 600 + 2 * 180
SERVANT_SHELLS = 2 * 2 + (1 + 1 + 3 + 6) + 2 * (3 + 1)
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
BOSS_CLASSES = ("SD_LibertyColossus", "SD_Consortium")
PRE_D119_STOCK_SKILL_4 = 759.0   # the route's shell-equivalents on skill 4 before D119
PRE_D119_AMMO_PICKUPS = {2: 97, 3: 88, 4: 72}   # the route's, before D119 (skills 2 / 3 / 4)
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
AKM_ROUNDS_GIVEN = {21020: 30, 21008: 30}   # a magazine; the rifle comes with one
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
    """RADIUS, HEIGHT, HEALTH and FACTION of a bestiary class, from its file:
    the FIRST constant of each (the boss's file also declares a quake's and a
    stomp's radius further down)."""
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


class Map09Test(pickup_events.PickupEventChecks, unittest.TestCase):

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
        cls.rounds = cls().progression_of(kills=True)   # a bare instance: the model asserts nothing
        cls.every_tag = set().union(*(r[0] for r in cls.rounds))

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

    def thing_specials(self, numbers):
        """[(tag, sector)] for every thing of `numbers` carrying a special on a
        tag (Door_Open; since V3 also Floor_LowerToLowest, the works' lift)."""
        return [(t["arg0"], self.sector_at(t["x"], t["y"])) for t in self.things
                if t["type"] in numbers and t.get("special") in (SPECIAL_DOOR_OPEN,
                                                                 pickup_events.SPECIAL_FLOOR_LOWER_TO_LOWEST)]

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

    def exit_sector(self):
        return self.front(self.exit_line())

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
        for texture in (m.CONTROL, m.FLAG_USSR_1, m.FLAG_USSR_2, m.SIGNAL, m.LOCKER, m.TURBINE,
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
        self.assertEqual("SDDOORB", m.DOOR, "the blue key's own door (D113)")
        leaf = {m.TAG_BLUE_DOOR: m.DOOR, m.TAG_YELLOW_DOOR: m.DOOR_YELLOW, m.TAG_RED_DOOR: m.DOOR_RED}
        for ld in self.lines:
            if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE:
                self.assertEqual(leaf[ld["arg0"]], self.sides[ld["sidefront"]]["texturetop"])

    # --- the Taiga/Alien set (D113) -------------------------------------------
    def walls_of(self, texture):
        """{zone} of every sector that has a drawn face wearing `texture`."""
        return {zone for _, zone in self.faces_of(texture)}

    def test_the_taiga_set_dresses_the_map(self):
        """The episode's own set where the design puts it; the stand-ins gone."""
        m = self.m
        floors = {"z1_yard": m.MOSS, "z2_taiga": m.BURNT, "z3_yard": m.MOSS, "z4_forest": m.PEAT,
                  "z5_edge": m.BURNT, "z7_rim": m.BURNT, "z1_ballast": m.BALLAST}
        floors.update({f"z8_tier_{k}": m.BURNT for k in range(1, m.TERRACES + 1)})
        for zone, flat in floors.items():
            self.assertEqual(flat, self.sectors[self.plan[zone]]["texturefloor"], zone)
        self.assertEqual(m.BURNT_TURN, self.sectors[self.plan["z2_taiga"]].get("rotationfloor"))
        used = {sd.get(p) for sd in self.sides for p in ("texturetop", "texturemiddle", "texturebottom")}
        used |= {s[k] for s in self.sectors for k in ("texturefloor", "textureceiling")}
        for gone in ("SDTUBB1", "SDDOOR1"):
            self.assertNotIn(gone, used, f"{gone} was a stand-in")
        # Planking only on the goods wagon and the platform's edge; rust only on the vats.
        self.assertEqual({"z1_ballast", "z1_track", "z1_yard"}, self.walls_of(m.WAGON))
        self.assertEqual({"z6_refinery"}, self.walls_of(m.RUST))
        # Logs on every hut, inside and out, and on the palisade.
        logs = self.walls_of(m.LOG_WALL)
        for zone in ("z1_halt", "z1_yard", "z3_izba_a", "z3_izba_b", "z3_izba_c", "z3_yard",
                     "z2_taiga", "s1_store"):
            self.assertIn(zone, logs)
        # Charred larch for the treeline and the trunks, birch here and there.
        for zone in ("z1_ballast", "z2_taiga", "z4_forest"):
            self.assertIn(zone, self.walls_of(m.BARK))
        self.assertTrue({"z2_taiga", "z4_forest", "z1_ballast"} <= self.walls_of(m.BIRCH))
        self.assertTrue(m.birch_trunks())
        self.assertLess(len(m.birch_trunks()), len(m.trunk_spots()) // 4, "birch is the odd one")
        for n, (x, y, length) in enumerate(m.LOGS, start=1):
            s = self.sectors[self.plan[f"prop_z2_log_{n}"]]
            self.assertEqual(m.MOSS if n in m.BIRCH_LOGS else m.BURNT, s["texturefloor"], n)
        # The invaders' metal on their works, fence, containment and crater.
        alien = self.walls_of(m.ALIEN)
        for zone in ("z5_works", "z3_yard", "z4_forest", "z7_rim", "z8_floor", "z8_tier_4",
                     "z5_red_portal", "closet_z5_w"):
            self.assertIn(zone, alien)
        self.assertEqual({"z5_works", "z7_rim", "z8_floor"}, self.walls_of(m.GLYPH))

    def test_every_glyph_plate_is_whole(self):
        """SDGLYP1 is one 64 plate: every line wearing it is a whole number of
        plates, starting on a plate's edge, and its faces a whole number of
        tiles high (the pylons two, the towers two, the gates' walls four)."""
        m = self.m
        n = 0
        for ld in self.lines:
            for side in [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else []):
                sd = self.sides[side]
                if m.GLYPH not in (sd.get("texturemiddle"), sd.get("texturebottom")):
                    continue
                if self.sectors[sd["sector"]]["heightfloor"] == self.sectors[sd["sector"]]["heightceiling"]:
                    continue
                (a, b) = self.line_points(ld)
                self.assertEqual(0, (abs(a[0] - b[0]) + abs(a[1] - b[1])) % 64, ld)
                self.assertEqual(0, sd.get("offsetx", 0), ld)
                n += 1
        self.assertGreaterEqual(n, 4 * len(m.PYLONS) + 4 * len(m.TOWERS) + len(m.GATE_GLYPHS))
        for height, zone in self.faces_of(m.GLYPH):
            self.assertEqual(0, height % m.TILE_SIZE, zone)

    def drawn_refs(self, texture):
        """[(offsety, the height the face is pegged to)] for every drawn part
        wearing `texture` (Doom's pegging, as map.drawn_parts has it)."""
        out = []
        for ld in self.lines:
            pairs = [(ld["sidefront"], ld.get("sideback"))]
            if "sideback" in ld:
                pairs.append((ld["sideback"], ld["sidefront"]))
            for side, other in pairs:
                sd = self.sides[side]
                s = self.sectors[sd["sector"]]
                if other is None:
                    if sd.get("texturemiddle") == texture:
                        out.append((sd.get("offsety", 0), s["heightfloor"] if ld.get("dontpegbottom")
                                    else s["heightceiling"]))
                    continue
                o = self.sectors[self.sides[other]["sector"]]
                if o["heightfloor"] > s["heightfloor"] and sd.get("texturebottom") == texture:
                    out.append((sd.get("offsety", 0), s["heightceiling"] if ld.get("dontpegbottom")
                                else o["heightfloor"]))
        return out

    def test_the_new_set_sits_on_the_world_grid(self):
        """Every face of the logs, the bark, the alien metal and the glyphs has
        its rows on one grid from the ground: the logs' joints meet every
        floor (the huts' one step up too), the glyph plates and the membrane
        run on through the terraces."""
        m = self.m
        for texture in (m.LOG_WALL, m.BARK, m.BIRCH, m.ALIEN, m.GLYPH):
            refs = self.drawn_refs(texture)
            self.assertTrue(refs, texture)
            for offsety, ref in refs:
                self.assertEqual(0, (ref + offsety - m.GROUND) % m.TILE_SIZE, (texture, ref, offsety))
        # SDLOGW1's joints every 16: the huts' floor (16) lands on one.
        self.assertEqual(0, m.HUT_FLOOR % 16)

    def test_the_portal_has_its_frame(self):
        """Four posts of SDPRTE1 in the field's corners, over the field, each
        32 face showing the middle of the lump (the cobalt channel); between
        them the field is one tile of SDPORT1 wide."""
        m = self.m
        posts = m.frame_posts()
        self.assertEqual(4, len(posts))
        for n, (x1, y1, x2, y2) in enumerate(posts, start=1):
            s = self.sectors[self.plan[f"prop_z8_frame_{n}"]]
            self.assertEqual(m.FRAME_TOP, s["heightfloor"])
            self.assertGreater(m.FRAME_TOP, m.PORTAL_TOP)
            self.assertEqual(self.plan[f"prop_z8_frame_{n}"], self.sector_at((x1 + x2) // 2, (y1 + y2) // 2))
        rims = [(ld, self.sides[s]) for ld in self.lines
                for s in [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else [])
                if self.sides[s].get("texturebottom") == m.PORTAL_RIM
                and self.sectors[self.sides[s]["sector"]]["heightfloor"] < m.FRAME_TOP]
        self.assertTrue(rims)
        for ld, sd in rims:
            (a, b) = self.line_points(ld)
            self.assertEqual(m.FRAME_POST, abs(a[0] - b[0]) + abs(a[1] - b[1]))
            self.assertEqual(m.FRAME_OFFSET, sd["offsetx"])
        fx1, fy1, fx2, fy2 = m.PORTAL_FIELD
        self.assertEqual(m.TILE_SIZE, fx2 - fx1 - 2 * m.FRAME_POST)
        self.assertEqual(m.TILE_SIZE, fy2 - fy1 - 2 * m.FRAME_POST)

    def test_the_locomotive_has_its_cab(self):
        """The train he came on: a cab the player steps into from beside the
        platform, SDCAB1 forward as one whole 128 picture, SDCAB2 on the
        other walls, each a whole tile high on the cab's floor."""
        m = self.m
        cab = self.plan["z1_cab"]
        self.assertIn(cab, self.reachable(frozenset()))
        fronts = [(ld, self.sides[s]) for ld in self.lines
                  for s in [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else [])
                  if self.sides[s].get("texturebottom") == m.CAB_FRONT and self.sides[s]["sector"] == cab]
        self.assertEqual(1, len(fronts))
        ld, sd = fronts[0]
        (a, b) = self.line_points(ld)
        self.assertEqual(128, abs(a[0] - b[0]) + abs(a[1] - b[1]))
        self.assertEqual(0, sd["offsetx"])
        self.assertEqual([(m.TILE_SIZE, "z1_cab")], self.faces_of(m.CAB_FRONT))
        self.assertTrue(self.faces_of(m.CAB_SIDE))
        for height, zone in self.faces_of(m.CAB_SIDE):
            self.assertEqual((m.TILE_SIZE, "z1_cab"), (height, zone))
        for texture in (m.CAB_FRONT, m.CAB_SIDE):
            for offsety, ref in self.drawn_refs(texture):
                self.assertEqual(0, (ref + offsety - m.HUT_FLOOR) % m.TILE_SIZE, texture)
        # Every SDCAB2 run on the cab's walls is whole windows.
        for ld in self.lines:
            for s in [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else []):
                if self.sides[s].get("texturebottom") == m.CAB_SIDE and self.sides[s]["sector"] == cab:
                    (a, b) = self.line_points(ld)
                    self.assertEqual(0, (abs(a[0] - b[0]) + abs(a[1] - b[1])) % 64)
                    self.assertEqual(0, self.sides[s]["offsetx"] % 64)

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

    def test_the_pits_hurt_and_are_walked_out_of(self):
        """Acid in the invaders' works and round the portal, molten metal in
        the refinery's channel: both hurt alike (the sector's damage, not the
        flat's), and every pit is one step deep."""
        m = self.m
        hurting = [i for i, s in enumerate(self.sectors) if s.get("damageamount")]
        self.assertEqual(len(m.WORKS_PITS) + len(m.CRATER_PITS) + 1, len(hurting))
        expected = {**{f"z5_acid_{n}": m.ACID for n in range(1, len(m.WORKS_PITS) + 1)},
                    **{f"z8_acid_{n}": m.ACID for n in range(1, len(m.CRATER_PITS) + 1)},
                    "z6_channel": m.MOLTEN}
        self.assertEqual(set(expected), {self.zone_of[i] for i in hurting})
        for i in hurting:
            s = self.sectors[i]
            zone = self.zone_of[i]
            self.assertEqual((m.LAVA_DAMAGE, m.LAVA_DAMAGE_INTERVAL, expected[zone]),
                             (s["damageamount"], s["damageinterval"], s["texturefloor"]), zone)
            walkable = [n for n in self.neighbours[i] if n not in self.unwalkable]
            self.assertTrue(walkable, zone)
            for n in walkable:
                self.assertEqual(m.STEP, self.sectors[n]["heightfloor"] - s["heightfloor"],
                                 f"{zone} -> {self.zone_of[n]}")
        # Nothing else is acid; the vats' tops stay molten (they cannot be walked on).
        acid = {self.zone_of[i] for i, s in enumerate(self.sectors) if s["texturefloor"] == m.ACID}
        self.assertEqual({z for z, f in expected.items() if f == m.ACID}, acid)

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
        self.assertEqual({m.TAG_BLUE_DOOR, m.TAG_S3_PANEL, m.TAG_QUARANTINE}, set(o1 - o0),
                         "V3: the blue key's quarantine room")
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD}, set(h1))
        self.assertTrue(self.named("z4_forest", "z5_works", "z5_key_top") <= r1)
        self.assertFalse(self.named("z6_refinery") & r1)
        self.assertEqual({m.TAG_YELLOW_DOOR, m.TAG_WORKS_LIFT}, set(o2 - o1), "V3: the yellow key's lift")
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
        self.assertGreater(m.CRATER_SKY - m.CRATER_FLOOR, 3 * height)
        x1, y1, x2, y2 = m.CRATER
        self.assertGreaterEqual(min(x2 - x1, y2 - y1), 2048)

    # The Consortium calls its servants from behind it (its design, 4.4): 144
    # behind and 80 to either side, then straight behind, then 120 to its
    # right and left, then in front: (behind, to its right).
    SERVANT_SPOTS = ((144, 80), (144, -80), (144, 0))
    SERVANT_KINDS = ("rifleman", "trooper", "hound", "doughboy")

    def test_the_portal_is_at_the_bosss_back(self):
        """The boss is the Consortium (D116), facing the red gate with the
        portal behind it: its first servant spots fall between it and the
        portal's base, on the crater's floor, with room for each servant."""
        m = self.m
        self.assertEqual("SD_Consortium", m.MONSTER_CLASSES[m.MONSTER_KINDS[m.BOSS_KIND]])
        bx, by = m.MAP09_BOSS_SPOT
        fx = round(math.cos(math.radians(m.BOSS_ANGLE)))
        fy = round(math.sin(math.radians(m.BOSS_ANGLE)))
        px1, py1, px2, py2 = m.PORTAL_BASE
        centre = ((px1 + px2) / 2, (py1 + py2) / 2)
        self.assertLess((centre[0] - bx) * fx + (centre[1] - by) * fy, 0, "the portal is behind it")
        self.assertEqual(m.CRATER_CENTRE[0], bx, "on the portal's axis")
        floor = self.plan["z8_floor"]
        servants = [m.MONSTER_KINDS[k] for k in self.SERVANT_KINDS]
        radius = max(self.body[e][0] for e in servants)
        height = max(self.body[e][1] for e in servants)
        sec = self.sectors[floor]
        self.assertGreaterEqual(sec["heightceiling"] - sec["heightfloor"], height)
        for behind, right in self.SERVANT_SPOTS:
            # forward is (fx, fy), its right (fy, -fx)
            x, y = bx - fx * behind + fy * right, by - fy * behind - fx * right
            self.assertTrue(px1 <= x <= px2, f"servant spot ({x}, {y}) not before the portal")
            under = {self.sector_at(x + dx, y + dy) for dx in (-radius, radius) for dy in (-radius, radius)}
            self.assertEqual({floor}, under, f"servant spot ({x}, {y})")

    def test_the_red_key_springs_the_works_closets(self):
        m = self.m
        red = self.things_of({m.ED_RED_CARD})[0]
        self.assertEqual((SPECIAL_DOOR_OPEN, m.TAG_AMBUSH), (red["special"], red["arg0"]))
        closets = [n for n in self.plan if n.startswith(m.CLOSET_PREFIX) and not n.endswith("_door")]
        self.assertEqual(2, len(closets))
        for name in closets:
            door = self.plan[f"{name}_door"]
            self.assertEqual(m.TAG_AMBUSH, self.sectors[door]["id"])
            # V3: the closet's lamp, a strip of the works, lies before it.
            self.assertTrue(self.named("z5_works", f"z5_closet_{name[-1]}_lamp") & self.neighbours[door], name)
            self.assertTrue([t for t in self.on(2, self.monsters())
                             if self.sector_at(t["x"], t["y"]) == self.plan[name]], f"{name} empty on 2")
            self.assertEqual(3, self.round_of(self.plan[name]))

    # --- secrets ---------------------------------------------------------------
    def test_three_secrets_each_behind_a_push_panel_with_a_way_back(self):
        m = self.m
        special = {self.zone_of[i] for i, s in enumerate(self.sectors) if s.get("special")}
        lamps = {e.lamp for e in m.PICKUP_EVENTS} | {"z5_closet_e_lamp"}   # V3: the events' lamps
        self.assertEqual(set(m.SECRET_ZONES) | lamps, special)
        for i, s in enumerate(self.sectors):
            if s.get("special"):
                want = m.SECTOR_SPECIAL_LIGHT_FLICKER if self.zone_of[i] in lamps else m.SECTOR_SPECIAL_SECRET
                self.assertEqual(want, s["special"], self.zone_of[i])
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
                + [(z, e, x, y) for z, e, x, y, _ in m.ITEMS + m.SECRET_ITEMS + m.AMMO])
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
                                   (m.ED_AKM, "z3_izba_a", 0),
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
        fixed |= {ednum for _z, ednum, *_ in m.AMMO}     # D119: ammunition scales with the monsters
        for kind in {t["type"] for t in self.things} - fixed:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def boss_number(self):
        return self.m.MONSTER_KINDS[self.m.BOSS_KIND]

    def ammo_needed(self, skill):
        """In shells: every monster on the skill, and the boss's servants."""
        return SERVANT_SHELLS + sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]]
                                    for t in self.on(skill, self.monsters()))

    def hit_points_of(self, t):
        """A thing's hit points; the boss's carry its servants'."""
        extra = SERVANT_HIT_POINTS if t["type"] == self.boss_number() else 0
        return self.hit_points.get(t["type"], 0) + extra

    @staticmethod
    def damage_of(t):
        return (SHELLS_GIVEN.get(t["type"], 0) * IZH_AVERAGE + ROUNDS_GIVEN.get(t["type"], 0) * PPSH_AVERAGE
                + AKM_ROUNDS_GIVEN.get(t["type"], 0) * AKM_AVERAGE
                + ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE + CELLS_GIVEN.get(t["type"], 0) * ROKS_AVERAGE)

    def on_route(self, things):
        off = self.named(*self.m.SECRET_ZONES)
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in off]

    def ammo_placed(self, skill, heavy=True):
        placed = self.on_route(self.on(skill, self.things))
        return sum(SHELLS_GIVEN.get(t["type"], 0) + ROUNDS_GIVEN.get(t["type"], 0) / ROUNDS_PER_SHELL
                   + AKM_ROUNDS_GIVEN.get(t["type"], 0) / AKM_ROUNDS_PER_SHELL
                   + heavy * (ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                              + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL)
                   + GRENADES_GIVEN.get(t["type"], 0) * SHELLS_PER_GRENADE for t in placed)

    def test_g3_8_the_ammo_budget(self):
        """D119: on every skill, ammunition on the route is inside that
        skill's G3-8 band of what killing every monster and the boss's
        servants takes (1.5-2.0 / 1.3-1.6 / 1.2-1.45 on skills 2 / 3 / 4). No
        drop and no secret counted. (The test it replaces, the budget without
        the heavy weapons, went with D119's mix: the PG-7V is the map's
        newest round after the forest, and is meant to be fired.)"""
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            low, high = G3_8_BANDS[skill]
            self.assertGreaterEqual(have, low * need, f"skill {skill}: {have} for {need}")
            self.assertLessEqual(have, high * need, f"skill {skill}: {have} for {need}")

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
        there cover at least its shells (the Consortium's 64). (8.4.3's second half, every
        monster but the boss on shells and rounds alone at the skill's floor,
        is not tested: with 8.3's 35 % and 8.4.2's rockets leading it cannot
        hold under the band's ceiling; flagged to the PM.)"""
        m = self.m
        boss_number = self.boss_number()
        boss = SHELLS_TO_KILL[m.MONSTER_CLASSES[boss_number]]
        for skill in SKILLS:
            spot = [t for t in self.on(skill, self.monsters()) if t["type"] == boss_number][0]
            where = self.sector_at(spot["x"], spot["y"])
            stage = next(k for k, r in enumerate(self.rounds) if where in r[1])
            own = self.stage_pools(skill)[stage][3]
            self.assertGreaterEqual(own["rockets"] + own["fuel"], boss, f"skill {skill}: {own}")
    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        start = int(found.group(1))
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = start * PPSH_AVERAGE
            for stage, (_opened, reach, _held) in enumerate(self.rounds):
                here = [t for t in self.on_route(self.on(skill, self.things))
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                hp_so_far += sum(self.hit_points_of(t) for t in here)
                damage += sum(self.damage_of(t) for t in here)
                self.assertGreaterEqual(damage, G3_8_BANDS[skill][0] * hp_so_far, f"skill {skill}, stage {stage}")
                seen = reach

    def arena(self):
        return {i for name, i in self.plan.items() if name.startswith(("z7_", "z8_"))}

    def test_the_crater_alone_pays_for_the_boss(self):
        """D116: the arena's stock (the rim, the red gate's porch, the
        terraces) is at least the Consortium's hit points (4000 since D119)
        and its servants on every skill, a magazine among it, and the boss is
        never left to the shotgun: the rockets and fuel there alone are a
        third of its bill. D119: and no more than the fight there takes - the
        stock inside the skill's G3-8 band of the boss, its servants and the
        crater's own monsters (it was filled for 9000)."""
        m = self.m
        boss = self.hit_points_of({"type": self.boss_number()})
        for skill in SKILLS:
            here = [t for t in self.on(skill, self.things) if self.sector_at(t["x"], t["y"]) in self.arena()]
            total = sum(self.damage_of(t) for t in here)
            heavy = sum(ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE
                        + CELLS_GIVEN.get(t["type"], 0) * ROKS_AVERAGE for t in here)
            self.assertGreaterEqual(total, boss, f"skill {skill}: {total} for {boss}")
            self.assertGreaterEqual(3 * heavy, boss, f"skill {skill}: {heavy} in rockets and fuel")
            self.assertTrue(any(t["type"] == m.ED_AKM_MAG for t in here), f"skill {skill}: no magazine")
            bill = boss + sum(self.hit_points.get(t["type"], 0) for t in here
                              if t["type"] in self.monster_numbers and t["type"] != self.boss_number())
            low, high = G3_8_BANDS[skill]
            self.assertGreaterEqual(total, low * bill, f"skill {skill}: {total} for {bill}")
            self.assertLessEqual(total, high * bill, f"skill {skill}: {total} for {bill}")

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
        the scaling down). The rifle stays beside the PPSh."""
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
        akm = self.things_of({m.ED_AKM})[0]
        ppsh = self.things_of({m.ED_PPSH})[0]
        self.assertEqual(self.sector_at(ppsh["x"], ppsh["y"]), self.sector_at(akm["x"], akm["y"]))

    def test_health_and_armour_on_skill_4(self):
        m = self.m
        found = Counter(t["type"] for t in self.on_route(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 18)
        arena = Counter(t["type"] for t in self.on(4, self.things)
                        if self.sector_at(t["x"], t["y"]) in self.arena())
        self.assertGreaterEqual(arena[m.ED_STIMPACK] + arena[m.ED_MEDIKIT], 8, "a long fight")
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        self.assertEqual(3, self.round_of(self.sector_at(vest["x"], vest["y"])), "before the boss")


if __name__ == "__main__":
    unittest.main()
