"""D104 (P4): the Episode 2 enemies DRAFT overlay, static checks.

`tools/make_ep2_enemy_overlay.py` packs `work/overlays/ep2-enemies/` (the
heavy machine-gunner SD_LegionGunner and the boss SD_LibertyColossus, with
the colossus's rocket and flame) into `work/overlays/sd-ep2-enemies.pk3`,
loaded after the mod with `-file`. Design:
docs/engine/2026-10-22_P4_ep2-enemies.md. What is checked, and why:

  tool       on a synthetic source (CI has no work/): it builds, holds
             exactly the source's files, two builds are byte-identical; it
             refuses an editor number the mod uses or one outside
             21100-21199, a class the mod declares, a path that would
             shadow a mod file, a .zs no #include names, an #include of a
             missing file, a stray file, and an --out under src/, dist/ or
             assets/
  mod        nothing under src/ names the two new classes yet: the overlay
             does not touch the mod (flips when the CEO approves the art)
  real       (skips without work/overlays/ep2-enemies/) the overlay builds;
             its classes exist and derive from classes the mod has; its
             editor numbers are free in the mod's MAPINFO and outside the
             numbers MOD-SPEC 6.1 / BESTIARY 2.5 reserve; every frame a
             state shows (the parent's inherited Spawn included) has its
             lumps in assets/sprites/ (all of rotations 1-8, or 0); every
             sound is a name the mod's SNDINFO defines; every $SD_ id is
             in its LANGUAGE in all three languages and none overrides a
             mod id; the brief's numbers hold (gunner 80 HP, burst 4-6,
             pain under the trooper's, drops the PPSh-41; colossus the
             General's health x 1.5 and his boss flags, A_BossDeath)
  doc        the design document names both classes and both numbers

Stdlib only.
"""

from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import make_ep2_enemy_overlay as ov  # noqa: E402

SRC = PROJECT_ROOT / "src"
SPRITES = PROJECT_ROOT / "assets" / "sprites"
REAL_SRC = ov.SRC_DIR
DOC = PROJECT_ROOT / "docs" / "engine" / "2026-10-22_P4_ep2-enemies.md"
NEW_CLASSES = ("SD_LegionGunner", "SD_LibertyColossus")
EXPECTED_CLASSES = {"SD_LegionGunner", "SD_LibertyColossus", "SD_ColossusRocket", "SD_ColossusFlame"}
EXPECTED_EDNUMS = {21110: "SD_LegionGunner", 21111: "SD_LibertyColossus"}
# MOD-SPEC 6.1: 21108 reserved (cloaked hound); BESTIARY 2.5 keeps
# 21100-21109 for the first seven classes and two variants.
RESERVED_EDNUMS = set(range(21100, 21110))
LANGS = ("enu default", "ru", "ca")


# ------------------------------------------------------------------ helpers
def run_tool(argv: list[str]) -> int:
    """The tool's main(), its manifest and refusals kept off the test log."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return ov.main(argv)


def write_fixture(root: Path, *, ednum: int = 21150, cls: str = "SD_FixtureEnemy",
                  extra_zs: str | None = None, include_missing: bool = False) -> Path:
    """A minimal overlay source: one class, one number, one string."""
    zsdir = root / "zscript" / "sd_ep2"
    zsdir.mkdir(parents=True)
    (zsdir / "fixture.zs").write_text(
        f"class {cls} : SD_Monster\n{{\n\tStates\n\t{{\n\tSpawn:\n\t\tSDLT A -1;\n\t\tStop;\n\t}}\n}}\n",
        encoding="utf-8")
    includes = ['#include "zscript/sd_ep2/fixture.zs"']
    if include_missing:
        includes.append('#include "zscript/sd_ep2/missing.zs"')
    if extra_zs:
        (zsdir / extra_zs).write_text("// orphan\n", encoding="utf-8")
    (root / "zscript.txt").write_text('version "4.12"\n' + "\n".join(includes) + "\n", encoding="utf-8")
    (root / "MAPINFO").write_text(f"DoomEdNums\n{{\n\t{ednum} = {cls}\n}}\n", encoding="utf-8")
    (root / "LANGUAGE").write_text('[enu default]\nSD_TAG_FIXTURE = "x";\n', encoding="utf-8")
    return root


def strip(text: str) -> str:
    return ov.strip_comments(text)


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


def sndinfo_names(text: str) -> set[str]:
    names: set[str] = set()
    for line in strip(text).splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^\$random\s+(\S+)", line)
        if m:
            names.add(m.group(1).lower())
        elif not line.startswith(("$", "{", "}")):
            names.add(line.split()[0].lower())
    return names


def class_blocks(text: str) -> dict[str, tuple[str | None, str]]:
    """class name -> (parent, body text up to the next class)."""
    text = strip(text)
    heads = list(re.finditer(r"^\s*class\s+(\w+)\s*(?::\s*(\w+))?", text, flags=re.M))
    out = {}
    for i, h in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[h.group(1)] = (h.group(2), text[h.start():end])
    return out


def states_block(body: str) -> str:
    m = re.search(r"\bStates\s*\{(.*?)\n\t\}", body, flags=re.S)
    return m.group(1) if m else ""


def state_frames(body: str) -> set[tuple[str, str]]:
    """(sprite, frame) for every state line of a class's States block."""
    frames: set[tuple[str, str]] = set()
    for line in states_block(body).splitlines():
        m = re.match(r"^\s*([A-Z0-9_]{4})\s+([A-Z\[\]]+)\s+-?\d+\b", line)
        if m and m.group(1) != "TNT1":
            frames.update((m.group(1), f) for f in m.group(2))
    return frames


