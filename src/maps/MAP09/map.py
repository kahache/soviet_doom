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
packed lumps only, populated and stocked. Wood, bark, moss, burnt earth and
alien metal have no approved lump yet: each wears the closest approved one
and is listed under "Pending textures" in the design document (the
art-director is drawing a "Taiga/Alien" set as a draft).

The route, in one line: the railhead (the train he came on, the halt) ->
west along the forest road through the fallen taiga -> the station's gate
(the BLUE gate in the invaders' fence seen at once) -> the laboratory, the
BLUE KEY on its bench -> the blue gate -> the standing dead forest -> the
invaders' works (the RED gate of the crater's containment wall, the YELLOW
door of the refinery and the YELLOW KEY on the derrick all seen from the
forest's edge) -> up the derrick's stair over the molten pit, the yellow key
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
  TAG_BOSS_EXIT and NO line carries that tag. He stands at MAP09_BOSS_SPOT;
  until episode 3's own final boss exists he is the General (BOSS_KIND);
* a key that springs an ambush: the red key's thing carries Door_Open on
  TAG_AMBUSH (Hexen-style item special). NOT VERIFIED in engine.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method;
the fallen trunks lie radially from the crater's centre, the diagonal ones
as staircases of 48-unit blocks (GridMap is axis-aligned).

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP09 SKILL=3 tools/run.sh
"""

from __future__ import annotations

import math
from dataclasses import replace

from sdbuild.udmf import (
    DOOR_SPEED_SLOW,
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
STEEL = "SDSTEL1"       # the invaders' fence, the buffer stop, the terraces' faces, the bunker
DOOR = "SDDOOR1"        # the blue gate's leaf (SDDOORB pending, as MAP06's)
CRATE = "SDCRAT1"       # stores in the station
CRATE_TOP = "SDCRTOP1"  # planks: the halt's and the izbas' floors and ceilings, the logs' tops
LOCKER = "SDLOCK1"      # the halt's row of lockers (S1)
LAB_FLOOR = "SDFLR3"    # grey two-tone tiles: the laboratory
CEIL_LAMP = "SDCEIL1"   # the laboratory's fluorescent panels
CEIL_CONCRETE = "SDCEIL2"
EXIT_FACE = "SDSW1D"    # the hazard panel every map's exit wears: the portal's breaker
# Metro
TILE = "SDTILE1"        # the laboratory's hall
TILE_DADO = "SDTILE2"   # the instrument room (128 high: one tile, its dado whole)
TUBBING = "SDTUBB1"     # cast-iron rings: the crater's containment wall, the works' towers (alien metal, stand-in)
# Tankograd
BRICK = "SDBRCK1"       # the refinery (the invaders build with what they take)
RUST = "SDRUST1"        # stripped trunks of the standing forest (bark, stand-in); the vats
DOOR_YELLOW = "SDDOORY"
DOOR_RED = "SDDOORR"
PORTAL = "SDPORT1"      # the portal's field, animated SDPORT1-4 (ANIMDEFS); the towers' cores
GATE = "SDGATE1"        # the control bunker's gate (the boss's death opens it)
FLAG_REICH = "SDFLAG1"
FLAG_LEGION = "SDFLAG2"
PLATE = "SDFLR4"        # the works' and the refinery's floors, the crater's floor
GRATING = "SDGRAT1"     # the refinery's bridge
MOLTEN = "SDMOLT1"      # the molten pits and channel, animated SDMOLT1-4 (ANIMDEFS)
# Railway (episode 2)
TRACK = "SDTRAK1"       # the railhead's track, rails along the flat's y: turned a quarter
BALLAST = "SDBLST1"     # the ground: ballast at the railhead, burnt earth everywhere outdoors (stand-in)
WAGON = "SDWAGN1"       # weathered planking: the goods wagon, the halt, the izbas, the palisade,
                        # the treeline and the fallen trunks (wood and bark, stand-in)
ARMOUR_STAR = "SDARMR1"     # the armoured wagon's flanks, a star per 128
ARMOUR = "SDARMR2"
SIGNAL = "SDSIGL1"      # the railhead's signal: single use only (D107), one 64 face
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
# The Marx-Engels poster SDPOSTR4 is in preparation and is not a lump yet. Its
# slots are built and wear a stand-in; approving it is this one line:
MARX_ENGELS: str | None = None   # -> "SDPOSTR4"

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

# Molten metal hurts: MAP03's UDMF sector fields, 10 every 32 tics (Doom's
# hellslime). Every pit is one step deep: walked out of, never a trap.
LAVA_DAMAGE = 10
LAVA_DAMAGE_INTERVAL = 32
LAVA_HURTS = {"damageamount": LAVA_DAMAGE, "damageinterval": LAVA_DAMAGE_INTERVAL}

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
TOWER = 256             # a tower's cast-iron body
TOWER_CORE = TOWER + TILE_SIZE      # its glowing core, one tile of the portal's field
DERRICK = 128           # the yellow key's platform: 8 steps up
LAVA = GROUND - STEP    # a molten pit: one step down
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
SECRET_PANEL_TAGS = (TAG_S1_PANEL, TAG_S2_PANEL, TAG_S3_PANEL)

# --- The boss --------------------------------------------------------------------
# Episode 3's final boss does not exist yet (D112). Until it does, the General
# stands in. To swap him: change BOSS_KIND (and add the new class to
# MONSTER_KINDS/MONSTER_CLASSES); the spot, the facing and the death special stay.
CRATER_CENTRE = (3968, 2816)    # the portal; the fallen trunks lie away from it
MAP09_BOSS_SPOT = (3968, 3136)  # on the crater's floor before the portal, facing the red gate
BOSS_ANGLE = 90
BOSS_KIND = "general"
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
         ("loco", (7104, 432, 7488, 528), ARMOUR))
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
CLEARING = (1664, 2944, 2304, 3456)
FOREST_PATHS = ((1792, 1952, 2304, 2304),)  # kept clear behind the blue gate
# Z5 The invaders' works, eating the forest.
WORKS = (2752, 3968, 5440, 5632)
WORKS_EDGE = (2752, 3968, 3200, 5632)
DERRICK_RECT = (4000, 4992, 4256, 5184)
DERRICK_STAIR_X = (4064, 4192)
DERRICK_STAIR_Y = 4768          # 7 steps of 32 north from here up to the platform at 4992
KEY_TOP = (4064, 4992, 4192, 5056)
WORKS_LAVA = ((3712, 4480, 4544, 4704), (4736, 4352, 4928, 4672))
TOWERS = ((3328, 4992, 3520, 5184), (4608, 5248, 4800, 5440), (4992, 4096, 5184, 4288))
TOWER_INSET = 32
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
FLAGS_RECESS = (5520, 4864, 5536, 4992)     # the two banners side by side (D12)
# Z7 The crater's rim, Z8 its terraces and floor, Z9 the control bunker.
CRATER = (2944, 1792, 4992, 3840)
RIM = 128
TERRACE = 64
PORTAL_BASE = (3840, 2688, 4096, 2944)
PORTAL_FIELD = (3872, 2720, 4064, 2912)
PYLONS = ((3584, 2432), (4288, 2432), (3584, 3136), (4288, 3136))
PYLON_SIZE = 64
CRATER_LAVA = ((3680, 2528, 3808, 2656), (4128, 2528, 4256, 2656), (3680, 2976, 3808, 3104),
               (4128, 2976, 4256, 3104))
EXIT_X = (3904, 4032)
BUNKER = (3840, 1536, 4096, 1728)
EXIT_NICHE = (3936, 1520, 4000, 1536)

# Every picture on the map: (name, texture, axis, coord, lo, hi). All in the
# research station: the laboratory's hall is exactly a poster high.
POSTERS = (
    # The hall: Lenin over the bench where the blue key lies, Stalin on the
    # west wall, the two slots either side.
    ("lab_hall_lenin", LENIN, "h", LAB_HALL[3], 1504, 1632),
    ("lab_hall_stalin", STALIN, "v", LAB_HALL[0], 1360, 1488),
    ("lab_hall_slot_n", STALIN, "h", LAB_HALL[3], 1664, 1792),
    ("lab_hall_slot_s", LENIN, "h", LAB_HALL[1], 1344, 1472),
    # The instrument room (128 high): the cosmonautics mural beside the boards.
    ("lab_instr_mural", MURAL, "v", LAB_INSTR[0], LAB_INSTR[1], LAB_INSTR[3]),
)
POSTER_SLOTS_MARX_ENGELS = ("lab_hall_slot_n", "lab_hall_slot_s")


def poster_faces():
    """POSTERS with each Marx-Engels slot wearing SDPOSTR4 once it exists."""
    return tuple((name, MARX_ENGELS if MARX_ENGELS and name in POSTER_SLOTS_MARX_ENGELS else texture,
                  axis, coord, lo, hi) for name, texture, axis, coord, lo, hi in POSTERS)


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


# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100
ED_TROOPER = 21101
ED_STORMTROOPER = 21102
ED_HOUND = 21103
ED_DOUGHBOY = 21104
ED_PANZERMENSCH = 21105
ED_GENERAL = 21106        # the stand-in boss
ED_PANZER_HEAVY = 21107
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
    "general": ED_GENERAL,
    "heavy": ED_PANZER_HEAVY,
}
MONSTER_CLASSES = {
    ED_RIFLEMAN: "SD_ReichRifleman",
    ED_TROOPER: "SD_LegionTrooper",
    ED_STORMTROOPER: "SD_Stormtrooper",
    ED_HOUND: "SD_ReichHound",
    ED_DOUGHBOY: "SD_Doughboy",
    ED_PANZERMENSCH: "SD_Panzermensch",
    ED_GENERAL: "SD_General",
    ED_PANZER_HEAVY: "SD_PanzermenschSchwer",
}
REICH = ("rifleman", "hound", "panzermensch", "heavy")
LEGION = ("trooper", "doughboy", "general")
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
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # in S2 only: the laboratory's secret prototype
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

# Design section 10: monsters per skill, Doom's skill pairs (udmf.skill_tier).
ENEMY_TOTALS = {2: 57, 3: 88, 4: 122}

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
    ("z3_lab_hall", "trooper", 1728, 1504, 0, 2),
    ("z3_lab_vest", "trooper", 1920, 1448, 0, 2),
    ("z3_lab_instr", "trooper", 1408, 1184, 0, 2),
    ("z3_lab_hall", "trooper", 1408, 1520, 0, 3),
    ("z3_lab_instr", "stormtrooper", 1728, 1184, 180, 3),
    ("z3_lab_hall", "doughboy", 1712, 1360, 180, 4),
    ("z3_lab_instr", "trooper", 1600, 1184, 90, 4),
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
    ("z5_works", "rifleman", 4992, 5568, 180, 2),
    ("z5_edge", "trooper", 3008, 5248, 270, 2),
    ("z5_works", "rifleman", 3456, 4608, 180, 3),
    ("z5_works", "trooper", 3840, 5504, 180, 3),
    ("z5_works", "stormtrooper", 4992, 4800, 180, 3),
    ("z5_works", "hound", 4544, 4224, 180, 3),
    ("z5_works", "doughboy", 3328, 5440, 180, 3),
    ("z5_derrick", "trooper", 4032, 5152, 270, 3),
    ("z5_works", "rifleman", 5312, 5376, 180, 3),
    ("z5_works", "stormtrooper", 4480, 5568, 180, 3),
    ("z5_works", "heavy", 5056, 5056, 180, 4),
    ("z5_works", "panzermensch", 3712, 4224, 180, 4),
    ("z5_works", "stormtrooper", 4224, 4096, 180, 4),
    ("z5_works", "rifleman", 3584, 5056, 180, 4),
    ("z5_works", "trooper", 4864, 5248, 180, 4),
    ("z5_works", "hound", 5248, 4224, 180, 4),
    ("z5_works", "doughboy", 4736, 5056, 180, 4),
    ("z5_works", "rifleman", 5312, 4992, 180, 4),
    ("z5_works", "stormtrooper", 3392, 4800, 180, 4),
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
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on - 4 every skill, 3 medium and easier, 2 easy only).
ITEMS = (
    # The weapons, on every skill, each before the fight it is for.
    ("z1_halt", ED_IZH, 7040, 864, 4),
    ("z3_izba_a", ED_PPSH, 832, 736, 4),
    ("z4_forest", ED_RPG7, 2560, 4288, 4),
    ("z5_edge", ED_ROKS3, 3008, 4800, 4),
    # Shell boxes (20).
    ("z1_halt", ED_SHELL_BOX, 6912, 800, 4),
    ("z2_taiga", ED_SHELL_BOX, 4224, 960, 4),
    ("z3_yard", ED_SHELL_BOX, 2176, 960, 4),
    ("z3_izba_b", ED_SHELL_BOX, 736, 1312, 4),
    ("z3_lab_vest", ED_SHELL_BOX, 2016, 1376, 4),
    ("z4_forest", ED_SHELL_BOX, 1792, 3008, 4),
    ("z4_forest", ED_SHELL_BOX, 2560, 4032, 4),
    ("z5_edge", ED_SHELL_BOX, 2880, 4160, 4),
    ("z5_edge", ED_SHELL_BOX, 2880, 5376, 4),
    ("z5_works", ED_SHELL_BOX, 4992, 4416, 4),
    ("z6_yellow_porch", ED_SHELL_BOX, 5520, 4736, 4),
    ("z6_refinery", ED_SHELL_BOX, 5632, 4096, 4),
    ("z6_refinery", ED_SHELL_BOX, 7232, 4608, 4),
    ("z7_rim", ED_SHELL_BOX, 3008, 3776, 4),
    ("z7_rim", ED_SHELL_BOX, 4928, 3776, 4),
    ("z7_rim", ED_SHELL_BOX, 3008, 1856, 4),
    ("z7_rim", ED_SHELL_BOX, 4928, 1856, 4),
    ("z7_rim", ED_SHELL_BOX, 4928, 3200, 4),
    ("z5_works", ED_SHELL_BOX, 4416, 5568, 4),
    ("z6_refinery", ED_SHELL_BOX, 6176, 5056, 4),
    ("z2_taiga", ED_SHELL_BOX, 2496, 960, 3),
    ("z5_edge", ED_SHELL_BOX, 3072, 4416, 3),
    ("z6_refinery", ED_SHELL_BOX, 5632, 5312, 3),
    ("z3_yard", ED_SHELL_BOX, 576, 1472, 2),
    ("z5_edge", ED_SHELL_BOX, 2880, 4672, 2),
    # Shells (4).
    ("z1_yard", ED_SHELLS, 6656, 1056, 4),
    ("z2_taiga", ED_SHELLS, 5632, 960, 4),
    ("z2_taiga", ED_SHELLS, 3008, 480, 4),
    ("z3_izba_c", ED_SHELLS, 832, 1664, 4),
    ("z4_forest", ED_SHELLS, 1152, 2240, 4),
    ("z5_works", ED_SHELLS, 3840, 4864, 4),
    ("z6_refinery", ED_SHELLS, 6176, 4736, 4),
    ("z2_taiga", ED_SHELLS, 4800, 960, 3),
    ("z4_forest", ED_SHELLS, 2048, 3712, 3),
    ("z6_refinery", ED_SHELLS, 6176, 4480, 3),
    ("z1_yard", ED_SHELLS, 6560, 800, 2),
    ("z3_yard", ED_SHELLS, 1856, 512, 2),
    # Boxes of rounds (50).
    ("z3_izba_a", ED_CLIP_BOX, 928, 800, 4),
    ("z3_lab_hall", ED_CLIP_BOX, 1376, 1312, 4),
    ("z4_forest", ED_CLIP_BOX, 2048, 2304, 4),
    ("z5_edge", ED_CLIP_BOX, 3136, 5056, 4),
    ("z5_works", ED_CLIP_BOX, 5376, 4736, 4),
    ("z6_refinery", ED_CLIP_BOX, 7232, 4864, 4),
    ("z7_red_porch", ED_CLIP_BOX, 3936, 3872, 4),
    ("z7_rim", ED_CLIP_BOX, 3968, 3776, 4),
    ("z5_works", ED_CLIP_BOX, 4992, 5568, 3),
    ("z3_yard", ED_CLIP_BOX, 2176, 1504, 2),
    # Clips (10).
    ("z1_platform", ED_CLIP, 6720, 640, 4),
    ("z2_taiga", ED_CLIP, 5824, 1280, 4),
    ("z3_yard", ED_CLIP, 576, 960, 4),
    ("z4_forest", ED_CLIP, 2560, 2240, 4),
    ("z5_works", ED_CLIP, 4416, 4096, 4),
    ("z2_taiga", ED_CLIP, 3648, 1376, 3),
    ("z1_yard", ED_CLIP, 5952, 832, 2),
    # PG-7V: a box with the RPG-7, boxes in the works, the refinery and on
    # the rim, loose rounds round the crater.
    ("z4_forest", ED_ROCKET_BOX, 2496, 4352, 4),
    ("z5_works", ED_ROCKET_BOX, 5312, 4608, 4),
    ("z6_refinery", ED_ROCKET_BOX, 5632, 4736, 4),
    ("z7_rim", ED_ROCKET_BOX, 3968, 3712, 4),
    ("z7_rim", ED_ROCKET_BOX, 3008, 2816, 4),
    ("z7_rim", ED_ROCKET_BOX, 4928, 2816, 4),
    ("z7_rim", ED_ROCKET, 3008, 3328, 4),
    ("z7_rim", ED_ROCKET, 4928, 3328, 4),
    ("z7_rim", ED_ROCKET, 3008, 2304, 4),
    ("z7_rim", ED_ROCKET, 4928, 2304, 4),
    ("z5_works", ED_ROCKET, 4416, 5056, 4),
    ("z6_refinery", ED_ROCKET, 6176, 5248, 4),
    ("z6_refinery", ED_ROCKET, 6176, 4224, 4),
    ("z6_refinery", ED_ROCKET_BOX, 7232, 4992, 3),
    ("z7_rim", ED_ROCKET_BOX, 4480, 3776, 3),
    # Fuel for the ROKS-3: a canister beside it, more in the works, the
    # refinery and on the rim, a pack in the red gate's porch.
    ("z5_edge", ED_CELL, 3072, 4800, 4),
    ("z5_works", ED_CELL, 5312, 5248, 4),
    ("z6_refinery", ED_CELL, 5632, 4480, 4),
    ("z7_rim", ED_CELL, 3328, 3776, 4),
    ("z7_red_porch", ED_CELL_PACK, 4000, 3872, 4),
    ("z7_rim", ED_CELL, 4608, 3776, 3),
    # Stimpacks: 7 on every skill, +3 medium, +2 easy.
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
    # Medikits: 7 on every skill, +2 medium.
    ("z3_izba_b", ED_MEDIKIT, 928, 1152, 4),
    ("z4_forest", ED_MEDIKIT, 2176, 3328, 4),
    ("z5_works", ED_MEDIKIT, 5376, 4096, 4),
    ("z6_refinery", ED_MEDIKIT, 7232, 5312, 4),
    ("z6_refinery", ED_MEDIKIT, 7232, 4032, 4),
    ("z7_rim", ED_MEDIKIT, 3008, 2880, 4),
    ("z7_rim", ED_MEDIKIT, 4928, 2880, 4),
    ("z5_edge", ED_MEDIKIT, 2816, 3968 + 64, 3),
    ("z7_rim", ED_MEDIKIT, 4160, 1856, 3),
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


def _outline(g: GridMap, rect, texture: str) -> None:
    """Style the four sides of a rectangle with one texture."""
    x1, y1, x2, y2 = rect
    style = LineStyle(texture=texture)
    g.style_h(y1, x1, x2, style)
    g.style_h(y2, x1, x2, style)
    g.style_v(x1, y1, y2, style)
    g.style_v(x2, y1, y2, style)


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=WAGON)
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
        """A closed door sector; its own walls are the jambs."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=wall)

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

    def lava(room: str, name: str, rect) -> int:
        """A molten pit one step deep: it hurts, and it is walked out of."""
        extra = {**tm.sectors[plan[room]].extra, **LAVA_HURTS}
        return like(room, name, [rect], floor=tm.sectors[plan[room]].heightfloor - STEP,
                    light=LIGHT_LAVA, flat=MOLTEN, wall=STEEL, extra=extra)

    def hut(room: str, name: str, roof, door_rect) -> None:
        """A wooden hut: a roof block, its room one step up inside, and a
        doorway whose sky sits on the roof's line (no slab above it)."""
        x1, y1, x2, y2 = roof
        block(f"{PROP_PREFIX}{name}_roof", ROOF, [roof], wall=WAGON,
              light=tm.sectors[plan[room]].lightlevel)
        zone(name, HUT_FLOOR, HUT_CEIL, [(x1 + IZBA_WALL, y1 + IZBA_WALL, x2 - IZBA_WALL, y2 - IZBA_WALL)],
             light=LIGHT_IZBA, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=WAGON)
        zone(f"{name}_door", HUT_FLOOR, ROOF, [door_rect], light=LIGHT_IZBA, flat=CRATE_TOP,
             ceiling=SKY, wall=WAGON)

    # The posters first: GridMap keeps the first style registered on a
    # segment, so nothing broader can paint over them.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))

    # ======================================================================
    # Z1 The railhead (start)
    # ======================================================================
    zone("z1_ballast", GROUND, RAIL_SKY, [RAIL_BALLAST], light=LIGHT_RAIL, flat=BALLAST,
         ceiling=SKY, wall=WAGON)
    zone("z1_yard", GROUND, RAIL_SKY, [RAIL_YARD], light=LIGHT_RAIL, flat=BALLAST,
         ceiling=SKY, wall=WAGON)
    like("z1_ballast", "z1_track", [RAIL_TRACK], flat=TRACK, extra={"rotationfloor": 90.0})
    zone("z1_platform", PLATFORM, RAIL_SKY, [RAIL_PLATFORM], light=LIGHT_RAIL, flat=CRATE_TOP,
         ceiling=SKY, wall=WAGON)
    prop("z1_ballast", "z1_buffer", [BUFFER], BUFFER_TOP, wall=STEEL, flat=PLATE)
    for name, rect, wall in TRAIN:
        prop("z1_ballast", f"z1_{name}", [rect], WAGON_TOP, wall=wall, flat=PLATE)
    # The armoured wagon's long flanks: one whole red star per 128.
    _, (ax1, ay1, ax2, ay2), _ = TRAIN[1]
    for y in (ay1, ay2):
        g.style_h(y, ax1, ax2, LineStyle(texture=ARMOUR_STAR))
    sx1, sy1, sx2, sy2 = SIGNAL_POST
    prop("z1_yard", "z1_signal", [SIGNAL_POST], SIGNAL_TOP, wall=STEEL, flat=PLATE)
    g.style_v(sx2, sy1, sy2, LineStyle(texture=SIGNAL))
    # The halt: a wooden hut on the platform, the IZh on its bench.
    block(f"{PROP_PREFIX}z1_halt_roof", ROOF, [HALT_ROOF], wall=WAGON, light=LIGHT_RAIL)
    zone("z1_halt", HUT_FLOOR, HUT_CEIL, [HALT], light=LIGHT_HALT, flat=CRATE_TOP,
         ceiling=CRATE_TOP, wall=WAGON)
    zone("z1_halt_door", HUT_FLOOR, ROOF, [HALT_DOOR], light=LIGHT_HALT, flat=CRATE_TOP,
         ceiling=SKY, wall=WAGON)
    # S1: of the three lockers on the halt's east wall the middle one stands
    # back in shadow; it is a panel onto the stationmaster's store.
    lx = LOCKERS_X
    for y1, y2 in zip(LOCKERS_Y, LOCKERS_Y[1:]):
        if (y1, y2) != S1_Y:
            g.style_v(lx, y1, y2, LineStyle(texture=LOCKER))
    zone("s1_niche", HUT_FLOOR, HUT_CEIL, [(lx, S1_Y[0], lx + NICHE_DEPTH, S1_Y[1])],
         light=LIGHT_CLUE, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=WAGON)
    s1_panel = zone("s1_panel", HUT_FLOOR, HUT_FLOOR,
                    [(lx + NICHE_DEPTH, S1_Y[0], lx + 2 * NICHE_DEPTH, S1_Y[1])], TAG_S1_PANEL,
                    light=LIGHT_CLUE, flat=CRATE_TOP, wall=WAGON)
    zone("s1_passage", HUT_FLOOR, HUT_CEIL, [(lx + 2 * NICHE_DEPTH, S1_Y[0], HALT_ROOF[2], S1_Y[1])],
         light=LIGHT_SECRET, flat=CRATE_TOP, ceiling=CRATE_TOP, wall=WAGON)
    zone("s1_store", HUT_FLOOR, HUT_CEIL, [(HALT_ROOF[2], 768, 7488, 1024)], light=LIGHT_SECRET,
         flat=CRATE_TOP, ceiling=CRATE_TOP, wall=WAGON, special=SECTOR_SPECIAL_SECRET)
    for x in (lx + NICHE_DEPTH, lx + 2 * NICHE_DEPTH):
        g.style_v(x, S1_Y[0], S1_Y[1], secret_panel_style(TAG_S1_PANEL, s1_panel, LOCKER))

    # ======================================================================
    # Z2 The fallen taiga
    # ======================================================================
    zone("z2_taiga", GROUND, TAIGA_SKY, [TAIGA], light=LIGHT_TAIGA, flat=BALLAST,
         ceiling=SKY, wall=WAGON)
    for n, (cx, cy, length) in enumerate(LOGS, start=1):
        prop("z2_taiga", f"z2_log_{n}", log_rects(cx, cy, length), LOG, wall=WAGON, flat=CRATE_TOP)

    # ======================================================================
    # Z3 The research station
    # ======================================================================
    zone("z3_yard", GROUND, STATION_SKY, [STATION_YARD], light=LIGHT_STATION, flat=BALLAST,
         ceiling=SKY, wall=WAGON)
    zone("z3_gate", GROUND, STATION_SKY, [STATION_GATE], light=LIGHT_STATION, flat=BALLAST,
         ceiling=SKY, wall=WAGON)
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
         flat=BALLAST, ceiling=CEIL_CONCRETE, wall=STEEL, extra=BLUE_LIGHT)
    blue_door = door("z4_blue_door", GROUND, TAG_BLUE_DOOR, (bx1, fy1 + 32, bx2, fy1 + 64),
                     light=LIGHT_STATION)
    zone("z4_blue_porch", GROUND, DOOR_HEIGHT, [(bx1, fy1 + 64, bx2, fy2)], light=LIGHT_FOREST,
         flat=BALLAST, ceiling=CEIL_CONCRETE, wall=STEEL)
    g.style_h(fy1, STATION_YARD[0], bx1, LineStyle(texture=STEEL))
    g.style_h(fy1, bx2, STATION_YARD[2], LineStyle(texture=STEEL))

    # ======================================================================
    # Z4 The standing forest at the epicentre
    # ======================================================================
    zone("z4_forest", GROUND, FOREST_SKY, [FOREST], light=LIGHT_FOREST, flat=BALLAST,
         ceiling=SKY, wall=RUST)
    for x, y in trunk_spots():
        g.carve(x - TRUNK // 2, y - TRUNK // 2, x + TRUNK // 2, y + TRUNK // 2)
    fx1, fy1_, fx2, fy2_ = FOREST
    g.style_h(fy1_, fx1, bx1, LineStyle(texture=STEEL))
    g.style_h(fy1_, bx2, fx2, LineStyle(texture=STEEL))
    g.style_v(fx1, fy1_, fy2_, LineStyle(texture=WAGON))
    g.style_h(fy2_, fx1, fx2, LineStyle(texture=WAGON))
    g.style_v(fx2, fy1_, CONTAINMENT_Y[1], LineStyle(texture=TUBBING))

    # ======================================================================
    # Z5 The invaders' works
    # ======================================================================
    zone("z5_works", GROUND, WORKS_SKY, [WORKS], light=LIGHT_WORKS, flat=PLATE,
         ceiling=SKY, wall=TUBBING)
    like("z5_works", "z5_edge", [WORKS_EDGE], flat=BALLAST, light=LIGHT_EDGE)
    for n, rect in enumerate(WORKS_LAVA, start=1):
        lava("z5_works", f"z5_lava_{n}", rect)
    for n, (x1, y1, x2, y2) in enumerate(TOWERS, start=1):
        prop("z5_works", f"z5_tower_{n}", [(x1, y1, x2, y2)], TOWER, wall=TUBBING, flat=PLATE)
        i = TOWER_INSET
        prop("z5_works", f"z5_tower_{n}_core", [(x1 + i, y1 + i, x2 - i, y2 - i)], TOWER_CORE,
             wall=PORTAL, flat=PLATE, light=LIGHT_GLOW)
    for n, rect in enumerate(PIPES, start=1):
        prop("z5_works", f"z5_pipe_{n}", [rect], PIPE, wall=STEEL, flat=PLATE)
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
    # S3: four recesses in the north wall, one tile of cast iron each; the
    # third is set twice as deep, in shadow, and is a panel.
    for x in PIPE_RECESSES_X:
        if (x, x + TILE_SIZE) == S3_X:
            continue
        zone(f"z5_recess_{x}", GROUND, GROUND + TILE_SIZE,
             [(x, WORKS_NORTH, x + TILE_SIZE, WORKS_NORTH + NICHE_DEPTH)], light=LIGHT_WORKS,
             flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING)
    zone("s3_niche", GROUND, GROUND + TILE_SIZE,
         [(S3_X[0], WORKS_NORTH, S3_X[1], WORKS_NORTH + 2 * NICHE_DEPTH)], light=LIGHT_CLUE,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING)
    s3_panel = zone("s3_panel", GROUND, GROUND,
                    [(S3_X[0], WORKS_NORTH + 2 * NICHE_DEPTH, S3_X[1], WORKS_NORTH + 3 * NICHE_DEPTH)],
                    TAG_S3_PANEL, light=LIGHT_CLUE, flat=PLATE, wall=TUBBING)
    zone("s3_passage", GROUND, GROUND + TILE_SIZE,
         [(S3_X[0], WORKS_NORTH + 3 * NICHE_DEPTH, S3_X[1], 5712)], light=LIGHT_SECRET,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING)
    zone("s3_store", GROUND, GROUND + TILE_SIZE, [(3968, 5712, 4352, 5888)], light=LIGHT_SECRET,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING, special=SECTOR_SPECIAL_SECRET)
    for y in (WORKS_NORTH + 2 * NICHE_DEPTH, WORKS_NORTH + 3 * NICHE_DEPTH):
        g.style_h(y, S3_X[0], S3_X[1], secret_panel_style(TAG_S3_PANEL, s3_panel, TUBBING))
    # The red gate in the crater's containment wall, south of the works.
    rx1, rx2 = RED_GATE_X
    cy1, cy2 = CONTAINMENT_Y
    zone("z5_red_portal", GROUND, DOOR_HEIGHT, [(rx1, cy2 - 32, rx2, cy2)], light=LIGHT_BEACON,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING, extra=RED_LIGHT)
    red_door = door("z7_red_door", GROUND, TAG_RED_DOOR, (rx1, cy2 - 64, rx2, cy2 - 32),
                    light=LIGHT_PORCH)
    zone("z7_red_porch", GROUND, DOOR_HEIGHT, [(rx1, cy1, rx2, cy2 - 64)], light=LIGHT_PORCH,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING)
    # The works' two closets in the containment wall, either side of the gate.
    for name, (cx1, cx2) in CLOSETS.items():
        zone(f"{name}_door", GROUND, GROUND, [(cx1, cy2 - NICHE_DEPTH, cx2, cy2)], TAG_AMBUSH,
             light=LIGHT_CLOSET, wall=TUBBING)
        zone(name, GROUND, GROUND + CLOSET_HEIGHT, [(cx1, cy1 + 32, cx2, cy2 - NICHE_DEPTH)],
             light=LIGHT_CLOSET, flat=PLATE, wall=TUBBING)
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
    lava("z6_refinery", "z6_channel", CHANNEL)
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
    # The occupiers' two banners side by side on the refinery's brick (D12).
    fx1_, fy1f, fx2_, fy2f = FLAGS_RECESS
    zone("z6_flags", GROUND, GROUND + TILE_SIZE, [FLAGS_RECESS], light=LIGHT_REFINERY, flat=PLATE,
         ceiling=CEIL_CONCRETE, wall=BRICK)
    half = (fy1f + fy2f) // 2
    g.style_v(fx1_, fy1f, half, LineStyle(texture=FLAG_REICH))
    g.style_v(fx1_, half, fy2f, LineStyle(texture=FLAG_LEGION))

    # ======================================================================
    # Z7 The crater's rim, Z8 its terraces and floor, Z9 the control bunker
    # ======================================================================
    zone("z7_rim", GROUND, CRATER_SKY, [CRATER], light=LIGHT_CRATER, flat=BALLAST,
         ceiling=SKY, wall=TUBBING)
    x1, y1, x2, y2 = CRATER
    for k in range(1, TERRACES + 1):
        i = RIM + TERRACE * (k - 1)
        zone(f"z8_tier_{k}", GROUND - STEP * k, CRATER_SKY, [(x1 + i, y1 + i, x2 - i, y2 - i)],
             light=LIGHT_CRATER, flat=BALLAST, ceiling=SKY, wall=STEEL)
    i = RIM + TERRACE * TERRACES
    zone("z8_floor", CRATER_FLOOR, CRATER_SKY, [(x1 + i, y1 + i, x2 - i, y2 - i)],
         light=LIGHT_CRATER, flat=PLATE, ceiling=SKY, wall=STEEL)
    for n, rect in enumerate(CRATER_LAVA, start=1):
        lava("z8_floor", f"z8_lava_{n}", rect)
    for n, (px, py) in enumerate(PYLONS, start=1):
        prop("z8_floor", f"z8_pylon_{n}", [(px, py, px + PYLON_SIZE, py + PYLON_SIZE)], PYLON,
             wall=TUBBING, flat=PLATE)
    prop("z8_floor", "z8_portal_base", [PORTAL_BASE], PORTAL_PLINTH, wall=STEEL, flat=PLATE)
    prop("z8_floor", "z8_portal", [PORTAL_FIELD], PORTAL_TOP, wall=PORTAL, flat=PLATE,
         light=LIGHT_GLOW)
    # The control bunker under the south rim: the gate only the boss's death opens.
    ex1, ex2 = EXIT_X
    zone("z9_exit_porch", GROUND, DOOR_HEIGHT, [(ex1, y1 - 32, ex2, y1)], light=LIGHT_PORCH,
         flat=PLATE, ceiling=CEIL_CONCRETE, wall=TUBBING)
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

    # Things.
    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=BLUE_KEY_SPOT[0], y=BLUE_KEY_SPOT[1], type=ED_BLUE_CARD))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD))
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
WALL_TEXTURES = ((CONCRETE, STEEL, CRATE, LOCKER, TILE, TILE_DADO, TUBBING, BRICK, RUST, PORTAL,
                  FLAG_REICH, FLAG_LEGION, WAGON, ARMOUR_STAR, ARMOUR, SIGNAL, TURBINE, CONTROL,
                  LENIN, STALIN, MURAL) + DOOR_LEAVES + SWITCH_FACES
                 + ((MARX_ENGELS,) if MARX_ENGELS else ()))
FLAT_TEXTURES = (CRATE_TOP, LAB_FLOOR, CEIL_LAMP, CEIL_CONCRETE, PLATE, GRATING, MOLTEN, TRACK,
                 BALLAST, SKY)
