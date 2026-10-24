"""No Spanish reaches the player (D129).

The CEO, 2026-10-24: «en el instalador o en algún sitio habías mezclado
español. La documentación solo tiene que ir en inglés, catalán y ruso.»
(the installer had Spanish mixed in; the texts go in English, Catalan and
Russian only). The game's languages are English, Russian and Catalan; Spanish
is used only in the chat with the CEO.

What is guarded:

  * src/lumps/LANGUAGE, every section and comment;
  * README.md (the repository's front page) and LICENSE.md (it ships);
  * README.txt and CREDITS.txt as tools/release.py renders them from the
    repo's LANGUAGE, docs/art/LICENSES.md and docs/sound/MUSIC-RIGHTS.md
    (CREDITS.txt quotes the registers' origin and licence cells);
  * every text file of the Windows, macOS and Linux portable packages as
    tools/release_portable.py assembles them (launchers, README-FIRST.txt,
    the readme note, gzdoom_portable.ini, GZDOOM-SOURCE.txt);
  * the source of both generators, so a Spanish template cannot come back;
  * no file the release or a portable package ships has a Spanish name;
  * the repo documentation (WORKING-AGREEMENTS §4): every .md, .html and
    .txt under docs/ except the Russian mirror docs/ru/, the HTML review
    sheets of docs/art/previews/ included;
  * the review-sheet generators: every .py of tools/, tools/art/ and
    tools/audio/ (their strings and comments) and tools/art/*.html.

The CEO's literal words stay literal (§4), so the docs and generator checks
read only what lies OUTSIDE quotation marks: «…», “…” and "…" in prose; in a
Python file, inside its comments and inside its string literals (a quotation
in a string is \\"…\\"); in an HTML sheet, the visible text with tags and
base64 removed, and in its scripts only «…», “…”, \\"…\\" and &quot;…&quot;
count as quotations, so a Spanish JS label is caught. Whether each quotation
carries its English gloss is NOT checked: §4 wants the gloss only "when the
text around them does not already restate them", and a machine cannot tell
a restatement (measured 2026-10-24: a "quote followed by an English
parenthesis or quote" heuristic flagged 41 quotations, 37 of them PRD rows
whose bold text restates the decision). Glosses stay a PMO review item.
Two narrow exceptions: the slogan "No pasarán" (D20, a name), and
SPEC_EDITS in tools/art/walk_stride.py, whose left sides are
gemini_enemy.py's pre-D129 text matched byte for byte (history, written by
nothing).

How Spanish is told apart from English, Russian and Catalan (SPANISH_TEXT):

  * the characters ¿ ¡ ñ á: none of them is written in English, Russian or
    Catalan (Catalan writes "ny" and "à");
  * the endings -ción / -ciones (Catalan: -ció / -cions);
  * frequent Spanish words that are not Catalan or English words: está,
    están, también, después, cómo, qué, más, juego, juegos, pulsa, elige,
    hay, muy, pero, los, las, descomprime, partidas, ruso, inglés, puedes,
    tienes, usted, listo, archivo, cerrar, ejecutar. Whole words, case-insensitive; "los"/"las" after a hyphen
    are skipped, because Catalan writes enclitics such as "definir-los".
    Catalan words that are also Spanish (aquí, carpeta, jugar, partida) are
    deliberately absent. The skill name «No pasaran, comrades» (D20) is a
    historical slogan used as a name, not Spanish text, and passes.

Spanish file names (SPANISH_NAME): jugar, juega, juego, leeme / léeme,
instrucciones, español / espanol, lanzador, partidas.

PENDING lists Spanish that still ships from a file this guard does not own,
so the suite stays green while its owner fixes it; each entry names the file.
Remove an entry once the text is gone.

Run:  python -m unittest tests.test_no_spanish -v
"""

from __future__ import annotations

import io
import re
import sys
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import licences  # noqa: E402
import release  # noqa: E402
import release_portable as rp  # noqa: E402

LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
VERSION = "0.0-test"
COMMIT = "0123456789ab"

SPANISH_WORDS = ("está", "están", "también", "después", "cómo", "qué", "más", "juego",
                 "juegos", "pulsa", "elige", "hay", "muy", "pero", "los", "las",
                 "descomprime", "partidas", "ruso", "inglés", "puedes", "tienes", "usted",
                 "listo", "archivo", "cerrar", "ejecutar")
