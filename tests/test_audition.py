"""Tests for tools/audio/audition.py: the engine gate (D26), the overlay
PK3, the engine command lines and the WAV measurement.

What is tested, and how, without ever starting GZDoom (D26):

- The engine gate: --play and --render refuse unless SD_ALLOW_ENGINE=1.
  Found 2026-10-13: the gate existed in tools/smoke.py and tools/run.sh and
  not here.
- `pack()`: which entries the overlay PK3 holds, in which order, their
  lump names, the MAPINFO it writes, the fixed zip date (byte-reproducible),
  and the `--candidates` numbering and manifest.
- The argv of `--play` and `--render`, built for real and handed to a fake
  `subprocess` that records it. Nothing is ever executed: every test case
  replaces `audition.subprocess` with a stub that raises if called, and a
  test that needs a "process" supplies its own fake on top.
- `--render`'s verdict, driven by a fake engine that writes WAV files where
  the console command told it to.
- `measure_wav()` on synthetic RIFF files (PCM 8/16 and IEEE float, plain
  and WAVE_FORMAT_EXTENSIBLE, which is what `writewave` emits).
- GZDoom and IWAD discovery on macOS and Windows, and the errors when
  something is missing. The gate is opened by patching `engine_allowed`,
  never by setting SD_ALLOW_ENGINE.
- `main()`: argument wiring and `--expect` parsing.

Every path constant of the module is redirected into a temporary directory
(`SandboxedCase`), so nothing here writes to work/, dist/ or logs/. The
tests that read the real MIDIs under work/audio/ skip when they are absent
(CI has no work/), like the Lenin photograph in tests/test_generators.py.
As a tripwire, the module hashes work/audio/ before the first test and
after the last one, and errors out if anything there changed.

Known defects in audition.py are pinned as `expectedFailure` with their
repro in the docstring; they belong to sound-designer and are not fixed
here (QA reports, does not fix).

Run:  python3 -m unittest tests.test_audition -v
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import os
import re
import struct
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AUDITION_PY = PROJECT_ROOT / "tools" / "audio" / "audition.py"
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import audition  # noqa: E402
from sdbuild.wad import WadError, validate_lump_name  # noqa: E402

# The real drafts and candidates: work/ is gitignored, so these exist on the
# working machines and not in CI.
REAL_AUDIO_DIR = PROJECT_ROOT / "work" / "audio"
REAL_CANDIDATES_DIR = REAL_AUDIO_DIR / "candidates"
REAL_MANIFEST = REAL_AUDIO_DIR / "candidates-lumps.txt"
HAVE_REAL_DRAFTS = any(REAL_AUDIO_DIR.glob("*.mid")) if REAL_AUDIO_DIR.is_dir() else False
HAVE_REAL_CANDIDATES = (any(REAL_CANDIDATES_DIR.glob("*.mid"))
                        if REAL_CANDIDATES_DIR.is_dir() else False)
real_drafts = unittest.skipUnless(
    HAVE_REAL_DRAFTS,
    f"no draft MIDIs ({REAL_AUDIO_DIR.relative_to(PROJECT_ROOT)} is under gitignored work/)")
real_candidates = unittest.skipUnless(
    HAVE_REAL_CANDIDATES,
    f"no candidate MIDIs ({REAL_CANDIDATES_DIR.relative_to(PROJECT_ROOT)} is under gitignored work/)")

MIDI_MAGIC = b"MThd"
FAKE_RATE = 1000            # Hz; small synthetic WAVs, the arithmetic is the same


# --- work/audio tripwire -----------------------------------------------------

def tree_digest(root: Path) -> str | None:
    """SHA-256 over every file under root (relative path + content), or None."""
    if not root.is_dir():
        return None
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(root).as_posix().encode())
            h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


_WORK_AUDIO_BEFORE: str | None = None


def setUpModule():
    global _WORK_AUDIO_BEFORE
    _WORK_AUDIO_BEFORE = tree_digest(REAL_AUDIO_DIR)


def tearDownModule():
    after = tree_digest(REAL_AUDIO_DIR)
    if after != _WORK_AUDIO_BEFORE:
        raise AssertionError(f"tests/test_audition.py changed {REAL_AUDIO_DIR}: "
                             f"digest {_WORK_AUDIO_BEFORE} -> {after}")


# --- helpers -----------------------------------------------------------------

def write_mids(folder: Path, names) -> dict[str, bytes]:
    """Distinct fake MIDI bytes per file; pack() copies bytes, never parses."""
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    for n in names:
        data = MIDI_MAGIC + n.encode()
        (folder / n).write_bytes(data)
        out[n] = data
    return out


def riff(fmt: bytes, data: bytes, extra_chunks: bytes = b"") -> bytes:
    body = b"WAVE" + chunk(b"fmt ", fmt) + extra_chunks + chunk(b"data", data)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def chunk(cid: bytes, body: bytes) -> bytes:
    return cid + struct.pack("<I", len(body)) + body + (b"\x00" if len(body) & 1 else b"")


def fmt_basic(tag: int, channels: int, rate: int, bits: int) -> bytes:
    align = channels * bits // 8
    return struct.pack("<HHIIHH", tag, channels, rate, rate * align, align, bits)


def fmt_extensible_float(channels: int, rate: int) -> bytes:
    """The fmt chunk GZDoom's writewave emits: EXTENSIBLE, IEEE-float subformat."""
    subformat = struct.pack("<H", audition.WAV_FORMAT_IEEE_FLOAT) + \
        b"\x00\x00\x00\x00\x10\x00\x80\x00\x00\xaa\x00\x38\x9b\x71"
    return (fmt_basic(audition.WAV_FORMAT_EXTENSIBLE, channels, rate, 32)
            + struct.pack("<HHI", 22, 32, 3) + subformat)


