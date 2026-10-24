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
    html = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soviet Doom title screen</title><style>{CSS}</style></head><body><main>
<h1>Pantalla de inicio épica (D126) — TITLEPIC</h1>
<p>2026-10-24 · P4 · art-director. Fuente: <code>work/art/reference/gemini_titlepic_A.jfif</code>
(Gemini, {m['source_size'][0]}×{m['source_size'][1]}, local, D77) → <code>tools/art/gen_titlepic.py</code> →
320×200 indexado a la paleta v2 ({m['dither']}). Todas las vistas a ×3 y en 4:3 (960×720), como el
motor muestra una pantalla 320×200 (cada píxel 1,2 veces más alto que ancho).</p>

<div class="ask"><b>Dos preguntas para el CEO.</b><br>
1. <b>Brazaletes (D105):</b> <span class="tag a">A</span> con el símbolo pintado como en los enemigos
(D108/D114) o <span class="tag b">B</span> con el cuadro vacío de Gemini.<br>
2. <b>Logo:</b> <span class="tag rec">recomendado</span> el mismo <code>M_DOOM</code> sin su placa negra (letras sobre
el cielo, con contorno de 1 px), o el <code>M_DOOM</code> actual con su placa negra (abajo, «alternativa»).
El logo libre también sustituye a <code>M_DOOM</code> en el menú (mismas letras, mismo sitio, 60,0).</div>

<h2>Hoy</h2>
<figure><img class="shot" src="{img['cur']}" alt="current TITLEPIC"><figcaption>TITLEPIC actual (D18, «Plakat»).</figcaption></figure>

<h2><span class="tag a">A</span> Con el símbolo en los brazaletes</h2>
<figure><img class="shot" src="{img['A']}" alt="TITLEPIC variant A"><figcaption>TITLEPIC_A_free.png ·
{m['files']['TITLEPIC_A_free.png']['colours']} colores · logo libre.</figcaption></figure>

<h2><span class="tag b">B</span> Con el cuadro vacío</h2>
<figure><img class="shot" src="{img['B']}" alt="TITLEPIC variant B"><figcaption>TITLEPIC_B_free.png ·
{m['files']['TITLEPIC_B_free.png']['colours']} colores · logo libre.</figcaption></figure>

<h2>Los brazaletes de cerca (×6)</h2>
<p>El símbolo se pinta sobre el cuadro de Gemini a su resolución original (1376×768), curvado con el brazo,
con <code>tools/art/armband_symbol.py</code> (el mismo warp que los enemigos), y después se reduce con el resto
del cuadro. El cuadro blanco hueco se rellena de blanco (modo <code>ring</code>, como el brazalete del General);
el de la izquierda, en sombra, con su propio blanco en sombra.</p>
<div class="arms">{arms_html}</div>

<h2>El menú principal encima</h2>
<p>Como lo dibuja el juego: el fondo atenuado (×{0.487}, medido en el motor, <code>gen_menu.py</code>), el logo y
las opciones en <code>SDMENU</code> crema/oro sin atenuar, el cursor de Freedoom. Simulación, no captura del motor
(NO VERIFICADO en GZDoom; la captura la hace el PM al instalar).</p>
<div class="tri">
<figure><img class="shot" src="{menus[('A','en')]}" alt="menu EN A"><figcaption><span class="tag a">A</span>EN</figcaption></figure>
<figure><img class="shot" src="{menus[('A','ru')]}" alt="menu RU A"><figcaption><span class="tag a">A</span>RU</figcaption></figure>
<figure><img class="shot" src="{menus[('A','ca')]}" alt="menu CA A"><figcaption><span class="tag a">A</span>CA</figcaption></figure>
<figure><img class="shot" src="{menus[('B','en')]}" alt="menu EN B"><figcaption><span class="tag b">B</span>EN</figcaption></figure>
<figure><img class="shot" src="{menus[('B','ru')]}" alt="menu RU B"><figcaption><span class="tag b">B</span>RU</figcaption></figure>
<figure><img class="shot" src="{menus[('B','ca')]}" alt="menu CA B"><figcaption><span class="tag b">B</span>CA</figcaption></figure>
</div>
<figure><img class="shot" style="max-width:480px" src="{menus[('cur','en')]}" alt="menu today"><figcaption>El menú hoy, para comparar.</figcaption></figure>

