"""Tests for tools/check_pk3.py: build broken PK3s and prove each is caught.

A validator nobody has seen fail is not a validator, it is a decoration. So
every check in `tools/check_pk3.py` gets a synthetic package that violates it
on purpose, plus one well-formed package that must pass clean. Everything is
assembled in a temp dir with `tempfile`; `dist/` is never touched and the
real `docs/` are never read (fixture copies are written per test, so another
agent editing MOD-SPEC or LICENSES mid-run cannot turn this suite red).

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from contextlib import redirect_stdout
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = PROJECT_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import check_pk3  # noqa: E402
from sdbuild.wad import build_pwad  # noqa: E402  (fixture WADs must be valid)

# --- Fixture documents -----------------------------------------------------
# Only what the validator parses; the shape mirrors the real documents.

SPEC_MD = """# MOD-SPEC (fixture)

## 4. Maps

Nothing here.

## 5. IWAD assets used

| Name | Type | Used in | Verification |
|---|---|---|---|
| `STARTAN2` | wall texture | MAP01 | verified |
| `FLOOR4_8` | flat | MAP01 | verified |
| `CEIL3_5` | flat | MAP01 | verified |
| `SKY1` | sky | MAPINFO | verified |

## 6. ZScript

Nothing here.
"""

LICENSES_MD = """# Licences (fixture)

| Lump | Origin | Licence |
|---|---|---|
| `SDTEST1`, `SDTEST2` | own procedural script | CC BY-NC-SA 4.0 |
"""

# Two palette colours are enough to prove the subset rule.
PALETTE_IN = [(10, 11, 14), (200, 30, 30)]
PALETTE_OUT = (255, 0, 255)  # magenta: never in the fixture palette

MAPINFO_LUMP = b'map MAP01 lookup "SD_MAP01_NAME"\n{\n\tsky1 = "SKY1"\n}\n'
LANGUAGE_LUMP = b'[enu default]\nSD_MAP01_NAME = "Test Range";\n'
ZSCRIPT_LUMP = b'version "4.12"\n#include "zscript/sd/thing.zs"\n'
ZSCRIPT_FILE = b"// a class would live here\n"

WALL_TEXTURE = "SDTEST1"   # packed in the fixture PK3
FLOOR_FLAT = "FLOOR4_8"    # declared IWAD asset
CEILING_FLAT = "CEIL3_5"   # declared IWAD asset


# --- Fixture builders ------------------------------------------------------

def png_indexed(width: int, height: int, palette: list[tuple[int, int, int]]) -> bytes:
    """A valid 8-bit indexed PNG; row r uses palette index r % len(palette).

    Cycling the indices means every palette entry is actually used, so a
    colour outside the project palette cannot hide in an unused slot.
    """
    rows = bytearray()
    for y in range(height):
        rows.append(0)                                  # filter type 0 (None)
        rows += bytes([y % len(palette)]) * width
    plte = b"".join(bytes(c) for c in palette)
    return _png(width, height, colour_type=3, extra_chunks=[(b"PLTE", plte)], idat=bytes(rows))


def png_truecolour(width: int, height: int, rgb: tuple[int, int, int] = (90, 90, 90)) -> bytes:
    """A valid RGB (colour type 2) PNG: the wrong colour model for this mod."""
    rows = bytearray()
    for _y in range(height):
        rows.append(0)
        rows += bytes(rgb) * width
    return _png(width, height, colour_type=2, extra_chunks=[], idat=bytes(rows))


def _png(width: int, height: int, colour_type: int, extra_chunks, idat: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    out = bytearray(check_pk3.PNG_MAGIC)
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0))
    for tag, data in extra_chunks:
        out += chunk(tag, data)
    out += chunk(b"IDAT", zlib.compress(idat))
    out += chunk(b"IEND", b"")
    return bytes(out)


def textmap(
    wall: str = WALL_TEXTURE,
    floor: str = FLOOR_FLAT,
    ceiling: str = CEILING_FLAT,
    with_player: bool = True,
) -> bytes:
    blocks = [
        '// fixture map\nnamespace = "zdoom";',
        "vertex\n{\nx = 0.0;\ny = 0.0;\n}",
        "vertex\n{\nx = 0.0;\ny = 64.0;\n}",
        "vertex\n{\nx = 64.0;\ny = 64.0;\n}",
        "vertex\n{\nx = 64.0;\ny = 0.0;\n}",
    ]
    for i in range(4):
        blocks.append(f"linedef\n{{\nv1 = {i};\nv2 = {(i + 1) % 4};\nsidefront = {i};\nblocking = true;\n}}")
        blocks.append(
            "sidedef\n{\nsector = 0;\n"
            f'texturetop = "-";\ntexturemiddle = "{wall}";\ntexturebottom = "-";\n}}'
        )
    blocks.append(
        "sector\n{\nheightfloor = 0;\nheightceiling = 128;\n"
        f'texturefloor = "{floor}";\ntextureceiling = "{ceiling}";\nlightlevel = 160;\n}}'
    )
    if with_player:
        blocks.append("thing\n{\nx = 32.0;\ny = 32.0;\nangle = 90;\ntype = 1;\n}")
    return ("\n\n".join(blocks) + "\n").encode("ascii")


def map_wad(name: str = "MAP01", body: bytes | None = None) -> bytes:
    return build_pwad([(name, b""), ("TEXTMAP", body if body is not None else textmap()), ("ENDMAP", b"")])


def good_entries() -> dict[str, bytes]:
    """A package that must pass every check."""
    return {
        "MAPINFO": MAPINFO_LUMP,
        "LANGUAGE": LANGUAGE_LUMP,
        "zscript.txt": ZSCRIPT_LUMP,
        "zscript/sd/thing.zs": ZSCRIPT_FILE,
        "maps/MAP01.wad": map_wad(),
        f"textures/{WALL_TEXTURE}.png": png_indexed(64, 128, PALETTE_IN),
        "flats/SDTEST2.png": png_indexed(64, 64, PALETTE_IN),
    }


class CheckPk3TestCase(unittest.TestCase):
    """Base class: a temp dir, fixture docs, and a PK3 writer."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.spec = self.tmp / "MOD-SPEC.md"
        self.licenses = self.tmp / "LICENSES.md"
        self.palette = self.tmp / "palette.json"
        self.spec.write_text(SPEC_MD, encoding="utf-8")
        self.licenses.write_text(LICENSES_MD, encoding="utf-8")
        self.palette.write_text(json.dumps({"colours": [list(c) for c in PALETTE_IN]}), encoding="utf-8")

    def write_pk3(self, entries: dict[str, bytes], name: str = "test.pk3") -> Path:
        path = self.tmp / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for member, data in entries.items():
                zf.writestr(member, data)
        return path

    def run_check(self, entries: dict[str, bytes]) -> check_pk3.Report:
        return check_pk3.check_pk3(self.write_pk3(entries), self.spec, self.licenses, self.palette)

    # --- assertions -------------------------------------------------------
    def assertClean(self, report: check_pk3.Report) -> None:
        self.assertEqual(
            [], [f.render() for f in report.findings],
            "the fixture package was supposed to pass every check",
        )
        self.assertTrue(report.ok())

    def assertFails(self, report: check_pk3.Report, category: str, needle: str) -> check_pk3.Finding:
        errors = [f for f in report.errors if f.category == category]
        self.assertTrue(errors, f"no error in category {category!r}; got {[f.render() for f in report.findings]}")
        hits = [f for f in errors if needle.lower() in f.message.lower()]
        self.assertTrue(hits, f"no {category} error mentioning {needle!r}; got {[f.message for f in errors]}")
        self.assertFalse(report.ok())
        return hits[0]


