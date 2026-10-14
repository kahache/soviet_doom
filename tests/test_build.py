"""Build the PK3 into a temp dir and check its structure (stdlib unittest).

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(TOOLS_DIR))

import build as build_cli  # noqa: E402
from sdbuild import wad  # noqa: E402
from sdbuild.pk3 import build as build_pk3  # noqa: E402

EXPECTED_ROOT_LUMPS = ("MAPINFO", "LANGUAGE", "zscript.txt")
EXPECTED_MAP_LUMPS = ["MAP01", "TEXTMAP", "ENDMAP"]


def _udmf_blocks(text: str, kind: str) -> list[str]:
    """Return the bodies of all `kind { ... }` blocks in a TEXTMAP."""
    return re.findall(rf"^{kind}\s*\{{(.*?)\}}", text, flags=re.S | re.M)


class BuildPk3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "out" / "sovietdoom.pk3"
        cls.entries = build_pk3(SRC_DIR, cls.out, TOOLS_DIR)
        cls.zf = zipfile.ZipFile(cls.out)
        cls.names = cls.zf.namelist()

    @classmethod
    def tearDownClass(cls):
        cls.zf.close()
        cls.tmp.cleanup()

    def test_zip_is_valid(self):
        self.assertTrue(zipfile.is_zipfile(self.out))
        self.assertIsNone(self.zf.testzip(), "corrupt member in pk3")

    def test_required_files_present(self):
        lowered = {n.lower() for n in self.names}
        self.assertIn("maps/map01.wad", lowered)
        for lump in EXPECTED_ROOT_LUMPS:
            self.assertIn(lump.lower(), lowered, f"{lump} missing from pk3 root")

    def test_root_lump_names_fit_wad_rules(self):
        for n in self.names:
            if "/" not in n:
                self.assertLessEqual(len(Path(n).stem), wad.MAX_LUMP_NAME, n)

    def test_zscript_includes_exist(self):
        text = self.zf.read("zscript.txt").decode("ascii")
        self.assertRegex(text, re.compile(r'^version\s+"4\.\d+"', re.M), "zscript.txt must pin a version")
        lowered = {n.lower() for n in self.names}
        for inc in re.findall(r'#include\s+"([^"]+)"', text):
            self.assertIn(inc.lower(), lowered, f"included file {inc} not in pk3")

    def test_mapinfo_references_language_and_handler(self):
        mapinfo = self.zf.read("MAPINFO").decode("ascii")
        language = self.zf.read("LANGUAGE").decode("utf-8")  # LANGUAGE carries Russian (D7)
        for ident in re.findall(r'lookup\s*=?\s*"([A-Z0-9_]+)"', mapinfo):
            self.assertRegex(language, re.compile(rf"^{ident}\s*=", re.M), f"{ident} missing in LANGUAGE")
        handlers = re.search(r'AddEventHandlers\s*=\s*"([^"]+)"', mapinfo)
        self.assertIsNotNone(handlers, "MAPINFO must register the event handler")
        zs = b"".join(self.zf.read(n) for n in self.names if n.lower().startswith("zscript/"))
        self.assertIn(f"class {handlers.group(1)}".encode(), zs)

    def test_map_wad_structure(self):
        blob = self.zf.read("maps/MAP01.wad")
        self.assertEqual(blob[:4], b"PWAD")
        names = [name for name, _, _ in wad.read_directory(blob)]
        self.assertEqual(names, EXPECTED_MAP_LUMPS)
        self.assertEqual(wad.read_lump(blob, "MAP01"), b"")
        self.assertEqual(wad.read_lump(blob, "ENDMAP"), b"")

    def test_textmap_contents(self):
        blob = self.zf.read("maps/MAP01.wad")
        text = wad.read_lump(blob, "TEXTMAP").decode("ascii")
        self.assertRegex(text, re.compile(r'^namespace\s*=\s*"zdoom";', re.M), "namespace must be zdoom")
        # namespace must be the first statement (comments aside)
        first_stmt = next(l for l in text.splitlines() if l.strip() and not l.startswith("//"))
        self.assertTrue(first_stmt.startswith("namespace"))

        # What the BUILD owes us is a well-formed TEXTMAP: the namespace, a
        # usable player start, and closed geometry. What is IN the map - how
        # many rooms, where the player stands - belongs to the map's own
        # tests, not here. This assertion used to pin the player to (256,256),
        # the centre of the F0 test room, and went red the moment MAP01 became
        # the real Zarya-7 map. A build test must not break when a designer
        # moves a player start.
        things = _udmf_blocks(text, "thing")
        starts = [t for t in things if re.search(r"type\s*=\s*1;", t)]
        self.assertEqual(len(starts), 1, "exactly one Player 1 start")
        player = starts[0]
        for flag in ("skill1", "skill2", "skill3", "skill4", "skill5", "single", "coop", "dm"):
            self.assertRegex(player, rf"{flag}\s*=\s*true;", f"{flag} not set on player start")
        for axis in ("x", "y"):
            self.assertRegex(player, rf"{axis}\s*=\s*-?\d+\.\d+;", f"player start has no {axis}")

        sectors = _udmf_blocks(text, "sector")
        vertices = _udmf_blocks(text, "vertex")
        linedefs = _udmf_blocks(text, "linedef")
        self.assertGreaterEqual(len(sectors), 1)
        self.assertGreaterEqual(len(vertices), 3, "a sector needs at least three vertices")
        self.assertGreaterEqual(len(linedefs), 3)
        for ld in linedefs:
            self.assertRegex(ld, r"sidefront\s*=\s*\d+;", "every linedef needs a front sidedef")
        sidedefs = _udmf_blocks(text, "sidedef")
        self.assertGreaterEqual(len(sidedefs), len(linedefs),
                                "each linedef needs at least its front sidedef")
        for sector in _udmf_blocks(text, "sector"):
            # Values are the designer's; the build only owes us that every
            # sector declares the fields the engine needs to render it.
            for field in ("heightfloor", "heightceiling", "lightlevel"):
                self.assertRegex(sector, rf"{field}\s*=\s*-?\d+;",
                                 f"a sector is missing {field}")

    def test_build_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            again = Path(d) / "again.pk3"
            build_pk3(SRC_DIR, again, TOOLS_DIR)
            self.assertEqual(again.read_bytes(), self.out.read_bytes())

    def test_cli_entry_point(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "cli.pk3"
            rc = build_cli.main(["--out", str(out), "--quiet"])
            self.assertEqual(rc, 0)
            self.assertTrue(zipfile.is_zipfile(out))


class WadWriterTest(unittest.TestCase):
    def test_roundtrip_offsets_and_sizes(self):
        lumps = [("A", b""), ("B", b"hello"), ("C", b"\x01\x02\x03"), ("D", b"")]
        blob = wad.build_pwad(lumps)
        directory = wad.read_directory(blob)
        self.assertEqual([n for n, _, _ in directory], ["A", "B", "C", "D"])
        for name, data in lumps:
            self.assertEqual(wad.read_lump(blob, name), data)
        # directory sits at the end and is 16 bytes per lump
        _, numlumps, infotableofs = wad.HEADER_STRUCT.unpack_from(blob, 0)
        self.assertEqual(numlumps, 4)
        self.assertEqual(len(blob), infotableofs + 16 * 4)

    def test_rejects_bad_names(self):
        for bad in ("", "TOOLONGNAME", "ñ", "a b"):
            with self.assertRaises(wad.WadError):
                wad.validate_lump_name(bad)
        self.assertEqual(wad.validate_lump_name("textmap"), "TEXTMAP")


if __name__ == "__main__":
    unittest.main()


class ApprovedAssetsInPk3Test(unittest.TestCase):
    """Blocker M1 (level-designer, 2026-10-12): the CEO-approved PNGs lived in
    assets/ but the build only packed src/, so every map naming SDCONC1 would
    have died with "Unknown texture". The build now folds assets/<folder>/<set>/
    into <folder>/ and this test keeps it that way."""

    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.pk3 = cls.root / "dist" / "sovietdoom.pk3"
        if not cls.pk3.exists():
            raise unittest.SkipTest("build the PK3 first: python3 tools/build.py")
        cls.names = set(zipfile.ZipFile(cls.pk3).namelist())

    def test_every_approved_asset_is_packed_flat(self):
        assets = self.root / "assets"
        if not assets.is_dir():
            self.skipTest("no assets/ tree")
        missing = []
        for folder in ("textures", "flats", "sprites"):
            base = assets / folder
            if not base.is_dir():
                continue
            for png in base.rglob("*.png"):
                want = f"{folder}/{png.name}"          # the set folder is dropped
                if want not in self.names:
                    missing.append(f"{png.relative_to(self.root)} -> {want}")
        self.assertEqual([], missing, "approved art missing from the PK3")

    def test_unapproved_art_never_ships(self):
        """work/ holds art the CEO has not judged; it must never reach the PK3."""
        leaked = [n for n in self.names if "work/" in n or "batch1" in n]
        self.assertEqual([], leaked)


class LumpLeftoverTest(unittest.TestCase):
    """PMO-01, 2026-10-13: an agent left MAPINFO.bak, .bak2 and .bak3 in
    src/lumps/ mid-edit. A lump is named after the file's stem, so all three
    became a second lump called MAPINFO and the package stopped validating.
    The build must not see editor leftovers at all."""

    def test_backups_and_dotfiles_never_become_lumps(self):
        from sdbuild.pk3 import collect_lumps
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            lumps = src / "lumps"
            lumps.mkdir(parents=True)
            (lumps / "MAPINFO").write_text("real")
            for junk in ("MAPINFO.bak", "MAPINFO.bak2", "MAPINFO.orig",
                         "MAPINFO~", ".DS_Store", "MAPINFO.swp"):
                (lumps / junk).write_text("junk")
            names = sorted(e.path for e in collect_lumps(src))
            self.assertEqual(["MAPINFO"], names)

    def test_a_real_lump_with_a_dot_in_its_name_still_packs(self):
        """zscript.txt is a real lump and must not be mistaken for a leftover."""
        from sdbuild.pk3 import collect_lumps
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "src"
            (src / "lumps").mkdir(parents=True)
            (src / "lumps" / "zscript.txt").write_text("version \"4.12\"")
            self.assertEqual(["zscript.txt"], [e.path for e in collect_lumps(src)])


class LocalizedAssetsTest(unittest.TestCase):
    """D48's pause plaque has an English and a Russian face. GZDoom finds a
    language variant by its PATH, `localized/textures/<BASE>.<lang>.<ext>`
    (g4.14.2, FTextureManager::AddLocalizedVariants), so unlike
    assets/textures/<set>/ the build must keep that path whole, and the
    variant must be the size of its base or the engine drops it."""

    def _assets(self, root: Path) -> Path:
        import check_pk3
        assets = root / "assets"
        (assets / "graphics" / "shell").mkdir(parents=True)
        (assets / "localized" / "textures").mkdir(parents=True)
        blob = check_pk3.PNG_MAGIC + b"fixture"
        (assets / "graphics" / "shell" / "M_PAUSE.png").write_bytes(blob)
        (assets / "localized" / "textures" / "M_PAUSE.ru.png").write_bytes(blob + b"ru")
        (assets / "localized" / "textures" / "M_PAUSE.ru.png.bak").write_bytes(b"junk")
        return assets

    def test_collect_keeps_the_localized_path(self):
        from sdbuild.pk3 import collect_assets
        with tempfile.TemporaryDirectory() as d:
            paths = sorted(e.path for e in collect_assets(self._assets(Path(d))))
        self.assertIn("localized/textures/M_PAUSE.ru.png", paths)
        self.assertIn("graphics/M_PAUSE.png", paths)          # the set folder still drops
        self.assertNotIn("localized/textures/M_PAUSE.ru.png.bak", paths)
        self.assertNotIn("textures/M_PAUSE.ru.png", paths)    # never flattened

    def test_built_pk3_carries_the_variant_at_its_path(self):
        with tempfile.TemporaryDirectory() as d:
            assets = self._assets(Path(d))
            out = Path(d) / "out" / "sovietdoom.pk3"
            build_pk3(SRC_DIR, out, TOOLS_DIR, assets)
            with zipfile.ZipFile(out) as zf:
                names = zf.namelist()
                self.assertIn("localized/textures/M_PAUSE.ru.png", names)
                self.assertEqual((assets / "localized" / "textures" / "M_PAUSE.ru.png").read_bytes(),
                                 zf.read("localized/textures/M_PAUSE.ru.png"))

    def test_every_real_variant_is_packed_at_its_path(self):
        variants = sorted((PROJECT_ROOT / "assets" / "localized").rglob("*.*")) \
            if (PROJECT_ROOT / "assets" / "localized").is_dir() else []
        if not variants:
            self.skipTest("no assets/localized/ yet")
        pk3 = PROJECT_ROOT / "dist" / "sovietdoom.pk3"
        if not pk3.exists():
            self.skipTest("build the PK3 first: python3 tools/build.py")
        names = set(zipfile.ZipFile(pk3).namelist())
        missing = [p.relative_to(PROJECT_ROOT / "assets").as_posix() for p in variants
                   if p.relative_to(PROJECT_ROOT / "assets").as_posix() not in names]
        self.assertEqual([], missing)

    def test_every_real_variant_matches_its_base_size(self):
        import check_pk3
        assets = PROJECT_ROOT / "assets"
        folder = assets / "localized" / "textures"
        variants = sorted(folder.glob("*.png")) if folder.is_dir() else []
        if not variants:
            self.skipTest("no assets/localized/textures/ yet")
        for variant in variants:
            parts = check_pk3.localized_name_parts(variant.name)
            self.assertNotIsInstance(parts, str, f"{variant.name}: {parts}")
            base_name = parts[0].upper()
            bases = [p for d in check_pk3.LOCALIZED_BASE_DIRS if (assets / d).is_dir()
                     for p in (assets / d).rglob("*.png") if p.stem.upper() == base_name]
            self.assertEqual(1, len(bases), f"{variant.name}: base {base_name} found {bases}")
            got = check_pk3.read_png(variant.read_bytes())
            want = check_pk3.read_png(bases[0].read_bytes())
            self.assertEqual((want.width, want.height), (got.width, got.height),
                             f"{variant.name} must be the size of {bases[0].name}")
