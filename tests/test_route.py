"""Tests for tools/route.py, the scripted G3 route runner: everything that can
be checked without GZDoom (D26: the engine runs are the PM's).

Covered:
* the helper PK3 is tooling and never reaches the mod: it refuses src/,
  dist/ and assets/, lives under the gitignored logs/, loads after the mod,
  and neither the sources nor a freshly built mod PK3 carry it;
* the routes: g3-auto runs skills 2, 3 and 4 by default; the start
  inventory (63dac93) is asserted by SLOT at A0 and the rack pickup at R1,
  keyed on DoomEdNum 21001 and the rack's position, never on a class name
  (the melee weapon was renamed once, D40); the R1 walk really ends on the
  21001 thing in MAP01, and the range-start walk on RANGE's;
* the zone tables: no dead row (`shovel_rack` went with f3cd8ea), RANGE's
  sectors have families of their own;
* RANGE is left by its exit switch (d1e891f), never by sdexit: the walk from
  the start ends against the switch, inside the use range; P4 (range-door)
  presses the gallery door from the passage side and walks into the hall
  taking no pickup; sdexit survives only as a JSON route's recourse;
* MAP02 (metro-critical): built lazily from the map, never from copied
  coordinates (tags and specials from map.py's constants, the pass by
  DoomEdNum 5, the switches and doors by special and tag); the blue door is
  pressed from the hall within reach, the pass walked onto (never `give`)
  and followed when it moves, the switches pressed from their faces, the
  exit walk crosses the gate and stops at the switch;
* MAP03 (tankograd-critical): the same method with two keys. Tags, specials,
  locks and the keys' editor numbers (6 yellow, 13 red, checked in map.py)
  from map.py's constants; each locked door found by its tag AND its lock and
  pressed from the hall; the keys walked onto from a body clear of their
  raised tops; keys counted (0, 1, 2), never named (Doom's YellowCard and
  RedCard today); the exit walk crosses the drum's gate and climbs the dais
  to the breaker; MAPINFO's `endtitle` makes the exit an end sequence;
* --print and --list-routes run with the engine unreachable;
* --parse judges a log: a synthetic clean run passes on every skill and on
  RANGE, and each failure the PM must see (slot 1 at the start, no pickup,
  the wrong weapon raised, the wrong rounds, a log error, a shut door, no
  exit, no inventory) fails with the right exit code; on MAP02 the blue
  door opening without the pass, a press that never reached it, the pass
  not picked up, a route-3 log that cannot see keys, the gate shut and the
  exit not reached; on MAP03 a door opening without its key (the yellow
  with none, the red with the yellow alone), a key not picked up, the exit
  not reached, and an exit that leads to a map instead of the episode's end;
* the gate: without SD_ALLOW_ENGINE nothing is launched.

Run:  python3 -m unittest tests.test_route -v
"""

from __future__ import annotations

import contextlib
import io
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import route  # noqa: E402
import smoke  # noqa: E402
from sdbuild import udmf  # noqa: E402

# The maps by what they are, not by slot (D62 renumbers): the route's own finders.
ZARYA, RANGE = route.ZARYA, route.RANGE
METRO = route.map_defining(*route.METRO_CONSTANTS)
FACTORY = route.map_defining(*route.TANKOGRAD_CONSTANTS)

PLAYER_RADIUS = 16
PICKUP_RADIUS = 20        # Doom's pickups (tests/test_map01.py)
MAX_STEP_UP = 24
USE_RANGE = 64            # Doom's use range from the player's centre
WALK_UNITS_PER_TIC = 8    # route.py's own estimate for +forward without cl_run
SAMPLE = 4                # units between samples along a walk


def _refuse(*_a, **_k):
    raise AssertionError("a test tried to start a process")


@contextlib.contextmanager
def no_engine():
    """Patch every way of starting a process: a test that reaches one fails."""
    with mock.patch("subprocess.Popen", side_effect=_refuse),             mock.patch.object(smoke, "run_engine", side_effect=_refuse):
        yield


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = route.main(argv)
    return code, out.getvalue(), err.getvalue()


# ============================================================================
# The helper never reaches the mod
# ============================================================================

class HelperIsToolingTest(unittest.TestCase):

    def test_the_helper_refuses_src_dist_and_assets(self):
        for root in (PROJECT_ROOT / "src", PROJECT_ROOT / "dist", PROJECT_ROOT / "assets"):
            target = root / "route-test-never-written.pk3"
            with self.assertRaises(route.RouteError, msg=str(root)):
                route.write_helper_pk3(target)
            self.assertFalse(target.exists(), target)

    def test_the_default_helper_lives_under_the_gitignored_logs(self):
        rel = route.HELPER_PK3.relative_to(PROJECT_ROOT)
        self.assertEqual("logs", rel.parts[0])
        ignored = PROJECT_ROOT.joinpath(".gitignore").read_text(encoding="utf-8").split()
        self.assertIn("logs/", ignored)

    def test_the_helper_pk3_is_an_event_handler_with_the_inventory_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = route.write_helper_pk3(Path(tmp) / "h.pk3")
            with zipfile.ZipFile(out) as zf:
                self.assertEqual({"zscript.txt", "MAPINFO"}, set(zf.namelist()))
                zs = zf.read("zscript.txt").decode()
                mapinfo = zf.read("MAPINFO").decode()
        self.assertIn(f"class {route.HELPER_CLASS} : EventHandler", zs)
        # The game state is asked after the level ends, when the per-level
        # helper is gone: a static handler answers it (PM's run, 20:36).
        self.assertIn(f"class {route.STATE_CLASS} : StaticEventHandler", zs)
        self.assertIn(f'AddEventHandlers = "{route.HELPER_CLASS}", "{route.STATE_CLASS}"', mapinfo)
        for event in ("sdinv", "sdpos", "sdtag", "sdlevel", "sdstate", "sdangle", "sdcount",
                      "sdclear", "sdexit", "sdstop"):
            self.assertIn(f'"{event}"', zs)
        # A warp keeps the body's velocity (PM, 21:15): setting the facing
        # stops it, and so does sdstop. Field names: g4.14.2's gzdoom.pk3.
        for event in ("sdangle", "sdstop"):
            block = zs.split(f'if (e.Name == "{event}")', 1)[1].split("return;", 1)[0]
            self.assertIn("pmo.Vel = (0, 0, 0);", block, event)
            self.assertIn("players[e.Player].vel = (0, 0);", block, event)
        state_block = zs.split(f"class {route.STATE_CLASS}", 1)[1]
        self.assertIn('"sdstate"', state_block)
        self.assertEqual(1, zs.count('"sdstate"'), "sdstate answered twice")
        # sdexit ends the level the engine's way; the console `exit` quits.
        self.assertIn("level.ExitLevel(0, false)", zs)
        # sdclear touches monsters only, living ones, and names each kill.
        clear = zs.split('"sdclear"', 1)[1].split('"sdinv"', 1)[0]
        self.assertIn("!a.bIsMonster || a.health <= 0", clear)
        self.assertIn("SDTEST cleared step=", clear)
        # By slot, never by class: the melee weapon is being renamed (D40).
        self.assertIn("LocateWeapon", zs)
        # route-4: keys by the Key base class, never by name (SD_BluePass).
        inv = zs.split('"sdinv"', 1)[1].split('"sdpos"', 1)[0]
        self.assertIn('item is "Key"', inv)
        self.assertIn("SDTEST key class=", inv)
        self.assertIn("keys=%d", inv)
        self.assertNotIn("BluePass", zs)
        self.assertNotIn("BlueCard", zs)
        self.assertNotRegex(zs, r"SD_Shovel|SD_IceAxe|SD_Tokarev")
        self.assertEqual(zs.count("{"), zs.count("}"), "unbalanced braces in the helper")

    def test_the_minimal_helper_keeps_the_proven_part_only(self):
        zs = route.helper_zscript(minimal=True)
        for event in ("sdangle", "sdhurt", "sdcount"):
            self.assertIn(f'"{event}"', zs)
        body = zs.split("class", 1)[1]
        for event in ("sdinv", "sdclear", "sdexit", "sdstate", "sdstop"):
            self.assertNotIn(event, body)
        self.assertNotIn("StaticEventHandler", zs)
        self.assertEqual(zs.count("{"), zs.count("}"))
        self.assertEqual(f'gameinfo\n{{\n    AddEventHandlers = "{route.HELPER_CLASS}"\n}}\n',
                         route.helper_mapinfo(minimal=True))

    def test_no_source_of_the_mod_mentions_the_helper(self):
        pattern = re.compile(rf"{route.HELPER_CLASS}|sdroute", re.I)
        for path in (PROJECT_ROOT / "src").rglob("*"):
            if path.is_file() and path.suffix not in (".pyc",) and "__pycache__" not in path.parts:
                text = path.read_bytes().decode("utf-8", errors="replace")
                self.assertIsNone(pattern.search(text), path)

    def test_a_freshly_built_mod_pk3_carries_no_helper(self):
        import build
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, build.main(["--out", str(out)]))
            with zipfile.ZipFile(out) as zf:
                for name in zf.namelist():
                    self.assertNotIn("sdroute", name.lower())
                    data = zf.read(name)
                    self.assertNotIn(route.HELPER_CLASS.encode(), data, name)

    def test_the_helper_loads_after_the_mod_with_the_tooling_config(self):
        r = route.ROUTES["g3-auto"]
        argv = route.build_command(Path("gzdoom"), Path("iwad.wad"), Path("mod.pk3"),
                                   Path("helper.pk3"), Path("log.txt"), Path("shots"), r, 4)
        self.assertEqual(str(smoke.TOOLING_CONFIG), argv[argv.index("-config") + 1])
        files = argv[argv.index("-file") + 1: argv.index("-file") + 3]
        self.assertEqual(["mod.pk3", "helper.pk3"], files)
        self.assertEqual("4", argv[argv.index("-skill") + 1])
        self.assertEqual(ZARYA, argv[argv.index("+map") + 1])
        self.assertTrue(argv[-1].startswith("+"), "the console sequence is the last argument")


# ============================================================================
# The routes
# ============================================================================

class RouteDefinitionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.map01 = route.MapData(ZARYA)
        cls.range = route.MapData(RANGE)
        cls.maps = {ZARYA: cls.map01, RANGE: cls.range, METRO: route.load_map_data(METRO),
                    FACTORY: route.load_map_data(FACTORY)}
        # Episode 2's routes (MAP04-MAP06, P4) walk maps of their own: every
        # map a built-in route names, loaded once.
        for r in route.all_routes().values():
            if r.map_name not in cls.maps:
                cls.maps[r.map_name] = route.load_map_data(r.map_name)

    def test_g3_auto_runs_skills_2_3_and_4_by_default(self):
        args = route.parse_args([])
        self.assertEqual("g3-auto", args.route)
        self.assertEqual([2, 3, 4], args.skills)
        self.assertEqual(ZARYA, route.ROUTES["g3-auto"].map_name)

    def test_the_start_inventory_is_checked_first_and_by_slot(self):
        """63dac93: TT-33 (slot 2) raised with SD_START_CLIP rounds, slot 1
        empty; the rack gives slot 1 before any door is opened."""
        rounds = route.start_rounds()
        self.assertIsNotNone(rounds, "SD_START_CLIP is gone from player.zs")
        self.assertEqual(50, rounds)
        for name in ("g3-auto", "g3-secrets", "range-start", "range-door"):
            steps = route.ROUTES[name].steps
            a0, r1 = steps[0], steps[[s.id for s in steps].index("R1")]
            self.assertEqual(("A0", False, route.SLOT_SIDEARM, rounds),
                             (a0.id, a0.melee, a0.ready_slot, a0.ready_ammo), name)
            self.assertTrue(r1.melee, name)
            before = steps[:steps.index(r1)]
            self.assertFalse([s for s in before if "use" in s.actions],
                             f"{name}: a door is opened before the rack")

    def test_the_slots_are_the_player_classes(self):
        """The slot numbers the route asserts are the ones player.zs gives."""
        text = route.PLAYER_ZS.read_text(encoding="utf-8")
        slots = dict(re.findall(r'Player\.WeaponSlot\s+(\d+),\s*"(\w+)"', text))
        self.assertIn(str(route.SLOT_MELEE), slots)
        start = re.search(r'Player\.StartItem\s+"(\w+)"\s*;', text).group(1)
        self.assertEqual(start, slots[str(route.SLOT_SIDEARM)], "the start weapon is not slot 2")
        self.assertNotEqual(start, slots[str(route.SLOT_MELEE)], "the melee weapon is given at start")

    def test_the_route_names_no_weapon_class(self):
        """Keyed on DoomEdNum 21001 and slots: a rename cannot break it."""
        source = Path(route.__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"SD_Shovel|SD_IceAxe|SD_Tokarev")
        self.assertEqual(21001, route.ED_MELEE)
        mapinfo = (PROJECT_ROOT / "src" / "lumps" / "MAPINFO").read_text(encoding="utf-8")
        weapon = re.search(r"^\s*21001\s*=\s*(\w+)", mapinfo, re.M).group(1)
        player = route.PLAYER_ZS.read_text(encoding="utf-8")
        self.assertRegex(player, rf'Player\.WeaponSlot\s+{route.SLOT_MELEE},\s*"{weapon}"',
                         "DoomEdNum 21001 is not the slot-1 weapon")

    def _walk(self, md, start, angle, target):
        """Sample the straight walk from `start` towards `target`, both on
        the axis `angle` (0/90/180/270). Returns the sectors crossed."""
        dx = {0: 1, 180: -1}.get(angle, 0)
        dy = {90: 1, 270: -1}.get(angle, 0)
        self.assertTrue(dx or dy, angle)
        if dx:
            self.assertEqual(start[1], target[1], "the walk is not along the row")
            n = int((target[0] - start[0]) / dx)
        else:
            self.assertEqual(start[0], target[0], "the walk is not along the column")
            n = int((target[1] - start[1]) / dy)
        self.assertGreater(n, 0, "the thing is behind the player")
        self.assertLessEqual(n, route.RACK_WALK * WALK_UNITS_PER_TIC, "too far for the walk")
        return [md.sector_at(start[0] + dx * d, start[1] + dy * d) for d in range(0, n + 1, SAMPLE)]

    def _clear_of_walls(self, md, point):
        here = md.sector_at(*point)
        for ox in (-PLAYER_RADIUS, PLAYER_RADIUS):
            for oy in (-PLAYER_RADIUS, PLAYER_RADIUS):
                self.assertEqual(here, md.sector_at(point[0] + ox, point[1] + oy),
                                 f"the body at {point} overlaps another sector")

    def test_the_rack_walk_ends_on_the_21001_thing_in_map01(self):
        md = self.map01
        for skill in (2, 3, 4):
            found = md.things_on(route.ED_MELEE, skill)
            self.assertEqual(1, len(found), f"skill {skill}")
        thing = md.things_on(route.ED_MELEE, 3)[0]
        start = route.MAP01_RACK_APPROACH
        self._clear_of_walls(md, start)
        player = [t for t in md.textmap.things if t.type == 1][0]
        dorm = md.sector_at(player.x, player.y)
        floor = md.textmap.sectors[dorm].heightfloor
        crossed = self._walk(md, start, route.MAP01_RACK_FACING, (thing.x, thing.y))
        for s in crossed:
            self.assertIsNotNone(s)
            name = md.name_of(s)
            self.assertEqual("Z1", route.zone_family(name), name)
            self.assertFalse(name.startswith(("prop_", "crate_")), name)
            self.assertLessEqual(md.textmap.sectors[s].heightfloor - floor, MAX_STEP_UP, name)
        # On the rack: its own alcove off the dorm, not the dorm floor. By
        # zone, not by sector name (the rack may be renamed with the weapon;
        # route.ZONE_PREFIXES must then follow, or R1's zone check fails).
        rack = md.sector_at(thing.x, thing.y)
        self.assertNotEqual(dorm, rack, "the 21001 thing is not in the rack's alcove")
        self.assertEqual("Z1", route.zone_family(md.name_of(rack)), md.name_of(rack))
        # The alcove's back wall stops the walk with the body over the thing.
        self.assertIsNone(md.sector_at(thing.x - PLAYER_RADIUS - 1, thing.y),
                          "the walk does not end against the alcove's back wall")
        # The start of the walk is reached with no door: the dorm, as A0.
        self.assertEqual("Z1", route.zone_family(md.name_of(md.sector_at(*start))))

    def test_the_range_walk_takes_the_21001_thing_and_no_other(self):
        md = self.range
        thing = md.things_on(route.ED_MELEE, 3)[0]
        start = route.RANGE_AXE_APPROACH
        self._clear_of_walls(md, start)
        crossed = self._walk(md, start, route.RANGE_AXE_FACING, (thing.x, thing.y))
        self.assertEqual({md.sector_at(*start)}, set(crossed))
        reach = PLAYER_RADIUS + PICKUP_RADIUS
        for t in md.textmap.things:
            if t is thing or t.type == 1:
                continue
            # Only the hall: the walk ends at its north wall, and the gallery
            # beyond it is another room.
            if md.sector_at(t.x, t.y) == md.sector_at(*start) and abs(t.x - start[0]) < reach:
                self.assertTrue(t.y < start[1] - reach, f"the walk also takes {t.type} at {t.x},{t.y}")

    def test_every_warp_lands_in_the_zone_its_step_expects(self):
        """A warp into a wall or the wrong room would make a step fail for
        the route's sake, not the map's. Checked for the steps that end
        where they warp (no walk): the mural shots, the pickups, A2, A5."""
        for name, r in route.all_routes().items():
            md = self.maps[r.map_name]
            for step in r.steps:
                if step.warp is None or not step.expect:
                    continue
                if any(a.split()[0] in ("forward", "use") for a in step.actions):
                    continue
                family = route.zone_family(md.name_of(md.sector_at(*step.warp)))
                self.assertIn(family, step.expect, f"{name} {step.id} at {step.warp}")

    def test_the_mural_route_is_section_17_13(self):
        r = route.ROUTES["mural"]
        self.assertFalse(r.must_exit)
        self.assertEqual(["M1", "M2", "M3a", "M3b", "M4", "M5"], [s.id for s in r.steps])
        self.assertEqual([(256, 976, 90), (320, 1192, 90), (208, 976, 80), (304, 976, 100),
                          (400, 1320, 90), (320, 1360, 90)],
                         [(*s.warp, s.angle) for s in r.steps])
        self.assertTrue(all("capture" in s.actions for s in r.steps))

    def test_every_walk_is_cleared_first_unless_told_not_to(self):
        for name, r in route.all_routes().items():
            cmds = route.route_commands(r)
            walks = [i for i, c in enumerate(cmds) if c == "+forward"]
            for i in walks:
                self.assertTrue(cmds[i - 2].startswith("netevent sdclear "), (name, cmds[i - 2]))
                _, _, _step, length, width = cmds[i - 2].split()
                tics = int(cmds[i + 1].split()[1])
                self.assertEqual((tics * route.WALK_UNITS_PER_TIC, route.CLEAR_HALF_WIDTH),
                                 (int(length), int(width)))
            self.assertEqual(len(walks), sum(c.startswith("netevent sdclear") for c in cmds), name)
            self.assertFalse([c for c in route.route_commands(r, clear=False)
                              if c.startswith("netevent sdclear")], name)

    def test_every_built_in_route_ends_by_a_switch_never_by_sdexit(self):
        """d1e891f gave RANGE an exit switch: range-start presses it, as
        MAP01's routes press theirs. sdexit stays in the helper, unused."""
        for name in ("g3-auto", "g3-secrets", "range-start", "range-door", "metro-critical",
                     "tankograd-critical"):
            r = route.route_by_name(name)
            self.assertEqual(("switch", True), (r.exit_by, r.must_exit), name)
            want = route.exit_expectation(r.map_name)
            self.assertEqual((want["end_sequence"], want["next_map"]), (r.end_sequence, r.next_map), name)
            self.assertEqual("use", r.steps[-1].actions[0], f"{name}: the last step presses")
        for name, r in route.all_routes().items():
            cmds = route.route_commands(r)
            self.assertNotIn("exit", cmds, f"{name}: the console exit quits GZDoom")
            self.assertNotIn("netevent sdexit", cmds, name)
            self.assertFalse([s.id for s in r.steps if "exit" in s.actions], name)
        self.assertIn('"sdexit"', route.helper_zscript(), "the recourse is gone from the helper")
        last = route.ROUTES["range-start"].steps[-1]
        self.assertEqual(("E1", True), (last.id, "capture" in last.actions))

    def _exit_lines(self, md):
        tm = md.textmap
        return [ld for ld in tm.linedefs if ld.special == route.SPECIAL_EXIT_NORMAL]

    def test_the_range_exit_walk_ends_against_its_switch(self):
        """E0 turns round on the start and walks west into the alcove; the
        back wall stops him with the switch inside the use range; E1
        presses it. Read back from the built RANGE."""
        md = self.range
        tm = md.textmap
        lines = self._exit_lines(md)
        self.assertEqual(1, len(lines), "RANGE has one exit switch")
        ld = lines[0]
        a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
        self.assertEqual(a.x, b.x, "the exit switch is not on a west/east wall")
        self.assertIn("playeruse", ld.flags, "the exit is pressed, not crossed")
        self.assertIsNone(ld.sideback, "the exit switch is on a one-sided wall")
        wall_x, (y_lo, y_hi) = a.x, sorted((a.y, b.y))
        alcove = tm.sidedefs[ld.sidefront].sector
        self.assertEqual("EXIT", route.zone_family(md.name_of(alcove)))
        # E0 starts on the player start, turned round.
        start = [t for t in tm.things if t.type == 1][0]
        e0, e1 = route.ROUTES["range-start"].steps[-2:]
        self.assertEqual(("E0", "E1"), (e0.id, e1.id))
        self.assertEqual((start.x, start.y), e0.warp)
        self.assertEqual((start.angle + 180) % 360, e0.angle)
        self.assertEqual(route.RANGE_EXIT_FACING, e0.angle)
        self.assertLess(y_lo + PLAYER_RADIUS, start.y)
        self.assertLess(start.y, y_hi - PLAYER_RADIUS, "the body does not fit in front of the switch")
        # The walk: hall then alcove, nothing else, no pickup, long enough.
        end = (wall_x + PLAYER_RADIUS, start.y)
        crossed = self._walk(md, e0.warp, e0.angle, end)
        self.assertEqual({"HALL", "EXIT"}, {route.zone_family(md.name_of(s)) for s in crossed})
        walk_tics = int([x for x in e0.actions if x.startswith("forward")][0].split()[1])
        self.assertGreaterEqual(walk_tics * WALK_UNITS_PER_TIC, e0.warp[0] - end[0] + PICKUP_RADIUS)
        reach = PLAYER_RADIUS + PICKUP_RADIUS
        for t in tm.things:
            if t.type != 1 and end[0] - reach < t.x < e0.warp[0] + reach:
                self.assertGreaterEqual(abs(t.y - start.y), reach, f"the walk takes {t.type} at {t.x},{t.y}")
        # Where the walk stops: in the alcove, the wall behind it solid, the
        # switch 16 ahead, inside the use range; E1 presses without moving.
        self.assertEqual(alcove, md.sector_at(*end))
        for dy in (-PLAYER_RADIUS + 1, PLAYER_RADIUS - 1):
            self.assertEqual(alcove, md.sector_at(end[0], end[1] + dy))
        self.assertIsNone(md.sector_at(wall_x - 1, start.y), "there is no wall behind the switch")
        self.assertLessEqual(end[0] - wall_x, USE_RANGE)
        self.assertIsNone(e1.warp)
        self.assertEqual(("use",), e1.actions[:1])

    def test_the_range_door_is_pressed_from_the_passage_and_walked_through(self):
        """P4: from the passage's south leg facing south, the line ahead is
        the gallery door's Door_Raise, wound with the passage in front (ZDoom
        fires a use special from the front only), within the use range; the
        walk crosses passage, door and hall only, and takes no pickup."""
        md = self.range
        tm = md.textmap
        p4a, p4b = (s for s in route.ROUTES["range-door"].steps if s.id.startswith("P4"))
        x, y = p4a.warp
        self.assertEqual(route.RANGE_DOOR_FACING, p4a.angle)
        self._clear_of_walls(md, p4a.warp)
        passage = md.sector_at(x, y)
        self.assertEqual("PASSAGE", route.zone_family(md.name_of(passage)))
        # The first horizontal line straight south of him.
        ahead = []
        for ld in tm.linedefs:
            a, b = tm.vertices[ld.v1], tm.vertices[ld.v2]
            if a.y == b.y and a.y < y and min(a.x, b.x) < x < max(a.x, b.x):
                ahead.append((y - a.y, ld))
        dist, door_line = min(ahead, key=lambda d: d[0])
        self.assertLessEqual(dist, USE_RANGE, "the door is out of reach")
        self.assertEqual(12, door_line.special, "not Door_Raise")
        self.assertEqual(route.RANGE_TAG_GALLERY_DOOR, door_line.arg0)
        self.assertIn("playeruse", door_line.flags)
        self.assertEqual(passage, tm.sidedefs[door_line.sidefront].sector,
                         "the passage-side face is wound the wrong way: use would not fire")
        door = tm.sidedefs[door_line.sideback].sector
        self.assertEqual(route.RANGE_TAG_GALLERY_DOOR, tm.sectors[door].identifier)
        self.assertEqual("GDOOR", route.zone_family(md.name_of(door)))
        self.assertEqual(((route.RANGE_TAG_GALLERY_DOOR, False),), p4a.tags)
        self.assertEqual(((route.RANGE_TAG_GALLERY_DOOR, True),), p4b.tags)
        # The walk south, at its longest.
        tics = int([a for a in p4b.actions if a.startswith("forward")][0].split()[1])
        end = (x, y - tics * WALK_UNITS_PER_TIC)
        crossed = self._walk(md, p4a.warp, p4a.angle, end)
        families = [route.zone_family(md.name_of(s)) for s in crossed]
        self.assertEqual({"PASSAGE", "GDOOR", "HALL"}, set(families))
        self.assertEqual("HALL", families[-1])
        self.assertIn("HALL", p4b.expect)
        reach = PLAYER_RADIUS + PICKUP_RADIUS
        for t in tm.things:
            if t.type != 1 and end[1] - reach < t.y < y + reach:
                self.assertGreaterEqual(abs(t.x - x), reach, f"the walk takes {t.type} at {t.x},{t.y}")

    def test_no_zone_row_is_dead(self):
        """Every prefix row and every whole name matches a sector of MAP01 or
        RANGE. The rack's old row (`shovel_rack`) went with the rename to
        `z1_ice_axe_rack` (f3cd8ea), which files under Z1 by its own name."""
        names = set(self.map01.plan) | set(self.range.plan) | set(self.maps[METRO].plan)             | set(self.maps[FACTORY].plan)
        for prefix, family in route.ZONE_PREFIXES:
            self.assertTrue([n for n in names if n.startswith(prefix)], f"dead row {prefix!r} -> {family}")
        for name in route.ZONE_NAMES:
            self.assertIn(name, self.range.plan)
        self.assertNotIn("shovel_rack", [p for p, _f in route.ZONE_PREFIXES])
        rack = self.map01.sector_at(*[(t.x, t.y) for t in self.map01.textmap.things
                                      if t.type == route.ED_MELEE][0])
        self.assertEqual(("z1_ice_axe_rack", "Z1"),
                         (self.map01.name_of(rack), route.zone_family(self.map01.name_of(rack))))

    def test_range_sectors_have_families_of_their_own(self):
        f1 = {route.zone_family(n) for n in self.map01.plan}
        f2 = {route.zone_family(n) for n in self.range.plan}
        self.assertNotIn("?", f1)
        self.assertNotIn("?", f2)
        self.assertEqual(len(self.range.plan), len(f2), "two RANGE sectors share a family")
        self.assertFalse(f1 & f2, "a family names a zone in both maps")

    def test_every_warp_starts_and_ends_at_rest(self):
        """The console `warp` keeps the player's velocity. PM, 21:15:
        range-door's E0 warped onto the start right after P4b's walk south,
        glided 39 units south and walked west into the hall's wall instead of
        the exit alcove. Every warp is now preceded by sdstop and followed by
        sdangle (which also stops the body) or by sdstop."""
        for name, r in route.all_routes().items():
            cmds = route.route_commands(r)
            warps = [i for i, c in enumerate(cmds) if c.startswith("warp ")]
            self.assertEqual(sum(1 for s in r.steps if s.warp is not None), len(warps), name)
            for i in warps:
                self.assertEqual("netevent sdstop", cmds[i - 2], (name, cmds[i]))
                self.assertTrue(cmds[i - 1].startswith("wait "), (name, cmds[i]))
                self.assertTrue(cmds[i + 1].startswith("wait "), (name, cmds[i]))
                after = cmds[i + 2]
                self.assertTrue(after == "netevent sdstop" or after.startswith("netevent sdangle "),
                                (name, cmds[i], after))
        # The exact case: between P4b's walk and E0's walk the body is
        # stopped before the warp and again by the facing after it.
        cmds = route.route_commands(route.ROUTES["range-door"])
        p4b = cmds.index("echo SDSTEP 3 P4b")
        e0 = cmds.index("echo SDSTEP 4 E0")
        released = max(i for i, c in enumerate(cmds[:e0]) if c == "-forward")
        self.assertGreater(released, p4b)
        between = [c for c in cmds[released:cmds.index("+forward", e0)] if not c.startswith("wait ")]
        x, y = route.RANGE_START
        self.assertEqual(["-forward", "screenshot", f"netevent sdpos 3", "echo SDSTEP 4 E0",
                          "netevent sdstop", f"warp {x} {y}",
                          f"netevent sdangle {route.RANGE_EXIT_FACING}", "screenshot",
                          "netevent sdclear 4 400 128"], between)

    def test_every_built_in_route_turns_into_a_sequence(self):
        for name, r in route.all_routes().items():
            text = route.console_sequence(r)
            self.assertLessEqual(len(text), route.MAX_SEQUENCE_CHARS, name)
            self.assertIn("quit", text)
            self.assertEqual(sum(1 for s in r.steps if "inv" in s.actions),
                             text.count("netevent sdinv"), name)

    def test_an_inventory_expectation_needs_an_inv_action(self):
        with self.assertRaises(route.RouteError):
            route.Step("X", actions=("capture",), melee=True)
        with self.assertRaises(route.RouteError):
            route.parse_action("inv 3")

    def test_a_json_route_may_still_end_by_sdexit(self):
        """The documented recourse for a map with no exit line."""
        r = route.route_from_json({"name": "noexit", "map": "RANGE", "exit_by": "console",
                                   "end_sequence": True, "steps": [
                                       {"id": "A0", "do": ["capture"]},
                                       {"id": "E1", "do": ["exit", "wait 35", "capture"]}]})
        self.assertEqual(("console", True), (r.exit_by, r.end_sequence))
        self.assertIn("netevent sdexit", route.route_commands(r))
        self.assertEqual("switch", route.route_from_json({"steps": []}).exit_by)
        with self.assertRaises(route.RouteError):
            route.route_from_json({"exit_by": "teleport", "steps": []})

    def test_a_json_route_carries_the_inventory_fields(self):
        r = route.route_from_json({"name": "mine", "map": "range", "must_exit": False, "steps": [
            {"id": "A0", "do": ["inv"], "melee": False, "ready_slot": 2, "ready_ammo": 50}]})
        self.assertEqual("RANGE", r.map_name)
        self.assertEqual((False, 2, 50), (r.steps[0].melee, r.steps[0].ready_slot,
                                          r.steps[0].ready_ammo))


