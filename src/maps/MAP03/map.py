"""MAP03 "Tankograd", the tractor factory - v1.1: v1 plus D68's three points.

Design document: docs/levels/MAP03-factory.md (section 15 is v1, section 16
is v1.1).
LORE's third map and the episode's climax ("Tractor factory (actually
tanks) - episode climax: the portal"). Built as MAP04 while MAP02 was the
practice range (D41); MAP03 since D62 (2026-10-14), and named Tankograd by
the CEO (D63). The player arrives where MAP02 left him: on rails, out of the
westbound tunnel, into the factory's goods spur.

What v0 was (design document section 14): the whole floor plan, walkable
from start to exit, with the keys IN PLAIN SIGHT on the route (MAP02's
lesson, D58), each on a lit pedestal in its key's colour (sector
`lightcolor`), light 192 spent on the two locks, the two keys and the exit.

What v1 adds (section 15, D60 "MVP first": complete and playable, balance
later), the way MAP02's v1 did it (MAP02 section 16):

* the Tankograd set (D66) where the design asked for it: soot brick and its
  whitewashed dado, corrugated rust on the tank line, chequer plate,
  grating, the molten channel, key-trimmed door leaves, the portal's cobalt
  field, the shut factory gates, clerestory glazing, the two flags at the
  drum, the works banner over the factory floor and chains over the pits;
* the red lock no longer wears red star plaques either side of it (the
  art-director's note: they camouflaged the red leaf); the yellow lock keeps
  its pair;
* section 9's population on the bestiary's own editor numbers (MAPINFO
  DoomEdNums 21100-21107), the General (21106) in the portal hall on every
  skill, both factions as D35 has the factory, two monster closets in the
  assembly hall on SW-A's tag, and the weapons, ammunition and health of
  G3-8's budget.

The route, in one line: goods spur -> dock -> assembly hall (both locked
doors seen at once: red at the west end, yellow in the south wall; the
yellow key seen up the office stair) -> offices, the YELLOW KEY on the
director's desk -> yellow door -> tank line -> foundry, the RED KEY on the
casting platform, and SW-A, which opens a shutter straight back into the
hall beside the red door (and the hall's two closets) -> red door -> portal
hall, the General -> control booth, SW-B, which opens the containment drum's
gate -> the portal, and the exit breaker at the top of its dais.

What v1.1 adds (section 16, D68, the CEO on open points 7, 8 and 4):

* S1, the design's first secret (section 8), with the Hand Katyusha in it:
  a row of four lockers on the archive's east wall, one set back in shadow;
  pushed, it opens for good onto a passage and a store room (sector special
  1024, counted as a secret);
* the molten channel hurts, by the UDMF sector fields `damageamount` and
  `damageinterval` (10 every 32 tics, Doom's hellslime); it is 16 deep, a
  step, open on every side;
* the General's death opens his stores: his thing carries the special
  Door_Open on a new tag, 12, and a steel shutter in the portal hall's north
  wall rises when he dies, onto health, ammunition and armour. Nothing else
  opens that tag, and the exit still depends on SW-B alone.

Geometry is painted with `GridMap` (tools/sdbuild/udmf.py), MAP01's method.

Run it (the PM or the CEO; agents never start GZDoom, D26):
    python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP03 SKILL=3 tools/run.sh
Since D62 MAPINFO wires it in (design document section 11): the metro's
exit leads here, and this map's exit ends the episode (cluster 1).
"""

from __future__ import annotations

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
    door_raise_style,
    exit_switch_style,
    remote_door_style,
    skill_tier,
    switch_door_open_style,
)

MAP_NAME = "MAP03"

# --- The approved sets (docs/art/TEXTURE-INDEX.md) ---------------------------
# The Soviet base set and the metro's tubbing, kept where v0 had them right.
CONCRETE = "SDCONC1"    # 64x128 prefab panels: the inspection pits
STAR = "SDSTAR1"        # 128x128 star plaque: either side of the YELLOW door only (v1)
STEEL = "SDSTEL1"       # green riveted plate: drum, booth, shutter, conveyors, pedestal
TILE_DADO = "SDTILE2"   # 64x128 tile over a green dado: the offices
CRATE = "SDCRAT1"       # 64x64 crate face: the director's desk front
DOOR = "SDDOOR1"        # 128x128 door leaf: D1, D2, the drum's gate
TUBBING = "SDTUBB1"     # 128x128 metro tubbing: the goods spur MAP02's tunnel ran into
FLOOR_LANE = "SDFLR1"   # hangar concrete with a yellow lane line along the image's y
FLOOR_CONCRETE = "SDFLR2"
FLOOR_TILE = "SDFLR3"
CEIL_PANEL = "SDCEIL1"  # lit panel
CEIL_CONCRETE = "SDCEIL2"
DESK_TOP = "SDCRTOP1"   # crate lid, planks: the desk's top
RAILS = "SDRAIL1"       # metro track bed, rails along the image's y
LOCKER = "SDLOCK1"      # 64x128 barracks locker (D29), one per 64 of wall: the archive's row (v1.1, S1)

# Tankograd (batch 4, D66: "Me gustan TODAS"), assets/textures/factory and
# assets/flats/factory. Animated lumps are placed by their first frame;
# src/lumps/ANIMDEFS cycles SDMOLT1-4 and SDPORT1-4 (mod-engineer's, N6c).
BRICK = "SDBRCK1"       # 64x128 soot-stained works brick: dock, hall, foundry, portal hall
BRICK_DADO = "SDBRCK2"  # 64x128 the same brick whitewashed to 64: only on walls 128 high
RUST = "SDRUST1"        # 64x128 rusted corrugated sheet: the closed shop (tank line)
DOOR_YELLOW = "SDDOORY"  # 128x128 SDDOOR1 with the yellow lock's trim and pass plate
DOOR_RED = "SDDOORR"    # 128x128 SDDOOR1 with the red lock's trim and pass plate
PORTAL = "SDPORT1"      # 128x128 the portal's cobalt field, frame 1 of SDPORT1-4
ROAD_GATE = "SDGATE1"   # 128x128 sliding factory gate, shut: set dressing in two recesses
WINDOW = "SDWIND1"      # 64x128 industrial glazing at night: the hall's clerestory
FLAG_REICH = "SDFLAG1"  # 64x128 the Fourth Reich's banner on brick
FLAG_LEGION = "SDFLAG2"  # 64x128 the Liberty Legion's banner on brick
FLOOR_PLATE = "SDFLR4"  # 64x64 cast-iron chequer plate
GRATING = "SDGRAT1"     # 64x64 steel bar grating: the foundry gallery
MOLTEN = "SDMOLT1"      # 64x64 molten metal, frame 1 of SDMOLT1-4: the channel
# The two pieces of batch 4 that were held in work/ until the validators
# accepted a masked RGBA wall and a 256x64 wall (installed in N6b). Set
# either to None to build without it; every use below is guarded.
CHAIN: str | None = "SDCHAN1"    # 64x128 masked: chain and hook, mid-texture over the pits
SLOGAN: str | None = "SDSLOG1"   # 256x64 the works banner, mid-texture over the hall
SLOGAN_SIZE = (256, 64)

HALL_WALL = BRICK       # what the hall's walls (and the shutter from the hall) wear

