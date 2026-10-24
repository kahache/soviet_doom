#!/usr/bin/env python3
"""Shared core of the 60 s trailer tools (V3, D3, D132): the shot list, the
cards, the map geometry the shots are checked against, the console sequence
of each shot and the throwaway helper PK3 that drives the camera.

Nothing here starts GZDoom (D26): `capture.py` is the only trailer tool that
does, behind SD_ALLOW_ENGINE=1, and it is the PM's. `edit.py` cuts and mixes
what capture.py recorded. The script and the cut list are
`docs/product/2026-10-24_V3_trailer-script.md`.

Files:
  tools/trailer/shots.json   the shots (map, skill, camera, actions) and the
                             timeline (bars of music per segment)
  tools/trailer/cards.json   the on-screen texts, EN / RU / CA
  work/trailer/              everything generated (gitignored): the helper
                             PK3, the raw shots, the music render, the
                             card PNGs, the exports

The camera is the player. Each shot launches the mod on one map with a
console sequence (route.py's method): cheats and gifts first, then a warp
and a view, all UNDER A SLATE (the helper paints the whole screen magenta
from the level's first frame); then `netevent sdroll` lifts the slate and
the shot's actions run, in tics. The first frame without the slate is the
shot's time zero: edit.py finds it in the recording, so the engine's
start-up time never matters and every cut is frame-exact against the
sequence's tics.

Python 3 standard library (+ route.py for the map data, which imports the
map sources through the build's own importer).
"""

from __future__ import annotations

import json
import math
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

TRAILER_DIR = Path(__file__).resolve().parent
TOOLS_DIR = TRAILER_DIR.parent
PROJECT_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import route  # noqa: E402  (map data, the proven route helper ZScript)

SHOTS_JSON = TRAILER_DIR / "shots.json"
CARDS_JSON = TRAILER_DIR / "cards.json"
WORK_DIR = PROJECT_ROOT / "work" / "trailer"
SHOTS_DIR = WORK_DIR / "shots"
HELPER_PK3 = WORK_DIR / "helper" / "sd-trailer-helper.pk3"
LANGUAGE_PATH = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"
FORBIDDEN_HELPER_ROOTS = (PROJECT_ROOT / "dist", PROJECT_ROOT / "src", PROJECT_ROOT / "assets")

TICS_PER_SECOND = 35
LOCALES = ("en", "ru", "ca")
LANGUAGE_SECTIONS = {"en": "enu default", "ru": "ru", "ca": "ca"}

# --- The player as a camera (Doom's numbers; the mod keeps them) ------------
PLAYER_RADIUS = 16
PLAYER_HEIGHT = 56
EYE_HEIGHT = 41          # Doom's default ViewHeight; src/zscript/sd/player.zs keeps it
MAX_STEP = 24

# --- Pre-roll: what happens under the slate --------------------------------
LOAD_TICS = 140          # route.LOAD_TICS: the map is drawn before the first command
SETTLE_TICS = 3          # after a warp, a view, a netevent
RAISE_TICS = 35          # a weapon switch: lower + raise, generously
PREROLL_MIN_TICS = 210   # at least 6 s of slate after the load, so ffmpeg is rolling
SPAWN_SETTLE_TICS = 8    # spawned monsters see the player before the roll
QUIT_TICS = 35           # after the last action, before quit
USE_HOLD_TICS = 2

# Monster sizes (src/zscript/monsters/*.zs constants), for the spawn checks.
ACTOR_SIZE = {
    "SD_ReichRifleman": (20, 56), "SD_LegionTrooper": (20, 56), "SD_Stormtrooper": (20, 56),
    "SD_ReichHound": (30, 56), "SD_Doughboy": (31, 56), "SD_Panzermensch": (24, 64),
    "SD_PanzermenschSchwer": (24, 64), "SD_LegionGunner": (20, 56), "SD_General": (40, 100),
    "SD_LibertyColossus": (44, 110), "SD_ChromeGeneral": (44, 110), "SD_Consortium": (56, 128),
}
WEAPONS = ("SD_IceAxe", "SD_Tokarev", "SD_Izh", "SD_Ppsh", "SD_Akm", "SD_Rpg7", "SD_Roks3",
           "SD_HandKatyusha", "SD_Rgd5")
MAPS = ("MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09", "RANGE")


class TrailerError(ValueError):
    """A shot list, a card or a timeline that cannot be used."""


# ============================================================================
# Shot actions (after the roll) and their console commands
# ============================================================================

ACTION_ARITY = {
    "wait": 1, "forward": 1, "back": 1, "left": 1, "right": 1, "fire": 1, "altfire": 1,
    "pan": 2, "tilt": 2, "weapon": 1, "spawn": (2, 3, 4), "hurt": 2, "use": 0, "exit": 0,
    "run": 1, "calm": 1,
}
_MOVE_KEYS = {"forward": "forward", "back": "back", "left": "moveleft", "right": "moveright",
              "fire": "attack", "altfire": "altattack"}


