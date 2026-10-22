"""MAP05 «Волжская ГЭС» / Volga Dam, v1 (docs/levels/MAP05-volga-dam.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map03_factory.py, whose model of play it repeats:

* structure: every sector closed and clockwise, no duplicate vertex, no step
  up over 16;
* only approved, packed textures (F_SKY1 is the engine's sky marker);
* the Dam set (D107) in place of every stand-in of v1 (design section 7.2):
  the water, the dam's concrete on one grid with its waterline on the water,
  the generators, the control room's boards and consoles, the spillway's
  rack, the masked insulators only as middle textures, SDSIGL1 once;
* everything is reachable and the exit is reached playing the map's own
  doors, switches and its TWO keys (blue and yellow) in order; no trap at
  any stage; the shortcut (SW-B) and the three secrets are never needed;
* the key grammar (D58): each lock seen before its key, each key seen from
  where its place is entered, each key's place in its lock's colour of
  light; the switches real faces, one-shot, each in sight of what it opens;
* the dam's verticality: three levels 384 apart in all, the descent and the
  climb made by stairs only, the parapets impassable, the spillway's water
  a light sting with steps out;
* the population: monsters per skill and nested, both factions where the
  design puts them, every body with room, the closets on their locks; the
  weapons on the route, consumables scaled down, G3-8's ammunition margin
  on every skill and at every stage;
* the three secrets: a push panel each, a clue that is a comparison, a way
  back; the Hand Katyusha in S3.

Run:  python3 -m unittest tests.test_map05_dam -v
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
DOOR_TILE = 128
SIGHT_STEP = 4
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}
KEY_SPRITE_MID = 8
MAX_WADE = 448          # the farthest the water is from a step out: ~2 s, ~10 HP of nukage

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
# G3-8 as MAP01-MAP03 measure it: each kill in IZh shells, heavy weapons
# converted at the ruler's ~62.5 HP a shell (MAP03's test, unchanged).
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


def _load_map05():
    path = PROJECT_ROOT / "src" / "maps" / "MAP05" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP05_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


def _class_facts(name: str) -> dict:
    """RADIUS, HEIGHT, HEALTH and FACTION of a bestiary class, from its file."""
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


class Map05Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map05()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_station"]
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
        cls.props = {i for name, i in cls.plan.items()
                     if name.startswith(cls.m.PROP_PREFIX) or name in cls.m.WINDOWS}
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
        """The sector containing (x, y): the nearest vertical line east of the
        point, and which side of it the point is on."""
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
                    continue          # too high to climb; dropping is free
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
        """{lock number: sector of the key that opens it}."""
        return {self.m.KEY_LOCKS[t["type"]]: self.sector_at(t["x"], t["y"]) for t in self.key_things()}

    def _progression(self):
        """Play the map as a player can (MAP03's model). Manual doors and
        push panels open whenever the player can stand at their line; then,
        one round at a time, every switch and locked door he can now reach
        and work (a locked door only once the sector of ITS key is
        reachable). Returns one (open tags, reachable sectors, locks held)
        per round."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        keys = self.key_sectors()
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = {lock for lock, sector in keys.items() if sector in reach}
            free, gated = set(), set()
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

    def test_the_dam_is_384_high_and_the_map_uses_it(self):
        """Three walking levels (hall, catwalk and control room, crest) and
        the water below: the crest stands 384 over the turbine hall, 448
        over the spillway's channel, and the player walks every level."""
        m = self.m
        self.assertEqual(384, m.CREST - m.GROUND)
        reach = self.rounds[-1][1]
        floors = {self.sectors[i]["heightfloor"] for i in reach}
        for level in (m.CHANNEL, m.GROUND, m.CATWALK, m.CREST):
            self.assertIn(level, floors)
        self.assertEqual(m.CREST, self.sectors[self.start]["heightfloor"], "the train arrives on top")
        self.assertEqual(m.CREST, self.sectors[self.front(self.exit_line())]["heightfloor"],
                         "and the player leaves on top, at the far end of the crest")

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

    def test_the_sky_is_over_the_outdoors_only(self):
        """F_SKY1 on the station, the spillway, the substation, the crest and
        their props; never over a room with a roof or under a door."""
        m = self.m
        sky = {self.zone_of[i] for i, s in enumerate(self.sectors) if s["textureceiling"] == m.SKY}
        outdoors = ("z1_station", "z7_east_walk", "z7_channel", "z7_west_walk", "z9_substation",
                    "z10_crest", "z9_pad", "rails_z1_station", "rails_z10_crest")
        for zone in outdoors:
            self.assertIn(zone, sky)
        for zone in sky:
            self.assertFalse(zone.startswith(("z5_", "z6_", "z4_", "z3_", "z8_", "d", "s", "closet_")), zone)
            self.assertNotIn(self.plan[zone], self.door_sectors)

    def used_textures(self):
        used = set()
        for sd in self.sides:
            used |= {sd.get(k) for k in ("texturetop", "texturemiddle", "texturebottom")}
        for s in self.sectors:
            used |= {s["texturefloor"], s["textureceiling"]}
        return used - {None, "-"}

    def drawn(self, ld, side_key):
        """[(part, height its texture is pegged to)] for the parts of this
        side the engine draws: Doom's pegging, written out again here so
        the map's own helper is not graded by itself."""
        side = self.sides[ld[side_key]]
        s = self.sectors[side["sector"]]
        other_key = "sideback" if side_key == "sidefront" else "sidefront"
        if other_key not in ld:
            return [("texturemiddle", s["heightfloor"] if ld.get("dontpegbottom") else s["heightceiling"])]
        o = self.sectors[self.sides[ld[other_key]]["sector"]]
        parts = []
        if o["heightfloor"] > s["heightfloor"]:
            parts.append(("texturebottom", s["heightceiling"] if ld.get("dontpegbottom") else o["heightfloor"]))
        sky = self.m.SKY
        if o["heightceiling"] < s["heightceiling"] and not (s["textureceiling"] == sky == o["textureceiling"]):
            parts.append(("texturetop", s["heightceiling"] if ld.get("dontpegtop") else o["heightceiling"]))
        return parts

    def faces(self, texture, part=None):
        """Every drawn face wearing `texture`: (linedef, side key, part, pegging height)."""
        out = []
        for ld in self.lines:
            for key in ("sidefront", "sideback"):
                if key not in ld:
                    continue
                for name, ref in self.drawn(ld, key):
                    if self.sides[ld[key]].get(name) == texture and part in (None, name):
                        out.append((ld, key, name, ref))
        return out

    def test_the_dam_set_is_on_the_map(self):
        """Design section 7.2 settled (D107): every lump the design proposed
        is worn, as itself where the art-director drew it, as the nearest
        approved piece where he did not; every piece of the installed Dam
        set is placed (the water's frames 2-4 by ANIMDEFS)."""
        m = self.m
        used = self.used_textures()
        for proposed, worn in m.DAM_SET.items():
            self.assertIn(worn, used, proposed)
            self.assertTrue(_packed(worn), worn)
            if _packed(proposed):
                self.assertEqual(proposed, worn, f"{proposed} was drawn: worn as itself")
            else:
                self.assertNotEqual(proposed, worn, proposed)
        dam = {p.stem for p in ASSETS.glob("textures/dam/*.png")} | {p.stem for p in ASSETS.glob("flats/dam/*.png")}
        self.assertEqual(dam - {"SDWATR2", "SDWATR3", "SDWATR4"}, dam & used)

    def test_what_still_waits_is_not_drawn_yet(self):
        used = self.used_textures()
        for proposed, what in self.m.PENDING_TEXTURES.items():
            self.assertFalse(_packed(proposed), f"{proposed} exists: put it on the map")
            self.assertNotIn(proposed, used)
            self.assertTrue(what)

    def test_no_stand_in_of_v1_is_left(self):
        """The lumps that stood in for the Dam set in v1 are gone where the
        set now stands: SDCONC2 (the hall), SDMFLR1 (the water), SDGRAT1 (the
        catwalk); SDGATE1 is S3's hut only, not the dam's face."""
        used = self.used_textures()
        for lump in ("SDCONC2", "SDMFLR1", "SDGRAT1"):
            self.assertNotIn(lump, used)
        gates = [ld for ld, *_ in self.faces(self.m.ROAD_GATE)]
        self.assertTrue(gates)
        for ld in gates:
            self.assertEqual(self.m.TAG_S3_PANEL, ld.get("arg0"), "SDGATE1 only on S3's panel")

    def test_the_water_is_the_volga(self):
        m = self.m
        for zone in ("z7_channel", "s1_niche", "s1_panel"):
            self.assertEqual(m.WATER, self.sectors[self.plan[zone]]["texturefloor"], zone)
        self.assertEqual("SDWATR1", m.WATER)
        for zone in ("z5_catwalk", "z5_yellow_portal", *(f"z5_stair_{n}" for n in range(1, m.CATWALK_STAIR_STEPS + 1))):
            self.assertEqual(m.GRATING, self.sectors[self.plan[zone]]["texturefloor"], zone)
        self.assertEqual("SDGRAT2", m.GRATING)

    def column(self, ld, key):
        """Where the map's grid puts the first column of this side's texture:
        Doom runs a front side from v1 to v2, a back side from v2 to v1."""
        (ax, ay), (bx, by) = self.line_points(ld)
        if key == "sideback":
            (ax, ay), (bx, by) = (bx, by), (ax, ay)
        if ay == by:
            return ax if bx > ax else -ax
        return ay if by > ay else -ay

    def test_the_dams_concrete_is_one_grid(self):
        """SDDAM1 everywhere is pegged to one grid: its foot on the hall's
        floor and every 128 above and below, whatever floor or ceiling a face
        hangs from, so the lift joints run level round the map; and along
        each wall its columns fall where the map's grid puts them, so a wall
        split by a neighbour's corner shows no seam."""
        m = self.m
        faces = self.faces(m.DAM)
        self.assertGreater(len(faces), 100)
        for ld, key, part, ref in faces:
            where = f"{self.zone_of[self.sides[ld[key]]['sector']]} {part}"
            self.assertEqual((m.GROUND - ref) % m.WALL_TILE, self.sides[ld[key]].get("offsety", 0), where)
            self.assertEqual(self.column(ld, key) % m.LUMP_WIDTH[m.DAM], self.sides[ld[key]].get("offsetx", 0), where)
        for zone in ("z5_hall", "z5_catwalk", "z7_east_walk", "z7_west_walk", "z7_channel", "z10_crest"):
            self.assertIn(m.DAM, self.one_sided_textures(self.plan[zone]), zone)

    def test_the_banks_are_wet_at_the_waterline(self):
        """Every face rising out of the water (onto a walkway or a step)
        wears SDDAM2 with its foot on the water: the tide mark 72 px down the
        tile sits 8 under the walkways' edge. The dam's face over the
        channel is the spillway's rack, standing in the water too."""
        m = self.m
        water = {self.plan["z7_channel"]} | {i for n, i in self.plan.items() if n.startswith("z7_steps_")}
        wet = self.faces(m.DAM_WET)
        self.assertGreaterEqual(len(wet), 4)
        for ld, key, part, ref in wet:
            self.assertEqual("texturebottom", part)
            self.assertIn(self.sides[ld[key]]["sector"], water)
            self.assertEqual((m.CHANNEL - ref) % m.WALL_TILE, self.sides[ld[key]]["offsety"])
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            for key, other in (("sidefront", "sideback"), ("sideback", "sidefront")):
                low, high = self.sides[ld[key]]["sector"], self.sides[ld[other]]["sector"]
                if low == self.plan["z7_channel"] and high in self.named("z7_east_walk", "z7_west_walk"):
                    self.assertEqual(m.DAM_WET, self.sides[ld[key]]["texturebottom"])
                    self.assertEqual(m.WALL_TILE - (m.GROUND - m.CHANNEL), self.sides[ld[key]]["offsety"])
        rack = self.faces(m.SPILLWAY)
        self.assertEqual(1, len(rack))
        ld, key, part, ref = rack[0]
        self.assertEqual(self.plan["z7_channel"], self.sides[ld[key]]["sector"])
        self.assertEqual(m.CHANNEL_RECT[2] - m.CHANNEL_RECT[0], self.length(ld))
        self.assertEqual((m.CHANNEL - ref) % m.WALL_TILE, self.sides[ld[key]]["offsety"])

    def test_the_generators_wear_their_housings(self):
        """SDTURB1 on the four housings, seen from the hall: 48 high, the
        tile's foot (flange and plinth) on the floor; the shafts steel."""
        m = self.m
        housings = self.faces(m.TURBINE, "texturebottom")
        hall = self.plan["z5_hall"]
        generators = self.named(*(f"{m.PROP_PREFIX}z5_generator_{n}" for n in range(1, len(m.GENERATOR_X) + 1)))
        self.assertEqual(4 * len(m.GENERATOR_X), len(housings))
        for ld, key, _part, ref in housings:
            self.assertEqual(hall, self.sides[ld[key]]["sector"])
            self.assertEqual(m.GROUND + m.GENERATOR, ref)
            self.assertEqual(m.WALL_TILE - m.GENERATOR, self.sides[ld[key]]["offsety"])
        for g in generators:
            self.assertEqual({m.STEEL}, set(self.one_sided_textures(g)), self.zone_of[g])

    def test_the_control_room_has_its_boards(self):
        """SDCTRL1 four times on the control room's walls, each a middle
        texture on an impassable line, standing on the floor, whole 64 px
        sections, drawn once under the 160 ceiling; the consoles show its
        desk (rows 64-95)."""
        m = self.m
        control = self.plan["z6_control"]
        boards = [ld for ld in self.lines if "sideback" in ld and m.CONTROL_PANEL in
                  (self.sides[ld["sidefront"]].get("texturemiddle"), self.sides[ld["sideback"]].get("texturemiddle"))]
        self.assertEqual(len(m.CONTROL_BOARDS), len(boards))
        room = self.sectors[control]
        self.assertGreaterEqual(room["heightceiling"] - room["heightfloor"], m.WALL_TILE)
        for ld in boards:
            self.assertTrue(ld.get("blocking") and ld.get("dontpegbottom"))
            self.assertFalse(ld.get("wrapmidtex"))
            self.assertEqual(0, self.length(ld) % 64)
            self.assertGreaterEqual(self.length(ld), m.WALL_TILE)
            sides = [k for k in ("sidefront", "sideback") if self.sides[ld[k]].get("texturemiddle") == m.CONTROL_PANEL]
            self.assertEqual(1, len(sides))
            self.assertEqual(control, self.sides[ld[sides[0]]]["sector"])
            other = self.sectors[self.back(ld) if sides[0] == "sidefront" else self.front(ld)]
            self.assertEqual((room["heightfloor"], room["heightceiling"]),
                             (other["heightfloor"], other["heightceiling"]))
        for name in m.CONTROL_BOARDS:
            self.assertNotIn(self.plan[name], self.rounds[-1][1], f"{name}: nobody walks into a board")
        consoles = self.faces(m.CONTROL_PANEL, "texturebottom")
        self.assertEqual(4 * len(m.CONSOLES), len(consoles))
        for ld, key, _part, ref in consoles:
            self.assertEqual(m.CATWALK + m.CONSOLE, ref)
            self.assertEqual(m.CONTROL_DESK_ROW, self.sides[ld[key]]["offsety"])

    def test_the_insulators_hang_from_the_gantry(self):
        """SDINSL1 is masked: only a middle texture of a two-sided line
        anyone can walk under, here the gantry's two long faces towards the
        substation, two strings each, the strings' foot over every head."""
        m = self.m
        lines = [ld for ld in self.lines if m.INSULATOR in
                 (self.sides[ld["sidefront"]].get("texturemiddle"),
                  self.sides[ld["sideback"]].get("texturemiddle") if "sideback" in ld else None)]
        self.assertEqual(2, len(lines))
        gantry = self.sectors[self.plan["z9_gantry"]]
        self.assertEqual(m.GANTRY, gantry["heightceiling"])
        tallest = max(height for _radius, height in self.body.values())
        self.assertGreater(m.GANTRY - m.WALL_TILE - gantry["heightfloor"], tallest)
        for ld in lines:
            self.assertIn("sideback", ld)
            self.assertFalse(ld.get("blocking") or ld.get("dontpegbottom"))
            self.assertEqual(self.named("z9_gantry", "z9_substation"), set(self._pair(ld)))
            self.assertEqual(2 * 64, self.length(ld))
            for key in ("sidefront", "sideback"):
                side = self.sides[ld[key]]
                worn = side.get("texturemiddle", "-")
                self.assertEqual(m.INSULATOR if side["sector"] == self.plan["z9_substation"] else "-", worn)
        self.assertIn(self.plan["z9_gantry"], self.rounds[-1][1], "walked under")

    def test_middle_textures_are_only_the_boards_and_the_strings(self):
        m = self.m
        for i, sd in enumerate(self.sides):
            for key in ("texturetop", "texturebottom"):
                self.assertNotEqual(m.INSULATOR, sd.get(key), f"sidedef {i}")
        for ld in self.lines:
            if "sideback" in ld:
                for key in ("sidefront", "sideback"):
                    self.assertIn(self.sides[ld[key]].get("texturemiddle", "-"), ("-",) + m.MIDDLE_TEXTURES)
            else:
                self.assertNotIn(self.sides[ld["sidefront"]].get("texturemiddle"), m.MIDDLE_TEXTURES)

    def test_the_signal_is_used_once(self):
        """D107: SDSIGL1 single use, one 64 span, never tiled: the one face
        of the post by the station's track, exactly one tile high."""
        m = self.m
        faces = self.faces(m.SIGNAL)
        self.assertEqual(1, len(faces))
        ld, key, part, ref = faces[0]
        self.assertEqual(64, self.length(ld))
        post = self.sectors[self.plan[f"{m.PROP_PREFIX}z1_signal"]]
        station = self.sectors[self.plan["z1_station"]]
        self.assertEqual("texturebottom", part)
        self.assertEqual(station["heightfloor"] + m.WALL_TILE, post["heightfloor"])
        self.assertEqual(0, self.sides[ld[key]].get("offsety", 0))
        self.assertEqual(self.plan["z1_station"], self.sides[ld[key]]["sector"])

    def test_the_train_is_armoured_with_one_star_per_face(self):
        m = self.m
        stars = self.faces(m.ARMOUR_STAR)
        self.assertEqual(len(m.TRAIN_STARS), len(stars), "one star, on one line")
        train = self.sectors[self.plan[f"{m.PROP_PREFIX}z1_train"]]
        for ld, _key, part, ref in stars:
            self.assertEqual(("texturebottom", train["heightfloor"]), (part, ref))
            self.assertEqual(m.WALL_TILE, self.length(ld))
            self.assertEqual(m.WALL_TILE, train["heightfloor"] - m.CREST, "one panel high, never stacked")
        self.assertTrue(self.faces(m.ARMOUR))

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
                self.assertEqual(DOOR_TILE, self.length(ld), f"linedef {i}")
                drop = self.sectors[room]["heightceiling"] - self.sectors[door]["heightfloor"]
                self.assertEqual(DOOR_TILE, drop, f"linedef {i}: leaf of {self.zone_of[door]}")
        self.assertEqual({self.m.DOOR: 6, self.m.DOOR_YELLOW: 2}, dict(faces),
                         "D1, D2 and the blue gate in SDDOOR1, the yellow door in its trim")

    def test_the_yellow_door_wears_its_trim(self):
        m = self.m
        faces = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE
                 and ld["arg0"] == m.TAG_YELLOW_DOOR]
        self.assertEqual(2, len(faces))
        for ld in faces:
            self.assertEqual(m.DOOR_YELLOW, self.sides[ld["sidefront"]]["texturetop"])

    def test_every_picture_on_a_wall_is_one_whole_tile(self):
        """The flags and the clerestory panes: each on one line exactly as
        wide as the picture, in a recess exactly as high."""
        m = self.m
        widths = {m.FLAG_REICH: 64, m.FLAG_LEGION: 64, m.WINDOW: 64}
        found = Counter()
        for ld in self.lines:
            texture = self.sides[ld["sidefront"]].get("texturemiddle")
            if "sideback" in ld or texture not in widths:
                continue
            found[texture] += 1
            self.assertEqual(widths[texture], self.length(ld), texture)
            s = self.sectors[self.front(ld)]
            self.assertEqual(128, s["heightceiling"] - s["heightfloor"], texture)
        self.assertEqual({m.FLAG_REICH: 1, m.FLAG_LEGION: 1, m.WINDOW: len(m.CLERESTORY)}, dict(found))

    def test_the_flags_hang_side_by_side_by_the_blue_gate(self):
        """D35, both factions on the map: their banners side by side in the
        station's west wall, next to the gate onto the crest."""
        for zone in ("z1_flag_sdflag1", "z1_flag_sdflag2"):
            self.assertIn(self.plan["z1_station"], self.neighbours[self.plan[zone]], zone)
        self.assertIn(self.plan["z1_flag_sdflag1"], self.neighbours[self.plan["z1_flag_sdflag2"]])

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
        self.assertEqual(2, len(colours))

    # --- scope -------------------------------------------------------------
    def test_the_start_and_the_keys_are_on_every_skill(self):
        m = self.m
        for ed in (m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_BLUE_CARD):
            found = self.things_of({ed})
            self.assertEqual(1, len(found), ed)
            for skill in range(1, 6):
                self.assertTrue(found[0][f"skill{skill}"], f"thing {ed} missing on skill {skill}")
            self.assertTrue(found[0]["single"])

    def test_the_only_special_sectors_are_the_secrets_and_the_water(self):
        m = self.m
        special = {self.zone_of[i]: s["special"] for i, s in enumerate(self.sectors) if s.get("special")}
        self.assertEqual({zone: m.SECTOR_SPECIAL_SECRET for zone in m.SECRET_ZONES}, special)
        hurting = {self.zone_of[i] for i, s in enumerate(self.sectors) if s.get("damageamount")}
        self.assertEqual({"z7_channel"}, hurting)

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.rounds[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         sorted(self.zone_of[i] for i in unreachable ^ self.props))

    def test_the_exit_is_reached_and_only_in_the_last_round(self):
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z11_exit_niche"], exit_sector)
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
        """Four rounds: (0) down into the dam, the hall, the spillway and the
        yellow key; (1) the yellow door and the control room; (2) SW-A, the
        cable gallery, the substation and the blue key; (3) the blue gate and
        SW-B, the crest, D2 and the exit."""
        m = self.m
        self.assertEqual(4, len(self.rounds))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3) = self.rounds
        self.assertEqual({m.TAG_D1_GATEHOUSE, m.TAG_S1_PANEL, m.TAG_S2_PANEL}, set(o0))
        self.assertEqual({m.LOCK_YELLOW_CARD}, set(h0), "the yellow key with no switch and no key")
        self.assertTrue(self.named("z5_hall", "z5_catwalk", "z7_west_walk", "z7_winch") <= r0)
        self.assertNotIn(self.plan["z6_control"], r0, "the control room is behind the yellow door")
        self.assertEqual({m.TAG_YELLOW_DOOR}, set(o1 - o0))
        self.assertIn(self.plan["z6_control"], r1)
        self.assertNotIn(self.plan["z9_substation"], r1, "the cable gallery is shut until SW-A")
        self.assertEqual({m.TAG_CABLE_SHUTTER}, set(o2 - o1))
        self.assertTrue(self.named("z8_cable_gallery", "z9_substation", "z9_pad") <= r2)
        self.assertEqual({m.LOCK_YELLOW_CARD, m.LOCK_BLUE_CARD}, set(h2))
        self.assertNotIn(self.plan["z10_crest"], r2, "the crest is behind the blue gate")
        self.assertEqual({m.TAG_BLUE_GATE, m.TAG_STATION_SHUTTER, m.TAG_D2_WEST, m.TAG_S3_PANEL},
                         set(o3 - o2))
        self.assertTrue(self.named("z10_crest", "z11_west_hall") <= r3)

    def test_the_shortcut_is_not_needed(self):
        """SW-B's shutter puts the substation 200 units from the blue gate;
        without it the way back is the long one, through the cable gallery,
        the control room, the hall and the three flights up."""
        m = self.m
        everything_but = self.every_tag - {m.TAG_STATION_SHUTTER}
        self.assertIn(self.front(self.exit_line()), self.reachable(everything_but))

    def test_no_secret_is_needed(self):
        m = self.m
        critical = self.every_tag - {m.TAG_S1_PANEL, m.TAG_S2_PANEL, m.TAG_S3_PANEL}
        self.assertIn(self.front(self.exit_line()), self.reachable(critical))

    def test_the_descent_and_the_climb_are_stairs(self):
        """No lift (MAP01 section 4): the three flights down from the
        gatehouse to the lower gallery and the cable gallery's flight up
        are steps of 16 the player walks both ways."""
        adj = self.adjacency(self.every_tag)
        chains = (["z2_gatehouse"] + [f"z3_flight1_{n}" for n in range(1, 8)] + ["z3_landing_1"]
                  + [f"z3_flight2_{n}" for n in range(1, 8)] + ["z3_landing_2"]
                  + [f"z3_flight3_{n}" for n in range(1, 8)] + ["z4_gallery"],
                  ["z8_cable_gallery"] + [f"z8_cable_stair_{n}" for n in range(1, self.m.CABLE_STAIR_STEPS + 1)]
                  + ["z8_cable_top"],
                  ["z5_hall"] + [f"z5_stair_{n}" for n in range(1, self.m.CATWALK_STAIR_STEPS + 1)]
                  + ["z5_catwalk"])
        for chain in chains:
            floors = [self.sectors[self.plan[z]]["heightfloor"] for z in chain]
            self.assertEqual(abs(floors[-1] - floors[0]), len(chain[1:]) * self.m.STEP, chain[0])
            for a, b in zip(chain, chain[1:]):
                self.assertIn(self.plan[b], adj[self.plan[a]], f"{a} -> {b}")
                self.assertIn(self.plan[a], adj[self.plan[b]], f"{b} -> {a}")

    def test_the_parapets_cannot_be_crossed(self):
        """Every line between a walkable sector and a parapet on the crest's
        side is impassable (`blocking`): no jump, no fall into the spillway
        from 448 up, no walk off the dam."""
        m = self.m
        parapets = self.named(f"{m.PROP_PREFIX}z10_parapet_n", f"{m.PROP_PREFIX}z10_parapet_s",
                              f"{m.PROP_PREFIX}z1_parapet_n")
        walkable_neighbours = 0
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a, b = self._pair(ld)
            for p, other in ((a, b), (b, a)):
                if p not in parapets or other in self.props:
                    continue
                if self.sectors[other]["heightfloor"] == m.CREST:
                    walkable_neighbours += 1
                    self.assertTrue(ld.get("blocking"), f"{self.zone_of[other]} -> {self.zone_of[p]}")
        self.assertGreater(walkable_neighbours, 0)
        rise = self.sectors[self.plan[f"{m.PROP_PREFIX}z10_parapet_s"]]["heightfloor"] - m.CREST
        self.assertGreater(rise, MAX_STEP_UP)

    # --- the keys ------------------------------------------------------------
    def test_one_blue_and_one_yellow_key_on_the_route_outside_any_secret(self):
        m = self.m
        self.assertEqual(sorted([m.ED_BLUE_CARD, m.ED_YELLOW_CARD]), sorted(t["type"] for t in self.key_things()))
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
        self.assertEqual(4, len(locked), "two doors, both faces")
        expected = {m.TAG_YELLOW_DOOR: (m.LOCK_YELLOW_CARD, "yellow_door"),
                    m.TAG_BLUE_GATE: (m.LOCK_BLUE_CARD, "z12_blue_gate")}
        for ld in locked:
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0), tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.back(ld))

    def test_the_blue_gate_is_seen_from_the_start(self):
        """The first thing the player sees down the platform is the lock he
        will leave by: the blue gate onto the crest, lit blue."""
        m = self.m
        sx, sy = m.PLAYER_START
        eye = self.eye(sx, sy, "z1_station")
        for y in (1904, 1936, 1968):
            for z in (400, 448, 496):
                self.assertIsNone(self.blocked(eye, (m.BLUE_GATE[2] + 1, y, z)), f"y {y} z {z}")

    def test_the_yellow_door_is_seen_on_entering_the_hall(self):
        """From the lower gallery's mouth, the yellow door high on the north
        catwalk, over the catwalk's edge: its upper half."""
        m = self.m
        eye = self.eye(m.HALL[2] - 32, 512, "z5_hall")
        for x in (2576, 2624, 2672):
            for z in (272, 304):
                self.assertIsNone(self.blocked(eye, (x, m.YELLOW_DOOR[1] - 1, z)), f"x {x} z {z}")

    def test_the_yellow_key_is_seen_across_the_water(self):
        m = self.m
        target = (*m.YELLOW_KEY_SPOT, self.sectors[self.plan["z7_winch"]]["heightfloor"] + KEY_SPRITE_MID)
        for eye in (self.eye(m.SPILL_GALLERY[0] - 16, 320, "z7_east_walk"),
                    self.eye(m.SPILL_GALLERY[0] + 64, 320, "z7_gallery")):
            self.assertIsNone(self.blocked(eye, target), eye)

    def test_the_blue_key_is_seen_on_entering_the_substation(self):
        m = self.m
        target = (*m.BLUE_KEY_SPOT, self.sectors[self.plan["z9_pad"]]["heightfloor"] + KEY_SPRITE_MID)
        for eye in (self.eye(m.SUBSTATION[0] + 16, 1120, "z9_substation"),
                    self.eye(m.CABLE_TOP[1] - 32, 1120, "z8_cable_top")):
            self.assertIsNone(self.blocked(eye, target), eye)

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        m = self.m
        views = (((m.SPILL_GALLERY[0] - 16, 320), m.YELLOW_KEY_SPOT),
                 ((m.SUBSTATION[0] + 16, 1120), m.BLUE_KEY_SPOT),
                 (m.PLAYER_START, (m.BLUE_GATE[2], 1920)))
        for (x0, y0), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"{t['type']} at ({t['x']}, {t['y']}) on ({x0}, {y0}) -> ({x1}, {y1})")

    def test_each_lock_is_seen_before_its_key(self):
        """Doom's grammar: the blue gate from the start (round 0, before the
        blue key's round 2); the yellow door from the hall, which the route
        crosses before the spillway (the hall is the spillway's only way in)."""
        m = self.m
        self.assertEqual(0, self.first_round_with(self.plan["z1_blue_portal"]))
        self.assertEqual(2, self.first_round_with(self.plan["z9_pad"]))
        without_hall = self.adjacency(set())
        hall = self.plan["z5_hall"]
        cut = {a: {b for b in dsts if b != hall} for a, dsts in without_hall.items() if a != hall}
        self.assertNotIn(self.plan["z7_winch"], self.flood(defaultdict(set, cut), self.start))

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
        self.assertEqual({m.TAG_CABLE_SHUTTER: self.plan["z6_swa_niche"],
                          m.TAG_STATION_SHUTTER: self.plan["z9_swb_niche"]}, found)
        self.assertEqual(self.named("shutter_cable"), self.doors[m.TAG_CABLE_SHUTTER])
        self.assertEqual(self.named("shutter_station"), self.doors[m.TAG_STATION_SHUTTER])

    def test_each_switch_is_in_sight_of_its_shutter(self):
        """A press shows its effect: SW-A beside the cable gallery's shutter,
        SW-B in the passage beside the station's."""
        m = self.m
        for niche, shutter, eye_xy in (("z6_swa_niche", m.CABLE_SHUTTER, (2928, 1248)),
                                       ("z9_swb_niche", m.STATION_SHUTTER, (4208, 1584))):
            room = self.sector_at(*eye_xy)
            eye = (*eye_xy, self.sectors[room]["heightfloor"] + VIEW_HEIGHT)
            x = shutter[0] - 1
            y = (shutter[1] + shutter[3]) / 2
            self.assertIsNone(self.blocked(eye, (x, y, self.sectors[room]["heightfloor"] + 64)), niche)

    def test_the_station_shutter_is_wall_from_the_station(self):
        """The shortcut is found from behind (MAP02's SH, MAP03's shutter):
        from the station it wears the station's brick and has no special."""
        m = self.m
        face = [ld for ld in self.lines if "sideback" in ld
                and set(self._pair(ld)) == self.named("shutter_station", "z1_station")]
        self.assertEqual(1, len(face))
        ld = face[0]
        side = ld["sidefront"] if self.front(ld) == self.plan["z1_station"] else ld["sideback"]
        self.assertEqual(m.BRICK, self.sides[side]["texturetop"])
        self.assertFalse(ld.get("special"))

    def test_the_closets_are_wall_until_they_open(self):
        m = self.m
        for name in (*m.CATWALK_CLOSETS, *m.STATION_CLOSETS):
            door = self.plan[f"{name}_door"]
            faces = [ld for ld in self.lines if "sideback" in ld and door in self._pair(ld)
                     and self.plan[name] not in self._pair(ld)]
            self.assertEqual(1, len(faces), name)
            ld = faces[0]
            side = ld["sidefront"] if self.front(ld) != door else ld["sideback"]
            self.assertNotIn(self.sides[side]["texturetop"], m.DOOR_LEAVES + (m.STEEL,), name)
            self.assertFalse(ld.get("special"), name)

    def test_the_exit_is_seen_from_the_west_door(self):
        niche = self.sectors[self.plan["z11_exit_niche"]]
        for z in (32, 64, 96):
            target = (self.m.EXIT_NICHE[0] + 1, 1920, niche["heightfloor"] + z)
            self.assertIsNone(self.blocked(self.eye(672, 1920, "z10_west_porch"), target, self.every_tag),
                              f"z {z}")

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

    # --- the water -----------------------------------------------------------------
    def test_the_water_stings_lightly(self):
        """The brief: light damage, not abused. Doom's nukage, 5 every 32
        tics; the channel is the only sector that hurts; no sector special."""
        m = self.m
        water = self.sectors[self.plan["z7_channel"]]
        self.assertEqual(m.WATER, water["texturefloor"])
        self.assertEqual((5, 32), (water["damageamount"], water["damageinterval"]))
        self.assertFalse(water.get("special"))

    def test_the_water_is_no_trap(self):
        """64 down from either walkway, three steps of 16 out on both banks at
        two places; no point of the water over MAX_WADE along it from a way out;
        nothing to pick up in it."""
        m = self.m
        channel = self.plan["z7_channel"]
        adj = self.adjacency(self.every_tag)
        for walk in ("z7_east_walk", "z7_west_walk"):
            self.assertIn(channel, adj[self.plan[walk]], f"{walk}: dropping in is free")
            self.assertNotIn(self.plan[walk], adj[channel], f"{walk}: 64 up is not a step")
        for k in range(1, len(m.STEPS_Y) + 1):
            for bank, walk in (("e", "z7_east_walk"), ("w", "z7_west_walk")):
                chain = ["z7_channel"] + [f"z7_steps_{bank}{k}_{n}" for n in (1, 2, 3)] + [walk]
                for a, b in zip(chain, chain[1:]):
                    self.assertIn(self.plan[b], adj[self.plan[a]], f"{a} -> {b}")
        ys = [(y1 + y2) / 2 for y1, y2 in m.STEPS_Y]
        for y in range(m.CHANNEL_RECT[1], m.CHANNEL_RECT[3] + 1, 32):
            self.assertLessEqual(min(abs(y - s) for s in ys), MAX_WADE, f"y {y}")
        self.assertFalse([t for t in self.things if t["type"] not in self.monster_numbers
                          and self.sector_at(t["x"], t["y"]) == channel])
        self.assertIn(self.start, self.flood(adj, channel), "a way back from the water")

    # --- population --------------------------------------------------------------
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
        for ednum in self.m.ROUTE_WEAPONS + (self.m.ED_HAND_KATYUSHA,):
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertEqual(set(self.m.MONSTER_CLASSES), {t["type"] for t in self.monsters()})
        self.assertNotIn(21106, {t["type"] for t in self.things}, "the General is MAP03's")

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
        """Design section 9; more than MAP03's 25 / 38 / 52, the episode's
        second map stepping up without its boss."""
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    # The route's beats, in the order it plays them (design section 6), by
    # the zone prefixes they hold.
    BEATS = (("station", ("z1_", "z2_")), ("galleries", ("z3_", "z4_")), ("hall", ("z5_",)),
             ("spillway", ("z7_",)), ("control", ("z6_", "closet_z5")),
             ("substation", ("z8_", "z9_")), ("crest", ("closet_z1", "z10_", "z11_")))

    def test_the_intensity_rises(self):
        """Ritmo creciente, in hit points met: each third of the route weighs
        more than the one before (the approach; the hall, the spillway and
        the control room; the substation and the crest), on every skill, and
        the crest is the heaviest beat of all, with the waves between."""
        m = self.m
        for skill in SKILLS:
            beat = {name: 0 for name, _ in self.BEATS}
            for zone, kind, _x, _y, _a, tier in m.MONSTERS:
                if tier > skill:
                    continue
                name = next(n for n, prefixes in self.BEATS if zone.startswith(prefixes))
                beat[name] += self.hit_points[m.MONSTER_KINDS[kind]]
            v = [beat[n] for n, _ in self.BEATS]
            thirds = (sum(v[:2]), sum(v[2:5]), sum(v[5:]))
            self.assertLess(thirds[0], thirds[1], f"skill {skill}: {beat}")
            self.assertLess(thirds[1], thirds[2], f"skill {skill}: {beat}")
            self.assertEqual(max(v), beat["crest"], f"skill {skill}: {beat}")

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

    def test_both_factions_hold_the_dam_where_the_design_says(self):
        """The Legion holds the station and the spillway, the Reich the
        machine (galleries, hall, substation); both man the control room and
        the crest. Hybrids stand anywhere; closets are counter-attacks."""
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
                seen[zone.split("_")[0]].add(faction)
        self.assertIn("LEGION", seen["legion"])
        self.assertIn("REICH", seen["reich"])
        for ground in ("z6", "z10"):
            self.assertTrue({"LEGION", "REICH"} <= seen[ground], f"{ground}: {seen[ground]}")

    def test_both_factions_hold_the_crest_on_every_skill(self):
        crest = self.plan["z10_crest"]
        for skill in SKILLS:
            here = [t for t in self.on(skill, self.monsters()) if self.sector_at(t["x"], t["y"]) == crest]
            self.assertTrue({"LEGION", "REICH"} <= {self.faction[t["type"]] for t in here}, skill)

    def test_the_heavies(self):
        """A Panzermensch in the turbine hall, one in the substation and one
        on the crest on every skill; the heavy Panzermensch by the west door from skill 3, and in
        the substation on skill 4; Doughboys where they can fly: the
        spillway and the crest, both under the sky."""
        m = self.m
        pz = self.things_of({m.ED_PANZERMENSCH})
        self.assertEqual({2: 3, 3: 3, 4: 3}, {s: len(self.on(s, pz)) for s in SKILLS})
        every = {self.zone_of[self.sector_at(t["x"], t["y"])] for t in pz if t["skill2"]}
        self.assertEqual({"z5_hall", "z9_substation", "z10_crest"}, every)
        heavy = self.things_of({m.ED_PANZER_HEAVY})
        self.assertEqual({2: 0, 3: 1, 4: 2}, {s: len(self.on(s, heavy)) for s in SKILLS})
        self.assertEqual(self.named("z10_crest", "z9_substation"),
                         {self.sector_at(t["x"], t["y"]) for t in heavy})
        for t in self.things_of({m.ED_DOUGHBOY}):
            self.assertEqual(m.SKY, self.sectors[self.sector_at(t["x"], t["y"])]["textureceiling"])

    def test_every_closet_holds_a_fight_and_opens_with_its_lock(self):
        m = self.m
        for names, tag in ((m.CATWALK_CLOSETS, m.TAG_YELLOW_DOOR), (m.STATION_CLOSETS, m.TAG_BLUE_GATE)):
            for name in names:
                door = self.plan[f"{name}_door"]
                self.assertEqual(tag, self.sectors[door]["id"], name)
                inside = [t for t in self.on(2, self.monsters()) if self.sector_at(t["x"], t["y"]) == self.plan[name]]
                self.assertTrue(inside, f"{name} is empty on skill 2")
                first = next(k for k, (opened, _r, _h) in enumerate(self.rounds) if tag in opened)
                self.assertNotIn(self.plan[name], self.rounds[first - 1][1], f"{name} open early")
                self.assertIn(self.plan[name], self.rounds[first][1], f"{name} never opens")
        self.assertEqual(self.named("yellow_door", "closet_z5_w_door", "closet_z5_e_door"),
                         self.doors[m.TAG_YELLOW_DOOR])
        self.assertEqual(self.named("z12_blue_gate", "closet_z1_s_door", "closet_z1_e_door"),
                         self.doors[m.TAG_BLUE_GATE])

    def test_the_weapons_are_on_every_skill_on_the_route(self):
        """Pistol start: the IZh on the platform and the PPSh in the lower
        gallery before the hall, the RPG-7 at the hall's door, the ROKS-3 in
        the control room; each once, on every skill, never in a secret."""
        m = self.m
        for ednum, zone, stage in ((m.ED_IZH, "z1_station", 0), (m.ED_PPSH, "z4_gallery", 0),
                                   (m.ED_RPG7, "z5_hall", 0), (m.ED_ROKS3, "z6_control", 1)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertFalse(self.sectors[where].get("special"))
            self.assertIn(where, self.rounds[stage][1])
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}))

    def test_the_rpg_is_met_before_the_halls_panzermensch(self):
        m = self.m
        rpg = self.things_of({m.ED_RPG7})[0]
        door = (m.HALL[2], 512)
        for t in self.things_of({m.ED_PANZERMENSCH}):
            if self.sector_at(t["x"], t["y"]) == self.plan["z5_hall"]:
                self.assertLess(math.dist(door, (rpg["x"], rpg["y"])), math.dist(door, (t["x"], t["y"])))

    def test_consumables_scale_down(self):
        m = self.m
        fixed = (self.monster_numbers | set(m.ROUTE_WEAPONS)
                 | {m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_BLUE_CARD})
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
                   + ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                   + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL for t in placed)

    def test_g3_8_the_ammo_budget(self):
        """On every skill, ammunition on the route is at least 1.35 times what
        killing every monster takes, and under three times on skill 4. No
        drop and no secret counted."""
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            self.assertGreaterEqual(have, G3_8_MARGIN * need, f"skill {skill}: {have} for {need}")
        self.assertLess(self.ammo_placed(4), 3 * self.ammo_needed(4))

    def start_rounds(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        """At every round of the route, the damage placed so far plus the
        starting rounds is at least G3-8's margin times the hit points met."""
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = self.start_rounds() * PPSH_AVERAGE
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
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 10)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        self.assertEqual(2, self.first_round_with(self.sector_at(vest["x"], vest["y"])),
                         "the heavy vest before the station's closets and the crest")

    # --- secrets -------------------------------------------------------------------
    def panel_lines(self, tag):
        return [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_OPEN and ld["arg0"] == tag]

    def test_three_secrets_each_a_push_panel_with_a_way_back(self):
        """Each secret: a push panel (Door_Open, both faces, `secret` on the
        automap) that opens for good; entered by its panel only; a way back
        to the start from inside; never needed (test_no_secret_is_needed)."""
        m = self.m
        adj = self.adjacency(self.every_tag)
        for tag, panel, store, stage in ((m.TAG_S1_PANEL, "s1_panel", "s1_store", 0),
                                         (m.TAG_S2_PANEL, "s2_panel", "s2_store", 0),
                                         (m.TAG_S3_PANEL, "s3_panel", "s3_hut", 3)):
            lines = self.panel_lines(tag)
            self.assertEqual(2, len(lines), panel)
            for ld in lines:
                self.assertEqual(self.plan[panel], self.back(ld))
                self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial") and ld.get("secret"), panel)
            self.assertEqual(stage, self.first_round_with(self.plan[store]), store)
            self.assertNotIn(self.plan[store], self.reachable(self.every_tag - {tag}), f"{store} without its panel")
            self.assertIn(self.start, self.flood(adj, self.plan[store]), f"a way back from {store}")
            self.assertTrue(self.sectors[self.plan[store]]["special"] & m.SECTOR_SPECIAL_SECRET)

    def test_the_first_two_clues_are_a_panel_in_shadow(self):
        """MAP01's rule, a comparison and never a sign: S1's outfall and S2's
        panel stand 16 back from their wall, darker than the room; S1's panel
        is the dam's own concrete, like the channel's walls; S2's panel is the
        one stretch of the gallery's wall with no cables on it."""
        m = self.m
        for niche, panel, room, face in (("s1_niche", "s1_panel", "z7_channel", m.DAM),
                                         ("s2_niche", "s2_panel", "z4_gallery", m.CONCRETE)):
            n = self.sectors[self.plan[niche]]
            self.assertLess(n["lightlevel"], self.sectors[self.plan[room]]["lightlevel"], niche)
            self.assertIn(self.plan[room], self.neighbours[self.plan[niche]])
            faces = [ld for ld in self.panel_lines(self.sectors[self.plan[panel]]["id"])
                     if self.front(ld) == self.plan[niche]]
            self.assertEqual(1, len(faces))
            self.assertEqual(face, self.sides[faces[0]["sidefront"]]["texturetop"])
        gallery = self.one_sided_textures(self.plan["z4_gallery"])
        self.assertEqual({m.TUNNEL}, set(gallery), "every other stretch of the gallery has its cables")

    def test_the_third_clue_is_the_hut_that_is_shut(self):
        """Two crane huts alike on the crest: the west one open, the east
        one shut by a corrugated gate, which is S3's panel."""
        m = self.m
        w, e = self.sectors[self.plan["z10_hut_w"]], self.sectors[self.plan["s3_hut"]]
        self.assertEqual((w["heightfloor"], w["heightceiling"]), (e["heightfloor"], e["heightceiling"]))
        self.assertEqual(m.HUT_W[2] - m.HUT_W[0], m.HUT_E[2] - m.HUT_E[0])
        face = [ld for ld in self.panel_lines(m.TAG_S3_PANEL) if self.front(ld) == self.plan["z10_hut_e_porch"]]
        self.assertEqual(1, len(face))
        self.assertEqual(m.ROAD_GATE, self.sides[face[0]["sidefront"]]["texturetop"])
        self.assertEqual(0, self.first_round_with(self.plan["z7_east_walk"]))
        self.assertIn(self.plan["z10_hut_w"], self.rounds[-1][1])

    def test_s3_holds_the_hand_katyusha_for_the_last_fight(self):
        m = self.m
        found = self.things_of({m.ED_HAND_KATYUSHA})
        self.assertEqual(1, len(found))
        t = found[0]
        self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)))
        self.assertEqual(self.plan["s3_hut"], self.sector_at(t["x"], t["y"]))
        self.assertEqual("SD_HandKatyusha", _doomednums().get(m.ED_HAND_KATYUSHA))
        cells = [c for c in self.things_of({m.ED_CELL}) if self.sector_at(c["x"], c["y"]) == self.plan["s3_hut"]]
        self.assertGreaterEqual(len(cells) * 20, 40, "one more volley's fuel beside it")


if __name__ == "__main__":
    unittest.main()
