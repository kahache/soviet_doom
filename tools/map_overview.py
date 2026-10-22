#!/usr/bin/env python3
"""Top-down overview PNGs of the maps, drawn from the generated TEXTMAP.

    python tools/map_overview.py --all             # every map + the campaign sheet
    python tools/map_overview.py MAP05 RANGE        # just these, into docs/levels/shots/
    python tools/map_overview.py MAP05 --out-dir /tmp/x
    python tools/map_overview.py --textmap some/TEXTMAP.txt --out x.png
    python tools/map_overview.py --sheet-only       # only campaign-overview.png

Why this exists: until 2026-10-22 every `docs/levels/shots/MAPxx-overview.png`
was drawn by a throwaway script of whichever agent built the map, so each
one had its own colours and legend and several went stale when textures or
start positions changed. This tool draws all of them the same way from the
same source the PK3 is built from (`src/maps/<MAP>/map.py` -> TEXTMAP, the
text `tools/build.py --print-textmap` prints), so a rerun after any map edit
refreshes the picture.

What a picture shows (north up, Doom's +y):
  * sectors filled by FLOOR HEIGHT: the map's distinct floor heights are
    ranked low -> high onto a dark-blue -> khaki ramp, so every step reads as
    a different tone; the stepped bar under the map is the exact key;
  * one-sided lines thick and black, steps (two-sided lines whose floors
    differ) thin, impassable two-sided rails pale;
  * doors: the door sector filled rust, a locked door in its key's colour
    with the key's letter; the switch that works a remote door, a lift or a
    floor drawn as a thick tick on its wall;
  * the exit switch (Exit_Normal / Exit_Secret) in red with "EXIT";
  * the player 1 start as a green arrow; keys as diamonds; weapons as white
    squares; secret sectors hatched magenta and numbered S1..Sn (TEXTMAP
    order); lines flagged `secret` (hidden doors) in magenta; damaging
    floors cross-hatched;
  * monsters on skill 3 as dots, one colour per class, counted in the legend;
  * a 512-unit grid, labelled on the edges.

Text here is a label for the team, never a game asset; it uses the sheets'
face (`tools/art/artlib.FONT_SMALL`), Pillow's default when that face is
missing (Linux CI). Output is deterministic on one machine (no timestamps);
like every text-bearing sheet it is not byte-identical across machines
(CLAUDE.md, "Text-bearing assets do not reproduce").

Reads src/ only; writes only the PNGs it is asked for. Needs Pillow + numpy
(the venv).
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
SHOTS_DIR = PROJECT_ROOT / "docs" / "levels" / "shots"
LANGUAGE = SRC_DIR / "lumps" / "LANGUAGE"
SHEET_NAME = "campaign-overview.png"

MAPS = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09", "RANGE")
EPISODES = (("Episode 1", ("MAP01", "MAP02", "MAP03")),
             ("Episode 2", ("MAP04", "MAP05", "MAP06")),
             ("Episode 3", ("MAP07", "MAP08", "MAP09")))

SKILL = 3                    # the skill the monsters and items are drawn for
GRID = 512                   # map units between grid lines
PAD_UNITS = 64               # map units of void around the map's bounding box
# Pixels per map unit, largest first: the first that fits wins, so the grid
# always lands on whole pixels-ish and the scale reads as a round 1:N.
SCALE_LADDER = (1 / 2, 1 / 3, 1 / 4, 1 / 5, 1 / 6, 1 / 8, 1 / 10, 1 / 12, 1 / 16, 1 / 20, 1 / 24, 1 / 32)
MAX_MAP_W, MAX_MAP_H = 2000, 1500        # map area of a single overview, px
TILE_W, TILE_H = 600, 440                # one map's area on the campaign sheet, px

# --------------------------------------------------------------- colours
BG = (24, 25, 30)
VOID = (32, 33, 39)
GRID_BLEND = 0.16            # how much of GRID_INK is mixed into the grid pixels
GRID_INK = (255, 255, 255)
INK = (232, 230, 222)
MUTE = (150, 150, 145)
WALL = (6, 6, 8)
STEP = (14, 14, 18)
RAIL = (205, 205, 200)
DOOR = (201, 111, 59)
KEY_COLOURS = {"blue": (64, 128, 255), "yellow": (255, 210, 48), "red": (240, 52, 52)}
LOCK_ANY = (230, 230, 230)
EXIT = (255, 36, 36)
SWITCH_OTHER = (64, 224, 232)
SECRET = (226, 64, 226)
HAZARD = (120, 255, 90)
START = (40, 232, 96)
WEAPON = (250, 250, 250)
# Floor ramp, low -> high: deep blue-slate, teal, moss, khaki, pale sand.
# Kept clear of saturated orange/red/yellow/blue so doors and keys stand out.
RAMP = ((38, 50, 92), (40, 92, 112), (62, 124, 104), (112, 146, 84),
        (166, 166, 104), (214, 204, 156))

# --------------------------------------------------------------- UDMF meaning
# ZDoom line specials (zdoom.org/wiki/Action_specials).
DOOR_OPEN, DOOR_RAISE, DOOR_LOCKED_RAISE = 11, 12, 13
DOOR_SPECIALS = {10, DOOR_OPEN, DOOR_RAISE, DOOR_LOCKED_RAISE, 14, 105, 106, 202, 249}
EXIT_NORMAL, EXIT_SECRET = 243, 244
TELEPORT_SPECIALS = {70, 71}
SECTOR_SECRET_BIT = 1024     # Boom generalised sector flag, as the maps write it
# Lock numbers (GZDoom lockdefs.txt): card, skull, either.
LOCKS = {1: "red", 4: "red", 129: "red", 2: "blue", 5: "blue", 130: "blue",
         3: "yellow", 6: "yellow", 131: "yellow"}
KEYS = {5: "blue", 40: "blue", 6: "yellow", 39: "yellow", 13: "red", 38: "red"}
PLAYER1_START = 1
WEAPONS = set(range(21001, 21020)) | {2001, 2002, 2003, 2004, 2005, 2006, 82}


@dataclass(frozen=True)
class MonsterClass:
    name: str
    colour: tuple[int, int, int]
    radius: int              # dot radius in px on a full overview


# Editor numbers -> our classes (docs/engine/MOD-SPEC.md 6.1: each SD_ class
# also replaces a Doom monster, so a map placing the Doom number spawns ours).
_RIFLEMAN = MonsterClass("Reich rifleman", (238, 70, 60), 4)
_TROOPER = MonsterClass("Legion trooper", (80, 168, 255), 4)
_STORM = MonsterClass("Stormtrooper", (184, 84, 236), 5)
_HOUND = MonsterClass("Reich hound", (255, 148, 36), 5)
_DOUGHBOY = MonsterClass("Doughboy", (150, 255, 120), 6)
_PANZER = MonsterClass("Panzermensch", (255, 92, 184), 7)
_SCHWER = MonsterClass("Panzermensch Schwer", (150, 20, 24), 8)
_GENERAL = MonsterClass("General (boss)", (255, 255, 255), 10)
MONSTERS: dict[int, MonsterClass] = {
    21100: _RIFLEMAN, 3004: _RIFLEMAN,
    21101: _TROOPER, 9: _TROOPER,
    21102: _STORM, 3001: _STORM,
    21103: _HOUND, 3002: _HOUND,
    21104: _DOUGHBOY, 3005: _DOUGHBOY,
    21105: _PANZER, 69: _PANZER,
    21107: _SCHWER, 3003: _SCHWER,
    21106: _GENERAL, 16: _GENERAL,
}
MONSTER_ORDER = (_RIFLEMAN, _TROOPER, _STORM, _HOUND, _DOUGHBOY, _PANZER, _SCHWER, _GENERAL)


# --------------------------------------------------------------- parsing
_BLOCK = re.compile(r"(\w+)\s*\{([^}]*)\}")
_FIELD = re.compile(r"(\w+)\s*=\s*([^;]+);")
_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def _value(raw: str):
    raw = raw.strip()
    if raw.startswith('"'):
        return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    try:
        return int(raw)
    except ValueError:
        return float(raw)


@dataclass
class UdmfMap:
    vertices: list[tuple[float, float]] = field(default_factory=list)
    linedefs: list[dict] = field(default_factory=list)
    sidedefs: list[dict] = field(default_factory=list)
    sectors: list[dict] = field(default_factory=list)
    things: list[dict] = field(default_factory=list)

    def side_sector(self, side: int | None) -> int | None:
        return None if side is None else self.sidedefs[side]["sector"]

    def line_sectors(self, line: dict) -> tuple[int | None, int | None]:
        return self.side_sector(line.get("sidefront")), self.side_sector(line.get("sideback"))


def parse_textmap(text: str) -> UdmfMap:
    """The blocks of a UDMF TEXTMAP, in file order (indices are the UDMF ones)."""
    m = UdmfMap()
    for kind, body in _BLOCK.findall(_COMMENT.sub("", text)):
        fields = {k: _value(v) for k, v in _FIELD.findall(body)}
        kind = kind.lower()
        if kind == "vertex":
            m.vertices.append((float(fields["x"]), float(fields["y"])))
        elif kind == "linedef":
            m.linedefs.append(fields)
        elif kind == "sidedef":
            m.sidedefs.append(fields)
        elif kind == "sector":
            m.sectors.append(fields)
        elif kind == "thing":
            m.things.append(fields)
    return m


def load_textmap(map_name: str, src: Path = SRC_DIR) -> str:
    """The TEXTMAP lump `src/maps/<MAP>/map.py` generates (what the PK3 packs)."""
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from sdbuild.pk3 import _load_map_module  # the build's own loader

    script = src / "maps" / map_name / "map.py"
    if not script.is_file():
        raise FileNotFoundError(f"no map script {script}")
    for name, data in _load_map_module(script, TOOLS_DIR).lumps():
        if name.upper() == "TEXTMAP":
            return data.decode("ascii")
    raise ValueError(f"{script} produced no TEXTMAP lump")


def map_names(map_name: str, language: Path = LANGUAGE) -> tuple[str, str]:
    """(English, Russian) display names from LANGUAGE; empty strings if absent."""
    if not language.is_file():
        return "", ""
    key = f"SD_{map_name.upper()}_NAME"
    names: dict[str, str] = {}
    section = ""
    for line in language.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("["):
            section = "enu" if "enu" in s else s.strip("[]").split()[0]
            continue
        mm = re.match(rf"{key}\s*=\s*\"(.*)\";", s)
        if mm and section not in names:
            names[section] = mm.group(1)
    return names.get("enu", ""), names.get("ru", "")


# --------------------------------------------------------------- analysis
@dataclass
class Features:
    door_sectors: dict[int, str]                      # sector -> "door" | key colour | "any"
    switch_lines: list[tuple[int, str]]               # (line, kind) kind: door|blue|...|other
    exit_lines: list[tuple[int, bool]]                # (line, secret exit?)
    secret_lines: list[int]                           # `secret` flag: hidden doors
    secret_sectors: list[int]
    hazard_sectors: list[int]
    start: dict | None
    keys: list[tuple[dict, str]]
    weapons: list[dict]
    monsters: list[tuple[dict, MonsterClass]]


def _on_skill(thing: dict, skill: int) -> bool:
    return bool(thing.get(f"skill{skill}")) and thing.get("single", False) is not False


def analyse(m: UdmfMap, skill: int = SKILL) -> Features:
    by_tag: dict[int, list[int]] = {}
    for i, s in enumerate(m.sectors):
        if s.get("id"):
            by_tag.setdefault(int(s["id"]), []).append(i)

    doors: dict[int, str] = {}
    switches: list[tuple[int, str]] = []
    exits: list[tuple[int, bool]] = []
    for li, line in enumerate(m.linedefs):
        special = line.get("special", 0)
        if not special:
            continue
        front, back = m.line_sectors(line)
        tag = int(line.get("arg0", 0) or 0)
        if special in (EXIT_NORMAL, EXIT_SECRET):
            exits.append((li, special == EXIT_SECRET))
            continue
        if special in TELEPORT_SPECIALS:
            continue
        if special in DOOR_SPECIALS:
            kind = "door"
            if special == DOOR_LOCKED_RAISE:
                kind = LOCKS.get(int(line.get("arg3", 0) or 0), "any")
            elif line.get("locknumber"):
                kind = LOCKS.get(int(line["locknumber"]), "any")
            targets = by_tag.get(tag, []) if tag else ([back] if back is not None else [])
            for t in targets:
                # a locked kind wins over a plain door on the same sector
                if doors.get(t, "door") == "door":
                    doors[t] = kind
            if back is None or back not in targets:
                switches.append((li, kind))
        else:
            switches.append((li, "other"))

    secret_sectors = [i for i, s in enumerate(m.sectors)
                      if (int(s.get("special", 0) or 0) & SECTOR_SECRET_BIT) or s.get("secret")]
    hazards = [i for i, s in enumerate(m.sectors) if int(s.get("damageamount", 0) or 0) > 0]
    secret_lines = [i for i, line in enumerate(m.linedefs) if line.get("secret")]

    start = None
    keys, weapons, monsters = [], [], []
    for t in m.things:
        ty = t.get("type")
        if ty == PLAYER1_START and start is None:
            start = t
        if not _on_skill(t, skill):
            continue
        if ty in KEYS:
            keys.append((t, KEYS[ty]))
        elif ty in WEAPONS:
            weapons.append(t)
        elif ty in MONSTERS:
            monsters.append((t, MONSTERS[ty]))
    return Features(doors, switches, exits, secret_lines, secret_sectors, hazards,
                    start, keys, weapons, monsters)


# --------------------------------------------------------------- geometry
@dataclass(frozen=True)
class View:
    """Map units -> image pixels (y flipped: north up)."""
    min_x: float
    max_y: float
    scale: float
    ox: int
    oy: int

    def px(self, x: float, y: float) -> tuple[float, float]:
        return self.ox + (x - self.min_x) * self.scale, self.oy + (self.max_y - y) * self.scale


def bounds(m: UdmfMap) -> tuple[float, float, float, float]:
    xs = [v[0] for v in m.vertices]
    ys = [v[1] for v in m.vertices]
    return min(xs) - PAD_UNITS, min(ys) - PAD_UNITS, max(xs) + PAD_UNITS, max(ys) + PAD_UNITS


def pick_scale(width: float, height: float, max_w: int, max_h: int) -> float:
    for s in SCALE_LADDER:
        if width * s <= max_w and height * s <= max_h:
            return s
    return min(max_w / width, max_h / height)


def scale_label(scale: float) -> str:
    inv = 1 / scale
    return f"1 px = {inv:g} units" if abs(inv - round(inv)) < 1e-9 else f"1 px = {inv:.1f} units"


def sector_labels(m: UdmfMap, view: View, w: int, h: int) -> np.ndarray:
    """Per-pixel sector index (-1 = void), even-odd fill of each sector's edges.

    Every linedef bounding a sector counts once for that sector (a line with
    the same sector on both sides counts for none), so holes - pillars, inner
    sectors - fall out of the parity without chaining edges into loops.
    """
    edges: dict[int, list[tuple[float, float, float, float]]] = {}
    for line in m.linedefs:
        front, back = m.line_sectors(line)
        if front == back:
            continue
        a = view.px(*m.vertices[line["v1"]])
        b = view.px(*m.vertices[line["v2"]])
        for s in (front, back):
            if s is not None:
                edges.setdefault(s, []).append((a[0], a[1], b[0], b[1]))

    label = np.full((h, w), -1, np.int32)
    for sec in sorted(edges):
        e = np.array(edges[sec], dtype=np.float64)
        x1, y1, x2, y2 = e[:, 0], e[:, 1], e[:, 2], e[:, 3]
        r0 = max(0, int(math.floor(min(y1.min(), y2.min()))))
        r1 = min(h, int(math.ceil(max(y1.max(), y2.max()))) + 1)
        c0 = max(0, int(math.floor(min(x1.min(), x2.min()))))
        c1 = min(w, int(math.ceil(max(x1.max(), x2.max()))) + 1)
        if r1 <= r0 or c1 <= c0:
            continue
        bw = c1 - c0
        toggles = np.zeros((r1 - r0, bw + 1), np.int32)
        for ax, ay, bx, by in e:
            if ay == by:
                continue
            lo, hi = (ay, by) if ay < by else (by, ay)
            rows = np.arange(max(r0, math.ceil(lo - 0.5)), min(r1, math.ceil(hi - 0.5)))
            if rows.size == 0:
                continue
            xc = ax + (rows + 0.5 - ay) * (bx - ax) / (by - ay)
            cols = np.clip(np.floor(xc - 0.5).astype(np.int64) + 1 - c0, 0, bw)
            np.add.at(toggles, (rows - r0, cols), 1)
        inside = (np.cumsum(toggles[:, :bw], axis=1) & 1).astype(bool)
        label[r0:r1, c0:c1][inside] = sec
    return label


def ramp(t: float) -> tuple[int, int, int]:
    t = min(1.0, max(0.0, t)) * (len(RAMP) - 1)
    i = min(int(t), len(RAMP) - 2)
    f = t - i
    a, b = RAMP[i], RAMP[i + 1]
    return tuple(int(round(a[k] + (b[k] - a[k]) * f)) for k in range(3))


def floor_colours(m: UdmfMap) -> tuple[list[int], dict[int, tuple[int, int, int]]]:
    heights = sorted({int(s.get("heightfloor", 0)) for s in m.sectors})
    n = len(heights)
    return heights, {hgt: ramp(0.5 if n == 1 else i / (n - 1)) for i, hgt in enumerate(heights)}


# --------------------------------------------------------------- fonts
def _font_path() -> str | None:
    try:
        sys.path.insert(0, str(TOOLS_DIR / "art"))
        import artlib  # the sheets' label face (Arial Narrow Bold / Arial Bold)
        return artlib.FONT_SMALL if Path(artlib.FONT_SMALL).is_file() else None
    except Exception:  # pragma: no cover - artlib missing is a broken checkout
        return None


_FONT_CACHE: dict[int, ImageFont.ImageFont] = {}


def font(size: int):
    if size not in _FONT_CACHE:
        path = _font_path()
        _FONT_CACHE[size] = (ImageFont.truetype(path, size) if path
                             else ImageFont.load_default(size=size))
    return _FONT_CACHE[size]


def text(d: ImageDraw.ImageDraw, xy, s: str, size: int, fill=INK, anchor="la", stroke: int = 0):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0) if stroke else None)


def text_w(s: str, size: int) -> float:
    return font(size).getlength(s)


# --------------------------------------------------------------- drawing
@dataclass(frozen=True)
class Style:
    """Pixel sizes; the campaign tiles use a smaller set than a full overview."""
    wall: int = 3
    step: int = 1
    rail: int = 2
    switch: int = 6
    marker: float = 1.0          # multiplies monster/key/start sizes
    labels: bool = True
    label_size: int = 15


FULL = Style()
TILE = Style(wall=2, step=1, rail=1, switch=4, marker=0.6, labels=False)


def _hatch(h: int, w: int, period: int, width: int, sign: int) -> np.ndarray:
    r, c = np.mgrid[0:h, 0:w]
    return ((c + sign * r) % period) < width


def _diamond(d, cx, cy, r, fill, outline=(0, 0, 0)):
    d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fill, outline=outline)
    d.polygon([(cx, cy - r + 1), (cx + r - 1, cy), (cx, cy + r - 1), (cx - r + 1, cy)], outline=outline)


def _arrow(d, cx, cy, angle_deg, r, fill):
    a = math.radians(angle_deg)
    pts = []
    for da, rr in ((0, r), (2.5, r * 0.8), (-2.5, r * 0.8)):
        pts.append((cx + math.cos(a + da) * rr, cy - math.sin(a + da) * rr))
    d.polygon(pts, fill=fill, outline=(0, 0, 0))


def _dot(d, cx, cy, r, fill):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=(0, 0, 0))


def draw_map(m: UdmfMap, feats: Features, w: int, h: int, view: View, style: Style) -> Image.Image:
    """The map area alone: fills, grid, lines, specials, things, labels."""
    label = sector_labels(m, view, w, h)
    _, fcol = floor_colours(m)
    n = len(m.sectors)
    lut = np.zeros((n + 1, 3), np.float64)
    lut[n] = VOID                                         # index -1 wraps to the last row
    for i, s in enumerate(m.sectors):
        lut[i] = fcol[int(s.get("heightfloor", 0))]
    for sec, kind in feats.door_sectors.items():
        lut[sec] = DOOR if kind == "door" else KEY_COLOURS.get(kind, LOCK_ANY)
    rgb = lut[label]

    # hatches: secrets magenta, damaging floors green
    for secs, colour, sign in ((feats.secret_sectors, SECRET, 1), (feats.hazard_sectors, HAZARD, -1)):
        if secs:
            mask = np.isin(label, secs) & _hatch(h, w, 7, 2, sign)
            rgb[mask] = colour

    # the 512 grid, blended so it reads on void and on floors
    gx = [view.px(x, 0)[0] for x in range(_grid_start(view.min_x), int(view.min_x + w / view.scale) + 1, GRID)]
    gy = [view.px(0, y)[1] for y in range(_grid_start(view.max_y - h / view.scale), int(view.max_y) + 1, GRID)]
    grid = np.zeros((h, w), bool)
    for x in gx:
        if 0 <= int(round(x)) < w:
            grid[:, int(round(x))] = True
    for y in gy:
        if 0 <= int(round(y)) < h:
            grid[int(round(y)), :] = True
    rgb[grid] = rgb[grid] * (1 - GRID_BLEND) + np.array(GRID_INK) * GRID_BLEND

    img = Image.fromarray(np.clip(np.round(rgb), 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)

    def seg(li, colour, width):
        line = m.linedefs[li]
        a = view.px(*m.vertices[line["v1"]])
        b = view.px(*m.vertices[line["v2"]])
        d.line([a, b], fill=colour, width=width)
        return a, b

    # structure: steps first, rails, then walls on top
    order = []
    for li, line in enumerate(m.linedefs):
        front, back = m.line_sectors(line)
        if back is None or front is None:
            order.append((2, li, WALL, style.wall))
        elif front == back:
            continue
        elif line.get("blocking"):
            order.append((1, li, RAIL, style.rail))
        elif m.sectors[front].get("heightfloor", 0) != m.sectors[back].get("heightfloor", 0) \
                or front in feats.door_sectors or back in feats.door_sectors:
            order.append((0, li, STEP, style.step))
    for _, li, colour, width in sorted(order):
        seg(li, colour, width)

    for li in feats.secret_lines:
        seg(li, SECRET, style.wall)
    for li, kind in feats.switch_lines:
        colour = SWITCH_OTHER if kind == "other" else DOOR if kind == "door" else KEY_COLOURS.get(kind, LOCK_ANY)
        seg(li, (0, 0, 0), style.switch + 2)
        seg(li, colour, style.switch)
    exit_points = []
    for li, secret_exit in feats.exit_lines:
        seg(li, (0, 0, 0), style.switch + 3)
        a, b = seg(li, EXIT if not secret_exit else SECRET, style.switch + 1)
        exit_points.append((((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), secret_exit))

    k = style.marker
    for t in feats.weapons:
        x, y = view.px(t["x"], t["y"])
        r = max(2, 4 * k)
        d.rectangle((x - r, y - r, x + r, y + r), fill=WEAPON, outline=(0, 0, 0))
    for t, cls in sorted(feats.monsters, key=lambda tc: tc[1].radius):
        x, y = view.px(t["x"], t["y"])
        _dot(d, x, y, max(2, cls.radius * k), cls.colour)
    for t, colour in feats.keys:
        x, y = view.px(t["x"], t["y"])
        r = max(5, 11 * k)
        _diamond(d, x, y, r, KEY_COLOURS[colour])
        if style.labels:
            text(d, (x, y + 1), colour[0].upper(), 13, fill=(0, 0, 0), anchor="mm")
    if feats.start is not None:
        x, y = view.px(feats.start["x"], feats.start["y"])
        _arrow(d, x, y, feats.start.get("angle", 0), max(7, 16 * k), START)

    if style.labels:
        size = style.label_size
        for i, sec in enumerate(feats.secret_sectors, 1):
            ys, xs = np.nonzero(label == sec)
            if xs.size:
                text(d, (float(xs.mean()), float(ys.mean())), f"S{i}", size, fill=(255, 190, 255),
                     anchor="mm", stroke=2)
        for (x, y), secret_exit in exit_points:
            text(d, (x, y - 10), "SECRET EXIT" if secret_exit else "EXIT", size, fill=(255, 120, 120),
                 anchor="md", stroke=2)
        if feats.start is not None:
            x, y = view.px(feats.start["x"], feats.start["y"])
            text(d, (x, y + 16), "START", size, fill=(150, 255, 170), anchor="ma", stroke=2)
    return img


def _grid_start(v: float) -> int:
    return int(math.floor(v / GRID) * GRID)


def _grid_labels(d: ImageDraw.ImageDraw, view: View, w: int, h: int, ox: int, oy: int) -> None:
    """Grid coordinates outside the map area: x along the top, y down the left."""
    for x in range(_grid_start(view.min_x), int(view.min_x + w / view.scale) + 1, GRID):
        px = view.px(x, 0)[0]
        if 0 <= px < w:
            text(d, (ox + px, oy - 4), str(x), 12, fill=MUTE, anchor="md")
    for y in range(_grid_start(view.max_y - h / view.scale), int(view.max_y) + 1, GRID):
        py = view.px(0, y)[1]
        if 0 <= py < h:
            text(d, (ox - 6, oy + py), str(y), 12, fill=MUTE, anchor="rm")


# --------------------------------------------------------------- legend
def _legend_items(feats: Features | None, counts: dict[MonsterClass, int] | None):
    """(icon painter, text) pairs; painters take (draw, x, y) with y the row centre."""
    def line_icon(colour, width, outline=False, floor=False):
        def paint(d, x, y):
            if floor:   # dark lines need a floor under them to be seen
                d.rectangle((x, y - 8, x + 26, y + 8), fill=RAMP[3])
            if outline:
                d.line([(x, y), (x + 26, y)], fill=(0, 0, 0), width=width + 2)
            d.line([(x, y), (x + 26, y)], fill=colour, width=width)
        return paint

    def box_icon(colour, hatch=None):
        def paint(d, x, y):
            d.rectangle((x, y - 8, x + 26, y + 8), fill=hatch[1] if hatch else colour, outline=(0, 0, 0))
            if hatch:
                for i in range(-16, 30, 5):
                    d.line([(x + max(0, i), y + 8 - max(0, -i)), (x + min(26, i + 16), y + 8 - min(16, 26 - i))],
                           fill=colour, width=2)
        return paint

    items = [
        (lambda d, x, y: _arrow(d, x + 13, y, 0, 14, START), "player start (arrow = facing)"),
        (line_icon(EXIT, 7, True), "exit switch (EXIT)"),
        (box_icon(DOOR), "door"),
    ]
    for colour in ("blue", "yellow", "red"):
        items.append((box_icon(KEY_COLOURS[colour]), f"{colour} locked door"))
    items += [
        (lambda d, x, y: (_diamond(d, x + 13, y, 10, KEY_COLOURS["blue"]),
                          _diamond(d, x + 30, y, 10, KEY_COLOURS["yellow"]),
                          _diamond(d, x + 47, y, 10, KEY_COLOURS["red"])), "        keys (B / Y / R)"),
        (line_icon(DOOR, 6, True), "remote-door switch (key colour if locked)"),
        (line_icon(SWITCH_OTHER, 6, True), "switch: lift / floor / other"),
        (box_icon(SECRET, hatch=(SECRET, (60, 60, 70))), "secret sector (S1, S2...)"),
        (line_icon(SECRET, 3), "hidden door (line flagged secret)"),
        (box_icon(HAZARD, hatch=(HAZARD, (60, 60, 70))), "damaging floor"),
        (line_icon(WALL, 4, floor=True), "solid wall (one-sided)"),
        (line_icon(STEP, 1, floor=True), "step / ledge (floor changes)"),
        (line_icon(RAIL, 2), "impassable rail (two-sided)"),
        (lambda d, x, y: d.rectangle((x + 9, y - 4, x + 17, y + 4), fill=WEAPON, outline=(0, 0, 0)),
         "weapon (skill %d)" % SKILL),
    ]
    for cls in MONSTER_ORDER:
        if counts is None or counts.get(cls):
            n = "" if counts is None else f"  x{counts[cls]}"
            items.append(((lambda c: lambda d, x, y: _dot(d, x + 13, y, min(c.radius, 9), c.colour))(cls),
                          f"{cls.name}{n}"))
    return items


ROW_H = 24
COL_W = 370


def legend_height(n_items: int, width: int) -> int:
    cols = max(1, (width - 40) // COL_W)
    return math.ceil(n_items / cols) * ROW_H


def draw_legend(d, items, x0: int, y0: int, width: int) -> int:
    cols = max(1, (width - 40) // COL_W)
    rows = math.ceil(len(items) / cols)
    for i, (paint, label) in enumerate(items):
        c, r = divmod(i, rows)
        x, y = x0 + c * COL_W, y0 + r * ROW_H + ROW_H // 2
        paint(d, x, y)
        text(d, (x + 36, y), label, 15, anchor="lm")
    return rows * ROW_H


def draw_floor_key(d, heights, colours, x0: int, y0: int, width: int) -> int:
    """The stepped bar: one cell per distinct floor height, low -> high."""
    text(d, (x0, y0), "floor height (map units), ranked low -> high:", 15, anchor="la")
    y = y0 + 22
    n = len(heights)
    cell = max(18, min(64, (width - 40) // max(1, n)))
    every = max(1, math.ceil(text_w("-9999", 12) * 1.3 / cell))
    for i, hgt in enumerate(heights):
        x = x0 + i * cell
        d.rectangle((x, y, x + cell - 1, y + 16), fill=colours[hgt], outline=(0, 0, 0))
        if i % every == 0 or i == n - 1:
            text(d, (x + cell / 2, y + 20), str(hgt), 12, fill=MUTE, anchor="ma")
    return 22 + 16 + 20 + 14


# --------------------------------------------------------------- pages
HEADER_H = 84
MARGIN = 48


def render_overview(textmap: str, map_name: str = "", title: str = "", source: str = "",
                    skill: int = SKILL, max_w: int = MAX_MAP_W, max_h: int = MAX_MAP_H) -> Image.Image:
    """One map's overview page: header, map with grid labels, legend, floor key."""
    m = parse_textmap(textmap)
    feats = analyse(m, skill)
    x0, y0, x1, y1 = bounds(m)
    scale = pick_scale(x1 - x0, y1 - y0, max_w, max_h)
    mw, mh = int(math.ceil((x1 - x0) * scale)), int(math.ceil((y1 - y0) * scale))
    view = View(x0, y1, scale, 0, 0)
    area = draw_map(m, feats, mw, mh, view, FULL)

    counts: dict[MonsterClass, int] = {}
    for _, cls in feats.monsters:
        counts[cls] = counts.get(cls, 0) + 1
    items = _legend_items(feats, counts)
    page_w = max(mw + 2 * MARGIN, 3 * COL_W + 2 * MARGIN)
    heights, colours = floor_colours(m)
    leg_h = legend_height(len(items), page_w - 2 * MARGIN)
    page_h = HEADER_H + 22 + mh + 28 + leg_h + 24 + 72 + 30
    img = Image.new("RGB", (page_w, page_h), BG)
    d = ImageDraw.Draw(img)

    head = f"{map_name}  {title}".strip() if title else map_name
    text(d, (MARGIN, 18), head or "map overview", 26, anchor="la")
    total = len(feats.monsters)
    sub = (f"north up  |  grid {GRID} units  |  {scale_label(scale)}  |  skill {skill}: "
           f"{total} monsters, {len(feats.keys)} keys, {len(feats.secret_sectors)} secrets, "
           f"{len(feats.door_sectors)} door sectors")
    text(d, (MARGIN, 66), sub, 15, fill=MUTE, anchor="ls")

    ax = (page_w - mw) // 2
    ay = HEADER_H + 22
    img.paste(area, (ax, ay))
    d.rectangle((ax - 1, ay - 1, ax + mw, ay + mh), outline=(70, 72, 80))
    _grid_labels(d, view, mw, mh, ax, ay)

    y = ay + mh + 28
    y += draw_legend(d, items, MARGIN, y, page_w - 2 * MARGIN) + 24
    draw_floor_key(d, heights, colours, MARGIN, y, page_w - 2 * MARGIN)
    foot = f"generated by tools/map_overview.py from {source or 'TEXTMAP'}"
    text(d, (MARGIN, page_h - 12), foot, 12, fill=MUTE, anchor="ls")
    return img


