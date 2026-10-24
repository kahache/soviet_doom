"""Tests for tools/release_portable.py, the Windows "unzip and double-click"
package (P5, D93; docs/engine/RELEASE.md, "Portable packages (P5)").

What is pinned:

  * the structure: one folder SovietDoom/ holding exactly the engine files,
    freedoom2.wad, the release's files, the launcher, the guide,
    GZDOOM-SOURCE.txt, gzdoom_portable.ini and SHA256SUMS; no Spanish file
    (D129: the player languages are English, Russian and Catalan);
  * the launcher, line by line: ASCII, CRLF, `cd /d "%~dp0"`, the
    "extract the zip first" guard, and one `start` with -iwad and -file;
  * the portable switch: gzdoom_portable.ini next to gzdoom.exe;
  * the licences: GPL, CC, Freedoom's BSD notice, LICENSE.md, GZDoom's
    licenses.zip, and GZDOOM-SOURCE.txt with the g4.14.2 tree, the source
    archives, the libraries, the written offer and every engine file's hash;
  * the guide (English): BOM, CRLF, SmartScreen, the language
    path read from LANGUAGE, the keys;
  * SHA256SUMS, the .sha256 beside the zip, and determinism (same inputs,
    same bytes, every timestamp the release zip's);
  * the refusals: --out inside the repo, an engine missing a required file
    or not g4.14.2, a freedoom2.wad that is not 0.13.0, a malformed release
    zip; and a user's ini, saves or WADs in the engine folder never ship;
  * macOS (D101/D102): every GZDoom.app entry of the official zip keeps its
    bytes and its external_attr (gzdoom 755, symlinks stay symlinks, the
    AppleDouble signature files ship), the .command launcher is 755, sh,
    `cd "$(dirname "$0")"`, -iwad/-file/-config/-savedir inside the folder;
    the guide explains Gatekeeper; SHA256SUMS skips only the ._* files;
  * Linux: /opt/gzdoom of the .deb (ar + data.tar, no dpkg) as gzdoom/,
    play.sh 755, folders 755, files 644, owner root, the release's
    mtime, a gzip header with no name or time; the guide lists the .deb's
    Depends and the apt command; the licence texts from the source archive;
  * both: determinism, and refusals for unsafe paths, escaping symlinks,
    other engine versions, broken archives.

Fast tests use a fake engine folder, a fake IWAD and a fake release zip whose
PK3 carries the repo's real LANGUAGE, plus a small fake macOS zip, .deb and
GZDoom source archive (never the real downloads). RealPortableTest uses the installed
GZDoom, iwads/freedoom2.wad and a real release build; it skips when either is
absent (CI) and runs in the art tier (tests/_tiers.py SLOW).

Run:  python -m unittest tests.test_release_portable -v
"""

from __future__ import annotations

