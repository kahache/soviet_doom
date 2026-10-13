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
class is being renamed (the shovel becomes an ice axe, D40): step A0 asserts
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

Ending a level: MAP01 must end by its exit switch (G3-4); MAP02 has no exit
line, so map02-start ends it with the helper's `sdexit` (Level.ExitLevel).
The console `exit` QUITS GZDoom (PM, 2026-10-13 20:39) and is never typed.
Both maps say `next = endtitle`, so the report checks that the level led
to an end sequence.

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
  python3 tools/route.py --steps my_route.json --print          # a route of your own
  python3 tools/route.py --list-routes

Exit codes: smoke's (1 log failures, 2 no gzdoom, 3 no IWAD, 4 build,
5 timeout, 6 engine exit status), plus
  8  the engine gate is shut (SD_ALLOW_ENGINE is not 1): nothing was launched
  9  the log is clean but the route failed (wrong zone, door shut, no exit)

NOT VERIFIED until the PM's first run (D26: this role does not start the
engine): that the helper's extra hooks compile and print as written, and
whether a `warp` onto a pickup collects it (the rack step does not rely on
that: it walks into the rack's alcove, which a move does collect).
VERIFIED by the PM's run of 2026-10-13 20:36 (route-1 helper): it compiles,
and position, tags, lines, inventory, the exit line and the unload are
printed as parsed here. Added after that run and NOT VERIFIED yet: sdclear,
sdexit, and the static SDRouteState that answers sdstate after the level
has ended (whether net events run during an intermission or an end text).
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
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
END_TEXT_TICS = 280      # an end text types itself out; MAP02's 74 characters fit well inside
# One argv element carries the whole sequence. Windows caps a command line at
# 32767 characters; we stay far below it. NOT VERIFIED: any shorter limit in
# GZDoom's own console buffer (the PM's hand runs used a few hundred chars).
MAX_SEQUENCE_CHARS = 8000

# --- What the helper knows how to count and hurt ----------------------------
# The PM's list, proven in engine on 2026-10-13 (MAP01 and MAP02). The index
# of a class here is the first argument of `netevent sdhurt`.
COUNT_CLASSES = (
    "SD_ReichRifleman", "SD_LegionTrooper", "SD_Stormtrooper", "SD_ReichHound",
    "SD_Doughboy", "SD_Panzermensch", "SD_PanzermenschSchwer", "SD_General",
    "SD_Clip", "SD_Izh",
)
HELPER_CLASS = "SDRouteHelper"
HELPER_VERSION = "route-2"

# Monsters as the map places them (DoomEdNums of the Freedoom stand-ins our
# bestiary replaces, docs/levels/MAP01-zarya-7.md section 8). Used to say how
# many monsters the engine should spawn on each skill.
# Plus the Doom numbers of the two the episode has not placed yet (16, 3003)
# and our own numbers (MOD-SPEC 6.1: 21100-21107; MAP02's gallery uses
# them), so the count holds on any map.
MONSTER_EDNUMS = frozenset({3004, 9, 3001, 3002, 3005, 69, 16, 3003} | set(range(21100, 21108)))
SECTOR_SPECIAL_SECRET = 1024     # udmf.SECTOR_SPECIAL_SECRET
SPECIAL_EXIT_NORMAL = 243        # udmf.SPECIAL_EXIT_NORMAL
GS_INTERMISSION = 1              # EGameState in GZDoom's zscript/engine/base.zs
GS_FINALE = 2                    # the same enum: an end text (a cluster's exittext)
GS_NAMES = {GS_INTERMISSION: "intermission", GS_FINALE: "end text"}
END_SEQUENCE_PREFIX = "enDSeQ"   # what GZDoom calls `next = endtitle` and its kin
# A door counts as open when a player fits under it (Doom player height 56).
PLAYER_HEIGHT = 56

# --- The start inventory (63dac93; design section 17.14) --------------------
# Keyed on the slot and the editor number, never on the class: the melee
# weapon is being renamed (shovel -> ice axe, D40) while this is written.
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
    rounds in its primary ammo pool.
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

    @property
    def checks_inventory(self) -> bool:
        return (self.melee, self.ready_slot, self.ready_ammo) != (None, None, None)


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
    # sdexit, for a map with no exit line: MAP02).
    exit_by: str = "switch"
    # The map's MAPINFO says `next = endtitle`: leaving it must lead to an
    # end sequence (GZDoom names them "enDSeQ" + hex: the PM's MAP01 run
    # of 2026-10-13 20:36 unloaded towards "enDSeQ1dce").
    end_sequence: bool = False


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

_A_STEPS = (
    Step("A0", actions=("level", "count", "inv", "capture"), expect=("Z1",),
         melee=False, ready_slot=SLOT_SIDEARM, ready_ammo=start_rounds(),
         note="the player start: TT-33 raised with its rounds, slot 1 empty; "
              "monsters on this skill, bestiary counts"),
    Step("R1", MAP01_RACK_APPROACH, MAP01_RACK_FACING, (f"forward {RACK_WALK}", "inv", "capture"),
         expect=("Z1",), melee=True,
         note=f"the dorm rack: walk onto the melee weapon (DoomEdNum {ED_MELEE}); slot 1 owned"),
    Step("A1", (256, 420), 90, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
         expect=("Z3",), note="D2 opens; walk into the barracks corridor"),
    Step("A2", (256, 940), 90, ("capture",), expect=("Z3", "Z4"),
         note="the komnata ahead"),
    Step("A3", (600, 1152), 0, ("use", f"wait {DOOR_WAIT}", f"forward {WALK}", "capture"),
         expect=("Z5",), note="D3 opens; walk into the service corridor"),
    Step("A4", (1040, 1256), 0, ("inv", "capture"), expect=("Z5", "Z5B"),
         note="the guard post: the IZh-58 is picked up here"),
    Step("A5", (1336, 1152), 0, (f"tag {MAP01_TAG_D4}", "capture"), expect=("Z6",),
         tags=((MAP01_TAG_D4, False),), note="the hangar, first contact; D4 still shut"),
    Step("A6", (1416, 1624), 0, ("use", f"wait {SWITCH_WAIT}", f"tag {MAP01_TAG_D4}",
                                 "capture", "angle 90", "capture"),
         expect=("Z7",), tags=((MAP01_TAG_D4, True),),
         note="SW-A: D4 and the three fuel-bay ambush panels open"),
    Step("A7", (2000, 1520), 0, ("inv", "capture"), expect=("Z6B",),
         note="the catwalk: the PPSh-41 is picked up here"),
    Step("A8", (2496, 1560), 90, (f"tag {MAP01_TAG_D5}", "use", f"wait {DOOR_WAIT}",
                                  f"forward {WALK}", "capture"),
         expect=("D6", "Z9"), tags=((MAP01_TAG_D5, False),),
         note="D6 opens; walk into it (the booth is through its east side); D5 still shut"),
    Step("A9", (2560, 1810), 90, ("use", f"wait {SWITCH_WAIT}", f"tag {MAP01_TAG_D5}", "capture"),
         expect=("Z9",), tags=((MAP01_TAG_D5, True),),
         note="SW-B: D5 and the three wave-2 closets open"),
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

# --- MAP02, the test range: the start inventory alone --------------------
# The same two checks as A0 and R1, on the range (src/maps/MAP02/map.py): the
# player starts at (160, 384) and the weapon row lies along y 624, the melee
# weapon (DoomEdNum ED_MELEE) first at x 288 and the next 112 further east,
# so walking north up x 288 collects that one and no other. No zones (MAP02
# has no zone plan). MAP02 has no exit line, so E1 ends it with the
# helper's sdexit (Level.ExitLevel), and its shot is cluster 2's end text
# (MAPINFO: `nointermission`, `next = endtitle`).
MAP02_AXE_APPROACH = (288, 560)
MAP02_AXE_FACING = 90

_MAP02_STEPS = (
    Step("A0", actions=("level", "inv", "capture"),
         melee=False, ready_slot=SLOT_SIDEARM, ready_ammo=start_rounds(),
         note="the player start: TT-33 raised with its rounds, slot 1 empty"),
    Step("R1", MAP02_AXE_APPROACH, MAP02_AXE_FACING, (f"forward {RACK_WALK}", "inv", "capture"),
         melee=True, note=f"walk north over the weapon row's first item (DoomEdNum {ED_MELEE})"),
    Step("E1", actions=("exit", f"wait {END_TEXT_TICS}", "state", "capture"),
         note="end MAP02 by sdexit (it has no exit line; the console `exit` quits GZDoom): "
              "cluster 2's end text, SD_END02_TEXT over SDFLR1, is what the shot must show"),
)

# --- MAP01, the mural shots M1-M5 (design section 17.13) ------------------
# Warp, face, shoot: the CEO judges the pictures. Run with --nomonsters so
# nothing walks into the frame. M3 is two shots (the doorway's two corners).
# M4's last clause (the health bonus at 432 1400 can be walked onto) is NOT
# scripted: the way to it is a 32-wide gap between the lectern (x <= 416)
# and a floor lamp (x >= 448), exactly one body, and a warp would skip the
# very question. The PM walks it by hand (docs/qa/GATE-REVIEWS.md, G3).
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

ROUTES: dict[str, Route] = {
    "g3-auto": Route(
        "g3-auto", "MAP01", _A_STEPS, expect_secrets=0, end_sequence=True,
        description="section 17.10's automatic run A1-A12 plus the start inventory (A0) and "
                    "the dorm rack (R1): the critical path, no secret (also G3-5's zero-secret run)"),
    "g3-secrets": Route(
        "g3-secrets", "MAP01", _SECRET_STEPS, expect_secrets="all", end_sequence=True,
        description="the same path with the three secrets of section 7 taken on the way"),
    "map02-start": Route(
        "map02-start", "MAP02", _MAP02_STEPS, expect_secrets=None, must_exit=True,
        exit_by="console", end_sequence=True,
        description="the test range: the start inventory, the slot-1 pickup, and its end text"),
    "mural": Route(
        "mural", "MAP01", _MURAL_STEPS, expect_secrets=None, must_exit=False,
        description="section 17.13's mural shots M1-M5 (run with --nomonsters)"),
}


def route_from_json(data: dict) -> Route:
    """A route of your own: {"name", "map", "expect_secrets"?, "must_exit"?,
    "steps": [{"id", "warp"?: [x, y], "angle"?, "do"?: [...], "expect"?: [...],
    "tags"?: {"10": true}, "melee"?: bool, "ready_slot"?, "ready_ammo"?, "note"?}]}."""
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
            )
            for s in data["steps"]
        )
        route = Route(str(data.get("name", "custom")), str(data.get("map", "MAP01")).upper(),
                      steps, data.get("expect_secrets"), bool(data.get("must_exit", True)),
                      str(data.get("description", "")))
    except (KeyError, TypeError) as exc:
        raise RouteError(f"malformed route file: {exc}") from exc
    for step in steps:
        if step.warp is not None and len(step.warp) != 2:
            raise RouteError(f"step {step.id}: warp needs [x, y]")
    return route


