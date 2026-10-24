"""The D74 weapon-sound alternatives again, this time with the weapon moving (D92).

The CEO could not judge the 15 alternatives of
docs/art/previews/2026-10-15_0033_M3_listening-alternatives.html without
seeing the weapon: "no tengo el gif del movimiento del arma" ("I don't have
the gif of the weapon moving"). This writes a
new page where every row plays the installed first-person sprites at game
speed (35 tics/s) on a small 320x200 mock, with the sound started on the
tic the game starts it:

  SDIZRLD   izh.zs Reload state, frame by frame; the sound on the tic of its
            A_StartSound("sd/weapon/izh/reload").
  SDRKFIR   roks3.zs Fire state with the trigger held ~1.5 s: a jet every
            3 tics, and every jet restarts the sound on CHAN_WEAPON (the
            previous one is cut, as GZDoom does); the last one rings out.
  pickups   walk up to the world sprite, touch (sound, gold flash, pickup
            message), the weapon in hand lowers and the new one raises at
            GZDoom's default 6 units per tic (16 + 16 tics).

Nothing is hard-coded from memory: the state sequences are parsed from
src/zscript/weapons/*.zs, the sprite offsets from the PNGs' grAb chunks,
the pickup messages from src/lumps/LANGUAGE, the labels and paths of the 15
alternatives from the 2026-10-15_0033 page. The audio is embedded as data
URIs as well as referenced by relative path: Chrome refuses fetch() on
file://, and WebAudio (needed to restart the flame sound every 3 tics on
the exact tic) has to read the bytes.

Run:  .venv/Scripts/python.exe tools/audio/gen_weapon_alts_animated.py [--stamp YYYY-MM-DD_HHMM]
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIEWS = ROOT / "docs" / "art" / "previews"
OLD_PAGE = PREVIEWS / "2026-10-15_0033_M3_listening-alternatives.html"
WEAPONS = ROOT / "src" / "zscript" / "weapons"
SPRITES = ROOT / "assets" / "sprites"
LANGUAGE = ROOT / "src" / "lumps" / "LANGUAGE"
REL = "../../../"  # from docs/art/previews/ to the repo root

TICRATE = 35
WEAPONTOP, WEAPONBOTTOM, RAISE = 32, 128, 6  # GZDoom defaults, no weapon overrides them
PRE, POST = 10, 18          # idle tics before / after the action
HELD = 52                   # ROKS-3 trigger held 52 tics = 1.49 s
WALK, STEP, START_D = 24, 12, 320  # pickup approach: 24 tics at 12 units/tic from 320 units
BONUS = 6                   # Doom's BONUSADD: the gold flash lasts 6 tics

FRAME_RE = re.compile(r"^\s*(\w{4})\s+([A-Z])\s+(-?\d+)\s*(Bright\s+)?(.*?);")

# lump -> (weapon dir, world sprite, new ready frame, weapon in hand before, LANGUAGE key)
PICKUPS = {
    "SDTTPKP": ("tt33", "SDTPA0", "SDTTA0", "SDAXA0", "SD_PICKUP_TOKAREV"),
    "SDAXPKP": ("ice_axe", "SDAPA0", "SDAXA0", "SDTTA0", "SD_PICKUP_ICEAXE"),
    "SDIZPKP": ("izh", "SDIPA0", "SDIZA0", "SDTTA0", "SD_PICKUP_IZH"),
}
SPRITE_DIRS = ["tt33", "ice_axe", "izh", "roks3"]


def parse_state(zs: Path, label: str) -> list[dict]:
    """Frame lines of one state label, up to its Goto/Loop/Stop."""
    lines, out, on = zs.read_text(encoding="utf-8").splitlines(), [], False
    for ln in lines:
        code = ln.split("//", 1)[0]
        if re.match(rf"^\s*{label}:\s*$", code):
            on = True
            continue
        if not on:
            continue
        if re.match(r"^\s*(Goto|Loop|Stop|Wait)\b", code):
            break
        m = FRAME_RE.match(code)
        if m:
            out.append({"spr": m[1] + m[2] + "0", "tics": int(m[3]),
                        "bright": bool(m[4]), "action": m[5].strip()})
    if not out:
        raise ValueError(f"no frames under {label}: in {zs.name}")
    return out


def action_sound(zs: Path, action: str) -> str | None:
    """The sound an action starts: inline A_StartSound, or inside the action's body."""
    m = re.search(r'A_StartSound\("([^"]+)"', action)
    if m:
        return m[1]
    name = re.match(r"(\w+)", action)
    if not name:
        return None
    body = re.search(rf"action void {name[1]}\s*\(\)\s*\{{(.*?)\n\t\}}", zs.read_text(encoding="utf-8"), re.S)
    m = body and re.search(r'A_StartSound\("([^"]+)"', body[1])
    return m[1] if m else None


