"""MAP03 "Tankograd", the tractor factory - v0, the grey box with the approved sets where they fit.

Design document: docs/levels/MAP03-factory.md. LORE's third map and the
episode's climax ("Tractor factory (actually tanks) - episode climax: the
portal"). Built as MAP04 while MAP02 was the practice range (D41); MAP03
since D62 (2026-10-14), and named Tankograd by the CEO (D63). The
player arrives where MAP02 left him: on rails, out of the westbound tunnel,
into the factory's goods spur.

What v0 is (design document section 12, D60 "MVP first"): the whole floor
plan, walkable from start to exit - every room, stair, door, switch, both
keys, both locked doors, the portal's containment gate and the exit - and
nothing else: no monsters, no weapons, no ammo, no health, no secrets.
Like MAP02's v0 it already wears the approved sets where they fit, and every
surface the player must read wears its real face from the first build: door
leaves, switch faces, the star plaques round the two locked doors.

What v0 does about MAP02's lesson (D58: the CEO never found the blue pass):
both keys lie IN PLAIN SIGHT on the route, each on a lit pedestal in its
key's colour (sector `lightcolor`), each seen from the doorway of its room
(tested sight lines); the yellow key is even seen from the factory floor,
up the office stair, and a yellow lane on the floor joins the yellow door to
that stair. Light 192 is spent on five places only: the two locks, the two
keys and the exit.

The route, in one line: goods spur -> dock -> assembly hall (both locked
doors seen at once: red at the west end, yellow in the south wall; the
yellow key seen up the office stair) -> offices, the YELLOW KEY on the
director's desk -> yellow door -> tank line -> foundry, the RED KEY on the
casting platform, and SW-A, which opens a shutter straight back into the
hall beside the red door -> red door -> portal hall -> control booth, SW-B,
which opens the containment drum's gate -> the portal, and the exit breaker
at the top of its dais.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP03 tools/run.sh
Since D62 MAPINFO wires it in (design document section 11, step 2): the
metro's exit leads here, and this map's exit ends the episode (cluster 1).
"""

from __future__ import annotations

from sdbuild.udmf import (
    DOOR_SPEED_SLOW,
    GridMap,
    LineStyle,
    Sector,
    TextMap,
    Thing,
    door_raise_style,
    exit_switch_style,
    remote_door_style,
    switch_door_open_style,
)

MAP_NAME = "MAP03"

# --- The approved set (docs/art/TEXTURE-INDEX.md) --------------------------
# No industrial set exists yet (brick, rust, chains: LORE). v0 dresses the
# factory in the Soviet base set and two metro pieces; the industrial pieces
# it wants are listed in the design document, section 7, for art-director.
CONCRETE = "SDCONC1"    # 64x128 prefab panels: dock, foundry, portal hall
STRIPE = "SDCONC2"      # 64x128 red stripe at mid height: the assembly hall (MAP01's hangar bands)
STAR = "SDSTAR1"        # 128x128 star plaque: either side of each locked door
STEEL = "SDSTEL1"       # green riveted plate: tank line, drum, booth, shutter, conveyors
TILE_DADO = "SDTILE2"   # 64x128 tile over a green dado: the offices
CRATE = "SDCRAT1"       # 64x64 crate face: the director's desk front
DOOR = "SDDOOR1"        # 128x128 door leaf
TUBBING = "SDTUBB1"     # 128x128 metro tubbing: the goods spur MAP02's tunnel ran into
FLOOR_LANE = "SDFLR1"   # hangar concrete with a yellow lane line along the image's y
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
CEIL_PANEL = "SDCEIL1"  # lit panel
CEIL_CONCRETE = "SDCEIL2"
DESK_TOP = "SDCRTOP1"   # crate lid, planks: the desk's top
RAILS = "SDRAIL1"       # metro track bed, rails along the image's y

# Switches (D25), one variant per switch. The exit keeps the hazard panel it
# wears on MAP01, the range and MAP02: the same face, the same meaning.
SW_A_FACE = "SDSW1B"    # foundry: push button, opens the shutter into the hall
SW_B_FACE = "SDSW1A"    # control booth: the knife switch, opens the drum's gate
EXIT_FACE = "SDSW1D"    # hazard panel at the top of the portal's dais
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64       # every SDSW1x is 64x128
SWITCH_HEIGHT = 128
PLAQUE = 128            # SDSTAR1 is 128x128

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED in engine
# on MAP02 (docs/qa/evidence/2026-10-14_1902_F3_map03-v0-walk.md: without the
# key the door printed its lock line; with it, it opened and stayed open).
# Delay 0 = opens and stays open, so a key gate can never be consumed.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock numbers read from shipped text, gzdoom.pk3 g4.14.2 -> lockdefs.txt:
# `Lock 1 Doom { RedCard ... }`, `Lock 3 Doom { YellowCard ... }`.
LOCK_RED_CARD = 1
LOCK_YELLOW_CARD = 3
# Doom's editor numbers; Freedoom draws them until we have our own keys.
ED_YELLOW_CARD = 6
ED_RED_CARD = 13
KEY_LOCKS = {ED_YELLOW_CARD: LOCK_YELLOW_CARD, ED_RED_CARD: LOCK_RED_CARD}

