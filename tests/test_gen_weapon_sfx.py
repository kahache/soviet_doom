"""Tests for tools/audio/gen_weapon_sfx.py: the arsenal's draft sound effects.

What is tested:

- The contract: every weapon logical name `src/lumps/SNDINFO` promises a
  final lump for is generated under that lump name (the ice axe's since
  D40; the shovel's retired lumps are not); a lump marked `wired` is really played by
  `src/zscript/`; lump and logical names are legal and unique; the engine
  timings the sounds are cut to still match the tic counts in
  `src/zscript/weapons/*.zs`; every lump has its card in
  `docs/sound/WEAPON-SOUNDS.md` and every source file its provenance row,
  with the SHA-256 of the file on disk (D44 put more `KEN-IMP` files in).
- The provenance rule of WEAPON-SOUNDS.md: the only foreign sources are files
  of the packs D36 authorised for this use (OGA-100, KEN-IMP), and no
  `shot_*` recording is used.
- Every rendered lump: deterministic, never clips, 16-bit mono 44.1 kHz,
  length within its card, starts at once when it is a shot or an impact,
  ends in silence; handling sounds sit under the quietest shot (short-term
  loudness), empty clicks further under.
- Timing against the engine: the PPSh's round lives inside one 3-tic cycle,
  the ice axe's swing peaks before the blow, the IZh snaps shut on the frame
  where the shells are counted, the Katyusha's charge and reload fit their
  20 tics, the RPG-7's reload is over before the next launch.
- The overlay PK3, the preview page and the before/after page (`--compare`:
  only the lumps that changed); `main()` writes only where it is told.
- Missing sources: the lumps that need them are skipped, the synthetic ones
  are still built.

The lumps that layer CC0 foley need `ffmpeg` and the gitignored
`work/audio/sfx_sources/`; they skip when either is absent (CI has neither).
Everything is skipped without numpy (CI's system python has none). The full
render of all 31 lumps takes ~10 s and is skipped with SD_SKIP_SLOW_ART=1
(`tools/verify.py fast`), as the art generator runs are; the contract and a
few synthetic lumps always run. Nothing is written under `work/`: every
output goes to a temporary directory, and a tripwire hashes the generator's
real output directory and PK3 before and after.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_weapon_sfx -v
"""

from __future__ import annotations

import hashlib
import io
import os
import re
import sys
import tempfile
import unittest
import wave
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    import numpy as np
    import gen_weapon_sfx as gws
except ImportError:                                    # pragma: no cover
    np = None
    gws = None

from sdbuild.wad import validate_lump_name  # noqa: E402

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the full render of every lump")

SNDINFO = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"
ZSCRIPT = PROJECT_ROOT / "src" / "zscript"
WEAPONS_ZS = ZSCRIPT / "weapons"
PLAN_DOC = PROJECT_ROOT / "docs" / "sound" / "WEAPON-SOUNDS.md"
REAL_OUT = PROJECT_ROOT / "work" / "audio" / "sfx" / "weapons"
REAL_PK3 = PROJECT_ROOT / "work" / "audio" / "sfx" / "sd-weapon-sfx-draft.pk3"

# Shots and impacts must be loud from the first millisecond.
ATTACK_EVENTS = ("fire", "hit", "wall", "explode", "burst")
ATTACK_EXEMPT = ("SDHKFIR", "SDRKFIR")  # a ripple of six, a valve opening: both build up
ONSET_WINDOW_S = 0.005
ONSET_LEVEL = 10 ** (-20 / 20)          # within 20 dB of full scale
END_WINDOW_S = 0.002
END_LEVEL = 10 ** (-40 / 20)
PPSH_ENERGY_IN_CYCLE = 0.90             # share of the round's energy in 3 tics
IZH_SNAP_TOLERANCE_S = 0.04
HANDLING_UNDER_SHOTS_DB = 3.0           # reload / pickup under the quietest shot
DRY_UNDER_SHOTS_DB = 8.0                # an empty click well under it
LOUDNESS_TOLERANCE_DB = 0.5
DETERMINISM_LUMPS = ("SDAXSWG", "SDAXHIT", "SDTTFIR", "SDIZFIR", "SDIZRLD", "SDPPFIR",
                     "SDTTDRY", "SDHKPKP")
