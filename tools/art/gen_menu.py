#!/usr/bin/env python3
"""Soviet Doom — the menu font SDMENU (D22 built, for D31) and its preview.

Why this exists
---------------
D22 (ratified 2026-10-13) says the English build draws five Latin capitals
with Cyrillic letterforms, level 2: R->Я, N->И, E->Э, W->Ш, A->Д. It is a
FONT-level mapping: LANGUAGE keeps correct English, the font draws the
letters differently. Until this module it was decided and built nowhere.

D31 (2026-10-13) puts it where the CEO asked for it first: the main menu and
the skill screen's headers become text (`TextItem` / `StaticText` in
MENUDEF) drawn in one folder font, `fonts/sdmenu/`, instead of Freedoom's
red graphics (debt T12).

What the font is
----------------
`assets/fonts/bigfont/` (alphabet C "Mashina", D24, cap 11 + 1 px shadow,
line 16) with exactly five files replaced:

    0052 R  <- the drawing of Я (U+042F)
    004E N  <- the drawing of И (U+0418)
    0045 E  <- the drawing of Э (U+042D)
    0057 W  <- the drawing of Ш (U+0428)
    0041 A  <- the drawing of Д (U+0414)

The five replacement glyphs are rendered by `gen_font.glyph_image()` from
gen_font's own stroke code for the Cyrillic letter, so they follow the same
stroke rules as every other glyph; they come out byte-identical to the
installed Cyrillic files, and the build asserts it. Every other file is
copied from `assets/fonts/bigfont/` byte for byte, so the menu font can never
drift from the alphabet the rest of the game uses.

One font serves both languages: Russian strings use Cyrillic code points,
which this font leaves untouched, so `[ru]` reads as real Russian.

The exceptions of docs/product/LANGUAGE-SWITCH.md (proper nouns, calibres,
key prompts keep Latin) are honoured by WHERE the font is used, not inside
it: SDMENU is only named by the menu descriptors, whose strings contain none
of those. BigFont and SmallFont, which print level names, weapon tags and
pickups, are not touched.

Nothing here edits gen_font.py. Output goes to work/art/menu/; `--install`
copies the built font to assets/fonts/sdmenu/ (approved for in-engine trial
by the CEO 2026-10-13, D31).

Usage
-----
    .venv/Scripts/python.exe tools/art/gen_menu.py                 # font + sheet
    .venv/Scripts/python.exe tools/art/gen_menu.py --install       # + assets/fonts/sdmenu/
    .venv/Scripts/python.exe tools/art/gen_menu.py --stamp 2026-10-13_1552
"""
from __future__ import annotations

import argparse
import re
import shutil
import struct
import sys
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

FONT_NAME = "sdmenu"                       # MENUDEF: Font "SDMENU" (names are case-insensitive)
BIGFONT_DIR = PROJECT_ROOT / "assets" / "fonts" / "bigfont"
INSTALL_DIR = PROJECT_ROOT / "assets" / "fonts" / FONT_NAME
OUT_ROOT = PROJECT_ROOT / "work" / "art" / "menu"
OUT_FONT = OUT_ROOT / FONT_NAME
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
TITLEPIC = PROJECT_ROOT / "assets" / "graphics" / "shell" / "TITLEPIC.png"
M_DOOM = PROJECT_ROOT / "assets" / "graphics" / "shell" / "M_DOOM.png"
SMALLFONT_DIR = PROJECT_ROOT / "assets" / "fonts" / "defsmallfont"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
MENUDEF = PROJECT_ROOT / "src" / "lumps" / "MENUDEF"

# D22, level 2 (docs/PRD.md; docs/product/LANGUAGE-SWITCH.md). Latin -> the
# Cyrillic letter whose drawing it takes. Nothing else is substituted.
SUBSTITUTION = {"R": "Я", "N": "И", "E": "Э", "W": "Ш", "A": "Д"}


def glyph_file(ch: str) -> str:
    return f"{ord(ch):04X}.png"


def reads_as(text: str) -> str:
    """What a string looks like in SDMENU, for labels and tests. The font
    has capitals only and the engine draws lowercase with them (NOT
    VERIFIED for this font; it is how bigfont already behaves), hence
    upper()."""
    return text.upper().translate(str.maketrans(SUBSTITUTION))