def grab(png: Path) -> tuple[int, int, int, int]:
    d = png.read_bytes()
    w, h = struct.unpack(">II", d[16:24])
    i = d.find(b"grAb")
    ox, oy = struct.unpack(">ii", d[i + 4:i + 12]) if i > 0 else (0, 0)
    return w, h, ox, oy


def frame(spr, sy=WEAPONTOP, sx=0, **kw):
    f = {"s": spr, "x": sx, "y": sy}
    f.update({k: v for k, v in kw.items() if v})
    return f


def izh_reload() -> dict:
    zs = WEAPONS / "izh.zs"
    ready = parse_state(zs, "Ready")[0]["spr"]
    frames = [frame(ready) for _ in range(PRE)]
    sounds, marks = [], []
    for st in parse_state(zs, "Reload"):
        snd = action_sound(zs, st["action"])
        if snd == "sd/weapon/izh/reload":
            sounds.append([len(frames), None])
            marks.append([len(frames), "the reload and its sound start (A_StartSound)"])
        if "ReloadIzh" in st["action"]:
            marks.append([len(frames), "the game loads the shells (A_SD_ReloadIzh)"])
        frames += [frame(st["spr"]) for _ in range(st["tics"])]
    if len(sounds) != 1:
        raise ValueError("izh.zs Reload: expected one sd/weapon/izh/reload hook")
    marks.append([len(frames), "back to Ready"])
    frames += [frame(ready) for _ in range(POST)]
    return {"frames": frames, "sounds": sounds, "marks": marks}


def roks_fire(held: int = HELD) -> dict:
    zs = WEAPONS / "roks3.zs"
    ready = parse_state(zs, "Ready")[0]["spr"]
    fire, flash = parse_state(zs, "Fire"), parse_state(zs, "Flash")
    frames = [frame(ready) for _ in range(PRE)]
    release, sounds, marks = PRE + held, [], [[PRE, "you pull the trigger"]]
    flash_seq: list[dict] = []
    t, i, guard = PRE, 0, 0
    while i < len(fire):
        guard += 1
        if guard > 1000:
            raise RuntimeError("roks3.zs Fire never ends")
        st = fire[i]
        if "A_GunFlash" in st["action"]:
            flash_seq = [fl for fl in flash for _ in range(fl["tics"])]
        if action_sound(zs, st["action"]) == "sd/weapon/roks3/fire":
            if sounds and sounds[-1][1] is None:
                sounds[-1][1] = t           # CHAN_WEAPON: the new jet cuts the old one
            sounds.append([t, None])
        if "A_ReFire" in st["action"] and t < release:
            i = 0                           # refire on entry: this frame is never shown
            continue
        for _ in range(st["tics"]):
            fl = flash_seq.pop(0) if flash_seq else None
            frames.append(frame(st["spr"], fl=fl and fl["spr"],
                                light=bool(fl and "A_Light1" in fl["action"])))
            t += 1
        i += 1
    marks.append([release, "you release the trigger"])
    marks.append([len(frames), "back to Ready"])
    frames += [frame(ready) for _ in range(POST)]
    return {"frames": frames, "sounds": sounds, "marks": marks}


