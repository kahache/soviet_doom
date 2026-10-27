#!/usr/bin/env python3
"""Record the trailer's engine shots: one GZDoom run per shot, filmed by FFmpeg.

THE PM'S TOOL (D26): it opens a GZDoom window on the desktop, so it refuses
unless SD_ALLOW_ENGINE=1; --print and --list show what it would do with the
engine unreachable. Windows only (the CEO's PC): it films the window with
FFmpeg (gfxcapture, the window by its HWND; else ddagrab, the GPU's copy of
its monitor; else gdigrab: CAPTURE_METHODS) and, when the machine has a
loopback capture device, the game's sound with dshow; it encodes on the GPU
when it can (ENCODERS) and measures every shot's smoothness afterwards.

Per shot (tools/trailer/shots.json, see trailer_lib.py):
  1. writes the helper PK3 (route.py's proven handler + the trailer camera)
     into work/trailer/helper/ (gitignored, never the mod);
  2. launches GZDoom with its OWN config, logs/gzdoom-trailer.ini, seeded from
     logs/gzdoom-tooling.ini the first time, so the trailer's cvars
     (screenblocks 12, no crosshair, no messages, music off) never reach the
     QA runs' screenshots; window 1280x720;
  3. finds the game window by the process id. GZDoom's win_w/win_h are the
     OUTER size (the PM's S01 run, 2026-10-24: +win_w 1280 +win_h 720 gave a
     1264x681 client area), so the tool asks for 1280x720 plus this
     desktop's frame (AdjustWindowRectEx: 1296x759 at 100 %); if the client
     area still differs it tries SetWindowPos, and failing that films the
     real client area (edit.py scales any size to 1080p). It starts FFmpeg
     on that window (gfxcapture) or its screen rectangle (ddagrab, gdigrab),
     falling back to the next method when one does not roll within
     PROBE_S, and keeps the window in place while GZDoom runs;
  4. waits for GZDoom to quit (the shot's console sequence ends in `quit`),
     stops FFmpeg with "q", and writes work/trailer/shots/<ID>.mkv plus
     <ID>.json (the argv, the rectangle, the method, timings, notes, the
     measure), <ID>.progress.txt and <ID>.log;
  5. measures the recording: new frames a second the recorder delivered
     (FFmpeg's repeated-frame count) and new frames a second where the
     picture moves (motion_report). Under MIN_EFFECTIVE_FPS the shot FAILS:
     the first cut's gdigrab shots had 14-26 (`--measure`). A silent sound
     track is noted.

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
  SD_ALLOW_ENGINE=1 python tools/trailer/capture.py --capture ddagrab  # one method only
  python tools/trailer/capture.py --print --shots S01               # argv + FFmpeg commands, no engine
  python tools/trailer/capture.py --measure                         # smoothness of the shots on disk, no engine
  python tools/trailer/capture.py --list                            # the shots and what they need

Exit codes: 0 ok; 2 no gzdoom; 3 no IWAD; 4 build failed; 8 the engine gate
is shut (nothing launched); 9 a shot failed (no window, FFmpeg error,
timeout, choppy: under MIN_EFFECTIVE_FPS); 10 not Windows or no FFmpeg.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import statistics
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
RESIZE_TRIES = 3
RESIZE_SETTLE_S = 0.6
MIN_CLIENT = (640, 360)     # below this a shot is not worth cutting
MAX_WINDOW_FIXES = 20
FFMPEG_STOP_S = 15.0
TIMEOUT_MARGIN_S = 60.0
CAPTURE_CRF = "14"          # near-lossless intermediate; edit.py re-encodes
CAPTURE_PRESET = "ultrafast"

# How the window is filmed, best first; `auto` tries them in this order and
# keeps the first that is rolling with frames after PROBE_S. gdigrab (GDI
# BitBlt of the composited desktop, on the CPU) gave the first cut only ~13
# distinct frames a second (the PM, S05, 2026-10-27); Windows.Graphics.Capture
# (gfxcapture, the window by its HWND: neither its place nor what covers it
# matters) and the Desktop Duplication API (ddagrab, the GPU's copy of the
# monitor) keep up at 60.
CAPTURE_METHODS = ("gfxcapture", "ddagrab", "gdigrab")
# The encoders, best first; the first that opens on this machine is used.
# h264_nvenc needs NVENC API 13.1, i.e. an NVIDIA driver >= 570: the CEO's
# RTX 3050 has 560.94 (API 12.2), so FFmpeg 8.1.2 cannot open it today
# (measured 2026-10-27). h264_mf with hw_encoding is the same NVENC silicon
# through the driver's own Media Foundation encoder: it works here, at no CPU
# cost; 40 Mb/s measured 71 dB PSNR on testsrc2 720p60 (libx264 CRF 14: 58).
ENCODERS = ("h264_nvenc", "h264_mf", "libx264")
MF_BITRATE = "40M"
NVENC_CQ = "16"
GOP_FRAMES = "60"           # a keyframe a second: edit.py seeks into every shot
PROBE_S = 2.5               # a recorder still running with frames after this is kept
STATS_PERIOD_S = "0.5"
ENCODER_PROBE_S = 30.0

# The smoothness measure after each shot (and `--measure`). Per-frame change
# = the mean absolute luma difference with the previous frame at 320x180
# (0..255). Measured 2026-10-27 on a gfxcapture of testsrc2: a repeated frame
# reads 0.0001-0.003 after the encoder, a real change >= 1, so DIFF_EPS sits
# well between. A 1 s window whose changes add up to MOTION_TOTAL is "moving"
# (a held, empty frame is not); a change >= CUT_DIFF (the slate lifting, a
# flash) is a cut and is left out of the sum.
MEASURE_SIZE = (320, 180)
DIFF_EPS = 0.02
MOTION_TOTAL = 6.0
CUT_DIFF = 40.0
MEASURE_WINDOW_S = 1.0
MIN_EFFECTIVE_FPS = 50.0    # the CEO's "slow and in jerks" (S05): ~13
# A window can move at fewer than 50 new frames a second with a perfect
# recorder: the game's sprites change on its 35 Hz tics, only movement is
# interpolated. When the recorder itself delivered this many new frames a
# second, a low count in the picture is the game's, and only noted.
CAPTURE_FULL_FPS = 55.0
SILENT_DB = -60.0           # a recording whose sound never reaches this heard nothing


# ============================================================================
# Windows: the game window
# ============================================================================

_WIN32 = None


def _win32():
    """user32 with typed prototypes (HWND is a pointer: an untyped call would
    pass a 64-bit handle as a C int), the process made DPI-aware once, so
    every rectangle is in physical pixels, as gdigrab's offsets are."""
    global _WIN32
    if _WIN32 is not None:
        return _WIN32
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
    H, B, I, U = wintypes.HWND, wintypes.BOOL, ctypes.c_int, wintypes.UINT
    proto = {
        "GetWindowLongW": (ctypes.c_long, [H, I]),
        "GetClientRect": (B, [H, ctypes.POINTER(wintypes.RECT)]),
        "GetWindowRect": (B, [H, ctypes.POINTER(wintypes.RECT)]),
        "ClientToScreen": (B, [H, ctypes.POINTER(wintypes.POINT)]),
        "AdjustWindowRectEx": (B, [ctypes.POINTER(wintypes.RECT), wintypes.DWORD, B, wintypes.DWORD]),
        "SetWindowPos": (B, [H, H, I, I, I, I, U]),
        "SetForegroundWindow": (B, [H]),
        "IsWindowVisible": (B, [H]),
        "GetWindowTextW": (I, [H, wintypes.LPWSTR, I]),
        "GetWindowThreadProcessId": (wintypes.DWORD, [H, ctypes.POINTER(wintypes.DWORD)]),
        "GetSystemMetrics": (I, [I]),
    }
    for name, (res, args) in proto.items():
        fn = getattr(user32, name)
        fn.restype, fn.argtypes = res, args
    _WIN32 = (ctypes, wintypes, user32)
    return _WIN32


