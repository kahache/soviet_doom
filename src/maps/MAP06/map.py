"""MAP06 "Red Square" (ÐšÑ€Ð°ÑÐ½Ð°Ñ Ð¿Ð»Ð¾Ñ‰Ð°Ð´ÑŒ), episode 2's last map - v1.

Design document: docs/levels/MAP06-red-square.md (section 4 is the plan,
section 5 the route, section 9 the population).
D104 (P4) opens episode 2, "The Road to Moscow": MAP04 the railway yard,
MAP05 the Volga dam, and this map, the episode's end. Moscow, November 1977,
days before the anniversary parade (SD_QUIT_04), held by the Fourth Reich
and the Liberty Legion. Sergeant Vilanova comes up out of the metro at
Ploshchad Revolyutsii, crosses Nikolskaya into the GUM, takes the square,
and goes through the Kremlin wall's Spasskaya gate to the episode's boss.

Built v1 straight away, MVP first (D60): the whole plan, textured with the
approved sets only, populated and stocked. v1.1 (2026-10-22) dresses it in
episode 2's Moscow set (D107): the square's setts with granite lines, the
Kremlin wall's brick with its swallowtail merlons against the sky, the GUM's
facade, the tribunes' and the mausoleum's granite, the Spasskaya's stone,
the parade banners on the wall, armour plate on the parade's vehicles.
Round 2 (D113) adds the GUM's shopfronts and glass vault, the Spasskaya's
clock and ruby star, the museum's brick, the crown's flags on the Kremlin's
brick and the blue leaf, under Moscow's night sky. What is still a stand-in
is listed under "Pending textures" in the design document.

The route, in one line: the station's hall (statues in its arches) ->
escalator -> the street pavilion -> Nikolskaya street -> the GUM's north
hall (the BLUE door seen down the arcade; the BLUE KEY seen on the bridge
over the glass-roofed line) -> round by the arcade and the atrium, up the
gallery stair, onto the bridge, the BLUE KEY -> the blue door -> Red Square
(the RED gate in the Kremlin wall, the YELLOW gatehouse at the south end and
the YELLOW KEY on the north reviewing stand, all seen from the blue door) ->
up the stand, the YELLOW KEY -> the yellow gatehouse -> the vehicle park on
the slope, the RED KEY (taking it opens the museum's closets behind the
player) -> back across the square to the Spasskaya gate, the red door -> the
Kremlin courtyard, the boss -> his death opens the exit gate -> the exit.

Three things this map does that earlier maps did not, each flagged in the
design document for the PM's engine pass (D26: this role never starts
GZDoom):

* open air at several sky heights: the square's sky (ceiling F_SKY1) sits at
  the GUM facade's height; the Kremlin wall is a closed sky block (floor =
  ceiling) with a walk 32 deep in front of it, open to the sky from
  WALL_WALK to MERLON_TOP, and the line between the walk and the square wears
  the masked SDKREM2 as its middle texture, so the swallowtail merlons stand
  against the sky; the Spasskaya tower rises in two closed sky blocks and
  its tent, open to the sky with the ruby star on it, inside an apron whose
  sky is higher (Doom's sky hack: no upper texture is drawn between two sky
  ceilings). NOT VERIFIED in engine;
* the exit depends on a death: the boss's thing carries Door_Open on
  TAG_BOSS_EXIT (MAP03 v1.1's thing special, D68), and NO line carries that
  tag. The boss stands at MAP06_BOSS_SPOT; he is the Liberty Colossus
  (BOSS_KIND, D116; the General stood in until then), the class named in
  one place;
* a key that springs an ambush: the red key's thing carries Door_Open on
  TAG_AMBUSH, run when it is picked up (Hexen-style item special), which
  opens two closets in the museum's wall on the square behind the player.
  NOT VERIFIED in engine; if it does not fire the closets stay shut and
  nothing is lost but the fight.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP06 SKILL=3 tools/run.sh
"""

from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path

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

MAP_NAME = "MAP06"


