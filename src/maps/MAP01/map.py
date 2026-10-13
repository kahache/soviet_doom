"""MAP01 "Zarya-7 Cosmodrome" - v1, the textured floor plan.

Design document (approved as text by the CEO): docs/levels/MAP01-zarya-7.md.
This file builds **v1** of its section 12 version plan: the v0 geometry
dressed in the approved "Soviet base" set, zone by zone, with the alignment
pass done. Light is still flat 160 (v2), there are still no enemies and no
items (v3).

v1 exists to answer ONE question, the v0 playtest finding at the end of the
design document. The CEO walked v0 and wrote: "no pude probar el nivel
porque las paredes no se abrian. Utilice IDCLIP." The doors were never
broken; what he hit was D4, the hangar gate, which by design has no special
of its own and is opened by SW-A in the fuel bay. In a grey box with no
light and no signage, a gate that does not answer reads as a wall. So v1 is
not "nicer walls": v1 is the signposting pass, and its gate criterion is
that a player who has never seen the map reaches the fuel bay without being
told. The three tools it uses, all of them texture:

* the **red stripe** (`SDCONC2`) is the base's route. It is born in the
  barracks corridor, runs both walls of the service corridor, turns the
  corner onto the hangar's west wall and ends on the lintel over the
  fuel-bay mouth. It also frames D4, because D4 is on the route too - just
  not yet.
* the **yellow lane** (`SDFLR1`) is the hangar's traffic. It forks at the
  foot of the entry stair: one branch east to D4, one branch north-west
  into the fuel bay. Two ways on, both marked; the player chooses and the
  map tells him which one answers.
* the **door recesses**. A 128-high lintel over every door leaf, so
  `SDDOOR1` tiles exactly once and a closed door looks like a closed door
  from across a 1536-unit hangar instead of like tiled grey.

Coordinates come from the design's section 3 table; deviations are recorded
in the zone's comment and in section 15 of the design document.

Geometry is painted, not wound by hand: `GridMap` (tools/sdbuild/udmf.py)
takes axis-aligned rectangles of sector and works out every shared edge,
every wall and every winding. See docs/levels/MAP01-zarya-7.md section 9 for
the engine specials used and how each number was verified.

Run it:
    python3 tools/build.py && MAP=MAP01 tools/run.sh
"""

from __future__ import annotations

