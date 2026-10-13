"""Self-contained HTML sheet builder for the batch-2 proposal previews.

Same house style as tools/art/make_preview.py (inline CSS, no dependencies,
every PNG embedded as a base64 data: URI, nearest-neighbour zoom) but built
for *sweep* sheets: several variants of one texture shown side by side, each
in several states and on top of the walls it will actually sit on, so the CEO
picks a variant in one look instead of over several rounds.

make_preview.py stays the tool for an approved batch: it reads the batch
manifest and the texture index. This one takes whatever cells the generator
hands it, because a sweep has no index rows yet.
"""

from __future__ import annotations

import base64
import datetime as dt
import html
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Zoom factors. 4x is the "Doom at 1080p" feel; the far view is point-sampled
# down by 8 first (see gen_switch.FAR_DIVISOR) and then blown back up, so what
# the CEO judges is the information that survives, not a smooth thumbnail.
ZOOM = 4
FAR_ZOOM = 6

CSS = """
:root{--bg:#1b1c1f;--card:#26282c;--ink:#e8e6e0;--mute:#9a9892;--red:#c8302a;--line:#3a3d44;--warn:#c9a227}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 -apple-system,Helvetica,Arial,sans-serif}
header{padding:20px 28px;border-bottom:2px solid var(--red)}h1{margin:0 0 6px;font-size:22px}
.meta{color:var(--mute);font-size:12px}.intro{max-width:980px;margin:10px 0 0}
section{padding:18px 28px;border-top:1px solid var(--line)}
h2{font-size:16px;margin:0 0 4px;color:var(--mute);text-transform:uppercase;letter-spacing:.08em}
h3{margin:0 0 4px;font-size:18px;font-family:Menlo,monospace}
.lead{max-width:980px;color:var(--mute);font-size:13px;margin:0 0 14px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(620px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px;position:relative}
.card.rec{border-color:var(--warn);box-shadow:0 0 0 2px var(--warn) inset}
.tag{position:absolute;top:12px;right:14px;font-size:11px;color:var(--warn);text-transform:uppercase;letter-spacing:.08em}
.desc{margin:4px 0 10px;max-width:640px}
.row{display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap;margin-bottom:12px}
.v{display:flex;flex-direction:column;gap:4px;font-size:11px;color:var(--mute)}
.v b{color:var(--ink);font-weight:600}
img.px{image-rendering:pixelated;image-rendering:crisp-edges;background:#000;border:1px solid var(--line);display:block}
dl{display:grid;grid-template-columns:max-content 1fr;gap:2px 10px;font-size:12px;margin:8px 0 0}
dt{color:var(--mute)}dd{margin:0;font-family:Menlo,monospace}
table{border-collapse:collapse;font-size:12px;margin-top:6px}
th,td{border:1px solid var(--line);padding:4px 9px;text-align:left}th{color:var(--mute);font-weight:600}
td.n{font-family:Menlo,monospace;text-align:right}
.ask{background:#2b2420;border-left:3px solid var(--warn);padding:10px 14px;max-width:980px;margin-top:10px}
.ask ol{margin:6px 0 0 18px;padding:0}.ask li{margin:4px 0}
.ramps{display:flex;flex-direction:column;gap:3px;font-size:12px}
.ramp{display:flex;align-items:center;gap:8px}.ramp .n{width:140px;color:var(--mute)}
.sw{display:flex}.sw i{display:block;width:13px;height:17px}
footer{padding:16px 28px;color:var(--mute);font-size:12px;border-top:1px solid var(--line)}
"""


def b64(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def img(path: Path, zoom: int, size: tuple[int, int], title: str = "") -> str:
    w, h = size
    return (f'<img class="px" src="{b64(path)}" width="{w * zoom}" height="{h * zoom}" '
            f'alt="{html.escape(title)}" title="{html.escape(title)}">')


def view(label: str, path: Path, zoom: int, size: tuple[int, int]) -> str:
    return f'<div class="v"><b>{html.escape(label)}</b>{img(path, zoom, size, label)}</div>'


def table(headers: list[str], rows: list[list[str]], numeric_from: int = 1) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for r in rows:
        cells = "".join(
            f'<td class="{"n" if i >= numeric_from else ""}">{html.escape(str(c))}</td>'
            for i, c in enumerate(r))
        body += f"<tr>{cells}</tr>"
    return f"<table><tr>{head}</tr>{body}</table>"


def palette_ramps(palette: dict) -> str:
    out = ['<div class="ramps">']
    for r in palette["ramps"]:
        sw = "".join(f'<i style="background:rgb({c[0]},{c[1]},{c[2]})"></i>' for c in r["colours"])
        out.append(f'<div class="ramp"><span class="n">{html.escape(r["name"])}</span>'
                   f'<span class="sw">{sw}</span></div>')
    out.append("</div>")
    return "\n".join(out)


def write_sheet(path: Path, *, lang: str, title: str, subtitle: str, intro: str,
                sections: list[tuple[str, str, str]], footer: str) -> Path:
    """sections = [(heading, lead paragraph, body html), ...]"""
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = "\n".join(
        f'<section><h2>{html.escape(h)}</h2>'
        + (f'<p class="lead">{lead}</p>' if lead else "")
        + f'{inner}</section>'
        for h, lead, inner in sections)
    doc = f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<header><h1>{html.escape(title)}</h1>
<div class="meta">{html.escape(subtitle)} &middot; {stamp}</div>
<p class="intro">{intro}</p></header>
{body}
<footer>{footer}</footer>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")
    return path
