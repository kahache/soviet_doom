"""Episode 2, «The Road to Moscow» (D104, P4): the three texture sets and the CEO's sheet.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode2.py
                            (macOS: .venv/bin/python tools/art/gen_episode2.py)

Renders gen_railway (MAP04), gen_dam (MAP05) and gen_moscow (MAP06) into
work/art/episode2/<set>/, the sheet views into work/art/episode2/<set>/views/,
a manifest per set, and the review sheet
docs/art/previews/2026-10-22_P4_episode2-textures.html: every texture on its
own (1x and zoomed), as a 3x3 mosaic and in a sample room (a small Doom-like
view, NOT the engine), with OK / NO / ? and «Copiar resultado» like the
listening sheets, and the table of proposed lump names.

Nothing goes to assets/, TEXTURE-INDEX.md or LICENSES.md from here: that
happens when the CEO approves (the PM installs). APPROVED 2026-10-22, 25/25
(D107): the 28 lumps were copied byte for byte from work/art/episode2/<set>/
into assets/textures/<set>/ (walls) and assets/flats/<set>/ (flats);
SDSIGL1 is for single use only (a signal or a panel), never as a mosaic.
Re-running this script rewrites the CEO's judged sheet: don't, unless a new
proposal is wanted.
"""

from __future__ import annotations

import base64
import html
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ep2lib  # noqa: E402
import gen_dam  # noqa: E402
import gen_moscow  # noqa: E402
import gen_railway  # noqa: E402

PROJECT_ROOT = ep2lib.PROJECT_ROOT
SHEET = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode2-textures.html"
TEXTURE_INDEX = PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md"
SCRIPT_REL = "tools/art/gen_episode2.py"
GIF_MS = 229                  # 8 tics at 35 Hz, like SDMOLT

# set module, map, Spanish heading, recommended light (art director's proposal; level-designer decides)
SETS = [
    (gen_railway, "MAP04", "Railway — la estación de clasificación de Sverdlovsk, 1977",
     "Luz recomendada: exteriores 144-176 de día nublado, naves y rotonda 112-144."),
    (gen_dam, "MAP05", "Dam — la presa del Volga en Zhiguli",
     "Luz recomendada: coronación y aliviadero 160-192, sala de turbinas 128-160, galerías 96-128."),
    (gen_moscow, "MAP06", "Moscow — la Plaza Roja y el Kremlin",
     "Luz recomendada: plaza 160-192 (es el final, a plena luz), interiores del GUM 128-144."),
]
NEW_FAMILIES = {
    "TRAK": "track on ballast (flat)", "BLST": "ballast (flat)", "WAGN": "goods wagon side",
    "TANK": "tank wagon side", "ARMR": "armoured-train plate", "SIGL": "railway signal",
    "DAM": "dam concrete", "TURB": "turbine / generator housing", "CTRL": "control panel",
    "SPIL": "spillway rack", "WATR": "water (flat, animated)", "INSL": "HV insulator (masked)",
    "COBL": "setts (flat)", "KREM": "Kremlin wall / merlon", "GUM": "GUM facade", "TRIB": "tribune granite",
    "BANR": "parade banner", "SPAS": "Spasskaya tower stone",
}
SPRITE_LIKE = re.compile(r"^[A-Z0-9]{4}[A-Z][0-9]([A-Z][0-9])?$")


# ================================================================ names
def existing_lumps(own: frozenset[str] = frozenset()) -> set[str]:
    """Every lump name already in use: files under assets/ and work/ (sprites,
    textures, sounds...) and every SD name the texture index mentions.

    `own` are this episode's lumps: since D107 (approved 2026-10-22) they are
    installed in assets/{textures,flats}/<set>/ and have rows in the index,
    so those copies and rows are not a clash with themselves. A file of the
    same name anywhere else in assets/ still is."""
    names = set()
    sets = {mod.SET_NAME for mod, *_ in SETS}
    for root in (PROJECT_ROOT / "assets", PROJECT_ROOT / "work"):
        if root.is_dir():
            for p in root.rglob("*"):
                if not p.is_file() or p.is_relative_to(ep2lib.WORK_ROOT):
                    continue
                if root.name == "assets" and p.stem.upper() in own and p.parent.name in sets:
                    continue
                names.add(p.stem.upper())
    if TEXTURE_INDEX.is_file():
        names |= set(re.findall(r"\bSD[A-Z0-9]{1,6}\b", TEXTURE_INDEX.read_text(encoding="utf-8"))) - own
    return names


