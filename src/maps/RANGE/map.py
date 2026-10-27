"""RANGE - the practice range (D41): the arsenal hall and the bestiary gallery.

The map lump is RANGE since D62 (2026-10-14): it was MAP02 until the MAPxx
slots went to the campaign. Design document: docs/levels/RANGE-practice-range.md. Built in F4 as an
engineering fixture (prove that each of the seven weapons can be picked up,
selected, fired and made to do damage) and shipped since D41 as a practice
range, a second episode on New Game (docs/engine/adr/007). MAP01 is not
touched by this file.

Layout:

* THE HALL, 2048 x 768. The player spawns at the west end with the TT-33;
  the seven weapon pickups and the ammo sit within a few steps; barrels at
  mid range and six targets at the east end.
* THE EXIT (D41 v1): a lit alcove in the hall's west wall, straight behind
  the player start, with an exit switch. Exit_Normal ends the map; MAPINFO
  (cluster 2, `next = endtitle`) shows the range's end text and returns to
  the title. Until this, the range could only be left through the menu.
* THE BESTIARY GALLERY (F5), north of the hall: one of each enemy class
  standing in a row (docs/engine/BESTIARY.md 11.1), deaf and facing the far
  wall. Since D41 v1 it is reached ON FOOT: a door in the hall's north wall
  opens on a dog-leg passage that comes out behind the row. The bend is
  there so that no line of sight runs from the gallery into the hall even
  with the door open: an `ambush` (deaf) monster that hears gunfire still
  wakes if it can see the shooter, so the hall's noise must not reach eyes
  in the gallery. Tested in tests/test_range_map.py. `warp 1024 1152`
  (GALLERY_ARRIVAL) still lands at the passage's mouth for the PM.

Every wall, floor and ceiling is an approved, packed project texture of
the Zarya-7 base set (docs/art/TEXTURE-INDEX.md), the set MAP01 is built
from; no IWAD texture or flat is left (M2d, after the M2 audit
docs/qa/2026-10-14_2357_M2-freedoom-audit.md item A4; until then the range
wore Freedoom's STARTAN2, FLOOR4_8 and CEIL3_5). The rooms dress as MAP01
dresses its own: the hall and the gallery are poured concrete (SDCONC1)
over hangar floor and tiled floor, the dog-leg passage is green steel plate
like MAP01's airlock. The two things a player must read as "press here"
still wear the signs MAP01 taught him, and only they do: the door leaf
SDDOOR1, and the exit switch SDSW1D (the hazard panel, MAP01's exit switch)
under the lamp panel SDCEIL1.

Targets: explosive barrels prove splash damage; six thing-3004 targets prove
hitscan and projectile damage on a living actor. 3004 is Doom's zombieman
number, and since F5 it spawns OUR SD_ReichRifleman (`replaces ZombieMan`).
They are flagged `ambush` (deaf) so they only react to what they can see,
which keeps the range predictable.

Run it with:  SD_ALLOW_ENGINE=1 MAP=RANGE tools/run.sh   (the PM; D26)
"""

from __future__ import annotations

from sdbuild.udmf import (
    GridMap,
    LineStyle,
    Sector,
    TextMap,
    Thing,
    door_raise_style,
    exit_switch_style,
)

MAP_NAME = "RANGE"

# --- Geometry -------------------------------------------------------------
HALL_LENGTH = 2048     # x axis; long enough to see projectile travel and
                       # to outrange the ROKS-3 (528 units of reach)
HALL_WIDTH = 768       # y axis; room to strafe without leaving the lane
FLOOR_HEIGHT = 0
CEILING_HEIGHT = 128   # standard Doom height; SDCONC1 is 128 tall and tiles
                       # exactly once, so no texture seams
LIGHT_LEVEL = 192      # brighter than MAP01: this is a diagnostic space
HALL = (0, 0, HALL_LENGTH, HALL_WIDTH)

# --- Approved project textures (docs/art/TEXTURE-INDEX.md) ---------------
# The Zarya-7 base set, chosen as MAP01 chooses (docs/levels/MAP01-zarya-7.md
# section 6): concrete for rooms, steel plate for the way through. No IWAD
# name may appear here (tests/test_range_map.py, the M2 audit's check).
WALL_TEXTURE = "SDCONC1"    # 64x128 prefab concrete: the hall and the gallery
FLOOR_FLAT = "SDFLR2"       # plain hangar concrete: the hall, the exit, the passage
CEILING_FLAT = "SDCEIL2"    # plain concrete ceiling panel, every room
GALLERY_FLOOR = "SDFLR3"    # grey two-tone tiles: the bestiary reads as a
                            # room apart from the firing hall