def pcm16_wav(seconds: float, peak: float, rate: int = FAKE_RATE, channels: int = 1) -> bytes:
    frames = int(seconds * rate)
    samples = [0] * (frames * channels)
    if samples:
        samples[len(samples) // 2] = int(peak * 32767)
    data = struct.pack(f"<{len(samples)}h", *samples)
    return riff(fmt_basic(audition.WAV_FORMAT_PCM, channels, rate, 16), data)


def float_ext_wav(seconds: float, peak: float, rate: int = FAKE_RATE, channels: int = 2) -> bytes:
    frames = int(seconds * rate)
    samples = [0.0] * (frames * channels)
    if samples:
        samples[1] = -peak
    data = struct.pack(f"<{len(samples)}f", *samples)
    return riff(fmt_extensible_float(channels, rate), data)


def load_fresh_audition(env: dict[str, str]) -> types.ModuleType:
    """Execute audition.py again under `env`, as a separate module object.

    GZDOOM_CANDIDATES is computed at import time from LOCALAPPDATA and
    ProgramFiles, so the Windows discovery can only be observed by importing
    under a controlled environment. The copy is not put in sys.modules and
    the shared `audition` module is untouched.
    """
    spec = importlib.util.spec_from_file_location("audition_fresh_copy", AUDITION_PY)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, env, clear=True):
        spec.loader.exec_module(module)
    return module


def _no_process(*args, **kwargs):
    raise AssertionError(f"audition tried to start a process: {args!r}")


class SandboxedCase(unittest.TestCase):
    """Every path audition.py reads or writes, moved into a tempdir.

    Also: `audition.subprocess` is a stub whose `call`/`run` raise, stdout
    and stderr are captured, and `require_engine` returns fake paths unless a
    test restores it (the engine gate itself is tested in EngineGateTests).
    """

    fake_engine = True

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.audio = self.tmp / "work" / "audio"
        self.candidates = self.audio / "candidates"
        self.logs = self.tmp / "logs"
        self.mod_pk3 = self.tmp / "dist" / "sovietdoom.pk3"
        self.test_pk3 = self.audio / "sd-music-draft.pk3"
        for name, value in (("AUDIO_DIR", self.audio), ("CANDIDATES_DIR", self.candidates),
                            ("TEST_PK3", self.test_pk3), ("MOD_PK3", self.mod_pk3),
                            ("LOG_DIR", self.logs),
                            ("TOOLING_CONFIG", self.logs / "gzdoom-tooling.ini")):
            self.enterContext(mock.patch.object(audition, name, value))
        self.proc = types.SimpleNamespace(
            call=mock.Mock(side_effect=_no_process), run=mock.Mock(side_effect=_no_process),
            TimeoutExpired=subprocess.TimeoutExpired)
        self.enterContext(mock.patch.object(audition, "subprocess", self.proc))
        self.out = self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.err = self.enterContext(contextlib.redirect_stderr(io.StringIO()))
        self.gzdoom = self.tmp / "engine" / "gzdoom.exe"
        self.iwad = self.tmp / "iwads" / "freedoom2.wad"
        if self.fake_engine:
            self.enterContext(mock.patch.object(audition, "require_engine",
                                                return_value=(self.gzdoom, self.iwad)))

    def packed(self) -> zipfile.ZipFile:
        zf = zipfile.ZipFile(self.test_pk3)
        self.addCleanup(zf.close)
        return zf

    def mapinfo(self) -> str:
        return self.packed().read("MAPINFO").decode()


# --- the engine gate (D26) ---------------------------------------------------

class EngineGateTests(unittest.TestCase):
    def test_gate_is_closed_without_the_variable(self):
        self.assertFalse(audition.engine_allowed({}))
        self.assertFalse(audition.engine_allowed({"SD_ALLOW_ENGINE": "0"}))
        self.assertFalse(audition.engine_allowed({"SD_ALLOW_ENGINE": "yes"}))

    def test_gate_opens_only_on_exactly_one(self):
        self.assertTrue(audition.engine_allowed({"SD_ALLOW_ENGINE": "1"}))

    def test_require_engine_refuses_before_looking_for_anything(self):
        env = {k: v for k, v in os.environ.items() if k != "SD_ALLOW_ENGINE"}
        with (mock.patch.dict(os.environ, env, clear=True),
              mock.patch.object(audition, "find", side_effect=AssertionError("must not search")),
              contextlib.redirect_stderr(io.StringIO()) as err):
            with self.assertRaises(SystemExit) as ctx:
                audition.require_engine()
        self.assertEqual(audition.EXIT_ENGINE_BLOCKED, ctx.exception.code)
        self.assertIn("SD_ALLOW_ENGINE", err.getvalue())

    def test_play_and_render_both_pass_through_the_gate(self):
        """Both commands that start GZDoom must call require_engine first."""
        for name in ("cmd_play", "cmd_render"):
            with self.subTest(command=name):
                with (mock.patch.object(audition, "require_engine",
                                        side_effect=SystemExit(audition.EXIT_ENGINE_BLOCKED)),
                      mock.patch.object(audition, "pack",
                                        side_effect=AssertionError("packed before the gate"))):
                    with self.assertRaises(SystemExit):
                        if name == "cmd_play":
                            audition.cmd_play("title")
                        else:
                            audition.cmd_render({})

    def test_main_play_without_the_gate_starts_nothing(self):
        env = {k: v for k, v in os.environ.items() if k != "SD_ALLOW_ENGINE"}
        proc = types.SimpleNamespace(call=mock.Mock(side_effect=_no_process),
                                     run=mock.Mock(side_effect=_no_process))
        for argv in (["--play", "title"], ["--play", "map01"], ["--render"]):
            with self.subTest(argv=argv):
                with (mock.patch.dict(os.environ, env, clear=True),
                      mock.patch.object(audition, "subprocess", proc),
                      mock.patch.object(audition, "pack",
                                        side_effect=AssertionError("packed before the gate")),
                      contextlib.redirect_stderr(io.StringIO())):
                    with self.assertRaises(SystemExit) as ctx:
                        audition.main(argv)
                self.assertEqual(audition.EXIT_ENGINE_BLOCKED, ctx.exception.code)
        proc.call.assert_not_called()
        proc.run.assert_not_called()


