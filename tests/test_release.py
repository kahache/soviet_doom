"""Tests for tools/release.py, the G6 distribution zip (docs/engine/RELEASE.md).

What is pinned:

  * the real release, made twice into temp dirs (`dist/` is never touched):
    the exact member list, the PK3 inside it, LICENSE.md verbatim, the
    generated CREDITS.txt and README.txt, SHA256SUMS, the .sha256 beside it;
  * the full licence texts (GPL-3.0, CC BY-NC-SA 4.0, Freedoom's BSD-3
    notice): byte for byte the repo files, whose SHA-256 is the published
    text's, named by LICENSE.md, README.txt and CREDITS.txt, and an edited or
    missing text refused before anything is built;
  * CREDITS.txt for a player without the repo (backlog G9): no repo path in
    its headings or its own sentences, the AI disclosure (D75) in English
    and Russian;
  * the player readme (fast tier, no build): the three campaign maps in
    MAPINFO order and the practice range in English and Russian, every name
    read from LANGUAGE, GZDoom 4.14.2's default keys (Space jumps, E uses,
    no Ctrl, no arrows), "choose Freedoom: Phase 2", launch lines for
    Windows, PowerShell, macOS and Linux, the hash check for each, no file
    or repo path the player does not have, no "draft" in shipped text;
  * nothing from work/, tools/, previews or any IWAD in the zip or the PK3;
  * determinism: same commit, same bytes, every timestamp the commit's;
  * the refusals: no --version, a bad version, a dirty tree, an asset with no
    licence row, an attribution the credits do not carry, a row that needs a
    credit and names nobody, music not cleared in MUSIC-RIGHTS 4.5, an IWAD
    smuggled into the PK3 - each with fake registers or a fake PK3, and on a
    refusal nothing is written.

The real runs use --allow-dirty (the tree is rarely clean while agents
work); the dirty refusal is tested with a stubbed git state.

Run:  python3 -m unittest tests.test_release -v
"""

from __future__ import annotations

import hashlib
import io
import re
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import licences  # noqa: E402
import release  # noqa: E402

VERSION = "0.0-test"
FOLDER = f"{release.MOD_NAME}-{VERSION}"

# The full licence texts (backlog N10) and the SHA-256 of the bytes their
# publishers served when the PM downloaded them on 2026-10-14 (Freedoom's
# notice on 2026-10-15, D75: v0.13.0's COPYING.adoc). Written here by hand,
# not read from release.py: an edit to a text AND to the tool's pin still
# fails here.
GPL_TEXT = "LICENSE-GPL-3.0.txt"
CC_TEXT = "LICENSE-CC-BY-NC-SA-4.0.txt"
FREEDOOM_TEXT = "LICENSE-FREEDOOM-BSD-3.txt"
PUBLISHED_SHA256 = {
    GPL_TEXT: "3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986",
    CC_TEXT: "e66c269d4819aaab34b49ef5220c4ddab6756f21bb5180761a4eb8561f2b7bbd",
    FREEDOOM_TEXT: "ed60abcf1ff64bf61bf8b4c585ab63643d655a21f8997ba284c01f94ed681fc5",
}
PUBLISHED_URL = {
    GPL_TEXT: "https://www.gnu.org/licenses/gpl-3.0.txt",
    CC_TEXT: "https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt",
    FREEDOOM_TEXT: "https://raw.githubusercontent.com/freedoom/freedoom/v0.13.0/COPYING.adoc",
}
FULL_TEXTS = tuple(PUBLISHED_SHA256)

# What a player without the repo cannot open: CREDITS.txt's headings and its
# own sentences must not send him there (G6 review 2.2, backlog G9).
REPO_ONLY = ("docs/", "tools/", "tests/", "src/", "work/", "dist/", "iwads/",
             "LICENSES.md", "MUSIC-RIGHTS", "RELEASE.md", "release.py")

# D75: the credits say which references were generated with AI; D79: and
# name Google Gemini, whose images the weapon frames are derived from; D93:
# and every AI tool the game was made with, in both halves of CREDITS.txt and
# README.txt.
AI_WORDS = {"default": ("AI", "Google Gemini", "Fooocus / SDXL", "hands", "pixel art", "not distributed",
                        "Freedoom's voices", "into Russian and Catalan"),
            "ru": ("ИИ", "Google Gemini", "Fooocus / SDXL", "рук", "пиксель-арт", "не распространяются",
                   "голосами Freedoom", "на русский и каталанский")}
