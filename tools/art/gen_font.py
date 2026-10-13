#!/usr/bin/env python3
"""Soviet Doom — the mod's own alphabet (debt T9).

Why this exists
---------------
Freedoom's `SmallFont` is ASCII only and GZDoom's Cyrillic glyph pack lives
under `filter/doom.id/`, which an id IWAD selects and Freedoom does not
(verified by listing `game_support.pk3`: `filter/doom.freedoom/` contains a
single decal lump and no fonts at all).  Without an alphabet of our own the
`[ru]` section of `LANGUAGE` cannot be shown, so rule D7 does not exist
inside the game.  `mod-engineer` verified the mechanism: PNG glyphs dropped
into `fonts/defsmallfont/<HEX>.png` inside the PK3 are drawn on top of
Freedoom.  This script draws the glyphs.

Design
------
Glyphs are **data, not images**: each one is a short list of strokes in a
normalised box (x and y in 0..1, y=0 is the baseline, y=1 the cap line).
A `Pen` turns those strokes into hard pixels at a given cap height, stem
weight and style.  Retouching a letter is editing one line; retuning the
whole family is editing one row of `STYLES`.

Three style variants are generated so the CEO can choose by looking:

  A  plakat      condensed poster grotesque, the Impact family of the
                 textures (SDPOSTR2, SDSTAR1).  Narrowest -> most Russian
                 text fits in Doom's 320-pixel line.
  B  kanzelyariya  wider institutional lineal, GOST drawing lettering and
                 enamel door signs.  Most legible, least shouty.
  C  mashina     slab-serif machinery lettering, square corners, slashed
                 zero.  Stencil-crate character, widest.

Two sizes, matching the metrics GZDoom itself uses for Doom:

  small  cap 7 px, line height 9   -> fonts/defsmallfont/  (HUD messages,
                                      pickups, the option menu, console)
  big    cap 11 px + 1 px shadow,
         line height 16            -> fonts/bigfont/       (menu headlines,
                                      level titles, intermission)

Nothing here writes to assets/.  Output goes to work/art/font/ (the H1
serif-fix proposal: work/art/font_fix/ and its sheet in docs/art/previews/;
approved and installed 2026-10-13, see MIRROR_TERMINALS).

Usage
-----
    .venv/bin/python tools/art/gen_font.py             # glyphs + all sheets
    .venv/bin/python tools/art/gen_font.py --sheets    # sheets only
    .venv/bin/python tools/art/gen_font.py --variant A
    .venv/bin/python tools/art/gen_font.py --serif-fix --stamp YYYY-MM-DD_HHMM
                     # H1 proposal: work/art/font_fix/ + docs/art/previews/ sheet
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import artlib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = PROJECT_ROOT / "work" / "art" / "font"
# Where the serif-fix proposal is built.  Never OUT_ROOT: work/art/font/ holds
# the Mac's renders, which tests/test_art.py compares with assets/.
OUT_ROOT_FIX = PROJECT_ROOT / "work" / "art" / "font_fix"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"

# Slab-serif defect of style C (QA finding H1, 2026-10-13).  The slabs are
# placed from Pen.terminals, and mirror() reflected the ink but not the
# terminals, so a mirrored glyph only got the slabs of its left half plus
# whatever its drawing function appended by hand.  M appends the bottom-right
# foot but not the top-right one; W appends a foot at (1.0, 0.0), where no
# stroke of W ends, so a floating foot is drawn there and its top-right slab
# is missing.  Both shipped asymmetric (M = Cyrillic M) at both sizes.
#
# True reflects the terminals in pixel space inside finish() and drops W's
# stray foot; only M, Cyrillic M and W change (6 of 214 files).  The CEO
# approved the proposal sheet `docs/art/previews/*_F2_font-C-serif-fix.png`
# on 2026-10-13 ("apruebo el arreglo de la fuente") and the six glyphs were
# installed in assets/fonts/ the same day, so True is the shipped value.
# False is kept on purpose: it reproduces the historical render of style C
# (work/art/font/C/, the Mac's) byte for byte, which is what the before
# column of the sheet and tests/test_gen_font_fix.py compare against.
MIRROR_TERMINALS = True


# --------------------------------------------------------------- styles
@dataclass(frozen=True)
class Size:
    cap: int                # cap height in pixels (ink)
    stem: int               # stroke weight in pixels
    chamfer: int            # corner cut of round shapes, in pixels
    bearing: int            # empty columns after the ink
    line: int               # FontHeight for font.inf
    shadow: int = 0         # 1 = 1 px drop shadow down-right (adds 1 px)
    slab: int = 0           # slab serif thickness in pixels (style C)


@dataclass(frozen=True)
class Style:
    key: str
    name: str
    blurb: str
    widths_small: dict      # width class -> ink width in px (cap 7)
    widths_big: dict        # width class -> ink width in px (cap 11)
    flat_apex: bool         # A/Л/Д with a flat top (poster) or a point
    slashed_zero: bool
    small: Size
    big: Size


_SMALL = dict(cap=7, chamfer=1, stem=1, bearing=1, line=9)
_BIG = dict(cap=11, chamfer=2, stem=2, bearing=1, line=16, shadow=1)

STYLES = {
    "A": Style(
        key="A", name="Plakat",
        blurb="Condensed poster grotesque — the Impact family of the textures",
        widths_small={"t": 1, "s": 3, "n": 4, "w": 5, "x": 6, "j": 7, "k": 8},
        widths_big={"t": 2, "s": 4, "n": 7, "w": 8, "x": 10, "j": 12, "k": 14},
        flat_apex=True, slashed_zero=False,
        small=Size(**_SMALL), big=Size(**_BIG),
    ),
    "B": Style(
        key="B", name="Kanzelyariya",
        blurb="Institutional lineal — GOST drawing lettering, enamel signs",
        widths_small={"t": 1, "s": 3, "n": 5, "w": 6, "x": 7, "j": 9, "k": 10},
        widths_big={"t": 2, "s": 5, "n": 8, "w": 9, "x": 11, "j": 13, "k": 16},
        flat_apex=False, slashed_zero=False,
        small=Size(**_SMALL),
        big=Size(**_BIG),
    ),
    "C": Style(
        key="C", name="Mashina",
        blurb="Slab machinery — square corners, slab feet, slashed zero",
        widths_small={"t": 1, "s": 3, "n": 5, "w": 6, "x": 7, "j": 9, "k": 10},
        widths_big={"t": 2, "s": 5, "n": 8, "w": 9, "x": 11, "j": 13, "k": 15},
        flat_apex=True, slashed_zero=True,
        small=Size(**{**_SMALL, "chamfer": 0, "slab": 1}),
        big=Size(**{**_BIG, "chamfer": 0, "slab": 2}),
    ),
}


# ------------------------------------------------------------------ pen
class Pen:
    """Draws one glyph on a pixel grid.

    Coordinates are normalised: x 0..1 left to right over the *ink* box,
    y 0..1 from the baseline up to the cap line.  Every stroke lands on the
    pixel grid: horizontals and verticals are written straight into the
    boolean array, diagonals are drawn by Pillow at 1:1 (aliased), so the
    result is the hard Doom staircase and never a grey fringe.

    Rounding is floor(v + 0.5) everywhere, never Python's round(), which
    rounds halves to even and silently shifts the middle stem of Ж, Ш, М.
    """

    def __init__(self, ink_w: int, size: Size, style: Style):
        self.pad = 1 if size.slab else 0          # room for the slab feet
        self.W = ink_w
        self.H = size.cap
        self.stem = size.stem
        self.cham = size.chamfer
        self.size = size
        self.style = style
        self.ink = np.zeros((self.H, self.W), bool)
        self.diag = Image.new("1", (self.W, self.H), 0)
        self.draw = ImageDraw.Draw(self.diag)
        self.terminals: list[tuple[float, float]] = []   # (x, y) for slabs
        self._mirror = False

    # -- coordinate mapping -------------------------------------------
    @staticmethod
    def _r(v: float) -> int:
        return int(math.floor(v + 0.5))

    def body_x(self) -> float:
        """x of the last stem of a letter whose descender tail takes the
        final stem-width of the box (Ц, Щ)."""
        span = self._wi - self.stem
        return (span - self.stem) / span if span else 0.0

    @property
    def _wi(self) -> int:
        return self.W - 2 * self.pad

    def _cx(self, x: float) -> int:
        """Column of an *extent* (an edge of a horizontal bar)."""
        return self.pad + self._r(x * (self._wi - 1))

    def _ry(self, y: float) -> int:
        return self._r((1 - y) * (self.H - 1))

    def _cs(self, x: float) -> int:
        """Left column of a vertical stem aligned at x."""
        return self.pad + self._r(x * (self._wi - self.stem))

    def _rs(self, y: float) -> int:
        """Top row of a horizontal bar aligned at y."""
        return self._r((1 - y) * (self.H - self.stem))

    # -- primitives ----------------------------------------------------
    def v(self, x: float, y0: float = 0.0, y1: float = 1.0, term: bool = True):
        c = self._cs(x)
        r0, r1 = self._ry(y1), self._ry(y0)
        self.ink[r0:r1 + 1, c:c + self.stem] = True
        if term:
            if y0 <= 0.001:
                self.terminals.append((x, 0.0))
            if y1 >= 0.999:
                self.terminals.append((x, 1.0))
        return self

    def h(self, y: float, x0: float = 0.0, x1: float = 1.0):
        r = self._rs(y)
        c0, c1 = self._cx(x0), self._cx(x1)
        self.ink[r:r + self.stem, c0:c1 + 1] = True
        return self

    def d(self, x0: float, y0: float, x1: float, y1: float, term: bool = True):
        """Diagonal stroke between two points, drawn aliased at 1:1."""
        def pt(x, y):
            return (self._cs(x) + (self.stem - 1) // 2,
                    self._rs(y) + (self.stem - 1) // 2)
        a, b = pt(x0, y0), pt(x1, y1)
        self.draw.line([a, b], fill=1, width=self.stem)
        for cc, rr in (a, b):          # square caps, exactly one stem wide
            self.draw.rectangle([cc, rr, cc + self.stem - 1, rr + self.stem - 1],
                                fill=1)
        if term:
            for x, y in ((x0, y0), (x1, y1)):
                if y <= 0.001 or y >= 0.999:
                    self.terminals.append((x, 0.0 if y <= 0.001 else 1.0))
        return self

    def dot(self, x: float, y: float):
        c, r = self._cs(x), self._rs(y)
        self.ink[r:r + self.stem, c:c + self.stem] = True
        return self

    def fill(self, x0: float, x1: float, y0: float, y1: float):
        """Solid block — used where a ring would have no counter left."""
        c0, c1 = self._cx(x0), self._cx(x1)
        r0, r1 = self._ry(y1), self._ry(y0)
        self.ink[r0:r1 + 1, c0:c1 + 1] = True
        return self

    def blob(self, x0: float, x1: float, y0: float, y1: float):
        """A ring if the box can hold a counter, otherwise a solid block."""
        c0, c1 = self._cx(x0), self._cx(x1)
        r0, r1 = self._ry(y1), self._ry(y0)
        if min(c1 - c0 + 1, r1 - r0 + 1) >= 2 * self.stem + 1:
            return self.ring(x0, x1, y0, y1)
        return self.fill(x0, x1, y0, y1)

    def cut_corner(self, corner: str, k: int | None = None):
        """Bevel one corner of the ink box by k pixels (default: the
        style's chamfer).  This is what gives A its poster apex."""
        k = self.cham if k is None else k
        if k <= 0:
            return self
        rr = 0 if corner[0] == "t" else self.H - 1
        cc = self.pad if corner[1] == "l" else self.W - 1 - self.pad
        dr = 1 if corner[0] == "t" else -1
        dc = 1 if corner[1] == "l" else -1
        for i in range(k):
            for j in range(k - i):
                r, c = rr + dr * i, cc + dc * j
                if 0 <= r < self.H and 0 <= c < self.W:
                    self.ink[r, c] = False
        return self

    def cut(self, x0: float, x1: float, y0: float, y1: float):
        """Erase a normalised box (used to open rings: С, Э, G...)."""
        c0, c1 = self._cx(x0), self._cx(x1)
        r0, r1 = self._ry(y1), self._ry(y0)
        self.ink[r0:r1 + 1, c0:c1 + 1] = False
        return self

    def ring(self, x0: float = 0.0, x1: float = 1.0, y0: float = 0.0,
             y1: float = 1.0, corners: str = "tl tr bl br", sides: str = "tblr"):
        """Hollow chamfered box: the workhorse of O С Э В Б Ь Ю Ф 8 ..."""
        c0, c1 = self._cx(x0), self._cx(x1)
        r0, r1 = self._ry(y1), self._ry(y0)      # r0 top, r1 bottom
        s = self.stem
        box = np.zeros_like(self.ink)
        box[r0:r1 + 1, c0:c1 + 1] = True
        inner = np.zeros_like(self.ink)
        if r1 - r0 + 1 > 2 * s and c1 - c0 + 1 > 2 * s:
            inner[r0 + s:r1 + 1 - s, c0 + s:c1 + 1 - s] = True
        shape = box & ~inner
        if "t" not in sides:
            shape[r0:r0 + s, c0 + s:c1 + 1 - s] = False
        if "b" not in sides:
            shape[r1 + 1 - s:r1 + 1, c0 + s:c1 + 1 - s] = False
        if "l" not in sides:
            shape[r0 + s:r1 + 1 - s, c0:c0 + s] = False
        if "r" not in sides:
            shape[r0 + s:r1 + 1 - s, c1 + 1 - s:c1 + 1] = False
        # chamfer: cut the outer corner, fill the matching inner corner so
        # the stroke keeps its weight all the way round.  A small bowl (Ы,
        # Ъ, the counter of 6) has no room for one: shrink it until the
        # ring still has a straight run between two cut corners.
        bw, bh = c1 - c0 + 1, r1 - r0 + 1
        k = max(0, min(self.cham, (min(bw, bh) - 2 * s - 1) // 2 + 1))
        if min(bw, bh) <= 2 * s + 1:
            k = 0
        if k:
            for name, (rr, cc, dr, dc) in {
                "tl": (r0, c0, 1, 1), "tr": (r0, c1, 1, -1),
                "bl": (r1, c0, -1, 1), "br": (r1, c1, -1, -1),
            }.items():
                if name not in corners:
                    continue
                for i in range(k):
                    for j in range(k - i):
                        r, c = rr + dr * i, cc + dc * j
                        if 0 <= r < self.H and 0 <= c < self.W:
                            shape[r, c] = False
                for i in range(max(k - s, 0)):
                    for j in range(max(k - s, 0) - i):
                        r = rr + dr * (s + i)
                        c = cc + dc * (s + j)
                        if 0 <= r < self.H and 0 <= c < self.W:
                            shape[r, c] = True
        self.ink |= shape
        return self

    # -- finish --------------------------------------------------------
    def mirror(self):
        """Mirror the left half onto the right at the end of the glyph."""
        self._mirror = True
        return self

    def finish(self) -> np.ndarray:
        self.ink |= np.asarray(self.diag, dtype=bool)
        if self._mirror:
            self.ink |= self.ink[:, ::-1]
        if self.size.slab:
            self._slabs()
        return self.ink

    def _terminal_columns(self) -> list[tuple[int, float]]:
        """(left column of the stem, y) of every stroke end that takes a slab.
        With MIRROR_TERMINALS a mirrored glyph also gets the reflection of
        each one, computed in pixels (W - c - stem) so it lands exactly on
        the reflected ink; reflecting x in normalised space would be off by
        one wherever the half-up rounding meets an exact half."""
        cols = [(self._cs(x), y) for x, y in self.terminals]
        if self._mirror and MIRROR_TERMINALS:
            cols += [(self.W - c - self.stem, y) for c, y in cols]
        return cols

    def _slabs(self):
        t = self.size.slab
        ov = self.pad
        # "Already a bar there" is judged on the drawing.  With the fix on, a
        # mirrored glyph judges it on the ink as it was before any slab: a
        # slab just laid on the left must not veto its twin on the right
        # (the two feet of a small W are one pixel apart).
        probe = self.ink.copy() if (self._mirror and MIRROR_TERMINALS) else self.ink
        for c, y in self._terminal_columns():
            row = self.H - 1 if y <= 0.001 else 0
            if self._run_width(row, c, probe) > self.stem:
                continue                 # already a bar there: no serif
            c0, c1 = max(c - ov, 0), min(c + self.stem - 1 + ov, self.W - 1)
            if y <= 0.001:
                self.ink[self.H - t:self.H, c0:c1 + 1] = True
            else:
                self.ink[0:t, c0:c1 + 1] = True

    def _run_width(self, row: int, col: int, ink: np.ndarray | None = None) -> int:
        """Width of the contiguous ink run through (row, col), measured on
        `ink` (default: the glyph as drawn so far)."""
        line = (self.ink if ink is None else ink)[row]
        if not line[col]:
            return 0
        a = b = col
        while a > 0 and line[a - 1]:
            a -= 1
        while b < self.W - 1 and line[b + 1]:
            b += 1
        return b - a + 1


# --------------------------------------------------------------- glyphs
# Every entry: codepoint -> (width class, drawing function).
# Width classes: t tiny, s narrow, n normal, w wide, x extra wide.
GLYPHS: dict[int, tuple[str, object, bool]] = {}


def glyph(ch: str, cls: str = "n", center: bool = False):
    """`center=True` for a letter with a stem or an apex on the middle axis
    (Т Ф Ж Ш Щ М У A V W): its ink width is nudged by one pixel when the
    parity would otherwise push that middle stem off axis."""
    def deco(fn):
        GLYPHS[ord(ch)] = (cls, fn, center)
        return fn
    return deco


def alias(src: str, *dsts: str):
    entry = GLYPHS[ord(src)]
    for d in dsts:
        GLYPHS[ord(d)] = entry


# ---- Latin capitals -------------------------------------------------
@glyph("A", center=True)
def _a(p: Pen):
    if p.style.flat_apex:
        p.v(0).v(1).h(1)
        p.cut_corner("tl").cut_corner("tr")
    else:
        p.d(0, 0, 0.5, 1).mirror()
        p.terminals.append((1.0, 0.0))
    p.h(0.30)


@glyph("B")
def _b(p: Pen):
    p.v(0).ring(0, 1, 0.50, 1, corners="tr br").ring(0, 1, 0, 0.52, corners="tr br")


@glyph("C")
def _c(p: Pen):
    p.ring().cut(0.62, 1.0, 0.28, 0.72)


@glyph("D")
def _d(p: Pen):
    p.ring(corners="tr br")


@glyph("E")
def _e(p: Pen):
    p.v(0).h(1).h(0.50, 0, 0.88).h(0)


@glyph("F")
def _f(p: Pen):
    p.v(0).h(1).h(0.50, 0, 0.88)


@glyph("G")
def _g(p: Pen):
    p.ring().cut(0.62, 1.0, 0.30, 0.66).h(0.42, 0.45, 1.0)


@glyph("H")
def _h(p: Pen):
    p.v(0).v(1).h(0.50)


@glyph("I", "s")
def _i(p: Pen):
    p.v(0.5)


@glyph("J", "s")
def _j(p: Pen):
    p.v(1, 0.22, 1).ring(0, 1, 0, 0.35, corners="bl br", sides="bl")


@glyph("K")
def _k(p: Pen):
    p.v(0).d(1, 1, 0.12, 0.48, term=False).d(0.12, 0.48, 1, 0)


@glyph("L")
def _l(p: Pen):
    p.v(0).h(0)


@glyph("M", "w", center=True)
def _m(p: Pen):
    p.v(0).d(0, 1, 0.5, 0.32, term=False).mirror()
    p.terminals.append((1.0, 0.0))


@glyph("N")
def _n(p: Pen):
    p.v(0).v(1).d(0, 1, 1, 0, term=False)


@glyph("O")
def _o(p: Pen):
    p.ring()


@glyph("P")
def _p(p: Pen):
    p.v(0).ring(0, 1, 0.45, 1, corners="tr br")


@glyph("Q")
def _q(p: Pen):
    p.ring().d(0.55, 0.32, 1.0, 0.0)


@glyph("R")
def _r(p: Pen):
    p.v(0).ring(0, 1, 0.45, 1, corners="tr br").d(0.45, 0.45, 1, 0)


@glyph("S")
def _s(p: Pen):
    p.ring(0, 1, 0.50, 1, corners="tl tr", sides="tl")
    p.ring(0, 1, 0, 0.52, corners="bl br", sides="br")
    p.h(0.50)


@glyph("T", center=True)
def _t(p: Pen):
    p.h(1).v(0.5, 0, 1)


@glyph("U")
def _u(p: Pen):
    p.v(0, 0.28, 1).v(1, 0.28, 1).ring(0, 1, 0, 0.45, corners="bl br", sides="blr")


@glyph("V", center=True)
def _v(p: Pen):
    p.d(0, 1, 0.5, 0).mirror()
    p.terminals.append((1.0, 1.0))


@glyph("W", "j", center=True)
def _w(p: Pen):
    p.d(0, 1, 0.33, 0).d(0.33, 0, 0.5, 0.75, term=False).mirror()
    if not MIRROR_TERMINALS:
        # The H1 defect: no stroke of W ends at (1.0, 0.0).  Not shipped since
        # 2026-10-13; kept so MIRROR_TERMINALS = False still reproduces the
        # historical render of style C (the "before" of the fix) exactly.
        p.terminals.append((1.0, 0.0))


@glyph("X", center=True)
def _x(p: Pen):
    p.d(0, 1, 0.5, 0.5, term=False).d(0, 0, 0.5, 0.5, term=False).mirror()
    p.terminals += [(0.0, 1.0), (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)]


@glyph("Y", center=True)
def _y(p: Pen):
    p.d(0, 1, 0.5, 0.45, term=False).v(0.5, 0, 0.5, term=False).mirror()
    p.terminals += [(0.0, 1.0), (1.0, 1.0), (0.5, 0.0)]


@glyph("Z")
def _z(p: Pen):
    p.h(1).h(0).d(1, 1, 0, 0, term=False)


# ---- digits ----------------------------------------------------------
@glyph("0")
def _d0(p: Pen):
    p.ring()
    if p.style.slashed_zero:
        p.d(0.2, 0.25, 0.8, 0.75, term=False)


@glyph("1", "s")
def _d1(p: Pen):
    p.v(0.6, 0, 1).d(0.6, 1.0, 0.0, 0.76, term=False)
    if p.size.slab:
        p.h(0)


@glyph("2")
def _d2(p: Pen):
    p.ring(0, 1, 0.48, 1, corners="tl tr", sides="tlr")
    p.h(0).d(1, 0.50, 0.0, 0.05, term=False)


@glyph("3")
def _d3(p: Pen):
    p.ring(0, 1, 0.50, 1, corners="tl tr", sides="tr")
    p.ring(0, 1, 0, 0.52, corners="bl br", sides="br")
    p.h(1, 0.1, 0.9).h(0, 0.1, 0.9).h(0.50, 0.3, 1)


@glyph("4")
def _d4(p: Pen):
    p.d(0.78, 1, 0.0, 0.28, term=False).h(0.28).v(0.78, 0, 1)


@glyph("5")
def _d5(p: Pen):
    p.h(1).v(0, 0.48, 1).h(0.50, 0, 0.8)
    p.ring(0, 1, 0, 0.52, corners="bl br tr", sides="rb")
    p.h(0, 0.1, 0.9)


@glyph("6")
def _d6(p: Pen):
    p.ring(0, 1, 0, 0.55, corners="bl br tr")
    p.v(0, 0.5, 0.82, term=False)
    p.d(0.0, 0.82, 0.8, 1.0, term=False)


@glyph("7")
def _d7(p: Pen):
    p.h(1).d(1, 0.92, 0.22, 0, term=False)


@glyph("8")
def _d8(p: Pen):
    p.ring(0, 1, 0.50, 1).ring(0, 1, 0, 0.52)


@glyph("9")
def _d9(p: Pen):
    p.ring(0, 1, 0.45, 1)
    p.v(1, 0.18, 0.5, term=False)
    p.d(1.0, 0.18, 0.2, 0.0, term=False)


# ---- punctuation and symbols ----------------------------------------
@glyph(" ", "s")
def _space(p: Pen):
    pass


@glyph("!", "t")
def _excl(p: Pen):
    p.v(0.5, 0.30, 1).dot(0.5, 0)


@glyph('"', "s")
def _quot(p: Pen):
    p.v(0, 0.70, 1, term=False).v(1, 0.70, 1, term=False)


@glyph("#")
def _hash(p: Pen):
    p.v(0.25, 0.05, 0.95, term=False).v(0.75, 0.05, 0.95, term=False)
    p.h(0.62).h(0.30)


@glyph("$")
def _dollar(p: Pen):
    _s(p)
    p.v(0.5, 0, 1, term=False)


@glyph("%", "w")
def _pct(p: Pen):
    p.blob(0, 0.3, 0.78, 1).blob(0.7, 1, 0, 0.22)
    p.d(1.0, 1.0, 0.0, 0.0, term=False)


@glyph("&")
def _amp(p: Pen):
    p.ring(0, 0.8, 0.52, 1).v(0, 0.15, 0.6, term=False)
    p.h(0, 0.15, 0.7).d(0.75, 0.5, 1, 0, term=False).d(0, 0.2, 0.8, 0.95, term=False)


@glyph("'", "t")
def _apos(p: Pen):
    p.v(0.5, 0.70, 1, term=False)


@glyph("(", "s")
def _lpar(p: Pen):
    p.ring(0, 1, 0, 1, sides="tbl").cut(0.45, 1.0, -0.1, 1.1)
    p.v(0, 0.12, 0.88, term=False)


@glyph(")", "s")
def _rpar(p: Pen):
    p.ring(0, 1, 0, 1, sides="tbr").cut(-0.1, 0.55, -0.1, 1.1)
    p.v(1, 0.12, 0.88, term=False)


@glyph("*", "s", center=True)
def _star(p: Pen):
    p.v(0.5, 0.45, 1, term=False).d(0, 0.55, 1, 0.95, term=False)
    p.d(0, 0.95, 1, 0.55, term=False)


@glyph("+", center=True)
def _plus(p: Pen):
    p.h(0.45, 0.1, 0.9).v(0.5, 0.18, 0.78, term=False)


@glyph(",", "t")
def _comma(p: Pen):
    p.dot(0.5, 0.18).v(0.5, 0, 0.2, term=False)


@glyph("-", "s")
def _minus(p: Pen):
    p.h(0.45, 0.05, 0.95)


@glyph(".", "t")
def _period(p: Pen):
    p.dot(0.5, 0)


@glyph("/", "s")
def _slash(p: Pen):
    p.d(0, 0, 1, 1, term=False)


@glyph(":", "t")
def _colon(p: Pen):
    p.dot(0.5, 0).dot(0.5, 0.55)


@glyph(";", "t")
def _semi(p: Pen):
    p.dot(0.5, 0.18).v(0.5, 0, 0.2, term=False).dot(0.5, 0.62)


@glyph("<", "s")
def _lt(p: Pen):
    p.d(1, 0.9, 0, 0.45, term=False).d(0, 0.45, 1, 0.0, term=False)


@glyph("=")
def _eq(p: Pen):
    p.h(0.62, 0.05, 0.95).h(0.26, 0.05, 0.95)


@glyph(">", "s")
def _gt(p: Pen):
    p.d(0, 0.9, 1, 0.45, term=False).d(1, 0.45, 0, 0.0, term=False)


@glyph("?")
def _quest(p: Pen):
    p.ring(0, 1, 0.70, 1, corners="tl tr", sides="tlr")
    p.d(1.0, 0.70, 0.5, 0.45, term=False)
    p.v(0.5, 0.3, 0.45, term=False).dot(0.5, 0)


@glyph("@", "j")
def _at(p: Pen):
    p.ring().ring(0.28, 0.75, 0.25, 0.70).cut(0.5, 1.0, 0.0, 0.22)


@glyph("[", "s")
def _lbr(p: Pen):
    p.v(0).h(1, 0, 0.9).h(0, 0, 0.9)


@glyph("\\", "s")
def _bslash(p: Pen):
    p.d(0, 1, 1, 0, term=False)


@glyph("]", "s")
def _rbr(p: Pen):
    p.v(1).h(1, 0.1, 1).h(0, 0.1, 1)


@glyph("^", "s")
def _caret(p: Pen):
    p.d(0, 0.6, 0.5, 1, term=False).d(1, 0.6, 0.5, 1, term=False)


@glyph("_", "s")
def _under(p: Pen):
    p.h(0)


@glyph("`", "t")
def _grave(p: Pen):
    p.d(0, 1, 1, 0.7, term=False)


@glyph("«", "w")
def _laquo(p: Pen):
    p.d(0.35, 0.67, 0.0, 0.5, term=False).d(0.0, 0.5, 0.35, 0.33, term=False)
    p.d(1.0, 0.67, 0.65, 0.5, term=False).d(0.65, 0.5, 1.0, 0.33, term=False)


@glyph("»", "w")
def _raquo(p: Pen):
    p.d(0.0, 0.67, 0.35, 0.5, term=False).d(0.35, 0.5, 0.0, 0.33, term=False)
    p.d(0.65, 0.67, 1.0, 0.5, term=False).d(1.0, 0.5, 0.65, 0.33, term=False)


@glyph("×", "s")
def _times(p: Pen):
    p.d(0.0, 0.62, 1.0, 0.30, term=False).d(0.0, 0.30, 1.0, 0.62, term=False)


@glyph("·", "t")
def _middot(p: Pen):
    p.dot(0.5, 0.45)


@glyph("№", "k")
def _numero(p: Pen):
    # N
    p.v(0.0, 0.18, 1).v(0.42, 0.18, 1).d(0.0, 1, 0.42, 0.18, term=False)
    # the raised o over its rule
    p.blob(0.58, 1.0, 0.52, 1.0).h(0.0, 0.58, 1.0)


@glyph("—", "w")
def _emdash(p: Pen):
    p.h(0.45, 0, 1)


@glyph("–", "s")
def _endash(p: Pen):
    p.h(0.45, 0, 1)


@glyph("…", "w", center=True)
def _ellipsis(p: Pen):
    p.dot(0, 0).dot(0.5, 0).dot(1, 0)


@glyph("°", "s")
def _degree(p: Pen):
    p.ring(0, 1, 0.55, 1)


# ---- Cyrillic capitals ----------------------------------------------
alias("A", "А")
alias("B", "В")
alias("E", "Е")
alias("K", "К")
alias("M", "М")
alias("H", "Н")
alias("O", "О")
alias("P", "Р")
alias("C", "С")
alias("T", "Т")
alias("X", "Х")


@glyph("Б")
def _cyr_be(p: Pen):
    p.v(0).h(1).ring(0, 1, 0, 0.52, corners="tr br")


@glyph("Г")
def _cyr_ghe(p: Pen):
    p.v(0).h(1)


@glyph("Д", "x")
def _cyr_de(p: Pen):
    p.h(0.18, 0, 1)                                  # the plinth
    p.v(0.80, 0.18, 1, term=False).h(1, 0.33, 0.80)  # roof and right leg
    p.d(0.12, 0.18, 0.36, 1.0, term=False)           # the splayed left leg
    p.v(0.0, 0, 0.18).v(1.0, 0, 0.18)                # the two feet


@glyph("Ж", "j", center=True)
def _cyr_zhe(p: Pen):
    p.v(0.5, 0, 1)
    p.d(0, 1, 0.5, 0.5, term=False).d(0, 0, 0.5, 0.5, term=False).mirror()
    p.terminals += [(0.0, 1.0), (0.0, 0.0), (1.0, 1.0), (1.0, 0.0)]


@glyph("З")
def _cyr_ze(p: Pen):
    p.ring(0, 1, 0.48, 1, corners="tl tr", sides="tr")
    p.ring(0, 1, 0, 0.52, corners="bl br", sides="br")
    p.h(0.50, 0.3, 1)


@glyph("И")
def _cyr_i(p: Pen):
    p.v(0).v(1).d(0, 0, 1, 1, term=False)


@glyph("Й")
def _cyr_short_i(p: Pen):
    p.v(0, 0, 0.78).v(1, 0, 0.78).d(0, 0, 1, 0.78, term=False)
    p.h(1, 0.25, 0.75)


@glyph("Л")
def _cyr_el(p: Pen):
    p.v(1, 0, 1).h(1, 0.28, 1)
    p.d(0.0, 0.0, 0.30, 1.0, term=False)
    p.terminals.append((0.0, 0.0))


@glyph("П")
def _cyr_pe(p: Pen):
    p.v(0).v(1).h(1)


@glyph("У", center=True)
def _cyr_u(p: Pen):
    p.d(0, 1, 0.55, 0.42, term=False).d(1, 1, 0.12, 0.0, term=False)
    p.terminals += [(0.0, 1.0), (1.0, 1.0)]


@glyph("Ф", "x", center=True)
def _cyr_ef(p: Pen):
    p.v(0.5, 0, 1).ring(0, 1, 0.18, 0.84)


@glyph("Ц", "w")
def _cyr_tse(p: Pen):
    b = p.body_x()
    p.v(0, 0.18, 1).v(b, 0.18, 1).h(0.18, 0, b).v(1, 0, 0.22)


@glyph("Ч")
def _cyr_che(p: Pen):
    p.v(1, 0, 1).v(0, 0.48, 1).h(0.48, 0, 1)


@glyph("Ш", "j", center=True)
def _cyr_sha(p: Pen):
    p.v(0).v(0.5).v(1).h(0)


@glyph("Щ", "k")
def _cyr_shcha(p: Pen):
    b = p.body_x()                  # body; the last stem-width is the tail
    p.v(0, 0.18, 1).v(b / 2, 0.18, 1).v(b, 0.18, 1)
    p.h(0.18, 0, b).v(1, 0, 0.22)


@glyph("Ъ", "x")
def _cyr_hard(p: Pen):
    p.h(1, 0, 0.3).v(0.3, 0, 1).ring(0.3, 1, 0, 0.52, corners="tr br")


@glyph("Ы", "x")
def _cyr_yeru(p: Pen):
    p.v(0).ring(0, 0.62, 0, 0.52, corners="tr br").v(1)


@glyph("Ь")
def _cyr_soft(p: Pen):
    p.v(0).ring(0, 1, 0, 0.52, corners="tr br")


@glyph("Э")
def _cyr_e(p: Pen):
    p.ring().cut(0.0, 0.38, 0.28, 0.72).h(0.48, 0.35, 0.82)


@glyph("Ю", "j")
def _cyr_yu(p: Pen):
    p.v(0).h(0.48, 0, 0.35).ring(0.28, 1, 0, 1)


@glyph("Я")
def _cyr_ya(p: Pen):
    p.v(1, 0, 1).ring(0, 1, 0.48, 1, corners="tl bl").h(0.48, 0, 1)
    p.d(0.85, 0.48, 0.0, 0.0, term=False)
    p.terminals.append((0.0, 0.0))


@glyph("Ё")
def _cyr_io(p: Pen):
    p.v(0, 0, 0.78).h(0.78).h(0.38, 0, 0.88).h(0)
    p.dot(0.25, 1.0).dot(0.9, 1.0)


# ------------------------------------------------------- font building
CYRILLIC = [chr(c) for c in range(0x0410, 0x0430)] + ["Ё"]
LATIN = [chr(c) for c in range(0x41, 0x5B)]
DIGITS = [chr(c) for c in range(0x30, 0x3A)]
PUNCT = list("!\"#$%&'()*+,-./:;<=>?@[\\]^_`") + ["«", "»", "×", "·", "№",
                                                 "—", "–", "…", "°"]


def ink_width(style: Style, size_key: str, cls: str, center: bool = False) -> int:
    table = style.widths_small if size_key == "small" else style.widths_big
    size = style.small if size_key == "small" else style.big
    w = max(table[cls], size.stem)
    if center and (w - size.stem) % 2:
        w += 1
    return w + 2 * (1 if size.slab else 0)


def render_glyph(ch: str, style: Style, size_key: str) -> tuple[np.ndarray, int]:
    """Returns (bool ink array of shape (cap, ink_w), advance in px)."""
    cls, fn, center = GLYPHS[ord(ch)]
    size = style.small if size_key == "small" else style.big
    w = ink_width(style, size_key, cls, center)
    pen = Pen(w, size, style)
    fn(pen)
    ink = pen.finish()
    return ink, w + size.bearing


# Colours: the small font is flat (Doom's is too, and 7 px leaves no room
# for a bevel); the big font gets a 1 px drop shadow so a menu headline
# holds over a texture.
def colours(style: Style):
    body_small = artlib.ramp_colour("cream_yellow", 0.90)
    body_big = artlib.ramp_colour("flag_red", 0.80)
    shadow = artlib.ramp_colour("concrete_cold", 0.04)
    return body_small, body_big, shadow


def glyph_image(ch: str, style: Style, size_key: str) -> Image.Image:
    ink, advance = render_glyph(ch, style, size_key)
    size = style.small if size_key == "small" else style.big
    body_s, body_b, shadow = colours(style)
    body = body_s if size_key == "small" else body_b
    h, w = ink.shape
    out_h, out_w = h + size.shadow, w + size.shadow
    rgba = np.zeros((out_h, out_w, 4), np.uint8)
    if size.shadow:
        sh = np.zeros((out_h, out_w), bool)
        sh[size.shadow:, size.shadow:] = ink
        sh &= ~np.pad(ink, ((0, size.shadow), (0, size.shadow)))
        rgba[sh] = (*shadow, 255)
    m = np.pad(ink, ((0, size.shadow), (0, size.shadow)))
    rgba[m] = (*body, 255)
    img = Image.fromarray(rgba, "RGBA")
    # pad to the advance width so the folder font spaces correctly
    canvas = Image.new("RGBA", (advance + size.shadow, out_h), (0, 0, 0, 0))
    canvas.paste(img, (0, 0))
    return canvas


def build_variant(style: Style, out_dir: Path) -> dict:
    report = {"variant": style.key, "name": style.name, "sizes": {}}
    for size_key, folder in (("small", "defsmallfont"), ("big", "bigfont")):
        size = style.small if size_key == "small" else style.big
        d = out_dir / style.key / folder
        d.mkdir(parents=True, exist_ok=True)
        n = 0
        widths = {}
        for ch in CYRILLIC + LATIN + DIGITS + PUNCT + [" "]:
            img = glyph_image(ch, style, size_key)
            img.save(d / f"{ord(ch):04X}.png")
            widths[f"U+{ord(ch):04X}"] = img.width
            n += 1
        # LF on every machine: Windows' default newline would write CRLF (H3)
        (d / "font.inf").write_text(f"FontHeight {size.line}\n", encoding="utf-8", newline="\n")
        report["sizes"][size_key] = {
            "folder": f"fonts/{folder}/",
            "glyphs": n,
            "cap_height": size.cap,
            "image_height": size.cap + size.shadow,
            "font_height": size.line,
            "stem": size.stem,
            "widths": widths,
        }
    return report


# ------------------------------------------------------------- text set
class RenderFont:
    """A built variant/size, ready to compose lines of text."""

    def __init__(self, style: Style, size_key: str):
        self.style = style
        self.size_key = size_key
        self.size = style.small if size_key == "small" else style.big
        self.cache: dict[str, Image.Image] = {}
        self.missing: set[str] = set()

    def glyph(self, ch: str) -> Image.Image | None:
        ch = ch.upper()
        if ch not in self.cache:
            if ord(ch) not in GLYPHS:
                self.missing.add(ch)
                return None
            self.cache[ch] = glyph_image(ch, self.style, self.size_key)
        return self.cache[ch]

    @property
    def height(self) -> int:
        return self.size.cap + self.size.shadow

    def width(self, text: str) -> int:
        return sum((g.width for g in (self.glyph(c) for c in text) if g), 0)

    def render(self, text: str) -> Image.Image:
        w = max(self.width(text), 1)
        img = Image.new("RGBA", (w, self.height), (0, 0, 0, 0))
        x = 0
        for c in text:
            g = self.glyph(c)
            if g is None:
                continue
            img.alpha_composite(g, (x, 0))
            x += g.width
        return img


# ----------------------------------------------------------- the sheets
BG = artlib.ramp_colour("concrete_cold", 0.12)
PANEL = artlib.ramp_colour("concrete_cold", 0.20)
WALL = artlib.ramp_colour("concrete_cold", 0.58)     # a lit wall, for contrast
LABEL = artlib.ramp_colour("concrete_cold", 0.78)
ACCENT = artlib.ramp_colour("flag_red", 0.78)
GOLD = artlib.ramp_colour("hazard_yellow", 0.80)

LABEL_FONT = ImageFont.truetype(artlib.FONT_SMALL, 15)
LABEL_SMALL = ImageFont.truetype(artlib.FONT_SMALL, 12)
TITLE_FONT = ImageFont.truetype(artlib.FONT_POSTER, 30)
SUB_FONT = ImageFont.truetype(artlib.FONT_POSTER, 19)

SCREEN_W = 320        # Doom's virtual screen width: a message must fit here

PHRASES = [
    # (kind, size, russian, english)
    ("Pickup line (HUD message)", "small",
     "ЯЩИК ВЫСТРЕЛОВ ПГ-7В.", "A CRATE OF PG-7V ROUNDS."),
    ("Pickup line, the long one", "small",
     "ВЫ ПОДОБРАЛИ РУЧНУЮ «КАТЮШУ». ОПЫТНЫЙ ОБРАЗЕЦ. НЕ РОНЯТЬ.",
     "YOU GOT THE HAND KATYUSHA. PROTOTYPE. DO NOT DROP IT."),
    ("Ammo pool name", "small",
     "ПАТРОНЫ 7,62×25 · 12 КАЛ. · 50 %", "7.62×25 ROUNDS · 12 GAUGE · 50 %"),
    ("Weapon tag / bunker sign", "small",
     "ОГНЕМЁТ РОКС-3 · ОБЪЕКТ № 7", "ROKS-3 FLAMETHROWER · SITE № 7"),
    ("Difficulty entry (the longest menu line)", "small",
     "ГЕРОЙ СОВЕТСКОГО СОЮЗА, ПОСМЕРТНО",
     "HERO OF THE SOVIET UNION, POSTHUMOUSLY"),
    ("Menu entry", "big", "НОВАЯ ИГРА", "NEW GAME"),
    ("Level title", "big", "ПОЛИГОН", "TEST RANGE"),
    ("Headline (both scripts in one line)", "big",
     "СОВЕТСКИЙ DOOM", "SOVIET DOOM"),
]


def scaled(img: Image.Image, k: int) -> Image.Image:
    return img.resize((img.width * k, img.height * k), Image.Resampling.NEAREST)


def new_sheet(w: int, h: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (w, h), BG)
    return img, ImageDraw.Draw(img)


def sheet_variant(style: Style, stamp: str) -> Path:
    small = RenderFont(style, "small")
    big = RenderFont(style, "big")
    W = 1500
    img, d = new_sheet(W, 2400)

    d.rectangle([0, 0, W, 86], fill=PANEL)
    d.rectangle([0, 84, W, 86], fill=ACCENT)
    d.text((28, 16), f"SOVIET DOOM · ALPHABET · VARIANT {style.key} — {style.name.upper()}",
           font=TITLE_FONT, fill=GOLD)
    d.text((30, 56), style.blurb, font=LABEL_FONT, fill=LABEL)
    d.text((W - 300, 60), stamp, font=LABEL_SMALL, fill=LABEL)

    y = 112
    x = 28

    rows_big = [list("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"),
                list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
                list("0123456789 .,:;!?-—«»()№×·%+=/")]
    rows_small = rows_big

    d.text((x, y), "BIG FONT — menu headlines, level titles  ·  cap 11 px + 1 px shadow, line 16  ·  fonts/bigfont/",
           font=LABEL_FONT, fill=GOLD)
    y += 24
    for row in rows_big:
        line = big.render("".join(row))
        img.paste(line, (x, y), line)
        z = scaled(line, 3)
        img.paste(z, (x, y + line.height + 8), z)
        y += line.height + 8 + z.height + 18

    y += 10
    d.text((x, y), "SMALL FONT — HUD messages, pickups, option menu  ·  cap 7 px, line 9  ·  fonts/defsmallfont/",
           font=LABEL_FONT, fill=GOLD)
    y += 24
    for row in rows_small:
        line = small.render("".join(row))
        img.paste(line, (x, y), line)
        z = scaled(line, 4)
        img.paste(z, (x, y + line.height + 8), z)
        y += line.height + 8 + z.height + 18

    # ---- real phrases, at the size they will be on screen
    y += 14
    d.rectangle([x, y, W - 28, y + 2], fill=ACCENT)
    y += 14
    d.text((x, y), "REAL STRINGS FROM LANGUAGE — 1× is exactly what the engine draws; "
                   "4× is how it looks on a 1080p screen", font=LABEL_FONT, fill=GOLD)
    y += 26
    d.text((x, y), f"the box is Doom's 320-pixel line: a message wider than the box wraps",
           font=LABEL_SMALL, fill=LABEL)
    y += 20

    for kind, size_key, ru, en in PHRASES:
        font = small if size_key == "small" else big
        d.text((x, y), f"{kind}  ·  {size_key} font", font=LABEL_SMALL, fill=LABEL)
        y += 16
        for text in (ru, en):
            line = font.render(text)
            box_h = line.height + 4
            d.rectangle([x, y, x + SCREEN_W + 2, y + box_h],
                        outline=artlib.ramp_colour("concrete_cold", 0.32))
            img.paste(line, (x + 2, y + 2), line)
            over = line.width - SCREEN_W
            z = scaled(line, 4)
            img.paste(z, (x + SCREEN_W + 30, y + 2 - (z.height - line.height) // 2
                          if z.height < 40 else y), z)
            d.text((x + SCREEN_W + 30 + z.width + 14, y + 2),
                   f"{line.width} px" + ("  ← OVER 320" if over > 0 else ""),
                   font=LABEL_SMALL, fill=ACCENT if over > 0 else LABEL)
            y += max(box_h, z.height) + 8
        y += 10

    # ---- legibility strip: same line over a lit concrete wall
    d.rectangle([x, y, W - 28, y + 2], fill=ACCENT)
    y += 14
    d.text((x, y), "LEGIBILITY — the same line over a lit wall (sector light 144) and over the dark",
           font=LABEL_FONT, fill=GOLD)
    y += 24
    for bgc, name in ((WALL, "wall 0.58"), (artlib.ramp_colour("military_green", 0.45), "steel door"),
                      (ACCENT, "poster red")):
        line = small.render("ВЫ ПОДОБРАЛИ ТТ-33 ТОКАРЕВА!  ·  YOU GOT THE TT-33 TOKAREV!")
        z = scaled(line, 3)
        d.rectangle([x, y, x + z.width + 16, y + z.height + 10], fill=bgc)
        img.paste(z, (x + 8, y + 5), z)
        d.text((x + z.width + 28, y + 6), name, font=LABEL_SMALL, fill=LABEL)
        y += z.height + 18

    y += 20
    missing = sorted(small.missing | big.missing)
    d.text((x, y), f"glyphs drawn: {len(GLYPHS)} codepoints per size  ·  "
                   f"missing in these strings: {missing if missing else 'none'}",
           font=LABEL_SMALL, fill=LABEL)
    y += 30

    img = img.crop((0, 0, W, min(y, img.height)))
    path = OUT_ROOT / f"{stamp}_F2_font-{style.key}-{style.name.lower()}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def sheet_compare(stamp: str) -> Path:
    W = 1500
    img, d = new_sheet(W, 2000)
    d.rectangle([0, 0, W, 86], fill=PANEL)
    d.rectangle([0, 84, W, 86], fill=ACCENT)
    d.text((28, 16), "SOVIET DOOM · ALPHABET · THE THREE VARIANTS HEAD TO HEAD",
           font=TITLE_FONT, fill=GOLD)
    d.text((30, 56), "same strings, same scale — pick one; mixing is allowed "
                     "(e.g. A for headlines, B for messages)",
           font=LABEL_FONT, fill=LABEL)
    d.text((W - 300, 60), stamp, font=LABEL_SMALL, fill=LABEL)
    y = 110
    x = 28

    for kind, size_key, ru, en in PHRASES:
        d.text((x, y), f"{kind.upper()}  ·  {size_key} font", font=LABEL_FONT, fill=GOLD)
        y += 22
        for key in ("A", "B", "C"):
            st = STYLES[key]
            f = RenderFont(st, size_key)
            d.text((x, y + 6), f"{key} {st.name}", font=LABEL_SMALL, fill=LABEL)
            xx = x + 130
            for text in (ru, en):
                line = f.render(text)
                k = 3 if size_key == "small" else 2
                z = scaled(line, k)
                img.paste(z, (xx, y), z)
                xx += z.width + 40
            y += max(f.height * (3 if size_key == "small" else 2), 20) + 12
        y += 18

    img = img.crop((0, 0, W, min(y + 20, img.height)))
    path = OUT_ROOT / f"{stamp}_F2_font-compare.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path



# ------------------------------------------------- the H1 serif-fix proposal
SERIF_FIX_GLYPHS = ["M", "М", "W"]          # the only glyphs the fix changes
SERIF_FIX_WORDS = [
    # (where the string lives in src/lumps/LANGUAGE, the string)
    ("SD_MAP01_NAME [ru], level title", "Космодром «Заря-7»"),
    ("SD_TAG_ROKS3 [enu], weapon tag", "ROKS-3 flamethrower"),
    ("SD_SKILL_2 [enu], skill menu", "I have seen worse winters"),
]
FIX_ZOOM = {"small": 10, "big": 8}        # glyph close-ups
FIX_WORD_ZOOM = {"small": 4, "big": 3}    # word close-ups


class mirror_terminals:
    """`with mirror_terminals(True):` renders with the H1 fix on, then puts
    the module switch back.  Used by the proposal; the shipped value is the
    module constant MIRROR_TERMINALS."""

    def __init__(self, on: bool):
        self.on = on

    def __enter__(self):
        global MIRROR_TERMINALS
        self.saved, MIRROR_TERMINALS = MIRROR_TERMINALS, self.on
        return self

    def __exit__(self, *exc):
        global MIRROR_TERMINALS
        MIRROR_TERMINALS = self.saved
        return False


def build_serif_fix(out_root: Path | None = None) -> dict:
    """Variant C with the H1 fix on, into work/art/font_fix/C/ (never into
    work/art/font/, the Mac's renders)."""
    out_root = OUT_ROOT_FIX if out_root is None else out_root
    out_root.mkdir(parents=True, exist_ok=True)
    with mirror_terminals(True):
        report = build_variant(STYLES["C"], out_root)
    manifest = {"proposal": "H1 slab-serif fix", "MIRROR_TERMINALS": True,
                "codepoints": len(GLYPHS), "variants": [report]}
    (out_root / "manifest.json").write_text(json.dumps(manifest, indent=1),
                                            encoding="utf-8", newline="\n")
    return report


def _gridded(img: Image.Image, k: int) -> Image.Image:
    """Nearest-neighbour close-up over a dark board, with a 1 px pixel grid."""
    z = scaled(img, k)
    board = Image.new("RGB", z.size, BG)
    board.paste(z, (0, 0), z)
    d = ImageDraw.Draw(board)
    grid = artlib.ramp_colour("concrete_cold", 0.22)
    for x in range(0, z.width, k):
        d.line([(x, 0), (x, z.height)], fill=grid)
    for y in range(0, z.height, k):
        d.line([(0, y), (z.width, y)], fill=grid)
    return board


def _diff(before: Image.Image, after: Image.Image, k: int) -> Image.Image:
    """Close-up of what the fix adds (gold) and removes (red)."""
    a = np.asarray(before)[..., 3] > 0
    b = np.asarray(after)[..., 3] > 0
    rgba = np.zeros(a.shape + (4,), np.uint8)
    rgba[a & b] = (*LABEL, 110)
    rgba[b & ~a] = (*GOLD, 255)
    rgba[a & ~b] = (*ACCENT, 255)
    return _gridded(Image.fromarray(rgba, "RGBA"), k)


def sheet_serif_fix(stamp: str, out_dir: Path | None = None) -> Path:
    """Before/after sheet of the H1 fix: M, Cyrillic M and W, then real
    LANGUAGE strings that contain them, both sizes, 1x and close-up."""
    style = STYLES["C"]
    needed = set("".join(SERIF_FIX_GLYPHS + [w for _k, w in SERIF_FIX_WORDS]).upper())
    fonts = {}
    for on in (False, True):
        with mirror_terminals(on):
            for size_key in ("small", "big"):
                f = RenderFont(style, size_key)
                for ch in needed:
                    f.glyph(ch)                # fill the cache while the switch holds
                fonts[(on, size_key)] = f
    W = 1500
    img, d = new_sheet(W, 2600)
    d.rectangle([0, 0, W, 86], fill=PANEL)
    d.rectangle([0, 84, W, 86], fill=ACCENT)
    d.text((28, 16), "SOVIET DOOM · ALPHABET C — SLAB-SERIF FIX (QA H1) · PROPOSAL",
           font=TITLE_FONT, fill=GOLD)
    d.text((30, 56), "BEFORE = installed in assets/fonts/   ·   AFTER = gen_font.py with "
                     "MIRROR_TERMINALS = True   ·   only these 3 glyphs change (6 of 214 files)",
           font=LABEL_FONT, fill=LABEL)
    d.text((W - 300, 60), stamp, font=LABEL_SMALL, fill=LABEL)
    x0, y = 28, 112

    for size_key in ("small", "big"):
        k = FIX_ZOOM[size_key]
        size = style.small if size_key == "small" else style.big
        d.text((x0, y), f"{size_key.upper()} FONT  ·  cap {size.cap} px"
                        + (f" + {size.shadow} px shadow" if size.shadow else "")
                        + f"  ·  1× then {k}×  ·  diff: gold = added, red = removed",
               font=LABEL_FONT, fill=GOLD)
        y += 26
        x = x0
        row_h = 0
        for ch in SERIF_FIX_GLYPHS:
            before = fonts[(False, size_key)].glyph(ch)
            after = fonts[(True, size_key)].glyph(ch)
            name = f"{ch}  U+{ord(ch):04X}" + ("  Cyrillic" if ord(ch) > 0x7F else "  Latin")
            d.text((x, y), name, font=LABEL_SMALL, fill=LABEL)
            yy = y + 18
            img.paste(before, (x, yy), before)
            img.paste(after, (x + before.width + 10, yy), after)
            yy += before.height + 8
            xx = x
            tile = None
            for label, tile in (("before", _gridded(before, k)), ("after", _gridded(after, k)),
                                ("diff", _diff(before, after, k))):
                d.text((xx, yy), label, font=LABEL_SMALL, fill=LABEL)
                img.paste(tile, (xx, yy + 16))
                xx += tile.width + 14
            x = xx + 30
            row_h = max(row_h, yy + 16 + tile.height - y)
        y += row_h + 26

    d.rectangle([x0, y, W - 28, y + 2], fill=ACCENT)
    y += 14
    d.text((x0, y), "REAL STRINGS FROM LANGUAGE — 1× is what the engine draws; "
                    "the close-up is how it reads on a 1080p screen",
           font=LABEL_FONT, fill=GOLD)
    y += 28
    for where, text in SERIF_FIX_WORDS:
        for size_key in ("small", "big"):
            k = FIX_WORD_ZOOM[size_key]
            d.text((x0, y), f"{where}  ·  {size_key} font  ·  1× and {k}×",
                   font=LABEL_SMALL, fill=LABEL)
            y += 18
            for on, tag in ((False, "BEFORE"), (True, "AFTER")):
                line = fonts[(on, size_key)].render(text)
                z = scaled(line, k)
                d.text((x0, y + 2), tag, font=LABEL_SMALL, fill=GOLD if on else LABEL)
                img.paste(line, (x0 + 70, y + 2), line)
                img.paste(z, (x0 + 70 + SCREEN_W + 20, y), z)
                y += max(line.height + 4, z.height) + 6
            y += 12

    img = img.crop((0, 0, W, min(y + 10, img.height)))
    out_dir = PREVIEW_DIR if out_dir is None else out_dir
    path = out_dir / f"{stamp}_F2_font-C-serif-fix.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


# ------------------------------------------------------------------ cli
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stamp", default="PREVIEW")
    ap.add_argument("--variant", default=None, help="A, B or C; default all")
    ap.add_argument("--sheets", action="store_true", help="sheets only")
    ap.add_argument("--serif-fix", action="store_true",
                    help="H1 proposal: variant C with MIRROR_TERMINALS on into "
                         "work/art/font_fix/, and the before/after sheet into docs/art/previews/")
    args = ap.parse_args()

    if args.serif_fix:
        build_serif_fix()
        print(sheet_serif_fix(args.stamp))
        return

    keys = [args.variant] if args.variant else list(STYLES)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest = {"stamp": args.stamp, "codepoints": len(GLYPHS), "variants": []}
    paths = []
    for k in keys:
        st = STYLES[k]
        if not args.sheets:
            manifest["variants"].append(build_variant(st, OUT_ROOT))
        paths.append(sheet_variant(st, args.stamp))
    paths.append(sheet_compare(args.stamp))
    if not args.sheets:
        (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
