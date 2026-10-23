"""Episode 2's pickup events (src/maps/common/pickup_events_e2.py), V3 A2/A3.

Owner: `level-designer`. The shared module of MAP04, MAP05 and MAP06: the
action specials a picked-up thing may run (numbers read from g4.14.2's own
table on 2026-10-23, the ones the routes already proved among them), and the
helpers that put one on a UDMF thing. What it holds:

* the numbers agree with the ones the campaign already proved in engine
  (Door_Open 11 in every route, Floor_LowerToLowest 21 as MAP04 wrote it);
* `special_fields` pads to UDMF's five arguments and refuses more, or none;
* `quake` hurts nobody and centres on the activator, and refuses an
  intensity outside the engine's 1..9;
* a rider is never farther from its key than RIDER_OFFSET, and that is
  inside the reach at which both are touched;
* the module names no monster class and no editor number (tests elsewhere
  scan src/maps for those);
* the three maps load it, and use it.

Run:  python3 -m unittest tests.test_pickup_events_e2 -v
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
MODULE = PROJECT_ROOT / "src" / "maps" / "common" / "pickup_events_e2.py"
MAPS = ("MAP04", "MAP05", "MAP06")

PROVEN = {"DOOR_OPEN": 11}                 # every route's switches and MAP06's red key
PLAYER_RADIUS, ITEM_RADIUS = 16, 20        # Doom's player; Inventory's default radius


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PickupEventsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ev = _load(MODULE, "sd_pickup_events_e2_test")

    def test_the_numbers(self):
        ev = self.ev
        for name, number in PROVEN.items():
            self.assertEqual(number, getattr(ev, name), name)
        self.assertEqual((11, 21, 23, 115, 120), (ev.DOOR_OPEN, ev.FLOOR_LOWER_TO_LOWEST,
                                                  ev.FLOOR_RAISE_BY_VALUE, ev.LIGHT_FLICKER, ev.RADIUS_QUAKE))
        self.assertEqual({11, 21, 23}, set(ev.TAG_SPECIALS))
        self.assertNotIn(ev.RADIUS_QUAKE, ev.TAG_SPECIALS, "its arg0 is an intensity, not a tag")
        self.assertLessEqual(set(ev.SINK_SPECIALS), set(ev.TAG_SPECIALS))

    def test_the_speeds_are_xlats(self):
        """gzdoom.pk3 xlat/defines.i: D_SLOW 16, F_NORMAL 16, F_FAST 32, F_TURBO 64."""
        ev = self.ev
        self.assertEqual((16, 16, 32, 64), (ev.DOOR_SPEED_SLOW, ev.FLOOR_SPEED_NORMAL,
                                            ev.FLOOR_SPEED_FAST, ev.FLOOR_SPEED_TURBO))

    def test_special_fields(self):
        ev = self.ev
        self.assertEqual({"special": 11, "arg0": 13, "arg1": 16, "arg2": 0, "arg3": 0, "arg4": 0},
                         ev.special_fields(11, (13, 16)))
        with self.assertRaises(ValueError):
            ev.special_fields(11, (1, 2, 3, 4, 5, 6))
        with self.assertRaises(ValueError):
            ev.special_fields(0, (1,))

    def test_the_quake_hurts_nobody_and_follows_the_player(self):
        ev = self.ev
        special, args = ev.quake(3, 105, 24)
        self.assertEqual(ev.RADIUS_QUAKE, special)
        self.assertEqual((3, 105, 0, 24, 0), args)
        for bad in ((0, 105, 24), (10, 105, 24), (3, 0, 24), (3, 105, 0)):
            with self.assertRaises(ValueError):
                ev.quake(*bad)

    def test_a_rider_is_taken_with_its_key(self):
        ev = self.ev
        self.assertLess(ev.RIDER_OFFSET, ev.PICKUP_REACH)
        self.assertEqual(PLAYER_RADIUS + ITEM_RADIUS, ev.PICKUP_REACH)
        self.assertEqual((672, 920), ev.rider_spot((672, 928), 0, -ev.RIDER_OFFSET))
        with self.assertRaises(ValueError):
            ev.rider_spot((0, 0), ev.RIDER_OFFSET + 1, 0)

    def test_it_names_no_monster_and_no_editor_number(self):
        text = MODULE.read_text(encoding="utf-8")
        self.assertNotRegex(text, r"\bSD_[A-Z][a-z]")
        self.assertFalse(re.findall(r"\b2\d{4}\b", text), "an editor number in the shared module")

    def test_the_three_maps_load_it_and_use_it(self):
        for name in MAPS:
            m = _load(PROJECT_ROOT / "src" / "maps" / name / "map.py", f"sdmap_{name}_events_test")
            self.assertEqual(self.ev.DOOR_OPEN, m.EVENTS.DOOR_OPEN, name)
            self.assertTrue(m.PICKUP_SPECIALS, name)
            for ednum, (special, args) in m.PICKUP_SPECIALS.items():
                self.assertIn(special, self.ev.TAG_SPECIALS, (name, ednum))
                self.assertIn(args[0], m.PICKUP_TAGS, (name, ednum))


if __name__ == "__main__":
    unittest.main()
