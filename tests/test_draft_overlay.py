"""Contract of tools/make_draft_overlay.py, the DRAFT sprite overlay
(MOD-SPEC 6.9): a separate PK3, loaded after the mod, that wears our
unapproved weapon and rifleman drafts under the Freedoom placeholder names
our states use today.

What is checked, and why:

  contract   the placeholder -> draft table agrees with MOD-SPEC 5.1 and
             6.3 and with gen_weapon.py's WeaponSpec; every placeholder is
             still named by its state file; run.sh hands extra arguments to
             GZDoom after its own `-file`, which is what puts the overlay
             above the mod
  build      the PK3 is built in a temporary folder from synthetic drafts
             (CI has no work/ and no IWAD), holds only sprites/*.png, every
             lump is a frame a state uses (and, with the IWAD, a frame the
             IWAD has), the PNG bytes and so the grAb offsets are unchanged,
             two builds are byte-identical
  isolation  nothing under src/ or dist/ changes, and an --out under src/,
             dist/ or assets/ is refused
  rotations  a rotated frame with fewer than eight rotations, or mixing
             rotation 0 with 1-8, is refused; with an IWAD, a rotated frame
             the IWAD has as rotation 0 or 9-G is refused, and mirrored
             pairs (POSSA2A8) are reported as hidden
  hand       --hand picks hand_<X>/ renders, and refuses a hand nobody drew
  installed  the six pickups D48 installed (INSTALLED) are named by their
             Spawn states, ship from assets/sprites/ and are never overlaid;
             a swap whose sprite is under assets/sprites/ is skipped
  real       (skips without work/art) today's drafts plan 101 lumps: 31
             weapon frames (held and flash of all seven, the Katyusha's
             pickup) and the rifleman's 70

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
from pathlib import Path

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
    seed = 0
    for swap in mdo.SWAPS:
        folder = weapons / swap.item if swap.group == "weapons" else rig
        folder.mkdir(parents=True, exist_ok=True)
        for letter in real_letters(swap):
            rots = mdo.ROTATIONS_8 if swap.group == "rifleman" and letter <= "G" else "0"
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


# ------------------------------------------------------------------ contract
class ContractTests(unittest.TestCase):
    def test_swaps_match_mod_spec(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        placeholders = section(spec, "### 5.1 IWAD sprites used as placeholders", "## 6. ZScript")
        reserved = section(spec, "### 6.3 Sprites to be drawn", "### 6.4")
        for swap in mdo.SWAPS:
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
        pairs = {(s.placeholder, s.draft) for s in mdo.SWAPS} | set(mdo.INSTALLED)
        for key, prefix, *placeholders in specs:
            for ph, ours in zip(placeholders, consts[prefix]):
                self.assertIn((ph, ours), pairs, f"{key}: gen_weapon says {ph} -> {ours}")
        axe = re.search(r'^AXE_SPRITE, AXE_PICKUP = "(\w{4})", "(\w{4})"', src, re.M).groups()
        self.assertIn(("PUNG", axe[0]), pairs)
        self.assertIn(("CSAW", axe[1]), pairs)
        for ph, ours in zip(("CHGG", "CHGF", "MGUN"), consts["PPSH"]):
            self.assertIn((ph, ours), pairs)

    def test_rifleman_maps_poss_to_sdrr(self):
        rig = [s for s in mdo.SWAPS if s.group == "rifleman"]
        self.assertEqual([(s.placeholder, s.draft) for s in rig], [("POSS", "SDRR")])

    def test_every_placeholder_is_still_named_by_its_state_file(self):
        for swap in mdo.SWAPS:
            self.assertTrue(real_letters(swap), f"src/zscript/{swap.zs} no longer names {swap.placeholder}")
        rifle = next(s for s in mdo.SWAPS if s.group == "rifleman")
        self.assertEqual(real_letters(rifle), "ABCDEFGHIJKLMNOPQRSTU")

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
class _Fixture(unittest.TestCase):
    """Synthetic drafts in a temporary folder; no test of its own."""

    def setUp(self):
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
        expected = sum(len(real_letters(s)) for s in mdo.SWAPS) + 7 * 7   # POSS A-G: 8 rotations, not 1
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
        self.assertFalse(any(n.startswith("sprites/POSS") for n in self.members()))
        self.build("--only", "rifleman")
        self.assertTrue(all(n.startswith("sprites/POSS") for n in self.members()))

    def test_dry_run_writes_nothing(self):
        code, out, _ = self.build("--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(self.out.exists())
        self.assertIn("sprites/POSSA1.png", out)

    def test_default_names(self):
        self.assertEqual(mdo.default_out("all", "E").name, "sd-draft-sprites.pk3")
        self.assertEqual(mdo.default_out("weapons", "B").name, "sd-draft-weapons-handB.pk3")
        self.assertEqual(mdo.default_out("rifleman", "B").name, "sd-draft-rifleman.pk3")
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
class RotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "zs" / "monsters").mkdir(parents=True)
        (self.root / "zs" / "monsters" / "reich_rifleman.zs").write_text(
            "States\n{\nSpawn:\n\tPOSS A 10;\n\tLoop;\nDeath:\n\tPOSS H -1;\n\tStop;\n}\n", encoding="utf-8")
        self.rig = self.root / "rig"
        self.rig.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, *names: str, grab=(1, 2)):
        for n in names:
            (self.rig / f"{n}.png").write_bytes(png(grab))

    def plan(self) -> mdo.Plan:
        return mdo.plan_overlay("rifleman", "E", self.root / "weapons", self.rig, self.root / "zs")

    def test_complete_frame_is_packed(self):
        self.put(*(f"SDRRA{r}" for r in mdo.ROTATIONS_8), "SDRRH0")
        lumps = sorted(e.lump for e in self.plan().entries)
        self.assertEqual(lumps, [f"POSSA{r}" for r in mdo.ROTATIONS_8] + ["POSSH0"])

    def test_partial_rotations_refused(self):
        self.put("SDRRA1", "SDRRA2", "SDRRA3", "SDRRH0")
        with self.assertRaisesRegex(mdo.OverlayError, "needs all of 12345678"):
            self.plan()

    def test_rotation_zero_mixed_with_rotations_refused(self):
        self.put(*(f"SDRRA{r}" for r in mdo.ROTATIONS_8), "SDRRA0")
        with self.assertRaisesRegex(mdo.OverlayError, "both rotation 0"):
            self.plan()

    def test_missing_grab_refused(self):
        self.put("SDRRH0", grab=None)
        with self.assertRaisesRegex(mdo.OverlayError, "no grAb"):
            self.plan()

    def test_missing_frame_keeps_the_iwads(self):
        self.put("SDRRH0")
        plan = self.plan()
        self.assertEqual([e.lump for e in plan.entries], ["POSSH0"])
        self.assertTrue(any(m.startswith("POSSA") for m in plan.missing))

    def iwad_check(self, names: list[str]) -> mdo.Plan:
        self.put(*(f"SDRRA{r}" for r in mdo.ROTATIONS_8), "SDRRH0")
        path = self.root / "fake.wad"
        path.write_bytes(wad(["S_START", *names, "S_END"]))
        plan = self.plan()
        mdo.check_against_iwad(plan, mdo.iwad_sprites(path))
        return plan

    def test_iwad_mirrored_pairs_are_hidden(self):
        plan = self.iwad_check(["POSSA1", "POSSA2A8", "POSSA3A7", "POSSA4A6", "POSSA5", "POSSH0"])
        self.assertIn("POSSA: hides 3 mirrored pair lump(s) of the IWAD", plan.notes)

    def test_iwad_rotation_zero_under_rotated_frame_refused(self):
        with self.assertRaisesRegex(mdo.OverlayError, "IWAD has rotation 0"):
            self.iwad_check(["POSSA0", "POSSH0"])

    def test_iwad_sixteen_angles_refused(self):
        with self.assertRaisesRegex(mdo.OverlayError, "16-angle"):
            self.iwad_check([*(f"POSSA{r}" for r in "123456789ABCDEFG"), "POSSH0"])

    def test_rotation_zero_over_rotated_iwad_frame_is_fine(self):
        plan = self.iwad_check(["POSSA1", "POSSH1", "POSSH2A8"])
        self.assertEqual(len(plan.entries), 9)

    def test_iwad_rotations_reads_both_halves_of_a_pair(self):
        rots, pairs = mdo.iwad_rotations({"POSSA2A8", "POSSB2A8", "POSSA1"}, "POSS", "A")
        self.assertEqual(rots, {"1", "2", "8"})
        self.assertEqual(pairs, 2)


# ---------------------------------------------------------------------- hand
class HandTests(unittest.TestCase):
    def setUp(self):
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
        self.assertIn("assumed", plan.hands["tt33"])
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

    def test_hand_letter_validated(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            mdo.main(["--hand", "BB", "--dry-run"])


# ----------------------------------------------------------------- installed
class InstalledTests(unittest.TestCase):
    """D48: the six world pickups ship from assets/sprites/; the overlay
    must never carry them, nor anything else already installed."""

    def test_installed_pickups_are_not_swapped(self):
        swapped = {s.draft for s in mdo.SWAPS} | {s.placeholder for s in mdo.SWAPS}
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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weapons, rig = make_drafts(root)
            sprites = root / "sprites" / "tt33"
            sprites.mkdir(parents=True)
            (sprites / "SDTTA0.png").write_bytes(png())
            plan = mdo.plan_overlay("all", "E", weapons, rig, sprites_dir=root / "sprites")
            self.assertFalse(any(e.lump.startswith("PISG") for e in plan.entries))
            self.assertTrue(any(e.lump.startswith("PISF") for e in plan.entries))
            self.assertTrue(any(n.startswith("SDTT: approved and installed") for n in plan.notes), plan.notes)


# ---------------------------------------------------------------------- real
@unittest.skipUnless((mdo.RIG_DIR / "SDRRA1.png").is_file() and (mdo.WEAPONS_DIR / "tt33").is_dir(),
                     "work/art drafts not present (CI has no work/)")
class RealDraftTests(unittest.TestCase):
    def test_todays_drafts(self):
        plan = mdo.plan_overlay()
        if IWAD.is_file():
            mdo.check_against_iwad(plan, mdo.iwad_sprites(IWAD))
        poss = [e for e in plan.entries if e.lump.startswith("POSS")]
        self.assertEqual(len(poss), 70)
        self.assertEqual(sum(e.lump[5] != "0" for e in poss), 56)
        self.assertEqual(len(plan.entries) - len(poss), 31)   # 37 until D48 installed the six pickups
        self.assertFalse({e.lump[:4] for e in plan.entries} & {ph for ph, _ in mdo.INSTALLED})
        self.assertEqual(plan.missing, [])
        self.assertTrue(all(h.startswith("E") for h in plan.hands.values()))

    def test_builds_from_todays_drafts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sd-draft-sprites.pk3"
            code, _, err = run_main(["--out", str(out)])
            self.assertEqual(code, 0, err)
            with zipfile.ZipFile(out) as zf:
                self.assertEqual(len(zf.namelist()), 101)


if __name__ == "__main__":
    unittest.main()
