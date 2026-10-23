"""D82 (2026-10-20): the player effects and the last world sprites are ours (M2c-i).

The CEO took option A of every item ("también las recomendadas", D82;
`docs/art/previews/2026-10-19_2208_F4_player-effects.html`), drawn by
`tools/art/gen_effects.py` into `work/art/effects/<SPRITE>/`. The fifty
lumps ship in `assets/sprites/effects/`. MOD-SPEC 5.1 ("Retired ... (D82)",
"The engine actors' overrides") and 6.3 ("The player effects, installed by
D82"). What is checked, and why:

  behaviour  the three projectile classes' States blocks are the ones at
             HEAD c68ad84, before D82, line for line (label, tics, action,
             flow), with only MISL A -> SDPG/SDKR A, MISL B/C/D -> SDPX
             A/B/C and PLSS/PLSE -> SDFJ/SDFX; the flame's Add 0.85 and the
             classes' constants are untouched
  retired    no States block anywhere names MISL, PLSS or PLSE, MOD-SPEC
             5.1 declares no IWAD sprite at all, and the three projectile
             files do not name the old lumps even in a comment
  overrides  the seven engine-actor sprites ship under the IWAD's names
             with exactly Freedoom's lump set (iwads/ where present; else
             the set as read on 2026-10-20), all rotation 0, and no
             States block of ours names them
  files      exactly the fifty lumps; every frame a state uses is shipped
             and every SD lump is used; each PNG has a grAb chunk before
             its image data equal to the manifest's; RGBA with hard alpha,
             inside palette v1; where work/ exists each is byte-identical
             to the approved render, and (slow) a fresh render of option A
             gives the same pixels
  package    the built PK3 carries them flat as sprites/<NAME>.png and
             check_pk3 passes sprites and licences
  licences   every lump has exactly one own-work row naming gen_effects.py
             and option A

Stdlib only, but for the palette and render checks (Pillow, numpy).
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
WEAPONS_ZS = SRC_DIR / "zscript" / "weapons"
EFFECTS = PROJECT_ROOT / "assets" / "sprites" / "effects"
WORK_EFFECTS = PROJECT_ROOT / "work" / "art" / "effects"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
SKIP_SLOW = os.environ.get("SD_SKIP_SLOW_ART") == "1"
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
    import gen_effects
    HAVE_NUMPY = HAVE_PIL
except ImportError:
    HAVE_NUMPY = False

ROTATED = ("A1", "A2A8", "A3A7", "A4A6", "A5")
# sprite -> (lump suffixes, grAb, canvas) as gen_effects drew option A
NEW = {
    "SDPG": (ROTATED, (36, 16), (72, 24)),
    "SDKR": (ROTATED, (36, 16), (72, 24)),
    "SDPX": (("A0", "B0", "C0"), (46, 55), (92, 84)),
    "SDFJ": (("A0", "B0"), (15, 18), (30, 28)),
    "SDFX": (tuple(f"{f}0" for f in "ABCDE"), (22, 30), (44, 42)),
}
# The engine actors' overrides: Freedoom 0.13.0's own lump set per name
# (read in iwads/freedoom2.wad on 2026-10-20; IwadTests re-reads it).
OVERRIDES = {
    "PUFF": "ABCD", "BLUD": "ABC", "TFOG": "ABCDEFGHIJ", "IFOG": "ABCDE",
    "BAR1": "AB", "BEXP": "ABCDE", "COLU": "A",
}
RETIRED = {"MISL", "PLSS", "PLSE"}
LUMP_COUNT = 50

# The States blocks at HEAD c68ad84 (2026-10-20), before D82, with the
# placeholder names; AFTER maps (old sprite, old letter) to ours.
BEFORE = {
    "pg7_grenade.zs": [
        ("Spawn", ":", "", 0, ""), ("Spawn", "MISL", "A", 1, "Bright"), ("Spawn", "->", "Loop", 0, ""),
        ("Death", ":", "", 0, ""),
        ("Death", "MISL", "B", 8, "Bright A_Explode(SD_PG7_BLAST_DAMAGE, SD_PG7_BLAST_RADIUS)"),
        ("Death", "MISL", "C", 6, "Bright"), ("Death", "MISL", "D", 4, "Bright"), ("Death", "->", "Stop", 0, "")],
    "katyusha_rocket.zs": [
        ("Spawn", ":", "", 0, ""), ("Spawn", "MISL", "A", 1, "Bright"), ("Spawn", "->", "Loop", 0, ""),
        ("Death", ":", "", 0, ""),
        ("Death", "MISL", "B", 6, "Bright A_Explode(SD_KAT_BLAST_DAMAGE, SD_KAT_BLAST_RADIUS, SD_KAT_NO_SELF_HARM)"),
        ("Death", "MISL", "C", 5, "Bright"), ("Death", "MISL", "D", 4, "Bright"), ("Death", "->", "Stop", 0, "")],
    "flame_blob.zs": [
        ("Spawn", ":", "", 0, ""), ("Spawn", "PLSS", "ABABABABABAB", 2, "Bright"),
        ("Spawn", "->", "Goto Death", 0, ""),
        ("Death", ":", "", 0, ""), ("Death", "PLSE", "ABCDE", 3, "Bright"), ("Death", "->", "Stop", 0, "")],
}
AFTER = {
    "pg7_grenade.zs": {("MISL", "A"): ("SDPG", "A"), ("MISL", "B"): ("SDPX", "A"),
                       ("MISL", "C"): ("SDPX", "B"), ("MISL", "D"): ("SDPX", "C")},
    "katyusha_rocket.zs": {("MISL", "A"): ("SDKR", "A"), ("MISL", "B"): ("SDPX", "A"),
                           ("MISL", "C"): ("SDPX", "B"), ("MISL", "D"): ("SDPX", "C")},
    "flame_blob.zs": {("PLSS", "A"): ("SDFJ", "A"), ("PLSS", "B"): ("SDFJ", "B"),
                      **{("PLSE", c): ("SDFX", c) for c in "ABCDE"}},
}
CONSTANTS = {
    "pg7_grenade.zs": {"SD_PG7_IMPACT_DAMAGE": 30, "SD_PG7_BLAST_DAMAGE": 100,
                       "SD_PG7_BLAST_RADIUS": 104, "SD_PG7_SPEED": 28},
    "katyusha_rocket.zs": {"SD_KAT_IMPACT_DAMAGE": 25, "SD_KAT_BLAST_DAMAGE": 70, "SD_KAT_BLAST_RADIUS": 96,
                           "SD_KAT_SPEED": 32, "SD_KAT_NO_SELF_HARM": 0},
    # D119: the ROKS-3 jet 4 -> 3 x random(1,8) (BALANCE slot 6).
    "flame_blob.zs": {"SD_FLAME_DAMAGE": 3, "SD_FLAME_SPEED": 22, "SD_FLAME_LIFE_TICS": 2},
}


def expected_names() -> set[str]:
    out = {f"{sp}{s}" for sp, (suffixes, _, _) in NEW.items() for s in suffixes}
    return out | {f"{sp}{f}0" for sp, frames in OVERRIDES.items() for f in frames}


def lumps() -> list[Path]:
    return sorted(EFFECTS.glob("*.png")) if EFFECTS.is_dir() else []


def converted(name: str) -> list[tuple]:
    """BEFORE with each frame line's sprite and letters mapped to ours."""
    out = []
    for label, sprite, frames, tics, rest in BEFORE[name]:
        if sprite in (":", "->"):
            out.append((label, sprite, frames, tics, rest))
            continue
        mapped = [AFTER[name][(sprite, f)] for f in frames]
        assert len({m[0] for m in mapped}) == 1
        out.append((label, mapped[0][0], "".join(m[1] for m in mapped), tics, rest))
    return out


