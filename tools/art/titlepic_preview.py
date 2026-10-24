#!/usr/bin/env python3
"""The CEO's sheet for the epic title screen (D126): docs/art/previews/2026-10-24_P4_titlepic.html.

    .venv/Scripts/python.exe tools/art/titlepic_preview.py     # after gen_titlepic.py

Self-contained (images embedded as base64 PNG at 1x, scaled by the browser
with nearest-neighbour). Shows, at x3 and at the 4:3 the engine displays a
320x200 screen at (960x720): today's TITLEPIC, variant A (the D12 symbol on
the Reich's armbands) and B (Gemini's empty square), the armbands close up,
the logo alternative with today's black plate, the 16:9 pillarbox, and the
main menu as the engine draws it over the title (background dimmed as
measured in gen_menu, M_DOOM and the SDMENU items undimmed) in English,
Russian and Catalan. The menu simulation reuses gen_menu's own drawing code.
"""
from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))
import gen_titlepic as gt  # noqa: E402

MENU_LANG = {   # src/lumps/LANGUAGE, SD_MNU_* (ReadThis off: the default)
    "en": ["NEW GAME", "OPTIONS", "LOAD GAME", "SAVE GAME", "QUIT GAME"],
    "ru": ["НОВАЯ ИГРА", "НАСТРОЙКИ", "ЗАГРУЗИТЬ", "СОХРАНИТЬ", "ВЫХОД"],
    "ca": ["NOVA PARTIDA", "OPCIONS", "CARREGA PARTIDA", "DESA PARTIDA", "SURT DEL JOC"],
}
ARM_ZOOM = 6
ARM_BOXES = {"front": (110, 166, 150, 200), "left": (16, 172, 56, 200)}   # screen px round the two armbands


def b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def menu_mock(title: Path, logo: Path, lang: str) -> Image.Image:
    """gen_menu.mock_main over another title and logo, with LANGUAGE's strings."""
    import gen_menu as gm
    font = gm.FolderFont(gm.PROJECT_ROOT / "assets" / "fonts" / "sdmenu")
    col = gm._colours()
    skull = gm._skull()
    rgb = np.asarray(Image.open(title).convert("RGB")).astype(float)
    s = Image.fromarray(np.clip(rgb * gm.DIM_KEEP + np.array(gm.DIM_ADD, float) + 0.5, 0, 255)
                        .astype("uint8"), "RGB").convert("RGBA")
    s.alpha_composite(Image.open(logo).convert("RGBA"), gm.LOGO_POS)
    over: list = []
    for i, text in enumerate(MENU_LANG[lang]):
        pos = (gm.MAIN_POS[0], gm.MAIN_POS[1] + i * gm.MAIN_SPACING)
        gm._put_text(s, font, text, pos, col["gold"] if i == 0 else col["cream"], col["shadow"], over)
    gm._put_selector(s, skull, gm.MAIN_POS)
    return s.convert("RGB")


def armbands(img: Path) -> list[Image.Image]:
    im = Image.open(img).convert("RGB")
    out = []
    for box in ARM_BOXES.values():
        c = im.crop(box)
        out.append(c.resize((c.width * ARM_ZOOM, int(c.height * ARM_ZOOM * 1.2)), Image.NEAREST))
    return out


CSS = """
:root{--bg:#16130f;--panel:#221d17;--ink:#efe3c4;--mute:#b3a68a;--gold:#dfb923;--red:#c8322a;--line:#3a3127}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif}
main{max-width:1000px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:36px 0 8px;border-top:1px solid var(--line);padding-top:20px}
p,li{color:var(--mute);max-width:72ch}b,strong{color:var(--ink)}code{color:var(--gold)}
.shot{display:block;width:100%;max-width:960px;aspect-ratio:4/3;image-rendering:pixelated;image-rendering:crisp-edges;background:#000}
.half{display:grid;grid-template-columns:1fr 1fr;gap:12px}.half .shot{max-width:none}
.tri{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}.tri .shot{max-width:none}
figure{margin:10px 0 18px}figcaption{color:var(--mute);font-size:13px;margin-top:4px}
.tag{display:inline-block;padding:1px 8px;border-radius:4px;font-weight:700;font-size:13px;margin-right:6px}
.a{background:var(--red);color:#fff}.b{background:#eee;color:#222}.rec{background:var(--gold);color:#221}
.arms{display:flex;gap:12px;flex-wrap:wrap;align-items:flex-start}.arms img{image-rendering:pixelated;max-width:100%}
.wide{width:100%;max-width:960px;aspect-ratio:16/9;background:#000;display:flex;justify-content:center}
.wide img{height:100%;aspect-ratio:4/3;image-rendering:pixelated}
table{border-collapse:collapse;font-size:14px}td,th{border:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
.ask{background:var(--panel);border-left:4px solid var(--gold);padding:12px 16px;margin:16px 0}
@media (max-width:700px){.half,.tri{grid-template-columns:1fr}}
"""