# ------------------------------------------------------------------- font
def build_font(out_dir: Path | None = None, source_dir: Path | None = None) -> dict:
    """Copy bigfont, then write the five substituted glyphs, rendered by
    gen_font from the Cyrillic letters' stroke code. The defaults (OUT_FONT,
    BIGFONT_DIR) are looked up when called, not when the module is imported,
    so patching the module constants or passing a path both redirect it."""
    import gen_font  # lazy: it opens system label fonts at import time

    out_dir = OUT_FONT if out_dir is None else out_dir
    source_dir = BIGFONT_DIR if source_dir is None else source_dir

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.iterdir():
        if old.is_file():
            old.unlink()
    for src in sorted(source_dir.iterdir()):
        shutil.copyfile(src, out_dir / src.name)
    style = gen_font.STYLES["C"]                  # the installed alphabet (D24)
    replaced = {}
    for latin, cyr in SUBSTITUTION.items():
        img = gen_font.glyph_image(cyr, style, "big")
        dst = out_dir / glyph_file(latin)
        img.save(dst)
        # The drawing must be the very glyph the game already shows for the
        # Cyrillic letter; anything else would be a sixth, unapproved form.
        if dst.read_bytes() != (source_dir / glyph_file(cyr)).read_bytes():
            raise RuntimeError(f"{dst.name}: gen_font's {cyr} differs from {source_dir / glyph_file(cyr)}")
        replaced[f"U+{ord(latin):04X} {latin}"] = f"U+{ord(cyr):04X} {cyr}"
    return {"font": FONT_NAME, "files": len(list(out_dir.iterdir())), "replaced": replaced}


def install(src: Path | None = None, dst: Path | None = None) -> Path:
    """Copy the built font over INSTALL_DIR. Defaults are resolved at call time."""
    src = OUT_FONT if src is None else src
    dst = INSTALL_DIR if dst is None else dst
    dst.mkdir(parents=True, exist_ok=True)
    for old in dst.iterdir():
        old.unlink()
    for f in sorted(src.iterdir()):
        shutil.copyfile(f, dst / f.name)
    return dst


# --------------------------------------------------------------- the sheet
def menudef_pair(menu: str, keyword: str, path: Path | None = None) -> tuple[int, int]:
    """The first `<keyword> x, y` line inside LISTMENU "<menu>" of the shipped
    MENUDEF. The suggested skill layout is read from there so the mock can
    never drift from what the game draws (B4)."""
    src = MENUDEF if path is None else path
    body = re.search(r'^LISTMENU\s+"%s"\s*\{(.*?)^\}' % re.escape(menu),
                     src.read_text(encoding="utf-8"), re.S | re.M)
    if body is None:
        raise ValueError(f'LISTMENU "{menu}" not found in {src}')
    m = re.search(r"^\s*%s\s+(-?\d+)\s*,\s*(-?\d+)" % re.escape(keyword), body.group(1), re.M)
    if m is None:
        raise ValueError(f'no "{keyword} x, y" line in LISTMENU "{menu}" of {src}')
    return int(m.group(1)), int(m.group(2))


# Engine geometry (src/lumps/MENUDEF, docs/engine/MOD-SPEC.md 6.6).
SCREEN = (320, 200)
LOGO_POS = (60, 0)
MAIN_POS = (97, 72)            # LISTMENU "MainMenu" Position
MAIN_SPACING = 16
SKILL_POS = (48, 63)           # LISTMENU "SkillMenu" Position
SKILL_SPACING = 12
STOCK_NEWG = (96, 14)          # where M_NEWG / M_SKILL are drawn today
STOCK_SKILL = (54, 38)
# Suggested skill screen (logo kept, one header under it): read from MENUDEF's
# LISTMENU "SkillMenu" (StaticText 32, 70 / Position 32, 90 at the time of B4).
SUGGEST_HEADER = menudef_pair("SkillMenu", "StaticText")
SUGGEST_ITEMS = menudef_pair("SkillMenu", "Position")
SELECTOR_OFFSET = (-32, -5)    # Doom's DEFAULTLISTMENU: Selector "M_SKULL1", -32, -5
# Menu dim, measured on the engine's own screenshot
# docs/qa/evidence/2026-10-13_1007_F2_mainmenu-ru.png against TITLEPIC.png:
# out = DIM_KEEP * in + DIM_ADD on 11 sample points (e.g. (193,44,37) ->
# (119,41,18); black -> (25,20,1)). The logo and the items are drawn undimmed.
DIM_KEEP = 0.487
DIM_ADD = (25, 20, 1)
ZOOM = 2

