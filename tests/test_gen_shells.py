"""Contract of tools/art/gen_shells.py (F5, backlog M2b: the Doughboy's shell
SDDL and the Panzermensch's / Schwer's shell SDPL, sweep and full sets).

Cheap tests (no rendering, always run):

  no font     the generator never rasterises text, never writes palette.json
              and never writes under assets/ or src/
  frames      the letters and counts come from the two .zs: Spawn A B, Death
              C D E, RenderStyle "Add"; each shell's sprite there is still
              the Freedoom placeholder or ours, nothing else
  geometry    the grAb hangs the centre half the class's Height above z
  options     three per shell; option A's materials are gen_heavy's own
              objects (the approved attack frames' shell); every material is
              flat (a glow); faction ramps kept (ART-BIBLE §6.2)
  prefixes    SDDL and SDPL collide with nothing: every doc mention is this
              shell's reservation, no other generator or ZScript file uses
              them, no IWAD lump or installed sprite of another set starts
              with them

Render tests (`tools/verify.py art`; SD_SKIP_SLOW_ART skips them):

  palette     every option's every frame is palette v2, hard alpha, inside
              its canvas
  seed        the same frame renders identically twice
  legibility  SDDL is not the storm bolt (centre and rim the other way
              round, larger); SDPL is the larger, heavier shell
  disk        the rendered full sets (when present) carry their grAb
"""

from __future__ import annotations

import os
import re
import struct
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_shells.py"
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the shells' renders")
# What a doc line that names one of the two sprites must also name: the shell it is reserved for.
# A line listing several prefixes (BESTIARY §2.3's namespace check) is a registry line, also fine.
OWNER_WORDS = {"SDDL": ("Doughboy", "DoughboyShell", "projectile", "shell", "BAL2"),
               "SDPL": ("Panzer", "PanzerShell", "projectile", "shell", "BAL7")}
REGISTRY_MIN = 3
REGISTRY_NAME = re.compile(r"\bSD[A-Z]{2}\b")