def parse_action(text: str) -> tuple[str, list[str]]:
    parts = str(text).split()
    if not parts or parts[0] not in ACTION_ARITY:
        raise TrailerError(f"unknown action {text!r} (known: {', '.join(ACTION_ARITY)})")
    word, args = parts[0], parts[1:]
    arity = ACTION_ARITY[word]
    allowed = arity if isinstance(arity, tuple) else (arity,)
    if len(args) not in allowed:
        raise TrailerError(f"{word} takes {allowed} argument(s): {text!r}")
    if word in ("wait", "forward", "back", "left", "right", "fire", "altfire"):
        if not args[0].isdigit() or int(args[0]) <= 0:
            raise TrailerError(f"{word} needs a positive tic count: {text!r}")
    if word in ("pan", "tilt"):
        _int(args[0], text)
        if not args[1].isdigit() or int(args[1]) <= 0:
            raise TrailerError(f"{word} needs a positive tic count: {text!r}")
    if word == "spawn":
        _int(args[1], text)
        if len(args) >= 3:
            _int(args[2], text)
        if len(args) == 4 and args[3] != "hold":
            raise TrailerError(f"spawn's fourth word can only be 'hold': {text!r}")
    if word == "calm" and (not args[0].isdigit() or int(args[0]) <= 0):
        raise TrailerError(f"calm needs a positive radius: {text!r}")
    if word == "hurt":
        _int(args[1], text)
    if word == "run" and args[0] not in ("on", "off"):
        raise TrailerError(f"run takes on/off: {text!r}")
    return word, args


def _int(value: str, text: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise TrailerError(f"not an integer in {text!r}") from exc


def action_tics(text: str) -> int:
    word, args = parse_action(text)
    if word in ("wait", "forward", "back", "left", "right", "fire", "altfire"):
        return int(args[0])
    if word in ("pan", "tilt"):
        return 0        # runs in the background (the helper's WorldTick); wait for it
    if word == "use":
        return USE_HOLD_TICS
    return SETTLE_TICS


def action_commands(text: str, names: list[str]) -> list[str]:
    word, args = parse_action(text)
    if word == "wait":
        return [f"wait {args[0]}"]
    if word in _MOVE_KEYS:
        key = _MOVE_KEYS[word]
        return [f"+{key}", f"wait {args[0]}", f"-{key}"]
    if word == "pan":
        return [f"netevent sdpan {int(args[0])} {int(args[1])}"]
    if word == "tilt":
        return [f"netevent sdtilt {int(args[0])} {int(args[1])}"]
    if word == "weapon":
        return [f"use {args[0]}", f"wait {SETTLE_TICS}"]
    if word == "spawn":
        side = int(args[2]) if len(args) >= 3 else 0
        hold = 1 if len(args) == 4 else 0
        return [f"netevent sdspawn {names.index(args[0])} {int(args[1])} {side} {hold}", f"wait {SETTLE_TICS}"]
    if word == "calm":
        return [f"netevent sdcalm {int(args[0])}", f"wait {SETTLE_TICS}"]
    if word == "hurt":
        return [f"netevent sdthurt {names.index(args[0])} {int(args[1])}", f"wait {SETTLE_TICS}"]
    if word == "use":
        return ["+use", f"wait {USE_HOLD_TICS}", "-use"]
    if word == "exit":
        return ["netevent sdexit", f"wait {SETTLE_TICS}"]
    if word == "run":
        return [f"cl_run {1 if args[0] == 'on' else 0}"]
    raise TrailerError(f"unhandled action {text!r}")  # pragma: no cover


# ============================================================================
# The shot list
# ============================================================================

@dataclass(frozen=True)
class Shot:
    id: str
    kind: str                       # "engine" or "still"
    data: dict

    @property
    def map(self) -> str | None:
        return self.data.get("map")

    @property
    def skill(self) -> int:
        return int(self.data.get("skill", 3))

    @property
    def requires(self) -> list[str]:
        return list(self.data.get("requires", ()))


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_shots(path: Path = SHOTS_JSON) -> dict:
    data = load_json(path)
    errors = validate_shots(data)
    if errors:
        raise TrailerError("shots.json:\n  " + "\n  ".join(errors))
    return data


def shots_by_id(data: dict) -> dict[str, Shot]:
    return {s["id"]: Shot(s["id"], s.get("kind", "engine"), s) for s in data["shots"]}


def classes_used(data: dict) -> list[str]:
    """Every class a spawn or hurt names, in a stable order: the helper's NAMES."""
    names: list[str] = []
    for s in data["shots"]:
        for text in list(s.get("setup", ())) + list(s.get("actions", ())):
            word, args = parse_action(text)
            if word in ("spawn", "hurt") and args[0] not in names:
                names.append(args[0])
    return names


ID_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,15}$")
STILL_MOTIONS = ("none", "push", "pull")