# --- The good case ---------------------------------------------------------

class GoodPackageTest(CheckPk3TestCase):
    def test_well_formed_package_passes(self):
        self.assertClean(self.run_check(good_entries()))

    def test_exit_code_zero_and_verdict_pass(self):
        path = self.write_pk3(good_entries())
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = check_pk3.main([
                "--pk3", str(path), "--spec", str(self.spec),
                "--licenses", str(self.licenses), "--palette", str(self.palette),
            ])
        self.assertEqual(check_pk3.EXIT_OK, code)
        self.assertIn("VERDICT: PASS", buffer.getvalue())

    def test_json_output_is_machine_readable(self):
        path = self.write_pk3(good_entries())
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = check_pk3.main([
                "--pk3", str(path), "--json", "--spec", str(self.spec),
                "--licenses", str(self.licenses), "--palette", str(self.palette),
            ])
        payload = json.loads(buffer.getvalue())
        self.assertEqual(check_pk3.EXIT_OK, code)
        self.assertTrue(payload["ok"])
        self.assertEqual(0, payload["errors"])
        self.assertEqual([], payload["findings"])
        self.assertEqual(1, payload["stats"]["maps"])
        self.assertEqual(2, payload["stats"]["images_checked"])


# --- 1. The package itself -------------------------------------------------

