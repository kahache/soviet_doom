#!/usr/bin/env python3
"""Static validator for the mod package: check dist/sovietdoom.pk3 offline.

This is the half of the automated verification that does NOT start the
engine. `tools/smoke.py` boots GZDoom and greps its log; it is slow, needs a
GZDoom install, an IWAD and a display, and it only sees what the engine
happened to touch while loading one map. This tool opens the zip and reads
the bytes: it runs in milliseconds, on any machine, with no GZDoom and no
IWAD, and it looks at *everything* in the package, including assets and maps
the engine would never load unless the player walked there.

The two are complementary, and on purpose there is no overlap:

  smoke.py  (runtime)          check_pk3.py (static)
  ------------------------     --------------------------------------------
  engine parses ZScript        every #include resolves to a packed file
  "Unknown texture" on load    every texture/flat a TEXTMAP names exists
  MAPINFO accepted             map WAD structure, lump order, UDMF parses
  map actually reached         lump names fit the 8-char WAD limit
  (sees nothing else)          PNG colour model, palette, sizes; sprite
                               rotations; licence provenance of every asset

Checks (one block of output per category):

  package    the file is a readable zip, no corrupt member, the paths the
             MOD-SPEC 2 layout requires are present
  lumps      root entries map to legal lump names (<= 8 ASCII chars, no
             extension in the lump name, valid characters)
  maps       every maps/*.wad is a PWAD whose directory is exactly
             marker / TEXTMAP / ENDMAP, and whose TEXTMAP parses as UDMF;
             every map MAPINFO names (`map`, `episode`, `next`) is packed,
             and every packed map has a MAPINFO `map` block (warning)
  textures   every texturetop/middle/bottom/floor/ceiling a TEXTMAP names
             (plus MAPINFO sky1/sky2) exists in the PK3 or is declared as an
             IWAD asset in MOD-SPEC 5. A name that resolves nowhere is
             exactly what the engine reports as "Unknown texture".
             The OFF and ON textures of every ANIMDEFS `switch` pair, and
             every frame of a `flat` / `texture` animation, are held to the
             same rule (MOD-SPEC 4.3, debt T16; animations since N6c)
  images     PNGs under textures/ and flats/ are colour type 3 (indexed),
             every colour they use is in docs/art/palette.json, and their
             dimensions follow the contract (the declared skies,
             SKY_TEXTURES, at a sky size, D113). The one exception is the
             masked wall textures (MASKED_TEXTURES, D66): RGBA, alpha hard
             0/255, every opaque pixel in the palette
  sprites    sprite lumps are NAMEFR[FR]: 4-char name, frame letter,
             rotation digit, and an optional mirrored pair (SDHNA2A8);
             every declared rotation set is complete, mirrors counted.
             Every sprite a ZScript `States` block names is packed under
             sprites/, is the engine's (TNT1, ####, ----), or is declared
             as an IWAD sprite in MOD-SPEC 5 - the same rule as textures
             (F5: four enemies draw our own sprites since D54-D56, the
             other three and the arsenal's held frames still borrow
             Freedoom's)
  licences   every packed asset has a row in docs/art/LICENSES.md
  zscript    every #include, transitively, points at a file in the PK3
  menus      every `Font "X"` in MENUDEF is an engine font or a packed
             fonts/<x>/ folder (MOD-SPEC 6.6: the menu font SDMENU)
  localized  every language variant sits in localized/textures/, is named
             <BASE>.<lang>[-<lang>].<ext> with 2-3 letter language IDs, has a
             packed base graphic and the base's exact size: the four things
             GZDoom's AddLocalizedVariants checks at load (MOD-SPEC 2)

Usage:
  python3 tools/check_pk3.py                      # dist/sovietdoom.pk3
  python3 tools/check_pk3.py --pk3 other.pk3
  python3 tools/check_pk3.py --json               # machine-readable, for CI
  python3 tools/check_pk3.py --quiet              # only the failures

Exit codes:
  0  everything passed (warnings do not fail the run; --strict makes them)
  1  at least one error

Python 3 standard library only, by design: this must run in a bare CI box.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PK3 = PROJECT_ROOT / "dist" / "sovietdoom.pk3"
DEFAULT_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
DEFAULT_LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
DEFAULT_PALETTE = PROJECT_ROOT / "docs" / "art" / "palette.json"

EXIT_OK = 0
EXIT_FAILURES = 1

# --- The contract, as named constants -------------------------------------
# MOD-SPEC 2 "PK3 layout" and the WAD format itself.
MAX_LUMP_NAME = 8                       # hard limit of the WAD directory
LUMP_NAME_EXTRA_CHARS = "_[]-\\"        # non-alphanumerics GZDoom tolerates
REQUIRED_ROOT_LUMPS = ("MAPINFO", "LANGUAGE", "zscript.txt")
MAPS_DIR = "maps"
ZSCRIPT_ENTRY = "zscript.txt"

# MOD-SPEC 2: "marker MAPxx (empty), TEXTMAP, ENDMAP (empty)".
MAP_TEXT_LUMP = "TEXTMAP"
MAP_END_LUMP = "ENDMAP"

# Folders the build packs verbatim (sdbuild.pk3.ASSET_DIRS) plus zscript/.
ASSET_DIRS = ("textures", "flats", "sprites", "sounds", "music", "graphics", "patches", "hires", "fonts")
# Folders a wall texture / flat name can be satisfied from.
TEXTURE_DIRS = ("textures", "flats", "patches", "graphics", "hires")
# Folders whose contents must be listed in LICENSES.md.
LICENSED_DIRS = ASSET_DIRS

# UDMF keys that name a wall texture or a flat (UDMF 1.1 + zdoom namespace).
WALL_TEXTURE_KEYS = ("texturetop", "texturemiddle", "texturebottom")
FLAT_TEXTURE_KEYS = ("texturefloor", "textureceiling")
NO_TEXTURE = "-"                        # UDMF "this side part has no texture"
# Engine-internal names that never correspond to a packed or IWAD lump.
BUILTIN_TEXTURE_NAMES = frozenset({"-", "", "F_SKY1", "SKY", "AASHITTY", "AASTINKY"})

# Image contract (docs/art/TEXTURE-INDEX.md batch 1).
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_COLOUR_TYPE_PALETTE = 3
PNG_COLOUR_TYPE_RGBA = 6
PNG_RGBA_CHANNELS = 4
# Masked wall textures (D66): the only lumps under textures/ that may be RGBA
# instead of indexed. A masked texture is drawn as the middle texture of a
# two-sided line and the engine leaves its transparent pixels open, so the
# player sees through the gaps. GZDoom's PNG loader marks every colour-type-6
# PNG as masked (`case 6: bMasked = true;` in
# src/common/textures/formats/pngtexture.cpp, tag g4.14.2; VERIFIED in the
# source 2026-10-14, NOT VERIFIED on screen until the PM's engine pass, D26).
# Held to: colour type 6 at 8 bits, alpha only 0 or 255 (hard, like the
# sprites: the software renderer has no partial transparency on walls), and
# every opaque pixel inside the palette. Flats can never be masked.
MASKED_TEXTURES = frozenset({"SDCHAN1",            # the Tankograd chain and hook (D66)
                             "SDKREM2",            # the Kremlin merlon, MAP06 (D107)
                             "SDINSL1",            # the dam's HV insulator string, MAP05 (D107)
                             # D113 (installed 2026-10-22): Episode 3's crane
                             # jib, MAP08; Episode 2 round 2's window bars and
                             # HV fence, MAP05, and the Kremlin's ruby star, MAP06.
                             "SDCRAN1", "SDGRIL1", "SDHVLT1", "SDRUBY1"})
MASKED_ALPHA = frozenset({0, 255})
DIMENSION_MULTIPLE = 8                  # Doom tiles on powers of two
FLAT_SIZE = (64, 64)                    # a Doom flat is 64x64 by definition
# Wall sizes the project allows (MOD-SPEC 2). 128x256 was added when the CEO
# approved the taller Lenin poster: at 128x128 the portrait had no room.
# 256x64 since D66: the Tankograd works banner SDSLOG1, one slogan in two lines.
ALLOWED_WALL_SIZES = ((64, 64), (64, 128), (128, 64), (128, 128), (128, 256),  # crates since D29
                      (256, 64))
# Sky textures (D113): MAPINFO's sky1 of MAP01, MAP03-09 and RANGE names our own skies, one
# 360-degree turn at 1024x128 (Freedoom's SKY1 is 256x128 and repeats four
# times round the view; how GZDoom maps the wider picture is NOT VERIFIED
# until the PM's engine pass, D26). Declared, like the masked textures: a
# lump in SKY_TEXTURES may be a sky size, any other wall at 1024x128 is
# still an unagreed size.
SKY_SIZES = ((1024, 128),)
SKY_TEXTURES = frozenset({"SDSKY1",                # the Urals at night, MAP04 and MAP05
                          "SDSKY2",                # Moscow at night, MAP06
                          "SDSKY3",                # the polar night with aurora, MAP07 (gen_episode3_skies)
                          "SDSKY4",                # the Kola fjord at night, MAP08
                          "SDSKY5",                # the Tunguska taiga and the portal's glow, MAP09
                          "SDSKY6",                # the Zarya-7 cosmodrome before dawn, MAP01 and RANGE (gen_episode1_skies)
                          "SDSKY7"})               # Tankograd at night, MAP03

# Sprite naming (Doom convention): NAMEFR or NAMEFRFR.
SPRITE_NAME_LEN = 4
SPRITE_ROTATIONS_8 = tuple("12345678")
SPRITE_ROTATIONS_16 = tuple("123456789ABCDEFG")
SPRITE_ROTATION_ALL = "0"               # one sprite for every viewing angle
SPRITE_FRAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]"
# Sprite names a States block may use without any lump behind them: TNT1 is
# the engine's own invisible sprite (gzdoom.pk3 sprites/), "####" and "----"
# mean "keep the previous sprite / frame".
ENGINE_SPRITES = frozenset({"TNT1", "####", "----"})
# State-flow keywords that are four letters long and would otherwise read as
# a sprite name at the start of a state line ("Goto Ready").
STATE_KEYWORDS = frozenset({"GOTO", "LOOP", "STOP", "WAIT", "FAIL"})
# The MOD-SPEC 5 Type cell that marks a row as a sprite rather than a texture.
SPEC_SPRITE_TYPE = "sprite"
RE_STATES_OPEN = re.compile(r"\bStates\s*\{", re.I)
RE_STATE_LABEL = re.compile(r"^\s*[A-Za-z_][\w.]*\s*:(?!:)")
RE_STATE_FRAME = re.compile(r'^\s*"?([A-Za-z0-9_#\-]{4})"?\s+"?([A-Za-z\[\]\\#]+)"?\s+\S')

RE_INCLUDE = re.compile(r'^\s*#include\s+"([^"]+)"', re.M)
RE_BACKTICKED = re.compile(r"`([^`]+)`")
RE_MAPINFO_SKY = re.compile(r"^\s*sky[12]\s*=\s*\"([^\"]*)\"", re.M | re.I)
# The maps MAPINFO names (MOD-SPEC 4): every `map X` and `episode X` block,
# and every `next` / `secretnext` that is a map rather than an end sequence
# (GZDoom's are all spelt End...: endtitle, EndGame { }, EndPic...). A map
# name is any lump name; since D62 the practice range is RANGE, not MAPxx.
RE_MAPINFO_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
RE_MAPINFO_BLOCK_MAP = re.compile(r'^\s*(map|episode)\s+"?([A-Za-z0-9_]+)"?', re.M | re.I)
RE_MAPINFO_NEXT_MAP = re.compile(r'^\s*(next|secretnext)\s*=\s*"?([A-Za-z0-9_]+)"?', re.M | re.I)
MAPINFO_END_PREFIX = "end"
# ANIMDEFS (MOD-SPEC 4.3). Syntax as the engine writes it in gzdoom.pk3 ->
# animdefs.txt (GZDoom g4.14.2): `switch [game [tier]] [quest] OFF [quest]
# on [sound S] pic ON tics N ... [off [sound S] pic OFF2 tics N]`.
ANIMDEFS_LUMPS = ("ANIMDEFS", "animdefs.txt")
ANIMDEFS_GAMES = frozenset({"doom", "heretic", "hexen", "strife"})
# Keywords that open a new top-level ANIMDEFS definition, so they end a switch.
ANIMDEFS_TOP_LEVEL = frozenset({
    "switch", "texture", "flat", "animateddoor", "warp", "warp2",
    "cameratexture", "canvastexture", "skyoffset",
})
RE_ANIMDEFS_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
RE_ANIMDEFS_TOKEN = re.compile(r'"[^"]*"|\S+')
RE_TEXTURES_DEF = re.compile(
    r"^\s*(?:texture|walltexture|flat|sprite|graphic)\s+\"?([A-Za-z0-9_\[\]\\\-]+)\"?",
    re.M | re.I,
)

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# MENUDEF (MOD-SPEC 6.6). Fonts GZDoom provides by name: the names in
# gzdoom.exe g4.14.2 and in gzdoom.pk3/menudef.txt. Any other name must be a
# folder font packed at fonts/<name>/ (MOD-SPEC 2); a font that resolves
# nowhere cannot draw the menu it was named for.
MENUDEF_LUMP = "MENUDEF"
ENGINE_FONTS = frozenset(name.upper() for name in (
    "SmallFont", "SmallFont2", "BigFont", "BigUpper", "ConsoleFont",
    "NewSmallFont", "NewConsoleFont", "IntermissionFont",
    "OriginalSmallFont", "OriginalBigFont",
))
FONTS_DIR = "fonts"
RE_MENUDEF_FONT = re.compile(r'^[ \t]*Font[ \t]+"([^"]+)"', re.M | re.I)

CATEGORIES = ("package", "lumps", "maps", "textures", "images", "sprites", "licences", "zscript", "menus",
              "localized")

# Language variants of graphics (MOD-SPEC 2; sdbuild.pk3.LOCALIZED_DIR). The
# rules below are GZDoom g4.14.2's FTextureManager::AddLocalizedVariants
# (src/common/textures/texturemanager.cpp), read in the source: it scans
# exactly LOCALIZED_TEXTURES_DIR, splits the file name on ".", takes the
# first token as the base graphic, the second as "-"-separated language IDs
# of 2 or 3 characters, and refuses a variant whose size differs from the
# base's. Each refusal is a console line, not a load error, so without this
# check a broken variant would ship silently.
LOCALIZED_DIR = "localized"
LOCALIZED_TEXTURES_DIR = "localized/textures"
LANGUAGE_ID_LENGTHS = (2, 3)
# Extensions the engine refuses to read as a language ID (`M_PAUSE.png`).
IMAGE_EXTENSIONS = frozenset({"png", "jpg", "gfx", "tga", "lmp"})
# Where a base graphic can live in our package. The engine looks the base up
# as a MiscPatch with TryAny, which reaches all of these namespaces.
LOCALIZED_BASE_DIRS = ("graphics", "textures", "patches", "flats", "sprites", "hires")


# --- Findings --------------------------------------------------------------

@dataclass(frozen=True)
class Finding:
    """One problem, always with the exact path it was found at."""

    category: str
    severity: str
    path: str      # path inside the PK3, or a doc path, or the PK3 itself
    message: str

    def render(self) -> str:
        tag = "ERROR" if self.severity == SEVERITY_ERROR else "warn "
        return f"  {tag}  {self.path}: {self.message}"

    def as_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class Report:
    pk3: str
    findings: list[Finding] = field(default_factory=list)
    # Per-category one-line summaries, shown when the category passes.
    notes: dict[str, list[str]] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)

    def add(self, category: str, severity: str, path: str, message: str) -> None:
        self.findings.append(Finding(category, severity, path, message))

    def error(self, category: str, path: str, message: str) -> None:
        self.add(category, SEVERITY_ERROR, path, message)

    def warn(self, category: str, path: str, message: str) -> None:
        self.add(category, SEVERITY_WARNING, path, message)

    def note(self, category: str, text: str) -> None:
        self.notes.setdefault(category, []).append(text)

    def skip(self, category: str, why: str) -> None:
        self.skipped[category] = why

    def of(self, category: str) -> list[Finding]:
        return [f for f in self.findings if f.category == category]

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == SEVERITY_WARNING]

    def ok(self, strict: bool = False) -> bool:
        return not self.errors and not (strict and self.warnings)


# --- Tiny WAD reader (deliberately NOT tools/sdbuild.wad) ------------------
# Validating the build's output with the build's own reader would only prove
# the writer and the reader agree. This parser is written from the Doom WAD
# spec instead, so a bug in sdbuild cannot hide here.

WAD_HEADER = struct.Struct("<4sii")
WAD_DIR_ENTRY = struct.Struct("<ii8s")


class WadFormatError(ValueError):
    pass


def read_wad_directory(blob: bytes) -> list[tuple[str, int, int]]:
    """[(name, offset, size), ...] in directory order; raise on malformation."""
    if len(blob) < WAD_HEADER.size:
        raise WadFormatError(f"only {len(blob)} bytes, too small for a WAD header")
    magic, numlumps, infotableofs = WAD_HEADER.unpack_from(blob, 0)
    if magic != b"PWAD":
        raise WadFormatError(f"magic is {magic!r}, expected b'PWAD' (a map WAD is never an IWAD)")
    if numlumps < 0:
        raise WadFormatError(f"negative lump count {numlumps}")
    end = infotableofs + numlumps * WAD_DIR_ENTRY.size
    if infotableofs < 0 or end > len(blob):
        raise WadFormatError(
            f"directory at {infotableofs} + {numlumps} entries runs past the end of the {len(blob)}-byte file"
        )
    entries: list[tuple[str, int, int]] = []
    for i in range(numlumps):
        filepos, size, raw = WAD_DIR_ENTRY.unpack_from(blob, infotableofs + i * WAD_DIR_ENTRY.size)
        try:
            name = raw.rstrip(b"\0").decode("ascii")
        except UnicodeDecodeError as exc:
            raise WadFormatError(f"lump {i} has a non-ASCII name {raw!r}") from exc
        if size < 0 or filepos < 0 or filepos + size > len(blob):
            raise WadFormatError(f"lump {name!r} data [{filepos}, {filepos + size}) is outside the file")
        entries.append((name, filepos, size))
    return entries


def wad_lump(blob: bytes, entries: list[tuple[str, int, int]], name: str) -> bytes | None:
    for lump_name, filepos, size in entries:
        if lump_name.upper() == name.upper():
            return blob[filepos:filepos + size]
    return None


# --- UDMF parsing ----------------------------------------------------------

class UdmfError(ValueError):
    pass


@dataclass
class UdmfBlock:
    kind: str
    index: int                      # index among blocks of the same kind
    fields: dict[str, str]          # raw values, strings already unquoted


@dataclass
class UdmfMap:
    namespace: str | None
    blocks: list[UdmfBlock]
    globals: dict[str, str]

    def of_kind(self, kind: str) -> list[UdmfBlock]:
        return [b for b in self.blocks if b.kind == kind]


def _strip_udmf_comments(text: str) -> str:
    """Remove // and /* */ comments without touching quoted strings."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise UdmfError("unterminated /* comment")
            out.append(" ")
            i = j + 2
            continue
        out.append(ch)
        i += 1
    if in_string:
        raise UdmfError("unterminated string literal")
    return "".join(out)


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def parse_udmf(text: str) -> UdmfMap:
    """Parse a TEXTMAP into blocks. Raises UdmfError on anything malformed."""
    body = _strip_udmf_comments(text)
    namespace: str | None = None
    globals_: dict[str, str] = {}
    blocks: list[UdmfBlock] = []
    counters: dict[str, int] = {}

    pos, n = 0, len(body)
    while pos < n:
        # Skip whitespace and stray semicolons between top-level items.
        while pos < n and (body[pos].isspace() or body[pos] == ";"):
            pos += 1
        if pos >= n:
            break
        match = re.compile(r"[A-Za-z_][A-Za-z0-9_]*").match(body, pos)
        if not match:
            raise UdmfError(f"unexpected character {body[pos]!r} at offset {pos}")
        identifier = match.group(0)
        pos = match.end()
        while pos < n and body[pos].isspace():
            pos += 1
        if pos >= n:
            raise UdmfError(f"{identifier!r} at offset {match.start()} is followed by nothing")
        if body[pos] == "=":
            end = body.find(";", pos)
            if end < 0:
                raise UdmfError(f"global assignment {identifier!r} has no terminating ';'")
            value = _unquote(body[pos + 1:end])
            if identifier.lower() == "namespace":
                namespace = value
            else:
                globals_[identifier.lower()] = value
            pos = end + 1
        elif body[pos] == "{":
            end = body.find("}", pos)
            if end < 0:
                raise UdmfError(f"block {identifier!r} is never closed")
            kind = identifier.lower()
            fields: dict[str, str] = {}
            for statement in body[pos + 1:end].split(";"):
                statement = statement.strip()
                if not statement:
                    continue
                if "=" not in statement:
                    raise UdmfError(f"block {kind!r}: statement {statement!r} is not key = value")
                key, _, value = statement.partition("=")
                fields[key.strip().lower()] = _unquote(value)
            index = counters.get(kind, 0)
            counters[kind] = index + 1
            blocks.append(UdmfBlock(kind, index, fields))
            pos = end + 1
        else:
            raise UdmfError(f"{identifier!r} is followed by {body[pos]!r}, expected '=' or '{{'")
    return UdmfMap(namespace, blocks, globals_)