SPANISH_TEXT = re.compile(
    r"[¿¡ñÑáÁ]"
    r"|\b\w{1,30}ci(?:ón|ones)\b"
    r"|(?<![-\w])(?:" + "|".join(SPANISH_WORDS) + r")\b",
    re.IGNORECASE)
SPANISH_NAME = re.compile(
    r"jugar|juega|juego|l[eé]eme|instrucciones|espa[ñn]ol|lanzador|partidas", re.IGNORECASE)

# Spanish that ships today from a file another role owns (D129 follow-up).
# Empty since the Episode 3 music rows of docs/art/LICENSES.md gave their
# Origin cell (quoted by CREDITS.txt) in English.
PENDING: tuple[str, ...] = ()


def spanish_lines(text: str) -> list[str]:
    """The lines of text that look Spanish, with what matched."""
    for pending in PENDING:
        text = text.replace(pending, "")
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        hits = [m.group(0) for m in SPANISH_TEXT.finditer(line)]
        if hits:
            found.append(f"{number}: {hits} {line.strip()[:120]}")
    return found


def pk3_with_language() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("LANGUAGE", LANGUAGE.read_bytes())
    return buffer.getvalue()


def release_texts() -> dict[str, str]:
    """README.txt and CREDITS.txt as tools/release.py writes them from this tree,
    with every licence-register row covered (so every Origin cell is quoted)."""
    language = LANGUAGE.read_text(encoding="utf-8")
    rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
    music = licences.verbatim_music_lines(licences.MUSIC_RIGHTS_PATH.read_text(encoding="utf-8"))
    check = release.LicenceCheck(coverage=[(row, list(row.tokens)) for row in rows])
    return {
        release.README_NAME: release.render_readme(VERSION, COMMIT,
                                                   release.language_strings(language)),
        "CREDITS.txt": release.render_credits(VERSION, COMMIT,
                                              release.parse_credit_lines(language), music, check),
    }


def release_files() -> dict[str, bytes]:
    """The release's files as a portable package receives them."""
    files = {name: b"" for name in release.RELEASE_FILES}
    files.update({name: text.encode("utf-8") for name, text in release_texts().items()})
    files[release.PK3_NAME] = pk3_with_language()
    files["LICENSE.md"] = (PROJECT_ROOT / "LICENSE.md").read_bytes()
    return files


def unix_engine(platform: str) -> rp.UnixEngine:
    facts = ({"macos_min": "10.15"} if platform == rp.MACOS else
             {"arch": "amd64", "depends": ["libc6", "libsdl2-2.0-0"], "recommends": ["libopenal1"]})
    return rp.UnixEngine(entries=[], licences={"gpl.txt": b"GPL"}, facts=facts)


def packages() -> dict[str, dict[str, bytes]]:
    """Every file of the three portable packages, by platform and path."""
    files = release_files()
    out = {rp.PLATFORM: rp.package_files(VERSION, files, {"gzdoom.exe": b"MZ"}, b"IWAD")}
    for platform in (rp.MACOS, rp.LINUX):
        entries = rp.unix_package(platform, VERSION, files, unix_engine(platform), b"IWAD")
        out[platform] = {e.path: e.data for e in entries if e.is_file}
    return out


TEXT_SUFFIXES = (".txt", ".md", ".bat", ".command", ".sh", ".ini")


class NoSpanishInTheGameTest(unittest.TestCase):

    def test_language_has_no_spanish_section(self):
        headers = re.findall(r"^\s*\[([^\]]+)\]", LANGUAGE.read_text(encoding="utf-8"), re.M)
        for header in headers:
            self.assertNotIn("es", header.lower().split(), f"[{header}]: no Spanish section")

    def test_language_has_no_spanish_text(self):
        self.assertEqual(spanish_lines(LANGUAGE.read_text(encoding="utf-8")), [])


class NoSpanishInWhatShipsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.packages = packages()

    def test_readme_md_and_licence(self):
        for name in ("README.md", "LICENSE.md"):
            text = (PROJECT_ROOT / name).read_text(encoding="utf-8")
            self.assertEqual(spanish_lines(text), [], name)

    def test_release_readme_and_credits(self):
        for name, text in release_texts().items():
            self.assertEqual(spanish_lines(text), [], name)

    def test_every_text_file_of_the_portable_packages(self):
        for platform, files in self.packages.items():
            for name, data in files.items():
                if name.endswith(TEXT_SUFFIXES) or "." not in name.rsplit("/", 1)[-1]:
                    if name.endswith(".wad") or name == release.PK3_NAME:
                        continue
                    text = data.decode("utf-8-sig", errors="replace")
                    self.assertEqual(spanish_lines(text), [], f"{platform}: {name}")

    def test_no_spanish_file_names(self):
        names = list(release.RELEASE_FILES)
        for files in self.packages.values():
            names += list(files)
        spanish = sorted(n for n in names if SPANISH_NAME.search(n))
        self.assertEqual(spanish, [], "a shipped file has a Spanish name")

    def test_the_guard_catches_the_old_spanish_files(self):
        # The names and phrases the packages carried before D129.
        for name in ("Jugar Soviet Doom.bat", "LEEME.txt", "jugar.sh",
                     "Jugar Soviet Doom.command"):
            self.assertRegex(name, SPANISH_NAME)
        for phrase in ("SOVIET DOOM 1.0 PARA WINDOWS - LISTO PARA JUGAR",
                       "Pulsa Intro para cerrar.", "El juego empieza en inglés.",
                       "No encuentro gzdoom.exe junto a este archivo."):
            self.assertTrue(spanish_lines(phrase), phrase)
        # ...and lets Catalan through.
        for phrase in ("N'estàs segur?", "definir-los a [default]", "Com jugar-hi.",
                       "Aquí només hi ha ids", "Prem %s per continuar", "CONTINUARÀ"):
            self.assertEqual(spanish_lines(phrase), [], phrase)


class NoSpanishInTheGeneratorsTest(unittest.TestCase):

    def test_the_release_generators_carry_no_spanish_template(self):
        for name in ("release.py", "release_portable.py"):
            text = (TOOLS_DIR / name).read_text(encoding="utf-8")
            self.assertEqual(spanish_lines(text), [], name)

    def test_the_sheet_generators_write_no_spanish(self):
        found = []
        for path in generator_files():
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            if path.suffix == ".py":
                hits = python_spanish_lines(text, HISTORICAL_PY.get(rel))
            else:
                hits = spanish_lines(html_unquoted(text))
            found += [f"{rel}:{hit}" for hit in hits]
        self.assertEqual(found, [])


class NoSpanishInTheDocsTest(unittest.TestCase):

    def test_docs_outside_quotations(self):
        found = []
        for path in doc_files():
            text = path.read_text(encoding="utf-8")
            text = html_unquoted(text) if path.suffix == ".html" else prose_unquoted(text)
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            found += [f"{rel}:{hit}" for hit in spanish_lines(text)]
        self.assertEqual(found, [])

    def test_the_quote_reader(self):
        # Spanish outside quotation marks is caught, in prose, HTML and Python...
        self.assertTrue(spanish_lines(prose_unquoted("Las texturas están listas.")))
        self.assertTrue(spanish_lines(html_unquoted(
            '<p class="x">Pulsa para votar</p>')))
        self.assertTrue(spanish_lines(html_unquoted(
            '<script>const L = {"copy": "Copiar el resultado de las votaciones"};</script>')))
        self.assertTrue(python_spanish_lines('x = "Elige una opción"\n'))
        self.assertTrue(python_spanish_lines('# los sprites de la pistola\n'))
        # ...and the CEO's quoted words pass, glossed or restated.
        for prose in ('The CEO: «las doy por buenas» ("I take them as good").',
                      'CEO verdict: "Ok consorcio, añade paleta si es\nnecesario" (D128).',
                      '“también las recomendadas”'):
            self.assertEqual(spanish_lines(prose_unquoted(prose)), [], prose)
        self.assertEqual(spanish_lines(html_unquoted(
            '<p>Your note: "ponle la bandera más grande"</p>'
            '<script>const N = "the CEO: \\"muy macarra\\"";</script>'
            '<img src="data:image/png;base64,ZXN0w6EgbG9zIGxhcw==">')), [])
        self.assertEqual(python_spanish_lines(
            'NOTE = ("the CEO, \\"rehaz los sprites de la pistola "\n'
            '        "también\\" (redo the pistol too)")\n'
            '# D82 ("también las recomendadas")\n'), [])