import calendar
import hashlib
import io
import plistlib
import stat
import sys
import tarfile
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
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
    "CREDITS.txt", "GZDOOM-SOURCE.txt",
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

    def test_the_launcher_runs_one_command(self):
        for name in (rp.BAT_EN,):
            lines = self.lines(name)
            self.assertEqual(lines[0], "@echo off")
            self.assertIn('cd /d "%~dp0"', lines)
            self.assertIn('if exist "%~dp0gzdoom.exe" goto play', lines)
            self.assertIn(":play", lines)
            self.assertEqual([ln for ln in lines if ln.startswith("start ")], [LAUNCH])
            self.assertEqual(lines[-2:], [LAUNCH, ""])

    def test_the_guard_says_to_extract_the_zip(self):
        en = "\r\n".join(self.lines(rp.BAT_EN))
        self.assertIn("Extract All", en)
        self.assertIn("pause", en)
        self.assertIn("exit /b 1", en)

    def test_one_launcher_only_and_no_spanish_one(self):
        # D129: no "Jugar Soviet Doom.bat" (Spanish is not a project language).
        self.assertEqual(sorted(n for n in self.files if n.endswith(".bat")), [rp.BAT_EN])

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

    def test_english_guide(self):
        text = self.text(rp.README_FIRST_NAME)
        for phrase in ("Extract All", "Play Soviet Doom", "Windows protected your PC",
                       "More info", "Run anyway", "Unblock",
                       "Options > Soviet Doom > Language > Russian or Catalan",
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


class WindowsDefaultTest(FakeInputs):
    """--platform windows is the default and keeps its name and engine source."""

    def test_the_default_platform_is_windows(self):
        self.assertEqual(self.config().platform, "windows")
        self.assertEqual(rp.zip_name(VERSION), f"sovietdoom-{VERSION}-windows.zip")

    def test_the_source_file_names_the_archives_on_the_v1_0_release(self):
        _, files = self.make()
        source = files[rp.SOURCE_NAME].decode("utf-8")
        self.assertIn("https://github.com/kahache/soviet_doom/releases/tag/v1.0", source)
        for name in ("gzdoom-g4.14.2-source.tar.gz", "openal-soft-1.23.1-source.tar.gz",
                     "libsndfile-1.2.2-source.tar.gz", "zmusic-1.1.14-source.tar.gz"):
            self.assertIn(name, source)
        self.assertIn("for Windows (64-bit)", source)
        self.assertIn("licenses.zip (GZDoom's own file, unchanged)", source)

    def test_an_engine_archive_is_refused_on_windows(self):
        config = self.config(engine_archive=self.root / "x.zip")
        with self.assertRaises(rp.PortableError) as caught:
            rp.make_portable(config)
        self.assertIn("for macos and linux", str(caught.exception))

    def test_an_unknown_platform_is_refused(self):
        with self.assertRaises(rp.PortableError):
            rp.make_portable(self.config(platform="beos"))


# --- macOS and Linux (fake engine archives) ---------------------------------------------

S_DIR = stat.S_IFDIR | 0o755
S_FILE = stat.S_IFREG | 0o644
S_EXEC = stat.S_IFREG | 0o755
S_LINK = stat.S_IFLNK | 0o755
FAKE_PLIST = plistlib.dumps({"CFBundleExecutable": "gzdoom",
                             "CFBundleShortVersionString": "g4.14.2",
                             "LSMinimumSystemVersion": "10.15"})
APPLEDOUBLE = b"\x00\x05\x16\x07\x00\x02\x00\x00Mac OS X        com.apple.cs.CodeDirectory"
# (name, Unix mode, data): a symlink's data is its target.
FAKE_MAC = [
    ("GZDoom.app/", S_DIR, b""),
    ("GZDoom.app/Contents/", S_DIR, b""),
    ("GZDoom.app/Contents/Info.plist", S_FILE, FAKE_PLIST),
    ("GZDoom.app/Contents/MacOS/", S_DIR, b""),
    ("GZDoom.app/Contents/MacOS/gzdoom", S_EXEC, b"\xca\xfe\xba\xbe fake GZDoom g4.14.2"),
    ("GZDoom.app/Contents/MacOS/gzdoom.pk3", S_FILE, b"PK engine"),
    ("GZDoom.app/Contents/MacOS/._gzdoom.pk3", S_FILE, APPLEDOUBLE),
    ("GZDoom.app/Contents/Frameworks/", S_DIR, b""),
    ("GZDoom.app/Contents/Frameworks/libfoo.1.dylib", S_FILE, b"dylib"),
    ("GZDoom.app/Contents/Frameworks/libfoo.dylib", S_LINK, b"libfoo.1.dylib"),
    ("GZDoom.app/Contents/Current", S_LINK, b"MacOS"),
    ("Licenses/", S_DIR, b""),
    ("Licenses/gpl.txt", S_FILE, b"GNU GPL 3"),
    ("Licenses/bsd.txt", S_FILE, b"BSD"),
    ("__MACOSX/._GZDoom.app", S_FILE, b"junk"),
]
MAC_LAUNCHERS = ("Play Soviet Doom.command",)
LINUX_LAUNCHERS = ("play.sh",)
EXEC_LINE = ('exec "$ENGINE" -iwad "$HERE/freedoom2.wad" -file "$HERE/sovietdoom.pk3" '
             '-config "$HERE/gzdoom.ini" -savedir "$HERE/saves" "$@"')
FAKE_CONTROL = """\
Package: gzdoom
Version: 4.14.2
Architecture: amd64
Depends: libc6, libsdl2-2.0-0 (>= 2.0.8), libasound2 | libasound2t64, libopus0:amd64
Recommends: libopenal1
Description: OpenGL version of ZDoom.
 A second line.
"""
# (name, tar type, mode, data or link target)
FAKE_DEB_DATA = [
    ("./", tarfile.DIRTYPE, 0o755, b""),
    ("./opt/", tarfile.DIRTYPE, 0o755, b""),
    ("./opt/gzdoom/", tarfile.DIRTYPE, 0o755, b""),
    ("./opt/gzdoom/gzdoom", tarfile.REGTYPE, 0o755, b"\x7fELF fake GZDoom g4.14.2"),
    ("./opt/gzdoom/gzdoom.pk3", tarfile.REGTYPE, 0o644, b"PK engine"),
    ("./opt/gzdoom/libzmusic.so.1", tarfile.REGTYPE, 0o644, b"\x7fELF zmusic"),
    ("./opt/gzdoom/libzmusic.so", tarfile.SYMTYPE, 0o777, b"libzmusic.so.1"),
    ("./opt/gzdoom/soundfonts/gzdoom.sf2", tarfile.REGTYPE, 0o664, b"RIFF sf2"),
    ("./usr/games/gzdoom", tarfile.REGTYPE, 0o755, b"#!/bin/bash\nexec /opt/gzdoom/gzdoom\n"),
]
FAKE_SOURCE = {
    "gzdoom-g4.14.2/docs/licenses/gpl.txt": b"GNU GPL 3",
    "gzdoom-g4.14.2/docs/licenses/bsd.txt": b"BSD",
    "gzdoom-g4.14.2/src/d_main.cpp": b"// source",
}


def fake_macos_zip(entries=FAKE_MAC) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, mode, data in entries:
            info = zipfile.ZipInfo(name, (2025, 5, 3, 11, 3, 10))
            info.create_system = 3
            info.external_attr = (mode << 16) | (0x10 if stat.S_ISDIR(mode) else 0)
            zf.writestr(info, data)
    return buffer.getvalue()


def fake_tar(entries, mode: str = "w:xz") -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode=mode) as tf:
        for name, kind, perm, data in entries:
            info = tarfile.TarInfo(name)
            info.type, info.mode, info.mtime = kind, perm, 1746242438
            if kind == tarfile.SYMTYPE:
                info.linkname = data.decode()
                tf.addfile(info)
            elif kind == tarfile.REGTYPE:
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
            else:
                tf.addfile(info)
    return buffer.getvalue()


