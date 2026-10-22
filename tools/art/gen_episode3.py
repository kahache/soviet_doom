"""Episode 3, «The Portal» (D112, P4): the three texture sets and the CEO's sheet.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode3.py
                            (macOS: .venv/bin/python tools/art/gen_episode3.py)

Renders gen_arctic (MAP07), gen_naval (MAP08) and gen_taiga (MAP09) into
work/art/episode3/<set>/, the sheet views into work/art/episode3/<set>/views/,
a manifest per set, and the review sheet
docs/art/previews/2026-10-22_P4_episode3-textures.html: every texture on its
own (1x and zoomed), as a 3x3 mosaic and in a sample room (a small Doom-like
view, NOT the engine), with OK / NO / ? and «Copiar resultado» like the
Episode 2 sheet, and the table of proposed lump names.

The sheet's CSS and vote script are Episode 2's (gen_episode2, read only),
with this sheet's own storage key and heading. Nothing goes to assets/,
TEXTURE-INDEX.md or LICENSES.md from here: that happens when the CEO
approves (the PM installs).
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ep3lib  # noqa: E402
import gen_arctic  # noqa: E402
import gen_episode2 as ep2sheet  # noqa: E402  (CSS, vote script, name rules: read only)
import gen_naval  # noqa: E402
import gen_taiga  # noqa: E402

PROJECT_ROOT = ep3lib.PROJECT_ROOT
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode3-textures.html"
TEXTURE_INDEX = PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md"
SCRIPT_REL = "tools/art/gen_episode3.py"
GIF_MS = ep2sheet.GIF_MS
SHEET_KEY = "sd-2026-10-22_P4_episode3-textures"

# set module, map, Spanish heading, recommended light (art director's proposal; level-designer decides)
SETS = [
    (gen_arctic, "MAP07", "Arctic — la estación de radar de Nueva Zembla",
     "Luz recomendada: exterior nevado 128-160 (la nieve ya es clara; más alto quema), barracones y sala del "
     "radar 112-144, la pantalla del radar como luz propia."),
    (gen_naval, "MAP08", "Naval — la base de submarinos de Severomorsk",
     "Luz recomendada: refugio excavado 96-128, muelle exterior 144-160 de día polar, interior del submarino "
     "112-144."),
    (gen_taiga, "MAP09", "Taiga/Alien — el portal de Tunguska",
     "Luz recomendada: taiga quemada 96-128 de noche, cabaña 112-144, el portal y el ácido 176-208 como en la "
     "fundición (MAP03)."),
]
NEW_FAMILIES = {
    "SNOW": "snow (flat)", "ICE": "ice (flat and wall)", "RADM": "radome panels", "HUT": "frosted corrugated hut",
    "RADR": "radar console (animated)", "HERM": "hermetic blast door", "RWY": "runway slabs (flat)",
    "HULL": "submarine hull", "RUBR": "anechoic rubber deck (flat)", "ROCK": "excavated living rock",
    "BULK": "watertight bulkhead door", "NAVC": "naval control panel", "CONT": "shipping container",
    "CRAN": "crane lattice (masked)", "PIER": "concrete quay (flat)",
    "BARK": "tree bark (trunk)", "LOGW": "log-cabin wall", "PEAT": "peat (flat)", "BURN": "burnt earth (flat)",
    "MOSS": "moss and lichen (flat)", "ALNM": "alien organic metal", "ACID": "acid (flat, animated)",
    "GLYP": "invader glyph plate", "PRTE": "portal rim",
}
# Approved lumps the sample rooms borrow, and the v2 ramps they carry (ART-BIBLE §3).
APPROVED_V2 = {f"SDPORT{i}": ("mosaic_cobalt",) for i in range(1, 5)}
APPROVED_ANIM = {"SDWATR1": [f"SDWATR{i}" for i in range(1, 5)], "SDPORT1": [f"SDPORT{i}" for i in range(1, 5)]}


def all_pieces():
    return [(mod, p) for mod, *_ in SETS for p in mod.PIECES]


# ================================================================ names
def existing_lumps() -> set[str]:
    """Every lump name already in use: files under assets/ and work/
    (sprites, textures, sounds...) except this episode's own drafts, and
    every SD name the texture index mentions."""
    names = set()
    for root in (PROJECT_ROOT / "assets", PROJECT_ROOT / "work"):
        if root.is_dir():
            for p in root.rglob("*"):
                if p.is_file() and not p.is_relative_to(ep3lib.WORK_ROOT):
                    names.add(p.stem.upper())
    if TEXTURE_INDEX.is_file():
        names |= set(re.findall(r"\bSD[A-Z0-9]{1,6}\b", TEXTURE_INDEX.read_text(encoding="utf-8")))
    return names


name_problems = ep2sheet.name_problems


# ================================================================ views
png_uri = ep2sheet.png_uri
file_uri = ep2sheet.file_uri


def anim_groups() -> dict[str, list[str]]:
    groups = dict(APPROVED_ANIM)
    for _, p in all_pieces():
        if len(p.lumps) == ep3lib.FRAMES:
            groups[p.lumps[0]] = p.lumps
    return groups


def piece_ramps() -> dict[str, tuple]:
    out = dict(APPROVED_V2)
    for _, p in all_pieces():
        for lump in p.lumps:
            out[lump] = p.v2_ramps
    return out


def lookup(lump: str, A: dict) -> np.ndarray:
    if lump not in A:
        A[lump] = ep3lib.load_approved(lump)
    return A[lump]


def room_spec(mod, piece) -> dict:
    R = mod.ROOM
    first = piece.lumps[0]
    if piece.kind == "flat":
        spec = {"back": R["wall"], "left": R["wall"], "right": R["wall"], "floor": first}
    elif piece.tiles in ("xy", "x"):
        spec = {"back": first, "left": first, "right": first, "floor": R["floor"]}
    else:
        spec = {"back": first, "left": R["wall"], "right": R["wall"], "floor": R["floor"]}
    spec["ceil"] = R["ceil"]
    spec.update(piece.scene or {})
    return spec


def sky_for(mod) -> np.ndarray:
    return ep3lib.night_sky() if mod.ROOM.get("sky") == "night" else ep3lib.ep2lib.sky_image()


def render_spec(mod, spec: dict, A: dict, frame: int = 0) -> np.ndarray:
    groups, ramps_of = anim_groups(), piece_ramps()

    def get(lump):
        if lump is None:
            return None
        if lump in groups:
            lump = groups[lump][frame]
        return lookup(lump, A)
    used = [spec[k] for k in ("back", "left", "right", "floor", "ceil") if spec.get(k)]
    ramps = tuple(sorted({r for u in used for r in ramps_of.get(u, ())}))
    return ep3lib.render_room(get(spec["back"]), get(spec["left"]), get(spec["right"]), get(spec["floor"]),
                              get(spec.get("ceil")), light=mod.ROOM["light"], version=2 if ramps else 1,
                              ramps=ramps, sky=sky_for(mod))


def animated(spec: dict) -> bool:
    groups = anim_groups()
    return any(spec.get(k) in groups for k in ("back", "left", "right", "floor", "ceil"))


def write_gif(frames: list[np.ndarray], path: Path, version: int = 1, ramps: tuple = ()) -> Path:
    imgs = [ep3lib.quantise_rgb(np.ascontiguousarray(f[..., :3]), version, ramps) for f in frames]
    path.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=GIF_MS, loop=0, optimize=False)
    return path


def render_view(mod, spec: dict, A: dict, path_stem: Path) -> Path:
    if animated(spec):
        frames = [render_spec(mod, spec, A, k) for k in range(ep3lib.FRAMES)]
        ramps = tuple(sorted({r for k in ("back", "left", "right", "floor", "ceil")
                              for r in piece_ramps().get(spec.get(k), ())}))
        return write_gif(frames, path_stem.with_suffix(".gif"), 2 if ramps else 1, ramps)
    path = path_stem.with_suffix(".png")
    Image.fromarray(render_spec(mod, spec, A)).save(path, optimize=True)
    return path


def make_views(mod, A: dict) -> dict:
    vdir = ep3lib.WORK_ROOT / mod.SET_NAME / "views"
    vdir.mkdir(parents=True, exist_ok=True)
    V = {}
    for p in mod.PIECES:
        V[p.key + "_room"] = render_view(mod, room_spec(mod, p), A, vdir / f"{p.key}_room")
        if len(p.lumps) > 1:
            V[p.key + "_anim"] = write_gif([A[lump] for lump in p.lumps], vdir / f"{p.key}_anim.gif",
                                           p.palette, p.v2_ramps)
    for i, (label, spec) in enumerate(mod.OVERVIEWS):
        spec = dict(spec)
        spec.setdefault("ceil", mod.ROOM["ceil"])
        V[f"overview{i}"] = render_view(mod, spec, A, vdir / f"overview{i}")
    return V


# ================================================================ sheet
JS = ep2sheet.JS.replace("sd-2026-10-22_P4_episode2-textures", SHEET_KEY).replace(
    "Texturas Episodio 2 (2026-10-22_P4, D104)", "Texturas Episodio 3 (2026-10-22_P4, D112)")
assert SHEET_KEY in JS and "Episodio 3" in JS
TILES_TXT = ep2sheet.TILES_TXT


def items_json(sets_data) -> list[dict]:
    items = []
    for mod, entries, A, V in sets_data:
        by_key = {e["piece"]: e for e in entries}
        for p in mod.PIECES:
            e = by_key[p.key]
            items.append({
                "id": p.key, "set": mod.SET_NAME, "lumps": p.lumps, "kind": "pared" if p.kind == "wall" else "suelo/techo",
                "w": p.size[0], "h": p.size[1], "tilesTxt": TILES_TXT[p.tiles], "pal": p.palette, "masked": p.masked,
                "title": p.title, "desc": p.desc, "rec": p.rec, "recWhy": p.rec_why, "whyV2": p.why_v2,
                "script": mod.SCRIPT_REL, "seed": e["seed"], "colours": e["colours_used"], "luma": e["mean_luma"],
                "seam": e["seam_score"], "img": png_uri(A[p.lumps[0]]),
                "anim": file_uri(V[p.key + "_anim"]) if p.key + "_anim" in V else None, "gifms": GIF_MS,
                "room": file_uri(V[p.key + "_room"]),
            })
    return items


def family_of(lump: str) -> str:
    return next((f for f in sorted(NEW_FAMILIES, key=len, reverse=True) if lump[2:].startswith(f)), "")


def lump_table(sets_data) -> str:
    rows = []
    for mod, entries, A, V in sets_data:
        by_key = {e["piece"]: e for e in entries}
        for p in mod.PIECES:
            e = by_key[p.key]
            fam = family_of(p.lumps[0])
            twin = mod.SHARED_SEED.get(p.key)
            seed = f"{e['seed']}" + (f" (= {twin})" if twin else "")
            rows.append(
                f"<tr><td><code>{html.escape(', '.join(p.lumps))}</code></td><td>{mod.SET_NAME}</td>"
                f"<td>{html.escape(p.title)}</td><td>{'pared' if p.kind == 'wall' else 'flat'}</td>"
                f"<td>{p.size[0]}×{p.size[1]}</td><td>{TILES_TXT[p.tiles]}</td>"
                f"<td>v{p.palette}{' + ' + ', '.join(p.v2_ramps) if p.v2_ramps else ''}{' RGBA' if p.masked else ''}</td>"
                f"<td>{html.escape(fam)} (nueva) — {html.escape(NEW_FAMILIES[fam])}</td>"
                f"<td>{seed}</td><td>propuesta</td></tr>")
        for lump, why in getattr(mod, "REUSED", []):
            rows.append(f"<tr><td><code>{lump}</code></td><td>{mod.SET_NAME}</td><td>{html.escape(why)}</td>"
                        f"<td>—</td><td>—</td><td>—</td><td>v1</td><td>existente</td><td>—</td>"
                        f"<td>aprobada (D107), reutilizada</td></tr>")
    head = ("<tr><th>Lump</th><th>Set</th><th>Qué es</th><th>Tipo</th><th>Tamaño</th><th>Tila</th><th>Paleta</th>"
            "<th>Familia</th><th>Semilla</th><th>Estado</th></tr>")
    return f'<div class="tablewrap"><table class="t">{head}{"".join(rows)}</table></div>'


def build_sheet(sets_data, problems: list[str], out: Path = SHEET) -> Path:
    items = items_json(sets_data)
    n_lumps = sum(len(i["lumps"]) for i in items)
    sections = []
    for (mod, entries, A, V), (_, mapname, heading, light) in zip(sets_data, SETS):
        ovs = "".join(
            f'<div class="v"><b>{html.escape(label)} (2×)</b><img class="px" src="{file_uri(V[f"overview{i}"])}" '
            f'width="640" height="400" alt=""></div>' for i, (label, _) in enumerate(mod.OVERVIEWS))
        sections.append(
            f'<h2>{mapname} · {html.escape(heading)}</h2><p class="lead">{html.escape(light)} '
            f'Generador <code>{mod.SCRIPT_REL}</code>, semilla base {mod.BATCH_SEED}.</p>'
            f'<h3>El set montado</h3><div class="ov">{ovs}</div>'
            f'<h3>Las piezas</h3><div id="cards-{mod.SET_NAME}"></div>')
    prob_html = ("<p><b>Comprobación de nombres:</b> los " + str(n_lumps) + " lumps propuestos son SD, de ≤ 8 "
                 "caracteres, y ninguno choca con un nombre existente en <code>assets/</code>, <code>work/</code> ni "
                 "<code>TEXTURE-INDEX.md</code>, ni se lee como fotograma de un sprite (por eso la consola es "
                 "<code>SDRADR</code> y no <code>SDRDR</code>: <code>SDRD</code> es un sprite).</p>") if not problems else (
        "<p><b>Problemas de nombres:</b></p><ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in problems) + "</ul>")
    intro = f"""