ED_PLAYER1_START = 1

# --- Heights ----------------------------------------------------------------
GROUND = 0              # dock, hall, tank line, foundry gallery, portal hall
OFFICES = 64            # the office floor, four steps up from the hall
FOUNDRY_PIT = -64       # the casting floor, four steps down from the gallery
CHANNEL = FOUNDRY_PIT - 16   # the metal channel in the casting floor (v2: molten)
TANK_PIT = -48          # the inspection pits under the tank line
STEP = 16               # every stair step; under MAX_STEP_UP 24
DESK = 16               # the desk and the ingot pedestal: one step up
CONVEYOR = 32           # the assembly lines: waist high, cover, not a step
DOOR_HEIGHT = 128       # SDDOOR1 is 128x128: every leaf is one tile high
SPUR_CEIL = GROUND + 128        # tubbing: one tile, as in MAP02's tunnels
DOCK_CEIL = 256
HALL_CEIL = 320                 # SDCONC2 in three bands, as MAP01's hangar
OFFICE_CEIL = OFFICES + DOOR_HEIGHT     # 192
LINE_CEIL = 256
FOUNDRY_CEIL = 256
PORTAL_HALL_CEIL = 384
DRUM_CEIL = 256
NICHE_DEPTH = 16

# --- Light ---------------------------------------------------------------------
# v0: one value per zone. 192 is spent on five places only: the two locks,
# the two keys and the exit (MAP02 v1's rule: the brightest things in a map
# are where it wants the player to look).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_SPUR = 112
LIGHT_DOCK = 144
LIGHT_HALL = 160
LIGHT_OFFICES = 128
LIGHT_DIRECTOR = 176    # the key's room: one step under the beacon
LIGHT_LINE = 144
LIGHT_VESTIBULE = 128
LIGHT_FOUNDRY = 128     # v2: the glow of the channel and the furnaces
LIGHT_GALLERY = 144
LIGHT_ANTE = 128
LIGHT_PORTAL_HALL = 128
LIGHT_BOOTH = 144
LIGHT_DRUM = 144
BEACON_ZONES = ("z3_red_portal", "z3_yellow_portal", "o_desk", "f_pedestal", "p_exit_niche")

# The keys' colours, in light: sector field `lightcolor` (0xRRGGBB) of the
# UDMF zdoom namespace, as MAP02 v1 uses it for the blue pass. On the portal
# round each locked door AND on the place its key lies: the colour of the
# lock is the colour of where the key is. NOT VERIFIED in our engine runs
# (checklist K4); if the engine ignored it, both places would still be 192s.
YELLOW = 0xFFD860
RED = 0xFF6048
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_D1_PLANNING = 1
TAG_D2_ARCHIVE = 2
TAG_YELLOW_DOOR = 4      # the tank line: Door_LockedRaise, lock 3
TAG_RED_DOOR = 5         # the portal shop: Door_LockedRaise, lock 1
TAG_SHUTTER = 10         # SW-A: the foundry's shutter into the hall
TAG_GATE = 11            # SW-B: the containment drum's gate

# --- Things --------------------------------------------------------------------
PLAYER_START = (4096, 1184)
PLAYER_ANGLE = 180       # facing west, down the spur, into the factory
YELLOW_KEY_SPOT = (2304, 2048)   # on the director's desk
RED_KEY_SPOT = (512, 352)        # on the ingot pedestal, casting platform
KEY_ZONES = {ED_YELLOW_CARD: "o_desk", ED_RED_CARD: "f_pedestal"}
LOCK_PORTALS = {LOCK_YELLOW_CARD: "z3_yellow_portal", LOCK_RED_CARD: "z3_red_portal"}

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design (the conveyors)
WINDOWS: tuple[str, ...] = ()    # v0 has no window
SECRET_ZONES: tuple[str, ...] = ()   # v0 has no secret (D60; v3 places them)