def sprite_rotations(sprite: str) -> dict[str, set[str]]:
    """frame -> rotations available under assets/sprites/ (mirrored pairs counted)."""
    rot: dict[str, set[str]] = {}
    for p in SPRITES.rglob(f"{sprite}*.png"):
        stem = p.stem
        for i in (4, 6):
            if len(stem) >= i + 2:
                rot.setdefault(stem[i], set()).add(stem[i + 1])
    return rot


def const_value(body: str, name: str) -> float:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([0-9.]+)\s*;", body)
    if not m:
        raise AssertionError(f"no const {name}")
    return float(m.group(1))


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

    def build(self, src: Path, out: Path, mod_src: Path = SRC) -> int:
        return run_tool(["--src", str(src), "--out", str(out), "--mod-src", str(mod_src)])

    def refused(self, src: Path, mod_src: Path = SRC) -> None:
        with self.assertRaises(ov.OverlayError):
            ov.plan_overlay(src, mod_src)

    def test_builds_and_is_reproducible(self):
        src = write_fixture(self.root / "src")
        a, b = self.root / "a.pk3", self.root / "b.pk3"
        self.assertEqual(self.build(src, a), 0)
        self.assertEqual(self.build(src, b), 0)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        names = zipfile.ZipFile(a).namelist()
        self.assertEqual(sorted(names), ["LANGUAGE", "MAPINFO", "zscript.txt", "zscript/sd_ep2/fixture.zs"])
        self.assertTrue(a.with_suffix(".txt").is_file())

    def test_refuses_a_number_the_mod_uses(self):
        self.refused(write_fixture(self.root / "s", ednum=21106))   # SD_General

    def test_refuses_a_number_outside_the_enemy_range(self):
        self.refused(write_fixture(self.root / "s", ednum=21250))

    def test_refuses_a_class_the_mod_declares(self):
        self.refused(write_fixture(self.root / "s", cls="SD_General"))

    def test_refuses_an_orphan_zs(self):
        self.refused(write_fixture(self.root / "s", extra_zs="orphan.zs"))

    def test_refuses_a_missing_include(self):
        self.refused(write_fixture(self.root / "s", include_missing=True))

    def test_refuses_a_stray_file(self):
        src = write_fixture(self.root / "s")
        (src / "sprites").mkdir()
        (src / "sprites" / "SDLGA1.png").write_bytes(b"x")
        self.refused(src)

    def test_refuses_to_shadow_a_mod_file(self):
        src = write_fixture(self.root / "s")
        mod = self.root / "mod"
        (mod / "zscript" / "sd_ep2").mkdir(parents=True)
        (mod / "zscript" / "sd_ep2" / "fixture.zs").write_text("class SD_Other : Actor {}\n", encoding="utf-8")
        (mod / "lumps").mkdir()
        (mod / "lumps" / "MAPINFO").write_text("DoomEdNums\n{\n}\n", encoding="utf-8")
        self.refused(src, mod)

    def test_refuses_to_write_into_the_mod(self):
        src = write_fixture(self.root / "s")
        for name in ov.FORBIDDEN_OUT:
            with self.subTest(name=name):
                self.assertEqual(self.build(src, PROJECT_ROOT / name / "x.pk3"), 1)
                self.assertFalse((PROJECT_ROOT / name / "x.pk3").exists())


class ModUntouchedTests(unittest.TestCase):
    def test_src_does_not_name_the_new_classes(self):
        for p in SRC.rglob("*"):
            if p.is_file() and p.suffix in ("", ".zs", ".txt", ".py"):
                text = p.read_text(encoding="utf-8", errors="replace")
                for cls in NEW_CLASSES:
                    self.assertNotIn(cls, text, f"{p} names {cls}: the draft entered the mod")


