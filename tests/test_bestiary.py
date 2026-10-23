"""F5 bestiary: the enemy classes held to their contract (stdlib unittest).

No GZDoom here. These tests read `src/` and the documents that own the
contract, and they guard what the engine would only reveal one fight at a
time:

- every class exists in its own file under zscript/monsters/ and is
  #included; each derives from SD_Monster and `replaces` its Doom actor;
- editor numbers are unique, inside the enemy block BESTIARY 2.5 reserves,
  clear of GZDoom's 14001-14165 and of the arsenal, and equal to BESTIARY's;
- health, speed, pain chance and the damage ranges equal BESTIARY 12;
- every DropItem is one of OUR actors (D35: captured Soviet arms);
- every LANGUAGE id the bestiary uses exists in [enu default] and [ru] (D21);
- SNDINFO has exactly the 47 bestiary sounds, the final-lump names in
  SNDINFO's comments are the ones docs/sound/ENEMY-SOUNDS.md has cards for,
  and the per-actor counts equal BESTIARY 12's Sounds column;
- every placeholder sprite frame and sound lump exists in
  iwads/freedoom2.wad (skipped where there is no IWAD, as in CI);
- the General's summon is wired as D35 says; RANGE's gallery places all.

Run:  python3 -m unittest tests.test_bestiary -v
"""

from __future__ import annotations

import re
import struct
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS_DIR = PROJECT_ROOT / "tools"
MONSTERS_DIR = SRC / "zscript" / "monsters"
BESTIARY_MD = PROJECT_ROOT / "docs" / "engine" / "BESTIARY.md"
ENEMY_SOUNDS_MD = PROJECT_ROOT / "docs" / "sound" / "ENEMY-SOUNDS.md"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
sys.path.insert(0, str(TOOLS_DIR))

# The contract, one row per class: file under zscript/monsters/, parent,
# replaced Doom class, editor number, constant prefix, SNDINFO actor key
# (None = shares its parent's sounds).
ENEMIES = {
    "SD_ReichRifleman": ("reich_rifleman.zs", "SD_Monster", "ZombieMan", 21100, "SD_RIFLEMAN", "reichrifleman"),
    "SD_LegionTrooper": ("legion_trooper.zs", "SD_Monster", "ShotgunGuy", 21101, "SD_TROOPER", "legiontrooper"),
    "SD_Stormtrooper": ("stormtrooper.zs", "SD_Monster", "DoomImp", 21102, "SD_STORM", "stormtrooper"),
    "SD_ReichHound": ("reich_hound.zs", "SD_Monster", "Demon", 21103, "SD_HOUND", "reichhound"),
    "SD_Doughboy": ("doughboy.zs", "SD_Monster", "Cacodemon", 21104, "SD_DOUGHBOY", "doughboy"),
    "SD_Panzermensch": ("panzermensch.zs", "SD_Monster", "HellKnight", 21105, "SD_PANZER", "panzermensch"),
    "SD_General": ("general.zs", "SD_Monster", "Cyberdemon", 21106, "SD_GENERAL", "general"),
    "SD_PanzermenschSchwer": ("panzermensch_schwer.zs", "SD_Panzermensch", "BaronOfHell", 21107,
                              "SD_PANZER_HEAVY", None),
    # P4 (D104, D112), in the mod since D116 on provisional sprites (MOD-SPEC
    # 6.12). The Consortium replaces nothing (its design doc 2.1): None.
    "SD_LegionGunner": ("legion_gunner.zs", "SD_Monster", "ChaingunGuy", 21110, "SD_GUNNER", "legiongunner"),
    "SD_LibertyColossus": ("liberty_colossus.zs", "SD_Monster", "SpiderMastermind", 21111, "SD_COLOSSUS",
                           "colossus"),
    "SD_Consortium": ("consortium.zs", "SD_Monster", None, 21112, "SD_CONSORTIUM", "consortium"),
    # D123: the colossus variant (the General's SDGN tinted chrome), MAP08's
    # mini-boss; the colossus's species and sounds, its own number only.
    "SD_ChromeGeneral": ("chrome_general.zs", "SD_LibertyColossus", None, 21113, "SD_CHROME", None),
}
# The P4 classes: placed in no map yet (level-designer's), so not on RANGE's
# gallery; their sounds are their own names over existing lumps, outside the
# F5 bestiary's 47 (SNDINFO "P4 enemies").
P4_ENEMIES = frozenset({"SD_LegionGunner", "SD_LibertyColossus", "SD_Consortium", "SD_ChromeGeneral"})
P4_SOUND_PREFIXES = ("sd/mon/legiongunner/", "sd/mon/colossus/", "sd/mon/consortium/")
# Their projectiles subclass the arsenal's (tests/test_ep2_enemies.py and
# test_ep3_boss.py check them), and the Consortium's half-health test fixture.
P4_OTHER_FILES = ("colossus_rocket.zs", "colossus_flame.zs", "consortium_rocket.zs", "consortium_orb.zs",
                  "consortium_flame.zs", "consortium_wounded.zs")