# ============================================================================
# --print and --list-routes: no engine
# ============================================================================

class PrintTest(unittest.TestCase):

    def test_print_shows_every_skill_and_the_rack_without_the_engine(self):
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print"])
            self.assertTrue((Path(tmp) / "h.pk3").is_file())
        self.assertEqual(route.EXIT_OK, code)
        for skill in (2, 3, 4):
            self.assertIn(f"skill {skill}: ", out)
            self.assertIn(f"-skill {skill} +map {ZARYA}", out)
        x, y = route.MAP01_RACK_APPROACH
        self.assertIn(f"warp {x} {y}", out)
        self.assertIn("netevent sdinv", out)

    def test_print_runs_on_range(self):
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print", "--route", "range-start", "--skills", "3"])
            self.assertEqual(route.EXIT_OK, code)
            self.assertIn(f"-skill 3 +map {RANGE}", out)
            self.assertNotIn("sdexit", out)
            x, y = route.RANGE_START
            self.assertIn(f"warp {x} {y}", out)
            self.assertIn(f"netevent sdangle {route.RANGE_EXIT_FACING}", out)
            self.assertIn("netevent sdclear", out)
            code, out, _ = run_main(["--print", "--route", "range-door", "--skills", "3"])
            self.assertEqual(route.EXIT_OK, code)
            self.assertIn(f"netevent sdtag {route.RANGE_TAG_GALLERY_DOOR}", out)
            code, out, _ = run_main(["--print", "--route", "range-start", "--no-clear"])
            self.assertEqual(route.EXIT_OK, code)
            self.assertNotIn("sdclear", out)

    def test_the_weapon_sprite_is_set_before_the_sequence_both_ways(self):
        """M5 needs the weapon out of the frame. The cvar goes before the
        sequence (an `extra` +cvar would run after its waits) and is set to
        1 otherwise, since the tooling config keeps the last value."""
        r = route.ROUTES["mural"]
        for hide, value in ((True, "0"), (False, "1")):
            argv = route.build_command(Path("gzdoom"), Path("i.wad"), Path("m.pk3"), Path("h.pk3"),
                                       Path("l.txt"), Path("s"), r, 3, hide_weapon=hide)
            i = argv.index("+r_drawplayersprites")
            self.assertEqual(value, argv[i + 1])
            self.assertLess(i, len(argv) - 1)
            self.assertTrue(argv[-1].startswith("+wait "))
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print", "--route", "mural", "--skills", "3",
                                     "--nomonsters", "--hide-weapon"])
        self.assertEqual(route.EXIT_OK, code)
        self.assertIn("-nomonsters", out)
        self.assertIn("+r_drawplayersprites 0", out)

    def test_list_routes(self):
        with no_engine():
            code, out, _ = run_main(["--list-routes"])
        self.assertEqual(route.EXIT_OK, code)
        for name in route.route_names():
            self.assertIn(name, out)
        self.assertIn("metro-critical", out)
        self.assertNotIn("UNAVAILABLE", out)


# ============================================================================
# --parse: a log in, a verdict out
# ============================================================================

class FakeRun:
    """Writes the log a clean run of `r` on `skill` would leave, from the
    map's own data: every step ends in a sector of a zone it expects."""

    _points: dict[tuple[str, str], tuple[int, int, int]] = {}

    def __init__(self, r: route.Route, skill: int, md: route.MapData):
        self.r, self.skill, self.md = r, skill, md
        self.melee_owned_from = [s.id for s in r.steps].index("R1") if any(
            s.id == "R1" for s in r.steps) else None
        self.overrides: dict = {}
        self.god_line = "God mode on."          # what g4.14.2 printed, PM's run 20:36
        # Where the level leads: the route's next map (MAPINFO), else the end
        # sequence the PM's MAP01 run unloaded towards at 20:36.
        self.next_map = r.next_map or "enDSeQ1dce"
        self.end_state = route.GS_FINALE
        self.cleared: list[tuple] = []          # (step, class, x, y, hp, dead) sdclear lines
        # Keys (route-4): the step each key is picked up at, from the steps
        # that expect one (`key`) or a count of them (`keys`), in order; and
        # the classes they are reported as: MAP02's pass, MAP03's two Doom
        # cards (no SD_ class yet). The route never reads the names.
        self.key_gains: list[int] = []
        for n, s in enumerate(r.steps):
            want = s.keys if s.keys is not None else (1 if s.key else 0)
            while len(self.key_gains) < want:
                self.key_gains.append(n)
        self.key_classes = ("YellowCard", "RedCard") if r.name == "tankograd-critical" \
            else ("SD_BluePass",)
        self.old_helper = False                 # a route-3 helper: no key lines, no keys=
        self.unpressed: set[str] = set()        # step ids whose presses print no line
        self.force_open: set[tuple[int, str]] = set()   # (tag, step id) read open whatever
        self.step_extra: dict[str, list[str]] = {}      # step id -> engine lines in it
        self.pos_override: dict[str, tuple[str, ...]] = {}  # step id -> families it ends in

    def point_in(self, families):
        for family in families:
            key = (self.md.map_name, family)
            if key not in self._points:
                self._points[key] = self._search(family)
            if self._points[key]:
                return self._points[key]
        raise AssertionError(f"no point in {families}")

    def _search(self, family):
        xs = [v.x for v in self.md.textmap.vertices]
        ys = [v.y for v in self.md.textmap.vertices]
        for x in range(int(min(xs)) + 8, int(max(xs)), 16):
            for y in range(int(min(ys)) + 8, int(max(ys)), 16):
                s = self.md.sector_at(x, y)
                if s is not None and route.zone_family(self.md.name_of(s)) == family:
                    return (x, y, s)
        return None

    def inventory_lines(self, number):
        weapons = [("SD_Pistol2", route.SLOT_SIDEARM)]
        if self.melee_owned_from is not None and number >= self.melee_owned_from:
            weapons.insert(0, ("SD_Melee1", route.SLOT_MELEE))
        ready, slot, ammo = "SD_Pistol2", route.SLOT_SIDEARM, route.start_rounds()
        weapons, ready, slot, ammo = self.overrides.get(number, (weapons, ready, slot, ammo))
        lines = [f"SDTEST weapon class={c} slot={s}" for c, s in weapons]
        if self.old_helper:
            lines.append(f"SDTEST inv weapons={len(weapons)} ready={ready} slot={slot} ammo={ammo}")
            return lines
        keys = [cls for cls, at in zip(self.key_classes, self.key_gains) if number >= at]
        lines = [f"SDTEST key class={k}" for k in keys] + lines
        lines.append(f"SDTEST inv weapons={len(weapons)} ready={ready} slot={slot} ammo={ammo} "
                     f"keys={len(keys)}")
        return lines

    def text(self, *, shut_tags=(), exit_=True, drop=(), extra=()):
        md, out = self.md, []
        out += ["GZDoom version g4.14.2", f"adding {PROJECT_ROOT}/dist/sovietdoom.pk3, 300 lumps",
                f"{self.r.map_name} - test", "SDTEST helper route-1 map=" + self.r.map_name,
                self.god_line]
        out += list(extra)
        secrets = len(md.secret_sectors())
        for n, step in enumerate(self.r.steps):
            out.append(f"SDSTEP {n} {step.id}")
            if step.id not in self.unpressed:
                out += [f"SDTEST line index=1 special={sp} arg0={a0} front=0 back=1 type=2 player=1"
                        for sp, a0 in step.presses]
            out += self.step_extra.get(step.id, [])
            if any(a.startswith("forward") for a in step.actions):
                mine = [c for c in self.cleared if c[0] == n]
                out += [f"SDTEST cleared step={c[0]} class={c[1]} x={c[2]} y={c[3]} hp={c[4]} "
                        f"dead={c[5]}" for c in mine]
                out.append(f"SDTEST clear step={n} killed={len(mine)}")
            if "level" in step.actions:
                out.append(f"SDTEST level map={self.r.map_name} monsters=0/{md.monsters_on(self.skill)} "
                           f"secrets=0/{secrets} items=0/40 time=140")
            if "inv" in step.actions and ("inv", n) not in drop:
                out += self.inventory_lines(n)
            for tag, want_open in step.tags:
                for sector in self._tag_sectors(tag):
                    is_open = (want_open and tag not in shut_tags) or (tag, step.id) in self.force_open
                    out.append(f"SDTEST tag {tag} sector={sector} floor=0 ceil={128 if is_open else 0}")
            if "capture" in step.actions:
                out.append(f"Captured Screenshot_Doom_{n:04d}.png")
            if step.id in self.pos_override:
                x, y, s = self.point_in(self.pos_override[step.id])
            elif step.expect:
                x, y, s = self.point_in(step.expect)
            elif step.warp:
                x, y = step.warp
                s = md.sector_at(x, y)
            else:
                x, y, s = 0, 0, md.sector_at(0, 0)
            out.append(f"SDTEST pos step={n} x={x} y={y} z=0 sector={s if s is not None else -1} "
                       f"angle=0 health=100")
        out.append(f"SDSTEP {len(self.r.steps)} END")
        if exit_ and self.r.must_exit:
            if self.r.exit_by == "switch":
                out.append("SDTEST line index=386 special=243 arg0=0 front=163 back=-1 type=2 player=1")
            else:
                out.append(f"SDTEST exitlevel map={self.r.map_name}")
            kills = sum(1 for c in self.cleared if c[5] == 1)
            out.append(f"SDTEST unloaded map={self.r.map_name} next={self.next_map} kills={kills}/{md.monsters_on(self.skill)} "
                       f"secrets=0/{secrets} items=0/40 time=4000")
            if self.end_state is not None:
                out.append(f"SDTEST state gamestate={self.end_state}")
        return "\n".join(out) + "\n"

    def _tag_sectors(self, tag):
        found = [i for i, s in enumerate(self.md.textmap.sectors) if s.identifier == tag]
        return found or [0]


class ParseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = {name: route.MapData(name) for name in (ZARYA, RANGE, METRO, FACTORY)}

    def judge(self, name, skill, **kw):
        r = route.route_by_name(name)
        fake = FakeRun(r, skill, self.data[r.map_name])
        overrides = kw.pop("overrides", {})
        fake.overrides.update(overrides)
        for key, value in kw.pop("attrs", {}).items():
            setattr(fake, key, value)
        log = route.scan_route_log(fake.text(**kw))
        return route.evaluate(r, skill, log, self.data[r.map_name])

    def test_a_clean_run_passes_on_skills_2_3_and_4(self):
        for skill in (2, 3, 4):
            rep = self.judge("g3-auto", skill)
            self.assertTrue(rep.passed, f"skill {skill}: {rep.problems}")
            self.assertTrue(rep.exit_reached)
            self.assertTrue(rep.log.god, "the engine's god message was not recognised")
            self.assertEqual([("A0", True), ("R1", True), ("A4", True), ("A7", True)],
                             [(w, ok) for w, ok, _d in rep.inventory])
            self.assertIn("PASS", route.render_report(rep))

    def test_a_clean_mural_run_passes(self):
        rep = self.judge("mural", 3)
        self.assertTrue(rep.passed, rep.problems)
        self.assertEqual(len(route.ROUTES["mural"].steps), len(rep.log.captures))

    def test_a_clean_run_passes_on_range(self):
        rep = self.judge("range-start", 3)
        self.assertTrue(rep.passed, rep.problems)
        self.assertEqual(14, rep.monsters_expected)

    def test_slot_1_owned_at_the_start_fails(self):
        both = [("SD_Melee1", 1), ("SD_Pistol2", 2)]
        rep = self.judge("g3-auto", 3, overrides={0: (both, "SD_Pistol2", 2, 50)})
        self.assertFalse(rep.passed)
        self.assertTrue(any("A0" in p and "slot 1" in p for p in rep.problems), rep.problems)

    def test_no_pickup_at_the_rack_fails(self):
        alone = [("SD_Pistol2", 2)]
        rep = self.judge("g3-auto", 4, overrides={1: (alone, "SD_Pistol2", 2, 50)})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith("R1:") and "slot 1 empty" in p for p in rep.problems),
                        rep.problems)

    def test_the_wrong_weapon_raised_at_the_start_fails(self):
        rep = self.judge("g3-auto", 2, overrides={0: ([("SD_Melee1", 1)], "SD_Melee1", 1, -1)})
        self.assertFalse(rep.passed)
        self.assertTrue(any("raised weapon in slot 1" in p for p in rep.problems), rep.problems)

    def test_the_wrong_starting_rounds_fail(self):
        rep = self.judge("range-start", 3, overrides={0: ([("SD_Pistol2", 2)], "SD_Pistol2", 2, 0)})
        self.assertFalse(rep.passed)
        self.assertTrue(any("0 rounds, wanted 50" in p for p in rep.problems), rep.problems)

    def test_no_inventory_reported_fails(self):
        rep = self.judge("g3-auto", 3, drop={("inv", 0)})
        self.assertFalse(rep.passed)
        self.assertTrue(any("A0: inventory not reported" in p for p in rep.problems), rep.problems)

    def test_a_shut_gate_fails(self):
        rep = self.judge("g3-auto", 3, shut_tags={route.MAP01_TAG_D4})
        self.assertFalse(rep.passed)
        self.assertTrue(any(f"tag {route.MAP01_TAG_D4}" in p for p in rep.problems), rep.problems)

    def test_no_exit_fails(self):
        rep = self.judge("g3-auto", 4, exit_=False)
        self.assertFalse(rep.passed)
        self.assertFalse(rep.exit_reached)

    def test_the_parse_flag_and_its_exit_codes(self):
        r = route.ROUTES["g3-auto"]
        fake = FakeRun(r, 4, self.data[ZARYA])
        with tempfile.TemporaryDirectory() as tmp, no_engine():
            good, bad, broken = (Path(tmp) / n for n in ("good.log", "bad.log", "broken.log"))
            good.write_text(fake.text(), encoding="utf-8")
            bad.write_text(fake.text(exit_=False), encoding="utf-8")
            broken.write_text(fake.text(extra=['Script error, "sovietdoom.pk3:zscript.txt" line 3:']),
                              encoding="utf-8")
            code, out, _ = run_main(["--parse", str(good), "--skill", "4"])
            self.assertEqual(route.EXIT_OK, code, out)
            self.assertIn("VERDICT        : PASS", out)
            self.assertIn("inventory (by slot):", out)
            code, out, _ = run_main(["--parse", str(bad), "--skill", "4"])
            self.assertEqual(route.EXIT_ROUTE_FAILED, code)
            code, out, _ = run_main(["--parse", str(broken), "--skill", "4"])
            self.assertEqual(route.EXIT_LOG_FAILURES, code)
            self.assertIn("script-error", out)

    # --- blockers in a scripted walk (PM's run, 2026-10-13 20:36) --------
    def test_a_blocker_in_a_walk_is_killed_and_reported_not_hidden(self):
        """Skills 3 and 4 failed at A1 only: a Stormtrooper stood in the
        Z1-Z3 corridor. sdclear kills it; the run passes, and the report
        says so in three places: the blockers list, the kill count and the
        verdict."""
        a1 = [s.id for s in route.ROUTES["g3-auto"].steps].index("A1")
        rep = self.judge("g3-auto", 3, attrs={"cleared": [(a1, "SD_Stormtrooper", 256, 610, 60, 1)]})
        self.assertTrue(rep.passed, rep.problems)
        text = route.render_report(rep)
        self.assertIn("blockers       : 1 killed by the route's sdclear", text)
        self.assertIn("[ok ] A1: SD_Stormtrooper at (256, 610), 60 hp, dead", text)
        self.assertIn("kills          : 1 of 33, of which 1 by the route's sdclear", text)
        self.assertIn("VERDICT        : PASS (1 blocker(s) killed by the route", text)

    def test_a_clean_run_says_no_blocker(self):
        text = route.render_report(self.judge("g3-auto", 2))
        self.assertIn("blockers       : none", text)
        self.assertTrue(text.endswith("VERDICT        : PASS"), text[-80:])

    def test_a_blocker_that_survives_fails(self):
        a1 = [s.id for s in route.ROUTES["g3-auto"].steps].index("A1")
        rep = self.judge("g3-auto", 4, attrs={"cleared": [(a1, "SD_Panzermensch", 256, 610, 500, 0)]})
        self.assertFalse(rep.passed)
        self.assertTrue(any("A1: blocker SD_Panzermensch" in p and "survived" in p
                            for p in rep.problems), rep.problems)

    # --- the god line, both spellings -----------------------------------
    def test_both_god_lines_are_recognised(self):
        for line in ("God mode on.", "Degreelessness Mode ON"):
            rep = self.judge("g3-auto", 3, attrs={"god_line": line})
            self.assertTrue(rep.log.god, line)
        rep = self.judge("g3-auto", 3, attrs={"god_line": "Buddha mode ON"})
        self.assertFalse(rep.log.god)

    # --- how a level ends -------------------------------------------------
    def test_range_ends_by_its_switch_into_its_end_text(self):
        rep = self.judge("range-start", 3)
        self.assertTrue(rep.passed, rep.problems)
        self.assertTrue(rep.exit_reached)
        self.assertIn("exit switch pressed: yes", rep.exit_detail)
        self.assertIn("after it: end text", rep.exit_detail)
        self.assertEqual(["A0", "R1", "E0"], [r.step.id for r in rep.steps if r.pos and r.step.expect])
        self.assertIn("HALL -> EXIT", route.render_report(rep))

    def test_range_without_its_exit_fails(self):
        rep = self.judge("range-start", 3, exit_=False)
        self.assertFalse(rep.passed)
        self.assertIn("exit switch pressed: NO", rep.exit_detail)

    def test_range_ended_by_sdexit_fails(self):
        """The switch is the exit now: sdexit on RANGE is not leaving it."""
        r = route.ROUTES["range-start"]
        fake = FakeRun(r, 3, self.data[RANGE])
        text = fake.text(exit_=False) + ("SDTEST exitlevel map=RANGE\n"
                                         "SDTEST unloaded map=RANGE next=enDSeQ1dce kills=0/14 "
                                         "secrets=0/0 items=0/0 time=208\n")
        rep = route.evaluate(r, 3, route.scan_route_log(text), self.data[RANGE])
        self.assertFalse(rep.passed)
        self.assertIn("the level was ended by sdexit, not by its exit switch", rep.problems)

    def test_the_post_exit_state_unseen_is_reported_not_failed(self):
        """Every engine run so far (20:36-20:52): no `SDTEST state` line after
        the exit. The unload line is enough; the report points at the shot."""
        rep = self.judge("range-start", 3, attrs={"end_state": None})
        self.assertTrue(rep.passed, rep.problems)
        self.assertIn("after it: " + route.AFTER_NOT_SEEN, rep.exit_detail)
        self.assertIn("judge the END shot", route.render_report(rep))

    def test_a_clean_p4_run_passes_and_a_door_that_stays_shut_fails(self):
        rep = self.judge("range-door", 3)
        self.assertTrue(rep.passed, rep.problems)
        self.assertIn(f"tag {route.RANGE_TAG_GALLERY_DOOR} at P4b: want open", route.render_report(rep))
        self.assertIn("walk-through at P4b", route.render_report(rep))
        rep = self.judge("range-door", 4, shut_tags={route.RANGE_TAG_GALLERY_DOOR})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith("P4b: tag 1") for p in rep.problems), rep.problems)

    def test_a_json_route_ended_by_sdexit_passes(self):
        r = route.route_from_json({"name": "noexit", "map": "RANGE", "exit_by": "console",
                                   "end_sequence": True,
                                   "steps": [{"id": "A0", "do": ["capture"]},
                                             {"id": "E1", "do": ["exit", "capture"]}]})
        fake = FakeRun(r, 3, self.data[RANGE])
        rep = route.evaluate(r, 3, route.scan_route_log(fake.text()), self.data[RANGE])
        self.assertTrue(rep.passed, rep.problems)
        self.assertIn("ended by sdexit: yes", rep.exit_detail)

    def test_a_console_exit_does_not_finish_map01(self):
        """G3-4 asks for the exit switch: sdexit on MAP01 is not an exit."""
        r = route.ROUTES["g3-auto"]
        fake = FakeRun(r, 3, self.data[ZARYA])
        text = fake.text(exit_=False) + ("SDTEST exitlevel map=MAP01\n"
                                         "SDTEST unloaded map=MAP01 next=enDSeQ1dce kills=0/33 "
                                         "secrets=0/3 items=0/26 time=900\n")
        rep = route.evaluate(r, 3, route.scan_route_log(text), self.data[ZARYA])
        self.assertFalse(rep.passed)
        self.assertFalse(rep.exit_reached)
        self.assertIn("the level was ended by sdexit, not by its exit switch", rep.problems)

    def test_an_exit_that_leads_to_a_map_not_an_end_sequence_fails(self):
        """The range ends the game (its own end text): leading to a map is wrong."""
        self.assertTrue(route.ROUTES["range-start"].end_sequence)
        rep = self.judge("range-start", 2, attrs={"next_map": ZARYA})
        self.assertFalse(rep.passed)
        self.assertTrue(any("not to an end sequence" in p for p in rep.problems), rep.problems)

    def test_the_pms_real_lines_parse(self):
        """Lines copied from the PM's skill-3 log of 2026-10-13 20:36."""
        log = route.scan_route_log(
            "SDTEST helper route-1 map=MAP01\nGod mode on.\nSDSTEP 0 A0\n"
            "SDTEST level map=MAP01 monsters=0/33 secrets=0/3 items=0/26 time=143\n"
            "SDTEST weapon class=SD_Tokarev slot=2\n"
            "SDTEST inv weapons=1 ready=SD_Tokarev slot=2 ammo=50\n"
            "Captured Screenshot_Doom_20261013_203633.png\n"
            "SDTEST pos step=0 x=252 y=85 z=0 sector=0 angle=90 health=91\n"
            "SDSTEP 13 A12\n"
            "SDTEST line index=386 special=243 arg0=0 front=163 back=-1 type=2 player=1\n"
            "SDTEST unloaded map=MAP01 next=enDSeQ1dce kills=1/21 secrets=0/3 items=2/26 time=1045\n")
        self.assertEqual("route-1", log.helper)
        self.assertTrue(log.god)
        self.assertEqual(33, log.levels[0][2])
        self.assertEqual(50, log.inventory[0].ammo)
        self.assertEqual("enDSeQ1dce", log.unloaded[0][1])
        self.assertTrue(log.unloaded[0][1].startswith(route.END_SEQUENCE_PREFIX))

    # The helper lines of the PM's map02-door log (range-door since D62),
    # 2026-10-13 21:15 on 87d613b
    # (docs/qa/evidence/2026-10-13_2115_F3_g3-map02-map02-door-skill3.log):
    # P4 passes, E0 glides out of line with the alcove and ends in the hall.
    # Verbatim: the log predates D62, when the range was the lump MAP02.
    PM_RANGE_DOOR_2115 = """\
SDTEST helper route-2 map=MAP02
God mode on.
SDSTEP 0 A0
SDTEST level map=MAP02 monsters=0/14 secrets=0/0 items=0/0 time=143
SDTEST weapon class=SD_Tokarev slot=2
SDTEST inv weapons=1 ready=SD_Tokarev slot=2 ammo=50
Captured Screenshot_Doom_20261013_211450.png
SDTEST pos step=0 x=140 y=384 z=0 sector=0 angle=0 health=85
SDSTEP 1 R1
SDTEST clear step=1 killed=0
An ice axe.
SDTEST weapon class=SD_IceAxe slot=1
SDTEST weapon class=SD_Tokarev slot=2
SDTEST inv weapons=2 ready=SD_IceAxe slot=1 ammo=-1
Captured Screenshot_Doom_20261013_211452.png
SDTEST pos step=1 x=288 y=751 z=0 sector=0 angle=90 health=85
SDSTEP 2 P4a
SDTEST tag 1 sector=2 floor=0 ceil=0
Captured Screenshot_Doom_20261013_211452_01.png
SDTEST pos step=2 x=672 y=864 z=0 sector=3 angle=270 health=85
SDSTEP 3 P4b
SDTEST line index=19 special=12 arg0=1 front=3 back=2 type=2 player=1
SDTEST tag 1 sector=2 floor=0 ceil=124
SDTEST clear step=3 killed=0
Captured Screenshot_Doom_20261013_211456.png
SDTEST pos step=3 x=672 y=630 z=0 sector=0 angle=270 health=85
SDSTEP 4 E0
Captured Screenshot_Doom_20261013_211456_01.png
SDTEST clear step=4 killed=0
Captured Screenshot_Doom_20261013_211458.png
SDTEST pos step=4 x=16 y=345 z=0 sector=0 angle=180 health=85
SDSTEP 5 E1
SDTEST state gamestate=0
Captured Screenshot_Doom_20261013_211506.png
SDTEST pos step=5 x=16 y=345 z=0 sector=0 angle=180 health=85
SDSTEP 6 END
Captured Screenshot_Doom_20261013_211508.png
SDTEST state gamestate=0
"""

    def test_the_pms_range_door_drift_is_caught_where_it_happened(self):
        """--parse on the real 21:15 log: P4 passes on both door readings
        and the walk-through; the run fails at E0 (in the hall, not the
        alcove) and therefore at the exit, and nowhere else."""
        with tempfile.TemporaryDirectory() as tmp, no_engine():
            log = Path(tmp) / "range-door-2115.log"
            log.write_text(self.PM_RANGE_DOOR_2115, encoding="utf-8")
            code, out, _ = run_main(["--parse", str(log), "--route", "range-door", "--skill", "3"])
        self.assertEqual(route.EXIT_ROUTE_FAILED, code, out)
        self.assertIn("[ok ] tag 1 at P4a: want shut: shut", out)
        self.assertIn("[ok ] tag 1 at P4b: want open: open", out)
        self.assertIn("[ok ] walk-through at P4b: ended in HALL (hall)", out)
        self.assertIn("[BAD] E0   expect EXIT", out)
        self.assertIn("got HALL hall @ (16, 345, 0)", out)
        problems = [l for l in out.splitlines() if l.startswith("PROBLEM")]
        self.assertEqual(2, len(problems), problems)
        self.assertIn("E0: ended in HALL (hall), expected EXIT", problems[0])
        self.assertIn("exit not reached: exit switch pressed: NO", problems[1])
        self.assertIn("VERDICT        : FAIL", out)
        # sdstate answers inside a level (gamestate 0): never read as an
        # intermission or an end text.
        rep = route.evaluate(route.ROUTES["range-door"], 3,
                             route.scan_route_log(self.PM_RANGE_DOOR_2115), self.data[RANGE])
        self.assertEqual([0, 0], rep.log.states)
        self.assertIn("after it: " + route.AFTER_NOT_SEEN, rep.exit_detail)

    def test_scan_judges_any_log_against_g3_2(self):
        clean = "GZDoom version g4.14.2\nMAP01 - Zarya-7\n"
        dirty = clean + "Texture SDNOPE1 not found\n"
        with tempfile.TemporaryDirectory() as tmp, no_engine():
            a, b = Path(tmp) / "a.log", Path(tmp) / "b.log"
            a.write_text(clean, encoding="utf-8")
            b.write_text(dirty, encoding="utf-8")
            code, out, _ = run_main(["--scan", str(a)])
            self.assertEqual(route.EXIT_OK, code, out)
            code, out, _ = run_main(["--scan", str(b)])
            self.assertEqual(route.EXIT_LOG_FAILURES, code)
            self.assertIn("SDNOPE1", out)
            code, _out, _ = run_main(["--scan", str(Path(tmp) / "missing.log")])
            self.assertEqual(route.EXIT_ROUTE_FAILED, code)

    def test_inventory_lines_belong_to_their_step(self):
        log = route.scan_route_log("SDSTEP 0 A0\nSDTEST weapon class=X slot=2\n"
                                   "SDTEST inv weapons=1 ready=X slot=2 ammo=50\n"
                                   "SDSTEP 1 R1\nSDTEST weapon class=Y slot=1\n"
                                   "SDTEST weapon class=X slot=2\n"
                                   "SDTEST inv weapons=2 ready=Y slot=1 ammo=-1\n")
        self.assertEqual({2}, log.inventory[0].slots())
        self.assertEqual({1, 2}, log.inventory[1].slots())
        self.assertEqual(("Y", 1, -1), (log.inventory[1].ready, log.inventory[1].ready_slot,
                                        log.inventory[1].ammo))

    # --- where the exit leads (D60: MAP01 -> the metro; MAPINFO says so) ----
    def test_map01_leading_to_mapinfos_next_map_passes(self):
        nxt = route.mapinfo_next(ZARYA)
        self.assertEqual((False, nxt), (route.ROUTES["g3-auto"].end_sequence,
                                       route.ROUTES["g3-auto"].next_map))
        self.assertEqual(nxt, route.ROUTES["g3-secrets"].next_map)
        rep = self.judge("g3-auto", 3, attrs={"next_map": nxt})
        self.assertTrue(rep.passed, rep.problems)
        self.assertIn(f"level unloaded towards: {nxt}", rep.exit_detail)
        # GZDoom's spelling of the lump may differ in case: not a failure.
        self.assertTrue(self.judge("g3-auto", 3, attrs={"next_map": nxt.lower()}).passed)

    def test_map01_leading_to_an_end_sequence_fails(self):
        """The old ending (before D60) is now wrong: MAP01 goes on to the metro."""
        rep = self.judge("g3-auto", 3, attrs={"next_map": "enDSeQ1dce"})
        self.assertFalse(rep.passed)
        self.assertIn(f"the level led to 'enDSeQ1dce', not to {route.mapinfo_next(ZARYA)} "
                      "(MAPINFO's next)", rep.problems)

    def test_map01_leading_to_another_map_fails(self):
        rep = self.judge("g3-auto", 4, attrs={"next_map": RANGE})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith(f"the level led to '{RANGE}'") for p in rep.problems))

    # --- MAP02: metro-critical ---------------------------------------------
    def m3(self, **kw):
        return self.judge("metro-critical", kw.pop("skill", 3), **kw)

    def test_a_clean_map02_run_passes_on_skills_2_3_and_4(self):
        for skill in (2, 3, 4):
            rep = self.m3(skill=skill)
            self.assertTrue(rep.passed, f"skill {skill}: {rep.problems}")
            self.assertTrue(rep.exit_reached)
            self.assertEqual(self.data[METRO].monsters_on(skill), rep.monsters_expected)
        text = route.render_report(rep)
        self.assertIn("keys [SD_BluePass]", text)
        self.assertIn("[ok ] press of special", text)
        self.assertEqual([("A0", True), ("BD0", True), ("PASS", True)],
                         [(w, ok) for w, ok, _d in rep.inventory])
        self.assertTrue(text.endswith("VERDICT        : PASS"), text[-80:])

    def test_map02_the_blue_door_opening_without_the_pass_fails(self):
        m = self.data[METRO].module
        rep = self.m3(attrs={"force_open": {(m.TAG_BLAST_DOOR, "BD0")}})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith(f"BD0: tag {m.TAG_BLAST_DOOR} is open") and "wanted shut" in p
                            for p in rep.problems), rep.problems)

    def test_map02_a_press_that_never_reached_the_blue_door_fails(self):
        """Shut because nobody pressed it is not shut because it is locked."""
        m = self.data[METRO].module
        rep = self.m3(attrs={"unpressed": {"BD0"}})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith(f"BD0: no press of special {m.SPECIAL_DOOR_LOCKED_RAISE}")
                            for p in rep.problems), rep.problems)

    def test_map02_the_lock_message_also_proves_the_press(self):
        """If a locked press prints no SDTEST line (NOT VERIFIED either way),
        the engine's lock message at that step is the evidence."""
        rep = self.m3(attrs={"unpressed": {"BD0"},
                             "step_extra": {"BD0": ["You need a blue pass to activate this object"]}})
        self.assertTrue(rep.passed, rep.problems)
        self.assertIn("BD0: You need a blue pass", route.render_report(rep))
        # A pickup line is not a lock message.
        rep = self.m3(attrs={"unpressed": {"BD0"}, "step_extra": {"BD0": ["Blue pass."]}})
        self.assertFalse(rep.passed)

    def test_map02_the_pass_not_picked_up_fails(self):
        rep = self.m3(attrs={"key_gains": []})
        self.assertFalse(rep.passed)
        self.assertIn("PASS: no key owned", rep.problems)

    def test_map02_a_key_before_the_pass_fails(self):
        rep = self.m3(attrs={"key_gains": [0]})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith("A0: a key already owned") for p in rep.problems), rep.problems)

    def test_map02_a_route3_log_cannot_prove_the_pass(self):
        rep = self.m3(attrs={"old_helper": True})
        self.assertFalse(rep.passed)
        self.assertIn("PASS: keys not reported (a helper older than route-4)", rep.problems)

    def test_map02_a_shut_gate_means_no_exit(self):
        """SW-B's gate stays shut: E0 stops in the west tunnel, the switch is
        never pressed, and the report says both."""
        m = self.data[METRO].module
        rep = self.m3(shut_tags={m.TAG_GATE}, exit_=False, attrs={"pos_override": {"E0": ("Z7",)}})
        self.assertFalse(rep.passed)
        self.assertFalse(rep.exit_reached)
        self.assertTrue(any(p.startswith(f"SWB: tag {m.TAG_GATE} is shut") for p in rep.problems))
        self.assertTrue(any(p.startswith("E0: ended in Z7") for p in rep.problems), rep.problems)
        self.assertTrue(any(p.startswith("exit not reached: exit switch pressed: NO")
                            for p in rep.problems), rep.problems)

    def test_map02_exit_not_reached_fails_with_exit_code_9(self):
        r = route.route_by_name("metro-critical")
        fake = FakeRun(r, 3, self.data[METRO])
        with tempfile.TemporaryDirectory() as tmp, no_engine():
            good, bad = Path(tmp) / "good.log", Path(tmp) / "bad.log"
            good.write_text(fake.text(), encoding="utf-8")
            bad.write_text(fake.text(exit_=False), encoding="utf-8")
            code, out, _ = run_main(["--parse", str(good), "--route", "metro-critical", "--skill", "3"])
            self.assertEqual(route.EXIT_OK, code, out)
            code, out, _ = run_main(["--parse", str(bad), "--route", "metro-critical", "--skill", "3"])
        self.assertEqual(route.EXIT_ROUTE_FAILED, code)
        self.assertIn("exit           : NOT REACHED", out)

    # --- MAP03: tankograd-critical -----------------------------------------
    def tk(self, **kw):
        return self.judge("tankograd-critical", kw.pop("skill", 3), **kw)

    def test_a_clean_map03_run_passes_on_skills_2_3_and_4_into_the_end_sequence(self):
        md = self.data[FACTORY]
        for skill in (2, 3, 4):
            rep = self.tk(skill=skill)
            self.assertTrue(rep.passed, f"skill {skill}: {rep.problems}")
            self.assertTrue(rep.exit_reached)
            self.assertEqual(md.module.ENEMY_TOTALS[skill], rep.monsters_expected, f"skill {skill}")
        self.assertTrue(rep.route.end_sequence)
        self.assertIn("level unloaded towards: enDSeQ", rep.exit_detail)
        text = route.render_report(rep)
        # The keys counted 0, 1, 2 and reported by class (Doom's cards today).
        self.assertEqual([("A0", True), ("YD0", True), ("RD0", True), ("YKEY", True), ("RDY", True),
                          ("RKEY", True)], [(w, ok) for w, ok, _d in rep.inventory])
        self.assertIn("keys [none]", text)
        self.assertIn("keys [YellowCard]", text)
        self.assertIn("keys [YellowCard, RedCard]", text)
        presses = [w for w, ok, _d in rep.doors if w.startswith("press of") and ok]
        self.assertEqual(7, len(presses), presses)       # YD0 RD0 YD1 RDY RD1 SWA SWB
        self.assertTrue(text.endswith("VERDICT        : PASS"), text[-80:])

    def test_map03_a_door_that_opens_without_its_key_fails(self):
        """The yellow door with no key, the red with no key, the red with the
        yellow key alone: each must stay shut, and the report names the step."""
        m = self.data[FACTORY].module
        for tag, sid, keys in ((m.TAG_YELLOW_DOOR, "YD0", "none"), (m.TAG_RED_DOOR, "RD0", "none"),
                               (m.TAG_RED_DOOR, "RDY", "YellowCard")):
            with self.subTest(sid):
                rep = self.tk(attrs={"force_open": {(tag, sid)}})
                self.assertFalse(rep.passed)
                self.assertTrue(any(p.startswith(f"{sid}: tag {tag} is open") and "wanted shut" in p
                                    for p in rep.problems), rep.problems)
                self.assertEqual(1, len(rep.problems), rep.problems)
                inv = {w: d for w, _ok, d in rep.inventory}
                self.assertIn(f"keys [{keys}]", inv[sid])

    def test_map03_a_press_that_never_reached_a_lock_fails_unless_the_engine_said_so(self):
        m = self.data[FACTORY].module
        rep = self.tk(attrs={"unpressed": {"YD0"}})
        self.assertFalse(rep.passed)
        self.assertTrue(any(p.startswith(f"YD0: no press of special {m.SPECIAL_DOOR_LOCKED_RAISE} "
                                         f"(arg0 {m.TAG_YELLOW_DOOR})") for p in rep.problems), rep.problems)
        # The lock line, in GZDoom's words or Freedoom's (NOT VERIFIED which).
        for sid, said in (("YD0", "You need a yellow key to open this door"),
                          ("RDY", "Red passcard needed for this door.")):
            rep = self.tk(attrs={"unpressed": {sid}, "step_extra": {sid: [said]}})
            self.assertTrue(rep.passed, (said, rep.problems))
        # A pickup line is not a lock message.
        rep = self.tk(attrs={"unpressed": {"RDY"}, "step_extra": {"RDY": ["Picked up a yellow keycard."]}})
        self.assertFalse(rep.passed)

    def test_map03_a_key_not_picked_up_fails(self):
        steps = [s.id for s in route.route_by_name("tankograd-critical").steps]
        rep = self.tk(attrs={"key_gains": [steps.index("YKEY")]})
        self.assertFalse(rep.passed)
        self.assertIn("RKEY: 1 key(s) owned (YellowCard), wanted 2", rep.problems)
        rep = self.tk(attrs={"key_gains": []})
        self.assertIn("YKEY: 0 key(s) owned (none), wanted 1", rep.problems)
        rep = self.tk(attrs={"old_helper": True})
        self.assertIn("YKEY: keys not reported (a helper older than route-4)", rep.problems)

    def test_map03_a_shut_gate_means_no_exit(self):
        m = self.data[FACTORY].module
        rep = self.tk(shut_tags={m.TAG_GATE}, exit_=False, attrs={"pos_override": {"E0": ("PH",)}})
        self.assertFalse(rep.passed)
        self.assertFalse(rep.exit_reached)
        self.assertTrue(any(p.startswith(f"SWB: tag {m.TAG_GATE} is shut") for p in rep.problems))
        self.assertTrue(any(p.startswith("E0: ended in PH") for p in rep.problems), rep.problems)
        self.assertTrue(any(p.startswith("exit not reached: exit switch pressed: NO")
                            for p in rep.problems), rep.problems)

    def test_map03_exit_not_reached_fails_with_exit_code_9(self):
        r = route.route_by_name("tankograd-critical")
        fake = FakeRun(r, 3, self.data[FACTORY])
        with tempfile.TemporaryDirectory() as tmp, no_engine():
            good, bad = Path(tmp) / "good.log", Path(tmp) / "bad.log"
            good.write_text(fake.text(), encoding="utf-8")
            bad.write_text(fake.text(exit_=False), encoding="utf-8")
            code, out, _ = run_main(["--parse", str(good), "--route", "tankograd-critical", "--skill", "3"])
            self.assertEqual(route.EXIT_OK, code, out)
            self.assertIn("exit           : REACHED", out)
            code, out, _ = run_main(["--parse", str(bad), "--route", "tankograd-critical", "--skill", "3"])
        self.assertEqual(route.EXIT_ROUTE_FAILED, code)
        self.assertIn("exit           : NOT REACHED", out)
        self.assertIn("VERDICT        : FAIL", out)

    def test_map03_an_exit_that_leads_to_a_map_not_the_episodes_end_fails(self):
        """MAP03 closes the episode (MAPINFO: next = endtitle): leaving it for
        a map, any map, is a failure even with the breaker pressed."""
        rep = self.tk(attrs={"next_map": ZARYA})
        self.assertFalse(rep.passed)
        self.assertTrue(rep.exit_reached)
        self.assertIn(f"the level led to '{ZARYA}', not to an end sequence", rep.problems)

    def test_key_lines_parse_and_an_old_inv_line_has_no_key_count(self):
        log = route.scan_route_log("SDSTEP 0 A0\nSDTEST inv weapons=1 ready=X slot=2 ammo=50\n"
                                   "SDSTEP 1 PASS\nSDTEST key class=SD_BluePass\n"
                                   "SDTEST weapon class=X slot=2\n"
                                   "SDTEST inv weapons=1 ready=X slot=2 ammo=50 keys=1\n"
                                   "SDTEST line index=7 special=13 arg0=4 front=1 back=2 type=2 player=1\n")
        self.assertEqual((None, []), (log.inventory[0].key_count, log.inventory[0].keys))
        self.assertEqual((1, ["SD_BluePass"]), (log.inventory[1].key_count, log.inventory[1].keys))
        self.assertEqual({2}, log.inventory[1].slots())
        self.assertEqual(1, log.lines[0].step)


