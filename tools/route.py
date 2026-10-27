#!/usr/bin/env python3
"""Scripted G3 route runs: walk a map's critical path in GZDoom by console.

`tools/smoke.py` proves the mod LOADS. This tool proves a map can be
FINISHED along its critical path, once per skill, and says where it broke if
it cannot: it warps the player in front of each door or switch, turns him,
presses use, walks through with `+forward`, and asks a throwaway helper
where he ended up. A door that did not open leaves him on the wrong side,
and the report says so. It is the automated half of criterion G3-4 (and,
with --nomonsters or a route that takes no secret, of G3-5) in
`docs/levels/MAP01-zarya-7.md` section 11; the routes are the "automatic run"
of section 17.10 of the same document.

What it does, per skill:
  1. builds the mod (tools/build.py) unless --no-build;
  2. writes its OWN helper PK3 into logs/route/ (gitignored): a ZScript
     EventHandler that sets the view angle, damages and counts actors, and
     reports position, door tags, line activations, secrets and the level's
     end. The helper is tooling: it never enters src/, dist/ or the mod PK3
     (tests/test_route.py enforces it);
  3. launches GZDoom through `smoke.run_engine`, the project's single gated
     launcher (D26: it refuses unless SD_ALLOW_ENGINE=1), with smoke's
     tooling `-config`, never the user's gzdoom.ini;
  4. reads the log with smoke's failure contract plus the two G3-2 patterns
     smoke does not carry, and the SDTEST lines the helper prints;
  5. prints a report: zones reached per step, secrets, doors opened, exit
     reached (intermission), the start inventory and the weapons picked up,
     errors, and a verdict.

The start inventory (commit 63dac93, design section 17.14): the player
spawns with the TT-33 raised and its 50 rounds, slot 1 EMPTY, and finds the
melee weapon on the dorm's rack. The route checks it by weapon SLOT, never by
class name, and finds the rack by DoomEdNum 21001 (MOD-SPEC 6.1), because the
class has been renamed once already (the shovel became the ice axe, D40) and
the zone with it (`z1_ice_axe_rack`, f3cd8ea): step A0 asserts
"slot 1 empty, ready weapon in slot 2, 50 rounds", step R1 walks into the
rack and asserts "a slot-1 weapon is owned".

Blockers (the PM's first run, 2026-10-13 20:36: skills 3 and 4 failed at A1
because a live Stormtrooper stood in the corridor, and a scripted walk cannot
step round a body). Before every `+forward` the helper's `sdclear` kills
the live monsters within CLEAR_HALF_WIDTH of the walk's line, and names
each one. The report lists them under "blockers", counts them apart under
"kills", and says so on the VERDICT line: a body in the way is reported,
never hidden. A blocker that survives fails the run. --no-clear turns it
off.

Ending a level: a built-in route ends its map by PRESSING the exit switch,
as a player does. MAP01's is G3-4's. RANGE's arrived with d1e891f: an
Exit_Normal switch in a lit alcove behind the start, the line x -32 from
y 352 to 416 (docs/levels/RANGE-practice-range.md section 4.1, P6 of its
section 7); range-start walks west into the alcove and presses it. The
helper's `sdexit` (Level.ExitLevel) stays as a documented recourse for a
map with no exit line: a JSON route with "exit_by": "console" uses it, no
built-in route does, and a switch route ended by sdexit fails. The console
`exit` QUITS GZDoom (PM, 2026-10-13 20:39) and is never typed.

Where the exit leads is read from MAPINFO's `next` for the map, never written
here (exit_expectation): since D60 (9fd800a) MAP01 leads to the metro, the
metro to the factory since D62, and only the map that ends the episode (the
factory) and the practice range (its own end text) say `next = endtitle`,
which the report checks as an end sequence. Map names are not written here
either: D62 (2026-10-14) renumbered the slots (the metro MAP03 -> MAP02, the
factory MAP04 -> MAP03, the range MAP02 -> RANGE), and each route finds its
map by the named constants its map.py defines (map_defining, ZARYA_MARKERS,
RANGE_MARKERS, METRO_CONSTANTS), so nothing here moved with them. The route
NAMES did: range-start, range-door and metro-critical were map02-start,
map02-door and map03-critical, the names the dated evidence of 2026-10-13
and 2026-10-14 carries.

MAP02, the metro-bunker (docs/levels/MAP02-metro.md sections 5 and 14.5):
`metro-critical` is MAP02's g3-auto. Start; the blue blast door pressed
WITHOUT the pass (it must stay shut, and the press must be seen); the pass
picked up by WALKING onto it (never `give`); the blast door pressed again and
walked through; SW-A (the shutter opens, the gate stays shut); SW-B (the
gate opens); through the gate to the exit switch, pressed. Nothing in it is a
copied coordinate: tags, specials and the pass's editor number come from the
named constants of src/maps/MAP02/map.py, every position from the built map
(the pass by DoomEdNum, the switches and doors by special and tag, the gate
by the ray from the exit line), so the route follows the map when v1 moves
things. The route is built when first asked for (route_by_name), so a MAP02
caught mid-edit cannot break MAP01's routes. The pass is checked by KEY,
never by class (SD_BluePass replaces BlueCard and may be renamed): sdinv
reports every Key in the inventory since route-4.

MAP03, Tankograd (docs/levels/MAP03-factory.md sections 5 and 15):
`tankograd-critical` is the factory's g3-auto, metro-critical's method with
two keys. Start; the yellow door (lock 3) and the red door (lock 1) pressed
with no key, both must stay shut; the yellow key (DoomEdNum 6) walked onto,
the yellow door opened and walked through; the red door pressed with the
yellow key alone, still shut; the red key (DoomEdNum 13) walked onto, the red
door opened and walked through; SW-A (the shutter and the hall's closets);
SW-B (the drum's gate); up the dais to the breaker, pressed. The keys are
Doom's YellowCard and RedCard (no SD_ class yet): the route counts keys by
the Key base class (Step.keys: 0, 1, 2) and lets the doors say which is
which. MAPINFO says `next = endtitle` for the factory, so its exit must lead
to an end sequence: the episode's end. Built lazily from the map, like the
metro's.

Usage (the PM's; D26: only the PM sets SD_ALLOW_ENGINE, and on Windows the
interpreter is .venv/Scripts/python.exe):
  SD_ALLOW_ENGINE=1 python3 tools/route.py                       # g3-auto, skills 2 3 4
  SD_ALLOW_ENGINE=1 python3 tools/route.py --skills 4 --keep-evidence   # one skill, filed
  SD_ALLOW_ENGINE=1 python3 tools/route.py --route g3-secrets --skills 3
  SD_ALLOW_ENGINE=1 python3 tools/route.py --nomonsters --skills 3
  SD_ALLOW_ENGINE=1 python3 tools/route.py --keep-evidence      # also file into docs/qa/evidence/
  python3 tools/route.py --print                                # sequence + argv, no engine
  python3 tools/route.py --parse logs/route/<run>/gzdoom.log --skill 3   # re-read a log
  python3 tools/route.py --scan logs/gzdoom.log                 # G3-2 on a hand-played run
  SD_ALLOW_ENGINE=1 python3 tools/route.py --route mural --skills 3 --nomonsters --keep-evidence
  SD_ALLOW_ENGINE=1 python3 tools/route.py --route range-door --skills 3 --keep-evidence  # RANGE's P4
  SD_ALLOW_ENGINE=1 python3 tools/route.py --route metro-critical --keep-evidence  # MAP02, skills 2 3 4
  SD_ALLOW_ENGINE=1 python3 tools/route.py --route tankograd-critical --keep-evidence  # MAP03, 2 3 4
  python3 tools/route.py --steps my_route.json --print          # a route of your own
  python3 tools/route.py --list-routes

Exit codes: smoke's (1 log failures, 2 no gzdoom, 3 no IWAD, 4 build,
5 timeout, 6 engine exit status), plus
  8  the engine gate is shut (SD_ALLOW_ENGINE is not 1): nothing was launched
  9  the log is clean but the route failed (wrong zone, door shut, no exit)

VERIFIED by the PM's runs (D26: this role does not start the engine):
  route-1, 2026-10-13 20:36: the helper compiles; position, tags, lines,
    inventory, the exit line and the unload print as parsed here;
  route-2, 20:50-20:52 (docs/qa/evidence/2026-10-13_2050_* and _2051_*,
    _2052_*): sdclear kills and names the blockers (6, 10 and 13 on skills
    2, 3 and 4), and sdexit ended RANGE towards its end sequence;
  route-2 again, 21:14-21:17 on 87d613b: range-start leaves RANGE by its
    exit switch (E0, E1), and range-door's P4 opens the gallery door from
    the passage side. range-door failed at E0 only: the warp kept P4b's
    velocity (see warp_commands, the route-3 fix).
NOT SEEN in any run: the static SDRouteState's answer to sdstate after the
level has ended (zero such lines, even for the one asked during RANGE's
end text). Inside a level it does answer (gamestate=0, range-door at
21:15, whose level never ended). Hypothesis, NOT VERIFIED, and supported by
that: GZDoom's `netevent` console command is refused outside a level.
Nothing is judged on it: the unload line names the end sequence, and the
END screenshot shows the screen.
NOT VERIFIED until the PM's next run: route-3's sdstop and the velocity
reset in sdangle (Actor.Vel and PlayerInfo.vel, read in g4.14.2's
gzdoom.pk3 on 2026-10-13). route-4's key lines in sdinv (`item is "Key"`,
the base class of every Doom key in gzdoom.pk3's zscript). That a press on
a LOCKED line still prints its SDTEST line when the key is missing
(hypothesis from memory of GZDoom's P_ActivateLine: WorldLinePreActivated
runs before the special, and Door_LockedRaise checks the lock inside the
special); a step that needs the press also accepts the engine's lock
message ("You need a blue pass...") at that step, should either be absent. Whether a `warp` onto a pickup collects it
is still unknown; no step relies on it (each walks onto its pickup).
Every
ZScript name it uses was checked against the declarations in GZDoom
g4.14.2's own gzdoom.pk3 (zscript/events.zs, doombase.zs, mapdata.zs,
engine/base.zs) on 2026-10-13; the angle, damage and count commands are the
PM's, proven in engine the same day. If the extras fail to compile, the
log shows a "Script error" naming the helper and --minimal-helper runs the
proven part alone.

Python 3 standard library only (plus the map's own source for map data).
"""

from __future__ import annotations

import argparse
import functools
import json
import math
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import smoke  # noqa: E402  (the gate, the engine discovery and the failure contract)

PROJECT_ROOT = smoke.PROJECT_ROOT

# --- Exit codes (smoke's, plus two of our own) ------------------------------
EXIT_OK = smoke.EXIT_OK
EXIT_LOG_FAILURES = smoke.EXIT_LOG_FAILURES
EXIT_TIMEOUT = smoke.EXIT_TIMEOUT
EXIT_ENGINE_FAILED = smoke.EXIT_ENGINE_FAILED
EXIT_BLOCKED = 8
EXIT_ROUTE_FAILED = 9

# --- Where things go ----------------------------------------------------------
# Everything this tool writes lives under logs/ (gitignored) unless
# --keep-evidence files a copy under docs/qa/evidence/.
ROUTE_DIR = PROJECT_ROOT / "logs" / "route"
HELPER_PK3 = ROUTE_DIR / "sdroute-helper.pk3"
EVIDENCE_DIR = smoke.EVIDENCE_DIR
DEFAULT_PHASE = "F3"
# The helper must never land where the mod is built from or shipped from.
FORBIDDEN_HELPER_ROOTS = (PROJECT_ROOT / "dist", PROJECT_ROOT / "src", PROJECT_ROOT / "assets")

# --- Engine timing (tics; GZDoom runs at 35 per second) ---------------------
TICS_PER_SECOND = smoke.TICS_PER_SECOND
LOAD_TICS = smoke.DEFAULT_WAIT_TICS   # the map is drawn before the first command
SETTLE_TICS = 3          # after a warp, a turn or a netevent, before the next act
USE_HOLD_TICS = 2        # +use is held this long, then released
SHOT_SETTLE_TICS = 3     # a screenshot is taken on the next frame: let it happen
INTERMISSION_TICS = 70   # after the exit switch, before the intermission shot
QUIT_SETTLE_TICS = 35    # after the last shot, so the PNG is flushed
TIMEOUT_MARGIN_S = 90.0  # engine start-up and shutdown on top of the route's tics
WALK_UNITS_PER_TIC = 8   # +forward with cl_run 0, an upper estimate (Doom walks ~8.3)
CLEAR_HALF_WIDTH = 128   # sdclear: how far either side of a walk a body counts as in the way
END_TEXT_TICS = 280      # an end text types itself out; RANGE's 74 characters fit well inside
# One argv element carries the whole sequence. Windows caps a command line at
# 32767 characters; we stay far below it. NOT VERIFIED: any shorter limit in
# GZDoom's own console buffer (the PM's hand runs used a few hundred chars).
MAX_SEQUENCE_CHARS = 8000

# --- What the helper knows how to count and hurt ----------------------------
# The PM's list, proven in engine on 2026-10-13 (MAP01 and RANGE). The index
# of a class here is the first argument of `netevent sdhurt`.
COUNT_CLASSES = (
    "SD_ReichRifleman", "SD_LegionTrooper", "SD_Stormtrooper", "SD_ReichHound",
    "SD_Doughboy", "SD_Panzermensch", "SD_PanzermenschSchwer", "SD_General",
    "SD_Clip", "SD_Izh",
    # D116: the P4 enemies, in the mod on provisional sprites, so a route can
    # hurt MAP06's and MAP09's bosses once level-designer places them.
    # Appended: the indices above (netevent sdhurt) do not move.
    "SD_LegionGunner", "SD_LibertyColossus", "SD_Consortium", "SD_AkmAmmo",
    # D123: the colossus variant, MAP08's mini-boss on skills 3-4 (appended).
    "SD_ChromeGeneral",
)
HELPER_CLASS = "SDRouteHelper"
HELPER_VERSION = "route-4"   # route-4: sdinv also names the keys owned (MAP02's pass)

# Monsters as the map places them (DoomEdNums of the Freedoom stand-ins our
# bestiary replaces, docs/levels/MAP01-zarya-7.md section 8). Used to say how
# many monsters the engine should spawn on each skill.
# Plus the Doom numbers of the two the episode has not placed yet (16, 3003)
# and our own numbers (MOD-SPEC 6.1: 21100-21107; RANGE's gallery uses
# them), so the count holds on any map. D116 adds the P4 enemies: Doom's
# chaingunner (65) and Spider Mastermind (7), which they replace, and
# 21110-21112; D123 the Chrome Marshal, 21113 (MAP08's bay on skills 3-4).
MONSTER_EDNUMS = frozenset({3004, 9, 3001, 3002, 3005, 69, 16, 3003, 65, 7}
                           | set(range(21100, 21108)) | {21110, 21111, 21112, 21113})
SECTOR_SPECIAL_SECRET = 1024     # udmf.SECTOR_SPECIAL_SECRET
SPECIAL_EXIT_NORMAL = 243        # udmf.SPECIAL_EXIT_NORMAL
GS_INTERMISSION = 1              # EGameState in GZDoom's zscript/engine/base.zs
GS_FINALE = 2                    # the same enum: an end text (a cluster's exittext)
GS_NAMES = {GS_INTERMISSION: "intermission", GS_FINALE: "end text"}
END_SEQUENCE_PREFIX = "enDSeQ"   # what GZDoom calls `next = endtitle` and its kin
# What the report says when sdstate goes unanswered after the exit (every
# run so far): not a failure; the END screenshot is the evidence.
AFTER_NOT_SEEN = "NOT SEEN (the helper cannot ask once the level is gone; judge the END shot)"
# A door counts as open when a player fits under it (Doom player height 56).
PLAYER_HEIGHT = 56

# --- The start inventory (63dac93; design section 17.14) --------------------
# Keyed on the slot and the editor number, never on the class: the melee
# weapon has been renamed once (shovel -> ice axe, D40) and may be again.
ED_MELEE = 21001          # MOD-SPEC 6.1 / MAPINFO DoomEdNums: the rack's weapon
SLOT_MELEE = 1            # Player.WeaponSlot 1 in src/zscript/sd/player.zs
SLOT_SIDEARM = 2          # Player.WeaponSlot 2: the TT-33, raised on spawn
PLAYER_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "player.zs"
_START_CLIP = re.compile(r"SD_START_CLIP\s*=\s*(\d+)")


def start_rounds(path: Path = PLAYER_ZS) -> int | None:
    """The player's starting 7.62x25 rounds, read from the actor (the same
    constant tests/test_map01.py reads). None if the constant is gone."""
    try:
        found = _START_CLIP.search(path.read_text(encoding="utf-8"))
    except OSError:
        return None
    return int(found.group(1)) if found else None

# --- The G3-2 patterns smoke's contract does not carry ----------------------
# docs/levels/MAP01-zarya-7.md section 11, G3-2, lists eight patterns. Six are
# covered by smoke.LOG_FAILURE_PATTERNS (script-error, unknown-texture,
# unknown-flat, missing-sprite, unknown-other for "Unknown line special",
# bad-thing for "Bad sector"); these two are not, so route adds them.
G3_EXTRA_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("texture-not-found", r"Texture .* not found", "G3-2: a texture lookup failed"),
    ("not-valid", r"is not a valid", "G3-2: the engine rejected a value"),
)


# ============================================================================
# Routes
# ============================================================================

ACTION_WORDS = ("use", "wait", "forward", "capture", "count", "tag", "angle",
                "hurt", "level", "state", "inv", "exit")
STEP_ID = re.compile(r"[A-Za-z0-9_-]{1,24}")


class RouteError(ValueError):
    """A route that cannot be turned into a console sequence."""


@dataclass(frozen=True)
class Step:
    """One stop on a route.

    `warp` and `angle` put the player somewhere facing somewhere; `actions`
    then run in order (see ACTION_WORDS); `expect` lists the zone families
    (see zone_family) the player may stand in when the step ends; `tags`
    maps a sector tag to whether its doors must be open (True) or shut
    (False) at the end of the step.

    The inventory expectations need an `inv` action in the step: `melee`
    is whether a slot-1 weapon is owned at the end of the step (None: not
    checked); `ready_slot` the slot of the raised weapon; `ready_ammo` the
    rounds in its primary ammo pool; `key` whether any key is owned (by
    the Key base class, never by name: MAP02's pass is SD_BluePass, which
    replaces BlueCard, and may be renamed); `keys` how many keys exactly
    (MAP03 holds two: 0 before the yellow key, 1 after it, 2 after the red;
    counted, never named, for the same reason).

    `presses` lists the (special, arg0) lines the player must be seen
    pressing during the step (the helper's SDTEST line, or the engine's
    lock message): a door that stays shut proves nothing if the press
    never reached it. Needs a `use` action.
    """

    id: str
    warp: tuple[int, int] | None = None
    angle: int | None = None
    actions: tuple[str, ...] = ()
    expect: tuple[str, ...] = ()
    tags: tuple[tuple[int, bool], ...] = ()
    note: str = ""
    melee: bool | None = None
    ready_slot: int | None = None
    ready_ammo: int | None = None
    key: bool | None = None
    presses: tuple[tuple[int, int], ...] = ()
    keys: int | None = None

    def __post_init__(self) -> None:
        if not STEP_ID.fullmatch(self.id):
            raise RouteError(f"step id {self.id!r} must match {STEP_ID.pattern}")
        for action in self.actions:
            parse_action(action)
        for tag, _open in self.tags:
            if not any(parse_action(a)[0] == "tag" and parse_action(a)[1] == (tag,)
                       for a in self.actions):
                raise RouteError(f"step {self.id}: expects tag {tag} but never asks for it")
        if self.checks_inventory and "inv" not in self.actions:
            raise RouteError(f"step {self.id}: expects an inventory but never asks for it")
        if self.presses and "use" not in self.actions:
            raise RouteError(f"step {self.id}: expects a press but never presses")

    @property
    def checks_inventory(self) -> bool:
        return (self.melee, self.ready_slot, self.ready_ammo, self.key, self.keys) \
            != (None, None, None, None, None)


@dataclass(frozen=True)
class Route:
    name: str
    map_name: str
    steps: tuple[Step, ...]
    # None: report the secrets found, expect nothing. "all": every secret
    # sector of the map. An int: exactly that many.
    expect_secrets: int | str | None = None
    must_exit: bool = True
    description: str = ""
    # How the level must end: "switch" (an Exit_Normal line pressed by the
    # player; a console exit does not count) or "console" (the helper's
    # sdexit: the recourse for a map with no exit line. No built-in route
    # uses it since RANGE got its switch, d1e891f; a JSON route may).
    exit_by: str = "switch"
    # The map's MAPINFO says `next = endtitle` (or another end): leaving it
    # must lead to an end sequence (GZDoom names them "enDSeQ" + hex: the
    # PM's MAP01 run of 2026-10-13 20:36 unloaded towards "enDSeQ1dce").
    # Built-in routes take it from MAPINFO (exit_expectation).
    end_sequence: bool = False
    # The map's MAPINFO names a next map: leaving must lead there (compared
    # without case). None: not checked.
    next_map: str | None = None


# --- Where a map's exit leads, and which map is which: from the sources -----
MAPINFO_PATH = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
MAPS_DIR = PROJECT_ROOT / "src" / "maps"
_MAPINFO_COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
_MAPINFO_MAP = re.compile(r"^[ \t]*map[ \t]+(\S+)[^\n{]*\n?\s*\{(.*?)^[ \t]*\}", re.M | re.S | re.I)
_MAPINFO_NEXT = re.compile(r"^\s*next\s*=\s*\"?([^\s\"{]+)", re.M | re.I)


def mapinfo_next(map_name: str, text: str | None = None) -> str | None:
    """The `next` of `map <map_name>` in MAPINFO (quotes dropped), or None."""
    if text is None:
        text = MAPINFO_PATH.read_text(encoding="utf-8")
    text = _MAPINFO_COMMENT.sub("", text)
    for name, body in _MAPINFO_MAP.findall(text):
        if name.upper() == map_name.upper():
            found = _MAPINFO_NEXT.search(body)
            return found.group(1) if found else None
    return None


def exit_expectation(map_name: str, text: str | None = None) -> dict:
    """Route keywords for where leaving `map_name` must lead, per MAPINFO:
    {"end_sequence": True} for `endtitle`, `EndGame {...}` and their kin (a
    next that is not a map), else {"next_map": <that map>}."""
    if text is None:
        text = MAPINFO_PATH.read_text(encoding="utf-8")
    nxt = mapinfo_next(map_name, text)
    if nxt is None:
        raise RouteError(f"MAPINFO has no `next` for {map_name}: cannot say where its exit leads")
    maps = {name.upper() for name, _body in _MAPINFO_MAP.findall(_MAPINFO_COMMENT.sub("", text))}
    if nxt.upper() not in maps and nxt.lower().startswith("end"):
        return {"end_sequence": True, "next_map": None}
    return {"end_sequence": False, "next_map": nxt}