def render_tile(textmap: str, skill: int = SKILL, tile_w: int = TILE_W, tile_h: int = TILE_H) -> tuple[Image.Image, float]:
    """The map area alone, fitted into a campaign-sheet tile, no labels."""
    m = parse_textmap(textmap)
    feats = analyse(m, skill)
    x0, y0, x1, y1 = bounds(m)
    scale = pick_scale(x1 - x0, y1 - y0, tile_w, tile_h)
    mw, mh = int(math.ceil((x1 - x0) * scale)), int(math.ceil((y1 - y0) * scale))
    return draw_map(m, feats, mw, mh, View(x0, y1, scale, 0, 0), TILE), scale


def render_campaign(textmaps: dict[str, str], skill: int = SKILL) -> Image.Image:
    """Episodes in rows of three, the range and the shared legend on the right."""
    cell_w, cell_h = TILE_W + 24, TILE_H + 64
    left = MARGIN + 30
    right_w = max(TILE_W, 2 * COL_W) + 24
    page_w = left + 3 * cell_w + right_w + MARGIN
    page_h = HEADER_H + 3 * cell_h + MARGIN
    img = Image.new("RGB", (page_w, page_h), BG)
    d = ImageDraw.Draw(img)
    text(d, (MARGIN, 18), "Soviet Doom - campaign overview", 26, anchor="la")
    text(d, (MARGIN, 66), f"every map from its TEXTMAP, north up, grid {GRID} units, floors ranked "
                          f"low -> high per map, monsters on skill {skill}", 15, fill=MUTE, anchor="ls")

    def put(name: str, x: int, y: int) -> None:
        if name not in textmaps:
            return
        tile, scale = render_tile(textmaps[name], skill)
        en, _ = map_names(name)
        feats = analyse(parse_textmap(textmaps[name]), skill)
        text(d, (x, y + 4), f"{name}  {en}", 18, anchor="la")
        text(d, (x + TILE_W, y + 8), f"{len(feats.monsters)} monsters, {len(feats.secret_sectors)} secrets, "
                                     f"{scale_label(scale)}", 13, fill=MUTE, anchor="ra")
        tx = x + (TILE_W - tile.width) // 2
        ty = y + 32 + (TILE_H - tile.height) // 2
        img.paste(tile, (tx, ty))
        d.rectangle((tx - 1, ty - 1, tx + tile.width, ty + tile.height), outline=(70, 72, 80))

    for r, (ep, names) in enumerate(EPISODES):
        y = HEADER_H + r * cell_h
        label = Image.new("RGB", (cell_h, 28), BG)
        text(ImageDraw.Draw(label), (cell_h // 2, 14), ep, 18, fill=MUTE, anchor="mm")
        img.paste(label.rotate(90, expand=True), (MARGIN - 6, y))
        for c, name in enumerate(names):
            put(name, left + c * cell_w, y)
    rx = left + 3 * cell_w
    put("RANGE", rx, HEADER_H)
    y = HEADER_H + cell_h + 8
    items = _legend_items(None, None)
    draw_legend(d, items, rx, y, right_w + 20)
    return img


# --------------------------------------------------------------- CLI
def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="PNG", optimize=False)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("maps", nargs="*", help="map lumps to draw (MAP01 ... RANGE)")
    p.add_argument("--all", action="store_true", help="every map plus the campaign sheet")
    p.add_argument("--sheet-only", action="store_true", help="only the campaign sheet")
    p.add_argument("--out-dir", type=Path, default=SHOTS_DIR, help="default: docs/levels/shots/")
    p.add_argument("--src", type=Path, default=SRC_DIR, help="source tree (default: src/)")
    p.add_argument("--textmap", type=Path, help="draw this TEXTMAP file instead of a map script")
    p.add_argument("--out", type=Path, help="output PNG for --textmap")
    p.add_argument("--skill", type=int, default=SKILL, choices=range(1, 6))
    args = p.parse_args(argv)

    if args.textmap:
        out = args.out or args.textmap.with_suffix(".png")
        save_png(render_overview(args.textmap.read_text(encoding="ascii"), args.textmap.stem,
                                 source=args.textmap.as_posix(), skill=args.skill), out)
        print(out)
        return 0

    names = list(MAPS) if (args.all or args.sheet_only) else [n.upper() for n in args.maps]
    if not names:
        p.error("name at least one map, or pass --all")
    textmaps = {n: load_textmap(n, args.src) for n in names}
    if not args.sheet_only:
        for n in names:
            en, ru = map_names(n)
            title = " / ".join(x for x in (en, ru) if x)
            out = args.out_dir / f"{n}-overview.png"
            save_png(render_overview(textmaps[n], n, title, f"src/maps/{n}/map.py", args.skill), out)
            print(out)
    if args.all or args.sheet_only:
        out = args.out_dir / SHEET_NAME
        save_png(render_campaign(textmaps, args.skill), out)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
