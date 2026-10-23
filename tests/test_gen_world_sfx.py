#!/usr/bin/env python3
"""Contract of tools/audio/gen_world_sfx.py (the world-sound candidates; D125 installed 50 of
them and a layered oof through tools/audio/master_world_sfx.py, tests/test_world_sfx_install.py).

Cheap tier (no rendering, no work/ files):

  table      every event 2-3 candidates numbered 1..k with ONE recommended;
             lump names valid, SD-prefixed, unique, not already in SNDINFO;
             every Freedoom reference has a target and a length
  licences   every source CC0 1.0 or ours (this round has no CC BY); no NC,
             ND or SA anywhere; downloads only under sfx_sources/world/
             (or the D36 packs and the voice reference pack already on disk)
  rules      the IZh pickup sits the weapon pickups' allowance under DSWPNUP;
             only the moving floor is a loop
  loop       make_loop is seamless: the seam steps like any other sample
  level      a synthetic burst lands on its target, peak at -1 dBFS

Slow tier (SD_SKIP_SLOW_ART skips it):

  freedoom   the targets re-measured from iwads/freedoom2.wad (when present)
  synthesis  every candidate without sources renders, lands within 1 dB of
             its target (the exit switch excepted, reported on the page) and
             under the decoded-peak ceiling; the page carries every id
"""
from __future__ import annotations

import json
import os
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools" / "audio"))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

try:
    import numpy as np
    import gen_world_sfx as w
except ImportError:                                    # pragma: no cover
    np = None
    w = None

from sdbuild.wad import validate_lump_name  # noqa: E402

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
SLOW_SKIPPED = bool(os.environ.get("SD_SKIP_SLOW_ART"))
slow = unittest.skipIf(SLOW_SKIPPED, "renders audio: verify.py art")
SNDINFO = PROJECT_ROOT / "src" / "lumps" / "SNDINFO"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"

ALLOWED_LICENCES = {"CC0 1.0", "ours"}
ALLOWED_PREFIXES = ("sfx_sources/world/", "sfx_sources/ken-imp/", "sfx_sources/oga-100/",
                    "voice_refs/haeldb/", "assets/sounds/")
# Freedoom's exit switch is an 8-bit, clipped lump at -5 dB A: a clean transient stays short of it
SHORT_ALLOWED = {"SDSWTCHX"}


@needs_numpy
class TableTests(unittest.TestCase):
    def test_every_event_has_two_or_three_numbered_candidates_and_one_recommended(self):
        for e in w.EVENTS:
            cs = [c for c in w.CANDS if c.lump == e.lump]
            self.assertIn(len(cs), (2, 3), e.lump)
            self.assertEqual([c.n for c in cs], list(range(1, len(cs) + 1)), e.lump)
            self.assertEqual(sum(c.rec for c in cs), 1, e.lump)
        self.assertEqual({c.lump for c in w.CANDS}, {e.lump for e in w.EVENTS})

    def test_lump_names(self):
        taken = set(re.findall(r"\b(SD[A-Z0-9]{2,6})\b", SNDINFO.read_text(encoding="utf-8")))
        names = [e.lump for e in w.EVENTS]
        self.assertEqual(len(names), len(set(names)))
        for n in names:
            validate_lump_name(n)
            self.assertTrue(n.startswith("SD"), n)
            self.assertNotIn(n, taken, f"{n} already ships")

    def test_every_reference_has_a_target_and_a_length(self):
        for e in w.EVENTS:
            self.assertIn(e.ref, w.FREEDOOM_LOUD_A)
            self.assertIn(e.ref, w.FREEDOOM_LENGTH_S)
            self.assertTrue(e.engine and e.ev and e.why and e.group)

    def test_kinds(self):
        kinds = {"síntesis", "grabación", "mezcla", "voz grabada", "voz IA"}
        for c in w.CANDS:
            self.assertIn(c.kind, kinds, c.name)
            if c.kind == "síntesis":
                self.assertEqual(c.sources, (), c.name)
            if c.kind == "voz IA":
                self.assertTrue(any(k.startswith("ai:") for k in c.sources), c.name)


