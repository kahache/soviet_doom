"""MAP07 «Новая Земля» / Novaya Zemlya - v1: the whole map, textured and populated.

Design document: docs/levels/MAP07-novaya-zemlya.md (section 13 is this build).
Episode 3, «The Portal» (D112), its first map: the Arctic radar station on
the archipelago, November 1977, the polar night. The invaders use the
station's radar as a beacon that guides their reinforcements to the portal.
Sergeant Vilanova lands on the iced runway in a polar-aviation Il-14; he
leaves from the frozen harbour, down the conning tower of the submarine that
takes him on to MAP08.

Built MVP first (D60): complete and walkable from start to exit, both keys on
the route in plain sight on lit places in their lock's colour (D58), the
population and the ammunition of G3-8's budget, three secrets. Balance and
light are later passes. Since D113 it wears Episode 3's Arctic set (snow, ice,
the runway's slabs, the radome's skin, the radar consoles, the hermetic door)
and the Naval set's submarine (hull, deck, bulkhead, panel); the three lumps
the design asked for and nobody drew are resolved in `ARCTIC_SET` below
(design section 7.2).

The route, in one line: the runway (the RED GATE to the harbour seen at once,
down the runway, shut) -> D1, the hangar (the YELLOW DOOR seen in its west
wall) -> D2, the covered service tunnel -> the barracks -> up the tunnel to the
radome's gallery: the YELLOW KEY on the antenna's platform across the drop ->
back to the hangar, the yellow door (and the hangar's two closets) -> the
command room, SW-A, which opens the bunker's stair -> down two flights to the
nuclear-test bunker: the RED KEY before the glowing core, and up the escape
stair to SW-B, which opens a shutter straight onto the runway beside the red
gate -> the red gate (and the runway's two closets) -> the harbour road, the
quay, the last fight -> the gangway, the submarine's deck, D3 into the
conning tower -> the exit switch.

Heights: the runway, the hangar, the barracks, the command room, the quay are
the ground (0); the radome's gallery and the antenna's platform +128 over
the radome's floor (0); the bunker -256; the sea -64; the submarine's deck
+32.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.
Outdoors (the runway, the harbour) the ceiling is F_SKY1, the engine's sky
marker (MAPINFO names the sky; scaffolding's). The kerbs round the runway and
the quay, and the pack ice round the sea, carry a low sky ceiling (Doom's
open-air trick, MAP05's parapets): beyond them the polar night, never a wall.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP07 SKILL=3 tools/run.sh
"""

from __future__ import annotations

from dataclasses import replace
from typing import NamedTuple

from sdbuild.udmf import (
    DOOR_SPEED_SLOW,
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
    skill_tier,
    switch_door_open_style,
)

MAP_NAME = "MAP07"

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# Soviet base.
CONCRETE = "SDCONC1"     # 64x128 prefab panels: the runway's buildings, the escape stair's head
CONCRETE_STRIPE = "SDCONC2"  # 64x128 the red-striped concrete: the barracks
STEEL = "SDSTEL1"        # green riveted plate: the Il-14 (no SDPLAN1 drawn), the dish, door tracks, the gangway
DOOR = "SDDOOR1"         # D1, D2, D3
CRATE = "SDCRAT1"        # 64x64 crate face: the runway's and the hangar's stacks
LOCKER = "SDLOCK1"       # 64x128 barracks lockers: the alcoves, S2's panel
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
CEIL_PANEL = "SDCEIL1"
CEIL_CONCRETE = "SDCEIL2"
CRATE_TOP = "SDCRTOP1"
# Metro (D42, D48).
TILE = "SDTILE1"         # 64x128 cream glazed tile: the command room
TUNNEL = "SDTUNL1"       # 64x128 tunnel concrete with cable runs: the covered service tunnels
TUBBING = "SDTUBB1"      # 128x128 cast-iron tubbing: the nuclear-test bunker
HAZARD = "SDMEDG1"       # 64x64 chevron band: the test chamber's passage
# Tankograd (D66).
BRICK = "SDBRCK1"        # 64x128 soot brick: the port's gatehouse at the runway's west end
RUST = "SDRUST1"         # 64x128 corrugated sheet: the hangar
FLAG_USSR_1 = "SDFLAG1"   # two Soviet flags side by side by the red gate (D119: SDFLAG1-4 are Soviet)
FLAG_USSR_2 = "SDFLAG2"
DOOR_YELLOW = "SDDOORY"  # the yellow lock's leaf
DOOR_RED = "SDDOORR"     # the red lock's leaf
RAMP = "SDGATE1"         # 128x128 corrugated gate: the Il-14's cargo ramp (S1's panel)
CORE = "SDPORT1"         # 128x128 the portal's cobalt (SDPORT1-4 by ANIMDEFS): the bunker's sealed core
PLATE = "SDFLR4"         # chequer plate: the plane's and the consoles' tops, the tower, the map table
# Episode 2 (D107).
DAM = "SDDAM1"           # 64x128 pale mass concrete: the steps up the quay wall (drawn wet, SDDAM2)
DAM_WET = "SDDAM2"       # 64x128 the same at the waterline: the quay wall over the sea
CONTROL_PANEL = "SDCTRL1"  # 128x128 control board: the command room's east board and the consoles' desk
GRATING = "SDGRAT2"      # expanded metal: the antenna's platform and the dish's mesh, seen from below
WATER = "SDWATR1"        # the Barents Sea's open lead (SDWATR2-4 by ANIMDEFS)
TANKER = "SDTANK1"       # 128x128 black tank wagon «НЕФТЬ»: the runway's fuel bowser
ARMOUR_STAR = "SDARMR1"  # 128x128 the plate with the red star: once, on the conning tower
WAREHOUSE = "SDBRCK3"    # 64x128 roundhouse brick: the harbour's warehouses and sheds
STORE_GATE = "SDGATE2"   # 128x128 goods-shed door «СКЛАД»: S3's panel
# Episode 3 (D112, D113): the Arctic set (gen_arctic.py) and the Naval set's
# submarine (gen_naval.py, MAP08's; a submarine is a submarine).
SNOW = "SDSNOW1"         # flat: wind-packed snow: the road, the quay, the snowbanks, the porches outside
RUNWAY_SLABS = "SDRWY1"  # flat: the runway's PAG slabs; tyre marks along the tile's y ...
RUNWAY_LINE = "SDRWY2"   # flat: ... the same slabs (same seed) with the centre-line dash along y
RUNWAY_TURN = {"rotationfloor": 90.0}   # both turned alike: y runs down the runway, the twins meet seamless
SEA_ICE = "SDICE1"       # flat: sea ice: the floes and the pack ice
ICE_WALL = "SDICE2"      # 64x128 glacier ice: the floes', the pack ice's and the snowbanks' faces
RADOME_SKIN = "SDRADM1"  # 128x128 the radome's fibreglass panels, its walls and its crown
HUT = "SDHUT1"           # 64x128 frosted corrugated sheet: the harbour's two sheds inside
RADAR = "SDRADR1"        # 128x128 radar console (SDRADR1-4 by ANIMDEFS): the command room's north boards
BLAST_DOOR = "SDHERM1"   # 128x128 the hermetic door: the bunker's two shutters, on the bunker's side
HULL_SIDE = "SDHULL1"    # 128x128 the submarine's black rubber-tiled hull and conning tower
HULL_NUMBER = "SDHULL2"  # 128x128 the same with «471»: once, on the tower's south face
DECK_RUBBER = "SDRUBR1"  # flat: the deck's rubber tiles, the worn path along y (the boat lies along y)
BULKHEAD = "SDBULK1"     # 128x128 round watertight door «3»: D3, the conning tower's hatch
NAV_PANEL = "SDNAVC1"    # 128x128 control-room panel: inside the conning tower, round the exit
SKY = "F_SKY1"           # the engine's sky marker, not a lump of ours (check_pk3 knows it)
# The posters (CEO 2026-10-22: «que esos posters puedan aparecer en cualquier
# nivel»; tests/test_posters.py).
LENIN = "SDPOSTR1"       # 128x256: the hangar's east wall, facing the yellow door
STALIN = "SDPOSTR3"      # 128x256: the command room's north wall, between the boards
MURAL = "SDPOSTR2"       # 128x128 cosmonautics mural: the barracks' red corner, on a sill
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
LUMP_WIDTH = {DAM_WET: 64, ICE_WALL: 64, RADOME_SKIN: 128, HULL_SIDE: 128}
WALL_TILE = 128          # the height SDDAM2, SDCTRL1, SDICE2, SDRADM1 and SDHULL1 repeat at
CONTROL_DESK_ROW = 64    # SDCTRL1: the desk (mimic bars, buttons, toggles) starts at this row

# Switches (D25), one variant per switch; the exit keeps the hazard panel
# every map's exit wears.
SW_A_FACE = "SDSW1A"     # command room: the knife switch, opens the bunker's stair
SW_B_FACE = "SDSW1B"     # bunker's escape stair: the push button, opens the shutter onto the runway
EXIT_FACE = "SDSW1D"
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64
SWITCH_HEIGHT = 128
DOOR_TILE = 128
DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_RED, BULKHEAD, BLAST_DOOR)

# --- The Arctic set: what the design asked for, what the map wears ----------
# {lump the design proposed (section 7.2): the lump the map wears for it}.
# Where the proposed lump was drawn (D113) the two are the same; where it was
# not, the nearest installed lump stands in. The day a proposed lump appears
# in assets/, tests/test_map07_novaya_zemlya.py turns red until the map wears it.
ARCTIC_SET = {
    "SDSNOW1": SNOW,             # flat: packed snow on the road, the quay, the snowbanks (the runway is SDRWY1)
    "SDSNOW2": ICE_WALL,         # not drawn: the snowbanks' faces wear the glacier ice
    "SDICE1": SEA_ICE,           # flat: sea ice, the floes and the pack ice
    "SDICE2": ICE_WALL,          # wall: the ice's edge, the floes' and the pack's faces
    "SDRADM1": RADOME_SKIN,      # wall: the radome's fibreglass panels
    "SDPLAN1": STEEL,            # not drawn: the Il-14 stays riveted steel (S1 is steel against the ramp)
    "SDSUBH1": HULL_SIDE,        # not drawn under that name: the Naval set's SDHULL1 is the hull
    "SDMAPT1": PLATE,            # not drawn: no installed flat is a map; the table stays chequer plate
    "SDRADR1": RADAR,            # wall: the radar console, its PPI scope sweeping (ANIMDEFS)
}

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED in engine
# on MAP02 and MAP03. Delay 0: opens and stays open.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock numbers from gzdoom.pk3 g4.14.2 -> lockdefs.txt: `Lock 1 Doom
# { RedCard ... }`, `Lock 3 Doom { YellowCard ... }`, both opened in the
# engine on MAP03.
LOCK_RED_CARD = 1
LOCK_YELLOW_CARD = 3
# Floor_LowerToLowest (tag, speed): 21 in ZDoom's (Hexen's) special table, the
# special MAP04's red key gives its gondolas. NOT VERIFIED in our engine runs
# (MAP04's K3; here V19-V21): if it failed, the radar's lift, the bunker's
# cells and the snowbank would stay shut, and nothing the route needs is in them.
SPECIAL_FLOOR_LOWER_TO_LOWEST = 21
# Doom's editor numbers; SD_RedPass and SD_YellowPass replace the cards.
ED_RED_CARD = 13
ED_YELLOW_CARD = 6
KEY_LOCKS = {ED_RED_CARD: LOCK_RED_CARD, ED_YELLOW_CARD: LOCK_YELLOW_CARD}

