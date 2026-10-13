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
* consumables scale down with skill, and the skill-4 ammo budget of
  criterion G3-8;
* the monster closets: tagged with their switch, reachable, escapable;
* the three re-hidden secrets, and Lenin's light;
* D38: the cosmonautics mural seen whole from the komnata's doorway and
  centre;
* G3 readiness (design section 18): per skill 2, 3 and 4, the exit reached
  pressing only what the map offers, the tutorial weapons before the
  switches, the ice axe (the shovel until D40) before the first melee, and
  ammunition against hit points with BALANCE section 7.

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
import test_udmf as udmf_tests  # noqa: E402

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
SOLID_FIXTURE_RADIUS = {2035: DRUM_RADIUS, 2028: LAMP_RADIUS}
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
MAPINFO = PROJECT_ROOT / "src" / "lumps" / "MAPINFO"
# What GZDoom's SpawnFilter names mean: the thing flag each rung spawns by.
SPAWN_FILTER_FLAG = {"baby": 1, "easy": 2, "normal": 3, "hard": 4, "nightmare": 5}
# The only line specials MAP01 may use: nothing locked, nothing scripted.
ALLOWED_SPECIALS = {udmf_tests.SPECIAL_DOOR_OPEN, udmf_tests.SPECIAL_DOOR_RAISE,
                    udmf_tests.SPECIAL_EXIT_NORMAL}
KEY_NUMBERS = {5, 6, 13, 38, 39, 40}   # Doom's six keys


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
                + [(z, e, x, y) for z, e, x, y, _ in self.m.ITEMS]
                + list(self.m.FIXTURES))
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
        self.assertEqual(6, len(closets))
        for name in closets:
            tag = self.sectors[self.plan[f"{name}_door"]]["id"]
            wanted = m.TAG_FUEL_BAY_AMBUSH if name.startswith("closet_a") else m.TAG_HANGAR_WAVE_2
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
            m.ED_PLAYER1_START, m.ED_BARREL, m.ED_FLOOR_LAMP}
        for kind in consumables:
            n = {s: len(self.on(s, self.things_of({kind}))) for s in SKILLS}
            self.assertGreaterEqual(n[2], n[3], kind)
            self.assertGreaterEqual(n[3], n[4], kind)

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
        """Criterion G3-8: on every skill, placed ammo outside the secrets is
        at least 1.35 times what killing every monster with the intended
        weapon takes. Skill 4 is the binding case."""
        for skill in SKILLS:
            need, have = self._ammo_needed(skill), self._ammo_placed(skill)
            self.assertGreaterEqual(have, G3_8_MARGIN * need,
                                    f"skill {skill}: {have} shell-eq for {need} needed")
        # ...and not a flood either: under three times on skill 4, where
        # what the stand-ins drop still comes on top (design section 8).
        self.assertLess(self._ammo_placed(4), 3 * self._ammo_needed(4))

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
        doorway, if his body were `spare` wider on every side.

        The room's box (the komnata plus the mural niche) is rasterised on
        LANE_GRID: each cell is walkable floor the player can reach, or not
        (a wall, a column, a prop such as the lectern). A centre is allowed
        when every cell under its grown box is walkable, the floors under it
        are within a step and the lowest ceiling clears his height, and no
        floor lamp or drum overlaps the box (Doom's test: the two square
        boxes overlap). Returns (allowed centres reached, the room's box)."""
        m = self.m
        x0, y0, x1, _ = m.KOMNATA_RECT
        y1 = m.MURAL_NICHE[3]                         # the niche is part of the walk
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

        # One grown body into the room from the middle of Z3's doorway.
        start = ((m.KOMNATA_DOORWAY[0] + m.KOMNATA_DOORWAY[1]) // 2, y0 + half)
        self.assertTrue(allowed(*start), f"the flood's start {start} is not floor")
        seen, stack = {start}, [start]
        while stack:
            cx, cy = stack.pop()
            for nxt in ((cx + g, cy), (cx - g, cy), (cx, cy + g), (cx, cy - g)):
                if nxt not in seen and allowed(*nxt):
                    seen.add(nxt)
                    stack.append(nxt)
        return seen, (x0, y0, x1, y1)

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
        thing with a tid or a special (a monster whose death opens a door
        would make the route depend on the skill)."""
        self.assertFalse(self.things_of(KEY_NUMBERS))
        for i, ld in enumerate(self.lines):
            if ld.get("special"):
                self.assertIn(ld["special"], ALLOWED_SPECIALS, f"linedef {i}")
        for t in self.things:
            self.assertFalse(t.get("special") or t.get("id"), t)

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
        G3_8_MARGIN times the hit points met so far. No drop counted."""
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
                self.assertGreaterEqual(damage_so_far, G3_8_MARGIN * hp_so_far,
                                        f"skill {skill}, stage {stage}")
                seen = reach

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
        poster = [ld for ld in self.lines
                  if self.sides[ld["sidefront"]]["texturemiddle"] == m.LENIN]
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


def _distance_to_segment(p, a, b):
    """Shortest distance from point p to the segment a-b, in the plane."""
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


if __name__ == "__main__":
    unittest.main()