# ============================================================================
# MAP02: metro-critical, read off the built map
# ============================================================================

def model_walk(tics: int) -> float:
    """Units covered by +forward from rest in `tics`, on Doom's constants
    (thrust 0.78 u/tic^2, friction 0.90625; route.ACCEL_TICS). A model, NOT
    a measurement."""
    friction = 0.90625
    top = 25 * 2048 / 65536 / (1 - friction)
    return top * (tics - friction * (1 - friction ** tics) / (1 - friction))


class BuiltMapRoute:
    """Geometry helpers for a route read off a built map (`self.md`)."""

    def tics(self, step):
        return int([a for a in step.actions if a.startswith("forward")][0].split()[1])

    def line_ahead(self, point, angle):
        """The nearest line straight ahead of `point` facing `angle`, and its distance."""
        md, tm = self.md, self.md.textmap
        x, y = point
        dx, dy = route.COMPASS[angle]
        ahead = []
        for ld in tm.linedefs:
            (x1, y1), (x2, y2) = route.line_ends(md, ld)
            if dx and x1 == x2 and min(y1, y2) < y < max(y1, y2) and (x1 - x) * dx > 0:
                ahead.append(((x1 - x) * dx, ld))
            if dy and y1 == y2 and min(x1, x2) < x < max(x1, x2) and (y1 - y) * dy > 0:
                ahead.append(((y1 - y) * dy, ld))
        self.assertTrue(ahead, f"no line ahead of {point} facing {angle}")
        return min(ahead, key=lambda a: a[0])

    def clear_of_walls(self, point):
        """The body fits: every corner on the same floor of the same zone (a
        rail strip under one corner is still the tunnel), none in a wall."""
        md = self.md
        here = md.sector_at(*point)
        self.assertIsNotNone(here, point)
        family = route.zone_family(md.name_of(here))
        floor = md.textmap.sectors[here].heightfloor
        for ox in (-PLAYER_RADIUS + 1, PLAYER_RADIUS - 1):
            for oy in (-PLAYER_RADIUS + 1, PLAYER_RADIUS - 1):
                s = md.sector_at(point[0] + ox, point[1] + oy)
                self.assertIsNotNone(s, f"the body at {point} is in a wall")
                self.assertEqual(family, route.zone_family(md.name_of(s)), f"the body at {point}")
                self.assertEqual(floor, md.textmap.sectors[s].heightfloor, f"the body at {point}")
        return here

    def walk(self, start, angle, length):
        dx, dy = route.COMPASS[angle]
        return [self.md.sector_at(start[0] + dx * d, start[1] + dy * d)
                for d in range(0, int(length) + 1, SAMPLE)]