def validate_shots(data: dict) -> list[str]:
    """Structure only (no map geometry: see check_geometry)."""
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["the top level must be an object"]
    for key in ("shots", "timeline", "music", "video"):
        if key not in data:
            errs.append(f"missing {key!r}")
    if errs:
        return errs
    seen: set[str] = set()
    for s in data["shots"]:
        sid = s.get("id", "?")
        if not ID_RE.match(str(sid)):
            errs.append(f"shot id {sid!r} must match {ID_RE.pattern}")
        if sid in seen:
            errs.append(f"shot {sid}: duplicate id")
        seen.add(sid)
        kind = s.get("kind", "engine")
        if kind == "engine":
            if s.get("map") not in MAPS:
                errs.append(f"shot {sid}: map {s.get('map')!r} is not one of {MAPS}")
            if int(s.get("skill", 3)) not in (1, 2, 3, 4, 5):
                errs.append(f"shot {sid}: skill must be 1-5")
            warp = s.get("warp")
            if not (isinstance(warp, list) and len(warp) == 2 and all(isinstance(v, int) for v in warp)):
                errs.append(f"shot {sid}: warp must be [x, y] integers")
            if not isinstance(s.get("angle"), int):
                errs.append(f"shot {sid}: angle must be an integer (0 east, 90 north)")
            if not -60 <= int(s.get("pitch", 0)) <= 60:
                errs.append(f"shot {sid}: pitch out of -60..60")
            for w in [s.get("weapon")] + list(s.get("give", ())):
                if w is not None and w not in WEAPONS and w not in ("ammo", "armor", "health"):
                    errs.append(f"shot {sid}: unknown weapon or gift {w!r}")
            for text in list(s.get("setup", ())) + list(s.get("actions", ())):
                try:
                    word, args = parse_action(text)
                except TrailerError as exc:
                    errs.append(f"shot {sid}: {exc}")
                    continue
                if word in ("spawn", "hurt") and args[0] not in ACTOR_SIZE:
                    errs.append(f"shot {sid}: {word} of unknown class {args[0]!r}")
                if word == "weapon" and args[0] not in WEAPONS:
                    errs.append(f"shot {sid}: weapon {args[0]!r} unknown")
            if not s.get("actions"):
                errs.append(f"shot {sid}: no actions after the roll")
            fb = s.get("fallback")
            if fb is not None and not isinstance(fb, dict):
                errs.append(f"shot {sid}: fallback must be an object")
            look = s.get("look_at")
            if look is not None and not (isinstance(look, list) and len(look) == 2):
                errs.append(f"shot {sid}: look_at must be [x, y]")
        elif kind == "still":
            if not s.get("image"):
                errs.append(f"shot {sid}: a still needs an image")
            if s.get("motion", "none") not in STILL_MOTIONS:
                errs.append(f"shot {sid}: motion must be one of {STILL_MOTIONS}")
        else:
            errs.append(f"shot {sid}: kind {kind!r} must be engine or still")
    shots = {s.get("id"): s for s in data["shots"]}
    cards = {}
    try:
        cards = load_json(CARDS_JSON)["cards"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        errs.append(f"cards.json unreadable: {exc}")
    for i, seg in enumerate(data["timeline"]):
        where = f"timeline[{i}]"
        if ("shot" in seg) == ("black" in seg):
            errs.append(f"{where}: exactly one of 'shot' or 'black'")
        if "shot" in seg and seg["shot"] not in shots:
            errs.append(f"{where}: unknown shot {seg['shot']!r}")
        if not isinstance(seg.get("bars"), (int, float)) or seg["bars"] <= 0:
            errs.append(f"{where}: bars must be positive")
        for c in seg.get("cards", ()):
            cid, span = card_ref(c)
            if cid not in cards:
                errs.append(f"{where}: unknown card {cid!r}")
            if span < 1 or i + span > len(data["timeline"]):
                errs.append(f"{where}: card {cid} spans past the timeline")
        if seg.get("transition", "cut") not in ("cut", "flash", "fade"):
            errs.append(f"{where}: transition must be cut, flash or fade")
        if "shot" in seg:
            shot = shots.get(seg["shot"], {})
            if shot.get("kind", "engine") == "engine":
                need = float(seg.get("from", 0.0)) + segment_seconds(data, seg)
                have = roll_tics(shot) / TICS_PER_SECOND if shot.get("actions") else 0
                if need > have + 1e-6:
                    errs.append(f"{where}: needs {need:.2f} s of {seg['shot']} after the roll, "
                                f"the shot runs {have:.2f} s")
    music = data["music"]
    for part in ("intro", "main"):
        if part in music:
            m = music[part]
            if not (PROJECT_ROOT / m.get("file", "")).is_file():
                errs.append(f"music.{part}: no file {m.get('file')!r}")
            if not m.get("bpm"):
                errs.append(f"music.{part}: bpm missing")
    return errs


def card_ref(entry) -> tuple[str, int]:
    """A timeline card: "ID" (this segment) or {"id": ID, "span": n} (n segments)."""
    if isinstance(entry, dict):
        return str(entry.get("id")), int(entry.get("span", 1))
    return str(entry), 1


def card_windows(data: dict) -> list[tuple[str, float, float]]:
    """[(card id, start s, end s)] over the whole cut."""
    tl = timeline(data)
    out = []
    for i, (start, _end, seg) in enumerate(tl):
        for entry in seg.get("cards", ()):
            cid, span = card_ref(entry)
            end = tl[min(i + span, len(tl)) - 1][1]
            if seg.get("end") or tl[min(i + span, len(tl)) - 1][2].get("end"):
                end += float(data["video"].get("tail_s", 0.0))
            out.append((cid, start, end))
    return out


def bar_seconds(music_part: dict) -> float:
    return music_part.get("beats_per_bar", 4) * 60.0 / float(music_part["bpm"])


def intro_seconds(data: dict) -> float:
    intro = data["music"].get("intro")
    return intro["bars"] * bar_seconds(intro) if intro else 0.0


def segment_seconds(data: dict, seg: dict) -> float:
    """Timeline segments are counted in bars of the main piece, except the
    ones flagged "intro", which run on the intro's bars."""
    part = data["music"]["intro"] if seg.get("intro") else data["music"]["main"]
    return float(seg["bars"]) * bar_seconds(part)


def timeline(data: dict) -> list[tuple[float, float, dict]]:
    """[(start, end, segment)] in seconds from the first frame."""
    out, t = [], 0.0
    for seg in data["timeline"]:
        d = segment_seconds(data, seg)
        out.append((t, t + d, seg))
        t += d
    return out


def total_seconds(data: dict) -> float:
    tl = timeline(data)
    return (tl[-1][1] if tl else 0.0) + float(data["video"].get("tail_s", 0.0))


# ============================================================================
# The console sequence of one shot
# ============================================================================

def resolve(shot: dict, available: set[str] | None) -> tuple[dict, list[str]]:
    """The shot as it will run on this PK3: a shot whose `requires` classes are
    missing runs its `fallback` (merged over it) instead; notes say so."""
    notes: list[str] = []
    missing = [c for c in shot.get("requires", ()) if available is not None and c not in available]
    if missing:
        fb = shot.get("fallback")
        if fb is None:
            return {}, [f"{shot['id']}: skipped, the PK3 lacks {', '.join(missing)} and there is no fallback"]
        merged = dict(shot)
        merged.update(fb)
        merged.pop("requires", None)
        notes.append(f"{shot['id']}: the PK3 lacks {', '.join(missing)}; running its fallback")
        return merged, notes
    return shot, notes


def setup_commands(shot: dict, names: list[str]) -> list[str]:
    """Everything before the roll, under the slate."""
    cmds = [f"wait {LOAD_TICS}"]
    if shot.get("god", True):
        cmds += ["god", f"wait {SETTLE_TICS}"]
    if shot.get("notarget", False):
        cmds += ["notarget", f"wait {SETTLE_TICS}"]
    for gift in shot.get("give", ()):
        cmds += [f"give {gift}", f"wait {SETTLE_TICS}"]
    if shot.get("weapon"):
        cmds += [f"give {shot['weapon']}", f"wait {SETTLE_TICS}", "give ammo", f"wait {SETTLE_TICS}",
                 f"use {shot['weapon']}", f"wait {RAISE_TICS}"]
    cmds += [f"cl_run {1 if shot.get('run') else 0}"]
    # The long wait comes BEFORE the warp: spawned or woken monsters must not
    # stand 4 s under the slate before the roll.
    used = sum(int(c.split()[1]) for c in cmds if c.startswith("wait "))
    cmds += [f"wait {max(PREROLL_MIN_TICS + LOAD_TICS - used, SETTLE_TICS)}"]
    x, y = shot["warp"]
    view = f"netevent sdview {int(shot['angle'])} {int(shot.get('pitch', 0))}"
    cmds += ["netevent sdstop", f"wait {SETTLE_TICS}", f"warp {x} {y}", f"wait {SETTLE_TICS}",
             view, f"wait {SETTLE_TICS}"]
    for text in shot.get("setup", ()):
        cmds += action_commands(text, names)
    cmds += [f"wait {SPAWN_SETTLE_TICS}", view, f"wait {SETTLE_TICS}"]
    return cmds


def roll_commands(shot: dict, names: list[str]) -> list[str]:
    cmds = ["netevent sdroll"]
    for text in shot["actions"]:
        cmds += action_commands(text, names)
    return cmds


def roll_tics(shot: dict) -> int:
    """How long the shot runs after the roll, in tics (the actions' own)."""
    return sum(action_tics(a) for a in shot["actions"])


def shot_commands(shot: dict, names: list[str]) -> list[str]:
    return setup_commands(shot, names) + roll_commands(shot, names) + [f"wait {QUIT_TICS}", "quit"]


def console_sequence(shot: dict, names: list[str]) -> str:
    text = "+" + "; ".join(shot_commands(shot, names))
    if len(text) > route.MAX_SEQUENCE_CHARS:
        raise TrailerError(f"shot {shot['id']}: console sequence is {len(text)} chars, "
                           f"over {route.MAX_SEQUENCE_CHARS}")
    return text


def sequence_seconds(shot: dict, names: list[str]) -> float:
    return sum(int(c.split()[1]) for c in shot_commands(shot, names)
               if c.startswith("wait ")) / TICS_PER_SECOND


# The cvars every trailer run sets, both ways (the trailer config keeps what
# the last run set). Names from GZDoom g4.14.2; the ones marked (?) are NOT
# VERIFIED in a run: an unknown one prints a console line and changes nothing.
VIEW_CVARS = (
    ("vid_fullscreen", "0"), ("i_pauseinbackground", "0"), ("i_soundinbackground", "1"),
    ("screenblocks", "12"),          # no status bar, no HUD: the weapon stays (r_drawplayersprites)
    ("r_drawplayersprites", "1"), ("crosshair", "0"), ("show_messages", "0"),
    ("con_notifytime", "0"),         # (?) no notify lines over the picture
    ("use_mouse", "0"),              # (?) a nudge of the CEO's mouse must not turn the camera
    ("freelook", "1"), ("lookspring", "0"),
    ("vid_scalemode", "0"), ("vid_scalefactor", "1"),
    ("snd_musicvolume", "0"),        # the trailer's music is the render, not the game's
)


def engine_argv(gzdoom: Path, iwad: Path, pk3s: list[Path], helper: Path, config: Path,
                log: Path, shot: dict, names: list[str], window: tuple[int, int],
                sound: bool) -> list[str]:
    argv = [str(gzdoom), "-config", str(config), "-iwad", str(iwad), "-file"]
    argv += [str(p) for p in pk3s] + [str(helper)]
    argv += ["+logfile", str(log), "-skill", str(shot.get("skill", 3)), "+map", shot["map"]]
    if not sound:
        argv.append("-nosound")
    if shot.get("nomonsters"):
        argv.append("-nomonsters")
    argv += ["+win_w", str(window[0]), "+win_h", str(window[1])]
    for name, value in VIEW_CVARS:
        argv += [f"+{name}", value]
    argv.append(console_sequence(shot, names))
    return argv


# ============================================================================
# The helper PK3: route.py's proven handler plus the trailer's camera
# ============================================================================

TRAILER_CLASS = "SDTrailerHelper"
SLATE_RGB = (255, 0, 255)


def trailer_zscript(names: list[str]) -> str:
    quoted = ", ".join(f'"{n}"' for n in names) or '"Actor"'
    return f"""
// GENERATED by tools/trailer/trailer_lib.py - trailer tooling, NEVER part of the mod.
//   netevent sdroll                 lift the slate: the shot's time zero
//   netevent sdslate                put the slate back
//   netevent sdview <yaw> <pitch>   set the view (degrees; pitch > 0 looks down) and stop the body
//   netevent sdpan <deg> <tics>     turn by <deg> over <tics>, interpolated (> 0 turns left)
//   netevent sdtilt <deg> <tics>    pitch by <deg> over <tics> (> 0 looks down)
//   netevent sdspawn <i> <dist> <side>  spawn NAMES[i] <dist> ahead, <side> degrees off the view,
//                                   facing and hunting the player
//   netevent sdthurt <i> <amount>   damage every live NAMES[i]
//   netevent sdcalm <radius>        remove (no corpse) every live monster but the bosses within
//                                   <radius> of the player: nothing of the map's in the lens
//   sdspawn's 4th arg 1: the actor holds its ground (STANDSTILL) and fights from there
class {TRAILER_CLASS} : EventHandler
{{
    static const string NAMES[] = {{ {quoted} }};
    bool slate;
    double panRate, tiltRate;
    int panLeft, tiltLeft;

    override void WorldLoaded(WorldEvent e)
    {{
        slate = true;
        Console.Printf("SDTRAILER helper map=%s", level.MapName);
    }}

    override void WorldTick()
    {{
        if (!playeringame[0] || !players[0].mo) return;
        let pmo = players[0].mo;
        if (panLeft > 0) {{ pmo.A_SetAngle(pmo.angle + panRate, SPF_INTERPOLATE); panLeft--; }}
        if (tiltLeft > 0) {{ pmo.A_SetPitch(pmo.pitch + tiltRate, SPF_INTERPOLATE); tiltLeft--; }}
    }}

    override void RenderOverlay(RenderEvent e)
    {{
        if (slate) Screen.Clear(0, 0, Screen.GetWidth(), Screen.GetHeight(), Color(255, {SLATE_RGB[0]}, {SLATE_RGB[1]}, {SLATE_RGB[2]}));
    }}

    override void NetworkProcess(ConsoleEvent e)
    {{
        if (e.Name == "sdroll") {{ slate = false; Console.Printf("SDTRAILER roll tic=%d", level.maptime); return; }}
        if (e.Name == "sdslate") {{ slate = true; return; }}
        let pmo = players[e.Player].mo;
        if (!pmo) return;
        if (e.Name == "sdview")
        {{
            pmo.angle = e.Args[0]; pmo.pitch = e.Args[1];
            pmo.Vel = (0, 0, 0); players[e.Player].vel = (0, 0);
            panLeft = 0; tiltLeft = 0;
            return;
        }}
        if (e.Name == "sdpan") {{ panRate = double(e.Args[0]) / e.Args[1]; panLeft = e.Args[1]; return; }}
        if (e.Name == "sdtilt") {{ tiltRate = double(e.Args[0]) / e.Args[1]; tiltLeft = e.Args[1]; return; }}
        if (e.Name == "sdspawn")
        {{
            // The class by name, as route.py's sdhurt hands NAMES[i] to
            // ThinkerIterator.Create (proven in engine): no class<> variable.
            Vector2 p = pmo.Vec2Angle(e.Args[1], pmo.angle + e.Args[2]);
            let a = Actor.Spawn(NAMES[e.Args[0]], (p.x, p.y, pmo.floorz));
            if (!a) {{ Console.Printf("SDTRAILER spawn class=%s ok=0 why=noclass", NAMES[e.Args[0]]); return; }}
            a.SetOrigin((p.x, p.y, a.floorz), false);
            if (!a.TestMobjLocation())
            {{
                Console.Printf("SDTRAILER spawn class=%s ok=0 x=%d y=%d why=blocked", NAMES[e.Args[0]], int(p.x), int(p.y));
                a.Destroy();
                return;
            }}
            a.angle = a.AngleTo(pmo);
            a.target = pmo;
            if (e.Args[3]) a.bSTANDSTILL = true;
            if (a.SeeState) a.SetState(a.SeeState);
            Console.Printf("SDTRAILER spawn class=%s ok=1 x=%d y=%d", NAMES[e.Args[0]], int(p.x), int(p.y));
            return;
        }}
        if (e.Name == "sdcalm")
        {{
            let it = ThinkerIterator.Create("Actor");
            Actor a; int n = 0;
            while ((a = Actor(it.Next())) != null)
            {{
                if (!a.bIsMonster || a.health <= 0 || a.player) continue;
                if (a is "SD_General" || a is "SD_LibertyColossus" || a is "SD_Consortium") continue;
                if (a.Distance2D(pmo) > e.Args[0]) continue;
                a.Destroy();
                n++;
            }}
            Console.Printf("SDTRAILER calm radius=%d removed=%d", e.Args[0], n);
            return;
        }}
        if (e.Name == "sdthurt")
        {{
            let it = ThinkerIterator.Create(NAMES[e.Args[0]]);
            Actor a; int n = 0;
            while ((a = Actor(it.Next())) != null)
                if (a.health > 0) {{ a.DamageMobj(pmo, pmo, e.Args[1], 'None'); n++; }}
            Console.Printf("SDTRAILER hurt %s x%d by %d", NAMES[e.Args[0]], n, e.Args[1]);
            return;
        }}
    }}
}}
"""


def helper_mapinfo() -> str:
    return (f'gameinfo\n{{\n    AddEventHandlers = "{route.HELPER_CLASS}", "{route.STATE_CLASS}", '
            f'"{TRAILER_CLASS}"\n}}\n')


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_helper_pk3(names: list[str], out: Path = HELPER_PK3) -> Path:
    """route.py's helper (sdstop, sdexit, sdpos...) plus the trailer camera, in
    one PK3 under work/trailer/ (gitignored). Refuses any place the mod is
    built or shipped from."""
    for root in FORBIDDEN_HELPER_ROOTS:
        if _inside(out, root):
            raise TrailerError(f"refusing to write the trailer helper into {root}")
    out.parent.mkdir(parents=True, exist_ok=True)
    text = route.helper_zscript() + trailer_zscript(names)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, body in (("zscript.txt", text), ("MAPINFO", helper_mapinfo())):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, body)
    return out


