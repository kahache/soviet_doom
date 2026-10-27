"""The V3 reloads experiment (D132, ADR 014): magazines with no new art.

Pins, without the engine (D26):
  * the switch: CVARINFO's `sd_reloads` (server, on by default on the
    branch), the name magazine.zs reads, the menu row and its note, the
    strings in [enu default], [ru] and [ca];
  * the key: KEYCONF's `defaultbind r +reload`;
  * the code: the mixin and the helper class, included before the
    weapons; the readout handler, registered in MAPINFO;
  * each gun: the mixin, its magazine and reload constants (the brief's
    durations), the 0-tic Fire guards, the Reload/ReloadLoop states, the
    Ready function's two hooks; the IZh-58's +reload after one barrel;
  * the sounds: each reload names a defined sound, the AKM's reuses SDPPRLD;
  * the docs: BALANCE.md section 10's sustained DPS recomputed from the code,
    the dated doc and MOD-SPEC 6.15;
  * against the installed gzdoom.pk3 (skipped without it, `art` tier): the
    engine constants and the virtual the mixin overrides.

What it cannot pin is what the engine does: the doc's checks R1-R14.

Run:  python3 -m unittest tests.test_reloads -v
"""

from __future__ import annotations

import re
import sys
import unittest
import zipfile
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))

import _v3_reload_states as v3  # noqa: E402
import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from test_language import parse_language  # noqa: E402

SRC = PROJECT_ROOT / "src"
LUMPS = SRC / "lumps"
WEAPONS = SRC / "zscript" / "weapons"
MAGAZINE_ZS = WEAPONS / "magazine.zs"
HUD_ZS = SRC / "zscript" / "sd" / "magazine_hud.zs"
CVARINFO = LUMPS / "CVARINFO"
KEYCONF = LUMPS / "KEYCONF"
MENUDEF = LUMPS / "MENUDEF"
MAPINFO = LUMPS / "MAPINFO"
SNDINFO = LUMPS / "SNDINFO"
LANGUAGE = LUMPS / "LANGUAGE"
ZSCRIPT_TXT = LUMPS / "zscript.txt"
BALANCE = PROJECT_ROOT / "docs" / "engine" / "BALANCE.md"
DOC = PROJECT_ROOT / "docs" / "engine" / "2026-10-25_V3_reloads.md"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
ADR = PROJECT_ROOT / "docs" / "engine" / "adr" / "014-weapon-reloads-experiment.md"

CVAR = "sd_reloads"
TICRATE = 35
MIXIN = "SD_MagazineWeapon"
LANGS = ("enu", "ru", "ca")
MENU_IDS = ("SD_OPTMNU_RELOADS", "SD_OPTMNU_RELOADHELP")
HELP_MAX = 48   # one StaticText row; as long as SD_OPTMNU_LANGHELP, which fits

# zs file -> (class, capacity, reload seconds asked by the brief, the reload
# sound, the lump it plays, tics into that lump of its loudest moment:
# docs/sound/WEAPON-SOUNDS.md section 4, "slide released", "bolt caught",
# "igniter armed").
GUNS = {
    "tokarev.zs": ("SD_Tokarev", 8, 1.2, "sd/weapon/tokarev/reload", "SDTTRLD", 0.70),
    "ppsh.zs": ("SD_Ppsh", 71, 2.5, "sd/weapon/ppsh/reload", "SDPPRLD", 0.86),
    "akm.zs": ("SD_Akm", 30, 2.0, "sd/weapon/akm/reload", "SDPPRLD", 0.86),
    "roks3.zs": ("SD_Roks3", 80, 2.5, "sd/weapon/roks3/reload", "SDRKRLD", 0.88),
}
NO_MAGAZINE = ("ice_axe.zs", "rpg7.zs", "katyusha.zs", "rgd5.zs")
DURATION_TOLERANCE = 0.05   # s: the brief's durations rounded to whole tics
CUE_TOLERANCE = 2           # tics: the loudest moment lands as the gun rises

