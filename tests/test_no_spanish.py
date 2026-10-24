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
  * no file the release or a portable package ships has a Spanish name.

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
PENDING = (
    # docs/art/LICENSES.md, the Episode 3 music rows (D113): their Origin cell
    # quotes the CEO, and CREDITS.txt quotes the Origin cell.
    '"las doy por buenas"',
)


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


if __name__ == "__main__":
    unittest.main()
