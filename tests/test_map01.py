"""MAP01 v3: density, combat and resources (design document section 17).

Owner: `level-designer`. `tests/test_udmf.py` holds the builder's tests and
the v0-v2 contract of the map (connectivity, gate order, light, sight
lines); this file holds what v3 added, read back from the generated TEXTMAP
rather than from the tables in `map.py`, so a typo in a table or a thing
dropped into a wall shows up here:

* the density target (D33): sector and line counts;
* every thing stands in the zone the table says, with room for its body;
* monsters per skill (design section 8), strictly increasing, Reich first
  and the Legion in the hangar (D35);
* the tutorial weapons on every skill, the RPG-7 only in S2;
* consumables scale down with skill, ammunition scales up with it (D119),
  and every skill's ammo budget inside its G3-8 band, shells no more than
  35 % of it;
* the monster closets: tagged with their switch, reachable, escapable;
* the three re-hidden secrets, and Lenin's light;
* D38: the cosmonautics mural seen whole from the komnata's doorway and
  centre;
* G3 readiness (design section 18): per skill 2, 3 and 4, the exit reached
  pressing only what the map offers, the tutorial weapons before the
  switches, the ice axe (the shovel until D40) before the first melee, and
  ammunition against hit points with BALANCE section 7;
* D43: the diegetic radio in the guard post (design section 17.16): on
  every skill, its zone kept to the post and the corridor in front of it,
  every lane past it at least 40 wide, and clear of every route step.

Run:  python3 -m unittest tests.test_map01 -v
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "tests"))

# Imported as a module, not by name: a TestCase class bound in this module's
# namespace would be collected and run a second time from here.
import _pickup_events as pe  # noqa: E402  (V3 A2's shared checks)
import route  # noqa: E402  (QA's tools/route.py: its steps, read not run)
import test_udmf as udmf_tests  # noqa: E402

# docs/levels/PICKUP-EVENTS.md R5 uses tests/test_safe_starts.py's distance.
SAFE_START_DISTANCE = 768

MAX_STEP_UP = udmf_tests.MAX_STEP_UP
_load_map01 = udmf_tests._load_map01
parse_textmap = udmf_tests.parse_textmap

# Bodies, from docs/engine/BESTIARY.md section 1 (read from gzdoom.pk3): the
# radius and height each stand-in needs to stand where it is put.
BODY = {3004: (20, 56), 9: (20, 56), 3001: (20, 56), 3002: (30, 56),
        3005: (31, 56), 69: (24, 64)}
PICKUP_RADIUS = 20   # Doom's pickups are 20 wide; they need no headroom
DRUM_RADIUS = 10     # barrel
LAMP_RADIUS = 16     # floor lamp

# What it takes to kill each stand-in with the weapon the map teaches for
# it, in IZh shells - criterion G3-8's own figures (design section 11):
# rifleman / trooper 1, stormtrooper 2, hound 3. v3 adds the two heavies of
# D35 at the same margin: a Doughboy has 400 HP (5 average barrels: 6), a
# Panzermensch 500 (6.25: 8).
SHELLS_TO_KILL = {3004: 1, 9: 1, 3001: 2, 3002: 3, 3005: 6, 69: 8}
G3_8_MARGIN = 1.35
# D119 (docs/engine/BALANCE.md): placed ammunition over what killing every
# monster takes, a band per skill instead of one floor, and shells no more
# than SHELL_SHARE_MAX of the damage placed. The stage-by-stage check holds
# every skill to its band's floor.
G3_8_BAND = {2: (1.5, 2.0), 3: (1.3, 1.6), 4: (1.2, 1.45)}
SHELL_SHARE_MAX = 0.35
NEWEST_SHARE_MIN = 0.4    # BALANCE 8.4
# D119's shell share (BALANCE 8.3): (placed shells + what the Legion's
# dropped IZhs carry) over (placed shell-equivalents + every drop), drops in
# shell-equivalents: a trooper's IZh 2 shells, a rifleman's clip 5 rounds.
DROP_SHELLS = 2
DROP_ROUNDS = 5
# The ammunition pickups v3 placed outside the secrets, per skill: D119
# takes objects away, not only rounds, so no skill may have more.
V3_AMMO_PICKUPS = {2: 25, 3: 21, 4: 19}
# D119's stretches along the weapons, by the zones of the tables: the TT-33
# alone up to the guard post, the IZh the newest weapon up to the catwalk,
# the PPSh-41 from there to the exit (design section 4).
MAP01_STRETCHES = (
    ("the TT-33", {"z1_dorm", "z2_washroom", "z3_corridor", "z3_alcove", "z4_komnata",
                   "tribune"}),
    ("the IZh", {"z5_service", "z5b_guard", "z5_flicker", "z6_hangar", "z6a_cradle",
                 "lane_a_cross", "cradle_spine", "gantry", "z7_fuel_bay", "weapon_rack",
                 "closet_a1", "closet_a2", "closet_a3", "closet_izh"}),
    ("the PPSh-41", {"z6b_catwalk", "z9_booth", "closet_w1", "closet_w2", "closet_e1",
                     "closet_ppsh", "z8_airlock", "z10_lift", "z10_exit"}),
)
# Ammo is counted in shell-equivalents: an IZh barrel averages 80 damage, a
# PPSh round 8 (docs/engine/BALANCE.md section 2), so ten rounds of 7.62 do
# the work of one shell.
ROUNDS_PER_SHELL = 10
# What each pickup gives, Doom's amounts (our classes keep them, MOD-SPEC
# 6.4) and the weapon AmmoGive constants in src/zscript/weapons/.
SHELLS_GIVEN = {2008: 4, 2049: 20, 21003: 8}
ROUNDS_GIVEN = {2007: 10, 2048: 50, 21004: 35}

SKILLS = (2, 3, 4)
MONSTER_NUMBERS = set(BODY)
VIEW_HEIGHT = udmf_tests.VIEW_HEIGHT
PLAYER_RADIUS = 16
# The diegetic radio (D43): SD_RADIO_RADIUS in radio.zs, read back by
# test_the_radio_is_the_class_mod_spec_describes; solid, like the fixtures.
ED_RADIO = 21200
RADIO_RADIUS = 16
SOLID_FIXTURE_RADIUS = {2035: DRUM_RADIUS, 2028: LAMP_RADIUS, ED_RADIO: RADIO_RADIUS}
# G3-F1: a lane the player must walk to a pickup is at least a body plus
# ROOM_TO_SPARE on each side (40 for 32), so it is walked, not threaded.
# Checked on a LANE_GRID raster; both must divide the map's 16-unit grid.
ROOM_TO_SPARE = 4
LANE_GRID = 4

# The 32-deep mural niche hides ~3 of the mural's 128 units from the
# doorway's corner; the sight test samples from this far in from each edge.
MURAL_JAMB_INSET = 4

# docs/engine/BALANCE.md section 7, the ruler G3 is read against: hit points
# per stand-in (each the HP of the bestiary class that replaces it,
# BESTIARY.md section 12) and the average damage per shot of the weapons
# MAP01 teaches (section 2).
HIT_POINTS = {3004: 20, 9: 30, 3001: 60, 3002: 150, 3005: 400, 69: 500}
IZH_AVERAGE = 80       # one barrel, 8 pellets of 5 x random(1,3)
PPSH_AVERAGE = 8       # one round, 4 x random(1,3)
TT33_AVERAGE = 12      # one round, 6 x random(1,3)
# Read, not owned: the player's starting rounds and the mod's skill rungs.
PLAYER_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "player.zs"
RADIO_ZS = PROJECT_ROOT / "src" / "zscript" / "sd" / "radio.zs"
MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
# What GZDoom's SpawnFilter names mean: the thing flag each rung spawns by.
SPAWN_FILTER_FLAG = {"baby": 1, "easy": 2, "normal": 3, "hard": 4, "nightmare": 5}
# The only line specials MAP01 may use: nothing locked, nothing scripted.
ALLOWED_SPECIALS = {udmf_tests.SPECIAL_DOOR_OPEN, udmf_tests.SPECIAL_DOOR_RAISE,
                    udmf_tests.SPECIAL_EXIT_NORMAL}
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys
# D43, the diegetic radio (design section 17.16). The guard post with its
# rack, where the radio stands; and the service corridor the post opens
# onto, with the sectors painted into it (its pipe runs, its lamp, the
# failing lamp): one room for the player, five sectors for the builder.
RADIO_POST = ("z5b_guard", "weapon_rack")
RADIO_CORRIDOR = ("z5_service", "z5_flicker", "pipes_1", "pipes_2", "lamp_z5_service_1")
# Sample spacing for the radio's zones, in map units.
RADIO_GRID = LANE_GRID


class Map01V3Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.m = _load_map01()
        textmap, cls.plan = cls.m.build_plan()
        cls.blocks = parse_textmap(textmap.render())
        cls.sectors = cls.blocks["sector"]
        cls.lines = cls.blocks["linedef"]
        cls.sides = cls.blocks["sidedef"]
        cls.verts = cls.blocks["vertex"]
        cls.things = cls.blocks["thing"]
        cls.zone_of = {i: name for name, i in cls.plan.items()}
        # Vertical lines only: a ray cast east crosses nothing else in a map
        # made of axis-aligned rectangles.
        cls.vertical = []
        for ld in cls.lines:
            a, b = cls.verts[ld["v1"]], cls.verts[ld["v2"]]
            if a["x"] == b["x"]:
                cls.vertical.append((a["x"], a["y"], b["y"], ld))
        # The v0-v2 reachability model, reused: every door open.
        model_class = udmf_tests.Map01Test
        model_class.setUpClass()
        model = model_class()
        cls.model = model
        cls.reachable, cls.adjacency = model._reachable(set(model_class.doors))
        props = {i for name, i in cls.plan.items()
                 if name in cls.m.WINDOWS or name.startswith(cls.m.PROP_PREFIXES)}
        cls.unwalkable = props | model_class.door_sectors

    # --- helpers ----------------------------------------------------------
    def sector_at(self, x, y):
        """The sector containing (x, y), found the way the engine does it:
        the nearest line east of the point, and which side of it we are on."""
        y = y + 0.25            # never exactly on a horizontal edge
        best = None
        for lx, y1, y2, ld in self.vertical:
            if lx <= x or not (min(y1, y2) < y < max(y1, y2)):
                continue
            if best is None or lx < best[0]:
                best = (lx, y1, y2, ld)
        if best is None:
            return None
        _, y1, y2, ld = best
        # Front is the right-hand side of v1 -> v2; running south, that is
        # west - where the point is.
        if y2 < y1:
            return self.sides[ld["sidefront"]]["sector"]
        return self.sides[ld["sideback"]]["sector"] if "sideback" in ld else None

    def things_of(self, numbers):
        return [t for t in self.things if t["type"] in numbers]

    def on(self, skill, things):
        return [t for t in things if t[f"skill{skill}"]]

    # --- D33: density ---------------------------------------------------
    def test_density_is_that_of_a_first_map(self):
        """The CEO's v2 verdict, as numbers (design section 17): Freedoom's
        MAP01 has 211 sectors and 1274 lines on 8.2 Mu2, ours had 80 and
        322 on 6.5. The target band, and why lines fall short of 1274 by
        design, are argued in section 17."""
        self.assertGreaterEqual(len(self.sectors), self.m.DENSITY_SECTORS_MIN)
        self.assertLessEqual(len(self.sectors), self.m.DENSITY_SECTORS_MAX)
        self.assertGreaterEqual(len(self.lines), self.m.DENSITY_LINES_MIN)

    # --- placement --------------------------------------------------------
    def test_every_thing_stands_in_the_zone_its_table_names(self):
        rows = ([(z, k, x, y) for z, k, x, y, *_ in self.m.MONSTERS]
                + [(z, e, x, y) for z, e, x, y, _ in self.m.ITEMS + self.m.AMMO]
                + list(self.m.FIXTURES)
                + [(z, "radio", x, y) for z, _p, _r, x, y, _a in self.m.RADIOS])
        for zone, what, x, y in rows:
            self.assertEqual(self.plan[zone], self.sector_at(x, y),
                             f"{what} at ({x}, {y}) is not in {zone} but in "
                             f"{self.zone_of.get(self.sector_at(x, y))}")

    def test_every_monster_has_room_for_its_body(self):
        """All four corners of the body's box on floor it can stand on (not
        a prop, a door or the void), within a step of each other, and the
        lowest ceiling over them at least the body's height above."""
        for t in self.things_of(MONSTER_NUMBERS):
            radius, height = BODY[t["type"]]
            x, y = t["x"], t["y"]
            under = {self.sector_at(x + dx, y + dy)
                     for dx in (-radius, radius) for dy in (-radius, radius)}
            under.add(self.sector_at(x, y))
            where = f"{t['type']} at ({x}, {y})"
            self.assertNotIn(None, under, f"{where} is in a wall")
            self.assertFalse(under & self.unwalkable,
                             f"{where} overlaps {[self.zone_of[s] for s in under & self.unwalkable]}")
            floors = [self.sectors[s]["heightfloor"] for s in under]
            ceils = [self.sectors[s]["heightceiling"] for s in under]
            self.assertLessEqual(max(floors) - min(floors), MAX_STEP_UP, where)
            self.assertGreaterEqual(min(ceils) - max(floors), height, where)

    def test_every_pickup_can_be_picked_up(self):
        """A pickup lies on walkable floor the player can reach, never on a
        crate (the player's body would not reach its height)."""
        for t in self.things:
            if t["type"] in MONSTER_NUMBERS or t["type"] == self.m.ED_PLAYER1_START:
                continue
            s = self.sector_at(t["x"], t["y"])
            self.assertIsNotNone(s, f"thing {t['type']} at ({t['x']}, {t['y']}) is in a wall")
            self.assertNotIn(s, self.unwalkable, f"thing {t['type']} on {self.zone_of[s]}")
            self.assertIn(s, self.reachable, f"thing {t['type']} in {self.zone_of[s]}")

    def test_no_thing_is_on_no_skill(self):
        for t in self.things:
            self.assertTrue(any(t[f"skill{n}"] for n in range(1, 6)), t)

    def test_skill_flags_come_in_doom_pairs(self):
        """Doom's skills 1-2 and 4-5 share their spawn flags; a thing set for
        one member of a pair and not the other is a typo."""
        for t in self.things:
            self.assertEqual(t["skill1"], t["skill2"], t)
            self.assertEqual(t["skill4"], t["skill5"], t)

    # --- monsters (design section 8) -------------------------------------
    def test_monsters_per_skill(self):
        monsters = self.things_of(MONSTER_NUMBERS)
        counts = {s: len(self.on(s, monsters)) for s in SKILLS}
        self.assertEqual(self.m.ENEMY_TOTALS, counts)
        self.assertLess(counts[2], counts[3])
        self.assertLess(counts[3], counts[4])

    def test_monsters_scale_up(self):
        """Monsters are nested: whatever fights on an easier skill also fights
        on a harder one (consumables do the opposite, below)."""
        for t in self.things_of(MONSTER_NUMBERS):
            if t["skill2"]:
                self.assertTrue(t["skill3"] and t["skill4"], t)
            if t["skill3"]:
                self.assertTrue(t["skill4"], t)

    def test_the_reich_is_met_first_and_the_legion_holds_the_hangar(self):
        """D35. Before the hangar - dorm to service corridor - only the
        Fourth Reich and the hybrid stormtroopers; the Legion's troopers and
        Doughboy first appear in the hangar."""
        m = self.m
        barracks = ("z1_", "z2_", "z3_", "z4_", "z5_", "z5b_")
        legion = {m.MONSTER_KINDS[k] for k in m.LEGION}
        early = [(z, k) for z, k, *_ in m.MONSTERS if z.startswith(barracks)]
        self.assertTrue(early)
        self.assertFalse([e for e in early if m.MONSTER_KINDS[e[1]] in legion], early)
        hangar = [k for z, k, *_ in m.MONSTERS if not z.startswith(barracks)]
        self.assertIn("trooper", hangar)

    def test_heavies_are_rare_and_never_on_easy(self):
        """D35: the Panzermensch stands in for 500 HP, so its stand-in is the
        Hell Knight (69), never the Baron (3003); one Doughboy and one
        Panzermensch at most, neither on skill 2."""
        heavy = self.things_of({3005, 69})
        self.assertEqual({3005, 69}, {t["type"] for t in heavy})
        self.assertFalse(self.things_of({3003, 65, 16, 7, 64}), "a monster with no bestiary class")
        for t in heavy:
            self.assertFalse(t["skill2"], t)
        self.assertEqual(Counter({3005: 1, 69: 1}), Counter(t["type"] for t in heavy))

    def test_every_closet_holds_a_fight_and_opens_with_its_switch(self):
        """The ambush rides SW-A's tag (D4's), wave 2 SW-B's (D5's): every
        closet panel carries one of those tags, and there is something in
        every closet on every skill."""
        m = self.m
        closets = [n for n in self.plan if n.startswith("closet_") and not n.endswith("_door")]
        self.assertEqual(6 + len(m.EVENT_CLOSETS), len(closets))
        for name in closets:
            tag = self.sectors[self.plan[f"{name}_door"]]["id"]
            if name in m.EVENT_CLOSETS:       # V3 A2: its weapon's pickup opens it
                wanted = m.EVENT_CLOSETS[name][0].tag
            elif name.startswith("closet_a"):
                wanted = m.TAG_FUEL_BAY_AMBUSH
            else:
                wanted = m.TAG_HANGAR_WAVE_2
            self.assertEqual(wanted, tag, name)
            inside = [t for t in self.on(2, self.things_of(MONSTER_NUMBERS))
                      if self.sector_at(t["x"], t["y"]) == self.plan[name]]
            self.assertTrue(inside, f"{name} is empty on skill 2")
        self.assertEqual(m.TAG_D4_HANGAR_AIRLOCK, m.TAG_FUEL_BAY_AMBUSH)
        self.assertEqual(m.TAG_D5_AIRLOCK_EXIT, m.TAG_HANGAR_WAVE_2)

    # --- weapons and resources ------------------------------------------
    def test_the_tutorial_weapons_are_on_every_skill_on_the_route(self):
        """Section 2: ice axe, IZh and PPSh, in that order along the route,
        on every skill and never in a secret; the RPG-7 only in S2."""
        m = self.m
        secret = {i for i, s in enumerate(self.sectors) if s.get("special", 0) & 1024}
        for ednum, zone in ((m.ED_ICE_AXE, "z1_ice_axe_rack"), (m.ED_IZH, "weapon_rack"),
                            (m.ED_PPSH, "z6b_catwalk")):
            found = self.things_of({ednum})
            self.assertEqual(1, len(found), ednum)
            t = found[0]
            self.assertTrue(all(t[f"skill{n}"] for n in range(1, 6)), ednum)
            self.assertEqual(self.plan[zone], self.sector_at(t["x"], t["y"]))
            self.assertNotIn(self.plan[zone], secret)
        rpg = self.things_of({m.ED_RPG7})
        self.assertEqual(1, len(rpg))
        self.assertEqual(self.plan["s2_closet"], self.sector_at(rpg[0]["x"], rpg[0]["y"]))
        # No Doom weapon number sneaks in: the arsenal is ours (D13), and
        # 2005/82 spawn nothing (MAPINFO DoomEdNums).
        self.assertFalse(self.things_of({2001, 2002, 2003, 2004, 2005, 2006, 82}))

    def _secret_sectors(self):
        return {i for i, s in enumerate(self.sectors) if s.get("special", 0) & 1024}

    def _outside_secrets(self, things):
        secret = self._secret_sectors()
        return [t for t in things if self.sector_at(t["x"], t["y"]) not in secret]

    def test_consumables_scale_down(self):
        """Section 8's principle: monsters up, consumables down, weapons
        flat. For every kind of consumable, skill 2 has at least what skill
        3 has, and skill 3 at least what skill 4 has."""
        m = self.m
        weapons = {m.ED_ICE_AXE, m.ED_IZH, m.ED_PPSH, m.ED_RPG7}
        consumables = {t["type"] for t in self.things} - MONSTER_NUMBERS - weapons - {
            m.ED_PLAYER1_START, m.ED_BARREL, m.ED_FLOOR_LAMP, m.ED_RADIO} - self._ammo_kinds()
        for kind in consumables:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

    def _ammo_kinds(self):
        """The ammunition pickups (not the weapons that also give some)."""
        m = self.m
        return (set(SHELLS_GIVEN) | set(ROUNDS_GIVEN)) - {m.ED_IZH, m.ED_PPSH}

    def test_ammunition_scales_up_and_there_is_less_of_it(self):
        """D119: ammunition rides with the monsters - for every kind, on the
        route, skill 2 has at most what skill 3 has and skill 3 at most what
        skill 4 has - and every skill has fewer ammunition pickups than v3
        placed (objects taken away, not only rounds)."""
        route = self._outside_secrets(self.things)
        for kind in self._ammo_kinds():
            n = {s: len(self.on(s, [t for t in route if t["type"] == kind])) for s in SKILLS}
            self.assertLessEqual(n[2], n[3], kind)
            self.assertLessEqual(n[3], n[4], kind)
        for skill in SKILLS:
            n = len([t for t in self.on(skill, route) if t["type"] in self._ammo_kinds()])
            self.assertLess(n, V3_AMMO_PICKUPS[skill], f"skill {skill}")

    def _ammo_needed(self, skill):
        return sum(SHELLS_TO_KILL[t["type"]] for t in self.on(skill, self.things_of(MONSTER_NUMBERS)))

    def _ammo_placed(self, skill):
        """Shell-equivalents placed for `skill`, no secret counted, no drop
        counted (criterion G3-8 counts placed ammunition only)."""
        placed = self._outside_secrets(self.on(skill, self.things))
        shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed)
        rounds = sum(ROUNDS_GIVEN.get(t["type"], 0) for t in placed)
        return shells + rounds / ROUNDS_PER_SHELL

    def test_g3_8_the_ammo_budget(self):
        """Criterion G3-8 as D119 reads it: on every skill, placed ammo
        outside the secrets is inside that skill's band of what killing
        every monster with the intended weapon takes (what the stand-ins
        drop still comes on top, design section 8), and shells are no more
        than 35 % of it, the troopers' dropped IZhs counted (BALANCE 8.3)."""
        for skill in SKILLS:
            need, have = self._ammo_needed(skill), self._ammo_placed(skill)
            low, high = G3_8_BAND[skill]
            self.assertGreaterEqual(have, low * need,
                                    f"skill {skill}: {have} shell-eq for {need} needed")
            self.assertLessEqual(have, high * need,
                                 f"skill {skill}: {have} shell-eq for {need} needed")
            placed = self._outside_secrets(self.on(skill, self.things))
            shells = sum(SHELLS_GIVEN.get(t["type"], 0) for t in placed)
            monsters = Counter(t["type"] for t in self.on(skill, self.things_of(MONSTER_NUMBERS)))
            m = self.m
            troopers, riflemen = monsters[m.MONSTER_KINDS["trooper"]], monsters[m.MONSTER_KINDS["rifleman"]]
            dropped = troopers * DROP_SHELLS + riflemen * DROP_ROUNDS / ROUNDS_PER_SHELL
            self.assertLessEqual(shells + troopers * DROP_SHELLS, SHELL_SHARE_MAX * (have + dropped),
                                 f"skill {skill}: {shells} shells placed")

    def test_health_and_armour_exist_outside_the_secrets_on_skill_4(self):
        """G3-5's other half: the skill-4 player who finds no secret must be
        able to heal on the way."""
        m = self.m
        found = Counter(t["type"] for t in self._outside_secrets(self.on(4, self.things)))
        self.assertGreaterEqual(found[m.ED_STIMPACK] + found[m.ED_MEDIKIT], 5)
        self.assertGreaterEqual(found[m.ED_ARMOR_BONUS], 6)

    # --- secrets (v2 walk: "era muy evidente") ---------------------------
    def test_every_secret_is_reachable_and_left_again(self):
        m = self.m
        secrets = self._secret_sectors()
        self.assertEqual({self.plan["s1_locker"], self.plan["s2_closet"],
                          self.plan["s3_sump"]}, secrets)
        back = defaultdict(set)
        for src, dsts in self.adjacency.items():
            for dst in dsts:
                back[dst].add(src)
        start = self.plan["z1_dorm"]
        for s in secrets:
            self.assertIn(s, self.reachable, self.zone_of[s])
            seen, stack = {start}, [start]
            while stack:
                for nxt in back[stack.pop()]:
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            self.assertIn(s, seen, f"no way back from {self.zone_of[s]}")
        self.assertEqual(3, len({m.TAG_S1_LOCKER_PANEL, m.TAG_S2_CATWALK_PANEL,
                                 m.TAG_S3_SUMP_PANEL}))

    def _texture_on(self, x, y1, y2):
        """The middle textures of the one-sided lines on x between y1, y2."""
        out = set()
        for lx, a, b, ld in self.vertical:
            if lx == x and y1 <= min(a, b) and max(a, b) <= y2:
                side = self.sides[ld["sidefront"]]
                out.add(side["texturemiddle"] if "sideback" not in ld else side["texturetop"])
        return out

    def test_s1_is_one_steel_back_wall_among_concrete_ones(self):
        """The clue is a comparison: of the three stalls, the middle one's
        back wall is plate (the panel), the other two are concrete. And the
        stall in front of the panel is lit like its neighbours - v2's darker
        sector is gone."""
        m = self.m
        self.assertEqual({m.CONC}, self._texture_on(960, 0, 48))
        self.assertEqual({m.CONC}, self._texture_on(960, 144, 192))
        self.assertEqual({m.STEEL}, self._texture_on(960, 64, 128))
        lights = {self.sectors[self.plan[f"stall_{n}"]]["lightlevel"] for n in (1, 2, 3)}
        self.assertEqual({m.LIGHT_WASHROOM}, lights)

    def test_s2_shows_a_lit_slit_beside_its_panel(self):
        """The clue section 7 always promised: a lit slit in the wall above
        the catwalk. Brighter than the catwalk, too thin to enter, and it
        opens onto the secret closet."""
        m = self.m
        slit = self.sectors[self.plan["s2_slit"]]
        self.assertGreater(slit["lightlevel"], m.LIGHT_CATWALK)
        self.assertLess(slit["heightceiling"] - slit["heightfloor"], 56)
        self.assertNotIn(self.plan["s2_slit"], self.reachable)
        neighbours = set()
        for ld in self.lines:
            if "sideback" in ld:
                pair = {self.sides[ld["sidefront"]]["sector"], self.sides[ld["sideback"]]["sector"]}
                if self.plan["s2_slit"] in pair:
                    neighbours |= pair
        self.assertIn(self.plan["s2_closet"], neighbours)
        self.assertIn(self.plan["z6b_catwalk"], neighbours)

    def test_s3_is_found_by_the_drain_not_by_a_lane(self):
        """v2 pointed a yellow lane - the map's 'go here' sign - at the sump
        wall. v3 removes it; a plain-concrete drain one step below the bay
        runs from the tank to the panel instead."""
        m = self.m
        self.assertNotIn("s3_lane", self.plan)
        drain = self.sectors[self.plan["fuel_drain"]]
        bay = self.sectors[self.plan["z7_fuel_bay"]]
        self.assertLess(drain["heightfloor"], bay["heightfloor"])
        self.assertEqual(m.CONCRETE_FLOOR, drain["texturefloor"])
        panel = self.plan["s3_panel"]
        touching = {self.sides[ld["sidefront"]]["sector"] for ld in self.lines
                    if "sideback" in ld and self.sides[ld["sideback"]]["sector"] == panel}
        self.assertIn(self.plan["fuel_drain"], touching, "the drain does not reach the panel")
        # No yellow lane anywhere in the bay.
        for name, i in self.plan.items():
            if self.sectors[i]["texturefloor"] == m.LANE:
                self.assertFalse(name.startswith(("z7_", "s3_", "fuel_drain")), name)

    # --- shape -------------------------------------------------------------
    def _faces_between(self, low, high):
        """Lower textures the `low` zone sees on `high`'s flank."""
        out = set()
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            for near, far in (("sidefront", "sideback"), ("sideback", "sidefront")):
                if (self.sides[ld[near]]["sector"] == self.plan[low]
                        and self.sides[ld[far]]["sector"] == self.plan[high]):
                    out.add(self.sides[ld[near]]["texturebottom"])
        return out

    def test_the_new_structures_are_steel_and_the_walls_stay_concrete(self):
        """What a structure is made of shows on its flank: the gantry, the
        spine and the kerb are plate like the cradle and the catwalk. The
        wall behind the gantry stays the hangar's concrete (ART-BIBLE 4:
        the hangar is mostly concrete), and the columns are steel."""
        m = self.m
        for low, high in (("z6_hangar", "gantry"), ("z6a_cradle", "cradle_spine"),
                          ("z6_hangar", "cradle_kerb_s"), ("z6_hangar", "plinth_c1"),
                          ("z7_fuel_bay", "plinth_tank")):
            self.assertEqual({m.STEEL}, self._faces_between(low, high), f"{high} from {low}")
        behind = {self.sides[ld["sidefront"]]["texturemiddle"] for ld in self.lines
                  if "sideback" not in ld
                  and self.verts[ld["v1"]]["y"] == self.verts[ld["v2"]]["y"] == 320
                  and self.sides[ld["sidefront"]]["sector"] in
                  {self.plan["gantry"]} | {self.plan[f"gantry_step_{n}"] for n in range(1, 6)}}
        self.assertEqual({m.CONC}, behind)

    def test_every_hangar_column_stands_on_a_plinth(self):
        """Five columns, each a hole in its plinth: the plinth is the only
        sector round it, one PLINTH above the hangar floor."""
        m = self.m
        hangar_floor = self.sectors[self.plan["z6_hangar"]]["heightfloor"]
        for name in ("c1", "c2", "c3", "c4", "c5"):
            plinth = self.sectors[self.plan[f"plinth_{name}"]]
            self.assertEqual(hangar_floor + m.PLINTH, plinth["heightfloor"], name)
            inner = [ld for ld in self.lines if "sideback" not in ld
                     and self.sides[ld["sidefront"]]["sector"] == self.plan[f"plinth_{name}"]]
            self.assertEqual(4, len(inner), f"{name}: the column's four faces")
            for ld in inner:
                self.assertEqual(m.STEEL, self.sides[ld["sidefront"]]["texturemiddle"])

    # --- D38: the cosmonautics mural ------------------------------------
    def _mural_targets(self):
        """Points on SDPOSTR2's face, bottom to top and edge to edge.

        The niche is 32 deep, so from the doorway's corner its own jambs
        hide a sliver of the mural's edge (about 3 units of 128); the
        samples start MURAL_JAMB_INSET in from each edge for that reason
        and no other.
        """
        x1, _, x2, y = self.m.MURAL_NICHE
        niche = self.sectors[self.plan["z4_mural"]]
        floor, ceil = niche["heightfloor"], niche["heightceiling"]
        for x in range(x1 + MURAL_JAMB_INSET, x2 - MURAL_JAMB_INSET + 1, 8):
            for z in range(floor + 2, ceil - 1, 8):
                yield (x, y - 1), z

    def _mural_eyes(self):
        """Where the player sees the mural from: three places across the
        doorway from Z3, one body into the room, and the room's centre."""
        lo, hi, y = self.m.KOMNATA_DOORWAY
        eyes = [((x, y + PLAYER_RADIUS), "the doorway")
                for x in (lo + PLAYER_RADIUS, (lo + hi) // 2, hi - PLAYER_RADIUS)]
        eyes.append((self.m.KOMNATA_CENTRE, "the centre"))
        return eyes

    def test_the_mural_is_seen_whole_from_the_doorway_and_the_centre(self):
        """D38. CEO, after his skill-3 run: «Hay un pequeño trozo cuadrado
        justo enfrente del poster de cosmonáutica, yo lo quitaría para que
        se vea bien el poster». It was v3's lectern, 48 high at the niche's
        mouth over a mural whose foot is at 16; the colonnade's west inner
        column also cut it from the doorway. Every sampled point of the
        mural is in view from every eye: the D4 sight-line method."""
        eye_z = self.sectors[self.plan["z4_komnata"]]["heightfloor"] + VIEW_HEIGHT
        for eye, where in self._mural_eyes():
            self.assertEqual(self.plan["z4_komnata"], self.sector_at(*eye), eye)
            for target, z in self._mural_targets():
                self.assertEqual([], self.model._blockers(eye, eye_z, target, z),
                                 f"the mural at {target}, z {z} is hidden from {where} {eye}")

    def test_no_solid_fixture_stands_in_front_of_the_mural(self):
        """Geometry is not the only thing that can block it: no floor lamp or
        drum stands within its radius of a line from an eye to the mural."""
        for eye, where in self._mural_eyes():
            for target, _ in self._mural_targets():
                for t in self.things_of(set(SOLID_FIXTURE_RADIUS)):
                    d = _distance_to_segment((t["x"], t["y"]), eye, target)
                    self.assertGreater(d, SOLID_FIXTURE_RADIUS[t["type"]],
                                       f"thing {t['type']} at ({t['x']}, {t['y']}) "
                                       f"in front of the mural from {where}")

    def test_the_lectern_is_still_on_the_tribune(self):
        """What the lectern gave stays: the tribune still reads as a
        tribune. The lectern stands on it, at its front edge, east of the
        niche and off the mural's axis."""
        lectern = self.plan[f"{self.m.FURNITURE_PREFIX}lectern"]
        x1, y1, x2, y2 = self.m.LECTERN_RECT
        self.assertEqual(lectern, self.sector_at((x1 + x2) // 2, (y1 + y2) // 2))
        self.assertGreaterEqual(x1, self.m.MURAL_NICHE[2], "the lectern is back on the axis")
        tribune = self.sectors[self.plan["tribune"]]
        self.assertEqual(tribune["heightfloor"] + self.m.FURNITURE_HEIGHT,
                         self.sectors[lectern]["heightfloor"])

    # --- G3-F1: every pickup in the komnata, with room to spare -----------
    def _komnata_flood(self, spare):
        """Where the player's centre can go in the komnata, from the
        doorway, if his body were `spare` wider on every side. Returns
        (allowed centres reached, the room's box): the komnata plus the
        mural niche, entered one grown body in from Z3's doorway."""
        m = self.m
        x0, y0, x1, _ = m.KOMNATA_RECT
        y1 = m.MURAL_NICHE[3]                         # the niche is part of the walk
        start = ((m.KOMNATA_DOORWAY[0] + m.KOMNATA_DOORWAY[1]) // 2, y0 + PLAYER_RADIUS + spare)
        return self._flood((x0, y0, x1, y1), start, spare), (x0, y0, x1, y1)

    def _flood(self, box, start, spare):
        """Where the player's centre can go inside `box`, from `start`, if
        his body were `spare` wider on every side.

        The box is rasterised on LANE_GRID: each cell is walkable floor the
        player can reach, or not (a wall, a column, a prop such as the
        lectern, or outside the box). A centre is allowed when every cell
        under its grown box is walkable, the floors under it are within a
        step and the lowest ceiling clears his height, and no solid fixture
        (floor lamp, drum, radio) overlaps the box (Doom's test: the two
        square boxes overlap). Returns the allowed centres reached."""
        x0, y0, x1, y1 = box
        g = LANE_GRID
        # The engine's point-in-sector, as `sector_at`, on the lines that
        # can matter here only: the full scan is too slow for a raster.
        lines = [v for v in self.vertical if v[0] > x0 and max(v[1], v[2]) > y0
                 and min(v[1], v[2]) < y1]

        def sector_at(x, y):
            y += 0.25
            best = None
            for lx, ya, yb, ld in lines:
                if lx > x and min(ya, yb) < y < max(ya, yb) and (best is None or lx < best[0]):
                    best = (lx, ya, yb, ld)
            if best is None:
                return None
            _, ya, yb, ld = best
            if yb < ya:
                return self.sides[ld["sidefront"]]["sector"]
            return self.sides[ld["sideback"]]["sector"] if "sideback" in ld else None

        cols, rows = (x1 - x0) // g, (y1 - y0) // g
        floor = {}
        for i in range(cols):
            for j in range(rows):
                s = sector_at(x0 + g * i + g / 2, y0 + g * j + g / 2)
                if s is not None and s in self.reachable and s not in self.unwalkable:
                    floor[i, j] = (self.sectors[s]["heightfloor"], self.sectors[s]["heightceiling"])
        half = PLAYER_RADIUS + spare
        fixtures = [(t["x"], t["y"], SOLID_FIXTURE_RADIUS[t["type"]])
                    for t in self.things_of(set(SOLID_FIXTURE_RADIUS))]

        def cells(c, origin):
            """Raster indices whose centres lie inside (c - half, c + half)."""
            return range(math.ceil((c - half - origin) / g - 0.5),
                         math.ceil((c + half - origin) / g - 0.5))

        def allowed(cx, cy):
            under = [floor.get((i, j)) for i in cells(cx, x0) for j in cells(cy, y0)]
            if not under or None in under:
                return False
            floors, ceils = [f for f, _ in under], [c for _, c in under]
            if max(floors) - min(floors) > MAX_STEP_UP or min(ceils) - max(floors) < udmf_tests.PLAYER_HEIGHT:
                return False
            return not any(abs(cx - fx) < half + r and abs(cy - fy) < half + r for fx, fy, r in fixtures)

        self.assertTrue(allowed(*start), f"the flood's start {start} is not floor")
        seen, stack = {start}, [start]
        while stack:
            cx, cy = stack.pop()
            for nxt in ((cx + g, cy), (cx - g, cy), (cx, cy + g), (cx, cy - g)):
                if nxt not in seen and allowed(*nxt):
                    seen.add(nxt)
                    stack.append(nxt)
        return seen

    def test_every_komnata_pickup_is_reached_with_room_to_spare(self):
        """QA finding G3-F1 (low): the tribune's east health bonus (432,
        1400) could be reached only through lanes exactly one body wide,
        between the lectern and the east floor lamp or behind the lectern.
        A body fits a 32 lane in the engine, but only straight on: it reads
        as a pickup you cannot get. Every pickup in the komnata is touched
        from where a body ROOM_TO_SPARE wider on each side can walk from the
        doorway. Run against the v3 lamp at (464, 1376), it fails on
        exactly that bonus."""
        reached, (x0, y0, x1, y1) = self._komnata_flood(ROOM_TO_SPARE)
        touch = PLAYER_RADIUS + PICKUP_RADIUS
        pickups = [t for t in self.things
                   if x0 < t["x"] < x1 and y0 < t["y"] < y1
                   and t["type"] not in MONSTER_NUMBERS
                   and t["type"] not in SOLID_FIXTURE_RADIUS
                   and t["type"] != self.m.ED_PLAYER1_START]
        self.assertGreaterEqual(len(pickups), 7, "the komnata's pickups went somewhere else")
        for t in pickups:
            self.assertTrue(any(abs(cx - t["x"]) < touch and abs(cy - t["y"]) < touch
                                for cx, cy in reached),
                            f"thing {t['type']} at ({t['x']}, {t['y']}) is reached only "
                            f"through a lane narrower than {2 * (PLAYER_RADIUS + ROOM_TO_SPARE)}")

    def test_the_komnata_lamps_stay_symmetric_about_the_mural(self):
        """G3-F1 moved both lamps out, not one: the room is still built on
        the mural's axis (D38)."""
        axis = (self.m.MURAL_NICHE[0] + self.m.MURAL_NICHE[2]) / 2
        west, east = self.m.KOMNATA_LAMPS_X
        self.assertEqual(axis - west, east - axis)
        lamps = sorted((t["x"], t["y"]) for t in self.things_of({self.m.ED_FLOOR_LAMP})
                       if t["y"] == self.m.KOMNATA_LAMP_Y)
        self.assertEqual([(west, self.m.KOMNATA_LAMP_Y), (east, self.m.KOMNATA_LAMP_Y)], lamps)

    # --- G3 readiness: skills 2, 3 and 4 (design section 18) -------------
    def _skill_rungs(self):
        """{thing flag: MAPINFO properties} for each skill the mod defines."""
        text = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        rungs = {}
        for body in re.findall(r"^skill\s+\w+\s*\{(.*?)\}", text, re.S | re.M):
            props = {}
            for line in body.splitlines():
                parts = line.split("=", 1)
                key = parts[0].strip().lower()
                if key:
                    props[key] = parts[1].strip().strip('"') if len(parts) == 2 else True
            rungs[SPAWN_FILTER_FLAG[props["spawnfilter"].lower()]] = props
        return rungs

    def test_skills_2_to_4_differ_only_in_what_spawns(self):
        """The mod's MAPINFO keeps Doom's rungs: rung N spawns the things
        flagged skillN, and rungs 2-4 multiply neither ammo nor damage nor
        bring the dead back. So the per-skill counts in this file are what
        each G3 run meets."""
        rungs = self._skill_rungs()
        self.assertEqual({1, 2, 3, 4, 5}, set(rungs))
        for flag in SKILLS:
            for prop in ("ammofactor", "damagefactor", "respawntime"):
                self.assertNotIn(prop, rungs[flag], f"rung {flag} has {prop}")

    def _start_rounds(self):
        """The player's starting 7.62x25 rounds, read from the actor."""
        found = re.search(r"SD_START_CLIP\s*=\s*(\d+)", PLAYER_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "SD_START_CLIP is gone from player.zs")
        return int(found.group(1))

    def _progression(self):
        """Play the map's doors as the player can: open every door and panel
        whose line he can stand at, then press every switch he can reach,
        until nothing new opens. Returns [(open tags, reachable sectors)],
        one row per round of switches."""
        uses = [ld for ld in self.lines if ld.get("playeruse")
                and ld.get("special") in (udmf_tests.SPECIAL_DOOR_OPEN,
                                          udmf_tests.SPECIAL_DOOR_RAISE)]
        switches = {ld["arg0"] for ld in uses if "sideback" not in ld}
        opened, rounds = set(), []
        while True:
            reach, _ = self.model._reachable(opened)
            pressable = set()
            for ld in uses:
                stand = {self.sides[ld["sidefront"]]["sector"]}
                if "sideback" in ld:
                    stand.add(self.sides[ld["sideback"]]["sector"])
                if stand & reach:
                    pressable.add(ld["arg0"])
            doors = pressable - opened - switches
            if doors:
                opened |= doors
                continue
            rounds.append((frozenset(opened), reach))
            pressed = pressable - opened
            if not pressed:
                return rounds
            opened |= pressed

    def test_nothing_the_route_needs_is_locked_scripted_or_on_a_thing(self):
        """Progress is lines only: no key, no locked or scripted special, no
        thing with a tid, and no monster with a special (a monster whose
        death opens a door would make the route depend on the skill). The
        only things with a special are V3 A2's two weapons, whose events
        open closets the route never needs (Map01PickupEventsTest)."""
        self.assertFalse(self.things_of(KEY_NUMBERS))
        for i, ld in enumerate(self.lines):
            if ld.get("special"):
                self.assertIn(ld["special"], ALLOWED_SPECIALS, f"linedef {i}")
        for t in self.things:
            self.assertFalse(t.get("id"), t)
            if t.get("special"):
                self.assertIn(t["type"], self.m.PICKUP_EVENTS, t)

    def test_every_skill_reaches_the_exit(self):
        """G3-4's static half, per skill: from the start, opening only what
        the map offers, the exit switch is reached, and not before the
        switches; and the three tutorial weapons are on that skill and
        reachable before any switch is pressed."""
        m = self.m
        rounds = self._progression()
        exits = [ld for ld in self.lines if ld.get("special") == udmf_tests.SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_sector = self.sides[exits[0]["sidefront"]]["sector"]
        before_switches = rounds[0][1]
        self.assertNotIn(exit_sector, before_switches, "the exit needs no switch")
        self.assertIn(exit_sector, rounds[-1][1], "the exit is never reached")
        for skill in SKILLS:
            for ednum in m.TUTORIAL_WEAPONS:
                found = self.on(skill, self.things_of({ednum}))
                self.assertEqual(1, len(found), f"skill {skill}: weapon {ednum}")
                where = self.sector_at(found[0]["x"], found[0]["y"])
                self.assertIn(where, before_switches,
                              f"skill {skill}: weapon {ednum} is behind a switch")

    def test_the_ice_axe_comes_before_the_first_melee(self):
        """CEO, v3 run: «una especie de sierra mecánica al lado donde se
        empieza que no se podía coger, solo iban los puños». The player
        started with the shovel, so the rack's could not be taken; he now
        starts with the TT-33 only and gets slot 1 at the rack (the ice axe
        since D40; the rack's zone is `z1_ice_axe_rack` since then). So the rack is in the
        dorm, reached with no door opened, and in view from the start; no
        hound (the ice axe's lesson) is in the dorm on any
        skill; and the dorm's riflemen fall to the starting rounds with
        G3-8's margin (BALANCE 7: two TT-33 rounds each)."""
        m = self.m
        sealed, _ = self.model._reachable(set())
        self.assertIn(self.plan["z1_ice_axe_rack"], sealed)
        axe = self.things_of({m.ED_ICE_AXE})[0]
        self.assertEqual(self.plan["z1_ice_axe_rack"], self.sector_at(axe["x"], axe["y"]))
        self.assertEqual([], self.model._blockers(m.PLAYER_START, VIEW_HEIGHT,
                                                  (axe["x"], axe["y"]), 8),
                         "the ice axe on its rack is hidden from the start")
        start_rounds = self._start_rounds()
        for skill in SKILLS:
            in_dorm = [t for t in self.on(skill, self.things_of(MONSTER_NUMBERS))
                       if self.sector_at(t["x"], t["y"]) in sealed]
            self.assertFalse([t for t in in_dorm if t["type"] == m.ED_DEMON],
                             f"skill {skill}: a hound before the ice axe")
            needed = sum(math.ceil(HIT_POINTS[t["type"]] / TT33_AVERAGE) for t in in_dorm)
            self.assertLessEqual(G3_8_MARGIN * needed, start_rounds,
                                 f"skill {skill}: the dorm needs {needed} of {start_rounds} rounds")

    def test_ammo_against_hit_points_by_skill_and_by_stage(self):
        """BALANCE 7 against the map, per skill. G3-8's per-kill figures are
        never kinder than the ruler's barrels-to-kill; and at every stage of
        the route (before the switches, after them) the damage placed so
        far outside the secrets, plus the starting rounds, is at least
        the floor of the skill's G3-8 band (D119) times the hit points met
        so far. No drop counted."""
        for ednum, hp in HIT_POINTS.items():
            self.assertGreaterEqual(SHELLS_TO_KILL[ednum], math.ceil(hp / IZH_AVERAGE), ednum)
        secret = self._secret_sectors()
        rounds = self._progression()
        for skill in SKILLS:
            hp_so_far, seen = 0, set()
            damage_so_far = self._start_rounds() * PPSH_AVERAGE
            for stage, (_, reach) in enumerate(rounds):
                here = [t for t in self.on(skill, self.things)
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                hp_so_far += sum(HIT_POINTS.get(t["type"], 0) for t in here)
                damage_so_far += sum(SHELLS_GIVEN.get(t["type"], 0) * IZH_AVERAGE
                                     + ROUNDS_GIVEN.get(t["type"], 0) * PPSH_AVERAGE
                                     for t in here
                                     if self.sector_at(t["x"], t["y"]) not in secret)
                self.assertGreaterEqual(damage_so_far, G3_8_BAND[skill][0] * hp_so_far,
                                        f"skill {skill}, stage {stage}")
                seen = reach

    def test_the_newest_weapons_pool_leads_every_stage(self):
        """BALANCE 8.4 (D119), stage by stage of the readiness check: a pool
        lies only from the stage where its weapon is (the TT-33's rounds from
        the start), and of each stage's ammunition other than shells the
        pool of the newest weapon met so far (the IZh excepted: shells have
        8.3) is the largest share and at least 40 % of it. MAP01 has rounds and shells only:
        the TT-33's and the PPSh-41's rounds lead."""
        m = self.m
        pool_of = {m.ED_IZH: "shells", m.ED_PPSH: "rounds"}
        pools = {"shells": SHELLS_GIVEN, "rounds": ROUNDS_GIVEN}
        weight = {"shells": 1, "rounds": 1 / ROUNDS_PER_SHELL}
        for skill in SKILLS:
            seen, newest, met = set(), "rounds", {"rounds"}
            for stage, row in enumerate(self._progression()):
                reach = row[1]
                here = [t for t in self._outside_secrets(self.on(skill, self.things))
                        if self.sector_at(t["x"], t["y"]) in reach - seen]
                for ednum, pool in pool_of.items():
                    if any(t["type"] == ednum for t in here):
                        met.add(pool)
                        if pool != "shells":
                            newest = pool
                share = {p: sum(pools[p].get(t["type"], 0) for t in here) * weight[p]
                         for p in pools if p != "shells"}
                for pool, amount in share.items():
                    if amount:
                        self.assertIn(pool, met, f"skill {skill}, stage {stage}: {pool} before its weapon")
                total = sum(share.values())
                if total:
                    self.assertEqual(max(share.values()), share[newest], f"skill {skill}, stage {stage}: {share}")
                    self.assertGreaterEqual(share[newest], NEWEST_SHARE_MIN * total,
                                            f"skill {skill}, stage {stage}: {share}")
                seen = reach

    def test_every_weapon_stretch_is_paid_for(self):
        """D119, stretch by stretch along the weapons: up to the IZh's rack
        (the TT-33 alone), up to the PPSh-41's catwalk (the IZh the newest),
        and to the exit, the damage placed so far outside the secrets plus
        the starting rounds is at least the skill's band floor times the hit
        points met so far, and each stretch's ammunition is mostly for the
        weapons it has: none of the TT-33's stretch is shells. Counted from
        the tables, which the zone test pins to the TEXTMAP."""
        m = self.m
        rows = [(z, e, lo) for z, e, _x, _y, lo in m.AMMO]
        rows += [(z, e, 2) for z, e, _x, _y, _top in m.ITEMS
                 if e in (m.ED_IZH, m.ED_PPSH)]
        for skill in SKILLS:
            hp, damage = 0, self._start_rounds() * PPSH_AVERAGE
            for name, zones in MAP01_STRETCHES:
                hp += sum(HIT_POINTS[m.MONSTER_KINDS[k]]
                          for z, k, _x, _y, _a, lo in m.MONSTERS if z in zones and lo <= skill)
                here = [e for z, e, lo in rows if z in zones and lo <= skill]
                damage += sum(SHELLS_GIVEN.get(e, 0) * IZH_AVERAGE
                              + ROUNDS_GIVEN.get(e, 0) * PPSH_AVERAGE for e in here)
                self.assertGreaterEqual(damage, G3_8_BAND[skill][0] * hp, f"skill {skill}, {name}")
                if name == "the TT-33":
                    self.assertFalse([e for e in here if e in SHELLS_GIVEN], name)
        every = set().union(*(zones for _n, zones in MAP01_STRETCHES))
        self.assertFalse({z for z, *_ in m.MONSTERS} - every)
        self.assertFalse({z for z, *_ in m.AMMO} - every)

    def test_the_night_sky_is_the_cradles_open_launch_slot(self):
        """D121: MAPINFO gives MAP01 a sky (SDSKY6), so some ceiling shows
        it: the slot over the transporter cradle, and nothing else. No sky
        sector is a door or touches one, and every room next to the sky has
        a ceiling no higher than the sky's, so no wall above it is lost."""
        m = self.m
        sky = {i for i, s in enumerate(self.sectors) if s["textureceiling"] == m.SKY}
        self.assertTrue(sky, "no F_SKY1 sector")
        self.assertEqual({"z6a_cradle", "cradle_kerb_s", "cradle_spine", "spine_step_1",
                          "spine_step_2", "spine_step_3"}, {self.zone_of[i] for i in sky})
        for ld in self.lines:
            if "sideback" not in ld:
                continue
            a = self.sides[ld["sidefront"]]["sector"]
            b = self.sides[ld["sideback"]]["sector"]
            for here, there in ((a, b), (b, a)):
                if here in sky and there not in sky:
                    self.assertNotIn(there, self.model.door_sectors, self.zone_of[there])
                    self.assertLessEqual(self.sectors[there]["heightceiling"],
                                         self.sectors[here]["heightceiling"], self.zone_of[there])

    def test_no_solid_fixture_narrows_a_doorway(self):
        """A drum or a floor lamp is on every skill and never moves: none
        stands in a doorway or within two bodies of it on the way through,
        so no doorway can be plugged on any run."""
        verts = self.verts
        for d in self.model.door_sectors:
            xs, ys = [], []
            for ld in self.lines:
                touching = {self.sides[ld["sidefront"]]["sector"]}
                if "sideback" in ld:
                    touching.add(self.sides[ld["sideback"]]["sector"])
                if d in touching:
                    for v in (verts[ld["v1"]], verts[ld["v2"]]):
                        xs.append(v["x"])
                        ys.append(v["y"])
            # The approach: the doorway's own width, two bodies deep either
            # side along the way through it (a door is thin that way). What
            # the fixtures standing in it leave free across the width must
            # still pass a body.
            x1, x2, y1, y2 = min(xs), max(xs), min(ys), max(ys)
            reach = 4 * PLAYER_RADIUS
            across_x = x2 - x1 > y2 - y1
            if across_x:
                y1, y2 = y1 - reach, y2 + reach
            else:
                x1, x2 = x1 - reach, x2 + reach
            lo, hi = (x1, x2) if across_x else (y1, y2)
            taken = []
            for t in self.things_of(set(SOLID_FIXTURE_RADIUS)):
                r = SOLID_FIXTURE_RADIUS[t["type"]]
                if x1 - r < t["x"] < x2 + r and y1 - r < t["y"] < y2 + r:
                    c = t["x"] if across_x else t["y"]
                    taken.append((c - r, c + r))
            free, edge = 0, lo
            for a, b in sorted(taken) + [(hi, hi)]:
                free = max(free, a - edge)
                edge = max(edge, b)
            self.assertGreaterEqual(free, 2 * PLAYER_RADIUS,
                                    f"{self.zone_of[d]}: fixtures leave {free} of {hi - lo}")

    # --- Lenin (CEO, v2 walk) --------------------------------------------
    def test_lenin_has_a_light_of_his_own(self):
        """«que haya iluminación en el poster de Lenin que no se veía bien».
        The poster is drawn at the light of the sector in front of it: that
        sector is a lamp, ringed by a step dimmer, in the darkest room."""
        m = self.m
        # The exit's own Lenin, not a Marx-Engels slot Lenin stands in for
        # (tests/test_posters.py): the slot's niche is not lenin_light.
        poster = [ld for ld in self.lines
                  if self.sides[ld["sidefront"]]["texturemiddle"] == m.LENIN
                  and self.sides[ld["sidefront"]]["sector"] not in
                  {self.plan["z6_slot_niche"]}]
        self.assertEqual(1, len(poster))
        lit = self.sides[poster[0]["sidefront"]]["sector"]
        self.assertEqual(self.plan["lenin_light"], lit)
        room = self.sectors[self.plan["z10_exit"]]["lightlevel"]
        halo = self.sectors[self.plan["lenin_halo"]]["lightlevel"]
        light = self.sectors[lit]["lightlevel"]
        self.assertEqual(m.CEIL_LAMP, self.sectors[lit]["textureceiling"])
        self.assertLess(room, halo)
        self.assertLess(halo, light)
        self.assertGreaterEqual(light - room, 4 * m.LAMP_STEP, "not enough to read from the door")
        self.assertLess(light, m.LIGHT_MAX, "burnt out: 192 is for the beacons")

    # --- D43: the diegetic radio (design section 17.16) -------------------
    def _radio(self):
        radios = self.things_of({ED_RADIO})
        self.assertEqual(1, len(radios), "MAP01 has exactly one radio")
        return radios[0]

    def _radio_constant(self, name):
        """A constant of SD_Radio, read from radio.zs (mod-engineer's)."""
        found = re.search(rf"\b{name}\s*=\s*(\d+)\s*;", RADIO_ZS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, f"{name} is gone from radio.zs")
        return int(found.group(1))

    def _bbox(self, zones):
        """(x1, y1, x2, y2) round every line that bounds any of `zones`."""
        wanted = {self.plan[z] for z in zones}
        xs, ys = [], []
        for ld in self.lines:
            touching = {self.sides[ld["sidefront"]]["sector"]}
            if "sideback" in ld:
                touching.add(self.sides[ld["sideback"]]["sector"])
            if touching & wanted:
                for v in (self.verts[ld["v1"]], self.verts[ld["v2"]]):
                    xs.append(v["x"])
                    ys.append(v["y"])
        return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))

    def _post_doorway(self):
        """(x1, x2, y): the guard post's mouth, the two-sided line between
        the post and the corridor (the post has no door; its south side is
        open, one 8 step up from the corridor)."""
        pair = {self.plan["z5b_guard"], self.plan["z5_service"]}
        xs, ys = [], set()
        for ld in self.lines:
            if "sideback" in ld and {self.sides[ld["sidefront"]]["sector"],
                                     self.sides[ld["sideback"]]["sector"]} == pair:
                for v in (self.verts[ld["v1"]], self.verts[ld["v2"]]):
                    xs.append(v["x"])
                    ys.add(v["y"])
        self.assertEqual(1, len(ys), "the post's mouth is not one straight line")
        return int(min(xs)), int(max(xs)), int(ys.pop())

    def _standable_in_disc(self, centre, radius):
        """Every RADIO_GRID point within `radius` of `centre` (in the plane)
        that is floor the player can stand on, with its sector. The radio
        measures in 3D, and 3D is never shorter than the plane: a point out
        of the plane disc is out of the sphere too."""
        cx, cy = centre
        n = int(radius) // RADIO_GRID
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                x, y = cx + i * RADIO_GRID, cy + j * RADIO_GRID
                if math.hypot(x - cx, y - cy) > radius:
                    continue
                s = self.sector_at(x, y)
                if s is not None and s in self.reachable and s not in self.unwalkable:
                    yield (x, y), s

    def test_one_radio_in_the_guard_post_on_every_skill(self):
        """D43: one SD_Radio (21200) in Z5b, on all five skills and in
        single play, playing «Колокольчик» (arg0 2) with the PM's back-wall
        reach (arg1 96). MAPINFO gives 21200 to SD_Radio, so it spawns."""
        m = self.m
        self.assertEqual(ED_RADIO, m.ED_RADIO)
        r = self._radio()
        self.assertEqual(self.plan["z5b_guard"], self.sector_at(r["x"], r["y"]))
        for n in range(1, 6):
            self.assertTrue(r[f"skill{n}"], f"the radio is missing on skill {n}")
        self.assertTrue(r["single"])
        self.assertEqual((2, 96), (m.RADIO_KOLOKOLCHIK, m.RADIO_REACH_BACK_WALL))
        self.assertEqual(m.RADIO_KOLOKOLCHIK, r.get("arg0"))
        self.assertEqual(m.RADIO_REACH_BACK_WALL, r.get("arg1"))
        mapinfo = re.sub(r"//[^\n]*", "", MAPINFO.read_text(encoding="utf-8"))
        self.assertRegex(mapinfo, rf"(?m)^\s*{ED_RADIO}\s*=\s*SD_Radio\s*$")

    def test_the_radio_stands_on_the_post_floor_against_its_back_wall(self):
        """Its body (SD_RADIO_RADIUS, SD_RADIO_HEIGHT, read from radio.zs)
        is on the post's own floor, not on a prop, with headroom; its north
        face is flush with the crate stack at the post's back, so it leaves
        no slot behind it: the 'against the back wall' that arg1 96 is for."""
        self.assertEqual(RADIO_RADIUS, self._radio_constant("SD_RADIO_RADIUS"))
        height = self._radio_constant("SD_RADIO_HEIGHT")
        r = self._radio()
        x, y, post = r["x"], r["y"], self.plan["z5b_guard"]
        for dx in (-RADIO_RADIUS + 1, RADIO_RADIUS - 1):
            for dy in (-RADIO_RADIUS + 1, RADIO_RADIUS - 1):
                self.assertEqual(post, self.sector_at(x + dx, y + dy), (dx, dy))
        sector = self.sectors[post]
        self.assertGreaterEqual(sector["heightceiling"] - sector["heightfloor"], height)
        self.assertEqual(self.plan[f"{self.m.PROP_PREFIX}guard"],
                         self.sector_at(x, y + RADIO_RADIUS + 1), "not against the crate stack")
        # A monster spawned overlapping a solid thing cannot move off it
        # (Doom's box test refuses every step that still overlaps): the
        # post's guard stands clear of the radio on every skill.
        for t in self.things_of(MONSTER_NUMBERS):
            reach = BODY[t["type"]][0] + RADIO_RADIUS
            self.assertTrue(abs(t["x"] - x) >= reach or abs(t["y"] - y) >= reach,
                            f"monster {t['type']} at ({t['x']}, {t['y']}) spawns inside the radio")

    def test_the_radio_zone_reaches_no_room_but_the_post_and_its_corridor(self):
        """MOD-SPEC 6.7: the reach is a sphere through walls, and the radio
        gives the music back only past reach + SD_RADIO_HYSTERESIS (64).
        Every spot within that of the radio where the player can stand is
        in the post (its rack included) or in the service corridor the post
        opens onto: never D3 or the komnata behind it, the step down or the
        hangar. So D_SDM01 is back before the player is in any other room.
        The post is 128 wide and 64 deep of floor and open along its whole
        south side: no zone of 160 fits in it, from anywhere in it; the
        stretch of corridor in front of it is the radio's by geometry
        (design section 17.16)."""
        r = self._radio()
        zone = r["arg1"] + self._radio_constant("SD_RADIO_HYSTERESIS")
        allowed = {self.plan[n] for n in RADIO_POST + RADIO_CORRIDOR}
        seen = set()
        for (x, y), s in self._standable_in_disc((r["x"], r["y"]), zone):
            seen.add(s)
            self.assertIn(s, allowed, f"({x}, {y}), in {self.zone_of[s]}, is within {zone} of the radio")
        self.assertIn(self.plan["z5b_guard"], seen)
        # ...and the corridor's two ends are outside it: D3 to the west, the
        # step down to the hangar to the east.
        x1, _, x2, _ = self._bbox(RADIO_CORRIDOR)
        self.assertGreater(r["x"] - x1, zone, "the zone reaches D3")
        self.assertGreater(x2 - r["x"], zone, "the zone reaches the step down to the hangar")

    def test_the_radio_plays_in_the_post_and_not_on_the_corridors_way(self):
        """Within its reach (arg1) the radio takes the music. Every spot the
        player's centre reaches in the post, the IZh's rack included, is
        within it: walking in for the IZh turns the radio on. Outside the
        post the reach covers only the strip of corridor in front of the
        mouth, north of the corridor's centre line, which is the line
        tools/route.py's A3 walks: passing along the corridor does not."""
        r = self._radio()
        reach, rx, ry = r["arg1"], r["x"], r["y"]
        post = {self.plan[n] for n in RADIO_POST}
        corridor = {self.plan[n] for n in RADIO_CORRIDOR}
        _, cy1, _, cy2 = self._bbox(RADIO_CORRIDOR)
        middle = (cy1 + cy2) / 2
        lo, hi, mouth_y = self._post_doorway()
        px1, _, px2, py2 = self._bbox(RADIO_POST)
        start = ((lo + hi) // 2, int(middle) + PLAYER_RADIUS)
        reached = self._flood((px1, int(middle), px2, py2), start, 0)
        inside = [c for c in reached if self.sector_at(*c) in post]
        self.assertTrue([c for c in inside if self.sector_at(*c) == self.plan["weapon_rack"]],
                        "no body reaches the IZh's rack")
        for cx, cy in inside:
            # Inside the post the player stands on the radio's floor: the
            # plane distance is the 3D one.
            self.assertLessEqual(math.hypot(cx - rx, cy - ry), reach,
                                 f"({cx}, {cy}) in the post is out of the radio's reach")
        for (x, y), s in self._standable_in_disc((rx, ry), reach):
            if s in post:
                continue
            self.assertIn(s, corridor, f"({x}, {y}) in {self.zone_of[s]}")
            self.assertGreater(y, middle, f"({x}, {y}): the reach crosses the corridor's middle")
            self.assertLess(y, mouth_y)
            self.assertTrue(lo - 2 * PLAYER_RADIUS <= x <= hi + 2 * PLAYER_RADIUS,
                            f"({x}, {y}): the reach runs along the corridor, not just at the mouth")
        a3 = [st for st in route.ROUTES["g3-auto"].steps if st.id == "A3"][0]
        self.assertLessEqual(a3.warp[1], middle, "A3 no longer walks the corridor's middle")

    def test_the_radio_leaves_every_lane_in_the_post_40_wide(self):
        """G3-F1's rule, applied to the radio, a solid box (radius 16) like
        a floor lamp. (1) From the corridor in front of the mouth, a body
        ROOM_TO_SPARE wider on every side (40) touches every pickup in the
        post and on the rack, the IZh above all. (2) On each side of the
        radio, the gap to the nearest wall, prop, step or solid fixture is
        either none (it stands against it) or at least 40: the radio makes
        no lane a body has to thread."""
        r = self._radio()
        rx, ry = r["x"], r["y"]
        post = {self.plan[n] for n in RADIO_POST}
        _, cy1, _, cy2 = self._bbox(RADIO_CORRIDOR)
        middle = int((cy1 + cy2) / 2)
        lo, hi, _ = self._post_doorway()
        px1, _, px2, py2 = self._bbox(RADIO_POST)
        start = ((lo + hi) // 2, middle + PLAYER_RADIUS + ROOM_TO_SPARE)
        reached = self._flood((px1, middle, px2, py2), start, ROOM_TO_SPARE)
        touch = PLAYER_RADIUS + PICKUP_RADIUS
        pickups = [t for t in self.things if self.sector_at(t["x"], t["y"]) in post
                   and t["type"] not in MONSTER_NUMBERS and t["type"] not in SOLID_FIXTURE_RADIUS]
        self.assertIn(self.m.ED_IZH, {t["type"] for t in pickups})
        for t in pickups:
            self.assertTrue(any(abs(cx - t["x"]) < touch and abs(cy - t["y"]) < touch
                                for cx, cy in reached),
                            f"thing {t['type']} at ({t['x']}, {t['y']}) is reached only through "
                            f"a lane narrower than {2 * (PLAYER_RADIUS + ROOM_TO_SPARE)}")
        # (2) the gaps round the radio's own box.
        lane = 2 * (PLAYER_RADIUS + ROOM_TO_SPARE)
        floor = self.sectors[self.plan["z5b_guard"]]["heightfloor"]
        others = [(t["x"], t["y"], SOLID_FIXTURE_RADIUS[t["type"]])
                  for t in self.things_of(set(SOLID_FIXTURE_RADIUS)) if t is not r]

        def blocked(x, y):
            s = self.sector_at(x, y)
            if s is None or s in self.unwalkable or s not in self.reachable:
                return True
            if abs(self.sectors[s]["heightfloor"] - floor) > MAX_STEP_UP:
                return True
            return any(abs(x - fx) < fr and abs(y - fy) < fr for fx, fy, fr in others)

        for side, (dx, dy) in (("north", (0, 1)), ("south", (0, -1)),
                               ("east", (1, 0)), ("west", (-1, 0))):
            for k in range(-RADIO_RADIUS + 2, RADIO_RADIUS - 1, 4):
                x0 = rx + dx * RADIO_RADIUS + (k if dx == 0 else 0)
                y0 = ry + dy * RADIO_RADIUS + (k if dy == 0 else 0)
                gap = next((d for d in range(lane)
                            if blocked(x0 + dx * (d + 0.5), y0 + dy * (d + 0.5))), None)
                self.assertIn(gap, (0, None),
                              f"the radio leaves a lane {gap} wide to its {side}, under {lane}")

    def test_the_radio_blocks_no_step_of_any_map01_route(self):
        """tools/route.py (QA's) warps and walks; a solid radio on a warp
        spot or in a walk would stop the route, and its sdclear kills only
        monsters. A3 walks east through D3 along y 1152 and A4 warps onto
        the IZh's rack at (1040, 1256). For every MAP01 route, no warp spot
        and no point of any straight walk (at route.WALK_UNITS_PER_TIC, its
        own upper estimate) puts the player's box on the radio's."""
        r = self._radio()
        block = PLAYER_RADIUS + RADIO_RADIUS

        def clear(x, y):
            return abs(x - r["x"]) >= block or abs(y - r["y"]) >= block

        routes = [rt for rt in route.ROUTES.values() if rt.map_name == self.m.MAP_NAME]
        self.assertTrue(routes)
        checked = set()
        for rt in routes:
            pos, angle = self.m.PLAYER_START, self.m.PLAYER_ANGLE
            for step in rt.steps:
                where = f"{rt.name} {step.id}"
                if step.warp is not None:
                    pos = step.warp
                    angle = step.angle if step.angle is not None else angle
                    self.assertTrue(clear(*pos), f"{where}: warps onto the radio")
                for action in step.actions:
                    word, *rest = action.split()
                    if word == "angle":
                        angle = int(rest[0])
                    elif word == "forward":
                        length = int(rest[0]) * route.WALK_UNITS_PER_TIC
                        ux, uy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                        for d in range(0, length + 1, RADIO_GRID):
                            self.assertTrue(clear(pos[0] + ux * d, pos[1] + uy * d),
                                            f"{where}: the walk runs into the radio")
                        pos = (pos[0] + ux * length, pos[1] + uy * length)
                checked.add(step.id)
        self.assertLessEqual({"A3", "A4"}, checked)


def _distance_to_segment(p, a, b):
    """Shortest distance from point p to the segment a-b, in the plane."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


class Map01PickupEventsTest(unittest.TestCase):
    """V3 A2, the weapons that spring closets (design section 20), against
    the rules of docs/levels/PICKUP-EVENTS.md section 6: each event's thing,
    special and tag (R7, R8), never closing (R1), the route finished with
    the events unfired and with them fired (R2, R3), the closets shut until
    then and left afterwards (R6), far from the start (R5), and announced
    (R4: the PPSh's squad in sight of the gun, the IZh's hound out of the
    room the rack stands in)."""

    @classmethod
    def setUpClass(cls):
        Map01V3Test.setUpClass()
        cls.v3 = Map01V3Test()
        cls.m, cls.plan, cls.model = cls.v3.m, cls.v3.plan, cls.v3.model
        cls.sectors, cls.lines, cls.things = cls.v3.sectors, cls.v3.lines, cls.v3.things
        cls.event_tags = {event.tag for event, _rects, _floor in cls.m.EVENT_CLOSETS.values()}

    def closet_of(self, event):
        return [name for name, (e, _r, _f) in self.m.EVENT_CLOSETS.items() if e == event]

    def test_each_weapon_carries_its_event_and_nothing_else_does(self):
        m = self.m
        for ednum, event in m.PICKUP_EVENTS.items():
            self.assertIn(ednum, m.TUTORIAL_WEAPONS, event.name)
            closets = self.closet_of(event)
            self.assertEqual(1, len(closets), event.name)
            pe.assert_event(self, self.things, self.sectors, self.lines, ednum, event,
                            {self.plan[f"{closets[0]}_door"]})
            self.assertEqual(pe.events.SPECIAL_DOOR_OPEN, event.special, event.name)
        self.assertEqual(len(m.PICKUP_EVENTS), len(pe.event_things(self.things)))

    def test_each_closet_is_shut_until_its_event_and_left_after_it(self):
        """R6: before its event no door the map opens reaches the closet, and
        its panel is wall (ceiling on floor); once the event has run, the
        closet joins the hangar or the corridor with a body's headroom."""
        doors = set(self.model.doors) - self.event_tags
        before, _ = self.model._reachable(doors)
        after, _ = self.model._reachable(doors | self.event_tags)
        for name in self.m.EVENT_CLOSETS:
            panel = self.sectors[self.plan[f"{name}_door"]]
            self.assertEqual(panel["heightfloor"], panel["heightceiling"], name)
            self.assertNotIn(self.plan[name], before, name)
            self.assertIn(self.plan[name], after, name)
            opened = pe.heights_after([self.m.EVENT_CLOSETS[name][0]], self.sectors,
                                      self.lines, self.v3.sides)[self.plan[f"{name}_door"]]
            self.assertGreaterEqual(opened[1] - opened[0], max(h for _r, h in BODY.values()), name)

    def test_the_route_needs_no_event_and_no_event_cuts_it(self):
        """R2, R3: every skill reaches the exit with no event fired (the
        route test plays lines only), and with both fired nothing reachable
        before is lost and the exit is still reached (R1)."""
        exits = [ld for ld in self.lines if ld.get("special") == udmf_tests.SPECIAL_EXIT_NORMAL]
        exit_sector = self.v3.sides[exits[0]["sidefront"]]["sector"]
        doors = set(self.model.doors) - self.event_tags
        before, _ = self.model._reachable(doors)
        after, _ = self.model._reachable(doors | self.event_tags)
        self.assertIn(exit_sector, before)
        self.assertLessEqual(before, after)
        rounds = self.v3._progression()
        self.assertFalse(self.event_tags & rounds[-1][0], "a line opens an event's tag")
        self.assertIn(exit_sector, rounds[-1][1])

    def test_events_keep_away_from_the_start(self):
        """R5: no event's thing and no closet within SAFE_START_DISTANCE."""
        sx, sy = self.m.PLAYER_START
        for t in pe.event_things(self.things):
            self.assertGreater(math.hypot(t["x"] - sx, t["y"] - sy), SAFE_START_DISTANCE, t)
        for name, (_e, (panel, room), _f) in self.m.EVENT_CLOSETS.items():
            for x1, y1, x2, y2 in (panel, room):
                nx, ny = min(max(sx, x1), x2), min(max(sy, y1), y2)
                self.assertGreater(math.hypot(nx - sx, ny - sy), SAFE_START_DISTANCE, name)

    def test_the_ppsh_squad_comes_out_in_sight_of_the_gun(self):
        """R4: from the PPSh-41's place on the catwalk the floor in front of
        its closet's panel is in view: the squad is seen as it comes out."""
        m = self.m
        gun = [t for t in self.things if t["type"] == m.ED_PPSH][0]
        (x1, _y1, x2, y2), _room = m.CLOSET_PPSH
        eye_z = self.sectors[self.plan["z6b_catwalk"]]["heightfloor"] + VIEW_HEIGHT
        target = ((x1 + x2) / 2, y2 + 24)
        self.assertEqual([], self.model._blockers((gun["x"], gun["y"]), eye_z, target,
                                                  m.HANGAR_FLOOR + VIEW_HEIGHT))

    def test_the_route_checks_the_events_by_the_maps_own_tags(self):
        """tools/route.py's g3-auto writes MAP01's tags as literals: the two
        events' must be the map's, shut at A0, open at A6 and A9."""
        m = self.m
        self.assertEqual((m.TAG_EVENT_IZH, m.TAG_EVENT_PPSH),
                         (route.MAP01_TAG_EVENT_IZH, route.MAP01_TAG_EVENT_PPSH))
        steps = {s.id: s for s in route.ROUTES["g3-auto"].steps}
        self.assertIn((m.TAG_EVENT_IZH, False), steps["A0"].tags)
        self.assertIn((m.TAG_EVENT_PPSH, False), steps["A0"].tags)
        self.assertIn((m.TAG_EVENT_IZH, True), steps["A6"].tags)
        self.assertIn((m.TAG_EVENT_PPSH, True), steps["A9"].tags)

    def test_the_izh_hound_comes_out_into_the_racks_corridor(self):
        """R4 for the one behind the player: the hound's panel opens onto the
        corridor in front of the guard post, where the rack's IZh lies, so
        the panel's grinding is heard where the gun is taken."""
        panel = self.plan["closet_izh_door"]
        corridor = {self.plan[z] for z in RADIO_CORRIDOR}
        self.assertTrue(self.model.neighbours[panel] & corridor)
        rack = [t for t in self.things if t["type"] == self.m.ED_IZH][0]
        (x1, y1, x2, y2), _room = self.m.CLOSET_IZH
        self.assertLess(math.hypot(rack["x"] - (x1 + x2) / 2, rack["y"] - y2), SAFE_START_DISTANCE / 2)


if __name__ == "__main__":
    unittest.main()