def window_dpi(hwnd: int) -> int | None:
    ctypes, wintypes, user32 = _win32()
    try:
        fn = user32.GetDpiForWindow
    except AttributeError:
        return None
    fn.restype, fn.argtypes = wintypes.UINT, [wintypes.HWND]
    return int(fn(hwnd))


WS_OVERLAPPEDWINDOW = 0x00CF0000
DEFAULT_BORDER = (16, 39)   # measured: +win_w 1280 +win_h 720 gave a 1264x681 client (S01, 2026-10-24)


def frame_border() -> tuple[int, int]:
    """Outer minus client size of a normal window on this desktop: GZDoom's
    win_w/win_h are the OUTER size (the PM's S01 run, 2026-10-24)."""
    if os.name != "nt":
        return DEFAULT_BORDER
    ctypes, wintypes, user32 = _win32()
    rc = wintypes.RECT(0, 0, 100, 100)
    if not user32.AdjustWindowRectEx(ctypes.byref(rc), WS_OVERLAPPEDWINDOW, False, 0):
        return DEFAULT_BORDER
    return (rc.right - rc.left) - 100, (rc.bottom - rc.top) - 100


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


def place_window(hwnd: int, width: int, height: int, origin: tuple[int, int] | None = None) -> None:
    """Give the window a client area of width x height, topmost: centred on
    the primary monitor, or with its client area's top-left at `origin`."""
    ctypes, wintypes, user32 = _win32()
    gwl_style, gwl_exstyle = -16, -20
    style = user32.GetWindowLongW(hwnd, gwl_style) & 0xFFFFFFFF
    exstyle = user32.GetWindowLongW(hwnd, gwl_exstyle) & 0xFFFFFFFF
    if origin is None:
        screen_w, screen_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        origin = ((screen_w - width) // 2, (screen_h - height) // 2)
    rc = wintypes.RECT(origin[0], origin[1], origin[0] + width, origin[1] + height)
    user32.AdjustWindowRectEx(ctypes.byref(rc), style, False, exstyle)
    x, y = max(0, rc.left), max(0, rc.top)
    hwnd_topmost, swp_showwindow = -1, 0x0040
    user32.SetWindowPos(hwnd, hwnd_topmost, x, y, rc.right - rc.left, rc.bottom - rc.top, swp_showwindow)
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
                if rect[2:] == tuple(size):
                    return hwnd, rect, time.monotonic() - started
                for _ in range(RESIZE_TRIES):
                    place_window(hwnd, *size)
                    time.sleep(RESIZE_SETTLE_S)
                    rect = client_rect(hwnd)
                    if rect[2:] == tuple(size):
                        return hwnd, rect, time.monotonic() - started
                # Not forced: film what there is; edit.py scales and crops any
                # client area to 16:9 1080p. Only a useless window fails.
                if rect[2] >= MIN_CLIENT[0] and rect[3] >= MIN_CLIENT[1]:
                    return hwnd, rect, time.monotonic() - started
                raise RuntimeError(f"the window's client area is {rect[2]}x{rect[3]}, "
                                   f"under {MIN_CLIENT[0]}x{MIN_CLIENT[1]}")
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
            if tuple(now) != tuple(rect) and fixes < MAX_WINDOW_FIXES:
                place_window(hwnd, rect[2], rect[3], origin=(rect[0], rect[1]))
                fixes += 1
        time.sleep(0.2)
    return fixes


def dxgi_outputs() -> list[dict]:
    """Every monitor of every graphics adapter, as DXGI numbers them (the
    numbers ddagrab's `-init_hw_device d3d11va=<name>:<adapter>` and
    `output_idx` take): adapter, output, adapter name, desktop rectangle.
    The CEO's PC also has a "Meta Virtual Monitor" adapter, so the monitor
    is chosen by where the window is, never by index 0."""
    import ctypes
    from ctypes import wintypes

    class GUID(ctypes.Structure):
        _fields_ = [("d1", ctypes.c_ulong), ("d2", ctypes.c_ushort), ("d3", ctypes.c_ushort),
                    ("d4", ctypes.c_ubyte * 8)]

    class ADAPTER_DESC(ctypes.Structure):
        _fields_ = [("Description", ctypes.c_wchar * 128), ("VendorId", wintypes.UINT),
                    ("DeviceId", wintypes.UINT), ("SubSysId", wintypes.UINT), ("Revision", wintypes.UINT),
                    ("DedicatedVideoMemory", ctypes.c_size_t), ("DedicatedSystemMemory", ctypes.c_size_t),
                    ("SharedSystemMemory", ctypes.c_size_t), ("LuidLow", wintypes.DWORD),
                    ("LuidHigh", wintypes.LONG)]

    class OUTPUT_DESC(ctypes.Structure):
        _fields_ = [("DeviceName", ctypes.c_wchar * 32), ("Desktop", wintypes.RECT),
                    ("Attached", wintypes.BOOL), ("Rotation", wintypes.UINT), ("Monitor", ctypes.c_void_p)]

    def method(obj, index, *argtypes):
        vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
        return ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)(vtable[index])

    # IDXGIFactory1 {770aae78-f26f-4dba-a829-253c83d1b387}; vtable slots:
    # IUnknown 0-2, IDXGIObject 3-6, IDXGIFactory::EnumAdapters 7;
    # IDXGIAdapter::EnumOutputs 7, GetDesc 8; IDXGIOutput::GetDesc 7.
    iid = GUID(0x770AAE78, 0xF26F, 0x4DBA, (ctypes.c_ubyte * 8)(0xA8, 0x29, 0x25, 0x3C, 0x83, 0xD1, 0xB3, 0x87))
    factory = ctypes.c_void_p()
    if ctypes.WinDLL("dxgi").CreateDXGIFactory1(ctypes.byref(iid), ctypes.byref(factory)) < 0:
        return []
    found = []
    release = lambda obj: method(obj, 2)(obj)  # noqa: E731
    for a in range(16):
        adapter = ctypes.c_void_p()
        if method(factory, 7, wintypes.UINT, ctypes.c_void_p)(factory, a, ctypes.byref(adapter)) < 0:
            break
        desc = ADAPTER_DESC()
        method(adapter, 8, ctypes.c_void_p)(adapter, ctypes.byref(desc))
        for o in range(16):
            output = ctypes.c_void_p()
            if method(adapter, 7, wintypes.UINT, ctypes.c_void_p)(adapter, o, ctypes.byref(output)) < 0:
                break
            od = OUTPUT_DESC()
            method(output, 7, ctypes.c_void_p)(output, ctypes.byref(od))
            r = od.Desktop
            found.append({"adapter": a, "output": o, "name": desc.Description, "device": od.DeviceName,
                          "rect": (r.left, r.top, r.right - r.left, r.bottom - r.top)})
            release(output)
        release(adapter)
    release(factory)
    return found


