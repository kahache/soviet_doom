"""Pickup events for episode 2 (MAP04, MAP05, MAP06): V3's A2 and A3.

D119 (the CEO's playtest) asked for keys and objects that make things happen
when they are picked up; D120 put it in V3 with the set pieces (A3: the dam
that bursts). This module holds what the three maps share and nothing else:
the action specials a picked-up thing may run, verified, and the two helpers
that put one on a UDMF thing. The maps keep their own tags, sectors and
tables; `docs/levels/MAP04..06` say, map by map, which pickup does what.

How a pickup event works (MAP04's red key is the model, since v1): a UDMF
thing carries `special` and `arg0..arg4`; GZDoom runs an inventory item's
special when the item is picked up (Inventory.DoPickupSpecial, the toucher is
the activator). VERIFIED in engine on MAP06: the route's RKEY step reads
tag 10 (the museum's closets) open after the red key is walked onto
(docs/qa/evidence/2026-10-23_0216_P4_g3-map06-redsquare-critical-skill3-report.txt).

One special per thing. When an event needs two (the dam's burst: the wall
falls AND the dam shakes AND the water rises), the extra specials ride on
**riders**: bonuses (HealthBonus, ArmorBonus: Doom's ALWAYSPICKUP items, so
they are taken even at full health and armour) lying RIDER_OFFSET from the
key, inside its pickup reach, so the walk that takes the key takes them in
the same tic or the next. A rider never carries the event the route needs;
it carries the dressing (the quake, the water).

THE NUMBERS. ZDoom's special table is compiled into the engine, not shipped
as text (tools/sdbuild/udmf.py says so). These were read on 2026-10-23 from
the engine itself: gzdoom.exe g4.14.2 (the Windows build in
%LOCALAPPDATA%/Programs/GZDoom) keeps the table as rows of {pointer to the
name, number, min args, max args}; for each name the row that points at its
string gives the number. Door_Open 11, Door_LockedRaise 13,
Floor_LowerToLowest 21, Floor_RaiseByValue 23, Light_ChangeToValue 112,
Light_Fade 113, Light_Flicker 115, Light_Strobe 116, Radius_Quake 120,
Exit_Normal 243: the four the routes already proved (11, 13, 243 and the
pickup above) came out right, which is what makes the rest trustworthy.
Note for the PM: tools/sdbuild/udmf.py's SPECIAL_LIGHT_CHANGE_TO_VALUE (110)
and SPECIAL_LIGHT_FLICKER (113) are WRONG by that table (110 is
Light_RaiseByValue, 113 Light_Fade); nobody uses them, and this module does
not touch them.

Nothing here names a monster class or an editor number: tests scan
src/maps for those (test_akm, test_ep2_enemies, test_ep3_boss).
"""

from __future__ import annotations

# --- Action specials (g4.14.2's own table, read 2026-10-23; see above) --------
DOOR_OPEN = 11                # Door_Open (tag, speed, lighttag): stays open
FLOOR_LOWER_TO_LOWEST = 21    # Floor_LowerToLowest (tag, speed): to the lowest neighbouring floor
FLOOR_RAISE_BY_VALUE = 23     # Floor_RaiseByValue (tag, speed, height)
LIGHT_FLICKER = 115           # Light_Flicker (tag, upper, lower): not used yet
RADIUS_QUAKE = 120            # Radius_Quake (intensity, duration, damrad, tremrad, tid)

# The specials whose arg0 is a sector tag: the ones a map's tests follow to
# sectors. Radius_Quake's arg0 is its intensity, not a tag.
TAG_SPECIALS = frozenset({DOOR_OPEN, FLOOR_LOWER_TO_LOWEST, FLOOR_RAISE_BY_VALUE})
# The specials that lower a floor for good: what a map calls a sinking sector
# (a wall that falls, a barricade that drops). The tests open them by
# putting the sector's floor on its lowest neighbour's.
SINK_SPECIALS = frozenset({FLOOR_LOWER_TO_LOWEST})

# --- Speeds (gzdoom.pk3 xlat/defines.i, shipped text: F_SLOW 8, F_NORMAL 16,
# F_FAST 32, F_TURBO 64, D_SLOW 16; the unit is 1/8 map unit a tic)
DOOR_SPEED_SLOW = 16          # D_SLOW: every door of the campaign
FLOOR_SPEED_NORMAL = 16       # F_NORMAL, MAP04's gondolas: 2 units a tic
FLOOR_SPEED_FAST = 32         # F_FAST: 4 units a tic, a 64 barricade down in 16 tics
FLOOR_SPEED_TURBO = 64        # F_TURBO: 8 units a tic, a wall 144 high down in 18 tics: a collapse

# --- Radius_Quake ----------------------------------------------------------------
# tid 0: the quake is centred on the activator, the player who picked the
# thing up. damrad 0: nobody is hurt (Hexen's quake hurts what stands inside
# damrad). tremrad, in 64-unit cells: how far from the centre it is felt.
# Its sound is `world/quake`, which only gzdoom.pk3's Hexen filter defines
# (`$alias world/quake Earthquake`): in Doom the shake is SILENT (NOT
# VERIFIED; the moving floors' own grinding is the sound these events rely
# on). The quake's look is NOT VERIFIED either: the PM's engine pass.
QUAKE_TID_ACTIVATOR = 0
QUAKE_NO_DAMAGE = 0
QUAKE_MAX_INTENSITY = 9       # the engine clamps 1..9

# --- Riders ----------------------------------------------------------------------
# A rider lies this far from the key along one axis: well inside the 36
# units (player radius 16 + an item's 20) at which both are touched, and
# far enough apart that the two sprites do not fight for the same pixels.
RIDER_OFFSET = 8
PICKUP_REACH = 16 + 20


def args5(args: tuple[int, ...]) -> tuple[int, int, int, int, int]:
    """A special's arguments padded to UDMF's five; more than five is an error."""
    args = tuple(int(a) for a in args)
    if len(args) > 5:
        raise ValueError(f"a special takes at most 5 arguments, got {args}")
    return args + (0,) * (5 - len(args))   # type: ignore[return-value]


def special_fields(special: int, args: tuple[int, ...]) -> dict:
    """The UDMF thing fields that make a thing run `special(args)` when it is
    picked up (or, on a monster, when it dies): `special` and `arg0..arg4`."""
    if special <= 0:
        raise ValueError(f"no special {special}")
    return {"special": int(special), **{f"arg{i}": a for i, a in enumerate(args5(args))}}


def quake(intensity: int, duration: int, tremor_cells: int) -> tuple[int, tuple[int, ...]]:
    """Radius_Quake on the activator, hurting nobody: (special, args)."""
    if not 1 <= intensity <= QUAKE_MAX_INTENSITY:
        raise ValueError(f"quake intensity {intensity} outside 1..{QUAKE_MAX_INTENSITY}")
    if duration <= 0 or tremor_cells <= 0:
        raise ValueError("a quake needs a duration and a tremor radius")
    return RADIUS_QUAKE, (intensity, duration, QUAKE_NO_DAMAGE, tremor_cells, QUAKE_TID_ACTIVATOR)


def rider_spot(key_spot: tuple[int, int], dx: int = 0, dy: int = 0) -> tuple[int, int]:
    """Where a rider lies: the key's spot moved by (dx, dy), each at most
    RIDER_OFFSET, so the key and its riders are taken together."""
    if max(abs(dx), abs(dy)) > RIDER_OFFSET:
        raise ValueError(f"a rider {dx, dy} from its key is too far to be taken with it")
    return key_spot[0] + dx, key_spot[1] + dy
