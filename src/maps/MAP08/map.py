"""MAP08 «Североморск» / Severomorsk - v1: the whole map, textured and populated.

Design document: docs/levels/MAP08-severomorsk.md (section 13 is this build).
Episode 3, «The Portal» (D112), its second map: the Northern Fleet's
submarine base at Severomorsk on the Kola peninsula, November 1977, taken by
the Liberty Legion and the Fourth Reich, who are shipping a cargo by sea and
rail towards the portal at Tunguska. Sergeant Vilanova arrives where MAP07
leaves him: by the fjord, in a patrol launch, at the outer pier; he leaves
by the goods train standing in the rail tunnel to the east (MAP09).

Built MVP first (D60): complete and walkable from start to exit, three keys
on the route in plain sight on lit places in their lock's colour (MAP02's
lesson, D58), the population and the ammunition of G3-8's budget, three
secrets. Balance and light are later passes. Approved lumps only: since
D113 the "Naval" set itself (the living rock, the hull, the containers, the
crane lattice, the quays' kerbs), and the nearest installed lump for each
naval piece never drawn (`NAVAL_SET`, `PENDING_TEXTURES`).

The route, in one line: the outer pier (the RED GATE of the rail tunnel seen
across the container yard, shut) -> the yard -> D1 into the covered dock cut
in the rock (the BLUE DOOR and the YELLOW DOOR seen across the basin) -> up
the gangway onto the submarine's deck -> D3, the bulkhead hatch, into the
boat: the control room and its periscope, SW-A, which opens the watertight
door -> the torpedo room: the BLUE KEY on the loading tray -> the blue door:
the workshops and the torpedo store, the YELLOW KEY on the torpedo cart ->
the yellow door (and the tunnel's two closets): down the rock tunnel to the
reactor hall, the RED KEY on the reactor's lid; SW-B in the passage opens a
shutter into the fleet barracks, the way back -> the red gate (and the
yard's two closets) -> the rail tunnel east -> the loading bay, the goods
train, the exit switch in the locomotive's cab.

Heights: the quays, the yard, the pier and the barracks are the ground (0);
the dock's water -64, the submarine's deck and inside +32, its fin +160; the
crane's deck and the dock's crane gallery +192, the workshop's gantry +128;
the reactor hall -128 deep in the rock, the reactor's lid +64 over it.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.
Outdoors (pier, yard) the ceiling is F_SKY1, the engine's sky marker. The
fjord is a prop of water under a low sky ceiling: the eye sees the water and
the far shore, nobody can walk into it (its opening over the pier is lower
than any body, tested). The covered dock, the rock tunnels and the reactor
hall are roofed: the base is cut into the granite (D112's brief).

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP08 SKILL=3 tools/run.sh
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

MAP_NAME = "MAP08"

# --- The approved lumps (docs/art/TEXTURE-INDEX.md) ---------------------------
# The "Naval" set (D113, gen_naval.py) is installed and worn: NAVAL_SET says
# which lump the map wears for each naval piece the design asked for (itself
# where it was drawn, the nearest installed lump where it never was),
# PENDING_TEXTURES what the map still waits for.
ROCK = "SDROCK1"         # 64x128 the living Kola gneiss: the cliffs, the dock, the tunnels, the reactor hall
ROCK_CEIL = "SDROCK2"    # the same rock as a ceiling: over the dock, the tunnels, the reactor hall
DAM_WET = "SDDAM2"       # 64x128 concrete at the waterline: the quays' faces in the water
CONCRETE = "SDCONC1"     # prefab panels: the barracks' corridor, the torpedo store, the shelter S1
CONCRETE_STRIPE = "SDCONC2"  # the red-striped prefab: the barracks' hall and mess
STEEL = "SDSTEL1"        # green riveted plate: the boat's inside, racks, lathes, the reactor's jacket
BRICK = "SDBRCK1"        # works brick: the workshops
BRICK_RAIL = "SDBRCK3"   # roundhouse brick: the loading bay
RUST = "SDRUST1"         # corrugated sheet: the yard's fence, the crane's tower and cab
CONTAINER_SIDE = "SDCONT1"  # 128x128 a container's side («ММФ»): one container per tile, one tile high
HULL = "SDHULL1"         # 128x128 the submarine's black anechoic tiles: hull, stern and fin
HULL_NUMBER = "SDHULL2"  # 128x128 the same hull with «471»: once on each long face of the fin
ARMOUR = "SDARMR2"       # 64x128 armour plate: the patrol launch, the locomotive's body
WAGON = "SDWAGN1"        # 128x128 covered goods wagon side
TANK = "SDTANK1"         # 128x128 tank wagon side
LOCKER = "SDLOCK1"       # 64x128 barracks lockers: the dormitory's north wall (and S2's panel)
NAVAL_PANEL = "SDNAVC1"  # 128x128 the boat's control-room panel: its two long walls
CAB_FRONT = "SDCAB1"     # 128x128 the locomotive's cab, the backhead and gauges: the cab's south wall
CAB_SIDE = "SDCAB2"      # 64x128 the cab's side from inside, a window per tile: its other walls
TUBBING = "SDTUBB1"      # 128x128 cast-iron segments: the bow's torpedo tubes (SDTORP1 never drawn)
CRANE_LATTICE = "SDCRAN1"  # 64x128 MASKED (RGBA, hard alpha): a crane's lattice, two-sided lines
DOOR = "SDDOOR1"         # D1 and D2
DOOR_BLUE = "SDDOORB"    # the blue door
BULKHEAD_DOOR = "SDBULK1"  # 128x128 the round watertight door: D3, the bulkhead hatch into the boat
DOOR_YELLOW = "SDDOORY"
DOOR_RED = "SDDOORR"
ROAD_GATE = "SDGATE1"    # corrugated gate: S3, the crane's cab
CRATE = "SDCRAT1"        # the cargo bound for Tunguska
FLAG_REICH = "SDFLAG1"   # both banners side by side by the train (D35)
FLAG_LEGION = "SDFLAG2"
LENIN = "SDPOSTR1"       # 128x256: the barracks' hall
STALIN = "SDPOSTR3"      # 128x256: the dock's south wall, facing the boat
MURAL = "SDPOSTR2"       # 128x128 cosmonautics mural: the mess, on a sill
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
FLOOR_LANE = "SDFLR1"
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
FLOOR_PLATE = "SDFLR4"   # chequer plate: the boat's inside, pads, the lid
DECK_RUBBER = "SDRUBR1"  # the submarine's deck from above: anechoic rubber tiles
DECK_HATCH = "SDRUBR2"   # the same deck with a flush round escape hatch: one tile, aft of the fin
PIER_EDGE = "SDPIER1"    # concrete quay edge: a bollard, the kerb and the steel angle at the tile's bottom
CEIL_PANEL = "SDCEIL1"
CEIL_CONCRETE = "SDCEIL2"
CRATE_TOP = "SDCRTOP1"
GRATING = "SDGRAT2"      # expanded metal: gangways, galleries, the crane's stair
WATER = "SDWATR1"        # the fjord and the dock: SDWATR1-4 animate through ANIMDEFS
TRACK = "SDTRAK1"        # track on ballast, rails along the image's y: turned a quarter
BALLAST = "SDBLST1"
SKY = "F_SKY1"           # the engine's sky marker, not a lump of ours

# Switches (D25), one variant per switch; the exit wears the hazard panel.
SW_A_FACE = "SDSW1A"     # the boat's control room: the knife switch, the watertight door
SW_B_FACE = "SDSW1B"     # the passage: the push button, the shutter into the barracks
EXIT_FACE = "SDSW1D"
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64
SWITCH_HEIGHT = 128
TILE = 128
WALL_TILE = 128          # the height every wall lump here repeats at
DOOR_LEAVES = (DOOR, DOOR_BLUE, DOOR_YELLOW, DOOR_RED, BULKHEAD_DOOR)
# The widths `align_to_world` lines up along a wall: a wall split by its
# neighbours' corners shows no seam. HULL_NUMBER, the doors and the posters
# are single pieces on lines exactly their width and keep offset 0.
LUMP_WIDTH = {ROCK: 64, DAM_WET: 64, HULL: 128, CAB_FRONT: 128, CAB_SIDE: 64, CRANE_LATTICE: 64}
FLAT_TILE = 64
# SDPIER1's kerb is at the bottom of the image, i.e. the SOUTH edge of each
# tile (Doom draws a flat with the image's top to the north). Each kerb strip
# turns it to the water: {which side the water is on: rotationfloor}. 0 and
# 180 hold whatever way the engine turns; 270 for the west edge assumes
# GZDoom turns a flat counter-clockwise (NOT VERIFIED: engine check V11; if
# the kerb lies on the land side it is 90).
KERB_ROTATION = {"south": 0.0, "north": 180.0, "west": 270.0}
# The escape hatch's tile centred on the hull's axis (y 1984, a tile edge):
# half a tile of panning, the same whichever way the engine pans.
HATCH_PANNING = FLAT_TILE // 2

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED in engine
# on MAP02 and MAP03. Delay 0: opens and stays open.
SPECIAL_DOOR_LOCKED_RAISE = 13
# gzdoom.pk3 g4.14.2 lockdefs.txt: Lock 1 RedCard, Lock 2 BlueCard, Lock 3
# YellowCard; all three opened in the engine before (MAP02, MAP03, MAP04).
LOCK_RED_CARD = 1
LOCK_BLUE_CARD = 2
LOCK_YELLOW_CARD = 3
# Doom's editor numbers; SD_BluePass, SD_YellowPass and SD_RedPass replace
# the cards (src/zscript/sd/keys.zs).
ED_BLUE_CARD = 5
ED_YELLOW_CARD = 6
ED_RED_CARD = 13
KEY_LOCKS = {ED_BLUE_CARD: LOCK_BLUE_CARD, ED_YELLOW_CARD: LOCK_YELLOW_CARD, ED_RED_CARD: LOCK_RED_CARD}
ED_PLAYER1_START = 1

# --- Heights -------------------------------------------------------------------
GROUND = 0              # pier, yard, quays, barracks, workshops, rail tunnel, bay
BASIN = -64             # the dock's water and the fjord
DECK = 32               # the submarine's deck and its inside
FIN = DECK + 128        # the fin's top: SDARMR1's star exactly once on each face
CRANE = 192             # the crane's deck on the pier, the dock's crane gallery
GANTRY = 128            # the workshop's gantry
REACTOR = -128          # the reactor hall, down in the rock
LID = REACTOR + 192     # +64: the reactor's lid, the red key
STEP = 16               # every stair step; under MAX_STEP_UP 24
STEP_RUN = 32
GANGWAY = GROUND + STEP  # quay 0 -> gangway 16 -> deck 32
STERN = DECK - STEP     # the stern's tapering casing: one step down from the deck
PAD = 16                # the key pads: one step up
CONTAINER = 128         # a container's top (one SDRUST1 tile)
CARGO = 64              # a crate's top (one SDCRAT1 tile)
WAGON_TOP = 128
FENCE = 128
LATHE = 48
RACK = 48               # the torpedo store's racks
BOAT_RACK = DECK + 32   # the torpedo room's racks
TABLE = 32
BUNK = 48
LAUNCH_DECK = 32
WHEELHOUSE = 96
SKY_CEIL = 768          # outdoors
FJORD_SKY = 48          # the fjord's low sky: 48 over the pier, under any body (56)
FENCE_SKY = FENCE + 16  # the open-air trick over the fence
LAUNCH_SKY = WHEELHOUSE + 16
PEN_ROOF = 448          # the covered dock, cut in the rock
INTERIOR = DECK + 128   # 160: the boat's inside, one tile high
PORCH = GROUND + 128    # the roofed porch in front of every door from outdoors or the dock
PORTAL = GROUND + 128   # a lock's portal: its leaf is one tile high on both faces
BARRACKS_HALL_CEIL = 256
BARRACKS_CEIL = 128
MESS_CEIL = 160
DORM_CEIL = GROUND + 128  # exactly one locker high
WORKSHOP_CEIL = 320
STORE_CEIL = 256
TUNNEL_HEIGHT = 128
RAIL_TUNNEL_CEIL = 128
BAY_CEIL = 320
REACTOR_CEIL = 384
CRANE_CAB_CEIL = CRANE + 128
CLOSET_HEIGHT = 128
NICHE_DEPTH = 16
POSTER_HEIGHT = 256
MURAL_SILL = 32
SECRET_HEIGHT = 128

# --- Light ---------------------------------------------------------------------
# The polar night (November at 69 N: no sun). 192 only on the three locks,
# the three keys and the exit (MAP02 v1's rule).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_OUTDOORS = 112
LIGHT_PEN = 128
LIGHT_SUB = 128
LIGHT_BARRACKS = 144
LIGHT_WORKSHOP = 144
LIGHT_TUNNEL = 112
LIGHT_REACTOR = 112
LIGHT_BAY = 128
LIGHT_CLOSET = 112
LIGHT_SHADOW = LIGHT_MIN
LIGHT_SECRET = 112
BEACON_ZONES = ("z2_red_portal", "z3_blue_portal", "z3_yellow_portal", "z4_tray", "z5_cart",
                "z8_lid", "z10_exit_niche")

BLUE = 0x90A8FF    # MAP02's pass blue
YELLOW = 0xFFD860  # MAP03's
RED = 0xFF6048     # MAP04's
BLUE_LIGHT = {"lightcolor": BLUE}
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_D1_PEN = 1           # yard -> the covered dock
TAG_D2_BARRACKS = 2      # yard -> the fleet barracks
TAG_D3_HATCH = 3         # the boat's deck -> its inside
TAG_BLUE_DOOR = 4        # north quay -> the workshops
TAG_YELLOW_DOOR = 5      # north quay -> the rock tunnel; and the tunnel's two closets
TAG_RED_GATE = 6         # yard -> the rail tunnel; and the yard's two closets
TAG_S1_PANEL = 7
TAG_S2_PANEL = 8
TAG_S3_PANEL = 9
TAG_WT_SHUTTER = 10      # SW-A: the boat's watertight door
TAG_BARRACKS_SHUTTER = 11  # SW-B: the shortcut from the reactor's passage into the barracks
TAG_TUNNEL_AMBUSH = TAG_YELLOW_DOOR
TAG_YARD_AMBUSH = TAG_RED_GATE

# --- The plan (x east, y north; design document section 4) ---------------------
# The fjord (a prop: water under a low sky), the pen's mouth and its boom.
FJORD = ((0, 0, 512, 2816), (512, 0, 1024, 256), (512, 1600, 1216, 2816))
MOUTH = (1024, 1792, 1216, 2176)
BOOM = (1216, 1792, 1248, 2176)
LAUNCH = (352, 640, 480, 1024)
WHEELHOUSE_RECT = (384, 768, 448, 896)
# The outer pier and its crane.
PIER = (512, 256, 1024, 1600)
CRANE_STAIR_X = (544, 640)
CRANE_STAIR_Y0 = 1088
CRANE_STAIR_STEPS = CRANE // STEP - 1          # 11; the deck is the 12th rise
CRANE_DECK = (544, 1440, 832, 1568)
CRANE_TOWER = (688, 1456, 832, 1568)            # solid: the crane's tower, up to the sky
S3_PANEL = (688, 1472, 704, 1552)
S3_CAB = (704, 1472, 816, 1552)
# The crane's tower, seen from the pier and the deck: corrugated sheet, not
# the pier's rock (S3's panel on its west face keeps its gate).
CRANE_TOWER_FACES = (("v", 832, 1456, 1568), ("h", 1568, 688, 832), ("h", 1456, 688, 832),
                     ("v", 688, 1456, 1472), ("v", 688, 1552, 1568))
# The pier's kerbs over the fjord, flush with the pier: SDPIER1 with its kerb
# to the water ({zone: (rect, where the water is)}). The west one is where the
# launch is moored; the corner tile is the west strip's.
PIER_KERBS = {"z1_kerb_w": ((512, 256, 576, 1088), "west"),
              "z1_kerb_s": ((576, 256, 1024, 320), "south")}
# The container yard.
YARD = (1024, 256, 2624, 1472)
YARD_FENCE = (1024, 224, 2624, 256)
YARD_TRACK = (1024, 320, 2624, 384)
CONTAINERS = ((1152, 960, 1408, 1088), (1664, 1088, 1792, 1344), (2048, 704, 2304, 832),
              (2048, 1152, 2304, 1280), (1216, 1216, 1472, 1344))
CARGO_YARD = ((2368, 1024, 2496, 1152), (1856, 768, 1984, 832), (1536, 960, 1600, 1024))
D1_PORCH_YARD = (1856, 1472, 1984, 1504)
D1_DOOR = (1856, 1504, 1984, 1536)
D1_PORCH_PEN = (1856, 1536, 1984, 1600)
D2_PORCH = (2624, 896, 2656, 1024)
D2_DOOR = (2656, 896, 2688, 1024)
D2_PORCH_IN = (2688, 896, 2720, 1024)
RED_PORTAL = (2624, 288, 2688, 416)
RED_GATE = (2688, 288, 2720, 416)
YARD_CLOSETS = {"closet_z2_e": ((2624, 1152, 2640, 1280), (2640, 1152, 2768, 1280)),
                "closet_z2_n": ((2304, 1472, 2432, 1488), (2304, 1488, 2432, 1584))}
# The fleet barracks.
BARRACKS_HALL = (2688, 832, 2944, 1088)
CORRIDOR = (2944, 896, 3584, 1024)
DORM = (2976, 1024, 3360, 1312)
BUNKS = ((3040, 1120, 3104, 1248), (3168, 1120, 3232, 1248), (3264, 1120, 3328, 1248))
MESS = (2976, 576, 3392, 896)
TABLES = ((3040, 672, 3328, 704), (3040, 768, 3328, 800))
BARRACKS_SHUTTER = (3584, 896, 3616, 1024)
# The passage from the reactor hall up into the barracks (SW-B).
PASSAGE_Y = (896, 1024)
PASSAGE_W = (3616, 3712)
PASSAGE_STEPS = (REACTOR - GROUND) // -STEP - 1    # 7; the hall is the 8th
PASSAGE_E = (3712 + PASSAGE_STEPS * STEP_RUN, 4352)  # 3936..4352
SWB_NICHE = (3632, 1024, 3696, 1040)
# The covered dock (the pen).
SOUTH_QUAY = (1280, 1600, 3200, 1792)
BASIN_RECT = (1248, 1792, 3200, 2176)
NORTH_QUAY = (1280, 2176, 3200, 2368)
BASIN_STEPS_X = ((1344, 1472), (2944, 3072))
# The quays' edges over the basin, one tile deep, flush: SDPIER1 with its
# kerb to the water, broken where the steps go down and the gangways land
# (and short of the yellow door's corner), so the quays keep touching both.
KERB_X = ((1280, 1344), (1472, 1760), (1856, 2944))
QUAY_KERBS = {"z3_kerb_s": ((1728, 1792), "north"), "z3_kerb_n": ((2176, 2240), "south")}
GALLERY_STAIR_X0 = 2208
GALLERY_STAIR_STEPS = CRANE // STEP - 1          # 11
GALLERY_Y = (1600, 1696)
GALLERY_RECT = (GALLERY_STAIR_X0 + GALLERY_STAIR_STEPS * STEP_RUN, 1600, 3200, 1696)   # 2560..3200
BLUE_PORTAL = (1664, 2368, 1792, 2432)
BLUE_DOOR = (1664, 2432, 1792, 2464)
BLUE_PORCH_IN = (1664, 2464, 1792, 2496)
YELLOW_PORTAL = (3200, 2208, 3264, 2336)
YELLOW_DOOR = (3264, 2208, 3296, 2336)
# The submarine: the hull lies in the basin, its deck at +32, its fin a
# solid block on the deck; its forward half runs into the rock (the covered
# berth), where D3 opens through the bulkhead into the boat.
HULL_Y = (1888, 2080)
DECK_RECT = (1536, 1888, 3200, 2080)
STERN_RECT = (1408, 1952, 1536, 2016)
FIN_RECT = (2304, 1936, 2496, 2032)
FIN_NUMBERS = (("h", 1936, 2336, 2464), ("h", 2032, 2336, 2464))   # «471», once on each long face
GANGWAYS = {"z4_gangway_s": (1760, 1792, 1856, 1888), "z4_gangway_n": (1760, 2080, 1856, 2176)}
ESCAPE_HATCH = (2176, 1952, 2240, 2016)          # SDRUBR2 on the hull's axis, aft of the fin
# Where the deck meets the rock of the covered berth either side of D3: the
# berth's rock face, not a wall of hull up to the roof.
BERTH_FACES = (("v", 3200, 1888, 1920), ("v", 3200, 2048, 2080))
HATCH_PORCH = (3168, 1920, 3200, 2048)
D3_DOOR = (3200, 1920, 3232, 2048)
TRUNK = (3232, 1920, 3328, 2048)
PASSAGE_AFT = (3328, 1952, 3456, 2016)
CONTROL = (3456, 1856, 3712, 2112)
PERISCOPE = (3568, 1968, 3600, 2000)            # solid: the periscope's well
SWA_NICHE = (3712, 2048, 3728, 2112)
WT_SHUTTER = (3712, 1952, 3744, 2016)
PASSAGE_FWD = (3744, 1952, 3904, 2016)
TORPEDO = (3904, 1856, 4224, 2112)
BOAT_RACKS = ((3968, 1888, 4160, 1920), (3968, 2048, 4160, 2080))
TRAY = (4096, 1952, 4160, 2016)
# The workshops and the torpedo store, behind the blue door.
WORKSHOP = (1408, 2464, 2560, 2816)
LATHES = ((1600, 2560, 1728, 2624), (1856, 2560, 1984, 2624), (2112, 2560, 2240, 2624))
GANTRY_STAIR = (1408, 1504)                      # x of the stair up the west wall
GANTRY_STAIR_Y0 = 2496
GANTRY_STAIR_STEPS = GANTRY // STEP - 1          # 7
GANTRY_RECT = (1408, GANTRY_STAIR_Y0 + GANTRY_STAIR_STEPS * STEP_RUN, 2560, 2816)   # y 2720..
STORE = (2560, 2464, 3200, 2816)
STORE_RACKS = ((2624, 2528, 3136, 2592), (2624, 2688, 3136, 2752))
CART = (2944, 2608, 3072, 2672)
# The rock tunnel down to the reactor, behind the yellow door.
TUNNEL_Y = (2208, 2336)
TUNNEL_W = (3296, 3584)
TUNNEL_STEPS = (REACTOR - GROUND) // -STEP - 1     # 7
TUNNEL_E = (3584 + TUNNEL_STEPS * STEP_RUN, 4352)   # 3808..4352
TUNNEL_CLOSETS = {"closet_z7_a": ((3968, 2336, 4096, 2352), (3968, 2352, 4096, 2480)),
                  "closet_z7_b": ((4160, 2336, 4288, 2352), (4160, 2352, 4288, 2480))}
# The reactor hall.
REACTOR_HALL = (4352, 896, 4992, 2368)
VESSEL = (4608, 1472, 4864, 1728)
LID_STAIR_X = (4512, 4608)
LID_STAIR_Y0 = 1248
LID_STAIR_STEPS = (LID - REACTOR) // STEP - 1     # 11
LANDING = (4512, LID_STAIR_Y0 + LID_STAIR_STEPS * STEP_RUN, 4608, 1728)   # y 1600..1728
# The rail tunnel east and the loading bay.
RAIL_TUNNEL = (2720, 288, 3712, 416)
RAIL_TRACK = (2752, 320, 3712, 384)   # from 32 past the gate: the gate's leaf stays one line
REFUGES = ((3072, 416, 3136, 480), (3392, 416, 3456, 480))
BAY = (3712, 64, 4480, 768)
BAY_TRACK = (3712, 320, 4288, 384)
GOODS_WAGON = (3840, 288, 4096, 416)
TANK_WAGON = (4128, 288, 4256, 416)
LOCO = (4288, 288, 4480, 416)
CAB = (4368, 304, 4464, 400)
CAB_DOOR = (4384, 400, 4448, 416)
CAB_STEP = (4384, 416, 4448, 448)
EXIT_NICHE = (4464, 320, 4480, 384)
# The cab's walls against the locomotive's body, all but the south one
# (CAB_FRONT): its back, the stubs beside its door and the exit's niche.
CAB_SIDES = (("v", 4368, 304, 400), ("h", 400, 4368, 4384), ("h", 400, 4448, 4464),
             ("v", 4384, 400, 416), ("v", 4448, 400, 416), ("v", 4464, 304, 320), ("v", 4464, 384, 400),
             ("h", 320, 4464, 4480), ("h", 384, 4464, 4480))
# The crane lattice (SDCRAN1), masked, on both faces of two-sided lines, its
# foot on the high side's floor, one tile tall; blocking, a railing: the
# outer crane's deck on the pier and the dock's crane gallery (design 7.1).
LATTICES = (("h", 1440, 640, 832), ("v", 544, 1440, 1568), ("h", 1568, 544, 688),
            ("h", 1696, 2560, 3200))
CARGO_BAY = ((3840, 512, 3968, 576), (4096, 576, 4224, 640), (4032, 128, 4160, 192), (3776, 160, 3840, 224))
BAY_FLAGS = {FLAG_REICH: (3968, 768, 4096, 784), FLAG_LEGION: (4096, 768, 4224, 784)}
# The posters (design section 7.3).
LENIN_NICHE = (2752, 1088, 2880, 1104)           # the barracks' hall, north wall
STALIN_NICHE = (1536, 1584, 1664, 1600)          # the dock's south wall, facing the boat
MESS_MURAL_NICHE = (3136, 560, 3264, 576)             # the mess's south wall, on a sill
SLOT_NICHES = {"z3_slot_w": (1408, 2368, 1536, 2384), "z3_slot_e": (1920, 2368, 2048, 2384)}
POSTERS = (
    ("z6_lenin", LENIN, "h", LENIN_NICHE[3], LENIN_NICHE[0], LENIN_NICHE[2]),
    ("z3_stalin", STALIN, "h", STALIN_NICHE[1], STALIN_NICHE[0], STALIN_NICHE[2]),
    ("z6_mural", MURAL, "h", MESS_MURAL_NICHE[1], MESS_MURAL_NICHE[0], MESS_MURAL_NICHE[2]),
    ("z3_slot_w", MARX, "h", SLOT_NICHES["z3_slot_w"][3], *SLOT_NICHES["z3_slot_w"][::2]),
    ("z3_slot_e", ENGELS, "h", SLOT_NICHES["z3_slot_e"][3], *SLOT_NICHES["z3_slot_e"][::2]),
)
POSTER_SLOTS_MARX_ENGELS = ("z3_slot_w", "z3_slot_e")   # Marx, Engels
# The secrets (design section 8).
S1_NICHE = (2624, 576, 2640, 704)     # the yard's east cliff: the one stretch set back, in shadow
S1_PANEL = (2640, 576, 2656, 704)
S1_PASSAGE = (2656, 576, 2688, 704)
S1_STORE = (2688, 480, 2880, 768)     # the 1941 air-raid shelter
S2_NICHE = (3104, 1312, 3168, 1328)   # the dormitory's lockers: one stands back, in shadow
S2_PANEL = (3104, 1328, 3168, 1344)
S2_PASSAGE = (3104, 1344, 3168, 1376)
S2_STORE = (3040, 1376, 3232, 1504)   # the political officer's office

# --- Things --------------------------------------------------------------------
PLAYER_START = (608, 832)
PLAYER_ANGLE = 0          # facing east, across the yard towards the red gate
BLUE_KEY_SPOT = (4128, 1984)     # on the torpedo room's loading tray
YELLOW_KEY_SPOT = (3008, 2640)   # on the torpedo cart, in the store
RED_KEY_SPOT = (4736, 1600)      # on the reactor's lid
KEY_ZONES = {ED_BLUE_CARD: "z4_tray", ED_YELLOW_CARD: "z5_cart", ED_RED_CARD: "z8_lid"}
LOCK_PORTALS = {LOCK_BLUE_CARD: "z3_blue_portal", LOCK_YELLOW_CARD: "z3_yellow_portal",
                LOCK_RED_CARD: "z2_red_portal"}

PROP_PREFIX = "prop_"
# Cut into the rock (D112's brief): every sector of these, roofed in concrete
# by default, wears the living rock overhead (SDROCK2). Portals, door
# sectors and the boat's inside keep their own ceilings.
ROCK_ROOFED = ("z2_d1_porch", "z2_d2_porch", "closet_z2", "s1_niche", "s1_panel", "z3_", "z4_deck",
               "z4_stern", "z4_escape_hatch", "z4_gangway", "z4_hatch_porch", "prop_z4_fin", "prop_z3_boom", "z7_", "closet_z7",
               "z8_", "z9_", "z11_")
SECRET_ZONES = ("s1_store", "s2_store", "s3_cab")
CLOSET_PREFIX = "closet_"

# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100
ED_TROOPER = 21101
ED_STORMTROOPER = 21102
ED_HOUND = 21103
ED_DOUGHBOY = 21104
ED_PANZERMENSCH = 21105
ED_PANZER_HEAVY = 21107
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
# Where each faction stands (D35: both on the map). The Legion came by sea:
# it holds the pier, the yard, the dock, the boat and the barracks it made
# its quarters. The Reich came by rail: it holds the workshops, the rock
# tunnel, the reactor and the passage. Both guard the cargo in the rail
# tunnel and the loading bay, the last fight. Stormtroopers are hybrids and
# stand anywhere; the closets are counter-attacks.
LEGION_GROUND = ("z1_", "z2_", "z3_", "z4_", "z6_")
REICH_GROUND = ("z5_", "z7_", "z8_", "z11_")
BOTH_GROUND = ("z9_", "z10_")
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # in S3 only, the crane's cab
ED_CLIP = 2007
ED_CLIP_BOX = 2048
ED_SHELLS = 2008
ED_SHELL_BOX = 2049
ED_ROCKET = 2010
ED_ROCKET_BOX = 2046
ED_CELL = 2047
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019

# Design section 9: monsters per skill (MAP05's size, a step above it).
ENEMY_TOTALS = {2: 33, 3: 50, 4: 64}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Facing: 0
# east, 90 north, 180 west, 270 south.
MONSTERS = (
    # The pier and the yard: the Legion unloading the cargo; a Doughboy over it.
    # The pier's trooper at its far north-east corner, 820 off: seen from
    # the start but past the safe distance (tests/test_safe_starts.py; at
    # 928 1344 he was 604 off).
    ("z1_pier", "trooper", 976, 1568, 270, 2),
    ("z2_yard", "trooper", 1600, 448, 180, 2),
    ("z2_yard", "trooper", 1920, 1024, 180, 2),
    ("z2_yard", "stormtrooper", 2432, 640, 180, 2),
    ("z2_yard", "doughboy", 2176, 1376, 180, 3),
    ("z2_yard", "stormtrooper", 1600, 1408, 270, 4),
    ("z2_yard", "trooper", 2240, 640, 180, 4),
    # The barracks: the Legion's quarters.
    ("z6_hall", "trooper", 2880, 960, 180, 2),
    ("z6_mess", "trooper", 3200, 736, 90, 2),
    ("z6_dorm", "stormtrooper", 3136, 1280, 270, 3),
    ("z6_corridor", "trooper", 3520, 960, 180, 4),
    # The covered dock: the Legion guards its prize, the boat.
    ("z3_kerb_s", "trooper", 2432, 1728, 90, 2),
    ("z3_south_quay", "trooper", 2944, 1760, 180, 2),
    ("z3_north_quay", "trooper", 2048, 2272, 270, 2),
    ("z3_north_quay", "stormtrooper", 2816, 2240, 270, 2),
    ("z3_gallery", "trooper", 2944, 1648, 90, 3),
    ("z4_deck", "doughboy", 2816, 1984, 180, 2),
    ("z4_deck", "trooper", 2048, 1984, 180, 4),
    # Inside the boat: close quarters.
    ("z4_control", "trooper", 3648, 1920, 180, 2),
    ("z4_control", "stormtrooper", 3520, 2064, 0, 2),
    ("z4_torpedo", "trooper", 3936, 1888, 90, 2),
    ("z4_torpedo", "stormtrooper", 4192, 2080, 180, 3),
    ("z4_control", "trooper", 3648, 2064, 180, 4),
    # The workshops and the torpedo store: the Reich, its heavy at the lathes.
    ("z5_workshop", "panzermensch", 2368, 2528, 180, 2),
    ("z5_workshop", "rifleman", 1600, 2688, 270, 2),
    ("z5_gantry", "rifleman", 2048, 2768, 270, 2),
    ("z5_store", "rifleman", 2688, 2784, 0, 2),
    ("z5_store", "hound", 3136, 2640, 180, 3),
    ("z5_gantry", "rifleman", 1664, 2768, 270, 3),
    ("z5_store", "stormtrooper", 3136, 2784, 180, 3),
    ("z5_workshop", "hound", 2432, 2752 - 64, 180, 4),
    # The yellow door's closets in the rock tunnel: the Reich comes up.
    ("closet_z7_a", "rifleman", 4000, 2416, 270, 2),
    ("closet_z7_a", "stormtrooper", 4064, 2448, 270, 4),
    ("closet_z7_b", "hound", 4224, 2400, 270, 2),
    ("closet_z7_b", "rifleman", 4256, 2456, 270, 3),
    # The reactor hall: tension; the heavies among the machinery.
    ("z8_hall", "panzermensch", 4736, 2176, 270, 2),
    ("z8_hall", "rifleman", 4448, 2112, 0, 2),
    ("z8_hall", "rifleman", 4928, 1280, 90, 2),
    ("z8_hall", "hound", 4448, 1792, 0, 2),
    ("z8_hall", "rifleman", 4928, 1664, 180, 3),
    ("z8_hall", "heavy", 4736, 1088, 90, 3),
    ("z8_hall", "hound", 4928, 1856, 180, 3),
    ("z8_hall", "stormtrooper", 4448, 1024, 90, 4),
    ("z11_passage_e", "rifleman", 4128, 960, 0, 4),
    # The red gate's closets in the yard: the Legion behind the player.
    ("closet_z2_e", "trooper", 2704, 1184, 180, 2),
    ("closet_z2_e", "stormtrooper", 2704, 1248, 180, 3),
    ("closet_z2_n", "trooper", 2336, 1536, 270, 2),
    ("closet_z2_n", "trooper", 2400, 1536, 270, 4),
    # The rail tunnel: both factions in the refuges.
    ("z9_refuge_1", "rifleman", 3104, 448, 270, 2),
    ("z9_refuge_2", "trooper", 3424, 448, 270, 3),
    ("z9_rails", "stormtrooper", 3584, 352, 180, 4),
    # The loading bay, the last fight: both factions guard the train.
    ("z10_bay", "panzermensch", 4352, 640, 180, 2),
    ("z10_bay", "trooper", 3904, 672, 270, 2),
    ("z10_bay", "rifleman", 4160, 224, 180, 2),
    ("z10_bay", "doughboy", 4032, 480, 180, 2),
    ("z10_bay", "stormtrooper", 4288, 512, 180, 2),
    ("z10_bay", "trooper", 3840, 128, 90, 2),
    ("z10_bay", "heavy", 4352, 160, 90, 3),
    ("z10_bay", "rifleman", 4416, 704, 180, 3),
    ("z10_bay", "trooper", 3968, 224, 90, 3),
    ("z10_bay", "hound", 4224, 704, 180, 3),
    ("z10_bay", "doughboy", 3904, 480, 0, 4),
    ("z10_bay", "stormtrooper", 4416, 96, 180, 4),
    ("z10_bay", "rifleman", 4224, 96, 90, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest
# skill tier it appears on). Weapons are on every skill.
ITEMS = (
    # The weapons, on the route, each before the fight it is for.
    ("z1_pier", ED_IZH, 736, 832, 4),
    ("z6_hall", ED_PPSH, 2752, 960, 4),
    ("z3_gallery", ED_RPG7, 3136, 1648, 4),
    ("z5_store", ED_ROKS3, 2752, 2640, 4),
    # Shell boxes (20).
    ("z2_yard", ED_SHELL_BOX, 1152, 1408, 4),
    ("z6_mess", ED_SHELL_BOX, 3328, 640, 4),
    ("z3_north_quay", ED_SHELL_BOX, 1344, 2304, 4),
    ("z5_gantry", ED_SHELL_BOX, 2496, 2768, 4),
    ("z8_hall", ED_SHELL_BOX, 4416, 1472, 4),
    ("z10_bay", ED_SHELL_BOX, 3776, 704, 4),
    # Shells (4).
    ("z1_pier", ED_SHELLS, 800, 896, 4),
    ("z2_yard", ED_SHELLS, 1536, 832, 4),
    ("z3_south_quay", ED_SHELLS, 2048, 1696, 4),
    ("z4_control", ED_SHELLS, 3520, 1920, 4),
    ("z5_workshop", ED_SHELLS, 1792, 2496, 4),
    ("z7_tunnel_w", ED_SHELLS, 3456, 2272, 4),
    ("z9_rails", ED_SHELLS, 3264, 352, 4),
    ("z1_pier", ED_SHELLS, 864, 896, 3),
    ("z6_dorm", ED_SHELLS, 3296, 1088, 3),
    ("z3_north_quay", ED_SHELLS, 2560, 2304, 3),
    ("z8_hall", ED_SHELLS, 4416, 1600, 3),
    ("z10_bay", ED_SHELLS, 3776, 576, 3),
    ("z2_yard", ED_SHELLS, 1600, 832, 2),
    ("z5_workshop", ED_SHELLS, 1856, 2496, 2),
    ("z10_bay", ED_SHELLS, 3840, 704, 2),
    # Boxes of rounds (50).
    ("z6_corridor", ED_CLIP_BOX, 3456, 960, 4),
    ("z3_south_quay", ED_CLIP_BOX, 1984, 1696, 4),
    ("z8_hall", ED_CLIP_BOX, 4416, 1344, 4),
    # Clips (10).
    ("z1_pier", ED_CLIP, 672, 704, 4),
    ("z2_yard", ED_CLIP, 1408, 448, 4),
    ("z4_trunk", ED_CLIP, 3264, 1984, 4),
    ("z9_rails", ED_CLIP, 2976, 352, 4),
    ("z1_pier", ED_CLIP, 736, 704, 3),
    ("z6_hall", ED_CLIP, 2752, 1024, 3),
    ("z2_yard", ED_CLIP, 1472, 448, 2),
    # PG-7V: a box with the RPG-7, rounds for the heavies.
    ("z3_gallery", ED_ROCKET_BOX, 3072, 1648, 4),
    ("z8_landing", ED_ROCKET_BOX, 4560, 1664, 4),
    ("z10_bay", ED_ROCKET, 3776, 640, 4),
    ("z9_refuge_1", ED_ROCKET, 3104, 464, 4),
    ("z5_workshop", ED_ROCKET, 1536, 2752 - 64, 4),
    ("z10_bay", ED_ROCKET, 3776, 448, 3),
    # Fuel for the ROKS-3.
    ("z5_store", ED_CELL, 2816, 2640, 4),
    ("z8_hall", ED_CELL, 4416, 1920, 4),
    ("z9_rails", ED_CELL, 3328, 352, 4),
    # Stimpacks.
    ("z1_pier", ED_STIMPACK, 576, 1024, 4),
    ("z6_mess", ED_STIMPACK, 3328, 832, 4),
    ("z3_south_quay", ED_STIMPACK, 1344, 1696, 4),
    ("z4_passage_fwd", ED_STIMPACK, 3824, 1984, 4),
    ("z5_workshop", ED_STIMPACK, 2496, 2496, 4),
    ("z8_hall", ED_STIMPACK, 4928, 1472, 4),
    ("z10_bay", ED_STIMPACK, 3776, 512, 4),
    ("z2_yard", ED_STIMPACK, 2496, 512, 3),
    ("z3_north_quay", ED_STIMPACK, 3072, 2304, 3),
    ("z8_hall", ED_STIMPACK, 4928, 1984, 3),
    ("z6_dorm", ED_STIMPACK, 3040, 1088, 2),
    ("z9_rails", ED_STIMPACK, 3200, 352, 2),
    # Medikits.
    ("z6_dorm", ED_MEDIKIT, 3296, 1280, 4),
    ("z4_control", ED_MEDIKIT, 3520, 1888, 4),
    ("z5_store", ED_MEDIKIT, 2688, 2784, 4),
    ("z8_hall", ED_MEDIKIT, 4416, 1088, 4),
    ("z11_passage_w", ED_MEDIKIT, 3664, 960, 4),
    ("z10_bay", ED_MEDIKIT, 3776, 256, 4),
    ("z3_south_quay", ED_MEDIKIT, 1408, 1632, 3),
    ("z10_bay", ED_MEDIKIT, 3744, 128, 3),
    # Armour: the flak vest in the barracks (round 0), the heavy vest in the
    # passage (round 3, before the yard's closets and the bay); plates.
    ("z6_dorm", ED_GREEN_ARMOR, 3328, 1088, 4),
    ("z11_passage_w", ED_BLUE_ARMOR, 3664, 992, 4),
    ("z1_crane_deck", ED_ARMOR_BONUS, 576, 1472, 4),
    ("z1_crane_deck", ED_ARMOR_BONUS, 640, 1472, 4),
    ("z3_gallery", ED_ARMOR_BONUS, 2624, 1648, 4),
    ("z3_gallery", ED_ARMOR_BONUS, 2688, 1648, 4),
    ("z4_deck", ED_ARMOR_BONUS, 1600, 1984, 4),
    ("z5_gantry", ED_ARMOR_BONUS, 1472, 2768, 4),
    ("z8_landing", ED_ARMOR_BONUS, 4560, 1696, 3),
    # Health bonuses: one in each nook.
    ("z4_hatch_porch", ED_HEALTH_BONUS, 3184, 1984, 4),
    ("z4_passage_aft", ED_HEALTH_BONUS, 3392, 1984, 4),
    ("z6_corridor", ED_HEALTH_BONUS, 3008, 960, 4),
    ("z7_tunnel_w", ED_HEALTH_BONUS, 3328, 2272, 4),
    ("z9_refuge_2", ED_HEALTH_BONUS, 3424, 464, 4),
    ("z2_d1_porch", ED_HEALTH_BONUS, 1920, 1488, 4),
    ("z5_gantry", ED_HEALTH_BONUS, 2432, 2768, 4),
    ("z1_crane_deck", ED_HEALTH_BONUS, 608, 1536, 4),
)

# The secrets' rewards, on every skill (MAP01's rule).
SECRET_ITEMS = (
    # S1, the 1941 shelter in the yard's cliff: shells and the flak vest.
    ("s1_store", ED_GREEN_ARMOR, 2784, 640, 4),
    ("s1_store", ED_SHELL_BOX, 2720, 544, 4),
    ("s1_store", ED_STIMPACK, 2848, 704, 4),
    # S2, the political officer's office behind the lockers: rockets, health.
    ("s2_store", ED_ROCKET_BOX, 3072, 1440, 4),
    ("s2_store", ED_MEDIKIT, 3200, 1440, 4),
    ("s2_store", ED_CLIP_BOX, 3136, 1472, 4),
    # S3, the crane's cab: the Hand Katyusha for the bay, fuel for a second volley.
    ("s3_cab", ED_HAND_KATYUSHA, 768, 1512, 4),
    ("s3_cab", ED_CELL, 736, 1488, 4),
    ("s3_cab", ED_CELL, 800, 1536, 4),
)


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0), on both faces.
    MAP02's to MAP05's helper, repeated so each map stays one file."""
    return LineStyle(
        special=SPECIAL_DOOR_LOCKED_RAISE,
        args=(tag, DOOR_SPEED_SLOW, 0, lock, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,
    )


def secret_panel_style(tag: int, panel_sector: int, texture: str) -> LineStyle:
    """A push panel that opens for good, one-sided on the automap."""
    style = door_open_style(tag, panel_sector, texture=texture)
    return replace(style, flags=style.flags + ("secret",))


BLOCKING = LineStyle(flags=("blocking",))
# A lattice railing: impassable, lower-unpegged so the masked middle texture
# stands on the higher floor (MAP05's BOARD_EDGE).
LATTICE_EDGE = LineStyle(flags=("blocking",), peg_bottom=True)


def drawn_parts(tm: TextMap, ld, side: int, other: int | None) -> list[tuple[str, int]]:
    """The parts of sidedef `side` the engine draws, each with the height
    Doom pegs its texture to (MAP05's and MAP07's helper, repeated so each
    map stays one file): a one-sided wall to its floor (lower-unpegged) or
    ceiling; a lower texture to the higher floor (or, lower-unpegged, to its
    own ceiling); an upper texture to the lower ceiling (or, upper-unpegged,
    to its own). Between two skies, nothing."""
    flags = set(ld.flags)
    s = tm.sectors[tm.sidedefs[side].sector]
    if other is None:
        return [("texturemiddle", s.heightfloor if "dontpegbottom" in flags else s.heightceiling)]
    o = tm.sectors[tm.sidedefs[other].sector]
    parts = []
    if o.heightfloor > s.heightfloor:
        parts.append(("texturebottom", s.heightceiling if "dontpegbottom" in flags else o.heightfloor))
    both_sky = s.textureceiling == SKY and o.textureceiling == SKY
    if o.heightceiling < s.heightceiling and not both_sky:
        parts.append(("texturetop", s.heightceiling if "dontpegtop" in flags else o.heightceiling))
    return parts


def world_column(tm: TextMap, ld, side: int) -> int:
    """The offset that starts this side's texture where the map's grid would
    have it. Doom runs a front side from v1 to v2, a back side from v2 to v1."""
    a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
    if side == ld.sideback:
        a, b = b, a
    if a.y == b.y:
        return int(a.x) if b.x > a.x else -int(a.x)
    return int(a.y) if b.y > a.y else -int(a.y)


def align_to_world(tm: TextMap, bases: dict[str, int], sectors: set[int] | None = None) -> None:
    """Peg every drawn face of the lumps in `bases` to one grid (MAP05's
    helper): the texture's foot on the height `bases` names and every
    WALL_TILE above and below it (`offsety`, positive raises the texture),
    and along the wall each column where the map's origin would put it
    (`offsetx`, for the lumps in LUMP_WIDTH). `sectors` limits it to the
    faces seen from those sectors."""
    for ld in tm.linedefs:
        for side, other in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            if side is None or (sectors is not None and tm.sidedefs[side].sector not in sectors):
                continue
            sd = tm.sidedefs[side]
            for key, ref in drawn_parts(tm, ld, side, other):
                texture = getattr(sd, key)
                base = bases.get(texture)
                if base is not None:
                    sd.offsety = (base - ref) % WALL_TILE
                    if texture in LUMP_WIDTH:
                        sd.offsetx = world_column(tm, ld, side) % LUMP_WIDTH[texture]
                    break


def wet_the_banks(tm: TextMap, water: set[int], banks: set[int]) -> None:
    """SDDAM2 on every face that rises out of the water onto a quay, the
    pier or a step: the lower texture of the side standing in the water
    (MAP05's and MAP07's helper)."""
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for low, high in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            ls, hs = tm.sidedefs[low].sector, tm.sidedefs[high].sector
            if ls in water and hs in banks and tm.sectors[hs].heightfloor > tm.sectors[ls].heightfloor:
                tm.sidedefs[low].texturebottom = DAM_WET


def hang_both(tm: TextMap, axis: str, coord: int, lo: int, hi: int, texture: str) -> int:
    """Hang a masked middle texture on BOTH faces of every two-sided line
    lying on the segment, each column where the map's grid puts it. GridMap
    dresses only the upper and lower parts of a two-sided line, so this is
    done on the built map. Returns how many lines it dressed."""
    dressed = 0
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        if axis == "h":
            on = a.y == b.y == coord and lo <= min(a.x, b.x) and max(a.x, b.x) <= hi
        else:
            on = a.x == b.x == coord and lo <= min(a.y, b.y) and max(a.y, b.y) <= hi
        if not on:
            continue
        for side in (ld.sidefront, ld.sideback):
            tm.sidedefs[side].texturemiddle = texture
            tm.sidedefs[side].offsetx = world_column(tm, ld, side) % LUMP_WIDTH[texture]
        dressed += 1
    if not dressed:
        raise ValueError(f"no two-sided line on {axis} {coord} {lo}..{hi}")
    return dressed


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1.1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=ROCK)
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

    def rails(room: str, name: str, rect) -> None:
        """A track strip along x: SDTRAK1 runs its rails along the image's y."""
        like(room, name, [rect], flat=TRACK, extra={**tm.sectors[plan[room]].extra, "rotationfloor": 90.0})

    def prop(name: str, floor: int, ceil: int, rect, *, light: int, wall: str,
             flat: str = FLOOR_PLATE, ceiling: str = SKY) -> int:
        return zone(f"{PROP_PREFIX}{name}", floor, ceil, [rect], light=light, flat=flat,
                    ceiling=ceiling, wall=wall)

    def closet(name: str, door_rect, room_rect, tag: int, floor: int, *, leaf: str) -> int:
        """A monster closet: a panel that opens for good with the lock that
        owns `tag`, wearing the wall it is cut into; a dead end."""
        door_index = zone(f"{name}_door", floor, floor, [door_rect], tag, light=LIGHT_CLOSET, wall=leaf)
        zone(name, floor, floor + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

    def stair(prefix: str, rects_floors, *, ceil_above: int | None, ceil: int | None = None,
              light: int, flat: str, wall: str, ceiling: str = CEIL_CONCRETE) -> None:
        for n, (rect, f) in enumerate(rects_floors, start=1):
            c = ceil if ceil is not None else f + ceil_above
            zone(f"{prefix}_{n}", f, c, [rect], light=light, flat=flat, ceiling=ceiling, wall=wall)

    # ======================================================================
    # The fjord, the pen's mouth, the patrol launch
    # ======================================================================
    zone(f"{PROP_PREFIX}z1_fjord", BASIN, FJORD_SKY, FJORD, light=LIGHT_OUTDOORS, flat=WATER,
         ceiling=SKY, wall=ROCK)
    prop("z3_mouth", BASIN, SKY_CEIL, MOUTH, light=LIGHT_OUTDOORS, wall=ROCK, flat=WATER)
    prop("z3_boom", BASIN + 32, PEN_ROOF, BOOM, light=LIGHT_PEN, wall=STEEL, ceiling=CEIL_CONCRETE)
    prop("z1_launch", LAUNCH_DECK, LAUNCH_SKY, LAUNCH, light=LIGHT_OUTDOORS, wall=ARMOUR)
    prop("z1_wheelhouse", WHEELHOUSE, LAUNCH_SKY, WHEELHOUSE_RECT, light=LIGHT_OUTDOORS, wall=ARMOUR)

    # ======================================================================
    # The outer pier and its crane
    # ======================================================================
    zone("z1_pier", GROUND, SKY_CEIL, [PIER], light=LIGHT_OUTDOORS, ceiling=SKY, wall=ROCK)
    for name, (rect, water) in PIER_KERBS.items():
        like("z1_pier", name, [rect], flat=PIER_EDGE, extra={"rotationfloor": KERB_ROTATION[water]})
    sx1, sx2 = CRANE_STAIR_X
    stair("z1_crane_stair",
          [((sx1, CRANE_STAIR_Y0 + STEP_RUN * (n - 1), sx2, CRANE_STAIR_Y0 + STEP_RUN * n), STEP * n)
           for n in range(1, CRANE_STAIR_STEPS + 1)],
          ceil_above=None, ceil=SKY_CEIL, light=LIGHT_OUTDOORS, flat=GRATING, wall=STEEL, ceiling=SKY)
    zone("z1_crane_deck", CRANE, SKY_CEIL, [CRANE_DECK], light=LIGHT_OUTDOORS, flat=GRATING,
         ceiling=SKY, wall=STEEL)
    g.carve(*CRANE_TOWER)
    s3_panel = zone("s3_panel", CRANE, CRANE, [S3_PANEL], TAG_S3_PANEL, light=LIGHT_SECRET, wall=RUST)
    zone("s3_cab", CRANE, CRANE_CAB_CEIL, [S3_CAB], light=LIGHT_SECRET, flat=FLOOR_PLATE,
         ceiling=CEIL_PANEL, wall=RUST, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # The container yard: the red gate in the east cliff, D1 and D2
    # ======================================================================
    zone("z2_yard", GROUND, SKY_CEIL, [YARD], light=LIGHT_OUTDOORS, ceiling=SKY, wall=ROCK)
    rails("z2_yard", "z2_rails", YARD_TRACK)
    prop("z2_fence", FENCE, FENCE_SKY, YARD_FENCE, light=LIGHT_OUTDOORS, wall=RUST)
    for n, rect in enumerate(CONTAINERS, start=1):
        prop(f"z2_container_{n}", CONTAINER, SKY_CEIL, rect, light=LIGHT_OUTDOORS, wall=CONTAINER_SIDE)
    for n, rect in enumerate(CARGO_YARD, start=1):
        prop(f"z2_cargo_{n}", CARGO, SKY_CEIL, rect, light=LIGHT_OUTDOORS, wall=CRATE, flat=CRATE_TOP)
    zone("z2_d1_porch", GROUND, PORCH, [D1_PORCH_YARD], light=LIGHT_OUTDOORS, wall=ROCK)
    d1 = door("d1_pen", GROUND, TAG_D1_PEN, D1_DOOR, light=LIGHT_PEN)
    zone("z2_d2_porch", GROUND, PORCH, [D2_PORCH], light=LIGHT_OUTDOORS, wall=ROCK)
    d2 = door("d2_barracks", GROUND, TAG_D2_BARRACKS, D2_DOOR, light=LIGHT_BARRACKS)
    zone("z2_red_portal", GROUND, PORTAL, [RED_PORTAL], light=LIGHT_BEACON, ceiling=CEIL_PANEL,
         wall=ROCK, extra=RED_LIGHT)
    red_gate = door("z13_red_gate", GROUND, TAG_RED_GATE, RED_GATE, light=LIGHT_TUNNEL)
    for name, (door_rect, room_rect) in YARD_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_YARD_AMBUSH, GROUND, leaf=ROCK)
    # S1: the one stretch of the east cliff that stands back, in shadow.
    zone("s1_niche", GROUND, PORCH, [S1_NICHE], light=LIGHT_SHADOW, wall=ROCK)
    s1_panel = zone("s1_panel", GROUND, GROUND, [S1_PANEL], TAG_S1_PANEL, light=LIGHT_SHADOW, wall=ROCK)
    zone("s1_passage", GROUND, SECRET_HEIGHT, [S1_PASSAGE], light=LIGHT_SECRET, wall=CONCRETE)
    zone("s1_store", GROUND, SECRET_HEIGHT, [S1_STORE], light=LIGHT_SECRET, wall=CONCRETE,
         special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # The fleet barracks
    # ======================================================================
    zone("z6_hall", GROUND, BARRACKS_HALL_CEIL, [BARRACKS_HALL], light=LIGHT_BARRACKS, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=CONCRETE_STRIPE)
    like("z6_hall", "z6_lenin_niche", [LENIN_NICHE], ceil=GROUND + POSTER_HEIGHT)
    like("z6_hall", "z6_d2_porch", [D2_PORCH_IN], ceil=PORCH)
    zone("z6_corridor", GROUND, BARRACKS_CEIL, [CORRIDOR], light=LIGHT_BARRACKS, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=CONCRETE)
    zone("z6_dorm", GROUND, DORM_CEIL, [DORM], light=LIGHT_BARRACKS, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=CONCRETE)
    for n, rect in enumerate(BUNKS, start=1):
        like("z6_dorm", f"{PROP_PREFIX}z6_bunk_{n}", [rect], floor=GROUND + BUNK, flat=FLOOR_PLATE, wall=STEEL)
    zone("z6_mess", GROUND, MESS_CEIL, [MESS], light=LIGHT_BARRACKS, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=CONCRETE_STRIPE)
    for n, rect in enumerate(TABLES, start=1):
        like("z6_mess", f"{PROP_PREFIX}z6_table_{n}", [rect], floor=GROUND + TABLE, flat=FLOOR_PLATE,
             wall=STEEL)
    like("z6_mess", f"{PROP_PREFIX}z6_mural_niche", [MESS_MURAL_NICHE], floor=GROUND + MURAL_SILL)
    barracks_shutter = door("shutter_barracks", GROUND, TAG_BARRACKS_SHUTTER, BARRACKS_SHUTTER,
                            light=LIGHT_BARRACKS)
    # S2: one locker of the dormitory's row stands back, in shadow.
    zone("s2_niche", GROUND, DORM_CEIL, [S2_NICHE], light=LIGHT_SHADOW, wall=LOCKER)
    s2_panel = zone("s2_panel", GROUND, GROUND, [S2_PANEL], TAG_S2_PANEL, light=LIGHT_SHADOW, wall=LOCKER)
    zone("s2_passage", GROUND, SECRET_HEIGHT, [S2_PASSAGE], light=LIGHT_SECRET, wall=CONCRETE)
    zone("s2_store", GROUND, SECRET_HEIGHT, [S2_STORE], light=LIGHT_SECRET, flat=FLOOR_TILE,
         wall=CONCRETE, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # The passage from the reactor hall up into the barracks (SW-B)
    # ======================================================================
    py1, py2 = PASSAGE_Y
    zone("z11_passage_w", GROUND, GROUND + TUNNEL_HEIGHT, [(PASSAGE_W[0], py1, PASSAGE_W[1], py2)],
         light=LIGHT_TUNNEL, wall=ROCK)
    stair("z11_passage_step",
          [((PASSAGE_W[1] + STEP_RUN * (n - 1), py1, PASSAGE_W[1] + STEP_RUN * n, py2), GROUND - STEP * n)
           for n in range(1, PASSAGE_STEPS + 1)],
          ceil_above=TUNNEL_HEIGHT, light=LIGHT_TUNNEL, flat=FLOOR_CONCRETE, wall=ROCK)
    zone("z11_passage_e", REACTOR, REACTOR + TUNNEL_HEIGHT, [(PASSAGE_E[0], py1, PASSAGE_E[1], py2)],
         light=LIGHT_TUNNEL, wall=ROCK)
    zone("z11_swb_niche", GROUND, GROUND + SWITCH_HEIGHT, [SWB_NICHE], light=LIGHT_TUNNEL, wall=STEEL)

    # ======================================================================
    # The covered dock: quays, basin, the crane gallery, the three doors
    # ======================================================================
    zone("z3_d1_porch", GROUND, PORCH, [D1_PORCH_PEN], light=LIGHT_PEN, wall=ROCK)
    zone("z3_south_quay", GROUND, PEN_ROOF, [SOUTH_QUAY], light=LIGHT_PEN, ceiling=CEIL_CONCRETE, wall=ROCK)
    zone("z3_basin", BASIN, PEN_ROOF, [BASIN_RECT], light=LIGHT_PEN, flat=WATER, wall=ROCK)
    zone("z3_north_quay", GROUND, PEN_ROOF, [NORTH_QUAY], light=LIGHT_PEN, ceiling=CEIL_CONCRETE, wall=ROCK)
    for name, ((ky1, ky2), water) in QUAY_KERBS.items():
        quay = "z3_south_quay" if water == "north" else "z3_north_quay"
        like(quay, name, [(kx1, ky1, kx2, ky2) for kx1, kx2 in KERB_X], flat=PIER_EDGE,
             extra={"rotationfloor": KERB_ROTATION[water]})
    for k, (bx1, bx2) in enumerate(BASIN_STEPS_X, start=1):
        for n in range(1, 4):      # three steps up out of the water on each quay
            f = BASIN + STEP * n
            south_y = BASIN_RECT[1] + STEP_RUN * (3 - n)
            like("z3_basin", f"z3_steps_s{k}_{n}", [(bx1, south_y, bx2, south_y + STEP_RUN)], floor=f,
                 flat=FLOOR_CONCRETE)
            north_y = BASIN_RECT[3] - STEP_RUN * (4 - n)
            like("z3_basin", f"z3_steps_n{k}_{n}", [(bx1, north_y, bx2, north_y + STEP_RUN)], floor=f,
                 flat=FLOOR_CONCRETE)
    gy1, gy2 = GALLERY_Y
    stair("z3_gallery_stair",
          [((GALLERY_STAIR_X0 + STEP_RUN * (n - 1), gy1, GALLERY_STAIR_X0 + STEP_RUN * n, gy2), STEP * n)
           for n in range(1, GALLERY_STAIR_STEPS + 1)],
          ceil_above=None, ceil=PEN_ROOF, light=LIGHT_PEN, flat=GRATING, wall=STEEL)
    zone("z3_gallery", CRANE, PEN_ROOF, [GALLERY_RECT], light=LIGHT_PEN, flat=GRATING, wall=STEEL)
    like("z3_south_quay", "z3_stalin_niche", [STALIN_NICHE], ceil=GROUND + POSTER_HEIGHT)
    for name, rect in SLOT_NICHES.items():
        like("z3_north_quay", f"{name}_niche", [rect], ceil=GROUND + POSTER_HEIGHT)
    zone("z3_blue_portal", GROUND, PORTAL, [BLUE_PORTAL], light=LIGHT_BEACON, ceiling=CEIL_PANEL,
         wall=ROCK, extra=BLUE_LIGHT)
    blue_door = door("z13_blue_door", GROUND, TAG_BLUE_DOOR, BLUE_DOOR, light=LIGHT_WORKSHOP)
    zone("z3_yellow_portal", GROUND, PORTAL, [YELLOW_PORTAL], light=LIGHT_BEACON, ceiling=CEIL_PANEL,
         wall=ROCK, extra=YELLOW_LIGHT)
    yellow_door = door("z13_yellow_door", GROUND, TAG_YELLOW_DOOR, YELLOW_DOOR, light=LIGHT_TUNNEL)

    # ======================================================================
    # The submarine: gangways, deck, fin; D3 into the covered berth
    # ======================================================================
    for name, rect in GANGWAYS.items():
        zone(name, GANGWAY, PEN_ROOF, [rect], light=LIGHT_PEN, flat=GRATING, wall=STEEL)
    zone("z4_deck", DECK, PEN_ROOF, [DECK_RECT], light=LIGHT_PEN, flat=DECK_RUBBER, wall=HULL)
    like("z4_deck", "z4_escape_hatch", [ESCAPE_HATCH], flat=DECK_HATCH,
         extra={"ypanningfloor": float(HATCH_PANNING)})
    zone("z4_stern", STERN, PEN_ROOF, [STERN_RECT], light=LIGHT_PEN, flat=DECK_RUBBER, wall=HULL)
    prop("z4_fin", FIN, PEN_ROOF, FIN_RECT, light=LIGHT_PEN, wall=HULL, flat=DECK_RUBBER, ceiling=CEIL_CONCRETE)
    zone("z4_hatch_porch", DECK, INTERIOR, [HATCH_PORCH], light=LIGHT_PEN, flat=DECK_RUBBER, wall=STEEL)
    d3 = door("d3_hatch", DECK, TAG_D3_HATCH, D3_DOOR, light=LIGHT_SUB)
    inside = dict(light=LIGHT_SUB, flat=FLOOR_PLATE, ceiling=CEIL_PANEL, wall=STEEL)
    zone("z4_trunk", DECK, INTERIOR, [TRUNK], **inside)
    zone("z4_passage_aft", DECK, INTERIOR, [PASSAGE_AFT], **inside)
    zone("z4_control", DECK, INTERIOR, [CONTROL], **inside)
    g.carve(*PERISCOPE)
    zone("z4_swa_niche", DECK, DECK + SWITCH_HEIGHT, [SWA_NICHE], **inside)
    wt_shutter = door("shutter_wt", DECK, TAG_WT_SHUTTER, WT_SHUTTER, light=LIGHT_SUB)
    zone("z4_passage_fwd", DECK, INTERIOR, [PASSAGE_FWD], **inside)
    zone("z4_torpedo", DECK, INTERIOR, [TORPEDO], **inside)
    for n, rect in enumerate(BOAT_RACKS, start=1):
        like("z4_torpedo", f"{PROP_PREFIX}z4_rack_{n}", [rect], floor=BOAT_RACK)
    zone("z4_tray", DECK + PAD, INTERIOR, [TRAY], light=LIGHT_BEACON, flat=FLOOR_PLATE, ceiling=CEIL_PANEL,
         wall=STEEL, extra=BLUE_LIGHT)

    # ======================================================================
    # The workshops and the torpedo store, behind the blue door
    # ======================================================================
    zone("z5_workshop", GROUND, WORKSHOP_CEIL, [WORKSHOP], light=LIGHT_WORKSHOP, flat=FLOOR_CONCRETE,
         ceiling=CEIL_PANEL, wall=BRICK)
    like("z5_workshop", "z5_blue_porch", [BLUE_PORCH_IN], ceil=PORCH)
    for n, rect in enumerate(LATHES, start=1):
        like("z5_workshop", f"{PROP_PREFIX}z5_lathe_{n}", [rect], floor=GROUND + LATHE, flat=FLOOR_PLATE,
             wall=STEEL)
    gx1, gx2 = GANTRY_STAIR
    stair("z5_gantry_stair",
          [((gx1, GANTRY_STAIR_Y0 + STEP_RUN * (n - 1), gx2, GANTRY_STAIR_Y0 + STEP_RUN * n), STEP * n)
           for n in range(1, GANTRY_STAIR_STEPS + 1)],
          ceil_above=None, ceil=WORKSHOP_CEIL, light=LIGHT_WORKSHOP, flat=GRATING, wall=STEEL,
          ceiling=CEIL_PANEL)
    zone("z5_gantry", GANTRY, WORKSHOP_CEIL, [GANTRY_RECT], light=LIGHT_WORKSHOP, flat=GRATING,
         ceiling=CEIL_PANEL, wall=STEEL)
    zone("z5_store", GROUND, STORE_CEIL, [STORE], light=LIGHT_WORKSHOP, flat=FLOOR_CONCRETE,
         ceiling=CEIL_PANEL, wall=CONCRETE)
    for n, rect in enumerate(STORE_RACKS, start=1):
        like("z5_store", f"{PROP_PREFIX}z5_rack_{n}", [rect], floor=GROUND + RACK, flat=FLOOR_PLATE, wall=STEEL)
    zone("z5_cart", GROUND + PAD, STORE_CEIL, [CART], light=LIGHT_BEACON, flat=FLOOR_PLATE,
         ceiling=CEIL_PANEL, wall=STEEL, extra=YELLOW_LIGHT)

    # ======================================================================
    # The rock tunnel down to the reactor, its two closets
    # ======================================================================
    ty1, ty2 = TUNNEL_Y
    zone("z7_tunnel_w", GROUND, GROUND + TUNNEL_HEIGHT, [(TUNNEL_W[0], ty1, TUNNEL_W[1], ty2)],
         light=LIGHT_TUNNEL, wall=ROCK)
    stair("z7_step",
          [((TUNNEL_W[1] + STEP_RUN * (n - 1), ty1, TUNNEL_W[1] + STEP_RUN * n, ty2), GROUND - STEP * n)
           for n in range(1, TUNNEL_STEPS + 1)],
          ceil_above=TUNNEL_HEIGHT, light=LIGHT_TUNNEL, flat=FLOOR_CONCRETE, wall=ROCK)
    zone("z7_tunnel_e", REACTOR, REACTOR + TUNNEL_HEIGHT, [(TUNNEL_E[0], ty1, TUNNEL_E[1], ty2)],
         light=LIGHT_TUNNEL, wall=ROCK)
    for name, (door_rect, room_rect) in TUNNEL_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_TUNNEL_AMBUSH, REACTOR, leaf=ROCK)

    # ======================================================================
    # The reactor hall: the lid, the red key
    # ======================================================================
    zone("z8_hall", REACTOR, REACTOR_CEIL, [REACTOR_HALL], light=LIGHT_REACTOR, wall=ROCK)
    lx1, lx2 = LID_STAIR_X
    stair("z8_lid_stair",
          [((lx1, LID_STAIR_Y0 + STEP_RUN * (n - 1), lx2, LID_STAIR_Y0 + STEP_RUN * n), REACTOR + STEP * n)
           for n in range(1, LID_STAIR_STEPS + 1)],
          ceil_above=None, ceil=REACTOR_CEIL, light=LIGHT_REACTOR, flat=GRATING, wall=STEEL)
    zone("z8_landing", LID, REACTOR_CEIL, [LANDING], light=LIGHT_REACTOR, flat=GRATING, wall=STEEL)
    zone("z8_lid", LID, REACTOR_CEIL, [VESSEL], light=LIGHT_BEACON, flat=FLOOR_PLATE, wall=STEEL,
         extra=RED_LIGHT)

    # ======================================================================
    # The rail tunnel and the loading bay: the goods train, the exit
    # ======================================================================
    zone("z9_tunnel", GROUND, RAIL_TUNNEL_CEIL, [RAIL_TUNNEL], light=LIGHT_TUNNEL, flat=BALLAST, wall=ROCK)
    rails("z9_tunnel", "z9_rails", RAIL_TRACK)
    for n, rect in enumerate(REFUGES, start=1):
        like("z9_tunnel", f"z9_refuge_{n}", [rect], ceil=GROUND + TUNNEL_HEIGHT)
    zone("z10_bay", GROUND, BAY_CEIL, [BAY], light=LIGHT_BAY, flat=BALLAST, ceiling=CEIL_CONCRETE,
         wall=BRICK_RAIL)
    rails("z10_bay", "z10_rails", BAY_TRACK)
    prop("z10_wagon", WAGON_TOP, BAY_CEIL, GOODS_WAGON, light=LIGHT_BAY, wall=WAGON, ceiling=CEIL_CONCRETE)
    prop("z10_tank", WAGON_TOP, BAY_CEIL, TANK_WAGON, light=LIGHT_BAY, wall=TANK, ceiling=CEIL_CONCRETE)
    prop("z10_loco", INTERIOR, BAY_CEIL, LOCO, light=LIGHT_BAY, wall=ARMOUR, ceiling=CEIL_CONCRETE)
    for n, rect in enumerate(CARGO_BAY, start=1):
        prop(f"z10_cargo_{n}", CARGO, BAY_CEIL, rect, light=LIGHT_BAY, wall=CRATE, flat=CRATE_TOP,
             ceiling=CEIL_CONCRETE)
    for texture, rect in BAY_FLAGS.items():
        like("z10_bay", f"z10_flag_{texture.lower()}", [rect], ceil=GROUND + TILE, flat=FLOOR_CONCRETE)
    zone("z10_cab_step", GROUND + STEP, BAY_CEIL, [CAB_STEP], light=LIGHT_BAY, flat=GRATING, wall=STEEL)
    zone("z10_cab", DECK, INTERIOR, [CAB, CAB_DOOR], light=LIGHT_BAY, flat=FLOOR_PLATE,
         ceiling=CEIL_PANEL, wall=ARMOUR)
    zone("z10_exit_niche", DECK, DECK + SWITCH_HEIGHT, [EXIT_NICHE], light=LIGHT_BEACON, wall=STEEL)

    # ======================================================================
    # Line styles. The FIRST rule registered on a segment wins.
    # ======================================================================
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    for texture, (x1, _y1, x2, y2) in BAY_FLAGS.items():
        g.style_h(y2, x1, x2, LineStyle(texture=texture))
    # Manual doors, both faces.
    for sector, (x1, y1, x2, y2), horizontal, leaf in ((d1, D1_DOOR, True, DOOR), (d2, D2_DOOR, False, DOOR),
                                                       (d3, D3_DOOR, False, BULKHEAD_DOOR)):
        tag = tm.sectors[sector].identifier
        if horizontal:
            for yy in (y1, y2):
                g.style_h(yy, x1, x2, door_raise_style(tag, sector, texture=leaf))
        else:
            for xx in (x1, x2):
                g.style_v(xx, y1, y2, door_raise_style(tag, sector, texture=leaf))
    # The three locks, both faces.
    for yy in (BLUE_DOOR[1], BLUE_DOOR[3]):
        g.style_h(yy, BLUE_DOOR[0], BLUE_DOOR[2],
                  locked_door_style(TAG_BLUE_DOOR, blue_door, LOCK_BLUE_CARD, texture=DOOR_BLUE))
    for xx in (YELLOW_DOOR[0], YELLOW_DOOR[2]):
        g.style_v(xx, YELLOW_DOOR[1], YELLOW_DOOR[3],
                  locked_door_style(TAG_YELLOW_DOOR, yellow_door, LOCK_YELLOW_CARD, texture=DOOR_YELLOW))
    for xx in (RED_GATE[0], RED_GATE[2]):
        g.style_v(xx, RED_GATE[1], RED_GATE[3],
                  locked_door_style(TAG_RED_GATE, red_gate, LOCK_RED_CARD, texture=DOOR_RED))
    # The watertight door: steel both sides, SW-A beside it.
    for xx in (WT_SHUTTER[0], WT_SHUTTER[2]):
        g.style_v(xx, WT_SHUTTER[1], WT_SHUTTER[3], remote_door_style(wt_shutter, texture=STEEL))
    g.style_v(SWA_NICHE[2], SWA_NICHE[1], SWA_NICHE[3],
              switch_door_open_style(TAG_WT_SHUTTER, texture=SW_A_FACE, repeatable=False))
    # The barracks' shutter: steel from the passage; from the corridor, the
    # corridor's own concrete (a shortcut found from behind).
    g.style_v(BARRACKS_SHUTTER[2], BARRACKS_SHUTTER[1], BARRACKS_SHUTTER[3],
              remote_door_style(barracks_shutter, texture=STEEL))
    g.style_v(BARRACKS_SHUTTER[0], BARRACKS_SHUTTER[1], BARRACKS_SHUTTER[3],
              remote_door_style(barracks_shutter, texture=CONCRETE))
    g.style_h(SWB_NICHE[3], SWB_NICHE[0], SWB_NICHE[2],
              switch_door_open_style(TAG_BARRACKS_SHUTTER, texture=SW_B_FACE, repeatable=False))
    # The secrets' panels.
    for xx in (S1_PANEL[0], S1_PANEL[2]):
        g.style_v(xx, S1_PANEL[1], S1_PANEL[3], secret_panel_style(TAG_S1_PANEL, s1_panel, ROCK))
    for yy in (S2_PANEL[1], S2_PANEL[3]):
        g.style_h(yy, S2_PANEL[0], S2_PANEL[2], secret_panel_style(TAG_S2_PANEL, s2_panel, LOCKER))
    for xx in (S3_PANEL[0], S3_PANEL[2]):
        g.style_v(xx, S3_PANEL[1], S3_PANEL[3], secret_panel_style(TAG_S3_PANEL, s3_panel, ROAD_GATE))
    # The fin's tactical number «471», once on each long face.
    for axis, coord, lo, hi in FIN_NUMBERS:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=HULL_NUMBER))
    # The covered berth's rock either side of D3, over the deck's bow.
    for axis, coord, lo, hi in BERTH_FACES:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=ROCK))
    # The crane's tower: corrugated sheet all round (S3's gate registered above).
    for axis, coord, lo, hi in CRANE_TOWER_FACES:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=RUST))
    # The lattice railings: impassable, their lattice hung after the build.
    for axis, coord, lo, hi in LATTICES:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LATTICE_EDGE)
    # The boat's control room: its long walls are the naval panels, one tile high.
    g.style_h(CONTROL[1], CONTROL[0], CONTROL[2], LineStyle(texture=NAVAL_PANEL))
    g.style_h(CONTROL[3], CONTROL[0], CONTROL[2], LineStyle(texture=NAVAL_PANEL))
    # The bow's torpedo tubes.
    g.style_v(TORPEDO[2], TORPEDO[1], TORPEDO[3], LineStyle(texture=TUBBING))
    # The dormitory's lockers, its north wall.
    g.style_h(DORM[3], DORM[0], DORM[2], LineStyle(texture=LOCKER))
    # The locomotive's cab: the backhead and its gauges on the south wall,
    # facing the door (on the north, to the platform); a window per tile on the rest.
    g.style_h(CAB[1], CAB[0], CAB[2], LineStyle(texture=CAB_FRONT))
    for axis, coord, lo, hi in CAB_SIDES:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=CAB_SIDE))
    # The boom across the pen's mouth: nothing crosses it, not even swimming.
    for xx in (BOOM[0], BOOM[2]):
        g.style_v(xx, BOOM[1], BOOM[3], BLOCKING)
    # The exit: the regulator at the back of its niche in the cab.
    g.style_v(EXIT_NICHE[2], EXIT_NICHE[1], EXIT_NICHE[3], exit_switch_style(texture=EXIT_FACE))

    g.build()

    # ======================================================================
    # Dressing the built map: the rock overhead, the waterline, alignment,
    # the lattices
    # ======================================================================
    for name, index in plan.items():
        sector = tm.sectors[index]
        if name.startswith(ROCK_ROOFED) and sector.textureceiling == CEIL_CONCRETE:
            sector.textureceiling = ROCK_CEIL
    water = {plan["z3_basin"], plan[f"{PROP_PREFIX}z1_fjord"], plan[f"{PROP_PREFIX}z3_mouth"]} | {
        i for n, i in plan.items() if n.startswith("z3_steps_")}
    banks = {i for n, i in plan.items() if n.startswith(("z3_steps_", "z3_kerb", "z1_kerb"))} | {
        plan["z3_south_quay"], plan["z3_north_quay"], plan["z1_pier"]}
    wet_the_banks(tm, water, banks)
    align_to_world(tm, {ROCK: GROUND, DAM_WET: BASIN})
    # The hull: from the water its flooding holes just over the waterline;
    # from the deck, the gangways and the stern its top edge on the deck, and
    # the fin one whole tile over the deck (the number too).
    align_to_world(tm, {HULL: BASIN}, sectors={plan["z3_basin"]})
    align_to_world(tm, {HULL: DECK, HULL_NUMBER: DECK},
                   sectors={plan["z4_deck"], plan["z4_escape_hatch"], plan["z4_stern"]}
                   | {plan[n] for n in GANGWAYS})
    # The cab: one tile high; on the 64/128 grid its back wall shows one
    # whole window and the backhead its middle (the cab is the tile's middle).
    align_to_world(tm, {CAB_FRONT: DECK, CAB_SIDE: DECK}, sectors={plan["z10_cab"], plan["z10_exit_niche"]})
    for axis, coord, lo, hi in LATTICES:
        hang_both(tm, axis, coord, lo, hi, CRANE_LATTICE)

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START, angle=PLAYER_ANGLE))
    for ednum, spot in ((ED_BLUE_CARD, BLUE_KEY_SPOT), (ED_YELLOW_CARD, YELLOW_KEY_SPOT),
                        (ED_RED_CARD, RED_KEY_SPOT)):
        tm.add_thing(Thing(x=spot[0], y=spot[1], type=ednum))
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
WALL_TEXTURES = ((ROCK, DAM_WET, CONCRETE, CONCRETE_STRIPE, STEEL, BRICK, BRICK_RAIL, RUST, CONTAINER_SIDE,
                  HULL, HULL_NUMBER, ARMOUR, WAGON, TANK, LOCKER, NAVAL_PANEL, CAB_FRONT, CAB_SIDE, TUBBING,
                  CRANE_LATTICE, ROAD_GATE, CRATE, FLAG_REICH, FLAG_LEGION, LENIN, STALIN, MURAL)
                 + DOOR_LEAVES + SWITCH_FACES + MARX_ENGELS)
