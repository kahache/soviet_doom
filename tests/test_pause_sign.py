"""T24: the pause sign follows the language (SD_StatusBar, ADR 010).

Contract: docs/engine/MOD-SPEC.md 6.5.1; reasons:
docs/engine/adr/010-pause-sign-per-language.md. What is pinned here, without
ever starting GZDoom (D26):

  * zscript.txt includes status_bar.zs once; the file declares
    SD_StatusBar : DoomStatusBar with no field and exactly one override,
    DrawPaused, which falls back to the engine (return false) and draws at
    D_Display's y = 4 with DTA_CleanNoMove;
  * MAPINFO's GameInfo registers it with StatusBarClass, once;
  * every engine name the file uses exists in the installed gzdoom.pk3, the
    class it derives from is the one Doom's GameInfo names, the virtual has
    the signature the override assumes, and nothing Freedoom or GZDoom loads
    for Freedoom sets another status bar (skipped where GZDoom or the IWAD
    is absent, as in CI);
  * LANGUAGE's SD_PAUSE_SIGN names M_PAUSE in English and, in Russian, the
    exact path the build packs the variant at;
  * the variant is P2's Russian plaque byte for byte and the size of M_PAUSE;
  * tools/release.py credits localized/ through the base's licence row.

What it cannot pin is what the engine draws: ADR 010's checks E1-E3.

Run:  python3 -m unittest tests.test_pause_sign -v
"""

from __future__ import annotations

import re
import struct
import sys
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
ASSETS = PROJECT_ROOT / "assets"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS))

import release  # noqa: E402
import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from sdbuild.pk3 import collect_assets  # noqa: E402
from test_bestiary import IWAD  # noqa: E402
from test_language import parse_language  # noqa: E402

STATUS_BAR_ZS = SRC / "zscript" / "sd" / "status_bar.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
MAPINFO = SRC / "lumps" / "MAPINFO"
LANGUAGE = SRC / "lumps" / "LANGUAGE"
LICENSES = PROJECT_ROOT / "docs" / "art" / "LICENSES.md"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
ADR = PROJECT_ROOT / "docs" / "engine" / "adr" / "010-pause-sign-per-language.md"

INCLUDE = "zscript/sd/status_bar.zs"
CLASS = "SD_StatusBar"
PARENT = "DoomStatusBar"            # gzdoom.pk3:mapinfo/doomcommon.txt
VIRTUAL = "DrawPaused"
STRING_ID = "SD_PAUSE_SIGN"
ENGLISH_SIGN = "M_PAUSE"
VARIANT_ASSET = ASSETS / "localized" / "textures" / "M_PAUSE.ru.png"
VARIANT_PATH = "localized/textures/M_PAUSE.ru.png"   # its path in the PK3
BASE_ASSET = ASSETS / "graphics" / "shell" / "M_PAUSE.png"
P2_RUSSIAN = PROJECT_ROOT / "work" / "art" / "shell_extra" / "pause_P2_ru.png"
SIGN_TOP = 4                        # D_Display: DrawTexture(..., x, 4, DTA_CleanNoMove)

# Names the file declares itself (class, constants, locals, the parameter).
# Everything else it names must exist in gzdoom.pk3's ZScript.
OWN_NAMES = frozenset(n.lower() for n in (
    CLASS, "SD_PAUSE_SIGN_ID", "SD_PAUSE_SIGN_TOP", "SD_PAUSED_BY_GAP", "SD_PAUSED_BY_ID",
    "player", "pauseSign", "size", "offset", "x", "fnt", "pausedBy",
))

