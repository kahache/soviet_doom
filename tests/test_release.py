"""Tests for tools/release.py, the G6 distribution zip (docs/engine/RELEASE.md).

What is pinned:

  * the real release, made twice into temp dirs (`dist/` is never touched):
    the exact member list, the PK3 inside it, LICENSE.md verbatim, the
    generated CREDITS.txt and README.txt, SHA256SUMS, the .sha256 beside it;
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

import release  # noqa: E402

VERSION = "0.0-test"
FOLDER = f"{release.MOD_NAME}-{VERSION}"


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

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_the_zip_is_named_after_the_version_in_its_folder(self):
        self.assertEqual(self.first.zip_path.name, f"{FOLDER}.zip")
        self.assertEqual(self.first.zip_path.parent.name, "a")

    def test_the_zip_holds_exactly_the_five_files_in_one_folder(self):
        self.assertEqual([i.filename for i in self.infos],
                         [f"{FOLDER}/{name}" for name in sorted(release.RELEASE_FILES)])
        self.assertEqual(sorted(self.files),
                         sorted(["sovietdoom.pk3", "LICENSE.md", "CREDITS.txt", "README.txt",
                                 "SHA256SUMS"]))

    def test_the_pk3_is_a_full_build(self):
        for lump in ("MAPINFO", "LANGUAGE", "zscript.txt", "maps/MAP01.wad", "maps/MAP02.wad"):
            self.assertIn(lump, self.pk3_names)
        self.assertTrue(any(n.startswith("textures/") for n in self.pk3_names))

    def test_licence_is_the_repo_file_verbatim(self):
        self.assertEqual(self.files[release.LICENCE_NAME],
                         (PROJECT_ROOT / "LICENSE.md").read_text(encoding="utf-8").encode("utf-8"))

    def test_sha256sums_lists_the_four_other_files_correctly(self):
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
        self.assertFalse(any("freedoom" in n.lower() for n in names))
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

    def test_credits_carry_the_in_game_credits_in_both_languages(self):
        credits = release.parse_credit_lines(self.language)
        for lang in (release.LANG_ENGLISH, release.LANG_RUSSIAN):
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
