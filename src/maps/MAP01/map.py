"""MAP01 "Zarya-7 Cosmodrome" - v2, light and detail.

Design document: docs/levels/MAP01-zarya-7.md. This file builds v2 of its
section 12 version plan (build record in section 16): the v1 map (textured
and signposted, section 15) with the light table of section 6, real switch
faces, the gate made legible, the three secrets flagged, and the approved
crates and lockers. Still no enemies and no items: that is v3.

v2 exists, first of all, to answer the v1 playtest (CEO, 2026-10-13). He
found SW-A and pressed it, but it wore SDDOOR1: no click, no change, so he
took it for a broken door and kept looking. Later he found D4 open without
knowing why. The fix, in the order the player meets it:

* the fuel-bay mouth is the brightest thing on the hangar's west side, at
  the end of a red wall left in shadow;
* next to the mouth, a window shows a lit alcove with a switch in it;
* the switch is a real switch (SDSW1A, a knife switch: "power"), alone in a
  64x128 alcove lit at the map's top value, and it clicks and flips;
* standing at it, the window on the player's right frames D4 across the
  hangar, dark in its unlit recess: the locked thing seen from the thing
  that unlocks it;
* the switch's one line opens D4 AND, through Door_Open's light-tag
  argument, brings up the light in D4's recess and in the control booth.

Geometry is painted, not wound by hand: `GridMap` (tools/sdbuild/udmf.py)
takes axis-aligned rectangles of sector and works out every shared edge,
every wall and every winding. Engine specials, and how each number was
verified, are in the design document's section 9.

Run it:
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP01 tools/run.sh
"""

from __future__ import annotations

from sdbuild.udmf import (
    SECTOR_SPECIAL_LIGHT_FLICKER,
    SECTOR_SPECIAL_SECRET,
    GridMap,
    LineStyle,
    Sector,
    TextMap,
    Thing,
    door_open_style,
    door_raise_style,
    exit_switch_style,
    remote_door_style,
    switch_door_open_style,
)

MAP_NAME = "MAP01"

# --- The approved set -----------------------------------------------------
# Every name below is a lump listed as approved in docs/art/TEXTURE-INDEX.md
# and packed into the PK3 from assets/. Nothing else is referenced.
CONC = "SDCONC1"      # prefab concrete panels - the default wall of the base
STRIPE = "SDCONC2"    # the same concrete with the worn red route stripe
STEEL = "SDSTEL1"     # military-green riveted plate - machinery and function
DOOR = "SDDOOR1"      # bunker door leaf, 128x128, hazard stripe along its foot
PLAQUE = "SDSTAR1"    # 128x128 emblem plaque
LENIN = "SDPOSTR1"    # 128x256 Lenin poster
MURAL = "SDPOSTR2"    # 128x128 cosmonautics mural

LANE = "SDFLR1"       # hangar concrete with the yellow lane line
CONCRETE_FLOOR = "SDFLR2"
TILE = "SDFLR3"       # grey Soviet floor tiles: the inhabited half of the base
CEIL_LAMP = "SDCEIL1"
CEIL = "SDCEIL2"

# Batch 3 props (approved 2026-10-13, D29).
CRATE_FACE = "SDCRAT1"   # 64x64: one crate; also the ends of a long crate
CRATE_LONG = "SDCRAT2"   # 128x64: the long side of a long crate
CRATE_TOP = "SDCRTOP1"   # 64x64 flat: the lid
LOCKER = "SDLOCK1"       # 64x128: a barracks locker, one per 64 of wall

# Switches (batch 2, approved 2026-10-13; src/lumps/ANIMDEFS pairs each OFF
# face with its ON twin, MOD-SPEC 4.3). Three switches, four variants: one
# each, chosen for what the switch DOES.
SW_A_FACE = "SDSW1A"     # knife switch (rubilnik): main power to the gate
SW_B_FACE = "SDSW1B"     # domed push button: a control-booth console
EXIT_FACE = "SDSW1D"     # hazard panel: the lift down into the metro
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64        # every SDSW1x is 64x128: one face per 64 of line
SWITCH_HEIGHT = 128

# `PRESSABLE` is the name tests/test_udmf.py uses for the door leaf, which is
# only ever allowed on a door the player can press or on a leaf a switch
# opens. Since v2 no switch wears it: switches wear SWITCH_FACES.
PRESSABLE = DOOR