def dda_target(rect: tuple[int, int, int, int], outputs: list[dict]) -> dict | None:
    """The DXGI output that holds the whole client rectangle, or None."""
    x, y, w, h = rect
    for out in outputs:
        ox, oy, ow, oh = out["rect"]
        if ox <= x and oy <= y and x + w <= ox + ow and y + h <= oy + oh:
            return out
    return None


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


def encoder_args(encoder: str) -> list[str]:
    if encoder == "h264_nvenc":     # NOT VERIFIED here (the driver is too old, see ENCODERS)
        return ["-c:v", "h264_nvenc", "-preset", "p5", "-tune", "hq", "-rc", "vbr", "-cq", NVENC_CQ,
                "-b:v", "0", "-pix_fmt", "yuv420p", "-g", GOP_FRAMES]
    if encoder == "h264_mf":
        return ["-c:v", "h264_mf", "-hw_encoding", "1", "-b:v", MF_BITRATE, "-pix_fmt", "nv12",
                "-g", GOP_FRAMES]
    return ["-c:v", "libx264", "-preset", CAPTURE_PRESET, "-crf", CAPTURE_CRF, "-pix_fmt", "yuv420p",
            "-g", GOP_FRAMES]


def pick_encoder(ffmpeg: Path, wanted: str | None = None) -> str:
    """The first of ENCODERS that encodes a fraction of a second of 720p60
    here (an encoder can be built in and still not open: NVENC on an old
    driver)."""
    for enc in ([wanted] if wanted else list(ENCODERS)):
        cmd = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-f", "lavfi",
               "-i", "color=c=gray:s=1280x720:r=60:d=0.2"] + encoder_args(enc) + ["-f", "null", "-"]
        try:
            if subprocess.run(cmd, capture_output=True, timeout=ENCODER_PROBE_S).returncode == 0:
                return enc
        except (OSError, subprocess.TimeoutExpired):
            pass
    return "libx264"