_CLASS_DECL = re.compile(r"^\s*class\s+(\w+)", re.M | re.I)


def pk3_classes(pk3s: list[Path]) -> set[str]:
    """Every ZScript class declared in the packages (to tell a V3 PK3 from a v1.2 one)."""
    found: set[str] = set()
    for pk3 in pk3s:
        with zipfile.ZipFile(pk3) as zf:
            for name in zf.namelist():
                if name.lower().endswith((".zs", ".zsc")) or name.lower().startswith("zscript"):
                    text = zf.read(name).decode("utf-8", "replace")
                    found.update(_CLASS_DECL.findall(text))
    return found


# ============================================================================
# Map geometry: does the camera fit, does it see its subject
# ============================================================================

class MapGeometry:
    """The built map (route.MapData) as segments, for the shot checks."""

    def __init__(self, map_name: str):
        self.md = route.load_map_data(map_name)
        tm = self.md.textmap
        self.sectors = tm.sectors
        self.segs = []
        for ld in tm.linedefs:
            a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
            front = tm.sidedefs[ld.sidefront].sector
            back = tm.sidedefs[ld.sideback].sector if ld.sideback is not None else None
            self.segs.append((a.x, a.y, b.x, b.y, front, back, ld))

    def sector(self, x: float, y: float) -> int | None:
        return self.md.sector_at(x, y)

    def name(self, sector: int | None) -> str | None:
        return self.md.name_of(sector)

    def floor(self, x: float, y: float) -> int | None:
        s = self.sector(x, y)
        return None if s is None else self.sectors[s].heightfloor

    def fits(self, x: float, y: float, radius: int = PLAYER_RADIUS,
             height: int = PLAYER_HEIGHT) -> str | None:
        """None if a body of this size can stand here (Doom's box test,
        simplified: no one-sided line through the box, and the highest floor
        and lowest ceiling under it leave room); else why not."""
        s = self.sector(x, y)
        if s is None:
            return "outside the map"
        sec = self.sectors[s]
        floor, ceil = sec.heightfloor, sec.heightceiling
        x1, y1, x2, y2 = x - radius, y - radius, x + radius, y + radius
        for ax, ay, bx, by, front, back, _ in self.segs:
            if not _seg_box(ax, ay, bx, by, x1, y1, x2, y2):
                continue
            if back is None:
                return f"a wall within {radius} units"
            for side in (front, back):
                floor = max(floor, self.sectors[side].heightfloor)
                ceil = min(ceil, self.sectors[side].heightceiling)
        if ceil - floor < height:
            return f"{ceil - floor} units of headroom, needs {height}"
        return None

    def sight(self, a: tuple[float, float], b: tuple[float, float],
              a_height: float = EYE_HEIGHT, b_height: float = 32.0) -> str | None:
        """None if the eye at `a` sees a point `b_height` over the floor at `b`
        (2D crossing of every line, with the floor and ceiling at the
        crossing); else what blocks it."""
        fa, fb = self.floor(*a), self.floor(*b)
        if fa is None or fb is None:
            return "an end is outside the map"
        za, zb = fa + a_height, fb + b_height
        for ax, ay, bx, by, front, back, _ in self.segs:
            t = _crossing(a, b, (ax, ay), (bx, by))
            if t is None:
                continue
            if back is None:
                return f"a wall at {_lerp2(a, b, t)}"
            z = za + (zb - za) * t
            lo = max(self.sectors[front].heightfloor, self.sectors[back].heightfloor)
            hi = min(self.sectors[front].heightceiling, self.sectors[back].heightceiling)
            if not lo < z < hi:
                return f"an opening {lo}..{hi} at {_lerp2(a, b, t)} (sight line at {z:.0f})"
        return None


