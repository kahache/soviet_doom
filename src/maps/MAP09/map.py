"""MAP09 "Tunguska" (Тунгуска), episode 3's last map - v1.

Design document: docs/levels/MAP09-tunguska.md (section 4 is the plan,
section 5 the route, section 10 the population).
D112 opens episode 3, "The Portal": MAP07 the Arctic radar station, MAP08 the
Northern Fleet's submarine base, and this map, the episode's and the
campaign's end. The Podkamennaya Tunguska, central Siberia, November 1977:
the site of the 1908 event, where the invaders keep their MAIN portal (the
one at Tankograd was a secondary one, SD_END03_TEXT's hook). Sergeant
Vilanova comes in by the railway from MAP08 to a railhead in the dead taiga,
walks the old forest road through the trees the 1908 blast laid flat, takes
the pass to the epicentre in the abandoned Soviet research station, crosses
the standing dead forest at the epicentre, the invaders' works that are
eating it, their refinery, and goes down into the crater to the portal, the
campaign's last boss, and the breaker that shuts the portal.

Built v1 straight away, MVP first (D60): the whole plan, with approved and
packed lumps only, populated and stocked. v1.1 (D113) dresses it in the
episode's own "Taiga/Alien" set: burnt earth, peat and moss underfoot, charred
larch and the odd birch for the trunks and the treeline, log walls for the
huts and the palisade, the invaders' organic metal and glyph plates for their
works and the crater, green acid in their pits (the refinery keeps its molten
metal), the portal framed, the blue door's own leaf and a cab on the
locomotive. What the set does not draw is still listed under "Pending
textures" in the design document.

The route, in one line: the railhead (the train he came on, the halt) ->
west along the forest road through the fallen taiga -> the station's gate
(the BLUE gate in the invaders' fence seen at once) -> the laboratory, the
BLUE KEY on its bench -> the blue gate -> the standing dead forest -> the
invaders' works (the RED gate of the crater's containment wall, the YELLOW
door of the refinery and the YELLOW KEY on the derrick all seen from the
forest's edge) -> up the derrick's stair over the acid pit, the yellow key
-> the yellow door -> the refinery, across its molten channel, the RED KEY
on its dais (taking it opens two closets in the works, behind the player)
-> back through the works to the red gate -> the crater's rim, down its
seven terraces to the floor, the portal and the boss -> his death opens the
containment's control bunker -> the breaker: the portal shuts, the
episode ends.

Three things flagged for the PM's engine pass (D26: this role never starts
GZDoom), each as MAP06 v1.1 left it:

* open air at several sky heights (railhead and taiga 320, station 256,
  forest 448, works and crater 512) and roofed buildings as closed sky
  blocks (the halt, the izbas): Doom's sky hack, NOT VERIFIED in engine;
* the exit depends on a death: the boss's thing carries Door_Open on
  TAG_BOSS_EXIT and NO line carries that tag. It stands at MAP09_BOSS_SPOT:
  since D116 the Consortium (BOSS_KIND), episode 3's own final boss, the
  portal behind it;
* a key that springs an ambush: the red key's thing carries Door_Open on
  TAG_AMBUSH (Hexen-style item special). NOT VERIFIED in engine.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method;
the fallen trunks lie radially from the crater's centre, the diagonal ones
as staircases of 48-unit blocks (GridMap is axis-aligned).

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP09 SKILL=3 tools/run.sh
"""

from __future__ import annotations

from typing import NamedTuple

import math
from dataclasses import replace

from sdbuild.udmf import (
    DOOR_SPEED_SLOW,
    SECTOR_SPECIAL_LIGHT_FLICKER,
    SECTOR_SPECIAL_SECRET,
    SPECIAL_DOOR_OPEN,
    GridMap,
    LineStyle,
    Sector,
    TextMap,
    Thing,
    door_open_style,
    exit_switch_style,
    remote_door_style,
    skill_tier,
)

MAP_NAME = "MAP09"

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# Soviet base
CONCRETE = "SDCONC1"    # the laboratory's outer walls and vestibule
STEEL = "SDSTEL1"       # the buffer stop, the signal post, the mast, the derrick, the bunker's hall
CRATE = "SDCRAT1"       # stores in the station
CRATE_TOP = "SDCRTOP1"  # planks: the halt's and the izbas' floors and ceilings, the platform
LOCKER = "SDLOCK1"      # the halt's row of lockers (S1)
LAB_FLOOR = "SDFLR3"    # grey two-tone tiles: the laboratory
CEIL_LAMP = "SDCEIL1"   # the laboratory's fluorescent panels
CEIL_CONCRETE = "SDCEIL2"
EXIT_FACE = "SDSW1D"    # the hazard panel every map's exit wears: the portal's breaker
# Metro
TILE = "SDTILE1"        # the laboratory's hall
TILE_DADO = "SDTILE2"   # the instrument room (128 high: one tile, its dado whole)
# Tankograd
BRICK = "SDBRCK1"       # the refinery (the invaders build with what they take)
RUST = "SDRUST1"        # the refinery's vats
DOOR_YELLOW = "SDDOORY"
DOOR_RED = "SDDOORR"
PORTAL = "SDPORT1"      # the portal's field, animated SDPORT1-4 (ANIMDEFS); the towers' cores
GATE = "SDGATE1"        # the control bunker's gate (the boss's death opens it)
FLAG_USSR_1 = "SDFLAG1"
FLAG_USSR_2 = "SDFLAG2"
PLATE = "SDFLR4"        # the works' and the refinery's floors, the crater's floor
GRATING = "SDGRAT1"     # the refinery's bridge
MOLTEN = "SDMOLT1"      # the refinery's channel and vats, animated SDMOLT1-4 (ANIMDEFS)
# Railway (episode 2)
TRACK = "SDTRAK1"       # the railhead's track, rails along the flat's y: turned a quarter
BALLAST = "SDBLST1"     # the railhead's ballast, under and beside the track
WAGON = "SDWAGN1"       # the goods wagon; the platform's planked edge
ARMOUR_STAR = "SDARMR1"     # the armoured wagon's flanks, a star per 128
ARMOUR = "SDARMR2"      # the armoured wagon's ends; the locomotive's boiler and cab outside
SIGNAL = "SDSIGL1"      # the railhead's signal: single use only (D107), one 64 face
CAB_FRONT = "SDCAB1"    # the locomotive's cab, inside, looking forward: one 128 face, never tiled
CAB_SIDE = "SDCAB2"     # the cab's sides and back from inside, 64 a window
# Episode 2, round 2
DOOR = "SDDOORB"        # the blue gate's leaf: the blue key door (D113)
# Taiga/Alien (episode 3, D113; docs/art/TEXTURE-INDEX.md "Taiga/Alien")
BURNT = "SDBURN1"       # the 1908 blast's burnt ground, charred trunks lying one way: the fallen
                        # taiga (turned, BURNT_TURN), the works' edge, the crater's rim and terraces
PEAT = "SDPEAT1"        # the Southern Swamp's peat under the standing forest
MOSS = "SDMOSS1"        # moss and lichen: the railhead's yard, the station's clearing, birch logs' tops
BARK = "SDBARK2"        # charred larch: the treeline, the fallen and the standing trunks
BIRCH = "SDBARK1"       # birch, the one tree that came back: the odd trunk among the larch
LOG_WALL = "SDLOGW1"    # round logs and moss: the halt, the izbas, the station's palisade
ALIEN = "SDALNM1"       # the invaders' organic metal: the works, the fence, the containment, the crater
GLYPH = "SDGLYP1"       # their glyph plates, 64 wide: the towers, the pylons, either side of two gates
PORTAL_RIM = "SDPRTE1"  # the portal's frame: the four posts at the field's corners
ACID = "SDACID1"        # their acid, animated SDACID1-4 (ANIMDEFS); the damage is the sector's
# Dam (episode 2)
TURBINE = "SDTURB1"     # the refinery's machines
CONTROL = "SDCTRL1"     # the laboratory's instrument boards, the refinery's console
# The engine's sky marker; MAPINFO's sky1 says which picture (a taiga night is pending).
SKY = "F_SKY1"

# The approved posters (CEO 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py). All in the research station.
LENIN = "SDPOSTR1"
STALIN = "SDPOSTR3"
MURAL = "SDPOSTR2"      # 128x128 cosmonautics mural: the instrument room
POSTER_WIDTH = 128
POSTER_HEIGHT = 256
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS

DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_RED, GATE)
SWITCH_FACES = (EXIT_FACE,)
SWITCH_HEIGHT = 128
TILE_SIZE = 128

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED on MAP02
# and MAP03; delay 0 opens it for good. Locks from gzdoom.pk3 lockdefs.txt.
SPECIAL_DOOR_LOCKED_RAISE = 13
LOCK_RED_CARD = 1
LOCK_BLUE_CARD = 2
LOCK_YELLOW_CARD = 3
ED_BLUE_CARD = 5
ED_YELLOW_CARD = 6
ED_RED_CARD = 13
KEY_LOCKS = {ED_BLUE_CARD: LOCK_BLUE_CARD, ED_YELLOW_CARD: LOCK_YELLOW_CARD,
             ED_RED_CARD: LOCK_RED_CARD}
ED_PLAYER1_START = 1

# Molten metal and acid hurt alike: MAP03's UDMF sector fields, 10 every 32
# tics (Doom's hellslime). The flat only looks the part; the damage is the
# sector's. Every pit is one step deep: walked out of, never a trap.
LAVA_DAMAGE = 10
LAVA_DAMAGE_INTERVAL = 32
LAVA_HURTS = {"damageamount": LAVA_DAMAGE, "damageinterval": LAVA_DAMAGE_INTERVAL}
# Which pits hold what: green acid where the invaders work (the works, the
# crater round the portal), molten metal where they smelt (the refinery).
WORKS_PIT_FLAT = ACID
CRATER_PIT_FLAT = ACID
CHANNEL_FLAT = MOLTEN
# The burnt ground's charred trunks run about 20 degrees off the flat's x;
# a quarter turn lays them about 70 degrees off the map's x whichever way the
# engine turns (NOT VERIFIED in engine): roughly radial from the crater across
# the fallen taiga, like the props.
BURNT_TURN = 90.0

# --- Heights ----------------------------------------------------------------
GROUND = 0
STEP = 16               # every stair step and terrace; under MAX_STEP_UP 24
STEP_DEPTH = 32
DOOR_HEIGHT = 128
NICHE_DEPTH = 16
CLOSET_HEIGHT = 128
HUT_FLOOR = GROUND + STEP       # the halt, the izbas, the laboratory: one step up
HUT_CEIL = HUT_FLOOR + 128      # 144
ROOF = 160              # the halt's and the izbas' roofs: closed sky blocks
LAB_CEIL = HUT_FLOOR + POSTER_HEIGHT    # 272: the hall is a poster high
BENCH_TOP = HUT_FLOOR + STEP
PLATFORM = GROUND + STEP
LOG = 32                # a fallen trunk: not a step (MAX_STEP_UP 24), seen over (eye 41)
WAGON_TOP = 128         # one tile of planking or armour
BUFFER_TOP = 48
SIGNAL_TOP = 128
MAST_TOP = 224
PIPE = 96               # the works' conduits: cover, not climbable
TOWER = 256             # a tower's body of the invaders' metal
TOWER_CORE = TOWER + TILE_SIZE      # its glowing core, one tile of the portal's field
DERRICK = 128           # the yellow key's platform: 8 steps up
LAVA = GROUND - STEP    # a pit (acid or molten): one step down
VAT = 96
TURBINE_TOP = TILE_SIZE
CONSOLE = TILE_SIZE
REFINERY_CEIL = 320
TERRACES = 7            # the crater: seven terraces of 16 down to its floor
CRATER_FLOOR = GROUND - STEP * (TERRACES + 1)   # -128
PORTAL_PLINTH = CRATER_FLOOR + 2 * STEP         # -96
PORTAL_TOP = PORTAL_PLINTH + 2 * TILE_SIZE      # 160: two whole tiles of the field
PYLON = 128
DAIS_TOP = GROUND + STEP
# The skies (each one-sided wall shows as high as the sector it bounds).
RAIL_SKY = 320
TAIGA_SKY = 320
STATION_SKY = 256
FOREST_SKY = 448        # the standing trunks rise out of sight: the "telegraph forest"
WORKS_SKY = 512
CRATER_SKY = 512