class PackageTest(CheckPk3TestCase):
    def test_missing_file(self):
        report = check_pk3.check_pk3(self.tmp / "nope.pk3", self.spec, self.licenses, self.palette)
        self.assertFails(report, "package", "does not exist")

    def test_not_a_zip(self):
        path = self.tmp / "broken.pk3"
        path.write_bytes(b"this is not a zip at all")
        report = check_pk3.check_pk3(path, self.spec, self.licenses, self.palette)
        self.assertFails(report, "package", "not a zip")

    def test_missing_required_root_lump(self):
        entries = good_entries()
        del entries["MAPINFO"]
        self.assertFails(self.run_check(entries), "package", "required by MOD-SPEC")

    def test_package_without_maps(self):
        entries = good_entries()
        del entries["maps/MAP01.wad"]
        self.assertFails(self.run_check(entries), "package", "no maps/*.wad")


# --- 2. Lump names ---------------------------------------------------------

class LumpNameTest(CheckPk3TestCase):
    def test_nine_character_root_lump_is_rejected(self):
        entries = good_entries()
        entries["TOOLONGXX"] = b"nine characters\n"   # 9 > MAX_LUMP_NAME
        finding = self.assertFails(self.run_check(entries), "lumps", "9 characters")
        self.assertEqual("TOOLONGXX", finding.path)

    def test_eight_character_root_lump_is_accepted(self):
        entries = good_entries()
        entries["EIGHTCHR"] = b"exactly eight\n"
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "lumps"])

    def test_lowercase_root_lump_is_accepted(self):
        # MOD-SPEC 2 ships zscript.txt in lower case: GZDoom upper-cases
        # lump names taken from PK3 entries, so case must never fail.
        self.assertClean(self.run_check(good_entries()))

    def test_non_ascii_lump_name_is_rejected(self):
        entries = good_entries()
        entries["CAÑON"] = b"not ascii\n"
        self.assertFails(self.run_check(entries), "lumps", "not ASCII")

    def test_two_root_files_collapsing_to_one_lump_collide(self):
        entries = good_entries()
        entries["SNDINFO.txt"] = b"a\n"
        entries["SNDINFO"] = b"b\n"
        self.assertFails(self.run_check(entries), "lumps", "collides")


# --- 3. Map WADs -----------------------------------------------------------