# --- pack() ------------------------------------------------------------------

class PackDraftsTests(SandboxedCase):
    DRAFTS = ("D_SDTITL.mid", "D_SDM01.mid", "D_SDFIX3.mid")

    def setUp(self):
        super().setUp()
        self.data = write_mids(self.audio, self.DRAFTS)

    def test_mapinfo_first_then_music_sorted_by_file_name(self):
        pairs = audition.pack()
        self.assertEqual([("D_SDFIX3", "D_SDFIX3.mid"), ("D_SDM01", "D_SDM01.mid"),
                          ("D_SDTITL", "D_SDTITL.mid")],
                         [(lump, p.name) for lump, p in pairs])
        self.assertEqual(["MAPINFO", "music/D_SDFIX3.mid", "music/D_SDM01.mid",
                          "music/D_SDTITL.mid"], self.packed().namelist())

    def test_music_bytes_are_copied_verbatim(self):
        audition.pack()
        zf = self.packed()
        for name, data in self.data.items():
            self.assertEqual(data, zf.read(f"{audition.MUSIC_DIR_IN_PK3}/{name}"))

    def test_lump_names_are_the_file_stems_and_valid_doom_lumps(self):
        for lump, p in audition.pack(quiet=True):
            self.assertEqual(p.stem, lump)
            self.assertEqual(lump, validate_lump_name(lump))     # <=8, ASCII, uppercase

    def test_mapinfo_points_title_and_map01_at_the_fixed_lumps(self):
        audition.pack()
        text = self.mapinfo()
        self.assertIn(f'TitleMusic = "{audition.TITLE_LUMP}"', text)
        self.assertIn(f'music = "{audition.MAP01_LUMP}"', text)
        self.assertIn('map MAP01 lookup "SD_MAP01_NAME"', text)
        self.assertNotIn("{{", text)                         # format() consumed the escapes
        self.assertEqual(text.count("{"), text.count("}"))

    def test_lump_overrides_title_and_map01(self):
        audition.pack(first_lump="D_SDFIX3")
        text = self.mapinfo()
        self.assertIn('TitleMusic = "D_SDFIX3"', text)
        self.assertIn('music = "D_SDFIX3"', text)

    def test_fixed_date_and_deflate_on_every_entry(self):
        audition.pack()
        for info in self.packed().infolist():
            with self.subTest(entry=info.filename):
                self.assertEqual(audition.FIXED_ZIP_TIME, info.date_time)
                self.assertEqual(zipfile.ZIP_DEFLATED, info.compress_type)

    def test_pack_is_byte_reproducible_regardless_of_file_times(self):
        audition.pack()
        first = self.test_pk3.read_bytes()
        for name in self.DRAFTS:                  # new mtimes must not leak into the zip
            os.utime(self.audio / name, (2_000_000_000, 2_000_000_000))
        self.test_pk3.unlink()
        audition.pack()
        self.assertEqual(first, self.test_pk3.read_bytes())

    def test_drafts_mode_writes_only_the_pk3(self):
        before = {p for p in self.tmp.rglob("*") if p.is_file()}
        audition.pack()
        after = {p for p in self.tmp.rglob("*") if p.is_file()}
        self.assertEqual({self.test_pk3}, after - before)

    def test_reports_the_mapping_unless_quiet(self):
        audition.pack()
        printed = self.out.getvalue()
        self.assertIn(str(self.test_pk3), printed)
        self.assertIn("title/MAP01 = D_SDTITL", printed)
        self.assertIn("D_SDM01  D_SDM01.mid", printed)
        self.out.seek(0)
        self.out.truncate()
        audition.pack(quiet=True)
        self.assertEqual("", self.out.getvalue())

    def test_no_drafts_is_a_clear_error(self):
        for name in self.DRAFTS:
            (self.audio / name).unlink()
        with self.assertRaises(SystemExit) as ctx:
            audition.pack()
        self.assertIn(str(self.audio), str(ctx.exception.code))
        self.assertIn("gen_music.py", str(ctx.exception.code))
        self.assertFalse(self.test_pk3.exists())

    @unittest.expectedFailure
    def test_lump_that_is_not_packed_is_refused(self):
        """BUG A2 (sound-designer). --lump is not checked against the pack.

        Repro: `audition.py --play map01 --candidates --lump D_CND13` with
        twelve candidates. Expected: a clear error before the engine starts.
        Observed: pack() writes a MAPINFO whose TitleMusic and MAP01 music
        name a lump that is not in the PK3, and --play launches GZDoom into
        silence: the exact symptom this tool exists to rule out. Same for a
        typo such as `--lump D_CNDl1`.
        """
        with self.assertRaises(SystemExit):
            audition.pack(first_lump="D_NOPE")

    @unittest.expectedFailure
    def test_draft_whose_stem_is_not_a_lump_name_is_refused(self):
        """BUG A6 (sound-designer). Draft stems are used as lump names unchecked.

        Repro: put `work/audio/D_SDMENU2.mid` next to the drafts (9-char
        stem) and run `audition.py --pack`. Expected: a clear error, as
        tools/sdbuild/pk3.py gives for src/lumps (validate_lump_name).
        Observed: packed as music/D_SDMENU2.mid. GZDoom truncates PK3 short
        names to 8 characters, so whether `writewave D_SDMENU2` and a MAPINFO
        `music = "D_SDMENU2"` find it is NOT VERIFIED in the engine; the
        tool's own docstring assumes drafts are "already named as lumps".
        """
        write_mids(self.audio, ["D_SDMENU2.mid"])
        with self.assertRaises(SystemExit):
            audition.pack()


