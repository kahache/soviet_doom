"""Episode 3, «The Portal» (D112, P4): the three texture sets and the CEO's sheet.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode3.py
                            (macOS: .venv/bin/python tools/art/gen_episode3.py)

Renders gen_arctic (MAP07), gen_naval (MAP08) and gen_taiga (MAP09) into
work/art/episode3/<set>/, the sheet views into work/art/episode3/<set>/views/,
a manifest per set, and the review sheet
docs/art/previews/2026-10-22_P4_episode3-textures.html: every texture on its
own (1x and zoomed), as a 3x3 mosaic and in a sample room (a small Doom-like
view, NOT the engine), with OK / NO / ? and «Copy result» like the
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

# set module, map, heading, recommended light (art director's proposal; level-designer decides)
SETS = [
    (gen_arctic, "MAP07", "Arctic — the Novaya Zemlya radar station",
     "Recommended light: snowy exterior 128-160 (the snow is already light; higher burns out), barracks and "
     "radar room 112-144, the radar screen as its own light."),
    (gen_naval, "MAP08", "Naval — the Severomorsk submarine base",
     "Recommended light: excavated pen 96-128, outer quay 144-160 in polar daylight, submarine interior "
     "112-144."),
    (gen_taiga, "MAP09", "Taiga/Alien — the Tunguska portal",
     "Recommended light: burnt taiga 96-128 at night, cabin 112-144, the portal and the acid 176-208 as in the "
     "foundry (MAP03)."),
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
def existing_lumps(own: frozenset[str] = frozenset()) -> set[str]:
    """Every lump name already in use: files under assets/ and work/
    (sprites, textures, sounds...) except this episode's own drafts, and
    every SD name the texture index mentions.

    `own` are this episode's lumps: since D113 (installed 2026-10-22) they
    sit in assets/{textures,flats}/<arctic|naval|taiga>/ and have rows in the
    index, so those copies and rows are not a clash with themselves. A file
    of the same name anywhere else in assets/ still is."""
    names = set()
    sets = {mod.SET_NAME for mod, *_ in SETS}
    for root in (PROJECT_ROOT / "assets", PROJECT_ROOT / "work"):
        if root.is_dir():
            for p in root.rglob("*"):
                if not p.is_file() or p.is_relative_to(ep3lib.WORK_ROOT):
                    continue
                if root.name == "assets" and p.stem.upper() in own and p.parent.name in sets:
                    continue
                names.add(p.stem.upper())
    if TEXTURE_INDEX.is_file():
        names |= set(re.findall(r"\bSD[A-Z0-9]{1,6}\b", TEXTURE_INDEX.read_text(encoding="utf-8"))) - own
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
# The copied result's first line: Episode 2's label, whatever its wording, becomes this sheet's.
JS = re.sub(r"(const L = \[`)[^`$]*\(2026-10-22_P4, D104\)", r"\1Episode 3 textures (2026-10-22_P4, D112)",
            ep2sheet.JS.replace("sd-2026-10-22_P4_episode2-textures", SHEET_KEY))
assert SHEET_KEY in JS and "Episode 3 textures" in JS
TILES_TXT = ep2sheet.TILES_TXT


def items_json(sets_data) -> list[dict]:
    items = []
    for mod, entries, A, V in sets_data:
        by_key = {e["piece"]: e for e in entries}
        for p in mod.PIECES:
            e = by_key[p.key]
            items.append({
                "id": p.key, "set": mod.SET_NAME, "lumps": p.lumps, "kind": "wall" if p.kind == "wall" else "floor/ceiling",
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
                f"<td>{html.escape(p.title)}</td><td>{'wall' if p.kind == 'wall' else 'flat'}</td>"
                f"<td>{p.size[0]}×{p.size[1]}</td><td>{TILES_TXT[p.tiles]}</td>"
                f"<td>v{p.palette}{' + ' + ', '.join(p.v2_ramps) if p.v2_ramps else ''}{' RGBA' if p.masked else ''}</td>"
                f"<td>{html.escape(fam)} (new) — {html.escape(NEW_FAMILIES[fam])}</td>"
                f"<td>{seed}</td><td>proposed</td></tr>")
        for lump, why in getattr(mod, "REUSED", []):
            rows.append(f"<tr><td><code>{lump}</code></td><td>{mod.SET_NAME}</td><td>{html.escape(why)}</td>"
                        f"<td>—</td><td>—</td><td>—</td><td>v1</td><td>existing</td><td>—</td>"
                        f"<td>approved (D107), reused</td></tr>")
    head = ("<tr><th>Lump</th><th>Set</th><th>What it is</th><th>Type</th><th>Size</th><th>Tiles</th><th>Palette</th>"
            "<th>Family</th><th>Seed</th><th>Status</th></tr>")
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
            f'Generator <code>{mod.SCRIPT_REL}</code>, base seed {mod.BATCH_SEED}.</p>'
            f'<h3>The set assembled</h3><div class="ov">{ovs}</div>'
            f'<h3>The pieces</h3><div id="cards-{mod.SET_NAME}"></div>')
    prob_html = ("<p><b>Name check:</b> the " + str(n_lumps) + " proposed lumps are SD, ≤ 8 characters, "
                 "and none clashes with an existing name in <code>assets/</code>, <code>work/</code> or "
                 "<code>TEXTURE-INDEX.md</code>, nor reads as a sprite frame (that is why the console is "
                 "<code>SDRADR</code> and not <code>SDRDR</code>: <code>SDRD</code> is a sprite).</p>") if not problems else (
        "<p><b>Name problems:</b></p><ul>" + "".join(f"<li>{html.escape(p)}</li>" for p in problems) + "</ul>")
    intro = f"""