def ar_archive(members: list[tuple[str, bytes]]) -> bytes:
    out = bytearray(b"!<arch>\n")
    for name, data in members:
        out += f"{name:<16}{0:<12}{0:<6}{0:<6}{'100644':<8}{len(data):<10}".encode() + b"`\n"
        out += data + (b"\n" if len(data) % 2 else b"")
    return bytes(out)


def fake_deb(control: str = FAKE_CONTROL, data=FAKE_DEB_DATA) -> bytes:
    control_tar = fake_tar([("./", tarfile.DIRTYPE, 0o755, b""),
                            ("./control", tarfile.REGTYPE, 0o644, control.encode())])
    return ar_archive([("debian-binary", b"2.0\n"), ("control.tar.xz", control_tar),
                       ("data.tar.xz", fake_tar(data))])


def fake_source() -> bytes:
    return fake_tar([(name, tarfile.REGTYPE, 0o644, data) for name, data in FAKE_SOURCE.items()],
                    mode="w:gz")


class UnixInputs(FakeInputs):
    """The Windows fakes plus a fake macOS zip, .deb and source archive."""

    def setUp(self) -> None:
        super().setUp()
        self.mac_zip = self.root / "gzdoom-4-14-2-macos.zip"
        self.mac_zip.write_bytes(fake_macos_zip())
        self.deb = self.root / "gzdoom_4.14.2_amd64.deb"
        self.deb.write_bytes(fake_deb())
        self.source = self.root / "gzdoom-g4.14.2-source.tar.gz"
        self.source.write_bytes(fake_source())

    def mac_config(self, out: str = "mac", **kw) -> rp.Config:
        base = dict(platform="macos", engine_archive=self.mac_zip)
        base.update(kw)
        return self.config(out, **base)

    def linux_config(self, out: str = "linux", **kw) -> rp.Config:
        base = dict(platform="linux", engine_archive=self.deb, gzdoom_source=self.source)
        base.update(kw)
        return self.config(out, **base)

    def assert_refused(self, config: rp.Config, words: str) -> None:
        with self.assertRaises(rp.PortableError) as caught:
            rp.make_portable(config)
        self.assertIn(words, str(caught.exception))
        self.assertFalse(config.out_dir.exists(), "nothing is written on a refusal")

    def assert_launcher(self, data: bytes, exe: str) -> list[str]:
        text = data.decode("ascii")
        self.assertNotIn("\r", text)
        lines = text.split("\n")
        self.assertEqual(lines[0], "#!/bin/sh")
        self.assertIn('cd "$(dirname "$0")" || exit 1', lines)
        self.assertIn(f'ENGINE="$HERE/{exe}"', lines)
        self.assertIn('mkdir -p "$HERE/saves"', lines)
        self.assertEqual([ln for ln in lines if ln.startswith("exec ")], [EXEC_LINE])
        self.assertEqual(lines[-2:], [EXEC_LINE, ""])
        return lines