def map_defining(*constants: str, maps_dir: Path = MAPS_DIR) -> str:
    """The one map whose map.py defines every one of `constants` at top level:
    routes find their map by what it is, not by its slot (D62 renumbers)."""
    found = []
    for script in sorted(maps_dir.glob("*/map.py")):
        source = script.read_text(encoding="utf-8")
        if all(re.search(rf"^{re.escape(c)}\s*=", source, re.M) for c in constants):
            found.append(script.parent.name)
    if len(found) != 1:
        raise RouteError(f"want one map defining {', '.join(constants)}, found {found or 'none'}")
    return found[0]


# Zarya-7 (the mural and Lenin are its own) and the practice range (its
# gallery door and weapon row): the constants that say which map is which.
ZARYA_MARKERS = ("MURAL_NICHE", "LENIN")
RANGE_MARKERS = ("TAG_GALLERY_DOOR", "WEAPON_ROW")


def parse_action(text: str) -> tuple[str, tuple]:
    """'wait 70' -> ('wait', (70,)). Raises RouteError on anything else."""
    parts = text.split()
    if not parts or parts[0] not in ACTION_WORDS:
        raise RouteError(f"unknown action {text!r} (known: {', '.join(ACTION_WORDS)})")
    word, rest = parts[0], parts[1:]
    try:
        if word in ("use", "capture", "count", "level", "state", "inv", "exit"):
            if rest:
                raise RouteError(f"{word!r} takes no argument: {text!r}")
            return word, ()
        if word in ("wait", "forward"):
            (tics,) = rest
            value = int(tics)
            if value <= 0:
                raise RouteError(f"{word} needs a positive tic count: {text!r}")
            return word, (value,)
        if word in ("tag", "angle"):
            (value,) = rest
            return word, (int(value),)
        if word == "hurt":
            cls, amount = rest
            if cls not in COUNT_CLASSES:
                raise RouteError(f"hurt: {cls!r} is not in COUNT_CLASSES")
            return word, (cls, int(amount))
    except ValueError as exc:  # wrong arity or not an int
        if isinstance(exc, RouteError):
            raise
        raise RouteError(f"malformed action {text!r}") from exc
    raise RouteError(f"unhandled action {text!r}")  # pragma: no cover


# --- MAP01 Zarya-7: section 17.10 of docs/levels/MAP01-zarya-7.md -----------
# Warp points and facings are the design document's (0 east, 90 north,
# 180 west, 270 south). Doors D4 and D5 are checked by their tags (10, 11:
# docs/levels/MAP01-zarya-7.md section 4) before and after their switch, so
# a door that was already open, or that never opened, is caught either way.
MAP01_TAG_D4 = 10
MAP01_TAG_D5 = 11
# V3 A2 (docs/levels/PICKUP-EVENTS.md; MAP01 design section 20): the IZh's
# pickup opens tag 12 (the hound's closet), the PPSh-41's tag 13 (the squad's).
# Both shut at A0; each checked open steps after its weapon, once the panel
# (2 units a tic, ~1.3 s) is surely up: the IZh's at A6 (after SW-A's wait),
# the PPSh's at A9 (after D6's and SW-B's). tests/test_map01.py holds both
# numbers to the map's TAG_EVENT_IZH and TAG_EVENT_PPSH.
MAP01_TAG_EVENT_IZH = 12
MAP01_TAG_EVENT_PPSH = 13
WALK = 35        # +forward tics through a manual door (section 17.10)
WALK_LONG = 70   # +forward tics across the airlock (section 17.10)
DOOR_WAIT = 70   # a manual door's rise, section 17.10
SWITCH_WAIT = 105
# The rack (design section 17.14): the melee weapon, DoomEdNum ED_MELEE, lies
# at (-16, 384) in a 32-deep alcove (x -32..0, y 352..416, floor 0, the
# dorm's own floor) in the dorm's west wall. R1 warps onto the dorm floor
# due east of it, between the alcove and the first bunk (x 64), faces west
# and walks: the alcove's back wall stops him on top of the weapon, and a
# move, unlike a warp, collects what it touches. tests/test_route.py reads
# the 21001 thing back from the built map and holds this geometry.
MAP01_RACK_APPROACH = (40, 384)
MAP01_RACK_FACING = 180
RACK_WALK = 35   # ~8 units a tic walking: far more than the 56 to the wall
# The two tutorial weapons are WALKED onto as the rack is, never warped onto
# (V3 A2, 2026-10-23). The PM's v3 pass at 12:18 warped onto them (A4 and A7
# warped to the things' own spots): a warp collects nothing, so both steps
# reported "owned [1, 2]" (no IZh, no PPSh), neither pickup ran its special,
# and tags 12 and 13 were still shut at A6 and A9. The map was right; the
# route never took the guns. Now:
# * the IZh (21003 at 1040 1256) lies in a 32-deep steel niche (x 1024..1056,
#   y 1232..1280, floor 8) in the guard post's east wall. A4 warps onto the
#   post's floor on the gun's row (floor 8; 40 east of the radio at 960 1264,
#   whose box and his are 32 wide each; 8 clear of the crates from y 1280),
#   faces east and walks: the niche's back wall stops him on
#   the gun, as the dorm's alcove does at R1.
# * the PPSh-41 (21004 at 2000 1520) lies on the catwalk (x 1792..2560,
#   y 1440..1600, floor 96). A7 warps 60 west of it on the catwalk, faces
#   east and walks along the catwalk's middle: nothing stops him, but the
#   walk and its glide (~290 units) end on the catwalk short of its east
#   end (x 2560), and the D6 recess and the S2 panel are off the lane.
# Both start further from the thing than touch (16 + 20) and the walks are
# checked against the built map by tests/test_route.py.
MAP01_IZH_APPROACH = (1000, 1256)
MAP01_IZH_FACING = 0
MAP01_PPSH_APPROACH = (1940, 1520)
MAP01_PPSH_FACING = 0
WEAPON_WALK = 35  # as RACK_WALK; the PPSh's lane is open, the IZh's ends at a wall

_A_STEPS = (
    Step("A0", actions=("level", "count", "inv", f"tag {MAP01_TAG_EVENT_IZH}",
                        f"tag {MAP01_TAG_EVENT_PPSH}", "capture"), expect=("Z1",),
         melee=False, ready_slot=SLOT_SIDEARM, ready_ammo=start_rounds(),
         tags=((MAP01_TAG_EVENT_IZH, False), (MAP01_TAG_EVENT_PPSH, False)),
         note="the player start: TT-33 raised with its rounds, slot 1 empty; "
              "monsters on this skill, bestiary counts; both weapons' closets shut"),
    Step("R1", MAP01_RACK_APPROACH, MAP01_RACK_FACING, (f"forward {RACK_WALK}", "inv", "capture"),
         expect=("Z1",), melee=True,
         note=f"the dorm rack: walk onto the melee weapon (DoomEdNum {ED_MELEE}); slot 1 owned"),
    Step("A1", (256, 420), 90, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
         expect=("Z3",), note="D2 opens; walk into the barracks corridor"),
    Step("A2", (256, 940), 90, ("capture",), expect=("Z3", "Z4"),
         note="the komnata ahead"),
    Step("A3", (600, 1152), 0, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
         expect=("Z5",), note="D3 opens; walk into the service corridor"),
    Step("A4", MAP01_IZH_APPROACH, MAP01_IZH_FACING, (f"forward {WEAPON_WALK}", "inv", "capture"),
         expect=("Z5B",),
         note="the guard post: walk into the rack's niche onto the IZh-58 (a warp would not "
              "take it, and its pickup opens tag 12)"),
    Step("A5", (1336, 1152), 0, (f"tag {MAP01_TAG_D4}", "capture"), expect=("Z6",),
         tags=((MAP01_TAG_D4, False),), note="the hangar, first contact; D4 still shut"),
    Step("A6", (1416, 1624), 0, ("use", f"wait {SWITCH_WAIT}", f"tag {MAP01_TAG_D4}",
                                 f"tag {MAP01_TAG_EVENT_IZH}", "capture", "angle 90", "capture"),
         expect=("Z7",), tags=((MAP01_TAG_D4, True), (MAP01_TAG_EVENT_IZH, True)),
         note="SW-A: D4 and the three fuel-bay ambush panels open; the IZh's closet "
              "(its pickup at A4) is open"),
    Step("A7", MAP01_PPSH_APPROACH, MAP01_PPSH_FACING, (f"forward {WEAPON_WALK}", "inv", "capture"),
         expect=("Z6B",),
         note="the catwalk: walk east onto the PPSh-41 (a warp would not take it, and its "
              "pickup opens tag 13)"),
    Step("A8", (2496, 1560), 90, (f"tag {MAP01_TAG_D5}", "use", f"wait {DOOR_WAIT}",
                                  f"forward {WALK}", "capture"),
         expect=("D6", "Z9"), tags=((MAP01_TAG_D5, False),),
         note="D6 opens; walk into it (the booth is through its east side); D5 still shut"),
    Step("A9", (2560, 1810), 90, ("use", f"wait {SWITCH_WAIT}", f"tag {MAP01_TAG_D5}",
                                  f"tag {MAP01_TAG_EVENT_PPSH}", "capture"),
         expect=("Z9",), tags=((MAP01_TAG_D5, True), (MAP01_TAG_EVENT_PPSH, True)),
         note="SW-B: D5 and the three wave-2 closets open; the PPSh-41's closet "
              "(its pickup at A7) is open"),
    Step("A10", (2660, 672), 0, (f"forward {WALK_LONG}", "capture"), expect=("Z8", "D5", "Z10"),
         note="through D4 into the airlock (ending past D4 proves it open)"),
    Step("A11", (2880, 672), 0, (f"forward {WALK_LONG}", "capture"), expect=("Z10",),
         note="through D5 into the exit lift room"),
    Step("A12", (3250, 640), 0, ("use",), note="the exit switch"),
)

# The three secrets of section 7, with the warps and facings of V4, V15 and
# V16 in section 17.10; each walks in after pushing the panel, because a
# secret counts when the player ENTERS its sector.
_S1 = Step("S1", (920, 96), 0, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
           expect=("S1",), note="secret 1: the middle shower stall's plate")
_S2 = Step("S2", (2208, 1560), 90, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
           expect=("S2",), note="secret 2: the catwalk panel under the slit")
_S3 = Step("S3", (1170, 1760), 180, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
           expect=("S3",), note="secret 3: the sump at the end of the drain")


def _insert_after(steps, anchor: str, extra: Step):
    out = []
    for step in steps:
        out.append(step)
        if step.id == anchor:
            out.append(extra)
    return tuple(out)


_SECRET_STEPS = _insert_after(_insert_after(_insert_after(_A_STEPS, "R1", _S1), "A6", _S3), "A7", _S2)

# --- RANGE, the practice range (D41; docs/levels/RANGE-practice-range.md) --
# The same two checks as A0 and R1, on the range (src/maps/RANGE/map.py): the
# player starts at (160, 384) facing east and the weapon row lies along
# y 624, the melee weapon (DoomEdNum ED_MELEE) first at x 288 and the next
# 112 further east, so walking north up x 288 collects that one and no other.
# Then the way out, as a player leaves (d1e891f, the design's section 4.1):
# E0 stands on the start, turns round (180) and walks west into the lit
# alcove until its back wall stops him, on top of nothing; E1 presses the
# Exit_Normal switch on that wall (x -32, y 352..416), 16 units ahead, inside
# Doom's 64-unit use range. Its shot is cluster 2's end text (MAPINFO:
# `nointermission`, `next = endtitle`). tests/test_route.py reads the exit
# line back from the built map and holds this geometry.
RANGE_AXE_APPROACH = (288, 560)
RANGE_AXE_FACING = 90
RANGE_START = (160, 384)
RANGE_EXIT_FACING = 180
EXIT_WALK = 50   # ~8 units a tic: far more than the 176 from the start to the alcove's wall

_RANGE_A0 = Step("A0", actions=("level", "inv", "capture"), expect=("HALL",),
                 melee=False, ready_slot=SLOT_SIDEARM, ready_ammo=start_rounds(),
                 note="the player start: TT-33 raised with its rounds, slot 1 empty")
_RANGE_R1 = Step("R1", RANGE_AXE_APPROACH, RANGE_AXE_FACING, (f"forward {RACK_WALK}", "inv", "capture"),
                 expect=("HALL",), melee=True,
                 note=f"walk north over the weapon row's first item (DoomEdNum {ED_MELEE})")
_RANGE_EXIT_STEPS = (
    Step("E0", RANGE_START, RANGE_EXIT_FACING, ("capture", f"forward {EXIT_WALK}", "capture"),
         expect=("EXIT",),
         note="P1: from the start, turned round, the lit alcove and the hazard panel whole; "
              "then walk into the alcove up to the switch"),
    Step("E1", actions=("use", f"wait {END_TEXT_TICS}", "state", "capture"),
         note="P6: press the exit switch; cluster 2's end text, SD_END02_TEXT over SDFLR1, "
              "is what the shot must show"),
)
_RANGE_STEPS = (_RANGE_A0, _RANGE_R1) + _RANGE_EXIT_STEPS

# --- RANGE's P4: the gallery door opened from the passage side -------------
# The design's section 7, P4, which the PM's pass of 20:57 did not exercise.
# The door (tag 1, x 640..768, y 768..832) carries Door_Raise on both faces;
# P4a warps into the passage's south leg facing the door (south) and reads
# tag 1 shut; P4b presses, reads it open, and walks through into the hall.
# The walk runs down x 672, 48 off the PPSh-41 (624, 624) and 64 off the
# RPG-7 (736, 624), so it takes no pickup on the way (tests/test_route.py).
# A route of its own (range-door) so range-start, proven at 20:52, stays as
# it is if P4 fails for the route's sake.
RANGE_TAG_GALLERY_DOOR = 1
RANGE_DOOR_PASSAGE_SIDE = (672, 864)
RANGE_DOOR_FACING = 270

_RANGE_P4 = (
    Step("P4a", RANGE_DOOR_PASSAGE_SIDE, RANGE_DOOR_FACING,
         (f"tag {RANGE_TAG_GALLERY_DOOR}", "capture"), expect=("PASSAGE",),
         tags=((RANGE_TAG_GALLERY_DOOR, False),),
         note="P4: in the passage, facing the gallery door from behind; still shut"),
    Step("P4b", actions=("use", f"wait {DOOR_WAIT}", f"tag {RANGE_TAG_GALLERY_DOOR}",
                         f"forward {WALK}", "capture"),
         expect=("HALL",), tags=((RANGE_TAG_GALLERY_DOOR, True),),
         note="P4: the door opens from the passage side; walk through into the hall"),
)

# --- MAP01, the mural shots M1-M5 (design section 17.13) ------------------
# Warp, face, shoot: the CEO judges the pictures. Run with --nomonsters so
# nothing walks into the frame. M3 is two shots (the doorway's two corners).
# M4's last clause (the health bonus at 432 1400 can be walked onto) is C12
# of docs/qa/GATE-REVIEWS.md, walked by hand and not scripted here: a warp
# onto the bonus would skip the very question, and the route reads no pickup
# message. Since f3cd8ea (G3-F1) the way to it is a 48-wide lane between the
# lectern (x <= 416) and the east floor lamp (x >= 464), a body and a half;
# the PM walked it at 20:57 (warp 440 1300, facing north, +forward: the log
# says "Health boosted!"), and G3-F1 is closed.
_MURAL_STEPS = (
    Step("M1", (256, 976), 90, ("capture",), expect=("Z4",),
         note="from the doorway: the mural whole, the lectern right of it on the tribune"),
    Step("M2", (320, 1192), 90, ("capture",), expect=("Z4",),
         note="from the centre: the inner columns either side of the tribune"),
    Step("M3a", (208, 976), 80, ("capture",), expect=("Z4",),
         note="from the doorway's west corner: a sliver behind the jamb at most"),
    Step("M3b", (304, 976), 100, ("capture",), expect=("Z4",),
         note="from the doorway's east corner"),
    Step("M4", (400, 1320), 90, ("capture",), expect=("Z4",),
         note="the lectern at the tribune's front-right corner: plank top level, no HOM or seam"),
    Step("M5", (320, 1360), 90, ("capture",), expect=("Z4",),
         note="close up: the health bonus at the mural's foot. Clutter or fine? (the CEO's call)"),
)

# --- MAP02 Metro-bunker: the critical path (docs/levels/MAP02-metro.md 5) --
# Built from the map, never from copied coordinates: another agent is
# building MAP02 v1 (the pass signposted, the map populated) while this is
# written, and v1 may move the pass, the switches or the doors. What the
# route reads, and where from:
#   * tags, the locked-door special and the pass's editor number: the named
#     constants of src/maps/MAP02/map.py (METRO_CONSTANTS);
#   * the blast door: the line(s) with that special and TAG_BLAST_DOOR, the
#     face whose front sector is the hall (METRO_HALL_FAMILY);
#   * the pass: the one DoomEdNum ED_BLUE_CARD thing spawning on skills 2,
#     3 and 4 (the same spot on each), walked onto from the first side of
#     it with a clear lane in its own zone;
#   * SW-A and SW-B: the one-sided, player-used lines whose arg0 is
#     TAG_SHUTTER and TAG_GATE;
#   * the exit: the Exit_Normal line; E0 starts on the ray out of its niche,
#     GATE_CLEARANCE past the far face of the first TAG_GATE sector it
#     crosses, so the walk to the switch proves the gate open.
# Every press is made from USE_DISTANCE in front of the line's front face,
# facing it. tests/test_route.py holds the geometry on the built map.
METRO_CONSTANTS = ("TAG_BLAST_DOOR", "TAG_SHUTTER", "TAG_GATE", "SPECIAL_DOOR_LOCKED_RAISE",
                   "ED_BLUE_CARD", "TAG_EVENT_PASS")
# V3 A2 (docs/levels/PICKUP-EVENTS.md; MAP02 design section 18): the pass's
# pickup opens the duty window (TAG_EVENT_PASS) into a way back to the hall.
# Shut (48 high) when the blue door is first pressed (BD0), open (a body high)
# when it is pressed with the pass (BD1), the door's 70 tics after the walk.
# The pass's walk itself goes through it (metro_critical, PASS): the booth
# is entered only from its step on the east, so the walk faces west, and
# the window's 48-high slot was the wall that stopped the walk's overshoot.
# Once the pass is taken the window's head rises (8 units, 4 tics, make it a
# body high) and the body walks on through it and drops into the hall: the
# PM's v3 pass of 2026-10-23 12:20 ended PASS at (2789, 1056) in z3_hall,
# falling (z 27), on all three skills. That is the event working, not a
# broken map; PASS now expects the room past the window whenever the walk's
# lane crosses a sector the pass's own event opens (pass_event_exit).
METRO_HALL_FAMILY = "Z3"        # the blast door is pressed from the hall's portal band
METRO_PASS_SKILLS = (2, 3, 4)   # G3's skills: the pass must lie at one spot on each
USE_DISTANCE = 32               # line to the body's centre: Doom's use range is 64
PLAYER_RADIUS = 16
MAX_STEP_UP = 24
SAMPLE_UNITS = 4                # spacing of the points a walk is checked at
# +forward from rest does not cover WALK_UNITS_PER_TIC from the first tic:
# Doom's walk thrust (forwardmove 25 x 2048 / 65536 = 0.78 units/tic^2) and
# ground friction (0.90625) give a top speed of 8.33 units/tic and leave the
# body ~9.7 tics behind it when it starts from rest, so n tics cover about
# 8.33 x (n - 9.7) units. Derived from Doom's constants, NOT VERIFIED in
# GZDoom; the walks below add ACCEL_TICS to the plain distance / 8, which
# covers the distance with margin on that model.
ACCEL_TICS = 12
PASS_APPROACH = 64     # the pass walk starts here: outside touch (16 + 20)
PASS_OVERSHOOT = 32    # and is sized to end this far past the pass
DOOR_CLEARANCE = 64    # BD1 walks this far past the blast door's far face
GATE_CLEARANCE = 64    # E0 starts this far past the gate's far face
MAX_RAY = 4096         # how far a ray looks for a door before giving up
PASS_DIRECTIONS = (0, 180, 90, 270)   # tried in this order; the first clear lane wins
COMPASS = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}


def walk_tics(distance: float) -> int:
    """+forward tics that carry the body `distance` units from rest."""
    return math.ceil(distance / WALK_UNITS_PER_TIC) + ACCEL_TICS


def _angle_of(vector: tuple[int, int]) -> int:
    for angle, v in COMPASS.items():
        if v == vector:
            return angle
    raise RouteError(f"not an axis direction: {vector}")


def _map_const(md: "MapData", name: str):
    try:
        return getattr(md.module, name)
    except AttributeError:
        raise RouteError(f"src/maps/{md.map_name}/map.py no longer defines {name}: "
                         f"the route reads it from there") from None


def line_ends(md: "MapData", ld) -> tuple[tuple[float, float], tuple[float, float]]:
    a, b = md.textmap.vertices[ld.v1], md.textmap.vertices[ld.v2]
    return (a.x, a.y), (b.x, b.y)


def front_normal(md: "MapData", ld) -> tuple[int, int]:
    """The unit vector out of a line's front face (Doom: the right of v1->v2)."""
    (x1, y1), (x2, y2) = line_ends(md, ld)
    if x1 == x2:
        return (1, 0) if y2 > y1 else (-1, 0)
    if y1 == y2:
        return (0, -1) if x2 > x1 else (0, 1)
    raise RouteError(f"line {ld.v1}->{ld.v2} is not axis-aligned")


def approach(md: "MapData", ld, distance: int = USE_DISTANCE) -> tuple[tuple[int, int], int]:
    """The point `distance` in front of a line's middle, and the facing at it."""
    (x1, y1), (x2, y2) = line_ends(md, ld)
    nx, ny = front_normal(md, ld)
    point = (int((x1 + x2) / 2 + nx * distance), int((y1 + y2) / 2 + ny * distance))
    return point, _angle_of((-nx, -ny))


def _longest(md: "MapData", lines: list, what: str):
    if not lines:
        raise RouteError(f"{md.map_name}: no line for {what}")
    def length(ld):
        (x1, y1), (x2, y2) = line_ends(md, ld)
        return abs(x2 - x1) + abs(y2 - y1)
    return max(lines, key=length)


def switch_line(md: "MapData", tag: int, what: str):
    """The one-sided, player-used switch line whose special acts on `tag`."""
    found = [ld for ld in md.textmap.linedefs
             if ld.special and ld.arg0 == tag and ld.sideback is None and "playeruse" in ld.flags]
    return _longest(md, found, f"{what} (a one-sided switch with arg0 {tag})")


def family_at(md: "MapData", point) -> str:
    return zone_family(md.name_of(md.sector_at(*point)))