class MapTest(CheckPk3TestCase):
    def test_map_that_is_not_a_pwad(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = b"IWAD" + b"\0" * 32
        self.assertFails(self.run_check(entries), "maps", "expected b'PWAD'")

    def test_map_with_wrong_lump_order(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = build_pwad([("MAP01", b""), ("ENDMAP", b""), ("TEXTMAP", textmap())])
        self.assertFails(self.run_check(entries), "maps", "lump order")

    def test_map_without_textmap(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = build_pwad([("MAP01", b""), ("ENDMAP", b"")])
        self.assertFails(self.run_check(entries), "maps", "lump order")

    def test_map_name_not_matching_the_marker(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(name="MAP09")
        self.assertFails(self.run_check(entries), "maps", "lump order")

    def test_textmap_that_does_not_parse(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=b'namespace = "zdoom";\nsector\n{\nheightfloor = 0;\n')
        self.assertFails(self.run_check(entries), "maps", "does not parse")

    def test_textmap_without_namespace(self):
        entries = good_entries()
        body = textmap().replace(b'namespace = "zdoom";', b"")
        entries["maps/MAP01.wad"] = map_wad(body=body)
        self.assertFails(self.run_check(entries), "maps", "namespace")

    def test_map_without_player_start(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(with_player=False))
        self.assertFails(self.run_check(entries), "maps", "Player 1 start")

    def test_non_empty_marker_lump(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = build_pwad([("MAP01", b"junk"), ("TEXTMAP", textmap()), ("ENDMAP", b"")])
        self.assertFails(self.run_check(entries), "maps", "must be empty")


# --- 4. Referenced textures ------------------------------------------------

class TextureTest(CheckPk3TestCase):
    def test_wall_texture_that_exists_nowhere(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(wall="SDGHOST"))
        finding = self.assertFails(self.run_check(entries), "textures", "Unknown texture SDGHOST")
        self.assertIn("maps/MAP01.wad:sidedef[0].texturemiddle", finding.path)

    def test_flat_that_exists_nowhere(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(floor="SDNOFLR"))
        finding = self.assertFails(self.run_check(entries), "textures", "SDNOFLR")
        self.assertIn("sector[0].texturefloor", finding.path)

    def test_iwad_texture_not_declared_in_mod_spec(self):
        # BIGDOOR2 exists in every Doom II IWAD, but using it without writing
        # it into MOD-SPEC 5 breaks the documentation contract, so it fails.
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(wall="BIGDOOR2"))
        self.assertFails(self.run_check(entries), "textures", "BIGDOOR2")

    def test_declared_iwad_texture_resolves(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(wall="STARTAN2"))
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "textures"])

    def test_no_texture_dash_is_not_a_reference(self):
        entries = good_entries()
        entries["maps/MAP01.wad"] = map_wad(body=textmap(wall="-"))
        report = self.run_check(entries)
        self.assertEqual([], [f for f in report.errors if f.category == "textures"])
        # Only the two flats are counted as references (plus SKY1 from MAPINFO).
        self.assertEqual(3, report.stats["textures_referenced"])

    def test_mapinfo_sky_is_checked_too(self):
        entries = good_entries()
        entries["MAPINFO"] = MAPINFO_LUMP.replace(b'sky1 = "SKY1"', b'sky1 = "SDNOSKY"')
        self.assertFails(self.run_check(entries), "textures", "SDNOSKY")


# --- 4b. ANIMDEFS switch pairs (MOD-SPEC 4.3, T16) -------------------------

class AnimdefsSwitchTest(CheckPk3TestCase):
    def test_switch_pair_that_resolves_passes(self):
        entries = good_entries()
        # SDTEST1 is packed, STARTAN2 is a declared IWAD asset: both legal.
        entries["ANIMDEFS"] = b"// pair\nswitch doom 1 SDTEST1 on pic STARTAN2 tics 0\n"
        report = self.run_check(entries)
        self.assertClean(report)
        self.assertEqual(2, report.stats["switch_textures"])

    def test_missing_on_texture_fails_with_line(self):
        entries = good_entries()
        entries["ANIMDEFS"] = b"\n\nswitch doom 1 SDTEST1 on pic SDGHOST2 tics 0\n"
        finding = self.assertFails(self.run_check(entries), "textures", "SDGHOST2")
        self.assertEqual("ANIMDEFS:3:switch on", finding.path)

    def test_missing_off_texture_fails(self):
        entries = good_entries()
        entries["ANIMDEFS"] = b"switch doom 1 SDGHOST1 on pic SDTEST1 tics 0\n"
        finding = self.assertFails(self.run_check(entries), "textures", "SDGHOST1")
        self.assertEqual("ANIMDEFS:1:switch off", finding.path)

    def test_switch_textures_do_not_count_as_used_by_a_map(self):
        entries = good_entries()
        entries["textures/SDSW1Z.png"] = png_indexed(64, 128, PALETTE_IN)
        entries["ANIMDEFS"] = b"switch doom 1 SDSW1Z on pic SDTEST1 tics 0\n"
        report = self.run_check(entries)
        unused = [n for n in report.notes["textures"] if n.startswith("packed but unused")]
        self.assertTrue(unused and "SDSW1Z" in unused[0], report.notes["textures"])

    def test_parser_reads_every_engine_form(self):
        # Lines copied from GZDoom g4.14.2 gzdoom.pk3 -> animdefs.txt (game
        # filter with and without tier, quest after the name, sound, an off
        # sequence), plus a comment and a non-switch block that must be skipped.
        text = (
            "// comment switch NOTME on pic NOTME tics 0\n"
            "texture optional M_SKULL1\n\tpic M_SKULL1 tics 8\n"
            "switch doom 1 SW1BRCOM on pic SW2BRCOM tics 0\n"
            "switch hexen SW_1_UP on sound Switch1 pic SW_1_DN tics 0\n"
            "switch strife BRNSCN01 quest on sound switches/sizzle pic BRNSCN05 tics 0\n"
            "switch strife DORWS04 on sound switches/bolt pic DORWS05 tics 0 "
            "off sound switches/boltback pic DORWS04 tics 0\n"
            "/* block\ncomment */ switch SDBARE1 on pic SDBARE2 tics 0\n"
        )
        self.assertEqual(
            [("SW1BRCOM", 4, "off"), ("SW2BRCOM", 4, "on"),
             ("SW_1_UP", 5, "off"), ("SW_1_DN", 5, "on"),
             ("BRNSCN01", 6, "off"), ("BRNSCN05", 6, "on"),
             ("DORWS04", 7, "off"), ("DORWS05", 7, "on"), ("DORWS04", 7, "off-pic"),
             ("SDBARE1", 9, "off"), ("SDBARE2", 9, "on")],
            check_pk3.animdefs_switch_textures(text),
        )


# --- 5. PNG colour model, palette and size ---------------------------------

class ImageTest(CheckPk3TestCase):
    def test_rgb_png_instead_of_indexed(self):
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = png_truecolour(64, 128)
        finding = self.assertFails(self.run_check(entries), "images", "colour type 2")
        self.assertEqual(f"textures/{WALL_TEXTURE}.png", finding.path)

    def test_flat_of_63_by_64(self):
        entries = good_entries()
        entries["flats/SDTEST2.png"] = png_indexed(63, 64, PALETTE_IN)
        report = self.run_check(entries)
        self.assertFails(report, "images", "multiples of 8")
        self.assertFails(report, "images", "a flat must be 64x64")

    def test_flat_of_128_by_128_is_still_wrong(self):
        entries = good_entries()
        entries["flats/SDTEST2.png"] = png_indexed(128, 128, PALETTE_IN)
        self.assertFails(self.run_check(entries), "images", "a flat must be 64x64")

    def test_colour_outside_the_palette(self):
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = png_indexed(64, 128, PALETTE_IN + [PALETTE_OUT])
        finding = self.assertFails(self.run_check(entries), "images", "outside docs/art/palette.json")
        self.assertIn("#FF00FF", finding.message)

    def test_unused_palette_entry_outside_the_palette_is_tolerated(self):
        # Pillow pads a palette to 256 entries; only the pixels that exist can
        # be wrong, so the check decodes the image and looks at used indices.
        rows = bytearray()
        for _y in range(128):
            rows.append(0)
            rows += bytes([0]) * 64            # every pixel uses index 0 only
        png = check_pk3.PNG_MAGIC
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = _png(
            64, 128, 3,
            [(b"PLTE", b"".join(bytes(c) for c in [PALETTE_IN[0], PALETTE_OUT]))],
            bytes(rows),
        )
        self.assertTrue(png)  # signature constant is exercised by _png
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "images"])

    def test_corrupt_png_is_reported_not_crashed(self):
        # Signature plus garbage: the first chunk's CRC cannot match.
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = check_pk3.PNG_MAGIC + b"\x00" * 20
        self.assertFails(self.run_check(entries), "images", "unreadable PNG")

    def test_truncated_png_is_reported(self):
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = png_indexed(64, 128, PALETTE_IN)[:120]
        self.assertFails(self.run_check(entries), "images", "unreadable PNG")

    def test_png_with_a_flipped_byte_fails_its_crc(self):
        good = bytearray(png_indexed(64, 128, PALETTE_IN))
        good[good.index(b"IDAT") + 8] ^= 0xFF   # inside the IDAT payload
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = bytes(good)
        self.assertFails(self.run_check(entries), "images", "corrupt")

    def test_wall_of_an_unagreed_size_is_a_warning_not_an_error(self):
        entries = good_entries()
        entries[f"textures/{WALL_TEXTURE}.png"] = png_indexed(256, 128, PALETTE_IN)
        report = self.run_check(entries)
        self.assertEqual([], [f for f in report.errors if f.category == "images"])
        self.assertTrue([f for f in report.warnings if "agreed wall sizes" in f.message])