def _lerp2(a, b, t):
    return (round(a[0] + (b[0] - a[0]) * t), round(a[1] + (b[1] - a[1]) * t))


def _crossing(p, q, r, s) -> float | None:
    """t on p->q where it properly crosses segment r-s, or None."""
    d1x, d1y = q[0] - p[0], q[1] - p[1]
    d2x, d2y = s[0] - r[0], s[1] - r[1]
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-12:
        return None
    t = ((r[0] - p[0]) * d2y - (r[1] - p[1]) * d2x) / den
    u = ((r[0] - p[0]) * d1y - (r[1] - p[1]) * d1x) / den
    if 0.0 < t < 1.0 and 0.0 <= u <= 1.0:
        return t
    return None


def _seg_box(ax, ay, bx, by, x1, y1, x2, y2) -> bool:
    """Does segment a-b touch the open box (x1,y1)-(x2,y2)?"""
    if max(ax, bx) <= x1 or min(ax, bx) >= x2 or max(ay, by) <= y1 or min(ay, by) >= y2:
        return False
    if x1 < ax < x2 and y1 < ay < y2:
        return True
    edges = (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1)))
    for r, s in edges:
        if _crossing((ax, ay), (bx, by), r, s) is not None:
            return True
    # an axis-aligned segment lying inside the box
    return x1 < (ax + bx) / 2 < x2 and y1 < (ay + by) / 2 < y2


