#!/usr/bin/env python3
"""Readers of the project's licence registers, shared by every tool and test.

Two registers say what may ship and whom it obliges us to credit:

  docs/art/LICENSES.md          every packed asset, its origin and licence
                                (any Markdown table with a Licence column)
  docs/sound/MUSIC-RIGHTS.md    section 4.5, "what ships": the music, its
                                obligation, and the credit lines to reproduce
                                verbatim

Two readers used to parse them, each its own way: tools/release.py (what may
ship, CREDITS.txt) and tests/test_credits.py (the in-game credits screen
carries every name). This module is the one reading both now use, so the
screen and the release can never disagree about a register.

The reading, in short:

  * a register row covers what the backticked names of its FIRST cell name:
    a lump stem, a file name, or a folder (`fonts/bigfont/*.png`); a language
    variant (`localized/textures/M_PAUSE.ru.png`) is covered by its base's
    row (check_pk3 category `localized` applies the same rule);
  * `idem` in a licence or origin cell means "the row above";
  * a licence cell obliges a credit when it says `credit`, `{{Attribution`,
    CC BY, BSD, MIT or OFL; whom is `credit "Name"` in that cell, else every
    bold span of the row that is a name. A row that needs a credit and names
    nobody is a problem the register must fix;
  * CC0 (or "courtesy") obliges nothing: its bold names are a courtesy
    credit, which the project gives anyway (ADR 009, D-009-3);
  * our own rows (D15) are credited by the team line and the licence line.

Python 3 standard library only, like tools/check_pk3.py.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402  (owner of the language-variant folder name)

PROJECT_ROOT = TOOLS_DIR.parent
LICENSES_PATH = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MUSIC_RIGHTS_PATH = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
LICENSES_SOURCE = "docs/art/LICENSES.md"     # how messages name the register

LOCALIZED_DIR = check_pk3.LOCALIZED_DIR

# --- Markdown -------------------------------------------------------------------

CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
TABLE_RULE_RE = re.compile(r"^\s*\|[\s|:-]+\|\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BACKTICKED_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

# --- The licence register -------------------------------------------------------

LICENCE_HEADER_RE = re.compile(r"licen[cs]e", re.I)
ORIGIN_HEADER_RE = re.compile(r"(origin|author)", re.I)
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
# A bold span with one of these words is a sentence, not a name.
NOT_A_NAME_RE = re.compile(r"\b(credit|required|accepted|licen[cs]e|none)\b", re.I)
IDEM = "idem"

# --- The music register (MUSIC-RIGHTS 4.5) ---------------------------------------

MUSIC_SHIPS_HEADING_RE = re.compile(r"^4\.5\b")
OBLIGATION_HEADER_RE = re.compile(r"^obligation", re.I)
OBLIGATION_CREDIT_RE = re.compile(r"^credit\s+(.+?)\s*$", re.I)
# The paragraphs that introduce a blockquote to reproduce verbatim.
VERBATIM_INTRO_RE = re.compile(r"credit line|courtesy line", re.I)
CREDIT_LINE_INTRO_RE = re.compile(r"credit line", re.I)


class RegisterError(ValueError):
    """A register row needs a credit but does not say whom to credit."""


# --- Small helpers ----------------------------------------------------------------

def plain(markdown: str) -> str:
    """A register cell as plain text: emphasis, code marks and escapes off."""
    text = markdown.replace("\\|", "|").replace("**", "").replace("`", "")
    text = re.sub(r"(?<!\w)\*(\S(?:.*?\S)?)\*(?!\w)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def cells(line: str) -> list[str]:
    """The cells of a Markdown table row; an escaped `\\|` stays in its cell."""
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
            header = cells(lines[i])
            rows = []
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append(cells(lines[j]))
                j += 1
            yield heading, header, rows
            i = j
            continue
        i += 1


def section_body(text: str, heading_re: re.Pattern[str]) -> str:
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


def localized_base(path: str) -> str | None:
    """The base graphic a language variant stands for, or None.

    `localized/textures/M_PAUSE.ru.png` -> `M_PAUSE`: the variant is the same
    asset in another language, so its base's licence row covers it (a row
    naming the variant itself also does). check_pk3 category `localized`
    applies the same rule; this is the shipping side of it.
    """
    head, _, filename = path.rpartition("/")
    if not head or head.split("/", 1)[0].lower() != LOCALIZED_DIR:
        return None
    base = filename.split(".", 1)[0]
    return base or None


# --- The licence register (docs/art/LICENSES.md) -----------------------------------

@dataclass
class RegisterRow:
    """One row of a register table."""

    source: str                 # register file name, for messages
    heading: str                # the section it sits in
    tokens: tuple[str, ...]     # what it covers: backticked names in its first cell
    licence: str                # the licence cell, `idem` resolved
    origin: str                 # origin / author, plain text
    required: tuple[str, ...]   # names the credits MUST carry
    courtesy: tuple[str, ...]   # names credited by choice (CC0)
    problem: str = ""           # a row that needs a credit but names nobody
    own_work: bool = False      # the project's own (D15): the team line credits it

    def covers(self, path: str) -> bool:
        stem = Path(path).stem.upper()
        name = Path(path).name.upper()
        base = (localized_base(path) or stem).upper()
        for token in self.tokens:
            upper = token.upper()
            if "/" in upper:
                head, _, tail = upper.rpartition("/")
                prefix = (head if ("*" in tail or not tail) else upper).rstrip("/") + "/"
                if path.upper().startswith(prefix):
                    return True
            elif upper in (stem, name, base):
                return True
        return False


def _names_in_row(row: list[str], licence: str) -> list[str]:
    """Whom a row names: `credit "X"` in the licence cell, else every bold
    span of the row that is a name, not a sentence."""
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


def _resolve_idem(origin: str, previous: str) -> str:
    """`idem` in an origin cell means "the row above": a bare `(a) idem` is
    the row above's origin; `(a) idem, variant B` keeps its variant."""
    if re.fullmatch(r"(\(a\)\s*)?idem\.?", origin, re.I):
        return previous
    return re.sub(r"\bidem\b", "same source as above", origin, flags=re.I)


