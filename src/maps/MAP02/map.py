"""MAP02 "Metro-bunker" - v1: the blue pass signposted, and the map populated.

Design document: docs/levels/MAP02-metro.md (v0 section 14, v1 section 16).
LORE's second campaign map (docs/product/LORE.md, "Metro-bunker tunnels:
first key, first heavy hybrids"). Built as MAP03 while MAP02 was the
practice range (D41); MAP02 since D62 (2026-10-14), when the slots began to
follow the campaign. The player arrives by the service lift MAP01 ends
on.

v0 (section 14) was the whole floor plan with nothing in it but the start
and the pass. The CEO walked it on 2026-10-14 (D58): "me gusta de momento",
but he never found the pass and crossed the blue door with idclip - MAP01's
v0/v1 failure again, a goal the map shows and a way to it the map does not.
v1 answers it the way MAP01 v1 and v2 did, by sight:

* the pass lies alone in the DUTY OFFICER'S BOOTH, a lit niche on the
  substation's side whose window looks onto the far east end of the hall:
  from the blue door, turning round, it is the brightest thing in the
  station and the pass is on its floor in plain view (tested sight lines);
* the booth and the blue door's portal share one blue light (lightcolor,
  NOT VERIFIED): the colour of the lock is the colour of where the key is;
* a yellow lane (SDFLR1, MAP01's word for "go here") comes down both staff
  stairs and runs along the track bed into the east tunnel, and ends at D3
  in a pool of light; the east staff stair is lit as a beacon;
* the window cannot be climbed or reached through: the way in is the track,
  the tunnel and D3, as in v0.

And section 9's population, placed: 23 / 36 / 51 monsters on skills 2 / 3 /
4 (the Legion holds the station, the Reich the depths, D35 inverted from
MAP01), the closets of SW-A on platform N and of SW-B in the west tunnel,
the three weapons on the route on every skill, and ammunition and health
scaled down by skill with G3-8's margin (tests/test_map02_metro.py).

The route, in one line: lift -> concourse -> escalator (the locked blast door
is seen at the far end of the hall from the top) -> hall (the lit booth and
the pass behind the player, seen on turning from the blue door) -> drop into
the open track down a staff stair -> the yellow lane east -> D3 under its
lamp -> substation, the BLUE PASS in the booth, and SW-A, which opens a
shutter back onto the platform and the closets there -> hall -> blast door
(blue) -> bunker -> command post, SW-B, which opens the tunnel gate, the
command post's own door onto the tunnel and the tunnel's closets -> west
tunnel -> exit.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP02 SKILL=3 tools/run.sh
"""

from __future__ import annotations

from sdbuild.events import door_open, event_thing
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

MAP_NAME = "MAP02"

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
CEIL_PANEL = "SDCEIL1"  # lit panel: the train's ceiling strip, the booth, D3's lamp
# The yellow lane (v1): MAP01's word for "go here", learnt in its hangar.
# SDFLR1 is the same concrete as the track bed's SDFLR2 with a worn yellow
# line on its columns 2..8 (TEXTURE-INDEX), i.e. along the image's y. Every
# lane here runs east-west, so it is turned a quarter (MAP01's LANE_ACROSS),
# and every lane strip is 64 wide on the 64 grid, so the line falls inside
# it whichever way the quarter turn goes (NOT VERIFIED which edge: K8).
LANE = "SDFLR1"
LANE_ALONG_X = {"rotationfloor": 90.0}

# Switches (D25): one variant per switch, for what it does. SDSW1C, unused
# by MAP01, goes to SW-A.
SW_A_FACE = "SDSW1C"    # substation: opens the platform shutter
SW_B_FACE = "SDSW1B"    # command post console: opens the tunnel gate
EXIT_FACE = "SDSW1D"    # hazard panel: the exit, as on MAP01 and the range
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