# Engine names that must be DECLARED, not merely mentioned, in gzdoom.pk3:
# name -> a regex over the whole ZScript corpus (case-insensitive, as ZScript).
DECLARATIONS = {
    "DoomStatusBar": r"^class\s+DoomStatusBar\s*:\s*BaseStatusBar\b",
    "DrawPaused": r"^\s*virtual\s+bool\s+DrawPaused\s*\(\s*int\s+\w+\s*\)",
    "CheckForTexture": r"native\s+static\s+TextureID\s+CheckForTexture\s*\(\s*String\s+\w+\s*,\s*int\s+\w+\s*=\s*Type_Any\s*,\s*int\s+\w+\s*=\s*TryAny\s*\)",
    "Type_MiscPatch": r"^\s*Type_MiscPatch\s*,",
    "GetScaledSize": r"native\s+static\s+Vector2\s+GetScaledSize\s*\(\s*TextureID",
    "GetScaledOffset": r"native\s+static\s+Vector2\s+GetScaledOffset\s*\(\s*TextureID",
    "IsValid": r"native\s+bool\s+IsValid\s*\(\s*\)",
    "Localize": r"native\s+static\s+String\s+Localize\s*\(\s*String",
    "GetWidth": r"native\s+static\s+int\s+GetWidth\s*\(\s*\)",
    "DrawTexture": r"native\s+static\s+vararg\s+void\s+DrawTexture\s*\(\s*TextureID\s+\w+\s*,\s*bool\s+\w+\s*,\s*double\s+\w+\s*,\s*double",
    "DrawText": r"native\s+static\s+vararg\s+void\s+DrawText\s*\(\s*Font\s+\w+\s*,\s*int\s+\w+\s*,\s*double\s+\w+\s*,\s*double\s+\w+\s*,\s*String",
    "DTA_CleanNoMove": r"^\s*DTA_CleanNoMove\s*,",
    "CleanXfac": r"native\s+readonly\s+int\s+CleanXfac\s*;",
    "CleanYfac": r"native\s+readonly\s+int\s+CleanYfac\s*;",
    "multiplayer": r"native\s+readonly\s+bool\s+multiplayer\s*;",
    "generic_ui": r"native\s+readonly\s+bool\s+generic_ui\s*;",
    "NewSmallFont": r"native\s+readonly\s+Font\s+NewSmallFont\s*;",
    "SmallFont": r"native\s+readonly\s+Font\s+SmallFont\s*;",
    "CR_RED": r"^\s*CR_RED\s*,",
    "StringWidth": r"native\s+int\s+StringWidth\s*\(\s*String\s+\w+\s*,\s*bool\s+\w+\s*=\s*true\s*\)",
    "Substitute": r"native\s+void\s+Substitute\s*\(\s*String\s+\w+\s*,\s*String",
    "GetUserName": r"native\s+clearscope\s+String\s+GetUserName\s*\(",
    "players": r"native\s+play\s+@PlayerInfo\s+players\s*\[",
}

ZS_KEYWORDS = frozenset({
    "class", "const", "override", "if", "return", "true", "false", "bool", "int",
    "double", "string", "vector2", "textureid", "font",
    "y",            # a Vector2's component (`size.y`); `x` is also our local
})


def strip_comments_and_strings(text: str) -> str:
    """ZScript source without comments and string literals."""
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text[i] == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            out.append('""')
            i = j + 1
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def status_bar_code() -> str:
    return strip_comments_and_strings(STATUS_BAR_ZS.read_text(encoding="utf-8"))


def gzdoom_pk3() -> Path | None:
    return next((c.parent / "gzdoom.pk3" for c in smoke.gzdoom_candidates()
                 if (c.parent / "gzdoom.pk3").is_file()), None)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", path
    return struct.unpack(">II", data[16:24])


def gameinfo_block(text: str) -> str:
    match = re.search(r"(?im)^\s*GameInfo\s*\{(.*?)^\s*\}", text, re.S)
    assert match, "MAPINFO has no GameInfo block"
    return match.group(1)


def strip_mapinfo_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


class IncludeTest(unittest.TestCase):
    def test_zscript_txt_includes_the_file_once(self):
        text = strip_mapinfo_comments(ZSCRIPT_TXT.read_text(encoding="utf-8"))
        self.assertEqual(len(re.findall(rf'#include\s+"{re.escape(INCLUDE)}"', text)), 1)
        self.assertTrue(STATUS_BAR_ZS.is_file())

    def test_the_class_derives_from_doom_and_is_alone_in_its_file(self):
        code = status_bar_code()
        self.assertEqual(re.findall(r"\bclass\s+(\w+)\s*:\s*(\w+)", code), [(CLASS, PARENT)])
        self.assertEqual(code.count("{"), code.count("}"), "unbalanced braces")


class OnlyDrawPausedTest(unittest.TestCase):
    """The bar must stay Doom's: one override, no state of our own."""

    def test_exactly_one_override_and_it_is_draw_paused(self):
        overrides = re.findall(r"\boverride\s+\w+\s+(\w+)\s*\(", status_bar_code())
        self.assertEqual(overrides, [VIRTUAL])
        self.assertRegex(status_bar_code(), r"\boverride\s+bool\s+DrawPaused\s*\(\s*int\s+player\s*\)")

    def test_no_fields_and_no_other_functions(self):
        code = status_bar_code()
        depth, members = 0, []
        for statement in re.split(r"(?<=[;{}])", code):
            body = statement.strip()
            if depth == 1 and body and not body.startswith(("const ", "}")):
                members.append(body)
            depth += statement.count("{") - statement.count("}")
        # At class depth only constants and the one function header may appear.
        headers = [m for m in members if m.endswith("{")]
        others = [m for m in members if not m.endswith("{")]
        self.assertEqual(others, [], "a field (or stray statement) at class level")
        self.assertEqual(len(headers), 1, headers)   # the class header sits at depth 0
        self.assertTrue(headers[0].startswith("override bool DrawPaused"), headers)

    def test_it_falls_back_to_the_engine_and_draws_where_the_engine_does(self):
        raw = STATUS_BAR_ZS.read_text(encoding="utf-8")
        code = status_bar_code()
        self.assertRegex(code, r"if\s*\(\s*!\s*pauseSign\.IsValid\(\)\s*\)\s*\{\s*return\s+false\s*;")
        self.assertRegex(code, r"return\s+true\s*;\s*\}\s*\}\s*$")
        self.assertRegex(raw, rf"const\s+SD_PAUSE_SIGN_TOP\s*=\s*{SIGN_TOP}\s*;")
        self.assertRegex(raw, rf'const\s+SD_PAUSE_SIGN_ID\s*=\s*"\${STRING_ID}"\s*;')
        self.assertRegex(code, r"DrawTexture\(\s*pauseSign\s*,\s*true\s*,\s*x\s*,\s*SD_PAUSE_SIGN_TOP\s*,\s*DTA_CleanNoMove\s*,\s*true\s*\)")
        self.assertRegex(code, r"CheckForTexture\([^;]*TexMan\.Type_MiscPatch\s*\)\s*;")