class PackCandidatesTests(SandboxedCase):
    # Real downloads have long names with punctuation; none is a lump name.
    NAMES = ("WM_Kolokolchik.mid", "MU_Scriabin_Prelude_op11n1.mid",
             "MU_Tchaikovsky_Seasons_August.mid", "notes.txt")

    def setUp(self):
        super().setUp()
        self.data = write_mids(self.candidates, self.NAMES)
        write_mids(self.audio, ["D_SDTITL.mid"])        # a draft, must be ignored

    def test_positional_lumps_in_sorted_file_order(self):
        pairs = audition.pack(use_candidates=True)
        self.assertEqual([("D_CND01", "MU_Scriabin_Prelude_op11n1.mid"),
                          ("D_CND02", "MU_Tchaikovsky_Seasons_August.mid"),
                          ("D_CND03", "WM_Kolokolchik.mid")],
                         [(lump, p.name) for lump, p in pairs])
        self.assertEqual(["MAPINFO", "music/D_CND01.mid", "music/D_CND02.mid",
                          "music/D_CND03.mid"], self.packed().namelist())
        self.assertEqual(self.data["WM_Kolokolchik.mid"], self.packed().read("music/D_CND03.mid"))
        for lump, _ in pairs:
            self.assertEqual(lump, validate_lump_name(lump))

    def test_numbering_stays_within_eight_characters_past_ninety_nine(self):
        write_mids(self.candidates, [f"zz_{i:03d}.mid" for i in range(97)])   # 100 in all
        pairs = audition.sources(use_candidates=True)
        self.assertEqual("D_CND100", pairs[-1][0])
        for lump, _ in pairs:
            validate_lump_name(lump)

    def test_default_title_and_map01_is_the_first_candidate(self):
        audition.pack(use_candidates=True)
        text = self.mapinfo()
        self.assertIn('TitleMusic = "D_CND01"', text)
        self.assertIn('music = "D_CND01"', text)

    def test_lump_selects_the_candidate(self):
        audition.pack(use_candidates=True, first_lump="D_CND03")
        self.assertIn('music = "D_CND03"', self.mapinfo())
        self.assertIn("title/MAP01 = D_CND03", self.out.getvalue())

    def test_manifest_maps_lumps_to_files_next_to_the_pk3(self):
        audition.pack(use_candidates=True)
        manifest = self.audio / "candidates-lumps.txt"
        self.assertEqual("D_CND01  MU_Scriabin_Prelude_op11n1.mid\n"
                         "D_CND02  MU_Tchaikovsky_Seasons_August.mid\n"
                         "D_CND03  WM_Kolokolchik.mid\n",
                         manifest.read_text())
        self.assertEqual(manifest.parent, self.test_pk3.parent)

    def test_no_candidates_is_a_clear_error(self):
        for name in self.NAMES:
            (self.candidates / name).unlink()
        with self.assertRaises(SystemExit) as ctx:
            audition.pack(use_candidates=True)
        self.assertIn(str(self.candidates), str(ctx.exception.code))

    @unittest.expectedFailure
    def test_numbering_does_not_depend_on_the_operating_system(self):
        """BUG A5 (sound-designer). D_CNDnn depends on the OS's path ordering.

        sources() sorts Path objects. WindowsPath compares case-insensitively,
        PosixPath (the Mac) by code point, so the same folder can number
        differently on the two machines, and "D_CND11" in a message, in the
        manifest or in a CEO verdict names a different piece.
        Repro (this PC): put `a.mid` and `B.mid` in work/audio/candidates/
        and run `audition.py --pack --candidates`: D_CND01 = a.mid. The same
        on the Mac gives D_CND01 = B.mid (from PurePosixPath ordering; not
        run on the Mac). Latent today: the current twelve candidates number
        the same on both (see RealMidiTests). Simulated here with pure paths,
        so it reproduces on any OS.
        """
        names = ["a_piece.mid", "B_piece.mid", "WM_x.mid", "WMa.mid"]

        def numbering(flavour):
            folder = mock.Mock()
            folder.glob.return_value = [flavour(n) for n in names]
            with mock.patch.object(audition, "CANDIDATES_DIR", folder):
                return {p.name: lump for lump, p in audition.sources(use_candidates=True)}

        self.assertEqual(numbering(PurePosixPath), numbering(PureWindowsPath))


# --- --play ------------------------------------------------------------------

class PlayCommandTests(SandboxedCase):
    def setUp(self):
        super().setUp()
        write_mids(self.audio, ["D_SDTITL.mid", "D_SDM01.mid"])
        self.seen_pk3 = None

        def fake_call(args):
            self.seen_pk3 = Path(args[args.index(str(self.test_pk3))]).is_file()
            return 0

        self.proc.call.side_effect = fake_call

    def expected_prefix(self) -> list[str]:
        return [str(self.gzdoom),
                "-config", str(self.logs / "gzdoom-tooling.ini"),
                "+snd_musicvolume", "0.8", "+snd_sfxvolume", "0.8",
                "-iwad", str(self.iwad),
                "-file", str(self.mod_pk3), "-file", str(self.test_pk3),
                "+logfile", str(self.logs / "audition.log")]

    def test_title_sits_on_the_title_screen(self):
        self.assertEqual(0, audition.cmd_play("title"))
        (args,), _ = self.proc.call.call_args
        self.assertEqual(self.expected_prefix(), args)
        self.assertNotIn("+map", args)

    def test_map01_warps_to_map01(self):
        audition.cmd_play("map01")
        (args,), _ = self.proc.call.call_args
        self.assertEqual(self.expected_prefix() + ["+map", "MAP01"], args)

    def test_tooling_config_and_explicit_volumes(self):
        """The CEO heard silence with his own gzdoom.ini at snd_musicvolume 0."""
        audition.cmd_play("title")
        (args,), _ = self.proc.call.call_args
        self.assertEqual(str(audition.TOOLING_CONFIG), args[args.index("-config") + 1])
        self.assertEqual("0.8", args[args.index("+snd_musicvolume") + 1])
        self.assertEqual("0.8", args[args.index("+snd_sfxvolume") + 1])

    def test_overlay_loads_after_the_mod_so_its_mapinfo_wins(self):
        audition.cmd_play("map01")
        (args,), _ = self.proc.call.call_args
        self.assertLess(args.index(str(self.mod_pk3)), args.index(str(self.test_pk3)))

    def test_packs_before_launching_and_returns_the_engine_exit_code(self):
        self.proc.call.side_effect = lambda args: 3
        self.assertEqual(3, audition.cmd_play("title"))
        self.assertTrue(self.test_pk3.is_file())
        self.proc.run.assert_not_called()

    def test_pk3_exists_when_the_engine_is_called(self):
        audition.cmd_play("title")
        self.assertTrue(self.seen_pk3)

    def test_prints_the_command_line(self):
        audition.cmd_play("map01")
        self.assertIn(" ".join(self.expected_prefix() + ["+map", "MAP01"]), self.out.getvalue())

    def test_candidates_and_lump_reach_the_overlay(self):
        write_mids(self.candidates, ["first.mid", "second.mid"])
        audition.cmd_play("title", use_candidates=True, lump="D_CND02")
        self.assertIn('TitleMusic = "D_CND02"', self.mapinfo())


