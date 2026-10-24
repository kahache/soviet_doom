"""MAP01 "Zarya-7 Cosmodrome" - v3, density, combat and resources.

Design document: docs/levels/MAP01-zarya-7.md. This file builds v3 of its
section 12 version plan (build record in section 17). v3 keeps the v2 plan
and the v2 flow exactly - the same rooms in the same places, the same gate
(SW-A -> D4, SW-B -> D5), the same signs - and fills it:

* SHAPE: every big box gets structure. Columns on plinths and wall
  pilasters in the hangar, a south gantry with its stair, a raised spine on
  the transporter cradle with rails running out from under it, a landing
  on the catwalk stair and columns along its edge; bunks, the ice-axe rack and
  door frames in the dorm; shower stalls and a counter in the washroom;
  bulkheads and an ammo alcove in the corridor; mess tables, a colonnade
  and a tribune in the komnata; pipes and a weapon rack in the service
  corridor; fuel tanks and a drain in the fuel bay; niches in the airlock;
  the lift platform and Lenin's own light in the exit room.
* COMBAT (design section 8): Freedoom actors as stand-ins for the bestiary,
  placed per skill tier, Reich first and the Liberty Legion holding the
  hangar (D35). The fuel-bay ambush rides SW-A's door tag and the hangar's
  second wave rides SW-B's: one switch line, one special, and the closets
  open with the door that switch already opens.
* RESOURCES: the tutorial weapons where section 2 puts them, ammo and
  health scaled down by skill, the three secrets re-hidden (the v2 walk:
  "era muy evidente").
* THE RADIO (D43, design section 17.16): one diegetic radio in the guard
  post, playing "Kolokolchik" in place of the level's music while the
  player is in the post.

The night-sky strip over the hangar is still open with the CEO (design
section 13, point 5) and is deliberately NOT built.

Geometry is painted, not wound by hand: `GridMap` (tools/sdbuild/udmf.py)
takes axis-aligned rectangles of sector (and, since v3, rectangles of
solid void: columns) and works out every edge, wall and winding.

Run it:
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP01 tools/run.sh
"""

from __future__ import annotations

from sdbuild.events import door_open, event_thing
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
    skill_tier,
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
STALIN = "SDPOSTR3"   # 128x256 Stalin poster (D55), Lenin's twin

LANE = "SDFLR1"       # hangar concrete with the yellow lane line
CONCRETE_FLOOR = "SDFLR2"
TILE = "SDFLR3"       # grey Soviet floor tiles: the inhabited half of the base
CEIL_LAMP = "SDCEIL1"
CEIL = "SDCEIL2"
# D121: the engine's sky marker, not a lump of ours (check_pk3 knows it);
# MAPINFO's sky1 for MAP01 is SDSKY6, the Zarya-7 sky (D113).
SKY = "F_SKY1"

# Batch 3 props (approved 2026-10-13, D29).
CRATE_FACE = "SDCRAT1"   # 64x64: one crate; also the ends of a long crate
CRATE_LONG = "SDCRAT2"   # 128x64: the long side of a long crate
CRATE_TOP = "SDCRTOP1"   # 64x64 flat: the lid; also a plank table top
LOCKER = "SDLOCK1"       # 64x128: a barracks locker, one per 64 of wall

# What the furniture is made of. No new texture: steel frames everywhere,
# and the two flats that read as what they top. A bunk's grey blanket is
# the plain ceiling panel (SDCEIL2: flat grey with a stain); a mess table's
# top and the ice-axe rack's shelf are planks (SDCRTOP1).
FURNITURE = STEEL
BUNK_TOP = CEIL
TABLE_TOP = CRATE_TOP

# Switches (batch 2, approved 2026-10-13; src/lumps/ANIMDEFS pairs each OFF
# face with its ON twin, MOD-SPEC 4.3). Three switches, four variants: one
# each, chosen for what the switch DOES.
SW_A_FACE = "SDSW1A"     # knife switch (rubilnik): main power to the gate
SW_B_FACE = "SDSW1B"     # domed push button: a control-booth console
EXIT_FACE = "SDSW1D"     # hazard panel: the lift down into the metro
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64        # every SDSW1x is 64x128: one face per 64 of line
SWITCH_HEIGHT = 128

# `PRESSABLE` is the name tests use for the door leaf, which is only ever
# allowed on a door the player can press or on a leaf a switch opens.
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
LIGHT_ALCOVE = 144         # Z3's ammo alcove: one lamp step over the corridor
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
LIGHT_CLOSET = 112         # inside a monster closet: unlit storage
LIGHT_CATWALK = 160
LIGHT_S2 = 144             # the RPG-7 closet, lit: its slit is the clue...
LIGHT_S2_SLIT = 176        # ...a bright line in the wall above the catwalk
LIGHT_BOOTH_DARK = 96      # the booth before SW-A...
LIGHT_BOOTH_LIT = 160      # ...and after: the value its window holds
LIGHT_AIRLOCK = 128
LIGHT_EXIT = 96            # the darkest room: MAP02 starts here
LIGHT_EXIT_SWITCH = 144
# Lenin (CEO, v2 walk: "que haya iluminacion en el poster de Lenin que no se
# veia bien"). The poster is drawn at the light of the sector in front of
# it, so it gets a sector of its own: a lamp over it, and a ring one step
# dimmer round that, in the darkest room of the map. 96 -> 128 -> 160: the
# eye goes to it from the doorway, the face reads, and 160 is still inside
# the band textures are authored for (ART-BIBLE 5: 144), so it is lit and
# not burnt out, with a falloff on the wall either side instead of a flat
# bright rectangle.
LIGHT_LENIN_HALO = 128
LIGHT_LENIN = 160

# --- The komnata's mural (D38) ----------------------------------------------
# CEO, v3 run on skill 3: "Hay un pequeño trozo cuadrado justo enfrente del
# poster de cosmonáutica, yo lo quitaría para que se vea bien el poster". The
# lectern stood on the axis at the niche's mouth; it moves to the tribune's
# east front corner, and the colonnade's inner pair moves out to the
# tribune's edges. tests/test_map01.py casts the sight lines.
KOMNATA_COLUMNS_X = (96, 192, 416, 512)      # west edges; each column is 32 square
LECTERN_RECT = (384, 1344, 416, 1376)        # beside the mural, off its sight cone
MURAL_NICHE = (256, 1408, 384, 1440)         # SDPOSTR2 hangs on its north wall
KOMNATA_DOORWAY = (192, 320, 960)            # Z3's mouth into the komnata: x from, x to, y
KOMNATA_CENTRE = (320, 1192)
KOMNATA_RECT = (0, 960, 640, 1408)           # the room itself; the niche opens off its north wall
# The two floor lamps either side of the tribune, symmetric about the
# mural's axis (x 320). QA finding G3-F1: at x 176 and 464 the east lamp
# stood flush with the tribune's edge (x 448), so the tribune's east health
# bonus (432, 1400) was reached only through lanes exactly one body wide
# (32): between the lectern and the lamp, or behind the lectern. Each lamp
# now stands 16 further out, which opens the lectern-lamp lane to 48, a
# body and a half; the west one moves with it to keep the symmetry. Both
# move AWAY from the mural's sight cone, so D38's tests are unaffected.
KOMNATA_LAMP_Y = 1376
KOMNATA_LAMPS_X = (160, 480)

# --- The posters (CEO 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py, design section 6.1) -------------
# A 128x256 portrait needs a one-sided wall exactly 128 long in a sector
# exactly 256 high. The exit room is that already; the hangar is 320, so
# its two portraits hang at the back of a 16-deep niche whose ceiling is
# 256 over the hangar floor, and the hangar's concrete closes the 64 above
# them like a frame. No niche is ever taller than its room: seen from
# across the room, its ceiling would cut the face.
POSTER_WIDTH = 128
POSTER_HEIGHT = 256
POSTER_NICHE_DEPTH = 16
# Stalin over the transporter's east field, between the two rails that run
# out to the east wall: the Legion's trooper holds the hangar under him.
# Seen from the entry stair across the whole hangar, in its 176.
STALIN_NICHE = (2688, 1008, 2688 + POSTER_NICHE_DEPTH, 1008 + POSTER_WIDTH)
# The first Marx-Engels slot: the hangar's north wall between the pilaster
# and the catwalk, facing the gantry: Marx (SDPOSTR4), the first the player meets.
HANGAR_SLOT_NICHE = (1664, 1600, 1664 + POSTER_WIDTH, 1600 + POSTER_NICHE_DEPTH)
# The second: the lift room's east wall beside the exit switch, 256 high
# already (no niche). Lit like Lenin's halo, one panel over the room's 96,
# so the founders read beside the way out: Engels (SDPOSTR5).
EXIT_SLOT_LIGHT = (3232, 480, 3264, 608)
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
# (name, texture, axis, coord, lo, hi): one GridMap style per picture.
POSTERS = (
    ("exit_lenin", LENIN, "h", 864, 3072, 3200),
    ("komnata_mural", MURAL, "h", 1440, 256, 384),
    ("hangar_stalin", STALIN, "v", STALIN_NICHE[2], STALIN_NICHE[1], STALIN_NICHE[3]),
    ("hangar_north_slot", MARX, "h", HANGAR_SLOT_NICHE[3],
     HANGAR_SLOT_NICHE[0], HANGAR_SLOT_NICHE[2]),
    ("exit_east_slot", ENGELS, "v", EXIT_SLOT_LIGHT[2], EXIT_SLOT_LIGHT[1], EXIT_SLOT_LIGHT[3]),
)
POSTER_SLOTS_MARX_ENGELS = ("hangar_north_slot", "exit_east_slot")   # Marx, Engels


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS

# --- Sector tags ----------------------------------------------------------
TAG_D1_DORM_WASHROOM = 1
TAG_D2_DORM_CORRIDOR = 2
TAG_D3_KOMNATA_SERVICE = 3
TAG_D6_CATWALK_BOOTH = 6
# D4 and D5 are opened by SW-A and SW-B. Since v3 each tag also names a set
# of monster closets, so that the ONE special a switch line can carry opens
# the gate and springs the fight at once: tag 10 = D4 + the three fuel-bay
# ambush panels (the ambush is the press of SW-A), tag 11 = D5 + the three
# hangar closets of wave 2 (the climax is the press of SW-B). Door_Open
# opens every sector carrying its tag and nothing ever closes them.
TAG_D4_HANGAR_AIRLOCK = 10
TAG_D5_AIRLOCK_EXIT = 11
TAG_FUEL_BAY_AMBUSH = TAG_D4_HANGAR_AIRLOCK
TAG_HANGAR_WAVE_2 = TAG_D5_AIRLOCK_EXIT
TAG_S1_LOCKER_PANEL = 101
TAG_S2_CATWALK_PANEL = 102
TAG_S3_SUMP_PANEL = 103
# 30 is the light tag of SW-A's Door_Open: SW-A's alcove, D4's recess and
# the control booth brighten to their brightest neighbour as D4 rises
# (VERIFIED in engine 2026-10-13, MOD-SPEC 4.2).
TAG_LIGHT_GATE_POWER = 30
# V3 A2, pickup events (docs/levels/PICKUP-EVENTS.md): each tag is carried by
# one closet's panel and by NO line; the weapon's own pickup opens it.
TAG_EVENT_IZH = 12       # the IZh off its rack: the hound's closet in the service corridor
TAG_EVENT_PPSH = 13      # the PPSh-41 on the catwalk: the squad's closet in the hangar's south wall

# --- Heights --------------------------------------------------------------
HANGAR_FLOOR = -32
HANGAR_CEIL = 288
SUMP_FLOOR = -96
DOOR_LEAF_HEIGHT = 128
SWITCH_PLATFORM = 24   # the most a player steps up (Doom's 24)
WINDOW_SILL = 32       # more than a step: a window, not a doorway
STEP = 16              # every stair in the map rises 16 per step
PLINTH = 8             # a column's base, and a shower tray's drop
FURNITURE_HEIGHT = 32  # bunks, tables, counters: low cover, not a step
CLOSET_HEIGHT = 128    # a monster closet: one door leaf high

LANE_ACROSS = {"rotationfloor": 90.0}  # a lane whose line runs east-west

# D33: the density target (design section 17). Freedoom's MAP01 has 211
# sectors and 1274 lines on 3.99 Mu2 of floor (8.24 is its bounding box);
# ours has 3.32 Mu2 of floor, so equal density is ~176 sectors. v3 stops at
# 165 rather than pad: every sector here has a job. Lines stop well short of
# 1060 by construction - a rectangle painter emits no diagonals, no curves,
# and merges collinear runs - which section 17 argues. The floor of the band
# is what v3 delivers, so a regression shows; the ceiling keeps a later
# pass from padding.
DENSITY_SECTORS_MIN = 160
DENSITY_SECTORS_MAX = 240
DENSITY_LINES_MIN = 750

# Sectors a player is not meant to stand in, by zone-name prefix: the
# windows (a sill is a window, not a step), the crates and the furniture.
PROP_PREFIX = "crate_"
FURNITURE_PREFIX = "prop_"
PROP_PREFIXES = (PROP_PREFIX, FURNITURE_PREFIX)
WINDOWS = ("booth_window", "fuel_window", "s2_slit")

# --- Things ---------------------------------------------------------------
ED_PLAYER1_START = 1
PLAYER_START = (256, 96)
PLAYER_ANGLE = 90  # north: D2, the way out of the dorm, is straight ahead

# Our own weapons (MOD-SPEC 6.1). Slot 1 is the ice axe since D40 (it was the
# shovel; same editor number, 21001). It is not in the player's start
# inventory (SD_Player): the one on the rack is the only way to get it.
ED_ICE_AXE = 21001
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
TUTORIAL_WEAPONS = (ED_ICE_AXE, ED_IZH, ED_PPSH)

# --- Pickup events (V3 A2: docs/levels/PICKUP-EVENTS.md; design section 20) ---
# MAP01 has no key, so its two events ride on tutorial weapons the player
# cannot own yet (rule R7): nothing drops a PPSh-41, and no Legion trooper
# (who drops an IZh) stands before the rack. A player who skips the rack,
# takes a dropped IZh in the hangar and comes back still picks the rack's up
# (it gives shells) and fires the event then; only with 50 shells would it
# wait. Each opens one closet, by Door_Open on a tag no line carries.
IZH_EVENT = door_open("izh_hound", TAG_EVENT_IZH)
PPSH_EVENT = door_open("ppsh_squad", TAG_EVENT_PPSH)
PICKUP_EVENTS = {ED_IZH: IZH_EVENT, ED_PPSH: PPSH_EVENT}
# The closets the events open: (panel, room). The IZh's lies south of the
# service corridor's pipe run, behind the player at the rack: the shotgun's
# first shot is at a hound (the guard post's lesson, "the IZh at close
# range"). The PPSh's is in the hangar's south wall east of the gantry, in
# full view of the catwalk where the gun lies: the squad crosses the floor
# under the player's new gun.
CLOSET_IZH = ((832, 1072, 960, 1088), (800, 960, 992, 1072))
CLOSET_PPSH = ((2240, 304, 2368, 320), (2224, 160, 2384, 304))
EVENT_CLOSETS = {"closet_izh": (IZH_EVENT, CLOSET_IZH, 0),
                 "closet_ppsh": (PPSH_EVENT, CLOSET_PPSH, -32)}

# Doom editor numbers our classes replace or Freedoom implements (MOD-SPEC
# 6.4: maps keep using Doom's numbers for ammo, and `replaces` does the
# rest). The pickup amounts are Doom's, which our subclasses keep.
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
ED_BACKPACK = 8
ED_COMPUTER_MAP = 2026    # "the base schematic" in S2
ED_BARREL = 2035          # a fuel drum, until it has its own sprite
ED_FLOOR_LAMP = 2028

# The diegetic radio (D43; MOD-SPEC 6.7, ADR 008), our decoration 21200:
# while the player is within its reach it plays one of two CC0 pieces IN
# PLACE OF the level's music, and gives D_SDM01 back past reach + 64. Its
# body is solid, radius 16, height 28 (src/zscript/sd/radio.zs).
ED_RADIO = 21200
RADIO_KOLOKOLCHIK = 2         # arg0: D_SDRAD2, "Kolokolchik"
# arg1, the reach. The PM's rule (D43 brief): 96 for a radio against a back
# wall, 128 for one in the middle of a room. Ours stands against the guard
# post's crate stack, so 96: it covers every spot of the post and the rack,
# and never the corridor's walking line (design section 17.16).
RADIO_REACH_BACK_WALL = 96

# V3 A4, the RGD-5 hand grenade (ADR 012; docs/engine/2026-10-23_V3_rgd5.md
# section 6), placed in Episode 1 on 2026-10-24: its own pool, counted 1.25
# shell-equivalents a grenade (BALANCE 8.1, 8.6). A grenade is a consumable
# here, so it rides in ITEMS and scales DOWN with skill: 4 / 3 / 2 grenades on
# skills 2 / 3 / 4. No crate (21022) in the campaign.
ED_RGD5 = 21009           # the pouch: the weapon and two grenades
ED_RGD5_AMMO = 21021      # one loose grenade (it gives the weapon too)
# V3 B5, the propaganda radio (D124; docs/sound/2026-10-23_V3_propaganda-radio.md
# 5.4): SD_Loudspeaker, a positional voice OVER the music (MOD-SPEC 6.14).
ED_LOUDSPEAKER = 21201

# Monsters: Freedoom's implementations of the Doom II actors, each standing
# in for the bestiary class that will `replaces` it (docs/engine/BESTIARY.md
# section 12), so F5 changes nothing in this file. D35: the Fourth Reich is
# met first, the Liberty Legion holds the hangar.
ED_ZOMBIEMAN = 3004       # -> SD_ReichRifleman (Reich)
ED_SHOTGUN_GUY = 9        # -> SD_LegionTrooper (Legion)
ED_IMP = 3001             # -> SD_Stormtrooper (hybrid, both factions)
ED_DEMON = 3002           # -> SD_ReichHound (Reich)
ED_CACODEMON = 3005       # -> SD_Doughboy (Legion)
ED_HELL_KNIGHT = 69       # -> SD_Panzermensch (Reich), 500 HP (D35)