RE_LABEL = re.compile(r"^\s*(\w+):\s*$")
RE_STATE = re.compile(r"^\s*([A-Z0-9#\-]{4})\s+([A-Z\[\]\\#]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")
RE_FLOW = re.compile(r"^\s*(Goto\s+\w+|Loop|Stop|Wait|Fail)\s*;\s*$")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def code(path: Path) -> str:
    return strip_comments(path.read_text(encoding="utf-8"))


def const(path: Path, name: str) -> str:
    m = re.search(rf"\bconst\s+{name}\s*=\s*([^;]+);", code(path))
    if not m:
        raise AssertionError(f"{path.name}: no const {name}")
    return m.group(1).strip()


def prefix(zs_file: str) -> str:
    return v3.GUNS[zs_file][1]


def states(path: Path) -> list[tuple]:
    text = code(path)
    m = re.search(r"\bStates\s*\{", text)
    assert m, path
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        i += 1
    label, rows = None, []
    for line in text[m.end():i - 1].splitlines():
        if not line.strip():
            continue
        if (mm := RE_LABEL.match(line)):
            label = mm.group(1)
            rows.append((label, ":", "", 0, ""))
        elif (mm := RE_STATE.match(line)):
            rows.append((label, mm.group(1), mm.group(2), int(mm.group(3)), mm.group(4)))
        elif (mm := RE_FLOW.match(line)):
            rows.append((label, "->", " ".join(mm.group(1).split()), 0, ""))
        else:
            raise AssertionError(f"{path.name}: unparsed States line {line!r}")
    return rows


def function_body(text: str, signature: str) -> str:
    m = re.search(signature, text)
    assert m, signature
    i = text.index("{", m.end())
    depth, j = 1, i + 1
    while depth:
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        j += 1
    return text[i + 1:j - 1]


def gzdoom_pk3() -> Path | None:
    return next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                 if (c.parent / "gzdoom.pk3").is_file()), None)


class SwitchTest(unittest.TestCase):
    def test_cvarinfo_declares_the_switch_on(self):
        lines = [ln.strip() for ln in code(CVARINFO).splitlines() if ln.strip()]
        # sd_touch (Android, D137) shares the lump: tests/test_touch.py.
        self.assertIn(f"server bool {CVAR} = true;", lines)
        self.assertEqual(len([ln for ln in lines if CVAR in ln]), 1)

    def test_the_code_reads_that_name(self):
        self.assertEqual(const(MAGAZINE_ZS, "SD_RELOADS_CVAR"), f'"{CVAR}"')
        body = function_body(code(MAGAZINE_ZS), r"static\s+bool\s+On\s*\(\s*\)")
        self.assertIn("CVar.FindCVar(SD_RELOADS_CVAR)", body)
        self.assertIn("cv != null && cv.GetBool()", body, "a missing CVar means off, v1.2's game")

    def test_the_menu_row(self):
        menu = code(MENUDEF)
        block = re.search(r'OptionMenu\s+"SD_OptionsMenu"\s*\{(.*?)\n\}', menu, re.S).group(1)
        self.assertIn(f'Option "$SD_OPTMNU_RELOADS", "{CVAR}", "OnOff"', block)
        # Since the Android work (D137) the note is an SDKeyText row, a
        # StaticText that fills its %s with the bound key (tests/test_touch.py).
        self.assertRegex(block, r'SDKeyText "\$SD_OPTMNU_RELOADHELP", "\+reload"')
        self.assertNotIn('StaticText "$SD_OPTMNU_RELOADHELP"', block)
        self.assertLess(block.index("SD_OPTMNU_RELOADS"), block.index("SD_CreditsMenu"))

    def test_the_strings_in_every_language(self):
        sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))
        for lang in LANGS:
            for ident in MENU_IDS:
                self.assertIn(ident, sections[lang], f"[{lang}] {ident}")
                self.assertTrue(sections[lang][ident].strip('"'), f"[{lang}] {ident} empty")
            help_text = sections[lang]["SD_OPTMNU_RELOADHELP"].strip('"')
            # The note names the key through "%s", filled with the bound key
            # when drawn (R by default: KEYCONF), never a literal letter
            # (D137, tests/test_touch.py).
            self.assertEqual(help_text.count("%s"), 1, f"[{lang}] the note names the key via %s")
            self.assertLessEqual(len(help_text.replace("%s", "R")), HELP_MAX, f"[{lang}] one menu row")
        for ident in MENU_IDS:
            sections["enu"][ident].encode("ascii")   # T17: English stays ASCII
        self.assertNotEqual(sections["ru"]["SD_OPTMNU_RELOADS"], sections["enu"]["SD_OPTMNU_RELOADS"])
        self.assertNotEqual(sections["ca"]["SD_OPTMNU_RELOADS"], sections["enu"]["SD_OPTMNU_RELOADS"])

    def test_the_key(self):
        lines = [ln.strip() for ln in code(KEYCONF).splitlines() if ln.strip()]
        self.assertEqual(lines, ["defaultbind r +reload"])