# --- --render ----------------------------------------------------------------

WRITEWAVE = re.compile(r'writewave (\S+) "([^"]+)" 0 (\d+)')


class RenderCommandTests(SandboxedCase):
    def setUp(self):
        super().setUp()
        write_mids(self.audio, ["D_SDTITL.mid", "D_SDM01.mid"])
        # lump -> (seconds, peak) the fake engine renders; None = writes nothing
        self.renders: dict[str, tuple[float, float] | None] = {
            "D_SDM01": (10.0, 0.5), "D_SDTITL": (4.0, 0.5)}
        self.proc.run.side_effect = self.fake_engine_run

    def fake_engine_run(self, args, timeout=None, env=None, check=None):
        """Write each WAV where the console told the engine to."""
        for lump, path, _rate in WRITEWAVE.findall(args[-1]):
            spec = self.renders.get(lump)
            if spec is not None:
                Path(path).write_bytes(pcm16_wav(*spec))
        return subprocess.CompletedProcess(args, 0)

    def run_args(self) -> tuple[list[str], dict]:
        (args,), kwargs = self.proc.run.call_args
        return args, kwargs

    def test_loads_only_the_overlay_not_the_mod(self):
        audition.cmd_render({})
        args, _ = self.run_args()
        self.assertEqual(1, args.count("-file"))
        self.assertEqual(str(self.test_pk3), args[args.index("-file") + 1])
        self.assertNotIn(str(self.mod_pk3), args)

    def test_windowed_silent_logged(self):
        audition.cmd_render({})
        args, _ = self.run_args()
        self.assertEqual(str(self.gzdoom), args[0])
        self.assertEqual(str(self.iwad), args[args.index("-iwad") + 1])
        self.assertIn("-nosound", args)
        self.assertEqual("0", args[args.index("+vid_fullscreen") + 1])
        self.assertEqual(str(self.logs / "audition-render.log"), args[args.index("+logfile") + 1])

    def test_console_waits_renders_every_lump_in_pack_order_then_quits(self):
        audition.cmd_render({})
        args, _ = self.run_args()
        out = self.audio / "render"
        self.assertEqual(
            "+" + "; ".join([
                f"wait {audition.RENDER_WAIT_TICS}",
                f'writewave D_SDM01 "{out / "D_SDM01.wav"}" 0 {audition.RENDER_SAMPLE_RATE}',
                f'writewave D_SDTITL "{out / "D_SDTITL.wav"}" 0 {audition.RENDER_SAMPLE_RATE}',
                f"wait {audition.RENDER_SETTLE_TICS}",
                "quit"]),
            args[-1])

    def test_bounded_by_the_timeout_and_never_checked(self):
        audition.cmd_render({})
        _, kwargs = self.run_args()
        self.assertEqual(audition.RENDER_TIMEOUT_S, kwargs["timeout"])
        self.assertIs(False, kwargs["check"])
        self.assertIn("SDL_VIDEODRIVER", kwargs["env"])
        self.proc.call.assert_not_called()

    def test_all_rendered_and_loud_enough_is_success(self):
        self.assertEqual(0, audition.cmd_render({"D_SDM01": 10.0}))
        printed = self.out.getvalue()
        self.assertRegex(printed, r"OK   D_SDM01 \(D_SDM01\.mid\): \d+ B, 10\.0s \(expected ~10\.0s\)")
        self.assertIn("OK   D_SDTITL", printed)

    def test_candidates_render_into_their_own_folder(self):
        write_mids(self.candidates, ["x.mid"])
        self.renders = {"D_CND01": (2.0, 0.5)}
        self.assertEqual(0, audition.cmd_render({}, use_candidates=True))
        self.assertTrue((self.audio / "render-candidates" / "D_CND01.wav").is_file())
        self.assertIn("OK   D_CND01 (x.mid)", self.out.getvalue())

    def test_missing_wav_fails(self):
        self.renders["D_SDTITL"] = None
        self.assertEqual(1, audition.cmd_render({}))
        self.assertIn("FAIL D_SDTITL", self.out.getvalue())
        self.assertIn("was not written", self.out.getvalue())

    def test_silent_wav_fails(self):
        self.renders["D_SDM01"] = (10.0, audition.MIN_PEAK_AMPLITUDE / 4)
        self.assertEqual(1, audition.cmd_render({}))
        self.assertIn("FAIL D_SDM01", self.out.getvalue())

    def test_duration_threshold_is_eighty_percent_of_the_expectation(self):
        # 10 s rendered: OK against 12.5 s (exactly 80 %), FAIL against 12.6 s.
        self.assertEqual(0, audition.cmd_render({"D_SDM01": 12.5}))
        self.assertEqual(1, audition.cmd_render({"D_SDM01": 12.6}))

    def test_no_expectation_means_no_length_check(self):
        self.renders["D_SDM01"] = (0.5, 0.5)
        self.assertEqual(0, audition.cmd_render({}))

    def test_engine_that_never_quits_is_exit_five(self):
        self.proc.run.side_effect = subprocess.TimeoutExpired("gzdoom", audition.RENDER_TIMEOUT_S)
        self.assertEqual(5, audition.cmd_render({}))
        self.assertIn("did not quit in time", self.err.getvalue())

    @unittest.expectedFailure
    def test_render_runs_on_the_tooling_config(self):
        """BUG A1 (sound-designer). --render runs on the user's own gzdoom.ini.

        Repro: read cmd_render()'s argv (or `SD_ALLOW_ENGINE=1 audition.py
        --render`, PM only): no `-config`. Expected: `-config
        logs/gzdoom-tooling.ini`, as --play and tools/smoke.py pass.
        Observed: the engine reads and, on quit, writes back the CEO's own
        config after a `-nosound +vid_fullscreen 0` run; tools/smoke.py's
        comment records that such a run "is enough to leave a developer with
        a silent game". The written-back values are NOT VERIFIED here (no
        engine run, D26).
        """
        audition.cmd_render({})
        args, _ = self.run_args()
        self.assertIn("-config", args)
        self.assertEqual(str(audition.TOOLING_CONFIG), args[args.index("-config") + 1])

    @unittest.expectedFailure
    def test_expectation_for_a_lump_that_was_not_rendered_is_an_error(self):
        """BUG A3 (sound-designer). A mistyped --expect silently checks nothing.

        Repro: `audition.py --render --expect D_SDMO1=142` (letter O for
        zero) with D_SDM01 rendering 10 s. Expected: an error naming the
        unknown lump. Observed: exit 0, D_SDM01 "OK" with "expected ~0.0s":
        the duration check the caller asked for never ran. Same for
        `--candidates --expect D_SDM01=...`, where the lumps are D_CNDnn.
        """
        self.assertNotEqual(0, audition.cmd_render({"D_SDMO1": 142.0}))