def spawn_point(warp, angle: float, dist: float, side: float = 0.0) -> tuple[float, float]:
    """Where the helper's sdspawn puts an actor (pmo.Vec2Angle)."""
    a = math.radians(angle + side)
    return (warp[0] + dist * math.cos(a), warp[1] + dist * math.sin(a))


def facing(a: tuple[float, float], b: tuple[float, float]) -> int:
    return round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 360


def angle_off(view: float, a, b) -> float:
    """How far `b` is from the centre of a view at `a` facing `view`, degrees."""
    d = (facing(a, b) - view + 180) % 360 - 180
    return abs(d)


H_FOV = 90.0             # GZDoom's default fov (horizontal, 4:3); wider at 16:9


MIN_CLEAR = 192          # nothing of the map's, and no spawn, nearer the lens than this (PM, 2026-10-25)
CONE_CLEAR = 384         # nor inside the view this near
CONE_HALF = 50.0         # degrees either side of the view's centre (16:9 at fov 90)
WALK_UNITS_PER_TIC = 8   # route.WALK_UNITS_PER_TIC: +forward with cl_run 0
BOSS_EDNUMS = frozenset({21106, 21111, 21112, 21113, 16, 7})
MONSTER_RANGE = range(21100, 21200)


def _is_monster(ednum: int) -> bool:
    return ednum in route.MONSTER_EDNUMS or ednum in MONSTER_RANGE


