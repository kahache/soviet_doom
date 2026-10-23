"""Shared checks for pickup events (V3 A2, docs/levels/PICKUP-EVENTS.md section 7).

Not a test module (the leading underscore keeps unittest discovery off it):
the map tests import it and call these over their parsed TEXTMAP, the dicts
`tests/test_udmf.parse_textmap` returns. Python 3 standard library only.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "tools"))

from sdbuild import events  # noqa: E402

SKILL_FLAGS = tuple(f"skill{n}" for n in range(1, 6))
DOOR_OPENS_BELOW_CEILING = 4   # ZDoom raises a door to the lowest neighbouring ceiling - 4


def event_things(things) -> list[dict]:
    """Every thing that carries a special (pickup or death events)."""
    return [t for t in things if t.get("special")]


def thing_args(thing) -> tuple[int, ...]:
    return tuple(thing.get(f"arg{i}", 0) for i in range(events.ARG_COUNT))


def tagged(sectors, tag) -> set[int]:
    return {i for i, s in enumerate(sectors) if s.get("id") == tag}


def lines_with_tag(lines, tag) -> list[int]:
    """Lines whose special acts on `tag` (arg0 of a tagged special)."""
    return [i for i, ld in enumerate(lines)
            if ld.get("special") in events.TAGGED_SPECIALS | {13} and ld.get("arg0") == tag]


def assert_event(test, things, sectors, lines, ednum, event, expected) -> dict:
    """The rules of section 7 for one event: its thing exists once, on every
    skill, with the event's special and args (padded to five); the sectors
    tagged arg0 are exactly `expected` (R8) and no line acts on that tag;
    the special opens or lifts, never closes (R1). Returns the thing."""
    found = [t for t in things if t["type"] == ednum and t.get("special")]
    test.assertEqual(1, len(found), f"{event.name}: one thing {ednum} carrying it")
    thing = found[0]
    test.assertTrue(all(thing.get(flag) for flag in SKILL_FLAGS),
                    f"{event.name}: on every skill (R7)")
    test.assertEqual(event.special, thing["special"], event.name)
    test.assertEqual(event.fields(), {"special": thing["special"],
                                      **{f"arg{i}": a for i, a in enumerate(thing_args(thing))}},
                     event.name)
    test.assertNotIn(thing["special"], events.CLOSING_SPECIALS, f"{event.name} (R1)")
    test.assertEqual(set(expected), tagged(sectors, event.tag), f"{event.name}: tagged sectors (R8)")
    test.assertEqual([], lines_with_tag(lines, event.tag), f"{event.name}: a line acts on its tag (R8)")
    return thing


def neighbours(lines, sides) -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    for ld in lines:
        if "sideback" in ld:
            a, b = sides[ld["sidefront"]]["sector"], sides[ld["sideback"]]["sector"]
            out.setdefault(a, set()).add(b)
            out.setdefault(b, set()).add(a)
    return out


def sector_after(event, index, sectors, around) -> tuple[float, float]:
    """(floor, ceiling) of sector `index` once `event` has run on it, by the
    engine's rule for that special. `around` is {sector: neighbours}."""
    s = sectors[index]
    floor, ceiling = s["heightfloor"], s["heightceiling"]
    near = [sectors[n] for n in around.get(index, ())]
    special, args = event.special, tuple(event.args) + (0,) * events.ARG_COUNT
    if special in (events.SPECIAL_DOOR_OPEN, events.SPECIAL_DOOR_RAISE):
        ceiling = min(n["heightceiling"] for n in near) - DOOR_OPENS_BELOW_CEILING
    elif special == events.SPECIAL_FLOOR_LOWER_TO_LOWEST:
        floor = min(n["heightfloor"] for n in near)
    elif special == events.SPECIAL_FLOOR_LOWER_BY_VALUE:
        floor -= args[2]
    elif special == events.SPECIAL_FLOOR_RAISE_BY_VALUE:
        floor += args[2]
    elif special == events.SPECIAL_CEILING_RAISE_BY_VALUE:
        ceiling += args[2]
    elif special == events.SPECIAL_CEILING_RAISE_TO_NEAREST:
        ceiling = min(n["heightceiling"] for n in near if n["heightceiling"] > ceiling)
    elif special == events.SPECIAL_FLOOR_CEILING_LOWER_BY_VALUE:
        floor, ceiling = floor - args[2], ceiling - args[2]
    elif special == events.SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE:
        floor, ceiling = floor + args[2], ceiling + args[2]
    elif special in (events.SPECIAL_LIGHT_CHANGE_TO_VALUE, events.SPECIAL_LIGHT_RAISE_BY_VALUE,
                     events.SPECIAL_LIGHT_FADE):
        pass                                  # light only: no height moves
    else:
        raise ValueError(f"{event.name}: no height rule for special {special}")
    return floor, ceiling


def heights_after(fired, sectors, lines, sides) -> dict[int, tuple[float, float]]:
    """{sector: (floor, ceiling)} for every sector moved by the `fired` events."""
    around = neighbours(lines, sides)
    out = {}
    for event in fired:
        for index in tagged(sectors, event.tag):
            out[index] = sector_after(event, index, sectors, around)
    return out
