"""MAP03 v0, Tankograd, the tractor factory grey box (docs/levels/MAP03-factory.md).

Owner: `level-designer`. Read back from the generated TEXTMAP, in the style
of tests/test_map02_metro.py:

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

Run:  python3 -m unittest tests.test_map03_factory -v
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

SPECIAL_DOOR_OPEN = 11
SPECIAL_DOOR_RAISE = 12
SPECIAL_EXIT_NORMAL = 243
DOOR_OPENS_BELOW_CEILING = 4    # ZDoom raises a door to lowest neighbour ceiling - 4
DOOR_TILE = 128                 # SDDOOR1 is 128x128
SIGHT_STEP = 4                  # sample spacing of a sight line, map units
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys
KEY_SPRITE_MID = 8              # a keycard stands about 16 high: aim at its middle

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

    def progression(self):
        """Play the map as a player can. Manual doors open whenever the
        player can stand at their line; then, one round at a time, every
        switch and locked door he can now reach and work (a locked door only
        once the sector of ITS key is reachable). Returns one (open tags,
        reachable sectors, locks held) per round."""
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
        h = self.heights(set().union(*(r[0] for r in self.progression())))
        for a, dsts in self.adjacency(set().union(*(r[0] for r in self.progression()))).items():
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
            self.assertIn(s["textureceiling"], flats, f"sector {self.zone_of[i]}")
        for name in walls | flats:
            self.assertTrue(_packed(name), f"{name} is not in assets/")

    def test_every_door_leaf_is_one_tile(self):
        """Every SDDOOR1 face is 128 wide and hangs 128 from the ceiling of
        the room it faces to the door's floor (no tiling, MAP01 section 6)."""
        faces = 0
        for i, ld in enumerate(self.lines):
            if "sideback" not in ld:
                continue
            a, b = self._pair(ld)
            for room, door, side in ((a, b, ld["sidefront"]), (b, a, ld["sideback"])):
                if door not in self.door_sectors:
                    continue
                if self.sides[side].get("texturetop") != self.m.DOOR:
                    continue
                faces += 1
                (ax, ay), (bx, by) = self.line_points(ld)
                self.assertEqual(DOOR_TILE, abs(bx - ax) + abs(by - ay), f"linedef {i}")
                drop = self.sectors[room]["heightceiling"] - self.sectors[door]["heightfloor"]
                self.assertEqual(DOOR_TILE, drop, f"linedef {i}: leaf of {self.zone_of[door]}")
        self.assertEqual(10, faces, "five leafed doors, two faces each")

    def test_star_plaques_frame_both_locked_doors(self):
        m = self.m
        plaques = [ld for ld in self.lines if "sideback" not in ld
                   and self.sides[ld["sidefront"]].get("texturemiddle") == m.STAR]
        self.assertEqual(4, len(plaques))
        by_portal = defaultdict(int)
        for ld in plaques:
            portal = self.front(ld)
            by_portal[self.zone_of[portal]] += 1
            s = self.sectors[portal]
            self.assertEqual(m.PLAQUE, s["heightceiling"] - s["heightfloor"])
            (ax, ay), (bx, by) = self.line_points(ld)
            self.assertEqual(m.PLAQUE, abs(bx - ax) + abs(by - ay))
        self.assertEqual({"z3_red_portal": 2, "z3_yellow_portal": 2}, dict(by_portal))

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

    # --- v0 scope -----------------------------------------------------------
    def test_v0_places_only_the_start_and_the_two_keys(self):
        """v0 is geometry (design section 12, D60): no monster, weapon or
        item yet, except what the route needs."""
        m = self.m
        self.assertEqual(sorted([1, m.ED_YELLOW_CARD, m.ED_RED_CARD]),
                         sorted(t["type"] for t in self.things))
        for t in self.things:
            for skill in range(1, 6):
                self.assertTrue(t[f"skill{skill}"], f"thing {t['type']} missing on skill {skill}")
            self.assertTrue(t["single"])

    def test_v0_has_no_secret(self):
        self.assertFalse([i for i, s in enumerate(self.sectors) if s.get("special")])

    # --- reachability and no softlock --------------------------------------
    def test_everything_is_reachable_at_the_end(self):
        reach = self.progression()[-1][1]
        unreachable = set(range(len(self.sectors))) - reach
        self.assertEqual(self.props, unreachable,
                         f"unexpected: {sorted(self.zone_of[i] for i in unreachable ^ self.props)}")

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
        for opened, reach, _held in self.progression():
            back = self.flood(self.reverse(self.adjacency(opened)), self.start)
            stranded = sorted(self.zone_of[i] for i in reach - back)
            self.assertEqual([], stranded, f"with tags {sorted(opened)} open")

    def test_from_everywhere_the_exit_can_be_reached_at_the_end(self):
        opened, reach, _ = self.progression()[-1]
        exit_sector = self.front(self.exit_line())
        onward = self.flood(self.reverse(self.adjacency(opened)), exit_sector)
        self.assertEqual([], sorted(self.zone_of[i] for i in reach - onward))

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
        self.assertEqual({m.TAG_D1_PLANNING, m.TAG_D2_ARCHIVE}, set(o0))
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

    # --- the keys ------------------------------------------------------------
    def test_one_yellow_and_one_red_key_on_the_route_outside_any_secret(self):
        m = self.m
        types = sorted(t["type"] for t in self.key_things())
        self.assertEqual(sorted([m.ED_YELLOW_CARD, m.ED_RED_CARD]), types)
        sectors = {t["type"]: self.sector_at(t["x"], t["y"]) for t in self.key_things()}
        for ed, zone in m.KEY_ZONES.items():
            self.assertEqual(self.plan[zone], sectors[ed])
            self.assertFalse(self.sectors[sectors[ed]].get("special"))

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
        self.assertEqual(self.named("shutter"), self.doors[m.TAG_SHUTTER])
        self.assertEqual(self.named("gate"), self.doors[m.TAG_GATE])

    def test_sw_a_stands_beside_the_shutter_passage(self):
        sw_a = [ld for ld in self.switch_lines() if ld["arg0"] == self.m.TAG_SHUTTER][0]
        (ax, ay), (bx, by) = self.line_points(sw_a)
        middle = ((ax + bx) / 2, (ay + by) / 2)
        self.assertLessEqual(math.dist(middle, (1728, 688)), DOOR_TILE)

    def test_the_shutter_is_wall_from_the_hall(self):
        """No door leaf the player cannot open from where he stands."""
        hall_face = [ld for ld in self.lines if "sideback" in ld
                     and set(self._pair(ld)) == self.named("shutter", "z3_hall")]
        self.assertEqual(1, len(hall_face))
        ld = hall_face[0]
        side = ld["sidefront"] if self.front(ld) == self.plan["z3_hall"] else ld["sideback"]
        self.assertEqual(self.m.STRIPE, self.sides[side]["texturetop"])
        self.assertFalse(ld.get("special"))

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


if __name__ == "__main__":
    unittest.main()
