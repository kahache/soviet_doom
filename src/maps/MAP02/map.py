"""MAP02 "Engineering Test Range" - F4 arsenal verification map.

NOT a campaign map and not a design artefact: MAP01 belongs to
`level-designer` and is untouched by this file. This is a firing range whose
only job is to prove, in the engine, that each of the seven weapons can be
picked up, selected, fired and made to do damage.

Layout: one 2048 x 768 hall. The player spawns at the west end with the two
starting weapons; the other five pickups and the ammo sit within a few steps;
the east end holds the targets.

Textures are the same three IWAD assets MAP01 uses (listed in
docs/engine/MOD-SPEC.md section 5); no new IWAD reference is introduced.

Targets: explosive barrels prove splash damage; six thing-3004 targets prove
hitscan and projectile damage on a living actor. 3004 is Doom's zombieman
number, and since F5 it spawns OUR SD_ReichRifleman (`replaces ZombieMan`).
They are flagged `ambush` (deaf) so they only react to what they can see,
which keeps the range predictable.

F5 adds the BESTIARY GALLERY: a second room, connected to nothing, with one
of each enemy class standing in a row (docs/engine/BESTIARY.md 11.1). They
are deaf and face the far wall, away from the arrival spot, so they stay put
until shot one at a time. Nobody walks there: the PM reaches it from the
console with `warp 1024 1152` (GALLERY_ARRIVAL below).

Run it with:  MAP=MAP02 tools/run.sh
"""

from __future__ import annotations

from sdbuild.udmf import Linedef, Sector, Sidedef, TextMap, Thing

MAP_NAME = "MAP02"

# --- Geometry -------------------------------------------------------------
HALL_LENGTH = 2048     # x axis; long enough to see projectile travel and
                       # to outrange the ROKS-3 (528 units of reach)
HALL_WIDTH = 768       # y axis; room to strafe without leaving the lane
FLOOR_HEIGHT = 0
CEILING_HEIGHT = 128   # standard Doom height; STARTAN2 is 128 tall and tiles
                       # exactly once, so no texture seams
LIGHT_LEVEL = 192      # brighter than MAP01: this is a diagnostic space

# --- IWAD assets (must exist in both doom2.wad and freedoom2.wad) --------
WALL_TEXTURE = "STARTAN2"
FLOOR_FLAT = "FLOOR4_8"
CEILING_FLAT = "CEIL3_5"

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
]

AMMO_ROW = [
    ED_CLIP_BOX,
    ED_CLIP_BOX,
    ED_SHELL_BOX,
    ED_SHELL_BOX,
    ED_ROCKET_BOX,
    ED_CELL_PACK,
    ED_CELL_PACK,
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

# --- Bestiary gallery (F5) --------------------------------------------------
# A separate room north of the hall, sharing no line with it: nothing fired
# in the arsenal range is heard or seen here.
GALLERY_X1 = 0
GALLERY_X2 = HALL_LENGTH
GALLERY_Y1 = 1024          # 256 units of solid void above the hall's north wall
GALLERY_Y2 = 1792          # as wide as the hall
GALLERY_CEILING = 192      # the General is 100 tall; the Doughboy needs air to float
GALLERY_LIGHT = 192        # BESTIARY 10 rule 3: the Panzermensch needs >= 128

# Where the PM lands with `warp 1024 1152`: mid-room, 448 units behind the row.
GALLERY_ARRIVAL = (1024, 1152)

GALLERY_ROW_Y = 1600       # 192 units from the north wall
GALLERY_FIRST_X = 256
GALLERY_SPACING = 224      # wider than any two radii plus a summoned recruit
GALLERY_FACING = 90        # north, away from the arrival spot: asleep until shot

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


def build_textmap() -> TextMap:
    tm = TextMap(comment=f"{MAP_NAME} generated by src/maps/{MAP_NAME}/map.py - do not edit by hand")

    sector = tm.add_sector(
        Sector(
            texturefloor=FLOOR_FLAT,
            textureceiling=CEILING_FLAT,
            heightfloor=FLOOR_HEIGHT,
            heightceiling=CEILING_HEIGHT,
            lightlevel=LIGHT_LEVEL,
        )
    )

    # Clockwise with y up, so every line's front side faces inwards.
    corners = [
        (0, 0),
        (0, HALL_WIDTH),
        (HALL_LENGTH, HALL_WIDTH),
        (HALL_LENGTH, 0),
    ]
    verts = [tm.add_vertex(x, y) for x, y in corners]
    for i, v1 in enumerate(verts):
        v2 = verts[(i + 1) % len(verts)]
        side = tm.add_sidedef(Sidedef(sector=sector, texturemiddle=WALL_TEXTURE))
        tm.add_linedef(Linedef(v1=v1, v2=v2, sidefront=side, blocking=True))

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

    # The bestiary gallery: an isolated room (same IWAD textures as the hall,
    # so MOD-SPEC 5 needs no new row) and one of each enemy, deaf.
    tm.add_room_rect(
        GALLERY_X1, GALLERY_Y1, GALLERY_X2, GALLERY_Y2,
        Sector(
            texturefloor=FLOOR_FLAT,
            textureceiling=CEILING_FLAT,
            heightfloor=FLOOR_HEIGHT,
            heightceiling=GALLERY_CEILING,
            lightlevel=GALLERY_LIGHT,
        ),
        WALL_TEXTURE,
    )
    for i, ednum in enumerate(GALLERY_ROW):
        tm.add_thing(Thing(
            x=GALLERY_FIRST_X + i * GALLERY_SPACING,
            y=GALLERY_ROW_Y,
            type=ednum,
            angle=GALLERY_FACING,
            extra={"ambush": True},
        ))

    return tm


def lumps() -> list[tuple[str, bytes]]:
    """Return the WAD lumps in directory order (contract used by the build)."""
    return [
        (MAP_NAME, b""),
        ("TEXTMAP", build_textmap().to_bytes()),
        ("ENDMAP", b""),
    ]
