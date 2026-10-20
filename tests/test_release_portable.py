"""Tests for tools/release_portable.py, the Windows "unzip and double-click"
package (P5, D93; docs/engine/RELEASE.md, "Portable packages (P5)").

What is pinned:

  * the structure: one folder SovietDoom/ holding exactly the engine files,
    freedoom2.wad, the release's files, the two launchers, the two guides,
    GZDOOM-SOURCE.txt, gzdoom_portable.ini and SHA256SUMS;
  * the launchers, line by line: ASCII, CRLF, `cd /d "%~dp0"`, the
    "extract the zip first" guard, and one `start` with -iwad and -file;
  * the portable switch: gzdoom_portable.ini next to gzdoom.exe;
  * the licences: GPL, CC, Freedoom's BSD notice, LICENSE.md, GZDoom's
    licenses.zip, and GZDOOM-SOURCE.txt with the g4.14.2 tree, the source
    archives, the libraries, the written offer and every engine file's hash;
  * the guides (Spanish and English): BOM, CRLF, SmartScreen, the language
    path read from LANGUAGE, the keys;
  * SHA256SUMS, the .sha256 beside the zip, and determinism (same inputs,
    same bytes, every timestamp the release zip's);
  * the refusals: --out inside the repo, an engine missing a required file
    or not g4.14.2, a freedoom2.wad that is not 0.13.0, a malformed release
    zip; and a user's ini, saves or WADs in the engine folder never ship.

Fast tests use a fake engine folder, a fake IWAD and a fake release zip whose
PK3 carries the repo's real LANGUAGE. RealPortableTest uses the installed
GZDoom, iwads/freedoom2.wad and a real release build; it skips when either is
absent (CI) and runs in the art tier (tests/_tiers.py SLOW).

Run:  python -m unittest tests.test_release_portable -v
"""

from __future__ import annotations

import hashlib
import io
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

import release  # noqa: E402
import release_portable as rp  # noqa: E402

VERSION = "0.0-test"
FOLDER = rp.FOLDER
LANGUAGE = PROJECT_ROOT / "src" / "lumps" / "LANGUAGE"
STAMP = (2026, 10, 20, 12, 0, 0)
FAKE_IWAD = b"IWAD fake freedoom2"

# What the package holds besides the engine's own files.
OURS = sorted([
    "CREDITS.txt", "GZDOOM-SOURCE.txt", "Jugar Soviet Doom.bat", "LEEME.txt",
    "LICENSE-CC-BY-NC-SA-4.0.txt", "LICENSE-FREEDOOM-BSD-3.txt", "LICENSE-GPL-3.0.txt",
    "LICENSE.md", "Play Soviet Doom.bat", "README-FIRST.txt", "README.txt", "SHA256SUMS",
    "freedoom2.wad", "gzdoom_portable.ini", "sovietdoom.pk3",
])
FAKE_ENGINE = {
    "gzdoom.exe": b"MZ fake engine GZDoom g4.14.2-m",
    "gzdoom.pk3": b"PK engine",
    "zmusic.dll": b"zmusic", "openal32.dll": b"openal", "sndfile.dll": b"sndfile",
    "licenses.zip": b"PK licences",
    "lights.pk3": b"PK lights", "brightmaps.pk3": b"PK brightmaps",
    "soundfonts/gzdoom.sf2": b"RIFF sf2",
    "fm_banks/GENMIDI.GS.wopl": b"WOPL",
}
# A user's things in the install folder: never packed.
USER_JUNK = {
    "gzdoom_portable.ini": b"[GlobalSettings]\nmy=secret\n",
    "gzdoom-littl.ini": b"old ini",
    "Save/save01.zds": b"save",
    "Screenshots/shot.png": b"png",
    "doom2.wad": b"IWAD commercial",
    "mymod.pk3": b"PK mod",
}
LAUNCH = ('start "" "%~dp0gzdoom.exe" -iwad "%~dp0freedoom2.wad" '
          '-file "%~dp0sovietdoom.pk3"')