def _load_pickup_events():
    """Episode 2's pickup events (src/maps/common/pickup_events_e2.py): the
    verified specials and the helpers MAP04, MAP05 and MAP06 share. Loaded by
    path, as the build loads this file."""
    path = Path(__file__).resolve().parents[1] / "common" / "pickup_events_e2.py"
    spec = importlib.util.spec_from_file_location("sd_pickup_events_e2", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVENTS = _load_pickup_events()

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# Soviet base (batch 1-3)
CONCRETE = "SDCONC1"    # 64x128 pale prefab panels: Nikolskaya's other houses, the gatehouse, the park
STEEL = "SDSTEL1"       # military-green riveted plate: door jambs, the street's truck, the tower's tent
CRATE = "SDCRAT1"       # 64x64 crate face: looted stock in the shops, S2's wall of crates
LONG_CRATE = "SDCRAT2"  # 128x64 long crate: the street's barricades
CRATE_TOP = "SDCRTOP1"
FLOOR_ASPHALT = "SDFLR2"    # plain concrete: the street and the vehicle park (asphalt, stand-in)
CEIL_CONCRETE = "SDCEIL2"
EXIT_FACE = "SDSW1D"    # the hazard panel every map's exit wears
# Metro (batch 2, D42, D48)
TILE = "SDTILE1"        # glazed cream tile: the escalator, the GUM's shops
MARBLE = "SDMARB1"      # red marble: the station's hall, the fountain, the courtyard's dais
STATION_WALL = "SDMARB2"    # tile over red marble with a brass rail: platforms, the GUM's halls
MOSAIC = "SDMOSA1"      # 128x128 cobalt star mosaic: the blue lock's frame (MAP02's), S1's row
BRASS = "SDBRAS1"       # 64x128 brass pilaster: the bronze statues, Minin and Pozharsky, the Tsar Bell
TUBBING = "SDTUBB1"     # 128x128 cast-iron tubbing: the track walls
PLATFORM_FACE = "SDMEDG1"   # 64x64 platform face: the edge towards the track
GRANITE = "SDMFLR1"     # grey granite: the arcade, thresholds, the stands, the monuments' tops
GRANITE_CHECK = "SDMFLR2"   # checker granite: the station hall, the GUM's floors
PLATFORM_EDGE = "SDMFLR3"   # platform edge from above, lip on row 63 (rotated per side)
RAILS = "SDRAIL1"       # track bed, rails along the image's y (turned a quarter)
CEIL_COFFER = "SDMCEIL1"    # whitewashed coffer: the GUM's halls and shops
CEIL_LAMP = "SDMCEIL2"      # coffer with a brass ring lamp: the station hall
# Tankograd (batch 4, D66): the Kremlin is red brick
BRICK = "SDBRCK1"       # 64x128 red brick: the courtyard's palaces (the flags' ground), S3's yard
BRICK_DADO = "SDBRCK2"  # the same brick whitewashed to 64: the parapet over the slope
DOOR_YELLOW = "SDDOORY"     # the yellow gatehouse's leaf
DOOR_RED = "SDDOORR"        # the Spasskaya gate's leaf
GATE = "SDGATE1"        # 128x128 shut sliding gate: courtyard gates, the exit gate, the GUM's south gate
FLAG_USSR = "SDFLAG1"      # the USSR state flag on SDBRCK1 (D119; the Reich's banner before): the courtyard's pair
FLAG_STANDARD = "SDFLAG2"  # a Red Army standard on SDBRCK1 (D119; the Legion's banner before): the courtyard's pair
PLATE = "SDFLR4"        # 64x64 chequer plate: the parade vehicles' decks
# Episode 2, Moscow (D107): Red Square and the Kremlin
COBBLES = "SDCOBL1"     # flat: the square's dark setts, the Kremlin courtyard
COBBLES_LINE = "SDCOBL2"    # flat: the setts with a line of pale granite slabs along x
KREMLIN = "SDKREM1"     # 64x128 the Kremlin wall's red brick
MERLON = "SDKREM2"      # 64x128 masked: SDKREM1's brick cut to a swallowtail in its top half
GUM_FACADE = "SDGUM1"   # 128x128 one bay of the GUM's facade: an arched window, a cornice
TRIBUNE = "SDTRIB1"     # 64x128 dark red granite, a black labradorite band on top
BANNER = "SDBANR1"      # 64x128 a parade banner hung on SDKREM1's brick
SPASSKAYA = "SDSPAS1"   # 64x128 the tower's brick and white stone, its frieze on top
# Episode 2, railway (D107): the armoured train's plate dresses the parade
ARMOUR_STAR = "SDARMR1"     # 128x128 armour plate with a red star: the missile carriers' flanks
ARMOUR = "SDARMR2"      # 64x128 the same plate without the star: every other vehicle face
# Episode 2, Moscow, round 2 (D113, approved 2026-10-22; design section 8)
DOOR_BLUE = "SDDOORB"   # 128x128 the blue lock's leaf (between the metro's cobalt mosaics)
CLOCK = "SDCLOK1"       # 128x128 the Spasskaya's clock face: one on each face of the clock stage
RUBY_STAR = "SDRUBY1"   # 128x128 MASKED: the ruby star on its spire, against the sky
# The GUM's shopfronts (64x128): the same front with three signs, «ТКАНИ»,
# «ОБУВЬ», «ЧАСЫ», one shop to each 64 of wall, in turn along the line.
SHOPFRONTS = ("SDGUMS1", "SDGUMS2", "SDGUMS3")
SHOPFRONT = SHOPFRONTS[0]   # what the line's walls are built in; dress_shopfronts deals the signs
SHOPFRONT_WIDTH = 64
GLASS_ROOF = "SDGUMR1"  # flat: the GUM's glass vault from below, over the line, the atrium, the gallery
MUSEUM = "SDMUSE1"      # 64x128 the Historical Museum's brick and white dressings: its wall, the Resurrection gate
FLAG_GONFALON_KREMLIN = "SDFLAG3"  # a parade gonfalon on the Kremlin's SDKREM1 (D119): the wall's crown
FLAG_TORN_KREMLIN = "SDFLAG4"      # the USSR flag after the battle, torn, on SDKREM1 (D119): the wall's crown
# The engine's sky marker (check_pk3 BUILTIN_TEXTURE_NAMES); MAPINFO's sky1
# says which picture: SDSKY2, Moscow at night (D113).
SKY = "F_SKY1"

# The approved posters (CEO 2026-10-22: Â«que esos posters puedan aparecer en
# cualquier nivelÂ»; tests/test_posters.py). Lenin and Stalin are 128x256.
LENIN = "SDPOSTR1"
STALIN = "SDPOSTR3"
MURAL = "SDPOSTR2"      # 128x128; not hung here (no 128-high wall on the route fits it)
POSTER_WIDTH = 128
POSTER_HEIGHT = 256
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS

DOOR_LEAVES = (DOOR_BLUE, DOOR_YELLOW, DOOR_RED, GATE)
SWITCH_FACES = (EXIT_FACE,)
SWITCH_HEIGHT = 128     # SDSW1D is 64x128
TILE_SIZE = 128         # every leaf, mosaic, gate and star plaque is 128 square

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED on MAP02
# and MAP03; delay 0 opens it for good. Lock numbers from gzdoom.pk3
# lockdefs.txt (MAP02, MAP03): 1 red card, 2 blue card, 3 yellow card.
SPECIAL_DOOR_LOCKED_RAISE = 13
LOCK_RED_CARD = 1
LOCK_BLUE_CARD = 2
LOCK_YELLOW_CARD = 3
# Doom's editor numbers; SD_BluePass, SD_YellowPass and SD_RedPass replace them.
ED_BLUE_CARD = 5
ED_YELLOW_CARD = 6
ED_RED_CARD = 13
KEY_LOCKS = {ED_BLUE_CARD: LOCK_BLUE_CARD, ED_YELLOW_CARD: LOCK_YELLOW_CARD,
             ED_RED_CARD: LOCK_RED_CARD}
ED_PLAYER1_START = 1

# --- Heights ----------------------------------------------------------------
GROUND = 0              # the street, the GUM's ground floor, the square, the Kremlin
METRO = -128            # the station: eight escalator steps under the street
METRO_CEIL = METRO + 192
TRACK = METRO - 16      # the track bed: one step down from the platform
GALLERY = 128           # the GUM's upper floor: galleries, bridge, upper shops
STEP = 16               # every stair step; under MAX_STEP_UP 24
STEP_DEPTH = 32
DOOR_HEIGHT = 128       # every leaf is one tile high
NICHE_DEPTH = 16
CLOSET_HEIGHT = 128
STATUE = 96             # a bronze figure on the station's arches
CRATES = 64             # a stack of SDCRAT1 / SDCRAT2: one tile, not a step
SHOP_CEIL = 160         # a shop: room over its crates for any body (heavy Panzermensch 72)
VEHICLE_HULL = 48       # a tank's or a lorry's deck
VEHICLE_TURRET = 80
CARRIER_HULL = 64       # the missile carrier
CARRIER_MISSILE = 96
BARRICADE = 64          # crates across a gate or a street: not climbable (step 24)
WINDOW_SILL = 112       # the GUM's facade windows: a slit 48 high, seen through, never passed
WINDOW_HEAD = 160
# The square's skies. Each one-sided wall shows as high as the sky of the
# sector it bounds; two sky ceilings side by side draw no wall between them.
SQUARE_SKY = 384        # the GUM's facade and the museum: three storeys, three bays of SDGUM1
STREET_SKY = SQUARE_SKY     # the GUM's north facade on Nikolskaya: the same three bays
PASSAGE_SKY = 448       # the GUM's glass roof (SDGUMR1) over its line, the atrium and the gallery
# The Kremlin wall: a body (closed sky block) at WALL_WALK and, on its open
# side, a walk WALL_WALK_DEPTH deep open to the sky up to MERLON_TOP. The
# line between the walk and the square wears MERLON as its middle texture:
# one tile, pegged to the walk's sky, its solid lower half the parapet and
# its upper half the swallowtails. The face below the walk is one tile of
# KREMLIN, so a BANNER hangs on it whole.
WALL_WALK = TILE_SIZE   # 128
MERLON_TOP = WALL_WALK + TILE_SIZE      # 256: the merlons' tips
WALL_WALK_DEPTH = 32
GATE_APRON_SKY = MERLON_TOP     # in front of the Spasskaya gate: the wall's own height over its arch
TOWER_APRON_SKY = 768   # round the tower: high enough to show its three stages
TOWER_BASE = 448
TOWER_STAGE = TOWER_BASE + TILE_SIZE    # 576: the clock stage (SDCLOK1 on each face)
TOWER_SPIRE = TOWER_STAGE + TILE_SIZE   # 704: the green tent
# The ruby star (SDRUBY1, masked) stands on the tent: the middle texture of
# the line that halves the tent's top (x RUBY_STAR_X), the tent open to the
# apron's sky so the star has the room between its top and that sky. The
# tent is 64 wide and the star 128: drawn at half scale (UDMF scalex_mid /
# scaley_mid 2: NOT VERIFIED in the engine), it is 64 x 64, its stem on the
# tent and its tips at the apron's sky.
RUBY_STAR_X = 1728
RUBY_STAR_SCALE = 2.0
PARAPET = 128           # the stone parapet over the slope: seen over, not climbed
FLAG_SILL = MERLON_TOP - TILE_SIZE      # 128: a flag hung in the crown, one tile
ARENA_SKY = 512
YARD_SKY = 256
MAUSOLEUM = (64, 112, 144)  # its three granite tiers (a prop: never walked, never fought on)
STAND_TOP = 128             # the reviewing stands: 7 steps of 16 and a top row
MININ_PLINTH = 64
MININ_BRONZE = 160
FOUNTAIN_RIM = 32
FOUNTAIN_SPOUT = 96
BELL = 128
CANNON = 64
DAIS = 16

# --- Light ---------------------------------------------------------------------
# 192 is spent on the three locks, the three keys and the exit, nowhere else.
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_HALL = 144
LIGHT_PLATFORM = 128
LIGHT_TRACK = 112
LIGHT_ESCALATOR = 128
LIGHT_PAVILION = 128
LIGHT_STREET = 112      # night, November
LIGHT_GUM = 128
LIGHT_SHOP = 112        # looted, dark
LIGHT_PASSAGE = 144
LIGHT_ATRIUM = 160
LIGHT_GALLERY = 144
LIGHT_SQUARE = 144      # floodlit for the parade
LIGHT_PARK = 128
LIGHT_PASSAGE_GATE = 112
LIGHT_ARENA = 144
LIGHT_EXIT_HALL = 128
LIGHT_CLOSET = 112
LIGHT_SECRET = 112
LIGHT_CLUE = LIGHT_MIN  # the odd one out of a row: in shadow (MAP03 v1.1's clue)
BEACON_ZONES = ("z6_blue_portal", "z4_blue_band", "z5_bridge_key", "z6_yellow_portal",
                "z6_tribune_n_top", "z6_red_portal", "z7_pedestal", "z10_exit_niche")

# The keys' colours, in light (sector `lightcolor`, as MAP02 and MAP03): each
# lock and the place its key lies wear the same colour, nothing else does.
BLUE = 0x90A8FF         # MAP02's PASS_BLUE
YELLOW = 0xFFD860       # MAP03's
RED = 0xFF6048          # MAP03's
BLUE_LIGHT = {"lightcolor": BLUE}
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_S1_PANEL = 1        # the station's mosaic row: the one set back in shadow
TAG_S2_PANEL = 2        # the GUM's upper shop whose back wall is crates
TAG_S3_PANEL = 3        # Nikolskaya: the courtyard gate set back deeper and darker
TAG_BLUE_DOOR = 4       # the GUM's doors onto the square: Door_LockedRaise, lock 2
TAG_YELLOW_DOOR = 5     # the gatehouse to the vehicle park: lock 3
TAG_RED_DOOR = 6        # the Spasskaya gate: lock 1
TAG_AMBUSH = 10         # the museum's two closets; ONLY the red key's pickup opens it
TAG_BOSS_EXIT = 12      # the exit gate; ONLY the boss's death opens it (no line carries it)
TAG_RESURRECTION = 13   # V3 (A3): the Resurrection gate's barricades and the reserve's gate; ONLY the yellow key
# The tags only a pickup opens (no line carries any of them).
PICKUP_TAGS = (TAG_AMBUSH, TAG_RESURRECTION)
# Sectors whose FLOOR a pickup lowers for good (MAP04's LIFT_TAGS): the tests
# open them by laying the floor on the lowest neighbour's.
LIFT_TAGS = (TAG_RESURRECTION,)
SECRET_PANEL_TAGS = (TAG_S1_PANEL, TAG_S2_PANEL, TAG_S3_PANEL)

# --- The boss --------------------------------------------------------------------
# Episode 2's boss is the Liberty Colossus (D104, in the mod since D116;
# docs/engine/2026-10-22_P4_ep2-enemies.md section 3), who replaced the
# General's stand-in here. Radius 44 / height 110: the dais's top (128 x 128)
# holds him, the courtyard's sky (ARENA_SKY) is far over him. The spot, the
# facing and the death special did not change with him.
MAP06_BOSS_SPOT = (960, 1536)   # on the dais in the Kremlin courtyard, facing the gate
BOSS_ANGLE = 0
BOSS_KIND = "colossus"
BOSS_DEATH_SPECIAL = (SPECIAL_DOOR_OPEN, (TAG_BOSS_EXIT, DOOR_SPEED_SLOW, 0, 0, 0))
RED_KEY_SPECIAL = (SPECIAL_DOOR_OPEN, (TAG_AMBUSH, DOOR_SPEED_SLOW, 0, 0, 0))
# V3 (A3, D119/D120), the map's set piece: the barriers come down. Taking the
# yellow key on the north stand, the crates barricading the Resurrection
# gate's two arches sink into the setts and, across Nikolskaya, the reserve
# courtyard's gate sinks with them (one Floor_LowerToLowest on one tag, no
# rider): the Reich's reserve marches out of its courtyard, straight down
# through the first arch and onto the square, behind the player as he goes
# south to the yellow gatehouse. Warned: both barricades are in sight of the
# key's spot and grind as they sink (tested); the wave has 450 units of
# street and the square's width to cross. Never in the way: the arches open
# a loop back onto Nikolskaya (already taken), the courtyard is a dead end,
# and nothing the route needs is behind either (tested).
SPECIAL_FLOOR_LOWER_TO_LOWEST = EVENTS.FLOOR_LOWER_TO_LOWEST
BARRIER_SPEED = EVENTS.FLOOR_SPEED_FAST   # 4 units a tic: the crates in 16 tics, the gate in 32
YELLOW_KEY_SPECIAL = (SPECIAL_FLOOR_LOWER_TO_LOWEST, (TAG_RESURRECTION, BARRIER_SPEED, 0, 0, 0))
PICKUP_SPECIALS = {ED_YELLOW_CARD: YELLOW_KEY_SPECIAL, ED_RED_CARD: RED_KEY_SPECIAL}

# --- Things --------------------------------------------------------------------
PLAYER_START = (5216, 4864)
PLAYER_ANGLE = 180      # facing west, down the station's hall
BLUE_KEY_SPOT = (4096, 2984)    # on the GUM's bridge, 24 back from its north edge
YELLOW_KEY_SPOT = (1712, 2784)  # on the top row of the north reviewing stand
RED_KEY_SPOT = (2176, 704)      # on the command post's plinth in the vehicle park
KEY_ZONES = {ED_BLUE_CARD: "z5_bridge_key", ED_YELLOW_CARD: "z6_tribune_n_top",
             ED_RED_CARD: "z7_pedestal"}
LOCK_PORTALS = {LOCK_BLUE_CARD: "z6_blue_portal", LOCK_YELLOW_CARD: "z6_yellow_portal",
                LOCK_RED_CARD: "z6_red_portal"}

# Zone-name families the tests use.
PROP_PREFIX = "prop_"           # unwalkable by design
SECRET_ZONES = ("s1_store", "s2_store", "s3_yard")
CLOSET_PREFIX = "closet_"
EXIT_ZONES = ("z10_hall", "z10_exit_niche")     # behind the boss's gate

# --- Plan (design document section 4) ----------------------------------------
# The station (Ploshchad Revolyutsii): a hall between two arcades, four arches
# a side, two bronze figures crouched in each arch, platforms and tracks behind.
HALL = (4096, 4736, 5376, 4992)
ARCHES_X = (4224, 4480, 4736, 4992)
ARCH_WIDTH = 128
ARCH_ROWS = {"s": (4672, 4736), "n": (4992, 5056)}
STATUE_SIZE = 32
ESCALATOR = (3840, 4800, 4096, 4928)    # 8 steps, rising west
PAVILION = (3520, 4160, 3840, 4992)
PAVILION_DOOR = (3584, 4096, 3776, 4160)
STREET = (2816, 3648, 4352, 4096)
STREET_GATES_X = (3008, 3264, 4032)     # three courtyard gates; the middle one is S3
# The Resurrection gate's two arches, barricaded: the square seen, not reached
# (until V3's yellow key brings the barricades down).
RESURRECTION_ARCHES_X = (2816, 3008)
# V3 (A3): the Reich's reserve, in a courtyard behind a gate in Nikolskaya's
# north wall, straight up the street from the first arch: a recess one tile
# high like the street's other gates, the gate (a sector the yellow key's
# special lowers) at its back, the courtyard behind, open to the sky.
RESERVE_RECESS = (2816, 4096, 2944, 4112)
RESERVE_GATE = (2816, 4112, 2944, 4128)
RESERVE = (2752, 4128, 2976, 4336)
# The GUM: the facade (x 3456-3520), the arcade, a row of shops, the line
# under its glass roof, the east gallery upstairs, the upper shops.
GUM_NORTH = (3520, 3328, 4352, 3584)
GUM_SOUTH = (3520, 1152, 4352, 1408)
ARCADE = (3520, 1408, 3776, 3328)
ARCADE_PILLARS_Y = (1600, 1920, 2752, 3072)
FACADE_WINDOWS_Y = (1600, 1920, 2752, 3072)
PASSAGE_S = (3968, 1408, 4224, 2944)
PASSAGE_N = (3968, 3008, 4224, 3328)
BRIDGE = (3968, 2944, 4224, 3008)
BRIDGE_KEY = (4032, 2944, 4160, 3008)
ATRIUM = (3808, 2176, 4352, 2496)
UPPER_WEST = (3808, 2880, 3968, 3072)
GALLERY_N = (4224, 2752, 4352, 3264)
GALLERY_S = (4224, 1536, 4352, 1920)
# The square: the Kremlin wall at x 1600-1664, the GUM's facade at x 3456.
SQUARE = (1664, 1152, 3456, 3456)
KREMLIN_STRIP_X = (1600, 1664)
ARENA_STRIP_X = (1344, 1408)
TOWER = (1600, 1216, 1856, 1408)
TOWER_MID = (1664, 1248, 1792, 1376)
TOWER_TOP = (1696, 1280, 1760, 1344)
GATE_Y = (1472, 1600)           # the Spasskaya gate's passage, north of the tower
TRIBUNE_N_Y = (2560, 3008)
TRIBUNE_S_Y = (1856, 2112)
TRIBUNE_X = (1664, 1984)        # a top row 96 deep, then 7 steps of 32 down to the square
TRIBUNE_TOP_DEPTH = 96
FLAGS_ON_THE_WALL = ((3136, FLAG_GONFALON_KREMLIN), (3264, FLAG_TORN_KREMLIN))
FLAG_WIDTH = 64
# The square's floor: dark setts, crossed by three lines of pale granite slabs
# (SDCOBL2, one line per 64 tile), each a strip of its own sector one tile
# deep on the flat grid. They cross where no thing stands (tested).
SQUARE_LINES_Y = (1728, 2240, 2816)
SQUARE_LINE_DEPTH = 64
# The parade banners (SDBANR1) on the Kremlin wall's face, each one 64 span of
# it, whole: two by the Spasskaya gate, one either side of the mausoleum, two
# at the north end. None under the crown's flags.
BANNERS_Y = (1664, 1792, 2112, 2432, 3008, 3392)
BANNER_WIDTH = 64
# World-aligned textures: {lump: the height their tile rows count from}. Their
# columns run with the world's x or y and their rows from that height, so the
# brick, the bays and the frieze run on unbroken from one line to the next.
ALIGN_PERIOD = 128      # every aligned lump is 128 high and 64 or 128 wide
ALIGNED = {KREMLIN: 0, MERLON: 0, BANNER: 0, GUM_FACADE: 0, SPASSKAYA: TOWER_BASE,
           FLAG_GONFALON_KREMLIN: 0, FLAG_TORN_KREMLIN: 0, MUSEUM: 0}
# The missile carriers' flanks: SDARMR1 with its star (rows 29-88, measured on
# the approved lump) whole on a 64-high hull, one star per 128.
STAR_ROWS = (29, 88)
STAR_OFFSET = 28
# The parade, halted where it was staged (design section 4.4): (name, hull, deck
# height, top piece, top height). Every one stands clear of the sight lines from
# the blue door to the three things the square must show (tested).
VEHICLES = (
    ("w1", (2240, 3072, 2336, 3264), VEHICLE_HULL, (2256, 3136, 2320, 3200), VEHICLE_TURRET),
    ("w2", (2240, 2176, 2336, 2560), CARRIER_HULL, (2272, 2208, 2304, 2528), CARRIER_MISSILE),
    ("w3", (2240, 1344, 2336, 1536), VEHICLE_HULL, (2256, 1408, 2320, 1472), VEHICLE_TURRET),
    ("m1", (2560, 2176, 2656, 2368), VEHICLE_HULL, None, None),
    ("m2", (2560, 1344, 2656, 1536), VEHICLE_HULL, None, None),
    ("e1", (2880, 2880, 2976, 3072), VEHICLE_HULL, (2896, 2944, 2960, 3008), VEHICLE_TURRET),
    ("e2", (2880, 1664, 2976, 2048), CARRIER_HULL, (2912, 1696, 2944, 2016), CARRIER_MISSILE),
    ("e3", (2880, 2560, 2976, 2752), VEHICLE_HULL, (2896, 2624, 2960, 2688), VEHICLE_TURRET),
    # The vehicle park on the slope.
    ("p1", (1856, 640, 1952, 832), VEHICLE_HULL, (1872, 704, 1936, 768), VEHICLE_TURRET),
    ("p2", (2432, 512, 2528, 768), CARRIER_HULL, (2464, 544, 2496, 736), CARRIER_MISSILE),
    ("p3", (2688, 704, 2784, 896), VEHICLE_HULL, None, None),
)
# The parade portraits on the GUM's facade, either side of its doors onto the
# square (design section 7.1): each hangs in a niche NICHE_DEPTH deep, raised
# PORTRAIT_SILL over the cobbles and exactly POSTER_HEIGHT tall, so the poster
# is whole and the facade shows above and below it. Floor 64: not a step.
PORTRAIT_SILL = 64
PORTRAIT_NICHES = {"lenin": (2496, 2624), "stalin": (2112, 2240)}     # y spans, facade x 3456
# The Kremlin courtyard's north wall: two Soviet flags (D119; the occupiers'
# banners until then) hang between Stalin and the Marx-Engels slot, each
# picture in a recess a poster high, among the portraits.
COURTYARD_PORTRAITS = {"stalin": (1024, 1152), "slot": (576, 704)}    # x spans, arena y 2048
# Every picture on the map: (name, texture, axis, coord, lo, hi), the segment
# one GridMap style paints. The slots wear Marx (the GUM) and Engels (the Kremlin).
POSTERS = (
    # The GUM's north hall: Lenin faces the player coming in from Nikolskaya,
    # beside the way on under the glass roof; the slot on the hall's east wall.
    ("gum_north_lenin", LENIN, "h", 3328, 3808, 3936),
    ("gum_north_slot", MARX, "v", 4352, 3392, 3520),
    # Red Square: the parade portraits on the GUM's facade.
    ("square_facade_lenin", LENIN, "v", 3456 + NICHE_DEPTH, *PORTRAIT_NICHES["lenin"]),
    ("square_facade_stalin", STALIN, "v", 3456 + NICHE_DEPTH, *PORTRAIT_NICHES["stalin"]),
    # The Kremlin courtyard, the boss's room.
    ("courtyard_stalin", STALIN, "h", 2048 + NICHE_DEPTH, *COURTYARD_PORTRAITS["stalin"]),
    ("courtyard_slot", ENGELS, "h", 2048 + NICHE_DEPTH, *COURTYARD_PORTRAITS["slot"]),
)
POSTER_SLOTS_MARX_ENGELS = ("gum_north_slot", "courtyard_slot")   # Marx, Engels


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS


CLOSETS = {"closet_z6_w": (1920, 2112), "closet_z6_e": (2304, 2496)}    # x spans, museum wall
MUSEUM_X = (1664, 2752)
PARK = (1664, 448, 2944, 1088)
GATEHOUSE = (2560, 2944)        # x span of the yellow gatehouse, y 1088-1152
YELLOW_GATE_X = (2688, 2816)
ARENA = (512, 768, 1344, 2048)
ARENA_COLUMNS = ((640, 1088), (1184, 1216), (1184, 1792), (576, 1664))
EXIT_Y = (1472, 1600)


# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich, 20 HP
ED_TROOPER = 21101        # SD_LegionTrooper, Legion, 30 HP
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both factions, 60 HP
ED_HOUND = 21103          # SD_ReichHound, Reich, 150 HP
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, 400 HP
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich, 500 HP
ED_PANZER_HEAVY = 21107   # SD_PanzermenschSchwer, Reich, 1000 HP
ED_GUNNER = 21110         # SD_LegionGunner, Legion, 80 HP: bursts of hitscan; drops 15 AKM rounds (D116)
ED_COLOSSUS = 21111       # SD_LibertyColossus, Legion, 4500 HP: episode 2's boss (D116)
MONSTER_KINDS = {
    "rifleman": ED_RIFLEMAN,
    "trooper": ED_TROOPER,
    "stormtrooper": ED_STORMTROOPER,
    "hound": ED_HOUND,
    "doughboy": ED_DOUGHBOY,
    "panzermensch": ED_PANZERMENSCH,
    "heavy": ED_PANZER_HEAVY,
    "gunner": ED_GUNNER,
    "colossus": ED_COLOSSUS,
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
    ED_COLOSSUS: "SD_LibertyColossus",
}
REICH = ("rifleman", "hound", "panzermensch", "heavy")
LEGION = ("trooper", "doughboy", "gunner", "colossus")
# Where each faction stands (D35's grammar, D104's Moscow): the Reich holds
# the station, the street and the slope (the military occupation); the
# Legion holds the GUM (capital, in the department store) and its
# counter-attack in the museum; both hold the square (the Reich's parade
# guard, the Legion's Doughboys over it) and both stand round the boss.
# Stormtroopers are hybrids and stand anywhere.
REICH_GROUND = ("z1_", "z3_", "z7_")
LEGION_GROUND = ("z2_", "z4_", "z5_", "closet_")
BOTH_GROUND = ("z6_", "z8_", "z9_")
# The arsenal (MAPINFO DoomEdNums, 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # in S2 only, never on the route (MAP03's S1, Doom's BFG tradition)
# Ammo, health and armour: Doom's numbers, replaced by our classes (MOD-SPEC 6.4).
ED_CLIP = 2007            # 10 rounds
ED_CLIP_BOX = 2048        # 50
ED_SHELLS = 2008          # 4
ED_SHELL_BOX = 2049       # 20
ED_ROCKET = 2010          # 1 PG-7V
ED_ROCKET_BOX = 2046      # 5
ED_CELL = 2047            # 20 fuel
ED_CELL_PACK = 17         # 100 fuel
ED_AKM_AMMO = 21020       # SD_AkmAmmo, one 30-round 7.62x39 magazine (D116, ADR 011)
ED_BACKPACK = 8           # SD_Backpack
ED_STIMPACK = 2011
ED_MEDIKIT = 2012
ED_HEALTH_BONUS = 2014
ED_ARMOR_BONUS = 2015
ED_GREEN_ARMOR = 2018
ED_BLUE_ARMOR = 2019

# Design section 9: monsters per skill, Doom's skill pairs (udmf.skill_tier).
ENEMY_TOTALS = {2: 42, 3: 69, 4: 98}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Facing: 0
# east, 90 north, 180 west, 270 south; most face where the player comes from.
MONSTERS = (
    # The station: a Reich picket on the platforms, facing the start.
    # The hall's first rifleman 830 down the hall, seen but past the safe
    # distance (tests/test_safe_starts.py; at 4600 he was 616 off).
    ("z1_hall", "rifleman", 4384, 4896, 0, 2),
    ("z1_plat_s", "rifleman", 4400, 4576, 0, 2),
    ("z1_plat_n", "rifleman", 4800, 5156, 0, 2),
    ("z1_hall", "rifleman", 4300, 4816, 0, 3),
    ("z1_plat_n", "rifleman", 4300, 5136, 0, 3),
    ("z1_plat_s", "stormtrooper", 4700, 4576, 0, 4),
    ("z1_hall", "rifleman", 4200, 4936, 0, 4),
    # The street pavilion: the Legion's door-watch, facing the escalator.
    ("z2_pavilion", "trooper", 3680, 4300, 0, 2),
    ("z2_pavilion", "trooper", 3600, 4600, 0, 3),
    ("z2_pavilion", "stormtrooper", 3720, 4250, 0, 4),
    # Nikolskaya: the Reich's checkpoint, facing the pavilion's door.
    ("z3_street", "rifleman", 3200, 3720, 90, 2),
    ("z3_street", "rifleman", 3600, 3700, 90, 2),
    ("z3_street", "rifleman", 4200, 3800, 90, 2),
    ("z3_street", "stormtrooper", 3000, 3720, 0, 2),
    ("z3_street", "hound", 3400, 3950, 90, 2),
    ("z3_street", "rifleman", 2900, 4000, 0, 3),
    ("z3_street", "rifleman", 4250, 4000, 180, 3),
    ("z3_street", "stormtrooper", 3800, 3700, 90, 3),
    ("z3_street", "hound", 3100, 4000, 0, 4),
    ("z3_street", "stormtrooper", 4100, 3700, 90, 4),
    ("z3_street", "rifleman", 2880, 3700, 0, 4),
    # The GUM's ground floor: the Legion in the shop of the nation.
    ("z4_north", "trooper", 3700, 3450, 90, 2),
    ("z4_north", "trooper", 4250, 3420, 90, 2),
    # The Legion gunner (D116) down the arcade's length, the GUM's long line.
    ("z4_arcade", "gunner", 3600, 2900, 90, 2),
    ("z4_shop_c", "stormtrooper", 3872, 2688, 0, 2),
    ("z4_south", "trooper", 3800, 1280, 90, 2),
    ("z4_north", "stormtrooper", 3900, 3400, 90, 3),
    ("z4_arcade", "trooper", 3600, 1700, 90, 3),
    ("z4_shop_b", "trooper", 3872, 1984, 180, 3),
    ("z4_arcade", "doughboy", 3620, 2650, 90, 4),
    ("z4_south", "trooper", 4100, 1250, 90, 4),
    ("z4_south", "trooper", 3650, 1250, 0, 4),
    # Upstairs and under the glass roof: snipers on the gallery, a Doughboy
    # floating over the line.
    ("z5_gallery_n", "trooper", 4288, 3100, 180, 2),
    ("z5_gallery_s", "gunner", 4288, 1700, 180, 2),    # D116: along the gallery
    ("z5_atrium", "stormtrooper", 3900, 2300, 90, 2),
    ("z5_passage_s", "doughboy", 4096, 1800, 90, 2),
    ("z5_upper_w", "trooper", 3870, 2920, 0, 3),
    ("z5_passage_n", "stormtrooper", 4170, 3150, 270, 3),
    ("z5_atrium", "doughboy", 4280, 2350, 180, 4),
    ("z5_shop_u1", "trooper", 4500, 2900, 180, 4),
    ("z5_shop_u3", "stormtrooper", 4500, 1700, 180, 4),
    # V3 (A3): the reserve, behind the courtyard gate the yellow key brings
    # down: five of the square's guard moved out (from 2700 3200, 3150 3300,
    # 2600 3000, 2800 3350, 3300 3100), so the square they come back to is
    # the one the player has half cleared. The Reich's, as Nikolskaya.
    ("z3_reserve", "rifleman", 2816, 4192, 270, 2),
    ("z3_reserve", "rifleman", 2912, 4192, 270, 3),
    ("z3_reserve", "hound", 2864, 4272, 270, 3),
    ("z3_reserve", "rifleman", 2800, 4288, 270, 4),
    ("z3_reserve", "stormtrooper", 2928, 4288, 270, 4),
    # Red Square: the parade's guard, the episode's open battle, facing the
    # GUM's doors.
    ("z6_square", "rifleman", 3100, 2900, 0, 2),
    ("z6_square", "rifleman", 3100, 1800, 0, 2),
    ("z6_square", "rifleman", 2600, 1700, 0, 2),
    ("z6_square", "rifleman", 2060, 2620, 0, 2),
    ("z6_square", "rifleman", 2100, 1500, 0, 2),
    ("z6_square", "stormtrooper", 2750, 2400, 0, 2),
    ("z6_square", "stormtrooper", 2450, 2900, 0, 2),
    ("z6_square", "stormtrooper", 1900, 3250, 0, 2),
    ("z6_square", "hound", 2800, 2000, 0, 2),
    ("z6_square", "hound", 2450, 2750, 0, 2),
    ("z6_square", "panzermensch", 2450, 2000, 0, 2),
    ("z6_square", "doughboy", 2700, 2800, 0, 2),
    ("z6_square", "rifleman", 2040, 2000, 0, 3),
    ("z6_square", "rifleman", 3000, 1300, 0, 3),
    ("z6_square", "stormtrooper", 2100, 3100, 0, 3),
    ("z6_square", "stormtrooper", 3200, 2550, 0, 3),
    ("z6_square", "doughboy", 2100, 2400, 0, 3),
    # The Legion's gunners (D116) behind the halted parade's vehicles, the
    # square's width to fire across at the GUM's doors.
    ("z6_square", "gunner", 2176, 2450, 0, 3),
    ("z6_square", "rifleman", 3300, 1700, 0, 4),
    ("z6_square", "rifleman", 1950, 1700, 0, 4),
    ("z6_square", "stormtrooper", 2450, 1250, 0, 4),
    ("z6_square", "heavy", 2750, 1700, 0, 4),
    ("z6_square", "panzermensch", 2450, 3300, 0, 4),
    ("z6_square", "hound", 3000, 2350, 0, 4),
    ("z6_square", "gunner", 2810, 1900, 0, 4),
    # The museum's closets (TAG_AMBUSH, the red key's pickup): the Legion's
    # counter-attack on the square already crossed, as the player comes back.
    ("closet_z6_w", "trooper", 1960, 3528, 270, 2),
    ("closet_z6_w", "trooper", 2020, 3528, 270, 3),
    ("closet_z6_w", "stormtrooper", 2080, 3528, 270, 4),
    ("closet_z6_e", "trooper", 2340, 3528, 270, 2),
    ("closet_z6_e", "stormtrooper", 2400, 3528, 270, 3),
    ("closet_z6_e", "stormtrooper", 2460, 3528, 270, 4),
    # The vehicle park on the slope: the Reich's staging ground, facing the gatehouse.
    ("z7_park", "rifleman", 2000, 950, 90, 2),
    ("z7_park", "rifleman", 2300, 900, 90, 2),
    ("z7_park", "rifleman", 2600, 600, 90, 2),
    ("z7_park", "hound", 1800, 950, 0, 2),
    ("z7_park", "panzermensch", 2300, 560, 90, 2),
    ("z7_park", "rifleman", 1750, 550, 90, 3),
    ("z7_park", "rifleman", 2850, 550, 90, 3),
    ("z7_park", "stormtrooper", 2050, 1000, 90, 3),
    ("z7_park", "heavy", 1760, 800, 0, 4),
    ("z7_park", "stormtrooper", 2600, 1050, 90, 4),
    ("z7_park", "hound", 2850, 950, 90, 4),
    # The Spasskaya gate's passage.
    ("z8_passage", "stormtrooper", 1488, 1536, 0, 3),
    # The Kremlin courtyard: the boss on his dais, both factions round him.
    ("z9_dais_2", BOSS_KIND, MAP06_BOSS_SPOT[0], MAP06_BOSS_SPOT[1], BOSS_ANGLE, 2),
    ("z9_arena", "stormtrooper", 1200, 1100, 180, 2),
    ("z9_arena", "stormtrooper", 1200, 1950, 180, 2),
    ("z9_arena", "doughboy", 700, 1300, 0, 2),
    ("z9_arena", "hound", 1250, 1650, 180, 3),
    ("z9_arena", "hound", 1250, 1400, 180, 3),
    ("z9_arena", "heavy", 700, 1750, 0, 4),
    ("z9_arena", "panzermensch", 1100, 1100, 180, 4),
    ("z9_arena", "doughboy", 1100, 1900, 180, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on - 4 every skill, 3 medium and easier, 2 easy only).
ITEMS = (
    # The weapons, on every skill, each before the fight it is for: the IZh
    # in the station, the PPSh in the GUM's north hall, the RPG-7 on the
    # gallery (before the square's Panzermensch), the ROKS-3 on the south
    # stand (before the slope's heavies).
    ("z1_hall", ED_IZH, 4992, 4864, 4),
    ("z4_north", ED_PPSH, 3800, 3500, 4),
    ("z5_gallery_n", ED_RPG7, 4288, 2880, 4),
    ("z6_tribune_s_top", ED_ROKS3, 1712, 1984, 4),
    # Stimpacks: 6 on every skill, +3 medium, +2 easy.
    ("z1_plat_s", ED_STIMPACK, 5000, 4556, 4),
    ("z3_street", ED_STIMPACK, 4300, 4050, 4),
    ("z4_shop_a", ED_STIMPACK, 3872, 1550, 4),
    ("z6_square", ED_STIMPACK, 3400, 1600, 4),
    ("z7_park", ED_STIMPACK, 1700, 500, 4),
    ("z9_arena", ED_STIMPACK, 1300, 1100, 4),
    ("z2_pavilion", ED_STIMPACK, 3560, 4400, 3),
    ("z6_square", ED_STIMPACK, 3400, 3000, 3),
    ("z9_arena", ED_STIMPACK, 1300, 1900, 3),
    ("z4_north", ED_STIMPACK, 3600, 3540, 2),
    ("z6_square", ED_STIMPACK, 3300, 1250, 2),
    # Medikits: 6 on every skill, +2 medium.
    ("z4_shop_d", ED_MEDIKIT, 3872, 3150, 4),
    ("z5_shop_u3", ED_MEDIKIT, 4550, 1650, 4),
    ("z6_square", ED_MEDIKIT, 3400, 2400, 4),
    ("z7_park", ED_MEDIKIT, 2850, 500, 4),
    ("z9_arena", ED_MEDIKIT, 560, 900, 4),
    ("z9_arena", ED_MEDIKIT, 560, 1950, 4),
    ("z6_square", ED_MEDIKIT, 2200, 3300, 3),
    ("z9_arena", ED_MEDIKIT, 1300, 1550, 3),
    # Armour: the flak vest in the GUM's west upper room, the heavy vest in
    # the Spasskaya gate's passage before the boss; plates at the three locks.
    ("z5_upper_w", ED_GREEN_ARMOR, 3870, 3030, 4),
    ("z8_passage", ED_BLUE_ARMOR, 1520, 1500, 4),
    ("z4_blue_band", ED_ARMOR_BONUS, 3552, 2208, 4),
    ("z4_blue_band", ED_ARMOR_BONUS, 3552, 2528, 4),
    ("z6_square", ED_ARMOR_BONUS, 2720, 1184, 4),
    ("z6_square", ED_ARMOR_BONUS, 2784, 1184, 4),
    ("z6_gate_apron", ED_ARMOR_BONUS, 1728, 1488, 4),
    ("z6_gate_apron", ED_ARMOR_BONUS, 1728, 1584, 4),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z1_band", ED_HEALTH_BONUS, 5344, 4776, 4),
    ("z1_track_s", ED_HEALTH_BONUS, 4160, 4416, 4),
    ("z1_track_n", ED_HEALTH_BONUS, 5300, 5306, 4),
    ("z2_door", ED_HEALTH_BONUS, 3680, 4128, 4),
    ("z4_north_door", ED_HEALTH_BONUS, 4096, 3616, 4),
    ("z4_atrium_gate", ED_HEALTH_BONUS, 3792, 2336, 4),
    ("z3_gate_arch_1", ED_HEALTH_BONUS, 2880, 3616, 4),
    ("z7_porch", ED_HEALTH_BONUS, 2752, 1056, 4),
    ("z9_exit_porch", ED_HEALTH_BONUS, 480, 1536, 4),
)

# D119 (the CEO's playtest: "siempre sale de sobras", and always on the
# shotgun): AMMUNITION FOLLOWS THE MONSTERS, not the consumables' rule, so it
# grows with skill as they do. Rows: (zone, editor number, x, y, lowest tier,
# highest tier), udmf.skill_tier's range (2 easy, 3 medium, 4 hard).
# G3-8's D119 bands (docs/engine/BALANCE.md): 1.5-2.0 x the ruler on skill 2,
# 1.3-1.6 on 3, 1.2-1.45 on 4; shells at most ~35 % of the damage placed; the
# rest for the weapons of each stretch, the newest first: the PPSh's boxes
# through the GUM and the square, rockets and fuel in moderation (the ROKS-3
# is being toned down, D119) and most of them for the colossus (3000 HP
# since D119, the Spider Mastermind's). Two AKM magazines on every skill:
# the rifle is MAP05's, and a pistol start never owns it.
AMMO = (
    # Stage 0: the station (the IZh), the pavilion, the street, the GUM
    # (the PPSh in the north hall, the RPG-7 on the north gallery).
    ("z1_hall", ED_SHELL_BOX, 4400, 4906, 2, 4),
    ("z1_plat_s", ED_SHELLS, 4800, 4556, 2, 3),
    ("z3_street", ED_SHELLS, 3500, 4050, 2, 2),
    ("z3_street", ED_SHELL_BOX, 3700, 4000, 4, 4),
    ("z2_pavilion", ED_CLIP_BOX, 3780, 4700, 2, 4),
    ("z1_hall", ED_CLIP_BOX, 4500, 4776, 4, 4),
    ("z4_north", ED_CLIP_BOX, 4000, 3540, 2, 4),
    ("z4_north", ED_AKM_AMMO, 3720, 3500, 2, 4),
    ("z4_shop_d", ED_CLIP_BOX, 3872, 3200, 2, 4),
    ("z4_arcade", ED_CLIP_BOX, 3560, 3200, 3, 4),
    ("z4_arcade", ED_CLIP_BOX, 3560, 2000, 2, 4),
    ("z5_gallery_n", ED_ROCKET_BOX, 4288, 2800, 2, 4),
    ("z5_gallery_s", ED_CLIP_BOX, 4288, 1600, 2, 4),
    ("z5_passage_s", ED_CLIP_BOX, 4180, 1450, 4, 4),
    ("z1_plat_n", ED_CLIP_BOX, 4600, 5156, 4, 4),
    ("z3_street", ED_CLIP_BOX, 2900, 3900, 4, 4),
    # Stage 1: the square and the south stand (the ROKS-3).
    ("z6_square", ED_SHELL_BOX, 3300, 2200, 3, 4),
    ("z6_square", ED_AKM_AMMO, 3350, 2050, 2, 4),
    ("z6_square", ED_CLIP_BOX, 3350, 1900, 2, 4),
    ("z6_square", ED_CLIP_BOX, 2650, 3400, 2, 4),
    ("z6_square", ED_ROCKET_BOX, 3350, 2500, 4, 4),
    ("z6_square", ED_CLIP_BOX, 3350, 2700, 2, 4),
    ("z6_tribune_s_top", ED_CELL, 1712, 1900, 2, 4),
    ("z6_square", ED_CLIP_BOX, 3300, 3400, 3, 4),
    ("z6_square", ED_CLIP_BOX, 3350, 1300, 4, 4),
    ("z6_square", ED_ROCKET_BOX, 2000, 3400, 3, 4),
    ("z6_square", ED_CLIP_BOX, 2200, 3400, 4, 4),
    ("z6_square", ED_CLIP_BOX, 2500, 3350, 4, 4),
    ("z6_square", ED_ROCKET_BOX, 3400, 2100, 4, 4),
    ("z6_tribune_s_top", ED_CLIP_BOX, 1712, 2080, 4, 4),
    # Stage 2: the vehicle park.
    ("z7_park", ED_CLIP_BOX, 2400, 1000, 2, 4),
    ("z7_park", ED_CLIP_BOX, 1750, 1000, 2, 4),
    ("z7_park", ED_ROCKET_BOX, 2100, 1000, 4, 4),
    ("z7_park", ED_CLIP_BOX, 1700, 700, 4, 4),
    ("z7_park", ED_SHELL_BOX, 2850, 800, 4, 4),
    ("z7_park", ED_CLIP_BOX, 2000, 520, 4, 4),
    ("z7_park", ED_CELL, 1700, 900, 4, 4),
    # Stage 3: the gate's passage and the courtyard, the colossus.
    ("z8_passage", ED_CLIP_BOX, 1440, 1500, 2, 4),
    ("z8_passage", ED_ROCKET_BOX, 1440, 1580, 2, 4),
    ("z8_passage", ED_CELL_PACK, 1520, 1580, 2, 4),
    ("z9_arena", ED_SHELL_BOX, 600, 900, 2, 4),
    ("z9_arena", ED_CLIP_BOX, 1300, 800, 2, 4),
    ("z9_arena", ED_ROCKET_BOX, 560, 820, 2, 4),
    ("z9_arena", ED_ROCKET_BOX, 560, 2000, 2, 4),
    ("z9_arena", ED_ROCKET_BOX, 1250, 1300, 2, 4),
    ("z9_arena", ED_CELL, 600, 1000, 3, 4),
    ("z9_arena", ED_CLIP_BOX, 1300, 1980, 3, 4),
    ("z9_arena", ED_ROCKET_BOX, 640, 1536, 4, 4),
    ("z9_arena", ED_CELL, 640, 2000, 4, 4),
)

# Kept out of ITEMS on purpose: ITEMS is the route's. Same row shape; every
# secret's reward is on every skill (MAP01's rule).
SECRET_ITEMS = (
    # S1: the station master's store - a backpack, a vest, shells.
    ("s1_store", ED_BACKPACK, 5600, 4928, 4),
    ("s1_store", ED_GREEN_ARMOR, 5600, 4856, 4),
    ("s1_store", ED_SHELL_BOX, 5680, 4928, 4),
    # S2: behind the crates, the Hand Katyusha (40 fuel, one volley) and a pack.
    ("s2_store", ED_HAND_KATYUSHA, 4768, 3168, 4),
    ("s2_store", ED_CELL_PACK, 4700, 3100, 4),
    # S3: the courtyard behind Nikolskaya's gate - medikits and PG-7V.
    ("s3_yard", ED_MEDIKIT, 3264, 4300, 4),
    ("s3_yard", ED_MEDIKIT, 3392, 4300, 4),
    ("s3_yard", ED_ROCKET_BOX, 3328, 4250, 4),
)


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = GRANITE, ceiling: str = CEIL_CONCRETE,
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


def _sides(tm: TextMap, ld):
    """[(sidedef, its sector, the other sector or None, start, end)] for each
    side of `ld`: start and end are the side's own run (v1->v2 for the front,
    v2->v1 for the back), the way the engine lays its texture."""
    a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
    front = tm.sidedefs[ld.sidefront]
    if ld.sideback is None:
        return [(front, tm.sectors[front.sector], None, a, b)]
    back = tm.sidedefs[ld.sideback]
    fs, bs = tm.sectors[front.sector], tm.sectors[back.sector]
    return [(front, fs, bs, a, b), (back, bs, fs, b, a)]


def _run(start, end) -> tuple[int, int]:
    """The unit direction of an axis-aligned run."""
    return ((end.x > start.x) - (end.x < start.x), (end.y > start.y) - (end.y < start.y))


def hang_merlons(tm: TextMap, walks: set[int], faces_x: tuple[int, ...]) -> None:
    """SDKREM2 on the face of each wall walk: the middle texture of every
    two-sided line on `faces_x` between a walk and the open ground, on the
    ground's side. The line is impassable (nothing floats onto the walk).
    GridMap dresses only the upper and lower parts of a two-sided line, so
    this is done on the built map, as MAP03 hangs its chains."""
    for ld in tm.linedefs:
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        if ld.sideback is None or a.x != b.x or a.x not in faces_x:
            continue
        front, back = tm.sidedefs[ld.sidefront], tm.sidedefs[ld.sideback]
        for walk, face in ((front, back), (back, front)):
            if walk.sector in walks and face.sector not in walks:
                face.texturemiddle = MERLON
                ld.blocking = True


def dress_carriers(tm: TextMap, carriers: dict[int, tuple[int, int, int, int]]) -> None:
    """The missile carriers' long flanks wear SDARMR1, its star whole: one
    star per 128 from the flank's end, raised STAR_OFFSET rows."""
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        indices = (tm.sidedefs[ld.sidefront].sector, tm.sidedefs[ld.sideback].sector)
        for (side, sector, other, start, end), far in zip(_sides(tm, ld), reversed(indices)):
            hull = carriers.get(far)
            if hull is None or side.texturebottom != ARMOUR or sector.heightfloor >= other.heightfloor:
                continue
            x1, y1, x2, y2 = hull
            if not (start.x == end.x and start.x in (x1, x2)):
                continue    # the short ends keep the plain plate
            dx, dy = _run(start, end)
            first = min(y1 * dy, y2 * dy)
            side.texturebottom = ARMOUR_STAR
            side.offsetx = int(start.y * dy - first) % ALIGN_PERIOD
            side.extra["offsety_bottom"] = STAR_OFFSET


def hang_the_ruby_star(tm: TextMap, plan: dict[str, int]) -> None:
    """SDRUBY1 on the line that halves the tent's top, on both its sides (the
    star faces the square and the courtyard), at half scale: Doom hangs a
    two-sided middle texture from the lower ceiling, here the apron's sky,
    so the 64 x 64 star stands from the tent (TOWER_SPIRE) to that sky. The
    line is impassable (nobody is up there; it keeps the gap between the
    halves out of any route's reckoning)."""
    halves = {plan["prop_z6_tower_top"], plan["prop_z6_tower_top_e"]}
    hung = 0
    for ld in tm.linedefs:
        if ld.sideback is None:
            continue
        if {tm.sidedefs[ld.sidefront].sector, tm.sidedefs[ld.sideback].sector} != halves:
            continue
        for side in (ld.sidefront, ld.sideback):
            sd = tm.sidedefs[side]
            sd.texturemiddle = RUBY_STAR
            sd.extra["scalex_mid"] = RUBY_STAR_SCALE
            sd.extra["scaley_mid"] = RUBY_STAR_SCALE
        hung += 1
    if hung != 1:
        raise ValueError(f"the ruby star's line: {hung} lines between the tent's halves")


def dress_shopfronts(tm: TextMap) -> None:
    """Deal the GUM's three shopfronts along the line's walls: every line
    that wears SHOPFRONT on a drawn part is cut at the world's 64 grid (the
    corners of the cut are new vertices on the same line: nothing moves),
    and each 64 of wall gets the sign of its column, SHOPFRONTS[(c // 64) %
    3], so the shops follow one another «ТКАНИ», «ОБУВЬ», «ЧАСЫ» along the
    walls and up the tiers. Each piece is world-aligned along the wall (a
    piece cut short by a corner shows the part of the front the grid gives
    it). Lines with a special are left alone (none of them wears it)."""
    width = SHOPFRONT_WIDTH
    for index in range(len(tm.linedefs)):
        ld = tm.linedefs[index]
        sides = [s for s in (ld.sidefront, ld.sideback) if s is not None]
        parts = ("texturetop", "texturemiddle", "texturebottom")
        if ld.special or not any(getattr(tm.sidedefs[s], p) == SHOPFRONT for s in sides for p in parts):
            continue
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        vertical = a.x == b.x
        lo, hi = (a.y, b.y) if vertical else (a.x, b.x)
        step = 1 if hi > lo else -1
        cuts = sorted(c for c in range(int(min(lo, hi)) // width * width + width, int(max(lo, hi)), width)
                      if min(lo, hi) < c < max(lo, hi))
        if step < 0:
            cuts.reverse()
        points = [lo] + cuts + [hi]
        originals = {s: replace(tm.sidedefs[s], extra=dict(tm.sidedefs[s].extra)) for s in sides}
        for n, (p, q) in enumerate(zip(points, points[1:])):
            sign = SHOPFRONTS[(int(min(p, q)) // width) % len(SHOPFRONTS)]
            if n == 0:
                piece, own = ld, {s: s for s in sides}
            else:
                own = {s: tm.add_sidedef(replace(originals[s], extra=dict(originals[s].extra)))
                       for s in sides}
                piece = replace(ld, sidefront=own[ld.sidefront],
                                sideback=own[ld.sideback] if ld.sideback is not None else None,
                                extra=dict(ld.extra))
                tm.add_linedef(piece)
            piece.v1 = tm.vertex(a.x, p) if vertical else tm.vertex(p, a.y)
            piece.v2 = tm.vertex(a.x, q) if vertical else tm.vertex(q, a.y)
            for s in sides:
                sd = tm.sidedefs[own[s]]
                for part in parts:
                    if getattr(originals[s], part) == SHOPFRONT:
                        setattr(sd, part, sign)
                # Doom runs a front side from v1 to v2, a back side from v2 to v1.
                start, run = (p, step) if s == ld.sidefront else (q, -step)
                sd.offsetx = int(start * run) % width


def align_to_world(tm: TextMap) -> None:
    """Give every side that wears an ALIGNED lump the offsets that lay it on
    the world: its columns follow x or y (so the brick runs on across lines),
    its rows count from the lump's height in ALIGNED. The anchors are Doom's
    pegging rules, per part (UDMF's offsety_top / _mid / _bottom)."""
    for ld in tm.linedefs:
        flags = set(ld.flags)
        for side, sector, other, start, end in _sides(tm, ld):
            parts = {"top": side.texturetop, "mid": side.texturemiddle, "bottom": side.texturebottom}
            if not any(t in ALIGNED for t in parts.values()):
                continue
            dx, dy = _run(start, end)
            side.offsetx = int(start.x * dx + start.y * dy) % ALIGN_PERIOD
            for part, texture in parts.items():
                if texture not in ALIGNED:
                    continue
                if other is None:
                    anchor = (sector.heightfloor + ALIGN_PERIOD if "dontpegbottom" in flags
                              else sector.heightceiling)
                elif part == "top":
                    anchor = (sector.heightceiling if "dontpegtop" in flags
                              else other.heightceiling + ALIGN_PERIOD)
                elif part == "bottom":
                    anchor = sector.heightceiling if "dontpegbottom" in flags else other.heightfloor
                else:
                    anchor = (max(sector.heightfloor, other.heightfloor) + ALIGN_PERIOD
                              if "dontpegbottom" in flags
                              else min(sector.heightceiling, other.heightceiling))
                offset = (ALIGNED[texture] - anchor) % ALIGN_PERIOD
                if offset:
                    side.extra[f"offsety_{part}"] = offset


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1.1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=CONCRETE)
    plan: dict[str, int] = {}

    def zone(name: str, floor: int, ceil: int, rects, tag: int | None = None, *,
             light: int, flat: str = GRANITE, ceiling: str = CEIL_CONCRETE,
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

    def block(name: str, top: int, rects, *, wall: str, light: int, flat: str = GRANITE) -> int:
        """A closed open-air block (floor = ceiling, sky): a wall top, a tower
        stage, a parapet. Seen as a wall `top` high with the sky above it."""
        return zone(name, top, top, rects, light=light, flat=flat, ceiling=SKY, wall=wall)

    def prop(room: str, name: str, rect, top: int, *, wall: str, flat: str | None = None) -> int:
        """Something standing in `room` that nobody walks on: a statue, a
        vehicle, a stack of crates. Its top is `top`, its sky the room's."""
        return like(room, f"{PROP_PREFIX}{name}", [rect], floor=top, wall=wall,
                    **({"flat": flat} if flat else {}))

    def recess(room: str, name: str, rect, *, ceil: int, back, texture: str,
               light: int | None = None) -> int:
        """A shallow recess one tile high in `room`'s wall; its back wall one
        whole tile of `texture`. `back` is ("v", x, y1, y2) or ("h", y, x1, x2)."""
        index = like(room, name, [rect], ceil=ceil, light=light, ceiling=CEIL_CONCRETE)
        kind, coord, lo, hi = back
        style = LineStyle(texture=texture)
        (g.style_v if kind == "v" else g.style_h)(coord, lo, hi, style)
        return index

    # The posters first: GridMap keeps the first style registered on a
    # segment, so nothing broader can paint over them.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))

    # ======================================================================
    # Z1 The station, Ploshchad Revolyutsii (start)
    # ======================================================================
    hx1, hy1, hx2, hy2 = HALL
    zone("z1_plat_s", METRO, METRO_CEIL, [(hx1, 4480, hx2, 4672)], light=LIGHT_PLATFORM,
         flat=GRANITE, ceiling=CEIL_COFFER, wall=STATION_WALL)
    zone("z1_edge_s", METRO, METRO_CEIL, [(hx1, 4480, hx2, 4512)], light=LIGHT_PLATFORM,
         flat=PLATFORM_EDGE, ceiling=CEIL_COFFER, wall=PLATFORM_FACE,
         extra={"rotationfloor": 180.0})
    zone("z1_track_s", TRACK, METRO_CEIL, [(hx1, 4352, hx2, 4480)], light=LIGHT_TRACK,
         flat=RAILS, ceiling=CEIL_COFFER, wall=TUBBING, extra={"rotationfloor": 90.0})
    zone("z1_plat_n", METRO, METRO_CEIL, [(hx1, 5056, hx2, 5248)], light=LIGHT_PLATFORM,
         flat=GRANITE, ceiling=CEIL_COFFER, wall=STATION_WALL)
    zone("z1_edge_n", METRO, METRO_CEIL, [(hx1, 5216, hx2, 5248)], light=LIGHT_PLATFORM,
         flat=PLATFORM_EDGE, ceiling=CEIL_COFFER, wall=PLATFORM_FACE)
    zone("z1_track_n", TRACK, METRO_CEIL, [(hx1, 5248, hx2, 5376)], light=LIGHT_TRACK,
         flat=RAILS, ceiling=CEIL_COFFER, wall=TUBBING, extra={"rotationfloor": 90.0})
    zone("z1_hall", METRO, METRO_CEIL, [HALL], light=LIGHT_HALL, flat=GRANITE_CHECK,
         ceiling=CEIL_LAMP, wall=MARBLE)
    # The arcades: the pillars are the void between the arches; in each arch
    # two bronze figures crouch either side of the way through.
    for side, (ay1, ay2) in ARCH_ROWS.items():
        for n, ax in enumerate(ARCHES_X, start=1):
            like("z1_hall", f"z1_arch_{side}{n}", [(ax, ay1, ax + ARCH_WIDTH, ay2)],
                 ceil=METRO + DOOR_HEIGHT)
            sy = ay1 + (ay2 - ay1 - STATUE_SIZE) // 2
            for tag_, sx in (("a", ax), ("b", ax + ARCH_WIDTH - STATUE_SIZE)):
                prop(f"z1_arch_{side}{n}", f"z1_statue_{side}{n}{tag_}",
                     (sx, sy, sx + STATUE_SIZE, sy + STATUE_SIZE), METRO + STATUE, wall=BRASS)
    # The east end: a band one tile high so the mosaics are whole tiles; the
    # second of the two mosaics stands back in shadow and is S1's panel.
    like("z1_hall", "z1_band", [(5312, hy1, hx2, hy2)], ceil=METRO + TILE_SIZE)
    g.style_v(hx2, hy1, 4864, LineStyle(texture=MOSAIC))
    zone("s1_niche", METRO, METRO + TILE_SIZE, [(hx2, 4864, hx2 + NICHE_DEPTH, hy2)],
         light=LIGHT_CLUE, flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=MARBLE)
    s1_panel = zone("s1_panel", METRO, METRO, [(hx2 + NICHE_DEPTH, 4864, hx2 + 2 * NICHE_DEPTH, hy2)],
                    TAG_S1_PANEL, light=LIGHT_CLUE, flat=GRANITE_CHECK, wall=MARBLE)
    zone("s1_passage", METRO, METRO + TILE_SIZE, [(hx2 + 2 * NICHE_DEPTH, 4864, 5472, hy2)],
         light=LIGHT_SECRET, flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=MARBLE)
    zone("s1_store", METRO, METRO + TILE_SIZE, [(5472, 4800, 5728, 5056)], light=LIGHT_SECRET,
         flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=MARBLE, special=SECTOR_SPECIAL_SECRET)
    for x in (hx2 + NICHE_DEPTH, hx2 + 2 * NICHE_DEPTH):
        g.style_v(x, 4864, hy2, secret_panel_style(TAG_S1_PANEL, s1_panel, MOSAIC))
    # The escalator: eight steps up to the street, rising west.
    ex1, ey1, ex2, ey2 = ESCALATOR
    for k in range(1, 9):
        floor = METRO + STEP * k
        zone(f"z1_esc_{k}", floor, floor + DOOR_HEIGHT,
             [(ex2 - STEP_DEPTH * k, ey1, ex2 - STEP_DEPTH * (k - 1), ey2)],
             light=LIGHT_ESCALATOR, flat=PLATE, ceiling=CEIL_COFFER, wall=TILE)

    # ======================================================================
    # Z2 The street pavilion, Z3 Nikolskaya street
    # ======================================================================
    zone("z2_pavilion", GROUND, 192, [PAVILION], light=LIGHT_PAVILION, flat=GRANITE,
         ceiling=CEIL_COFFER, wall=CONCRETE)
    zone("z2_door", GROUND, DOOR_HEIGHT, [PAVILION_DOOR], light=LIGHT_PAVILION,
         flat=GRANITE, ceiling=CEIL_COFFER, wall=CONCRETE)
    zone("z3_street", GROUND, STREET_SKY, [STREET], light=LIGHT_STREET, flat=FLOOR_ASPHALT,
         ceiling=SKY, wall=CONCRETE)
    sx1, sy1, sx2, sy2 = STREET
    # The GUM's north facade, across the street from the courtyard gates.
    g.style_h(sy1, GUM_NORTH[0], GUM_NORTH[2], LineStyle(texture=GUM_FACADE))
    for n, gx in enumerate(STREET_GATES_X, start=1):
        if n == 2:
            continue    # S3, below
        recess("z3_street", f"z3_yard_gate_{n}", (gx, sy2, gx + TILE_SIZE, sy2 + NICHE_DEPTH),
               ceil=GROUND + TILE_SIZE, back=("h", sy2 + NICHE_DEPTH, gx, gx + TILE_SIZE),
               texture=GATE)
    s3x = STREET_GATES_X[1]
    zone("s3_niche", GROUND, GROUND + TILE_SIZE, [(s3x, sy2, s3x + TILE_SIZE, sy2 + 2 * NICHE_DEPTH)],
         light=LIGHT_CLUE, flat=FLOOR_ASPHALT, wall=CONCRETE)
    s3_panel = zone("s3_panel", GROUND, GROUND,
                    [(s3x, sy2 + 2 * NICHE_DEPTH, s3x + TILE_SIZE, sy2 + 3 * NICHE_DEPTH)],
                    TAG_S3_PANEL, light=LIGHT_CLUE, flat=FLOOR_ASPHALT, wall=GATE)
    zone("s3_yard", GROUND, YARD_SKY, [(3200, sy2 + 3 * NICHE_DEPTH, 3456, 4400)],
         light=LIGHT_SECRET, flat=GRANITE, ceiling=SKY, wall=BRICK, special=SECTOR_SPECIAL_SECRET)
    for y in (sy2 + 2 * NICHE_DEPTH, sy2 + 3 * NICHE_DEPTH):
        g.style_h(y, s3x, s3x + TILE_SIZE, secret_panel_style(TAG_S3_PANEL, s3_panel, GATE))
    # V3 (A3): the reserve's courtyard gate, in a recess like the street's
    # other gates; the gate is a sector as high as the recess (floor =
    # ceiling, its face SDGATE1 from the street, as theirs), which the yellow
    # key's special sinks to the ground.
    recess("z3_street", "z3_reserve_recess", RESERVE_RECESS, ceil=GROUND + TILE_SIZE,
           back=("h", RESERVE_GATE[1], RESERVE_GATE[0], RESERVE_GATE[2]), texture=GATE)
    zone("z3_reserve_gate", GROUND + TILE_SIZE, GROUND + TILE_SIZE, [RESERVE_GATE], TAG_RESURRECTION,
         light=LIGHT_STREET, flat=FLOOR_ASPHALT, ceiling=CEIL_CONCRETE, wall=BRICK)
    zone("z3_reserve", GROUND, YARD_SKY, [RESERVE], light=LIGHT_STREET, flat=FLOOR_ASPHALT,
         ceiling=SKY, wall=BRICK)
    prop("z3_street", "z3_barricade_1", (3328, 3776, 3456, 3840), BARRICADE, wall=LONG_CRATE,
         flat=CRATE_TOP)
    prop("z3_street", "z3_barricade_2", (3904, 3840, 4032, 3904), BARRICADE, wall=LONG_CRATE,
         flat=CRATE_TOP)
    prop("z3_street", "z3_truck", (2944, 3840, 3136, 3936), BARRICADE, wall=STEEL, flat=PLATE)
    # The Resurrection gate's two arches, barricaded across their middle: the
    # square is seen from the street, and not reached.
    for n, ax in enumerate(RESURRECTION_ARCHES_X, start=1):
        zone(f"z3_gate_arch_{n}", GROUND, 192, [(ax, 3584, ax + TILE_SIZE, 3648)],
             light=LIGHT_STREET, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=MUSEUM)
        # V3 (A3): the barricade is no prop any more: the yellow key's
        # special sinks it to the arches' floor (TAG_RESURRECTION).
        zone(f"z3_gate_barricade_{n}", BARRICADE, 192,
             [(ax, 3520, ax + TILE_SIZE, 3584)], TAG_RESURRECTION, light=LIGHT_STREET, flat=CRATE_TOP,
             ceiling=CEIL_CONCRETE, wall=LONG_CRATE)
        zone(f"z6_gate_arch_{n}", GROUND, 192, [(ax, 3456, ax + TILE_SIZE, 3520)],
             light=LIGHT_SQUARE, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=MUSEUM)

    # ======================================================================
    # Z4 The GUM, ground floor
    # ======================================================================
    zone("z4_north", GROUND, 256, [GUM_NORTH], light=LIGHT_GUM, flat=GRANITE_CHECK,
         ceiling=CEIL_COFFER, wall=STATION_WALL)
    zone("z4_north_door", GROUND, 192, [(3968, 3584, 4224, 3648)], light=LIGHT_GUM,
         flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=CONCRETE)
    zone("z4_south", GROUND, 256, [GUM_SOUTH], light=LIGHT_GUM, flat=GRANITE_CHECK,
         ceiling=CEIL_COFFER, wall=STATION_WALL)
    recess("z4_south", "z4_ilyinka_gate", (3904, 1152 - NICHE_DEPTH, 4032, 1152),
           ceil=GROUND + TILE_SIZE, back=("h", 1152 - NICHE_DEPTH, 3904, 4032), texture=GATE)
    zone("z4_arcade", GROUND, 192, [ARCADE], light=LIGHT_GUM, flat=GRANITE,
         ceiling=CEIL_COFFER, wall=STATION_WALL)
    for y in ARCADE_PILLARS_Y:
        g.carve(3680, y, 3744, y + 64)
    # The blue lock: the GUM's doors onto the square, between two cobalt
    # mosaics on the arcade side (MAP02's blue door), a band one tile high.
    zone("z4_blue_band", GROUND, DOOR_HEIGHT, [(3520, 2176, 3584, 2560)], light=LIGHT_BEACON,
         flat=GRANITE, ceiling=CEIL_COFFER, wall=STATION_WALL, extra=BLUE_LIGHT)
    blue_door = door("z4_blue_door", GROUND, TAG_BLUE_DOOR, (3488, 2304, 3520, 2432),
                     light=LIGHT_GUM)
    zone("z6_blue_portal", GROUND, DOOR_HEIGHT, [(3456, 2304, 3488, 2432)], light=LIGHT_BEACON,
         flat=GRANITE, ceiling=CEIL_CONCRETE, wall=CONCRETE, extra=BLUE_LIGHT)
    for y in FACADE_WINDOWS_Y:
        zone(f"{PROP_PREFIX}z4_window_{y}", WINDOW_SILL, WINDOW_HEAD, [(3456, y, 3520, y + TILE_SIZE)],
             light=LIGHT_GUM, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=CONCRETE)
    # The row of shops between the arcade and the line: looted, dark.
    shops = {"a": (1472, 1792), "b": (1856, 2112), "c": (2560, 2816), "d": (3136, 3264)}
    for s, (y1, y2) in shops.items():
        zone(f"z4_shop_{s}", GROUND, SHOP_CEIL, [(3808, y1, 3936, y2)], light=LIGHT_SHOP,
             flat=GRANITE, ceiling=CEIL_COFFER, wall=TILE)
    doorways = {"z4_shop_a_front": (3936, 1568, 3968, 1696),
                "z4_shop_b_back": (3776, 1920, 3808, 2048), "z4_shop_b_front": (3936, 1920, 3968, 2048),
                "z4_shop_c_back": (3776, 2624, 3808, 2752), "z4_shop_c_front": (3936, 2624, 3968, 2752),
                "z4_shop_d_front": (3936, 3168, 3968, 3232)}
    for name, rect in doorways.items():
        zone(name, GROUND, DOOR_HEIGHT, [rect], light=LIGHT_SHOP, flat=GRANITE,
             ceiling=CEIL_COFFER, wall=TILE)
    prop("z4_shop_a", "z4_crates_a", (3808, 1600, 3872, 1664), CRATES, wall=CRATE, flat=CRATE_TOP)
    prop("z4_shop_d", "z4_crates_d", (3808, 3232, 3872, 3264), CRATES, wall=CRATE, flat=CRATE_TOP)
    zone("z4_atrium_gate", GROUND, 192, [(3776, 2240, 3808, 2432)], light=LIGHT_GUM,
         flat=GRANITE, ceiling=CEIL_COFFER, wall=STATION_WALL)

    # ======================================================================
    # Z5 The line under the glass roof, the atrium, the gallery and the bridge
    # (the vault SDGUMR1 over all of it; the shopfronts SDGUMS1-3 dealt along
    # its walls by dress_shopfronts after the build)
    # ======================================================================
    zone("z5_passage_s", GROUND, PASSAGE_SKY, [PASSAGE_S], light=LIGHT_PASSAGE,
         flat=GRANITE_CHECK, ceiling=GLASS_ROOF, wall=SHOPFRONT)
    zone("z5_passage_n", GROUND, PASSAGE_SKY, [PASSAGE_N], light=LIGHT_PASSAGE,
         flat=GRANITE_CHECK, ceiling=GLASS_ROOF, wall=SHOPFRONT)
    zone("z5_atrium", GROUND, PASSAGE_SKY, [ATRIUM], light=LIGHT_ATRIUM, flat=GRANITE_CHECK,
         ceiling=GLASS_ROOF, wall=SHOPFRONT)
    prop("z5_atrium", "z5_fountain", (4032, 2272, 4160, 2400), FOUNTAIN_RIM, wall=MARBLE,
         flat=GRANITE)
    prop("z5_atrium", "z5_spout", (4064, 2304, 4128, 2368), FOUNTAIN_SPOUT, wall=BRASS,
         flat=GRANITE)
    zone("z5_bridge", GALLERY, PASSAGE_SKY, [BRIDGE], light=LIGHT_GALLERY, flat=GRANITE,
         ceiling=GLASS_ROOF, wall=STEEL)
    zone("z5_bridge_key", GALLERY, PASSAGE_SKY, [BRIDGE_KEY], light=LIGHT_BEACON, flat=GRANITE,
         ceiling=GLASS_ROOF, wall=STEEL, extra=BLUE_LIGHT)
    zone("z5_upper_w", GALLERY, PASSAGE_SKY, [UPPER_WEST], light=LIGHT_GALLERY, flat=GRANITE,
         ceiling=GLASS_ROOF, wall=SHOPFRONT)
    zone("z5_gallery_n", GALLERY, PASSAGE_SKY, [GALLERY_N], light=LIGHT_GALLERY, flat=GRANITE,
         ceiling=GLASS_ROOF, wall=SHOPFRONT)
    zone("z5_gallery_s", GALLERY, PASSAGE_SKY, [GALLERY_S], light=LIGHT_GALLERY, flat=GRANITE,
         ceiling=GLASS_ROOF, wall=SHOPFRONT)
    for k in range(1, 9):
        floor = STEP * k
        zone(f"z5_gstair_n_{k}", floor, PASSAGE_SKY,
             [(4224, 2496 + STEP_DEPTH * (k - 1), 4352, 2496 + STEP_DEPTH * k)],
             light=LIGHT_GALLERY, flat=GRANITE, ceiling=GLASS_ROOF, wall=STATION_WALL)
        zone(f"z5_gstair_s_{k}", floor, PASSAGE_SKY,
             [(4224, 2176 - STEP_DEPTH * k, 4352, 2176 - STEP_DEPTH * (k - 1))],
             light=LIGHT_GALLERY, flat=GRANITE, ceiling=GLASS_ROOF, wall=STATION_WALL)
    upper = {"u1": ((4384, 2816, 4608, 3008), (4352, 2880, 4384, 2944)),
             "u2": ((4384, 3072, 4608, 3264), (4352, 3136, 4384, 3200)),
             "u3": ((4384, 1600, 4608, 1856), (4352, 1696, 4384, 1760))}
    for s, (room, gap) in upper.items():
        zone(f"z5_shop_{s}", GALLERY, 256, [room], light=LIGHT_SHOP, flat=GRANITE,
             ceiling=CEIL_COFFER, wall=TILE)
        zone(f"z5_shop_{s}_door", GALLERY, 256, [gap], light=LIGHT_SHOP, flat=GRANITE,
             ceiling=CEIL_COFFER, wall=TILE)
    # S2: U2's back wall is crates where the other upper shops show tile; the
    # middle of it is a panel onto the stock room.
    s2_panel = zone("s2_panel", GALLERY, GALLERY, [(4608, 3104, 4624, 3232)], TAG_S2_PANEL,
                    light=LIGHT_SHOP, flat=GRANITE, wall=CRATE)
    zone("s2_store", GALLERY, 256, [(4624, 3040, 4864, 3296)], light=LIGHT_SECRET, flat=GRANITE,
         ceiling=CEIL_COFFER, wall=TILE, special=SECTOR_SPECIAL_SECRET)
    g.style_v(4608, 3072, 3104, LineStyle(texture=CRATE))
    g.style_v(4608, 3232, 3264, LineStyle(texture=CRATE))
    for x in (4608, 4624):
        g.style_v(x, 3104, 3232, secret_panel_style(TAG_S2_PANEL, s2_panel, CRATE))

    # ======================================================================
    # Z6 Red Square
    # ======================================================================
    zone("z6_square", GROUND, SQUARE_SKY, [SQUARE], light=LIGHT_SQUARE, flat=COBBLES,
         ceiling=SKY, wall=CONCRETE)
    sq_x1, sq_y1, sq_x2, sq_y2 = SQUARE
    # The granite lines across the setts (before anything stands on them).
    for n, ly in enumerate(SQUARE_LINES_Y, start=1):
        like("z6_square", f"z6_line_{n}", [(sq_x1, ly, sq_x2, ly + SQUARE_LINE_DEPTH)],
             flat=COBBLES_LINE)
    # The GUM's facade on the square: three storeys of bays, the blue door's
    # portal, the window slits and the portraits' niches cut into it.
    g.style_v(sq_x2, sq_y1, sq_y2, LineStyle(texture=GUM_FACADE))
    # Higher skies round the Spasskaya tower, and the wall's own height in
    # front of its gate.
    tx1, ty1, tx2, ty2 = TOWER
    like("z6_square", "z6_tower_apron", [(tx2, sq_y1, 2048, GATE_Y[0]), (sq_x1, ty2, tx2, GATE_Y[0]),
                                         (sq_x1, sq_y1, tx2, ty1)], ceil=TOWER_APRON_SKY)
    like("z6_square", "z6_gate_apron", [(sq_x1, GATE_Y[0], 1792, GATE_Y[1])], ceil=GATE_APRON_SKY)
    # The Kremlin wall, on the square and down the slope (the vehicle park's
    # west side): the body, and the walk whose face wears the swallowtails
    # (hang_merlons, after the build). Where the parapet over the slope meets
    # it, a solid pier as high as the merlons.
    kx1, kx2 = KREMLIN_STRIP_X
    walk_x = kx2 - WALL_WALK_DEPTH
    spans = ((PARK[1], ty1), (ty2, GATE_Y[0]), (GATE_Y[1], sq_y2))
    block("prop_z6_wall", WALL_WALK, [(kx1, y1, walk_x, y2) for y1, y2 in spans],
          wall=KREMLIN, light=LIGHT_SQUARE)
    zone("prop_z6_wall_walk", WALL_WALK, MERLON_TOP, [(walk_x, y1, kx2, y2) for y1, y2 in spans],
         light=LIGHT_SQUARE, ceiling=SKY, wall=KREMLIN)
    piers = block("prop_z6_wall_piers", MERLON_TOP, [(kx1, PARK[3], kx2, sq_y1)], wall=KREMLIN,
                  light=LIGHT_SQUARE)
    # Two Soviet flags side by side in the crown, where the merlons give
    # way (D119; the occupiers' until then): each on a pier's face, one
    # tile, behind the walk.
    for n, (fy, texture) in enumerate(FLAGS_ON_THE_WALL, start=1):
        zone(f"{PROP_PREFIX}z6_flag_{n}", FLAG_SILL, MERLON_TOP, [(walk_x, fy, kx2, fy + FLAG_WIDTH)],
             light=LIGHT_SQUARE, ceiling=SKY, wall=KREMLIN)
        g.paint(piers, kx1, fy, walk_x, fy + FLAG_WIDTH)
        g.style_v(walk_x, fy, fy + FLAG_WIDTH, LineStyle(texture=texture))
    # The parade's banners on the wall's face, below the walk.
    for by in BANNERS_Y:
        g.style_v(kx2, by, by + BANNER_WIDTH, LineStyle(texture=BANNER))
    # The Spasskaya tower: its stone base, the clock stage (a clock on each
    # face), the green tent and the ruby star on it. The tent is open to the
    # apron's sky in two halves; the line between them carries the star.
    block("prop_z6_tower", TOWER_BASE, [TOWER], wall=SPASSKAYA, light=LIGHT_SQUARE)
    block("prop_z6_tower_mid", TOWER_STAGE, [TOWER_MID], wall=CLOCK, light=LIGHT_SQUARE)
    rx1, ry1, rx2, ry2 = TOWER_TOP
    for name, rect in (("prop_z6_tower_top", (rx1, ry1, RUBY_STAR_X, ry2)),
                       ("prop_z6_tower_top_e", (RUBY_STAR_X, ry1, rx2, ry2))):
        zone(name, TOWER_SPIRE, TOWER_APRON_SKY, [rect], light=LIGHT_SQUARE, ceiling=SKY, wall=STEEL)
    g.style_v(RUBY_STAR_X, ry1, ry2, LineStyle(flags=("blocking",)))
    # The red lock: the Spasskaya gate, in the wall beside the tower.
    zone("z6_red_portal", GROUND, DOOR_HEIGHT, [(kx1, GATE_Y[0], kx2, GATE_Y[1])],
         light=LIGHT_BEACON, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=KREMLIN, extra=RED_LIGHT)
    red_door = door("z8_red_door", GROUND, TAG_RED_DOOR, (1568, GATE_Y[0], kx1, GATE_Y[1]),
                    light=LIGHT_PASSAGE_GATE)
    # The mausoleum, three granite tiers, closed: architecture, nothing else
    # (D12: no fight on it, nothing on it; tested).
    for n, (rect, top) in enumerate(zip(((sq_x1, 2176, 1856, 2432), (sq_x1, 2208, 1824, 2400),
                                         (sq_x1, 2240, 1792, 2368)), MAUSOLEUM), start=1):
        prop("z6_square", f"z6_mausoleum_{n}", rect, top, wall=TRIBUNE, flat=GRANITE)
    # The two reviewing stands either side of it: seven steps up to a top row
    # against the wall. The yellow key lies on the north one's top row.
    for side, (ty_1, ty_2), extra in (("n", TRIBUNE_N_Y, YELLOW_LIGHT), ("s", TRIBUNE_S_Y, {})):
        top_light = LIGHT_BEACON if side == "n" else LIGHT_SQUARE
        zone(f"z6_tribune_{side}_top", STAND_TOP, SQUARE_SKY,
             [(TRIBUNE_X[0], ty_1, TRIBUNE_X[0] + TRIBUNE_TOP_DEPTH, ty_2)], light=top_light,
             flat=GRANITE, ceiling=SKY, wall=TRIBUNE, extra=extra)
        for k in range(1, 8):
            x2 = TRIBUNE_X[1] - STEP_DEPTH * (k - 1)
            zone(f"z6_tribune_{side}_{k}", STEP * k, SQUARE_SKY, [(x2 - STEP_DEPTH, ty_1, x2, ty_2)],
                 light=LIGHT_SQUARE, flat=GRANITE, ceiling=SKY, wall=TRIBUNE)
    # The parade, halted: armour plate (dress_carriers puts the star on the
    # missile carriers' flanks after the build).
    carriers: dict[int, tuple[int, int, int, int]] = {}
    for name, hull, deck, top, top_h in VEHICLES:
        room = "z7_park" if name.startswith("p") else "z6_square"
        if room == "z7_park":
            continue    # below, once the park exists
        index = prop(room, f"z6_vehicle_{name}", hull, deck, wall=ARMOUR, flat=PLATE)
        if deck == CARRIER_HULL:
            carriers[index] = hull
        if top:
            prop(room, f"z6_vehicle_{name}_top", top, top_h, wall=ARMOUR, flat=PLATE)
    # Minin and Pozharsky: bronze on a granite plinth, at the square's south end.
    prop("z6_square", "z6_minin_plinth", (3136, 1344, 3264, 1408), MININ_PLINTH, wall=TRIBUNE,
         flat=GRANITE)
    prop("z6_square", "z6_minin", (3168, 1360, 3232, 1392), MININ_BRONZE, wall=BRASS, flat=GRANITE)
    # The parade portraits on the GUM's facade, raised over the cobbles.
    for who, (py1, py2) in PORTRAIT_NICHES.items():
        like("z6_square", f"{PROP_PREFIX}z6_portrait_{who}", [(sq_x2, py1, sq_x2 + NICHE_DEPTH, py2)],
             floor=GROUND + PORTRAIT_SILL, ceil=GROUND + PORTRAIT_SILL + POSTER_HEIGHT,
             ceiling=CEIL_CONCRETE, flat=GRANITE)
    # The Historical Museum's red brick with its white dressings, and its two
    # closets: their shut leaves are the museum's own wall (the ambush).
    g.style_h(sq_y2, MUSEUM_X[0], MUSEUM_X[1], LineStyle(texture=MUSEUM))
    for name, (cx1, cx2) in CLOSETS.items():
        zone(f"{name}_door", GROUND, GROUND, [(cx1, sq_y2, cx2, sq_y2 + NICHE_DEPTH)], TAG_AMBUSH,
             light=LIGHT_CLOSET, wall=MUSEUM)
        zone(name, GROUND, GROUND + CLOSET_HEIGHT, [(cx1, sq_y2 + NICHE_DEPTH, cx2, 3584)],
             light=LIGHT_CLOSET, wall=BRICK)
    # The yellow lock: the gatehouse at the square's south end (its face is
    # the square's wall, 384 high), one tile high portals both sides.
    gx1, gx2 = YELLOW_GATE_X
    zone("z6_yellow_portal", GROUND, DOOR_HEIGHT, [(gx1, 1120, gx2, sq_y1)], light=LIGHT_BEACON,
         flat=GRANITE, ceiling=CEIL_CONCRETE, wall=CONCRETE, extra=YELLOW_LIGHT)
    yellow_door = door("z7_yellow_door", GROUND, TAG_YELLOW_DOOR, (gx1, 1088, gx2, 1120),
                       light=LIGHT_PARK)
    # The parapet over the slope: the vehicle park is seen across it.
    block("prop_z6_parapet", PARAPET, [(sq_x1, PARK[3], GATEHOUSE[0], sq_y1)], wall=BRICK_DADO,
          light=LIGHT_SQUARE)

    # ======================================================================
    # Z7 The vehicle park on the slope (Vasilyevsky spusk)
    # ======================================================================
    zone("z7_park", GROUND, SQUARE_SKY, [PARK], light=LIGHT_PARK, flat=FLOOR_ASPHALT,
         ceiling=SKY, wall=CONCRETE)
    zone("z7_porch", GROUND, DOOR_HEIGHT, [(gx1, 1024, gx2, PARK[3])], light=LIGHT_PARK,
         flat=FLOOR_ASPHALT, ceiling=CEIL_CONCRETE, wall=CONCRETE)
    for name, hull, deck, top, top_h in VEHICLES:
        if not name.startswith("p"):
            continue
        index = prop("z7_park", f"z7_vehicle_{name}", hull, deck, wall=ARMOUR, flat=PLATE)
        if deck == CARRIER_HULL:
            carriers[index] = hull
        if top:
            prop("z7_park", f"z7_vehicle_{name}_top", top, top_h, wall=ARMOUR, flat=PLATE)
    zone("z7_pedestal", GROUND + STEP, SQUARE_SKY, [(2112, 640, 2240, 768)], light=LIGHT_BEACON,
         flat=PLATE, ceiling=SKY, wall=STEEL, extra=RED_LIGHT)

    # ======================================================================
    # Z8 The Spasskaya gate's passage, Z9 the Kremlin courtyard, Z10 the exit
    # ======================================================================
    zone("z8_passage", GROUND, DOOR_HEIGHT, [(ARENA_STRIP_X[1], GATE_Y[0], 1568, GATE_Y[1])],
         light=LIGHT_PASSAGE_GATE, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=KREMLIN)
    ax1, ay1, ax2, ay2 = ARENA
    zone("z9_arena", GROUND, ARENA_SKY, [ARENA], light=LIGHT_ARENA, flat=COBBLES, ceiling=SKY,
         wall=BRICK)
    zone("z9_gate_apron", GROUND, GATE_APRON_SKY, [(ARENA_STRIP_X[0], GATE_Y[0], ARENA_STRIP_X[1], GATE_Y[1])],
         light=LIGHT_ARENA, flat=COBBLES, ceiling=SKY, wall=KREMLIN)
    # The Kremlin wall from inside: its walk on the courtyard's side, the
    # body behind; two piers as high as the merlons flank the gate's passage.
    zx1, zx2 = ARENA_STRIP_X
    zwalk_x = zx1 + WALL_WALK_DEPTH
    zspans = ((ay1, GATE_Y[0] - WALL_WALK_DEPTH), (GATE_Y[1] + WALL_WALK_DEPTH, ay2))
    zone("prop_z9_wall_walk", WALL_WALK, MERLON_TOP, [(zx1, y1, zwalk_x, y2) for y1, y2 in zspans],
         light=LIGHT_ARENA, ceiling=SKY, wall=KREMLIN)
    block("prop_z9_wall", WALL_WALK, [(zwalk_x, y1, zx2, y2) for y1, y2 in zspans],
          wall=KREMLIN, light=LIGHT_ARENA)
    block("prop_z9_wall_piers", MERLON_TOP, [(zx1, GATE_Y[0] - WALL_WALK_DEPTH, zx2, GATE_Y[0]),
                                            (zx1, GATE_Y[1], zx2, GATE_Y[1] + WALL_WALK_DEPTH)],
          wall=KREMLIN, light=LIGHT_ARENA)
    zone("z9_dais_1", GROUND + DAIS, ARENA_SKY, [(832, 1408, 1088, 1664)], light=LIGHT_ARENA,
         flat=GRANITE_CHECK, ceiling=SKY, wall=MARBLE)
    zone("z9_dais_2", GROUND + 2 * DAIS, ARENA_SKY, [(896, 1472, 1024, 1600)], light=LIGHT_ARENA,
         flat=GRANITE_CHECK, ceiling=SKY, wall=MARBLE)
    # The Tsar Bell and the Tsar Cannon (bronze, the Kremlin's own), and four columns.
    prop("z9_arena", "z9_tsar_bell", (640, 1792, 768, 1920), BELL, wall=BRASS)
    prop("z9_arena", "z9_tsar_cannon", (1024, 960, 1280, 1024), CANNON, wall=BRASS)
    for cx, cy in ARENA_COLUMNS:
        g.carve(cx, cy, cx + 64, cy + 64)
    for n, (fx, texture) in enumerate(((768, FLAG_USSR), (896, FLAG_STANDARD)), start=1):
        recess("z9_arena", f"z9_flag_{n}", (fx, ay2, fx + 64, ay2 + NICHE_DEPTH),
               ceil=GROUND + TILE_SIZE, back=("h", ay2 + NICHE_DEPTH, fx, fx + 64), texture=texture)
    for who, (px1, px2) in COURTYARD_PORTRAITS.items():
        like("z9_arena", f"z9_portrait_{who}", [(px1, ay2, px2, ay2 + NICHE_DEPTH)],
             ceil=GROUND + POSTER_HEIGHT, ceiling=CEIL_CONCRETE)
    zone("z9_exit_porch", GROUND, DOOR_HEIGHT, [(448, EXIT_Y[0], ax1, EXIT_Y[1])],
         light=LIGHT_ARENA, flat=GRANITE, ceiling=CEIL_CONCRETE, wall=BRICK)
    exit_gate = door("z10_gate", GROUND, TAG_BOSS_EXIT, (416, EXIT_Y[0], 448, EXIT_Y[1]),
                     light=LIGHT_EXIT_HALL)
    zone("z10_hall", GROUND, DOOR_HEIGHT, [(192, EXIT_Y[0], 416, EXIT_Y[1])],
         light=LIGHT_EXIT_HALL, flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=STATION_WALL)
    zone("z10_exit_niche", GROUND, GROUND + SWITCH_HEIGHT, [(176, 1504, 192, 1568)],
         light=LIGHT_BEACON, flat=GRANITE_CHECK, ceiling=CEIL_COFFER, wall=STEEL)

    # ======================================================================
    # Line styles: the three locks, the exit gate, the exit
    # ======================================================================
    for x in (3488, 3520):
        g.style_v(x, 2304, 2432, locked_door_style(TAG_BLUE_DOOR, blue_door, LOCK_BLUE_CARD,
                                                   texture=DOOR_BLUE))
    g.style_v(3520, 2176, 2304, LineStyle(texture=MOSAIC))
    g.style_v(3520, 2432, 2560, LineStyle(texture=MOSAIC))
    for y in (1088, 1120):
        g.style_h(y, gx1, gx2, locked_door_style(TAG_YELLOW_DOOR, yellow_door, LOCK_YELLOW_CARD,
                                                 texture=DOOR_YELLOW))
    for x in (1568, kx1):
        g.style_v(x, GATE_Y[0], GATE_Y[1], locked_door_style(TAG_RED_DOOR, red_door, LOCK_RED_CARD,
                                                             texture=DOOR_RED))
    # The exit gate: a shut gate on both faces, no special on either, so
    # pressing it does nothing and only the boss's death opens it.
    for x in (416, 448):
        g.style_v(x, EXIT_Y[0], EXIT_Y[1], remote_door_style(exit_gate, texture=GATE))
    g.style_v(176, 1504, 1568, exit_switch_style(texture=EXIT_FACE))

    g.build()

    # Middle textures and offsets, on the built lines.
    hang_merlons(tm, {plan["prop_z6_wall_walk"], plan["prop_z9_wall_walk"]},
                 (KREMLIN_STRIP_X[1], ARENA_STRIP_X[0]))
    dress_carriers(tm, carriers)
    hang_the_ruby_star(tm, plan)
    dress_shopfronts(tm)
    align_to_world(tm)

    # Things.
    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=BLUE_KEY_SPOT[0], y=BLUE_KEY_SPOT[1], type=ED_BLUE_CARD))
    for ednum, (x, y) in ((ED_YELLOW_CARD, YELLOW_KEY_SPOT), (ED_RED_CARD, RED_KEY_SPOT)):
        tm.add_thing(Thing(x=x, y=y, type=ednum, extra=EVENTS.special_fields(*PICKUP_SPECIALS[ednum])))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        extra = {}
        if (x, y) == MAP06_BOSS_SPOT and kind == BOSS_KIND:
            special, args = BOSS_DEATH_SPECIAL
            extra = {"special": special, **{f"arg{i}": a for i, a in enumerate(args)}}
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle,
                                     extra=extra))
    for _zone, ednum, x, y, top in ITEMS + SECRET_ITEMS:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(highest=top)))
    for _zone, ednum, x, y, low, high in AMMO:
        tm.add_thing(Thing.on_skills(x, y, ednum, skill_tier(low, high)))
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
WALL_TEXTURES = ((CONCRETE, STEEL, CRATE, LONG_CRATE, TILE, MARBLE, STATION_WALL, MOSAIC,
                 BRASS, TUBBING, PLATFORM_FACE, BRICK, BRICK_DADO, FLAG_USSR,
                 FLAG_STANDARD, LENIN, STALIN, KREMLIN, MERLON, GUM_FACADE, TRIBUNE, BANNER,
                 SPASSKAYA, ARMOUR_STAR, ARMOUR, CLOCK, RUBY_STAR, MUSEUM, FLAG_GONFALON_KREMLIN,
                 FLAG_TORN_KREMLIN) + SHOPFRONTS + DOOR_LEAVES + SWITCH_FACES
                 + MARX_ENGELS)
FLAT_TEXTURES = (FLOOR_ASPHALT, CEIL_CONCRETE, CRATE_TOP, GRANITE, GRANITE_CHECK, PLATFORM_EDGE,
                 RAILS, CEIL_COFFER, CEIL_LAMP, PLATE, COBBLES, COBBLES_LINE, GLASS_ROOF, SKY)
