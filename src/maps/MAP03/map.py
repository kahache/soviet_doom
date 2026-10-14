"""MAP03 "Metro-bunker" - v0, the grey box with the metro set where it is easy.

Design document: docs/levels/MAP03-metro.md. LORE's second campaign map
(docs/product/LORE.md, "Metro-bunker tunnels: first key, first heavy
hybrids") built as MAP03, because MAP02 is the practice range since D41.
The player arrives by the service lift MAP01 ends on.

What v0 is (design document section 12): the whole floor plan, walkable from
start to exit - every room, stair, door, switch, the key, the locked door,
the gate, the exit and the two secrets - and NOTHING else: no monsters, no
weapons, no ammo, no health. Unlike MAP01's v0 it is not one grey texture:
the brief asked for the approved metro set where it is easy (D42, D48), and
MAP01's v0 walk proved that a grey box cannot signpost (doors that read as
walls), so every surface the player must read wears its real texture from
the first build: door leaves, switch faces, the mosaic round the locked door.

The route, in one line: lift -> concourse -> escalator (the locked blast door
is seen at the far end of the hall from the top) -> hall -> drop into the
open track -> east tunnel -> substation, the BLUE PASS, and SW-A, which opens
a shutter back onto the platform -> hall -> blast door (blue) -> bunker ->
command post, SW-B, which opens the tunnel gate and the command post's own
door onto the tunnel -> west tunnel -> exit.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP03 tools/run.sh
MAPINFO has no MAP03 entry yet (mod-engineer's; proposed in the design
document section 11): until it lands the map loads with `+map MAP03` and no
title.
"""

from __future__ import annotations

