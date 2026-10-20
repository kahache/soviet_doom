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
  LICENSE-GPL-3.0.txt, LICENSE-CC-BY-NC-SA-4.0.txt
                   the full licence texts LICENSE.md points to (D15), byte for
                   byte as their publishers serve them: each one's SHA-256 is
                   pinned below (LICENCE_TEXTS)
  LICENSE-FREEDOOM-BSD-3.txt
                   Freedoom's BSD-3 notice (D75), verbatim: the licence of the
                   Freedoom pixels our weapon frames carry (the TT-33 hands),
                   whose clause 2 asks the notice to travel with the package
  CREDITS.txt      generated: the in-game credits (LANGUAGE SD_CRED_*, English
                   and Russian, in screen order), the credit lines
                   docs/sound/MUSIC-RIGHTS.md 4.5 says to reproduce verbatim,
                   the provenance of every packed asset as
                   docs/art/LICENSES.md records it, and every AI tool the
                   game was made with and what each did (D75, D79, D93); its
                   headings name no repo path
  README.txt       generated: the player readme, English and Russian (the
                   campaign's three maps and the range, what to download,
                   how to start it, GZDoom's default keys, what it was made
                   with, the hash check);
                   every map and menu name is read from LANGUAGE
  SHA256SUMS       `sha256sum -c` format, for the seven files above

It refuses (exit 1, nothing written) when:
  * the git tree has uncommitted changes, unless --allow-dirty (tests only:
    a release is made from a commit, so the zip can be traced to it);
  * a full licence text is missing or is not the published text (its
    SHA-256 differs from the pinned one);
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
import licences  # noqa: E402  (tools/licences.py: the one reading of the registers)
# Re-exported: the tests and the pipeline below have always found them here.
from licences import (  # noqa: E402,F401
    MusicRow,
    RegisterRow,
    localized_base,
    normalise,
    parse_licence_register,
    parse_music_register,
    plain,
    verbatim_music_lines,
)

MOD_NAME = build_tool.MOD_NAME
PK3_NAME = f"{MOD_NAME}.pk3"
DEFAULT_OUT_DIR = PROJECT_ROOT / "dist" / "release"
DEFAULT_LICENSES = licences.LICENSES_PATH
DEFAULT_MUSIC_RIGHTS = licences.MUSIC_RIGHTS_PATH
DEFAULT_LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
DEFAULT_LICENCE_FILE = PROJECT_ROOT / "LICENSE.md"
DEFAULT_LICENCE_TEXTS_DIR = PROJECT_ROOT   # where LICENSE-*.txt live in the repo

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
GPL_TEXT_NAME = "LICENSE-GPL-3.0.txt"
CC_TEXT_NAME = "LICENSE-CC-BY-NC-SA-4.0.txt"
FREEDOOM_TEXT_NAME = "LICENSE-FREEDOOM-BSD-3.txt"
RELEASE_FILES = (CREDITS_NAME, CC_TEXT_NAME, FREEDOOM_TEXT_NAME, GPL_TEXT_NAME, LICENCE_NAME,
                 README_NAME, SUMS_NAME, PK3_NAME)


@dataclass(frozen=True)
class LicenceText:
    """A full licence text shipped verbatim: where it was downloaded from and
    the SHA-256 of the bytes served there (backlog N10, downloaded by the PM
    with the CEO's permission on 2026-10-14; Freedoom's notice on 2026-10-15,
    D75). The pin is what makes "verbatim" checkable: an edited, re-wrapped or
    truncated text stops the release."""
    name: str
    covers: str
    url: str
    sha256: str


CRLF = b"\r\n"
LF = b"\n"

# The two licences of D15, as LICENSE.md assigns them, and Freedoom's BSD-3
# notice (D75): Freedoom v0.13.0's COPYING.adoc, the tag the IWAD we test with
# was built from (D2), for the Freedoom-derived pixels the PK3 packs.
LICENCE_TEXTS = (
    LicenceText(GPL_TEXT_NAME, "code", "https://www.gnu.org/licenses/gpl-3.0.txt",
                "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986"),
    LicenceText(CC_TEXT_NAME, "assets and documentation",
                "https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt",
                "e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd"),
    LicenceText(FREEDOOM_TEXT_NAME, "Freedoom-derived art",
                "https://raw.githubusercontent.com/freedoom/freedoom/v0.13.0/COPYING.adoc",
                "ed60abcf1ff64bf61bf8b4c585ab63643d655a21f8997ba284c01f94ed681fc5"),
)

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
# tools/check_pk3.py audits, plus the language variants (MOD-SPEC 2,
# "Language variants"; T24). Everything else in the PK3 (lumps, ZScript, maps
# generated from src/maps/*/map.py) is the project's own source under
# LICENSE.md.
LOCALIZED_DIR = licences.LOCALIZED_DIR
ASSET_DIRS = tuple(check_pk3.LICENSED_DIRS) + (LOCALIZED_DIR,)