def _ray_past_door(md: "MapData", start, angle: int, door_tag: int, what: str) -> tuple[int, int]:
    """From `start` along `angle`: the distance at which the ray leaves the
    first sector tagged `door_tag`, and the sector it enters there."""
    dx, dy = COMPASS[angle]
    inside = False
    for t in range(SAMPLE_UNITS, MAX_RAY, SAMPLE_UNITS):
        s = md.sector_at(start[0] + dx * t, start[1] + dy * t)
        if s is None:
            raise RouteError(f"{what}: the ray from {start} facing {angle} hits a wall at {t} "
                             f"before passing a sector tagged {door_tag}")
        if md.textmap.sectors[s].identifier == door_tag:
            inside = True
        elif inside:
            return t, s
    raise RouteError(f"{what}: no sector tagged {door_tag} within {MAX_RAY} of {start}")


def lane_is_clear(md: "MapData", start, angle: int, must: int, may: int, family: str) -> bool:
    """A body walking from `start` along `angle` stays in `family` for the
    first `must` units (lateral edges included, no step over MAX_STEP_UP
    from where it started, no opening lower than PLAYER_HEIGHT), and up to
    `may` units either stays in it or is stopped by a wall, a step or a low
    opening (MAP02 v1's booth window is 48 high)."""
    dx, dy = COMPASS[angle]
    px, py = -dy, dx
    s0 = md.sector_at(*start)
    if s0 is None:
        return False
    floor0 = md.textmap.sectors[s0].heightfloor
    for t in range(0, may + 1, SAMPLE_UNITS):
        for off in (-(PLAYER_RADIUS - 1), 0, PLAYER_RADIUS - 1):
            x, y = start[0] + dx * t + px * off, start[1] + dy * t + py * off
            s = md.sector_at(x, y)
            sec = md.textmap.sectors[s] if s is not None else None
            blocked = (sec is None or sec.heightfloor - floor0 > MAX_STEP_UP
                       or sec.heightceiling - sec.heightfloor < PLAYER_HEIGHT)
            if not blocked and zone_family(md.name_of(s)) == family:
                continue
            if t <= must:
                return False
            return blocked     # past the pass: a wall stops him; another room does not
    return True


def pass_spot(md: "MapData", ednum: int) -> tuple[int, int]:
    """The pass: the one `ednum` thing of each of METRO_PASS_SKILLS, one spot."""
    per_skill = {s: sorted({(int(t.x), int(t.y)) for t in md.things_on(ednum, s)})
                 for s in METRO_PASS_SKILLS}
    spots = {tuple(v) for v in per_skill.values()}
    if any(len(v) != 1 for v in per_skill.values()) or len(spots) != 1:
        raise RouteError(f"{md.map_name}: want one DoomEdNum {ednum} at one spot on skills "
                         f"{METRO_PASS_SKILLS}, found {per_skill}")
    return per_skill[METRO_PASS_SKILLS[0]][0]


def pass_walk(md: "MapData", spot, run_up: int = PASS_APPROACH) -> tuple[tuple[int, int], int, str, int]:
    """Where to start the walk onto the pass (or a key), facing which way,
    the zone family it ends in, and its tics. `run_up` is how far from the
    pickup the walk starts (MAP03's keys lie on raised tops 64 and 128
    wide, so their walks start further out: KEY_APPROACH)."""
    home = md.sector_at(*spot)
    family = zone_family(md.name_of(home)) if home is not None else "?"
    if family == "?":
        raise RouteError(f"the pickup at {spot} lies in sector {md.name_of(home)!r}, which has no "
                         f"zone family: add a ZONE_PREFIXES row in tools/route.py")
    tics = walk_tics(run_up + PASS_OVERSHOOT)
    for angle in PASS_DIRECTIONS:
        dx, dy = COMPASS[angle]
        start = (spot[0] - dx * run_up, spot[1] - dy * run_up)
        if lane_is_clear(md, start, angle, run_up + PLAYER_RADIUS,
                         tics * WALK_UNITS_PER_TIC, family):
            return start, angle, family, tics
    raise RouteError(f"no clear lane of {run_up} units in {family} onto the pickup at {spot}")


def pass_event_exit(md: "MapData", start, angle: int, reach: int, tag: int) -> str | None:
    """The zone family a walk from `start` along `angle` ends in once the
    pickup's event has opened the sectors tagged `tag`, if the walk crosses
    one within `reach` (a door the event raises: the body walks through it
    and on into the room beyond); None if the lane meets a wall first or
    never crosses one."""
    dx, dy = COMPASS[angle]
    inside = False
    for t in range(SAMPLE_UNITS, reach + 1, SAMPLE_UNITS):
        s = md.sector_at(start[0] + dx * t, start[1] + dy * t)
        if s is None:
            return None
        if md.textmap.sectors[s].identifier == tag:
            inside = True
        elif inside:
            return zone_family(md.name_of(s))
    return None


def start_family(md: "MapData") -> str:
    """The zone family of the map's one player start."""
    starts = [t for t in md.textmap.things if t.type == ED_PLAYER1_START]
    if len(starts) != 1:
        raise RouteError(f"{md.map_name}: want one player start, found {len(starts)}")
    return family_at(md, (starts[0].x, starts[0].y))


@dataclass(frozen=True)
class DoorWalk:
    """A locked door pressed from `point` facing `angle` (its face in the
    pressing room), and the walk of `tics` through it into `inside`."""
    point: tuple[int, int]
    angle: int
    tics: int
    inside: str


def locked_door_walk(md: "MapData", special: int, tag: int, from_family: str, what: str,
                     lock: int | None = None) -> DoorWalk:
    """The face of the locked door (`special`, arg0 `tag`, and arg3 `lock`
    if given) whose front sector is in `from_family`; the press point in
    front of it, and the walk DOOR_CLEARANCE past its far face."""
    tm = md.textmap
    faces = [ld for ld in tm.linedefs if ld.special == special and ld.arg0 == tag
             and (lock is None or ld.arg3 == lock)
             and zone_family(md.name_of(tm.sidedefs[ld.sidefront].sector)) == from_family]
    lock_text = "" if lock is None else f" (lock {lock})"
    point, angle = approach(md, _longest(md, faces, f"{what}'s {from_family} face{lock_text}"))
    beyond, room = _ray_past_door(md, point, angle, tag, what)
    return DoorWalk(point, angle, walk_tics(beyond + DOOR_CLEARANCE), zone_family(md.name_of(room)))


def exit_walk(md: "MapData", gate_tag: int, what: str) -> tuple[tuple[int, int], int, int, str]:
    """E0: the start on the ray out of the exit's niche, GATE_CLEARANCE past
    the far face of the first sector tagged `gate_tag` it crosses, facing the
    switch; the walk's tics (it ends against the switch); the exit's family."""
    tm = md.textmap
    exits = [ld for ld in tm.linedefs if ld.special == SPECIAL_EXIT_NORMAL]
    exit_line = _longest(md, exits, "the exit switch")
    exit_mid, exit_angle = approach(md, exit_line, 0)
    exit_family = zone_family(md.name_of(tm.sidedefs[exit_line.sidefront].sector))
    out = (exit_angle + 180) % 360
    past_gate, _room = _ray_past_door(md, exit_mid, out, gate_tag, what)
    e0_t = past_gate + GATE_CLEARANCE
    ox, oy = COMPASS[out]
    e0_point = (int(exit_mid[0] + ox * e0_t), int(exit_mid[1] + oy * e0_t))
    return e0_point, exit_angle, walk_tics(e0_t - PLAYER_RADIUS), exit_family


def metro_critical(md: "MapData | None" = None) -> Route:
    """MAP02's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*METRO_CONSTANTS))
    tag_bd, tag_sh, tag_gate, locked, ed_pass, tag_win = (_map_const(md, n) for n in METRO_CONSTANTS)

    a0_family = start_family(md)

    # The blast door, its hall face; BD1 walks through it to the room behind.
    bd = locked_door_walk(md, locked, tag_bd, METRO_HALL_FAMILY, "the blast door")
    bd_point, bd_angle, bd_tics, inside_family = bd.point, bd.angle, bd.tics, bd.inside

    spot = pass_spot(md, ed_pass)
    pass_start, pass_angle, pass_family, pass_tics = pass_walk(md, spot)
    # V3 A2: the pass opens the duty window; a walk that runs into it ends
    # past it (METRO_CONSTANTS' comment). Read from the map, so a pass moved
    # off the window's lane (test_a_moved_pass_is_followed) ends at home.
    through = pass_event_exit(md, pass_start, pass_angle, pass_tics * WALK_UNITS_PER_TIC, tag_win)
    pass_end = through or pass_family
    pass_tags = ((tag_sh, False),) + (((tag_win, True),) if through else ())
    pass_actions = (f"forward {pass_tics}", "inv", f"tag {tag_sh}")         + ((f"tag {tag_win}",) if through else ()) + ("capture",)

    swa = switch_line(md, tag_sh, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_gate, "SW-B")
    swb_point, swb_angle = approach(md, swb)

    e0_point, exit_angle, e0_tics, exit_family = exit_walk(md, tag_gate, "the exit tunnel's gate")

    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,),
             key=False, note="the player start (from MAP01's lift): no key; monsters on this skill"),
        Step("BD0", bd_point, bd_angle,
             ("use", f"wait {DOOR_WAIT}", f"tag {tag_bd}", f"tag {tag_win}", "inv", "capture"),
             expect=(family_at(md, bd_point),), tags=((tag_bd, False), (tag_win, False)), key=False,
             presses=((locked, tag_bd),),
             note="the blue door pressed WITHOUT the pass: pressed, and still shut (K2's first half); "
                  "the duty window a slot"),
        Step("PASS", pass_start, pass_angle, pass_actions,
             expect=(pass_end,), tags=pass_tags, key=True,
             note=f"walk onto the pass (DoomEdNum {ed_pass} at {spot}), no give: a key is owned; "
                  "the shutter still shut" + ("; the pass opened the duty window and the walk "
                                              "carries on through it, down into the hall (V3 A2)"
                                              if through else "")),
        Step("BD1", bd_point, bd_angle,
             ("use", f"wait {DOOR_WAIT}", f"tag {tag_bd}", f"tag {tag_win}", f"forward {bd_tics}",
              "capture"),
             expect=(inside_family,), tags=((tag_bd, True), (tag_win, True)), presses=((locked, tag_bd),),
             note="the blue door with the pass: open; walk through it into the bunker; the pass "
                  "opened the duty window (V3 A2)"),
        Step("SWA", swa_point, swa_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sh}", f"tag {tag_gate}", "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_sh, True), (tag_gate, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A: the shutter opens; the gate is still shut"),
        Step("SWB", swb_point, swb_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_gate}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_gate, True),),
             presses=((swb.special, swb.arg0),),
             note="SW-B: the gate and the command post's tunnel door open"),
        Step("E0", e0_point, exit_angle, ("capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,),
             note="from the west tunnel, through the gate, into the exit niche up to the switch"),
        Step("E1", actions=("use",), note="the exit switch"),
    )
    return Route("metro-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="the metro's critical path: the blue door shut without the pass, the pass "
                             "walked onto, the door open, SW-A, SW-B, the gate, out by the exit switch")


# --- MAP03 Tankograd: the critical path (docs/levels/MAP03-factory.md 5, 15)
# metro-critical's method on the factory, the episode's last map. Nothing is a
# copied coordinate or a class name; what the route reads, and where from:
#   * tags, the locked-door special, the two lock numbers and the two keys'
#     editor numbers (6 yellow, 13 red: Doom's cards, which Freedoom draws;
#     no SD_ class yet): the named constants of src/maps/MAP03/map.py
#     (TANKOGRAD_CONSTANTS);
#   * each locked door: the Door_LockedRaise line with its tag AND its lock
#     whose front sector is in the assembly hall (TANKOGRAD_HALL_FAMILY), so
#     a door that lost its lock, or swapped it, has no face and no route;
#   * each key: the one thing of its editor number on skills 2, 3 and 4,
#     walked onto from KEY_APPROACH, never given;
#   * SW-A and SW-B: the one-sided switches whose arg0 is TAG_SHUTTER and
#     TAG_GATE; the exit: E0 on the ray out of the breaker's niche, past the
#     drum's gate (TAG_GATE), so the walk up the dais proves the gate open.
# Keys are COUNTED by the Key base class (0, 1, 2), never named: the yellow
# and red cards may get SD_ classes the way MAP02's pass did. Which key is
# which is proved by the doors: both shut with no key (YD0, RD0), the red one
# still shut with the yellow key alone (RDY: lock 1 is not lock 3), each open
# once its own key is owned. The order is the brief's (N2): the yellow key and
# door, the red key and door, SW-A, SW-B, the breaker. MAPINFO's `next` for
# the factory is `endtitle` (cluster 1 ends the episode, D62), so the exit is
# judged as an end sequence, read from MAPINFO like every other route's.
TANKOGRAD_CONSTANTS = ("TAG_YELLOW_DOOR", "TAG_RED_DOOR", "TAG_SHUTTER", "TAG_GATE",
                       "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_YELLOW_CARD", "LOCK_RED_CARD",
                       "ED_YELLOW_CARD", "ED_RED_CARD", "TAG_EVENT_YELLOW", "TAG_EVENT_RED")
# V3 A2/A3 (docs/levels/PICKUP-EVENTS.md; MAP03 design section 19): the yellow
# key's pickup opens the two office closets (TAG_EVENT_YELLOW): shut at YD0,
# open at YD1, the door's 70 tics after the key. The red key's raises the
# goods lift (TAG_EVENT_RED), whose car is never "shut" by the door rule (it
# is always 192 high, it moves): RKEY and RD1 only print its floor and ceiling
# for the PM (before: -256 and -64; after: -64 and 128), judged by eye.
TANKOGRAD_HALL_FAMILY = "Z3"    # both locks are pressed from the assembly hall's portals
# The yellow key lies on the director's desk (64 deep, 16 up), the red on the
# ingot pedestal (128 square, 16 up), each in the middle: PASS_APPROACH (64)
# would start the body on the top's edge. 96 starts it a body clear of it,
# on the room's own floor, and the walk steps up 16 onto the top.
KEY_APPROACH = 96


def tankograd_critical(md: "MapData | None" = None) -> Route:
    """MAP03's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*TANKOGRAD_CONSTANTS))
    (tag_yd, tag_rd, tag_sh, tag_gate, locked, lock_y, lock_r, ed_y, ed_r, tag_ye, tag_lift) = (
        _map_const(md, n) for n in TANKOGRAD_CONSTANTS)

    a0_family = start_family(md)
    yd = locked_door_walk(md, locked, tag_yd, TANKOGRAD_HALL_FAMILY, "the yellow door", lock_y)
    rd = locked_door_walk(md, locked, tag_rd, TANKOGRAD_HALL_FAMILY, "the red door", lock_r)
    yd_family, rd_family = family_at(md, yd.point), family_at(md, rd.point)

    y_spot = pass_spot(md, ed_y)
    y_start, y_angle, y_family, y_tics = pass_walk(md, y_spot, KEY_APPROACH)
    r_spot = pass_spot(md, ed_r)
    r_start, r_angle, r_family, r_tics = pass_walk(md, r_spot, KEY_APPROACH)

    swa = switch_line(md, tag_sh, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_gate, "SW-B")
    swb_point, swb_angle = approach(md, swb)

    e0_point, exit_angle, e0_tics, exit_family = exit_walk(md, tag_gate, "the drum's gate")

    press = ("use", f"wait {DOOR_WAIT}")
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start (off MAP02's rails): no key; monsters on this skill"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", f"tag {tag_ye}", "inv", "capture"),
             expect=(yd_family,), tags=((tag_yd, False), (tag_ye, False)), keys=0,
             presses=((locked, tag_yd),),
             note=f"the yellow door (lock {lock_y}) pressed with no key: pressed, and still shut; "
                  "the office closets shut"),
        Step("RD0", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(rd_family,), tags=((tag_rd, False),), keys=0, presses=((locked, tag_rd),),
             note=f"the red door (lock {lock_r}) pressed with no key: pressed, and still shut"),
        Step("YKEY", y_start, y_angle,
             (f"forward {y_tics}", "inv", f"tag {tag_yd}", f"tag {tag_rd}", "capture"),
             expect=(y_family,), tags=((tag_yd, False), (tag_rd, False)), keys=1,
             note=f"walk onto the yellow key (DoomEdNum {ed_y} at {y_spot}), no give: one key; "
                  "both doors still shut"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"tag {tag_ye}", f"forward {yd.tics}",
                                                 "capture"),
             expect=(yd.inside,), tags=((tag_yd, True), (tag_ye, True)), presses=((locked, tag_yd),),
             note="the yellow door with its key: open; walk through it to the tank line; the key "
                  "opened the office closets (V3 A2)"),
        Step("RDY", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(rd_family,), tags=((tag_rd, False),), keys=1, presses=((locked, tag_rd),),
             note="the red door pressed with the yellow key only: still shut"),
        Step("RKEY", r_start, r_angle,
             (f"forward {r_tics}", "inv", f"tag {tag_rd}", f"tag {tag_sh}", f"tag {tag_lift}", "capture"),
             expect=(r_family,), tags=((tag_rd, False), (tag_sh, False)), keys=2,
             note=f"walk onto the red key (DoomEdNum {ed_r} at {r_spot}), no give: two keys; "
                  "the red door and the shutter still shut"),
        Step("RD1", rd.point, rd.angle, press + (f"tag {tag_rd}", f"tag {tag_lift}", f"forward {rd.tics}",
                                                 "capture"),
             expect=(rd.inside,), tags=((tag_rd, True),), presses=((locked, tag_rd),),
             note="the red door with its key: open; walk through it to the portal hall; the goods "
                  "lift's floor and ceiling printed (V3 A3: up by its travel since RKEY)"),
        Step("SWA", swa_point, swa_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sh}", f"tag {tag_gate}", "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_sh, True), (tag_gate, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A: the shutter and the hall's two closets open; the drum's gate still shut"),
        Step("SWB", swb_point, swb_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_gate}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_gate, True),),
             presses=((swb.special, swb.arg0),),
             note="SW-B: the drum's gate opens"),
        Step("E0", e0_point, exit_angle, ("capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,),
             note="from the portal hall, through the gate and up the dais to the breaker"),
        Step("E1", actions=("use",), note="the exit breaker: the episode's end"),
    )
    return Route("tankograd-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="the factory's critical path: both locks shut without keys, the yellow "
                             "key walked onto and its door opened, the red door shut on the yellow "
                             "key, the red key and its door, SW-A, SW-B, the gate, the breaker, the "
                             "episode's end")


# --- MAP05 Volga Dam: the critical path (docs/levels/MAP05-volga-dam.md 5, 13)
# tankograd-critical's method on the dam, the second map of episode 2. What the
# route reads, and where from (nothing copied, nothing named by class):
#   * tags, specials, the two locks and the two keys' editor numbers (5 blue,
#     6 yellow: SD_BluePass and SD_YellowPass replace Doom's cards): the named
#     constants of src/maps/MAP05/map.py (DAM_CONSTANTS);
#   * the yellow door: its Door_LockedRaise face (tag AND lock) in the portal
#     on the turbine hall's catwalk (family Z5); the blue gate: its face in the
#     station's portal (Z1); each walked through into the room beyond;
#   * each key: the one thing of its editor number on skills 2, 3 and 4,
#     walked onto from KEY_APPROACH (both lie on pads one step up);
#   * SW-A and SW-B: the one-sided switches whose arg0 is TAG_CABLE_SHUTTER and
#     TAG_STATION_SHUTTER;
#   * the exit: D2, the west bank's MANUAL door (Door_Raise, TAG_D2_WEST), is
#     pressed from the crest's porch (Z10), and the walk goes on straight
#     through it to the exit switch, which stands on the same line.
# Order: both locks shut with no key (YD0, BG0); the yellow key; the yellow
# door; SW-A; the blue key (the gate still shut, and the station's shutter);
# SW-B, the shortcut; the blue gate with its key, onto the crest; D2; the
# switch. MAPINFO's `next` for the dam is MAP06.
# V3 (A2, A3): two pickups do things. The yellow key brings the old sluice's
# wall down (Floor_LowerToLowest on TAG_SLUICE_BREACH: the dam bursts): YD0
# reads it shut, YKEY waits and reads it open. The blue key opens the
# substation's tool store (Door_Open on TAG_SUBSTATION_STORE): SWA reads it
# shut, BKEY waits and reads it open. The burst's riders (the quake, the
# water) have no tag the route can judge; the PM looks at them.
DAM_CONSTANTS = ("TAG_BLUE_GATE", "TAG_YELLOW_DOOR", "TAG_CABLE_SHUTTER", "TAG_STATION_SHUTTER",
                 "TAG_D2_WEST", "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_BLUE_CARD", "LOCK_YELLOW_CARD",
                 "ED_BLUE_CARD", "ED_YELLOW_CARD", "TAG_SLUICE_BREACH", "TAG_SUBSTATION_STORE")
DAM_YELLOW_FAMILY = "Z5"   # the yellow door is pressed from its portal on the hall's catwalk
DAM_BLUE_FAMILY = "Z1"     # the blue gate from its portal in the station
DAM_CREST_FAMILY = "Z10"   # D2 from the crest's west porch
DAM_SPECIAL_DOOR_RAISE = 12   # Door_Raise, udmf.SPECIAL_DOOR_RAISE: D2 is a manual door