# --- PNG reading (stdlib: struct + zlib) -----------------------------------

class PngError(ValueError):
    pass


@dataclass
class PngInfo:
    width: int
    height: int
    bit_depth: int
    colour_type: int
    interlace: int
    palette: list[tuple[int, int, int]]
    used_indices: set[int] | None        # None when not decoded (interlaced)
    # RGBA (colour type 6, 8 bits, not interlaced) only, else None: the alpha
    # values present and the RGB of every pixel whose alpha is not 0.
    alphas: set[int] | None = None
    opaque_colours: set[tuple[int, int, int]] | None = None

    @property
    def indexed(self) -> bool:
        return self.colour_type == PNG_COLOUR_TYPE_PALETTE

    def used_colours(self) -> list[tuple[int, int, int]]:
        if self.used_indices is None:
            return list(self.palette)
        out = []
        for i in sorted(self.used_indices):
            if i < len(self.palette):
                out.append(self.palette[i])
        return out


def _png_chunks(blob: bytes) -> Iterable[tuple[str, bytes]]:
    if not blob.startswith(PNG_MAGIC):
        raise PngError("missing PNG signature")
    pos = len(PNG_MAGIC)
    while pos < len(blob):
        if pos + 8 > len(blob):
            raise PngError(f"truncated chunk header at offset {pos}")
        (length,) = struct.unpack_from(">I", blob, pos)
        ctype = blob[pos + 4:pos + 8].decode("ascii", "replace")
        start = pos + 8
        if start + length + 4 > len(blob):
            raise PngError(f"chunk {ctype} at offset {pos} claims {length} bytes but the file ends")
        data = blob[start:start + length]
        (stored_crc,) = struct.unpack_from(">I", blob, start + length)
        if zlib.crc32(blob[pos + 4:start + length]) & 0xFFFFFFFF != stored_crc:
            raise PngError(f"chunk {ctype} at offset {pos} fails its CRC: the file is corrupt")
        yield ctype, data
        pos = start + length + 4
        if ctype == "IEND":
            return
    raise PngError("no IEND chunk: the file is truncated")


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def _unfilter(raw: bytes, width: int, height: int, bit_depth: int, channels: int = 1) -> bytes:
    """Reverse the PNG per-scanline filters (1 channel for palette, 4 for RGBA)."""
    stride = (width * channels * bit_depth + 7) // 8
    bpp = max(1, channels * bit_depth // 8)
    out = bytearray()
    previous = bytearray(stride)
    pos = 0
    for row in range(height):
        if pos + 1 + stride > len(raw):
            raise PngError(f"IDAT ends after {row} of {height} scanlines")
        ftype = raw[pos]
        line = bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ftype == 0:
            pass
        elif ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                upleft = previous[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + _paeth(left, previous[i], upleft)) & 0xFF
        else:
            raise PngError(f"scanline {row} uses unknown filter type {ftype}")
        out += line
        previous = line
    return bytes(out)


def _indices_from_scanlines(data: bytes, width: int, height: int, bit_depth: int) -> set[int]:
    if bit_depth == 8:
        return set(data)
    stride = (width * bit_depth + 7) // 8
    per_byte = 8 // bit_depth
    mask = (1 << bit_depth) - 1
    used: set[int] = set()
    for row in range(height):
        line = data[row * stride:(row + 1) * stride]
        for x in range(width):
            byte = line[x // per_byte]
            shift = 8 - bit_depth * (x % per_byte + 1)
            used.add((byte >> shift) & mask)
    return used


def read_png(blob: bytes) -> PngInfo:
    """Parse a PNG far enough to know its colour model and the colours used."""
    width = height = bit_depth = colour_type = interlace = -1
    palette: list[tuple[int, int, int]] = []
    idat = bytearray()
    seen_ihdr = False
    for ctype, data in _png_chunks(blob):
        if ctype == "IHDR":
            if len(data) != 13:
                raise PngError(f"IHDR is {len(data)} bytes, expected 13")
            width, height, bit_depth, colour_type, _comp, _filt, interlace = struct.unpack(">IIBBBBB", data)
            seen_ihdr = True
        elif ctype == "PLTE":
            if len(data) % 3:
                raise PngError(f"PLTE length {len(data)} is not a multiple of 3")
            palette = [tuple(data[i:i + 3]) for i in range(0, len(data), 3)]  # type: ignore[misc]
        elif ctype == "IDAT":
            idat += data
    if not seen_ihdr:
        raise PngError("no IHDR chunk")

    used: set[int] | None = None
    if colour_type == PNG_COLOUR_TYPE_PALETTE and interlace == 0:
        try:
            raw = zlib.decompress(bytes(idat))
        except zlib.error as exc:
            raise PngError(f"IDAT does not inflate: {exc}") from exc
        used = _indices_from_scanlines(_unfilter(raw, width, height, bit_depth), width, height, bit_depth)
    alphas: set[int] | None = None
    opaque: set[tuple[int, int, int]] | None = None
    if colour_type == PNG_COLOUR_TYPE_RGBA and bit_depth == 8 and interlace == 0:
        try:
            raw = zlib.decompress(bytes(idat))
        except zlib.error as exc:
            raise PngError(f"IDAT does not inflate: {exc}") from exc
        pixels = _unfilter(raw, width, height, bit_depth, PNG_RGBA_CHANNELS)
        alphas = set(pixels[3::PNG_RGBA_CHANNELS])
        opaque = {tuple(pixels[i:i + 3]) for i in range(0, len(pixels), PNG_RGBA_CHANNELS)  # type: ignore[misc]
                  if pixels[i + 3]}
    return PngInfo(width, height, bit_depth, colour_type, interlace, palette, used, alphas, opaque)


# --- Reading the documents that hold the contract --------------------------

def _spec_iwad_rows(spec: Path) -> list[tuple[str, str]]:
    """(NAME, type cell) for every table row of MOD-SPEC 5, subsections
    included (a `###` heading does not end a `##` section)."""
    if not spec.is_file():
        return []
    text = spec.read_text(encoding="utf-8")
    match = re.search(r"^##\s*5\..*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not match:
        return []
    rows: list[tuple[str, str]] = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = line.split("|")
        cell = RE_BACKTICKED.findall(cells[1].strip())
        if cell:
            kind = cells[2].strip().lower() if len(cells) > 2 else ""
            rows.append((cell[0].strip().upper(), kind))
    return rows


def iwad_assets_from_spec(spec: Path) -> set[str]:
    """Names declared in MOD-SPEC 5 'IWAD assets used' (first table column).

    An IWAD texture reference is legal only if it is written down there, so
    this parse is the whole point of the texture check: adding an IWAD name
    to a map without documenting it must fail.
    """
    return {name for name, _ in _spec_iwad_rows(spec)}


def iwad_sprites_from_spec(spec: Path) -> set[str]:
    """The MOD-SPEC 5 rows whose Type cell says `sprite` (section 5.1)."""
    return {name for name, kind in _spec_iwad_rows(spec) if SPEC_SPRITE_TYPE in kind}


def licensed_names(licenses: Path) -> set[str]:
    """Every backticked token in LICENSES.md, uppercased.

    Deliberately generous about *where* the name appears (any table row, any
    paragraph): the check is "this asset has a documented provenance", and
    the shape of the document belongs to the art-director, not to QA.
    """
    if not licenses.is_file():
        return set()
    text = licenses.read_text(encoding="utf-8")
    names: set[str] = set()
    for token in RE_BACKTICKED.findall(text):
        # Keep the token whole as well as split. Splitting on "/" is what makes
        # `SDCONC1, SDSTEL1` work, but it also shredded `fonts/defsmallfont/*.png`
        # into three meaningless pieces, so a directory could never be declared
        # and a 214-file font looked like 214 undocumented assets.
        whole = token.strip().strip("`")
        if whole:
            names.add(whole.upper())
        for piece in re.split(r"[,\s/]+", token):
            piece = piece.strip().strip("`")
            if not piece:
                continue
            names.add(piece.upper())
            names.add(Path(piece).stem.upper())
    return names


# Lumps approved in palette v2 (docs/art/ART-BIBLE.md section 3). Every other
# indexed lump must stay inside v1; these may use the v2 ramps too. Sprites
# are RGBA and are not palette-checked here (tests/test_palette_v2.py is).
# D66: the Tankograd brick (marble_red), the two banners hung on it (Soviet
# flags since D119, v2 only through the brick) and the four portal frames
# (mosaic_cobalt).
# D80: the blue pass's status bar icon STKEYS0 (graphics/, mosaic_cobalt).
# M2e-i (D89, D90, D92): none. Status bar A's four indexed pictures (STBAR,
# STARMS, SDSBRU, SDARRU) use v1 colours only; the 42 v2 faces STF* are RGBA
# (tests/test_palette_v2.py lists them in APPROVED_IN_V2).
PALETTE_V2_LUMPS = frozenset({"SDMOSA1"}  # D56
                             | {"SDBRCK1", "SDBRCK2", "SDFLAG1", "SDFLAG2"}
                             | {f"SDPORT{i}" for i in range(1, 5)}
                             | {"STKEYS0"}
                             # D107: Episode 2's bricks in marble_red, as SDBRCK1
                             # (D66): the roundhouse, the Kremlin wall, the banner
                             # hung on it and the Spasskaya stone.
                             | {"SDBRCK3", "SDKREM1", "SDBANR1", "SDSPAS1"}
                             # D113: Episode 3's portal rim (mosaic_cobalt);
                             # Episode 2 round 2's blue key door (mosaic_cobalt),
                             # the Spasskaya clock and the Historical Museum
                             # (marble_red) and the two banners on SDKREM1
                             # (marble_red; Soviet flags since D119).
                             | {"SDPRTE1", "SDDOORB", "SDCLOK1", "SDMUSE1", "SDFLAG3", "SDFLAG4"}
                             # D113: MAP09's sky, the portal's glow in mosaic_cobalt
                             # (only where the portal lights it; gen_episode3_skies).
                             | {"SDSKY5"}
                             # D126: the Gemini title screen (palette v2).
                             | {"TITLEPIC"}
                             # D122: V3's operations map background (mosaic_gold,
                             # marble_red, mosaic_cobalt; gen_ops_map.py). Its
                             # arrows, markers and the five awards are RGBA.
                             | {"SDOPMAP"})
# The masked lumps (RGBA, so not in PALETTE_V2_LUMPS, which is indexed lumps
# only) approved in v2: D107's merlon SDKREM2 is SDKREM1's brick cut out.
PALETTE_V2_MASKED = frozenset({"SDKREM2"})


def palette_v2_colours(palette_json: Path) -> set[tuple[int, int, int]] | None:
    """Palette v2 (`colours_v2`) as an RGB set, or None if absent."""
    try:
        data = json.loads(palette_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    colours = {tuple(int(c) for c in rgb) for rgb in data.get("colours_v2", [])
               if isinstance(rgb, (list, tuple)) and len(rgb) == 3}
    return colours or None  # type: ignore[return-value]


def palette_colours(palette_json: Path) -> set[tuple[int, int, int]] | None:
    """The approved palette as an RGB set, or None if the file is unusable."""
    if not palette_json.is_file():
        return None
    try:
        data = json.loads(palette_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    colours: set[tuple[int, int, int]] = set()
    for rgb in data.get("colours", []):
        if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
            colours.add(tuple(int(c) for c in rgb))  # type: ignore[arg-type]
    for ramp in data.get("ramps", []):
        for rgb in ramp.get("colours", []):
            colours.add(tuple(int(c) for c in rgb))
    for extra in data.get("extras", []):
        rgb = extra.get("rgb")
        if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
            colours.add(tuple(int(c) for c in rgb))
    return colours or None


# --- The package under test ------------------------------------------------

@dataclass
class Package:
    path: Path
    zf: zipfile.ZipFile
    names: list[str]                              # paths inside the zip

    def lower_map(self) -> dict[str, str]:
        return {n.lower(): n for n in self.names}

    def read(self, name: str) -> bytes:
        return self.zf.read(name)

    def find(self, path: str) -> str | None:
        """Resolve a PK3 path case-insensitively (GZDoom is case-blind)."""
        return self.lower_map().get(path.lower())

    def files_under(self, folder: str) -> list[str]:
        prefix = folder.lower() + "/"
        return [n for n in self.names if n.lower().startswith(prefix) and not n.endswith("/")]


# --- Individual checks -----------------------------------------------------

def check_package(pkg: Package, report: Report) -> None:
    bad = pkg.zf.testzip()
    if bad is not None:
        report.error("package", bad, "member fails its CRC: the zip is corrupt")
    files = [n for n in pkg.names if not n.endswith("/")]
    report.stats["entries"] = len(files)
    report.stats["uncompressed_bytes"] = sum(i.file_size for i in pkg.zf.infolist())
    for required in REQUIRED_ROOT_LUMPS:
        if pkg.find(required) is None:
            report.error("package", required, "required by MOD-SPEC 2 but not in the PK3")
    maps = [n for n in pkg.files_under(MAPS_DIR) if n.lower().endswith(".wad")]
    if not maps:
        report.error("package", f"{MAPS_DIR}/", "no maps/*.wad in the PK3")
    report.note("package", f"{len(files)} files, {report.stats['uncompressed_bytes']} bytes uncompressed")
    report.note("package", f"{len(maps)} map WAD(s), "
                           f"{len(REQUIRED_ROOT_LUMPS)}/{len(REQUIRED_ROOT_LUMPS)} required root lumps present"
                if all(pkg.find(r) for r in REQUIRED_ROOT_LUMPS) else f"{len(maps)} map WAD(s)")


def lump_name_problem(stem: str) -> str | None:
    """Why `stem` cannot be a WAD lump name, or None if it is fine.

    Case is not a problem: GZDoom upper-cases lump names taken from PK3
    entries, which is why MOD-SPEC 2 itself ships `zscript.txt`.
    """
    if not stem:
        return "empty lump name"
    if len(stem) > MAX_LUMP_NAME:
        return f"lump name {stem.upper()!r} is {len(stem)} characters, the WAD limit is {MAX_LUMP_NAME}"
    try:
        stem.encode("ascii")
    except UnicodeEncodeError:
        return f"lump name {stem!r} is not ASCII"
    for ch in stem.upper():
        if not (ch.isalnum() or ch in LUMP_NAME_EXTRA_CHARS):
            return f"lump name {stem.upper()!r} contains {ch!r}, which is not legal in a WAD directory"
    return None


def check_root_lumps(pkg: Package, report: Report) -> None:
    roots = [n for n in pkg.names if "/" not in n and not n.endswith("/")]
    report.stats["root_lumps"] = len(roots)
    for name in sorted(roots):
        stem = Path(name).stem
        problem = lump_name_problem(stem)
        if problem:
            report.error("lumps", name, problem)
        if len(Path(name).suffixes) > 1:
            report.warn("lumps", name,
                        f"more than one extension: GZDoom would name the lump {stem.upper()!r}")
    seen: dict[str, str] = {}
    for name in sorted(roots):
        key = Path(name).stem.upper()
        if key in seen:
            report.error("lumps", name, f"collides with {seen[key]}: both become lump {key!r}")
        seen[key] = name
    report.note("lumps", f"{len(roots)} root entries -> {len(seen)} lump names, all <= {MAX_LUMP_NAME} chars"
                if not report.of("lumps") else f"{len(roots)} root entries")


@dataclass
class MapInfo:
    pk3_path: str
    lump_name: str
    udmf: UdmfMap | None


def check_maps(pkg: Package, report: Report) -> list[MapInfo]:
    maps: list[MapInfo] = []
    wads = sorted(n for n in pkg.files_under(MAPS_DIR) if n.lower().endswith(".wad"))
    for name in sorted(pkg.files_under(MAPS_DIR)):
        if not name.lower().endswith(".wad"):
            report.error("maps", name, "maps/ may only contain .wad files (MOD-SPEC 2)")
    for name in wads:
        expected = Path(name).stem.upper()
        problem = lump_name_problem(Path(name).stem)
        if problem:
            report.error("maps", name, problem)
        blob = pkg.read(name)
        try:
            entries = read_wad_directory(blob)
        except WadFormatError as exc:
            report.error("maps", name, f"not a valid PWAD: {exc}")
            maps.append(MapInfo(name, expected, None))
            continue
        order = [e[0].upper() for e in entries]
        wanted = [expected, MAP_TEXT_LUMP, MAP_END_LUMP]
        if order != wanted:
            report.error("maps", name,
                         f"lump order is {order}, MOD-SPEC 2 requires exactly {wanted}")
        for lump_name, _pos, size in entries:
            if lump_name.upper() in (expected, MAP_END_LUMP) and size != 0:
                report.error("maps", f"{name}:{lump_name}",
                             f"marker lump must be empty, it is {size} bytes")
        textmap = wad_lump(blob, entries, MAP_TEXT_LUMP)
        if textmap is None:
            report.error("maps", name, f"no {MAP_TEXT_LUMP} lump: the map has no geometry")
            maps.append(MapInfo(name, expected, None))
            continue
        try:
            text = textmap.decode("ascii")
        except UnicodeDecodeError as exc:
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}", f"is not ASCII: {exc}")
            maps.append(MapInfo(name, expected, None))
            continue
        try:
            udmf = parse_udmf(text)
        except UdmfError as exc:
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}", f"does not parse as UDMF: {exc}")
            maps.append(MapInfo(name, expected, None))
            continue
        if udmf.namespace is None:
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}", "no `namespace` declaration (UDMF requires it first)")
        if not udmf.of_kind("sector"):
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}", "no sector blocks: nothing to stand on")
        if not udmf.of_kind("vertex"):
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}", "no vertex blocks")
        if not any(b.fields.get("type") == "1" for b in udmf.of_kind("thing")):
            report.error("maps", f"{name}:{MAP_TEXT_LUMP}",
                         "no thing of type 1 (Player 1 start): the map cannot be entered")
        maps.append(MapInfo(name, expected, udmf))
        report.note("maps", f"{name}: {expected}/{MAP_TEXT_LUMP}/{MAP_END_LUMP}, "
                            f"{len(udmf.of_kind('vertex'))} vertices, {len(udmf.of_kind('linedef'))} linedefs, "
                            f"{len(udmf.of_kind('sector'))} sectors, {len(udmf.of_kind('thing'))} things")
    report.stats["maps"] = len(wads)
    check_mapinfo_maps(pkg, {Path(n).stem.upper() for n in wads}, report)
    return maps


