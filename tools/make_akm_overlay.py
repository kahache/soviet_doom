#!/usr/bin/env python3
"""Pack the AKM DRAFT overlay: the second slot-4 weapon, playable by `give`.

    .venv/Scripts/python.exe tools/make_akm_overlay.py --sprites   # (re)draw the provisional sprites (Pillow)
    python tools/make_akm_overlay.py             # -> work/overlays/sd-draft-akm.pk3 (+ .txt)
    python tools/make_akm_overlay.py --dry-run   # print the plan, write nothing

    SD_ALLOW_ENGINE=1 tools/run.sh -file work/overlays/sd-draft-akm.pk3
    (then, in the console: give SD_Akm / give SD_AkmAmmo / summon SD_AkmAmmo)

Why. D112: the CEO asked for "more weapons" for V2 (docs/ICEBOX.md, "V2
content"). The first is the AKM, the 1970s Soviet assault rifle in
7.62x39, as a SECOND weapon in slot 4 beside the PPSh-41. Its art is not
drawn yet; its BEHAVIOUR can be played now, on provisional sprites made
from the PPSh-41's installed frames (tinted, never shipped in the mod).
Until the CEO approves it nothing of it enters the mod, so it lives in a
SEPARATE, self-contained PK3 loaded after it, like the Episode 2 enemies
(tools/make_ep2_enemy_overlay.py, whose parsing and guards this tool
reuses). Unlike that overlay, this one carries its own sprites (four new
names, never a name the mod has) and a SNDINFO of new logical names over
lumps the mod already ships. Design, balance and integration plan:
docs/engine/2026-10-22_P4_akm.md.

What it reads (never writes, except --sprites, which writes only the
overlay's own sprites/ folder):
  work/overlays/akm/              the overlay's source tree (gitignored work/):
      zscript.txt                 its own ZSCRIPT root: version + #includes only
      zscript/sd_akm/*.zs         the classes
      MAPINFO                     a DoomEdNums block only
      LANGUAGE                    its SD_ ids in [enu default], [ru] and [ca]
      SNDINFO                     its sd/weapon/akm/* names
      sprites/<NAME><F>0.png      provisional sprites, NAME one of OWN_SPRITES
  src/lumps/MAPINFO, src/zscript/, assets/sprites/ (the mod) to refuse an
                                  editor number, a class, a file path or a
                                  sprite name the mod already has
  assets/sprites/ppsh/, assets/sprites/pickups/SDCLA0.png  (--sprites only)

What it writes: work/overlays/sd-draft-akm.pk3, a deterministic zip of
exactly those files at those paths, and a plain-text manifest beside it.
Refuses to write under src/, dist/ or assets/.

Refusals (exit 1, the reason printed): a file that is not one of the kinds
above; an #include of a missing file, or a .zs no #include names; a
DoomEdNum the mod's MAPINFO assigns, or one outside the weapon and ammo
sub-ranges 21000-21039 (MOD-SPEC 6.1); a class the mod declares; a path
that would shadow a mod file; a sprite that is not a PNG, not one of
OWN_SPRITES, or whose four-letter name the mod's assets/sprites/ uses.

Exit codes: 0 built (or dry run), 1 refused. Packing is standard library
only; --sprites needs Pillow (the venv).
"""

from __future__ import annotations

import argparse
import io
import re
import struct
import sys
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path

