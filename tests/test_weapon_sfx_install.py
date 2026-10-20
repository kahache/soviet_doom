"""N9 (D74): the 25 approved weapon sounds, mastered and installed; N9e
(D83) added the IZh-58's shot, SDIZFIR take B.

What is pinned, and why:

  contract   exactly the 25 OK of D74 and SDIZFIR B (D83), each in the take
             the CEO chose (SDAXSWG C, SDAXWAL C, SDTTFIR B, SDPPFIR C,
             SDIZFIR B, the rest A); the five not approved (NO or "?") are
             never installed,
             never rendered by the mastering tool and still play Freedoom
             (or Doom's generic pickup); the reloads parked by D47 are the
             three guns with no reload state
  files      assets/sounds/weapons/ holds exactly the 26 OGGs, each the file
             tools/audio/master_weapon_sfx.py installed (SHA-256 pinned in
             INSTALLED_SHA256), each a Vorbis stream
  package    every SNDINFO weapon alias resolves: to a lump packed as
             sounds/<LUMP>.ogg, or to a Freedoom DS* lump (checked in the
             IWAD when present); no alias is defined twice; every approved
             lump has an alias and nothing packed lacks one
  hooks      each approved sound is played where WEAPON-SOUNDS section 6
             says: the swing on the first Fire frame, the wall sound by the
             axe's puff, pickups by Inventory.PickupSound, the empty click
             by A_SD_WeaponReady on every gun's Ready, the RPG-7's reload in
             the split launch frame, the Katyusha's on its own channel; the
             tic totals of every state stay what BALANCE.md pins
  licences   a LICENSES.md row per packed sound, WEAPON-SOUNDS section 2.1
             and section 10 name every installed lump
  loudness   (numpy + ffmpeg) every installed OGG, decoded, sits within its
             window: the target +-1 dB, or, for the lumps listed short of
             target, that shortfall; the peak never reaches 0 dBFS; the
             Freedoom references re-measured from the IWAD
  takes      (slow: renders) re-rendering every lump with its D74 take and
             mastering it gives the pinned WAV master byte for byte, and the
             OGG in assets/; another take does not; the master is the
             draft's level only (gain, shelf, limiter), not a new sound

The first five blocks are stdlib only (CI's python has no numpy). The
renders need the gitignored work/audio/sfx_sources/ and ffmpeg and are
skipped with SD_SKIP_SLOW_ART=1 (`tools/verify.py fast`).

Run:  .venv/Scripts/python.exe -m unittest tests.test_weapon_sfx_install -v
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
WEAPONS_ZS = SRC_DIR / "zscript" / "weapons"
SNDINFO = SRC_DIR / "lumps" / "SNDINFO"
ASSET_DIR = PROJECT_ROOT / "assets" / "sounds" / "weapons"
MASTER_PY = TOOLS_DIR / "audio" / "master_weapon_sfx.py"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
WEAPON_SOUNDS = PROJECT_ROOT / "docs" / "sound" / "WEAPON-SOUNDS.md"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(TOOLS_DIR / "audio"))

import check_pk3  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from sdbuild.wad import read_lump  # noqa: E402

try:
    import numpy as np
    import gen_weapon_alts as alts
    import gen_weapon_sfx as gws
    import master_weapon_sfx as mws
except ImportError:                                    # pragma: no cover
    np = alts = gws = mws = None

needs_numpy = unittest.skipIf(np is None, "numpy is not installed (CI's system python)")
slow = unittest.skipIf(os.environ.get("SD_SKIP_SLOW_ART"),
                       "SD_SKIP_SLOW_ART is set: skipping the re-render of the 25 masters")

# --- D74, as ratified (docs/PRD.md) ----------------------------------------------
# lump -> (logical name, take)
D74_OK: dict[str, tuple[str, str]] = {
    "SDAXSWG": ("sd/weapon/iceaxe/swing", "C"),
    "SDAXHIT": ("sd/weapon/iceaxe/hit", "A"),
    "SDAXWAL": ("sd/weapon/iceaxe/wall", "C"),
    "SDTTFIR": ("sd/weapon/tokarev/fire", "B"),
    "SDTTRLD": ("sd/weapon/tokarev/reload", "A"),
    "SDTTDRY": ("sd/weapon/tokarev/dry", "A"),
    "SDIZDRY": ("sd/weapon/izh/dry", "A"),
    "SDIZFIR": ("sd/weapon/izh/fire", "B"),          # D83, installed by N9e
    "SDPPFIR": ("sd/weapon/ppsh/fire", "C"),
    "SDPPRLD": ("sd/weapon/ppsh/reload", "A"),
    "SDPPPKP": ("sd/weapon/ppsh/pickup", "A"),
    "SDPPDRY": ("sd/weapon/ppsh/dry", "A"),
    "SDRPFIR": ("sd/weapon/rpg7/fire", "A"),
    "SDRPEXP": ("sd/weapon/rpg7/explode", "A"),
    "SDRPRLD": ("sd/weapon/rpg7/reload", "A"),
    "SDRPPKP": ("sd/weapon/rpg7/pickup", "A"),
    "SDRPDRY": ("sd/weapon/rpg7/dry", "A"),
    "SDRKRLD": ("sd/weapon/roks3/reload", "A"),
    "SDRKPKP": ("sd/weapon/roks3/pickup", "A"),
    "SDRKDRY": ("sd/weapon/roks3/dry", "A"),
    "SDHKCHG": ("sd/weapon/katyusha/charge", "A"),
    "SDHKFIR": ("sd/weapon/katyusha/fire", "A"),
    "SDHKEXP": ("sd/weapon/katyusha/burst", "A"),
    "SDHKRLD": ("sd/weapon/katyusha/reload", "A"),
    "SDHKPKP": ("sd/weapon/katyusha/pickup", "A"),
    "SDHKDRY": ("sd/weapon/katyusha/dry", "A"),
}
# D74's drafts of these five were NO or "?": master_weapon_sfx.py refuses
# them (UNDECIDED there). D94 (N9e) approved alternatives for four, below;
# the IZh-58's pickup (all three alternatives NO) keeps Doom's generic one.
D74_REFUSED = ("SDTTPKP", "SDIZRLD", "SDRKFIR", "SDAXPKP", "SDIZPKP")
# Still not ours: logical name -> what plays (None: Doom's generic weapon
# pickup, i.e. no SNDINFO line and no Inventory.PickupSound).
UNDECIDED: dict[str, tuple[str, str | None]] = {
    "SDIZPKP": ("sd/weapon/izh/pickup", None),
}
# D94 (N9e): the approved alternatives of gen_weapon_alts.py. group -> {member: lump}
D94: dict[str, dict[str, str]] = {
    "sd/weapon/tokarev/pickup": {"sd/weapon/tokarev/pickup/1": "SDTTPKP1", "sd/weapon/tokarev/pickup/2": "SDTTPKP2"},
    "sd/weapon/iceaxe/pickup": {"sd/weapon/iceaxe/pickup/1": "SDAXPKP1", "sd/weapon/iceaxe/pickup/3": "SDAXPKP3"},
    "sd/weapon/izh/reload": {"sd/weapon/izh/reload": "SDIZRLD"},
    "sd/weapon/roks3/fire": {"sd/weapon/roks3/fire/1": "SDRKFIR1", "sd/weapon/roks3/fire/2": "SDRKFIR2",
                             "sd/weapon/roks3/fire/3": "SDRKFIR3"},
}
D94_LUMPS = {lump: name for g in D94.values() for name, lump in g.items()}
D94_ALT_OF = {"SDTTPKP1": "SDTTPKP_alt1", "SDTTPKP2": "SDTTPKP_alt2", "SDAXPKP1": "SDAXPKP_alt1",
              "SDAXPKP3": "SDAXPKP_alt3", "SDIZRLD": "SDIZRLD_alt3", "SDRKFIR1": "SDRKFIR_alt1",
              "SDRKFIR2": "SDRKFIR_alt2", "SDRKFIR3": "SDRKFIR_alt3"}
ALT_PAGE_DIR = PROJECT_ROOT / "work" / "audio" / "alt"
PARKED = {"SDTTRLD", "SDPPRLD", "SDRKRLD"}       # D47: no reload state
GUNS = {"tokarev.zs": "tokarev", "izh.zs": "izh", "ppsh.zs": "ppsh", "rpg7.zs": "rpg7",
        "roks3.zs": "roks3", "katyusha.zs": "katyusha"}
PICKUPS = {"ppsh.zs": "ppsh", "rpg7.zs": "rpg7", "roks3.zs": "roks3", "katyusha.zs": "katyusha",
           "tokarev.zs": "tokarev", "ice_axe.zs": "iceaxe"}      # the last two since D94 (N9e)
NO_PICKUP_SOUND = ("izh.zs",)

# The States' tic totals per label as BALANCE.md pins them (unchanged by N9).
TIC_TOTALS = {
    "ice_axe.zs": {"Fire": 27}, "tokarev.zs": {"Fire": 16}, "izh.zs": {"Fire": 23, "Reload": 30},
    "ppsh.zs": {"Fire": 6}, "rpg7.zs": {"Fire": 26}, "roks3.zs": {"Fire": 23},
    "katyusha.zs": {"Fire": 60},
}

OGG_MAGIC = b"OggS"
VORBIS_ID = b"\x01vorbis"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def master_constant(name: str):
    """A literal constant of master_weapon_sfx.py, read without importing it
    (it needs numpy): the stdlib tests use the same pins as the tool."""
    tree = ast.parse(MASTER_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        targets = [node.target] if isinstance(node, ast.AnnAssign) else getattr(node, "targets", [])
        if any(isinstance(t, ast.Name) and t.id == name for t in targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {MASTER_PY.name}")


def sndinfo_aliases() -> dict[str, str]:
    """logical name -> lump; `$random` lines (the enemies' takes, N9e) name
    no lump and are tests/test_enemy_sfx_install.py's."""
    out: dict[str, str] = {}
    for raw in SNDINFO.read_text(encoding="utf-8").splitlines():
        line = raw.split("//")[0].strip()
        if not line or line.startswith("$random"):
            continue
        logical, lump = line.split()
        if logical in out:
            raise AssertionError(f"{logical} defined twice in SNDINFO")
        out[logical] = lump
    return out


def code(zs_file: str) -> str:
    text = (WEAPONS_ZS / zs_file).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


RE_FRAME = re.compile(r"^\s*([A-Z0-9]{4})\s+([A-Z\[\]\\]+)\s+(-?\d+)\s*(.*?)\s*;\s*$")


def state_rows(zs_file: str) -> list[tuple[str, str, str, int, str]]:
    """(label, sprite, frames, tics, rest) for every frame line of States."""
    body = code(zs_file)
    m = re.search(r"\bStates\s*\{", body)
    depth, i = 1, m.end()
    while depth:
        depth += {"{": 1, "}": -1}.get(body[i], 0)
        i += 1
    label, rows = None, []
    for line in body[m.end():i - 1].splitlines():
        lab = re.match(r"^\s*(\w+):\s*$", line)
        if lab:
            label = lab.group(1)
            continue
        fr = RE_FRAME.match(line)
        if fr:
            rows.append((label, fr.group(1), fr.group(2), int(fr.group(3)), fr.group(4)))
    return rows


# --- Contract ---------------------------------------------------------------------

class ContractTests(unittest.TestCase):
    def test_the_tool_installs_exactly_the_d74_ok_in_their_takes(self):
        installs = master_constant("INSTALLED_SHA256")
        self.assertEqual(set(installs), set(D74_OK))
        text = MASTER_PY.read_text(encoding="utf-8")
        found = dict(re.findall(r'Install\("(SD[A-Z]{5})", "([ABC])"', text))
        self.assertEqual(found, {lump: take for lump, (_, take) in D74_OK.items()})

    def test_the_tool_refuses_the_undecided(self):
        self.assertEqual(set(master_constant("UNDECIDED")), set(D74_REFUSED))
        self.assertFalse(set(D74_REFUSED) & set(D74_OK))

    def test_the_tool_installs_exactly_the_d94_alternatives(self):
        self.assertEqual(set(master_constant("ALT_INSTALLED_SHA256")), set(D94_LUMPS))
        trimmed = master_constant("ALT_CODEC_TRIMMED")
        self.assertLessEqual(set(trimmed), set(D94_LUMPS))
        for lump, db in trimmed.items():
            self.assertTrue(0 < db <= 2.0, lump)
        self.assertTrue({"SDIZPKP_alt1", "SDIZPKP_alt2", "SDIZPKP_alt3"}
                        <= set(master_constant("REJECTED_ALTS")))

    def test_the_parked_reloads_are_the_guns_without_a_reload_state(self):
        self.assertEqual(set(master_constant("PARKED")), PARKED)
        for zs_file in ("tokarev.zs", "ppsh.zs", "roks3.zs"):
            self.assertNotRegex(code(zs_file), r"(?m)^\s*Reload:", zs_file)
            self.assertNotIn("/reload", code(zs_file), zs_file)

    def test_short_of_target_names_only_installed_lumps(self):
        short = master_constant("SHORT_OF_TARGET")
        self.assertLessEqual(set(short), set(D74_OK))
        for lump, db in short.items():
            self.assertGreater(db, 1.0, f"{lump}: within the window is not short")


# --- Files ------------------------------------------------------------------------

class FileTests(unittest.TestCase):
    def test_exactly_the_34_oggs(self):
        self.assertEqual(sorted(p.name for p in ASSET_DIR.iterdir()),
                         sorted(f"{lump}.ogg" for lump in {**D74_OK, **D94_LUMPS}))

    def test_each_d94_alternative_is_the_installed_file(self):
        pins = master_constant("ALT_INSTALLED_SHA256")
        for lump in D94_LUMPS:
            data = (ASSET_DIR / f"{lump}.ogg").read_bytes()
            self.assertEqual(sha256(data), pins[lump][1], lump)
            self.assertTrue(data.startswith(OGG_MAGIC), lump)

    @unittest.skipUnless(ALT_PAGE_DIR.is_dir(), "work/ not present (CI has no work/)")
    def test_untrimmed_alternatives_are_the_oggs_the_ceo_heard(self):
        trimmed = master_constant("ALT_CODEC_TRIMMED")
        for lump, alt in D94_ALT_OF.items():
            same = (ASSET_DIR / f"{lump}.ogg").read_bytes() == (ALT_PAGE_DIR / f"{alt}.ogg").read_bytes()
            self.assertEqual(same, lump not in trimmed, lump)

    def test_no_undecided_sound_anywhere_in_assets(self):
        for path in (PROJECT_ROOT / "assets").rglob("*"):
            self.assertNotIn(path.stem.upper(), UNDECIDED, str(path))

    def test_each_is_the_installed_file(self):
        pins = master_constant("INSTALLED_SHA256")
        for lump in D74_OK:
            with self.subTest(lump):
                self.assertEqual(sha256((ASSET_DIR / f"{lump}.ogg").read_bytes()), pins[lump][1])

    def test_each_is_a_vorbis_stream(self):
        for lump in D74_OK:
            data = (ASSET_DIR / f"{lump}.ogg").read_bytes()
            self.assertTrue(data.startswith(OGG_MAGIC), lump)
            self.assertIn(VORBIS_ID, data[:64], lump)


# --- Package and SNDINFO ------------------------------------------------------------

class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name) / "sovietdoom.pk3"
        build_pk3(SRC_DIR, out, TOOLS_DIR, PROJECT_ROOT / "assets")
        cls.pk3 = out
        with zipfile.ZipFile(out) as zf:
            cls.names = set(zf.namelist())
        cls.aliases = sndinfo_aliases()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_approved_lump_has_its_alias(self):
        for lump, (logical, _) in D74_OK.items():
            self.assertEqual(self.aliases.get(logical), lump, logical)

    def test_every_sd_alias_resolves_to_a_packed_lump(self):
        sd = {lump for lump in self.aliases.values() if lump.startswith("SD")}
        self.assertTrue(sd)
        for lump in sd:
            self.assertIn(f"sounds/{lump}.ogg", self.names, lump)

    def test_every_other_alias_is_a_freedoom_lump(self):
        others = {lump for lump in self.aliases.values() if not lump.startswith("SD")}
        for lump in others:
            self.assertRegex(lump, r"^DS[A-Z0-9]{1,6}$")
        if not IWAD.is_file():
            self.skipTest("iwads/freedoom2.wad is not on this machine")
        blob = IWAD.read_bytes()
        for lump in sorted(others):
            with self.subTest(lump):
                self.assertTrue(read_lump(blob, lump))

    def test_every_packed_sound_has_an_alias(self):
        packed = {Path(n).stem for n in self.names if n.startswith("sounds/")}
        weapons = {p.stem for p in ASSET_DIR.glob("*.ogg")}
        self.assertEqual(weapons, set(D74_OK) | set(D94_LUMPS))
        self.assertLessEqual(weapons, packed)        # the enemies' (N9e) are packed too
        self.assertLessEqual(packed, set(self.aliases.values()))

    def test_the_d94_groups(self):
        text = SNDINFO.read_text(encoding="utf-8")
        for group, members in D94.items():
            with self.subTest(group):
                if len(members) == 1:
                    self.assertEqual(self.aliases.get(group), next(iter(members.values())))
                else:
                    m = re.search(rf"(?m)^\$random\s+{re.escape(group)}\s*\{{\s*([^}}]*?)\s*\}}", text)
                    self.assertIsNotNone(m)
                    self.assertEqual(m.group(1).split(), list(members))
                    for name, lump in members.items():
                        self.assertEqual(self.aliases.get(name), lump)
                for lump in members.values():
                    self.assertIn(f"sounds/{lump}.ogg", self.names)

    def test_the_undecided_still_play_what_they_played(self):
        for lump, (logical, today) in UNDECIDED.items():
            with self.subTest(lump):
                self.assertEqual(self.aliases.get(logical), today)
                self.assertNotIn(f"sounds/{lump}.ogg", self.names)

    def test_check_pk3_passes_licences_and_package(self):
        report = check_pk3.check_pk3(self.pk3)
        self.assertEqual([f.render() for f in report.errors], [])
        self.assertGreaterEqual(report.stats["assets_packed"], len(D74_OK))