# Strings proposed for LANGUAGE (mod-engineer owns the lump; these are the
# art director's proposal and what the sheet draws).
MAIN_ITEMS = [  # (id, English, Russian)
    ("SD_MNU_NEWGAME", "New Game", "Новая игра"),
    ("SD_MNU_OPTIONS", "Options", "Настройки"),
    ("SD_MNU_LOADGAME", "Load Game", "Загрузить"),
    ("SD_MNU_SAVEGAME", "Save Game", "Сохранить"),
    ("SD_MNU_QUITGAME", "Quit Game", "Выход"),
]
SKILL_HEAD = ("SD_MNU_CHOOSESKILL", "Choose difficulty", "Выберите сложность")
SKILL_ITEMS = {  # src/lumps/LANGUAGE, SD_SKILL_1..5
    "en": ["I am still a Pioneer", "I have seen worse winters", "Not one step back",
           "No pasaran, comrades", "Hero of the Soviet Union, posthumously"],
    "ru": ["Я ещё пионер", "Бывали зимы и похуже", "Ни шагу назад",
           "Но пасаран, товарищи", "Герой Советского Союза, посмертно"],
}


def _colours():
    import artlib
    return {
        # Approximations of GZDoom's font colour translation (NOT VERIFIED:
        # the engine maps each glyph colour by luminance onto the named
        # text colour's ramp; these are the palette colours nearest in role).
        "cream": artlib.ramp_colour("cream_yellow", 0.92),
        "gold": artlib.ramp_colour("hazard_yellow", 0.88),
        "red": artlib.ramp_colour("flag_red", 0.95),
        "shadow": artlib.ramp_colour("concrete_cold", 0.04),
    }


class FolderFont:
    """Draws text with a folder font's PNGs, recoloured the way a menu Font
    colour would: the brightest glyph colour becomes `body`, darker ones
    `shadow`."""

    def __init__(self, folder: Path):
        from PIL import Image
        self.folder = folder
        self.cache = {}
        self.Image = Image

    def glyph(self, ch: str):
        ch = ch.upper()
        if ch not in self.cache:
            p = self.folder / glyph_file(ch)
            self.cache[ch] = self.Image.open(p).convert("RGBA") if p.is_file() else None
        return self.cache[ch]

    def width(self, text: str) -> int:
        return sum(g.width for g in map(self.glyph, text) if g is not None)

    def render(self, text: str, body, shadow):
        import numpy as np
        Image = self.Image
        gl = [g for g in map(self.glyph, text) if g is not None]
        h = max((g.height for g in gl), default=1)
        out = Image.new("RGBA", (max(self.width(text), 1), h), (0, 0, 0, 0))
        x = 0
        for g in gl:
            out.alpha_composite(g, (x, 0))
            x += g.width
        a = np.asarray(out).copy()
        on = a[..., 3] > 0
        lum = a[..., :3].astype(int).sum(-1)
        bright = on & (lum >= lum[on].max() * 0.5) if on.any() else on
        a[bright, :3] = body
        a[on & ~bright, :3] = shadow
        return Image.fromarray(a, "RGBA")


def _skull():
    """M_SKULL1 from Freedoom's IWAD, the menu cursor the engine still draws
    (it is not ours; shown so the mock is honest). None if the IWAD is not
    in this clone."""
    if not IWAD.is_file():
        return None
    from PIL import Image
    data = IWAD.read_bytes()
    n, off = struct.unpack_from("<4xii", data, 0)
    lumps = {}
    for i in range(n):
        pos, size, name = struct.unpack_from("<ii8s", data, off + 16 * i)
        lumps[name.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
    if "M_SKULL1" not in lumps or "PLAYPAL" not in lumps:
        return None
    pp = lumps["PLAYPAL"][0]
    pal = [tuple(data[pp + 3 * i: pp + 3 * i + 3]) for i in range(256)]
    p0 = lumps["M_SKULL1"][0]
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


def _dimmed_title():
    import numpy as np
    from PIL import Image
    rgb = np.asarray(Image.open(TITLEPIC).convert("RGB")).astype(float)
    out = rgb * DIM_KEEP + np.array(DIM_ADD, float)
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype("uint8"), "RGB").convert("RGBA")


def _put_text(screen, font, text, pos, body, shadow, overflow: list):
    img = font.render(text, body, shadow)
    if pos[0] + img.width > SCREEN[0]:
        overflow.append(f"{text!r} ends at x={pos[0] + img.width}")
    screen.alpha_composite(img, pos)


def _put_selector(screen, skull, item_pos):
    if skull is None:
        return
    img, (lo, to) = skull
    x = item_pos[0] + SELECTOR_OFFSET[0] - lo
    y = item_pos[1] + SELECTOR_OFFSET[1] - to
    screen.alpha_composite(img, (max(x, 0), max(y, 0)))


