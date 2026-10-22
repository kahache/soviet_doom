"""MAP06 Red Square, episode 2's last map, v1 (docs/levels/MAP06-red-square.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map03_factory.py. The contract:

* structure: every sector closed and clockwise, no duplicate vertex, no
  step up higher than a stair step;
* only approved, packed textures (and the engine's sky marker F_SKY1); every
  picture on a wall one whole tile; the three locks wear their key's look;
* the Moscow set (D107, v1.1): setts with granite lines on the square, the
  GUM's facade, the tribunes' and the mausoleum's granite, the Spasskaya's
  stone, banners whole on the wall, armour on the parade with the carriers'
  stars whole, and every world-aligned lump laid on the world, so the brick
  runs on from line to line;
* the open air: every outdoor zone has the sky, every closed sky block is a
  wall top (floor = ceiling), the Kremlin wall's swallowtails (SDKREM2, a
  middle texture) stand on its brick against the sky, the tower rises over
  the wall;
* everything is reachable playing the map's own doors, its THREE keys in
  order, the red key's pickup (the closets) and the boss's death (the exit
  gate); no trap at any stage; the exit only after the boss dies, and no
  line can open his gate;
* the key grammar (MAP02's lesson, D58): each lock seen before its key, each
  key seen from where the player comes, in its lock's colour of light, alone
  on its spot, and no monster between;
* three secrets, none needed, each with a way back; the Hand Katyusha in S2;
* the population: per skill and nested, on the bestiary's MAPINFO numbers,
  with room for every body, factions where the design puts them, the boss
  at MAP06_BOSS_SPOT; weapons on the route, consumables scaled down, G3-8's
  ammunition margin on every skill and at every stage, health on skill 4.

Run:  python3 -m unittest tests.test_map06_red_square -v
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


def _load_map06():
    path = PROJECT_ROOT / "src" / "maps" / "MAP06" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP06_test", path)
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


class Map06Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map06()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_hall"]
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
        """D104: the episode's end is the largest map built so far."""
        xs = [v["x"] for v in self.verts]
        ys = [v["y"] for v in self.verts]
        self.assertGreater((max(xs) - min(xs)) * (max(ys) - min(ys)), 3776 * 2144 * 2)

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

    def test_every_door_leaf_and_picture_is_one_whole_tile(self):
        """Each door opens one tile high (its portals are one tile), each
        mosaic, gate and flag is exactly the height of its face."""
        for tag, sectors in self.doors.items():
            for i in sectors:
                s = self.sectors[i]
                lowest = min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                self.assertEqual(self.m.DOOR_HEIGHT, lowest - s["heightfloor"], self.zone_of[i])
        for texture in (self.m.MOSAIC, self.m.GATE, self.m.FLAG_REICH, self.m.FLAG_LEGION, self.m.BANNER):
            faces = 0
            for ld in self.lines:
                sides = [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else [])
                for side in sides:
                    sd = self.sides[side]
                    s = self.sectors[sd["sector"]]
                    if s["heightfloor"] == s["heightceiling"]:
                        continue    # a closed door or panel: its leaf is its neighbours' flank
                    if "sideback" not in ld and sd.get("texturemiddle") == texture:
                        faces += 1
                        self.assertEqual(self.m.TILE_SIZE, s["heightceiling"] - s["heightfloor"],
                                         f"{texture} on {self.zone_of[sd['sector']]}")
                    elif "sideback" in ld and sd.get("texturebottom") == texture:
                        other = self.sectors[self.sides[ld["sideback"] if side == ld["sidefront"]
                                                        else ld["sidefront"]]["sector"]]
                        if other["heightfloor"] > s["heightfloor"]:
                            faces += 1
                            self.assertEqual(self.m.TILE_SIZE, other["heightfloor"] - s["heightfloor"],
                                             f"{texture} flank on {self.zone_of[sd['sector']]}")
            self.assertTrue(faces, texture)

    def test_each_lock_wears_its_keys_look(self):
        """The yellow and red leaves wear their trim; the blue leaf is MAP02's
        door between two cobalt mosaics."""
        m = self.m
        leaf = {m.TAG_BLUE_DOOR: m.DOOR, m.TAG_YELLOW_DOOR: m.DOOR_YELLOW, m.TAG_RED_DOOR: m.DOOR_RED}
        for ld in self.lines:
            if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE:
                self.assertEqual(leaf[ld["arg0"]], self.sides[ld["sidefront"]]["texturetop"])
        band = self.plan["z4_blue_band"]
        mosaics = [ld for ld in self.lines if "sideback" not in ld and self.front(ld) == band
                   and self.sides[ld["sidefront"]].get("texturemiddle") == m.MOSAIC]
        self.assertEqual(2, len(mosaics))

    def sides_of(self, ld):
        """[(sidedef, its sector, the other sector or None, start, end)], each
        side's run the way the engine lays its texture."""
        a, b = self.verts[ld["v1"]], self.verts[ld["v2"]]
        front = self.sides[ld["sidefront"]]
        if "sideback" not in ld:
            return [(front, front["sector"], None, a, b)]
        back = self.sides[ld["sideback"]]
        return [(front, front["sector"], back["sector"], a, b), (back, back["sector"], front["sector"], b, a)]

    def wall_faces(self, x):
        """[(outer sidedef, outer sector, walk sector)] on the wall face at x."""
        walks = self.named("prop_z6_wall_walk", "prop_z9_wall_walk")
        out = []
        for lx, _y1, _y2, ld in self.vertical:
            if lx != x or "sideback" not in ld:
                continue
            for sd, sector, other, _s, _e in self.sides_of(ld):
                if other in walks and sector not in walks:
                    out.append((sd, sector, other, ld))
        return out

    def test_the_kremlin_wall_wears_its_swallowtails_against_the_sky(self):
        """The body is a closed sky block at WALL_WALK; the walk in front of
        it is open to the sky from WALL_WALK to MERLON_TOP, exactly one tile,
        and every line between the walk and the open ground wears SDKREM2 as
        its middle texture on the ground's side, over one tile of SDKREM1
        (or a banner), and is impassable."""
        m = self.m
        self.assertEqual(m.TILE_SIZE, m.MERLON_TOP - m.WALL_WALK)
        for name, floor, ceiling in (("prop_z6_wall", m.WALL_WALK, m.WALL_WALK),
                                     ("prop_z9_wall", m.WALL_WALK, m.WALL_WALK),
                                     ("prop_z6_wall_walk", m.WALL_WALK, m.MERLON_TOP),
                                     ("prop_z9_wall_walk", m.WALL_WALK, m.MERLON_TOP),
                                     ("prop_z6_wall_piers", m.MERLON_TOP, m.MERLON_TOP),
                                     ("prop_z9_wall_piers", m.MERLON_TOP, m.MERLON_TOP)):
            s = self.sectors[self.plan[name]]
            self.assertEqual((floor, ceiling, SKY_FLAT), (s["heightfloor"], s["heightceiling"], s["textureceiling"]),
                             name)
        merlons = 0
        for x in (m.KREMLIN_STRIP_X[1], m.ARENA_STRIP_X[0]):
            faces = self.wall_faces(x)
            self.assertTrue(faces, x)
            for sd, sector, walk, ld in faces:
                where = f"x {x}, {self.zone_of[sector]}"
                self.assertEqual(m.MERLON, sd.get("texturemiddle"), where)
                self.assertTrue(ld.get("blocking"), where)
                floor = self.sectors[sector]["heightfloor"]
                if floor < m.WALL_WALK:
                    self.assertIn(sd.get("texturebottom"), (m.KREMLIN, m.BANNER), where)
                merlons += 1
        worn = sum(1 for sd in self.sides if sd.get("texturemiddle") == m.MERLON)
        self.assertEqual(merlons, worn, "SDKREM2 only on the wall's faces")
        # The square's wall: the walk runs its whole length but for the flags.
        x = m.KREMLIN_STRIP_X[1] - m.WALL_WALK_DEPTH // 2
        flags = [(fy, fy + m.FLAG_WIDTH) for fy, _ in m.FLAGS_ON_THE_WALL]
        for y in range(m.GATE_Y[1] + 16, m.SQUARE[3], 32):
            expected = ("prop_z6_flag" if any(a < y < b for a, b in flags) else "prop_z6_wall_walk")
            self.assertTrue(self.zone_of[self.sector_at(x, y)].startswith(expected), y)

    def test_the_wall_walk_is_out_of_reach(self):
        """The stands' top rows are as high as the walk: only the impassable
        merlon line keeps the player (and a floating Doughboy) off it."""
        m = self.m
        walk = self.plan["prop_z6_wall_walk"]
        for side in ("n", "s"):
            top = self.plan[f"z6_tribune_{side}_top"]
            self.assertEqual(m.WALL_WALK, self.sectors[top]["heightfloor"])
            self.assertIn(walk, self.neighbours[top])
            self.assertNotIn(walk, self.adjacency(frozenset())[top])

    def visible_parts(self, sd, sector, other, ld=None):
        """{part: (texture, anchor)}: each drawn part with Doom's row anchor
        before offsets (the height of the texture's row 0), for an unflagged
        two-sided line or a wall (pegged to its floor when flagged so)."""
        s = self.sectors[sector]
        if other is None:
            pegged = ld is None or ld.get("dontpegbottom")
            return {"mid": (sd.get("texturemiddle"),
                            s["heightfloor"] + self.m.ALIGN_PERIOD if pegged else s["heightceiling"])}
        o = self.sectors[other]
        parts = {}
        if o["heightfloor"] > s["heightfloor"]:
            parts["bottom"] = (sd.get("texturebottom"), o["heightfloor"])
        both_sky = s["textureceiling"] == o["textureceiling"] == SKY_FLAT
        if o["heightceiling"] < s["heightceiling"] and not both_sky:
            parts["top"] = (sd.get("texturetop"), o["heightceiling"] + self.m.ALIGN_PERIOD)
        if sd.get("texturemiddle") not in (None, "-"):
            parts["mid"] = (sd["texturemiddle"], min(s["heightceiling"], o["heightceiling"]))
        return parts

    def test_the_moscow_lumps_are_laid_on_the_world(self):
        """Every drawn part wearing an ALIGNED lump has its row 0 at the
        lump's height (mod one tile) and its column 0 on the world's grid,
        so the brick, the merlons, the bays and the frieze run on unbroken."""
        m = self.m
        checked = Counter()
        for ld in self.lines:
            if ld.get("dontpegtop") or (ld.get("dontpegbottom") and "sideback" in ld):
                continue    # no aligned lump sits on a flagged two-sided line
            for sd, sector, other, start, end in self.sides_of(ld):
                for part, (texture, anchor) in self.visible_parts(sd, sector, other, ld).items():
                    if texture not in m.ALIGNED:
                        continue
                    offset = sd.get(f"offsety_{part}", 0) + sd.get("offsety", 0)
                    self.assertEqual(m.ALIGNED[texture] % m.ALIGN_PERIOD, (anchor + offset) % m.ALIGN_PERIOD,
                                     f"{texture} {part} on {self.zone_of[sector]}")
                    dx = (end["x"] > start["x"]) - (end["x"] < start["x"])
                    dy = (end["y"] > start["y"]) - (end["y"] < start["y"])
                    self.assertEqual((start["x"] * dx + start["y"] * dy) % m.ALIGN_PERIOD,
                                     sd.get("offsetx", 0) % m.ALIGN_PERIOD, f"{texture} on {self.zone_of[sector]}")
                    checked[texture] += 1
        self.assertEqual(set(m.ALIGNED), set(checked), "every aligned lump is on the map")

    def test_the_banners_hang_whole_on_the_wall(self):
        m = self.m
        hung = []
        for sd, sector, walk, ld in self.wall_faces(m.KREMLIN_STRIP_X[1]):
            if sd.get("texturebottom") != m.BANNER:
                continue
            a, b = self.line_points(ld)
            y1, y2 = sorted((a[1], b[1]))
            hung.append(y1)
            self.assertEqual(m.BANNER_WIDTH, y2 - y1)
            self.assertEqual(0, y1 % m.BANNER_WIDTH, "its column 0 on the line's start")
            self.assertEqual(m.TILE_SIZE, self.sectors[walk]["heightfloor"] - self.sectors[sector]["heightfloor"])
            for fy, _ in m.FLAGS_ON_THE_WALL:
                self.assertFalse(fy < y2 and y1 < fy + m.FLAG_WIDTH, "a Soviet banner under an occupier's flag")
        self.assertEqual(sorted(m.BANNERS_Y), sorted(hung))

    def test_the_square_is_setts_crossed_by_granite_lines(self):
        m = self.m
        square = self.sectors[self.plan["z6_square"]]
        self.assertEqual(m.COBBLES, square["texturefloor"])
        self.assertEqual(m.COBBLES, self.sectors[self.plan["z9_arena"]]["texturefloor"])
        for n, y in enumerate(m.SQUARE_LINES_Y, start=1):
            line = self.sectors[self.plan[f"z6_line_{n}"]]
            self.assertEqual(m.COBBLES_LINE, line["texturefloor"])
            for key in ("heightfloor", "heightceiling", "textureceiling", "lightlevel"):
                self.assertEqual(square[key], line[key], key)
            self.assertEqual((0, 64), (y % 64, m.SQUARE_LINE_DEPTH), "one line of slabs, on the flat grid")

    def test_the_monuments_wear_their_stone(self):
        """The GUM's facade on the square and on Nikolskaya; the stands and
        the mausoleum in the tribune's granite; the Spasskaya's base."""
        m = self.m
        sq_x1, sq_y1, sq_x2, sq_y2 = m.SQUARE
        square_side = self.named("z6_square", "z6_line_1", "z6_line_2", "z6_line_3")
        facade = 0
        for lx, y1, y2, ld in self.vertical:
            if lx != sq_x2:
                continue
            for sd, sector, other, _s, _e in self.sides_of(ld):
                if sector in square_side:
                    for part, (texture, _a) in self.visible_parts(sd, sector, other).items():
                        if part != "mid":
                            self.assertEqual(m.GUM_FACADE, texture, (y1, y2, part))
                            facade += 1
                        elif other is None:
                            self.assertEqual(m.GUM_FACADE, texture, (y1, y2))
                            facade += 1
        self.assertGreater(facade, 10)
        street = [sd for ld in self.lines for sd, sector, other, s, e in self.sides_of(ld)
                  if sector == self.plan["z3_street"] and s["y"] == e["y"] == m.STREET[1]
                  and m.GUM_NORTH[0] <= min(s["x"], e["x"]) and max(s["x"], e["x"]) <= m.GUM_NORTH[2]]
        self.assertTrue(street)
        for sd in street:
            self.assertIn(m.GUM_FACADE, (sd.get("texturemiddle"), sd.get("texturetop")))
        stone = {m.TRIBUNE: [n for n in self.plan if n.startswith(("z6_tribune_", "prop_z6_mausoleum"))],
                 m.SPASSKAYA: ["prop_z6_tower"]}
        for texture, names in stone.items():
            for name in names:
                index = self.plan[name]
                flanks = [sd for ld in self.lines for sd, sector, other, _s, _e in self.sides_of(ld)
                          if other == index and self.sectors[sector]["heightfloor"] < self.sectors[index]["heightfloor"]
                          and sector not in self.named("prop_z6_wall", "prop_z6_wall_walk")]
                self.assertTrue(flanks, name)
                for sd in flanks:
                    self.assertEqual(texture, sd["texturebottom"], name)

    def test_the_parade_wears_armour_and_the_carriers_their_stars_whole(self):
        m = self.m
        carriers = {}
        for name, hull, deck, _top, _h in m.VEHICLES:
            family = "z7" if name.startswith("p") else "z6"
            if deck == m.CARRIER_HULL:
                carriers[self.plan[f"prop_{family}_vehicle_{name}"]] = hull
        vehicles = {i for n, i in self.plan.items() if "_vehicle_" in n}
        stars = 0
        for ld in self.lines:
            for sd, sector, other, start, end in self.sides_of(ld):
                if other not in vehicles or self.sectors[sector]["heightfloor"] >= self.sectors[other]["heightfloor"]:
                    continue
                self.assertIn(sd["texturebottom"], (m.ARMOUR, m.ARMOUR_STAR), self.zone_of[other])
                if sd["texturebottom"] != m.ARMOUR_STAR:
                    continue
                stars += 1
                self.assertIn(other, carriers)
                x1, y1, x2, y2 = carriers[other]
                self.assertTrue(start["x"] == end["x"] in (x1, x2), "on a long flank")
                height = self.sectors[other]["heightfloor"] - self.sectors[sector]["heightfloor"]
                first = sd["offsety_bottom"]
                self.assertTrue(first <= m.STAR_ROWS[0] and m.STAR_ROWS[1] < first + height, "the star whole")
                dy = (end["y"] > start["y"]) - (end["y"] < start["y"])
                self.assertEqual((start["y"] * dy - min(y1 * dy, y2 * dy)) % m.ALIGN_PERIOD, sd["offsetx"])
                self.assertEqual(0, (y2 - y1) % m.ALIGN_PERIOD, "a whole number of stars")
        self.assertGreaterEqual(stars, 2 * len(carriers))

    def test_the_tower_rises_over_the_wall_and_the_apron_shows_it(self):
        m = self.m
        tops = [self.sectors[self.plan[n]]["heightfloor"]
                for n in ("prop_z6_tower", "prop_z6_tower_mid", "prop_z6_tower_top")]
        self.assertEqual([m.TOWER_BASE, m.TOWER_STAGE, m.TOWER_SPIRE], tops)
        self.assertGreater(tops[0], m.MERLON_TOP)
        apron = self.sectors[self.plan["z6_tower_apron"]]
        self.assertGreaterEqual(apron["heightceiling"], m.TOWER_SPIRE)
        self.assertIn(self.plan["z6_tower_apron"], self.neighbours[self.plan["prop_z6_tower"]])

    def test_the_flags_hang_side_by_side_on_the_wall_and_in_the_courtyard(self):
        m = self.m
        for texture in (m.FLAG_REICH, m.FLAG_LEGION):
            zones = {self.zone_of[self.sides[side]["sector"]][:5] for ld in self.lines
                     for side in [ld["sidefront"]] + ([ld["sideback"]] if "sideback" in ld else [])
                     if texture in (self.sides[side].get("texturemiddle"), self.sides[side].get("texturebottom"))}
            self.assertTrue({"prop_", "z9_fl"} <= zones, f"{texture}: {zones}")

    # --- the open air ----------------------------------------------------------
    def test_the_outdoors_has_the_sky_and_every_sky_block_is_a_wall_top(self):
        for name in ("z3_street", "z5_passage_s", "z5_atrium", "z6_square", "z7_park", "z9_arena", "s3_yard"):
            self.assertEqual(SKY_FLAT, self.sectors[self.plan[name]]["textureceiling"], name)
        for i, s in enumerate(self.sectors):
            if s["textureceiling"] == SKY_FLAT and s["heightceiling"] == s["heightfloor"]:
                self.assertIn(i, self.props, self.zone_of[i])
                self.assertFalse(s.get("id"), self.zone_of[i])

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
        """Five rounds: the station, the street and the GUM (the blue key);
        the blue door (the square, the yellow key); the yellow gatehouse (the
        vehicle park, the red key); the Spasskaya gate with the closets the
        red key sprang; the boss's death and his gate."""
        m = self.m
        r = self.rounds
        self.assertEqual(5, len(r))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3), (o4, r4, h4) = r
        self.assertEqual(set(m.SECRET_PANEL_TAGS), set(o0), "the push panels open whether found or not")
        self.assertEqual({m.LOCK_BLUE_CARD}, set(h0))
        self.assertFalse(self.named("z6_square") & r0, "the square is behind the blue door")
        self.assertEqual({m.TAG_BLUE_DOOR}, set(o1 - o0))
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD}, set(h1))
        self.assertFalse(self.named("z7_park") & r1)
        self.assertEqual({m.TAG_YELLOW_DOOR}, set(o2 - o1))
        self.assertEqual({m.LOCK_BLUE_CARD, m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD}, set(h2))
        self.assertFalse(self.named("z9_arena", "closet_z6_w", "closet_z6_e") & r2)
        self.assertEqual({m.TAG_RED_DOOR, m.TAG_AMBUSH}, set(o3 - o2))
        self.assertTrue(self.named("z9_arena", "closet_z6_w", "closet_z6_e") <= r3)
        self.assertFalse(self.named(*m.EXIT_ZONES) & r3, "the exit is behind the boss's gate")
        self.assertEqual({m.TAG_BOSS_EXIT}, set(o4 - o3))
        self.assertTrue(self.named(*m.EXIT_ZONES) <= r4)

    def test_the_exit_is_reached_only_after_the_boss_dies(self):
        m = self.m
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z10_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        alive = self.progression_of(kills=False)
        self.assertNotIn(exit_sector, alive[-1][1], "the exit without killing the boss")
        self.assertIn(exit_sector, self.rounds[-1][1])
        niche = self.sectors[exit_sector]
        self.assertEqual(m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])

    def test_no_line_opens_the_bosss_gate_or_the_closets(self):
        """Only things carry TAG_BOSS_EXIT and TAG_AMBUSH: pressing the gate
        does nothing, and nothing but the red key opens the closets."""
        m = self.m
        for ld in self.lines:
            if ld.get("special"):
                self.assertNotIn(ld.get("arg0"), (m.TAG_BOSS_EXIT, m.TAG_AMBUSH), ld)
        gate = self.plan["z10_gate"]
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
        self.assertIn(self.plan["z10_exit_niche"], self.reachable(critical))

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
                    m.TAG_YELLOW_DOOR: (m.LOCK_YELLOW_CARD, "z7_yellow_door"),
                    m.TAG_RED_DOOR: (m.LOCK_RED_CARD, "z8_red_door")}
        for ld in locked:
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0), tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.sides[ld["sideback"]]["sector"])

    def test_the_blue_door_is_seen_from_the_gums_north_hall(self):
        eye = self.eye(3648, 3456, "z4_north")
        for y in (2336, 2368, 2400):
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (3521, y, z)), f"y {y} z {z}")

    def test_the_blue_key_is_seen_on_the_bridge_from_below(self):
        target = self.key_target(self.m.BLUE_KEY_SPOT, "z5_bridge_key")
        for point, zone in (((4096, 3552), "z4_north"), ((4096, 3300), "z5_passage_n")):
            self.assertIsNone(self.blocked(self.eye(*point, zone), target), point)

    def test_the_square_shows_its_locks_and_the_yellow_key_from_the_blue_door(self):
        """Stepping out of the GUM: the red gate, the yellow gatehouse and the
        yellow key on the stand, all at once, across the parade."""
        m = self.m
        eye = self.eye(3424, 2368, "z6_square")
        for y in (1504, 1536, 1568):
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (1601, y, z)), f"red gate y {y} z {z}")
        for x in (2720, 2752, 2784):
            for z in (32, 64, 96):
                self.assertIsNone(self.blocked(eye, (x, 1121, z)), f"yellow gate x {x} z {z}")
        self.assertIsNone(self.blocked(eye, self.key_target(m.YELLOW_KEY_SPOT, "z6_tribune_n_top")))

    def test_the_red_key_is_seen_through_the_yellow_gatehouse(self):
        target = self.key_target(self.m.RED_KEY_SPOT, "z7_pedestal")
        self.assertIsNone(self.blocked(self.eye(2752, 1056, "z7_porch"), target))

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        m = self.m
        views = ((self.eye(4096, 3552, "z4_north"), m.BLUE_KEY_SPOT),
                 (self.eye(3424, 2368, "z6_square"), m.YELLOW_KEY_SPOT),
                 (self.eye(2752, 1056, "z7_porch"), m.RED_KEY_SPOT))
        for (x0, y0, _z), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"monster {t['type']} at ({t['x']}, {t['y']}) "
                                             f"on the view to {(x1, y1)}")

    def test_the_exit_is_seen_from_the_bosss_gate(self):
        eye = self.eye(480, 1536, "z9_exit_porch")
        self.assertIsNone(self.blocked(eye, (177, 1536, 64), {self.m.TAG_BOSS_EXIT}))

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
        self.assertEqual(m.MAP06_BOSS_SPOT, (b["x"], b["y"]))
        self.assertTrue(all(b[f"skill{n}"] for n in range(1, 6)))
        special, args = m.BOSS_DEATH_SPECIAL
        self.assertEqual((SPECIAL_DOOR_OPEN, m.TAG_BOSS_EXIT), (special, args[0]))
        self.assertEqual((special,) + args[:2], (b["special"], b["arg0"], b["arg1"]))
        self.assertEqual("z9_dais_2", self.zone_of[self.sector_at(b["x"], b["y"])])
        self.assertEqual(max(self.hit_points.values()), self.hit_points[ed], "the strongest thing here")
        self.assertEqual([(m.TAG_BOSS_EXIT, self.sector_at(b["x"], b["y"]))],
                         self.thing_specials(self.monster_numbers), "one death special, his")

    def test_the_courtyard_is_his_size(self):
        """He never has to pass a door to fight: the courtyard's sky is far
        over him and its floor round the dais is open."""
        m = self.m
        height = self.body[m.MONSTER_KINDS[m.BOSS_KIND]][1]
        self.assertGreater(m.ARENA_SKY, 4 * height)

    def test_the_red_key_springs_the_museums_closets(self):
        m = self.m
        red = self.things_of({m.ED_RED_CARD})[0]
        self.assertEqual((SPECIAL_DOOR_OPEN, m.TAG_AMBUSH), (red["special"], red["arg0"]))
        closets = [n for n in self.plan if n.startswith(m.CLOSET_PREFIX) and not n.endswith("_door")]
        self.assertEqual(2, len(closets))
        for name in closets:
            door = self.plan[f"{name}_door"]
            self.assertEqual(m.TAG_AMBUSH, self.sectors[door]["id"])
            self.assertIn(self.plan["z6_square"], self.neighbours[door])
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
        for name in m.SECRET_ZONES:
            self.assertEqual(0, self.round_of(self.plan[name]), f"{name} needs a key")

    def test_s2_holds_the_hand_katyusha_and_nothing_else_does(self):
        m = self.m
        found = self.things_of({m.ED_HAND_KATYUSHA})
        self.assertEqual(1, len(found))
        self.assertEqual(self.plan["s2_store"], self.sector_at(found[0]["x"], found[0]["y"]))
        self.assertTrue(all(found[0][f"skill{n}"] for n in range(1, 6)))

    def test_each_clue_is_a_comparison_in_shadow(self):
        """MAP01's rule: a clue is a comparison, never a sign. S1 and S3 are
        the odd one of a row, set back and darker; S2 is the one upper shop
        whose back wall is crates."""
        m = self.m
        for niche in ("s1_niche", "s3_niche"):
            self.assertEqual(m.LIGHT_CLUE, self.sectors[self.plan[niche]]["lightlevel"])
        backs = Counter()
        for ld in self.lines:
            if "sideback" in ld:
                continue
            zone = self.zone_of[self.front(ld)]
            if zone.startswith("z5_shop_u") and not zone.endswith("_door"):
                (x1, _), (x2, _) = self.line_points(ld)
                if x1 == x2 == 4608:
                    backs[(zone, self.sides[ld["sidefront"]]["texturemiddle"])] += 1
        self.assertEqual({"z5_shop_u1": m.TILE, "z5_shop_u2": m.CRATE, "z5_shop_u3": m.TILE},
                         {z: t for z, t in backs})

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
                         "every class of the bestiary fights at the episode's end")

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

    def test_nothing_stands_on_the_mausoleum(self):
        """D12: the mausoleum is architecture; nothing fights or lies on it."""
        tomb = {self.plan[n] for n in self.plan if n.startswith("prop_z6_mausoleum")}
        self.assertEqual(3, len(tomb))
        for t in self.things:
            self.assertNotIn(self.sector_at(t["x"], t["y"]), tomb, t)

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
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)
        self.assertGreater(counts[4], 52, "harder than Tankograd (52 on skill 4)")

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
        courtyard = self.named("z9_arena", "z9_dais_2")
        for skill in (3, 4):
            here = {self.faction[t["type"]] for t in self.on(skill, self.monsters())
                    if self.sector_at(t["x"], t["y"]) in courtyard}
            self.assertTrue({"LEGION", "REICH"} <= here, f"skill {skill}: {here}")

    def test_the_weapons_are_on_every_skill_on_the_route_in_order(self):
        m = self.m
        for ednum, zone, stage in ((m.ED_IZH, "z1_hall", 0), (m.ED_PPSH, "z4_north", 0),
                                   (m.ED_RPG7, "z5_gallery_n", 0), (m.ED_ROKS3, "z6_tribune_s_top", 1)):
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
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 12)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        self.assertEqual(3, self.round_of(self.sector_at(vest["x"], vest["y"])), "before the boss")


if __name__ == "__main__":
    unittest.main()