def mapinfo_map_references(text: str) -> tuple[list[tuple[str, str]], set[str]]:
    """([(what, NAME)], {names with a `map` block}) from a MAPINFO text.

    `what` is "map", "episode", "next" or "secretnext". End sequences are
    left out: a `next` spelt End... that is not itself a map block."""
    code = RE_MAPINFO_COMMENT.sub("", text)
    blocks = [(kind.lower(), name.upper()) for kind, name in RE_MAPINFO_BLOCK_MAP.findall(code)]
    defined = {name for kind, name in blocks if kind == "map"}
    refs = list(blocks)
    for key, name in RE_MAPINFO_NEXT_MAP.findall(code):
        if name.upper() not in defined and name.lower().startswith(MAPINFO_END_PREFIX):
            continue
        refs.append((key.lower(), name.upper()))
    return refs, defined


def check_mapinfo_maps(pkg: Package, packed: set[str], report: Report) -> None:
    """Every map MAPINFO names is packed, and every packed map has its block.

    A `map`, `episode` or `next` naming a map with no maps/<NAME>.wad is a
    level the engine cannot load (an episode that starts nowhere, an exit
    into nothing); a packed map without a `map` block loads with no title,
    no cluster and the engine's default `next`. D62 renamed three maps at
    once, which is how either would happen."""
    mapinfo_path = pkg.find("MAPINFO")
    if not mapinfo_path:
        return
    refs, defined = mapinfo_map_references(pkg.read(mapinfo_path).decode("ascii", "replace"))
    for what, name in refs:
        if name not in packed:
            report.error("maps", f"{mapinfo_path}:{what} {name}",
                         f"MAPINFO names map {name!r}, but there is no {MAPS_DIR}/{name}.wad in the PK3")
    for name in sorted(packed - defined):
        report.warn("maps", f"{MAPS_DIR}/{name}.wad",
                    "no `map` block in MAPINFO: no title, no cluster, the engine's default `next`")
    missing = sum(1 for _what, name in refs if name not in packed)
    report.note("maps", f"MAPINFO: {len(defined)} map block(s), {len(refs)} map reference(s), "
                        f"{len(refs) - missing} packed")


