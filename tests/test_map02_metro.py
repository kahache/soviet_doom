"""MAP02, the metro-bunker, v0 and v1 (docs/levels/MAP02-metro.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map01.py and the MAP01 half of tests/test_udmf.py. v0's
contract (design section 14):

* structure: every sector closed and clockwise, no duplicate vertex;
* only approved, packed textures; the Stalin poster's slot ready for a
  128x256 picture;
* everything is reachable, and the exit is reached, playing the map's own
  doors, switches and its one key in order (the progression model);
* no trap: from every place the player can reach at any stage there is a way
  back to the start, and at the end a way on to the exit;
* the key grammar: the blue door is seen before the pass is found, the pass
  is reachable without the door, the door opens for good;
* the switches are real switch faces, one-shot, each beside or in sight of
  what it opens; doors one tile high; the two secrets flagged and left again.

v1 (design section 16), after the CEO's v0 walk (D58: the pass not found):

* the pass alone in the duty officer's booth, a lit niche whose window on
  the hall is seen from the blue door, the hall and the window itself, and
  which can be looked through but not climbed or reached through;
* 192 and the blue light kept for the lock and the key;
* the yellow lane from both staff stairs along the track to D3, the light
  rising from the tunnel to D3, and D3 seen down the lane;
* the population of section 9: monsters per skill and nested, the
  bestiary's own MAPINFO numbers, the Legion in the station and the Reich in
  the depths, the closets on the switches' tags, the weapons on the route,
  consumables scaled down, and G3-8's ammunition margin on every skill;
* D119: ammunition scaled up with the monsters and fewer pickups of it,
  every skill inside its G3-8 band, shells no more than 35 % of the damage
  placed, and every weapon stretch paid for.

Run:  python3 -m unittest tests.test_map02_metro -v
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
USE_RANGE = udmf_tests.USE_RANGE           # 64

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4    # ZDoom raises a door to lowest neighbour ceiling - 4
DOOR_TILE = 128                 # SDDOOR1 is 128x128
SIGHT_STEP = 4                  # sample spacing of a sight line, map units
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys

ASSETS = PROJECT_ROOT / "assets"
MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
MONSTER_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters"
PLAYER_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "player.zs"

PLAYER_RADIUS = 16
PICKUP_RADIUS = 20     # Doom's pickups, the pass among them, are 20 wide
SKILLS = (2, 3, 4)
DOOM_MONSTERS = {3004, 9, 3001, 3002, 3005, 69, 3003, 16, 7, 65, 64, 66, 67, 68, 71, 84, 58, 3006}
# The class file of each bestiary class: its RADIUS, HEIGHT and HEALTH
# constants are read from it (BESTIARY: "the code is the truth").
CLASS_FILES = {
    "SD_ReichRifleman": "reich_rifleman.zs",
    "SD_LegionTrooper": "legion_trooper.zs",
    "SD_Stormtrooper": "stormtrooper.zs",
    "SD_ReichHound": "reich_hound.zs",
    "SD_Doughboy": "doughboy.zs",
    "SD_Panzermensch": "panzermensch.zs",
}
# Criterion G3-8 as MAP01 measures it (tests/test_map01.py, design section 11
# there): what each kill costs in IZh shells and what placed
# ammunition is worth in shell-equivalents (10 rounds of 7.62 = 1 shell).
SHELLS_TO_KILL = {"SD_ReichRifleman": 1, "SD_LegionTrooper": 1, "SD_Stormtrooper": 2,
                  "SD_ReichHound": 3, "SD_Doughboy": 6, "SD_Panzermensch": 8}
ROUNDS_PER_SHELL = 10
SHELLS_GIVEN = {2008: 4, 2049: 20, 21003: 8}
ROUNDS_GIVEN = {2007: 10, 2048: 50, 21004: 35}
IZH_AVERAGE = 80       # docs/engine/BALANCE.md 2: one barrel
PPSH_AVERAGE = 8       # one round
# D119 (docs/engine/BALANCE.md): a G3-8 band per skill, shells no more than
# SHELL_SHARE_MAX of the damage placed, and fewer ammunition pickups than v1
# placed outside the secrets. The PG-7V count now, as on MAP03 (a direct hit
# averages 135, about two shells): D119's share is of all the damage placed.
G3_8_BAND = {2: (1.5, 2.0), 3: (1.3, 1.6), 4: (1.2, 1.45)}
SHELL_SHARE_MAX = 0.35
# The command post, where the Panzermensch at the console stands on every
# skill: the map's mini-boss stage for BALANCE 8.4.
MINI_BOSS_ZONE = "b4_cp"
NEWEST_SHARE_MIN = 0.4    # BALANCE 8.4
ROCKET_SHARE_MAX = 0.3    # BALANCE 8.4, the PM's amendment: outside a boss's stage
FUEL_SHARE_MAX = 0.15     # ...and fuel at most 15 % of the map's ammunition
# D119's shell share (BALANCE 8.3): (placed shells + what the Legion's
# dropped IZhs carry) over (placed shell-equivalents + every drop), drops in
# shell-equivalents: a trooper's IZh 2 shells, a rifleman's clip 5 rounds.
DROP_SHELLS = 2
DROP_ROUNDS = 5
V1_AMMO_PICKUPS = {2: 34, 3: 28, 4: 24}
ROCKETS_GIVEN = {2010: 1, 2046: 5, 21005: 2}
SHELLS_PER_ROCKET = 2
RPG_AVERAGE = 135      # one PG-7V, direct hit only
# D119's stretches along the weapons, by the zones of the tables (design
# section 5): the TT-33 alone on the concourse, the IZh the newest from the
# kassa to the platforms, the PPSh-41 from the train to the bunker's
# dormitory, the RPG-7 from the armoury to the exit.
MAP02_STRETCHES = (
    ("the TT-33", {"z1_lift", "z2_concourse"}),
    ("the IZh", {"z2_kassa", "esc_6", "z3_hall", "z3_portal", "z4_platform_n",
                 "z4_platform_s"}),
    ("the PPSh-41", {"z6_train", "z6_cab_e", "rails_z7_tunnel_e", "z7_tunnel_e",
                     "rails_z5_track", "z5_track", "z8_substation", "sub_stair_1",
                     "closet_pw", "closet_pe", "b1_vestibule", "b2_spine", "b3_dorm"}),
    ("the RPG-7", {"b5_armoury", "b5_lamp", "closet_armoury", "b4_cp", "closet_t1",
                   "closet_t2", "z9_exit_tunnel", "rails_z9_exit_tunnel"}),
)


def _load_map02():
    path = PROJECT_ROOT / "src" / "maps" / "MAP02" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP02_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


class Map02Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map02()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        cls.start = cls.plan["z1_lift"]
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
        # V3 A2: what each pickup event does to the sectors it moves, and the
        # sector each event's thing lies in (the model fires it there).
        cls.events = tuple(cls.m.PICKUP_EVENTS.values())
        cls.event_heights = pe.heights_after(cls.events, cls.sectors, cls.lines, cls.sides)
        cls.monster_numbers = set(cls.m.MONSTER_CLASSES)
        cls.body, cls.hit_points = {}, {}
        for ednum, name in cls.m.MONSTER_CLASSES.items():
            text = (MONSTER_ZS / CLASS_FILES[name]).read_text(encoding="utf-8")
            const = {k: int(v) for k, v in
                     re.findall(r"const\s+SD_\w+?_(RADIUS|HEIGHT|HEALTH)\s*=\s*(\d+)", text)}
            cls.body[ednum] = (const["RADIUS"], const["HEIGHT"])
            cls.hit_points[ednum] = const["HEALTH"]

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
            ceiling = s["heightceiling"]
            floor = s["heightfloor"]
            if i in self.door_sectors and s["id"] in open_tags:
                ceiling = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[i])
                           - DOOR_OPENS_BELOW_CEILING)
            if i in self.event_heights and s["id"] in open_tags:
                floor, ceiling = self.event_heights[i]     # V3 A2: the event has run
            out.append((floor, ceiling))
        return out

    def event_spots(self):
        """[(tag, sector)] for every pickup event: where its thing lies."""
        by_type = {t["type"]: t for t in pe.event_things(self.things)}
        return [(event.tag, self.sector_at(by_type[ednum]["x"], by_type[ednum]["y"]))
                for ednum, event in self.m.PICKUP_EVENTS.items()]

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

    def reachable(self, open_tags):
        return self.flood(self.adjacency(open_tags), self.start)

    def key_sector(self):
        keys = [t for t in self.things if t["type"] in KEY_NUMBERS]
        self.assertEqual(1, len(keys), "one key in the map")
        return self.sector_at(keys[0]["x"], keys[0]["y"])

    def progression(self, events=False):
        """Play the map as a player can. Manual doors and push panels open
        whenever the player can stand at their line; then, one round at a
        time, every switch and locked door he can now reach and work (a
        locked door only once the key's sector is reachable). With `events`
        (V3 A2), a pickup event runs as soon as its thing's sector is
        reachable, as a manual door does; without it (the default) none
        runs: the critical route never relies on one (PICKUP-EVENTS R3).
        Returns one (open tags, reachable sectors, key held) per round."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        key = self.key_sector()
        spots = self.event_spots() if events else []
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = key in reach
            free, gated = {tag for tag, sector in spots if sector in reach}, set()
            for ld in uses:
                stand = {self.front(ld)}
                if "sideback" in ld:
                    stand.add(self.sides[ld["sideback"]]["sector"])
                if not stand & reach:
                    continue
                tag = ld["arg0"]
                if ld["special"] == self.m.SPECIAL_DOOR_LOCKED_RAISE:
                    if held:
                        gated.add(tag)
                elif "sideback" in ld:
                    free.add(tag)
                else:
                    gated.add(tag)           # a switch: one round per press
            if free - opened:
                opened |= free
                continue
            rounds.append((frozenset(opened), reach, held))
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

    def blocked(self, eye, target):
        """Sample the 3D segment; any sample in the void or outside its
        sector's floor..ceiling blocks the view (doors closed)."""
        (x0, y0, z0), (x1, y1, z1) = eye, target
        h = self.heights(set())
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
        """A zone painted over by a later one leaves a sector with no line."""
        loops = udmf_tests.sector_loops(self.blocks)
        for name, index in self.plan.items():
            self.assertTrue(loops.get(index), f"{name} was painted out of existence")

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
            self.assertIn(s["textureceiling"], flats, f"sector {self.zone_of[i]}")
        for name in walls | flats:
            self.assertTrue(_packed(name), f"{name} is not in assets/")

    def test_the_stalin_poster_slot_fits_the_poster_whole(self):
        """D55's poster is 128x256: its slot is one 128-long one-sided wall,
        256 from floor to ceiling, in the secret shelter's niche."""
        m = self.m
        slot = [ld for ld in self.lines if "sideback" not in ld
                and self.sides[ld["sidefront"]].get("texturemiddle") == m.STALIN_SLOT_TEXTURE
                and self.front(ld) == self.plan["s1_poster_niche"]]
        self.assertEqual(1, len(slot))
        (ax, ay), (bx, by) = self.line_points(slot[0])
        self.assertEqual(m.POSTER_WIDTH, abs(bx - ax) + abs(by - ay))
        s = self.sectors[self.plan["s1_poster_niche"]]
        self.assertEqual(m.POSTER_HEIGHT, s["heightceiling"] - s["heightfloor"])
        self.assertIn(self.plan["s1_shelter"], self.neighbours[self.plan["s1_poster_niche"]])

    def test_every_door_leaf_is_one_tile(self):
        """Every SDDOOR1 face is 128 wide and hangs 128 from the ceiling of
        the room it faces to the door's floor (no tiling, MAP01 section 6)."""
        for i, ld in enumerate(self.lines):
            if "sideback" not in ld:
                continue
            a, b = self._pair(ld)
            for room, door, side in ((a, b, ld["sidefront"]), (b, a, ld["sideback"])):
                if door not in self.door_sectors:
                    continue
                if self.sides[side].get("texturetop") != self.m.DOOR:
                    continue
                (ax, ay), (bx, by) = self.line_points(ld)
                self.assertEqual(DOOR_TILE, abs(bx - ax) + abs(by - ay), f"linedef {i}")
                drop = self.sectors[room]["heightceiling"] - self.sectors[door]["heightfloor"]
                self.assertEqual(DOOR_TILE, drop, f"linedef {i}: leaf of {self.zone_of[door]}")

    def test_the_mosaics_frame_the_blast_door(self):
        m = self.m
        mosaic = [ld for ld in self.lines if "sideback" not in ld
                  and self.sides[ld["sidefront"]].get("texturemiddle") == m.MOSAIC]
        self.assertEqual(2, len(mosaic))
        portal = self.sectors[self.plan["z3_portal"]]
        self.assertEqual(128, portal["heightceiling"] - portal["heightfloor"])
        for ld in mosaic:
            self.assertEqual(self.plan["z3_portal"], self.front(ld))
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(128, abs(by - ay))

    def test_the_platform_face_is_one_edge_tile(self):
        faces = [ld for ld in self.lines if self.sides[ld["sidefront"]].get("texturebottom") == self.m.EDGE]
        self.assertTrue(faces)
        for ld in faces:
            a, b = self._pair(ld)
            drop = abs(self.sectors[a]["heightfloor"] - self.sectors[b]["heightfloor"])
            self.assertEqual(64, drop)

    def test_every_light_is_in_range_and_every_lamp_one_step_up(self):
        m = self.m
        for i, s in enumerate(self.sectors):
            self.assertGreaterEqual(s["lightlevel"], m.LIGHT_MIN, self.zone_of[i])
            self.assertLessEqual(s["lightlevel"], m.LIGHT_MAX, self.zone_of[i])
        lamps = [n for n in self.plan if n.startswith("lamp_")]
        self.assertEqual(len(m.HALL_LAMPS), len(lamps))
        for name in lamps:
            s = self.sectors[self.plan[name]]
            self.assertEqual(m.CEIL_LAMP, s["textureceiling"])
            self.assertEqual(m.LIGHT_HALL + m.LAMP_STEP, s["lightlevel"])

    # --- what the route needs is on every skill ---------------------------
    def test_the_start_and_the_pass_are_on_every_skill(self):
        """v0 placed only these two; since v1 the map is populated, and these
        two still spawn on every skill and in single player."""
        for ednum in (self.m.ED_PLAYER1_START, self.m.ED_BLUE_CARD):
            found = [t for t in self.things if t["type"] == ednum]
            self.assertEqual(1, len(found), ednum)
            for skill in range(1, 6):
                self.assertTrue(found[0][f"skill{skill}"], f"thing {ednum} missing on skill {skill}")
            self.assertTrue(found[0]["single"])

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        """Every sector but the props, the pickup events run (the armoury's
        store opens only with its RPG-7's)."""
        reach = self.progression(events=True)[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        props = self.props - set(self.event_heights)   # the pass's window: a way once it sinks
        self.assertEqual(props, unreachable,
                         f"unexpected: {sorted(self.zone_of[i] for i in unreachable ^ props)}")

    def test_the_exit_is_reached_and_not_before_sw_b(self):
        rounds = self.progression()
        exit_sector = self.front(self.exit_line())
        self.assertEqual(self.plan["z9_exit_niche"], exit_sector)
        self.assertNotIn("sideback", self.exit_line())
        self.assertIn(exit_sector, rounds[-1][1], "the exit is never reached")
        before_sw_b = self.reachable(set().union(*(r[0] for r in rounds)) - {self.m.TAG_GATE})
        self.assertNotIn(exit_sector, before_sw_b, "the exit must need SW-B")
        niche = self.sectors[exit_sector]
        self.assertEqual(self.m.SWITCH_HEIGHT, niche["heightceiling"] - niche["heightfloor"])

    def test_no_trap_at_any_stage(self):
        """From every sector the player can reach at any stage of the map
        there is a way back to the start with what is open at that stage:
        no drop without a climb back, no door that shuts him in."""
        for opened, reach, _held in self.progression():
            adj = self.adjacency(opened)
            reverse = defaultdict(set)
            for src, dsts in adj.items():
                for dst in dsts:
                    reverse[dst].add(src)
            back = self.flood(reverse, self.start)
            stranded = sorted(self.zone_of[i] for i in reach - back)
            self.assertEqual([], stranded, f"with tags {sorted(opened)} open")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        opened, reach, _ = self.progression()[-1]
        adj = self.adjacency(opened)
        exit_sector = self.front(self.exit_line())
        reverse = defaultdict(set)
        for src, dsts in adj.items():
            for dst in dsts:
                reverse[dst].add(src)
        onward = self.flood(reverse, exit_sector)
        self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward))

    def test_the_track_is_left_by_the_staff_stairs(self):
        """The open track is 64 below the platform: dropping in is free, and
        the stairs at both platform ends are the way up. Since v1 the stairs'
        feet are on the lane, the walkway half of the track bed."""
        adj = self.adjacency(set())
        track = self.named("z5_track", "lane_track", "rails_z5_track")
        platform = self.plan["z4_platform_n"]
        self.assertTrue(track & adj[platform])
        for t in track:
            self.assertNotIn(platform, adj[t])
        for side in ("w", "e"):
            self.assertIn(self.plan[f"stair_{side}3"], adj[self.plan["lane_track"]])
            self.assertIn(platform, adj[self.plan[f"stair_{side}1"]])

    def test_the_route_is_the_designed_one(self):
        m = self.m
        rounds = self.progression()
        sealed = self.reachable(set())
        self.assertEqual({self.start}, sealed, "the lift is shut by D1")
        first_opened, first, held = rounds[0]
        self.assertTrue(held, "the pass is reached with no switch and no key")
        self.assertEqual({m.TAG_D1_LIFT, m.TAG_D2_KASSA, m.TAG_D3_SUBSTATION,
                          m.TAG_S1_SHELTER, m.TAG_S2_CAB}, set(first_opened))
        bunker = self.named("b1_vestibule", "b2_spine", "b3_dorm", "b4_cp", "b5_armoury")
        self.assertFalse(bunker & first, "the bunker is behind the blue door")
        self.assertIn(self.plan["z7_tunnel_w"], first, "the gate is walked up to early")
        self.assertNotIn(self.plan["z9_exit_niche"], first)
        # Round 2: SW-A (the shutter) and the blue door. Round 3: SW-B.
        self.assertEqual(3, len(rounds))
        self.assertEqual({m.TAG_SHUTTER, m.TAG_BLAST_DOOR, m.TAG_D4_BUNKER, m.TAG_D5_ARMOURY},
                         set(rounds[1][0] - first_opened))
        self.assertTrue(bunker <= rounds[1][1])
        self.assertEqual({m.TAG_GATE}, set(rounds[2][0] - rounds[1][0]))

    # --- the key -------------------------------------------------------------
    def test_one_blue_pass_outside_the_bunker_and_outside_a_secret(self):
        key = self.key_sector()
        self.assertEqual(self.plan[self.m.KEY_ZONE], key)
        keys = [t for t in self.things if t["type"] in KEY_NUMBERS]
        self.assertEqual(self.m.ED_BLUE_CARD, keys[0]["type"])
        self.assertNotIn(self.zone_of[key], self.m.SECRET_ZONES)
        self.assertFalse(self.sectors[key].get("special"))

    def test_the_blue_door_opens_with_the_pass_and_stays_open(self):
        m = self.m
        locked = [ld for ld in self.lines if ld.get("special") == m.SPECIAL_DOOR_LOCKED_RAISE]
        self.assertEqual(2, len(locked), "both faces")
        for ld in locked:
            self.assertIn("sideback", ld)
            self.assertTrue(ld.get("playeruse") and ld.get("repeatspecial"))
            self.assertEqual((m.TAG_BLAST_DOOR, 16, 0, m.LOCK_BLUE_CARD, 0),
                             tuple(ld[f"arg{i}"] for i in range(5)))
            a, b = self._pair(ld)
            self.assertIn(self.plan["blast_door"], (a, b))
            self.assertEqual(self.plan["blast_door"], self.sides[ld["sideback"]]["sector"],
                             "the door is the back side, so the face is pressed from the room")

    def test_the_blue_door_is_seen_from_the_top_of_the_escalator(self):
        """The key grammar: the locked door is seen before the pass is found,
        from the first place that overlooks the station."""
        top = self.sectors[self.plan["esc_10"]]
        eye = (3120, 896, top["heightfloor"] + VIEW_HEIGHT)
        for y in (848, 896, 944):
            for z in (16, 64, 112):
                self.assertIsNone(self.blocked(eye, (1281, y, z)), f"door point y {y} z {z}")
        self.assertIsNotNone(self.blocked(eye, (1200, 896, 64)), "the shut leaf hides the bunker")

    def test_the_gate_is_seen_from_the_track(self):
        track = self.sectors[self.plan["z5_track"]]
        eye = (1408, 1408, track["heightfloor"] + VIEW_HEIGHT)
        for y in (1376, 1408, 1440):
            for z in (-48, -16, 16):
                self.assertIsNone(self.blocked(eye, (833, y, z)), f"gate point y {y} z {z}")

    # --- switches --------------------------------------------------------------
    def switch_lines(self):
        return [ld for ld in self.lines if "sideback" not in ld
                and ld.get("special") == SPECIAL_DOOR_OPEN]

    def test_every_switch_is_a_real_face_drawn_once_and_one_shot(self):
        m = self.m
        switches = self.switch_lines()
        faces = [self.sides[ld["sidefront"]].get("texturemiddle") for ld in switches]
        self.assertEqual(2, len(switches))
        self.assertEqual(len(faces), len(set(faces)), "one variant per switch")
        for ld, face in zip(switches, faces):
            self.assertIn(face, m.SWITCH_FACES)
            self.assertTrue(_packed(face.replace("SDSW1", "SDSW2")), f"{face}'s ON twin")
            self.assertTrue(ld.get("playeruse"))
            self.assertFalse(ld.get("repeatspecial"), "a gate switch stays on")
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.SWITCH_WIDTH, abs(bx - ax) + abs(by - ay))
            s = self.sectors[self.front(ld)]
            self.assertEqual(m.SWITCH_HEIGHT, s["heightceiling"] - s["heightfloor"])

    def test_each_switch_opens_what_the_design_says(self):
        m = self.m
        found = {ld["arg0"]: self.front(ld) for ld in self.switch_lines()}
        self.assertEqual({m.TAG_SHUTTER: self.plan["z8_substation"],
                          m.TAG_GATE: self.plan["b4_cp"]}, found)
        # v1: each switch also opens its closets (one line, one special).
        self.assertEqual(self.named("shutter", "closet_pw_door", "closet_pe_door"),
                         self.doors[m.TAG_SHUTTER])
        self.assertEqual(self.named("gate", "cp_door", "closet_t1_door", "closet_t2_door"),
                         self.doors[m.TAG_GATE])

    def test_sw_b_stands_beside_the_door_it_opens(self):
        """MAP01's lesson (v1 walk): the press must show its effect. SW-B's
        line shares a corner with the command post's door onto the tunnel."""
        sw_b = [ld for ld in self.switch_lines() if ld["arg0"] == self.m.TAG_GATE][0]
        door_lines = [ld for ld in self.lines if "sideback" in ld
                      and self.plan["cp_door"] in self._pair(ld)
                      and self.plan["b4_cp"] in self._pair(ld)]
        self.assertEqual(1, len(door_lines))
        self.assertTrue({sw_b["v1"], sw_b["v2"]} & {door_lines[0]["v1"], door_lines[0]["v2"]})

    def test_sw_a_is_within_a_few_steps_of_the_shutter(self):
        sw_a = [ld for ld in self.switch_lines() if ld["arg0"] == self.m.TAG_SHUTTER][0]
        (ax, ay), (bx, by) = self.line_points(sw_a)
        middle = ((ax + bx) / 2, (ay + by) / 2)
        self.assertLessEqual(math.dist(middle, (2832, 1184)), 2 * DOOR_TILE)

    # --- doors -----------------------------------------------------------------
    def test_every_door_opens_tall_enough(self):
        for index in sorted(self.door_sectors):
            s = self.sectors[index]
            opened = (min(self.sectors[n]["heightceiling"] for n in self.neighbours[index])
                      - DOOR_OPENS_BELOW_CEILING)
            self.assertGreaterEqual(opened - s["heightfloor"], PLAYER_HEIGHT, self.zone_of[index])

    def test_no_press_can_consume_a_gate(self):
        """Manual doors and panels repeat; every one-shot line opens for good."""
        for i, ld in enumerate(self.lines):
            special = ld.get("special")
            if special not in (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE,
                               self.m.SPECIAL_DOOR_LOCKED_RAISE):
                continue
            if "sideback" in ld:
                self.assertTrue(ld.get("repeatspecial"), f"linedef {i}")
            else:
                self.assertEqual(SPECIAL_DOOR_OPEN, special, f"linedef {i}")

    # --- secrets ----------------------------------------------------------------
    def test_two_secrets_flagged_reachable_and_left_again(self):
        flagged = {i for i, s in enumerate(self.sectors)
                   if s.get("special") == self.m.SECTOR_SPECIAL_SECRET}
        self.assertEqual(self.named(*self.m.SECRET_ZONES), flagged)
        opened, reach, _ = self.progression()[0]
        self.assertTrue(flagged <= reach, "both secrets are open before any switch")
        adj = self.adjacency(opened)
        for secret in flagged:
            self.assertIn(self.start, self.flood(adj, secret), self.zone_of[secret])

    # =====================================================================
    # v1, the pass signposted (D58; design section 16.1)
    # =====================================================================
    def test_the_pass_lies_alone_in_the_lit_booth(self):
        m = self.m
        booth = self.plan["z8_booth"]
        self.assertEqual(booth, self.key_sector())
        s = self.sectors[booth]
        self.assertEqual(m.LIGHT_BEACON, s["lightlevel"])
        self.assertEqual(m.CEIL_PANEL, s["textureceiling"], "a lamp panel over the pass")
        inside = [t["type"] for t in self.things if self.sector_at(t["x"], t["y"]) == booth]
        self.assertEqual([m.ED_BLUE_CARD], inside, "the pass alone in its niche")
        # Two steps up from the substation, so the window's sill is its floor.
        step = self.sectors[self.plan["z8_booth_step"]]
        sub = self.sectors[self.plan["z8_substation"]]
        self.assertEqual(m.STEP, step["heightfloor"] - sub["heightfloor"])
        self.assertEqual(m.STEP, s["heightfloor"] - step["heightfloor"])
        self.assertIn(self.plan["z8_booth_step"], self.neighbours[booth])

    def test_192_is_kept_for_the_lock_and_the_key(self):
        """The two brightest places in the map are the blue door's portal and
        the booth (with its window): one says where to go, the other what to
        fetch first. Nothing else may compete with them."""
        brightest = {self.zone_of[i] for i, s in enumerate(self.sectors)
                     if s["lightlevel"] == self.m.LIGHT_MAX}
        self.assertEqual({"z3_portal", "z8_booth", "duty_window"}, brightest)

    def test_the_lock_and_the_key_share_the_blue_light(self):
        tinted = {self.zone_of[i]: s.get("lightcolor") for i, s in enumerate(self.sectors)
                  if "lightcolor" in s}
        self.assertEqual({"z3_portal": self.m.PASS_BLUE, "z8_booth": self.m.PASS_BLUE,
                          "duty_window": self.m.PASS_BLUE}, tinted)

    def pass_points(self):
        x, y = self.m.KEY_SPOT
        floor = self.sectors[self.plan["z8_booth"]]["heightfloor"]
        return [(x + dx, y + dy, floor + dz) for dx in (-8, 8) for dy in (-8, 8) for dz in (4, 12)]

    def test_the_pass_is_seen_from_the_blue_door(self):
        """D58's criterion: a player who reaches the blue door without the
        pass sees where it is. From in front of the door, turning round, the
        pass lies in plain view on the booth's floor at the hall's far end;
        and from the middle of the hall, and right at the window."""
        portal = self.sectors[self.plan["z3_portal"]]
        hall = self.sectors[self.plan["z3_hall"]]
        eyes = [(1312, y, portal["heightfloor"] + VIEW_HEIGHT) for y in (848, 896, 944)]
        eyes += [(2048, 1000, hall["heightfloor"] + VIEW_HEIGHT),
                 (2780, 1056, hall["heightfloor"] + VIEW_HEIGHT)]
        for eye in eyes:
            for target in self.pass_points():
                self.assertIsNone(self.blocked(eye, target), f"from {eye} to {target}")

    def test_the_window_is_seen_through_and_never_crossed(self):
        """Shorter than a player, so never walked or jumped through; the pass
        further from it than a player's radius plus a pickup's, so never
        taken through it. The way in is the track, the tunnel and D3."""
        m = self.m
        window = self.sectors[self.plan["duty_window"]]
        self.assertLess(window["heightceiling"] - window["heightfloor"], PLAYER_HEIGHT)
        self.assertGreater(window["heightfloor"] - self.sectors[self.plan["z3_hall"]]["heightfloor"],
                           MAX_STEP_UP)
        hall_face = m.DUTY_WINDOW[0]
        self.assertGreaterEqual(m.KEY_SPOT[0] - hall_face, PLAYER_RADIUS + PICKUP_RADIUS)
        # With every door but D3 open, the hall is reached and the booth is not.
        reach = self.reachable({m.TAG_D1_LIFT, m.TAG_D2_KASSA, m.TAG_S1_SHELTER, m.TAG_S2_CAB})
        self.assertIn(self.plan["z3_hall"], reach)
        self.assertNotIn(self.plan["z8_booth"], reach)

    def lane_sectors(self):
        return {i for i, s in enumerate(self.sectors) if s["texturefloor"] == self.m.LANE}

    def test_the_yellow_lane_runs_from_the_staff_stairs_to_d3(self):
        """MAP01's yellow means "go here". It comes down both staff stairs and
        runs along the walkway half of the track bed, into the east tunnel,
        and stops at D3. Every lane strip is 64 wide on the 64 grid and
        turned a quarter, so its line shows whichever way the turn goes."""
        m = self.m
        lane = self.lane_sectors()
        y1, y2 = m.LANE_Y
        self.assertEqual(64, y2 - y1)
        self.assertEqual(0, y1 % 64)
        for x in range(m.LANE_X[0] + 8, m.LANE_X[1], 16):
            for y in (y1 + 8, y2 - 8):
                self.assertIn(self.sector_at(x, y), lane, f"no lane at ({x}, {y})")
        for x in (m.LANE_X[0] - 8, m.LANE_X[1] + 8):
            self.assertNotIn(self.sector_at(x, y1 + 8), lane, f"lane beyond its ends at x {x}")
        for i in lane:
            self.assertEqual(90.0, float(self.sectors[i].get("rotationfloor", 0)), self.zone_of[i])
        for side in ("w", "e"):
            for n in (1, 2, 3):
                self.assertIn(self.plan[f"stair_{side}{n}"], lane)
            self.assertTrue(self.neighbours[self.plan[f"stair_{side}3"]] & lane,
                            f"the {side} stair's foot is off the lane")
        # It ends on D3: the sector in front of D3's tunnel face is lane.
        d3_faces = [ld for ld in self.lines if "sideback" in ld
                    and self.plan["d3"] in self._pair(ld)
                    and self.line_points(ld)[0][1] == y1]
        self.assertEqual(1, len(d3_faces))
        self.assertTrue(set(self._pair(d3_faces[0])) & lane)

    def test_light_leads_down_the_east_stair_to_d3_and_up_to_the_booth(self):
        """MAP01's other sign: light. The east staff stair (the way down
        towards the pass) is lit under a lamp; the lane ends in a pool of
        light at D3 in a dark tunnel; the light rises up the substation
        stair to the booth, the brightest thing there is."""
        m = self.m
        light = lambda name: self.sectors[self.plan[name]]["lightlevel"]
        for n in (1, 2, 3):
            self.assertGreater(light(f"stair_e{n}"), light("z4_platform_n"))
            self.assertEqual(m.CEIL_LAMP, self.sectors[self.plan[f"stair_e{n}"]]["textureceiling"])
            self.assertEqual(light("z4_platform_n"), light(f"stair_w{n}"))
        self.assertGreaterEqual(light("lane_d3") - light("z7_tunnel_e"), 4 * m.LAMP_STEP)
        self.assertEqual(m.CEIL_PANEL, self.sectors[self.plan["lane_d3"]]["textureceiling"])
        self.assertLess(light("z7_tunnel_e"), light("z8_substation"))
        self.assertLess(light("z8_substation"), light("z8_booth"))

    def test_d3_is_seen_down_the_lane_from_both_stair_feet(self):
        track = self.sectors[self.plan["lane_track"]]["heightfloor"]
        for eye_x in (1376, 2720):
            eye = (eye_x, 1376, track + VIEW_HEIGHT)
            for x in (2960, 3008, 3056):
                for dz in (16, 64, 112):
                    target = (x, 1345, track + dz)
                    self.assertIsNone(self.blocked(eye, target), f"from {eye} to {target}")

    # =====================================================================
    # v1, the population of section 9 (design section 16.4)
    # =====================================================================
    def things_of(self, numbers):
        return [t for t in self.things if t["type"] in numbers]

    @staticmethod
    def on(skill, things):
        return [t for t in things if t[f"skill{skill}"]]

    def monsters(self):
        return self.things_of(self.monster_numbers)

    def test_every_thing_stands_in_the_zone_its_table_names(self):
        rows = ([(z, k, x, y) for z, k, x, y, *_ in self.m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in self.m.ITEMS + self.m.AMMO])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is in {self.zone_of.get(self.sector_at(x, y))}")

    def test_the_monsters_are_the_bestiarys_own_numbers_in_mapinfo(self):
        """The PM's brief: MAPINFO's editor numbers. Every monster is one of
        21100-21105, each assigned in MAPINFO's DoomEdNums to the class this
        map means; no Doom monster number, no General, no heavy
        Panzermensch (both kept for the factory, design section 9)."""
        text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        block = re.search(r"DoomEdNums\s*\{(.*?)\}", text, re.S).group(1)
        assigned = {int(n): c for n, c in re.findall(r"(\d+)\s*=\s*(\w+)", block)}
        for ednum, name in self.m.MONSTER_CLASSES.items():
            self.assertEqual(name, assigned.get(ednum), ednum)
        for ednum in self.m.ROUTE_WEAPONS:
            self.assertIn(ednum, assigned)
        self.assertFalse(self.things_of(DOOM_MONSTERS))
        self.assertFalse(self.things_of({21106, 21107}))
        self.assertTrue(self.monsters())

    def test_every_monster_has_room_for_its_body(self):
        """All four corners of the body's box on floor it can stand on (not a
        prop, a window, a door or the void), within a step of each other,
        and the lowest ceiling over them at least the body's height above."""
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
        reach = self.progression(events=True)[-1][1]   # the store's box: the RPG-7's event
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
        """Section 9: 23 / 36 / 51. Whatever fights on an easier skill also
        fights on a harder one."""
        counts = {s: len(self.on(s, self.monsters())) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        for t in self.monsters():
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    def test_the_legion_holds_the_station_and_the_reich_the_depths(self):
        """D35, inverted from MAP01: the standing garrison of the station
        (concourse to train) is the Legion's, that of the depths (track,
        tunnels, substation, bunker, exit) the Reich's; stormtroopers are
        hybrids and stand anywhere. The closets are the counter-attack and
        are not a garrison."""
        m = self.m
        station = ("z2_", "esc_", "z3_", "arches_", "z4_", "z6_", "s2_")
        legion = set(m.LEGION)
        reich = set(m.REICH)
        seen = defaultdict(set)
        for zone, kind, *_ in m.MONSTERS:
            if zone.startswith(m.CLOSET_PREFIX):
                continue
            where = "station" if zone.startswith(station) else "depths"
            seen[where].add(kind)
            if where == "station":
                self.assertNotIn(kind, reich, f"{kind} in {zone}")
            else:
                self.assertNotIn(kind, legion, f"{kind} in {zone}")
        self.assertIn("trooper", seen["station"])
        self.assertIn("rifleman", seen["depths"])

    def test_the_heavies(self):
        """LORE: "first heavy hybrids". A Panzermensch at the command post on
        every skill (the first one an easy-skill player meets), a second in
        the exit tunnel on skill 4; one Doughboy, in the escalator shaft,
        from skill 3."""
        m = self.m
        pz = self.things_of({m.ED_PANZERMENSCH})
        self.assertEqual({2: 1, 3: 1, 4: 2}, {s: len(self.on(s, pz)) for s in SKILLS})
        every = [t for t in pz if t["skill2"]]
        self.assertEqual(self.plan["b4_cp"], self.sector_at(every[0]["x"], every[0]["y"]))
        db = self.things_of({m.ED_DOUGHBOY})
        self.assertEqual(1, len(db))
        self.assertFalse(db[0]["skill2"])
        self.assertTrue(self.zone_of[self.sector_at(db[0]["x"], db[0]["y"])].startswith("esc_"))

    def test_every_closet_holds_a_fight_and_opens_with_its_switch(self):
        """SW-A's closets on platform N, SW-B's in the west tunnel; each panel
        on its switch's tag, each closet occupied on skill 2, shut until its
        switch's round and open after it."""
        m = self.m
        closets = [n for n in self.plan if n.startswith(m.CLOSET_PREFIX) and not n.endswith("_door")
                   and n not in m.EVENT_CLOSETS]      # V3 A2's: Map02PickupEventsTest
        self.assertEqual(4, len(closets))
        rounds = self.progression()
        for name in closets:
            tag = self.sectors[self.plan[f"{name}_door"]]["id"]
            wanted = m.TAG_PLATFORM_AMBUSH if name.startswith("closet_p") else m.TAG_TUNNEL_WAVE
            self.assertEqual(wanted, tag, name)
            inside = [t for t in self.on(2, self.monsters())
                      if self.sector_at(t["x"], t["y"]) == self.plan[name]]
            self.assertTrue(inside, f"{name} is empty on skill 2")
            first = next(k for k, (opened, _r, _h) in enumerate(rounds) if tag in opened)
            self.assertNotIn(self.plan[name], rounds[first - 1][1], f"{name} open early")
            self.assertIn(self.plan[name], rounds[first][1], f"{name} never opens")
        self.assertEqual(m.TAG_SHUTTER, m.TAG_PLATFORM_AMBUSH)
        self.assertEqual(m.TAG_GATE, m.TAG_TUNNEL_WAVE)

    def test_the_weapons_are_on_every_skill_on_the_route(self):
        """Pistol start (+map MAP02 gives the TT-33 only): the IZh in the
        kassa and the PPSh in the train before any switch, the RPG-7 in the
        armoury before the command post's Panzermensch; none in a secret,
        each once, on every skill."""
        m = self.m
        rounds = self.progression()
        secret = {i for i, s in enumerate(self.sectors) if s.get("special", 0) & 1024}
        for ednum, zone, stage in ((m.ED_IZH, "z2_kassa", 0), (m.ED_PPSH, "z6_train", 0),
                                   (m.ED_RPG7, "b5_lamp", 1)):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            where = self.sector_at(t["x"], t["y"])
            self.assertEqual(self.plan[zone], where)
            self.assertNotIn(where, secret)
            self.assertIn(where, rounds[stage][1], f"weapon {ednum} not reached by round {stage}")
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}),
                         "a Doom weapon number: the arsenal is ours (D13)")

    def secret_sectors(self):
        return {i for i, s in enumerate(self.sectors) if s.get("special", 0) & 1024}

    def outside_secrets(self, things):
        secret = self.secret_sectors()
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in secret]

    def test_consumables_scale_down(self):
        """Monsters up, consumables down, weapons flat (MAP01 section 8)."""
        m = self.m
        fixed = self.monster_numbers | set(m.ROUTE_WEAPONS) | {m.ED_PLAYER1_START, m.ED_BLUE_CARD}
        for kind in {t["type"] for t in self.things} - fixed - self.ammo_kinds():
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def ammo_kinds(self):
        """The ammunition pickups (not the weapons that also give some)."""
        return (set(SHELLS_GIVEN) | set(ROUNDS_GIVEN) | set(ROCKETS_GIVEN)) - set(self.m.ROUTE_WEAPONS)

    def test_ammunition_scales_up_and_there_is_less_of_it(self):
        """D119: on the route, for every kind of ammunition, skill 2 has at
        most what skill 3 has and skill 3 at most what skill 4 has; and every
        skill has fewer ammunition pickups than v1 placed."""
        route = self.outside_secrets(self.things)
        for kind in self.ammo_kinds():
            n = {s: len(self.on(s, [t for t in route if t["type"] == kind])) for s in SKILLS}
            self.assertLessEqual(n[2], n[3], kind)
            self.assertLessEqual(n[3], n[4], kind)
        for skill in SKILLS:
            n = len([t for t in self.on(skill, route) if t["type"] in self.ammo_kinds()])
            self.assertLess(n, V1_AMMO_PICKUPS[skill], f"skill {skill}")

    def ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[self.m.MONSTER_CLASSES[t["type"]]]
                   for t in self.on(skill, self.monsters()))

    def ammo_placed(self, skill):
        placed = self.outside_secrets(self.on(skill, self.things))
        shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed)
        rounds = sum(ROUNDS_GIVEN.get(t["type"], 0) for t in placed)
        rockets = sum(ROCKETS_GIVEN.get(t["type"], 0) for t in placed)
        return shells + rounds / ROUNDS_PER_SHELL + rockets * SHELLS_PER_ROCKET

    def test_g3_8_the_ammo_budget(self):
        """G3-8 as D119 reads it: on every skill, ammunition placed outside
        the secrets is inside that skill's band of what killing every
        monster with the intended weapon takes, and shells are no more than
        35 % of it, the troopers' dropped IZhs counted there (BALANCE 8.3)
        and nowhere else."""
        for skill in SKILLS:
            need, have = self.ammo_needed(skill), self.ammo_placed(skill)
            low, high = G3_8_BAND[skill]
            self.assertGreaterEqual(have, low * need, f"skill {skill}: {have} for {need}")
            self.assertLessEqual(have, high * need, f"skill {skill}: {have} for {need}")
            placed = self.outside_secrets(self.on(skill, self.things))
            shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed)
            kinds = Counter(self.m.MONSTER_CLASSES[t["type"]] for t in self.on(skill, self.monsters()))
            troopers, riflemen = kinds["SD_LegionTrooper"], kinds["SD_ReichRifleman"]
            dropped = troopers * DROP_SHELLS + riflemen * DROP_ROUNDS / ROUNDS_PER_SHELL
            self.assertLessEqual(shells + troopers * DROP_SHELLS, SHELL_SHARE_MAX * (have + dropped),
                                 f"skill {skill}: {shells} shells placed")

    def test_the_newest_weapons_pool_leads_every_stage(self):
        """BALANCE 8.4 (D119, with the PM's amendment), stage by stage of the
        readiness check: a pool lies only from the stage where its weapon is
        (the TT-33's rounds from the start); of each stage's ammunition other
        than shells the leading pool is the largest share and at least 40 %
        of it. The leader is the newest weapon's pool, the IZh excepted
        (shells have 8.3) and the ROKS-3 excepted (fuel stays moderate, at
        most 15 % of the map's ammunition: the weapon before it leads); and
        outside the command post's stage (its Panzermensch,
        on every skill, is the map's heavy set piece: a mini-boss) the PG-7V are at most 30 % of the stage
        and the newest bullet weapon's rounds lead."""
        m = self.m
        pool_of = {m.ED_IZH: "shells", m.ED_PPSH: "rounds", m.ED_RPG7: "rockets"}
        pools = {"shells": SHELLS_GIVEN, "rounds": ROUNDS_GIVEN, "rockets": ROCKETS_GIVEN, "fuel": {}}
        weight = {"shells": 1, "rounds": 1 / ROUNDS_PER_SHELL, "rockets": SHELLS_PER_ROCKET, "fuel": 0}
        for skill in SKILLS:
            route = self.outside_secrets(self.on(skill, self.things))
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
                boss = self.plan[MINI_BOSS_ZONE] in reach - seen
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
                seen = reach

    def test_every_weapon_stretch_is_paid_for(self):
        """D119, stretch by stretch along the weapons: the damage placed so
        far outside the secrets plus the starting rounds is at least the
        skill's band floor times the hit points met so far, and the TT-33's
        stretch holds no shells. Counted from the tables, which the zone
        test pins to the TEXTMAP."""
        m = self.m
        rows = [(z, e, lo) for z, e, _x, _y, lo in m.AMMO]
        rows += [(z, e, 2) for z, e, _x, _y, _top in m.ITEMS
                 if e in m.ROUTE_WEAPONS or e == m.ED_ROCKET_BOX]
        for skill in SKILLS:
            hp, damage = 0, self.start_rounds() * PPSH_AVERAGE
            for name, zones in MAP02_STRETCHES:
                hp += sum(self.hit_points[m.MONSTER_KINDS[k]]
                          for z, k, _x, _y, _a, lo in m.MONSTERS if z in zones and lo <= skill)
                here = [e for z, e, lo in rows if z in zones and lo <= skill]
                damage += sum(SHELLS_GIVEN.get(e, 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(e, 0) * PPSH_AVERAGE
                              + ROCKETS_GIVEN.get(e, 0) * RPG_AVERAGE for e in here)
                self.assertGreaterEqual(damage, G3_8_BAND[skill][0] * hp, f"skill {skill}, {name}")
                if name == "the TT-33":
                    self.assertFalse([e for e in here if e in SHELLS_GIVEN], name)
        every = set().union(*(zones for _n, zones in MAP02_STRETCHES))
        self.assertFalse({z for z, *_ in m.MONSTERS} - every)
        self.assertFalse({z for z, *_ in m.AMMO} - every)

    def start_rounds(self):
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        """MAP01's G3 readiness check: at every stage of the route the damage
        placed so far outside the secrets, plus the starting rounds, is at
        least the floor of the skill's G3-8 band (D119) times the hit points
        met so far, the PG-7V counted."""
        secret = self.secret_sectors()
        rounds = self.progression()
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage = self.start_rounds() * PPSH_AVERAGE
            for stage, (_opened, reach, _held) in enumerate(rounds):
                here = [t for t in self.on(skill, self.things)
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                hp_so_far += sum(self.hit_points.get(t["type"], 0) for t in here)
                damage += sum(SHELLS_GIVEN.get(t["type"], 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(t["type"], 0) * PPSH_AVERAGE
                              + ROCKETS_GIVEN.get(t["type"], 0) * RPG_AVERAGE
                              for t in here if self.sector_at(t["x"], t["y"]) not in secret)
                self.assertGreaterEqual(damage, G3_8_BAND[skill][0] * hp_so_far,
                                        f"skill {skill}, stage {stage}")
                seen = reach

    def test_health_and_armour_outside_the_secrets_on_skill_4(self):
        m = self.m
        found = Counter(t["type"] for t in self.outside_secrets(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 6)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)
        self.assertEqual(1, found[m.ED_GREEN_ARMOR])


class Map02PickupEventsTest(unittest.TestCase):
    """V3 A2 (design section 18) against docs/levels/PICKUP-EVENTS.md section
    6: the pass sinks the duty window's sill, a way back into the hall; the
    RPG-7 opens the armoury's store and brings its lights up. Each event's
    thing, special and tag (R7, R8), never closing (R1), the route finished
    without them and not cut by them (R2, R3), far from the start (R5),
    announced (R4) and left by what it releases (R6)."""

    SAFE_START_DISTANCE = 768   # tests/test_safe_starts.py's

    @classmethod
    def setUpClass(cls):
        Map02Test.setUpClass()
        cls.t = Map02Test()
        cls.m, cls.plan, cls.sectors = cls.t.m, cls.t.plan, cls.t.sectors
        cls.lines, cls.things = cls.t.lines, cls.t.things

    def test_each_event_rides_its_item(self):
        m = self.m
        pe.assert_event(self, self.things, self.sectors, self.lines, m.ED_BLUE_CARD, m.PASS_EVENT,
                        {self.plan["duty_window"]})
        pe.assert_event(self, self.things, self.sectors, self.lines, m.ED_RPG7, m.RPG_EVENT,
                        {self.plan["closet_armoury_door"]})
        self.assertEqual(len(m.PICKUP_EVENTS), len(pe.event_things(self.things)))
        self.assertEqual(pe.events.SPECIAL_DOOR_OPEN, m.PASS_EVENT.special)
        self.assertEqual(pe.events.SPECIAL_DOOR_OPEN, m.RPG_EVENT.special)

    def test_the_pass_opens_the_window_a_way_out_not_in(self):
        """After the pass: the window's head has risen to a doorway's (the
        booth's ceiling less 4) over the booth's own floor, so the booth
        drops into the hall; from the hall the booth is still more than a
        step up, so the way in stays the track and D3."""
        t, m = self.t, self.m
        floor, ceiling = t.event_heights[self.plan["duty_window"]]
        booth = self.sectors[self.plan["z8_booth"]]
        self.assertEqual(booth["heightfloor"], floor)
        self.assertEqual(booth["heightceiling"] - pe.DOOR_OPENS_BELOW_CEILING, ceiling)
        self.assertGreaterEqual(ceiling - floor, PLAYER_HEIGHT)
        hall = self.sectors[self.plan["z3_hall"]]["heightfloor"]
        self.assertGreater(floor - hall, MAX_STEP_UP)
        adj = t.adjacency({m.TAG_EVENT_PASS})
        window, hall, booth_s = self.plan["duty_window"], self.plan["z3_hall"], self.plan["z8_booth"]
        self.assertIn(window, adj[booth_s])
        self.assertIn(hall, adj[window])
        self.assertNotIn(window, adj[hall], "a way into the booth from the hall")
        doors = {m.TAG_D1_LIFT, m.TAG_D2_KASSA, m.TAG_S1_SHELTER, m.TAG_S2_CAB, m.TAG_EVENT_PASS}
        self.assertNotIn(booth_s, t.reachable(doors), "the window lets the player in")

    def test_the_route_needs_no_event_and_no_event_cuts_it(self):
        """R2, R3: the exit with no event run (every other test of the map
        plays it so), and with both run nothing reached before is lost."""
        without, with_events = self.t.progression(), self.t.progression(events=True)
        exit_sector = self.t.front(self.t.exit_line())
        self.assertIn(exit_sector, without[-1][1])
        self.assertIn(exit_sector, with_events[-1][1])
        self.assertLessEqual(without[-1][1], with_events[-1][1])
        for tag, _sector in self.t.event_spots():
            self.assertNotIn(tag, without[-1][0], "a line opens an event's tag")

    def test_the_store_is_shut_until_the_rpg_and_left_after_it(self):
        """R6: the store's panel is wall until the RPG-7 is taken; then it
        joins the armoury with a body's headroom, guards in it on skill 2."""
        t, m = self.t, self.m
        panel = self.sectors[self.plan["closet_armoury_door"]]
        self.assertEqual(panel["heightfloor"], panel["heightceiling"])
        store = self.plan["closet_armoury"]
        self.assertNotIn(store, t.progression()[-1][1])
        self.assertIn(store, t.progression(events=True)[-1][1])
        floor, ceiling = t.event_heights[self.plan["closet_armoury_door"]]
        self.assertGreaterEqual(ceiling - floor, max(h for _r, h in t.body.values()))
        guards = [x for x in t.on(2, t.monsters()) if t.sector_at(x["x"], x["y"]) == store]
        self.assertTrue(guards)

    def test_the_armoury_comes_up_to_its_lamp_as_the_store_opens(self):
        """Door_Open's light tag: each tagged sector goes to its brightest
        neighbour. Tagged is the armoury alone, dark, and its brightest
        neighbour is the lamp the RPG-7 lies under."""
        t, m = self.t, self.m
        lit = pe.tagged(self.sectors, m.TAG_EVENT_RPG_LIGHTS)
        self.assertEqual({self.plan["b5_armoury"]}, lit)
        armoury = self.sectors[self.plan["b5_armoury"]]
        brightest = max(self.sectors[n]["lightlevel"] for n in t.neighbours[self.plan["b5_armoury"]])
        self.assertEqual(m.LIGHT_ARMOURY_LAMP, brightest)
        self.assertEqual(m.LIGHT_ARMOURY_LAMP, self.sectors[self.plan["b5_lamp"]]["lightlevel"])
        self.assertLess(armoury["lightlevel"], brightest)
        rpg = t.things_of({m.ED_RPG7})[0]
        self.assertEqual(self.plan["b5_lamp"], t.sector_at(rpg["x"], rpg["y"]))
        self.assertEqual(m.TAG_EVENT_RPG_LIGHTS, m.RPG_EVENT.args[2])

    def test_the_store_opens_in_sight_of_the_launcher(self):
        """R4: from the RPG-7's place, the floor in front of the store's
        panel is in view (the guards are seen as they come out)."""
        t, m = self.t, self.m
        rpg = t.things_of({m.ED_RPG7})[0]
        (x1, y1, x2, _y2), _store = m.CLOSET_ARMOURY
        floor = self.sectors[self.plan["b5_armoury"]]["heightfloor"]
        self.assertIsNone(t.blocked((rpg["x"], rpg["y"], floor + VIEW_HEIGHT),
                                    ((x1 + x2) / 2, y1 - 24, floor + VIEW_HEIGHT)))

    def test_events_keep_away_from_the_start(self):
        """R5: no event thing and no sector an event moves near the start."""
        sx, sy = self.m.PLAYER_START
        for x in pe.event_things(self.things):
            self.assertGreater(math.hypot(x["x"] - sx, x["y"] - sy), self.SAFE_START_DISTANCE, x)
        for rect in (self.m.DUTY_WINDOW, *self.m.CLOSET_ARMOURY):
            x1, y1, x2, y2 = rect
            nx, ny = min(max(sx, x1), x2), min(max(sy, y1), y2)
            self.assertGreater(math.hypot(nx - sx, ny - sy), self.SAFE_START_DISTANCE, rect)


if __name__ == "__main__":
    unittest.main()