# --- Hooks ----------------------------------------------------------------------------

class HookTests(unittest.TestCase):
    def test_the_swing_starts_with_the_wind_up(self):
        fire = [r for r in state_rows("ice_axe.zs") if r[0] == "Fire"]
        self.assertEqual(fire[0][2:], ("B", 5, 'A_StartSound("sd/weapon/iceaxe/swing", CHAN_WEAPON)'))
        self.assertIn("A_SD_IceAxeSwing", fire[1][4])

    def test_the_wall_sound_is_the_axe_puffs(self):
        puff = code("ice_axe_puff.zs")
        self.assertRegex(puff, r"class\s+SD_IceAxePuff\s*:\s*BulletPuff")
        self.assertIn('AttackSound "sd/weapon/iceaxe/wall";', puff)
        self.assertNotIn("SeeSound", puff)          # a hit on flesh stays the axe's own sound
        self.assertIn('"SD_IceAxePuff", LAF_ISMELEEATTACK', code("ice_axe.zs"))

    def test_pickup_sounds_on_the_approved_four_only(self):
        for zs_file, key in PICKUPS.items():
            self.assertIn(f'Inventory.PickupSound "sd/weapon/{key}/pickup";', code(zs_file), zs_file)
        for zs_file in NO_PICKUP_SOUND:
            self.assertNotIn("PickupSound", code(zs_file), zs_file)

    def test_every_gun_clicks_empty_from_ready(self):
        helper = code("weapon_sounds.zs")
        self.assertRegex(helper, r"class\s+SD_WeaponSounds\s+play")
        self.assertIn("CheckAmmo(Weapon.PrimaryFire, false)", helper)   # counts, never switches
        self.assertIn("!(player.oldbuttons & BT_ATTACK)", helper)       # one click per press
        for zs_file, key in GUNS.items():
            with self.subTest(zs_file):
                ready = [r for r in state_rows(zs_file) if r[0] == "Ready"]
                self.assertEqual([r[3:] for r in ready], [(1, "A_SD_WeaponReady")])
                body = code(zs_file)
                fn = body[body.index("action void A_SD_WeaponReady()"):]
                self.assertIn(f'SD_WeaponSounds.DryClick(invoker, "sd/weapon/{key}/dry");', fn)
                self.assertIn("A_WeaponReady();", fn)
        self.assertNotIn("A_SD_WeaponReady", code("ice_axe.zs"))   # a melee weapon is never empty

    def test_the_rpg7_reloads_in_the_split_launch_frame(self):
        fire = [r[2:] for r in state_rows("rpg7.zs") if r[0] == "Fire"]
        self.assertEqual(fire, [("B", 8, "A_GunFlash"), ("B", 4, 'A_FireProjectile("SD_Pg7Grenade")'),
                                ("B", 10, 'A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON)'),
                                ("B", 4, "A_ReFire")])

    def test_the_katyusha_reloads_without_cutting_the_salvo(self):
        fire = [r[2:] for r in state_rows("katyusha.zs") if r[0] == "Fire"]
        salvo = next(k for k, r in enumerate(fire) if "A_SD_FireKatyusha" in r[2])
        self.assertEqual(fire[salvo + 1], ("B", 0, 'A_StartSound("sd/weapon/katyusha/reload", SD_KATYUSHA_RELOAD_CHANNEL)'))
        self.assertEqual(fire[salvo + 2], ("B", 20, "A_ReFire"))
        self.assertRegex(code("katyusha.zs"), r"SD_KATYUSHA_RELOAD_CHANNEL\s*=\s*CHAN_5\s*;")
        self.assertIn('A_StartSound("sd/weapon/katyusha/fire", CHAN_WEAPON)', code("katyusha.zs"))

    def test_tic_totals_unchanged(self):
        for zs_file, want in TIC_TOTALS.items():
            totals: dict[str, int] = {}
            for label, _, frames, tics, _ in state_rows(zs_file):
                totals[label] = totals.get(label, 0) + len(frames) * tics
            for label, n in want.items():
                self.assertEqual(totals.get(label), n, f"{zs_file} {label}")

    def test_the_new_files_are_included(self):
        entry = (SRC_DIR / "lumps" / "zscript.txt").read_text(encoding="utf-8")
        for name in ("ice_axe_puff.zs", "weapon_sounds.zs"):
            self.assertIn(f'#include "zscript/weapons/{name}"', entry)