# --- The posters (CEO 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py) ---------------------------------
# A 128x256 portrait needs a one-sided wall exactly 128 long in a sector
# exactly 256 high, and the only 256 in this station is the 1941 shelter:
# the hall is 224, the platforms 160, everything else 128 (a niche taller
# than its room shows the poster's head only from close by). So the
# portraits are the shelter's red corner and the mural goes on the route,
# in the concourse, whose walls are exactly its 128.
LENIN = "SDPOSTR1"      # 128x256
STALIN = STALIN_POSTER  # 128x256, D55
MURAL = "SDPOSTR2"      # 128x128 cosmonautics mural
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
# (name, texture, axis, coord, lo, hi): one GridMap style per picture.
POSTERS = (
    # The concourse's west wall, beside the escalator's mouth: straight ahead
    # of the player as he steps out of the lift (a vestibule mosaic panel).
    ("concourse_mural", MURAL, "v", 3136, 960, 1088),
    # S1, the 1941 shelter. Stalin alone on the north wall, at the back of
    # his niche, facing the passage (section 8: the one place in a 1977
    # station where he can still hang).
    ("shelter_stalin", STALIN, "h", 1872, 3008, 3136),
    # Lenin on the west wall, on the left as the player comes in.
    ("shelter_lenin", LENIN, "v", 2880, 1664, 1792),
    # The Marx-Engels pair (D117): Marx on the east wall, facing Lenin
    # across the room; Engels round the corner to his right, on the south
    # wall beside the passage's mouth, facing Stalin.
    ("shelter_east_slot", MARX, "v", 3264, 1664, 1792),
    ("shelter_south_slot", ENGELS, "h", 1600, 3136, 3264),
)
POSTER_SLOTS_MARX_ENGELS = ("shelter_east_slot", "shelter_south_slot")   # Marx, Engels


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS


# --- Specials not in sdbuild.udmf ----------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag). The argument SHAPE is
# read from gzdoom.pk3 g4.14.2 -> xlat/base.txt, e.g. Doom's blue "open and
# stay" door, line 133: `Door_LockedRaise (tag, D_FAST, 0, BCard | ...)`: a
# delay of 0 is a door that opens and STAYS open, so the key gate can never
# be consumed. The NUMBER, 13, follows 10 Door_Close / 11 Door_Open /
# 12 Door_Raise (all three verified in engine on MAP01) in ZDoom's compiled
# table: VERIFIED on the v0 engine pass (K2, docs/qa/evidence/
# 2026-10-14_1902_F3_map03-v0-walk.md): locked without the pass, open for
# good with it.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock 2 is "Blue key card" in gzdoom.pk3 -> lockdefs.txt (`Lock 2 Doom
# { BlueCard ... }`): read from shipped text.
LOCK_BLUE_CARD = 2
ED_BLUE_CARD = 5        # Doom's BlueCard, replaced by SD_BluePass (MOD-SPEC 6); Freedoom's sprite

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

# --- Light -------------------------------------------------------------------
# v0: one value per zone. v1 adds the signs that lead to the pass (design
# section 16): 192 is kept for the lock and the key, and nothing else.
LIGHT_MIN = 96
LIGHT_MAX = 192
LAMP_STEP = 16
LIGHT_BEACON = LIGHT_MAX  # the lock (the portal) and the key (the booth): only they
LIGHT_LIFT = 128
LIGHT_CONCOURSE = 160
LIGHT_KASSA = 144
LIGHT_ESCALATOR = 144
LIGHT_HALL = 160
LIGHT_PORTAL = LIGHT_BEACON   # the blast door: the brightest thing at the hall's west end
LIGHT_BOOTH = LIGHT_BEACON    # the pass's niche: the brightest thing at its east end
LIGHT_ARCHES = 144
LIGHT_PLATFORM = 144
LIGHT_STAFF_STAIR = LIGHT_PLATFORM + 2 * LAMP_STEP   # 176: the east stair, the way down
LIGHT_TRACK = 112
LIGHT_TUNNEL = 96
LIGHT_D3_POOL = LIGHT_TUNNEL + 5 * LAMP_STEP          # 176: the lane ends in light at D3
LIGHT_TRAIN = 128
LIGHT_SUBSTATION = 144   # v0 128: one step brighter, the light rises towards the pass
LIGHT_SECRET = 112
LIGHT_BUNKER = 128
LIGHT_DORM = 112
LIGHT_CP = 128
LIGHT_CLOSET = 112       # inside a monster closet: unlit storage (MAP01's value)
LIGHT_ARMOURY_DARK = LIGHT_MIN               # V3 A2: the armoury before the RPG-7 is taken...
LIGHT_ARMOURY_LAMP = LIGHT_DORM + 2 * LAMP_STEP   # ...its one lamp, 144, the level it comes up to
LIGHT_EXIT = 144         # the exit niche: the one lit spot past the gate