def dam_critical(md: "MapData | None" = None) -> Route:
    """MAP05's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*DAM_CONSTANTS))
    (tag_bg, tag_yd, tag_sha, tag_shb, tag_d2, locked, lock_b, lock_y, ed_b, ed_y,
     tag_sluice, tag_store) = (_map_const(md, n) for n in DAM_CONSTANTS)
    tm = md.textmap

    a0_family = start_family(md)
    yd = locked_door_walk(md, locked, tag_yd, DAM_YELLOW_FAMILY, "the yellow door", lock_y)
    bg = locked_door_walk(md, locked, tag_bg, DAM_BLUE_FAMILY, "the blue gate", lock_b)
    yd_family, bg_family = family_at(md, yd.point), family_at(md, bg.point)

    y_spot = pass_spot(md, ed_y)
    y_start, y_angle, y_family, y_tics = pass_walk(md, y_spot, KEY_APPROACH)
    b_spot = pass_spot(md, ed_b)
    b_start, b_angle, b_family, b_tics = pass_walk(md, b_spot, KEY_APPROACH)

    swa = switch_line(md, tag_sha, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_shb, "SW-B")
    swb_point, swb_angle = approach(md, swb)

    # D2 and the exit switch on one line: press the door, walk to the switch.
    d2_faces = [ld for ld in tm.linedefs if ld.special == DAM_SPECIAL_DOOR_RAISE and ld.arg0 == tag_d2
                and zone_family(md.name_of(tm.sidedefs[ld.sidefront].sector)) == DAM_CREST_FAMILY]
    d2_point, d2_angle = approach(md, _longest(md, d2_faces, f"D2's {DAM_CREST_FAMILY} face"))
    exit_line = _longest(md, [ld for ld in tm.linedefs if ld.special == SPECIAL_EXIT_NORMAL], "the exit switch")
    exit_mid, exit_angle = approach(md, exit_line, 0)
    if exit_angle != d2_angle or (d2_point[0] - exit_mid[0]) * (d2_point[1] - exit_mid[1]) != 0:
        raise RouteError(f"D2 at {d2_point} facing {d2_angle} and the exit switch at {exit_mid} "
                         f"facing {exit_angle} are not on one line")
    e0_tics = walk_tics(math.dist(d2_point, exit_mid) - PLAYER_RADIUS)
    exit_family = zone_family(md.name_of(tm.sidedefs[exit_line.sidefront].sector))

    press = ("use", f"wait {DOOR_WAIT}")
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start (off MAP04's armoured train): no key; monsters on this skill"),
        Step("BG0", bg.point, bg.angle, press + (f"tag {tag_bg}", "inv", "capture"),
             expect=(bg_family,), tags=((tag_bg, False),), keys=0, presses=((locked, tag_bg),),
             note=f"the blue gate (lock {lock_b}) pressed with no key: pressed, and still shut"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", f"tag {tag_sluice}", "inv", "capture"),
             expect=(yd_family,), tags=((tag_yd, False), (tag_sluice, False)), keys=0,
             presses=((locked, tag_yd),),
             note=f"the yellow door (lock {lock_y}) on the catwalk pressed with no key: still shut; "
                  "the sluice's wall still standing"),
        Step("YKEY", y_start, y_angle,
             (f"forward {y_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_yd}", f"tag {tag_bg}",
              f"tag {tag_sluice}", "capture"),
             expect=(y_family,), tags=((tag_yd, False), (tag_bg, False), (tag_sluice, True)), keys=1,
             note=f"walk onto the yellow key (DoomEdNum {ed_y} at {y_spot}) on the spillway's "
                  "winch house, no give: one key; both locks still shut; its pickup has brought "
                  "the sluice's wall down (V3, A3: the dam bursts)"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"forward {yd.tics}", "capture"),
             expect=(yd.inside,), tags=((tag_yd, True),), presses=((locked, tag_yd),),
             note="the yellow door with its key: open (and the catwalk's closets); into the control room"),
        Step("SWA", swa_point, swa_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sha}", f"tag {tag_shb}", f"tag {tag_store}",
              "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_sha, True), (tag_shb, False), (tag_store, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A: the cable gallery's shutter opens; the station's shutter and the "
                  "substation's tool store still shut"),
        Step("BKEY", b_start, b_angle,
             (f"forward {b_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_bg}", f"tag {tag_shb}",
              f"tag {tag_store}", "capture"),
             expect=(b_family,), tags=((tag_bg, False), (tag_shb, False), (tag_store, True)), keys=2,
             note=f"walk onto the blue key (DoomEdNum {ed_b} at {b_spot}) on the substation's "
                  "pad, no give: two keys; the blue gate and the station's shutter still shut; "
                  "its pickup has opened the tool store (V3, A2)"),
        Step("SWB", swb_point, swb_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_shb}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_shb, True),),
             presses=((swb.special, swb.arg0),),
             note="SW-B: the shutter into the station opens, the shortcut back"),
        Step("BG1", bg.point, bg.angle, press + (f"tag {tag_bg}", f"forward {bg.tics}", "capture"),
             expect=(bg.inside,), tags=((tag_bg, True),), presses=((locked, tag_bg),),
             note="the blue gate with its key: open (and the station's closets); onto the crest"),
        Step("E0", d2_point, d2_angle,
             press + (f"tag {tag_d2}", "capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,), tags=((tag_d2, True),), presses=((DAM_SPECIAL_DOOR_RAISE, tag_d2),),
             note="D2, the west bank's door, pressed from the crest; through it to the exit switch"),
        Step("E1", actions=("use",), note="the exit switch: on to MAP06"),
    )
    return Route("dam-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="the dam's critical path: both locks shut without keys, the yellow key "
                             "across the spillway and its door, SW-A, the blue key in the substation, "
                             "SW-B, the blue gate onto the crest, D2, the exit switch")


# --- MAP04 «Транссиб» / Trans-Siberian: the critical path ----------------------
# (docs/levels/MAP04-transsib.md, "Progression"). tankograd-critical's method
# on the Sverdlovsk yard, episode 2's first map. Read off the built map, never
# copied: the tags, the lock numbers and the keys' editor numbers from the
# named constants of the map that defines TRANSSIB_CONSTANTS (TAG_HATCH and
# TURNTABLE are its own); each lock is the Door_LockedRaise face whose front
# sector is in the yard (TRANSSIB_YARD_FAMILY); each key the one thing of its
# number on skills 2-4, walked onto from TRANSSIB_KEY_APPROACH; SW-A and SW-B
# the one-sided switches on TAG_SHUTTER and TAG_HATCH; E0 on the ray out of the
# cab's exit niche, past the train's rear hatch (TAG_HATCH), so the walk down
# the train proves the hatch open. The yellow key lies on the signal box's
# lever frame, reached in play along the boxcars' roofs: the route warps into
# the box, as tankograd-critical warps to the director's desk. The red key's
# pickup drops two gondolas' sides in the yard (Floor_LowerToLowest on a tag no
# line carries); their troops may stand in a later walk, and sdclear names
# them as blockers. V3 (A2): the yellow key's pickup opens the platelayers'
# hut (Door_Open on TAG_YARD_HUT, no line carries it): RD0 reads it shut,
# YKEY waits a door's rise and reads it open, so the engine pass proves the
# pickup's door. Where the exit leads is MAPINFO's `next`, as for every
# route.
TRANSSIB_CONSTANTS = ("TAG_YELLOW_DOOR", "TAG_RED_DOOR", "TAG_SHUTTER", "TAG_HATCH",
                      "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_YELLOW_CARD", "LOCK_RED_CARD",
                      "ED_YELLOW_CARD", "ED_RED_CARD", "TURNTABLE", "TAG_YARD_HUT")
TRANSSIB_YARD_FAMILY = "Z2"     # both locks are pressed from the yard's portal bands
TRANSSIB_KEY_APPROACH = 96      # the lever frame and the king post are 64 square, 16 up


def transsib_critical(md: "MapData | None" = None) -> Route:
    """The Sverdlovsk yard's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*TRANSSIB_CONSTANTS))
    (tag_yd, tag_rd, tag_sh, tag_hatch, locked, lock_y, lock_r, ed_y, ed_r, _turntable, tag_hut) = (
        _map_const(md, n) for n in TRANSSIB_CONSTANTS)

    a0_family = start_family(md)
    yd = locked_door_walk(md, locked, tag_yd, TRANSSIB_YARD_FAMILY, "the yellow door", lock_y)
    rd = locked_door_walk(md, locked, tag_rd, TRANSSIB_YARD_FAMILY, "the red door", lock_r)
    yd_family, rd_family = family_at(md, yd.point), family_at(md, rd.point)

    y_spot = pass_spot(md, ed_y)
    y_start, y_angle, y_family, y_tics = pass_walk(md, y_spot, TRANSSIB_KEY_APPROACH)
    r_spot = pass_spot(md, ed_r)
    r_start, r_angle, r_family, r_tics = pass_walk(md, r_spot, TRANSSIB_KEY_APPROACH)

    swa = switch_line(md, tag_sh, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_hatch, "SW-B")
    swb_point, swb_angle = approach(md, swb)

    e0_point, exit_angle, e0_tics, exit_family = exit_walk(md, tag_hatch, "the train's rear hatch")

    press = ("use", f"wait {DOOR_WAIT}")
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start, in the service tunnel from Tankograd: no key"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", "inv", "capture"),
             expect=(yd_family,), tags=((tag_yd, False),), keys=0, presses=((locked, tag_yd),),
             note=f"the yellow door (lock {lock_y}) pressed with no key: pressed, and still shut"),
        Step("RD0", rd.point, rd.angle, press + (f"tag {tag_rd}", f"tag {tag_hut}", "inv", "capture"),
             expect=(rd_family,), tags=((tag_rd, False), (tag_hut, False)), keys=0,
             presses=((locked, tag_rd),),
             note=f"the red door (lock {lock_r}) pressed with no key: pressed, and still shut; "
                  "the platelayers' hut shut"),
        Step("YKEY", y_start, y_angle,
             (f"forward {y_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_yd}", f"tag {tag_rd}",
              f"tag {tag_hut}", "capture"),
             expect=(y_family,), tags=((tag_yd, False), (tag_rd, False), (tag_hut, True)), keys=1,
             note=f"walk onto the yellow key on the signal box's lever frame (DoomEdNum {ed_y} "
                  f"at {y_spot}), no give: one key; both doors still shut, and its pickup has "
                  "opened the platelayers' hut (V3, A2: the item special's Door_Open)"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"forward {yd.tics}", "capture"),
             expect=(yd.inside,), tags=((tag_yd, True),), presses=((locked, tag_yd),),
             note="the yellow door with its key: open; walk through it to the goods warehouse"),
        Step("RDY", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(rd_family,), tags=((tag_rd, False),), keys=1, presses=((locked, tag_rd),),
             note="the red door pressed with the yellow key only: still shut"),
        Step("RKEY", r_start, r_angle,
             (f"forward {r_tics}", "inv", f"tag {tag_rd}", f"tag {tag_sh}", "capture"),
             expect=(r_family,), tags=((tag_rd, False), (tag_sh, False)), keys=2,
             note=f"walk onto the red key on the turntable's king post (DoomEdNum {ed_r} at "
                  f"{r_spot}), no give: two keys; the red door and the road gate still shut"),
        Step("SWA", swa_point, swa_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sh}", f"tag {tag_hatch}", "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_sh, True), (tag_hatch, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A: the roundhouse's road gate opens onto the yard; the hatch still shut"),
        Step("RD1", rd.point, rd.angle, press + (f"tag {tag_rd}", f"forward {rd.tics}", "capture"),
             expect=(rd.inside,), tags=((tag_rd, True),), presses=((locked, tag_rd),),
             note="the red door with its key: open; walk through it to the platform"),
        Step("SWB", swb_point, swb_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_hatch}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_hatch, True),),
             presses=((swb.special, swb.arg0),),
             note="SW-B in the stationmaster's office: the armoured train's rear hatch opens"),
        Step("E0", e0_point, exit_angle, ("capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,),
             note="from the rear balcony, through the hatch and down the train to the cab"),
        Step("E1", actions=("use",), note="the locomotive's regulator: the exit"),
    )
    return Route("transsib-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="the Sverdlovsk yard's critical path: both locks shut without keys, the "
                             "yellow key on the signal box's frame and its door, the red door shut on "
                             "the yellow key, the red key on the turntable, SW-A, the red door, SW-B, "
                             "the train's hatch, the regulator in the cab")


# --- MAP06 Red Square: the critical path (docs/levels/MAP06-red-square.md 5, 13)
# tankograd-critical's method with three keys and a boss whose death opens the
# exit. Nothing is a copied coordinate or a class name; what the route reads:
#   * tags, the locked-door special, the three locks and the three keys'
#     editor numbers: the named constants of src/maps/MAP06/map.py
#     (REDSQUARE_CONSTANTS);
#   * each locked door: the Door_LockedRaise line with its tag AND its lock
#     whose front sector is in the family the design presses it from (the
#     blue door from the GUM's arcade, Z4; the yellow and red from the square,
#     Z6), walked through DOOR_CLEARANCE past its far face;
#   * each key: the one thing of its editor number on skills 2, 3 and 4,
#     walked onto, never given; the red key's pickup opens TAG_AMBUSH (the
#     museum's closets), so RKEY expects that tag open: the item special is
#     the map's one NOT VERIFIED mechanism the route can see;
#   * the boss: the class of map.py's BOSS_KIND (MONSTER_KINDS ->
#     MONSTER_CLASSES), which must be one the helper can hurt (COUNT_CLASSES);
#     BOSS0 stands in the courtyard with the exit gate (TAG_BOSS_EXIT) shut,
#     BOSS1 hurts him past his health and expects the gate open: his death
#     special, nothing else, opens it (no line carries the tag);
#   * the exit: E0 on the ray out of the exit's niche, past the exit gate.
# Keys are COUNTED (0..3), never named. The order is the design's: the blue
# door refused, the blue key on the GUM's bridge, the blue door; the yellow and
# red doors refused on the blue key; the yellow key on the north stand, the
# yellow gatehouse; the red door refused on two keys; the red key in the
# vehicle park (the closets open); the Spasskaya gate; the boss; the exit.
# V3 (A3): the yellow key's pickup brings the barriers down
# (Floor_LowerToLowest on TAG_RESURRECTION: the Resurrection gate's two
# barricades and the reserve's courtyard gate): YD0 reads the tag shut (the
# courtyard gate is floor = ceiling), YKEY waits and reads it open, so the
# engine pass proves a pickup's Floor_LowerToLowest.
REDSQUARE_CONSTANTS = ("TAG_BLUE_DOOR", "TAG_YELLOW_DOOR", "TAG_RED_DOOR", "TAG_AMBUSH",
                       "TAG_BOSS_EXIT", "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_BLUE_CARD",
                       "LOCK_YELLOW_CARD", "LOCK_RED_CARD", "ED_BLUE_CARD", "ED_YELLOW_CARD",
                       "ED_RED_CARD", "MAP06_BOSS_SPOT", "BOSS_KIND", "TAG_RESURRECTION")
REDSQUARE_GUM_FAMILY = "Z4"       # the blue door is pressed from the GUM's arcade
REDSQUARE_SQUARE_FAMILY = "Z6"    # the yellow and red doors from Red Square
REDSQUARE_ARENA_FAMILY = "Z9"     # the Kremlin courtyard, where the boss stands
BOSS_HURT = 100000                # far past any boss's health: one netevent kills him
BOSS_WAIT = 105                   # his death, then Door_Open's rise at speed 16


def redsquare_critical(md: "MapData | None" = None) -> Route:
    """MAP06's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*REDSQUARE_CONSTANTS))
    (tag_bd, tag_yd, tag_rd, tag_amb, tag_exit, locked, lock_b, lock_y, lock_r,
     ed_b, ed_y, ed_r, boss_spot, boss_kind, tag_res) = (_map_const(md, n) for n in REDSQUARE_CONSTANTS)
    kinds, classes = _map_const(md, "MONSTER_KINDS"), _map_const(md, "MONSTER_CLASSES")
    boss_class = classes[kinds[boss_kind]]
    if boss_class not in COUNT_CLASSES:
        raise RouteError(f"the boss {boss_class} is not in COUNT_CLASSES: the helper cannot hurt it")
    if family_at(md, boss_spot) != REDSQUARE_ARENA_FAMILY:
        raise RouteError(f"MAP06_BOSS_SPOT {boss_spot} is not in the courtyard ({REDSQUARE_ARENA_FAMILY})")

    a0_family = start_family(md)
    bd = locked_door_walk(md, locked, tag_bd, REDSQUARE_GUM_FAMILY, "the blue door", lock_b)
    yd = locked_door_walk(md, locked, tag_yd, REDSQUARE_SQUARE_FAMILY, "the yellow door", lock_y)
    rd = locked_door_walk(md, locked, tag_rd, REDSQUARE_SQUARE_FAMILY, "the red door", lock_r)
    walks = {}
    for name, ed in (("b", ed_b), ("y", ed_y), ("r", ed_r)):
        spot = pass_spot(md, ed)
        walks[name] = (spot,) + pass_walk(md, spot, KEY_APPROACH)   # two of them lie on raised tops

    # BOSS0/BOSS1 stand where the gate's passage opens into the courtyard:
    # on the red door's line, a body's width inside the courtyard.
    dx, dy = COMPASS[rd.angle]
    for t in range(SAMPLE_UNITS, MAX_RAY, SAMPLE_UNITS):
        if family_at(md, (rd.point[0] + dx * t, rd.point[1] + dy * t)) == REDSQUARE_ARENA_FAMILY:
            break
    else:
        raise RouteError(f"the ray through the red door never reaches {REDSQUARE_ARENA_FAMILY}")
    t += 2 * PLAYER_RADIUS
    arena_point = (rd.point[0] + dx * t, rd.point[1] + dy * t)
    e0_point, exit_angle, e0_tics, exit_family = exit_walk(md, tag_exit, "the exit gate")

    press = ("use", f"wait {DOOR_WAIT}")
    (b_spot, b_start, b_angle, b_family, b_tics) = walks["b"]
    (y_spot, y_start, y_angle, y_family, y_tics) = walks["y"]
    (r_spot, r_start, r_angle, r_family, r_tics) = walks["r"]
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start in the station's hall: no key; monsters on this skill"),
        Step("BD0", bd.point, bd.angle, press + (f"tag {tag_bd}", "inv", "capture"),
             expect=(family_at(md, bd.point),), tags=((tag_bd, False),), keys=0,
             presses=((locked, tag_bd),),
             note=f"the GUM's blue door (lock {lock_b}) pressed with no key: still shut"),
        Step("BKEY", b_start, b_angle, (f"forward {b_tics}", "inv", f"tag {tag_bd}", "capture"),
             expect=(b_family,), tags=((tag_bd, False),), keys=1,
             note=f"walk onto the blue key on the bridge (DoomEdNum {ed_b} at {b_spot}): one key"),
        Step("BD1", bd.point, bd.angle, press + (f"tag {tag_bd}", f"forward {bd.tics}", "capture"),
             expect=(bd.inside,), tags=((tag_bd, True),), presses=((locked, tag_bd),),
             note="the blue door with its key: open; walk through it onto Red Square"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", f"tag {tag_res}", "inv", "capture"),
             expect=(family_at(md, yd.point),), tags=((tag_yd, False), (tag_res, False)), keys=1,
             presses=((locked, tag_yd),),
             note=f"the yellow gatehouse (lock {lock_y}) pressed with the blue key: still shut; "
                  "the barriers still up"),
        Step("RD0", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(family_at(md, rd.point),), tags=((tag_rd, False),), keys=1,
             presses=((locked, tag_rd),),
             note=f"the Spasskaya gate (lock {lock_r}) pressed with the blue key: still shut"),
        Step("YKEY", y_start, y_angle,
             (f"forward {y_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_yd}", f"tag {tag_res}", "capture"),
             expect=(y_family,), tags=((tag_yd, False), (tag_res, True)), keys=2,
             note=f"up the north stand onto the yellow key (DoomEdNum {ed_y} at {y_spot}): two keys; "
                  "its pickup has brought the barriers down (V3, A3: Floor_LowerToLowest)"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"forward {yd.tics}", "capture"),
             expect=(yd.inside,), tags=((tag_yd, True),), presses=((locked, tag_yd),),
             note="the yellow gatehouse with its key: open; walk through to the vehicle park"),
        Step("RDY", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(family_at(md, rd.point),), tags=((tag_rd, False),), keys=2,
             presses=((locked, tag_rd),),
             note="the Spasskaya gate pressed with the blue and yellow keys: still shut"),
        Step("RKEY", r_start, r_angle,
             (f"forward {r_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_rd}", f"tag {tag_amb}",
              "capture"),
             expect=(r_family,), tags=((tag_rd, False), (tag_amb, True)), keys=3,
             note=f"walk onto the red key (DoomEdNum {ed_r} at {r_spot}): three keys, and its "
                  "pickup opens the museum's closets (the item special, NOT VERIFIED until this passes)"),
        Step("RD1", rd.point, rd.angle, press + (f"tag {tag_rd}", f"forward {rd.tics}", "capture"),
             expect=(rd.inside,), tags=((tag_rd, True),), presses=((locked, tag_rd),),
             note="the Spasskaya gate with its key: open; walk through the passage"),
        Step("BOSS0", arena_point, rd.angle, (f"tag {tag_exit}", "count", "capture"),
             expect=(family_at(md, arena_point),), tags=((tag_exit, False),),
             note=f"in the Kremlin courtyard: the exit gate is shut while the boss ({boss_class}) lives"),
        Step("BOSS1", actions=(f"hurt {boss_class} {BOSS_HURT}", f"wait {BOSS_WAIT}",
                               f"tag {tag_exit}", "count", "capture"),
             tags=((tag_exit, True),),
             note="the boss killed (helper damage): his death special opens the exit gate"),
        Step("E0", e0_point, exit_angle, ("capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,),
             note="through the exit gate, down the hall to the exit switch"),
        Step("E1", actions=("use",), note="the exit switch: episode 2's end"),
    )
    return Route("redsquare-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="Red Square's critical path: the blue door refused, the blue key on the "
                             "GUM's bridge, the blue door, the yellow and red gates refused, the "
                             "yellow key on the stand, the yellow gatehouse, the red key (the "
                             "closets open), the Spasskaya gate, the boss killed, his gate, the exit")

# --- MAP09 Tunguska: the critical path (docs/levels/MAP09-tunguska.md 5, 14)
# redsquare-critical's method on the campaign's last map: three keys, a key
# whose pickup springs an ambush, and a boss whose death opens the exit.
# Nothing is a copied coordinate or a class name; what the route reads:
#   * tags, the locked-door special, the three locks and the three keys'
#     editor numbers: the named constants of src/maps/MAP09/map.py
#     (TUNGUSKA_CONSTANTS);
#   * each locked door: the Door_LockedRaise line with its tag AND its lock
#     whose front sector is in the family the design presses it from (the
#     blue gate from the station's yard, Z3; the yellow door and the red gate
#     from the works, Z5), walked through DOOR_CLEARANCE past its far face;
#   * each key: the one thing of its editor number on skills 2, 3 and 4,
#     walked onto, never given; the red key's pickup opens TAG_AMBUSH (the
#     works' closets), so RKEY expects that tag open; since V3 (design
#     section 18) the blue key's opens TAG_QUARANTINE (the laboratory's
#     quarantine room, Door_Open), so BKEY waits and expects it open. The
#     yellow key's lift (TAG_WORKS_LIFT) is not asked: its car is always a
#     body high, so "open" would prove nothing (the checklist reads it);
#   * the boss: the class of map.py's BOSS_KIND, which must be one the helper
#     can hurt (COUNT_CLASSES); BOSS0 stands on the crater's first terrace
#     (Z8) with the bunker's gate (TAG_BOSS_EXIT) shut, BOSS1 hurts him past
#     his health and expects the gate open (no line carries the tag). Since
#     D116 the boss is the Consortium (4000 HP since D119; 9000 before): one
#     hurt at full health kills it outright (its Breach is checked in its
#     chase, never in the damage). Should it be mid-Breach (65 tics invulnerable), the first hurt
#     does nothing, so BOSS1 hurts it again after TUNGUSKA_BREACH_WAIT; a
#     dead boss is not hurt twice (the helper skips health <= 0);
#   * the exit: E0 on the ray out of the exit's niche, past the bunker's gate.
# The order is the design's: the blue gate refused, the blue key in the
# laboratory, the blue gate; the yellow door and the red gate refused on the
# blue key; the yellow key on the derrick, the yellow door; the red gate
# refused on two keys; the red key in the refinery (the closets open); the
# red gate; the boss; the exit.
TUNGUSKA_CONSTANTS = ("TAG_BLUE_DOOR", "TAG_YELLOW_DOOR", "TAG_RED_DOOR", "TAG_AMBUSH",
                      "TAG_BOSS_EXIT", "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_BLUE_CARD",
                      "LOCK_YELLOW_CARD", "LOCK_RED_CARD", "ED_BLUE_CARD", "ED_YELLOW_CARD",
                      "ED_RED_CARD", "MAP09_BOSS_SPOT", "BOSS_KIND", "TAG_QUARANTINE")
TUNGUSKA_STATION_FAMILY = "Z3"    # the blue gate is pressed from the station's yard
TUNGUSKA_WORKS_FAMILY = "Z5"      # the yellow door and the red gate from the works
TUNGUSKA_CRATER_FAMILY = "Z8"     # the crater's terraces and floor, where the boss stands
TUNGUSKA_BREACH_WAIT = 70         # past the Consortium's Breach (65 tics invulnerable)


def tunguska_critical(md: "MapData | None" = None) -> Route:
    """MAP09's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*TUNGUSKA_CONSTANTS))
    (tag_bd, tag_yd, tag_rd, tag_amb, tag_exit, locked, lock_b, lock_y, lock_r,
     ed_b, ed_y, ed_r, boss_spot, boss_kind, tag_qr) = (_map_const(md, n) for n in TUNGUSKA_CONSTANTS)
    kinds, classes = _map_const(md, "MONSTER_KINDS"), _map_const(md, "MONSTER_CLASSES")
    boss_class = classes[kinds[boss_kind]]
    if boss_class not in COUNT_CLASSES:
        raise RouteError(f"the boss {boss_class} is not in COUNT_CLASSES: the helper cannot hurt it")
    if family_at(md, boss_spot) != TUNGUSKA_CRATER_FAMILY:
        raise RouteError(f"MAP09_BOSS_SPOT {boss_spot} is not in the crater ({TUNGUSKA_CRATER_FAMILY})")

    a0_family = start_family(md)
    bd = locked_door_walk(md, locked, tag_bd, TUNGUSKA_STATION_FAMILY, "the blue gate", lock_b)
    yd = locked_door_walk(md, locked, tag_yd, TUNGUSKA_WORKS_FAMILY, "the yellow door", lock_y)
    rd = locked_door_walk(md, locked, tag_rd, TUNGUSKA_WORKS_FAMILY, "the red gate", lock_r)
    walks = {}
    for name, ed in (("b", ed_b), ("y", ed_y), ("r", ed_r)):
        spot = pass_spot(md, ed)
        walks[name] = (spot,) + pass_walk(md, spot, KEY_APPROACH)

    # BOSS0/BOSS1 stand where the red gate's porch opens onto the crater: on
    # the gate's line, a body's width onto the first terrace.
    dx, dy = COMPASS[rd.angle]
    for t in range(SAMPLE_UNITS, MAX_RAY, SAMPLE_UNITS):
        if family_at(md, (rd.point[0] + dx * t, rd.point[1] + dy * t)) == TUNGUSKA_CRATER_FAMILY:
            break
    else:
        raise RouteError(f"the ray through the red gate never reaches {TUNGUSKA_CRATER_FAMILY}")
    t += 2 * PLAYER_RADIUS
    crater_point = (rd.point[0] + dx * t, rd.point[1] + dy * t)
    e0_point, exit_angle, e0_tics, exit_family = exit_walk(md, tag_exit, "the bunker's gate")

    press = ("use", f"wait {DOOR_WAIT}")
    (b_spot, b_start, b_angle, b_family, b_tics) = walks["b"]
    (y_spot, y_start, y_angle, y_family, y_tics) = walks["y"]
    (r_spot, r_start, r_angle, r_family, r_tics) = walks["r"]
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start on the railhead's platform: no key; monsters on this skill"),
        Step("BD0", bd.point, bd.angle, press + (f"tag {tag_bd}", "inv", "capture"),
             expect=(family_at(md, bd.point),), tags=((tag_bd, False),), keys=0,
             presses=((locked, tag_bd),),
             note=f"the blue gate in the invaders' fence (lock {lock_b}) pressed with no key: still shut"),
        Step("BKEY", b_start, b_angle,
             (f"forward {b_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_bd}", f"tag {tag_qr}", "capture"),
             expect=(b_family,), tags=((tag_bd, False), (tag_qr, True)), keys=1,
             note=f"walk onto the blue key on the laboratory's bench (DoomEdNum {ed_b} at {b_spot}): one key, "
                  "and its pickup opens the quarantine room (V3)"),
        Step("BD1", bd.point, bd.angle, press + (f"tag {tag_bd}", f"forward {bd.tics}", "capture"),
             expect=(bd.inside,), tags=((tag_bd, True),), presses=((locked, tag_bd),),
             note="the blue gate with its key: open; walk through it into the standing forest"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", "inv", "capture"),
             expect=(family_at(md, yd.point),), tags=((tag_yd, False),), keys=1,
             presses=((locked, tag_yd),),
             note=f"the refinery's yellow door (lock {lock_y}) pressed with the blue key: still shut"),
        Step("RD0", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(family_at(md, rd.point),), tags=((tag_rd, False),), keys=1,
             presses=((locked, tag_rd),),
             note=f"the crater's red gate (lock {lock_r}) pressed with the blue key: still shut"),
        Step("YKEY", y_start, y_angle, (f"forward {y_tics}", "inv", f"tag {tag_yd}", "capture"),
             expect=(y_family,), tags=((tag_yd, False),), keys=2,
             note=f"across the derrick onto the yellow key (DoomEdNum {ed_y} at {y_spot}): two keys"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"forward {yd.tics}", "capture"),
             expect=(yd.inside,), tags=((tag_yd, True),), presses=((locked, tag_yd),),
             note="the yellow door with its key: open; walk through into the refinery"),
        Step("RDY", rd.point, rd.angle, press + (f"tag {tag_rd}", "inv", "capture"),
             expect=(family_at(md, rd.point),), tags=((tag_rd, False),), keys=2,
             presses=((locked, tag_rd),),
             note="the red gate pressed with the blue and yellow keys: still shut"),
        Step("RKEY", r_start, r_angle,
             (f"forward {r_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_rd}", f"tag {tag_amb}",
              "capture"),
             expect=(r_family,), tags=((tag_rd, False), (tag_amb, True)), keys=3,
             note=f"walk onto the red key (DoomEdNum {ed_r} at {r_spot}): three keys, and its "
                  "pickup opens the works' closets (the item special, NOT VERIFIED until this passes)"),
        Step("RD1", rd.point, rd.angle, press + (f"tag {tag_rd}", f"forward {rd.tics}", "capture"),
             expect=(rd.inside,), tags=((tag_rd, True),), presses=((locked, tag_rd),),
             note="the red gate with its key: open; walk through onto the crater's rim"),
        Step("BOSS0", crater_point, rd.angle, (f"tag {tag_exit}", "count", "capture"),
             expect=(family_at(md, crater_point),), tags=((tag_exit, False),),
             note=f"on the crater's first terrace: the bunker's gate is shut while the boss ({boss_class}) lives"),
        Step("BOSS1", actions=(f"hurt {boss_class} {BOSS_HURT}", f"wait {TUNGUSKA_BREACH_WAIT}",
                               f"hurt {boss_class} {BOSS_HURT}", f"wait {BOSS_WAIT}",
                               f"tag {tag_exit}", "count", "capture"),
             tags=((tag_exit, True),),
             note="the boss killed (helper damage, again past a Breach): its death special "
                  "opens the bunker's gate"),
        Step("E0", e0_point, exit_angle, ("capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,),
             note="through the bunker's gate, down its hall to the portal's breaker"),
        Step("E1", actions=("use",), note="the breaker: the portal shuts, episode 3's end"),
    )
    return Route("tunguska-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="Tunguska's critical path: the blue gate refused, the blue key in the "
                             "laboratory, the blue gate, the yellow door and red gate refused, the "
                             "yellow key on the derrick, the yellow door, the red key (the closets "
                             "open), the red gate, the boss killed, his gate, the breaker")


