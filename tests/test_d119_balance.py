"""D119: the CEO's playtest of Episodes 2 and 3 (2026-10-23), in numbers.

(a) "The flamethrower kills every enemy too easily": the ROKS-3's jet goes
    from 4 to 3 x random(1,8), 210 -> 157.5 damage a second, 18 -> 13.5 a
    unit of fuel; the bosses' own flames keep 4.
(b) "You always end up with the shotgun": a Legion trooper's dropped IZh
    carries 2 shells, not the engine's half of 8.
(c) The bosses at classic Doom's level: the Consortium 4000 (the
    Cyberdemon's), the Liberty Colossus 3000 (the Spider Mastermind's).
(d) BALANCE.md section 8 publishes the maps' ammunition rules.

The why is docs/engine/BALANCE.md; this file pins the code and the doc to
each other. No engine is started (D26).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ZS = PROJECT_ROOT / "src" / "zscript"
BALANCE = PROJECT_ROOT / "docs" / "engine" / "BALANCE.md"
TICS_PER_SECOND = 35


def code(rel: str) -> str:
    text = (ZS / rel).read_text(encoding="utf-8")
    return re.sub(r"//[^\n]*", "", text)


def const(rel: str, name: str) -> float:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([-\d.]+)\s*;", code(rel))
    assert m, f"no const {name} in {rel}"
    return float(m.group(1))


def avg_missile(base: float) -> float:
    """Doom's projectile damage: base x random(1,8), average 4.5."""
    return base * 4.5


def avg_hitscan(base: float) -> float:
    """Doom's bullet damage: base x random(1,3), average 2."""
    return base * 2


class RoksThreeTest(unittest.TestCase):
    def setUp(self):
        self.flame = const("weapons/flame_blob.zs", "SD_FLAME_DAMAGE")
        fire = re.search(r"SDRK A (\d+) Bright A_SD_FireRoks3;", code("weapons/roks3.zs"))
        self.assertIsNotNone(fire)
        self.cycle = int(fire.group(1))
        self.dps = avg_missile(self.flame) * TICS_PER_SECOND / self.cycle

    def test_the_jet_is_three_by_d8_every_three_tics(self):
        self.assertEqual(self.flame, 3)
        self.assertEqual(self.cycle, 3, "the jet sound loops in 3 tics (gen_weapon_alts.py)")
        self.assertAlmostEqual(self.dps, 157.5)

    def test_it_sits_between_slot_four_and_doom_s_plasma(self):
        """Over 1.5 x the AKM (slot 4b, 105), under Doom's plasma (262.5)
        and under the RPG-7's direct hits (181.7): strong, not the best."""
        akm = avg_hitscan(const("weapons/akm.zs", "SD_AKM_DAMAGE")) * TICS_PER_SECOND / 4
        rpg = avg_missile(const("weapons/pg7_grenade.zs", "SD_PG7_IMPACT_DAMAGE")) * TICS_PER_SECOND / 26
        self.assertGreaterEqual(self.dps, 1.5 * akm)
        self.assertLess(self.dps, rpg)
        self.assertLess(self.dps, 262.5)

    def test_fuel_is_better_spent_on_the_katyusha(self):
        per_cell = avg_missile(self.flame) / const("weapons/roks3.zs", "SD_ROKS3_AMMO_USE")
        kat = (const("weapons/katyusha.zs", "SD_KATYUSHA_ROCKETS")
               * avg_missile(const("weapons/katyusha_rocket.zs", "SD_KAT_IMPACT_DAMAGE"))
               / const("weapons/katyusha.zs", "SD_KATYUSHA_AMMO_USE"))
        self.assertAlmostEqual(per_cell, 13.5)
        self.assertLess(per_cell, kat)

    def test_the_bosses_flames_keep_their_damage(self):
        for rel, cls in (("monsters/colossus_flame.zs", "SD_ColossusFlame"),
                         ("monsters/consortium_flame.zs", "SD_ConsortiumFlame")):
            with self.subTest(cls):
                self.assertEqual(const(rel, "SD_BOSS_FLAME_DAMAGE"), 4)
                self.assertRegex(code(rel), r"\bDamage\s+SD_BOSS_FLAME_DAMAGE\s*;")