FAST_LUMPS = {"SDAXSWG", "SDIZFIR", "SDRKFIR"}   # synthetic only: no ffmpeg needed


def tree_digest(paths) -> str:
    h = hashlib.sha256()
    for root in paths:
        files = sorted(root.rglob("*")) if root.is_dir() else [root]
        for p in files:
            if p.is_file():
                h.update(str(p).encode())
                h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


_BEFORE = ""


def setUpModule():
    global _BEFORE
    _BEFORE = tree_digest([REAL_OUT, REAL_PK3])


def tearDownModule():
    if tree_digest([REAL_OUT, REAL_PK3]) != _BEFORE:
        raise AssertionError("tests/test_gen_weapon_sfx.py changed the real output under work/")


# --- ZScript readers -------------------------------------------------------------

RE_FRAME = re.compile(r"^\s*([A-Z0-9_]{4})\s+([A-Z\[\]\\]+)\s+(-?\d+)\b(.*)$")


def zs_text(zs_file: str) -> str:
    return (WEAPONS_ZS / zs_file).read_text(encoding="utf-8")


def slot1_file() -> str:
    """The melee weapon's file (ice_axe.zs since D40), found by its slot."""
    for path in sorted(WEAPONS_ZS.glob("*.zs")):
        if re.search(r"Weapon\.SlotNumber\s+1\s*;", path.read_text(encoding="utf-8")):
            return path.name
    raise AssertionError("no weapon declares Weapon.SlotNumber 1")


def state_frames(zs_file: str, label: str) -> list[tuple[str, int, str]]:
    """(frames, tics, rest of line) for each line of a state block, in order."""
    lines = zs_text(zs_file).splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.strip() == f"{label}:")
    out = []
    for ln in lines[start + 1:]:
        if ln.strip().startswith(("Goto", "Loop", "Stop")) or ln.strip().endswith(":"):
            break
        m = RE_FRAME.match(ln)
        if m:
            out.append((m.group(2), int(m.group(3)), m.group(4)))
    return out


def total_tics(frames) -> int:
    return sum(len(fr) * t for fr, t, _ in frames)


def sndinfo_weapon_targets() -> dict[str, str]:
    """logical name -> final lump, from SNDINFO's comments and header."""
    targets = {}
    for ln in SNDINFO.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(sd/weapon/\S+)\s+\S+\s*//\s*->\s*([A-Z0-9]+)", ln)
        if m:
            targets[m.group(1)] = m.group(2)
        m = re.match(r"^//\s+(sd/weapon/\S+)\s+([A-Z0-9]+)\s*$", ln)
        if m:
            targets[m.group(1)] = m.group(2)
        # Installed (N9, D74): the right-hand column is already our lump.
        m = re.match(r"^(sd/weapon/\S+)\s+(SD[A-Z0-9]+)\b", ln)
        if m:
            targets[m.group(1)] = m.group(2)
    return targets


def zscript_sounds() -> set[str]:
    text = "\n".join(p.read_text(encoding="utf-8") for p in ZSCRIPT.rglob("*.zs"))
    return set(re.findall(r'"(sd/weapon/[^"]+)"', text))


def pcm_of(data: bytes) -> tuple[np.ndarray, wave._wave_params]:
    with wave.open(io.BytesIO(data)) as w:
        params = w.getparams()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return x, params


# --- Contract -----------------------------------------------------------------