PROJECTILES = {
    "SD_StormBolt": ("storm_bolt.zs", "SD_STORMBOLT"),
    "SD_DoughboyShell": ("doughboy_shell.zs", "SD_DOUGHBOYSHELL"),
    "SD_PanzerShell": ("panzer_shell.zs", "SD_PANZERSHELL"),
    "SD_GeneralShell": ("general_shell.zs", "SD_GENERALSHELL"),
}
BASE = ("SD_Monster", "monster.zs")

# Damage ranges each enemy can deal, built from its own constants:
# (kind, dice-or-damage constant, multiplier constant or None for a
# projectile, which the engine rolls as random(1,8) x Damage).
DAMAGE_SOURCES = {
    "SD_ReichRifleman": [("SD_RIFLEMAN_HIT_DICE", "SD_RIFLEMAN_HIT_MULT")],
    "SD_LegionTrooper": [("SD_TROOPER_HIT_DICE", "SD_TROOPER_HIT_MULT")],
    "SD_Stormtrooper": [("SD_STORM_MELEE_DICE", "SD_STORM_MELEE_MULT"), ("SD_StormBolt", None)],
    "SD_ReichHound": [("SD_HOUND_MELEE_DICE", "SD_HOUND_MELEE_MULT")],
    "SD_Doughboy": [("SD_DOUGHBOY_MELEE_DICE", "SD_DOUGHBOY_MELEE_MULT"), ("SD_DoughboyShell", None)],
    "SD_Panzermensch": [("SD_PANZER_MELEE_DICE", "SD_PANZER_MELEE_MULT"), ("SD_PanzerShell", None)],
    "SD_General": [("SD_GeneralShell", None)],
}
PROJECTILE_DAMAGE_DIE = 8          # Doom: projectile Damage N hits for random(1,8) x N
MULTI_SHOT_CONSTANTS = {"SD_LegionTrooper": "SD_TROOPER_SHOTS", "SD_General": "SD_GENERAL_SALVO"}

# Editor numbers (BESTIARY 2.5, MOD-SPEC 6.1, ADR 002).
ENEMY_EDNUM_MIN, ENEMY_EDNUM_MAX = 21100, 21199
GZDOOM_RESERVED = range(14001, 14166)      # AmbientSound, SoundSequence, MusicChanger...
ARSENAL_EDNUMS = range(21000, 21020)

BESTIARY_SOUND_TOTAL = 47                  # BESTIARY 12, reconciled 2026-10-13
SOUND_PREFIX = "sd/mon/"
FINAL_LUMP_RE = re.compile(r"->\s*(SD[A-Z]{6})\b")


# --- small readers ----------------------------------------------------------