def sprite_prefixes(names: set[str]) -> set[str]:
    return {n[:4] for n in names if SPRITE_LIKE.match(n)}


def name_problems(lumps: list[str], taken: set[str]) -> list[str]:
    out = []
    sprites = sprite_prefixes(taken)
    for lump in lumps:
        if not (len(lump) <= 8 and lump.isupper() and lump.startswith("SD") and lump.isalnum()):
            out.append(f"{lump}: not an SD name of <= 8 upper-case characters")
        if lump in taken:
            out.append(f"{lump}: already in use")
        if SPRITE_LIKE.match(lump) and lump[:4] in sprites:
            out.append(f"{lump}: reads as a frame of the sprite {lump[:4]}")
    if len(set(lumps)) != len(lumps):
        out.append("a lump name is used twice")
    return out


# ================================================================ views
def png_uri(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(arr), "RGBA" if arr.shape[2] == 4 else "RGB").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def file_uri(path: Path) -> str:
    kind = "gif" if path.suffix == ".gif" else "png"
    return f"data:image/{kind};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_gif(frames: list[np.ndarray], version: int, path: Path) -> Path:
    imgs = [ep2lib.quantise_rgb(f[..., :3], version) for f in frames]
    path.parent.mkdir(parents=True, exist_ok=True)
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=GIF_MS, loop=0, optimize=False)
    return path


def lookup(lump: str, A: dict) -> np.ndarray:
    if lump in A:
        return A[lump]
    A[lump] = ep2lib.load_approved(lump)
    return A[lump]


def room_spec(mod, piece: ep2lib.Piece) -> dict:
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


def render_spec(spec: dict, A: dict, light: float, frame: int = 0) -> np.ndarray:
    def get(lump):
        if lump is None:
            return None
        if lump.endswith("1") and lump[:-1] + "2" in A and lump.startswith("SDWATR"):
            lump = f"{lump[:-1]}{frame + 1}"
        return lookup(lump, A)
    used = [spec[k] for k in ("back", "left", "right", "floor", "ceil") if spec.get(k)]
    version = 2 if any(u in V2_LUMPS for u in used) else 1
    return ep2lib.render_room(get(spec["back"]), get(spec["left"]), get(spec["right"]), get(spec["floor"]),
                              get(spec.get("ceil")), light=light, version=version)


V2_LUMPS: set[str] = set()


def animated(spec: dict) -> bool:
    return any(str(spec.get(k, "")).startswith("SDWATR") for k in ("back", "left", "right", "floor"))


def make_views(mod, A: dict) -> dict:
    vdir = ep2lib.WORK_ROOT / mod.SET_NAME / "views"
    vdir.mkdir(parents=True, exist_ok=True)
    V = {}
    light = mod.ROOM["light"]
    for p in mod.PIECES:
        spec = room_spec(mod, p)
        if animated(spec):
            frames = [render_spec(spec, A, light, k) for k in range(ep2lib.FRAMES)]
            V[p.key + "_room"] = write_gif(frames, 1, vdir / f"{p.key}_room.gif")
            V[p.key + "_anim"] = write_gif([A[l] for l in p.lumps], p.palette, vdir / f"{p.key}_anim.gif")
        else:
            path = vdir / f"{p.key}_room.png"
            Image.fromarray(render_spec(spec, A, light)).save(path, optimize=True)
            V[p.key + "_room"] = path
    for i, (label, spec) in enumerate(mod.OVERVIEWS):
        spec = dict(spec)
        spec.setdefault("ceil", mod.ROOM["ceil"])
        if animated(spec):
            frames = [render_spec(spec, A, light, k) for k in range(ep2lib.FRAMES)]
            V[f"overview{i}"] = write_gif(frames, 1, vdir / f"overview{i}.gif")
        else:
            path = vdir / f"overview{i}.png"
            Image.fromarray(render_spec(spec, A, light)).save(path, optimize=True)
            V[f"overview{i}"] = path
    return V


