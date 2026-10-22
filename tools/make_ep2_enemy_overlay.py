#!/usr/bin/env python3
"""Pack the Episode 2 enemies DRAFT overlay: two new classes, playable by summon.

    python tools/make_ep2_enemy_overlay.py             # -> work/overlays/sd-ep2-enemies.pk3 (+ .txt)
    python tools/make_ep2_enemy_overlay.py --dry-run   # print the plan, write nothing

    SD_ALLOW_ENGINE=1 tools/run.sh -file work/overlays/sd-ep2-enemies.pk3
    (then, in the console: summon SD_LegionGunner / summon SD_LibertyColossus)

Why. D104 asks for two new Liberty Legion enemies for Episode 2, the heavy
machine-gunner `SD_LegionGunner` and the boss `SD_LibertyColossus`. Their art
is still being drawn; their BEHAVIOUR can be played now, on provisional
sprites the mod already ships (the trooper's SDLT and the General's SDGN,
tinted). Until the CEO approves the art nothing of them enters the mod, so
they live in a SEPARATE, self-contained PK3 loaded after it, as the draft
sprite overlay does (MOD-SPEC 6.9, tools/make_draft_overlay.py). That tool
swaps sprites under placeholder names and carries no code; this one carries
code and lumps and no sprites, so it is its own script rather than a mode
of the other. Design and integration plan:
docs/engine/2026-10-22_P4_ep2-enemies.md.

What it reads (never writes):
  work/overlays/ep2-enemies/      the overlay's source tree (gitignored work/):
      zscript.txt                 its own ZSCRIPT root: version + #includes only
      zscript/sd_ep2/*.zs         the classes
      MAPINFO                     a DoomEdNums block only
      LANGUAGE                    its SD_ ids in [enu default], [ru] and [ca]
  src/lumps/MAPINFO, src/zscript/ (the mod) to refuse an editor number, a
                                  class name or a file path the mod already has

What it writes: work/overlays/sd-ep2-enemies.pk3, a deterministic zip of
exactly those files at those paths, and a plain-text manifest beside it.
Refuses to write under src/, dist/ or assets/.

Refusals (exit 1, the reason printed): a file in the source tree that is not
one of the four kinds above; an #include that names a missing file, or a .zs
no #include names; a DoomEdNum the mod's MAPINFO already assigns, or one
outside the enemy sub-range 21100-21199; a class the mod already declares;
an overlay path that is also a path in the mod (it would shadow it).

Exit codes: 0 built (or dry run), 1 refused. Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "work" / "overlays" / "ep2-enemies"
OUT = PROJECT_ROOT / "work" / "overlays" / "sd-ep2-enemies.pk3"
MOD_SRC = PROJECT_ROOT / "src"
# Nothing of a draft goes into the build input, the build output or the
# approved art: reaching any of them is an approval the CEO did not give.
FORBIDDEN_OUT = ("src", "dist", "assets")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # as tools/sdbuild/pk3.py: reproducible
ROOT_LUMPS = ("zscript.txt", "MAPINFO", "LANGUAGE")
ZS_DIR = "zscript/sd_ep2/"
ENEMY_EDNUMS = range(21100, 21200)       # MOD-SPEC 6.1: the enemy sub-range


class OverlayError(Exception):
    """A reason to refuse; printed, exit 1."""


@dataclass
class Plan:
    src: Path
    files: dict[str, Path] = field(default_factory=dict)   # pk3 path -> source file
    classes: dict[str, str] = field(default_factory=dict)  # class -> pk3 path
    ednums: dict[int, str] = field(default_factory=dict)   # number -> class


# --------------------------------------------------------------------- parse
def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def zscript_includes(text: str) -> list[str]:
    return re.findall(r'^\s*#include\s+"([^"]+)"', strip_comments(text), flags=re.M)


def zscript_classes(text: str) -> list[str]:
    return re.findall(r"^\s*class\s+(\w+)", strip_comments(text), flags=re.M)


def mapinfo_ednums(text: str) -> dict[int, str]:
    """Every `N = Class` inside every DoomEdNums block."""
    out: dict[int, str] = {}
    for block in re.findall(r"DoomEdNums\s*\{(.*?)\}", strip_comments(text), flags=re.S):
        for num, cls in re.findall(r"^\s*(\d+)\s*=\s*(\w+)", block, flags=re.M):
            out[int(num)] = cls
    return out


def mod_classes(zs_root: Path = MOD_SRC / "zscript") -> set[str]:
    names: set[str] = set()
    for p in zs_root.rglob("*.zs"):
        names.update(zscript_classes(p.read_text(encoding="utf-8")))
    return names


def mod_paths(src: Path = MOD_SRC) -> set[str]:
    """The pk3 paths of the mod's ZScript files (src/zscript/** -> zscript/**).

    The root lumps (zscript.txt, MAPINFO, LANGUAGE) are left out on purpose:
    GZDoom reads every lump of those names from every file and merges them,
    so the overlay's own copies add to the mod's instead of hiding them."""
    return {f"zscript/{p.relative_to(src / 'zscript').as_posix()}" for p in (src / "zscript").rglob("*.zs")}


# ---------------------------------------------------------------------- plan
def plan_overlay(src: Path = SRC_DIR, mod_src: Path = MOD_SRC) -> Plan:
    if not src.is_dir():
        raise OverlayError(f"no overlay source at {src}")
    plan = Plan(src=src)
    for p in sorted(src.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(src).as_posix()
        if rel in ROOT_LUMPS or (rel.startswith(ZS_DIR) and rel.endswith(".zs") and rel.count("/") == 2):
            plan.files[rel] = p
        else:
            raise OverlayError(f"{rel}: not an overlay file (allowed: {', '.join(ROOT_LUMPS)}, {ZS_DIR}*.zs)")
    for lump in ROOT_LUMPS:
        if lump not in plan.files:
            raise OverlayError(f"missing {lump}")

    # The ZSCRIPT root: every include exists, every .zs is included.
    includes = zscript_includes(plan.files["zscript.txt"].read_text(encoding="utf-8"))
    zs_files = {k for k in plan.files if k.endswith(".zs")}
    for inc in includes:
        if inc not in plan.files:
            raise OverlayError(f"zscript.txt includes {inc}, which is not in the overlay")
    for orphan in sorted(zs_files - set(includes)):
        raise OverlayError(f"{orphan} is not #included by zscript.txt")

    # No path, class or editor number the mod already has.
    shadowed = zs_files & mod_paths(mod_src)
    if shadowed:
        raise OverlayError(f"would shadow the mod's {sorted(shadowed)}")
    known = mod_classes(mod_src / "zscript")
    for rel in sorted(zs_files):
        for cls in zscript_classes(plan.files[rel].read_text(encoding="utf-8")):
            if cls in known:
                raise OverlayError(f"{rel}: class {cls} is already the mod's")
            if cls in plan.classes:
                raise OverlayError(f"{rel}: class {cls} declared twice")
            plan.classes[cls] = rel

    mod_numbers = mapinfo_ednums((mod_src / "lumps" / "MAPINFO").read_text(encoding="utf-8"))
    plan.ednums = mapinfo_ednums(plan.files["MAPINFO"].read_text(encoding="utf-8"))
    if not plan.ednums:
        raise OverlayError("MAPINFO assigns no editor number")
    for num, cls in sorted(plan.ednums.items()):
        if num in mod_numbers:
            raise OverlayError(f"DoomEdNum {num} is already the mod's {mod_numbers[num]}")
        if num not in ENEMY_EDNUMS:
            raise OverlayError(f"DoomEdNum {num} is outside the enemy sub-range 21100-21199")
        if cls not in plan.classes:
            raise OverlayError(f"DoomEdNum {num} names {cls}, which the overlay does not declare")
    return plan


# --------------------------------------------------------------------- write
def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(p)


def guard_out(out: Path, root: Path = PROJECT_ROOT) -> None:
    resolved = out.resolve()
    for name in FORBIDDEN_OUT:
        base = (root / name).resolve()
        if resolved == base or base in resolved.parents:
            raise OverlayError(f"refusing to write {out}: nothing of a draft overlay goes under {name}/")


def write_pk3(plan: Plan, out: Path) -> Path:
    """A deterministic zip of the plan's files, bytes unchanged."""
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in sorted(plan.files):
            info = zipfile.ZipInfo(rel, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, plan.files[rel].read_bytes())
    tmp.replace(out)
    return out