def strip_zs_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def zs_constants(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for name, expr in re.findall(r"^\s*const\s+(\w+)\s*=\s*([^;]+);", strip_zs_comments(text), re.M):
        try:
            out[name] = float(eval(expr, {"__builtins__": {}}, dict(out)))  # literals and earlier consts
        except Exception:  # noqa: BLE001 - non-numeric consts are not ours to check
            continue
    return out


def zs_default(text: str, prop: str) -> str | None:
    block = re.search(r"Default\s*\{(.*?)\}", strip_zs_comments(text), re.S)
    if not block:
        return None
    m = re.search(rf"^\s*{re.escape(prop)}\s+([^;]+);", block.group(1), re.M)
    return m.group(1).strip() if m else None


def zs_states(text: str) -> str:
    m = re.search(r"States\s*\{(.*?)^\s*\}", strip_zs_comments(text), re.S | re.M)
    return m.group(1) if m else ""


def state_frames(text: str) -> list[tuple[str, str]]:
    """(SPRITE, frame letters) for every state line."""
    out = []
    for line in zs_states(text).splitlines():
        line = re.sub(r"^\s*(\w+\s*:\s*)+", "", line)
        m = re.match(r'^\s*([A-Z0-9]{4})\s+([A-Z\[\]\\]+)\s+\S', line)
        if m and m.group(1) not in {"GOTO", "LOOP", "STOP", "WAIT", "FAIL"}:
            out.append((m.group(1), m.group(2)))
    return out


def parse_language(text: str) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: list[str] = []
    for raw in text.splitlines():
        line = raw.split("//")[0].strip()
        if not line:
            continue
        header = re.match(r"^\[([^\]]+)\]$", line)
        if header:
            current = header.group(1).split()
            for code in current:
                sections.setdefault(code, {})
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$", line)
        if m and current:
            for code in current:
                sections[code][m.group(1)] = m.group(2)
    return sections


RANDOM_RE = re.compile(r"^\$random\s+(\S+)\s*\{\s*([^}]*?)\s*\}\s*$")


def sndinfo_entries() -> list[tuple[str, str, str | None]]:
    """(logical, lump it plays, final lump) for the sd/mon/ names the classes
    play. A placeholder line names its final lump in a `// -> SD...` comment;
    an installed one (N9e) IS the final lump; a `$random` alias over several
    approved takes (D86) counts once, as `$random`, with its card's name as
    the final lump (the members' lump with the take digit back to the card's
    letter is not recoverable, so the card is read from the group's first
    member: SDRRIAT1 -> SDRRIATK through ENEMY-SOUNDS' cards)."""
    out, groups, members = [], {}, set()
    lines = (SRC / "lumps" / "SNDINFO").read_text(encoding="utf-8").splitlines()
    for raw in lines:
        m = RANDOM_RE.match(raw.split("//")[0].strip())
        if m and m.group(1).startswith(SOUND_PREFIX):
            groups[m.group(1)] = m.group(2).split()
            members |= set(groups[m.group(1)])
    cards = set(re.findall(r"^\|\s*`(SD[A-Z]{6})`\s*\|", ENEMY_SOUNDS_MD.read_text(encoding="utf-8"), re.M))
    lump_of = {}
    for raw in lines:
        code, _, comment = raw.partition("//")
        parts = code.split()
        if len(parts) == 2 and parts[0].startswith(SOUND_PREFIX):
            lump_of[parts[0]] = parts[1].upper()
            if parts[0] in members:
                continue
            final = FINAL_LUMP_RE.search(comment)
            lump = parts[1].upper()
            out.append((parts[0], lump, final.group(1) if final else (lump if lump in cards else None)))
    for group, ms in groups.items():
        first = lump_of[ms[0]]
        card = next((c for c in cards if c[:7] == first[:7]), None)
        out.append((group, "$random", card))
    return out


def bestiary_summary() -> dict[str, dict[str, str]]:
    """BESTIARY 12, keyed by class name."""
    text = BESTIARY_MD.read_text(encoding="utf-8")
    section = re.search(r"^## 12\..*?$(.*?)^## 13\.", text, re.M | re.S).group(1)
    cols = ["n", "name", "class", "faction", "ednum", "replaces", "hp", "speed", "pain",
            "attack", "sprite", "images", "sounds"]
    rows: dict[str, dict[str, str]] = {}
    for line in section.splitlines():
        if not re.match(r"^\|\s*\d+\s*\|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        row = dict(zip(cols, cells))
        name = re.search(r"`(\w+)`", row["class"]).group(1)
        rows[name] = row
    return rows


def number(cell: str) -> int:
    return int(re.search(r"\d+", cell.replace("*", "")).group(0))


def iwad_namespace(path: Path) -> tuple[set[str], set[str]]:
    """(sprite lumps between S_START/S_END, every lump name) of a WAD."""
    blob = path.read_bytes()
    count, offset = struct.unpack("<ii", blob[4:12])
    names = [blob[offset + 16 * i + 8: offset + 16 * i + 16].rstrip(b"\0").decode("ascii", "replace").upper()
             for i in range(count)]
    sprites: set[str] = set()
    inside = False
    for name in names:
        if name in ("S_START", "SS_START"):
            inside = True
        elif name in ("S_END", "SS_END"):
            inside = False
        elif inside:
            sprites.add(name)
    return sprites, set(names)


def read_zs(filename: str) -> str:
    return (MONSTERS_DIR / filename).read_text(encoding="utf-8")


def mapinfo_ednums() -> dict[int, str]:
    text = (SRC / "lumps" / "MAPINFO").read_text(encoding="utf-8")
    block = re.search(r"^DoomEdNums\s*\{(.*?)^\}", text, re.S | re.M).group(1)
    out: dict[int, str] = {}
    for line in block.splitlines():
        line = line.split("//")[0].strip()
        if not line:
            continue
        num, _, cls = line.partition("=")
        key = int(num)
        if key in out:
            raise AssertionError(f"editor number {key} assigned twice")
        out[key] = cls.strip()
    return out


# --- the tests ---------------------------------------------------------------

class BestiaryClassesTest(unittest.TestCase):
    def test_each_class_has_its_own_file(self):
        for cls, (filename, *_rest) in ENEMIES.items():
            declared = re.findall(r"^class\s+(\w+)", read_zs(filename), re.M)
            self.assertEqual([cls], declared, f"{filename} must declare exactly {cls}")
        for cls, (filename, _) in PROJECTILES.items():
            self.assertEqual([cls], re.findall(r"^class\s+(\w+)", read_zs(filename), re.M))
        self.assertEqual([BASE[0]], re.findall(r"^class\s+(\w+)", read_zs(BASE[1]), re.M))

    def test_every_monster_file_is_included(self):
        entry = (SRC / "lumps" / "zscript.txt").read_text(encoding="utf-8")
        included = {inc.lower() for inc in re.findall(r'^\s*#include\s+"([^"]+)"', entry, re.M)}
        on_disk = {f"zscript/monsters/{p.name}".lower() for p in MONSTERS_DIR.glob("*.zs")}
        expected = {f"zscript/monsters/{f}".lower() for f, *_ in ENEMIES.values()}
        expected |= {f"zscript/monsters/{f}".lower() for f, _ in PROJECTILES.values()}
        expected |= {f"zscript/monsters/{f}" for f in P4_OTHER_FILES}
        expected.add(f"zscript/monsters/{BASE[1]}")
        self.assertEqual(expected, on_disk, "zscript/monsters/ holds exactly the bestiary's files")
        self.assertEqual(set(), on_disk - included, "monster files that nothing #includes")

    def test_parent_and_replacement(self):
        for cls, (filename, parent, replaced, *_rest) in ENEMIES.items():
            if replaced is None:      # the Consortium (D116): its own number only
                self.assertRegex(strip_zs_comments(read_zs(filename)), rf"(?m)^class\s+{cls}\s*:\s*{parent}\s*$")
                continue
            self.assertRegex(read_zs(filename),
                             rf"class\s+{cls}\s*:\s*{parent}\s+replaces\s+{replaced}\b",
                             f"{cls} must derive from {parent} and replace {replaced} (BESTIARY 2.4)")
        self.assertRegex(read_zs(BASE[1]), r"class\s+SD_Monster\s*:\s*Actor\b")

    def test_no_doom_monster_sound_or_string_leaks_in(self):
        """BESTIARY 2.4: nothing inherited from Doom's monsters."""
        for filename in [f for f, *_ in ENEMIES.values()] + [f for f, _ in PROJECTILES.values()]:
            text = strip_zs_comments(read_zs(filename))
            for prop in ("SeeSound", "AttackSound", "PainSound", "DeathSound", "ActiveSound"):
                value = zs_default(text, prop)
                if value is not None:
                    self.assertTrue(value.strip('"').startswith(SOUND_PREFIX), f"{filename} {prop} {value}")
            self.assertNotRegex(text, r'"\$(OB|FN)_', f"{filename} uses an engine string id")

    def test_every_class_sets_its_own_species(self):
        """Vanilla infighting across our classes needs distinct species (BESTIARY 2.2)."""
        seen = {}
        for cls, (filename, parent, *_rest) in ENEMIES.items():
            species = zs_default(read_zs(filename), "Species")
            if parent != "SD_Monster":
                self.assertIsNone(species, f"{cls} must inherit {parent}'s species")
                continue
            self.assertEqual(f'"{cls}"', species, f"{cls} must set Species to its own name")
            self.assertNotIn(species, seen)
            seen[species] = cls
        self.assertNotRegex(strip_zs_comments("".join(read_zs(f) for f, *_ in ENEMIES.values())),
                            r"(DONTHARMSPECIES|DOHARMSPECIES)")


class BestiaryEditorNumbersTest(unittest.TestCase):
    def test_numbers_unique_in_block_and_clear_of_collisions(self):
        ednums = mapinfo_ednums()
        by_class = {cls: num for num, cls in ednums.items()}
        for cls, (_f, _p, _r, ednum, *_rest) in ENEMIES.items():
            self.assertEqual(ednum, by_class.get(cls), f"{cls} must be {ednum} in MAPINFO DoomEdNums")
            self.assertTrue(ENEMY_EDNUM_MIN <= ednum <= ENEMY_EDNUM_MAX, f"{cls} outside 21100-21199")
            self.assertNotIn(ednum, GZDOOM_RESERVED)
            self.assertNotIn(ednum, ARSENAL_EDNUMS)
        bestiary = {num for num, cls in ednums.items() if cls in ENEMIES}
        self.assertEqual(len(ENEMIES), len(bestiary))
        others_in_block = {num: cls for num, cls in ednums.items()
                           if ENEMY_EDNUM_MIN <= num <= ENEMY_EDNUM_MAX and cls not in ENEMIES}
        self.assertEqual({}, others_in_block, "something else sits in the enemy block")
        for cls in PROJECTILES:
            self.assertNotIn(cls, by_class, f"{cls} is a projectile and must not be placeable")

    def test_numbers_match_bestiary(self):
        summary = bestiary_summary()
        for cls, (_f, _p, replaced, ednum, *_rest) in ENEMIES.items():
            self.assertIn(cls, summary, f"{cls} missing from BESTIARY 12")
            self.assertEqual(ednum, number(summary[cls]["ednum"]))
            self.assertIn(replaced or "nothing", summary[cls]["replaces"])

    def test_mod_spec_lists_the_numbers(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        for cls, (_f, _p, _r, ednum, *_rest) in ENEMIES.items():
            self.assertRegex(spec, rf"\|\s*{ednum}\s*\|\s*`{cls}`", f"MOD-SPEC 6.1 lacks {ednum} = {cls}")


class BestiaryNumbersTest(unittest.TestCase):
    """The code is the truth; BESTIARY 12 must say the same thing."""

    def resolved(self, cls: str, prop: str) -> float:
        filename = ENEMIES[cls][0]
        text = read_zs(filename)
        value = zs_default(text, prop)
        self.assertIsNotNone(value, f"{cls} sets no {prop}")
        consts = zs_constants(text)
        return consts[value] if value in consts else float(value)

    def test_health_speed_painchance(self):
        summary = bestiary_summary()
        for cls in ENEMIES:
            row = summary[cls]
            self.assertEqual(number(row["hp"]), self.resolved(cls, "Health"), f"{cls} Health")
            if ENEMIES[cls][1] != "SD_Monster":
                continue      # a variant inherits speed and pain chance
            self.assertEqual(number(row["speed"]), self.resolved(cls, "Speed"), f"{cls} Speed")
            self.assertEqual(number(row["pain"]), self.resolved(cls, "PainChance"), f"{cls} PainChance")

    def test_damage_ranges(self):
        summary = bestiary_summary()
        projectile_damage = {}
        for proj, (filename, prefix) in PROJECTILES.items():
            consts = zs_constants(read_zs(filename))
            projectile_damage[proj] = consts[f"{prefix}_DAMAGE"]
            self.assertEqual(f"{prefix}_DAMAGE", zs_default(read_zs(filename), "Damage"))
        for cls, sources in DAMAGE_SOURCES.items():
            consts = zs_constants(read_zs(ENEMIES[cls][0]))
            ranges = set()
            for first, mult in sources:
                if mult is None:
                    d = projectile_damage[first]
                    ranges.add((int(d), int(d * PROJECTILE_DAMAGE_DIE)))
                else:
                    ranges.add((int(consts[mult]), int(consts[first] * consts[mult])))
            documented = {(int(a), int(b)) for a, b in re.findall(r"(\d+)–(\d+)", summary[cls]["attack"])}
            self.assertEqual(documented, ranges, f"{cls}: BESTIARY 12 says {summary[cls]['attack']!r}")

    def test_multi_shot_counts(self):
        summary = bestiary_summary()
        for cls, const in MULTI_SHOT_CONSTANTS.items():
            consts = zs_constants(read_zs(ENEMIES[cls][0]))
            self.assertEqual(number(re.search(r"(\d+)×", summary[cls]["attack"]).group(1)), consts[const])
        general = zs_states(read_zs("general.zs"))
        missile = re.search(r"Missile:(.*?)Goto See;", general, re.S).group(1)
        self.assertEqual(zs_constants(read_zs("general.zs"))["SD_GENERAL_SALVO"],
                         missile.count("A_SD_GeneralShot"), "one shell per salvo frame")


class BestiaryDropsTest(unittest.TestCase):
    def test_every_drop_is_ours(self):
        """D35: the invaders drop captured Soviet arms - our classes, no IWAD item."""
        ours = set()
        for path in (SRC / "zscript").rglob("*.zs"):
            ours |= set(re.findall(r"^class\s+(\w+)", path.read_text(encoding="utf-8"), re.M))
        drops = {}
        for cls, (filename, *_rest) in ENEMIES.items():
            for item in re.findall(r'DropItem\s+"([^"]+)"', strip_zs_comments(read_zs(filename))):
                drops.setdefault(cls, []).append(item)
                self.assertTrue(item.startswith("SD_"), f"{cls} drops {item}, not one of ours")
                self.assertIn(item, ours, f"{cls} drops {item}, which no ZScript class declares")
        self.assertEqual({"SD_ReichRifleman": ["SD_Clip"], "SD_LegionTrooper": ["SD_Izh"],
                          "SD_LegionGunner": ["SD_AkmAmmo"]}, drops)   # D116: the AKM's magazine


class BestiaryLanguageTest(unittest.TestCase):
    def test_every_id_exists_in_both_languages(self):
        sections = parse_language((SRC / "lumps" / "LANGUAGE").read_text(encoding="utf-8"))
        ids = set()
        for path in MONSTERS_DIR.glob("*.zs"):
            ids |= set(re.findall(r'"\$(SD_[A-Z0-9_]+)"', path.read_text(encoding="utf-8")))
        self.assertIn("SD_GENERAL_ORDER", ids)
        for cls, (filename, *_rest) in ENEMIES.items():
            self.assertRegex(read_zs(filename), r'Tag\s+"\$SD_TAG_', f"{cls} has no Tag of its own")
        for ident in sorted(ids):
            self.assertIn(ident, sections["default"], f"{ident} missing in [enu default]")
            self.assertIn(ident, sections["ru"], f"{ident} missing in [ru] (D21)")
            self.assertRegex(sections["ru"][ident], r"[Ѐ-ӿ]", f"{ident} [ru] is not Russian")


class BestiarySoundsTest(unittest.TestCase):
    def test_47_sounds_matching_the_sound_designers_cards(self):
        entries = [e for e in sndinfo_entries() if not e[0].startswith(P4_SOUND_PREFIXES)]
        self.assertEqual(BESTIARY_SOUND_TOTAL, len(entries))
        finals = [f for _, _, f in entries]
        self.assertNotIn(None, finals, "every bestiary SNDINFO line names its final lump in a comment")
        self.assertEqual(len(finals), len(set(finals)), "a final lump is named twice")
        cards = set(re.findall(r"^\|\s*`(SD[A-Z]{6})`\s*\|", ENEMY_SOUNDS_MD.read_text(encoding="utf-8"), re.M))
        self.assertEqual(cards, set(finals), "SNDINFO's final lumps vs docs/sound/ENEMY-SOUNDS.md cards")

    def test_per_actor_counts_match_bestiary(self):
        summary = bestiary_summary()
        entries = sndinfo_entries()
        for cls, (*_rest, key) in ENEMIES.items():
            expected = number(summary[cls]["sounds"])
            got = 0 if key is None else sum(1 for logical, _, _ in entries
                                             if logical.startswith(f"{SOUND_PREFIX}{key}/"))
            self.assertEqual(expected, got, f"{cls}: BESTIARY 12 says {expected} sounds")

    def test_every_sound_the_bestiary_plays_is_defined(self):
        defined = {logical for logical, _, _ in sndinfo_entries()}
        used = set()
        for path in MONSTERS_DIR.glob("*.zs"):
            used |= set(re.findall(r'"(sd/mon/[a-z0-9/_]+)"', path.read_text(encoding="utf-8")))
        self.assertEqual(defined, used, "SNDINFO sd/mon/ names and the names the classes play differ")


class BestiaryGeneralTest(unittest.TestCase):
    def test_summon_is_wired_as_d35_says(self):
        text = read_zs("general.zs")
        consts = zs_constants(text)
        self.assertEqual(0.5, consts["SD_GENERAL_SUMMON_FRACTION"])
        self.assertEqual(2, consts["SD_GENERAL_SUMMON_COUNT"])
        code = strip_zs_comments(text)
        self.assertIn('A_SpawnItemEx("SD_ReichRifleman"', code)
        self.assertIn('StringTable.Localize("$SD_GENERAL_ORDER")', code)
        self.assertIn('"sd/mon/general/summon"', code)
        self.assertRegex(code, r"summoned\s*=\s*true;\s*SetStateLabel\(\"Summon\"\)",
                         "the once-only flag must be set before the jump")
        self.assertRegex(zs_states(text), r"Summon:\s*\n\s*SDGN Q 15 Bright A_SD_GeneralSummon;")
        see = re.search(r"See:(.*?)Loop;", zs_states(text), re.S).group(1)
        self.assertNotIn("A_Chase", see, "every See frame must check the summon first")


class BestiaryRangeTest(unittest.TestCase):
    def test_gallery_places_one_of_each_deaf(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("sdmap_RANGE", SRC / "maps" / "RANGE" / "map.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        things = module.build_textmap().things
        placed = [t for t in things if ENEMY_EDNUM_MIN <= t.type <= ENEMY_EDNUM_MAX]
        self.assertEqual(sorted(e[3] for c, e in ENEMIES.items() if c not in P4_ENEMIES),
                         sorted(t.type for t in placed))
        for thing in placed:
            self.assertTrue(thing.extra.get("ambush"), f"{thing.type} must be deaf")
            self.assertTrue(module.GALLERY_Y1 < thing.y < module.GALLERY_Y2, "inside the gallery")


@unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not present (CI has no IWAD)")
class BestiaryPlaceholdersInIwadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sprites, cls.lumps = iwad_namespace(IWAD)

    def test_every_placeholder_sprite_frame_exists(self):
        files = [f for f, *_ in ENEMIES.values()] + [f for f, _ in PROJECTILES.values()]
        # Our own sprites ship from assets/sprites/ (the Legion's SDLT since
        # D54) and are not placeholders: tests/test_legion_sprites.py checks them.
        ours = {p.stem[:4].upper() for p in (PROJECT_ROOT / "assets" / "sprites").rglob("*.png")}
        checked = 0
        for filename in files:
            for sprite, frames in state_frames(read_zs(filename)):
                if sprite in ours:
                    continue
                for frame in frames:
                    hit = any(name.startswith(sprite) and (name[4:5] == frame or name[6:7] == frame)
                              for name in self.sprites)
                    self.assertTrue(hit, f"{filename}: {sprite}{frame} is not a sprite in {IWAD.name}")
                    checked += 1
        # Since D81 (2026-10-20) every enemy and enemy projectile names our own
        # sprite (the shells were the last): nothing is left to check in the
        # IWAD. A class added on a placeholder turns this red on purpose: its
        # frames are then checked above and this line is relaxed with it.
        self.assertEqual(checked, 0, "D81: no bestiary state names an IWAD sprite")

    def test_every_declared_iwad_sprite_exists(self):
        import check_pk3
        for name in check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC):
            self.assertTrue(any(s.startswith(name) for s in self.sprites), f"MOD-SPEC 5.1 {name} not in the IWAD")

    def test_every_placeholder_sound_exists(self):
        # Since N9e (D83, D86) most lines play our own lumps (packed, held by
        # tests/test_enemy_sfx_install.py); the Freedoom stand-ins left are
        # the voices (D87).
        placeholders = [(logical, lump) for logical, lump, _ in sndinfo_entries() if lump.startswith("DS")]
        self.assertTrue(placeholders)
        for logical, lump in placeholders:
            self.assertIn(lump, self.lumps, f"{logical} -> {lump} is not a lump in {IWAD.name}")


if __name__ == "__main__":
    unittest.main()
