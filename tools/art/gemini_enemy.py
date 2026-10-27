"""Enemy sprite sets from Gemini model sheets (D104/D105: "redo the enemies, let Gemini improve them").

    python tools/art/gemini_enemy.py rifleman            # lumps + metrics into work/art/enemies_gemini/rifleman/
    python tools/art/gemini_enemy.py legion|storm        # the Legion trooper (SDLT), the hybrid stormtrooper (SDHS)
    python tools/art/gemini_enemy.py hound|doughboy|panzer|panzer_heavy|general   # D105 batch 2
    python tools/art/gemini_enemy.py all                 # every enemy, then the overlay and the sheet
    python tools/art/gemini_enemy.py rifleman --check    # print the plan (sheets, figures, facings, scales) only
    python tools/art/gemini_enemy.py overlay             # every built enemy -> work/overlays/sd-draft-enemies.pk3
    python tools/art/gemini_enemy.py sheet               # the CEO's review sheet (docs/art/previews/...)
    python tools/art/gemini_enemy.py armband             # the armband-symbol PROPOSAL (not installed anywhere)

Input: the PM's Gemini sheets in work/art/reference/enemies/gemini/gem_<enemy>_<pose>.png
(gitignored, never pushed, D77): one row of figures on a flat background that
is magenta-ish but not exactly #FF00FF (pale pink, dark magenta). A standing
pose sheet holds the five views front, 3/4 front, profile, 3/4 back, back;
the death sheets hold rotation-0 frames. Batch 2 (D105): the hound's sheets are
a 2 x 4 grid (`Sheet.rows`, `Sheet.pick` chooses the five views) with a painted
ground shadow (`Sheet.shadow`); the hound ships mirror pairs (`EnemySpec.pairs`,
SDHNA2A8); the doughboy hangs under its origin (`feet_sink`); misplaced glows
and an ember in flight are erased (`Sheet.erase`), a projectile dropped
(`Sheet.core`); figures bridged by a flash or smoke are cut at fixed columns
with the bridge given to its owner (`Sheet.split_x`); the Panzermensch's
lettered armbands become plain fields (`patch` mode) and the Schwer is the
same art larger with a black plate (`shade`); the General's death armbands
are covered by hand (`Sheet.patch`).

Output: the SAME lumps the enemy ships today in assets/sprites/<folder>/
(same frame letters, same rotations, same names), RGBA with hard alpha, in
palette v2 (the Consortium in v3, D128: EnemySpec.palette_version), each with its grAb offsets: `left` = the canvas' half width on
the body's axis, `top` = the floor line, FEET_SINK px above the feet's last
row, the same for every rotation of a frame (MOD-SPEC 6.3). Written to
work/art/enemies_gemini/<enemy>/, never to assets/ (`guard_out`).

The steps (pure functions on arrays, tests/test_gemini_enemy.py):
  1. estimate_background - the commonest border colour (quantised), per image
  2. key_background      - alpha: colour distance to it above KEY_TOL, then
                           FRINGE_PASSES rims of near-background pixels go (halo)
  3. label / figures     - 8-connected components; the `count` biggest are the
                           figures (a merged pair, two flashes touching, is cut
                           at its emptiest column); a small piece within
                           ATTACH_PX of a figure joins it (a flash, a dropped
                           rifle, blood drops), anything further is dropped
                           (the stray helmet, the A/B/C letters)
  3b. sole               - a figure cut by the sheet's bottom edge (the
                           stormtrooper's 193-px sheets) gets `Sheet.sole`
                           rows of dark boot sole under its last row
  4. blank_armband       - any symbol inside the armband's white field is
                           painted white (Gemini's own symbol on the death
                           sheet); `box` mode paints the field's whole box
                           white (a white cross on red becomes a plain white
                           patch); `none` leaves it (the Legion's US flag).
  4b. the D12 symbol      - D108, "la mezcla" ("the mix"): on the Reich (EnemySpec.symbol),
                           AFTER the mirror (source_picture: never mirrored),
                           armband_symbol's option 1 on every field it finds
                           (select_fields), and on the close pictures (the
                           profiles, rotations 3 and 7, and the corpse letters:
                           close_sources) option 2, Fooocus' repaint, from
                           work/art/armband_fooocus/cache/ (made by run_d108.py
                           there; this tool never runs SDXL). `--symbol none`
                           builds the empty fields of D105; `control` draws the
                           control sheet
  5. normalise_facing    - a side view that faces right is mirrored, so views
                           2-4 face left (Doom's rotations 2-4); `auto` reads
                           the facing from where the art reaches further from
                           the legs' axis (the rifle's muzzle). With
                           `armband_side`, a front (back) view whose armband
                           is on the other side of the legs' axis is mirrored
                           too, so a body part (the hybrid's mechanical arm)
                           keeps its side of the body in every sheet
  6. sheet scale         - every sheet to the turn sheet's scale by the helmet's
                           width (death2 is drawn larger); one global scale puts
                           the turn sheet's front view at TARGET_HEIGHT rows,
                           with Doom's 1.2 pixel aspect
  7. downscale           - premultiplied box filter, alpha >= 1/2, palette v2 (v3: CONSORTIUM)
  8. outline             - edge pixels not already dark are shaded (sel-out)
  9. place               - per frame letter, one canvas for all rotations,
                           feet on the floor line, the legs' axis at `left`;
                           rotations 6-8 are rotations 4-2 mirrored, written
                           as eight separate lumps (no A2A8 pairs: the armband
                           sits on one arm, as in the set it replaces)
Frames Gemini does not draw are derived and listed in `derived` of the
metrics: pain in rotations 2-8 (the standing view, tilted back), the gib
(the death frames with procedural blood).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import re
import struct
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import palette  # noqa: E402

ROOT = artlib.PROJECT_ROOT
REF_DIR = ROOT / "work" / "art" / "reference" / "enemies" / "gemini"
OUT_ROOT = ROOT / "work" / "art" / "enemies_gemini"
SPRITES_DIR = ROOT / "assets" / "sprites"
OVERLAY = ROOT / "work" / "overlays" / "sd-draft-enemies.pk3"
SHEET_HTML = ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_enemies-gemini.html"
ARMBAND_PNG = ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_rifleman-armband-proposal.png"
# Nothing of a draft goes into the build input, the build output or the
# approved art: reaching any of them is an approval the CEO did not give.
FORBIDDEN_OUT = ("assets", "src", "dist")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)   # as tools/sdbuild/pk3.py: reproducible

TRANSPARENT = -1
BG_QUANT = 8            # border colours are binned to 8 levels before the mode
KEY_TOL = 60.0          # RGB distance to the background under which a pixel is background
FRINGE_TOL = 110.0      # a rim pixel this close to the background is a halo pixel
FRINGE_PASSES = 2       # rims peeled
FIGURE_FRAC = 0.25      # a component this fraction of the biggest is a figure
ATTACH_PX = 12          # source px: a smaller piece this close to a figure belongs to it
MIN_PIECE = 6           # source px: specks smaller than this are noise
SPLIT_MARGIN = 0.15     # a merged pair is cut no nearer its ends than this fraction
LEGS_FRAC = 0.4         # the bottom fraction of a figure whose median column is its axis
FACING_RATIO = 1.15     # one side must reach this much further to call a facing
HELMET_BAND = 0.09      # x the reference height: the band under the top that is the helmet
RED_MIN, RED_GB_MAX = 110, 90      # armband red: r above, g and b below (and r > 2 g)
WHITE_MIN, WHITE_SPREAD = 150, 80  # armband field: every channel above, max - min below
ARMBAND_NEAR = 4                   # px: a white group this close to red is the armband's field
FIELD_GAP = 2                      # px: white pixels this close are one field
MIN_FIELD = 4                      # white px: a smaller group is a glint, not a field
TARGET_HEIGHT = 59      # rows of SDRRA1's figure today (10..68): the new set is as tall in game
LEGION_HEIGHT = 56      # rows of SDLTA1's figure today (13..68)
STORM_HEIGHT = 50       # rows of SDHSA1's figure today (19..68)
SOLE_RGB = (26, 24, 20)  # the derived boot sole under a figure cut by the sheet's bottom edge
STORM_SOLE = 5          # source rows: the stormtrooper's boots end at the 193-px sheets' last row
FIELD_BOX_MAX = 14      # source px: a `box`-mode field taller or wider is not an armband (sparks, the energy ball)
BOX_WHITE_MIN = 125     # `box` mode: the hybrid's field is beige in shade (182,172,145)
BOX_PURITY = 0.45       # `box` mode: a field's box must be this much white or red (measured: bands 0.48-1.0, cannon 0.17)
MARKER_RED_MIN = 60     # the armband's red for the side test: darker than RED_MIN (the hybrid's band in shade)
MARKER_MIN_PX = 8       # red px needed to read a side
MARKER_OFFSET = 4.0     # source px: the band's mean column must be this far off the legs' axis
FEET_SINK = 4           # the feet's last row is this far under `top` (as SDRRA1: top 64, feet 68)
PIXEL_ASPECT = 1.2      # Doom's 320x200 is shown at 4:3: square Gemini pixels are squashed
CANVAS_PAD = 2          # px of air round the widest rotation
OUTLINE_SHADE = 0.45    # x the inner neighbours' colour: the sel-out outline
PAIN_TILT = 9.0         # degrees the standing view leans back for a derived pain frame
VIEW_OF_ROT = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 3, 7: 2, 8: 1}   # the five views -> eight rotations
MIRRORED_ROTS = (6, 7, 8)
SIDE_VIEWS = (1, 2, 3)  # views that face a side; normalised to face LEFT (Doom rotations 2-4)
BLOOD_RGB = ((92, 10, 10), (128, 16, 14), (165, 26, 20), (60, 6, 6))
TICS_PER_SEC = 35
# D105, batch 2 (hound, doughboy, Panzermensch, General)
HOUND_HEIGHT = 36       # rows of SDHNA3A7's figure today (20..55): the hound is sized by its PROFILE
DOUGHBOY_HEIGHT = 77    # rows of SDDBA1's figure today (14..90)
PANZER_HEIGHT = 68      # rows of SDPMA1's figure today (23..90)
PANZER_HEAVY_HEIGHT = 76  # SDPM x 1.12: the Schwer is drawn 12 % larger (D65, D67)
GENERAL_HEIGHT = 96     # rows of SDGNA1's figure today (24..119)
DOUGHBOY_SINK = 14      # the floating head hangs 14 px under its origin (SDDBA1: top 76, last row 90)
SHADOW_G = 0.45         # a painted ground shadow: green under this x min(r, b) ...
SHADOW_RB = 0.35        # ... red and blue within this fraction of each other (the background's hue, darker)
SHADOW_MIN = 30         # ... and not black
GLOW_BLUE = 25          # `erase`: a glow pixel is this much bluer than red ...
GLOW_WHITE = 205        # ... or this bright in every channel (the white-hot core)
BRIDGE_FIRE_R, BRIDGE_FIRE_G = 225, 0.55     # a split's flash: red above, green above this x red, blue under green
BRIDGE_SMOKE_SPREAD, BRIDGE_SMOKE_MIN, BRIDGE_SMOKE_MAX = 26, 110, 240   # a split's smoke: grey, light, not white
FIRE_R, FIRE_G, FIRE_B = 170, 0.35, 30   # `erase` fire: red above, green above this x red, blue under green + this
ERASE_KEEP = 0.03       # after an erase, pieces under this fraction of the figure go (stray sparks)
FLAG_BLUE = 0.08        # a white field whose box is this much blue is a US flag, not an armband: left alone
PATCH_LIGHT = 110       # `patch` mode: a light mark on the band has every channel above this ...
PATCH_SPREAD = 100      # ... and max - min under this (white to the E's pink in shade)
PATCH_RING = 3          # px round a `patch` mark whose figure pixels ...
PATCH_RING_RED = 0.2    # ... must be at least this much red (measured: the E's 0.26-0.93, glints and gloves 0.0-0.11)
PATCH_PURITY = 0.55     # a `patch` box this much light or red (the E's 0.56-0.83; a glint on the armour 0.29-0.46)
PATCH_YELLOW = 20       # ... and no more than this yellower (blue under green): the General's coat is
PATCH_TINT = 12         # a light mark may be this much greener than red (a cold white)
PATCH_FLAG_BLUE = 0.03  # blue within a field's width round a `patch` mark: a US flag, left alone
PATCH_MIN_SIDE = 3      # source px: a light mark thinner than this is a glint (between the visor's eyes)
PATCH_RGB = (226, 220, 206)   # the plain field painted over it (the proposal's field colour)
PANZER_FIELD_MAX = 20   # source px: the «E» (~13) and the back emblem's field (~17); a glow is bigger
SHADE_KEEP = 190        # a pixel this bright in some channel is a glow: the plate's shade spares it
PLATE_SHADE = 0.55      # the Schwer's black plate (D65): every colour but red and white x this
NEW_TOL = 80            # `guide`: a pixel this far (max channel) from every guide pixel within 1 px is new paint
FLASH_MIN = 40          # `guide`: new paint with fewer flash-coloured px than this is not a muzzle flash
ALIGN_R = 3             # `guide`: px searched each way to register the guide sheet on this one
FLASH_GLOW = 8          # `guide`: px round a flash where a neighbour's body is repainted from the guide (the glow Gemini cast on it)


# ------------------------------------------------------------------ specs
@dataclass(frozen=True)
class Sheet:
    """One Gemini image: `count` figures in a row, left to right."""
    file: str
    count: int
    facing: tuple[str, ...] = ()     # per figure: front/back/left/right/auto (side views)
    scale_ref: int | None = 0        # the figure whose helmet sets the sheet's scale; None: 1.0
    sole: int = 0                    # source rows of derived sole under a figure touching the bottom edge
    rows: int = 1                    # a grid sheet (the hound's 2 x 4): figures are read row by row
    pick: tuple[int, ...] = ()       # grid-order figures used, in view order (front ... back); () all
    core: bool = False               # keep each figure's biggest piece only (a projectile in flight goes)
    shadow: bool = False             # key out Gemini's painted ground shadow (the background's hue, darker)
    erase: tuple = ()                # (view, (x0, y0, x1, y1) fractions of the box[, "glow"|"fire"]): that goes
    split_x: tuple = ()              # (sheet column, "fire"|"smoke"|""): where figures bridged by a flash or smoke are cut
    rel_scale: float = 1.0           # with scale_ref None: the sheet drawn this much smaller than turn
    patch: tuple = ()                # (view, (x0, y0, x1, y1) source px of the figure's crop): painted a plain field
    guide: str = ""                  # D119: the sheet Gemini painted this one over (the gunner's fire over turn): split by its figures
    flash: tuple = ()                # with `guide`: (x0, x1, view): a muzzle flash centred in sheet columns x0..x1 goes to that figure
    path: tuple = ()                 # ((x, y), ...) left to right: a merged pair is cut along it, the lower figure under it


@dataclass(frozen=True)
class Src:
    """Where a lump's picture comes from."""
    sheet: str
    view: int                        # figure index on the sheet
    tilt: float = 0.0                # degrees leaning back (a derived pain frame)
    blood: int = 0                   # procedural blood: 0 none, 1-3 spray, 4-6 pool (the gib)
    mirror: bool = False             # flipped (an override for a rotation that faces the other way)
    core: bool = False               # the figure's biggest piece only (smoke or debris left behind)


@dataclass(frozen=True)
class Rotated:
    """A frame letter in eight rotations from a five-view sheet."""
    sheet: str
    tilt: float = 0.0
    override: tuple[tuple[int, Src], ...] = ()   # (rotation, Src): another picture for that rotation


@dataclass(frozen=True)
class EnemySpec:
    name: str
    sprite: str                      # four letters, e.g. SDRR
    folder: str                      # assets/sprites/<folder>/: the set it replaces
    sheets: dict
    rotated: dict                    # letter -> Rotated
    single: dict                     # letter -> Src (rotation 0)
    ref_sheet: str = "turn"          # its view 0 sets TARGET_HEIGHT
    derived: tuple[str, ...] = ()    # what is not Gemini's own drawing, for the report
    anims: tuple = ()                # (label, ((letter, tics), ...), loop)
    notes: str = ""
    target_height: int = TARGET_HEIGHT   # rows of the turn sheet's front view in game (the shipped A1's)
    armband: str = "blank"           # blank: a symbol in the field goes; box: the field's box goes white; none
    armband_side: str | None = None  # side of the legs' axis the armband is on in a FRONT view (normalised)
    reask: tuple = ()                # (file, short prompt): what to ask Gemini for again (the quality gate)
    pairs: bool = False              # rotations 2-4 written as mirror pairs (SDHNA2A8), as the shipped set
    feet_sink: int = FEET_SINK       # rows of the picture under `top` (a floating head hangs lower)
    ref_view: int = 0                # the ref sheet's view whose height is target_height
    shade: float = 1.0               # every colour but red and white x this (the Schwer's black plate)
    field_max: int | None = None     # source px: a white field bigger than this is not an armband (blank/fill)
    symbol: str = "none"             # the D12 symbol on the armband (D108): none, or warp (armband_symbol, option 1)
    symbol_fields: str = "white"     # how its fields are found (armband_symbol.select_fields)
    corpse: tuple[str, ...] = ()     # death letters seen close (the corpse, the frame before): option 2 on them
    palette_version: int = 2         # the palette the lumps snap to (docs/art/palette.json); 3 = v2 + reich_greygreen (D128)


STAND = ("front", "left", "left", "left", "back")
SIDES_AUTO = ("front", "auto", "auto", "auto", "back")

RIFLEMAN = EnemySpec(
    name="rifleman", sprite="SDRR", folder="rifleman", symbol="warp", corpse=("K", "L"),
    sheets={
        "turn": Sheet("gem_rifleman_turn.png", 5, STAND),
        "walkL": Sheet("gem_rifleman_walkL.png", 5, STAND),
        "walkR": Sheet("gem_rifleman_walkR.png", 5, STAND),
        "aim": Sheet("gem_rifleman_aim.png", 5, SIDES_AUTO),
        "fire": Sheet("gem_rifleman_fire.png", 5, SIDES_AUTO),
        "death": Sheet("gem_rifleman_death.png", 6),        # 5 and 6 are wrong: unused
        "death2": Sheet("gem_rifleman_death2.png", 3),      # drawn larger: helmet-normalised
    },
    rotated={
        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("fire"),
        "G": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
    },
    single={
        "H": Src("death", 1), "I": Src("death", 2), "J": Src("death2", 0), "K": Src("death2", 1),
        "L": Src("death2", 2),
        "M": Src("death", 1, blood=1), "N": Src("death", 1, blood=2), "O": Src("death", 2, blood=2),
        "P": Src("death", 3, blood=3), "Q": Src("death2", 0, blood=3), "R": Src("death2", 1, blood=3),
        "S": Src("death2", 2, blood=4), "T": Src("death2", 2, blood=5), "U": Src("death2", 2, blood=6),
    },
    derived=(   # shown to the CEO on the review sheet (English, D129)
        "B and D: the same standing view (turn); Gemini gives two strides (A = walkL, C = walkR) and the still view",
        "G2-G8 (pain): the standing view tilted 9 degrees backwards; G1 is Gemini's pain (death, figure 1)",
        "M-U (gib, XDeath): Gemini has no sheet; they are the death frames with procedural blood (spurt, then pool)",
        "rotations 6-8: 4-2 mirrored (rifle and armband change arm, like Doom's mirror pairs)",
    ),
    anims=(
        ("walk (See: A A B B C C D D, 4 tics)", (("A", 8), ("B", 8), ("C", 8), ("D", 8)), True),
        ("fire (Missile: E 10, F 8, E 8)", (("E", 10), ("F", 8), ("E", 8), ("B", 12)), True),
        ("pain (Pain: G 6)", (("B", 20), ("G", 6), ("B", 14)), True),
        ("die (Death: H I J K 5, L)", (("H", 5), ("I", 5), ("J", 5), ("K", 5), ("L", 45)), True),
        ("gib (XDeath: M-T 5, U)", tuple((c, 5) for c in "MNOPQRST") + (("U", 45),), True),
    ),
)