# --- MAP07 Novaya Zemlya: the critical path (docs/levels/MAP07-novaya-zemlya.md 5, 13)
# dam-critical's method on the Arctic radar station, episode 3's first map.
# What the route reads, and where from (nothing copied, nothing named by class):
#   * tags, specials, the two locks and the two keys' editor numbers (6
#     yellow, 13 red: SD_YellowPass and SD_RedPass replace Doom's cards): the
#     named constants of src/maps/MAP07/map.py (ZEMLYA_CONSTANTS; RADOME is
#     the map's own, so no other map answers to the set);
#   * the yellow door: its Door_LockedRaise face (tag AND lock) in the
#     hangar's portal (family Z2); the red gate: its face in the runway's
#     portal (Z1); each walked through into the room beyond;
#   * each key: the one thing of its editor number on skills 2, 3 and 4,
#     walked onto from KEY_APPROACH (the yellow on a pad on the antenna's
#     platform, the red on a plinth in the test chamber);
#   * SW-A and SW-B: the one-sided switches whose arg0 is TAG_BUNKER_SHUTTER
#     and TAG_RUNWAY_SHUTTER;
#   * the exit: D3, the conning tower's MANUAL hatch (Door_Raise,
#     TAG_D3_HATCH), pressed from the deck's porch (Z11); the walk goes on
#     straight through it to the exit switch, on the same line;
#   * V3's pickup events (design section 17): the red key's sinks the
#     bunker's cell walls (TAG_BUNKER_CELLS, Floor_LowerToLowest), so RKEY
#     waits and expects that tag open (a wall sunk is a player's height
#     open). The yellow key's lift (TAG_RADAR_LIFT) is not asked: its car is
#     always a body high, so "open" would prove nothing (the engine
#     checklist's V19 reads its floor); the road's medikit is never taken.
# Order: both locks shut with no key (RG0, YD0); the yellow key; the yellow
# door; SW-A; the red key (the gate and the runway's shutter still shut, the
# cells open); SW-B, the shortcut; the red gate with its key; D3; the switch.
ZEMLYA_CONSTANTS = ("TAG_RED_GATE", "TAG_YELLOW_DOOR", "TAG_BUNKER_SHUTTER", "TAG_RUNWAY_SHUTTER",
                    "TAG_D3_HATCH", "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_RED_CARD", "LOCK_YELLOW_CARD",
                    "ED_RED_CARD", "ED_YELLOW_CARD", "RADOME", "TAG_BUNKER_CELLS")
ZEMLYA_YELLOW_FAMILY = "Z2"   # the yellow door is pressed from its portal in the hangar
ZEMLYA_RED_FAMILY = "Z1"      # the red gate from its portal at the runway's west end
ZEMLYA_DECK_FAMILY = "Z11"    # D3 from the hatch's porch on the submarine's deck
ZEMLYA_SPECIAL_DOOR_RAISE = 12   # Door_Raise, udmf.SPECIAL_DOOR_RAISE: D3 is a manual door


def zemlya_critical(md: "MapData | None" = None) -> Route:
    """MAP07's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*ZEMLYA_CONSTANTS))
    (tag_rg, tag_yd, tag_sha, tag_shb, tag_d3, locked, lock_r, lock_y, ed_r, ed_y, _radome, tag_cells) = (
        _map_const(md, n) for n in ZEMLYA_CONSTANTS)
    tm = md.textmap

    a0_family = start_family(md)
    yd = locked_door_walk(md, locked, tag_yd, ZEMLYA_YELLOW_FAMILY, "the yellow door", lock_y)
    rg = locked_door_walk(md, locked, tag_rg, ZEMLYA_RED_FAMILY, "the red gate", lock_r)
    yd_family, rg_family = family_at(md, yd.point), family_at(md, rg.point)

    y_spot = pass_spot(md, ed_y)
    y_start, y_angle, y_family, y_tics = pass_walk(md, y_spot, KEY_APPROACH)
    r_spot = pass_spot(md, ed_r)
    r_start, r_angle, r_family, r_tics = pass_walk(md, r_spot, KEY_APPROACH)

    swa = switch_line(md, tag_sha, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_shb, "SW-B")
    swb_point, swb_angle = approach(md, swb)

    # D3 and the exit switch on one line: press the hatch, walk to the switch.
    d3_faces = [ld for ld in tm.linedefs if ld.special == ZEMLYA_SPECIAL_DOOR_RAISE and ld.arg0 == tag_d3
                and zone_family(md.name_of(tm.sidedefs[ld.sidefront].sector)) == ZEMLYA_DECK_FAMILY]
    d3_point, d3_angle = approach(md, _longest(md, d3_faces, f"D3's {ZEMLYA_DECK_FAMILY} face"))
    exit_line = _longest(md, [ld for ld in tm.linedefs if ld.special == SPECIAL_EXIT_NORMAL], "the exit switch")
    exit_mid, exit_angle = approach(md, exit_line, 0)
    if exit_angle != d3_angle or (d3_point[0] - exit_mid[0]) * (d3_point[1] - exit_mid[1]) != 0:
        raise RouteError(f"D3 at {d3_point} facing {d3_angle} and the exit switch at {exit_mid} "
                         f"facing {exit_angle} are not on one line")
    e0_tics = walk_tics(math.dist(d3_point, exit_mid) - PLAYER_RADIUS)
    exit_family = zone_family(md.name_of(tm.sidedefs[exit_line.sidefront].sector))

    press = ("use", f"wait {DOOR_WAIT}")
    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start (off the Il-14 on the runway): no key; monsters on this skill"),
        Step("RG0", rg.point, rg.angle, press + (f"tag {tag_rg}", "inv", "capture"),
             expect=(rg_family,), tags=((tag_rg, False),), keys=0, presses=((locked, tag_rg),),
             note=f"the red gate (lock {lock_r}) pressed with no key: pressed, and still shut"),
        Step("YD0", yd.point, yd.angle, press + (f"tag {tag_yd}", "inv", "capture"),
             expect=(yd_family,), tags=((tag_yd, False),), keys=0, presses=((locked, tag_yd),),
             note=f"the yellow door (lock {lock_y}) in the hangar pressed with no key: still shut"),
        Step("YKEY", y_start, y_angle,
             (f"forward {y_tics}", "inv", f"tag {tag_yd}", f"tag {tag_rg}", "capture"),
             expect=(y_family,), tags=((tag_yd, False), (tag_rg, False)), keys=1,
             note=f"walk onto the yellow key (DoomEdNum {ed_y} at {y_spot}) on the antenna's "
                  "platform, no give: one key; both locks still shut"),
        Step("YD1", yd.point, yd.angle, press + (f"tag {tag_yd}", f"forward {yd.tics}", "capture"),
             expect=(yd.inside,), tags=((tag_yd, True),), presses=((locked, tag_yd),),
             note="the yellow door with its key: open (and the hangar's closets); into the command room"),
        Step("SWA", swa_point, swa_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sha}", f"tag {tag_shb}", "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_sha, True), (tag_shb, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A: the bunker's shutter opens; the runway's shutter still shut"),
        Step("RKEY", r_start, r_angle,
             (f"forward {r_tics}", f"wait {DOOR_WAIT}", "inv", f"tag {tag_rg}", f"tag {tag_shb}",
              f"tag {tag_cells}", "capture"),
             expect=(r_family,), tags=((tag_rg, False), (tag_shb, False), (tag_cells, True)), keys=2,
             note=f"walk onto the red key (DoomEdNum {ed_r} at {r_spot}) before the core, no "
                  "give: two keys; the red gate and the runway's shutter still shut; its pickup "
                  "sinks the cells' walls (Floor_LowerToLowest on an item, NOT VERIFIED until this passes)"),
        Step("SWB", swb_point, swb_angle,
             ("use", f"wait {SWITCH_WAIT}", f"tag {tag_shb}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_shb, True),),
             presses=((swb.special, swb.arg0),),
             note="SW-B at the escape stair's head: the shutter onto the runway opens, the shortcut"),
        Step("RG1", rg.point, rg.angle, press + (f"tag {tag_rg}", f"forward {rg.tics}", "capture"),
             expect=(rg.inside,), tags=((tag_rg, True),), presses=((locked, tag_rg),),
             note="the red gate with its key: open (and the runway's closets); onto the harbour road"),
        Step("E0", d3_point, d3_angle,
             press + (f"tag {tag_d3}", "capture", f"forward {e0_tics}", "capture"),
             expect=(exit_family,), tags=((tag_d3, True),), presses=((ZEMLYA_SPECIAL_DOOR_RAISE, tag_d3),),
             note="D3, the conning tower's hatch, pressed from the deck; through it to the exit switch"),
        Step("E1", actions=("use",), note="the exit switch: down the submarine, on to the next map"),
    )
    return Route("zemlya-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="Novaya Zemlya's critical path: both locks shut without keys, the yellow "
                             "key on the antenna's platform and its door, SW-A, the red key in the "
                             "bunker, SW-B, the red gate onto the harbour, D3, the exit switch")


# --- MAP08 «Североморск» / Severomorsk: the critical path ---------------------
# (docs/levels/MAP08-severomorsk.md 5, 13). dam-critical's method with three
# keys, on episode 3's submarine base. What the route reads, and where from:
#   * tags, the locked-door special, the three locks and the three keys'
#     editor numbers (5 blue, 6 yellow, 13 red): the named constants of the
#     map that defines SEVEROMORSK_CONSTANTS (TAG_WT_SHUTTER, the boat's
#     watertight door, is its own);
#   * each lock: its Door_LockedRaise face (tag AND lock) in its portal: the
#     red gate's in the container yard (Z2), the blue and the yellow door's
#     on the dock's north quay (Z3); each walked through into the room beyond;
#   * each key: the one thing of its number on skills 2-4, walked onto from
#     KEY_APPROACH, never given (tray, cart and lid are one step up);
#   * SW-A and SW-B: the one-sided switches on TAG_WT_SHUTTER (the boat's
#     control room) and TAG_BARRACKS_SHUTTER (the reactor's passage);
#   * the exit: the Exit_Normal line in the locomotive's cab; E0 stands in the
#     cab before it (the walk from the gate to the bay is the open tunnel);
#   * V3's pickup events (design section 18): the yellow key's sinks the
#     torpedo magazine's wall (TAG_MAGAZINE, Floor_LowerToLowest), so YKEY
#     waits and expects that tag open (a wall sunk is a player's height
#     open). The blue key's cradle (TAG_TORPEDO_LIFT) is not asked: its car
#     is always a body high, so "open" would prove nothing (the engine
#     checklist's V13 reads its floor).
# Order: the three locks refused with no key; SW-A; the blue key; the blue
# door; the yellow key (the magazine opens); the yellow door; the red key;
# SW-B, the way back; the red gate; the regulator. Where the exit leads is
# MAPINFO's `next`.
SEVEROMORSK_CONSTANTS = ("TAG_BLUE_DOOR", "TAG_YELLOW_DOOR", "TAG_RED_GATE", "TAG_WT_SHUTTER",
                         "TAG_BARRACKS_SHUTTER", "SPECIAL_DOOR_LOCKED_RAISE", "LOCK_BLUE_CARD",
                         "LOCK_YELLOW_CARD", "LOCK_RED_CARD", "ED_BLUE_CARD", "ED_YELLOW_CARD",
                         "ED_RED_CARD", "TAG_MAGAZINE")
SEVEROMORSK_YARD_FAMILY = "Z2"   # the red gate is pressed from its portal in the yard's cliff
SEVEROMORSK_DOCK_FAMILY = "Z3"   # the blue and yellow doors from their portals on the north quay


def severomorsk_critical(md: "MapData | None" = None) -> Route:
    """MAP08's critical path, read off the built map (see the block above)."""
    md = md or load_map_data(map_defining(*SEVEROMORSK_CONSTANTS))
    (tag_bd, tag_yd, tag_rg, tag_wt, tag_sh, locked, lock_b, lock_y, lock_r, ed_b, ed_y, ed_r, tag_mag) = (
        _map_const(md, n) for n in SEVEROMORSK_CONSTANTS)
    tm = md.textmap

    a0_family = start_family(md)
    rg = locked_door_walk(md, locked, tag_rg, SEVEROMORSK_YARD_FAMILY, "the red gate", lock_r)
    bd = locked_door_walk(md, locked, tag_bd, SEVEROMORSK_DOCK_FAMILY, "the blue door", lock_b)
    yd = locked_door_walk(md, locked, tag_yd, SEVEROMORSK_DOCK_FAMILY, "the yellow door", lock_y)

    walks = {}
    for ed in (ed_b, ed_y, ed_r):
        spot = pass_spot(md, ed)
        walks[ed] = (spot,) + pass_walk(md, spot, KEY_APPROACH)

    swa = switch_line(md, tag_wt, "SW-A")
    swa_point, swa_angle = approach(md, swa)
    swb = switch_line(md, tag_sh, "SW-B")
    swb_point, swb_angle = approach(md, swb)
    exit_line = _longest(md, [ld for ld in tm.linedefs if ld.special == SPECIAL_EXIT_NORMAL], "the exit switch")
    e0_point, e0_angle = approach(md, exit_line)

    def key_step(sid, ed, keys, tags, note, opens=()):
        """Walk onto a key; `tags` must stay shut, `opens` (its pickup's
        tags) must be open after a door's wait."""
        spot, start, angle, family, tics = walks[ed]
        wait = (f"wait {DOOR_WAIT}",) if opens else ()
        return Step(sid, start, angle,
                    (f"forward {tics}",) + wait + ("inv",) + tuple(f"tag {t}" for t in tags + opens) + ("capture",),
                    expect=(family,), tags=tuple((t, False) for t in tags) + tuple((t, True) for t in opens),
                    keys=keys, note=f"walk onto {note} (DoomEdNum {ed} at {spot}), no give")

    press = ("use", f"wait {DOOR_WAIT}")

    def refused(sid, door, tag, lock, what):
        return Step(sid, door.point, door.angle, press + (f"tag {tag}", "inv", "capture"),
                    expect=(family_at(md, door.point),), tags=((tag, False),), keys=0,
                    presses=((locked, tag),), note=f"{what} (lock {lock}) pressed with no key: still shut")

    def opened(sid, door, tag, note):
        return Step(sid, door.point, door.angle, press + (f"tag {tag}", f"forward {door.tics}", "capture"),
                    expect=(door.inside,), tags=((tag, True),), presses=((locked, tag),), note=note)

    steps = (
        Step("A0", actions=("level", "count", "inv", "capture"), expect=(a0_family,), keys=0,
             note="the player start on the outer pier (off MAP07's launch): no key"),
        refused("RG0", rg, tag_rg, lock_r, "the red gate of the rail tunnel"),
        refused("BD0", bd, tag_bd, lock_b, "the blue door on the north quay"),
        refused("YD0", yd, tag_yd, lock_y, "the yellow door on the north quay"),
        Step("SWA", swa_point, swa_angle, ("use", f"wait {SWITCH_WAIT}", f"tag {tag_wt}", f"tag {tag_sh}", "capture"),
             expect=(family_at(md, swa_point),), tags=((tag_wt, True), (tag_sh, False)),
             presses=((swa.special, swa.arg0),),
             note="SW-A in the boat's control room: the watertight door opens; the barracks' shutter still shut"),
        key_step("BKEY", ed_b, 1, (tag_bd, tag_yd, tag_rg), "the blue key on the torpedo room's tray"),
        opened("BD1", bd, tag_bd, "the blue door with its key: into the workshops"),
        key_step("YKEY", ed_y, 2, (tag_yd, tag_rg), "the yellow key on the torpedo cart (its pickup sinks "
                 "the magazine's wall: Floor_LowerToLowest on an item, NOT VERIFIED until this passes)",
                 opens=(tag_mag,)),
        opened("YD1", yd, tag_yd, "the yellow door with its key (and the tunnel's closets): down the rock tunnel"),
        key_step("RKEY", ed_r, 3, (tag_rg, tag_sh), "the red key on the reactor's lid"),
        Step("SWB", swb_point, swb_angle, ("use", f"wait {SWITCH_WAIT}", f"tag {tag_sh}", "capture"),
             expect=(family_at(md, swb_point),), tags=((tag_sh, True),), presses=((swb.special, swb.arg0),),
             note="SW-B in the passage: the shutter into the barracks opens, the way back"),
        opened("RG1", rg, tag_rg, "the red gate with its key (and the yard's closets): into the rail tunnel"),
        Step("E0", e0_point, e0_angle, ("capture",), expect=(family_at(md, e0_point),),
             note="in the locomotive's cab at the loading bay, before the regulator"),
        Step("E1", actions=("use",), note="the regulator: the goods train east, on to MAP09"),
    )
    return Route("severomorsk-critical", md.map_name, steps, expect_secrets=0,
                 **exit_expectation(md.map_name),
                 description="the submarine base's critical path: the three locks refused, SW-A in the "
                             "boat, the blue key in the torpedo room, the blue door, the yellow key in "
                             "the torpedo store, the yellow door, the red key on the reactor's lid, "
                             "SW-B, the red gate, the regulator in the locomotive's cab")