def own_texture_names(pkg: Package) -> dict[str, str]:
    """{LUMPNAME: pk3 path} for every texture-ish asset packed in the PK3."""
    found: dict[str, str] = {}
    for folder in TEXTURE_DIRS:
        for path in pkg.files_under(folder):
            found.setdefault(Path(path).stem.upper(), path)
    # A TEXTURES lump can define composite names that have no file of their own.
    textures_lump = pkg.find("TEXTURES") or pkg.find("textures.txt")
    if textures_lump:
        try:
            text = pkg.read(textures_lump).decode("ascii", "replace")
        except KeyError:
            text = ""
        for name in RE_TEXTURES_DEF.findall(text):
            found.setdefault(name.upper(), textures_lump)
    return found


def animdefs_switch_textures(text: str) -> list[tuple[str, int, str]]:
    """Every texture name the `switch` definitions of an ANIMDEFS text use.

    Returns (NAME, line, role) with role "off" (the name after `switch`),
    "on" (each `pic` of the `on` sequence) or "off-pic" (each `pic` of an
    optional `off` sequence). Token-based like the engine's scanner, so a
    definition may span lines; comments are blanked with their newlines kept
    so the line numbers stay true. Non-switch definitions are skipped.
    """
    tokens = _animdefs_tokens(text)
    found: list[tuple[str, int, str]] = []
    i = 0
    while i < len(tokens):
        if tokens[i][0].lower() != "switch":
            i += 1
            continue
        i += 1
        if i < len(tokens) and tokens[i][0].lower() in ANIMDEFS_GAMES:
            game = tokens[i][0].lower()
            i += 1
            if game == "doom" and i < len(tokens) and tokens[i][0].isdigit():
                i += 1                                   # the Doom tier: 1, 2 or 3
        if i < len(tokens) and tokens[i][0].lower() == "quest":
            i += 1
        if i >= len(tokens):
            break
        found.append((tokens[i][0].upper(), tokens[i][1], "off"))
        i += 1
        role = "on"
        while i < len(tokens) and tokens[i][0].lower() not in ANIMDEFS_TOP_LEVEL:
            word = tokens[i][0].lower()
            if word in ("on", "off"):
                role = "on" if word == "on" else "off-pic"
            elif word == "sound":
                i += 1                                   # skip the sound name
            elif word == "pic" and i + 1 < len(tokens):
                i += 1
                found.append((tokens[i][0].upper(), tokens[i][1], role))
            i += 1
    return found


