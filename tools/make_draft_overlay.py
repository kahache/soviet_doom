#!/usr/bin/env python3
"""Build a DRAFT sprite overlay: play the mod with unapproved sprites on.

    .venv/Scripts/python.exe tools/make_draft_overlay.py              (Windows)
    .venv/bin/python tools/make_draft_overlay.py                      (macOS)
    ... make_draft_overlay.py --only weapons|enemies|all    (default: all)
    ... make_draft_overlay.py --hand B      renders of another hand, if any
    ... make_draft_overlay.py --dry-run     print the plan, write nothing

    SD_ALLOW_ENGINE=1 tools/run.sh -file work/overlays/sd-draft-sprites.pk3

Why. The CEO judges art by looking and maps in GZDoom. Drafts wait at his
gate in `work/art/`; the art-director's advice is "approve by judging them
in GZDoom". Approving means renaming the actors' states to our own sprite
names (`SDTT`, `SDHK`, ...) and moving the PNGs into `assets/`; this tool
does neither. It packs a SEPARATE PK3, loaded after the mod, that carries
our drafts under the names of the Freedoom placeholders our states use
today (`PISG`, `BFGG`, ...).

What is installed, and so never overlaid. D48 (2026-10-14) installed the
world pickups of six weapons (ice axe option C, TT-33, IZh-58, PPSh-41,
RPG-7, ROKS-3): their Spawn states name `SDAP`, `SDTP`, `SDIP`, `SDPQ`,
`SDRP`, `SDKP` and the PNGs ship from `assets/sprites/` (INSTALLED). The
held and flash frames were held back the same day (the CEO found hand E
deformed in MAP01) and stay drafts here, with the hand Katyusha. A swap
whose sprite is already under
`assets/sprites/` is skipped with a note, so an approval is never shadowed
by its own draft. D54 (2026-10-14) installed the Liberty Legion trooper's
full set (`SDLT`, 70 lumps in `assets/sprites/legion/`, its states renamed
from `SPOS`): the overlay never carried the Legion and carries nothing of
it now (INSTALLED_ENEMIES; no swap names `SPOS` or `SDLT`). D55 (2026-10-14)
installed the Reich rifleman (`SDRR`, 70 lumps in `assets/sprites/rifleman/`,
renamed from `POSS`) and the Reich hound (`SDHN`, 46 lumps with mirrored
pairs in `assets/sprites/hound/`, renamed from `SARG`) the same way: the
rifleman's swap, the overlay's only enemy, is gone, and the hound never had
one. D56 (2026-10-14) installed the Hybrid Stormtrooper (`SDHS`, 77 lumps)
and his bolt (`SDBL`, 5) in `assets/sprites/storm/`, renamed from `TROO`
and `BAL1`; the overlay never carried them either. N17 (2026-10-15)
installed the TT-33's held and flash frames, the D61 hands (`SDTT` A-C,
`SDTF` A in `assets/sprites/tt33/`, renamed from `PISG` and `PISF`): their
two swaps are gone and INSTALLED_WEAPON_FRAMES records them, so the hand E
drafts in work/art/weapons/tt33/ can never be packed over them. D79
(2026-10-20) did the same for the PPSh-41 (`SDPP` A-B, `SDPF` A, built
from the CEO's Gemini pair by tools/art/gemini_frames.py, renamed from
`CHGG` and `CHGF`), and D84 (2026-10-20) for the IZh-58 (`SDIZ` A-D,
`SDIF` A-B), the RPG-7 (`SDRL` A-B, `SDRF` A-D), the ROKS-3 (`SDRK` A-B,
`SDKF` A) and the hand Katyusha (`SDHK` A-B, `SDHF` A-B), renamed from
`SHTG`/`SHTF`, `MISG`/`MISF`, `PLSG`/`PLSF` and `BFGG`/`BFGF`; the
Katyusha's floor pickup `SDHP` (D80, renamed from `BFUG`) went into
INSTALLED with them. D88 (the same day) installed the ice axe (`SDAX` A-D,
renamed from `PUNG`): no weapon swap is left, so today the overlay has
nothing to pack and says so, as `--only enemies` has since D55. The
machinery stays for the next weapon or enemy drafted. The `enemies` group keeps the rig machinery (eight rotations, the IWAD
check) for the next enemy drafted on the rig; today it has no swap, so
`--only enemies` has nothing to pack and says so.

GZDoom resolves a sprite by lump name and the last-loaded file wins, so the
drafts show up with no ZScript at all, and removing `-file ...overlay...`
from the command line puts Freedoom back.

What it reads (never writes):
  src/zscript/weapons/*.zs, src/zscript/monsters/*.zs (an enemy swap's)
                        the frame letters each placeholder sprite is used
                        with in a States block
  assets/sprites/       which of our sprites are installed (never overlaid)
  work/art/weapons/<weapon>/   SD.. A0-style HUD frames, flash, pickup
                        (`*_proposed.png` and `variants/` are skipped: a
                        proposal no state shows is not wired)
  work/art/enemies/rig/        an enemy's rotations 1-8 or 0 (--rig-dir); the
                        rifleman's SDRR renders still sit there, installed
  iwads/freedoom2.wad (optional) the rotation-safety check below

What it writes: work/overlays/<name>.pk3 (only `sprites/*.png`, copied
byte for byte so the grAb offsets travel with them) and a plain-text
manifest beside it. Refuses to write under src/, dist/ or assets/.

Rotations, and why a partial frame is refused. GZDoom fills a frame's
rotation slots from the LAST-loaded file first and never overwrites a slot
already filled (`R_InstallSpriteLump` in src/r_data/sprites.cpp, read at
tag g4.14.2; MOD-SPEC 6.9). So if the overlay brings all eight rotations
of a frame, Doom II's mirrored pair `POSSA2A8` finds both its slots taken
and is ignored; if it brought only some, the IWAD would fill the rest and
the monster would turn into the other drawing as it turns. Therefore:
  * a rotated frame must come with all of rotations 1-8, else refused;
  * a frame may not mix rotation 0 with 1-8 in our drafts;
  * with an IWAD present, our rotated frame is refused if the IWAD has the
    same frame as rotation 0 or as 16-angle rotations 9-G, because those
    would fill the slots our eight leave empty.

Exit codes: 0 built (or dry run), 1 refused (the reason is printed),
2 usage.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZS_ROOT = PROJECT_ROOT / "src" / "zscript"
SPRITES_DIR = PROJECT_ROOT / "assets" / "sprites"
WEAPONS_DIR = PROJECT_ROOT / "work" / "art" / "weapons"
RIG_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"
OUT_DIR = PROJECT_ROOT / "work" / "overlays"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
# Folders the overlay must never touch: the build input, the build output
# and the approved art. A draft reaching any of them is an approval the CEO
# did not give.
FORBIDDEN_OUT = ("src", "dist", "assets")

DEFAULT_HAND = "E"          # gen_weapon.py's RECOMMENDED_HAND, the hand drawn
GROUPS = ("weapons", "enemies")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # same as tools/sdbuild/pk3.py: reproducible
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ROTATIONS_8 = "12345678"


@dataclass(frozen=True)
class Swap:
    """One placeholder sprite and the draft that stands in for it."""
    group: str          # "weapons" or "enemies"
    item: str           # the work/ folder under the group's root ("" = the root)
    zs: str             # path under src/zscript/, read for the frame letters
    placeholder: str    # the Freedoom sprite our states name today (MOD-SPEC 5.1)
    draft: str          # our reserved name (MOD-SPEC 6.3)


# The correspondence placeholder -> our name for the drafts still waiting
# at the CEO's gate. It is MOD-SPEC 6.3's table and gen_weapon.py's
# WeaponSpec (ph_held/ph_flash/ph_pickup) side by side;
# tests/test_draft_overlay.py holds them equal.
SWAPS: tuple[Swap, ...] = (
    # No weapon swap since 2026-10-20: D84 installed the IZh-58's, RPG-7's,
    # ROKS-3's and hand Katyusha's held and flash frames, D88 the ice axe's
    # (INSTALLED_WEAPON_FRAMES), with the Katyusha's floor pickup
    # (INSTALLED). A weapon drafted again joins as
    # Swap("weapons", "<folder>", "weapons/<file>.zs", "<IWAD>", "SD..").
    # No enemy swap since D55: the rifleman's POSS -> SDRR, the last one, is
    # installed (INSTALLED_ENEMIES). An enemy drafted on the rig joins as
    # Swap("enemies", "", "monsters/<file>.zs", "<IWAD>", "SD..").
)


# Approved and installed (D48, 2026-10-14): the Spawn states name our
# pickups and the PNGs ship from assets/sprites/, so the overlay carries
# none of them. (placeholder it replaced, our name), for the record and the
# tests; the held and flash frames are NOT here (hand E held back, D48).
# The hand Katyusha's floor pickup joined on 2026-10-20 (D80, its Spawn
# line changed with D84's install).
INSTALLED: tuple[tuple[str, str], ...] = (
    ("CSAW", "SDAP"),    # ice axe, pickup option C
    ("PIST", "SDTP"),    # TT-33
    ("SHOT", "SDIP"),    # IZh-58
    ("MGUN", "SDPQ"),    # PPSh-41
    ("LAUN", "SDRP"),    # RPG-7
    ("PLAS", "SDKP"),    # ROKS-3
    ("BFUG", "SDHP"),    # hand Katyusha, the D51 draft (D80, installed 2026-10-20 in pickups/)
)

# Held and flash frames approved and installed whole (N17, 2026-10-15): the
# TT-33 in Freedoom's pistol hands recoloured (R3-A1, D61; approved in hand,
# D63). Every tokarev.zs state names our sprites, the PNGs ship from
# assets/sprites/tt33/, and no swap may name either side, so the overlay can
# never shadow them with the old hand E drafts (tests/test_tt33_sprites.py).
INSTALLED_WEAPON_FRAMES: tuple[tuple[str, str], ...] = (
    ("PISG", "SDTT"),    # TT-33 held, A-C (work/art/weapons_fd/tt33/, hand_study.build_tt33_fd)
    ("PISF", "SDTF"),    # its muzzle flash, A
    # D79 (2026-10-20): the PPSh-41 from the CEO's Gemini pair
    # (tools/art/gemini_frames.py, work/art/weapons/hand_G/ppsh/;
    # tests/test_ppsh_sprites.py).
    ("CHGG", "SDPP"),    # PPSh-41 held, A-B
    ("CHGF", "SDPF"),    # its muzzle flash, A
    # D84 (2026-10-20): the IZh-58, RPG-7, ROKS-3 and hand Katyusha from the
    # CEO's Gemini images (tools/art/gemini_frames.py,
    # work/art/weapons/hand_G/<weapon>/; tests/test_gemini_weapons_install.py).
    ("SHTG", "SDIZ"),    # IZh-58 held, A-D
    ("SHTF", "SDIF"),    # its muzzle flash, A-B
    ("MISG", "SDRL"),    # RPG-7 held, A-B
    ("MISF", "SDRF"),    # its backblast and flash, A-D
    ("PLSG", "SDRK"),    # ROKS-3 held, A-B
    ("PLSF", "SDKF"),    # its flame at the nozzle, A
    ("BFGG", "SDHK"),    # hand Katyusha held, A-B
    ("BFGF", "SDHF"),    # its salvo's flash, A-B
    # D88 (2026-10-20): the ice axe, its ready frame from the CEO's Gemini
    # image and the swing rotated from it (gemini_frames.py).
    ("PUNG", "SDAX"),    # ice axe held, A-D
)

# Enemies approved and installed whole: every state names our sprite, the
# PNGs ship from assets/sprites/, and no swap may name either side, so the
# overlay can never shadow or resurrect them (tests/test_legion_sprites.py).
INSTALLED_ENEMIES: tuple[tuple[str, str], ...] = (
    ("SPOS", "SDLT"),    # Liberty Legion trooper, cell C full set (D54)
    ("POSS", "SDRR"),    # Reich rifleman, rig cell E, bloody death (D55; tests/test_rifleman_sprites.py)
    ("SARG", "SDHN"),    # Reich hound, German shepherd cell A, mirrored pairs (D55; tests/test_hound_sprites.py)
    ("TROO", "SDHS"),    # Hybrid Stormtrooper, cell E, death redone (D56; tests/test_storm_sprites.py)
    ("BAL1", "SDBL"),    # his bolt, SD_StormBolt (D56)
    ("BOS2", "SDPM"),    # Panzermensch, cell D; the Schwer draws SDPS from its own States (D67)
    ("HEAD", "SDDB"),    # Doughboy, cell C with the bigger flag (D70; tests/test_doughboy_sprites.py)
    ("CYBR", "SDGN"),    # the General, CD (D73; tests/test_general_sprites.py); Summon CYBR E F -> SDGN Q R
    ("MANF", "SDGL"),    # his shell, SD_GeneralShell, in flight; its burst was MISL B-D, not listed:
                         # the PG-7V grenade and the Katyusha rocket still wear MISL (D73)
)


class OverlayError(RuntimeError):
    """The overlay would be wrong; nothing is written."""


@dataclass(frozen=True)
class Entry:
    lump: str           # e.g. POSSA1 (the name the engine sees)
    source: Path        # the draft PNG, copied byte for byte
    grab: tuple[int, int]
    swap: Swap

    @property
    def path(self) -> str:
        return f"sprites/{self.lump}.png"


@dataclass
class Plan:
    entries: list[Entry] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)   # state frames with no draft: the IWAD's stays
    unused: list[str] = field(default_factory=list)    # drafts no state shows
    notes: list[str] = field(default_factory=list)
    hands: dict[str, str] = field(default_factory=dict)


# ------------------------------------------------------------------ ZScript
def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def state_letters(text: str, sprite: str) -> str:
    """The frame letters a States block uses with `sprite`, sorted, unique.
    A state line is `SPRT ABC <tics> ...`; `####`/`----` are other sprites."""
    letters: set[str] = set()
    for m in re.finditer(rf"^\s*{re.escape(sprite)}\s+([A-Z\[\]\\^]+)\s", strip_comments(text), re.M):
        letters |= {c for c in m.group(1) if "A" <= c <= "Z"}
    return "".join(sorted(letters))


# ---------------------------------------------------------------------- PNG
def read_grab(data: bytes) -> tuple[int, int] | None:
    """The grAb chunk (ZDoom's sprite offsets) of a PNG, or None."""
    if not data.startswith(PNG_SIGNATURE):
        raise OverlayError("not a PNG")
    i = len(PNG_SIGNATURE)
    while i + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[i:i + 8])
        if ctype == b"grAb":
            return struct.unpack(">ii", data[i + 8:i + 16])
        if ctype == b"IDAT":   # grAb must come before IDAT to count
            return None
        i += 12 + length
    return None