def write_tree(root: Path, files: dict[str, bytes]) -> None:
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def fake_pk3() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("LANGUAGE", LANGUAGE.read_bytes())
    return buffer.getvalue()


def fake_release_files() -> dict[str, bytes]:
    files = {name: f"fake {name}\n".encode() for name in release.RELEASE_FILES}
    files[release.PK3_NAME] = fake_pk3()
    files[release.README_NAME] = b"SOVIET DOOM\n===========\nthe release readme\n"
    del files[release.SUMS_NAME]
    files[release.SUMS_NAME] = release.render_sums(files).encode("ascii")
    return files


def fake_release_zip(files: dict[str, bytes] | None = None, version: str = VERSION) -> bytes:
    files = fake_release_files() if files is None else files
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name in sorted(files):
            zf.writestr(zipfile.ZipInfo(f"{release.MOD_NAME}-{version}/{name}", STAMP),
                        files[name])
    return buffer.getvalue()


def read_package(path: Path) -> tuple[dict[str, bytes], list[zipfile.ZipInfo]]:
    with zipfile.ZipFile(path) as zf:
        infos = zf.infolist()
        return {i.filename: zf.read(i.filename) for i in infos}, infos


class FakeInputs(unittest.TestCase):
    """A fake engine folder (with a user's junk), IWAD and release zip."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.engine = self.root / "GZDoom"
        write_tree(self.engine, {**FAKE_ENGINE, **USER_JUNK})
        self.iwad = self.root / "freedoom2.wad"
        self.iwad.write_bytes(FAKE_IWAD)
        self.release_zip = self.root / f"{release.MOD_NAME}-{VERSION}.zip"
        self.release_zip.write_bytes(fake_release_zip())
        pin = mock.patch.object(rp, "FREEDOOM2_SHA256", hashlib.sha256(FAKE_IWAD).hexdigest())
        pin.start()
        self.addCleanup(pin.stop)
        self.addCleanup(self._tmp.cleanup)

    def config(self, out: str = "out", **kw) -> rp.Config:
        base = dict(engine_dir=self.engine, iwad=self.iwad, release_zip=self.release_zip)
        base.update(kw)
        return rp.Config(VERSION, self.root / out, **base)

    def make(self, out: str = "out", **kw) -> tuple[rp.Portable, dict[str, bytes]]:
        made = rp.make_portable(self.config(out, **kw))
        files, _ = read_package(made.zip_path)
        return made, {name.split("/", 1)[1]: data for name, data in files.items()}


class StructureTest(FakeInputs):

    def test_one_folder_with_exactly_the_engine_and_our_files(self):
        made, files = self.make()
        self.assertEqual(made.zip_path.name, f"sovietdoom-{VERSION}-windows.zip")
        self.assertTrue(all(m.startswith(FOLDER + "/") for m in made.members))
        self.assertEqual(sorted(files), sorted(OURS + list(FAKE_ENGINE)))

    def test_the_engine_files_ship_unchanged(self):
        _, files = self.make()
        for name, data in FAKE_ENGINE.items():
            self.assertEqual(files[name], data, name)

    def test_a_users_ini_saves_screenshots_and_wads_never_ship(self):
        made, files = self.make()
        self.assertNotIn("gzdoom-littl.ini", files)
        self.assertNotIn("doom2.wad", files)
        self.assertNotIn("mymod.pk3", files)
        self.assertFalse(any(n.startswith(("Save/", "Screenshots/")) for n in files))
        # The portable ini that ships is ours, not the user's.
        self.assertNotIn(b"secret", files[rp.PORTABLE_INI])
        self.assertTrue(any("doom2.wad" in w for w in made.warnings))

    def test_the_release_files_ship_byte_for_byte_and_the_readme_gains_a_note(self):
        _, files = self.make()
        original = fake_release_files()
        for name in release.RELEASE_FILES:
            if name in (release.README_NAME, release.SUMS_NAME):
                continue
            self.assertEqual(files[name], original[name], name)
        readme = files[release.README_NAME].decode("utf-8")
        self.assertTrue(readme.endswith(original[release.README_NAME].decode("utf-8")))
        self.assertIn("PORTABLE WINDOWS PACKAGE", readme)
        self.assertIn("Play Soviet Doom.bat", readme)

    def test_freedoom2_wad_ships(self):
        _, files = self.make()
        self.assertEqual(files["freedoom2.wad"], FAKE_IWAD)


class LauncherTest(FakeInputs):

    def setUp(self) -> None:
        super().setUp()
        _, self.files = self.make()

    def lines(self, name: str) -> list[str]:
        data = self.files[name]
        data.decode("ascii")  # cmd.exe reads a .bat in the OEM code page: ASCII only
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), f"{name}: CRLF only")
        return data.decode("ascii").split("\r\n")

    def test_both_launchers_run_the_same_commands(self):
        for name in (rp.BAT_ES, rp.BAT_EN):
            lines = self.lines(name)
            self.assertEqual(lines[0], "@echo off")
            self.assertIn('cd /d "%~dp0"', lines)
            self.assertIn('if exist "%~dp0gzdoom.exe" goto play', lines)
            self.assertIn(":play", lines)
            self.assertEqual([ln for ln in lines if ln.startswith("start ")], [LAUNCH])
            self.assertEqual(lines[-2:], [LAUNCH, ""])

    def test_the_guard_says_to_extract_the_zip_in_each_language(self):
        es = "\r\n".join(self.lines(rp.BAT_ES))
        en = "\r\n".join(self.lines(rp.BAT_EN))
        self.assertIn("Extraer todo", es)
        self.assertIn("Extract All", en)
        for text in (es, en):
            self.assertIn("pause", text)
            self.assertIn("exit /b 1", text)

    def test_no_iwad_picker_flag_is_needed_and_none_is_passed(self):
        # -iwad leaves one candidate, so g4.14.2 shows no picker (d_iwad.cpp).
        text = self.files[rp.BAT_EN].decode("ascii")
        self.assertNotIn("queryiwad", text)
        self.assertIn("-iwad", text)


class PortableModeTest(FakeInputs):

    def test_the_portable_ini_sits_next_to_gzdoom_exe(self):
        made, files = self.make()
        self.assertIn(f"{FOLDER}/gzdoom_portable.ini", made.members)
        self.assertIn(f"{FOLDER}/gzdoom.exe", made.members)
        text = files["gzdoom_portable.ini"].decode("ascii")
        # Comment lines only: GZDoom fills in its defaults on the first run.
        self.assertTrue(all(ln.startswith("#") for ln in text.split("\r\n") if ln))


class LicenceTest(FakeInputs):

    def setUp(self) -> None:
        super().setUp()
        _, self.files = self.make()
        self.source = self.files[rp.SOURCE_NAME].decode("utf-8")

    def test_every_licence_ships(self):
        for name in ("LICENSE.md", "LICENSE-GPL-3.0.txt", "LICENSE-CC-BY-NC-SA-4.0.txt",
                     "LICENSE-FREEDOOM-BSD-3.txt", "licenses.zip", rp.SOURCE_NAME):
            self.assertIn(name, self.files)

    def test_the_source_file_points_to_the_exact_engine_source(self):
        for url in ("https://github.com/ZDoom/gzdoom/tree/g4.14.2",
                    "https://github.com/ZDoom/gzdoom/releases/tag/g4.14.2",
                    "https://github.com/ZDoom/gzdoom/archive/refs/tags/g4.14.2.zip",
                    "https://github.com/ZDoom/gzdoom/archive/refs/tags/g4.14.2.tar.gz",
                    "https://github.com/kcat/openal-soft/tree/1.23.1",
                    "https://github.com/libsndfile/libsndfile/releases/tag/1.2.2",
                    "https://github.com/ZDoom/ZMusic"):
            self.assertIn(url, self.source)
        self.assertIn("WRITTEN OFFER", self.source)
        self.assertIn("three years", self.source)
        self.assertIn("LICENSE-GPL-3.0.txt", self.source)

    def test_the_source_file_lists_every_engine_files_hash(self):
        for name, data in FAKE_ENGINE.items():
            self.assertIn(f"{hashlib.sha256(data).hexdigest()}  {name}", self.source)


class GuideTest(FakeInputs):

    def setUp(self) -> None:
        super().setUp()
        _, self.files = self.make()

    def text(self, name: str) -> str:
        data = self.files[name]
        self.assertTrue(data.startswith(rp.UTF8_BOM), f"{name}: Notepad needs the BOM")
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""), f"{name}: CRLF only")
        return data[len(rp.UTF8_BOM):].decode("utf-8")

    def test_spanish_guide(self):
        text = self.text(rp.LEEME_NAME)
        for phrase in ("Extraer todo", "Jugar Soviet Doom", "Windows protegió su PC",
                       "Más información", "Ejecutar de todas formas", "Desbloquear",
                       "Options > Soviet Doom > Language > Russian",
                       "New Game > Soviet Doom", "gzdoom_portable.ini", "Save",
                       "W A S D", "Program Files", "GZDOOM-SOURCE.txt"):
            self.assertIn(phrase, text)

    def test_english_guide(self):
        text = self.text(rp.README_FIRST_NAME)
        for phrase in ("Extract All", "Play Soviet Doom", "Windows protected your PC",
                       "More info", "Run anyway", "Unblock",
                       "Options > Soviet Doom > Language > Russian",
                       "New Game > Soviet Doom", "gzdoom_portable.ini", "W A S D",
                       "Program Files", "GZDOOM-SOURCE.txt"):
            self.assertIn(phrase, text)

    def test_menu_names_come_from_language(self):
        with mock.patch.object(release, "language_strings",
                               return_value={"default": {}}):
            with self.assertRaises(rp.PortableError):
                rp.menu_names(fake_pk3())


class SumsAndDeterminismTest(FakeInputs):

    def test_sha256sums_covers_every_other_file(self):
        _, files = self.make()
        lines = files["SHA256SUMS"].decode("ascii").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
        self.assertEqual(sorted(listed), sorted(n for n in files if n != "SHA256SUMS"))
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256(files[name]).hexdigest(), digest, name)

    def test_the_sha256_beside_the_zip(self):
        made, _ = self.make()
        digest = hashlib.sha256(made.zip_path.read_bytes()).hexdigest()
        self.assertEqual(made.sha_path.read_text(encoding="ascii"),
                         f"{digest}  {made.zip_path.name}\n")

    def test_same_inputs_same_bytes_and_the_release_timestamp(self):
        first, _ = self.make("a")
        second, _ = self.make("b")
        self.assertEqual(first.zip_path.read_bytes(), second.zip_path.read_bytes())
        _, infos = read_package(first.zip_path)
        self.assertEqual({i.date_time for i in infos}, {STAMP})
        self.assertEqual([i.filename for i in infos], sorted(i.filename for i in infos))


class RefusalTest(FakeInputs):

    def assert_refused(self, config: rp.Config, words: str) -> None:
        with self.assertRaises(rp.PortableError) as caught:
            rp.make_portable(config)
        self.assertIn(words, str(caught.exception))
        self.assertFalse(config.out_dir.exists(), "nothing is written on a refusal")

    def test_out_inside_the_repo(self):
        config = self.config()
        config.out_dir = PROJECT_ROOT / "dist" / "portable-test-never-written"
        self.assert_refused(config, "inside the repo")

    def test_a_bad_version(self):
        config = self.config()
        config.version = "v1.0"
        self.assert_refused(config, "not a release version")

    def test_no_engine(self):
        self.assert_refused(self.config(engine_dir=self.root / "nowhere"), "no GZDoom")

    def test_an_engine_missing_a_required_file(self):
        (self.engine / "zmusic.dll").unlink()
        self.assert_refused(self.config(), "zmusic.dll")

    def test_an_engine_that_is_not_g4_14_2(self):
        (self.engine / "gzdoom.exe").write_bytes(b"MZ GZDoom g4.12.2")
        self.assert_refused(self.config(), "is not GZDoom g4.14.2")

    def test_a_freedoom2_wad_that_is_not_0_13_0(self):
        self.iwad.write_bytes(b"IWAD another freedoom")
        self.assert_refused(self.config(), "is not Freedoom 0.13.0")

    def test_a_release_zip_missing_a_file(self):
        files = fake_release_files()
        del files["CREDITS.txt"]
        self.release_zip.write_bytes(fake_release_zip(files))
        self.assert_refused(self.config(), "must hold exactly")

    def test_a_release_zip_for_another_version(self):
        self.release_zip.write_bytes(fake_release_zip(version="9.9"))
        self.assert_refused(self.config(), "must hold exactly")

    def test_a_release_zip_whose_sums_lie(self):
        files = fake_release_files()
        files["LICENSE.md"] = b"edited\n"
        self.release_zip.write_bytes(fake_release_zip(files))
        self.assert_refused(self.config(), "SHA256SUMS does not match")

    def test_the_cli_exits_1(self):
        out = self.root / "cli"
        with redirect_stderr(io.StringIO()) as err:
            code = rp.main(["--version", VERSION, "--out", str(out), "--engine-dir",
                            str(self.root / "nowhere"), "--iwad", str(self.iwad),
                            "--release-zip", str(self.release_zip)])
        self.assertIn("no GZDoom", err.getvalue())
        self.assertEqual(code, rp.EXIT_REFUSED)
        self.assertFalse(out.exists())


ENGINE_PRESENT = (rp.DEFAULT_ENGINE_DIR / rp.ENGINE_EXE).is_file()
IWAD_PRESENT = rp.DEFAULT_IWAD.is_file()


@unittest.skipUnless(ENGINE_PRESENT and IWAD_PRESENT,
                     "needs the installed GZDoom g4.14.2 and iwads/freedoom2.wad (not on CI)")
class RealPortableTest(unittest.TestCase):
    """The installed engine, the real IWAD and a release built from this tree."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        made = release.make_release(release.Config(VERSION, root / "release", allow_dirty=True))
        config = dict(engine_dir=rp.DEFAULT_ENGINE_DIR, iwad=rp.DEFAULT_IWAD,
                      release_zip=made.zip_path)
        cls.first = rp.make_portable(rp.Config(VERSION, root / "a", **config))
        cls.second = rp.make_portable(rp.Config(VERSION, root / "b", **config))
        files, _ = read_package(cls.first.zip_path)
        cls.files = {name.split("/", 1)[1]: data for name, data in files.items()}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_deterministic(self):
        self.assertEqual(self.first.zip_path.read_bytes(), self.second.zip_path.read_bytes())

    def test_the_engine_and_ours(self):
        for name in OURS + list(rp.ENGINE_REQUIRED) + ["soundfonts/gzdoom.sf2"]:
            self.assertIn(name, self.files)
        for name, data in self.files.items():
            if "/" in name or name in OURS:
                continue
            self.assertIn(name, rp.ENGINE_FILES, f"{name}: not an engine file we know")
            self.assertEqual(data, (rp.DEFAULT_ENGINE_DIR / name).read_bytes(), name)

    def test_the_real_iwad_and_pk3(self):
        self.assertEqual(hashlib.sha256(self.files["freedoom2.wad"]).hexdigest(),
                         rp.FREEDOOM2_SHA256)
        with zipfile.ZipFile(io.BytesIO(self.files["sovietdoom.pk3"])) as zf:
            self.assertIn("LANGUAGE", zf.namelist())

    def test_no_user_file_ships(self):
        for name in self.files:
            self.assertFalse(name.lower().endswith((".cfg", ".zds", ".log")), name)
            if name.lower().endswith(".ini"):
                self.assertEqual(name, rp.PORTABLE_INI)


if __name__ == "__main__":
    unittest.main()
