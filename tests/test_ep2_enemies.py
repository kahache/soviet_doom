"""D104 (P4), integrated by D116: the Legion gunner and the Liberty Colossus.

Until D116 (2026-10-22) the two Episode 2 enemies lived in a DRAFT overlay,
`work/overlays/ep2-enemies/`, packed by `tools/make_ep2_enemy_overlay.py`.
D116 moved them into the mod on provisional sprites (MOD-SPEC 6.12); the
overlay and its tool are SUPERSEDED, kept, not deleted. Design:
docs/engine/2026-10-22_P4_ep2-enemies.md. What is checked, and why:

  tool       (the superseded tool, still on a synthetic source; CI has no
             work/): it builds, holds exactly the source's files, two builds
             are byte-identical; it refuses an editor number the mod uses or
             one outside 21100-21199, a class the mod declares, a path that
             would shadow a mod file, a .zs no #include names, an #include
             of a missing file, a stray file, and an --out under src/,
             dist/ or assets/; and now the real overlay itself
  mod        the four classes in src/zscript/monsters/, one per file, each
             #included; the gunner replaces ChaingunGuy and the colossus
             SpiderMastermind; 21110 and 21111 in MAPINFO; every frame a
             state shows has its lumps in assets/sprites/; the provisional
             tint is on marked lines only and the header's documented swap
             leaves the final sprite and no tint; every sound is the class's
             own SNDINFO name over a lump the mod ships (or a DS placeholder)
             with its final lump named; five ids in three languages; the
             brief's numbers (gunner 80 HP, bursts of 4-6, pain under the
             trooper's, drops SD_AkmAmmo; colossus the General's health x 1.5
             and his boss flags); placed where the design says (the gunner
             in MAP04-MAP06, the colossus MAP06's boss)
  doc        the design document and the contracts name them

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

sys.path.insert(0, str(TESTS_DIR))
import _p4_mod as p4  # noqa: E402

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


class SupersededOverlayTests(unittest.TestCase):
    """D116: the classes are the mod's now, so the overlay tool refuses the
    real source (a class the mod declares, a number its MAPINFO assigns):
    the old overlay can no longer be built over the mod by mistake."""

    def test_tool_says_superseded(self):
        self.assertIn("SUPERSEDED", ov.__doc__)

    @unittest.skipUnless(REAL_SRC.is_dir(), "no work/overlays/ep2-enemies/ (gitignored work/)")
    def test_real_overlay_is_refused(self):
        with self.assertRaises(ov.OverlayError):
            ov.plan_overlay(REAL_SRC, SRC)


# --------------------------------------------------------------------- mod
FILES = {
    "SD_LegionGunner": "zscript/monsters/legion_gunner.zs",
    "SD_LibertyColossus": "zscript/monsters/liberty_colossus.zs",
    "SD_ColossusRocket": "zscript/monsters/colossus_rocket.zs",
    "SD_ColossusFlame": "zscript/monsters/colossus_flame.zs",
}
REPLACES = {"SD_LegionGunner": "ChaingunGuy", "SD_LibertyColossus": "SpiderMastermind"}
PROJECTILE_PARENTS = {"SD_ColossusRocket": "SD_Pg7Grenade", "SD_ColossusFlame": "SD_FlameBlob"}
# Provisional sprite -> final sprite (MOD-SPEC 6.12).
SWAPS = {"SD_LegionGunner": (("SDLT", "SDLG"),), "SD_LibertyColossus": (("SDGN", "SDLC"),)}
SOUND_KEYS = {"SD_LegionGunner": "legiongunner", "SD_LibertyColossus": "colossus"}
SOUND_COUNT = 13   # gunner 6, colossus 7 (BESTIARY 12)
IDS = {"SD_TAG_GUNNER", "SD_TAG_COLOSSUS", "SD_OB_GUNNER", "SD_OB_COLOSSUS", "SD_OBHIT_COLOSSUS"}


class ModTests(unittest.TestCase):
    """The gunner and the colossus as the mod ships them (D116)."""

    @classmethod
    def setUpClass(cls):
        cls.text = {c: p4.read(f) for c, f in FILES.items()}
        cls.blocks: dict[str, tuple[str | None, str]] = {}
        for p in (SRC / "zscript").rglob("*.zs"):
            cls.blocks.update(p4.class_blocks(p.read_text(encoding="utf-8")))
        cls.gunner = cls.blocks["SD_LegionGunner"][1]
        cls.colossus = cls.blocks["SD_LibertyColossus"][1]

    def test_one_class_per_file_and_included(self):
        inc = p4.includes()
        for cls, rel in FILES.items():
            with self.subTest(cls=cls):
                self.assertEqual(list(p4.class_blocks(self.text[cls])), [cls])
                self.assertIn(rel.lower(), inc)

    def test_parents_and_replacements(self):
        for cls, doom in REPLACES.items():
            self.assertEqual(p4.class_head(self.text[cls], cls), f"class {cls} : SD_Monster replaces {doom}")
        for cls, parent in PROJECTILE_PARENTS.items():
            self.assertEqual(p4.class_head(self.text[cls], cls), f"class {cls} : {parent}")

    def test_editor_numbers(self):
        ednums = p4.mapinfo_ednums()
        for num, cls in EXPECTED_EDNUMS.items():
            self.assertEqual(ednums.get(num), cls)
            self.assertNotIn(num, RESERVED_EDNUMS)
        for cls in PROJECTILE_PARENTS:
            self.assertNotIn(cls, ednums.values(), "a projectile is not placeable")

    def test_every_frame_has_its_sprites(self):
        for cls in FILES:
            frames = p4.frames_with_inheritance(cls, self.blocks)
            self.assertTrue(frames, cls)
            for sprite, frame in sorted(frames):
                with self.subTest(cls=cls, sprite=sprite, frame=frame):
                    rots = p4.sprite_rotations(sprite).get(frame, set())
                    self.assertTrue("0" in rots or set("12345678") <= rots,
                                    f"{sprite}{frame}: rotations {sorted(rots)}")

    def test_provisional_look_and_its_documented_swap(self):
        """MOD-SPEC 6.12: today an existing sprite, tinted; the header's sed
        renames it to the final name and deletes only the marked lines."""
        for cls, swaps in SWAPS.items():
            with self.subTest(cls=cls):
                text = self.text[cls]
                marked = p4.provisional_code_lines(text)
                self.assertTrue(any(l.startswith("Translation ") for l in marked), marked)
                for line in marked:
                    self.assertRegex(line, r"^(Translation |Scale |const SD_\w+_SCALE )", line)
                swapped, pairs = p4.apply_documented_swap(text)
                self.assertEqual(tuple(pairs), swaps)
                frames = p4.state_frames(p4.class_blocks(swapped)[cls][1])
                self.assertEqual({s for s, _ in frames}, {swaps[0][1]})
                self.assertEqual({f for _, f in frames}, {f for _, f in p4.state_frames(self.blocks[cls][1])})
                code = p4.strip_comments(swapped)
                self.assertNotIn("Translation", code)
                self.assertNotRegex(code, r"\bScale\b")
                self.assertFalse(p4.sprite_rotations(swaps[0][1]), f"{swaps[0][1]} is drawn: do the swap")

    def test_sounds_are_their_own_names_over_existing_lumps(self):
        lines = p4.sndinfo_lines()
        shipped = {p.stem.upper() for p in (PROJECT_ROOT / "assets" / "sounds").rglob("*.ogg")}
        for cls in FILES:
            used = set(re.findall(r'"(sd/[a-z0-9/_]+)"', p4.strip_comments(self.text[cls])))
            for name in sorted(used):
                with self.subTest(cls=cls, name=name):
                    self.assertIn(name, lines, f"{name} not in SNDINFO")
                    key = SOUND_KEYS.get(cls)
                    if key and name.startswith("sd/mon/"):
                        self.assertTrue(name.startswith(f"sd/mon/{key}/"), name)
        finals = []
        for name, (lump, comment) in lines.items():
            if name.startswith(tuple(f"sd/mon/{k}/" for k in SOUND_KEYS.values())):
                with self.subTest(name=name):
                    self.assertTrue(lump in shipped or lump.startswith("DS"), lump)
                    final = p4.FINAL_LUMP_RE.search(comment)
                    self.assertIsNotNone(final, f"{name}: no '-> final lump' in its comment")
                    self.assertNotIn(final.group(1), shipped, "the final lump is not recorded yet")
                    finals.append(final.group(1))
        self.assertEqual(len(finals), len(set(finals)))
        self.assertEqual(len(finals), SOUND_COUNT)

    def test_strings_in_three_languages(self):
        sections = p4.language_sections()
        used = set(re.findall(r'"\$(SD_\w+)"', "\n".join(self.blocks[c][1] for c in FILES)))
        self.assertEqual(used, IDS)
        for lang in LANGS:
            with self.subTest(lang=lang):
                self.assertLessEqual(IDS, set(sections[lang]))
                for sid in IDS:
                    if sid.startswith("SD_OB"):
                        self.assertIn("%o", sections[lang][sid])
        for sid in IDS:
            self.assertTrue(sections["enu default"][sid].isascii(), sid)

    def test_gunner_numbers(self):
        tbody = self.blocks["SD_LegionTrooper"][1]
        self.assertEqual(const_value(self.gunner, "SD_GUNNER_HEALTH"), 80)
        self.assertEqual((const_value(self.gunner, "SD_GUNNER_BURST_MIN"),
                          const_value(self.gunner, "SD_GUNNER_BURST_MAX")), (4, 6))
        self.assertLess(const_value(self.gunner, "SD_GUNNER_PAINCHANCE"), const_value(tbody, "SD_TROOPER_PAINCHANCE"))
        self.assertIn("SD_FACTION_LEGION", self.gunner)

    def test_gunner_drops_akm_magazines(self):
        """D116, the AKM doc section 3: the Legion's heavy infantry carries
        7.62x39; no amount, so a dropped magazine is half of one (15)."""
        self.assertEqual(re.findall(r'DropItem\s+"([^"]+)"', self.gunner), ["SD_AkmAmmo"])
        self.assertRegex(self.gunner, r'DropItem\s+"SD_AkmAmmo"\s*;')
        self.assertEqual(self.blocks["SD_AkmAmmo"][0], "Ammo")

    def test_colossus_is_a_boss(self):
        gbody = self.blocks["SD_General"][1]
        self.assertEqual(const_value(self.colossus, "SD_COLOSSUS_HEALTH"),
                         const_value(gbody, "SD_GENERAL_HEALTH") * 1.5)
        for flag in ("+BOSS", "+NORADIUSDMG", "+DONTMORPH", "+BOSSDEATH"):
            self.assertIn(flag, gbody)
            self.assertIn(flag, self.colossus)
        self.assertIn("A_BossDeath", self.colossus)
        self.assertIn("A_NoBlocking", self.colossus)
        for label in ("Rockets:", "Flame:", "Stomp:", "Death:"):
            self.assertIn(label, self.colossus)
        self.assertEqual(self.colossus.count("A_SD_ColossusRocket;"), 3)   # the three-rocket salvo
        for cls in PROJECTILE_PARENTS:
            self.assertIn(f'"{cls}"', self.colossus)
            self.assertIn('Obituary ""', self.blocks[cls][1])

    # D116, placed (level-designer, 2026-10-22): both only in the P4 maps
    # (episodes 2 and 3); the gunner must be in MAP04-MAP06 and the colossus
    # is MAP06's boss (episode 3's maps may reuse him, e.g. MAP08's bay).
    P4_MAPS = {"MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09"}
    PLACED_IN = {"SD_LegionGunner": P4_MAPS, "SD_LibertyColossus": P4_MAPS}
    MUST_PLACE = {"SD_LegionGunner": {"MAP04", "MAP05", "MAP06"}, "SD_LibertyColossus": {"MAP06"}}

    def test_placed_where_the_design_says(self):
        """Episode 1's maps and the range stay as v1.0 shipped them; each new
        class is named only by the maps that place it, by its class and its
        editor number together (the map's MONSTER_CLASSES)."""
        number = {cls: num for num, cls in EXPECTED_EDNUMS.items()}
        found = {cls: set() for cls in REPLACES}
        for p in (SRC / "maps").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            for cls in REPLACES:
                named = cls in text or re.search(rf"\b{number[cls]}\b", text)
                if named:
                    self.assertIn(p.parent.name, self.PLACED_IN[cls], f"{p} names {cls}")
                    self.assertIn(cls, text, p)
                    self.assertRegex(text, rf"\b{number[cls]}\b", p)
                    found[cls].add(p.parent.name)
        for cls, maps in self.MUST_PLACE.items():
            self.assertLessEqual(maps, found[cls], cls)


class DocTests(unittest.TestCase):
    def test_doc_names_both_and_says_integrated(self):
        text = DOC.read_text(encoding="utf-8")
        for needle in (*NEW_CLASSES, "21110", "21111", "make_ep2_enemy_overlay.py", "D116", "SDLG", "SDLC"):
            self.assertIn(needle, text)

    def test_contracts_name_them(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        bestiary = (PROJECT_ROOT / "docs" / "engine" / "BESTIARY.md").read_text(encoding="utf-8")
        balance = (PROJECT_ROOT / "docs" / "engine" / "BALANCE.md").read_text(encoding="utf-8")
        for num, cls in EXPECTED_EDNUMS.items():
            self.assertIsNotNone(re.search(rf"\|\s*{num}\s*\|\s*`{cls}`", spec), f"MOD-SPEC 6.1 lacks {num}")
            self.assertTrue(f"`{cls}`" in bestiary, f"BESTIARY lacks {cls}")
        for name in ("Legion gunner", "Liberty Colossus"):
            self.assertTrue(name in balance, f"BALANCE lacks {name}")


if __name__ == "__main__":
    unittest.main()