# The licence registers are read by tools/licences.py, the same reading
# tests/test_credits.py uses for the in-game screen; this tool is the strict
# side of it: every packed asset needs a row whose FIRST cell names it
# (RegisterRow.covers), and a CC0 (courtesy) name missing from the credits is
# a warning, not a refusal.
MUSIC_DIR = "music/"

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


def wrap(text: str, indent: str = "  ", hang: str | None = None) -> list[str]:
    """Wrap at TEXT_WIDTH; continuation lines get `hang` (default: indent
    plus two spaces)."""
    hang = indent + "  " if hang is None else hang
    return textwrap.wrap(text, TEXT_WIDTH, initial_indent=indent, subsequent_indent=hang,
                         break_on_hyphens=False, break_long_words=False) or [indent.rstrip()]


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
    # A zip entry stores seconds in steps of two (MS-DOS time), so an odd
    # commit second would read back one lower; round down here so what is
    # written is what is read.
    stamp = tuple(time.gmtime(commit_time - commit_time % 2)[:6])
    return max(stamp, MIN_ZIP_TIME)  # type: ignore[return-value]


# --- The generated texts -------------------------------------------------------------

# CREDITS.txt is read by a player who has the package, not the repo (G6 review
# docs/qa/2026-10-14_2356_G6-readiness.md 2.2, backlog G9): its headings and
# its own sentences name only files inside the package. (A register cell it
# quotes, an asset's origin, may still name the generator that drew it.)
CREDITS_HEADINGS = {
    "screen_en": "English - as shown in the game (Options > Soviet Doom > Credits)",
    "ai_en": "AI tools used to make the game",
    "music": "Music credit lines, reproduced word for word",
    "assets": f"Every picture, sound and piece of music in {PK3_NAME}: origin and licence",
    "screen_ru": "Русский - как в игре (Настройки (Options) > Советский Doom > Авторы)",
    "ai_ru": "ИИ-инструменты, с которыми сделана игра",
}

# D75, D79, D93: the release names every AI tool the game was made with and
# what each did. Two claims depend on what the PK3 packs, so they are read
# from it rather than written by hand (AiShips): the sergeant's face drawn
# from Gemini images (D89, D90) and voice lines from Chatterbox (D87, D91).
# The in-game screen carries a short form (SD_CRED_AI_*, D93). The Russian is
# reviewed with the rest of the in-game text in N11.
AI_TOOLS = ("Claude", "Anthropic", "Claude Code", "Google Gemini", "Fooocus / SDXL",
            "Chatterbox", "Resemble AI")
FACE_LUMP_RE = re.compile(r"^STF(ST|TR|TL|OUCH|EVL|KILL|GOD|DEAD)", re.IGNORECASE)
VOICE_TOOL_MARK = "chatterbox"          # a register Origin naming it means a take ships


@dataclass(frozen=True)
class AiShips:
    face: bool = False      # our STF* face lumps are packed (drawn from Gemini images)
    voices: bool = False    # a packed sound's register row names Chatterbox


def ai_ships(check: LicenceCheck) -> AiShips:
    """What the AI lines may claim, read from the packed assets' register rows."""
    paths = [path for _, covered in check.coverage for path in covered]
    return AiShips(
        face=any(FACE_LUMP_RE.match(Path(path).stem) for path in paths),
        voices=any(VOICE_TOOL_MARK in (row.origin or "").lower()
                   for row, covered in check.coverage if covered))