def iwad_sprite_lumps() -> set[str]:
    data = IWAD.read_bytes()
    _, n, off = struct.unpack("<4sii", data[:12])
    names, inside = set(), False
    for i in range(n):
        nm = data[off + 16 * i + 8:off + 16 * i + 16].rstrip(b"\0").decode("ascii", "replace")
        if nm in ("S_START", "SS_START"):
            inside = True
        elif nm in ("S_END", "SS_END"):
            inside = False
        elif inside:
            names.add(nm)
    return names


class BehaviourTests(unittest.TestCase):
    def test_states_are_the_pre_d82_ones_but_for_the_names(self):
        for name in BEFORE:
            with self.subTest(file=name):
                self.assertEqual(states(WEAPONS_ZS / name), converted(name))

    def test_constants_and_flame_style_untouched(self):
        for name, want in CONSTANTS.items():
            text = (WEAPONS_ZS / name).read_text(encoding="utf-8")
            got = {k: int(v) for k, v in re.findall(r"const\s+(SD_\w+)\s*=\s*(\d+)\s*;", text)}
            self.assertEqual(got, want, name)
        flame = (WEAPONS_ZS / "flame_blob.zs").read_text(encoding="utf-8")
        self.assertIn('RenderStyle "Add";', flame)
        self.assertIn("Alpha 0.85;", flame)
        self.assertIn("+ZDOOMTRANS", flame)

    def test_the_burst_is_shared(self):
        used = {name: {sp for _, sp, *_ in frame_rows(states(WEAPONS_ZS / name))}
                for name in ("pg7_grenade.zs", "katyusha_rocket.zs")}
        self.assertEqual(used["pg7_grenade.zs"], {"SDPG", "SDPX"})
        self.assertEqual(used["katyusha_rocket.zs"], {"SDKR", "SDPX"})


