"""`dam-critical`, MAP05's automatic route (tools/route.py), checked on the
built map without the engine (D26): the PM runs it in the engine.

Owner: `level-designer`. What it holds: the route finds MAP05 by its own
constants, walks the design's order (both locks shut without keys, the
yellow key, the yellow door, SW-A, the blue key, SW-B, the blue gate, D2,
the exit switch), presses each line from the room the design presses it
from, walks onto each key without `give`, and its last walk goes from D2
straight to the exit switch on one line through the open door.

Run:  python3 -m unittest tests.test_map05_route -v
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import route  # noqa: E402

PLAYER_RADIUS = 16
PICKUP_RADIUS = 20
USE_RANGE = 64
SAMPLE = 4


class DamRouteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.map_name = route.map_defining(*route.DAM_CONSTANTS)
        cls.md = route.load_map_data(cls.map_name)
        cls.m = cls.md.module
        cls.r = route.dam_critical(cls.md)
        cls.steps = {s.id: s for s in cls.r.steps}

    def family(self, point):
        return route.zone_family(self.md.name_of(self.md.sector_at(*point)))

    def test_the_route_is_registered_and_finds_the_dam(self):
        self.assertEqual("MAP05", self.map_name)
        self.assertIn("dam-critical", route.route_names())
        self.assertEqual("dam-critical", self.r.name)
        self.assertEqual(self.map_name, self.r.map_name)

    def test_it_plays_the_designs_order(self):
        self.assertEqual(["A0", "BG0", "YD0", "YKEY", "YD1", "SWA", "BKEY", "SWB", "BG1", "E0", "E1"],
                         [s.id for s in self.r.steps])
        self.assertEqual([0, 0, 0, 1, None, None, 2, None, None, None, None],
                         [s.keys for s in self.r.steps])

    def test_its_exit_leads_to_mapinfos_next_by_a_switch(self):
        self.assertEqual(route.exit_expectation(self.map_name)["next_map"], self.r.next_map)
        self.assertFalse(self.r.end_sequence)
        self.assertEqual(("switch", True, 0), (self.r.exit_by, self.r.must_exit, self.r.expect_secrets))
        self.assertEqual(("use",), self.r.steps[-1].actions)

    def test_each_press_is_made_from_the_room_the_design_names(self):
        m = self.m
        want = {"BG0": ("Z1", m.TAG_BLUE_GATE), "BG1": ("Z1", m.TAG_BLUE_GATE),
                "YD0": ("Z5", m.TAG_YELLOW_DOOR), "YD1": ("Z5", m.TAG_YELLOW_DOOR),
                "SWA": ("Z6", m.TAG_CABLE_SHUTTER), "SWB": ("Z9", m.TAG_STATION_SHUTTER),
                "E0": ("Z10", m.TAG_D2_WEST)}
        for sid, (family, tag) in want.items():
            step = self.steps[sid]
            self.assertEqual(family, self.family(step.warp), sid)
            self.assertEqual(tag, step.presses[0][1], sid)
            self.assertIn("use", step.actions, sid)

    def test_each_press_reaches_its_line(self):
        """The warp stands within Doom's use range of the pressed line's
        middle, facing it."""
        tm = self.md.textmap
        for sid in ("BG0", "YD0", "SWA", "SWB", "E0"):
            step = self.steps[sid]
            special, tag = step.presses[0]
            lines = [ld for ld in tm.linedefs if ld.special == special and ld.arg0 == tag]
            middles = []
            for ld in lines:
                (x1, y1), (x2, y2) = route.line_ends(self.md, ld)
                middles.append(((x1 + x2) / 2, (y1 + y2) / 2))
            middle = min(middles, key=lambda p: math.dist(step.warp, p))   # the face before him
            self.assertLess(math.dist(step.warp, middle), USE_RANGE, sid)
            dx, dy = route.COMPASS[step.angle]
            ahead = (step.warp[0] + dx * route.USE_DISTANCE, step.warp[1] + dy * route.USE_DISTANCE)
            self.assertLess(math.dist(ahead, middle), 1, f"{sid} faces its line")

    def test_the_doors_lead_where_the_design_says(self):
        self.assertEqual("Z6", self.steps["YD1"].expect[0], "the yellow door into the control room")
        self.assertEqual("Z10", self.steps["BG1"].expect[0], "the blue gate onto the crest")
        self.assertEqual("Z11", self.steps["E0"].expect[0], "D2 into the west bank's hall")

    def test_the_keys_are_walked_onto_never_given(self):
        m = self.m
        for sid, spot, family in (("YKEY", m.YELLOW_KEY_SPOT, "Z7"), ("BKEY", m.BLUE_KEY_SPOT, "Z9")):
            step = self.steps[sid]
            self.assertEqual(family, self.family(step.warp), sid)
            gap = math.dist(step.warp, spot)
            self.assertGreater(gap, PLAYER_RADIUS + PICKUP_RADIUS, f"{sid}: the warp lands on the key")
            tics = int(next(a for a in step.actions if a.startswith("forward")).split()[1])
            self.assertGreaterEqual((tics - route.ACCEL_TICS) * route.WALK_UNITS_PER_TIC, gap, sid)
            dx, dy = route.COMPASS[step.angle]
            for k in range(0, int(gap), SAMPLE):
                p = (step.warp[0] + dx * k, step.warp[1] + dy * k)
                self.assertEqual(family, self.family(p), f"{sid} at {p}")
        for c in route.route_commands(self.r):
            self.assertNotIn(c.split()[0], ("give", "summon"), c)

    def test_the_last_walk_goes_through_d2_to_the_exit_switch(self):
        """E0 stands before D2 on the crest, presses it, and walks west along
        one line through the door's sector and the west hall to the switch:
        every sample on the way in the crest's porch, D2 or the hall, and
        the walk long enough to reach the switch's wall."""
        m = self.m
        step = self.steps["E0"]
        self.assertEqual(180, step.angle)
        exit_x = m.EXIT_NICHE[0]
        self.assertEqual((m.EXIT_NICHE[1] + m.EXIT_NICHE[3]) / 2, step.warp[1], "the switch is on the line")
        families = set()
        for x in range(int(step.warp[0]), exit_x + PLAYER_RADIUS, -SAMPLE):
            families.add(self.family((x, step.warp[1])))
        self.assertEqual({"Z10", "D2", "Z11"}, families)
        tics = int(next(a for a in step.actions if a.startswith("forward")).split()[1])
        self.assertGreaterEqual((tics - route.ACCEL_TICS) * route.WALK_UNITS_PER_TIC,
                                step.warp[0] - exit_x - PLAYER_RADIUS)
        self.assertEqual(((m.TAG_D2_WEST, True),), step.tags)

    def test_the_tags_are_checked_shut_before_and_open_after(self):
        m = self.m
        shut = {sid: dict(self.steps[sid].tags) for sid in ("BG0", "YD0", "YKEY", "SWA", "BKEY")}
        self.assertFalse(shut["BG0"][m.TAG_BLUE_GATE])
        self.assertFalse(shut["YD0"][m.TAG_YELLOW_DOOR])
        # V3: the pickups' tags, shut before their key and open after it.
        self.assertFalse(shut["YD0"][m.TAG_SLUICE_BREACH])
        self.assertEqual({m.TAG_YELLOW_DOOR: False, m.TAG_BLUE_GATE: False, m.TAG_SLUICE_BREACH: True},
                         shut["YKEY"])
        self.assertEqual({m.TAG_CABLE_SHUTTER: True, m.TAG_STATION_SHUTTER: False,
                          m.TAG_SUBSTATION_STORE: False}, shut["SWA"])
        self.assertEqual({m.TAG_BLUE_GATE: False, m.TAG_STATION_SHUTTER: False, m.TAG_SUBSTATION_STORE: True},
                         shut["BKEY"])
        for sid, tag in (("YD1", m.TAG_YELLOW_DOOR), ("SWB", m.TAG_STATION_SHUTTER), ("BG1", m.TAG_BLUE_GATE)):
            self.assertEqual({tag: True}, dict(self.steps[sid].tags), sid)

    def test_it_turns_into_a_console_sequence(self):
        text = route.console_sequence(self.r)
        self.assertLessEqual(len(text), route.MAX_SEQUENCE_CHARS)
        self.assertIn("quit", text)
        self.assertEqual(sum(1 for s in self.r.steps if "inv" in s.actions), text.count("netevent sdinv"))


if __name__ == "__main__":
    unittest.main()