class MacosPackageTest(UnixInputs):

    def setUp(self) -> None:
        super().setUp()
        self.made = rp.make_portable(self.mac_config())
        with zipfile.ZipFile(self.made.zip_path) as zf:
            self.infos = {i.filename: i for i in zf.infolist()}
            self.data = {name: zf.read(name) for name in self.infos}

    def mode(self, name: str) -> int:
        return self.infos[f"{FOLDER}/{name}"].external_attr >> 16

    def file(self, name: str) -> bytes:
        return self.data[f"{FOLDER}/{name}"]

    def test_name_and_folder(self):
        self.assertEqual(self.made.zip_path.name, f"sovietdoom-{VERSION}-macos.zip")
        self.assertTrue(all(name.startswith(FOLDER + "/") for name in self.infos))
        for name in (*MAC_LAUNCHERS, "freedoom2.wad", "sovietdoom.pk3",
                     "README-FIRST.txt", "GZDOOM-SOURCE.txt", "SHA256SUMS", "LICENSE.md",
                     "LICENSE-GPL-3.0.txt", "gzdoom-licenses/gpl.txt",
                     "gzdoom-licenses/bsd.txt"):
            self.assertIn(f"{FOLDER}/{name}", self.infos, name)

    def test_every_app_entry_keeps_its_bytes_and_its_external_attr(self):
        for name, mode, data in FAKE_MAC:
            if not name.startswith("GZDoom.app"):
                continue
            info = self.infos[f"{FOLDER}/{name}"]
            self.assertEqual(info.external_attr >> 16, mode, name)
            self.assertEqual(info.create_system, 3, name)
            self.assertEqual(self.data[info.filename], data, name)

    def test_the_executable_stays_755_and_symlinks_stay_symlinks(self):
        self.assertEqual(self.mode("GZDoom.app/Contents/MacOS/gzdoom"), S_EXEC)
        for name, target in (("GZDoom.app/Contents/Frameworks/libfoo.dylib", b"libfoo.1.dylib"),
                             ("GZDoom.app/Contents/Current", b"MacOS")):
            self.assertTrue(stat.S_ISLNK(self.mode(name)), name)
            self.assertEqual(self.file(name), target)
        self.assertTrue(stat.S_ISDIR(self.mode("GZDoom.app/Contents/MacOS/")))

    def test_the_appledouble_signatures_ship_beside_their_files(self):
        self.assertEqual(self.file("GZDoom.app/Contents/MacOS/._gzdoom.pk3"), APPLEDOUBLE)

    def test_junk_outside_the_app_is_not_packed(self):
        self.assertFalse(any("__MACOSX" in name for name in self.infos))
        self.assertTrue(any("__MACOSX" in w for w in self.made.warnings))

    def test_the_launchers(self):
        for name in MAC_LAUNCHERS:
            self.assertEqual(self.mode(name), S_EXEC, name)
            lines = self.assert_launcher(self.file(name), "GZDoom.app/Contents/MacOS/gzdoom")
            self.assertIn("  read -r _", lines)       # the Terminal window waits
        self.assertIn(b"Unzip the package", self.file(MAC_LAUNCHERS[0]))
        self.assertEqual(sorted(n for n in self.infos if n.endswith(".command")),
                         [f"{FOLDER}/{name}" for name in MAC_LAUNCHERS])

    def test_our_files_are_644(self):
        for name in ("README-FIRST.txt", "freedoom2.wad", "sovietdoom.pk3", "SHA256SUMS",
                     "gzdoom-licenses/gpl.txt"):
            self.assertEqual(self.mode(name), S_FILE, name)

    def test_the_guide_explains_gatekeeper(self):
        self.assertNotIn(f"{FOLDER}/LEEME.txt", self.infos)      # D129: no Spanish guide
        data = self.file("README-FIRST.txt")
        self.assertTrue(data.startswith(rp.UTF8_BOM))
        self.assertNotIn(b"\r", data)
        en = data.decode("utf-8-sig")
        self.assertIn("xattr -dr com.apple.quarantine", en)
        self.assertIn("macOS 10.15", en)          # LSMinimumSystemVersion
        self.assertIn("Options > Soviet Doom > Language > Russian or Catalan.", en)
        self.assertIn(f"sovietdoom-{VERSION}-macos.zip", en)
        self.assertIn("gzdoom.ini", en)
        self.assertIn("Open Anyway", en)
        self.assertIn("Play Soviet Doom.command", en)

    def test_the_readme_note_says_macos(self):
        self.assertIn(b"PORTABLE MACOS PACKAGE", self.file("README.txt"))

    def test_the_source_file(self):
        source = self.file("GZDOOM-SOURCE.txt").decode("utf-8")
        self.assertNotIn("\r", source)
        self.assertIn("macOS (Intel and Apple\nsilicon)", source)
        self.assertIn("https://github.com/kahache/soviet_doom/releases/tag/v1.0", source)
        self.assertIn("zmusic-1.1.14-source.tar.gz", source)
        self.assertIn("MoltenVK", source)
        self.assertIn("WRITTEN OFFER", source)
        exe = dict((n, d) for n, _, d in FAKE_MAC)["GZDoom.app/Contents/MacOS/gzdoom"]
        self.assertIn(f"{hashlib.sha256(exe).hexdigest()}  GZDoom.app/Contents/MacOS/gzdoom",
                      source)

    def test_sha256sums_skips_only_the_appledouble_files(self):
        lines = self.file("SHA256SUMS").decode("ascii").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
        regular = {i.filename.split("/", 1)[1] for i in self.infos.values()
                   if stat.S_ISREG(i.external_attr >> 16)}
        expected = {n for n in regular if n != "SHA256SUMS" and "/._" not in n}
        self.assertEqual(set(listed), expected)
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256(self.file(name)).hexdigest(), digest, name)

    def test_deterministic_with_the_release_timestamp(self):
        again = rp.make_portable(self.mac_config("mac2"))
        self.assertEqual(again.zip_path.read_bytes(), self.made.zip_path.read_bytes())
        self.assertEqual({i.date_time for i in self.infos.values()}, {STAMP})
        names = list(self.infos)
        self.assertEqual(names, sorted(names))

    def test_the_sha256_beside_the_zip(self):
        digest = hashlib.sha256(self.made.zip_path.read_bytes()).hexdigest()
        self.assertEqual(self.made.sha_path.read_text(encoding="ascii"),
                         f"{digest}  sovietdoom-{VERSION}-macos.zip\n")