from sdbuild.udmf import (
    DOOR_SPEED_SLOW,
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

MAP_NAME = "MAP03"

# --- The approved set (docs/art/TEXTURE-INDEX.md) --------------------------
# Metro set, D42 (first six) and D48 (the ten fill pieces): all approved.
TILE = "SDTILE1"        # 64x128 glazed cream tile
TILE_DADO = "SDTILE2"   # 64x128 tile over a military-green dado: the bunker, the 1941 shelter
TILE_FRIEZE = "SDTILE3"  # 64x128 tile with a ceramic frieze: the concourse
MARBLE = "SDMARB1"      # 64x128 red marble: the pylons and the escalator shaft
STATION = "SDMARB2"     # 64x128 tile over marble with a brass rail: station walls
MOSAIC = "SDMOSA1"      # 128x128 the star with rays (D47): round the blast door
TUNNEL = "SDTUNL1"      # 64x128 board-cast tunnel concrete: service spaces
TUBBING = "SDTUBB1"     # 128x128 cast-iron tubbing: the running tunnels
EDGE = "SDMEDG1"        # 64x64 platform face towards the track, chevrons
FLOOR_GRANITE = "SDMFLR1"   # 64x64 polished grey granite
FLOOR_HALL = "SDMFLR2"      # 64x64 pale/dark granite checker: the hall
FLOOR_COPING = "SDMFLR3"    # 64x64 platform edge from above, lip on row 63
RAILS = "SDRAIL1"           # 64x64 one track per tile, rails along the image's y
CEIL_COFFER = "SDMCEIL1"    # 64x64 coffered plaster
CEIL_LAMP = "SDMCEIL2"      # 64x64 coffer with a ring lamp
# Base set, D30 and before: what the metro set has no piece for.
STEEL = "SDSTEL1"       # green riveted plate: lift, train, bunker steelwork, shutters
DOOR = "SDDOOR1"        # 128x128 door leaf
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
CEIL_CONCRETE = "SDCEIL2"
CEIL_PANEL = "SDCEIL1"  # lit panel: the train's ceiling strip

# Switches (D25): one variant per switch, for what it does. SDSW1C, unused
# by MAP01, goes to SW-A.
SW_A_FACE = "SDSW1C"    # substation: opens the platform shutter
SW_B_FACE = "SDSW1B"    # command post console: opens the tunnel gate
EXIT_FACE = "SDSW1D"    # hazard panel: the exit, as on MAP01 and MAP02
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64       # every SDSW1x is 64x128
SWITCH_HEIGHT = 128

# The Stalin poster (D55, cell 4C, «СЛАВА СТАЛИНУ!»), 128x256 like Lenin.
# Its slot is built: a 128-long wall, exactly 256 from floor to ceiling, at
# the back of a shallow niche in the sealed 1941 shelter (secret S1). The
# poster is installed since 3d24d39, so the slot wears it.
STALIN_POSTER = "SDPOSTR3"
STALIN_SLOT_TEXTURE = STALIN_POSTER
POSTER_WIDTH = 128
POSTER_HEIGHT = 256

# --- Specials not in sdbuild.udmf ----------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag). The argument SHAPE is
# read from gzdoom.pk3 g4.14.2 -> xlat/base.txt, e.g. Doom's blue "open and
# stay" door, line 133: `Door_LockedRaise (tag, D_FAST, 0, BCard | ...)`: a
# delay of 0 is a door that opens and STAYS open, so the key gate can never
# be consumed. The NUMBER, 13, follows 10 Door_Close / 11 Door_Open /
# 12 Door_Raise (all three verified in engine on MAP01) in ZDoom's compiled
# table: from memory of the source, NOT VERIFIED - engine checklist K2.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock 2 is "Blue key card" in gzdoom.pk3 -> lockdefs.txt (`Lock 2 Doom
# { BlueCard ... }`): read from shipped text.
LOCK_BLUE_CARD = 2
ED_BLUE_CARD = 5        # Doom's BlueCard; Freedoom draws it until we have a pass sprite

ED_PLAYER1_START = 1

# --- Heights ----------------------------------------------------------------
UPPER = 160             # the lift, the concourse, the top of the escalator
STATION_FLOOR = 0       # hall, platforms, train, substation, bunker
TRACK = -64             # track bed, tunnels, the command post, the shelter
STEP = 16               # every stair step; under MAX_STEP_UP 24
DOOR_HEIGHT = 128       # SDDOOR1 is 128x128: every leaf is one tile high
TUNNEL_CEIL = TRACK + 128       # tubbing: one 128 tile from floor to ceiling
PLATFORM_CEIL = 160
HALL_CEIL = 224
ARCH_CEIL = 128
UPPER_CEIL = UPPER + 128        # 288: lift, concourse, the escalator shaft
TRAIN_CEIL = 112
TURNSTILE_HEIGHT = 32           # waist high: cover, not a step
SHELTER_CEIL = TRACK + POSTER_HEIGHT   # 192: the poster wall is 256 high

# --- Light (v0: one value per zone; lamps, beacons and change are v2) ------
LIGHT_MIN = 96
LIGHT_MAX = 192
LAMP_STEP = 16
LIGHT_LIFT = 128
LIGHT_CONCOURSE = 160
LIGHT_KASSA = 144
LIGHT_ESCALATOR = 144
LIGHT_HALL = 160
LIGHT_PORTAL = 192       # the blast door: the brightest thing at the hall's far end
LIGHT_ARCHES = 144
LIGHT_PLATFORM = 144
LIGHT_TRACK = 112
LIGHT_TUNNEL = 96
LIGHT_TRAIN = 128
LIGHT_SUBSTATION = 128
LIGHT_SECRET = 112
LIGHT_BUNKER = 128
LIGHT_DORM = 112
LIGHT_CP = 128
LIGHT_EXIT = 144         # the exit niche: the one lit spot past the gate

# --- Tags --------------------------------------------------------------------
TAG_D1_LIFT = 1
TAG_D2_KASSA = 2
TAG_D3_SUBSTATION = 3
TAG_BLAST_DOOR = 4       # the blue door: Door_LockedRaise, lock 2
TAG_D4_BUNKER = 5
TAG_D5_ARMOURY = 6
TAG_SHUTTER = 10         # SW-A: the substation's shutter onto platform N
TAG_GATE = 11            # SW-B: the tunnel gate AND the command post's tunnel door
TAG_S1_SHELTER = 101
TAG_S2_CAB = 102

# --- Things --------------------------------------------------------------------
PLAYER_START = (3776, 896)
PLAYER_ANGLE = 180       # facing west, at D1
KEY_SPOT = (2976, 1088)  # on the duty officer's side of the substation
KEY_ZONE = "z8_substation"

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design (turnstiles)
WINDOWS: tuple[str, ...] = ()    # v0 has no window
SECRET_ZONES = ("s1_shelter", "s2_cab")

# Train: four cars between two cabs, partitions with gangways, two doors a
# car on the platform side. y is fixed; x below.
TRAIN_Y = (320, 448)
TRAIN_WALL_Y = (432, 448)        # the car side towards platform S
GANGWAY_Y = (344, 408)
CAB_W = (1280, 1344)
CAB_E = (2752, 2816)
CAB_W_PARTITION = (1344, 1360)
CAB_E_PARTITION = (2736, 2752)
CAR_PARTITIONS = ((1664, 1680), (2048, 2064), (2432, 2448))
CARS = ((1360, 1664), (1680, 2048), (2064, 2432), (2448, 2736))
CAR_DOOR = 64

# Pylons: six, 128 long, the arches between them 128 wide.
PYLONS = tuple((1344 + 256 * k, 1472 + 256 * k) for k in range(6))
HALL_LAMPS = (1536, 1792, 2048, 2304, 2560)
HALL_AXIS = (864, 928)           # y of the lamp line, the hall's centre


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0).

    Repeatable and on both faces, like a manual door: pressed without the key
    it prints the engine's lock message and can be pressed again; pressed
    with it, it opens for good. Nothing in the map closes it.
    """
    return LineStyle(
        special=SPECIAL_DOOR_LOCKED_RAISE,
        args=(tag, DOOR_SPEED_SLOW, 0, lock, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,
    )


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v0 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=TUNNEL)
    plan: dict[str, int] = {}

    def zone(name: str, floor: int, ceil: int, rects, tag: int | None = None, *,
             light: int, flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
             wall: str | None = None, special: int = 0, extra: dict | None = None) -> int:
        if name in plan:
            raise ValueError(f"duplicate zone name {name!r}")
        index = tm.add_sector(_sector(floor, ceil, tag, light=light, flat=flat,
                                      ceiling=ceiling, special=special, extra=extra))
        g.paint_all(index, rects)
        if wall:
            g.set_wall(index, wall)
        plan[name] = index
        return index

    def like(room: str, name: str, rects, *, floor: int | None = None,
             ceil: int | None = None, light: int | None = None, **kw) -> int:
        s = tm.sectors[plan[room]]
        kw.setdefault("flat", s.texturefloor)
        kw.setdefault("ceiling", s.textureceiling)
        kw.setdefault("extra", dict(s.extra))
        kw.setdefault("wall", g.wall_of(plan[room]))
        return zone(name, s.heightfloor if floor is None else floor,
                    s.heightceiling if ceil is None else ceil, rects,
                    light=s.lightlevel if light is None else light, **kw)

    def door(name: str, floor: int, tag: int, rect, *, light: int) -> int:
        """A closed door sector; its own walls are the steel track."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=STEEL)

    def rails(room: str, x1: int, x2: int, y1: int, y2: int) -> None:
        """The rail strip down the middle of a 128-wide track bed: SDRAIL1
        runs its rails along the image's y, so a track laid along x turns it
        a quarter (rotationfloor 90; NOT VERIFIED which way, either reads)."""
        like(room, f"rails_{room}", [(x1, y1, x2, y2)], flat=RAILS,
             extra={"rotationfloor": 90.0})

    # ======================================================================
    # Arrival: the lift from Zarya-7, the concourse, the escalator
    # ======================================================================
    zone("z1_lift", UPPER, UPPER_CEIL, [(3648, 768, 3904, 1024)],
         light=LIGHT_LIFT, wall=STEEL)
    d1 = door("d1", UPPER, TAG_D1_LIFT, (3584, 832, 3648, 960), light=LIGHT_CONCOURSE)
    zone("z2_concourse", UPPER, UPPER_CEIL, [(3136, 640, 3584, 1152)],
         light=LIGHT_CONCOURSE, flat=FLOOR_GRANITE, ceiling=CEIL_COFFER, wall=TILE_FRIEZE)
    # The turnstile line across the concourse: two barriers, waist high,
    # three gaps; the middle gap is on the escalator's axis.
    for n, rect in enumerate(((3264, 704, 3296, 832), (3264, 960, 3296, 1088)), start=1):
        like("z2_concourse", f"{PROP_PREFIX}turnstiles_{n}", [rect],
             floor=UPPER + TURNSTILE_HEIGHT, wall=STEEL, flat=FLOOR_CONCRETE)
    d2 = door("d2", UPPER, TAG_D2_KASSA, (3296, 1152, 3424, 1216), light=LIGHT_KASSA)
    zone("z2_kassa", UPPER, UPPER_CEIL, [(3264, 1216, 3456, 1344)],
         light=LIGHT_KASSA, flat=FLOOR_TILE, wall=TILE)
    # The escalator: ten steps of 16 down to the hall, one shaft ceiling so
    # the view from the top runs the whole length of the hall to the blast
    # door (tested).
    for i in range(10):
        x1 = 2816 + 32 * i
        zone(f"esc_{i + 1}", STATION_FLOOR + STEP * (i + 1), UPPER_CEIL,
             [(x1, 832, x1 + 32, 960)], light=LIGHT_ESCALATOR,
             flat=FLOOR_GRANITE, ceiling=CEIL_COFFER, wall=MARBLE)

    # ======================================================================
    # The station: hall, pylons, two platforms, the open track and the train
    # ======================================================================
    zone("z3_hall", STATION_FLOOR, HALL_CEIL, [(1344, 704, 2816, 1088)],
         light=LIGHT_HALL, flat=FLOOR_HALL, ceiling=CEIL_COFFER, wall=STATION)
    for n, x in enumerate(HALL_LAMPS, start=1):
        like("z3_hall", f"lamp_z3_hall_{n}", [(x, HALL_AXIS[0], x + 64, HALL_AXIS[1])],
             light=LIGHT_HALL + LAMP_STEP, ceiling=CEIL_LAMP)
    # The portal: a 128-high band across the hall's west end, so the blast
    # door and the two mosaics either side of it are each one whole tile.
    zone("z3_portal", STATION_FLOOR, ARCH_CEIL, [(1280, 704, 1344, 1088)],
         light=LIGHT_PORTAL, flat=FLOOR_HALL, ceiling=CEIL_COFFER, wall=MARBLE)
    blast = door("blast_door", STATION_FLOOR, TAG_BLAST_DOOR, (1248, 832, 1280, 960),
                 light=LIGHT_BUNKER)
    for row, (y1, y2) in (("n", (1088, 1152)), ("s", (640, 704))):
        zone(f"arches_{row}", STATION_FLOOR, ARCH_CEIL, [(1280, y1, 2816, y2)],
             light=LIGHT_ARCHES, flat=FLOOR_HALL, ceiling=CEIL_COFFER, wall=MARBLE)
        for x1, x2 in PYLONS:
            g.carve(x1, y1, x2, y2)

    zone("z4_platform_n", STATION_FLOOR, PLATFORM_CEIL, [(1280, 1152, 2816, 1344)],
         light=LIGHT_PLATFORM, flat=FLOOR_GRANITE, ceiling=CEIL_COFFER, wall=STATION)
    # The coping along the open edge. SDMFLR3's lip is its row 63; turned
    # half round so it lies on the track side (NOT VERIFIED, checklist K7).
    like("z4_platform_n", "coping_n", [(1536, 1280, 2560, 1344)], flat=FLOOR_COPING,
         extra={"rotationfloor": 180.0})
    # Staff stairs at both ends, down into the track bed: the way back up.
    for side, xs in (("w", (1472, 1408, 1344)), ("e", (2560, 2624, 2688))):
        for n, x in enumerate(xs, start=1):
            like("z4_platform_n", f"stair_{side}{n}", [(x, 1280, x + 64, 1344)],
                 floor=STATION_FLOOR - STEP * n, flat=FLOOR_CONCRETE)
    zone("z4_platform_s", STATION_FLOOR, PLATFORM_CEIL, [(1280, 448, 2816, 640)],
         light=LIGHT_PLATFORM, flat=FLOOR_GRANITE, ceiling=CEIL_COFFER, wall=STATION)

    zone("z5_track", TRACK, PLATFORM_CEIL, [(1280, 1344, 2816, 1472)],
         light=LIGHT_TRACK, wall=TILE)
    rails("z5_track", 1280, 2816, 1376, 1440)

    # The train stands at platform S, doors open. Floor at platform height,
    # so it is a second, parallel way along the station.
    zone("z6_train", STATION_FLOOR, TRAIN_CEIL, [(1280, TRAIN_Y[0], 2816, TRAIN_Y[1])],
         light=LIGHT_TRAIN, flat=FLOOR_CONCRETE, ceiling=CEIL_PANEL, wall=STEEL)
    g.carve(1280, TRAIN_WALL_Y[0], 2816, TRAIN_WALL_Y[1])
    for x1, x2 in CARS:
        for dx in (x1 + CAR_DOOR, x2 - 2 * CAR_DOOR):
            g.paint(plan["z6_train"], dx, TRAIN_WALL_Y[0], dx + CAR_DOOR, TRAIN_WALL_Y[1])
    for x1, x2 in CAR_PARTITIONS + (CAB_E_PARTITION, CAB_W_PARTITION):
        g.carve(x1, TRAIN_Y[0], x2, GANGWAY_Y[0])
        g.carve(x1, GANGWAY_Y[1], x2, TRAIN_WALL_Y[0])
    like("z6_train", "z6_cab_e", [(CAB_E[0], TRAIN_Y[0], CAB_E[1], TRAIN_WALL_Y[0])])
    # S2: the west cab. Its gangway is shut by a panel where the east cab's
    # stands open: the comparison is the clue (design document section 7).
    like("z6_train", "s2_cab", [(CAB_W[0], TRAIN_Y[0], CAB_W[1], TRAIN_WALL_Y[0])],
         light=LIGHT_SECRET, special=SECTOR_SPECIAL_SECRET)
    s2_panel = zone("s2_panel", STATION_FLOOR, STATION_FLOOR,
                    [(CAB_W_PARTITION[0], GANGWAY_Y[0], CAB_W_PARTITION[1], GANGWAY_Y[1])],
                    TAG_S2_CAB, light=LIGHT_TRAIN, wall=STEEL)

    # ======================================================================
    # East: the running tunnel, the substation (the pass, SW-A), shelter S1
    # ======================================================================
    zone("z7_tunnel_e", TRACK, TUNNEL_CEIL, [(2816, 1344, 3200, 1472)],
         light=LIGHT_TUNNEL, wall=TUBBING)
    rails("z7_tunnel_e", 2816, 3200, 1376, 1440)
    d3 = door("d3", TRACK, TAG_D3_SUBSTATION, (2944, 1312, 3072, 1344), light=LIGHT_SUBSTATION)
    # Three steps up from the track to the substation, under the tunnel's
    # own ceiling: D3's leaf is then one tile high from both sides.
    for n, y in enumerate((1280, 1248, 1216), start=1):
        zone(f"sub_stair_{n}", TRACK + STEP * n, TUNNEL_CEIL, [(2944, y, 3072, y + 32)],
             light=LIGHT_SUBSTATION)
    zone("z8_substation", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT,
         [(2880, 1024, 3072, 1216)], light=LIGHT_SUBSTATION)
    like("z8_substation", "z8_passage", [(2848, 1152, 2880, 1216)])
    shutter = door("shutter", STATION_FLOOR, TAG_SHUTTER, (2816, 1152, 2848, 1216),
                   light=LIGHT_PLATFORM)

    s1_panel = zone("s1_panel", TRACK, TRACK, [(3072, 1472, 3136, 1504)], TAG_S1_SHELTER,
                    light=LIGHT_TUNNEL, wall=TUNNEL)
    zone("s1_passage", TRACK, TUNNEL_CEIL, [(3072, 1504, 3136, 1600)],
         light=LIGHT_SECRET, flat=FLOOR_TILE, wall=TILE_DADO)
    zone("s1_shelter", TRACK, SHELTER_CEIL, [(2880, 1600, 3264, 1856)],
         light=LIGHT_SECRET, flat=FLOOR_TILE, wall=TILE_DADO, special=SECTOR_SPECIAL_SECRET)
    like("s1_shelter", "s1_poster_niche", [(3008, 1856, 3136, 1872)], special=0)

    # ======================================================================
    # West: the blast door, the bunker, the command post, the gate, the exit
    # ======================================================================
    zone("b1_vestibule", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT,
         [(1088, 832, 1248, 960)], light=LIGHT_BUNKER, wall=STEEL)
    d4 = door("d4", STATION_FLOOR, TAG_D4_BUNKER, (1056, 832, 1088, 960), light=LIGHT_BUNKER)
    zone("b2_spine", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT, [(576, 832, 1056, 960)],
         light=LIGHT_BUNKER, wall=TILE_DADO)
    d5 = door("d5", STATION_FLOOR, TAG_D5_ARMOURY, (544, 832, 576, 960), light=LIGHT_DORM)
    zone("b5_armoury", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT, [(384, 768, 544, 1024)],
         light=LIGHT_DORM, wall=STEEL)
    like("b2_spine", "b3_doorway", [(768, 768, 896, 832)])
    zone("b3_dorm", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT, [(576, 512, 1056, 768)],
         light=LIGHT_DORM, wall=TILE_DADO)
    for n, y in enumerate((960, 992, 1024), start=1):
        floor = STATION_FLOOR - STEP * n
        zone(f"cp_stair_{n}", floor, floor + DOOR_HEIGHT, [(896, y, 1024, y + 32)],
             light=LIGHT_CP, wall=STEEL)
    zone("b4_cp", TRACK, TUNNEL_CEIL, [(768, 1056, 1152, 1312)], light=LIGHT_CP, wall=STEEL)
    cp_door = door("cp_door", TRACK, TAG_GATE, (960, 1312, 1088, 1344), light=LIGHT_TUNNEL)

    # The west tunnel, in two sectors either side of the gate (one sector
    # on both sides would be one room to the engine's eye and to the tests'
    # reachability model). The rail strips stop one tile short of the gate
    # so its faces stay single 128-long lines: a texture restarts at every
    # linedef, and a leaf split by a strip's edges comes out in pieces.
    zone("z7_tunnel_w", TRACK, TUNNEL_CEIL, [(832, 1344, 1280, 1472)],
         light=LIGHT_TUNNEL, wall=TUBBING)
    rails("z7_tunnel_w", 896, 1280, 1376, 1440)
    gate = door("gate", TRACK, TAG_GATE, (768, 1344, 832, 1472), light=LIGHT_TUNNEL)
    zone("z9_exit_tunnel", TRACK, TUNNEL_CEIL, [(384, 1344, 768, 1472)],
         light=LIGHT_TUNNEL, wall=TUBBING)
    rails("z9_exit_tunnel", 384, 704, 1376, 1440)
    zone("z9_exit_niche", TRACK, TUNNEL_CEIL, [(352, 1376, 384, 1440)],
         light=LIGHT_EXIT, wall=TUNNEL)

    # ======================================================================
    # Line styles: doors, switches, the key, the exit, signs
    # ======================================================================
    for sector, x, (y1, y2) in ((d1, 3584, (832, 960)), (d1, 3648, (832, 960)),
                                (d4, 1056, (832, 960)), (d4, 1088, (832, 960)),
                                (d5, 544, (832, 960)), (d5, 576, (832, 960))):
        tag = tm.sectors[sector].identifier
        g.style_v(x, y1, y2, door_raise_style(tag, sector, texture=DOOR))
    for sector, y, (x1, x2) in ((d2, 1152, (3296, 3424)), (d2, 1216, (3296, 3424)),
                                (d3, 1312, (2944, 3072)), (d3, 1344, (2944, 3072))):
        tag = tm.sectors[sector].identifier
        g.style_h(y, x1, x2, door_raise_style(tag, sector, texture=DOOR))

    # The blue blast door, between two mosaics, both faces locked.
    for x in (1248, 1280):
        g.style_v(x, 832, 960, locked_door_style(TAG_BLAST_DOOR, blast, LOCK_BLUE_CARD,
                                                 texture=DOOR))
    g.style_v(1280, 704, 832, LineStyle(texture=MOSAIC))
    g.style_v(1280, 960, 1088, LineStyle(texture=MOSAIC))

    # The shutter: plain steel from the platform (it has no handle there:
    # the substation opens it), steel from the passage too.
    for x in (2816, 2848):
        g.style_v(x, 1152, 1216, remote_door_style(shutter, texture=STEEL))
    # SW-A on the substation's west wall, beside the passage to the shutter.
    g.style_v(2880, 1088, 1152, switch_door_open_style(TAG_SHUTTER, texture=SW_A_FACE,
                                                       repeatable=False))

    # The gate: a door leaf on both faces, one tile wide and high.
    for x in (768, 832):
        g.style_v(x, 1344, 1472, remote_door_style(gate, texture=DOOR))
    # The command post's door onto the tunnel: a leaf on the CP side; on the
    # tunnel side it is tubbing like the rest of the wall, so before SW-B it
    # is not a door that will not open (MAP01's v0 and v1 lesson).
    g.style_h(1312, 960, 1088, remote_door_style(cp_door, texture=DOOR))
    g.style_h(1344, 960, 1088, remote_door_style(cp_door, texture=TUBBING))
    # SW-B on the CP's north wall, right beside that door: pressed, the door
    # opens in front of the player, and the gate beyond it.
    g.style_h(1312, 1088, 1152, switch_door_open_style(TAG_GATE, texture=SW_B_FACE,
                                                       repeatable=False))

    # The exit, at the back of its niche past the gate.
    g.style_v(352, 1376, 1440, exit_switch_style(texture=EXIT_FACE))

    # Secrets: S1's panel is a patch of cast concrete in a tubbing wall;
    # S2's panel is train steel like the partition it closes.
    for y in (1472, 1504):
        g.style_h(y, 3072, 3136, door_open_style(TAG_S1_SHELTER, s1_panel, texture=TUNNEL))
    for x in CAB_W_PARTITION:
        g.style_v(x, GANGWAY_Y[0], GANGWAY_Y[1], door_open_style(TAG_S2_CAB, s2_panel,
                                                                  texture=STEEL))
    # The poster slot.
    g.style_h(1872, 3008, 3136, LineStyle(texture=STALIN_SLOT_TEXTURE))

    # The platform face towards the open track: 64 high, one SDMEDG1 tile,
    # hung from its top edge.
    g.style_h(1344, 1536, 2560, LineStyle(texture=EDGE, peg_bottom=False))

    g.build()

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=KEY_SPOT[0], y=KEY_SPOT[1], type=ED_BLUE_CARD))
    return tm, plan


def build_textmap() -> TextMap:
    return build_plan()[0]


def lumps() -> list[tuple[str, bytes]]:
    """Return the WAD lumps in directory order (contract used by the build)."""
    return [
        (MAP_NAME, b""),
        ("TEXTMAP", build_textmap().to_bytes()),
        ("ENDMAP", b""),
    ]


# Every lump name this map may put in a sidedef or a sector.
WALL_TEXTURES = (TILE, TILE_DADO, TILE_FRIEZE, MARBLE, STATION, MOSAIC, TUNNEL,
                 TUBBING, EDGE, STEEL, DOOR, STALIN_POSTER) + SWITCH_FACES
FLAT_TEXTURES = (FLOOR_GRANITE, FLOOR_HALL, FLOOR_COPING, RAILS, CEIL_COFFER,
                 CEIL_LAMP, FLOOR_CONCRETE, FLOOR_TILE, CEIL_CONCRETE, CEIL_PANEL)