# --- The posters (CEO 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py, design section 17) --------------
LENIN = "SDPOSTR1"      # 128x256 Lenin poster «ЛЕНИН ЖИВ»
STALIN = "SDPOSTR3"     # 128x256 Stalin poster «СЛАВА СТАЛИНУ!» (D55)
MURAL = "SDPOSTR2"      # 128x128 cosmonautics mural
POSTER_WIDTH = 128
POSTER_HEIGHT = 256     # Lenin, Stalin and (commissioned at the same size) Marx-Engels
MURAL_HEIGHT = 128
# The Marx-Engels poster SDPOSTR4 is in preparation and is not a lump yet.
# Its slots are built and wear a Lenin or a Stalin; approving it is this line:
MARX_ENGELS: str | None = None   # -> "SDPOSTR4"
# The assembly hall is 320 high: its two portraits hang at the back of
# niches 16 deep and exactly POSTER_HEIGHT high, one either side of the red
# door's portal in the hall's west wall, the wall a player faces from the
# arch (the flags' and the gates' recess pattern). Symmetric about the
# door's axis, y 1184, 96 clear of the portal band so the red leaf stays
# the only red thing at the end of the hall (section 15.2).
POSTER_NICHE_DEPTH = 16
POSTER_NICHES = {
    "z3_poster_s": (1600 - POSTER_NICHE_DEPTH, 768, 1600, 896),
    "z3_poster_n": (1600 - POSTER_NICHE_DEPTH, 1472, 1600, 1600),
}
# Every picture: (name, texture, axis, coord, lo, hi), one GridMap style.
POSTERS = (
    # The dock, 256 high: the two flank the arch into the hall, the first
    # thing the player sees coming off the spur (he arrives facing west).
    ("dock_lenin", LENIN, "v", 3136, 960, 1088),
    ("dock_slot_n", STALIN, "v", 3136, 1280, 1408),
    # The assembly hall, either side of the red door: the works' red corner,
    # now under the Legion's guns.
    ("hall_stalin", STALIN, "v", 1600 - POSTER_NICHE_DEPTH, 1472, 1600),
    ("hall_slot_s", LENIN, "v", 1600 - POSTER_NICHE_DEPTH, 768, 896),
    # The director's office is 128 high, so the portrait design section 7.1
    # wanted behind his desk cannot hang whole there: the mural does, on
    # the north wall, centred behind the desk where the yellow key lies.
    ("director_mural", MURAL, "h", 2208, 2240, 2368),
)
POSTER_SLOTS_MARX_ENGELS = ("dock_slot_n", "hall_slot_s")


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """POSTERS with each Marx-Engels slot wearing SDPOSTR4 once it exists."""
    return tuple((name, MARX_ENGELS if MARX_ENGELS and name in POSTER_SLOTS_MARX_ENGELS else texture,
                  axis, coord, lo, hi) for name, texture, axis, coord, lo, hi in POSTERS)

# Switches (D25), one variant per switch. The exit keeps the hazard panel it
# wears on MAP01, the range and MAP02: the same face, the same meaning.
SW_A_FACE = "SDSW1B"    # foundry: push button, opens the shutter into the hall
SW_B_FACE = "SDSW1A"    # control booth: the knife switch, opens the drum's gate
EXIT_FACE = "SDSW1D"    # hazard panel at the top of the portal's dais
SWITCH_FACES = (SW_A_FACE, SW_B_FACE, EXIT_FACE)
SWITCH_WIDTH = 64       # every SDSW1x is 64x128
SWITCH_HEIGHT = 128
PLAQUE = 128            # SDSTAR1 is 128x128
TILE = 128              # SDDOORx, SDGATE1, SDPORT1: 128 square; the walls are 128 high
DOOR_LEAVES = (DOOR, DOOR_YELLOW, DOOR_RED)

# --- Specials and keys -------------------------------------------------------
# Door_LockedRaise (tag, speed, delay, lock, lighttag): 13, VERIFIED in engine
# on MAP02 (docs/qa/evidence/2026-10-14_1902_F3_map03-v0-walk.md: without the
# key the door printed its lock line; with it, it opened and stayed open).
# Delay 0 = opens and stays open, so a key gate can never be consumed.
SPECIAL_DOOR_LOCKED_RAISE = 13
# Lock numbers read from shipped text, gzdoom.pk3 g4.14.2 -> lockdefs.txt:
# `Lock 1 Doom { RedCard ... }`, `Lock 3 Doom { YellowCard ... }`.
LOCK_RED_CARD = 1
LOCK_YELLOW_CARD = 3
# Doom's editor numbers; Freedoom draws them until we have our own keys.
ED_YELLOW_CARD = 6
ED_RED_CARD = 13
KEY_LOCKS = {ED_YELLOW_CARD: LOCK_YELLOW_CARD, ED_RED_CARD: LOCK_RED_CARD}

ED_PLAYER1_START = 1

# --- Heights ----------------------------------------------------------------
GROUND = 0              # dock, hall, tank line, foundry gallery, portal hall
OFFICES = 64            # the office floor, four steps up from the hall
FOUNDRY_PIT = -64       # the casting floor, four steps down from the gallery
CHANNEL = FOUNDRY_PIT - 16   # the molten channel in the casting floor
TANK_PIT = -48          # the inspection pits under the tank line
STEP = 16               # every stair step; under MAX_STEP_UP 24
DESK = 16               # the desk and the ingot pedestal: one step up
CONVEYOR = 32           # the assembly lines: waist high, cover, not a step
DOOR_HEIGHT = 128       # SDDOOR1 is 128x128: every leaf is one tile high
SPUR_CEIL = GROUND + 128        # tubbing: one tile, as in MAP02's tunnels
DOCK_CEIL = 256
HALL_CEIL = 320
OFFICE_CEIL = OFFICES + DOOR_HEIGHT     # 192
LINE_CEIL = 256
FOUNDRY_CEIL = 256
PORTAL_HALL_CEIL = 384
DRUM_CEIL = 256
NICHE_DEPTH = 16
CLERESTORY_SILL = HALL_CEIL - TILE      # 192: one SDWIND1 tile under the roof
CLOSET_HEIGHT = 128     # a monster closet: one panel high, as on MAP01 and MAP02

# --- Light ---------------------------------------------------------------------
# 192 is spent on five places only: the two locks, the two keys and the exit
# (MAP02 v1's rule: the brightest things in a map are where it wants the
# player to look). v2 is the light pass (glow, flicker, the portal's light).
LIGHT_MIN = 96
LIGHT_MAX = 192
LIGHT_BEACON = LIGHT_MAX
LIGHT_SPUR = 112
LIGHT_DOCK = 144
LIGHT_HALL = 160
LIGHT_OFFICES = 128
LIGHT_DIRECTOR = 176    # the key's room: one step under the beacon
LIGHT_LINE = 144
LIGHT_VESTIBULE = 128
LIGHT_FOUNDRY = 128     # v2: the glow of the channel and the furnaces
LIGHT_GALLERY = 144
LIGHT_ANTE = 128
LIGHT_PORTAL_HALL = 128
LIGHT_BOOTH = 144
LIGHT_DRUM = 144
LIGHT_CLOSET = 112      # inside a monster closet: unlit storage (MAP01's value)
LIGHT_S1_NICHE = LIGHT_MIN   # the set-back locker: the one in shadow (S1's clue, v1.1)
LIGHT_SECRET = 112      # S1's passage and store (MAP02's value)
LIGHT_STORES = 144      # the General's stores, once open: lit, but not a beacon
BEACON_ZONES = ("z3_red_portal", "z3_yellow_portal", "o_desk", "f_pedestal", "p_exit_niche")

# The keys' colours, in light: sector field `lightcolor` (0xRRGGBB) of the
# UDMF zdoom namespace, as MAP02 v1 uses it for the blue pass. On the portal
# round each locked door AND on the place its key lies: the colour of the
# lock is the colour of where the key is. NOT VERIFIED in our engine runs
# (checklist K4); if the engine ignored it, both places would still be 192s.
YELLOW = 0xFFD860
RED = 0xFF6048
YELLOW_LIGHT = {"lightcolor": YELLOW}
RED_LIGHT = {"lightcolor": RED}