<div class="intro">
<p><b>What this is (D112, P4).</b> Episode 3's three texture sets, «The Portal», as a <b>draft</b>:
{len(items)} pieces, {n_lumps} lumps, all procedural from our generators, by the same method as the Episode 2 you
approved (fixed seed, palette v1, Doom 1993-96 style, 64/128 px). Nothing is in <code>assets/</code> or the
index: if you say OK, the PM installs them as they are.</p>
<ul>
<li>Each piece is shown <b>on its own</b> (1× and zoomed), as a <b>3×3 mosaic</b> (to see whether it tiles) and in a
<b>sample room</b>: a minimal Doom-like view (320×200, 90°, eye at 41 units, light falling off with distance).
<b>It is not GZDoom</b>: it shows scale and repetition; the real test is in the engine, with the level-designer.</li>
<li><b>Palette:</b> v1 throughout. One exception, with D66 as the precedent: the <b>portal rim</b>
(<code>SDPRTE1</code>) uses v2's <code>mosaic_cobalt</code>, the portal's own (<code>SDPORT1-4</code>), because it is part
of the portal. Nothing else carries cobalt, gold or the Legion's pink.</li>
<li><b>Text:</b> no system font. The submarine's number «471», the container's «ММФ» and the compartment's «3» come
from our alphabet (bigfont, D24); the container's number from the 3×5-pixel digits; the console plates look like text
and say nothing; the <b>invader glyphs</b> are an invented grammar of rings and strokes (not letters of any
alphabet).</li>
<li><b>Three pieces repeat their twin's seed on purpose</b> (the runway with a centre line, the hull with a number,
the deck with a hatch): they are the same surface with something painted on or set into it.</li>
<li><b>Reused, already approved:</b> the water <code>SDWATR1-4</code> for the basin and <code>SDDAM2</code> for the
quay face; the portal <code>SDPORT1-4</code> in the rim's sample room.</li>
</ul>
<p>Mark <b>OK / NO / ?</b> on each one, add notes if you like and press <b>Copy result</b> to paste it to me.</p>
</div>"""
    ask = """
<div class="ask"><p><b>Besides the OK/NO, four questions:</b></p><ol>
<li><b>The acid's green.</b> Palette v1 has no saturated green: the acid (<code>SDACID1-4</code>), the invader metal's
veins and the glyphs are painted in <code>military_green</code> with yellow crests, an olive «toxic» green.
A true acid green is a new ramp in the 30 free slots (palette v3). My recommendation: see it in the engine first;
if it looks like mud in GZDoom, we open the <code>acid_green</code> ramp.</li>
<li><b>Very light snow and radome.</b> The snow, the radome and the runways sit above the walls' 0.45-0.70 band
(ART-BIBLE §6.1): it is an Arctic exterior. The Reich soldiers (dark) read easily; the Legion (pink and chrome)
reads a little worse on white. I propose light 128-160 on the snowy exterior, no more. All right?</li>
<li><b>Blue-grey ice.</b> Without cobalt (that is the portal's), the ice is <code>steel_blue</code>'s blue-grey, like the
Volga's water. All right, or do you want it bluer (that would be another v3 ramp)?</li>
<li><b>Animated and masked.</b> The radar console (<code>SDRADR1-4</code>) and the acid need ANIMDEFS
(mod-engineer; I propose 12 tics per frame for the radar and 8 for the acid). The lattice <code>SDCRAN1</code> is RGBA
like <code>SDCHAN1</code> and <code>SDINSL1</code>. Still to be seen in the engine (D26: the PM does it).</li>
</ol></div>"""
    data = json.dumps(items, ensure_ascii=False)
    sets_js = json.dumps([m.SET_NAME for m, *_ in sets_data])
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Episode 3 textures</title>
<style>{ep2sheet.CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Soviet Doom · Episode 3 textures (draft)</h1>
  <span class="prog"><b id="pDone">0</b> / {len(items)} judged</span>
  <button class="primary" id="copyTop">Copy result</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
{intro}
{"".join(sections)}
<h2>Proposed lump names</h2>
{prob_html}
{lump_table(sets_data)}
<h2>Questions</h2>
{ask}
<h2>Result</h2>
<p class="meta">General comment (optional):</p>
<textarea class="note" id="general" placeholder="Anything about the three sets as a whole"></textarea>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copy result</button><span class="copied" id="copiedBottom"></span> <button id="reset">Clear answers</button></p>
<footer>Origin (a): procedural, <code>tools/art/gen_arctic.py</code> (seed 5700+n), <code>gen_naval.py</code> (5800+n),
<code>gen_taiga.py</code> (5900+n), shared machinery in <code>ep3lib.py</code> on top of <code>ep2lib.py</code>, sheet
<code>{SCRIPT_REL}</code>; PNGs in <code>work/art/episode3/&lt;set&gt;/</code>; tests <code>tests/test_gen_episode3.py</code>.
Palette <code>docs/art/palette.json</code> unmodified. Licence: our own work, CC BY-NC-SA 4.0 (D15). The sample room is NOT
the engine's colormap or mipmaps (NOT VERIFIED in GZDoom). The radar and the acid need ANIMDEFS
(mod-engineer). Nothing installed: if one is good, the PM installs it with your OK.</footer>
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
    problems = name_problems(all_lumps, existing_lumps(frozenset(all_lumps)))
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