def draft_frames(folder: Path, draft: str) -> dict[str, dict[str, Path]]:
    """{letter: {rotation: path}} for `<draft><L><R>.png` in folder. Names
    with a suffix (`_proposed`, `_optionA`, `_variantB`) do not match."""
    out: dict[str, dict[str, Path]] = {}
    if not folder.is_dir():
        return out
    pat = re.compile(rf"^{re.escape(draft)}([A-Z])([0-9])\.png$")
    for p in sorted(folder.iterdir()):
        m = pat.match(p.name)
        if m and p.is_file():
            out.setdefault(m.group(1), {})[m.group(2)] = p
    return out


def recorded_hand(folder: Path) -> str | None:
    """The hand gen_weapon.py wrote into metrics.json, if it recorded one."""
    try:
        metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    sm = metrics.get("_state_machine")
    return sm.get("hand") if isinstance(sm, dict) else None


def weapon_folder(weapons_dir: Path, item: str, hand: str, plan: Plan) -> Path:
    """Where the renders of `item` in `hand` live.

    gen_weapon.py writes every hand into the same folder, so another hand's
    renders are looked for in `<weapons_dir>/hand_<X>/<item>/` first (render
    them there by passing out_dir to its build_* functions; nothing does yet).
    Otherwise the main folder is used if the hand it recorded is `hand`."""
    alt = weapons_dir / f"hand_{hand}" / item
    if alt.is_dir():
        plan.hands[item] = f"{hand} (hand_{hand}/)"
        return alt
    main = weapons_dir / item
    rec = recorded_hand(main)
    if rec is None:
        if hand != DEFAULT_HAND:
            raise OverlayError(
                f"{item}: no renders of hand {hand}: {alt} does not exist, and {main} does not record its "
                f"hand (gen_weapon.py draws hand {DEFAULT_HAND} by default)")
        plan.hands[item] = f"{DEFAULT_HAND} (assumed: metrics.json does not record the hand)"
        return main
    if rec != hand:
        raise OverlayError(f"{item}: the renders in {main} are hand {rec}, not {hand}; render hand {hand} "
                           f"into {alt} first")
    plan.hands[item] = rec
    return main