# ================================================================ sheet
CSS = """
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4;--well:#1b1c1f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--well:#0e0e0f}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--well:#0e0e0f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
h2{font-size:17px;margin:30px 0 4px;padding-top:10px;border-top:2px solid var(--accent)}
h3{font-size:14px;margin:16px 0 6px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.prog{font-variant-numeric:tabular-nums;color:var(--mute)}.prog b{color:var(--ink)}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.intro p{margin:6px 0;max-width:900px}.intro ul{margin:6px 0;padding-left:20px;max-width:900px}
.lead{color:var(--mute);margin:2px 0 10px}
.card{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:14px 0}
.row{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:10px 16px;padding:12px}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
.name code{font:600 15px ui-monospace,Consolas,monospace}
.ev{display:inline-block;background:var(--chip);border-radius:10px;padding:0 8px;margin-left:6px;font-size:12px;color:var(--mute)}
.meta{color:var(--mute);font-size:12.5px;margin:3px 0}.meta b{color:var(--ink);font-weight:600}
.views{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start;margin:8px 0}
.v{display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:var(--mute);max-width:100%}
.v b{color:var(--ink);font-weight:600}
img.px,.mosaic{image-rendering:pixelated;image-rendering:crisp-edges;display:block;max-width:100%;height:auto;background:var(--well);border:1px solid var(--line)}
.mosaic{background-repeat:repeat;max-width:100%}
.masked{background-color:#7d8ea3 !important}
.vote{display:flex;flex-direction:column;gap:6px}
.btns{display:flex;gap:6px}.btns button{flex:1;font-weight:650;padding:6px 0}
.btns button.on.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btns button.on.no{background:var(--no);border-color:var(--no);color:#fff}
.btns button.on.q{background:var(--q);border-color:var(--q);color:#111}
textarea.note{width:100%;min-height:64px;resize:vertical;font:inherit;font-size:13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 7px}
.rec{font-size:12.5px;border-left:3px solid var(--q);padding:2px 8px;margin:6px 0;max-width:820px}
.ov{display:flex;flex-wrap:wrap;gap:14px}
table.t{border-collapse:collapse;font-size:12.5px;width:100%}
table.t th,table.t td{border-top:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top}
table.t th{color:var(--mute);font-weight:600;font-size:12px}
table.t td code{font:600 13px ui-monospace,Consolas,monospace}
.tablewrap{overflow-x:auto}
.ask{border-left:3px solid var(--q);background:var(--card);padding:8px 14px;max-width:900px}
#result{width:100%;min-height:150px;font:12.5px ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);padding:10px}
.copied{color:var(--ok);font-weight:600;margin-left:8px}
footer{color:var(--mute);font-size:12.5px;margin-top:24px}
@media (max-width:760px){.row{grid-template-columns:1fr}}
"""