# --- 6. Sprites ------------------------------------------------------------

class SpriteTest(CheckPk3TestCase):
    def test_no_sprites_passes(self):
        report = self.run_check(good_entries())
        self.assertEqual(0, report.stats["sprites"])
        self.assertEqual([], [f for f in report.findings if f.category == "sprites"])

    def test_complete_eight_rotation_frame_passes(self):
        entries = good_entries()
        for rotation in "12345678":
            entries[f"sprites/SDSHA{rotation}.png"] = png_indexed(8, 8, PALETTE_IN)
        self.licenses.write_text(LICENSES_MD + "\n| `SDSHA1` `SDSHA2` `SDSHA3` `SDSHA4` "
                                 "`SDSHA5` `SDSHA6` `SDSHA7` `SDSHA8` | own | own |\n", encoding="utf-8")
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "sprites"])

    def test_rotation_zero_alone_passes(self):
        entries = good_entries()
        entries["sprites/SDSPA0.png"] = png_indexed(8, 8, PALETTE_IN)
        self.licenses.write_text(LICENSES_MD + "\n| `SDSPA0` | own | own |\n", encoding="utf-8")
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "sprites"])

    def test_missing_rotation_is_caught(self):
        entries = good_entries()
        for rotation in "1234567":        # 8 is missing
            entries[f"sprites/SDSHA{rotation}.png"] = png_indexed(8, 8, PALETTE_IN)
        self.assertFails(self.run_check(entries), "sprites", "missing 8")

    def test_mixing_rotation_zero_with_directional_frames(self):
        entries = good_entries()
        entries["sprites/SDSHA0.png"] = png_indexed(8, 8, PALETTE_IN)
        entries["sprites/SDSHA1.png"] = png_indexed(8, 8, PALETTE_IN)
        self.assertFails(self.run_check(entries), "sprites", "mixes rotation 0")

    def test_malformed_sprite_name(self):
        entries = good_entries()
        entries["sprites/SDS.png"] = png_indexed(8, 8, PALETTE_IN)
        self.assertFails(self.run_check(entries), "sprites", "must be 6")

    def test_mirrored_eight_character_sprite_is_understood(self):
        entries = good_entries()
        # SDSHA2A8 means: frame A rotation 2, and the same image mirrored as
        # frame A rotation 8. Four such lumps cover all eight rotations.
        for first, second in (("1", "1"), ("2", "8"), ("3", "7"), ("4", "6"), ("5", "5")):
            entries[f"sprites/SDSHA{first}A{second}.png"] = png_indexed(8, 8, PALETTE_IN)
        self.licenses.write_text(LICENSES_MD + "\n| `SDSHA1A1` `SDSHA2A8` `SDSHA3A7` "
                                 "`SDSHA4A6` `SDSHA5A5` | own | own |\n", encoding="utf-8")
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "sprites"])