class IzhDropTest(unittest.TestCase):
    def test_a_dropped_izh_carries_two_shells(self):
        body = code("weapons/izh.zs")
        self.assertEqual(const("weapons/izh.zs", "SD_IZH_DROPPED_SHELLS"), 2)
        self.assertEqual(const("weapons/izh.zs", "SD_IZH_AMMO_GIVE"), 8, "a placed IZh still gives 8")
        m = re.search(r"override\s+void\s+ModifyDropAmount\s*\(\s*int\s+\w+\s*\)\s*\{(.*?)\}", body, re.S)
        self.assertIsNotNone(m, "SD_Izh must override ModifyDropAmount")
        self.assertIn("Super.ModifyDropAmount", m.group(1), "keep the engine's halving and skill rule")
        self.assertRegex(m.group(1), r"AmmoGive1\s*=\s*min\(\s*AmmoGive1\s*,\s*SD_IZH_DROPPED_SHELLS\s*\)")

    def test_the_trooper_still_drops_the_izh(self):
        self.assertRegex(code("monsters/legion_trooper.zs"), r'DropItem\s+"SD_Izh"\s*;')

    def test_the_izh_stays_under_slot_four(self):
        """Sustained, the IZh is still slot 3: under the PPSh-41."""
        barrel = 8 * avg_hitscan(5)   # SD_IZH_PELLETS x SD_IZH_DAMAGE
        sustained = 2 * barrel * TICS_PER_SECOND / (2 * 23 + 30)
        ppsh = avg_hitscan(const("weapons/ppsh.zs", "SD_PPSH_DAMAGE")) * TICS_PER_SECOND / 3
        self.assertEqual(const("weapons/izh.zs", "SD_IZH_PELLETS"), 8)
        self.assertLess(sustained, ppsh)


class BossHealthTest(unittest.TestCase):
    def test_classic_doom_hit_points(self):
        self.assertEqual(const("monsters/consortium.zs", "SD_CONSORTIUM_HEALTH"), 4000)   # Cyberdemon
        self.assertEqual(const("monsters/liberty_colossus.zs", "SD_COLOSSUS_HEALTH"), 3000)  # Mastermind
        self.assertEqual(const("monsters/general.zs", "SD_GENERAL_HEALTH"), 3000)

    def test_two_phases_and_the_wounded_fixture(self):
        health = const("monsters/consortium.zs", "SD_CONSORTIUM_HEALTH")
        fraction = const("monsters/consortium.zs", "SD_CONSORTIUM_BREACH_FRACTION")
        margin = const("monsters/consortium_wounded.zs", "SD_WOUNDED_MARGIN")
        self.assertEqual(fraction, 0.5)
        self.assertEqual(margin, 100)
        self.assertEqual(int(health * fraction) + margin, 2100)


class BalanceDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = BALANCE.read_text(encoding="utf-8")

    def test_the_ammunition_rules_are_published(self):
        self.assertIn("## 8. Ammunition in the maps (D119)", self.text)
        for band in ("1.5–2.0", "1.3–1.6", "1.2–1.45", "35 %"):
            self.assertIn(band, self.text)

    def test_the_new_numbers_are_in_the_tables(self):
        self.assertIn("| 6 | ROKS-3 flamethrower | 1 Cell | 13.5 (3–24) | 3 | 11.67 | 157.5 |", self.text)
        self.assertIn("| Liberty Colossus (P4, D116; D119) | 3000 |", self.text)
        self.assertIn("| The Consortium (P4, D116; D119), whole | 4000 |", self.text)


if __name__ == "__main__":
    unittest.main()