def camera_path(v: dict) -> list[tuple[float, float]]:
    """Where the lens stands during the shot: the warp, and the end of each
    walk (straight along the start's facing: an upper bound for a pan)."""
    pts = [tuple(v["warp"])]
    x, y = v["warp"]
    for text in v.get("actions", ()):
        word, args = parse_action(text)
        step = {"forward": 1, "back": -1}.get(word)
        if step:
            d = step * int(args[0]) * WALK_UNITS_PER_TIC
            x += d * math.cos(math.radians(v["angle"]))
            y += d * math.sin(math.radians(v["angle"]))
            pts.append((x, y))
    return pts


def clearance(v: dict, geo: "MapGeometry", sid: str) -> list[str]:
    """The PM's first cut (2026-10-25): a Panzermensch 32 units from the Red
    Square camera and a doughboy 86 units in front of Severomorsk's filled
    half the frame. No monster of the map, on the shot's skill, may stand
    within MIN_CLEAR of the lens, or within CONE_CLEAR inside the view,
    unless the shot's `calm R` removes it (bosses are never removed)."""
    calm = 0
    for text in v.get("setup", ()):
        word, args = parse_action(text)
        if word == "calm":
            calm = max(calm, int(args[0]))
    skill = int(v.get("skill", 3))
    errs = []
    path = camera_path(v)
    for t in geo.md.textmap.things:
        if not _is_monster(t.type) or not getattr(t, f"skill{skill}", True):
            continue
        boss = t.type in BOSS_EDNUMS
        if not boss and math.hypot(t.x - path[0][0], t.y - path[0][1]) <= calm:
            continue
        if v.get("nomonsters") and not boss:
            continue
        for p in path:
            d = math.hypot(t.x - p[0], t.y - p[1])
            in_cone = d < CONE_CLEAR and angle_off(v["angle"], p, (t.x, t.y)) < CONE_HALF
            if d < MIN_CLEAR or (in_cone and not boss):     # a boss is the subject: in view, not on the lens
                errs.append(f"{sid}: thing {t.type} at ({t.x:.0f}, {t.y:.0f}) is {d:.0f} units from the lens"
                            + ("" if boss else f" (calm {calm} does not reach it)"))
                break
    return errs