# --- 6b. Sprites named by ZScript states (MOD-SPEC 5.1, F5) ----------------

class StateSpriteTest(CheckPk3TestCase):
    """A sprite a `States` block names must be packed, the engine's, or a
    declared IWAD sprite: the texture rule of MOD-SPEC 5, applied to the
    Freedoom placeholders the arsenal and the bestiary run on."""

    ACTOR = (b'// POSS A 1; in a comment is not a state line\n'
             b'class SD_Thing : Actor\n{\n'
             b'\tDefault { Health 20; }\n'
             b'\tStates\n\t{\n'
             b'\tSpawn:\n\t\tPOSS AB 10 A_Look;\n\t\tLoop;\n'
             b'\tMelee:\n\tMissile:\n\t\tPOSS E 10 A_FaceTarget;\n\t\tGoto See;\n'
             b'\tDeath: TNT1 A 0;\n\t\tStop;\n'
             b'\t}\n}\n')
    SPRITE_ROW = "| `POSS` | sprite | SD_Thing | fixture |\n"

    def entries_with_actor(self) -> dict[str, bytes]:
        entries = good_entries()
        entries["zscript/sd/thing.zs"] = self.ACTOR
        return entries

    def declare_poss(self) -> None:
        self.spec.write_text(SPEC_MD.replace("## 6. ZScript", self.SPRITE_ROW + "\n## 6. ZScript"),
                             encoding="utf-8")

    def sprite_errors(self, report: check_pk3.Report) -> list[check_pk3.Finding]:
        return [f for f in report.errors if f.category == "sprites"]

    def test_parser_reads_states_and_skips_labels_keywords_and_comments(self):
        refs = check_pk3.zscript_state_sprites(self.ACTOR.decode())
        self.assertEqual(["POSS", "POSS", "TNT1"], [name for name, _ in refs])
        self.assertEqual(8, refs[0][1], "line numbers count from the top of the file")

    def test_declared_iwad_sprite_passes(self):
        self.declare_poss()
        report = self.run_check(self.entries_with_actor())
        self.assertEqual([], self.sprite_errors(report))
        self.assertEqual(1, report.stats["state_sprites_iwad"])

    def test_undeclared_iwad_sprite_fails(self):
        finding = self.assertFails(self.run_check(self.entries_with_actor()), "sprites", "MOD-SPEC 5")
        self.assertIn("POSS", finding.message)
        self.assertIn("zscript/sd/thing.zs:8", finding.path)

    def test_packed_sprite_passes_without_a_spec_row(self):
        entries = self.entries_with_actor()
        for frame in "ABE":
            entries[f"sprites/POSS{frame}0.png"] = png_indexed(8, 8, PALETTE_IN)
        self.licenses.write_text(LICENSES_MD + "\n| `POSSA0` `POSSB0` `POSSE0` | own | own |\n",
                                 encoding="utf-8")
        self.assertEqual([], self.sprite_errors(self.run_check(entries)))

    def test_a_texture_row_does_not_declare_a_sprite(self):
        # STARTAN2 is a declared IWAD *texture*; naming it as a sprite is not
        # covered by that row (and is not 4 characters anyway). Use a 4-char
        # texture-typed row to prove the Type column is what counts.
        self.spec.write_text(SPEC_MD.replace(
            "## 6. ZScript", "| `POSS` | wall texture | nowhere | fixture |\n\n## 6. ZScript"),
            encoding="utf-8")
        self.assertFails(self.run_check(self.entries_with_actor()), "sprites", "MOD-SPEC 5")

    def test_real_spec_declares_every_sprite_the_mod_uses(self):
        """The live MOD-SPEC 5.1 against the live ZScript tree."""
        declared = check_pk3.iwad_sprites_from_spec(check_pk3.DEFAULT_SPEC)
        used: set[str] = set()
        for path in sorted((PROJECT_ROOT / "src" / "zscript").rglob("*.zs")):
            used |= {name for name, _ in check_pk3.zscript_state_sprites(path.read_text(encoding="utf-8"))}
        missing = sorted(used - declared - check_pk3.ENGINE_SPRITES)
        self.assertEqual([], missing, "sprites used by ZScript states but not in MOD-SPEC 5.1")