class RenderWithoutTheModTests(SandboxedCase):
    fake_engine = False

    @unittest.expectedFailure
    def test_render_does_not_need_the_mod_pk3(self):
        """BUG A7 (sound-designer). --render demands dist/sovietdoom.pk3 it never loads.

        cmd_render() deliberately does not load the mod PK3 "so measurement
        does not depend on somebody else's build being mid-flight", but it
        calls require_engine(), which exits when that file is missing.
        Repro: with GZDoom and the IWAD present and dist/ empty (or
        mid-rebuild), `SD_ALLOW_ENGINE=1 audition.py --render` exits with
        "dist/sovietdoom.pk3 missing; run python3 tools/build.py".
        Expected: the render proceeds. Here: gate patched open (never the
        variable), engine and IWAD found, no mod PK3, a fake engine.
        """
        write_mids(self.audio, ["D_SDM01.mid"])
        self.gzdoom.parent.mkdir(parents=True)
        self.gzdoom.write_bytes(b"")
        self.iwad.parent.mkdir(parents=True)
        self.iwad.write_bytes(b"IWAD")
        self.proc.run.side_effect = lambda *a, **k: subprocess.CompletedProcess(a, 0)
        with (mock.patch.object(audition, "engine_allowed", return_value=True),
              mock.patch.object(audition, "GZDOOM_CANDIDATES", (self.gzdoom,)),
              mock.patch.object(audition, "IWAD_CANDIDATES", (self.iwad,))):
            try:
                audition.cmd_render({})
            except SystemExit as exc:
                self.fail(f"render refused: {exc.code}")
        self.proc.run.assert_called_once()


# --- measure_wav() -----------------------------------------------------------

class MeasureWavTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def wav(self, data: bytes) -> Path:
        p = self.tmp / "x.wav"
        p.write_bytes(data)
        return p

    def test_pcm16_mono(self):
        seconds, peak = audition.measure_wav(self.wav(pcm16_wav(3.0, 0.5)))
        self.assertAlmostEqual(3.0, seconds)
        self.assertAlmostEqual(0.5, peak, places=3)

    def test_pcm16_stereo_counts_frames_not_samples(self):
        seconds, _ = audition.measure_wav(self.wav(pcm16_wav(2.0, 0.5, channels=2)))
        self.assertAlmostEqual(2.0, seconds)

    def test_writewave_format_extensible_float(self):
        seconds, peak = audition.measure_wav(self.wav(float_ext_wav(1.5, 0.25)))
        self.assertAlmostEqual(1.5, seconds)
        self.assertAlmostEqual(0.25, peak)

    def test_plain_ieee_float(self):
        data = struct.pack("<4f", 0.0, 0.75, -0.1, 0.0)
        fmt = fmt_basic(audition.WAV_FORMAT_IEEE_FLOAT, 1, 4, 32)
        self.assertEqual((1.0, 0.75), audition.measure_wav(self.wav(riff(fmt, data))))

    def test_pcm8_is_unsigned_around_128(self):
        fmt = fmt_basic(audition.WAV_FORMAT_PCM, 1, 4, 8)
        seconds, peak = audition.measure_wav(self.wav(riff(fmt, bytes([128, 128, 192, 128]))))
        self.assertEqual(1.0, seconds)
        self.assertAlmostEqual(0.5, peak)
        _, peak = audition.measure_wav(self.wav(riff(fmt, bytes([0, 128, 128, 128]))))
        self.assertEqual(1.0, peak)                                   # -128 is full scale

    def test_digital_silence_has_zero_peak(self):
        self.assertEqual(0.0, audition.measure_wav(self.wav(pcm16_wav(1.0, 0.0)))[1])

    def test_skips_odd_sized_chunks_with_their_pad_byte(self):
        fmt = fmt_basic(audition.WAV_FORMAT_PCM, 1, 2, 16)
        data = struct.pack("<2h", 0, 16384)
        p = self.wav(riff(fmt, data, extra_chunks=chunk(b"LIST", b"odd")))
        self.assertEqual((1.0, 0.5), audition.measure_wav(p))

    def test_rejects_what_it_cannot_read(self):
        fmt16 = fmt_basic(audition.WAV_FORMAT_PCM, 1, 4, 16)
        cases = {
            "not RIFF": b"RIFX" + b"\x00" * 40,
            "no data chunk": b"RIFF\x10\x00\x00\x00WAVE" + chunk(b"fmt ", fmt16),
            "no fmt chunk": b"RIFF\x10\x00\x00\x00WAVE" + chunk(b"data", b"\x00\x00"),
            "24-bit PCM": riff(fmt_basic(audition.WAV_FORMAT_PCM, 1, 4, 24), b"\x00" * 12),
        }
        for label, data in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(ValueError):
                    audition.measure_wav(self.wav(data))