ED_PLAYER1_START = 1

# Which map each fixed route walks, found by its constants (D62 renumbers the
# slots), and where its exit must lead, read from MAPINFO (D60: MAP01 now
# leads to the metro; D62: the metro to the factory; only an episode's last
# map and the range end the game).
ZARYA = map_defining(*ZARYA_MARKERS)
RANGE = map_defining(*RANGE_MARKERS)
_ZARYA_EXIT = exit_expectation(ZARYA)
_RANGE_EXIT = exit_expectation(RANGE)

ROUTES: dict[str, Route] = {
    "g3-auto": Route(
        "g3-auto", ZARYA, _A_STEPS, expect_secrets=0, **_ZARYA_EXIT,
        description="section 17.10's automatic run A1-A12 plus the start inventory (A0) and "
                    "the dorm rack (R1): the critical path, no secret (also G3-5's zero-secret run)"),
    "g3-secrets": Route(
        "g3-secrets", ZARYA, _SECRET_STEPS, expect_secrets="all", **_ZARYA_EXIT,
        description="the same path with the three secrets of section 7 taken on the way"),
    "range-start": Route(
        "range-start", RANGE, _RANGE_STEPS, expect_secrets=None, must_exit=True, **_RANGE_EXIT,
        description="the practice range: the start inventory, the slot-1 pickup, and out by "
                    "its exit switch to the end text"),
    "range-door": Route(
        "range-door", RANGE, (_RANGE_A0, _RANGE_R1) + _RANGE_P4 + _RANGE_EXIT_STEPS,
        expect_secrets=None, must_exit=True, **_RANGE_EXIT,
        description="range-start plus P4: the gallery door opened from the passage side"),
    "mural": Route(
        "mural", ZARYA, _MURAL_STEPS, expect_secrets=None, must_exit=False,
        description="section 17.13's mural shots M1-M5 (run with --nomonsters)"),
}

# Routes read off a map that is still being built: made when first asked for,
# so a MAP02 caught mid-edit fails its own route and nothing else.
LAZY_ROUTES: dict[str, Callable[[], Route]] = {
    "metro-critical": metro_critical,
    "tankograd-critical": tankograd_critical,
    "transsib-critical": transsib_critical,
    "dam-critical": dam_critical,
    "redsquare-critical": redsquare_critical,
    "severomorsk-critical": severomorsk_critical,
    "zemlya-critical": zemlya_critical,
    "tunguska-critical": tunguska_critical,
}


def route_names() -> list[str]:
    return sorted(set(ROUTES) | set(LAZY_ROUTES))


def route_by_name(name: str) -> Route:
    if name in ROUTES:
        return ROUTES[name]
    if name in LAZY_ROUTES:
        return LAZY_ROUTES[name]()
    raise RouteError(f"no route {name!r} (known: {', '.join(route_names())})")


def all_routes() -> dict[str, Route]:
    """Every built-in route, the lazy ones built (a RouteError propagates)."""
    return {name: route_by_name(name) for name in route_names()}


EXIT_WAYS = ("switch", "console")


def route_from_json(data: dict) -> Route:
    """A route of your own: {"name", "map", "expect_secrets"?, "must_exit"?,
    "exit_by"?: "switch" | "console", "end_sequence"?: bool, "next_map"?: str,
    "steps": [{"id", "warp"?: [x, y], "angle"?, "do"?: [...], "expect"?: [...],
    "tags"?: {"10": true}, "melee"?: bool, "ready_slot"?, "ready_ammo"?,
    "key"?: bool, "keys"?: int, "presses"?: [[special, arg0], ...], "note"?}]}.

    "exit_by": "console" is the documented recourse for a map with no exit
    line: the route's `exit` action sends the helper's sdexit."""
    try:
        steps = tuple(
            Step(
                id=str(s["id"]),
                warp=tuple(int(v) for v in s["warp"]) if s.get("warp") is not None else None,
                angle=int(s["angle"]) if s.get("angle") is not None else None,
                actions=tuple(s.get("do", ())),
                expect=tuple(str(f).upper() for f in s.get("expect", ())),
                tags=tuple((int(k), bool(v)) for k, v in s.get("tags", {}).items()),
                note=str(s.get("note", "")),
                melee=bool(s["melee"]) if s.get("melee") is not None else None,
                ready_slot=int(s["ready_slot"]) if s.get("ready_slot") is not None else None,
                ready_ammo=int(s["ready_ammo"]) if s.get("ready_ammo") is not None else None,
                key=bool(s["key"]) if s.get("key") is not None else None,
                presses=tuple((int(p[0]), int(p[1])) for p in s.get("presses", ())),
                keys=int(s["keys"]) if s.get("keys") is not None else None,
            )
            for s in data["steps"]
        )
        route = Route(str(data.get("name", "custom")), str(data.get("map", ZARYA)).upper(),
                      steps, data.get("expect_secrets"), bool(data.get("must_exit", True)),
                      str(data.get("description", "")),
                      exit_by=str(data.get("exit_by", "switch")),
                      end_sequence=bool(data.get("end_sequence", False)),
                      next_map=str(data["next_map"]) if data.get("next_map") else None)
    except (KeyError, TypeError, IndexError) as exc:
        raise RouteError(f"malformed route file: {exc}") from exc
    if route.exit_by not in EXIT_WAYS:
        raise RouteError(f"exit_by {route.exit_by!r} must be one of {', '.join(EXIT_WAYS)}")
    for step in steps:
        if step.warp is not None and len(step.warp) != 2:
            raise RouteError(f"step {step.id}: warp needs [x, y]")
    return route


# ============================================================================
# Map data: what the map's own source says (no engine)
# ============================================================================

# Zone families: the report speaks of "Z3" or "the D6 door", not of sector 57.
# RANGE's five sectors (docs/levels/RANGE-practice-range.md section 3) carry
# no zone number, so they are named whole, and checked first; their
# families are RANGE's own, none shared with MAP01 (tests/test_route.py).
ZONE_NAMES: dict[str, str] = {
    "hall": "HALL", "exit_alcove": "EXIT", "gallery_door": "GDOOR",
    "gallery_passage": "PASSAGE", "gallery": "GALLERY",
}
# Most of MAP01's sector names carry their zone (`z3_corridor`,
# `lamp_z3_corridor_1`, `z1_ice_axe_rack`); the rest are mapped by prefix
# here. First match wins. Every row must match a sector of some map: a row
# that matches none is dead (tests/test_route.py).
ZONE_PREFIXES: tuple[tuple[str, str], ...] = (
    # A door's recess belongs to the room it is cut into, so that a player
    # still standing in front of a shut door is never counted as "in the door".
    ("d3_recess", "Z4"), ("d4_recess", "Z6"), ("d5_recess", "Z10"), ("d6_recess", "Z6B"),
    ("s1_", "S1"), ("s2_", "S2"), ("s3_", "S3"), ("sump_step", "S3"),
    ("prop_bunk", "Z1"), ("frame_d1_dorm", "Z1"), ("frame_d2_dorm", "Z1"),
    ("frame_d1_washroom", "Z2"), ("prop_basin", "Z2"), ("stall_", "Z2"),
    ("bulkhead_", "Z3"),
    ("prop_mess", "Z4"), ("tribune", "Z4"), ("prop_lectern", "Z4"),
    ("pipes_", "Z5"), ("crate_guard", "Z5B"), ("weapon_rack", "Z5B"),
    ("cradle_", "Z6A"), ("spine_", "Z6A"), ("rail_", "Z6A"),
    ("catwalk_", "Z6B"),
    ("step_down", "Z6"), ("lane_", "Z6"), ("gantry", "Z6"), ("plinth_c", "Z6"),
    ("crate_h", "Z6"), ("shadow_", "Z6"), ("closet_w", "Z6"), ("closet_e", "Z6"),
    # V3 A2's closets (PICKUP-EVENTS.md): MAP01's IZh hound off the service
    # corridor, its PPSh squad in the hangar; MAP02's armoury store (before
    # "closet_a", which is MAP01's fuel bay); MAP03's two office closets.
    ("closet_izh", "Z5"), ("closet_ppsh", "Z6"), ("closet_armoury", "B5"), ("closet_o", "OF"),
    ("fuel_", "Z7"), ("plinth_tank", "Z7"), ("closet_a", "Z7"),
    ("booth_window", "Z9"),
    ("airlock_", "Z8"), ("frame_d5", "Z8"),
    ("lenin_", "Z10"),
    # MAP02 (docs/levels/MAP02-metro.md section 4): the bunker's rooms are
    # B1-B5, and the pieces without a zone number go with the room they serve.
    # Its z-numbered sectors file by name, so MAP02 shares the Z families'
    # names with MAP01; a route never mixes maps.
    ("b1_", "B1"), ("b2_", "B2"), ("b3_", "B3"), ("b4_", "B4"), ("b5_", "B5"),
    ("cp_stair_", "B4"), ("cp_door", "CPD"), ("blast_door", "BD"),
    ("esc_", "ESC"), ("prop_turnstiles", "Z2"), ("arches_", "Z3"),
    ("coping_", "Z4"), ("stair_", "Z4"), ("sub_stair_", "Z8"),
    ("shutter", "SH"), ("gate", "GATE"),
    # MAP03 Tankograd (docs/levels/MAP03-factory.md sections 4 and 15): its
    # z-numbered sectors file by name (Z1 spur, Z2 dock, Z3 hall) and SH /
    # GATE above serve it too; the rest go by the letter of their part of the
    # works. The drum (dais, inner porch, the breaker's niche) is its own
    # family, so E0 ending in it proves the walk passed the gate.
    ("closet_h", "Z3"), ("prop_conveyor", "Z3"), ("prop_clerestory", "Z3"),
    ("yellow_door", "YD"), ("red_door", "RD"),
    ("o_", "OF"),                       # the offices, the yellow key's desk among them
    ("t_", "TL"),                       # the vestibule, the tank line, its pits, the pouring arch
    ("f_", "FD"),                       # the foundry: gallery, casting floor, platform, red key
    ("p_drum", "DR"), ("p_inner_porch", "DR"), ("p_dais_", "DR"), ("p_exit_niche", "DR"),
    ("p_", "PH"),                       # the antechamber, the portal hall, the booth, the porch
)
_ZONE_IN_NAME = re.compile(r"(?:^|_)(z\d+[ab]?)(?:_|$)")
_DOOR_NAME = re.compile(r"^(d\d)(?:_|$)")


def zone_family(name: str | None) -> str:
    """'lamp_z3_corridor_1' -> 'Z3'; 'd6' and 'd6_recess' -> 'D6'; '?' if unknown."""
    if not name:
        return "?"
    if name in ZONE_NAMES:
        return ZONE_NAMES[name]
    for prefix, family in ZONE_PREFIXES:
        if name.startswith(prefix):
            return family
    match = _ZONE_IN_NAME.search(name)
    if match:
        return match.group(1).upper()
    match = _DOOR_NAME.match(name)
    if match:
        return match.group(1).upper()
    return "?"


class MapData:
    """The map as its source builds it: sector names, monsters per skill,
    secret sectors, and which sector a point is in."""

    def __init__(self, map_name: str, src: Path = PROJECT_ROOT / "src"):
        from sdbuild.pk3 import _load_map_module  # the build's own importer

        script = src / "maps" / map_name / "map.py"
        if not script.is_file():
            raise RouteError(f"no map source {script}")
        module = _load_map_module(script, TOOLS_DIR)
        self.module = module          # its named constants (metro_critical reads them)
        self.map_name = map_name
        if hasattr(module, "build_plan"):
            self.textmap, self.plan = module.build_plan()
        elif hasattr(module, "build_textmap"):
            # A map without a zone plan (none today; RANGE had none until
            # d1e891f): positions, monsters, secrets and things still work;
            # zones read '?', so a route on it should not use `expect`.
            self.textmap, self.plan = module.build_textmap(), {}
        else:
            raise RouteError(f"{script} has neither build_plan() nor build_textmap()")
        self.names = {index: name for name, index in self.plan.items()}
        tm = self.textmap
        self._vertical = []
        for ld in tm.linedefs:
            a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
            if a.x == b.x:
                self._vertical.append((a.x, a.y, b.y, ld))

    def name_of(self, sector: int | None) -> str | None:
        return None if sector is None else self.names.get(sector)

    def sector_at(self, x: float, y: float) -> int | None:
        """Ray cast east to the nearest vertical line (the map is axis-aligned
        rectangles); the side of it we are on is our sector. The same method as
        tests/test_map01.py."""
        y = y + 0.25  # never exactly on a horizontal edge
        best = None
        for lx, y1, y2, ld in self._vertical:
            if lx <= x or not (min(y1, y2) < y < max(y1, y2)):
                continue
            if best is None or lx < best[0]:
                best = (lx, y1, y2, ld)
        if best is None:
            return None
        _, y1, y2, ld = best
        sides = self.textmap.sidedefs
        if y2 < y1:
            return sides[ld.sidefront].sector
        return sides[ld.sideback].sector if ld.sideback is not None else None

    def monsters_on(self, skill: int) -> int:
        return sum(1 for t in self.textmap.things
                   if t.type in MONSTER_EDNUMS and getattr(t, f"skill{skill}"))

    def things_on(self, ednum: int, skill: int) -> list:
        """The things of one editor number that spawn on `skill`."""
        return [t for t in self.textmap.things
                if t.type == ednum and getattr(t, f"skill{skill}")]

    def secret_sectors(self) -> list[int]:
        return [i for i, s in enumerate(self.textmap.sectors)
                if s.special & SECTOR_SPECIAL_SECRET]

    def families(self) -> set[str]:
        return {zone_family(n) for n in self.plan}


@functools.lru_cache(maxsize=None)
def load_map_data(map_name: str) -> MapData:
    """MapData, built once per process (a lazy route and its report share it)."""
    return MapData(map_name)


# ============================================================================
# The helper PK3 (tooling; never part of the mod)
# ============================================================================

def helper_zscript(minimal: bool = False) -> str:
    """The EventHandler's source. `minimal` keeps only the PM's proven part
    (angle, hurt, count), for when the extras do not compile."""
    names = ", ".join(f'"{n}"' for n in COUNT_CLASSES)
    core = f"""
    override void NetworkProcess(ConsoleEvent e)
    {{
        if (e.Name == "sdexit")
        {{
            // End the level as an exit line would: the console `exit` QUITS
            // GZDoom, it does not end the level.
            Console.Printf("SDTEST exitlevel map=%s", level.MapName);
            level.ExitLevel(0, false);
            return;
        }}
        if (e.Name == "sdlevel")
        {{
            Console.Printf("SDTEST level map=%s monsters=%d/%d secrets=%d/%d items=%d/%d time=%d",
                level.MapName, level.killed_monsters, level.total_monsters,
                level.found_secrets, level.total_secrets, level.found_items, level.total_items,
                level.maptime);
            return;
        }}
        if (e.Name == "sdtag")
        {{
            let tagged = level.CreateSectorTagIterator(e.Args[0]);
            int si;
            while ((si = tagged.Next()) >= 0)
            {{
                let sec = level.Sectors[si];
                Console.Printf("SDTEST tag %d sector=%d floor=%d ceil=%d", e.Args[0], si,
                    int(sec.CenterFloor()), int(sec.CenterCeiling()));
            }}
            return;
        }}
        let pmo = players[e.Player].mo;
        if (!pmo) return;
        // A warp keeps the body's velocity (PM, 21:15: E0 of range-door drifted
        // 39 units south after P4b's walk). Setting the facing stops the body,
        // and sdstop does only that: Actor.Vel and PlayerInfo.vel, both
        // writable in g4.14.2's gzdoom.pk3 (actors/actor.zs, player/player.zs).
        if (e.Name == "sdangle")
        {{
            pmo.angle = e.Args[0]; pmo.pitch = 0;
            pmo.Vel = (0, 0, 0); players[e.Player].vel = (0, 0);
            return;
        }}
        if (e.Name == "sdstop") {{ pmo.Vel = (0, 0, 0); players[e.Player].vel = (0, 0); return; }}
        if (e.Name == "sdclear")
        {{
            // Args: step, length of the walk ahead, half-width. Kills only
            // LIVE MONSTERS in that corridor, and names each one, so the
            // report can tell the route's kills from the player's.
            Vector2 dir = Actor.AngleToVector(pmo.angle, 1);
            let it = ThinkerIterator.Create("Actor");
            Actor a;
            int n = 0;
            while ((a = Actor(it.Next())) != null)
            {{
                if (!a.bIsMonster || a.health <= 0) continue;
                Vector2 d = pmo.Vec2To(a);
                double along = d dot dir;
                double across = abs(d.x * dir.y - d.y * dir.x);
                if (along < -e.Args[2] || along > e.Args[1] + e.Args[2] || across > e.Args[2]) continue;
                int hp = a.health;
                a.DamageMobj(pmo, pmo, hp + 1000, 'None', DMG_FORCED | DMG_THRUSTLESS | DMG_NO_FACTOR);
                Console.Printf("SDTEST cleared step=%d class=%s x=%d y=%d hp=%d dead=%d", e.Args[0],
                    a.GetClassName(), int(a.pos.x), int(a.pos.y), hp, a.health <= 0 ? 1 : 0);
                n++;
            }}
            Console.Printf("SDTEST clear step=%d killed=%d", e.Args[0], n);
            return;
        }}
        if (e.Name == "sdinv")
        {{
            // Weapons by SLOT (the classes are being renamed, D40), then the
            // raised one and the rounds in its primary pool. Keys by the Key
            // base class, never by name (MAP02's pass replaces Doom's blue card).
            int owned = 0, keys = 0;
            for (let item = pmo.Inv; item; item = item.Inv)
            {{
                if (item is "Key")
                {{
                    Console.Printf("SDTEST key class=%s", item.GetClassName());
                    keys++;
                    continue;
                }}
                let w = Weapon(item);
                if (!w) continue;
                bool wf; int ws, wi;
                [wf, ws, wi] = players[e.Player].weapons.LocateWeapon(w.GetClass());
                Console.Printf("SDTEST weapon class=%s slot=%d", w.GetClassName(), wf ? ws : -1);
                owned++;
            }}
            Name readyName = 'None';
            int readySlot = -1, readyAmmo = -1;
            let ready = players[e.Player].ReadyWeapon;
            if (ready)
            {{
                readyName = ready.GetClassName();
                bool rf; int rs, ri;
                [rf, rs, ri] = players[e.Player].weapons.LocateWeapon(ready.GetClass());
                if (rf) readySlot = rs;
                if (ready.Ammo1) readyAmmo = ready.Ammo1.Amount;
            }}
            Console.Printf("SDTEST inv weapons=%d ready=%s slot=%d ammo=%d keys=%d", owned, readyName,
                readySlot, readyAmmo, keys);
            return;
        }}
        if (e.Name == "sdpos")
        {{
            Console.Printf("SDTEST pos step=%d x=%d y=%d z=%d sector=%d angle=%d health=%d",
                e.Args[0], int(pmo.pos.x), int(pmo.pos.y), int(pmo.pos.z),
                pmo.CurSector.Index(), int(pmo.angle), pmo.health);
            return;
        }}"""
    proven = """
        if (e.Name == "sdhurt")
        {
            let it = ThinkerIterator.Create(NAMES[e.Args[0]]);
            Actor a; int n = 0;
            while ((a = Actor(it.Next())) != null)
                if (a.health > 0) { a.DamageMobj(pmo, pmo, e.Args[1], 'None'); n++; }
            Console.Printf("SDTEST hurt %s x%d by %d", NAMES[e.Args[0]], n, e.Args[1]);
            return;
        }
        if (e.Name == "sdcount")
        {
            for (int i = 0; i < NAMES.Size(); i++)
            {
                let it = ThinkerIterator.Create(NAMES[i]);
                Actor a; int alive = 0, total = 0;
                while ((a = Actor(it.Next())) != null) { total++; if (a.health > 0) alive++; }
                Console.Printf("SDTEST count %s total=%d alive=%d", NAMES[i], total, alive);
            }
        }
    }"""
    extras = """
    int lastSecrets;

    override void WorldLoaded(WorldEvent e)
    {
        lastSecrets = level.found_secrets;
        Console.Printf("SDTEST helper %s map=%s", "@VERSION@", level.MapName);
    }

    override void WorldTick()
    {
        if (level.found_secrets == lastSecrets) return;
        lastSecrets = level.found_secrets;
        int sec = -1;
        if (playeringame[0] && players[0].mo) sec = players[0].mo.CurSector.Index();
        Console.Printf("SDTEST secret found=%d/%d sector=%d", level.found_secrets, level.total_secrets, sec);
    }

    override void WorldLinePreActivated(WorldEvent e)
    {
        let ln = e.ActivatedLine;
        if (!ln) return;
        int front = ln.frontsector ? ln.frontsector.Index() : -1;
        int back = ln.backsector ? ln.backsector.Index() : -1;
        int byPlayer = (e.Thing && e.Thing.player) ? 1 : 0;
        Console.Printf("SDTEST line index=%d special=%d arg0=%d front=%d back=%d type=%d player=%d",
            ln.Index(), ln.special, ln.args[0], front, back, e.ActivationType, byPlayer);
    }

    override void WorldUnloaded(WorldEvent e)
    {
        Console.Printf("SDTEST unloaded map=%s next=%s kills=%d/%d secrets=%d/%d items=%d/%d time=%d",
            level.MapName, e.NextMap, level.killed_monsters, level.total_monsters,
            level.found_secrets, level.total_secrets, level.found_items, level.total_items,
            level.maptime);
    }
""".replace("@VERSION@", HELPER_VERSION)
    if minimal:
        body = """
    override void NetworkProcess(ConsoleEvent e)
    {
        let pmo = players[e.Player].mo;
        if (!pmo) return;
        if (e.Name == "sdangle") { pmo.angle = e.Args[0]; pmo.pitch = 0; return; }""" + proven
    else:
        body = extras + core + proven
    return (
        'version "4.12"\n'
        "// GENERATED by tools/route.py - QA tooling, NEVER part of the mod.\n"
        "// It lives in logs/route/ (gitignored) and is loaded with -file after\n"
        "// the mod PK3 for one scripted run. Console interface:\n"
        "//   netevent sdangle <deg>         set the view angle (pitch level) and stop the body\n"
        "//   netevent sdstop                stop the body (velocity 0), around every warp\n"
        "//   netevent sdhurt <idx> <amount> damage every live actor of NAMES[idx]\n"
        "//   netevent sdcount               live / total counts of NAMES\n"
        "//   netevent sdpos <step>          position, sector index, health\n"
        "//   netevent sdinv                 weapons owned by slot, the raised one, its rounds, keys\n"
        "//   netevent sdtag <tag>           floor / ceiling of each sector with the tag\n"
        "//   netevent sdlevel               kills, secrets, items, map time\n"
        "//   netevent sdclear <step> <len> <w> kill live monsters in the walk ahead\n"
        "//   netevent sdexit                end the level (the console `exit` quits)\n"
        "//   netevent sdstate               gamestate (1 intermission, 2 end text),\n"
        f"//                                  answered by {STATE_CLASS}, which outlives the level\n"
        f"class {HELPER_CLASS} : EventHandler\n"
        "{\n"
        f"    static const string NAMES[] = {{ {names} }};\n"
        + body
        + "\n}\n"
        + ("" if minimal else STATE_HANDLER)
    )