class MacosRefusalTest(UnixInputs):

    def with_mac(self, entries) -> rp.Config:
        self.mac_zip.write_bytes(fake_macos_zip(entries))
        return self.mac_config()

    def test_no_engine_archive(self):
        self.assert_refused(self.mac_config(engine_archive=None), "--engine-archive not found")

    def test_another_gzdoom_version(self):
        plist = plistlib.dumps({"CFBundleShortVersionString": "g4.12.2"})
        entries = [(n, m, plist if n.endswith("Info.plist") else d) for n, m, d in FAKE_MAC]
        self.assert_refused(self.with_mac(entries), "does not say g4.14.2")

    def test_a_symlink_that_leaves_the_app(self):
        entries = FAKE_MAC + [("GZDoom.app/Contents/evil", S_LINK, b"../../../etc/passwd")]
        self.assert_refused(self.with_mac(entries), "leaves GZDoom.app/")

    def test_an_absolute_symlink(self):
        entries = FAKE_MAC + [("GZDoom.app/Contents/evil", S_LINK, b"/etc/passwd")]
        self.assert_refused(self.with_mac(entries), "leaves GZDoom.app/")

    def test_an_unsafe_path(self):
        entries = FAKE_MAC + [("GZDoom.app/../../evil", S_FILE, b"x")]
        self.assert_refused(self.with_mac(entries), "unsafe path")

    def test_an_executable_without_its_bit(self):
        entries = [(n, S_FILE if n.endswith("MacOS/gzdoom") else m, d) for n, m, d in FAKE_MAC]
        self.assert_refused(self.with_mac(entries), "is not executable")

    def test_no_licences(self):
        entries = [e for e in FAKE_MAC if not e[0].startswith("Licenses")]
        self.assert_refused(self.with_mac(entries), "licence texts")