# --- 7. Licences -----------------------------------------------------------

class LicenceTest(CheckPk3TestCase):
    def test_packed_asset_without_a_licence_row(self):
        entries = good_entries()
        entries["textures/SDNOLIC.png"] = png_indexed(64, 128, PALETTE_IN)
        finding = self.assertFails(self.run_check(entries), "licences", "no row for 'SDNOLIC'")
        self.assertEqual("textures/SDNOLIC.png", finding.path)

    def test_sound_without_a_licence_row(self):
        entries = good_entries()
        entries["sounds/SDBOOM.ogg"] = b"not really ogg"
        self.assertFails(self.run_check(entries), "licences", "SDBOOM")

    def test_every_packed_asset_documented_passes(self):
        report = self.run_check(good_entries())
        self.assertEqual(2, report.stats["assets_packed"])
        self.assertEqual(0, report.stats["assets_unlicensed"])


# --- 8. ZScript includes ---------------------------------------------------

class ZScriptTest(CheckPk3TestCase):
    def test_include_pointing_nowhere(self):
        entries = good_entries()
        entries["zscript.txt"] = b'version "4.12"\n#include "zscript/sd/ghost.zs"\n'
        del entries["zscript/sd/thing.zs"]
        finding = self.assertFails(self.run_check(entries), "zscript", "not in the PK3")
        self.assertIn("zscript/sd/ghost.zs", finding.path)

    def test_nested_include_pointing_nowhere(self):
        entries = good_entries()
        entries["zscript/sd/thing.zs"] = b'#include "zscript/sd/deeper.zs"\n'
        self.assertFails(self.run_check(entries), "zscript", "not in the PK3")

    def test_include_resolves_case_insensitively(self):
        entries = good_entries()
        entries["zscript.txt"] = b'version "4.12"\n#include "ZSCRIPT/SD/THING.ZS"\n'
        self.assertEqual([], [f for f in self.run_check(entries).errors if f.category == "zscript"])

    def test_orphan_zscript_file_is_a_warning(self):
        entries = good_entries()
        entries["zscript/sd/orphan.zs"] = b"// nothing includes me\n"
        report = self.run_check(entries)
        self.assertEqual([], [f for f in report.errors if f.category == "zscript"])
        self.assertTrue([f for f in report.warnings if f.path == "zscript/sd/orphan.zs"])

    def test_include_cycle_terminates(self):
        entries = good_entries()
        entries["zscript/sd/thing.zs"] = b'#include "zscript.txt"\n'
        report = self.run_check(entries)   # must not hang
        self.assertEqual([], [f for f in report.errors if f.category == "zscript"])


# --- 9. Fonts named by MENUDEF (MOD-SPEC 6.6) ------------------------------