_AI_TEXT = {
    LANG_ENGLISH: {
        "claude": ("Claude (Anthropic), through Claude Code. The project lead ran the "
                   "game as a studio of AI agents and approved every asset. Claude wrote "
                   "the design documents and the game code, generated the maps by "
                   "program, painted the textures and the pixel art by program, modelled "
                   "the enemies on a 3D rig of the project's own and rendered their "
                   "sprites from it, made the sound effects, sequenced the original music "
                   "and the arrangements of public-domain works, wrote the build and test "
                   "tools and translated the text into Russian."),
        "gemini": ("Google Gemini. The project lead generated images with it, from which "
                   "the first-person frames of the PPSh-41, IZh-58, RPG-7, ROKS-3, hand "
                   "Katyusha and ice axe{face} were drawn and reworked into pixel art. The "
                   "source images are not distributed."),
        "face": ", and the sergeant's face in the status bar,",
        "fooocus": ("Fooocus / SDXL, run locally. Reference images of hands holding the "
                    "weapons, generated by the project lead; used as references only and "
                    "not distributed."),
        "voices_no": ("Chatterbox (Resemble AI), run locally. Trial takes of the enemies' "
                      "voice lines, made with its predefined voices; none is in this "
                      "release, where the enemies speak with Freedoom's voices."),
        "voices_yes": ("Chatterbox (Resemble AI), run locally. Some of the enemies' voice "
                       "lines, made with its predefined voices; the others are Freedoom's."),
    },
    LANG_RUSSIAN: {
        "claude": ("Claude (Anthropic) в Claude Code. Руководитель проекта вёл игру как "
                   "студию ИИ-агентов и утверждал каждый ресурс. Claude написал проектные "
                   "документы и код игры, сгенерировал карты программно, программно "
                   "нарисовал текстуры и пиксель-арт, смоделировал врагов на собственном "
                   "3D-риге проекта и отрисовал по нему их спрайты, сделал звуковые "
                   "эффекты, секвенировал оригинальную музыку и обработки произведений из "
                   "общественного достояния, написал инструменты сборки и проверки и "
                   "перевёл тексты на русский."),
        "gemini": ("Google Gemini. Руководитель проекта создал с его помощью изображения, "
                   "по которым нарисованы кадры от первого лица для ППШ-41, ИЖ-58, РПГ-7, "
                   "РОКС-3, ручной «Катюши» и ледоруба{face}, переработанные в пиксель-арт. "
                   "Исходные изображения не распространяются."),
        "face": ", а также лицо сержанта в строке состояния",
        "fooocus": ("Fooocus / SDXL, запущенная локально. Референсные изображения рук с "
                    "оружием, созданные руководителем проекта; использованы только как "
                    "образец и не распространяются."),
        "voices_no": ("Chatterbox (Resemble AI), запущенная локально. Пробные дубли "
                      "реплик врагов, записанные её стандартными голосами; в этот выпуск "
                      "они не вошли, враги говорят голосами Freedoom."),
        "voices_yes": ("Chatterbox (Resemble AI), запущенная локально. Часть реплик "
                       "врагов, записанная её стандартными голосами; остальные - голоса "
                       "Freedoom."),
    },
}


def ai_disclosure(lang: str, ships: AiShips = AiShips()) -> list[str]:
    """One paragraph per AI tool, in CREDITS.txt's order."""
    text = _AI_TEXT[lang]
    return [text["claude"],
            text["gemini"].format(face=text["face"] if ships.face else ""),
            text["fooocus"],
            text["voices_yes" if ships.voices else "voices_no"]]


# The disclosure as one text per language, before the package is read (the
# Gemini tests in tests/test_ppsh_sprites.py and test_gemini_weapons_install.py
# read it); CREDITS.txt itself is written from ai_disclosure(lang, ai_ships()).
AI_DISCLOSURE = {lang: " ".join(ai_disclosure(lang)) for lang in _AI_TEXT}