# --- Light ---------------------------------------------------------------------
# A November night in the taiga; 192 is spent on the three locks, the three
# keys and the exit, nowhere else.
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_RAIL = 128
LIGHT_HALT = 112
LIGHT_TAIGA = 112
LIGHT_STATION = 128
LIGHT_IZBA = 112
LIGHT_LAB = 144
LIGHT_INSTR = 128
LIGHT_FOREST = 104
LIGHT_WORKS = 144
LIGHT_EDGE = 120
LIGHT_LAVA = 176
LIGHT_GLOW = 176        # the portal's field and the towers' cores
LIGHT_REFINERY = 128
LIGHT_CRATER = 160
LIGHT_PORCH = 128
LIGHT_EXIT_HALL = 128
LIGHT_CLOSET = 112
LIGHT_SECRET = 112
LIGHT_CLUE = LIGHT_MIN  # the odd one out of a row: in shadow (MAP01's rule)
BEACON_ZONES = ("z3_blue_portal", "z3_key_bench", "z5_yellow_portal", "z5_key_top",
                "z5_red_portal", "z6_key_dais", "z9_exit_niche")

BLUE = 0x90A8FF         # MAP02's PASS_BLUE
YELLOW = 0xFFD860
RED = 0xFF6048
BLUE_LIGHT = {"lightcolor": BLUE}
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_S1_PANEL = 1        # the halt: the locker set back in shadow
TAG_S2_PANEL = 2        # the instrument room: the board set back in shadow
TAG_S3_PANEL = 3        # the works: the pipe recess set back deeper and darker
TAG_BLUE_DOOR = 4       # the gate in the invaders' fence: lock 2
TAG_YELLOW_DOOR = 5     # the refinery's door: lock 3
TAG_RED_DOOR = 6        # the crater's containment gate: lock 1
TAG_AMBUSH = 10         # the works' two closets; ONLY the red key's pickup opens them
TAG_BOSS_EXIT = 12      # the control bunker's gate; ONLY the boss's death opens it
# V3 (D120, A2 and A3): tags only a pickup moves (no line carries them).
TAG_QUARANTINE = 13     # the blue key: the laboratory's quarantine room opens, the Legion inside
TAG_WORKS_LIFT = 14     # the yellow key: the works' cargo lift comes down with three of theirs
# Tag 15 is kept for the crater's Breach (design section 18.3): the boss's
# second phase sinking the crater's ground needs ZScript, mod-engineer's.
LIFT_SPEED = 8          # 1 unit a tic: the car's 128 take ~3.7 s, its winch heard all the way
# Floor_LowerToLowest (tag, speed): 21 in ZDoom's (Hexen's) special table, the
# special MAP04's red key gives its gondolas. NOT VERIFIED in our engine runs
# (MAP04's K3; here the checklist's E12): if it failed, the works' lift would
# stay up, and nothing the route needs is in it.
SPECIAL_FLOOR_LOWER_TO_LOWEST = 21
SECRET_PANEL_TAGS = (TAG_S1_PANEL, TAG_S2_PANEL, TAG_S3_PANEL)

# --- The boss --------------------------------------------------------------------
# Episode 3's final boss, the Consortium (D112, in the mod since D116;
# docs/engine/2026-10-22_P4_ep3-final-boss.md). It replaced the General, who
# stood in until it existed: the spot, the facing and the death special did not
# move. Rooted in phase 1, it calls its servants through the portal BEHIND it
# (144 behind, 80 to either side): it faces north, the red gate, so the portal
# (PORTAL_BASE, 192 south of the spot) is at its back (tested).
CRATER_CENTRE = (3968, 2816)    # the portal; the fallen trunks lie away from it
MAP09_BOSS_SPOT = (3968, 3136)  # on the crater's floor before the portal, facing the red gate
BOSS_ANGLE = 90
BOSS_KIND = "consortium"
BOSS_DEATH_SPECIAL = (SPECIAL_DOOR_OPEN, (TAG_BOSS_EXIT, DOOR_SPEED_SLOW, 0, 0, 0))
RED_KEY_SPECIAL = (SPECIAL_DOOR_OPEN, (TAG_AMBUSH, DOOR_SPEED_SLOW, 0, 0, 0))

# --- Things --------------------------------------------------------------------
PLAYER_START = (7296, 640)
PLAYER_ANGLE = 180      # on the halt's platform beside the train, facing west down the line
BLUE_KEY_SPOT = (1568, 1424)    # on the laboratory's bench
YELLOW_KEY_SPOT = (4128, 5024)  # on the derrick, at the head of its stair
RED_KEY_SPOT = (7168, 4736)     # on the refinery's dais
KEY_ZONES = {ED_BLUE_CARD: "z3_key_bench", ED_YELLOW_CARD: "z5_key_top",
             ED_RED_CARD: "z6_key_dais"}
LOCK_PORTALS = {LOCK_BLUE_CARD: "z3_blue_portal", LOCK_YELLOW_CARD: "z5_yellow_portal",
                LOCK_RED_CARD: "z5_red_portal"}

PROP_PREFIX = "prop_"
SECRET_ZONES = ("s1_store", "s2_store", "s3_store")
CLOSET_PREFIX = "closet_"

# --- V3: events on pickup and the set pieces (D120's A2 and A3) -----------------
# A thing whose UDMF `special` GZDoom runs when it is picked up (the red
# key's closets are the first; the Door_Open form VERIFIED in the engine by
# tunguska-critical's RKEY, 2026-10-23). Each event's tag is carried by no
# line; its monsters wait where no line has an opening (nothing sees or
# hears them) until it fires; a flickering lamp (sector special 65) stands in
# front of each new one, seen before it fires. None is on the critical path,
# none shuts the player in. Design document section 18;
# tests/_pickup_events_e3.py checks them.
class PickupEvent(NamedTuple):
    name: str
    trigger: int                      # editor number of the thing that carries the special
    spot: tuple[int, int]             # where that thing lies
    special: int
    args: tuple[int, ...]             # the tag first
    zones: tuple[str, ...]            # the sectors the tag moves
    waiting: tuple[str, ...]          # where the released monsters wait
    lamp: str                         # the warning lamp, in front of the event


# A2, the quarantine room: in the laboratory hall's east wall, north of the
# vestibule, a door that is the hall's tile until it moves; the blue key
# taken, it opens on the Legion's three. Its lamp is the strip of hall in
# front of it.
QUARANTINE_DOOR = (1792, 1488, 1808, 1552)
QUARANTINE = (1808, 1488, 1952, 1584)
QUARANTINE_LAMP = (1776, 1488, 1792, 1552)    # short of the north wall: Marx's slot stays whole
# A3, the works' cargo lift: in the works' north wall, east of the
# recesses, a gate a door high; its car waits up at 128 behind it, its steel
# face under the gate's lintel, until the yellow key brings it down.
WORKS_LIFT_GATE = (4992, 5632, 5120, 5664)
WORKS_LIFT_CAR = (4992, 5664, 5120, 5792)
LIFT_CAR_FLOOR = GROUND + DOOR_HEIGHT
LIFT_CAR_HEIGHT = 128
LIGHT_EVENT_LAMP = 160   # each new event's lamp, flickering down to its darkest neighbour
EXIT_ZONES = ("z9_hall", "z9_exit_niche")

# --- Plan (design document section 4) ----------------------------------------
# Z1 The railhead (south-east): the track, the train he came on, the halt.
RAIL_BALLAST = (5888, 384, 7552, 576)
RAIL_TRACK = (5888, 448, 7552, 512)
RAIL_YARD = (5888, 576, 6784, 1152)
RAIL_PLATFORM = (6016, 576, 7488, 704)
HALT_ROOF = (6784, 704, 7296, 1024)
HALT = (6848, 736, 7232, 960)
HALT_DOOR = (6976, 704, 7104, 736)
BUFFER = (5888, 432, 5952, 528)
SIGNAL_POST = (5920, 608, 5984, 672)    # its east face, towards the platform, wears SDSIGL1
TRAIN = (("wagon", (6080, 432, 6464, 528), WAGON),
         ("armour", (6528, 432, 7040, 528), ARMOUR),
         ("loco", (7104, 432, 7344, 528), ARMOUR))     # the boiler; the cab behind it
# The locomotive's cab at its east end, wider and taller than the boiler like
# a real one, a room the player can step into from the platform's side: one
# 128 face of SDCAB1 forward (the backhead), SDCAB2 on the sides and back.
CAB_SHELL = (7344, 416, 7488, 560)
CAB_WALL = 8
CAB = (7352, 424, 7480, 552)            # 128 x 128 inside
CAB_DOOR = (7416, 552, 7480, 560)       # in the north side, at the back, towards the platform
LOCKERS_X = 7232
LOCKERS_Y = (768, 832, 896, 960)        # three lockers; the middle one is S1's panel
S1_Y = (832, 896)
# Z2 The fallen taiga: the 1908 blast laid the forest flat, every trunk
# pointing away from the epicentre. (centre x, centre y, length).
TAIGA = (2304, 384, 5888, 1408)
LOGS = ((2560, 1216, 256), (2944, 1152, 256), (3392, 1216, 256), (3840, 1152, 256),
        (4288, 1216, 256), (4736, 1152, 256), (5184, 1216, 256), (5568, 1152, 256),
        (2752, 704, 256), (3200, 768, 256), (3648, 704, 256), (4096, 768, 256),
        (4544, 704, 256), (4992, 768, 256), (5440, 704, 256))
LOG_WIDTH = 32
LOG_BLOCK = 48          # a diagonal trunk: a staircase of blocks, one per 32 along it
LOG_STAIR = 32
BIRCH_LOGS = (3, 8, 13)     # of the fifteen (numbered from 1), birch, moss on top; the rest larch
# The treeline is charred larch; here and there a birch, one 64 face to the
# sky: (axis, line, start). Every one on a wall with the void behind it.
TREELINE_BIRCHES = (("h", 384, 2560), ("h", 384, 3456), ("h", 384, 4352), ("h", 384, 5248),
                    ("h", 384, 6272), ("h", 384, 7104),
                    ("h", 1408, 2816), ("h", 1408, 3712), ("h", 1408, 4608), ("h", 1408, 5504),
                    ("v", 1024, 2560), ("v", 1024, 3584), ("h", 4608, 1536), ("h", 4608, 2304))
BIRCH_WIDTH = 64
# Z3 The research station: a palisaded clearing, three izbas, the laboratory.
STATION_YARD = (512, 448, 2240, 1856)
STATION_GATE = (2240, 768, 2304, 1088)
IZBAS = {"a": (640, 576, 1024, 896), "b": (640, 1088, 1024, 1408), "c": (640, 1536, 1024, 1792)}
IZBA_WALL = 32
IZBA_DOOR = 128
MAST = (1600, 640, 1664, 704)
LAB = (1312, 896, 2048, 1600)
LAB_HALL = (1344, 1280, 1792, 1568)
LAB_VEST = (1792, 1344, 2048, 1472)
LAB_INSTR = (1344, 1120, 1792, 1248)
LAB_INSTR_DOOR = (1536, 1248, 1664, 1280)
KEY_BENCH = (1536, 1392, 1600, 1456)
BOARDS_Y = 1120
BOARDS_X = (1376, 1504, 1632, 1760)     # three boards of SDCTRL1; the middle one is S2's panel
S2_X = (1504, 1632)
# The gate in the invaders' fence: portal, door, porch, through the fence.
BLUE_GATE_X = (1920, 2048)
FENCE_Y = (1856, 1952)
# Z4 The standing forest at the epicentre: stripped trunks still upright.
FOREST = (1024, 1952, 2752, 4608)
TRUNK = 32
TRUNK_GRID = (1152, 2112, 256)  # first x, first y, spacing
TRUNK_COUNT = (7, 10)
TRUNK_JITTER = 32
BIRCH_EVERY = 7             # of the standing trunks, every seventh (from the fourth) is a birch
CLEARING = (1664, 2944, 2304, 3456)
FOREST_PATHS = ((1792, 1952, 2304, 2304),)  # kept clear behind the blue gate
# Z5 The invaders' works, eating the forest.
WORKS = (2752, 3968, 5440, 5632)
WORKS_EDGE = (2752, 3968, 3200, 5632)
DERRICK_RECT = (4000, 4992, 4256, 5184)
DERRICK_STAIR_X = (4064, 4192)
DERRICK_STAIR_Y = 4768          # 7 steps of 32 north from here up to the platform at 4992
KEY_TOP = (4064, 4992, 4192, 5056)
WORKS_PITS = ((3712, 4480, 4544, 4704), (4736, 4352, 4928, 4672))
TOWERS = ((3328, 4992, 3520, 5184), (4608, 5248, 4800, 5440), (4992, 4096, 5184, 4288))
TOWER_INSET = 32
GLYPH_WIDTH = 64        # one SDGLYP1 plate: a strip up the middle third of each tower face
PIPES = ((3264, 4000, 3520, 4064), (4736, 4864, 5248, 4928), (4608, 4992, 4672, 5184),
         (4864, 5440, 5376, 5504))
