#!/usr/bin/env python3
"""Record the trailer's engine shots: one GZDoom run per shot, filmed by FFmpeg.

THE PM'S TOOL (D26): it opens a GZDoom window on the desktop, so it refuses
unless SD_ALLOW_ENGINE=1; --print and --list show what it would do with the
engine unreachable. Windows only (the CEO's PC): it films the window with
FFmpeg's gdigrab and, when the machine has a loopback capture device, the
game's sound with dshow.

Per shot (tools/trailer/shots.json, see trailer_lib.py):
  1. writes the helper PK3 (route.py's proven handler + the trailer camera)
     into work/trailer/helper/ (gitignored, never the mod);
  2. launches GZDoom with its OWN config, logs/gzdoom-trailer.ini, seeded from
     logs/gzdoom-tooling.ini the first time, so the trailer's cvars
     (screenblocks 12, no crosshair, no messages, music off) never reach the
     QA runs' screenshots; window 1280x720;
  3. finds the game window by the process id, gives it an exact 1280x720
     client area (AdjustWindowRectEx + SetWindowPos, topmost, centred on the
     primary monitor), and starts FFmpeg on that screen rectangle
     (gdigrab "desktop" with an offset: it reads the composited desktop, so
     an OpenGL or Vulkan window is not black);
  4. waits for GZDoom to quit (the shot's console sequence ends in `quit`),
     stops FFmpeg with "q", and writes work/trailer/shots/<ID>.mkv plus
     <ID>.json (the argv, the rectangle, timings, notes) and <ID>.log.

The shot's time zero is not measured here: the helper paints the screen
magenta until `netevent sdroll`, and edit.py finds the first frame without
it. So FFmpeg only has to be rolling before the slate lifts (>= 6 s after the
map has loaded; the manifest records how long the window took to appear).

Do not touch the mouse or the keyboard while it runs: the window is topmost
and the picture is the screen. Each shot takes ~15-25 s.

Usage (from the repo root; the venv's python is not needed, the standard
library is):
  SD_ALLOW_ENGINE=1 python tools/trailer/capture.py                 # every engine shot
  SD_ALLOW_ENGINE=1 python tools/trailer/capture.py --shots S01 S13 # some
  SD_ALLOW_ENGINE=1 python tools/trailer/capture.py --pk3 PATH      # a V3 PK3 (RGD-5, ops map, medals)
  python tools/trailer/capture.py --print --shots S01               # argv + FFmpeg command, no engine
  python tools/trailer/capture.py --list                            # the shots and what they need

Exit codes: 0 ok; 2 no gzdoom; 3 no IWAD; 4 build failed; 8 the engine gate
is shut (nothing launched); 9 a shot failed (no window, FFmpeg error,
timeout); 10 not Windows or no FFmpeg.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trailer_lib as tl  # noqa: E402
import smoke  # noqa: E402  (tools/ is on the path through trailer_lib)

EXIT_BLOCKED = 8
EXIT_SHOT_FAILED = 9
EXIT_PLATFORM = 10

TRAILER_CONFIG = tl.PROJECT_ROOT / "logs" / "gzdoom-trailer.ini"
FFMPEG_FALLBACKS = (Path(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"),)
# Loopback devices that carry what the speakers play, by the names Windows
# drivers give them. The CEO's PC has "What U Hear (Sound Blaster Z SE)"
# (ffmpeg -list_devices true -f dshow -i dummy, 2026-10-24).
LOOPBACK_HINTS = ("what u hear", "stereo mix", "mezcla est", "loopback", "wave out mix")

WINDOW_WAIT_S = 45.0        # GZDoom start-up until its window shows
STABLE_S = 1.0              # the window's client rect unchanged this long before we size it
MIN_SHOWN_S = 2.0           # and shown at least this long (the start-up log window comes first)
RESIZE_TRIES = 6
RESIZE_SETTLE_S = 0.6
FFMPEG_STOP_S = 15.0
TIMEOUT_MARGIN_S = 60.0
CAPTURE_CRF = "14"          # near-lossless intermediate; edit.py re-encodes
CAPTURE_PRESET = "ultrafast"


# ============================================================================
# Windows: the game window
# ============================================================================

def _win32():
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)   # per-monitor: physical pixels
    except (OSError, AttributeError):
        try:
            user32.SetProcessDPIAware()
        except AttributeError:
            pass
    user32.GetWindowLongW.restype = ctypes.c_long
    return ctypes, wintypes, user32


def windows_of(pid: int) -> list[tuple[int, str, tuple[int, int, int, int]]]:
    """Visible top-level windows of a process: (hwnd, title, client rect on screen)."""
    ctypes, wintypes, user32 = _win32()
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def each(hwnd, _lparam):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, buf, 256)
            found.append((hwnd, buf.value, client_rect(hwnd)))
        return True

    user32.EnumWindows(each, 0)
    return found


def client_rect(hwnd: int) -> tuple[int, int, int, int]:
    """(x, y, w, h) of the client area in screen pixels."""
    ctypes, wintypes, user32 = _win32()
    rc = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rc))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rc.right - rc.left, rc.bottom - rc.top


def place_window(hwnd: int, width: int, height: int) -> None:
    """Give the window a client area of exactly width x height, topmost,
    centred on the primary monitor."""
    ctypes, wintypes, user32 = _win32()
    gwl_style, gwl_exstyle = -16, -20
    style = user32.GetWindowLongW(hwnd, gwl_style) & 0xFFFFFFFF
    exstyle = user32.GetWindowLongW(hwnd, gwl_exstyle) & 0xFFFFFFFF
    rc = wintypes.RECT(0, 0, width, height)
    user32.AdjustWindowRectEx(ctypes.byref(rc), style, False, exstyle)
    outer_w, outer_h = rc.right - rc.left, rc.bottom - rc.top
    screen_w, screen_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    x = max(0, (screen_w - outer_w) // 2)
    y = max(0, (screen_h - outer_h) // 2)
    hwnd_topmost, swp_showwindow = -1, 0x0040
    user32.SetWindowPos(hwnd, hwnd_topmost, x, y, outer_w, outer_h, swp_showwindow)
    user32.SetForegroundWindow(hwnd)


def wait_for_window(proc: subprocess.Popen, size: tuple[int, int]) -> tuple[int, tuple, float]:
    """Wait for GZDoom's window, size it, and return (hwnd, client rect, seconds
    since launch). Raises RuntimeError if it never settles."""
    started = time.monotonic()
    first_seen = None
    last_rect, stable_since = None, None
    while time.monotonic() - started < WINDOW_WAIT_S:
        if proc.poll() is not None:
            raise RuntimeError(f"GZDoom exited (status {proc.returncode}) before its window settled")
        wins = windows_of(proc.pid)
        if wins:
            hwnd, _title, rect = max(wins, key=lambda w: w[2][2] * w[2][3])
            now = time.monotonic()
            first_seen = first_seen or now
            if rect != last_rect:
                last_rect, stable_since = rect, now
            elif now - stable_since >= STABLE_S and now - first_seen >= MIN_SHOWN_S:
                for _ in range(RESIZE_TRIES):
                    place_window(hwnd, *size)
                    time.sleep(RESIZE_SETTLE_S)
                    rect = client_rect(hwnd)
                    if rect[2:] == tuple(size):
                        return hwnd, rect, time.monotonic() - started
                raise RuntimeError(f"the window would not take a {size[0]}x{size[1]} client area "
                                   f"(it is {rect[2]}x{rect[3]})")
        time.sleep(0.1)
    raise RuntimeError(f"no settled GZDoom window after {WINDOW_WAIT_S:.0f} s")


def watch_window(proc: subprocess.Popen, rect: tuple, size: tuple[int, int], timeout: float) -> int:
    """While GZDoom runs, keep its window on the filmed rectangle: if the
    engine moves or resizes it (or a new window replaces the start-up one),
    put it back. FFmpeg films a fixed screen rectangle, so this is what keeps
    the picture whole. Returns how many times it had to."""
    started, fixes = time.monotonic(), 0
    while proc.poll() is None and time.monotonic() - started < timeout:
        wins = windows_of(proc.pid)
        if wins:
            hwnd, _title, now = max(wins, key=lambda w: w[2][2] * w[2][3])
            if tuple(now) != tuple(rect):
                place_window(hwnd, *size)
                fixes += 1
        time.sleep(0.2)
    return fixes


# ============================================================================
# FFmpeg
# ============================================================================

def find_ffmpeg() -> Path | None:
    found = shutil.which("ffmpeg")
    if found:
        return Path(found)
    for cand in FFMPEG_FALLBACKS:
        if cand.is_file():
            return cand
    return None


def loopback_device(ffmpeg: Path) -> str | None:
    """The first dshow audio device whose name says it carries the speakers' mix."""
    try:
        out = subprocess.run([str(ffmpeg), "-hide_banner", "-list_devices", "true", "-f", "dshow",
                              "-i", "dummy"], capture_output=True, text=True, errors="replace",
                             timeout=20).stderr
    except (OSError, subprocess.TimeoutExpired):
        return None
    for line in out.splitlines():
        if "(audio)" not in line or '"' not in line:
            continue
        name = line.split('"')[1]
        if any(h in name.lower() for h in LOOPBACK_HINTS):
            return name
    return None