# The assembly hall's two lines, split by the centre aisle the lane runs up.
CONVEYOR_ROWS = ((896, 960), (1408, 1472))
CONVEYOR_RUNS = ((1792, 2240), (2368, 2880))
LANE_X = (2272, 2336)            # the yellow lane: yellow door -> office stair


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0), on both faces.

    Repeatable like a manual door: pressed without the key it prints the
    engine's lock line and can be pressed again; with it, it opens for good.
    MAP02's helper, repeated here so each map stays one file (it moves into
    sdbuild.udmf when a third map wants it).
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
    g = GridMap(tm, wall=CONCRETE)
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
        """A 64-wide rail strip along x: SDRAIL1 runs its rails along the
        image's y, so it is turned a quarter (MAP02's K8, either way reads)."""
        like(room, f"rails_{room}", [(x1, y1, x2, y2)], flat=RAILS,
             extra={"rotationfloor": 90.0})

    def steps(prefix: str, xs, y1: int, y2: int, floors, *, room: str) -> None:
        """A run of 32-deep steps across x, one sector per step."""
        for n, (x, floor) in enumerate(zip(xs, floors), start=1):
            like(room, f"{prefix}_{n}", [(x, y1, x + 32, y2)], floor=floor, wall=CONCRETE)

    # ======================================================================
    # Arrival: the goods spur MAP02's tunnel ran into, and the loading dock
    # ======================================================================
    zone("z1_spur", GROUND, SPUR_CEIL, [(3648, 1120, 4160, 1248)],
         light=LIGHT_SPUR, wall=TUBBING)
    rails("z1_spur", 3648, 4160, 1152, 1216)
    zone("z2_dock", GROUND, DOCK_CEIL, [(3136, 896, 3648, 1472)],
         light=LIGHT_DOCK, wall=CONCRETE)
    rails("z2_dock", 3328, 3648, 1152, 1216)     # the buffer stop is v1's
    zone("z2_arch", GROUND, 192, [(3072, 1120, 3136, 1248)],
         light=LIGHT_HALL, wall=CONCRETE)

    # ======================================================================
    # The assembly hall: the factory's public face, and the hub
    # ======================================================================
    zone("z3_hall", GROUND, HALL_CEIL, [(1600, 704, 3072, 1664)],
         light=LIGHT_HALL, ceiling=CEIL_PANEL, wall=STRIPE)
    for r, (y1, y2) in enumerate(CONVEYOR_ROWS, start=1):
        for c, (x1, x2) in enumerate(CONVEYOR_RUNS, start=1):
            like("z3_hall", f"{PROP_PREFIX}conveyor_{r}{c}", [(x1, y1, x2, y2)],
                 floor=GROUND + CONVEYOR, wall=STEEL, flat=FLOOR_CONCRETE)
    # The red door's portal: a 128-high band across the west end, so the
    # leaf and the two star plaques either side are each one whole tile.
    zone("z3_red_portal", GROUND, DOOR_HEIGHT, [(1600, 992, 1664, 1376)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=STRIPE, extra=RED_LIGHT)
    red_door = door("red_door", GROUND, TAG_RED_DOOR, (1568, 1120, 1600, 1248),
                    light=LIGHT_ANTE)
    # The yellow door's portal, in the south wall, the same way.
    zone("z3_yellow_portal", GROUND, DOOR_HEIGHT, [(2112, 704, 2496, 768)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=STRIPE, extra=YELLOW_LIGHT)
    yellow_door = door("yellow_door", GROUND, TAG_YELLOW_DOOR, (2240, 672, 2368, 704),
                       light=LIGHT_VESTIBULE)
    # The yellow lane: from the yellow door's portal, up the centre aisle,
    # to the foot of the office stair. Lock and key joined by a line.
    zone("z3_lane", GROUND, HALL_CEIL, [(LANE_X[0], 768, LANE_X[1], 1664)],
         light=LIGHT_HALL, flat=FLOOR_LANE, ceiling=CEIL_PANEL, wall=STRIPE)

    # ======================================================================
    # The offices: four steps up, the director's office straight ahead
    # ======================================================================
    for n in range(1, 5):
        y = 1664 + 32 * (n - 1)
        zone(f"o_stair_{n}", GROUND + STEP * n, OFFICE_CEIL, [(2240, y, 2368, y + 32)],
             light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    zone("o_corridor", OFFICES, OFFICE_CEIL, [(1856, 1792, 2752, 1920)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    zone("o_director_doorway", OFFICES, OFFICE_CEIL, [(2240, 1920, 2368, 1952)],
         light=LIGHT_DIRECTOR, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO,
         extra=YELLOW_LIGHT)
    zone("o_director", OFFICES, OFFICE_CEIL, [(2176, 1952, 2432, 2208)],
         light=LIGHT_DIRECTOR, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO,
         extra=YELLOW_LIGHT)
    zone("o_desk", OFFICES + DESK, OFFICE_CEIL, [(2240, 2016, 2368, 2080)],
         light=LIGHT_BEACON, flat=DESK_TOP, ceiling=CEIL_PANEL, wall=CRATE,
         extra=YELLOW_LIGHT)
    d1 = door("d1_planning", OFFICES, TAG_D1_PLANNING, (1920, 1920, 2048, 1952),
              light=LIGHT_OFFICES)
    zone("o_planning", OFFICES, OFFICE_CEIL, [(1856, 1952, 2112, 2208)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    d2 = door("d2_archive", OFFICES, TAG_D2_ARCHIVE, (2560, 1920, 2688, 1952),
              light=LIGHT_OFFICES)
    zone("o_archive", OFFICES, OFFICE_CEIL, [(2496, 1952, 2752, 2208)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)

    # ======================================================================
    # Behind the yellow door: the tank line, where the "tractors" are tanks
    # ======================================================================
    zone("t_vestibule", GROUND, DOOR_HEIGHT, [(2240, 448, 2368, 672)],
         light=LIGHT_VESTIBULE, wall=STEEL)
    zone("t_line", GROUND, LINE_CEIL, [(1856, 64, 3328, 448)],
         light=LIGHT_LINE, ceiling=CEIL_PANEL, wall=STEEL)
    # Two inspection pits under the line, a tank's length each, with three
    # steps at both ends: the long sides are drops, the ends the way out.
    for name, x1 in (("pit_a", 2432), ("pit_b", 2880)):
        like("t_line", f"t_{name}", [(x1 + 64, 192, x1 + 320, 320)], floor=TANK_PIT,
             wall=CONCRETE)
        steps(f"t_{name}_w", (x1, x1 + 32), 192, 320, (TANK_PIT + 2 * STEP, TANK_PIT + STEP),
              room="t_line")
        steps(f"t_{name}_e", (x1 + 320, x1 + 352), 192, 320, (TANK_PIT + STEP, TANK_PIT + 2 * STEP),
              room="t_line")
    zone("t_pour_arch", GROUND, DOOR_HEIGHT, [(1792, 192, 1856, 320)],
         light=LIGHT_GALLERY, wall=CONCRETE)

    # ======================================================================
    # The foundry: a gallery at ground level over the casting floor
    # ======================================================================
    zone("f_floor", FOUNDRY_PIT, FOUNDRY_CEIL, [(384, 64, 1408, 640)],
         light=LIGHT_FOUNDRY, wall=CONCRETE)
    like("f_floor", "f_channel", [(768, 128, 1152, 192)], floor=CHANNEL)
    zone("f_gallery", GROUND, FOUNDRY_CEIL, [(1408, 64, 1792, 640)],
         light=LIGHT_GALLERY, wall=CONCRETE)
    steps("f_stair", (1376, 1344, 1312), 256, 384,
          (GROUND - STEP, GROUND - 2 * STEP, GROUND - 3 * STEP), room="f_floor")
    zone("f_platform", GROUND, FOUNDRY_CEIL, [(384, 192, 640, 512)],
         light=LIGHT_FOUNDRY, wall=CONCRETE)
    steps("f_platform_stair", (640, 672, 704), 288, 416,
          (GROUND - STEP, GROUND - 2 * STEP, GROUND - 3 * STEP), room="f_floor")
    zone("f_pedestal", GROUND + DESK, FOUNDRY_CEIL, [(448, 288, 576, 416)],
         light=LIGHT_BEACON, wall=STEEL, extra=RED_LIGHT)
    # The shortcut: a short passage from the gallery's north wall to a
    # shutter flush with the assembly hall's south wall, beside the red door.
    zone("f_passage", GROUND, DOOR_HEIGHT, [(1664, 640, 1792, 672)],
         light=LIGHT_GALLERY, wall=CONCRETE)
    shutter = door("shutter", GROUND, TAG_SHUTTER, (1664, 672, 1792, 704), light=LIGHT_HALL)
    zone("f_swa_niche", GROUND, GROUND + SWITCH_HEIGHT, [(1600, 640, 1664, 640 + NICHE_DEPTH)],
         light=LIGHT_GALLERY, wall=CONCRETE)

    # ======================================================================
    # Behind the red door: the portal hall, the booth, the containment drum
    # ======================================================================
    zone("p_ante", GROUND, DOOR_HEIGHT, [(1408, 1120, 1568, 1248)],
         light=LIGHT_ANTE, wall=STEEL)
    zone("p_hall", GROUND, PORTAL_HALL_CEIL, [(384, 768, 1408, 1664)],
         light=LIGHT_PORTAL_HALL, flat=FLOOR_TILE, wall=CONCRETE)
    zone("p_booth", GROUND, DOOR_HEIGHT, [(1088, 1664, 1344, 1792)],
         light=LIGHT_BOOTH, ceiling=CEIL_PANEL, wall=STEEL)
    # The drum: a solid ring round the portal, one gate in its east face,
    # a 128-high porch either side of the gate so its leaf is one tile.
    g.carve(640, 1024, 1024, 1408)
    zone("p_drum", GROUND, DRUM_CEIL, [(704, 1088, 960, 1344)],
         light=LIGHT_DRUM, wall=STEEL)
    gate = door("gate", GROUND, TAG_GATE, (960, 1152, 1024, 1280), light=LIGHT_DRUM)
    zone("p_porch", GROUND, DOOR_HEIGHT, [(1024, 1152, 1088, 1280)],
         light=LIGHT_PORTAL_HALL, wall=STEEL)
    like("p_drum", "p_inner_porch", [(896, 1152, 960, 1280)], ceil=DOOR_HEIGHT)
    for n, x in enumerate((832, 768, 704), start=1):
        like("p_drum", f"p_dais_{n}", [(x, 1088, x + 64, 1344)], floor=GROUND + STEP * n)
    zone("p_exit_niche", GROUND + 3 * STEP, GROUND + 3 * STEP + SWITCH_HEIGHT,
         [(704 - NICHE_DEPTH, 1184, 704, 1248)], light=LIGHT_BEACON, wall=STEEL)

    # ======================================================================
    # Line styles: doors, locks, switches, the exit
    # ======================================================================
    for sector, y, (x1, x2) in ((d1, 1920, (1920, 2048)), (d1, 1952, (1920, 2048)),
                                (d2, 1920, (2560, 2688)), (d2, 1952, (2560, 2688))):
        tag = tm.sectors[sector].identifier
        g.style_h(y, x1, x2, door_raise_style(tag, sector, texture=DOOR))

    # The two locked doors, both faces, each between two star plaques.
    for y in (672, 704):
        g.style_h(y, 2240, 2368, locked_door_style(TAG_YELLOW_DOOR, yellow_door,
                                                   LOCK_YELLOW_CARD, texture=DOOR))
    g.style_h(704, 2112, 2240, LineStyle(texture=STAR))
    g.style_h(704, 2368, 2496, LineStyle(texture=STAR))
    for x in (1568, 1600):
        g.style_v(x, 1120, 1248, locked_door_style(TAG_RED_DOOR, red_door,
                                                   LOCK_RED_CARD, texture=DOOR))
    g.style_v(1600, 992, 1120, LineStyle(texture=STAR))
    g.style_v(1600, 1248, 1376, LineStyle(texture=STAR))

    # The shutter: steel on the foundry side; on the hall side it wears the
    # hall's own wall, so until SW-A opens it it is wall, not a door that
    # will not open (MAP01 v0/v1, MAP02's SH).
    g.style_h(672, 1664, 1792, remote_door_style(shutter, texture=STEEL))
    g.style_h(704, 1664, 1792, remote_door_style(shutter, texture=STRIPE))
    g.style_h(640 + NICHE_DEPTH, 1600, 1664,
              switch_door_open_style(TAG_SHUTTER, texture=SW_A_FACE, repeatable=False))

    # The drum's gate: a leaf on both faces. SW-B on the booth's back wall.
    for x in (960, 1024):
        g.style_v(x, 1152, 1280, remote_door_style(gate, texture=DOOR))
    g.style_h(1792, 1184, 1248, switch_door_open_style(TAG_GATE, texture=SW_B_FACE,
                                                       repeatable=False))

    # The exit: the breaker at the back of its niche, on top of the dais.
    g.style_v(704 - NICHE_DEPTH, 1184, 1248, exit_switch_style(texture=EXIT_FACE))

    g.build()

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD))
    tm.add_thing(Thing(x=RED_KEY_SPOT[0], y=RED_KEY_SPOT[1], type=ED_RED_CARD))
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
WALL_TEXTURES = (CONCRETE, STRIPE, STAR, STEEL, TILE_DADO, CRATE, DOOR, TUBBING) + SWITCH_FACES
FLAT_TEXTURES = (FLOOR_LANE, FLOOR_CONCRETE, FLOOR_TILE, CEIL_PANEL, CEIL_CONCRETE,
                 DESK_TOP, RAILS)