# --------------------------------------------------------------------- plan
def installed_sprites(sprites_dir: Path = SPRITES_DIR) -> set[str]:
    """The four-letter names of the sprites approved into assets/sprites/."""
    if not sprites_dir.is_dir():
        return set()
    return {p.stem[:4].upper() for p in sprites_dir.rglob("*.png")}


def plan_overlay(only: str = "all", hand: str = DEFAULT_HAND, weapons_dir: Path = WEAPONS_DIR,
                 rig_dir: Path = RIG_DIR, zs_root: Path | None = None,
                 sprites_dir: Path = SPRITES_DIR, item: str | None = None) -> Plan:
    """`item` packs one weapon only (e.g. a weapon's Gemini frames, hand G,
    tools/art/gemini_frames.py; every weapon drafted so far is installed:
    the PPSh's by D79, the IZh-58's, RPG-7's, ROKS-3's and hand Katyusha's
    by D84, the ice axe's by D88). `zs_root` defaults to ZS_ROOT as it
    stands at the call (the tests point it at fixture weapons)."""
    zs_root = ZS_ROOT if zs_root is None else zs_root
    groups = GROUPS if only == "all" else (only,)
    plan = Plan()
    zs_cache: dict[str, str] = {}
    installed = installed_sprites(sprites_dir)
    retired = {name for pair in INSTALLED_ENEMIES for name in pair}
    retired_frames = {name for pair in INSTALLED_WEAPON_FRAMES for name in pair}
    for swap in SWAPS:
        if swap.group not in groups or (item is not None and swap.item != item):
            continue
        if swap.placeholder in retired or swap.draft in retired:
            plan.notes.append(f"{swap.draft}: an enemy installed whole (INSTALLED_ENEMIES); "
                              f"not overlaid on {swap.placeholder}")
            continue
        if swap.placeholder in retired_frames or swap.draft in retired_frames:
            plan.notes.append(f"{swap.draft}: held and flash frames installed whole "
                              f"(INSTALLED_WEAPON_FRAMES); not overlaid on {swap.placeholder}")
            continue
        if swap.draft in installed:
            plan.notes.append(f"{swap.draft}: approved and installed under {_rel(sprites_dir)}; "
                              f"not overlaid on {swap.placeholder}")
            continue
        if swap.zs not in zs_cache:
            zs_cache[swap.zs] = (zs_root / swap.zs).read_text(encoding="utf-8")
        letters = state_letters(zs_cache[swap.zs], swap.placeholder)
        if swap.group == "weapons":
            folder = weapon_folder(weapons_dir, swap.item, hand, plan)
        else:
            folder = rig_dir
        drafts = draft_frames(folder, swap.draft)
        if not letters:
            plan.notes.append(f"{swap.placeholder}: src/zscript/{swap.zs} no longer names it (the real "
                              f"sprite may have landed); {swap.draft} skipped")
            continue
        for letter in sorted(set(drafts) - set(letters)):
            for rot in sorted(drafts[letter]):
                plan.unused.append(f"{swap.draft}{letter}{rot} (no {swap.placeholder} {letter} state)")
        for letter in letters:
            rots = drafts.get(letter)
            if not rots:
                plan.missing.append(f"{swap.placeholder}{letter} (no {swap.draft}{letter} draft in "
                                    f"{_rel(folder)}; the IWAD's stays)")
                continue
            if "0" in rots and len(rots) > 1:
                raise OverlayError(f"{swap.draft}{letter}: both rotation 0 and rotations "
                                   f"{''.join(sorted(set(rots) - {'0'}))} in {_rel(folder)}")
            if "0" not in rots and set(rots) != set(ROTATIONS_8):
                raise OverlayError(
                    f"{swap.draft}{letter}: rotations {''.join(sorted(rots))} only; a rotated frame needs "
                    f"all of {ROTATIONS_8}, or the IWAD's {swap.placeholder}{letter} fills the gaps and the "
                    f"sprite changes drawing as it turns")
            for rot, src in sorted(rots.items()):
                grab = read_grab(src.read_bytes())
                if grab is None:
                    raise OverlayError(f"{_rel(src)} has no grAb chunk before its image data: GZDoom "
                                       f"would draw it at offset 0,0")
                plan.entries.append(Entry(f"{swap.placeholder}{letter}{rot}", src, grab, swap))
    if not plan.entries:
        raise OverlayError("nothing to pack: no draft matches a state frame")
    return plan