def write(out: Path = gt.PREVIEW, work: Path = gt.OUT_DIR) -> Path:
    m = json.loads((work / "manifest.json").read_text(encoding="utf-8"))
    A, B = work / "TITLEPIC_A_free.png", work / "TITLEPIC_B_free.png"
    A_plate = work / "TITLEPIC_A_plate.png"
    logo_free = work / "M_DOOM_free.png"
    cur = Image.open(gt.CUR_TITLEPIC).convert("RGB")
    img = {k: b64(Image.open(p).convert("RGB")) for k, p in
           {"A": A, "B": B, "A_plate": A_plate}.items()}
    img["cur"] = b64(cur)
    menus = {}
    for lang in ("en", "ru", "ca"):
        for v, p in (("A", A), ("B", B)):
            mock = menu_mock(p, logo_free, lang)
            mock.save(work / f"MENUMOCK_{v}_{lang}.png")
            menus[(v, lang)] = b64(mock)
    menus[("cur", "en")] = b64(menu_mock(gt.CUR_TITLEPIC, gt.CUR_M_DOOM, "en"))
    arm_a, arm_b = armbands(A), armbands(B)
    arms_html = "".join(
        f'<figure><img src="{b64(a)}" alt="armband {n}, variant A"><figcaption><span class="tag a">A</span>{n}</figcaption></figure>'
        f'<figure><img src="{b64(b)}" alt="armband {n}, variant B"><figcaption><span class="tag b">B</span>{n}</figcaption></figure>'
        for n, a, b in zip(ARM_BOXES, arm_a, arm_b))
    logo_chk = Image.new("RGBA", (200, 64), (60, 120, 60, 255))
    logo_chk.alpha_composite(Image.open(logo_free).convert("RGBA"))
    logo_old = Image.open(gt.CUR_M_DOOM).convert("RGBA")
    crop = m["crop_padded"]
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soviet Doom title screen</title><style>{CSS}</style></head><body><main>
<h1>Epic title screen (D126) — TITLEPIC</h1>
<p>2026-10-24 · P4 · art-director. Source: <code>work/art/reference/gemini_titlepic_A.jfif</code>
(Gemini, {m['source_size'][0]}×{m['source_size'][1]}, local, D77) → <code>tools/art/gen_titlepic.py</code> →
320×200 indexed to palette v2 ({m['dither']}). Every view at ×3 and in 4:3 (960×720), the way the
engine shows a 320×200 screen (each pixel 1.2 times taller than wide).</p>

<div class="ask"><b>Two questions for the CEO.</b><br>
1. <b>Armbands (D105):</b> <span class="tag a">A</span> with the symbol painted as on the enemies
(D108/D114) or <span class="tag b">B</span> with Gemini's empty square.<br>
2. <b>Logo:</b> <span class="tag rec">recommended</span> the same <code>M_DOOM</code> without its black plate (letters on
the sky, with a 1 px outline), or today's <code>M_DOOM</code> with its black plate (below, «alternative»).
The free logo also replaces <code>M_DOOM</code> in the menu (same letters, same place, 60,0).</div>

<h2>Today</h2>
<figure><img class="shot" src="{img['cur']}" alt="current TITLEPIC"><figcaption>Current TITLEPIC (D18, «Plakat»).</figcaption></figure>

<h2><span class="tag a">A</span> With the symbol on the armbands</h2>
<figure><img class="shot" src="{img['A']}" alt="TITLEPIC variant A"><figcaption>TITLEPIC_A_free.png ·
{m['files']['TITLEPIC_A_free.png']['colours']} colours · free logo.</figcaption></figure>

<h2><span class="tag b">B</span> With the empty square</h2>
<figure><img class="shot" src="{img['B']}" alt="TITLEPIC variant B"><figcaption>TITLEPIC_B_free.png ·
{m['files']['TITLEPIC_B_free.png']['colours']} colours · free logo.</figcaption></figure>