# --- Light (design section 6; the owner pins the numbers) -----------------
# Range 96..192. A lamp sector is exactly LAMP_STEP over its room. 192, the
# top of the range, is for the hangar lamps and for the BEACONS that say
# "go here": the fuel-bay mouth, the window beside it, and - once SW-A is
# thrown - SW-A's alcove and D4's recess.
LIGHT_MIN = 96
LIGHT_MAX = 192
LAMP_STEP = 16
LIGHT_DORM = 144
LIGHT_WASHROOM = 112
LIGHT_SECRET = 96          # S1 and the S3 sump
LIGHT_CORRIDOR = 128       # Z3
LIGHT_KOMNATA = 160
LIGHT_MURAL = 176          # the niche: the mural is meaning, lit as such
LIGHT_SERVICE = 112        # Z5
LIGHT_FLICKER = 144        # Z5's failing lamp: flickers down to Z5's 112
LIGHT_GUARD = 128
LIGHT_HANGAR = 176
LIGHT_WEST_BAY = 144       # the red wall's strip of floor, in shadow...
LIGHT_BEACON = 192         # ...so the lit mouth at its end reads at once
LIGHT_GATE_DEAD = 112      # D4's recess before SW-A: an unpowered gate
LIGHT_SWITCH_READY = 160   # SW-A's alcove before it is thrown: the bay's
                           # brightest spot; it rises to LIGHT_BEACON when it is
LIGHT_FUEL_BAY = 112
LIGHT_CATWALK = 160
LIGHT_BOOTH_DARK = 96      # the booth before SW-A...
LIGHT_BOOTH_LIT = 160      # ...and after: the value its window holds
LIGHT_AIRLOCK = 128
LIGHT_EXIT = 96            # the darkest room: MAP02 starts here
LIGHT_EXIT_SWITCH = 144

# --- Sector tags ----------------------------------------------------------
# Design section 9 reserved 10 = D4, 11 = D5, 20/21 = closets and ambush
# panels, 30 = booth light. Every manual door has a tag of its own, because
# a tagged door opens from either flanking line without depending on which
# side the engine considers "front". The secret panels take 101-103.
TAG_D1_DORM_WASHROOM = 1
TAG_D2_DORM_CORRIDOR = 2
TAG_D3_KOMNATA_SERVICE = 3
TAG_D6_CATWALK_BOOTH = 6
TAG_D4_HANGAR_AIRLOCK = 10
TAG_D5_AIRLOCK_EXIT = 11
TAG_S1_LOCKER_PANEL = 101
TAG_S2_CATWALK_PANEL = 102
TAG_S3_SUMP_PANEL = 103
# 30 is the light tag of SW-A's Door_Open: every sector carrying it
# brightens, as D4 rises, to its brightest neighbour. Three sectors carry
# it: SW-A's own alcove (the lamp over the switch comes up: the feedback the
# player gets without turning his head), D4's recess (dark gate -> lit
# gate) and the control booth (dark window -> beacon). The behaviour is NOT
# VERIFIED in engine (design section 16).
TAG_LIGHT_GATE_POWER = 30

# --- Things ---------------------------------------------------------------
ED_PLAYER1_START = 1
PLAYER_START = (256, 96)
PLAYER_ANGLE = 90  # north: D2, the way out of the dorm, is straight ahead

# --- Heights --------------------------------------------------------------
# A closed door is a sector whose ceiling sits on its floor. `Door_Raise` /
# `Door_Open` then lift it to (lowest neighbouring ceiling - 4).
HANGAR_FLOOR = -32
HANGAR_CEIL = 288
SUMP_FLOOR = -96

# Every door leaf is an upper texture running from the door's own ceiling up
# to the ceiling of the room it faces. `SDDOOR1` is 128x128, so a leaf reads
# as one door only where that distance is 128. Where the room is taller the
# door gets a RECESS: a short sector in front of it, floor unchanged, ceiling
# exactly 128 above the floor.
DOOR_LEAF_HEIGHT = 128

# SW-A's alcove is a control platform one step up from the fuel bay, and its
# window onto the hangar has a sill a player cannot step over.
SWITCH_PLATFORM = 24   # the most a player steps up (Doom's 24)
WINDOW_SILL = 32       # more than a step: a window, not a doorway

# Every yellow lane below is 128 units across, not 64: SDFLR1 carries its
# line on texture columns 2..8 of a 64-wide flat, so 128 shows two lines 64
# apart - a marked traffic lane rather than a scratch.
LANE_ACROSS = {"rotationfloor": 90.0}  # a lane whose line runs east-west

# Things a player is not meant to stand in, by zone-name prefix: the two
# windows (a sill 32 high is a window, not a step) and the crates.
PROP_PREFIX = "crate_"
WINDOWS = ("booth_window", "fuel_window")