# The pass's colour, in light (v1). Sector field `lightcolor` of the UDMF
# zdoom namespace, 0xRRGGBB (the field name from the UDMF zdoom spec, as
# Ultimate Doom Builder writes it); a pale cobalt, the mosaics' ground (D56).
# On the portal round the blue door and on the booth where the pass lies:
# from one, the other is the only blue light in the station. NOT VERIFIED in
# our engine runs (checklist L4); if the engine ignores it, both places
# are still the two 192s of the map.
PASS_BLUE = 0x90A8FF
PASS_LIGHT = {"lightcolor": PASS_BLUE}

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
# The monster closets ride the switches' own tags (MAP01 v3, section 17.3
# there: one line, one special): SW-A opens the shutter and the platform's
# closets, SW-B the gate, the command post's door and the tunnel's closets.
TAG_PLATFORM_AMBUSH = TAG_SHUTTER
TAG_TUNNEL_WAVE = TAG_GATE
# V3 A2, pickup events (docs/levels/PICKUP-EVENTS.md; design section 18).
# Each tag is carried by the sectors its event moves and by NO line.
TAG_EVENT_PASS = 12      # the blue pass: the duty window opens up, a way back into the hall
TAG_EVENT_RPG = 13       # the RPG-7: the armoury's store opens...
TAG_EVENT_RPG_LIGHTS = 14  # ...and, as it rises, the armoury's lights come up (Door_Open's lighttag)

# --- The duty officer's booth (v1): the pass's lit niche ----------------------
# A raised booth in the substation's south-west corner, two steps up, with a
# window onto the hall's east end. The pass lies on its floor; the window's
# sill is the booth's floor, so from anywhere along the hall's axis the eye
# (41 over the hall floor) looks across the sill onto the pass. The window
# is shorter than a player (48 < 56): seen through, never climbed through,
# jump or no jump; and the pass lies further from it than a player's and a
# pickup's radii together, so it is not taken through it either (tested).
BOOTH = (2848, 1024, 2944, 1088)
BOOTH_STEP = (2944, 1024, 2976, 1088)
DUTY_WINDOW = (2816, 1024, 2848, 1088)   # in the hall's east wall, x 2816
BOOTH_FLOOR = 2 * STEP                   # 32: two steps up from the substation
WINDOW_TOP = BOOTH_FLOOR + 48            # 80: a 48-high slot, under a player's 56

# --- The lane and the rails (v1) ------------------------------------------
# The track bed is 128 wide: the walkway with its yellow lane on the
# platform side, the rails on the outer side. v0 had the rails in the
# middle, which left 32 either side: too narrow to be sure the lane's line
# shows. Both strips are 64 wide on the 64 grid.
LANE_Y = (1344, 1408)
RAIL_Y = (1408, 1472)
LANE_X = (1344, 3072)    # from the west staff stair's foot to D3's east jamb

# --- Things --------------------------------------------------------------------
PLAYER_START = (3776, 896)
PLAYER_ANGLE = 180       # facing west, at D1
KEY_SPOT = (2896, 1056)  # alone in the duty officer's booth (v1; v0 2976 1088)
KEY_ZONE = "z8_booth"

# --- Pickup events (V3 A2; design section 18) ----------------------------------
# The pass: the station wall over the duty window (its head, 80) slides up
# like a door, to the booth's ceiling less 4 (124). The 48-high slot becomes
# a doorway one way: down from the booth (32) into the hall (0), on the blue
# door's axis, the pass in hand; from the hall the booth is still 32 up, more
# than a step, so the way IN is still the track and D3. Sinking the sill
# instead would leave a 48 gap at the booth's floor, under a body (tested).
# The route never needs it (rule R3): the way back by D3 and the track, or by
# SW-A's shutter, is still there.
PASS_EVENT = door_open("pass_window", TAG_EVENT_PASS)
# The RPG-7: the armoury is dark but for the lamp over the launcher's rack;
# taking it opens the store in the north wall (the Reich's guards) and, as the
# panel rises, the armoury comes up to the lamp's light (Door_Open's light
# tag: each tagged sector goes to its brightest neighbour's level, MAP01's
# SW-A, VERIFIED there).
RPG_EVENT = door_open("rpg_alarm", TAG_EVENT_RPG, lighttag=TAG_EVENT_RPG_LIGHTS)
CLOSET_ARMOURY = ((400, 1024, 528, 1040), (384, 1040, 544, 1152))   # panel, store
ARMOURY_LAMP = (384, 768, 448, 832)      # the pool of light the RPG-7 lies in

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design (turnstiles)
WINDOWS = ("duty_window",)       # seen through, never walked
SECRET_ZONES = ("s1_shelter", "s2_cab")
LANE_PREFIX = "lane_"
CLOSET_PREFIX = "closet_"
CLOSET_HEIGHT = 128      # a monster closet: one panel high, as on MAP01

# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
# The bestiary's own numbers (21100-21105, BESTIARY 2.5): MAPINFO assigns them
# and each class also `replaces` its Doom twin. MAP01 places the Doom twins
# (it was populated before the bestiary existed); this map uses ours.
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich, 20 HP
ED_TROOPER = 21101        # SD_LegionTrooper, Legion, 30 HP
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both factions, 60 HP
ED_HOUND = 21103          # SD_ReichHound, Reich, 150 HP
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, 400 HP
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich, 500 HP
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
}
MONSTER_CLASSES = {
    ED_RIFLEMAN: "SD_ReichRifleman",
    ED_TROOPER: "SD_LegionTrooper",
    ED_STORMTROOPER: "SD_Stormtrooper",
    ED_HOUND: "SD_ReichHound",
    ED_DOUGHBOY: "SD_Doughboy",
    ED_PANZERMENSCH: "SD_Panzermensch",
}
REICH = ("rifleman", "hound", "panzermensch")
LEGION = ("trooper", "doughboy")
# The arsenal (MAPINFO DoomEdNums, 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7)
# V3 A2: what each event rides on. The pass is a key (always taken); nothing
# drops an RPG-7, so the armoury's is always taken too (rule R7).
PICKUP_EVENTS = {ED_BLUE_CARD: PASS_EVENT, ED_RPG7: RPG_EVENT}
EVENT_CLOSETS = {"closet_armoury": (RPG_EVENT, CLOSET_ARMOURY)}
# Ammo, health and armour: Doom's numbers, which our classes replace
# (src/zscript/sd/ammo.zs; MOD-SPEC 6.4), as on MAP01.
ED_CLIP = 2007            # 10 rounds of 7.62x25
ED_CLIP_BOX = 2048        # 50
ED_SHELLS = 2008          # 4 shells
ED_SHELL_BOX = 2049       # 20
ED_ROCKET_BOX = 2046      # 5 PG-7V
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019
ED_BACKPACK = 8

