"""tools/audio/gen_weapon_alts_animated.py: the D92 page that plays each
weapon's installed frames in sync with the D74 alternatives.

The timelines are read from src/zscript and assets/ (tracked), so those
tests run everywhere; the page build needs the gitignored work/audio files
and skips without them. Nothing is written to the repo: the page goes to a
temp directory.

Run:  .venv/Scripts/python.exe -m unittest tests.test_gen_weapon_alts_animated -v
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "audio"))

import gen_weapon_alts_animated as g  # noqa: E402

HAVE_AUDIO = (ROOT / "work" / "audio" / "alt" / "SDRKFIR_alt1.ogg").exists()


class Timelines(unittest.TestCase):
    def test_izh_reload_follows_the_state_and_its_sound_hook(self):
        a = g.izh_reload()
        reload = g.parse_state(g.WEAPONS / "izh.zs", "Reload")
        self.assertEqual([s["spr"] for s in reload][:1], ["SDIZD0"])
        # one sound, on the first tic of the Reload state
        self.assertEqual(a["sounds"], [[g.PRE, None]])
        shown = [f["s"] for f in a["frames"][g.PRE:g.PRE + sum(s["tics"] for s in reload)]]
        expected = [s["spr"] for s in reload for _ in range(s["tics"])]
        self.assertEqual(shown, expected)

    def test_roks_restarts_the_sound_every_jet_and_cuts_the_previous(self):
        a = g.roks_fire()
        starts = [s for s, _ in a["sounds"]]
        self.assertGreater(len(starts), 10)
        self.assertEqual({b - a_ for a_, b in zip(starts, starts[1:])}, {3})
        for (s, stop), (nxt, _) in zip(a["sounds"], a["sounds"][1:]):
            self.assertEqual(stop, nxt)           # CHAN_WEAPON: the new one cuts the old
        self.assertIsNone(a["sounds"][-1][1])     # the last one rings out
        self.assertLess(starts[-1], g.PRE + g.HELD)
        # every jet shows the gun flash, and the 20-tic B frame only after release
        self.assertTrue(all(f.get("fl") == "SDKFA0" for f in a["frames"][g.PRE:g.PRE + 3]))
        first_b = next(i for i, f in enumerate(a["frames"]) if f["s"] == "SDRKB0")
        self.assertGreaterEqual(first_b, g.PRE + g.HELD)

    def test_pickup_sound_on_touch_then_lower_and_raise_at_six_units(self):
        for lump in g.PICKUPS:
            a = g.pickup(lump)
            touch = a["sounds"][0][0]
            self.assertEqual(touch, g.WALK)
            self.assertTrue(all("w" in f for f in a["frames"][:touch]))
            self.assertFalse(any("w" in f for f in a["frames"][touch:]))
            new = g.PICKUPS[lump][2]
            ys = [f["y"] for f in a["frames"] if f["s"] == new]
            raise_ys = ys[:ys.index(g.WEAPONTOP) + 1]
            self.assertEqual(len(raise_ys), (g.WEAPONBOTTOM - g.WEAPONTOP) // g.RAISE)
            self.assertTrue(all(b - a_ == -g.RAISE for a_, b in zip(raise_ys, raise_ys[1:])))

    def test_sprite_offsets_come_from_grab(self):
        w, h, ox, oy = g.grab(g.SPRITES / "izh" / "SDIZA0.png")
        self.assertGreater(w, 0)
        self.assertLess(ox, 0)  # first-person sprites carry negative offsets


@unittest.skipUnless(HAVE_AUDIO, "work/audio/alt not present (gitignored)")
class Page(unittest.TestCase):
    def test_page_has_15_rows_embedded_audio_and_relative_sprites(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = g.main(["--stamp", "2000-01-01_0000", "--out-dir", tmp])
            html = out.read_text(encoding="utf-8")
        self.assertNotIn("__DATA__", html)
        self.assertNotIn("__STAMP__", html)
        data = json.loads(re.search(r"const D = (\{.*?\});\n", html, re.S)[1])
        self.assertEqual(len(data["items"]), 15)
        self.assertEqual(set(data["anims"]), {"SDTTPKP", "SDAXPKP", "SDIZPKP", "SDIZRLD", "SDRKFIR"})
        self.assertTrue(all(s["src"].startswith("../../../assets/sprites/") for s in data["sprites"].values()))
        audio = json.loads(re.search(r"const AUD = (\{.*?\});\n", html, re.S)[1])
        for it in data["items"]:
            for k in ("src", "rej", "repSrc"):
                self.assertTrue(audio[it[k]].startswith("data:audio/"))


if __name__ == "__main__":
    unittest.main()