@needs_numpy
class LicenceTests(unittest.TestCase):
    def test_sources_are_cc0_or_ours(self):
        for k, s in w.SOURCES.items():
            self.assertIn(s.licence, ALLOWED_LICENCES, k)
            self.assertNotRegex(s.licence + s.who, r"\b(NC|ND|SA)\b", k)
            self.assertTrue(s.path.startswith(ALLOWED_PREFIXES), s.path)
            if s.licence != "ours":
                self.assertTrue(s.url.startswith("https://"), k)

    def test_every_candidate_source_is_known(self):
        for c in w.CANDS:
            for k in c.sources:
                if k.startswith("ai:"):
                    self.assertIn(k[3:], w.AI.values(), c.name)
                else:
                    self.assertIn(k, w.SOURCES, c.name)

    def test_chips_name_every_source(self):
        for c in w.CANDS:
            chips = w.licence_chips(c)
            self.assertGreaterEqual(len(chips), len(c.sources), c.name)
            self.assertTrue(all(ch["l"] in ("CC0 1.0", "nuestro", "voz IA") for ch in chips), c.name)


@needs_numpy
class RuleTests(unittest.TestCase):
    def test_izh_pickup_follows_the_weapon_pickups(self):
        e = w.EVENT["SDIZPKP"]
        self.assertEqual(e.ref, "DSWPNUP")
        self.assertAlmostEqual(e.target_db, w.FREEDOOM_LOUD_A["DSWPNUP"] - w.alts.ALLOWANCE_DB["pickup"])
        for e in w.EVENTS:
            if e.lump != "SDIZPKP":
                self.assertEqual(e.offset_db, 0.0, e.lump)

    def test_only_the_moving_floor_loops(self):
        self.assertEqual([e.lump for e in w.EVENTS if e.loop], ["SDPMOVE"])

    def test_make_loop_is_seamless(self):
        rng = np.random.default_rng(1)
        x = np.cumsum(rng.standard_normal(w.gws.n_of(1.0))) * 1e-3     # a slow random walk
        loop = w.make_loop(x, 0.4)
        steps = np.abs(np.diff(np.concatenate([loop, loop[:1]])))
        self.assertLess(steps[-1], 6 * np.median(steps))
        self.assertEqual(len(loop), w.gws.n_of(0.4))
        with self.assertRaises(ValueError):
            w.make_loop(x[:100], 0.4)

    def test_level_hits_the_target(self):
        rng = np.random.default_rng(2)
        n = w.gws.n_of(0.3)
        x = rng.standard_normal(n) * w.gws.env(n, 0.001, 0.05)
        for target in (-20.0, -12.0):
            y, lim = w.level(x, target)
            self.assertAlmostEqual(w.alts.loud_a_db(y), target, delta=0.2)
            self.assertLessEqual(np.max(np.abs(y)), 10 ** (w.PEAK_DBFS / 20) + 1e-9)


@needs_numpy
@slow
class FreedoomTests(unittest.TestCase):
    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not here")
    def test_targets_are_measured(self):
        import gen_sfx as gs
        for name, v in w.FREEDOOM_LOUD_A.items():
            x, rate = gs.dmx_to_float(gs.wad_lump(IWAD, name))
            self.assertAlmostEqual(w.alts.loud_a_db(x, rate), v, delta=0.01, msg=name)
            self.assertAlmostEqual(len(x) / rate, w.FREEDOOM_LENGTH_S[name], delta=0.01, msg=name)


@needs_numpy
@slow
class SynthesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.done = [w.render(c) for c in w.CANDS if not c.sources]

    def test_every_synthetic_candidate_lands(self):
        self.assertGreaterEqual(len(self.done), 15)
        for d in self.done:
            e = w.EVENT[d.cand.lump]
            if e.lump not in SHORT_ALLOWED:
                self.assertAlmostEqual(d.levels["loud_a"], e.target_db, delta=1.0, msg=d.cand.name)
            self.assertLessEqual(w.mws.decoded_peak_db(d.ogg), w.mws.DECODED_PEAK_CEILING_DBFS + 0.01, d.cand.name)
            self.assertLess(d.levels["length"], 2.0, d.cand.name)

    def test_renders_are_deterministic(self):
        c = next(c for c in w.CANDS if c.name == "SDTELEPT_w1")
        a, b = w.render(c), w.render(c)
        self.assertTrue(np.array_equal(a.y, b.y))

    def test_page_carries_every_id(self):
        page = w.page_html(self.done)
        items = json.loads(re.search(r"const ITEMS = (\[.*?\]);\n", page, re.S).group(1))
        self.assertEqual({i["id"] for i in items}, {d.cand.name for d in self.done})
        self.assertNotIn("__", page.replace("__proto__", ""))
        self.assertIn("Copiar resultado", page)


if __name__ == "__main__":
    unittest.main()