<div class="intro">
<p><b>Qué es (D112, P4).</b> Los tres conjuntos de texturas del Episodio 3, «The Portal», en <b>borrador</b>:
{len(items)} piezas, {n_lumps} lumps, todas procedurales con nuestros generadores, por el mismo método que el Episodio 2
que aprobaste (semilla fija, paleta v1, estilo Doom 1993-96, 64/128 px). Nada está en <code>assets/</code> ni en el
índice: si dices OK, el PM las instala tal cual.</p>
<ul>
<li>Cada pieza se ve <b>sola</b> (1× y ampliada), en <b>mosaico 3×3</b> (para ver si tila) y en una <b>sala de muestra</b>:
una vista mínima tipo Doom (320×200, 90°, ojo a 41 unidades, luz que cae con la distancia). <b>No es GZDoom</b>: sirve
para ver escala y repetición; la prueba real es en el motor, con el level-designer.</li>
<li><b>Paleta:</b> v1 en todo. Una sola excepción con el precedente de D66: el <b>borde del portal</b>
(<code>SDPRTE1</code>) usa el <code>mosaic_cobalt</code> de la v2, el del portal <code>SDPORT1-4</code>, porque es parte
del portal. Nada más lleva cobalto, ni oro, ni el rosa de la Legión.</li>
<li><b>Texto:</b> ninguna fuente del sistema. El número del submarino «471», «ММФ» del contenedor y el «3» del
compartimento salen de nuestro alfabeto (bigfont, D24); el número del contenedor, de dígitos de 3×5 píxeles; las placas
de las consolas parecen texto y no dicen nada; los <b>glifos invasores</b> son una gramática inventada de anillos y
trazos (no son letras de ningún alfabeto).</li>
<li><b>Tres piezas repiten la semilla de su gemela a propósito</b> (la pista con línea central, el casco con número,
la cubierta con escotilla): son la misma superficie con algo pintado o encastrado encima.</li>
<li><b>Reutilizadas, ya aprobadas:</b> el agua <code>SDWATR1-4</code> para la dársena y <code>SDDAM2</code> para el
paramento del muelle; el portal <code>SDPORT1-4</code> en la sala de muestra del borde.</li>
</ul>
<p>Marca <b>OK / NO / ?</b> en cada una, escribe notas si quieres y pulsa <b>Copiar resultado</b> para pegármelo.</p>
</div>"""
    ask = """