ED_PLAYER1_START = 1

# --- Heights -------------------------------------------------------------------
GROUND = 0               # the runway, the hangar, the barracks, the command room, the radome's floor, the quay
GALLERY = 128            # the radome's entrance gallery and the antenna's platform
BUNKER = -256            # the nuclear-test bunker
SEA = -64                # the open lead in the harbour
DECK = 32                # the submarine's deck
STEP = 16                # every stair step; under MAX_STEP_UP 24
STEP_RUN = 32            # every stair step is 32 deep
FLIGHT_STEPS = 7         # seven steps and a landing: 128 per flight
DOOR_HEIGHT = 128
ROOF = GROUND + DOOR_HEIGHT     # every porch, tunnel and shed
SKY_CEIL = 512                   # outdoors: the polar night
KERB = 32                        # the snowbanks: cover to the knee, never a step
KERB_SKY = KERB + 16             # the open-air trick over the kerbs
ICE_LIP = SEA + STEP             # the pack ice: one step out of the water ...
ICE_SKY = ICE_LIP + 16           # ... and the sky just over it
PAD = 16                         # the key pads: one step up
CONSOLE = 32                     # the command room's consoles and map table: waist high
HANGAR_CEIL = 320
BARRACKS_CEIL = 160
COMMAND_CEIL = 256               # the posters stand straight on its walls
RADOME_CEIL = 512                # the radome's rim
DOME_CEIL = 704                  # its crown
DISH_CEIL = 640                  # the dish's underside over the antenna's platform
BUNKER_CEIL = BUNKER + 224
FUSELAGE = 160                   # the Il-14 on the runway
WING = 64                        # low wings: a polar Il-14, not a high-wing An-12
NACELLE = 128
TAILPLANE = 96
TANKER_TOP = 128                 # the fuel bowser: one SDTANK1 tile high
CRATES = 64
BUNK = 32
AIRFRAME = 128                   # the Il-14 under repair in the hangar
SAIL_TOP = DECK + DOOR_HEIGHT    # the conning tower: one SDARMR1 panel high
CORE_SILL = BUNKER + 48          # the core's viewing slot: over the knee, never entered
NICHE_DEPTH = 16
CLOSET_HEIGHT = 128
POSTER_HEIGHT = 256
MURAL_SILL = 32

# --- Light ---------------------------------------------------------------------
# The polar night. 192 is spent on five places only: the two locks, the two
# keys and the exit (MAP02 v1's rule).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_OUTDOORS = 128     # the runway and the quay under the floodlights
LIGHT_SEA = 112
LIGHT_HANGAR = 144
LIGHT_TUNNEL = 112
LIGHT_BARRACKS = 128
LIGHT_RADOME = 144
LIGHT_DISH = 128         # under the dish
LIGHT_COMMAND = 160
LIGHT_BUNKER = 112
LIGHT_LAMP = 144         # the bunker's one lamp, flickering against the hall
LIGHT_CHAMBER = 96
LIGHT_CORE = 176         # the sealed core glows: bright, but not a beacon
LIGHT_CLOSET = 112
LIGHT_SHED = 112
LIGHT_SHADOW = LIGHT_MIN  # a secret's set-back panel: the one in shadow
LIGHT_SECRET = 112
BEACON_ZONES = ("z1_red_portal", "z2_yellow_portal", "z5_key_pad", "z7_key_plinth", "z12_exit_niche")

# The keys' colours, in light (sector `lightcolor`, as MAP03-MAP06): the
# colour of the lock is the colour of where its key lies.
YELLOW = 0xFFD860        # MAP03's
RED = 0xFF6048           # MAP03's
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- The sea -------------------------------------------------------------------
# The open lead the icebreakers keep at the quay: freezing, a light sting,
# not a trap (MAP05's channel: Doom's nukage, 5 every 32 tics); steps up the
# quay wall at three places.
WATER_DAMAGE = 5
WATER_DAMAGE_INTERVAL = 32
WATER_HURTS = {"damageamount": WATER_DAMAGE, "damageinterval": WATER_DAMAGE_INTERVAL}

# --- Tags --------------------------------------------------------------------
TAG_D1_HANGAR = 1
TAG_D2_TUNNEL = 2
TAG_D3_HATCH = 3         # the conning tower's hatch, the last door before the exit
TAG_YELLOW_DOOR = 4      # hangar -> command room: Door_LockedRaise, lock 3; and the hangar's closets
TAG_RED_GATE = 5         # runway -> harbour: Door_LockedRaise, lock 1; and the runway's closets
TAG_S1_PANEL = 6
TAG_S2_PANEL = 7
TAG_S3_PANEL = 8
TAG_BUNKER_SHUTTER = 10  # SW-A: the bunker's stair
TAG_RUNWAY_SHUTTER = 11  # SW-B: the escape stair's shutter onto the runway
# Closets ride the lock that lets the player past them (MAP05's rule): the
# yellow door opens the hangar's two, the red gate the runway's two.
TAG_HANGAR_AMBUSH = TAG_YELLOW_DOOR
TAG_RUNWAY_AMBUSH = TAG_RED_GATE
# V3 (D120, A2 and A3): tags only a pickup moves (no line carries them).
TAG_RADAR_LIFT = 12      # the yellow key: the radar's cargo lift comes down with the Reich
TAG_BUNKER_CELLS = 13    # the red key: the containment cells' walls sink into the floor
TAG_SNOWBANK = 14        # the road's medikit: the snowbank sinks off the warehouse's front
LIFT_SPEED = 8           # 1 unit a tic: the car's 128 take ~3.7 s, the winch heard all the way
WALL_SPEED = 32          # 4 units a tic: the cells' 224 are down in ~1.6 s
BANK_SPEED = 16          # 2 units a tic: the bank's 128 in ~1.8 s

# --- The plan (x east, y north; design document section 4) ---------------------
# The runway, the start at its east end beside the Il-14.
RUNWAY = (1664, 0, 4608, 576)
CENTRELINE = (1728, 256, 3776, 320)
KERBS = {"s": (1664, -32, 4640, 0), "e": (4608, 0, 4640, 608),
         "n1": (2432, 576, 3456, 608), "n2": (4352, 576, 4640, 608)}
# The Il-14: a fuselage, two low wings, two nacelles over them, the
# tailplane; its hold is S1, behind the cargo ramp under the tail.
FUSELAGE_RECT = (3840, 240, 4352, 368)
WINGS = ((4032, 64, 4160, 240), (4032, 368, 4160, 544))
NACELLES = ((3968, 128, 4064, 176), (3968, 432, 4064, 480))
TAILPLANES = ((4288, 176, 4352, 240), (4288, 368, 4352, 432))
S1_HOLD = (4192, 256, 4336, 352)
S1_PANEL = (4336, 256, 4352, 352)
RAMP_PORCH = (4352, 256, 4384, 352)    # under the tail fin
TANKER_RECT = (2816, 96, 3072, 160)
RUNWAY_CRATES = ((2304, 384, 2432, 448), (3328, 64, 3392, 192))
# The west end: the port's gatehouse, the red gate in it, the Soviet flags.
RED_PORTAL = (1600, 224, 1664, 352)
RED_GATE = (1568, 224, 1600, 352)
GATE_PORCH = (1536, 224, 1568, 352)
FLAG_RECESSES = {FLAG_USSR_1: (1648, 384, 1664, 448), FLAG_USSR_2: (1648, 448, 1664, 512)}
# The north side's west part: the bunker's block; the escape stair's shutter
# and the red gate's two closets are cut into its front.
BUNKER_FRONT_X = (1664, 2432)
RUNWAY_SHUTTER = (1792, 576, 1920, 608)
ESCAPE_TOP = (1792, 608, 1920, 672)
ESCAPE_X = (1792, 1920)
ESCAPE_STEPS = (GROUND - BUNKER) // STEP - 1          # 15: the bunker's floor is the 16th rise
SWB_NICHE = (1920, 608, 1936, 672)
RUNWAY_CLOSETS = {"closet_z1_a": ((2048, 576, 2176, 592), (2048, 592, 2176, 720)),
                  "closet_z1_b": ((2240, 576, 2368, 592), (2240, 592, 2368, 720))}
# The hangar, north of the runway's east part.
HANGAR = (3456, 704, 4352, 1344)
HANGAR_FRONT_X = (3456, 4352)
D1_OUT = (3840, 576, 3968, 608)
D1_DOOR = (3840, 608, 3968, 640)
D1_IN = (3840, 640, 3968, 704)
D2_PORCH = (3840, 1312, 3968, 1344)
D2_DOOR = (3840, 1344, 3968, 1376)
YELLOW_PORTAL = (3392, 960, 3456, 1088)
YELLOW_DOOR = (3360, 960, 3392, 1088)
COMMAND_PORCH = (3328, 960, 3360, 1088)
HANGAR_CLOSETS = {"closet_z2_n": ((4352, 1120, 4368, 1248), (4368, 1120, 4496, 1248)),
                  "closet_z2_s": ((4352, 768, 4368, 896), (4368, 768, 4496, 896))}
HANGAR_CRATES = ((3584, 736, 3648, 800), (3520, 1184, 3584, 1248), (4160, 832, 4224, 960))
AIRFRAME_RECT = (3712, 1120, 4032, 1216)
# The covered service tunnels and the barracks.
TUNNEL_N = (3840, 1376, 3968, 1728)
BARRACKS = (3456, 1728, 4352, 2176)
BUNKS = ((3584, 1792, 3776, 1856), (3584, 2048, 3776, 2112), (4096, 1792, 4288, 1856),
         (4096, 2048, 4288, 2112))