def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(p)


# --------------------------------------------------------------------- IWAD
def iwad_sprites(path: Path) -> set[str]:
    """Lump names between S_START/SS_START and S_END/SS_END of a WAD."""
    blob = path.read_bytes()
    count, offset = struct.unpack("<ii", blob[4:12])
    sprites, inside = set(), False
    for i in range(count):
        name = blob[offset + 16 * i + 8: offset + 16 * i + 16].rstrip(b"\0").decode("ascii", "replace").upper()
        if name in ("S_START", "SS_START"):
            inside = True
        elif name in ("S_END", "SS_END"):
            inside = False
        elif inside:
            sprites.add(name)
    return sprites


def iwad_rotations(sprites: set[str], sprite: str, letter: str) -> tuple[set[str], int]:
    """(rotation chars the IWAD gives frame `letter` of `sprite`, number of
    lumps that are mirrored pairs such as POSSA2A8)."""
    rots: set[str] = set()
    pairs = 0
    for name in sprites:
        if not name.startswith(sprite):
            continue
        hit = False
        if name[4:5] == letter:
            rots.add(name[5:6])
            hit = True
        if len(name) == 8 and name[6:7] == letter:
            rots.add(name[7:8])
            hit = True
        if hit and len(name) == 8:
            pairs += 1
    return rots, pairs