def bob(t: int) -> tuple[int, int]:
    """A_WeaponReady's bob while running (Doom: 64-tic angle, x cos, y |sin|, amplitude 16 max)."""
    import math
    a = 2 * math.pi * t / 64
    return round(8 * math.cos(a)), WEAPONTOP + round(8 * abs(math.sin(a)))


def pickup(lump: str) -> dict:
    _, world, new, old, _ = PICKUPS[lump]
    frames = []
    for t in range(WALK):
        sx, sy = bob(t)
        frames.append(frame(old, sy, sx, w=START_D - STEP * t, walk=STEP * t))
    touch = len(frames)
    # The touch tic: the player's psprites ticked before the move that touched
    # the item, so the weapon in hand starts lowering on the next tic.
    frames.append(frame(old, walk=STEP * WALK, b=BONUS, msg=1))
    sy = WEAPONTOP
    for k in range(1, 99):
        sy = min(WEAPONBOTTOM, sy + RAISE)
        frames.append(frame(old, sy, walk=STEP * WALK, b=max(0, BONUS - k), msg=1))
        if sy >= WEAPONBOTTOM:
            break
    lowered = len(frames)
    sy = WEAPONBOTTOM
    while sy > WEAPONTOP:                   # Select: A_Raise, 6 units per tic
        sy = max(WEAPONTOP, sy - RAISE)
        frames.append(frame(new, sy, walk=STEP * WALK, b=max(0, BONUS - (len(frames) - touch)), msg=1))
    up = len(frames)
    frames += [frame(new, walk=STEP * WALK, msg=1) for _ in range(POST)]
    marks = [[touch, "you touch it: sound, flash and message"],
             [lowered, "the weapon in hand is down; the new one raises"],
             [up, "up, ready"]]
    return {"frames": frames, "sounds": [[touch, None]], "marks": marks, "world": world}


def language() -> dict:
    out = {}
    for ln in LANGUAGE.read_text(encoding="utf-8").splitlines():
        m = re.match(r'\s*(SD_PICKUP_\w+)\s*=\s*"(.*)";', ln)
        if m and m[1] not in out:           # the first block is English
            out[m[1]] = m[2]
    return out


def old_items() -> list[dict]:
    m = re.search(r"const ITEMS = (\[.*?\]);\n", OLD_PAGE.read_text(encoding="utf-8"), re.S)
    items = json.loads(m[1])
    if len(items) != 15:
        raise ValueError(f"expected 15 alternatives, got {len(items)}")
    return items


def data_uri(rel: str) -> str:
    p = ROOT / rel
    mime = "audio/ogg" if p.suffix == ".ogg" else "audio/wav"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def build(stamp: str) -> tuple[str, dict]:
    items, msgs = old_items(), language()
    anims = {"SDIZRLD": izh_reload(), "SDRKFIR": roks_fire()}
    for lump, (_, _, _, _, key) in PICKUPS.items():
        anims[lump] = pickup(lump)
        anims[lump]["msg"] = msgs[key]
    sprites = {}
    for d in SPRITE_DIRS:
        for png in sorted((SPRITES / d).glob("*.png")):
            w, h, ox, oy = grab(png)
            sprites[png.stem] = {"src": f"{REL}assets/sprites/{d}/{png.name}", "w": w, "h": h, "ox": ox, "oy": oy}
    audio = {}
    for it in items:
        for key in ("src", "rej", "repSrc"):
            rel = it[key].removeprefix(REL)
            audio[it[key]] = data_uri(rel)
    data = {"items": items, "anims": anims, "sprites": sprites, "tic": TICRATE}
    page = TEMPLATE.replace("__STAMP__", stamp)
    page = page.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    page = page.replace("__AUDIO__", json.dumps(audio, separators=(",", ":")))
    return page, data