# --- Tags --------------------------------------------------------------------
TAG_D1_PLANNING = 1
TAG_D2_ARCHIVE = 2
TAG_YELLOW_DOOR = 4      # the tank line: Door_LockedRaise, lock 3
TAG_RED_DOOR = 5         # the portal shop: Door_LockedRaise, lock 1
TAG_SHUTTER = 10         # SW-A: the foundry's shutter into the hall, and the hall's closets
TAG_GATE = 11            # SW-B: the containment drum's gate
# The closets ride SW-A's own tag (MAP01 v3, MAP02 v1): one line, one special.
TAG_HALL_AMBUSH = TAG_SHUTTER
TAG_S1_PANEL = 6         # v1.1: S1's locker panel (Door_Open, pushed, opens for good)
TAG_GENERAL_STORES = 12  # v1.1: the General's stores; ONLY his death opens it (no line carries it)

# --- Things --------------------------------------------------------------------
PLAYER_START = (4096, 1184)
PLAYER_ANGLE = 180       # facing west, down the spur, into the factory
YELLOW_KEY_SPOT = (2304, 2048)   # on the director's desk
RED_KEY_SPOT = (512, 352)        # on the ingot pedestal, casting platform
KEY_ZONES = {ED_YELLOW_CARD: "o_desk", ED_RED_CARD: "f_pedestal"}
LOCK_PORTALS = {LOCK_YELLOW_CARD: "z3_yellow_portal", LOCK_RED_CARD: "z3_red_portal"}

# Zone-name families the tests use.
PROP_PREFIX = "prop_"            # unwalkable by design (the conveyors, the clerestory sills)
WINDOWS: tuple[str, ...] = ()    # nothing is seen through and never walked
SECRET_ZONES: tuple[str, ...] = ("s1_store",)   # v1.1: S1 (D68); S2 and S3 stay v3's (section 8)
REWARD_ZONES: tuple[str, ...] = ("p_stores",)   # v1.1: opened by the General's death only (D68)
CLOSET_PREFIX = "closet_"

# The assembly hall's two lines, split by the centre aisle the lane runs up.
CONVEYOR_ROWS = ((896, 960), (1408, 1472))
CONVEYOR_RUNS = ((1792, 2240), (2368, 2880))
LANE_X = (2272, 2336)            # the yellow lane: yellow door -> office stair
# The clerestory: 64-wide windows in the hall's long walls, east of the
# office stair, each a sill 16 deep at CLERESTORY_SILL with the glazing on
# its back wall: brick below, one pane tile above.
CLERESTORY_NORTH = (2432, 2560, 2688, 2816, 2944)    # x of each window, y 1664
CLERESTORY_SOUTH = (2560, 2688, 2816, 2944)          # x of each window, y 704
# The works banner hangs from the hall's roof across its axis, between the
# arch and the red door: a 16-deep strip, the banner on both long faces.
BANNER = (2624, 1056, 2640, 1312)
# A chain and hook over the middle of each inspection pit.
HOISTS = {"t_pit_a": (2592, 224, 2656, 288), "t_pit_b": (3040, 224, 3104, 288)}

# --- v1.1 (D68) ----------------------------------------------------------------
# S1 (design section 8): a row of four lockers fills the archive's east wall
# (x 2752, y 1952..2208). The third from the south stands NICHE_DEPTH back,
# in shadow: the comparison is the clue. It is a push panel that opens for
# good onto a passage and the store where the Hand Katyusha lies.
LOCKER_ROW = (2752, 1952, 2208)                 # x, y1, y2: four SDLOCK1 tiles
LOCKER_WIDTH = 64
S1_NICHE = (2752, 2080, 2768, 2144)
S1_PANEL = (2768, 2080, 2784, 2144)
S1_PASSAGE = (2784, 2080, 2848, 2144)
S1_STORE = (2848, 1984, 3040, 2240)
# The molten channel's damage: UDMF zdoom sector fields, VERIFIED in the
# spec (design section 16.2). 10 every 32 tics is Doom's hellslime (type 5):
# twice nukage, half super hellslime; about 19 HP a second standing in it.
CHANNEL_DAMAGE = 10
CHANNEL_DAMAGE_INTERVAL = 32    # tics: Doom's own sector-damage period (also the field's default)
CHANNEL_HURTS = {"damageamount": CHANNEL_DAMAGE, "damageinterval": CHANNEL_DAMAGE_INTERVAL}
# The General's stores: a steel shutter in the portal hall's north wall, in
# a porch one tile high, and a room behind it. His thing special opens it
# when he dies (UDMF thing `special` + `arg0..4`; GZDoom runs a monster's
# special in AActor::Die, design section 16.3).
STORES_PORCH = (640, 1664, 768, 1696)
STORES_DOOR = (640, 1696, 768, 1728)
STORES = (576, 1728, 832, 1920)
GENERAL_DEATH_SPECIAL = (SPECIAL_DOOR_OPEN, (TAG_GENERAL_STORES, DOOR_SPEED_SLOW, 0, 0, 0))

# --- Editor numbers (src/lumps/MAPINFO, DoomEdNums) ---------------------------
# The bestiary's own numbers (21100-21107, BESTIARY 2.5), as MAP02 places
# them; each class also `replaces` its Doom twin.
ED_RIFLEMAN = 21100       # SD_ReichRifleman, Reich, 20 HP
ED_TROOPER = 21101        # SD_LegionTrooper, Legion, 30 HP
ED_STORMTROOPER = 21102   # SD_Stormtrooper, both factions, 60 HP
ED_HOUND = 21103          # SD_ReichHound, Reich, 150 HP
ED_DOUGHBOY = 21104       # SD_Doughboy, Legion, 400 HP
ED_PANZERMENSCH = 21105   # SD_Panzermensch, Reich, 500 HP
ED_GENERAL = 21106        # SD_General, Legion, 3000 HP: the episode's boss
ED_PANZER_HEAVY = 21107   # SD_PanzermenschSchwer, Reich, 1000 HP
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
# Where each faction stands (D35: the factory MIXES, both flags side by
# side). The Legion holds the works' public face, the Reich the yards and the
# closed shop; both meet in the foundry and both guard the portal under the
# General. Stormtroopers are hybrids and stand anywhere; the closets are the
# counter-attack, not a garrison.
LEGION_GROUND = ("z3_", "o_")
REICH_GROUND = ("z1_", "z2_", "rails_", "t_")
BOTH_GROUND = ("f_", "p_")
# The arsenal (MAPINFO DoomEdNums, 21000-21019).
ED_IZH = 21003
ED_PPSH = 21004
ED_RPG7 = 21005
ED_ROKS3 = 21006
ROUTE_WEAPONS = (ED_IZH, ED_PPSH, ED_RPG7, ED_ROKS3)
ED_HAND_KATYUSHA = 21007  # SD_HandKatyusha, slot 7: in S1 only (D68), never on the route
# Ammo, health and armour: Doom's numbers, which our classes replace
# (src/zscript/sd/ammo.zs; MOD-SPEC 6.4), as on MAP01 and MAP02.
ED_CLIP = 2007            # 10 rounds of 7.62x25
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

# Design section 9: monsters per skill, Doom's skill pairs (udmf.skill_tier).
ENEMY_TOTALS = {2: 25, 3: 38, 4: 52}

