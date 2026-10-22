"""MAP04 «Транссиб» / Trans-Siberian, the Sverdlovsk marshalling yard - v1.

Design document: docs/levels/MAP04-transsib.md. Episode 2, «The Road to
Moscow» (D104, P4), opens here: November 1977, the Trans-Siberian's
marshalling yard at Sverdlovsk, held by the Fourth Reich (the yard, the
roundhouse) and the Liberty Legion (the signal box, the goods warehouse),
both on the passenger platform where the Soviet armoured train waits. The
sergeant comes up from Tankograd by a service tunnel; he leaves on the
armoured train, by the regulator in its locomotive's cab.

Built at once as MAP03's v1 was (D60 "MVP first", the PM's brief): the whole
floor plan walkable from start to exit, textured with the approved sets
(Soviet base, metro, Tankograd, and since 2026-10-22 episode 2's Railway set,
D107: ballast and track, the wagons, the tank, the armoured train, the
signals, the roundhouse brick, the warehouse's gates; since round 2, D113,
the night sky over the yard, the wagons' roofs and the gondolas' floors, the
cab from inside, the signal box's glazing and lever frame, the roundhouse's
road doors and the station board; what is still missing is listed in the
design document's "Still pending"), populated on the bestiary's own
numbers, secrets in.

The route, in one line: service tunnel -> the yard (the YELLOW door seen in
its south wall, the signal box glowing yellow over the wagons) -> up the
goods ramp and along the roofs of a coupled rake of boxcars (the RED door
seen below, in the north wall) -> the signal box, the YELLOW KEY on its lever
frame -> yellow door -> goods warehouse -> roundhouse, the RED KEY on the
turntable's bridge (taking it drops the sides of two gondolas in the yard:
the counter-attack) -> SW-A, the roundhouse's road gate onto the yard ->
red door -> the platform, the armoured train -> SW-B in the stationmaster's
office, which unbolts the train's rear hatch -> through the train to the
locomotive's cab, and the exit.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP04 SKILL=3 tools/run.sh
"""

from __future__ import annotations

from dataclasses import replace

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
    skill_tier,
    switch_door_open_style,
)

MAP_NAME = "MAP04"

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# Soviet base.
CONCRETE = "SDCONC1"    # 64x128 prefab panels: pit walls, the goods ramp, S1's cable box
STAR = "SDSTAR1"        # 128x128 star plaque: either side of the YELLOW door
STEEL = "SDSTEL1"       # green riveted plate: the loco and its cab, the turntable, the lever frame, door tracks
TILE_DADO = "SDTILE2"   # 64x128 tile over a green dado: the signal box, the offices
CRATE = "SDCRAT1"       # 64x64 crate face: flatcar loads, the warehouse's stacks, S3's row
DOOR = "SDDOOR1"        # 128x128 door leaf: D1, D2, the train's hatch
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
CEIL_PANEL = "SDCEIL1"  # lit panel
CEIL_CONCRETE = "SDCEIL2"
# The metro set (D42, D48): the tunnel and the station.
TUBBING = "SDTUBB1"     # 128x128 cast-iron tubbing: the service tunnel from Tankograd
TUNNEL_WALL = "SDTUNL1"  # 64x128 tunnel concrete with cables: the tunnel's refuge niches
STATION = "SDMARB2"     # 64x128 tile over red marble: the passenger platform's walls
FLOOR_STATION = "SDMFLR2"   # granite checker: the platform
FLOOR_COPING = "SDMFLR3"    # platform edge from above, lip on row 63: along the train
RAILS = "SDRAIL1"       # track bed, rails along the image's y: turned 90 to run along x
# Tankograd (D66).
BRICK = "SDBRCK1"       # 64x128 soot brick: the yard, the warehouse, the roundhouse
BRICK_DADO = "SDBRCK2"  # 64x128 whitewashed to 64: the passages, the red door's flanks
DOOR_YELLOW = "SDDOORY"  # 128x128 the yellow lock's leaf
DOOR_RED = "SDDOORR"    # 128x128 the red lock's leaf
WINDOW = "SDWIND1"      # 64x128 glazing at night: the roundhouse's clerestory
FLAG_REICH = "SDFLAG1"  # 64x128 the Fourth Reich's banner on brick
FLAG_LEGION = "SDFLAG2"  # 64x128 the Liberty Legion's banner on brick
FLOOR_PLATE = "SDFLR4"  # 64x64 chequer plate: wagon roofs, the train's floor, the hub
GRATING = "SDGRAT1"     # 64x64 grating: the signal box's step
# Episode 2 (D107, approved 2026-10-22): the Railway set, and one dam piece.
TRACK = "SDTRAK1"       # flat: track on ballast, rails along the image's y: turned 90 to run along x
BALLAST = "SDBLST1"     # flat: loose ballast, the yard's ground and the roundhouse's stalls
WAGON_SIDE = "SDWAGN1"  # 128x128 covered goods wagon: boxcars, the rake, the gondolas
TANK_SIDE = "SDTANK1"   # 128x128 tank wagon «НЕФТЬ»
ARMOUR_STAR = "SDARMR1"  # 128x128 armour plate with the red star: one panel per face, never stacked
ARMOUR = "SDARMR2"      # 64x128 the same plate, plain: the armoured train
SIGNAL = "SDSIGL1"      # 64x128 colour-light signal: SINGLE USE (D107), one 64 span per signal
ROUNDHOUSE_BRICK = "SDBRCK3"  # 64x128 roundhouse brick, a frieze on top
GOODS_GATE = "SDGATE2"  # 128x128 the warehouse's padlocked sliding gate «СКЛАД»
DECK = "SDGRAT2"        # flat (dam set): expanded metal over a void, the turntable bridge's deck
# Episode 2, round 2 (D113, approved 2026-10-22): the Railway set's second
# batch and the night sky (design document section 7.2).
SKY = "F_SKY1"          # the engine's sky marker (not a lump of ours); MAPINFO's sky1 is SDSKY1
WAGON_ROOF = "SDWROF1"  # flat: a goods wagon's roof, its walkway along the image's y: turned 90
GONDOLA_BED = "SDGOND1"  # flat: an open wagon's floor, four 32 x 32 discharge flaps a tile
CAB_FRONT = "SDCAB1"    # 128x128 the locomotive cab's backhead: ONE piece, the cab's front wall
CAB_SIDE = "SDCAB2"     # 64x128 the cab's sides from inside
BOX_GLAZING = "SDSBOX1"  # 64x64 the signal box's glazing lit from inside; rows 8-55 the 48-high opening
LEVER_TOP = "SDLEVR1"   # flat: the lever frame from above, the boards the signalman stands on at its foot
LEVER_FRONT = "SDLEVR2"  # 64x64 the lever frame from the front: rows 45-60 its plates and cast-iron bed
STALL_DOORS = "SDRHDR1"  # 128x128 a roundhouse road's wooden doors: stall 2 and S2's panel, the same face
STATION_BOARD = "SDSTAN1"   # 256x64 «СВЕРДЛОВСК / СОРТИРОВОЧНЫЙ», hung under the canopy over the coping

# Switches (D25), one variant per switch; the exit keeps the hazard panel
# every map's exit wears.
SW_A_FACE = "SDSW1B"    # roundhouse: the road gate's push button
SW_B_FACE = "SDSW1A"    # stationmaster's office: the knife switch that unbolts the hatch
EXIT_FACE = "SDSW1D"    # the locomotive's cab
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64
SWITCH_HEIGHT = 128
TILE = 128
DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_RED)

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED on MAP02
# and MAP03. Delay 0: opens and stays open.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Floor_LowerToLowest (tag, speed): 21 in ZDoom's (Hexen's) special table,
# the action xlat/doom.txt gives Doom's "lower floor to lowest" lines. NOT
# VERIFIED in our engine runs (design document, engine checklist K3); if it
# failed, the gondolas would stay shut, and nothing the route needs is in them.
SPECIAL_FLOOR_LOWER_TO_LOWEST = 21
FLOOR_SPEED = 16        # 2 units a tic: a 96 side is down in ~1.4 s
LOCK_RED_CARD = 1       # gzdoom.pk3 lockdefs.txt, as MAP03
LOCK_YELLOW_CARD = 3
ED_YELLOW_CARD = 6      # Doom's cards, drawn by Freedoom until we have our own
ED_RED_CARD = 13
KEY_LOCKS = {ED_YELLOW_CARD: LOCK_YELLOW_CARD, ED_RED_CARD: LOCK_RED_CARD}
ED_PLAYER1_START = 1

