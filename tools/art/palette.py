"""Generate the mod palette: docs/art/palette.json (the only source of colours).

Run with the project venv:  .venv/bin/python tools/art/palette.py

Design (see docs/art/ART-BIBLE.md, "Palette"):

- The palette is built from **ramps**, like the original Doom palette: each
  ramp is one material/hue going from near-black to its lightest tone. Ramps
  let a texture be shaded (bevels, grime, lamps) without leaving the palette,
  and let the engine darken a sector smoothly (every ramp ends near black).
- Ramps are generated, not hand-picked, so the file is reproducible from
  this script. Colour endpoints are the named constants below; the rationale
  for each is the comment next to it.
- Total ≤ 256 colours (PNG indexed, `docs/art/ART-BIBLE.md` §2). Batch 1
  uses 162; the remaining slots are reserved for later sets (metro marble,
  mosaics, industrial rust) so that approved textures never need requantising.

Versions (ART-BIBLE §3):

- **v1**, 162 colours, ratified by the CEO on 2026-10-12 ("Palette OK"):
  `RAMPS` + `EXTRAS`. Frozen: never edited, never reordered.
- **v2**, 226 colours, D45 (CEO, 2026-10-14): v1 followed by the four
  `ADDED_RAMPS` (marble red, mosaic cobalt, mosaic gold, flesh pink) in the
  reserved slots, built with the same gamma rule. v1 is the first 162
  entries of v2, index for index, so a v1 PNG is a valid v2 PNG.
- **v3**, 242 colours, D128 (CEO, 2026-10-24: "añade paleta si es
  necesario"): v2 followed by one more ramp, `reich_greygreen` (the Reich's
  grey-green skin), in slots 226-241 of the 30 that v2 left reserved. v2 is
  the first 226 entries of v3, so no approved asset changes: a PNG only
  ever holds colours of its own version (tests/test_palette_v2.py), and no
  version before v3 has a colour in those slots.

Layout of palette.json since v2. The top-level `colours` / `ramps` /
`index` / `count` are still **v1**, deliberately: they are what
`artlib.quantize`, `check_pk3.py` and every generator read by default, so
no approved v1 texture can pick up a v2 colour when it is regenerated (the
"approved textures keep their colours" rule, made mechanical). v2 lives in
`colours_v2` (the full list), `added_ramps` and `added_index`, and a
generator opts in explicitly with `colours(2)` / `ramp_colours(name)`
below. The top-level view moves to v2 only when the first v2 texture is
approved, together with artlib, check_pk3 and their tests.

Since v3 (D128) `colours_v2` stays exactly v2 (226 colours: every reader
that means "palette v2" by that key, check_pk3 and the generators' tests
among them, keeps meaning it) and `colours_v3` is the full v3 list; a
generator opts into v3 with `colours(3)`. Only the Consortium (SDCN,
gemini_enemy.CONSORTIUM) is drawn in v3 today.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PALETTE_JSON = PROJECT_ROOT / "docs" / "art" / "palette.json"

# Hard limit of an indexed PNG / Doom palette.
MAX_COLOURS = 256

# Ramp length. 16 is Doom's own granularity for most of its ramps: enough
# steps for a bevel + a shadow + a highlight without visible banding at 1x.
RAMP_STEPS = 16
# The dominant material (cold concrete) gets a longer ramp: most of MAP01's
# surface area is concrete, and the long ramp hides banding on large flats.
CONCRETE_STEPS = 32

# Gamma used when interpolating ramps. Linear interpolation in sRGB makes the
# dark half of a ramp too dark too fast; 1.8 keeps more usable mid-dark tones,
# which is where Doom lighting (sector light 96-160) lives.
RAMP_GAMMA = 1.8

# Each ramp: (name, darkest RGB, lightest RGB, steps, why).
# Darkest tones are not pure black: a pure-black floor under diminished
# lighting loses all texture. Pure black and white are added separately.
RAMPS = [
    (
        "concrete_cold",
        (10, 11, 14), (212, 214, 218), CONCRETE_STEPS,
        "Prefab concrete of the 1970s cosmodrome, slightly blue: the base "
        "material of the Soviet base set (walls, floors, ceilings).",
    ),
    (
        "plaster_warm",
        (18, 16, 12), (224, 214, 192), RAMP_STEPS,
        "Warm whitewash and poster paper. Breaks the monotony of cold "
        "concrete; also the cream of propaganda typography.",
    ),
    (
        "military_green",
        (8, 12, 7), (142, 160, 104), RAMP_STEPS,
        "Soviet 4BO-style military green: steel doors, riveted plates, "
        "crates, vehicles.",
    ),
    (
        "flag_red",
        (26, 4, 4), (228, 52, 44), RAMP_STEPS,
        "Flag red for stars, banners, stripes and poster grounds. The top "
        "of the ramp is the painted red of Soviet signage, not orange.",
    ),
    (
        "cream_yellow",
        (40, 32, 10), (248, 236, 176), RAMP_STEPS,
        "Aged cream of posters and painted walls; light of incandescent "
        "and fluorescent lamps.",
    ),
    (
        "hazard_yellow",
        (52, 40, 0), (250, 208, 40), RAMP_STEPS,
        "Saturated industrial yellow: hangar floor markings, hazard stripes, "
        "the hammer and sickle on red.",
    ),
    (
        "steel_blue",
        (8, 10, 14), (176, 186, 200), RAMP_STEPS,
        "Bare steel and chrome: bunker door frames, rivets, pipes, rails. "
        "Blue-grey so that it reads apart from concrete.",
    ),
    (
        "rust_brown",
        (20, 8, 4), (204, 122, 60), RAMP_STEPS,
        "Rust, dried grime, wood and leather. Used sparingly in the base "
        "(it is the industrial set's main colour).",
    ),
    (
        "khaki_olive",
        (18, 16, 8), (196, 176, 116), RAMP_STEPS,
        "Uniform khaki and sun-faded paint. Bridges green and cream.",
    ),
]

# Extra single colours outside the ramps.
EXTRAS = [
    ("black", (0, 0, 0), "True black for the deepest shadows and outlines."),
    ("white", (255, 255, 255), "True white for lamp cores and specular dots."),
]

# ------------------------------------------------------------ palette v2
# D45 (CEO, 2026-10-14): three additions in the reserved slots, appended
# after v1 so no v1 colour moves. "Cobalt and gold" is two ramps of 16, not
# one: a single gamma ramp from blue to gold passes through grey-green in
# the middle and would be useless for either. 4 x 16 = 64 of the 94 free
# slots; 30 stay reserved (the industrial set, MAP03).
#
# Saturation is chosen against the neighbours already in v1: the marble
# sits between flag_red (signage, HSV saturation ~0.81) and flesh_pink
# (~0.26) at ~0.67, so a marble wall, a red stripe and a Legion face are
# three different reds; the gold is a warmer, less saturated smalt gold
# (~0.70) than hazard_yellow's paint (~0.84); the cobalt is a true blue
# (~0.57), never confused with steel_blue's grey-blue (~0.12).
PALETTE_V2_DATE = "2026-10-14"
PALETTE_V2_DECISION = "D45"
PALETTE_V3_DATE = "2026-10-24"
PALETTE_V3_DECISION = "D128"
ADDED_RAMPS = [
    # (name, darkest RGB, lightest RGB, steps, version, why)
    (
        "marble_red",
        (22, 6, 6), (234, 100, 78), RAMP_STEPS, 2,
        "Red marble of the metro stations (the warm Shrosha-type stone of the "
        "1930s-50s halls): between flag_red's signage red and flesh_pink, so "
        "a marble wall never reads as a painted stripe or as a face.",
    ),
    (
        "mosaic_cobalt",
        (3, 5, 26), (110, 150, 255), RAMP_STEPS, 2,
        "Cobalt smalt, the blue ground of the metro mosaics. A true blue; "
        "steel_blue is a grey-blue and stays the Liberty Legion's chrome.",
    ),
    (
        "mosaic_gold",
        (36, 20, 2), (255, 206, 76), RAMP_STEPS, 2,
        "Gold smalt of the mosaics: warmer and less saturated than "
        "hazard_yellow, so a gilded star reads as metal leaf, not as paint.",
    ),
    (
        # Endpoints taken unchanged from the candidate in
        # tools/art/gen_legion.py (FLESH_DARK, FLESH_LIGHT): the Legion
        # drafts the CEO saw are drawn with exactly these 16 colours.
        "flesh_pink",
        (24, 10, 10), (242, 190, 180), RAMP_STEPS, 2,
        "Pink flesh of the Liberty Legion (LORE, BESTIARY 2.1): low "
        "saturation so it reads as skin; steel_blue gives its chrome.",
    ),
    # ------------------------------------------------------- palette v3
    # D128 (CEO, 2026-10-24): one ramp in the reserved slots 226-241 (14
    # stay free). Endpoints fitted to the grey-green flesh of the Reich half
    # in the CEO's Gemini sheets of the Consortium (consortium_gemini.ramps()
    # "gflesh": G over R by ~15, over B by ~12 at mid tone); v2 had no such
    # colour and snapped that skin to concrete grey. Bluer and greyer than
    # military_green (HSV saturation ~0.12 against ~0.35), so a Reich face
    # never reads as a steel door or a crate.
    (
        "reich_greygreen",
        (8, 14, 11), (166, 188, 170), RAMP_STEPS, 3,
        "Grey-green skin of the Reich's undead (LORE, BESTIARY): the "
        "German half of the Consortium; greyer and bluer than "
        "military_green so flesh never reads as painted steel.",
    ),
]

# Version history: (version, date, decision, what it added).
VERSIONS = [
    (1, "2026-10-12", "ratified by the CEO in the batch-1 verdict (\"Palette OK\")",
     [name for name, *_ in RAMPS] + [name for name, *_ in EXTRAS]),
    (2, PALETTE_V2_DATE, f"{PALETTE_V2_DECISION}: marble red, mosaic cobalt and gold, flesh pink "
     "in the reserved slots; approved textures keep their colours",
     [r[0] for r in ADDED_RAMPS if r[4] == 2]),
    (3, PALETTE_V3_DATE, f"{PALETTE_V3_DECISION}: the Reich's grey-green skin in the reserved slots "
     "(the Consortium's German half); approved assets keep their colours",
     [r[0] for r in ADDED_RAMPS if r[4] == 3]),
]
LATEST_VERSION = VERSIONS[-1][0]


def _lerp_gamma(a: int, b: int, t: float) -> int:
    """Interpolate one channel with RAMP_GAMMA (perceptual-ish ramp)."""
    la, lb = (a / 255) ** RAMP_GAMMA, (b / 255) ** RAMP_GAMMA
    v = la + (lb - la) * t
    return round((v ** (1 / RAMP_GAMMA)) * 255)


def ramp_rule(dark, light, steps: int) -> list[list[int]]:
    """The one ramp rule of the palette: `steps` colours from `dark` to
    `light`, each channel interpolated with RAMP_GAMMA."""
    return [
        [_lerp_gamma(dark[c], light[c], i / (steps - 1)) for c in range(3)]
        for i in range(steps)
    ]


def build_ramps() -> list[dict]:
    """The v1 ramps (frozen)."""
    return [{"name": name, "why": why, "colours": ramp_rule(dark, light, steps)}
            for name, dark, light, steps, why in RAMPS]


def build_added_ramps() -> list[dict]:
    """The ramps added after v1, in slot order, each tagged with its version."""
    return [{"name": name, "version": version, "why": why,
             "colours": ramp_rule(dark, light, steps)}
            for name, dark, light, steps, version, why in ADDED_RAMPS]


def build_palette() -> dict:
    ramps = build_ramps()
    flat: list[list[int]] = []
    index: dict[str, list[int]] = {}
    for ramp in ramps:
        start = len(flat)
        flat.extend(ramp["colours"])
        index[ramp["name"]] = [start, len(flat) - 1]
    extras = []
    for name, rgb, why in EXTRAS:
        index[name] = [len(flat), len(flat)]
        flat.append(list(rgb))
        extras.append({"name": name, "rgb": list(rgb), "why": why})

    # v2 and later: appended after v1, so every v1 index keeps its colour.
    added = build_added_ramps()
    full = [list(c) for c in flat]
    added_index: dict[str, list[int]] = {}
    for ramp in added:
        start = len(full)
        full.extend(ramp["colours"])
        added_index[ramp["name"]] = [start, len(full) - 1]
    counts = {}
    for version, *_ in VERSIONS:
        counts[version] = len(flat) + sum(len(r["colours"]) for r in added if r["version"] <= version)
    versions = [{"version": v, "date": date, "decision": decision, "adds": adds, "count": counts[v]}
                for v, date, decision, adds in VERSIONS]

    for colours in (flat, full):
        assert len(colours) <= MAX_COLOURS, f"{len(colours)} colours > {MAX_COLOURS}"
        assert len({tuple(c) for c in colours}) == len(colours), "duplicate colour"
    assert full[:len(flat)] == flat, "v1 must be the exact prefix of every later version"
    assert counts[LATEST_VERSION] == len(full)
    return {
        "name": "Soviet Doom palette",
        "version": LATEST_VERSION,
        "date": PALETTE_V3_DATE,
        "decision": PALETTE_V3_DECISION,
        "generator": "tools/art/palette.py",
        "layout": (
            "colours, ramps, extras, index and count are palette v1 (the frozen 162 colours every "
            "approved texture is drawn in, and what artlib.quantize and check_pk3 read by default). "
            "colours_v2 is the full v2 list: v1 as its exact prefix, then the v2 added_ramps at the "
            "slots given by added_index. colours_v3 is the full v3 list (D128): v2 as its exact "
            "prefix, then the v3 added_ramps. A generator opts into a version explicitly "
            "(palette.colours(2), palette.colours(3))."),
        "max_colours": MAX_COLOURS,
        "count": len(flat),
        "ramp_gamma": RAMP_GAMMA,
        "ramps": ramps,
        "extras": extras,
        "index": index,
        "colours": flat,
        "versions": versions,
        "added_ramps": added,
        "added_index": added_index,
        "colours_v2": full[:counts[2]],
        "colours_v3": full,
    }


# ------------------------------------------------- readers (for generators)
_loaded: dict | None = None


def load() -> dict:
    """palette.json as written by main() (cached)."""
    global _loaded
    if _loaded is None:
        _loaded = json.loads(PALETTE_JSON.read_text(encoding="utf-8"))
    return _loaded


def colours(version: int = 1) -> list[tuple[int, int, int]]:
    """The colour list of one palette version, in index order."""
    pal = load()
    count = {v["version"]: v["count"] for v in pal["versions"]}
    if version not in count:
        raise KeyError(f"palette version {version} does not exist")
    full = pal.get(f"colours_v{max(count)}", pal["colours_v2"])
    return [tuple(c) for c in full[:count[version]]]


def ramp_colours(name: str) -> list[tuple[int, int, int]]:
    """Colours of any ramp, v1 or added, darkest first."""
    pal = load()
    for r in pal["ramps"] + pal["added_ramps"]:
        if r["name"] == name:
            return [tuple(c) for c in r["colours"]]
    raise KeyError(name)


def ramp_version(name: str) -> int:
    """The palette version that introduced a ramp (1 for every v1 ramp)."""
    for r in load()["added_ramps"]:
        if r["name"] == name:
            return r["version"]
    ramp_colours(name)          # KeyError if it does not exist at all
    return 1


def main() -> None:
    pal = build_palette()
    PALETTE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PALETTE_JSON.write_text(json.dumps(pal, indent=1), encoding="utf-8")
    print(f"wrote {PALETTE_JSON} (v{pal['version']}: {len(pal['colours_v3'])} colours; "
          f"v1 {pal['count']} colours in {len(pal['ramps'])} ramps, "
          f"+{len(pal['added_ramps'])} added ramps)")


if __name__ == "__main__":
    main()
