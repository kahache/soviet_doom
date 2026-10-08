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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

NAMESPACE_ZDOOM = "zdoom"
NO_TEXTURE = "-"  # UDMF/Doom convention for "no texture on this side part"


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
    blocking: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "v1": self.v1,
            "v2": self.v2,
            "sidefront": self.sidefront,
        }
        if self.sideback is not None:
            fields["sideback"] = self.sideback
        if self.blocking:
            fields["blocking"] = True
        fields.update(self.extra)
        return _block("linedef", fields)


@dataclass
class Sector:
    texturefloor: str
    textureceiling: str
    heightfloor: int = 0
    heightceiling: int = 128
    lightlevel: int = 160
    extra: dict[str, Any] = field(default_factory=dict)

    def to_udmf(self) -> str:
        fields: dict[str, Any] = {
            "heightfloor": self.heightfloor,
            "heightceiling": self.heightceiling,
            "texturefloor": self.texturefloor,
            "textureceiling": self.textureceiling,
            "lightlevel": self.lightlevel,
        }
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

    # Each add_* returns the index the new block will have in TEXTMAP.
    def add_vertex(self, x: float, y: float) -> int:
        self.vertices.append(Vertex(x, y))
        return len(self.vertices) - 1

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