# --- Heights ----------------------------------------------------------------
GROUND = 0              # the yard, the warehouse, the roundhouse
TUNNEL_FLOOR = -64      # the service tunnel, three steps under the yard
TUNNEL_CEIL = TUNNEL_FLOOR + TILE   # tubbing: one tile, as on MAP02 and MAP03
WAGON = 96              # a boxcar's roof
FLATCAR = 64            # a flatcar's load of crates: one crate high
GONDOLA_FLOOR = 16      # an open wagon's bed
STEP = 16               # every step; under MAX_STEP_UP 24
CABIN = 128             # the signal box's floor: two steps over the roofs
CABIN_CEIL = 240
SILL = 160              # the signal box's windows: 160..208
LINTEL = 208            # a 48-high opening: seen through, never climbed through
LEVER_FRAME = CABIN + STEP   # the frame the yellow key lies on
PIT = -64               # the turntable's pit
HUB = GROUND + STEP     # the turntable's king post, the red key on it
PLATFORM = 32           # the passenger platform, two steps over the yard
TRAIN_FLOOR = 48        # inside the armoured train, one step over the platform
TRAIN_CEIL = TRAIN_FLOOR + TILE     # 176: the hatch's leaf is one tile
DOOR_HEIGHT = 128
YARD_CEIL = 384         # the night sky's height over the yard: its walls stand 384, then SDSKY1
WAREHOUSE_CEIL = 256
ROUNDHOUSE_CEIL = 320
PLATFORM_CEIL = 256     # the platform's canopy
STALL_CEIL = 128        # a stall is one gate high
LOCO_STALL_CEIL = 192
CLERESTORY_SILL = ROUNDHOUSE_CEIL - TILE   # one SDWIND1 tile under the roof
NICHE_DEPTH = 16
GOODS_GATES = ((2112, 2240), (2880, 3008))   # the warehouse's two shut gates on the yard, x spans
# The Railway set's alignment (D107). A wagon side is one 128 tile; a car
# stands 96 high, so its top 32 rows are cut and the underframe sits on the
# ground. Along x every car starts on a plank post and ends on the tile's
# seam (a 320 car is half a tile and two tiles); the tank shows «НЕФТЬ» twice,
# centred, never cut.
WAGON_TILE = 128
WAGON_OFFSET_Y = WAGON_TILE - WAGON
WAGON_OFFSET_X = 64
TANK_OFFSET_X = 96
ARMOUR_WIDTH = 64       # SDARMR2's plate
SIGNAL_WIDTH = 64       # SDSIGL1: one span per signal (D107)
SIGNAL_PILLAR = TILE    # the signal's concrete pillar: one tile high, so the face is never stacked
# Round 2's alignment (D113). Every bed of a gondola starts 16 off SDGOND1's
# 32 flap grid (x and y), so the flat is panned 16 both ways: the flaps' joints
# fall on the bed's edges (16 is its own opposite modulo 32: the sign of the
# panning cannot matter). The lever frame is one flat tile 32 off the 64 grid
# both ways: panned 32 (the same argument), it shows one whole frame.
GONDOLA_PAN = 16
LEVER_PAN = 32
# The frame's boards (the image's foot) towards the box's door, east. NOT
# VERIFIED which way GZDoom turns a positive rotationfloor: if the boards
# face west in the engine, this is 270.
LEVER_ROTATION = 90.0
LEVER_FRONT_ROW = 45    # SDLEVR2 on the frame's 16-high front: rows 45-60, the plates and the bed
BOX_GLAZING_ROW = 8     # SDSBOX1's rows 8-55 fill the 48-high window (UDMF offsety_mid)
GLAZING_WIDTH = 64
# The cab's front wall (x, y1, y2): one SDCAB1 across its 128, the exit's
# niche cut into its middle (the regulator is the exit).
CAB_FRONT_WALL = (640, 2464, 2592)
# The station board hangs from the canopy over the platform's edge: the line
# between the platform and the coping (y 2368), one board long, readable
# from the platform (its south face) and from the red door's vestibule.
COPING_EDGE_Y = 2368
STATION_BOARD_X = (2048, 2304)
STATION_BOARD_SIZE = (256, 64)

# --- The posters (CEO 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py) -----------------------------------
LENIN = "SDPOSTR1"      # 128x256 «ЛЕНИН ЖИВ»
STALIN = "SDPOSTR3"     # 128x256 «СЛАВА СТАЛИНУ!»
MURAL = "SDPOSTR2"      # 128x128 cosmonautics mural
POSTER_WIDTH = 128
POSTER_HEIGHT = 256
MURAL_HEIGHT = 128
# The Marx-Engels poster SDPOSTR4 is in preparation (not a lump yet). Its
# slots are built and wear a stand-in; approving it is this one line:
MARX_ENGELS: str | None = None   # -> "SDPOSTR4"
# Every picture: (name, texture, axis, coord, lo, hi), one GridMap style
# each. A portrait hangs on a one-sided line exactly 128 long in a sector
# exactly 256 high (the warehouse's own walls, or a 16-deep niche cut to
# 256 in the yard and the roundhouse); the mural in a niche 128 high.
POSTERS = (
    # The station's front on the yard: Lenin and Stalin either side of the
    # red door's portal, the faces the rake's roofs look down on. Each in
    # a niche of its own, lit one step over the night.
    ("yard_red_door_lenin", LENIN, "h", 1920 + NICHE_DEPTH, 2432, 2560),
    ("yard_red_door_stalin", STALIN, "h", 1920 + NICHE_DEPTH, 2944, 3072),
    # The goods warehouse, taken: the Legion hung its banner beside the
    # Stalin that was already on the east wall.
    ("warehouse_legion_stalin", STALIN, "v", 3328, 320, 448),
    # The platform: the station's mural on the building's wall, between
    # the banners and the red door's vestibule, facing the train.
    ("platform_mural", MURAL, "h", 2048 - NICHE_DEPTH, 1024, 1152),
    # Marx-Engels slots (stand-in Lenin): the roundhouse's south wall, the
    # depot's own poster over the turntable's stairs; and the warehouse's
    # west wall beside the passage to the roundhouse.
    ("roundhouse_south", LENIN, "h", 384 - NICHE_DEPTH, 960, 1088),
    ("warehouse_west", LENIN, "v", 1920, 320, 448),
)
POSTER_SLOTS_MARX_ENGELS = ("roundhouse_south", "warehouse_west")
# The niches cut for them: (zone, room, rect, ceiling height above the floor).
POSTER_NICHES = (
    ("z2_poster_lenin", "z2_yard", (2432, 1920, 2560, 1920 + NICHE_DEPTH), POSTER_HEIGHT),
    ("z2_poster_stalin", "z2_yard", (2944, 1920, 3072, 1920 + NICHE_DEPTH), POSTER_HEIGHT),
    ("z6_poster_mural", "z6_platform", (1024, 2048 - NICHE_DEPTH, 1152, 2048), MURAL_HEIGHT),
    ("z5_poster_slot", "z5_hall", (960, 384 - NICHE_DEPTH, 1088, 384), POSTER_HEIGHT),
)


def poster_faces():
    """POSTERS with each Marx-Engels slot wearing SDPOSTR4 once it exists."""
    return tuple((name, MARX_ENGELS if MARX_ENGELS and name in POSTER_SLOTS_MARX_ENGELS else texture,
                  axis, coord, lo, hi) for name, texture, axis, coord, lo, hi in POSTERS)


# --- Light ---------------------------------------------------------------------
# 192 is spent on five places only: the two locks, the two keys and the exit
# (MAP02 and MAP03's rule).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_TUNNEL = 112
LIGHT_YARD = 128        # night
LIGHT_ROOFS = 128
LIGHT_CABIN = 176       # the signal box: lit, and yellow (its windows are the yard's lamp)
LIGHT_WAREHOUSE = 144
LIGHT_OFFICE = 128
LIGHT_ROUNDHOUSE = 128
LIGHT_STALL = 112
LIGHT_DARK_STALL = LIGHT_MIN    # S2's clue: the stall in shadow
LIGHT_PLATFORM = 160
LIGHT_STATIONMASTER = 144
LIGHT_TRAIN = 128
LIGHT_CAB = 144
LIGHT_NICHE = LIGHT_MIN         # S1's and S3's clue: the niche in shadow
LIGHT_SECRET = 112
LIGHT_GONDOLA = 112
LIGHT_POSTER_STEP = 16          # a poster's niche: one lamp step over its room
BEACON_ZONES = ("z2_yellow_portal", "z2_red_portal", "z3_frame", "z5_hub", "z7_exit_niche")

YELLOW = 0xFFD860       # MAP03's two colours: the lock's colour is where its key lies
RED = 0xFF6048
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_D1_ROUNDHOUSE = 1   # manual door, warehouse passage -> roundhouse
TAG_D2_OFFICE = 2       # manual door, the warehouse office
TAG_YELLOW_DOOR = 4     # yard -> warehouse: Door_LockedRaise, lock 3
TAG_RED_DOOR = 5        # yard -> platform: Door_LockedRaise, lock 1
TAG_S1_PANEL = 6        # the tunnel's cable box (S1)
TAG_S2_PANEL = 7        # the dark stall's gate (S2)
TAG_S3_PANEL = 8        # the crate set back (S3)
TAG_SHUTTER = 10        # SW-A: the roundhouse's road gate onto the yard
TAG_HATCH = 11          # SW-B: the armoured train's rear hatch
TAG_GONDOLAS = 12       # the red key's pickup: the gondolas' sides drop (no line carries it)
LIFT_TAGS = (TAG_GONDOLAS,)

