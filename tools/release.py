#!/usr/bin/env python3
"""Assemble the player's distribution zip of Soviet Doom (gate G6).

Usage:
  python3 tools/release.py --version 1.0
  python3 tools/release.py --version 1.0-rc1 --allow-dirty   # tests only

It publishes nothing: no tag, no upload, no GitHub release. What it makes is
dist/release/sovietdoom-<version>.zip (dist/ is gitignored), plus
sovietdoom-<version>.zip.sha256 beside it, and the zip holds one folder
sovietdoom-<version>/ with exactly:

  sovietdoom.pk3   the mod, built by tools/build.py from the checked-out tree
  LICENSE.md       the repo's licence file, verbatim
  CREDITS.txt      generated: the in-game credits (LANGUAGE SD_CRED_*, English
                   and Russian, in screen order), the credit lines
                   docs/sound/MUSIC-RIGHTS.md 4.5 says to reproduce verbatim,
                   and the provenance of every packed asset as
                   docs/art/LICENSES.md records it
  README.txt       a short player readme, English and Russian
  SHA256SUMS       `sha256sum -c` format, for the four files above

It refuses (exit 1, nothing written) when:
  * the git tree has uncommitted changes, unless --allow-dirty (tests only:
    a release is made from a commit, so the zip can be traced to it);
  * the PK3 packs an asset with no row in docs/art/LICENSES.md (and, for
    music, none in MUSIC-RIGHTS 4.5, the "what ships" table);
  * a packed asset's licence requires attribution and the credits do not
    carry the name, in English and in Russian;
  * anything from work/, tools/, tests/, logs/, iwads/, a preview, or any
    IWAD would enter the zip or the PK3;
  * tools/check_pk3.py rejects the PK3.

Deterministic: same commit, same bytes. Entries are sorted, every timestamp
is the commit's own time (UTC), permissions and the "made on" system are
fixed, and the PK3 build is already reproducible (sdbuild/pk3.py).

The checklist this tool serves, and what is still missing for G6:
docs/engine/RELEASE.md.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build as build_tool  # noqa: E402  (tools/build.py: the one way to build)
import check_pk3  # noqa: E402

MOD_NAME = build_tool.MOD_NAME
PK3_NAME = f"{MOD_NAME}.pk3"
DEFAULT_OUT_DIR = PROJECT_ROOT / "dist" / "release"
DEFAULT_LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
DEFAULT_MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
DEFAULT_LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
DEFAULT_LICENCE_FILE = PROJECT_ROOT / "LICENSE.md"

EXIT_OK = 0
EXIT_REFUSED = 1

# A release version: 1.0, 1.0.1, 1.0-rc1. No leading "v": the tag is v<version>
# and the file name already says what it is.
VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?(?:-[0-9A-Za-z][0-9A-Za-z.]*)?$")

# The files of the zip, in the order SHA256SUMS lists them (sorted by name).
LICENCE_NAME = "LICENSE.md"
CREDITS_NAME = "CREDITS.txt"
README_NAME = "README.txt"
SUMS_NAME = "SHA256SUMS"
RELEASE_FILES = (CREDITS_NAME, LICENCE_NAME, README_NAME, SUMS_NAME, PK3_NAME)

# Zip determinism. The zip format cannot store a date before 1980.
MIN_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ZIP_CREATE_SYSTEM_UNIX = 3              # ZipInfo defaults to 0 on Windows, 3 elsewhere
ZIP_FILE_MODE = 0o100644                # regular file, rw-r--r--
ZIP_COMPRESSLEVEL = 9

# What never ships (CLAUDE.md, build.py): any path component with one of
# these names, any preview, any IWAD. Compared case-insensitively.
FORBIDDEN_DIRS = frozenset({"work", "tools", "tests", "logs", "iwads", "previews", ".git", ".venv"})
FORBIDDEN_NAME_PARTS = ("preview",)
WAD_SUFFIX = ".wad"
IWAD_MAGIC = b"IWAD"
PWAD_MAGIC = b"PWAD"
MAPS_DIR = "maps/"

# Folders whose files are "assets" and need a licence row: the same list
# tools/check_pk3.py audits. Everything else in the PK3 (lumps, ZScript, maps
# generated from src/maps/*/map.py) is the project's own source under
# LICENSE.md.
ASSET_DIRS = check_pk3.LICENSED_DIRS

# --- Reading the licence registers ------------------------------------------
# The same reading as tests/test_credits.py (which guards the in-game screen),
# made strict for shipping: only the FIRST cell of a register table row names
# what the row covers, and CC0 is a courtesy, not an obligation.

CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
TABLE_RULE_RE = re.compile(r"^\s*\|[\s|:-]+\|\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BACKTICKED_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
LICENCE_HEADER_RE = re.compile(r"licen[cs]e", re.I)
QUOTED_CREDIT_RE = re.compile(r'credit\s+"([^"]+)"', re.I)
# A licence cell that obliges a credit. "credited as a courtesy" does not
# match `credit\b`; that is deliberate.
REQUIRES_CREDIT_RE = re.compile(
    r"credit\b|\{\{Attribution|\bCC[ -]?BY\b|\bBSD\b|\bMIT\b|\bOFL\b", re.I)
COURTESY_RE = re.compile(r"\bCC0\b|courtesy", re.I)
OWN_WORK_RE = re.compile(r"\(D15\)|Soviet Doom project")
# Our own rows (D15, CC BY-NC-SA 4.0) are attributed by the team line and
# the licence line, which both languages' credits must carry.
OWN_WORK_CREDITS = ("Soviet Doom", "CC BY-NC-SA 4.0")
NOT_A_NAME_RE = re.compile(r"\b(credit|required|accepted|licen[cs]e|none)\b", re.I)
IDEM = "idem"

MUSIC_DIR = "music/"
MUSIC_SHIPS_HEADING_RE = re.compile(r"^4\.5\b")
OBLIGATION_HEADER_RE = re.compile(r"^obligation", re.I)
OBLIGATION_CREDIT_RE = re.compile(r"^credit\s+(.+?)\s*$", re.I)
VERBATIM_INTRO_RE = re.compile(r"credit line|courtesy line", re.I)

# --- Reading the in-game credits ---------------------------------------------

CREDIT_PREFIX = "SD_CRED_"
CREDIT_TITLE_ID = "SD_CRED_TITLE"
CREDIT_HEADER_MARK = "SD_CRED_H_"
LANG_ENGLISH = "default"
LANG_RUSSIAN = "ru"
LANGUAGE_SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
LANGUAGE_ASSIGN_RE = re.compile(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*?)\s*;?\s*$")
LANGUAGE_STRING_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')

TEXT_WIDTH = 76
COMMIT_SHORT = 12                       # hex digits of the commit quoted in the texts


class ReleaseError(RuntimeError):
    """The release is refused; the message says why and what to do."""


# --- Small helpers -------------------------------------------------------------

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plain(markdown: str) -> str:
    """A register cell as plain text: emphasis, code marks and escapes off."""
    text = markdown.replace("\\|", "|").replace("**", "").replace("`", "")
    text = re.sub(r"(?<!\w)\*(\S(?:.*?\S)?)\*(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def wrap(text: str, indent: str = "  ", hang: str | None = None) -> list[str]:
    """Wrap at TEXT_WIDTH; continuation lines get `hang` (default: indent
    plus two spaces)."""
    hang = indent + "  " if hang is None else hang
    return textwrap.wrap(text, TEXT_WIDTH, initial_indent=indent, subsequent_indent=hang,
                         break_on_hyphens=False, break_long_words=False) or [indent.rstrip()]


# --- Markdown tables -------------------------------------------------------------

def _cells(line: str) -> list[str]:
    return [c.strip() for c in CELL_SPLIT_RE.split(line.strip().strip("|"))]


def iter_tables(text: str):
    """Yield (heading, header cells, [row cells, ...]) for every table."""
    lines = text.splitlines()
    heading = ""
    i = 0
    while i < len(lines):
        match = HEADING_RE.match(lines[i])
        if match:
            heading = match.group(2)
        if (i + 1 < len(lines) and lines[i].lstrip().startswith("|")
                and TABLE_RULE_RE.match(lines[i + 1])):
            header = _cells(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(_cells(lines[j]))
                j += 1
            yield heading, header, rows
            i = j
            continue
        i += 1


# --- The licence register (docs/art/LICENSES.md) ---------------------------------

@dataclass
class RegisterRow:
    """One row of a register table, as far as shipping is concerned."""

    source: str                 # register file name, for messages
    heading: str                # the section it sits in
    tokens: tuple[str, ...]     # what it covers: backticked names in its first cell
    licence: str                # the licence cell, `idem` resolved
    origin: str                 # origin / author, plain text
    required: tuple[str, ...]   # names the credits MUST carry
    courtesy: tuple[str, ...]   # names credited by choice (CC0)
    problem: str = ""           # a row that needs a credit but names nobody

    def covers(self, path: str) -> bool:
        stem = Path(path).stem.upper()
        name = Path(path).name.upper()
        for token in self.tokens:
            upper = token.upper()
            if "/" in upper:
                head, _, tail = upper.rpartition("/")
                prefix = (head if ("*" in tail or not tail) else upper).rstrip("/") + "/"
                if path.upper().startswith(prefix):
                    return True
            elif upper in (stem, name):
                return True
        return False


def _names_in_row(row: list[str], licence: str) -> list[str]:
    quoted = QUOTED_CREDIT_RE.findall(licence)
    if quoted:
        return quoted
    names: list[str] = []
    for cell in row:
        for span in BOLD_RE.findall(cell):
            span = span.strip()
            if not NOT_A_NAME_RE.search(span) and span not in names:
                names.append(span)
    return names


def _row_tokens(first_cell: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for token in BACKTICKED_RE.findall(first_cell):
        token = token.strip()
        if token and not token.startswith("{{"):
            tokens.append(token)
    return tuple(tokens)


def parse_licence_register(text: str, source: str = "docs/art/LICENSES.md") -> list[RegisterRow]:
    """Every row of every table that has a Licence column."""
    rows_out: list[RegisterRow] = []
    for heading, header, rows in iter_tables(text):
        col = next((k for k, h in enumerate(header) if LICENCE_HEADER_RE.search(h)), None)
        if col is None:
            continue
        origin_cols = [k for k, h in enumerate(header)
                       if k != col and re.match(r"(origin|author)", h, re.I)]
        previous: RegisterRow | None = None
        for row in rows:
            if col >= len(row) or not row:
                continue
            cell = row[col]
            origin = "; ".join(plain(row[k]) for k in origin_cols if k < len(row) and row[k])
            if cell.lower().startswith(IDEM) and previous is not None:
                licence = previous.licence
                required, courtesy = previous.required, previous.courtesy
                origin = _resolve_idem(origin, previous.origin)
                problem = previous.problem
            else:
                licence = plain(cell)
                required, courtesy, problem = _credits_for(row, cell)
                if previous is not None:
                    origin = _resolve_idem(origin, previous.origin)
            entry = RegisterRow(source, heading, _row_tokens(row[0]), licence, origin,
                                required, courtesy, problem)
            rows_out.append(entry)
            previous = entry
    return rows_out


def _resolve_idem(origin: str, previous: str) -> str:
    """`idem` in an origin cell means "the row above": a bare `(a) idem` is
    the row above's origin; `(a) idem, variant B` keeps its variant."""
    if re.fullmatch(r"(\(a\)\s*)?idem\.?", origin, re.I):
        return previous
    return re.sub(r"\bidem\b", "same source as above", origin, flags=re.I)


