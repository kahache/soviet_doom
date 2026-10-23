"""`zemlya-critical`, MAP07's automatic route (tools/route.py), checked on the
built map without the engine (D26): the PM runs it in the engine.

Owner: `level-designer`. What it holds: the route finds MAP07 by its own
constants, walks the design's order (both locks shut without keys, the
yellow key, the yellow door, SW-A, the red key, SW-B, the red gate, D3, the
exit switch), presses each line from the room the design presses it from,
walks onto each key without `give`, and its last walk goes from the deck
through the conning tower's hatch straight to the exit switch on one line.

Run:  python3 -m unittest tests.test_map07_route -v
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


class ZemlyaRouteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.map_name = route.map_defining(*route.ZEMLYA_CONSTANTS)
        cls.md = route.load_map_data(cls.map_name)
        cls.m = cls.md.module
        cls.r = route.zemlya_critical(cls.md)
        cls.steps = {s.id: s for s in cls.r.steps}

    def family(self, point):
        return route.zone_family(self.md.name_of(self.md.sector_at(*point)))

    def test_the_route_is_registered_and_finds_novaya_zemlya(self):
        self.assertEqual("MAP07", self.map_name)
        self.assertIn("zemlya-critical", route.route_names())
        self.assertEqual("zemlya-critical", self.r.name)
        self.assertEqual(self.map_name, self.r.map_name)

    def test_it_plays_the_designs_order(self):
        self.assertEqual(["A0", "RG0", "YD0", "YKEY", "YD1", "SWA", "RKEY", "SWB", "RG1", "E0", "E1"],
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
        want = {"RG0": ("Z1", m.TAG_RED_GATE), "RG1": ("Z1", m.TAG_RED_GATE),
                "YD0": ("Z2", m.TAG_YELLOW_DOOR), "YD1": ("Z2", m.TAG_YELLOW_DOOR),
                "SWA": ("Z6", m.TAG_BUNKER_SHUTTER), "SWB": ("Z7", m.TAG_RUNWAY_SHUTTER),
                "E0": ("Z11", m.TAG_D3_HATCH)}
        for sid, (family, tag) in want.items():
            step = self.steps[sid]
            self.assertEqual(family, self.family(step.warp), sid)
            self.assertEqual(tag, step.presses[0][1], sid)
            self.assertIn("use", step.actions, sid)

    def test_each_press_reaches_its_line(self):
        """The warp stands within Doom's use range of the pressed line's
        middle, facing it."""
        tm = self.md.textmap
        for sid in ("RG0", "YD0", "SWA", "SWB", "E0"):
            step = self.steps[sid]
            special, tag = step.presses[0]
            lines = [ld for ld in tm.linedefs if ld.special == special and ld.arg0 == tag]
            middles = []
            for ld in lines:
                (x1, y1), (x2, y2) = route.line_ends(self.md, ld)
                middles.append(((x1 + x2) / 2, (y1 + y2) / 2))
            middle = min(middles, key=lambda p: math.dist(step.warp, p))
            self.assertLess(math.dist(step.warp, middle), USE_RANGE, sid)
            dx, dy = route.COMPASS[step.angle]
            ahead = (step.warp[0] + dx * route.USE_DISTANCE, step.warp[1] + dy * route.USE_DISTANCE)
            self.assertLess(math.dist(ahead, middle), 1, f"{sid} faces its line")

    def test_the_doors_lead_where_the_design_says(self):
        self.assertEqual("Z6", self.steps["YD1"].expect[0], "the yellow door into the command room")
        self.assertEqual("Z8", self.steps["RG1"].expect[0], "the red gate onto the harbour road")
        self.assertEqual("Z12", self.steps["E0"].expect[0], "D3 into the conning tower")

    def test_the_keys_are_walked_onto_never_given(self):
        m = self.m
        for sid, spot, family in (("YKEY", m.YELLOW_KEY_SPOT, "Z5"), ("RKEY", m.RED_KEY_SPOT, "Z7")):
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

    def test_the_last_walk_goes_through_d3_to_the_exit_switch(self):
        """E0 stands before D3 on the deck, presses it, and walks west along
        one line through the hatch and the tower to the switch: every sample
        on the way in the hatch's porch, D3 or the tower, and the walk long
        enough to reach the switch's wall."""
        m = self.m
        step = self.steps["E0"]
        self.assertEqual(180, step.angle)
        exit_x = m.EXIT_NICHE[0]
        self.assertEqual((m.EXIT_NICHE[1] + m.EXIT_NICHE[3]) / 2, step.warp[1], "the switch is on the line")
        families = set()
        for x in range(int(step.warp[0]), exit_x + PLAYER_RADIUS, -SAMPLE):
            families.add(self.family((x, step.warp[1])))
        self.assertEqual({"Z11", "D3", "Z12"}, families)
        tics = int(next(a for a in step.actions if a.startswith("forward")).split()[1])
        self.assertGreaterEqual((tics - route.ACCEL_TICS) * route.WALK_UNITS_PER_TIC,
                                step.warp[0] - exit_x - PLAYER_RADIUS)
        self.assertEqual(((m.TAG_D3_HATCH, True),), step.tags)

    def test_the_tags_are_checked_shut_before_and_open_after(self):
        m = self.m
        shut = {sid: dict(self.steps[sid].tags) for sid in ("RG0", "YD0", "YKEY", "SWA", "RKEY")}
        self.assertFalse(shut["RG0"][m.TAG_RED_GATE])
        self.assertFalse(shut["YD0"][m.TAG_YELLOW_DOOR])
        self.assertEqual({m.TAG_YELLOW_DOOR: False, m.TAG_RED_GATE: False}, shut["YKEY"])
        self.assertEqual({m.TAG_BUNKER_SHUTTER: True, m.TAG_RUNWAY_SHUTTER: False}, shut["SWA"])
        self.assertEqual({m.TAG_RED_GATE: False, m.TAG_RUNWAY_SHUTTER: False, m.TAG_BUNKER_CELLS: True},
                         shut["RKEY"], "V3: the red key's pickup sinks the cells' walls")
        for sid, tag in (("YD1", m.TAG_YELLOW_DOOR), ("SWB", m.TAG_RUNWAY_SHUTTER), ("RG1", m.TAG_RED_GATE)):
            self.assertEqual({tag: True}, dict(self.steps[sid].tags), sid)

    def test_it_turns_into_a_console_sequence(self):
        text = route.console_sequence(self.r)
        self.assertLessEqual(len(text), route.MAX_SEQUENCE_CHARS)
        self.assertIn("quit", text)
        self.assertEqual(sum(1 for s in self.r.steps if "inv" in s.actions), text.count("netevent sdinv"))


if __name__ == "__main__":
    unittest.main()