# --- GZDoom and IWAD discovery -----------------------------------------------

class DiscoveryTests(SandboxedCase):
    fake_engine = False

    def setUp(self):
        super().setUp()
        self.enterContext(mock.patch.object(audition, "engine_allowed", return_value=True))
        self.which = self.enterContext(mock.patch.object(audition.shutil, "which",
                                                         return_value=None))
        self.mac = self.tmp / "Applications" / "GZDoom.app" / "Contents" / "MacOS" / "gzdoom"
        self.win = self.tmp / "Programs" / "GZDoom" / "gzdoom.exe"
        self.freedoom = self.tmp / "iwads" / "freedoom2.wad"
        self.doom2 = self.tmp / "iwads" / "doom2.wad"
        self.enterContext(mock.patch.object(audition, "GZDOOM_CANDIDATES", (self.mac, self.win)))
        self.enterContext(mock.patch.object(audition, "IWAD_CANDIDATES",
                                            (self.freedoom, self.doom2)))

    def touch(self, *paths: Path):
        for p in paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x")

    def test_windows_candidates_come_from_localappdata_and_program_files(self):
        local = str(self.tmp / "Local")
        progs = str(self.tmp / "Program Files")
        fresh = load_fresh_audition({"LOCALAPPDATA": local, "ProgramFiles": progs,
                                     "HOME": str(self.tmp), "USERPROFILE": str(self.tmp)})
        self.assertEqual(4, len(fresh.GZDOOM_CANDIDATES))
        self.assertEqual("/Applications/GZDoom.app/Contents/MacOS/gzdoom",
                         fresh.GZDOOM_CANDIDATES[0].as_posix())          # macOS first
        self.assertEqual(Path(local) / "Programs" / "GZDoom" / "gzdoom.exe",
                         fresh.GZDOOM_CANDIDATES[2])
        self.assertEqual(Path(progs) / "GZDoom" / "gzdoom.exe", fresh.GZDOOM_CANDIDATES[3])

    def test_without_windows_variables_only_macos_is_searched(self):
        fresh = load_fresh_audition({"HOME": str(self.tmp), "USERPROFILE": str(self.tmp)})
        self.assertEqual(2, len(fresh.GZDOOM_CANDIDATES))
        self.assertTrue(all(p.name == "gzdoom" for p in fresh.GZDOOM_CANDIDATES))
        self.assertEqual(["freedoom2.wad", "doom2.wad"], [p.name for p in fresh.IWAD_CANDIDATES])

    def test_find_returns_the_first_existing_file_and_skips_directories(self):
        a, b, c = self.tmp / "a", self.tmp / "b", self.tmp / "c"
        a.mkdir()                                  # a directory named like the binary
        self.touch(b, c)
        self.assertEqual(b, audition.find((a, b, c)))
        self.assertIsNone(audition.find((a, self.tmp / "missing")))

    def test_windows_install_is_found(self):
        self.touch(self.win, self.freedoom, self.mod_pk3)
        self.assertEqual((self.win, self.freedoom), audition.require_engine())
        self.which.assert_not_called()

    def test_macos_install_wins_over_windows_and_freedoom_over_doom2(self):
        self.touch(self.mac, self.win, self.freedoom, self.doom2, self.mod_pk3)
        self.assertEqual((self.mac, self.freedoom), audition.require_engine())

    def test_doom2_when_freedoom_is_absent(self):
        self.touch(self.win, self.doom2, self.mod_pk3)
        self.assertEqual(self.doom2, audition.require_engine()[1])

    def test_falls_back_to_gzdoom_on_the_path(self):
        on_path = self.tmp / "bin" / "gzdoom"
        self.which.return_value = str(on_path)
        self.touch(self.freedoom, self.mod_pk3)
        self.assertEqual(on_path, audition.require_engine()[0])
        self.which.assert_called_with("gzdoom")

    def test_no_engine_is_a_clear_error(self):
        self.touch(self.freedoom, self.mod_pk3)
        with self.assertRaises(SystemExit) as ctx:
            audition.require_engine()
        self.assertIn("gzdoom not found", str(ctx.exception.code))

    def test_no_iwad_names_the_iwads_folder(self):
        self.touch(self.win, self.mod_pk3)
        with self.assertRaises(SystemExit) as ctx:
            audition.require_engine()
        self.assertIn(str(audition.PROJECT_ROOT / "iwads"), str(ctx.exception.code))

    def test_no_mod_pk3_says_how_to_build_it(self):
        self.touch(self.win, self.freedoom)
        with self.assertRaises(SystemExit) as ctx:
            audition.require_engine()
        self.assertIn(str(self.mod_pk3), str(ctx.exception.code))
        self.assertIn("tools/build.py", str(ctx.exception.code))

    @unittest.expectedFailure
    def test_engine_not_found_names_where_it_looked(self):
        """BUG A8 (sound-designer). The not-found message is macOS-only.

        Repro (this PC, gate open, GZDoom not unzipped):
        `audition.py --render` says "gzdoom not found (brew install --cask
        gzdoom)": wrong advice on Windows, and no path. Expected: the paths
        searched (as the IWAD error names iwads/), so the Windows location
        %LOCALAPPDATA%\\Programs\\GZDoom\\gzdoom.exe is visible.
        """
        self.touch(self.freedoom, self.mod_pk3)
        with self.assertRaises(SystemExit) as ctx:
            audition.require_engine()
        self.assertIn(str(self.win), str(ctx.exception.code))

    @unittest.skipUnless(
        os.environ.get("LOCALAPPDATA")
        and (Path(os.environ["LOCALAPPDATA"]) / "Programs" / "GZDoom" / "gzdoom.exe").is_file(),
        "GZDoom is not unzipped at %LOCALAPPDATA%\\Programs\\GZDoom (not the Windows PC)")
    def test_this_pc_finds_the_documented_windows_install(self):
        """CLAUDE.md: GZDoom g4.14.2 unzipped at %LOCALAPPDATA%\\Programs\\GZDoom."""
        expected = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "GZDoom" / "gzdoom.exe"
        fresh = load_fresh_audition(dict(os.environ))
        self.assertEqual(expected, audition.find(fresh.GZDOOM_CANDIDATES))


