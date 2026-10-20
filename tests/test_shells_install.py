"""D81 (2026-10-20): the Doughboy's and the Panzermensch's shells are ours (M2b-i).

The CEO took the recommended option of both sweeps ("los que tú
recomiendas", D81; `docs/art/previews/2026-10-19_2200_F5_enemy-shells.html`):
option A, the Doughboy's "comet" `SDDL` and the Panzermensch's (and the
Schwer's) "ember" `SDPL`, drawn by `tools/art/gen_shells.py` into
`work/art/shells/SDDL/` and `.../SDPL/`. Their five lumps each ship beside
their throwers, in `assets/sprites/doughboy/` and
`assets/sprites/panzermensch/`. MOD-SPEC 6.3, "The two enemy shells,
installed by D81". What is checked, and why:

  behaviour  each class's States block is the one at HEAD e84c56c, before
             D81, line for line (label, frames, tics, Bright, flow), with
             only BAL2 renamed SDDL and BAL7 SDPL; the additive render
             style and the class's constants are untouched
  sprite     no state anywhere names BAL2 or BAL7, MOD-SPEC 5.1 no longer
             declares them, and the shell zs do not mention them even in a
             comment; every frame a state uses has its lump and every lump
             is used
  files      exactly the five lumps per shell, rotation 0, each with a grAb
             chunk before its image data equal to gen_shells.grab (the ball
             centred half the actor's Height over z); RGBA with hard alpha,
             inside palette v1; where work/ exists each is byte-identical to
             the approved render, and where numpy is installed a fresh
             render of option A gives the same pixels
  package    the built PK3 carries them flat as sprites/<NAME>.png and
             check_pk3 passes sprites and licences
  licences   every lump has an own-work row (CC BY-NC-SA 4.0) naming
             gen_shells.py
  bestiary   BESTIARY.md lists both shells as installed and nothing under
             "Still on Freedoom placeholders"

Doom's own CacodemonBall (BAL2) and BaronBall (BAL7) are not touched; no
class of ours fires them.

Stdlib only, but for the palette and render checks (Pillow, numpy).
"""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
MONSTERS = SRC_DIR / "zscript" / "monsters"
ASSET_SPRITES = PROJECT_ROOT / "assets" / "sprites"
WORK_SHELLS = PROJECT_ROOT / "work" / "art" / "shells"
BESTIARY = PROJECT_ROOT / "docs" / "engine" / "BESTIARY.md"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "art"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_pk3  # noqa: E402
import licences  # noqa: E402
import palette as palette_mod  # noqa: E402  (stdlib only)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_panzermensch_sprites import PNG_SIGNATURE, read_grab  # noqa: E402
from test_ppsh_sprites import frame_rows, states  # noqa: E402

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:   # CI's stdlib-only interpreter
    HAVE_PIL = False
try:
    import numpy as np
    import gen_shells
    HAVE_NUMPY = HAVE_PIL
except ImportError:
    HAVE_NUMPY = False

# shell -> (its .zs, the class, Freedoom's placeholder, ours, the folder it
# shares with its thrower, canvas side, grAb as gen_shells drew it)
SHELLS = {
    "doughboy": ("doughboy_shell.zs", "SD_DoughboyShell", "BAL2", "SDDL", "doughboy", 48, (24, 28)),
    "panzer": ("panzer_shell.zs", "SD_PanzerShell", "BAL7", "SDPL", "panzermensch", 56, (28, 36)),
}
FRAMES = "ABCDE"
CONSTANTS = {"doughboy_shell.zs": {"RADIUS": 6, "HEIGHT": 8, "SPEED": 10, "FASTSPEED": 20, "DAMAGE": 5},
             "panzer_shell.zs": {"RADIUS": 6, "HEIGHT": 16, "SPEED": 15, "FASTSPEED": 20, "DAMAGE": 8}}


def _before(old: str) -> tuple:
    """The States block at HEAD e84c56c (2026-10-20), before D81."""
    return (("Spawn", ":", "", 0, ""), ("Spawn", old, "AB", 4, "Bright"), ("Spawn", "->", "Loop", 0, ""),
            ("Death", ":", "", 0, ""), ("Death", old, "CDE", 6, "Bright"), ("Death", "->", "Stop", 0, ""))


def zs(key: str) -> Path:
    return MONSTERS / SHELLS[key][0]


def lumps(key: str) -> list[Path]:
    ours, folder = SHELLS[key][3], SHELLS[key][4]
    return sorted((ASSET_SPRITES / folder).glob(f"{ours}*.png"))


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d81_ones_but_for_the_name(self):
        for key, (_, _, old, ours, *_rest) in SHELLS.items():
            expected = [(lb, ours if sp == old else sp, fr, tics, rest) for lb, sp, fr, tics, rest in _before(old)]
            self.assertEqual(states(zs(key)), expected, key)

    def test_render_style_and_constants_untouched(self):
        import re
        for key in SHELLS:
            text = zs(key).read_text(encoding="utf-8")
            self.assertIn('RenderStyle "Add";', text, key)
            self.assertIn("+ZDOOMTRANS", text, key)
            got = {k: int(v) for k, v in re.findall(r"const\s+SD_\w+?SHELL_(\w+)\s*=\s*(\d+)\s*;", text)}
            self.assertEqual(got, CONSTANTS[SHELLS[key][0]], key)