<h2>The armbands close up (×6)</h2>
<p>The symbol is painted on Gemini's painting at its original resolution (1376×768), curved with the arm,
by <code>tools/art/armband_symbol.py</code> (the same warp as the enemies), and is then scaled down with the rest
of the painting. The hollow white square is filled with white (<code>ring</code> mode, like the General's armband);
the left one, in shadow, with its own shadowed white.</p>
<div class="arms">{arms_html}</div>

<h2>The main menu on top</h2>
<p>As the game draws it: the background dimmed (×{0.487}, measured in the engine, <code>gen_menu.py</code>), the logo and
the items in <code>SDMENU</code> cream/gold undimmed, Freedoom's cursor. A simulation, not an engine screenshot
(NOT VERIFIED in GZDoom; the PM takes the screenshot at install).</p>
<div class="tri">
<figure><img class="shot" src="{menus[('A','en')]}" alt="menu EN A"><figcaption><span class="tag a">A</span>EN</figcaption></figure>
<figure><img class="shot" src="{menus[('A','ru')]}" alt="menu RU A"><figcaption><span class="tag a">A</span>RU</figcaption></figure>
<figure><img class="shot" src="{menus[('A','ca')]}" alt="menu CA A"><figcaption><span class="tag a">A</span>CA</figcaption></figure>
<figure><img class="shot" src="{menus[('B','en')]}" alt="menu EN B"><figcaption><span class="tag b">B</span>EN</figcaption></figure>
<figure><img class="shot" src="{menus[('B','ru')]}" alt="menu RU B"><figcaption><span class="tag b">B</span>RU</figcaption></figure>
<figure><img class="shot" src="{menus[('B','ca')]}" alt="menu CA B"><figcaption><span class="tag b">B</span>CA</figcaption></figure>
</div>
<figure><img class="shot" style="max-width:480px" src="{menus[('cur','en')]}" alt="menu today"><figcaption>The menu today, for comparison.</figcaption></figure>

<h2>Alternative: the logo with its black plate</h2>
<div class="half">
<figure><img class="shot" src="{img['A_plate']}" alt="TITLEPIC A with the plate"><figcaption>TITLEPIC_A_plate.png: <code>M_DOOM</code>
untouched; its 200×58 black plate covers the sky (the tip of the flag and the torch end up under it).</figcaption></figure>
<figure><img class="shot" src="{img['A']}" alt="TITLEPIC A free logo"><figcaption>TITLEPIC_A_free.png (recommended).</figcaption></figure>
</div>
<div class="arms"><figure><img src="{b64(logo_old.resize((600, 192), Image.NEAREST))}" alt="M_DOOM today"><figcaption>M_DOOM today</figcaption></figure>
<figure><img src="{b64(logo_chk.resize((600, 192), Image.NEAREST))}" alt="M_DOOM free"><figcaption>M_DOOM_free (green = transparent)</figcaption></figure></div>

<h2>On a widescreen (16:9)</h2>
<div class="wide"><img src="{img['A']}" alt="16:9 pillarbox"></div>
<p>GZDoom shows 320×200 screens in 4:3 with black bars at the sides on 16:9 (NOT VERIFIED on this PC;
it is what it does with the current TITLEPIC). That is why the framing fills the 4:3 and not the 16:9.</p>

<h2>Framing decisions</h2>
<table>
<tr><th>What</th><th>Decision</th></tr>
<tr><td>Aspect ratio</td><td>Gemini's painting is 16:9 (1376×768); the screen is 4:3. A 4:3 window of
{crop[2]-crop[0]}×{crop[3]} px from x={crop[0]}: it takes in the PPSh's muzzle flash, the sergeant, the flag, the Kremlin
tower and the whole robot statue with its torch; the buildings at the edges are lost.</td></tr>
<tr><td>Sky for the logo</td><td>Gemini's top third is not enough: the hero's helmet fell under the
logo's subtitle. {m['sky_pad']} px of sky are added on top (the painting's own smoke, mirrored and
blurred) and the helmet starts just under the logo (row ~61; the logo takes 0-57).</td></tr>
<tr><td>Logo band</td><td>Rows 0-60 darkened (×0.50 behind the logo, ×0.78 at the sides) and softened
(1 px blur): the torch and the tip of the flag stay as a glow behind «DOOM»; the hero
is not touched.</td></tr>
<tr><td>Contract</td><td><code>M_DOOM</code> 200×64 at (60,0) (MOD-SPEC 6.6, MainMenuLogoTest): the logo is painted into
the TITLEPIC at that place, so when the menu opens the engine's <code>M_DOOM</code> lands exactly on top.</td></tr>
<tr><td>Palette</td><td>Palette v2 (226 colours), nearest colour in CIELAB with a soft 4×4 ordered dither
(clean, repeatable pixels). The enemies' weighted RGB turned the sergeant's eyes yellow.</td></tr>
</table>
<p>Install after the CEO's choice (PM): <code>work/art/titlepic_gemini/install.sh A</code> (or <code>B</code>;
add <code>plate</code> to keep the black plate). It copies the TITLEPIC (and the plate-free M_DOOM), adds TITLEPIC to
the approved palette v2 and rewrites its rows in <code>docs/art/LICENSES.md</code> (a derivative work of Gemini, D126).</p>
</main></body></html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(write())
