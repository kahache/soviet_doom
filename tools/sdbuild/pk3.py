"""Assemble the mod PK3 from the src/ tree.

A PK3 is a plain zip that GZDoom mounts like a WAD. Folder names are
meaningful (maps/, textures/, flats/, sprites/, sounds/, music/, graphics/,
zscript/), and files at the root become lumps named after the file without
its extension (MAPINFO, LANGUAGE, zscript.txt -> ZSCRIPT ...).

Layout of src/ (see docs/engine/MOD-SPEC.md for the contract):
  src/lumps/<NAME>            -> <NAME> at the PK3 root
  src/zscript/**              -> zscript/** (included from zscript.txt)
  src/maps/<MAP>/map.py       -> maps/<MAP>.wad generated from Python
  src/maps/<MAP>.wad          -> maps/<MAP>.wad copied verbatim (UDB output)
  src/<assetdir>/**           -> <assetdir>/** copied verbatim for the
                                 standard asset folders listed below

The zip is deterministic: fixed timestamps, sorted entries, so two builds of
the same sources are byte-identical.
"""

from __future__ import annotations

import importlib.util
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from sdbuild.wad import build_pwad, validate_lump_name

ASSET_DIRS = ("textures", "flats", "sprites", "sounds", "music", "graphics",
              "patches", "hires", "fonts")
# `fonts` is the one asset folder whose SUBFOLDER is meaningful: GZDoom reads
# a folder font as fonts/<fontname>/<HEX>.png, so flattening it the way a
# texture set is flattened would destroy the font. Listed here so the build
# keeps the path intact.
NESTED_ASSET_DIRS = ("fonts",)
MAP_SCRIPT_NAME = "map.py"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)  # earliest zip timestamp; reproducible builds
IGNORED_FILES = {".DS_Store", "Thumbs.db"}


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class Entry:
    path: str      # path inside the PK3, forward slashes
    data: bytes


def _iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name not in IGNORED_FILES and "__pycache__" not in p.parts:
            yield p


def _load_map_module(script: Path, tools_dir: Path):
    """Import src/maps/<MAP>/map.py as an isolated module."""
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    spec = importlib.util.spec_from_file_location(f"sdmap_{script.parent.name}", script)
    if spec is None or spec.loader is None:
        raise BuildError(f"cannot import map script {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "lumps"):
        raise BuildError(f"{script} must define lumps() -> list[(name, bytes)]")
    return module


def collect_maps(src: Path, tools_dir: Path) -> list[Entry]:
    entries: list[Entry] = []
    maps_dir = src / "maps"
    if not maps_dir.is_dir():
        return entries
    for child in sorted(maps_dir.iterdir()):
        if child.is_dir():
            script = child / MAP_SCRIPT_NAME
            if not script.is_file():
                continue
            map_name = validate_lump_name(child.name)
            module = _load_map_module(script, tools_dir)
            lumps = module.lumps()
            if not lumps or lumps[0][0].upper() != map_name:
                raise BuildError(
                    f"{script}: first lump must be the map marker {map_name!r}, got {lumps[0][0] if lumps else None!r}"
                )
            entries.append(Entry(f"maps/{map_name}.wad", build_pwad(lumps)))
        elif child.suffix.lower() == ".wad":
            map_name = validate_lump_name(child.stem)
            entries.append(Entry(f"maps/{map_name}.wad", child.read_bytes()))
    return entries


def collect_lumps(src: Path) -> list[Entry]:
    entries: list[Entry] = []
    lumps_dir = src / "lumps"
    if not lumps_dir.is_dir():
        return entries
    for p in _iter_files(lumps_dir):
        if p.parent != lumps_dir:
            raise BuildError(f"src/lumps must be flat, found {p}")
        # Root files become lumps named after the stem; enforce the 8-char rule.
        validate_lump_name(p.stem)
        entries.append(Entry(p.name, p.read_bytes()))
    return entries


def collect_tree(src: Path, folder: str) -> list[Entry]:
    base = src / folder
    if not base.is_dir():
        return []
    entries = []
    for p in _iter_files(base):
        rel = p.relative_to(src).as_posix()
        entries.append(Entry(rel, p.read_bytes()))
    return entries


def collect_assets(assets: Path) -> list[Entry]:
    """Approved art from `assets/<folder>/<set>/NAME.png` -> `<folder>/NAME.png`.

    The art pipeline keeps CEO-approved PNGs in `assets/`, grouped by set
    (`assets/textures/soviet_base/SDCONC1.png`). GZDoom names a lump after the
    file, so the set folder is dropped on the way in: the engine sees
    `textures/SDCONC1.png` and the map's `SDCONC1` resolves. Without this the
    textures never reach the PK3 and every map referencing them dies with
    "Unknown texture" (blocker M1, found by level-designer 2026-10-12).
    """
    if not assets.is_dir():
        return []
    entries: list[Entry] = []
    for folder in ASSET_DIRS:
        base = assets / folder
        if not base.is_dir():
            continue
        for p in _iter_files(base):
            if folder in NESTED_ASSET_DIRS:
                # keep fonts/<fontname>/<HEX>.png; the engine needs the folder
                rel = p.relative_to(assets).as_posix()
            else:
                rel = f"{folder}/{p.name}"            # drop the set folder
            entries.append(Entry(rel, p.read_bytes()))
    return entries


def collect_entries(src: Path, tools_dir: Path, assets: Path | None = None) -> list[Entry]:
    entries: list[Entry] = []
    entries += collect_lumps(src)
    entries += collect_tree(src, "zscript")
    entries += collect_maps(src, tools_dir)
    for folder in ASSET_DIRS:
        entries += collect_tree(src, folder)
    if assets is not None:
        entries += collect_assets(assets)
    seen: set[str] = set()
    for e in entries:
        key = e.path.lower()
        if key in seen:
            raise BuildError(f"duplicate PK3 path {e.path}")
        seen.add(key)
    return sorted(entries, key=lambda e: e.path.lower())


def write_pk3(entries: list[Entry], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for e in entries:
            info = zipfile.ZipInfo(e.path, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, e.data)
    tmp.replace(out)


def build(src: Path, out: Path, tools_dir: Path, assets: Path | None = None) -> list[Entry]:
    if not src.is_dir():
        raise BuildError(f"source dir not found: {src}")
    entries = collect_entries(src, tools_dir, assets)
    if not entries:
        raise BuildError(f"nothing to pack under {src}")
    write_pk3(entries, out)
    return entries