class SpriteTests(unittest.TestCase):
    def test_no_state_anywhere_names_bal2_or_bal7(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & {"BAL2", "BAL7"}, path.name)

    def test_the_shell_files_do_not_mention_them(self):
        for key, (_, _, old, *_rest) in SHELLS.items():
            self.assertNotIn(old, zs(key).read_text(encoding="utf-8"), f"{key}: not even in a comment")

    def test_mod_spec_retires_them(self):
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertFalse({"BAL2", "BAL7"} & declared)

    def test_every_frame_used_is_installed_and_every_lump_used(self):
        for key, (_, _, _, ours, *_rest) in SHELLS.items():
            used = {f"{sp}{f}0" for _, sp, frames, _, _ in frame_rows(states(zs(key))) for f in frames}
            self.assertEqual({p.stem for p in lumps(key)}, used, key)
            self.assertEqual(used, {f"{ours}{f}0" for f in FRAMES}, key)


class FileTests(unittest.TestCase):
    def test_canvas_and_offsets(self):
        for key, (*_, side, grab) in SHELLS.items():
            for p in lumps(key):
                data = p.read_bytes()
                self.assertTrue(data.startswith(PNG_SIGNATURE), p)
                self.assertEqual(struct.unpack(">II", data[16:24]), (side, side), p.name)
                self.assertEqual(read_grab(data), grab, f"{p.name}: grAb before IDAT")
        if HAVE_NUMPY:
            for key, (*_, grab) in SHELLS.items():
                self.assertEqual(gen_shells.grab(key), grab, key)

    @unittest.skipUnless(all((WORK_SHELLS / v[3]).is_dir() for v in SHELLS.values()),
                         "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for key, (_, _, _, ours, *_rest) in SHELLS.items():
            for p in lumps(key):
                source = WORK_SHELLS / ours / p.name
                self.assertTrue(source.is_file(), source)
                self.assertEqual(p.read_bytes(), source.read_bytes(), p)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_rgba_hard_alpha_palette_v1(self):
        v1 = set(palette_mod.colours(1))
        for key in SHELLS:
            for p in lumps(key):
                with Image.open(p) as img:
                    self.assertEqual(img.mode, "RGBA", p.name)
                    raw = img.tobytes()
                self.assertLessEqual(set(raw[3::4]), {0, 255}, p.name)
                used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
                self.assertFalse(used - v1, p.name)

    @unittest.skipUnless(HAVE_NUMPY, "numpy/Pillow not available in this interpreter")
    def test_a_fresh_render_of_option_a_gives_the_same_pixels(self):
        for key in SHELLS:
            self.assertEqual(gen_shells.RECOMMENDED[key], "A", "D81: option A for both")
            for f, path in zip(FRAMES, lumps(key)):
                with Image.open(path) as img:
                    installed = np.asarray(img.convert("RGBA"))
                np.testing.assert_array_equal(installed, gen_shells.render(key, "A", f), err_msg=f"{key} {f}")


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pk3 = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, cls.pk3, TOOLS_DIR, PROJECT_ROOT / "assets")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_flat_under_sprites(self):
        with zipfile.ZipFile(self.pk3) as zf:
            names = set(zf.namelist())
            for key in SHELLS:
                for p in lumps(key):
                    self.assertIn(f"sprites/{p.name}", names)
                    self.assertEqual(zf.read(f"sprites/{p.name}"), p.read_bytes())

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


class LicenceTests(unittest.TestCase):
    def test_every_lump_has_an_own_work_row(self):
        rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
        for key in SHELLS:
            for p in lumps(key):
                found = [r for r in rows if r.covers(f"sprites/{p.name}")]
                self.assertEqual(len(found), 1, f"{p.stem}: {len(found)} rows in docs/art/LICENSES.md")
                self.assertTrue(found[0].own_work, p.stem)
                self.assertEqual(found[0].required, licences.OWN_WORK_CREDITS, p.stem)
            first = next(r for r in rows if r.covers(f"sprites/{SHELLS[key][3]}A0.png"))
            self.assertIn("tools/art/gen_shells.py", first.origin, key)
            self.assertIn("option A", first.origin, key)


class BestiaryTests(unittest.TestCase):
    def test_listed_as_installed_and_no_placeholder_left(self):
        text = BESTIARY.read_text(encoding="utf-8")
        for key, (_, cls, old, ours, folder, *_rest) in SHELLS.items():
            row = next(ln for ln in text.splitlines() if ln.startswith(f"| `{cls}` | `{ours}` | 5, "))
            self.assertIn(f"assets/sprites/{folder}/", row)
            self.assertIn(f"`{old}`", row)
            self.assertIn("D81", row)
        section = text[text.index("**Still on Freedoom placeholders"):text.index("**Sounds:")]
        self.assertNotIn("| `SD_", section, "no class is left on a Freedoom sprite")


if __name__ == "__main__":
    unittest.main()