LOCKER_ALCOVES = {"z4_lockers_w": (3520, 2176, 3776, 2192), "z4_lockers_e": (4032, 2176, 4288, 2192)}
RED_CORNER_NICHE = (3840, 2176, 3968, 2192)
TUNNEL_W_Y = (1920, 2048)
TUNNEL_W_STEPS = (GALLERY - GROUND) // STEP          # 8: the eighth is level with the gallery
TUNNEL_W_X0 = 3456                                   # the barracks' west wall
# S2: the lockers' east alcove; one bay stands 16 further back, in shadow.
S2_NICHE = (4160, 2192, 4224, 2208)
S2_PANEL = (4160, 2208, 4224, 2224)
S2_PASSAGE = (4160, 2224, 4224, 2288)
S2_STORE = (4032, 2288, 4352, 2432)
# The radome: a stepped octagon, its crown, the dish over the antenna's
# platform, the gallery the tunnel arrives on.
RADOME = (2176, 1536, 3200, 2560)
DOME = (2304, 1664, 3072, 2432)
CHAMFER = ((192, 64), (128, 128), (64, 192))      # each corner, stepped
DISH = (2432, 1792, 2944, 2304)
PLATFORM = (2560, 1920, 2816, 2176)
PEDESTAL = (2656, 2016, 2720, 2080)               # the antenna's mast: solid, up into the dish
KEY_PAD = (2752, 2016, 2816, 2080)
PLATFORM_STAIR_X = (2624, 2752)
PLATFORM_STAIR_STEPS = (GALLERY - GROUND) // STEP - 1   # 7: the platform is the 8th rise
BALCONY = (3008, 1856, 3200, 2112)
BALCONY_STAIR_X = (3072, 3200)
BALCONY_STAIR_STEPS = 7                              # down north to the floor, the 8th rise is the floor
# The command room, behind the yellow door.
COMMAND = (2688, 832, 3328, 1344)
CONSOLES = ((2816, 960, 2944, 1024), (3072, 960, 3200, 1024))
MAP_TABLE = (2880, 1120, 3136, 1216)
SWA_NICHE = (2672, 1024, 2688, 1088)
SHUTTER_PORCH = (2688, 1152, 2720, 1280)
BUNKER_SHUTTER = (2656, 1152, 2688, 1280)
STALIN_X = (2944, 3072)                              # on the north wall, between the boards
SLOTS_X = {"z6_slot_w": (2752, 2880), "z6_slot_e": (3136, 3264)}   # the south wall, either side of its axis
BOARD_DEPTH = 8
CONTROL_BOARDS = {
    "prop_z6_board_nw": ((COMMAND[0], COMMAND[3] - BOARD_DEPTH, STALIN_X[0], COMMAND[3]),
                         ("h", COMMAND[3] - BOARD_DEPTH, COMMAND[0], STALIN_X[0])),
    "prop_z6_board_ne": ((STALIN_X[1], COMMAND[3] - BOARD_DEPTH, COMMAND[2], COMMAND[3]),
                         ("h", COMMAND[3] - BOARD_DEPTH, STALIN_X[1], COMMAND[2])),
    "prop_z6_board_e": ((COMMAND[2] - BOARD_DEPTH, 1152, COMMAND[2], 1280),
                        ("v", COMMAND[2] - BOARD_DEPTH, 1152, 1280)),
}
# The boards' faces: the two flanking Stalin are radar consoles (two PPI scopes
# each, 256 long); the east one stays the control board the consoles' desk matches.
BOARD_FACES = {"prop_z6_board_nw": RADAR, "prop_z6_board_ne": RADAR, "prop_z6_board_e": CONTROL_PANEL}
# The bunker: the stair from the command room, the hall, the test chamber.
BUNKER_STAIR_Y = (1152, 1280)
STAIR_TOP = (2592, 1152, 2656, 1280)
BUNKER_LANDING = (2304, 1152, 2368, 1280)
BUNKER_HALL = (1536, 1152, 2080, 1856)
PILLARS = ((1664, 1600, 1728, 1664), (1888, 1600, 1952, 1664))
LAMP = (1728, 1408, 1856, 1536)
PASSAGE = (1728, 1856, 1856, 1920)
CHAMBER = (1536, 1920, 2048, 2368)
KEY_PLINTH = (1760, 2112, 1824, 2176)
CORE_SLOT = (1728, 2368, 1856, 2384)
# The harbour: the road from the red gate, the quay, the sea, the submarine.
ROAD = (1152, 128, 1536, 448)
QUAY = (768, -256, 1152, 1664)
SEA_RECT = (0, -256, 768, 1664)
SEA_STEPS_Y = ((128, 256), (768, 896), (1408, 1536))   # where the quay wall has steps out
QUAY_KERBS = {"n": (768, 1664, 1152, 1696), "s": (768, -288, 1152, -256)}
PACK_ICE = {"w": (-32, -288, 0, 1696), "n": (0, 1664, 768, 1696), "s": (0, -288, 768, -256)}
FLOES = ((64, 1408, 192, 1536), (544, -192, 672, -64))
HULL = ((256, 256, 512, 1280), (320, 1280, 448, 1344), (320, 192, 448, 256))
GANGWAY = (512, 928, 768, 1056)
SAIL = (272, 672, 448, 928)
SAIL_ROOM = (304, 736, 416, 864)
HATCH = (416, 736, 448, 864)
HATCH_PORCH = (448, 736, 480, 864)
EXIT_NICHE = (288, 768, 304, 832)
SAIL_STAR = ("h", SAIL[3], 296, 424)        # SDARMR1 once, on the tower's north face
SAIL_NUMBER = ("h", SAIL[1], 296, 424)      # SDHULL2 «471» once, on its south face
SHED = (1168, 1088, 1344, 1280)             # the open shed (the comparison)
SHED_DOORWAY = (1152, 1120, 1168, 1248)
SHED_PORCH = (1120, 1120, 1152, 1248)
S3_SHED = (1168, 1408, 1344, 1600)          # S3: the shut one
S3_PANEL = (1152, 1440, 1168, 1568)
S3_PORCH = (1120, 1440, 1152, 1568)
SHED_FRONT_X = 1152
# The posters (design section 7.3). Lenin in a recess in the hangar's east
# wall, facing the yellow door across the hangar; Stalin straight on the
# command room's north wall between its boards (the room is 256 high); the
# mural on a sill in the barracks' red corner, between the locker alcoves;
# the two Marx-Engels slots straight on the command room's south wall, either
# side of the room's axis: seen from the room (facing south) Marx is the east
# one, on the left, and Engels the west one (D117).
LENIN_NICHE = (HANGAR[2], 960, HANGAR[2] + NICHE_DEPTH, 1088)
POSTERS = (
    ("z2_lenin", LENIN, "v", LENIN_NICHE[2], LENIN_NICHE[1], LENIN_NICHE[3]),
    ("z6_stalin", STALIN, "h", COMMAND[3], *STALIN_X),
    ("z4_mural", MURAL, "h", RED_CORNER_NICHE[3], RED_CORNER_NICHE[0], RED_CORNER_NICHE[2]),
    ("z6_slot_w", ENGELS, "h", COMMAND[1], *SLOTS_X["z6_slot_w"]),
    ("z6_slot_e", MARX, "h", COMMAND[1], *SLOTS_X["z6_slot_e"]),
)
POSTER_SLOTS_MARX_ENGELS = ("z6_slot_e", "z6_slot_w")   # Marx, Engels

# --- Things --------------------------------------------------------------------
PLAYER_START = (3712, 224)
PLAYER_ANGLE = 180       # facing west, down the runway, towards the red gate
YELLOW_KEY_SPOT = (2784, 2048)   # on the antenna's platform, across the drop from the gallery
RED_KEY_SPOT = (1792, 2144)      # on the plinth before the core, in the test chamber
KEY_ZONES = {ED_YELLOW_CARD: "z5_key_pad", ED_RED_CARD: "z7_key_plinth"}
LOCK_PORTALS = {LOCK_YELLOW_CARD: "z2_yellow_portal", LOCK_RED_CARD: "z1_red_portal"}

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design
WINDOWS: tuple[str, ...] = ()    # nothing seen through and never walked
SECRET_ZONES = ("s1_hold", "s2_store", "s3_shed")
CLOSET_PREFIX = "closet_"

# --- V3: events on pickup and the set pieces (D120's A2 and A3) -----------------
# A thing whose UDMF `special` GZDoom runs when it is picked up (MAP04's red
# key, MAP09's red key; the Door_Open form VERIFIED in the engine by
# tunguska-critical's RKEY, 2026-10-23). Each event's tag is carried by no
# line; its monsters wait where no line has an opening (nothing sees or
# hears them) until it fires; a flickering lamp (sector special 65, the
# bunker's lamp) stands in front of it, seen before it fires, and the
# moving floor sounds. None is on the critical path, none shuts the player
# in. Design document section 17; tests/_pickup_events_e3.py checks them.
class PickupEvent(NamedTuple):
    name: str
    trigger: int                      # editor number of the thing that carries the special
    spot: tuple[int, int]             # where that thing lies
    special: int
    args: tuple[int, ...]             # the tag first
    zones: tuple[str, ...]            # the sectors the tag moves
    waiting: tuple[str, ...]          # where the released monsters wait
    lamp: str                         # the warning lamp, in front of the event


# A3, the radar's cargo lift: its car waits up at the gallery's height (128)
# behind a gate a door high in the radome's west wall, so from the radome it
# is the car's steel face under the gate's lintel; the yellow key brings it
# down to the floor with three of the Reich's.
RADAR_LIFT_GATE = (2144, 2128, 2176, 2224)
RADAR_LIFT_CAR = (2064, 2096, 2144, 2256)
# A2, the bunker's containment cells: two cells behind the test chamber's west
# wall; each wall panel is a sector whose floor stands at the chamber's
# ceiling and sinks to its floor when the red key is taken. Its lamp is the
# strip of chamber in front of it.
BUNKER_CELLS = {"z7_cell_s": ((1520, 1984, 1536, 2112), (1424, 1968, 1520, 2128), (1536, 1984, 1552, 2112)),
                "z7_cell_n": ((1520, 2176, 1536, 2304), (1424, 2160, 1520, 2320), (1536, 2176, 1552, 2304))}
CELL_HEIGHT = 128
# A3, the snowbank that sinks: a bank of snow a door high against a
# warehouse's front on the harbour road, under a broken floodlight; the
# medikit lies in its light. Taken, the bank sinks into the road and the
# warehouse's ground floor behind it is open, the Legion inside.
SNOWBANK = (1280, 448, 1408, 480)
SNOWBANK_POCKET = (1264, 480, 1424, 608)
SNOWBANK_LAMP = (1280, 416, 1408, 448)
SNOWBANK_TOP = GROUND + DOOR_HEIGHT
MEDIKIT_SPOT = (1344, 432)
LIGHT_EVENT_LAMP = 160   # each event's lamp, flickering down to its darkest neighbour


# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich
ED_TROOPER = 21101        # SD_LegionTrooper, Legion
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both
ED_HOUND = 21103          # SD_ReichHound, Reich
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, flies
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich
ED_PANZER_HEAVY = 21107   # SD_PanzermenschSchwer, Reich
ED_GUNNER = 21110         # SD_LegionGunner, Legion (D116): the heavy machine-gunner
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
    "heavy": ED_PANZER_HEAVY,
    "gunner": ED_GUNNER,
}
MONSTER_CLASSES = {
    ED_RIFLEMAN: "SD_ReichRifleman",
    ED_TROOPER: "SD_LegionTrooper",
    ED_STORMTROOPER: "SD_Stormtrooper",
    ED_HOUND: "SD_ReichHound",
    ED_DOUGHBOY: "SD_Doughboy",
    ED_PANZERMENSCH: "SD_Panzermensch",
    ED_PANZER_HEAVY: "SD_PanzermenschSchwer",
    ED_GUNNER: "SD_LegionGunner",
}
REICH = ("rifleman", "hound", "panzermensch", "heavy")
LEGION = ("trooper", "doughboy", "gunner")
# Where each faction stands (D35: both on the map). The Liberty Legion came
# by air: it holds the airfield (the runway, the hangar) and sleeps in the
# barracks; the Fourth Reich runs the beacon: the tunnels, the radome and
# the bunker under it. Both man the command room and both hold the harbour,
# the last fight. Stormtroopers are hybrids and stand anywhere; the closets
# are counter-attacks, not garrisons. The General is MAP03's and MAP06's.
LEGION_GROUND = ("z1_", "z2_", "z4_")
REICH_GROUND = ("z3_", "z5_", "z7_")
BOTH_GROUND = ("z6_", "z8_", "z9_", "z10_", "z11_", "z12_")
# The arsenal (MAPINFO DoomEdNums 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ED_AKM = 21008            # slot 4's second weapon (D116): episode 3 may start here, with the pistol
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_AKM, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # in S3 only, on the quay, for the last fight
# Ammo, health and armour: Doom's numbers, which our classes replace.
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
# V3 A4, the RGD-5 hand grenade (ADR 012; docs/engine/2026-10-23_V3_rgd5.md
# section 6): its own pool, counted 1.25 shell-equivalents a grenade
# (BALANCE 8.1). A grenade is a consumable here, so it rides in ITEMS and
# scales DOWN with skill: 4 / 3 / 2 grenades on skills 2 / 3 / 4.
ED_RGD5 = 21009           # the pouch: the weapon and two grenades
ED_RGD5_AMMO = 21021      # one loose grenade (it gives the weapon too)
ED_RGD5_BOX = 21022       # a crate of four: a secret's reward only (none here)
# V3 B5, the propaganda radio (D124; docs/sound/2026-10-23_V3_propaganda-radio.md
# 5.4): SD_Loudspeaker, a positional voice over the music (MOD-SPEC 6.14).
ED_LOUDSPEAKER = 21201
LOUDSPEAKER_FLAG_OLIVE = 8  # SD_LS_FLAG_OLIVE: the army's olive SDLO, not the grey street SDLS (D132)
ED_AKM_MAG = 21020        # SD_AkmAmmo: one 30-round 7.62x39 magazine (ADR 011)

