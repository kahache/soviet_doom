"""Build the self-contained HTML preview sheet of a texture batch for the CEO.

Run with the project venv:
  .venv/bin/python tools/art/make_preview.py --stamp 2026-10-09_1530

Reads work/art/batch1/manifest.json (written by gen_soviet_base.py) and
docs/art/palette.json, embeds every PNG as base64 and writes:
  docs/art/previews/<stamp>_F2_batch1-soviet-base.html      (English)
  docs/ru/art/previews/<stamp>_F2_batch1-soviet-base.html   (Russian mirror, D7)

No external dependencies in the HTML: inline CSS, inline JS, data: URIs.
The approve / discard buttons are visual only: they compose a summary the
CEO can paste in chat; nothing is written anywhere.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = PROJECT_ROOT / "work" / "art" / "batch1" / "manifest.json"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
TEXTURE_INDEX = PROJECT_ROOT / "docs" / "art" / "TEXTURE-INDEX.md"
PREVIEW_DIR_EN = PROJECT_ROOT / "docs" / "art" / "previews"
PREVIEW_DIR_RU = PROJECT_ROOT / "docs" / "ru" / "art" / "previews"
SLUG = "F2_batch1-soviet-base"

# The status shown on each card is read from the texture index (the single
# owner of that fact); its vocabulary is English in both index mirrors.
STATUS_COLUMN = "Status"
STATUS_FALLBACK = "proposed"

# Zoom factors shown on the sheet. 4x is the "Doom at 1080p" feel; the 2x2
# tile at 2x shows seams at a size where they would be visible in-game.
ZOOM = 4
TILE_ZOOM = 2

LABELS = {
    "en": {
        "title": "Soviet Doom — texture batch 1: Soviet base (F2)",
        "intro": "Every texture below is procedural (script + seed) and quantised to the mod palette. "
                 "Look at the 4x view for detail and at the 2x2 tile for seams. Mark each card with "
                 "Approve / Discard, add a note if you like, then copy the summary box into the chat. "
                 "The status in the corner of each card comes from docs/art/TEXTURE-INDEX.md: "
                 "only the cards not yet approved need a verdict.",
        "palette": "Palette", "palette_note": "{n} colours in {r} ramps (max 256). Source: docs/art/palette.json.",
        "fonts": "Fonts", "summary": "Summary to paste in chat", "copy": "Copy",
        "approve": "Approve", "discard": "Discard", "reset": "Reset", "note": "note…",
        "lump": "Lump", "kind": "Kind", "wall": "wall", "flat": "flat", "size": "Size", "set": "Set",
        "origin": "Origin", "colours": "Colours used", "seam": "Seam ratio",
        "seam_help": "wrap-edge contrast / strongest interior edge; ≤ 1 means the seam is no stronger than a feature inside the texture",
        "view1": "1x", "view4": "4x", "tile": "2x2 tile", "licence": "Licence",
        "licence_val": "own work, CC BY-NC-SA 4.0 (D15)",
        "status": "status: {s}", "none": "(nothing marked yet)",
        "approved": "APPROVED", "discarded": "DISCARDED", "undecided": "UNDECIDED",
        "mirror": "Russian mirror: docs/ru/art/previews/",
    },
    "ru": {
        "title": "Soviet Doom — партия текстур 1: советская база (F2)",
        "intro": "Все текстуры ниже процедурные (скрипт + зерно) и приведены к палитре мода. "
                 "Смотрите вид 4x для деталей и плитку 2x2 для швов. Отметьте каждую карточку "
                 "«Одобрить» / «Отклонить», при желании добавьте заметку и скопируйте сводку в чат. "
                 "Статус в углу карточки берётся из docs/art/TEXTURE-INDEX.md: вердикт нужен только "
                 "по ещё не одобренным карточкам.",
        "palette": "Палитра", "palette_note": "{n} цветов в {r} рампах (максимум 256). Источник: docs/art/palette.json.",
        "fonts": "Шрифты", "summary": "Сводка для вставки в чат", "copy": "Копировать",
        "approve": "Одобрить", "discard": "Отклонить", "reset": "Сброс", "note": "заметка…",
        "lump": "Ламп", "kind": "Тип", "wall": "стена", "flat": "флэт", "size": "Размер", "set": "Набор",
        "origin": "Происхождение", "colours": "Использовано цветов", "seam": "Коэф. шва",
        "seam_help": "контраст на стыке / самый сильный внутренний контраст; ≤ 1 значит, что шов не заметнее деталей внутри текстуры",
        "view1": "1x", "view4": "4x", "tile": "плитка 2x2", "licence": "Лицензия",
        "licence_val": "собственная работа, CC BY-NC-SA 4.0 (D15)",
        "status": "статус: {s}", "none": "(пока ничего не отмечено)",
        "approved": "ОДОБРЕНО", "discarded": "ОТКЛОНЕНО", "undecided": "НЕ РЕШЕНО",
        "mirror": "Английский оригинал: docs/art/previews/",
    },
}

CSS = """
:root{--bg:#1b1c1f;--card:#26282c;--ink:#e8e6e0;--mute:#9a9892;--red:#c8302a;--green:#6d7a4e;--line:#3a3d44}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif}
header{padding:20px 28px;border-bottom:2px solid var(--red)}h1{margin:0 0 6px;font-size:22px}
.meta{color:var(--mute);font-size:12px}.intro{max-width:900px;margin:10px 0 0}
section{padding:18px 28px}h2{font-size:16px;margin:0 0 10px;color:var(--mute);text-transform:uppercase;letter-spacing:.08em}
.ramps{display:flex;flex-direction:column;gap:4px}.ramp{display:flex;align-items:center;gap:8px;font-size:12px}
.ramp .n{width:130px;color:var(--mute)}.sw{display:flex}.sw i{display:block;width:14px;height:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(560px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px;position:relative}
.card.ok{border-color:#5a9a4a;box-shadow:0 0 0 2px #5a9a4a inset}.card.no{border-color:var(--red);box-shadow:0 0 0 2px var(--red) inset;opacity:.75}
.card h3{margin:0 0 4px;font-size:18px;font-family:Menlo,monospace}.card .st{position:absolute;top:12px;right:14px;font-size:11px;color:var(--mute)}
.desc{margin:4px 0 10px}.views{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap}
.v{display:flex;flex-direction:column;gap:4px;font-size:11px;color:var(--mute)}
img.px,.tile{box-sizing:content-box;image-rendering:pixelated;image-rendering:crisp-edges;background:#000;border:1px solid var(--line)}
.tile{background-repeat:repeat}
dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 10px;font-size:12px;margin:10px 0 0}dt{color:var(--mute)}dd{margin:0;font-family:Menlo,monospace}
.btns{display:flex;gap:8px;margin-top:10px;align-items:center}
button{cursor:pointer;border:1px solid var(--line);background:#33363c;color:var(--ink);padding:5px 12px;border-radius:4px;font-size:13px}
button.a{border-color:#5a9a4a}button.d{border-color:var(--red)}
input.note{flex:1;background:#1f2124;border:1px solid var(--line);color:var(--ink);padding:5px 8px;border-radius:4px;font-size:12px}
textarea{width:100%;min-height:150px;background:#111214;color:var(--ink);border:1px solid var(--line);font:12px Menlo,monospace;padding:8px}
.note-font{font-size:12px;color:var(--mute);max-width:900px}
"""

JS = """
const L=%s;const state={};
function mark(id,v){state[id]=state[id]||{};state[id].v=v;const c=document.getElementById('c-'+id);c.classList.remove('ok','no');if(v==='ok')c.classList.add('ok');if(v==='no')c.classList.add('no');render();}
function note(id,t){state[id]=state[id]||{};state[id].n=t;render();}
function render(){const ids=[...document.querySelectorAll('.card')].map(c=>c.dataset.lump);const lines=[];
for(const g of ['ok','no','und']){const items=ids.filter(i=>(state[i]&&state[i].v||'und')===g);if(!items.length)continue;
const head=g==='ok'?L.approved:g==='no'?L.discarded:L.undecided;lines.push(head+': '+items.map(i=>i+((state[i]&&state[i].n)?' ('+state[i].n+')':'')).join(', '));}
document.getElementById('sum').value=lines.length?lines.join('\\n'):L.none;}
function copySum(){const t=document.getElementById('sum');t.select();document.execCommand('copy');}
window.addEventListener('DOMContentLoaded',render);
"""


def b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def index_statuses(index_md: Path = TEXTURE_INDEX) -> dict[str, str]:
    """{lump: status} from the Markdown tables of the texture index: any row
    whose first cell is a back-quoted lump, status taken from the column
    named STATUS_COLUMN of the nearest header above it."""
    statuses, status_col = {}, None
    for line in index_md.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if STATUS_COLUMN in cells:
            status_col = cells.index(STATUS_COLUMN)
        elif status_col is not None and cells[0].startswith("`") and len(cells) > status_col:
            statuses[cells[0].strip("`")] = cells[status_col]
    return statuses


def build(lang: str, manifest: dict, palette: dict, stamp: str) -> str:
    L = LABELS[lang]
    e = html.escape
    statuses = index_statuses()
    ramps_html = "".join(
        f'<div class="ramp"><span class="n">{e(r["name"])}</span><span class="sw">'
        + "".join(f'<i style="background:rgb({c[0]},{c[1]},{c[2]})" title="{c}"></i>' for c in r["colours"])
        + "</span></div>"
        for r in palette["ramps"]
    )
    extras_html = '<div class="ramp"><span class="n">extras</span><span class="sw">' + "".join(
        f'<i style="background:rgb({x["rgb"][0]},{x["rgb"][1]},{x["rgb"][2]})" title="{x["name"]}"></i>' for x in palette["extras"]
    ) + "</span></div>"
    cards = []
    for t in manifest["textures"]:
        src = b64(PROJECT_ROOT / t["file"])
        w, h = t["width"], t["height"]
        desc = t["description_" + lang]
        cards.append(f"""
<div class="card" id="c-{t['lump']}" data-lump="{t['lump']}">
  <h3>{t['lump']}</h3><span class="st">{e(L['status'].format(s=statuses.get(t['lump'], STATUS_FALLBACK)))}</span>
  <p class="desc">{e(desc)}</p>
  <div class="views">
    <div class="v">{L['view1']}<img class="px" src="{src}" width="{w}" height="{h}" alt="{t['lump']}"></div>
    <div class="v">{L['view4']}<img class="px" src="{src}" width="{w * ZOOM}" height="{h * ZOOM}" alt="{t['lump']} x{ZOOM}"></div>
    <div class="v">{L['tile']}<div class="tile" style="width:{w * 2 * TILE_ZOOM}px;height:{h * 2 * TILE_ZOOM}px;background-image:url('{src}');background-size:{w * TILE_ZOOM}px {h * TILE_ZOOM}px"></div></div>
  </div>
  <dl>
    <dt>{L['kind']}</dt><dd>{L[t['kind']]}</dd>
    <dt>{L['size']}</dt><dd>{w}×{h}</dd>
    <dt>{L['set']}</dt><dd>{e(t['set'])}</dd>
    <dt>{L['origin']}</dt><dd>{e(t['script'])} · seed {t['seed']} (BATCH_SEED {manifest['batch_seed']} + {t['seed_offset']})</dd>
    <dt>{L['colours']}</dt><dd>{t['colours_used']} / {palette['count']}</dd>
    <dt>{L['seam']}</dt><dd title="{e(L['seam_help'])}">{t['seam_score']:.2f}</dd>
    <dt>{L['licence']}</dt><dd>{e(L['licence_val'])}</dd>
  </dl>
  <div class="btns">
    <button class="a" onclick="mark('{t['lump']}','ok')">{L['approve']}</button>
    <button class="d" onclick="mark('{t['lump']}','no')">{L['discard']}</button>
    <button onclick="mark('{t['lump']}','und')">{L['reset']}</button>
    <input class="note" placeholder="{L['note']}" oninput="note('{t['lump']}',this.value)">
  </div>
</div>""")
    font_note = manifest["font_note_" + lang]
    labels_json = json.dumps({k: L[k] for k in ("approved", "discarded", "undecided", "none")}, ensure_ascii=False)
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"><title>{e(L['title'])}</title><style>{CSS}</style></head>
<body>
<header>
  <h1>{e(L['title'])}</h1>
  <div class="meta">{stamp} · set <b>{e(manifest['set'])}</b> · {len(manifest['textures'])} textures · {e(manifest['script'])} · BATCH_SEED {manifest['batch_seed']} · {e(L['mirror'])}</div>
  <p class="intro">{e(L['intro'])}</p>
</header>
<section><h2>{L['summary']}</h2><textarea id="sum" readonly></textarea><div class="btns"><button onclick="copySum()">{L['copy']}</button></div></section>
<section><h2>{L['palette']}</h2><p class="meta">{e(L['palette_note'].format(n=palette['count'], r=len(palette['ramps'])))}</p><div class="ramps">{ramps_html}{extras_html}</div></section>
<section><h2>{L['fonts']}</h2><p class="note-font">{e(font_note)}</p></section>
<section><div class="grid">{''.join(cards)}</div></section>
<script>{JS % labels_json}</script>
</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM prefix of the preview file (default: now)")
    args = ap.parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    palette = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    for lang, out_dir in (("en", PREVIEW_DIR_EN), ("ru", PREVIEW_DIR_RU)):
        out_dir.mkdir(parents=True, exist_ok=True)
        out = out_dir / f"{args.stamp}_{SLUG}.html"
        out.write_text(build(lang, manifest, palette, args.stamp), encoding="utf-8")
        print(f"wrote {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
