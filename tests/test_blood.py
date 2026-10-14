"""D49 (CEO, 2026-10-14): blood is dark red for every faction, "nada de oliva".

Pins the one `BloodColor` every enemy class carries, ties it to the palette
and to BESTIARY 2.1 (which owns the colour contract), and checks what the
colour does to the stock blood sprite. GZDoom does not paint blood with the
`BloodColor` value itself: CreateBloodTranslation (g4.14.2,
src/r_data/r_translate.cpp) maps every palette index to
`BloodColor * max(r, g, b) / 255`, so the value is the colour at FULL
brightness and Freedoom's BLUD pixels come out darker. The last test runs
that formula on the real BLUD frames (skipped where there is no IWAD, as in
CI) and proves the hit blood lands on the same flag_red 0-5 band the drawn
deaths use (tools/art/gen_rig.py, BLOOD_MAX_INDEX).

Run:  python3 -m unittest tests.test_blood -v
"""

from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MONSTERS_DIR = PROJECT_ROOT / "src" / "zscript" / "monsters"
BESTIARY_MD = PROJECT_ROOT / "docs" / "engine" / "BESTIARY.md"
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"

D49_BLOOD = "AD 27 21"          # flag_red 9 = (173, 39, 33), the colour at full brightness
D49_RAMP, D49_INDEX = "flag_red", 9
BLOOD_MAX_INDEX = 5             # the drawn deaths stop at flag_red 5 (gen_rig.BLOOD_MAX_INDEX)
# Every class that bleeds, one file each; SD_PanzermenschSchwer inherits its
# parent's blood and must not set its own.
BLEEDERS = ("reich_rifleman.zs", "legion_trooper.zs", "stormtrooper.zs", "reich_hound.zs",
            "doughboy.zs", "panzermensch.zs", "general.zs")
INHERITS = ("panzermensch_schwer.zs",)
RE_BLOOD = re.compile(r'^\s*BloodColor\s+"([^"]*)"\s*;', re.M)
RETIRED = ("53 4A 30", "C6 BD AA")   # khaki_olive 3 (Reich) and plaster_warm 12 (Legion)


def rgb(value: str) -> tuple[int, int, int]:
    r, g, b = (int(x, 16) for x in value.split())
    return r, g, b


def ramp(name: str) -> list[tuple[int, int, int]]:
    data = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    for entry in data["ramps"]:
        if entry["name"] == name:
            return [tuple(c) for c in entry["colours"]]
    raise AssertionError(f"no ramp {name} in palette.json")


def section_2_1() -> str:
    text = BESTIARY_MD.read_text(encoding="utf-8")
    match = re.search(r"^### 2\.1 .*?$(.*?)(?=^### )", text, re.M | re.S)
    if not match:
        raise AssertionError("BESTIARY.md has no section 2.1")
    return match.group(1)


class BloodColourTest(unittest.TestCase):
    def test_every_enemy_bleeds_d49_dark_red(self):
        for filename in BLEEDERS:
            found = RE_BLOOD.findall((MONSTERS_DIR / filename).read_text(encoding="utf-8"))
            self.assertEqual([D49_BLOOD], found, f"{filename}: BloodColor must be D49's {D49_BLOOD}")

    def test_heavy_panzermensch_inherits_the_blood(self):
        for filename in INHERITS:
            found = RE_BLOOD.findall((MONSTERS_DIR / filename).read_text(encoding="utf-8"))
            self.assertIn(found, ([], [D49_BLOOD]), filename)

    def test_no_monster_keeps_a_retired_blood(self):
        for path in sorted(MONSTERS_DIR.glob("*.zs")):
            for value in RE_BLOOD.findall(path.read_text(encoding="utf-8")):
                self.assertNotIn(value.upper(), RETIRED, f"{path.name}: olive or pale blood is gone (D49)")
                self.assertEqual(D49_BLOOD, value.upper(), path.name)

    def test_the_colour_is_a_palette_red(self):
        self.assertEqual(ramp(D49_RAMP)[D49_INDEX], rgb(D49_BLOOD))

    def test_bestiary_2_1_says_dark_red_and_cites_d49(self):
        text = section_2_1()
        row = next((line for line in text.splitlines() if line.startswith("| Blood")), "")
        self.assertTrue(row, "BESTIARY 2.1 lost its Blood row")
        self.assertIn("dark red", row.lower())
        self.assertNotIn("olive", row.lower())
        self.assertNotIn("pale", row.lower())
        self.assertIn("D49", text)
        self.assertIn(f'"{D49_BLOOD}"', text)


class BloodOnScreenTest(unittest.TestCase):
    """The engine's blood translation applied to Freedoom's BLUD frames."""

    @classmethod
    def setUpClass(cls):
        if not IWAD.is_file():
            raise unittest.SkipTest("no iwads/freedoom2.wad")
        blob = IWAD.read_bytes()
        _magic, count, offset = struct.unpack("<4sii", blob[:12])
        lumps = {}
        for i in range(count):
            pos, size, name = struct.unpack("<ii8s", blob[offset + 16 * i: offset + 16 * i + 16])
            lumps.setdefault(name.rstrip(b"\0").decode("ascii"), (pos, size))
        pos, _size = lumps["PLAYPAL"]
        cls.playpal = [tuple(blob[pos + 3 * i: pos + 3 * i + 3]) for i in range(256)]
        cls.indices: set[int] = set()
        for name in (n for n in lumps if n.startswith("BLUD")):
            pos, size = lumps[name]
            patch = blob[pos: pos + size]
            width = struct.unpack("<h", patch[:2])[0]
            for column in struct.unpack(f"<{width}i", patch[8: 8 + 4 * width]):
                q = column
                while patch[q] != 0xFF:          # Doom patch posts: top, length, pad, pixels, pad
                    length = patch[q + 1]
                    cls.indices.update(patch[q + 3: q + 3 + length])
                    q += 4 + length
        if not cls.indices:
            raise unittest.SkipTest("no BLUD frames in the IWAD")

    def translated(self) -> list[tuple[int, int, int]]:
        r, g, b = rgb(D49_BLOOD)
        out = []
        for index in sorted(self.indices):
            bright = max(self.playpal[index])
            out.append((r * bright // 255, g * bright // 255, b * bright // 255))
        return out

    def test_hit_blood_lands_on_the_deaths_red_band(self):
        reds = ramp(D49_RAMP)

        def nearest(c):
            return min(range(len(reds)), key=lambda i: sum((a - b) ** 2 for a, b in zip(c, reds[i])))

        steps = {nearest(c) for c in self.translated()}
        self.assertLessEqual(max(steps), BLOOD_MAX_INDEX,
                             f"the brightest hit blood is flag_red {max(steps)}: brighter than the drawn deaths")
        self.assertGreaterEqual(len(steps), 3, "the blood sprite collapsed to too few shades")