def check_against_iwad(plan: Plan, sprites: set[str]) -> None:
    """Refuse a rotated frame the IWAD would still leak into; note what is hidden."""
    frames: dict[tuple[str, str], list[str]] = {}
    for e in plan.entries:
        frames.setdefault((e.lump[:4], e.lump[4]), []).append(e.lump[5])
    for (sprite, letter), ours in sorted(frames.items()):
        theirs, pairs = iwad_rotations(sprites, sprite, letter)
        if not theirs:
            plan.notes.append(f"{sprite}{letter}: not in the IWAD; only the overlay defines it")
            continue
        if ours == ["0"]:
            continue    # rotation 0 fills all 16 slots first: nothing of the IWAD's is left to show
        if "0" in theirs:
            raise OverlayError(f"{sprite}{letter}: ours has rotations 1-8 but the IWAD has rotation 0, "
                               f"which would fill the 16-angle slots ours leave empty")
        wide = sorted(r for r in theirs if r not in ROTATIONS_8)
        if wide:
            raise OverlayError(f"{sprite}{letter}: the IWAD has 16-angle rotations {''.join(wide)}, which "
                               f"would fill the slots our eight leave empty")
        if pairs:
            plan.notes.append(f"{sprite}{letter}: hides {pairs} mirrored pair lump(s) of the IWAD")