# README.txt's short form ("MADE WITH"), each line wrapped under the heading.
_MADE_WITH = {
    LANG_ENGLISH: {
        "lead": ("The engine is GZDoom and the game data under it is Freedoom. The game "
                 "itself was made by a studio of AI agents run by the project lead, who "
                 "approved every asset:"),
        "claude": ("Claude (Anthropic), through Claude Code: design, maps, code, "
                   "textures, sprites, sound effects, music and the Russian text."),
        "gemini": "Google Gemini: images the first-person weapons{face} were drawn from.",
        "face": " and the sergeant's face",
        "fooocus": "Fooocus / SDXL, run locally: reference images of the hands.",
        "voices_no": ("Chatterbox (Resemble AI), run locally: trial voice takes; in this "
                      "release the enemies speak with Freedoom's voices."),
        "voices_yes": "Chatterbox (Resemble AI), run locally: some enemy voice lines.",
        "rest": ("Sound clips from CC0 packs by Kenney, rubberduck and Darsycho "
                 "(OpenGameArt); public-domain music, some in MIDI sequences by Jerry "
                 "Engelbach and Peter Gerloff. Built with Python, Pillow, NumPy and "
                 f"FFmpeg. Everyone credited: {CREDITS_NAME}."),
    },
    LANG_RUSSIAN: {
        "lead": ("Движок - GZDoom, игровые данные под ним - Freedoom. Саму игру сделала "
                 "студия ИИ-агентов во главе с руководителем проекта, который "
                 "утверждал каждый ресурс:"),
        "claude": ("Claude (Anthropic) в Claude Code: проект, карты, код, текстуры, "
                   "спрайты, звуковые эффекты, музыка и русский текст."),
        "gemini": ("Google Gemini: изображения, по которым нарисовано оружие от первого "
                   "лица{face}."),
        "face": " и лицо сержанта",
        "fooocus": "Fooocus / SDXL, запущенная локально: референсные изображения рук.",
        "voices_no": ("Chatterbox (Resemble AI), запущенная локально: пробные дубли "
                      "голосов; в этом выпуске враги говорят голосами Freedoom."),
        "voices_yes": ("Chatterbox (Resemble AI), запущенная локально: часть реплик "
                       "врагов."),
        "rest": ("Звуковые фрагменты из CC0-наборов Kenney, rubberduck и Darsycho "
                 "(OpenGameArt); музыка из общественного достояния, частью в "
                 "MIDI-секвенциях Джерри Энгельбаха (Jerry Engelbach) и Петера Герлоффа "
                 "(Peter Gerloff). Инструменты: Python, Pillow, NumPy и FFmpeg. Все "
                 f"авторы: {CREDITS_NAME}."),
    },
}


def render_made_with(lang: str, ships: AiShips = AiShips()) -> str:
    text = _MADE_WITH[lang]
    out = wrap(text["lead"], "  ", "  ")
    for item in (text["claude"],
                 text["gemini"].format(face=text["face"] if ships.face else ""),
                 text["fooocus"],
                 text["voices_yes" if ships.voices else "voices_no"]):
        out += wrap(item, "    ", "      ")
    out += wrap(text["rest"], "  ", "  ")
    return "\n".join(out)


def render_credits(version: str, commit: str, credits: dict[str, list[tuple[str, str]]],
                   music_lines: list[str], check: LicenceCheck) -> str:
    title = f"Soviet Doom {version} - credits"
    out = [title, "=" * len(title), ""]
    out += wrap("Who made this game and what it is built from: the credits as the game "
                "shows them, in English and in Russian, the music credit lines their "
                f"licences ask for, and the origin and licence of every asset in {PK3_NAME}. "
                f"Built from commit {commit}.", "", "")
    out.append("")

    def section(heading: str, lead: list[str] | None = None) -> None:
        out.extend([heading, "-" * len(heading)])
        out.extend(lead or [])

    def screen(lines: list[tuple[str, str]], heading: str) -> None:
        section(heading)
        for ident, text in lines:
            if ident == CREDIT_TITLE_ID:
                continue
            if ident.startswith(CREDIT_HEADER_MARK):
                out.extend(["", text.upper()])
            else:
                out.append("  " + text)
        out.append("")

    ships = ai_ships(check)

    def ai_section(heading: str, lang: str) -> None:
        section(heading)
        for paragraph in ai_disclosure(lang, ships):
            out.extend(wrap(paragraph, "  ", "  "))
            out.append("")

    screen(credits.get(LANG_ENGLISH, []), CREDITS_HEADINGS["screen_en"])

    out.append("")
    ai_section(CREDITS_HEADINGS["ai_en"], LANG_ENGLISH)

    if music_lines:
        out.append("")
        section(CREDITS_HEADINGS["music"])
        for line in music_lines:
            out.extend(wrap(line))
            out.append("")

    out.append("")
    section(CREDITS_HEADINGS["assets"],
            [""] + wrap("Quoted from the project's licence registers. An origin may name the "
                        "script or file in the project's source repository that made the "
                        "asset; those are not part of this package.", "", "") + [""])
    for row, paths in check.coverage:
        out.extend(wrap(_describe_paths(row, paths), "* ", "  "))
        if row.origin:
            out.extend(wrap("Origin: " + row.origin, "    "))
        out.extend(wrap("Licence: " + row.licence, "    "))
        music = [check.music[p] for p in paths if p in check.music]
        for entry in music:
            out.extend(wrap("Obligation: " + entry.obligation, "    "))
        out.append("")
    out.extend(wrap("Everything else in the PK3 (maps, ZScript, definition lumps) is the "
                    "project's own work: code under GNU GPL 3.0 or later, the rest under "
                    "CC BY-NC-SA 4.0 (LICENSE.md; the full texts are "
                    f"{GPL_TEXT_NAME} and {CC_TEXT_NAME}). Art made from Freedoom's "
                    "pixels keeps Freedoom's BSD licence (BSD 3-clause), whose notice is "
                    f"{FREEDOOM_TEXT_NAME}.", "", ""))
    out.append("")

    out.append("")
    screen(credits.get(LANG_RUSSIAN, []), CREDITS_HEADINGS["screen_ru"])

    out.append("")
    ai_section(CREDITS_HEADINGS["ai_ru"], LANG_RUSSIAN)
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