def manifest_text(plan: Plan, out: Path) -> str:
    lines = [f"# Episode 2 enemies DRAFT overlay {out.name}: NOT IN THE MOD. Load it after the mod:",
             f"#   SD_ALLOW_ENGINE=1 tools/run.sh -file {_rel(out)}",
             "#   console: summon SD_LegionGunner / summon SD_LibertyColossus",
             f"# source: {_rel(plan.src)}", f"# {len(plan.files)} files", ""]
    lines += [f"{rel:<40} <- {_rel(p)}" for rel, p in sorted(plan.files.items())]
    lines += ["", "# classes"] + [f"  {c:<22} {rel}" for c, rel in sorted(plan.classes.items())]
    lines += ["", "# editor numbers"] + [f"  {n} = {c}" for n, c in sorted(plan.ednums.items())]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=SRC_DIR, help="overlay source tree")
    ap.add_argument("--out", type=Path, default=OUT, help="output PK3")
    ap.add_argument("--mod-src", type=Path, default=MOD_SRC, help=argparse.SUPPRESS)
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args(argv)
    try:
        guard_out(args.out)
        plan = plan_overlay(args.src, args.mod_src)
        text = manifest_text(plan, args.out)
        if args.dry_run:
            print(text, end="")
            return 0
        write_pk3(plan, args.out)
        args.out.with_suffix(".txt").write_text(text, encoding="utf-8")
    except OverlayError as exc:
        print(f"make_ep2_enemy_overlay: {exc}", file=sys.stderr)
        return 1
    print(text, end="")
    print(f"wrote {_rel(args.out)} ({len(plan.files)} files) and {_rel(args.out.with_suffix('.txt'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