# -------------------------------------------------------------------- write
def guard_out(out: Path, root: Path = PROJECT_ROOT) -> None:
    resolved = out.resolve()
    for name in FORBIDDEN_OUT:
        base = (root / name).resolve()
        if resolved == base or base in resolved.parents:
            raise OverlayError(f"refusing to write {out}: nothing of the draft overlay goes under {name}/")


def write_pk3(plan: Plan, out: Path) -> Path:
    """A deterministic zip holding only sprites/<LUMP>.png, bytes unchanged."""
    guard_out(out)
    seen: set[str] = set()
    for e in plan.entries:
        if e.lump in seen:
            raise OverlayError(f"{e.lump} would be packed twice")
        seen.add(e.lump)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for e in sorted(plan.entries, key=lambda e: e.path):
            info = zipfile.ZipInfo(e.path, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, e.source.read_bytes())
    tmp.replace(out)
    return out


def manifest_text(plan: Plan, out: Path, iwad: Path | None) -> str:
    lines = [f"# Draft sprite overlay {out.name}: NOT APPROVED ART. Load it after the mod:",
             f"#   SD_ALLOW_ENGINE=1 tools/run.sh -file {_rel(out)}",
             f"# IWAD rotation check: {_rel(iwad) if iwad else 'skipped (no IWAD)'}",
             f"# {len(plan.entries)} lumps", ""]
    for item, hand in sorted(plan.hands.items()):
        lines.append(f"hand {item}: {hand}")
    lines.append("")
    for e in sorted(plan.entries, key=lambda e: e.path):
        lines.append(f"{e.path:<22} <- {_rel(e.source)}  grAb {e.grab[0]},{e.grab[1]}")
    for title, rows in (("state frames with no draft (IWAD placeholder stays)", plan.missing),
                        ("drafts no state shows (not packed)", plan.unused), ("notes", plan.notes)):
        if rows:
            lines += ["", f"# {title}"] + [f"  {r}" for r in rows]
    return "\n".join(lines) + "\n"


