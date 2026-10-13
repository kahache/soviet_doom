"""Tiny UDMF (Universal Doom Map Format) TEXTMAP generator.

UDMF is the text-based map format GZDoom reads from the TEXTMAP lump. A map
is a list of blocks ("vertex", "linedef", "sidedef", "sector", "thing"), each
a brace-delimited set of `key = value;` pairs. Indices (v1, sidefront,
sector...) refer to the order in which blocks of that kind appear, so the
builder keeps insertion order and hands indices back to the caller.

Only the fields the project needs are modelled; anything else can be passed
through `extra` as raw key/value pairs. Field semantics follow the UDMF 1.1
spec plus the ZDoom extensions (namespace "zdoom").

Geometry convention (Doom): y grows "up" on the map editor view, and a
linedef's FRONT side is on the RIGHT of the v1 -> v2 direction. So the lines
of a closed room must run CLOCKWISE (as seen with y up) for their single
front sidedef to face the inside of the sector.

Two levels of API:

* The block classes (`Vertex`, `Linedef`, `Sidedef`, `Sector`, `Thing`) and
  `TextMap`, which are a thin, literal mapping onto UDMF.
* `GridMap`, a *painter* on top of them: you paint axis-aligned rectangles of
  sector onto a plane and it works out every shared edge, every one-sided
  wall and every winding for you. A floor plan of dozens of rooms is then a
  readable table of rectangles instead of hand-wound vertex lists. This is
  what blocker M2 asked for (`docs/levels/MAP01-zarya-7.md` section 10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

NAMESPACE_ZDOOM = "zdoom"
NO_TEXTURE = "-"  # UDMF/Doom convention for "no texture on this side part"

# --- ZDoom action specials -------------------------------------------------
# Argument SHAPES are verified against the engine's own translation tables in
# /Applications/GZDoom.app/Contents/MacOS/gzdoom.pk3 -> xlat/base.txt and
# xlat/doom.txt (e.g. `1 = USE|MONST|REP, Door_Raise (0, D_SLOW, VDOORWAIT,
# tag)`, `11 = USE, Exit_Normal (0)`).
#
# The NUMBERS below are NOT in any data file GZDoom ships: ZDoom's special
# table is compiled into the binary. They are therefore verified the only way
# left - empirically, by walking the map and seeing the door move (see
# docs/levels/MAP01-zarya-7.md section 9 for the evidence of each one).
SPECIAL_DOOR_CLOSE = 10            # Door_Close(tag, speed, lighttag)
SPECIAL_DOOR_OPEN = 11             # Door_Open(tag, speed, lighttag) - stays open
SPECIAL_DOOR_RAISE = 12            # Door_Raise(tag, speed, delay, lighttag)
SPECIAL_EXIT_NORMAL = 243          # Exit_Normal(pos)
# NOT VERIFIED - not used by MAP01 v0, kept so v2 does not re-guess them.
SPECIAL_LIGHT_CHANGE_TO_VALUE = 110  # Light_ChangeToValue(tag, value)
SPECIAL_LIGHT_FLICKER = 113          # Light_Flicker(tag, upper, lower)

# Door speeds and waits, from xlat/defines.i of gzdoom.pk3 (VERIFIED: that
# file is shipped text, not compiled).
DOOR_SPEED_SLOW = 16     # D_SLOW: the speed vanilla Doom doors use
DOOR_SPEED_NORMAL = 32   # D_NORMAL
DOOR_SPEED_FAST = 64     # D_FAST
DOOR_WAIT_TICS = 150     # VDOORWAIT: ~4.3 s before a Door_Raise closes again

# Sector specials. NOT VERIFIED (not used in v0; the secrets are flagged in
# v2). ZDoom ORs 1024 into a sector's special to mark it secret.
SECTOR_SPECIAL_SECRET = 1024

# Linedef flag fields of the zdoom UDMF namespace. All default to false, so a
# flag is written only when it is set. Keeping the list here (rather than as
# free-form `extra` keys) is what makes a typo a build error instead of a
# flag the engine silently ignores.
LINEDEF_FLAGS = (
    "blocking",          # impassable (every one-sided wall)
    "blockmonsters",
    "twosided",          # has a back side; the engine needs this explicitly
    "dontpegtop",        # "upper unpegged"
    "dontpegbottom",     # "lower unpegged" (door tracks)
    "secret",            # shows as one-sided on the automap
    "blocksound",
    "dontdraw",          # never appears on the automap
    "mapped",            # starts revealed on the automap
    "repeatspecial",     # the special can be triggered more than once
    "playercross",
    "playeruse",
    "monstercross",
    "monsteruse",
    "impact",
    "playerpush",
    "monsterpush",
    "missilecross",
    "monsteractivate",
    "blockplayers",
    "blockeverything",
)

LINEDEF_ARG_COUNT = 5  # arg0..arg4


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # UDMF accepts floats; repr keeps them exact and deterministic.
        return repr(value)
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    raise TypeError(f"unsupported UDMF value type: {type(value)!r}")


def _block(kind: str, fields: dict[str, Any]) -> str:
    lines = [f"{kind}", "{"]
    for key, value in fields.items():
        if value is None:
            continue
        lines.append(f"\t{key} = {_fmt(value)};")
    lines.append("}")
    return "\n".join(lines)


@dataclass
class Vertex:
    x: float
    y: float

    def to_udmf(self) -> str:
        return _block("vertex", {"x": float(self.x), "y": float(self.y)})


@dataclass
class Sidedef:
    sector: int
    texturemiddle: str = NO_TEXTURE
    texturetop: str = NO_TEXTURE
    texturebottom: str = NO_TEXTURE
    offsetx: int = 0
    offsety: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "sector": self.sector,
            "texturetop": self.texturetop,
            "texturemiddle": self.texturemiddle,
            "texturebottom": self.texturebottom,
            "offsetx": self.offsetx,
            "offsety": self.offsety,
        }
        fields.update(self.extra)
        return _block("sidedef", fields)


@dataclass
class Linedef:
    v1: int
    v2: int
    sidefront: int
    sideback: int | None = None  # None -> one-sided (UDMF default -1)
    special: int = 0
    arg0: int = 0
    arg1: int = 0
    arg2: int = 0
    arg3: int = 0
    arg4: int = 0
    identifier: int | None = None  # UDMF `id`: the linedef's own tag
    flags: tuple[str, ...] = ()
    blocking: bool = False  # kept as a named argument: the commonest flag
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = [f for f in self.flags if f not in LINEDEF_FLAGS]
        if unknown:
            raise ValueError(f"unknown linedef flag(s): {', '.join(unknown)}")

    @property
    def args(self) -> tuple[int, int, int, int, int]:
        return (self.arg0, self.arg1, self.arg2, self.arg3, self.arg4)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "v1": self.v1,
            "v2": self.v2,
            "sidefront": self.sidefront,
        }
        if self.sideback is not None:
            fields["sideback"] = self.sideback
        if self.identifier is not None:
            fields["id"] = self.identifier
        if self.blocking:
            fields["blocking"] = True
        for name in LINEDEF_FLAGS:
            if name in self.flags and name not in fields:
                fields[name] = True
        if self.special:
            fields["special"] = self.special
            for i, value in enumerate(self.args):
                fields[f"arg{i}"] = value
        fields.update(self.extra)
        return _block("linedef", fields)


@dataclass
class Sector:
    texturefloor: str
    textureceiling: str
    heightfloor: int = 0
    heightceiling: int = 128
    lightlevel: int = 160
    identifier: int | None = None  # UDMF `id`: the sector tag doors act on
    special: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "heightfloor": self.heightfloor,
            "heightceiling": self.heightceiling,
            "texturefloor": self.texturefloor,
            "textureceiling": self.textureceiling,
            "lightlevel": self.lightlevel,
        }
        if self.identifier is not None:
            fields["id"] = self.identifier
        if self.special:
            fields["special"] = self.special
        fields.update(self.extra)
        return _block("sector", fields)


@dataclass
class Thing:
    """A map object. `type` is the DoomEdNum (1 = Player 1 start).

    In the zdoom namespace every skill/mode flag defaults to false, so a
    thing that should always appear must set skill1..skill5 and
    single/coop/dm explicitly. We default them all to True.
    """

    x: float
    y: float
    type: int
    angle: int = 0
    height: float = 0.0
    skill1: bool = True
    skill2: bool = True
    skill3: bool = True
    skill4: bool = True
    skill5: bool = True
    single: bool = True
    coop: bool = True
    dm: bool = True
    extra: dict[str, Any] = field(default_factory=dict)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "x": float(self.x),
            "y": float(self.y),
            "height": float(self.height),
            "angle": self.angle,
            "type": self.type,
            "skill1": self.skill1,
            "skill2": self.skill2,
            "skill3": self.skill3,
            "skill4": self.skill4,
            "skill5": self.skill5,
            "single": self.single,
            "coop": self.coop,
            "dm": self.dm,
        }
        fields.update(self.extra)
        return _block("thing", fields)


class TextMap:
    """Accumulates map blocks and renders the TEXTMAP lump text."""

    def __init__(self, namespace: str = NAMESPACE_ZDOOM, comment: str = ""):
        self.namespace = namespace
        self.comment = comment
        self.vertices: list[Vertex] = []
        self.linedefs: list[Linedef] = []
        self.sidedefs: list[Sidedef] = []
        self.sectors: list[Sector] = []
        self.things: list[Thing] = []
        self._vertex_index: dict[tuple[float, float], int] = {}

    # Each add_* returns the index the new block will have in TEXTMAP.
    def add_vertex(self, x: float, y: float) -> int:
        self.vertices.append(Vertex(x, y))
        return len(self.vertices) - 1

    def vertex(self, x: float, y: float) -> int:
        """add_vertex, but reusing a vertex already at that exact point.

        Shared corners are the normal case once rooms touch, and a duplicate
        vertex at the same spot is how "leaks" and node-builder artefacts get
        born, so anything geometric goes through here.
        """
        key = (float(x), float(y))
        index = self._vertex_index.get(key)
        if index is None:
            index = self.add_vertex(x, y)
            self._vertex_index[key] = index
        return index

    def add_sidedef(self, sidedef: Sidedef) -> int:
        self.sidedefs.append(sidedef)
        return len(self.sidedefs) - 1

    def add_linedef(self, linedef: Linedef) -> int:
        self.linedefs.append(linedef)
        return len(self.linedefs) - 1

    def add_sector(self, sector: Sector) -> int:
        self.sectors.append(sector)
        return len(self.sectors) - 1

    def add_thing(self, thing: Thing) -> int:
        self.things.append(thing)
        return len(self.things) - 1

    def add_room_rect(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        sector: Sector,
        wall: str,
    ) -> int:
        """Add an isolated rectangular room: one sector, four closed walls.

        The four lines are wound clockwise with y up, so each one-sided front
        side faces the interior. Use `GridMap` instead as soon as rooms have
        to touch each other; this helper is for a room that stands alone
        (a test fixture, a one-room map).

        Returns the new sector's index.
        """
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"degenerate rectangle ({x1},{y1})-({x2},{y2})")
        index = self.add_sector(sector)
        corners = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
        verts = [self.vertex(x, y) for x, y in corners]
        for i, v1 in enumerate(verts):
            v2 = verts[(i + 1) % len(verts)]
            side = self.add_sidedef(Sidedef(sector=index, texturemiddle=wall))
            self.add_linedef(Linedef(v1=v1, v2=v2, sidefront=side, blocking=True))
        return index

    def render(self) -> str:
        parts: list[str] = []
        if self.comment:
            parts.append("\n".join(f"// {line}" for line in self.comment.splitlines()))
        parts.append(f'namespace = "{self.namespace}";')
        for group in (self.things, self.vertices, self.linedefs, self.sidedefs, self.sectors):
            for item in group:
                parts.append(item.to_udmf())
        return "\n\n".join(parts) + "\n"

    def to_bytes(self) -> bytes:
        return self.render().encode("ascii")


# ---------------------------------------------------------------------------
# GridMap: painting a floor plan out of axis-aligned rectangles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LineStyle:
    """What to put on the linedefs covering one boundary segment.

    `back_sector` pins the orientation: the line is wound so that this
    sector ends up on the BACK side. That matters because ZDoom triggers a
    `playeruse` special only from the FRONT side, so a door's two flanking
    lines must both face away from the door sector or the door opens from
    one side only.

    `texture` overrides the GridMap's wall texture on this segment's two
    sidedefs. A surface the player is meant to press has to look different
    from the wall next to it; that is not decoration, it is the only thing
    telling him the door is a door. It is also how a single wall run gets a
    texture of its own - the red route stripe of MAP01, say - without
    changing the room it belongs to.

    `peg_bottom` is the tri-state override of the GridMap's floor-pegging
    default (see `GridMap.peg_bottom`). A door leaf MUST set it False: the
    leaf is an upper texture that has to ride up with the door's ceiling.
    """

    special: int = 0
    args: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
    flags: tuple[str, ...] = ()
    back_sector: int | None = None
    texture: str | None = None
    peg_bottom: bool | None = None

    def __post_init__(self) -> None:
        unknown = [f for f in self.flags if f not in LINEDEF_FLAGS]
        if unknown:
            raise ValueError(f"unknown linedef flag(s): {', '.join(unknown)}")
        if len(self.args) != LINEDEF_ARG_COUNT:
            raise ValueError(f"a line special takes exactly {LINEDEF_ARG_COUNT} args")


@dataclass(frozen=True)
class _Rule:
    """A LineStyle claimed over one axis-aligned segment of the plane."""

    vertical: bool
    coord: int   # x for a vertical segment, y for a horizontal one
    lo: int
    hi: int
    style: LineStyle


@dataclass(frozen=True)
class _Paint:
    sector: int
    x1: int
    y1: int
    x2: int
    y2: int


class GridMap:
    """Paint rectangles of sector onto a plane, then emit correct UDMF.

    Painting is last-wins, like a raster: paint the hangar, then paint the
    catwalk on top of it, and the catwalk's cells stop belonging to the
    hangar. A sector may be painted as several rectangles; rectangles of the
    same sector that touch are simply merged (no linedef between them).

    What the emitter guarantees, which is the whole reason this exists:

    * every boundary between two different sectors becomes a two-sided
      linedef, and every boundary with the void becomes a one-sided wall;
    * partial overlaps are split correctly (the classic source of HOM);
    * winding is always such that the front sidedef faces the right sector;
    * collinear neighbouring segments that are identical in every respect
      are merged back into one linedef, so the output stays readable.
    """

    def __init__(self, textmap: TextMap, wall: str, peg_bottom: bool = True):
        self.tm = textmap
        self.wall = wall
        # Floor pegging. Doom aligns a wall texture to the CEILING by
        # default, so in any room that is not an exact multiple of the
        # texture height the cut panel lands on the floor - a half panel
        # with its grime line floating in mid-air. Pegged to the floor
        # instead (`dontpegbottom`), panels stack up from the ground the way
        # they were poured and the cut hides at the ceiling. It also puts
        # SDCONC2's red stripe at the same height in every room, which is
        # the whole point of having a stripe.
        self.peg_bottom = peg_bottom
        self._paints: list[_Paint] = []
        self._rules: list[_Rule] = []
        # Per-sector wall texture.
        #
        # A ONE-SIDED wall wears the material of the room it encloses: you
        # are inside that room looking at its own wall.
        #
        # A TWO-SIDED line wears the material of the OTHER sector, because
        # that is whose structure you are looking at. The lower part of a
        # sidedef is the flank of the neighbour's raised floor - the side of
        # the transporter cradle, the front of the catwalk - and its upper
        # part is the flank of the neighbour's dropped ceiling, i.e. the
        # lintel over a doorway. Dressing those in the material of the room
        # you are standing in is the classic way to get a steel catwalk with
        # a concrete face. So: `wall_of(the sector across the line)`.
        self._walls: dict[int, str] = {}

    def set_wall(self, sector: int, texture: str) -> None:
        """Give one sector's own sidedefs a wall texture of their own."""
        self._walls[sector] = texture

    def set_walls(self, texture: str, sectors: Iterable[int]) -> None:
        for sector in sectors:
            self.set_wall(sector, texture)

    def wall_of(self, sector: int | None) -> str:
        return self._walls.get(sector, self.wall) if sector is not None else self.wall

    # --- input ------------------------------------------------------------
    def paint(self, sector: int, x1: int, y1: int, x2: int, y2: int) -> None:
        """Claim the rectangle [x1,x2] x [y1,y2] for `sector` (last wins)."""
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"degenerate rectangle ({x1},{y1})-({x2},{y2})")
        self._paints.append(_Paint(sector, x1, y1, x2, y2))

    def paint_all(self, sector: int, rects: Iterable[tuple[int, int, int, int]]) -> None:
        for x1, y1, x2, y2 in rects:
            self.paint(sector, x1, y1, x2, y2)

    def style_v(self, x: int, y1: int, y2: int, style: LineStyle) -> None:
        """Apply `style` to the boundary segment on the vertical line x."""
        if y1 >= y2:
            raise ValueError(f"degenerate vertical segment at x={x}: {y1}..{y2}")
        self._rules.append(_Rule(True, x, y1, y2, style))

    def style_h(self, y: int, x1: int, x2: int, style: LineStyle) -> None:
        """Apply `style` to the boundary segment on the horizontal line y."""
        if x1 >= x2:
            raise ValueError(f"degenerate horizontal segment at y={y}: {x1}..{x2}")
        self._rules.append(_Rule(False, y, x1, x2, style))

    # --- the grid ---------------------------------------------------------
    def _axes(self) -> tuple[list[int], list[int]]:
        xs: set[int] = set()
        ys: set[int] = set()
        for p in self._paints:
            xs.update((p.x1, p.x2))
            ys.update((p.y1, p.y2))
        # Rule endpoints must be grid lines too, or a rule could cover half
        # an elementary segment and there would be no way to honour it.
        for r in self._rules:
            if r.vertical:
                xs.add(r.coord)
                ys.update((r.lo, r.hi))
            else:
                ys.add(r.coord)
                xs.update((r.lo, r.hi))
        return sorted(xs), sorted(ys)

    def _occupancy(self, xs: list[int], ys: list[int]) -> dict[tuple[int, int], int]:
        xi = {v: i for i, v in enumerate(xs)}
        yi = {v: i for i, v in enumerate(ys)}
        occ: dict[tuple[int, int], int] = {}
        for p in self._paints:
            for i in range(xi[p.x1], xi[p.x2]):
                for j in range(yi[p.y1], yi[p.y2]):
                    occ[(i, j)] = p.sector
        return occ

    def _style_for(self, vertical: bool, coord: int, lo: int, hi: int) -> LineStyle | None:
        """The style whose segment contains [lo,hi] on this grid line."""
        for r in self._rules:
            if r.vertical == vertical and r.coord == coord and r.lo <= lo and hi <= r.hi:
                return r.style
        return None

    # --- output -----------------------------------------------------------
    def build(self) -> None:
        """Emit every vertex, sidedef and linedef the painted plan implies."""
        xs, ys = self._axes()
        occ = self._occupancy(xs, ys)

        # Vertical grid lines: cell (i-1, j) is west of x=xs[i], (i, j) east.
        for i, x in enumerate(xs):
            runs = self._runs(
                len(ys) - 1,
                lambda j, i=i: (occ.get((i - 1, j)) if i > 0 else None,
                                occ.get((i, j)) if i < len(xs) - 1 else None),
                lambda j, x=x: self._style_for(True, x, ys[j], ys[j + 1]),
            )
            for (west, east, style), j1, j2 in runs:
                self._emit(x, ys[j1], x, ys[j2], west, east, style, vertical=True)

        # Horizontal grid lines: cell (i, j-1) is south of y=ys[j], (i, j) north.
        for j, y in enumerate(ys):
            runs = self._runs(
                len(xs) - 1,
                lambda i, j=j: (occ.get((i, j - 1)) if j > 0 else None,
                                occ.get((i, j)) if j < len(ys) - 1 else None),
                lambda i, y=y: self._style_for(False, y, xs[i], xs[i + 1]),
            )
            for (south, north, style), i1, i2 in runs:
                self._emit(xs[i1], y, xs[i2], y, south, north, style, vertical=False)

    @staticmethod
    def _runs(count, sides, style_of):
        """Group consecutive elementary segments that are identical.

        Yields ((near, far, style), start, stop) with [start, stop) the run of
        elementary indices. Segments where both sides are the same sector (or
        both void) carry no linedef and break the run.
        """
        out = []
        key = None
        start = 0
        for k in range(count):
            near, far = sides(k)
            current = None if near == far else (near, far, style_of(k))
            if current != key:
                if key is not None:
                    out.append((key, start, k))
                key, start = current, k
        if key is not None:
            out.append((key, start, count))
        return out

    def _emit(self, ax, ay, bx, by, near, far, style, vertical: bool) -> None:
        """One linedef for the segment, wound so `near` is the front side.

        For a vertical line `near` is the west side and the line runs SOUTH
        (direction (0,-1), whose right-hand side is west). For a horizontal
        line `near` is the south side and the line runs EAST (direction
        (1,0), whose right-hand side is south). When `near` is void the
        winding is reversed so the existing sector is still the front.
        """
        style = style or LineStyle()
        if vertical:
            forward = ((ax, by), (bx, ay))   # south: front = west = near
        else:
            forward = ((ax, ay), (bx, by))   # east: front = south = near
        reverse = (forward[1], forward[0])

        front_sector, back_sector = near, far
        points = forward
        if front_sector is None:
            front_sector, back_sector = far, near
            points = reverse
        if style.back_sector is not None and back_sector != style.back_sector:
            if front_sector != style.back_sector:
                raise ValueError(
                    f"LineStyle.back_sector={style.back_sector} is on neither side "
                    f"of the segment ({ax},{ay})-({bx},{by})"
                )
            front_sector, back_sector = back_sector, front_sector
            points = reverse if points is forward else forward

        v1 = self.tm.vertex(*points[0])
        v2 = self.tm.vertex(*points[1])
        flags = set(style.flags)
        # One-sided: own material. Two-sided: the neighbour's (see __init__).
        front_wall = style.texture or self.wall_of(
            front_sector if back_sector is None else back_sector)
        back_wall = style.texture or self.wall_of(front_sector)
        peg = self.peg_bottom if style.peg_bottom is None else style.peg_bottom
        if peg:
            flags.add("dontpegbottom")
        if back_sector is None:
            front = self.tm.add_sidedef(Sidedef(sector=front_sector, texturemiddle=front_wall))
            back_index = None
            flags.add("blocking")
        else:
            # Both side parts are textured on both sides: wherever the two
            # sectors differ in floor or ceiling height the engine needs a
            # texture there, and where they agree it simply draws nothing.
            # On a closed door the upper part IS the door leaf, and it is
            # left pegged (no `dontpegtop`) so the texture rides up with the
            # ceiling and the leaf looks like it slides.
            front = self.tm.add_sidedef(
                Sidedef(sector=front_sector, texturetop=front_wall, texturebottom=front_wall)
            )
            back_index = self.tm.add_sidedef(
                Sidedef(sector=back_sector, texturetop=back_wall, texturebottom=back_wall)
            )
            flags.add("twosided")
        self.tm.add_linedef(
            Linedef(
                v1=v1,
                v2=v2,
                sidefront=front,
                sideback=back_index,
                special=style.special,
                arg0=style.args[0],
                arg1=style.args[1],
                arg2=style.args[2],
                arg3=style.args[3],
                arg4=style.args[4],
                flags=tuple(sorted(flags)),
            )
        )


