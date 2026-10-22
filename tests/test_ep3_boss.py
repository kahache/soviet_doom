"""D112 (P4), integrated by D116: the Episode 3 final boss, the Consortium.

Until D116 (2026-10-22) the boss lived in a DRAFT overlay,
`work/overlays/ep3-boss/`, packed by `tools/make_ep3_boss_overlay.py`. D116
moved it into the mod on a provisional sprite (MOD-SPEC 6.12); the overlay
and its tool are SUPERSEDED, kept, not deleted. Design:
docs/engine/2026-10-22_P4_ep3-final-boss.md. What is checked, and why:

  tool       (the superseded tool, on a synthetic source; CI has no work/):
             it builds reproducibly and refuses an editor number the mod or
             a sibling overlay uses or one outside 21100-21199, a class the
             mod or a sibling declares, a shadowing path, an orphan .zs, a
             missing #include, a stray file, an --out under src/, dist/ or
             assets/; and now the real overlay itself
  mod        the boss, its three projectiles and the half-health test
             fixture SD_ConsortiumWounded in src/zscript/monsters/, one per
             file, each #included; the boss replaces nothing and is 21112;
             every frame has its sprites; the provisional tint is on marked
             lines only and the documented swap leaves SDCN and no tint; its
             eight sounds are its own SNDINFO names over shipped lumps (or a
             DS placeholder) with final lumps named; three ids in three
             languages; the brief (health twice the colossus's, the
             General's boss flags, two phases at half health, the arsenal's
             projectiles passing through monsters, servants from both
             factions); placed in no map yet
  doc        the design document and the contracts name it

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

import make_ep3_boss_overlay as ov  # noqa: E402

sys.path.insert(0, str(TESTS_DIR))
import _p4_mod as p4  # noqa: E402

SRC = PROJECT_ROOT / "src"
SPRITES = PROJECT_ROOT / "assets" / "sprites"
REAL_SRC = ov.SRC_DIR
EP2_SRC = ov.OVERLAYS / "ep2-enemies"
DOC = PROJECT_ROOT / "docs" / "engine" / "2026-10-22_P4_ep3-final-boss.md"
BOSS = "SD_Consortium"
NEW_CLASSES = (BOSS, "SD_ConsortiumWounded", "SD_ConsortiumRocket", "SD_ConsortiumOrb", "SD_ConsortiumFlame")
EXPECTED_EDNUMS = {21112: BOSS}
# MOD-SPEC 6.1 / BESTIARY 2.5: 21100-21109 the first nine; 21110 and 21111
# the ep2-enemies overlay (docs/engine/2026-10-22_P4_ep2-enemies.md).
RESERVED_EDNUMS = set(range(21100, 21112))
COLOSSUS_HEALTH = 4500     # docs/engine/2026-10-22_P4_ep2-enemies.md section 3
PROJECTILE_PARENTS = {"SD_ConsortiumRocket": "SD_Pg7Grenade",
                      "SD_ConsortiumOrb": "SD_GeneralShell",
                      "SD_ConsortiumFlame": "SD_FlameBlob"}
LANGS = ("enu default", "ru", "ca")


# ------------------------------------------------------------------ helpers
def run_tool(argv: list[str]) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return ov.main(argv)


def write_fixture(root: Path, *, ednum: int = 21150, cls: str = "SD_FixtureBoss",
                  extra_zs: str | None = None, include_missing: bool = False) -> Path:
    """A minimal overlay source: one class, one number, one string."""
    zsdir = root / "zscript" / "sd_ep3"
    zsdir.mkdir(parents=True)
    (zsdir / "fixture.zs").write_text(
        f"class {cls} : SD_Monster\n{{\n\tStates\n\t{{\n\tSpawn:\n\t\tSDPS A -1;\n\t\tStop;\n\t}}\n}}\n",
        encoding="utf-8")
    includes = ['#include "zscript/sd_ep3/fixture.zs"']
    if include_missing:
        includes.append('#include "zscript/sd_ep3/missing.zs"')
    if extra_zs:
        (zsdir / extra_zs).write_text("// orphan\n", encoding="utf-8")
    (root / "zscript.txt").write_text('version "4.12"\n' + "\n".join(includes) + "\n", encoding="utf-8")
    (root / "MAPINFO").write_text(f"DoomEdNums\n{{\n\t{ednum} = {cls}\n}}\n", encoding="utf-8")
    (root / "LANGUAGE").write_text('[enu default]\nSD_TAG_FIXTURE = "x";\n', encoding="utf-8")
    return root


def write_sibling(root: Path, *, ednum: int, cls: str) -> Path:
    (root / "zscript" / "sd_ep2").mkdir(parents=True)
    (root / "zscript" / "sd_ep2" / "sib.zs").write_text(f"class {cls} : SD_Monster {{}}\n", encoding="utf-8")
    (root / "MAPINFO").write_text(f"DoomEdNums\n{{\n\t{ednum} = {cls}\n}}\n", encoding="utf-8")
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
    frames: set[tuple[str, str]] = set()
    for line in states_block(body).splitlines():
        m = re.match(r"^\s*([A-Z0-9_]{4})\s+([A-Z\[\]]+)\s+-?\d+\b", line)
        if m and m.group(1) != "TNT1":
            frames.update((m.group(1), f) for f in m.group(2))
    return frames


def state_labels(body: str) -> set[str]:
    return set(re.findall(r"^\s*(\w+):", states_block(body), flags=re.M))


def sprite_rotations(sprite: str) -> dict[str, set[str]]:
    rot: dict[str, set[str]] = {}
    for p in SPRITES.rglob(f"{sprite}*.png"):
        stem = p.stem
        for i in (4, 6):
            if len(stem) >= i + 2:
                rot.setdefault(stem[i], set()).add(stem[i + 1])
    return rot


def const_value(body: str, name: str) -> float:
    m = re.search(rf"\bconst\s+{name}\s*=\s*(-?[0-9.]+)\s*;", body)
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
        self.no_sibling = (self.root / "absent",)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, src: Path, out: Path) -> int:
        return run_tool(["--src", str(src), "--out", str(out), "--mod-src", str(SRC),
                         "--sibling", str(self.no_sibling[0])])

    def refused(self, src: Path, mod_src: Path = SRC, siblings=None) -> None:
        with self.assertRaises(ov.OverlayError):
            ov.plan_overlay(src, mod_src, siblings if siblings is not None else self.no_sibling)

    def test_builds_and_is_reproducible(self):
        src = write_fixture(self.root / "src")
        a, b = self.root / "a.pk3", self.root / "b.pk3"
        self.assertEqual(self.build(src, a), 0)
        self.assertEqual(self.build(src, b), 0)
        self.assertEqual(a.read_bytes(), b.read_bytes())
        names = zipfile.ZipFile(a).namelist()
        self.assertEqual(sorted(names), ["LANGUAGE", "MAPINFO", "zscript.txt", "zscript/sd_ep3/fixture.zs"])
        self.assertTrue(a.with_suffix(".txt").is_file())

    def test_dry_run_writes_nothing(self):
        src = write_fixture(self.root / "src")
        out = self.root / "dry.pk3"
        self.assertEqual(run_tool(["--src", str(src), "--out", str(out), "--dry-run",
                                   "--sibling", str(self.no_sibling[0])]), 0)
        self.assertFalse(out.exists())

    def test_refuses_a_number_the_mod_uses(self):
        self.refused(write_fixture(self.root / "s", ednum=21106))   # SD_General

    def test_refuses_a_number_a_sibling_overlay_uses(self):
        sib = write_sibling(self.root / "sib", ednum=21111, cls="SD_SiblingBoss")
        self.refused(write_fixture(self.root / "s", ednum=21111), siblings=(sib,))

    def test_refuses_a_class_a_sibling_overlay_declares(self):
        sib = write_sibling(self.root / "sib", ednum=21111, cls="SD_FixtureBoss")
        self.refused(write_fixture(self.root / "s", ednum=21150), siblings=(sib,))

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
        (src / "sprites" / "SDCNA1.png").write_bytes(b"x")
        self.refused(src)

    def test_refuses_a_zs_in_the_ep2_folder(self):
        src = write_fixture(self.root / "s")
        (src / "zscript" / "sd_ep2").mkdir()
        (src / "zscript" / "sd_ep2" / "x.zs").write_text("// x\n", encoding="utf-8")
        self.refused(src)

    def test_refuses_to_shadow_a_mod_file(self):
        src = write_fixture(self.root / "s")
        mod = self.root / "mod"
        (mod / "zscript" / "sd_ep3").mkdir(parents=True)
        (mod / "zscript" / "sd_ep3" / "fixture.zs").write_text("class SD_Other : Actor {}\n", encoding="utf-8")
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
    real source (a class the mod declares, a number its MAPINFO assigns)."""

    def test_tool_says_superseded(self):
        self.assertIn("SUPERSEDED", ov.__doc__)

    @unittest.skipUnless(REAL_SRC.is_dir(), "no work/overlays/ep3-boss/ (gitignored work/)")
    def test_real_overlay_is_refused(self):
        with self.assertRaises(ov.OverlayError):
            ov.plan_overlay(REAL_SRC, SRC)