# The per-level helper is destroyed when its level ends, so it cannot say
# what comes after (the PM's first run: "gamestate intermission: NOT SEEN").
# A static handler lives across levels, but it did not answer either: the
# route-2 runs (20:50-20:52) printed no "SDTEST state" line, not even for the
# sdstate asked during RANGE's end text; inside a level it answers
# (gamestate=0 in range-door's log of 21:15, whose level never ended).
# Hypothesis, NOT VERIFIED, supported by that: GZDoom's
# `netevent` command is refused outside a level. Nothing is judged on it:
# the unload line names the end sequence, and the END screenshot (and
# RANGE's E1) shows what is on screen. Kept because it costs nothing and
# would corroborate if a later engine answers.
STATE_CLASS = "SDRouteState"
STATE_HANDLER = f"""
class {STATE_CLASS} : StaticEventHandler
{{
    override void NetworkProcess(ConsoleEvent e)
    {{
        if (e.Name == "sdstate") Console.Printf("SDTEST state gamestate=%d", gamestate);
    }}
}}
"""


def helper_mapinfo(minimal: bool = False) -> str:
    handlers = f'"{HELPER_CLASS}"' + ("" if minimal else f', "{STATE_CLASS}"')
    return f"gameinfo\n{{\n    AddEventHandlers = {handlers}\n}}\n"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def write_helper_pk3(out: Path = HELPER_PK3, minimal: bool = False) -> Path:
    """Write the helper PK3. Refuses any place the mod is built or shipped from."""
    for root in FORBIDDEN_HELPER_ROOTS:
        if _inside(out, root):
            raise RouteError(f"refusing to write the test helper into {root}: "
                             "it is tooling and must never reach the mod")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, text in (("zscript.txt", helper_zscript(minimal)), ("MAPINFO", helper_mapinfo(minimal))):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, text)
    return out


# ============================================================================
# The console sequence and the command line
# ============================================================================

def action_commands(action: str) -> list[str]:
    word, args = parse_action(action)
    if word == "use":
        return ["+use", f"wait {USE_HOLD_TICS}", "-use"]
    if word == "wait":
        return [f"wait {args[0]}"]
    if word == "forward":
        return ["+forward", f"wait {args[0]}", "-forward"]
    if word == "capture":
        return ["screenshot", f"wait {SHOT_SETTLE_TICS}"]
    if word == "count":
        return ["netevent sdcount", f"wait {SETTLE_TICS}"]
    if word == "level":
        return ["netevent sdlevel", f"wait {SETTLE_TICS}"]
    if word == "state":
        return ["netevent sdstate", f"wait {SETTLE_TICS}"]
    if word == "inv":
        return ["netevent sdinv", f"wait {SETTLE_TICS}"]
    if word == "exit":
        return ["netevent sdexit", f"wait {SETTLE_TICS}"]
    if word == "tag":
        return [f"netevent sdtag {args[0]}", f"wait {SETTLE_TICS}"]
    if word == "angle":
        return [f"netevent sdangle {args[0]}", f"wait {SETTLE_TICS}"]
    if word == "hurt":
        return [f"netevent sdhurt {COUNT_CLASSES.index(args[0])} {args[1]}", f"wait {SETTLE_TICS}"]
    raise RouteError(f"unhandled action {action!r}")  # pragma: no cover


def clear_commands(number: int, tics: int) -> list[str]:
    """Before a scripted walk: kill the live monsters standing in its way.

    The scripted +forward cannot step round a body: on the PM's first run
    (2026-10-13 20:36, skills 3 and 4) a Stormtrooper in the Z1-Z3 corridor
    stopped A1 and failed a map that is not broken. The helper kills only
    live monsters within CLEAR_HALF_WIDTH of the walk's line, from behind
    the player to the walk's length plus that margin, and names each one in
    the log, so the report can say a body was in the way and the kill count
    can tell the route's kills from the rest."""
    return [f"netevent sdclear {number} {tics * WALK_UNITS_PER_TIC} {CLEAR_HALF_WIDTH}",
            f"wait {SETTLE_TICS}"]


def warp_commands(warp: tuple[int, int], angle: int | None) -> list[str]:
    """Stop the body, warp, stop it again (by the facing, or by sdstop).

    The console `warp` moves the player and keeps his velocity. On the PM's
    run of 2026-10-13 21:15, range-door's E0 warped onto the start straight
    after P4b's 35-tic walk south and, before it walked west, glided ~39
    units south out of line with the exit alcove: it ended at (16, 345) in
    the hall instead of at the switch. A warp step must start at rest: the
    stop before the warp kills the glide, the one after kills anything
    picked up while the warp settles."""
    cmds = ["netevent sdstop", f"wait {SETTLE_TICS}",
            f"warp {warp[0]} {warp[1]}", f"wait {SETTLE_TICS}"]
    if angle is None:
        cmds += ["netevent sdstop", f"wait {SETTLE_TICS}"]
    return cmds


def step_commands(number: int, step: Step, clear: bool = True) -> list[str]:
    cmds = [f"echo SDSTEP {number} {step.id}"]
    if step.warp is not None:
        cmds += warp_commands(step.warp, step.angle)
    if step.angle is not None:
        cmds += [f"netevent sdangle {step.angle}", f"wait {SETTLE_TICS}"]
    for action in step.actions:
        word, args = parse_action(action)
        if clear and word == "forward":
            cmds += clear_commands(number, args[0])
        cmds += action_commands(action)
    cmds += [f"netevent sdpos {number}", f"wait {SETTLE_TICS}"]
    return cmds


END_STEP_ID = "END"


def route_commands(route: Route, god: bool = True, notarget: bool = False,
                   clear: bool = True) -> list[str]:
    cmds = [f"wait {LOAD_TICS}"]
    if god:
        cmds += ["god", f"wait {SETTLE_TICS}"]
    if notarget:
        cmds += ["notarget", f"wait {SETTLE_TICS}"]
    for number, step in enumerate(route.steps):
        cmds += step_commands(number, step, clear)
    # The end: the intermission (if the exit was reached) is what is on
    # screen now. Shoot it, ask for the game state, and quit.
    cmds += [f"echo SDSTEP {len(route.steps)} {END_STEP_ID}", f"wait {INTERMISSION_TICS}",
             "screenshot", f"wait {SHOT_SETTLE_TICS}", "netevent sdstate", f"wait {SETTLE_TICS}",
             f"wait {QUIT_SETTLE_TICS}", "quit"]
    return cmds


def console_sequence(route: Route, god: bool = True, notarget: bool = False,
                     clear: bool = True) -> str:
    text = "+" + "; ".join(route_commands(route, god, notarget, clear))
    if len(text) > MAX_SEQUENCE_CHARS:
        raise RouteError(f"console sequence is {len(text)} chars, over {MAX_SEQUENCE_CHARS}")
    return text


def sequence_tics(route: Route, god: bool = True, notarget: bool = False,
                  clear: bool = True) -> int:
    return sum(int(c.split()[1]) for c in route_commands(route, god, notarget, clear)
               if c.startswith("wait "))


def build_command(gzdoom: Path, iwad: Path, pk3: Path, helper: Path, log: Path,
                  shot_dir: Path, route: Route, skill: int, *, god: bool = True,
                  notarget: bool = False, nomonsters: bool = False,
                  window: tuple[int, int] | None = (smoke.SMOKE_WINDOW_W, smoke.SMOKE_WINDOW_H),
                  hide_weapon: bool = False, clear: bool = True,
                  extra: list[str] | None = None) -> list[str]:
    """smoke.build_command's order and tooling config, with the helper after
    the mod and the route's sequence instead of smoke's.

    `extra` goes straight to GZDoom AFTER the sequence, so a `+cvar` there
    runs only once the sequence's waits are over: settings the shots need
    are flags here instead (`hide_weapon`)."""
    argv = [str(gzdoom), "-config", str(smoke.TOOLING_CONFIG), "-iwad", str(iwad),
            "-file", str(pk3), str(helper), "+logfile", str(log),
            "-skill", str(skill), "+map", route.map_name, "-nosound"]
    if nomonsters:
        argv.append("-nomonsters")
    argv += ["+vid_fullscreen", "0"]
    if window is not None:
        argv += ["+win_w", str(window[0]), "+win_h", str(window[1])]
    # Walking speed is part of the route: +forward N tics covers ~8 units a
    # tic walking and twice that running. The tooling config is ours, so
    # pinning it here changes nobody's game.
    argv += ["+i_pauseinbackground", "0", "+cl_run", "0", "+screenshot_dir", str(shot_dir)]
    # Always set, both ways: the tooling config keeps what the last run set.
    argv += ["+r_drawplayersprites", "0" if hide_weapon else "1"]
    argv.append(console_sequence(route, god, notarget, clear))
    argv += list(extra or [])
    return argv


# ============================================================================
# Reading the log
# ============================================================================

RE_STEP = re.compile(r"^SDSTEP (\d+) (\S+)\s*$")
RE_POS = re.compile(r"^SDTEST pos step=(\d+) x=(-?\d+) y=(-?\d+) z=(-?\d+) sector=(-?\d+)"
                    r" angle=(-?\d+) health=(-?\d+)")
RE_TAG = re.compile(r"^SDTEST tag (\d+) sector=(\d+) floor=(-?\d+) ceil=(-?\d+)")
RE_LINE = re.compile(r"^SDTEST line index=(\d+) special=(\d+) arg0=(-?\d+) front=(-?\d+)"
                     r" back=(-?\d+) type=(\d+) player=([01])")
RE_SECRET = re.compile(r"^SDTEST secret found=(\d+)/(\d+) sector=(-?\d+)")
RE_LEVEL = re.compile(r"^SDTEST level map=(\S+) monsters=(\d+)/(\d+) secrets=(\d+)/(\d+)"
                      r" items=(\d+)/(\d+) time=(\d+)")
RE_UNLOADED = re.compile(r"^SDTEST unloaded map=(\S+) next=(\S*) kills=(\d+)/(\d+)"
                         r" secrets=(\d+)/(\d+) items=(\d+)/(\d+) time=(\d+)")
RE_STATE = re.compile(r"^SDTEST state gamestate=(\d+)")
RE_COUNT = re.compile(r"^SDTEST count (\S+) total=(\d+) alive=(\d+)")
RE_HELPER = re.compile(r"^SDTEST helper (\S+)")
RE_WEAPON = re.compile(r"^SDTEST weapon class=(\S+) slot=(-?\d+)")
# `keys=` since route-4; a route-3 log has none, and its key count is unknown.
RE_INV = re.compile(r"^SDTEST inv weapons=(\d+) ready=(\S+) slot=(-?\d+) ammo=(-?\d+)(?: keys=(\d+))?")
RE_KEY = re.compile(r"^SDTEST key class=(\S+)")
RE_CLEARED = re.compile(r"^SDTEST cleared step=(\d+) class=(\S+) x=(-?\d+) y=(-?\d+) hp=(-?\d+)"
                        r" dead=([01])")
RE_CLEAR = re.compile(r"^SDTEST clear step=(\d+) killed=(\d+)")
RE_EXITLEVEL = re.compile(r"^SDTEST exitlevel map=(\S+)")
RE_CAPTURED = re.compile(r"^Captured (\S+)")
# The `god` cheat's answer, STSTR_DQDON. Measured: the PM's run of
# 2026-10-13 20:36 (g4.14.2 on Freedoom 0.13.0) printed "God mode on.";
# GZDoom's own language.csv says "Degreelessness Mode ON" (Freedoom's
# strings replace it: hypothesis, not checked). Both are accepted.
RE_GOD = re.compile(r"^(God mode on|Degreelessness Mode ON|Invincible Mode ON)", re.I)
# The engine's own secret message: "A secret is revealed!" does reach the
# log (logs/gzdoom.log, 2026-10-13 16:21); the SDTEST secret line is the
# measured signal, this one is corroboration.
RE_SECRET_MESSAGE = re.compile(r"(?i)\bsecret\b")
# The blue pass in the engine's words: its pickup line ("Blue pass.") and the
# lock-2 lines LANGUAGE overrides (PD_BLUEC / PD_BLUECO, "You need a blue
# pass to ..."; Freedoom's "Blue passcard needed for this door."), English and
# Russian. Whether the locked-door midprint reaches the log is NOT VERIFIED
# (pickup and secret messages do). A line that also says "need" is a lock
# message: proof that the press reached a locked line at that step.
# MAP03's yellow and red keys are still Doom's (YellowCard, RedCard: no SD_
# class yet, LANGUAGE overrides none of their lines), so they speak in the
# engine's or Freedoom's words, whichever wins: "yellow" / "red" and "need"
# either way (NOT VERIFIED which text the PM's run prints), and the Russian
# stems in case the CEO's Russian build overrides them later.
RE_PASS_MESSAGE = re.compile(r"(?i)\b(?:blue|yellow|red)\b|синий|синяя|жёлт|желт|красн")
RE_LOCK_WORD = re.compile(r"(?i)\bneed|нуж")

_EXTRA = [(pid, re.compile(rx), why) for pid, rx, why in G3_EXTRA_PATTERNS]


@dataclass
class Pos:
    step: int
    x: int
    y: int
    z: int
    sector: int
    angle: int
    health: int


@dataclass
class LineUse:
    index: int
    special: int
    arg0: int
    front: int
    back: int
    kind: int
    by_player: bool
    step: int = -1      # the SDSTEP it was printed under


@dataclass
class Inventory:
    """One `sdinv` answer: weapons as (class, slot), the raised one, its rounds,
    and the keys (route-4; `key_count` None on an older helper's line)."""

    weapons: list[tuple[str, int]]
    ready: str
    ready_slot: int
    ammo: int
    keys: list[str] = field(default_factory=list)
    key_count: int | None = None

    def slots(self) -> set[int]:
        return {slot for _cls, slot in self.weapons}


@dataclass
class RouteLog:
    """Everything the run printed that the report needs."""

    smoke: smoke.LogReport
    extra_failures: list[smoke.LogHit] = field(default_factory=list)
    helper: str | None = None
    god: bool = False
    steps_seen: dict[int, str] = field(default_factory=dict)
    positions: dict[int, Pos] = field(default_factory=dict)
    tags: dict[int, list[list[tuple[int, int, int]]]] = field(default_factory=dict)
    tag_steps: dict[int, list[int]] = field(default_factory=dict)
    lines: list[LineUse] = field(default_factory=list)
    secrets: list[tuple[int, int, int]] = field(default_factory=list)  # found, total, sector
    secret_messages: list[str] = field(default_factory=list)
    levels: list[tuple] = field(default_factory=list)
    unloaded: list[tuple] = field(default_factory=list)
    states: list[int] = field(default_factory=list)
    counts: list[dict[str, tuple[int, int]]] = field(default_factory=list)
    captures: list[tuple[int, str]] = field(default_factory=list)  # (step number, file)
    inventory: dict[int, Inventory] = field(default_factory=dict)  # step number -> last answer
    # The route's own kills (sdclear): (step, class, x, y, hp, dead).
    cleared: list[tuple[int, str, int, int, int, bool]] = field(default_factory=list)
    clears: dict[int, int] = field(default_factory=dict)   # step -> sdclear calls answered
    exitlevel: list[str] = field(default_factory=list)     # maps ended by sdexit
    pass_messages: list[tuple[int, str]] = field(default_factory=list)  # (step, engine line)

    def lock_steps(self) -> set[int]:
        """Steps at which the engine said a key was needed."""
        return {step for step, text in self.pass_messages if RE_LOCK_WORD.search(text)}

    @property
    def failures(self) -> list[smoke.LogHit]:
        return sorted(self.smoke.failures + self.extra_failures, key=lambda h: h.lineno)


def scan_route_log(text: str, strict: bool = False) -> RouteLog:
    log = RouteLog(smoke=smoke.scan_log(text, strict=strict))
    current = -1
    count_block: dict[str, tuple[int, int]] | None = None
    tag_block_step: dict[int, int] = {}
    weapons: list[tuple[str, int]] = []   # the weapon lines before an inv line
    keys: list[str] = []                  # the key lines before an inv line
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not smoke.is_benign(line) and not any(h.lineno == lineno for h in log.smoke.failures):
            for pid, rx, why in _EXTRA:
                if rx.search(line):
                    log.extra_failures.append(smoke.LogHit(lineno, pid, why, line))
                    break
        if not line.startswith("SDTEST count"):
            count_block = None
        if m := RE_STEP.match(line):
            current = int(m.group(1))
            log.steps_seen[current] = m.group(2)
        elif m := RE_POS.match(line):
            p = Pos(*(int(g) for g in m.groups()))
            log.positions[p.step] = p
        elif m := RE_TAG.match(line):
            tag, sector, floor, ceil = (int(g) for g in m.groups())
            readings = log.tags.setdefault(tag, [])
            if tag_block_step.get(tag) != current or not readings:
                readings.append([])
                log.tag_steps.setdefault(tag, []).append(current)
                tag_block_step[tag] = current
            readings[-1].append((sector, floor, ceil))
        elif m := RE_LINE.match(line):
            g = m.groups()
            log.lines.append(LineUse(int(g[0]), int(g[1]), int(g[2]), int(g[3]), int(g[4]),
                                     int(g[5]), g[6] == "1", current))
        elif m := RE_SECRET.match(line):
            log.secrets.append(tuple(int(g) for g in m.groups()))
        elif m := RE_LEVEL.match(line):
            log.levels.append((m.group(1),) + tuple(int(g) for g in m.groups()[1:]))
        elif m := RE_UNLOADED.match(line):
            log.unloaded.append((m.group(1), m.group(2)) + tuple(int(g) for g in m.groups()[2:]))
        elif m := RE_STATE.match(line):
            log.states.append(int(m.group(1)))
        elif m := RE_COUNT.match(line):
            if count_block is None:
                count_block = {}
                log.counts.append(count_block)
            count_block[m.group(1)] = (int(m.group(2)), int(m.group(3)))
        elif m := RE_WEAPON.match(line):
            weapons.append((m.group(1), int(m.group(2))))
        elif m := RE_CLEARED.match(line):
            g = m.groups()
            log.cleared.append((int(g[0]), g[1], int(g[2]), int(g[3]), int(g[4]), g[5] == "1"))
        elif m := RE_CLEAR.match(line):
            step = int(m.group(1))
            log.clears[step] = log.clears.get(step, 0) + 1
        elif m := RE_EXITLEVEL.match(line):
            log.exitlevel.append(m.group(1))
        elif m := RE_KEY.match(line):
            keys.append(m.group(1))
        elif m := RE_INV.match(line):
            log.inventory[current] = Inventory(
                weapons, m.group(2), int(m.group(3)), int(m.group(4)), keys,
                int(m.group(5)) if m.group(5) is not None else None)
            weapons, keys = [], []
        elif m := RE_HELPER.match(line):
            log.helper = m.group(1)
        elif m := RE_CAPTURED.match(line):
            log.captures.append((current, m.group(1)))
        elif RE_GOD.match(line):
            log.god = True
        elif current >= 0 and not line.startswith("SDTEST") and RE_PASS_MESSAGE.search(line):
            log.pass_messages.append((current, line.strip()))
        elif not line.startswith("SDTEST") and RE_SECRET_MESSAGE.search(line):
            log.secret_messages.append(line.strip())
    return log


# ============================================================================
# The report
# ============================================================================

@dataclass
class StepResult:
    number: int
    step: Step
    pos: Pos | None
    sector_name: str | None
    family: str
    static_family: str | None
    ok: bool
    why: str


@dataclass
class SkillReport:
    route: Route
    skill: int
    log: RouteLog
    steps: list[StepResult]
    doors: list[tuple[str, bool, str]]          # (what, ok, detail)
    secrets_found: int | None
    secrets_total: int
    secrets_ok: bool
    exit_reached: bool
    exit_detail: str
    monsters_expected: int
    monsters_engine: int | None
    problems: list[str]
    run_problem: str | None = None
    inventory: list[tuple[str, bool, str]] = field(default_factory=list)  # (what, ok, detail)

    @property
    def passed(self) -> bool:
        return not self.problems and not self.log.failures and self.run_problem is None

    @property
    def zones_reached(self) -> list[str]:
        seen: list[str] = []
        for r in self.steps:
            if r.pos is not None and r.family not in seen:
                seen.append(r.family)
        return seen


def _door_open(readings: list[tuple[int, int, int]]) -> bool:
    return bool(readings) and all(ceil - floor >= PLAYER_HEIGHT for _s, floor, ceil in readings)


