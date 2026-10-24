"""MAP03 Tankograd, the tractor factory, v0 and v1 (docs/levels/MAP03-factory.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map02_metro.py. v0's contract (design section 14):

* structure: every sector closed and clockwise, no duplicate vertex;
* only approved, packed textures;
* everything is reachable, and the exit is reached, playing the map's own
  doors, switches and its TWO keys in order (the progression model, here
  with one lock number per key);
* no trap: from every place the player can reach at any stage there is a way
  back to the start, and at the end a way on to the exit;
* the key grammar and MAP02's lesson (D58, the pass nobody found): each
  locked door is seen before its key, each key is seen from where its room
  is entered, and each key's place wears its lock's colour of light;
* the switches are real switch faces, one-shot, each in sight of what it
  opens; doors one tile high.

v1 (design section 15):

* the Tankograd set (D66) placed where the design asked for it, each piece
  one whole tile where it is a picture (gates, flags, glazing, leaves), the
  key-trimmed leaves on their own locks, and the red lock no longer framed
  by red star plaques (the art-director's note);
* the population of section 9 on the bestiary's own MAPINFO numbers, the
  General among them: monsters per skill and nested, both factions where
  D35 puts them, every body with room to stand, SW-A's closets in the hall;
* the weapons on the route, consumables scaled down, G3-8's ammunition
  margin on every skill and at every stage, health on skill 4; since D119
  the ammunition scales up instead, fewer pickups of it, every skill inside
  its G3-8 band, shells no more than 35 % of the damage placed, and every
  weapon stretch paid for;
* the keys' sight lines still hold with the hall dressed (banner, chains,
  clerestory).

v1.1 (design section 16, D68):

* S1 holds the Hand Katyusha: a sector counted as secret, reached by a push
  panel in a row of lockers (the one set back in shadow), with a way back,
  and never needed for the exit;
* the molten channel hurts (UDMF `damageamount` / `damageinterval`), and it
  is no trap: a step out on every side, nothing in it;
* the General's death opens his stores: his thing carries Door_Open on a tag
  no line carries; the stores are reached only after his death (the model
  plays the kill once his sector is reachable), and the exit never needs it.

Run:  python3 -m unittest tests.test_map03_factory -v
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
import _pickup_events as pe  # noqa: E402  (V3 A2's shared checks)
import test_udmf as udmf_tests  # noqa: E402

parse_textmap = udmf_tests.parse_textmap
MAX_STEP_UP = udmf_tests.MAX_STEP_UP       # 24
PLAYER_HEIGHT = udmf_tests.PLAYER_HEIGHT   # 56
VIEW_HEIGHT = udmf_tests.VIEW_HEIGHT       # 41

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4    # ZDoom raises a door to lowest neighbour ceiling - 4
DOOR_TILE = 128                 # SDDOOR1 and its key-trimmed twins are 128x128
SIGHT_STEP = 4                  # sample spacing of a sight line, map units
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys
KEY_SPRITE_MID = 8              # a keycard stands about 16 high: aim at its middle

ASSETS = PROJECT_ROOT / "assets"
MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
MONSTER_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters"
PLAYER_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "player.zs"

SKILLS = (2, 3, 4)
DOOM_MONSTERS = {3004, 9, 3001, 3002, 3005, 69, 3003, 16, 7, 65, 64, 66, 67, 68, 71, 84, 58, 3006}
# The class file of each bestiary class: RADIUS, HEIGHT, HEALTH and the
# faction are read from it (BESTIARY: "the code is the truth"). The heavy
# Panzermensch derives from the Panzermensch and changes only its health,
# so its body and faction are its parent's.
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
# Criterion G3-8 as MAP01 and MAP02 measure it: what each kill costs in IZh
# shells. MAP01's ruler (8 shells for 500 HP, about 62.5 HP a shell),
# extended by hit points to the two heavies this map introduces.
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8,
                  "SD_PanzermenschSchwer": 16, "SD_General": 48}
# D119 (docs/engine/BALANCE.md): a G3-8 band per skill instead of one floor,
# shells no more than SHELL_SHARE_MAX of the damage placed, and fewer
# ammunition pickups on the route than v1 placed.
G3_8_BAND = {2: (1.5, 2.0), 3: (1.3, 1.6), 4: (1.2, 1.45)}
SHELL_SHARE_MAX = 0.35
NEWEST_SHARE_MIN = 0.4    # BALANCE 8.4
ROCKET_SHARE_MAX = 0.3    # BALANCE 8.4, the PM's amendment: outside a boss's stage
FUEL_SHARE_MAX = 0.15     # ...and fuel at most 15 % of the map's ammunition
# D119's shell share (BALANCE 8.3): (placed shells + what the Legion's
# dropped IZhs carry) over (placed shell-equivalents + every drop), drops in
# shell-equivalents: a trooper's IZh 2 shells, a rifleman's clip 5 rounds.
DROP_SHELLS = 2
DROP_ROUNDS = 5
V1_AMMO_PICKUPS = {2: 36, 3: 33, 4: 28}
SHELLS_GIVEN = {2008: 4, 2049: 20, 21003: 8}
ROUNDS_GIVEN = {2007: 10, 2048: 50, 21004: 35}
ROCKETS_GIVEN = {2010: 1, 2046: 5, 21005: 2}
CELLS_GIVEN = {2047: 20, 17: 100, 21006: 40}
# The factory is the first map with the RPG-7's rounds and the ROKS-3's fuel
# to spend on heavies, so both count (BALANCE 8.1): a PG-7V direct hit
# averages 135 (BALANCE 2; the General takes no blast), counted as 2 shells;
# a unit of fuel is 13.5 / 80 of a shell since D119 cut the ROKS-3's jet.
ROUNDS_PER_SHELL = 10
SHELLS_PER_ROCKET = 2
SHELLS_PER_CELL = 13.5 / 80   # D119 (BALANCE 8.1): the ROKS-3's jet is 13.5 now
# V3 A4, the RGD-5 (BALANCE 8.1, 8.6; placed in Episode 1 on 2026-10-24): a
# grenade counts 1.25 shell-equivalents (its 100 blast at the centre over the
# IZh's 80), the pouch (the weapon) 2, a loose one 1, the crate 4. Counted in
# the band (8.2) and in the shell share's whole (8.3) only: the stage
# readiness, the newest weapon's lead (8.4.2) and the boss's stage (8.4.3)
# leave grenades out (the bosses take no splash).
GRENADES_GIVEN = {21009: 2, 21021: 1, 21022: 4}
SHELLS_PER_GRENADE = 1.25
IZH_AVERAGE = 80       # docs/engine/BALANCE.md 2: one barrel
PPSH_AVERAGE = 8       # one round
RPG_AVERAGE = 135      # one PG-7V, direct hit only
ROKS_AVERAGE = 13.5    # one jet, one unit of fuel (D119; was 18)
# D119's stretches along the weapons, by the zones of the tables (design
# section 5): the IZh from the dock, the PPSh-41 upstairs, the RPG-7 on the
# tank line, the ROKS-3 in the foundry, and the General's hall.
MAP03_STRETCHES = (
    ("the IZh", {"z1_spur", "z2_dock", "z2_arch", "z3_hall"}),
    ("the PPSh-41", {"o_corridor", "o_director", "o_planning", "o_archive",
                     "closet_hs", "closet_hn", "closet_ow", "closet_oe"}),
    ("the RPG-7", {"t_vestibule", "t_line"}),
    ("the ROKS-3", {"f_gallery", "f_floor", "f_platform", "f_lift"}),
    ("the General", {"p_ante", "p_booth", "p_hall", "p_dais_1", "p_dais_2"}),
)


def _load_map03():
    path = PROJECT_ROOT / "src" / "maps" / "MAP03" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP03_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


def _class_facts(name: str) -> dict:
    """RADIUS, HEIGHT, HEALTH and FACTION of a bestiary class, from its file,
    falling back to its parent's file for what it does not redefine."""
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