# The events, in the order the route meets them (design section 17).
PICKUP_EVENTS = (
    PickupEvent("radar_lift", ED_YELLOW_CARD, YELLOW_KEY_SPOT, SPECIAL_FLOOR_LOWER_TO_LOWEST,
                (TAG_RADAR_LIFT, LIFT_SPEED), ("z5_lift_car",), ("z5_lift_car",), "z5_lift_gate"),
    PickupEvent("bunker_cells", ED_RED_CARD, RED_KEY_SPOT, SPECIAL_FLOOR_LOWER_TO_LOWEST,
                (TAG_BUNKER_CELLS, WALL_SPEED), tuple(f"{n}_wall" for n in BUNKER_CELLS),
                tuple(BUNKER_CELLS), "z7_cell_s_lamp"),
    PickupEvent("snowbank", ED_MEDIKIT, MEDIKIT_SPOT, SPECIAL_FLOOR_LOWER_TO_LOWEST,
                (TAG_SNOWBANK, BANK_SPEED), ("z8_snowbank",), ("z8_snowbank_pocket",), "z8_snowbank_lamp"),
)

# Design section 9: monsters per skill, Doom's skill pairs (udmf.skill_tier).
ENEMY_TOTALS = {2: 37, 3: 55, 4: 72}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Facing: 0
# east, 90 north, 180 west, 270 south.
MONSTERS = (
    # The runway: the Legion's picket along the runway. The start is safe
    # (tests/test_safe_starts.py: nobody sees it within 768): the first
    # trooper crouches behind the crates west of the plane, out of sight
    # until the player walks round them; the second stands on the runway
    # 840 off, seen, the first shot the player's (PM, 2026-10-22 14:13: at
    # 300 and 580 the two of them took a skill-3 player to 3 % in 1.3 s).
    ("z1_runway", "trooper", 3296, 128, 0, 2),
    ("z1_runway", "trooper", 2880, 352, 0, 2),
    ("z1_runway", "trooper", 2688, 448, 0, 3),
    ("z1_runway", "doughboy", 2176, 448, 0, 3),
    ("z1_runway", "stormtrooper", 2560, 160, 0, 4),
    ("z1_runway", "trooper", 1920, 480, 0, 4),
    # The Legion's machine-gunners (D116): three, four, five by skill, each
    # by cover with a long line down ground the player must cross. On the
    # runway, behind the west crates, the runway's whole length east of him
    # (1480 from the start: tests/test_safe_starts.py); by the red gate on
    # skill 4, the gate's flags at his back.
    ("z1_runway", "gunner", 2240, 416, 0, 2),
    ("z1_runway", "gunner", 1792, 96, 0, 4),
    # The hangar: the Legion's ground crew.
    ("z2_hangar", "trooper", 3648, 960, 270, 2),
    ("z2_hangar", "trooper", 4096, 1024, 180, 2),
    ("z2_hangar", "stormtrooper", 3648, 1280, 270, 2),
    ("z2_hangar", "trooper", 4224, 1280, 180, 3),
    # Behind the airframe under repair, the hangar's floor to its door.
    ("z2_hangar", "gunner", 3872, 1264, 270, 2),
    # The covered tunnel: the Reich's sentries.
    ("z3_tunnel_n", "rifleman", 3904, 1504, 270, 2),
    ("z3_tunnel_n", "hound", 3904, 1632, 270, 3),
    # The barracks: the Legion asleep, then not.
    ("z4_barracks", "trooper", 3904, 1856, 270, 2),
    ("z4_barracks", "trooper", 3968, 2080, 270, 2),
    ("z4_barracks", "trooper", 3520, 1952, 0, 2),
    ("z4_barracks", "stormtrooper", 4224, 1952, 180, 3),
    ("z4_barracks", "trooper", 4288, 1760, 180, 4),
    # The radome: the Reich at the beacon; the Panzermensch under the crown
    # on every skill, the RPG-7 met before, in the barracks.
    ("z5_dome", "panzermensch", 2560, 2368, 270, 2),
    ("z5_platform", "rifleman", 2608, 2144, 0, 2),
    ("z5_dome", "hound", 2368, 1984, 0, 2),
    ("z5_radome", "rifleman", 2880, 1600, 90, 2),
    ("z5_dish", "stormtrooper", 2880, 1856, 180, 3),
    # V3 (A3): the radar's cargo lift, down with the yellow key, the Reich's
    # three that stood by the radome's west wall and under the dish.
    ("z5_lift_car", "rifleman", 2104, 2120, 0, 2),
    ("z5_lift_car", "hound", 2104, 2180, 0, 3),
    ("z5_lift_car", "rifleman", 2104, 2232, 0, 4),
    ("z5_radome", "hound", 2688, 1600, 90, 4),
    # The command room: both factions at the plotting table.
    ("z6_command", "trooper", 2784, 1248, 270, 2),
    ("z6_command", "rifleman", 3232, 1120, 180, 2),
    ("z6_command", "stormtrooper", 3008, 1280, 270, 2),
    ("z6_command", "trooper", 2752, 896, 90, 3),
    ("z6_command", "rifleman", 3264, 896, 180, 3),
    ("z6_command", "stormtrooper", 3008, 896, 90, 4),
    # The yellow door's closets in the hangar: the Legion comes back.
    ("closet_z2_n", "trooper", 4400, 1152, 180, 2),
    ("closet_z2_n", "stormtrooper", 4464, 1216, 180, 4),
    ("closet_z2_s", "trooper", 4400, 800, 180, 2),
    # The bunker: the Reich's, the hounds in the dark.
    ("z7_landing", "rifleman", 2336, 1216, 180, 2),
    ("z7_hall", "hound", 1792, 1344, 90, 2),
    ("z7_hall", "panzermensch", 1792, 1728, 270, 2),
    ("z7_chamber", "rifleman", 1984, 2304, 180, 3),
    ("z7_chamber", "heavy", 1600, 2304, 0, 4),
    # V3 (A2): the containment cells, open when the red key is taken: the
    # hall's two riflemen and two hounds wait in them now.
    ("z7_cell_s", "rifleman", 1472, 2016, 0, 2),
    ("z7_cell_n", "rifleman", 1472, 2208, 0, 2),
    ("z7_cell_n", "hound", 1472, 2280, 0, 3),
    ("z7_cell_s", "hound", 1472, 2088, 0, 4),
    # The red gate's closets in the bunker's front: behind the player.
    ("closet_z1_a", "trooper", 2080, 656, 270, 2),
    ("closet_z1_a", "stormtrooper", 2144, 656, 270, 3),
    ("closet_z1_b", "trooper", 2272, 656, 270, 2),
    ("closet_z1_b", "trooper", 2336, 656, 270, 4),
    # The harbour, the last fight: both factions on the quay, the heavy by
    # the gangway, Doughboys over the open water, a watch on the deck.
    ("z9_quay", "panzermensch", 960, 1472, 270, 2),
    ("z9_quay", "stormtrooper", 896, 0, 0, 2),
    ("z9_quay", "stormtrooper", 1024, 640, 0, 2),
    ("z9_quay", "trooper", 960, -128, 90, 2),
    ("z9_quay", "rifleman", 864, 1216, 0, 2),
    ("z10_sea", "doughboy", 128, 768, 0, 2),
    ("z11_deck", "rifleman", 384, 1152, 270, 2),
    ("z9_quay", "heavy", 960, 896, 270, 3),
    ("z9_quay", "stormtrooper", 1088, 1344, 180, 3),
    ("z10_sea", "doughboy", 608, 1600, 270, 3),
    ("z11_deck", "trooper", 384, 448, 90, 3),
    ("z8_road", "trooper", 1344, 224, 0, 4),
    ("z9_quay", "hound", 960, 320, 0, 4),
    ("z9_quay", "stormtrooper", 1024, 1600, 270, 4),
    ("z10_sea", "doughboy", 128, 128, 0, 4),
    ("z11_deck", "stormtrooper", 448, 1024, 270, 4),
    # At the quay's south end, by the kerb, the whole quay north down his
    # sights; on the deck by the hull's edge from skill 3, down the boat.
    ("z9_quay", "gunner", 1056, -192, 90, 2),
    ("z11_deck", "gunner", 320, 1216, 270, 3),
    # V3 (A3): the warehouse behind the road's snowbank, open when the
    # medikit under the broken floodlight is taken: from the quay.
    ("z8_snowbank_pocket", "rifleman", 1312, 544, 270, 2),
    ("z8_snowbank_pocket", "rifleman", 1376, 544, 270, 3),
    ("z8_snowbank_pocket", "trooper", 1344, 584, 270, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest
# skill tier it appears on - 4 = every skill, 3 = medium and easier, 2 =
# easy only). Weapons are on every skill.
ITEMS = (
    # The weapons, on every skill, on the route, each before the fight it is
    # for: the IZh by the plane, the PPSh in the hangar, the RPG-7 in the
    # barracks (before the radome's Panzermensch), the ROKS-3 in the command
    # room (for the bunker's corridors).
    ("z1_runway", ED_IZH, 3520, 160, 4),
    ("z2_hangar", ED_PPSH, 3712, 1024, 4),
    # The AKM (D116) in the hangar's racks, after the PPSh, before the RPG-7:
    # episode 3 can be started here with the pistol (D104), so it is on the
    # route even for whoever took one at the Volga dam.
    ("z2_hangar", ED_AKM, 4032, 768, 4),
    ("z4_barracks", ED_RPG7, 3648, 2144, 4),
    ("z6_command", ED_ROKS3, 3008, 1072, 4),
    # Stimpacks.
    ("z1_runway", ED_STIMPACK, 3776, 96, 4),
    ("z2_hangar", ED_STIMPACK, 3520, 1088, 4),
    ("z4_barracks", ED_STIMPACK, 4032, 1792, 4),
    ("z5_radome", ED_STIMPACK, 3104, 1760, 4),
    ("z7_hall", ED_STIMPACK, 1600, 1792, 4),
    ("z9_quay", ED_STIMPACK, 832, 768, 4),
    ("z2_hangar", ED_STIMPACK, 4288, 832, 3),
    ("z7_chamber", ED_STIMPACK, 1600, 1984, 3),
    ("z9_quay", ED_STIMPACK, 1088, 1472, 3),
    ("z5_radome", ED_STIMPACK, 3104, 1792, 2),
    ("z9_quay", ED_STIMPACK, 832, 192, 2),
    # Medikits.
    ("z4_barracks", ED_MEDIKIT, 4032, 2144, 4),
    ("z6_command", ED_MEDIKIT, 2752, 1184, 4),
    ("z7_escape_top", ED_MEDIKIT, 1856, 640, 4),
    ("z8_snowbank_lamp", ED_MEDIKIT, *MEDIKIT_SPOT, 4),   # V3: the snowbank's bait, under the floodlight
    ("z9_quay", ED_MEDIKIT, 1088, 1536, 4),
    ("z5_dome", ED_MEDIKIT, 2368, 1728, 3),
    ("z9_quay", ED_MEDIKIT, 832, 0, 3),
    # Armour: the flak vest in the hangar (for the radome), the heavy vest at
    # the top of the escape stair (for the closets and the harbour); plates
    # at the locks and the keys' rooms.
    ("z2_hangar", ED_GREEN_ARMOR, 4224, 1088, 4),
    ("z7_escape_top", ED_BLUE_ARMOR, 1888, 640, 4),
    ("z2_yellow_portal", ED_ARMOR_BONUS, 3424, 992, 4),
    ("z2_yellow_portal", ED_ARMOR_BONUS, 3424, 1056, 4),
    ("z1_runway", ED_ARMOR_BONUS, 1728, 192, 4),
    ("z1_runway", ED_ARMOR_BONUS, 1728, 384, 4),
    ("z5_balcony", ED_ARMOR_BONUS, 3104, 1888, 4),
    ("z5_balcony", ED_ARMOR_BONUS, 3104, 2080, 4),
    ("z7_chamber", ED_ARMOR_BONUS, 1984, 1984, 3),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z1_ramp_porch", ED_HEALTH_BONUS, 4368, 304, 4),
    ("z2_lenin_niche", ED_HEALTH_BONUS, 4360, 1024, 4),
    ("z4_lockers_w", ED_HEALTH_BONUS, 3648, 2184, 4),
    ("z5_dome", ED_HEALTH_BONUS, 2688, 2400, 4),
    ("z7_passage", ED_HEALTH_BONUS, 1792, 1888, 4),
    ("z9_shed", ED_HEALTH_BONUS, 1248, 1152, 4),
    ("z9_shed", ED_HEALTH_BONUS, 1248, 1216, 4),
    ("z11_gangway", ED_HEALTH_BONUS, 640, 992, 4),
    ("z12_sail", ED_HEALTH_BONUS, 352, 800, 4),
    # The RGD-5 (V3 A4): Episode 3 is a pistol start, so the pouch again,
    # in the hangar; loose ones in the barracks, among the bunks.
    ("z2_hangar", ED_RGD5, 3900, 1000, 4),
    ("z4_barracks", ED_RGD5_AMMO, 3800, 1950, 3),
    ("z4_barracks", ED_RGD5_AMMO, 4150, 1950, 2),
)

# The barracks' radio (V3 B5): (zone, x, y, lines, reach, flags, jingle),
# as MAP04's. Far from Moscow: the dam's victory, the lore's line, the
# factory-fortress and the time signal. The actor's reach (384) in a hall
# 896 x 448. Olive (D132): the test site's army barracks.
LOUDSPEAKERS = (
    ("z4_barracks", 3904, 1952, (2, 7, 13, 16), 0, LOUDSPEAKER_FLAG_OLIVE, 0),
)

# D119 (the CEO's playtest: "siempre sale de sobras", "siempre acabas con la
# escopeta"): the route's ammunition, kept apart from ITEMS because it no
# longer scales DOWN with skill. It scales with the monsters it pays for,
# like them: (zone, editor number, x, y, LOWEST skill tier it appears on -
# 2 = every skill, 3 = medium and harder, 4 = hard only). So each skill's
# stock sits in its own G3-8 band (docs/engine/BALANCE.md, D119: 1.5-2.0 /
# 1.3-1.6 / 1.2-1.45 on skills 2 / 3 / 4), shells are at most ~35 % of the
# damage, and the rest follows the weapons the player holds at each stage,
# the newest first: the AKM's magazines lead, then PG-7V, the PPSh's rounds,
# and fuel sparingly (the ROKS-3 is being toned down).
AMMO = (
    # The runway, the hangar, the tunnel, the barracks and the radome (the
    # IZh, the PPSh, the AKM and the RPG-7 all found here): the AKM's
    # magazines lead, PG-7V the strong second (at most 30 % of a stage's
    # damage outside a boss's, BALANCE 8.4.2).
    ("z1_runway", ED_SHELLS, 3584, 448, 2),
    ("z2_hangar", ED_CLIP_BOX, 4288, 1088, 2),
    ("z2_hangar", ED_AKM_MAG, 3904, 832, 2),
    ("z4_barracks", ED_AKM_MAG, 3584, 2016, 2),
    ("z4_barracks", ED_ROCKET, 3712, 2144, 2),
    ("z5_radome", ED_AKM_MAG, 2944, 1632, 2),
    ("z4_barracks", ED_SHELLS, 3520, 1792, 3),
    ("z5_dome", ED_ROCKET_BOX, 3040, 2400, 3),
    ("z3_tunnel_n", ED_AKM_MAG, 3872, 1408, 3),
    ("z5_radome", ED_AKM_MAG, 3008, 1600, 4),
    ("z1_runway", ED_SHELLS, 3648, 448, 4),
    # The command room (the ROKS-3 and its own 40): two magazines, so the
    # AKM still leads its fuel.
    ("z6_command", ED_AKM_MAG, 3200, 1184, 2),
    ("z6_command", ED_AKM_MAG, 3072, 1072, 2),
    ("z6_command", ED_SHELLS, 2752, 1280, 3),
    # The bunker.
    ("z7_hall", ED_AKM_MAG, 1856, 1216, 2),
    ("z7_hall", ED_AKM_MAG, 1600, 1216, 2),
    ("z7_flight2_4", ED_SHELLS, 2192, 1216, 2),
    ("z7_hall", ED_CLIP_BOX, 2016, 1216, 2),
    ("z7_escape_top", ED_ROCKET, 1824, 640, 2),
    ("z7_hall", ED_CELL, 2016, 1600, 3),
    ("z7_hall", ED_AKM_MAG, 1600, 1536, 4),
    ("z7_flight1_3", ED_AKM_MAG, 2512, 1216, 4),
    ("z7_hall", ED_ROCKET_BOX, 2016, 1408, 4),
    # The road and the harbour, the last fight.
    ("z8_road", ED_ROCKET, 1472, 192, 2),
    ("z8_road", ED_AKM_MAG, 1472, 384, 2),
    ("z9_quay", ED_AKM_MAG, 1024, 1408, 2),
    ("z9_quay", ED_AKM_MAG, 1088, 256, 2),
    ("z9_quay", ED_AKM_MAG, 832, 1088, 2),
    ("z9_quay", ED_CELL, 1088, 832, 2),
    ("z9_quay", ED_SHELLS, 1088, 1024, 2),
    ("z9_quay", ED_CLIP_BOX, 832, 512, 2),
    ("z9_quay", ED_ROCKET_BOX, 1088, 1152, 2),
    ("z9_quay", ED_AKM_MAG, 832, 1408, 3),
    ("z9_quay", ED_AKM_MAG, 1088, 704, 3),
    ("z9_quay", ED_SHELL_BOX, 960, 64, 3),
    ("z9_quay", ED_ROCKET_BOX, 960, 1216, 3),
    ("z9_quay", ED_AKM_MAG, 1088, 1600, 4),
    ("z9_quay", ED_AKM_MAG, 832, -192, 4),
    ("z9_quay", ED_CLIP_BOX, 960, 1408, 4),
)

# The secrets' rewards, on every skill (MAP01's rule); kept out of ITEMS,
# which is the route's.
SECRET_ITEMS = (
    # S1, the Il-14's hold: what the crew flew in.
    ("s1_hold", ED_SHELL_BOX, 4224, 304, 4),
    ("s1_hold", ED_MEDIKIT, 4288, 288, 4),
    ("s1_hold", ED_CLIP_BOX, 4288, 320, 4),
    # S2, the commissar's store behind the lockers.
    ("s2_store", ED_ROCKET_BOX, 4096, 2368, 4),
    ("s2_store", ED_STIMPACK, 4192, 2368, 4),
    ("s2_store", ED_SHELL_BOX, 4288, 2368, 4),
    # S3, the shut shed on the quay: the Hand Katyusha, for the last fight,
    # and a canister towards a second volley.
    ("s3_shed", ED_HAND_KATYUSHA, 1280, 1504, 4),
    ("s3_shed", ED_CELL, 1216, 1440, 4),
    ("s3_shed", ED_CELL, 1216, 1568, 4),
)


def pickup_special(ednum: int, spot: tuple[int, int]) -> dict:
    """The UDMF `special` and `arg0..` of the thing `ednum` at `spot`, if
    an event of PICKUP_EVENTS rides it (MAP04's form); else nothing."""
    for event in PICKUP_EVENTS:
        if (event.trigger, tuple(event.spot)) == (ednum, tuple(spot)):
            return {"special": event.special, **{f"arg{i}": a for i, a in enumerate(event.args)}}
    return {}


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
    MAP02's and MAP03's helper, repeated so each map stays one file."""
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


BLOCKING = LineStyle(flags=("blocking",))   # a kerb's or the pack ice's edge: nobody crosses it
# A control board's face: impassable (the board is a picture on a two-sided
# line), lower-unpegged so its middle texture stands on the floor.
BOARD_EDGE = LineStyle(flags=("blocking",), peg_bottom=True)


def hang(tm: TextMap, segment: tuple[int, int, int, int], room: int, texture: str) -> None:
    """Hang a middle texture on the two-sided line `segment`, on its face
    towards `room` (MAP03's and MAP05's helper, repeated so each map stays
    one file). Doom draws a two-sided middle texture once, never tiled
    downwards: with `dontpegbottom`, its foot on the higher of the floors."""
    x1, y1, x2, y2 = segment
    ends = {(float(x1), float(y1)), (float(x2), float(y2))}
    for ld in tm.linedefs:
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        if ld.sideback is None or {(float(a.x), float(a.y)), (float(b.x), float(b.y))} != ends:
            continue
        for side in (ld.sidefront, ld.sideback):
            if tm.sidedefs[side].sector == room:
                tm.sidedefs[side].texturemiddle = texture
                return
    raise ValueError(f"no two-sided line {segment} facing sector {room}")


def drawn_parts(tm: TextMap, ld, side: int, other: int | None) -> list[tuple[str, int]]:
    """The parts of sidedef `side` the engine draws, each with the height
    Doom pegs its texture to (MAP05's helper): a one-sided wall to its floor
    (lower-unpegged) or ceiling; a lower texture to the higher floor (or,
    lower-unpegged, to its own ceiling); an upper texture to the lower
    ceiling (or, upper-unpegged, to its own). Between two skies, nothing."""
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
    """Peg every drawn face of the lumps in `bases` to one grid: the
    texture's foot on the height `bases` names and every WALL_TILE above and
    below it (MAP05's helper): SDDAM2's tide mark sits on the sea, the
    consoles show SDCTRL1's desk. `sectors` limits it to the faces seen from
    those sectors."""
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
    """SDDAM2 on every face that rises out of the sea onto the quay or a
    step: the lower texture of the side standing in the water."""
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for low, high in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            ls, hs = tm.sidedefs[low].sector, tm.sidedefs[high].sector
            if ls in water and hs in banks and tm.sectors[hs].heightfloor > tm.sectors[ls].heightfloor:
                tm.sidedefs[low].texturebottom = DAM_WET


def dress_lower(tm: TextMap, room: int, neighbours: set[int], texture: str) -> None:
    """`texture` on the lower part of every side of `room` that faces one of
    `neighbours`: the flank of a raised floor seen from inside `room`."""
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for near, far in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            if tm.sidedefs[near].sector == room and tm.sidedefs[far].sector in neighbours:
                tm.sidedefs[near].texturebottom = texture


def corner_chamfers(rect: tuple[int, int, int, int]) -> list[tuple[int, int, int, int]]:
    """The stepped corners that make the radome's square an octagon."""
    x1, y1, x2, y2 = rect
    out = []
    for w, h in CHAMFER:
        out += [(x1, y1, x1 + w, y1 + h), (x2 - w, y1, x2, y1 + h),
                (x1, y2 - h, x1 + w, y2), (x2 - w, y2 - h, x2, y2)]
    return out


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
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

    def door(name: str, floor: int, tag: int, rect, *, light: int, wall: str = STEEL) -> int:
        """A closed door sector; its own walls are the steel track."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=wall)

    def prop(room: str, name: str, rect, top: int, wall: str, flat: str = PLATE) -> int:
        """A solid block standing in `room`, `top` high: unwalkable."""
        s = tm.sectors[plan[room]]
        return zone(f"{PROP_PREFIX}{name}", s.heightfloor + top, s.heightceiling, [rect],
                    light=s.lightlevel, flat=flat, ceiling=s.textureceiling, wall=wall)

    def closet(name: str, door_rect, room_rect, tag: int, floor: int, *, leaf: str) -> int:
        """A monster closet (MAP01 v3's, MAP05's): a panel in a wall that
        opens for good with the lock that owns `tag`, wearing the wall it is
        cut into, so it is wall until it moves; a dead end walked out of."""
        door_index = zone(f"{name}_door", floor, floor, [door_rect], tag, light=LIGHT_CLOSET, wall=leaf)
        zone(name, floor, floor + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

    def rim(name: str, rect, floor: int, sky_over: int, wall: str, flat: str) -> int:
        """Doom's open-air trick (MAP05's parapets): a strip whose sky ceiling
        stands just over its floor, so beyond it the sky, never a wall."""
        return zone(f"{PROP_PREFIX}{name}", floor, sky_over, [rect], light=LIGHT_OUTDOORS,
                    flat=flat, ceiling=SKY, wall=wall)

    # ======================================================================
    # The runway: the Il-14, the red gate at the far end
    # ======================================================================
    zone("z1_runway", GROUND, SKY_CEIL, [RUNWAY], light=LIGHT_OUTDOORS, flat=RUNWAY_SLABS, ceiling=SKY,
         wall=CONCRETE, extra=RUNWAY_TURN)
    like("z1_runway", "z1_centreline", [CENTRELINE], flat=RUNWAY_LINE, extra=RUNWAY_TURN)
    for key, rect in KERBS.items():
        rim(f"z1_kerb_{key}", rect, GROUND + KERB, GROUND + KERB_SKY, ICE_WALL, SNOW)
    for n, rect in enumerate(WINGS, start=1):
        prop("z1_runway", f"z1_wing_{n}", rect, WING, STEEL)
    for n, rect in enumerate(NACELLES, start=1):
        prop("z1_runway", f"z1_nacelle_{n}", rect, NACELLE, STEEL)
    for n, rect in enumerate(TAILPLANES, start=1):
        prop("z1_runway", f"z1_tailplane_{n}", rect, TAILPLANE, STEEL)
    prop("z1_runway", "z1_fuselage", FUSELAGE_RECT, FUSELAGE, STEEL)
    # S1: the hold, behind the cargo ramp under the tail.
    zone("s1_hold", GROUND, ROOF, [S1_HOLD], light=LIGHT_SECRET, flat=PLATE, ceiling=PLATE,
         wall=STEEL, special=SECTOR_SPECIAL_SECRET)
    s1_panel = zone("s1_panel", GROUND, GROUND, [S1_PANEL], TAG_S1_PANEL, light=LIGHT_SECRET, wall=STEEL)
    zone("z1_ramp_porch", GROUND, ROOF, [RAMP_PORCH], light=LIGHT_OUTDOORS, flat=RUNWAY_SLABS, ceiling=PLATE,
         wall=STEEL, extra=RUNWAY_TURN)
    prop("z1_runway", "z1_tanker", TANKER_RECT, TANKER_TOP, TANKER)
    for n, rect in enumerate(RUNWAY_CRATES, start=1):
        prop("z1_runway", f"z1_crates_{n}", rect, CRATES, CRATE, flat=CRATE_TOP)
    # The gatehouse's red gate and the Soviet flags beside it.
    zone("z1_red_portal", GROUND, ROOF, [RED_PORTAL], light=LIGHT_BEACON, ceiling=CEIL_PANEL,
         wall=BRICK, extra=RED_LIGHT)
    red_gate = door("z13_red_gate", GROUND, TAG_RED_GATE, RED_GATE, light=LIGHT_OUTDOORS)
    for texture, rect in FLAG_RECESSES.items():
        zone(f"z1_flag_{texture.lower()}", GROUND, GROUND + DOOR_TILE, [rect], light=LIGHT_OUTDOORS,
             wall=BRICK)
        g.style_v(rect[0], rect[1], rect[3], LineStyle(texture=texture))
    # The bunker's block: the escape stair's shutter, the closets.
    runway_shutter = door("shutter_runway", GROUND, TAG_RUNWAY_SHUTTER, RUNWAY_SHUTTER, light=LIGHT_TUNNEL)
    for name, (door_rect, room_rect) in RUNWAY_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_RUNWAY_AMBUSH, GROUND, leaf=CONCRETE)

    # ======================================================================
    # The hangar
    # ======================================================================
    zone("z1_d1_porch", GROUND, ROOF, [D1_OUT], light=LIGHT_OUTDOORS, flat=SNOW, ceiling=CEIL_PANEL, wall=RUST)
    d1 = door("d1_hangar", GROUND, TAG_D1_HANGAR, D1_DOOR, light=LIGHT_HANGAR)
    zone("z2_hangar", GROUND, HANGAR_CEIL, [HANGAR], light=LIGHT_HANGAR, ceiling=CEIL_PANEL, wall=RUST)
    like("z2_hangar", "z2_d1_porch", [D1_IN], ceil=ROOF)
    like("z2_hangar", "z2_d2_porch", [D2_PORCH], ceil=ROOF)
    zone("z2_yellow_portal", GROUND, ROOF, [YELLOW_PORTAL], light=LIGHT_BEACON, ceiling=CEIL_PANEL,
         wall=STEEL, extra=YELLOW_LIGHT)
    yellow_door = door("yellow_door", GROUND, TAG_YELLOW_DOOR, YELLOW_DOOR, light=LIGHT_COMMAND)
    like("z2_hangar", "z2_lenin_niche", [LENIN_NICHE], ceil=GROUND + POSTER_HEIGHT, ceiling=CEIL_CONCRETE)
    for n, rect in enumerate(HANGAR_CRATES, start=1):
        prop("z2_hangar", f"z2_crates_{n}", rect, CRATES, CRATE, flat=CRATE_TOP)
    prop("z2_hangar", "z2_airframe", AIRFRAME_RECT, AIRFRAME, STEEL)
    for name, (door_rect, room_rect) in HANGAR_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_HANGAR_AMBUSH, GROUND, leaf=RUST)
    d2 = door("d2_tunnel", GROUND, TAG_D2_TUNNEL, D2_DOOR, light=LIGHT_TUNNEL)

    # ======================================================================
    # The covered tunnels and the barracks
    # ======================================================================
    zone("z3_tunnel_n", GROUND, ROOF, [TUNNEL_N], light=LIGHT_TUNNEL, wall=TUNNEL)
    zone("z4_barracks", GROUND, BARRACKS_CEIL, [BARRACKS], light=LIGHT_BARRACKS, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=CONCRETE_STRIPE)
    for n, rect in enumerate(BUNKS, start=1):
        prop("z4_barracks", f"z4_bunk_{n}", rect, BUNK, STEEL)
    for name, rect in LOCKER_ALCOVES.items():
        like("z4_barracks", name, [rect], ceil=GROUND + DOOR_TILE, wall=LOCKER)
    like("z4_barracks", f"{PROP_PREFIX}z4_mural_niche", [RED_CORNER_NICHE], floor=GROUND + MURAL_SILL)
    zone("s2_niche", GROUND, GROUND + DOOR_TILE, [S2_NICHE], light=LIGHT_SHADOW, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=LOCKER)
    s2_panel = zone("s2_panel", GROUND, GROUND, [S2_PANEL], TAG_S2_PANEL, light=LIGHT_SHADOW, wall=LOCKER)
    zone("s2_passage", GROUND, ROOF, [S2_PASSAGE], light=LIGHT_SECRET, wall=CONCRETE)
    zone("s2_store", GROUND, ROOF, [S2_STORE], light=LIGHT_SECRET, wall=CONCRETE,
         special=SECTOR_SPECIAL_SECRET)
    ty1, ty2 = TUNNEL_W_Y
    for n in range(1, TUNNEL_W_STEPS + 1):
        x = TUNNEL_W_X0 - STEP_RUN * n
        f = GROUND + STEP * n
        zone(f"z3_stair_{n}", f, f + DOOR_HEIGHT, [(x, ty1, x + STEP_RUN, ty2)], light=LIGHT_TUNNEL,
             wall=TUNNEL)

    # ======================================================================
    # The radome: the gallery, the antenna's platform, the dish
    # ======================================================================
    zone("z5_radome", GROUND, RADOME_CEIL, [RADOME], light=LIGHT_RADOME, ceiling=CEIL_CONCRETE,
         wall=RADOME_SKIN)
    like("z5_radome", "z5_dome", [DOME], ceil=DOME_CEIL)
    zone("z5_dish", GROUND, DISH_CEIL, [DISH], light=LIGHT_DISH, ceiling=GRATING, wall=STEEL)
    zone("z5_platform", GALLERY, DISH_CEIL, [PLATFORM], light=LIGHT_DISH, flat=GRATING, ceiling=GRATING,
         wall=STEEL)
    zone("z5_key_pad", GALLERY + PAD, DISH_CEIL, [KEY_PAD], light=LIGHT_BEACON, flat=PLATE, ceiling=GRATING,
         wall=STEEL, extra=YELLOW_LIGHT)
    sx1, sx2 = PLATFORM_STAIR_X
    for n in range(1, PLATFORM_STAIR_STEPS + 1):
        y1 = PLATFORM[1] - STEP_RUN * (PLATFORM_STAIR_STEPS + 1 - n)
        ceil = DISH_CEIL if y1 >= DISH[1] else DOME_CEIL
        zone(f"z5_stair_{n}", GROUND + STEP * n, ceil, [(sx1, y1, sx2, y1 + STEP_RUN)], light=LIGHT_DISH,
             flat=GRATING, ceiling=GRATING if ceil == DISH_CEIL else CEIL_CONCRETE, wall=STEEL)
    zone("z5_balcony", GALLERY, RADOME_CEIL, [BALCONY], light=LIGHT_RADOME, flat=PLATE, wall=STEEL)
    bx1, bx2 = BALCONY_STAIR_X
    for n in range(1, BALCONY_STAIR_STEPS + 1):
        y1 = BALCONY[3] + STEP_RUN * (n - 1)
        zone(f"z5_gallery_stair_{n}", GALLERY - STEP * n, RADOME_CEIL, [(bx1, y1, bx2, y1 + STEP_RUN)],
             light=LIGHT_RADOME, flat=PLATE, wall=STEEL)
    for rect in corner_chamfers(RADOME):
        g.carve(*rect)
    g.carve(*PEDESTAL)
    # V3 (A3): the radar's cargo lift. The gate is a door high in the
    # radome's wall, its lamp flickering; the car waits up at the gallery's
    # height, its steel face under the gate's lintel, until the yellow key.
    zone("z5_lift_gate", GROUND, ROOF, [RADAR_LIFT_GATE], light=LIGHT_EVENT_LAMP, ceiling=CEIL_PANEL,
         wall=RADOME_SKIN, special=SECTOR_SPECIAL_LIGHT_FLICKER)
    zone("z5_lift_car", GALLERY, GALLERY + DOOR_HEIGHT, [RADAR_LIFT_CAR], TAG_RADAR_LIFT, light=LIGHT_CLOSET,
         flat=PLATE, ceiling=PLATE, wall=STEEL)

    # ======================================================================
    # The command room, behind the yellow door
    # ======================================================================
    zone("z6_command", GROUND, COMMAND_CEIL, [COMMAND], light=LIGHT_COMMAND, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=TILE)
    zone("z6_porch", GROUND, ROOF, [COMMAND_PORCH], light=LIGHT_COMMAND, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=STEEL)
    for n, rect in enumerate(CONSOLES, start=1):
        prop("z6_command", f"z6_console_{n}", rect, CONSOLE, CONTROL_PANEL)
    prop("z6_command", "z6_map_table", MAP_TABLE, CONSOLE, STEEL)
    for name, (rect, _face) in CONTROL_BOARDS.items():
        like("z6_command", name, [rect])
    zone("z6_swa_niche", GROUND, GROUND + SWITCH_HEIGHT, [SWA_NICHE], light=LIGHT_COMMAND,
         flat=FLOOR_TILE, wall=STEEL)
    zone("z6_shutter_porch", GROUND, ROOF, [SHUTTER_PORCH], light=LIGHT_COMMAND, flat=FLOOR_TILE,
         wall=STEEL)
    bunker_shutter = door("shutter_bunker", GROUND, TAG_BUNKER_SHUTTER, BUNKER_SHUTTER, light=LIGHT_TUNNEL)

    # ======================================================================
    # The bunker: two flights down, the hall, the test chamber, the escape
    # ======================================================================
    ky1, ky2 = BUNKER_STAIR_Y
    zone("z7_stair_top", GROUND, ROOF, [STAIR_TOP], light=LIGHT_TUNNEL, wall=TUNNEL)
    x = STAIR_TOP[0]
    floor = GROUND
    for n in range(1, FLIGHT_STEPS + 1):
        floor -= STEP
        zone(f"z7_flight1_{n}", floor, floor + DOOR_HEIGHT, [(x - STEP_RUN, ky1, x, ky2)],
             light=LIGHT_TUNNEL, wall=TUNNEL)
        x -= STEP_RUN
    floor -= STEP
    assert x == BUNKER_LANDING[2], x
    zone("z7_landing", floor, floor + DOOR_HEIGHT, [BUNKER_LANDING], light=LIGHT_TUNNEL, wall=TUNNEL)
    x = BUNKER_LANDING[0]
    for n in range(1, FLIGHT_STEPS + 1):
        floor -= STEP
        zone(f"z7_flight2_{n}", floor, floor + DOOR_HEIGHT, [(x - STEP_RUN, ky1, x, ky2)],
             light=LIGHT_BUNKER, wall=TUBBING)
        x -= STEP_RUN
    floor -= STEP
    assert floor == BUNKER and x == BUNKER_HALL[2], (floor, x)
    zone("z7_hall", BUNKER, BUNKER_CEIL, [BUNKER_HALL], light=LIGHT_BUNKER, flat=PLATE, wall=TUBBING)
    like("z7_hall", "z7_lamp", [LAMP], light=LIGHT_LAMP, ceiling=CEIL_PANEL,
         special=SECTOR_SPECIAL_LIGHT_FLICKER)
    for rect in PILLARS:
        g.carve(*rect)
    zone("z7_passage", BUNKER, BUNKER + DOOR_HEIGHT, [PASSAGE], light=LIGHT_BUNKER, flat=PLATE, wall=HAZARD)
    zone("z7_chamber", BUNKER, BUNKER_CEIL, [CHAMBER], light=LIGHT_CHAMBER, flat=PLATE, wall=TUBBING)
    zone("z7_key_plinth", BUNKER + PAD, BUNKER_CEIL, [KEY_PLINTH], light=LIGHT_BEACON, flat=PLATE,
         wall=STEEL, extra=RED_LIGHT)
    zone(f"{PROP_PREFIX}z7_core", CORE_SILL, CORE_SILL + DOOR_TILE, [CORE_SLOT], light=LIGHT_CORE,
         flat=PLATE, wall=STEEL)
    # V3 (A2): the containment cells behind the chamber's west wall; each
    # wall panel's floor stands at the chamber's ceiling until the red key.
    for name, (wall_rect, cell_rect, lamp_rect) in BUNKER_CELLS.items():
        like("z7_chamber", f"{name}_lamp", [lamp_rect], light=LIGHT_EVENT_LAMP,
             special=SECTOR_SPECIAL_LIGHT_FLICKER)
        zone(f"{name}_wall", BUNKER_CEIL, BUNKER_CEIL, [wall_rect], TAG_BUNKER_CELLS, light=LIGHT_CLOSET,
             flat=PLATE, wall=TUBBING)
        zone(name, BUNKER, BUNKER + CELL_HEIGHT, [cell_rect], light=LIGHT_CLOSET, flat=PLATE, wall=TUBBING)
    ex1, ex2 = ESCAPE_X
    y = ESCAPE_TOP[3]
    for n in range(1, ESCAPE_STEPS + 1):
        f = GROUND - STEP * n
        zone(f"z7_escape_{n}", f, f + DOOR_HEIGHT, [(ex1, y, ex2, y + STEP_RUN)], light=LIGHT_BUNKER,
             wall=TUBBING)
        y += STEP_RUN
    assert y == BUNKER_HALL[1], y
    zone("z7_escape_top", GROUND, ROOF, [ESCAPE_TOP], light=LIGHT_TUNNEL, wall=CONCRETE)
    zone("z7_swb_niche", GROUND, GROUND + SWITCH_HEIGHT, [SWB_NICHE], light=LIGHT_TUNNEL, wall=STEEL)

    # ======================================================================
    # The harbour: the road, the quay and its sheds, the sea, the submarine
    # ======================================================================
    zone("z8_gate_porch", GROUND, ROOF, [GATE_PORCH], light=LIGHT_OUTDOORS, flat=SNOW, ceiling=CEIL_PANEL,
         wall=BRICK)
    zone("z8_road", GROUND, SKY_CEIL, [ROAD], light=LIGHT_OUTDOORS, flat=SNOW, ceiling=SKY, wall=WAREHOUSE)
    # V3 (A3): the snowbank against a warehouse's front, the broken
    # floodlight's patch before it; the medikit taken, the bank sinks.
    like("z8_road", "z8_snowbank_lamp", [SNOWBANK_LAMP], light=LIGHT_EVENT_LAMP,
         special=SECTOR_SPECIAL_LIGHT_FLICKER)
    zone("z8_snowbank", SNOWBANK_TOP, SKY_CEIL, [SNOWBANK], TAG_SNOWBANK, light=LIGHT_OUTDOORS, flat=SNOW,
         ceiling=SKY, wall=WAREHOUSE)
    zone("z8_snowbank_pocket", GROUND, ROOF, [SNOWBANK_POCKET], light=LIGHT_SHED, ceiling=CEIL_CONCRETE,
         wall=WAREHOUSE)
    zone("z9_quay", GROUND, SKY_CEIL, [QUAY], light=LIGHT_OUTDOORS, flat=SNOW, ceiling=SKY, wall=WAREHOUSE)
    for key, rect in QUAY_KERBS.items():
        rim(f"z9_kerb_{key}", rect, GROUND + KERB, GROUND + KERB_SKY, ICE_WALL, SNOW)
    # The two sheds alike inside (S3's comparison): frosted corrugated sheet.
    zone("z9_shed", GROUND, ROOF, [SHED], light=LIGHT_SHED, wall=HUT)
    zone("z9_shed_doorway", GROUND, ROOF, [SHED_DOORWAY], light=LIGHT_SHED, wall=WAREHOUSE)
    zone("z9_shed_porch", GROUND, ROOF, [SHED_PORCH], light=LIGHT_OUTDOORS, flat=SNOW, wall=WAREHOUSE)
    zone("s3_shed", GROUND, ROOF, [S3_SHED], light=LIGHT_SHED, wall=HUT, special=SECTOR_SPECIAL_SECRET)
    s3_panel = zone("s3_panel", GROUND, GROUND, [S3_PANEL], TAG_S3_PANEL, light=LIGHT_SHED, wall=WAREHOUSE)
    zone("z9_s3_porch", GROUND, ROOF, [S3_PORCH], light=LIGHT_OUTDOORS, flat=SNOW, wall=WAREHOUSE)
    # The sheds' fronts either side of the doorway and the panel are solid.
    for (dy1, dy2), (_x1, hy1, _x2, hy2) in (((SHED_DOORWAY[1], SHED_DOORWAY[3]), SHED),
                                           ((S3_PANEL[1], S3_PANEL[3]), S3_SHED)):
        g.carve(SHED_FRONT_X, hy1, SHED_FRONT_X + NICHE_DEPTH, dy1)
        g.carve(SHED_FRONT_X, dy2, SHED_FRONT_X + NICHE_DEPTH, hy2)
    zone("z10_sea", SEA, SKY_CEIL, [SEA_RECT], light=LIGHT_SEA, flat=WATER, ceiling=SKY, wall=DAM,
         extra=WATER_HURTS)
    for key, rect in PACK_ICE.items():
        zone(f"{PROP_PREFIX}z10_ice_{key}", ICE_LIP, ICE_SKY, [rect], light=LIGHT_SEA, flat=SEA_ICE,
             ceiling=SKY, wall=ICE_WALL)
    for n, rect in enumerate(FLOES, start=1):
        zone(f"z10_floe_{n}", ICE_LIP, SKY_CEIL, [rect], light=LIGHT_SEA, flat=SEA_ICE, ceiling=SKY,
             wall=ICE_WALL)
    for k, (sy1, sy2) in enumerate(SEA_STEPS_Y, start=1):
        for n in range(1, 4):      # three steps up the quay wall
            x0 = QUAY[0] - STEP_RUN * (4 - n)
            zone(f"z10_steps_{k}_{n}", SEA + STEP * n, SKY_CEIL, [(x0, sy1, x0 + STEP_RUN, sy2)],
                 light=LIGHT_SEA, ceiling=SKY, wall=DAM)
    zone("z11_deck", DECK, SKY_CEIL, list(HULL), light=LIGHT_OUTDOORS, flat=DECK_RUBBER, ceiling=SKY,
         wall=HULL_SIDE)
    zone("z11_gangway", GROUND + STEP, SKY_CEIL, [GANGWAY], light=LIGHT_OUTDOORS, flat=PLATE, ceiling=SKY,
         wall=STEEL)
    zone(f"{PROP_PREFIX}z11_sail", SAIL_TOP, SKY_CEIL, [SAIL], light=LIGHT_OUTDOORS, flat=PLATE,
         ceiling=SKY, wall=HULL_SIDE)
    zone("z12_sail", DECK, SAIL_TOP, [SAIL_ROOM], light=LIGHT_SHED, flat=PLATE, ceiling=PLATE, wall=STEEL)
    d3 = door("d3_hatch", DECK, TAG_D3_HATCH, HATCH, light=LIGHT_SHED)
    zone("z11_hatch_porch", DECK, SAIL_TOP, [HATCH_PORCH], light=LIGHT_OUTDOORS, flat=DECK_RUBBER,
         ceiling=PLATE, wall=HULL_SIDE)
    zone("z12_exit_niche", DECK, DECK + SWITCH_HEIGHT, [EXIT_NICHE], light=LIGHT_BEACON, flat=PLATE,
         wall=STEEL)
    g.carve(SAIL[0], EXIT_NICHE[1], EXIT_NICHE[0], EXIT_NICHE[3])   # solid behind the switch

    # ======================================================================
    # Line styles. The FIRST rule registered on a segment wins, so the
    # specific ones (doors, panels, posters) come before the facades.
    # ======================================================================
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    # Manual doors, both faces.
    for sector, (x1, y1, x2, y2), horizontal, leaf in ((d1, D1_DOOR, True, DOOR), (d2, D2_DOOR, True, DOOR),
                                                        (d3, HATCH, False, BULKHEAD)):
        tag = tm.sectors[sector].identifier
        if horizontal:
            for yy in (y1, y2):
                g.style_h(yy, x1, x2, door_raise_style(tag, sector, texture=leaf))
        else:
            for xx in (x1, x2):
                g.style_v(xx, y1, y2, door_raise_style(tag, sector, texture=leaf))
    # The locks, both faces.
    for xx in (YELLOW_DOOR[0], YELLOW_DOOR[2]):
        g.style_v(xx, YELLOW_DOOR[1], YELLOW_DOOR[3],
                  locked_door_style(TAG_YELLOW_DOOR, yellow_door, LOCK_YELLOW_CARD, texture=DOOR_YELLOW))
    for xx in (RED_GATE[0], RED_GATE[2]):
        g.style_v(xx, RED_GATE[1], RED_GATE[3],
                  locked_door_style(TAG_RED_GATE, red_gate, LOCK_RED_CARD, texture=DOOR_RED))
    # The bunker's shutter: the hermetic door both sides, SW-A beside it.
    for xx in (BUNKER_SHUTTER[0], BUNKER_SHUTTER[2]):
        g.style_v(xx, BUNKER_SHUTTER[1], BUNKER_SHUTTER[3], remote_door_style(bunker_shutter, texture=BLAST_DOOR))
    g.style_v(SWA_NICHE[0], SWA_NICHE[1], SWA_NICHE[3],
              switch_door_open_style(TAG_BUNKER_SHUTTER, texture=SW_A_FACE, repeatable=False))
    # The escape stair's shutter: the hermetic door from the stair; from the
    # runway, the bunker block's own concrete (a shortcut found from behind).
    g.style_h(RUNWAY_SHUTTER[3], RUNWAY_SHUTTER[0], RUNWAY_SHUTTER[2],
              remote_door_style(runway_shutter, texture=BLAST_DOOR))
    g.style_h(RUNWAY_SHUTTER[1], RUNWAY_SHUTTER[0], RUNWAY_SHUTTER[2],
              remote_door_style(runway_shutter, texture=CONCRETE))
    g.style_v(SWB_NICHE[2], SWB_NICHE[1], SWB_NICHE[3],
              switch_door_open_style(TAG_RUNWAY_SHUTTER, texture=SW_B_FACE, repeatable=False))
    # The secrets' panels: the plane's ramp, the locker, the store's door.
    for xx in (S1_PANEL[0], S1_PANEL[2]):
        g.style_v(xx, S1_PANEL[1], S1_PANEL[3], secret_panel_style(TAG_S1_PANEL, s1_panel, RAMP))
    for yy in (S2_PANEL[1], S2_PANEL[3]):
        g.style_h(yy, S2_PANEL[0], S2_PANEL[2], secret_panel_style(TAG_S2_PANEL, s2_panel, LOCKER))
    for xx in (S3_PANEL[0], S3_PANEL[2]):
        g.style_v(xx, S3_PANEL[1], S3_PANEL[3], secret_panel_style(TAG_S3_PANEL, s3_panel, STORE_GATE))
    # The command room's boards: every edge of each strip impassable.
    for (x1, y1, x2, y2), _face in CONTROL_BOARDS.values():
        for xx in (x1, x2):
            g.style_v(xx, y1, y2, BOARD_EDGE)
        for yy in (y1, y2):
            g.style_h(yy, x1, x2, BOARD_EDGE)
    # The sealed core behind its slot, the cobalt animated (SDPORT1-4).
    g.style_h(CORE_SLOT[3], CORE_SLOT[0], CORE_SLOT[2], LineStyle(texture=CORE))
    # The conning tower's star and its number, once each.
    for (axis, coord, lo, hi), texture in ((SAIL_STAR, ARMOUR_STAR), (SAIL_NUMBER, HULL_NUMBER)):
        g.style_h(coord, lo, hi, LineStyle(texture=texture))
    # The facades on the runway: the hangar's corrugated front, the
    # gatehouse's brick at the west end (the Soviet flags hang on its pixels).
    g.style_h(RUNWAY[3], *HANGAR_FRONT_X, LineStyle(texture=RUST))
    g.style_v(RUNWAY[0], RUNWAY[1], RUNWAY[3], LineStyle(texture=BRICK))
    # The kerbs' and the pack ice's edges: nobody crosses them, not even
    # jumping (the open-air trick has the void a little beyond).
    for rect in KERBS.values():
        _block_edges(g, rect, RUNWAY)
    for rect in QUAY_KERBS.values():
        _block_edges(g, rect, QUAY)
    for rect in PACK_ICE.values():
        _block_edges(g, rect, SEA_RECT)
    # The exit: the switch at the back of its niche, in the conning tower.
    g.style_v(EXIT_NICHE[0], EXIT_NICHE[1], EXIT_NICHE[3], exit_switch_style(texture=EXIT_FACE))
    # V3: the snowbank's face towards the road is packed ice; its flanks in
    # the notch are the warehouse's brick, like the front either side.
    g.style_h(SNOWBANK[1], SNOWBANK[0], SNOWBANK[2], LineStyle(texture=ICE_WALL))

    g.build()

    # ======================================================================
    # Dressing the built lines: the waterline, the consoles, the boards
    # ======================================================================
    water = {plan["z10_sea"]} | {i for n, i in plan.items() if n.startswith("z10_steps_")}
    wet_the_banks(tm, water, water | {plan["z9_quay"]})
    align_to_world(tm, {DAM_WET: SEA})
    # The consoles, 32 high, show the board's desk (rows 64-95).
    align_to_world(tm, {CONTROL_PANEL: GROUND + CONSOLE + CONTROL_DESK_ROW}, sectors={plan["z6_command"]})
    for name, (_rect, (axis, coord, lo, hi)) in CONTROL_BOARDS.items():
        segment = (lo, coord, hi, coord) if axis == "h" else (coord, lo, coord, hi)
        hang(tm, segment, plan["z6_command"], BOARD_FACES[name])
    # Episode 3's walls on one grid each: the radome's panels from its floor
    # (whole tiles to the rim and the crown), the hull's deck edge on the deck
    # (and on the tower's top), the snowbanks' ice from the ground, the sea
    # ice's from the water.
    align_to_world(tm, {RADOME_SKIN: GROUND, HULL_SIDE: DECK})
    banks = {i for n, i in plan.items() if n.startswith((f"{PROP_PREFIX}z1_kerb_", f"{PROP_PREFIX}z9_kerb_"))}
    align_to_world(tm, {ICE_WALL: GROUND}, sectors=banks | {plan["z1_runway"], plan["z9_quay"]})
    ice = {i for n, i in plan.items() if n.startswith((f"{PROP_PREFIX}z10_ice_", "z10_floe_"))}
    align_to_world(tm, {ICE_WALL: SEA}, sectors=ice | water)
    # Inside the conning tower: the tower's own flank is its inner wall, so
    # the room round the exit wears the control-room panel, not the hull.
    dress_lower(tm, plan["z12_sail"], {plan[f"{PROP_PREFIX}z11_sail"]}, NAV_PANEL)

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START, angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD,
                       extra=pickup_special(ED_YELLOW_CARD, YELLOW_KEY_SPOT)))
    tm.add_thing(Thing(x=RED_KEY_SPOT[0], y=RED_KEY_SPOT[1], type=ED_RED_CARD,
                       extra=pickup_special(ED_RED_CARD, RED_KEY_SPOT)))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle))
    for _zone, ednum, x, y, top in ITEMS + SECRET_ITEMS:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top), extra=pickup_special(ednum, (x, y))))
    for _zone, ednum, x, y, lowest in AMMO:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(lowest)))
    for _zone, x, y, lines, reach, flags, jingle in LOUDSPEAKERS:
        mask = sum(1 << (line - 1) for line in lines)
        tm.add_thing(Thing(x=x, y=y, type=ED_LOUDSPEAKER,
                           extra={"arg0": mask, "arg1": reach, "arg3": flags, "arg4": jingle}))
    return tm, plan


def _block_edges(g: GridMap, rect: tuple[int, int, int, int], room: tuple[int, int, int, int]) -> None:
    """Flag `blocking` on the edges of the rim `rect` that touch `room`."""
    x1, y1, x2, y2 = rect
    rx1, ry1, rx2, ry2 = room
    lo, hi = max(x1, rx1), min(x2, rx2)
    if lo < hi:
        for yy in (y1, y2):
            if yy in (ry1, ry2):
                g.style_h(yy, lo, hi, BLOCKING)
    lo, hi = max(y1, ry1), min(y2, ry2)
    if lo < hi:
        for xx in (x1, x2):
            if xx in (rx1, rx2):
                g.style_v(xx, lo, hi, BLOCKING)


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
WALL_TEXTURES = ((CONCRETE, CONCRETE_STRIPE, STEEL, CRATE, LOCKER, TILE, TUNNEL, TUBBING, HAZARD, BRICK,
                  RUST, FLAG_USSR_1, FLAG_USSR_2, RAMP, CORE, DAM, DAM_WET, CONTROL_PANEL, TANKER,
                  ARMOUR_STAR, WAREHOUSE, STORE_GATE, LENIN, STALIN, MURAL,
                  ICE_WALL, RADOME_SKIN, HUT, RADAR, HULL_SIDE, HULL_NUMBER, NAV_PANEL)
                 + DOOR_LEAVES + SWITCH_FACES + MARX_ENGELS)
FLAT_TEXTURES = (FLOOR_CONCRETE, FLOOR_TILE, CEIL_PANEL, CEIL_CONCRETE, CRATE_TOP, PLATE,
                 GRATING, WATER, SNOW, RUNWAY_SLABS, RUNWAY_LINE, SEA_ICE, DECK_RUBBER)
BUILTIN_FLATS = (SKY,)
# Middle textures on two-sided lines, drawn once: the command room's boards.
MIDDLE_TEXTURES = (CONTROL_PANEL, RADAR)
# Still waiting, with nothing standing in (no installed lump is near enough).
PENDING_TEXTURES = {
    "SDAURO1": "the polar night's sky with the aurora (MAPINFO's sky1, scaffolding's): SKY1 meanwhile",
}
