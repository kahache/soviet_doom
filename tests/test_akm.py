"""D112 (P4): the AKM DRAFT overlay, static checks.

`tools/make_akm_overlay.py` packs `work/overlays/akm/` (SD_Akm, slot 4's
second weapon, and SD_AkmAmmo, its 7.62x39 pool and magazine, with their
provisional sprites, strings and sound names) into
`work/overlays/sd-draft-akm.pk3`, loaded after the mod with `-file`.
Design and balance: docs/engine/2026-10-22_P4_akm.md. What is checked:

  tool       on a synthetic source (CI has no work/): it builds, holds
             exactly the source's files, two builds are byte-identical; it
             refuses an editor number the mod uses or one outside
             21000-21039, a class the mod declares, a .zs no #include
             names, an #include of a missing file, a stray file, a sprite
             that is not the AKM's, one whose name the mod's assets use,
             one that is not a PNG, and an --out under src/, dist/ or
             assets/; the grAb writer round-trips; the tint keeps alpha
  mod        nothing under src/ names the two classes or uses their two
             editor numbers yet (flips when the CEO approves the weapon)
  real       (skips without work/overlays/akm/) the overlay builds; its
             classes and numbers; every frame a state shows has its PNG,
             rotation 0, with grAb offsets; every sound it plays is in its
             SNDINFO and every lump there is one the mod ships; every
             $SD_ id in three languages, English ASCII, none a mod id;
             the brief's numbers against the PPSh-41 (slower, harder per
             round, tighter, between the PPSh and the RPG-7 in DPS, own
             pool that is not Clip, slot 4)
  doc        the design document names both classes, both numbers, the
             tool and the Gemini block

Stdlib only.
"""

from __future__ import annotations

import contextlib
import io
import re
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import make_akm_overlay as ov  # noqa: E402

SRC = PROJECT_ROOT / "src"
SOUNDS = PROJECT_ROOT / "assets" / "sounds"
REAL_SRC = ov.SRC_DIR
DOC = PROJECT_ROOT / "docs" / "engine" / "2026-10-22_P4_akm.md"
NEW_CLASSES = ("SD_Akm", "SD_AkmAmmo")
EXPECTED_EDNUMS = {21008: "SD_Akm", 21020: "SD_AkmAmmo"}
ENGINE_PARENTS = {"DoomWeapon", "Ammo"}
LANGS = ("enu default", "ru", "ca")
TICS_PER_SECOND = 35
RPG7_DPS = 181.7   # BALANCE.md section 2, slot 5: the AKM must stay under it