class Map03Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map03()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_spur"]
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
        # V3 A2/A3: what each key's event does to the sectors it moves.
        cls.events = tuple(cls.m.PICKUP_EVENTS.values())
        cls.event_heights = pe.heights_after(cls.events, cls.sectors, cls.lines, cls.sides)
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
        """The sector containing (x, y): the nearest vertical line east of
        the point and which side of it the point is on (front = west when
        the line runs south)."""
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
            floor, ceiling = s["heightfloor"], s["heightceiling"]
            if i in self.door_sectors and s["id"] in open_tags:
                ceiling = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                           - DOOR_OPENS_BELOW_CEILING)
            if i in self.event_heights and s["id"] in open_tags:
                floor, ceiling = self.event_heights[i]     # V3 A2/A3: the event has run
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
        out = {}
        for t in self.key_things():
            out[self.m.KEY_LOCKS[t["type"]]] = self.sector_at(t["x"], t["y"])
        return out

    def death_specials(self):
        """[(tag, sector the monster stands in)] for every monster whose
        thing special opens a door when it dies (v1.1: the General)."""
        return [(t["arg0"], self.sector_at(t["x"], t["y"])) for t in self.things
                if t["type"] in self.monster_numbers and t.get("special") == SPECIAL_DOOR_OPEN]

    def event_spots(self):
        """[(tag, sector)] for every pickup event: where its key lies."""
        by_type = {t["type"]: t for t in self.things if t.get("special")}
        return [(event.tag, self.sector_at(by_type[ednum]["x"], by_type[ednum]["y"]))
                for ednum, event in self.m.PICKUP_EVENTS.items()]

    def progression(self, kills=False, events=None):
        """Play the map as a player can. Manual doors open whenever the
        player can stand at their line; then, one round at a time, every
        switch and locked door he can now reach and work (a locked door only
        once the sector of ITS key is reachable). With `kills`, a monster's
        death special counts as a switch the player works once he can reach
        the monster; without it (the default) nobody has to die: the
        critical route. `events` (V3 A2/A3; by default as `kills`: the
        full play) runs each key's pickup event as soon as the key's sector
        is reachable, as a manual door opens; without it no event runs, and
        the route must still be finished (PICKUP-EVENTS R3). Returns one
        (open tags, reachable sectors, locks held) per round."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        keys = self.key_sectors()
        deaths = self.death_specials() if kills else []
        spots = self.event_spots() if (kills if events is None else events) else []
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = {lock for lock, sector in keys.items() if sector in reach}
            free, gated = {tag for tag, sector in spots if sector in reach}, set()
            gated |= {tag for tag, sector in deaths if sector in reach}
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
                    gated.add(tag)           # a switch: one round per press
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
        """{texture: total length} of the one-sided walls of a sector."""
        out = Counter()
        for ld in self.lines:
            if "sideback" in ld or self.front(ld) != sector:
                continue
            (ax, ay), (bx, by) = self.line_points(ld)
            out[self.sides[ld["sidefront"]].get("texturemiddle")] += abs(bx - ax) + abs(by - ay)
        return out

    def middle_faces(self, texture):
        """Two-sided lines with `texture` in the middle: [(line, sector it faces)]."""
        out = []
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            for side in (ld["sidefront"], ld["sideback"]):
                if self.sides[side].get("texturemiddle") == texture:
                    out.append((ld, self.sides[side]["sector"]))
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
        """Every height change the player walks UP is 16 at most; anything
        higher is a drop (served by a stair, test_no_trap) or a prop."""
        every = set().union(*(r[0] for r in self.progression(kills=True)))
        h = self.heights(every)
        for a, dsts in self.adjacency(every).items():
            for b in dsts:
                rise = h[b][0] - h[a][0]
                self.assertLessEqual(rise, self.m.STEP, f"{self.zone_of[a]} -> {self.zone_of[b]}")

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
            self.assertIn(s["textureceiling"], flats | set(self.m.BUILTIN_FLATS),
                          f"sector {self.zone_of[i]}")
        for name in walls | flats:
            self.assertTrue(_packed(name), f"{name} is not in assets/")

    def test_the_sky_is_over_the_loading_dock(self):
        """D121: MAPINFO gives MAP03 a sky (SDSKY7), so some ceiling shows
        it: the loading dock, the works' yard, and its rails, nothing else.
        No sky sector is a door or touches one, and every room next to the
        sky (the spur's tunnel, the arch, the road gate's recess) keeps a
        ceiling of its own below the sky's, so the wall above it is drawn."""
        m = self.m
        sky = {i for i, s in enumerate(self.sectors) if s["textureceiling"] == m.SKY}
        self.assertTrue(sky, "no F_SKY1 sector")
        self.assertEqual({"z2_dock", "rails_z2_dock"}, {self.zone_of[i] for i in sky})
        doors = {i for i, s in enumerate(self.sectors) if s["heightceiling"] == s["heightfloor"]}
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a = self.sides[ld["sidefront"]]["sector"]
            b = self.sides[ld["sideback"]]["sector"]
            for here, there in ((a, b), (b, a)):
                if here in sky and there not in sky:
                    self.assertNotIn(there, doors, self.zone_of[there])
                    self.assertLess(self.sectors[there]["heightceiling"],
                                    self.sectors[here]["heightceiling"], self.zone_of[there])

    def test_the_tankograd_set_is_placed(self):
        """v1 (D66): every installed Tankograd piece the design asked for is
        on a wall or a floor of the built map, animations by frame 1."""
        used = set()
        for sd in self.sides:
            used |= {sd.get(k) for k in ("texturetop", "texturemiddle", "texturebottom")}
        for s in self.sectors:
            used |= {s["texturefloor"], s["textureceiling"]}
        for name in self.m.TANKOGRAD:
            self.assertIn(name, used, name)
            self.assertTrue(_packed(name), f"{name} is not in assets/")
        for name in ("SDMOLT1", "SDPORT1"):
            self.assertIn(name, self.m.TANKOGRAD, "an animation is placed by its first frame")

    def test_every_door_leaf_is_one_tile(self):
        """Every door-leaf face is 128 wide and hangs 128 from the ceiling of
        the room it faces to the door's floor (no tiling, MAP01 section 6)."""
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
                         "five leafed doors, two faces each, each lock in its own trim")

    def test_each_locked_door_wears_its_keys_trim(self):
        m = self.m
        for tag, leaf in ((m.TAG_YELLOW_DOOR, m.DOOR_YELLOW), (m.TAG_RED_DOOR, m.DOOR_RED)):
            faces = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE
                     and ld["arg0"] == tag]
            self.assertEqual(2, len(faces))
            for ld in faces:
                self.assertEqual(leaf, self.sides[ld["sidefront"]]["texturetop"], tag)

    def test_star_plaques_frame_the_yellow_door_only(self):
        """The art-director's note on v0: red star plaques either side of the
        red door camouflaged its red trim. They stay at the yellow lock."""
        m = self.m
        plaques = [ld for ld in self.lines if "sideback" not in ld
                   and self.sides[ld["sidefront"]].get("texturemiddle") == m.STAR]
        self.assertEqual(2, len(plaques))
        for ld in plaques:
            portal = self.front(ld)
            self.assertEqual("z3_yellow_portal", self.zone_of[portal])
            s = self.sectors[portal]
            self.assertEqual(m.PLAQUE, s["heightceiling"] - s["heightfloor"])
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.PLAQUE, abs(bx - ax) + abs(by - ay))

    def test_the_red_door_stands_out_from_its_wall(self):
        """Either side of the red leaf, plain whitewashed brick, one tile high:
        nothing red on the red lock's wall but the leaf itself."""
        m = self.m
        walls = self.one_sided_textures(self.plan["z3_red_portal"])
        self.assertEqual({m.BRICK_DADO: 2 * DOOR_TILE}, dict(walls))
        portal = self.sectors[self.plan["z3_red_portal"]]
        self.assertEqual(DOOR_TILE, portal["heightceiling"] - portal["heightfloor"])

    def test_every_picture_on_a_wall_is_one_whole_tile(self):
        """The shut gates, the flags and the clerestory panes: each on one
        line exactly as wide as the picture, in a recess exactly as high."""
        m = self.m
        widths = {m.ROAD_GATE: 128, m.FLAG_REICH: 64, m.FLAG_LEGION: 64, m.WINDOW: 64}
        found = Counter()
        for ld in self.lines:
            texture = self.sides[ld["sidefront"]].get("texturemiddle")
            if "sideback" in ld or texture not in widths:
                continue
            found[texture] += 1
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(widths[texture], abs(bx - ax) + abs(by - ay), texture)
            s = self.sectors[self.front(ld)]
            self.assertEqual(128, s["heightceiling"] - s["heightfloor"], texture)
        north, south = len(m.CLERESTORY_NORTH), len(m.CLERESTORY_SOUTH)
        self.assertEqual({m.ROAD_GATE: 2, m.FLAG_REICH: 1, m.FLAG_LEGION: 1,
                          m.WINDOW: north + south}, dict(found))

    def test_the_flags_hang_side_by_side_at_the_drum(self):
        """LORE: both flags side by side; here either side of the drum's gate."""
        for zone in ("p_flag_reich", "p_flag_legion"):
            self.assertIn(self.plan["p_hall"], self.neighbours[self.plan[zone]], zone)

    def test_the_banner_hangs_over_the_factory_floor(self):
        m = self.m
        if not m.SLOGAN:
            self.skipTest("SDSLOG1 not installed")
        faces = self.middle_faces(m.SLOGAN)
        self.assertEqual(2, len(faces), "one face each way along the hall")
        for ld, room in faces:
            self.assertEqual(self.plan["z3_hall"], room)
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(ax, bx, "it faces along the hall's axis")
            self.assertEqual(m.SLOGAN_SIZE[0], abs(by - ay))
        self.assertGreaterEqual(m.HALL_CEIL - m.SLOGAN_SIZE[1], 4 * PLAYER_HEIGHT,
                                "high over the floor, out of every sight line")

    def test_chains_hang_over_both_pits(self):
        m = self.m
        if not m.CHAIN:
            self.skipTest("SDCHAN1 not installed")
        by_pit = Counter(self.zone_of[room] for _ld, room in self.middle_faces(m.CHAIN))
        self.assertEqual({"t_pit_a": 4, "t_pit_b": 4}, dict(by_pit))

    def test_the_drum_is_steel_and_the_portal_is_behind_the_dais(self):
        m = self.m
        dais = self.one_sided_textures(self.plan["p_dais_3"])
        self.assertGreaterEqual(dais[m.PORTAL], 2 * 96, "the wall behind the dais")
        ring = [ld for ld in self.lines if "sideback" not in ld
                and self.front(ld) == self.plan["p_hall"]
                and all(640 <= v <= 1024 for v in (self.line_points(ld)[0][0], self.line_points(ld)[1][0]))
                and all(1024 <= v <= 1408 for v in (self.line_points(ld)[0][1], self.line_points(ld)[1][1]))]
        self.assertTrue(ring)
        for ld in ring:
            self.assertEqual(m.STEEL, self.sides[ld["sidefront"]]["texturemiddle"])

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
        """The colour of the lock is the colour of where the key is, and no
        other sector of the map wears it."""
        m = self.m
        keys = self.key_sectors()
        colours = set()
        for lock, portal in m.LOCK_PORTALS.items():
            colour = self.sectors[self.plan[portal]].get("lightcolor")
            self.assertIsNotNone(colour, portal)
            self.assertEqual(colour, self.sectors[keys[lock]].get("lightcolor"),
                             f"the key of lock {lock}")
            colours.add(colour)
            wearing = {self.zone_of[i] for i, s in enumerate(self.sectors)
                       if s.get("lightcolor") == colour}
            same = defaultdict(set)
            for a, ns in self.neighbours.items():
                same[a] = {b for b in ns if self.sectors[b].get("lightcolor") == colour}
            key_room = {self.zone_of[i] for i in self.flood(same, keys[lock])}
            self.assertEqual({portal} | key_room, wearing,
                             "one patch of colour round the key, one at the lock")
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

    def test_the_only_special_sectors_are_the_secret_and_the_channel(self):
        """v1.1: S1 is the one sector with a `special`, the secret bit and
        nothing else; the channel hurts by the UDMF damage fields, not by a
        special (no Damage_InstantDeath 115, no Boom damage bits). S2 and S3
        are v3's (design section 8)."""
        m = self.m
        special = {self.zone_of[i]: s["special"] for i, s in enumerate(self.sectors) if s.get("special")}
        self.assertEqual({zone: m.SECTOR_SPECIAL_SECRET for zone in m.SECRET_ZONES}, special)
        hurting = {self.zone_of[i] for i, s in enumerate(self.sectors) if s.get("damageamount")}
        self.assertEqual({"f_channel"}, hurting)

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        """With the General killed (and the keys' events run: the full play),
        every sector but the props; without him and with no event, every
        sector but the props, his stores, the yellow key's closets and the
        red key's goods lift (V3 A2/A3)."""
        events_only = self.named(*self.m.OFFICE_CLOSETS, *self.m.EVENT_ZONES["office_closets"],
                                 *self.m.EVENT_ZONES["goods_lift"])
        shut = self.named(*self.m.REWARD_ZONES, "p_stores_door") | events_only
        for kills, closed in ((True, set()), (False, shut)):
            reach = self.progression(kills)[-1][1]
            unreachable = set(range(len(self.sectors))) - reach
            expected = self.props | closed
            self.assertEqual(expected, unreachable,
                             f"kills={kills}: {sorted(self.zone_of[i] for i in unreachable ^ expected)}")

    def test_the_exit_is_reached_and_only_in_the_last_round(self):
        rounds = self.progression()
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["p_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        self.assertIn(exit_sector, rounds[-1][1], "the exit is never reached")
        for opened, reach, _ in rounds[:-1]:
            self.assertNotIn(exit_sector, reach, f"exit reached with only {sorted(opened)}")
        niche = self.sectors[exit_sector]
        self.assertEqual(self.m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])

    def test_no_trap_at_any_stage(self):
        """From every sector the player can reach at any stage there is a
        way back to the start with what is open at that stage."""
        for kills in (False, True):
            for opened, reach, _held in self.progression(kills):
                back = self.flood(self.reverse(self.adjacency(opened)), self.start)
                stranded = sorted(self.zone_of[i] for i in reach - back)
                self.assertEqual([], stranded, f"with tags {sorted(opened)} open, kills={kills}")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        for kills in (False, True):
            opened, reach, _ = self.progression(kills)[-1]
            exit_sector = self.front(self.exit_line())
            onward = self.flood(self.reverse(self.adjacency(opened)), exit_sector)
            self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward), f"kills={kills}")

    def test_the_drops_are_left_by_stairs(self):
        """Foundry floor and tank pits are below their rooms: dropping in is
        free, and each has its stair back up."""
        adj = self.adjacency(set().union(*(r[0] for r in self.progression())))
        for low, high, stair_top, stair_bottom in (
                ("f_floor", "f_gallery", "f_stair_1", "f_stair_3"),
                ("f_floor", "f_platform", "f_platform_stair_1", "f_platform_stair_3"),
                ("t_pit_a", "t_line", "t_pit_a_w_1", "t_pit_a_w_2"),
                ("t_pit_b", "t_line", "t_pit_b_e_2", "t_pit_b_e_1")):
            low_i, high_i = self.plan[low], self.plan[high]
            if high_i in self.neighbours[low_i]:
                self.assertIn(low_i, adj[high_i], f"{high} -> {low}")
                self.assertNotIn(high_i, adj[low_i], f"{low} -> {high} is a drop")
            self.assertIn(self.plan[stair_bottom], adj[low_i], low)
            self.assertIn(high_i, adj[self.plan[stair_top]], stair_top)

    def test_the_route_is_the_designed_one(self):
        """Four rounds: the offices and the yellow key; the yellow door; the
        red door and SW-A; SW-B. Each gate in its round and no earlier."""
        m = self.m
        rounds = self.progression()
        self.assertEqual(4, len(rounds))
        (o0, r0, h0), (o1, r1, h1), (o2, r2, h2), (o3, r3, h3) = rounds
        # S1's panel is a push panel like D1 and D2: the model opens it with
        # them, whether or not a player finds it (it is never needed).
        self.assertEqual({m.TAG_D1_PLANNING, m.TAG_D2_ARCHIVE, m.TAG_S1_PANEL}, set(o0))
        self.assertEqual({m.LOCK_YELLOW_CARD}, set(h0), "the yellow key with no switch and no key")
        self.assertIn(self.plan["o_desk"], r0)
        line = self.named("t_vestibule", "t_line", "f_gallery", "f_floor", "f_platform")
        self.assertFalse(line & r0, "the tank line and the foundry are behind the yellow door")
        self.assertEqual({m.TAG_YELLOW_DOOR}, set(o1 - o0))
        self.assertTrue(line <= r1)
        self.assertEqual({m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD}, set(h1))
        portal = self.named("p_ante", "p_hall", "p_booth")
        self.assertFalse(portal & r1, "the portal hall is behind the red door")
        self.assertEqual({m.TAG_RED_DOOR, m.TAG_SHUTTER}, set(o2 - o1))
        self.assertTrue(portal <= r2)
        self.assertNotIn(self.plan["p_drum"], r2, "the drum is shut until SW-B")
        self.assertEqual({m.TAG_GATE}, set(o3 - o2))
        self.assertIn(self.plan["p_drum"], r3)

    def test_the_shortcut_is_not_needed(self):
        """The red door is reached the long way too: SW-A's shutter is a
        shortcut, never the only way (design section 5)."""
        m = self.m
        rounds = self.progression()
        everything_but_the_shutter = set().union(*(r[0] for r in rounds)) - {m.TAG_SHUTTER}
        self.assertIn(self.plan["p_exit_niche"], self.reachable(everything_but_the_shutter))

    def test_neither_the_secret_nor_the_generals_stores_is_needed(self):
        """D68: the exit is reached with every tag open but S1's panel and
        the stores', so nobody needs the secret or the General's death."""
        m = self.m
        every = set().union(*(r[0] for r in self.progression(kills=True)))
        self.assertIn(m.TAG_GENERAL_STORES, every)
        critical = every - {m.TAG_S1_PANEL, m.TAG_GENERAL_STORES}
        self.assertIn(self.plan["p_exit_niche"], self.reachable(critical))

    # --- the keys ------------------------------------------------------------
    def test_one_yellow_and_one_red_key_on_the_route_outside_any_secret(self):
        m = self.m
        types = sorted(t["type"] for t in self.key_things())
        self.assertEqual(sorted([m.ED_YELLOW_CARD, m.ED_RED_CARD]), types)
        sectors = {t["type"]: self.sector_at(t["x"], t["y"]) for t in self.key_things()}
        for ed, zone in m.KEY_ZONES.items():
            self.assertEqual(self.plan[zone], sectors[ed])
            self.assertFalse(self.sectors[sectors[ed]].get("special"))

    def test_each_key_lies_alone_on_its_pedestal(self):
        """MAP02's booth rule: nothing else on the lit place the key lies."""
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
            self.assertIn("sideback", ld)
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            lock, door = expected[ld["arg0"]]
            self.assertEqual((ld["arg0"], 16, 0, lock, 0),
                             tuple(ld[f"arg{i}"] for i in range(5)))
            self.assertEqual(self.plan[door], self.sides[ld["sideback"]]["sector"],
                             "the door is the back side, so the face is pressed from the room")

    def test_both_locked_doors_are_seen_on_entering_the_hall(self):
        """The key grammar: both locks are shown at once, from the arch out
        of the dock, before either key."""
        eye = self.eye(3104, 1184, "z2_arch")
        for y in (1136, 1184, 1232):
            for z in (16, 64, 112):
                self.assertIsNone(self.blocked(eye, (1601, y, z)), f"red door y {y} z {z}")
        # The yellow leaf from above the conveyors' height: from the arch the
        # south-east line hides its bottom 32 units, as cover should.
        for x in (2256, 2304, 2352):
            for z in (48, 80, 112):
                self.assertIsNone(self.blocked(eye, (x, 705, z)), f"yellow door x {x} z {z}")

    def test_the_banner_does_not_hide_the_red_door_from_the_arch(self):
        """The banner hangs across the line from the arch to the red door:
        at the banner the sight line is still under its bottom edge."""
        m = self.m
        eye = self.eye(3104, 1184, "z2_arch")
        bottom = m.HALL_CEIL - m.SLOGAN_SIZE[1]
        for z in (16, 64, 112):
            t = (eye[0] - m.BANNER[2]) / (eye[0] - 1601)
            self.assertLess(eye[2] + (z - eye[2]) * t, bottom, f"z {z}")

    def test_the_yellow_key_is_seen_from_the_factory_floor(self):
        """MAP02's lesson (D58): the key is shown, not hidden. From the
        middle of the hall, up the lane and the stair, on the lit desk."""
        target = (self.m.YELLOW_KEY_SPOT[0], self.m.YELLOW_KEY_SPOT[1],
                  self.sectors[self.plan["o_desk"]]["heightfloor"] + KEY_SPRITE_MID)
        for y in (1024, 1184):
            self.assertIsNone(self.blocked(self.eye(2304, y, "z3_lane"), target), f"from y {y}")

    def test_the_red_key_is_seen_on_entering_the_foundry(self):
        target = (self.m.RED_KEY_SPOT[0], self.m.RED_KEY_SPOT[1],
                  self.sectors[self.plan["f_pedestal"]]["heightfloor"] + KEY_SPRITE_MID)
        self.assertIsNone(self.blocked(self.eye(1760, 256, "f_gallery"), target))
        self.assertIsNone(self.blocked(self.eye(1824, 256, "t_pour_arch"), target))

    def test_no_monster_stands_between_a_key_and_where_it_is_seen(self):
        """The sight lines are clear of bodies at spawn on every skill: no
        monster's box crosses the line from a viewpoint to its key."""
        m = self.m
        views = ((self.eye(2304, 1024, "z3_lane"), m.YELLOW_KEY_SPOT),
                 (self.eye(2304, 1184, "z3_lane"), m.YELLOW_KEY_SPOT),
                 (self.eye(1760, 256, "f_gallery"), m.RED_KEY_SPOT),
                 (self.eye(1824, 256, "t_pour_arch"), m.RED_KEY_SPOT))
        for (x0, y0, _z), (x1, y1) in views:
            for t in self.monsters():
                radius = self.body[t["type"]][0]
                n = max(1, int(math.dist((x0, y0), (x1, y1)) / SIGHT_STEP))
                for k in range(n + 1):
                    x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                    inside = abs(x - t["x"]) < radius and abs(y - t["y"]) < radius
                    self.assertFalse(inside, f"{t['type']} at ({t['x']}, {t['y']}) "
                                             f"on the line ({x0}, {y0}) -> ({x1}, {y1})")

    def test_the_lane_joins_the_yellow_door_to_the_office_stair(self):
        lane = self.plan["z3_lane"]
        self.assertEqual(self.m.FLOOR_LANE, self.sectors[lane]["texturefloor"])
        self.assertIn(self.plan["z3_yellow_portal"], self.neighbours[lane])
        self.assertIn(self.plan["o_stair_1"], self.neighbours[lane])

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
        self.assertEqual(m.EXIT_FACE, self.sides[self.exit_line()["sidefront"]]["texturemiddle"],
                         "the exit wears the hazard panel, as on MAP01 and MAP02")

    def test_each_switch_opens_what_the_design_says(self):
        m = self.m
        found = {ld["arg0"]: self.front(ld) for ld in self.switch_lines()}
        self.assertEqual({m.TAG_SHUTTER: self.plan["f_swa_niche"],
                          m.TAG_GATE: self.plan["p_booth"]}, found)
        self.assertEqual(self.named("shutter", "closet_hs_door", "closet_hn_door"),
                         self.doors[m.TAG_SHUTTER])
        self.assertEqual(self.named("gate"), self.doors[m.TAG_GATE])

    def test_sw_a_stands_beside_the_shutter_passage(self):
        sw_a = [ld for ld in self.switch_lines() if ld["arg0"] == self.m.TAG_SHUTTER][0]
        (ax, ay), (bx, by) = self.line_points(sw_a)
        middle = ((ax + bx) / 2, (ay + by) / 2)
        self.assertLessEqual(math.dist(middle, (1728, 688)), DOOR_TILE)

    def test_the_shutter_and_the_closets_are_wall_from_the_hall(self):
        """No door leaf the player cannot open from where he stands: the
        shutter and the closet panels wear the hall's own brick."""
        for door in ("shutter", "closet_hs_door", "closet_hn_door"):
            hall_face = [ld for ld in self.lines if "sideback" in ld
                         and set(self._pair(ld)) == self.named(door, "z3_hall")]
            self.assertEqual(1, len(hall_face), door)
            ld = hall_face[0]
            side = ld["sidefront"] if self.front(ld) == self.plan["z3_hall"] else ld["sideback"]
            self.assertEqual(self.m.HALL_WALL, self.sides[side]["texturetop"], door)
            self.assertFalse(ld.get("special"), door)

    def test_the_gate_is_seen_before_and_from_sw_b(self):
        for eye in (self.eye(1440, 1184, "p_ante"), self.eye(1216, 1744, "p_booth")):
            for y in (1168, 1216, 1264):
                self.assertIsNone(self.blocked(eye, (1025, y, 64)), f"from {eye[:2]}, y {y}")

    def test_the_exit_is_seen_from_the_drums_gate(self):
        opened = self.progression()[-1][0]
        niche = self.sectors[self.plan["p_exit_niche"]]
        for z in (32, 64, 96):
            target = (689, 1216, niche["heightfloor"] + z)
            self.assertIsNone(self.blocked(self.eye(1056, 1216, "p_porch"), target, opened),
                              f"z {z}")

    # --- doors -----------------------------------------------------------------
    def test_every_door_opens_tall_enough(self):
        for index in sorted(self.door_sectors):
            s = self.sectors[index]
            opened = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[index])
                      - DOOR_OPENS_BELOW_CEILING)
            self.assertGreaterEqual(opened - s["heightfloor"], PLAYER_HEIGHT, self.zone_of[index])

    def test_no_press_can_consume_a_gate(self):
        """Manual doors repeat; every one-shot line opens for good."""
        for i, ld in enumerate(self.lines):
            special = ld.get("special")
            if special not in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE,
                               self.m.SPECIAL_DOOR_LOCKED_RAISE):
                continue
            if "sideback" in ld:
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
            else:
                self.assertEqual(SPECIAL_DOOR_OPEN, special, f"linedef {i}")

    # --- v1: population --------------------------------------------------------
    def test_every_thing_stands_in_the_zone_its_table_names(self):
        m = self.m
        rows = ([(z, k, x, y) for z, k, x, y, *_ in m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in m.ITEMS + m.SECRET_ITEMS + m.STORES_ITEMS
                   + m.AMMO])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is in {self.zone_of.get(self.sector_at(x, y))}")

    def test_the_monsters_are_the_bestiarys_own_numbers_in_mapinfo(self):
        """MAPINFO's editor numbers, 21100-21107, each assigned in DoomEdNums
        to the class this map means; no Doom monster number."""
        text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        block = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S).group(1)
        assigned = {int(n): c for n, c in re.findall(r"(\d+)\s*=\s*(\w+)", block)}
        for ednum, name in self.m.MONSTER_CLASSES.items():
            self.assertEqual(name, assigned.get(ednum), ednum)
        for ednum in self.m.ROUTE_WEAPONS:
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertEqual(set(self.m.MONSTER_CLASSES), {t["type"] for t in self.monsters()},
                         "every class of the bestiary fights here, the episode's climax")

    def test_every_monster_has_room_for_its_body(self):
        """All four corners of the body's box on floor it can stand on (not a
        prop, a door or the void), within a step of each other, and the
        lowest ceiling over them at least the body's height above."""
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
        """Doom's bodies are squares: two that overlap at spawn are stuck."""
        bodies = self.monsters()
        for i, a in enumerate(bodies):
            for b in bodies[i + 1:]:
                reach = self.body[a["type"]][0] + self.body[b["type"]][0]
                apart = abs(a["x"] - b["x"]) >= reach or abs(a["y"] - b["y"]) >= reach
                self.assertTrue(apart, f"{a['type']} at ({a['x']}, {a['y']}) and "
                                       f"{b['type']} at ({b['x']}, {b['y']})")

    def test_every_pickup_can_be_picked_up(self):
        reach = self.progression(kills=True)[-1][1]
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
        """Section 9: 25 / 38 / 52. Whatever fights on an easier skill also
        fights on a harder one."""
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    def test_the_tables_factions_are_the_classes_own(self):
        """REICH and LEGION in the map say what each class's ZScript says."""
        m = self.m
        for kind, ednum in m.MONSTER_KINDS.items():
            faction = self.faction[ednum]
            if kind in m.REICH:
                self.assertEqual("REICH", faction, kind)
            elif kind in m.LEGION:
                self.assertEqual("LEGION", faction, kind)
            else:
                self.assertEqual("BOTH", faction, kind)

    def test_the_factory_mixes_the_two_factions(self):
        """D35 for the climax: the Legion holds the works' public face (hall,
        offices), the Reich the yards and the closed shop (spur, dock, tank
        line); both meet in the foundry and both guard the portal. Hybrids
        stand anywhere; the closets are the counter-attack, not a garrison."""
        m = self.m
        seen = defaultdict(set)
        for zone, kind, *_ in m.MONSTERS:
            if zone.startswith(m.CLOSET_PREFIX):
                continue
            faction = self.faction[m.MONSTER_KINDS[kind]]
            if zone.startswith(m.LEGION_GROUND):
                ground = "legion"
                self.assertNotEqual("REICH", faction, f"{kind} in {zone}")
            elif zone.startswith(m.REICH_GROUND):
                ground = "reich"
                self.assertNotEqual("LEGION", faction, f"{kind} in {zone}")
            else:
                self.assertTrue(zone.startswith(m.BOTH_GROUND), zone)
                ground = zone[:2]
            seen[ground].add(faction)
        self.assertIn("LEGION", seen["legion"])
        self.assertIn("REICH", seen["reich"])
        for ground in ("f_", "p_"):
            self.assertTrue({"LEGION", "REICH"} <= seen[ground], f"{ground}: {seen[ground]}")

    def test_both_factions_guard_the_portal_on_every_skill(self):
        m = self.m
        portal = {self.plan["p_hall"]}
        for skill in SKILLS:
            here = [t for t in self.on(skill, self.monsters())
                    if self.sector_at(t["x"], t["y"]) in portal]
            factions = {self.faction[t["type"]] for t in here}
            self.assertTrue({"LEGION", "REICH"} <= factions, f"skill {skill}: {factions}")

    def test_the_general_is_the_boss_of_the_portal_hall(self):
        """BESTIARY section 9: one General, on every skill, in the portal hall
        (384 high: he never passes a door), where the red door leads."""
        m = self.m
        generals = self.things_of({m.ED_GENERAL})
        self.assertEqual(1, len(generals))
        g = generals[0]
        self.assertTrue(all(g[f"skill{n}"] for n in range(1, 6)))
        self.assertEqual(self.plan["p_hall"], self.sector_at(g["x"], g["y"]))
        rounds = self.progression()
        self.assertNotIn(self.plan["p_hall"], rounds[1][1], "behind the red door")
        hp = self.hit_points
        self.assertEqual(max(hp.values()), hp[m.ED_GENERAL], "the strongest thing in the episode")

    def test_the_heavies(self):
        """LORE: the heavy hybrids. A Panzermensch on the tank line on every
        skill; the heavy Panzermensch on skill 4 only, on the tank line and in
        the portal hall; Doughboys in the foundry's tall room."""
        m = self.m
        pz = self.things_of({m.ED_PANZERMENSCH})
        self.assertEqual({2: 1, 3: 1, 4: 2}, {s: len(self.on(s, pz)) for s in SKILLS})
        every = [t for t in pz if t["skill2"]]
        self.assertEqual(self.plan["t_line"], self.sector_at(every[0]["x"], every[0]["y"]))
        heavy = self.things_of({m.ED_PANZER_HEAVY})
        self.assertEqual({2: 0, 3: 0, 4: 2}, {s: len(self.on(s, heavy)) for s in SKILLS})
        self.assertEqual(self.named("t_line", "p_hall"),
                         {self.sector_at(t["x"], t["y"]) for t in heavy})
        db = self.things_of({m.ED_DOUGHBOY})
        self.assertEqual({2: 1, 3: 1, 4: 3}, {s: len(self.on(s, db)) for s in SKILLS})
        self.assertIn(self.plan["f_floor"], {self.sector_at(t["x"], t["y"]) for t in db if t["skill2"]})

    def test_every_closet_holds_a_fight_and_opens_with_sw_a(self):
        """SW-A's closets in the hall: each panel on SW-A's tag, each closet
        occupied on skill 2, shut until SW-A's round and open after it."""
        m = self.m
        closets = [n for n in self.plan if n.startswith(m.CLOSET_PREFIX) and not n.endswith("_door")
                   and n not in m.OFFICE_CLOSETS]     # V3 A2's: Map03PickupEventsTest
        self.assertEqual(2, len(closets))
        rounds = self.progression()
        for name in closets:
            tag = self.sectors[self.plan[f"{name}_door"]]["id"]
            self.assertEqual(m.TAG_HALL_AMBUSH, tag, name)
            self.assertIn(self.plan["z3_hall"], self.neighbours[self.plan[f"{name}_door"]], name)
            inside = [t for t in self.on(2, self.monsters())
                      if self.sector_at(t["x"], t["y"]) == self.plan[name]]
            self.assertTrue(inside, f"{name} is empty on skill 2")
            first = next(k for k, (opened, _r, _h) in enumerate(rounds) if tag in opened)
            self.assertNotIn(self.plan[name], rounds[first - 1][1], f"{name} open early")
            self.assertIn(self.plan[name], rounds[first][1], f"{name} never opens")
        self.assertEqual(m.TAG_SHUTTER, m.TAG_HALL_AMBUSH)

    def test_the_weapons_are_on_every_skill_on_the_route(self):
        """Pistol start (+map MAP03 gives the TT-33 only): the IZh in the
        dock and the PPSh upstairs before any lock, the RPG-7 at the foot of
        the yellow door and the ROKS-3 on the foundry gallery before the red
        door; each once, on every skill, never in a secret."""
        m = self.m
        rounds = self.progression()
        for ednum, zone, stage in ((m.ED_IZH, "z2_dock", 0), (m.ED_PPSH, "o_corridor", 0),
                                   (m.ED_RPG7, "t_line", 1), (m.ED_ROKS3, "f_gallery", 1)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertFalse(self.sectors[where].get("special"))
            self.assertIn(where, rounds[stage][1], f"weapon {ednum} not reached by round {stage}")
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}),
                         "a Doom weapon number: the arsenal is ours (D13)")

    def test_the_rpg_is_met_before_the_tank_lines_panzermensch(self):
        """The RPG-7 lies at the yellow door's foot, nearer the door than any
        heavy on the tank line: it is in hand before the heavies are met."""
        m = self.m
        rpg = self.things_of({m.ED_RPG7})[0]
        door = (2304, 448)
        heavies = [t for t in self.things_of({m.ED_PANZERMENSCH, m.ED_PANZER_HEAVY})
                   if self.sector_at(t["x"], t["y"]) == self.plan["t_line"]]
        self.assertTrue(heavies)
        for t in heavies:
            self.assertLess(math.dist(door, (rpg["x"], rpg["y"])), math.dist(door, (t["x"], t["y"])))

    def test_consumables_scale_down(self):
        """Monsters up, consumables down, weapons flat (MAP01 section 8)."""
        m = self.m
        fixed = (self.monster_numbers | set(m.ROUTE_WEAPONS)
                 | {m.ED_PLAYER1_START, m.ED_YELLOW_CARD, m.ED_RED_CARD})
        for kind in {t["type"] for t in self.things} - fixed - self.ammo_kinds():
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def ammo_kinds(self):
        """The ammunition pickups (not the weapons that also give some)."""
        return ((set(SHELLS_GIVEN) | set(ROUNDS_GIVEN) | set(ROCKETS_GIVEN) | set(CELLS_GIVEN))
                - set(self.m.ROUTE_WEAPONS))

    def test_ammunition_scales_up_and_there_is_less_of_it(self):
        """D119: on the route, for every kind of ammunition, skill 2 has at
        most what skill 3 has and skill 3 at most what skill 4 has; and every
        skill has fewer ammunition pickups than v1 placed. The secret and
        the General's stores are on every skill, as before."""
        route = self.on_route(self.things)
        for kind in self.ammo_kinds():
            n = {s: len(self.on(s, [t for t in route if t["type"] == kind])) for s in SKILLS}
            self.assertLessEqual(n[2], n[3], kind)
            self.assertLessEqual(n[3], n[4], kind)
        for skill in SKILLS:
            n = len([t for t in self.on(skill, route) if t["type"] in self.ammo_kinds()])
            self.assertLess(n, V1_AMMO_PICKUPS[skill], f"skill {skill}")
        off = [t for t in self.things if t not in route and t["type"] in self.ammo_kinds()]
        for t in off:
            self.assertTrue(all(t[f"skill{s}"] for s in SKILLS), t)

    def ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]]
                   for t in self.on(skill, self.monsters()))

    def on_route(self, things):
        """The things outside the secret and the General's stores: what the
        route itself hands out (MAP02's `outside_secrets`, plus the stores)."""
        off = self.named(*self.m.SECRET_ZONES, *self.m.REWARD_ZONES)
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in off]

    def ammo_placed(self, skill):
        placed = self.on_route(self.on(skill, self.things))
        return sum(SHELLS_GIVEN.get(t["type"], 0)
                   + ROUNDS_GIVEN.get(t["type"], 0) / ROUNDS_PER_SHELL
                   + ROCKETS_GIVEN.get(t["type"], 0) * SHELLS_PER_ROCKET
                   + CELLS_GIVEN.get(t["type"], 0) * SHELLS_PER_CELL
                   + GRENADES_GIVEN.get(t["type"], 0) * SHELLS_PER_GRENADE for t in placed)

    def test_g3_8_the_ammo_budget(self):
        """G3-8 as D119 reads it, the General included: on every skill,
        ammunition placed on the route is inside that skill's band of what
        killing every monster takes, and shells are no more than 35 % of
        it, the troopers' dropped IZhs counted there (BALANCE 8.3) and
        nowhere else."""
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            low, high = G3_8_BAND[skill]
            self.assertGreaterEqual(have, low * need, f"skill {skill}: {have} for {need}")
            self.assertLessEqual(have, high * need, f"skill {skill}: {have} for {need}")
            placed = self.on_route(self.on(skill, self.things))
            shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed)
            kinds = Counter(self.m.MONSTER_CLASSES[t["type"]] for t in self.on(skill, self.monsters()))
            troopers, riflemen = kinds["SD_LegionTrooper"], kinds["SD_ReichRifleman"]
            dropped = troopers * DROP_SHELLS + riflemen * DROP_ROUNDS / ROUNDS_PER_SHELL
            self.assertLessEqual(shells + troopers * DROP_SHELLS, SHELL_SHARE_MAX * (have + dropped),
                                 f"skill {skill}: {shells} shells placed")

    def test_the_heavy_weapons_have_their_rounds(self):
        """The RPG-7 and the ROKS-3 are placed with something to fire beyond
        their own load. (v1 also asked shells and rounds alone to cover every
        monster but the General; BALANCE 8.4 as the PM amended it drops that
        rule, which cannot hold together with 8.3's shell share and the
        skill-4 ceiling.)"""
        m = self.m
        self.assertTrue(self.things_of({m.ED_ROCKET, m.ED_ROCKET_BOX}))
        self.assertTrue(self.things_of({m.ED_CELL, m.ED_CELL_PACK}))

    def start_rounds(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        """MAP01's G3 readiness check: at every stage of the route the damage
        placed so far, plus the starting rounds, is at least the floor of the
        skill's G3-8 band (D119) times the hit points met so far."""
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
                self.assertGreaterEqual(damage, G3_8_BAND[skill][0] * hp_so_far,
                                        f"skill {skill}, stage {stage}")
                seen = reach

    def test_the_newest_weapons_pool_leads_every_stage(self):
        """BALANCE 8.4 (D119, with the PM's amendment), stage by stage of the
        readiness check: a pool lies only from the stage where its weapon is
        (the TT-33's rounds from the start); of each stage's ammunition other
        than shells the leading pool is the largest share and at least 40 %
        of it. The leader is the newest weapon's pool, the IZh excepted
        (shells have 8.3) and the ROKS-3 excepted (fuel stays moderate, at
        most 15 % of the map's ammunition: the weapon before it leads); and
        outside the General's stage the PG-7V are at most 30 % of the stage
        and the newest bullet weapon's rounds lead.
        In the General's stage the PG-7V and the fuel together are at
        least his 48 shells (8.4, third rule)."""
        m = self.m
        pool_of = {m.ED_IZH: "shells", m.ED_PPSH: "rounds", m.ED_RPG7: "rockets",
                   m.ED_ROKS3: "fuel"}
        pools = {"shells": SHELLS_GIVEN, "rounds": ROUNDS_GIVEN, "rockets": ROCKETS_GIVEN,
                 "fuel": CELLS_GIVEN}
        weight = {"shells": 1, "rounds": 1 / ROUNDS_PER_SHELL, "rockets": SHELLS_PER_ROCKET,
                  "fuel": SHELLS_PER_CELL}
        for skill in SKILLS:
            route = self.on_route(self.on(skill, self.things))
            total_map = sum(pools[p].get(t["type"], 0) * weight[p] for t in route for p in pools)
            fuel_map = sum(pools[p].get(t["type"], 0) * weight[p] for t in route for p in pools
                           if p == "fuel")
            self.assertLessEqual(fuel_map, FUEL_SHARE_MAX * total_map, f"skill {skill}: fuel")
            seen, newest, met = set(), "rounds", {"rounds"}
            for stage, row in enumerate(self.progression()):
                reach = row[1]
                here = [t for t in route if self.sector_at(t["x"], t["y"]) in reach - seen]
                for ednum, pool in pool_of.items():
                    if any(t["type"] == ednum for t in here):
                        met.add(pool)
                        if pool not in ("shells", "fuel"):
                            newest = pool
                share = {p: sum(pools[p].get(t["type"], 0) for t in here) * weight[p] for p in pools}
                for pool, amount in share.items():
                    if amount:
                        self.assertIn(pool, met, f"skill {skill}, stage {stage}: {pool} before its weapon")
                boss = any(m.MONSTER_CLASSES.get(t["type"]) == "SD_General" for t in here)
                leader = newest
                if leader == "rockets" and not boss:
                    leader = "rounds"
                    self.assertLessEqual(share["rockets"], ROCKET_SHARE_MAX * sum(share.values()),
                                         f"skill {skill}, stage {stage}: {share}")
                rest = {p: v for p, v in share.items() if p != "shells"}
                if sum(rest.values()):
                    self.assertEqual(max(rest.values()), rest[leader], f"skill {skill}, stage {stage}: {rest}")
                    self.assertGreaterEqual(rest[leader], NEWEST_SHARE_MIN * sum(rest.values()),
                                            f"skill {skill}, stage {stage}: {rest}")
                if boss:
                    self.assertGreaterEqual(share["rockets"] + share["fuel"], SHELLS_TO_KILL["SD_General"],
                                            f"skill {skill}, stage {stage}: the boss's stage")
                seen = reach

    def test_every_weapon_stretch_is_paid_for(self):
        """D119, stretch by stretch along the weapons: the damage placed so
        far on the route plus the starting rounds is at least the skill's
        band floor times the hit points met so far. Counted from the tables,
        which the zone test pins to the TEXTMAP."""
        m = self.m
        rows = [(z, e, lo) for z, e, _x, _y, lo in m.AMMO]
        rows += [(z, e, 2) for z, e, _x, _y, _top in m.ITEMS if e in m.ROUTE_WEAPONS]
        for skill in SKILLS:
            hp, damage = 0, self.start_rounds() * PPSH_AVERAGE
            for name, zones in MAP03_STRETCHES:
                hp += sum(self.hit_points[m.MONSTER_KINDS[k]]
                          for z, k, _x, _y, _a, lo in m.MONSTERS if z in zones and lo <= skill)
                here = [e for z, e, lo in rows if z in zones and lo <= skill]
                damage += sum(SHELLS_GIVEN.get(e, 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(e, 0) * PPSH_AVERAGE
                              + ROCKETS_GIVEN.get(e, 0) * RPG_AVERAGE
                              + CELLS_GIVEN.get(e, 0) * ROKS_AVERAGE for e in here)
                self.assertGreaterEqual(damage, G3_8_BAND[skill][0] * hp, f"skill {skill}, {name}")
        every = set().union(*(zones for _n, zones in MAP03_STRETCHES))
        self.assertFalse({z for z, *_ in m.MONSTERS} - every)
        self.assertFalse({z for z, *_ in m.AMMO} - every)

    def test_health_and_armour_on_skill_4(self):
        """A boss map: at least MAP02's health on skill 4, the flak vest on
        the tank line and the heavy vest before the General."""
        m = self.m
        found = Counter(t["type"] for t in self.on_route(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 7)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])
        self.assertEqual(1, found[m.ED_BLUE_ARMOR])
        vest = self.things_of({m.ED_BLUE_ARMOR})[0]
        rounds = self.progression()
        where = self.sector_at(vest["x"], vest["y"])
        self.assertIn(where, rounds[2][1])
        self.assertNotIn(where, rounds[1][1])

    # --- v1.1 (D68): S1 and the Hand Katyusha --------------------------------
    def test_s1_holds_the_hand_katyusha(self):
        """D68 "ok secreto": slot 7 lies in S1, the one secret sector, on
        every skill, and nowhere else; MAPINFO gives 21007 to our class."""
        m = self.m
        found = self.things_of({m.ED_HAND_KATYUSHA})
        self.assertEqual(1, len(found))
        t = found[0]
        self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)) and t["single"])
        where = self.sector_at(t["x"], t["y"])
        self.assertIn(self.zone_of[where], m.SECRET_ZONES)
        self.assertTrue(self.sectors[where]["special"] & m.SECTOR_SPECIAL_SECRET)
        self.assertNotIn(m.ED_HAND_KATYUSHA, m.ROUTE_WEAPONS)
        text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        block = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S).group(1)
        assigned = {int(n): c for n, c in re.findall(r"(\d+)\s*=\s*(\w+)", block)}
        self.assertEqual("SD_HandKatyusha", assigned.get(m.ED_HAND_KATYUSHA))

    def s1_panel_lines(self):
        return [ld for ld in self.lines if ld.get("special") == SPECIAL_DOOR_OPEN
                and ld["arg0"] == self.m.TAG_S1_PANEL]

    def test_s1_opens_from_the_archive_with_no_key_and_lets_the_player_out(self):
        """Reachable without tricks: a push panel (Door_Open, playeruse) on
        the archive side, open for good, reached in the first round with no
        key and no switch; without the panel S1 is shut; from S1 there is a
        way back to the start and on to the exit."""
        m = self.m
        lines = self.s1_panel_lines()
        self.assertEqual(2, len(lines), "both faces of the panel")
        niche = self.plan["s1_niche"]
        fronts = {self.front(ld) for ld in lines}
        self.assertIn(niche, fronts, "pressed from the archive's side")
        for ld in lines:
            self.assertIn("sideback", ld)
            self.assertEqual(self.plan["s1_panel"], self.sides[ld["sideback"]]["sector"])
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            self.assertTrue(ld.get("secret"), "one-sided on the automap, as a secret door is")
        store = self.named(*m.SECRET_ZONES)
        first = self.progression()[0]
        self.assertTrue(store <= first[1], "S1 needs no key and no switch")
        self.assertEqual(set(), set(first[2]) & {m.LOCK_RED_CARD})
        shut = set().union(*(r[0] for r in self.progression(kills=True))) - {m.TAG_S1_PANEL}
        self.assertFalse(store & self.reachable(shut), "S1 is entered by its panel only")
        adj = self.adjacency(first[0])
        for zone in m.SECRET_ZONES:
            self.assertIn(self.start, self.flood(adj, self.plan[zone]), f"a way back from {zone}")

    def test_s1s_clue_is_the_locker_in_shadow(self):
        """MAP01's rule, a comparison and never a sign: four lockers fill the
        archive's east wall, and the one that is the panel stands 16 back,
        darker than the other three. Each locker one whole tile."""
        m = self.m
        archive = self.plan["o_archive"]
        x, y1, y2 = m.LOCKER_ROW
        row = self.one_sided_textures(archive)
        self.assertEqual(3 * m.LOCKER_WIDTH, row[m.LOCKER], "three lockers flush with the wall")
        self.assertEqual(4 * m.LOCKER_WIDTH, y2 - y1, "four lockers fill the wall")
        panel_faces = [ld for ld in self.s1_panel_lines() if self.front(ld) == self.plan["s1_niche"]]
        self.assertEqual(1, len(panel_faces))
        ld = panel_faces[0]
        self.assertEqual(m.LOCKER, self.sides[ld["sidefront"]]["texturetop"], "the fourth is the panel")
        (ax, ay), (bx, by) = self.line_points(ld)
        self.assertEqual(x + m.NICHE_DEPTH, ax)
        self.assertEqual(m.LOCKER_WIDTH, abs(by - ay))
        niche, panel = self.sectors[self.plan["s1_niche"]], self.sectors[self.plan["s1_panel"]]
        self.assertEqual(DOOR_TILE, niche["heightceiling"] - panel["heightfloor"], "one locker high")
        self.assertLess(niche["lightlevel"], self.sectors[archive]["lightlevel"], "the one in shadow")
        self.assertEqual(self.sectors[archive]["heightfloor"], niche["heightfloor"])

    # --- v1.1 (D68): the molten channel ------------------------------------------
    def test_the_molten_channel_hurts(self):
        """D68 "que haga daño": UDMF zdoom `damageamount` every
        `damageinterval` tics, between Doom's nukage (5) and super
        hellslime (20) per 32 tics; no sector special for it."""
        m = self.m
        channel = self.sectors[self.plan["f_channel"]]
        self.assertEqual(m.MOLTEN, channel["texturefloor"])
        self.assertEqual(m.CHANNEL_DAMAGE, channel["damageamount"])
        self.assertEqual(m.CHANNEL_DAMAGE_INTERVAL, channel["damageinterval"])
        per_32_tics = channel["damageamount"] * 32 / channel["damageinterval"]
        self.assertGreaterEqual(per_32_tics, 5)
        self.assertLessEqual(per_32_tics, 20)
        self.assertFalse(channel.get("special"))

    def test_the_molten_channel_is_no_one_way_trap(self):
        """No wall in the channel: every line round it is two-sided onto the
        casting floor, a step up of 16 the player climbs back from anywhere;
        it is 64 across, so no point of it is over 32 from the edge; nothing
        to pick up or fight stands in it."""
        m = self.m
        channel = self.plan["f_channel"]
        around = [ld for ld in self.lines if channel in (self.front(ld),) or
                  ("sideback" in ld and self.sides[ld["sideback"]]["sector"] == channel)]
        self.assertTrue(around)
        width = {"x": set(), "y": set()}
        for ld in around:
            self.assertIn("sideback", ld, "a wall in the channel")
            self.assertFalse(ld.get("blocking"))
            (ax, ay), (bx, by) = self.line_points(ld)
            width["x"] |= {ax, bx}
            width["y"] |= {ay, by}
        self.assertEqual({self.plan["f_floor"]}, self.neighbours[channel])
        every = set().union(*(r[0] for r in self.progression(kills=True)))
        adj = self.adjacency(every)
        self.assertIn(self.plan["f_floor"], adj[channel], "out of the channel")
        self.assertIn(channel, adj[self.plan["f_floor"]])
        rise = self.sectors[self.plan["f_floor"]]["heightfloor"] - self.sectors[channel]["heightfloor"]
        self.assertLessEqual(rise, m.STEP)
        narrow = min(max(v) - min(v) for v in width.values())
        self.assertLessEqual(narrow / 2, 32, "the edge is never more than 32 away")
        self.assertFalse([t for t in self.things if self.sector_at(t["x"], t["y"]) == channel])
        self.assertIn(self.start, self.flood(adj, channel), "a way back from the channel")

    # --- v1.1 (D68): the General's death opens his stores ------------------------
    def test_the_general_carries_the_stores_special(self):
        """UDMF thing `special` + `arg0..`: Door_Open (11) on the stores' tag,
        at the doors' speed. Nothing else in the map carries that tag: no
        line, no other thing; it names one door sector, the stores'."""
        m = self.m
        g = self.things_of({m.ED_GENERAL})[0]
        self.assertEqual(SPECIAL_DOOR_OPEN, g.get("special"))
        self.assertEqual((m.TAG_GENERAL_STORES, 16, 0), (g["arg0"], g["arg1"], g["arg2"]))
        others = [t for t in self.things if t.get("special") and t is not g
                  and t["type"] not in m.PICKUP_EVENTS]     # V3 A2/A3: the keys' events
        self.assertFalse(others)
        self.assertFalse([ld for ld in self.lines if ld.get("special") and ld.get("arg0") == m.TAG_GENERAL_STORES])
        self.assertEqual(self.named("p_stores_door"), self.doors[m.TAG_GENERAL_STORES])
        tagged = {i for i, s in enumerate(self.sectors) if s.get("id") == m.TAG_GENERAL_STORES}
        self.assertEqual(self.named("p_stores_door"), tagged)
        used = {s.get("id") for i, s in enumerate(self.sectors) if i not in tagged}
        self.assertNotIn(m.TAG_GENERAL_STORES, used)

    def test_the_stores_open_only_after_his_death(self):
        """Played with the kill: the stores open in the round after the
        General can be reached, never before. Played without it: never."""
        m = self.m
        stores = self.plan["p_stores"]
        self.assertFalse([r for r in self.progression() if stores in r[1]], "open without his death")
        rounds = self.progression(kills=True)
        first = next(k for k, (opened, _r, _h) in enumerate(rounds) if m.TAG_GENERAL_STORES in opened)
        g = self.things_of({m.ED_GENERAL})[0]
        self.assertIn(self.sector_at(g["x"], g["y"]), rounds[first - 1][1], "he is met first")
        self.assertNotIn(stores, rounds[first - 1][1])
        self.assertIn(stores, rounds[first][1])
        # From the portal hall it is a steel shutter in a porch one tile high,
        # with nothing to press: no door that will not open (MAP01's lesson).
        face = [ld for ld in self.lines if "sideback" in ld
                and set(self._pair(ld)) == self.named("p_stores_porch", "p_stores_door")]
        self.assertEqual(1, len(face))
        self.assertFalse(face[0].get("special"))
        side = face[0]["sidefront"] if self.front(face[0]) == self.plan["p_stores_porch"] else face[0]["sideback"]
        self.assertEqual(m.STEEL, self.sides[side]["texturetop"])
        porch = self.sectors[self.plan["p_stores_porch"]]
        self.assertEqual(DOOR_TILE, porch["heightceiling"] - porch["heightfloor"])
        self.assertIn(self.plan["p_hall"], self.neighbours[self.plan["p_stores_porch"]])

    def test_the_exit_depends_on_sw_b_alone(self):
        """D68: nobody is locked in if the General lives. The drum's gate has
        one opener, SW-B in the booth; his special names another tag; and
        the critical route (nobody killed) reaches the exit the round SW-B
        opens the gate."""
        m = self.m
        openers = [ld for ld in self.lines if ld.get("special") and ld.get("arg0") == m.TAG_GATE]
        self.assertEqual(1, len(openers))
        self.assertEqual(self.plan["p_booth"], self.front(openers[0]))
        self.assertNotEqual(m.TAG_GATE, self.things_of({m.ED_GENERAL})[0]["arg0"])
        rounds = self.progression()
        exit_sector = self.front(self.exit_line())
        first = next(k for k, r in enumerate(rounds) if exit_sector in r[1])
        self.assertIn(m.TAG_GATE, rounds[first][0])
        self.assertNotIn(m.TAG_GATE, rounds[first - 1][0])
        self.assertNotIn(m.TAG_GENERAL_STORES, set().union(*(r[0] for r in rounds)))

    def test_the_stores_hold_health_ammunition_and_armour(self):
        """The reward, on every skill: health, ammunition and armour."""
        m = self.m
        stores = self.plan["p_stores"]
        for skill in SKILLS:
            kinds = {t["type"] for t in self.on(skill, self.things)
                     if self.sector_at(t["x"], t["y"]) == stores}
            self.assertTrue(kinds & {m.ED_MEDIKIT, m.ED_STIMPACK}, f"skill {skill}: health")
            self.assertTrue(kinds & {m.ED_SHELL_BOX, m.ED_ROCKET_BOX, m.ED_CLIP_BOX, m.ED_CELL},
                            f"skill {skill}: ammunition")
            self.assertTrue(kinds & {m.ED_GREEN_ARMOR, m.ED_BLUE_ARMOR, m.ED_ARMOR_BONUS},
                            f"skill {skill}: armour")
        self.assertFalse([t for t in self.monsters() if self.sector_at(t["x"], t["y"]) == stores])