PASSAGE_TEXTURE = "SDSTEL1" # green steel plate: the passage as MAP01's airlock

# Only on what the player presses, so it reads as it did in MAP01.
DOOR_TEXTURE = "SDDOOR1"    # 128x128 door leaf: the gallery door is 128 wide
TRACK_TEXTURE = "SDSTEL1"   # the door's jambs, as on every MAP01 door
EXIT_TEXTURE = "SDSW1D"     # 64x128 hazard panel: MAP01's exit switch
LAMP_FLAT = "SDCEIL1"       # the lit panel over the exit

# Both room materials are 64 wide. A wall run starts its texture at its
# own first vertex, so a run that starts off the 64 grid (the hall's west
# wall north of the exit alcove starts at y 416) would end on a cut panel
# in the corner; world_align() shifts each one-sided room wall so its
# panels sit on the map's 64 grid, as they would if the wall were unbroken.
PANEL_WIDTH = 64
ALIGNED_TEXTURES = (WALL_TEXTURE, PASSAGE_TEXTURE)

# --- The posters (CEO, 2026-10-22: «que esos posters puedan aparecer en
# cualquier nivel»; tests/test_posters.py, design document section 5.1) ------
# The range is a room of the Zarya-7 base, so it hangs what the base hangs.
# Each picture is one 128-long wall line in a room exactly its height, so it
# is seen whole: the 128x256 portraits in the gallery (256 high), the 128x128
# mural in the hall (128 high). world_align() leaves them at offset 0: it
# shifts only ALIGNED_TEXTURES.
LENIN = "SDPOSTR1"          # 128x256 Lenin poster
STALIN = "SDPOSTR3"         # 128x256 Stalin poster (D55)
MURAL = "SDPOSTR2"          # 128x128 cosmonautics mural
# The Marx-Engels pair (D117), 128x256 each like Lenin and Stalin: Marx
# carries «ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels «СОЕДИНЯЙТЕСЬ!» (his face mirrored
# to look at Marx). Hung on the two Marx-Engels slots, Marx's first.
MARX = "SDPOSTR4"
ENGELS = "SDPOSTR5"
MARX_ENGELS = (MARX, ENGELS)     # in the order of POSTER_SLOTS_MARX_ENGELS
# (name, texture, axis, coord, lo, hi): the segment one GridMap style paints.
# The gallery's far wall, the one the bestiary row faces and the player sees
# over it from the passage's mouth, carries Lenin and Stalin either side of
# the axis (x 1024); its two end walls carry the Marx-Engels pair (D117),
# facing each other across the row: Marx west, on the left from the passage's
# mouth, Engels east. The mural hangs in the hall's west wall beside
# the exit alcove: the player turns to it to leave.
POSTERS = (
    ("gallery_lenin", LENIN, "h", 1792, 832, 960),
    ("gallery_stalin", STALIN, "h", 1792, 1088, 1216),
    ("gallery_west_slot", MARX, "v", 0, 1344, 1472),
    ("gallery_east_slot", ENGELS, "v", 2048, 1344, 1472),
    ("hall_mural", MURAL, "v", 0, 448, 576),
)
POSTER_SLOTS_MARX_ENGELS = ("gallery_west_slot", "gallery_east_slot")   # Marx, Engels


def poster_faces() -> tuple[tuple[str, str, str, int, int, int], ...]:
    """Every picture as painted: (name, texture, axis, coord, lo, hi). Since
    D117 each Marx-Engels slot wears its own poster in POSTERS itself."""
    return POSTERS


WALL_TEXTURES = (WALL_TEXTURE, PASSAGE_TEXTURE, DOOR_TEXTURE, TRACK_TEXTURE, EXIT_TEXTURE,
                 LENIN, STALIN, MURAL) + MARX_ENGELS
FLAT_TEXTURES = (FLOOR_FLAT, CEILING_FLAT, GALLERY_FLOOR, LAMP_FLAT)

# --- Editor numbers -------------------------------------------------------
# Mod actors: reserved range 21000-21999 (see docs/engine/MOD-SPEC.md).
ED_PLAYER1_START = 1