class MapinfoTest(unittest.TestCase):
    def test_gameinfo_registers_the_class_once(self):
        text = strip_mapinfo_comments(MAPINFO.read_text(encoding="utf-8"))
        everywhere = re.findall(r'(?im)^\s*StatusBarClass\s*=\s*"([^"]*)"', text)
        self.assertEqual(everywhere, [CLASS])
        self.assertRegex(gameinfo_block(text), rf'(?im)^\s*StatusBarClass\s*=\s*"{CLASS}"\s*$')

    def test_no_sbarinfo_of_our_own(self):
        """An SBARINFO in the mod would compete with the class (ST_CreateStatusBar)."""
        lumps = {p.name.split(".")[0].upper() for p in (SRC / "lumps").iterdir() if p.is_file()}
        self.assertNotIn("SBARINFO", lumps)


class LanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def value(self, code: str) -> str:
        return self.sections[code][STRING_ID].strip('"')

    def test_english_names_m_pause(self):
        self.assertEqual(self.value("default"), ENGLISH_SIGN)

    def test_russian_names_the_packed_variant_by_its_full_path(self):
        russian = self.value("ru")
        self.assertIn("/", russian, "a full path is what makes CheckForTexture look up the file")
        packed = {e.path.lower(): e.path for e in collect_assets(ASSETS)}
        self.assertIn(russian.lower(), packed, "the [ru] value is not a path the build packs")
        self.assertEqual(packed[russian.lower()], VARIANT_PATH)

    def test_the_english_sign_is_packed_under_graphics(self):
        packed = {e.path for e in collect_assets(ASSETS)}
        self.assertIn(f"graphics/{ENGLISH_SIGN}.png", packed)


class AssetTest(unittest.TestCase):
    def test_same_size_as_the_base(self):
        self.assertEqual(png_size(VARIANT_ASSET), png_size(BASE_ASSET))
        self.assertEqual(png_size(VARIANT_ASSET), (77, 20))   # MOD-SPEC 2

    def test_it_is_p2_russian_byte_for_byte(self):
        if not P2_RUSSIAN.is_file():
            self.skipTest("work/ is not in this clone (gitignored)")
        self.assertEqual(VARIANT_ASSET.read_bytes(), P2_RUSSIAN.read_bytes())

    def test_it_differs_from_the_english_plaque(self):
        self.assertNotEqual(VARIANT_ASSET.read_bytes(), BASE_ASSET.read_bytes())


class ReleaseCreditTest(unittest.TestCase):
    def test_localized_is_an_asset_folder(self):
        self.assertIn("localized", release.ASSET_DIRS)
        self.assertIn(VARIANT_PATH, release.asset_paths([VARIANT_PATH, "MAPINFO", "graphics/M_PAUSE.png"]))

    def test_base_name_of_a_variant(self):
        self.assertEqual(release.localized_base(VARIANT_PATH), "M_PAUSE")
        self.assertEqual(release.localized_base("localized/textures/M_PAUSE.ru-uk.png"), "M_PAUSE")
        self.assertIsNone(release.localized_base("graphics/M_PAUSE.png"))
        self.assertIsNone(release.localized_base("M_PAUSE.ru.png"))

    def test_the_real_register_covers_the_variant_through_m_pause(self):
        rows = release.parse_licence_register(LICENSES.read_text(encoding="utf-8"))
        covering = [r for r in rows if r.covers(VARIANT_PATH)]
        self.assertTrue(covering, "no LICENSES.md row covers the Russian pause plaque")
        self.assertTrue(any("M_PAUSE" in (t.upper() for t in r.tokens) for r in covering))
        result = release.check_licences([VARIANT_PATH], rows, [], {})
        self.assertFalse([e for e in result.errors if VARIANT_PATH in e], result.errors)

    def test_a_variant_with_no_row_is_refused(self):
        rows = release.parse_licence_register(LICENSES.read_text(encoding="utf-8"))
        orphan = "localized/textures/SDNOPE1.ru.png"
        result = release.check_licences([orphan], rows, [], {})
        self.assertTrue([e for e in result.errors if e.startswith(orphan)], result.errors)