# --- Licences and documents --------------------------------------------------------------

class DocumentTests(unittest.TestCase):
    def test_a_licence_row_per_packed_sound(self):
        text = LICENSES.read_text(encoding="utf-8")
        for lump in {**D74_OK, **D94_LUMPS}:
            self.assertRegex(text, rf"(?m)^\| `{lump}` \|", lump)
        for lump in UNDECIDED:
            self.assertNotRegex(text, rf"(?m)^\| `{lump}` \|", lump)

    def test_weapon_sounds_records_the_install(self):
        text = WEAPON_SOUNDS.read_text(encoding="utf-8")
        section = text[text.index("## 10."):]
        for lump in D74_OK:
            self.assertIn(f"`{lump}`", section, lump)
        pins = {**master_constant("INSTALLED_SHA256"), **master_constant("ALT_INSTALLED_SHA256")}
        for lump, (_, ogg) in pins.items():
            self.assertIn(ogg, section, f"{lump}'s OGG hash is not in WEAPON-SOUNDS section 10")


# --- Loudness (numpy + ffmpeg) -------------------------------------------------------------

@needs_numpy
class LoudnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if gws.ffmpeg_path() is None:
            raise unittest.SkipTest("ffmpeg is not on the PATH: cannot decode the OGGs")
        cls.decoded = {lump: gws.decode(ASSET_DIR / f"{lump}.ogg") for lump in D74_OK}

    def test_in_window_or_at_the_pinned_shortfall(self):
        for inst in mws.INSTALLS:
            x = self.decoded[inst.lump]
            loud = alts.loud_a_db(x)
            short = mws.SHORT_OF_TARGET.get(inst.lump)
            with self.subTest(inst.lump, loud=round(loud, 2), target=round(inst.target_db, 2)):
                if short is None:
                    self.assertLessEqual(abs(loud - inst.target_db),
                                         mws.LOUDNESS_TOLERANCE_DB + mws.CODEC_LOUDNESS_DB)
                else:
                    self.assertAlmostEqual(inst.target_db - loud, short,
                                           delta=mws.SHORT_TOLERANCE_DB + mws.CODEC_LOUDNESS_DB)

    def test_never_clips(self):
        for lump, x in self.decoded.items():
            self.assertLess(alts.peak_db(x), mws.DECODED_PEAK_CEILING_DBFS, lump)
        for lump in D94_LUMPS:
            x = gws.decode(ASSET_DIR / f"{lump}.ogg")
            self.assertLess(alts.peak_db(x), mws.DECODED_PEAK_CEILING_DBFS, lump)

    def test_d94_alternatives_in_their_window(self):
        # their target is the one gen_weapon_alts.py levelled them to for the
        # page; a codec trim lowers the peaks, and the level by at most ~1 dB
        for inst in mws.ALT_INSTALLS:
            x = gws.decode(ASSET_DIR / f"{inst.lump}.ogg")
            self.assertLessEqual(abs(alts.loud_a_db(x) - inst.target_db),
                                 mws.LOUDNESS_TOLERANCE_DB + mws.CODEC_LOUDNESS_DB, inst.lump)

    def test_louder_than_the_drafts_were_or_turned_down_to_target(self):
        # The drafts' loudest 50 ms A (WEAPON-SOUNDS section 10, "before"): every
        # short lump gained at least 3 dB; none was turned past its target.
        # SDIZFIR (D83, take B) is the deepest: 7.0 dB short on its master, a
        # boom with 88 % of its energy under 300 Hz, where A-weighting counts
        # little; the codec may take up to CODEC_LOUDNESS_DB more.
        for inst in mws.INSTALLS:
            if inst.lump in mws.SHORT_OF_TARGET:
                floor = inst.target_db - 7.0 - (mws.CODEC_LOUDNESS_DB if inst.lump == "SDIZFIR" else 0.0)
                self.assertGreater(alts.loud_a_db(self.decoded[inst.lump]), floor, inst.lump)

    def test_bass_only_lumps_were_lifted(self):
        # SDAXHIT, SDRPEXP, SDHKEXP were flagged on the sheet (> 90 % under 300 Hz).
        for lump in ("SDRPEXP", "SDHKEXP"):
            self.assertGreaterEqual(alts.share_above(self.decoded[lump]), mws.BASS_FLAG_SHARE, lump)
        self.assertGreater(alts.share_above(self.decoded["SDAXHIT"]), 0.05)

    def test_handling_sits_under_its_weapons_shot(self):
        targets = {i.lump: i.target_db for i in mws.INSTALLS}
        heard = dict(targets, SDRKFIR=mws.FREEDOOM_LOUD_A["DSFLAME"])
        for lump, t in targets.items():
            kind = mws.INSTALLS_BY_LUMP[lump].kind
            weapon = lump[:4]
            shot = heard.get(f"{weapon}FIR")
            if kind in ("reload", "dry") and shot is not None:
                self.assertLess(t, shot, lump)
        self.assertLess(targets["SDAXSWG"], targets["SDAXHIT"])
        self.assertLessEqual(targets["SDHKCHG"], targets["SDHKFIR"])

    def test_freedoom_references_remeasured(self):
        if not IWAD.is_file():
            self.skipTest("iwads/freedoom2.wad is not on this machine")
        for name, want in mws.FREEDOOM_LOUD_A.items():
            x, rate = alts.read_wav(gws.placeholder_wav(name))
            self.assertAlmostEqual(alts.loud_a_db(x, rate), want, delta=mws.FREEDOOM_TOLERANCE_DB, msg=name)