def check_geometry(data: dict) -> list[str]:
    """Each engine shot (and its fallback) against its built map: the camera
    fits; every spawn lands where its body fits and in sight of the camera;
    the `look_at` subject is in sight and inside the view."""
    errs: list[str] = []
    geos: dict[str, MapGeometry] = {}
    for s in data["shots"]:
        if s.get("kind", "engine") != "engine":
            continue
        variants = [s] + ([dict(s, **s["fallback"])] if s.get("fallback") else [])
        for v in variants:
            sid = v["id"] + (" (fallback)" if v is not s else "")
            geo = geos.setdefault(v["map"], MapGeometry(v["map"]))
            warp = tuple(v["warp"])
            why = geo.fits(*warp)
            if why:
                errs.append(f"{sid}: camera at {warp} on {v['map']}: {why}")
                continue
            for text in list(v.get("setup", ())) + list(v.get("actions", ())):
                word, args = parse_action(text)
                if word != "spawn":
                    continue
                side = int(args[2]) if len(args) >= 3 else 0
                if int(args[1]) < MIN_CLEAR:
                    errs.append(f"{sid}: {text!r} is closer than {MIN_CLEAR} units")
                p = spawn_point(warp, v["angle"], int(args[1]), side)
                r, h = ACTOR_SIZE[args[0]]
                why = geo.fits(*p, radius=r, height=h)
                if why:
                    errs.append(f"{sid}: {text!r} lands at {tuple(round(c) for c in p)}: {why}")
                    continue
                why = geo.sight(warp, p, b_height=h / 2)
                if why:
                    errs.append(f"{sid}: {text!r} out of sight: {why}")
            look = v.get("look_at")
            if look:
                why = geo.sight(warp, tuple(look), b_height=float(v.get("look_height", 48)))
                if why:
                    errs.append(f"{sid}: look_at {look} out of sight: {why}")
                if angle_off(v["angle"], warp, look) > H_FOV / 2:
                    errs.append(f"{sid}: look_at {look} is outside the {H_FOV:.0f} degree view")
            errs += clearance(v, geo, sid)
            things = v.get("subject_thing")
            if things:
                ed, x, y = things
                if not any(t.type == ed and t.x == x and t.y == y for t in geo.md.textmap.things):
                    errs.append(f"{sid}: no thing {ed} at ({x}, {y}) on {v['map']}")
    return errs


# ============================================================================
# Cards: the texts, in the game's own bitmap font
# ============================================================================

def language_strings(path: Path = LANGUAGE_PATH) -> dict[str, dict[str, str]]:
    """{locale: {id: text}} from the LANGUAGE lump (only `ID = "text";` lines)."""
    text = path.read_text(encoding="utf-8")
    out: dict[str, dict[str, str]] = {loc: {} for loc in LOCALES}
    section = None
    for line in text.splitlines():
        m = re.match(r"^\s*\[([^\]]+)\]", line)
        if m:
            heads = m.group(1).strip()
            section = next((loc for loc, h in LANGUAGE_SECTIONS.items() if heads == h), None)
            continue
        if section is None:
            continue
        m = re.match(r'^\s*([A-Z0-9_]+)\s*=\s*"(.*)"\s*;', line)
        if m:
            out[section][m.group(1)] = m.group(2)
    return out


def card_lines(card: dict, locale: str, strings: dict[str, dict[str, str]] | None = None) -> list[str]:
    """A card's lines in one locale. A line may be {"lang": ID} (read from
    LANGUAGE, so map names stay the game's) or {"text": "..."}; "{version}"
    is filled in by edit.py."""
    lines = card[locale] if locale in card else card.get("all")
    if lines is None:
        raise TrailerError(f"card has no {locale!r} text")
    out = []
    for ln in lines:
        if isinstance(ln, dict) and "lang" in ln:
            strings = strings if strings is not None else language_strings()
            if ln["lang"] not in strings[locale]:
                raise TrailerError(f"{ln['lang']} missing from LANGUAGE [{locale}]")
            out.append(strings[locale][ln["lang"]])
        else:
            out.append(str(ln))
    return out


def font_glyphs(font: str) -> set[str]:
    d = FONTS_DIR / font
    return {chr(int(p.stem, 16)) for p in d.glob("*.png") if re.fullmatch(r"[0-9A-Fa-f]{4}", p.stem)}


def missing_glyphs(text: str, font: str) -> set[str]:
    have = font_glyphs(font)
    return {ch for ch in text.upper() if ch not in have}