LEGION = EnemySpec(
    name="legion", sprite="SDLT", folder="legion", target_height=LEGION_HEIGHT, armband="none",
    sheets={
        "turn": Sheet("gem_legion_turn.png", 5, SIDES_AUTO),
        "walkL": Sheet("gem_legion_walkL.png", 5, SIDES_AUTO),
        "walkR": Sheet("gem_legion_walkR.png", 5, SIDES_AUTO),
        "aim": Sheet("gem_legion_aim.png", 5, SIDES_AUTO),
        "fire": Sheet("gem_legion_fire.png", 5, SIDES_AUTO),
        "death": Sheet("gem_legion_death.png", 5),         # pain, impact, falling 45, nearly down, lying
    },
    rotated={
        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("fire"),
        "G": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
    },
    single={
        "H": Src("death", 0), "I": Src("death", 1), "J": Src("death", 2), "K": Src("death", 3),
        "L": Src("death", 4),
        "M": Src("death", 0, blood=1), "N": Src("death", 1, blood=1), "O": Src("death", 1, blood=2),
        "P": Src("death", 2, blood=2), "Q": Src("death", 2, blood=3), "R": Src("death", 3, blood=3),
        "S": Src("death", 4, blood=4), "T": Src("death", 4, blood=5), "U": Src("death", 4, blood=6),
    },
    derived=(
        "B and D: the standing view (turn); A = walkL, C = walkR",
        "G2-G8 (pain): the standing view tilted 9 degrees; G1 = Gemini's pain (death, figure 1)",
        "H-L (death): the death sheet's 5 figures as drawn (pain, impact, falling, nearly down, lying)",
        "M-U (gib, XDeath): no Gemini sheet; the death frames with procedural blood (spurt and pool)",
        "rotations 6-8: 4-2 mirrored. The flag: Gemini painted it on the trooper's RIGHT shoulder "
        "(image left when facing us), consistent in the 5 views; the mirror moves it to the other shoulder in "
        "2-3 (Gemini drew the 3/4 and the profile facing right) and it stays on his shoulder in 7-8. "
        "At game scale it is ~3x2 px: accepted, like the shotgun changing hands. To make it exact, "
        "ask Gemini for the 3 views of the other side (see the list) and set them as overrides of 2-4",
        "armband: none (the Legion wears none; the flag is left alone: armband='none')",
    ),
    anims=(
        ("walk (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("fire (Missile: E 10, F 10, E 10)", (("E", 10), ("F", 10), ("E", 10), ("B", 12)), True),
        ("pain (Pain: G 3, G 3)", (("B", 20), ("G", 6), ("B", 14)), True),
        ("die (Death: H I J K 5, L)", (("H", 5), ("I", 5), ("J", 5), ("K", 5), ("L", 45)), True),
        ("gib (XDeath: M-T 5, U)", tuple((c, 5) for c in "MNOPQRST") + (("U", 45),), True),
    ),
    reask=(
        ("gem_legion_turnB.png", "Same Liberty Legion trooper, same style and scale, magenta background: "
         "3/4 front, profile and 3/4 back views facing LEFT, US flag patch on his RIGHT shoulder, "
         "10 px of background under the boots"),
        ("gem_legion_death.png", "Same 5 death frames, with 12 px of background on every side: the lying "
         "body's dropped shotgun is cut by the right and bottom edges"),
    ),
)

STORM = EnemySpec(
    name="storm", sprite="SDHS", folder="storm", target_height=STORM_HEIGHT, armband="box",
    armband_side="right", symbol="warp", symbol_fields="box", corpse=("L", "M"),
    sheets={   # one canvas size and scale (193 px): no helmet normalisation (scale_ref None)
        "turn": Sheet("gem_storm_turn.png", 5, SIDES_AUTO, None, STORM_SOLE),
        "walkL": Sheet("gem_storm_walkL.png", 5, SIDES_AUTO, None, STORM_SOLE),
        "walkR": Sheet("gem_storm_walkR.png", 5, SIDES_AUTO, None, STORM_SOLE),
        "aim": Sheet("gem_storm_aim.png", 5, SIDES_AUTO, None, STORM_SOLE),
        "fire": Sheet("gem_storm_fire.png", 5, SIDES_AUTO, None, STORM_SOLE),
        "death": Sheet("gem_storm_death.png", 5, scale_ref=None, sole=STORM_SOLE),
    },
    rotated={
        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("aim"), "G": Rotated("fire"),
        "H": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
    },
    single={
        "I": Src("death", 0), "J": Src("death", 1), "K": Src("death", 2), "L": Src("death", 3),
        "M": Src("death", 4),
        "N": Src("death", 0, blood=1), "O": Src("death", 1, blood=1), "P": Src("death", 1, blood=2),
        "Q": Src("death", 2, blood=2), "R": Src("death", 2, blood=3), "S": Src("death", 3, blood=3),
        "T": Src("death", 4, blood=5), "U": Src("death", 4, blood=6),
    },
    derived=(
        "B and D: the standing view (turn); A = walkL, C = walkR",
        "E and F: the same charge (aim) twice (the class asks for E F 8 tics before G); G = fire (the bolt). "
        "Melee uses the same E F G",
        "H2-H8 (pain): the standing view tilted 9 degrees; H1 = Gemini's pain (death, figure 1)",
        "I-M (death): the death sheet's 5 figures as drawn (the 2nd with the sparks, the 5th with the smoke)",
        "N-U (gib, XDeath): no Gemini sheet; the death frames with procedural blood",
        "boots: the six sheets (193 px) cut the soles at the last row; a dark sole "
        "5 source px tall (~1 px in game) is added under every figure touching the edge",
        "mechanical arm: measured by the armband (left arm) in the front and back views of the "
        "6 sheets, the body is NOT flipped in any of them (the big mechanical arm is always the right one, "
        "image left when facing us). What changes is the WEAPON: in turn/walk the drill-cannon comes out of the "
        "mechanical arm; in aim/fire the energy cannon comes out of the left arm (the armband's) and the "
        "mechanical one hangs. Mirroring aim/fire would flip the body and the ball would jump sides going from "
        "walking to firing, so the rule (armband_side) mirrors no view; if the CEO wants the bolt from the "
        "mechanical arm, Gemini is asked again (see the list)",
        "rotations 6-8: 4-2 mirrored (mechanical arm and armband change sides, as on the rifleman)",
        "armband: red with an EMPTY white field (D105); Gemini's white cross is painted plain white (box mode)",
    ),
    anims=(
        ("walk (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("attack (Missile: E F 8, G 6)", (("E", 8), ("F", 8), ("G", 6), ("B", 14)), True),
        ("pain (Pain: H 2, H 2)", (("B", 20), ("H", 4), ("B", 14)), True),
        ("die (Death: I 8 J 8 K 6 L 6, M)", (("I", 8), ("J", 8), ("K", 6), ("L", 6), ("M", 45)), True),
        ("gib (XDeath: N-T 5, U)", tuple((c, 5) for c in "NOPQRST") + (("U", 45),), True),
    ),
    reask=(
        ("gem_storm_turn.png, _walkL, _walkR, _aim, _fire, _death", "Same sheets on a 1024x238 canvas "
         "(not 193): the boots' soles are cut by the bottom edge; leave 10 px of background under the feet"),
        ("gem_storm_aim2.png, gem_storm_fire2.png", "Only if the CEO wants it: the energy ball charged and "
         "the bolt fired from the MECHANICAL right arm (image left when facing us), the human left arm "
         "with the red armband (plain white field, no symbol) hanging"),
        ("gem_storm_charge.png", "Optional: the same 5 views with a smaller, half-charged ball, so E and F differ"),
        ("gem_storm_aim.png, gem_storm_fire.png (views 4-5)", "Back views: the ball's glow must stay in front "
         "of him (hidden by the body), not painted over his back; the bolt starts AT the muzzle, no gap"),
    ),
)
# -------------------------------------------------- D105, second batch
HOUND_PICK = (0, 1, 2, 6, 3)   # 2 x 4 grid: front, 3/4 front, profile (top row), 3/4 back (bottom), back (top)
HOUND_LUNGE = 8.0       # degrees the bite leans forward for the derived snap (G)
GENERAL_DEATH_SCALE = 0.72   # the death sheet is drawn smaller: its bazooka is 152 px, the aim sheet's 210
GENERAL_FIRE_SPLIT = ((626, "fire"), (828, "smoke"), (418, "fire|smoke>"))   # the profile's muzzle flash and the 3/4 back's back-blast bridge figures
PANZER_EMBER = tuple((v, box, kind) for v in (0, 1) for box, kind in (   # the ember in flight, stuck to the fist
    ((0.75, 0.0, 1.0, 0.35), "fire"), ((0.8, 0.0, 1.0, 0.2), "all")))
PANZER_SOLE = 3         # source rows: the Panzermensch's boots end at the 182-px sheets' last row
# the symbol Gemini drew in the armband of death frames 1-4, by hand: the band is shaded and
# the symbol touches the glove and the coat, so the automatic grouping cannot isolate it
GENERAL_DEATH_FIELDS = ((0, (136, 71, 149, 83)), (1, (132, 104, 145, 116)), (2, (109, 58, 121, 68)),
                        (3, (151, 78, 159, 90)))
GENERAL_FIELD_MAX = 40  # source px: the General's armband field; his coat and the cape's stripes are bigger
STAND_RIGHT = ("front", "left", "right", "left", "back")   # the General's profile faces right on every sheet


def _hound(file: str) -> Sheet:
    return Sheet(file, 8, STAND, None, rows=2, pick=HOUND_PICK, shadow=True)


HOUND = EnemySpec(
    name="hound", sprite="SDHN", folder="hound", target_height=HOUND_HEIGHT, armband="none",
    pairs=True, ref_view=2,
    sheets={
        "turn": _hound("gem_hound_turn.png"),
        "walkL": _hound("gem_hound_walkL.png"),
        "walkR": _hound("gem_hound_walkR.png"),
        "bite": _hound("gem_hound_bite.png"),
        # pain, rearing, falling, sinking (drawn facing left), collapsing, lying: normalised to face left
        "death": Sheet("gem_hound_death.png", 6, ("right", "right", "right", "left", "right", "right"),
                       None, rows=2, shadow=True),
    },
    rotated={
        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
        "E": Rotated("turn"), "F": Rotated("bite"), "G": Rotated("bite", tilt=-HOUND_LUNGE),
        "H": Rotated("turn", tilt=PAIN_TILT, override=((3, Src("death", 0)),)),
    },
    single={
        "I": Src("death", 0), "J": Src("death", 1), "K": Src("death", 2), "L": Src("death", 3),
        "M": Src("death", 4), "N": Src("death", 5),
    },
    derived=(
        "sheets in a 2 x 4 grid (not 1 x 5): from each sheet we use front (row 1, figure 1), 3/4 front "
        "(row 1, 2), profile (row 1, 3), 3/4 back (row 2, 3) and back (row 1, 4); the other three "
        "(front and back repeated, row 2's big profile) are spare. The shadows painted on the "
        "ground (walkR, bite, death) are removed with the key (the background's dark magenta)",
        "size: the profile (A3A7 today, 36 rows) sets the height; the front ends up ~37 rows (31 today, "
        "but today's front is 14 px wide: Gemini's is a real front-on dog)",
        "rotations in mirror pairs (SDHNA2A8...), like today's set: the engine mirrors 6-8",
        "B and D: the still view (turn); A = walkL, C = walkR",
        "attack (Melee E F G): E = turn (growls), F = bite, G = bite tilted 8 degrees forward "
        "(the snap). The bite sheet barely changes pose (mouth wider and drool): it does NOT work as an "
        "attack on its own; see the list",
        "H (pain): the still view tilted 9 degrees; H3H7 = Gemini's pain (death, figure 1, in profile)",
        "I-N (death, 6 frames): death's 6 figures as drawn: pain, rearing, falling, sinking "
        "(drawn facing the other way: mirrored), collapsing, lying; all face left",
        "armband: none (armband='none')",
    ),
    anims=(
        ("run (See: A A B B C C D D, 2 tics)", (("A", 4), ("B", 4), ("C", 4), ("D", 4)), True),
        ("bite (Melee: E F 8, G 8)", (("E", 8), ("F", 8), ("G", 8), ("B", 12)), True),
        ("pain (Pain: H 2, H 2)", (("B", 20), ("H", 4), ("B", 14)), True),
        ("die (Death: I 8 J 8 K L M 4, N)", (("I", 8), ("J", 8), ("K", 4), ("L", 4), ("M", 4), ("N", 45)), True),
    ),
    reask=(
        ("gem_hound_lunge.png", "Same Reich hound, same style, scale and 2x4 grid, magenta background, NO "
         "ground shadow: the attack lunge, front paws off the ground, jaws wide open at full stretch, head "
         "thrust forward; front, 3/4 front, profile facing left, 3/4 back, back"),
        ("gem_hound_walkL.png, gem_hound_walkR.png", "Optional: the two strides more different (legs "
         "fully extended vs. gathered under the body), one row of 5 views, no shadow"),
        ("gem_hound_pain.png", "Optional: the hound flinching from a hit, head jerked aside, front view "
         "(for H1, today derived by tilting the standing view)"),
    ),
)

DOUGHBOY = EnemySpec(
    name="doughboy", sprite="SDDB", folder="doughboy", target_height=DOUGHBOY_HEIGHT, armband="none",
    feet_sink=DOUGHBOY_SINK,
    sheets={
        "turn": Sheet("gem_doughboy_turn.png", 5, STAND, None),
        # the profile's second glow on the back of the head and the glow on the 3/4 back's nape go
        "attack": Sheet("gem_doughboy_attack.png", 5, STAND, None,
                        erase=((2, (0.68, 0.25, 1.0, 0.9)), (3, (0.70, 0.3, 1.0, 0.9)))),
        "death": Sheet("gem_doughboy_death.png", 6, (), None),
    },
    rotated={
        "A": Rotated("turn"), "B": Rotated("turn"), "C": Rotated("attack"), "D": Rotated("attack"),
        "E": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
        "F": Rotated("turn", tilt=PAIN_TILT / 2, override=((1, Src("death", 1)),)),
    },
    single={
        "G": Src("death", 0), "H": Src("death", 1), "I": Src("death", 2), "J": Src("death", 3),
        "K": Src("death", 4), "L": Src("death", 5),
    },
    derived=(
        "A and B: the still view (turn); C and D: the open mouth with the ball (attack). The class asks for B C D "
        "at 5 tics: there is no in-between 'opens the mouth' frame, so B is the still head",
        "attack, view 3 (profile): the duplicated glow on the back of the head is erased; view 4 (3/4 back): the "
        "glow painted over the back of the head is erased (the mouth cannot be seen from there). Its blue "
        "and white pixels are removed; the head stays",
        "E (pain): E1 = Gemini's pain (death, figure 1, with sparks); E2-E8 the still view "
        "tilted 9 degrees. F (pain continues): F1 = the hit (death, figure 2); F2-F8 tilted 4.5 degrees",
        "G-L (death, 6 frames): death's 6 figures as drawn (pain, hit, cracks, falls, heap, "
        "remains with the helmet)",
        "hangs 14 px below its origin as today (floating head); the helmet's flag (D12) is left alone: "
        "armband='none'",
        "rotations 6-8: 4-2 mirrored (the helmet's flag shows on the other side, as on the Legion)",
    ),
    anims=(
        ("float (See: A 3)", (("A", 3),), True),
        ("attack (Missile: B C D 5)", (("B", 5), ("C", 5), ("D", 5), ("A", 15)), True),
        ("pain (Pain: E 3 E 3 F 6)", (("A", 20), ("E", 6), ("F", 6), ("A", 14)), True),
        ("die (Death: G-K 8, L)", (("G", 8), ("H", 8), ("I", 8), ("J", 8), ("K", 8), ("L", 45)), True),
    ),
    reask=(
        ("gem_doughboy_attack.png (views 3-4)", "Same 5 views: the profile with ONE energy ball, in the "
         "open mouth only; the 3/4 back view with no glow on the back of the head (the mouth faces away)"),
        ("gem_doughboy_charge.png", "Optional: the same 5 views with the mouth half open and a small "
         "spark, for the frame before the shot (B)"),
    ),
)


def _panzer(file: str, facing=STAND, core: bool = False, count: int = 5) -> Sheet:
    return Sheet(file, count, facing, None, PANZER_SOLE, core=core)


PANZER_SHEETS = {
    "turn": _panzer("gem_panzer_turn.png"),
    "walkL": _panzer("gem_panzer_walkL.png"),
    "walkR": _panzer("gem_panzer_walkR.png"),
    "aim": _panzer("gem_panzer_aim.png"),
    "fire": Sheet("gem_panzer_fire.png", 5, ("front", "right", "right", "left", "back"), None, PANZER_SOLE,
                  core=True, erase=PANZER_EMBER),
    "death": _panzer("gem_panzer_death.png", (), count=6),
}
PANZER_ROTATED = {
    "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
    "E": Rotated("aim"), "F": Rotated("aim"), "G": Rotated("fire"),
    "H": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
}
PANZER_SINGLE = {
    "I": Src("death", 0), "J": Src("death", 1), "K": Src("death", 2), "L": Src("death", 3),
    "M": Src("death", 4), "N": Src("death", 5), "O": Src("death", 5, core=True),
}
PANZER_DERIVED = (
    "B and D: the still view (turn); A = walkL, C = walkR",
    "E and F: the arm back with the projectile (aim) twice (the class asks for E F 8 tics); G = fire (the "
    "throw). The projectile in flight on the fire sheet is removed (it is its own actor, SDPL)",
    "H (pain): H1 = Gemini's pain (death, figure 1); H2-H8 the still view tilted 9 degrees",
    "I-N (death): death's 6 figures; O (the corpse, -1) = figure 6 without the smoke (it has gone out)",
    "boots: the six sheets (182 px) cut the sole at the last row; a dark sole "
    "3 source px tall is added under every figure touching the edge",
    "armbands (both arms in fire) and the back emblem: EMPTY white field (D105); Gemini's «E» "
    "is painted white (fill mode: the red enclosed in the field too)",
    "rotations 6-8: 4-2 mirrored",
)
PANZER_REASK = (
    ("gem_panzer_turn.png, _walkL, _walkR, _aim, _fire, _death", "Same sheets on a taller canvas "
     "(1024x200): the boots' soles and the raised glowing fist are cut by the bottom and top edges; "
     "leave 10 px of background all round"),
    ("gem_panzer_aim.png, gem_panzer_fire.png", "Armbands and the back emblem: red with a PLAIN WHITE "
     "field, no letter, no symbol"),
    ("gem_panzer_fire.png (views 2-3)", "Optional: 3/4 front and profile throwing to the LEFT, as the "
     "turn sheet faces (today mirrored, so the armband changes arm)"),
)

PANZER = EnemySpec(
    name="panzer", sprite="SDPM", folder="panzermensch", target_height=PANZER_HEIGHT, armband="patch",
    field_max=PANZER_FIELD_MAX, symbol="warp", symbol_fields="plain", corpse=("N", "O"),
    sheets=PANZER_SHEETS, rotated=PANZER_ROTATED, single=PANZER_SINGLE,
    derived=PANZER_DERIVED,
    anims=(
        ("walk (See: A 3, A B B C C D D 3)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("throw (Missile: E F 8, G 8)", (("E", 8), ("F", 8), ("G", 8), ("B", 14)), True),
        ("pain (Pain: H 2, H 2)", (("B", 20), ("H", 4), ("B", 14)), True),
        ("die (Death: I-N 8, O)", tuple((c, 8) for c in "IJKLMN") + (("O", 45),), True),
    ),
    reask=PANZER_REASK,
)

PANZER_HEAVY = EnemySpec(
    name="panzer_heavy", sprite="SDPS", folder="panzermensch", target_height=PANZER_HEAVY_HEIGHT,
    armband="patch", field_max=PANZER_FIELD_MAX, shade=PLATE_SHADE,
    symbol="warp", symbol_fields="plain", corpse=("N", "O"),
    sheets=PANZER_SHEETS, rotated=PANZER_ROTATED, single=PANZER_SINGLE,
    derived=PANZER_DERIVED[:-1] + (
        "the Schwer shares the Panzermensch's art (the class is the base one with SDPS for SDPM): the same "
        "Gemini sheets, 12 % bigger (76 rows, D65/D67) and with the plate blackened (x0.55 everything "
        "but reds and whites), like D65's «black plate». No extra stacks or spikes; it dies "
        "face up (today's, face down)",
        "rotations 6-8: 4-2 mirrored",
    ),
    anims=PANZER.anims,
    reask=PANZER_REASK + (
        ("gem_panzer_heavy_turn.png", "Optional: the heavy Panzermensch, same sheets, black armour "
         "plate, larger spikes and two exhaust stacks on the back"),
    ),
)

GENERAL = EnemySpec(
    name="general", sprite="SDGN", folder="general", target_height=GENERAL_HEIGHT, armband="none",
    field_max=GENERAL_FIELD_MAX, symbol="warp", symbol_fields="ring", corpse=("M", "O", "P"),
    sheets={
        "turn": Sheet("gem_general_turn.png", 5, STAND_RIGHT, None),
        "walkL": Sheet("gem_general_walkL.png", 5, STAND_RIGHT, None),
        "walkR": Sheet("gem_general_walkR.png", 5, STAND_RIGHT, None),
        "aim": Sheet("gem_general_aim.png", 5, STAND_RIGHT, None),
        "fire": Sheet("gem_general_fire.png", 5, STAND_RIGHT, None, split_x=GENERAL_FIRE_SPLIT),
        "death": Sheet("gem_general_death.png", 5, (), None, rel_scale=GENERAL_DEATH_SCALE,
                       patch=GENERAL_DEATH_FIELDS),
    },
    rotated={
        "A": Rotated("walkL"), "B": Rotated("turn"), "C": Rotated("walkR"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("fire"),
        "G": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
        "Q": Rotated("turn"), "R": Rotated("aim"),
    },
    single={
        "H": Src("death", 0), "I": Src("death", 1), "J": Src("death", 2), "K": Src("death", 2, tilt=PAIN_TILT),
        "L": Src("death", 3), "M": Src("death", 3), "N": Src("death", 4), "O": Src("death", 4),
        "P": Src("death", 4),
    },
    derived=(
        "B and D: the still view (turn); A = walkL, C = walkR; E = aim (bazooka aiming), F = fire "
        "(muzzle flash and back-blast smoke). In fire four figures touch (flash with smoke, flash with "
        "face, smoke with epaulette): they are cut at fixed columns and the flash or smoke that crosses goes "
        "whole to the figure that fires it (split_x by colour)",
        "G (pain): G1 = Gemini's pain (death, figure 1, the monocle popping out); G2-G8 the still view "
        "tilted 9 degrees",
        "Q (the order, 'Vorwärts!') and R (pointing at them): Gemini did not draw them. Q = the still view, R = aim "
        "(points with the bazooka). See the list",
        "H-P (death, 9 frames in the class, 5 from Gemini): H = pain with the monocle, I = hit (drops the "
        "bazooka, the cap flies off), J = clutches his chest, K = the same tilted 9 degrees (staggers), "
        "L and M = kneeling, N O P = lying with the cape",
        "the death sheet is drawn smaller (the bazooka is 152 px; 210 in aim): scaled x1.39",
        "profile: Gemini drew it facing RIGHT on all six sheets: it is mirrored (Doom's 2-4 face "
        "left). The flag moves to the outer arm in 3 and stays on his arm in 7, as on the Legion",
        "armband (left arm): in turn/walk/aim/fire Gemini drew it red with an empty white "
        "square: left as is. In the death (H-L) it painted a «C» inside: covered with a plain white "
        "field, by hand (4 boxes, Sheet.patch): the band is in shadow and the symbol touches the glove and the "
        "coat, so automatic detection cannot isolate it. US flag and striped cape: untouched",
        "NOTE, Gemini's consistency: in the front and back views the flag is on the "
        "LEFT arm (where the armband goes in 3/4). Not corrected (mirroring the front would move the bazooka "
        "to the other shoulder): see the list",
        "rotations 6-8: 4-2 mirrored",
    ),
    anims=(
        ("walk (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("fire (Missile: E 6 F 12 E 12 F 12)", (("E", 6), ("F", 12), ("E", 12), ("F", 12), ("B", 14)), True),
        ("pain (Pain: G 10)", (("B", 20), ("G", 10), ("B", 14)), True),
        ("the order (Summon: Q 15, R 15)", (("Q", 15), ("R", 15), ("B", 14)), True),
        ("die (Death: H-O 10, P)", tuple((c, 10) for c in "HIJKLMNO") + (("P", 45),), True),
    ),
    reask=(
        ("gem_general_summon.png", "Same General, same style and scale, magenta background, 5 views "
         "(front, 3/4 front, profile facing left, 3/4 back, back): left fist raised high giving an "
         "order, bazooka on the right shoulder; and a second sheet pointing forward with the left arm"),
        ("gem_general_turn.png, _walkL, _walkR, _aim, _fire (views 1 and 5)", "Front and back views: "
         "US flag patch on his RIGHT arm, red armband with a plain white field on his LEFT arm, as in "
         "the 3/4 views"),
        ("gem_general_fire.png", "Same 5 views with more space between figures: the muzzle flash and "
         "the back-blast smoke must not touch the next figure"),
        ("gem_general_death.png", "Same 5 frames at the same scale as the turn sheet (they are ~30 % "
         "smaller), plus a frame falling between kneeling and lying; armband field plain white"),
    ),
)

ENEMIES = {"rifleman": RIFLEMAN, "legion": LEGION, "storm": STORM, "hound": HOUND, "doughboy": DOUGHBOY,
           "panzer": PANZER, "panzer_heavy": PANZER_HEAVY, "general": GENERAL}

# ------------------------------------------- D119: the Legion gunner (SDLG)
# A new set, not a redraw: SD_LegionGunner wears the trooper's SDLT tinted
# brass today (PROVISIONAL-D116); SDLG is the final sprite (design doc
# 2026-10-22_P4_ep2-enemies.md section 4: the trooper's 70 lumps and letters).
# Kept out of ENEMIES (the installed seven, `all`) until the CEO approves it.
GUNNER_HEIGHT = LEGION_HEIGHT   # "the trooper's, ~56 units tall": the two Legion infantrymen stand as tall
SIDES_RIGHT = ("front", "right", "right", "right", "back")   # Gemini's turntable: 3/4, profile, 3/4 back all face right
# fire is turn plus flashes (registered 1 px off): the 3/4 front's flash lies over the profile's thigh,
# the profile's touches the 3/4 back, the back view's (its muzzle on his right, image left) the 3/4 back
GUNNER_FLASH = ((440, 580, 1), (580, 720, 2), (720, 840, 4))
# death_v2: the falling man's boots (frame 3) stand on the corpse's (frame 5); under this line is the corpse
GUNNER_DEATH_PATH = ((540, 507), (628, 507), (634, 499), (722, 497), (726, 440), (1023, 440))
GUNNER_DEATH_PICK = (0, 1, 2, 4, 3)   # left to right by mean column the corpse comes before the sitting man

GUNNER = EnemySpec(
    name="gunner", sprite="SDLG", folder="legion_gunner", target_height=GUNNER_HEIGHT, armband="none",
    sheets={   # one 1024 x 572 canvas and scale for all six: no helmet normalisation
        "turn": Sheet("gem_gunner_turn.png", 5, SIDES_RIGHT, None),
        "strideA": Sheet("gem_gunner_strideA.png", 5, SIDES_RIGHT, None),   # D127: tools/art/walk_stride.py
        "strideC": Sheet("gem_gunner_strideC.png", 5, SIDES_RIGHT, None),
        "aim": Sheet("gem_gunner_aim_v3.png", 5, SIDES_RIGHT, None),        # v3: the front aims at the camera (D119)
        "fire": Sheet("gem_gunner_fire.png", 5, SIDES_RIGHT, None, guide="turn", flash=GUNNER_FLASH),
        "death": Sheet("gem_gunner_death_v2.png", 5, (), None, pick=GUNNER_DEATH_PICK, path=GUNNER_DEATH_PATH),
    },
    rotated={
        "A": Rotated("strideA"), "B": Rotated("turn"), "C": Rotated("strideC"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("fire"),
        "G": Rotated("turn", tilt=PAIN_TILT, override=((1, Src("death", 0)),)),
    },
    single={
        "H": Src("death", 0), "I": Src("death", 1), "J": Src("death", 2), "K": Src("death", 3),
        "L": Src("death", 4),
        "M": Src("death", 0, blood=1), "N": Src("death", 1, blood=1), "O": Src("death", 1, blood=2),
        "P": Src("death", 2, blood=2), "Q": Src("death", 2, blood=3), "R": Src("death", 3, blood=3),
        "S": Src("death", 4, blood=4), "T": Src("death", 4, blood=5), "U": Src("death", 4, blood=6),
    },
    derived=(
        "B and D: the standing view (turn). A and C (D127): Gemini gave no strides (walkL = walkR = turn), so "
        "they come from turn with the legs cut out and moved (tools/art/walk_stride.py): A left leg "
        "forward, C the right; front and back one boot lifts, in profile the legs open (A) and the "
        "near one passes in front (C). walk_stride.py build sets A's and C's torso on B's (the raised "
        "leg moves the legs' axis): build them with it, not with this command",
        "E (aim): gem_gunner_aim_v3, from the front it aims at the camera (D119); in the other views he carries the "
        "machine gun at the hip, as in turn",
        "F (fire): from the front the muzzle flash comes towards the camera, in front of the chest (D119: frontal, not sideways). "
        "The fire sheet is turn with the flashes painted on top and four figures touch through them; they are parted "
        "with turn as the guide (each pixel to the turn figure it grows from) and each flash goes whole to the figure "
        "that fires; where one figure's flash covers its neighbour's body, the neighbour is repainted from turn. "
        "The 3/4 back (F4, F6) has no flash: Gemini did not draw it (the muzzle is hidden)",
        "G2-G8 (pain): the standing view tilted 9 degrees; G1 = Gemini's pain (death, figure 1)",
        "H-L (death): death_v2's 5 figures (hit with the weapon, arms flung open, falls backwards with the weapon "
        "flying, sitting with the weapon on the ground, lying). Figure 3's boots step on the lying man's: they are cut "
        "along a hand-drawn line (Sheet.path), the horizontal boots going to the lying man",
        "M-U (gib, XDeath): no Gemini sheet; the death frames with procedural blood (spurt and pool)",
        "rotations 6-8: 4-2 mirrored; the flag moves to the other shoulder in 2-4 (Gemini drew 3/4, profile and 3/4 "
        "back facing right), as on the Legion trooper",
        "insignia: only the US flag on the shoulder (armband='none': left alone); no swastika",
    ),
    anims=(
        ("walk (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("burst (Missile: E 10, F 3 E 2 x5, pause E 20)",
         (("E", 10),) + (("F", 3), ("E", 2)) * 5 + (("E", 20), ("B", 12)), True),
        ("pain (Pain: G 3, G 3)", (("B", 20), ("G", 6), ("B", 14)), True),
        ("die (Death: H I J K 5, L)", (("H", 5), ("I", 5), ("J", 5), ("K", 5), ("L", 45)), True),
        ("gib (XDeath: M-T 5, U)", tuple((c, 5) for c in "MNOPQRST") + (("U", 45),), True),
    ),
    reask=(
        ("gem_gunner_fire.png (view 4)", "Optional: the 3/4 back view with the muzzle flash visible past his "
         "right hip; and 40 px of background between figures so the flashes do not touch the next figure"),
    ),
)

# Built and previewed, not installed: the CEO sees them first (D119).
PENDING = {"gunner": GUNNER}

# ------------------------------------- D119: the Liberty Colossus (SDLC)
# A new set, not a redraw: SD_LibertyColossus wears the General's SDGN x1.3
# tinted chrome today (PROVISIONAL-D116); SDLC is the final sprite (design doc
# 2026-10-22_P4_ep2-enemies.md section 4: the General's 81 lumps and letters).
# Gemini drew him from a prompt, no reference. aim and fire are read from
# the *_sep sheets tools/art/colossus_gemini.py writes (views 3-4-5 parted by
# hand masks); build him with `python tools/art/colossus_gemini.py all`.
COLOSSUS_HEIGHT = 128   # boss scale: ~120-130 px (design doc 4), torch raised included; the General is 96
COLOSSUS_BIG = 540 / 403    # walk, aim, fire, death are drawn larger than turn (front view 540 rows vs 403)
COLOSSUS_STOMP_SCALE = 0.5 * COLOSSUS_BIG   # the 2-row stomp sheet: half the walk sheet's size (crown-to-foot 263 vs 516)
COLOSSUS_PAIN_TILT = 6.0     # a statue flinches less than a man (PAIN_TILT 9)
COLOSSUS_TOPPLE = 20.0  # degrees: M, the toppling frame pushed further over
COLOSSUS_STAGGER = 8.0  # degrees: K, the crumbling frame leaning
COLOSSUS_DEATH_PICK = (0, 1, 2, 4, 3)   # by mean column the corpse (under) comes before the falling body


def _stomp(pick: tuple[int, ...]) -> Sheet:
    return Sheet("gem_colossus_stomp.png", 10, SIDES_RIGHT, None, rows=2, pick=pick,
                 rel_scale=COLOSSUS_STOMP_SCALE)


COLOSSUS = EnemySpec(
    name="colossus", sprite="SDLC", folder="colossus", target_height=COLOSSUS_HEIGHT, armband="none",
    sheets={   # turn (1024 x 434) sets the scale; the 1024 x 572 sheets x 403/540, the stomp's at half that
        "turn": Sheet("gem_colossus_turn.png", 5, SIDES_RIGHT, None),
        "strideA": Sheet("gem_colossus_strideA.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),   # D127
        "strideC": Sheet("gem_colossus_strideC.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),
        "aim": Sheet("gem_colossus_aim_sep.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),   # = aim_v2
        "fire": Sheet("gem_colossus_fire_sep.png", 5, SIDES_RIGHT, None, rel_scale=COLOSSUS_BIG),
        "stompQ": _stomp((0, 1, 2, 3, 4)),          # top row: the foot raised
        "stompR": _stomp((5, 6, 7, 8, 9)),          # bottom row: the foot down, the dust ring
        "death": Sheet("gem_colossus_death.png", 5, (), None, pick=COLOSSUS_DEATH_PICK, rel_scale=COLOSSUS_BIG),
    },
    rotated={
        "A": Rotated("strideA"), "B": Rotated("turn"),
        "C": Rotated("strideC"), "D": Rotated("turn"),
        "E": Rotated("aim"), "F": Rotated("fire"),
        "G": Rotated("turn", tilt=COLOSSUS_PAIN_TILT, override=((1, Src("death", 0)),)),
        "Q": Rotated("stompQ"), "R": Rotated("stompR"),
    },
    single={
        "H": Src("death", 0), "I": Src("death", 1), "J": Src("death", 2),
        "K": Src("death", 2, tilt=COLOSSUS_STAGGER), "L": Src("death", 3),
        "M": Src("death", 3, tilt=COLOSSUS_TOPPLE), "N": Src("death", 4), "O": Src("death", 4),
        "P": Src("death", 4),
    },
    derived=(
        "B and D: the standing view (turn, rescued from the chat; drawn smaller than the other sheets: those are scaled x403/540). A and C (D127): Gemini gave no strides (walkL = walkR), so they come from walkL with the boots cut out and moved (tools/art/walk_stride.py): one boot lifts under the robe (or the metal leg through the slit in front) and the robe sways; in profile the front boot steps forward (A) and the back one passes (C). walk_stride.py build sets A's and C's torso on B's: build them with it, not with this command",
        "E (aim) and F (fire): in aim and fire view 3 (profile) covers view 4's shoulders (3/4 back) with the arm, the torch "
        "and the flame, and view 4's torch touches view 5's tablet. They are parted by hand "
        "(tools/art/colossus_gemini.py: each pixel to the walkL figure it grows from, and polygons measured at x4 "
        "where the guide does not reach); what the arm covered of view 4 is repainted from walkL (aim) or from the already "
        "parted aim (fire)",
        "E1/F1, front: the torch aims at the camera (D119); F1 = the burst in front of the torch",
        "F: the fire sheet's two rockets in flight (3/4 front and profile) are removed: the rocket is its own "
        "actor (SD_ColossusRocket, the RPG-7's PG-7), like the Panzermensch's projectile. In the profile the "
        "jet of flame stays, closed to a point where the rocket's tail was; so F serves both verbs "
        "(rockets and jet)",
        "G (pain): G1 = the first death frame (it cracks, shards fly); G2-G8 the standing view (turn) "
        "tilted 6 degrees (a statue bends less than a man)",
        "Q and R (stomp): the 2-row stomp sheet, top Q (the foot up), bottom R (the foot down with the "
        "ring of dust and cracks); it is drawn at half size: scaled x2",
        "H-P (death, 9 frames in the class, 5 from Gemini): H = cracks (shards), I = drops the torch, "
        "J = crumbles (the tablet breaks), K = the same tilted 8 degrees, L = falls (in the air, resting on "
        "the feet), M = the same 20 degrees further over, N O P = the body on the ground smoking, with the torch "
        "and the tablet",
        "rotations 6-8: 4-2 mirrored; the flag moves to the other shoulder in 2-4 (Gemini drew 3/4, profile and "
        "3/4 back facing right), as on the Legion trooper",
        "insignia: only the US flag on the shoulder (armband='none': left alone); the tablet, blank "
        "(Gemini put no text on it in any sheet)",
    ),
    anims=(
        ("walk (See: A 3, A B B C C D D 3)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("rockets (Rockets: E 10, F 8 E 6 x3, E 16)",
         (("E", 10), ("F", 8), ("E", 6), ("F", 8), ("E", 6), ("F", 8), ("E", 16), ("B", 12)), True),
        ("fire jet (Flame: E 10, F 3 x5, E 12)", (("E", 10),) + (("F", 3),) * 5 + (("E", 12), ("B", 12)), True),
        ("stomp (Stomp: Q 14, R 6, R 14)", (("Q", 14), ("R", 20), ("B", 14)), True),
        ("pain (Pain: G 10)", (("B", 20), ("G", 10), ("B", 14)), True),
        ("die (Death: H-O 10, P)", tuple((c, 10) for c in "HIJKLMNO") + (("P", 45),), True),
    ),
    reask=(
        ("gem_colossus_aim.png, gem_colossus_fire.png", "Optional: the same 5 views with 80 px of background "
         "between figures (the profile's levelled torch and flame must not reach the next figure), and the "
         "front view's torch held a little closer to the body so the burst is not cut by the left edge"),
        ("gem_colossus_jet.png", "Optional (frame S of the design doc): the 5 views spraying a long jet of "
         "flame from the torch instead of a rocket, so the fire jet and the rocket salvo look different"),
    ),
)
PENDING["colossus"] = COLOSSUS

# ------------------------------- D112/D116/D127: the Consortium (SDCN)
# Episode 3's final boss, a new set: SD_Consortium wears the heavy
# Panzermensch's SDPS x1.75 tinted cobalt today (PROVISIONAL-D116); SDCN is
# its own (design doc 2026-10-22_P4_ep3-final-boss.md section 5: 95 lumps).
# Two halves in one body, so eight rotations of their own, none mirrored:
# tools/art/consortium_gemini.py rewrites Gemini's sheets as eight pictures
# per frame letter (gem_consortium_fix_<L>.png: the halves on the doc's side,
# the arms Gemini swapped or doubled repaired, rotations 6-8 the other side
# with the halves' materials exchanged) and this spec reads them as plain
# one-row sheets. Build it with `python tools/art/consortium_gemini.py all`.
CONSORTIUM_HEIGHT = 140   # boss scale: twice the Panzermensch (68 rows) and "~135-145 px" (design doc 5)
CONSORTIUM_SWAY = 2.0     # degrees: the walk's rock from foot to foot (Gemini's strides barely differ)
CONSORTIUM_PAIN_TILT = 5.0    # a boss barely flinches (PAIN_TILT 9)
CONSORTIUM_COLLAPSE = 10.0    # degrees: M, the collapsing frame sunk further over
CONSORTIUM_FIELD_MAX = 40     # source px: its armband field (~12 x 24 at the rooted sheet's scale)
CONSORTIUM_FAR = (6, 7, 8)    # rotations drawn from the fixed sheet's views 5-7 (never a mirror)


def _cn_sheet(name: str, count: int = 8) -> Sheet:
    return Sheet(f"gem_consortium_fix_{name}.png", count, (), None)


def _cn_eight(key: str, tilt: float = 0.0) -> Rotated:
    """Eight rotations from a fixed sheet: views 0-4 rotations 1-5, views 5-7 rotations 6-8
    (they face right: the tilt mirrored, as the engine's mirror would)."""
    return Rotated(key, tilt=tilt, override=tuple((r, Src(key, r - 1, tilt=-tilt)) for r in CONSORTIUM_FAR))


CONSORTIUM = EnemySpec(
    name="consortium", sprite="SDCN", folder="consortium", target_height=CONSORTIUM_HEIGHT, armband="none",
    ref_sheet="Q", symbol="warp", symbol_fields="white", field_max=CONSORTIUM_FIELD_MAX,
    palette_version=3,   # D128: palette v3's reich_greygreen for the Reich half's skin (v2 made it concrete grey)
    sheets={k: _cn_sheet(k) for k in "QRABCEFGHS"} | {"death": _cn_sheet("death", 5)},
    rotated={
        "Q": _cn_eight("Q"), "R": _cn_eight("R"),
        "A": _cn_eight("A", CONSORTIUM_SWAY), "B": _cn_eight("B"), "C": _cn_eight("C", -CONSORTIUM_SWAY),
        "D": _cn_eight("B"),
        "E": _cn_eight("E"), "F": _cn_eight("F"), "G": _cn_eight("G"), "H": _cn_eight("H", CONSORTIUM_PAIN_TILT),
        "S": _cn_eight("S"),
    },
    single={
        "I": Src("death", 0), "J": Src("death", 1), "K": Src("death", 2), "L": Src("death", 3),
        "M": Src("death", 3, tilt=CONSORTIUM_COLLAPSE), "N": Src("death", 4), "O": Src("death", 4, core=True),
    },
    derived=(
        "Sides (D112, doc §2): the Reich half on ITS left, on the viewer's RIGHT when facing us. Gemini drew "
        "every sheet the wrong way round: each view is mirrored (the rockets leave 32 units to its left, the orbs to its "
        "right, as in the actor)",
        "Rotations 6-8 (its right side, the Legion's): Gemini did not draw that side. They are the 3/4 back, the profile "
        "and the 3/4 front NOT mirrored, with the two halves' materials swapped by hand in code "
        "(grey-green <-> pink skin by luminance, SS helmet <-> M1 on the helmets' row, the rocket launcher "
        "in chrome, the armband as a chrome bracer). Never a mirror: the armband does not change arm",
        "Q and R (phase 1, rooted): the rooted sheet; R = Q with the core lit (breathing). B and D (phase 2, standing): turn",
        "A and C (walk, phase 2): walk top (A) and bottom (C). Fixed by hand: in A front, 3/4 back and back "
        "Gemini put the cable skirt where a leg goes: C's legs (same sheet) under the belt. The 3/4 "
        "front and profile ones drag torn-out cables (the doc: \"stumps dragging\"). It sways ±2 degrees",
        "E (orb warning): aim top. Fixed: 3/4 front, the Reich arm held a glowing chrome projector "
        "-> the rocket launcher (olive, dark muzzle); 3/4 back, a third arm hanging and, from the back, the "
        "raised arm also hanging: removed",
        "F (rocket warning): aim bottom. Fixed: front, the rocket launcher seen muzzle-on was raised by the "
        "Legion arm and another hung from the Reich one: the body is mirrored and the launcher stays, olive, on the Reich "
        "arm; the Legion arm hangs with its projector (transplanted from rooted, to scale). Profile: a projector "
        "pointing backwards (removed), the pink fist on the launcher (grey-green), the launcher hanging "
        "(removed; the hip it covered, filled with the cable knot itself: Fooocus, D127, did not work). 3/4 back and back: the "
        "Legion arm raised backwards -> hanging (from E), the repeated launcher hanging: removed",
        "G (shot, both phases): fire_v2 with the legs swapped for the cable knot and fire's smoke (same "
        "scale; its hanging arms removed, and the gap filled with the knot itself). Fixed: front, each weapon "
        "was on the other half's arm (orb in the Reich fist, rocket from the Legion one): the body is mirrored and "
        "the arms are not, with the skin repainted; 3/4 front, the orb came out of the launcher's muzzle and the rocket out of "
        "the Legion hand: orange flash on the launcher, blue discharge from a chrome cannon; 3/4 back, "
        "orb on the Reich arm (flash) and a rocket fired backwards (removed). The rockets in flight are removed "
        "(they are their own actor)",
        "H (pain): the discarded fire sheet (both mouths screaming, arms down) without the rockets or the flashes, "
        "tilted 5 degrees",
        "S (breach): breach; the cable column squashed to the height of rooted's skirt (otherwise the boss grew "
        "25 % in the breach's first frame)",
        "I-O (death): death's 5, mirrored. I = the core cracks, J = both heads scream, K = the halves "
        "break apart, L = collapses burning, M = the same sunk 10 degrees, N and O = the two helmets among the ashes",
        "Armband: Gemini's white field with armband_symbol's symbol (option 1, D108/D114), after the "
        "mirror; rotations 6-8 have no armband (it is the Legion side). The US flag is flipped "
        "by the mirror (on the right shoulder, as the US Army wears it)",
    ),
    anims=(
        ("rooted (Spawn/See phase 1: Q R 6)", (("Q", 6), ("R", 6)), True),
        ("walk, phase 2 (Walk: A B B C C D D 3)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("orbs (Orbs: E 12, G 6, E 10, G 6, E 16)", (("E", 12), ("G", 6), ("E", 10), ("G", 6), ("E", 16), ("Q", 12)), True),
        ("rockets (Rockets: F 12, G 8 F 6 x3, F 16)",
         (("F", 12), ("G", 8), ("F", 6), ("G", 8), ("F", 6), ("G", 8), ("F", 16), ("Q", 12)), True),
        ("flame (Flame: E 10, G 3 x5, E 12)", (("E", 10),) + (("G", 3),) * 5 + (("E", 12), ("Q", 12)), True),
        ("breach (Breach: S 10 S 10, E 20, F 15, G 10)", (("Q", 12), ("S", 20), ("E", 20), ("F", 15), ("G", 10), ("B", 20)), True),
        ("pain (Pain: H 3 H 3)", (("Q", 20), ("H", 6), ("Q", 14)), True),
        ("die (Death: I J K L M N 10, O 30)", tuple((c, 10) for c in "IJKLMN") + (("O", 45),), True),
    ),
)
PENDING["consortium"] = CONSORTIUM


# ------------------------------------------------------------- palette
def palette_rgb(version: int = 2) -> np.ndarray:
    """Palette `version` as an (n, 3) array. Every set is v2 but the
    Consortium's (v3 since D128: its Reich half's grey-green skin)."""
    return np.array(palette.colours(version), dtype=np.int32)


def snap(rgb: np.ndarray, pal: np.ndarray) -> np.ndarray:
    """(..., 3) colours -> palette indices (weighted RGB nearest)."""
    flat = rgb.reshape(-1, 3).astype(np.int32)
    w = np.array([3, 4, 2], np.int32)
    out = np.empty(flat.shape[0], np.int32)
    for s in range(0, flat.shape[0], 32768):
        d = (((flat[s:s + 32768, None, :] - pal[None]) ** 2) * w).sum(axis=2)
        out[s:s + 32768] = d.argmin(axis=1)
    return out.reshape(rgb.shape[:-1])


# ------------------------------------------------------------ 1-2. key
def estimate_background(rgb: np.ndarray) -> np.ndarray:
    """The commonest border colour (binned), refined to the mean of the
    border pixels near it. Figures may touch the border; they are a minority."""
    b = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.int32)
    q = b // BG_QUANT
    u, c = np.unique(q, axis=0, return_counts=True)
    mode = u[c.argmax()] * BG_QUANT + BG_QUANT // 2
    near = np.abs(b - mode).max(axis=1) <= 2 * BG_QUANT
    return b[near].mean(axis=0)


def neighbours8(mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(mask)
    h, w = mask.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy or dx:
                out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] |= \
                    mask[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def key_background(rgb: np.ndarray, bg=None, tol: float = KEY_TOL,
                   fringe: float = FRINGE_TOL, passes: int = FRINGE_PASSES) -> np.ndarray:
    """Foreground mask: far from the background colour, minus halo rims."""
    bg = estimate_background(rgb) if bg is None else np.asarray(bg, np.float64)
    dist = np.sqrt(((rgb.astype(np.float64) - bg) ** 2).sum(axis=-1))
    fg = dist > tol
    for _ in range(passes):
        rim = fg & neighbours8(~fg) & (dist < fringe)
        if not rim.any():
            break
        fg &= ~rim
    return fg


# ------------------------------------------------------- 3. components
def label(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """8-connected labels (0 = background) by row runs and union-find."""
    h, w = mask.shape
    parent: list[int] = [0]

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    runs = []          # (y, x0, x1, label)
    prev: list[tuple[int, int, int]] = []
    for y in range(h):
        row = mask[y].astype(np.int8)
        d = np.diff(np.concatenate([[0], row, [0]]))
        starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
        cur = []
        for x0, x1 in zip(starts, ends):
            lab = 0
            for px0, px1, pl in prev:
                if px0 <= x1 and px1 >= x0:        # 8-connected: [x0-1, x1] overlaps [px0, px1-1]
                    if lab == 0:
                        lab = find(pl)
                    else:
                        a, b = find(lab), find(pl)
                        if a != b:
                            parent[max(a, b)] = min(a, b)
                            lab = min(a, b)
            if lab == 0:
                lab = len(parent)
                parent.append(lab)
            cur.append((int(x0), int(x1), lab))
            runs.append((y, int(x0), int(x1), lab))
        prev = cur
    out = np.zeros((h, w), np.int32)
    roots: dict[int, int] = {}
    for y, x0, x1, lab in runs:
        r = find(lab)
        out[y, x0:x1] = roots.setdefault(r, len(roots) + 1)
    return out, len(roots)


def _dilate(mask: np.ndarray, r: int) -> np.ndarray:
    for _ in range(r):
        mask = mask | neighbours8(mask)
    return mask


def bridge_mask(rgb: np.ndarray, kind: str) -> np.ndarray:
    """The colour of what bridges two figures: `fire` a muzzle flash (bright
    yellow to white-hot, not the gold of an epaulette), `smoke` a back-blast
    cloud (light neutral grey)."""
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lo, hi = a.min(axis=-1), a.max(axis=-1)
    if kind == "fire":
        return (lo > GLOW_WHITE) | ((r > BRIDGE_FIRE_R) & (g > BRIDGE_FIRE_G * r) & (b < g))
    if kind == "smoke":
        return (hi - lo < BRIDGE_SMOKE_SPREAD) & (lo > BRIDGE_SMOKE_MIN) & (hi < BRIDGE_SMOKE_MAX)
    return np.zeros(a.shape[:2], bool)


def _fixed_cut(cols: np.ndarray, at: tuple) -> tuple | None:
    """The first (x, kind) of `at` inside the columns `cols`, away from their ends."""
    c0, c1 = cols[0], cols[-1]
    m = int((c1 - c0) * SPLIT_MARGIN)
    return next(((x, k) for x, k in at if c0 + m < x < c1 - m), None)


def split_merged(mask: np.ndarray, at: tuple = (), rgb: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Cut a component holding two figures at its emptiest column (away from
    its ends), or at the first sheet column of `at` ((x, kind) pairs) inside
    it, away from its ends as well: a flash or a smoke cloud bridging two figures puts the emptiest
    column in the wrong place. With a `kind` (see bridge_mask) every piece
    of that colour reaching left of the cut goes whole to the LEFT figure
    (the profile's flash in front of the next figure's face); a kind ending
    in `>` sends its pieces reaching right of the cut to the RIGHT figure;
    `|` joins several kinds. After such a
    fixed cut, crumbs under ERASE_KEEP of a side go."""
    cols = np.flatnonzero(mask.any(axis=0))
    c0, c1 = cols[0], cols[-1]
    m = int((c1 - c0) * SPLIT_MARGIN)
    fixed = _fixed_cut(cols, at)
    if fixed:
        cut, kind = fixed
    else:
        counts = mask[:, c0 + m:c1 - m + 1].sum(axis=0)
        cut, kind = c0 + m + int(counts.argmin()), ""
    left = mask.copy()
    left[:, cut:] = False
    for k in (kind.split("|") if kind and rgb is not None else ()):
        lab, n = label(mask & bridge_mask(rgb, k.rstrip(">")))
        if k.endswith(">"):      # every piece reaching right of the cut goes to the RIGHT figure
            reach = np.unique(lab[:, cut:])
            left &= ~np.isin(lab, reach[reach > 0])
        else:
            reach = np.unique(lab[:, :cut])
            left |= np.isin(lab, reach[reach > 0])
    right = mask & ~left
    if fixed:
        left, right = _drop_crumbs(left), _drop_crumbs(right)
    return left, right


def _drop_crumbs(mask: np.ndarray) -> np.ndarray:
    lab, n = label(mask)
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    keep = np.flatnonzero(areas >= ERASE_KEEP * mask.sum())
    return np.isin(lab, keep[keep > 0])


def path_below(shape: tuple[int, int], path: tuple) -> np.ndarray:
    """The pixels on or under a polyline ((x, y), ...) drawn left to right,
    within its first and last columns (nothing outside them is under it)."""
    h, w = shape
    xs = np.array([p[0] for p in path], np.float64)
    ys = np.array([p[1] for p in path], np.float64)
    cols = np.arange(w)
    cut = np.interp(cols, xs, ys)
    inside = (cols >= xs[0]) & (cols <= xs[-1])
    return (np.arange(h)[:, None] >= cut[None, :]) & inside[None, :]


def figures(fg: np.ndarray, count: int, split_x: tuple = (), rgb: np.ndarray | None = None,
            path: tuple = ()) -> list[np.ndarray]:
    """The `count` figures of a sheet, left to right, each a bool mask with its satellites.
    With a `path` (Sheet.path), a merged pair is cut along it instead of at a
    column: what lies under the path is the lower figure (the gunner's corpse
    under the falling man's boots)."""
    lab, n = label(fg)
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    areas[0] = 0
    comps = [lab == i for i in range(1, n + 1) if areas[i] >= MIN_PIECE]
    comps.sort(key=lambda c: -int(c.sum()))
    if not comps:
        raise ValueError("no figure on the sheet")
    big = [c for c in comps if c.sum() >= FIGURE_FRAC * comps[0].sum()]
    rest = [c for c in comps if c.sum() < FIGURE_FRAC * comps[0].sum()]
    below = path_below(fg.shape, path) if path else None
    while len(big) < count:            # two figures merged (touching flashes)
        if below is not None:          # the piece the path crosses: the most on its lesser side
            k = max(range(len(big)), key=lambda i: min(int((big[i] & below).sum()), int((big[i] & ~below).sum())))
            m = big.pop(k)
            if not (m & below).any() or not (m & ~below).any():
                raise ValueError("the split path crosses no merged figure")
            big += [m & ~below, m & below]
            continue
        spans = [np.flatnonzero(c.any(axis=0)) for c in big]
        # a piece a fixed cut applies to goes first (its emptiest column may be a flash), then the widest
        widest = max(range(len(big)), key=lambda i: (_fixed_cut(spans[i], split_x) is not None, np.ptp(spans[i])))
        a, b = split_merged(big.pop(widest), split_x, rgb)
        big += [a, b]
    big.sort(key=lambda c: -int(c.sum()))
    rest += big[count:]
    big = big[:count]
    pending = list(rest)
    changed = True
    while changed and pending:         # satellites join the figure they are near (chains allowed)
        changed = False
        grown = [_dilate(f, ATTACH_PX) for f in big]
        left = []
        for piece in pending:
            hits = [i for i, g in enumerate(grown) if (g & piece).any()]
            if hits:
                i = max(hits, key=lambda k: int((grown[k] & piece).sum()))
                big[i] = big[i] | piece
                changed = True
            else:
                left.append(piece)
        pending = left
    big.sort(key=lambda c: float(np.flatnonzero(c.any(axis=0)).mean()))
    return big


def shifted(a: np.ndarray, dy: int, dx: int, fill=0) -> np.ndarray:
    """`a` moved dy rows down and dx columns right, `fill` where nothing comes in."""
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    src_y, dst_y = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    src_x, dst_x = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[dst_y, dst_x] = a[src_y, src_x]
    return out


def align_guide(rgb: np.ndarray, guide_rgb: np.ndarray, mask: np.ndarray, r: int = ALIGN_R) -> tuple[int, int]:
    """(dy, dx) that moves the guide sheet onto this one: the least mean
    colour difference over `mask` (Gemini redraws a sheet a pixel off)."""
    a = rgb.astype(np.int32)
    best = None
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.abs(a - shifted(guide_rgb, dy, dx).astype(np.int32))[mask].mean())
            if best is None or d < best[0]:
                best = (d, dy, dx)
    return best[1], best[2]


def new_paint(rgb: np.ndarray, guide_rgb: np.ndarray, fg: np.ndarray, tol: float = NEW_TOL) -> np.ndarray:
    """Foreground pixels whose colour no guide pixel within 1 px has: what
    Gemini added (a flash), not a contour a sub-pixel off."""
    a = rgb.astype(np.int32)
    best = np.full(fg.shape, 10 ** 6, np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            g = shifted(guide_rgb, dy, dx).astype(np.int32)
            best = np.minimum(best, np.abs(a - g).max(axis=-1))
    return fg & (best > tol)


def guided_figures(fg: np.ndarray, rgb: np.ndarray, guide_rgb: np.ndarray, guide_masks: list[np.ndarray],
                   flash: tuple = ()) -> tuple[list[np.ndarray], list[np.ndarray], np.ndarray]:
    """The figures of a sheet Gemini painted over another of the same set
    (D119: the gunner's fire sheet is his turn sheet plus muzzle flashes,
    which bridge four figures whose extents overlap, so no column cuts
    them). Every pixel goes to the guide figure it grows from (8-connected,
    through the foreground); a flash (new paint holding FLASH_MIN flash
    pixels) centred in the columns of a `flash` entry goes whole to its
    figure. Returns (masks, heals, guide_rgb registered): `heals[k]` are the
    pixels of guide figure k that a neighbour's flash covers, repainted
    from the guide so the body has no hole."""
    union = np.zeros_like(fg)
    for g in guide_masks:
        union |= g
    dy, dx = align_guide(rgb, guide_rgb, union & fg)
    g_rgb = shifted(guide_rgb, dy, dx)
    gm = [shifted(g, dy, dx, False) for g in guide_masks]
    own = np.full(fg.shape, -1, np.int32)
    for k, g in enumerate(gm):
        own[g & fg & (own < 0)] = k
    free = fg & (own < 0)
    while free.any():
        grew = False
        for k in range(len(gm)):
            add = neighbours8(own == k) & free
            if add.any():
                own[add] = k
                free &= ~add
                grew = True
        if not grew:
            break
    lab, n = label(new_paint(rgb, g_rgb, fg))
    fire = bridge_mask(rgb, "fire")
    lit = [np.zeros_like(fg) for _ in gm]      # round each figure's flash: its glow on a neighbour
    for i in range(1, n + 1):
        piece = lab == i
        if int((piece & fire).sum()) < FLASH_MIN:
            continue
        cx = float(np.nonzero(piece)[1].mean())
        for x0, x1, view in flash:
            if x0 <= cx < x1:
                own[piece] = view
                lit[view] |= _dilate(piece, FLASH_GLOW)
    masks = [own == k for k in range(len(gm))]
    glow = [np.zeros_like(fg) if not any(l.any() for j, l in enumerate(lit) if j != k) else
            np.logical_or.reduce([l for j, l in enumerate(lit) if j != k]) for k in range(len(gm))]
    heals = [g & fg & (~m | gl) for g, m, gl in zip(gm, masks, glow)]
    rl, rn = label(fg & (own < 0))       # what no guide figure reaches (a flying case): a satellite
    for i in range(1, rn + 1):
        piece = rl == i
        if piece.sum() < MIN_PIECE:
            continue
        hits = [k for k, m in enumerate(masks) if (_dilate(m, ATTACH_PX) & piece).any()]
        if hits:
            masks[hits[0]] |= piece
    return masks, heals, g_rgb


def shadow_mask(rgb: np.ndarray) -> np.ndarray:
    """Gemini's painted ground shadow: the background's magenta hue, darker
    (green far under red and blue, red and blue alike, not black)."""
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lo, hi = np.minimum(r, b), np.maximum(r, b)
    return (g < SHADOW_G * lo) & (hi - lo < SHADOW_RB * hi) & (lo > SHADOW_MIN)


def grid_order(masks: list[np.ndarray], rows: int, height: int) -> list[np.ndarray]:
    """Figures of a `rows`-row grid sheet, row by row, left to right in each
    row (the row is the band of the sheet holding the figure's centre)."""
    def key(m):
        ys, xs = np.nonzero(m)
        return min(rows - 1, int(ys.mean() * rows / height)), float(xs.mean())
    return sorted(masks, key=key)


def largest(mask: np.ndarray) -> np.ndarray:
    """The biggest 8-connected piece of a mask."""
    lab, n = label(mask)
    if n <= 1:
        return mask
    return lab == 1 + int(np.argmax(np.bincount(lab.ravel(), minlength=n + 1)[1:]))


def erase_glow(rgb: np.ndarray, mask: np.ndarray, box: tuple[float, float, float, float],
               kind: str = "glow") -> np.ndarray:
    """A glow Gemini painted where it does not belong (a duplicated muzzle
    glow, one on the back of the head; `fire`: an ember in flight stuck to
    the fist): in `box` (fractions x0, y0, x1, y1 of the figure's box) its
    pixels (`glow`: blue and white-hot; `fire`: yellow, orange and
    white-hot; `all`: everything, the ember's halo ring) leave the mask, then pieces under ERASE_KEEP of the figure
    go (the sparks or the ember's rim left floating)."""
    h, w = mask.shape
    x0, y0, x1, y1 = (int(round(f * n)) for f, n in zip(box, (w, h, w, h)))
    a = rgb[y0:y1, x0:x1].astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hot = a.min(axis=-1) > GLOW_WHITE
    if kind == "all":
        glow = np.ones_like(hot)
    elif kind == "fire":
        glow = hot | ((r > FIRE_R) & (g > FIRE_G * r) & (b < g + FIRE_B))
    else:
        glow = hot | (b - r > GLOW_BLUE)
    mask = mask.copy()
    mask[y0:y1, x0:x1] &= ~glow
    lab, n = label(mask)
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    keep = np.flatnonzero(areas >= ERASE_KEEP * mask.sum())
    return np.isin(lab, keep[keep > 0])


def darken(rgb: np.ndarray, mask: np.ndarray, k: float) -> np.ndarray:
    """Every colour of the figure but its reds, whites and glows x k (a black plate)."""
    if k == 1.0:
        return rgb
    keep = red_mask(rgb, MARKER_RED_MIN) | white_mask(rgb) | (rgb.max(axis=-1) > SHADE_KEEP)
    out = rgb.astype(np.float64)
    out[mask & ~keep] *= k
    return np.clip(out, 0, 255).astype(np.uint8)


def crop(rgb: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.flatnonzero(mask.any(axis=1)), np.flatnonzero(mask.any(axis=0))
    sl = (slice(ys[0], ys[-1] + 1), slice(xs[0], xs[-1] + 1))
    return rgb[sl].copy(), mask[sl].copy()


# ------------------------------------------------------- 4. the armband
def red_mask(rgb: np.ndarray, rmin: int = RED_MIN) -> np.ndarray:
    r, g, b = (rgb[..., k].astype(np.int32) for k in range(3))
    return (r > rmin) & (g < RED_GB_MAX) & (b < RED_GB_MAX) & (r > 2 * g) & (r > 2 * b)


def white_mask(rgb: np.ndarray, wmin: int = WHITE_MIN) -> np.ndarray:
    a = rgb.astype(np.int32)
    return (a.min(axis=-1) > wmin) & (a.max(axis=-1) - a.min(axis=-1) < WHITE_SPREAD)


def armband_fields(rgb: np.ndarray, mask: np.ndarray, loose: bool = False) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (y0, x0, y1, x1) of the armband's white fields: white
    pixels grouped within FIELD_GAP px (a ring broken by the symbol is one
    field), kept when the group lies within ARMBAND_NEAR px of the red.
    `loose`: a beige field on a band in shade counts (BOX_WHITE_MIN, MARKER_RED_MIN)."""
    wmin, rmin = (BOX_WHITE_MIN, MARKER_RED_MIN) if loose else (WHITE_MIN, RED_MIN)
    white = mask & white_mask(rgb, wmin)
    near_red = _dilate(red_mask(rgb, rmin) & mask, ARMBAND_NEAR)
    lab, n = label(_dilate(white, FIELD_GAP))
    out = []
    for i in range(1, n + 1):
        blob = (lab == i) & white
        if blob.sum() >= MIN_FIELD and (blob & near_red).any():
            ys, xs = np.flatnonzero(blob.any(axis=1)), np.flatnonzero(blob.any(axis=0))
            out.append((int(ys[0]), int(xs[0]), int(ys[-1]) + 1, int(xs[-1]) + 1))
    return out


def field_purity(rgb: np.ndarray, mask: np.ndarray, box: tuple[int, int, int, int]) -> float:
    """Fraction of the figure's pixels in `box` that are the field's white or
    the band's red (loose thresholds): a field ON the armband is nearly all
    white and red; a pale highlight touching the band (the hybrid's cannon
    metal, sparks) is mostly something else."""
    y0, x0, y1, x1 = box
    sub, m = rgb[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    if not m.any():
        return 0.0
    ok = (white_mask(sub, BOX_WHITE_MIN) | red_mask(sub, MARKER_RED_MIN)) & m
    return float(ok.sum()) / float(m.sum())


def blue_frac(rgb: np.ndarray, mask: np.ndarray) -> float:
    """Fraction of the figure's pixels that are blue (a US flag's canton)."""
    a = rgb.astype(np.int32)
    blue = mask & (a[..., 2] > a[..., 0] + GLOW_BLUE) & (a[..., 2] > a[..., 1])
    return float(blue.sum()) / max(1, int(mask.sum()))


def light_mask(rgb: np.ndarray) -> np.ndarray:
    """A letter or field painted light on the band: pale, white to pink, in
    shade too; not the yellowish beige of a coat or a cap (PATCH_YELLOW)."""
    a = rgb.astype(np.int32)
    lo, hi = a.min(axis=-1), a.max(axis=-1)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (lo > PATCH_LIGHT) & (hi - lo < PATCH_SPREAD) & (r >= g - PATCH_TINT) & (b >= g - PATCH_YELLOW)


def patch_armband(rgb: np.ndarray, mask: np.ndarray, field_max: int) -> tuple[np.ndarray, int]:
    """Mode `patch`: a light mark ON the red band (the Panzermensch's white
    «E», a white field with or without a symbol) becomes one plain white
    patch, its whole box painted PATCH_RGB: pale pixels grouped within
    FIELD_GAP, near the band's red (dark red in shade counts), no bigger
    than `field_max`, the box mostly light or red (PATCH_PURITY), the ring of
    PATCH_RING px round it mostly red (PATCH_RING_RED: it sits ON the band;
    a glove or a cape's stripe does not) and no blue near it (a US flag).
    A mark the grouping cannot isolate is named by hand (Sheet.patch)."""
    rgb = rgb.copy()
    light = light_mask(rgb) & mask
    red = red_mask(rgb, MARKER_RED_MIN) & mask
    near_red = _dilate(red, ARMBAND_NEAR)
    lab, n = label(_dilate(light, FIELD_GAP))
    boxes = []
    for i in range(1, n + 1):
        blob = (lab == i) & light
        if blob.sum() < MIN_FIELD or not (blob & near_red).any():
            continue
        ys, xs = np.nonzero(blob)
        boxes.append((ys.min(), xs.min(), ys.max() + 1, xs.max() + 1))
    painted = 0
    for y0, x0, y1, x1 in boxes:
        if max(y1 - y0, x1 - x0) > field_max or min(y1 - y0, x1 - x0) < PATCH_MIN_SIDE:
            continue
        m = mask[y0:y1, x0:x1]
        if float(((light | red)[y0:y1, x0:x1] & m).sum()) / float(m.sum()) < PATCH_PURITY:
            continue
        ry0, rx0 = max(0, y0 - PATCH_RING), max(0, x0 - PATCH_RING)
        ry1, rx1 = y1 + PATCH_RING, x1 + PATCH_RING
        ring = mask[ry0:ry1, rx0:rx1].copy()
        ring[y0 - ry0:y1 - ry0, x0 - rx0:x1 - rx0] = False
        if not ring.any() or float((red[ry0:ry1, rx0:rx1] & ring).sum()) / float(ring.sum()) < PATCH_RING_RED:
            continue                     # not ON the band: a glove, a stripe of the cape
        g = max(y1 - y0, x1 - x0)          # the canton may lie a field's width away
        gy0, gx0 = max(0, y0 - g), max(0, x0 - g)
        if blue_frac(rgb[gy0:y1 + g, gx0:x1 + g], mask[gy0:y1 + g, gx0:x1 + g]) >= PATCH_FLAG_BLUE:
            continue                     # a US flag (its canton)
        sub = rgb[y0:y1, x0:x1]
        painted += int((m & ~(sub == PATCH_RGB).all(axis=-1)).sum())
        sub[m] = PATCH_RGB
    return rgb, painted


def blank_armband(rgb: np.ndarray, mask: np.ndarray, mode: str = "blank",
                  field_max: int | None = None) -> tuple[np.ndarray, int]:
    """Paint white whatever lies INSIDE an armband's white field (a symbol
    Gemini drew): in the field's box, a pixel with white on both sides in
    its row AND in its column (a broken ring still encloses). Mode `fill`:
    as `blank`, and a red pixel enclosed both ways goes white too (a white
    ring on the red, the General's, becomes a plain field). Mode `box`:
    the field's whole box (within the figure) goes white, so a white symbol
    on the red (a cross) becomes a plain white patch; a field bigger than
    FIELD_BOX_MAX is not an armband and is left. Mode `none`: nothing.
    In every mode a field bigger than `field_max` (a coat, a cape's stripe)
    or with a blue canton (a US flag, FLAG_BLUE) is left.
    Returns (rgb, pixels painted)."""
    rgb = rgb.copy()
    painted = 0
    if mode == "none":
        return rgb, 0
    if mode == "patch":
        return patch_armband(rgb, mask, field_max or FIELD_BOX_MAX)
    for y0, x0, y1, x1 in armband_fields(rgb, mask, loose=mode == "box"):
        if field_max is not None and max(y1 - y0, x1 - x0) > field_max:
            continue
        if blue_frac(rgb[y0:y1, x0:x1], mask[y0:y1, x0:x1]) >= FLAG_BLUE:
            continue
        box = rgb[y0:y1, x0:x1]
        white = white_mask(box, BOX_WHITE_MIN if mode == "box" else WHITE_MIN)
        if mode == "box":
            if max(y1 - y0, x1 - x0) > FIELD_BOX_MAX \
                    or field_purity(rgb, mask, (y0, x0, y1, x1)) < BOX_PURITY:
                continue
            hole = ~white & mask[y0:y1, x0:x1]
            if hole.any():
                box[hole] = box[white].mean(axis=0).astype(rgb.dtype)
                painted += int(hole.sum())
            continue
        h, w = white.shape
        cols, rows = np.arange(w)[None, :], np.arange(h)[:, None]
        first_x = np.where(white.any(axis=1, keepdims=True), white.argmax(axis=1)[:, None], w)
        last_x = np.where(white.any(axis=1, keepdims=True), w - 1 - white[:, ::-1].argmax(axis=1)[:, None], -1)
        first_y = np.where(white.any(axis=0, keepdims=True), white.argmax(axis=0)[None, :], h)
        last_y = np.where(white.any(axis=0, keepdims=True), h - 1 - white[::-1].argmax(axis=0)[None, :], -1)
        in_row, in_col = (cols > first_x) & (cols < last_x), (rows > first_y) & (rows < last_y)
        hole = (in_row | in_col) & ~white & ~red_mask(box) & mask[y0:y1, x0:x1]
        if mode == "fill":
            hole |= in_row & in_col & ~white & mask[y0:y1, x0:x1]
        if hole.any():
            box[hole] = box[white].mean(axis=0).astype(rgb.dtype)
            painted += int(hole.sum())
    return rgb, painted


# ------------------------------------------------------ 5. orientation
def body_axis(mask: np.ndarray) -> float:
    """The median column of the bottom LEGS_FRAC of the figure: its legs' axis."""
    ys = np.flatnonzero(mask.any(axis=1))
    y0 = ys[-1] - max(1, int((ys[-1] - ys[0] + 1) * LEGS_FRAC))
    sub = mask[y0:ys[-1] + 1]
    return float(np.median(np.nonzero(sub)[1]))


def detect_facing(mask: np.ndarray) -> str | None:
    """'left' or 'right': the side the art reaches further on from the legs'
    axis (a levelled rifle points where the figure faces); None if neither."""
    xs = np.flatnonzero(mask.any(axis=0))
    ax = body_axis(mask)
    left, right = ax - xs[0], xs[-1] - ax
    if left > FACING_RATIO * right:
        return "left"
    if right > FACING_RATIO * left:
        return "right"
    return None


def facing_of(sheet: Sheet, view: int, mask: np.ndarray) -> str:
    want = sheet.facing[view] if view < len(sheet.facing) else "front"
    if want != "auto":
        return want
    got = detect_facing(mask)
    if got is None:
        raise ValueError(f"{sheet.file} view {view + 1}: facing is ambiguous, name it in the spec")
    return got


def marker_side(rgb: np.ndarray, mask: np.ndarray) -> str | None:
    """'left' or 'right': the side of the legs' axis the armband's red lies on
    (a dark red counts: MARKER_RED_MIN); None when too little red or too
    near the axis to tell."""
    a = rgb.astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = mask & (r > MARKER_RED_MIN) & (r > 2 * g) & (r > 2 * b)
    if red.sum() < MARKER_MIN_PX:
        return None
    off = float(np.nonzero(red)[1].mean()) - body_axis(mask)
    if abs(off) < MARKER_OFFSET:
        return None
    return "right" if off > 0 else "left"


def add_sole(rgb: np.ndarray, mask: np.ndarray, rows: int) -> tuple[np.ndarray, np.ndarray]:
    """`rows` rows of dark sole under the figure's last row (its footprint
    repeated): the boots a sheet's bottom edge cut off."""
    if rows <= 0:
        return rgb, mask
    last = mask[-1]
    rgb = np.concatenate([rgb, np.zeros((rows,) + rgb.shape[1:], rgb.dtype)])
    mask = np.concatenate([mask, np.repeat(last[None], rows, axis=0)])
    rgb[-rows:][mask[-rows:]] = SOLE_RGB
    return rgb, mask


def normalise(rgb: np.ndarray, mask: np.ndarray, facing: str) -> tuple[np.ndarray, np.ndarray, bool]:
    """A figure facing right is mirrored to face left (rotations 2-4)."""
    if facing == "right":
        return rgb[:, ::-1].copy(), mask[:, ::-1].copy(), True
    return rgb, mask, False


# -------------------------------------------------------------- 6. scale
def helmet_width(mask: np.ndarray, band: int) -> int:
    """Width of the piece holding the topmost pixel, within `band` rows of it."""
    ys = np.flatnonzero(mask.any(axis=1))
    top = mask[ys[0]:ys[0] + band]
    lab, _ = label(top)
    first = lab[0][lab[0] > 0][0]
    cols = np.flatnonzero((lab == first).any(axis=0))
    return int(cols[-1] - cols[0] + 1)


# ----------------------------------------------------------- 7-8. pixels
def tilt(rgb: np.ndarray, mask: np.ndarray, deg: float) -> tuple[np.ndarray, np.ndarray]:
    """Lean the figure about its feet (positive: top moves right). High-res, before the downscale."""
    if not deg:
        return rgb, mask
    h, w = mask.shape
    pad = int(h * math.sin(math.radians(abs(deg)))) + 2
    rgba = np.zeros((h, w + 2 * pad, 4), np.uint8)
    rgba[:, pad:pad + w, :3] = rgb
    rgba[:, pad:pad + w, 3] = mask * 255
    ax = body_axis(mask) + pad
    im = Image.fromarray(rgba, "RGBA").rotate(-deg, resample=Image.NEAREST, center=(ax, h - 1),
                                              fillcolor=(0, 0, 0, 0))
    a = np.asarray(im)
    m = a[..., 3] > 127
    return crop(a[..., :3], m)


def downscale(rgb: np.ndarray, mask: np.ndarray, sx: float, sy: float, pal: np.ndarray) -> np.ndarray:
    """Palette indices (-1 transparent): premultiplied box filter, alpha >= 1/2."""
    h, w = mask.shape
    nw, nh = max(1, round(w * sx)), max(1, round(h * sy))
    a = mask.astype(np.float32)
    pre = np.dstack([rgb.astype(np.float32) * a[..., None], a * 255.0])
    chans = [np.asarray(Image.fromarray(pre[..., k]).resize((nw, nh), Image.BOX)) for k in range(4)]
    alpha = chans[3] / 255.0
    op = alpha >= 0.5
    col = np.dstack(chans[:3]) / np.maximum(alpha, 1e-6)[..., None]
    idx = np.full((nh, nw), TRANSPARENT, np.int32)
    if op.any():
        idx[op] = snap(np.clip(col[op], 0, 255)[None], pal)[0]
    return idx


def outline(idx: np.ndarray, pal: np.ndarray, shade: float = OUTLINE_SHADE) -> np.ndarray:
    """Sel-out: every opaque pixel touching transparency (4-neighbours)
    takes the mean colour of its inner 8-neighbours x shade (its own colour
    if it has none). The rim is where the background's tint survives the key,
    so the rim's own colour is never trusted (no pink or red halo)."""
    op = idx >= 0
    padded = np.pad(op, 1)
    edge = op & ~(padded[:-2, 1:-1] & padded[2:, 1:-1] & padded[1:-1, :-2] & padded[1:-1, 2:])
    inner = op & ~edge
    rgb = pal[np.clip(idx, 0, None)].astype(np.float64)
    acc = np.zeros(idx.shape + (3,))
    cnt = np.zeros(idx.shape)
    h, w = idx.shape
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if not (dy or dx):
                continue
            src = (slice(max(0, -dy), h - max(0, dy)), slice(max(0, -dx), w - max(0, dx)))
            dst = (slice(max(0, dy), h + min(0, dy)), slice(max(0, dx), w + min(0, dx)))
            m = inner[src]
            acc[dst] += rgb[src] * m[..., None]
            cnt[dst] += m
    out = idx.copy()
    if edge.any():
        base = np.where(cnt[..., None] > 0, acc / np.maximum(cnt, 1)[..., None], rgb)
        out[edge] = snap((base[edge] * shade)[None], pal)[0]
    return out


def add_blood(idx: np.ndarray, level: int, pal: np.ndarray, seed: int) -> np.ndarray:
    """The gib's blood, drawn at sprite scale: levels 1-3 a spray from the
    chest growing, 4-6 a pool under a lying body growing. Deterministic."""
    if level <= 0:
        return idx
    rng = np.random.default_rng(seed)
    blood = [int(snap(np.array([[c]]), pal)[0, 0]) for c in BLOOD_RGB]
    h, w = idx.shape
    out = idx.copy()
    op = idx >= 0
    ys, xs = np.flatnonzero(op.any(axis=1)), np.flatnonzero(op.any(axis=0))
    if level <= 3:
        cx, cy = float(np.median(np.nonzero(op)[1])), ys[0] + 0.35 * (ys[-1] - ys[0])
        n, reach = 18 * level, 4 + 4 * level
        for _ in range(n):
            ang, r = rng.uniform(0, 2 * math.pi), abs(rng.normal(0, reach / 2))
            x, y = int(round(cx + r * math.cos(ang))), int(round(cy + 0.8 * r * math.sin(ang)))
            if 0 <= x < w and 0 <= y < h:
                out[y, x] = blood[rng.integers(0, len(blood))]
        # a wound: the chest's own pixels darkened red
        wound = (np.abs(np.arange(w)[None] - cx) <= level) & (np.abs(np.arange(h)[:, None] - cy) <= level) & op
        out[wound] = blood[1]
    else:
        k = level - 3
        cx, base = (xs[0] + xs[-1]) / 2, ys[-1]
        rx, ry = (xs[-1] - xs[0]) * (0.25 + 0.12 * k), 1 + k
        yy, xx = np.mgrid[0:h, 0:w]
        pool = ((xx - cx) / max(rx, 1)) ** 2 + ((yy - base) / ry) ** 2 <= 1.0
        out[pool & ~op] = blood[3]
        out[pool & op & (yy >= base - 1)] = blood[0]
        for _ in range(6 * k):
            x, y = int(rng.integers(xs[0], xs[-1] + 1)), int(rng.integers(ys[0], ys[-1] + 1))
            if op[y, x]:
                out[y, x] = blood[rng.integers(0, 3)]
    return out


# ------------------------------------------------------------- 9. place
def feet_anchor(idx: np.ndarray) -> tuple[float, int]:
    """(axis column, last opaque row) of a sprite-scale picture."""
    op = idx >= 0
    return body_axis(op), int(np.flatnonzero(op.any(axis=1))[-1])


def _ceil8(v: float) -> int:
    return int(math.ceil(v / 8.0)) * 8


def place_frame(pics: dict[str, np.ndarray],
                sink: int = FEET_SINK) -> tuple[dict[str, np.ndarray], tuple[int, int]]:
    """One canvas for every picture of a frame letter: legs' axis at `left`,
    the last row `sink` under `top`. Returns ({lump: canvas}, (left, top))."""
    half, above, below = 0.0, 0, 0
    anchors = {}
    for lump, idx in pics.items():
        ax, last = feet_anchor(idx)
        floor = last - sink
        anchors[lump] = (ax, floor)
        half = max(half, ax + 1, idx.shape[1] - ax)
        above = max(above, floor)
        below = max(below, idx.shape[0] - floor)
    w = _ceil8(2 * (half + CANVAS_PAD))
    top = above + CANVAS_PAD
    h = _ceil8(top + below)
    left = w // 2
    out = {}
    for lump, idx in pics.items():
        ax, floor = anchors[lump]
        c = np.full((h, w), TRANSPARENT, np.int32)
        ox, oy = int(round(left - ax)), top - floor
        c[oy:oy + idx.shape[0], ox:ox + idx.shape[1]] = idx
        out[lump] = c
    return out, (left, top)


# ---------------------------------------------------------------- names
PAIR_ROTS = (1, 2, 3, 4, 5)   # with mirror pairs: rotations 6-8 are 4-2 flipped by the engine


def rot_lump(spec: EnemySpec, letter: str, r: int) -> str:
    """SDRRA2, or SDHNA2A8 for a set written in mirror pairs."""
    if spec.pairs and 2 <= r <= 4:
        return f"{spec.sprite}{letter}{r}{letter}{10 - r}"
    return f"{spec.sprite}{letter}{r}"


def rots_of(spec: EnemySpec) -> tuple[int, ...]:
    return PAIR_ROTS if spec.pairs else tuple(range(1, 9))


def ref_lump(spec: EnemySpec, letter: str = "B") -> str:
    """The lump whose figure is target_height tall: the ref view's rotation."""
    return rot_lump(spec, letter, spec.ref_view + 1)


def lump_names(spec: EnemySpec) -> list[str]:
    names = [rot_lump(spec, f, r) for f in sorted(spec.rotated) for r in rots_of(spec)]
    names += [f"{spec.sprite}{f}0" for f in sorted(spec.single)]
    return sorted(names)


def current_names(spec: EnemySpec, sprites_dir: Path = SPRITES_DIR) -> list[str]:
    return sorted(p.stem.upper() for p in (sprites_dir / spec.folder).glob(f"{spec.sprite}*.png"))


# ----------------------------------------------------------------- I/O
def guard_out(path: Path, root: Path = ROOT) -> None:
    """Refuse to write under assets/, src/ or dist/ (an approval nobody gave)."""
    try:
        rel = Path(path).resolve().relative_to(root.resolve())
    except ValueError:
        return
    if rel.parts and rel.parts[0] in FORBIDDEN_OUT:
        raise SystemExit(f"gemini_enemy: refusing to write under {rel.parts[0]}/: {rel}")


def to_rgba(idx: np.ndarray, pal: np.ndarray) -> np.ndarray:
    rgba = np.zeros(idx.shape + (4,), np.uint8)
    op = idx >= 0
    rgba[op, :3] = pal[idx[op]]
    rgba[op, 3] = 255
    return rgba


def save_sprite(rgba: np.ndarray, grab: tuple[int, int], path: Path) -> Path:
    guard_out(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *grab))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def read_grab(path: Path) -> tuple[int, int] | None:
    data = Path(path).read_bytes()
    i = data.find(b"grAb")
    return struct.unpack(">ii", data[i + 4:i + 12]) if i >= 0 else None


# --------------------------------------------------------------- build
@dataclass
class Cut:
    rgb: np.ndarray
    mask: np.ndarray
    facing: str
    mirrored: bool
    painted: int
    edges: tuple = ()           # sheet edges the figure touches (top/bottom/left/right): cut art
    sole: int = 0               # rows of derived sole added
    marker: str | None = None   # side the armband was read on (front/back views, armband_side)


@dataclass
class SheetCut:
    bg: tuple
    figs: list = field(default_factory=list)   # Cut per figure
    helmet: int = 0
    scale: float = 1.0


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"))


def touched_edges(mask: np.ndarray) -> tuple[str, ...]:
    """The sheet edges a figure's mask reaches (its art is likely cut there)."""
    return tuple(n for n, line in (("top", mask[0]), ("bottom", mask[-1]),
                                   ("left", mask[:, 0]), ("right", mask[:, -1])) if line.any())


def cut_sheet(rgb: np.ndarray, sheet: Sheet, armband: str = "blank",
              armband_side: str | None = None, field_max: int | None = None,
              guide: tuple | None = None) -> SheetCut:
    """`guide`: (rgb, full-sheet figure masks) of the sheet named by Sheet.guide."""
    bg = estimate_background(rgb)
    fg = key_background(rgb, bg)
    if sheet.shadow:
        fg &= ~shadow_mask(rgb)
    sc = SheetCut(tuple(round(float(v)) for v in bg))
    heals, g_rgb = None, None
    if guide is not None:
        masks, heals, g_rgb = guided_figures(fg, rgb, guide[0], guide[1], sheet.flash)
    else:
        masks = figures(fg, sheet.count, sheet.split_x, rgb, sheet.path)
    if sheet.rows > 1:
        masks = grid_order(masks, sheet.rows, rgb.shape[0])
    if sheet.pick:
        masks = [masks[k] for k in sheet.pick]
    erase: dict[int, list] = {}
    for view, box, *kind in sheet.erase:
        erase.setdefault(view, []).append((box, kind[0] if kind else "glow"))
    for i, m in enumerate(masks):
        if sheet.core:
            m = largest(m)
        edges = touched_edges(m)
        src = rgb
        if heals is not None and heals[i].any():   # a neighbour's flash over this body: the guide's pixels
            src = rgb.copy()
            src[heals[i]] = g_rgb[heals[i]]
            m = m | heals[i]
        c_rgb, c_mask = crop(src, m)
        for box, kind in erase.get(i, ()):
            c_mask = erase_glow(c_rgb, c_mask, box, kind)
        if i in erase:
            c_rgb, c_mask = crop(c_rgb, c_mask)
        sole = sheet.sole if "bottom" in edges else 0
        c_rgb, c_mask = add_sole(c_rgb, c_mask, sole)
        c_rgb, painted = blank_armband(c_rgb, c_mask, armband, field_max)
        for view, (x0, y0, x1, y1) in sheet.patch:
            if view == i:
                sub, m = c_rgb[y0:y1, x0:x1], c_mask[y0:y1, x0:x1]
                painted += int(m.sum())
                sub[m] = PATCH_RGB
        face = facing_of(sheet, i, c_mask) if i in SIDE_VIEWS and sheet.facing else \
            (sheet.facing[i] if i < len(sheet.facing) else "front")
        c_rgb, c_mask, mir = normalise(c_rgb, c_mask, face)
        marker = None
        if armband_side and sheet.facing and face in ("front", "back"):
            marker = marker_side(c_rgb, c_mask)
            want = armband_side if face == "front" else {"left": "right", "right": "left"}[armband_side]
            if marker is not None and marker != want:      # the body is drawn mirrored: put it back
                c_rgb, c_mask, mir = c_rgb[:, ::-1].copy(), c_mask[:, ::-1].copy(), True
        sc.figs.append(Cut(c_rgb, c_mask, face, mir, painted, edges, sole, marker))
    return sc


def guide_of(spec: EnemySpec, key: str, rgbs: dict) -> tuple | None:
    """(rgb, full-sheet figure masks) of the sheet `key` is painted over, or None."""
    s = spec.sheets[key]
    if not s.guide:
        return None
    g = spec.sheets[s.guide]
    if g.guide or g.rows > 1 or g.pick:
        raise ValueError(f"{s.file}: its guide {g.file} must be a plain one-row sheet")
    grgb = rgbs[s.guide]
    return grgb, figures(key_background(grgb, estimate_background(grgb)), g.count, g.split_x, grgb, g.path)


def plan(spec: EnemySpec, ref_dir: Path = REF_DIR) -> dict[str, SheetCut]:
    rgbs = {k: load_rgb(ref_dir / s.file) for k, s in spec.sheets.items()}
    cuts = {k: cut_sheet(rgbs[k], s, spec.armband, spec.armband_side, spec.field_max, guide_of(spec, k, rgbs))
            for k, s in spec.sheets.items()}
    ref = cuts[spec.ref_sheet]
    ref_h = ref.figs[spec.ref_view].mask.shape[0]
    band = max(4, int(HELMET_BAND * ref_h))
    for k, s in spec.sheets.items():
        if s.scale_ref is not None:
            cuts[k].helmet = helmet_width(cuts[k].figs[s.scale_ref].mask, band)
    ref_helmet = ref.helmet or 1
    for k, s in spec.sheets.items():
        cuts[k].scale = ref_helmet / cuts[k].helmet if s.scale_ref is not None else 1.0 / s.rel_scale
    return cuts


CLOSE_ROTS = (3, 7)      # the profiles: seen closest, with the corpses (D108: option 2 there)


@dataclass
class SymbolPass:
    """The D12 symbol for one enemy's pictures (D108): option 1 (armband_symbol,
    painted at Gemini's resolution) on every picture with a field; with
    `fooocus`, option 2's cached repaint over it."""
    mode: str = "warp"
    fields: str = "white"
    field_max: int | None = None
    fooocus: bool = False
    cache_dir: Path | None = None


def symbol_pass(spec: EnemySpec, mode: str = "spec", fooocus: bool = False,
                cache_dir: Path | None = None) -> SymbolPass | None:
    """The spec's own symbol (`spec`), or forced off (`none`) / on (`warp`)."""
    m = spec.symbol if mode == "spec" else mode
    if m == "none":
        return None
    return SymbolPass(m, spec.symbol_fields, spec.field_max, fooocus, cache_dir)


def symbolise(rgb: np.ndarray, mask: np.ndarray, sp: SymbolPass) -> tuple[np.ndarray, str]:
    """(picture, status): `nofield`, `option1`, or option 2's status
    (`fooocus`, `partial`, `fallback`, `missing`: armband_symbol.apply_fooocus)."""
    import armband_symbol as asym     # it imports this module: imported here, when first needed
    key = asym.picture_key(rgb, mask)
    prepped, fields = asym.select_fields(rgb, mask, sp.fields, sp.field_max)
    if not fields:
        return rgb, "nofield"
    out = asym.apply_symbol(prepped, mask, sp.mode, seed=asym.picture_seed(key), fields=fields)
    if not sp.fooocus:
        return out, "option1"
    return asym.apply_fooocus(out, mask, key, sp.cache_dir or asym.FOOOCUS_CACHE)


def source_picture(cut: Cut, mirror: bool = False, core: bool = False, shade: float = 1.0,
                   symbol: SymbolPass | None = None, retouch=None,
                   key: tuple | None = None) -> tuple[np.ndarray, np.ndarray, str | None]:
    """(rgb, mask, symbol status) at Gemini's resolution, before the tilt:
    the biggest piece (core), the mirror, THEN the symbol (never mirrored,
    D105/D108), then the black plate (the symbol is drawn on the shared art,
    so the Schwer reuses the Panzermensch's repaints). `retouch(key, rgb,
    mask) -> rgb` (insignia_fix.py, V3): a repaint after the mirror and
    before the symbol, inside the silhouette (the mask is never changed);
    None, the default, leaves every picture as it was."""
    rgb, mask = cut.rgb, cut.mask
    if core:
        rgb, mask = crop(rgb, largest(mask))
    if mirror:
        rgb, mask = rgb[:, ::-1], mask[:, ::-1]
    if retouch is not None:
        rgb = retouch(key, np.ascontiguousarray(rgb), np.ascontiguousarray(mask))
    status = None
    if symbol is not None:
        rgb, status = symbolise(np.ascontiguousarray(rgb), np.ascontiguousarray(mask), symbol)
    return darken(rgb, mask, shade), mask, status


def render(cut: Cut, scale: float, pal: np.ndarray, tilt_deg: float = 0.0, mirror: bool = False,
           blood: int = 0, seed: int = 0, core: bool = False, shade: float = 1.0,
           symbol: SymbolPass | None = None, picture: tuple | None = None) -> np.ndarray:
    rgb, mask, _ = picture if picture is not None else source_picture(cut, mirror, core, shade, symbol)
    if tilt_deg:
        # lean back: away from the facing (views facing left lean right); front/back lean right a little
        rgb, mask = tilt(rgb, mask, tilt_deg if not mirror else -tilt_deg)
    idx = downscale(rgb, mask, scale * PIXEL_ASPECT, scale, pal)
    idx = outline(idx, pal)
    return add_blood(idx, blood, pal, seed)


def lump_sources(spec: EnemySpec) -> dict[str, tuple]:
    """lump -> (sheet, view, mirror, core, tilt, blood, seed): the picture each lump is drawn from."""
    out = {}
    for letter, rot in spec.rotated.items():
        over = dict(rot.override)
        for r in rots_of(spec):
            src = over.get(r)
            if src is not None:
                out[rot_lump(spec, letter, r)] = (src.sheet, src.view, src.mirror, src.core, src.tilt, src.blood, 0)
            else:
                out[rot_lump(spec, letter, r)] = (rot.sheet, VIEW_OF_ROT[r], r in MIRRORED_ROTS, False, rot.tilt, 0, 0)
    for n, (letter, src) in enumerate(sorted(spec.single.items())):
        out[f"{spec.sprite}{letter}0"] = (src.sheet, src.view, src.mirror, src.core, src.tilt, src.blood, 7000 + n)
    return out


def close_sources(spec: EnemySpec) -> set[tuple]:
    """(sheet, view, mirror, core) of the pictures seen close (D108): the
    profiles (rotations CLOSE_ROTS of every rotated letter) and the corpse
    letters. Every lump drawn from one of them gets option 2 (the gib's last
    frame is the corpse's picture with blood: the same repaint)."""
    src = lump_sources(spec)
    lumps = [rot_lump(spec, f, r) for f in spec.rotated for r in CLOSE_ROTS if r in rots_of(spec)]
    lumps += [f"{spec.sprite}{f}0" for f in spec.corpse if f in spec.single]
    return {src[lu][:4] for lu in lumps if lu in src}


def build(spec: EnemySpec, out_dir: Path | None = None, ref_dir: Path = REF_DIR,
          symbol: str = "spec", cache_dir: Path | None = None, retouch=None) -> dict:
    """`retouch`: source_picture's hook (insignia_fix.py); None builds the set as approved."""
    pal = palette_rgb(spec.palette_version)
    out_dir = out_dir or OUT_ROOT / spec.name
    guard_out(out_dir)
    cuts = plan(spec, ref_dir)
    base = spec.target_height / cuts[spec.ref_sheet].figs[spec.ref_view].mask.shape[0]
    for letter, rot in spec.rotated.items():
        over = dict(rot.override)
        if spec.pairs and set(over) - set(PAIR_ROTS):
            raise ValueError(f"{spec.name} {letter}: a mirror-pair set draws no rotation "
                             f"{sorted(set(over) - set(PAIR_ROTS))}")
    close = close_sources(spec)
    pictures: dict[tuple, tuple] = {}
    status: dict[str, str] = {}
    frames: dict[str, dict[str, np.ndarray]] = {}
    for lump, (sheet, view, mirror, core, tilt_deg, blood, seed) in lump_sources(spec).items():
        key = (sheet, view, mirror, core)
        if key not in pictures:     # one picture (and one symbol) per source, shared by its lumps
            sp = symbol_pass(spec, symbol, fooocus=key in close, cache_dir=cache_dir)
            pictures[key] = source_picture(cuts[sheet].figs[view], mirror, core, spec.shade, sp,
                                           retouch, key)
        if pictures[key][2] is not None:
            status[lump] = pictures[key][2]
        frames.setdefault(lump[len(spec.sprite)], {})[lump] = render(
            cuts[sheet].figs[view], base * cuts[sheet].scale, pal, tilt_deg, mirror, blood, seed,
            picture=pictures[key])
    written, grabs = [], {}
    for letter in sorted(frames):
        canv, grab = place_frame(frames[letter], spec.feet_sink)
        for lump, idx in sorted(canv.items()):
            save_sprite(to_rgba(idx, pal), grab, out_dir / f"{lump}.png")
            written.append(lump)
            grabs[lump] = {"size": [int(idx.shape[1]), int(idx.shape[0])], "grab": list(grab)}
    metrics = {
        "enemy": spec.name, "sprite": spec.sprite, "lumps": len(written), "target_height": spec.target_height,
        "base_scale": round(base, 4), "pixel_aspect": PIXEL_ASPECT,
        "sheets": {k: {"file": spec.sheets[k].file, "background": list(c.bg), "helmet_px": c.helmet,
                       "scale": round(c.scale, 4),
                       "figures": [{"size": [int(f.mask.shape[1]), int(f.mask.shape[0])], "facing": f.facing,
                                    "mirrored": f.mirrored, "armband_px_blanked": f.painted,
                                    "edges": list(f.edges), "sole_rows": f.sole, "armband_side": f.marker}
                                   for f in c.figs]}
                   for k, c in cuts.items()},
        "derived": list(spec.derived), "frames": grabs,
        "gate": quality_gate(spec, cuts, written),
        "reask": [list(r) for r in spec.reask],
        "symbol": {lu: status[lu] for lu in sorted(status)},
        "symbol_close": sorted(lu for lu, s in lump_sources(spec).items() if s[:4] in close),
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    return metrics


# ------------------------------------------------------------------ gate
def quality_gate(spec: EnemySpec, cuts: dict, written=None) -> list[str]:
    """What the build could not do cleanly, for the CEO's sheet: art cut
    by a sheet edge (with or without a derived sole), a front/back view
    whose armband side could not be read or had to be mirrored, a lump set
    that is not the spec's."""
    out = []
    for k, c in cuts.items():
        for i, f in enumerate(c.figs):
            where = f"{spec.sheets[k].file} figure {i + 1}"
            cut = [e for e in f.edges if not (e == "bottom" and f.sole)]
            if cut:
                out.append(f"{where}: the drawing touches the edge ({', '.join(cut)}): cut")
            if f.sole:
                out.append(f"{where}: boots cut by the bottom edge, derived sole ({f.sole} px)")
            if spec.armband_side and spec.sheets[k].facing and f.facing in ("front", "back"):
                if f.marker is None:
                    out.append(f"{where}: the armband side cannot be read (unchecked)")
                elif f.mirrored:
                    out.append(f"{where}: body flipped relative to turn: mirrored")
    if written is not None and sorted(written) != lump_names(spec):
        out.append("the lumps written are not the spec's set")
    return out


# --------------------------------------------------------------- overlay
def overlay_plan(out_root: Path = OUT_ROOT, enemies=None) -> dict[str, Path]:
    """pk3 path -> PNG: every built enemy whose lump set is complete (the shipped set's names)."""
    files: dict[str, Path] = {}
    for spec in (enemies or ENEMIES.values()):
        folder = out_root / spec.name
        have = sorted(p.stem.upper() for p in folder.glob(f"{spec.sprite}*.png"))
        if not have:
            continue
        want = lump_names(spec)
        if have != want:
            raise SystemExit(f"gemini_enemy: {spec.name}: built lumps differ from the spec: "
                             f"missing {sorted(set(want) - set(have))}, extra {sorted(set(have) - set(want))}")
        for name in have:
            files[f"sprites/{name}.png"] = folder / f"{name}.png"
    return files


def write_overlay(files: dict[str, Path], out: Path = OVERLAY) -> Path:
    guard_out(out)
    if not files:
        raise SystemExit("gemini_enemy: nothing to pack (build an enemy first)")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for arc in sorted(files):
            info = zipfile.ZipInfo(arc, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, files[arc].read_bytes())
    lines = [f"{out.name}: draft enemy sprites from Gemini sheets (D104/D105), load AFTER the mod:",
             f"  SD_ALLOW_ENGINE=1 tools/run.sh -file work/overlays/{out.name}",
             "Same lump names as assets/sprites/<enemy>/: each replaces the shipped lump of that name.", ""]
    lines += [f"{arc}  <- {files[arc].relative_to(ROOT).as_posix() if files[arc].is_relative_to(ROOT) else files[arc]}"
              for arc in sorted(files)]
    out.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# ------------------------------------------------------------ review sheet
def _b64(path_or_img) -> str:
    if isinstance(path_or_img, Image.Image):
        buf = io.BytesIO()
        path_or_img.save(buf, "PNG")
        data = buf.getvalue()
    else:
        data = Path(path_or_img).read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def _frames_json(folder: Path, sprite: str) -> dict:
    out = {}
    for p in sorted(folder.glob(f"{sprite}*.png")):
        g = read_grab(p) or (0, 0)
        with Image.open(p) as im:
            w, h = im.size
        out[p.stem.upper()] = {"src": _b64(p), "w": w, "h": h, "left": g[0], "top": g[1]}
    return out


def review_sheet(specs=None, out: Path = SHEET_HTML, out_root: Path = OUT_ROOT,
                 sprites_dir: Path = SPRITES_DIR) -> Path:
    """The CEO's sheet: per enemy, current vs new, eight rotations, looping animations, OK/NO/?."""
    items = []
    for spec in (specs or ENEMIES.values()):
        new_dir = out_root / spec.name
        if not any(new_dir.glob(f"{spec.sprite}*.png")):
            continue
        metrics = json.loads((new_dir / "metrics.json").read_text(encoding="utf-8"))
        items.append({
            "id": spec.name, "sprite": spec.sprite, "letters": sorted(spec.rotated),
            "anims": [{"label": a[0], "seq": [list(s) for s in a[1]]} for a in spec.anims],
            "cur": _frames_json(sprites_dir / spec.folder, spec.sprite),
            "new": _frames_json(new_dir, spec.sprite),
            "derived": list(spec.derived), "notes": spec.notes,
            "gate": metrics.get("gate", []), "reask": metrics.get("reask", []),
            "symbol": symbol_summary(metrics) if metrics.get("symbol") else "",
            "sheets": {k: [f["facing"] + (" (mirrored)" if f["mirrored"] else "") for f in v["figures"]]
                       for k, v in metrics["sheets"].items()},
        })
    html = SHEET_TEMPLATE.replace("/*ITEMS*/[]", json.dumps(items))
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


SHEET_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gemini Enemies</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1d1b;--mute:#6b6862;--line:#dcd8cf;--accent:#a3201c;--ok:#1f7a3a;--no:#b3261e;--q:#9a6a00;--chip:#efece4;--well:#3b3d42}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--well:#2a2b2f}}
:root[data-theme="dark"]{--bg:#161616;--card:#202020;--ink:#ebe8e2;--mute:#a19d95;--line:#3a3834;--accent:#e0574f;--ok:#4cc074;--no:#f0726a;--q:#e3b341;--chip:#2c2b29;--well:#2a2b2f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px 48px}
header.top{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 0}
header.top .wrap{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;padding-bottom:0}
h1{font-size:18px;margin:0;font-weight:650}
h2{font-size:17px;margin:30px 0 4px;padding-top:10px;border-top:2px solid var(--accent)}
h3{font-size:13px;margin:14px 0 6px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.prog{color:var(--mute)}.prog b{color:var(--ink)}
button{font:inherit;cursor:pointer;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:5px 10px}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.card{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:14px 0}
.row{display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:10px 16px;padding:12px}
.row.v-ok{box-shadow:inset 4px 0 var(--ok)}.row.v-no{box-shadow:inset 4px 0 var(--no)}.row.v-q{box-shadow:inset 4px 0 var(--q)}
.meta{color:var(--mute);font-size:12.5px;margin:3px 0}
.strip{display:flex;flex-wrap:wrap;gap:4px;padding:4px 0;align-items:flex-end}
.cell{display:flex;flex-direction:column;align-items:center;font-size:11px;color:var(--mute)}
.stage{background:var(--well);border:1px solid var(--line);position:relative;overflow:hidden}
.stage img{position:absolute;image-rendering:pixelated;image-rendering:crisp-edges}
.floor{position:absolute;left:0;right:0;height:1px;background:rgba(255,255,255,.18)}
.pair{display:flex;gap:16px;flex-wrap:wrap}
.vote{display:flex;flex-direction:column;gap:6px}
.btns{display:flex;gap:6px}.btns button{flex:1;font-weight:650;padding:6px 0}
.btns button.on.ok{background:var(--ok);border-color:var(--ok);color:#fff}
.btns button.on.no{background:var(--no);border-color:var(--no);color:#fff}
.btns button.on.q{background:var(--q);border-color:var(--q);color:#111}
textarea{width:100%;min-height:60px;font:inherit;font-size:13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink);padding:5px 7px}
#result{min-height:140px;font:12.5px ui-monospace,Consolas,monospace}
.rots button{padding:2px 8px;margin:0 2px}.rots button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.copied{color:var(--ok);font-weight:600;margin-left:8px}
ul{margin:6px 0;padding-left:20px}
@media (max-width:760px){.row{grid-template-columns:1fr}}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <h1>Soviet Doom · Enemies redrawn with Gemini (draft)</h1>
  <span class="prog"><b id="pDone">0</b> / <span id="pAll">0</span> judged</span>
  <button class="primary" id="copyTop">Copy result</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
<p>Each enemy: the <b>current</b> one (installed) against the <b>new</b> one (from the Gemini sheets, D104/D105), enlarged ×3 without smoothing,
on its floor line (the light line) with the real offsets. Enemies: rifleman <code>SDRR</code>, Legion trooper
<code>SDLT</code>, hybrid stormtrooper <code>SDHS</code>, Reich hound <code>SDHN</code>, doughboy <code>SDDB</code>,
Panzermensch <code>SDPM</code> and Panzermensch Schwer <code>SDPS</code> (the same art, bigger and with the black plate),
The General <code>SDGN</code>. Same lump names (the hound in mirror pairs as today: «(mirrored)» is the rotation the
engine flips): the overlay <code>work/overlays/sd-draft-enemies.pk3</code> replaces them when loaded after the mod. On everything
of the Reich the armband (and the Panzermensch's emblem) carries the D12 symbol per <b>«la mezcla»</b> ("the mix", the CEO's decision, D108):
option 1 (painted at Gemini's resolution, bent with the arm, never mirrored) on every frame, and option 2 (Fooocus, local SDXL)
on top in the profiles (rotations 3 and 7) and the corpses, chosen by an objective metric; the General's US flag is left
alone. Control sheet: <code>docs/art/previews/2026-10-22_P4_armbands-applied.png</code>. Mark OK / NO / ? per row and press <b>Copy result</b>.</p>
<div id="enemies"></div>
<h2>General note</h2>
<textarea id="general" placeholder="Anything general"></textarea>
<h3>Result</h3>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copy result</button><span class="copied" id="copiedBottom"></span> <button id="reset">Clear answers</button></p>
<p class="meta">Tool: <code>tools/art/gemini_enemy.py</code> (background key per image, figures by components, orientation and scale
normalised, premultiplied box filter, palette v2, outline, offsets with the feet on the floor). The Gemini sheets do not leave
<code>work/</code> (D77); this sheet carries only the derived sprites. Nothing installed: the PM installs it on your OK. NOT VERIFIED in GZDoom (D26).</p>
</div>
<script>
const ITEMS = /*ITEMS*/[];
const Z = 3, TIC = 1000 / 35;
const KEY = "sd-2026-10-22_P4_enemies-gemini";
let S = {};
try { S = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { S = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
const st = id => (S[id] = S[id] || {v: "", n: ""});
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const ROWS = [];
function frame(set, sp, L, r){
  // the picture of letter L in rotation r: its own lump, a mirror pair (SDHNA2A8), or the
  // pair's other half flipped as the engine does (offset mirrored too), or the rotation-0 lump
  if (r && set[sp + L + r]) return set[sp + L + r];
  if (r >= 2 && r <= 4 && set[sp + L + r + L + (10 - r)]) return set[sp + L + r + L + (10 - r)];
  if (r >= 6 && r <= 8) { const g = set[sp + L + (10 - r) + L + r]; if (g) return Object.assign({}, g, {left: g.w - g.left, flip: true}); }
  return set[sp + L + "0"] || null;
}
function box(frames){
  // one stage size for a group of pictures: the union of their extents about (left, top)
  let l = 0, r = 0, u = 0, d = 0;
  for (const f of frames) { if (!f) continue;
    l = Math.max(l, f.left); r = Math.max(r, f.w - f.left); u = Math.max(u, f.top); d = Math.max(d, f.h - f.top); }
  return {l, r, u, d, w: l + r, h: u + d};
}
function place(img, f, b){
  img.src = f.src; img.width = f.w * Z; img.height = f.h * Z;
  img.style.left = (b.l - f.left) * Z + "px"; img.style.top = (b.u - f.top) * Z + "px";
  img.style.transform = f.flip ? "scaleX(-1)" : "";
}
function stage(f, b, id){
  if (!f) return `<div class="stage" style="width:${b.w*Z}px;height:${b.h*Z}px"></div>`;
  return `<div class="stage" style="width:${b.w*Z}px;height:${b.h*Z}px"><div class="floor" style="top:${b.u*Z}px"></div>` +
    `<img ${id ? `id="${id}"` : ""} src="${f.src}" width="${f.w*Z}" height="${f.h*Z}" style="left:${(b.l-f.left)*Z}px;top:${(b.u-f.top)*Z}px${f.flip ? ";transform:scaleX(-1)" : ""}" alt=""></div>`;
}
function row(id, title, body){
  ROWS.push({id, title});
  return `<div class="card"><div class="row" id="r-${id}" data-id="${id}"><div><b>${esc(title)}</b>${body}</div>
    <div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
    <textarea class="note" placeholder="Notes (what to ask Gemini again, what to change…)">${esc(st(id).n)}</textarea></div></div></div>`;
}
function rotStrip(set, sp, L){
  const fr = [1,2,3,4,5,6,7,8].map(r => frame(set, sp, L, r)), b = box(fr);
  return `<div class="strip">` + fr.map((f, k) => `<div class="cell">${stage(f, b)}${L}${k + 1}${f && f.flip ? " (mirrored)" : ""}</div>`).join("") + `</div>`;
}
function build(){
  let html = "";
  for (const it of ITEMS) {
    html += `<h2>${esc(it.id)} <code>${it.sprite}</code></h2><p class="meta">Derived (not drawn by Gemini):</p><ul class="meta">` +
      it.derived.map(d => `<li>${esc(d)}</li>`).join("") + `</ul>` +
      (it.symbol ? `<p class="meta">Armband D12 (D108), lumps per route: ${esc(it.symbol.replace(/option1/g, "option 1").replace(/fooocus/g, "Fooocus").replace(/fallback/g, "option 1 (below the threshold)").replace(/missing/g, "option 1 (not generated)"))}</p>` : "") +
      ((it.gate || []).length ? `<p class="meta">Quality gate (measured):</p><ul class="meta">` + it.gate.map(d => `<li>${esc(d)}</li>`).join("") + `</ul>` : "") +
      ((it.reask || []).length ? `<p class="meta">Ask Gemini again:</p><ul class="meta">` + it.reask.map(([f, p]) => `<li><code>${esc(f)}</code>: ${esc(p)}</li>`).join("") + `</ul>` : "") +
      `<p class="meta">Orientation read per sheet: ` + Object.entries(it.sheets).map(([k, v]) => `<b>${k}</b> ${v.join(", ")}`).join(" · ") + `</p>`;
    for (const L of it.letters) {
      html += row(`${it.id}-${L}`, `Frame ${L}: the 8 rotations (top current, bottom new)`,
        `<h3>current</h3>${rotStrip(it.cur, it.sprite, L)}<h3>new</h3>${rotStrip(it.new, it.sprite, L)}`);
    }
    const singles = Object.keys(it.new).filter(n => n.length === 6 && n.endsWith("0")).sort();
    const bs = box(singles.map(n => it.new[n])), bc = box(singles.map(n => it.cur[n]));
    html += row(`${it.id}-death`, `Death${singles.length > 7 ? " and gib" : ""} (rotation 0): ${singles.map(n => n[4]).join(" ")}`,
      `<h3>current</h3><div class="strip">` + singles.map(n => `<div class="cell">${stage(it.cur[n], bc)}${n[4]}</div>`).join("") +
      `</div><h3>new</h3><div class="strip">` + singles.map(n => `<div class="cell">${stage(it.new[n], bs)}${n[4]}</div>`).join("") + `</div>`);
    it.anims.forEach((a, k) => {
      const id = `${it.id}-anim${k}`;
      html += row(id, `Looping animation: ${a.label}`,
        `<div class="rots" data-anim="${id}">rotation: ` + [1,2,3,4,5,6,7,8].map(r => `<button data-r="${r}" class="${r===1?"on":""}">${r}</button>`).join("") +
        `</div><div class="pair"><div class="cell" id="${id}-cur"></div><div class="cell" id="${id}-new"></div></div>`);
    });
  }
  document.getElementById("enemies").innerHTML = html;
  document.getElementById("pAll").textContent = ROWS.length;
  ROWS.forEach(r => paint(r.id));
  for (const it of ITEMS) it.anims.forEach((a, k) => startAnim(it, a, `${it.id}-anim${k}`, 1));
}
const TIMERS = {};
function startAnim(it, a, id, rot){
  clearTimeout(TIMERS[id + "c"]); clearTimeout(TIMERS[id + "n"]);
  for (const [which, set] of [["cur", it.cur], ["new", it.new]]) {
    const fr = a.seq.map(([L]) => frame(set, it.sprite, L, rot)), b = box(fr);
    const el = document.getElementById(`${id}-${which}`);
    el.innerHTML = stage(fr.find(Boolean), b, `${id}-${which}-img`) + (which === "cur" ? "current" : "new");
    let i = 0;
    const step = () => {
      const [, tics] = a.seq[i], f = fr[i], img = document.getElementById(`${id}-${which}-img`);
      if (f && img) place(img, f, b);
      i = (i + 1) % a.seq.length;
      TIMERS[id + which[0]] = setTimeout(step, tics * TIC);
    };
    step();
  }
}
function paint(id){
  const r = document.getElementById("r-" + id), s = st(id);
  r.classList.remove("v-ok", "v-no", "v-q");
  if (s.v) r.classList.add("v-" + s.v);
  r.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === s.v));
}
function summary(){
  const label = {ok: "OK", no: "NO", q: "?"};
  const done = ROWS.filter(r => st(r.id).v).length;
  document.getElementById("pDone").textContent = done;
  const L = [`Gemini enemies (2026-10-22_P4, D104/D105): ${done}/${ROWS.length} judged`];
  for (const r of ROWS) { const s = st(r.id), n = (s.n || "").trim().replace(/\s+/g, " ");
    L.push(`${r.id}: ${label[s.v] || "not judged"}${n ? ` — «${n}»` : ""}`); }
  const g = (document.getElementById("general").value || "").trim().replace(/\s+/g, " ");
  if (g) L.push(`General: «${g}»`);
  document.getElementById("result").value = L.join("\n");
}
function copy(which){
  const t = document.getElementById("result"), msg = document.getElementById(which);
  summary();
  const ok = () => { msg.textContent = "copied"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "select and Ctrl+C below"); } catch (e) { msg.textContent = "select and Ctrl+C below"; } };
  try { if (navigator.clipboard && window.isSecureContext !== false) navigator.clipboard.writeText(t.value).then(ok, fallback); else fallback(); } catch (e) { fallback(); }
}
document.addEventListener("click", e => {
  const rb = e.target.closest(".rots button");
  if (rb) { const box = rb.parentElement, id = box.dataset.anim, [en, k] = [id.split("-anim")[0], +id.split("-anim")[1]];
    box.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === rb));
    const it = ITEMS.find(x => x.id === en); startAnim(it, it.anims[k], id, +rb.dataset.r); return; }
  const b = e.target.closest(".btns button"); if (!b) return;
  const id = b.closest(".row").dataset.id, s = st(id);
  s.v = s.v === b.dataset.v ? "" : b.dataset.v; save(); paint(id); summary();
});
document.addEventListener("input", e => {
  if (e.target.id === "general") { S._general = e.target.value; save(); summary(); return; }
  const r = e.target.closest(".row"); if (!r || !e.target.classList.contains("note")) return;
  st(r.dataset.id).n = e.target.value; save(); summary();
});
document.getElementById("copyTop").addEventListener("click", () => copy("copiedTop"));
document.getElementById("copyBottom").addEventListener("click", () => copy("copiedBottom"));
document.getElementById("reset").addEventListener("click", () => { if (confirm("Clear this sheet's answers and notes?")) { S = {}; save(); document.getElementById("general").value = ""; build(); summary(); } });
document.getElementById("general").value = S._general || "";
build(); summary();
</script>
</body>
</html>
"""



# ------------------------------------------------- the armbands' control sheet
# D108: per Reich enemy, every picture that carries the symbol, cut round
# the armband at x4, the ones repainted by Fooocus (option 2) framed green.
CONTROL_PNG = ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_armbands-applied.png"
CONTROL_ZOOM = 4
CONTROL_WIN = 22         # sprite px round the symbol shown per tile
CONTROL_COLS = 12
CONTROL_STATUS = {       # status -> (frame colour, short label)
    "fooocus": ((70, 200, 110), "F"), "partial": ((200, 200, 70), "F/1"),
    "fallback": ((230, 140, 40), "1 (threshold)"), "missing": ((150, 150, 150), "1 (not generated)"),
    "option1": ((90, 92, 100), "1"),
}


def symbol_summary(metrics: dict) -> str:
    """'n option1, n fooocus, ...' over a build's lumps (nofield left out)."""
    counts: dict[str, int] = {}
    for st in metrics.get("symbol", {}).values():
        if st != "nofield":
            counts[st] = counts.get(st, 0) + 1
    return ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) or "off"


def _symbol_window(idx: np.ndarray, bare: np.ndarray, win: int = CONTROL_WIN) -> tuple[int, int]:
    """(y0, x0) of the win x win window centred on what the symbol changed."""
    diff = (idx != bare)
    if diff.any():
        ys, xs = np.nonzero(diff)
        cy, cx = int(round(ys.mean())), int(round(xs.mean()))
    else:
        cy, cx = idx.shape[0] // 2, idx.shape[1] // 2
    return max(0, min(idx.shape[0] - win, cy - win // 2)), max(0, min(idx.shape[1] - win, cx - win // 2))


def control_tiles(spec: EnemySpec, ref_dir: Path = REF_DIR, cache_dir: Path | None = None) -> list[dict]:
    """One tile per picture with a symbol (a source shared by several lumps is one tile)."""
    pal = palette_rgb(spec.palette_version)
    cuts = plan(spec, ref_dir)
    base = spec.target_height / cuts[spec.ref_sheet].figs[spec.ref_view].mask.shape[0]
    close = close_sources(spec)
    by_key: dict[tuple, list[str]] = {}
    for lump, src in sorted(lump_sources(spec).items()):
        by_key.setdefault(src[:4], []).append(lump)
    tiles = []
    for key, lumps in sorted(by_key.items(), key=lambda kv: kv[1][0]):
        sheet, view, mirror, core = key
        cut, sc = cuts[sheet].figs[view], base * cuts[sheet].scale
        sp = symbol_pass(spec, "spec", fooocus=key in close, cache_dir=cache_dir)
        if sp is None:
            return []
        pic = source_picture(cut, mirror, core, spec.shade, sp)
        if pic[2] in (None, "nofield"):
            continue
        idx = render(cut, sc, pal, picture=pic)
        bare = render(cut, sc, pal, picture=source_picture(cut, mirror, core, spec.shade, None))
        if bare.shape != idx.shape:
            bare = idx
        y0, x0 = _symbol_window(idx, bare)
        win = idx[y0:y0 + CONTROL_WIN, x0:x0 + CONTROL_WIN]
        tiles.append({"lumps": lumps, "status": pic[2], "close": key in close, "rgba": to_rgba(win, pal)})
    return tiles


def control_sheet(specs=None, out: Path = CONTROL_PNG, ref_dir: Path = REF_DIR,
                  cache_dir: Path | None = None) -> Path:
    """The PNG: per Reich enemy, its symbol tiles at x CONTROL_ZOOM, framed by
    status (green: Fooocus), with counts of lumps per option."""
    guard_out(out)
    rows = []
    for spec in (ENEMIES.values() if specs is None else specs):
        if spec.symbol == "none":
            continue
        tiles = control_tiles(spec, ref_dir, cache_dir)
        n_f = sum(len(t["lumps"]) for t in tiles if t["status"] in ("fooocus", "partial"))
        n_all = sum(len(t["lumps"]) for t in tiles)
        fall = [t["lumps"][0] for t in tiles if t["status"] in ("fallback", "missing")]
        rows.append((spec, tiles, n_f, n_all, fall))
    z, w = CONTROL_ZOOM, CONTROL_WIN * CONTROL_ZOOM
    cell_w, cell_h = w + 10, w + 34
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 15)
        small = ImageFont.truetype(artlib.FONT_SMALL, 11)
    except OSError:  # pragma: no cover - no system font
        font = small = ImageFont.load_default()
    heights = [56 + ((len(t) + CONTROL_COLS - 1) // CONTROL_COLS) * cell_h for _, t, *_ in rows]
    W, H = 16 + CONTROL_COLS * cell_w, 70 + sum(heights) + 60
    img = Image.new("RGB", (W, H), (58, 60, 66))
    dr = ImageDraw.Draw(img)
    dr.text((10, 8), "Armbands applied (D108, «la mezcla», \"the mix\"): option 1 on every Reich frame; "
                     "Fooocus (option 2) on top in profiles (rot. 3 and 7) and corpses.", fill=(240, 236, 228), font=font)
    dr.text((10, 32), f"x{z}, a {CONTROL_WIN} px sprite window round the symbol; one tile per "
                      "source picture (the lumps sharing it below). Green = Fooocus; orange = below "
                      "the threshold (option 1 stays); grey = not generated.", fill=(214, 208, 196), font=small)
    y = 62
    for (spec, tiles, n_f, n_all, fall), hh in zip(rows, heights):
        msg = f"{spec.sprite} ({spec.name}): {n_all} lumps with the symbol, {n_f} with Fooocus, {n_all - n_f} option 1"
        dr.text((10, y + 10), msg, fill=(240, 236, 228), font=font)
        if fall:
            dr.text((10, y + 30), "close but on option 1 (below the threshold or not generated): " + ", ".join(fall),
                    fill=(230, 140, 40), font=small)
        for i, t in enumerate(tiles):
            cx, cy = 10 + (i % CONTROL_COLS) * cell_w, y + 52 + (i // CONTROL_COLS) * cell_h
            colour, short = CONTROL_STATUS.get(t["status"], ((90, 92, 100), t["status"]))
            dr.rectangle([cx - 3, cy - 3, cx + w + 2, cy + w + 2], outline=colour, width=3)
            dr.rectangle([cx, cy, cx + w - 1, cy + w - 1], fill=(92, 92, 92))
            sp = Image.fromarray(t["rgba"], "RGBA")
            big = sp.resize((sp.width * z, sp.height * z), Image.NEAREST)
            img.paste(big, (cx, cy), big)
            names = " ".join(lu[len(spec.sprite):] for lu in t["lumps"][:4]) + (" …" if len(t["lumps"]) > 4 else "")
            dr.text((cx, cy + w + 4), names, fill=(214, 208, 196), font=small)
            dr.text((cx, cy + w + 17), short, fill=colour, font=small)
        y += hh
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.crop((0, 0, W, y + 10)).save(out, optimize=True)
    return out


# --------------------------------------------------- the armband proposal
# The CEO (2026-10-22): no symbol is composed on the new set until he has
# seen how it would sit on the band. This is that proposal, a PNG only;
# nothing here reaches the lumps or the overlay.
# The approved D12 symbol, as SDRRA1 carries it (the rig's 7x7 badge,
# rig_core.ARMBAND): K black, W white, R the red frame. Read-only reference.
BADGE = ("RRRRRRR",
         "RKWKKKR",
         "RKWKWWR",
         "RKKKKKR",
         "RWWKWKR",
         "RKKKWKR",
         "RRRRRRR")
SYMBOL = tuple(row[1:-1] for row in BADGE[1:-1])     # the 5x5 black-on-white field
EDGE_FIELD = 0.6        # x the band's extent: the field painted on a band that shows none
BAND_WRAP = 60.0        # degrees of the band's half-turn seen (cylinder); its edges are foreshortened
PROPOSAL_ZOOM = 6
PROPOSAL_VIEWS = (      # (label, sheet, view, foreshortened width of the flat badge, quarter turns)
    ("front (B1)", "turn", 0, 5, 0),
    ("3/4 (B2)", "turn", 1, 6, 0),
    ("profile (B3)", "turn", 2, 7, 0),
    ("death, corpse (L)", "death2", 2, 7, 1),
)


def band_boxes(rgb: np.ndarray, mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """The armband's white fields; where the band shows no field (seen edge-on,
    the front view), the biggest red band's box instead."""
    fields = armband_fields(rgb, mask)
    if fields:
        return fields
    lab, n = label(red_mask(rgb) & mask)
    if n == 0:
        return []
    k = 1 + int(np.argmax(np.bincount(lab.ravel(), minlength=n + 1)[1:]))
    ys, xs = np.nonzero(lab == k)
    if ys.size < MIN_FIELD:
        return []
    return [(int(ys.min()), int(xs.min()), int(ys.max()) + 1, int(xs.max()) + 1)]


def band_axes(rgb: np.ndarray, mask: np.ndarray, box: tuple[int, int, int, int]):
    """(centre, around, along, half-extent around, half-extent along) of the
    armband at a white field: PCA of the red band's pixels near it. The band
    is long AROUND the arm; ALONG is the arm's axis, pointing up the screen
    (or right, for a lying arm). The frame is kept right-handed: never mirrored."""
    y0, x0, y1, x1 = box
    pad = max(y1 - y0, x1 - x0)
    sl = (slice(max(0, y0 - pad), y1 + pad), slice(max(0, x0 - pad), x1 + pad))
    band = (red_mask(rgb[sl]) | white_mask(rgb[sl])) & mask[sl]
    ys, xs = np.nonzero(band)
    pts = np.stack([xs + sl[1].start, ys + sl[0].start], axis=1).astype(np.float64)
    c = pts.mean(axis=0)
    _, v = np.linalg.eigh(np.cov((pts - c).T))
    around, along = v[:, 1].copy(), v[:, 0].copy()   # major axis: round the arm
    if along[1] > 0.3 or (abs(along[1]) <= 0.3 and along[0] < 0):
        along = -along
    if along[0] * around[1] - along[1] * around[0] < 0:
        around = -around
    wy = white_mask(rgb[y0:y1, x0:x1]) & mask[y0:y1, x0:x1]
    wys, wxs = np.nonzero(wy)
    shrink = 1.0
    if len(wys):
        wpts = np.stack([wxs + x0, wys + y0], axis=1).astype(np.float64)
        fc = wpts.mean(axis=0)
        d = wpts - fc
    else:                                            # no field: one on the band's middle
        fc, d, shrink = c, pts - c, EDGE_FIELD
    ha = max(2.0, shrink * float(np.abs(d @ around).max()) + 0.5)
    hl = max(2.0, shrink * float(np.abs(d @ along).max()) + 0.5)
    return fc, around, along, ha, hl


def warp_symbol(rgb: np.ndarray, mask: np.ndarray, wrap: float = BAND_WRAP) -> tuple[np.ndarray, int]:
    """The D12 symbol drawn INTO each armband field at source resolution,
    bent round the arm: across the band, a column's position on screen is
    sin(theta) of its angle round the cylinder, so the far columns crowd
    together; along the arm it follows the band's tilt. Never mirrored."""
    rgb = rgb.copy()
    drawn = 0
    s = math.sin(math.radians(wrap))
    n = len(SYMBOL)
    black = np.array([[SYMBOL[j][i] == "K" for i in range(n)] for j in range(n)])
    for box in band_boxes(rgb, mask):
        c, around, along, ha, hl = band_axes(rgb, mask, box)
        y0, x0, y1, x1 = box
        grow = int(max(ha, hl)) + 1                  # the field may reach past a red box
        box = (max(0, y0 - grow), max(0, x0 - grow), min(rgb.shape[0], y1 + grow), min(rgb.shape[1], x1 + grow))
        y0, x0, y1, x1 = box
        ys, xs = np.mgrid[y0:y1, x0:x1]
        d = np.stack([xs - c[0], ys - c[1]], axis=-1).astype(np.float64)
        a = np.clip((d @ around) / ha, -1, 1)        # -1..1 across the band, on screen
        lv = (d @ along) / hl                         # -1..1 along the arm (up = +1)
        theta = np.arcsin(np.clip(a * s, -1, 1)) / math.radians(wrap)   # -1..1 round the arm
        u, v = (theta + 1) / 2, (1 - lv) / 2
        inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1) & mask[y0:y1, x0:x1]
        ui, vi = np.clip((u * n).astype(int), 0, n - 1), np.clip((v * n).astype(int), 0, n - 1)
        sub = rgb[y0:y1, x0:x1]
        ink = inside & black[vi, ui]
        sub[inside & ~ink] = (226, 220, 206)          # the field (Gemini's, or one painted on an edge-on band)
        sub[ink] = (18, 16, 14)
        drawn += int(ink.sum())
    return rgb, drawn


def stamp_badge(idx: np.ndarray, pal: np.ndarray, width: int = 7, quarter: int = 0) -> np.ndarray:
    """The approved 7x7 badge stamped flat on the field (as the shipped set
    does), its frame trimmed to `width` columns for a band seen at an angle
    (the symbol's 5 columns always whole), turned by quarter turns (a lying
    arm). Rotation keeps the symbol's handedness; it is never flipped."""
    rgba = to_rgba(idx, pal)
    fields = band_boxes(rgba[..., :3], idx >= 0)
    if not fields:
        return idx
    y0, x0, y1, x1 = max(fields, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    cols = {"R": (193, 44, 37), "K": (0, 0, 0), "W": (207, 198, 177)}
    trim = 7 - max(5, min(7, width))
    badge = [row[(trim + 1) // 2: 7 - trim // 2] for row in BADGE]
    arr = np.array([[snap(np.array([[cols[ch]]]), pal)[0, 0] for ch in row] for row in badge])
    arr = np.rot90(arr, -quarter)
    out = idx.copy()
    cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    by, bx = cy - arr.shape[0] // 2, cx - arr.shape[1] // 2
    for j in range(arr.shape[0]):
        for i in range(arr.shape[1]):
            if 0 <= by + j < out.shape[0] and 0 <= bx + i < out.shape[1] and out[by + j, bx + i] >= 0:
                out[by + j, bx + i] = arr[j, i]
    return out


def armband_proposal(spec: EnemySpec = RIFLEMAN, out: Path = ARMBAND_PNG, ref_dir: Path = REF_DIR) -> Path:
    """The PNG for the CEO: per view, the new frame with the empty field, the
    symbol bent into the field at source resolution then reduced with the
    figure (A), the flat approved badge foreshortened at sprite scale (B),
    at x PROPOSAL_ZOOM. Writes nothing but `out`."""
    pal = palette_rgb()
    cuts = plan(spec, ref_dir)
    base = spec.target_height / cuts[spec.ref_sheet].figs[0].mask.shape[0]
    rows = []
    for label_txt, sheet, view, width, quarter in PROPOSAL_VIEWS:
        cut = cuts[sheet].figs[view]
        sc = base * cuts[sheet].scale
        blank = outline(downscale(cut.rgb, cut.mask, sc * PIXEL_ASPECT, sc, pal), pal)
        bent_rgb, _ = warp_symbol(cut.rgb, cut.mask)
        bent = outline(downscale(bent_rgb, cut.mask, sc * PIXEL_ASPECT, sc, pal), pal)
        flat = stamp_badge(blank, pal, width, quarter)
        rows.append((label_txt, [to_rgba(i, pal) for i in (blank, bent, flat)]))
    z = PROPOSAL_ZOOM
    heads = ("new, empty field (goes to the overlay)", "A: symbol bent with the armband, real scale",
             "B: approved 7x7 badge foreshortened (legible)")
    col_w = [max(r[1][k].shape[1] for r in rows) * z + 24 for k in range(3)]
    label_w, head_h, gap = 190, 64, 18
    row_h = [max(i.shape[0] for i in r[1]) * z + gap for r in rows]
    W = label_w + sum(col_w)
    H = head_h + sum(row_h) + 22 * len(ARMBAND_NOTES) + 30
    img = Image.new("RGB", (W, H), (58, 60, 66))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 15)
        small = ImageFont.truetype(artlib.FONT_SMALL, 13)
    except OSError:  # pragma: no cover - no system font
        font = small = ImageFont.load_default()
    dr.text((10, 8), f"{spec.sprite}: armband proposal (D12), x{z}. NOT installed: the CEO decides first.",
            fill=(240, 236, 228), font=font)
    x = label_w
    for k, hd in enumerate(heads):
        dr.text((x, 38), hd, fill=(220, 214, 200), font=small)
        x += col_w[k]
    y = head_h
    for (label_txt, ims), rh in zip(rows, row_h):
        dr.text((10, y + 10), label_txt, fill=(240, 236, 228), font=font)
        x = label_w
        for k, im in enumerate(ims):
            big = Image.fromarray(im, "RGBA").resize((im.shape[1] * z, im.shape[0] * z), Image.NEAREST)
            img.paste(big, (x, y), big)
            x += col_w[k]
        y += rh
    for i, line in enumerate(ARMBAND_NOTES):
        dr.text((10, y + 8 + 22 * i), line, fill=(214, 208, 196), font=small)
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return out


ARMBAND_NOTES = (
    "How it would be done on every frame (automatic, gemini_enemy.py): each frame's armband white field is found",
    "(armband_fields); the PCA of the red gives the arm's axis and the direction round it. A draws the symbol at Gemini's resolution",
    "bent like a cylinder (the far columns crowd together, sin(theta), +-60 degrees) and reduces it with the figure. B stamps the approved",
    "badge at sprite scale, trimming the red frame by the angle (7/6/5 columns, the 5x5 symbol always whole),",
    "turned 90 degrees if the arm is lying. The mirror rotations (6-8) are stamped AFTER the mirror: never flipped.",
    "Where the armband is not visible nothing is put. At real scale the field is 3-5 px: the curvature barely shows and the",
    "symbol blurs (A); B reads, but it is a flat sticker bigger than the armband (like the current set).",
)


# ------------------------------------------- D119: the gunner's preview and install
GUNNER_SHEET_HTML = ROOT / "docs" / "art" / "previews" / "2026-10-23_P4_gunner-gemini.html"
GUNNER_ACTOR = ROOT / "src" / "zscript" / "monsters" / "legion_gunner.zs"
GUNNER_PROVISIONAL = ("legion", "SDLT")       # what SD_LegionGunner wears today (PROVISIONAL-D116)
# legion_gunner.zs: Translation "0:255=%[0.00,0.00,0.00]:[1.25,0.95,0.50]", the palette by luminance
# onto that ramp. Imitated here for the comparison only (NOT VERIFIED against the engine's palettised tint).
GUNNER_TINT = (1.25, 0.95, 0.50)
LINEUP_ZOOM = 3
GUNNER_LINEUP = (   # (label, lump, set): provisional / Gemini / the Legion trooper, then the frontal shot
    ("provisional today B1", "SDLTB1", "prov"), ("new SDLG B1", "SDLGB1", "new"),
    ("Legion trooper SDLT B1", "SDLTB1", "legion"),
    ("provisional F1 (sideways)", "SDLTF1", "prov"), ("new SDLG F1 (frontal)", "SDLGF1", "new"),
    ("new SDLG E1 (aims)", "SDLGE1", "new"),
)
PROVISIONAL_HEADER_START = "// PROVISIONAL LOOK (D116):"
PROVISIONAL_HEADER_END = "// (MOD-SPEC 6.12; tests/test_ep2_enemies.py pins both halves).\n"
INSTALLED_HEADER = (
    "// LOOK (D119): SDLG, his own 70 lumps drawn from the CEO's Gemini sheets by\n"
    "// tools/art/gemini_enemy.py gunner, in assets/sprites/legion_gunner/ (the\n"
    "// trooper's frame letters: design doc section 4). Rotation 1 fires at the\n"
    "// player (F1: the flash in front of the chest).\n")


def tint_provisional(rgba: np.ndarray, tint=GUNNER_TINT) -> np.ndarray:
    """The provisional look: luminance times the tint ramp (an imitation of the Translation)."""
    out = rgba.copy()
    lum = (0.299 * rgba[..., 0] + 0.587 * rgba[..., 1] + 0.114 * rgba[..., 2]) / 255.0
    for c in range(3):
        out[..., c] = np.clip(lum * tint[c] * 255.0, 0, 255).astype(np.uint8)
    return out


def provisional_frames(spec: EnemySpec, sprites_dir: Path = SPRITES_DIR) -> dict:
    """The lumps the actor wears today, tinted, under the new names (SDLTB1 -> SDLGB1)."""
    folder, sprite = GUNNER_PROVISIONAL
    out = {}
    for p in sorted((sprites_dir / folder).glob(f"{sprite}*.png")):
        g = read_grab(p) or (0, 0)
        with Image.open(p) as im:
            img = Image.fromarray(tint_provisional(np.asarray(im.convert("RGBA"))), "RGBA")
        out[spec.sprite + p.stem.upper()[len(sprite):]] = {"src": _b64(img), "w": img.width, "h": img.height,
                                                           "left": g[0], "top": g[1]}
    return out


def gunner_lineup(new_dir: Path, sprites_dir: Path = SPRITES_DIR, z: int = LINEUP_ZOOM) -> Image.Image:
    """The scale check: provisional, new and the Legion trooper on one floor line, at x z."""
    pics = []
    for label_txt, lump, kind in GUNNER_LINEUP:
        p = (new_dir if kind == "new" else sprites_dir / GUNNER_PROVISIONAL[0]) / f"{lump}.png"
        with Image.open(p) as im:
            rgba = np.asarray(im.convert("RGBA"))
        if kind == "prov":
            rgba = tint_provisional(rgba)
        pics.append((label_txt, rgba, read_grab(p) or (0, 0)))
    above = max(g[1] for _, _, g in pics)
    below = max(a.shape[0] - g[1] for _, a, g in pics)
    cell = max(max(g[0], a.shape[1] - g[0]) for _, a, g in pics) * 2 * z + 24
    head, foot = 10, 30
    img = Image.new("RGB", (cell * len(pics), head + (above + below) * z + foot), (59, 61, 66))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 13)
    except OSError:  # pragma: no cover - no system font
        font = ImageFont.load_default()
    floor = head + above * z
    dr.line([(0, floor), (img.width, floor)], fill=(110, 112, 118))
    for i, (label_txt, rgba, (left, top)) in enumerate(pics):
        big = Image.fromarray(rgba, "RGBA").resize((rgba.shape[1] * z, rgba.shape[0] * z), Image.NEAREST)
        img.paste(big, (i * cell + cell // 2 - left * z, floor - top * z), big)
        dr.text((i * cell + 8, floor + below * z + 8), label_txt, fill=(230, 226, 218), font=font)
    return img


def gunner_sheet(spec: EnemySpec, out: Path = GUNNER_SHEET_HTML, out_root: Path = OUT_ROOT,
                 sprites_dir: Path = SPRITES_DIR) -> Path:
    """The CEO's sheet for the gunner (D119): the review sheet's layout with `current`
    the provisional tinted trooper, plus the scale line-up and the frontal-shot check."""
    new_dir = out_root / spec.name
    metrics = json.loads((new_dir / "metrics.json").read_text(encoding="utf-8"))
    item = {
        "id": spec.name, "sprite": spec.sprite, "letters": sorted(spec.rotated),
        "anims": [{"label": a[0], "seq": [list(s) for s in a[1]]} for a in spec.anims],
        "cur": provisional_frames(spec, sprites_dir), "new": _frames_json(new_dir, spec.sprite),
        "derived": list(spec.derived), "notes": spec.notes,
        "gate": metrics.get("gate", []), "reask": metrics.get("reask", []), "symbol": "",
        "sheets": {k: [f["facing"] + (" (mirrored)" if f["mirrored"] else "") for f in v["figures"]]
                   for k, v in metrics["sheets"].items()},
    }
    intro = (
        "<p>The <b>Legion gunner</b> (<code>SD_LegionGunner</code>, final sprite <code>SDLG</code>, 70 lumps "
        "with the trooper's letters: design <code>docs/engine/2026-10-22_P4_ep2-enemies.md</code> §4), taken from today's "
        "Gemini sheets: <code>turn</code>, <code>walkL</code>, <code>walkR</code>, <code>aim_v3</code>, <code>fire</code> "
        "and <code>death_v2</code>. <b>Current</b> = what he wears in the game today: the trooper <code>SDLT</code> tinted brass "
        "(D116; the tint here is an imitation of the <code>Translation</code>, NOT VERIFIED). <b>New</b> = SDLG. Everything ×3 without "
        "smoothing, on its floor line (the light line) with the real offsets. What you asked for in the playthrough (D119): "
        "<b>from the front he fires at you</b>: in F1 the muzzle flash comes out in front of the chest (the provisional one fires sideways). "
        "Height: the Legion trooper's (56 px). Only insignia: the US flag on the shoulder. Nothing installed: the "
        "lumps are in <code>work/art/enemies_gemini/gunner/</code> with the actor patch. Mark OK / NO / ? per row "
        "and press <b>Copy result</b>.</p>"
        f'<h3>Scale and frontal shot (×{LINEUP_ZOOM})</h3><p><img alt="Scale line-up" style="max-width:100%;'
        f'image-rendering:pixelated" src="{_b64(gunner_lineup(new_dir, sprites_dir))}"></p>')
    html = SHEET_TEMPLATE
    for old, new in (
            ("<title>Gemini Enemies</title>", "<title>Gemini Gunner</title>"),
            ("Soviet Doom · Enemies redrawn with Gemini (draft)",
             "Soviet Doom · The Legion gunner with Gemini (draft, D119)"),
            ('const KEY = "sd-2026-10-22_P4_enemies-gemini";', 'const KEY = "sd-2026-10-23_P4_gunner-gemini";'),
            ("Gemini enemies (2026-10-22_P4, D104/D105)", "Gemini gunner (2026-10-23_P4, D119)")):
        if html.count(old) != 1:
            raise ValueError(f"gunner_sheet: the review template changed ({old!r})")
        html = html.replace(old, new)
    i0 = html.index("<p>Each enemy")
    i1 = html.index("</p>", i0) + len("</p>")
    html = html[:i0] + intro + html[i1:]
    html = html.replace("/*ITEMS*/[]", json.dumps([item]))
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def installed_actor(text: str, old: str = "SDLT", new: str = "SDLG") -> str:
    """legion_gunner.zs once SDLG is installed: the header's documented swap
    (MOD-SPEC 6.12: the sprite renamed at the start of each state line, every
    PROVISIONAL-D116 code line deleted), plus the comment lines right above a
    deleted line (the tint's explanation) and the provisional header paragraph
    replaced by what he wears."""
    i0 = text.index(PROVISIONAL_HEADER_START)
    i1 = text.index(PROVISIONAL_HEADER_END, i0) + len(PROVISIONAL_HEADER_END)
    text = text[:i0] + INSTALLED_HEADER + text[i1:]
    out: list[str] = []
    for line in text.splitlines():
        st = line.strip()
        if "PROVISIONAL-D116" in line and st and not st.startswith("/"):
            while out and out[-1].strip().startswith("//") and out[-1].startswith("\t"):
                out.pop()
            continue
        out.append(re.sub(rf"^(\s*){old} ", rf"\g<1>{new} ", line))
    return "\n".join(out) + "\n"


def install_patch(spec: EnemySpec, actor: Path = GUNNER_ACTOR, out_root: Path = OUT_ROOT) -> list[Path]:
    """In work/art/enemies_gemini/<name>/: legion_gunner.zs.patch (a unified
    diff of installed_actor, for `git apply`) and install.sh (copies the lumps
    and applies it). Writes nothing outside work/; the PM runs it on the CEO's OK."""
    import difflib
    d = out_root / spec.name
    guard_out(d)
    have = sorted(p.stem.upper() for p in d.glob(f"{spec.sprite}*.png"))
    if have != lump_names(spec):
        raise SystemExit(f"gemini_enemy: build {spec.name} first (its lumps differ from the spec)")
    text = actor.read_text(encoding="utf-8")
    rel = actor.relative_to(ROOT).as_posix() if actor.is_relative_to(ROOT) else actor.name
    diff = difflib.unified_diff(text.splitlines(keepends=True), installed_actor(text).splitlines(keepends=True),
                                f"a/{rel}", f"b/{rel}")
    patch = d / "legion_gunner.zs.patch"
    patch.write_text("".join(diff), encoding="utf-8", newline="\n")
    sh = d / "install.sh"
    sh.write_text(
        "#!/usr/bin/env bash\n"
        "# D119: install the Legion gunner's SDLG set ONLY after the CEO's OK on\n"
        f"# {GUNNER_SHEET_HTML.relative_to(ROOT).as_posix()}. Run from the repo root.\n"
        "# Also at install, by hand: the licence rows in docs/art/LICENSES.md (as the\n"
        "# Legion trooper's section, sources gem_gunner_*.png), drop SD_LegionGunner\n"
        "# from SWAPS in tests/test_ep2_enemies.py (its provisional test is red once\n"
        "# SDLG exists, by design), and MOD-SPEC 6.12's table row.\n"
        "set -euo pipefail\n"
        f"mkdir -p assets/sprites/{spec.folder}\n"
        f"cp work/art/enemies_gemini/{spec.name}/{spec.sprite}*.png assets/sprites/{spec.folder}/\n"
        f"git apply work/art/enemies_gemini/{spec.name}/legion_gunner.zs.patch\n"
        f"echo \"installed {len(have)} lumps in assets/sprites/{spec.folder}/ and patched {rel}\"\n",
        encoding="utf-8", newline="\n")
    return [patch, sh]


# ------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", help="an enemy (" + ", ".join(ENEMIES) + "), a pending one (" + ", ".join(PENDING)
                                 + "), 'all', 'overlay', 'sheet', 'control' (the D108 armbands' control sheet), "
                                 "'armband' or 'gunner-sheet' (D119: the gunner's preview and install patch)")
    ap.add_argument("--check", action="store_true", help="print the plan only, write nothing")
    import armband_symbol as asym     # imports this module: here, not at the top
    asym.add_symbol_arg(ap)
    args = ap.parse_args(argv)
    if args.what == "all" and not args.check:
        for spec in ENEMIES.values():
            m = build(spec, symbol=args.symbol)
            print(f"gemini_enemy: {spec.name}: {m['lumps']} lumps, {len(m['gate'])} gate notes, "
                  f"symbol {symbol_summary(m)}")
        print(f"gemini_enemy: wrote {review_sheet().relative_to(ROOT).as_posix()}")
        if args.symbol != "none":
            print(f"gemini_enemy: wrote {control_sheet().relative_to(ROOT).as_posix()}")
        args.what = "overlay"
    if args.what == "control":
        print(f"gemini_enemy: wrote {control_sheet().relative_to(ROOT).as_posix()}")
        return 0
    if args.what == "overlay":
        out = write_overlay(overlay_plan())
        print(f"gemini_enemy: wrote {out.relative_to(ROOT).as_posix()} (+ .txt)")
        return 0
    if args.what == "sheet":
        print(f"gemini_enemy: wrote {review_sheet().relative_to(ROOT).as_posix()}")
        return 0
    if args.what == "gunner-sheet":
        print(f"gemini_enemy: wrote {gunner_sheet(GUNNER).relative_to(ROOT).as_posix()}")
        for f in install_patch(GUNNER):
            print(f"gemini_enemy: wrote {f.relative_to(ROOT).as_posix()}")
        return 0
    if args.what == "armband":
        print(f"gemini_enemy: wrote {armband_proposal().relative_to(ROOT).as_posix()}")
        return 0
    spec = ENEMIES.get(args.what) or PENDING.get(args.what)
    if spec is None:
        ap.error(f"unknown enemy {args.what!r}")
    if args.check:
        for k, c in plan(spec).items():
            print(k, "bg", c.bg, "helmet", c.helmet, "scale", round(c.scale, 3),
                  [(f.mask.shape[1], f.mask.shape[0], f.facing, f.mirrored, f.painted, f.edges, f.marker)
                   for f in c.figs])
        return 0
    m = build(spec, symbol=args.symbol)
    print(f"gemini_enemy: {m['lumps']} lumps -> work/art/enemies_gemini/{spec.name}/ (base scale {m['base_scale']}), "
          f"symbol {symbol_summary(m)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