def ffmpeg_command(ffmpeg: Path, rect: tuple[int, int, int, int], fps: int, out: Path,
                   audio_device: str | None, method: str = "gdigrab", hwnd: int | None = None,
                   dda: dict | None = None, encoder: str = "libx264",
                   progress: Path | None = None) -> list[str]:
    """The recorder of one shot. gfxcapture films the window `hwnd` (its
    client area); ddagrab and gdigrab film the screen rectangle `rect`
    (ddagrab on the DXGI output `dda`, offsets relative to that monitor).
    Video timestamps are the capture's own clock; `-fps_mode cfr` repeats a
    frame only where the recorder brought none, and `-progress` reports how
    many it repeated (capture_stats). The loopback audio is the first input,
    so it is opened before the picture starts."""
    x, y, w, h = rect
    cmd = [str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-y"]
    if progress is not None:
        cmd += ["-progress", str(progress), "-stats_period", STATS_PERIOD_S]
    audio_map = None
    if method == "gdigrab":
        cmd += ["-thread_queue_size", "1024", "-f", "gdigrab", "-framerate", str(fps), "-draw_mouse", "0",
                "-offset_x", str(x), "-offset_y", str(y), "-video_size", f"{w}x{h}", "-i", "desktop"]
        video_map, audio_map = "0:v", "1:a"
    else:
        video_map, audio_map = "[v]", "0:a"
    if audio_device:
        cmd += ["-thread_queue_size", "1024", "-f", "dshow", "-audio_buffer_size", "50",
                "-i", f"audio={audio_device}"]
    if method == "gfxcapture":
        if not hwnd:
            raise ValueError("gfxcapture films a window: it needs its HWND")
        cmd += ["-filter_complex",
                f"gfxcapture=hwnd={int(hwnd)}:max_framerate={fps}:capture_cursor=0:capture_border=0,"
                "hwdownload,format=bgra[v]"]
    elif method == "ddagrab":
        if dda is None:
            raise ValueError("ddagrab needs the DXGI output that holds the window")
        ox, oy = dda["rect"][:2]
        cmd += ["-init_hw_device", f"d3d11va=dda:{dda['adapter']}", "-filter_hw_device", "dda",
                "-filter_complex",
                f"ddagrab=output_idx={dda['output']}:framerate={fps}:video_size={w}x{h}:"
                f"offset_x={x - ox}:offset_y={y - oy}:draw_mouse=0:dup_frames=0,hwdownload,format=bgra[v]"]
    elif method != "gdigrab":
        raise ValueError(f"unknown capture method {method!r} (known: {', '.join(CAPTURE_METHODS)})")
    cmd += ["-map", video_map] + (["-map", audio_map] if audio_device else [])
    cmd += ["-fps_mode", "cfr", "-r", str(fps)] + encoder_args(encoder)
    if audio_device:
        cmd += ["-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
    cmd.append(str(out))
    return cmd


def read_progress(path: Path) -> dict[str, str]:
    """The last value of every key FFmpeg's -progress wrote."""
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return values
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip()
    return values


def capture_stats(progress: dict[str, str]) -> dict:
    """Frames written, frames FFmpeg had to repeat (the recorder brought
    none for that 1/60 s), and the new frames a second the recorder
    delivered: (frames - repeated) / seconds."""
    def num(key, kind=int):
        try:
            return kind(progress[key])
        except (KeyError, ValueError):
            return None
    frames, dups, us = num("frame"), num("dup_frames"), num("out_time_us")
    stats = {"frames": frames, "dup_frames": dups, "seconds": round(us / 1e6, 3) if us else None}
    stats["delivered_fps"] = (round((frames - (dups or 0)) / (us / 1e6), 2)
                              if frames and us and us > 0 else None)
    return stats


def start_recorder(cmd: list[str], err_path: Path, progress: Path, game: subprocess.Popen,
                   probe_s: float = PROBE_S) -> tuple[subprocess.Popen | None, str | None]:
    """Start FFmpeg and give it probe_s: (the running recorder, None), or
    (None, why it failed) after stopping it."""
    if progress.exists():
        progress.unlink()
    with open(err_path, "a", encoding="utf-8") as err:
        err.write(f"\n=== {subprocess.list2cmdline(cmd)}\n")
    err = open(err_path, "a", encoding="utf-8")
    rec = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err)
    err.close()
    deadline = time.monotonic() + probe_s
    while time.monotonic() < deadline and game.poll() is None:
        if rec.poll() is not None:
            tail = err_path.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-1:]
            return None, f"FFmpeg exited ({rec.returncode}): {' '.join(tail)}"
        time.sleep(0.1)
    if rec.poll() is not None:
        return None, f"FFmpeg exited ({rec.returncode})"
    frames = capture_stats(read_progress(progress)).get("frames") or 0
    if frames <= 0:
        stop_ffmpeg(rec)
        return None, f"no frames after {probe_s:.1f} s"
    return rec, None