class LinuxPackageTest(UnixInputs):

    def setUp(self) -> None:
        super().setUp()
        self.made = rp.make_portable(self.linux_config())
        self.raw = self.made.zip_path.read_bytes()
        with tarfile.open(self.made.zip_path) as tf:
            self.members = {m.name: m for m in tf.getmembers()}
            self.data = {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isreg()}

    def member(self, name: str) -> tarfile.TarInfo:
        return self.members[f"{FOLDER}/{name}"] if name else self.members[FOLDER]

    def file(self, name: str) -> bytes:
        return self.data[f"{FOLDER}/{name}"]

    def test_name_and_folder(self):
        self.assertEqual(self.made.zip_path.name, f"sovietdoom-{VERSION}-linux.tar.gz")
        self.assertTrue(all(n == FOLDER or n.startswith(FOLDER + "/") for n in self.members))
        for name in (*LINUX_LAUNCHERS, "freedoom2.wad", "sovietdoom.pk3",
                     "README-FIRST.txt", "GZDOOM-SOURCE.txt", "SHA256SUMS",
                     "gzdoom/gzdoom", "gzdoom/gzdoom.pk3", "gzdoom/libzmusic.so.1",
                     "gzdoom/soundfonts/gzdoom.sf2", "gzdoom-licenses/gpl.txt",
                     "gzdoom-licenses/bsd.txt"):
            self.assertIn(f"{FOLDER}/{name}", self.members, name)

    def test_only_opt_gzdoom_is_packed(self):
        self.assertFalse(any("usr/games" in n for n in self.members))
        self.assertTrue(any("/usr/games/gzdoom" in w for w in self.made.warnings))
        self.assertNotIn(f"{FOLDER}/gzdoom-licenses/d_main.cpp", self.members)

    def test_modes(self):
        for name, member in self.members.items():
            if member.isdir():
                self.assertEqual(member.mode, 0o755, name)
        for name in ("gzdoom/gzdoom", *LINUX_LAUNCHERS):
            self.assertEqual(self.member(name).mode, 0o755, name)
        for name in ("gzdoom/gzdoom.pk3", "gzdoom/libzmusic.so.1", "README-FIRST.txt",
                     "freedoom2.wad", "gzdoom/soundfonts/gzdoom.sf2"):   # 664 in the .deb
            self.assertEqual(self.member(name).mode, 0o644, name)

    def test_every_parent_folder_is_an_entry(self):
        for name in self.members:
            parent = name.rsplit("/", 1)[0]
            if "/" in name:
                self.assertTrue(self.members[parent].isdir(), parent)

    def test_symlinks_stay_symlinks(self):
        link = self.member("gzdoom/libzmusic.so")
        self.assertTrue(link.issym())
        self.assertEqual(link.linkname, "libzmusic.so.1")

    def test_owner_mtime_and_gzip_header_are_fixed(self):
        mtime = calendar.timegm((*STAMP, 0, 0, 0))
        for name, member in self.members.items():
            self.assertEqual((member.uid, member.gid, member.uname, member.gname),
                             (0, 0, "root", "root"), name)
            self.assertEqual(member.mtime, mtime, name)
        self.assertEqual(self.raw[:3], b"\x1f\x8b\x08")
        self.assertEqual(self.raw[3] & 0x08, 0, "no file name in the gzip header")
        self.assertEqual(self.raw[4:8], b"\x00\x00\x00\x00", "no time in the gzip header")

    def test_deterministic(self):
        again = rp.make_portable(self.linux_config("linux2"))
        self.assertEqual(again.zip_path.read_bytes(), self.raw)
        names = list(self.members)
        self.assertEqual(names, sorted(names))

    def test_the_launchers(self):
        for name in LINUX_LAUNCHERS:
            lines = self.assert_launcher(self.file(name), "gzdoom/gzdoom")
            self.assertNotIn("  read -r _", lines)
        self.assertIn(f"tar xzf sovietdoom-{VERSION}-linux.tar.gz".encode(),
                      self.file("play.sh"))

    def test_the_guide_lists_the_debs_dependencies_and_the_apt_command(self):
        self.assertNotIn(f"{FOLDER}/LEEME.txt", self.members)    # D129: no Spanish guide
        self.assertNotIn(f"{FOLDER}/jugar.sh", self.members)
        for name in ("README-FIRST.txt",):
            data = self.file(name)
            self.assertFalse(data.startswith(rp.UTF8_BOM), name)
            text = data.decode("utf-8")
            self.assertIn("libc6, libsdl2-2.0-0, libasound2, libopus0", text)
            apt = text[text.index("sudo apt install"):].split("\n")
            command = ""
            for line in apt:
                command += line.strip().rstrip("\\")
                if not line.endswith("\\"):
                    break
            self.assertEqual(command.split(), ["sudo", "apt", "install", "libc6",
                                               "libsdl2-2.0-0", "libasound2", "libopus0",
                                               "libopenal1", "libsndfile1"])
            self.assertIn("libasound2t64", text)
            self.assertIn("./play.sh", text)
            self.assertIn("Options > Soviet Doom > Language > Russian or Catalan.", text)

    def test_the_source_file_and_the_licences(self):
        source = self.file("GZDOOM-SOURCE.txt").decode("utf-8")
        self.assertIn("for Linux (x86-64", source)
        self.assertIn("libzmusic.so.1", source)
        self.assertIn("https://github.com/kahache/soviet_doom/releases/tag/v1.0", source)
        self.assertIn(f"{hashlib.sha256(b'PK engine').hexdigest()}  gzdoom/gzdoom.pk3", source)
        self.assertEqual(self.file("gzdoom-licenses/gpl.txt"), b"GNU GPL 3")

    def test_sha256sums(self):
        lines = self.file("SHA256SUMS").decode("ascii").splitlines()
        listed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
        regular = {n.split("/", 1)[1] for n in self.data}
        self.assertEqual(set(listed), regular - {"SHA256SUMS"})
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256(self.file(name)).hexdigest(), digest, name)