def _animdefs_tokens(text: str) -> list[tuple[str, int]]:
    """(token, line) of an ANIMDEFS text, comments blanked with their newlines kept."""
    def blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    clean = RE_ANIMDEFS_COMMENT.sub(blank, text)
    return [(m.group(0).strip('"'), clean.count("\n", 0, m.start()) + 1)
            for m in RE_ANIMDEFS_TOKEN.finditer(clean)]


def animdefs_anim_textures(text: str) -> list[tuple[str, int, str]]:
    """Every picture name the `flat` and `texture` animations of an ANIMDEFS use.

    Syntax from the engine's parser, FTextureAnimator::ParseAnim in
    src/gamedata/textures/animations.cpp (GZDoom tag g4.14.2, read
    2026-10-14): `flat|texture [optional] NAME` then either `pic FRAME tics N`
    repeated or one `range LAST tics N`; `rand A B` may replace `tics N`, and
    `oscillate`, `random`, `allowdecals`, `notrim` may appear. A FRAME that
    is a bare number is an offset from NAME, not a name, so it is skipped.
    Returns (NAME, line, role) with role "flat" or "texture"; switches and
    the other definitions are skipped.
    """
    tokens = _animdefs_tokens(text)
    found: list[tuple[str, int, str]] = []
    i = 0
    while i < len(tokens):
        kind = tokens[i][0].lower()
        if kind not in ("flat", "texture"):
            i += 1
            continue
        i += 1
        if i < len(tokens) and tokens[i][0].lower() == "optional":
            i += 1
        if i >= len(tokens):
            break
        found.append((tokens[i][0].upper(), tokens[i][1], kind))
        i += 1
        while i < len(tokens) and tokens[i][0].lower() not in ANIMDEFS_TOP_LEVEL:
            if tokens[i][0].lower() in ("pic", "range") and i + 1 < len(tokens):
                i += 1
                if not tokens[i][0].isdigit():
                    found.append((tokens[i][0].upper(), tokens[i][1], kind))
            i += 1
    return found