def main(argv=None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=_dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    ap.add_argument("--out-dir", type=Path, default=PREVIEWS)
    a = ap.parse_args(argv)
    page, _ = build(a.stamp)
    out = a.out_dir / f"{a.stamp}_M3_listening-alternatives-animated.html"
    out.write_text(page, encoding="utf-8", newline="\n")
    print(out)
    return out


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Alternatives with the weapon</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
.prog{font-variant-numeric:tabular-nums;color:var(--mute)}.prog b{color:var(--ink)}
.bar{flex:1 1 160px;height:6px;background:var(--chip);border-radius:3px;overflow:hidden;min-width:120px}
.bar i{display:block;height:100%;background:var(--accent);width:0}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
label.chk{color:var(--mute);user-select:none}
.intro p{margin:6px 0}.intro ul{margin:6px 0;padding-left:20px}
details.grp{margin:14px 0;border:1px solid var(--line);border-radius:8px;background:var(--card)}
details.grp>summary{cursor:pointer;padding:10px 12px;font-weight:650;font-size:15px;list-style:none;display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
details.grp>summary::-webkit-details-marker{display:none}
details.grp>summary::before{content:"\25B8";color:var(--mute)}
details.grp[open]>summary::before{content:"\25BE"}
.gcount{margin-left:auto;font-weight:400;color:var(--mute);font-size:13px;font-variant-numeric:tabular-nums}
.rejnote{font-weight:400;color:var(--mute);font-size:13px}
.tag{display:inline-block;font-size:11px;border-radius:10px;padding:0 7px;margin-left:4px;border:1px solid var(--line);color:var(--mute)}
.tag.no{border-color:var(--no);color:var(--no)}.tag.q{border-color:var(--q);color:var(--q)}
.row{display:grid;grid-template-columns:minmax(0,640px) minmax(0,1fr);gap:10px 18px;padding:12px;border-top:1px solid var(--line)}
.row.hide{display:none}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
canvas.scr{display:block;width:100%;max-width:640px;aspect-ratio:320/200;image-rendering:pixelated;image-rendering:crisp-edges;background:#000;border-radius:4px;cursor:pointer}
.tl{position:relative;height:14px;margin-top:6px;background:var(--chip);border-radius:3px;max-width:640px}
.tl .mk{position:absolute;top:0;bottom:0;width:2px;background:var(--mute)}
.tl .mk.snd{background:var(--accent)}
.tl .ph{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--ink)}
.clock{font:12px ui-monospace,Consolas,monospace;color:var(--mute);margin-top:3px;font-variant-numeric:tabular-nums}
.marks{margin:4px 0 0;padding-left:18px;font-size:12.5px;color:var(--mute)}
.marks li.on{color:var(--ink);font-weight:600}
.name code{font:600 14px ui-monospace,Consolas,monospace}
.ev{display:inline-block;background:var(--chip);border-radius:10px;padding:0 8px;margin-left:6px;font-size:12px;color:var(--mute)}
.what{margin:3px 0}
.meta{color:var(--mute);font-size:12.5px;margin:2px 0}.meta b{color:var(--ink);font-weight:600}
.snds{display:flex;flex-direction:column;gap:5px;margin:10px 0}
.snds button{text-align:left}
.snds button.sel{border-color:var(--accent);box-shadow:inset 3px 0 var(--accent);font-weight:600}
button.play{font-weight:650;padding:7px 14px}
.btns{display:flex;gap:6px;margin-top:10px}
.btns button{flex:1;font-weight:650;padding:6px 0}
.btns button.on.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btns button.on.no{background:var(--no);border-color:var(--no);color:#fff}
.btns button.on.q{background:var(--q);border-color:var(--q);color:#111}
textarea.note{width:100%;min-height:34px;margin-top:6px;resize:vertical;font:inherit;font-size:13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 7px}
#result{width:100%;min-height:150px;font:12.5px ui-monospace,Consolas,monospace;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink);padding:10px}
.copied{color:var(--ok);font-weight:600;margin-left:8px}
footer{color:var(--mute);font-size:12.5px;margin-top:24px}
@media (max-width:1000px){.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>M3 sound alternatives, with the weapon moving</h1>
  <span class="prog">Judged <b id="pDone">0</b> of <b>15</b></span>
  <span class="bar"><i id="pBar"></i></span>
  <label class="chk"><input type="checkbox" id="onlyOpen"> unjudged only</label>
  <button class="primary" id="copyTop">Copy result</button><span id="copied" class="copied"></span>
</div></header>
<div class="wrap">
<section class="intro">
  <p>The same 15 alternatives as the 15 October sheet (D74), now <b>with the weapon moving</b> (D92): each row shows the frames installed in the game, at game speed (35 tics per second), and the sound starts on the same tic the game starts it. Press <b>▶ play</b> (or the screen). Below the screen you can switch the sound: the alternative, the rejected draft and what plays today (Freedoom), with the same animation.</p>
  <ul>
    <li><b>IZh reload:</b> frames D, C, B, A of <code>izh.zs</code> (6 + 8 + 8 + 8 tics); the sound starts with frame D and the game loads the shells on the last one.</li>
    <li><b>Flamethrower:</b> the trigger held 1.5 s. Every 3 tics a jet comes out and the game <b>restarts the sound</b>, cutting the previous one; the same happens here. On release, the last one plays out in full.</li>
    <li><b>Pickup:</b> you walk up to the weapon on the floor, touch it (sound, gold flash and message), the weapon in your hand lowers and the new one raises (16 + 16 tics, as in the game). For the TT-33 you hold the ice axe so the switch shows: in a normal game you already start with the TT-33.</li>
    <li>Volume: the alternatives are already raised; the rejected ones stay at the old, lower volume. Compare the character, not the volume.</li>
    <li>The screen is a 320×200 mock (grey MAP01-style wall and floor, a plain status bar) scaled 2×. The weapon is placed with each PNG's offsets, as in the original Doom with the status bar visible (16 pixels higher than without it; in GZDoom <b>not verified</b> in the engine).</li>
  </ul>
</section>
<main id="groups"></main>
<section>
  <h2 style="font-size:16px;margin:24px 0 6px">Result to paste into the chat</h2>
  <p class="meta">It updates by itself. If the button does not copy (some browsers block it on local files), select the text and press Ctrl+C.</p>
  <textarea id="result" readonly></textarea>
  <p><button class="primary" id="copyBottom">Copy result</button> <button id="reset">Clear all my answers</button></p>
</section>
<footer>Generated __STAMP__ by sound-designer with <code>tools/audio/gen_weapon_alts_animated.py</code>. States read from <code>src/zscript/weapons/izh.zs</code> and <code>roks3.zs</code>; sprites from <code>assets/sprites/</code> (relative path: do not move the page out of <code>docs/art/previews/</code>). Audio: <code>work/audio/alt/</code>, <code>work/audio/sfx/weapons/ogg/</code>, <code>work/audio/preview/freedoom/</code>; it is also embedded in the page because the browser does not let WebAudio read local files.</footer>
</div>
<script>
const D = __DATA__;
const AUD = __AUDIO__;
const TIC = D.tic, VIEWH = 168, CY = 84, EYE = 41, PROJ = 160, SBAR = 16;
const KEY = "sd-m3-alternatives-animated-__STAMP__";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
function st(id){ return S[id] || (S[id] = {v:"", n:""}); }
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const secs = t => (t / TIC).toFixed(2) + " s";

/* sprites: relative paths to assets/ */
const IMG = {};
let pending = 0;
for (const [k, s] of Object.entries(D.sprites)) {
  const im = new Image(); pending++;
  im.onload = im.onerror = () => { if (--pending === 0) D.items.forEach(it => draw(it.id, 0)); };
  im.src = s.src; IMG[k] = im;
}
const ok = k => IMG[k] && IMG[k].complete && IMG[k].naturalWidth > 0;

/* the mock: one grey wall, floor, ceiling, status bar strip */
function scene(g, walk, light){
  const L = light ? 1.25 : 1, c = (r, gg, b) => `rgb(${Math.min(255, r*L)|0},${Math.min(255, gg*L)|0},${Math.min(255, b*L)|0})`;
  const dist = 640 - (walk || 0), s = PROJ / dist;
  const top = Math.round(CY - (128 - EYE) * s), bot = Math.round(CY + EYE * s);
  g.fillStyle = c(58, 56, 54); g.fillRect(0, 0, 320, top);
  g.fillStyle = c(108, 106, 102); g.fillRect(0, top, 320, bot - top);
  g.fillStyle = c(78, 76, 72);
  const bh = 16 * s, bw = 32 * s;
  for (let r = 0, y = bot; y > top; r++, y -= bh) {
    g.fillRect(0, Math.round(y), 320, 1);
    const off = (r % 2) * bw / 2;
    for (let x = 160 - 8 * bw + off; x < 320; x += bw) g.fillRect(Math.round(x), Math.round(y - bh), 1, Math.round(bh));
  }
  g.fillStyle = c(84, 82, 78); g.fillRect(0, bot, 320, VIEWH - bot);
  g.fillStyle = c(66, 64, 60);
  for (let z = dist - 64; z > 8; z -= 64) { const y = Math.round(CY + EYE * PROJ / z); if (y < VIEWH) g.fillRect(0, y, 320, 1); }
  for (let wx = -320; wx <= 320; wx += 64) { g.beginPath(); g.moveTo(160 + wx * s, bot); g.lineTo(160 + wx * PROJ / 8, CY + EYE * PROJ / 8); g.strokeStyle = c(66, 64, 60); g.lineWidth = 1; g.stroke(); }
}
function spr(g, k, x, y){
  const s = D.sprites[k]; if (!ok(k)) return;
  g.drawImage(IMG[k], Math.round(x - s.ox), Math.round(y - s.oy - SBAR));
}
function draw(id, tic){
  const it = D.items.find(i => i.id === id), A = D.anims[it.lump];
  const cv = document.getElementById("c-" + id), g = cv.getContext("2d");
  const f = A.frames[Math.min(tic, A.frames.length - 1)];
  g.imageSmoothingEnabled = false;
  g.save(); g.beginPath(); g.rect(0, 0, 320, VIEWH); g.clip();
  scene(g, f.walk, f.light);
  if (f.w && ok(A.world)) {             /* the world pickup, standing on the floor, 40 units to the left */
    const w = D.sprites[A.world], s = PROJ / f.w;
    const x = 160 - 40 * s, y = CY + EYE * s;
    g.drawImage(IMG[A.world], Math.round(x - w.ox * s), Math.round(y - w.oy * s), Math.round(w.w * s), Math.round(w.h * s));
  }
  spr(g, f.s, f.x, f.y);
  if (f.fl) spr(g, f.fl, f.x, f.y);
  if (f.b) { g.fillStyle = "rgba(255,200,40,0.18)"; g.fillRect(0, 0, 320, VIEWH); }
  if (f.msg && A.msg) { g.font = "8px monospace"; g.fillStyle = "#e04030"; g.textBaseline = "top"; g.fillText(A.msg, 2, 2); }
  g.restore();
  g.fillStyle = "#2a2520"; g.fillRect(0, VIEWH, 320, 200 - VIEWH);
  g.fillStyle = "#4d443a"; g.fillRect(0, VIEWH, 320, 1);
  const ph = document.getElementById("ph-" + id); if (ph) ph.style.left = (100 * tic / (A.frames.length - 1)) + "%";
  const ck = document.getElementById("ck-" + id); if (ck) ck.textContent = `tic ${tic} / ${A.frames.length - 1} · ${secs(tic)}`;
  document.querySelectorAll(`#mk-${id} li`).forEach(li => li.classList.toggle("on", +li.dataset.t <= tic && (li.nextElementSibling ? +li.nextElementSibling.dataset.t > tic : true)));
}

/* audio: WebAudio, sounds scheduled on the tic the game starts (and cuts) them */
let AC = null, master = null;
const BUF = {};
async function buffer(path){
  if (BUF[path]) return BUF[path];
  let ab = null;
  try { const r = await fetch(path); if (r.ok) ab = await r.arrayBuffer(); } catch (e) {}
  if (!ab) ab = await (await fetch(AUD[path])).arrayBuffer();
  return BUF[path] = await AC.decodeAudioData(ab);
}
let cur = null;
function stopAll(){
  if (!cur) return;
  cur.srcs.forEach(s => { try { s.stop(); } catch (e) {} });
  cancelAnimationFrame(cur.raf); const id = cur.id; cur = null; draw(id, 0);
}
async function play(id){
  stopAll();
  if (!AC) { AC = new (window.AudioContext || window.webkitAudioContext)(); master = AC.createGain(); master.gain.value = 0.9; master.connect(AC.destination); }
  if (AC.state === "suspended") await AC.resume();
  const it = D.items.find(i => i.id === id), A = D.anims[it.lump], path = it[st(id).snd || "src"];
  let b; try { b = await buffer(path); } catch (e) { document.getElementById("ck-" + id).textContent = "could not read the audio: " + path; return; }
  const me = {id, srcs: [], raf: 0}; cur = me;
  const t0 = AC.currentTime + 0.06;
  for (const [a, z] of A.sounds) {
    const s = AC.createBufferSource(); s.buffer = b; s.connect(master);
    s.start(t0 + a / TIC); if (z !== null) s.stop(t0 + z / TIC); me.srcs.push(s);
  }
  const step = () => {
    if (cur !== me) return;
    const tic = Math.max(0, Math.floor((AC.currentTime - t0) * TIC));
    if (tic >= A.frames.length) { draw(id, A.frames.length - 1); cur = null; return; }
    draw(id, tic); me.raf = requestAnimationFrame(step);
  };
  step();
}

const SND = it => [["src", `Alternative ${it.id.slice(-1)} · ${it.label}`], ["rej", `The rejected one (${it.lump}, you said ${it.verdict})`], ["repSrc", `In the game today: ${it.rep}`]];
function rowHTML(it){
  const A = D.anims[it.lump], s = st(it.id), n = A.frames.length - 1;
  const snd = new Set(A.sounds.map(x => x[0]));
  const mk = A.marks.map(([t]) => `<i class="mk${snd.has(t) ? " snd" : ""}" style="left:${100 * t / n}%"></i>`).join("");
  const restarts = A.sounds.length > 1 ? `<div class="meta">The sound starts ${A.sounds.length} times (every ${A.sounds[1][0] - A.sounds[0][0]} tics), cutting the previous one; the last one plays out in full.</div>` : "";
  return `<div class="row" id="r-${it.id}" data-id="${it.id}">
    <div><canvas class="scr" id="c-${it.id}" width="320" height="200" title="play"></canvas>
      <div class="tl"><span>${mk}</span><i class="ph" id="ph-${it.id}"></i></div>
      <div class="clock" id="ck-${it.id}">tic 0 / ${n} · ${secs(0)}</div>
      <ol class="marks" id="mk-${it.id}">${A.marks.map(([t, l]) => `<li data-t="${t}">tic ${t} (${secs(t)}): ${esc(l)}</li>`).join("")}</ol>
      ${restarts}</div>
    <div><div class="name"><code>${esc(it.id)}</code><span class="ev">${esc(it.ev)}</span></div>
      <div class="what"><b>${esc(it.label)}.</b> ${esc(it.what)}</div>
      <div class="meta"><b>Level:</b> ${esc(it.lvl)}</div>
      <div class="snds">${SND(it).map(([k, l]) => `<button data-snd="${k}" class="${(s.snd || "src") === k ? "sel" : ""}">${esc(l)}</button>`).join("")}</div>
      <button class="primary play">▶ play</button>
      <div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
      <textarea class="note" placeholder="Note (optional)">${esc(s.n || "")}</textarea></div>
  </div>`;
}
function build(){
  let h = "";
  for (const L of [...new Set(D.items.map(i => i.lump))]) {
    const its = D.items.filter(i => i.lump === L), a = its[0];
    const tag = a.verdict === "NO" ? `<span class="tag no">you said NO</span>` : `<span class="tag q">you said ?</span>`;
    h += `<details class="grp" open><summary><code>${esc(L)}</code> ${esc(a.group)} · ${esc(a.ev)} ${tag}<span class="rejnote">rejected: ${esc(a.rejWhat)}</span><span class="gcount" data-l="${esc(L)}"></span></summary>`;
    for (const it of its) h += rowHTML(it);
    h += `</details>`;
  }
  document.getElementById("groups").innerHTML = h;
  for (const it of D.items) { paint(it.id); draw(it.id, 0); }
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok", "v-no", "v-q"); if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
  r.querySelectorAll(".snds button").forEach(b => b.classList.toggle("sel", b.dataset.snd === (s.snd || "src")));
  r.classList.toggle("hide", document.getElementById("onlyOpen").checked && !!s.v);
}
function summary(){
  const I = D.items, by = v => I.filter(i => st(i.id).v === v).map(i => i.id), done = I.filter(i => st(i.id).v).length;
  document.getElementById("pDone").textContent = done;
  document.getElementById("pBar").style.width = (100 * done / I.length) + "%";
  for (const L of new Set(I.map(i => i.lump))) {
    const g = I.filter(i => i.lump === L), d = g.filter(i => st(i.id).v).length;
    const el = document.querySelector(`.gcount[data-l="${L}"]`); if (el) el.textContent = `${d} / ${g.length}`;
  }
  const notes = I.filter(i => (st(i.id).n || "").trim()).map(i => `${i.id}: «${st(i.id).n.trim().replace(/\s+/g, " ")}»`);
  const open = I.filter(i => !st(i.id).v).map(i => i.id);
  const L = [`M3 alternatives with the weapon (__STAMP__): ${done}/${I.length} judged`,
    `OK (${by("ok").length}): ${by("ok").join(", ") || "—"}`,
    `NO (${by("no").length}): ${by("no").join(", ") || "—"}`,
    `? (${by("q").length}): ${by("q").join(", ") || "—"}`,
    `notes: ${notes.join(" / ") || "—"}`];
  if (open.length) L.push(`unjudged (${open.length}): ${open.join(", ")}`);
  document.getElementById("result").value = L.join("\n");
}
function copy(){
  const t = document.getElementById("result"), msg = document.getElementById("copied");
  summary();
  const done = () => { msg.textContent = "copied"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? done() : (msg.textContent = "select and press Ctrl+C below"); } catch (e) { msg.textContent = "select and press Ctrl+C below"; } t.scrollIntoView({block:"center"}); };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(done, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const r = e.target.closest(".row"); if (!r) return;
  const id = r.dataset.id, s = st(id);
  const v = e.target.closest(".btns button"), k = e.target.closest(".snds button");
  if (v) { s.v = s.v === v.dataset.v ? "" : v.dataset.v; save(); paint(id); summary(); }
  else if (k) { s.snd = k.dataset.snd; save(); paint(id); play(id); }
  else if (e.target.closest("button.play") || e.target.closest("canvas.scr")) play(id);
});
document.addEventListener("input", e => {
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.getElementById("onlyOpen").addEventListener("change", () => D.items.forEach(i => paint(i.id)));
document.getElementById("copyTop").addEventListener("click", copy);
document.getElementById("copyBottom").addEventListener("click", copy);
document.getElementById("reset").addEventListener("click", () => { if (confirm("Clear all the answers and notes on this sheet?")) { stopAll(); S = {}; save(); build(); summary(); } });
build(); summary();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
