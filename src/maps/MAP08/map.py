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
secrets. Balance and light are later passes. Approved lumps only; the naval
pieces nobody has drawn yet wear the nearest approved lump (`NAVAL_SET`,
`PENDING_TEXTURES`).

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
# No "Naval" set exists yet (the art-director is drafting one, D112): every
# lump below is approved and packed; NAVAL_SET says which stands in for which
# naval piece, PENDING_TEXTURES what the map still waits for.
ROCK = "SDDAM1"          # mass concrete: stands in for the living Kola granite (SDROCK1, pending)
CONCRETE = "SDCONC1"     # prefab panels: the barracks' corridor, the torpedo store, the tunnel's closets
CONCRETE_STRIPE = "SDCONC2"  # the red-striped prefab: the barracks' hall and mess
STEEL = "SDSTEL1"        # green riveted plate: the boat's inside, racks, lathes, the reactor's jacket
TUNNEL = "SDTUNL1"       # board-cast concrete with cable runs: the rock tunnels
BRICK = "SDBRCK1"        # works brick: the workshops
BRICK_RAIL = "SDBRCK3"   # roundhouse brick: the loading bay
RUST = "SDRUST1"         # corrugated sheet: the containers, the yard's fence, the crane
ARMOUR = "SDARMR2"       # 64x128 armour plate: the submarine's hull and fin, the launch, the locomotive
ARMOUR_STAR = "SDARMR1"  # 128x128 the plate with the red star: once on each face of the fin
WAGON = "SDWAGN1"        # 128x128 covered goods wagon side
TANK = "SDTANK1"         # 128x128 tank wagon side
LOCKER = "SDLOCK1"       # 64x128 barracks lockers: the dormitory's north wall (and S2's panel)
CONTROL_PANEL = "SDCTRL1"  # 128x128 control board: the boat's control room, the locomotive's desk
TUBBING = "SDTUBB1"      # 128x128 cast-iron rings: the bow's torpedo tubes (SDTORP1, pending)
DOOR = "SDDOOR1"         # D1, D2, D3 and the blue door (no blue trim drawn: SDDOORB, pending)
DOOR_YELLOW = "SDDOORY"
DOOR_RED = "SDDOORR"
ROAD_GATE = "SDGATE1"    # corrugated gate: S3, the crane's cab
CRATE = "SDCRAT1"        # the cargo bound for Tunguska
FLAG_REICH = "SDFLAG1"   # both banners side by side by the train (D35)
FLAG_LEGION = "SDFLAG2"
LENIN = "SDPOSTR1"       # 128x256: the barracks' hall
STALIN = "SDPOSTR3"      # 128x256: the dock's south wall, facing the boat
MURAL = "SDPOSTR2"       # 128x128 cosmonautics mural: the mess, on a sill
# The Marx-Engels poster SDPOSTR4 is in preparation (not a lump yet). Its
# slots are built and wear a stand-in; approving it is this one line:
MARX_ENGELS: str | None = None   # -> "SDPOSTR4"
FLOOR_LANE = "SDFLR1"
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
FLOOR_PLATE = "SDFLR4"   # chequer plate: the boat's deck and inside, pads, the lid
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
DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_RED)

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
FIN_STARS = (("h", 1936, 2336, 2464), ("h", 2032, 2336, 2464))
GANGWAYS = {"z4_gangway_s": (1760, 1792, 1856, 1888), "z4_gangway_n": (1760, 2080, 1856, 2176)}
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
    ("z3_slot_w", STALIN, "h", SLOT_NICHES["z3_slot_w"][3], *SLOT_NICHES["z3_slot_w"][::2]),
    ("z3_slot_e", LENIN, "h", SLOT_NICHES["z3_slot_e"][3], *SLOT_NICHES["z3_slot_e"][::2]),
)
POSTER_SLOTS_MARX_ENGELS = ("z3_slot_w", "z3_slot_e")
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
    ("z1_pier", "trooper", 928, 1344, 270, 2),
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
    ("z3_south_quay", "trooper", 2432, 1728, 90, 2),
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
    """POSTERS with each Marx-Engels slot wearing SDPOSTR4 once it exists."""
    return tuple((name, MARX_ENGELS if MARX_ENGELS and name in POSTER_SLOTS_MARX_ENGELS else texture,
                  axis, coord, lo, hi) for name, texture, axis, coord, lo, hi in POSTERS)


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


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
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
        prop(f"z2_container_{n}", CONTAINER, SKY_CEIL, rect, light=LIGHT_OUTDOORS, wall=RUST)
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
         light=LIGHT_TUNNEL, wall=TUNNEL)
    stair("z11_passage_step",
          [((PASSAGE_W[1] + STEP_RUN * (n - 1), py1, PASSAGE_W[1] + STEP_RUN * n, py2), GROUND - STEP * n)
           for n in range(1, PASSAGE_STEPS + 1)],
          ceil_above=TUNNEL_HEIGHT, light=LIGHT_TUNNEL, flat=FLOOR_CONCRETE, wall=TUNNEL)
    zone("z11_passage_e", REACTOR, REACTOR + TUNNEL_HEIGHT, [(PASSAGE_E[0], py1, PASSAGE_E[1], py2)],
         light=LIGHT_TUNNEL, wall=TUNNEL)
    zone("z11_swb_niche", GROUND, GROUND + SWITCH_HEIGHT, [SWB_NICHE], light=LIGHT_TUNNEL, wall=STEEL)

    # ======================================================================
    # The covered dock: quays, basin, the crane gallery, the three doors
    # ======================================================================
    zone("z3_d1_porch", GROUND, PORCH, [D1_PORCH_PEN], light=LIGHT_PEN, wall=ROCK)
    zone("z3_south_quay", GROUND, PEN_ROOF, [SOUTH_QUAY], light=LIGHT_PEN, ceiling=CEIL_CONCRETE, wall=ROCK)
    zone("z3_basin", BASIN, PEN_ROOF, [BASIN_RECT], light=LIGHT_PEN, flat=WATER, wall=ROCK)
    zone("z3_north_quay", GROUND, PEN_ROOF, [NORTH_QUAY], light=LIGHT_PEN, ceiling=CEIL_CONCRETE, wall=ROCK)
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
    zone("z4_deck", DECK, PEN_ROOF, [DECK_RECT], light=LIGHT_PEN, flat=FLOOR_PLATE, wall=ARMOUR)
    zone("z4_stern", STERN, PEN_ROOF, [STERN_RECT], light=LIGHT_PEN, flat=FLOOR_PLATE, wall=ARMOUR)
    prop("z4_fin", FIN, PEN_ROOF, FIN_RECT, light=LIGHT_PEN, wall=ARMOUR, ceiling=CEIL_CONCRETE)
    zone("z4_hatch_porch", DECK, INTERIOR, [HATCH_PORCH], light=LIGHT_PEN, flat=FLOOR_PLATE, wall=STEEL)
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
         light=LIGHT_TUNNEL, wall=TUNNEL)
    stair("z7_step",
          [((TUNNEL_W[1] + STEP_RUN * (n - 1), ty1, TUNNEL_W[1] + STEP_RUN * n, ty2), GROUND - STEP * n)
           for n in range(1, TUNNEL_STEPS + 1)],
          ceil_above=TUNNEL_HEIGHT, light=LIGHT_TUNNEL, flat=FLOOR_CONCRETE, wall=TUNNEL)
    zone("z7_tunnel_e", REACTOR, REACTOR + TUNNEL_HEIGHT, [(TUNNEL_E[0], ty1, TUNNEL_E[1], ty2)],
         light=LIGHT_TUNNEL, wall=TUNNEL)
    for name, (door_rect, room_rect) in TUNNEL_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_TUNNEL_AMBUSH, REACTOR, leaf=TUNNEL)

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
    zone("z9_tunnel", GROUND, RAIL_TUNNEL_CEIL, [RAIL_TUNNEL], light=LIGHT_TUNNEL, flat=BALLAST, wall=TUNNEL)
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
         ceiling=CEIL_PANEL, wall=STEEL)
    zone("z10_exit_niche", DECK, DECK + SWITCH_HEIGHT, [EXIT_NICHE], light=LIGHT_BEACON, wall=STEEL)

    # ======================================================================
    # Line styles. The FIRST rule registered on a segment wins.
    # ======================================================================
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    for texture, (x1, _y1, x2, y2) in BAY_FLAGS.items():
        g.style_h(y2, x1, x2, LineStyle(texture=texture))
    # Manual doors, both faces.
    for sector, (x1, y1, x2, y2), horizontal in ((d1, D1_DOOR, True), (d2, D2_DOOR, False),
                                                 (d3, D3_DOOR, False)):
        tag = tm.sectors[sector].identifier
        if horizontal:
            for yy in (y1, y2):
                g.style_h(yy, x1, x2, door_raise_style(tag, sector, texture=DOOR))
        else:
            for xx in (x1, x2):
                g.style_v(xx, y1, y2, door_raise_style(tag, sector, texture=DOOR))
    # The three locks, both faces.
    for yy in (BLUE_DOOR[1], BLUE_DOOR[3]):
        g.style_h(yy, BLUE_DOOR[0], BLUE_DOOR[2],
                  locked_door_style(TAG_BLUE_DOOR, blue_door, LOCK_BLUE_CARD, texture=DOOR))
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
    # The fin's red stars, once on each long face.
    for axis, coord, lo, hi in FIN_STARS:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=ARMOUR_STAR))
    # The boat's control room: its long walls are the boards, one tile high.
    g.style_h(CONTROL[1], CONTROL[0], CONTROL[2], LineStyle(texture=CONTROL_PANEL))
    g.style_h(CONTROL[3], CONTROL[0], CONTROL[2], LineStyle(texture=CONTROL_PANEL))
    # The bow's torpedo tubes.
    g.style_v(TORPEDO[2], TORPEDO[1], TORPEDO[3], LineStyle(texture=TUBBING))
    # The dormitory's lockers, its north wall.
    g.style_h(DORM[3], DORM[0], DORM[2], LineStyle(texture=LOCKER))
    # The locomotive's desk, the cab's south wall (its door is on the north, to the platform).
    g.style_h(CAB[1], CAB[0], CAB[2], LineStyle(texture=CONTROL_PANEL))
    # The boom across the pen's mouth: nothing crosses it, not even swimming.
    for xx in (BOOM[0], BOOM[2]):
        g.style_v(xx, BOOM[1], BOOM[3], BLOCKING)
    # The exit: the regulator at the back of its niche in the cab.
    g.style_v(EXIT_NICHE[2], EXIT_NICHE[1], EXIT_NICHE[3], exit_switch_style(texture=EXIT_FACE))

    g.build()

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
WALL_TEXTURES = ((ROCK, CONCRETE, CONCRETE_STRIPE, STEEL, TUNNEL, BRICK, BRICK_RAIL, RUST, ARMOUR,
                  ARMOUR_STAR, WAGON, TANK, LOCKER, CONTROL_PANEL, TUBBING, ROAD_GATE, CRATE,
                  FLAG_REICH, FLAG_LEGION, LENIN, STALIN, MURAL)
                 + DOOR_LEAVES + SWITCH_FACES + ((MARX_ENGELS,) if MARX_ENGELS else ()))