def check_textures(pkg: Package, maps: list[MapInfo], iwad_names: set[str], report: Report) -> None:
    own = own_texture_names(pkg)
    referenced: dict[str, list[str]] = {}        # NAME -> where it is used
    used_by_maps: set[str] = set()

    def reference(name: str, where: str, by_map: bool = True) -> None:
        clean = name.strip()
        if clean.upper() in BUILTIN_TEXTURE_NAMES or clean == NO_TEXTURE:
            return
        referenced.setdefault(clean.upper(), []).append(where)
        if by_map:
            used_by_maps.add(clean.upper())

    for info in maps:
        if info.udmf is None:
            continue
        for block in info.udmf.of_kind("sidedef"):
            for key in WALL_TEXTURE_KEYS:
                if key in block.fields:
                    reference(block.fields[key], f"{info.pk3_path}:sidedef[{block.index}].{key}")
        for block in info.udmf.of_kind("sector"):
            for key in FLAT_TEXTURE_KEYS:
                if key in block.fields:
                    reference(block.fields[key], f"{info.pk3_path}:sector[{block.index}].{key}")

    mapinfo_path = pkg.find("MAPINFO")
    if mapinfo_path:
        text = pkg.read(mapinfo_path).decode("ascii", "replace")
        for sky in RE_MAPINFO_SKY.findall(text):
            reference(sky, f"{mapinfo_path}:sky")

    switch_names = anim_names = 0
    for lump in ANIMDEFS_LUMPS:
        animdefs_path = pkg.find(lump)
        if not animdefs_path:
            continue
        text = pkg.read(animdefs_path).decode("ascii", "replace")
        for name, line, role in animdefs_switch_textures(text):
            switch_names += 1
            reference(name, f"{animdefs_path}:{line}:switch {role}", by_map=False)
        for name, line, role in animdefs_anim_textures(text):
            anim_names += 1
            reference(name, f"{animdefs_path}:{line}:{role} frame", by_map=False)
    report.stats["switch_textures"] = switch_names
    report.stats["anim_textures"] = anim_names

    from_pk3 = from_iwad = 0
    for name in sorted(referenced):
        if name in own:
            from_pk3 += 1
        elif name in iwad_names:
            from_iwad += 1
        else:
            for where in referenced[name]:
                report.error(
                    "textures", where,
                    f"texture {name!r} is in neither the PK3 nor MOD-SPEC 5 "
                    f"(the engine would say: Unknown texture {name})",
                )
    report.stats["textures_referenced"] = len(referenced)
    report.stats["textures_from_pk3"] = from_pk3
    report.stats["textures_from_iwad"] = from_iwad
    report.note("textures",
                f"{len(referenced)} distinct names referenced: {from_pk3} from the PK3, "
                f"{from_iwad} declared IWAD assets (MOD-SPEC 5), "
                f"{len(referenced) - from_pk3 - from_iwad} unresolved")
    if switch_names:
        report.note("textures", f"{switch_names} switch texture name(s) in ANIMDEFS checked the same way")
    if anim_names:
        report.note("textures", f"{anim_names} animation frame name(s) in ANIMDEFS checked the same way")
    unused = sorted(set(own) - used_by_maps)
    if unused:
        report.note("textures", f"packed but unused by any map: {', '.join(unused)}")


def _check_masked(path: str, png: PngInfo, palette: set[tuple[int, int, int]] | None, report: Report) -> None:
    """A MASKED_TEXTURES lump: 8-bit RGBA, hard alpha, opaque pixels in the palette."""
    if png.colour_type != PNG_COLOUR_TYPE_RGBA or png.bit_depth != 8:
        report.error("images", path,
                     f"PNG colour type {png.colour_type} at {png.bit_depth} bits: a masked texture "
                     f"must be colour type {PNG_COLOUR_TYPE_RGBA} (RGBA) at 8 bits")
        return
    if png.alphas is None:                       # interlaced: not decoded
        report.warn("images", path, "interlaced RGBA PNG: alpha and colours not checked")
        return
    soft = sorted(png.alphas - MASKED_ALPHA)
    if soft:
        report.error("images", path,
                     f"masked texture with partial alpha {soft[:6]}: alpha must be hard 0/255")
    if palette is not None and Path(path).stem.upper() in PALETTE_V2_MASKED:
        palette = palette_v2_colours(DEFAULT_PALETTE) or palette
    if palette is not None:
        offending = sorted(c for c in png.opaque_colours or set() if c not in palette)
        if offending:
            shown = ", ".join(f"#{r:02X}{g:02X}{b:02X}" for r, g, b in offending[:8])
            more = f" (+{len(offending) - 8} more)" if len(offending) > 8 else ""
            report.error("images", path,
                         f"{len(offending)} opaque colour(s) outside docs/art/palette.json: {shown}{more}")


def check_images(pkg: Package, palette: set[tuple[int, int, int]] | None, report: Report) -> None:
    images = sorted(pkg.files_under("textures") + pkg.files_under("flats"))
    pngs = [p for p in images if p.lower().endswith(".png")]
    for path in images:
        if not path.lower().endswith(".png"):
            report.warn("images", path, "not a PNG: the project's texture format is indexed PNG")
    if palette is None:
        report.skip("images", f"{DEFAULT_PALETTE.name} unreadable: colours not checked")
    checked = 0
    for path in pngs:
        is_flat = path.lower().startswith("flats/")
        try:
            png = read_png(pkg.read(path))
        except PngError as exc:
            report.error("images", path, f"unreadable PNG: {exc}")
            continue
        checked += 1
        masked = not is_flat and Path(path).stem.upper() in MASKED_TEXTURES
        if masked:
            _check_masked(path, png, palette, report)
        elif not png.indexed:
            report.error("images", path,
                         f"PNG colour type {png.colour_type}, must be {PNG_COLOUR_TYPE_PALETTE} "
                         "(indexed / mode P) so the palette discipline is enforceable"
                         + (f"; only the masked textures ({', '.join(sorted(MASKED_TEXTURES))}) "
                            "may be RGBA" if png.colour_type == PNG_COLOUR_TYPE_RGBA else ""))
        if png.interlace:
            report.warn("images", path, "interlaced PNG: colours checked against the whole PLTE, not the used pixels")
        if png.width % DIMENSION_MULTIPLE or png.height % DIMENSION_MULTIPLE:
            report.error("images", path,
                         f"{png.width}x{png.height}: both sides must be multiples of {DIMENSION_MULTIPLE}")
        if is_flat:
            if (png.width, png.height) != FLAT_SIZE:
                report.error("images", path,
                             f"{png.width}x{png.height}: a flat must be {FLAT_SIZE[0]}x{FLAT_SIZE[1]}")
        elif Path(path).stem.upper() in SKY_TEXTURES:
            if (png.width, png.height) not in SKY_SIZES:
                report.warn("images", path,
                            f"{png.width}x{png.height} is not one of the agreed sky sizes "
                            + " / ".join(f"{w}x{h}" for w, h in SKY_SIZES))
        elif (png.width, png.height) not in ALLOWED_WALL_SIZES:
            report.warn("images", path,
                        f"{png.width}x{png.height} is not one of the agreed wall sizes "
                        + " / ".join(f"{w}x{h}" for w, h in ALLOWED_WALL_SIZES))
        if palette is not None and png.indexed:
            allowed = palette
            if Path(path).stem.upper() in PALETTE_V2_LUMPS:
                allowed = palette_v2_colours(DEFAULT_PALETTE) or palette
            offending = sorted({c for c in png.used_colours() if c not in allowed})
            if offending:
                shown = ", ".join(f"#{r:02X}{g:02X}{b:02X}" for r, g, b in offending[:8])
                more = f" (+{len(offending) - 8} more)" if len(offending) > 8 else ""
                report.error("images", path,
                             f"{len(offending)} colour(s) outside docs/art/palette.json: {shown}{more}")
    report.stats["images_checked"] = checked
    report.note("images", f"{checked} PNG(s) under textures/ and flats/"
                + (f", colours checked against {len(palette)} palette entries" if palette else ""))


