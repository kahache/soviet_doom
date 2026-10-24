#!/usr/bin/env python3
"""Cut the 60 s trailer from capture.py's shots, to the music's bars.

Runs no engine (D26): it reads work/trailer/shots/*.mkv (capture.py, the
PM's), renders the music from our own MIDI with GZDoom's synthesiser loaded
as a library (zmusic.dll + gzdoom.sf2, the way the listening sheets were
made: tools/audio/gen_enemy_alts.zmusic_render; no window, no new
soundfont), draws every text in the game's bitmap fonts (assets/fonts/,
never a system font), and writes, for each locale:

  work/trailer/sovietdoom-trailer-en.mp4   (and -ru, -ca)
      1920x1080 (or --height 720), 60 fps, H.264 High, AAC 192 kb/s, faststart

How the cut is timed: the timeline in tools/trailer/shots.json counts bars
(the main piece, D_SDBS9A, is 140 BPM: one bar = 1.714 s = 60 tics), so every
cut falls on a downbeat; each engine shot starts at its "roll" (the first
frame without the helper's magenta slate, found here and cached in
work/trailer/shots/<ID>.sync.json) plus the segment's "from" seconds.
A shot that was not captured falls back to its `fallback` still (the
operations map and the medal, from the v3 branch's PNGs, when the PK3 had
no V3 intermission), or, with --allow-missing, to a grey placeholder card
naming it, so the cut can be previewed before every shot exists.

Usage (the venv: Pillow and numpy):
  .venv/Scripts/python.exe tools/trailer/edit.py                     # en, ru, ca
  .venv/Scripts/python.exe tools/trailer/edit.py --locales en --allow-missing   # a preview
  .venv/Scripts/python.exe tools/trailer/edit.py --contact S15       # frames of one shot, to pick "from"
  .venv/Scripts/python.exe tools/trailer/edit.py --cards-only        # the card PNGs, to proof the texts
  .venv/Scripts/python.exe tools/trailer/edit.py --music-only        # work/trailer/audio/music.wav
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trailer_lib as tl  # noqa: E402

AUDIO_TOOLS = tl.TOOLS_DIR / "audio"
BUILD_DIR = tl.WORK_DIR / "build"
CARDS_DIR = tl.WORK_DIR / "cards"
AUDIO_DIR = tl.WORK_DIR / "audio"
CONTACT_DIR = tl.WORK_DIR / "contact"

RATE = 44100
SLATE_TOL = 80              # per channel, on a 32x18 thumbnail
SLATE_FRACTION = 0.9        # of the thumbnail's pixels
THUMB = (32, 18)
FLASH_S = 0.12              # the white flash on a "flash" cut
FADE_IN_S = 0.6             # the trailer's first frames, from black
FADE_OUT_S = 1.2            # the last ones, to black
CARD_FADE_S = 0.12          # short: a lower third must read from its first second (PM, 2026-10-25)
EDGE_FADE_S = 0.008         # on every sfx slice, against clicks
PEAK_DBFS = -1.0
SEG_CRF, FINAL_CRF = "14", "18"
BAND_ALPHA = 150            # the lower third's dark band
MARGIN_X, MARGIN_BOTTOM = 96, 96
STILL_PUSH = 0.06           # a still's slow push-in over its segment


# ============================================================================
# Small helpers
# ============================================================================

def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg") or r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"
    if not Path(found).is_file() and not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found")
    return found


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if proc.returncode != 0:
        tail = "\n".join(proc.stderr.strip().splitlines()[-15:])
        raise SystemExit(f"ffmpeg failed ({proc.returncode}):\n{subprocess.list2cmdline(cmd)}\n{tail}")


def frames(t: float, fps: int) -> int:
    return int(round(t * fps))


def load_image(path: str, git_ref: str | None = None) -> Image.Image:
    """An image from the tree, or from a branch (V3's PNGs live on v3 until it
    is merged): `git show <ref>:<path>` reads the object, nothing is checked out."""
    p = tl.PROJECT_ROOT / path
    if p.is_file():
        return Image.open(p).convert("RGBA")
    if git_ref:
        proc = subprocess.run(["git", "-C", str(tl.PROJECT_ROOT), "show", f"{git_ref}:{path}"],
                              capture_output=True)
        if proc.returncode == 0:
            import io
            return Image.open(io.BytesIO(proc.stdout)).convert("RGBA")
    raise FileNotFoundError(f"{path} is neither in the tree nor on {git_ref or 'any branch'}")


def read_text(path: str, git_ref: str | None = None) -> str:
    p = tl.PROJECT_ROOT / path
    if p.is_file():
        return p.read_text(encoding="utf-8")
    if git_ref:
        proc = subprocess.run(["git", "-C", str(tl.PROJECT_ROOT), "show", f"{git_ref}:{path}"],
                              capture_output=True)
        if proc.returncode == 0:
            return proc.stdout.decode("utf-8")
    raise FileNotFoundError(f"{path} is neither in the tree nor on {git_ref or 'any branch'}")


# ============================================================================
# Text in the game's bitmap fonts
# ============================================================================

_GLYPHS: dict[tuple[str, str], Image.Image] = {}


def glyph(font: str, ch: str) -> Image.Image:
    key = (font, ch)
    if key not in _GLYPHS:
        path = tl.FONTS_DIR / font / f"{ord(ch):04X}.png"
        if not path.is_file():
            raise tl.TrailerError(f"font {font} has no glyph for {ch!r} (U+{ord(ch):04X})")
        _GLYPHS[key] = Image.open(path).convert("RGBA")
    return _GLYPHS[key]


def render_line(text: str, font: str, scale: int) -> Image.Image:
    """One line at native size, then nearest-neighbour x scale (the fonts are
    upper case only; the engine folds case the same way)."""
    chars = [glyph(font, ch) for ch in text.upper()]
    w = sum(g.width for g in chars) or 1
    h = max((g.height for g in chars), default=1)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for g in chars:
        img.alpha_composite(g, (x, 0))
        x += g.width
    return img.resize((w * scale, h * scale), Image.NEAREST)


def fill_vars(text: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        text = text.replace("{" + k + "}", v)
    return text


def render_card(card: dict, styles: dict, locale: str, size: tuple[int, int],
                values: dict[str, str], strings: dict) -> Image.Image:
    W, H = size
    k = H / 1080.0
    style = styles[card["style"]]
    scale = max(1, round(style["scale"] * k))
    gap = round(style.get("line_gap", 12) * k)
    lines = [render_line(fill_vars(t, values), style["font"], scale)
             for t in tl.card_lines(card, locale, strings)]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    anchor = style.get("anchor", "center")
    block_h = sum(l.height for l in lines) + gap * (len(lines) - 1)
    if anchor == "center":
        y = (H - block_h) // 2
        for l in lines:
            img.alpha_composite(l, ((W - l.width) // 2, y))
            y += l.height + gap
    elif anchor == "bottom":
        y = H - round(MARGIN_BOTTOM * k) - block_h
        if style.get("band"):
            pad = round(18 * k)
            width = max(l.width for l in lines)
            band = Image.new("RGBA", (width + 4 * pad, block_h + 2 * pad), (0, 0, 0, int(style.get("band_alpha", BAND_ALPHA))))
            img.alpha_composite(band, ((W - band.width) // 2, y - pad))
        for l in lines:
            img.alpha_composite(l, ((W - l.width) // 2, y))
            y += l.height + gap
    elif anchor == "lower-left":
        kicker = None
        if card.get("kicker"):
            ks = styles["kicker"]
            kt = tl.card_lines({locale: [card["kicker"]]}, locale, strings)[0]
            kicker = render_line(kt, ks["font"], max(1, round(ks["scale"] * k)))
        x0, y_bottom = round(MARGIN_X * k), H - round(MARGIN_BOTTOM * k)
        total = block_h + ((kicker.height + gap) if kicker else 0)
        width = max([l.width for l in lines] + ([kicker.width] if kicker else []))
        if style.get("band"):
            pad = round(18 * k)
            band = Image.new("RGBA", (width + 2 * pad, total + 2 * pad), (0, 0, 0, BAND_ALPHA))
            img.alpha_composite(band, (x0 - pad, y_bottom - total - pad))
        y = y_bottom - total
        if kicker:
            img.alpha_composite(kicker, (x0, y))
            y += kicker.height + gap
        for l in lines:
            img.alpha_composite(l, (x0, y))
            y += l.height + gap
    elif anchor == "end":
        logo = None
        if card.get("logo"):
            lg = load_image(card["logo"]["image"])
            ls = max(1, round(card["logo"].get("scale", 4) * k))
            logo = lg.resize((lg.width * ls, lg.height * ls), Image.NEAREST)
        total = (logo.height + 2 * gap if logo else 0) + block_h
        y = (H - total) // 2
        if logo:
            img.alpha_composite(logo, ((W - logo.width) // 2, y))
            y += logo.height + 2 * gap
        for l in lines:
            img.alpha_composite(l, ((W - l.width) // 2, y))
            y += l.height + gap
        if card.get("credit"):
            cs = styles["credit"]
            line = render_line(card["credit"][locale], cs["font"], max(1, round(cs["scale"] * k)))
            img.alpha_composite(line, ((W - line.width) // 2, H - round(MARGIN_BOTTOM * k / 2) - line.height))
    else:
        raise tl.TrailerError(f"unknown anchor {anchor!r}")
    return img


def card_values(data: dict, version: str) -> dict[str, str]:
    """{version} from the command line or shots.json; {weapons}: nine when the
    RGD-5 shot was filmed with the RGD-5 (a V3 PK3), else eight (D116)."""
    weapons = "8"
    manifest = tl.SHOTS_DIR / "S11.json"
    if manifest.is_file():
        try:
            if json.loads(manifest.read_text(encoding="utf-8"))["shot"].get("weapon") == "SD_Rgd5":
                weapons = "9"
        except (KeyError, json.JSONDecodeError):
            pass
    return {"version": version.upper(), "weapons": weapons}


def write_cards(data: dict, locale: str, size, values) -> dict[str, Path]:
    cards = tl.load_json(tl.CARDS_JSON)
    strings = tl.language_strings()
    out = {}
    d = CARDS_DIR / locale
    d.mkdir(parents=True, exist_ok=True)
    used = {cid for cid, _a, _b in tl.card_windows(data)}
    for cid in sorted(used):
        p = d / f"{cid}.png"
        render_card(cards["cards"][cid], cards["styles"], locale, size, values, strings).save(p)
        out[cid] = p
    return out


# ============================================================================
# Stills (title, and the V3 fallbacks)
# ============================================================================

def still_image(shot: dict, size: tuple[int, int]) -> Image.Image:
    """The still at 2x the frame (so the push-in never shows its pixels move)."""
    W, H = size[0] * 2, size[1] * 2
    ref = shot.get("git_ref")
    base = load_image(shot["image"], ref)
    if shot.get("opsmap"):
        text = read_text("src/lumps/SDOPSCR", ref)
        for line in text.splitlines():
            p = line.split()
            if len(p) == 6 and p[0] == "IfLeaving" and p[1] == shot["opsmap"] and p[2] == "Pic":
                pic = load_image(f"assets/graphics/opsmap/{p[5]}.png", ref)
                base.alpha_composite(pic, (int(p[3]), int(p[4])))
    if shot.get("dim"):
        shade = Image.new("RGBA", base.size, (0, 0, 0, int(255 * float(shot["dim"]))))
        base.alpha_composite(shade)
    for layer in shot.get("layers", ()):
        pic = load_image(layer["image"], layer.get("git_ref", ref))
        s = int(layer.get("scale", 1))
        pic = pic.resize((pic.width * s, pic.height * s), Image.NEAREST)
        if layer.get("pos", "center") == "center":
            base.alpha_composite(pic, ((base.width - pic.width) // 2, (base.height - pic.height) // 2))
    if shot.get("aspect") == "doom":       # 320x200 shown at 4:3, as the engine does
        target_h = H
        target_w = round(target_h * 4 / 3)
    else:
        target_w, target_h = W, round(W * base.height / base.width)
    big = base.resize((base.width * 8, base.height * 8), Image.NEAREST)
    pic = big.resize((target_w, target_h), Image.LANCZOS)
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    frame.alpha_composite(pic, ((W - target_w) // 2, (H - target_h) // 2))
    return frame


def placeholder_image(label: str, size: tuple[int, int]) -> Image.Image:
    W, H = size[0] * 2, size[1] * 2
    img = Image.new("RGBA", (W, H), (48, 48, 56, 255))
    line = render_line(f"MISSING {label}", "bigfont", 8)
    img.alpha_composite(line, ((W - line.width) // 2, (H - line.height) // 2))
    return img


# ============================================================================
# Engine shots: the roll
# ============================================================================

def thumbs(video: Path, fps: int, start: float = 0.0, seconds: float | None = None) -> np.ndarray:
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", str(video)]
    if seconds:
        cmd += ["-t", f"{seconds:.3f}"]
    cmd += ["-an", "-vf", f"fps={fps},scale={THUMB[0]}:{THUMB[1]}:flags=area,format=rgb24",
            "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (THUMB[0] * THUMB[1] * 3)
    return np.frombuffer(raw[: n * THUMB[0] * THUMB[1] * 3], np.uint8).reshape(n, THUMB[1], THUMB[0], 3)


def slate_mask(frames_: np.ndarray) -> np.ndarray:
    target = np.array(tl.SLATE_RGB, np.int16)
    close = (np.abs(frames_.astype(np.int16) - target) <= SLATE_TOL).all(axis=-1)
    return close.mean(axis=(1, 2)) >= SLATE_FRACTION


def roll_index(mask: np.ndarray) -> int | None:
    """The first frame after the LAST run of slate frames (None: no slate, or
    the recording ends on it)."""
    idx = np.flatnonzero(mask)
    if idx.size == 0 or idx[-1] + 1 >= mask.size:
        return None
    return int(idx[-1]) + 1


def find_roll(sid: str, fps: int) -> float:
    sync = tl.SHOTS_DIR / f"{sid}.sync.json"
    video = tl.SHOTS_DIR / f"{sid}.mkv"
    if sync.is_file():
        s = json.loads(sync.read_text(encoding="utf-8"))
        if "roll_s_manual" in s:
            return float(s["roll_s_manual"])
        if s.get("video_mtime") == video.stat().st_mtime and "roll_s" in s:
            return float(s["roll_s"])
    i = roll_index(slate_mask(thumbs(video, fps)))
    if i is None:
        raise SystemExit(f"{sid}: no magenta slate found in {video}: re-capture it, or write "
                         f'{{"roll_s_manual": <seconds>}} into {sync}')
    roll = i / fps
    sync.write_text(json.dumps({"roll_s": roll, "frame": i, "fps": fps,
                                "video_mtime": video.stat().st_mtime}, indent=1), encoding="utf-8")
    return roll


def contact_sheet(sid: str, fps: int, step: float = 0.25, cols: int = 6) -> Path:
    """Frames of one shot every `step` s after its roll, labelled, to choose `from`."""
    video = tl.SHOTS_DIR / f"{sid}.mkv"
    roll = find_roll(sid, fps)
    data = tl.load_shots()
    shot = tl.shots_by_id(data)[sid].data
    seconds = tl.roll_tics(shot) / tl.TICS_PER_SECOND
    CONTACT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONTACT_DIR / f"{sid}_%04d.png"
    run([ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{roll:.3f}", "-i", str(video),
         "-t", f"{seconds:.3f}", "-an", "-vf", f"fps={1 / step},scale=320:-1", str(tmp)])
    tiles = sorted(CONTACT_DIR.glob(f"{sid}_*.png"))
    if not tiles:
        raise SystemExit(f"{sid}: no frames after the roll")
    w, h = Image.open(tiles[0]).size
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + 16)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for i, t in enumerate(tiles):
        x, y = (i % cols) * w, (i // cols) * (h + 16)
        sheet.paste(Image.open(t), (x, y + 16))
        draw.text((x + 4, y + 2), f"from {i * step:.2f} s", fill=(255, 255, 255))   # a QA aid, not trailer text
        t.unlink()
    out = CONTACT_DIR / f"{sid}.png"
    sheet.save(out)
    return out


# ============================================================================
# The picture
# ============================================================================

def segment_plan(data: dict, available_shots: dict, allow_missing: bool) -> list[dict]:
    """What each timeline segment shows: an engine clip, a still, or black."""
    shots = tl.shots_by_id(data)
    plan = []
    missing = []
    for i, (start, end, seg) in enumerate(tl.timeline(data)):
        if seg.get("end"):
            end += float(data["video"].get("tail_s", 0.0))
        item = {"i": i, "start": start, "end": end, "seg": seg}
        if seg.get("black"):
            item["kind"] = "black"
        else:
            shot = shots[seg["shot"]].data
            if shot.get("kind", "engine") == "still":
                item.update(kind="still", shot=shot)
            elif seg["shot"] in available_shots:
                item.update(kind="engine", shot=shot, video=available_shots[seg["shot"]])
            elif shot.get("fallback", {}).get("kind") == "still":
                item.update(kind="still", shot=dict(shot, **shot["fallback"]))
            elif allow_missing:
                item.update(kind="placeholder", label=seg["shot"])
            else:
                missing.append(seg["shot"])
        plan.append(item)
    if missing:
        raise SystemExit("not captured yet: " + ", ".join(missing) +
                         " (run capture.py, or pass --allow-missing for a preview)")
    return plan


def render_segment(item: dict, size, fps: int, out: Path, first: bool, last: bool) -> None:
    W, H = size
    n = frames(item["end"], fps) - frames(item["start"], fps)
    dur = n / fps
    vf = []
    trans = item["seg"].get("transition", "cut")
    if first or trans == "fade":
        vf.append(f"fade=t=in:st=0:d={FADE_IN_S}")
    elif trans == "flash":
        vf.append(f"fade=t=in:st=0:d={FLASH_S}:color=white")
    if last:
        vf.append(f"fade=t=out:st={max(0.0, dur - FADE_OUT_S):.3f}:d={FADE_OUT_S}")
    ff = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y"]
    kind = item["kind"]
    if kind == "black":
        ff += ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={fps}"]
        chain = ["format=yuv420p"]
    elif kind == "engine":
        start = item["roll"] + float(item["seg"].get("from", 0.0))
        ff += ["-ss", f"{start:.4f}", "-i", str(item["video"])]
        chain = [f"fps={fps}", f"scale={W}:{H}:flags=lanczos:force_original_aspect_ratio=increase",
                 f"crop={W}:{H}", "setsar=1", "format=yuv420p"]
    else:   # still or placeholder: a 2x picture, pushed in slowly
        img = still_image(item["shot"], size) if kind == "still" else placeholder_image(item["label"], size)
        png = BUILD_DIR / f"still_{item['i']:02d}.png"
        img.convert("RGB").save(png)
        motion = item.get("shot", {}).get("motion", "none") if kind == "still" else "none"
        z0, z1 = {"push": (1.0, 1.0 + STILL_PUSH), "pull": (1.0 + STILL_PUSH, 1.0)}.get(motion, (1.0, 1.0))
        ff += ["-loop", "1", "-framerate", str(fps), "-i", str(png)]
        if z0 == z1:
            chain = [f"scale={W}:{H}:flags=lanczos", "setsar=1", "format=yuv420p"]
        else:
            chain = [f"zoompan=z='{z0}+({z1}-{z0})*on/{max(n - 1, 1)}':x='iw/2-(iw/zoom/2)':"
                     f"y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps}", "setsar=1", "format=yuv420p"]
    ff += ["-an", "-vf", ",".join(chain + vf), "-frames:v", str(n), "-r", str(fps),
           "-c:v", "libx264", "-preset", "medium", "-crf", SEG_CRF, "-pix_fmt", "yuv420p", str(out)]
    run(ff)


def render_base(plan: list[dict], size, fps: int) -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    listing = BUILD_DIR / "segments.txt"
    lines = []
    for item in plan:
        seg = BUILD_DIR / f"seg_{item['i']:02d}.mp4"
        render_segment(item, size, fps, seg, item is plan[0], item is plan[-1])
        lines.append(f"file '{seg.as_posix()}'")
        print(f"  segment {item['i']:2d} {item['kind']:11s} {item['start']:6.2f}-{item['end']:6.2f} s "
              f"{item['seg'].get('shot', 'black')}")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    base = BUILD_DIR / "base.mp4"
    run([ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
         "-i", str(listing), "-c", "copy", str(base)])
    return base


# ============================================================================
# The sound
# ============================================================================

def zmusic(path: Path, seconds: float) -> np.ndarray:
    sys.path.insert(0, str(AUDIO_TOOLS))
    import gen_enemy_alts as ea  # the listening sheets' renderer: zmusic.dll + gzdoom.sf2
    x, rate = ea.zmusic_render(path.read_bytes(), seconds)
    if rate != RATE:
        raise SystemExit(f"zmusic rendered at {rate} Hz, expected {RATE}")
    return x


def fade(x: np.ndarray, fade_in: float, fade_out: float) -> np.ndarray:
    x = x.copy()
    a, b = int(fade_in * RATE), int(fade_out * RATE)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None]
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None]
    return x


def music_track(data: dict, total: float) -> np.ndarray:
    m = data["music"]
    out = np.zeros((int(total * RATE) + 1, 2))
    t0 = 0.0
    if "intro" in m:
        intro_s = tl.intro_seconds(data)
        x = zmusic(tl.PROJECT_ROOT / m["intro"]["file"], intro_s + 0.1)[: int(intro_s * RATE)]
        x = fade(x, 0.0, float(m["intro"].get("fade_out_s", 0.25)))
        out[: len(x)] += x
        t0 = intro_s
    main = m["main"]
    skip = float(main.get("offset_bars", 0)) * tl.bar_seconds(main)
    x = zmusic(tl.PROJECT_ROOT / main["file"], skip + total - t0 + 0.1)[int(skip * RATE):]
    i0 = int(t0 * RATE)
    x = x[: len(out) - i0]
    out[i0: i0 + len(x)] += x
    tail = float(data["video"].get("tail_s", 0.0)) + FADE_OUT_S
    return fade(out, 0.0, min(tail, total))


def shot_audio(video: Path, start: float, seconds: float) -> np.ndarray | None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-ss", f"{max(start, 0):.4f}", "-i", str(video),
           "-t", f"{seconds:.4f}", "-vn", "-ac", "2", "-ar", str(RATE), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    if not raw:
        return None
    return np.frombuffer(raw, "<f4").reshape(-1, 2).astype(np.float64)


def sfx_track(plan: list[dict], total: float, offset_s: float) -> np.ndarray:
    out = np.zeros((int(total * RATE) + 1, 2))
    for item in plan:
        if item["kind"] != "engine":
            continue
        dur = item["end"] - item["start"]
        x = shot_audio(item["video"], item["roll"] + float(item["seg"].get("from", 0.0)) - offset_s, dur)
        if x is None:
            continue
        x = fade(x[: int(dur * RATE)], EDGE_FADE_S, EDGE_FADE_S)
        i0 = int(item["start"] * RATE)
        n = min(len(x), len(out) - i0)
        out[i0: i0 + n] += x[:n]
    return out


def db(v: float) -> float:
    return 10 ** (v / 20)


def write_wav(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(np.clip(np.round(x * 32767), -32767, 32767).astype("<i2").tobytes())


def mix(data: dict, plan: list[dict] | None, total: float, sfx: bool, offset_s: float) -> Path:
    v = data["video"]
    x = music_track(data, total) * db(float(v.get("music_gain_db", 0.0)))
    if sfx and plan:
        x = x + sfx_track(plan, total, offset_s) * db(float(v.get("sfx_gain_db", -9.0)))
    peak = float(np.abs(x).max()) or 1.0
    x = x * (db(PEAK_DBFS) / peak)
    out = AUDIO_DIR / ("mix.wav" if plan else "music.wav")
    write_wav(out, x)
    return out


# ============================================================================
# One locale: cards over the base, the mix under it
# ============================================================================

def export(data: dict, base: Path, audio: Path, locale: str, size, fps: int, values, out: Path) -> None:
    cards = write_cards(data, locale, size, values)
    total = tl.total_seconds(data)
    ff = [ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y", "-i", str(base), "-i", str(audio)]
    graph, prev = [], "[0:v]"
    for n, (cid, a, b) in enumerate(tl.card_windows(data)):
        # Each card is read only for its own window and shifted into place:
        # looping fifteen full-frame PNGs over the whole minute is what made
        # the first preview take eight minutes.
        span = b - a
        ff += ["-loop", "1", "-framerate", str(fps), "-t", f"{span:.3f}", "-i", str(cards[cid])]
        k = n + 2
        d = min(CARD_FADE_S, span / 4)
        graph.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d={d:.3f}:alpha=1,"
                     f"fade=t=out:st={span - d:.3f}:d={d:.3f}:alpha=1,setpts=PTS-STARTPTS+{a:.3f}/TB[c{n}]")
        graph.append(f"{prev}[c{n}]overlay=0:0:eof_action=pass:repeatlast=0[v{n}]")
        prev = f"[v{n}]"
    ff += ["-filter_complex", ";".join(graph) if graph else "[0:v]null[vout]",
           "-map", prev if graph else "[vout]", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", FINAL_CRF, "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-r", str(fps), "-c:a", "aac", "-b:a", "192k",
           "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)]
    run(ff)


# ============================================================================
# Main
# ============================================================================

def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--locales", default=",".join(tl.LOCALES))
    ap.add_argument("--version", help="the release named on the end card (default: shots.json video.version)")
    ap.add_argument("--height", type=int, choices=(720, 1080))
    ap.add_argument("--fps", type=int)
    ap.add_argument("--allow-missing", action="store_true", help="grey placeholders for uncaptured shots")
    ap.add_argument("--no-sfx", action="store_true", help="music only, no game sound under it")
    ap.add_argument("--audio-offset-ms", type=float, default=0.0,
                    help="delay the recorded game sound by this much (A/V drift of the capture)")
    ap.add_argument("--contact", metavar="SHOT", help="write a contact sheet of one shot and stop")
    ap.add_argument("--cards-only", action="store_true", help="write the card PNGs and stop")
    ap.add_argument("--music-only", action="store_true", help="write work/trailer/audio/music.wav and stop")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    data = tl.load_shots()
    v = data["video"]
    fps = args.fps or int(v.get("fps", 60))
    H = args.height or int(v.get("height", 1080))
    size = (round(H * 16 / 9), H)
    version = args.version or str(v.get("version", "v1.3"))
    locales = [l.strip() for l in args.locales.split(",") if l.strip()]
    bad = [l for l in locales if l not in tl.LOCALES]
    if bad:
        raise SystemExit(f"unknown locale(s) {bad}; known: {tl.LOCALES}")
    total = tl.total_seconds(data)
    if args.contact:
        print(contact_sheet(args.contact, fps))
        return 0
    values = card_values(data, version)
    if args.cards_only:
        for loc in locales:
            for cid, p in write_cards(data, loc, size, values).items():
                print(p)
        return 0
    if args.music_only:
        print(mix(data, None, total, False, 0.0))
        return 0

    available = {}
    for sid, s in tl.shots_by_id(data).items():
        video = tl.SHOTS_DIR / f"{sid}.mkv"
        manifest = tl.SHOTS_DIR / f"{sid}.json"
        if s.kind == "engine" and video.is_file():
            ok = True
            if manifest.is_file():
                ok = json.loads(manifest.read_text(encoding="utf-8")).get("ok", True)
            if ok:
                available[sid] = video
            else:
                print(f"note: {sid}'s capture is marked failed in {manifest.name}; not used")
    plan = segment_plan(data, available, args.allow_missing)
    for item in plan:
        if item["kind"] == "engine":
            item["roll"] = find_roll(item["seg"]["shot"], fps)
    print(f"cut: {len(plan)} segments, {total:.2f} s, {size[0]}x{size[1]} at {fps} fps")
    base = render_base(plan, size, fps)
    audio = mix(data, plan, total, not args.no_sfx, args.audio_offset_ms / 1000.0)
    for loc in locales:
        out = tl.WORK_DIR / f"sovietdoom-trailer-{loc}.mp4"
        export(data, base, audio, loc, size, fps, values, out)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
