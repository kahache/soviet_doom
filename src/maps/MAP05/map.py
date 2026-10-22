"""MAP05 «Волжская ГЭС» / Volga Dam - v1: the whole map, textured and populated.

Design document: docs/levels/MAP05-volga-dam.md (section 13 is this build).
Episode 2, «The Road to Moscow» (D104, P4), its second map: the Zhiguli
hydroelectric station on the Volga, November 1977, held by the Fourth Reich
and the Liberty Legion. Sergeant Vilanova arrives where MAP04 leaves him: in
the armoured train, at the dam's station on the east bank, level with the
crest; he leaves by the west bank's door at the far end of the crest.

Built MVP first (D60): complete and walkable from start to exit, both keys
on the route in plain sight on lit places in their lock's colour (MAP02's
lesson, D58), the population and the ammunition of G3-8's budget, three
secrets. Balance and light are later passes.

The route, in one line: the station (the BLUE GATE onto the crest seen at
once, shut) -> the gatehouse, D1 -> the inspection gallery, three flights
down inside the concrete -> the lower gallery -> the turbine hall (the
YELLOW DOOR seen high on the north catwalk) -> the spillway gallery -> the
spillway: the YELLOW KEY on the winch house across the water (the channel
hurts a little) -> back to the hall, up the catwalk stair, the yellow door
(and the catwalk's two closets) -> the control room, SW-A, which opens the
cable gallery -> up the cable gallery to the substation: the BLUE KEY on the
transformer pad, and SW-B, which opens a shutter straight back into the
station -> the blue gate (and the station's two closets) -> the crest,
westwards, the last fight -> D2, the west bank's door -> the exit switch.

Heights: the turbine hall is the ground (0); the catwalk and the control
room are at +192; the station, the substation and the crest at +384; the
spillway's channel at -64. The descent is three flights inside the dam, the
climb back one flight in the cable gallery: the dam is 384 high and the map
uses all of it.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.
Outdoors (station, spillway, substation, crest) the ceiling is F_SKY1, the
engine's sky marker (MAPINFO names SKY1 for MAP05). The parapets carry a
low sky ceiling (Doom's open-air trick): beyond them the sky, never a wall.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP05 SKILL=3 tools/run.sh
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

MAP_NAME = "MAP05"

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# The "Dam" set (tools/art/gen_dam.py) is approved and installed with the rest
# of episode 2 (25/25, D107) and is on the map. Design section 7.2 says where
# each piece went; `DAM_SET` below maps every lump the design proposed to the
# approved lump the map wears for it (a proposed name never drawn takes the
# nearest approved one).
DAM = "SDDAM1"           # 64x128 mass concrete, a lift joint every 64: the dam itself, outside and in
DAM_WET = "SDDAM2"       # 64x128 the same at the waterline (mark 72 px down, slime at the foot): the channel's banks
TURBINE = "SDTURB1"      # 128x128 generator housing, the 1957 maker's plate, a plinth at the foot
CONTROL_PANEL = "SDCTRL1"  # 128x128 control board in 64 px sections: the control room's boards and consoles
SPILLWAY = "SDSPIL1"     # 64x128 trash rack before running water: the dam's face over the channel
INSULATOR = "SDINSL1"    # 64x128 MASKED (RGBA, hard alpha, like SDCHAN1): HV strings, a middle texture
CONCRETE = "SDCONC1"     # prefab panels: S2's pump room and its panel (the gallery's comparison)
STEEL = "SDSTEL1"        # green riveted plate: catwalk, transformers, pylons, door tracks
TILE_DADO = "SDTILE2"    # tile over a green dado: the control room, the gatehouse
TUNNEL = "SDTUNL1"       # board-cast concrete with cable runs: the inspection and cable galleries
BRICK = "SDBRCK1"        # works brick: the station's buildings
RUST = "SDRUST1"         # corrugated sheet: the substation's east and west walls, the crane huts
DOOR = "SDDOOR1"         # D1 and D2
# Round 2 of the Dam set (D113, approved 2026-10-22; design section 7.2).
DOOR_BLUE = "SDDOORB"    # 128x128 the blue lock's leaf: the blue gate onto the crest
GRILL = "SDGRIL1"        # 64x128 MASKED: window bars, the control room's two windows over the hall
FENCE = "SDHVLT1"        # 64x128 MASKED: the substation's high-voltage fence, its north and south sides
DOOR_YELLOW = "SDDOORY"  # the yellow lock's trim
ROAD_GATE = "SDGATE1"    # corrugated gate: S3's shut hut
WINDOW = "SDWIND1"       # industrial glazing at night: the turbine hall's clerestory
# From the railway set (gen_railway.py, D107): MAP04's armoured train, which
# brings the player here, and one signal at the end of the station's track.
ARMOUR = "SDARMR2"       # 64x128 armour plate: the armoured train, as MAP04's
ARMOUR_STAR = "SDARMR1"  # 128x128 the plate with the red star: one panel per face, never stacked
SIGNAL = "SDSIGL1"       # 64x128 colour-light signal: SINGLE USE (D107), one 64 span, red over the track
FLAG_REICH = "SDFLAG1"   # both banners side by side by the blue gate (D35)
FLAG_LEGION = "SDFLAG2"
# The posters (CEO 2026-10-22: «que esos posters puedan aparecer en cualquier
# nivel»; tests/test_posters.py). Approved pictures, not pending ones: no
# "Dam" piece waits for them (design section 7.3).
LENIN = "SDPOSTR1"       # 128x256: presides over the turbine hall (electrification)
STALIN = "SDPOSTR3"      # 128x256: the station's, now beside the occupiers' banners
MURAL = "SDPOSTR2"       # 128x128 cosmonautics mural: the control room
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
CRATE = "SDCRAT1"        # crate faces: the crest's barricades
FLOOR_LANE = "SDFLR1"    # concrete with a yellow lane line: the road on the crest
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"    # the turbine hall's and the control room's floor
CEIL_PANEL = "SDCEIL1"
CEIL_CONCRETE = "SDCEIL2"
CRATE_TOP = "SDCRTOP1"
RAILS = "SDRAIL1"        # track bed, rails along the image's y: turned a quarter
FLOOR_PLATE = "SDFLR4"   # chequer plate: generator tops, consoles, pads, the gantry's underside
GRATING = "SDGRAT2"      # expanded metal over the void (dam set): the catwalk and its stair
WATER = "SDWATR1"        # the Volga: SDWATR1-4 animate through ANIMDEFS (8 tics a frame)
SKY = "F_SKY1"           # the engine's sky marker, not a lump of ours (check_pk3 knows it)
# The widths of the lumps `align_to_world` lines up along a wall as well.
LUMP_WIDTH = {DAM: 64, DAM_WET: 64, SPILLWAY: 64, TURBINE: 128, ARMOUR: 64}

# Switches (D25), one variant per switch; the exit keeps the hazard panel
# every map's exit wears.
SW_A_FACE = "SDSW1A"     # control room: the knife switch, opens the cable gallery
SW_B_FACE = "SDSW1B"     # substation: the push button, opens the shutter into the station
EXIT_FACE = "SDSW1D"
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64
SWITCH_HEIGHT = 128
TILE = 128               # door leaves, gates, flags, panes: one whole tile
DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_BLUE)

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED in engine
# on MAP02 and MAP03. Delay 0: opens and stays open.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock numbers from gzdoom.pk3 g4.14.2 -> lockdefs.txt: `Lock 2 Doom
# { BlueCard ... }`, `Lock 3 Doom { YellowCard ... }`. Both already opened
# in the engine (MAP02's blue door, MAP03's yellow door).
LOCK_BLUE_CARD = 2
LOCK_YELLOW_CARD = 3
# Doom's editor numbers; SD_BluePass and SD_YellowPass replace the cards
# (src/zscript/sd/keys.zs), so the passes are drawn as ours.
ED_BLUE_CARD = 5
ED_YELLOW_CARD = 6
KEY_LOCKS = {ED_BLUE_CARD: LOCK_BLUE_CARD, ED_YELLOW_CARD: LOCK_YELLOW_CARD}

ED_PLAYER1_START = 1

# --- Heights -------------------------------------------------------------------
GROUND = 0              # the turbine hall, the lower gallery, the spillway's walkways
CATWALK = 192           # the hall's north catwalk and the control room behind it
CREST = 384             # the station, the substation, the crest: the top of the dam
CHANNEL = -64           # the spillway's water
STEP = 16               # every stair step; under MAX_STEP_UP 24
STEP_RUN = 32           # every stair step is 32 deep
FLIGHT_STEPS = 7        # seven steps and a landing: 128 down per flight
FLIGHT_DROP = (FLIGHT_STEPS + 1) * STEP
DOOR_HEIGHT = 128
GALLERY_HEIGHT = 128    # every inspection gallery: one door high
PARAPET = 32            # the crest's parapets: cover to the waist, never a step
PAD = 16                # the key pads and the winch house: one step up
CONSOLE = 32            # the control room's consoles: waist high
GENERATOR = 48          # the generators' housings: chest high, cover, not a step
TRANSFORMER = 96        # the substation's transformers
TRAIN = 128             # the armoured train standing in the station
CRATES = 64             # the crest's barricades
HALL_CEIL = 448
CONTROL_CEIL = CATWALK + 160
ROOF = CREST + DOOR_HEIGHT          # 512: every roofed room at crest level
SKY_CEIL = 768                      # outdoors: the sky over the dam
PARAPET_SKY = CREST + PARAPET + 16  # 432: the open-air trick over the parapets
CLERESTORY_SILL = HALL_CEIL - TILE  # 320
WINDOW_SILL = CATWALK + 48          # the control room's windows onto the hall
WINDOW_TOP = CATWALK + 128   # an 80-high slot: never the 64..72 gap only the base Panzermensch fits (D67)
WINDOW_BARS_ROW = 2     # SDGRIL1 in the 80-high window: rows 2-81, both riveted flats inside it
NICHE_DEPTH = 16
CLOSET_HEIGHT = 128
POSTER_HEIGHT = 256     # SDPOSTR1 and SDPOSTR3: a recess exactly this high
GANTRY = CREST + 320    # 704: the substation gantry's underside; its insulator strings hang 128 from it
WALL_TILE = 128         # the height every wall lump of the Dam set repeats at (all are 128 high)
CONTROL_DESK_ROW = 64   # SDCTRL1: the desk (mimic bars, buttons, toggles) starts at this row

# --- Light ---------------------------------------------------------------------
# A November night. 192 is spent on five places only: the two locks, the two
# keys and the exit (MAP02 v1's rule).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_OUTDOORS = 128    # the station, the crest, the substation under the floodlights
LIGHT_SPILLWAY = 112    # the spillway: the darkest outdoor place
LIGHT_GATEHOUSE = 144
LIGHT_GALLERY = 112     # the inspection galleries inside the concrete
LIGHT_HALL = 160
LIGHT_CONTROL = 160
LIGHT_CLOSET = 112
LIGHT_HUT = 112
LIGHT_SHADOW = LIGHT_MIN    # a secret's set-back panel: the one in shadow
LIGHT_SECRET = 112
BEACON_ZONES = ("z1_blue_portal", "z5_yellow_portal", "z7_winch", "z9_pad", "z11_exit_niche")

# The keys' colours, in light (sector `lightcolor`, UDMF zdoom, as MAP02 and
# MAP03): the colour of the lock is the colour of where its key lies. The
# blue is MAP02's pass blue, the yellow MAP03's.
BLUE = 0x90A8FF
YELLOW = 0xFFD860
BLUE_LIGHT = {"lightcolor": BLUE}
YELLOW_LIGHT = {"lightcolor": YELLOW}

# --- The spillway's water -----------------------------------------------------
# A light sting, not a trap (the brief: "daño leve, sin abusar"): Doom's
# nukage, 5 every 32 tics, about 5 HP a second; the channel is 256 across
# with steps out on both banks at two places. UDMF zdoom sector fields, as
# MAP03's molten channel (VERIFIED in the spec there).
WATER_DAMAGE = 5
WATER_DAMAGE_INTERVAL = 32
WATER_HURTS = {"damageamount": WATER_DAMAGE, "damageinterval": WATER_DAMAGE_INTERVAL}

# --- Tags --------------------------------------------------------------------
TAG_D1_GATEHOUSE = 1
TAG_D2_WEST = 2          # the west bank's door, the last door before the exit
TAG_BLUE_GATE = 3        # the crest gate: Door_LockedRaise, lock 2; and the station's closets
TAG_YELLOW_DOOR = 4      # the control room: Door_LockedRaise, lock 3; and the catwalk's closets
TAG_S1_PANEL = 5
TAG_S2_PANEL = 6
TAG_S3_PANEL = 7
TAG_CABLE_SHUTTER = 10   # SW-A: the cable gallery
TAG_STATION_SHUTTER = 11  # SW-B: the shortcut from the substation into the station
# Closets ride the lock that lets the player past them (MAP03 rides SW-A's):
# the yellow door opens the catwalk's two, the blue gate the station's two.
TAG_CATWALK_AMBUSH = TAG_YELLOW_DOOR
TAG_STATION_AMBUSH = TAG_BLUE_GATE

# --- The plan (x east, y north; design document section 4) ---------------------
# The station, on the east bank, level with the crest.
STATION = (4288, 1408, 4864, 2048)
TRAIN_BLOCK = (4544, 1856, 4864, 1984)
STATION_RAILS = (4288, 1888, 4544, 1952)
# The train's star (SDARMR1, one panel, never stacked): the middle 128 of
# its south side, the face along the platform. Its west end stands on the
# station's rails, which split that face in three: plain plate there.
TRAIN_STARS = (("h", TRAIN_BLOCK[1], 4640, 4768),)
# SDSIGL1, single use: a concrete post 16 x 64 north of the track, its east
# face the signal, red, towards the train: the line ends at the shut gate.
SIGNAL_POST = (4304, 1968, 4320, 2032)
BLUE_PORTAL = (4224, 1856, 4288, 1984)
BLUE_GATE = (4192, 1856, 4224, 1984)
GATE_PORCH = (4128, 1856, 4192, 1984)
D1_PORCH = (4480, 1408, 4608, 1440)
D1_DOOR = (4480, 1376, 4608, 1408)
GATEHOUSE = (4416, 1152, 4672, 1376)
FLAG_RECESSES = {FLAG_REICH: (4272, 1728, 4288, 1792), FLAG_LEGION: (4272, 1792, 4288, 1856)}
# The inspection gallery: three flights of seven steps, two landings.
G1_X = (4480, 4608)
LANDING_1 = (4416, 800, 4672, 928)
LANDING_2 = (4416, 448, 4672, 576)
LOWER_GALLERY = (3456, 448, 4192, 576)
# The turbine hall.
HALL = (1664, 128, 3456, 896)
GENERATOR_X = (1984, 2368, 2752, 3136)     # centres
GENERATOR_Y = 448
GENERATOR_HALF = 96
COLUMN_HALF = 32         # the generator's shaft, solid, up to the roof
CATWALK_Y = (768, 896)
CATWALK_STAIR_STEPS = CATWALK // STEP - 1   # 11 steps, the catwalk is the 12th rise
CATWALK_X0 = HALL[0] + CATWALK_STAIR_STEPS * STEP_RUN    # 2016
YELLOW_PORTAL = (2560, 768, 2688, 896)
YELLOW_DOOR = (2560, 896, 2688, 928)
CLERESTORY = (1856, 2240, 2624, 3008, 3264)  # x of each pane in the hall's south wall
# The control room, behind the yellow door.
CONTROL = (2304, 928, 2944, 1312)
CONTROL_PORCH = (2560, 928, 2688, 960)
CONTROL_WINDOWS = {"win_z6_w": (2368, 896, 2496, 928), "win_z6_e": (2752, 896, 2880, 928)}
CONSOLES = ((2368, 1088, 2496, 1152), (2752, 1088, 2880, 1152))
SWA_NICHE = (2944, 1216, 2960, 1280)
CABLE_PORCH = (2912, 1056, 2944, 1184)
CABLE_SHUTTER = (2944, 1056, 2976, 1184)
CABLE_Y = (1056, 1184)
CABLE_FLAT = (2976, 3072)
CABLE_STAIR_STEPS = (CREST - CATWALK) // STEP - 1      # 11, the top corridor is the 12th rise
CABLE_TOP = (3072 + CABLE_STAIR_STEPS * STEP_RUN, 3584)  # 3424..3584
# The substation.
SUBSTATION = (3584, 896, 4160, 1664)
TRANSFORMERS = ((3712, 928, 3840, 1120), (3712, 1440, 3840, 1632), (3968, 928, 4096, 1120))
PYLONS = ((3632, 1376, 3664, 1408), (3632, 1536, 3664, 1568))   # solid, 32 square
# The gantry: a beam from pylon to pylon at GANTRY, SDINSL1 hung on both its
# long faces (two strings each), against the sky. Walked under, never on.
GANTRY_RECT = (PYLONS[0][0], PYLONS[0][3], PYLONS[1][2], PYLONS[1][1])
# The high-voltage fence (SDHVLT1, D113): the substation's south and north
# sides are a two-sided line, the fence its middle texture, the night behind
# it. Behind each side a strip FENCE_STRIP deep, open to a sky exactly as
# high as the fence (so the fence, hung from that sky, stands whole on the
# ground), and behind that a closed sky block (floor = ceiling): two sky
# ceilings side by side draw no wall between them, so through the wire the
# sky comes down to the dam's edge. The line is impassable. The east and
# west sides stay corrugated sheet: the cable gallery and the passage to the
# station come in through them.
FENCE_SIDES_Y = (SUBSTATION[1], SUBSTATION[3])      # 896 south, 1664 north
FENCE_STRIP = 16
FENCE_HEIGHT = 128      # SDHVLT1 is 64x128: one panel high
FENCE_WIDTH = 64        # one panel, its post on the tile's edge (posts on the world's 64 grid)
BLUE_PAD = (3904, 1216, 4032, 1344)
SWB_NICHE = (4176, 1600, 4240, 1616)   # in the passage's north wall, beside the shutter
STATION_PASSAGE = (4160, 1472, 4256, 1600)
STATION_SHUTTER = (4256, 1472, 4288, 1600)
# The spillway, west of the hall, its north end under the crest's parapet.
SPILL_GALLERY = (1408, 256, 1664, 384)
EAST_WALK = (1152, 128, 1408, 1760)
CHANNEL_RECT = (896, 128, 1152, 1760)
WEST_WALK = (512, 128, 896, 1760)
STEPS_Y = ((448, 576), (1280, 1408))       # where the banks have steps out of the water
WINCH = (576, 832, 768, 1024)
# The crest, from the blue gate west to the west bank.
CREST_RECT = (640, 1792, 4192, 2048)
CREST_RAILS = (704, 1888, 4128, 1952)
PARAPET_N = (640, 2048, 4192, 2080)
PARAPET_S = (640, 1760, 4192, 1792)
STATION_PARAPET = (4288, 2048, 4864, 2080)
HUT_W = (2304, 1632, 2560, 1760)           # the open crane hut (the comparison)
HUT_E = (3200, 1632, 3456, 1760)           # S3: the shut one
HUT_FRONT_X = {"w": (2368, 2496), "e": (3264, 3392)}
BARRICADES = ((1536, 1808, 1664, 1856), (2048, 1984, 2176, 2032), (2880, 1808, 3008, 1856),
              (3584, 1984, 3712, 2032))
WEST_PORCH = (640, 1856, 704, 1984)
WEST_DOOR = (608, 1856, 640, 1984)
WEST_HALL = (448, 1792, 608, 2048)
EXIT_NICHE = (432, 1888, 448, 1952)
# The posters (design section 7.3). Lenin in a recess in the turbine hall's
# west wall, at the end the player looks down on entering from the lower
# gallery, clear of the generators' shafts; Stalin in a recess in the
# station's west wall, between the shutter and the occupiers' two banners:
# the first wall the player sees, the picture the invaders hung their flags
# beside. The cosmonautics mural on a 32-high sill in the control room's
# north wall, straight ahead through the yellow door: the room is 160 high,
# the mural 128. The two portraits on the catwalk's back wall flank the
# yellow door symmetrically (320 either side of its axis): the Marx-Engels
# slots.
LENIN_NICHE = (HALL[0] - NICHE_DEPTH, 576, HALL[0], 704)
STALIN_NICHE = (STATION[0] - NICHE_DEPTH, 1600, STATION[0], 1728)
CONTROL_MURAL_NICHE = (2560, CONTROL[3], 2688, CONTROL[3] + NICHE_DEPTH)
MURAL_SILL = CONTROL_CEIL - CATWALK - TILE     # 32: the mural's foot over the floor
CATWALK_SLOTS_X = {"z5_catwalk_w": (2240, 2368), "z5_catwalk_e": (2880, 3008)}
POSTERS = (
    ("z5_lenin", LENIN, "v", LENIN_NICHE[0], LENIN_NICHE[1], LENIN_NICHE[3]),
    ("z1_stalin", STALIN, "v", STALIN_NICHE[0], STALIN_NICHE[1], STALIN_NICHE[3]),
    ("z6_mural", MURAL, "h", CONTROL_MURAL_NICHE[3], CONTROL_MURAL_NICHE[0], CONTROL_MURAL_NICHE[2]),
    ("z5_catwalk_w", MARX, "h", CATWALK_Y[1], *CATWALK_SLOTS_X["z5_catwalk_w"]),
    ("z5_catwalk_e", ENGELS, "h", CATWALK_Y[1], *CATWALK_SLOTS_X["z5_catwalk_e"]),
)
POSTER_SLOTS_MARX_ENGELS = ("z5_catwalk_w", "z5_catwalk_e")   # Marx, Engels
# The control room's boards (SDCTRL1, for the design's SDPANL1): each a strip
# BOARD_DEPTH deep along a wall, the board a middle texture on its room face,
# drawn once and standing on the floor (128 of the room's 160; the tiled wall
# shows above it). Two flank the mural on the north wall, one tile on each
# side wall faces the other across the room. {name: (strip, board face)}.
BOARD_DEPTH = 8
CONTROL_BOARDS = {
    "prop_z6_board_nw": ((CONTROL[0], CONTROL[3] - BOARD_DEPTH, CONTROL_MURAL_NICHE[0], CONTROL[3]),
                         ("h", CONTROL[3] - BOARD_DEPTH, CONTROL[0], CONTROL_MURAL_NICHE[0])),
    "prop_z6_board_ne": ((CONTROL_MURAL_NICHE[2], CONTROL[3] - BOARD_DEPTH, CONTROL[2], CONTROL[3]),
                         ("h", CONTROL[3] - BOARD_DEPTH, CONTROL_MURAL_NICHE[2], CONTROL[2])),
    "prop_z6_board_w": ((CONTROL[0], CONTROL[1], CONTROL[0] + BOARD_DEPTH, CONTROL[1] + TILE),
                        ("v", CONTROL[0] + BOARD_DEPTH, CONTROL[1], CONTROL[1] + TILE)),
    "prop_z6_board_e": ((CONTROL[2] - BOARD_DEPTH, CONTROL[1], CONTROL[2], CONTROL[1] + TILE),
                        ("v", CONTROL[2] - BOARD_DEPTH, CONTROL[1], CONTROL[1] + TILE)),
}
# The closets.
CATWALK_CLOSETS = {"closet_z5_w": (2112, 2240), "closet_z5_e": (3200, 3328)}
STATION_CLOSETS = {"closet_z1_s": ((4704, 1392, 4832, 1408), (4704, 1264, 4832, 1392)),
                   "closet_z1_e": ((4864, 1472, 4880, 1600), (4880, 1472, 5008, 1600))}
# The secrets (design section 8).
S1_NICHE = (960, 112, 1088, 128)    # the channel's outfall, set back in shadow
S1_PANEL = (960, 96, 1088, 112)
S1_CULVERT = (960, -32, 1088, 96)
S1_STORE = (896, -224, 1152, -32)
S2_NICHE = (3776, 432, 3840, 448)   # the one gallery panel with no cables on it
S2_PANEL = (3776, 416, 3840, 432)
S2_PASSAGE = (3776, 352, 3840, 416)
S2_STORE = (3648, 160, 3968, 352)

# --- Things --------------------------------------------------------------------
PLAYER_START = (4704, 1664)
PLAYER_ANGLE = 180       # facing west, along the platform, towards the blue gate
YELLOW_KEY_SPOT = (672, 928)     # on the winch house, across the spillway's water
BLUE_KEY_SPOT = (3968, 1280)     # on the transformer pad, in the substation
KEY_ZONES = {ED_YELLOW_CARD: "z7_winch", ED_BLUE_CARD: "z9_pad"}
LOCK_PORTALS = {LOCK_YELLOW_CARD: "z5_yellow_portal", LOCK_BLUE_CARD: "z1_blue_portal"}

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design
WINDOWS = tuple(CONTROL_WINDOWS)  # seen through, never walked
SECRET_ZONES = ("s1_store", "s2_store", "s3_hut")
CLOSET_PREFIX = "closet_"

# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich
ED_TROOPER = 21101        # SD_LegionTrooper, Legion
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both
ED_HOUND = 21103          # SD_ReichHound, Reich
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, flies
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich
ED_PANZER_HEAVY = 21107   # SD_PanzermenschSchwer, Reich
ED_GUNNER = 21110         # SD_LegionGunner, Legion, 80 HP: bursts of hitscan; drops 15 AKM rounds (D116)
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
# Where each faction stands (D35: both on the map). The Legion holds the
# east bank's station and the open water (the spillway, where its Doughboys
# fly); the Reich runs the machine: the galleries, the turbine hall and the
# substation. Both man the control room and both hold the crest, the last
# fight. Stormtroopers are hybrids and stand anywhere; the closets are
# counter-attacks, not garrisons. The General is MAP03's and is not here.
LEGION_GROUND = ("z1_", "z2_", "z7_")
REICH_GROUND = ("z3_", "z4_", "z5_", "z8_", "z9_")
BOTH_GROUND = ("z6_", "z10_", "z11_")
# The arsenal (MAPINFO DoomEdNums 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ED_AKM = 21008            # SD_Akm, slot 4's second weapon (D116): 30 rounds of its own pool
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7, ED_ROKS3, ED_AKM)
ED_HAND_KATYUSHA = 21007  # in S3 only, on the crest, for the last fight
# Ammo, health and armour: Doom's numbers, which our classes replace.
ED_CLIP = 2007
ED_CLIP_BOX = 2048
ED_SHELLS = 2008
ED_SHELL_BOX = 2049
ED_ROCKET = 2010
ED_ROCKET_BOX = 2046
ED_CELL = 2047
ED_AKM_AMMO = 21020       # SD_AkmAmmo, one 30-round 7.62x39 magazine (D116, ADR 011)
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019

# Design section 9: monsters per skill, Doom's skill pairs (udmf.skill_tier).
ENEMY_TOTALS = {2: 31, 3: 46, 4: 60}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Facing: 0
# east, 90 north, 180 west, 270 south.
MONSTERS = (
    # The station: the Legion's picket at the train, in the lee of it
    # between the train and the parapet, facing the train: hidden from the
    # start (tests/test_safe_starts.py), met as the player rounds the
    # train's west end. On the open platform they saw the start from 370
    # and 450, the whole station being within 768 of it.
    ("z1_station", "trooper", 4592, 2016, 270, 2),
    ("z1_station", "trooper", 4784, 2016, 270, 2),
    ("z1_station", "stormtrooper", 4688, 2016, 270, 4),
    # The gatehouse.
    ("z2_gatehouse", "trooper", 4480, 1216, 90, 2),
    ("z2_gatehouse", "stormtrooper", 4608, 1312, 270, 4),
    # The inspection gallery, inside the concrete: the Reich's.
    ("z3_landing_1", "rifleman", 4544, 864, 90, 2),
    ("z3_landing_1", "rifleman", 4640, 832, 90, 3),
    ("z3_landing_2", "hound", 4544, 512, 90, 3),
    ("z4_gallery", "rifleman", 3712, 512, 0, 2),
    ("z4_gallery", "rifleman", 3968, 480, 0, 2),
    ("z4_gallery", "hound", 3584, 512, 0, 3),
    # The turbine hall: the Reich at the machines; the Panzermensch at the
    # far west end on every skill, the RPG-7 at the door the player enters by.
    ("z5_hall", "panzermensch", 1792, 288, 0, 2),
    ("z5_hall", "rifleman", 2176, 256, 0, 2),
    ("z5_hall", "rifleman", 2560, 672, 0, 2),
    ("z5_hall", "stormtrooper", 2944, 256, 0, 2),
    ("z5_catwalk", "rifleman", 2304, 832, 270, 2),
    ("z5_hall", "hound", 2176, 672, 0, 3),
    ("z5_hall", "stormtrooper", 2560, 256, 0, 3),
    ("z5_catwalk", "rifleman", 3008, 832, 270, 3),
    ("z5_hall", "hound", 1792, 640, 0, 4),
    ("z5_hall", "stormtrooper", 3328, 704, 180, 4),
    # The spillway: the Legion on the walkways, its Doughboys over the water.
    ("z7_channel", "doughboy", 1024, 1088, 270, 2),
    # The Legion gunners (D116) on the west walkway: the channel's whole
    # width to fire across, the parapet for cover; the second on hard.
    ("z7_west_walk", "gunner", 640, 576, 0, 2),
    ("z7_west_walk", "trooper", 704, 1344, 0, 2),
    ("z7_west_walk", "stormtrooper", 800, 1152, 0, 3),
    ("z7_channel", "doughboy", 1024, 1536, 270, 4),
    ("z7_west_walk", "gunner", 640, 1600, 270, 4),
    # The control room: both factions at the consoles.
    ("z6_control", "trooper", 2400, 1248, 270, 2),
    ("z6_control", "rifleman", 2848, 1024, 180, 2),
    ("z6_control", "stormtrooper", 2624, 1248, 270, 2),
    ("z6_control", "gunner", 2848, 1248, 180, 3),     # D116: down the console rows
    ("z6_control", "stormtrooper", 2400, 1024, 0, 4),
    # The yellow door's closets on the catwalk: the Reich comes back.
    ("closet_z5_w", "rifleman", 2144, 944, 270, 2),
    ("closet_z5_w", "stormtrooper", 2208, 1008, 270, 4),
    ("closet_z5_e", "hound", 3288, 952, 270, 2),
    ("closet_z5_e", "rifleman", 3224, 1016, 270, 3),
    # The substation: the Reich's heavies among the transformers.
    ("z9_substation", "hound", 3640, 1280, 0, 2),
    ("z9_substation", "rifleman", 4096, 1216, 180, 2),
    ("z9_substation", "rifleman", 3904, 1568, 180, 2),
    ("z9_substation", "panzermensch", 3904, 1024, 270, 2),
    ("z9_substation", "hound", 4064, 1600, 180, 3),
    ("z9_substation", "heavy", 4064, 1456, 180, 4),
    # The blue gate's closets in the station: the Legion behind the player.
    ("closet_z1_s", "trooper", 4736, 1312, 90, 2),
    ("closet_z1_s", "stormtrooper", 4800, 1360, 90, 3),
    ("closet_z1_e", "trooper", 4944, 1504, 180, 2),
    ("closet_z1_e", "trooper", 4944, 1568, 180, 4),
    # The crest, the last fight: both factions, the heavy by the west door.
    ("z10_crest", "panzermensch", 2048, 1856, 0, 2),
    ("z10_crest", "stormtrooper", 3648, 1840, 0, 2),
    ("z10_crest", "rifleman", 3008, 2000, 0, 2),
    ("z10_crest", "rifleman", 2688, 1840, 0, 2),
    ("z10_crest", "doughboy", 2432, 2000, 0, 2),
    ("z10_crest", "gunner", 1408, 1840, 0, 2),        # D116: the crest's length to fire along
    ("z10_crest", "stormtrooper", 1792, 1840, 0, 3),
    ("z10_crest", "doughboy", 1216, 2000, 0, 3),
    ("z10_crest", "heavy", 896, 1840, 0, 3),
    ("z10_hut_w", "trooper", 2432, 1696, 90, 3),
    ("z10_crest", "hound", 2688, 2000, 0, 4),
    ("z10_crest", "doughboy", 3200, 1840, 0, 4),
    ("z10_crest", "rifleman", 1088, 2000, 0, 4),
    ("z11_west_hall", "stormtrooper", 512, 1840, 0, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest
# skill tier it appears on - 4 = every skill, 3 = medium and easier, 2 =
# easy only). Weapons are on every skill.
ITEMS = (
    # The weapons, on every skill, on the route, each before the fight it is
    # for: the IZh on the platform, the PPSh in the lower gallery, the RPG-7
    # at the turbine hall's door (before the Panzermensch), the ROKS-3 in
    # the control room (for the substation and the crest).
    ("z1_station", ED_IZH, 4480, 1664, 4),
    ("z4_gallery", ED_PPSH, 3840, 512, 4),
    ("z5_hall", ED_RPG7, 3392, 512, 4),
    ("z6_control", ED_ROKS3, 2624, 1056, 4),
    # The AKM (D116; docs/engine/2026-10-22_P4_akm.md section 6): the
    # episode's new rifle, at the gallery's west end, after the PPSh and
    # before the hall's door and its RPG-7, for the dam's long sightlines.
    ("z4_gallery", ED_AKM, 3648, 512, 4),
    # Shell boxes (20).
    ("z5_hall", ED_SHELL_BOX, 1760, 192, 4),
    ("z7_east_walk", ED_SHELL_BOX, 1280, 1664, 4),
    ("z6_control", ED_SHELL_BOX, 2880, 1280, 4),
    ("z9_substation", ED_SHELL_BOX, 3648, 960, 4),
    ("z10_crest", ED_SHELL_BOX, 3968, 1840, 4),
    ("z10_crest", ED_SHELL_BOX, 1984, 2000, 4),
    # Shells (4).
    ("z1_station", ED_SHELLS, 4544, 1504, 4),
    ("z2_gatehouse", ED_SHELLS, 4608, 1216, 4),
    ("z4_gallery", ED_SHELLS, 3520, 480, 4),
    ("z5_hall", ED_SHELLS, 3008, 704, 4),
    ("z7_gallery", ED_SHELLS, 1536, 320, 4),
    ("z8_cable_gallery", ED_SHELLS, 3024, 1120, 4),
    ("z10_crest", ED_SHELLS, 2816, 2000, 4),
    ("z10_crest", ED_SHELLS, 1280, 1840, 4),
    ("z1_station", ED_SHELLS, 4608, 1504, 3),
    ("z5_hall", ED_SHELLS, 2368, 224, 3),
    ("z7_west_walk", ED_SHELLS, 576, 1088, 3),
    ("z9_substation", ED_SHELLS, 4096, 1376, 3),
    ("z10_crest", ED_SHELLS, 3456, 1840, 3),
    ("z4_gallery", ED_SHELLS, 3584, 544, 2),
    ("z5_hall", ED_SHELLS, 2752, 704, 2),
    ("z10_crest", ED_SHELLS, 2304, 2000, 2),
    # Boxes of rounds (50).
    ("z5_hall", ED_CLIP_BOX, 2752, 192, 4),
    ("z6_control", ED_CLIP_BOX, 2368, 1264, 4),
    ("z10_crest", ED_CLIP_BOX, 3840, 2000, 4),
    # Clips (10).
    ("z1_station", ED_CLIP, 4352, 1472, 4),
    ("z3_landing_1", ED_CLIP, 4448, 832, 4),
    ("z4_gallery", ED_CLIP, 4032, 512, 4),
    ("z7_east_walk", ED_CLIP, 1216, 320, 4),
    ("z1_station", ED_CLIP, 4416, 1472, 3),
    ("z5_hall", ED_CLIP, 1984, 224, 3),
    ("z1_station", ED_CLIP, 4480, 1472, 2),
    # AKM magazines (30): 4 / 3 / 2 on skills 2 / 3 / 4, plus the gunners'
    # drops (15 each, not counted).
    ("z4_gallery", ED_AKM_AMMO, 3616, 512, 4),
    ("z10_crest", ED_AKM_AMMO, 3040, 1872, 4),
    ("z6_control", ED_AKM_AMMO, 2496, 1056, 3),
    ("z7_west_walk", ED_AKM_AMMO, 576, 1408, 2),
    # PG-7V: a box with the RPG-7, rounds for the substation and the crest.
    ("z5_hall", ED_ROCKET_BOX, 3392, 640, 4),
    ("z9_substation", ED_ROCKET_BOX, 3648, 1600, 4),
    ("z10_crest", ED_ROCKET, 3904, 2000, 4),
    ("z10_crest", ED_ROCKET, 2560, 1840, 4),
    ("z10_crest", ED_ROCKET, 1600, 2000, 4),
    ("z9_passage", ED_ROCKET, 4192, 1536, 3),
    # Fuel for the ROKS-3.
    ("z6_control", ED_CELL, 2688, 1056, 4),
    ("z9_substation", ED_CELL, 4096, 1632, 4),
    ("z10_crest", ED_CELL, 3136, 2000, 4),
    # Stimpacks.
    ("z1_station", ED_STIMPACK, 4800, 1472, 4),
    ("z4_gallery", ED_STIMPACK, 3520, 544, 4),
    ("z5_hall", ED_STIMPACK, 2368, 672, 4),
    ("z7_west_walk", ED_STIMPACK, 576, 192, 4),
    ("z9_gantry", ED_STIMPACK, 3648, 1472, 4),     # between the pylons, under the strings
    ("z10_crest", ED_STIMPACK, 3072, 1840, 4),
    ("z2_gatehouse", ED_STIMPACK, 4448, 1312, 3),
    ("z7_east_walk", ED_STIMPACK, 1216, 1408, 3),
    ("z10_crest", ED_STIMPACK, 1792, 2000, 3),
    ("z5_hall", ED_STIMPACK, 1760, 448, 2),
    ("z10_crest", ED_STIMPACK, 3584, 1840, 2),
    # Medikits.
    ("z5_hall", ED_MEDIKIT, 2368, 736, 4),
    ("z7_west_walk", ED_MEDIKIT, 576, 1664, 4),
    ("z6_control", ED_MEDIKIT, 2336, 960, 4),
    ("z9_passage", ED_MEDIKIT, 4208, 1504, 4),
    ("z10_crest", ED_MEDIKIT, 2304, 1840, 4),
    ("z10_crest", ED_MEDIKIT, 1216, 1840, 3),
    ("z9_substation", ED_MEDIKIT, 3648, 1216, 3),
    # Armour: the flak vest up on the catwalk (for climbing it), the heavy
    # vest in the substation's passage before the station's closets and the
    # crest; plates at the locks and the keys' rooms.
    ("z5_catwalk", ED_GREEN_ARMOR, 3424, 800, 4),
    ("z9_passage", ED_BLUE_ARMOR, 4192, 1568, 4),
    ("z5_catwalk", ED_ARMOR_BONUS, 2496, 832, 4),
    ("z5_catwalk", ED_ARMOR_BONUS, 2752, 832, 4),
    ("z1_station", ED_ARMOR_BONUS, 4352, 1856, 4),
    ("z1_station", ED_ARMOR_BONUS, 4352, 1984, 4),
    ("z7_west_walk", ED_ARMOR_BONUS, 640, 800, 4),
    ("z7_west_walk", ED_ARMOR_BONUS, 640, 1056, 4),
    ("z6_control", ED_ARMOR_BONUS, 2496, 1248, 3),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z3_landing_2", ED_HEALTH_BONUS, 4640, 480, 4),
    ("z5_stair_6", ED_HEALTH_BONUS, 1840, 832, 4),
    ("z7_gallery", ED_HEALTH_BONUS, 1600, 288, 4),
    ("z8_cable_top", ED_HEALTH_BONUS, 3456, 1088, 4),
    ("z9_substation", ED_HEALTH_BONUS, 4128, 1376, 4),
    ("z10_hut_w", ED_HEALTH_BONUS, 2336, 1664, 4),
    ("z10_hut_w", ED_HEALTH_BONUS, 2528, 1664, 4),
    ("z10_gate_porch", ED_HEALTH_BONUS, 4160, 1920, 4),
    ("z11_west_hall", ED_HEALTH_BONUS, 528, 2000, 4),
)

# The secrets' rewards, on every skill (MAP01's rule); kept out of ITEMS,
# which is the route's.
SECRET_ITEMS = (
    # S1, the drain under the spillway: rockets and health.
    ("s1_store", ED_ROCKET_BOX, 960, -128, 4),
    ("s1_store", ED_MEDIKIT, 1088, -128, 4),
    ("s1_store", ED_SHELL_BOX, 1024, -192, 4),
    # S2, the pump room behind the gallery: the flak vest and shells.
    ("s2_store", ED_GREEN_ARMOR, 3808, 256, 4),
    ("s2_store", ED_SHELL_BOX, 3712, 224, 4),
    ("s2_store", ED_STIMPACK, 3904, 224, 4),
    # S3, the shut crane hut on the crest: the Hand Katyusha, for the last
    # fight, and a canister towards a second volley.
    ("s3_hut", ED_HAND_KATYUSHA, 3328, 1696, 4),
    ("s3_hut", ED_CELL, 3264, 1664, 4),
    ("s3_hut", ED_CELL, 3392, 1664, 4),
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


BLOCKING = LineStyle(flags=("blocking",))   # a parapet's edge: nobody crosses it, not even jumping
# A control board's face: impassable (the board is a picture on a two-sided
# line), lower-unpegged so its middle texture stands on the floor.
BOARD_EDGE = LineStyle(flags=("blocking",), peg_bottom=True)


def hang(tm: TextMap, segment: tuple[int, int, int, int], room: int, texture: str) -> None:
    """Hang a middle texture on the two-sided line `segment`, on its face
    towards `room` (MAP03's helper, repeated so each map stays one file).
    GridMap dresses only the upper and lower parts of a two-sided line, so
    this is done on the built map. Doom draws a two-sided middle texture
    once, never tiled downwards: its top at the lower of the two ceilings,
    or, with `dontpegbottom`, its foot on the higher of the two floors."""
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


def bar_the_windows(tm: TextMap, plan: dict[str, int]) -> None:
    """SDGRIL1 in the control room's two windows, on the hall's face of each:
    the middle texture of the line between the window and the catwalk, on
    both its sides (the bars are seen from the hall and from the room).
    Doom hangs it from the window's head (the lower ceiling); `offsety_mid`
    (UDMF zdoom, added to the side's offsety) puts row 2 there, so the 80
    rows of the window show both riveted flats. Seen through; the sill (48
    over the catwalk) is what keeps anyone from climbing in."""
    catwalk = plan["z5_catwalk"]
    windows = {plan[name] for name in CONTROL_WINDOWS}
    barred = 0
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        pair = {tm.sidedefs[ld.sidefront].sector, tm.sidedefs[ld.sideback].sector}
        if catwalk not in pair or not pair & windows:
            continue
        for side in (ld.sidefront, ld.sideback):
            tm.sidedefs[side].texturemiddle = GRILL
            tm.sidedefs[side].extra["offsety_mid"] = WINDOW_BARS_ROW
        barred += 1
    if barred != len(windows):
        raise ValueError(f"{barred} window lines barred, {len(windows)} windows")


def drawn_parts(tm: TextMap, ld, side: int, other: int | None) -> list[tuple[str, int]]:
    """The parts of sidedef `side` the engine draws, each with the height
    Doom pegs its texture to: a one-sided wall to its floor (lower-unpegged)
    or ceiling; a lower texture to the higher floor (or, lower-unpegged, to
    its own ceiling); an upper texture to the lower ceiling (or, upper-
    unpegged, to its own). Where two sky ceilings meet nothing is drawn."""
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


def align_to_world(tm: TextMap, bases: dict[str, int], sectors: set[int] | None = None) -> None:
    """Peg every drawn face of the lumps in `bases` to one grid: the texture's
    foot on the height `bases` names, and every WALL_TILE above and below it,
    whichever floor or ceiling the face hangs from. A sidedef's `offsety`
    (Doom's row offset: positive raises the texture) moves each face onto the
    grid, so the dam's lift joints run level from the spillway's floor to the
    parapets and round the hall, and SDDAM2's waterline sits on the water.
    Along the wall the same: `offsetx` puts every column of a lump in
    LUMP_WIDTH where it would fall on a wall from the map's origin, so a
    wall split by its neighbours' corners shows no seam.
    `sectors` limits it to the faces seen from those sectors."""
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


def world_column(tm: TextMap, ld, side: int) -> int:
    """The offset that starts this side's texture where the map's grid
    would have it. Doom runs a front side's texture from v1 to v2 and a back
    side's from v2 to v1; every line here is axis-aligned."""
    a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
    if side == ld.sideback:
        a, b = b, a
    if a.y == b.y:
        return int(a.x) if b.x > a.x else -int(a.x)
    return int(a.y) if b.y > a.y else -int(a.y)


def wet_the_banks(tm: TextMap, water: set[int], banks: set[int]) -> None:
    """SDDAM2 on every face that rises out of the water onto a bank or a
    step: the lower texture of the side standing in the water."""
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        for low, high in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            ls, hs = tm.sidedefs[low].sector, tm.sidedefs[high].sector
            if ls in water and hs in banks and tm.sectors[hs].heightfloor > tm.sectors[ls].heightfloor:
                tm.sidedefs[low].texturebottom = DAM_WET


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=DAM)
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
        """A rail strip along x: SDRAIL1 runs its rails along the image's y."""
        like(room, name, [rect], flat=RAILS, extra={**tm.sectors[plan[room]].extra, "rotationfloor": 90.0})

    def recess(room: str, name: str, rect, *, ceil: int, back, texture: str) -> int:
        """A shallow recess one tile high, its back wall one tile of `texture`."""
        index = like(room, name, [rect], ceil=ceil)
        kind, coord, lo, hi = back
        if kind == "v":
            g.style_v(coord, lo, hi, LineStyle(texture=texture))
        else:
            g.style_h(coord, lo, hi, LineStyle(texture=texture))
        return index

    def closet(name: str, door_rect, room_rect, tag: int, floor: int, *, leaf: str) -> int:
        """A monster closet (MAP01 v3's, MAP03's): a panel in a wall that opens
        for good with the lock that owns `tag`, wearing the wall it is cut
        into, so it is wall until it moves; a dead end the player walks out of."""
        door_index = zone(f"{name}_door", floor, floor, [door_rect], tag, light=LIGHT_CLOSET, wall=leaf)
        zone(name, floor, floor + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

    # ======================================================================
    # The station: the armoured train in, the blue gate onto the crest
    # ======================================================================
    zone("z1_station", CREST, SKY_CEIL, [STATION], light=LIGHT_OUTDOORS,
         ceiling=SKY, wall=BRICK)
    rails("z1_station", "rails_z1_station", STATION_RAILS)
    zone(f"{PROP_PREFIX}z1_train", CREST + TRAIN, SKY_CEIL, [TRAIN_BLOCK], light=LIGHT_OUTDOORS,
         flat=FLOOR_PLATE, ceiling=SKY, wall=ARMOUR)
    zone(f"{PROP_PREFIX}z1_signal", CREST + TILE, SKY_CEIL, [SIGNAL_POST], light=LIGHT_OUTDOORS,
         ceiling=SKY, wall=DAM)
    zone("z1_blue_portal", CREST, ROOF, [BLUE_PORTAL], light=LIGHT_BEACON,
         ceiling=CEIL_PANEL, wall=BRICK, extra=BLUE_LIGHT)
    blue_gate = door("z12_blue_gate", CREST, TAG_BLUE_GATE, BLUE_GATE, light=LIGHT_OUTDOORS)
    zone("z1_d1_porch", CREST, ROOF, [D1_PORCH], light=LIGHT_OUTDOORS, wall=BRICK)
    for texture, rect in FLAG_RECESSES.items():
        x1, y1, x2, y2 = rect
        recess("z1_station", f"z1_flag_{texture.lower()}", rect, ceil=CREST + TILE,
               back=("v", x1, y1, y2), texture=texture)
    # Stalin's recess: its own concrete ceiling, so the station's brick shows
    # above it under the sky.
    like("z1_station", "z1_stalin_niche", [STALIN_NICHE], ceil=CREST + POSTER_HEIGHT,
         ceiling=CEIL_CONCRETE)
    zone(f"{PROP_PREFIX}z1_parapet_n", CREST + PARAPET, PARAPET_SKY, [STATION_PARAPET],
         light=LIGHT_OUTDOORS, ceiling=SKY, wall=DAM)
    d1 = door("d1_gatehouse", CREST, TAG_D1_GATEHOUSE, D1_DOOR, light=LIGHT_GATEHOUSE)
    zone("z2_gatehouse", CREST, ROOF, [GATEHOUSE], light=LIGHT_GATEHOUSE,
         flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)

    # ======================================================================
    # The inspection gallery: three flights down inside the concrete
    # ======================================================================
    gx1, gx2 = G1_X
    y = GATEHOUSE[1]
    floor = CREST
    for n in range(1, FLIGHT_STEPS + 1):          # flight 1, south
        floor -= STEP
        zone(f"z3_flight1_{n}", floor, floor + GALLERY_HEIGHT, [(gx1, y - STEP_RUN, gx2, y)],
             light=LIGHT_GALLERY, wall=TUNNEL)
        y -= STEP_RUN
    floor -= STEP
    zone("z3_landing_1", floor, floor + GALLERY_HEIGHT, [LANDING_1], light=LIGHT_GALLERY, wall=TUNNEL)
    y = LANDING_1[1]
    for n in range(1, FLIGHT_STEPS + 1):          # flight 2, south
        floor -= STEP
        zone(f"z3_flight2_{n}", floor, floor + GALLERY_HEIGHT, [(gx1, y - STEP_RUN, gx2, y)],
             light=LIGHT_GALLERY, wall=TUNNEL)
        y -= STEP_RUN
    floor -= STEP
    zone("z3_landing_2", floor, floor + GALLERY_HEIGHT, [LANDING_2], light=LIGHT_GALLERY, wall=TUNNEL)
    x = LANDING_2[0]
    for n in range(1, FLIGHT_STEPS + 1):          # flight 3, west
        floor -= STEP
        zone(f"z3_flight3_{n}", floor, floor + GALLERY_HEIGHT,
             [(x - STEP_RUN, LANDING_2[1], x, LANDING_2[3])], light=LIGHT_GALLERY, wall=TUNNEL)
        x -= STEP_RUN
    floor -= STEP
    assert floor == GROUND and x == LOWER_GALLERY[2], (floor, x)
    zone("z4_gallery", GROUND, GALLERY_HEIGHT, [LOWER_GALLERY], light=LIGHT_GALLERY, wall=TUNNEL)
    # S2: one panel of the gallery's south wall has no cables on it, and
    # stands back in shadow; it opens onto the pump room.
    zone("s2_niche", GROUND, GALLERY_HEIGHT, [S2_NICHE], light=LIGHT_SHADOW, wall=TUNNEL)
    s2_panel = zone("s2_panel", GROUND, GROUND, [S2_PANEL], TAG_S2_PANEL, light=LIGHT_SHADOW,
                    wall=TUNNEL)
    zone("s2_passage", GROUND, GALLERY_HEIGHT, [S2_PASSAGE], light=LIGHT_SECRET, wall=CONCRETE)
    zone("s2_store", GROUND, GALLERY_HEIGHT, [S2_STORE], light=LIGHT_SECRET, wall=CONCRETE,
         special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # The turbine hall: four generators, the catwalk, the yellow door
    # ======================================================================
    zone("z5_hall", GROUND, HALL_CEIL, [HALL], light=LIGHT_HALL, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=DAM)
    for n, cx in enumerate(GENERATOR_X, start=1):
        like("z5_hall", f"{PROP_PREFIX}z5_generator_{n}",
             [(cx - GENERATOR_HALF, GENERATOR_Y - GENERATOR_HALF,
               cx + GENERATOR_HALF, GENERATOR_Y + GENERATOR_HALF)],
             floor=GROUND + GENERATOR, flat=FLOOR_PLATE, wall=TURBINE)
        g.carve(cx - COLUMN_HALF, GENERATOR_Y - COLUMN_HALF, cx + COLUMN_HALF, GENERATOR_Y + COLUMN_HALF)
    cy1, cy2 = CATWALK_Y
    for n in range(1, CATWALK_STAIR_STEPS + 1):
        x = HALL[0] + STEP_RUN * (n - 1)
        like("z5_hall", f"z5_stair_{n}", [(x, cy1, x + STEP_RUN, cy2)], floor=GROUND + STEP * n,
             flat=GRATING, wall=DAM)
    like("z5_hall", "z5_catwalk", [(CATWALK_X0, cy1, HALL[2], cy2)], floor=CATWALK,
         flat=GRATING, wall=DAM)
    like("z5_hall", "z5_lenin_niche", [LENIN_NICHE], ceil=GROUND + POSTER_HEIGHT)
    zone("z5_yellow_portal", CATWALK, CATWALK + DOOR_HEIGHT, [YELLOW_PORTAL], light=LIGHT_BEACON,
         flat=GRATING, ceiling=CEIL_PANEL, wall=STEEL, extra=YELLOW_LIGHT)
    yellow_door = door("yellow_door", CATWALK, TAG_YELLOW_DOOR, YELLOW_DOOR, light=LIGHT_CONTROL)
    for n, x in enumerate(CLERESTORY, start=1):
        recess("z5_hall", f"{PROP_PREFIX}z5_clerestory_{n}", (x, HALL[1] - NICHE_DEPTH, x + 64, HALL[1]),
               ceil=HALL_CEIL, back=("h", HALL[1] - NICHE_DEPTH, x, x + 64), texture=WINDOW)
        tm.sectors[plan[f"{PROP_PREFIX}z5_clerestory_{n}"]].heightfloor = CLERESTORY_SILL
    for name, (x1, x2) in CATWALK_CLOSETS.items():
        closet(name, (x1, cy2, x2, cy2 + NICHE_DEPTH), (x1, cy2 + NICHE_DEPTH, x2, cy2 + NICHE_DEPTH + TILE),
               TAG_CATWALK_AMBUSH, CATWALK, leaf=DAM)

    # ======================================================================
    # The control room, behind the yellow door
    # ======================================================================
    zone("z6_control", CATWALK, CONTROL_CEIL, [CONTROL], light=LIGHT_CONTROL, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=TILE_DADO)
    zone("z6_porch", CATWALK, CATWALK + DOOR_HEIGHT, [CONTROL_PORCH], light=LIGHT_CONTROL,
         flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=STEEL)
    for name, rect in CONTROL_WINDOWS.items():
        zone(name, WINDOW_SILL, WINDOW_TOP, [rect], light=LIGHT_CONTROL, flat=FLOOR_PLATE,
             ceiling=CEIL_CONCRETE, wall=STEEL)
    for n, rect in enumerate(CONSOLES, start=1):
        like("z6_control", f"{PROP_PREFIX}z6_console_{n}", [rect], floor=CATWALK + CONSOLE,
             flat=FLOOR_PLATE, wall=CONTROL_PANEL)
    for name, (rect, _face) in CONTROL_BOARDS.items():
        like("z6_control", name, [rect])
    like("z6_control", f"{PROP_PREFIX}z6_mural_niche", [CONTROL_MURAL_NICHE], floor=CATWALK + MURAL_SILL)
    zone("z6_swa_niche", CATWALK, CATWALK + SWITCH_HEIGHT, [SWA_NICHE], light=LIGHT_CONTROL,
         flat=FLOOR_TILE, wall=STEEL)
    zone("z6_cable_porch", CATWALK, CATWALK + DOOR_HEIGHT, [CABLE_PORCH], light=LIGHT_CONTROL,
         flat=FLOOR_TILE, wall=STEEL)
    cable_shutter = door("shutter_cable", CATWALK, TAG_CABLE_SHUTTER, CABLE_SHUTTER, light=LIGHT_GALLERY)

    # ======================================================================
    # The cable gallery, up to the substation
    # ======================================================================
    ky1, ky2 = CABLE_Y
    zone("z8_cable_gallery", CATWALK, CATWALK + GALLERY_HEIGHT, [(CABLE_FLAT[0], ky1, CABLE_FLAT[1], ky2)],
         light=LIGHT_GALLERY, wall=TUNNEL)
    for n in range(1, CABLE_STAIR_STEPS + 1):
        x = CABLE_FLAT[1] + STEP_RUN * (n - 1)
        f = CATWALK + STEP * n
        zone(f"z8_cable_stair_{n}", f, f + GALLERY_HEIGHT, [(x, ky1, x + STEP_RUN, ky2)],
             light=LIGHT_GALLERY, wall=TUNNEL)
    zone("z8_cable_top", CREST, ROOF, [(CABLE_TOP[0], ky1, CABLE_TOP[1], ky2)],
         light=LIGHT_GALLERY, wall=TUNNEL)

    # ======================================================================
    # The substation: transformers, the blue key, SW-B
    # ======================================================================
    zone("z9_substation", CREST, SKY_CEIL, [SUBSTATION], light=LIGHT_OUTDOORS, ceiling=SKY, wall=RUST)
    sx1, _sy1, sx2, _sy2 = SUBSTATION
    for side, fy, out in (("s", FENCE_SIDES_Y[0], -1), ("n", FENCE_SIDES_Y[1], 1)):
        strip, verge = sorted((fy, fy + out * FENCE_STRIP)), sorted((fy + out * FENCE_STRIP, fy + out * 2 * FENCE_STRIP))
        zone(f"{PROP_PREFIX}z9_fence_{side}", CREST, CREST + FENCE_HEIGHT, [(sx1, strip[0], sx2, strip[1])],
             light=LIGHT_OUTDOORS, ceiling=SKY, wall=RUST)
        zone(f"{PROP_PREFIX}z9_verge_{side}", CREST, CREST, [(sx1, verge[0], sx2, verge[1])],
             light=LIGHT_OUTDOORS, ceiling=SKY, wall=RUST)
    for n, rect in enumerate(TRANSFORMERS, start=1):
        zone(f"{PROP_PREFIX}z9_transformer_{n}", CREST + TRANSFORMER, SKY_CEIL, [rect],
             light=LIGHT_OUTDOORS, flat=FLOOR_PLATE, ceiling=SKY, wall=STEEL)
    for rect in PYLONS:
        g.carve(*rect)
    zone("z9_gantry", CREST, GANTRY, [GANTRY_RECT], light=LIGHT_OUTDOORS, ceiling=FLOOR_PLATE, wall=STEEL)
    zone("z9_pad", CREST + PAD, SKY_CEIL, [BLUE_PAD], light=LIGHT_BEACON, flat=FLOOR_PLATE,
         ceiling=SKY, wall=STEEL, extra=BLUE_LIGHT)
    zone("z9_passage", CREST, ROOF, [STATION_PASSAGE], light=LIGHT_OUTDOORS, wall=BRICK)
    zone("z9_swb_niche", CREST, CREST + SWITCH_HEIGHT, [SWB_NICHE], light=LIGHT_OUTDOORS, wall=STEEL)
    station_shutter = door("shutter_station", CREST, TAG_STATION_SHUTTER, STATION_SHUTTER,
                           light=LIGHT_OUTDOORS)

    # ======================================================================
    # The spillway: the gallery out, the walkways, the water, the winch
    # ======================================================================
    zone("z7_gallery", GROUND, GALLERY_HEIGHT, [SPILL_GALLERY], light=LIGHT_GALLERY, wall=TUNNEL)
    zone("z7_east_walk", GROUND, SKY_CEIL, [EAST_WALK], light=LIGHT_SPILLWAY, ceiling=SKY, wall=DAM)
    zone("z7_channel", CHANNEL, SKY_CEIL, [CHANNEL_RECT], light=LIGHT_SPILLWAY, flat=WATER,
         ceiling=SKY, wall=DAM, extra=WATER_HURTS)
    zone("z7_west_walk", GROUND, SKY_CEIL, [WEST_WALK], light=LIGHT_SPILLWAY, ceiling=SKY, wall=DAM)
    wx1, _wy1, wx2, _wy2 = CHANNEL_RECT
    for k, (sy1, sy2) in enumerate(STEPS_Y, start=1):
        for n in range(1, 4):      # three steps up from the water on each bank
            f = CHANNEL + STEP * n
            east = wx2 - STEP_RUN * (4 - n)
            like("z7_channel", f"z7_steps_e{k}_{n}", [(east, sy1, east + STEP_RUN, sy2)], floor=f,
                 flat=FLOOR_CONCRETE, extra={})
            west = wx1 + STEP_RUN * (3 - n)
            like("z7_channel", f"z7_steps_w{k}_{n}", [(west, sy1, west + STEP_RUN, sy2)], floor=f,
                 flat=FLOOR_CONCRETE, extra={})
    zone("z7_winch", GROUND + PAD, GROUND + PAD + DOOR_HEIGHT, [WINCH], light=LIGHT_BEACON,
         flat=FLOOR_PLATE, ceiling=CEIL_PANEL, wall=STEEL, extra=YELLOW_LIGHT)
    # S1: the channel's outfall, at its south end, set back in shadow.
    zone("s1_niche", CHANNEL, CHANNEL + TILE, [S1_NICHE], light=LIGHT_SHADOW, flat=WATER, wall=DAM)
    s1_panel = zone("s1_panel", CHANNEL, CHANNEL, [S1_PANEL], TAG_S1_PANEL, light=LIGHT_SHADOW,
                    flat=WATER, wall=DAM)
    zone("s1_culvert", CHANNEL, CHANNEL + GALLERY_HEIGHT, [S1_CULVERT], light=LIGHT_SECRET, wall=TUNNEL)
    zone("s1_store", CHANNEL, CHANNEL + GALLERY_HEIGHT, [S1_STORE], light=LIGHT_SECRET, wall=TUNNEL,
         special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # The crest: the road west along the top of the dam
    # ======================================================================
    zone("z10_crest", CREST, SKY_CEIL, [CREST_RECT], light=LIGHT_OUTDOORS, flat=FLOOR_LANE,
         ceiling=SKY, wall=DAM, extra={"rotationfloor": 90.0})
    rails("z10_crest", "rails_z10_crest", CREST_RAILS)
    zone(f"{PROP_PREFIX}z10_parapet_n", CREST + PARAPET, PARAPET_SKY, [PARAPET_N],
         light=LIGHT_OUTDOORS, ceiling=SKY, wall=DAM)
    zone(f"{PROP_PREFIX}z10_parapet_s", CREST + PARAPET, PARAPET_SKY, [PARAPET_S],
         light=LIGHT_OUTDOORS, ceiling=SKY, wall=DAM)
    zone("z10_gate_porch", CREST, ROOF, [GATE_PORCH], light=LIGHT_OUTDOORS, wall=DAM)
    zone("z10_west_porch", CREST, ROOF, [WEST_PORCH], light=LIGHT_OUTDOORS, wall=DAM)
    for n, rect in enumerate(BARRICADES, start=1):
        zone(f"{PROP_PREFIX}z10_barricade_{n}", CREST + CRATES, SKY_CEIL, [rect],
             light=LIGHT_OUTDOORS, flat=CRATE_TOP, ceiling=SKY, wall=CRATE)
    # The two crane huts on the crest's south side: the west one open, the
    # east one (S3) shut by a corrugated gate that is a push panel.
    hx1, hx2 = HUT_FRONT_X["w"]
    zone("z10_hut_w", CREST, ROOF, [HUT_W], light=LIGHT_HUT, wall=RUST)
    zone("z10_hut_w_door", CREST, ROOF, [(hx1, PARAPET_S[1], hx2, PARAPET_S[3])], light=LIGHT_HUT, wall=RUST)
    zone("z10_hut_w_porch", CREST, ROOF, [(hx1, CREST_RECT[1], hx2, CREST_RECT[1] + 32)],
         light=LIGHT_OUTDOORS, wall=RUST)
    ex1, ex2 = HUT_FRONT_X["e"]
    zone("s3_hut", CREST, ROOF, [HUT_E], light=LIGHT_HUT, wall=RUST, special=SECTOR_SPECIAL_SECRET)
    s3_panel = zone("s3_panel", CREST, CREST, [(ex1, PARAPET_S[1], ex2, PARAPET_S[3])], TAG_S3_PANEL,
                    light=LIGHT_HUT, wall=RUST)
    zone("z10_hut_e_porch", CREST, ROOF, [(ex1, CREST_RECT[1], ex2, CREST_RECT[1] + 32)],
         light=LIGHT_OUTDOORS, wall=RUST)
    # The huts' fronts either side of the doorway and the panel are solid:
    # the parapet never touches a door or a doorway.
    for (fx1, fx2), (hut_x1, _hy1, hut_x2, _hy2) in ((HUT_FRONT_X["w"], HUT_W), (HUT_FRONT_X["e"], HUT_E)):
        g.carve(hut_x1, PARAPET_S[1], fx1, PARAPET_S[3])
        g.carve(fx2, PARAPET_S[1], hut_x2, PARAPET_S[3])
    d2 = door("d2_west", CREST, TAG_D2_WEST, WEST_DOOR, light=LIGHT_OUTDOORS)
    zone("z11_west_hall", CREST, ROOF, [WEST_HALL], light=LIGHT_GATEHOUSE, flat=FLOOR_TILE,
         ceiling=CEIL_PANEL, wall=TILE_DADO)
    zone("z11_exit_niche", CREST, CREST + SWITCH_HEIGHT, [EXIT_NICHE], light=LIGHT_BEACON, wall=STEEL)

    # ======================================================================
    # The station's closets, on the blue gate's tag
    # ======================================================================
    for name, (door_rect, room_rect) in STATION_CLOSETS.items():
        closet(name, door_rect, room_rect, TAG_STATION_AMBUSH, CREST, leaf=BRICK)

    # ======================================================================
    # Line styles. The FIRST rule registered on a segment wins, so the
    # specific ones (doors, panels, doorways) come before the parapets.
    # ======================================================================
    # The posters: each on its own one-sided line, whole.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    # Manual doors, both faces.
    for sector, (x1, y1, x2, y2), horizontal in ((d1, D1_DOOR, True), (d2, WEST_DOOR, False)):
        tag = tm.sectors[sector].identifier
        if horizontal:
            for yy in (y1, y2):
                g.style_h(yy, x1, x2, door_raise_style(tag, sector, texture=DOOR))
        else:
            for xx in (x1, x2):
                g.style_v(xx, y1, y2, door_raise_style(tag, sector, texture=DOOR))
    # The yellow door, both faces.
    for yy in (YELLOW_DOOR[1], YELLOW_DOOR[3]):
        g.style_h(yy, YELLOW_DOOR[0], YELLOW_DOOR[2],
                  locked_door_style(TAG_YELLOW_DOOR, yellow_door, LOCK_YELLOW_CARD, texture=DOOR_YELLOW))
    # The blue gate, both faces: the blue lock's leaf.
    for xx in (BLUE_GATE[0], BLUE_GATE[2]):
        g.style_v(xx, BLUE_GATE[1], BLUE_GATE[3],
                  locked_door_style(TAG_BLUE_GATE, blue_gate, LOCK_BLUE_CARD, texture=DOOR_BLUE))
    # The cable gallery's shutter: steel both sides, SW-A beside it.
    for xx in (CABLE_SHUTTER[0], CABLE_SHUTTER[2]):
        g.style_v(xx, CABLE_SHUTTER[1], CABLE_SHUTTER[3], remote_door_style(cable_shutter, texture=STEEL))
    g.style_v(SWA_NICHE[2], SWA_NICHE[1], SWA_NICHE[3],
              switch_door_open_style(TAG_CABLE_SHUTTER, texture=SW_A_FACE, repeatable=False))
    # The station's shutter: steel from the substation's passage; from the
    # station, the station's own brick (a shortcut found from behind).
    g.style_v(STATION_SHUTTER[0], STATION_SHUTTER[1], STATION_SHUTTER[3],
              remote_door_style(station_shutter, texture=STEEL))
    g.style_v(STATION_SHUTTER[2], STATION_SHUTTER[1], STATION_SHUTTER[3],
              remote_door_style(station_shutter, texture=BRICK))
    g.style_h(SWB_NICHE[3], SWB_NICHE[0], SWB_NICHE[2],
              switch_door_open_style(TAG_STATION_SHUTTER, texture=SW_B_FACE, repeatable=False))
    # The dam's face over the channel's north end: the spillway's trash rack,
    # the water running out under it (SDSPIL1 for the design's SDSLUC1).
    g.style_h(CHANNEL_RECT[3], CHANNEL_RECT[0], CHANNEL_RECT[2], LineStyle(texture=SPILLWAY))
    # The turbine hall's catwalk and its stair are steel in front of the
    # hall's concrete: their face to the hall and every riser.
    g.style_h(CATWALK_Y[0], HALL[0], HALL[2], LineStyle(texture=STEEL))
    for n in range(1, CATWALK_STAIR_STEPS + 1):
        g.style_v(HALL[0] + STEP_RUN * n, CATWALK_Y[0], CATWALK_Y[1], LineStyle(texture=STEEL))
    # The generators' columns: steel shafts out of the SDTURB1 housings.
    for cx in GENERATOR_X:
        x1, y1 = cx - COLUMN_HALF, GENERATOR_Y - COLUMN_HALF
        x2, y2 = cx + COLUMN_HALF, GENERATOR_Y + COLUMN_HALF
        for xx in (x1, x2):
            g.style_v(xx, y1, y2, LineStyle(texture=STEEL))
        for yy in (y1, y2):
            g.style_h(yy, x1, x2, LineStyle(texture=STEEL))
    # The substation's pylons: steel towers carrying the gantry.
    for x1, y1, x2, y2 in PYLONS:
        for xx in (x1, x2):
            g.style_v(xx, y1, y2, LineStyle(texture=STEEL))
        for yy in (y1, y2):
            g.style_h(yy, x1, x2, LineStyle(texture=STEEL))
    # The control room's boards: every edge of each strip impassable.
    for (x1, y1, x2, y2), _face in CONTROL_BOARDS.values():
        for xx in (x1, x2):
            g.style_v(xx, y1, y2, BOARD_EDGE)
        for yy in (y1, y2):
            g.style_h(yy, x1, x2, BOARD_EDGE)
    # The substation's fence: nobody crosses it.
    for fy in FENCE_SIDES_Y:
        g.style_h(fy, SUBSTATION[0], SUBSTATION[2], BLOCKING)
    # The armoured train's stars, and the signal at the end of its track.
    for axis, coord, lo, hi in TRAIN_STARS:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=ARMOUR_STAR))
    g.style_v(SIGNAL_POST[2], SIGNAL_POST[1], SIGNAL_POST[3], LineStyle(texture=SIGNAL))
    # The secrets' panels.
    for x_or_y in (S1_PANEL[1], S1_PANEL[3]):
        g.style_h(x_or_y, S1_PANEL[0], S1_PANEL[2], secret_panel_style(TAG_S1_PANEL, s1_panel, DAM))
    for x_or_y in (S2_PANEL[1], S2_PANEL[3]):
        g.style_h(x_or_y, S2_PANEL[0], S2_PANEL[2], secret_panel_style(TAG_S2_PANEL, s2_panel, CONCRETE))
    for x_or_y in (PARAPET_S[1], PARAPET_S[3]):
        g.style_h(x_or_y, ex1, ex2, secret_panel_style(TAG_S3_PANEL, s3_panel, ROAD_GATE))
    # The open hut's doorway and both huts' porches are walked through.
    g.style_h(PARAPET_S[3], hx1, hx2, LineStyle())
    g.style_h(CREST_RECT[1] + 32, hx1, hx2, LineStyle())
    g.style_h(CREST_RECT[1] + 32, ex1, ex2, LineStyle())
    # The parapets' crest-side edges: nobody crosses them, not even jumping
    # (the drop beyond the south one is the spillway, 448 down).
    g.style_h(PARAPET_S[3], PARAPET_S[0], PARAPET_S[2], BLOCKING)
    g.style_h(PARAPET_N[1], PARAPET_N[0], PARAPET_N[2], BLOCKING)
    g.style_h(STATION_PARAPET[1], STATION_PARAPET[0], STATION_PARAPET[2], BLOCKING)
    # The exit: the switch at the back of its niche, in the west bank's hall.
    g.style_v(EXIT_NICHE[0], EXIT_NICHE[1], EXIT_NICHE[3], exit_switch_style(texture=EXIT_FACE))

    g.build()

    # ======================================================================
    # Dressing the built lines: the waterline, one grid for the dam's
    # concrete, the machines' faces, the boards, the insulators
    # ======================================================================
    water = {plan["z7_channel"]} | {i for n, i in plan.items() if n.startswith("z7_steps_")}
    wet_the_banks(tm, water, water | {plan["z7_east_walk"], plan["z7_west_walk"]})
    # SDDAM1 world-aligned from the hall's floor; SDDAM2's and the rack's foot
    # on the water, so the tide mark runs 8 under the walkways' edge.
    align_to_world(tm, {DAM: GROUND, DAM_WET: CHANNEL, SPILLWAY: CHANNEL, ARMOUR: CREST})
    # The generators' housings, 48 high, show the foot of SDTURB1 (the lower
    # flange and the concrete plinth on the floor); the steel shafts rise
    # out of them.
    align_to_world(tm, {TURBINE: GROUND}, sectors={plan["z5_hall"]})
    # The consoles, 32 high, show the board's desk (rows 64-95).
    align_to_world(tm, {CONTROL_PANEL: CATWALK + CONSOLE + CONTROL_DESK_ROW}, sectors={plan["z6_control"]})
    for _rect, (axis, coord, lo, hi) in CONTROL_BOARDS.values():
        segment = (lo, coord, hi, coord) if axis == "h" else (coord, lo, coord, hi)
        hang(tm, segment, plan["z6_control"], CONTROL_PANEL)
    gx1, gy1, gx2, gy2 = GANTRY_RECT
    for xx in (gx1, gx2):
        hang(tm, (xx, gy1, xx, gy2), plan["z9_substation"], INSULATOR)
    # Round 2 (D113): the high-voltage fence and the window bars.
    for fy in FENCE_SIDES_Y:
        hang(tm, (SUBSTATION[0], fy, SUBSTATION[2], fy), plan["z9_substation"], FENCE)
    bar_the_windows(tm, plan)
    for ld in tm.linedefs:
        for side in (ld.sidefront, ld.sideback):
            if side is not None and tm.sidedefs[side].texturemiddle in (FENCE, GRILL):
                tm.sidedefs[side].offsetx = world_column(tm, ld, side) % FENCE_WIDTH

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START, angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD))
    tm.add_thing(Thing(x=BLUE_KEY_SPOT[0], y=BLUE_KEY_SPOT[1], type=ED_BLUE_CARD))
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
WALL_TEXTURES = ((DAM, DAM_WET, TURBINE, CONTROL_PANEL, SPILLWAY, INSULATOR, CONCRETE, STEEL, TILE_DADO,
                  TUNNEL, BRICK, RUST, ROAD_GATE, WINDOW, FLAG_REICH, FLAG_LEGION, CRATE, LENIN, STALIN,
                  MURAL, ARMOUR, ARMOUR_STAR, SIGNAL, GRILL, FENCE)
                 + DOOR_LEAVES + SWITCH_FACES + MARX_ENGELS)
FLAT_TEXTURES = (FLOOR_LANE, FLOOR_CONCRETE, FLOOR_TILE, CEIL_PANEL, CEIL_CONCRETE, CRATE_TOP,
                 RAILS, FLOOR_PLATE, GRATING, WATER)
BUILTIN_FLATS = (SKY,)
# Middle textures on two-sided lines, drawn once: the masked insulators, the
# control boards, the window bars and the substation's fence. Nothing else
# hangs in mid-air.
MIDDLE_TEXTURES = (INSULATOR, CONTROL_PANEL, GRILL, FENCE)
# Design section 7.2, settled: {lump the design proposed: the approved lump
# the map wears for it}. Proposed names the art-director drew are worn as
# themselves; the ones never drawn (no such lump in assets/) take the nearest
# approved piece (D107's set, or the approved lump that stood in).
DAM_SET = {
    "SDWATR1": WATER,           # drawn: the channel, S1's outfall (SDWATR2-4 by ANIMDEFS)
    "SDTURB1": TURBINE,         # drawn: the four generators' housings
    "SDTURB2": DAM,             # never drawn: the turbine hall wears the dam's own concrete
    "SDPANL1": CONTROL_PANEL,   # never drawn: four SDCTRL1 boards on the control room's walls
    "SDPANL2": CONTROL_PANEL,   # never drawn: SDCTRL1's desk on the two consoles
    "SDSLUC1": SPILLWAY,        # never drawn: the trash rack on the dam's face over the channel
    "SDHVLT1": FENCE,           # drawn (D113): the substation's fence, north and south, a two-sided line
    "SDDOORB": DOOR_BLUE,       # drawn (D113): the blue gate's leaf
    "SDGRIL1": GRILL,           # drawn (D113): bars in the control room's two windows over the hall
}
# Still waiting, with nothing standing in: {proposed lump: what and where}.
# Round 2 (D113) drew the last three; nothing of section 7.2 waits.
PENDING_TEXTURES: dict[str, str] = {}
