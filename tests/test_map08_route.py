"""`severomorsk-critical`, MAP08's automatic route (tools/route.py), checked on
the built map without the engine (D26): the PM runs it in the engine.

Owner: `level-designer`. What it holds: the route finds MAP08 by its own
constants, walks the design's order (the three locks refused without keys,
SW-A, the blue key, the blue door, the yellow key, the yellow door, the red
key, SW-B, the red gate, the regulator), presses each line from the room the
design presses it from and within use range facing it, walks onto each key
without `give`, and ends in the locomotive's cab before the exit switch.

Run:  python3 -m unittest tests.test_map08_route -v
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


class SeveromorskRouteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.map_name = route.map_defining(*route.SEVEROMORSK_CONSTANTS)
        cls.md = route.load_map_data(cls.map_name)
        cls.m = cls.md.module
        cls.r = route.severomorsk_critical(cls.md)
        cls.steps = {s.id: s for s in cls.r.steps}

    def family(self, point):
        return route.zone_family(self.md.name_of(self.md.sector_at(*point)))

    def test_the_route_is_registered_and_finds_the_base(self):
        self.assertEqual("MAP08", self.map_name)
        self.assertIn("severomorsk-critical", route.route_names())
        self.assertEqual("severomorsk-critical", self.r.name)
        self.assertEqual(self.map_name, self.r.map_name)

    def test_it_plays_the_designs_order(self):
        self.assertEqual(["A0", "RG0", "BD0", "YD0", "SWA", "BKEY", "BD1", "YKEY", "YD1", "RKEY",
                          "SWB", "RG1", "E0", "E1"], [s.id for s in self.r.steps])
        self.assertEqual([0, 0, 0, 0, None, 1, None, 2, None, 3, None, None, None, None],
                         [s.keys for s in self.r.steps])

    def test_its_exit_leads_to_mapinfos_next_by_a_switch(self):
        self.assertEqual(route.exit_expectation(self.map_name)["next_map"], self.r.next_map)
        self.assertFalse(self.r.end_sequence)
        self.assertEqual(("switch", True, 0), (self.r.exit_by, self.r.must_exit, self.r.expect_secrets))
        self.assertEqual(("use",), self.r.steps[-1].actions)

    def test_each_press_is_made_from_the_room_the_design_names(self):
        m = self.m
        want = {"RG0": ("Z2", m.TAG_RED_GATE), "RG1": ("Z2", m.TAG_RED_GATE),
                "BD0": ("Z3", m.TAG_BLUE_DOOR), "BD1": ("Z3", m.TAG_BLUE_DOOR),
                "YD0": ("Z3", m.TAG_YELLOW_DOOR), "YD1": ("Z3", m.TAG_YELLOW_DOOR),
                "SWA": ("Z4", m.TAG_WT_SHUTTER), "SWB": ("Z11", m.TAG_BARRACKS_SHUTTER)}
        for sid, (family, tag) in want.items():
            step = self.steps[sid]
            self.assertEqual(family, self.family(step.warp), sid)
            self.assertEqual(tag, step.presses[0][1], sid)
            self.assertIn("use", step.actions, sid)

    def test_each_press_reaches_its_line(self):
        """The warp stands within Doom's use range of the pressed line's
        middle, facing it."""
        tm = self.md.textmap
        for sid in ("RG0", "BD0", "YD0", "SWA", "SWB"):
            step = self.steps[sid]
            special, tag = step.presses[0]
            middles = []
            for ld in tm.linedefs:
                if ld.special == special and ld.arg0 == tag:
                    (x1, y1), (x2, y2) = route.line_ends(self.md, ld)
                    middles.append(((x1 + x2) / 2, (y1 + y2) / 2))
            middle = min(middles, key=lambda p: math.dist(step.warp, p))
            self.assertLess(math.dist(step.warp, middle), USE_RANGE, sid)
            dx, dy = route.COMPASS[step.angle]
            ahead = (step.warp[0] + dx * route.USE_DISTANCE, step.warp[1] + dy * route.USE_DISTANCE)
            self.assertLess(math.dist(ahead, middle), 1, f"{sid} faces its line")

    def test_the_doors_lead_where_the_design_says(self):
        self.assertEqual("Z5", self.steps["BD1"].expect[0], "the blue door into the workshops")
        self.assertEqual("Z7", self.steps["YD1"].expect[0], "the yellow door into the rock tunnel")
        self.assertEqual("Z9", self.steps["RG1"].expect[0], "the red gate into the rail tunnel")

    def test_the_keys_are_walked_onto_never_given(self):
        m = self.m
        for sid, spot, family in (("BKEY", m.BLUE_KEY_SPOT, "Z4"), ("YKEY", m.YELLOW_KEY_SPOT, "Z5"),
                                  ("RKEY", m.RED_KEY_SPOT, "Z8")):
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

    def test_the_last_stop_is_the_cab_facing_the_regulator(self):
        m = self.m
        step = self.steps["E0"]
        self.assertEqual("Z10", self.family(step.warp))
        self.assertEqual(self.md.plan["z10_cab"], self.md.sector_at(*step.warp))
        self.assertEqual(0, step.angle, "the regulator is on the cab's east wall")
        self.assertLess(m.EXIT_NICHE[2] - step.warp[0], USE_RANGE)
        self.assertEqual((m.EXIT_NICHE[1] + m.EXIT_NICHE[3]) / 2, step.warp[1])

    def test_the_tags_are_checked_shut_before_and_open_after(self):
        m = self.m
        shut = {sid: dict(self.steps[sid].tags) for sid in ("RG0", "BD0", "YD0", "BKEY", "YKEY", "RKEY")}
        self.assertEqual({m.TAG_RED_GATE: False}, shut["RG0"])
        self.assertEqual({m.TAG_BLUE_DOOR: False, m.TAG_YELLOW_DOOR: False, m.TAG_RED_GATE: False}, shut["BKEY"])
        self.assertEqual({m.TAG_YELLOW_DOOR: False, m.TAG_RED_GATE: False}, shut["YKEY"])
        self.assertEqual({m.TAG_RED_GATE: False, m.TAG_BARRACKS_SHUTTER: False}, shut["RKEY"])
        self.assertEqual({m.TAG_WT_SHUTTER: True, m.TAG_BARRACKS_SHUTTER: False}, dict(self.steps["SWA"].tags))
        for sid, tag in (("BD1", m.TAG_BLUE_DOOR), ("YD1", m.TAG_YELLOW_DOOR), ("SWB", m.TAG_BARRACKS_SHUTTER),
                         ("RG1", m.TAG_RED_GATE)):
            self.assertEqual({tag: True}, dict(self.steps[sid].tags), sid)

    def test_it_turns_into_a_console_sequence(self):
        text = route.console_sequence(self.r)
        self.assertLessEqual(len(text), route.MAX_SEQUENCE_CHARS)
        self.assertIn("quit", text)
        self.assertEqual(sum(1 for s in self.r.steps if "inv" in s.actions), text.count("netevent sdinv"))


if __name__ == "__main__":
    unittest.main()