class RetiredTests(unittest.TestCase):
    def test_no_state_anywhere_names_misl_plss_plse(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & RETIRED, path.name)

    def test_no_other_lump_of_ours_names_them(self):
        for path in sorted((SRC_DIR / "lumps").rglob("*")):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                for old in RETIRED:
                    self.assertNotRegex(text, rf"\b{old}\b", f"{path.name} names {old}")

    def test_the_projectile_files_do_not_mention_them(self):
        for name in BEFORE:
            text = (WEAPONS_ZS / name).read_text(encoding="utf-8")
            for old in RETIRED:
                self.assertNotIn(old, text, f"{name}: not even in a comment")

    def test_mod_spec_declares_no_iwad_sprite(self):
        self.assertEqual(check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC), set())

    def test_no_state_of_ours_names_an_override(self):
        for path in sorted((SRC_DIR / "zscript").rglob("*.zs")):
            names = {n for n, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
            self.assertFalse(names & set(OVERRIDES), path.name)


class FileTests(unittest.TestCase):
    def test_exactly_the_fifty_lumps(self):
        self.assertEqual({p.stem for p in lumps()}, expected_names())
        self.assertEqual(len(expected_names()), LUMP_COUNT)

    def test_every_frame_a_state_uses_is_shipped_and_every_sd_lump_used(self):
        used: set[str] = set()
        for name in BEFORE:
            for _, sp, frames, _, _ in frame_rows(states(WEAPONS_ZS / name)):
                used |= {(sp, f) for f in frames}
        shipped = {(p.stem[:4], p.stem[4]) for p in lumps() if p.stem[:4] in NEW}
        self.assertEqual(shipped, used)

    def test_rotations(self):
        for p in lumps():
            if p.stem[:4] in ("SDPG", "SDKR"):
                self.assertIn(p.stem[4:], ROTATED, p.name)
            else:
                self.assertEqual(len(p.stem), 6, p.name)
                self.assertEqual(p.stem[5], "0", p.name)

    def test_grab_and_canvas_of_the_sd_sprites(self):
        for p in lumps():
            data = p.read_bytes()
            self.assertTrue(data.startswith(PNG_SIGNATURE), p)
            self.assertIsNotNone(read_grab(data), f"{p.name}: grAb before IDAT")
            if p.stem[:4] in NEW:
                _, grab, canvas = NEW[p.stem[:4]]
                self.assertEqual(struct.unpack(">II", data[16:24]), canvas, p.name)
                self.assertEqual(read_grab(data), grab, p.name)

    @unittest.skipUnless((WORK_EFFECTS / "manifest.json").is_file(), "work/ not present (CI has no work/)")
    def test_grab_and_size_are_the_manifests(self):
        manifest = json.loads((WORK_EFFECTS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["lumps"], LUMP_COUNT)
        for sprite, entry in manifest["sprites"].items():
            self.assertEqual(entry["option"], "A", f"{sprite}: D82 took option A")
            for name, info in entry["lumps"].items():
                data = (EFFECTS / f"{name}.png").read_bytes()
                self.assertEqual(list(struct.unpack(">II", data[16:24])), info["size"], name)
                self.assertEqual(list(read_grab(data)), info["grab"], name)

    @unittest.skipUnless(WORK_EFFECTS.is_dir(), "work/ not present (CI has no work/)")
    def test_byte_identical_to_the_approved_render(self):
        for p in lumps():
            source = WORK_EFFECTS / p.stem[:4] / p.name
            self.assertTrue(source.is_file(), source)
            self.assertEqual(p.read_bytes(), source.read_bytes(), p.name)

    @unittest.skipUnless(HAVE_PIL, "Pillow not available in this interpreter")
    def test_rgba_hard_alpha_palette_v1(self):
        v1 = set(palette_mod.colours(1))
        for p in lumps():
            with Image.open(p) as img:
                self.assertEqual(img.mode, "RGBA", p.name)
                raw = img.tobytes()
            self.assertLessEqual(set(raw[3::4]), {0, 255}, p.name)
            used = {tuple(raw[i:i + 3]) for i in range(0, len(raw), 4) if raw[i + 3]}
            self.assertTrue(used, p.name)
            self.assertFalse(used - v1, p.name)

    @unittest.skipUnless(HAVE_NUMPY, "numpy/Pillow not available in this interpreter")
    @unittest.skipIf(SKIP_SLOW, "SD_SKIP_SLOW_ART=1: renders the whole set")
    def test_a_fresh_render_of_option_a_gives_the_same_pixels(self):
        for e in gen_effects.EFFECTS:
            self.assertEqual(gen_effects.recommended(e.key), "A", e.key)
            for name, (rgba, grab) in gen_effects.render_set(e.key, "A").items():
                with Image.open(EFFECTS / f"{name}.png") as img:
                    installed = np.asarray(img.convert("RGBA"))
                np.testing.assert_array_equal(installed, rgba, err_msg=name)
                self.assertEqual(read_grab((EFFECTS / f"{name}.png").read_bytes()), tuple(grab), name)


class IwadTests(unittest.TestCase):
    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not in git")
    def test_overrides_are_exactly_freedooms_lump_set(self):
        iwad = iwad_sprite_lumps()
        for sprite, frames in OVERRIDES.items():
            theirs = {n for n in iwad if n.startswith(sprite)}
            ours = {p.stem for p in lumps() if p.stem.startswith(sprite)}
            self.assertEqual(ours, theirs, sprite)
            self.assertEqual(ours, {f"{sprite}{f}0" for f in frames}, sprite)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not in git")
    def test_new_prefixes_are_not_iwad_sprites(self):
        prefixes = {n[:4] for n in iwad_sprite_lumps()}
        self.assertFalse(set(NEW) & prefixes)
        self.assertLessEqual(RETIRED, prefixes, "the retired names were Freedoom's")


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
            for p in lumps():
                self.assertIn(f"sprites/{p.name}", names)
                self.assertEqual(zf.read(f"sprites/{p.name}"), p.read_bytes())

    def test_check_pk3_passes_sprites_and_licences(self):
        report = check_pk3.check_pk3(self.pk3)
        errors = [f for f in report.errors if f.category in ("sprites", "licences")]
        self.assertEqual([], errors)


class LicenceTests(unittest.TestCase):
    def test_every_lump_has_one_own_work_row(self):
        rows = licences.parse_licence_register(licences.LICENSES_PATH.read_text(encoding="utf-8"))
        for p in lumps():
            found = [r for r in rows if r.covers(f"sprites/{p.name}")]
            self.assertEqual(len(found), 1, f"{p.stem}: {len(found)} rows in docs/art/LICENSES.md")
            self.assertTrue(found[0].own_work, p.stem)
            self.assertEqual(found[0].required, licences.OWN_WORK_CREDITS, p.stem)
            self.assertIn("tools/art/gen_effects.py", found[0].origin, p.stem)
            self.assertIn("option A", found[0].origin, p.stem)


if __name__ == "__main__":
    unittest.main()