# --- Ready-made styles -----------------------------------------------------

def door_raise_style(tag: int, door_sector: int, speed: int = DOOR_SPEED_SLOW,
                     delay: int = DOOR_WAIT_TICS, texture: str | None = None) -> LineStyle:
    """A manual door: press to open, closes again, works from both sides."""
    return LineStyle(
        special=SPECIAL_DOOR_RAISE,
        args=(tag, speed, delay, 0, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,   # the leaf is an upper texture: it rides with the door
    )


def door_open_style(tag: int, door_sector: int, speed: int = DOOR_SPEED_SLOW,
                    texture: str | None = None) -> LineStyle:
    """A push panel that opens and STAYS open: cannot consume a gate."""
    return LineStyle(
        special=SPECIAL_DOOR_OPEN,
        args=(tag, speed, 0, 0, 0),
        flags=("playeruse", "repeatspecial"),
        back_sector=door_sector,
        texture=texture,
        peg_bottom=False,   # the leaf is an upper texture: it rides with the door
    )


def remote_door_style(door_sector: int, texture: str | None = None) -> LineStyle:
    """A door that only a switch opens: no special, just the leaf's face."""
    return LineStyle(back_sector=door_sector, texture=texture, peg_bottom=False)


def switch_door_open_style(tag: int, speed: int = DOOR_SPEED_SLOW,
                           texture: str | None = None) -> LineStyle:
    """A wall switch that opens a remote door for good. Repeatable."""
    return LineStyle(
        special=SPECIAL_DOOR_OPEN,
        args=(tag, speed, 0, 0, 0),
        flags=("playeruse", "repeatspecial"),
        texture=texture,
    )


def exit_switch_style(texture: str | None = None) -> LineStyle:
    """The level exit, on a one-sided wall line."""
    return LineStyle(special=SPECIAL_EXIT_NORMAL, args=(0, 0, 0, 0, 0),
                     flags=("playeruse",), texture=texture)