# --- Things --------------------------------------------------------------------
PLAYER_START = (4480, 1184)
PLAYER_ANGLE = 180       # facing west, up the tunnel to the yard
YELLOW_KEY_SPOT = (2112, 1600)   # on the signal box's lever frame
RED_KEY_SPOT = (1024, 1184)      # on the turntable's king post
KEY_ZONES = {ED_YELLOW_CARD: "z3_frame", ED_RED_CARD: "z5_hub"}
LOCK_PORTALS = {LOCK_YELLOW_CARD: "z2_yellow_portal", LOCK_RED_CARD: "z2_red_portal"}
# The red key's pickup special (UDMF thing `special` + `arg0..`): GZDoom runs
# an inventory item's special when it is picked up (Inventory.DoPickupSpecial,
# read in g4.14.2's zscript; NOT VERIFIED in our engine runs, checklist K4).
RED_KEY_PICKUP_SPECIAL = (SPECIAL_FLOOR_LOWER_TO_LOWEST, (TAG_GONDOLAS, FLOOR_SPEED, 0, 0, 0))

# Zone-name families the tests use.
PROP_PREFIX = "prop_"           # unwalkable by design (wagons, crate stacks, sills, the loco)
SECRET_ZONES: tuple[str, ...] = ("s1_store", "s2_store", "s3_store")
GONDOLA_PREFIX = "z2_gondola_"   # the counter-attack: open wagons whose sides drop

# A marker the route reads to find this map (tools/route.py, transsib-critical).
TURNTABLE = (768, 928, 1280, 1440)          # the pit's square, the bridge across it
TURNTABLE_BRIDGE = (768, 1120, 1280, 1248)
HUB_RECT = (992, 1152, 1056, 1216)
ROAD = (1664, 1120, 1760, 1248)             # the roundhouse's road out to the yard
SW_A_NICHE = (1680, 1248, 1744, 1264)       # SW-A, in the road's north wall beside the gate
BALCONY = (2304, 2432, 2496, 2592)          # the train's rear balcony, open to the platform
TRAIN_FLANK = (2432, 576, 2304)             # y, x1, x2: the train's side along the coping
# The red star (SDARMR1): one panel per face, never stacked or side by side,
# each a wall exactly one tile high: both long walls of the gun wagon, and
# the back of the rear balcony, the star the platform sees. (y, x1, x2)
STAR_PANELS = ((2464, 1472, 1600), (2592, 1472, 1600), (2592, 2336, 2464))

# The yard's wagons (x1, y1, x2, y2, height, side texture). Row 1 is south of
# the main track, row 2 north of it, row 3 the coupled rake whose roofs are
# the way to the signal box.
ROW_1 = (960, 1088)
ROW_2 = (1280, 1408)
ROW_3 = (1536, 1664)
WAGONS = {
    "prop_wagon_1a": (2048, 960, 2368, 1088, WAGON, WAGON_SIDE),     # a boxcar
    "prop_flatcar_1": (2880, 960, 3072, 1088, FLATCAR, CRATE),
    "prop_wagon_2a": (1984, 1280, 2304, 1408, WAGON, TANK_SIDE),     # a tank wagon «НЕФТЬ»
    "prop_flatcar_2": (2432, 1280, 2752, 1408, FLATCAR, CRATE),
}
ROOFS = ((2304, 2624), (2624, 2944), (2944, 3264), (3264, 3584))   # four boxcars, coupled
RAMP_XS = (3584, 3616, 3648, 3680, 3712)    # the goods ramp, west (high) to east (low)
# The two gondolas: (shell, bed, side that drops). The side faces the main track.
GONDOLAS = {
    "z2_gondola_1": ((2880, 1280, 3200, 1408), (2896, 1296, 3184, 1392), (2976, 1280, 3104, 1296)),
    "z2_gondola_2": ((2496, 960, 2816, 1088), (2512, 976, 2800, 1072), (2592, 1072, 2720, 1088)),
}
# The signal box: a brick tower at the rake's west end, windows all round.
CABIN_OUTER = (2048, 1472, 2304, 1728)
CABIN_ROOM = (2080, 1504, 2272, 1696)
CABIN_STEP = (2272, 1536, 2304, 1664)
LEVER_FRAME_RECT = (2080, 1568, 2144, 1632)
SILLS = ((2048, 1472, 2304, 1504), (2048, 1696, 2304, 1728), (2048, 1504, 2080, 1696),
         (2272, 1504, 2304, 1536), (2272, 1664, 2304, 1696))

# S1: three refuge niches in the tunnel's north wall; the middle one's back
# is a cable box of prefab panel among the tunnel's boarded concrete, in
# shadow, and it is a push panel.
TUNNEL_NICHES = ((4160, 4224), (4288, 4352), (4416, 4480))
S1_NICHE_INDEX = 1
S1_PANEL = (4288, 1264, 4352, 1280)
S1_PASSAGE = (4288, 1280, 4352, 1344)
S1_STORE = (4224, 1344, 4416, 1472)
# S2: three stalls in the roundhouse's west wall; the third is dark, and its
# shut gate is a push panel.
STALLS = {"z5_stall_1": (192, 448, 384, 576), "z5_stall_2": (192, 1120, 384, 1248),
          "z5_stall_3": (192, 1408, 384, 1536)}
S2_PANEL = (176, 1408, 192, 1536)
S2_STORE = (16, 1344, 176, 1600)
# S3: four crates fill a stretch of the warehouse's south wall; the third
# stands back, in shadow.
CRATE_ROW = (2560, 2816, 128)      # x1, x2, y of the wall
S3_NICHE = (2688, 112, 2752, 128)
S3_PANEL = (2688, 96, 2752, 112)
S3_STORE = (2624, 0, 2816, 96)
CRATE_WIDTH = 64
# Two colour-light signals in the yard: each a concrete pillar one tile high
# (cover in the aisles) wearing SDSIGL1 on ONE 64-long face (D107: single
# use, never tiled, never stacked); the other faces are the pillar's
# concrete. (name, pillar, face line as (x, y1, y2)). The main track's
# signal faces east, the tunnel's mouth: the first thing seen out of it;
# the north aisle's faces west, towards the box.
SIGNALS = (
    ("prop_signal_main", (3456, 1088, 3488, 1152), (3488, 1088, 1152)),
    ("prop_signal_north", (3264, 1440, 3296, 1504), (3264, 1440, 1504)),
)
# The roundhouse's clerestory, in its north wall.
CLERESTORY = (512, 704, 896, 1088, 1280, 1472)
# The platform's canopy columns: carved solid, marble-clad.
COLUMNS = (896, 1408, 1920, 2432, 2944)
COLUMN_Y = (2176, 2240)

# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich, 20 HP
ED_TROOPER = 21101        # SD_LegionTrooper, Legion, 30 HP
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both factions, 60 HP
ED_HOUND = 21103          # SD_ReichHound, Reich, 150 HP
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, 400 HP
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich, 500 HP
ED_PANZER_HEAVY = 21107   # SD_PanzermenschSchwer, Reich, 1000 HP
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
    "heavy": ED_PANZER_HEAVY,
}
MONSTER_CLASSES = {
    ED_RIFLEMAN: "SD_ReichRifleman",
    ED_TROOPER: "SD_LegionTrooper",
    ED_STORMTROOPER: "SD_Stormtrooper",
    ED_HOUND: "SD_ReichHound",
    ED_DOUGHBOY: "SD_Doughboy",
    ED_PANZERMENSCH: "SD_Panzermensch",
    ED_PANZER_HEAVY: "SD_PanzermenschSchwer",
}
REICH = ("rifleman", "hound", "panzermensch", "heavy")
LEGION = ("trooper", "doughboy")
# Where each faction stands (D35). The Reich holds the yard and the
# roundhouse (the locomotives), the Legion the signal box and the goods
# warehouse (the supplies); both guard the platform and the train. The
# gondolas are the counter-attack, mixed.
REICH_GROUND = ("z1_", "z2_", "z5_")
LEGION_GROUND = ("z3_", "z4_")
BOTH_GROUND = ("z6_", "z7_")
# The arsenal (MAPINFO DoomEdNums 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7)
SECRET_WEAPONS = (ED_ROKS3,)      # early, in S2: MAP03 handed it out on its route
# Ammo, health, armour: Doom's numbers, which our classes replace.
ED_CLIP = 2007            # 10 rounds
ED_CLIP_BOX = 2048        # 50
ED_SHELLS = 2008          # 4 shells
ED_SHELL_BOX = 2049       # 20
ED_ROCKET = 2010          # 1 PG-7V
ED_ROCKET_BOX = 2046      # 5 PG-7V
ED_CELL = 2047            # 20 fuel
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019

