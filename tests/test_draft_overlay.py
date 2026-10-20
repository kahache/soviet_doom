"""Contract of tools/make_draft_overlay.py, the DRAFT sprite overlay
(MOD-SPEC 6.9): a separate PK3, loaded after the mod, that wears our
unapproved weapon drafts (and, when one is drafted on the rig, an enemy's)
under the Freedoom placeholder names our states use today.

What is checked, and why:

  contract   the placeholder -> draft table agrees with MOD-SPEC 5.1 and
             6.3 and with gen_weapon.py's WeaponSpec; every placeholder is
             still named by its state file; run.sh hands extra arguments to
             GZDoom after its own `-file`, which is what puts the overlay
             above the mod
  build      the PK3 is built in a temporary folder from synthetic drafts
             (CI has no work/ and no IWAD) of two fixture weapons standing in
             since D88 left no real weapon swap (FIXTURE_WEAPONS: SHT2 ->
             SDXS, SAWG -> SDXW, IWAD sprites no class of ours uses, their
             state files in a temporary copy of src/zscript/), holds only sprites/*.png, every
             lump is a frame a state uses (and, with the IWAD, a frame the
             IWAD has), the PNG bytes and so the grAb offsets are unchanged,
             two builds are byte-identical
  isolation  nothing under src/ or dist/ changes, and an --out under src/,
             dist/ or assets/ is refused
  rotations  a rotated frame with fewer than eight rotations, or mixing
             rotation 0 with 1-8, is refused; with an IWAD, a rotated frame
             the IWAD has as rotation 0 or 9-G is refused, and mirrored
             pairs (XPOSA2A8) are reported as hidden; an enemy fixture
             (XPOS -> SDXR) stands in since D55 left no real enemy swap
  hand       --hand picks hand_<X>/ renders, and refuses a hand nobody drew
  installed  the six pickups D48 installed (INSTALLED) are named by their
             Spawn states, ship from assets/sprites/ and are never overlaid;
             a swap whose sprite is under assets/sprites/ is skipped; the
             Legion trooper installed whole by D54 and the rifleman and the
             hound by D55, the Stormtrooper and his bolt by D56
             (INSTALLED_ENEMIES: SPOS -> SDLT, POSS -> SDRR, SARG -> SDHN,
             TROO -> SDHS, BAL1 -> SDBL) are in no swap, and a swap naming
             one would be skipped; the TT-33's held and flash frames,
             installed by N17 (INSTALLED_WEAPON_FRAMES: PISG -> SDTT,
             PISF -> SDTF), the PPSh-41's by D79 (CHGG -> SDPP,
             CHGF -> SDPF), and the IZh-58's, RPG-7's, ROKS-3's and hand
             Katyusha's by D84 (SHTG/SHTF, MISG/MISF, PLSG/PLSF,
             BFGG/BFGF) and the ice axe's by D88 (PUNG), likewise; the
             Katyusha's floor pickup joined INSTALLED (BFUG -> SDHP, D80)
  real       (skips without work/art) no swap is left since D88, so the
             real overlay has nothing to pack and says so (exit 1, nothing
             written); the ice axe's 4 left with D88 (4 until then), the 20
             of the IZh-58, RPG-7, ROKS-3 and hand Katyusha (and its pickup)
             with D84 (24 until then), the PPSh-41's 3 with D79 (27 until
             then), the TT-33's 4 with N17 (31 until then), the rifleman's
             70 with D55 (101 until then)

Stdlib only: the tool copies bytes and reads PNG chunks with struct.
"""

from __future__ import annotations

import io
import json
import re
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from contextlib import redirect_stderr, redirect_stdout
import shutil
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import make_draft_overlay as mdo  # noqa: E402

IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
GEN_WEAPON = TOOLS_DIR / "art" / "gen_weapon.py"
RUN_SH = TOOLS_DIR / "run.sh"
LUMP_PATH = re.compile(r"^sprites/([A-Z0-9]{4})([A-Z])([0-8])\.png$")


# ------------------------------------------------------------------ fixtures
def png(grab: tuple[int, int] | None = (5, -7), w: int = 2, h: int = 2, seed: int = 0) -> bytes:
    """A tiny valid RGBA PNG, with a grAb chunk before IDAT unless None."""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    raw = b"".join(b"\0" + bytes([(seed + x) % 256, 0, 0, 255]) * w for x in range(h))
    out = mdo.PNG_SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    if grab is not None:
        out += chunk(b"grAb", struct.pack(">ii", *grab))
    return out + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def wad(names: list[str]) -> bytes:
    """A WAD whose lumps are all empty: only the directory matters here."""
    directory = b"".join(struct.pack("<ii", 12, 0) + n.encode().ljust(8, b"\0") for n in names)
    return b"IWAD" + struct.pack("<ii", len(names), 12) + directory


def real_letters(swap: mdo.Swap) -> str:
    return mdo.state_letters((mdo.ZS_ROOT / swap.zs).read_text(encoding="utf-8"), swap.placeholder)