def _credits_for(row: list[str], cell: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    quoted = QUOTED_CREDIT_RE.findall(cell)
    if quoted:
        return tuple(quoted), (), ""
    if OWN_WORK_RE.search(cell):
        return OWN_WORK_CREDITS, (), ""
    if REQUIRES_CREDIT_RE.search(cell):
        names = _names_in_row(row, cell)
        if not names:
            return (), (), ("its licence requires attribution but the row names nobody "
                            '(write credit "Name" in the licence cell, or the name in bold)')
        return tuple(names), (), ""
    if COURTESY_RE.search(cell):
        return (), tuple(_names_in_row(row, cell)), ""
    return (), (), ""


# --- The music register (docs/sound/MUSIC-RIGHTS.md 4.5) ---------------------------

@dataclass
class MusicRow:
    tokens: tuple[str, ...]
    obligation: str
    required: tuple[str, ...]


def _section_body(text: str, heading_re: re.Pattern[str]) -> str:
    """The text under the first heading whose title matches, up to the next
    heading of the same or a higher level."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match and heading_re.search(match.group(2)):
            level = len(match.group(1))
            body = []
            for nxt in lines[i + 1:]:
                inner = HEADING_RE.match(nxt)
                if inner and len(inner.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def parse_music_register(text: str) -> list[MusicRow]:
    out: list[MusicRow] = []
    for _, header, rows in iter_tables(_section_body(text, MUSIC_SHIPS_HEADING_RE)):
        col = next((k for k, h in enumerate(header) if OBLIGATION_HEADER_RE.match(h)), None)
        if col is None:
            continue
        for row in rows:
            if col >= len(row):
                continue
            obligation = plain(row[col])
            match = OBLIGATION_CREDIT_RE.match(obligation)
            out.append(MusicRow(_row_tokens(row[0]), obligation,
                                (match.group(1),) if match else ()))
    return out


def verbatim_music_lines(text: str) -> list[str]:
    """The blockquotes MUSIC-RIGHTS 4.5 introduces as a line to reproduce
    ("The credit line", "The courtesy line"), as plain text, in order."""
    section = _section_body(text, MUSIC_SHIPS_HEADING_RE)
    lines = section.splitlines()
    out: list[str] = []
    armed = False
    quote: list[str] = []
    for line in lines + [""]:
        if line.startswith(">"):
            if armed:
                quote.append(line.lstrip(">").strip())
            continue
        if quote:
            out.append(plain(" ".join(quote)))
            quote = []
            armed = False
        if VERBATIM_INTRO_RE.search(line):
            armed = True
    return out


# --- The in-game credits (LANGUAGE SD_CRED_*) -------------------------------------

def _strip_comment(line: str) -> str:
    out = []
    in_string = False
    i = 0
    while i < len(line):
        char = line[i]
        if char == "\\" and in_string:
            out.append(line[i:i + 2])
            i += 2
            continue
        if char == '"':
            in_string = not in_string
        elif not in_string and line.startswith("//", i):
            break
        out.append(char)
        i += 1
    return "".join(out)


def parse_language_lines(language_text: str, prefix: str) -> dict[str, list[tuple[str, str]]]:
    """{language code: [(id, text), ...]} for the ids starting with `prefix`,
    in definition order. Adjacent strings are joined, as GZDoom joins them."""
    sections: dict[str, list[tuple[str, str]]] = {}
    current: list[str] = []
    for raw in language_text.splitlines():
        line = _strip_comment(raw).strip()
        if not line:
            continue
        header = LANGUAGE_SECTION_RE.match(line)
        if header:
            current = header.group(1).split()
            for code in current:
                sections.setdefault(code, [])
            continue
        assign = LANGUAGE_ASSIGN_RE.match(line)
        if assign and current and assign.group(1).startswith(prefix):
            value = "".join(LANGUAGE_STRING_RE.findall(assign.group(2)))
            value = value.replace('\\"', '"').replace("\\n", " ")
            for code in current:
                sections[code].append((assign.group(1), value))
    return sections


def parse_credit_lines(language_text: str) -> dict[str, list[tuple[str, str]]]:
    """SD_CRED_* per language, in definition order, which is the screen order
    (tests/test_credits.py keeps the menu and LANGUAGE in step)."""
    return parse_language_lines(language_text, CREDIT_PREFIX)


def language_strings(language_text: str) -> dict[str, dict[str, str]]:
    """{language code: {id: text}} for every SD_* id."""
    return {code: dict(lines) for code, lines in parse_language_lines(language_text, "SD_").items()}


def credits_text(lines: list[tuple[str, str]]) -> str:
    """What a player reads on the credits screen, as one string."""
    return normalise(" ".join(text for ident, text in lines if ident != CREDIT_TITLE_ID))


# --- The licence check -----------------------------------------------------------

@dataclass
class LicenceCheck:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # row -> the packed paths it covers, in register order (for CREDITS.txt)
    coverage: list[tuple[RegisterRow, list[str]]] = field(default_factory=list)
    music: dict[str, MusicRow] = field(default_factory=dict)


def asset_paths(pk3_names) -> list[str]:
    return sorted(n for n in pk3_names
                  if not n.endswith("/") and n.split("/", 1)[0] in ASSET_DIRS and "/" in n)


def check_licences(pk3_names, licence_rows: list[RegisterRow], music_rows: list[MusicRow],
                   credits: dict[str, list[tuple[str, str]]]) -> LicenceCheck:
    """Every packed asset has a register row; every name its licence obliges
    is in the credits of both languages."""
    result = LicenceCheck()
    english = credits_text(credits.get(LANG_ENGLISH, []))
    russian = credits_text(credits.get(LANG_RUSSIAN, []))
    if not english:
        result.errors.append(f"LANGUAGE: no {CREDIT_PREFIX}* lines in [enu default]; "
                             "the credits cannot be generated")
    if not russian:
        result.errors.append(f"LANGUAGE: no {CREDIT_PREFIX}* lines in [ru]; D7 needs both languages")

    covered: dict[int, list[str]] = {}
    for path in asset_paths(pk3_names):
        rows = [k for k, row in enumerate(licence_rows) if row.covers(path)]
        if not rows:
            result.errors.append(
                f"{path}: no licence row in docs/art/LICENSES.md (a table row whose first "
                "cell names it); a packed asset without recorded provenance cannot ship")
            continue
        for k in rows:
            covered.setdefault(k, []).append(path)
        if path.startswith(MUSIC_DIR):
            music = [m for m in music_rows if Path(path).stem.upper() in (t.upper() for t in m.tokens)]
            if not music:
                result.errors.append(
                    f"{path}: no row in docs/sound/MUSIC-RIGHTS.md 4.5 (\"what ships\"); "
                    "music needs its rights cleared there before it ships")
            else:
                result.music[path] = music[0]

    needed: dict[str, list[str]] = {}
    courtesy: dict[str, list[str]] = {}
    for k in sorted(covered):
        row, paths = licence_rows[k], covered[k]
        result.coverage.append((row, paths))
        if row.problem:
            result.errors.append(f"{paths[0]}: {row.source} row {', '.join(row.tokens)}: {row.problem}")
        for name in row.required:
            needed.setdefault(name, []).extend(paths)
        for name in row.courtesy:
            courtesy.setdefault(name, []).extend(paths)
    for path, music in result.music.items():
        for name in music.required:
            needed.setdefault(name, []).append(path)

    for name, paths in needed.items():
        for lang, text in ((LANG_ENGLISH, english), (LANG_RUSSIAN, russian)):
            if text and name not in text:
                result.errors.append(
                    f"{paths[0]}: its licence requires the credit {name!r}, which the [{lang}] "
                    f"credits (LANGUAGE {CREDIT_PREFIX}*, hence CREDITS.txt) do not carry")
    for name, paths in courtesy.items():
        if name not in english:
            result.warnings.append(f"{paths[0]}: courtesy credit {name!r} is not in the credits")
    return result


# --- Content guard ------------------------------------------------------------------

def forbidden_reason(path: str) -> str | None:
    """Why a path may not ship, or None."""
    parts = [p.lower() for p in path.replace("\\", "/").split("/") if p]
    for part in parts[:-1]:
        if part in FORBIDDEN_DIRS:
            return f"comes from {part}/, which never ships"
    if any(mark in path.lower() for mark in FORBIDDEN_NAME_PARTS):
        return "is a preview, which never ships"
    return None


def guard_pk3(pk3_bytes: bytes) -> list[str]:
    """Problems with what the PK3 holds: work/, tools/, previews, IWADs."""
    errors: list[str] = []
    with zipfile.ZipFile(io.BytesIO(pk3_bytes)) as zf:
        for info in zf.infolist():
            name = info.filename
            if name.endswith("/"):
                continue
            why = forbidden_reason(name)
            if why:
                errors.append(f"{PK3_NAME}:{name} {why}")
            data = zf.read(info)
            if data[:4] == IWAD_MAGIC:
                errors.append(f"{PK3_NAME}:{name} is an IWAD; the game data is never redistributed (D2)")
            elif name.lower().endswith(WAD_SUFFIX):
                if not name.lower().startswith(MAPS_DIR):
                    errors.append(f"{PK3_NAME}:{name} is a WAD outside maps/")
                elif data[:4] != PWAD_MAGIC:
                    errors.append(f"{PK3_NAME}:{name} is not a PWAD")
    return errors


def guard_members(names) -> list[str]:
    """Problems with the zip's own member list: exactly RELEASE_FILES, under
    one folder, and nothing forbidden."""
    errors: list[str] = []
    names = list(names)
    for name in names:
        why = forbidden_reason(name)
        if why:
            errors.append(f"{name} {why}")
        if name.lower().endswith(WAD_SUFFIX):
            errors.append(f"{name} is a WAD; the IWAD is never shipped (D2)")
    roots = {n.split("/", 1)[0] for n in names}
    leaves = sorted(n.split("/", 1)[1] if "/" in n else n for n in names)
    if len(roots) != 1:
        errors.append(f"the zip must hold one folder, not {sorted(roots)}")
    if leaves != sorted(RELEASE_FILES):
        errors.append(f"the zip must hold exactly {sorted(RELEASE_FILES)}, not {leaves}")
    return errors


# --- Git -------------------------------------------------------------------------

@dataclass(frozen=True)
class TreeState:
    commit: str            # full hash, or "unknown"
    commit_time: int | None
    dirty: tuple[str, ...]  # porcelain lines; empty = clean


def _git(args: list[str], root: Path) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return done.stdout


def git_state(root: Path = PROJECT_ROOT) -> TreeState:
    try:
        commit = _git(["rev-parse", "HEAD"], root).strip()
        stamp = int(_git(["log", "-1", "--format=%ct", "HEAD"], root).strip())
        porcelain = _git(["status", "--porcelain", "--untracked-files=all"], root)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return TreeState("unknown", None, ("not a git checkout (or git is missing)",))
    dirty = tuple(line for line in porcelain.splitlines() if line.strip())
    return TreeState(commit, stamp, dirty)


def zip_time(commit_time: int | None) -> tuple[int, int, int, int, int, int]:
    if commit_time is None:
        return MIN_ZIP_TIME
    stamp = tuple(time.gmtime(commit_time)[:6])
    return max(stamp, MIN_ZIP_TIME)  # type: ignore[return-value]


# --- The generated texts -------------------------------------------------------------

def render_credits(version: str, commit: str, credits: dict[str, list[tuple[str, str]]],
                   music_lines: list[str], check: LicenceCheck) -> str:
    title = f"Soviet Doom {version} - credits"
    out = [title, "=" * len(title), ""]
    out += wrap("Generated by tools/release.py from the project's licence registers "
                "(docs/art/LICENSES.md, docs/sound/MUSIC-RIGHTS.md) and the in-game "
                f"credits (LANGUAGE), commit {commit}.", "", "")
    out.append("")

    def screen(lines: list[tuple[str, str]], heading: str) -> None:
        out.extend([heading, "-" * len(heading)])
        for ident, text in lines:
            if ident == CREDIT_TITLE_ID:
                continue
            if ident.startswith(CREDIT_HEADER_MARK):
                out.extend(["", text.upper()])
            else:
                out.append("  " + text)
        out.append("")

    screen(credits.get(LANG_ENGLISH, []),
           "English - as shown in the game (Options > Soviet Doom > Credits)")

    if music_lines:
        heading = "Music credit lines (verbatim, docs/sound/MUSIC-RIGHTS.md 4.5)"
        out.extend(["", heading, "-" * len(heading)])
        for line in music_lines:
            out.extend(wrap(line))
            out.append("")

    heading = "Every packed asset, its origin and its licence (docs/art/LICENSES.md)"
    out.extend(["", heading, "-" * len(heading), ""])
    for row, paths in check.coverage:
        out.extend(wrap(_describe_paths(row, paths), "* ", "  "))
        if row.origin:
            out.extend(wrap("Origin: " + row.origin, "    "))
        out.extend(wrap("Licence: " + row.licence, "    "))
        music = [check.music[p] for p in paths if p in check.music]
        for entry in music:
            out.extend(wrap("Obligation (MUSIC-RIGHTS 4.5): " + entry.obligation, "    "))
        out.append("")
    out.extend(wrap("Everything else in the PK3 (maps, ZScript, definition lumps) is the "
                    "project's own work: code under GNU GPL 3.0 or later, the rest under "
                    "CC BY-NC-SA 4.0 (LICENSE.md).", "", ""))
    out.append("")

    out.append("")
    screen(credits.get(LANG_RUSSIAN, []),
           "Русский - как в игре (Настройки (Options) > Советский Doom > Авторы)")
    return "\n".join(out).rstrip() + "\n"


def _describe_paths(row: RegisterRow, paths: list[str]) -> str:
    """`textures/SDCONC1.png, ...`, or `fonts/bigfont/ (113 files)` for a
    folder row."""
    folders: dict[str, int] = {}
    files: list[str] = []
    for path in paths:
        folder_tokens = [t for t in row.tokens if "/" in t]
        if folder_tokens and not any(Path(path).stem.upper() == t.upper() for t in row.tokens):
            folder = path.rsplit("/", 1)[0] + "/"
            folders[folder] = folders.get(folder, 0) + 1
        else:
            files.append(path)
    parts = files + [f"{folder} ({count} files)" for folder, count in sorted(folders.items())]
    return ", ".join(parts)


README_TEMPLATE = """\
SOVIET DOOM {version}
{rule}

A total conversion for GZDoom. The USSR of the 1970s is invaded by two allied
alien factions, Yankee and Nazi, united to defend capital. You are a Spetsnaz
sergeant who came to this country as a refugee child from Barcelona.
A fan project, not affiliated with id Software.

This release: the campaign map {map01}, and a practice range
({newgame} > {ep02}). Built from commit {commit}.

WHAT YOU NEED
  1. GZDoom {gzdoom} or newer (free): https://zdoom.org/downloads
  2. Freedoom: Phase 2, the file freedoom2.wad (free; tested with
     Freedoom {freedoom}): https://freedoom.github.io/download.html
     The game data (the IWAD) is NOT in this package; download it yourself.
  3. {pk3}, from this package.

HOW TO PLAY
  Put freedoom2.wad in the GZDoom folder, then drag {pk3} onto
  gzdoom.exe. Or, from a command line in that folder:

    gzdoom -iwad freedoom2.wad -file {pk3}

BASIC CONTROLS (GZDoom's defaults; change them in Options > Customize Controls)
  Move ............ W A S D, or the arrow keys
  Turn and aim .... mouse
  Fire ............ left mouse button, or Ctrl
  Use ............. E or Space: open doors, press switches
  Weapons ......... 1 to 7
  Automap ......... Tab
  Menu ............ Esc
  Language ........ Options > Soviet Doom > Language (English or Russian)

LICENCE AND CREDITS
  Code: GNU GPL 3.0 or later. Art, sound, maps and text: CC BY-NC-SA 4.0.
  See LICENSE.md. Everyone credited, and every asset's origin: CREDITS.txt.
  Check the download: SHA256SUMS (sha256sum -c SHA256SUMS).

----------------------------------------------------------------------------

СОВЕТСКИЙ DOOM {version}
{rule_ru}

Тотальная конверсия для GZDoom. СССР 1970-х годов подвергается вторжению двух
союзных инопланетных фракций, янки и нацистов, объединившихся ради защиты
капитала. Вы - сержант спецназа, попавший в эту страну ребёнком-беженцем из
Барселоны. Фанатский проект, не связанный с компанией id Software.

В этом выпуске: карта кампании - {map01_ru} - и учебный полигон
({newgame_ru} > {ep02_ru}). Собрано из коммита {commit}.

ЧТО НУЖНО
  1. GZDoom {gzdoom} или новее (бесплатно): https://zdoom.org/downloads
  2. Freedoom: Phase 2, файл freedoom2.wad (бесплатно; проверено с
     Freedoom {freedoom}): https://freedoom.github.io/download.html
     Игровых данных (IWAD) в этом архиве НЕТ - скачайте их сами.
  3. {pk3} из этого архива.

КАК ИГРАТЬ
  Положите freedoom2.wad в папку GZDoom и перетащите {pk3} на
  gzdoom.exe. Или из командной строки в этой папке:

    gzdoom -iwad freedoom2.wad -file {pk3}

ОСНОВНОЕ УПРАВЛЕНИЕ (по умолчанию в GZDoom; меняется в настройках управления)
  Движение ........ W A S D или стрелки
  Поворот, прицел . мышь
  Огонь ........... левая кнопка мыши или Ctrl
  Действие ........ E или пробел: открыть дверь, нажать рубильник
  Оружие .......... 1-7
  Карта ........... Tab
  Меню ............ Esc
  Язык ............ Настройки (Options) > Советский Doom > Язык

ЛИЦЕНЗИЯ И АВТОРЫ
  Код: GNU GPL 3.0 или новее. Графика, звук, карты и тексты: CC BY-NC-SA 4.0.
  См. LICENSE.md. Все авторы и происхождение каждого ресурса: CREDITS.txt.
  Проверка загрузки: SHA256SUMS (sha256sum -c SHA256SUMS).
"""

# D3 and D2 (docs/PRD.md): the versions the mod is built and tested against.
GZDOOM_MINIMUM = "4.14.2"
FREEDOOM_TESTED = "0.13.0"


# The LANGUAGE ids the readme quotes, so it names things as the game does.
README_IDS = {"map01": "SD_MAP01_NAME", "ep02": "SD_EP02_NAME", "newgame": "SD_MNU_NEWGAME"}


def render_readme(version: str, commit: str, strings: dict[str, dict[str, str]]) -> str:
    title_en = f"SOVIET DOOM {version}"
    title_ru = f"СОВЕТСКИЙ DOOM {version}"
    names: dict[str, str] = {}
    for key, ident in README_IDS.items():
        for lang, suffix in ((LANG_ENGLISH, ""), (LANG_RUSSIAN, "_ru")):
            value = strings.get(lang, {}).get(ident)
            if not value:
                raise ReleaseError(f"LANGUAGE [{lang}] lacks {ident}, which README.txt quotes")
            # Menu labels are drawn in capitals; the readme writes them as a
            # title, in each language's own convention ("New Game", "Новая игра").
            if value.isupper():
                value = value.title() if lang == LANG_ENGLISH else value.capitalize()
            names[key + suffix] = value
    return README_TEMPLATE.format(
        version=version, commit=commit, pk3=PK3_NAME,
        gzdoom=GZDOOM_MINIMUM, freedoom=FREEDOOM_TESTED,
        rule="=" * len(title_en), rule_ru="=" * len(title_ru), **names)


def render_sums(files: dict[str, bytes]) -> str:
    return "".join(f"{sha256(files[name])}  {name}\n"
                   for name in sorted(files) if name != SUMS_NAME)


# --- The pipeline -----------------------------------------------------------------------

@dataclass
class Config:
    version: str
    out_dir: Path = DEFAULT_OUT_DIR
    allow_dirty: bool = False
    repo_root: Path = PROJECT_ROOT
    src: Path = build_tool.DEFAULT_SRC
    assets: Path = build_tool.DEFAULT_ASSETS
    licenses: Path = DEFAULT_LICENSES
    music_rights: Path = DEFAULT_MUSIC_RIGHTS
    language: Path | None = None        # None: the LANGUAGE lump inside the built PK3
    licence_file: Path = DEFAULT_LICENCE_FILE
    spec: Path = check_pk3.DEFAULT_SPEC
    palette: Path = check_pk3.DEFAULT_PALETTE


@dataclass
class Release:
    zip_path: Path
    sha_path: Path
    members: list[str]
    warnings: list[str]


def build_pk3(config: Config, workdir: Path) -> Path:
    """tools/build.py, as the CLI runs it."""
    out = workdir / PK3_NAME
    code = build_tool.main(["--src", str(config.src), "--assets", str(config.assets),
                            "--out", str(out), "--quiet"])
    if code != 0 or not out.is_file():
        raise ReleaseError("tools/build.py failed; fix the build first")
    return out


def _read(path: Path, what: str) -> str:
    if not path.is_file():
        raise ReleaseError(f"{what} not found: {path}")
    return path.read_text(encoding="utf-8")


def make_release(config: Config) -> Release:
    if not VERSION_RE.match(config.version or ""):
        raise ReleaseError(f"--version {config.version!r} is not a release version "
                           "(1.0, 1.0.1, 1.0-rc1; no leading v)")
    state = git_state(config.repo_root)
    if state.dirty and not config.allow_dirty:
        listing = "\n".join("  " + line for line in state.dirty[:20])
        more = f"\n  ... and {len(state.dirty) - 20} more" if len(state.dirty) > 20 else ""
        raise ReleaseError("the git tree has uncommitted changes; a release is made from a "
                           f"commit (--allow-dirty is for tests only):\n{listing}{more}")
    # Short hash, and "+dirty" when the tree is not the commit (tests only).
    commit = state.commit[:COMMIT_SHORT] + ("+dirty" if state.dirty else "")

    with tempfile.TemporaryDirectory(prefix="sd-release-") as tmp:
        pk3_path = build_pk3(config, Path(tmp))
        pk3_bytes = pk3_path.read_bytes()

        errors = guard_pk3(pk3_bytes)
        with zipfile.ZipFile(io.BytesIO(pk3_bytes)) as zf:
            pk3_names = zf.namelist()
            language_text = (_read(config.language, "LANGUAGE") if config.language
                             else zf.read("LANGUAGE").decode("utf-8"))
        credits = parse_credit_lines(language_text)
        music_text = _read(config.music_rights, "MUSIC-RIGHTS.md")
        check = check_licences(pk3_names,
                               parse_licence_register(_read(config.licenses, "LICENSES.md")),
                               parse_music_register(music_text), credits)
        errors += check.errors
        if errors:
            raise ReleaseError("refused:\n" + "\n".join("  " + e for e in errors))

        report = check_pk3.check_pk3(pk3_path, config.spec, config.licenses, config.palette)
        if not report.ok():
            raise ReleaseError("tools/check_pk3.py rejects the PK3:\n"
                               + "\n".join(f.render() for f in report.errors))

    files: dict[str, bytes] = {
        PK3_NAME: pk3_bytes,
        LICENCE_NAME: _read(config.licence_file, "LICENSE.md").encode("utf-8"),
        CREDITS_NAME: render_credits(config.version, commit, credits,
                                     verbatim_music_lines(music_text), check).encode("utf-8"),
        README_NAME: render_readme(config.version, commit,
                                   language_strings(language_text)).encode("utf-8"),
    }
    files[SUMS_NAME] = render_sums(files).encode("ascii")

    folder = f"{MOD_NAME}-{config.version}"
    members = [f"{folder}/{name}" for name in sorted(files)]
    errors = guard_members(members)
    if errors:
        raise ReleaseError("refused:\n" + "\n".join("  " + e for e in errors))

    stamp = zip_time(state.commit_time)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for member in members:
            info = zipfile.ZipInfo(member, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = ZIP_CREATE_SYSTEM_UNIX
            info.external_attr = ZIP_FILE_MODE << 16
            zf.writestr(info, files[member.split("/", 1)[1]], compresslevel=ZIP_COMPRESSLEVEL)
    data = buffer.getvalue()

    config.out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = config.out_dir / f"{folder}.zip"
    sha_path = config.out_dir / f"{folder}.zip.sha256"
    _write_atomic(zip_path, data)
    _write_atomic(sha_path, f"{sha256(data)}  {zip_path.name}\n".encode("ascii"))
    return Release(zip_path, sha_path, members, check.warnings)


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/release.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.0")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR,
                        help="where the zip goes (default: dist/release/)")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="build from a tree with uncommitted changes (TESTS ONLY)")
    args = parser.parse_args(argv)
    try:
        release = make_release(Config(args.version, args.out_dir, args.allow_dirty))
    except ReleaseError as exc:
        print(f"release: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    for warning in release.warnings:
        print(f"release: warning: {warning}", file=sys.stderr)
    print(release.zip_path)
    for member in release.members:
        print(f"  {member}")
    print(release.sha_path.read_text(encoding="ascii").strip())
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