# Design section 9: monsters per skill, Doom's skill pairs (udmf.skill_tier).
# V3 A2 adds the armoury's two guards on every skill.
ENEMY_TOTALS = {2: 25, 3: 38, 4: 53}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Tier 2 is on
# every skill, 3 from medium up, 4 on hard only. Section 9's table, placed
# (section 16.4 for the two changes to it). D35 inverted from MAP01: the
# Liberty Legion holds the station, the Fourth Reich the depths.
MONSTERS = (
    # Concourse and kassa: the Legion's picket at the turnstiles, facing D1.
    ("z2_concourse", "trooper", 3200, 1100, 0, 2),
    ("z2_concourse", "trooper", 3200, 700, 0, 2),
    ("z2_kassa", "trooper", 3360, 1290, 270, 3),
    ("z2_concourse", "stormtrooper", 3200, 896, 0, 4),
    # The escalator shaft, the map's one tall room: the Doughboy.
    ("esc_6", "doughboy", 2976, 896, 0, 3),
    # The hall, first big fight: the Legion between the pylons, facing the
    # escalator they expect the player down.
    ("z3_hall", "trooper", 1700, 760, 0, 2),
    ("z3_hall", "trooper", 2200, 1030, 0, 2),
    ("z3_hall", "trooper", 2500, 760, 0, 2),
    ("z3_hall", "trooper", 1500, 1030, 0, 2),
    ("z3_hall", "stormtrooper", 2000, 760, 0, 2),
    ("z3_hall", "trooper", 2650, 1030, 0, 3),
    ("z3_hall", "stormtrooper", 1900, 1030, 0, 3),
    ("z3_hall", "trooper", 1450, 760, 0, 4),
    ("z3_hall", "stormtrooper", 2350, 1030, 0, 4),
    # The train: a parallel corridor, facing its open doors.
    ("z6_train", "trooper", 1500, 376, 90, 2),
    ("z6_train", "trooper", 2250, 376, 90, 2),
    ("z6_train", "trooper", 1850, 376, 90, 3),
    ("z6_train", "trooper", 2600, 376, 90, 4),
    ("z6_train", "stormtrooper", 2000, 376, 90, 4),
    # The track and the east tunnel: the Reich's hounds in the dark.
    ("rails_z7_tunnel_e", "hound", 3100, 1440, 180, 2),
    ("rails_z5_track", "rifleman", 2300, 1440, 180, 2),
    ("rails_z7_tunnel_e", "hound", 2900, 1440, 180, 3),
    ("rails_z5_track", "rifleman", 1800, 1440, 0, 3),
    ("rails_z5_track", "hound", 1500, 1440, 0, 4),
    # The substation: the pass's guard, facing the stair up from D3.
    ("z8_substation", "rifleman", 3040, 1056, 90, 2),
    ("z8_substation", "rifleman", 2920, 1120, 90, 2),
    ("z8_substation", "stormtrooper", 3040, 1150, 90, 3),
    ("z8_substation", "rifleman", 2992, 1180, 90, 4),
    # SW-A's closets on platform N (tag 10): the counter-attack on ground
    # already cleared, as the player comes back through the shutter.
    ("closet_pw", "stormtrooper", 1216, 1200, 0, 2),
    ("closet_pe", "stormtrooper", 2856, 1256, 180, 2),
    ("closet_pw", "hound", 1216, 1290, 0, 3),
    ("closet_pe", "stormtrooper", 2904, 1256, 180, 4),
    ("closet_pe", "trooper", 2880, 1304, 180, 4),
    # The bunker: the Reich at home.
    ("b1_vestibule", "rifleman", 1120, 896, 0, 2),
    ("b2_spine", "rifleman", 800, 900, 0, 2),
    ("b2_spine", "hound", 650, 896, 0, 2),
    ("b3_dorm", "rifleman", 700, 600, 90, 2),
    ("b3_dorm", "rifleman", 950, 650, 90, 3),
    ("b2_spine", "stormtrooper", 1000, 880, 0, 3),
    ("b5_armoury", "rifleman", 460, 980, 270, 4),
    # V3 A2: the armoury's guards, in the store the RPG-7's pickup opens.
    ("closet_armoury", "rifleman", 424, 1096, 270, 2),
    ("closet_armoury", "stormtrooper", 504, 1096, 270, 2),
    ("b3_dorm", "hound", 850, 650, 90, 4),
    # The command post: the Panzermensch at the console, on every skill.
    ("b4_cp", "panzermensch", 960, 1220, 270, 2),
    ("b4_cp", "rifleman", 1100, 1150, 270, 4),
    # SW-B's closets in the west tunnel's north wall (tag 11): the climax.
    ("closet_t1", "rifleman", 920, 1512, 270, 2),
    ("closet_t2", "rifleman", 1110, 1512, 270, 2),
    ("closet_t1", "hound", 990, 1565, 270, 3),
    ("closet_t2", "rifleman", 1190, 1512, 270, 4),
    ("closet_t2", "hound", 1150, 1565, 270, 4),
    # The exit tunnel: stragglers; on skill 4 a second Panzermensch.
    ("z9_exit_tunnel", "rifleman", 500, 1376, 0, 2),
    ("z9_exit_tunnel", "rifleman", 600, 1376, 0, 3),
    ("rails_z9_exit_tunnel", "panzermensch", 450, 1420, 0, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on - 4 = every skill, 3 = medium and easier, 2 = easy
# only). Weapons and everything inside a secret are on every skill.
ITEMS = (
    # The weapons, on every skill, on the route, before the heavies.
    ("z2_kassa", ED_IZH, 3300, 1300, 4),
    ("z6_train", ED_PPSH, 1760, 340, 4),
    ("b5_lamp", ED_RPG7, 420, 800, 4),
    ("b5_armoury", ED_ROCKET_BOX, 420, 1000, 4),
    # S1, the 1941 shelter's stores.
    ("s1_shelter", ED_BLUE_ARMOR, 3072, 1700, 4),
    ("s1_shelter", ED_BACKPACK, 2950, 1650, 4),
    ("s1_shelter", ED_MEDIKIT, 3200, 1650, 4),
    ("s1_shelter", ED_MEDIKIT, 3200, 1750, 4),
    ("s1_shelter", ED_CLIP_BOX, 2950, 1780, 4),
    # S2, the west cab.
    ("s2_cab", ED_SHELL_BOX, 1312, 350, 4),
    ("s2_cab", ED_ARMOR_BONUS, 1296, 404, 4),
    ("s2_cab", ED_ARMOR_BONUS, 1328, 404, 4),
    # Stimpacks: 4 on every skill, +2 medium, +2 easy.
    ("z2_kassa", ED_STIMPACK, 3290, 1240, 4),
    ("z6_cab_e", ED_STIMPACK, 2784, 340, 4),
    ("z8_substation", ED_STIMPACK, 2900, 1200, 4),
    ("b2_spine", ED_STIMPACK, 1020, 940, 4),
    ("z4_platform_n", ED_STIMPACK, 2000, 1200, 3),
    ("b3_dorm", ED_STIMPACK, 600, 540, 3),
    ("z3_hall", ED_STIMPACK, 2700, 1060, 2),
    ("z9_exit_tunnel", ED_STIMPACK, 720, 1400, 2),
    # Medikits outside S1: 3 on every skill, +1 medium, +1 easy.
    ("z8_substation", ED_MEDIKIT, 3040, 1200, 4),
    ("b5_armoury", ED_MEDIKIT, 500, 790, 4),
    ("b4_cp", ED_MEDIKIT, 790, 1290, 4),
    ("z4_platform_s", ED_MEDIKIT, 2600, 600, 3),
    ("b1_vestibule", ED_MEDIKIT, 1220, 850, 2),
    # Armour: the flak vest in the armoury; plates by the blue door, in the
    # kassa, the dorm and on the substation stair; two more on the platform
    # on skills 1-3.
    ("b5_armoury", ED_GREEN_ARMOR, 460, 900, 4),
    ("z3_portal", ED_ARMOR_BONUS, 1312, 800, 4),
    ("z3_portal", ED_ARMOR_BONUS, 1312, 990, 4),
    ("z2_kassa", ED_ARMOR_BONUS, 3420, 1240, 4),
    ("b3_dorm", ED_ARMOR_BONUS, 1040, 540, 4),
    ("b3_dorm", ED_ARMOR_BONUS, 1040, 740, 4),
    ("sub_stair_1", ED_ARMOR_BONUS, 3008, 1296, 4),
    ("z4_platform_n", ED_ARMOR_BONUS, 1500, 1200, 3),
    ("z4_platform_n", ED_ARMOR_BONUS, 2500, 1200, 3),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z1_lift", ED_HEALTH_BONUS, 3700, 800, 4),
    ("stair_e1", ED_HEALTH_BONUS, 2592, 1312, 4),
    ("stair_w1", ED_HEALTH_BONUS, 1504, 1312, 4),
    ("z3_portal", ED_HEALTH_BONUS, 1300, 720, 4),
    ("z3_portal", ED_HEALTH_BONUS, 1300, 1070, 4),
    ("sub_stair_2", ED_HEALTH_BONUS, 3008, 1264, 4),
    ("z8_passage", ED_HEALTH_BONUS, 2864, 1184, 4),
    ("b3_doorway", ED_HEALTH_BONUS, 832, 800, 4),
    ("z6_cab_e", ED_HEALTH_BONUS, 2800, 420, 4),
    ("z2_kassa", ED_HEALTH_BONUS, 3440, 1330, 4),
)

# D119 (the CEO's playtest: "siempre sale de sobras", "siempre acabas con la
# escopeta"), applied as docs/engine/BALANCE.md section 8 rules it: the
# ammunition scales UP with the monsters, the other way from the consumables
# above, so every skill sits in its band of what killing everything takes
# (skill 2 1.5-2.0, skill 3 1.3-1.6, skill 4 1.2-1.45); shells, the Legion's
# dropped IZhs counted, are no more than 35 % of it; and at every stage of the
# route the newest weapon's pool leads the rest. Each spot is one an earlier
# version already used for ammunition, so every pickup still stands where it
# was checked to be walkable and reachable. (zone, editor number, x, y,
# LOWEST skill tier it appears on - 2 = every skill, 3 = medium and up, 4 =
# hard only, as a monster scales.)
AMMO = (
    # The station, the TT-33, then the IZh in the kassa, then the PPSh on
    # the train: rounds lead; four shells by the IZh, more from skill 3.
    ("z2_concourse", ED_CLIP, 3520, 680, 2),
    ("z2_kassa", ED_SHELLS, 3420, 1300, 2),
    ("z3_hall", ED_CLIP_BOX, 1450, 1060, 2),
    ("z6_train", ED_CLIP_BOX, 1840, 400, 2),
    ("z8_substation", ED_CLIP_BOX, 3050, 1040, 2),
    ("z5_track", ED_CLIP_BOX, 1312, 1376, 2),
    ("z3_hall", ED_SHELLS, 1400, 760, 3),
    ("z7_tunnel_e", ED_CLIP_BOX, 3150, 1376, 3),
    ("z6_train", ED_CLIP_BOX, 2600, 340, 3),
    ("z4_platform_s", ED_CLIP_BOX, 1400, 600, 3),
    ("z3_hall", ED_SHELLS, 2750, 1040, 4),
    ("z8_substation", ED_CLIP_BOX, 3050, 1120, 4),
    # The bunker, the RPG-7 the newest (its box is in ITEMS, beside it): a
    # second box of PG-7V from skill 3, rounds under them.
    ("b3_dorm", ED_CLIP_BOX, 620, 740, 2),
    ("b4_cp", ED_CLIP_BOX, 1130, 1290, 2),
    ("b5_armoury", ED_ROCKET_BOX, 500, 1000, 3),
    # V3 A2: the guards' rounds, in the store the RPG-7 opens: what their two
    # kills cost on skills 3 and 4 inside BALANCE 8.2's floors.
    ("closet_armoury", ED_CLIP_BOX, 464, 1128, 3),
    ("b1_vestibule", ED_SHELLS, 1200, 940, 4),
    ("b2_spine", ED_CLIP_BOX, 620, 940, 4),
    ("b2_spine", ED_CLIP_BOX, 700, 850, 4),
    # SW-B's tunnel and the exit: rounds for skill 4's stragglers (the PG-7V
    # stay the bunker's, the command post's Panzermensch being the map's
    # heavy set piece: BALANCE 8.4 keeps rockets to 30 % elsewhere).
    ("z9_exit_tunnel", ED_CLIP_BOX, 700, 1360, 4),
)

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
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
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

    def rails(room: str, x1: int, x2: int) -> None:
        """The rail strip on the outer half of a 128-wide track bed (v1; v0
        had it in the middle): SDRAIL1 runs its rails along the image's y,
        so a track laid along x turns it a quarter (rotationfloor 90; NOT
        VERIFIED which way, either reads)."""
        like(room, f"rails_{room}", [(x1, RAIL_Y[0], x2, RAIL_Y[1])], flat=RAILS,
             extra={"rotationfloor": 90.0})

    def lane(room: str, name: str, x1: int, x2: int, **kw) -> int:
        """A strip of the yellow lane on the walkway half of a track bed."""
        return like(room, f"{LANE_PREFIX}{name}", [(x1, LANE_Y[0], x2, LANE_Y[1])],
                    flat=LANE, extra=dict(LANE_ALONG_X), **kw)

    def closet(name: str, door_rect, room_rect, tag: int, *, floor: int, leaf: str) -> int:
        """A monster closet (MAP01 v3's): a panel in a wall that opens for
        good with the switch that owns `tag`, together with that switch's
        gate. The panel and the closet wear the wall they are cut into, so
        it is wall until it moves; nothing closes it again, and the closet
        is a dead end the player walks out of."""
        door_index = zone(f"{name}_door", floor, floor, [door_rect], tag,
                          light=LIGHT_CLOSET, wall=leaf)
        zone(name, floor, floor + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

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
    # v1: in the pass's blue light (PASS_LIGHT), as the booth is.
    zone("z3_portal", STATION_FLOOR, ARCH_CEIL, [(1280, 704, 1344, 1088)],
         light=LIGHT_PORTAL, flat=FLOOR_HALL, ceiling=CEIL_COFFER, wall=MARBLE,
         extra=PASS_LIGHT)
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
    # v1: both wear the yellow lane, which carries on along the track bed;
    # the east one, the way to the pass, is lit from a lamp above it.
    for side, xs in (("w", (1472, 1408, 1344)), ("e", (2560, 2624, 2688))):
        lit = side == "e"
        for n, x in enumerate(xs, start=1):
            like("z4_platform_n", f"stair_{side}{n}", [(x, 1280, x + 64, 1344)],
                 floor=STATION_FLOOR - STEP * n, flat=LANE, extra=dict(LANE_ALONG_X),
                 light=LIGHT_STAFF_STAIR if lit else LIGHT_PLATFORM,
                 ceiling=CEIL_LAMP if lit else CEIL_COFFER)
    zone("z4_platform_s", STATION_FLOOR, PLATFORM_CEIL, [(1280, 448, 2816, 640)],
         light=LIGHT_PLATFORM, flat=FLOOR_GRANITE, ceiling=CEIL_COFFER, wall=STATION)

    zone("z5_track", TRACK, PLATFORM_CEIL, [(1280, 1344, 2816, 1472)],
         light=LIGHT_TRACK, wall=TILE)
    rails("z5_track", 1280, 2816)
    # The yellow lane, from the west staff stair's foot along the platform
    # face to the tunnel mouth; it carries on to D3 below.
    lane("z5_track", "track", LANE_X[0], 2816)

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
    rails("z7_tunnel_e", 2816, 3200)
    lane("z7_tunnel_e", "tunnel_e", 2816, 2944)
    # ...and ends in light at D3: a lamp panel over the door, the leaf lit
    # by it in a tunnel at 96.
    lane("z7_tunnel_e", "d3", 2944, LANE_X[1], light=LIGHT_D3_POOL, ceiling=CEIL_PANEL)
    d3 = door("d3", TRACK, TAG_D3_SUBSTATION, (2944, 1312, 3072, 1344), light=LIGHT_SUBSTATION)
    # Three steps up from the track to the substation, under the tunnel's
    # own ceiling: D3's leaf is then one tile high from both sides.
    for n, y in enumerate((1280, 1248, 1216), start=1):
        zone(f"sub_stair_{n}", TRACK + STEP * n, TUNNEL_CEIL, [(2944, y, 3072, y + 32)],
             light=LIGHT_SUBSTATION)
    zone("z8_substation", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT,
         [(2880, 1024, 3072, 1216)], light=LIGHT_SUBSTATION)
    like("z8_substation", "z8_passage", [(2848, 1152, 2880, 1216)])
    # v1, the duty officer's booth: the pass's lit niche, two steps up in
    # the substation's south-west corner, glazed onto the hall's east end
    # (design section 16.1). The window is DUTY_WINDOW, in the hall's wall.
    like("z8_substation", "z8_booth_step", [BOOTH_STEP], floor=STEP)
    zone("z8_booth", BOOTH_FLOOR, STATION_FLOOR + DOOR_HEIGHT, [BOOTH],
         light=LIGHT_BOOTH, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE, extra=PASS_LIGHT)
    zone("duty_window", BOOTH_FLOOR, WINDOW_TOP, [DUTY_WINDOW], PASS_EVENT.tag,
         light=LIGHT_BOOTH, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=STATION, extra=PASS_LIGHT)
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
    # V3 A2: dark until the RPG-7 is taken (the light tag of its event), but
    # for the lamp over the launcher's rack in the south-west corner.
    zone("b5_armoury", STATION_FLOOR, STATION_FLOOR + DOOR_HEIGHT, [(384, 768, 544, 1024)],
         TAG_EVENT_RPG_LIGHTS, light=LIGHT_ARMOURY_DARK, wall=STEEL)
    like("b5_armoury", "b5_lamp", [ARMOURY_LAMP], light=LIGHT_ARMOURY_LAMP, ceiling=CEIL_PANEL)
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
    rails("z7_tunnel_w", 896, 1280)
    gate = door("gate", TRACK, TAG_GATE, (768, 1344, 832, 1472), light=LIGHT_TUNNEL)
    zone("z9_exit_tunnel", TRACK, TUNNEL_CEIL, [(384, 1344, 768, 1472)],
         light=LIGHT_TUNNEL, wall=TUBBING)
    rails("z9_exit_tunnel", 384, 704)
    zone("z9_exit_niche", TRACK, TUNNEL_CEIL, [(352, 1376, 384, 1440)],
         light=LIGHT_EXIT, wall=TUNNEL)

    # ======================================================================
    # v1: the monster closets (design section 16.4)
    # ======================================================================
    # SW-A's, in platform N's two end walls: marble panels in marble walls.
    closet("closet_pw", (1264, 1184, 1280, 1312), (1168, 1168, 1264, 1328),
           TAG_PLATFORM_AMBUSH, floor=STATION_FLOOR, leaf=STATION)
    closet("closet_pe", (2816, 1232, 2832, 1328), (2832, 1232, 2928, 1328),
           TAG_PLATFORM_AMBUSH, floor=STATION_FLOOR, leaf=STATION)
    # SW-B's, in the west tunnel's north wall: one tubbing ring each.
    closet("closet_t1", (896, 1472, 1024, 1488), (880, 1488, 1040, 1600),
           TAG_TUNNEL_WAVE, floor=TRACK, leaf=TUBBING)
    closet("closet_t2", (1088, 1472, 1216, 1488), (1072, 1488, 1232, 1600),
           TAG_TUNNEL_WAVE, floor=TRACK, leaf=TUBBING)
    # V3 A2: the armoury's store, opened by the RPG-7's pickup (design
    # section 18): a steel panel in the armoury's steel north wall.
    for name, (event, (panel, store)) in EVENT_CLOSETS.items():
        closet(name, panel, store, event.tag, floor=STATION_FLOOR, leaf=STEEL)

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
    # The posters: Stalin's slot in S1's niche, Lenin and the Marx-Engels
    # slots on the shelter's other walls, the mural in the concourse.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))

    # The platform face towards the open track: 64 high, one SDMEDG1 tile,
    # hung from its top edge.
    g.style_h(1344, 1536, 2560, LineStyle(texture=EDGE, peg_bottom=False))

    g.build()

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(event_thing(KEY_SPOT[0], KEY_SPOT[1], ED_BLUE_CARD, PASS_EVENT))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle))
    for _zone, ednum, x, y, top in ITEMS:
        if ednum in PICKUP_EVENTS:
            tm.add_thing(event_thing(x, y, ednum, PICKUP_EVENTS[ednum]))
        else:
            tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top)))
    for _zone, ednum, x, y, lowest in AMMO:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(lowest)))
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
                 TUBBING, EDGE, STEEL, DOOR, STALIN_POSTER, LENIN, MURAL) + SWITCH_FACES     + MARX_ENGELS
FLAT_TEXTURES = (FLOOR_GRANITE, FLOOR_HALL, FLOOR_COPING, RAILS, CEIL_COFFER,
                 CEIL_LAMP, FLOOR_CONCRETE, FLOOR_TILE, CEIL_CONCRETE, CEIL_PANEL, LANE)