# Every monster: (zone, kind, x, y, facing, lowest skill tier). Tier 2 is on
# every skill, 3 from medium up, 4 on hard only. Section 9's table, placed
# (section 15.4 for the cells v1 changed). Facing: 0 east, 90 north, 180
# west, 270 south; most face where the player comes from.
MONSTERS = (
    # The dock: the Reich's picket on the yard, facing the spur.
    ("z2_dock", "rifleman", 3300, 1000, 0, 2),
    ("z2_dock", "rifleman", 3300, 1380, 0, 2),
    ("z2_dock", "rifleman", 3200, 1184, 0, 3),
    ("z2_dock", "rifleman", 3450, 960, 0, 4),
    # The assembly hall, the big fight on the factory floor: the Legion
    # between the lines, facing the arch.
    ("z3_hall", "trooper", 1900, 1100, 0, 2),
    ("z3_hall", "trooper", 2500, 1100, 0, 2),
    ("z3_hall", "trooper", 2000, 1550, 0, 2),
    ("z3_hall", "trooper", 2700, 1550, 0, 2),
    ("z3_hall", "trooper", 1750, 800, 0, 2),
    ("z3_hall", "trooper", 2700, 800, 0, 2),
    ("z3_hall", "stormtrooper", 2150, 1250, 0, 2),
    ("z3_hall", "trooper", 2850, 1184, 0, 3),
    ("z3_hall", "trooper", 1800, 1300, 0, 3),
    ("z3_hall", "stormtrooper", 2450, 1300, 0, 3),
    ("z3_hall", "trooper", 2950, 900, 0, 4),
    ("z3_hall", "trooper", 2950, 1450, 0, 4),
    ("z3_hall", "stormtrooper", 1700, 1550, 0, 4),
    # The offices: close quarters upstairs.
    ("o_corridor", "trooper", 2000, 1856, 0, 2),
    ("o_corridor", "trooper", 2600, 1856, 180, 2),
    ("o_director", "trooper", 2300, 2150, 270, 2),
    ("o_planning", "trooper", 1984, 2080, 270, 3),
    ("o_archive", "stormtrooper", 2624, 2080, 270, 4),
    # The tank line, the closed shop: the Reich at work; the Panzermensch at
    # the pouring arch on every skill, the heavy at the export gate on 4.
    ("t_line", "panzermensch", 2000, 256, 0, 2),
    ("t_line", "hound", 2600, 400, 180, 2),
    ("t_line", "rifleman", 2900, 120, 180, 2),
    ("t_line", "rifleman", 3100, 400, 180, 2),
    ("t_line", "hound", 3200, 120, 180, 3),
    ("t_line", "rifleman", 2200, 120, 90, 3),
    ("t_line", "rifleman", 2150, 400, 0, 3),
    ("t_line", "rifleman", 2700, 120, 180, 4),
    ("t_line", "heavy", 3290, 256, 180, 4),
    # The foundry, where the two meet: the Legion's Doughboys in the tall
    # room over the casting floor, hybrids on the gallery, a hound on 4.
    ("f_floor", "doughboy", 1000, 400, 0, 2),
    ("f_gallery", "stormtrooper", 1600, 500, 0, 2),
    ("f_floor", "stormtrooper", 900, 560, 0, 2),
    ("f_floor", "stormtrooper", 800, 300, 0, 3),
    ("f_floor", "doughboy", 1150, 520, 0, 4),
    ("f_floor", "hound", 1250, 560, 0, 4),
    # SW-A's closets in the hall (tag 10): the counter-attack on ground
    # already cleared, as the player comes back through the shutter.
    ("closet_hs", "trooper", 1952, 632, 90, 2),
    ("closet_hn", "trooper", 1760, 1736, 270, 2),
    ("closet_hn", "stormtrooper", 1710, 1736, 270, 3),
    ("closet_hs", "trooper", 2000, 632, 90, 4),
    ("closet_hn", "stormtrooper", 1810, 1736, 270, 4),
    # The portal hall, the climax: the General behind the drum, on every
    # skill, his escort of both factions round it.
    ("p_hall", "general", 480, 1216, 0, 2),
    ("p_hall", "hound", 1200, 880, 180, 2),
    ("p_hall", "hound", 1200, 1560, 180, 2),
    ("p_hall", "stormtrooper", 800, 880, 0, 3),
    ("p_hall", "stormtrooper", 800, 1550, 0, 3),
    ("p_hall", "panzermensch", 520, 900, 0, 4),
    ("p_hall", "heavy", 520, 1550, 0, 4),
    # The drum, behind the gate: the portal's last guard on the dais.
    ("p_dais_2", "stormtrooper", 800, 1120, 0, 2),
    ("p_dais_2", "stormtrooper", 800, 1310, 0, 3),
    ("p_dais_1", "doughboy", 864, 1216, 0, 4),
)