class WiringTest(unittest.TestCase):
    def test_both_files_are_included_once_and_the_mixin_before_the_guns(self):
        text = strip_comments(ZSCRIPT_TXT.read_text(encoding="utf-8"))
        includes = re.findall(r'#include\s+"([^"]+)"', text)
        for inc in ("zscript/weapons/magazine.zs", "zscript/sd/magazine_hud.zs"):
            self.assertEqual(includes.count(inc), 1, inc)
        first_gun = min(includes.index(f"zscript/weapons/{z}") for z in GUNS)
        self.assertLess(includes.index("zscript/weapons/magazine.zs"), first_gun)

    def test_the_mixin_and_the_helpers(self):
        text = code(MAGAZINE_ZS)
        self.assertEqual(len(re.findall(rf"\bmixin\s+class\s+{MIXIN}\b", text)), 1)
        self.assertEqual(len(re.findall(r"\bclass\s+SD_Reloads\b", text)), 1)
        for field in ("sdMagFired", "sdReloadTic"):
            m = re.search(rf"^\s*(\w+\s+)*int\s+{field}\s*;", text, re.M)
            self.assertIsNotNone(m, field)
            self.assertNotIn("transient", m.group(0), f"{field} must go into the saved game")
        self.assertRegex(text, r"override\s+bool\s+DepleteAmmo\s*\(\s*bool\s+altFire\s*,\s*bool\s+checkEnough\s*,"
                               r"\s*int\s+ammouse\s*,\s*bool\s+forceammouse\s*\)")
        deplete = function_body(text, r"override\s+bool\s+DepleteAmmo")
        self.assertIn("Super.DepleteAmmo(altFire, checkEnough, ammouse, forceammouse)", deplete)
        self.assertIn("!altFire && SD_Reloads.On()", deplete)
        tick = function_body(text, r"action\s+void\s+A_SD_ReloadTick")
        self.assertIn("A_WeaponOffset(0, SD_Reloads.ReloadOffset(t, total, drop), WOF_INTERPOLATE)", tick)
        self.assertIn("A_StartSound(reloadSound, CHAN_WEAPON)", tick)
        self.assertIn("t == total - drop", tick)
        self.assertNotRegex(text, r"\bA_(Lower|Raise)\b", "A_Lower at the bottom brings up the pending weapon")

    def test_the_offsets_are_the_engines_rest_and_bottom(self):
        self.assertEqual(float(const(MAGAZINE_ZS, "SD_RELOAD_TOP")), 32.0)
        self.assertEqual(float(const(MAGAZINE_ZS, "SD_RELOAD_BOTTOM")), 128.0)

    def test_the_readout_is_registered_last_once(self):
        text = strip_comments(MAPINFO.read_text(encoding="utf-8"))
        lines = re.findall(r"(?im)^\s*AddEventHandlers\s*=\s*(.+)$", text)
        self.assertEqual(len(lines), 1)
        names = re.findall(r'"([^"]+)"', lines[0])
        self.assertEqual(names[0], "SD_LoadReporter")
        self.assertEqual(names[-1], "SD_MagazineHud")
        self.assertEqual(names.count("SD_MagazineHud"), 1)
        hud = code(HUD_ZS)
        self.assertRegex(hud, r"class\s+SD_MagazineHud\s*:\s*EventHandler")
        self.assertEqual(set(re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", hud)), {"RenderOverlay"})
        self.assertIn("SD_Reloads.On()", hud)
        self.assertIn("SD_Reloads.Magazine(p.ReadyWeapon)", hud)

    def test_the_readout_knows_every_magazine(self):
        body = function_body(code(MAGAZINE_ZS), r"static\s+int\s*,\s*int\s+Magazine\s*\(")
        for zs_file, (cls, *_rest) in GUNS.items():
            self.assertIn(f"{cls}(w)", body, cls)
            self.assertIn(f"{cls}.{v3.GUNS[zs_file][0]}", body, cls)
        self.assertIn("SD_Izh(w)", body)


class GunTest(unittest.TestCase):
    def test_each_gun_includes_the_mixin_once(self):
        for zs_file in GUNS:
            self.assertEqual(len(re.findall(rf"^\s*mixin\s+{MIXIN}\s*;", code(WEAPONS / zs_file), re.M)), 1, zs_file)

    def test_no_other_weapon_has_a_magazine(self):
        for zs_file in NO_MAGAZINE + ("izh.zs",):
            text = code(WEAPONS / zs_file)
            self.assertNotIn(MIXIN, text, zs_file)
            self.assertNotIn("SD_MagazineDry", text, zs_file)

    def test_capacities_and_durations(self):
        for zs_file, (_, capacity, seconds, *_rest) in GUNS.items():
            path = WEAPONS / zs_file
            self.assertEqual(int(const(path, v3.GUNS[zs_file][0])), capacity, zs_file)
            total = int(const(path, f"{prefix(zs_file)}_RELOAD_TICS"))
            drop = int(const(path, f"{prefix(zs_file)}_RELOAD_DROP"))
            self.assertAlmostEqual(total / TICRATE, seconds, delta=DURATION_TOLERANCE, msg=zs_file)
            self.assertGreater(drop, 0, zs_file)
            self.assertLess(2 * drop, total, f"{zs_file}: the gun is out of sight for a while")

    def test_the_sound_peaks_as_the_gun_comes_back_up(self):
        for zs_file, (*_x, cue) in GUNS.items():
            path = WEAPONS / zs_file
            total = int(const(path, f"{prefix(zs_file)}_RELOAD_TICS"))
            drop = int(const(path, f"{prefix(zs_file)}_RELOAD_DROP"))
            sound_tic = int(const(path, f"{prefix(zs_file)}_RELOAD_SOUND_TIC"))
            self.assertTrue(0 < sound_tic < total - drop, zs_file)
            self.assertAlmostEqual(sound_tic + cue * TICRATE, total - drop, delta=CUE_TOLERANCE, msg=zs_file)

    def test_the_akm_magazine_is_what_the_weapon_gives(self):
        self.assertEqual(const(WEAPONS / "akm.zs", "SD_AKM_MAGAZINE"), const(WEAPONS / "akm.zs", "SD_AKM_AMMO_GIVE"))

    def test_the_fire_guards(self):
        for zs_file in GUNS:
            rows = states(WEAPONS / zs_file)
            fire = [r for r in rows if r[0] == "Fire" and r[1] not in (":", "->")]
            self.assertEqual(fire[0][3:], (0, v3.guard_rest(zs_file)), f"{zs_file}: the first Fire frame")
            guards = [r for r in rows if "SD_MagazineDry" in r[4]]
            self.assertEqual(len(guards), len(v3.GUARDS[zs_file]), zs_file)
            self.assertTrue(all(r[0] == "Fire" and r[3] == 0 for r in guards), zs_file)

    def test_the_reload_states(self):
        for zs_file in GUNS:
            rows = states(WEAPONS / zs_file)
            ready = [r for r in rows if r[0] == "Ready" and r[1] not in (":", "->")][0]
            block = [r for r in rows if r[0] in ("Reload", "ReloadLoop")]
            self.assertEqual(block, v3.reload_rows(zs_file, ready[1], True), zs_file)
            loop = [r for r in block if r[0] == "ReloadLoop" and r[1] not in (":", "->")]
            self.assertEqual(sum(r[3] for r in loop), 1, f"{zs_file}: one tic a pass, RELOAD_TICS passes")

    def test_with_the_edits_undone_the_states_are_as_before(self):
        """The guards and the two labels are the whole state change."""
        for zs_file in GUNS:
            rows = states(WEAPONS / zs_file)
            stripped = [r for r in rows if r[0] not in ("Reload", "ReloadLoop") and "SD_MagazineDry" not in r[4]]
            self.assertEqual(v3.with_reloads(zs_file, stripped), rows, zs_file)

    def test_the_ready_function(self):
        for zs_file in GUNS:
            text = code(WEAPONS / zs_file)
            body = function_body(text, r"action\s+state\s+A_SD_WeaponReady\s*\(\s*\)")
            capacity = v3.GUNS[zs_file][0]
            self.assertIn("player.PendingWeapon == WP_NOCHANGE", body, zs_file)
            self.assertIn(f"invoker.SD_MagazineDry({capacity})", body, zs_file)
            self.assertIn('return ResolveState("Reload");', body, zs_file)
            self.assertIn(f"A_WeaponReady(invoker.SD_ReadyFlags({capacity}));", body, zs_file)
            self.assertLess(body.index("ResolveState"), body.index("DryClick"), zs_file)

    def test_the_izh_reloads_on_the_key_after_one_barrel(self):
        text = code(WEAPONS / "izh.zs")
        body = function_body(text, r"clearscope\s+bool\s+SD_CanReloadIzh\s*\(\s*\)")
        self.assertIn("SD_Reloads.On()", body)
        self.assertIn("barrels < SD_IZH_BARRELS", body)
        self.assertIn("Ammo1.Amount > barrels", body)
        ready = function_body(text, r"action\s+void\s+A_SD_WeaponReady\s*\(\s*\)")
        self.assertIn("A_WeaponReady(invoker.SD_CanReloadIzh() ? WRF_ALLOWRELOAD : 0);", ready)
        self.assertEqual(len(re.findall(r"(?m)^\s*Reload:", text)), 1, "the IZh's own Reload state, unchanged")


class SoundTest(unittest.TestCase):
    def sndinfo(self) -> dict[str, str]:
        out = {}
        for line in strip_comments(SNDINFO.read_text(encoding="utf-8")).splitlines():
            parts = line.split()
            if len(parts) == 2 and not parts[0].startswith("$"):
                out[parts[0]] = parts[1]
        return out

    def test_each_reload_sound_is_defined_and_played_by_its_gun(self):
        names = self.sndinfo()
        for zs_file, (_, _, _, sound, lump, _) in GUNS.items():
            self.assertEqual(names.get(sound), lump, sound)
            self.assertIn(f'"{sound}"', code(WEAPONS / zs_file), zs_file)


class BalanceDocTest(unittest.TestCase):
    """BALANCE.md section 10's figures, recomputed from the code."""

    def avg_damage(self, zs_file: str) -> float:
        if zs_file == "roks3.zs":
            return int(const(WEAPONS / "flame_blob.zs", "SD_FLAME_DAMAGE")) * 4.5
        name = {"tokarev.zs": "SD_TT_DAMAGE", "ppsh.zs": "SD_PPSH_DAMAGE", "akm.zs": "SD_AKM_DAMAGE"}[zs_file]
        return int(const(WEAPONS / zs_file, name)) * 2

    # Tics a round while the trigger is held (BALANCE.md section 2): the
    # TT-33's whole Fire state; the PPSh-41 two rounds in its 6.
    CADENCE = {"tokarev.zs": 16, "ppsh.zs": 3, "akm.zs": 4, "roks3.zs": 3}

    def test_section_10_rows(self):
        text = BALANCE.read_text(encoding="utf-8")
        self.assertIn("## 10. Reloads (V3 experiment)", text)
        section = text.split("## 10. Reloads (V3 experiment)", 1)[1]
        for zs_file, (_, capacity, *_rest) in GUNS.items():
            path = WEAPONS / zs_file
            total = int(const(path, f"{prefix(zs_file)}_RELOAD_TICS"))
            empty = capacity * self.CADENCE[zs_file]
            dmg = capacity * self.avg_damage(zs_file)
            before = self.avg_damage(zs_file) * TICRATE / self.CADENCE[zs_file]
            after = dmg * TICRATE / (empty + total)
            row = next(ln for ln in section.splitlines()
                       if ln.startswith("| ") and ln.split("|")[2].strip().split()[0] == str(capacity))
            cells = [c.strip() for c in row.strip("|").split("|")]
            self.assertTrue(cells[3].startswith(f"{total} tics"), zs_file)
            self.assertTrue(cells[4].startswith(f"{empty} tics"), zs_file)
            self.assertEqual(float(cells[5].replace(" ", "")), dmg, zs_file)
            self.assertAlmostEqual(float(cells[6]), before, delta=0.051, msg=zs_file)
            self.assertAlmostEqual(float(cells[7].strip("*")), after, delta=0.051, msg=zs_file)

    def test_the_docs_exist_and_cross_reference(self):
        for path in (DOC, ADR):
            self.assertTrue(path.is_file(), path)
        doc = DOC.read_text(encoding="utf-8")
        for ref in ("BALANCE.md", "ADR 014", "MOD-SPEC.md", CVAR, "defaultbind r +reload"):
            self.assertIn(ref, doc)
        self.assertIn("## 6.15 Weapon reloads", MOD_SPEC.read_text(encoding="utf-8"))


@unittest.skipUnless(gzdoom_pk3() is not None, "no gzdoom.pk3 on this machine (CI)")
class EngineNamesTest(unittest.TestCase):
    """The engine facts the code leans on, read from the installed gzdoom.pk3."""

    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(gzdoom_pk3()) as z:
            cls.files = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()
                         if n.startswith(("zscript/", "engine/")) or n == "menudef.txt"}

    def test_the_constants(self):
        consts = self.files["zscript/constants.zs"]
        self.assertRegex(consts, r"WRF_ALLOWRELOAD\s*=\s*16")
        self.assertRegex(consts, r"WOF_INTERPOLATE\s*=\s*1\s*<<\s*3")
        self.assertRegex(consts, r"WEAPONBOTTOM\s*=\s*128")
        self.assertRegex(consts, r"WEAPONTOP\s*=\s*32")

    def test_the_virtual_the_mixin_overrides(self):
        weapons = self.files["zscript/actors/inventory/weapons.zs"]
        self.assertRegex(weapons, r"virtual\s+bool\s+DepleteAmmo\s*\(\s*bool\s+altFire\s*,\s*bool\s+checkEnough\s*=\s*true\s*,"
                                  r"\s*int\s+ammouse\s*=\s*-1\s*,\s*bool\s+forceammouse\s*=\s*false\s*\)")
        self.assertIn("native void A_WeaponOffset(double wx = 0, double wy = 32, int flags = 0);",
                      self.files["zscript/actors/actor.zs"])

    def test_the_menu_list_and_the_control_row(self):
        menudef = self.files["menudef.txt"]
        self.assertRegex(menudef, r'OptionValue\s+"OnOff"')
        self.assertRegex(menudef, r'Control\s+"\$CNTRLMNU_RELOAD"\s*,\s*"\+reload"')

    def test_nothing_is_bound_to_r_or_reload_by_default(self):
        for name, text in self.files.items():
            if name.startswith("engine/") and name.endswith(".txt"):
                for line in text.splitlines():
                    parts = line.split()
                    if len(parts) >= 2:
                        self.assertNotEqual(parts[0].lower(), "r", f"{name}: {line}")
                        self.assertNotIn("+reload", parts[1:], f"{name}: {line}")


if __name__ == "__main__":
    unittest.main()