# --- main() ------------------------------------------------------------------

class MainTests(unittest.TestCase):
    def setUp(self):
        self.pack = self.enterContext(mock.patch.object(audition, "pack"))
        self.play = self.enterContext(mock.patch.object(audition, "cmd_play", return_value=4))
        self.render = self.enterContext(mock.patch.object(audition, "cmd_render", return_value=1))
        self.enterContext(contextlib.redirect_stderr(io.StringIO()))

    def test_no_arguments_packs_the_drafts(self):
        for argv in ([], ["--pack"]):
            with self.subTest(argv=argv):
                self.assertEqual(0, audition.main(argv))
                self.pack.assert_called_with(use_candidates=False, first_lump=None)
        self.play.assert_not_called()
        self.render.assert_not_called()

    def test_pack_candidates_with_lump(self):
        audition.main(["--pack", "--candidates", "--lump", "D_CND11"])
        self.pack.assert_called_once_with(use_candidates=True, first_lump="D_CND11")

    def test_play_is_wired_and_returns_its_code(self):
        self.assertEqual(4, audition.main(["--play", "map01", "--candidates", "--lump", "D_CND02"]))
        self.play.assert_called_once_with("map01", use_candidates=True, lump="D_CND02")
        self.pack.assert_not_called()

    def test_play_accepts_only_title_and_map01(self):
        with self.assertRaises(SystemExit) as ctx:
            audition.main(["--play", "map02"])
        self.assertEqual(2, ctx.exception.code)
        self.play.assert_not_called()

    def test_expect_is_parsed_into_seconds_per_lump(self):
        self.assertEqual(1, audition.main(["--render", "--expect", "D_SDM01=142",
                                           "--expect", "D_SDTITL=61.5", "--candidates"]))
        self.render.assert_called_once_with({"D_SDM01": 142.0, "D_SDTITL": 61.5},
                                            use_candidates=True)

    def test_render_without_expect_has_no_expectations(self):
        audition.main(["--render"])
        self.render.assert_called_once_with({}, use_candidates=False)

    @unittest.expectedFailure
    def test_malformed_expect_is_a_usage_error(self):
        """BUG A4 (sound-designer). A malformed --expect crashes with a traceback.

        Repro: `audition.py --render --expect D_SDM01` (no `=`) or
        `--expect D_SDM01=2:22`. Expected: an argparse usage error (exit 2)
        naming the LUMP=SECONDS form. Observed: an uncaught
        `ValueError: could not convert string to float`.
        """
        for bad in ("D_SDM01", "D_SDM01=2:22"):
            with self.subTest(expect=bad):
                try:
                    audition.main(["--render", "--expect", bad])
                except ValueError as exc:
                    self.fail(f"traceback instead of a usage error: {exc}")
                except SystemExit as exc:
                    self.assertEqual(2, exc.code)


# --- the real MIDIs under work/audio (skipped without them) ------------------

class RealMidiTests(unittest.TestCase):
    """Pack the real drafts and candidates into a tempdir; work/ is only read."""

    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.test_pk3 = self.tmp / "sd-music-draft.pk3"
        self.enterContext(mock.patch.object(audition, "TEST_PK3", self.test_pk3))
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def entries(self) -> dict[str, bytes]:
        with zipfile.ZipFile(self.test_pk3) as zf:
            return {i.filename: zf.read(i) for i in zf.infolist()}

    @real_drafts
    def test_real_drafts_pack_as_valid_lumps_and_cover_the_overlay(self):
        # Drafts mode reads AUDIO_DIR and writes only TEST_PK3 (patched above).
        with mock.patch.object(audition, "AUDIO_DIR", REAL_AUDIO_DIR):
            pairs = audition.pack()
        lumps = [lump for lump, _ in pairs]
        for lump, path in pairs:
            with self.subTest(lump=lump):
                try:
                    self.assertEqual(lump, validate_lump_name(lump))
                except WadError as exc:
                    self.fail(str(exc))
        entries = self.entries()
        for lump, path in pairs:
            data = entries[f"music/{lump}.mid"]
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(MIDI_MAGIC, data[:4])
        # The overlay's MAPINFO names these two; they must be among the drafts.
        self.assertIn(audition.TITLE_LUMP, lumps)
        self.assertIn(audition.MAP01_LUMP, lumps)

    @real_candidates
    def test_real_candidates_number_as_on_the_mac(self):
        # The manifest goes to AUDIO_DIR, so AUDIO_DIR is a tempdir here.
        with (mock.patch.object(audition, "AUDIO_DIR", self.tmp),
              mock.patch.object(audition, "CANDIDATES_DIR", REAL_CANDIDATES_DIR)):
            pairs = audition.pack(use_candidates=True)
        self.assertEqual([f"D_CND{i:02d}" for i in range(1, len(pairs) + 1)],
                         [lump for lump, _ in pairs])
        for lump, path in pairs:
            self.assertEqual(path.read_bytes(), self.entries()[f"music/{lump}.mid"])
        if not REAL_MANIFEST.is_file():
            self.skipTest("no manifest from the Mac to compare against")
        # The Mac wrote work/audio/candidates-lumps.txt; same numbering here
        # means "D_CND11" names the same piece on both machines (see A5).
        self.assertEqual(REAL_MANIFEST.read_text().splitlines(),
                         (self.tmp / "candidates-lumps.txt").read_text().splitlines())


if __name__ == "__main__":
    unittest.main()