# ============================================================================
# Smoothness: how many new pictures a second the recording really has
# ============================================================================

_DIFF_RE = re.compile(r"pts_time:\s*([-\d.]+)\s*\n\s*lavfi\.signalstats\.YAVG=([-\d.]+)")


def parse_frame_diffs(text: str) -> list[tuple[float, float]]:
    """(time, change from the previous frame) from FFmpeg's metadata print."""
    return [(float(t), float(d)) for t, d in _DIFF_RE.findall(text)]


def frame_diffs(ffmpeg: Path, video: Path) -> list[tuple[float, float]]:
    """Every frame's change from the one before (see DIFF_EPS). The metadata
    file is written next to the video by a bare name (a drive letter's colon
    would end the filter option)."""
    name = f"{video.stem}.diff.txt"
    w, h = MEASURE_SIZE
    vf = (f"scale={w}:{h}:flags=area,format=gray,tblend=all_mode=difference,signalstats,"
          f"metadata=mode=print:key=lavfi.signalstats.YAVG:file={name}")
    subprocess.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", video.name, "-an",
                    "-vf", vf, "-f", "null", "-"], cwd=str(video.parent), capture_output=True,
                   timeout=300)
    out = video.parent / name
    try:
        return parse_frame_diffs(out.read_text(encoding="utf-8", errors="replace"))
    finally:
        out.unlink(missing_ok=True)