def ffmpeg_command(ffmpeg: Path, rect: tuple[int, int, int, int], fps: int, out: Path,
                   audio_device: str | None) -> list[str]:
    x, y, w, h = rect
    cmd = [str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-y",
           "-thread_queue_size", "1024", "-f", "gdigrab", "-framerate", str(fps), "-draw_mouse", "0",
           "-offset_x", str(x), "-offset_y", str(y), "-video_size", f"{w}x{h}", "-i", "desktop"]
    if audio_device:
        cmd += ["-thread_queue_size", "1024", "-f", "dshow", "-audio_buffer_size", "50",
                "-i", f"audio={audio_device}"]
    cmd += ["-map", "0:v"] + (["-map", "1:a"] if audio_device else [])
    cmd += ["-c:v", "libx264", "-preset", CAPTURE_PRESET, "-crf", CAPTURE_CRF, "-pix_fmt", "yuv420p",
            "-fps_mode", "cfr", "-r", str(fps)]
    if audio_device:
        cmd += ["-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
    cmd.append(str(out))
    return cmd


def stop_ffmpeg(proc: subprocess.Popen) -> int | None:
    try:
        proc.stdin.write(b"q")
        proc.stdin.flush()
        proc.stdin.close()
    except (OSError, ValueError):
        pass
    try:
        return proc.wait(timeout=FFMPEG_STOP_S)
    except subprocess.TimeoutExpired:
        proc.terminate()
        return proc.wait(timeout=FFMPEG_STOP_S)


# ============================================================================
# One shot
# ============================================================================

def seed_config(config: Path = TRAILER_CONFIG) -> Path:
    """The trailer's own config: a copy of the tooling one the first time."""
    if not config.exists():
        config.parent.mkdir(parents=True, exist_ok=True)
        if smoke.TOOLING_CONFIG.is_file():
            shutil.copyfile(smoke.TOOLING_CONFIG, config)
        else:
            config.write_text("", encoding="utf-8")
    return config


def capture_shot(shot: dict, names: list[str], gzdoom: Path, iwad: Path, pk3s: list[Path],
                 helper: Path, ffmpeg: Path, audio_device: str | None, window: tuple[int, int],
                 fps: int, notes: list[str]) -> dict:
    tl.SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    sid = shot["id"]
    video = tl.SHOTS_DIR / f"{sid}.mkv"
    log = tl.SHOTS_DIR / f"{sid}.log"
    argv = tl.engine_argv(gzdoom, iwad, pk3s, helper, seed_config(), log, shot, names, window,
                          sound=audio_device is not None)
    manifest = {"id": sid, "when": datetime.now().isoformat(timespec="seconds"), "argv": argv,
                "fps": fps, "audio_device": audio_device, "window": list(window), "notes": notes,
                "shot": shot, "ok": False}
    timeout = tl.sequence_seconds(shot, names) + TIMEOUT_MARGIN_S
    game = subprocess.Popen(argv, cwd=str(tl.PROJECT_ROOT), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **smoke._spawn_options())
    rec = None
    try:
        hwnd, rect, shown_s = wait_for_window(game, window)
        manifest.update(rect=list(rect), window_after_s=round(shown_s, 2))
        cmd = ffmpeg_command(ffmpeg, rect, fps, video, audio_device)
        manifest["ffmpeg"] = cmd
        rec = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                               stderr=open(tl.SHOTS_DIR / f"{sid}.ffmpeg.txt", "w", encoding="utf-8"))
        manifest["window_fixes"] = watch_window(game, rect, window, timeout)
        if game.poll() is None:
            smoke._kill_group(game)
            manifest["error"] = f"GZDoom ran past {timeout:.0f} s and was killed"
        try:
            manifest["rect_at_end"] = list(client_rect(hwnd))
        except OSError:
            pass
    except RuntimeError as exc:
        manifest["error"] = str(exc)
        if game.poll() is None:
            smoke._kill_group(game)
    finally:
        if rec is not None:
            manifest["ffmpeg_status"] = stop_ffmpeg(rec)
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    manifest["roll_seen_in_log"] = "SDTRAILER roll" in text
    manifest["spawns_failed"] = [ln for ln in text.splitlines() if "SDTRAILER spawn" in ln and "ok=0" in ln]
    manifest["script_errors"] = [ln for ln in text.splitlines() if "Script error" in ln][:10]
    manifest["ok"] = ("error" not in manifest and video.is_file() and manifest["roll_seen_in_log"]
                      and not manifest["script_errors"])
    (tl.SHOTS_DIR / f"{sid}.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False),
                                              encoding="utf-8")
    return manifest