def default_out(only: str, hand: str, item: str | None = None) -> Path:
    stem = {"all": "sd-draft-sprites", "weapons": "sd-draft-weapons", "enemies": "sd-draft-enemies"}[only]
    if hand != DEFAULT_HAND and only != "enemies":
        stem += f"-hand{hand}"
    if item:
        stem += f"-{item}"
    return OUT_DIR / f"{stem}.pk3"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", choices=("all", *GROUPS), default="all")
    ap.add_argument("--hand", default=DEFAULT_HAND, type=str.upper,
                    help="which hand's weapon renders to use (default E, the one drawn)")
    ap.add_argument("--item", choices=sorted({s.item for s in SWAPS if s.group == "weapons"}),
                    help="pack this weapon only (e.g. --hand G --item <weapon>: its Gemini frames)")
    ap.add_argument("--out", type=Path, help="output PK3 (default work/overlays/sd-draft-*.pk3)")
    ap.add_argument("--weapons-dir", type=Path, default=WEAPONS_DIR)
    ap.add_argument("--rig-dir", type=Path, default=RIG_DIR)
    ap.add_argument("--sprites-dir", type=Path, default=SPRITES_DIR,
                    help="the installed sprites, never overlaid (default assets/sprites)")
    ap.add_argument("--iwad", type=Path, default=IWAD,
                    help="IWAD for the rotation check (skipped when absent)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[A-Z]", args.hand):
        ap.error("--hand takes one letter, A-F in gen_weapon.py's sweep")
    out = args.out or default_out(args.only, args.hand, args.item)
    try:
        guard_out(out)
        plan = plan_overlay(args.only, args.hand, args.weapons_dir, args.rig_dir,
                            sprites_dir=args.sprites_dir, item=args.item)
        iwad = args.iwad if args.iwad and args.iwad.is_file() else None
        if iwad:
            check_against_iwad(plan, iwad_sprites(iwad))
        text = manifest_text(plan, out, iwad)
        if args.dry_run:
            print(text, end="")
            return 0
        write_pk3(plan, out)
        out.with_suffix(".txt").write_text(text, encoding="utf-8")
    except OverlayError as exc:
        print(f"make_draft_overlay: {exc}", file=sys.stderr)
        return 1
    print(text, end="")
    print(f"wrote {_rel(out)} ({len(plan.entries)} sprite lumps) and {_rel(out.with_suffix('.txt'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