class MetroRouteTest(BuiltMapRoute, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.md = route.load_map_data(METRO)
        cls.m = cls.md.module
        cls.r = route.route_by_name("metro-critical")
        cls.steps = {s.id: s for s in cls.r.steps}

    def test_it_is_built_lazily_and_offered_everywhere(self):
        self.assertNotIn("metro-critical", route.ROUTES, "built at import: a broken MAP02 would break MAP01")
        self.assertIn("metro-critical", route.route_names())
        self.assertEqual("metro-critical", route.parse_args(["--route", "metro-critical"]).route)
        self.assertEqual(METRO, self.r.map_name)

    def test_the_order_is_the_critical_path(self):
        self.assertEqual(["A0", "BD0", "PASS", "BD1", "SWA", "SWB", "E0", "E1"],
                         [s.id for s in self.r.steps])
        self.assertEqual(("switch", False, True, 0),
                         (self.r.exit_by, self.r.end_sequence, self.r.must_exit, self.r.expect_secrets))

    def test_mapinfo_leads_the_metro_into_the_factory(self):
        """D62: the metro no longer ends the episode; its exit must lead to
        MAPINFO's next map, the factory (MAP03), and the route expects that."""
        text = route.MAPINFO_PATH.read_text(encoding="utf-8")
        block = re.search(rf"^map {METRO}\b.*?^}}", text, re.M | re.S).group(0)
        self.assertRegex(block, r'(?m)^\s*next\s*=\s*"MAP03"')
        self.assertEqual((False, "MAP03"), (self.r.end_sequence, self.r.next_map))

    def test_tags_and_specials_are_map_py_constants(self):
        m, s = self.m, self.steps
        bd, sh, gate = m.TAG_BLAST_DOOR, m.TAG_SHUTTER, m.TAG_GATE
        self.assertEqual(((bd, False),), s["BD0"].tags)
        self.assertEqual(((bd, True),), s["BD1"].tags)
        self.assertEqual(((m.SPECIAL_DOOR_LOCKED_RAISE, bd),), s["BD0"].presses)
        self.assertEqual(s["BD0"].presses, s["BD1"].presses)
        self.assertEqual(((sh, False),), s["PASS"].tags)
        self.assertEqual(((sh, True), (gate, False)), s["SWA"].tags)
        self.assertEqual(((gate, True),), s["SWB"].tags)
        self.assertEqual(((udmf.SPECIAL_DOOR_OPEN, sh),), s["SWA"].presses)
        self.assertEqual(((udmf.SPECIAL_DOOR_OPEN, gate),), s["SWB"].presses)
        self.assertEqual((False, False, True), (s["A0"].key, s["BD0"].key, s["PASS"].key))

    def test_no_map02_position_is_written_in_route_py(self):
        """Every warp comes from the built map: none is a literal in the source,
        and the pass is never named (it is found by DoomEdNum, owned as a Key)."""
        source = Path(route.__file__).read_text(encoding="utf-8")
        for step in self.r.steps:
            if step.warp is None:
                continue
            x, y = step.warp
            self.assertNotIn(f"({x}, {y})", source, step.id)
            self.assertNotIn(f"{x} {y}", source, step.id)
        for literal in ('"KEY_SPOT"', '"SD_BluePass"', '"BlueCard"'):
            self.assertNotIn(literal, source)

    def test_the_zones_are_the_designs(self):
        """docs/levels/MAP02-metro.md section 4: start in the lift, the blue door
        from the hall's portal, the pass in the substation (its booth since
        v1), the gas lock behind the door, SW-A in the substation, SW-B in the
        command post, the exit in Z9."""
        want = {"A0": ("Z1",), "BD0": ("Z3",), "PASS": ("Z8",), "BD1": ("B1",), "SWA": ("Z8",),
                "SWB": ("B4",), "E0": ("Z9",)}
        self.assertEqual(want, {k: v.expect for k, v in self.steps.items() if v.expect})
        if hasattr(self.m, "KEY_ZONE"):
            self.assertEqual(self.steps["PASS"].expect, (route.zone_family(self.m.KEY_ZONE),))

    def test_the_blue_door_is_pressed_from_the_hall_within_reach(self):
        md, tm, m = self.md, self.md.textmap, self.m
        bd0, bd1 = self.steps["BD0"], self.steps["BD1"]
        self.assertEqual((bd0.warp, bd0.angle), (bd1.warp, bd1.angle))
        here = self.clear_of_walls(bd0.warp)
        dist, ld = self.line_ahead(bd0.warp, bd0.angle)
        self.assertLessEqual(dist, USE_RANGE)
        self.assertEqual((m.SPECIAL_DOOR_LOCKED_RAISE, m.TAG_BLAST_DOOR, m.LOCK_BLUE_CARD),
                         (ld.special, ld.arg0, ld.arg3))
        self.assertIn("playeruse", ld.flags)
        self.assertEqual(here, tm.sidedefs[ld.sidefront].sector, "pressed from the back face")
        door = tm.sidedefs[ld.sideback].sector
        self.assertEqual(m.TAG_BLAST_DOOR, tm.sectors[door].identifier)
        # BD1's walk: hall, door, the room behind; long enough on the model.
        crossed = self.walk(bd1.warp, bd1.angle, self.tics(bd1) * WALK_UNITS_PER_TIC)
        families = [route.zone_family(md.name_of(s)) for s in crossed if s is not None]
        self.assertEqual(["Z3", "BD", "B1"], list(dict.fromkeys(families))[:3])
        inside = next(i for i, s in enumerate(crossed)
                      if s is not None and route.zone_family(md.name_of(s)) == "B1")
        self.assertGreaterEqual(model_walk(self.tics(bd1)), inside * SAMPLE + PLAYER_RADIUS)

    def test_the_pass_is_walked_onto_never_given(self):
        md, m = self.md, self.m
        step = self.steps["PASS"]
        for skill in (2, 3, 4):
            self.assertEqual(1, len(md.things_on(m.ED_BLUE_CARD, skill)), f"skill {skill}")
        thing = md.things_on(m.ED_BLUE_CARD, 3)[0]
        start = step.warp
        self.clear_of_walls(start)
        dx, dy = route.COMPASS[step.angle]
        gap = (thing.x - start[0]) * dx + (thing.y - start[1]) * dy
        self.assertEqual(0, (thing.x - start[0]) * dy - (thing.y - start[1]) * dx, "the pass is off the lane")
        self.assertGreater(gap, PLAYER_RADIUS + PICKUP_RADIUS, "the warp lands on the pass")
        self.assertGreaterEqual(model_walk(self.tics(step)), gap, "the walk stops short of the pass")
        floor = md.textmap.sectors[md.sector_at(*start)].heightfloor
        for s in self.walk(start, step.angle, gap):
            self.assertEqual("Z8", route.zone_family(md.name_of(s)), md.name_of(s))
            self.assertLessEqual(md.textmap.sectors[s].heightfloor - floor, MAX_STEP_UP)
        for name, r in route.all_routes().items():
            for c in route.route_commands(r):
                self.assertNotIn(c.split()[0], ("give", "summon"), (name, c))

    def test_a_moved_pass_is_followed(self):
        """v1 may move the pass: the route finds it by DoomEdNum, wherever it lies."""
        md = route.MapData(METRO)      # a private copy: the cached one stays as built
        m = md.module
        sub = md.plan["z8_substation"]
        verts = {(v.x, v.y) for ld in md.textmap.linedefs for side in (ld.sidefront, ld.sideback)
                 if side is not None and md.textmap.sidedefs[side].sector == sub
                 for v in (md.textmap.vertices[ld.v1], md.textmap.vertices[ld.v2])}
        spot = (int(sum(x for x, _ in verts) / len(verts)) // 16 * 16,
                int(sum(y for _, y in verts) / len(verts)) // 16 * 16)
        self.assertEqual(sub, md.sector_at(*spot))
        thing = [t for t in md.textmap.things if t.type == m.ED_BLUE_CARD][0]
        self.assertNotEqual((thing.x, thing.y), spot)
        thing.x, thing.y = spot
        moved = {s.id: s for s in route.metro_critical(md).steps}["PASS"]
        dx, dy = route.COMPASS[moved.angle]
        self.assertEqual((spot[0] - dx * route.PASS_APPROACH, spot[1] - dy * route.PASS_APPROACH),
                         moved.warp)
        self.assertNotEqual(self.steps["PASS"].warp, moved.warp)
        # Two passes, or none, is not a route.
        md.textmap.things.append(type(thing)(x=spot[0] + 64, y=spot[1], type=m.ED_BLUE_CARD))
        with self.assertRaises(route.RouteError):
            route.metro_critical(md)
        md.textmap.things[:] = [t for t in md.textmap.things if t.type != m.ED_BLUE_CARD]
        with self.assertRaises(route.RouteError):
            route.metro_critical(md)

    def test_the_switches_are_pressed_from_their_faces(self):
        tm, m = self.md.textmap, self.m
        for sid, tag, face in (("SWA", m.TAG_SHUTTER, m.SW_A_FACE), ("SWB", m.TAG_GATE, m.SW_B_FACE)):
            step = self.steps[sid]
            here = self.clear_of_walls(step.warp)
            dist, ld = self.line_ahead(step.warp, step.angle)
            self.assertLessEqual(dist, USE_RANGE, sid)
            self.assertEqual((udmf.SPECIAL_DOOR_OPEN, tag), (ld.special, ld.arg0), sid)
            self.assertIsNone(ld.sideback, sid)
            self.assertEqual(here, tm.sidedefs[ld.sidefront].sector, sid)
            self.assertEqual(face, tm.sidedefs[ld.sidefront].texturemiddle, sid)

    def test_the_exit_walk_crosses_the_gate_and_ends_at_the_switch(self):
        md, tm, m = self.md, self.md.textmap, self.m
        e0, e1 = self.steps["E0"], self.steps["E1"]
        self.clear_of_walls(e0.warp)
        exits = [ld for ld in tm.linedefs if ld.special == route.SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_line = exits[0]
        self.assertEqual((m.EXIT_FACE, None), (tm.sidedefs[exit_line.sidefront].texturemiddle,
                                               exit_line.sideback))
        self.assertIn("playeruse", exit_line.flags)
        (x1, y1), _ = route.line_ends(md, exit_line)
        dx, dy = route.COMPASS[e0.angle]
        to_wall = (x1 - e0.warp[0]) * dx if dx else (y1 - e0.warp[1]) * dy
        walk = to_wall - PLAYER_RADIUS
        end = (e0.warp[0] + dx * walk, e0.warp[1] + dy * walk)
        crossed = self.walk(e0.warp, e0.angle, walk)
        self.assertNotIn(None, crossed)
        families = list(dict.fromkeys(route.zone_family(md.name_of(s)) for s in crossed))
        self.assertEqual(["Z7", "GATE", "Z9"], families)
        for s in crossed:
            if route.zone_family(md.name_of(s)) == "GATE":
                self.assertEqual(m.TAG_GATE, tm.sectors[s].identifier)
        self.assertEqual(tm.sidedefs[exit_line.sidefront].sector, md.sector_at(*end))
        dist, ahead = self.line_ahead(end, e0.angle)
        self.assertIs(exit_line, ahead, "the walk does not end against the exit switch")
        self.assertLessEqual(dist, USE_RANGE)
        self.assertGreaterEqual(model_walk(self.tics(e0)), walk)
        self.assertIsNone(e1.warp)
        self.assertEqual(("use",), e1.actions)

    def test_print_runs_on_map02(self):
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print", "--route", "metro-critical"])
        self.assertEqual(route.EXIT_OK, code)
        for skill in (2, 3, 4):
            self.assertIn(f"-skill {skill} +map {METRO}", out)
        self.assertIn(f"netevent sdtag {self.m.TAG_BLAST_DOOR}", out)
        self.assertNotIn("sdexit", out)
        self.assertNotRegex(out, r"(?m)^\s+give\b")


# ============================================================================
# MAP03: tankograd-critical, read off the built map
# ============================================================================

class TankogradRouteTest(BuiltMapRoute, unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.md = route.load_map_data(FACTORY)
        cls.m = cls.md.module
        cls.r = route.route_by_name("tankograd-critical")
        cls.steps = {s.id: s for s in cls.r.steps}

    def test_it_is_built_lazily_and_offered_everywhere(self):
        self.assertNotIn("tankograd-critical", route.ROUTES, "built at import: a broken MAP03 would break MAP01")
        self.assertIn("tankograd-critical", route.route_names())
        self.assertEqual("tankograd-critical", route.parse_args(["--route", "tankograd-critical"]).route)
        self.assertEqual(FACTORY, self.r.map_name)
        self.assertEqual("MAP03", FACTORY, "D62: the factory is the campaign's third slot")

    def test_the_order_is_the_briefs(self):
        """N2: both locks shut at first; the yellow key and door; the red key
        and door (and, between them, the red door refused on the yellow key);
        SW-A; SW-B; the breaker."""
        self.assertEqual(["A0", "YD0", "RD0", "YKEY", "YD1", "RDY", "RKEY", "RD1", "SWA", "SWB",
                          "E0", "E1"], [s.id for s in self.r.steps])
        self.assertEqual(("switch", True, 0), (self.r.exit_by, self.r.must_exit, self.r.expect_secrets))

    def test_mapinfo_makes_the_factorys_exit_the_episodes_end(self):
        text = route.MAPINFO_PATH.read_text(encoding="utf-8")
        block = re.search(rf"^map {FACTORY}\b.*?^}}", text, re.M | re.S).group(0)
        self.assertRegex(block, r"(?m)^\s*next\s*=\s*endtitle\b")
        self.assertEqual({"end_sequence": True, "next_map": None}, route.exit_expectation(FACTORY))
        self.assertEqual((True, None), (self.r.end_sequence, self.r.next_map))

    def test_the_keys_are_doom_cards_6_and_13_on_locks_3_and_1(self):
        """The brief: yellow 6, red 13, checked in map.py, and the doors carry
        the matching locks (gzdoom.pk3 lockdefs.txt: 3 YellowCard, 1 RedCard,
        as map.py cites it)."""
        m, tm = self.m, self.md.textmap
        self.assertEqual((6, 13), (m.ED_YELLOW_CARD, m.ED_RED_CARD))
        self.assertEqual((3, 1), (m.LOCK_YELLOW_CARD, m.LOCK_RED_CARD))
        self.assertEqual({6: 3, 13: 1}, m.KEY_LOCKS)
        for tag, lock in ((m.TAG_YELLOW_DOOR, m.LOCK_YELLOW_CARD), (m.TAG_RED_DOOR, m.LOCK_RED_CARD)):
            lines = [ld for ld in tm.linedefs if ld.special == m.SPECIAL_DOOR_LOCKED_RAISE and ld.arg0 == tag]
            self.assertEqual(2, len(lines), f"tag {tag}: a face each side")
            self.assertEqual({lock}, {ld.arg3 for ld in lines}, f"tag {tag}")

    def test_tags_specials_and_key_counts_are_map_py_constants(self):
        m, s = self.m, self.steps
        yd, rd, sh, gate, lk = (m.TAG_YELLOW_DOOR, m.TAG_RED_DOOR, m.TAG_SHUTTER, m.TAG_GATE,
                                m.SPECIAL_DOOR_LOCKED_RAISE)
        want_tags = {"YD0": ((yd, False),), "RD0": ((rd, False),), "YKEY": ((yd, False), (rd, False)),
                     "YD1": ((yd, True),), "RDY": ((rd, False),), "RKEY": ((rd, False), (sh, False)),
                     "RD1": ((rd, True),), "SWA": ((sh, True), (gate, False)), "SWB": ((gate, True),)}
        self.assertEqual(want_tags, {k: v.tags for k, v in s.items() if v.tags})
        want_presses = {"YD0": ((lk, yd),), "YD1": ((lk, yd),), "RD0": ((lk, rd),), "RDY": ((lk, rd),),
                        "RD1": ((lk, rd),), "SWA": ((udmf.SPECIAL_DOOR_OPEN, sh),),
                        "SWB": ((udmf.SPECIAL_DOOR_OPEN, gate),)}
        self.assertEqual(want_presses, {k: v.presses for k, v in s.items() if v.presses})
        self.assertEqual({"A0": 0, "YD0": 0, "RD0": 0, "YKEY": 1, "RDY": 1, "RKEY": 2},
                         {k: v.keys for k, v in s.items() if v.keys is not None})
        self.assertEqual(set(), {k for k, v in s.items() if v.key is not None}, "keys are counted here")

    def test_no_map03_position_or_key_class_is_written_in_route_py(self):
        source = Path(route.__file__).read_text(encoding="utf-8")
        for step in self.r.steps:
            if step.warp is None:
                continue
            x, y = step.warp
            self.assertNotIn(f"({x}, {y})", source, step.id)
            self.assertNotIn(f"{x} {y}", source, step.id)
        for literal in ('"YellowCard"', '"RedCard"', '"YELLOW_KEY_SPOT"', '"RED_KEY_SPOT"', '"o_desk"',
                        '"f_pedestal"'):
            self.assertNotIn(literal, source)

    def test_the_zones_are_the_designs(self):
        """docs/levels/MAP03-factory.md sections 4-5: start on the spur, both
        locks pressed from the hall, the yellow key in the offices, the tank
        line behind the yellow door, the red key and SW-A in the foundry, the
        portal hall behind the red door, SW-B in its booth, the breaker in
        the drum."""
        want = {"A0": ("Z1",), "YD0": ("Z3",), "RD0": ("Z3",), "YKEY": ("OF",), "YD1": ("TL",),
                "RDY": ("Z3",), "RKEY": ("FD",), "RD1": ("PH",), "SWA": ("FD",), "SWB": ("PH",),
                "E0": ("DR",)}
        self.assertEqual(want, {k: v.expect for k, v in self.steps.items() if v.expect})
        unfiled = sorted(n for n in self.md.plan if route.zone_family(n) == "?")
        self.assertEqual([], unfiled, "a MAP03 sector has no zone family")
        self.assertEqual(self.steps["YKEY"].expect,
                         (route.zone_family(self.m.KEY_ZONES[self.m.ED_YELLOW_CARD]),))
        self.assertEqual(self.steps["RKEY"].expect,
                         (route.zone_family(self.m.KEY_ZONES[self.m.ED_RED_CARD]),))

    def test_each_lock_is_pressed_from_the_hall_within_reach_and_walked_through(self):
        md, tm, m = self.md, self.md.textmap, self.m
        for presses, walk_id, tag, lock, door_family, inside in (
                (("YD0",), "YD1", m.TAG_YELLOW_DOOR, m.LOCK_YELLOW_CARD, "YD", "TL"),
                (("RD0", "RDY"), "RD1", m.TAG_RED_DOOR, m.LOCK_RED_CARD, "RD", "PH")):
            with self.subTest(walk_id):
                through = self.steps[walk_id]
                for sid in presses:
                    self.assertEqual((through.warp, through.angle),
                                     (self.steps[sid].warp, self.steps[sid].angle), sid)
                here = self.clear_of_walls(through.warp)
                dist, ld = self.line_ahead(through.warp, through.angle)
                self.assertLessEqual(dist, USE_RANGE)
                self.assertEqual((m.SPECIAL_DOOR_LOCKED_RAISE, tag, lock), (ld.special, ld.arg0, ld.arg3))
                self.assertIn("playeruse", ld.flags)
                self.assertEqual(here, tm.sidedefs[ld.sidefront].sector, "pressed from the back face")
                self.assertEqual(m.LOCK_PORTALS[lock], md.name_of(here))
                self.assertEqual(tag, tm.sectors[tm.sidedefs[ld.sideback].sector].identifier)
                crossed = self.walk(through.warp, through.angle, self.tics(through) * WALK_UNITS_PER_TIC)
                families = [route.zone_family(md.name_of(s)) for s in crossed if s is not None]
                self.assertEqual(["Z3", door_family, inside], list(dict.fromkeys(families))[:3])
                first = next(i for i, s in enumerate(crossed)
                             if s is not None and route.zone_family(md.name_of(s)) == inside)
                self.assertGreaterEqual(model_walk(self.tics(through)), first * SAMPLE + PLAYER_RADIUS)

    def test_the_keys_are_walked_onto_never_given(self):
        md, m = self.md, self.m
        for sid, ed, spot in (("YKEY", m.ED_YELLOW_CARD, m.YELLOW_KEY_SPOT),
                              ("RKEY", m.ED_RED_CARD, m.RED_KEY_SPOT)):
            with self.subTest(sid):
                step = self.steps[sid]
                for skill in (2, 3, 4):
                    self.assertEqual(1, len(md.things_on(ed, skill)), f"skill {skill}")
                thing = md.things_on(ed, 3)[0]
                self.assertEqual(spot, (thing.x, thing.y))
                self.assertEqual(m.KEY_ZONES[ed], md.name_of(md.sector_at(thing.x, thing.y)))
                start = step.warp
                self.clear_of_walls(start)      # on the room's floor, a body clear of the raised top
                dx, dy = route.COMPASS[step.angle]
                gap = (thing.x - start[0]) * dx + (thing.y - start[1]) * dy
                self.assertEqual(0, (thing.x - start[0]) * dy - (thing.y - start[1]) * dx, "off the lane")
                self.assertGreater(gap, PLAYER_RADIUS + PICKUP_RADIUS, "the warp lands on the key")
                self.assertGreaterEqual(model_walk(self.tics(step)), gap, "the walk stops short of the key")
                floor = md.textmap.sectors[md.sector_at(*start)].heightfloor
                for s in self.walk(start, step.angle, gap):
                    self.assertEqual(step.expect, (route.zone_family(md.name_of(s)),), md.name_of(s))
                    self.assertLessEqual(md.textmap.sectors[s].heightfloor - floor, MAX_STEP_UP)

    def test_a_door_that_loses_or_swaps_its_lock_has_no_route(self):
        """The doors are found by tag AND lock: a yellow door on lock 1 is not
        the yellow door, and the route refuses to be built rather than test it."""
        md = route.MapData(FACTORY)      # a private copy: the cached one stays as built
        m = md.module
        route.tankograd_critical(md)     # as built: fine
        for ld in md.textmap.linedefs:
            if ld.special == m.SPECIAL_DOOR_LOCKED_RAISE and ld.arg0 == m.TAG_YELLOW_DOOR:
                ld.arg3 = m.LOCK_RED_CARD
        with self.assertRaises(route.RouteError):
            route.tankograd_critical(md)

    def test_the_switches_are_pressed_from_their_faces(self):
        tm, m = self.md.textmap, self.m
        for sid, tag, face in (("SWA", m.TAG_SHUTTER, m.SW_A_FACE), ("SWB", m.TAG_GATE, m.SW_B_FACE)):
            with self.subTest(sid):
                step = self.steps[sid]
                here = self.clear_of_walls(step.warp)
                dist, ld = self.line_ahead(step.warp, step.angle)
                # SW-A sits at the back of a 16-deep niche: Doom's use trace
                # passes a two-sided line with no special if it is open, so
                # step through the niche's mouth (same floor, a body's height).
                while ld.sideback is not None and not ld.special:
                    for side in (ld.sidefront, ld.sideback):
                        sec = tm.sectors[tm.sidedefs[side].sector]
                        self.assertEqual(tm.sectors[here].heightfloor, sec.heightfloor, sid)
                        self.assertGreaterEqual(sec.heightceiling - sec.heightfloor, route.PLAYER_HEIGHT)
                    x, y = step.warp
                    dx, dy = route.COMPASS[step.angle]
                    dist2, ld = self.line_ahead((x + dx * (dist + 1), y + dy * (dist + 1)), step.angle)
                    dist += 1 + dist2
                self.assertLessEqual(dist, USE_RANGE)
                self.assertEqual((udmf.SPECIAL_DOOR_OPEN, tag), (ld.special, ld.arg0))
                self.assertIsNone(ld.sideback)
                self.assertEqual(face, tm.sidedefs[ld.sidefront].texturemiddle)

    def test_the_exit_walk_crosses_the_gate_and_climbs_to_the_breaker(self):
        md, tm, m = self.md, self.md.textmap, self.m
        e0, e1 = self.steps["E0"], self.steps["E1"]
        self.clear_of_walls(e0.warp)
        exits = [ld for ld in tm.linedefs if ld.special == route.SPECIAL_EXIT_NORMAL]
        self.assertEqual(1, len(exits))
        exit_line = exits[0]
        self.assertEqual((m.EXIT_FACE, None), (tm.sidedefs[exit_line.sidefront].texturemiddle,
                                               exit_line.sideback))
        self.assertIn("playeruse", exit_line.flags)
        (x1, y1), _ = route.line_ends(md, exit_line)
        dx, dy = route.COMPASS[e0.angle]
        to_wall = (x1 - e0.warp[0]) * dx if dx else (y1 - e0.warp[1]) * dy
        walk = to_wall - PLAYER_RADIUS
        end = (e0.warp[0] + dx * walk, e0.warp[1] + dy * walk)
        crossed = self.walk(e0.warp, e0.angle, walk)
        self.assertNotIn(None, crossed)
        self.assertEqual(["PH", "GATE", "DR"],
                         list(dict.fromkeys(route.zone_family(md.name_of(s)) for s in crossed)))
        floors = [tm.sectors[s].heightfloor for s in crossed]
        for a, b in zip(floors, floors[1:]):
            self.assertLessEqual(b - a, MAX_STEP_UP, "a step up the dais too high to walk")
        for s in crossed:
            if route.zone_family(md.name_of(s)) == "GATE":
                self.assertEqual(m.TAG_GATE, tm.sectors[s].identifier)
        # The body stops with its front at the breaker: on the dais's top
        # step, level with the niche the breaker is set in.
        niche = tm.sectors[tm.sidedefs[exit_line.sidefront].sector]
        self.assertEqual("DR", route.zone_family(md.name_of(md.sector_at(*end))))
        self.assertEqual(niche.heightfloor, tm.sectors[md.sector_at(*end)].heightfloor)
        dist, ahead = self.line_ahead(end, e0.angle)
        self.assertIs(exit_line, ahead, "the walk does not end against the breaker")
        self.assertLessEqual(dist, USE_RANGE)
        self.assertGreaterEqual(model_walk(self.tics(e0)), walk)
        self.assertIsNone(e1.warp)
        self.assertEqual(("use",), e1.actions)

    def test_print_runs_on_map03(self):
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print", "--route", "tankograd-critical"])
        self.assertEqual(route.EXIT_OK, code)
        for skill in (2, 3, 4):
            self.assertIn(f"-skill {skill} +map {FACTORY}", out)
        for tag in (self.m.TAG_YELLOW_DOOR, self.m.TAG_RED_DOOR, self.m.TAG_SHUTTER, self.m.TAG_GATE):
            self.assertIn(f"netevent sdtag {tag}", out)
        self.assertNotIn("sdexit", out)
        self.assertNotRegex(out, r"(?m)^\s+give\b")


class MapinfoAndMapNamesTest(unittest.TestCase):
    """Where each exit leads and which map is which come from the sources:
    D60 changed the first, D62 changes the second."""

    SAMPLE = """
// a comment: next = MAP99
episode MAP01 { name = "x" }
map MAP01 lookup "SD_MAP01_NAME"
{
	cluster = 3
	next = "MAP02"   // D60
}
map MAP02 lookup "SD_MAP02_NAME"
{
	next = endtitle
}
map RANGE lookup "SD_RANGE_NAME"
{
	next = EndGame { Text = "$SD_END02_TEXT" }
}
map NONEXT lookup "X"
{
	cluster = 1
}
/* map MAP07 { next = MAP08 } */
"""

    def test_mapinfo_next_reads_quoted_bare_and_block_values(self):
        t = self.SAMPLE
        self.assertEqual("MAP02", route.mapinfo_next("MAP01", t))
        self.assertEqual("MAP02", route.mapinfo_next("map01", t))
        self.assertEqual("endtitle", route.mapinfo_next("MAP02", t))
        self.assertEqual("EndGame", route.mapinfo_next("RANGE", t))
        self.assertIsNone(route.mapinfo_next("NONEXT", t))
        self.assertIsNone(route.mapinfo_next("MAP07", t), "a commented-out block was read")

    def test_exit_expectation(self):
        t = self.SAMPLE
        self.assertEqual({"end_sequence": False, "next_map": "MAP02"}, route.exit_expectation("MAP01", t))
        self.assertEqual({"end_sequence": True, "next_map": None}, route.exit_expectation("MAP02", t))
        self.assertEqual({"end_sequence": True, "next_map": None}, route.exit_expectation("RANGE", t))
        for name in ("NONEXT", "MAP99"):
            with self.assertRaises(route.RouteError):
                route.exit_expectation(name, t)

    def test_the_real_mapinfo(self):
        """Today (D60, D62): Zarya-7 leads to the metro, the metro to the
        factory; the factory and the range end the game."""
        self.assertEqual(METRO, route.mapinfo_next(ZARYA))
        self.assertEqual({"end_sequence": False, "next_map": METRO}, route.exit_expectation(ZARYA))
        factory = route.exit_expectation(METRO)["next_map"]
        self.assertIsNotNone(factory, "the metro ends the game: D62 says it leads to the factory")
        self.assertNotIn(factory.upper(), {ZARYA, RANGE, METRO})
        self.assertTrue(route.exit_expectation(factory)["end_sequence"])
        self.assertEqual(FACTORY, factory.upper(), "the metro leads to another map than the factory")
        self.assertTrue(route.exit_expectation(RANGE)["end_sequence"])
        # D62: the slots follow the campaign, so the map numbers say the order.
        self.assertEqual(("MAP01", "MAP02", "MAP03"), (ZARYA, METRO, factory.upper()))

    def test_maps_are_found_by_their_constants(self):
        self.assertEqual(4, len({ZARYA, RANGE, METRO, FACTORY}))
        for name in (ZARYA, RANGE, METRO, FACTORY):
            source = (route.MAPS_DIR / name / "map.py").read_text(encoding="utf-8")
            self.assertRegex(source, rf'(?m)^MAP_NAME = "{name}"', "the folder is not the map's lump name")
        with self.assertRaises(route.RouteError):
            route.map_defining("MAP_NAME")             # every map: ambiguous
        with self.assertRaises(route.RouteError):
            route.map_defining("NO_MAP_DEFINES_THIS")
        source = Path(route.__file__).read_text(encoding="utf-8")
        import ast
        literals = {n.value for n in ast.walk(ast.parse(source))
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for slot in ("MAP01", "RANGE", "MAP02", "MAP03"):
            self.assertNotIn(slot, literals, f"route.py names {slot} as a value")


# ============================================================================
# The gate (D26)
# ============================================================================

class GateTest(unittest.TestCase):

    def test_without_the_gate_nothing_is_launched(self):
        env = {k: v for k, v in os.environ.items() if k != smoke.ENGINE_GATE_VAR}
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pk3 = tmp / "mod.pk3"
            pk3.write_bytes(b"PK")
            fake_gzdoom = tmp / "gzdoom.exe"

            def refuse(*_a, **_k):
                raise AssertionError("a process was started without the gate")

            with mock.patch.dict(os.environ, env, clear=True), \
                    mock.patch("subprocess.Popen", side_effect=refuse), \
                    mock.patch.object(smoke, "find_gzdoom", return_value=fake_gzdoom), \
                    mock.patch.object(smoke, "find_iwad", return_value=tmp / "freedoom2.wad"), \
                    mock.patch.object(route, "HELPER_PK3", tmp / "h.pk3"), \
                    mock.patch.object(route, "ROUTE_DIR", tmp / "route"):
                code, _out, err = run_main(["--no-build", "--pk3", str(pk3), "--skills", "3"])
        self.assertEqual(route.EXIT_BLOCKED, code)
        self.assertIn(smoke.ENGINE_GATE_VAR, err)


if __name__ == "__main__":
    unittest.main()