# ============================================================================
# Map data: what the map's own source says (no engine)
# ============================================================================

# Zone families: the report speaks of "Z3" or "the D6 door", not of sector 57.
# Most sector names carry their zone (`z3_corridor`, `lamp_z3_corridor_1`);
# the rest are mapped by prefix here. First match wins.
ZONE_PREFIXES: tuple[tuple[str, str], ...] = (
    # A door's recess belongs to the room it is cut into, so that a player
    # still standing in front of a shut door is never counted as "in the door".
    ("d3_recess", "Z4"), ("d4_recess", "Z6"), ("d5_recess", "Z10"), ("d6_recess", "Z6B"),
    ("s1_", "S1"), ("s2_", "S2"), ("s3_", "S3"), ("sump_step", "S3"),
    ("prop_bunk", "Z1"), ("shovel_rack", "Z1"), ("frame_d1_dorm", "Z1"), ("frame_d2_dorm", "Z1"),
    ("frame_d1_washroom", "Z2"), ("prop_basin", "Z2"), ("stall_", "Z2"),
    ("bulkhead_", "Z3"),
    ("prop_mess", "Z4"), ("tribune", "Z4"), ("prop_lectern", "Z4"),
    ("pipes_", "Z5"), ("crate_guard", "Z5B"), ("weapon_rack", "Z5B"),
    ("cradle_", "Z6A"), ("spine_", "Z6A"), ("rail_", "Z6A"),
    ("catwalk_", "Z6B"),
    ("step_down", "Z6"), ("lane_", "Z6"), ("gantry", "Z6"), ("plinth_c", "Z6"),
    ("crate_h", "Z6"), ("shadow_", "Z6"), ("closet_w", "Z6"), ("closet_e", "Z6"),
    ("fuel_", "Z7"), ("plinth_tank", "Z7"), ("closet_a", "Z7"),
    ("booth_window", "Z9"),
    ("airlock_", "Z8"), ("frame_d5", "Z8"),
    ("lenin_", "Z10"),
)
_ZONE_IN_NAME = re.compile(r"(?:^|_)(z\d+[ab]?)(?:_|$)")
_DOOR_NAME = re.compile(r"^(d\d)(?:_|$)")