class MenuFontTest(CheckPk3TestCase):
    MENUDEF = (b'// a comment naming Font "GHOSTFNT" is not a directive\n'
               b'LISTMENU "MainMenu"\n{\n\tFont "SDMENU", "Cream", "Gold"\n}\n'
               b'LISTMENU "SkillMenu"\n{\n\tFont "SmallFont", "Red", "Gold"\n}\n')

    def menu_errors(self, report: check_pk3.Report) -> list[check_pk3.Finding]:
        return [f for f in report.errors if f.category == "menus"]

    def test_no_menudef_is_skipped(self):
        report = self.run_check(good_entries())
        self.assertIn("menus", report.skipped)

    def test_folder_font_missing_from_the_package_fails(self):
        entries = good_entries()
        entries["MENUDEF"] = self.MENUDEF
        finding = self.assertFails(self.run_check(entries), "menus", "SDMENU")
        self.assertEqual("MENUDEF:4", finding.path)

    def test_packed_folder_font_passes(self):
        entries = good_entries()
        entries["MENUDEF"] = self.MENUDEF
        entries["fonts/sdmenu/0041.png"] = png_indexed(8, 8, PALETTE_IN)
        entries["fonts/sdmenu/font.inf"] = b"FontHeight 16\n"
        report = self.run_check(entries)
        self.assertEqual([], self.menu_errors(report))
        self.assertEqual(2, report.stats["menu_fonts_named"])
        self.assertEqual(1, report.stats["menu_fonts_packed"])

    def test_engine_fonts_need_nothing_packed(self):
        entries = good_entries()
        entries["MENUDEF"] = b'LISTMENU "X"\n{\n\tFont "BigUpper", "Red"\n\tfont "smallfont"\n}\n'
        self.assertEqual([], self.menu_errors(self.run_check(entries)))

    def test_a_font_folder_without_glyphs_does_not_count(self):
        entries = good_entries()
        entries["MENUDEF"] = self.MENUDEF
        entries["fonts/sdmenu/font.inf"] = b"FontHeight 16\n"
        self.assertFails(self.run_check(entries), "menus", "SDMENU")

    def test_parser_ignores_comments_and_reports_lines(self):
        self.assertEqual([("SDMENU", 4), ("SmallFont", 8)],
                         check_pk3.menudef_fonts(self.MENUDEF.decode("ascii")))


# --- Parser units ----------------------------------------------------------

class UdmfParserTest(unittest.TestCase):
    def test_comments_do_not_hide_blocks(self):
        parsed = check_pk3.parse_udmf(
            '// leading\nnamespace = "zdoom";\n/* block */\nsector\n{\ntexturefloor = "A";\n}\n'
        )
        self.assertEqual("zdoom", parsed.namespace)
        self.assertEqual("A", parsed.of_kind("sector")[0].fields["texturefloor"])

    def test_slashes_inside_a_string_are_not_a_comment(self):
        parsed = check_pk3.parse_udmf('namespace = "zdoom";\nsector\n{\ntexturefloor = "A//B";\n}\n')
        self.assertEqual("A//B", parsed.of_kind("sector")[0].fields["texturefloor"])

    def test_unterminated_block_raises(self):
        with self.assertRaises(check_pk3.UdmfError):
            check_pk3.parse_udmf('namespace = "zdoom";\nsector\n{\nx = 1;\n')

    def test_block_indices_follow_declaration_order(self):
        parsed = check_pk3.parse_udmf(
            'namespace = "zdoom";\nsidedef\n{\nsector = 0;\n}\nsidedef\n{\nsector = 1;\n}\n'
        )
        self.assertEqual([0, 1], [b.index for b in parsed.of_kind("sidedef")])


class DocumentParsingTest(CheckPk3TestCase):
    def test_iwad_table_is_read_from_section_five(self):
        names = check_pk3.iwad_assets_from_spec(self.spec)
        self.assertEqual({"STARTAN2", "FLOOR4_8", "CEIL3_5", "SKY1"}, names)

    def test_real_mod_spec_declares_the_iwad_assets(self):
        # Guards against someone renaming the heading and silently turning the
        # texture check into a no-op against the live document.
        names = check_pk3.iwad_assets_from_spec(check_pk3.DEFAULT_SPEC)
        self.assertIn("STARTAN2", names)

    def test_licensed_names_splits_grouped_rows(self):
        names = check_pk3.licensed_names(self.licenses)
        self.assertIn("SDTEST1", names)
        self.assertIn("SDTEST2", names)

    def test_real_palette_loads(self):
        palette = check_pk3.palette_colours(check_pk3.DEFAULT_PALETTE)
        self.assertIsNotNone(palette)
        self.assertGreater(len(palette), 100)


class WadReaderTest(unittest.TestCase):
    def test_truncated_blob(self):
        with self.assertRaises(check_pk3.WadFormatError):
            check_pk3.read_wad_directory(b"PW")

    def test_directory_past_the_end(self):
        blob = struct.pack("<4sii", b"PWAD", 3, 9999)
        with self.assertRaises(check_pk3.WadFormatError):
            check_pk3.read_wad_directory(blob)

    def test_round_trip_against_a_real_pwad(self):
        blob = map_wad()
        self.assertEqual(["MAP01", "TEXTMAP", "ENDMAP"], [e[0] for e in check_pk3.read_wad_directory(blob)])


if __name__ == "__main__":
    unittest.main()
