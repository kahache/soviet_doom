"""V3 (D120, proposal A4): the RGD-5 hand grenade, slot 8, ADR 012.

A thrown weapon whose grenade is its own ammunition: SD_Rgd5 (the hand and
the pouch of two, 21009), SD_Rgd5Ammo (the pool and one loose grenade,
21021; it hands over the weapon too), SD_Rgd5Box (a crate, 21022) and the
fused, bouncing SD_Rgd5Grenade. On provisional sprites (D116, MOD-SPEC
6.12) until Gemini's are drawn. Design and balance:
docs/engine/2026-10-23_V3_rgd5.md. Checked, without the engine (D26):

  mod      the four classes, their files and includes; the three editor
           numbers, free and in their sub-ranges; slot 8 in SD_Player and on
           the class; never raised by itself; one press, one throw; every
           frame names an installed sprite; the documented swaps give the
           final names and drop every tint and scale; five sounds of its own
           over shipped lumps, final lumps reserved; six ids in three
           languages; the loose grenade gives the weapon
  fuse     the burst only from the fuse (Death is "stopped", not the
           blast); 1.5-2 s; the arc lofted up, autoaim off, clamped
  balance  under the RPG-7 on any one target, wider than the PG-7V's blast,
           kills a rifleman and a trooper inside most of its radius, nothing
           on the three bosses (+NORADIUSDMG); a scarce pool
  maps     placed, if at all, only in Episodes 2-3 or the range
  docs     ADR 012, the design doc, the Gemini prompts, MOD-SPEC and BALANCE

Stdlib only.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))
import _p4_mod as p4  # noqa: E402

SRC = PROJECT_ROOT / "src"
SOUNDS = PROJECT_ROOT / "assets" / "sounds"
DOCS = PROJECT_ROOT / "docs"
DESIGN = DOCS / "engine" / "2026-10-23_V3_rgd5.md"
ADR = DOCS / "engine" / "adr" / "012-rgd5-hand-grenade.md"
PROMPTS = DOCS / "product" / "2026-10-23_V3_gemini-rgd5-prompts.md"

WEAPON_FILE = "zscript/weapons/rgd5.zs"
AMMO_FILE = "zscript/weapons/rgd5_ammo.zs"
GRENADE_FILE = "zscript/weapons/rgd5_grenade.zs"
FILES = {WEAPON_FILE: ["SD_Rgd5"], AMMO_FILE: ["SD_Rgd5Ammo", "SD_Rgd5Box"],
         GRENADE_FILE: ["SD_Rgd5Grenade"]}
EDNUMS = {21009: "SD_Rgd5", 21021: "SD_Rgd5Ammo", 21022: "SD_Rgd5Box"}
SLOT = 8
IDS = {"SD_TAG_RGD5", "SD_PICKUP_RGD5", "SD_OB_RGD5", "SD_AMMO_RGD5", "SD_GOT_RGD5", "SD_GOT_RGD5BOX"}
SOUND_NAMES = {"sd/weapon/rgd5/pin", "sd/weapon/rgd5/throw", "sd/weapon/rgd5/bounce",
               "sd/weapon/rgd5/explode", "sd/weapon/rgd5/pickup"}
# MOD-SPEC 6.12: provisional sprite -> final, per file, as each header's sed says.
SWAPS = {WEAPON_FILE: [("SDAX", "SDRG"), ("SDHB", "SDRQ")],
         AMMO_FILE: [("SDHB", "SDRJ"), ("SDRB", "SDRZ")],
         GRENADE_FILE: [("SDHB", "SDRN")]}
FINAL_SPRITES = {"SDRG", "SDRQ", "SDRJ", "SDRZ", "SDRN"}
TICS_PER_SECOND = 35
FUSE_SECONDS = (1.5, 2.0)          # the brief: ~1.5-2 s
PROJECTILE_AVG = 4.5               # Doom projectile damage x random(1,8): avg x4.5 (BALANCE 0)
ICE_AXE_SELECTION = 3700
# Where a level designer may place it (the design doc section 6): Episodes 2
# and 3 and the practice range; Episode 1 shipped in v1.0.
ALLOWED_MAPS = {"MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09", "RANGE"}


def body(rel: str, cls: str) -> str:
    return p4.class_blocks(p4.read(rel))[cls][1]


def label_lines(text: str, label: str) -> list[str]:
    states = p4.states_block(text)
    lines = states.splitlines()
    start = next(i for i, l in enumerate(lines) if re.match(rf"^\s*{label}:\s*$", l))
    out = []
    for line in lines[start + 1:]:
        if re.match(r"^\s*(Goto|Loop|Stop)\b", line) or re.match(r"^\s*\w+:\s*$", line):
            break
        out.append(line)
    return out


def tics(lines: list[str]) -> int:
    return sum(int(m.group(1)) for l in lines if (m := re.match(r"^\s*\w{4}\s+[A-Z]+\s+(\d+)\b", l)))


class ModTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.texts = {rel: p4.read(rel) for rel in FILES}
        cls.weapon = body(WEAPON_FILE, "SD_Rgd5")
        cls.ammo = body(AMMO_FILE, "SD_Rgd5Ammo")
        cls.box = body(AMMO_FILE, "SD_Rgd5Box")
        cls.grenade = body(GRENADE_FILE, "SD_Rgd5Grenade")
        cls.player = p4.strip_comments(body("zscript/sd/player.zs", "SD_Player"))

    def test_classes_files_and_includes(self):
        for rel, classes in FILES.items():
            with self.subTest(rel=rel):
                self.assertEqual(list(p4.class_blocks(self.texts[rel])), classes)
                self.assertIn(rel, p4.includes())
        self.assertEqual(p4.class_head(self.texts[WEAPON_FILE], "SD_Rgd5"), "class SD_Rgd5 : DoomWeapon")
        self.assertEqual(p4.class_head(self.texts[AMMO_FILE], "SD_Rgd5Ammo"), "class SD_Rgd5Ammo : Ammo")
        self.assertEqual(p4.class_head(self.texts[AMMO_FILE], "SD_Rgd5Box"), "class SD_Rgd5Box : SD_Rgd5Ammo")
        self.assertEqual(p4.class_head(self.texts[GRENADE_FILE], "SD_Rgd5Grenade"), "class SD_Rgd5Grenade : Actor")
        # nothing is replaced: Doom has no grenade
        for rel in FILES:
            self.assertNotRegex(p4.strip_comments(self.texts[rel]), r"\breplaces\b", rel)
        # no other file declares these classes
        files = p4.mod_class_files()
        for rel, classes in FILES.items():
            for c in classes:
                self.assertEqual(files[c], SRC / rel)

    def test_editor_numbers_are_free_and_in_their_ranges(self):
        ednums = p4.mapinfo_ednums()
        for num, cls in EDNUMS.items():
            self.assertEqual(ednums.get(num), cls)
            self.assertEqual(list(ednums.values()).count(cls), 1, cls)
        self.assertIn(21009, range(21000, 21020))          # MOD-SPEC 6.1 weapons
        for num in (21021, 21022):
            self.assertIn(num, range(21020, 21040))        # ammo and items
        # No tool gives the numbers another meaning.
        for p in (PROJECT_ROOT / "tools").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            for num in EDNUMS:
                self.assertNotRegex(text, rf"\b{num}\b", f"{p} names {num}")

    def test_slot_eight_on_its_own_key(self):
        self.assertRegex(self.player, rf'Player\.WeaponSlot\s+{SLOT}\s*,\s*"SD_Rgd5"\s*;')
        self.assertEqual(p4.default_value(self.weapon, "Weapon.SlotNumber"), str(SLOT))
        self.assertEqual(re.findall(rf'Player\.WeaponSlot\s+{SLOT}\b[^;]*;', self.player),
                         [f'Player.WeaponSlot {SLOT}, "SD_Rgd5";'])
        self.assertNotIn("SD_Rgd5", re.findall(r'Player\.StartItem\s+"(\w+)"', self.player))
        self.assertNotIn("SD_Rgd5Ammo", re.findall(r'Player\.StartItem\s+"(\w+)"', self.player))

    def test_never_raised_by_itself_and_one_press_one_throw(self):
        for flag in ("+WEAPON.NOAUTOFIRE", "+WEAPON.NO_AUTO_SWITCH", "+WEAPON.NOAUTOSWITCHTO"):
            self.assertIn(flag, self.weapon)
        self.assertGreater(int(p4.default_value(self.weapon, "Weapon.SelectionOrder")), ICE_AXE_SELECTION)
        fire = "\n".join(label_lines(self.weapon, "Fire"))
        self.assertNotIn("A_ReFire", fire)
        self.assertEqual(fire.count("A_SD_ThrowRgd5"), 1)
        self.assertIn("A_CheckReload", fire)       # the last grenade gone, the engine switches away
        self.assertEqual(tics(label_lines(self.weapon, "Fire")), 33)

    def test_the_throw_is_an_arc_with_no_autoaim(self):
        self.assertRegex(self.weapon, r'A_FireProjectile\("SD_Rgd5Grenade",[^;]*FPF_NOAUTOAIM[^;]*loft\)')
        loft = p4.const_value(self.weapon.replace("-", ""), "SD_RGD5_LOFT")
        self.assertIn("const SD_RGD5_LOFT      = -", self.weapon)    # negative is up in GZDoom
        self.assertTrue(5 <= loft <= 20, loft)
        self.assertIn("max(SD_RGD5_LOFT, SD_RGD5_MAX_UP - pitch)", self.weapon)
        self.assertEqual(p4.default_value(self.weapon, "Weapon.AmmoType"), "SD_Rgd5Ammo")

    def test_the_fuse_alone_reaches_the_burst(self):
        g = self.grenade
        self.assertIn("-NOGRAVITY", g)
        self.assertIn('BounceType "Doom"', g)
        self.assertEqual(p4.default_value(g, "Damage"), "0")
        self.assertEqual(p4.state_labels(g), {"Spawn", "Death", "Detonate"})
        for label in ("Spawn", "Death"):
            lines = "\n".join(label_lines(g, label))
            self.assertIn("A_SD_BurnFuse", lines, label)
            self.assertNotIn("A_Explode", lines, label)
            self.assertNotIn("Detonate", lines, label)
        self.assertIn("A_SD_Detonate", "\n".join(label_lines(g, "Detonate")))
        self.assertEqual(len(re.findall(r'SetStateLabel\("Detonate"\)', g)), 1)
        self.assertEqual(len(re.findall(r"\bA_Explode\(", g)), 1)
        self.assertIn("XF_HURTSOURCE", g)          # the risk weapon, as the RPG-7
        fuse = p4.const_value(g, "SD_RGD5_FUSE_TICS") / TICS_PER_SECOND
        self.assertTrue(FUSE_SECONDS[0] <= fuse <= FUSE_SECONDS[1], fuse)

    def test_balance_under_the_rpg7_and_for_groups(self):
        pg7 = body("zscript/weapons/pg7_grenade.zs", "SD_Pg7Grenade")
        pg7_one_target = (p4.const_value(pg7, "SD_PG7_IMPACT_DAMAGE") * PROJECTILE_AVG
                          + p4.const_value(pg7, "SD_PG7_BLAST_DAMAGE"))
        blast = p4.const_value(self.grenade, "SD_RGD5_BLAST_DAMAGE")
        radius = p4.const_value(self.grenade, "SD_RGD5_BLAST_RADIUS")
        self.assertLess(blast, pg7_one_target)                               # below the RPG-7 a unit
        self.assertLessEqual(blast, p4.const_value(pg7, "SD_PG7_BLAST_DAMAGE"))
        self.assertGreater(radius, p4.const_value(pg7, "SD_PG7_BLAST_RADIUS"))   # wider: the group tool
        # Doom's linear falloff: a target dies inside r = R (1 - HP / D).
        for rel, cls, const, at_least in (("reich_rifleman.zs", "SD_ReichRifleman", "SD_RIFLEMAN_HEALTH", 0.75),
                                          ("legion_trooper.zs", "SD_LegionTrooper", "SD_TROOPER_HEALTH", 0.6)):
            hp = p4.const_value(body(f"zscript/monsters/{rel}", cls), const)
            self.assertGreaterEqual(1 - hp / blast, at_least, cls)
        # The three bosses take no splash: a grenade never does a boss's work.
        for rel, cls in (("general.zs", "SD_General"), ("liberty_colossus.zs", "SD_LibertyColossus"),
                         ("consortium.zs", "SD_Consortium")):
            self.assertIn("+NORADIUSDMG", body(f"zscript/monsters/{rel}", cls), cls)
        # Scarce: the pool holds fewer grenades than the RPG-7's crate's worth x 2.
        self.assertLessEqual(p4.const_value(self.ammo, "SD_RGD5_MAX"), 10)
        self.assertEqual(p4.const_value(self.ammo, "SD_RGD5_BACKPACK"), 0)
        self.assertEqual(p4.const_value(self.ammo, "SD_RGD5_BACKPACK_MAX"), 2 * p4.const_value(self.ammo, "SD_RGD5_MAX"))
        self.assertEqual(p4.const_value(self.ammo, "SD_RGD5_LOOSE"), 1)
        self.assertGreater(p4.const_value(self.box, "SD_RGD5_CRATE"), p4.const_value(self.weapon, "SD_RGD5_AMMO_GIVE"))

    def test_a_loose_grenade_gives_the_weapon(self):
        m = re.search(r"override\s+bool\s+TryPickup\s*\(\s*in\s+out\s+Actor\s+toucher\s*\)\s*\{(.*?)\n\t\}", self.ammo, re.S)
        self.assertIsNotNone(m)
        code = m.group(1)
        self.assertLess(code.index("Super.TryPickup"), code.index('Spawn("SD_Rgd5")'))   # the ammo first
        self.assertIn('FindInventory("SD_Rgd5") == null', code)
        self.assertIn("AmmoGive1 = 0", code)
        self.assertIn("CallTryPickup(toucher)", code)
        self.assertIn("Destroy()", code)
        self.assertNotIn("TryPickup", self.box)    # the crate inherits it

    def test_every_frame_has_its_sprite(self):
        for cls, b in (("SD_Rgd5", self.weapon), ("SD_Rgd5Ammo", self.ammo), ("SD_Rgd5Box", self.box),
                       ("SD_Rgd5Grenade", self.grenade)):
            frames = p4.state_frames(b)
            self.assertTrue(frames, cls)
            for sprite, frame in sorted(frames):
                with self.subTest(cls=cls, sprite=sprite, frame=frame):
                    self.assertIn("0", p4.sprite_rotations(sprite).get(frame, set()), f"{sprite}{frame}0")
        icon = p4.default_value(self.ammo, "Inventory.Icon")
        self.assertTrue(list(p4.SPRITES.rglob(f"{icon}.png")), icon)

    def test_provisional_look_and_its_documented_swaps(self):
        for rel, pairs in SWAPS.items():
            with self.subTest(rel=rel):
                text = self.texts[rel]
                marked = p4.provisional_code_lines(text)
                self.assertTrue(marked)
                self.assertTrue(all(l.startswith(("Translation ", "Scale ", "const ")) for l in marked), marked)
                swapped, found = p4.apply_documented_swap(text)
                self.assertEqual(found, pairs)
                code = p4.strip_comments(swapped)
                self.assertNotIn("Translation", code)
                self.assertNotRegex(code, r"\bScale\b")
                sprites = {s for c in p4.class_blocks(swapped).values() for s, _ in p4.state_frames(c[1])}
                finals = {new for _, new in pairs}
                # the PG-7V's burst SDPX stays: it is ours already
                self.assertEqual(sprites - {"SDPX"}, finals)
        for name in FINAL_SPRITES:
            self.assertFalse(p4.sprite_rotations(name), f"{name} is drawn: do the swap")
        # the final names are free: no other class of the mod names them
        others = "\n".join(p.read_text(encoding="utf-8") for p in (SRC / "zscript").rglob("*.zs")
                           if p.relative_to(SRC).as_posix() not in FILES)
        for name in FINAL_SPRITES:
            self.assertNotRegex(others, rf"\b{name}\b")

    def test_sounds(self):
        lines = p4.sndinfo_lines()
        shipped = {p.stem.upper() for p in SOUNDS.rglob("*.ogg")}
        used = set()
        for text in self.texts.values():
            used |= set(re.findall(r'"(sd/weapon/rgd5/[^"]+)"', p4.strip_comments(text)))
        self.assertEqual(used, SOUND_NAMES)
        finals = set()
        for name in sorted(used):
            with self.subTest(name=name):
                lump, comment = lines[name]
                self.assertIn(lump, shipped)
                self.assertIn("REUSED", comment)
                final = p4.FINAL_LUMP_RE.search(comment)
                self.assertIsNotNone(final)
                self.assertTrue(final.group(1).startswith("SDRG"))
                self.assertNotIn(final.group(1), shipped)
                finals.add(final.group(1))
        self.assertEqual(len(finals), len(SOUND_NAMES))
        self.assertEqual(lines["sd/weapon/rgd5/explode"][0], lines["sd/weapon/rpg7/explode"][0])
        pitch = [d for d in p4.sndinfo_directives() if d[:2] == ["$pitchset", "sd/weapon/rgd5/explode"]]
        self.assertEqual(len(pitch), 1)
        self.assertGreater(float(pitch[0][2]), 1.0)     # higher: a smaller crack than the PG-7V's

    def test_strings_in_three_languages(self):
        sections = p4.language_sections()
        used = set()
        for text in self.texts.values():
            used |= set(re.findall(r'"\$(SD_\w+)"', p4.strip_comments(text)))
        self.assertEqual(used, IDS)
        for lang in p4.LANGS:
            with self.subTest(lang=lang):
                self.assertLessEqual(IDS, set(sections[lang]))
        for sid in IDS:
            self.assertTrue(sections["enu default"][sid].isascii(), sid)
            self.assertIn("RGD-5", sections["enu default"][sid])
            self.assertIn("РГД-5", sections["ru"][sid])
            self.assertIn("RGD-5", sections["ca"][sid])
            self.assertNotEqual(sections["ca"][sid], sections["enu default"][sid], sid)
        for lang in p4.LANGS:
            self.assertEqual(re.findall(r"%[ok]", sections[lang]["SD_OB_RGD5"]).count("%o"), 1)
            self.assertEqual(re.findall(r"%[ok]", sections[lang]["SD_OB_RGD5"]).count("%k"), 1)

    def test_placed_only_in_episodes_two_and_three_or_the_range(self):
        for p in (SRC / "maps").rglob("*.py"):
            text = p.read_text(encoding="utf-8")
            if any(re.search(rf"\b{num}\b", text) for num in EDNUMS):
                self.assertIn(p.parent.name, ALLOWED_MAPS, f"{p} places the RGD-5")


class DocTests(unittest.TestCase):
    def test_design_doc(self):
        text = DESIGN.read_text(encoding="utf-8")
        for needle in (*EDNUMS.values(), "SD_Rgd5Grenade", *map(str, EDNUMS), "ADR 012", "D116",
                       "give SD_Rgd5", "summon SD_Rgd5Ammo", *FINAL_SPRITES, "NOT VERIFIED"):
            self.assertIn(needle, text)

    def test_adr(self):
        text = ADR.read_text(encoding="utf-8")
        for needle in ("slot 8", "SD_Rgd5Ammo", "commonbinds.txt", "## Options", "## Decision", "## Consequences"):
            self.assertIn(needle, text)

    def test_gemini_prompts(self):
        text = PROMPTS.read_text(encoding="utf-8")
        for needle in ("#FF00FF", "RGD-5", "gemini_rgd5_A.png", "gemini_rgd5_B.png", "gemini_rgd5_C.png",
                       "gemini_rgd5_D.png", "gemini_rgd5_pickup.png", "work/art/reference/"):
            self.assertIn(needle, text)
        self.assertGreaterEqual(text.count("```text"), 6)

    def test_contracts(self):
        spec = (DOCS / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        for num, cls in EDNUMS.items():
            self.assertRegex(spec, rf"\|\s*{num}\s*\|\s*`{cls}`", f"MOD-SPEC 6.1 lacks {num}")
        for cls in (*EDNUMS.values(), "SD_Rgd5Grenade"):
            self.assertRegex(spec, rf"\|\s*`{cls}`\s*\|", f"MOD-SPEC 6 lacks {cls}")
        self.assertIn("012-rgd5-hand-grenade.md", spec)
        balance = (DOCS / "engine" / "BALANCE.md").read_text(encoding="utf-8")
        for needle in ("RGD-5", "SD_Rgd5Ammo", "| 8 |"):
            self.assertIn(needle, balance)


if __name__ == "__main__":
    unittest.main()
