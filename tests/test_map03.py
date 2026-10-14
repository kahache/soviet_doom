"""MAP03 v0, the metro-bunker grey box (docs/levels/MAP03-metro.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map01.py and the MAP01 half of tests/test_udmf.py:

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

Run:  python3 -m unittest tests.test_map03 -v
"""

from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from collections import defaultdict
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
USE_RANGE = udmf_tests.USE_RANGE           # 64

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4    # ZDoom raises a door to lowest neighbour ceiling - 4
DOOR_TILE = 128                 # SDDOOR1 is 128x128
SIGHT_STEP = 4                  # sample spacing of a sight line, map units
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys

ASSETS = PROJECT_ROOT / "assets"


def _load_map03():
    path = PROJECT_ROOT / "src" / "maps" / "MAP03" / "map.py"
    spec = importlib.util.spec_from_file_location("sdmap_MAP03_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _packed(name: str) -> bool:
    return any(ASSETS.glob(f"textures/*/{name}.png")) or any(ASSETS.glob(f"flats/*/{name}.png"))


class Map03V0Test(unittest.TestCase):

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

    def reachable(self, open_tags):
        return self.flood(self.adjacency(open_tags), self.start)

    def key_sector(self):
        keys = [t for t in self.things if t["type"] in KEY_NUMBERS]
        self.assertEqual(1, len(keys), "one key in the map")
        return self.sector_at(keys[0]["x"], keys[0]["y"])

    def progression(self):
        """Play the map as a player can. Manual doors and push panels open
        whenever the player can stand at their line; then, one round at a
        time, every switch and locked door he can now reach and work (a
        locked door only once the key's sector is reachable). Returns one
        (open tags, reachable sectors, key held) per round."""
        uses = [ld for ld in self.lines if ld.get("playeruse") and ld.get("special") in
                (SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE, self.m.SPECIAL_DOOR_LOCKED_RAISE)]
        key = self.key_sector()
        opened, rounds = set(), []
        while True:
            reach = self.reachable(opened)
            held = key in reach
            free, gated = set(), set()
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

    # --- v0 scope -----------------------------------------------------------
    def test_v0_places_only_the_start_and_the_key(self):
        """v0 is geometry (design section 12): no monster, weapon or item yet,
        except what the route needs: the start and the pass."""
        self.assertEqual(sorted([1, self.m.ED_BLUE_CARD]), sorted(t["type"] for t in self.things))
        for t in self.things:
            for skill in range(1, 6):
                self.assertTrue(t[f"skill{skill}"], f"thing {t['type']} missing on skill {skill}")
            self.assertTrue(t["single"])

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.progression()[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         f"unexpected: {sorted(self.zone_of[i] for i in unreachable ^ self.props)}")

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
        the stairs at both platform ends are the way up."""
        adj = self.adjacency(set())
        track = self.plan["z5_track"]
        platform = self.plan["z4_platform_n"]
        self.assertIn(track, adj[platform])
        self.assertNotIn(platform, adj[track])
        for side in ("w", "e"):
            self.assertIn(self.plan[f"stair_{side}3"], adj[track])
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
        self.assertEqual(self.named("shutter"), self.doors[m.TAG_SHUTTER])
        self.assertEqual(self.named("gate", "cp_door"), self.doors[m.TAG_GATE])

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


if __name__ == "__main__":
    unittest.main()