from sdbuild.udmf import (
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
# Every name below is a lump of the "Soviet base" batch, listed in
# docs/art/TEXTURE-INDEX.md and packed into the PK3 from assets/. Nothing
# else is referenced: no IWAD texture survives v1.
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

LIGHT = 160  # still flat across the whole map; the light design is v2

# `SDSWT1`/`SDSWT2` do not exist yet - design document request A3, in hand
# with the art director. Until they land, every surface that is a SWITCH
# rather than a door wears the door leaf as a stand-in, which is a lie we
# know about: it reads "door", not "lever". Swapping it is one constant.
SWITCH_PLACEHOLDER = DOOR

# `PRESSABLE` is the name tests/test_udmf.py uses for the texture that is
# only ever allowed on a surface the player can press.
PRESSABLE = DOOR

# --- Sector tags ----------------------------------------------------------
# Design section 9 reserved 10 = D4, 11 = D5, 20/21 = closets and ambush
# panels, 30 = booth light. v0 additionally needs a tag per manual door,
# because a tagged door opens from either flanking line without depending on
# which side the engine considers "front". 1-9 were free; the secret panels
# take 101-103, well clear of the reserved block.
TAG_D1_DORM_WASHROOM = 1
TAG_D2_DORM_CORRIDOR = 2
TAG_D3_KOMNATA_SERVICE = 3
TAG_D6_CATWALK_BOOTH = 6
TAG_D4_HANGAR_AIRLOCK = 10
TAG_D5_AIRLOCK_EXIT = 11
TAG_S1_LOCKER_PANEL = 101
TAG_S2_CATWALK_PANEL = 102
TAG_S3_SUMP_PANEL = 103

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
# exactly 128 above the floor. The recess is also what makes a shut door
# legible at distance - a lintel casts the door into a frame.
DOOR_LEAF_HEIGHT = 128

# Every yellow lane below is 128 units across, not 64. SDFLR1 carries its
# line on texture columns 2..8 of a 64-wide flat, so a 64-wide lane shows
# one line and a 128-wide lane shows two, 64 apart: a marked traffic lane
# rather than a scratch, legible from the far side of the hangar, and the
# same either way round whichever way `rotationfloor` turns the flat.
LANE_ACROSS = {"rotationfloor": 90.0}  # a lane whose line runs east-west


def _sector(floor: int, ceil: int, tag: int | None = None, *,
            flat: str = CONCRETE_FLOOR, ceiling: str = CEIL,
            extra: dict | None = None) -> Sector:
    return Sector(
        texturefloor=flat,
        textureceiling=ceiling,
        heightfloor=floor,
        heightceiling=ceil,
        lightlevel=LIGHT,
        identifier=tag,
        extra=dict(extra or {}),
    )


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map and return it together with {zone name: sector index}.

    The name map is what lets the tests and QA talk about "the booth window"
    or "the exit lift" instead of about sector 39.
    """
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=CONC)
    plan: dict[str, int] = {}

    def zone(name: str, floor: int, ceil: int, rects, tag: int | None = None, *,
             flat: str = CONCRETE_FLOOR, ceiling: str = CEIL,
             wall: str | None = None, extra: dict | None = None) -> int:
        """One named sector, painted as one or more rectangles.

        `wall` is what this sector is MADE of. Its one-sided walls wear it
        directly; on a two-sided boundary it is what the room ACROSS the
        line sees, because what that line draws is this sector's structure -
        the flank of its raised floor, the lintel under its lower ceiling.
        So `wall=STEEL` on the catwalk gives the hangar a plate soffit under
        a concrete wall, which is the right way round.
        """
        if name in plan:
            raise ValueError(f"duplicate zone name {name!r}")
        index = tm.add_sector(_sector(floor, ceil, tag, flat=flat, ceiling=ceiling, extra=extra))
        g.paint_all(index, rects)
        if wall:
            g.set_wall(index, wall)
        plan[name] = index
        return index

    def door(name: str, floor: int, tag: int, rect) -> int:
        """A closed door sector (ceiling resting on the floor).

        Its own walls are the door TRACK - the strip of jamb the leaf slides
        past - so they are steel, like the leaf.
        """
        return zone(name, floor, floor, [rect], tag, wall=STEEL)

    # ======================================================================
    # Act 1 - barracks.  Dorm -> washroom (+ secret locker) and dorm -> corridor
    # ======================================================================
    # Z1 dorm, the player's "before": ordinary, lit, 640 x 448, and exactly
    # 128 high, so every surface in it is one clean panel.
    z1_dorm = zone("z1_dorm", 0, 128, [(0, 0, 640, 448)], flat=TILE)

    # D1, manual door east to the washroom. 128 wide, in its own recess, so
    # the dorm and the washroom never share any other edge.
    d1 = door("d1", 0, TAG_D1_DORM_WASHROOM, (640, 32, 704, 160))
    z2_washroom = zone("z2_washroom", 0, 96, [(704, 0, 896, 192)],
                       flat=TILE, ceiling=CEIL_LAMP)

    # S1, secret locker closet behind a push panel that stays open. The panel
    # is a steel plate in a concrete wall: that seam IS the clue (section 7).
    s1_panel = door("s1_panel", 0, TAG_S1_LOCKER_PANEL, (896, 64, 928, 128))
    s1_locker = zone("s1_locker", 0, 96, [(928, 32, 1024, 160)], wall=STEEL)

    # D2, manual door north to the barracks corridor.
    d2 = door("d2", 0, TAG_D2_DORM_CORRIDOR, (192, 448, 320, 512))
    # Z3 corridor: where the red stripe is born. 128 wide, 448 long, 96 high,
    # so the stripe sits at 59..70 - chest height - on both walls.
    z3_corridor = zone("z3_corridor", 0, 96, [(192, 512, 320, 960)], flat=TILE)

    # Z4 Leninskaya komnata: the only wide, tall room of the barracks.
    # Opens straight off the corridor - no door, the room is the reward.
    z4_komnata = zone("z4_komnata", 0, 192, [(0, 960, 640, 1408)], flat=TILE)
    # The mural alcove. SDPOSTR2 is 128x128 and the komnata is 192 high, so
    # on a flat wall the mural would tile one and a half times. A 128-wide,
    # 128-high niche in the north wall gives it exactly one tile and turns a
    # wall decoration into a shrine - which is what a Leninskaya komnata is.
    z4_mural = zone("z4_mural", 0, 128, [(256, 1408, 384, 1440)],
                    flat=TILE, ceiling=CEIL_LAMP)

    # ======================================================================
    # Act 2 - service corridor, guard post, and the descent into the hangar
    # ======================================================================
    # D3's recess, on the komnata side: 192 of room, 128 of door leaf.
    d3_recess = zone("d3_recess", 0, DOOR_LEAF_HEIGHT, [(576, 1088, 640, 1216)],
                     flat=TILE, wall=STRIPE)
    d3 = door("d3", 0, TAG_D3_KOMNATA_SERVICE, (640, 1088, 704, 1216))
    z5_service = zone("z5_service", 0, 112, [(704, 1088, 1152, 1216)])
    # Z5b guard post, 8 units up: in v3 this is where the IZh is. Steel =
    # function: this is the room that gives you a weapon.
    z5b_guard = zone("z5b_guard", 8, 112, [(896, 1216, 1024, 1344)],
                     wall=STEEL, ceiling=CEIL_LAMP)

    # ======================================================================
    # Act 3 - the hangar and everything carved out of it
    # ======================================================================
    # Painting is last-wins, so the hangar is laid down whole and every
    # stair, the cradle, the catwalk and every yellow lane are then painted
    # ON TOP of it. Anything carved out of the hangar must come after this.
    z6_hangar = zone("z6_hangar", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 320, 2688, 1600)])

    # Three steps down from the service corridor into the hangar, each with
    # a higher ceiling than the last: the space opens up ahead of the player
    # before he is in it. Without them the 32-unit drop would be one-way.
    step_down_1 = zone("step_down_1", -8, 112, [(1152, 1088, 1216, 1216)])
    step_down_2 = zone("step_down_2", -16, 160, [(1216, 1088, 1280, 1216)])
    step_down_3 = zone("step_down_3", -24, 224, [(1280, 1088, 1344, 1216)])

    # --- the yellow lanes, and the fork that is the whole point of v1 -----
    # The player leaves the bottom step heading east at x = 1344. Lane A is
    # under his feet the moment he does, running east to the gate. Lane B
    # leaves the same spot to his left, hugs the west wall - the red-striped
    # one - and disappears into the fuel-bay mouth. Two destinations, both
    # marked on the floor, before he has taken a step into the room.
    lane_a_cross = zone("lane_a_cross", HANGAR_FLOOR, HANGAR_CEIL,
                        [(1344, 608, 2624, 736)], flat=LANE, extra=LANE_ACROSS)
    lane_a_spur = zone("lane_a_spur", HANGAR_FLOOR, HANGAR_CEIL,
                       [(1344, 736, 1472, 1216)], flat=LANE)
    lane_b_cross = zone("lane_b_cross", HANGAR_FLOOR, HANGAR_CEIL,
                        [(1152, 1216, 1344, 1344)], flat=LANE, extra=LANE_ACROSS)
    lane_b_spur = zone("lane_b_spur", HANGAR_FLOOR, HANGAR_CEIL,
                       [(1152, 1344, 1280, 1600)], flat=LANE)

    # Z6a transporter cradle, a walkable island of cover at +64 over the
    # floor, climbed by three steps on its west side and dropped off from
    # any of its four sides. Steel, like everything the base services.
    cradle_step_1 = zone("cradle_step_1", -16, HANGAR_CEIL, [(1504, 960, 1536, 1088)], wall=STEEL)
    cradle_step_2 = zone("cradle_step_2", 0, HANGAR_CEIL, [(1536, 960, 1568, 1088)], wall=STEEL)
    cradle_step_3 = zone("cradle_step_3", 16, HANGAR_CEIL, [(1568, 960, 1600, 1088)], wall=STEEL)
    z6a_cradle = zone("z6a_cradle", 32, HANGAR_CEIL, [(1600, 832, 2240, 1216)], wall=STEEL)

    # Eight steps up the east end of the hangar to the catwalk (+128).
    catwalk_steps = []
    for i in range(8):
        y1 = 1184 + i * 32
        catwalk_steps.append(
            zone(f"catwalk_step_{i + 1}", -16 + i * 16, HANGAR_CEIL,
                 [(2304, y1, 2560, y1 + 32)], wall=STEEL)
        )

    # Z6b catwalk along the north wall, 96 up, overlooking the whole hangar.
    # Its front face is a 128-high band of plate over the hangar floor:
    # exactly one SDSTEL1 tile, which is why it is 96 and not 100.
    #
    # The design table starts it at x 1280. It starts at 1472 instead, and
    # the 192 units it gives up are the most valuable in the map: at 1280
    # the catwalk's west end stood directly in the line of sight from the
    # hangar floor to the fuel-bay mouth, so from anywhere east of about
    # x 1350 the only way on was hidden behind a wall of green plate. That
    # is the v0 finding coming back in a different costume. Screenshot of
    # the fault: docs/levels/shots/2026-10-13_1009_F3_map01-v1-catwalk-screens-the-mouth.png.
    CATWALK_WEST = 1472
    z6b_catwalk = zone("z6b_catwalk", 96, HANGAR_CEIL,
                       [(CATWALK_WEST, 1440, 2560, 1600)], wall=STEEL)

    # D6's recess, on the catwalk side: 192 of headroom, 128 of door leaf.
    d6_recess = zone("d6_recess", 96, 96 + DOOR_LEAF_HEIGHT, [(2432, 1536, 2560, 1600)],
                     wall=STEEL)

    # S2, the loose panel off the catwalk: the RPG-7 closet in v3. A secret
    # must look like the wall it is in, so the panel is plate, not a door.
    s2_panel = door("s2_panel", 96, TAG_S2_CATWALK_PANEL, (2176, 1600, 2240, 1632))
    s2_closet = zone("s2_closet", 96, 192, [(2112, 1632, 2304, 1792)], wall=STEEL)

    # ======================================================================
    # Act 3b - fuel bay (SW-A) and the sump secret under it
    # ======================================================================
    # A short passage through the hangar's north wall, so the opening reads
    # as a doorway and not as a missing wall. Its ceiling is 160 against the
    # hangar's 288: that 128-unit difference is the lintel over the mouth,
    # one exact tile of red-striped concrete, and the only thing in the
    # hangar that says "through here".
    fuel_passage = zone("fuel_passage", HANGAR_FLOOR, 160, [(1152, 1600, 1280, 1664)],
                        flat=LANE, wall=STRIPE)
    # Design table says y 1600..1920; shifted 64 north to make room for the
    # passage. Same size, same relations.
    z7_fuel_bay = zone("z7_fuel_bay", HANGAR_FLOOR, 160, [(1152, 1664, 1600, 1984)],
                       wall=STEEL)
    # The second yellow lane of section 7: inside the bay it runs west and
    # stops dead at the wall the sump panel is in. It points at the secret
    # and explains nothing, which is the whole craft of a secret.
    s3_lane = zone("s3_lane", HANGAR_FLOOR, 160, [(1152, 1728, 1280, 1856)],
                   flat=LANE, wall=STEEL, extra=LANE_ACROSS)

    s3_panel = door("s3_panel", HANGAR_FLOOR, TAG_S3_SUMP_PANEL, (1120, 1728, 1152, 1792))
    # Four 16-unit steps down to the sump. The design gave the sump a ceiling
    # of 0, which is only 32 above the fuel-bay floor: the doorway would have
    # been 32 high and impassable. The stairwell is ceilinged at 64 instead
    # and the sump itself keeps its -96 floor and its 0 ceiling.
    sump_step_1 = zone("sump_step_1", -48, 64, [(1088, 1728, 1120, 1792)], wall=STEEL)
    sump_step_2 = zone("sump_step_2", -64, 64, [(1056, 1728, 1088, 1792)], wall=STEEL)
    sump_step_3 = zone("sump_step_3", -80, 64, [(1024, 1728, 1056, 1792)], wall=STEEL)
    s3_sump = zone("s3_sump", SUMP_FLOOR, 0, [(896, 1664, 1024, 1856)])

    # ======================================================================
    # Act 4 - control booth (SW-B)
    # ======================================================================
    # Design table says x 2560..2816; shifted 128 west so the booth actually
    # touches the catwalk and D6 has a wall to sit in.
    d6 = door("d6", 96, TAG_D6_CATWALK_BOOTH, (2432, 1600, 2560, 1664))
    z9_booth = zone("z9_booth", 96, 224, [
        (2560, 1616, 2688, 1664),
        (2432, 1664, 2688, 1856),
    ], flat=TILE, ceiling=CEIL_LAMP, wall=STEEL)
    # The booth window: a sill 32 above the booth floor (so it cannot be
    # stepped through) and 160 above the hangar floor. It is a window, so it
    # is the one sector of the map no player can stand in. This is the
    # beacon SW-A lights in v2.
    booth_window = zone("booth_window", 128, 224, [(2560, 1600, 2688, 1616)],
                        flat=TILE, ceiling=CEIL_LAMP, wall=STEEL)

    # ======================================================================
    # Act 5 - the two-leaf airlock and the exit lift
    # ======================================================================
    # D4's recess, on the HANGAR side, and the most load-bearing 64 units of
    # geometry in the map. Without it the leaf spans the hangar's whole 320
    # of wall and tiles two and a half times: from the floor it reads as
    # patterned wall, which is exactly what the CEO reported. With it, the
    # gate is a 256-wide pair of leaves under a lintel, framed in red.
    d4_recess = zone("d4_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
                     [(2624, 544, 2688, 800)], wall=STRIPE)
    # D4, 256 wide, remote: shut when the hangar is first seen, opened for
    # good by SW-A. No use-special on its lines - it is the gate.
    d4 = door("d4", HANGAR_FLOOR, TAG_D4_HANGAR_AIRLOCK, (2688, 544, 2752, 800))
    z8_airlock = zone("z8_airlock", HANGAR_FLOOR, 96, [(2752, 544, 2912, 800)], wall=STEEL)
    # D5, 128 wide, the inner leaf; opened for good by SW-B in the booth.
    d5 = door("d5", HANGAR_FLOOR, TAG_D5_AIRLOCK_EXIT, (2912, 608, 2944, 736))
    # Z10, the service lift shaft: the tallest, emptiest room of the map, and
    # exactly 256 units from floor to ceiling - the height of the Lenin
    # poster, which goes on its north wall. The last Soviet face you see
    # before the map drops you into the metro.
    z10_exit = zone("z10_exit", HANGAR_FLOOR, 224, [(2944, 480, 3264, 864)])
    # ...and D5's recess on the lift-room side, for the same reason as D4's.
    # Painted AFTER the lift room, because painting is last-wins and this
    # rectangle lies inside it.
    d5_recess = zone("d5_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
                     [(2944, 608, 3008, 736)], wall=STEEL)

    # ======================================================================
    # Doors, switches and the exit
    # ======================================================================
    # ORDER MATTERS from here down. GridMap resolves a segment with the FIRST
    # rule that covers it, so the specific ones (a door leaf, a poster) must
    # be registered before the broad ones (a whole striped wall run).
    #
    # Both flanking lines of every manual door carry the special, and the
    # style pins the winding so the door sector is always on the BACK side:
    # a `playeruse` special only fires from the front, so this is what makes
    # a door openable from both rooms.
    for tag, door_sector, segments in (
        (TAG_D1_DORM_WASHROOM, d1, [("v", 640, 32, 160), ("v", 704, 32, 160)]),
        (TAG_D2_DORM_CORRIDOR, d2, [("h", 448, 192, 320), ("h", 512, 192, 320)]),
        (TAG_D3_KOMNATA_SERVICE, d3, [("v", 640, 1088, 1216), ("v", 704, 1088, 1216)]),
        # D6's east side meets the booth from y 1616 up; below that it meets
        # the window sector, which no player can stand in, so that stretch
        # stays a plain two-sided line.
        (TAG_D6_CATWALK_BOOTH, d6, [("h", 1600, 2432, 2560), ("v", 2560, 1616, 1664)]),
    ):
        style = door_raise_style(tag, door_sector, texture=DOOR)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    # The three secret panels: push once, open for good. They wear STEEL,
    # not the door leaf: a secret that advertises itself is a corridor.
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

    # SW-A, north wall of the fuel bay: opens D4 for good. Repeatable, so a
    # second press can never undo or consume the gate.
    # TODO(A3): SWITCH_PLACEHOLDER is the door leaf standing in for a switch
    # texture that does not exist yet. The bay is 192 high, so it tiles one
    # and a half times. When SDSWT1/SDSWT2 arrive this becomes one tile in a
    # 128-high niche; nothing else about the map changes.
    g.style_h(1984, 1280, 1408, switch_door_open_style(TAG_D4_HANGAR_AIRLOCK,
                                                       texture=SWITCH_PLACEHOLDER))
    # SW-B, north wall of the control booth: opens D5 for good. The booth is
    # exactly 128 high, so here the stand-in at least tiles once.
    g.style_h(1856, 2496, 2624, switch_door_open_style(TAG_D5_AIRLOCK_EXIT,
                                                       texture=SWITCH_PLACEHOLDER))
    # The exit, on the east wall of the lift shaft (256 high: two tiles of
    # the stand-in until A3 lands).
    g.style_v(3264, 608, 736, exit_switch_style(texture=SWITCH_PLACEHOLDER))

    # --- the three pictures ----------------------------------------------
    # Each one is exactly as wide and as tall as its wall, so it appears
    # once, whole, with no offset. That is why they are where they are.
    #   SDSTAR1 128x128 - dorm north wall, right of D2: the first thing the
    #     player sees on waking, next to the door he is about to use.
    #   SDPOSTR2 128x128 - the back wall of the komnata's mural niche.
    #   SDPOSTR1 128x256 - the lift room's north wall, which is 256 high.
    g.style_h(448, 320, 448, LineStyle(texture=PLAQUE))
    g.style_h(1440, 256, 384, LineStyle(texture=MURAL))
    g.style_h(864, 3072, 3200, LineStyle(texture=LENIN))

    # --- the red route ----------------------------------------------------
    # One continuous marking from the barracks to the fuel bay, plus the
    # frame around D4. Registered last so a door, a switch or a poster on
    # the same wall run wins over it.
    #
    # Z3, both walls: the stripe is born here, 96-high corridor, one tile.
    g.style_v(192, 512, 960, LineStyle(texture=STRIPE))
    g.style_v(320, 512, 960, LineStyle(texture=STRIPE))
    # Z4, the east wall either side of D3's recess: in an open room the
    # stripe stops being a band and becomes a pointer at the way out.
    g.style_v(640, 960, 1088, LineStyle(texture=STRIPE))
    g.style_v(640, 1216, 1408, LineStyle(texture=STRIPE))
    # Z5, both walls, the guard post's doorway interrupting the north one.
    g.style_h(1088, 704, 1152, LineStyle(texture=STRIPE))
    g.style_h(1216, 704, 896, LineStyle(texture=STRIPE))
    g.style_h(1216, 1024, 1152, LineStyle(texture=STRIPE))
    # The hangar's west wall, from the corner at the foot of the entry stair
    # all the way north to the fuel-bay mouth. This is the single most
    # important run of texture in the map: it is the sentence "the route
    # continues over here", said without words, to a player who has just
    # walked 1900 units of red-striped corridor to get here.
    g.style_v(1152, 1216, 1600, LineStyle(texture=STRIPE))
    # ...and the lintel over the mouth itself, seen from anywhere in the
    # hangar: 128 of wall between the passage's ceiling and the hangar's,
    # one exact tile, the stripe riding across it.
    g.style_h(1600, 1152, 1280, LineStyle(texture=STRIPE))
    # D4's frame: the lintel over the recess and both of its jambs. The gate
    # is on the route too - it is simply not open yet, and the leaf under
    # this frame says so.
    g.style_v(2624, 544, 800, LineStyle(texture=STRIPE))
    g.style_h(544, 2624, 2688, LineStyle(texture=STRIPE))
    g.style_h(800, 2624, 2688, LineStyle(texture=STRIPE))

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
WALL_TEXTURES = (CONC, STRIPE, STEEL, DOOR, PLAQUE, LENIN, MURAL)
FLAT_TEXTURES = (LANE, CONCRETE_FLOOR, TILE, CEIL_LAMP, CEIL)