from make_ep2_enemy_overlay import (  # the same parsing and guards as the Episode 2 overlay
    FIXED_ZIP_TIME,
    OverlayError,
    guard_out,
    mapinfo_ednums,
    mod_classes,
    mod_paths,
    zscript_classes,
    zscript_includes,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "work" / "overlays" / "akm"
OUT = PROJECT_ROOT / "work" / "overlays" / "sd-draft-akm.pk3"
MOD_SRC = PROJECT_ROOT / "src"
MOD_SPRITES = PROJECT_ROOT / "assets" / "sprites"
ROOT_LUMPS = ("zscript.txt", "MAPINFO", "LANGUAGE", "SNDINFO")
ZS_DIR = "zscript/sd_akm/"
SPRITE_DIR = "sprites/"
# MOD-SPEC 6.1: 21000-21019 weapons, 21020-21039 ammo and items.
WEAPON_AMMO_EDNUMS = range(21000, 21040)
# The AKM's four sprite names (MOD-SPEC 6.3 reserves nothing starting SDAK,
# SDAF, SDAQ or SDAM; the mod's SDA* are SDAB, SDAG, SDAH, SDAP, SDAX).
OWN_SPRITES = ("SDAK", "SDAF", "SDAQ", "SDAM")
SPRITE_NAME = re.compile(r"^([A-Z0-9]{4})([A-Z])0\.png$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

# --sprites: which installed lump each provisional sprite is made from, and
# whether it is tinted. The flash is the PPSh's own, renamed (a flash is a
# flash); everything the player looks at is tinted so it never reads as the
# PPSh-41.
SPRITE_SOURCES: dict[str, tuple[str, bool]] = {
    "SDAKA0": ("ppsh/SDPPA0.png", True),     # held, ready
    "SDAKB0": ("ppsh/SDPPB0.png", True),     # held, firing (the kick)
    "SDAFA0": ("ppsh/SDPFA0.png", False),    # muzzle flash
    "SDAQA0": ("ppsh/SDPQA0.png", True),     # world pickup
    "SDAMA0": ("pickups/SDCLA0.png", True),  # magazine pickup (from the 7.62x25 magazine)
}
# The tint: the luminance of each pixel mapped onto a warm plum-orange (the
# AKM's laminated wood and phosphated steel read browner and redder than
# the PPSh's blued steel and birch), blended with the original so hands
# still read as hands. Alpha untouched. PROVISIONAL, like the sprites.
TINT_GAIN = (1.30, 0.78, 0.52)
TINT_STRENGTH = 0.65


@dataclass
class Plan:
    src: Path
    files: dict[str, Path] = field(default_factory=dict)   # pk3 path -> source file
    classes: dict[str, str] = field(default_factory=dict)  # class -> pk3 path
    ednums: dict[int, str] = field(default_factory=dict)   # number -> class
    sprites: list[str] = field(default_factory=list)       # lump names


# ------------------------------------------------------------------- sprites
def png_grab(data: bytes) -> tuple[int, int] | None:
    """The grAb offsets of a PNG, or None."""
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        if ctype == b"grAb":
            return struct.unpack(">ii", data[pos + 8:pos + 16])
        if ctype == b"IEND":
            return None
        pos += 12 + length
    return None


def with_grab(data: bytes, x: int, y: int) -> bytes:
    """`data` with a grAb chunk (ZDoom's sprite offsets) right after IHDR.

    Pillow does not write private chunks, so a re-saved sprite gets its
    offsets back here. An existing grAb is dropped first."""
    if not data.startswith(PNG_SIGNATURE):
        raise OverlayError("not a PNG")
    chunks = []
    pos = len(PNG_SIGNATURE)
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + length
        if ctype != b"grAb":
            chunks.append(data[pos:end])
        pos = end
    body = struct.pack(">ii", x, y)
    grab = struct.pack(">I", len(body)) + b"grAb" + body + struct.pack(">I", zlib.crc32(b"grAb" + body) & 0xFFFFFFFF)
    return PNG_SIGNATURE + chunks[0] + grab + b"".join(chunks[1:])


def tint_rgba(pixels, gain=TINT_GAIN, strength=TINT_STRENGTH):
    """[(r, g, b, a)] -> the same list tinted; alpha untouched."""
    out = []
    for r, g, b, a in pixels:
        lum = (0.299 * r + 0.587 * g + 0.114 * b)
        tinted = [min(255.0, lum * k) for k in gain]
        out.append(tuple(int(round(c * (1 - strength) + t * strength)) for c, t in zip((r, g, b), tinted)) + (a,))
    return out


def make_sprites(sprites_root: Path = MOD_SPRITES, dest: Path = SRC_DIR / "sprites") -> list[Path]:
    """Draw the provisional sprites into the overlay's sprites/ folder."""
    from PIL import Image   # the venv's; only this mode needs it

    guard_out(dest)
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for name, (rel, tinted) in sorted(SPRITE_SOURCES.items()):
        src = sprites_root / rel
        data = src.read_bytes()
        grab = png_grab(data)
        if grab is None:
            raise OverlayError(f"{rel} has no grAb offsets")
        if tinted:
            im = Image.open(io.BytesIO(data)).convert("RGBA")
            flat = getattr(im, "get_flattened_data", im.getdata)   # getdata is deprecated in Pillow 12
            im.putdata(tint_rgba(list(flat())))
            buf = io.BytesIO()
            im.save(buf, format="PNG", optimize=False)
            data = with_grab(buf.getvalue(), *grab)
        out = dest / f"{name}.png"
        out.write_bytes(data)
        written.append(out)
    return written


# ---------------------------------------------------------------------- plan
def mod_sprite_names(sprites_root: Path = MOD_SPRITES) -> set[str]:
    return {p.name[:4].upper() for p in sprites_root.rglob("*.png")} if sprites_root.is_dir() else set()


def plan_overlay(src: Path = SRC_DIR, mod_src: Path = MOD_SRC, mod_sprites: Path = MOD_SPRITES) -> Plan:
    if not src.is_dir():
        raise OverlayError(f"no overlay source at {src}")
    plan = Plan(src=src)
    taken = mod_sprite_names(mod_sprites)
    for p in sorted(src.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(src).as_posix()
        if rel in ROOT_LUMPS or (rel.startswith(ZS_DIR) and rel.endswith(".zs") and rel.count("/") == 2):
            plan.files[rel] = p
        elif rel.startswith(SPRITE_DIR) and rel.count("/") == 1:
            m = SPRITE_NAME.match(p.name)
            if not m:
                raise OverlayError(f"{rel}: a sprite is <NAME><FRAME>0.png (rotation 0)")
            if m.group(1) not in OWN_SPRITES:
                raise OverlayError(f"{rel}: {m.group(1)} is not one of the AKM's sprites {OWN_SPRITES}")
            if m.group(1) in taken:
                raise OverlayError(f"{rel}: {m.group(1)} is already a sprite of the mod (assets/sprites/)")
            if not p.read_bytes().startswith(PNG_SIGNATURE):
                raise OverlayError(f"{rel}: not a PNG")
            plan.files[rel] = p
            plan.sprites.append(p.stem)
        else:
            raise OverlayError(f"{rel}: not an overlay file "
                               f"(allowed: {', '.join(ROOT_LUMPS)}, {ZS_DIR}*.zs, {SPRITE_DIR}*.png)")
    for lump in ROOT_LUMPS:
        if lump not in plan.files:
            raise OverlayError(f"missing {lump}")

    includes = zscript_includes(plan.files["zscript.txt"].read_text(encoding="utf-8"))
    zs_files = {k for k in plan.files if k.endswith(".zs")}
    for inc in includes:
        if inc not in plan.files:
            raise OverlayError(f"zscript.txt includes {inc}, which is not in the overlay")
    for orphan in sorted(zs_files - set(includes)):
        raise OverlayError(f"{orphan} is not #included by zscript.txt")

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
        if num not in WEAPON_AMMO_EDNUMS:
            raise OverlayError(f"DoomEdNum {num} is outside the weapon and ammo sub-ranges 21000-21039")
        if cls not in plan.classes:
            raise OverlayError(f"DoomEdNum {num} names {cls}, which the overlay does not declare")
    return plan


# --------------------------------------------------------------------- write
def _rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(p)


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
    lines = [f"# AKM DRAFT overlay {out.name}: NOT IN THE MOD. Load it after the mod:",
             f"#   SD_ALLOW_ENGINE=1 tools/run.sh -file {_rel(out)}",
             "#   console: give SD_Akm / give SD_AkmAmmo / summon SD_Akm / summon SD_AkmAmmo",
             f"# source: {_rel(plan.src)}", f"# {len(plan.files)} files", ""]
    lines += [f"{rel:<40} <- {_rel(p)}" for rel, p in sorted(plan.files.items())]
    lines += ["", "# classes"] + [f"  {c:<22} {rel}" for c, rel in sorted(plan.classes.items())]
    lines += ["", "# editor numbers"] + [f"  {n} = {c}" for n, c in sorted(plan.ednums.items())]
    lines += ["", "# provisional sprites"] + [f"  {s}" for s in sorted(plan.sprites)]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", type=Path, default=SRC_DIR, help="overlay source tree")
    ap.add_argument("--out", type=Path, default=OUT, help="output PK3")
    ap.add_argument("--mod-src", type=Path, default=MOD_SRC, help=argparse.SUPPRESS)
    ap.add_argument("--mod-sprites", type=Path, default=MOD_SPRITES, help=argparse.SUPPRESS)
    ap.add_argument("--sprites", action="store_true",
                    help="first (re)draw the provisional sprites into <src>/sprites/ (needs Pillow)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = ap.parse_args(argv)
    try:
        guard_out(args.out)
        if args.sprites and not args.dry_run:
            for p in make_sprites(args.mod_sprites, args.src / "sprites"):
                print(f"drew {_rel(p)}")
        plan = plan_overlay(args.src, args.mod_src, args.mod_sprites)
        text = manifest_text(plan, args.out)
        if args.dry_run:
            print(text, end="")
            return 0
        write_pk3(plan, args.out)
        args.out.with_suffix(".txt").write_text(text, encoding="utf-8")
    except OverlayError as exc:
        print(f"make_akm_overlay: {exc}", file=sys.stderr)
        return 1
    print(text, end="")
    print(f"wrote {_rel(args.out)} ({len(plan.files)} files) and {_rel(args.out.with_suffix('.txt'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