# The player readme (G6 review docs/qa/2026-10-14_2356_G6-readiness.md §2.4,
# §5). It names only files inside the package, never a repo path. Map, menu,
# skill and language names come from LANGUAGE (README_IDS), so the readme and
# the game cannot disagree. The controls are GZDoom 4.14.2's default bindings
# for a new configuration as the review read them in the engine's gzdoom.pk3
# (engine/commonbinds.txt + engine/defbinds.txt: W A S D, E uses, Space jumps,
# Ctrl and the arrows unbound); the sign-off run confirms them on a fresh
# config (RELEASE.md §2, row 5). The Russian half is reviewed once by N11 (D60).
README_TEMPLATE = """\
SOVIET DOOM {version}
{rule}

A total conversion for GZDoom. The USSR of the 1970s is invaded by two allied
alien factions, Yankee and Nazi, united to defend capital. You are a Spetsnaz
sergeant who came to this country as a refugee child from Barcelona.
A fan project, not affiliated with id Software.

WHAT IS IN IT
  The campaign, three maps played in order ({newgame} > {ep01}):
    1. {map01}
    2. {map02}
    3. {map03}, the end of the episode
  The practice range: every weapon, no story ({newgame} > {ep02}).
  Five difficulties, from "{skill1}"
  to "{skill5}".
  English and Russian, switched inside the game.
  Built from commit {commit}.

WHAT YOU NEED
  1. GZDoom {gzdoom} or newer, free, for Windows, macOS and Linux:
     https://zdoom.org/downloads
  2. Freedoom: Phase 2, the file freedoom2.wad (free; tested with
     Freedoom {freedoom}): https://freedoom.github.io/download.html
     The Freedoom download holds two files: this game needs freedoom2.wad,
     not freedoom1.wad. The game data (the IWAD) is NOT in this package.
  3. {pk3}, from this package.

HOW TO START (Windows)
  1. Unzip GZDoom into a folder of its own.
  2. Copy freedoom2.wad and {pk3} into that folder.
  3. Drag {pk3} onto gzdoom.exe. If GZDoom asks which game to play,
     choose Freedoom: Phase 2.
  Or, from a command prompt in that folder:
    gzdoom -iwad freedoom2.wad -file {pk3}
  In PowerShell, type .\\gzdoom instead of gzdoom.

HOW TO START (macOS, Linux)
  Start GZDoom from a terminal with the same two options, giving the path
  of each file:
    gzdoom -iwad /path/to/freedoom2.wad -file /path/to/{pk3}
  On macOS the program is GZDoom.app/Contents/MacOS/gzdoom.

LANGUAGE AND CREDITS
  {options} > {optmnu} > {language}:
    {langauto}, {langen} or {langru}.
  It applies at once and is remembered.
  The credits are on the same screen: {options} > {optmnu} > {credits}.

CONTROLS (GZDoom's defaults on a new install; change them in
Options > Customize Controls)
  Move ............ W A S D
  Turn and aim .... mouse
  Fire ............ left mouse button
  Use ............. E: open doors, press switches
  Jump ............ Space (in classic Doom, Space opened doors)
  Run ............. hold Shift; Caps Lock toggles always-run
  Weapons ......... 1 to 7, or the mouse wheel
  Automap ......... Tab
  Save / load ..... F2 / F3; quick save / quick load: F6 / F9
  Menu ............ Esc
  An older GZDoom configuration keeps its own keys.

LICENCE AND CREDITS
  Code: GNU GPL 3.0 or later. Art, sound, maps and text: CC BY-NC-SA 4.0.
  See LICENSE.md; the full texts are LICENSE-GPL-3.0.txt and
  LICENSE-CC-BY-NC-SA-4.0.txt. Art made from Freedoom's pixels keeps
  Freedoom's BSD licence: LICENSE-FREEDOOM-BSD-3.txt. Everyone credited, and
  every asset's origin: CREDITS.txt.

MADE WITH
{made_with}

CHECK THE DOWNLOAD
  SHA256SUMS holds the SHA-256 of every other file in this package.
  Linux:   sha256sum -c SHA256SUMS
  macOS:   shasum -a 256 -c SHA256SUMS
  Windows, in PowerShell:
    Get-FileHash {pk3}
  or in a command prompt:
    certutil -hashfile {pk3} SHA256
  and compare the result with the file's line in SHA256SUMS (capital or
  small letters do not matter).

----------------------------------------------------------------------------

СОВЕТСКИЙ DOOM {version}
{rule_ru}

Тотальная конверсия для GZDoom. СССР 1970-х годов подвергается вторжению двух
союзных инопланетных фракций, янки и нацистов, объединившихся ради защиты
капитала. Вы - сержант спецназа, попавший в эту страну ребёнком-беженцем из
Барселоны. Фанатский проект, не связанный с компанией id Software.

ЧТО ВНУТРИ
  Кампания: три карты, проходятся по порядку ({newgame_ru} > {ep01_ru}):
    1. {map01_ru}
    2. {map02_ru}
    3. {map03_ru} - конец эпизода
  Полигон: всё оружие, без сюжета ({newgame_ru} > {ep02_ru}).
  Пять уровней сложности, от «{skill1_ru}»
  до «{skill5_ru}».
  Английский и русский языки, переключаются в игре.
  Собрано из коммита {commit}.

ЧТО НУЖНО
  1. GZDoom {gzdoom} или новее, бесплатно, для Windows, macOS и Linux:
     https://zdoom.org/downloads
  2. Freedoom: Phase 2, файл freedoom2.wad (бесплатно; проверено с
     Freedoom {freedoom}): https://freedoom.github.io/download.html
     В архиве Freedoom два файла: игре нужен freedoom2.wad, а не
     freedoom1.wad. Игровых данных (IWAD) в этом архиве НЕТ.
  3. {pk3} из этого архива.

КАК ЗАПУСТИТЬ (Windows)
  1. Распакуйте GZDoom в отдельную папку.
  2. Скопируйте в неё freedoom2.wad и {pk3}.
  3. Перетащите {pk3} на gzdoom.exe. Если GZDoom спросит, в какую
     игру играть, выберите Freedoom: Phase 2.
  Или из командной строки в этой папке:
    gzdoom -iwad freedoom2.wad -file {pk3}
  В PowerShell пишите .\\gzdoom вместо gzdoom.

КАК ЗАПУСТИТЬ (macOS, Linux)
  Запустите GZDoom из терминала с теми же двумя параметрами, указав путь
  к каждому файлу:
    gzdoom -iwad /путь/к/freedoom2.wad -file /путь/к/{pk3}
  В macOS программа находится в GZDoom.app/Contents/MacOS/gzdoom.

ЯЗЫК И АВТОРЫ
  {options_ru} (Options) > {optmnu_ru} > {language_ru}:
    {langauto_ru}, {langen_ru} или {langru_ru}.
  Применяется сразу и запоминается.
  Там же список авторов: {options_ru} > {optmnu_ru} > {credits_ru}.

УПРАВЛЕНИЕ (по умолчанию в новом GZDoom; меняется в настройках управления,
Options > Customize Controls)
  Движение ........ W A S D
  Поворот, прицел . мышь
  Огонь ........... левая кнопка мыши
  Действие ........ E: открыть дверь, нажать рубильник
  Прыжок .......... пробел (в классическом Doom пробел открывал двери)
  Бег ............. удерживать Shift; Caps Lock - всегда бегом
  Оружие .......... 1-7 или колесо мыши
  Карта ........... Tab
  Сохранить/загр. . F2 / F3; быстро: F6 / F9
  Меню ............ Esc
  В старой конфигурации GZDoom остаются ваши прежние клавиши.

ЛИЦЕНЗИЯ И АВТОРЫ
  Код: GNU GPL 3.0 или новее. Графика, звук, карты и тексты: CC BY-NC-SA 4.0.
  См. LICENSE.md; полные тексты лицензий: LICENSE-GPL-3.0.txt и
  LICENSE-CC-BY-NC-SA-4.0.txt. Графика на основе пикселей Freedoom остаётся
  под лицензией BSD проекта Freedoom: LICENSE-FREEDOOM-BSD-3.txt. Все авторы
  и происхождение каждого ресурса: CREDITS.txt.

ЧЕМ СДЕЛАНО
{made_with_ru}

ПРОВЕРКА ЗАГРУЗКИ
  В SHA256SUMS записаны SHA-256 всех остальных файлов этого архива.
  Linux:   sha256sum -c SHA256SUMS
  macOS:   shasum -a 256 -c SHA256SUMS
  Windows, в PowerShell:
    Get-FileHash {pk3}
  или в командной строке:
    certutil -hashfile {pk3} SHA256
  и сравните результат со строкой этого файла в SHA256SUMS (регистр букв
  значения не имеет).
"""

