"""Tests for tools/route.py, the scripted G3 route runner: everything that can
be checked without GZDoom (D26: the engine runs are the PM's).

Covered:
* the helper PK3 is tooling and never reaches the mod: it refuses src/,
  dist/ and assets/, lives under the gitignored logs/, loads after the mod,
  and neither the sources nor a freshly built mod PK3 carry it;
* the routes: g3-auto runs skills 2, 3 and 4 by default; the start
  inventory (63dac93) is asserted by SLOT at A0 and the rack pickup at R1,
  keyed on DoomEdNum 21001 and the rack's position, never on a class name
  (the melee weapon is being renamed, D40); the R1 walk really ends on the
  21001 thing in MAP01, and the map02-start walk on MAP02's;
* --print and --list-routes run with the engine unreachable;
* --parse judges a log: a synthetic clean run passes on every skill and on
  MAP02, and each failure the PM must see (slot 1 at the start, no pickup,
  the wrong weapon raised, the wrong rounds, a log error, a shut door, no
  exit, no inventory) fails with the right exit code;
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

PLAYER_RADIUS = 16
PICKUP_RADIUS = 20        # Doom's pickups (tests/test_map01.py)
MAX_STEP_UP = 24
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
                      "sdclear", "sdexit"):
            self.assertIn(f'"{event}"', zs)
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
        self.assertNotRegex(zs, r"SD_Shovel|SD_IceAxe|SD_Tokarev")
        self.assertEqual(zs.count("{"), zs.count("}"), "unbalanced braces in the helper")

    def test_the_minimal_helper_keeps_the_proven_part_only(self):
        zs = route.helper_zscript(minimal=True)
        for event in ("sdangle", "sdhurt", "sdcount"):
            self.assertIn(f'"{event}"', zs)
        body = zs.split("class", 1)[1]
        for event in ("sdinv", "sdclear", "sdexit", "sdstate"):
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
        self.assertEqual("MAP01", argv[argv.index("+map") + 1])
        self.assertTrue(argv[-1].startswith("+"), "the console sequence is the last argument")


# ============================================================================
# The routes
# ============================================================================

class RouteDefinitionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.map01 = route.MapData("MAP01")
        cls.map02 = route.MapData("MAP02")

    def test_g3_auto_runs_skills_2_3_and_4_by_default(self):
        args = route.parse_args([])
        self.assertEqual("g3-auto", args.route)
        self.assertEqual([2, 3, 4], args.skills)
        self.assertEqual("MAP01", route.ROUTES["g3-auto"].map_name)

    def test_the_start_inventory_is_checked_first_and_by_slot(self):
        """63dac93: TT-33 (slot 2) raised with SD_START_CLIP rounds, slot 1
        empty; the rack gives slot 1 before any door is opened."""
        rounds = route.start_rounds()
        self.assertIsNotNone(rounds, "SD_START_CLIP is gone from player.zs")
        self.assertEqual(50, rounds)
        for name in ("g3-auto", "g3-secrets", "map02-start"):
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

    def test_the_map02_walk_takes_the_21001_thing_and_no_other(self):
        md = self.map02
        thing = md.things_on(route.ED_MELEE, 3)[0]
        start = route.MAP02_AXE_APPROACH
        self._clear_of_walls(md, start)
        crossed = self._walk(md, start, route.MAP02_AXE_FACING, (thing.x, thing.y))
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
        for name, r in route.ROUTES.items():
            md = self.map01 if r.map_name == "MAP01" else self.map02
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
        for name, r in route.ROUTES.items():
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

    def test_map02_start_ends_the_range_by_the_helper(self):
        r = route.ROUTES["map02-start"]
        self.assertEqual(("console", True, True), (r.exit_by, r.end_sequence, r.must_exit))
        self.assertEqual("E1", r.steps[-1].id)
        self.assertIn("exit", r.steps[-1].actions)
        self.assertIn("capture", r.steps[-1].actions)
        cmds = route.route_commands(r)
        self.assertIn("netevent sdexit", cmds)
        for name, other in route.ROUTES.items():
            self.assertNotIn("exit", route.route_commands(other), f"{name}: the console exit quits GZDoom")
        for name in ("g3-auto", "g3-secrets"):
            self.assertEqual(("switch", True), (route.ROUTES[name].exit_by,
                                                route.ROUTES[name].end_sequence))
            self.assertNotIn("netevent sdexit", route.route_commands(route.ROUTES[name]))

    def test_every_built_in_route_turns_into_a_sequence(self):
        for name, r in route.ROUTES.items():
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

    def test_a_json_route_carries_the_inventory_fields(self):
        r = route.route_from_json({"name": "mine", "map": "map02", "must_exit": False, "steps": [
            {"id": "A0", "do": ["inv"], "melee": False, "ready_slot": 2, "ready_ammo": 50}]})
        self.assertEqual("MAP02", r.map_name)
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
            self.assertIn(f"-skill {skill} +map MAP01", out)
        x, y = route.MAP01_RACK_APPROACH
        self.assertIn(f"warp {x} {y}", out)
        self.assertIn("netevent sdinv", out)

    def test_print_runs_on_map02(self):
        with tempfile.TemporaryDirectory() as tmp, no_engine(), \
                mock.patch.object(route, "HELPER_PK3", Path(tmp) / "h.pk3"):
            code, out, _ = run_main(["--print", "--route", "map02-start", "--skills", "3"])
            self.assertEqual(route.EXIT_OK, code)
            self.assertIn("-skill 3 +map MAP02", out)
            self.assertIn("netevent sdexit", out)
            self.assertIn("netevent sdclear", out)
            code, out, _ = run_main(["--print", "--route", "map02-start", "--no-clear"])
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
        for name in route.ROUTES:
            self.assertIn(name, out)


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
        self.next_map = "enDSeQ1dce"            # the same run's MAP01 exit
        self.end_state = route.GS_FINALE
        self.cleared: list[tuple] = []          # (step, class, x, y, hp, dead) sdclear lines

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
        lines.append(f"SDTEST inv weapons={len(weapons)} ready={ready} slot={slot} ammo={ammo}")
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
                    is_open = want_open and tag not in shut_tags
                    out.append(f"SDTEST tag {tag} sector={sector} floor=0 ceil={128 if is_open else 0}")
            if "capture" in step.actions:
                out.append(f"Captured Screenshot_Doom_{n:04d}.png")
            if step.expect:
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
            out.append(f"SDTEST state gamestate={self.end_state}")
        return "\n".join(out) + "\n"

    def _tag_sectors(self, tag):
        found = [i for i, s in enumerate(self.md.textmap.sectors) if s.identifier == tag]
        return found or [0]


class ParseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data = {name: route.MapData(name) for name in ("MAP01", "MAP02")}

    def judge(self, name, skill, **kw):
        r = route.ROUTES[name]
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

    def test_a_clean_run_passes_on_map02(self):
        rep = self.judge("map02-start", 3)
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
        rep = self.judge("map02-start", 3, overrides={0: ([("SD_Pistol2", 2)], "SD_Pistol2", 2, 0)})
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
        fake = FakeRun(r, 4, self.data["MAP01"])
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
    def test_map02_ends_by_sdexit_into_its_end_text(self):
        rep = self.judge("map02-start", 3)
        self.assertTrue(rep.passed, rep.problems)
        self.assertTrue(rep.exit_reached)
        self.assertIn("ended by sdexit: yes", rep.exit_detail)
        self.assertIn("after it: end text", rep.exit_detail)

    def test_map02_without_its_exit_fails(self):
        rep = self.judge("map02-start", 3, exit_=False)
        self.assertFalse(rep.passed)
        self.assertIn("ended by sdexit: NO", rep.exit_detail)

    def test_a_console_exit_does_not_finish_map01(self):
        """G3-4 asks for the exit switch: sdexit on MAP01 is not an exit."""
        r = route.ROUTES["g3-auto"]
        fake = FakeRun(r, 3, self.data["MAP01"])
        text = fake.text(exit_=False) + ("SDTEST exitlevel map=MAP01\n"
                                         "SDTEST unloaded map=MAP01 next=enDSeQ1dce kills=0/33 "
                                         "secrets=0/3 items=0/26 time=900\n")
        rep = route.evaluate(r, 3, route.scan_route_log(text), self.data["MAP01"])
        self.assertFalse(rep.passed)
        self.assertFalse(rep.exit_reached)
        self.assertIn("the level was ended by sdexit, not by its exit switch", rep.problems)

    def test_an_exit_that_leads_to_a_map_not_an_end_sequence_fails(self):
        rep = self.judge("g3-auto", 2, attrs={"next_map": "MAP02"})
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