# --- the docs and the sheet generators: what lies outside quotation marks ---

DOCS_DIR = PROJECT_ROOT / "docs"
RU_MIRROR = DOCS_DIR / "ru"
DOC_SUFFIXES = (".md", ".html", ".txt")
GENERATOR_DIRS = (TOOLS_DIR, TOOLS_DIR / "art", TOOLS_DIR / "audio")
# A name, not Spanish text: the hard skill (D20), the Republican slogan.
NAMES = re.compile(r"no pasar[aá]n", re.IGNORECASE)
# Python files whose named top-level assignment holds history, not output.
HISTORICAL_PY = {"tools/art/walk_stride.py": "SPEC_EDITS"}

QUOTATION = re.compile(r"«[^«»]{0,1500}»|“[^“”]{0,1500}”|\"[^\"]{0,1500}\"", re.S)
SCRIPT_QUOTATION = re.compile(
    r"«[^«»]{0,1500}»|“[^“”]{0,1500}”|\\\"(?:[^\"\\]|\\[^\"]){0,1500}\\\"|&quot;.{0,1500}?&quot;", re.S)
DATA_URI = re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+")
SEPARATOR = "\x00"


def _blank(match: re.Match) -> str:
    """The match as spaces, keeping its line breaks (and separators)."""
    return re.sub(r"[^\n\x00]", " ", match.group(0))


def prose_unquoted(text: str) -> str:
    """Prose with every quotation blanked; line numbers kept."""
    return QUOTATION.sub(_blank, NAMES.sub("", text))


def html_unquoted(text: str) -> str:
    """An HTML sheet's visible text and script text, quotations blanked."""
    text = DATA_URI.sub("", NAMES.sub("", text))
    text = re.sub(r"<style.*?</style>", _blank, text, flags=re.S | re.I)
    out, pos = [], 0
    for m in re.finditer(r"<script[^>]*>(.*?)</script>", text, re.S | re.I):
        out.append(prose_unquoted(re.sub(r"<[^>]*>", _blank, text[pos:m.start(1)])))
        out.append(SCRIPT_QUOTATION.sub(_blank, m.group(1)))
        pos = m.end(1)
    out.append(prose_unquoted(re.sub(r"<[^>]*>", _blank, text[pos:])))
    return "".join(out)


def _python_pieces(src: str, historical: str | None):
    """(line, text) of a Python file's comments, and of its string literals."""
    import ast
    import tokenize
    skip = range(0)
    if historical:
        for node in ast.parse(src).body:
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == historical for t in node.targets):
                skip = range(node.lineno, node.end_lineno + 1)
    comments, strings = [], []
    middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.start[0] in skip:
            continue
        if tok.type == tokenize.COMMENT:
            comments.append((tok.start[0], tok.string[1:]))
        elif tok.type == tokenize.STRING:
            try:
                value = ast.literal_eval(tok.string)
            except (ValueError, SyntaxError):
                value = tok.string
            if isinstance(value, str):
                strings.append((tok.start[0], value))
        elif middle is not None and tok.type == middle:
            strings.append((tok.start[0], tok.string))
    return comments, strings


def python_spanish_lines(src: str, historical: str | None = None) -> list[str]:
    """Spanish in a Python file's comments and strings, outside quotations.
    Quotations may run across adjacent literals or comment lines, so each
    kind is read as one stream."""
    found = []
    for pieces in _python_pieces(src, historical):
        joined = prose_unquoted(SEPARATOR.join(text for _, text in pieces))
        for (line, _), text in zip(pieces, joined.split(SEPARATOR)):
            for offset, part in enumerate(text.split("\n")):
                hits = [m.group(0) for m in SPANISH_TEXT.finditer(part)]
                if hits:
                    found.append(f"{line + offset}: {hits} {part.strip()[:120]}")
    return found


def doc_files() -> list[Path]:
    return sorted(p for p in DOCS_DIR.rglob("*")
                  if p.is_file() and p.suffix in DOC_SUFFIXES and RU_MIRROR not in p.parents)


def generator_files() -> list[Path]:
    files = [p for d in GENERATOR_DIRS for p in d.glob("*.py")]
    files += (TOOLS_DIR / "art").glob("*.html")
    return sorted(files)


if __name__ == "__main__":
    unittest.main()