def mock_main(lang: str, menu_font, skull, col):
    from PIL import Image
    s = _dimmed_title()
    s.alpha_composite(Image.open(M_DOOM).convert("RGBA"), LOGO_POS)
    over = []
    for i, (_id, en, ru) in enumerate(MAIN_ITEMS):
        pos = (MAIN_POS[0], MAIN_POS[1] + i * MAIN_SPACING)
        body = col["gold"] if i == 0 else col["cream"]       # item 0 selected
        _put_text(s, menu_font, en if lang == "en" else ru, pos, body, col["shadow"], over)
    _put_selector(s, skull, MAIN_POS)
    return s, over


def mock_skill(lang: str, layout: str, menu_font, small_font, skull, col):
    from PIL import Image
    s = _dimmed_title()
    over = []
    head = SKILL_HEAD[1] if lang == "en" else SKILL_HEAD[2]
    newg = MAIN_ITEMS[0][1] if lang == "en" else MAIN_ITEMS[0][2]
    if layout == "stock":
        _put_text(s, menu_font, newg, STOCK_NEWG, col["cream"], col["shadow"], over)
        _put_text(s, menu_font, head, STOCK_SKILL, col["cream"], col["shadow"], over)
        items = SKILL_POS
    else:
        s.alpha_composite(Image.open(M_DOOM).convert("RGBA"), LOGO_POS)
        _put_text(s, menu_font, head, SUGGEST_HEADER, col["cream"], col["shadow"], over)
        items = SUGGEST_ITEMS
    for i, name in enumerate(SKILL_ITEMS[lang]):
        pos = (items[0], items[1] + i * SKILL_SPACING)
        body = col["gold"] if i == 2 else col["red"]           # rung 3 selected
        _put_text(s, small_font, name, pos, body, col["shadow"], over)
    _put_selector(s, skull, (items[0], items[1] + 2 * SKILL_SPACING))
    return s, over