RED_GATE_X = (3904, 4032)
CONTAINMENT_Y = (3840, 3968)
CLOSETS = {"closet_z5_w": (3456, 3712), "closet_z5_e": (4224, 4480)}
YELLOW_DOOR_Y = (4672, 4800)
REFINERY_WALL_X = (5440, 5536)
PIPE_RECESSES_X = (3584, 3840, 4096, 4352)  # the north wall's four recesses; the third is S3's
S3_X = (4096, 4224)
WORKS_NORTH = 5632
# Z6 The refinery.
REFINERY = (5536, 3968, 7296, 5376)
CHANNEL = (6272, 3968, 6400, 5376)
BRIDGE = (6272, 4608, 6400, 4864)
VATS = ((5760, 4160, 5952, 4352), (5760, 4992, 5952, 5184), (6656, 4160, 6848, 4352),
        (6656, 4992, 6848, 5184))
TURBINES = ((6976, 4096, 7232, 4224), (6976, 5120, 7232, 5248))
REF_CONSOLE = (6528, 5248, 6784, 5312)
KEY_DAIS = (7104, 4672, 7232, 4800)
FLAGS_RECESS = (5520, 4864, 5536, 4992)     # the two Soviet flags side by side (D119)
# Z7 The crater's rim, Z8 its terraces and floor, Z9 the control bunker.
CRATER = (2944, 1792, 4992, 3840)
RIM = 128
TERRACE = 64
PORTAL_BASE = (3840, 2688, 4096, 2944)
PORTAL_FIELD = (3872, 2720, 4064, 2912)
PYLONS = ((3584, 2432), (4288, 2432), (3584, 3136), (4288, 3136))
PYLON_SIZE = 64         # one glyph plate a face
# The portal's frame: four posts of SDPRTE1 at the field's corners, standing
# proud of it, so the field shows one tile wide between them.
FRAME_POST = 32
FRAME_TOP = PORTAL_TOP + 2 * STEP      # 192: 32 over the field
FRAME_OFFSET = 16       # a 32 face shows the middle of the 64 lump: the cobalt channel
CRATER_PITS = ((3680, 2528, 3808, 2656), (4128, 2528, 4256, 2656), (3680, 2976, 3808, 3104),
               (4128, 2976, 4256, 3104))
EXIT_X = (3904, 4032)
BUNKER = (3840, 1536, 4096, 1728)
EXIT_NICHE = (3936, 1520, 4000, 1536)
# Glyph plates either side of the two gates the invaders guard: the red gate on
# the works' side of the containment, the bunker's gate on the crater's.
GATE_GLYPHS = (("h", CONTAINMENT_Y[1], RED_GATE_X[0] - GLYPH_WIDTH),
               ("h", CONTAINMENT_Y[1], RED_GATE_X[1]),
               ("h", CRATER[1], EXIT_X[0] - GLYPH_WIDTH),
               ("h", CRATER[1], EXIT_X[1]))

# Every picture on the map: (name, texture, axis, coord, lo, hi). All in the
# research station: the laboratory's hall is exactly a poster high.
POSTERS = (
    # The hall: Lenin over the bench where the blue key lies, Stalin on the
    # west wall, the two slots either side.
    ("lab_hall_lenin", LENIN, "h", LAB_HALL[3], 1504, 1632),
    ("lab_hall_stalin", STALIN, "v", LAB_HALL[0], 1360, 1488),
    ("lab_hall_slot_n", MARX, "h", LAB_HALL[3], 1664, 1792),
    ("lab_hall_slot_s", ENGELS, "h", LAB_HALL[1], 1344, 1472),
    # The instrument room (128 high): the cosmonautics mural beside the boards.
    ("lab_instr_mural", MURAL, "v", LAB_INSTR[0], LAB_INSTR[1], LAB_INSTR[3]),
)
POSTER_SLOTS_MARX_ENGELS = ("lab_hall_slot_n", "lab_hall_slot_s")   # Marx, Engels


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS


def log_direction(cx: int, cy: int) -> str:
    """Which way a fallen trunk lies: away from the crater's centre, snapped
    to the nearest of four axes ("ns", "ew", "ne" rising east, "se" falling)."""
    dx, dy = cx - CRATER_CENTRE[0], cy - CRATER_CENTRE[1]
    angle = math.degrees(math.atan2(dy, dx)) % 180
    if angle < 22.5 or angle >= 157.5:
        return "ew"
    if angle < 67.5:
        return "ne"
    if angle < 112.5:
        return "ns"
    return "se"


def log_rects(cx: int, cy: int, length: int) -> list[tuple[int, int, int, int]]:
    """The rectangles of one fallen trunk: one along an axis, or a staircase
    of LOG_BLOCK squares stepping LOG_STAIR on a diagonal."""
    half, w = length // 2, LOG_WIDTH // 2
    way = log_direction(cx, cy)
    if way == "ns":
        return [(cx - w, cy - half, cx + w, cy + half)]
    if way == "ew":
        return [(cx - half, cy - w, cx + half, cy + w)]
    n = int(length / math.sqrt(2)) // LOG_STAIR
    rise = 1 if way == "ne" else -1
    b = LOG_BLOCK // 2
    out = []
    for k in range(n):
        off = (k - (n - 1) / 2) * LOG_STAIR
        x, y = int(cx + off), int(cy + rise * off)
        out.append((x - b, y - b, x + b, y + b))
    return out