ED_SD_ICE_AXE = 21001   # slot 1, the ice axe (D40; the shovel until then)
ED_SD_TOKAREV = 21002
ED_SD_IZH = 21003
ED_SD_PPSH = 21004
ED_SD_RPG7 = 21005
ED_SD_ROKS3 = 21006
ED_SD_KATYUSHA = 21007
# V3 A4, the RGD-5 hand grenade (ADR 012): slot 8, a pool of its own. The
# pouch (the weapon and two grenades) ends the weapon row; a crate of four
# ends the ammunition row, so the range holds the pool's maximum (six) on
# every skill: throw at the barrels (128 of blast against their 64-unit
# spacing) and at the far targets aimed up.
ED_SD_RGD5 = 21009
ED_SD_RGD5_BOX = 21022

# Standard Doom/Freedoom items (unchanged by the mod: the arsenal reuses the
# four vanilla ammo pools - Clip, Shell, RocketAmmo, Cell).
ED_CLIP_BOX = 2048       # 50 rounds of 7.62x25 for the TT-33 and the PPSh
ED_SHELL_BOX = 2049      # 20 shells for the IZh
ED_ROCKET_BOX = 2046     # 5 rounds for the RPG-7
ED_CELL_PACK = 17        # 100 fuel units for the ROKS-3 / Katyusha
ED_BACKPACK = 8
ED_MEDIKIT = 2012
ED_BLUE_ARMOR = 2019
ED_BARREL = 2035         # target: proves splash damage
ED_ZOMBIEMAN = 3004      # target: Doom's number, spawns SD_ReichRifleman since F5

# Bestiary (F5): docs/engine/MOD-SPEC.md 6.1. One of each, in this order
# along the gallery row, west to east; the General last, with room on both
# sides for the two riflemen he summons.
ED_SD_REICH_RIFLEMAN = 21100
ED_SD_LEGION_TROOPER = 21101
ED_SD_STORMTROOPER = 21102
ED_SD_REICH_HOUND = 21103
ED_SD_DOUGHBOY = 21104
ED_SD_PANZERMENSCH = 21105
ED_SD_GENERAL = 21106
ED_SD_PANZERMENSCH_SCHWER = 21107

# --- Placement ------------------------------------------------------------
PLAYER_X = 160
PLAYER_Y = HALL_WIDTH / 2
PLAYER_ANGLE = 0            # facing +x, down the lane

PICKUP_FIRST_X = 288        # first item of a row
PICKUP_SPACING = 112        # map units between items; wide enough not to
                            # grab two by accident when walking the row
WEAPON_ROW_Y = 624          # north wall side
AMMO_ROW_Y = 144            # south wall side

WEAPON_ROW = [
    ED_SD_ICE_AXE,
    ED_SD_TOKAREV,
    ED_SD_IZH,
    ED_SD_PPSH,
    ED_SD_RPG7,
    ED_SD_ROKS3,
    ED_SD_KATYUSHA,
    ED_SD_RGD5,
]

AMMO_ROW = [
    ED_CLIP_BOX,
    ED_CLIP_BOX,
    ED_SHELL_BOX,
    ED_SHELL_BOX,
    ED_ROCKET_BOX,
    ED_CELL_PACK,
    ED_CELL_PACK,
    ED_SD_RGD5_BOX,
]

SUPPORT_ITEMS = [
    (ED_BACKPACK, 288, 384),
    (ED_MEDIKIT, 400, 384),
    (ED_MEDIKIT, 512, 384),
    (ED_BLUE_ARMOR, 624, 384),
]

# Barrels at mid range, zombiemen at the far wall.
BARRELS = [
    (1248, 256), (1248, 512),
    (1440, 256), (1440, 512),
    (1632, 256), (1632, 512),
]

TARGETS = [
    (1856, 160), (1856, 384), (1856, 608),
    (1984, 256), (1984, 384), (1984, 512),
]

