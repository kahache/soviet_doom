"""The pickup-event helper (V3 A2): tools/sdbuild/events.py and tests/_pickup_events.py.

Owner: `level-designer`. docs/levels/PICKUP-EVENTS.md is the pattern; the
maps' own event tests are in tests/test_map01.py, test_map02_metro.py and
test_map03_factory.py. Here: the numbers are the table's (VERIFIED in the
engine's compiled special table, section 3), the validation refuses what the
safety rules forbid (R1, tag 0), a thing carries its event on every skill
(R7), and the height rules the map tests use are the engine's.

Run:  python3 -m unittest tests.test_pickup_events -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

import _pickup_events as pe  # noqa: E402
from sdbuild import events, udmf  # noqa: E402

DOC = PROJECT_ROOT / "docs" / "levels" / "PICKUP-EVENTS.md"


class EventsTest(unittest.TestCase):

    def test_the_numbers_are_the_engines(self):
        """GZDoom g4.14.2's compiled table (PICKUP-EVENTS.md section 3), and
        the ones udmf.py and the maps already proved on lines agree."""
        want = {"SPECIAL_DOOR_CLOSE": 10, "SPECIAL_DOOR_OPEN": 11, "SPECIAL_DOOR_RAISE": 12,
                "SPECIAL_FLOOR_LOWER_BY_VALUE": 20, "SPECIAL_FLOOR_LOWER_TO_LOWEST": 21,
                "SPECIAL_FLOOR_LOWER_TO_NEAREST": 22, "SPECIAL_FLOOR_RAISE_BY_VALUE": 23,
                "SPECIAL_FLOOR_RAISE_TO_NEAREST": 25, "SPECIAL_FLOOR_MOVE_TO_VALUE": 37,
                "SPECIAL_CEILING_LOWER_BY_VALUE": 40, "SPECIAL_CEILING_RAISE_BY_VALUE": 41,
                "SPECIAL_CEILING_MOVE_TO_VALUE": 47, "SPECIAL_FLOOR_CEILING_LOWER_BY_VALUE": 95,
                "SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE": 96, "SPECIAL_LIGHT_RAISE_BY_VALUE": 110,
                "SPECIAL_LIGHT_CHANGE_TO_VALUE": 112, "SPECIAL_LIGHT_FADE": 113,
                "SPECIAL_CEILING_RAISE_TO_NEAREST": 252, "SPECIAL_CEILING_LOWER_TO_FLOOR": 254}
        self.assertEqual(want, {name: getattr(events, name) for name in want})
        self.assertEqual(udmf.SPECIAL_DOOR_OPEN, events.SPECIAL_DOOR_OPEN)
        self.assertEqual(udmf.SPECIAL_DOOR_RAISE, events.SPECIAL_DOOR_RAISE)
        self.assertEqual(udmf.SPECIAL_DOOR_CLOSE, events.SPECIAL_DOOR_CLOSE)

    def test_the_document_lists_every_number(self):
        text = DOC.read_text(encoding="utf-8")
        for name in ("Door_Open", "Floor_LowerToLowest", "FloorAndCeiling_RaiseByValue",
                     "Light_ChangeToValue", "Ceiling_RaiseToNearest"):
            self.assertIn(f"`{name}`", text)
        for number in sorted(events.EVENT_SPECIALS | events.CLOSING_SPECIALS):
            self.assertIn(f"{number}", text)

    def test_closing_specials_and_tag_zero_are_refused(self):
        for special in events.CLOSING_SPECIALS:
            with self.assertRaises(ValueError):
                events.PickupEvent("x", special, (5, 16))
        with self.assertRaises(ValueError):
            events.door_open("x", 0)
        with self.assertRaises(ValueError):
            events.PickupEvent("x", events.SPECIAL_DOOR_OPEN, ())
        with self.assertRaises(ValueError):
            events.PickupEvent("x", events.SPECIAL_DOOR_OPEN, (1, 2, 3, 4, 5, 6))
        with self.assertRaises(ValueError):
            events.PickupEvent("x", udmf.SPECIAL_EXIT_NORMAL, (1,))
        with self.assertRaises(ValueError):
            events.light_change("x", 3, 300)

    def test_a_thing_carries_its_event_on_every_skill(self):
        event = events.door_open("closet", 14, lighttag=15)
        thing = events.event_thing(64, 128, 5, event)
        text = thing.to_udmf()
        for field in ("special = 11;", "arg0 = 14;", "arg1 = 16;", "arg2 = 15;", "arg3 = 0;",
                      "arg4 = 0;", "type = 5;"):
            self.assertIn(field, text)
        for n in range(1, 6):
            self.assertIn(f"skill{n} = true;", text)
        self.assertEqual({"special": 96, "arg0": 3, "arg1": 16, "arg2": 192, "arg3": 0, "arg4": 0},
                         events.lift_raise_by_value("lift", 3, 192).fields())

    def test_the_heights_after_an_event_follow_the_engines_rules(self):
        """Door: lowest neighbouring ceiling - 4. Lower to lowest: the lowest
        neighbouring floor. A lift car: floor and ceiling by the same value."""
        sectors = [{"heightfloor": 0, "heightceiling": 128, "id": 0},
                   {"heightfloor": 32, "heightceiling": 32, "id": 7},
                   {"heightfloor": -64, "heightceiling": 96, "id": 0}]
        around = {1: {0, 2}}
        self.assertEqual((32, 92), pe.sector_after(events.door_open("d", 7), 1, sectors, around))
        self.assertEqual((-64, 32), pe.sector_after(events.floor_lower_to_lowest("f", 7), 1,
                                                    sectors, around))
        self.assertEqual((224, 224), pe.sector_after(events.lift_raise_by_value("l", 7, 192), 1,
                                                     sectors, around))
        self.assertEqual((16, 16), pe.sector_after(events.lift_lower_by_value("l", 7, 16), 1,
                                                   sectors, around))
        self.assertEqual((32, 96), pe.sector_after(events.ceiling_raise_to_nearest("c", 7), 1,
                                                   sectors, around))


if __name__ == "__main__":
    unittest.main()
