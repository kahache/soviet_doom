"""Shared readers for the P4 integration tests (D116): test_ep2_enemies.py,
test_ep3_boss.py and test_akm.py read the classes the three draft overlays
carried, now in `src/`, with these. Not a test module (no `test` prefix).

Stdlib only.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SPRITES = PROJECT_ROOT / "assets" / "sprites"
LANGS = ("enu default", "ru", "ca")
# The mark on every line of code that exists only because the art is not
# drawn yet (MOD-SPEC 6.12): deleted by the documented swap.
PROVISIONAL_MARK = "PROVISIONAL-D116"
# `sed -i -e 's/^\(\s*\)OLD /\1NEW /' ...` as each class's header writes it.
SWAP_PAIR_RE = re.compile(r"s/\^\\\(\\s\*\\\)([A-Z0-9]{4}) /\\1([A-Z0-9]{4}) /")
FINAL_LUMP_RE = re.compile(r"->\s*(SD[A-Z0-9]{5,6})\b")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def class_blocks(text: str) -> dict[str, tuple[str | None, str]]:
    """class name -> (parent, body text up to the next class), comments stripped."""
    text = strip_comments(text)
    heads = list(re.finditer(r"^\s*class\s+(\w+)\s*(?::\s*(\w+))?", text, flags=re.M))
    out = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[h.group(1)] = (h.group(2), text[h.start():end])
    return out


def class_head(text: str, cls: str) -> str:
    m = re.search(rf"^\s*class\s+{cls}\b[^\n{{]*", strip_comments(text), flags=re.M)
    return m.group(0).strip() if m else ""


def mod_class_files() -> dict[str, Path]:
    out = {}
    for p in (SRC / "zscript").rglob("*.zs"):
        for c in class_blocks(p.read_text(encoding="utf-8")):
            out[c] = p
    return out


def states_block(body: str) -> str:
    m = re.search(r"\bStates\s*\{(.*?)\n\t\}", body, flags=re.S)
    return m.group(1) if m else ""


def state_labels(body: str) -> set[str]:
    return set(re.findall(r"^\s*(\w+):", states_block(body), flags=re.M))


def state_frames(body: str) -> set[tuple[str, str]]:
    """(sprite, frame) for every state line of a class's States block."""
    frames: set[tuple[str, str]] = set()
    for line in states_block(body).splitlines():
        m = re.match(r"^\s*([A-Z0-9_]{4})\s+([A-Z\[\]]+)\s+-?\d+\b", line)
        if m and m.group(1) != "TNT1":
            frames.update((m.group(1), f) for f in m.group(2))
    return frames


def sprite_rotations(sprite: str) -> dict[str, set[str]]:
    """frame -> rotations available under assets/sprites/ (mirrored pairs counted)."""
    rot: dict[str, set[str]] = {}
    for p in SPRITES.rglob(f"{sprite}*.png"):
        stem = p.stem
        for i in (4, 6):
            if len(stem) >= i + 2:
                rot.setdefault(stem[i], set()).add(stem[i + 1])
    return rot


def frames_with_inheritance(cls: str, blocks: dict[str, tuple[str | None, str]]) -> set[tuple[str, str]]:
    """The frames a class can show: its own, plus its parents' while it has no Spawn."""
    parent, body = blocks[cls]
    frames, labels = state_frames(body), state_labels(body)
    while "Spawn" not in labels and parent in blocks:
        pparent, pbody = blocks[parent]
        frames |= state_frames(pbody)
        labels |= state_labels(pbody)
        parent = pparent
    return frames


def const_value(body: str, name: str) -> float:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([0-9.]+)\s*;", body)
    if not m:
        raise AssertionError(f"no const {name}")
    return float(m.group(1))


def default_value(body: str, prop: str) -> str | None:
    m = re.search(rf"^\s*{re.escape(prop)}\s+([^;]+);", body, flags=re.M)
    return m.group(1).strip().strip('"') if m else None


def mapinfo_ednums() -> dict[int, str]:
    text = strip_comments(read("lumps/MAPINFO"))
    block = re.search(r"^DoomEdNums\s*\{(.*?)^\}", text, re.S | re.M).group(1)
    out: dict[int, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if line:
            num, _, cls = line.partition("=")
            out[int(num)] = cls.strip()
    return out


def language_sections() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    current = None
    for line in strip_comments(read("lumps/LANGUAGE")).splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            current = head.group(1).strip()
            out.setdefault(current, {})
            continue
        m = re.match(r'^\s*(\w+)\s*=\s*"(.*)"\s*;', line)
        if m and current is not None:
            out[current][m.group(1)] = m.group(2)
    return out


def sndinfo_lines() -> dict[str, tuple[str, str]]:
    """logical -> (lump, comment) for the plain `logical lump` lines."""
    out = {}
    for raw in read("lumps/SNDINFO").splitlines():
        code, _, comment = raw.partition("//")
        parts = code.split()
        if len(parts) == 2 and not parts[0].startswith("$"):
            out[parts[0].lower()] = (parts[1].upper(), comment.strip())
    return out


def sndinfo_directives() -> list[list[str]]:
    """Every `$...` directive line, split (comments stripped)."""
    return [raw.split("//")[0].split() for raw in read("lumps/SNDINFO").splitlines()
            if raw.split("//")[0].strip().startswith("$")]


def includes() -> list[str]:
    return [i.lower() for i in re.findall(r'^\s*#include\s+"([^"]+)"', read("lumps/zscript.txt"), flags=re.M)]


def apply_documented_swap(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Run the swap a class's header documents (MOD-SPEC 6.12), in Python:
    rename the sprite at the start of each state line and delete every code
    line that carries the provisional mark. Returns (new text, pairs)."""
    sed = next((l for l in text.splitlines() if l.startswith("//   sed -i")), "")
    pairs = SWAP_PAIR_RE.findall(sed)
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if PROVISIONAL_MARK in line and stripped and not stripped.startswith("/"):
            continue
        for old, new in pairs:
            line = re.sub(rf"^(\s*){old} ", rf"\g<1>{new} ", line)
        out.append(line)
    return "\n".join(out) + "\n", pairs


def provisional_code_lines(text: str) -> list[str]:
    return [l.strip() for l in text.splitlines()
            if PROVISIONAL_MARK in l and l.strip() and not l.strip().startswith("/")]