# --- The exit (D41 v1) ------------------------------------------------------
# An alcove in the west wall, centred on the player start's row: turn round
# and it is there. One switch face wide (64), one face high (128), so the
# panel is seen whole; brighter than the hall, so it reads as the way out.
SWITCH_WIDTH = 64
SWITCH_HEIGHT = 128
EXIT_DEPTH = 32
EXIT_ALCOVE = (-EXIT_DEPTH, int(PLAYER_Y) - SWITCH_WIDTH // 2, 0, int(PLAYER_Y) + SWITCH_WIDTH // 2)
EXIT_LIGHT = 224

# --- Bestiary gallery (F5) --------------------------------------------------
# A separate room north of the hall; 256 units of solid ground between them,
# crossed only by the passage below.
GALLERY_X1 = 0
GALLERY_X2 = HALL_LENGTH
GALLERY_Y1 = 1024          # 256 units of solid void above the hall's north wall
GALLERY_Y2 = 1792          # as wide as the hall
# 256 since the posters (CEO, 2026-10-22): two SDCONC1 panels exactly, where
# 192 cut the second at the ceiling, and the height a 128x256 portrait needs.
# It was 192 for the General (100 tall) and the floating Doughboy: they keep
# more air, not less.
GALLERY_CEILING = 256
GALLERY_LIGHT = 192        # BESTIARY 10 rule 3: the Panzermensch needs >= 128

# Where the passage comes out, and where the PM lands with `warp 1024 1152`:
# mid-room, 448 units behind the row.
GALLERY_ARRIVAL = (1024, 1152)

GALLERY_ROW_Y = 1600       # 192 units from the north wall
GALLERY_FIRST_X = 256
GALLERY_SPACING = 224      # wider than any two radii plus a summoned recruit
GALLERY_FACING = 90        # north, away from the passage: asleep until shot

GALLERY_ROW = [
    ED_SD_REICH_RIFLEMAN,
    ED_SD_LEGION_TROOPER,
    ED_SD_STORMTROOPER,
    ED_SD_REICH_HOUND,
    ED_SD_DOUGHBOY,
    ED_SD_PANZERMENSCH,
    ED_SD_PANZERMENSCH_SCHWER,
    ED_SD_GENERAL,
]

# --- The way to the gallery (D41 v1) -----------------------------------------
# A manual door in the hall's north wall, beside the weapon row (x 640-768,
# between the RPG-7 and the ROKS-3 pickups, 144 north of them), then a
# dog-leg: north 64, east along a cross passage, north again into the
# gallery's south wall at x 960-1088, centred on GALLERY_ARRIVAL. A straight
# line through the passage must leave the south leg (x <= 768 at y 896) and
# enter the north leg (x >= 960 at y 960): 192 across in 64, so 576 across
# over the passage's 192 of depth, and the two mouths span 448. None exists.
PASSAGE_WIDTH = 128          # one SDDOOR1 leaf
PASSAGE_CEILING = 128
PASSAGE_LIGHT = 160          # one step under both rooms: a way through, not a room
DOOR_X = 640
DOOR_DEPTH = 64
GALLERY_DOOR = (DOOR_X, HALL_WIDTH, DOOR_X + PASSAGE_WIDTH, HALL_WIDTH + DOOR_DEPTH)
MOUTH_X = GALLERY_ARRIVAL[0] - PASSAGE_WIDTH // 2
LEG_SOUTH = (DOOR_X, HALL_WIDTH + DOOR_DEPTH, DOOR_X + PASSAGE_WIDTH, 896)
LEG_CROSS = (DOOR_X, 896, MOUTH_X + PASSAGE_WIDTH, 960)
LEG_NORTH = (MOUTH_X, 960, MOUTH_X + PASSAGE_WIDTH, GALLERY_Y1)
PASSAGE = (LEG_SOUTH, LEG_CROSS, LEG_NORTH)
TAG_GALLERY_DOOR = 1


def _room(floor: int, ceil: int, light: int, ceiling: str = CEILING_FLAT,
          tag: int | None = None, floor_flat: str = FLOOR_FLAT) -> Sector:
    return Sector(
        texturefloor=floor_flat,
        textureceiling=ceiling,
        heightfloor=floor,
        heightceiling=ceil,
        lightlevel=light,
        identifier=tag,
    )


def world_align(tm: TextMap) -> None:
    """Set offsetx on every one-sided room wall so its panel seams fall on
    multiples of PANEL_WIDTH in map space (the faces the player presses,
    the door leaf and the exit switch, are left whole at offset 0)."""
    for ld in tm.linedefs:
        if ld.sideback is not None:
            continue
        side = tm.sidedefs[ld.sidefront]
        if side.texturemiddle not in ALIGNED_TEXTURES:
            continue
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        along = a.x if a.y == b.y else a.y          # every RANGE line is axis-aligned
        forward = (b.x - a.x) + (b.y - a.y) > 0
        side.offsetx = int(along if forward else -along) % PANEL_WIDTH


def build_plan() -> tuple[TextMap, dict[str, int]]:
    """Build the map and return it with {zone name: sector index}."""
    tm = TextMap(comment=f"{MAP_NAME} generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")
    g = GridMap(tm, wall=WALL_TEXTURE)
    plan: dict[str, int] = {}

    def zone(name: str, sector: Sector, rects) -> int:
        index = tm.add_sector(sector)
        g.paint_all(index, rects)
        plan[name] = index
        return index

    zone("hall", _room(FLOOR_HEIGHT, CEILING_HEIGHT, LIGHT_LEVEL), [HALL])
    zone("exit_alcove", _room(FLOOR_HEIGHT, FLOOR_HEIGHT + SWITCH_HEIGHT, EXIT_LIGHT,
                              ceiling=LAMP_FLAT), [EXIT_ALCOVE])
    # The door: a closed sector (ceiling on its floor) whose own walls are
    # the steel track the leaf slides past. It rises to the lower of its two
    # neighbours' ceilings less 4: 124, over the player's 56.
    door = zone("gallery_door", _room(FLOOR_HEIGHT, FLOOR_HEIGHT, PASSAGE_LIGHT,
                                      tag=TAG_GALLERY_DOOR), [GALLERY_DOOR])
    g.set_wall(door, TRACK_TEXTURE)
    passage = zone("gallery_passage", _room(FLOOR_HEIGHT, PASSAGE_CEILING, PASSAGE_LIGHT), PASSAGE)
    # Its own walls, and the lintel the gallery sees over the mouth (a
    # two-sided line wears the material of the sector across it).
    g.set_wall(passage, PASSAGE_TEXTURE)
    zone("gallery", _room(FLOOR_HEIGHT, GALLERY_CEILING, GALLERY_LIGHT, floor_flat=GALLERY_FLOOR),
         [(GALLERY_X1, GALLERY_Y1, GALLERY_X2, GALLERY_Y2)])

    # Specific faces first: GridMap keeps the first style registered on a
    # segment. The door's leaf on both faces, each line wound with the door
    # behind it so it is pressed from either room.
    x1, y1, x2, y2 = GALLERY_DOOR
    leaf = door_raise_style(TAG_GALLERY_DOOR, door, texture=DOOR_TEXTURE)
    g.style_h(y1, x1, x2, leaf)
    g.style_h(y2, x1, x2, leaf)
    g.style_v(EXIT_ALCOVE[0], EXIT_ALCOVE[1], EXIT_ALCOVE[3], exit_switch_style(texture=EXIT_TEXTURE))
    # The alcove's side walls are the panel's steel frame.
    for y in (EXIT_ALCOVE[1], EXIT_ALCOVE[3]):
        g.style_h(y, EXIT_ALCOVE[0], EXIT_ALCOVE[2], LineStyle(texture=TRACK_TEXTURE))
    # The pictures: plain wall lines, no special, nothing moves.
    for _name, texture, axis, coord, lo, hi in poster_faces():
        (g.style_h if axis == "h" else g.style_v)(coord, lo, hi, LineStyle(texture=texture))
    g.build()
    world_align(tm)

    tm.add_thing(Thing(x=PLAYER_X, y=PLAYER_Y, type=ED_PLAYER1_START, angle=PLAYER_ANGLE))

    for i, ednum in enumerate(WEAPON_ROW):
        tm.add_thing(Thing(x=PICKUP_FIRST_X + i * PICKUP_SPACING, y=WEAPON_ROW_Y, type=ednum))
    for i, ednum in enumerate(AMMO_ROW):
        tm.add_thing(Thing(x=PICKUP_FIRST_X + i * PICKUP_SPACING, y=AMMO_ROW_Y, type=ednum))
    for ednum, x, y in SUPPORT_ITEMS:
        tm.add_thing(Thing(x=x, y=y, type=ednum))
    for x, y in BARRELS:
        tm.add_thing(Thing(x=x, y=y, type=ED_BARREL))
    for x, y in TARGETS:
        # `ambush` is the UDMF name of the "deaf" flag: the actor ignores
        # noise and only wakes when it sees the player.
        tm.add_thing(Thing(x=x, y=y, type=ED_ZOMBIEMAN, angle=180, extra={"ambush": True}))

    # The bestiary gallery: one of each enemy, deaf, facing away from the
    # passage's mouth.
    for i, ednum in enumerate(GALLERY_ROW):
        tm.add_thing(Thing(
            x=GALLERY_FIRST_X + i * GALLERY_SPACING,
            y=GALLERY_ROW_Y,
            type=ednum,
            angle=GALLERY_FACING,
            extra={"ambush": True},
        ))

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