<h2>Alternativa: el logo con su placa negra</h2>
<div class="half">
<figure><img class="shot" src="{img['A_plate']}" alt="TITLEPIC A with the plate"><figcaption>TITLEPIC_A_plate.png: <code>M_DOOM</code>
sin tocar; su placa negra de 200×58 tapa el cielo (la punta de la bandera y la antorcha quedan debajo).</figcaption></figure>
<figure><img class="shot" src="{img['A']}" alt="TITLEPIC A free logo"><figcaption>TITLEPIC_A_free.png (recomendado).</figcaption></figure>
</div>
<div class="arms"><figure><img src="{b64(logo_old.resize((600, 192), Image.NEAREST))}" alt="M_DOOM today"><figcaption>M_DOOM hoy</figcaption></figure>
<figure><img src="{b64(logo_chk.resize((600, 192), Image.NEAREST))}" alt="M_DOOM free"><figcaption>M_DOOM_free (verde = transparente)</figcaption></figure></div>

<h2>En pantalla panorámica (16:9)</h2>
<div class="wide"><img src="{img['A']}" alt="16:9 pillarbox"></div>
<p>GZDoom muestra las pantallas 320×200 en 4:3 con bandas negras a los lados en 16:9 (NO VERIFICADO en este PC;
es lo que hace con el TITLEPIC actual). Por eso el encuadre llena el 4:3 y no el 16:9.</p>

<h2>Decisiones de encuadre</h2>
<table>
<tr><th>Qué</th><th>Decisión</th></tr>
<tr><td>Proporción</td><td>El cuadro de Gemini es 16:9 (1376×768); la pantalla es 4:3. Ventana 4:3 de
{crop[2]-crop[0]}×{crop[3]} px desde x={crop[0]}: entran el fogonazo de la PPSh, el sargento, la bandera, la torre
del Kremlin y la estatua-robot entera con la antorcha; se pierden los edificios de los extremos.</td></tr>
<tr><td>Cielo para el logo</td><td>El tercio de arriba de Gemini no basta: el casco del héroe caía bajo el
subtítulo del logo. Se añaden {m['sky_pad']} px de cielo encima (el humo del propio cuadro, reflejado y
difuminado) y el casco empieza justo bajo el logo (fila ~61; el logo ocupa 0-57).</td></tr>
<tr><td>Franja del logo</td><td>Filas 0-60 oscurecidas (×0,50 detrás del logo, ×0,78 en los lados) y suavizadas
(desenfoque de 1 px): la antorcha y la punta de la bandera quedan como un resplandor detrás de «DOOM»; el héroe
no se toca.</td></tr>
<tr><td>Contrato</td><td><code>M_DOOM</code> 200×64 en (60,0) (MOD-SPEC 6.6, MainMenuLogoTest): el logo va pintado en
el TITLEPIC en ese sitio, así que al abrir el menú el <code>M_DOOM</code> del motor cae exactamente encima.</td></tr>
<tr><td>Paleta</td><td>Paleta v2 (226 colores), color más cercano en CIELAB con un tramado ordenado 4×4 suave
(píxel limpio y repetible). El RGB ponderado de los enemigos ponía los ojos del sargento amarillos.</td></tr>
</table>
<p>Instalación tras la elección del CEO (PM): <code>work/art/titlepic_gemini/install.sh A</code> (o <code>B</code>;
añade <code>plate</code> para conservar la placa negra). Copia el TITLEPIC (y el M_DOOM sin placa), añade TITLEPIC a
la paleta v2 aprobada y reescribe sus filas en <code>docs/art/LICENSES.md</code> (obra derivada de Gemini, D126).</p>
</main></body></html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(write())
