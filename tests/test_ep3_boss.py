"""D112 (P4): the Episode 3 final boss DRAFT overlay, static checks.

`tools/make_ep3_boss_overlay.py` packs `work/overlays/ep3-boss/` (the boss
SD_Consortium, its draft-only half-health twin SD_ConsortiumWounded and its
three projectiles) into `work/overlays/sd-ep3-boss.pk3`, loaded after the
mod with `-file`. Design: docs/engine/2026-10-22_P4_ep3-final-boss.md. What
is checked, and why:

  tool       on a synthetic source (CI has no work/): it builds, holds
             exactly the source's files, two builds are byte-identical; it
             refuses an editor number the mod uses, one a sibling overlay
             uses (the ep2-enemies overlay's 21110 and 21111) or one outside
             21100-21199, a class the mod or a sibling declares, a path that
             would shadow a mod file, a .zs no #include names, an #include
             of a missing file, a stray file, and an --out under src/,
             dist/ or assets/
  mod        nothing under src/ names the new classes yet (flips at
             integration)
  real       (skips without work/overlays/ep3-boss/) the overlay builds; its
             classes exist and derive from classes the mod (or the overlay)
             has; its editor number is free in the mod and in the ep2
             overlay; every frame a state shows (the parent's inherited
             Spawn included) has its lumps in assets/sprites/; every sound
             is a name the mod's SNDINFO defines; every $SD_ id is in its
             LANGUAGE in all three languages and none overrides a mod id;
             the brief holds: health twice the colossus's, the General's
             boss flags, A_BossDeath, two phases split at half health, the
             three existing projectiles, reinforcements from both factions,
             its own fire passing through monsters
  doc        the design document names the class, the number, the tool, and
             MAP09's swap (BOSS_KIND, MAP09_BOSS_SPOT)

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


class ModUntouchedTests(unittest.TestCase):
    def test_src_does_not_name_the_new_classes(self):
        for p in SRC.rglob("*"):
            if p.is_file() and p.suffix in ("", ".zs", ".txt", ".py"):
                text = p.read_text(encoding="utf-8", errors="replace")
                for cls in NEW_CLASSES:
                    self.assertNotIn(cls, text, f"{p} names {cls}: the draft entered the mod")


# -------------------------------------------------------------------- real
@unittest.skipUnless(REAL_SRC.is_dir(), "no work/overlays/ep3-boss/ (gitignored work/)")
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
        cls.boss = cls.blocks[BOSS][1]

    def parent_body(self, parent: str) -> str:
        if parent in self.blocks:
            return self.blocks[parent][1]
        return class_blocks(self.mod_classes[parent].read_text(encoding="utf-8"))[parent][1]

    def test_builds(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "sd-ep3-boss.pk3"
            self.assertEqual(run_tool(["--src", str(REAL_SRC), "--out", str(out)]), 0)
            self.assertEqual(sorted(zipfile.ZipFile(out).namelist()), sorted(self.plan.files))

    def test_classes(self):
        self.assertEqual(set(self.plan.classes), set(NEW_CLASSES))
        for cls, (parent, _) in self.blocks.items():
            with self.subTest(cls=cls):
                self.assertTrue(parent in self.mod_classes or parent in self.blocks,
                                f"{cls} derives from {parent}, not a mod class")
        for cls, parent in PROJECTILE_PARENTS.items():
            self.assertEqual(self.blocks[cls][0], parent)
        self.assertEqual(self.blocks[BOSS][0], "SD_Monster")
        self.assertEqual(self.blocks["SD_ConsortiumWounded"][0], BOSS)

    def test_editor_numbers(self):
        self.assertEqual(self.plan.ednums, EXPECTED_EDNUMS)
        mod = ov.mapinfo_ednums((SRC / "lumps" / "MAPINFO").read_text(encoding="utf-8"))
        for num in self.plan.ednums:
            self.assertNotIn(num, mod)
            self.assertNotIn(num, RESERVED_EDNUMS)
            self.assertIn(num, ov.ENEMY_EDNUMS)
        if (EP2_SRC / "MAPINFO").is_file():
            ep2 = ov.mapinfo_ednums((EP2_SRC / "MAPINFO").read_text(encoding="utf-8"))
            self.assertFalse(set(ep2) & set(self.plan.ednums))

    def test_every_frame_has_its_sprites(self):
        for cls, (parent, body) in self.blocks.items():
            frames = state_frames(body)
            p, labels = parent, state_labels(body)
            # inherited states (the projectiles' flight, the twin's everything)
            while "Spawn" not in labels and p is not None and (p in self.blocks or p in self.mod_classes):
                pbody = self.parent_body(p)
                frames |= state_frames(pbody)
                labels |= state_labels(pbody)
                p = self.blocks[p][0] if p in self.blocks else None
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
                for sid, text in overlay[lang].items():
                    if sid.startswith("SD_OB_"):
                        self.assertIn("%o", text, f"{lang} {sid}")
        if (EP2_SRC / "LANGUAGE").is_file():
            ep2 = language_sections((EP2_SRC / "LANGUAGE").read_text(encoding="utf-8"))
            self.assertFalse(used & set(ep2.get("enu default", {})), "an id collides with the ep2 overlay")

    def test_health_is_twice_the_colossus(self):
        colossus = COLOSSUS_HEALTH
        ep2 = EP2_SRC / "zscript" / "sd_ep2" / "liberty_colossus.zs"
        if ep2.is_file():
            colossus = const_value(class_blocks(ep2.read_text(encoding="utf-8"))["SD_LibertyColossus"][1],
                                   "SD_COLOSSUS_HEALTH")
        self.assertEqual(const_value(self.boss, "SD_CONSORTIUM_HEALTH"), 2 * colossus)

    def test_boss_flags_are_the_generals(self):
        gbody = class_blocks((SRC / "zscript" / "monsters" / "general.zs").read_text(encoding="utf-8"))["SD_General"][1]
        for flag in ("+BOSS", "+NORADIUSDMG", "+DONTMORPH", "+BOSSDEATH"):
            self.assertIn(flag, gbody)
            self.assertIn(flag, self.boss)
        self.assertIn("A_BossDeath", self.boss)
        self.assertIn("A_NoBlocking", self.boss)
        self.assertNotRegex(self.boss, r"^\s*class\s+SD_Consortium\s*:\s*SD_Monster\s+replaces",
                            "replaces nothing (design doc 2)")
        death = states_block(self.boss).split("Death:")[1]
        self.assertLess(death.index("A_NoBlocking"), death.index("A_BossDeath"))

    def test_two_phases_at_half_health(self):
        self.assertEqual(const_value(self.boss, "SD_CONSORTIUM_BREACH_FRACTION"), 0.5)
        labels = state_labels(self.boss)
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
        # every attack state of each phase is reachable from the chooser
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
        for cls, path in self.mod_classes.items():
            body = class_blocks(path.read_text(encoding="utf-8")).get(cls, (None, ""))[1]
            m = re.search(r"SD_Monster\.Faction\s+(SD_FACTION_\w+)", body)
            if m:
                faction[cls] = m.group(1)
        called = set(re.findall(r'class<Actor>\s+\w+\s*=\s*"(SD_\w+)"', self.boss))
        self.assertTrue(called)
        for cls in called:
            self.assertIn(cls, self.mod_classes, cls)
        sides = {faction[c] for c in called}
        self.assertIn("SD_FACTION_REICH", sides)
        self.assertIn("SD_FACTION_LEGION", sides)
        self.assertIn("A_KillChildren", self.boss)
        self.assertIn("servant.master = self", self.boss)
        self.assertIn("bNoInfighting = true", self.boss)
        self.assertLessEqual(const_value(self.boss, "SD_CONSORTIUM_CAP_ROOTED"),
                             const_value(self.boss, "SD_CONSORTIUM_CAP_FREE"))
        self.assertLessEqual(const_value(self.boss, "SD_CONSORTIUM_WAVE"),
                             const_value(self.boss, "SD_CONSORTIUM_CAP_FREE"))
        self.assertIn("override int DamageMobj", self.boss)


class DocTests(unittest.TestCase):
    def test_doc_names_the_boss_and_the_swap(self):
        text = DOC.read_text(encoding="utf-8")
        for needle in (BOSS, "21112", "make_ep3_boss_overlay.py", "BOSS_KIND", "MAP09_BOSS_SPOT",
                       "Door_Open", "SDCN", "SD_ConsortiumWounded"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