class Map03PickupEventsTest(unittest.TestCase):
    """V3 A2 and A3 (design section 19) against docs/levels/PICKUP-EVENTS.md
    section 6: the yellow key opens the two office closets at the stair head,
    the red key brings the foundry's goods lift up with its crew (the map's
    set piece). Each event's thing, special and tag (R7, R8), never closing
    (R1), the route finished without them and not cut by them (R2, R3), far
    from the start (R5), in sight of where the key is taken (R4), and left
    by what it releases (R6)."""

    SAFE_START_DISTANCE = 768   # tests/test_safe_starts.py's

    @classmethod
    def setUpClass(cls):
        Map03Test.setUpClass()
        cls.t = Map03Test()
        cls.m, cls.plan, cls.sectors = cls.t.m, cls.t.plan, cls.t.sectors
        cls.lines, cls.things = cls.t.lines, cls.t.things

    def test_each_key_carries_its_event(self):
        m, t = self.m, self.t
        pe.assert_event(self, self.things, self.sectors, self.lines, m.ED_YELLOW_CARD,
                        m.YELLOW_EVENT, t.named(*m.EVENT_ZONES["office_closets"]))
        pe.assert_event(self, self.things, self.sectors, self.lines, m.ED_RED_CARD,
                        m.LIFT_EVENT, t.named(*m.EVENT_ZONES["goods_lift"]))
        self.assertEqual(pe.events.SPECIAL_DOOR_OPEN, m.YELLOW_EVENT.special)
        self.assertEqual((pe.events.SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE, m.TAG_EVENT_RED,
                          pe.events.MOVER_SPEED_NORMAL, m.LIFT_TRAVEL),
                         (m.LIFT_EVENT.special, *m.LIFT_EVENT.args))
        # The keys' events and the General's death: every thing special there is.
        self.assertEqual(len(m.PICKUP_EVENTS) + 1, len(pe.event_things(self.things)))

    def test_the_route_needs_no_event_and_no_event_cuts_it(self):
        """R2, R3: the exit with no event run and nobody killed (the
        critical route), and with the events run nothing reached is lost."""
        t = self.t
        without, with_events = t.progression(), t.progression(events=True)
        exit_sector = t.front(t.exit_line())
        self.assertIn(exit_sector, without[-1][1])
        self.assertIn(exit_sector, with_events[-1][1])
        self.assertLessEqual(without[-1][1], with_events[-1][1])
        for tag, _sector in t.event_spots():
            self.assertNotIn(tag, without[-1][0], "a line opens an event's tag")

    def test_the_office_closets_open_at_the_stair_head_in_front_of_the_key(self):
        """R4, R6: both panels are wall until the yellow key is taken, open
        onto the corridor with a body's headroom after it, hold a clerk each
        on skill 2, and the corridor in front of each is seen from the
        director's doorway, the way out with the key."""
        t, m = self.t, self.m
        without, with_events = t.progression()[-1][1], t.progression(events=True)[-1][1]
        doorway = t.plan["o_director_doorway"]
        eye_z = self.sectors[doorway]["heightfloor"] + VIEW_HEIGHT
        for name, ((x1, y1, x2, _y2), _room) in m.OFFICE_CLOSETS.items():
            panel = self.sectors[t.plan[f"{name}_door"]]
            self.assertEqual(panel["heightfloor"], panel["heightceiling"], name)
            self.assertIn(t.plan["o_corridor"], t.neighbours[t.plan[f"{name}_door"]], name)
            self.assertNotIn(t.plan[name], without, name)
            self.assertIn(t.plan[name], with_events, name)
            floor, ceiling = t.event_heights[t.plan[f"{name}_door"]]
            self.assertGreaterEqual(ceiling - floor, max(h for _r, h in t.body.values()), name)
            inside = [x for x in t.on(2, t.monsters()) if t.sector_at(x["x"], x["y"]) == t.plan[name]]
            self.assertTrue(inside, f"{name} is empty on skill 2")
            self.assertIsNone(t.blocked((2304, 1936, eye_z), ((x1 + x2) / 2, y1 + 40, eye_z)), name)

    def test_the_goods_lift_is_a_wall_until_the_red_key(self):
        """A3, before: the car's ceiling flush with the casting floor (no
        opening: the shaft's front is wall, no sight, no sound) and its floor
        LIFT_TRAVEL under it; it touches the casting floor only."""
        t, m = self.t, self.m
        car = self.sectors[t.plan["f_lift"]]
        foundry = self.sectors[t.plan["f_floor"]]
        self.assertEqual(foundry["heightfloor"], car["heightceiling"])
        self.assertEqual(foundry["heightfloor"] - m.LIFT_TRAVEL, car["heightfloor"])
        self.assertEqual({t.plan["f_floor"]}, t.neighbours[t.plan["f_lift"]])
        self.assertNotIn(t.plan["f_lift"], t.progression()[-1][1])
        crew = [x for x in t.monsters() if t.sector_at(x["x"], x["y"]) == t.plan["f_lift"]]
        self.assertTrue(crew)
        for x in crew:
            self.assertTrue(all(x[f"skill{s}"] for s in SKILLS), "the crew is the set piece's, on every skill")
            self.assertLessEqual(t.body[x["type"]][1], car["heightceiling"] - car["heightfloor"])

    def test_the_goods_lift_comes_up_level_with_the_casting_floor(self):
        """A3, after: floor and ceiling up LIFT_TRAVEL together, the car's
        floor level with the casting floor and a body's headroom over it, so
        the crew walks out and the player can walk in (R6); a dead end with
        no other way, so nothing is shut (R1)."""
        t = self.t
        floor, ceiling = t.event_heights[t.plan["f_lift"]]
        self.assertEqual(self.sectors[t.plan["f_floor"]]["heightfloor"], floor)
        self.assertGreaterEqual(ceiling - floor, max(h for _r, h in t.body.values()))
        self.assertIn(t.plan["f_lift"], t.progression(events=True)[-1][1])

    def test_the_goods_lift_is_seen_from_the_red_keys_pedestal(self):
        """R4: from the pedestal, where the red key is taken, the casting
        floor in front of the lift is in view (the lifting front with it)."""
        t, m = self.t, self.m
        pedestal = self.sectors[t.plan["f_pedestal"]]
        x1, y1, x2, _y2 = m.LIFT_CAR
        floor = self.sectors[t.plan["f_floor"]]["heightfloor"]
        self.assertIsNone(t.blocked((*m.RED_KEY_SPOT, pedestal["heightfloor"] + VIEW_HEIGHT),
                                    ((x1 + x2) / 2, y1 - 24, floor + VIEW_HEIGHT)))

    def test_events_keep_away_from_the_start(self):
        """R5: no event thing and no sector an event moves near the start."""
        sx, sy = self.m.PLAYER_START
        for x in pe.event_things(self.things):
            self.assertGreater(math.hypot(x["x"] - sx, x["y"] - sy), self.SAFE_START_DISTANCE, x)
        rects = [r for pair in self.m.OFFICE_CLOSETS.values() for r in pair] + [self.m.LIFT_CAR]
        for x1, y1, x2, y2 in rects:
            nx, ny = min(max(sx, x1), x2), min(max(sy, y1), y2)
            self.assertGreater(math.hypot(nx - sx, ny - sy), self.SAFE_START_DISTANCE)


if __name__ == "__main__":
    unittest.main()