# Monsters per skill (Doom's skill pairs, udmf.skill_tier).
ENEMY_TOTALS = {2: 29, 3: 42, 4: 56}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Tier 2 is on
# every skill, 3 from medium up, 4 on hard only. Facing: 0 east, 90 north,
# 180 west, 270 south; most face where the player comes from.
MONSTERS = (
    # The tunnel's mouth: the Reich's picket either side of it in the yard,
    # backs to the yard's east wall, out of the tunnel's line: the start is
    # safe (tests/test_safe_starts.py); at the top of the stair they saw the
    # start 593 off, straight down the tunnel.
    ("z2_yard", "rifleman", 3776, 1056, 90, 2),
    ("z2_yard", "rifleman", 3776, 1312, 270, 4),
    # The yard, the Reich among the wagons.
    ("z2_yard", "rifleman", 3450, 900, 0, 2),
    ("z2_yard", "rifleman", 3550, 1460, 0, 2),
    ("z2_yard", "rifleman", 2400, 880, 0, 2),
    ("z2_yard", "hound", 2700, 1125, 0, 2),
    ("z2_yard", "rifleman", 2950, 1250, 0, 3),
    ("z2_yard", "stormtrooper", 2200, 1440, 0, 3),
    ("z2_yard", "rifleman", 3200, 1830, 0, 4),
    ("z2_yard", "stormtrooper", 2000, 880, 0, 4),
    # Snipers on the rake's roofs.
    ("z2_roof_2", "rifleman", 2780, 1600, 0, 2),
    ("z2_roof_4", "rifleman", 3400, 1600, 0, 2),
    ("z2_roof_3", "rifleman", 3100, 1600, 0, 3),
    ("z2_roof_1", "stormtrooper", 2470, 1600, 0, 4),
    # The signal box: the Legion's signalmen.
    ("z3_cabin", "trooper", 2240, 1530, 0, 2),
    ("z3_cabin", "trooper", 2240, 1670, 0, 4),
    # The goods warehouse: the Legion's depot, its first Doughboy.
    ("z4_hall", "trooper", 2560, 380, 90, 2),
    ("z4_hall", "trooper", 2100, 380, 90, 2),
    ("z4_hall", "trooper", 3050, 200, 90, 2),
    ("z4_hall", "stormtrooper", 2800, 380, 90, 2),
    ("z4_hall", "doughboy", 2600, 200, 90, 2),
    ("z4_office", "trooper", 3200, 600, 270, 2),
    ("z4_hall", "trooper", 2000, 560, 0, 3),
    ("z4_hall", "stormtrooper", 2350, 190, 90, 3),
    ("z4_hall", "trooper", 2950, 560, 180, 4),
    ("z4_hall", "doughboy", 2250, 570, 0, 4),
    # The roundhouse: the Reich's locomotives.
    ("z5_hall", "hound", 1400, 700, 0, 2),
    ("z5_hall", "hound", 600, 1550, 0, 2),
    ("z5_hall", "rifleman", 520, 800, 0, 2),
    ("z5_hall", "rifleman", 1450, 1500, 0, 2),
    ("z5_rails_stall", "panzermensch", 560, 1184, 0, 3),
    ("z5_hall", "hound", 1450, 900, 180, 3),
    ("z5_stall_2", "rifleman", 300, 1184, 0, 4),
    # The gondolas (the red key's counter-attack), mixed.
    ("z2_gondola_1", "trooper", 2960, 1344, 270, 2),
    ("z2_gondola_2", "rifleman", 2580, 1024, 90, 2),
    ("z2_gondola_1", "stormtrooper", 3040, 1344, 270, 3),
    ("z2_gondola_2", "hound", 2680, 1024, 90, 3),
    ("z2_gondola_1", "trooper", 3120, 1344, 270, 4),
    ("z2_gondola_2", "stormtrooper", 2760, 1024, 90, 4),
    # The platform, the climax: both factions round the armoured train.
    ("z6_platform", "panzermensch", 1100, 2300, 0, 2),
    ("z6_platform", "trooper", 2000, 2150, 0, 2),
    ("z6_platform", "trooper", 2600, 2340, 0, 2),
    ("z6_platform", "rifleman", 3100, 2300, 180, 2),
    ("z6_platform", "rifleman", 1600, 2340, 0, 2),
    ("z6_platform", "stormtrooper", 1300, 2150, 0, 2),
    ("z6_platform", "doughboy", 1800, 2300, 0, 2),
    ("z6_platform", "doughboy", 700, 2200, 0, 3),
    ("z6_platform", "trooper", 2300, 2200, 0, 3),
    ("z6_platform", "hound", 1500, 2130, 0, 3),
    ("z6_platform", "heavy", 500, 2300, 0, 4),
    ("z6_platform", "stormtrooper", 2800, 2300, 180, 4),
    ("z6_platform", "rifleman", 1200, 2340, 0, 4),
    # The armoured train, close quarters.
    ("z7_gun", "stormtrooper", 1500, 2528, 0, 2),
    ("z7_troop", "rifleman", 2000, 2528, 0, 2),
    ("z7_cab", "rifleman", 740, 2528, 0, 3),
    ("z7_gun", "panzermensch", 1650, 2528, 0, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on: 4 = every skill, 3 = medium and easier, 2 = easy only).
ITEMS = (
    # The weapons, on every skill, each before the fight it is for: the IZh
    # in the tunnel, the PPSh in the warehouse office, the RPG-7 at the
    # roundhouse's door (before its Panzermensch and the platform's).
    ("z1_tunnel", ED_IZH, 4100, 1136, 4),
    ("z4_office", ED_PPSH, 3250, 520, 4),
    ("z5_hall", ED_RPG7, 1500, 520, 4),
    # Shell boxes (20).
    ("z1_tunnel", ED_SHELL_BOX, 4200, 1232, 4),
    ("z2_yard", ED_SHELL_BOX, 3700, 1800, 4),
    ("z4_hall", ED_SHELL_BOX, 2560, 560, 4),
    ("z5_hall", ED_SHELL_BOX, 500, 600, 4),
    ("z6_vestibule", ED_SHELL_BOX, 2752, 1984, 4),
    ("z6_platform", ED_SHELL_BOX, 900, 2340, 4),
    ("z2_yard", ED_SHELL_BOX, 2600, 1830, 3),
    # Shells (4).
    ("z2_yard", ED_SHELLS, 3600, 900, 4),
    ("z2_roof_3", ED_SHELLS, 3000, 1600, 4),
    ("z4_hall", ED_SHELLS, 2000, 200, 4),
    ("z5_hall", ED_SHELLS, 1300, 600, 4),
    ("z6_platform", ED_SHELLS, 2200, 2340, 4),
    ("z2_yard", ED_SHELLS, 2300, 1800, 3),
    ("z4_hall", ED_SHELLS, 3200, 200, 3),
    ("z5_hall", ED_SHELLS, 600, 700, 3),
    ("z2_yard", ED_SHELLS, 3500, 1800, 2),
    ("z6_platform", ED_SHELLS, 2700, 2150, 2),
    # Boxes of rounds (50) and clips (10).
    ("z4_office", ED_CLIP_BOX, 3150, 600, 4),
    ("z5_hall", ED_CLIP_BOX, 1500, 1600, 4),
    ("z6_platform", ED_CLIP_BOX, 2500, 2150, 4),
    ("z1_mouth", ED_CLIP, 3900, 1184, 4),
    ("z3_cabin", ED_CLIP, 2160, 1520, 4),
    ("z2_yard", ED_CLIP, 3700, 1450, 3),
    ("z4_hall", ED_CLIP, 2700, 560, 2),
    # PG-7V: a box with the launcher, a box and loose rounds for the platform.
    ("z5_hall", ED_ROCKET_BOX, 1550, 600, 4),
    ("z6_vestibule", ED_ROCKET_BOX, 2720, 1984, 4),
    ("z6_platform", ED_ROCKET, 2900, 2150, 4),
    ("z6_platform", ED_ROCKET, 2900, 2400, 4),
    ("z6_office", ED_ROCKET, 3000, 2000, 4),
    ("z6_office", ED_ROCKET_BOX, 3150, 2000, 3),
    # Stimpacks.
    ("z2_yard", ED_STIMPACK, 3700, 900, 4),
    ("z4_hall", ED_STIMPACK, 2900, 600, 4),
    ("z5_hall", ED_STIMPACK, 1550, 1500, 4),
    ("z6_platform", ED_STIMPACK, 3250, 2400, 4),
    ("z7_troop", ED_STIMPACK, 2200, 2500, 4),
    ("z2_yard", ED_STIMPACK, 2100, 1800, 3),
    ("z4_hall", ED_STIMPACK, 1980, 360, 3),
    ("z6_platform", ED_STIMPACK, 3250, 2150, 3),
    ("z5_hall", ED_STIMPACK, 450, 450, 2),
    # Medikits.
    ("z3_cabin", ED_MEDIKIT, 2160, 1680, 4),
    ("z5_hall", ED_MEDIKIT, 1600, 1100, 4),
    ("z6_office", ED_MEDIKIT, 3080, 2000, 4),
    ("z7_gun", ED_MEDIKIT, 1400, 2570, 4),
    ("z6_platform", ED_MEDIKIT, 2400, 2400, 3),
    ("z4_hall", ED_MEDIKIT, 3250, 300, 3),
    # Armour: the flak vest in the warehouse, plates at both locks and on
    # the roofs.
    ("z4_hall", ED_GREEN_ARMOR, 2560, 470, 4),
    ("z2_yellow_portal", ED_ARMOR_BONUS, 2420, 800, 4),
    ("z2_yellow_portal", ED_ARMOR_BONUS, 2700, 800, 4),
    ("z2_red_portal", ED_ARMOR_BONUS, 2610, 1888, 4),
    ("z2_red_portal", ED_ARMOR_BONUS, 2890, 1888, 4),
    ("z2_roof_1", ED_ARMOR_BONUS, 2400, 1570, 4),
    ("z2_roof_1", ED_ARMOR_BONUS, 2400, 1630, 4),
    ("z6_platform", ED_ARMOR_BONUS, 2752, 2080, 3),
    # Health bonuses: one in each nook.
    ("z1_niche_1", ED_HEALTH_BONUS, 4192, 1256, 4),
    ("z1_niche_3", ED_HEALTH_BONUS, 4448, 1256, 4),
    ("z2_ramp_3", ED_HEALTH_BONUS, 3664, 1600, 4),
    ("z3_step", ED_HEALTH_BONUS, 2288, 1600, 4),
    ("z5_stall_1", ED_HEALTH_BONUS, 368, 512, 4),
    ("z5_road", ED_HEALTH_BONUS, 1712, 1184, 4),
    ("z5_porch", ED_HEALTH_BONUS, 1632, 512, 4),
    ("z6_balcony", ED_HEALTH_BONUS, 2400, 2560, 4),
    ("z7_engine", ED_HEALTH_BONUS, 1000, 2500, 4),
)

# The secrets' rewards, kept out of ITEMS (the route's) on purpose; on every
# skill, MAP01's rule.
SECRET_ITEMS = (
    # S1, the tunnel's cable box: the flak vest and two stimpacks, early help.
    ("s1_store", ED_GREEN_ARMOR, 4320, 1408, 4),
    ("s1_store", ED_STIMPACK, 4260, 1400, 4),
    ("s1_store", ED_STIMPACK, 4380, 1400, 4),
    # S2, the dark stall: the ROKS-3, a map early, and fuel.
    ("s2_store", ED_ROKS3, 96, 1472, 4),
    ("s2_store", ED_CELL, 64, 1400, 4),
    ("s2_store", ED_CELL, 128, 1540, 4),
    # S3, the crate set back: the heavy vest and rockets, for the platform.
    ("s3_store", ED_BLUE_ARMOR, 2720, 48, 4),
    ("s3_store", ED_ROCKET_BOX, 2660, 48, 4),
)


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0), on both faces
    (MAP02's and MAP03's helper, repeated so each map stays one file)."""
    return LineStyle(
        special=SPECIAL_DOOR_LOCKED_RAISE,
        args=(tag, DOOR_SPEED_SLOW, 0, lock, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,
    )


def secret_panel_style(tag: int, door_sector: int, texture: str) -> LineStyle:
    """A push panel that opens for good, one-sided on the automap."""
    panel = door_open_style(tag, door_sector, texture=texture)
    return replace(panel, flags=panel.flags + ("secret",))


def align_run(tm: TextMap, vertical: bool, coord: int, lo: int, hi: int, *, width: int,
              base: int = 0, offset_y: int | None = None) -> None:
    """Make one texture run continuously along the segment [lo, hi] of a grid
    line, however the painter split it into linedefs: on every sidedef there,
    the x offset is the run's `base` plus the distance from the segment's
    end on the viewer's left (each side sees its own left), modulo `width`.
    `offset_y`, when given, is set on the same sidedefs."""
    for ld in tm.linedefs:
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        if vertical:
            if not a.x == b.x == coord:
                continue
            p, q = a.y, b.y
        else:
            if not a.y == b.y == coord:
                continue
            p, q = a.x, b.x
        if min(p, q) < lo or max(p, q) > hi:
            continue
        # The front side reads its texture from v1 to v2, the back from v2 to v1.
        for side, start, end in ((ld.sidefront, p, q), (ld.sideback, q, p)):
            if side is None:
                continue
            sd = tm.sidedefs[side]
            sd.offsetx = int(base + (start - lo if end > start else hi - start)) % width
            if offset_y is not None:
                sd.offsety = offset_y


def align_car(tm: TextMap, rect, *, base: int) -> None:
    """A wagon's four faces: the long sides continuous from `base`, the ends
    whole; every face lifted WAGON_OFFSET_Y so the underframe meets the ground."""
    x1, y1, x2, y2 = rect
    for y in (y1, y2):
        align_run(tm, False, y, x1, x2, width=WAGON_TILE, base=base, offset_y=WAGON_OFFSET_Y)
    for x in (x1, x2):
        align_run(tm, True, x, y1, y2, width=WAGON_TILE, offset_y=WAGON_OFFSET_Y)


def world_column(tm: TextMap, ld, side: int) -> int:
    """Where the map's grid puts the first column of this side's texture:
    Doom runs a front side's texture from v1 to v2, a back side's from v2 to
    v1 (MAP05's helper; every line here is axis-aligned)."""
    a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
    if side == ld.sideback:
        a, b = b, a
    if a.y == b.y:
        return int(a.x) if b.x > a.x else -int(a.x)
    return int(a.y) if b.y > a.y else -int(a.y)


def glaze_the_box(tm: TextMap, plan: dict[str, int]) -> None:
    """SDSBOX1 in every window of the signal box, seen from the yard: the
    middle texture of each line between the window band and the open air,
    on the open air's side only (from inside, the yard is seen through the
    window). Doom hangs a two-sided middle texture from the lower ceiling,
    here the window head (208): `offsety_mid` (UDMF zdoom, added to the
    side's offsety) puts row 8 there, so rows 8-55 fill the 48-high opening.
    Columns on the 64 grid, so every pane is whole. The glass is opaque, so
    the line also blocks the monsters' sight: nobody in the box shoots
    through a pane nobody outside can see through (UDMF `blocksight`)."""
    sills = plan[f"{PROP_PREFIX}cabin_sills"]
    inside = {sills, plan["z3_cabin"], plan["z3_step"], plan["z3_frame"]}
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for side, other in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            if tm.sidedefs[other].sector != sills or tm.sidedefs[side].sector in inside:
                continue
            sd = tm.sidedefs[side]
            sd.texturemiddle = BOX_GLAZING
            sd.offsetx = world_column(tm, ld, side) % GLAZING_WIDTH
            sd.extra["offsety_mid"] = BOX_GLAZING_ROW
            ld.extra["blocksight"] = True


def hang_the_station_board(tm: TextMap, plan: dict[str, int]) -> None:
    """SDSTAN1 under the canopy over the platform's edge: the middle texture
    of the one line between the platform and the coping's board stretch, on
    the platform's side. Pegged to the canopy (256), it hangs 64 down to 192,
    over every head; nothing passes through it (a middle texture is not a
    wall: the line stays open to walk under)."""
    platform, under = plan["z6_platform"], plan["z6_coping_board"]
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        sectors = (tm.sidedefs[ld.sidefront].sector, tm.sidedefs[ld.sideback].sector)
        ends = (tm.vertices[ld.v1].y, tm.vertices[ld.v2].y)
        if set(sectors) != {platform, under} or ends != (COPING_EDGE_Y, COPING_EDGE_Y):
            continue
        side = ld.sidefront if sectors[0] == platform else ld.sideback
        tm.sidedefs[side].texturemiddle = STATION_BOARD
        tm.sidedefs[side].offsetx = (world_column(tm, ld, side) - STATION_BOARD_X[0]) % STATION_BOARD_SIZE[0]
        return
    raise ValueError("the station board's line is missing")


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=BRICK)
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

    def door(name: str, floor: int, tag: int, rect, *, light: int, wall: str = STEEL) -> int:
        """A closed door sector; its own walls are the steel track."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=wall)

    def rails(room: str, name: str, rect, flat: str = TRACK) -> int:
        """A 64-wide track along x, one flat tile wide on the 64 grid (so one
        track, never a rail of the next): turned a quarter (MAP02's K8)."""
        return like(room, name, [rect], flat=flat, extra={"rotationfloor": 90.0})

    def recess(room: str, name: str, rect, *, ceil: int, back, texture: str) -> int:
        """A shallow recess one tile high in `room`'s wall, its back wall one
        whole tile of `texture`. `back` is ("v", x, y1, y2) or ("h", y, x1, x2).
        A recess under the night sky gets a roof of its own: two sky ceilings
        side by side draw no wall between them, and the wall over the recess
        would vanish into the sky."""
        roofed = {"ceiling": CEIL_CONCRETE} if tm.sectors[plan[room]].textureceiling == SKY else {}
        index = like(room, name, [rect], ceil=ceil, **roofed)
        kind, coord, lo, hi = back
        if kind == "v":
            g.style_v(coord, lo, hi, LineStyle(texture=texture))
        else:
            g.style_h(coord, lo, hi, LineStyle(texture=texture))
        return index

    # ======================================================================
    # Z1: the service tunnel from Tankograd, and the stair up to the yard
    # ======================================================================
    zone("z1_tunnel", TUNNEL_FLOOR, TUNNEL_CEIL, [(4032, 1120, 4544, 1248)],
         light=LIGHT_TUNNEL, wall=TUBBING)
    # The tunnel keeps the metro's track bed on concrete (Tankograd's line).
    rails("z1_tunnel", "z1_tunnel_rails", (4032, 1152, 4544, 1216), flat=RAILS)
    for n, x in enumerate((4000, 3968, 3936), start=1):
        zone(f"z1_stair_{n}", TUNNEL_FLOOR + STEP * n, GROUND + TILE, [(x, 1120, x + 32, 1248)],
             light=LIGHT_TUNNEL, wall=CONCRETE)
    zone("z1_mouth", GROUND, GROUND + TILE, [(3840, 1120, 3936, 1248)],
         light=LIGHT_YARD, wall=BRICK)
    # The refuge niches; the middle one is S1's cable box, in shadow.
    for n, (x1, x2) in enumerate(TUNNEL_NICHES, start=1):
        dark = n - 1 == S1_NICHE_INDEX
        like("z1_tunnel", f"z1_niche_{n}", [(x1, 1248, x2, 1248 + NICHE_DEPTH)],
             light=LIGHT_NICHE if dark else LIGHT_TUNNEL, wall=TUNNEL_WALL)
        if not dark:
            g.style_h(1248 + NICHE_DEPTH, x1, x2, LineStyle(texture=TUNNEL_WALL))
    s1_panel = zone("s1_panel", TUNNEL_FLOOR, TUNNEL_FLOOR, [S1_PANEL], TAG_S1_PANEL,
                    light=LIGHT_NICHE, wall=TUNNEL_WALL)
    zone("s1_passage", TUNNEL_FLOOR, TUNNEL_CEIL, [S1_PASSAGE], light=LIGHT_SECRET,
         wall=TUNNEL_WALL)
    zone("s1_store", TUNNEL_FLOOR, TUNNEL_CEIL, [S1_STORE], light=LIGHT_SECRET,
         wall=TUNNEL_WALL, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # Z2: the yard, the hub. Night, under the open sky (SDSKY1): everything
    # standing in it (wagons, roofs, ramp, signals) shares its sky.
    # ======================================================================
    zone("z2_yard", GROUND, YARD_CEIL, [(1792, 768, 3840, 1920)],
         light=LIGHT_YARD, flat=BALLAST, ceiling=SKY, wall=BRICK)
    # The main track, from the tunnel's rails to the roundhouse's road gate,
    # and a siding along the north wall: track on ballast, each strip one
    # tile of the 64 grid.
    rails("z2_yard", "z2_rails_main", (1792, 1152, 3840, 1216))
    rails("z2_yard", "z2_rails_north", (1792, 1728, 3840, 1792))
    # A wagon's roof seen from above: its walkway runs along the car (x).
    roof = dict(flat=WAGON_ROOF, extra={"rotationfloor": 90.0})
    for name, (x1, y1, x2, y2, height, side) in WAGONS.items():
        like("z2_yard", name, [(x1, y1, x2, y2)], floor=GROUND + height, wall=side,
             **(roof if height == WAGON else {"flat": "SDCRTOP1"}))
    # The gondolas: an open bed inside a wagon's shell; the side towards the
    # main track is the red key's (it drops to the ground when the key is taken).
    for name, (shell, bed, side) in GONDOLAS.items():
        like("z2_yard", f"{PROP_PREFIX}{name[3:]}_shell", [shell], floor=GROUND + WAGON,
             wall=WAGON_SIDE, **roof)
        like("z2_yard", name, [bed], floor=GONDOLA_FLOOR, light=LIGHT_GONDOLA, wall=WAGON_SIDE,
             flat=GONDOLA_BED, extra={"rotationfloor": 90.0, "xpanningfloor": float(GONDOLA_PAN),
                                      "ypanningfloor": float(GONDOLA_PAN)})
        like("z2_yard", f"{name}_side", [side], floor=GROUND + WAGON, wall=WAGON_SIDE, **roof)
        tm.sectors[plan[f"{name}_side"]].identifier = TAG_GONDOLAS
    # The coupled rake: four boxcars' roofs, end to end, and the goods ramp
    # up to its east end.
    for n, (x1, x2) in enumerate(ROOFS, start=1):
        like("z2_yard", f"z2_roof_{n}", [(x1, ROW_3[0], x2, ROW_3[1])], floor=GROUND + WAGON,
             wall=WAGON_SIDE, light=LIGHT_ROOFS, **roof)
    for n, x in enumerate(RAMP_XS, start=1):
        like("z2_yard", f"z2_ramp_{n}", [(x, ROW_3[0], x + 32, ROW_3[1])],
             floor=GROUND + WAGON - STEP * n, wall=CONCRETE, flat=FLOOR_CONCRETE)
    # The signals: a concrete pillar one tile high each, the signal on one
    # face only (D107).
    for name, pillar, (fx, fy1, fy2) in SIGNALS:
        like("z2_yard", name, [pillar], floor=GROUND + SIGNAL_PILLAR, wall=CONCRETE,
             flat=FLOOR_CONCRETE)
        g.style_v(fx, fy1, fy2, LineStyle(texture=SIGNAL))
    # The goods warehouse's own gates on the yard, shut and padlocked, either
    # side of the yellow lock and well clear of it: each a whole tile at the
    # back of a recess cut to its height.
    for n, (x1, x2) in enumerate(GOODS_GATES, start=1):
        recess("z2_yard", f"z2_goods_gate_{n}", (x1, 768 - NICHE_DEPTH, x2, 768),
               ceil=GROUND + TILE, back=("h", 768 - NICHE_DEPTH, x1, x2), texture=GOODS_GATE)
    # The Reich's banner either side of the tunnel's mouth.
    recess("z2_yard", "z2_flag_s", (3840, 960, 3840 + NICHE_DEPTH, 1024),
           ceil=GROUND + TILE, back=("v", 3840 + NICHE_DEPTH, 960, 1024), texture=FLAG_REICH)
    recess("z2_yard", "z2_flag_n", (3840, 1344, 3840 + NICHE_DEPTH, 1408),
           ceil=GROUND + TILE, back=("v", 3840 + NICHE_DEPTH, 1344, 1408), texture=FLAG_REICH)
    # The yellow door's portal band in the south wall, the red door's in
    # the north wall: 128 high, so each leaf and its flanks are one tile.
    zone("z2_yellow_portal", GROUND, DOOR_HEIGHT, [(2368, 768, 2752, 832)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=BRICK, extra=YELLOW_LIGHT)
    yellow_door = door("yellow_door", GROUND, TAG_YELLOW_DOOR, (2496, 736, 2624, 768),
                       light=LIGHT_WAREHOUSE)
    zone("z2_red_portal", GROUND, DOOR_HEIGHT, [(2560, 1856, 2944, 1920)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=BRICK, extra=RED_LIGHT)
    red_door = door("red_door", GROUND, TAG_RED_DOOR, (2688, 1920, 2816, 1952),
                    light=LIGHT_PLATFORM)

    # ======================================================================
    # Z3: the signal box, a brick tower at the rake's west end
    # ======================================================================
    # The window band and the porch from the roofs are open to the sky: from
    # the yard the box is its brick tower, the lit glazing (SDSBOX1, hung on
    # the band's outer lines after the build) and the night above the window
    # heads; the cabin's own ceiling is inside.
    zone(f"{PROP_PREFIX}cabin_sills", SILL, LINTEL, list(SILLS), light=LIGHT_CABIN,
         ceiling=SKY, wall=BRICK, extra=YELLOW_LIGHT)
    zone("z3_step", CABIN - STEP, CABIN_CEIL, [CABIN_STEP], light=LIGHT_CABIN,
         flat=GRATING, ceiling=SKY, wall=BRICK)
    zone("z3_cabin", CABIN, CABIN_CEIL, [CABIN_ROOM], light=LIGHT_CABIN, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=TILE_DADO, extra=YELLOW_LIGHT)
    zone("z3_frame", LEVER_FRAME, CABIN_CEIL, [LEVER_FRAME_RECT], light=LIGHT_BEACON,
         flat=LEVER_TOP, ceiling=CEIL_PANEL, wall=LEVER_FRONT,
         extra={**YELLOW_LIGHT, "rotationfloor": LEVER_ROTATION,
                "xpanningfloor": float(LEVER_PAN), "ypanningfloor": float(LEVER_PAN)})

    # ======================================================================
    # Z4: the goods warehouse, behind the yellow door
    # ======================================================================
    zone("z4_vestibule", GROUND, DOOR_HEIGHT, [(2496, 640, 2624, 736)],
         light=LIGHT_WAREHOUSE, wall=BRICK_DADO)
    zone("z4_hall", GROUND, WAREHOUSE_CEIL, [(1920, 128, 3328, 640)],
         light=LIGHT_WAREHOUSE, ceiling=CEIL_PANEL, wall=BRICK)
    for n, rect in enumerate(((2048, 448, 2304, 512), (2816, 448, 3008, 512),
                              (2176, 256, 2432, 320), (2688, 256, 2944, 320)), start=1):
        like("z4_hall", f"{PROP_PREFIX}stack_{n}", [rect], floor=GROUND + TILE, wall=CRATE,
             flat="SDCRTOP1")
    # The office in the north-east corner, behind D2.
    g.carve(3072, 448, 3328, 640)
    zone("z4_office", GROUND, DOOR_HEIGHT, [(3088, 464, 3328, 640)],
         light=LIGHT_OFFICE, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    like("z4_hall", "z4_porch", [(3152, 384, 3280, 448)], ceil=DOOR_HEIGHT)
    d2 = door("d2_office", GROUND, TAG_D2_OFFICE, (3152, 448, 3280, 464), light=LIGHT_OFFICE)
    # The Legion's banner on the east wall.
    recess("z4_hall", "z4_flag", (3328, 192, 3328 + NICHE_DEPTH, 256),
           ceil=GROUND + TILE, back=("v", 3328 + NICHE_DEPTH, 192, 256), texture=FLAG_LEGION)
    # S3: the crate set back in the south wall's row, in shadow.
    like("z4_hall", "s3_niche", [S3_NICHE], ceil=GROUND + TILE, light=LIGHT_NICHE, wall=CRATE)
    s3_panel = zone("s3_panel", GROUND, GROUND, [S3_PANEL], TAG_S3_PANEL, light=LIGHT_NICHE,
                    wall=CRATE)
    zone("s3_store", GROUND, GROUND + TILE, [S3_STORE], light=LIGHT_SECRET, wall=CRATE,
         special=SECTOR_SPECIAL_SECRET)
    # The passage west to the roundhouse, D1 at its far end.
    zone("z4_passage", GROUND, DOOR_HEIGHT, [(1696, 448, 1920, 576)],
         light=LIGHT_WAREHOUSE, wall=BRICK_DADO)
    d1 = door("d1_roundhouse", GROUND, TAG_D1_ROUNDHOUSE, (1664, 448, 1696, 576),
              light=LIGHT_ROUNDHOUSE)

    # ======================================================================
    # Z5: the roundhouse and its turntable
    # ======================================================================
    zone("z5_hall", GROUND, ROUNDHOUSE_CEIL, [(384, 384, 1664, 1664)],
         light=LIGHT_ROUNDHOUSE, wall=ROUNDHOUSE_BRICK)
    like("z5_hall", "z5_porch", [(1600, 448, 1664, 576)], ceil=DOOR_HEIGHT)
    tx1, ty1, tx2, ty2 = TURNTABLE
    bx1, by1, bx2, by2 = TURNTABLE_BRIDGE
    like("z5_hall", "z5_pit_s", [(tx1, ty1, tx2, by1)], floor=PIT, wall=CONCRETE)
    like("z5_hall", "z5_pit_n", [(tx1, by2, tx2, ty2)], floor=PIT, wall=CONCRETE)
    # Three steps up out of each half of the pit, at its outer edge.
    for n in range(1, 4):
        y = ty1 + 32 * (n - 1)
        like("z5_hall", f"z5_pit_s_{n}", [(960, y, 1088, y + 32)], floor=GROUND - STEP * n,
             wall=CONCRETE)
        y = ty2 - 32 * n
        like("z5_hall", f"z5_pit_n_{n}", [(960, y, 1088, y + 32)], floor=GROUND - STEP * n,
             wall=CONCRETE)
    # The bridge: an expanded-metal deck over the pit, its one track down
    # the middle (either side of the king post), in line with the yard's.
    like("z5_hall", "z5_bridge", [TURNTABLE_BRIDGE], flat=DECK, wall=STEEL, extra={})
    hx1, hy1, hx2, hy2 = HUB_RECT
    rails("z5_bridge", "z5_bridge_track_w", (bx1, hy1, hx1, hy2))
    rails("z5_bridge", "z5_bridge_track_e", (hx2, hy1, bx2, hy2))
    zone("z5_hub", HUB, ROUNDHOUSE_CEIL, [HUB_RECT], light=LIGHT_BEACON, flat=FLOOR_PLATE,
         wall=STEEL, extra=RED_LIGHT)
    rails("z5_hall", "z5_rails_road", (bx2, 1152, 1664, 1216))
    rails("z5_hall", "z5_rails_stall", (384, 1152, bx1, 1216))
    # The road out to the yard and its gate (SW-A): steel from the
    # roundhouse, the yard's own brick from the yard (wall until it opens).
    zone("z5_road", GROUND, DOOR_HEIGHT, [ROAD],
         light=LIGHT_ROUNDHOUSE, wall=ROUNDHOUSE_BRICK)
    shutter = door("shutter", GROUND, TAG_SHUTTER, (1760, 1120, 1792, 1248), light=LIGHT_YARD)
    zone("z5_swa_niche", GROUND, GROUND + SWITCH_HEIGHT, [SW_A_NICHE], light=LIGHT_ROUNDHOUSE,
         wall=ROUNDHOUSE_BRICK)
    # The stalls: a locomotive in the first, a shut gate at the back of the
    # second, and the third dark, its gate S2's panel. Ballast underfoot: a
    # stall is 128 wide, and a track flat across it would show a second
    # track's rails (the stall's track is pending, design document §7.2).
    for name, rect in STALLS.items():
        ceil = LOCO_STALL_CEIL if name == "z5_stall_1" else STALL_CEIL
        light = LIGHT_DARK_STALL if name == "z5_stall_3" else LIGHT_STALL
        zone(name, GROUND, ceil, [rect], light=light, flat=BALLAST, wall=ROUNDHOUSE_BRICK)
    like("z5_stall_1", f"{PROP_PREFIX}loco", [(192, 464, 352, 560)], floor=GROUND + WAGON,
         wall=STEEL, flat=FLOOR_PLATE)
    g.style_v(192, 1120, 1248, LineStyle(texture=STALL_DOORS))
    s2_panel = zone("s2_panel", GROUND, GROUND, [S2_PANEL], TAG_S2_PANEL,
                    light=LIGHT_DARK_STALL, wall=STALL_DOORS)
    zone("s2_store", GROUND, GROUND + TILE, [S2_STORE], light=LIGHT_SECRET, wall=ROUNDHOUSE_BRICK,
         special=SECTOR_SPECIAL_SECRET)
    for n, x in enumerate(CLERESTORY, start=1):
        recess("z5_hall", f"{PROP_PREFIX}clerestory_{n}", (x, 1664, x + 64, 1664 + NICHE_DEPTH),
               ceil=ROUNDHOUSE_CEIL, back=("h", 1664 + NICHE_DEPTH, x, x + 64), texture=WINDOW)
        tm.sectors[plan[f"{PROP_PREFIX}clerestory_{n}"]].heightfloor = CLERESTORY_SILL

    # ======================================================================
    # Z6: the passenger platform, behind the red door
    # ======================================================================
    zone("z6_vestibule", GROUND, DOOR_HEIGHT, [(2688, 1952, 2816, 2016)],
         light=LIGHT_PLATFORM, flat=FLOOR_STATION, ceiling=CEIL_PANEL, wall=STATION)
    zone("z6_step", GROUND + STEP, DOOR_HEIGHT, [(2688, 2016, 2816, 2048)],
         light=LIGHT_PLATFORM, flat=FLOOR_STATION, ceiling=CEIL_PANEL, wall=STATION)
    zone("z6_platform", PLATFORM, PLATFORM_CEIL, [(384, 2048, 3328, 2432)],
         light=LIGHT_PLATFORM, flat=FLOOR_STATION, ceiling=CEIL_PANEL, wall=STATION)
    like("z6_platform", "z6_coping", [(576, COPING_EDGE_Y, 2304, 2432)], flat=FLOOR_COPING,
         extra={"rotationfloor": 180.0})
    # The coping under the station board, a sector of its own (the same in
    # every respect) so that the board's stretch of the platform's edge is a
    # line exactly one board long: a middle texture repeats along its line.
    board_x1, board_x2 = STATION_BOARD_X
    like("z6_coping", "z6_coping_board", [(board_x1, COPING_EDGE_Y, board_x2, 2432)])
    for x in COLUMNS:
        g.carve(x, COLUMN_Y[0], x + 64, COLUMN_Y[1])
    # Both banners side by side over the station (LORE: the two factions).
    for name, x, texture in (("z6_flag_reich", 1536, FLAG_REICH), ("z6_flag_legion", 1664, FLAG_LEGION)):
        recess("z6_platform", name, (x, 2048 - NICHE_DEPTH, x + 64, 2048),
               ceil=PLATFORM + TILE, back=("h", 2048 - NICHE_DEPTH, x, x + 64), texture=texture)
    zone("z6_office", PLATFORM, PLATFORM + SWITCH_HEIGHT, [(2944, 1952, 3200, 2048)],
         light=LIGHT_STATIONMASTER, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    zone("z6_balcony", TRAIN_FLOOR, TRAIN_CEIL, [BALCONY],
         light=LIGHT_TRAIN, flat=FLOOR_PLATE, wall=ARMOUR)

    # ======================================================================
    # Z7: the armoured train, rear hatch to the locomotive's cab. Armour
    # plate (one tile high inside: 48..176); the locomotive's cab is a steam
    # cab from inside (D113): its sides SDCAB2, its front the backhead SDCAB1,
    # the exit's niche (the regulator) cut into the middle of it.
    # ======================================================================
    train = dict(light=LIGHT_TRAIN, flat=FLOOR_PLATE, ceiling=CEIL_CONCRETE, wall=ARMOUR)
    zone("z7_exit_niche", TRAIN_FLOOR, TRAIN_CEIL, [(624, 2496, 640, 2560)],
         **{**train, "light": LIGHT_BEACON, "wall": STEEL})
    zone("z7_cab", TRAIN_FLOOR, TRAIN_CEIL, [(640, 2464, 832, 2592)],
         **{**train, "light": LIGHT_CAB, "ceiling": CEIL_PANEL, "wall": CAB_SIDE})
    zone("z7_engine", TRAIN_FLOOR, TRAIN_CEIL, [(832, 2464, 1216, 2592)], **train)
    zone("z7_couple_1", TRAIN_FLOOR, TRAIN_CEIL, [(1216, 2496, 1280, 2560)], **train)
    zone("z7_gun", TRAIN_FLOOR, TRAIN_CEIL, [(1280, 2464, 1792, 2592)], **train)
    zone("z7_couple_2", TRAIN_FLOOR, TRAIN_CEIL, [(1792, 2496, 1856, 2560)], **train)
    zone("z7_troop", TRAIN_FLOOR, TRAIN_CEIL, [(1856, 2464, 2272, 2592)], **train)
    hatch = door("z7_hatch", TRAIN_FLOOR, TAG_HATCH, (2272, 2464, 2304, 2592), light=LIGHT_TRAIN)

    # ======================================================================
    # The posters' niches (tests/test_posters.py)
    # ======================================================================
    for name, room, rect, height in POSTER_NICHES:
        s = tm.sectors[plan[room]]
        like(room, name, [rect], ceil=s.heightfloor + height,
             light=s.lightlevel + LIGHT_POSTER_STEP, ceiling=CEIL_PANEL)

    # ======================================================================
    # Line styles: the posters first (GridMap keeps the first style
    # registered on a segment), doors, locks, switches, the exit, the train
    # ======================================================================
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    # D1 and D2: manual doors, a leaf on both faces.
    for x in (1664, 1696):
        g.style_v(x, 448, 576, door_raise_style(TAG_D1_ROUNDHOUSE, d1, texture=DOOR))
    for y in (448, 464):
        g.style_h(y, 3152, 3280, door_raise_style(TAG_D2_OFFICE, d2, texture=DOOR))
    # The yellow door between two star plaques; the red door between plain
    # whitewashed brick (MAP03 v1's rule for the red lock).
    for y in (736, 768):
        g.style_h(y, 2496, 2624, locked_door_style(TAG_YELLOW_DOOR, yellow_door,
                                                   LOCK_YELLOW_CARD, texture=DOOR_YELLOW))
    g.style_h(768, 2368, 2496, LineStyle(texture=STAR))
    g.style_h(768, 2624, 2752, LineStyle(texture=STAR))
    for y in (1920, 1952):
        g.style_h(y, 2688, 2816, locked_door_style(TAG_RED_DOOR, red_door,
                                                   LOCK_RED_CARD, texture=DOOR_RED))
    g.style_h(1920, 2560, 2688, LineStyle(texture=BRICK_DADO))
    g.style_h(1920, 2816, 2944, LineStyle(texture=BRICK_DADO))
    # The road gate: steel from the roundhouse, brick from the yard.
    g.style_v(1760, 1120, 1248, remote_door_style(shutter, texture=STEEL))
    g.style_v(1792, 1120, 1248, remote_door_style(shutter, texture=BRICK))
    g.style_h(SW_A_NICHE[3], SW_A_NICHE[0], SW_A_NICHE[2],
              switch_door_open_style(TAG_SHUTTER, texture=SW_A_FACE, repeatable=False))
    # The pit's walls are concrete whichever side they are seen from.
    for y in (ty1, ty2):
        g.style_h(y, tx1, 960, LineStyle(texture=CONCRETE))
        g.style_h(y, 1088, tx2, LineStyle(texture=CONCRETE))
    for x in (tx1, tx2):
        g.style_v(x, ty1, by1, LineStyle(texture=CONCRETE))
        g.style_v(x, by2, ty2, LineStyle(texture=CONCRETE))
    # The hatch: a leaf on both faces; SW-B on the office's back wall.
    for x in (2272, 2304):
        g.style_v(x, 2464, 2592, remote_door_style(hatch, texture=DOOR))
    g.style_h(1952, 3040, 3104, switch_door_open_style(TAG_HATCH, texture=SW_B_FACE,
                                                       repeatable=False))
    # The train's flank along the platform is armour plate, not station tile:
    # plain plate (224 high, so a star there would be stacked), 27 whole
    # plates from the coping up; the stars are on the faces one tile high.
    flank_y, flank_x1, flank_x2 = TRAIN_FLANK
    g.style_h(flank_y, flank_x1, flank_x2, LineStyle(texture=ARMOUR))
    for y, x1, x2 in STAR_PANELS:
        g.style_h(y, x1, x2, LineStyle(texture=ARMOUR_STAR))
    # The exit: the regulator panel on the cab's front wall, in its niche
    # cut into the middle of the backhead (SDCAB1, aligned after the build).
    g.style_v(624, 2496, 2560, exit_switch_style(texture=EXIT_FACE))
    fx, fy1, fy2 = CAB_FRONT_WALL
    g.style_v(fx, fy1, fy2, LineStyle(texture=CAB_FRONT))
    # The secrets' panels, flagged secret (one-sided on the automap).
    nx1, nx2 = TUNNEL_NICHES[S1_NICHE_INDEX]
    for y in (S1_PANEL[1], S1_PANEL[3]):
        g.style_h(y, nx1, nx2, secret_panel_style(TAG_S1_PANEL, s1_panel, CONCRETE))
    for x in (S2_PANEL[0], S2_PANEL[2]):
        g.style_v(x, S2_PANEL[1], S2_PANEL[3], secret_panel_style(TAG_S2_PANEL, s2_panel, STALL_DOORS))
    for y in (S3_PANEL[1], S3_PANEL[3]):
        g.style_h(y, S3_PANEL[0], S3_PANEL[2], secret_panel_style(TAG_S3_PANEL, s3_panel, CRATE))
    # S3's row: crates on the warehouse's south wall either side of the niche.
    cx1, cx2, cy = CRATE_ROW
    g.style_h(cy, cx1, S3_NICHE[0], LineStyle(texture=CRATE))
    g.style_h(cy, S3_NICHE[2], cx2, LineStyle(texture=CRATE))

    g.build()

    # ======================================================================
    # Alignment of the Railway set (after the painter has split the lines)
    # ======================================================================
    for x1, y1, x2, y2, _height, side in WAGONS.values():
        if side in (WAGON_SIDE, TANK_SIDE):
            align_car(tm, (x1, y1, x2, y2),
                      base=WAGON_OFFSET_X if side == WAGON_SIDE else TANK_OFFSET_X)
    for shell, _bed, _side in GONDOLAS.values():
        align_car(tm, shell, base=WAGON_OFFSET_X)
    for x1, x2 in ROOFS:
        align_car(tm, (x1, ROW_3[0], x2, ROW_3[1]), base=WAGON_OFFSET_X)
    # The balcony's back: the star panel starts on a plate seam.
    _y, star_x1, _x2 = STAR_PANELS[-1]
    align_run(tm, False, BALCONY[3], BALCONY[0], BALCONY[2], width=ARMOUR_WIDTH,
              base=BALCONY[0] - star_x1)

    # ======================================================================
    # Round 2 (D113): the cab's backhead, the lever frame's front, the box's
    # glazing, the station board
    # ======================================================================
    # The backhead runs as one tile across the cab's front, the exit's niche
    # cut into its middle: its round windows and its sides either side.
    align_run(tm, True, fx, fy1, fy2, width=TILE)
    frame, cabin = plan["z3_frame"], plan["z3_cabin"]
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for side, other in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            # The frame's 16-high front, seen from the cabin: its plates and bed.
            if tm.sidedefs[side].sector == cabin and tm.sidedefs[other].sector == frame:
                tm.sidedefs[side].offsety = LEVER_FRONT_ROW
    glaze_the_box(tm, plan)
    hang_the_station_board(tm, plan)

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD))
    special, args = RED_KEY_PICKUP_SPECIAL
    tm.add_thing(Thing(x=RED_KEY_SPOT[0], y=RED_KEY_SPOT[1], type=ED_RED_CARD,
                       extra={"special": special, **{f"arg{i}": a for i, a in enumerate(args)}}))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle))
    for _zone, ednum, x, y, top in ITEMS + SECRET_ITEMS:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top)))
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
WALL_TEXTURES = ((CONCRETE, STAR, STEEL, TILE_DADO, CRATE, TUBBING, TUNNEL_WALL, STATION,
                  BRICK, BRICK_DADO, WINDOW, FLAG_REICH, FLAG_LEGION,
                  LENIN, STALIN, MURAL,
                  WAGON_SIDE, TANK_SIDE, ARMOUR_STAR, ARMOUR, SIGNAL, ROUNDHOUSE_BRICK, GOODS_GATE,
                  CAB_FRONT, CAB_SIDE, BOX_GLAZING, LEVER_FRONT, STALL_DOORS, STATION_BOARD)
                 + DOOR_LEAVES + SWITCH_FACES + ((MARX_ENGELS,) if MARX_ENGELS else ()))
FLAT_TEXTURES = (FLOOR_CONCRETE, FLOOR_TILE, CEIL_PANEL, CEIL_CONCRETE, FLOOR_STATION,
                 FLOOR_COPING, RAILS, FLOOR_PLATE, GRATING, "SDCRTOP1", TRACK, BALLAST, DECK,
                 WAGON_ROOF, GONDOLA_BED, LEVER_TOP)
# The engine's own flats, not lumps of ours (check_pk3 knows them).
BUILTIN_FLATS = (SKY,)
# Middle textures on two-sided lines, drawn once: the box's glazing and the
# station board. Nothing else hangs in mid-air.
MIDDLE_TEXTURES = (BOX_GLAZING, STATION_BOARD)