def check_sprites(pkg: Package, report: Report) -> None:
    """Sprite lumps are NAMEFR[FR]; every declared rotation set is complete.

    What ships today (assets/sprites/, 2026-10-14) exercises every rule:
    the six weapon pickups of D48, rotation 0 only; the Reich rifleman
    (SDRR, 70), the Legion trooper (SDLT, 70) and the Stormtrooper (SDHS,
    77), eight rotations drawn one by one for the frames seen from every
    side and rotation 0 for the death and gib frames, plus the
    Stormtrooper's bolt (SDBL, 5, rotation 0); and the Reich hound (SDHN,
    46), whose rotations 2-4 are mirrored pairs (`SDHNA2A8`: one image
    serves rotation 2 and, flipped, 8), so a frame is five lumps
    (D54-D56). An empty sprites/ is still a pass.
    """
    files = sorted(pkg.files_under("sprites"))
    report.stats["sprites"] = len(files)
    # (sprite name, frame letter) -> set of rotation characters
    frames: dict[tuple[str, str], set[str]] = {}
    for path in files:
        stem = Path(path).stem.upper()
        problem = lump_name_problem(Path(path).stem)
        if problem:
            report.error("sprites", path, problem)
            continue
        if len(stem) not in (6, 8):
            report.error("sprites", path,
                         f"sprite lump {stem!r} is {len(stem)} characters; must be 6 (NAMEFR) or 8 (NAMEFRFR)")
            continue
        name = stem[:SPRITE_NAME_LEN]
        if not name.isalnum():
            report.error("sprites", path, f"sprite name {name!r} must be 4 alphanumeric characters")
            continue
        pairs = [(stem[4], stem[5])] + ([(stem[6], stem[7])] if len(stem) == 8 else [])
        for frame, rotation in pairs:
            if frame not in SPRITE_FRAME_CHARS:
                report.error("sprites", path, f"frame character {frame!r} is not in A-Z[\\]")
                continue
            if rotation != SPRITE_ROTATION_ALL and rotation not in SPRITE_ROTATIONS_16:
                report.error("sprites", path,
                             f"rotation {rotation!r} is not 0 (all angles) or 1-9/A-G")
                continue
            frames.setdefault((name, frame), set()).add(rotation)
    for (name, frame), rotations in sorted(frames.items()):
        if SPRITE_ROTATION_ALL in rotations and rotations != {SPRITE_ROTATION_ALL}:
            report.error("sprites", f"sprites/{name}{frame}*",
                         f"frame {frame} mixes rotation 0 (all angles) with {sorted(rotations - {'0'})}")
            continue
        if rotations == {SPRITE_ROTATION_ALL}:
            continue
        wanted = set(SPRITE_ROTATIONS_16 if rotations & set("9ABCDEFG") else SPRITE_ROTATIONS_8)
        missing = sorted(wanted - rotations)
        if missing:
            report.error("sprites", f"sprites/{name}{frame}*",
                         f"incomplete rotation set, missing {''.join(missing)} "
                         f"(the engine would say: Missing sprite)")
    report.stats["sprite_frames"] = len(frames)
    report.note("sprites", f"{len(files)} sprite lump(s), {len(frames)} frame(s)"
                + (" - nothing to check yet" if not files else ""))


def zscript_state_sprites(text: str) -> list[tuple[str, int]]:
    """Every sprite name a ZScript `States` block uses, as (NAME, line).

    A state line is `SPRITE FRAMES DURATION ...`, optionally after one or
    more `Label:` prefixes. Comments go first (they quote engine lines), and
    the four-letter flow keywords (`Goto`, `Loop`...) are not sprites.
    """
    code = _strip_udmf_comments(text)
    found: list[tuple[str, int]] = []
    for opening in RE_STATES_OPEN.finditer(code):
        depth, end = 1, opening.end()
        while end < len(code) and depth:
            if code[end] == "{":
                depth += 1
            elif code[end] == "}":
                depth -= 1
            end += 1
        first_line = code.count("\n", 0, opening.end()) + 1
        for offset, line in enumerate(code[opening.end():end - 1].split("\n")):
            label = RE_STATE_LABEL.match(line)
            while label:
                line = line[label.end():]
                label = RE_STATE_LABEL.match(line)
            frame = RE_STATE_FRAME.match(line)
            if not frame:
                continue
            name = frame.group(1).upper()
            if name in STATE_KEYWORDS:
                continue
            found.append((name, first_line + offset))
    return found


def check_state_sprites(pkg: Package, iwad_sprites: set[str], report: Report) -> None:
    """Every sprite a States block names resolves: packed, engine, or declared IWAD.

    The runtime twin of this is the engine's "Missing sprite"; the static
    rule is MOD-SPEC 5's texture rule applied to sprites, so that a Freedoom
    placeholder sprite is used only if it is written down.
    """
    packed = {Path(p).stem.upper()[:SPRITE_NAME_LEN] for p in pkg.files_under("sprites")}
    named: dict[str, list[str]] = {}
    for path in sorted(pkg.files_under("zscript")):
        if not path.lower().endswith(".zs"):
            continue
        try:
            refs = zscript_state_sprites(pkg.read(path).decode("utf-8", "replace"))
        except UdmfError as exc:          # the comment stripper's error type
            report.error("sprites", path, f"cannot be read: {exc}")
            continue
        for name, line in refs:
            named.setdefault(name, []).append(f"{path}:{line}")
    from_iwad = 0
    for name, where in sorted(named.items()):
        if name in ENGINE_SPRITES or name in packed:
            continue
        if name in iwad_sprites:
            from_iwad += 1
            continue
        report.error("sprites", where[0],
                     f"sprite {name!r} is named by {len(where)} state line(s) but is neither "
                     f"packed under sprites/ nor declared as an IWAD sprite in MOD-SPEC 5")
    report.stats["state_sprites"] = len(named)
    report.stats["state_sprites_iwad"] = from_iwad
    report.note("sprites", f"{len(named)} sprite name(s) used by ZScript states, "
                           f"{from_iwad} of them declared IWAD placeholders (MOD-SPEC 5)")


def check_licences(pkg: Package, declared: set[str], report: Report) -> None:
    packed: list[str] = []
    for folder in LICENSED_DIRS:
        packed += pkg.files_under(folder)
    # A licence row may declare a DIRECTORY as well as a lump. One font is one
    # asset in 214 files; demanding a row per glyph would be bookkeeping, not
    # provenance. A declared token containing "/" covers everything beneath it,
    # with a trailing glob stripped, so `fonts/defsmallfont/*.png` in
    # LICENSES.md covers that folder and nothing else.
    prefixes = []
    for token in declared:
        if "/" not in token:
            continue
        head, _, tail = token.rpartition("/")
        # `fonts/defsmallfont/*.png` -> the folder; `assets/textures/set/` -> itself
        base = head if ("*" in tail or not tail) else token
        if base:
            prefixes.append(base.upper().rstrip("/") + "/")
    prefixes = tuple(prefixes)
    missing = 0
    for path in sorted(packed):
        stem = Path(path).stem.upper()
        if (stem in declared or Path(path).name.upper() in declared
                or path.upper().startswith(prefixes)):
            continue
        if True:
            missing += 1
            report.error("licences", path,
                         f"no row for {stem!r} in {DEFAULT_LICENSES.relative_to(PROJECT_ROOT)}: "
                         "a packed asset without recorded provenance cannot ship")
    report.stats["assets_packed"] = len(packed)
    report.stats["assets_unlicensed"] = missing
    report.note("licences", f"{len(packed)} packed asset(s), {len(packed) - missing} with a documented origin")


def check_zscript(pkg: Package, report: Report) -> None:
    entry = pkg.find(ZSCRIPT_ENTRY)
    if entry is None:
        report.skip("zscript", f"no {ZSCRIPT_ENTRY} (already reported by `package`)")
        return
    seen: set[str] = set()
    queue = [entry]
    count = 0
    while queue:
        current = queue.pop(0)
        if current.lower() in seen:
            continue
        seen.add(current.lower())
        text = pkg.read(current).decode("utf-8", "replace")
        for include in RE_INCLUDE.findall(text):
            count += 1
            target = pkg.find(include)
            if target is None:
                report.error("zscript", f"{current} -> {include}",
                             "#include points at a file that is not in the PK3")
                continue
            queue.append(target)
    report.stats["zscript_files"] = len(seen)
    report.stats["zscript_includes"] = count
    # Files under zscript/ that nothing includes are dead weight at best and a
    # forgotten wiring at worst (the engine simply never compiles them).
    orphans = [p for p in sorted(pkg.files_under("zscript")) if p.lower() not in seen]
    for path in orphans:
        report.warn("zscript", path,
                    "packed but reachable from no #include: the engine never compiles it")
    report.note("zscript", f"{count} #include(s), {len(seen)} file(s) reachable from {ZSCRIPT_ENTRY}")


def menudef_fonts(text: str) -> list[tuple[str, int]]:
    """Every `Font "X"` directive in a MENUDEF, as (name, line), comments out.

    Comments go first because MENUDEF quotes engine lines in them."""
    code = _strip_udmf_comments(text)
    return [(m.group(1), code.count("\n", 0, m.start()) + 1)
            for m in RE_MENUDEF_FONT.finditer(code)]


