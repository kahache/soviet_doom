"""tunguska-critical: MAP09's automatic route, read off the built map.

Owner: `level-designer` (the route block in tools/route.py and this file).
redsquare-critical's checks (tests/test_map06_route.py) on Tunguska: three
keys counted, never named; each lock pressed from the room the design presses
it from, refused before its key and walked through after it; the keys walked
onto; the red key's pickup expected to open the works' closets; the boss
killed by the helper's damage, his death expected to open the bunker's gate;
the exit walk through that gate. No engine is started (D26).

Run:  python3 -m unittest tests.test_map09_route -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import route  # noqa: E402
from sdbuild import udmf  # noqa: E402
# Imported as a module, so its TestCases are not collected twice here.
import test_route as tr  # noqa: E402

TUNGUSKA = route.map_defining(*route.TUNGUSKA_CONSTANTS)
NAME = "tunguska-critical"


class TunguskaRouteTest(tr.BuiltMapRoute, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.md = route.load_map_data(TUNGUSKA)
        cls.m = cls.md.module
        cls.r = route.route_by_name(NAME)
        cls.steps = {s.id: s for s in cls.r.steps}

    def test_it_is_built_lazily_and_offered_everywhere(self):
        self.assertNotIn(NAME, route.ROUTES, "built at import: a broken MAP09 would break MAP01")
        self.assertIn(NAME, route.route_names())
        self.assertEqual(NAME, route.parse_args(["--route", NAME]).route)
        self.assertEqual("MAP09", TUNGUSKA)
        self.assertEqual(TUNGUSKA, self.r.map_name)

    def test_the_order_is_the_designs(self):
        self.assertEqual(["A0", "BD0", "BKEY", "BD1", "YD0", "RD0", "YKEY", "YD1", "RDY", "RKEY",
                          "RD1", "BOSS0", "BOSS1", "E0", "E1"], [s.id for s in self.r.steps])
        self.assertEqual(("switch", True, 0), (self.r.exit_by, self.r.must_exit, self.r.expect_secrets))
        want = route.exit_expectation(TUNGUSKA)
        self.assertEqual((want["end_sequence"], want["next_map"]), (self.r.end_sequence, self.r.next_map))
        self.assertEqual("use", self.r.steps[-1].actions[0])

    def test_tags_presses_and_key_counts_are_map_py_constants(self):
        m, s = self.m, self.steps
        bd, yd, rd, amb, ex, lk = (m.TAG_BLUE_DOOR, m.TAG_YELLOW_DOOR, m.TAG_RED_DOOR, m.TAG_AMBUSH,
                                   m.TAG_BOSS_EXIT, m.SPECIAL_DOOR_LOCKED_RAISE)
        self.assertEqual({"BD0": ((bd, False),), "BKEY": ((bd, False),), "BD1": ((bd, True),),
                          "YD0": ((yd, False),), "RD0": ((rd, False),), "YKEY": ((yd, False),),
                          "YD1": ((yd, True),), "RDY": ((rd, False),),
                          "RKEY": ((rd, False), (amb, True)), "RD1": ((rd, True),),
                          "BOSS0": ((ex, False),), "BOSS1": ((ex, True),)},
                         {k: v.tags for k, v in s.items() if v.tags})
        self.assertEqual({"BD0": ((lk, bd),), "BD1": ((lk, bd),), "YD0": ((lk, yd),), "YD1": ((lk, yd),),
                          "RD0": ((lk, rd),), "RDY": ((lk, rd),), "RD1": ((lk, rd),)},
                         {k: v.presses for k, v in s.items() if v.presses})
        self.assertEqual({"A0": 0, "BD0": 0, "BKEY": 1, "YD0": 1, "RD0": 1, "YKEY": 2, "RDY": 2,
                          "RKEY": 3}, {k: v.keys for k, v in s.items() if v.keys is not None})

    def test_the_zones_are_the_designs(self):
        """The railhead start; the blue gate from the station's yard (Z3), its
        key in the laboratory (Z3); the yellow door and the red gate from the
        works (Z5); the yellow key on the derrick (Z5); the refinery (Z6); the
        crater's rim (Z7) and terraces (Z8); the bunker (Z9)."""
        want = {"A0": ("Z1",), "BD0": ("Z3",), "BKEY": ("Z3",), "BD1": ("Z4",), "YD0": ("Z5",),
                "RD0": ("Z5",), "YKEY": ("Z5",), "YD1": ("Z6",), "RDY": ("Z5",), "RKEY": ("Z6",),
                "RD1": ("Z7",), "BOSS0": ("Z8",), "E0": ("Z9",)}
        self.assertEqual(want, {k: v.expect for k, v in self.steps.items() if v.expect})
        self.assertEqual([], sorted(n for n in self.md.plan if route.zone_family(n) == "?"))

    def test_no_map09_position_or_class_is_written_in_route_py(self):
        source = Path(route.__file__).read_text(encoding="utf-8")
        for step in self.r.steps:
            if step.warp is None:
                continue
            x, y = step.warp
            self.assertNotIn(f"({x}, {y})", source, step.id)
        block = source[source.index("TUNGUSKA_CONSTANTS = "):source.index("ED_PLAYER1_START = 1")]
        for literal in ('"SD_General"', '"MAP09"', '"z3_key_bench"', '"z5_key_top"', '"z6_key_dais"',
                        '"BLUE_KEY_SPOT"'):
            self.assertNotIn(literal, block)

    def test_each_lock_is_pressed_within_reach_and_walked_through(self):
        md, tm, m = self.md, self.md.textmap, self.m
        for presses, walk_id, tag, lock, family, door_family, inside in (
                (("BD0",), "BD1", m.TAG_BLUE_DOOR, m.LOCK_BLUE_CARD, "Z3", "Z4", "Z4"),
                (("YD0",), "YD1", m.TAG_YELLOW_DOOR, m.LOCK_YELLOW_CARD, "Z5", "Z6", "Z6"),
                (("RD0", "RDY"), "RD1", m.TAG_RED_DOOR, m.LOCK_RED_CARD, "Z5", "Z7", "Z7")):
            with self.subTest(walk_id):
                through = self.steps[walk_id]
                for sid in presses:
                    self.assertEqual((through.warp, through.angle),
                                     (self.steps[sid].warp, self.steps[sid].angle), sid)
                here = self.clear_of_walls(through.warp)
                dist, ld = self.line_ahead(through.warp, through.angle)
                self.assertLessEqual(dist, tr.USE_RANGE)
                self.assertEqual((m.SPECIAL_DOOR_LOCKED_RAISE, tag, lock), (ld.special, ld.arg0, ld.arg3))
                # The face is the portal's; the body stands in front of it (each
                # portal is 32 deep, so the body may stand in the room outside).
                self.assertEqual(m.LOCK_PORTALS[lock], md.name_of(tm.sidedefs[ld.sidefront].sector))
                self.assertEqual(family, route.zone_family(md.name_of(here)))
                self.assertEqual(tag, tm.sectors[tm.sidedefs[ld.sideback].sector].identifier)
                crossed = self.walk(through.warp, through.angle, self.tics(through) * tr.WALK_UNITS_PER_TIC)
                families = list(dict.fromkeys(route.zone_family(md.name_of(s))
                                              for s in crossed if s is not None))
                self.assertEqual(family, families[0])
                self.assertIn(inside, families)
                first = next(i for i, s in enumerate(crossed)
                             if s is not None and route.zone_family(md.name_of(s)) == inside
                             and md.name_of(s) != md.name_of(tm.sidedefs[ld.sideback].sector))
                self.assertGreaterEqual(tr.model_walk(self.tics(through)), first * tr.SAMPLE + tr.PLAYER_RADIUS)

    def test_the_keys_are_walked_onto_never_given(self):
        md, m = self.md, self.m
        for sid, ed, spot in (("BKEY", m.ED_BLUE_CARD, m.BLUE_KEY_SPOT),
                              ("YKEY", m.ED_YELLOW_CARD, m.YELLOW_KEY_SPOT),
                              ("RKEY", m.ED_RED_CARD, m.RED_KEY_SPOT)):
            with self.subTest(sid):
                step = self.steps[sid]
                for skill in (2, 3, 4):
                    self.assertEqual(1, len(md.things_on(ed, skill)), f"skill {skill}")
                thing = md.things_on(ed, 3)[0]
                self.assertEqual(spot, (thing.x, thing.y))
                self.assertEqual(m.KEY_ZONES[ed], md.name_of(md.sector_at(thing.x, thing.y)))
                start = step.warp
                self.clear_of_walls(start)
                dx, dy = route.COMPASS[step.angle]
                gap = (thing.x - start[0]) * dx + (thing.y - start[1]) * dy
                self.assertEqual(0, (thing.x - start[0]) * dy - (thing.y - start[1]) * dx, "off the lane")
                self.assertGreater(gap, tr.PLAYER_RADIUS + tr.PICKUP_RADIUS)
                self.assertGreaterEqual(tr.model_walk(self.tics(step)), gap)
                floor = md.textmap.sectors[md.sector_at(*start)].heightfloor
                for s in self.walk(start, step.angle, gap):
                    self.assertEqual(step.expect, (route.zone_family(md.name_of(s)),), md.name_of(s))
                    self.assertLessEqual(md.textmap.sectors[s].heightfloor - floor, tr.MAX_STEP_UP)

    def test_the_boss_is_hurt_by_his_own_class_in_the_crater(self):
        m, md = self.m, self.md
        boss_class = m.MONSTER_CLASSES[m.MONSTER_KINDS[m.BOSS_KIND]]
        self.assertIn(boss_class, route.COUNT_CLASSES)
        b1 = self.steps["BOSS1"]
        self.assertEqual(f"hurt {boss_class} {route.BOSS_HURT}", b1.actions[0])
        self.assertIsNone(b1.warp, "BOSS1 stays where BOSS0 stood")
        self.assertGreater(route.BOSS_HURT, 10 * self.hp(boss_class))
        here = self.clear_of_walls(self.steps["BOSS0"].warp)
        self.assertEqual("Z8", route.zone_family(md.name_of(here)))
        self.assertEqual("Z8", route.family_at(md, m.MAP09_BOSS_SPOT))

    def hp(self, cls):
        text = (PROJECT_ROOT / "src" / "zscript" / "monsters" / "general.zs").read_text(encoding="utf-8")
        self.assertEqual("SD_General", cls, "a new boss: read his health from his own file")
        return int(re.search(r"SD_GENERAL_HEALTH\s*=\s*(\d+)", text).group(1))

    def test_a_boss_the_helper_cannot_hurt_has_no_route(self):
        md = route.MapData(TUNGUSKA)
        route.tunguska_critical(md)
        md.module.MONSTER_CLASSES = dict(md.module.MONSTER_CLASSES)
        md.module.MONSTER_CLASSES[md.module.MONSTER_KINDS[md.module.BOSS_KIND]] = "SD_NoSuchBoss"
        with self.assertRaises(route.RouteError):
            route.tunguska_critical(md)

    def test_a_door_that_loses_or_swaps_its_lock_has_no_route(self):
        md = route.MapData(TUNGUSKA)
        m = md.module
        for ld in md.textmap.linedefs:
            if ld.special == m.SPECIAL_DOOR_LOCKED_RAISE and ld.arg0 == m.TAG_YELLOW_DOOR:
                ld.arg3 = m.LOCK_RED_CARD
        with self.assertRaises(route.RouteError):
            route.tunguska_critical(md)

    def test_the_exit_walk_crosses_the_bunkers_gate_to_the_switch(self):
        md, tm, m = self.md, self.md.textmap, self.m
        e0, e1 = self.steps["E0"], self.steps["E1"]
        exits = [ld for ld in tm.linedefs if ld.special == route.SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_line = exits[0]
        self.assertEqual((m.EXIT_FACE, None), (tm.sidedefs[exit_line.sidefront].texturemiddle,
                                               exit_line.sideback))
        (x1, y1), _ = route.line_ends(md, exit_line)
        dx, dy = route.COMPASS[e0.angle]
        to_wall = (x1 - e0.warp[0]) * dx if dx else (y1 - e0.warp[1]) * dy
        walk = to_wall - tr.PLAYER_RADIUS
        crossed = self.walk(e0.warp, e0.angle, walk)
        self.assertNotIn(None, crossed)
        self.assertIn(m.TAG_BOSS_EXIT, {tm.sectors[s].identifier for s in crossed})
        self.assertEqual("Z9", route.zone_family(md.name_of(crossed[-1])))
        end = (e0.warp[0] + dx * walk, e0.warp[1] + dy * walk)
        dist, ahead = self.line_ahead(end, e0.angle)
        self.assertIs(exit_line, ahead)
        self.assertLessEqual(dist, tr.USE_RANGE)
        self.assertGreaterEqual(tr.model_walk(self.tics(e0)), walk)
        self.assertEqual(("use",), e1.actions)

    def test_print_runs_on_map09(self):
        with tempfile.TemporaryDirectory() as tmp, tr.no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = tr.run_main(["--print", "--route", NAME])
        self.assertEqual(route.EXIT_OK, code)
        for skill in (2, 3, 4):
            self.assertIn(f"-skill {skill} +map {TUNGUSKA}", out)
        m = self.m
        for tag in (m.TAG_BLUE_DOOR, m.TAG_YELLOW_DOOR, m.TAG_RED_DOOR, m.TAG_AMBUSH, m.TAG_BOSS_EXIT):
            self.assertIn(f"netevent sdtag {tag}", out)
        self.assertIn(f"netevent sdhurt {route.COUNT_CLASSES.index('SD_General')} {route.BOSS_HURT}", out)
        self.assertNotIn("sdexit", out)
        self.assertNotRegex(out, r"(?m)^\s+give\b")


if __name__ == "__main__":
    unittest.main()