# D3 and D2 (docs/PRD.md): the versions the mod is built and tested against.
GZDOOM_MINIMUM = "4.14.2"
FREEDOOM_TESTED = "0.13.0"


# The LANGUAGE ids the readme quotes, so it names things as the game does.
README_IDS = {
    "map01": "SD_MAP01_NAME", "map02": "SD_MAP02_NAME", "map03": "SD_MAP03_NAME",
    "ep01": "SD_EP01_NAME", "ep02": "SD_EP02_NAME",
    "newgame": "SD_MNU_NEWGAME", "options": "SD_MNU_OPTIONS",
    "optmnu": "SD_OPTMNU_TITLE", "language": "SD_OPTMNU_LANGUAGE",
    "langauto": "SD_LANGVAL_AUTO", "langen": "SD_LANGVAL_EN", "langru": "SD_LANGVAL_RU",
    "credits": "SD_CRED_TITLE",
    "skill1": "SD_SKILL_1", "skill5": "SD_SKILL_5",
}


def render_readme(version: str, commit: str, strings: dict[str, dict[str, str]],
                  ships: AiShips = AiShips()) -> str:
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
        rule="=" * len(title_en), rule_ru="=" * len(title_ru),
        made_with=render_made_with(LANG_ENGLISH, ships),
        made_with_ru=render_made_with(LANG_RUSSIAN, ships), **names)


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
    licence_texts_dir: Path = DEFAULT_LICENCE_TEXTS_DIR
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


