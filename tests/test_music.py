"""The music that ships, and the downloads it came from (D43).

What is pinned here, without ever starting GZDoom (D26):

- Every lump in `assets/music/` is a legal lump name, a well-formed Standard
  MIDI File with zero hanging notes, and has provenance in both registers
  (`docs/art/LICENSES.md`, which `tools/check_pk3.py` reads, and
  `docs/sound/MUSIC-RIGHTS.md`, which owns the rights analysis).
- Each installed file is REPRODUCIBLE from its source, byte for byte:
  `D_SDM01` from `tools/audio/gen_music.py`, `D_SDINTL` from Engelbach's
  download with `midi_edit.py --trim-head`. An approved asset that nobody can
  regenerate is an asset nobody can repair.
- The downloaded candidates in `work/audio/candidates/` (tracked in git since
  D43) are exactly the files whose SHA-256 MUSIC-RIGHTS records, every one has
  a stable lump in the registry, and the three D43 discards are gone.
- The Engelbach credit is where the credits live.

Python standard library only, like the tools. Run:
    python3 -m unittest tests.test_music -v
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import audition  # noqa: E402
import gen_music  # noqa: E402
import midi_edit  # noqa: E402
import midi_inspect  # noqa: E402
from sdbuild.wad import validate_lump_name  # noqa: E402

MUSIC_ASSETS = PROJECT_ROOT / "assets" / "music"
CANDIDATES = PROJECT_ROOT / "work" / "audio" / "candidates"
REGISTRY = CANDIDATES / audition.CANDIDATE_REGISTRY_NAME
MUSIC_RIGHTS = PROJECT_ROOT / "docs" / "sound" / "MUSIC-RIGHTS.md"
SOUNDTRACK = PROJECT_ROOT / "docs" / "sound" / "SOUNDTRACK.md"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"

INSTALLED = ("D_SDINTL", "D_SDM01")                 # D43
ENGELBACH_SOURCE = "WM_Internationale_orch2.mid"
DISCARDED = ("MU_RimskyKorsakov_FugueBACH.mid",    # D_CND02
             "MU_Scriabin_Prelude_op11n1.mid",     # D_CND04
             "MU_Tchaikovsky_WoodenSoldiers.mid")  # D_CND08
RADIO = ("WM_Ej_uchnem.mid", "WM_Kolokolchik.mid")  # the diegetic radio, CC0 (D43)
ENGELBACH = "Jerry Engelbach"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InstalledMusicTests(unittest.TestCase):
    def test_the_installed_set_is_exactly_the_d43_set(self):
        self.assertEqual(sorted(INSTALLED),
                         sorted(p.stem for p in MUSIC_ASSETS.glob("*.mid")))
        self.assertEqual([], [p.name for p in MUSIC_ASSETS.iterdir()
                              if p.suffix.lower() != ".mid"])

    def test_every_lump_is_a_legal_name_and_a_clean_midi(self):
        for path in sorted(MUSIC_ASSETS.glob("*.mid")):
            with self.subTest(lump=path.stem):
                self.assertEqual(path.stem, validate_lump_name(path.stem))
                info = midi_inspect.parse(path)
                self.assertEqual(0, info["hanging"], "a hanging note drones under the map")
                self.assertGreater(info["notes"], 0)

    def test_every_lump_has_provenance_in_both_registers(self):
        licenses = LICENSES.read_text(encoding="utf-8")
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        for lump in INSTALLED:
            with self.subTest(lump=lump):
                self.assertIn(f"`{lump}`", licenses)
                self.assertIn(lump, rights)

    def test_d_sdm01_is_what_the_generator_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _seconds, _size = gen_music.generate("map01", Path(tmp), None, quiet=True)
            self.assertEqual(sha256(MUSIC_ASSETS / "D_SDM01.mid"), sha256(path))

    def test_d_sdintl_is_engelbachs_file_with_the_head_silence_trimmed(self):
        source = CANDIDATES / ENGELBACH_SOURCE
        fmt, division, tracks = midi_edit.read_smf(source.read_bytes())
        start = midi_edit.first_note_tick(tracks)
        self.assertEqual(2863, start, "the 1.99 s hole SOUNDTRACK.md 4.1 measured")
        midi_edit.trim_head(tracks, start)
        rebuilt = midi_edit.write_smf(fmt, division, tracks)
        self.assertEqual(hashlib.sha256(rebuilt).hexdigest(),
                         sha256(MUSIC_ASSETS / "D_SDINTL.mid"))


class CandidateTests(unittest.TestCase):
    def test_discards_are_gone_and_the_radio_pieces_stay(self):
        for name in DISCARDED:
            self.assertFalse((CANDIDATES / name).exists(), name)
        for name in RADIO:
            self.assertTrue((CANDIDATES / name).is_file(), name)

    def test_every_candidate_hash_is_recorded_in_music_rights(self):
        rights = MUSIC_RIGHTS.read_text(encoding="utf-8")
        files = sorted(CANDIDATES.glob("*.mid"))
        self.assertTrue(files)
        for path in files:
            with self.subTest(file=path.name):
                self.assertIn(sha256(path), rights)

    def test_every_candidate_has_a_registered_lump_and_vice_versa(self):
        registered = audition.read_registry(REGISTRY)
        present = {p.name for p in CANDIDATES.glob("*.mid")}
        self.assertEqual(present, set(registered))
        lumps = list(registered.values())
        self.assertEqual(len(lumps), len(set(lumps)), "two files share a lump")
        for lump in lumps:
            validate_lump_name(lump)
        # retired numbers are kept, commented, so they are never handed out again
        text = REGISTRY.read_text(encoding="utf-8")
        for name in DISCARDED:
            self.assertIn(name, text)


class CreditTests(unittest.TestCase):
    def test_engelbach_is_credited_wherever_the_credits_live(self):
        for doc in (MUSIC_RIGHTS, SOUNDTRACK, LICENSES):
            with self.subTest(doc=doc.name):
                self.assertIn(ENGELBACH, doc.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