def make_drafts(root: Path, hand_record: str | None = "E") -> tuple[Path, Path]:
    """Synthetic work/art: one draft per frame each real state uses, plus an
    unused frame and a proposal that must not be packed."""
    weapons, rig = root / "weapons", root / "rig"
    rig.mkdir(parents=True, exist_ok=True)    # empty since D55: no enemy swap is left
    seed = 0
    for swap in mdo.SWAPS:
        folder = weapons / swap.item if swap.group == "weapons" else rig
        folder.mkdir(parents=True, exist_ok=True)
        for letter in real_letters(swap):
            rots = mdo.ROTATIONS_8 if swap.group == "enemies" and letter <= "G" else "0"
            for rot in rots:
                seed += 1
                (folder / f"{swap.draft}{letter}{rot}.png").write_bytes(png((seed, -seed), seed=seed))
        if swap.group == "weapons":
            (folder / f"{swap.draft}Z0.png").write_bytes(png())                 # no state shows Z
            (folder / f"{swap.draft}Y0_proposed.png").write_bytes(png())        # a proposal
            if hand_record:
                (folder / "metrics.json").write_text(
                    json.dumps({"_state_machine": {"hand": hand_record}}), encoding="utf-8")
    return weapons, rig


def run_main(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = mdo.main(argv)
    return code, out.getvalue(), err.getvalue()


def snapshot(folder: Path) -> dict[str, tuple[int, int]]:
    if not folder.is_dir():
        return {}
    return {p.relative_to(folder).as_posix(): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in folder.rglob("*") if p.is_file()}


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    return text[i:text.index(end, i + len(start))]


# Fixture weapons. Since D88 (2026-10-20) every weapon drafted is installed
# and SWAPS is empty, so two fictitious weapons stand in for the build, hand
# and installed tests, as FIXTURE_ENEMY does for the rotation rules. Their
# placeholders are IWAD sprites no class of ours uses (Freedoom's super
# shotgun SHT2 and chainsaw SAWG, so the IWAD check has frames to find); their
# state files are written into a temporary copy of src/zscript/, which
# mdo.ZS_ROOT points at while they run.
REAL_SWAPS = mdo.SWAPS
FIXTURE_WEAPONS = (
    mdo.Swap("weapons", "ssg", "weapons/fixture_ssg.zs", "SHT2", "SDXS"),
    mdo.Swap("weapons", "saw", "weapons/fixture_saw.zs", "SAWG", "SDXW"),
)
FIXTURE_ZS = {
    "weapons/fixture_ssg.zs": ("States\n{\nReady:\n\tSHT2 A 1 A_WeaponReady;\n\tLoop;\nFire:\n"
                               "\tSHT2 A 3;\n\tSHT2 B 7 A_FireBullets(11.2, 7.1, 20, 5);\n\tSHT2 C 7;\n"
                               "\tGoto Ready;\nSpawn:\n\tSDXP A -1;\n\tStop;\n}\n"),
    "weapons/fixture_saw.zs": ("States\n{\nReady:\n\tSAWG CD 4 A_WeaponReady;\n\tLoop;\nFire:\n"
                               "\tSAWG AB 4 A_Saw;\n\tSAWG B 0 A_ReFire;\n\tGoto Ready;\n}\n"),
}
_fixture_dir: tempfile.TemporaryDirectory | None = None


def fixture_zs_root() -> Path:
    """src/zscript/ copied once into a temporary folder, plus the fixtures."""
    global _fixture_dir
    if _fixture_dir is None:
        _fixture_dir = tempfile.TemporaryDirectory()
        root = Path(_fixture_dir.name) / "zscript"
        shutil.copytree(mdo.ZS_ROOT, root)
        for rel, text in FIXTURE_ZS.items():
            (root / rel).write_text(text, encoding="utf-8")
    return Path(_fixture_dir.name) / "zscript"


def tearDownModule():
    if _fixture_dir is not None:
        _fixture_dir.cleanup()


class _FixtureWeapons(unittest.TestCase):
    """SWAPS holds the two fixture weapons and ZS_ROOT the copy with their
    state files; no test of its own."""

    def setUp(self):
        for name, value in (("SWAPS", FIXTURE_WEAPONS), ("ZS_ROOT", fixture_zs_root())):
            patcher = mock.patch.object(mdo, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)


# ------------------------------------------------------------------ contract
class ContractTests(unittest.TestCase):
    def test_swaps_match_mod_spec(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        placeholders = section(spec, "### 5.1 IWAD sprites used as placeholders", "## 6. ZScript")
        reserved = section(spec, "### 6.3 Sprites to be drawn", "### 6.4")
        for swap in REAL_SWAPS:
            self.assertIn(f"| `{swap.placeholder}` | sprite |", placeholders, f"{swap.placeholder} not in 5.1")
            self.assertIn(f"`{swap.draft}`", reserved, f"{swap.draft} not reserved in 6.3")

    def test_swaps_match_gen_weapon(self):
        src = GEN_WEAPON.read_text(encoding="utf-8")
        consts = {}
        for m in re.finditer(r"^(\w+)_SPRITE, (\w+)_FLASH, (\w+)_PICKUP = \"(\w{4})\", \"(\w{4})\", \"(\w{4})\"",
                             src, re.M):
            consts[m.group(1)] = (m.group(4), m.group(5), m.group(6))
        specs = re.findall(r'WeaponSpec\("(\w+)",.*?(\w+)_SPRITE,\s*\w+_FLASH,\s*\w+_PICKUP,\s*'
                           r'"(\w{4})",\s*"(\w{4})",\s*"(\w{4})"', src, re.S)
        self.assertEqual(len(specs), 5, "gen_weapon.py's WEAPONS table changed shape")
        pairs = ({(s.placeholder, s.draft) for s in REAL_SWAPS} | set(mdo.INSTALLED)
                 | set(mdo.INSTALLED_WEAPON_FRAMES))
        for key, prefix, *placeholders in specs:
            for ph, ours in zip(placeholders, consts[prefix]):
                self.assertIn((ph, ours), pairs, f"{key}: gen_weapon says {ph} -> {ours}")
        axe = re.search(r'^AXE_SPRITE, AXE_PICKUP = "(\w{4})", "(\w{4})"', src, re.M).groups()
        self.assertIn(("PUNG", axe[0]), pairs)
        self.assertIn(("CSAW", axe[1]), pairs)
        for ph, ours in zip(("CHGG", "CHGF", "MGUN"), consts["PPSH"]):
            self.assertIn((ph, ours), pairs)

    def test_no_enemy_swap_is_left_after_d55(self):
        """The rifleman's POSS -> SDRR was the last enemy swap: installed by
        D55 with the hound, both recorded in INSTALLED_ENEMIES instead."""
        self.assertEqual([s for s in REAL_SWAPS if s.group != "weapons"], [])
        self.assertIn(("POSS", "SDRR"), mdo.INSTALLED_ENEMIES)
        self.assertIn(("SARG", "SDHN"), mdo.INSTALLED_ENEMIES)

    def test_no_weapon_swap_is_left_after_d88(self):
        """The ice axe's PUNG -> SDAX was the last weapon swap (D88)."""
        self.assertEqual(REAL_SWAPS, ())
        self.assertIn(("PUNG", "SDAX"), mdo.INSTALLED_WEAPON_FRAMES)

    def test_fixture_weapons_are_iwad_sprites_no_class_of_ours_uses(self):
        for swap in FIXTURE_WEAPONS:
            for path in sorted(mdo.ZS_ROOT.rglob("*.zs")):
                self.assertEqual(mdo.state_letters(path.read_text(encoding="utf-8"), swap.placeholder), "",
                                 f"{path.name} names {swap.placeholder}")
            self.assertNotIn(swap.draft, mdo.installed_sprites())

    def test_every_placeholder_is_still_named_by_its_state_file(self):
        for swap in REAL_SWAPS:
            self.assertTrue(real_letters(swap), f"src/zscript/{swap.zs} no longer names {swap.placeholder}")

    def test_state_letters_parser(self):
        text = ("States {\n Spawn:\n  POSS AB 10 A_Look; // POSS Z 1\n /* POSS Y 2; */\n"
                "  POSS PQRST 5;\n  POSSX A 1;\n  #### # 0;\n }\n")
        self.assertEqual(mdo.state_letters(text, "POSS"), "ABPQRST")

    def test_run_sh_appends_extra_args_after_the_mods_file(self):
        """GZDoom collects every `-file` in command-line order (FArgs::CollectFiles),
        so an extra `-file` given to run.sh lands after dist/sovietdoom.pk3."""
        text = RUN_SH.read_text(encoding="utf-8")
        self.assertRegex(text, r'ARGS=\(-iwad "\$IWAD_PATH" -file "\$PK3"')
        self.assertRegex(text, r'exec "\$GZDOOM_BIN" "\$\{ARGS\[@\]\}" "\$@"\s*$')


# --------------------------------------------------------------------- build
class _Fixture(_FixtureWeapons):
    """Synthetic drafts in a temporary folder; no test of its own."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.weapons, self.rig = make_drafts(self.root)
        self.out = self.root / "out" / "overlay.pk3"
        self.no_iwad = self.root / "none.wad"

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, *extra: str, out: Path | None = None) -> tuple[int, str, str]:
        return run_main(["--out", str(out or self.out), "--weapons-dir", str(self.weapons),
                         "--rig-dir", str(self.rig), "--iwad", str(self.no_iwad),
                         "--sprites-dir", str(self.root / "no-sprites"), *extra])

    def members(self) -> list[str]:
        with zipfile.ZipFile(self.out) as zf:
            return zf.namelist()


class BuildTests(_Fixture):
    def test_builds_in_a_temporary_folder(self):
        code, out, err = self.build()
        self.assertEqual(code, 0, err)
        self.assertTrue(self.out.is_file())
        self.assertTrue(self.out.with_suffix(".txt").is_file())
        self.assertIn("NOT APPROVED ART", self.out.with_suffix(".txt").read_text(encoding="utf-8"))
        expected = sum(len(real_letters(s)) for s in mdo.SWAPS)   # weapons only since D55: rotation 0 each
        self.assertEqual(len(self.members()), expected)

    def test_holds_only_sprites(self):
        self.build()
        for name in self.members():
            self.assertRegex(name, LUMP_PATH)
        with zipfile.ZipFile(self.out) as zf:
            for name in zf.namelist():
                self.assertTrue(zf.read(name).startswith(mdo.PNG_SIGNATURE), name)
        self.assertFalse(any("proposed" in n or "Z0" in n for n in self.members()))

    def test_every_lump_is_a_frame_a_state_uses(self):
        self.build()
        letters = {s.placeholder: real_letters(s) for s in mdo.SWAPS}
        for name in self.members():
            sprite, letter, _ = LUMP_PATH.match(name).groups()
            self.assertIn(sprite, letters, name)
            self.assertIn(letter, letters[sprite], name)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not present (CI has no IWAD)")
    def test_every_lump_replaces_a_frame_of_the_iwad(self):
        self.build()
        sprites = mdo.iwad_sprites(IWAD)
        for name in self.members():
            sprite, letter, _ = LUMP_PATH.match(name).groups()
            rots, _ = mdo.iwad_rotations(sprites, sprite, letter)
            self.assertTrue(rots, f"{name}: {sprite}{letter} is not in {IWAD.name}")

    def test_png_bytes_and_grab_unchanged(self):
        self.build()
        with zipfile.ZipFile(self.out) as zf:
            for e in mdo.plan_overlay("all", "E", self.weapons, self.rig).entries:
                data = zf.read(e.path)
                self.assertEqual(data, e.source.read_bytes(), e.path)
                self.assertEqual(mdo.read_grab(data), e.grab)
        self.assertIn("grAb", self.out.with_suffix(".txt").read_text(encoding="utf-8"))

    def test_deterministic(self):
        self.build()
        first = self.out.read_bytes()
        self.build()
        self.assertEqual(first, self.out.read_bytes())

    def test_only_filters(self):
        self.build("--only", "weapons")
        weapons = {s.placeholder for s in mdo.SWAPS if s.group == "weapons"}
        self.assertTrue(all(LUMP_PATH.match(n).group(1) in weapons for n in self.members()))
        code, _, err = self.build("--only", "enemies", out=self.root / "out" / "enemies.pk3")
        self.assertEqual(code, 1, "no enemy swap is left since D55")
        self.assertIn("nothing to pack", err)
        self.assertFalse((self.root / "out" / "enemies.pk3").exists())

    def test_dry_run_writes_nothing(self):
        code, out, _ = self.build("--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists())
        self.assertIn("sprites/SHT2A0.png", out)

    def test_default_names(self):
        self.assertEqual(mdo.default_out("all", "E").name, "sd-draft-sprites.pk3")
        self.assertEqual(mdo.default_out("weapons", "B").name, "sd-draft-weapons-handB.pk3")
        self.assertEqual(mdo.default_out("enemies", "B").name, "sd-draft-enemies.pk3")
        self.assertEqual(mdo.default_out("all", "E").parent, PROJECT_ROOT / "work" / "overlays")


class IsolationTests(_Fixture):
    def test_nothing_changes_under_src_or_dist(self):
        before = {d: snapshot(PROJECT_ROOT / d) for d in ("src", "dist")}
        code, _, err = self.build()
        self.assertEqual(code, 0, err)
        for d, snap in before.items():
            self.assertEqual(snapshot(PROJECT_ROOT / d), snap, f"{d}/ changed")

    def test_refuses_to_write_under_src_dist_or_assets(self):
        for d in mdo.FORBIDDEN_OUT:
            target = PROJECT_ROOT / d / "zz-draft-overlay-test" / "x.pk3"
            code, _, err = self.build(out=target)
            self.assertEqual(code, 1, d)
            self.assertIn(f"under {d}/", err)
            self.assertFalse(target.parent.exists(), target)
        with self.assertRaises(mdo.OverlayError):
            mdo.guard_out(PROJECT_ROOT / "dist")


# ----------------------------------------------------------------- rotations
# An enemy drafted on the rig, for the rotation rules. Until D55 the
# rifleman (POSS -> SDRR) was the real one; both names are installed now,
# so a fictitious pair stands in and SWAPS is patched to hold it alone.
FIXTURE_ENEMY = mdo.Swap("enemies", "", "monsters/fixture_enemy.zs", "XPOS", "SDXR")


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "zs" / "monsters").mkdir(parents=True)
        (self.root / "zs" / "monsters" / "fixture_enemy.zs").write_text(
            "States\n{\nSpawn:\n\tXPOS A 10;\n\tLoop;\nDeath:\n\tXPOS H -1;\n\tStop;\n}\n", encoding="utf-8")
        self.rig = self.root / "rig"
        self.rig.mkdir()
        patcher = mock.patch.object(mdo, "SWAPS", (FIXTURE_ENEMY,))
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, *names: str, grab=(1, 2)):
        for n in names:
            (self.rig / f"{n}.png").write_bytes(png(grab))

    def plan(self) -> mdo.Plan:
        return mdo.plan_overlay("enemies", "E", self.root / "weapons", self.rig, self.root / "zs")

    def test_complete_frame_is_packed(self):
        self.put(*(f"SDXRA{r}" for r in mdo.ROTATIONS_8), "SDXRH0")
        lumps = sorted(e.lump for e in self.plan().entries)
        self.assertEqual(lumps, [f"XPOSA{r}" for r in mdo.ROTATIONS_8] + ["XPOSH0"])

    def test_partial_rotations_refused(self):
        self.put("SDXRA1", "SDXRA2", "SDXRA3", "SDXRH0")
        with self.assertRaisesRegex(mdo.OverlayError, "needs all of 12345678"):
            self.plan()

    def test_rotation_zero_mixed_with_rotations_refused(self):
        self.put(*(f"SDXRA{r}" for r in mdo.ROTATIONS_8), "SDXRA0")
        with self.assertRaisesRegex(mdo.OverlayError, "both rotation 0"):
            self.plan()

    def test_missing_grab_refused(self):
        self.put("SDXRH0", grab=None)
        with self.assertRaisesRegex(mdo.OverlayError, "no grAb"):
            self.plan()

    def test_missing_frame_keeps_the_iwads(self):
        self.put("SDXRH0")
        plan = self.plan()
        self.assertEqual([e.lump for e in plan.entries], ["XPOSH0"])
        self.assertTrue(any(m.startswith("XPOSA") for m in plan.missing))

    def iwad_check(self, names: list[str]) -> mdo.Plan:
        self.put(*(f"SDXRA{r}" for r in mdo.ROTATIONS_8), "SDXRH0")
        path = self.root / "fake.wad"
        path.write_bytes(wad(["S_START", *names, "S_END"]))
        plan = self.plan()
        mdo.check_against_iwad(plan, mdo.iwad_sprites(path))
        return plan

    def test_iwad_mirrored_pairs_are_hidden(self):
        plan = self.iwad_check(["XPOSA1", "XPOSA2A8", "XPOSA3A7", "XPOSA4A6", "XPOSA5", "XPOSH0"])
        self.assertIn("XPOSA: hides 3 mirrored pair lump(s) of the IWAD", plan.notes)

    def test_iwad_rotation_zero_under_rotated_frame_refused(self):
        with self.assertRaisesRegex(mdo.OverlayError, "IWAD has rotation 0"):
            self.iwad_check(["XPOSA0", "XPOSH0"])

    def test_iwad_sixteen_angles_refused(self):
        with self.assertRaisesRegex(mdo.OverlayError, "16-angle"):
            self.iwad_check([*(f"XPOSA{r}" for r in "123456789ABCDEFG"), "XPOSH0"])

    def test_rotation_zero_over_rotated_iwad_frame_is_fine(self):
        plan = self.iwad_check(["XPOSA1", "XPOSH1", "XPOSH2A8"])
        self.assertEqual(len(plan.entries), 9)

    def test_iwad_rotations_reads_both_halves_of_a_pair(self):
        rots, pairs = mdo.iwad_rotations({"XPOSA2A8", "XPOSB2A8", "XPOSA1"}, "XPOS", "A")
        self.assertEqual(rots, {"1", "2", "8"})
        self.assertEqual(pairs, 2)


# ---------------------------------------------------------------------- hand
class HandTests(_FixtureWeapons):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_other_hand_without_renders_refused(self):
        weapons, rig = make_drafts(self.root, hand_record="E")
        with self.assertRaisesRegex(mdo.OverlayError, "hand E, not B"):
            mdo.plan_overlay("weapons", "B", weapons, rig)

    def test_unrecorded_hand_is_assumed_default_only(self):
        weapons, rig = make_drafts(self.root, hand_record=None)
        plan = mdo.plan_overlay("weapons", "E", weapons, rig)
        self.assertIn("assumed", plan.hands["ssg"])
        with self.assertRaisesRegex(mdo.OverlayError, "no renders of hand B"):
            mdo.plan_overlay("weapons", "B", weapons, rig)

    def test_hand_folder_is_preferred(self):
        weapons, rig = make_drafts(self.root, hand_record="E")
        alt = weapons / "hand_B"
        for item in {s.item for s in mdo.SWAPS if s.group == "weapons"}:
            (alt / item).mkdir(parents=True)
            for f in (weapons / item).glob("SD*.png"):
                (alt / item / f.name).write_bytes(png((99, 99)))
        plan = mdo.plan_overlay("weapons", "B", weapons, rig)
        self.assertTrue(all(e.grab == (99, 99) for e in plan.entries))
        self.assertTrue(all(h.startswith("B") for h in plan.hands.values()))

    def test_one_item_with_its_own_hand(self):
        """--hand G --item saw: only that weapon, from hand_G/saw/ (a
        weapon's Gemini frames, as the arsenal's were before D79, D84 and
        D88 installed them), and the other weapon's missing hand G is no
        error."""
        weapons, rig = make_drafts(self.root, hand_record="E")
        alt = weapons / "hand_G" / "saw"
        alt.mkdir(parents=True)
        for f in (weapons / "saw").glob("SD*.png"):
            (alt / f.name).write_bytes(png((77, 77)))
        plan = mdo.plan_overlay("weapons", "G", weapons, rig, item="saw")
        self.assertTrue(plan.entries)
        self.assertTrue(all(e.swap.item == "saw" and e.grab == (77, 77) for e in plan.entries))
        self.assertEqual(set(plan.hands), {"saw"})
        self.assertEqual(mdo.default_out("weapons", "G", "saw").name, "sd-draft-weapons-handG-saw.pk3")

    def test_hand_letter_validated(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            mdo.main(["--hand", "BB", "--dry-run"])


# ----------------------------------------------------------------- installed
class InstalledTests(_FixtureWeapons):
    """D48: the six world pickups ship from assets/sprites/; the overlay
    must never carry them, nor anything else already installed. The fixture
    weapons stand in for the drafts still waiting (none since D88)."""

    def test_installed_pickups_are_not_swapped(self):
        swapped = {n for s in REAL_SWAPS + FIXTURE_WEAPONS for n in (s.draft, s.placeholder)}
        for placeholder, ours in mdo.INSTALLED:
            self.assertNotIn(ours, swapped)
            self.assertNotIn(placeholder, swapped)

    def test_installed_pickups_are_the_spawn_states_and_ship(self):
        names = {p.stem for p in mdo.SPRITES_DIR.rglob("*.png")} if mdo.SPRITES_DIR.is_dir() else set()
        texts = "\n".join(p.read_text(encoding="utf-8") for p in (mdo.ZS_ROOT / "weapons").glob("*.zs"))
        for placeholder, ours in mdo.INSTALLED:
            self.assertIn(f"{ours}A0", names, f"{ours}A0 is not under assets/sprites/")
            self.assertRegex(texts, rf"\n\s*{ours} A -1;", f"no Spawn state shows {ours}")
            self.assertEqual(mdo.state_letters(texts, placeholder), "", f"{placeholder} is still named")
            self.assertEqual(mdo.installed_sprites() & {ours}, {ours})

    def test_a_swap_already_installed_is_skipped(self):
        """A held sprite under assets/sprites/ is skipped, its flash still
        packed. A fixture weapon (XHLG -> SDXH, XHLF -> SDXF) stands in
        since D84 left the ice axe's single swap the only real one."""
        held = mdo.Swap("weapons", "fixture", "weapons/fixture.zs", "XHLG", "SDXH")
        flash = mdo.Swap("weapons", "fixture", "weapons/fixture.zs", "XHLF", "SDXF")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zs = root / "zs" / "weapons"
            zs.mkdir(parents=True)
            (zs / "fixture.zs").write_text("States\n{\nReady:\n\tXHLG A 1;\n\tLoop;\nFlash:\n"
                                           "\tXHLF A 3 Bright;\n\tStop;\n}\n", encoding="utf-8")
            folder = root / "weapons" / "fixture"
            folder.mkdir(parents=True)
            for name in ("SDXHA0", "SDXFA0"):
                (folder / f"{name}.png").write_bytes(png())
            sprites = root / "sprites" / "fixture"
            sprites.mkdir(parents=True)
            (sprites / "SDXHA0.png").write_bytes(png())
            with mock.patch.object(mdo, "SWAPS", (held, flash)):
                plan = mdo.plan_overlay("weapons", "E", root / "weapons", root / "rig", zs_root=root / "zs",
                                        sprites_dir=root / "sprites")
            self.assertFalse(any(e.lump.startswith("XHLG") for e in plan.entries))
            self.assertTrue(any(e.lump.startswith("XHLF") for e in plan.entries))
            self.assertTrue(any(n.startswith("SDXH: approved and installed") for n in plan.notes), plan.notes)

    def test_a_swap_naming_the_installed_ppsh_frames_is_skipped(self):
        """D79: the PPSh-41's old swaps (hand E and the Gemini test, hand G)
        are never packed again, whatever drafts are on disk."""
        old = (mdo.Swap("weapons", "ppsh", "weapons/ppsh.zs", "CHGG", "SDPP"),
               mdo.Swap("weapons", "ppsh", "weapons/ppsh.zs", "CHGF", "SDPF"))
        self.assertEqual(mdo.INSTALLED_WEAPON_FRAMES[2:4], (("CHGG", "SDPP"), ("CHGF", "SDPF")))
        self.assertFalse([s for s in mdo.SWAPS if s.item == "ppsh"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            for folder in (weapons / "ppsh", weapons / "hand_G" / "ppsh"):
                folder.mkdir(parents=True, exist_ok=True)
                for name in ("SDPPA0", "SDPPB0", "SDPFA0"):
                    (folder / f"{name}.png").write_bytes(png())
            with mock.patch.object(mdo, "SWAPS", mdo.SWAPS + old):
                plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "no-sprites")
            self.assertFalse(any(e.lump.startswith(("CHGG", "CHGF", "SDPP", "SDPF")) for e in plan.entries))
            for draft in ("SDPP", "SDPF"):
                self.assertTrue(any(n.startswith(f"{draft}: held and flash frames installed whole")
                                    for n in plan.notes), plan.notes)

    def test_a_swap_naming_the_d84_and_d88_weapons_is_skipped(self):
        """D84 and D88: the IZh-58's, RPG-7's, ROKS-3's, hand Katyusha's and
        ice axe's old swaps (hand E and the Gemini drafts, hand G) are never
        packed again, nor the Katyusha's pickup (D80), whatever drafts are
        on disk."""
        frames = {"izh": ("weapons/izh.zs", (("SHTG", "SDIZ"), ("SHTF", "SDIF"))),
                  "rpg7": ("weapons/rpg7.zs", (("MISG", "SDRL"), ("MISF", "SDRF"))),
                  "roks3": ("weapons/roks3.zs", (("PLSG", "SDRK"), ("PLSF", "SDKF"))),
                  "katyusha": ("weapons/katyusha.zs", (("BFGG", "SDHK"), ("BFGF", "SDHF"))),
                  "ice_axe": ("weapons/ice_axe.zs", (("PUNG", "SDAX"),))}
        self.assertEqual(mdo.INSTALLED_WEAPON_FRAMES[4:],
                         tuple(pair for _, pairs in frames.values() for pair in pairs))
        self.assertIn(("BFUG", "SDHP"), mdo.INSTALLED)
        self.assertEqual(REAL_SWAPS, (), "no weapon waits since D88")
        old = tuple(mdo.Swap("weapons", item, zs, ph, ours)
                    for item, (zs, pairs) in frames.items() for ph, ours in pairs)
        old += (mdo.Swap("weapons", "katyusha", "weapons/katyusha.zs", "BFUG", "SDHP"),)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            for swap in old:
                for folder in (weapons / swap.item, weapons / "hand_G" / swap.item):
                    folder.mkdir(parents=True, exist_ok=True)
                    for letter in "ABCD":
                        (folder / f"{swap.draft}{letter}0.png").write_bytes(png())
            with mock.patch.object(mdo, "SWAPS", mdo.SWAPS + old):
                plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "no-sprites")
            names = {n for s in old for n in (s.placeholder, s.draft)}
            self.assertFalse(any(e.lump[:4] in names for e in plan.entries))
            self.assertTrue(plan.entries, "the fixture weapons are still packed")
            for _, pairs in frames.values():
                for _, draft in pairs:
                    self.assertTrue(any(n.startswith(f"{draft}: held and flash frames installed whole")
                                        for n in plan.notes), plan.notes)

    def test_a_swap_naming_the_installed_tt33_frames_is_skipped(self):
        """N17: even with the hand E drafts on disk and nothing under
        assets/sprites/, the TT-33's old swaps are never packed again."""
        old = (mdo.Swap("weapons", "tt33", "weapons/tokarev.zs", "PISG", "SDTT"),
               mdo.Swap("weapons", "tt33", "weapons/tokarev.zs", "PISF", "SDTF"))
        self.assertEqual(mdo.INSTALLED_WEAPON_FRAMES[:2], (("PISG", "SDTT"), ("PISF", "SDTF")))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            folder = weapons / "tt33"
            folder.mkdir(parents=True)
            for name in ("SDTTA0", "SDTTB0", "SDTTC0", "SDTFA0"):
                (folder / f"{name}.png").write_bytes(png())
            (folder / "metrics.json").write_text(json.dumps({"_state_machine": {"hand": "E"}}), encoding="utf-8")
            with mock.patch.object(mdo, "SWAPS", mdo.SWAPS + old):
                plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "no-sprites")
            self.assertFalse(any(e.lump.startswith(("PISG", "PISF", "SDTT", "SDTF")) for e in plan.entries))
            for draft in ("SDTT", "SDTF"):
                self.assertTrue(any(n.startswith(f"{draft}: held and flash frames installed whole")
                                    for n in plan.notes), plan.notes)


    def test_the_legion_is_installed_whole_and_never_overlaid(self):
        """D54: SDLT ships from assets/sprites/legion/ and every trooper state
        names it; the overlay names neither SPOS nor SDLT."""
        self.assertIn(("SPOS", "SDLT"), mdo.INSTALLED_ENEMIES)
        swapped = {s.draft for s in mdo.SWAPS} | {s.placeholder for s in mdo.SWAPS}
        self.assertFalse(swapped & {"SPOS", "SDLT"})
        text = (mdo.ZS_ROOT / "monsters" / "legion_trooper.zs").read_text(encoding="utf-8")
        self.assertEqual(mdo.state_letters(text, "SPOS"), "")
        self.assertEqual(mdo.state_letters(text, "SDLT"), "ABCDEFGHIJKLMNOPQRSTU")

    def test_a_swap_naming_an_installed_enemy_is_skipped(self):
        """Even with drafts on disk and nothing under assets/sprites/, a swap
        for the Legion is never packed."""
        legion = mdo.Swap("enemies", "", "monsters/legion_trooper.zs", "SPOS", "SDLT")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            for letter in "ABCDEFG":
                for rot in mdo.ROTATIONS_8:
                    (rig / f"SDLT{letter}{rot}.png").write_bytes(png())
            with mock.patch.object(mdo, "SWAPS", mdo.SWAPS + (legion,)):
                plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "no-sprites")
            self.assertFalse(any(e.lump.startswith(("SPOS", "SDLT")) for e in plan.entries))
            self.assertTrue(any(n.startswith("SDLT: an enemy installed whole") for n in plan.notes), plan.notes)

    def test_the_rifleman_and_the_hound_are_installed_whole_and_never_overlaid(self):
        """D55: SDRR and SDHN ship from assets/sprites/rifleman/ and hound/
        and every state names them; the overlay names neither side."""
        self.assertEqual(mdo.INSTALLED_ENEMIES[:3], (("SPOS", "SDLT"), ("POSS", "SDRR"), ("SARG", "SDHN")))
        swapped = {s.draft for s in mdo.SWAPS} | {s.placeholder for s in mdo.SWAPS}
        self.assertFalse(swapped & {"POSS", "SDRR", "SARG", "SDHN"})
        for zs, old, new, letters in (("reich_rifleman.zs", "POSS", "SDRR", "ABCDEFGHIJKLMNOPQRSTU"),
                                      ("reich_hound.zs", "SARG", "SDHN", "ABCDEFGHIJKLMN")):
            text = (mdo.ZS_ROOT / "monsters" / zs).read_text(encoding="utf-8")
            self.assertEqual(mdo.state_letters(text, old), "", zs)
            self.assertEqual(mdo.state_letters(text, new), letters, zs)
            self.assertIn(new, mdo.installed_sprites())

    def test_the_stormtrooper_and_his_bolt_are_installed_whole_and_never_overlaid(self):
        """D56: SDHS and SDBL ship from assets/sprites/storm/ and every state
        names them; the overlay names neither side."""
        self.assertEqual(mdo.INSTALLED_ENEMIES[3:5], (("TROO", "SDHS"), ("BAL1", "SDBL")))
        swapped = {s.draft for s in mdo.SWAPS} | {s.placeholder for s in mdo.SWAPS}
        self.assertFalse(swapped & {"TROO", "SDHS", "BAL1", "SDBL"})
        for zs, old, new, letters in (("stormtrooper.zs", "TROO", "SDHS", "ABCDEFGHIJKLMNOPQRSTU"),
                                      ("storm_bolt.zs", "BAL1", "SDBL", "ABCDE")):
            text = (mdo.ZS_ROOT / "monsters" / zs).read_text(encoding="utf-8")
            self.assertEqual(mdo.state_letters(text, old), "", zs)
            self.assertEqual(mdo.state_letters(text, new), letters, zs)
            self.assertIn(new, mdo.installed_sprites())

    def test_a_swap_naming_the_rifleman_is_skipped(self):
        """Even with the rig's SDRR renders on disk and nothing under
        assets/sprites/, the old rifleman swap is never packed again."""
        rifle = mdo.Swap("enemies", "", "monsters/reich_rifleman.zs", "POSS", "SDRR")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            for letter in "ABCDEFG":
                for rot in mdo.ROTATIONS_8:
                    (rig / f"SDRR{letter}{rot}.png").write_bytes(png())
            with mock.patch.object(mdo, "SWAPS", mdo.SWAPS + (rifle,)):
                plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "no-sprites")
            self.assertFalse(any(e.lump.startswith(("POSS", "SDRR")) for e in plan.entries))
            self.assertTrue(any(n.startswith("SDRR: an enemy installed whole") for n in plan.notes), plan.notes)


# ---------------------------------------------------------------------- real
@unittest.skipUnless((mdo.WEAPONS_DIR / "tt33").is_dir(), "work/art drafts not present (CI has no work/)")
class RealDraftTests(unittest.TestCase):
    """37 until D48 installed the six pickups; +70 POSS until D55; 31 until
    N17 installed the TT-33's held and flash frames (PISG A-C, PISF A); 27
    until D79 installed the PPSh-41's (CHGG A-B, CHGF A); 24 until D84
    installed the IZh-58's, RPG-7's, ROKS-3's and hand Katyusha's (SHTG A-D,
    SHTF A-B, MISG A-B, MISF A-D, PLSG A-B, PLSF A, BFGG A-B, BFGF A-B) and
    the Katyusha's pickup (BFUG A, D80); 4 until D88 installed the ice axe's
    (PUNG A-D). Since then the real overlay has nothing to pack."""

    def test_todays_drafts(self):
        with self.assertRaisesRegex(mdo.OverlayError, "nothing to pack"):
            mdo.plan_overlay()

    def test_builds_nothing_from_todays_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sd-draft-sprites.pk3"
            code, _, err = run_main(["--out", str(out)])
            self.assertEqual(code, 1, err)
            self.assertIn("nothing to pack", err)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