# --------------------------------------------------------------------- mod
FILES = {
    BOSS: "zscript/monsters/consortium.zs",
    "SD_ConsortiumRocket": "zscript/monsters/consortium_rocket.zs",
    "SD_ConsortiumOrb": "zscript/monsters/consortium_orb.zs",
    "SD_ConsortiumFlame": "zscript/monsters/consortium_flame.zs",
    "SD_ConsortiumWounded": "zscript/monsters/consortium_wounded.zs",
}
SOUND_COUNT = 8    # sight, active, pain, death, call, breach, step, flame (BESTIARY 12)
IDS = {"SD_TAG_CONSORTIUM", "SD_OB_CONSORTIUM", "SD_CONSORTIUM_FREE"}


class ModTests(unittest.TestCase):
    """The Consortium as the mod ships it (D116)."""

    @classmethod
    def setUpClass(cls):
        cls.text = {c: p4.read(f) for c, f in FILES.items()}
        cls.blocks: dict[str, tuple[str | None, str]] = {}
        for p in (SRC / "zscript").rglob("*.zs"):
            cls.blocks.update(p4.class_blocks(p.read_text(encoding="utf-8")))
        cls.boss = cls.blocks[BOSS][1]

    def test_one_class_per_file_and_included(self):
        inc = p4.includes()
        for cls, rel in FILES.items():
            with self.subTest(cls=cls):
                self.assertEqual(list(p4.class_blocks(self.text[cls])), [cls])
                self.assertIn(rel.lower(), inc)

    def test_parents_and_replaces_nothing(self):
        """Design doc 2.1: the Icon of Sin is a scripted wall target, not a
        monster, and every other Doom boss is taken: its own number only."""
        self.assertEqual(p4.class_head(self.text[BOSS], BOSS), f"class {BOSS} : SD_Monster")
        for cls, parent in PROJECTILE_PARENTS.items():
            self.assertEqual(p4.class_head(self.text[cls], cls), f"class {cls} : {parent}")
        self.assertEqual(p4.class_head(self.text["SD_ConsortiumWounded"], "SD_ConsortiumWounded"),
                         f"class SD_ConsortiumWounded : {BOSS}")

    def test_editor_numbers(self):
        ednums = p4.mapinfo_ednums()
        self.assertEqual(ednums.get(21112), BOSS)
        for cls in (*PROJECTILE_PARENTS, "SD_ConsortiumWounded"):
            self.assertNotIn(cls, ednums.values(), f"{cls} is not placeable")

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
        text = self.text[BOSS]
        marked = p4.provisional_code_lines(text)
        self.assertTrue(any(l.startswith("Translation ") for l in marked), marked)
        for line in marked:
            self.assertRegex(line, r"^(Translation |Scale |const SD_\w+_SCALE )", line)
        swapped, pairs = p4.apply_documented_swap(text)
        self.assertEqual(pairs, [("SDPS", "SDCN")])
        frames = p4.state_frames(p4.class_blocks(swapped)[BOSS][1])
        self.assertEqual({s for s, _ in frames}, {"SDCN"})
        code = p4.strip_comments(swapped)
        self.assertNotIn("Translation", code)
        self.assertNotRegex(code, r"\bScale\b")
        self.assertFalse(p4.sprite_rotations("SDCN"), "SDCN is drawn: do the swap")
        # the two state edits the drawing adds are named in the header
        self.assertIn("rooted See shows SDCN Q R", text)

    def test_sounds_are_its_own_names_over_existing_lumps(self):
        lines = p4.sndinfo_lines()
        shipped = {p.stem.upper() for p in (PROJECT_ROOT / "assets" / "sounds").rglob("*.ogg")}
        used = set(re.findall(r'"(sd/[a-z0-9/_]+)"', p4.strip_comments(self.text[BOSS])))
        for name in sorted(used):
            with self.subTest(name=name):
                self.assertIn(name, lines)
                if name.startswith("sd/mon/"):
                    self.assertTrue(name.startswith("sd/mon/consortium/"), name)
        finals = []
        for name, (lump, comment) in lines.items():
            if name.startswith("sd/mon/consortium/"):
                with self.subTest(name=name):
                    self.assertIn(name, used, f"{name} is defined but the boss does not play it")
                    self.assertTrue(lump in shipped or lump.startswith("DS"), lump)
                    final = p4.FINAL_LUMP_RE.search(comment)
                    self.assertIsNotNone(final, f"{name}: no '-> final lump' in its comment")
                    self.assertNotIn(final.group(1), shipped)
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
                self.assertIn("%o", sections[lang]["SD_OB_CONSORTIUM"])
        for sid in IDS:
            self.assertTrue(sections["enu default"][sid].isascii(), sid)

    def test_health_is_twice_the_colossus(self):
        colossus = const_value(self.blocks["SD_LibertyColossus"][1], "SD_COLOSSUS_HEALTH")
        self.assertEqual(colossus, COLOSSUS_HEALTH)
        self.assertEqual(const_value(self.boss, "SD_CONSORTIUM_HEALTH"), 2 * colossus)

    def test_boss_flags_are_the_generals(self):
        gbody = self.blocks["SD_General"][1]
        for flag in ("+BOSS", "+NORADIUSDMG", "+DONTMORPH", "+BOSSDEATH"):
            self.assertIn(flag, gbody)
            self.assertIn(flag, self.boss)
        self.assertIn("A_BossDeath", self.boss)
        death = p4.states_block(self.boss).split("Death:")[1]
        self.assertLess(death.index("A_NoBlocking"), death.index("A_BossDeath"))

    def test_two_phases_at_half_health(self):
        self.assertEqual(const_value(self.boss, "SD_CONSORTIUM_BREACH_FRACTION"), 0.5)
        labels = p4.state_labels(self.boss)
        for label in ("Spawn", "See", "Walk", "Missile", "Orbs", "Rockets", "Flame", "Summon",
                      "Breach", "Volley", "Barrage", "Sweep", "Pain", "Death"):
            self.assertIn(label, labels)
        self.assertIn("CHF_DONTMOVE", self.boss)              # rooted in phase 1
        self.assertIn('SetStateLabel("Breach")', self.boss)
        self.assertIn("unbound = true", self.boss)
        self.assertIn("bInvulnerable = true", self.boss)
        self.assertIn("bInvulnerable = false", self.boss)
        self.assertLess(const_value(self.boss, "SD_CONSORTIUM_FREE_MISSILE_CHANCE_MULT"),
                        const_value(self.boss, "SD_CONSORTIUM_MISSILE_CHANCE_MULT"))
        for label in ("Orbs", "Rockets", "Flame", "Summon", "Volley", "Barrage", "Sweep"):
            self.assertIn(f'SetStateLabel("{label}")', self.boss)

    def test_attacks_reuse_the_mods_projectiles(self):
        for cls in PROJECTILE_PARENTS:
            self.assertIn(f'"{cls}"', self.boss)
            self.assertIn("override bool CanCollideWith", self.blocks[cls][1])
        for cls in ("SD_ConsortiumRocket", "SD_ConsortiumFlame"):
            self.assertIn('Obituary ""', self.blocks[cls][1])

    def test_reinforcements_from_both_factions(self):
        faction = {}
        for cls, (_, body) in self.blocks.items():
            m = re.search(r"SD_Monster\.Faction\s+(SD_FACTION_\w+)", body)
            if m:
                faction[cls] = m.group(1)
        called = set(re.findall(r'class<Actor>\s+\w+\s*=\s*"(SD_\w+)"', self.boss))
        self.assertTrue(called)
        sides = {faction[c] for c in called}
        self.assertEqual(sides, {"SD_FACTION_REICH", "SD_FACTION_LEGION"})
        self.assertIn("A_KillChildren", self.boss)
        self.assertIn("servant.master = self", self.boss)
        self.assertIn("bNoInfighting = true", self.boss)
        self.assertLessEqual(const_value(self.boss, "SD_CONSORTIUM_CAP_ROOTED"),
                             const_value(self.boss, "SD_CONSORTIUM_CAP_FREE"))
        self.assertLessEqual(const_value(self.boss, "SD_CONSORTIUM_WAVE"),
                             const_value(self.boss, "SD_CONSORTIUM_CAP_FREE"))
        self.assertIn("override int DamageMobj", self.boss)

    def test_wounded_fixture_starts_over_the_breach(self):
        """The test fixture spawns over the Breach threshold, so the first
        hits trigger it; it carries no string, sound or number of its own."""
        body = self.blocks["SD_ConsortiumWounded"][1]
        self.assertIn("SD_CONSORTIUM_BREACH_FRACTION", body)
        self.assertGreater(const_value(body, "SD_WOUNDED_MARGIN"), 0)
        self.assertNotRegex(body, r'"\$SD_|"sd/')

    def test_placed_in_no_map_yet(self):
        for p in (SRC / "maps").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            self.assertNotIn(BOSS, text, p)
            self.assertIsNone(re.search(r"\b21112\b", text), f"{p} names 21112")


class DocTests(unittest.TestCase):
    def test_doc_names_the_boss_and_the_swap(self):
        text = DOC.read_text(encoding="utf-8")
        for needle in (BOSS, "21112", "make_ep3_boss_overlay.py", "BOSS_KIND", "MAP09_BOSS_SPOT",
                       "Door_Open", "SDCN", "SD_ConsortiumWounded", "D116"):
            self.assertIn(needle, text)

    def test_contracts_name_it(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        bestiary = (PROJECT_ROOT / "docs" / "engine" / "BESTIARY.md").read_text(encoding="utf-8")
        balance = (PROJECT_ROOT / "docs" / "engine" / "BALANCE.md").read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(rf"\|\s*21112\s*\|\s*`{BOSS}`", spec))
        self.assertTrue(f"`{BOSS}`" in bestiary, "BESTIARY lacks the boss")
        self.assertTrue("The Consortium" in balance, "BALANCE lacks the boss")


if __name__ == "__main__":
    unittest.main()