# --- Takes: the re-render (slow) ---------------------------------------------------------

@needs_numpy
@slow
class TakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = gws.Sources()
        missing = [i.lump for i in mws.INSTALLS
                   if not cls.src.available(gws.LUMPS_BY_NAME[i.lump].sources)]
        if missing:
            raise unittest.SkipTest(f"work/audio/sfx_sources/ or ffmpeg missing ({len(missing)} lumps)")
        cls.done, skipped = mws.build(sources=cls.src)
        assert not skipped, skipped

    def test_the_d74_take_gives_the_installed_master(self):
        for m in self.done:
            with self.subTest(m.install.lump):
                wav_pin, ogg_pin = mws.INSTALLED_SHA256[m.install.lump]
                self.assertEqual(sha256(m.wav), wav_pin)
                self.assertEqual(sha256(mws.ogg_of(m)), ogg_pin)

    def test_another_take_is_not_what_is_installed(self):
        for m in self.done:
            lump = m.install.lump
            if not gws.LUMPS_BY_NAME[lump].sweep:
                continue
            for take in gws.TAKES:
                if take == m.install.take:
                    continue
                with self.subTest(lump, take=take):
                    other = mws.master(m.install, mws.render_draft(m.install, self.src, take))
                    self.assertNotEqual(sha256(other.wav), mws.INSTALLED_SHA256[lump][0])

    def test_the_master_is_the_draft_levelled_not_a_new_sound(self):
        for m in self.done:
            with self.subTest(m.install.lump):
                pre = m.pre_limit
                self.assertEqual(len(m.x), len(m.draft))
                r = float(np.corrcoef(m.x, pre)[0, 1])
                self.assertGreater(r, 0.9)
                self.assertLessEqual(m.limit_db, mws.MAX_LIMIT_DB)
                self.assertLessEqual(m.shelf_db, mws.MAX_SHELF_DB)
                if m.shelf_db:
                    self.assertLess(alts.share_above(m.draft), mws.BASS_FLAG_SHARE)

    def test_window_on_the_wav_masters(self):
        for m in self.done:
            loud = alts.loud_a_db(m.x)
            short = mws.SHORT_OF_TARGET.get(m.install.lump)
            with self.subTest(m.install.lump):
                self.assertEqual(m.reached, short is None)
                if short is None:
                    self.assertLessEqual(abs(loud - m.install.target_db), mws.LOUDNESS_TOLERANCE_DB)
                else:
                    self.assertAlmostEqual(m.install.target_db - loud, short, delta=mws.SHORT_TOLERANCE_DB)
                    # at the brief's ceiling: more limiting would not pay
                    best = alts.loud_a_db(mws.limited(m.pre_limit, mws.MAX_LIMIT_DB))
                    self.assertLessEqual(best - loud, mws.PLATEAU_DB + 0.05)
                self.assertLessEqual(alts.peak_db(m.x), mws.PEAK_DBFS + 0.01)

    def test_deterministic(self):
        again = mws.master(self.done[0].install, mws.render_draft(self.done[0].install, self.src))
        self.assertEqual(again.wav, self.done[0].wav)

    def test_the_undecided_cannot_be_rendered(self):
        inst = mws.Install("SDIZRLD", "A", "reload", "DSSHOTGN", 0.0, "")
        with self.assertRaises(ValueError):
            mws.render_draft(inst, self.src)

    def test_list_writes_nothing(self):
        import io
        from contextlib import redirect_stderr, redirect_stdout
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(mws.main(["--list"]), 0)
        self.assertIn("26 approved (D74, D83)", out.getvalue())
        with redirect_stderr(err):
            self.assertEqual(mws.main(["SDIZRLD"]), 2)
        self.assertIn("SDIZRLD", err.getvalue())


if __name__ == "__main__":
    unittest.main()