MONSTER_KINDS = {
    "rifleman": ED_ZOMBIEMAN,
    "trooper": ED_SHOTGUN_GUY,
    "stormtrooper": ED_IMP,
    "hound": ED_DEMON,
    "doughboy": ED_CACODEMON,
    "panzermensch": ED_HELL_KNIGHT,
}
REICH = ("rifleman", "hound", "panzermensch")
LEGION = ("trooper", "doughboy")

# Design section 8: monsters per skill. Strictly increasing (G3-8).
# V3 A2 adds three on every skill: the IZh's hound, the PPSh-41's two.
ENEMY_TOTALS = {2: 24, 3: 36, 4: 49}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Tier 2 is
# on every skill, 3 from medium up, 4 on hard only (udmf.skill_tier).
MONSTERS = (
    # Z1 dorm - the alarm: the Reich is already in the barracks.
    ("z1_dorm", "rifleman", 416, 400, 270, 2),
    ("z1_dorm", "rifleman", 592, 240, 180, 2),
    ("z1_dorm", "rifleman", 192, 400, 0, 3),
    ("z1_dorm", "rifleman", 560, 192, 180, 4),
    # Z2 washroom - the hound the ice axe answers.
    ("z2_washroom", "hound", 800, 96, 180, 3),
    # Z3 corridor.
    ("z3_corridor", "rifleman", 224, 780, 270, 2),
    ("z3_corridor", "rifleman", 288, 910, 270, 2),
    ("z3_corridor", "hound", 256, 680, 270, 3),
    ("z3_corridor", "rifleman", 296, 860, 270, 4),
    # Z4 komnata - crossfire across the tables, a trooper-less room.
    ("z4_komnata", "rifleman", 96, 1300, 0, 2),
    ("z4_komnata", "rifleman", 544, 1300, 180, 2),
    ("tribune", "rifleman", 240, 1376, 270, 2),
    ("z4_komnata", "stormtrooper", 320, 1248, 270, 3),
    ("z4_komnata", "rifleman", 544, 1120, 180, 4),
    ("z4_komnata", "hound", 560, 1180, 270, 4),
    # Z5 service corridor and guard post - the IZh at close range.
    ("z5_service", "rifleman", 880, 1160, 180, 2),
    # The guard stands at the post's mouth, clear of the radio behind him
    # (it was at 960 1250, where the radio now is; design section 17.16).
    ("z5b_guard", "rifleman", 960, 1224, 270, 2),
    ("z5_flicker", "rifleman", 1060, 1150, 180, 3),
    ("z5_service", "stormtrooper", 1110, 1170, 180, 4),
    # Z6 hangar, first contact - the Legion holds it.
    ("z6a_cradle", "trooper", 1680, 900, 180, 2),
    ("lane_a_cross", "trooper", 2560, 672, 180, 2),
    ("cradle_spine", "trooper", 1880, 1024, 180, 2),
    ("gantry", "rifleman", 1800, 352, 90, 2),
    ("z6a_cradle", "stormtrooper", 2000, 1150, 180, 2),
    ("z6_hangar", "trooper", 2300, 900, 180, 3),
    ("gantry", "rifleman", 2100, 352, 90, 3),
    ("z6_hangar", "stormtrooper", 2450, 500, 180, 3),
    ("z6_hangar", "trooper", 2600, 1000, 180, 4),
    ("z6b_catwalk", "trooper", 2400, 1520, 270, 4),
    ("z6_hangar", "stormtrooper", 1320, 820, 0, 4),
    # Z9 booth - a sniper at the window, the reason to respect the catwalk.
    ("z9_booth", "trooper", 2620, 1640, 270, 4),
    # Z7 fuel-bay ambush: three panels behind the player as SW-A is thrown.
    ("closet_a1", "stormtrooper", 1250, 2056, 270, 2),
    ("closet_a1", "hound", 1320, 2056, 270, 3),
    ("closet_a2", "stormtrooper", 1440, 2056, 270, 2),
    ("closet_a2", "trooper", 1510, 2056, 270, 4),
    ("closet_a3", "hound", 1672, 1820, 180, 2),
    ("closet_a3", "stormtrooper", 1672, 1900, 180, 4),
    # Z6 hangar, wave 2: Legion reinforcements out of three closets as SW-B
    # is pressed, while the player is up in the booth.
    ("closet_w1", "trooper", 1080, 600, 0, 2),
    ("closet_w2", "rifleman", 1080, 800, 0, 2),
    ("closet_e1", "trooper", 2760, 1230, 180, 2),
    ("closet_w1", "trooper", 1080, 680, 0, 3),
    ("closet_e1", "doughboy", 2760, 1300, 180, 3),
    ("closet_w2", "stormtrooper", 1080, 860, 0, 4),
    # V3 A2 (design section 20): the IZh's hound, the PPSh-41's squad.
    # The same on every skill: a set piece, and BALANCE 8's band leaves no
    # room for more on skill 4 without breaking D119's pickup ceiling.
    ("closet_izh", "hound", 896, 1016, 90, 2),
    ("closet_ppsh", "trooper", 2264, 232, 90, 2),
    ("closet_ppsh", "rifleman", 2344, 232, 90, 2),
    # Z8 / Z10 exit: stragglers, and the Panzermensch that gates the lift.
    ("z8_airlock", "trooper", 2830, 760, 180, 2),
    ("z10_lift", "panzermensch", 3136, 660, 180, 3),
    ("z10_exit", "trooper", 3010, 520, 180, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest
# skill tier it appears on - 4 = every skill, 3 = medium and easier, 2 =
# easy only). Weapons and every pickup inside a secret are on every skill.
ITEMS = (
    # The tutorial weapons, on every skill, on the critical path.
    ("z1_ice_axe_rack", ED_ICE_AXE, -16, 384, 4),
    ("weapon_rack", ED_IZH, 1040, 1256, 4),
    ("z6b_catwalk", ED_PPSH, 2000, 1520, 4),
    # S1 - the locker closet behind the shower stall.
    ("s1_locker", ED_GREEN_ARMOR, 1040, 96, 4),
    ("s1_locker", ED_STIMPACK, 1008, 56, 4),
    ("s1_locker", ED_STIMPACK, 1008, 136, 4),
    # S2 - the RPG-7 closet above the catwalk.
    ("s2_closet", ED_RPG7, 2208, 1712, 4),
    ("s2_closet", ED_ROCKET_BOX, 2160, 1712, 4),
    ("s2_closet", ED_COMPUTER_MAP, 2256, 1712, 4),
    # S3 - the sump the fuel drains into.
    ("s3_sump", ED_BACKPACK, 960, 1760, 4),
    ("s3_sump", ED_SHELL_BOX, 930, 1700, 4),
    ("s3_sump", ED_MEDIKIT, 930, 1820, 4),
    ("s3_sump", ED_MEDIKIT, 990, 1820, 4),
    # Stimpacks: 3 on every skill, +1 medium, +2 easy.
    ("z3_alcove", ED_STIMPACK, 176, 696, 4),
    ("z3_alcove_e", ED_HEALTH_BONUS, 336, 832, 4),
    ("z6_hangar", ED_STIMPACK, 1200, 1060, 4),
    ("z9_booth", ED_STIMPACK, 2460, 1700, 4),
    ("z5b_guard", ED_STIMPACK, 1000, 1240, 3),
    ("z4_komnata", ED_STIMPACK, 32, 1380, 2),
    ("z8_airlock", ED_STIMPACK, 2780, 740, 2),
    # Medikits outside the sump: 2 on every skill, +1 medium, +1 easy.
    ("pipes_1", ED_MEDIKIT, 1000, 1104, 4),
    ("z7_fuel_bay", ED_MEDIKIT, 1300, 1700, 4),
    ("gantry", ED_MEDIKIT, 1600, 352, 3),
    ("z8_airlock", ED_MEDIKIT, 2880, 600, 2),
    # Armour bonuses: 6 on every skill, +2 medium and easy.
    ("gantry", ED_ARMOR_BONUS, 1700, 352, 4),
    ("gantry", ED_ARMOR_BONUS, 1900, 352, 4),
    ("gantry", ED_ARMOR_BONUS, 2000, 352, 4),
    ("cradle_spine", ED_ARMOR_BONUS, 1760, 1024, 4),
    ("cradle_spine", ED_ARMOR_BONUS, 1960, 1024, 4),
    ("z9_booth", ED_ARMOR_BONUS, 2640, 1800, 4),
    ("z1_dorm", ED_ARMOR_BONUS, 32, 352, 3),
    ("z1_dorm", ED_ARMOR_BONUS, 32, 416, 3),
    # Health bonuses: the dressing for corners, every skill.
    ("z2_washroom", ED_HEALTH_BONUS, 860, 40, 4),
    ("z3_corridor", ED_HEALTH_BONUS, 300, 540, 4),
    ("z4_komnata", ED_HEALTH_BONUS, 608, 980, 4),
    ("z4_mural", ED_HEALTH_BONUS, 320, 1424, 4),
    ("z5b_guard", ED_HEALTH_BONUS, 912, 1270, 4),
    ("catwalk_landing", ED_HEALTH_BONUS, 2432, 1312, 4),
    ("z6_hangar", ED_HEALTH_BONUS, 2650, 340, 4),
    ("z6_hangar", ED_HEALTH_BONUS, 1170, 340, 4),
    ("airlock_niche_n", ED_HEALTH_BONUS, 2832, 816, 4),
    ("airlock_niche_s", ED_HEALTH_BONUS, 2832, 528, 4),
    # ...and one in each nook v3 made, for whoever looks into it.
    ("stall_1", ED_HEALTH_BONUS, 928, 24, 4),
    ("stall_3", ED_HEALTH_BONUS, 928, 168, 4),
    ("tribune", ED_HEALTH_BONUS, 208, 1392, 4),
    ("tribune", ED_HEALTH_BONUS, 432, 1400, 4),   # clear of the lectern (D38)
    ("z10_lift", ED_HEALTH_BONUS, 3090, 600, 4),
    ("plinth_tank_2", ED_HEALTH_BONUS, 1240, 1824, 4),
    # The RGD-5 (V3 A4, design section 21). The first pouch where the lesson
    # is safe: the komnata's south-east corner by D3, found once the room is
    # cleared and while D3 is still shut; beyond the door wait the service
    # corridor's riflemen and then the Legion massed round the cradle, the
    # first group worth a throw. Loose ones at the hangar's foot (for the
    # cradle) and on the catwalk (thrown down on wave 2's closets).
    ("z4_komnata", ED_RGD5, 600, 1040, 4),
    ("z6_hangar", ED_RGD5_AMMO, 1240, 980, 3),
    ("z6b_catwalk", ED_RGD5_AMMO, 2300, 1572, 2),
)

# The propaganda loudspeakers (V3 B5, design section 21), on every skill:
# (zone, x, y, lines, reach, flags, jingle). Lines are the radio's 1-16
# (SDRAD01-16), the thing's arg0 their bit mask; reach 0 = the actor's 384;
# flags arg3 (4 = the valve bed); jingle arg4 (0 = a random one of three).
# The komnata's: the political room's slogans and RAD11, «the Zarya-7
# garrison is still holding», about this very base (Episode 1's line only).
# It stands at the west wall, so its reach + 128 stays clear of the guard
# post's SD_Radio (reach + 64). The hangar's, reach 512 (the hangar is 1536
# long): the air-raid alert, the fallen-objects notice, the weather and the
# time signal, as the invasion lands.
LOUDSPEAKERS = (
    ("z4_komnata", 64, 1200, (5, 7, 13, 11), 0, 0, 0),
    ("z6_hangar", 1920, 1300, (3, 4, 10, 16), 512, 0, 0),
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
    # Z1-Z4, the TT-33 alone (and the ice axe): its rounds.
    ("z4_komnata", ED_CLIP_BOX, 32, 980, 2),
    ("z4_komnata", ED_CLIP_BOX, 608, 1380, 3),
    ("z3_alcove", ED_CLIP_BOX, 176, 672, 4),
    # Z5 to the fuel bay, the IZh met: its own 8 shells, four more by its
    # rack and four in the bay from skill 3; the Legion's dropped IZhs bring
    # the rest. Rounds for the TT-33 and, from the catwalk, the PPSh.
    ("z5b_guard", ED_SHELLS, 1000, 1272, 3),     # was 980 1262: under the radio
    ("z7_fuel_bay", ED_SHELLS, 1200, 1700, 3),
    ("z5_service", ED_CLIP_BOX, 740, 1190, 2),
    ("z6_hangar", ED_CLIP_BOX, 1320, 1050, 2),
    ("z7_fuel_bay", ED_CLIP_BOX, 1560, 1950, 3),
    ("z6_hangar", ED_CLIP_BOX, 1340, 470, 4),
    # The catwalk on, the PPSh the newest: its boxes of rounds.
    ("z6b_catwalk", ED_CLIP_BOX, 2048, 1560, 2),
    ("z6_hangar", ED_CLIP_BOX, 2600, 1560, 2),
    ("gantry", ED_CLIP_BOX, 2200, 352, 2),
    ("z6_hangar", ED_CLIP_BOX, 2560, 1250, 3),
    ("z6b_catwalk", ED_CLIP_BOX, 2480, 1480, 3),
    ("z9_booth", ED_CLIP_BOX, 2480, 1800, 3),
    ("z8_airlock", ED_CLIP_BOX, 2780, 600, 3),
    ("z6_hangar", ED_CLIP_BOX, 2600, 1376, 4),
    # V3 A2: the PPSh squad's own box, left in its closet - what its three
    # extra kills cost on every skill (BALANCE 8.2's floors), and rounds,
    # not shells, so the troopers' dropped IZhs keep shells under 35 %.
    ("closet_ppsh", ED_CLIP_BOX, 2304, 184, 2),
)

# Fuel drums (Freedoom's barrel) and floor lamps: part of the room, on
# every skill. (zone, editor number, x, y)
FIXTURES = (
    ("z6_hangar", ED_BARREL, 1400, 420),
    ("z6_hangar", ED_BARREL, 2300, 420),
    ("z6a_cradle", ED_BARREL, 1630, 900),
    ("z6_hangar", ED_BARREL, 2600, 1150),
    ("z6_hangar", ED_BARREL, 1640, 1480),
    ("shadow_cradle_s", ED_BARREL, 2000, 800),
    # The drum stack in the fuel bay's north-west corner: the fuel drains
    # from here towards the sump (S3's clue is the drain, not the drums).
    ("z7_fuel_bay", ED_BARREL, 1180, 1890),
    ("z7_fuel_bay", ED_BARREL, 1180, 1950),
    ("z7_fuel_bay", ED_BARREL, 1215, 1920),
    ("z7_fuel_bay", ED_BARREL, 1540, 1680),
    ("z4_komnata", ED_FLOOR_LAMP, KOMNATA_LAMPS_X[0], KOMNATA_LAMP_Y),
    ("z4_komnata", ED_FLOOR_LAMP, KOMNATA_LAMPS_X[1], KOMNATA_LAMP_Y),
    ("z10_exit", ED_FLOOR_LAMP, 3248, 832),
)

# The diegetic radio, on every skill: (zone, piece, reach, x, y, facing).
# Z5b, the guard post: a dead-end side room off the service corridor, met
# once on the way to the hangar (MOD-SPEC 6.7: keep radios out of rooms the
# player crosses again and again). It stands on the post's floor against
# the crate stack at its back, centred on the doorway: 48 free either side
# of it, so the way to the IZh's rack in the east wall stays a body and a
# half wide. Its reach + 64 covers the post and the stretch of corridor in
# front of it and no other room (design section 17.16).
RADIOS = (
    ("z5b_guard", RADIO_KOLOKOLCHIK, RADIO_REACH_BACK_WALL, 960, 1264, 270),
)


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
    tm = TextMap(comment=f"{MAP_NAME} v3 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
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

    def like(room: str, name: str, rects, *, floor: int | None = None,
             ceil: int | None = None, light: int | None = None, **kw) -> int:
        """A sector that is part of `room`: its heights, light and flats
        unless told otherwise. Steps, plinths, frames, kerbs, alcoves."""
        s = tm.sectors[plan[room]]
        kw.setdefault("flat", s.texturefloor)
        kw.setdefault("ceiling", s.textureceiling)
        kw.setdefault("extra", dict(s.extra))
        return zone(name, s.heightfloor if floor is None else floor,
                    s.heightceiling if ceil is None else ceil, rects,
                    light=s.lightlevel if light is None else light, **kw)

    def door(name: str, floor: int, tag: int, rect, *, light: int) -> int:
        """A closed door sector (ceiling resting on the floor).

        Its own walls are the door TRACK - the strip of jamb the leaf slides
        past - so they are steel, like the leaf. Its light is what the
        doorway shows once open.
        """
        return zone(name, floor, floor, [rect], tag, light=light, wall=STEEL)

    def lamp(room: str, n: int, rect) -> int:
        """One SDCEIL1 panel = one 64x64 sector exactly LAMP_STEP over its room."""
        s = tm.sectors[plan[room]]
        return zone(f"lamp_{room}_{n}", s.heightfloor, s.heightceiling, [rect],
                    light=s.lightlevel + LAMP_STEP, flat=s.texturefloor,
                    ceiling=CEIL_LAMP, extra=dict(s.extra))

    crate_faces: list[tuple[str, int, int, int, str]] = []

    def crate(name: str, room: str, rect, height: int, exposed: str) -> int:
        """A crate, or a stack of them, standing on `room`'s floor.

        Each exposed side ("nsew") wears the face that fits its length
        exactly: SDCRAT2 on a 128 side, SDCRAT1 on a 64 side, so no crate is
        ever cut. A stack is a taller crate: 128 of SDCRAT1 is two crates.
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

    def furniture(name: str, room: str, rect, *, top: str,
                  height: int = FURNITURE_HEIGHT) -> int:
        """Bunks, tables, counters: steel-framed, waist high, top as given.

        FURNITURE_HEIGHT (32) is more than a step, so nothing climbs on it,
        and less than an eye (41), so it is cover you can see over: it stops
        the low half of a hitscan line, not the view.
        """
        s = tm.sectors[plan[room]]
        return zone(f"{FURNITURE_PREFIX}{name}", s.heightfloor + height, s.heightceiling,
                    [rect], light=s.lightlevel, flat=top, ceiling=s.textureceiling,
                    wall=FURNITURE)

    solid_faces: list[tuple[int, int, int, int, str]] = []

    def column(x1: int, y1: int, x2: int, y2: int, texture: str = STEEL,
               plinth_of: str | None = None, name: str = "") -> None:
        """A solid column (void) with every face in `texture`.

        With `plinth_of`, the column stands on a plinth one PLINTH above
        that room's floor and 16 wider each side: a base the eye reads as
        weight, and the zocalo the brief asked for. A pilaster is a column
        carved into a wall.
        """
        if plinth_of:
            s = tm.sectors[plan[plinth_of]]
            like(plinth_of, f"plinth_{name}", [(x1 - 16, y1 - 16, x2 + 16, y2 + 16)],
                 floor=s.heightfloor + PLINTH, flat=CONCRETE_FLOOR,
                 ceiling=s.textureceiling, wall=STEEL)
        g.carve(x1, y1, x2, y2)
        solid_faces.append((x1, y1, x2, y2, texture))

    def closet(name: str, door_rect, room_rect, tag: int, *, leaf: str,
               floor: int = HANGAR_FLOOR) -> int:
        """A monster closet: a panel in a wall that opens for good.

        The panel is a door sector with no use-special of its own: it opens
        when the switch that owns `tag` is pressed, together with the gate
        that switch opens (one line, one special). Its leaf wears the wall it
        is cut into, so the panel is wall until it moves; a door never
        closes behind the player and a closet the player walks into he walks
        out of.
        """
        door_index = zone(f"{name}_door", floor, floor, [door_rect], tag,
                          light=LIGHT_CLOSET, wall=leaf)
        zone(name, floor, floor + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

    # ======================================================================
    # Act 1 - barracks.  Dorm -> washroom (+ secret locker) and dorm -> corridor
    # ======================================================================
    # Z1 dorm, the player's "before": ordinary, lit, 640 x 448, exactly 128
    # high. v3: four steel bunks with their blankets, three lamps, the
    # ice-axe rack, and steel frames round both doors.
    zone("z1_dorm", 0, 128, [(0, 0, 640, 448)], flat=TILE, light=LIGHT_DORM)
    lamp("z1_dorm", 1, (288, 224, 352, 288))
    lamp("z1_dorm", 2, (128, 160, 192, 224))
    lamp("z1_dorm", 3, (448, 160, 512, 224))
    # Six bunks, two-high (twelve men slept here): two by the lockers, four
    # by the east wall, the aisle down the middle from the start to D2.
    for n, rect in enumerate(((64, 0, 128, 128), (64, 320, 128, 448),
                              (384, 0, 448, 128), (480, 0, 544, 128),
                              (480, 320, 544, 448), (576, 320, 640, 448)), start=1):
        furniture(f"bunk_{n}", "z1_dorm", rect, top=BUNK_TOP)
    # The ice-axe rack (the shovel rack until D40): a steel niche in the west
    # wall past the lockers. The ice axe on it is the weapon the alarm makes
    # the player reach for. The zone name carries `z1_` so that tools/route.py
    # reads it as Z1 by its name alone, whatever the weapon is called next.
    like("z1_dorm", "z1_ice_axe_rack", [(-32, 352, 0, 416)], flat=TABLE_TOP, wall=STEEL)
    # Door frames: a 16-deep steel surround either side of the leaf, so a
    # door reads as a door from across the room (the v0 and v1 findings).
    like("z1_dorm", "frame_d1_dorm", [(624, 16, 640, 176)], wall=STEEL)
    like("z1_dorm", "frame_d2_dorm", [(176, 432, 336, 448)], wall=STEEL)

    # D1, manual door east to the washroom.
    d1 = door("d1", 0, TAG_D1_DORM_WASHROOM, (640, 32, 704, 160), light=LIGHT_WASHROOM)
    zone("z2_washroom", 0, 96, [(704, 0, 896, 192)],
         flat=TILE, ceiling=CEIL_LAMP, light=LIGHT_WASHROOM)
    like("z2_washroom", "frame_d1_washroom", [(704, 16, 720, 176)], wall=STEEL)
    # Three wash basins along the north wall, tiled tops.
    for n, x in enumerate((736, 800, 864), start=1):
        furniture(f"basin_{n}", "z2_washroom", (x, 160, x + 32, 192), top=TILE)
    # Three shower stalls in the east wall, a shower tray (PLINTH) below the
    # room, steel partitions between them. S1 (v3): the middle stall's back
    # wall is a steel panel where the other two are concrete. That is the
    # whole clue: a player comparing the three stalls sees it; one walking
    # past sees steel partitions and steel among them. v2's plate on a bare
    # concrete wall, in a darker sector, was found at once ("muy evidente").
    for n, (y1, y2) in enumerate(((0, 48), (64, 128), (144, 192)), start=1):
        like("z2_washroom", f"stall_{n}", [(896, y1, 960, y2)],
             floor=-PLINTH, flat=CONCRETE_FLOOR, ceiling=CEIL)
    column(896, 48, 960, 64)
    column(896, 128, 960, 144)
    s1_panel = door("s1_panel", 0, TAG_S1_LOCKER_PANEL, (960, 64, 976, 128),
                    light=LIGHT_SECRET)
    zone("s1_locker", 0, 96, [(976, 32, 1072, 160)], wall=STEEL,
         light=LIGHT_SECRET, special=SECTOR_SPECIAL_SECRET)

    # D2, manual door north to the barracks corridor.
    d2 = door("d2", 0, TAG_D2_DORM_CORRIDOR, (192, 448, 320, 512), light=LIGHT_DORM)
    # Z3 corridor: where the red stripe is born. v3: two steel bulkheads
    # break the run into three bays, and an alcove holds the first supplies.
    zone("z3_corridor", 0, 96, [(192, 512, 320, 960)], flat=TILE, light=LIGHT_CORRIDOR)
    lamp("z3_corridor", 1, (224, 576, 288, 640))
    lamp("z3_corridor", 2, (224, 832, 288, 896))
    like("z3_corridor", "bulkhead_1", [(192, 736, 320, 752)], ceil=80, wall=STEEL)
    like("z3_corridor", "bulkhead_2", [(192, 928, 320, 944)], ceil=80, wall=STEEL)
    like("z3_corridor", "z3_alcove", [(160, 640, 192, 704)], light=LIGHT_ALCOVE,
         ceiling=CEIL_LAMP, wall=STEEL)
    # ...and a fire-point opposite, in the third bay: somewhere to stand
    # out of the line of the corridor when the hound comes.
    like("z3_corridor", "z3_alcove_e", [(320, 800, 352, 864)], wall=STEEL)

    # Z4 Leninskaya komnata: mess hall to the south (three tables: the
    # "crossfire in a room with cover" of section 5 finally has cover),
    # political room to the north (a colonnade framing the mural, and a
    # tribune two steps up).
    zone("z4_komnata", 0, 192, [KOMNATA_RECT], flat=TILE, light=LIGHT_KOMNATA)
    lamp("z4_komnata", 1, (128, 1152, 192, 1216))
    lamp("z4_komnata", 2, (448, 1152, 512, 1216))
    lamp("z4_komnata", 3, (288, 1120, 352, 1184))
    for n, x in enumerate((64, 256, 448), start=1):
        furniture(f"mess_table_{n}", "z4_komnata", (x, 1024, x + 128, 1056), top=TABLE_TOP)
    # The colonnade. v3 put its inner pair at x 256 and 352, on the mural's
    # own edges, and the west one stood in the line from the doorway to the
    # mural; they now stand on the tribune's edges (x 192 and 416), still
    # symmetric about the axis, framing the tribune and leaving the cone
    # from the doorway to the mural clear (D38, design section 17.13).
    for x in KOMNATA_COLUMNS_X:
        column(x, 1232, x + 32, 1264, texture=CONC)
    like("z4_komnata", "tribune_step", [(192, 1312, 448, 1344)], floor=PLINTH, wall=STEEL)
    like("z4_komnata", "tribune", [(192, 1344, 448, 1408)], floor=2 * PLINTH, wall=STEEL)
    # The lectern stands at the tribune's front edge, east of the mural, the
    # speaker beside the picture. v3 had it on the axis at the niche's mouth,
    # 48 high in front of a mural whose foot is at 16: the CEO's "pequeño
    # trozo cuadrado justo enfrente del poster" (D38).
    furniture("lectern", "tribune", LECTERN_RECT, top=TABLE_TOP)
    # The mural niche stands on the tribune: 128 high above ITS floor, so
    # SDPOSTR2 is still one tile.
    zone("z4_mural", 2 * PLINTH, 2 * PLINTH + 128, [MURAL_NICHE],
         flat=TILE, ceiling=CEIL_LAMP, light=LIGHT_MURAL)

    # ======================================================================
    # Act 2 - service corridor, guard post, and the descent into the hangar
    # ======================================================================
    zone("d3_recess", 0, DOOR_LEAF_HEIGHT, [(576, 1088, 640, 1216)],
         flat=TILE, wall=STRIPE, light=LIGHT_KOMNATA)
    d3 = door("d3", 0, TAG_D3_KOMNATA_SERVICE, (640, 1088, 704, 1216), light=LIGHT_SERVICE)
    zone("z5_service", 0, 112, [(704, 1088, 1152, 1216)], light=LIGHT_SERVICE)
    # v3: a run of pipes under the ceiling along the south wall, broken by
    # the failing lamp's housing.
    # It starts 16 clear of D3, so the door's leaf is one height all along.
    like("z5_service", "pipes_1", [(720, 1088, 1024, 1120)], ceil=96, wall=STEEL)
    like("z5_service", "pipes_2", [(1088, 1088, 1152, 1120)], ceil=96, wall=STEEL)
    lamp("z5_service", 1, (768, 1136, 832, 1200))
    zone("z5_flicker", 0, 112, [(1024, 1088, 1088, 1216)], light=LIGHT_FLICKER,
         ceiling=CEIL_LAMP, special=SECTOR_SPECIAL_LIGHT_FLICKER)
    zone("z5b_guard", 8, 112, [(896, 1216, 1024, 1344)],
         wall=STEEL, ceiling=CEIL_LAMP, light=LIGHT_GUARD)
    crate("guard", "z5b_guard", (896, 1280, 1024, 1344), 64, exposed="s")
    # The weapon rack: a steel niche in the post's east wall, and the IZh in
    # it. Steel = function: this is where the weapon is (section 6).
    like("z5b_guard", "weapon_rack", [(1024, 1232, 1056, 1280)], wall=STEEL)

    # ======================================================================
    # Act 3 - the hangar and everything carved out of it
    # ======================================================================
    zone("z6_hangar", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 320, 2688, 1600)], light=LIGHT_HANGAR)

    zone("step_down_1", -8, 112, [(1152, 1088, 1216, 1216)], light=128)
    zone("step_down_2", -16, 160, [(1216, 1088, 1280, 1216)], light=144)
    zone("step_down_3", -24, 224, [(1280, 1088, 1344, 1216)], light=160)

    # --- the yellow lanes: the fork at the foot of the entry stair ---------
    zone("lane_a_cross", HANGAR_FLOOR, HANGAR_CEIL, [(1344, 608, 2624, 736)],
         flat=LANE, extra=LANE_ACROSS, light=LIGHT_HANGAR)
    zone("lane_a_spur", HANGAR_FLOOR, HANGAR_CEIL, [(1344, 736, 1472, 1216)],
         flat=LANE, light=LIGHT_HANGAR)
    zone("lane_b_cross", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 1216, 1344, 1344)],
         flat=LANE, extra=LANE_ACROSS, light=LIGHT_WEST_BAY)
    zone("lane_b_spur", HANGAR_FLOOR, HANGAR_CEIL, [(1152, 1344, 1280, 1600)],
         flat=LANE, light=LIGHT_WEST_BAY)

    # --- Z6a transporter cradle ---------------------------------------------
    # v3 gives it volume: rails run out from under it to east and west (the
    # transporter rolls on them), a kerb along its south edge, and a raised
    # erector spine with a stair - a high point in the middle of the floor,
    # kept out of the SW-A -> D4 sight line (tested).
    for n, (floor, x) in enumerate(((-16, 1504), (0, 1536), (16, 1568)), start=1):
        zone(f"cradle_step_{n}", floor, HANGAR_CEIL, [(x, 960, x + 32, 1088)],
             wall=STEEL, light=LIGHT_HANGAR)
    # D121: the roof over the cradle is the launch slot, slid open - the
    # cosmodrome's night over the transporter. Same height as the hangar's
    # roof, so no wall is lost at its edge; the kerb, the spine and its steps
    # are the cradle's (`like`) and open with it. Nothing else is: no door,
    # no recess, no room under a lower ceiling touches the slot.
    zone("z6a_cradle", 32, HANGAR_CEIL, [(1600, 832, 2240, 1216)], wall=STEEL,
         light=LIGHT_HANGAR, ceiling=SKY)
    # One kerb, on the SOUTH edge only. A north kerb was built and the
    # sight-line test refused it: the line from SW-A to the foot of D4
    # crosses the cradle's north edge 4 units above the cradle floor.
    like("z6a_cradle", "cradle_kerb_s", [(1600, 832, 2240, 848)], floor=32 + STEP,
         wall=STEEL)
    for n, x in enumerate((1640, 1664, 1688), start=1):
        like("z6a_cradle", f"spine_step_{n}", [(x, 960, x + 24, 1088)], floor=32 + n * STEP,
             wall=STEEL)
    like("z6a_cradle", "cradle_spine", [(1712, 960, 2048, 1088)], floor=32 + 4 * STEP,
         wall=STEEL)
    for side, (y1, y2) in (("s", (880, 896)), ("n", (1152, 1168))):
        like("z6_hangar", f"rail_w_{side}", [(1472, y1, 1600, y2)],
             floor=HANGAR_FLOOR - PLINTH, wall=STEEL)
        like("z6_hangar", f"rail_e_{side}", [(2240, y1, 2688, y2)],
             floor=HANGAR_FLOOR - PLINTH, wall=STEEL)

    # --- the catwalk stair: three steps, a landing, three steps -------------
    for i, (y1, floor) in enumerate(((1184, -16), (1216, 0), (1248, 16)), start=1):
        zone(f"catwalk_step_{i}", floor, HANGAR_CEIL, [(2304, y1, 2560, y1 + 32)],
             wall=STEEL, light=LIGHT_HANGAR)
    zone("catwalk_landing", 32, HANGAR_CEIL, [(2304, 1280, 2560, 1344)],
         wall=STEEL, light=LIGHT_HANGAR)
    for i, (y1, floor) in enumerate(((1344, 48), (1376, 64), (1408, 80)), start=4):
        zone(f"catwalk_step_{i}", floor, HANGAR_CEIL, [(2304, y1, 2560, y1 + 32)],
             wall=STEEL, light=LIGHT_HANGAR)

    # Z6b catwalk along the north wall, 96 up, from x 1792 (v2: the sight
    # line from SW-A to D4 crosses the north wall's first 300 units).
    CATWALK_WEST = 1792
    zone("z6b_catwalk", 96, HANGAR_CEIL, [(CATWALK_WEST, 1440, 2560, 1600)],
         wall=STEEL, light=LIGHT_CATWALK)
    lamp("z6b_catwalk", 1, (1856, 1504, 1920, 1568))
    lamp("z6b_catwalk", 2, (2112, 1504, 2176, 1568))
    zone("d6_recess", 96, 96 + DOOR_LEAF_HEIGHT, [(2432, 1536, 2560, 1600)],
         wall=STEEL, light=LIGHT_CATWALK)
    # Two columns stand on the catwalk's front edge: the cover the v2 note
    # left to v3 as "a balance decision". A parapet was the alternative and
    # is not built: 32 of plate is a cut texture, 64 hides the hangar from
    # the eye (41) of the player the catwalk is built for.
    column(1952, 1440, 1984, 1472)
    column(2272, 1440, 2304, 1472)

    # S2, the loose panel off the catwalk: the RPG-7 closet. v3's clue, the
    # one section 7 always promised: a lit SLIT in the hangar's north wall
    # above the catwalk, beside the panel, "where there should be none". It
    # is seen from the hangar floor and from the catwalk, and it is too
    # thin to climb through; the panel under it is the way in.
    s2_panel = door("s2_panel", 96, TAG_S2_CATWALK_PANEL, (2176, 1600, 2240, 1632),
                    light=LIGHT_CATWALK)
    zone("s2_closet", 96, 192, [(2112, 1632, 2304, 1792)], wall=STEEL,
         light=LIGHT_S2, special=SECTOR_SPECIAL_SECRET)
    zone("s2_slit", 160, 176, [(2256, 1600, 2304, 1632)], wall=STEEL, light=LIGHT_S2_SLIT)

    # --- the south gantry: the hangar's second high place ------------------
    # A maintenance gantry along the south wall, 96 over the floor, reached
    # by a five-step stair at its west end and dropped off anywhere along
    # its front. In the first contact two riflemen hold it; in wave 2 it is
    # where the player can stand to see the closets open.
    for i in range(5):
        x1 = 1376 + i * 32
        like("z6_hangar", f"gantry_step_{i + 1}", [(x1, 320, x1 + 32, 384)],
             floor=HANGAR_FLOOR + (i + 1) * STEP, wall=STEEL)
    like("z6_hangar", "gantry", [(1536, 320, 2240, 384)], floor=HANGAR_FLOOR + 6 * STEP,
         wall=STEEL)
    column(1728, 384, 1760, 416)
    column(2016, 384, 2048, 416)

    # --- the hangar lamps ------------------------------------------------
    for n, x in enumerate((1216, 1472, 1728, 1984, 2240, 2496), start=1):
        lamp("z6_hangar", n, (x, 448, x + 64, 512))
    for n, x in enumerate((1472, 1728, 1984, 2176), start=7):
        lamp("z6_hangar", n, (x, 1280, x + 64, 1344))
    # v3: one more over the east field, where wave 2 comes out of the east
    # wall and the player crosses from the catwalk stair to D4.
    lamp("z6_hangar", 11, (2592, 1248, 2656, 1312))

    # --- columns: the roof has to stand on something -----------------------
    # Five free-standing steel columns on plinths: two in the west strip,
    # two in the south band between the lamps and lane A, one in the east
    # field between the cradle and the catwalk stair. None on a tested sight
    # line. Then pilasters: steel ribs carved into the long concrete walls.
    for name, x, y in (("c1", 1216, 640), ("c2", 1216, 896), ("c3", 1600, 512),
                       ("c4", 2112, 512), ("c5", 2368, 1056)):
        column(x, y, x + 64, y + 64, plinth_of="z6_hangar", name=name)
    for x1, y1, x2, y2 in ((1152, 448, 1168, 512), (1152, 960, 1168, 1024),
                           (2672, 384, 2688, 448), (2672, 928, 2688, 992),
                           (2672, 1440, 2688, 1504), (1600, 1584, 1664, 1600),
                           (2560, 320, 2624, 336)):
        column(x1, y1, x2, y2)

    # --- the crate piles: the hangar's low cover --------------------------
    crate("h1", "z6_hangar", (1184, 352, 1312, 416), 64, exposed="nsew")
    crate("h2", "z6_hangar", (1792, 544, 1920, 608), 64, exposed="nsw")
    crate("h3_stack", "z6_hangar", (1920, 544, 1984, 608), 128, exposed="nsew")
    crate("h4", "z6_hangar", (2368, 352, 2496, 416), 64, exposed="nsew")
    crate("h5", "z6_hangar", (2112, 1344, 2176, 1408), 64, exposed="nsew")
    # Three single crates where the first contact and wave 2 want cover:
    # the west strip by the stair foot, the south-west by the gantry stair,
    # and the east field the player crosses from the catwalk to D4.
    crate("h6", "z6_hangar", (2432, 960, 2496, 1024), 64, exposed="nsew")
    crate("h7", "z6_hangar", (1216, 1008, 1280, 1072), 64, exposed="nsew")
    crate("h8", "z6_hangar", (1392, 432, 1456, 496), 64, exposed="nsew")

    # --- shadows (section 6: "144 in the bay shadows and under the catwalk")
    # One step darker than the hangar: the strip of floor under the
    # catwalk's lip, and the strip in front of the gantry.
    like("z6_hangar", "shadow_catwalk", [(1792, 1408, 2304, 1440)],
         light=LIGHT_HANGAR - LAMP_STEP)
    like("z6_hangar", "shadow_gantry", [(1536, 384, 2240, 432)],
         light=LIGHT_HANGAR - LAMP_STEP)
    # ...and the transporter's own shadow on the floor along both long
    # sides of the cradle, which the lamp rows light from north and south.
    like("z6_hangar", "shadow_cradle_s", [(1600, 784, 2240, 832)],
         light=LIGHT_HANGAR - LAMP_STEP)
    like("z6_hangar", "shadow_cradle_n", [(1600, 1216, 2240, 1264)],
         light=LIGHT_HANGAR - LAMP_STEP)

    # --- wave 2: three closets in the hangar walls (tag 11, SW-B) ----------
    # Concrete panels in concrete walls: invisible until they move, except
    # for the seam a sharp eye catches (a leaf hangs from the top, the wall
    # stands on the floor, and 320 is not a whole number of panels).
    closet("closet_w1", (1136, 576, 1152, 704), (1024, 560, 1136, 720),
           TAG_HANGAR_WAVE_2, leaf=CONC)
    closet("closet_w2", (1136, 768, 1152, 896), (1024, 752, 1136, 912),
           TAG_HANGAR_WAVE_2, leaf=CONC)
    closet("closet_e1", (2688, 1216, 2704, 1344), (2704, 1200, 2816, 1360),
           TAG_HANGAR_WAVE_2, leaf=CONC)

    # --- V3 A2: the closets the weapons open (design section 20) -----------
    # Concrete panels in concrete walls, as wave 2's: wall until they move.
    for name, (event, (panel, room), floor) in EVENT_CLOSETS.items():
        closet(name, panel, room, event.tag, leaf=CONC, floor=floor)

    # --- the hangar's two portraits (design section 6.1) ------------------
    # 16-deep niches, 256 over the hangar floor: the poster whole, the
    # hangar's concrete above it. Too shallow to stand in; the floor is the
    # hangar's, so nothing on any route changes.
    like("z6_hangar", "z6_stalin_niche", [STALIN_NICHE], ceil=HANGAR_FLOOR + POSTER_HEIGHT)
    like("z6_hangar", "z6_slot_niche", [HANGAR_SLOT_NICHE],
         ceil=HANGAR_FLOOR + POSTER_HEIGHT)

    # ======================================================================
    # Act 3b - fuel bay (SW-A) and the sump secret under it
    # ======================================================================
    zone("fuel_passage", HANGAR_FLOOR, 160, [(1152, 1600, 1280, 1664)],
         flat=LANE, wall=STRIPE, light=LIGHT_BEACON)
    zone("z7_fuel_bay", HANGAR_FLOOR, 160, [(1152, 1664, 1600, 1984)],
         wall=STEEL, light=LIGHT_FUEL_BAY)
    lamp("z7_fuel_bay", 1, (1280, 1888, 1344, 1952))
    # A fuel tank on its plinth: the ambush's cover. And from the plinth a
    # drain runs west, one PLINTH below the floor, and stops at the bay's
    # west wall. S3's clue (v3): spilt fuel runs downhill, and the drain
    # goes somewhere. v2 pointed a yellow lane at that wall, which is the
    # traffic sign the rest of the map uses for "go here" - so it read as a
    # door. The drain is plain concrete: it is found by a player who asks
    # where it goes.
    column(1440, 1792, 1536, 1888, plinth_of="z7_fuel_bay", name="tank")
    column(1248, 1792, 1312, 1856, plinth_of="z7_fuel_bay", name="tank_2")
    like("z7_fuel_bay", "fuel_drain", [(1152, 1744, 1424, 1776)],
         floor=HANGAR_FLOOR - PLINTH)
    # The fuel lines: a run of pipe under the ceiling down the east wall.
    like("z7_fuel_bay", "fuel_pipes", [(1568, 1664, 1600, 1984)], ceil=128, wall=STEEL)

    # SW-A's alcove and its window onto the hangar: the v1 playtest's answer
    # (design section 16.1). Unchanged in v3.
    alcove_floor = HANGAR_FLOOR + SWITCH_PLATFORM
    zone("z7_switch_alcove", alcove_floor, alcove_floor + SWITCH_HEIGHT,
         [(1344, 1600, 1472, 1664)], TAG_LIGHT_GATE_POWER, wall=STEEL,
         ceiling=CEIL_LAMP, light=LIGHT_SWITCH_READY)
    zone("fuel_window", alcove_floor + WINDOW_SILL, alcove_floor + SWITCH_HEIGHT,
         [(1344, 1584, 1536, 1600)], light=LIGHT_BEACON)

    # The ambush (tag 10, SW-A): steel panels in the bay's steel walls,
    # behind the player as he stands at the switch.
    closet("closet_a1", (1216, 1984, 1344, 2000), (1200, 2000, 1360, 2112),
           TAG_FUEL_BAY_AMBUSH, leaf=STEEL)
    closet("closet_a2", (1408, 1984, 1536, 2000), (1392, 2000, 1552, 2112),
           TAG_FUEL_BAY_AMBUSH, leaf=STEEL)
    closet("closet_a3", (1600, 1792, 1616, 1920), (1616, 1776, 1728, 1936),
           TAG_FUEL_BAY_AMBUSH, leaf=STEEL)

    s3_panel = door("s3_panel", HANGAR_FLOOR, TAG_S3_SUMP_PANEL, (1120, 1728, 1152, 1792),
                    light=LIGHT_FUEL_BAY)
    zone("sump_step_1", -48, 64, [(1088, 1728, 1120, 1792)], wall=STEEL, light=LIGHT_FUEL_BAY)
    zone("sump_step_2", -64, 64, [(1056, 1728, 1088, 1792)], wall=STEEL, light=LIGHT_SECRET)
    zone("sump_step_3", -80, 64, [(1024, 1728, 1056, 1792)], wall=STEEL, light=LIGHT_SECRET)
    zone("s3_sump", SUMP_FLOOR, 0, [(896, 1664, 1024, 1856)],
         light=LIGHT_SECRET, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # Act 4 - control booth (SW-B)
    # ======================================================================
    d6 = door("d6", 96, TAG_D6_CATWALK_BOOTH, (2432, 1600, 2560, 1664), light=LIGHT_FLICKER)
    zone("z9_booth", 96, 224, [
        (2560, 1616, 2688, 1664),
        (2432, 1664, 2688, 1856),
    ], TAG_LIGHT_GATE_POWER, flat=TILE, ceiling=CEIL_LAMP, wall=STEEL,
        light=LIGHT_BOOTH_DARK)
    zone("booth_window", 128, 224, [(2560, 1600, 2688, 1616)],
         flat=TILE, ceiling=CEIL_LAMP, wall=STEEL, light=LIGHT_BOOTH_LIT)

    # ======================================================================
    # Act 5 - the two-leaf airlock and the exit lift
    # ======================================================================
    zone("d4_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
         [(2624, 544, 2688, 800)], TAG_LIGHT_GATE_POWER, wall=STRIPE,
         light=LIGHT_GATE_DEAD)
    d4 = door("d4", HANGAR_FLOOR, TAG_D4_HANGAR_AIRLOCK, (2688, 544, 2752, 800),
              light=LIGHT_BEACON)
    zone("z8_airlock", HANGAR_FLOOR, 96, [(2752, 544, 2912, 800)], wall=STEEL,
         light=LIGHT_AIRLOCK)
    lamp("z8_airlock", 1, (2800, 640, 2864, 704))
    # Two decontamination niches, low and steel: where stragglers wait.
    like("z8_airlock", "airlock_niche_n", [(2800, 800, 2864, 832)], ceil=64, wall=STEEL)
    like("z8_airlock", "airlock_niche_s", [(2800, 512, 2864, 544)], ceil=64, wall=STEEL)
    like("z8_airlock", "frame_d5_airlock", [(2896, 592, 2912, 752)], wall=STEEL)
    d5 = door("d5", HANGAR_FLOOR, TAG_D5_AIRLOCK_EXIT, (2912, 608, 2944, 736),
              light=LIGHT_AIRLOCK)
    # Z10, the service lift shaft, exactly 256 high: Lenin's height.
    zone("z10_exit", HANGAR_FLOOR, 224, [(2944, 480, 3264, 864)], light=LIGHT_EXIT)
    # The lift itself: a steel cage floor one PLINTH up, in the middle of
    # the shaft. The Panzermensch stands on it.
    like("z10_exit", "z10_lift", [(3072, 576, 3200, 736)], floor=HANGAR_FLOOR + PLINTH,
         wall=STEEL)
    # Lenin's light (CEO, v2 walk). The poster's wall belongs to the sector
    # in front of it, so that sector IS the light on the poster: a lamp
    # panel over it, and a ring one step dimmer around that.
    like("z10_exit", "lenin_halo", [(3040, 768, 3232, 864)], light=LIGHT_LENIN_HALO)
    like("z10_exit", "lenin_light", [(3072, 800, 3200, 864)], light=LIGHT_LENIN,
         ceiling=CEIL_LAMP)
    # The Marx-Engels slot beside the exit switch gets the halo's light: a
    # strip of lamp panel along the east wall, one step dimmer than Lenin.
    like("z10_exit", "z10_slot_light", [EXIT_SLOT_LIGHT], light=LIGHT_LENIN_HALO,
         ceiling=CEIL_LAMP)
    zone("z10_exit_niche", HANGAR_FLOOR, HANGAR_FLOOR + SWITCH_HEIGHT,
         [(3264, 608, 3296, 672)], ceiling=CEIL_LAMP, light=LIGHT_EXIT_SWITCH)
    zone("d5_recess", HANGAR_FLOOR, HANGAR_FLOOR + DOOR_LEAF_HEIGHT,
         [(2944, 608, 3008, 736)], wall=STEEL, light=LIGHT_EXIT)

    # ======================================================================
    # Doors, switches and the exit
    # ======================================================================
    # ORDER MATTERS from here down. GridMap resolves a segment with the FIRST
    # rule that covers it, so the specific ones (a door leaf, a switch, a
    # poster, a crate face) are registered before the broad wall runs.
    for tag, door_sector, segments in (
        (TAG_D1_DORM_WASHROOM, d1, [("v", 640, 32, 160), ("v", 704, 32, 160)]),
        (TAG_D2_DORM_CORRIDOR, d2, [("h", 448, 192, 320), ("h", 512, 192, 320)]),
        (TAG_D3_KOMNATA_SERVICE, d3, [("v", 640, 1088, 1216), ("v", 704, 1088, 1216)]),
        (TAG_D6_CATWALK_BOOTH, d6, [("h", 1600, 2432, 2560), ("v", 2560, 1616, 1664)]),
    ):
        style = door_raise_style(tag, door_sector, texture=DOOR)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    # The three secret panels: push once, open for good. Plate, like the
    # steel around them.
    for tag, door_sector, segments in (
        (TAG_S1_LOCKER_PANEL, s1_panel, [("v", 960, 64, 128), ("v", 976, 64, 128)]),
        (TAG_S2_CATWALK_PANEL, s2_panel, [("h", 1600, 2176, 2240), ("h", 1632, 2176, 2240)]),
        (TAG_S3_SUMP_PANEL, s3_panel, [("v", 1152, 1728, 1792), ("v", 1120, 1728, 1792)]),
    ):
        style = door_open_style(tag, door_sector, texture=STEEL)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    for door_sector, segments in (
        (d4, [("v", 2688, 544, 800), ("v", 2752, 544, 800)]),
        (d5, [("v", 2912, 608, 736), ("v", 2944, 608, 736)]),
    ):
        style = remote_door_style(door_sector, texture=DOOR)
        for axis, coord, lo, hi in segments:
            (g.style_v if axis == "v" else g.style_h)(coord, lo, hi, style)

    g.style_v(1472, 1600, 1600 + SWITCH_WIDTH, switch_door_open_style(
        TAG_D4_HANGAR_AIRLOCK, texture=SW_A_FACE,
        lighttag=TAG_LIGHT_GATE_POWER, repeatable=False))
    g.style_h(1856, 2528, 2528 + SWITCH_WIDTH, switch_door_open_style(
        TAG_D5_AIRLOCK_EXIT, texture=SW_B_FACE, repeatable=False))
    g.style_v(3296, 608, 608 + SWITCH_WIDTH, exit_switch_style(texture=EXIT_FACE))

    # --- the crate faces, columns and the dorm lockers ----------------------
    for axis, coord, lo, hi, face in crate_faces:
        (g.style_v if axis == "v" else g.style_h)(
            coord, lo, hi, LineStyle(texture=face, peg_bottom=False))
    for x1, y1, x2, y2, texture in solid_faces:
        face = LineStyle(texture=texture)
        g.style_h(y1, x1, x2, face)
        g.style_h(y2, x1, x2, face)
        g.style_v(x1, y1, y2, face)
        g.style_v(x2, y1, y2, face)
    g.style_v(0, 64, 320, LineStyle(texture=LOCKER))
    # The hangar's south wall stays concrete above the gantry and its stair:
    # those one-sided lines belong to the gantry sectors, whose material
    # (steel) is for their FRONT face, not for the wall they stand against.
    g.style_h(320, 1376, 2240, LineStyle(texture=CONC))

    # --- the plaque and the posters (POSTERS) -----------------------------
    g.style_h(448, 352, 480, LineStyle(texture=PLAQUE))
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))

    # --- the red route ----------------------------------------------------
    g.style_v(192, 512, 960, LineStyle(texture=STRIPE))      # Z3, both walls
    g.style_v(320, 512, 960, LineStyle(texture=STRIPE))
    g.style_v(640, 960, 1088, LineStyle(texture=STRIPE))     # Z4, either side of D3
    g.style_v(640, 1216, 1408, LineStyle(texture=STRIPE))
    g.style_h(1088, 704, 1152, LineStyle(texture=STRIPE))    # Z5, both walls
    g.style_h(1216, 704, 896, LineStyle(texture=STRIPE))
    g.style_h(1216, 1024, 1152, LineStyle(texture=STRIPE))
    g.style_v(1152, 1216, 1600, LineStyle(texture=STRIPE))   # hangar west wall
    g.style_h(1600, 1152, 1280, LineStyle(texture=STRIPE))   # lintel over the mouth
    g.style_v(2624, 544, 800, LineStyle(texture=STRIPE))     # D4's frame
    g.style_h(544, 2624, 2688, LineStyle(texture=STRIPE))
    g.style_h(800, 2624, 2688, LineStyle(texture=STRIPE))

    # Design section 13, point 5, decided by D121: the night sky is the
    # cradle's open launch slot (above, Z6a).
    g.build()

    tm.add_thing(
        Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START, angle=PLAYER_ANGLE)
    )
    for _zone, kind, x, y, angle, tier in MONSTERS:
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle))
    for _zone, ednum, x, y, top in ITEMS:
        if ednum in PICKUP_EVENTS:
            tm.add_thing(event_thing(x, y, ednum, PICKUP_EVENTS[ednum]))
        else:
            tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top)))
    for _zone, ednum, x, y, lowest in AMMO:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(lowest)))
    for _zone, ednum, x, y in FIXTURES:
        tm.add_thing(Thing(x=x, y=y, type=ednum))
    for _zone, piece, reach, x, y, angle in RADIOS:
        tm.add_thing(Thing(x=x, y=y, type=ED_RADIO, angle=angle,
                           extra={"arg0": piece, "arg1": reach}))
    for _zone, x, y, lines, reach, flags, jingle in LOUDSPEAKERS:
        mask = sum(1 << (line - 1) for line in lines)
        tm.add_thing(Thing(x=x, y=y, type=ED_LOUDSPEAKER,
                           extra={"arg0": mask, "arg1": reach, "arg3": flags, "arg4": jingle}))

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
WALL_TEXTURES = (CONC, STRIPE, STEEL, DOOR, PLAQUE, LENIN, MURAL, STALIN,
                 CRATE_FACE, CRATE_LONG, LOCKER) + SWITCH_FACES + MARX_ENGELS
FLAT_TEXTURES = (LANE, CONCRETE_FLOOR, TILE, CEIL_LAMP, CEIL, CRATE_TOP)
# The engine's own flats, not lumps of ours (check_pk3 knows them).
BUILTIN_FLATS = (SKY,)
