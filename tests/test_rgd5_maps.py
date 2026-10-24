"""The RGD-5 in the maps (V3 A4, ADR 012): where the grenades lie, and how many.

The placement advice is docs/engine/2026-10-23_V3_rgd5.md section 6; the
budget is docs/engine/BALANCE.md section 8 (a grenade counts 1.25
shell-equivalents in the band; each map's own test counts it). Pinned here,
on the maps as their sources build them (no engine, D26):

  * grenades in MAP01-MAP09 and the range (Episode 1 since 2026-10-24;
    test_rgd5.py pins the sources; this pins the built things);
  * per map and skill, the advice's count: 4 / 3 / 2, 3 / 3 / 2 and 3 / 2 / 2
    grenades on skills 2 / 3 / 4, each on the route, in the zones the advice
    (or, for Episode 1, its map's design document, "V3") names, scaling DOWN
    with skill like every consumable;
  * the first pouch where a pistol start needs it: MAP01 (the lesson),
    MAP02, MAP03, MAP04 and MAP07;
  * none in a boss's arena (the bosses take no splash: MAP03's General,
    MAP06's colossus, MAP09's Consortium), no crate in the campaign (a
    secret's reward only, and no map has one yet);
  * the range holds the pouch and the crate on every skill: the pool's full
    six, to throw at the barrels.

Run:  python3 -m unittest tests.test_rgd5_maps -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import route  # noqa: E402
from test_bestiary import zs_constants  # noqa: E402

ZS = PROJECT_ROOT / "src" / "zscript" / "weapons"
POUCH, LOOSE, CRATE = 21009, 21021, 21022
SKILLS = (2, 3, 4)


def _consts(name: str) -> dict[str, float]:
    return zs_constants((ZS / name).read_text(encoding="utf-8"))


GIVES = {POUCH: int(_consts("rgd5.zs")["SD_RGD5_AMMO_GIVE"]),
         LOOSE: int(_consts("rgd5_ammo.zs")["SD_RGD5_LOOSE"]),
         CRATE: int(_consts("rgd5_ammo.zs")["SD_RGD5_CRATE"])}
POOL_MAX = int(_consts("rgd5_ammo.zs")["SD_RGD5_MAX"])

# docs/engine/2026-10-23_V3_rgd5.md section 6, as built: grenades on skills
# 2 / 3 / 4, and the zones they lie in.
ADVICE = {
    # Episode 1 (2026-10-24), each map's design document, "V3": the pouch
    # first, loose ones after.
    "MAP01": ((4, 3, 2), {"z4_komnata", "z6_hangar", "z6b_catwalk"}),
    "MAP02": ((3, 3, 2), {"z2_kassa", "b2_spine"}),
    "MAP03": ((4, 3, 2), {"z2_dock", "t_line", "f_gallery"}),
    "MAP04": ((4, 3, 2), {"z1_tunnel", "z2_yard", "z4_hall"}),
    "MAP05": ((3, 3, 2), {"z4_gallery", "z5_catwalk"}),
    "MAP06": ((4, 3, 2), {"z3_street"}),
    "MAP07": ((4, 3, 2), {"z2_hangar", "z4_barracks"}),
    "MAP08": ((3, 2, 2), {"z2_yard"}),
    "MAP09": ((3, 2, 2), {"z3_izba_a", "z3_izba_b", "z3_yard"}),
}
# Where the advice puts the first grenade a pistol start needs: the pouch.
POUCH_FIRST = {"MAP01": "z4_komnata", "MAP02": "z2_kassa", "MAP03": "z2_dock",
               "MAP04": "z1_tunnel", "MAP07": "z2_hangar"}
# The bosses' maps: (the boss's spot constant, its arena's zone prefix).
BOSS_ARENAS = {"MAP06": ("MAP06_BOSS_SPOT", "z9_"), "MAP09": ("MAP09_BOSS_SPOT", "z8_")}
# MAP03 names no spot constant: the General is the "general" row of its
# MONSTERS, and the portal hall's zones are p_* (the antechamber, the booth,
# the drum, the stores).
GENERAL_ARENA = ("MAP03", "general", "p_")


def grenades(md, skill: int) -> list:
    return [t for t in md.textmap.things if t.type in GIVES and getattr(t, f"skill{skill}")]


class CampaignTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {name: route.load_map_data(name) for name in ADVICE}

    def zone(self, md, t) -> str | None:
        return md.name_of(md.sector_at(t.x, t.y))

    def test_the_advices_count_per_skill(self):
        for name, (counts, _zones) in ADVICE.items():
            md = self.maps[name]
            found = tuple(sum(GIVES[t.type] for t in grenades(md, s)) for s in SKILLS)
            self.assertEqual(counts, found, name)

    def test_in_the_advices_zones_on_the_route(self):
        for name, (_counts, zones) in ADVICE.items():
            md = self.maps[name]
            secrets = set(md.secret_sectors())
            for t in grenades(md, 2):
                self.assertIn(self.zone(md, t), zones, f"{name}: {t.type} at ({t.x}, {t.y})")
                self.assertNotIn(md.sector_at(t.x, t.y), secrets, name)

    def test_the_pouch_where_a_pistol_start_needs_it(self):
        for name, zone in POUCH_FIRST.items():
            md = self.maps[name]
            pouches = [t for t in md.textmap.things if t.type == POUCH]
            self.assertEqual(1, len(pouches), name)
            self.assertEqual(zone, self.zone(md, pouches[0]), name)
            self.assertTrue(all(getattr(pouches[0], f"skill{n}") for n in range(1, 6)), name)

    def test_never_in_a_bosss_arena(self):
        for name, (spot_name, prefix) in BOSS_ARENAS.items():
            md = self.maps[name]
            spot = getattr(md.module, spot_name)
            self.assertTrue(md.name_of(md.sector_at(*spot)).startswith(prefix), "the arena's prefix")
            for t in md.textmap.things:
                if t.type in GIVES:
                    self.assertFalse(self.zone(md, t).startswith(prefix), f"{name}: ({t.x}, {t.y})")

    def test_never_in_the_generals_portal_hall(self):
        name, kind, prefix = GENERAL_ARENA
        md = self.maps[name]
        rows = [row for row in md.module.MONSTERS if row[1] == kind]
        self.assertEqual(1, len(rows), "one General")
        self.assertTrue(md.name_of(md.sector_at(rows[0][2], rows[0][3])).startswith(prefix))
        for t in md.textmap.things:
            if t.type in GIVES:
                self.assertFalse(self.zone(md, t).startswith(prefix), f"{name}: ({t.x}, {t.y})")

    def test_the_pouch_comes_before_any_loose_grenade_in_episode_1(self):
        """A pistol start meets the weapon first: in each Episode 1 map's
        ITEMS the pouch is the first RGD-5 row, the loose ones after it."""
        for name in ("MAP01", "MAP02", "MAP03"):
            rows = [row[1] for row in self.maps[name].module.ITEMS if row[1] in GIVES]
            self.assertEqual(POUCH, rows[0], name)
            self.assertEqual(1, rows.count(POUCH), name)

    def test_no_crate_in_the_campaign(self):
        for name, md in self.maps.items():
            self.assertFalse([t for t in md.textmap.things if t.type == CRATE], name)


class RangeTest(unittest.TestCase):
    def test_the_pouch_and_the_crate_on_every_skill_the_pools_six(self):
        md = route.load_map_data("RANGE")
        for skill in range(1, 6):
            here = [t for t in md.textmap.things if t.type in GIVES and getattr(t, f"skill{skill}")]
            self.assertEqual({POUCH, CRATE}, {t.type for t in here}, skill)
            self.assertEqual(POOL_MAX, sum(GIVES[t.type] for t in here), skill)


if __name__ == "__main__":
    unittest.main()