JS = r"""
const KEY = "sd-2026-10-22_P4_episode2-textures";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
const st = id => (S[id] = S[id] || {v:"", n:""});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function zoomFor(w){ return w <= 64 ? 4 : 3; }
function card(it){
  const z = zoomFor(it.w), mz = it.w <= 64 ? 2 : 1;
  const mk = it.masked ? " masked" : "";
  const anim = it.anim ? `<div class="v"><b>animada, ${it.gifms} ms/fotograma (4×)</b><img class="px${mk}" src="${it.anim}" width="${it.w*4}" height="${it.h*4}" alt=""></div>` : "";
  const tex = it.anim ? "" : `<div class="v"><b>sola ${z}×</b><img class="px${mk}" src="${it.img}" width="${it.w*z}" height="${it.h*z}" alt=""></div>`;
  return `<div class="card"><div class="row" id="r-${it.id}" data-id="${it.id}"><div>
    <div class="name"><code>${esc(it.lumps.join(", "))}</code><span class="ev">${it.kind} · ${it.w}×${it.h} · tila: ${esc(it.tilesTxt)} · paleta v${it.pal}${it.masked ? " · enmascarada (RGBA)" : ""}</span></div>
    <p class="meta"><b>${esc(it.title)}.</b> ${esc(it.desc)}</p>
    <div class="views">
      <div class="v"><b>sola 1×</b><img class="px${mk}" src="${it.img}" width="${it.w}" height="${it.h}" alt=""></div>
      ${tex}${anim}
      <div class="v"><b>mosaico 3×3 (${mz}×)</b><div class="mosaic${mk}" style="width:${it.w*3*mz}px;height:${it.h*3*mz}px;background-image:url(${it.img});background-size:${it.w*mz}px ${it.h*mz}px"></div></div>
    </div>
    <div class="views"><div class="v"><b>sala de muestra (2×; no es el motor)</b><img class="px" src="${it.room}" width="640" height="400" alt=""></div></div>
    <p class="rec"><b>Recomiendo: ${esc(it.rec)}.</b> ${esc(it.recWhy)}${it.whyV2 ? ` <i>Paleta: ${esc(it.whyV2)}</i>` : ""}</p>
    <p class="meta">Origen (a) ${esc(it.script)}, semilla ${it.seed} · colores ${it.colours} · luma media ${it.luma} · costura ${it.seam === null ? "n/a" : it.seam}</p>
  </div>
  <div class="vote">
    <div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
    <textarea class="note" placeholder="Notas (qué cambiar, más claro, otro color…)">${esc(st(it.id).n)}</textarea>
  </div></div></div>`;
}
function build(){
  for (const set of SETS) {
    document.getElementById("cards-" + set).innerHTML = ITEMS.filter(i => i.set === set).map(card).join("");
  }
  ITEMS.forEach(i => paint(i.id));
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok","v-no","v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
}
function summary(){
  const label = {ok:"OK", no:"NO", q:"?"};
  const done = ITEMS.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  const L = [`Texturas Episodio 2 (2026-10-22_P4, D104): ${done}/${ITEMS.length} juzgadas`];
  let cur = "";
  for (const i of ITEMS) {
    if (i.set !== cur) { cur = i.set; L.push(`[${i.set}]`); }
    const s = st(i.id), n = (s.n || "").trim().replace(/\s+/g, " ");
    L.push(`${i.lumps.join("/")}: ${label[s.v] || "sin juzgar"}${n ? ` — «${n}»` : ""}`);
  }
  const g = (document.getElementById("general").value || "").trim().replace(/\s+/g, " ");
  if (g) L.push(`General: «${g}»`);
  document.getElementById("result").value = L.join("\n");
}
function copy(which){
  const t = document.getElementById("result"), msg = document.getElementById(which);
  summary();
  const ok = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(ok, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  if (e.target.id === "general") { S._general = e.target.value; save(); summary(); return; }
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.getElementById("copyTop").addEventListener("click", () => copy("copiedTop"));
document.getElementById("copyBottom").addEventListener("click", () => copy("copiedBottom"));
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar las respuestas y notas de esta hoja?")) { S = {}; save(); document.getElementById("general").value = ""; build(); summary(); } });
document.getElementById("general").value = S._general || "";
build(); summary();
"""

TILES_TXT = {"xy": "x e y", "x": "solo x", "y": "solo y", "no": "no (pieza única)"}


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


