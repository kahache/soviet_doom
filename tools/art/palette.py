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


def _lerp_gamma(a: int, b: int, t: float) -> int:
    """Interpolate one channel with RAMP_GAMMA (perceptual-ish ramp)."""
    la, lb = (a / 255) ** RAMP_GAMMA, (b / 255) ** RAMP_GAMMA
    v = la + (lb - la) * t
    return round((v ** (1 / RAMP_GAMMA)) * 255)


def build_ramps() -> list[dict]:
    ramps = []
    for name, dark, light, steps, why in RAMPS:
        colours = [
            [_lerp_gamma(dark[c], light[c], i / (steps - 1)) for c in range(3)]
            for i in range(steps)
        ]
        ramps.append({"name": name, "why": why, "colours": colours})
    return ramps


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
    assert len(flat) <= MAX_COLOURS, f"{len(flat)} colours > {MAX_COLOURS}"
    assert len({tuple(c) for c in flat}) == len(flat), "duplicate colour"
    return {
        "name": "Soviet Doom palette",
        "version": 1,
        "generator": "tools/art/palette.py",
        "max_colours": MAX_COLOURS,
        "count": len(flat),
        "ramp_gamma": RAMP_GAMMA,
        "ramps": ramps,
        "extras": extras,
        "index": index,
        "colours": flat,
    }


def main() -> None:
    pal = build_palette()
    PALETTE_JSON.parent.mkdir(parents=True, exist_ok=True)
    PALETTE_JSON.write_text(json.dumps(pal, indent=1), encoding="utf-8")
    print(f"wrote {PALETTE_JSON} ({pal['count']} colours, {len(pal['ramps'])} ramps)")


if __name__ == "__main__":
    main()