def read_licence_text(directory: Path, text: LicenceText) -> bytes:
    """The published bytes of a full licence text, or ReleaseError.

    Line endings: the texts are served with LF only and hold no CR at all,
    and the repo has no .gitattributes while this PC runs core.autocrlf=true,
    so a fresh Windows checkout may hand us CRLF. Turning CRLF back into LF
    restores exactly the bytes git stores (and the publisher served); the
    pinned SHA-256 then proves it, so nothing else can slip through."""
    path = directory / text.name
    if not path.is_file():
        raise ReleaseError(f"{text.name} not found: {path}; it is the licence text for the "
                           f"{text.covers}, downloaded verbatim from {text.url}")
    data = path.read_bytes().replace(CRLF, LF)
    digest = sha256(data)
    if digest != text.sha256:
        raise ReleaseError(f"{text.name} is not the text published at {text.url} "
                           f"(SHA-256 {digest}, expected {text.sha256}); a licence text "
                           "ships verbatim: restore it from git, never edit it")
    return data


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

    # Read first: a missing or edited text refuses before anything is built.
    licence_texts = {text.name: read_licence_text(config.licence_texts_dir, text)
                     for text in LICENCE_TEXTS}

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
        **licence_texts,
        CREDITS_NAME: render_credits(config.version, commit, credits,
                                     verbatim_music_lines(music_text), check).encode("utf-8"),
        README_NAME: render_readme(config.version, commit, language_strings(language_text),
                                   ai_ships(check)).encode("utf-8"),
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