class EngineNamesTest(unittest.TestCase):
    """Every name the file uses exists in the installed gzdoom.pk3 (T13)."""

    @classmethod
    def setUpClass(cls):
        pk3 = gzdoom_pk3()
        if pk3 is None:
            raise unittest.SkipTest("no gzdoom.pk3 on this machine (CI)")
        with zipfile.ZipFile(pk3) as zf:
            cls.names = zf.namelist()
            cls.zscript = "\n".join(zf.read(n).decode("latin-1") for n in cls.names
                                    if n.lower().endswith(".zs"))
            cls.doomcommon = zf.read("mapinfo/doomcommon.txt").decode("latin-1")
            cls.language = "\n".join(zf.read(n).decode("utf-8", "replace") for n in cls.names
                                     if n.lower().startswith("language."))
            cls.mapinfos = {n: zf.read(n).decode("latin-1") for n in cls.names
                            if n.lower().endswith(".txt") and "mapinfo" in n.lower()}
        cls.words = {w.lower() for w in re.findall(r"[A-Za-z_]\w*", cls.zscript)}

    def test_every_declaration_the_file_relies_on(self):
        missing = [name for name, pattern in DECLARATIONS.items()
                   if not re.search(pattern, self.zscript, re.M | re.I)]
        self.assertEqual(missing, [], "gzdoom.pk3 no longer declares these as the file assumes")

    def test_every_identifier_in_the_file_is_an_engine_name(self):
        used = {w.lower() for w in re.findall(r"[A-Za-z_]\w*", status_bar_code())}
        foreign = used - OWN_NAMES - ZS_KEYWORDS - {"sd_statusbar"}
        unknown = sorted(foreign - self.words)
        self.assertEqual(unknown, [], "names gzdoom.pk3's ZScript does not have")
        undeclared = sorted(foreign - {k.lower() for k in DECLARATIONS}
                            - {"texman", "screen", "stringtable"})
        self.assertEqual(undeclared, [], "add these to DECLARATIONS so a rename is caught")

    def test_doom_names_the_parent_class(self):
        self.assertRegex(self.doomcommon, rf'(?im)^\s*statusbarclass\s*=\s*"{PARENT}"')
        self.assertNotRegex(self.doomcommon, r'(?im)^\s*statusbar\s*=',
                            "doomcommon sets an SBARINFO status bar again")

    def test_the_by_line_string_exists(self):
        self.assertIn("TXT_BY", self.language)

    def test_nothing_gzdoom_loads_for_doom_sets_another_status_bar(self):
        """Only filter/harmony/ (another game) may; doomcommon is the parent's."""
        setters = sorted(n for n, t in self.mapinfos.items()
                         if re.search(r'(?im)^\s*statusbar(class)?\s*=', t))
        for name in setters:
            low = name.lower()
            if low == "mapinfo/doomcommon.txt":
                continue
            self.assertFalse(low.startswith(("filter/doom", "filter/game-doom")),
                             f"{name} sets a status bar for Doom games")
            self.assertTrue(low.startswith("filter/") or low.startswith("mapinfo/"), name)
            if low.startswith("mapinfo/"):
                self.assertNotRegex(low, r"mapinfo/(doom|freedoom)", name)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not present (CI has no IWAD)")
    def test_freedoom_defines_no_status_bar(self):
        data = IWAD.read_bytes()
        count, offset = struct.unpack("<ii", data[4:12])
        lumps = {data[offset + 16 * i + 8: offset + 16 * i + 16].rstrip(b"\0").decode("latin-1").upper()
                 for i in range(count)}
        self.assertFalse(lumps & {"MAPINFO", "ZMAPINFO", "SBARINFO", "GAMEINFO"})


class DocumentsTest(unittest.TestCase):
    def test_mod_spec_and_the_adr_carry_the_contract(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertIn("### 6.5.1", spec)
        for needle in (f"`{CLASS}`", f"`{STRING_ID}`", 'StatusBarClass = "SD_StatusBar"',
                       "localized/textures/m_pause.ru.png"):
            self.assertIn(needle, spec)
        self.assertTrue(ADR.is_file())
        adr = ADR.read_text(encoding="utf-8")
        for check in ("E1", "E2", "E3"):
            self.assertIn(f"| {check} |", adr)


if __name__ == "__main__":
    unittest.main()