def motion_report(diffs: list[tuple[float, float]], delivered_fps: float | None = None,
                  min_fps: float = MIN_EFFECTIVE_FPS) -> dict:
    """The verdict on one recording. Per full MEASURE_WINDOW_S window that
    moves (its changes, cuts left out, add up to MOTION_TOTAL): how many frames
    differ from the one before, a second. The shot is choppy when the median
    of those is under min_fps, unless the recorder delivered CAPTURE_FULL_FPS
    new frames a second (then the picture itself changed that slowly: noted),
    or when the recorder delivered under min_fps."""
    rep: dict = {"delivered_fps": delivered_fps, "min_fps": min_fps}
    buckets: dict[int, list[float]] = {}
    if diffs:
        t0, t_end = diffs[0][0], diffs[-1][0]
        full = int((t_end - t0) / MEASURE_WINDOW_S)
        for t, d in diffs:
            k = int((t - t0) / MEASURE_WINDOW_S)
            if k < full:
                buckets.setdefault(k, []).append(d)
    moving = []
    for k in sorted(buckets):
        w = [d for d in buckets[k] if d < CUT_DIFF]     # a cut is neither motion nor a gap
        if sum(w) < MOTION_TOTAL:
            continue
        moving.append((round(k * MEASURE_WINDOW_S, 2), round(sum(d > DIFF_EPS for d in w) / MEASURE_WINDOW_S, 1)))
    content = round(statistics.median(r for _, r in moving), 1) if moving else None
    rep.update(frames=len(diffs) + (1 if diffs else 0), moving_windows=len(moving),
               content_fps=content, slow_windows=[m for m in moving if m[1] < min_fps][:20])
    rep["ok"], rep["why"] = True, ""
    if not diffs:
        rep["ok"], rep["why"] = False, "no frames to measure"
    elif delivered_fps is not None and delivered_fps < min_fps:
        rep["ok"] = False
        rep["why"] = f"the recorder delivered {delivered_fps:.1f} new frames/s (< {min_fps:.0f})"
    elif content is not None and content < min_fps:
        if delivered_fps is not None and delivered_fps >= CAPTURE_FULL_FPS:
            rep["why"] = (f"note: {content:.1f} new frames/s where it moves, but the recorder had "
                          f"{delivered_fps:.1f}: the game's own 35 Hz animation, not the capture")
        else:
            rep["ok"] = False
            rep["why"] = f"only {content:.1f} new frames/s where the picture moves (< {min_fps:.0f})"
    return rep


def describe(rep: dict) -> str:
    parts = []
    if rep.get("delivered_fps") is not None:
        parts.append(f"{rep['delivered_fps']:.1f} fps delivered")
    if rep.get("content_fps") is not None:
        parts.append(f"{rep['content_fps']:.1f} new frames/s in {rep['moving_windows']} s of motion")
    return ", ".join(parts) or "nothing measured"


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
        # The whole tree: C:\ProgramData\chocolatey\bin\ffmpeg.exe is a shim
        # that starts the real ffmpeg.exe, and terminate() would only end the
        # shim and leave the recorder running (seen 2026-10-27 with ffplay's).
        smoke._kill_group(proc)
        return proc.poll()


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


def method_order(preferred: str | None, forced: str | None = None) -> list[str]:
    """`--capture X` films with X only; `auto` starts from the method that
    worked last and falls back through the rest of CAPTURE_METHODS."""
    if forced and forced != "auto":
        return [forced]
    order = list(CAPTURE_METHODS)
    if preferred in order:
        order.remove(preferred)
        order.insert(0, preferred)
    return order