# Consumables scale DOWN with skill: (zone, editor number, x, y, highest skill
# tier it appears on - 4 = every skill, 3 = medium and easier, 2 = easy
# only). Weapons are on every skill.
ITEMS = (
    # The weapons, on every skill, on the route, each before the fight it
    # is for: the IZh in the dock, the PPSh upstairs, the RPG-7 at the
    # yellow door's foot (before the Panzermenschen), the ROKS-3 on the
    # foundry gallery (MAP02 section 9 kept it for the factory).
    ("z2_dock", ED_IZH, 3400, 1300, 4),
    ("o_corridor", ED_PPSH, 2700, 1860, 4),
    ("t_line", ED_RPG7, 2304, 400, 4),
    ("f_gallery", ED_ROKS3, 1700, 300, 4),
    # Shell boxes (20): seven on every skill, the last before the General.
    ("z3_hall", ED_SHELL_BOX, 1700, 1250, 4),
    ("z3_hall", ED_SHELL_BOX, 2950, 1300, 4),
    ("o_planning", ED_SHELL_BOX, 2000, 2150, 4),
    ("f_gallery", ED_SHELL_BOX, 1500, 350, 4),
    ("p_booth", ED_SHELL_BOX, 1150, 1730, 4),
    ("p_hall", ED_SHELL_BOX, 1300, 800, 4),
    ("p_ante", ED_SHELL_BOX, 1530, 1220, 4),
    # Shells (4): 5 on every skill, +4 medium, +2 easy.
    ("z2_dock", ED_SHELLS, 3200, 950, 4),
    ("z3_hall", ED_SHELLS, 2150, 800, 4),
    ("t_line", ED_SHELLS, 1950, 400, 4),
    ("f_floor", ED_SHELLS, 1000, 560, 4),
    ("p_hall", ED_SHELLS, 450, 800, 4),
    ("z2_dock", ED_SHELLS, 3500, 950, 3),
    ("z3_hall", ED_SHELLS, 2600, 1600, 3),
    ("t_line", ED_SHELLS, 3000, 400, 3),
    ("f_floor", ED_SHELLS, 500, 150, 3),
    ("z3_hall", ED_SHELLS, 1800, 1600, 2),
    ("t_vestibule", ED_SHELLS, 2304, 560, 2),
    # Boxes of rounds (50): the PPSh's appetite.
    ("z3_hall", ED_CLIP_BOX, 2500, 1350, 4),
    ("o_archive", ED_CLIP_BOX, 2600, 2150, 4),
    ("t_line", ED_CLIP_BOX, 3200, 400, 4),
    ("p_hall", ED_CLIP_BOX, 1100, 1600, 4),
    # Clips (10): 3 on every skill, +1 medium, +1 easy.
    ("z2_dock", ED_CLIP, 3550, 1400, 4),
    ("z3_hall", ED_CLIP, 2000, 1250, 4),
    ("f_floor", ED_CLIP, 900, 250, 4),
    ("z3_hall", ED_CLIP, 2700, 1250, 3),
    ("z2_dock", ED_CLIP, 3250, 1400, 2),
    # PG-7V: a box with the RPG-7, a box in the antechamber and one in the
    # booth, four loose rounds round the drum for the General.
    ("t_line", ED_ROCKET_BOX, 2200, 400, 4),
    ("p_ante", ED_ROCKET_BOX, 1440, 1150, 4),
    ("p_booth", ED_ROCKET_BOX, 1300, 1730, 4),
    ("p_hall", ED_ROCKET, 1350, 1600, 4),
    ("p_hall", ED_ROCKET, 1350, 800, 4),
    ("p_hall", ED_ROCKET, 450, 1600, 4),
    ("p_hall", ED_ROCKET, 600, 1640, 4),
    # Fuel for the ROKS-3: a canister beside it, one before the General.
    ("f_gallery", ED_CELL, 1500, 150, 4),
    ("p_ante", ED_CELL, 1530, 1150, 4),
    # Stimpacks: 5 on every skill, +3 medium, +1 easy.
    ("z2_dock", ED_STIMPACK, 3600, 1000, 4),
    ("z3_hall", ED_STIMPACK, 2950, 760, 4),
    ("t_line", ED_STIMPACK, 2600, 120, 4),
    ("f_gallery", ED_STIMPACK, 1700, 600, 4),
    ("p_hall", ED_STIMPACK, 450, 1000, 4),
    ("z3_hall", ED_STIMPACK, 1700, 760, 3),
    ("o_planning", ED_STIMPACK, 1900, 2000, 3),
    ("p_hall", ED_STIMPACK, 450, 1450, 3),
    ("f_floor", ED_STIMPACK, 1250, 120, 2),
    # Medikits: 5 on every skill, +1 medium.
    ("z3_hall", ED_MEDIKIT, 2400, 1600, 4),
    ("o_archive", ED_MEDIKIT, 2700, 2000, 4),
    ("t_line", ED_MEDIKIT, 3290, 120, 4),
    ("f_platform", ED_MEDIKIT, 450, 450, 4),
    ("p_booth", ED_MEDIKIT, 1216, 1700, 4),
    ("p_hall", ED_MEDIKIT, 1300, 1640, 3),
    # Armour: the flak vest on the tank line, the heavy vest in the
    # antechamber before the General; plates at both locks, in the
    # director's office and on the casting platform.
    ("t_line", ED_GREEN_ARMOR, 2000, 120, 4),
    ("p_ante", ED_BLUE_ARMOR, 1488, 1184, 4),
    ("z3_red_portal", ED_ARMOR_BONUS, 1632, 1050, 4),
    ("z3_red_portal", ED_ARMOR_BONUS, 1632, 1320, 4),
    ("z3_yellow_portal", ED_ARMOR_BONUS, 2150, 736, 4),
    ("z3_yellow_portal", ED_ARMOR_BONUS, 2460, 736, 4),
    ("o_director", ED_ARMOR_BONUS, 2200, 1980, 4),
    ("o_director", ED_ARMOR_BONUS, 2400, 1980, 4),
    ("f_platform", ED_ARMOR_BONUS, 600, 230, 4),
    ("f_platform", ED_ARMOR_BONUS, 600, 480, 3),
    # Health bonuses: one in each nook, for whoever looks into it.
    ("z1_spur", ED_HEALTH_BONUS, 3800, 1136, 4),
    ("z2_arch", ED_HEALTH_BONUS, 3104, 1150, 4),
    ("o_stair_2", ED_HEALTH_BONUS, 2304, 1712, 4),
    ("t_vestibule", ED_HEALTH_BONUS, 2304, 620, 4),
    ("t_pit_a", ED_HEALTH_BONUS, 2530, 256, 4),
    ("t_pit_b", ED_HEALTH_BONUS, 2980, 256, 4),
    ("t_pour_arch", ED_HEALTH_BONUS, 1824, 256, 4),
    ("f_passage", ED_HEALTH_BONUS, 1728, 656, 4),
    ("p_porch", ED_HEALTH_BONUS, 1056, 1216, 4),
    ("p_dais_3", ED_HEALTH_BONUS, 736, 1120, 4),
)

# v1.1 (D68). Kept out of ITEMS on purpose: ITEMS is the route's, and these
# are not on it. Same row shape; everything here is on every skill (MAP01's
# rule for secrets, applied to the boss's stores too).
SECRET_ITEMS = (
    # S1: the Hand Katyusha (its pickup gives 40 fuel, one volley) and a
    # canister towards a second.
    ("s1_store", ED_HAND_KATYUSHA, 2976, 2112, 4),
    ("s1_store", ED_CELL, 2912, 2048, 4),
)
STORES_ITEMS = (
    # The General's stores: health, ammunition, armour, for the drum's
    # guard after the boss.
    ("p_stores", ED_MEDIKIT, 640, 1856, 4),
    ("p_stores", ED_MEDIKIT, 768, 1856, 4),
    ("p_stores", ED_SHELL_BOX, 640, 1792, 4),
    ("p_stores", ED_ROCKET_BOX, 768, 1792, 4),
    ("p_stores", ED_GREEN_ARMOR, 704, 1888, 4),
)


def _sector(floor: int, ceil: int, tag: int | None = None, *, light: int,
            flat: str = FLOOR_CONCRETE, ceiling: str = CEIL_CONCRETE,
            special: int = 0, extra: dict | None = None) -> Sector:
    return Sector(texturefloor=flat, textureceiling=ceiling, heightfloor=floor,
                  heightceiling=ceil, lightlevel=light, identifier=tag,
                  special=special, extra=dict(extra or {}))


