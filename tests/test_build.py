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

        things = _udmf_blocks(text, "thing")
        self.assertEqual(len(things), 1)
        player = things[0]
        self.assertRegex(player, r"type\s*=\s*1;")
        for flag in ("skill1", "skill2", "skill3", "skill4", "skill5", "single", "coop", "dm"):
            self.assertRegex(player, rf"{flag}\s*=\s*true;", f"{flag} not set on player start")
        self.assertRegex(player, r"x\s*=\s*256\.0;")
        self.assertRegex(player, r"y\s*=\s*256\.0;")

        self.assertEqual(len(_udmf_blocks(text, "sector")), 1)
        self.assertEqual(len(_udmf_blocks(text, "vertex")), 4)
        linedefs = _udmf_blocks(text, "linedef")
        self.assertEqual(len(linedefs), 4)
        for ld in linedefs:
            self.assertRegex(ld, r"blocking\s*=\s*true;")
            self.assertRegex(ld, r"sidefront\s*=\s*\d+;")
            self.assertNotIn("sideback", ld)
        sidedefs = _udmf_blocks(text, "sidedef")
        self.assertEqual(len(sidedefs), 4)
        sector = _udmf_blocks(text, "sector")[0]
        self.assertRegex(sector, r"heightfloor\s*=\s*0;")
        self.assertRegex(sector, r"heightceiling\s*=\s*128;")
        self.assertRegex(sector, r"lightlevel\s*=\s*160;")

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