def _credits_for(row: list[str], cell: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """(required names, courtesy names, problem) for a licence cell."""
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


def parse_licence_register(text: str, source: str = LICENSES_SOURCE) -> list[RegisterRow]:
    """Every row of every table that has a Licence column."""
    rows_out: list[RegisterRow] = []
    for heading, header, rows in iter_tables(text):
        col = next((k for k, h in enumerate(header) if LICENCE_HEADER_RE.search(h)), None)
        if col is None:
            continue
        origin_cols = [k for k, h in enumerate(header)
                       if k != col and ORIGIN_HEADER_RE.match(h)]
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
                problem, own = previous.problem, previous.own_work
            else:
                licence = plain(cell)
                required, courtesy, problem = _credits_for(row, cell)
                own = required == OWN_WORK_CREDITS and not QUOTED_CREDIT_RE.search(cell)
                if previous is not None:
                    origin = _resolve_idem(origin, previous.origin)
            entry = RegisterRow(source, heading, _row_tokens(row[0]), licence, origin,
                                required, courtesy, problem, own)
            rows_out.append(entry)
            previous = entry
    return rows_out


def credited_names(rows: list[RegisterRow]) -> list[str]:
    """Every name the in-game credits must carry for these register rows, in
    register order: the required names and the courtesy ones (ADR 009 gives
    the courtesy credit too). Our own rows are left to the team line.

    Raises RegisterError on a row that needs a credit and names nobody: the
    register must say whom.
    """
    names: list[str] = []
    for row in rows:
        if row.problem:
            raise RegisterError(f"{row.source} row {', '.join(row.tokens) or row.heading}: "
                                f"{row.problem}")
        if row.own_work:
            continue
        names.extend(n for n in (*row.required, *row.courtesy) if n not in names)
    return names


def attribution_names(text: str, source: str = LICENSES_SOURCE) -> list[str]:
    """credited_names() of a LICENSES.md text."""
    return credited_names(parse_licence_register(text, source))


# --- The music register (docs/sound/MUSIC-RIGHTS.md 4.5) -----------------------------

@dataclass
class MusicRow:
    tokens: tuple[str, ...]
    obligation: str
    required: tuple[str, ...]


def parse_music_register(text: str) -> list[MusicRow]:
    """The rows of the tables in MUSIC-RIGHTS 4.5 that have an Obligation
    column; `credit X` in that cell obliges the credit X."""
    out: list[MusicRow] = []
    for _, header, rows in iter_tables(section_body(text, MUSIC_SHIPS_HEADING_RE)):
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


def music_attribution_names(text: str) -> list[str]:
    """Every name MUSIC-RIGHTS 4.5 obliges the credits to carry, in order."""
    names: list[str] = []
    for row in parse_music_register(text):
        names.extend(n for n in row.required if n not in names)
    return names


def _verbatim_quotes(text: str, intro_re: re.Pattern[str]) -> list[str]:
    section = section_body(text, MUSIC_SHIPS_HEADING_RE)
    out: list[str] = []
    armed = False
    quote: list[str] = []
    for line in section.splitlines() + [""]:
        if line.startswith(">"):
            if armed:
                quote.append(line.lstrip(">").strip())
            continue
        if quote:
            out.append(plain(" ".join(quote)))
            quote = []
            armed = False
        if intro_re.search(line):
            armed = True
    return out


def verbatim_music_lines(text: str) -> list[str]:
    """The blockquotes MUSIC-RIGHTS 4.5 introduces as a line to reproduce
    ("The credit line", "The courtesy line"), as plain text, in order."""
    return _verbatim_quotes(text, VERBATIM_INTRO_RE)


def verbatim_music_credit(text: str) -> str:
    """The first line MUSIC-RIGHTS 4.5 introduces as "The credit line" (the
    obligation, not a courtesy), as plain text; "" when there is none."""
    quotes = _verbatim_quotes(text, CREDIT_LINE_INTRO_RE)
    return quotes[0] if quotes else ""