class LinuxRefusalTest(UnixInputs):

    def test_no_source_archive(self):
        self.assert_refused(self.linux_config(gzdoom_source=None), "--gzdoom-source not found")

    def test_a_source_archive_of_another_version(self):
        self.source.write_bytes(fake_tar([("gzdoom-g4.12.2/docs/licenses/gpl.txt",
                                           tarfile.REGTYPE, 0o644, b"GPL")], mode="w:gz"))
        self.assert_refused(self.linux_config(), "is not GZDoom g4.14.2's source")

    def test_another_deb_version(self):
        self.deb.write_bytes(fake_deb(FAKE_CONTROL.replace("4.14.2", "4.12.2")))
        self.assert_refused(self.linux_config(), "is not GZDoom g4.14.2")

    def test_not_an_ar_archive(self):
        self.deb.write_bytes(b"PK not a deb")
        self.assert_refused(self.linux_config(), "no ar header")

    def test_a_cut_ar_archive(self):
        self.deb.write_bytes(fake_deb()[:-100])
        self.assert_refused(self.linux_config(), "cut short")

    def test_a_symlink_that_leaves_the_engine(self):
        data = FAKE_DEB_DATA + [("./opt/gzdoom/evil", tarfile.SYMTYPE, 0o777, b"../../etc/x")]
        self.deb.write_bytes(fake_deb(data=data))
        self.assert_refused(self.linux_config(), "leaves gzdoom/")

    def test_a_device_or_hard_link(self):
        data = FAKE_DEB_DATA + [("./opt/gzdoom/hard", tarfile.LNKTYPE, 0o644, b"gzdoom")]
        self.deb.write_bytes(fake_deb(data=data))
        self.assert_refused(self.linux_config(), "neither a file")

    def test_the_cli_builds_linux(self):
        out = self.root / "cli"
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()) as printed:
            code = rp.main(["--platform", "linux", "--version", VERSION, "--out", str(out),
                            "--iwad", str(self.iwad), "--release-zip", str(self.release_zip),
                            "--engine-archive", str(self.deb),
                            "--gzdoom-source", str(self.source)])
        self.assertEqual(code, rp.EXIT_OK)
        self.assertTrue((out / f"sovietdoom-{VERSION}-linux.tar.gz").is_file())
        self.assertIn("SovietDoom/play.sh", printed.getvalue())