FLAT_TEXTURES = (FLOOR_LANE, FLOOR_CONCRETE, FLOOR_TILE, FLOOR_PLATE, CEIL_PANEL, CEIL_CONCRETE,
                 CRATE_TOP, GRATING, WATER, TRACK, BALLAST)
BUILTIN_FLATS = (SKY,)
# The naval pieces the design wants and nobody has drawn: {proposed lump:
# the approved lump the map wears for it meanwhile}. The art-director's
# "Naval" set (D112, in draft) replaces them one line each.
NAVAL_SET = {
    "SDROCK1": ROCK,           # living Kola granite: the dock, the cliffs, the reactor hall
    "SDHULL1": ARMOUR,         # the submarine's black rubber-tiled hull and fin
    "SDHULL2": ARMOUR_STAR,    # the fin with the star (a tactical number would be text: D27)
    "SDBULK1": STEEL,          # the boat's inside: bulkheads, pipes, valves
    "SDHTCH1": DOOR,           # the oval watertight hatch (D3)
    "SDTORP1": TUBBING,        # the bow's torpedo-tube doors
    "SDCONT1": RUST,           # a shipping container's side
    "SDLOCO1": ARMOUR,         # the diesel locomotive's body
    "SDREAC1": STEEL,          # the reactor vessel's jacket
    "SDDOORB": DOOR,           # the blue door's trim (the blue door wears SDDOOR1 in blue light)
}
PENDING_TEXTURES = {
    "SDPERI1": "the periscope's tube, masked: the control room's well is a solid steel column meanwhile",
    "SDNSKY1": "the polar night sky with the aurora (MAPINFO's sky, the scaffolding's call)",
}