def _sector(floor: int, ceil: int, tag: int | None = None, *,
            light: int, flat: str = CONCRETE_FLOOR, ceiling: str = CEIL,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(
        texturefloor=flat,
        textureceiling=ceiling,
        heightfloor=floor,
        heightceiling=ceil,
        lightlevel=light,
        identifier=tag,
        special=special,
        extra=dict(extra or {}),
    )


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map and return it together with {zone name: sector index}.

    The name map is what lets the tests and QA talk about "the booth window"
    or "the exit lift" instead of about sector 39.
    """
    tm = TextMap(comment=f"{MAP_NAME} v2 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=CONC)
    plan: dict[str, int] = {}

    def zone(name: str, floor: int, ceil: int, rects, tag: int | None = None, *,
             light: int, flat: str = CONCRETE_FLOOR, ceiling: str = CEIL,
             wall: str | None = None, special: int = 0,
             extra: dict | None = None) -> int:
        """One named sector, painted as one or more rectangles.

        `wall` is what this sector is MADE of. Its one-sided walls wear it
        directly; on a two-sided boundary it is what the room ACROSS the
        line sees, because what that line draws is this sector's structure -
        the flank of its raised floor, the lintel under its lower ceiling.
        """
        if name in plan:
            raise ValueError(f"duplicate zone name {name!r}")
        index = tm.add_sector(_sector(floor, ceil, tag, light=light, flat=flat,
                                      ceiling=ceiling, special=special, extra=extra))
        g.paint_all(index, rects)
        if wall:
            g.set_wall(index, wall)
        plan[name] = index
        return index

    def door(name: str, floor: int, tag: int, rect, *, light: int) -> int:
        """A closed door sector (ceiling resting on the floor).

        Its own walls are the door TRACK - the strip of jamb the leaf slides
        past - so they are steel, like the leaf. Its light is what the
        doorway shows once open.
        """
        return zone(name, floor, floor, [rect], tag, light=light, wall=STEEL)

    def lamp(room: str, n: int, rect) -> int:
        """One SDCEIL1 panel = one 64x64 sector exactly LAMP_STEP over its room.

        Same floor and ceiling as the room, so all it adds is the lamp on the
        ceiling and the pool of light under it. Named `lamp_<room>_<n>` so
        the tests can find the room it belongs to.
        """
        s = tm.sectors[plan[room]]
        return zone(f"lamp_{room}_{n}", s.heightfloor, s.heightceiling, [rect],
                    light=s.lightlevel + LAMP_STEP, flat=s.texturefloor,
                    ceiling=CEIL_LAMP, extra=dict(s.extra))

    crate_faces: list[tuple[str, int, int, int, str]] = []

    def crate(name: str, room: str, rect, height: int, exposed: str) -> int:
        """A crate, or a stack of them, standing on `room`'s floor.

        `exposed` lists the sides the room can see ("nsew"); the others are
        against a wall, and the wall above the crate stays the room's own.
        Each exposed side wears the face that fits its length exactly:
        SDCRAT2 on a 128 side, SDCRAT1 on a 64 side, so no crate is ever
        cut. A stack is a taller crate: 128 of SDCRAT1 is two crates.
        """
        s = tm.sectors[plan[room]]
        x1, y1, x2, y2 = rect
        index = zone(f"{PROP_PREFIX}{name}", s.heightfloor + height, s.heightceiling, [rect],
                     light=s.lightlevel, flat=CRATE_TOP, ceiling=s.textureceiling,
                     wall=g.wall_of(plan[room]))
        sides = {"s": ("h", y1, x1, x2), "n": ("h", y2, x1, x2),
                 "w": ("v", x1, y1, y2), "e": ("v", x2, y1, y2)}
        for key in exposed:
            axis, coord, lo, hi = sides[key]
            face = {64: CRATE_FACE, 128: CRATE_LONG}[hi - lo]
            crate_faces.append((axis, coord, lo, hi, face))
        return index

    # ======================================================================
    # Act 1 - barracks.  Dorm -> washroom (+ secret locker) and dorm -> corridor
    # ======================================================================
    # Z1 dorm, the player's "before": ordinary, lit, 640 x 448, and exactly
    # 128 high, so every surface in it is one clean panel.
    zone("z1_dorm", 0, 128, [(0, 0, 640, 448)], flat=TILE, light=LIGHT_DORM)
    lamp("z1_dorm", 1, (288, 224, 352, 288))

    # D1, manual door east to the washroom, in its own recess.
    d1 = door("d1", 0, TAG_D1_DORM_WASHROOM, (640, 32, 704, 160), light=LIGHT_WASHROOM)
    zone("z2_washroom", 0, 96, [(704, 0, 896, 192)],
         flat=TILE, ceiling=CEIL_LAMP, light=LIGHT_WASHROOM)

    # S1, secret locker closet behind a push panel that stays open. The panel
    # is a steel plate in a concrete wall: that seam IS the clue (section 7).
    s1_panel = door("s1_panel", 0, TAG_S1_LOCKER_PANEL, (896, 64, 928, 128),
                    light=LIGHT_SECRET)
    zone("s1_locker", 0, 96, [(928, 32, 1024, 160)], wall=STEEL,
         light=LIGHT_SECRET, special=SECTOR_SPECIAL_SECRET)

    # D2, manual door north to the barracks corridor.
    d2 = door("d2", 0, TAG_D2_DORM_CORRIDOR, (192, 448, 320, 512), light=LIGHT_DORM)
    # Z3 corridor: where the red stripe is born. 128 wide, 448 long, 96 high,
    # with a lamp every 256: pools of light on the stripe.
    zone("z3_corridor", 0, 96, [(192, 512, 320, 960)], flat=TILE, light=LIGHT_CORRIDOR)
    lamp("z3_corridor", 1, (224, 576, 288, 640))
    lamp("z3_corridor", 2, (224, 832, 288, 896))

    # Z4 Leninskaya komnata: the only wide, tall room of the barracks.
    zone("z4_komnata", 0, 192, [(0, 960, 640, 1408)], flat=TILE, light=LIGHT_KOMNATA)
    lamp("z4_komnata", 1, (128, 1152, 192, 1216))
    lamp("z4_komnata", 2, (448, 1152, 512, 1216))
    # The mural alcove: 128x128, one tile of SDPOSTR2, lit as a shrine.
    zone("z4_mural", 0, 128, [(256, 1408, 384, 1440)],
         flat=TILE, ceiling=CEIL_LAMP, light=LIGHT_MURAL)

    # ======================================================================
    # Act 2 - service corridor, guard post, and the descent into the hangar
    # ======================================================================
    # D3's recess, on the komnata side: 192 of room, 128 of door leaf.
    zone("d3_recess", 0, DOOR_LEAF_HEIGHT, [(576, 1088, 640, 1216)],
         flat=TILE, wall=STRIPE, light=LIGHT_KOMNATA)
    d3 = door("d3", 0, TAG_D3_KOMNATA_SERVICE, (640, 1088, 704, 1216), light=LIGHT_SERVICE)
    zone("z5_service", 0, 112, [(704, 1088, 1152, 1216)], light=LIGHT_SERVICE)
    lamp("z5_service", 1, (768, 1120, 832, 1184))
    # The failing lamp: a full-width strip of corridor whose light flickers
    # at random between its own 144 and the corridor's 112 (sector special
    # dLight_Flicker, design section 9). It is ambient from the first tic and
    # needs no trigger, which is why it is a SECTOR special and not the
    # Light_Flicker LINE special. Past the guard post, before the stair.
    zone("z5_flicker", 0, 112, [(1024, 1088, 1088, 1216)], light=LIGHT_FLICKER,
         ceiling=CEIL_LAMP, special=SECTOR_SPECIAL_LIGHT_FLICKER)
    # Z5b guard post, 8 units up: in v3 this is where the IZh is.
    zone("z5b_guard", 8, 112, [(896, 1216, 1024, 1344)],
         wall=STEEL, ceiling=CEIL_LAMP, light=LIGHT_GUARD)
    # The guard's crates: one long crate along the back wall, its 128 face
    # to the doorway. The post is 104 high, so a 128 locker would be cut;
    # the lockers live in the dorm, whose wall is exactly 128.
    crate("guard", "z5b_guard", (896, 1280, 1024, 1344), 64, exposed="s")

    # ======================================================================
    # Act 3 - the hangar and everything carved out of it
    # ======================================================================
    # Painting is last-wins, so the hangar is laid down whole and everything
    # carved out of it is painted on top afterwards.
    zone("z6_hangar", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 320, 2688, 1600)], light=LIGHT_HANGAR)

    # Three steps down from the service corridor into the hangar. The
    # ceiling rises 112 -> 160 -> 224 -> 288 and the light with it.
    zone("step_down_1", -8, 112, [(1152, 1088, 1216, 1216)], light=128)
    zone("step_down_2", -16, 160, [(1216, 1088, 1280, 1216)], light=144)
    zone("step_down_3", -24, 224, [(1280, 1088, 1344, 1216)], light=160)

    # --- the yellow lanes: the fork at the foot of the entry stair ---------
    # Lane A runs east to the gate; lane B hugs the red west wall into the
    # fuel-bay mouth. v2 leaves lane B in shadow (LIGHT_WEST_BAY) so the lit
    # mouth at its end is the brightest thing on that side of the hangar.
    zone("lane_a_cross", HANGAR_FLOOR, HANGAR_CEIL, [(1344, 608, 2624, 736)],
         flat=LANE, extra=LANE_ACROSS, light=LIGHT_HANGAR)
    zone("lane_a_spur", HANGAR_FLOOR, HANGAR_CEIL, [(1344, 736, 1472, 1216)],
         flat=LANE, light=LIGHT_HANGAR)
    zone("lane_b_cross", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 1216, 1344, 1344)],
         flat=LANE, extra=LANE_ACROSS, light=LIGHT_WEST_BAY)
    zone("lane_b_spur", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 1344, 1280, 1600)],
         flat=LANE, light=LIGHT_WEST_BAY)

    # Z6a transporter cradle, a walkable island of cover at +64.
    for n, (floor, x) in enumerate(((-16, 1504), (0, 1536), (16, 1568)), start=1):
        zone(f"cradle_step_{n}", floor, HANGAR_CEIL, [(x, 960, x + 32, 1088)],
             wall=STEEL, light=LIGHT_HANGAR)
    zone("z6a_cradle", 32, HANGAR_CEIL, [(1600, 832, 2240, 1216)], wall=STEEL,
         light=LIGHT_HANGAR)

    # Eight steps up the east end of the hangar to the catwalk (+128).
    for i in range(8):
        y1 = 1184 + i * 32
        zone(f"catwalk_step_{i + 1}", -16 + i * 16, HANGAR_CEIL,
             [(2304, y1, 2560, y1 + 32)], wall=STEEL, light=LIGHT_HANGAR)

    # Z6b catwalk along the north wall, 96 up. Its front face is a 128 band
    # of plate over the hangar floor: exactly one SDSTEL1 tile.
    #
    # The design table starts it at x 1280. v1 moved it to 1472: at 1280 its
    # west end stood in the line of sight from the hangar floor to the
    # fuel-bay mouth (docs/levels/shots/2026-10-13_1009_F3_map01-v1-catwalk-screens-the-mouth.png).
    # v2 moves it again, to 1792, for the same reason one step further: the
    # sight line from SW-A's alcove, through the fuel-bay window, to D4
    # crosses the north wall's first 300 units at catwalk height. A catwalk
    # there would hide the gate from the switch that opens it.
    CATWALK_WEST = 1792
    zone("z6b_catwalk", 96, HANGAR_CEIL, [(CATWALK_WEST, 1440, 2560, 1600)],
         wall=STEEL, light=LIGHT_CATWALK)

    # D6's recess, on the catwalk side: 192 of headroom, 128 of door leaf.
    zone("d6_recess", 96, 96 + DOOR_LEAF_HEIGHT, [(2432, 1536, 2560, 1600)],
         wall=STEEL, light=LIGHT_CATWALK)

    # S2, the loose panel off the catwalk: the RPG-7 closet in v3.
    s2_panel = door("s2_panel", 96, TAG_S2_CATWALK_PANEL, (2176, 1600, 2240, 1632),
                    light=LIGHT_CATWALK)
    zone("s2_closet", 96, 192, [(2112, 1632, 2304, 1792)], wall=STEEL,
         light=LIGHT_GUARD, special=SECTOR_SPECIAL_SECRET)

    # --- the hangar lamps ------------------------------------------------
    # The design's grid is 6 x 2 on a 256 pitch. The south row is whole; in
    # the north row two cells fall on the fork lane and on the catwalk stair,
    # so it keeps four, the last pulled 64 west off the stair's flank. Each
    # lamp is a 64x64 pool of light on bare floor.
    for n, x in enumerate((1216, 1472, 1728, 1984, 2240, 2496), start=1):
        lamp("z6_hangar", n, (x, 448, x + 64, 512))
    for n, x in enumerate((1472, 1728, 1984, 2176), start=7):
        lamp("z6_hangar", n, (x, 1280, x + 64, 1344))

    # --- the crate piles: the hangar's low cover --------------------------
    # All free-standing, in the south half (v0's "empty 1536 x 768") or
    # between the cradle and the catwalk, and none on the sight line from
    # SW-A to D4 or from the bottom step to the fuel-bay mouth (tested).
    crate("h1", "z6_hangar", (1216, 352, 1344, 416), 64, exposed="nsew")
    crate("h2", "z6_hangar", (1792, 352, 1920, 416), 64, exposed="nsw")
    crate("h3_stack", "z6_hangar", (1920, 352, 1984, 416), 128, exposed="nsew")
    crate("h4", "z6_hangar", (2368, 352, 2496, 416), 64, exposed="nsew")
    crate("h5", "z6_hangar", (2112, 1344, 2176, 1408), 64, exposed="nsew")

    # ======================================================================
    # Act 3b - fuel bay (SW-A) and the sump secret under it
    # ======================================================================
    # A short passage through the hangar's north wall; its 128 lintel is one
    # exact tile of red-striped concrete. v2 lights it as a beacon.
    zone("fuel_passage", HANGAR_FLOOR, 160, [(1152, 1600, 1280, 1664)],
         flat=LANE, wall=STRIPE, light=LIGHT_BEACON)
    zone("z7_fuel_bay", HANGAR_FLOOR, 160, [(1152, 1664, 1600, 1984)],
         wall=STEEL, light=LIGHT_FUEL_BAY)

    # --- SW-A's alcove and the window: the v1 playtest's answer -----------
    # In v1 SW-A was on the bay's back wall, facing away from everything it
    # did. v2 moves it into an alcove cut through the bay's SOUTH wall, next
    # to the mouth, and makes the alcove's whole south side a window onto
    # the hangar:
    #
    #   * from the hangar, walking up the red wall, the window shows a lit
    #     alcove with a switch in it beside the lit mouth: anticipation;
    #   * at the switch the player faces east, and the window on his right
    #     frames D4, dark in its recess, ~37 degrees off his line of sight;
    #   * pressing it opens D4 and lights its recess (TAG_LIGHT_GATE_POWER),
    #     which he can watch through the same window.
    #
    # The alcove: 128 x 64, one step (24) up from the bay - a control
    # platform - with its ceiling 128 above its floor, so SW-A on its east
    # wall is exactly one 64x128 switch face. The step is what lets the eye
    # clear the transporter cradle on the way to D4: from the bay's floor
    # the cradle hides the lower half of the gate.
    alcove_floor = HANGAR_FLOOR + SWITCH_PLATFORM
    #
    # It carries the light tag: lit LIGHT_SWITCH_READY (the bay's brightest
    # spot) until SW-A is thrown, then up to its brightest neighbour, the
    # window. That is the change the player sees while still facing the
    # switch; D4 sits ~37 degrees to his right and from the back corner of
    # the alcove the switch's own wall hides it (design section 16).
    zone("z7_switch_alcove", alcove_floor, alcove_floor + SWITCH_HEIGHT,
         [(1344, 1600, 1472, 1664)], TAG_LIGHT_GATE_POWER, wall=STEEL,
         ceiling=CEIL_LAMP, light=LIGHT_SWITCH_READY)
    # The window's sill: a 16-deep strip on the hangar side, WINDOW_SILL over
    # the alcove (and more over the hangar) - more than a player steps up,
    # so it is a window and not a doorway - open to the alcove's ceiling. It
    # runs 64 further east than the alcove because the line to D4 leaves it
    # heading south-east. It is lit as a beacon: from the hangar its sill
    # and lintel frame the window in light, next to the lit mouth.
    zone("fuel_window", alcove_floor + WINDOW_SILL, alcove_floor + SWITCH_HEIGHT,
         [(1344, 1584, 1536, 1600)], light=LIGHT_BEACON)

    # The second yellow lane of section 7: inside the bay it runs west and
    # stops dead at the wall the sump panel is in.
    zone("s3_lane", HANGAR_FLOOR, 160, [(1152, 1728, 1280, 1856)],
         flat=LANE, wall=STEEL, extra=LANE_ACROSS, light=LIGHT_FUEL_BAY)

    s3_panel = door("s3_panel", HANGAR_FLOOR, TAG_S3_SUMP_PANEL, (1120, 1728, 1152, 1792),
                    light=LIGHT_FUEL_BAY)
    # Four 16-unit steps down to the sump; the stairwell is ceilinged at 64
    # so the panel's doorway opens tall enough (design section 14, dev. 4).
    zone("sump_step_1", -48, 64, [(1088, 1728, 1120, 1792)], wall=STEEL, light=LIGHT_FUEL_BAY)
    zone("sump_step_2", -64, 64, [(1056, 1728, 1088, 1792)], wall=STEEL, light=LIGHT_SECRET)
    zone("sump_step_3", -80, 64, [(1024, 1728, 1056, 1792)], wall=STEEL, light=LIGHT_SECRET)
    zone("s3_sump", SUMP_FLOOR, 0, [(896, 1664, 1024, 1856)],
         light=LIGHT_SECRET, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # Act 4 - control booth (SW-B)
    # ======================================================================
    d6 = door("d6", 96, TAG_D6_CATWALK_BOOTH, (2432, 1600, 2560, 1664), light=LIGHT_FLICKER)
    # Dark until SW-A: it carries the light tag, so as D4 rises it comes up
    # to its brightest neighbour, the window at LIGHT_BOOTH_LIT.
    zone("z9_booth", 96, 224, [
        (2560, 1616, 2688, 1664),
        (2432, 1664, 2688, 1856),
    ], TAG_LIGHT_GATE_POWER, flat=TILE, ceiling=CEIL_LAMP, wall=STEEL,
        light=LIGHT_BOOTH_DARK)
    # The booth window: a sill 32 above the booth floor and 160 above the
    # hangar floor. Its own light is the value the booth rises to.
    zone("booth_window", 128, 224, [(2560, 1600, 2688, 1616)],
         flat=TILE, ceiling=CEIL_LAMP, wall=STEEL, light=LIGHT_BOOTH_LIT)

    # ======================================================================
    # Act 5 - the two-leaf airlock and the exit lift
    # ======================================================================
    # D4's recess, on the hangar side: the gate is a 256-wide pair of leaves
    # under a lintel, framed in red. v2 makes it the gate's power indicator:
    # dark (unpowered) until SW-A; it carries the light tag, so as D4 rises
    # it comes up to its brightest neighbour, D4's own sector at LIGHT_BEACON.
    zone("d4_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
         [(2624, 544, 2688, 800)], TAG_LIGHT_GATE_POWER, wall=STRIPE,
         light=LIGHT_GATE_DEAD)
    # D4, 256 wide, remote: no use-special on its lines - it is the gate.
    d4 = door("d4", HANGAR_FLOOR, TAG_D4_HANGAR_AIRLOCK, (2688, 544, 2752, 800),
              light=LIGHT_BEACON)
    zone("z8_airlock", HANGAR_FLOOR, 96, [(2752, 544, 2912, 800)], wall=STEEL,
         light=LIGHT_AIRLOCK)
    # D5, 128 wide, the inner leaf; opened for good by SW-B in the booth.
    d5 = door("d5", HANGAR_FLOOR, TAG_D5_AIRLOCK_EXIT, (2912, 608, 2944, 736),
              light=LIGHT_AIRLOCK)
    # Z10, the service lift shaft, exactly 256 high: Lenin's height.
    zone("z10_exit", HANGAR_FLOOR, 224, [(2944, 480, 3264, 864)], light=LIGHT_EXIT)
    # The exit switch's niche in the east wall: on the 256-high wall the
    # face would tile twice. 64 x 128, one face, and the only lit thing in
    # the darkest room of the map.
    zone("z10_exit_niche", HANGAR_FLOOR, HANGAR_FLOOR + SWITCH_HEIGHT,
         [(3264, 608, 3296, 672)], ceiling=CEIL_LAMP, light=LIGHT_EXIT_SWITCH)
    # ...and D5's recess on the lift-room side, painted after the lift room.
    zone("d5_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
         [(2944, 608, 3008, 736)], wall=STEEL, light=LIGHT_EXIT)

    # ======================================================================
    # Doors, switches and the exit
    # ======================================================================
    # ORDER MATTERS from here down. GridMap resolves a segment with the FIRST
    # rule that covers it, so the specific ones (a door leaf, a switch, a
    # poster, a crate face) are registered before the broad wall runs.
    #
    # Both flanking lines of every manual door carry the special, wound so
    # the door sector is on the BACK side (a `playeruse` special fires only
    # from the front).
    for tag, door_sector, segments in (
        (TAG_D1_DORM_WASHROOM, d1, [("v", 640, 32, 160), ("v", 704, 32, 160)]),
        (TAG_D2_DORM_CORRIDOR, d2, [("h", 448, 192, 320), ("h", 512, 192, 320)]),
        (TAG_D3_KOMNATA_SERVICE, d3, [("v", 640, 1088, 1216), ("v", 704, 1088, 1216)]),
        # D6's east side meets the booth from y 1616 up; below that it meets
        # the window sector, which no player can stand in.
        (TAG_D6_CATWALK_BOOTH, d6, [("h", 1600, 2432, 2560), ("v", 2560, 1616, 1664)]),
    ):
        style = door_raise_style(tag, door_sector, texture=DOOR)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    # The three secret panels: push once, open for good. Plate, not a door
    # leaf: a secret that advertises itself is a corridor.
    for tag, door_sector, segments in (
        (TAG_S1_LOCKER_PANEL, s1_panel, [("v", 896, 64, 128), ("v", 928, 64, 128)]),
        (TAG_S2_CATWALK_PANEL, s2_panel, [("h", 1600, 2176, 2240), ("h", 1632, 2176, 2240)]),
        (TAG_S3_SUMP_PANEL, s3_panel, [("v", 1152, 1728, 1792), ("v", 1120, 1728, 1792)]),
    ):
        style = door_open_style(tag, door_sector, texture=STEEL)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    # D4 and D5 are opened only by their switches, so they carry no special
    # of their own - but their leaves still have to look like doors.
    for door_sector, segments in (
        (d4, [("v", 2688, 544, 800), ("v", 2752, 544, 800)]),
        (d5, [("v", 2912, 608, 736), ("v", 2944, 608, 736)]),
    ):
        style = remote_door_style(door_sector, texture=DOOR)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    # The three switches. Each is ONE face: a 64-long one-sided line on a
    # wall exactly 128 high, so it never tiles, and each flips to its SDSW2x
    # twin when used (src/lumps/ANIMDEFS).
    #
    # SW-A, east wall of its alcove: opens D4 for good and, through
    # Door_Open's light-tag argument, powers the light in D4's recess and
    # the booth. ONE-SHOT, so it stays on SDSW2A: a repeatable switch face
    # pops back to OFF after a second, which on the switch that opens the
    # gate would read "it switched itself off again". Door_Open cannot be
    # undone, so one press can never consume the gate (design section 4).
    g.style_v(1472, 1600, 1600 + SWITCH_WIDTH, switch_door_open_style(
        TAG_D4_HANGAR_AIRLOCK, texture=SW_A_FACE,
        lighttag=TAG_LIGHT_GATE_POWER, repeatable=False))
    # SW-B, north wall of the control booth (128 high): opens D5 for good.
    g.style_h(1856, 2528, 2528 + SWITCH_WIDTH, switch_door_open_style(
        TAG_D5_AIRLOCK_EXIT, texture=SW_B_FACE, repeatable=False))
    # The exit, at the back of its niche in the lift shaft's east wall.
    g.style_v(3296, 608, 608 + SWITCH_WIDTH, exit_switch_style(texture=EXIT_FACE))

    # --- the crate faces, and the dorm lockers ----------------------------
    # A crate side hangs from the crate's top edge (peg_bottom=False, see
    # GridMap) so the crate is whole whatever the ceiling above it.
    for axis, coord, lo, hi, face in crate_faces:
        (g.style_v if axis == "v" else g.style_h)(
            coord, lo, hi, LineStyle(texture=face, peg_bottom=False))
    # Four lockers on the dorm's west wall: the dorm is exactly 128 high and
    # SDLOCK1 is 64x128, so 256 of wall is four whole lockers.
    g.style_v(0, 64, 320, LineStyle(texture=LOCKER))

    # --- the three pictures ----------------------------------------------
    # Each one is exactly as wide and as tall as its wall, so it appears
    # once, whole, with no offset.
    g.style_h(448, 320, 448, LineStyle(texture=PLAQUE))
    g.style_h(1440, 256, 384, LineStyle(texture=MURAL))
    g.style_h(864, 3072, 3200, LineStyle(texture=LENIN))

    # --- the red route ----------------------------------------------------
    # One continuous marking from the barracks to the fuel bay, plus the
    # frame around D4. Registered last so anything specific on the same
    # wall run wins over it.
    g.style_v(192, 512, 960, LineStyle(texture=STRIPE))      # Z3, both walls
    g.style_v(320, 512, 960, LineStyle(texture=STRIPE))
    g.style_v(640, 960, 1088, LineStyle(texture=STRIPE))     # Z4, either side of D3
    g.style_v(640, 1216, 1408, LineStyle(texture=STRIPE))
    g.style_h(1088, 704, 1152, LineStyle(texture=STRIPE))    # Z5, both walls
    g.style_h(1216, 704, 896, LineStyle(texture=STRIPE))
    g.style_h(1216, 1024, 1152, LineStyle(texture=STRIPE))
    # The hangar's west wall, from the foot of the entry stair north to the
    # fuel-bay mouth: "the route continues over here", without words.
    g.style_v(1152, 1216, 1600, LineStyle(texture=STRIPE))
    # ...and the lintel over the mouth itself.
    g.style_h(1600, 1152, 1280, LineStyle(texture=STRIPE))
    # D4's frame: the lintel over the recess and both of its jambs.
    g.style_v(2624, 544, 800, LineStyle(texture=STRIPE))
    g.style_h(544, 2624, 2688, LineStyle(texture=STRIPE))
    g.style_h(800, 2624, 2688, LineStyle(texture=STRIPE))

    # NOT BUILT (design section 13, point 5, open with the CEO): a strip of
    # night sky over the hangar is one more rectangle painted over the
    # hangar with ceiling flat F_SKY1, the IWAD's sky marker (MAPINFO already
    # names SKY1, MOD-SPEC 5). Nothing above would have to move for it.
    g.build()

    tm.add_thing(
        Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START, angle=PLAYER_ANGLE)
    )

    return tm, plan


def build_textmap() -> TextMap:
    return build_plan()[0]


def lumps() -> list[tuple[str, bytes]]:
    """Return the WAD lumps in directory order (contract used by the build)."""
    return [
        (MAP_NAME, b""),                          # map marker
        ("TEXTMAP", build_textmap().to_bytes()),  # UDMF map body
        ("ENDMAP", b""),                          # end-of-map marker
    ]


# Every lump name this map may put in a sidedef or a sector, for the tests
# and for criterion G3-3. Nothing outside this set reaches the TEXTMAP.
WALL_TEXTURES = (CONC, STRIPE, STEEL, DOOR, PLAQUE, LENIN, MURAL,
                 CRATE_FACE, CRATE_LONG, LOCKER) + SWITCH_FACES
FLAT_TEXTURES = (LANE, CONCRETE_FLOOR, TILE, CEIL_LAMP, CEIL, CRATE_TOP)