class DebHelpersTest(unittest.TestCase):

    def test_parse_control_joins_continuation_lines(self):
        fields = rp.parse_control(FAKE_CONTROL)
        self.assertEqual(fields["Version"], "4.14.2")
        self.assertEqual(fields["Description"], "OpenGL version of ZDoom. A second line.")

    def test_deb_packages_drops_versions_alternatives_and_arch(self):
        self.assertEqual(rp.deb_packages("libc6, libsdl2-2.0-0 (>= 2.0.8), "
                                         "libasound2 | libasound2t64, libopus0:amd64"),
                         ["libc6", "libsdl2-2.0-0", "libasound2", "libopus0"])
        self.assertEqual(rp.deb_packages(""), [])

    def test_read_ar(self):
        members = rp.read_ar(ar_archive([("a", b"odd"), ("b/", b"even")]), "t")
        self.assertEqual(members, {"a": b"odd", "b": b"even"})

    def test_apt_command_lines_end_in_backslashes(self):
        text = rp.apt_command([f"libpackage{i}" for i in range(20)])
        lines = text.split("\n")
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(line.endswith(" \\") for line in lines[:-1]))
        self.assertTrue(all(len(line) <= 76 for line in lines))

    def test_safe_path(self):
        self.assertEqual(rp.safe_path("./opt/gzdoom/", "t"), "opt/gzdoom")
        for bad in ("/etc/passwd", "a/../b", "..", "a\\b", "C:/x", "a//b"):
            with self.assertRaises(rp.PortableError, msg=bad):
                rp.safe_path(bad, "t")


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