# -------------------------------------------------------------------- real
@unittest.skipUnless(REAL_SRC.is_dir(), "no work/overlays/ep2-enemies/ (gitignored work/)")
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
        cls.mod_classes = mod_class_files()

    def test_builds(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "sd-ep2-enemies.pk3"
            self.assertEqual(run_tool(["--src", str(REAL_SRC), "--out", str(out)]), 0)
            self.assertEqual(sorted(zipfile.ZipFile(out).namelist()), sorted(self.plan.files))

    def test_classes(self):
        self.assertEqual(set(self.plan.classes), EXPECTED_CLASSES)
        for cls, (parent, _) in self.blocks.items():
            with self.subTest(cls=cls):
                self.assertIn(parent, self.mod_classes, f"{cls} derives from {parent}, not a mod class")

    def test_editor_numbers(self):
        self.assertEqual(self.plan.ednums, EXPECTED_EDNUMS)
        mod = ov.mapinfo_ednums((SRC / "lumps" / "MAPINFO").read_text(encoding="utf-8"))
        for num in self.plan.ednums:
            self.assertNotIn(num, mod)
            self.assertNotIn(num, RESERVED_EDNUMS)
            self.assertIn(num, ov.ENEMY_EDNUMS)

    def test_every_frame_has_its_sprites(self):
        for cls, (parent, body) in self.blocks.items():
            frames = state_frames(body)
            labels = set(re.findall(r"^\s*(\w+):", states_block(body), flags=re.M))
            if "Spawn" not in labels and parent in self.mod_classes:
                # the inherited Spawn (the projectiles' flight)
                pbody = class_blocks(self.mod_classes[parent].read_text(encoding="utf-8"))[parent][1]
                frames |= state_frames(pbody)
            self.assertTrue(frames, cls)
            for sprite, frame in sorted(frames):
                with self.subTest(cls=cls, sprite=sprite, frame=frame):
                    rots = sprite_rotations(sprite).get(frame, set())
                    self.assertTrue("0" in rots or set("12345678") <= rots,
                                    f"{sprite}{frame}: rotations {sorted(rots)}")

    def test_sounds_are_defined(self):
        defined = sndinfo_names((SRC / "lumps" / "SNDINFO").read_text(encoding="utf-8"))
        used = set(re.findall(r'"(sd/[^"]+)"', self.zs_text))
        self.assertTrue(used)
        for name in sorted(used):
            self.assertIn(name.lower(), defined, name)

    def test_strings_in_three_languages(self):
        overlay = language_sections(self.plan.files["LANGUAGE"].read_text(encoding="utf-8"))
        mod = language_sections((SRC / "lumps" / "LANGUAGE").read_text(encoding="utf-8"))
        used = set(re.findall(r'"\$(SD_\w+)"', self.zs_text))
        self.assertTrue(used)
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(set(overlay.get(lang, {})), used)
                self.assertFalse(used & set(mod.get(lang, {})), "an overlay id overrides a mod id")

    def test_gunner_numbers(self):
        body = self.blocks["SD_LegionGunner"][1]
        trooper = class_blocks((SRC / "zscript" / "monsters" / "legion_trooper.zs").read_text(encoding="utf-8"))
        tbody = trooper["SD_LegionTrooper"][1]
        self.assertEqual(const_value(body, "SD_GUNNER_HEALTH"), 80)
        self.assertEqual((const_value(body, "SD_GUNNER_BURST_MIN"), const_value(body, "SD_GUNNER_BURST_MAX")), (4, 6))
        self.assertLess(const_value(body, "SD_GUNNER_PAINCHANCE"), const_value(tbody, "SD_TROOPER_PAINCHANCE"))
        self.assertIn('DropItem "SD_Ppsh"', body)
        self.assertIn("SD_FACTION_LEGION", body)

    def test_colossus_is_a_boss(self):
        body = self.blocks["SD_LibertyColossus"][1]
        general = class_blocks((SRC / "zscript" / "monsters" / "general.zs").read_text(encoding="utf-8"))
        gbody = general["SD_General"][1]
        self.assertEqual(const_value(body, "SD_COLOSSUS_HEALTH"), const_value(gbody, "SD_GENERAL_HEALTH") * 1.5)
        for flag in ("+BOSS", "+NORADIUSDMG", "+DONTMORPH", "+BOSSDEATH"):
            self.assertIn(flag, gbody)
            self.assertIn(flag, body)
        self.assertIn("A_BossDeath", body)
        self.assertIn("A_NoBlocking", body)
        for label in ("Rockets:", "Flame:", "Stomp:", "Death:"):
            self.assertIn(label, body)
        self.assertEqual(body.count("A_SD_ColossusRocket;"), 3)   # the three-rocket salvo


class DocTests(unittest.TestCase):
    def test_doc_names_both(self):
        text = DOC.read_text(encoding="utf-8")
        for needle in (*NEW_CLASSES, "21110", "21111", "make_ep2_enemy_overlay.py"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