def audio_peak_db(ffmpeg: Path, video: Path) -> float | None:
    """The loudest sample of the recording's sound, dBFS (None: no sound)."""
    try:
        err = subprocess.run([str(ffmpeg), "-hide_banner", "-nostats", "-i", str(video), "-vn",
                              "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True,
                             errors="replace", timeout=300).stderr
    except (OSError, subprocess.TimeoutExpired):
        return None
    found = re.search(r"max_volume:\s*(-?[\d.]+|-inf) dB", err)
    if not found:
        return None
    return float("-inf") if found.group(1) == "-inf" else float(found.group(1))


def measure(ffmpeg: Path, video: Path, progress: Path | None) -> dict:
    stats = capture_stats(read_progress(progress)) if progress is not None and progress.is_file() else {}
    rep = motion_report(frame_diffs(ffmpeg, video), stats.get("delivered_fps"))
    rep["capture"] = stats
    peak = audio_peak_db(ffmpeg, video)
    rep["audio_peak_db"] = peak
    if peak is not None and peak < SILENT_DB:
        rep["audio_note"] = (f"the sound peaks at {peak:.0f} dBFS: the loopback heard nothing "
                             "(GZDoom's volume, or its output is not the loopback's card: --al-device)")
    return rep


def capture_shot(shot: dict, names: list[str], gzdoom: Path, iwad: Path, pk3s: list[Path],
                 helper: Path, ffmpeg: Path, audio_device: str | None, window: tuple[int, int],
                 fps: int, notes: list[str], state: dict | None = None) -> dict:
    """state: {"forced": --capture, "preferred": the method that worked last,
    "encoder": the encoder, "extra": more engine cvars}; updated in place."""
    state = state if state is not None else {}
    tl.SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    sid = shot["id"]
    video = tl.SHOTS_DIR / f"{sid}.mkv"
    log = tl.SHOTS_DIR / f"{sid}.log"
    err_path = tl.SHOTS_DIR / f"{sid}.ffmpeg.txt"
    progress = tl.SHOTS_DIR / f"{sid}.progress.txt"
    err_path.write_text("", encoding="utf-8")
    encoder = state.get("encoder", "libx264")
    bw, bh = frame_border()
    outer = (window[0] + bw, window[1] + bh)    # win_w/win_h are the outer size
    argv = tl.engine_argv(gzdoom, iwad, pk3s, helper, seed_config(), log, shot, names, outer,
                          sound=audio_device is not None, extra=tuple(state.get("extra", ())))
    manifest = {"id": sid, "when": datetime.now().isoformat(timespec="seconds"), "argv": argv,
                "fps": fps, "audio_device": audio_device, "window": list(window), "notes": notes,
                "shot": shot, "ok": False}
    timeout = tl.sequence_seconds(shot, names) + TIMEOUT_MARGIN_S
    game = subprocess.Popen(argv, cwd=str(tl.PROJECT_ROOT), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **smoke._spawn_options())
    rec = None
    try:
        hwnd, rect, shown_s = wait_for_window(game, window)
        manifest.update(rect=list(rect), window_after_s=round(shown_s, 2), outer_asked=list(outer),
                        dpi=window_dpi(hwnd))
        if tuple(rect[2:]) != tuple(window):
            notes.append(f"client area {rect[2]}x{rect[3]}, not {window[0]}x{window[1]}: "
                         "edit.py scales it to the trailer's frame")
        tried = []
        for method in method_order(state.get("preferred"), state.get("forced")):
            dda = None
            if method == "ddagrab":
                dda = dda_target(rect, dxgi_outputs())
                if dda is None:
                    tried.append("ddagrab: no DXGI output holds the window")
                    continue
            cmd = ffmpeg_command(ffmpeg, rect, fps, video, audio_device, method=method, hwnd=hwnd,
                                 dda=dda, encoder=encoder, progress=progress)
            rec, why = start_recorder(cmd, err_path, progress, game)
            if rec is not None:
                manifest.update(ffmpeg=cmd, capture_method=method, encoder=encoder,
                                dda_output=dda)
                state["preferred"] = method
                break
            tried.append(f"{method}: {why}")
        if tried:
            manifest["capture_fallbacks"] = tried
            notes.extend(tried)
        if rec is None:
            raise RuntimeError("no recorder started: " + "; ".join(tried))
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
    if rec is not None and video.is_file():
        manifest["motion"] = measure(ffmpeg, video, progress)
    manifest["ok"] = ("error" not in manifest and video.is_file() and manifest["roll_seen_in_log"]
                      and not manifest["script_errors"] and manifest.get("motion", {}).get("ok", False))
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
    ap.add_argument("--capture", choices=("auto",) + CAPTURE_METHODS, default="auto",
                    help="how to film the window (default auto: gfxcapture, then ddagrab, then gdigrab)")
    ap.add_argument("--encoder", choices=ENCODERS,
                    help="the video encoder (default: the first of %s that opens here)" % ", ".join(ENCODERS))
    ap.add_argument("--al-device",
                    help="GZDoom's OpenAL output (snd_aldevice), e.g. \"OpenAL Soft on Altavoces (Sound "
                         "Blaster Z SE)\": the loopback only hears the card it belongs to")
    ap.add_argument("--measure", action="store_true",
                    help="measure the smoothness of the shots already filmed, run no engine")
    ap.add_argument("--print", action="store_true", help="print the argv and FFmpeg command, run nothing")
    ap.add_argument("--list", action="store_true", help="list the shots, run nothing")
    return ap.parse_args(argv)


def extra_cvars(args: argparse.Namespace) -> tuple[tuple[str, str], ...]:
    return (("snd_aldevice", args.al_device),) if getattr(args, "al_device", None) else ()


def measure_existing(wanted: list[str], shots: dict) -> int:
    """--measure: the smoothness verdict on recordings already in SHOTS_DIR."""
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("ffmpeg not found", file=sys.stderr)
        return EXIT_PLATFORM
    failed = 0
    for sid in wanted:
        if shots[sid].kind != "engine":
            continue
        video = tl.SHOTS_DIR / f"{sid}.mkv"
        if not video.is_file():
            print(f"{sid}: no recording")
            continue
        rep = measure(ffmpeg, video, tl.SHOTS_DIR / f"{sid}.progress.txt")
        print(f"{sid}: {'ok' if rep['ok'] else 'CHOPPY'} ({describe(rep)})" + (f": {rep['why']}" if rep["why"] else ""))
        if rep.get("audio_note"):
            print(f"  note: {rep['audio_note']}")
        failed += 0 if rep["ok"] else 1
    return EXIT_SHOT_FAILED if failed else 0


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

    if args.measure:
        return measure_existing(wanted, shots)

    pk3s = args.pk3 or [tl.PROJECT_ROOT / "dist" / f"{smoke.MOD_NAME}.pk3"]
    if args.print:
        ffmpeg = find_ffmpeg() or Path("ffmpeg")
        methods = method_order(None, args.capture)
        encoder = args.encoder or ENCODERS[0]
        for sid in wanted:
            shot = shots[sid].data
            if shot.get("kind", "engine") != "engine":
                continue
            bw, bh = frame_border()
            argv_ = tl.engine_argv(Path("gzdoom.exe"), Path("freedoom2.wad"), pk3s, tl.HELPER_PK3,
                                   TRAILER_CONFIG, tl.SHOTS_DIR / f"{sid}.log", shot, names,
                                   (window[0] + bw, window[1] + bh),
                                   sound=not args.no_audio, extra=extra_cvars(args))
            print(f"--- {sid} ({tl.sequence_seconds(shot, names):.1f} s of console sequence)")
            print(subprocess.list2cmdline(argv_))
            example = {"adapter": 0, "output": 0, "rect": (0, 0, 1920, 1080)}
            for method in methods:
                print(f"# {method}" + (" (the HWND and the rectangle are examples)" if method == methods[0] else ""))
                print(subprocess.list2cmdline(ffmpeg_command(
                    ffmpeg, (320, 180, *window), fps, tl.SHOTS_DIR / f"{sid}.mkv",
                    None if args.no_audio else (args.audio_device or "<loopback>"), method=method,
                    hwnd=0x1234, dda=example, encoder=encoder, progress=tl.SHOTS_DIR / f"{sid}.progress.txt")))
        return 0

    if not smoke.engine_allowed():
        print(smoke.ENGINE_GATE_MSG, file=sys.stderr)
        return EXIT_BLOCKED
    if os.name != "nt":
        print("capture.py films a Windows window (gfxcapture/ddagrab/gdigrab); this is not Windows",
              file=sys.stderr)
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
    encoder = pick_encoder(ffmpeg, args.encoder)
    if args.encoder and encoder != args.encoder:
        print(f"note: {args.encoder} does not open here; encoding with {encoder}", file=sys.stderr)
    print(f"capture: {args.capture} ({', '.join(method_order(None, args.capture))}), encoder {encoder}")
    state = {"forced": args.capture, "encoder": encoder, "extra": extra_cvars(args)}
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
        m = capture_shot(shot, names, gzdoom, iwad, pk3s, helper, ffmpeg, audio, window, fps, notes, state)
        motion = m.get("motion", {})
        status = "ok" if m["ok"] else "FAILED: " + (m.get("error") or
                                                     ("no roll in the log" if not m["roll_seen_in_log"]
                                                      else "; ".join(m["script_errors"]) or
                                                      motion.get("why") or "no video"))
        detail = f" [{m.get('capture_method', '?')}: {describe(motion)}]" if motion else ""
        print(status + detail + (f" ({len(m['spawns_failed'])} spawn(s) blocked)" if m["spawns_failed"] else ""))
        if m["ok"] and motion.get("why"):
            print(f"  {motion['why']}")
        if motion.get("audio_note"):
            print(f"  note: {motion['audio_note']}")
        failed += 0 if m["ok"] else 1
    print(f"shots in {tl.SHOTS_DIR}; next: python tools/trailer/edit.py")
    return EXIT_SHOT_FAILED if failed else 0


if __name__ == "__main__":
    sys.exit(main())