def check_menus(pkg: Package, report: Report) -> None:
    lumps = [n for n in pkg.names
             if "/" not in n and Path(n).stem.upper() == MENUDEF_LUMP]
    if not lumps:
        report.skip("menus", "no MENUDEF in the PK3")
        return
    named = packed = 0
    for lump in sorted(lumps):
        try:
            fonts = menudef_fonts(pkg.read(lump).decode("utf-8", "replace"))
        except UdmfError as exc:          # the stripper's own error type
            report.error("menus", lump, f"cannot be read: {exc}")
            continue
        for name, line in fonts:
            named += 1
            if name.upper() in ENGINE_FONTS:
                continue
            glyphs = [f for f in pkg.files_under(f"{FONTS_DIR}/{name}")
                      if f.lower().endswith(".png")]
            if glyphs:
                packed += 1
                continue
            report.error(
                "menus", f"{lump}:{line}",
                f"font {name!r} is neither an engine font nor a {FONTS_DIR}/{name.lower()}/ "
                "folder in the PK3: the menu that names it cannot be drawn in it")
    report.stats["menu_fonts_named"] = named
    report.stats["menu_fonts_packed"] = packed
    report.note("menus", f"{named} Font directive(s) in MENUDEF, {packed} resolved to a packed "
                         f"folder font, the rest engine fonts")


# --- Orchestration ---------------------------------------------------------

def localized_name_parts(filename: str) -> tuple[str, list[str]] | str:
    """(BASE, [language IDs]) for a variant's file name, or why the engine
    would ignore it. Mirrors AddLocalizedVariants token by token."""
    tokens = [t for t in filename.split(".") if t]
    if len(tokens) < 2 or (len(tokens) == 2 and tokens[1].lower() in IMAGE_EXTENSIONS):
        return ("contains no language ID: GZDoom ignores it "
                "(name it <BASE>.<lang>.<ext>, e.g. M_PAUSE.ru.png)")
    langs = [t for t in tokens[1].lower().split("-") if t]
    bad = [lang for lang in langs if len(lang) not in LANGUAGE_ID_LENGTHS]
    if bad or not langs:
        return (f"invalid language ID {', '.join(repr(b) for b in bad) or repr(tokens[1])}: "
                f"GZDoom takes {' or '.join(map(str, LANGUAGE_ID_LENGTHS))} letters (ru, enu)")
    return tokens[0], langs


def check_localized(pkg: Package, iwad_names: set[str], declared: set[str], report: Report) -> None:
    """Language variants: right folder, right name, a base, the same size.

    Also the provenance rule of `licences`: the variant is the same asset in
    another language, so its base's row in LICENSES.md covers it (or a row
    of its own). Kept here rather than in LICENSED_DIRS because
    check_licences above matches a file by its stem, its name or a folder
    row, and would ask for a `M_PAUSE.RU` row. tools/release.py adds the
    folder to its own asset list and matches a variant by its base too
    (tools/licences.py, `localized_base` and `RegisterRow.covers`).
    """
    files = sorted(pkg.files_under(LOCALIZED_DIR))
    report.stats["localized_variants"] = 0
    if not files:
        report.note("localized", "no language variants packed")
        return
    bases: dict[str, str] = {}
    for folder in LOCALIZED_BASE_DIRS:
        for path in pkg.files_under(folder):
            bases.setdefault(Path(path).stem.upper(), path)
    valid = 0
    for path in files:
        folder, _, filename = path.rpartition("/")
        if folder.lower() != LOCALIZED_TEXTURES_DIR:
            report.error("localized", path,
                         f"outside {LOCALIZED_TEXTURES_DIR}/: GZDoom only scans that folder, "
                         "so this file is never loaded")
            continue
        parts = localized_name_parts(filename)
        if isinstance(parts, str):
            report.error("localized", path, parts)
            continue
        base, langs = parts
        problem = lump_name_problem(base)
        if problem:
            report.error("localized", path, f"base {problem}")
            continue
        key = base.upper()
        base_path = bases.get(key)
        if base_path is None:
            if key in iwad_names:
                report.warn("localized", path,
                            f"base {key} is an IWAD graphic: size not checked offline")
            else:
                report.error("localized", path,
                             f"unknown base graphic {key}: nothing packed under "
                             f"{'/, '.join(LOCALIZED_BASE_DIRS)}/ has that name, so GZDoom "
                             "prints 'Unknown texture ... for localized variant' and drops it")
                continue
        else:
            try:
                variant = read_png(pkg.read(path))
                original = read_png(pkg.read(base_path))
            except PngError as exc:
                report.error("localized", path, f"size not comparable with {base_path}: {exc}")
                continue
            if (variant.width, variant.height) != (original.width, original.height):
                report.error("localized", path,
                             f"{variant.width}x{variant.height}, but {base_path} is "
                             f"{original.width}x{original.height}: GZDoom refuses a variant "
                             "that is not the same size as the graphic it replaces")
                continue
        if not (key in declared or Path(filename).stem.upper() in declared
                or filename.upper() in declared):
            report.error("localized", path,
                         f"no row for {key!r} (or for the variant) in "
                         f"{DEFAULT_LICENSES.relative_to(PROJECT_ROOT)}: "
                         "a packed asset without recorded provenance cannot ship")
            continue
        valid += 1
        report.note("localized", f"{path} -> {key} for {', '.join(langs)}")
    report.stats["localized_variants"] = valid
    report.notes.setdefault("localized", []).insert(
        0, f"{valid} of {len(files)} language variant(s) valid; NB GZDoom g4.14.2 registers "
           "them but does not draw them (MOD-SPEC 2)")


def check_pk3(
    pk3: Path,
    spec: Path = DEFAULT_SPEC,
    licenses: Path = DEFAULT_LICENSES,
    palette_json: Path = DEFAULT_PALETTE,
) -> Report:
    report = Report(pk3=str(pk3))
    if not pk3.is_file():
        report.error("package", str(pk3), "file does not exist (run python3 tools/build.py)")
        return report
    if not zipfile.is_zipfile(pk3):
        report.error("package", str(pk3), "not a zip archive: a PK3 is a zip (MOD-SPEC 2)")
        return report
    try:
        zf = zipfile.ZipFile(pk3)
    except zipfile.BadZipFile as exc:
        report.error("package", str(pk3), f"cannot be opened as a zip: {exc}")
        return report
    with zf:
        pkg = Package(pk3, zf, [n for n in zf.namelist() if not n.endswith("/")])
        check_package(pkg, report)
        check_root_lumps(pkg, report)
        maps = check_maps(pkg, report)
        check_textures(pkg, maps, iwad_assets_from_spec(spec), report)
        check_images(pkg, palette_colours(palette_json), report)
        check_sprites(pkg, report)
        check_state_sprites(pkg, iwad_sprites_from_spec(spec), report)
        check_licences(pkg, licensed_names(licenses), report)
        check_zscript(pkg, report)
        check_menus(pkg, report)
        check_localized(pkg, iwad_assets_from_spec(spec), licensed_names(licenses), report)
    return report


def render(report: Report, strict: bool = False, quiet: bool = False) -> str:
    lines: list[str] = [f"check_pk3: {report.pk3}", ""]
    for category in CATEGORIES:
        found = report.of(category)
        errors = [f for f in found if f.severity == SEVERITY_ERROR]
        if category in report.skipped:
            status = "SKIP"
        elif errors:
            status = "FAIL"
        elif found:
            status = "warn"
        else:
            status = "OK"
        if quiet and status == "OK":
            continue
        head = f"{category:<9} {status:<4}"
        notes = report.notes.get(category, [])
        summary = report.skipped.get(category) or (notes[0] if notes else "")
        lines.append(f"{head}  {summary}".rstrip())
        for note in notes[1:]:
            lines.append(f"{'':<15}{note}")
        for finding in found:
            lines.append(finding.render())
    lines.append("")
    lines.append(f"--- {len(report.errors)} error(s), {len(report.warnings)} warning(s) ---")
    lines.append("VERDICT: PASS" if report.ok(strict) else "VERDICT: FAIL")
    return "\n".join(lines)


def as_json(report: Report, strict: bool = False) -> str:
    return json.dumps(
        {
            "pk3": report.pk3,
            "ok": report.ok(strict),
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "stats": report.stats,
            "skipped": report.skipped,
            "notes": report.notes,
            "findings": [f.as_dict() for f in report.findings],
        },
        indent=2,
        sort_keys=True,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tools/check_pk3.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--pk3", type=Path, default=DEFAULT_PK3, help="package to validate")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC, help="MOD-SPEC.md (IWAD asset table)")
    parser.add_argument("--licenses", type=Path, default=DEFAULT_LICENSES, help="LICENSES.md")
    parser.add_argument("--palette", type=Path, default=DEFAULT_PALETTE, help="palette.json")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument("--quiet", action="store_true", help="hide categories that pass cleanly")
    parser.add_argument("--json", action="store_true", help="machine-readable output (for CI)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = check_pk3(args.pk3, args.spec, args.licenses, args.palette)
    print(as_json(report, args.strict) if args.json else render(report, args.strict, args.quiet))
    return EXIT_OK if report.ok(args.strict) else EXIT_FAILURES


if __name__ == "__main__":
    sys.exit(main())