# README.txt's "Made with" names the AI tools and the non-AI foundations.
MADE_WITH_WORDS = ("GZDoom", "Freedoom", "Kenney", "rubberduck", "Darsycho", "OpenGameArt",
                   "Jerry Engelbach", "Peter Gerloff", "Python", "Pillow", "CREDITS.txt")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_bytes(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buffer.getvalue()


# --- The real release -----------------------------------------------------------

class RealReleaseTest(unittest.TestCase):
    """The package as it would ship today, built twice."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sd-test-release-")
        root = Path(cls._tmp.name)
        cls.first = release.make_release(release.Config(VERSION, root / "a", allow_dirty=True))
        cls.second = release.make_release(release.Config(VERSION, root / "b", allow_dirty=True))
        cls.data = cls.first.zip_path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(cls.data)) as zf:
            cls.infos = zf.infolist()
            cls.files = {i.filename.split("/", 1)[1]: zf.read(i) for i in cls.infos}
        cls.pk3 = cls.files[release.PK3_NAME]
        with zipfile.ZipFile(io.BytesIO(cls.pk3)) as zf:
            cls.pk3_names = zf.namelist()
            cls.language = zf.read("LANGUAGE").decode("utf-8")
        cls.credits = cls.files[release.CREDITS_NAME].decode("utf-8")
        cls.readme = cls.files[release.README_NAME].decode("utf-8")
        # What the AI lines may claim, read as make_release reads it.
        cls.ships = release.ai_ships(release.check_licences(
            cls.pk3_names,
            release.parse_licence_register(release.DEFAULT_LICENSES.read_text(encoding="utf-8")),
            release.parse_music_register(release.DEFAULT_MUSIC_RIGHTS.read_text(encoding="utf-8")),
            release.parse_credit_lines(cls.language)))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_the_zip_is_named_after_the_version_in_its_folder(self):
        self.assertEqual(self.first.zip_path.name, f"{FOLDER}.zip")
        self.assertEqual(self.first.zip_path.parent.name, "a")

    def test_the_zip_holds_exactly_the_eight_files_in_one_folder(self):
        self.assertEqual([i.filename for i in self.infos],
                         [f"{FOLDER}/{name}" for name in sorted(release.RELEASE_FILES)])
        self.assertEqual(sorted(self.files),
                         sorted(["sovietdoom.pk3", "LICENSE.md", "CREDITS.txt", "README.txt",
                                 "SHA256SUMS", GPL_TEXT, CC_TEXT, FREEDOOM_TEXT]))

    def test_the_full_licence_texts_are_the_repo_files_byte_for_byte(self):
        for name in FULL_TEXTS:
            with self.subTest(name=name):
                repo = (PROJECT_ROOT / name).read_bytes()
                # The texts hold no CR; a CRLF checkout (autocrlf, no
                # .gitattributes) is turned back into the bytes git stores.
                self.assertEqual(self.files[name], repo.replace(b"\r\n", b"\n"))
                self.assertEqual(sha(self.files[name]), PUBLISHED_SHA256[name])

    def test_the_readme_and_credits_name_the_full_texts(self):
        for name in FULL_TEXTS:
            self.assertIn(name, self.readme)
            self.assertIn(name, self.credits)

    def test_the_freedoom_notice_ships_because_freedoom_material_does(self):
        """BSD-3 clause 2 (D75): what the PK3 derives from Freedoom carries
        the notice with it, verbatim. Until D123 that was the TT-33's hands;
        since D123 (the Gemini TT-33) it is the three enemy gib sounds that
        edit Freedoom's DSSLOP (docs/art/LICENSES.md, "Base IWAD")."""
        for gib in ("SDRRIXDT", "SDLTRXDT", "SDSTOXDT"):
            self.assertTrue(any(n.startswith("sounds/") and f"/{gib}." in n for n in self.pk3_names), gib)
        self.assertIn(b"Contributors to the Freedoom project", self.files[FREEDOOM_TEXT])

    def test_credits_name_no_repo_path_outside_the_quoted_registers(self):
        """Headings and the tool's own sentences: every line but the quoted
        register cells (an asset's Origin, Licence and Obligation) and the
        in-game lines."""
        own = [line for line in self.credits.splitlines()
               if not line.startswith(("* ", "  "))]
        for line in own:
            for repo_only in REPO_ONLY:
                self.assertNotIn(repo_only, line)

    def test_credits_carry_the_ai_disclosure_in_both_languages(self):
        english, russian = self.credits.split(release.CREDITS_HEADINGS["screen_ru"])
        ships = self.ships
        for half, lang in ((english, "default"), (russian, "ru")):
            flat = release.normalise(half)
            for paragraph in release.ai_disclosure(lang, ships):
                self.assertIn(release.normalise(paragraph), flat)
            for word in release.AI_TOOLS:
                self.assertIn(word, flat, f"[{lang}]")

    def test_the_ai_claims_follow_what_the_package_packs(self):
        """The face line appears once our STF* lumps are packed, the voices
        line flips once a packed sound's register row names Chatterbox."""
        face = any(release.FACE_LUMP_RE.match(Path(n).stem) for n in self.pk3_names)
        for text in (self.credits, self.readme):
            self.assertEqual("sergeant's face" in text, face)
            self.assertEqual("speak with Freedoom's voices" in release.normalise(text),
                             not self.ships.voices)

    def test_the_readme_says_what_the_game_was_made_with(self):
        en, ru = self.readme.split(README_RULE)
        for half, lang in ((en, "default"), (ru, "ru")):
            self.assertIn(release.render_made_with(lang, self.ships), half)

    def test_the_pk3_is_a_full_build(self):
        for lump in ("MAPINFO", "LANGUAGE", "zscript.txt", "maps/MAP01.wad", "maps/RANGE.wad"):
            self.assertIn(lump, self.pk3_names)
        self.assertTrue(any(n.startswith("textures/") for n in self.pk3_names))

    def test_licence_is_the_repo_file_verbatim(self):
        self.assertEqual(self.files[release.LICENCE_NAME],
                         (PROJECT_ROOT / "LICENSE.md").read_text(encoding="utf-8").encode("utf-8"))

    def test_sha256sums_lists_the_six_other_files_correctly(self):
        lines = self.files[release.SUMS_NAME].decode("ascii").splitlines()
        listed = {}
        for line in lines:
            match = re.fullmatch(r"([0-9a-f]{64})  (\S+)", line)
            self.assertIsNotNone(match, f"not sha256sum format: {line!r}")
            listed[match.group(2)] = match.group(1)
        self.assertEqual(sorted(listed), sorted(n for n in release.RELEASE_FILES
                                                if n != release.SUMS_NAME))
        for name, digest in listed.items():
            self.assertEqual(digest, sha(self.files[name]), name)

    def test_the_sha256_file_beside_the_zip_matches(self):
        self.assertEqual(self.first.sha_path.read_text(encoding="ascii"),
                         f"{sha(self.data)}  {FOLDER}.zip\n")

    def test_nothing_from_work_tools_previews_or_an_iwad(self):
        names = [i.filename for i in self.infos] + self.pk3_names
        for name in names:
            parts = [p.lower() for p in name.split("/")[:-1]]
            for banned in ("work", "tools", "tests", "iwads", "previews", "logs"):
                self.assertNotIn(banned, parts, name)
            self.assertNotIn("preview", name.lower())
        self.assertFalse(any(i.filename.lower().endswith(".wad") for i in self.infos))
        # Freedoom's licence notice is the one Freedoom file that ships (D75);
        # nothing else of Freedoom's is named in the zip or the PK3.
        self.assertFalse(any("freedoom" in n.lower() for n in names
                             if n != f"{FOLDER}/{FREEDOOM_TEXT}"))
        with zipfile.ZipFile(io.BytesIO(self.pk3)) as zf:
            for name in zf.namelist():
                self.assertNotEqual(zf.read(name)[:4], b"IWAD", f"{name} is an IWAD")
        self.assertEqual(release.guard_pk3(self.pk3), [])

    def test_two_runs_give_the_same_bytes(self):
        self.assertEqual(self.data, self.second.zip_path.read_bytes())
        self.assertEqual(self.first.sha_path.read_bytes(), self.second.sha_path.read_bytes())

    def test_every_timestamp_is_the_commits_and_attributes_are_fixed(self):
        stamp = release.zip_time(release.git_state(PROJECT_ROOT).commit_time)
        for info in self.infos:
            self.assertEqual(info.date_time, stamp, info.filename)
            self.assertEqual(info.create_system, release.ZIP_CREATE_SYSTEM_UNIX)
            self.assertEqual(info.external_attr >> 16, release.ZIP_FILE_MODE)

    def test_credits_carry_the_in_game_credits_in_every_language(self):
        credits = release.parse_credit_lines(self.language)
        for lang in (release.LANG_ENGLISH, release.LANG_RUSSIAN, release.LANG_CATALAN):
            self.assertTrue(credits[lang], f"no SD_CRED_* in [{lang}]")
            for ident, text in credits[lang]:
                if ident != release.CREDIT_TITLE_ID:
                    self.assertIn(text if not ident.startswith(release.CREDIT_HEADER_MARK)
                                  else text.upper(), self.credits, f"[{lang}] {ident}")

    def test_credits_carry_the_music_lines_verbatim(self):
        rights = (PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md").read_text(encoding="utf-8")
        lines = release.verbatim_music_lines(rights)
        self.assertTrue(any("Jerry Engelbach" in line for line in lines))
        flat = release.normalise(self.credits)
        for line in lines:
            self.assertIn(line, flat)

    def test_credits_list_every_packed_asset(self):
        for path in release.asset_paths(self.pk3_names):
            folder = path.rsplit("/", 1)[0] + "/ ("
            self.assertTrue(path in self.credits or folder in self.credits, path)

    def test_readme_is_english_and_russian_and_says_how_to_play(self):
        for needle in ("GZDoom", "freedoom2.wad", "gzdoom -iwad freedoom2.wad -file sovietdoom.pk3",
                       "NOT in this package", "НЕТ", release.GZDOOM_MINIMUM, "CREDITS.txt",
                       "LICENSE.md", "СОВЕТСКИЙ DOOM", "W A S D", "not affiliated with id Software"):
            self.assertIn(needle, self.readme)
        strings = release.language_strings(self.language)
        self.assertIn(strings["default"]["SD_MAP01_NAME"], self.readme)
        self.assertIn(strings["ru"]["SD_MAP01_NAME"], self.readme)

    def test_the_real_registers_cover_the_real_pk3(self):
        rows = release.parse_licence_register(
            (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8"))
        music = release.parse_music_register(
            (PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md").read_text(encoding="utf-8"))
        check = release.check_licences(self.pk3_names, rows, music,
                                       release.parse_credit_lines(self.language))
        self.assertEqual(check.errors, [])
        needed = {n for row, _ in check.coverage for n in row.required}
        self.assertIn("Jerry Engelbach", needed, "the register reader lost the Engelbach row")


# --- The player readme (no build: these run at the fast tier) ---------------------

README_RULE = "-" * 76


class ReadmeTest(unittest.TestCase):
    """README.txt as render_readme writes it from the repo's LANGUAGE lump
    (the G6 review, docs/qa/2026-10-14_2356_G6-readiness.md §2.4 and §5):
    the three-map campaign and the range, GZDoom 4.14.2's default keys,
    Freedoom: Phase 2, launch and hash-check lines for every system, and
    nothing a player without the repo cannot open."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.language = (PROJECT_ROOT / "src" / "lumps" / "LANGUAGE").read_text(encoding="utf-8")
        cls.strings = release.language_strings(cls.language)
        cls.en_names = cls.strings[release.LANG_ENGLISH]
        cls.ru_names = cls.strings[release.LANG_RUSSIAN]
        cls.readme = release.render_readme("1.0", "0123456789ab", cls.strings)
        cls.en, cls.ru = cls.readme.split(README_RULE)

    def _line(self, half: str, label: str) -> str:
        found = [line for line in half.splitlines() if line.strip().startswith(label + " ..")]
        self.assertEqual(len(found), 1, f"one controls line {label!r}")
        return found[0]

    def test_the_campaign_is_three_maps_in_order_in_both_languages(self):
        for half, names in ((self.en, self.en_names), (self.ru, self.ru_names)):
            with self.subTest(lang="ru" if half is self.ru else "en"):
                for number in (1, 2, 3):
                    self.assertRegex(half, rf"\n    {number}\. {re.escape(names[f'SD_MAP0{number}_NAME'])}")
                self.assertIn(names["SD_EP01_NAME"], half)
        self.assertIn("three maps played in order", self.en)
        self.assertIn("три карты", self.ru)
        self.assertIn("Tankograd", self.en)
        self.assertIn("Танкоград", self.ru)

    def test_the_readme_follows_the_mapinfo_chain(self):
        # The order the readme prints is the order MAPINFO plays.
        mapinfo = (PROJECT_ROOT / "src" / "lumps" / "MAPINFO").read_text(encoding="utf-8")
        chain: dict[str, str] = {}
        current = None
        for raw in mapinfo.splitlines():
            line = raw.split("//", 1)[0].strip()
            head = re.match(r"map (\w+) ", line)
            if head:
                current = head.group(1)
            nxt = re.fullmatch(r'next = "?(\w+)"?', line)
            if nxt and current:
                chain.setdefault(current, nxt.group(1))
        self.assertEqual([chain["MAP01"], chain["MAP02"], chain["MAP03"]],
                         ["MAP02", "MAP03", "endtitle"])

    def test_the_practice_range_and_the_new_game_paths(self):
        for half, names, newgame in ((self.en, self.en_names, "New Game"),
                                     (self.ru, self.ru_names, "Новая игра")):
            self.assertIn(f"({newgame} > {names['SD_EP01_NAME']})", half)
            self.assertIn(f"({newgame} > {names['SD_EP02_NAME']})", half)

    def test_every_quoted_name_comes_from_language_in_its_own_half(self):
        for key, ident in release.README_IDS.items():
            for half, names in ((self.en, self.en_names), (self.ru, self.ru_names)):
                value = names[ident]
                if value.isupper():
                    value = (value.title() if half is self.en else value.capitalize())
                self.assertIn(value, half, f"{ident} ({key})")

    def test_the_controls_are_gzdooms_default_bindings(self):
        # GZDoom 4.14.2, engine/commonbinds.txt + engine/defbinds.txt (G6
        # review §3.2): Space jumps, E uses, Ctrl and the arrows are unbound.
        move, fire = self._line(self.en, "Move"), self._line(self.en, "Fire")
        use, jump = self._line(self.en, "Use"), self._line(self.en, "Jump")
        self.assertIn("W A S D", move)
        self.assertNotIn("arrow", move)
        self.assertIn("left mouse button", fire)
        self.assertNotIn("Ctrl", fire)
        self.assertIn("E:", use)
        self.assertNotIn("Space", use)
        self.assertIn("Space", jump)
        for label, keys in (("Weapons", "1 to 7"), ("Automap", "Tab"), ("Menu", "Esc"),
                            ("Run", "Shift"), ("Save / load", "F2 / F3")):
            self.assertIn(keys, self._line(self.en, label))
        self.assertNotIn("arrow", self.en)
        self.assertNotIn("Ctrl", self.en)

        move, fire = self._line(self.ru, "Движение"), self._line(self.ru, "Огонь")
        use, jump = self._line(self.ru, "Действие"), self._line(self.ru, "Прыжок")
        self.assertIn("W A S D", move)
        self.assertNotIn("стрелк", move)
        self.assertNotIn("Ctrl", fire)
        self.assertIn("E:", use)
        self.assertNotIn("пробел", use)
        self.assertIn("пробел", jump)
        self.assertNotIn("стрелк", self.ru)
        self.assertNotIn("Ctrl", self.ru)

    def test_it_says_to_pick_phase_2_not_phase_1(self):
        self.assertIn("choose Freedoom: Phase 2", self.en)
        self.assertIn("выберите Freedoom: Phase 2", self.ru)
        for half in (self.en, self.ru):
            self.assertIn("freedoom1.wad", half)
            self.assertIn("freedoom2.wad", half)

    def test_launch_lines_for_windows_powershell_macos_and_linux(self):
        for half in (self.en, self.ru):
            self.assertIn("gzdoom -iwad freedoom2.wad -file sovietdoom.pk3", half)
            self.assertIn(".\\gzdoom", half)
            self.assertIn("GZDoom.app/Contents/MacOS/gzdoom", half)
            self.assertIn("Linux", half)

    def test_hash_check_lines_for_every_system(self):
        for half in (self.en, self.ru):
            for command in ("sha256sum -c SHA256SUMS", "shasum -a 256 -c SHA256SUMS",
                            "Get-FileHash sovietdoom.pk3",
                            "certutil -hashfile sovietdoom.pk3 SHA256"):
                self.assertIn(command, half)

    def test_made_with_names_every_ai_tool_and_foundation_in_both_halves(self):
        self.assertIn("\nMADE WITH\n", self.en)
        self.assertIn("\nЧЕМ СДЕЛАНО\n", self.ru)
        for half in (self.en, self.ru):
            flat = release.normalise(half)
            for word in release.AI_TOOLS + MADE_WITH_WORDS:
                self.assertIn(word, flat)
        self.assertIn("Freedoom's voices", release.normalise(self.en))
        self.assertIn("голосами Freedoom", release.normalise(self.ru))

    def test_it_names_the_three_languages(self):
        """P6: Catalan is the third language, in the list and in the menu path."""
        self.assertIn("English, Russian and Catalan, switched inside the game.", self.en)
        self.assertIn("Три языка: английский, русский и каталанский", self.ru)
        self.assertIn(f"{self.en_names['SD_LANGVAL_RU']} or {self.en_names['SD_LANGVAL_CA']}.",
                      self.en)
        self.assertIn(f"{self.ru_names['SD_LANGVAL_RU']} или {self.ru_names['SD_LANGVAL_CA']}.",
                      self.ru)
        self.assertIn("the Russian and Catalan text", release.normalise(self.en))
        self.assertIn("русский и каталанский тексты", release.normalise(self.ru))

    def test_made_with_follows_what_ships(self):
        face_voices = release.render_readme("1.0", "0123456789ab", self.strings,
                                            release.AiShips(face=True, voices=True))
        en, ru = face_voices.split(README_RULE)
        self.assertIn("the sergeant's face", release.normalise(en))
        self.assertIn("лицо сержанта", release.normalise(ru))
        self.assertIn("some enemy voice lines", en)
        self.assertNotIn("Freedoom's voices", release.normalise(en))
        self.assertNotIn("голосами Freedoom", release.normalise(ru))
        self.assertNotIn("sergeant's face", self.readme)
        for line in face_voices.splitlines():
            self.assertLessEqual(len(line), 78, line)

    def test_it_names_no_file_the_player_does_not_have(self):
        shipped = set(release.RELEASE_FILES) | {"freedoom1.wad", "freedoom2.wad", "gzdoom.exe"}
        named = set(re.findall(r"[\w.-]+\.(?:md|txt|pk3|wad|py|sh|exe|png|zip)\b", self.readme))
        self.assertEqual(named - shipped, set())
        for repo_only in ("docs/", "tools/", "src/", "assets/", "tests/", "work/", "dist/",
                          "iwads/", "LICENSES.md", "MUSIC-RIGHTS", "RELEASE.md"):
            self.assertNotIn(repo_only, self.readme)

    def test_nothing_shipped_is_marked_as_a_draft(self):
        for word in ("draft", "черновик", "NOT VERIFIED", "TODO"):
            self.assertNotIn(word.lower(), self.readme.lower())

    def test_lines_fit_a_plain_text_window(self):
        for line in self.readme.splitlines():
            self.assertLessEqual(len(line), 78, line)

    def test_a_missing_quoted_id_refuses(self):
        strings = {lang: dict(names) for lang, names in self.strings.items()}
        del strings[release.LANG_RUSSIAN]["SD_MAP03_NAME"]
        with self.assertRaises(release.ReleaseError) as caught:
            release.render_readme("1.0", "0123456789ab", strings)
        self.assertIn("SD_MAP03_NAME", str(caught.exception))


# --- The full licence texts (no build: these run at the fast tier) ----------------

class LicenceTextTest(unittest.TestCase):
    """LICENSE-GPL-3.0.txt, LICENSE-CC-BY-NC-SA-4.0.txt and
    LICENSE-FREEDOOM-BSD-3.txt: in the repo, unedited, pinned in the tool,
    named by LICENSE.md, and refused when missing or touched."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sd-test-release-")
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_the_repo_texts_are_the_published_texts(self):
        for name, digest in PUBLISHED_SHA256.items():
            with self.subTest(name=name):
                data = (PROJECT_ROOT / name).read_bytes()
                self.assertEqual(sha(data.replace(b"\r\n", b"\n")), digest,
                                 f"{name} was edited; restore it from git")
                self.assertNotIn(b"\r", data.replace(b"\r\n", b""), f"{name}: a lone CR")

    def test_the_tool_pins_the_same_texts_hashes_and_sources(self):
        pinned = {t.name: (t.sha256, t.url) for t in release.LICENCE_TEXTS}
        self.assertEqual(pinned, {n: (PUBLISHED_SHA256[n], PUBLISHED_URL[n])
                                  for n in PUBLISHED_SHA256})
        for name in PUBLISHED_SHA256:
            self.assertIn(name, release.RELEASE_FILES)

    def test_a_crlf_checkout_still_gives_the_published_bytes(self):
        for text in release.LICENCE_TEXTS:
            original = (PROJECT_ROOT / text.name).read_bytes().replace(b"\r\n", b"\n")
            (self.root / text.name).write_bytes(original.replace(b"\n", b"\r\n"))
            self.assertEqual(release.read_licence_text(self.root, text), original)

    def test_an_edited_or_missing_text_is_refused(self):
        gpl = next(t for t in release.LICENCE_TEXTS if t.name == GPL_TEXT)
        with self.assertRaises(release.ReleaseError) as caught:
            release.read_licence_text(self.root, gpl)
        self.assertIn("not found", str(caught.exception))
        original = (PROJECT_ROOT / GPL_TEXT).read_bytes().replace(b"\r\n", b"\n")
        for edited in (original + b"\n", original.replace(b"GNU", b"GNU's", 1),
                       original[:-100], original.replace(b"\n", b"\n ", 1)):
            (self.root / GPL_TEXT).write_bytes(edited)
            with self.subTest(size=len(edited)), self.assertRaises(release.ReleaseError) as caught:
                release.read_licence_text(self.root, gpl)
            self.assertIn("never edit it", str(caught.exception))
            self.assertIn(gpl.url, str(caught.exception))

    def test_make_release_refuses_an_edited_text_before_building(self):
        for text in release.LICENCE_TEXTS:
            (self.root / text.name).write_bytes((PROJECT_ROOT / text.name).read_bytes())
        (self.root / CC_TEXT).write_bytes(b"not the licence\n")
        config = release.Config(VERSION, self.root / "out", allow_dirty=True,
                                licence_texts_dir=self.root)
        with mock.patch.object(release, "build_pk3") as build:
            with self.assertRaises(release.ReleaseError) as caught:
                release.make_release(config)
        build.assert_not_called()
        self.assertIn(CC_TEXT, str(caught.exception))
        self.assertFalse(config.out_dir.exists())

    def test_licence_md_points_to_both_texts_and_says_what_each_covers(self):
        text = (PROJECT_ROOT / "LICENSE.md").read_text(encoding="utf-8")
        self.assertNotIn("will be added", text)
        self.assertNotIn("будут добавлены", text)
        english = text.split("\n---\n", 1)[0]
        for name in FULL_TEXTS:
            self.assertIn(name, english)
            self.assertIn(PUBLISHED_URL[name], english)
        # Each file named in the bullet that says what it covers (D15).
        bullets = [b for b in re.split(r"\n- ", english) if "LICENSE-" in b]
        self.assertTrue(any(GPL_TEXT in b and "**code**" in b and CC_TEXT not in b
                            for b in bullets), bullets)
        self.assertTrue(any(CC_TEXT in b and "**assets and documentation**" in b
                            and GPL_TEXT not in b for b in bullets), bullets)
        self.assertTrue(any(FREEDOOM_TEXT in b and "**Freedoom-derived material**" in b
                            and GPL_TEXT not in b and CC_TEXT not in b for b in bullets), bullets)
        russian = text.split("\n---\n", 1)[1]
        for name in FULL_TEXTS:
            self.assertIn(name, russian)

    def test_licence_md_reads_right_inside_the_package(self):
        """G6 review 2.2 (backlog G9): the player's copy has no docs/, so it
        says CREDITS.txt reproduces the registers; it credits no pack the
        game does not use (OTEX: none used, docs/art/LICENSES.md); and the
        Russian half names the same third parties as the English."""
        text = (PROJECT_ROOT / "LICENSE.md").read_text(encoding="utf-8")
        english, russian = text.split("\n---\n", 1)
        self.assertRegex(release.normalise(english), r"release package.*CREDITS\.txt`? reproduces")
        self.assertIn("CREDITS.txt", russian)
        self.assertNotIn("OTEX", text)
        # D123: the Freedoom-derived material is the DSSLOP gibs; the TT-33
        # is named only as history (its hands are ours since D123).
        for half in (english, russian):
            for name in ("Freedoom", "BSD", "Jerry Engelbach", FREEDOOM_TEXT, "DSSLOP", "D123"):
                self.assertIn(name, half)
        self.assertNotIn("today the TT-33", english)
        self.assertNotIn("сейчас — руки с ТТ-33", russian)

    def test_no_otex_texture_is_packed(self):
        """Why LICENSE.md may drop OTEX: no source lump or asset names it."""
        for folder in ("src", "assets"):
            for path in (PROJECT_ROOT / folder).rglob("*"):
                self.assertNotIn("otex", path.name.lower(), path)
                if path.is_file() and path.suffix.lower() in ("", ".txt", ".py", ".zs", ".json"):
                    body = path.read_text(encoding="utf-8", errors="replace").lower()
                    self.assertNotIn("otex", body, path)


# --- CREDITS.txt (no build: these run at the fast tier) ---------------------------

class CreditsTextTest(unittest.TestCase):
    """CREDITS.txt as render_credits writes it from the repo's LANGUAGE lump
    and a one-row licence check: what a player without the repo reads."""

    @classmethod
    def setUpClass(cls) -> None:
        language = (PROJECT_ROOT / "src" / "lumps" / "LANGUAGE").read_text(encoding="utf-8")
        cls.credits_lines = release.parse_credit_lines(language)
        row = release.parse_licence_register(
            "| Lump | Origin | Licence |\n|---|---|---|\n"
            "| `SDTTA0` | (a) `tools/art/hand_study.py`, Freedoom's PISGA0 recoloured "
            "| modified BSD licence, credit \"Freedoom\" |\n")[0]
        check = release.LicenceCheck(coverage=[(row, ["sprites/tt33/SDTTA0.png"])])
        cls.text = release.render_credits("1.0", "0123456789ab", cls.credits_lines,
                                          ["Music line, verbatim."], check)
        cls.lines = cls.text.splitlines()

    def test_the_headings_name_no_repo_path(self):
        for heading in release.CREDITS_HEADINGS.values():
            self.assertIn(heading, self.lines)
        # Every underlined line is a heading, whatever the dictionary says.
        underlined = [self.lines[k - 1] for k, line in enumerate(self.lines)
                      if k and line and set(line) <= {"-", "="}
                      and len(line) == len(self.lines[k - 1])]
        self.assertGreaterEqual(len(underlined), len(release.CREDITS_HEADINGS))
        for heading in underlined:
            for repo_only in REPO_ONLY:
                self.assertNotIn(repo_only, heading)

    def test_the_tools_own_sentences_name_no_repo_path(self):
        own = [line for line in self.lines if not line.startswith(("* ", "    "))]
        own = [line for line in own if not any(line == "  " + text
                                               for lang in self.credits_lines.values()
                                               for _, text in lang)]
        for line in own:
            for repo_only in REPO_ONLY:
                self.assertNotIn(repo_only, line)
        self.assertNotIn("(MUSIC-RIGHTS", self.text)

    def test_the_quoted_register_cell_is_kept(self):
        """Provenance is the register's: an Origin cell may name its
        generator, and CREDITS.txt quotes it, it does not edit it."""
        self.assertIn("Origin: (a) tools/art/hand_study.py", self.text)

    def test_the_ai_disclosure_is_in_each_language_half(self):
        english, russian = self.text.split(release.CREDITS_HEADINGS["screen_ru"])
        self.assertIn(release.CREDITS_HEADINGS["ai_en"], english)
        self.assertIn(release.CREDITS_HEADINGS["ai_ru"], russian)
        for half, lang in ((english, "default"), (russian, "ru")):
            flat = release.normalise(half)
            for paragraph in release.ai_disclosure(lang):
                self.assertIn(release.normalise(paragraph), flat)
            for word in AI_WORDS[lang] + release.AI_TOOLS:
                self.assertIn(word, flat, f"[{lang}]")

    def test_the_catalan_screen_closes_the_file(self):
        """P6: the [ca] credits screen as the game shows it, after the
        Russian half; a LANGUAGE without [ca] gets no Catalan heading."""
        heading = release.CREDITS_HEADINGS["screen_ca"]
        before, catalan = self.text.split(heading)
        self.assertIn(release.CREDITS_HEADINGS["ai_ru"], before)
        self.assertNotIn(release.CREDITS_HEADINGS["ai_en"], catalan)
        for ident, text in self.credits_lines[release.LANG_CATALAN]:
            if ident != release.CREDIT_TITLE_ID:
                self.assertIn(text.upper() if ident.startswith(release.CREDIT_HEADER_MARK)
                              else "  " + text, catalan, ident)
        self.assertIn("els textos en rus i català", catalan)
        without = {lang: lines for lang, lines in self.credits_lines.items()
                   if lang != release.LANG_CATALAN}
        check = release.LicenceCheck(coverage=[])
        self.assertNotIn(heading, release.render_credits("1.0", "0123456789ab", without, [], check))

    def test_the_ai_text_names_no_repo_path(self):
        every = [release.ai_disclosure(lang, release.AiShips(face, voices))
                 for lang in ("default", "ru") for face in (False, True) for voices in (False, True)]
        for paragraph in (p for paragraphs in every for p in paragraphs):
            for repo_only in REPO_ONLY:
                self.assertNotIn(repo_only, paragraph)

    def test_ai_ships_reads_the_packed_rows(self):
        rows = release.parse_licence_register(
            "| Lump | Origin | Licence |\n|---|---|---|\n"
            "| `STFST00` | drawn from Google Gemini images | CC BY-NC-SA 4.0 |\n"
            "| `SDRRISIT` | a Chatterbox take, processed | CC BY-NC-SA 4.0 |\n")
        nothing = release.LicenceCheck(coverage=[(rows[1], [])])
        self.assertEqual(release.ai_ships(nothing), release.AiShips())
        both = release.LicenceCheck(coverage=[(rows[0], ["graphics/hud/STFST00.png"]),
                                              (rows[1], ["sounds/SDRRISIT.ogg"])])
        self.assertEqual(release.ai_ships(both), release.AiShips(face=True, voices=True))
        text = release.render_credits("1.0", "0123456789ab", self.credits_lines, [], both)
        self.assertIn("the sergeant's face in the status bar", release.normalise(text))
        self.assertIn("Some of the enemies' voice lines", release.normalise(text))
        self.assertNotIn("speak with Freedoom's voices", release.normalise(text))

    def test_it_names_every_full_text_and_the_notice_for_freedoom_art(self):
        flat = release.normalise(self.text)
        for name in FULL_TEXTS:
            self.assertIn(name, flat)
        self.assertRegex(flat, r"Freedoom's BSD licence.*" + re.escape(FREEDOOM_TEXT))

    def test_the_tools_own_lines_fit_a_plain_text_window(self):
        for line in self.lines:
            if not line.startswith(("* ", "    ")):
                self.assertLessEqual(len(line), 78, line)


# --- Refusals of the command line and the tree ------------------------------------

class RefusalTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sd-test-release-")
        self.out = Path(self._tmp.name) / "out"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_version_is_mandatory(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            release.main([])
        self.assertEqual(caught.exception.code, 2)

    def test_a_malformed_version_is_refused(self):
        for bad in ("v1.0", "1", "1.0 beta", "", "../1.0"):
            with self.subTest(bad=bad), self.assertRaises(release.ReleaseError):
                release.make_release(release.Config(bad, self.out, allow_dirty=True))
        self.assertFalse(self.out.exists())

    def test_good_versions_match(self):
        for good in ("1.0", "1.0.1", "1.0-rc1", "2.10.3-beta.2"):
            self.assertRegex(good, release.VERSION_RE)

    def test_a_dirty_tree_is_refused_without_allow_dirty(self):
        dirty = release.TreeState("0" * 40, 1_800_000_000, (" M src/lumps/LANGUAGE",))
        with mock.patch.object(release, "git_state", return_value=dirty):
            with self.assertRaises(release.ReleaseError) as caught:
                release.make_release(release.Config("1.0", self.out))
            self.assertIn("--allow-dirty", str(caught.exception))
            self.assertIn("src/lumps/LANGUAGE", str(caught.exception))
            with redirect_stderr(io.StringIO()) as err:
                code = release.main(["--version", "1.0", "--out-dir", str(self.out)])
            self.assertEqual(code, release.EXIT_REFUSED)
            self.assertIn("uncommitted", err.getvalue())
        self.assertFalse(self.out.exists())

    def test_a_tree_outside_git_counts_as_dirty(self):
        state = release.git_state(Path(self._tmp.name))
        self.assertTrue(state.dirty)
        self.assertEqual(release.zip_time(None), release.MIN_ZIP_TIME)


# --- The licence check, with fake registers --------------------------------------------

FAKE_LICENSES = """\
# Asset provenance (fixture)

Prose that names `SDPROSE1` does not license it: only a table row does.

## Own work

| Lump | Origin | Licence |
|---|---|---|
| `SDOWN1`, `SDOWN2` | (a) generator | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `fonts/small/*.png` (3) | (a) font generator | idem |

## Third party

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `OTEXW1` | wall | OTEX 1.1 by **Ola Bjorling (ukiro)** | non-commercial, credit "Ola Bjorling (ukiro)" required |
| `OTEXW2` | wall | idem | idem |
| `D_ATTR` | music | sequenced by **Jane Roe** | `{{Attribution\\|Jane Roe}}`, credit "Jane Roe" is required |
| `D_CC0` | music | sequenced by **Anna Example** | CC0 1.0, no obligation; credited as a courtesy |
| `SDNONAME` | wall | a pack | CC BY 3.0 |
"""

FAKE_MUSIC_RIGHTS = """\
# Music rights (fixture)

### 4.5 What ships, and the credits it obliges

| Lump | Cue | Obligation |
|---|---|---|
| `D_ATTR` | title | **credit Jane Roe** |
| `D_CC0` | radio | **none**; credited as a courtesy |

**The credit line**, to be reproduced verbatim:

> *Title music* by **Jane Roe**, used under her attribution licence.

## 5. Next
"""

FAKE_LANGUAGE = """\
[enu default]
SD_CRED_TITLE = "Credits";
SD_CRED_H_TEAM = "Made by";
SD_CRED_TEAM_1 = "the Soviet Doom project"; // a comment
SD_CRED_TEAM_2 = "under CC BY-NC-SA 4.0";
SD_CRED_MUSIC_1 = "Title music by Jane Roe.";
SD_OTHER = "not a credit";

[ru]
SD_CRED_TITLE = "Авторы";
SD_CRED_H_TEAM = "Создатели";
SD_CRED_TEAM_1 = "проект Soviet Doom";
SD_CRED_TEAM_2 = "по лицензии CC BY-NC-SA 4.0";
SD_CRED_MUSIC_1 = "Музыка: Джейн Роу (Jane Roe).";
"""


class LicenceCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = release.parse_licence_register(FAKE_LICENSES)
        self.music = release.parse_music_register(FAKE_MUSIC_RIGHTS)
        self.credits = release.parse_credit_lines(FAKE_LANGUAGE)

    def check(self, names, credits=None):
        return release.check_licences(names, self.rows, self.music,
                                      self.credits if credits is None else credits)

    def test_a_fully_licensed_and_credited_pk3_passes(self):
        result = self.check(["MAPINFO", "textures/SDOWN1.png", "flats/SDOWN2.png",
                             "fonts/small/0041.png", "fonts/small/font.inf",
                             "music/D_ATTR.mid", "music/D_CC0.mid", "zscript/x.zs"])
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 1, "the CC0 courtesy name is only a warning")
        self.assertIn("Anna Example", result.warnings[0])

    def test_an_asset_without_a_licence_row_fails(self):
        result = self.check(["textures/SDOWN1.png", "textures/SDGHOST.png", "sprites/ABCDA0.png"])
        self.assertEqual(len(result.errors), 2)
        for path in ("textures/SDGHOST.png", "sprites/ABCDA0.png"):
            self.assertTrue(any(e.startswith(path + ": no licence row") for e in result.errors), path)

    def test_a_name_in_prose_is_not_a_licence_row(self):
        result = self.check(["textures/SDPROSE1.png"])
        self.assertEqual(len(result.errors), 1)

    def test_a_folder_row_covers_only_its_folder(self):
        self.assertEqual(self.check(["fonts/small/0042.png"]).errors, [])
        self.assertEqual(len(self.check(["fonts/big/0042.png"]).errors), 1)

    def test_an_attribution_missing_from_the_credits_fails(self):
        result = self.check(["textures/OTEXW1.png"])
        self.assertEqual(len(result.errors), 2, result.errors)   # English and Russian
        self.assertTrue(all("Ola Bjorling (ukiro)" in e for e in result.errors))

    def test_idem_inherits_the_obligation(self):
        result = self.check(["textures/OTEXW2.png"])
        self.assertTrue(result.errors)
        self.assertIn("Ola Bjorling (ukiro)", result.errors[0])

    def test_an_attribution_in_english_only_fails_in_russian(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE.replace("(Jane Roe)", ""))
        result = self.check(["music/D_ATTR.mid"], credits)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("[ru]", result.errors[0])

    # P6 (D97): the Catalan credits screen is checked like the other two.
    FAKE_CATALAN = (
        "\n[ca]\n"
        'SD_CRED_TITLE = "Crèdits";\n'
        'SD_CRED_H_TEAM = "Fet per";\n'
        'SD_CRED_TEAM_1 = "el projecte Soviet Doom";\n'
        'SD_CRED_TEAM_2 = "amb llicència CC BY-NC-SA 4.0";\n'
        'SD_CRED_MUSIC_1 = "Música del títol: Jane Roe.";\n'
    )

    def test_a_complete_catalan_screen_passes(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE + self.FAKE_CATALAN)
        result = self.check(["textures/SDOWN1.png", "music/D_ATTR.mid"], credits)
        self.assertEqual(result.errors, [])

    def test_an_attribution_missing_from_the_catalan_credits_fails(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE + self.FAKE_CATALAN.replace("Jane Roe", "algú"))
        result = self.check(["music/D_ATTR.mid"], credits)
        self.assertEqual(len(result.errors), 1, result.errors)
        self.assertIn("[ca]", result.errors[0])
        self.assertIn("Jane Roe", result.errors[0])

    def test_a_catalan_section_without_credit_lines_fails(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE + '\n[ca]\nSD_OTHER = "res";\n')
        result = self.check(["textures/SDOWN1.png"], credits)
        self.assertEqual(len(result.errors), 1, result.errors)
        self.assertIn("[ca]", result.errors[0])

    def test_the_real_catalan_credits_name_everyone(self):
        """The shipped LANGUAGE: every name a register row or MUSIC-RIGHTS
        obliges is on the [ca] screen too (the real-PK3 check runs only at
        the build tier; this one reads the registers directly)."""
        language = (PROJECT_ROOT / "src" / "lumps" / "LANGUAGE").read_text(encoding="utf-8")
        credits = release.parse_credit_lines(language)
        catalan = release.credits_text(credits[release.LANG_CATALAN])
        rows = release.parse_licence_register(
            (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8"))
        music = release.parse_music_register(
            (PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md").read_text(encoding="utf-8"))
        needed = {n for row in rows for n in row.required} | {n for m in music for n in m.required}
        self.assertIn("Jerry Engelbach", needed)
        self.assertEqual(sorted(n for n in needed if n not in catalan), [])

    def test_own_work_needs_the_team_and_the_licence_in_the_credits(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE.replace("CC BY-NC-SA 4.0", "CC0"))
        result = self.check(["textures/SDOWN1.png"], credits)
        self.assertEqual(len(result.errors), 2)
        self.assertTrue(all("CC BY-NC-SA 4.0" in e for e in result.errors))

    def test_a_row_that_needs_a_credit_and_names_nobody_fails(self):
        result = self.check(["textures/SDNONAME.png"])
        self.assertEqual(len(result.errors), 1)
        self.assertIn("names nobody", result.errors[0])

    def test_music_needs_a_music_rights_row(self):
        rows = release.parse_licence_register(
            FAKE_LICENSES + "\n| Lump | Licence |\n|---|---|\n| `D_NEW` | Soviet Doom project (D15) |\n")
        result = release.check_licences(["music/D_NEW.mid"], rows, self.music, self.credits)
        self.assertEqual(len(result.errors), 1)
        self.assertIn("MUSIC-RIGHTS", result.errors[0])

    def test_a_music_obligation_missing_from_the_credits_fails(self):
        credits = release.parse_credit_lines(FAKE_LANGUAGE.replace("Jane Roe", "someone"))
        result = self.check(["music/D_ATTR.mid"], credits)
        self.assertTrue(result.errors)
        self.assertTrue(all("Jane Roe" in e for e in result.errors))

    def test_no_credits_at_all_fails(self):
        result = self.check(["textures/SDOWN1.png"], {})
        self.assertEqual(len(result.errors), 2)

    def test_the_verbatim_lines_are_read(self):
        self.assertEqual(release.verbatim_music_lines(FAKE_MUSIC_RIGHTS),
                         ["Title music by Jane Roe, used under her attribution licence."])

    def test_the_screen_guard_shares_this_reading(self):
        """tests/test_credits.py reads the registers through tools/licences.py
        too: the names its screen must carry are these rows' required and
        courtesy names, our own rows aside, and the row that names nobody is
        an error there as well."""
        self.assertIs(release.parse_licence_register, licences.parse_licence_register)
        self.assertIs(release.parse_music_register, licences.parse_music_register)
        with self.assertRaises(licences.RegisterError):
            licences.credited_names(self.rows)
        named = [row for row in self.rows if not row.problem]
        self.assertEqual(licences.credited_names(named),
                         ["Ola Bjorling (ukiro)", "Jane Roe", "Anna Example"])
        self.assertEqual(licences.music_attribution_names(FAKE_MUSIC_RIGHTS), ["Jane Roe"])

    def test_language_reading_keeps_order_and_drops_comments(self):
        ids = [i for i, _ in self.credits["default"]]
        self.assertEqual(ids, ["SD_CRED_TITLE", "SD_CRED_H_TEAM", "SD_CRED_TEAM_1",
                               "SD_CRED_TEAM_2", "SD_CRED_MUSIC_1"])
        self.assertEqual(dict(self.credits["default"])["SD_CRED_TEAM_1"], "the Soviet Doom project")


# --- Guards on what enters the zip ---------------------------------------------------

class GuardTest(unittest.TestCase):
    def test_a_clean_pk3_passes(self):
        pk3 = zip_bytes({"MAPINFO": b"x", "maps/MAP01.wad": b"PWAD....", "textures/SDX.png": b"png"})
        self.assertEqual(release.guard_pk3(pk3), [])

    def test_work_tools_previews_and_iwads_are_caught_in_the_pk3(self):
        pk3 = zip_bytes({
            "work/art/draft.png": b"png",
            "tools/build.py": b"py",
            "graphics/previews/sheet.png": b"png",
            "textures/SDPREVIEW.png": b"png",
            "freedoom2.wad": b"IWAD....",
            "maps/MAP09.wad": b"IWAD....",
            "maps/MAP10.wad": b"junk",
            "music/D_X.mid": b"IWAD....",
        })
        errors = release.guard_pk3(pk3)
        for needle in ("work/art/draft.png", "tools/build.py", "graphics/previews/sheet.png",
                       "textures/SDPREVIEW.png", "freedoom2.wad", "maps/MAP09.wad",
                       "maps/MAP10.wad is not a PWAD", "music/D_X.mid is an IWAD"):
            self.assertTrue(any(needle in e for e in errors), f"{needle} not caught: {errors}")

    def test_the_member_list_must_be_exact(self):
        good = [f"{FOLDER}/{n}" for n in release.RELEASE_FILES]
        self.assertEqual(release.guard_members(good), [])
        errors = release.guard_members(good + [f"{FOLDER}/iwads/freedoom2.wad"])
        self.assertTrue(any("iwads/" in e for e in errors))
        self.assertTrue(any("WAD" in e for e in errors))
        self.assertTrue(release.guard_members(good + ["work/x.png"]))
        self.assertTrue(release.guard_members(good[:-1]))


# --- The refusals, end to end (fake inputs, the real pipeline) --------------------------

class EndToEndRefusalTest(unittest.TestCase):
    """make_release refuses and writes nothing. The PK3 is built once and
    reused through a stubbed build_pk3, so each case costs no build."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory(prefix="sd-test-release-")
        cls.root = Path(cls._tmp.name)
        cls.pk3 = release.build_pk3(release.Config(VERSION), cls.root).read_bytes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def _stub(self, pk3: bytes):
        def fake_build(config, workdir):
            out = Path(workdir) / release.PK3_NAME
            out.write_bytes(pk3)
            return out
        return mock.patch.object(release, "build_pk3", side_effect=fake_build)

    def _refused(self, config: release.Config, pk3: bytes | None = None) -> str:
        with self._stub(self.pk3 if pk3 is None else pk3):
            with self.assertRaises(release.ReleaseError) as caught:
                release.make_release(config)
        self.assertFalse(config.out_dir.exists(), "a refused release wrote files")
        return str(caught.exception)

    def _config(self, name: str, **kw) -> release.Config:
        return release.Config(VERSION, self.root / name, allow_dirty=True, **kw)

    def test_a_register_without_an_asset_row_refuses(self):
        real = (PROJECT_ROOT / "docs" / "art" / "LICENSES.md").read_text(encoding="utf-8")
        fake = self.root / "LICENSES-no-sdconc1.md"
        fake.write_text(real.replace("`SDCONC1`, ", ""), encoding="utf-8")
        message = self._refused(self._config("out1", licenses=fake))
        self.assertIn("textures/SDCONC1.png", message)
        self.assertIn("no licence row", message)

    def test_credits_without_a_required_name_refuse(self):
        real = (PROJECT_ROOT / "src" / "lumps" / "LANGUAGE").read_text(encoding="utf-8")
        fake = self.root / "LANGUAGE-no-engelbach"
        fake.write_text(real.replace("Jerry Engelbach", "J. E."), encoding="utf-8")
        message = self._refused(self._config("out2", language=fake))
        self.assertIn("music/D_SDINTL.mid", message)
        self.assertIn("'Jerry Engelbach'", message)

    def test_a_clean_tree_releases_without_allow_dirty_and_without_the_dirty_mark(self):
        clean = release.TreeState("ab" * 20, 1_800_000_000, ())
        config = release.Config("1.0", self.root / "clean")
        with self._stub(self.pk3), mock.patch.object(release, "git_state", return_value=clean):
            made = release.make_release(config)
        with zipfile.ZipFile(made.zip_path) as zf:
            readme = zf.read("sovietdoom-1.0/README.txt").decode("utf-8")
            stamps = {i.date_time for i in zf.infolist()}
        self.assertIn("commit ababababab", readme)
        self.assertNotIn("+dirty", readme)
        self.assertEqual(stamps, {release.zip_time(1_800_000_000)})

    def test_a_dirty_test_release_says_so(self):
        dirty = release.TreeState("cd" * 20, 1_800_000_000, ("?? new.txt",))
        config = self._config("dirty")
        with self._stub(self.pk3), mock.patch.object(release, "git_state", return_value=dirty):
            made = release.make_release(config)
        with zipfile.ZipFile(made.zip_path) as zf:
            for name in (release.README_NAME, release.CREDITS_NAME):
                self.assertIn("cdcdcdcdcdcd+dirty", zf.read(f"{FOLDER}/{name}").decode("utf-8"))

    def test_an_iwad_inside_the_pk3_refuses(self):
        with zipfile.ZipFile(io.BytesIO(self.pk3)) as zf:
            files = {n: zf.read(n) for n in zf.namelist()}
        files["freedoom2.wad"] = b"IWAD" + bytes(8)
        message = self._refused(self._config("out3"), zip_bytes(files))
        self.assertIn("freedoom2.wad is an IWAD", message)


if __name__ == "__main__":
    unittest.main()