def sheet(stamp: str, font_dir: Path | None = None, out_dir: Path | None = None,
          mock_dir: Path | None = None) -> Path:
    """The menu sweep PNG, plus MENUMOCK_main_<lang>.png. Defaults are resolved
    at call time. With no `out_dir` the sweep goes to PREVIEW_DIR and the two
    mocks to OUT_ROOT (as always); with an explicit `out_dir` everything goes
    there unless `mock_dir` says otherwise (B5). Missing folders are created."""
    from PIL import Image, ImageDraw, ImageFont
    import artlib

    font_dir = OUT_FONT if font_dir is None else font_dir
    if mock_dir is None:
        mock_dir = OUT_ROOT if out_dir is None else out_dir
    out_dir = PREVIEW_DIR if out_dir is None else out_dir

    col = _colours()
    menu_font = FolderFont(font_dir)
    small_font = FolderFont(SMALLFONT_DIR)
    skull = _skull()
    f_title = ImageFont.truetype(artlib.FONT_POSTER, 30)
    f_lab = ImageFont.truetype(artlib.FONT_SMALL, 15)
    f_sm = ImageFont.truetype(artlib.FONT_SMALL, 13)
    bg = artlib.ramp_colour("concrete_cold", 0.12)
    panel = artlib.ramp_colour("concrete_cold", 0.20)
    label = artlib.ramp_colour("concrete_cold", 0.78)
    gold = artlib.ramp_colour("hazard_yellow", 0.80)
    accent = artlib.ramp_colour("flag_red", 0.78)

    cw, ch = SCREEN[0] * ZOOM, SCREEN[1] * ZOOM
    pad = 28
    W = pad * 3 + cw * 2 + SCREEN[0] + 20
    rows = [("MAIN MENU", "main"), ("SKILL SCREEN, headers at today's positions (M_NEWG 96,14 / M_SKILL 54,38)", "stock"),
            (f"SKILL SCREEN, suggested (MENUDEF): logo kept at 60,0, one header at "
             f"{SUGGEST_HEADER[0]},{SUGGEST_HEADER[1]}, rungs from {SUGGEST_ITEMS[0]},{SUGGEST_ITEMS[1]}", "suggest")]
    H = 112 + 260 + len(rows) * (ch + 70) + 300
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 86], fill=panel)
    d.rectangle([0, 84, W, 86], fill=accent)
    d.text((pad, 14), "SOVIET DOOM · MENU FONT SDMENU · TREATMENT B (D31) · ENGLISH AND RUSSIAN",
           font=f_title, fill=gold)
    d.text((pad + 2, 56), "Reference for the in-engine trial: compare with the engine screenshot. "
                          "TITLEPIC dimmed as the engine dims it, M_DOOM at (60,0), 1× and 2×.",
           font=f_lab, fill=label)
    d.text((W - 220, 62), stamp, font=f_sm, fill=label)

    # --- the substitution itself
    y = 104
    d.text((pad, y), "D22 LEVEL 2 IN THE FONT  ·  only these five files differ from assets/fonts/bigfont/  "
                     "·  1× and 6×", font=f_lab, fill=gold)
    y += 26
    x = pad
    for latin, cyr in SUBSTITUTION.items():
        g0 = menu_font.render(latin, col["cream"], col["shadow"])
        z = g0.resize((g0.width * 6, g0.height * 6), Image.Resampling.NEAREST)
        d.text((x, y), f"{latin} U+{ord(latin):04X}  ->  drawn as {cyr}", font=f_sm, fill=label)
        img.paste(g0, (x, y + 22), g0)
        img.paste(z, (x + g0.width + 10, y + 22), z)
        x += max(z.width + g0.width + 40, 190)
    y += 22 + 12 * 6 + 14
    proof = [("en", en) for _i, en, _r in MAIN_ITEMS] + [("en", SKILL_HEAD[1])]
    line = "   ".join(f"{t.upper()} -> {reads_as(t)}" for _l, t in proof)
    d.text((pad, y), "reads as:  " + line, font=f_sm, fill=label)
    y += 20
    d.text((pad, y), "Russian strings use Cyrillic code points and are untouched: НОВАЯ ИГРА stays НОВАЯ ИГРА.",
           font=f_sm, fill=label)
    y += 34

    overflow_all = []
    for title, kind in rows:
        d.rectangle([pad, y, W - pad, y + 2], fill=accent)
        y += 10
        d.text((pad, y), title, font=f_lab, fill=gold)
        y += 24
        x = pad
        for lang in ("en", "ru"):
            if kind == "main":
                scr, over = mock_main(lang, menu_font, skull, col)
            else:
                scr, over = mock_skill(lang, kind, menu_font, small_font, skull, col)
            overflow_all += [f"{kind}/{lang}: {o}" for o in over]
            z = scr.resize((cw, ch), Image.Resampling.NEAREST)
            d.text((x, y), "ENGLISH (D22 letterforms)" if lang == "en" else "RUSSIAN (real Cyrillic)",
                   font=f_sm, fill=label)
            img.paste(z.convert("RGB"), (x, y + 18))
            if lang == "en":
                img.paste(scr.convert("RGB"), (pad * 3 + cw * 2 + 10, y + 18))
                d.text((pad * 3 + cw * 2 + 10, y + 18 + SCREEN[1] + 6), "1× (English)", font=f_sm, fill=label)
            x += cw + pad
        y += ch + 40

    notes = [
        "Font colours are approximations of a MENUDEF Font colour translation (cream items, gold selected); "
        "the engine's own translation is NOT VERIFIED until the engine pass.",
        "Cursor: Freedoom's M_SKULL1 at the default selector offset (-32,-5), read from iwads/freedoom2.wad. "
        "It is not ours either (outside T12).",
        "Skill rungs are SmallFont (our defsmallfont, unchanged: D22 is not applied to running text here).",
        "Treatment C (painted poster-style menu graphics, one set per language) is parked for docs/ICEBOX.md "
        "by the CEO's decision of 2026-10-13.",
        "Width check against the 320-px screen: " + ("; ".join(overflow_all) if overflow_all else "every line fits."),
    ]
    for n in notes:
        d.text((pad, y), "· " + n, font=f_sm, fill=label)
        y += 20
    img = img.crop((0, 0, W, y + 16))
    path = out_dir / f"{stamp}_F2_menu-sweep.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    mock_dir.mkdir(parents=True, exist_ok=True)
    for lang in ("en", "ru"):
        mock_main(lang, menu_font, skull, col)[0].convert("RGB").save(mock_dir / f"MENUMOCK_main_{lang}.png")
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stamp", default="PREVIEW")
    ap.add_argument("--install", action="store_true",
                    help="copy the built font to assets/fonts/sdmenu/ (D31 trial)")
    ap.add_argument("--no-sheet", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows console is cp1252
    report = build_font()
    print(report)
    if args.install:
        print("installed:", install())
    if not args.no_sheet:
        print(sheet(args.stamp))


if __name__ == "__main__":
    main()
