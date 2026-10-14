"""MAP02's blue pass: SD_BluePass replaces Doom's BlueCard.

Contract: docs/engine/MOD-SPEC.md 6, "The blue pass"; the map:
docs/levels/MAP02-metro.md 5. What is pinned here, without ever starting
GZDoom (D26):

  * zscript.txt includes keys.zs once, and the file declares
    `SD_BluePass : BlueCard replaces BlueCard`, so the editor number 5 that
    MAP02 places spawns it with the map untouched;
  * the class sets `Species "BlueCard"` and its own pickup id, and borrows
    its sprite from BlueCard (no States block: MOD-SPEC 5.1 has no row);
  * LANGUAGE says "pass" / "propusk" in both languages: the pickup line and
    the engine's two lock-2 lines PD_BLUEC / PD_BLUECO;
  * lock 2 accepts the class. GZDoom's lock test (OneKey::check,
    src/gamedata/a_keys.cpp, g4.14.2) accepts an inventory item when its
    class IS the key (DObject::IsA, exact) or its Species is the key's
    name; inheritance is never consulted. `lock_accepts` below is that
    rule, and it runs against lock 2 as GZDoom ships it: read from the
    installed gzdoom.pk3 when there is one, else the copy recorded here
    from g4.14.2 (CI has no engine).

What it cannot pin is what the engine does: MOD-SPEC 6's checks P1-P6, the
PM's engine pass.

Run:  python3 -m unittest tests.test_blue_pass -v
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
TOOLS = PROJECT_ROOT / "tools"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(TOOLS))

import smoke  # noqa: E402  (only its engine-locating helper; nothing is run)
from sdbuild.pk3 import build as build_pk3  # noqa: E402
from test_bestiary import strip_zs_comments, zs_default  # noqa: E402
from test_language import parse_language  # noqa: E402

KEYS_ZS = SRC / "zscript" / "sd" / "keys.zs"
ZSCRIPT_TXT = SRC / "lumps" / "zscript.txt"
LANGUAGE = SRC / "lumps" / "LANGUAGE"
OWN_LOCKDEFS = SRC / "lumps" / "LOCKDEFS"
MAP02 = SRC / "maps" / "MAP02" / "map.py"
MOD_SPEC = PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md"
INCLUDE = "zscript/sd/keys.zs"

CLASS = "SD_BluePass"
REPLACED = "BlueCard"
LOCK = 2
DOOM_EDNUM = 5
PICKUP_ID = "SD_PICKUP_BLUEPASS"

# Lock 2 exactly as gzdoom.pk3 g4.14.2 -> lockdefs.txt writes it (read
# 2026-10-14). Used when no engine is installed; when one is, the test
# below compares this copy with the real file.
ENGINE_LOCKDEFS_G4_14_2 = """
Lock 2 Doom
{
	//$Title "Blue key card"
	BlueCard
	Message "$PD_BLUEC"
	RemoteMessage "$PD_BLUECO"
	Mapcolor 0 0 255
}
"""

# The lock keywords ParseLock knows (a_keys.cpp, keywords_lock) and how many
# arguments each takes; anything else in a lock block is a key class name.
LOCK_KEYWORD_ARGS = {"message": 1, "remotemessage": 1, "mapcolor": 3}


# --- the engine's rules, in Python ----------------------------------------

def strip_cpp_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


GAME = "Doom"   # gameinfo.gametype on freedoom2.wad and doom2.wad


def parse_lock(lockdefs: str, number: int, game: str = GAME) -> dict:
    """One `Lock N [game] { ... }` block -> {keys, message, remote}.

    `keys` is the list of key groups that must ALL be held; a plain key name
    is a group of one, `Any { a b }` a group of several (ParseLock). The
    LAST definition of the number wins, as Locks.InsertNew does. A block for
    another game (`Lock 2 Chex`, `Lock 2 Heretic`) goes to ParseLock's sink
    (CheckGame), so it is skipped here.
    """
    text = strip_cpp_comments(lockdefs)
    found = None
    for match in re.finditer(r"\bLock\s+(\d+)\s*(\w+)?\s*\{", text, re.I):
        block_game = match.group(2)
        if int(match.group(1)) != number or (block_game and block_game.lower() != game.lower()):
            continue
        depth, end = 1, match.end()
        while depth:
            depth += {"{": 1, "}": -1}.get(text[end], 0)
            end += 1
        found = text[match.end():end - 1]
    if found is None:
        raise KeyError(f"no Lock {number}")
    tokens = re.findall(r'"[^"]*"|[{}]|[^\s{}"]+', found)
    lock = {"keys": [], "message": None, "remote": None}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()
        if low == "any":
            close = tokens.index("}", i)
            lock["keys"].append(tokens[i + 2:close])
            i = close + 1
        elif low in LOCK_KEYWORD_ARGS:
            args = tokens[i + 1:i + 1 + LOCK_KEYWORD_ARGS[low]]
            if low == "message":
                lock["message"] = args[0].strip('"')
            elif low == "remotemessage":
                lock["remote"] = args[0].strip('"')
            i += 1 + LOCK_KEYWORD_ARGS[low]
        elif low == "lockedsound":
            i += 2
            while i < len(tokens) and tokens[i] == ",":
                i += 2
        else:
            lock["keys"].append([tok])
            i += 1
    return lock


def species_of(class_name: str, species: str | None) -> str:
    """AActor::GetSpecies for a non-monster: Species, else its own class."""
    return species if species else class_name


def lock_accepts(lock: dict, class_name: str, species: str | None) -> bool:
    """P_CheckKeys -> Lock::check -> Keygroup::check -> OneKey::check for a
    player holding exactly one item. FNames compare case-insensitively.
    Inheritance plays no part: IsA is `type == GetClass()`."""
    held = {class_name.lower(), species_of(class_name, species).lower()}
    if not lock["keys"]:
        return True                     # an empty lock opens for any Key
    return all(any(key.lower() in held for key in group) for group in lock["keys"])


def installed_lockdefs() -> str | None:
    """lockdefs.txt from the gzdoom.pk3 beside an installed GZDoom, if any."""
    for exe in smoke.gzdoom_candidates():
        pk3 = exe.parent / "gzdoom.pk3"
        if pk3.is_file():
            with zipfile.ZipFile(pk3) as zf:
                return zf.read("lockdefs.txt").decode("utf-8", "replace")
    return None


def engine_lock(number: int) -> dict:
    return parse_lock(installed_lockdefs() or ENGINE_LOCKDEFS_G4_14_2, number)


def effective_lock(number: int) -> dict:
    """The lock the game runs with: ours if the mod ships a LOCKDEFS that
    defines it (loaded after gzdoom.pk3), else the engine's."""
    if OWN_LOCKDEFS.is_file():
        try:
            return parse_lock(OWN_LOCKDEFS.read_text(encoding="utf-8"), number)
        except KeyError:
            pass
    return engine_lock(number)


