"""The CEO's preview of V3 B1 and B3 (ADR 013):
docs/art/previews/2026-10-23_V3_ops-map-medals.png, everything at x2.

  rows 1-3  the nine positions of the operations map: position 1 is the
            stats page after MAP01 (the gold pulse on Zarya-7); positions
            2-9 are the "Entering" page before each map (the new red arrow,
            the blinking ring on the next site), each composed by READING the
            generated script SDOPSCR the way the engine draws it
            (gen_ops_map.visible), with the engine's text mocked in our fonts
  row 4     the stats page over the map (Doom's figures, mocked), and the
            awards page at the end of episode 2 in English and Russian
  row 5     the five awards at x4, earned and not earned, with their names
            in the three languages

Text is drawn ONLY with the mod's approved bitmap fonts (v3lib.BitmapFont:
assets/fonts/bigfont and defsmallfont), never a system font (D27). Font
colours are an approximation of the engine's translations; the layout of
the awards page is SD_StatusScreen's (zscript/sd/status_screen.zs), whose
constants tests/test_awards.py compares with AWARDS_LAYOUT below.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import gen_medals  # noqa: E402
import gen_ops_map  # noqa: E402
import v3lib  # noqa: E402

LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
ZOOM = 2
CLOSEUP = 4
GAP = 16
LABEL_H = 22
BACKDROP = (18, 18, 22, 255)
LABEL = (232, 220, 170)
GOLD = (236, 191, 70)
RED = (220, 50, 42)
CREAM = (230, 218, 163)
GREY = (150, 150, 150)
DARKGREY = (90, 90, 90)
WHITE = (240, 240, 240)

# SD_StatusScreen's awards page, in its 320x200 space (the same names as the
# ZScript constants, without the SD_ prefix).
AWARDS_LAYOUT = {
    "TITLE_Y": 3, "EPISODE_Y": 21, "SUMMARY_LABEL_Y": 32, "SUMMARY_VALUE_Y": 41,
    "SUMMARY_COLUMNS": 4, "SUMMARY_COLUMN_W": 72, "ROWS_Y": 51, "ROW_H": 29,
    "ICON_X": 22, "TEXT_X": 54, "TEXT_RIGHT": 314, "NAME_DY": 3, "RULE_DY": 13,
    "RULE_LINE_H": 9, "RULE_MAX_LINES": 2, "SCREEN_W": 320,
}
DIM_AMOUNT = 0.72

# The stats page's places (gzdoom.pk3 statscreen.zs / statscreen_sp.zs).
SP_STATSX, SP_STATSY, SP_TIMEX, SP_TIMEY, TITLEY = 50, 50, 8, 200 - 32, 5


# -------------------------------------------------------------- strings
def language() -> dict[str, dict[str, str]]:
    """LANGUAGE -> {code: {id: text}} (the test suite's parser, simplified)."""
    sections: dict[str, dict[str, str]] = {}
    current: list[str] = []
    for raw in LANGUAGE.read_text(encoding="utf-8").splitlines():
        line = re.sub(r'^((?:[^"/]|"[^"]*"|/(?!/))*)//.*$', r"\1", raw).strip()
        if not line:
            continue
        m = re.match(r"^\[([^\]]+)\]$", line)
        if m:
            current = m.group(1).split()
            for c in current:
                sections.setdefault(c, {})
            continue
        m = re.match(r'^([A-Za-z0-9_]+)\s*=\s*"(.*)";?$', line)
        if m and current:
            for c in current:
                sections[c][m.group(1)] = m.group(2)
    return sections


def wrap(font, text: str, width: int) -> list[str]:
    """Word wrap like Font.BreakLines (spaces only, a too-long word stays whole)."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if font.width(trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ the frames
class Pictures:
    """The generated lumps as PIL images with their grAb offsets."""

    def __init__(self):
        import tempfile
        from PIL import Image
        self.blobs = {}
        with tempfile.TemporaryDirectory() as tmp:          # the preview writes nothing but the sheet
            built = gen_ops_map.build(Path(tmp))
        for name, blob in built.items():
            if name.endswith(".png"):
                self.blobs[name[:-4]] = blob
        for lump, drawer in gen_medals.AWARDS:
            self.blobs[lump] = v3lib.png_bytes(gen_medals.render(drawer))
        self.images = {k: Image.open(io.BytesIO(v)).convert("RGBA") for k, v in self.blobs.items()}
        self.grabs = {k: v3lib.read_grab(v) or (0, 0) for k, v in self.blobs.items()}
        self.script = gen_ops_map.parse_script(gen_ops_map.script_text())

    def draw(self, canvas, lump, x, y):
        gx, gy = self.grabs[lump]
        canvas.alpha_composite(self.images[lump], (x - gx, y - gy))


def map_page(pics: Pictures, page: str, current: str, nxt: str, frame=0):
    from PIL import Image
    canvas = Image.new("RGBA", (gen_ops_map.WIDTH, gen_ops_map.HEIGHT), (0, 0, 0, 255))
    visited = gen_ops_map.MAPS[:gen_ops_map.MAPS.index(current) + 1]
    for lump, x, y in gen_ops_map.visible(pics.script, page, current, nxt, visited, True, frame):
        pics.draw(canvas, lump, x, y)
    return canvas


def centred(font, canvas, y, text, colour, cx=160):
    font.draw(canvas, cx - font.width(text) // 2, y, text, colour)


def entering_text(canvas, big, name):
    centred(big, canvas, TITLEY + 2, "Entering", RED)
    centred(big, canvas, TITLEY + 2 + big.height + 4, name, RED)


def stats_text(canvas, big, name, figures):
    lh = big.height * 3 // 2
    centred(big, canvas, TITLEY + 2, name, RED)
    centred(big, canvas, TITLEY + 2 + big.height + 4, "Finished", RED)
    rows = (("Kills", figures[0]), ("Items", figures[1]), ("Secret", figures[2]))
    for i, (label, value) in enumerate(rows):
        big.draw(canvas, SP_STATSX, SP_STATSY + i * lh, label, RED)
        big.draw(canvas, 320 - SP_STATSX - big.width(value), SP_STATSY + i * lh, value, RED)
    big.draw(canvas, SP_TIMEX, SP_TIMEY, "Time", RED)
    big.draw(canvas, 160 - SP_TIMEX - big.width(figures[3]), SP_TIMEY, figures[3], RED)
    big.draw(canvas, 160 + SP_TIMEX, SP_TIMEY, "Par", RED)
    big.draw(canvas, 320 - SP_TIMEX - big.width(figures[4]), SP_TIMEY, figures[4], RED)


def awards_page(pics: Pictures, big, small, strings, episode, figures, earned):
    """The awards page as SD_StatusScreen draws it (layout AWARDS_LAYOUT)."""
    import numpy as np
    from PIL import Image
    L = AWARDS_LAYOUT
    last = gen_ops_map.MAPS[episode * 3 - 1]
    canvas = map_page(pics, "stats", last, "")
    arr = np.asarray(canvas, dtype=np.float64).copy()
    arr[..., :3] *= (1 - DIM_AMOUNT)
    canvas = Image.fromarray(arr.astype(np.uint8), "RGBA")
    ep_ids = {1: "SD_EP01_NAME", 2: "SD_EP03_NAME", 3: "SD_EP04_NAME"}
    centred(big, canvas, L["TITLE_Y"], strings["SD_AWARDS_TITLE"], GOLD)
    centred(small, canvas, L["EPISODE_Y"], strings[ep_ids[episode]], CREAM)
    labels = ("SD_AWARDS_KILLS", "SD_AWARDS_SECRETS", "SD_AWARDS_TIME", "SD_AWARDS_PAR")
    x0 = L["SCREEN_W"] // 2 - 2 * L["SUMMARY_COLUMN_W"] + L["SUMMARY_COLUMN_W"] // 2
    for c in range(L["SUMMARY_COLUMNS"]):
        cx = x0 + c * L["SUMMARY_COLUMN_W"]
        centred(small, canvas, L["SUMMARY_LABEL_Y"], strings[labels[c]], GREY, cx)
        centred(small, canvas, L["SUMMARY_VALUE_Y"], figures[c], WHITE, cx)
    names = ("COURAGE", "REDSTAR", "REDBANNER", "PATRIOTIC", "HERO")
    for i, (lump, _) in enumerate(gen_medals.AWARDS):
        y = L["ROWS_Y"] + i * L["ROW_H"]
        icon = pics.images[lump]
        if not earned[i]:
            a = np.asarray(icon, dtype=np.float64).copy()
            a[..., :3] *= 1 - 170 / 255
            icon = Image.fromarray(a.astype(np.uint8), "RGBA")
        canvas.alpha_composite(icon, (L["ICON_X"], y))
        small.draw(canvas, L["TEXT_X"], y + L["NAME_DY"], strings[f"SD_MEDAL_{names[i]}_NAME"],
                   GOLD if earned[i] else DARKGREY)
        rule = wrap(small, strings[f"SD_MEDAL_{names[i]}_RULE"], L["TEXT_RIGHT"] - L["TEXT_X"])
        for k, line in enumerate(rule[:L["RULE_MAX_LINES"]]):
            small.draw(canvas, L["TEXT_X"], y + L["RULE_DY"] + k * L["RULE_LINE_H"], line,
                       CREAM if earned[i] else GREY)
    return canvas


# ---------------------------------------------------------------- sheet
def write_sheet(path: Path) -> None:
    from PIL import Image
    pics = Pictures()
    big = v3lib.BitmapFont("bigfont")
    small = v3lib.BitmapFont("defsmallfont")
    strings = language()
    en, ru = strings["default"], strings["ru"]
    names = [en[f"SD_{m}_NAME"] for m in gen_ops_map.MAPS]

    cells = []
    first = map_page(pics, "stats", "MAP01", "MAP02")
    cells.append(("1  MAP01 Zarya-7, stats page: the gold pulse is where you are", first))
    for i in range(1, 9):
        cur, nxt = gen_ops_map.MAPS[i - 1], gen_ops_map.MAPS[i]
        page = map_page(pics, "entering", cur, nxt)
        entering_text(page, big, names[i])
        cells.append((f"{i + 1}  entering {nxt}: the new red arrow, the ring blinks", page))
    stats = map_page(pics, "stats", "MAP05", "MAP06")
    stats_text(stats, big, names[4], ("82%", "64%", "100%", "5:12", "5:30"))
    cells.append(("stats page over the map (MAP05; Doom's text, mocked)", stats))
    figures = ("82%", "7/9", "16:40", "17:30")
    earned = (True, True, False, True, False)
    cells.append(("awards page, episode 2 (English)",
                  awards_page(pics, big, small, en, 2, figures, earned)))
    cells.append(("awards page, episode 2 (Russian)",
                  awards_page(pics, big, small, ru, 2, figures, earned)))

    fw, fh = gen_ops_map.WIDTH * ZOOM, gen_ops_map.HEIGHT * ZOOM
    cols = 3
    rows = (len(cells) + cols - 1) // cols
    band_h = closeup_height(small)
    width = cols * fw + (cols + 1) * GAP
    height = 40 + rows * (fh + LABEL_H + GAP) + band_h + GAP
    sheet = Image.new("RGBA", (width, height), BACKDROP)
    small.draw(sheet, GAP, 12, "SOVIET DOOM V3 - OPERATIONS MAP (B1) AND AWARDS (B3), ADR 013 - ALL AT X2, PROPOSAL", LABEL, 2)
    for k, (label, img) in enumerate(cells):
        r, c = divmod(k, cols)
        x = GAP + c * (fw + GAP)
        y = 40 + r * (fh + LABEL_H + GAP)
        small.draw(sheet, x, y, label, LABEL)
        sheet.alpha_composite(img.resize((fw, fh), Image.Resampling.NEAREST), (x, y + LABEL_H))
    closeup(sheet, pics, small, strings, 40 + rows * (fh + LABEL_H + GAP))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path, optimize=True)


def closeup_height(small) -> int:
    return LABEL_H + gen_medals.HEIGHT * CLOSEUP + GAP + 5 * (small.height + 2) + GAP


def closeup(sheet, pics, small, strings, top):
    """Row 5: each award at x4, earned and not, with its three names."""
    import numpy as np
    from PIL import Image
    small.draw(sheet, GAP, top, "the five awards at x4 (earned / not earned) and their names in EN, RU, CA", LABEL)
    names = ("COURAGE", "REDSTAR", "REDBANNER", "PATRIOTIC", "HERO")
    col_w = (sheet.width - 2 * GAP) // 5
    for i, (lump, _) in enumerate(gen_medals.AWARDS):
        x = GAP + i * col_w
        y = top + LABEL_H
        icon = pics.images[lump]
        big_icon = icon.resize((icon.width * CLOSEUP, icon.height * CLOSEUP), Image.Resampling.NEAREST)
        sheet.alpha_composite(big_icon, (x, y))
        a = np.asarray(big_icon, dtype=np.float64).copy()
        a[..., :3] *= 1 - 170 / 255
        sheet.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"), (x + big_icon.width + 8, y))
        ty = y + big_icon.height + 8
        for code, colour in (("default", GOLD), ("ru", CREAM), ("ca", WHITE)):
            small.draw(sheet, x, ty, strings[code][f"SD_MEDAL_{names[i]}_NAME"], colour)
            ty += small.height + 2
        small.draw(sheet, x, ty, lump, GREY)