class NoFontTests(unittest.TestCase):
    def test_no_font_no_palette_write_no_install(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("ImageFont", src)
        self.assertNotIn("truetype", src)
        self.assertNotRegex(src, r"PALETTE_JSON|palette\.json\"\)\.write")
        self.assertNotRegex(src, r"ASSETS\s*/[^\n]*(save|write)")
        self.assertNotIn("shutil", src)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_shells
        cls.g = gen_shells

    def test_frames_come_from_the_zs(self):
        g = self.g
        for k, sh in g.SHELLS.items():
            st = g.zs_states(sh.zs)
            self.assertEqual("".join(f for _, f, _ in st["Spawn"]), g.FLIGHT, k)
            self.assertEqual("".join(f for _, f, _ in st["Death"]), g.BURST, k)
            self.assertEqual(set(st), {"Spawn", "Death"}, k)
            names = {s for seq in st.values() for s, _, _ in seq}
            self.assertEqual(len(names), 1, k)
            self.assertIn(names.pop(), (sh.placeholder, sh.sprite), k)
            self.assertIn('RenderStyle "Add"', sh.zs.read_text(encoding="utf-8"), k)
            self.assertIn(sh.cls, sh.zs.read_text(encoding="utf-8"), k)
        self.assertEqual(g.FRAMES, "ABCDE")
        self.assertTrue(set(g.SWEEP_FRAMES) <= set(g.FRAMES))
        self.assertTrue(set(g.SWEEP_FRAMES) & set(g.FLIGHT) and set(g.SWEEP_FRAMES) & set(g.BURST))

    def test_lumps_and_grab(self):
        g = self.g
        for k, sh in g.SHELLS.items():
            names = [g.lump(k, f) for f in g.FRAMES]
            self.assertEqual(names, [f"{sh.sprite}{f}0" for f in "ABCDE"])
            self.assertTrue(all(len(n) <= 8 for n in names))
            height = g.zs_const(sh.zs, "HEIGHT")
            gx, gy = g.grab(k)
            self.assertEqual(gx, sh.canvas.w // 2, k)
            self.assertEqual(gy, sh.canvas.h // 2 + height // 2, k)      # centre at half the Height over z
            self.assertEqual(sh.canvas.w, sh.canvas.h)
            self.assertEqual(g.full_path(k, "A").parent, g.OUT_DIR / sh.sprite)
        self.assertEqual(g.OUT_DIR, PROJECT_ROOT / "work" / "art" / "shells")

    def test_options(self):
        g = self.g
        import gen_heavy
        for k in g.SHELLS:
            self.assertEqual(list(g.OPTIONS[k]), ["A", "B", "C"], k)
            self.assertIn(g.RECOMMENDED[k], g.OPTIONS[k])
            self.assertTrue(g.RECOMMENDATION_WHY[k], k)
        for n in ("sdl_core", "sdl_trail"):
            self.assertIs(g.MATERIALS[n], gen_heavy.DB_NEW[n])
        for n in ("pzl_core", "pzl_shell", "pzl_smoke"):
            self.assertIs(g.MATERIALS[n], gen_heavy.PM_NEW[n])
        for n, m in g.MATERIALS.items():
            self.assertTrue(m.flat, n)

    def test_faction_ramps(self):
        g = self.g
        for n, m in g.MATERIALS.items():
            forbidden = g.LEGION_FORBIDDEN if n.startswith("sdl_") else g.REICH_FORBIDDEN
            self.assertFalse(m.ramps & forbidden, n)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class PrefixTests(unittest.TestCase):
    """SDDL and SDPL are reserved for these two shells and nobody else's."""

    @classmethod
    def setUpClass(cls):
        import gen_shells
        cls.g = gen_shells

    def test_form(self):
        names = [sh.sprite for sh in self.g.SHELLS.values()]
        self.assertEqual(len(set(names)), len(names))
        for n in names:
            self.assertRegex(n, r"^SD[A-Z]{2}$")

    def test_docs_reserve_them_for_these_shells(self):
        for sh in self.g.SHELLS.values():
            for doc in ("docs/engine/BESTIARY.md", "docs/engine/MOD-SPEC.md", "docs/art/LICENSES.md",
                        "docs/art/TEXTURE-INDEX.md"):
                for line in (PROJECT_ROOT / doc).read_text(encoding="utf-8").splitlines():
                    if re.search(rf"\b{sh.sprite}", line):
                        registry = len(re.findall(REGISTRY_NAME, line)) >= REGISTRY_MIN
                        self.assertTrue(registry or any(w in line for w in OWNER_WORDS[sh.sprite]),
                                        f"{doc}: {line[:120]}")

    def test_no_other_generator_or_class_uses_them(self):
        for sh in self.g.SHELLS.values():
            for py in sorted(ART_TOOLS.glob("*.py")):
                if py.name == SOURCE.name:
                    continue
                self.assertNotRegex(py.read_text(encoding="utf-8"), rf"=\s*[\"']{sh.sprite}[\"']", py.name)
            for zs in sorted((PROJECT_ROOT / "src").rglob("*.zs")):
                if zs == sh.zs:
                    continue
                for line in zs.read_text(encoding="utf-8").splitlines():
                    code = line.split("//")[0]
                    self.assertNotRegex(code, rf"\b{sh.sprite}\b", zs.name)

    def test_no_installed_sprite_or_iwad_lump_starts_with_them(self):
        prefixes = {p.name[:4] for p in (PROJECT_ROOT / "assets" / "sprites").rglob("*.png")}
        for k, sh in self.g.SHELLS.items():
            for png in (PROJECT_ROOT / "assets").rglob(f"{sh.sprite}*.png"):   # only after the install: ours
                ours = self.g.full_path(k, png.stem[4])
                if not ours.parent.is_dir():
                    continue    # a clean checkout has no gitignored work/ (QA-M4-1)
                self.assertTrue(ours.is_file(), png)
                self.assertEqual(png.read_bytes(), ours.read_bytes(), png)
            if not any((PROJECT_ROOT / "assets").rglob(f"{sh.sprite}*.png")):
                self.assertNotIn(sh.sprite, prefixes)
        iwad = PROJECT_ROOT / "iwads" / "freedoom2.wad"
        if not iwad.is_file():
            self.skipTest("iwads/freedoom2.wad not on this machine")
        data = iwad.read_bytes()
        _, n, off = struct.unpack("<4sii", data[:12])
        lumps = {data[off + 16 * i + 8:off + 16 * i + 16].rstrip(b"\0").decode("ascii", "replace")
                 for i in range(n)}
        for sh in self.g.SHELLS.values():
            self.assertFalse([x for x in lumps if x.startswith(sh.sprite)], sh.sprite)


@slow
@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_heavy
        import gen_shells as g
        cls.g = g
        cls.v2 = set(gen_heavy.palette_v2())
        cls.spr = {(k, o, f): g.render(k, o, f) for k in g.SHELLS for o in g.OPTIONS[k] for f in g.FRAMES}

    def test_palette_and_hard_alpha(self):
        for key, rgba in self.spr.items():
            a = rgba[..., 3]
            self.assertTrue(set(np.unique(a)) <= {0, 255}, key)
            self.assertTrue((a > 0).any(), key)
            self.assertTrue({tuple(int(v) for v in p) for p in rgba[..., :3][a > 0]} <= self.v2, key)
            sh = self.g.SHELLS[key[0]]
            self.assertEqual(rgba.shape, (sh.canvas.h, sh.canvas.w, 4), key)

    def test_deterministic(self):
        g = self.g
        for k in g.SHELLS:
            np.testing.assert_array_equal(g.render(k, g.RECOMMENDED[k], "A"), self.spr[(k, g.RECOMMENDED[k], "A")])

    def test_doughboy_shell_is_not_the_bolt(self):
        g = self.g
        bolt = g.references().get("SDBLA0")
        if bolt is None:
            self.skipTest("SDBL is not installed")
        mb = g.measure(bolt)
        md = g.measure(self.spr[("doughboy", g.RECOMMENDED["doughboy"], "A")])
        self.assertNotEqual((md["centre"], md["rim"]), (mb["centre"], mb["rim"]))
        self.assertGreater(md["px"], mb["px"])

    def test_panzer_shell_is_the_heaviest_in_flight(self):
        g = self.g
        mp = g.measure(self.spr[("panzer", g.RECOMMENDED["panzer"], "A")])
        md = g.measure(self.spr[("doughboy", g.RECOMMENDED["doughboy"], "A")])
        self.assertGreater(mp["px"], md["px"])
        bolt = g.references().get("SDBLA0")
        if bolt is not None:
            self.assertGreater(mp["w"], g.measure(bolt)["w"])

    def test_bursts_grow_then_fade(self):
        g = self.g
        for k in g.SHELLS:
            o = g.RECOMMENDED[k]
            m = [g.measure(self.spr[(k, o, f)]) for f in g.BURST]
            self.assertLess(g.measure(self.spr[(k, o, "A")])["w"], m[0]["w"], k)
            self.assertGreater(m[0]["luma"], m[2]["luma"], k)

    def test_full_sets_on_disk(self):
        g = self.g
        for k in g.SHELLS:
            if not g.full_path(k, "A").is_file():
                self.skipTest("the full sets are not rendered on this machine (work/ is gitignored)")
            for f in g.FRAMES:
                path = g.full_path(k, f)
                self.assertEqual(g.core.read_grab(path), g.grab(k), path)
                rgba = np.asarray(Image.open(path).convert("RGBA"))
                np.testing.assert_array_equal(rgba, self.spr[(k, g.RECOMMENDED[k], f)])


if __name__ == "__main__":
    unittest.main()