<div class="ask"><p><b>Además del OK/NO, cuatro preguntas:</b></p><ol>
<li><b>Verde del ácido.</b> La paleta v1 no tiene un verde saturado: el ácido (<code>SDACID1-4</code>), las venas del
metal invasor y los glifos están pintados con el <code>military_green</code> y crestas amarillas, un verde «tóxico» oliva.
Un verde ácido de verdad es una rampa nueva en los 30 huecos libres (paleta v3). Mi recomendación: verlo antes en el
motor; si en GZDoom parece barro, abrimos la rampa <code>acid_green</code>.</li>
<li><b>Nieve y radomo muy claros.</b> La nieve, el radomo y las pistas quedan por encima de la banda 0.45-0.70 de las
paredes (ART-BIBLE §6.1): es un exterior ártico. Los soldados del Reich (oscuros) se leen de sobra; la Legión (rosa y
cromo) se lee algo peor sobre blanco. Propongo luz 128-160 en el exterior nevado, no más. ¿Vale?</li>
<li><b>Hielo gris-azul.</b> Sin cobalto (es del portal), el hielo es el gris-azul de <code>steel_blue</code>, como el agua
del Volga. ¿Vale, o lo quieres más azul (sería otra rampa v3)?</li>
<li><b>Animadas y enmascarada.</b> La consola de radar (<code>SDRADR1-4</code>) y el ácido necesitan ANIMDEFS
(mod-engineer; propongo 12 tics por fotograma para el radar y 8 para el ácido). La celosía <code>SDCRAN1</code> es RGBA
como <code>SDCHAN1</code> y <code>SDINSL1</code>. Pendiente de verlas en el motor (D26: lo hace el PM).</li>
</ol></div>"""
    data = json.dumps(items, ensure_ascii=False)
    sets_js = json.dumps([m.SET_NAME for m, *_ in sets_data])
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Texturas Episodio 3</title>
<style>{ep2sheet.CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Soviet Doom · Texturas del Episodio 3 (borrador)</h1>
  <span class="prog"><b id="pDone">0</b> / {len(items)} juzgadas</span>
  <button class="primary" id="copyTop">Copiar resultado</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
{intro}
{"".join(sections)}
<h2>Nombres de lump propuestos</h2>
{prob_html}
{lump_table(sets_data)}
<h2>Preguntas</h2>
{ask}
<h2>Resultado</h2>
<p class="meta">Comentario general (opcional):</p>
<textarea class="note" id="general" placeholder="Algo sobre los tres sets en conjunto"></textarea>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copiar resultado</button><span class="copied" id="copiedBottom"></span> <button id="reset">Borrar respuestas</button></p>
<footer>Origen (a): procedural, <code>tools/art/gen_arctic.py</code> (semilla 5700+n), <code>gen_naval.py</code> (5800+n),
<code>gen_taiga.py</code> (5900+n), máquinas comunes en <code>ep3lib.py</code> sobre <code>ep2lib.py</code>, hoja
<code>{SCRIPT_REL}</code>; PNG en <code>work/art/episode3/&lt;set&gt;/</code>; tests <code>tests/test_gen_episode3.py</code>.
Paleta <code>docs/art/palette.json</code> sin modificar. Licencia: obra propia, CC BY-NC-SA 4.0 (D15). La sala de muestra NO
es el colormap ni los mipmaps del motor (NO VERIFICADO en GZDoom). El radar y el ácido necesitan ANIMDEFS
(mod-engineer). Nada instalado: si una vale, la instala el PM con tu OK.</footer>
</div>
<script>
const SETS = {sets_js};
const ITEMS = {data};
{JS}
</script>
</body>
</html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    return out


# ================================================================ main
def main() -> None:
    all_lumps = [lump for _, p in all_pieces() for lump in p.lumps]
    problems = name_problems(all_lumps, existing_lumps())
    A: dict = {}
    built = []
    for mod, *_ in SETS:
        entries, arrays = mod.build()
        A.update(arrays)
        built.append((mod, entries))
    sets_data = []
    for mod, entries in built:
        V = make_views(mod, A)
        sets_data.append((mod, entries, A, V))
        (ep3lib.WORK_ROOT / mod.SET_NAME / "manifest.json").write_text(json.dumps({
            "episode": 3, "phase": "P4", "decision": ep3lib.DECISION, "set": mod.SET_NAME, "script": mod.SCRIPT_REL,
            "batch_seed": mod.BATCH_SEED, "status": "drafts for the CEO; nothing in assets/",
            "preview": SHEET.relative_to(PROJECT_ROOT).as_posix(), "pieces": entries,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        for e in entries:
            print(f'{mod.SET_NAME:7s} {e["piece"]:8s} {e["width"]:3d}x{e["height"]:3d} v{e["palette_version"]} '
                  f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')
    sheet = build_sheet(sets_data, problems)
    print("name problems:", problems or "none")
    print(f"sheet: {sheet} ({sheet.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