# ============================================================================
# Main
# ============================================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--shots", nargs="*", help="shot ids (default: every engine shot)")
    ap.add_argument("--pk3", action="append", type=Path,
                    help="the mod PK3 (repeatable, load order); default: build dist/sovietdoom.pk3")
    ap.add_argument("--no-build", action="store_true", help="use dist/sovietdoom.pk3 as it is")
    ap.add_argument("--gzdoom")
    ap.add_argument("--iwad")
    ap.add_argument("--fps", type=int)
    ap.add_argument("--no-audio", action="store_true", help="film the picture only (-nosound)")
    ap.add_argument("--audio-device", help="dshow device to record the game's sound from")
    ap.add_argument("--print", action="store_true", help="print the argv and FFmpeg command, run nothing")
    ap.add_argument("--list", action="store_true", help="list the shots, run nothing")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = tl.load_shots()
    names = tl.classes_used(data)
    shots = tl.shots_by_id(data)
    wanted = args.shots or [sid for sid, s in shots.items() if s.kind == "engine"]
    unknown = [s for s in wanted if s not in shots]
    if unknown:
        print(f"unknown shot(s): {', '.join(unknown)}", file=sys.stderr)
        return 2
    window = tuple(data["video"].get("capture_window", (1280, 720)))
    fps = args.fps or int(data["video"].get("fps", 60))

    if args.list:
        for sid in wanted:
            s = shots[sid].data
            need = f" requires {', '.join(s['requires'])}" if s.get("requires") else ""
            print(f"{sid:6s} {s.get('kind', 'engine'):6s} {s.get('map', ''):6s} "
                  f"{tl.roll_tics(s) / tl.TICS_PER_SECOND if s.get('actions') else 0:5.2f} s{need}  {s.get('note', '')}")
        return 0

    pk3s = args.pk3 or [tl.PROJECT_ROOT / "dist" / f"{smoke.MOD_NAME}.pk3"]
    if args.print:
        ffmpeg = find_ffmpeg() or Path("ffmpeg")
        for sid in wanted:
            shot = shots[sid].data
            if shot.get("kind", "engine") != "engine":
                continue
            argv_ = tl.engine_argv(Path("gzdoom.exe"), Path("freedoom2.wad"), pk3s, tl.HELPER_PK3,
                                   TRAILER_CONFIG, tl.SHOTS_DIR / f"{sid}.log", shot, names, window,
                                   sound=not args.no_audio)
            print(f"--- {sid} ({tl.sequence_seconds(shot, names):.1f} s of console sequence)")
            print(subprocess.list2cmdline(argv_))
            print(subprocess.list2cmdline(ffmpeg_command(ffmpeg, (320, 180, *window), fps,
                                                         tl.SHOTS_DIR / f"{sid}.mkv",
                                                         None if args.no_audio else (args.audio_device or "<loopback>"))))
        return 0

    if not smoke.engine_allowed():
        print(smoke.ENGINE_GATE_MSG, file=sys.stderr)
        return EXIT_BLOCKED
    if os.name != "nt":
        print("capture.py films a Windows window (gdigrab); this is not Windows", file=sys.stderr)
        return EXIT_PLATFORM
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("ffmpeg not found on the PATH (the CEO's PC has it under C:\\ProgramData\\chocolatey\\bin)",
              file=sys.stderr)
        return EXIT_PLATFORM
    try:
        gzdoom = smoke.find_gzdoom(args.gzdoom)
        iwad = smoke.find_iwad(args.iwad)
    except smoke.SmokeError as exc:
        print(exc, file=sys.stderr)
        return exc.code
    if not args.pk3 and not args.no_build:
        try:
            smoke.run_build()
        except smoke.SmokeError as exc:
            print(exc, file=sys.stderr)
            return exc.code
    audio = None if args.no_audio else (args.audio_device or loopback_device(ffmpeg))
    if not args.no_audio and audio is None:
        print("note: no loopback audio device found; filming the picture only", file=sys.stderr)
    available = tl.pk3_classes(pk3s)
    helper = tl.write_helper_pk3(names)
    failed = 0
    for sid in wanted:
        shot, notes = tl.resolve(shots[sid].data, available)
        for n in notes:
            print(f"note: {n}")
        if not shot or shot.get("kind", "engine") != "engine":
            continue
        print(f"{sid}: {shot['map']} skill {shot.get('skill', 3)} ... ", end="", flush=True)
        m = capture_shot(shot, names, gzdoom, iwad, pk3s, helper, ffmpeg, audio, window, fps, notes)
        status = "ok" if m["ok"] else "FAILED: " + (m.get("error") or
                                                     ("no roll in the log" if not m["roll_seen_in_log"]
                                                      else "; ".join(m["script_errors"]) or "no video"))
        print(status + (f" ({len(m['spawns_failed'])} spawn(s) blocked)" if m["spawns_failed"] else ""))
        failed += 0 if m["ok"] else 1
    print(f"shots in {tl.SHOTS_DIR}; next: python tools/trailer/edit.py")
    return EXIT_SHOT_FAILED if failed else 0


if __name__ == "__main__":
    sys.exit(main())