def evaluate(route: Route, skill: int, log: RouteLog, mapdata: MapData,
             nomonsters: bool = False) -> SkillReport:
    problems: list[str] = []
    if log.helper is None:
        problems.append("the helper never reported (not loaded, or its ZScript did not compile: "
                        "look for 'Script error' above; --minimal-helper runs the proven part)")

    results: list[StepResult] = []
    for number, step in enumerate(route.steps):
        pos = log.positions.get(number)
        if pos is None:
            ok = not step.expect
            why = "no position reported" + ("" if ok else " (the sequence stopped, or the engine died)")
            results.append(StepResult(number, step, None, None, "?", None, ok, why))
            if not ok:
                problems.append(f"{step.id}: {why}")
            continue
        # Where he is, by the position (map data, independent of how the
        # engine numbers sectors) first, and by the engine's sector index
        # only when the position falls on a line.
        engine_name = mapdata.name_of(pos.sector)
        static = mapdata.sector_at(pos.x, pos.y)
        static_name = mapdata.name_of(static) if static is not None else None
        name = static_name or engine_name
        family = zone_family(name)
        static_family = zone_family(static_name) if static_name else None
        ok, why = True, ""
        if step.expect and family not in step.expect:
            ok = False
            why = f"ended in {family} ({name}), expected {'/'.join(step.expect)}"
            problems.append(f"{step.id}: {why}")
        elif static_name and engine_name and zone_family(engine_name) != static_family:
            why = (f"note: engine sector {pos.sector} is {engine_name} in map data, the position "
                   f"({pos.x}, {pos.y}) is in {static_name}")
        if pos.health <= 0:
            ok = False
            why = (why + "; " if why else "") + f"player dead (health {pos.health})"
            problems.append(f"{step.id}: player dead")
        results.append(StepResult(number, step, pos, name, family, static_family, ok, why))

    # Doors: the tagged ones by their sectors' heights, the manual ones by
    # the step that walks through them.
    doors: list[tuple[str, bool, str]] = []
    for number, step in enumerate(route.steps):
        for tag, want_open in step.tags:
            readings = None
            for i, at_step in enumerate(log.tag_steps.get(tag, [])):
                if at_step == number:
                    readings = log.tags[tag][i]
            if readings is None:
                doors.append((f"tag {tag} at {step.id}", False, "not reported"))
                problems.append(f"{step.id}: tag {tag} not reported")
                continue
            is_open = _door_open(readings)
            names = sorted({zone_family(mapdata.name_of(s)) + ":" + str(mapdata.name_of(s))
                            for s, _f, _c in readings})
            detail = (f"{'open' if is_open else 'shut'} ({len(readings)} sector(s): "
                      f"{', '.join(names)})")
            ok = is_open == want_open
            doors.append((f"tag {tag} at {step.id}: want {'open' if want_open else 'shut'}", ok, detail))
            if not ok:
                problems.append(f"{step.id}: tag {tag} is {detail}, wanted "
                                f"{'open' if want_open else 'shut'}")
    # Presses: the line was reached, so a door that stays shut means
    # something. The helper's line event, or the engine's lock message.
    locked_at = log.lock_steps()
    for number, step in enumerate(route.steps):
        for special, arg0 in step.presses:
            by_line = any(u.step == number and u.by_player and u.special == special
                          and u.arg0 == arg0 for u in log.lines)
            said = [text for at, text in log.pass_messages if at == number and at in locked_at]
            ok = by_line or bool(said)
            detail = ("the player's press is in the log" if by_line
                      else f"the engine said {said[0]!r}" if said
                      else "NOT SEEN: no SDTEST line for it and no lock message")
            doors.append((f"press of special {special} arg0 {arg0} at {step.id}", ok, detail))
            if not ok:
                problems.append(f"{step.id}: no press of special {special} (arg0 {arg0}) seen: "
                                "the use never reached the line, so its door proves nothing")
    for r in results:
        if r.step.expect and any(a.startswith("forward") for a in r.step.actions) \
                and any(a == "use" for a in r.step.actions):
            doors.append((f"walk-through at {r.step.id}", r.ok,
                          f"ended in {r.family}" + (f" ({r.sector_name})" if r.sector_name else "")))

    inventory = evaluate_inventory(route, skill, log, mapdata, problems)

    # Secrets.
    secret_total = len(mapdata.secret_sectors())
    found = None
    if log.secrets:
        found = log.secrets[-1][0]
    if log.unloaded:
        found = max(found or 0, log.unloaded[-1][4])
    elif log.levels:
        found = max(found or 0, log.levels[-1][3])
    want = route.expect_secrets
    if want == "all":
        want = secret_total
    secrets_ok = True
    if want is not None:
        secrets_ok = found == want
        if not secrets_ok:
            problems.append(f"secrets: found {found}, expected {want} of {secret_total}")

    # Exit: the level was ended the way the route says (the exit switch, or
    # the helper's sdexit on a map without one), and the game left it.
    exit_line = any(u.special == SPECIAL_EXIT_NORMAL and u.by_player for u in log.lines)
    exit_console = bool(log.exitlevel)
    left = [u for u in log.unloaded if u[1]]
    after = sorted({s for s in log.states if s in (GS_INTERMISSION, GS_FINALE)})
    triggered = exit_line if route.exit_by == "switch" else exit_console
    exit_reached = triggered and (bool(left) or bool(after))
    how = (f"exit switch pressed: {'yes' if exit_line else 'NO'}" if route.exit_by == "switch"
           else f"ended by sdexit: {'yes' if exit_console else 'NO'}")
    exit_detail = (f"{how}; level unloaded towards: {left[-1][1] if left else 'NOT SEEN'}; "
                   f"after it: {', '.join(GS_NAMES[s] for s in after) if after else AFTER_NOT_SEEN}")
    if route.must_exit and not exit_reached:
        problems.append("exit not reached: " + exit_detail)
    if route.exit_by == "switch" and exit_console:
        problems.append("the level was ended by sdexit, not by its exit switch")
    if exit_reached and route.end_sequence and not left[-1][1].startswith(END_SEQUENCE_PREFIX):
        problems.append(f"the level led to {left[-1][1]!r}, not to an end sequence")
    if exit_reached and route.next_map and left[-1][1].upper() != route.next_map.upper():
        problems.append(f"the level led to {left[-1][1]!r}, not to {route.next_map} "
                        "(MAPINFO's next)")

    # The route's own kills (sdclear): never a failure on their own, always
    # reported, so G3 knows a body stood in a scripted walk. A blocker that
    # survived is a failure: the walk after it proves nothing.
    for step, cls, x, y, hp, dead in log.cleared:
        if not dead:
            sid = route.steps[step].id if step < len(route.steps) else str(step)
            problems.append(f"{sid}: blocker {cls} at ({x}, {y}) survived sdclear")

    # Monsters on this skill: engine vs the map's own things.
    expected = 0 if nomonsters else mapdata.monsters_on(skill)
    engine = log.levels[0][2] if log.levels else None
    if engine is not None and engine != expected:
        problems.append(f"monsters: engine spawned {engine}, the map places {expected} on skill {skill}")

    return SkillReport(route, skill, log, results, doors, found, secret_total, secrets_ok,
                       exit_reached, exit_detail, expected, engine, problems,
                       inventory=inventory)


def kills_line(rep: "SkillReport") -> str:
    """Kills at the end, and how many of them were the route's (sdclear)."""
    by_route = sum(1 for c in rep.log.cleared if c[5])
    if rep.log.unloaded:
        kills, total = rep.log.unloaded[-1][2], rep.log.unloaded[-1][3]
        return f"{kills} of {total}, of which {by_route} by the route's sdclear"
    return f"? (level never unloaded), {by_route} by the route's sdclear"


def describe_inventory(inv: Inventory) -> str:
    owned = ", ".join(f"{slot}:{cls}" for cls, slot in sorted(inv.weapons, key=lambda w: w[1]))
    text = f"raised slot {inv.ready_slot} ({inv.ready}), {inv.ammo} rounds; owned [{owned or 'none'}]"
    if inv.key_count is not None:
        text += f"; keys [{', '.join(inv.keys) or 'none'}]"
    return text


def evaluate_inventory(route: Route, skill: int, log: RouteLog, mapdata: MapData,
                       problems: list[str]) -> list[tuple[str, bool, str]]:
    """The start inventory and the pickups, by slot (never by class: D40).

    Every step that asked for `inv` is reported; the steps that carry an
    expectation (melee, ready_slot, ready_ammo) are judged."""
    rows: list[tuple[str, bool, str]] = []
    for number, step in enumerate(route.steps):
        if "inv" not in step.actions:
            continue
        inv = log.inventory.get(number)
        if inv is None:
            ok = not step.checks_inventory
            rows.append((step.id, ok, "not reported"))
            if not ok:
                problems.append(f"{step.id}: inventory not reported (helper missing, or --minimal-helper)")
            continue
        wrong = []
        if step.melee is not None and (SLOT_MELEE in inv.slots()) != step.melee:
            wrong.append(f"slot {SLOT_MELEE} {'empty' if step.melee else 'already owned'}")
            if step.melee and not mapdata.things_on(ED_MELEE, skill):
                wrong.append(f"no DoomEdNum {ED_MELEE} on skill {skill} in the map")
        if step.ready_slot is not None and inv.ready_slot != step.ready_slot:
            wrong.append(f"raised weapon in slot {inv.ready_slot}, wanted {step.ready_slot}")
        if step.ready_ammo is not None and inv.ammo != step.ready_ammo:
            wrong.append(f"{inv.ammo} rounds, wanted {step.ready_ammo}")
        if step.key is not None:
            if inv.key_count is None:
                wrong.append("keys not reported (a helper older than route-4)")
            elif (inv.key_count > 0) != step.key:
                wrong.append("no key owned" if step.key
                             else f"a key already owned ({', '.join(inv.keys) or inv.key_count})")
        if step.keys is not None:
            if inv.key_count is None:
                wrong.append("keys not reported (a helper older than route-4)")
            elif inv.key_count != step.keys:
                wrong.append(f"{inv.key_count} key(s) owned ({', '.join(inv.keys) or 'none'}), "
                             f"wanted {step.keys}")
        detail = describe_inventory(inv) + (f"  -- {'; '.join(wrong)}" if wrong else "")
        rows.append((step.id, not wrong, detail))
        for w in wrong:
            problems.append(f"{step.id}: {w}")
    return rows


def render_report(rep: SkillReport) -> str:
    out = [f"=== route {rep.route.name} / {rep.route.map_name} / skill {rep.skill} ==="]
    if rep.run_problem:
        out.append(f"engine run     : {rep.run_problem}")
    out.append(f"helper         : {rep.log.helper or 'NOT LOADED'}")
    out.append(f"god mode       : {'on' if rep.log.god else 'not seen in the log'}")
    out.append(f"monsters       : engine {rep.monsters_engine if rep.monsters_engine is not None else '?'}"
               f", map data {rep.monsters_expected}")
    if rep.log.counts:
        first = rep.log.counts[0]
        out.append("bestiary (start): " + ", ".join(f"{k} {v[1]}/{v[0]}" for k, v in first.items() if v[0]))
    out.append("steps:")
    for r in rep.steps:
        where = (f"{r.family:<4} {r.sector_name or '?'} @ ({r.pos.x}, {r.pos.y}, {r.pos.z}) hp {r.pos.health}"
                 if r.pos else "-")
        mark = "ok " if r.ok else "BAD"
        expect = "/".join(r.step.expect) or "-"
        out.append(f"  [{mark}] {r.step.id:<4} expect {expect:<12} got {where}"
                   + (f"  -- {r.why}" if r.why else ""))
    out.append("zones reached  : " + (" -> ".join(rep.zones_reached) or "none"))
    out.append("doors:")
    for what, ok, detail in rep.doors or [("none checked", True, "")]:
        out.append(f"  [{'ok ' if ok else 'BAD'}] {what}: {detail}")
    out.append("inventory (by slot):")
    for what, ok, detail in rep.inventory or [("none asked", True, "")]:
        out.append(f"  [{'ok ' if ok else 'BAD'}] {what}: {detail}")
    out.append(f"secrets        : {rep.secrets_found if rep.secrets_found is not None else '?'}"
               f" of {rep.secrets_total}" + ("" if rep.secrets_ok else "  -- NOT AS EXPECTED"))
    for msg in rep.log.secret_messages:
        out.append(f"  engine said  : {msg}")
    if rep.log.pass_messages:
        ids_ = {n: s.id for n, s in enumerate(rep.route.steps)}
        out.append("key messages   :")
        for step, msg in rep.log.pass_messages:
            out.append(f"  {ids_.get(step, step)}: {msg}")
    out.append(f"exit           : {'REACHED' if rep.exit_reached else 'NOT REACHED'} ({rep.exit_detail})")
    ids = {n: s.id for n, s in enumerate(rep.route.steps)}
    out.append(f"blockers       : {len(rep.log.cleared) or 'none'} killed by the route's sdclear"
               + (f" (sdclear answered {sum(rep.log.clears.values())} time(s))" if rep.log.clears
                  else ""))
    for step, cls, x, y, hp, dead in rep.log.cleared:
        out.append(f"  [{'ok ' if dead else 'BAD'}] {ids.get(step, step)}: {cls} at ({x}, {y}),"
                   f" {hp} hp, {'dead' if dead else 'SURVIVED'}")
    out.append(f"kills          : {kills_line(rep)}")
    out.append(f"screenshots    : {len(rep.log.captures)}")
    failures = rep.log.failures
    out.append(f"log failures   : {len(failures) or 'none'}")
    for hit in failures:
        out.append(hit.render())
    for p in rep.problems:
        out.append(f"PROBLEM        : {p}")
    note = (f" ({len(rep.log.cleared)} blocker(s) killed by the route, listed above)"
            if rep.log.cleared else "")
    out.append(f"VERDICT        : {'PASS' if rep.passed else 'FAIL'}{note}")
    return "\n".join(out)


# ============================================================================
# Running it
# ============================================================================

def run_dir_for(route: Route, skill: int, when: datetime | None = None) -> Path:
    when = when or datetime.now()
    return ROUTE_DIR / f"{when:%Y%m%d-%H%M%S}-{route.name}-skill{skill}"


def keep_evidence(rep: SkillReport, run_dir: Path, phase: str, nomonsters: bool) -> list[Path]:
    slug = f"g3-{rep.route.map_name.lower()}-{rep.route.name}-skill{rep.skill}" + ("-nomonsters" if nomonsters else "")
    stem = smoke.evidence_stem(phase, slug)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    kept = []
    log = run_dir / "gzdoom.log"
    if log.exists():
        kept.append(Path(shutil.copy2(log, EVIDENCE_DIR / f"{stem}.log")))
    report = EVIDENCE_DIR / f"{stem}-report.txt"
    report.write_text(render_report(rep) + "\n", encoding="utf-8")
    kept.append(report)
    ids = {n: s.id for n, s in enumerate(rep.route.steps)}
    ids[len(rep.route.steps)] = END_STEP_ID
    seen: dict[str, int] = {}
    for step_no, name in rep.log.captures:
        src = run_dir / "shots" / name
        if not src.exists():
            continue
        label = ids.get(step_no, f"step{step_no}")
        seen[label] = seen.get(label, 0) + 1
        suffix = label.lower() + (f"-{seen[label]}" if seen[label] > 1 else "")
        kept.append(Path(shutil.copy2(src, EVIDENCE_DIR / f"{stem}-{suffix}.png")))
    return kept


def scan_only(path: Path, strict: bool = False) -> int:
    """G3-2 on any log: smoke's failure contract plus G3_EXTRA_PATTERNS."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"route: {exc}", file=sys.stderr)
        return EXIT_ROUTE_FAILED
    log = scan_route_log(text, strict)
    failures = log.failures
    print(f"log            : {path}")
    print(f"map entered    : {log.smoke.map_entered or 'NOT SEEN'}")
    print(f"G3-2 hits      : {len(failures) or 'none'}")
    for hit in failures:
        print(hit.render())
    print(f"VERDICT        : {'PASS' if not failures else 'FAIL'}")
    return EXIT_OK if not failures else EXIT_LOG_FAILURES


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="tools/route.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--route", default="g3-auto", choices=route_names(),
                   help="built-in route (default g3-auto)")
    p.add_argument("--steps", type=Path, help="a route of your own, as JSON (overrides --route)")
    p.add_argument("--skills", type=int, nargs="+", default=[2, 3, 4], choices=range(1, 6),
                   help="skills to run, one engine run each (default: 2 3 4)")
    p.add_argument("--no-god", action="store_true", help="do not type `god` (default: god on)")
    p.add_argument("--notarget", action="store_true", help="also type `notarget`")
    p.add_argument("--nomonsters", action="store_true", help="pass -nomonsters (G3-5)")
    p.add_argument("--no-clear", action="store_true",
                   help="do not kill the live monsters standing in a scripted walk's way")
    p.add_argument("--hide-weapon", action="store_true",
                   help="no first-person weapon in the shots (r_drawplayersprites 0): the mural's M5")
    p.add_argument("--minimal-helper", action="store_true",
                   help="helper with the PM's proven commands only (no positions, doors or exit)")
    p.add_argument("--timeout", type=float, help="hard timeout per run, seconds (default: route length + 90)")
    p.add_argument("--window", type=smoke.parse_window,
                   default=(smoke.SMOKE_WINDOW_W, smoke.SMOKE_WINDOW_H),
                   help="window WxH, or 'native' (default: smoke's)")
    p.add_argument("--no-build", action="store_true", help="use dist/ as it is")
    p.add_argument("--pk3", default=str(smoke.DEFAULT_PK3), help="mod PK3 to load")
    p.add_argument("--gzdoom", help="GZDoom binary (else $GZDOOM, else the usual places)")
    p.add_argument("--iwad", help="IWAD (else $IWAD, else iwads/)")
    p.add_argument("--strict", action="store_true", help="engine warnings are failures")
    p.add_argument("--keep-evidence", action="store_true",
                   help="copy log, report and screenshots to docs/qa/evidence/")
    p.add_argument("--phase", default=DEFAULT_PHASE, help="phase tag for evidence names (default F3)")
    p.add_argument("--print", dest="print_only", action="store_true",
                   help="write the helper, print the sequence and argv; no engine")
    p.add_argument("--parse", type=Path, metavar="LOG", help="report on an existing log; no engine")
    p.add_argument("--scan", type=Path, metavar="LOG",
                   help="G3-2 only: the log of any run (a hand-played one too) against smoke's "
                        "patterns plus G3's two; no route, no engine")
    p.add_argument("--skill", type=int, default=3, help="the skill of the --parse log (default 3)")
    p.add_argument("--list-routes", action="store_true", help="list the built-in routes")
    p.add_argument("extra", nargs="*", help="extra args passed straight to gzdoom")
    return p.parse_args(argv)


def load_route(args: argparse.Namespace) -> Route:
    if args.steps:
        return route_from_json(json.loads(args.steps.read_text(encoding="utf-8")))
    return route_by_name(args.route)


def main(argv: list[str] | None = None) -> int:
    # Engine logs carry Cyrillic when the game runs in Russian; a Windows
    # console (cp1252) cannot print it, so the report is written as UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv)
    if args.list_routes:
        for name in route_names():
            try:
                r = route_by_name(name)
            except (RouteError, OSError) as exc:
                print(f"{name:<18} UNAVAILABLE: {exc}")
                continue
            print(f"{name:<18} {r.map_name}  {len(r.steps)} steps  {r.description}")
        return EXIT_OK
    if args.scan:
        return scan_only(args.scan, args.strict)
    try:
        route = load_route(args)
        mapdata = load_map_data(route.map_name)
    except (RouteError, OSError, json.JSONDecodeError) as exc:
        print(f"route: {exc}", file=sys.stderr)
        return EXIT_ROUTE_FAILED
    god = not args.no_god

    if args.parse:
        text = args.parse.read_text(encoding="utf-8", errors="replace")
        rep = evaluate(route, args.skill, scan_route_log(text, args.strict), mapdata, args.nomonsters)
        print(render_report(rep))
        return EXIT_OK if rep.passed else (EXIT_LOG_FAILURES if rep.log.failures else EXIT_ROUTE_FAILED)

    helper = write_helper_pk3(HELPER_PK3, minimal=args.minimal_helper)
    if args.print_only:
        print(f"helper : {helper}")
        print(f"tics   : {sequence_tics(route, god, args.notarget, not args.no_clear)}")
        for skill in args.skills:
            cmd = build_command(Path("gzdoom"), Path("<iwad>"), Path(args.pk3), helper,
                                Path("<log>"), Path("<shots>"), route, skill, god=god,
                                notarget=args.notarget, nomonsters=args.nomonsters,
                                window=args.window, hide_weapon=args.hide_weapon, clear=not args.no_clear,
                                extra=args.extra)
            print(f"skill {skill}: " + " ".join(a for a in cmd[1:] if not a.startswith("+wait ")))
        print("sequence:")
        for c in route_commands(route, god, args.notarget, not args.no_clear):
            print(f"  {c}")
        return EXIT_OK

    try:
        gzdoom = smoke.find_gzdoom(args.gzdoom)
        iwad = smoke.find_iwad(args.iwad)
        if not args.no_build:
            smoke.run_build()
        pk3 = Path(args.pk3)
        if not pk3.is_file():
            raise smoke.SmokeError(f"{pk3} missing; run python3 tools/build.py", smoke.EXIT_BUILD_FAILED)
    except smoke.SmokeError as exc:
        print(f"route: {exc}", file=sys.stderr)
        return exc.code

    timeout = args.timeout or (sequence_tics(route, god, args.notarget, not args.no_clear) / TICS_PER_SECOND + TIMEOUT_MARGIN_S)
    worst = EXIT_OK
    summary = []
    for skill in args.skills:
        run_dir = run_dir_for(route, skill)
        shots = run_dir / "shots"
        shots.mkdir(parents=True, exist_ok=True)
        log_path = run_dir / "gzdoom.log"
        argv_ = build_command(gzdoom, iwad, pk3, helper, log_path, shots, route, skill, god=god,
                              notarget=args.notarget, nomonsters=args.nomonsters,
                              window=args.window, hide_weapon=args.hide_weapon, clear=not args.no_clear,
                              extra=args.extra)
        print(f"\nskill {skill}: " + " ".join(a for a in argv_[1:] if not a.startswith("+wait ")))
        try:
            result = smoke.run_engine(argv_, timeout)
        except smoke.EngineBlocked as blocked:
            print(str(blocked).replace("smoke:", "route:", 1), file=sys.stderr)
            return EXIT_BLOCKED
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        rep = evaluate(route, skill, scan_route_log(text, args.strict), mapdata, args.nomonsters)
        if result.timed_out:
            rep.run_problem = f"TIMED OUT after {timeout:.0f}s, killed"
        elif result.returncode not in (0, None):
            rep.run_problem = f"engine exited {result.returncode}"
        report = render_report(rep)
        (run_dir / "report.txt").write_text(report + "\n", encoding="utf-8")
        print(report)
        print(f"run dir        : {run_dir}")
        if args.keep_evidence:
            for path in keep_evidence(rep, run_dir, args.phase, args.nomonsters):
                print(f"evidence       : {path}")
        code = EXIT_OK
        if result.timed_out:
            code = EXIT_TIMEOUT
        elif rep.log.failures:
            code = EXIT_LOG_FAILURES
        elif rep.run_problem:
            code = EXIT_ENGINE_FAILED
        elif not rep.passed:
            code = EXIT_ROUTE_FAILED
        summary.append((skill, code))
        if worst == EXIT_OK:
            worst = code
    print("\n--- route summary ---")
    for skill, code in summary:
        print(f"skill {skill}: {'PASS' if code == EXIT_OK else f'FAIL (exit {code})'}")
    return worst


if __name__ == "__main__":
    sys.exit(main())