def lump_table(sets_data) -> str:
    rows = []
    for mod, entries, A, V in sets_data:
        by_key = {e["piece"]: e for e in entries}
        for p in mod.PIECES:
            e = by_key[p.key]
            fam = next((f for f in sorted(NEW_FAMILIES, key=len, reverse=True) if p.lumps[0][2:].startswith(f)), "")
            fam_txt = f"{fam} (nueva)" if fam else p.lumps[0][2:-1] + " (existente)"
            rows.append(
                f"<tr><td><code>{html.escape(', '.join(p.lumps))}</code></td><td>{mod.SET_NAME}</td>"
                f"<td>{html.escape(p.title)}</td><td>{'pared' if p.kind == 'wall' else 'flat'}</td>"
                f"<td>{p.size[0]}×{p.size[1]}</td><td>{TILES_TXT[p.tiles]}</td>"
                f"<td>v{p.palette}{' RGBA' if p.masked else ''}</td><td>{html.escape(fam_txt)}</td>"
                f"<td>{e['seed']}</td><td>propuesta</td></tr>")
    for lump, why in gen_moscow.REUSED:
        rows.append(f"<tr><td><code>{lump}</code></td><td>moscow</td><td>{html.escape(why)}</td><td>pared</td>"
                    f"<td>64×128</td><td>x e y</td><td>v1</td><td>MARB (existente)</td><td>1938</td>"
                    f"<td>aprobada (D42), reutilizada</td></tr>")
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
        reuse = ""
        if mod is gen_moscow:
            marb = ep2lib.load_approved("SDMARB1")
            reuse = ('<h3>Reutilizada, ya aprobada</h3><div class="card"><div class="row" style="grid-template-columns:1fr">'
                     f'<div><div class="name"><code>SDMARB1</code><span class="ev">aprobada D42 · no se vota</span></div>'
                     f'<p class="meta">{html.escape(gen_moscow.REUSED[0][1])}</p><div class="views">'
                     f'<div class="v"><b>4×</b><img class="px" src="{png_uri(marb)}" width="256" height="512" alt=""></div>'
                     '</div></div></div></div>')
        sections.append(
            f'<h2>{mapname} · {html.escape(heading)}</h2><p class="lead">{html.escape(light)} '
            f'Generador <code>{mod.SCRIPT_REL}</code>, semilla base {mod.BATCH_SEED}.</p>'
            f'<h3>El set montado</h3><div class="ov">{ovs}</div>'
            f'<h3>Las piezas</h3><div id="cards-{mod.SET_NAME}"></div>{reuse}')
    prob_html = ("<p><b>Comprobación de nombres:</b> los " + str(n_lumps) + " lumps propuestos son SD, de ≤ 8 "
                 "caracteres, y ninguno choca con un nombre existente en <code>assets/</code>, <code>work/</code> ni "
                 "<code>TEXTURE-INDEX.md</code>, ni se lee como fotograma de un sprite.</p>") if not problems else (
        "<p><b>Problemas de nombres:</b></p><ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in problems) + "</ul>")
    intro = f"""
<div class="intro">
<p><b>Qué es (D104, P4).</b> Los tres conjuntos de texturas del Episodio 2, «The Road to Moscow», en <b>borrador</b>:
{len(items)} piezas, {n_lumps} lumps, todas procedurales con nuestros generadores (semilla fija, paleta v1, estilo Doom 1993-96,
64/128 px). Nada está en <code>assets/</code> ni en el índice: si dices OK, el PM las instala tal cual.</p>
<ul>
<li>Cada pieza se ve <b>sola</b> (1× y ampliada), en <b>mosaico 3×3</b> (para ver si tila) y en una <b>sala de muestra</b>:
una vista mínima tipo Doom (320×200, 90°, ojo a 41 unidades, luz que cae con la distancia). <b>No es GZDoom</b>: sirve
para ver escala y repetición; la prueba real es en el motor, con el level-designer.</li>
<li><b>Paleta:</b> v1. Los ladrillos (rotonda, muralla del Kremlin, almena, pancarta sobre el muro, Spásskaya) usan
<code>marble_red</code> de la v2, igual que el ladrillo de Tankogrado que aprobaste (D66): v1 no tiene rojo de ladrillo cocido.
Ningún cobalto ni oro de mosaico (son del portal y del metro).</li>
<li><b>Texto:</b> ninguna fuente del sistema. «НЕФТЬ», «СКЛАД» y «М2» salen de nuestro alfabeto (bigfont, D24); el número del
vagón y el año de la placa, de dígitos de 3×5 píxeles dibujados aquí; las placas del panel de control parecen texto y no dicen nada.</li>
<li><b>D12:</b> Kremlin y Plaza Roja como lugares y piedra; la pancarta lleva estrella y hoz y martillo, sin texto ni retratos.</li>
<li><b>Mármol de Plóshchad Revolyutsii:</b> ya existe (<code>SDMARB1</code>, aprobado en el Metro), se reutiliza.</li>
</ul>
<p>Marca <b>OK / NO / ?</b> en cada una, escribe notas si quieres y pulsa <b>Copiar resultado</b> para pegármelo.</p>
</div>"""
    ask = """
<div class="ask"><p><b>Además del OK/NO, tres preguntas:</b></p><ol>
<li><b>Verde de la turbina.</b> La paleta v1 no tiene el «gris-verde» de la maquinaria soviética; lo he pintado con el verde
4BO de las puertas (ata con la base). Si lo quieres de verdad gris-verde, es una rampa nueva en los 30 huecos libres
(paleta v3). Mi recomendación: no, el 4BO vale.</li>
<li><b>Agua.</b> Gris-azul (steel_blue), no azul Doom saturado, para no parecerse al portal. ¿Vale, o la quieres más azul?</li>
<li><b>Enmascaradas.</b> La almena <code>SDKREM2</code> y el aislador <code>SDINSL1</code> son RGBA como la cadena
<code>SDCHAN1</code>: funcionan como textura media de una línea de dos caras. Pendiente de verlas en el motor (D26: lo hace el PM).</li>
</ol></div>"""
    data = json.dumps(items, ensure_ascii=False)
    sets_js = json.dumps([m.SET_NAME for m, *_ in sets_data])
    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Texturas Episodio 2</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Soviet Doom · Texturas del Episodio 2 (borrador)</h1>
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
<footer>Origen (a): procedural, <code>tools/art/gen_railway.py</code> (semilla 5400+n), <code>gen_dam.py</code> (5500+n),
<code>gen_moscow.py</code> (5600+n), máquinas comunes en <code>ep2lib.py</code>, hoja <code>{SCRIPT_REL}</code>; PNG en
<code>work/art/episode2/&lt;set&gt;/</code>; tests <code>tests/test_gen_episode2.py</code>. Paleta <code>docs/art/palette.json</code>
sin modificar. Licencia: obra propia, CC BY-NC-SA 4.0 (D15). La sala de muestra NO es el colormap ni los mipmaps del motor
(NO VERIFICADO en GZDoom). El agua necesita ANIMDEFS (mod-engineer). Nada instalado: si una vale, la instala el PM con tu OK.</footer>
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
    all_lumps = [l for mod, *_ in SETS for p in mod.PIECES for l in p.lumps]
    problems = name_problems(all_lumps, existing_lumps(frozenset(all_lumps)))
    for mod, *_ in SETS:
        for p in mod.PIECES:
            if p.palette == 2:
                V2_LUMPS.update(p.lumps)
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
        (ep2lib.WORK_ROOT / mod.SET_NAME / "manifest.json").write_text(json.dumps({
            "episode": 2, "phase": "P4", "decision": "D104", "set": mod.SET_NAME, "script": mod.SCRIPT_REL,
            "batch_seed": mod.BATCH_SEED, "status": "drafts for the CEO; nothing in assets/",
            "preview": SHEET.relative_to(PROJECT_ROOT).as_posix(), "pieces": entries,
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        for e in entries:
            print(f'{mod.SET_NAME:8s} {e["piece"]:8s} {e["width"]:3d}x{e["height"]:3d} v{e["palette_version"]} '
                  f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')
    sheet = build_sheet(sets_data, problems)
    print("name problems:", problems or "none")
    print(f"sheet: {sheet} ({sheet.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
