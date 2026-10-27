"""Pickup events (V3 A2): a map thing whose special fires when it is picked up.

The pattern, its safety rules and how each event is tested live in
`docs/levels/PICKUP-EVENTS.md`; this module is the generators' half of it.

GZDoom runs an inventory item's `special` (with `arg0..arg4`) once, with the
player as activator, at the moment the item is picked up
(`Inventory.DoPickupSpecial`, gzdoom.pk3 g4.14.2, zscript/actors/inventory/
inventory.zs). A monster's special runs when it dies (MAP03's General, v1.1).
In UDMF both are plain thing fields: `special = 21; arg0 = 12; arg1 = 16;`.

The special NUMBERS below are VERIFIED (2026-10-23) against the compiled
special table of the engine we ship on, GZDoom g4.14.2 (`gzdoom.exe`, the
`{name, number, min_args, max_args}` records the binary carries; no data
file lists them). The BEHAVIOUR of a pickup special is VERIFIED in the
GZDoom source only; each map's engine checklist walks its events.

Python 3 standard library only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .udmf import DOOR_SPEED_SLOW, Thing

# --- The specials an event may use (number, ZDoom name and argument shape) ---
SPECIAL_DOOR_OPEN = 11                  # Door_Open (tag, speed, lighttag): stays open
SPECIAL_DOOR_RAISE = 12                 # Door_Raise (tag, speed, delay, lighttag): opens, closes again
SPECIAL_FLOOR_LOWER_BY_VALUE = 20       # Floor_LowerByValue (tag, speed, height)
SPECIAL_FLOOR_LOWER_TO_LOWEST = 21      # Floor_LowerToLowest (tag, speed): to the lowest neighbouring floor
SPECIAL_FLOOR_LOWER_TO_NEAREST = 22     # Floor_LowerToNearest (tag, speed)
SPECIAL_FLOOR_RAISE_BY_VALUE = 23       # Floor_RaiseByValue (tag, speed, height)
SPECIAL_FLOOR_RAISE_TO_NEAREST = 25     # Floor_RaiseToNearest (tag, speed)
SPECIAL_FLOOR_MOVE_TO_VALUE = 37        # Floor_MoveToValue (tag, speed, height, negative)
SPECIAL_CEILING_RAISE_BY_VALUE = 41     # Ceiling_RaiseByValue (tag, speed, height)
SPECIAL_CEILING_MOVE_TO_VALUE = 47      # Ceiling_MoveToValue (tag, speed, height, negative)
SPECIAL_FLOOR_CEILING_LOWER_BY_VALUE = 95   # FloorAndCeiling_LowerByValue (tag, speed, height): a lift car
SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE = 96   # FloorAndCeiling_RaiseByValue (tag, speed, height)
SPECIAL_LIGHT_RAISE_BY_VALUE = 110      # Light_RaiseByValue (tag, value)
SPECIAL_LIGHT_CHANGE_TO_VALUE = 112     # Light_ChangeToValue (tag, value)
SPECIAL_LIGHT_FADE = 113                # Light_Fade (tag, value, tics)
SPECIAL_CEILING_RAISE_TO_NEAREST = 252  # Ceiling_RaiseToNearest (tag, speed)

# Specials that CLOSE or CRUSH: never on a pickup (rule R1, the player is
# never shut in). Listed so the validation below and the map tests refuse them.
SPECIAL_DOOR_CLOSE = 10                 # Door_Close (tag, speed, lighttag)
SPECIAL_CEILING_LOWER_TO_FLOOR = 254    # Ceiling_LowerToFloor (tag, speed)
SPECIAL_CEILING_LOWER_BY_VALUE = 40     # Ceiling_LowerByValue (tag, speed, height)
CLOSING_SPECIALS = frozenset({SPECIAL_DOOR_CLOSE, SPECIAL_CEILING_LOWER_TO_FLOOR,
                              SPECIAL_CEILING_LOWER_BY_VALUE})

# What a pickup may carry. A floor that RISES is allowed (a step, a bridge, a
# lift car that comes up) but its test must show it shuts no way (rule R1).
EVENT_SPECIALS = frozenset({
    SPECIAL_DOOR_OPEN, SPECIAL_DOOR_RAISE,
    SPECIAL_FLOOR_LOWER_BY_VALUE, SPECIAL_FLOOR_LOWER_TO_LOWEST, SPECIAL_FLOOR_LOWER_TO_NEAREST,
    SPECIAL_FLOOR_RAISE_BY_VALUE, SPECIAL_FLOOR_RAISE_TO_NEAREST, SPECIAL_FLOOR_MOVE_TO_VALUE,
    SPECIAL_CEILING_RAISE_BY_VALUE, SPECIAL_CEILING_MOVE_TO_VALUE, SPECIAL_CEILING_RAISE_TO_NEAREST,
    SPECIAL_FLOOR_CEILING_LOWER_BY_VALUE, SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE,
    SPECIAL_LIGHT_RAISE_BY_VALUE, SPECIAL_LIGHT_CHANGE_TO_VALUE, SPECIAL_LIGHT_FADE,
})
# The specials whose arg0 is a sector tag (all of the above).
TAGGED_SPECIALS = EVENT_SPECIALS | CLOSING_SPECIALS

ARG_COUNT = 5            # arg0..arg4
MOVER_SPEED_SLOW = 8     # F_SLOW / P_SLOW (xlat/defines.i): 1 unit a tic, a slow, heard move
MOVER_SPEED_NORMAL = 16  # 2 units a tic: MAP04's gondola sides
MOVER_SPEED_FAST = 32    # 4 units a tic


@dataclass(frozen=True)
class PickupEvent:
    """One special, fired once when its thing is picked up (or dies).

    `name` is the event's id in the map's design document and tests
    (e.g. "card_closets"); `args` start with the sector tag.
    """

    name: str
    special: int
    args: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.special in CLOSING_SPECIALS:
            raise ValueError(f"{self.name}: special {self.special} closes or crushes (rule R1)")
        if self.special not in EVENT_SPECIALS:
            raise ValueError(f"{self.name}: special {self.special} is not an event special")
        if not 1 <= len(self.args) <= ARG_COUNT:
            raise ValueError(f"{self.name}: 1 to {ARG_COUNT} args, got {len(self.args)}")
        if self.args[0] <= 0:
            raise ValueError(f"{self.name}: arg0 is the sector tag and must be > 0 "
                             "(tag 0 on a thing acts on nothing, or on the wrong sector)")

    @property
    def tag(self) -> int:
        return self.args[0]

    def fields(self) -> dict[str, Any]:
        """The UDMF thing fields: `special` and every arg, unset ones 0."""
        padded = tuple(self.args) + (0,) * (ARG_COUNT - len(self.args))
        return {"special": self.special, **{f"arg{i}": a for i, a in enumerate(padded)}}


# --- Constructors, one per shape the maps use ------------------------------------
def door_open(name: str, tag: int, speed: int = DOOR_SPEED_SLOW, lighttag: int = 0) -> PickupEvent:
    """Open every door sector tagged `tag` for good; `lighttag` sectors light
    up as the door rises (Doom's lit-door effect: from their darkest to their
    brightest neighbour's level)."""
    return PickupEvent(name, SPECIAL_DOOR_OPEN, (tag, speed, lighttag))


def floor_lower_to_lowest(name: str, tag: int, speed: int = MOVER_SPEED_NORMAL) -> PickupEvent:
    """Drop every sector tagged `tag` to its lowest neighbouring floor: a wall
    that sinks into the ground (MAP04's gondola sides)."""
    return PickupEvent(name, SPECIAL_FLOOR_LOWER_TO_LOWEST, (tag, speed))


def floor_lower_by_value(name: str, tag: int, height: int,
                         speed: int = MOVER_SPEED_SLOW) -> PickupEvent:
    """Sink every floor tagged `tag` by `height` units (a floor that gives way)."""
    return PickupEvent(name, SPECIAL_FLOOR_LOWER_BY_VALUE, (tag, speed, height))


def ceiling_raise_to_nearest(name: str, tag: int, speed: int = MOVER_SPEED_NORMAL) -> PickupEvent:
    """Lift every ceiling tagged `tag` to the nearest higher neighbouring ceiling."""
    return PickupEvent(name, SPECIAL_CEILING_RAISE_TO_NEAREST, (tag, speed))


def lift_lower_by_value(name: str, tag: int, height: int,
                        speed: int = MOVER_SPEED_SLOW) -> PickupEvent:
    """Move floor and ceiling of every sector tagged `tag` down together by
    `height`: a goods-lift car that descends with what stands on it."""
    return PickupEvent(name, SPECIAL_FLOOR_CEILING_LOWER_BY_VALUE, (tag, speed, height))


def lift_raise_by_value(name: str, tag: int, height: int,
                        speed: int = MOVER_SPEED_NORMAL) -> PickupEvent:
    """Move floor and ceiling of every sector tagged `tag` up together by
    `height`: a goods-lift car that comes up a shaft with what stands on it.
    A car whose ceiling starts flush with the room's floor is a wall (the
    room sees the shaft's front from floor to ceiling) until it rises: its
    front lifts like a gate while the car's floor, and its load, come up
    behind it (MAP03's goods lift, design section 19)."""
    return PickupEvent(name, SPECIAL_FLOOR_CEILING_RAISE_BY_VALUE, (tag, speed, height))


def light_change(name: str, tag: int, value: int) -> PickupEvent:
    """Set the light of every sector tagged `tag` to `value` (0..255)."""
    if not 0 <= value <= 255:
        raise ValueError(f"{name}: light {value} outside 0..255")
    return PickupEvent(name, SPECIAL_LIGHT_CHANGE_TO_VALUE, (tag, value))


def event_thing(x: float, y: float, type: int, event: PickupEvent, angle: int = 0,
                **kwargs: Any) -> Thing:
    """A pickup carrying `event`, present on EVERY skill (an event that exists
    on one skill only would make the maps differ in more than numbers)."""
    thing = Thing(x=x, y=y, type=type, angle=angle, **kwargs)
    thing.extra.update(event.fields())
    return thing
