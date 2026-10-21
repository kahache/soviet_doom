#!/usr/bin/env python3
"""Soviet Doom - the last Freedoom pieces of the shell (debt T12): the menu
cursor M_SKULL1/M_SKULL2 and the pause sign M_PAUSE. A SWEEP, not an asset:
nothing here writes to assets/.

Why this exists
---------------
MOD-SPEC 10, T12: after D31 the menu is text in our alphabet, but three
Freedoom pictures were left in the shell. One of them, M_EPISOD, is no
longer drawn (D41 redeclared the episode screen with a text header), so it
is not swept. The other two are:

  M_SKULL1 / M_SKULL2  the blinking skull Doom's DEFAULTLISTMENU draws as
                       the list cursor (`Selector "M_SKULL1", -32, -5`). The
                       blink is gzdoom.pk3's own ANIMDEFS (animdefs.txt,
                       g4.14.2: `texture optional M_SKULL1` / `pic M_SKULL1
                       tics 8` / `pic M_SKULL2 tics 8`), so two same-size
                       pictures that replace the two lumps blink by themselves.
  M_PAUSE              the sign GZDoom draws at the top of the game view
                       while paused: `pausesign = "M_PAUSE"` in gzdoom.pk3's
                       mapinfo/doomcommon.txt. One lump name for both
                       languages - see "Localising M_PAUSE" below.

What it draws
-------------
Five cursor options, each in its two blink phases, on a 20x20 canvas (the
Freedoom skull is 20x19):

  A  bevelled red star (the Kremlin star; ten facets, light left of every ray)
  B  hammer and sickle, the approved geometry of SDSTAR1 v5, imported from
     gen_soviet_base.hammer_sickle() - never re-traced
  C  red wedge (El Lissitzky, 1919): the wedge thrusts 3 px towards the item
  D  red flag on a pole, the cloth waving between the phases
  E  Sputnik: steel sphere, four swept antennae; phase 2 adds the "beep"

and three pause-sign options:

  P1 icon, no text: two cream bars on the bevelled star (one lump, no language)
  P2 word on a red plaque, one picture per language, same size (SDSTAR1's
     cream border on flag red)
  P3 word alone, cream with its shadow, one picture per language, same size

The canvas is sized by English and Russian (D48). Catalan «PAUSA» (P6) is
fitted inside P2's approved 77x20 plaque and is not drawn for P3, whose
bare canvas is narrower than the word (PAUSE_CANVAS_LANGS).

The words are set in SDMENU, READ from assets/fonts/sdmenu/ (D31; the menu
font, D22 letterforms in English: PAUSE reads PДUSЭ), recoloured the way the
menu's Font colour does it (gen_menu.FolderFont). No system font is used for
anything that could reach the game, so every picture here is byte-identical
on the Mac and on the Windows PC (D27; CLAUDE.md "Text-bearing assets do
not reproduce across the two machines"). The sheet's labels are HTML text.

Every output picture is RGBA with hard alpha (0/255) and opaque pixels from
docs/art/palette.json only: the ART-BIBLE 2 exception for assets drawn over
something else, like M_DOOM and the folder fonts.

Localising M_PAUSE (read in the engine, g4.14.2)
------------------------------------------------
gzdoom.exe carries the localised-texture loader: its strings include the
folder "localized/textures/", "%s contains no language IDs and will be
ignored", "Localized texture %s must be the same size as the one it
replaces", "Invalid language ID in texture %s" and "Unknown texture %s for
localized variant %s". So a picture can have per-language variants that the
engine swaps by the `language` CVar, provided the variant has exactly the
size of the picture it replaces - which is why P2 and P3 pad both languages
to one canvas. The FILE NAME the loader expects (e.g.
`localized/textures/m_pause.ru.png`) is from memory of the engine source,
which is not on this machine: NOT VERIFIED until an engine pass reads the
log for those messages. The alternative that needs no loader is a
status-bar `DrawPaused` override (zscript/ui/statusbar/statusbar.zs line
239 in gzdoom.pk3: `virtual bool DrawPaused(int player) { return false; }`)
that prints a LANGUAGE string in SDMENU - mod-engineer's code, and the mod
has no status-bar class yet (MOD-SPEC 6.5).

Imports, never runs, the approved generators: gen_menu (FolderFont, the
dimmed title, the main-menu mock, its colours) and gen_soviet_base (the
emblem's geometry). Neither writes anything when imported.

Usage
-----
    .venv/Scripts/python.exe tools/art/gen_cursor.py                         # work/art/shell_extra/
    .venv/Scripts/python.exe tools/art/gen_cursor.py --stamp 2026-10-13_2215 # + docs/art/previews/
    .venv/Scripts/python.exe tools/art/gen_cursor.py --catalan --install --stamp 2026-10-21   # P6: CA plaque only
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import gen_menu  # noqa: E402  (stdlib-only at import time)

SCRIPT_REL = "tools/art/gen_cursor.py"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "shell_extra"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SDMENU_DIR = PROJECT_ROOT / "assets" / "fonts" / "sdmenu"
SMALLFONT_DIR = gen_menu.SMALLFONT_DIR
IWAD = gen_menu.IWAD
# A clean engine screenshot of MAP01 on this PC (smoke run, 464x281, no
# console lines): the backdrop the pause sign is judged on.
GAME_SHOT = PROJECT_ROOT / "docs" / "qa" / "evidence" / "2026-10-13_1448_F3_smoke-map01-windows.png"

# ------------------------------------------------------------ engine facts
SELECTOR = gen_menu.SELECTOR_OFFSET   # (-32, -5): DEFAULTLISTMENU's Selector
BLINK_TICS = 8                        # gzdoom.pk3 animdefs.txt: pic M_SKULLn tics 8
TICRATE = 35
SCREEN = gen_menu.SCREEN              # 320x200 virtual menu screen
MAIN_POS = gen_menu.MAIN_POS          # src/lumps/MENUDEF "MainMenu" Position 97, 72
MAIN_SPACING = gen_menu.MAIN_SPACING
SKILL_HEADER = (32, 70)               # src/lumps/MENUDEF "SkillMenu" StaticText 32, 70
SKILL_POS = (32, 90)                  # "SkillMenu" Position 32, 90
SKILL_SPACING = 12
SKILL_SELECTED = 2                    # rung 3, "Not one step back", in the mock
PAUSE_TOP = 4                         # pause sign drawn centred at y = 4 (NOT VERIFIED, see doc)

# ----------------------------------------------------------------- canvas
CURSOR_W, CURSOR_H = 20, 20
# The canvas' top row lands on item y - 5 (the selector offset). SDMENU's
# capitals fill glyph rows 0..10 (cap 11, shadow under it), so their middle
# is item y + 5.5, i.e. canvas y 10.5: every cursor is centred there.
CURSOR_CX, CURSOR_CY = 10.0, 10.5
ALPHA_CUT = 128                       # supersampled coverage -> hard alpha
CURSOR_MAX_W = -SELECTOR[0] - 8       # keep >= 8 px between cursor and text

# --------------------------------------------------------------- the sweep
CURSORS = {  # id -> (name, one-line rationale)
    "A": ("Red star", "the Kremlin star, bevelled, gold rim; phase 2 brightens it and the rim flares"),
    "B": ("Hammer and sickle", "SDSTAR1's approved geometry at 17 px, gold; phase 2 flares to cream"),
    "C": ("Red wedge", "Lissitzky's wedge; phase 2 thrusts 3 px towards the item"),
    "D": ("Red flag", "a flag on a pole; the cloth waves between the phases"),
    "E": ("Sputnik", "the cosmodrome's own emblem; phase 2 adds the beep"),
}
PAUSE_OPTIONS = {
    "P1": ("Icon, no text", "two cream bars on the red star: one lump, no language"),
    "P2": ("Word on a plaque", "SDMENU in cream on SDSTAR1's red plaque, one picture per language"),
    "P3": ("Word alone", "SDMENU in cream with its shadow, one picture per language"),
}
PAUSE_WORDS = {"en": "PAUSE", "ru": "ПАУЗА", "ca": "PAUSA"}
# The languages that SIZE the canvas: D48 approved P2 at 77x20 from the
# English and Russian words, and the installed M_PAUSE / M_PAUSE.ru are
# that size. A later language (Catalan, P6) is fitted INSIDE that canvas,
# never allowed to grow it: GZDoom refuses a localised variant of another
# size, and growing it would rewrite the two approved plaques. SDMENU's
# Latin A is D22's Д, so «PAUSA» reads PДUSД (66 px, 3 more than PAUSE):
# it fits P2's plaque with 5 px of red each side, but not P3's bare
# 63 px canvas, so Catalan has P2 only (pause_languages).
PAUSE_CANVAS_LANGS = ("en", "ru")
PLAQUE_PAD_X, PLAQUE_PAD_Y = 7, 4
PLAQUE_BORDER = 1
ICON_SIZE = 32
WEDGE_THRUST = 3                      # px the wedge advances in phase 2
FLAG_WAVE = 1.3                       # px amplitude of the cloth's wave
FLAG_WAVELENGTH = 12.0
STAR_R = 7.5                          # cursor A: rim + contour stay inside 20x20


def _np():
    import numpy as np
    return np


def colours() -> dict:
    """Named palette colours used here (all from docs/art/palette.json)."""
    import artlib
    rc = artlib.ramp_colour
    return {
        "red_hi": rc("flag_red", 1.0), "red_lit": rc("flag_red", 0.88),
        "red": rc("flag_red", 0.74), "red_shade": rc("flag_red", 0.56),
        "red_dark": rc("flag_red", 0.20),
        "gold": rc("hazard_yellow", 0.80), "gold_hi": rc("hazard_yellow", 1.0),
        "cream": rc("cream_yellow", 0.92), "cream_hi": rc("cream_yellow", 1.0),
        "steel_hi": rc("steel_blue", 0.95), "steel": rc("steel_blue", 0.70),
        "steel_shade": rc("steel_blue", 0.45), "steel_dark": rc("steel_blue", 0.18),
        "ink": rc("concrete_cold", 0.04),
    }


# --------------------------------------------------------- rasterisation
def rasterise(ov):
    """Box-downsample an artlib.Overlay to its pixel size, cut the alpha at
    50 % and snap every opaque pixel to the palette. Returns an RGBA image
    with hard alpha."""
    import artlib
    from PIL import Image
    np = _np()
    small = ov.img.resize((ov.w, ov.h), Image.Resampling.BOX)   # Pillow un-premultiplies
    a = np.asarray(small)
    opaque = a[..., 3] >= ALPHA_CUT
    rgb = np.asarray(artlib.quantize(Image.fromarray(np.ascontiguousarray(a[..., :3]), "RGB")).convert("RGB"))
    out = np.zeros(a.shape, np.uint8)
    out[opaque, :3] = rgb[opaque]
    out[opaque, 3] = 255
    return Image.fromarray(out, "RGBA")


def _bevelled_star(ov, cx, cy, r, light, dark, rim, rim_w=1.0, halo=None):
    """Five-pointed star in ten facets: on every ray the left half is lit
    and the right half shaded (the Kremlin star's bevel). `halo` adds a
    second, outer contour so a light rim still separates from a red
    backdrop (the dimmed title is red)."""
    import artlib
    pts = artlib.star_points(cx, cy, r)
    if halo is not None:
        h = ov.group(outline=halo, outline_width=rim_w + 1.0)
        h.polygon(pts, halo)
        ov.end_group(h)
    g = ov.group(outline=rim, outline_width=rim_w)
    g.polygon(pts, dark)
    for i in range(0, 10, 2):
        g.polygon([(cx, cy), pts[i], pts[(i - 1) % 10]], light)
    ov.end_group(g)


# ------------------------------------------------------------ the cursors
def _cursor_star(ov, phase, c):
    # Red on the red title needs a light rim to read: gold in phase 1, and
    # in phase 2 the facets brighten and the rim flares (the blink).
    if phase == 1:
        _bevelled_star(ov, CURSOR_CX, CURSOR_CY, STAR_R, c["red_lit"], c["red_shade"], c["gold"], halo=c["ink"])
    else:
        _bevelled_star(ov, CURSOR_CX, CURSOR_CY, STAR_R, c["red_hi"], c["red"], c["cream_hi"], halo=c["ink"])


def _cursor_hammer_sickle(ov, phase, c):
    import gen_soviet_base
    fill = c["gold"] if phase == 1 else c["cream_hi"]
    gen_soviet_base.hammer_sickle(ov, CURSOR_CX, CURSOR_CY, 8.5, fill, c["red_dark"])


def _cursor_wedge(ov, phase, c):
    dx = 0 if phase == 1 else WEDGE_THRUST
    g = ov.group(outline=c["ink"], outline_width=1.0)
    g.rect(1, 6.5, 4, 14.5, fill=c["cream"])                      # the white field the wedge pierces
    ov.end_group(g)
    g = ov.group(outline=c["red_dark"], outline_width=1.0)
    tip = (14.5 + dx, CURSOR_CY)
    g.polygon([(2.0 + dx, 3.0), tip, (2.0 + dx, 18.0)], c["red"])
    g.polygon([(2.0 + dx, 3.0), tip, (2.0 + dx, CURSOR_CY)], c["red_lit"])
    ov.end_group(g)


def _cursor_flag(ov, phase, c):
    import artlib
    phi = 0.0 if phase == 1 else math.pi
    g = ov.group(outline=c["ink"], outline_width=1.0)
    g.rect(2, 2.5, 3.5, 19, fill=c["steel"])                      # pole
    g.ellipse(1.4, 1.0, 4.1, 3.7, fill=c["gold"])                  # finial
    ov.end_group(g)
    x0, x1, h = 3.5, 18.5, 8.0
    xs = [x0 + (x1 - x0) * i / 24 for i in range(25)]

    def wave(x):
        return FLAG_WAVE * math.sin(2 * math.pi * (x - x0) / FLAG_WAVELENGTH + phi) * (x - x0) / (x1 - x0)

    top = [(x, 4.0 + wave(x)) for x in xs]
    bottom = [(x, 4.0 + h + wave(x)) for x in reversed(xs)]
    g = ov.group(outline=c["red_dark"], outline_width=1.0)
    g.polygon(top + bottom, c["red"])
    # the crests of the wave catch the light
    for i in range(24):
        xm = (xs[i] + xs[i + 1]) / 2
        slope = math.cos(2 * math.pi * (xm - x0) / FLAG_WAVELENGTH + phi)
        if slope > 0.35:
            g.polygon([top[i], top[i + 1], (xs[i + 1], 4.0 + h + wave(xs[i + 1])),
                       (xs[i], 4.0 + h + wave(xs[i]))], c["red_lit"])
    g.polygon(artlib.star_points(6.6, 7.2 + wave(6.6), 2.4), c["gold"])
    ov.end_group(g)


def _cursor_sputnik(ov, phase, c):
    cx, cy, r = 10.5, CURSOR_CY, 4.6
    for ex, ey in ((0.8, 3.0), (0.5, 8.3), (0.5, 12.7), (0.8, 18.0)):   # four swept antennae
        ov.line([(cx - r * 0.6, cy + (ey - cy) * 0.18), (ex, ey)], c["steel_dark"], 1.2)
    g = ov.group(outline=c["steel_dark"], outline_width=1.0)
    g.ellipse(cx - r, cy - r, cx + r, cy + r, fill=c["steel_shade"])
    g.ellipse(cx - r * 0.85, cy - r * 0.9, cx + r * 0.55, cy + r * 0.5, fill=c["steel"])
    g.ellipse(cx - r * 0.55, cy - r * 0.62, cx - r * 0.05, cy - r * 0.12, fill=c["steel_hi"])
    ov.end_group(g)
    if phase == 2:
        for r_out in (6.6, 8.9):
            ov.arc_ring(cx, cy, r_out, r_out - 1.3, -38, 38, c["cream_hi"])


CURSOR_DRAW = {"A": _cursor_star, "B": _cursor_hammer_sickle, "C": _cursor_wedge,
               "D": _cursor_flag, "E": _cursor_sputnik}


def cursor_image(option: str, phase: int):
    """One phase (1 = M_SKULL1, 2 = M_SKULL2) of one cursor option."""
    from artlib import Overlay
    ov = Overlay(CURSOR_W, CURSOR_H)
    CURSOR_DRAW[option](ov, phase, colours())
    return rasterise(ov)


# --------------------------------------------------------- the pause sign
def sdmenu_font():
    """The installed menu font, read (never rebuilt) from assets/fonts/sdmenu/."""
    return gen_menu.FolderFont(SDMENU_DIR)


def missing_glyphs(text: str, folder: Path = SDMENU_DIR) -> list[str]:
    return [ch for ch in text if ch != " " and not (folder / gen_menu.glyph_file(ch.upper())).is_file()]


def _word(lang: str, c):
    return sdmenu_font().render(PAUSE_WORDS[lang], c["cream"], c["ink"])


def pause_canvas_size(option: str) -> tuple[int, int]:
    """One size for every language: the engine refuses a localised variant
    of another size ("Localized texture %s must be the same size as the
    one it replaces", gzdoom.exe g4.14.2). Sized by PAUSE_CANVAS_LANGS only."""
    if option == "P1":
        return ICON_SIZE, ICON_SIZE
    c = colours()
    words = [_word(lang, c) for lang in PAUSE_CANVAS_LANGS]
    w, h = max(x.width for x in words), max(x.height for x in words)
    if option == "P2":
        return w + 2 * PLAQUE_PAD_X, h + 2 * PLAQUE_PAD_Y
    return w, h


def pause_room(option: str) -> tuple[int, int]:
    """The largest word an option's canvas holds: P2 keeps at least one red
    pixel between the word and the cream border; P3 is the bare word."""
    W, H = pause_canvas_size(option)
    if option == "P2":
        inset = 2 * (PLAQUE_BORDER + 1)
        return W - inset, H - inset
    return W, H


def pause_languages(option: str) -> tuple[str, ...]:
    """The languages an option is drawn in: "xx" for the wordless P1, else
    every PAUSE_WORDS language whose word fits the option's canvas."""
    if option == "P1":
        return ("xx",)
    c = colours()
    room_w, room_h = pause_room(option)
    return tuple(lang for lang in PAUSE_WORDS
                 if lang in PAUSE_CANVAS_LANGS
                 or (_word(lang, c).width <= room_w and _word(lang, c).height <= room_h))


def pause_image(option: str, lang: str):
    """The pause sign of one option in one language (P1 ignores `lang`)."""
    from PIL import Image
    from artlib import Overlay
    c = colours()
    W, H = pause_canvas_size(option)
    if option != "P1" and lang not in pause_languages(option):
        raise ValueError(f"pause sign {option}: {PAUSE_WORDS[lang]!r} ({lang}) does not fit {W}x{H}")
    if option == "P1":
        ov = Overlay(W, H)
        _bevelled_star(ov, W / 2, H / 2 + 1.0, 15.5, c["red_lit"], c["red_shade"], c["red_dark"])
        g = ov.group(outline=c["red_dark"], outline_width=1.0)
        g.rect(11.5, 11.5, 14.5, 23.0, fill=c["cream"])
        g.rect(17.5, 11.5, 20.5, 23.0, fill=c["cream"])
        ov.end_group(g)
        return rasterise(ov)
    word = _word(lang, c)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if option == "P2":
        img.paste(c["cream"] + (255,), (0, 0, W, H))
        b = PLAQUE_BORDER
        img.paste(c["red"] + (255,), (b, b, W - b, H - b))
        img.paste(c["red_dark"] + (255,), (b, H - b - 1, W - b, H - b))   # inner shadow line
    img.alpha_composite(word, ((W - word.width) // 2, (H - word.height) // 2))
    return img


# ----------------------------------------------------------- references
def read_wad_patch(name: str, wad: Path = IWAD):
    """A Doom-format patch from the IWAD as (RGBA image, (left, top)), or
    None when the IWAD is not in this clone. Shown on the sheet as 'today'."""
    if not wad.is_file():
        return None
    from PIL import Image
    data = wad.read_bytes()
    n, off = struct.unpack_from("<4xii", data, 0)
    lumps = {}
    for i in range(n):
        pos, size, nm = struct.unpack_from("<ii8s", data, off + 16 * i)
        lumps[nm.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
    if name not in lumps or "PLAYPAL" not in lumps:
        return None
    pp = lumps["PLAYPAL"][0]
    pal = [tuple(data[pp + 3 * i: pp + 3 * i + 3]) for i in range(256)]
    p0 = lumps[name][0]
    w, h, lo, to = struct.unpack_from("<hhhh", data, p0)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for col in range(w):
        q = p0 + struct.unpack_from("<I", data, p0 + 8 + 4 * col)[0]
        while data[q] != 0xFF:
            top, length = data[q], data[q + 1]
            for j in range(length):
                px[col, top + j] = (*pal[data[q + 3 + j]], 255)
            q += length + 4
    return img, (lo, to)


# -------------------------------------------------------------- contexts
def menu_backdrop(lang: str):
    """The main menu as the engine draws it today (dimmed TITLEPIC, M_DOOM at
    60,0, the items in SDMENU, item 1 selected) WITHOUT a cursor: the
    cursor is laid over it, phase by phase."""
    screen, overflow = gen_menu.mock_main(lang, sdmenu_font(), None, gen_menu._colours())
    return screen


def skill_backdrop(lang: str):
    """The skill screen with today's MENUDEF positions (header 32,70; rungs
    from 32,90 in SmallFont), rung 3 selected, without a cursor."""
    from PIL import Image
    col = gen_menu._colours()
    s = gen_menu._dimmed_title()
    s.alpha_composite(Image.open(gen_menu.M_DOOM).convert("RGBA"), gen_menu.LOGO_POS)
    over: list = []
    head = gen_menu.SKILL_HEAD[1] if lang == "en" else gen_menu.SKILL_HEAD[2]
    gen_menu._put_text(s, sdmenu_font(), head, SKILL_HEADER, col["cream"], col["shadow"], over)
    small = gen_menu.FolderFont(SMALLFONT_DIR)
    for i, name in enumerate(gen_menu.SKILL_ITEMS[lang]):
        pos = (SKILL_POS[0], SKILL_POS[1] + i * SKILL_SPACING)
        body = col["gold"] if i == SKILL_SELECTED else col["red"]
        gen_menu._put_text(s, small, name, pos, body, col["shadow"], over)
    return s


def selector_xy(item_pos, offsets=(0, 0)) -> tuple[int, int]:
    """Where the engine puts the cursor's top-left for an item at item_pos."""
    return (item_pos[0] + SELECTOR[0] - offsets[0], item_pos[1] + SELECTOR[1] - offsets[1])


MAIN_CURSOR_AT = selector_xy(MAIN_POS)
SKILL_CURSOR_AT = selector_xy((SKILL_POS[0], SKILL_POS[1] + SKILL_SELECTED * SKILL_SPACING))


def compose(backdrop, sprite, at):
    out = backdrop.copy()
    out.alpha_composite(sprite, (max(at[0], 0), max(at[1], 0)))
    return out


def pause_at(sign, screen_w: int) -> tuple[int, int]:
    """Top-centre of the screen, scale 1 (the 464x281 shot has CleanXfac 1)."""
    return (screen_w - sign.width) // 2, PAUSE_TOP


# ------------------------------------------------------------------ build
def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(out_dir: Path = OUT_DIR) -> dict:
    """Write every option and its contexts under out_dir; returns the
    manifest (also written as out_dir/manifest.json)."""
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = out_dir / "context"
    ctx.mkdir(exist_ok=True)
    files: dict = {}

    def save(img, rel):
        p = out_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(p, optimize=True)
        files[rel] = {"size": list(img.size), "sha256": _sha(p)}
        return img

    backdrops = {f"main_{lang}": menu_backdrop(lang) for lang in ("en", "ru")}
    backdrops.update({f"skill_{lang}": skill_backdrop(lang) for lang in ("en", "ru")})
    for key, img in backdrops.items():
        save(img.convert("RGB"), f"context/backdrop_{key}.png")

    cursors = {}
    for opt in CURSORS:
        for phase in (1, 2):
            img = save(cursor_image(opt, phase), f"cursor_{opt}_{phase}.png")
            cursors[(opt, phase)] = img
        for lang in ("en", "ru"):
            save(compose(backdrops[f"main_{lang}"], cursors[(opt, 1)], MAIN_CURSOR_AT).convert("RGB"),
                 f"context/main_{lang}_{opt}.png")
        save(compose(backdrops["skill_en"], cursors[(opt, 1)], SKILL_CURSOR_AT).convert("RGB"),
             f"context/skill_en_{opt}.png")

    shot = Image.open(GAME_SHOT).convert("RGBA")
    save(shot.convert("RGB"), "context/backdrop_game.png")
    for opt in PAUSE_OPTIONS:
        for lang in pause_languages(opt):
            sign = save(pause_image(opt, lang), f"pause_{opt}_{lang}.png")
            save(compose(shot, sign, pause_at(sign, shot.width)).convert("RGB"),
                 f"context/game_{opt}_{lang}.png")

    for name in ("M_SKULL1", "M_SKULL2", "M_PAUSE"):
        ref = read_wad_patch(name)
        if ref is not None:
            save(ref[0], f"freedoom/ref_{name}.png")
            files[f"freedoom/ref_{name}.png"]["offsets"] = list(ref[1])

    manifest = {
        "script": SCRIPT_REL,
        "what": "T12 sweep: menu cursor (M_SKULL1/M_SKULL2) and pause sign (M_PAUSE). Proposals, not assets.",
        "cursor_canvas": [CURSOR_W, CURSOR_H],
        "selector_offset": list(SELECTOR),
        "blink_tics": BLINK_TICS,
        "cursors": {k: {"name": v[0], "why": v[1], "lumps": {"M_SKULL1": f"cursor_{k}_1.png",
                                                            "M_SKULL2": f"cursor_{k}_2.png"}}
                    for k, v in CURSORS.items()},
        "pause": {k: {"name": v[0], "why": v[1], "size": list(pause_canvas_size(k))}
                  for k, v in PAUSE_OPTIONS.items()},
        "pause_words": PAUSE_WORDS,
        "font": "assets/fonts/sdmenu (read, not rebuilt)",
        "files": files,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
    return manifest


# ------------------------------------------------------------------ sheet
def _b64(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode("ascii")


RECOMMENDED_CURSOR = "A"
RECOMMENDED_PAUSE = "P2"

CSS = """
:root{--bg:#1d1f22;--panel:#2a2d31;--ink:#e6e1d3;--mute:#9aa0a6;--red:#b8322a;--gold:#d9b23a;--line:#3a3e44}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{background:var(--panel);border-bottom:3px solid var(--red);padding:18px 24px}
h1{margin:0;font-size:22px;color:var(--gold);letter-spacing:.04em}
h2{margin:32px 0 6px;font-size:18px;color:var(--gold);border-top:2px solid var(--red);padding-top:12px}
h3{margin:0 0 4px;font-size:15px}
main{padding:0 24px 40px;max-width:1500px}
p,li{color:var(--ink)} .mute{color:var(--mute)} code{color:var(--gold)}
img{image-rendering:pixelated;image-rendering:crisp-edges}
.row{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start;background:var(--panel);
 border:1px solid var(--line);border-radius:6px;padding:14px;margin:12px 0}
.row.rec{border:2px solid var(--gold)}
.badge{display:inline-block;background:var(--gold);color:#1d1f22;font-weight:700;font-size:12px;
 padding:1px 8px;border-radius:10px;margin-left:8px;vertical-align:2px}
.meta{width:230px}
.cell{display:flex;flex-direction:column;gap:4px;max-width:100%;overflow-x:auto}
.cap{font-size:12px;color:var(--mute)}
.chk{background:repeating-conic-gradient(#3a3d42 0 25%,#2f3236 0 50%) 0 0/8px 8px;padding:4px;display:inline-block}
.stage{position:relative;display:inline-block;line-height:0;background-repeat:no-repeat;image-rendering:pixelated;image-rendering:crisp-edges;max-width:none}
.stage .spr{position:absolute}
.blink{animation:blink BLINKs steps(1,end) infinite}
@keyframes blink{0%{opacity:0}50%{opacity:1}}
table{border-collapse:collapse;margin:8px 0}
td,th{border:1px solid var(--line);padding:4px 10px;text-align:left;vertical-align:top}
@media (max-width:700px){main{padding:0 16px 32px}.meta{width:100%}}
"""


_BACKDROPS: dict = {}   # backdrop rel path -> CSS class; each picture is embedded once


def _stage(backdrop_rel, sprites, scale, out_dir):
    """A context picture: backdrop at `scale`, sprite phases laid over it at
    their engine positions. sprites = [(rel1, rel2_or_None, (x, y))]. The
    backdrop is a CSS background embedded once per sheet, not per use."""
    from PIL import Image
    bp = out_dir / backdrop_rel
    w, h = Image.open(bp).size
    cls = _BACKDROPS.setdefault(backdrop_rel, f"bd{len(_BACKDROPS)}")
    html = [f'<div class="stage {cls}" style="width:{w * scale}px;height:{h * scale}px;'
            f'background-size:{w * scale}px {h * scale}px">']
    for rel1, rel2, (x, y) in sprites:
        sw, sh = Image.open(out_dir / rel1).size
        style = f"left:{x * scale}px;top:{y * scale}px;width:{sw * scale}px;height:{sh * scale}px"
        html.append(f'<img class="spr" style="{style}" src="{_b64(out_dir / rel1)}" alt="">')
        if rel2:
            html.append(f'<img class="spr blink" style="{style}" src="{_b64(out_dir / rel2)}" alt="">')
    html.append("</div>")
    return "".join(html)


def _sprite(rel, scale, out_dir):
    from PIL import Image
    w, h = Image.open(out_dir / rel).size
    return f'<span class="chk"><img src="{_b64(out_dir / rel)}" width="{w * scale}" height="{h * scale}" alt=""></span>'


def sheet(stamp: str, out_dir: Path = OUT_DIR, preview_dir: Path = PREVIEW_DIR) -> Path:
    """The self-contained HTML sweep for the CEO (needs build() first)."""
    _BACKDROPS.clear()
    blink_s = f"{2 * BLINK_TICS / TICRATE:.3f}"
    css = CSS.replace("BLINKs", f"{blink_s}s")
    main_at = {"en": MAIN_CURSOR_AT, "ru": MAIN_CURSOR_AT}
    have_ref = (out_dir / "freedoom" / "ref_M_SKULL1.png").is_file()
    o = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
         f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Shell cursor and pause</title><style>{css}</style></head><body>",
         "<header><h1>SOVIET DOOM · THE LAST FREEDOOM PIECES OF THE SHELL (T12)</h1>",
         f"<div class='mute'>Menu cursor <code>M_SKULL1</code>/<code>M_SKULL2</code> and pause sign "
         f"<code>M_PAUSE</code>. Sweep {stamp}, <code>{SCRIPT_REL}</code>, files in "
         f"<code>work/art/shell_extra/</code>. Proposals only: nothing is in <code>assets/</code>.</div></header><main>"]

    o.append("<h2>Recommendation</h2><ul>"
             f"<li><b>Cursor: A, the red star.</b> It is the one shape that reads at 17 px on both screens "
             "(cream items on the dimmed title, red rungs on the skill screen), it is already the mod's "
             "emblem (<code>SDSTAR1</code>, the title lockup) and its blink — the facets brighten and the "
             "gold rim flares to cream — is as calm as the skull's. The gold rim and a dark contour are "
             "what keep a red star readable on the red title. Runner-up: B, gold on red reads best of all, "
             "but at 17 px the hammer and the sickle start to merge. C and D are red on red and read as a "
             "UI arrow and a flag; E (Sputnik) is the most ours but its grey sphere is weak on the title.</li>"
             f"<li><b>Pause: P2, the word on a red plaque, one picture per language.</b> GZDoom g4.14.2 "
             "can swap a picture by language (<code>localized/textures/</code>, read in "
             "<code>gzdoom.exe</code>), as long as both have exactly the same size — so both are drawn on "
             "one canvas. The plaque keeps the word legible on any wall. <b>The file name the loader wants "
             "is NOT VERIFIED</b> (engine source not on this machine): one engine pass settles it. If it "
             "does not work, P1 (the icon) needs no localisation at all and is the fallback.</li>"
             "<li><code>M_EPISOD</code> is not swept: D41 already replaced it with a text header.</li></ul>")

    # ---------------- cursors
    o.append("<h2>1 · Menu cursor — five options, two blink phases each</h2>"
             f"<p class='mute'>20×20 canvas (Freedoom's skull is 20×19). The engine draws it at "
             f"<code>Selector \"M_SKULL1\", {SELECTOR[0]}, {SELECTOR[1]}</code> from each item and blinks "
             f"M_SKULL1/M_SKULL2 every {BLINK_TICS} tics (gzdoom.pk3 <code>animdefs.txt</code>); the contexts "
             f"below blink at that rate ({blink_s} s per cycle). Menu: the real items in <code>SDMENU</code> "
             "read from <code>assets/fonts/sdmenu/</code>, TITLEPIC dimmed as the engine dims it, M_DOOM at "
             "60,0. Skill screen: today's MENUDEF positions (header 32,70; rungs from 32,90). Shown at 2×.</p>")
    if have_ref:
        o.append("<div class='row'><div class='meta'><h3>Today: Freedoom's skull</h3>"
                 "<div class='cap'>M_SKULL1 / M_SKULL2 from <code>iwads/freedoom2.wad</code>, for comparison "
                 "(BSD, Freedoom; not ours)</div></div>")
        lo, to = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))["files"][
            "freedoom/ref_M_SKULL1.png"]["offsets"]
        o.append(f"<div class='cell'><span class='cap'>phase 1 · 2 · 4×</span><div>"
                 f"{_sprite('freedoom/ref_M_SKULL1.png', 4, out_dir)} {_sprite('freedoom/ref_M_SKULL2.png', 4, out_dir)}"
                 "</div></div>")
        for lang in ("en", "ru"):
            o.append(f"<div class='cell'><span class='cap'>main menu, {lang.upper()}</span>"
                     + _stage(f"context/backdrop_main_{lang}.png",
                              [("freedoom/ref_M_SKULL1.png", "freedoom/ref_M_SKULL2.png",
                                selector_xy(MAIN_POS, (lo, to)))], 2, out_dir) + "</div>")
        o.append("</div>")
    for opt, (name, why) in CURSORS.items():
        rec = opt == RECOMMENDED_CURSOR
        o.append(f"<div class='row{' rec' if rec else ''}'><div class='meta'><h3>{opt} · {name}"
                 f"{'<span class=badge>recommended</span>' if rec else ''}</h3>"
                 f"<div class='cap'>{why}</div>"
                 f"<div class='cap'>files: <code>cursor_{opt}_1.png</code> → M_SKULL1, "
                 f"<code>cursor_{opt}_2.png</code> → M_SKULL2</div></div>")
        o.append(f"<div class='cell'><span class='cap'>phase 1 · phase 2 · 1×</span><div>"
                 f"{_sprite(f'cursor_{opt}_1.png', 1, out_dir)} {_sprite(f'cursor_{opt}_2.png', 1, out_dir)}"
                 f"</div><span class='cap'>4×</span><div>{_sprite(f'cursor_{opt}_1.png', 4, out_dir)} "
                 f"{_sprite(f'cursor_{opt}_2.png', 4, out_dir)}</div></div>")
        for lang in ("en", "ru"):
            o.append(f"<div class='cell'><span class='cap'>main menu, {lang.upper()} (blinking)</span>"
                     + _stage(f"context/backdrop_main_{lang}.png",
                              [(f"cursor_{opt}_1.png", f"cursor_{opt}_2.png", main_at[lang])], 2, out_dir)
                     + "</div>")
        o.append("<div class='cell'><span class='cap'>skill screen, EN (blinking)</span>"
                 + _stage("context/backdrop_skill_en.png",
                          [(f"cursor_{opt}_1.png", f"cursor_{opt}_2.png", SKILL_CURSOR_AT)], 2, out_dir)
                 + "</div></div>")

    # ---------------- pause
    o.append("<h2>2 · Pause sign — one lump, two languages</h2>"
             "<p class='mute'>Backdrop: the clean MAP01 smoke screenshot on this PC "
             "(<code>docs/qa/evidence/2026-10-13_1448_F3_smoke-map01-windows.png</code>, 464×281, scale 1, "
             "shown at 2×). The sign is centred at the top, y = 4 (Doom's placement; NOT VERIFIED for "
             "g4.14.2). The words are <code>SDMENU</code>, so English carries D22's letterforms: PAUSE reads "
             "PДUSЭ, like the menu.</p>")
    o.append("<table><tr><th>Way</th><th>What it costs</th><th>Status</th></tr>"
             "<tr><td>An icon, no text (P1)</td><td>one picture replaces <code>M_PAUSE</code>; nothing else</td>"
             "<td>works by construction</td></tr>"
             "<tr><td>A picture per language (P2, P3)</td><td><code>graphics/M_PAUSE.png</code> (English) plus a "
             "Russian variant under <code>localized/textures/</code>, <b>same size</b>; no code</td>"
             "<td>loader present in <code>gzdoom.exe</code> g4.14.2 (its strings: <code>localized/textures/</code>, "
             "\"Localized texture %s must be the same size as the one it replaces\", \"%s contains no language "
             "IDs and will be ignored\"); exact file name NOT VERIFIED</td></tr>"
             "<tr><td>Text, not a picture</td><td>a status-bar class overriding <code>DrawPaused</code> "
             "(gzdoom.pk3 <code>statusbar.zs</code> line 239) to print a LANGUAGE string in SDMENU; "
             "mod-engineer's ZScript, and the mod has no status bar of its own yet (MOD-SPEC 6.5)</td>"
             "<td>possible; more work than the picture</td></tr></table>")
    from PIL import Image
    shot_w = Image.open(out_dir / "context" / "backdrop_game.png").width
    if (out_dir / "freedoom" / "ref_M_PAUSE.png").is_file():
        sign = Image.open(out_dir / "freedoom" / "ref_M_PAUSE.png")
        o.append("<div class='row'><div class='meta'><h3>Today: Freedoom's M_PAUSE</h3>"
                 f"<div class='cap'>{sign.width}×{sign.height}, English only</div></div>"
                 f"<div class='cell'><span class='cap'>4×</span>{_sprite('freedoom/ref_M_PAUSE.png', 4, out_dir)}</div>"
                 "<div class='cell'><span class='cap'>in game</span>"
                 + _stage("context/backdrop_game.png",
                          [("freedoom/ref_M_PAUSE.png", None, pause_at(sign, shot_w))], 2, out_dir)
                 + "</div></div>")
    for opt, (name, why) in PAUSE_OPTIONS.items():
        rec = opt == RECOMMENDED_PAUSE
        langs = pause_languages(opt)
        w, h = pause_canvas_size(opt)
        o.append(f"<div class='row{' rec' if rec else ''}'><div class='meta'><h3>{opt} · {name}"
                 f"{'<span class=badge>recommended</span>' if rec else ''}</h3>"
                 f"<div class='cap'>{why}</div><div class='cap'>{w}×{h}"
                 f"{', every language drawn' if opt != 'P1' else ''}</div></div>")
        sprites = " ".join(_sprite(f"pause_{opt}_{lang}.png", 4, out_dir) for lang in langs)
        o.append(f"<div class='cell'><span class='cap'>4× ({' / '.join(l.upper() for l in langs if l != 'xx') or 'no text'})"
                 f"</span><div>{sprites}</div></div>")
        for lang in langs:
            sign = Image.open(out_dir / f"pause_{opt}_{lang}.png")
            label = "in game" if lang == "xx" else f"in game, {lang.upper()}"
            o.append(f"<div class='cell'><span class='cap'>{label}</span>"
                     + _stage("context/backdrop_game.png",
                              [(f"pause_{opt}_{lang}.png", None, pause_at(sign, shot_w))], 2, out_dir)
                     + "</div>")
        o.append("</div>")

    o.append("<h2>Notes</h2><ul class='mute'>"
             "<li>Every picture is RGBA with hard alpha and opaque pixels from <code>docs/art/palette.json</code> "
             "only (the ART-BIBLE §2 exception, like M_DOOM and the fonts). No system font is used: the words "
             "are our own glyphs, so the pictures are byte-identical on the Mac and on this PC (D27).</li>"
             "<li>The menu colours are the same approximations as the D31 sheet: the engine's Cream/Gold "
             "translation of SDMENU is NOT VERIFIED until an engine pass; the cursor itself is drawn "
             "untranslated, so it is exact.</li>"
             "<li>B reuses <code>SDSTAR1</code>'s approved hammer-and-sickle geometry "
             "(<code>gen_soviet_base.hammer_sickle</code>), shrunk; it is not re-traced.</li>"
             "<li>Freedoom's pictures are shown for comparison only (BSD licence, read from the IWAD).</li>"
             "</ul></main></body></html>")
    path = preview_dir / f"{stamp}_F2_shell-cursor-pause-sweep.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    bd_css = "".join(f".{cls}{{background-image:url({_b64(out_dir / rel)})}}" for rel, cls in _BACKDROPS.items())
    o[0] = o[0].replace("</style>", bd_css + "</style>")
    path.write_text("".join(o), encoding="utf-8")
    return path


# ------------------------------------------------------- Catalan (P6, D97)
CATALAN_PAUSE_OPTION = "P2"            # the approved plaque (D48)
CATALAN_PAUSE_FILE = f"pause_{CATALAN_PAUSE_OPTION}_ca.png"
# ADR 010: the variant the build packs as localized/textures/M_PAUSE.ca.png.
PAUSE_LOCALIZED_DIR = PROJECT_ROOT / "assets" / "localized" / "textures"
CATALAN_PAUSE_LUMP = "M_PAUSE.ca.png"
PREVIEW_CROP_W, PREVIEW_CROP_H = 120, 30   # the top-centre of the game shot around the sign
PREVIEW_GAP = 4


def catalan_pause(out_dir: Path = OUT_DIR, install_dir: Path | None = None) -> dict[str, Path]:
    """Write ONLY the Catalan P2 plaque: out_dir/pause_P2_ca.png and, with
    install_dir, install_dir/M_PAUSE.ca.png, the same bytes. Nothing else of
    the sweep is rewritten, so the approved English and Russian plaques
    cannot move."""
    import io
    buf = io.BytesIO()
    pause_image(CATALAN_PAUSE_OPTION, "ca").save(buf, format="PNG", optimize=True)
    written = {}
    out_dir.mkdir(parents=True, exist_ok=True)
    written["work"] = out_dir / CATALAN_PAUSE_FILE
    written["work"].write_bytes(buf.getvalue())
    if install_dir is not None:
        install_dir.mkdir(parents=True, exist_ok=True)
        written["asset"] = install_dir / CATALAN_PAUSE_LUMP
        written["asset"].write_bytes(buf.getvalue())
    return written


def catalan_preview(path: Path, zoom: int = 4) -> Path:
    """P2 in English, Russian and Catalan, each at the top centre of the
    MAP01 game shot where the engine draws it, one above the other at
    `zoom` (nearest neighbour), for the CEO to compare by eye."""
    from PIL import Image
    shot = Image.open(GAME_SHOT).convert("RGBA")
    x0 = (shot.width - PREVIEW_CROP_W) // 2
    tiles = []
    for lang in ("en", "ru", "ca"):
        sign = pause_image(CATALAN_PAUSE_OPTION, lang)
        framed = compose(shot, sign, pause_at(sign, shot.width))
        tiles.append(framed.crop((x0, 0, x0 + PREVIEW_CROP_W, PREVIEW_CROP_H)))
    sheet_h = len(tiles) * PREVIEW_CROP_H + (len(tiles) - 1) * PREVIEW_GAP
    sheet_img = Image.new("RGBA", (PREVIEW_CROP_W, sheet_h), (0, 0, 0, 255))
    for k, tile in enumerate(tiles):
        sheet_img.paste(tile, (0, k * (PREVIEW_CROP_H + PREVIEW_GAP)))
    big = sheet_img.convert("RGB").resize((PREVIEW_CROP_W * zoom, sheet_h * zoom), Image.NEAREST)
    path.parent.mkdir(parents=True, exist_ok=True)
    big.save(path, optimize=True)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stamp", help="also write docs/art/previews/<stamp>_F2_shell-cursor-pause-sweep.html")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--catalan", action="store_true",
                    help="P6: write only the Catalan P2 plaque (work/), and with --stamp the "
                         "EN/RU/CA preview docs/art/previews/<stamp>_P6_pause-ca.png")
    ap.add_argument("--install", action="store_true",
                    help="with --catalan: also write assets/localized/textures/M_PAUSE.ca.png")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows console is cp1252
    if args.catalan:
        files = catalan_pause(args.out, PAUSE_LOCALIZED_DIR if args.install else None)
        for p in files.values():
            print(f"wrote {p}")
        if args.stamp:
            print(f"wrote {catalan_preview(PREVIEW_DIR / f'{args.stamp}_P6_pause-ca.png')}")
        return
    manifest = build(args.out)
    print(f"{len(manifest['files'])} files in {args.out}")
    if args.stamp:
        print(sheet(args.stamp, args.out))


if __name__ == "__main__":
    main()