FLAT_TEXTURES = (FLOOR_LANE, FLOOR_CONCRETE, FLOOR_TILE, FLOOR_PLATE, DECK_RUBBER, DECK_HATCH, PIER_EDGE,
                 CEIL_PANEL, CEIL_CONCRETE, ROCK_CEIL, CRATE_TOP, GRATING, WATER, TRACK, BALLAST)
# Middle textures on two-sided lines, drawn once: the masked crane lattice.
# Nothing else hangs in mid-air.
MIDDLE_TEXTURES = (CRANE_LATTICE,)
BUILTIN_FLATS = (SKY,)
# Design section 7.2, settled (D113): {lump the design proposed: the lump
# the map wears for it}. Proposed names the art-director drew are worn as
# themselves; the ones never drawn (no such lump in assets/) wear the nearest
# installed piece.
NAVAL_SET = {
    "SDROCK1": ROCK,            # drawn: the cliffs, the dock, the tunnels, the reactor hall (SDROCK2 overhead)
    "SDHULL1": HULL,            # drawn: the hull's flanks, the stern, the fin
    "SDHULL2": HULL_NUMBER,     # drawn: «471» once on each face of the fin (the red star SDARMR1 retired)
    "SDBULK1": BULKHEAD_DOOR,   # drawn as a round watertight door, not a wall: D3, the bulkhead hatch
    "SDHTCH1": BULKHEAD_DOOR,   # never drawn: D3 wears SDBULK1; SDRUBR2's flush hatch lies on the deck
    "SDTORP1": TUBBING,         # never drawn: the bow keeps SDTUBB1 (a round door there would never open)
    "SDCONT1": CONTAINER_SIDE,  # drawn: the yard's five containers
    "SDLOCO1": ARMOUR,          # never drawn: the body stays SDARMR2; inside, the cab wears SDCAB1/SDCAB2
    "SDREAC1": STEEL,           # never drawn: the vessel's jacket stays SDSTEL1
    "SDDOORB": DOOR_BLUE,       # drawn (episode 2): the blue door
}
# Still waiting, with nothing standing in: {proposed lump: what and where}.
PENDING_TEXTURES = {
    "SDPERI1": "the periscope's tube, masked: the control room's well is a solid steel column meanwhile",
    "SDNSKY1": "the polar night sky with the aurora (MAPINFO's sky, the scaffolding's call)",
}