def zone_family(name: str | None) -> str:
    """'lamp_z3_corridor_1' -> 'Z3'; 'd6' and 'd6_recess' -> 'D6'; '?' if unknown."""
    if not name:
        return "?"
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

    def __init__(self, map_name: str = "MAP01", src: Path = PROJECT_ROOT / "src"):
        from sdbuild.pk3 import _load_map_module  # the build's own importer

        script = src / "maps" / map_name / "map.py"
        if not script.is_file():
            raise RouteError(f"no map source {script}")
        module = _load_map_module(script, TOOLS_DIR)
        self.map_name = map_name
        if hasattr(module, "build_plan"):
            self.textmap, self.plan = module.build_plan()
        elif hasattr(module, "build_textmap"):
            # A map without a zone plan (MAP02, the test range): positions,
            # monsters, secrets and things still work; zones read '?', so a
            # route on it should not use `expect`.
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
        if (e.Name == "sdangle") {{ pmo.angle = e.Args[0]; pmo.pitch = 0; return; }}
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
            // raised one and the rounds in its primary pool.
            int owned = 0;
            for (let item = pmo.Inv; item; item = item.Inv)
            {{
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
            Console.Printf("SDTEST inv weapons=%d ready=%s slot=%d ammo=%d", owned, readyName,
                readySlot, readyAmmo);
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
        "//   netevent sdangle <deg>         set the view angle (pitch level)\n"
        "//   netevent sdhurt <idx> <amount> damage every live actor of NAMES[idx]\n"
        "//   netevent sdcount               live / total counts of NAMES\n"
        "//   netevent sdpos <step>          position, sector index, health\n"
        "//   netevent sdinv                 weapons owned by slot, the raised one, its rounds\n"
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
# A static handler lives across levels. NOT VERIFIED: that GZDoom runs net
# events during the intermission and the end text; if it does not, the
# report says NOT SEEN and the END screenshot is the evidence.
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


def step_commands(number: int, step: Step, clear: bool = True) -> list[str]:
    cmds = [f"echo SDSTEP {number} {step.id}"]
    if step.warp is not None:
        cmds += [f"warp {step.warp[0]} {step.warp[1]}", f"wait {SETTLE_TICS}"]
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
RE_INV = re.compile(r"^SDTEST inv weapons=(\d+) ready=(\S+) slot=(-?\d+) ammo=(-?\d+)")
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


@dataclass
class Inventory:
    """One `sdinv` answer: weapons as (class, slot), the raised one, its rounds."""

    weapons: list[tuple[str, int]]
    ready: str
    ready_slot: int
    ammo: int

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

    @property
    def failures(self) -> list[smoke.LogHit]:
        return sorted(self.smoke.failures + self.extra_failures, key=lambda h: h.lineno)


def scan_route_log(text: str, strict: bool = False) -> RouteLog:
    log = RouteLog(smoke=smoke.scan_log(text, strict=strict))
    current = -1
    count_block: dict[str, tuple[int, int]] | None = None
    tag_block_step: dict[int, int] = {}
    weapons: list[tuple[str, int]] = []   # the weapon lines before an inv line
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
                                     int(g[5]), g[6] == "1"))
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
        elif m := RE_INV.match(line):
            log.inventory[current] = Inventory(weapons, m.group(2), int(m.group(3)), int(m.group(4)))
            weapons = []
        elif m := RE_HELPER.match(line):
            log.helper = m.group(1)
        elif m := RE_CAPTURED.match(line):
            log.captures.append((current, m.group(1)))
        elif RE_GOD.match(line):
            log.god = True
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
                   f"after it: {', '.join(GS_NAMES[s] for s in after) if after else 'NOT SEEN'}")
    if route.must_exit and not exit_reached:
        problems.append("exit not reached: " + exit_detail)
    if route.exit_by == "switch" and exit_console:
        problems.append("the level was ended by sdexit, not by its exit switch")
    if exit_reached and route.end_sequence and not left[-1][1].startswith(END_SEQUENCE_PREFIX):
        problems.append(f"the level led to {left[-1][1]!r}, not to an end sequence")

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
    return f"raised slot {inv.ready_slot} ({inv.ready}), {inv.ammo} rounds; owned [{owned or 'none'}]"


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
    p.add_argument("--route", default="g3-auto", choices=sorted(ROUTES),
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
    return ROUTES[args.route]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.list_routes:
        for name, r in ROUTES.items():
            print(f"{name:<12} {r.map_name}  {len(r.steps)} steps  {r.description}")
        return EXIT_OK
    if args.scan:
        return scan_only(args.scan, args.strict)
    try:
        route = load_route(args)
        mapdata = MapData(route.map_name)
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