def locked_door_style(tag: int, door_sector: int, lock: int,
                      texture: str | None = None) -> LineStyle:
    """A door that opens with a key and STAYS open (delay 0), on both faces.

    Repeatable like a manual door: pressed without the key it prints the
    engine's lock line and can be pressed again; with it, it opens for good.
    MAP02's helper, repeated here so each map stays one file (it moves into
    sdbuild.udmf when a third map wants it).
    """
    return LineStyle(
        special=SPECIAL_DOOR_LOCKED_RAISE,
        args=(tag, DOOR_SPEED_SLOW, 0, lock, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,
    )


def hang(tm: TextMap, segment: tuple[int, int, int, int], room: int, texture: str) -> None:
    """Hang a middle texture on the two-sided line `segment`, on its face
    towards `room` (a banner, a chain). GridMap dresses only the upper and
    lower parts of a two-sided line, so this is done on the built map.

    Pegged as Doom pegs a two-sided middle texture by default: its top at
    the lower of the two ceilings, drawn once, not tiled downwards.
    """
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


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map; return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} v1.1 generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
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

    def door(name: str, floor: int, tag: int, rect, *, light: int) -> int:
        """A closed door sector; its own walls are the steel track."""
        return zone(name, floor, floor, [rect], tag, light=light, wall=STEEL)

    def rails(room: str, x1: int, x2: int, y1: int, y2: int) -> None:
        """A 64-wide rail strip along x: SDRAIL1 runs its rails along the
        image's y, so it is turned a quarter (MAP02's K8, either way reads)."""
        like(room, f"rails_{room}", [(x1, y1, x2, y2)], flat=RAILS,
             extra={"rotationfloor": 90.0})

    def steps(prefix: str, xs, y1: int, y2: int, floors, *, room: str) -> None:
        """A run of 32-deep steps across x, one sector per step."""
        for n, (x, floor) in enumerate(zip(xs, floors), start=1):
            like(room, f"{prefix}_{n}", [(x, y1, x + 32, y2)], floor=floor, wall=CONCRETE)

    def recess(room: str, name: str, rect, *, ceil: int, back, texture: str) -> int:
        """A shallow recess one tile high in `room`'s wall, its back wall one
        whole tile of `texture` (a shut gate, a flag). `back` is the back
        wall's segment, ("v", x, y1, y2) or ("h", y, x1, x2)."""
        index = like(room, name, [rect], ceil=ceil, wall=BRICK)
        kind, coord, lo, hi = back
        style = LineStyle(texture=texture)
        if kind == "v":
            g.style_v(coord, lo, hi, style)
        else:
            g.style_h(coord, lo, hi, style)
        return index

    def closet(name: str, door_rect, room_rect, tag: int, *, leaf: str) -> int:
        """A monster closet (MAP01 v3's, MAP02 v1's): a panel in a wall that
        opens for good with the switch that owns `tag`, together with that
        switch's gate. The panel and the closet wear the wall they are cut
        into, so it is wall until it moves; nothing closes it again, and the
        closet is a dead end the player walks out of."""
        door_index = zone(f"{name}_door", GROUND, GROUND, [door_rect], tag,
                          light=LIGHT_CLOSET, wall=leaf)
        zone(name, GROUND, GROUND + CLOSET_HEIGHT, [room_rect], light=LIGHT_CLOSET, wall=leaf)
        return door_index

    # ======================================================================
    # Arrival: the goods spur MAP02's tunnel ran into, and the loading dock
    # ======================================================================
    zone("z1_spur", GROUND, SPUR_CEIL, [(3648, 1120, 4160, 1248)],
         light=LIGHT_SPUR, wall=TUBBING)
    rails("z1_spur", 3648, 4160, 1152, 1216)
    zone("z2_dock", GROUND, DOCK_CEIL, [(3136, 896, 3648, 1472)],
         light=LIGHT_DOCK, wall=BRICK)
    rails("z2_dock", 3328, 3648, 1152, 1216)     # the buffer stop is v2's
    # The yard's road gate, shut, in the dock's north wall.
    recess("z2_dock", "z2_road_gate", (3328, 1472, 3456, 1472 + NICHE_DEPTH),
           ceil=GROUND + TILE, back=("h", 1472 + NICHE_DEPTH, 3328, 3456), texture=ROAD_GATE)
    zone("z2_arch", GROUND, 192, [(3072, 1120, 3136, 1248)],
         light=LIGHT_HALL, wall=BRICK)

    # ======================================================================
    # The assembly hall: the factory's public face, and the hub
    # ======================================================================
    zone("z3_hall", GROUND, HALL_CEIL, [(1600, 704, 3072, 1664)],
         light=LIGHT_HALL, ceiling=CEIL_PANEL, wall=HALL_WALL)
    for r, (y1, y2) in enumerate(CONVEYOR_ROWS, start=1):
        for c, (x1, x2) in enumerate(CONVEYOR_RUNS, start=1):
            like("z3_hall", f"{PROP_PREFIX}conveyor_{r}{c}", [(x1, y1, x2, y2)],
                 floor=GROUND + CONVEYOR, wall=STEEL, flat=FLOOR_PLATE)
    # The red door's portal: a 128-high band across the west end, so the
    # leaf and the whitewashed brick either side are each one whole tile.
    zone("z3_red_portal", GROUND, DOOR_HEIGHT, [(1600, 992, 1664, 1376)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=BRICK, extra=RED_LIGHT)
    red_door = door("red_door", GROUND, TAG_RED_DOOR, (1568, 1120, 1600, 1248),
                    light=LIGHT_ANTE)
    # The yellow door's portal, in the south wall, the same way.
    zone("z3_yellow_portal", GROUND, DOOR_HEIGHT, [(2112, 704, 2496, 768)],
         light=LIGHT_BEACON, ceiling=CEIL_PANEL, wall=BRICK, extra=YELLOW_LIGHT)
    yellow_door = door("yellow_door", GROUND, TAG_YELLOW_DOOR, (2240, 672, 2368, 704),
                       light=LIGHT_VESTIBULE)
    # The yellow lane: from the yellow door's portal, up the centre aisle,
    # to the foot of the office stair. Lock and key joined by a line.
    zone("z3_lane", GROUND, HALL_CEIL, [(LANE_X[0], 768, LANE_X[1], 1664)],
         light=LIGHT_HALL, flat=FLOOR_LANE, ceiling=CEIL_PANEL, wall=HALL_WALL)
    # The works banner, hung from the roof across the hall's axis.
    like("z3_hall", "z3_banner", [BANNER])
    # The two portraits' niches in the west wall (POSTER_NICHES).
    for name, rect in POSTER_NICHES.items():
        like("z3_hall", name, [rect], ceil=GROUND + POSTER_HEIGHT)
    # The clerestory: sills one pane tile under the roof, glazing behind.
    for n, x in enumerate(CLERESTORY_NORTH, start=1):
        recess("z3_hall", f"{PROP_PREFIX}clerestory_n{n}", (x, 1664, x + 64, 1664 + NICHE_DEPTH),
               ceil=HALL_CEIL, back=("h", 1664 + NICHE_DEPTH, x, x + 64), texture=WINDOW)
        tm.sectors[plan[f"{PROP_PREFIX}clerestory_n{n}"]].heightfloor = CLERESTORY_SILL
    for n, x in enumerate(CLERESTORY_SOUTH, start=1):
        recess("z3_hall", f"{PROP_PREFIX}clerestory_s{n}", (x, 704 - NICHE_DEPTH, x + 64, 704),
               ceil=HALL_CEIL, back=("h", 704 - NICHE_DEPTH, x, x + 64), texture=WINDOW)
        tm.sectors[plan[f"{PROP_PREFIX}clerestory_s{n}"]].heightfloor = CLERESTORY_SILL

    # ======================================================================
    # The offices: four steps up, the director's office straight ahead
    # ======================================================================
    for n in range(1, 5):
        y = 1664 + 32 * (n - 1)
        zone(f"o_stair_{n}", GROUND + STEP * n, OFFICE_CEIL, [(2240, y, 2368, y + 32)],
             light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    zone("o_corridor", OFFICES, OFFICE_CEIL, [(1856, 1792, 2752, 1920)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    zone("o_director_doorway", OFFICES, OFFICE_CEIL, [(2240, 1920, 2368, 1952)],
         light=LIGHT_DIRECTOR, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO,
         extra=YELLOW_LIGHT)
    zone("o_director", OFFICES, OFFICE_CEIL, [(2176, 1952, 2432, 2208)],
         light=LIGHT_DIRECTOR, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO,
         extra=YELLOW_LIGHT)
    zone("o_desk", OFFICES + DESK, OFFICE_CEIL, [(2240, 2016, 2368, 2080)],
         light=LIGHT_BEACON, flat=DESK_TOP, ceiling=CEIL_PANEL, wall=CRATE,
         extra=YELLOW_LIGHT)
    d1 = door("d1_planning", OFFICES, TAG_D1_PLANNING, (1920, 1920, 2048, 1952),
              light=LIGHT_OFFICES)
    zone("o_planning", OFFICES, OFFICE_CEIL, [(1856, 1952, 2112, 2208)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_PANEL, wall=TILE_DADO)
    d2 = door("d2_archive", OFFICES, TAG_D2_ARCHIVE, (2560, 1920, 2688, 1952),
              light=LIGHT_OFFICES)
    zone("o_archive", OFFICES, OFFICE_CEIL, [(2496, 1952, 2752, 2208)],
         light=LIGHT_OFFICES, flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    # v1.1, S1: the set-back locker, its panel, the passage, the store.
    zone("s1_niche", OFFICES, OFFICE_CEIL, [S1_NICHE], light=LIGHT_S1_NICHE,
         flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    s1_panel = zone("s1_panel", OFFICES, OFFICES, [S1_PANEL], TAG_S1_PANEL,
                    light=LIGHT_S1_NICHE, flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    zone("s1_passage", OFFICES, OFFICE_CEIL, [S1_PASSAGE], light=LIGHT_SECRET,
         flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO)
    zone("s1_store", OFFICES, OFFICE_CEIL, [S1_STORE], light=LIGHT_SECRET,
         flat=FLOOR_TILE, ceiling=CEIL_CONCRETE, wall=TILE_DADO, special=SECTOR_SPECIAL_SECRET)

    # ======================================================================
    # Behind the yellow door: the tank line, where the "tractors" are tanks
    # ======================================================================
    zone("t_vestibule", GROUND, DOOR_HEIGHT, [(2240, 448, 2368, 672)],
         light=LIGHT_VESTIBULE, wall=RUST)
    zone("t_line", GROUND, LINE_CEIL, [(1856, 64, 3328, 448)],
         light=LIGHT_LINE, flat=FLOOR_PLATE, ceiling=CEIL_PANEL, wall=RUST)
    # Two inspection pits under the line, a tank's length each, with two
    # steps at both ends: the long sides are drops, the ends the way out.
    for name, x1 in (("pit_a", 2432), ("pit_b", 2880)):
        like("t_line", f"t_{name}", [(x1 + 64, 192, x1 + 320, 320)], floor=TANK_PIT,
             wall=CONCRETE, flat=FLOOR_CONCRETE)
        steps(f"t_{name}_w", (x1, x1 + 32), 192, 320, (TANK_PIT + 2 * STEP, TANK_PIT + STEP),
              room="t_line")
        steps(f"t_{name}_e", (x1 + 320, x1 + 352), 192, 320, (TANK_PIT + STEP, TANK_PIT + 2 * STEP),
              room="t_line")
        if CHAIN:
            like(f"t_{name}", f"t_{name}_hoist", [HOISTS[f"t_{name}"]])
    # The closed shop's export gate, shut, in the line's east wall.
    recess("t_line", "t_export_gate", (3328, 192, 3328 + NICHE_DEPTH, 320),
           ceil=GROUND + TILE, back=("v", 3328 + NICHE_DEPTH, 192, 320), texture=ROAD_GATE)
    zone("t_pour_arch", GROUND, DOOR_HEIGHT, [(1792, 192, 1856, 320)],
         light=LIGHT_GALLERY, wall=BRICK)

    # ======================================================================
    # The foundry: a gallery at ground level over the casting floor
    # ======================================================================
    zone("f_floor", FOUNDRY_PIT, FOUNDRY_CEIL, [(384, 64, 1408, 640)],
         light=LIGHT_FOUNDRY, flat=FLOOR_PLATE, wall=BRICK)
    # v1.1 (D68): it hurts. 16 below the casting floor and open on all four
    # sides: one step out, anywhere along it.
    like("f_floor", "f_channel", [(768, 128, 1152, 192)], floor=CHANNEL, flat=MOLTEN,
         extra=CHANNEL_HURTS)
    zone("f_gallery", GROUND, FOUNDRY_CEIL, [(1408, 64, 1792, 640)],
         light=LIGHT_GALLERY, flat=GRATING, wall=BRICK)
    steps("f_stair", (1376, 1344, 1312), 256, 384,
          (GROUND - STEP, GROUND - 2 * STEP, GROUND - 3 * STEP), room="f_floor")
    zone("f_platform", GROUND, FOUNDRY_CEIL, [(384, 192, 640, 512)],
         light=LIGHT_FOUNDRY, flat=FLOOR_PLATE, wall=BRICK)
    steps("f_platform_stair", (640, 672, 704), 288, 416,
          (GROUND - STEP, GROUND - 2 * STEP, GROUND - 3 * STEP), room="f_floor")
    zone("f_pedestal", GROUND + DESK, FOUNDRY_CEIL, [(448, 288, 576, 416)],
         light=LIGHT_BEACON, wall=STEEL, extra=RED_LIGHT)
    # The shortcut: a short passage from the gallery's north wall to a
    # shutter flush with the assembly hall's south wall, beside the red door.
    zone("f_passage", GROUND, DOOR_HEIGHT, [(1664, 640, 1792, 672)],
         light=LIGHT_GALLERY, wall=BRICK_DADO)
    shutter = door("shutter", GROUND, TAG_SHUTTER, (1664, 672, 1792, 704), light=LIGHT_HALL)
    zone("f_swa_niche", GROUND, GROUND + SWITCH_HEIGHT, [(1600, 640, 1664, 640 + NICHE_DEPTH)],
         light=LIGHT_GALLERY, wall=BRICK)

    # ======================================================================
    # Behind the red door: the portal hall, the booth, the containment drum
    # ======================================================================
    zone("p_ante", GROUND, DOOR_HEIGHT, [(1408, 1120, 1568, 1248)],
         light=LIGHT_ANTE, wall=BRICK_DADO)
    zone("p_hall", GROUND, PORTAL_HALL_CEIL, [(384, 768, 1408, 1664)],
         light=LIGHT_PORTAL_HALL, flat=FLOOR_PLATE, wall=BRICK)
    zone("p_booth", GROUND, DOOR_HEIGHT, [(1088, 1664, 1344, 1792)],
         light=LIGHT_BOOTH, ceiling=CEIL_PANEL, wall=STEEL)
    # The drum: a solid ring round the portal, one gate in its east face,
    # a 128-high porch either side of the gate so its leaf is one tile.
    g.carve(640, 1024, 1024, 1408)
    zone("p_drum", GROUND, DRUM_CEIL, [(704, 1088, 960, 1344)],
         light=LIGHT_DRUM, wall=STEEL)
    gate = door("gate", GROUND, TAG_GATE, (960, 1152, 1024, 1280), light=LIGHT_DRUM)
    zone("p_porch", GROUND, DOOR_HEIGHT, [(1024, 1152, 1088, 1280)],
         light=LIGHT_PORTAL_HALL, wall=STEEL)
    like("p_drum", "p_inner_porch", [(896, 1152, 960, 1280)], ceil=DOOR_HEIGHT)
    # v1.1: the General's stores, behind a steel shutter in the north wall.
    zone("p_stores_porch", GROUND, DOOR_HEIGHT, [STORES_PORCH],
         light=LIGHT_PORTAL_HALL, flat=FLOOR_PLATE, wall=STEEL)
    stores_door = door("p_stores_door", GROUND, TAG_GENERAL_STORES, STORES_DOOR,
                       light=LIGHT_STORES)
    zone("p_stores", GROUND, DOOR_HEIGHT, [STORES], light=LIGHT_STORES,
         flat=FLOOR_PLATE, ceiling=CEIL_PANEL, wall=STEEL)
    for n, x in enumerate((832, 768, 704), start=1):
        like("p_drum", f"p_dais_{n}", [(x, 1088, x + 64, 1344)], floor=GROUND + STEP * n)
    zone("p_exit_niche", GROUND + 3 * STEP, GROUND + 3 * STEP + SWITCH_HEIGHT,
         [(704 - NICHE_DEPTH, 1184, 704, 1248)], light=LIGHT_BEACON, wall=STEEL)
    # The two flags side by side over the drum (LORE), one either side of
    # the gate, each in a recess one tile high in the ring's east face.
    recess("p_hall", "p_flag_reich", (1024 - NICHE_DEPTH, 1056, 1024, 1120),
           ceil=GROUND + TILE, back=("v", 1024 - NICHE_DEPTH, 1056, 1120), texture=FLAG_REICH)
    recess("p_hall", "p_flag_legion", (1024 - NICHE_DEPTH, 1312, 1024, 1376),
           ceil=GROUND + TILE, back=("v", 1024 - NICHE_DEPTH, 1312, 1376), texture=FLAG_LEGION)

    # ======================================================================
    # Line styles: doors, locks, switches, the exit, the drum
    # ======================================================================
    # The posters first: GridMap keeps the first style registered on a segment.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))

    for sector, y, (x1, x2) in ((d1, 1920, (1920, 2048)), (d1, 1952, (1920, 2048)),
                                (d2, 1920, (2560, 2688)), (d2, 1952, (2560, 2688))):
        tag = tm.sectors[sector].identifier
        g.style_h(y, x1, x2, door_raise_style(tag, sector, texture=DOOR))

    # The yellow door, both faces, between its two star plaques.
    for y in (672, 704):
        g.style_h(y, 2240, 2368, locked_door_style(TAG_YELLOW_DOOR, yellow_door,
                                                   LOCK_YELLOW_CARD, texture=DOOR_YELLOW))
    g.style_h(704, 2112, 2240, LineStyle(texture=STAR))
    g.style_h(704, 2368, 2496, LineStyle(texture=STAR))
    # The red door, both faces, between plain whitewashed brick: red star
    # plaques beside a red-trimmed leaf hid it (art-director, v1).
    for x in (1568, 1600):
        g.style_v(x, 1120, 1248, locked_door_style(TAG_RED_DOOR, red_door,
                                                   LOCK_RED_CARD, texture=DOOR_RED))
    g.style_v(1600, 992, 1120, LineStyle(texture=BRICK_DADO))
    g.style_v(1600, 1248, 1376, LineStyle(texture=BRICK_DADO))

    # The shutter: steel on the foundry side; on the hall side it wears the
    # hall's own wall, so until SW-A opens it it is wall, not a door that
    # will not open (MAP01 v0/v1, MAP02's SH).
    g.style_h(672, 1664, 1792, remote_door_style(shutter, texture=STEEL))
    g.style_h(704, 1664, 1792, remote_door_style(shutter, texture=HALL_WALL))
    g.style_h(640 + NICHE_DEPTH, 1600, 1664,
              switch_door_open_style(TAG_SHUTTER, texture=SW_A_FACE, repeatable=False))

    # The drum's gate: a leaf on both faces. SW-B on the booth's back wall.
    for x in (960, 1024):
        g.style_v(x, 1152, 1280, remote_door_style(gate, texture=DOOR))
    g.style_h(1792, 1184, 1248, switch_door_open_style(TAG_GATE, texture=SW_B_FACE,
                                                       repeatable=False))
    # The drum is steel outside as well as in (the portal hall is brick),
    # and the wall behind the dais is the portal itself.
    for y1, y2 in ((1024, 1152), (1280, 1408)):
        g.style_v(1024, y1, y2, LineStyle(texture=STEEL))
    g.style_v(640, 1024, 1408, LineStyle(texture=STEEL))
    g.style_h(1024, 640, 1024, LineStyle(texture=STEEL))
    g.style_h(1408, 640, 1024, LineStyle(texture=STEEL))
    for y1, y2 in ((1088, 1184), (1248, 1344)):
        g.style_v(704, y1, y2, LineStyle(texture=PORTAL))

    # v1.1, S1: the archive's row of lockers; the third stands back, in
    # shadow, and is the panel. Flagged `secret`: one-sided on the automap.
    lx, ly1, ly2 = LOCKER_ROW
    g.style_v(lx, ly1, S1_NICHE[1], LineStyle(texture=LOCKER))
    g.style_v(lx, S1_NICHE[3], ly2, LineStyle(texture=LOCKER))
    panel = door_open_style(TAG_S1_PANEL, s1_panel, texture=LOCKER)
    panel = replace(panel, flags=panel.flags + ("secret",))
    for x in (S1_PANEL[0], S1_PANEL[2]):
        g.style_v(x, S1_PANEL[1], S1_PANEL[3], panel)
    # The General's stores: steel on both faces, no special on either, so
    # pressing it does nothing and nothing but his death opens it.
    for y in (STORES_DOOR[1], STORES_DOOR[3]):
        g.style_h(y, STORES_DOOR[0], STORES_DOOR[2], remote_door_style(stores_door, texture=STEEL))

    # The tunnel's mouth in the dock's brick, and the hall's closets.
    g.style_v(3648, 1120, 1248, LineStyle(texture=BRICK))

    # The exit: the breaker at the back of its niche, on top of the dais.
    g.style_v(704 - NICHE_DEPTH, 1184, 1248, exit_switch_style(texture=EXIT_FACE))

    # ======================================================================
    # v1: SW-A's two closets in the hall (design section 15.4)
    # ======================================================================
    # In the south wall just east of the shutter, and in the north wall at
    # the hall's west end above the red door: brick panels in brick walls.
    closet("closet_hs", (1856, 704 - NICHE_DEPTH, 2048, 704), (1856, 576, 2048, 704 - NICHE_DEPTH),
           TAG_HALL_AMBUSH, leaf=HALL_WALL)
    closet("closet_hn", (1664, 1664, 1856, 1664 + NICHE_DEPTH), (1664, 1664 + NICHE_DEPTH, 1856, 1792),
           TAG_HALL_AMBUSH, leaf=HALL_WALL)

    g.build()

    # Middle textures, on the built lines.
    if SLOGAN:
        bx1, by1, bx2, by2 = BANNER
        hall = plan["z3_hall"]
        hang(tm, (bx1, by1, bx1, by2), hall, SLOGAN)
        hang(tm, (bx2, by1, bx2, by2), hall, SLOGAN)
    if CHAIN:
        for pit, (hx1, hy1, hx2, hy2) in HOISTS.items():
            room = plan[pit]
            for segment in ((hx1, hy1, hx2, hy1), (hx1, hy2, hx2, hy2),
                            (hx1, hy1, hx1, hy2), (hx2, hy1, hx2, hy2)):
                hang(tm, segment, room, CHAIN)

    tm.add_thing(Thing(x=PLAYER_START[0], y=PLAYER_START[1], type=ED_PLAYER1_START,
                       angle=PLAYER_ANGLE))
    tm.add_thing(Thing(x=YELLOW_KEY_SPOT[0], y=YELLOW_KEY_SPOT[1], type=ED_YELLOW_CARD))
    tm.add_thing(Thing(x=RED_KEY_SPOT[0], y=RED_KEY_SPOT[1], type=ED_RED_CARD))
    for _zone, kind, x, y, angle, tier in MONSTERS:
        extra = {}
        if kind == "general":
            # v1.1 (D68): his death opens the stores. UDMF thing fields.
            special, args = GENERAL_DEATH_SPECIAL
            extra = {"special": special, **{f"arg{i}": a for i, a in enumerate(args)}}
        tm.add_thing(Thing.on_skills(x, y, MONSTER_KINDS[kind], skill_tier(tier), angle=angle,
                                     extra=extra))
    for _zone, ednum, x, y, top in ITEMS + SECRET_ITEMS + STORES_ITEMS:
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
WALL_TEXTURES = ((CONCRETE, STAR, STEEL, TILE_DADO, CRATE, TUBBING, BRICK, BRICK_DADO, RUST,
                  PORTAL, ROAD_GATE, WINDOW, FLAG_REICH, FLAG_LEGION, LOCKER)
                 + DOOR_LEAVES + SWITCH_FACES + tuple(t for t in (CHAIN, SLOGAN) if t)
                 + (LENIN, STALIN, MURAL) + ((MARX_ENGELS,) if MARX_ENGELS else ()))
FLAT_TEXTURES = (FLOOR_LANE, FLOOR_CONCRETE, FLOOR_TILE, CEIL_PANEL, CEIL_CONCRETE,
                 DESK_TOP, RAILS, FLOOR_PLATE, GRATING, MOLTEN)
# The Tankograd lumps (D66) this map places, frame 1 standing for each animation.
TANKOGRAD = (BRICK, BRICK_DADO, RUST, DOOR_YELLOW, DOOR_RED, PORTAL, ROAD_GATE, WINDOW,
             FLAG_REICH, FLAG_LEGION, FLOOR_PLATE, GRATING, MOLTEN) + tuple(t for t in (CHAIN, SLOGAN) if t)