@needs_numpy
class ContractTest(unittest.TestCase):

    def test_every_promised_lump_is_generated(self):
        by_logical = {lump.logical: lump.name for lump in gws.LUMPS}
        targets = sndinfo_weapon_targets()
        self.assertGreaterEqual(len(targets), 11)
        for logical, lump_name in targets.items():
            with self.subTest(logical):
                self.assertEqual(by_logical.get(logical), lump_name)
        for old, new in gws.RETIRED_LUMPS.items():
            self.assertNotIn(old, targets.values())
            self.assertIn(new, gws.LUMPS_BY_NAME)

    def test_wired_lumps_are_played_by_the_code(self):
        played = zscript_sounds()
        for lump in gws.LUMPS:
            if lump.wired:
                with self.subTest(lump.name):
                    self.assertIn(lump.logical, played,
                                  f"{lump.logical} is marked wired but no .zs plays it")

    def test_names_are_legal_and_unique(self):
        for lump in gws.LUMPS:
            self.assertEqual(validate_lump_name(lump.name), lump.name)
            self.assertTrue(lump.logical.startswith("sd/weapon/"), lump.logical)
        self.assertEqual(len({lump.name for lump in gws.LUMPS}), len(gws.LUMPS))
        self.assertEqual(len({lump.logical for lump in gws.LUMPS}), len(gws.LUMPS))
        self.assertFalse(set(gws.RETIRED_LUMPS) & set(gws.LUMPS_BY_NAME))

    def test_every_gun_has_fire_reload_pickup_and_dry(self):
        for weapon in ("TT-33", "IZh-58", "PPSh-41", "RPG-7", "ROKS-3", "hand Katyusha"):
            events = {lump.event for lump in gws.LUMPS if lump.weapon == weapon}
            self.assertLessEqual({"fire", "reload", "pickup", "dry"}, events, weapon)
        axe = {lump.event for lump in gws.LUMPS if lump.weapon == "ice axe"}
        self.assertLessEqual({"swing", "hit", "wall"}, axe)

    def test_only_authorised_foley_and_no_recorded_shots(self):
        for key, (pack, rel) in gws.SOURCE_FILES.items():
            self.assertIn(pack, gws.ALLOWED_PACKS, key)
            self.assertNotIn("shot_", rel)
        used = {k for lump in gws.LUMPS for k in lump.sources}
        self.assertLessEqual(used, set(gws.SOURCE_FILES))

    def test_plan_document_has_every_card_and_source(self):
        doc = PLAN_DOC.read_text(encoding="utf-8")
        for lump in gws.LUMPS:
            self.assertIn(f"`{lump.name}`", doc, lump.name)
            self.assertIn(f"`{lump.logical}`", doc, lump.logical)
        used = {k for lump in gws.LUMPS for k in lump.sources}
        for key in used:
            self.assertIn(Path(gws.SOURCE_FILES[key][1]).name, doc, key)

    def test_plan_document_has_every_source_hash(self):
        doc = PLAN_DOC.read_text(encoding="utf-8")
        used = {k for lump in gws.LUMPS for k in lump.sources}
        if not all(gws.source_path(k).is_file() for k in used):
            self.skipTest("the gitignored sources are not on this machine")
        for key in sorted(used):
            with self.subTest(key):
                self.assertIn(gws.sha256_file(gws.source_path(key)), doc)

    def test_change_notes_name_real_lumps(self):
        self.assertLessEqual(set(gws.CHANGE_NOTES), set(gws.LUMPS_BY_NAME))

    def test_ppsh_rate_matches_zscript(self):
        fire = [f for f in state_frames("ppsh.zs", "Fire") if "A_FireBullets" in f[2]]
        self.assertEqual({t for _, t, _ in fire}, {gws.PPSH_TICS_PER_ROUND})

    def test_tokarev_cycle_matches_zscript(self):
        self.assertEqual(total_tics(state_frames("tokarev.zs", "Fire")), gws.TT_CYCLE_TICS)

    def test_melee_lead_in_matches_zscript(self):
        fire = state_frames(slot1_file(), "Fire")
        self.assertEqual(fire[0][1], gws.MELEE_TICS_BEFORE_HIT)
        self.assertRegex(fire[1][2], r"A_SD_\w+Swing")

    def test_izh_reload_matches_zscript(self):
        reload = state_frames("izh.zs", "Reload")
        self.assertIn("sd/weapon/izh/reload", reload[0][2])
        self.assertEqual(total_tics(reload), gws.IZH_RELOAD_TICS)
        close = next(i for i, f in enumerate(reload) if "A_SD_ReloadIzh" in f[2])
        self.assertEqual(total_tics(reload[:close]), gws.IZH_RELOAD_CLOSE_TICS)

    def test_rpg7_cycle_matches_zscript(self):
        fire = state_frames("rpg7.zs", "Fire")
        self.assertEqual(total_tics(fire), gws.RPG7_CYCLE_TICS)
        launch = next(i for i, f in enumerate(fire) if "A_FireProjectile" in f[2])
        self.assertEqual(total_tics(fire[:launch]), gws.RPG7_TICS_BEFORE_LAUNCH)

    def test_katyusha_frames_match_zscript(self):
        fire = state_frames("katyusha.zs", "Fire")
        self.assertIn("sd/weapon/katyusha/charge", fire[0][2])
        self.assertEqual(fire[0][1], gws.KATYUSHA_CHARGE_TICS)
        salvo = next(i for i, f in enumerate(fire) if "A_SD_FireKatyusha" in f[2])
        # N9: a 0-tic frame starts the reload as the recovery begins.
        recovery = next(f for f in fire[salvo + 1:] if f[1] > 0)
        self.assertIn("A_ReFire", recovery[2])
        self.assertEqual(recovery[1], gws.KATYUSHA_RECOVERY_TICS)

    def test_overlay_sndinfo_marks_the_unwired_names(self):
        text = gws.sndinfo_text(gws.LUMPS)
        for lump in gws.LUMPS:
            suffix = "" if lump.wired else r"\s+// needs a hook"
            self.assertRegex(text, rf"(?m)^{re.escape(lump.logical)}\s+{lump.name}{suffix}$")

    def test_list_writes_nothing(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(gws.main(["--list"]), 0)
        self.assertIn(f"{len(gws.LUMPS)} lumps", out.getvalue())


# --- Rendered lumps -------------------------------------------------------------

@needs_numpy
@slow
class RenderTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sources = gws.Sources()
        cls.result = gws.build(sources=cls.sources)

    def rendered(self, name: str) -> bytes:
        if name not in self.result.rendered:
            self.skipTest(f"{name} not built here: {self.result.skipped.get(name)}")
        return self.result.rendered[name]

    def floats(self, name: str) -> np.ndarray:
        x, _ = pcm_of(self.rendered(name))
        return x / gws.PCM_MAX

    def test_synthetic_lumps_always_build(self):
        for lump in gws.LUMPS:
            if not lump.sources:
                self.assertIn(lump.name, self.result.rendered, self.result.skipped.get(lump.name))

    def test_deterministic(self):
        again = gws.build(set(DETERMINISM_LUMPS), gws.Sources())
        for name in DETERMINISM_LUMPS:
            with self.subTest(name):
                self.assertEqual(again.rendered.get(name), self.result.rendered.get(name))

    def test_format_peak_and_no_clipping(self):
        for lump in gws.LUMPS:
            with self.subTest(lump.name):
                x, p = pcm_of(self.rendered(lump.name))
                self.assertEqual((p.nchannels, p.sampwidth, p.framerate), (1, 2, gws.SR))
                ceiling = round(10 ** (lump.peak_dbfs / 20) * gws.PCM_MAX) + 1
                peak = int(np.max(np.abs(x.astype(np.int32))))
                self.assertLessEqual(peak, ceiling)
                self.assertLess(peak, gws.PCM_MAX)
                if gws.loudness_of(lump) is None:
                    self.assertGreater(peak, ceiling - 64)     # really normalised

    def test_handling_sounds_are_levelled(self):
        for lump in gws.LUMPS:
            target = gws.loudness_of(lump)
            if target is None:
                continue
            with self.subTest(lump.name):
                x = self.floats(lump.name)
                st = gws.short_term_db(x)
                peak_db = 20 * np.log10(np.max(np.abs(x)))
                self.assertLessEqual(st, target + LOUDNESS_TOLERANCE_DB)
                # Either at the target, or held down by its peak ceiling.
                self.assertTrue(st >= target - LOUDNESS_TOLERANCE_DB
                                or peak_db >= lump.peak_dbfs - LOUDNESS_TOLERANCE_DB,
                                (st, peak_db))

    def test_handling_sits_under_every_shot(self):
        shots = [gws.short_term_db(self.floats(lump.name)) for lump in gws.LUMPS
                 if lump.event in ("fire", "hit") and lump.name in self.result.rendered]
        quietest = min(shots)
        for lump in gws.LUMPS:
            if lump.event not in ("reload", "pickup", "dry"):
                continue
            with self.subTest(lump.name):
                margin = DRY_UNDER_SHOTS_DB if lump.event == "dry" else HANDLING_UNDER_SHOTS_DB
                self.assertLessEqual(gws.short_term_db(self.floats(lump.name)), quietest - margin)

    def test_length_within_card(self):
        for lump in gws.LUMPS:
            with self.subTest(lump.name):
                x, _ = pcm_of(self.rendered(lump.name))
                lo, hi = lump.length_s
                self.assertTrue(lo <= len(x) / gws.SR <= hi, len(x) / gws.SR)

    def test_shots_start_at_once_and_everything_ends_quiet(self):
        for lump in gws.LUMPS:
            with self.subTest(lump.name):
                xf = self.floats(lump.name)
                if lump.event in ATTACK_EVENTS and lump.name not in ATTACK_EXEMPT:
                    head = np.abs(xf[:gws.n_of(ONSET_WINDOW_S)])
                    self.assertGreater(head.max(), ONSET_LEVEL)
                tail = np.abs(xf[-gws.n_of(END_WINDOW_S):])
                self.assertLess(tail.max(), END_LEVEL)

    def test_ppsh_round_fits_one_cycle(self):
        x = self.floats("SDPPFIR")
        e = np.cumsum(x ** 2)
        cycle = gws.n_of(gws.tics(gws.PPSH_TICS_PER_ROUND))
        self.assertGreaterEqual(e[cycle] / e[-1], PPSH_ENERGY_IN_CYCLE)

    def test_tokarev_shot_fits_its_cycle(self):
        self.assertLessEqual(len(self.floats("SDTTFIR")) / gws.SR, gws.tics(gws.TT_CYCLE_TICS))

    def test_axe_swing_peaks_before_the_blow(self):
        x = self.floats("SDAXSWG")
        peak_t = np.argmax(np.abs(x)) / gws.SR
        self.assertLess(peak_t, gws.tics(gws.MELEE_TICS_BEFORE_HIT))
        self.assertGreater(peak_t, 0.05)        # a swing builds; it is not a hit

    def test_izh_snaps_shut_on_the_reload_frame(self):
        x = self.floats("SDIZRLD")
        loudest = np.argmax(np.abs(x)) / gws.SR
        self.assertAlmostEqual(loudest, gws.tics(gws.IZH_RELOAD_CLOSE_TICS),
                               delta=IZH_SNAP_TOLERANCE_S)
        self.assertLessEqual(len(x) / gws.SR, gws.tics(gws.IZH_RELOAD_TICS) + 0.1)

    def test_katyusha_charge_and_reload_fit_their_tics(self):
        self.assertLessEqual(len(self.floats("SDHKCHG")) / gws.SR,
                             gws.tics(gws.KATYUSHA_CHARGE_TICS) + 0.15)
        self.assertLessEqual(len(self.floats("SDHKRLD")) / gws.SR,
                             gws.tics(gws.KATYUSHA_RECOVERY_TICS) + 0.01)

    def test_rpg7_reload_is_over_before_the_next_launch(self):
        self.assertLessEqual(len(self.floats("SDRPRLD")) / gws.SR, gws.RPG7_RELOAD_WINDOW_S)

    def test_takes_are_varispeed_of_take_a(self):
        lump = gws.LUMPS_BY_NAME["SDIZFIR"]
        a = gws.render(lump, self.sources, "A")
        for take in ("B", "C"):
            with self.subTest(take):
                x = gws.render(lump, self.sources, take)
                self.assertAlmostEqual(len(x) / len(a), 1 / gws.TAKES[take], delta=0.05)

    def test_ppsh_previews(self):
        self.rendered("SDPPFIR")
        previews = gws.ppsh_previews(self.result.samples["SDPPFIR"])
        self.assertEqual(len(previews), 3)
        for name, x in previews.items():
            with self.subTest(name):
                self.assertLessEqual(np.max(np.abs(x)), 10 ** (gws.DEFAULT_PEAK_DBFS / 20) + 1e-9)
        engine = previews["SDPPFIR_burst_700rpm_engine.wav"]
        real = previews["SDPPFIR_burst_900rpm_real.wav"]
        self.assertGreater(len(engine), len(real))     # same 24 rounds, slower rate


@needs_numpy
class FastRenderTest(unittest.TestCase):
    """A few synthetic lumps, always: the generator is not silently broken under `fast`."""

    def test_synthetic_lumps_render_deterministically(self):
        a = gws.build(FAST_LUMPS, gws.Sources())
        b = gws.build(FAST_LUMPS, gws.Sources())
        self.assertEqual(set(a.rendered), FAST_LUMPS)
        self.assertEqual(a.rendered, b.rendered)

    def test_short_term_loudness_ruler(self):
        sine = 0.5 * np.sin(2 * np.pi * 1000 * np.arange(gws.SR) / gws.SR)
        self.assertAlmostEqual(gws.short_term_db(sine), 20 * np.log10(0.5 / np.sqrt(2)), delta=0.1)
        self.assertAlmostEqual(gws.short_term_db(gws.levelled(sine, -30.0)), -30.0, delta=0.01)
        self.assertIs(gws.levelled(sine, None), sine)


@needs_numpy
class MissingSourcesTest(unittest.TestCase):

    def test_sourced_lumps_skip_and_synthetic_ones_build(self):
        # Every sourced lump, plus one synthetic one to prove the rest go on.
        names = {lump.name for lump in gws.LUMPS if lump.sources} | {"SDAXSWG"}
        with tempfile.TemporaryDirectory() as tmp:
            result = gws.build(names, gws.Sources(Path(tmp)))
        for lump in gws.LUMPS:
            if lump.name not in names:
                continue
            with self.subTest(lump.name):
                if lump.sources:
                    self.assertIn(lump.name, result.skipped)
                else:
                    self.assertIn(lump.name, result.rendered)


# --- PK3, preview and main() ---------------------------------------------------------

@needs_numpy
class Pk3Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = gws.build(FAST_LUMPS, gws.Sources())

    def test_overlay_layout_and_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.pk3", Path(tmp) / "b.pk3"
            gws.write_pk3(a, self.result.rendered)
            gws.write_pk3(b, self.result.rendered)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as zf:
                names = zf.namelist()
                self.assertEqual(names[0], "SNDINFO")
                self.assertEqual(sorted(names[1:]),
                                 sorted(f"sounds/{n}.wav" for n in self.result.rendered))
                for info in zf.infolist():
                    self.assertEqual(info.date_time, gws.FIXED_ZIP_TIME)
                sndinfo = zf.read("SNDINFO").decode("ascii")
        defined = dict(re.findall(r"^(sd/weapon/\S+)\s+(\S+)", sndinfo, re.M))
        expected = {gws.LUMPS_BY_NAME[n].logical: n for n in self.result.rendered}
        self.assertEqual(defined, expected)

    def test_preview_page_embeds_every_clip(self):
        page = gws.preview_html(self.result, gws.Sources(), "2026-10-13_0000")
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("<title>Arsenal sound drafts</title>", page)
        for name in self.result.rendered:
            self.assertIn(name, page)
        # Every sweep lump has three takes; every lump has a "Today" slot.
        sweeps = sum(gws.LUMPS_BY_NAME[n].sweep for n in self.result.rendered)
        self.assertEqual(page.count("Draft, take "), 3 * sweeps)
        self.assertGreaterEqual(page.count("<audio "), 3 + len(self.result.rendered) - 1)
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)

    def test_dmx_to_wav(self):
        body = bytes([128, 255, 0, 128])
        lump = (b"\x03\x00" + (11025).to_bytes(2, "little")
                + (len(body) + 32).to_bytes(4, "little") + bytes(16) + body + bytes(16))
        x, p = pcm_of(gws.dmx_to_wav(lump))
        self.assertEqual((p.framerate, len(x)), (11025, 4))
        self.assertEqual(int(x[0]), 0)
        self.assertGreater(int(x[1]), 32000)
        self.assertLess(int(x[2]), -32000)
        with self.assertRaises(ValueError):
            gws.dmx_to_wav(b"\x01\x00" + lump[2:])

    def test_main_writes_only_where_told(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, pk3 = Path(tmp) / "out", Path(tmp) / "draft.pk3"
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = gws.main(["--only", "SDAXSWG", "sdizfir", "--no-ogg",
                                 "--out", str(out), "--pk3", str(pk3)])
            self.assertEqual(code, 0)
            self.assertEqual(sorted(p.name for p in out.iterdir()),
                             ["MANIFEST.txt", "PROVENANCE.tsv", "SDAXSWG.wav", "SDIZFIR.wav"])
            self.assertTrue(pk3.is_file())
            manifest = (out / "MANIFEST.txt").read_text(encoding="utf-8")
            self.assertIn("synthesis only (SYN)", manifest)
            tsv = (out / "PROVENANCE.tsv").read_text(encoding="utf-8").splitlines()
            self.assertEqual(tsv[0], "lump\troute\tpack\tfile\tsegment\tsha256")
            self.assertIn("SDAXSWG\tC\tSYN\tgen_weapon_sfx.py\t\t", tsv)

    def test_manifest_sources(self):
        text = ("# header\n\nSDAXHIT  take A  0.3 s  ...\n"
                "    KEN-IMP  ken-imp/extracted/Audio/impactPunch_heavy_000.ogg  abc\n"
                "SDAXSWG  take A  0.3 s  ...\n    synthesis only (SYN)\n")
        self.assertEqual(gws.manifest_sources(text),
                         {"SDAXHIT": {"impactPunch_heavy_000.ogg"}, "SDAXSWG": set()})

    def test_compare_page_shows_only_what_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp)
            (before / "SDAXSWG.wav").write_bytes(self.result.rendered["SDAXSWG"])   # same
            (before / "SDIZFIR.wav").write_bytes(gws.wav_bytes(np.zeros(100)))       # changed
            # SDRKFIR has no "before": new, so it is shown too
            self.assertEqual(gws.changed_lumps(self.result, before), ["SDIZFIR", "SDRKFIR"])
            page = gws.compare_html(self.result, gws.Sources(), before, "2026-10-14_0000")
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn("<title>Arsenal sound changes</title>", page)
        self.assertIn("SDIZFIR", page)
        self.assertIn("SDRKFIR", page)
        self.assertNotIn("SDAXSWG", page)
        self.assertEqual(page.count("<b>Before</b>"), 2)
        self.assertEqual(page.count("<b>After</b>"), 2)
        self.assertEqual(page.count("After, take "), 2)        # SDIZFIR is a sweep lump
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)

    def test_compare_needs_preview_and_a_copy(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                gws.main(["--compare", "somewhere"])
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(SystemExit):
                    gws.main(["--out", tmp, "--compare", tmp, "--preview", str(Path(tmp) / "p.html")])

    def test_main_rejects_unknown_lump(self):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                gws.main(["--only", "SDNOPE"])


if __name__ == "__main__":
    unittest.main()