# ------------------------------------------------------------------ helpers
def run_tool(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return ov.main(argv)


def tiny_png(grab: tuple[int, int] | None = None) -> bytes:
    """A 1x1 RGBA PNG built with zlib, optionally with grAb."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
    data = ov.PNG_SIGNATURE + ihdr + idat + chunk(b"IEND", b"")
    return ov.with_grab(data, *grab) if grab else data


def write_fixture(root: Path, *, ednum: int = 21015, cls: str = "SD_FixtureGun",
                  extra_zs: str | None = None, include_missing: bool = False,
                  sprite: str = "SDAKA0.png", sprite_bytes: bytes | None = None) -> Path:
    zsdir = root / "zscript" / "sd_akm"
    zsdir.mkdir(parents=True)
    (zsdir / "fixture.zs").write_text(
        f"class {cls} : DoomWeapon\n{{\n\tStates\n\t{{\n\tSpawn:\n\t\tSDAK A -1;\n\t\tStop;\n\t}}\n}}\n",
        encoding="utf-8")
    includes = ['#include "zscript/sd_akm/fixture.zs"']
    if include_missing:
        includes.append('#include "zscript/sd_akm/missing.zs"')
    if extra_zs:
        (zsdir / extra_zs).write_text("// orphan\n", encoding="utf-8")
    (root / "zscript.txt").write_text('version "4.12"\n' + "\n".join(includes) + "\n", encoding="utf-8")
    (root / "MAPINFO").write_text(f"DoomEdNums\n{{\n\t{ednum} = {cls}\n}}\n", encoding="utf-8")
    (root / "LANGUAGE").write_text('[enu default]\nSD_TAG_FIXTURE = "x";\n', encoding="utf-8")
    (root / "SNDINFO").write_text("sd/weapon/fixture/fire SDPPFIR\n", encoding="utf-8")
    (root / "sprites").mkdir()
    (root / "sprites" / sprite).write_bytes(tiny_png((0, 0)) if sprite_bytes is None else sprite_bytes)
    return root


def strip(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def language_sections(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    current = None
    for line in strip(text).splitlines():
        head = re.match(r"^\s*\[([^\]]+)\]", line)
        if head:
            current = head.group(1).strip()
            out.setdefault(current, {})
            continue
        m = re.match(r'^\s*(\w+)\s*=\s*"(.*)"\s*;', line)
        if m and current is not None:
            out[current][m.group(1)] = m.group(2)
    return out


def sndinfo_map(text: str) -> dict[str, str]:
    """logical name -> lump, for plain `name LUMP` lines."""
    out = {}
    for line in strip(text).splitlines():
        parts = line.split()
        if len(parts) >= 2 and not parts[0].startswith(("$", "{", "}")):
            out[parts[0].lower()] = parts[1]
    return out


def class_blocks(text: str) -> dict[str, tuple[str | None, str]]:
    text = strip(text)
    heads = list(re.finditer(r"^\s*class\s+(\w+)\s*(?::\s*(\w+))?", text, flags=re.M))
    out = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[h.group(1)] = (h.group(2), text[h.start():end])
    return out


def state_frames(body: str) -> set[tuple[str, str]]:
    frames: set[tuple[str, str]] = set()
    m = re.search(r"\bStates\s*\{(.*?)\n\t\}", body, flags=re.S)
    for line in (m.group(1) if m else "").splitlines():
        s = re.match(r"^\s*([A-Z0-9_]{4})\s+([A-Z]+)\s+-?\d+\b", line)
        if s and s.group(1) != "TNT1":
            frames.update((s.group(1), f) for f in s.group(2))
    return frames


def label_block(body: str, label: str) -> list[str]:
    """The state lines under `label:` up to its Goto/Loop/Stop."""
    lines = body.splitlines()
    start = next(i for i, l in enumerate(lines) if re.match(rf"^\s*{label}:\s*$", l))
    out = []
    for line in lines[start + 1:]:
        if re.match(r"^\s*(Goto|Loop|Stop)\b", line):
            break
        out.append(line)
    return out


def tics_per_round(body: str, fire_call: str) -> float:
    lines = label_block(body, "Fire")
    tics = sum(int(m.group(1)) for l in lines if (m := re.match(r"^\s*\w{4}\s+[A-Z]+\s+(\d+)\b", l)))
    rounds = sum(1 for l in lines if fire_call in l)
    return tics / rounds


def const_value(body: str, name: str) -> float:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([0-9.]+)\s*;", body)
    if not m:
        raise AssertionError(f"no const {name}")
    return float(m.group(1))


def default_value(body: str, prop: str) -> str:
    m = re.search(rf"^\s*{re.escape(prop)}\s+([^;]+);", body, flags=re.M)
    if not m:
        raise AssertionError(f"no {prop}")
    return m.group(1).strip().strip('"')


def mod_class_files() -> dict[str, Path]:
    out = {}
    for p in (SRC / "zscript").rglob("*.zs"):
        for c in ov.zscript_classes(p.read_text(encoding="utf-8")):
            out[c] = p
    return out


# -------------------------------------------------------------------- tool
class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, src: Path, out: Path) -> int:
        return run_tool(["--src", str(src), "--out", str(out), "--mod-src", str(SRC)])

    def refused(self, src: Path, mod_src: Path = SRC, mod_sprites: Path = ov.MOD_SPRITES) -> None:
        with self.assertRaises(ov.OverlayError):
            ov.plan_overlay(src, mod_src, mod_sprites)

    def test_builds_and_is_reproducible(self):
        src = write_fixture(self.root / "src")
        a, b = self.root / "a.pk3", self.root / "b.pk3"
        self.assertEqual(self.build(src, a), 0)
        self.assertEqual(self.build(src, b), 0)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertEqual(sorted(zipfile.ZipFile(a).namelist()),
                         ["LANGUAGE", "MAPINFO", "SNDINFO", "sprites/SDAKA0.png",
                          "zscript.txt", "zscript/sd_akm/fixture.zs"])
        self.assertTrue(a.with_suffix(".txt").is_file())

    def test_refuses_a_number_the_mod_uses(self):
        self.refused(write_fixture(self.root / "s", ednum=21004))   # SD_Ppsh

    def test_refuses_a_number_outside_weapons_and_ammo(self):
        self.refused(write_fixture(self.root / "s", ednum=21110))

    def test_refuses_a_class_the_mod_declares(self):
        self.refused(write_fixture(self.root / "s", cls="SD_Ppsh"))

    def test_refuses_an_orphan_zs(self):
        self.refused(write_fixture(self.root / "s", extra_zs="orphan.zs"))

    def test_refuses_a_missing_include(self):
        self.refused(write_fixture(self.root / "s", include_missing=True))

    def test_refuses_a_stray_file(self):
        src = write_fixture(self.root / "s")
        (src / "TEXTURES").write_text("x", encoding="utf-8")
        self.refused(src)

    def test_refuses_a_sprite_that_is_not_the_akms(self):
        self.refused(write_fixture(self.root / "s", sprite="SDPPA0.png"))

    def test_refuses_a_rotated_or_misnamed_sprite(self):
        self.refused(write_fixture(self.root / "s", sprite="SDAKA1.png"))

    def test_refuses_a_sprite_name_the_mod_uses(self):
        src = write_fixture(self.root / "s")
        sprites = self.root / "modsprites" / "x"
        sprites.mkdir(parents=True)
        (sprites / "SDAKA0.png").write_bytes(tiny_png())
        self.refused(src, mod_sprites=self.root / "modsprites")

    def test_refuses_a_sprite_that_is_not_a_png(self):
        self.refused(write_fixture(self.root / "s", sprite_bytes=b"GIF89a"))

    def test_refuses_to_write_into_the_mod(self):
        src = write_fixture(self.root / "s")
        for name in ("src", "dist", "assets"):
            with self.subTest(name=name):
                self.assertEqual(self.build(src, PROJECT_ROOT / name / "x.pk3"), 1)
                self.assertFalse((PROJECT_ROOT / name / "x.pk3").exists())

    def test_grab_round_trip(self):
        data = tiny_png((-152, -96))
        self.assertEqual(ov.png_grab(data), (-152, -96))
        again = ov.with_grab(data, 3, 4)          # replaces, never duplicates
        self.assertEqual(ov.png_grab(again), (3, 4))
        self.assertEqual(again.count(b"grAb"), 1)
        self.assertIsNone(ov.png_grab(tiny_png()))

    def test_tint_keeps_alpha_and_order(self):
        px = [(0, 0, 0, 0), (100, 100, 100, 255), (200, 200, 200, 128)]
        out = ov.tint_rgba(px)
        self.assertEqual([p[3] for p in out], [0, 255, 128])
        self.assertLess(sum(out[1][:3]), sum(out[2][:3]))
        self.assertGreater(out[1][0], out[1][2])   # warm: more red than blue


class ModUntouchedTests(unittest.TestCase):
    def test_src_does_not_name_the_new_classes(self):
        for p in SRC.rglob("*"):
            if p.is_file() and p.suffix in ("", ".zs", ".txt", ".py"):
                text = p.read_text(encoding="utf-8", errors="replace")
                for cls in NEW_CLASSES:
                    self.assertIsNone(re.search(rf"\b{cls}\b", text), f"{p} names {cls}: the draft entered the mod")

    def test_numbers_still_free_in_the_mod(self):
        mod = ov.mapinfo_ednums((SRC / "lumps" / "MAPINFO").read_text(encoding="utf-8"))
        for num in EXPECTED_EDNUMS:
            self.assertNotIn(num, mod)


# -------------------------------------------------------------------- real
@unittest.skipUnless(REAL_SRC.is_dir(), "no work/overlays/akm/ (gitignored work/)")
class RealOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = ov.plan_overlay(REAL_SRC, SRC)
        cls.blocks: dict[str, tuple[str | None, str]] = {}
        for rel, path in cls.plan.files.items():
            if rel.endswith(".zs"):
                cls.blocks.update(class_blocks(path.read_text(encoding="utf-8")))
        cls.zs_text = "\n".join(strip(p.read_text(encoding="utf-8"))
                                for r, p in cls.plan.files.items() if r.endswith(".zs"))
        cls.akm = cls.blocks["SD_Akm"][1]
        cls.ammo = cls.blocks["SD_AkmAmmo"][1]
        cls.ppsh = class_blocks((SRC / "zscript" / "weapons" / "ppsh.zs").read_text(encoding="utf-8"))["SD_Ppsh"][1]

    def test_builds(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "sd-draft-akm.pk3"
            self.assertEqual(run_tool(["--src", str(REAL_SRC), "--out", str(out)]), 0)
            self.assertEqual(sorted(zipfile.ZipFile(out).namelist()), sorted(self.plan.files))

    def test_classes(self):
        self.assertEqual(set(self.plan.classes), set(NEW_CLASSES))
        known = set(mod_class_files()) | ENGINE_PARENTS
        for cls, (parent, _) in self.blocks.items():
            with self.subTest(cls=cls):
                self.assertIn(parent, known)
                self.assertNotIn("replaces", self.blocks[cls][1].splitlines()[0], "the AKM replaces nothing")

    def test_editor_numbers(self):
        self.assertEqual(self.plan.ednums, EXPECTED_EDNUMS)
        self.assertIn(21008, range(21000, 21020))   # MOD-SPEC 6.1 weapons
        self.assertIn(21020, range(21020, 21040))   # ammo and items

    def test_every_frame_has_its_sprite(self):
        have = {Path(r).stem for r in self.plan.files if r.startswith("sprites/")}
        for cls, (_, body) in self.blocks.items():
            frames = state_frames(body)
            self.assertTrue(frames, cls)
            for sprite, frame in sorted(frames):
                with self.subTest(cls=cls, sprite=sprite, frame=frame):
                    self.assertIn(f"{sprite}{frame}0", have)
                    self.assertIsNotNone(ov.png_grab(self.plan.files[f"sprites/{sprite}{frame}0.png"].read_bytes()))
        self.assertIn('Inventory.Icon "SDAMA0"', self.ammo)
        self.assertIn("SDAMA0", have)

    def test_sounds(self):
        snd = sndinfo_map(self.plan.files["SNDINFO"].read_text(encoding="utf-8"))
        used = set(re.findall(r'"(sd/[^"]+)"', self.zs_text))
        self.assertTrue(used)
        for name in sorted(used):
            with self.subTest(name=name):
                self.assertIn(name.lower(), snd)
                self.assertTrue(name.startswith("sd/weapon/akm/"))
        mod = sndinfo_map((SRC / "lumps" / "SNDINFO").read_text(encoding="utf-8"))
        shipped = {p.stem.upper() for p in SOUNDS.rglob("*.ogg")}
        for name, lump in snd.items():
            with self.subTest(name=name):
                self.assertNotIn(name, mod, "an overlay name overrides a mod name")
                self.assertIn(lump.upper(), shipped)

    def test_strings_in_three_languages(self):
        overlay = language_sections(self.plan.files["LANGUAGE"].read_text(encoding="utf-8"))
        mod = language_sections((SRC / "lumps" / "LANGUAGE").read_text(encoding="utf-8"))
        used = set(re.findall(r'"\$(SD_\w+)"', self.zs_text))
        self.assertEqual(used, {"SD_TAG_AKM", "SD_PICKUP_AKM", "SD_OB_AKM", "SD_AMMO_AKM", "SD_GOT_AKMMAG"})
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(set(overlay.get(lang, {})), used)
                self.assertFalse(used & set(mod.get(lang, {})), "an overlay id overrides a mod id")
        for k, v in overlay["enu default"].items():
            self.assertTrue(v.isascii(), k)
        self.assertIn("АКМ", overlay["ru"]["SD_TAG_AKM"])

    def test_slot_four_beside_the_ppsh(self):
        self.assertEqual(default_value(self.akm, "Weapon.SlotNumber"), "4")
        self.assertEqual(default_value(self.ppsh, "Weapon.SlotNumber"), "4")
        self.assertLess(int(default_value(self.akm, "Weapon.SelectionOrder")),
                        int(default_value(self.ppsh, "Weapon.SelectionOrder")))

    def test_own_pool_not_clip(self):
        self.assertEqual(default_value(self.akm, "Weapon.AmmoType"), "SD_AkmAmmo")
        self.assertEqual(self.blocks["SD_AkmAmmo"][0], "Ammo")   # its own pool: GetParentAmmo() is itself
        self.assertEqual(const_value(self.akm, "SD_AKM_AMMO_GIVE"), const_value(self.ammo, "SD_AKM_MAG"))
        self.assertEqual(const_value(self.ammo, "SD_AKM_BACKPACK_MAX"), 2 * const_value(self.ammo, "SD_AKM_MAX"))

    def test_slower_harder_tighter_than_the_ppsh(self):
        akm_tics = tics_per_round(self.akm, "A_SD_FireAkm")
        ppsh_tics = tics_per_round(self.ppsh, "A_FireBullets")
        self.assertEqual((akm_tics, ppsh_tics), (4, 3))
        akm_dmg = 2 * const_value(self.akm, "SD_AKM_DAMAGE")     # x random(1,3): avg x2
        ppsh_dmg = 2 * const_value(self.ppsh, "SD_PPSH_DAMAGE")
        self.assertGreater(akm_dmg, ppsh_dmg)
        akm_dps = akm_dmg * TICS_PER_SECOND / akm_tics
        ppsh_dps = ppsh_dmg * TICS_PER_SECOND / ppsh_tics
        self.assertAlmostEqual(akm_dps, 105.0)
        self.assertTrue(ppsh_dps < akm_dps < RPG7_DPS, (ppsh_dps, akm_dps))
        ppsh_spread = const_value(self.ppsh, "SD_PPSH_SPREAD")
        self.assertLess(const_value(self.akm, "SD_AKM_SPREAD_SHORT"), const_value(self.akm, "SD_AKM_SPREAD_LONG"))
        self.assertLess(const_value(self.akm, "SD_AKM_SPREAD_LONG"), ppsh_spread)
        self.assertEqual(const_value(self.akm, "SD_AKM_BULLETS"), 1)   # round 1 pinpoint
        self.assertIn("player.refire", self.akm)
        self.assertIn("A_ReFire", "\n".join(label_block(self.akm, "Fire")))


class DocTests(unittest.TestCase):
    def test_doc_names_everything(self):
        text = DOC.read_text(encoding="utf-8")
        for needle in (*NEW_CLASSES, "21008", "21020", "make_akm_overlay.py", "sd-draft-akm.pk3",
                       "[WEAPON]", "gemini_akm_A.png", "give SD_Akm"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