def keys_source() -> str:
    return KEYS_ZS.read_text(encoding="utf-8")


def class_species() -> str | None:
    value = zs_default(keys_source(), "Species")
    return value.strip('"') if value else None


# --- tests -----------------------------------------------------------------

class ClassTest(unittest.TestCase):
    def test_zscript_txt_includes_keys_once(self):
        includes = re.findall(r'^\s*#include\s+"([^"]+)"', ZSCRIPT_TXT.read_text(encoding="utf-8"), re.M)
        self.assertEqual(includes.count(INCLUDE), 1, f"{INCLUDE} must be included exactly once")
        self.assertTrue(KEYS_ZS.is_file())

    def test_the_class_replaces_bluecard_and_derives_from_it(self):
        code = strip_zs_comments(keys_source())
        self.assertRegex(code, rf"\bclass\s+{CLASS}\s*:\s*{REPLACED}\s+replaces\s+{REPLACED}\b",
                         "SD_BluePass must derive from AND replace BlueCard: the replacement "
                         "is what puts it where MAP02 places editor number 5")

    def test_species_is_bluecard(self):
        """THE line that opens MAP02's blast door (see lock_accepts)."""
        self.assertEqual(class_species(), REPLACED)

    def test_the_pickup_line_is_an_id_of_ours(self):
        self.assertEqual(zs_default(keys_source(), "Inventory.PickupMessage"), f'"${PICKUP_ID}"')

    def test_the_sprite_is_the_pass(self):
        """D63: SDKB A/B replaced BlueCard's inherited BKEY; the states are
        BlueCard's but for the name (tests/test_pickup_sprites.py)."""
        code = strip_zs_comments(keys_source())
        self.assertRegex(code, r"\bStates\b")
        self.assertRegex(code, r"(?m)^\s*SDKB\s+A\s+10\s*;")
        self.assertNotRegex(code, r"(?m)^\s*BKEY\s")

    def test_the_file_is_ascii(self):
        self.assertTrue(keys_source().isascii(), "every other .zs of the mod is ASCII; keep it so")

    def test_braces_balance(self):
        code = strip_zs_comments(keys_source())
        self.assertEqual(code.count("{"), code.count("}"))


class LanguageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = parse_language(LANGUAGE.read_text(encoding="utf-8"))

    def value(self, code: str, key: str) -> str:
        self.assertIn(key, self.sections[code], f"[{code}] has no {key}")
        return self.sections[code][key].strip('"')

    def test_the_pickup_line_in_both_languages(self):
        self.assertEqual(self.value("default", PICKUP_ID), "Blue pass.")
        self.assertEqual(self.value("ru", PICKUP_ID), "Синий пропуск.")

    def test_lock_2_lines_say_pass_in_english(self):
        for key in ("PD_BLUEC", "PD_BLUECO"):
            text = self.value("default", key).lower()
            self.assertIn("blue pass", text, key)
            self.assertNotIn("card", text, key)

    def test_lock_2_lines_say_propusk_in_russian(self):
        for key in ("PD_BLUEC", "PD_BLUECO"):
            text = self.value("ru", key).lower()
            self.assertIn("синий пропуск", text, key)
            self.assertNotIn("карт", text, key)

    def test_the_overridden_ids_are_lock_2s(self):
        """The ids we rewrite must be the ones lock 2 prints; MAP02's door
        works by tag (4), so the player reads the REMOTE one."""
        lock = effective_lock(LOCK)
        self.assertEqual({lock["message"], lock["remote"]}, {"$PD_BLUEC", "$PD_BLUECO"})
        self.assertEqual(lock["remote"], "$PD_BLUECO")


class LockTest(unittest.TestCase):
    def test_the_recorded_lock_matches_the_installed_engine(self):
        real = installed_lockdefs()
        if real is None:
            self.skipTest("no gzdoom.pk3 installed (CI): the recorded g4.14.2 copy stands in")
        self.assertEqual(parse_lock(real, LOCK), parse_lock(ENGINE_LOCKDEFS_G4_14_2, LOCK))

    def test_lock_2_accepts_the_pass(self):
        lock = effective_lock(LOCK)
        self.assertTrue(lock_accepts(lock, CLASS, class_species()),
                        f"lock {LOCK} ({lock['keys']}) would not open for {CLASS} "
                        f"with Species {class_species()!r}: MAP02 could not be finished")

    def test_inheritance_alone_would_not_open_it(self):
        """The trap the Species line avoids: GZDoom does not walk parents."""
        self.assertFalse(lock_accepts(engine_lock(LOCK), CLASS, None))

    def test_lock_2_still_accepts_dooms_bluecard(self):
        """`give BlueCard` (NO_REPLACE) still opens it: the model is sane."""
        self.assertTrue(lock_accepts(engine_lock(LOCK), REPLACED, None))

    def test_other_games_locks_are_ignored(self):
        text = ENGINE_LOCKDEFS_G4_14_2 + "\nLock 2 Chex { ChexBlueCard }\n"
        self.assertEqual(parse_lock(text, LOCK)["keys"], [["BlueCard"]])

    def test_the_rule_is_all_groups_any_member(self):
        lock = parse_lock("Lock 9 { A Any { B C } }", 9)
        self.assertEqual(lock["keys"], [["A"], ["B", "C"]])
        self.assertFalse(lock_accepts(lock, "A", None))
        self.assertTrue(lock_accepts(parse_lock("Lock 9 { Any { B C } }", 9), "X", "c"))

    def test_map02_still_asks_for_editor_number_5_and_lock_2(self):
        """Read-only: the map is level-designer's. If either constant moves,
        the replacement no longer reaches the map's key or door."""
        source = MAP02.read_text(encoding="utf-8")
        self.assertRegex(source, rf"(?m)^ED_BLUE_CARD\s*=\s*{DOOM_EDNUM}\b")
        self.assertRegex(source, rf"(?m)^LOCK_BLUE_CARD\s*=\s*{LOCK}\b")


class PackageTest(unittest.TestCase):
    def test_keys_zs_is_packed(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sovietdoom.pk3"
            build_pk3(SRC, out, TOOLS, PROJECT_ROOT / "assets")
            with zipfile.ZipFile(out) as zf:
                self.assertIn(INCLUDE, zf.namelist())


class SpecTest(unittest.TestCase):
    def test_mod_spec_records_the_class_and_the_mechanism(self):
        spec = MOD_SPEC.read_text(encoding="utf-8")
        self.assertIn(f"| `{CLASS}` | `{REPLACED}` *replaces {REPLACED}* |", spec)
        self.assertIn("**The blue pass (MAP02, 2026-10-14).**", spec)
        self.assertIn('Species "BlueCard"', spec)
        self.assertIn("give SD_BluePass", spec)


if __name__ == "__main__":
    unittest.main()