def trunk_spots() -> list[tuple[int, int]]:
    """The standing forest's trunks: a grid with a fixed jitter, the clearing
    and the path behind the blue gate left open."""
    x0, y0, step = TRUNK_GRID
    out = []
    for i in range(TRUNK_COUNT[0]):
        for j in range(TRUNK_COUNT[1]):
            jx = ((i * 37 + j * 61) % 5 - 2) * (TRUNK_JITTER // 2)
            jy = ((i * 53 + j * 29) % 5 - 2) * (TRUNK_JITTER // 2)
            x, y = x0 + step * i + jx, y0 + step * j + jy
            if any(a <= x <= c and b <= y <= d for a, b, c, d in (CLEARING,) + FOREST_PATHS):
                continue
            out.append((x, y))
    return out


def birch_trunks() -> list[tuple[int, int]]:
    """The standing trunks that are birch: every BIRCH_EVERY-th, from the fourth."""
    return [spot for n, spot in enumerate(trunk_spots()) if n % BIRCH_EVERY == 3]


def frame_posts() -> tuple[tuple[int, int, int, int], ...]:
    """The portal frame's four posts, in the field's corners."""
    x1, y1, x2, y2 = PORTAL_FIELD
    p = FRAME_POST
    return ((x1, y1, x1 + p, y1 + p), (x2 - p, y1, x2, y1 + p),
            (x1, y2 - p, x1 + p, y2), (x2 - p, y2 - p, x2, y2))


# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100
ED_TROOPER = 21101
ED_STORMTROOPER = 21102
ED_HOUND = 21103
ED_DOUGHBOY = 21104
ED_PANZERMENSCH = 21105
ED_PANZER_HEAVY = 21107
ED_GUNNER = 21110         # the Legion's heavy machine-gunner (D116): long lines, cover
ED_CONSORTIUM = 21112     # episode 3's final boss (D116): 9000 HP, two phases
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
    "heavy": ED_PANZER_HEAVY,
    "gunner": ED_GUNNER,
    "consortium": ED_CONSORTIUM,
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
    ED_CONSORTIUM: "SD_Consortium",
}
REICH = ("rifleman", "hound", "panzermensch", "heavy")
LEGION = ("trooper", "doughboy", "gunner")
# The Consortium is both factions in one body (SD_FACTION_BOTH), like the
# stormtrooper: in neither tuple.
# Where each faction stands (D35): the Reich holds the railhead, the taiga and
# the station's yard (the military occupation); the Legion holds the
# laboratory (capital takes the science) and springs the closets; both hold
# the forest, the works, the refinery and the crater, and both guard the boss.
REICH_GROUND = ("z1_", "z2_", "z3_yard", "z3_izba", "z3_gate")
LEGION_GROUND = ("z3_lab", "closet_")
BOTH_GROUND = ("z4_", "z5_", "z6_", "z7_", "z8_")
# The arsenal (MAPINFO DoomEdNums, 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ED_AKM = 21008            # slot 4's second weapon (D116): the station's armoury, after the PPSh
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_AKM, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # in S2 only: the laboratory's secret prototype
ED_AKM_MAG = 21020        # SD_AkmAmmo: one 30-round 7.62x39 magazine (ADR 011)
ED_CLIP = 2007
ED_CLIP_BOX = 2048
ED_SHELLS = 2008
ED_SHELL_BOX = 2049
ED_ROCKET = 2010
ED_ROCKET_BOX = 2046
ED_CELL = 2047
ED_CELL_PACK = 17
ED_BACKPACK = 8
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019
# V3 A4, the RGD-5 hand grenade (ADR 012; docs/engine/2026-10-23_V3_rgd5.md
# section 6): its own pool, counted 1.25 shell-equivalents a grenade
# (BALANCE 8.1). A grenade is a consumable here, so it rides in ITEMS and
# scales DOWN with skill: 3 / 2 / 2 grenades on skills 2 / 3 / 4, all at the
# research station, none in the crater (the Consortium takes no splash).
ED_RGD5 = 21009           # the pouch: the weapon and two grenades (none here)
ED_RGD5_AMMO = 21021      # one loose grenade (it gives the weapon too)
ED_RGD5_BOX = 21022       # a crate of four: a secret's reward only (none here)
# V3 B5, the propaganda radio (D124; docs/sound/2026-10-23_V3_propaganda-radio.md
# 5.4): SD_Loudspeaker, a positional voice over the music (MOD-SPEC 6.14).
ED_LOUDSPEAKER = 21201
LOUDSPEAKER_FLAG_BED = 4  # SD_LS_FLAG_BED: the valve set's hum and crackle in a loop

# Design section 10: monsters per skill, Doom's skill pairs (udmf.skill_tier).
# The boss's servants are not here: it calls them in the fight (section 11).
# The events, in the order the route meets them (design section 18). The red
# key's closets are v1's (RED_KEY_SPECIAL); V3 gives each a flickering lamp
# on the works' floor before it, like the new ones.
PICKUP_EVENTS = (
    PickupEvent("quarantine", ED_BLUE_CARD, BLUE_KEY_SPOT, SPECIAL_DOOR_OPEN,
                (TAG_QUARANTINE, DOOR_SPEED_SLOW), ("z3_lab_quarantine_door",), ("z3_lab_quarantine",),
                "z3_lab_lamp"),
    PickupEvent("works_lift", ED_YELLOW_CARD, YELLOW_KEY_SPOT, SPECIAL_FLOOR_LOWER_TO_LOWEST,
                (TAG_WORKS_LIFT, LIFT_SPEED), ("z5_lift_car",), ("z5_lift_car",), "z5_lift_gate"),
    PickupEvent("works_closets", ED_RED_CARD, RED_KEY_SPOT, RED_KEY_SPECIAL[0], RED_KEY_SPECIAL[1][:2],
                tuple(f"{n}_door" for n in CLOSETS), tuple(CLOSETS), "z5_closet_w_lamp"),
)

ENEMY_TOTALS = {2: 60, 3: 92, 4: 127}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Facing: 0
# east, 90 north, 180 west, 270 south; most face where the player comes from.
MONSTERS = (
    # The railhead: a Reich picket on the line, facing the train.
    ("z1_yard", "rifleman", 6400, 960, 0, 2),
    ("z1_yard", "rifleman", 6208, 800, 0, 2),
    ("z1_yard", "hound", 6080, 1056, 0, 3),
    ("z1_platform", "rifleman", 6304, 640, 0, 4),
    # The fallen taiga: hounds among the trunks, a few riflemen on the road.
    ("z2_taiga", "hound", 5248, 960, 0, 2),
    ("z2_taiga", "hound", 3584, 960, 0, 2),
    ("z2_taiga", "rifleman", 2752, 960, 0, 2),
    ("z2_taiga", "rifleman", 4416, 960, 0, 2),
    ("z2_taiga", "stormtrooper", 3200, 1024, 0, 3),
    ("z2_taiga", "hound", 4800, 480, 90, 3),
    ("z2_taiga", "rifleman", 2496, 480, 0, 4),
    ("z2_taiga", "stormtrooper", 4032, 1376, 270, 4),
    ("z2_taiga", "hound", 2624, 1376, 0, 4),
    # The station's yard: the Reich's guard, facing the gate.
    ("z3_yard", "rifleman", 1216, 512, 0, 2),
    ("z3_yard", "rifleman", 1728, 832, 0, 2),
    ("z3_yard", "rifleman", 2144, 1344, 270, 2),
    ("z3_yard", "stormtrooper", 1152, 1728, 0, 2),
    ("z3_yard", "rifleman", 2144, 1760, 270, 2),
    ("z3_yard", "rifleman", 1216, 992, 0, 3),
    ("z3_yard", "hound", 1792, 1728, 0, 3),
    ("z3_izba_b", "rifleman", 832, 1248, 0, 3),
    ("z3_yard", "stormtrooper", 2112, 576, 90, 4),
    ("z3_yard", "rifleman", 1152, 1472, 0, 4),
    ("z3_yard", "panzermensch", 1664, 1728, 0, 4),
    # The laboratory: the Legion has taken the science.
    ("z3_lab_hall", "trooper", 1440, 1344, 0, 2),
    ("z3_lab_vest", "trooper", 1920, 1448, 0, 2),
    ("z3_lab_instr", "trooper", 1408, 1184, 0, 2),
    ("z3_lab_instr", "stormtrooper", 1728, 1184, 180, 3),
    ("z3_lab_hall", "doughboy", 1712, 1360, 180, 4),
    # V3 (A2): the quarantine room, open when the blue key is taken: two of
    # the hall's troopers and one of the instrument room's.
    ("z3_lab_quarantine", "trooper", 1840, 1520, 180, 2),
    ("z3_lab_quarantine", "trooper", 1904, 1520, 180, 3),
    ("z3_lab_quarantine", "trooper", 1872, 1560, 180, 4),
    ("z3_lab_vest", "stormtrooper", 1856, 1368, 0, 4),
    # The standing forest: hunters among the trunks, heads floating in the clearing.
    ("z4_forest", "hound", 1792, 2496, 270, 2),
    ("z4_forest", "hound", 2304, 3520, 270, 2),
    ("z4_forest", "doughboy", 1984, 3200, 270, 2),
    ("z4_forest", "trooper", 2560, 3776, 270, 2),
    ("z4_forest", "rifleman", 1536, 4032, 270, 2),
    ("z4_forest", "doughboy", 2304, 4032, 270, 3),
    ("z4_forest", "hound", 1280, 3008, 0, 3),
    ("z4_forest", "stormtrooper", 2560, 2752, 270, 3),
    ("z4_forest", "doughboy", 1536, 3520, 0, 4),
    ("z4_forest", "hound", 2048, 4288, 270, 4),
    ("z4_forest", "stormtrooper", 1280, 2496, 0, 4),
    # The Legion's machine-gunners (D116): three, four, five by skill, each by
    # cover with a long line down the ground the player has to cross.
    # At the clearing's east edge, a trunk at his shoulder: the clearing and
    # the forest's depth back to the blue gate down his sights.
    ("z4_forest", "gunner", 2400, 3104, 90, 3),
    # The works: the invaders' industry, both factions, facing the forest.
    ("z5_works", "rifleman", 3392, 4352, 180, 2),
    ("z5_works", "rifleman", 3648, 4928, 180, 2),
    ("z5_works", "trooper", 3968, 4224, 180, 2),
    ("z5_works", "trooper", 4416, 4864, 180, 2),
    ("z5_works", "stormtrooper", 3584, 5312, 180, 2),
    ("z5_works", "stormtrooper", 4608, 4096, 180, 2),
    ("z5_works", "hound", 3776, 4096, 180, 2),
    ("z5_works", "hound", 4352, 5376, 180, 2),
    ("z5_works", "panzermensch", 5088, 4608, 180, 2),
    ("z5_works", "doughboy", 4160, 4352, 180, 2),
    ("z5_derrick", "trooper", 4224, 5152, 270, 2),
    ("z5_works", "rifleman", 5248, 4416, 180, 2),
    ("z5_works", "trooper", 5248, 5120, 180, 2),
    ("z5_edge", "trooper", 3008, 5248, 270, 2),
    ("z5_works", "rifleman", 3456, 4608, 180, 3),
    ("z5_works", "trooper", 3840, 5504, 180, 3),
    ("z5_works", "stormtrooper", 4992, 4800, 180, 3),
    ("z5_works", "hound", 4544, 4224, 180, 3),
    ("z5_works", "doughboy", 3328, 5440, 180, 3),
    ("z5_derrick", "trooper", 4032, 5152, 270, 3),
    ("z5_works", "rifleman", 5312, 5376, 180, 3),
    ("z5_works", "heavy", 5056, 5056, 180, 4),
    ("z5_works", "panzermensch", 3712, 4224, 180, 4),
    ("z5_works", "stormtrooper", 4224, 4096, 180, 4),
    ("z5_works", "rifleman", 3584, 5056, 180, 4),
    # V3 (A3): the works' cargo lift, down with the yellow key: three of the
    # works' north side.
    ("z5_lift_car", "rifleman", 5024, 5712, 270, 2),
    ("z5_lift_car", "stormtrooper", 5088, 5712, 270, 3),
    ("z5_lift_car", "trooper", 5056, 5760, 270, 4),
    ("z5_works", "hound", 5248, 4224, 180, 4),
    ("z5_works", "doughboy", 4736, 5056, 180, 4),
    ("z5_works", "rifleman", 5312, 4992, 180, 4),
    ("z5_works", "stormtrooper", 3392, 4800, 180, 4),
    # South of the east conduit: the works' whole width west to the forest's edge.
    ("z5_works", "gunner", 5184, 4800, 180, 2),
    # The works' closets (TAG_AMBUSH, the red key's pickup): the Legion's
    # counter-attack behind the player as he comes back for the red gate.
    ("closet_z5_w", "trooper", 3520, 3904, 90, 2),
    ("closet_z5_w", "trooper", 3648, 3904, 90, 3),
    ("closet_z5_w", "stormtrooper", 3584, 3904, 90, 4),
    ("closet_z5_e", "trooper", 4288, 3904, 90, 2),
    ("closet_z5_e", "stormtrooper", 4416, 3904, 90, 3),
    ("closet_z5_e", "stormtrooper", 4352, 3904, 90, 4),
    # The refinery: its heavies on the floor, both factions, facing the door.
    ("z6_refinery", "rifleman", 5760, 4864, 180, 2),
    ("z6_refinery", "trooper", 6080, 4480, 180, 2),
    ("z6_refinery", "trooper", 6080, 5056, 180, 2),
    ("z6_refinery", "stormtrooper", 6528, 4480, 180, 2),
    ("z6_refinery", "stormtrooper", 6528, 5056, 180, 2),
    ("z6_refinery", "panzermensch", 6656, 4608, 180, 2),
    ("z6_refinery", "hound", 5952, 4096, 180, 2),
    ("z6_refinery", "doughboy", 6912, 4864, 180, 2),
    ("z6_refinery", "rifleman", 7104, 4416, 180, 2),
    ("z6_refinery", "trooper", 7104, 5056, 180, 2),
    ("z6_refinery", "stormtrooper", 7104, 4288, 180, 2),
    ("z6_refinery", "rifleman", 5760, 5312, 180, 3),
    ("z6_refinery", "stormtrooper", 6080, 4160, 180, 3),
    ("z6_refinery", "heavy", 6912, 4416, 180, 3),
    ("z6_refinery", "hound", 6464, 5312, 180, 3),
    ("z6_refinery", "trooper", 7168, 4992, 180, 3),
    ("z6_refinery", "doughboy", 6080, 4608, 180, 3),
    ("z6_refinery", "heavy", 6912, 5056, 180, 4),
    ("z6_refinery", "stormtrooper", 5760, 4032, 180, 4),
    ("z6_refinery", "rifleman", 6528, 4032, 180, 4),
    ("z6_refinery", "panzermensch", 7168, 4352, 180, 4),
    ("z6_refinery", "trooper", 6528, 4864, 180, 4),
    ("z6_refinery", "hound", 7104, 5312, 180, 4),
    # Past the channel in a vat's lee, the bridge and the yellow door down his sights.
    ("z6_refinery", "gunner", 6720, 4416, 180, 2),
    # The crater: the boss before the portal, both factions on the terraces.
    ("z8_floor", BOSS_KIND, MAP09_BOSS_SPOT[0], MAP09_BOSS_SPOT[1], BOSS_ANGLE, 2),
    ("z8_floor", "stormtrooper", 3584, 2880, 90, 2),
    ("z8_floor", "stormtrooper", 4352, 2880, 90, 2),
    ("z8_floor", "doughboy", 3968, 2496, 90, 2),
    ("z8_tier_4", "trooper", 3968, 3488, 90, 2),
    ("z8_tier_3", "rifleman", 3296, 3520, 0, 2),
    ("z8_tier_3", "rifleman", 4640, 3520, 180, 2),
    ("z8_tier_3", "hound", 3232, 2816, 90, 2),
    ("z8_tier_3", "panzermensch", 4704, 2816, 90, 2),
    ("z8_floor", "trooper", 3712, 3200, 90, 3),
    ("z8_floor", "trooper", 4224, 3200, 90, 3),
    ("z8_tier_4", "hound", 4576, 2112, 90, 3),
    ("z8_tier_6", "heavy", 3392, 2240, 90, 3),
    ("z8_floor", "doughboy", 3584, 2432 + 96, 90, 4),
    ("z8_tier_5", "stormtrooper", 4512, 3392, 180, 4),
    ("z8_tier_5", "stormtrooper", 3424, 3392, 0, 4),
    ("z8_tier_1", "heavy", 3104, 2048, 90, 4),
    # Across the crater from the red gate, firing up the terraces at whoever
    # comes down them: the boss's covering fire.
    ("z8_tier_2", "gunner", 4480, 2016, 90, 2),
    ("z8_tier_6", "gunner", 3712, 2272, 90, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on - 4 every skill, 3 medium and easier, 2 easy only).
ITEMS = (
    # The weapons, on every skill, each before the fight it is for.
    ("z1_halt", ED_IZH, 7040, 864, 4),
    ("z3_izba_a", ED_PPSH, 832, 736, 4),
    ("z3_izba_a", ED_AKM, 736, 640, 4),     # the station's rifle, beside the PPSh (D116)
    ("z4_forest", ED_RPG7, 2560, 4288, 4),
    ("z5_edge", ED_ROKS3, 3008, 4800, 4),
    # Stimpacks: 9 on every skill, +4 medium, +3 easy.
    ("z1_halt", ED_STIMPACK, 7168, 800, 4),
    ("z3_izba_c", ED_STIMPACK, 736, 1728, 4),
    ("z4_forest", ED_STIMPACK, 1280, 4288, 4),
    ("z5_edge", ED_STIMPACK, 2816, 5568, 4),
    ("z6_refinery", ED_STIMPACK, 5632, 5056, 4),
    ("z7_rim", ED_STIMPACK, 3008, 3584, 4),
    ("z7_rim", ED_STIMPACK, 4928, 3584, 4),
    ("z2_taiga", ED_STIMPACK, 2368, 1344, 3),
    ("z5_works", ED_STIMPACK, 5376, 5568, 3),
    ("z7_rim", ED_STIMPACK, 3968, 1856, 3),
    ("z3_lab_vest", ED_STIMPACK, 1856, 1440, 2),
    ("z6_refinery", ED_STIMPACK, 7232, 4160, 2),
    ("z8_tier_1", ED_STIMPACK, 3712, 1952, 4),      # the arena's
    ("z8_tier_1", ED_STIMPACK, 4224, 1952, 4),
    ("z8_tier_1", ED_STIMPACK, 3200, 3680, 3),
    ("z8_tier_1", ED_STIMPACK, 4736, 3680, 2),
    # Medikits: 9 on every skill, +3 medium.
    ("z3_izba_b", ED_MEDIKIT, 928, 1152, 4),
    ("z4_forest", ED_MEDIKIT, 2176, 3328, 4),
    ("z5_works", ED_MEDIKIT, 5376, 4096, 4),
    ("z6_refinery", ED_MEDIKIT, 7232, 5312, 4),
    ("z6_refinery", ED_MEDIKIT, 7232, 4032, 4),
    ("z7_rim", ED_MEDIKIT, 3008, 2880, 4),
    ("z7_rim", ED_MEDIKIT, 4928, 2880, 4),
    ("z5_edge", ED_MEDIKIT, 2816, 3968 + 64, 3),
    ("z7_rim", ED_MEDIKIT, 4160, 1856, 3),
    ("z8_tier_1", ED_MEDIKIT, 3104, 3584, 4),       # the arena's
    ("z8_tier_1", ED_MEDIKIT, 4832, 3584, 4),
    ("z8_tier_1", ED_MEDIKIT, 4224, 3680, 3),
    # Armour: the flak vest in the station's store izba, the heavy vest at
    # the red gate before the crater; plates at the three locks.
    ("z3_izba_c", ED_GREEN_ARMOR, 928, 1664, 4),
    ("z7_red_porch", ED_BLUE_ARMOR, 3968, 3872, 4),
    ("z3_blue_portal", ED_ARMOR_BONUS, 1952, 1872, 4),
    ("z3_blue_portal", ED_ARMOR_BONUS, 2016, 1872, 4),
    ("z5_yellow_portal", ED_ARMOR_BONUS, 5456, 4704, 4),
    ("z5_yellow_portal", ED_ARMOR_BONUS, 5456, 4768, 4),
    ("z5_red_portal", ED_ARMOR_BONUS, 3936, 3952, 4),
    ("z5_red_portal", ED_ARMOR_BONUS, 4000, 3952, 4),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z1_halt_door", ED_HEALTH_BONUS, 7040, 720, 4),
    ("z3_gate", ED_HEALTH_BONUS, 2272, 928, 4),
    ("z3_izba_a_door", ED_HEALTH_BONUS, 1008, 736, 4),
    ("z3_lab_instr_door", ED_HEALTH_BONUS, 1600, 1264, 4),
    ("z4_blue_porch", ED_HEALTH_BONUS, 1984, 1936, 4),
    ("z6_flags", ED_HEALTH_BONUS, 5528, 4928, 4),
    ("z9_exit_porch", ED_HEALTH_BONUS, 3968, 1776, 4),
    # The RGD-5 (V3 A4): loose grenades in two of the izbas, one more in
    # the yard on easy.
    ("z3_izba_a", ED_RGD5_AMMO, 750, 700, 4),
    ("z3_izba_b", ED_RGD5_AMMO, 750, 1300, 4),
    ("z3_yard", ED_RGD5_AMMO, 1160, 1000, 2),
)

# The station's radio (V3 B5): (zone, x, y, lines, reach, flags, jingle), as
# MAP04's. The last Soviet outpost before the alien works: one speaker at
# the foot of the yard's mast, two lines only (the lore's line and the
# Motherland), and the valve set's bed under them: a far, noisy station.
LOUDSPEAKERS = (
    ("z3_yard", 1632, 736, (7, 5), 0, LOUDSPEAKER_FLAG_BED, 0),
)

# D119 (the CEO's playtest: "siempre sale de sobras", "siempre acabas con la
# escopeta"): the route's ammunition, kept apart from ITEMS because it no
# longer scales DOWN with skill. It scales with the monsters it pays for,
# like them: (zone, editor number, x, y, LOWEST skill tier it appears on -
# 2 = every skill, 3 = medium and harder, 4 = hard only). So each skill's
# stock sits in its own G3-8 band (docs/engine/BALANCE.md, D119: 1.5-2.0 /
# 1.3-1.6 / 1.2-1.45 on skills 2 / 3 / 4), shells are at most ~35 % of the
# damage, and the rest follows the weapons the player holds at each stage,
# the newest first; fuel sparingly (the ROKS-3 is being toned down).
AMMO = (
    # The railhead, the taiga and the station (the IZh, then the PPSh and
    # the AKM in the first izba).
    ("z1_halt", ED_SHELLS, 6912, 800, 2),
    ("z2_taiga", ED_SHELLS, 4224, 960, 2),
    ("z3_yard", ED_AKM_MAG, 2176, 960, 2),
    ("z3_yard", ED_AKM_MAG, 2176, 1504, 2),
    ("z3_izba_a", ED_CLIP_BOX, 928, 800, 2),
    ("z3_lab_hall", ED_AKM_MAG, 1376, 1376, 2),
    ("z2_taiga", ED_SHELL_BOX, 5632, 960, 3),
    ("z3_lab_vest", ED_AKM_MAG, 2016, 1376, 3),
    ("z3_lab_hall", ED_CLIP_BOX, 1376, 1312, 3),
    ("z1_yard", ED_SHELL_BOX, 6656, 1056, 4),
    # The standing forest and the works (the RPG-7, then the ROKS-3).
    ("z4_forest", ED_ROCKET_BOX, 2496, 4352, 2),
    ("z4_forest", ED_AKM_MAG, 2112, 3456, 2),
    ("z4_forest", ED_SHELL_BOX, 1792, 3008, 2),
    ("z4_forest", ED_CLIP_BOX, 2048, 2304, 2),
    ("z5_edge", ED_CELL, 3072, 4800, 2),
    ("z5_edge", ED_SHELLS, 2880, 4160, 2),
    ("z5_edge", ED_AKM_MAG, 3072, 4416, 2),
    ("z5_edge", ED_AKM_MAG, 2880, 4672, 2),
    ("z5_works", ED_AKM_MAG, 5312, 4608, 2),
    ("z5_works", ED_AKM_MAG, 5376, 4864, 2),
    ("z5_works", ED_AKM_MAG, 5376, 4736, 2),
    ("z5_works", ED_SHELLS, 3840, 4864, 2),
    ("z5_works", ED_AKM_MAG, 4416, 5568, 2),
    ("z4_forest", ED_AKM_MAG, 2560, 2240, 3),
    ("z5_edge", ED_ROCKET_BOX, 2880, 5376, 3),
    ("z5_works", ED_AKM_MAG, 4416, 4096, 3),
    ("z5_edge", ED_AKM_MAG, 2944, 5440, 3),
    ("z4_forest", ED_ROCKET_BOX, 2560, 4032, 4),
    ("z4_forest", ED_AKM_MAG, 2048, 3712, 4),
    ("z5_works", ED_AKM_MAG, 4416, 5056, 4),
    ("z5_works", ED_AKM_MAG, 4992, 5568, 4),
    ("z5_works", ED_SHELL_BOX, 4992, 4416, 4),
    ("z5_works", ED_AKM_MAG, 5312, 5248, 4),
    ("z5_edge", ED_CLIP_BOX, 3136, 5056, 4),
    ("z5_edge", ED_AKM_MAG, 2944, 4288, 4),
    ("z5_edge", ED_CLIP_BOX, 3008, 5248, 4),
    ("z5_works", ED_CLIP_BOX, 5376, 5056, 4),
    # The refinery.
    ("z6_yellow_porch", ED_AKM_MAG, 5520, 4736, 2),
    ("z6_refinery", ED_ROCKET_BOX, 5632, 4736, 2),
    ("z6_refinery", ED_AKM_MAG, 5632, 4608, 2),
    ("z6_refinery", ED_SHELL_BOX, 5632, 4096, 2),
    ("z6_refinery", ED_CLIP_BOX, 7232, 4864, 2),
    ("z6_refinery", ED_AKM_MAG, 6176, 4736, 2),
    ("z6_refinery", ED_CELL, 5632, 4480, 2),
    ("z6_refinery", ED_AKM_MAG, 5632, 5312, 2),
    ("z6_refinery", ED_ROCKET_BOX, 7232, 4992, 3),
    ("z6_refinery", ED_AKM_MAG, 7232, 4608, 3),
    ("z6_refinery", ED_AKM_MAG, 6176, 4480, 3),
    ("z6_refinery", ED_CLIP_BOX, 5632, 4992, 3),
    ("z6_refinery", ED_AKM_MAG, 6176, 5056, 4),
    ("z6_refinery", ED_ROCKET_BOX, 6176, 5248, 4),
    ("z6_refinery", ED_AKM_MAG, 6176, 4608, 4),
    ("z6_refinery", ED_CLIP_BOX, 6176, 4224, 4),
    ("z6_refinery", ED_AKM_MAG, 6560, 4608, 4),
    ("z6_refinery", ED_CLIP_BOX, 6560, 4736, 4),
    # The crater: the Consortium's arena (4000 HP since D119, and its
    # servants). The rim and the red gate's porch, then the first terrace,
    # the ring the player circles on: PG-7V first (it takes no blast, so
    # impacts only), magazines, shells, a little fuel.
    ("z7_red_porch", ED_CLIP_BOX, 3936, 3872, 2),
    ("z7_red_porch", ED_CELL, 4000, 3872, 2),
    ("z7_rim", ED_ROCKET_BOX, 3968, 3712, 2),
    ("z7_rim", ED_ROCKET_BOX, 3008, 2816, 2),
    ("z7_rim", ED_ROCKET_BOX, 4928, 2816, 2),
    ("z7_rim", ED_SHELL_BOX, 3008, 3776, 2),
    ("z7_rim", ED_SHELL_BOX, 4928, 3776, 2),
    ("z7_rim", ED_ROCKET_BOX, 4928, 3200, 2),
    ("z7_rim", ED_CLIP_BOX, 3968, 3776, 2),
    ("z7_rim", ED_CELL, 3328, 3776, 2),
    ("z8_tier_1", ED_ROCKET_BOX, 3104, 2560, 2),
    ("z8_tier_1", ED_ROCKET_BOX, 4832, 2560, 2),
    ("z8_tier_1", ED_ROCKET, 3456, 1952, 2),
    ("z8_tier_1", ED_ROCKET, 4480, 1952, 2),
    ("z8_tier_1", ED_AKM_MAG, 3104, 2816, 2),
    ("z8_tier_1", ED_AKM_MAG, 4832, 2816, 2),
    ("z8_tier_1", ED_AKM_MAG, 3968, 3680, 2),
    ("z8_tier_1", ED_ROCKET_BOX, 3104, 3328, 2),
    ("z8_tier_1", ED_CELL, 3968, 1952, 2),
    ("z8_tier_1", ED_CLIP_BOX, 3712, 3680, 2),
    ("z8_tier_1", ED_AKM_MAG, 4832, 3328, 2),
    ("z7_rim", ED_ROCKET_BOX, 3008, 1856, 4),
    ("z8_tier_1", ED_ROCKET_BOX, 4832, 3072, 4),
)

# Kept out of ITEMS on purpose: ITEMS is the route's. Every secret's reward is
# on every skill (MAP01's rule).
SECRET_ITEMS = (
    # S1: the halt's locker - a backpack, a vest, shells.
    ("s1_store", ED_BACKPACK, 7392, 896, 4),
    ("s1_store", ED_GREEN_ARMOR, 7392, 832, 4),
    ("s1_store", ED_SHELL_BOX, 7424, 960, 4),
    # S2: behind the instrument board, the laboratory's prototype: the Hand
    # Katyusha (Soviet science fiction) and a pack for it.
    ("s2_store", ED_HAND_KATYUSHA, 1568, 992, 4),
    ("s2_store", ED_CELL_PACK, 1504, 960, 4),
    # S3: behind the works' pipe recess - medikits and PG-7V.
    ("s3_store", ED_MEDIKIT, 4064, 5824, 4),
    ("s3_store", ED_MEDIKIT, 4256, 5824, 4),
    ("s3_store", ED_ROCKET_BOX, 4160, 5776, 4),
)


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = BALLAST, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0), on both faces
    (MAP02's and MAP03's helper, repeated so each map stays one file)."""
    return LineStyle(special=SPECIAL_DOOR_LOCKED_RAISE, args=(tag, DOOR_SPEED_SLOW, 0, lock, 0),
                     flags=("playeruse", "repeatspecial"), back_sector=door_sector,
                     texture=texture, peg_bottom=False)


def secret_panel_style(tag: int, panel: int, texture: str) -> LineStyle:
    """A push panel that opens for good, drawn one-sided on the automap."""
    style = door_open_style(tag, panel, texture=texture)
    return replace(style, flags=style.flags + ("secret",))


# --- Alignment (MAP05's method, repeated so each map stays one file) ----------
# Every lump below is 128 high. ROW_BASES: the height each lump's foot sits on,
# with every 128 above and below it, whatever floor or ceiling a face hangs
# from, so the logs' joints meet every floor, the glyph plates and the alien
# membrane run on through the terraces, the cab's pictures stand whole on its
# floor. COLUMN_WIDTHS: the lumps whose columns fall where they would on a
# wall from the map's origin, so a wall split by its neighbours' corners shows
# no seam (and a glyph plate on a 64 line starts on its edge).
LUMP_HEIGHT = 128
ROW_BASES = {LOG_WALL: GROUND, ALIEN: GROUND, GLYPH: GROUND, BARK: GROUND, BIRCH: GROUND,
             ARMOUR: GROUND, PORTAL_RIM: PORTAL_PLINTH, CAB_FRONT: HUT_FLOOR, CAB_SIDE: HUT_FLOOR}
COLUMN_WIDTHS = {LOG_WALL: 128, ALIEN: 128, GLYPH: 64, BARK: 64, BIRCH: 64, ARMOUR: 64}


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


def world_column(tm: TextMap, ld, side: int) -> int:
    """The offset that starts this side's texture where the map's grid would
    have it. Doom runs a front side's texture from v1 to v2 and a back side's
    from v2 to v1; every line here is axis-aligned."""
    a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
    if side == ld.sideback:
        a, b = b, a
    if a.y == b.y:
        return int(a.x) if b.x > a.x else -int(a.x)
    return int(a.y) if b.y > a.y else -int(a.y)


def align_to_world(tm: TextMap) -> None:
    """Peg every drawn face of the lumps in ROW_BASES to the world's rows, and
    those in COLUMN_WIDTHS to its columns (a sidedef's `offsety`, positive
    raises the texture; `offsetx` along the line)."""
    for ld in tm.linedefs:
        for side, other in ((ld.sidefront, ld.sideback), (ld.sideback, ld.sidefront)):
            if side is None:
                continue
            sd = tm.sidedefs[side]
            for key, ref in drawn_parts(tm, ld, side, other):
                texture = getattr(sd, key)
                if texture in ROW_BASES:
                    sd.offsety = (ROW_BASES[texture] - ref) % LUMP_HEIGHT
                    if texture in COLUMN_WIDTHS:
                        sd.offsetx = world_column(tm, ld, side) % COLUMN_WIDTHS[texture]
                    break


def align_run(tm: TextMap, vertical: bool, coord: int, lo: int, hi: int, *, width: int,
              base: int = 0) -> None:
    """MAP04's: one texture continuous along the segment [lo, hi] of a grid
    line, however the painter split it: on every sidedef there the x offset
    is `base` plus the distance from the segment's end on the viewer's left
    (each side sees its own left), modulo `width`."""
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
        for side, start, end in ((ld.sidefront, p, q), (ld.sideback, q, p)):
            if side is None:
                continue
            tm.sidedefs[side].offsetx = int(base + (start - lo if end > start else hi - start)) % width


def _outline(g: GridMap, rect, texture: str) -> None:
    """Style the four sides of a rectangle with one texture."""
    x1, y1, x2, y2 = rect
    style = LineStyle(texture=texture)
    g.style_h(y1, x1, x2, style)
    g.style_h(y2, x1, x2, style)
    g.style_v(x1, y1, y2, style)
    g.style_v(x2, y1, y2, style)


def pickup_special(ednum: int, spot: tuple[int, int]) -> dict:
    """The UDMF `special` and `arg0..` of the thing `ednum` at `spot`, if
    an event of PICKUP_EVENTS rides it (the red key's form); else nothing."""
    for event in PICKUP_EVENTS:
        if (event.trigger, tuple(event.spot)) == (ednum, tuple(spot)):
            return {"special": event.special, **{f"arg{i}": a for i, a in enumerate(event.args)}}
    return {}


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=BARK)
    plan: dict[str, int] = {}

    def zone(name: str, floor: int, ceil: int, rects, tag: int | None = None, *,
             light: int, flat: str = BALLAST, ceiling: str = CEIL_CONCRETE,
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
        """A closed door sector; its own walls are the jambs, its floor a
        threshold of plate."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=wall, flat=PLATE)

    def block(name: str, top: int, rects, *, wall: str, light: int, flat: str = CRATE_TOP) -> int:
        """A closed open-air block (floor = ceiling, sky): a roof, seen as a
        wall `top` high with the sky above it."""
        return zone(name, top, top, rects, light=light, flat=flat, ceiling=SKY, wall=wall)

    def prop(room: str, name: str, rects, top: int, *, wall: str, flat: str | None = None,
             light: int | None = None) -> int:
        """Something standing in `room` that nobody walks on: a trunk, a
        wagon, a tower. Its top is `top`, its sky the room's."""
        return like(room, f"{PROP_PREFIX}{name}", rects, floor=top, wall=wall, light=light,
                    **({"flat": flat} if flat else {}))

    def pit(room: str, name: str, rect, flat: str) -> int:
        """A pit of molten metal or acid one step deep: it hurts, and it is
        walked out of."""
        extra = {**tm.sectors[plan[room]].extra, **LAVA_HURTS}
        return like(room, name, [rect], floor=tm.sectors[plan[room]].heightfloor - STEP,
                    light=LIGHT_LAVA, flat=flat, wall=STEEL, extra=extra)

    def hut(room: str, name: str, roof, door_rect) -> None:
        """A wooden hut: a roof block, its room one step up inside, and a
        doorway whose sky sits on the roof's line (no slab above it)."""
        x1, y1, x2, y2 = roof
        block(f"{PROP_PREFIX}{name}_roof", ROOF, [roof], wall=LOG_WALL,
              light=tm.sectors[plan[room]].lightlevel)
        zone(name, HUT_FLOOR, HUT_CEIL, [(x1 + IZBA_WALL, y1 + IZBA_WALL, x2 - IZBA_WALL, y2 - IZBA_WALL)],
             light=LIGHT_IZBA, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=LOG_WALL)
        zone(f"{name}_door", HUT_FLOOR, ROOF, [door_rect], light=LIGHT_IZBA, flat=CRATE_TOP,
             ceiling=SKY, wall=LOG_WALL)

    # The posters first: GridMap keeps the first style registered on a
    # segment, so nothing broader can paint over them.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    # Then the odd birch in the treeline and the glyph plates by the gates,
    # before the broader runs they stand in.
    for axis, coord, lo in TREELINE_BIRCHES:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, lo + BIRCH_WIDTH, LineStyle(texture=BIRCH))
    for axis, coord, lo in GATE_GLYPHS:
        (g.style_h if axis == "h" else g.style_v)(coord, lo, lo + GLYPH_WIDTH, LineStyle(texture=GLYPH))

    # ======================================================================
    # Z1 The railhead (start)
    # ======================================================================
    zone("z1_ballast", GROUND, RAIL_SKY, [RAIL_BALLAST], light=LIGHT_RAIL, flat=BALLAST,
         ceiling=SKY, wall=BARK)
    zone("z1_yard", GROUND, RAIL_SKY, [RAIL_YARD], light=LIGHT_RAIL, flat=MOSS,
         ceiling=SKY, wall=BARK)
    like("z1_ballast", "z1_track", [RAIL_TRACK], flat=TRACK, extra={"rotationfloor": 90.0})
    zone("z1_platform", PLATFORM, RAIL_SKY, [RAIL_PLATFORM], light=LIGHT_RAIL, flat=CRATE_TOP,
         ceiling=SKY, wall=WAGON)
    # The platform's two walls onto the void: the halt's store behind it (logs)
    # and the treeline at its east end.
    px1, py1, px2, py2 = RAIL_PLATFORM
    g.style_h(py2, HALT_ROOF[2], px2, LineStyle(texture=LOG_WALL))
    g.style_v(px2, py1, py2, LineStyle(texture=BARK))
    prop("z1_ballast", "z1_buffer", [BUFFER], BUFFER_TOP, wall=STEEL, flat=PLATE)
    for name, rect, wall in TRAIN:
        prop("z1_ballast", f"z1_{name}", [rect], WAGON_TOP, wall=wall, flat=PLATE)
    # The armoured wagon's long flanks: one whole red star per 128.
    _, (ax1, ay1, ax2, ay2), _ = TRAIN[1]
    for y in (ay1, ay2):
        g.style_h(y, ax1, ax2, LineStyle(texture=ARMOUR_STAR))
    # The locomotive's cab: a shell of armour plate, the room inside one step up
    # under a roof of plate, its doorway's sky on the shell's line (the huts'
    # way: no slab over it), and the cab's own pictures on its four walls.
    block(f"{PROP_PREFIX}z1_cab_shell", ROOF, [CAB_SHELL], wall=ARMOUR, light=LIGHT_RAIL, flat=PLATE)
    zone("z1_cab", HUT_FLOOR, HUT_CEIL, [CAB], light=LIGHT_HALT, flat=PLATE, ceiling=PLATE,
         wall=CAB_SIDE)
    zone("z1_cab_door", HUT_FLOOR, ROOF, [CAB_DOOR], light=LIGHT_HALT, flat=PLATE, ceiling=SKY,
         wall=ARMOUR)
    kx1, ky1, kx2, ky2 = CAB
    g.style_v(kx1, ky1, ky2, LineStyle(texture=CAB_FRONT))
    g.style_v(kx2, ky1, ky2, LineStyle(texture=CAB_SIDE))
    g.style_h(ky1, kx1, kx2, LineStyle(texture=CAB_SIDE))
    g.style_h(ky2, kx1, CAB_DOOR[0], LineStyle(texture=CAB_SIDE))
    sx1, sy1, sx2, sy2 = SIGNAL_POST
    prop("z1_yard", "z1_signal", [SIGNAL_POST], SIGNAL_TOP, wall=STEEL, flat=PLATE)
    g.style_v(sx2, sy1, sy2, LineStyle(texture=SIGNAL))
    # The halt: a wooden hut on the platform, the IZh on its bench.
    block(f"{PROP_PREFIX}z1_halt_roof", ROOF, [HALT_ROOF], wall=LOG_WALL, light=LIGHT_RAIL)
    zone("z1_halt", HUT_FLOOR, HUT_CEIL, [HALT], light=LIGHT_HALT, flat=CRATE_TOP,
         ceiling=CRATE_TOP, wall=LOG_WALL)
    zone("z1_halt_door", HUT_FLOOR, ROOF, [HALT_DOOR], light=LIGHT_HALT, flat=CRATE_TOP,
         ceiling=SKY, wall=LOG_WALL)
    # S1: of the three lockers on the halt's east wall the middle one stands
    # back in shadow; it is a panel onto the stationmaster's store.
    lx = LOCKERS_X
    for y1, y2 in zip(LOCKERS_Y, LOCKERS_Y[1:]):
        if (y1, y2) != S1_Y:
            g.style_v(lx, y1, y2, LineStyle(texture=LOCKER))
    zone("s1_niche", HUT_FLOOR, HUT_CEIL, [(lx, S1_Y[0], lx + NICHE_DEPTH, S1_Y[1])],
         light=LIGHT_CLUE, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=LOG_WALL)
    s1_panel = zone("s1_panel", HUT_FLOOR, HUT_FLOOR,
                    [(lx + NICHE_DEPTH, S1_Y[0], lx + 2 * NICHE_DEPTH, S1_Y[1])], TAG_S1_PANEL,
                    light=LIGHT_CLUE, flat=CRATE_TOP, wall=LOG_WALL)
    zone("s1_passage", HUT_FLOOR, HUT_CEIL, [(lx + 2 * NICHE_DEPTH, S1_Y[0], HALT_ROOF[2], S1_Y[1])],
         light=LIGHT_SECRET, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=LOG_WALL)
    zone("s1_store", HUT_FLOOR, HUT_CEIL, [(HALT_ROOF[2], 768, 7488, 1024)], light=LIGHT_SECRET,
         flat=CRATE_TOP, ceiling=CRATE_TOP, wall=LOG_WALL, special=SECTOR_SPECIAL_SECRET)
    for x in (lx + NICHE_DEPTH, lx + 2 * NICHE_DEPTH):
        g.style_v(x, S1_Y[0], S1_Y[1], secret_panel_style(TAG_S1_PANEL, s1_panel, LOCKER))

    # ======================================================================
    # Z2 The fallen taiga
    # ======================================================================
    zone("z2_taiga", GROUND, TAIGA_SKY, [TAIGA], light=LIGHT_TAIGA, flat=BURNT,
         ceiling=SKY, wall=BARK, extra={"rotationfloor": BURNT_TURN})
    for n, (cx, cy, length) in enumerate(LOGS, start=1):
        birch = n in BIRCH_LOGS
        prop("z2_taiga", f"z2_log_{n}", log_rects(cx, cy, length), LOG,
             wall=BIRCH if birch else BARK, flat=MOSS if birch else BURNT)
    # The taiga's west wall is the station's palisade, seen from outside.
    g.style_v(TAIGA[0], TAIGA[1], TAIGA[3], LineStyle(texture=LOG_WALL))

    # ======================================================================
    # Z3 The research station
    # ======================================================================
    zone("z3_yard", GROUND, STATION_SKY, [STATION_YARD], light=LIGHT_STATION, flat=MOSS,
         ceiling=SKY, wall=LOG_WALL)
    zone("z3_gate", GROUND, STATION_SKY, [STATION_GATE], light=LIGHT_STATION, flat=MOSS,
         ceiling=SKY, wall=LOG_WALL)
    prop("z3_yard", "z3_mast", [MAST], MAST_TOP, wall=STEEL, flat=PLATE)
    for key, (x1, y1, x2, y2) in IZBAS.items():
        cy = (y1 + y2) // 2
        hut("z3_yard", f"z3_izba_{key}", (x1, y1, x2, y2),
            (x2 - IZBA_WALL, cy - IZBA_DOOR // 2, x2, cy + IZBA_DOOR // 2))
    prop("z3_izba_b", "z3_izba_b_crates", [(672, 1344, 736, 1376)], 64, wall=CRATE, flat=CRATE_TOP)
    # The laboratory: concrete, a hall a poster high, an instrument room, a vestibule.
    g.carve(*LAB)
    _outline(g, LAB, CONCRETE)
    zone("z3_lab_hall", HUT_FLOOR, LAB_CEIL, [LAB_HALL], light=LIGHT_LAB, flat=LAB_FLOOR,
         ceiling=CEIL_LAMP, wall=TILE)
    zone("z3_lab_vest", HUT_FLOOR, HUT_CEIL, [LAB_VEST], light=LIGHT_LAB, flat=LAB_FLOOR,
         ceiling=CEIL_LAMP, wall=CONCRETE)
    zone("z3_lab_instr", HUT_FLOOR, HUT_CEIL, [LAB_INSTR], light=LIGHT_INSTR, flat=LAB_FLOOR,
         ceiling=CEIL_LAMP, wall=TILE_DADO)
    zone("z3_lab_instr_door", HUT_FLOOR, HUT_CEIL, [LAB_INSTR_DOOR], light=LIGHT_INSTR,
         flat=LAB_FLOOR, ceiling=CEIL_LAMP, wall=TILE_DADO)
    zone("z3_key_bench", BENCH_TOP, LAB_CEIL, [KEY_BENCH], light=LIGHT_BEACON, flat=LAB_FLOOR,
         ceiling=CEIL_LAMP, wall=STEEL, extra=BLUE_LIGHT)
    # V3 (A2): the quarantine room, its door the hall's tile, its lamp before it.
    like("z3_lab_hall", "z3_lab_lamp", [QUARANTINE_LAMP], light=LIGHT_EVENT_LAMP,
         special=SECTOR_SPECIAL_LIGHT_FLICKER)
    zone("z3_lab_quarantine_door", HUT_FLOOR, HUT_FLOOR, [QUARANTINE_DOOR], TAG_QUARANTINE,
         light=LIGHT_CLOSET, flat=LAB_FLOOR, ceiling=CEIL_LAMP, wall=TILE)
    zone("z3_lab_quarantine", HUT_FLOOR, HUT_CEIL, [QUARANTINE], light=LIGHT_CLOSET, flat=LAB_FLOOR,
         ceiling=CEIL_LAMP, wall=TILE_DADO)
    # S2: of the three instrument boards on the room's south wall the middle
    # one stands back in shadow; behind it, the prototype.
    for x1, x2 in zip(BOARDS_X, BOARDS_X[1:]):
        if (x1, x2) != S2_X:
            g.style_h(BOARDS_Y, x1, x2, LineStyle(texture=CONTROL))
    zone("s2_niche", HUT_FLOOR, HUT_CEIL, [(S2_X[0], BOARDS_Y - NICHE_DEPTH, S2_X[1], BOARDS_Y)],
         light=LIGHT_CLUE, flat=LAB_FLOOR, ceiling=CEIL_LAMP, wall=TILE_DADO)
    s2_panel = zone("s2_panel", HUT_FLOOR, HUT_FLOOR,
                    [(S2_X[0], BOARDS_Y - 2 * NICHE_DEPTH, S2_X[1], BOARDS_Y - NICHE_DEPTH)],
                    TAG_S2_PANEL, light=LIGHT_CLUE, flat=LAB_FLOOR, wall=TILE_DADO)
    zone("s2_passage", HUT_FLOOR, HUT_CEIL, [(S2_X[0], 1056, S2_X[1], BOARDS_Y - 2 * NICHE_DEPTH)],
         light=LIGHT_SECRET, flat=LAB_FLOOR, ceiling=CEIL_LAMP, wall=TILE_DADO)
    zone("s2_store", HUT_FLOOR, HUT_CEIL, [(1440, 928, 1696, 1056)], light=LIGHT_SECRET,
         flat=LAB_FLOOR, ceiling=CEIL_LAMP, wall=TILE_DADO, special=SECTOR_SPECIAL_SECRET)
    for y in (BOARDS_Y - NICHE_DEPTH, BOARDS_Y - 2 * NICHE_DEPTH):
        g.style_h(y, S2_X[0], S2_X[1], secret_panel_style(TAG_S2_PANEL, s2_panel, CONTROL))
    # The blue gate in the invaders' fence, north of the yard.
    bx1, bx2 = BLUE_GATE_X
    fy1, fy2 = FENCE_Y
    zone("z3_blue_portal", GROUND, DOOR_HEIGHT, [(bx1, fy1, bx2, fy1 + 32)], light=LIGHT_BEACON,
         flat=MOSS, ceiling=CEIL_CONCRETE, wall=ALIEN, extra=BLUE_LIGHT)
    blue_door = door("z4_blue_door", GROUND, TAG_BLUE_DOOR, (bx1, fy1 + 32, bx2, fy1 + 64),
                     light=LIGHT_STATION, wall=ALIEN)
    zone("z4_blue_porch", GROUND, DOOR_HEIGHT, [(bx1, fy1 + 64, bx2, fy2)], light=LIGHT_FOREST,
         flat=PEAT, ceiling=CEIL_CONCRETE, wall=ALIEN)
    g.style_h(fy1, STATION_YARD[0], bx1, LineStyle(texture=ALIEN))
    g.style_h(fy1, bx2, STATION_YARD[2], LineStyle(texture=ALIEN))

    # ======================================================================
    # Z4 The standing forest at the epicentre
    # ======================================================================
    zone("z4_forest", GROUND, FOREST_SKY, [FOREST], light=LIGHT_FOREST, flat=PEAT,
         ceiling=SKY, wall=BARK)
    for x, y in trunk_spots():
        g.carve(x - TRUNK // 2, y - TRUNK // 2, x + TRUNK // 2, y + TRUNK // 2)
    for x, y in birch_trunks():
        _outline(g, (x - TRUNK // 2, y - TRUNK // 2, x + TRUNK // 2, y + TRUNK // 2), BIRCH)
    fx1, fy1_, fx2, fy2_ = FOREST
    g.style_h(fy1_, fx1, bx1, LineStyle(texture=ALIEN))
    g.style_h(fy1_, bx2, fx2, LineStyle(texture=ALIEN))
    g.style_v(fx1, fy1_, fy2_, LineStyle(texture=BARK))
    g.style_h(fy2_, fx1, fx2, LineStyle(texture=BARK))
    g.style_v(fx2, fy1_, CONTAINMENT_Y[1], LineStyle(texture=ALIEN))

    # ======================================================================
    # Z5 The invaders' works
    # ======================================================================
    zone("z5_works", GROUND, WORKS_SKY, [WORKS], light=LIGHT_WORKS, flat=PLATE,
         ceiling=SKY, wall=ALIEN)
    like("z5_works", "z5_edge", [WORKS_EDGE], flat=BURNT, light=LIGHT_EDGE)
    # The edge's west wall stands where the forest goes on: the treeline.
    g.style_v(WORKS_EDGE[0], FOREST[3], WORKS_EDGE[3], LineStyle(texture=BARK))
    for n, rect in enumerate(WORKS_PITS, start=1):
        pit("z5_works", f"z5_acid_{n}", rect, WORKS_PIT_FLAT)
    for n, (x1, y1, x2, y2) in enumerate(TOWERS, start=1):
        prop("z5_works", f"z5_tower_{n}", [(x1, y1, x2, y2)], TOWER, wall=ALIEN, flat=PLATE)
        # A strip of glyph plates up the middle of each face.
        gx, gy = (x1 + x2 - GLYPH_WIDTH) // 2, (y1 + y2 - GLYPH_WIDTH) // 2
        for y in (y1, y2):
            g.style_h(y, gx, gx + GLYPH_WIDTH, LineStyle(texture=GLYPH))
        for x in (x1, x2):
            g.style_v(x, gy, gy + GLYPH_WIDTH, LineStyle(texture=GLYPH))
        i = TOWER_INSET
        prop("z5_works", f"z5_tower_{n}_core", [(x1 + i, y1 + i, x2 - i, y2 - i)], TOWER_CORE,
             wall=PORTAL, flat=PLATE, light=LIGHT_GLOW)
    for n, rect in enumerate(PIPES, start=1):
        prop("z5_works", f"z5_pipe_{n}", [rect], PIPE, wall=ALIEN, flat=PLATE)
    # The derrick: a stair of seven steps north out of the avenue to a platform
    # at 128; the yellow key at the stair's head.
    zone("z5_derrick", DERRICK, WORKS_SKY, [DERRICK_RECT], light=LIGHT_WORKS, flat=GRATING,
         ceiling=SKY, wall=STEEL)
    sx1_, sx2_ = DERRICK_STAIR_X
    for k in range(1, 8):
        y = DERRICK_STAIR_Y + STEP_DEPTH * (k - 1)
        zone(f"z5_dstair_{k}", STEP * k, WORKS_SKY, [(sx1_, y, sx2_, y + STEP_DEPTH)],
             light=LIGHT_WORKS, flat=GRATING, ceiling=SKY, wall=STEEL)
    zone("z5_key_top", DERRICK, WORKS_SKY, [KEY_TOP], light=LIGHT_BEACON, flat=GRATING,
         ceiling=SKY, wall=STEEL, extra=YELLOW_LIGHT)
    # V3 (A3): the works' cargo lift in the north wall, its gate's lamp flickering.
    zone("z5_lift_gate", GROUND, GROUND + DOOR_HEIGHT, [WORKS_LIFT_GATE], light=LIGHT_EVENT_LAMP, flat=PLATE,
         ceiling=CEIL_CONCRETE, wall=ALIEN, special=SECTOR_SPECIAL_LIGHT_FLICKER)
    zone("z5_lift_car", LIFT_CAR_FLOOR, LIFT_CAR_FLOOR + LIFT_CAR_HEIGHT, [WORKS_LIFT_CAR], TAG_WORKS_LIFT,
         light=LIGHT_CLOSET, flat=PLATE, ceiling=CEIL_CONCRETE, wall=STEEL)
    # S3: four recesses in the north wall, one tile of the invaders' metal each; the
    # third is set twice as deep, in shadow, and is a panel.
    for x in PIPE_RECESSES_X:
        if (x, x + TILE_SIZE) == S3_X:
            continue
        zone(f"z5_recess_{x}", GROUND, GROUND + TILE_SIZE,
             [(x, WORKS_NORTH, x + TILE_SIZE, WORKS_NORTH + NICHE_DEPTH)], light=LIGHT_WORKS,
             flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN)
    zone("s3_niche", GROUND, GROUND + TILE_SIZE,
         [(S3_X[0], WORKS_NORTH, S3_X[1], WORKS_NORTH + 2 * NICHE_DEPTH)], light=LIGHT_CLUE,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN)
    s3_panel = zone("s3_panel", GROUND, GROUND,
                    [(S3_X[0], WORKS_NORTH + 2 * NICHE_DEPTH, S3_X[1], WORKS_NORTH + 3 * NICHE_DEPTH)],
                    TAG_S3_PANEL, light=LIGHT_CLUE, flat=PLATE, wall=ALIEN)
    zone("s3_passage", GROUND, GROUND + TILE_SIZE,
         [(S3_X[0], WORKS_NORTH + 3 * NICHE_DEPTH, S3_X[1], 5712)], light=LIGHT_SECRET,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN)
    zone("s3_store", GROUND, GROUND + TILE_SIZE, [(3968, 5712, 4352, 5888)], light=LIGHT_SECRET,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN, special=SECTOR_SPECIAL_SECRET)
    for y in (WORKS_NORTH + 2 * NICHE_DEPTH, WORKS_NORTH + 3 * NICHE_DEPTH):
        g.style_h(y, S3_X[0], S3_X[1], secret_panel_style(TAG_S3_PANEL, s3_panel, ALIEN))
    # The red gate in the crater's containment wall, south of the works.
    rx1, rx2 = RED_GATE_X
    cy1, cy2 = CONTAINMENT_Y
    zone("z5_red_portal", GROUND, DOOR_HEIGHT, [(rx1, cy2 - 32, rx2, cy2)], light=LIGHT_BEACON,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN, extra=RED_LIGHT)
    red_door = door("z7_red_door", GROUND, TAG_RED_DOOR, (rx1, cy2 - 64, rx2, cy2 - 32),
                    light=LIGHT_PORCH, wall=ALIEN)
    zone("z7_red_porch", GROUND, DOOR_HEIGHT, [(rx1, cy1, rx2, cy2 - 64)], light=LIGHT_PORCH,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN)
    # The works' two closets in the containment wall, either side of the gate.
    for name, (cx1, cx2) in CLOSETS.items():
        zone(f"{name}_door", GROUND, GROUND, [(cx1, cy2 - NICHE_DEPTH, cx2, cy2)], TAG_AMBUSH,
             light=LIGHT_CLOSET, flat=PLATE, wall=ALIEN)
        zone(name, GROUND, GROUND + CLOSET_HEIGHT, [(cx1, cy1 + 32, cx2, cy2 - NICHE_DEPTH)],
             light=LIGHT_CLOSET, flat=PLATE, wall=ALIEN)
        # V3: the closet's warning lamp, a strip of the works' floor before it.
        like("z5_works", f"z5_closet_{name[-1]}_lamp", [(cx1, cy2, cx2, cy2 + NICHE_DEPTH)],
             light=LIGHT_EVENT_LAMP, special=SECTOR_SPECIAL_LIGHT_FLICKER)
    # The yellow door: the refinery's, in the works' east wall.
    wx1, wx2 = REFINERY_WALL_X
    yy1, yy2 = YELLOW_DOOR_Y
    zone("z5_yellow_portal", GROUND, DOOR_HEIGHT, [(wx1, yy1, wx1 + 32, yy2)], light=LIGHT_BEACON,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=BRICK, extra=YELLOW_LIGHT)
    yellow_door = door("z6_yellow_door", GROUND, TAG_YELLOW_DOOR, (wx1 + 32, yy1, wx1 + 64, yy2),
                       light=LIGHT_REFINERY)
    zone("z6_yellow_porch", GROUND, DOOR_HEIGHT, [(wx1 + 64, yy1, wx2, yy2)], light=LIGHT_REFINERY,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=BRICK)

    # ======================================================================
    # Z6 The refinery
    # ======================================================================
    zone("z6_refinery", GROUND, REFINERY_CEIL, [REFINERY], light=LIGHT_REFINERY, flat=PLATE,
         ceiling=CEIL_CONCRETE, wall=BRICK)
    pit("z6_refinery", "z6_channel", CHANNEL, CHANNEL_FLAT)
    zone("z6_bridge", GROUND, REFINERY_CEIL, [BRIDGE], light=LIGHT_REFINERY, flat=GRATING,
         ceiling=CEIL_CONCRETE, wall=STEEL)
    for n, rect in enumerate(VATS, start=1):
        prop("z6_refinery", f"z6_vat_{n}", [rect], VAT, wall=RUST, flat=MOLTEN)
    for n, rect in enumerate(TURBINES, start=1):
        prop("z6_refinery", f"z6_turbine_{n}", [rect], TURBINE_TOP, wall=TURBINE, flat=PLATE)
    prop("z6_refinery", "z6_console", [REF_CONSOLE], CONSOLE, wall=STEEL, flat=PLATE)
    g.style_h(REF_CONSOLE[1], REF_CONSOLE[0], REF_CONSOLE[2], LineStyle(texture=CONTROL))
    zone("z6_key_dais", DAIS_TOP, REFINERY_CEIL, [KEY_DAIS], light=LIGHT_BEACON, flat=PLATE,
         ceiling=CEIL_CONCRETE, wall=STEEL, extra=RED_LIGHT)
    # Two Soviet flags side by side on the refinery's brick (D119: SDFLAG1-4 are Soviet).
    fx1_, fy1f, fx2_, fy2f = FLAGS_RECESS
    zone("z6_flags", GROUND, GROUND + TILE_SIZE, [FLAGS_RECESS], light=LIGHT_REFINERY, flat=PLATE,
         ceiling=CEIL_CONCRETE, wall=BRICK)
    half = (fy1f + fy2f) // 2
    g.style_v(fx1_, fy1f, half, LineStyle(texture=FLAG_USSR_1))
    g.style_v(fx1_, half, fy2f, LineStyle(texture=FLAG_USSR_2))

    # ======================================================================
    # Z7 The crater's rim, Z8 its terraces and floor, Z9 the control bunker
    # ======================================================================
    zone("z7_rim", GROUND, CRATER_SKY, [CRATER], light=LIGHT_CRATER, flat=BURNT,
         ceiling=SKY, wall=ALIEN)
    x1, y1, x2, y2 = CRATER
    for k in range(1, TERRACES + 1):
        i = RIM + TERRACE * (k - 1)
        zone(f"z8_tier_{k}", GROUND - STEP * k, CRATER_SKY, [(x1 + i, y1 + i, x2 - i, y2 - i)],
             light=LIGHT_CRATER, flat=BURNT, ceiling=SKY, wall=ALIEN)
    i = RIM + TERRACE * TERRACES
    zone("z8_floor", CRATER_FLOOR, CRATER_SKY, [(x1 + i, y1 + i, x2 - i, y2 - i)],
         light=LIGHT_CRATER, flat=PLATE, ceiling=SKY, wall=ALIEN)
    for n, rect in enumerate(CRATER_PITS, start=1):
        pit("z8_floor", f"z8_acid_{n}", rect, CRATER_PIT_FLAT)
    for n, (px, py) in enumerate(PYLONS, start=1):
        prop("z8_floor", f"z8_pylon_{n}", [(px, py, px + PYLON_SIZE, py + PYLON_SIZE)], PYLON,
             wall=GLYPH, flat=PLATE)
    prop("z8_floor", "z8_portal_base", [PORTAL_BASE], PORTAL_PLINTH, wall=ALIEN, flat=PLATE)
    prop("z8_floor", "z8_portal", [PORTAL_FIELD], PORTAL_TOP, wall=PORTAL, flat=PLATE,
         light=LIGHT_GLOW)
    for n, rect in enumerate(frame_posts(), start=1):
        prop("z8_floor", f"z8_frame_{n}", [rect], FRAME_TOP, wall=PORTAL_RIM, flat=PLATE,
             light=LIGHT_GLOW)
    # The control bunker under the south rim: the gate only the boss's death opens.
    ex1, ex2 = EXIT_X
    zone("z9_exit_porch", GROUND, DOOR_HEIGHT, [(ex1, y1 - 32, ex2, y1)], light=LIGHT_PORCH,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=ALIEN)
    exit_gate = door("z9_gate", GROUND, TAG_BOSS_EXIT, (ex1, y1 - 64, ex2, y1 - 32),
                     light=LIGHT_EXIT_HALL)
    zone("z9_hall", GROUND, DOOR_HEIGHT, [BUNKER], light=LIGHT_EXIT_HALL, flat=PLATE,
         ceiling=CEIL_LAMP, wall=STEEL)
    zone("z9_exit_niche", GROUND, GROUND + SWITCH_HEIGHT, [EXIT_NICHE], light=LIGHT_BEACON,
         flat=PLATE, ceiling=CEIL_LAMP, wall=STEEL)

    # ======================================================================
    # Line styles: the three locks, the bunker's gate, the exit
    # ======================================================================
    for y in (fy1 + 32, fy1 + 64):
        g.style_h(y, bx1, bx2, locked_door_style(TAG_BLUE_DOOR, blue_door, LOCK_BLUE_CARD,
                                                 texture=DOOR))
    for x in (wx1 + 32, wx1 + 64):
        g.style_v(x, yy1, yy2, locked_door_style(TAG_YELLOW_DOOR, yellow_door, LOCK_YELLOW_CARD,
                                                 texture=DOOR_YELLOW))
    for y in (cy2 - 64, cy2 - 32):
        g.style_h(y, rx1, rx2, locked_door_style(TAG_RED_DOOR, red_door, LOCK_RED_CARD,
                                                 texture=DOOR_RED))
    # The bunker's gate: a shut gate on both faces, no special on either, so
    # pressing it does nothing and only the boss's death opens it.
    for y in (y1 - 64, y1 - 32):
        g.style_h(y, ex1, ex2, remote_door_style(exit_gate, texture=GATE))
    g.style_h(EXIT_NICHE[1], EXIT_NICHE[0], EXIT_NICHE[2], exit_switch_style(texture=EXIT_FACE))

    g.build()
    align_to_world(tm)
    # The cab's pictures start on each wall's left end (SDCAB1 is one 128
    # face), and each frame post shows the middle of its lump.
    align_run(tm, True, kx1, ky1, ky2, width=128)
    for args in ((True, kx2, ky1, ky2), (False, ky1, kx1, kx2), (False, ky2, kx1, CAB_DOOR[0])):
        align_run(tm, *args, width=64)
    for x1, y1, x2, y2 in frame_posts():
        for x in (x1, x2):
            align_run(tm, True, x, y1, y2, width=64, base=FRAME_OFFSET)
        for y in (y1, y2):
            align_run(tm, False, y, x1, x2, width=64, base=FRAME_OFFSET)

    # Things.
    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=BLUE_KEY_SPOT[0], y=BLUE_KEY_SPOT[1], type=ED_BLUE_CARD,
                       extra=pickup_special(ED_BLUE_CARD, BLUE_KEY_SPOT)))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD,
                       extra=pickup_special(ED_YELLOW_CARD, YELLOW_KEY_SPOT)))
    special, args = RED_KEY_SPECIAL
    tm.add_thing(Thing(x=RED_KEY_SPOT[0], y=RED_KEY_SPOT[1], type=ED_RED_CARD,
                       extra={"special": special, **{f"arg{i}": a for i, a in enumerate(args)}}))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        extra = {}
        if (x, y) == MAP09_BOSS_SPOT and kind == BOSS_KIND:
            special, args = BOSS_DEATH_SPECIAL
            extra = {"special": special, **{f"arg{i}": a for i, a in enumerate(args)}}
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle,
                                     extra=extra))
    for _zone, ednum, x, y, top in ITEMS + SECRET_ITEMS:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top)))
    for _zone, ednum, x, y, lowest in AMMO:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(lowest)))
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
        (MAP_NAME, b""),
        ("TEXTMAP", build_textmap().to_bytes()),
        ("ENDMAP", b""),
    ]


# Every lump name this map may put in a sidedef or a sector.
WALL_TEXTURES = ((CONCRETE, STEEL, CRATE, LOCKER, TILE, TILE_DADO, BRICK, RUST, PORTAL,
                  FLAG_USSR_1, FLAG_USSR_2, WAGON, ARMOUR_STAR, ARMOUR, SIGNAL, TURBINE, CONTROL,
                  CAB_FRONT, CAB_SIDE, BARK, BIRCH, LOG_WALL, ALIEN, GLYPH, PORTAL_RIM,
                  LENIN, STALIN, MURAL) + DOOR_LEAVES + SWITCH_FACES
                 + MARX_ENGELS)
FLAT_TEXTURES = (CRATE_TOP, LAB_FLOOR, CEIL_LAMP, CEIL_CONCRETE, PLATE, GRATING, MOLTEN, TRACK,
                 BALLAST, BURNT, PEAT, MOSS, ACID, SKY)
