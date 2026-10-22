"""Enemy sprite sets from Gemini model sheets (D104/D105: "redo the enemies, let Gemini improve them").

    python tools/art/gemini_enemy.py rifleman            # lumps + metrics into work/art/enemies_gemini/rifleman/
    python tools/art/gemini_enemy.py legion|storm        # the Legion trooper (SDLT), the hybrid stormtrooper (SDHS)
    python tools/art/gemini_enemy.py all                 # every enemy, then the overlay and the sheet
    python tools/art/gemini_enemy.py rifleman --check    # print the plan (sheets, figures, facings, scales) only
    python tools/art/gemini_enemy.py overlay             # every built enemy -> work/overlays/sd-draft-enemies.pk3
    python tools/art/gemini_enemy.py sheet               # the CEO's review sheet (docs/art/previews/...)
    python tools/art/gemini_enemy.py armband             # the armband-symbol PROPOSAL (not installed anywhere)

Input: the PM's Gemini sheets in work/art/reference/enemies/gemini/gem_<enemy>_<pose>.png
(gitignored, never pushed, D77): one row of figures on a flat background that
is magenta-ish but not exactly #FF00FF (pale pink, dark magenta). A standing
pose sheet holds the five views front, 3/4 front, profile, 3/4 back, back;
the death sheets hold rotation-0 frames.

Output: the SAME lumps the enemy ships today in assets/sprites/<folder>/
(same frame letters, same rotations, same names), RGBA with hard alpha, in
palette v2, each with its grAb offsets: `left` = the canvas' half width on
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
                           The CEO's D12 symbol is NOT composed (CEO,
                           2026-10-22, D105): see `armband` for the proposal
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
  7. downscale           - premultiplied box filter, alpha >= 1/2, palette v2
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


# ------------------------------------------------------------------ specs
@dataclass(frozen=True)
class Sheet:
    """One Gemini image: `count` figures in a row, left to right."""
    file: str
    count: int
    facing: tuple[str, ...] = ()     # per figure: front/back/left/right/auto (side views)
    scale_ref: int | None = 0        # the figure whose helmet sets the sheet's scale; None: 1.0
    sole: int = 0                    # source rows of derived sole under a figure touching the bottom edge


@dataclass(frozen=True)
class Src:
    """Where a lump's picture comes from."""
    sheet: str
    view: int                        # figure index on the sheet
    tilt: float = 0.0                # degrees leaning back (a derived pain frame)
    blood: int = 0                   # procedural blood: 0 none, 1-3 spray, 4-6 pool (the gib)


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


STAND = ("front", "left", "left", "left", "back")
SIDES_AUTO = ("front", "auto", "auto", "auto", "back")

RIFLEMAN = EnemySpec(
    name="rifleman", sprite="SDRR", folder="rifleman",
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
    derived=(   # shown to the CEO (Spanish)
        "B y D: la misma vista de pie (turn); Gemini da dos zancadas (A = walkL, C = walkR) y la vista quieta",
        "G2-G8 (dolor): la vista de pie inclinada 9 grados hacia atrás; G1 es el dolor de Gemini (death, figura 1)",
        "M-U (reventón, XDeath): Gemini no tiene hoja; son los frames de muerte con sangre procedural (chorro y luego charco)",
        "rotaciones 6-8: las 4-2 en espejo (fusil y brazalete cambian de brazo, como los pares espejo de Doom)",
    ),
    anims=(
        ("andar (See: A A B B C C D D, 4 tics)", (("A", 8), ("B", 8), ("C", 8), ("D", 8)), True),
        ("disparar (Missile: E 10, F 8, E 8)", (("E", 10), ("F", 8), ("E", 8), ("B", 12)), True),
        ("dolor (Pain: G 6)", (("B", 20), ("G", 6), ("B", 14)), True),
        ("morir (Death: H I J K 5, L)", (("H", 5), ("I", 5), ("J", 5), ("K", 5), ("L", 45)), True),
        ("reventar (XDeath: M-T 5, U)", tuple((c, 5) for c in "MNOPQRST") + (("U", 45),), True),
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
        "B y D: la vista de pie (turn); A = walkL, C = walkR",
        "G2-G8 (dolor): la vista de pie inclinada 9 grados; G1 = el dolor de Gemini (death, figura 1)",
        "H-L (muerte): las 5 figuras de la hoja death tal cual (dolor, impacto, cayendo, casi en el suelo, tumbado)",
        "M-U (reventón, XDeath): sin hoja de Gemini; los frames de muerte con sangre procedural (chorro y charco)",
        "rotaciones 6-8: las 4-2 en espejo. La bandera: Gemini la pintó en el hombro DERECHO del soldado "
        "(izquierda de la imagen de frente), coherente en las 5 vistas; con el espejo pasa al otro hombro en "
        "2-3 (Gemini dibujó la 3/4 y el perfil mirando a la derecha) y queda en su hombro en 7-8. "
        "A escala de juego mide ~3x2 px: se acepta, como la escopeta que cambia de mano. Para que sea exacto "
        "basta pedir a Gemini las 3 vistas del otro lado (ver la lista) y ponerlas como override de 2-4",
        "brazalete: ninguno (la Legión no lleva; la bandera no se toca: armband='none')",
    ),
    anims=(
        ("andar (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("disparar (Missile: E 10, F 10, E 10)", (("E", 10), ("F", 10), ("E", 10), ("B", 12)), True),
        ("dolor (Pain: G 3, G 3)", (("B", 20), ("G", 6), ("B", 14)), True),
        ("morir (Death: H I J K 5, L)", (("H", 5), ("I", 5), ("J", 5), ("K", 5), ("L", 45)), True),
        ("reventar (XDeath: M-T 5, U)", tuple((c, 5) for c in "MNOPQRST") + (("U", 45),), True),
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
    armband_side="right",
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
        "B y D: la vista de pie (turn); A = walkL, C = walkR",
        "E y F: la misma carga (aim) dos veces (la clase pide E F 8 tics antes de G); G = fire (el rayo). "
        "El cuerpo a cuerpo (Melee) usa los mismos E F G",
        "H2-H8 (dolor): la vista de pie inclinada 9 grados; H1 = el dolor de Gemini (death, figura 1)",
        "I-M (muerte): las 5 figuras de la hoja death tal cual (la 2 con las chispas, la 5 con el humo)",
        "N-U (reventón, XDeath): sin hoja de Gemini; los frames de muerte con sangre procedural",
        "botas: las seis hojas (193 px) cortan las suelas en la última fila; se añade una suela oscura "
        "de 5 px de origen (~1 px en juego) bajo cada figura que toca el borde",
        "brazo mecánico: medido por el brazalete (brazo izquierdo) en las vistas de frente y espalda de las "
        "6 hojas, el cuerpo NO está invertido en ninguna (el brazo mecánico grande es siempre el derecho, a la "
        "izquierda de la imagen de frente). Lo que cambia es el ARMA: en turn/walk el cañón-taladro sale del "
        "brazo mecánico; en aim/fire el cañón de energía sale del brazo izquierdo (el del brazalete) y el "
        "mecánico cuelga. Espejar aim/fire invertiría el cuerpo y la bola saltaría de lado al pasar de andar "
        "a disparar, así que la regla (armband_side) no espeja ninguna vista; si el CEO quiere el rayo en el "
        "brazo mecánico, se pide de nuevo a Gemini (ver la lista)",
        "rotaciones 6-8: las 4-2 en espejo (brazo mecánico y brazalete cambian de lado, como en el fusilero)",
        "brazalete: rojo con el campo blanco VACÍO (D105); la cruz blanca de Gemini se pinta a blanco liso (modo box)",
    ),
    anims=(
        ("andar (See: A A B B C C D D, 3 tics)", (("A", 6), ("B", 6), ("C", 6), ("D", 6)), True),
        ("atacar (Missile: E F 8, G 6)", (("E", 8), ("F", 8), ("G", 6), ("B", 14)), True),
        ("dolor (Pain: H 2, H 2)", (("B", 20), ("H", 4), ("B", 14)), True),
        ("morir (Death: I 8 J 8 K 6 L 6, M)", (("I", 8), ("J", 8), ("K", 6), ("L", 6), ("M", 45)), True),
        ("reventar (XDeath: N-T 5, U)", tuple((c, 5) for c in "NOPQRST") + (("U", 45),), True),
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
ENEMIES = {"rifleman": RIFLEMAN, "legion": LEGION, "storm": STORM}


# ------------------------------------------------------------- palette
def palette_rgb() -> np.ndarray:
    return np.array(palette.colours(2), dtype=np.int32)


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


def split_merged(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Cut a component holding two figures at its emptiest column (away from its ends)."""
    cols = np.flatnonzero(mask.any(axis=0))
    c0, c1 = cols[0], cols[-1]
    m = int((c1 - c0) * SPLIT_MARGIN)
    counts = mask[:, c0 + m:c1 - m + 1].sum(axis=0)
    cut = c0 + m + int(counts.argmin())
    left = mask.copy()
    left[:, cut:] = False
    return left, mask & ~left


def figures(fg: np.ndarray, count: int) -> list[np.ndarray]:
    """The `count` figures of a sheet, left to right, each a bool mask with its satellites."""
    lab, n = label(fg)
    areas = np.bincount(lab.ravel(), minlength=n + 1)
    areas[0] = 0
    comps = [lab == i for i in range(1, n + 1) if areas[i] >= MIN_PIECE]
    comps.sort(key=lambda c: -int(c.sum()))
    if not comps:
        raise ValueError("no figure on the sheet")
    big = [c for c in comps if c.sum() >= FIGURE_FRAC * comps[0].sum()]
    rest = [c for c in comps if c.sum() < FIGURE_FRAC * comps[0].sum()]
    while len(big) < count:            # two figures merged (touching flashes)
        widest = max(range(len(big)), key=lambda i: np.ptp(np.flatnonzero(big[i].any(axis=0))))
        a, b = split_merged(big.pop(widest))
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


def blank_armband(rgb: np.ndarray, mask: np.ndarray, mode: str = "blank") -> tuple[np.ndarray, int]:
    """Paint white whatever lies INSIDE an armband's white field (a symbol
    Gemini drew): in the field's box, a pixel with white on both sides in
    its row AND in its column (a broken ring still encloses). Mode `box`:
    the field's whole box (within the figure) goes white, so a white symbol
    on the red (a cross) becomes a plain white patch; a field bigger than
    FIELD_BOX_MAX is not an armband and is left. Mode `none`: nothing.
    Returns (rgb, pixels painted)."""
    rgb = rgb.copy()
    painted = 0
    if mode == "none":
        return rgb, 0
    for y0, x0, y1, x1 in armband_fields(rgb, mask, loose=mode == "box"):
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
        inside = ((cols > first_x) & (cols < last_x)) | ((rows > first_y) & (rows < last_y))
        hole = inside & ~white & ~red_mask(box) & mask[y0:y1, x0:x1]
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


def place_frame(pics: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], tuple[int, int]]:
    """One canvas for every picture of a frame letter: legs' axis at `left`,
    the last row FEET_SINK under `top`. Returns ({lump: canvas}, (left, top))."""
    half, above, below = 0.0, 0, 0
    anchors = {}
    for lump, idx in pics.items():
        ax, last = feet_anchor(idx)
        floor = last - FEET_SINK
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
def lump_names(spec: EnemySpec) -> list[str]:
    names = [f"{spec.sprite}{f}{r}" for f in sorted(spec.rotated) for r in range(1, 9)]
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
              armband_side: str | None = None) -> SheetCut:
    bg = estimate_background(rgb)
    fg = key_background(rgb, bg)
    sc = SheetCut(tuple(round(float(v)) for v in bg))
    for i, m in enumerate(figures(fg, sheet.count)):
        edges = touched_edges(m)
        c_rgb, c_mask = crop(rgb, m)
        sole = sheet.sole if "bottom" in edges else 0
        c_rgb, c_mask = add_sole(c_rgb, c_mask, sole)
        c_rgb, painted = blank_armband(c_rgb, c_mask, armband)
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


def plan(spec: EnemySpec, ref_dir: Path = REF_DIR) -> dict[str, SheetCut]:
    cuts = {k: cut_sheet(load_rgb(ref_dir / s.file), s, spec.armband, spec.armband_side)
            for k, s in spec.sheets.items()}
    ref = cuts[spec.ref_sheet]
    ref_h = ref.figs[0].mask.shape[0]
    band = max(4, int(HELMET_BAND * ref_h))
    for k, s in spec.sheets.items():
        if s.scale_ref is not None:
            cuts[k].helmet = helmet_width(cuts[k].figs[s.scale_ref].mask, band)
    ref_helmet = ref.helmet or 1
    for k, s in spec.sheets.items():
        cuts[k].scale = ref_helmet / cuts[k].helmet if s.scale_ref is not None else 1.0
    return cuts


def render(cut: Cut, scale: float, pal: np.ndarray, tilt_deg: float = 0.0, mirror: bool = False,
           blood: int = 0, seed: int = 0) -> np.ndarray:
    rgb, mask = cut.rgb, cut.mask
    if mirror:
        rgb, mask = rgb[:, ::-1], mask[:, ::-1]
    if tilt_deg:
        # lean back: away from the facing (views facing left lean right); front/back lean right a little
        rgb, mask = tilt(rgb, mask, tilt_deg if not mirror else -tilt_deg)
    idx = downscale(rgb, mask, scale * PIXEL_ASPECT, scale, pal)
    idx = outline(idx, pal)
    return add_blood(idx, blood, pal, seed)


def build(spec: EnemySpec, out_dir: Path | None = None, ref_dir: Path = REF_DIR) -> dict:
    pal = palette_rgb()
    out_dir = out_dir or OUT_ROOT / spec.name
    guard_out(out_dir)
    cuts = plan(spec, ref_dir)
    base = spec.target_height / cuts[spec.ref_sheet].figs[0].mask.shape[0]
    frames: dict[str, dict[str, np.ndarray]] = {}
    for letter, rot in spec.rotated.items():
        over = dict(rot.override)
        pics = {}
        for r in range(1, 9):
            src = over.get(r)
            if src is not None:
                sc = cuts[src.sheet]
                pics[f"{spec.sprite}{letter}{r}"] = render(sc.figs[src.view], base * sc.scale, pal,
                                                           src.tilt, False, src.blood)
                continue
            sc = cuts[rot.sheet]
            pics[f"{spec.sprite}{letter}{r}"] = render(sc.figs[VIEW_OF_ROT[r]], base * sc.scale, pal,
                                                       rot.tilt, r in MIRRORED_ROTS)
        frames[letter] = pics
    for n, (letter, src) in enumerate(sorted(spec.single.items())):
        sc = cuts[src.sheet]
        frames[letter] = {f"{spec.sprite}{letter}0": render(sc.figs[src.view], base * sc.scale, pal,
                                                            src.tilt, False, src.blood, seed=7000 + n)}
    written, grabs = [], {}
    for letter in sorted(frames):
        canv, grab = place_frame(frames[letter])
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
    }
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    return metrics


# ------------------------------------------------------------------ gate
def quality_gate(spec: EnemySpec, cuts: dict, written=None) -> list[str]:
    """What the build could not do cleanly, in Spanish for the CEO: art cut
    by a sheet edge (with or without a derived sole), a front/back view
    whose armband side could not be read or had to be mirrored, a lump set
    that is not the spec's."""
    out = []
    for k, c in cuts.items():
        for i, f in enumerate(c.figs):
            where = f"{spec.sheets[k].file} figura {i + 1}"
            cut = [e for e in f.edges if not (e == "bottom" and f.sole)]
            if cut:
                out.append(f"{where}: el dibujo toca el borde ({', '.join(cut)}): cortado")
            if f.sole:
                out.append(f"{where}: botas cortadas por el borde inferior, suela derivada ({f.sole} px)")
            if spec.armband_side and spec.sheets[k].facing and f.facing in ("front", "back"):
                if f.marker is None:
                    out.append(f"{where}: no se lee el lado del brazalete (sin comprobar)")
                elif f.mirrored:
                    out.append(f"{where}: cuerpo invertido respecto a turn: espejado")
    if written is not None and sorted(written) != lump_names(spec):
        out.append("los lumps escritos no son el conjunto de la spec")
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
            "sheets": {k: [f["facing"] + (" (espejo)" if f["mirrored"] else "") for f in v["figures"]]
                       for k, v in metrics["sheets"].items()},
        })
    html = SHEET_TEMPLATE.replace("/*ITEMS*/[]", json.dumps(items))
    guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


SHEET_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Enemigos Gemini</title>
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
  <h1>Soviet Doom · Enemigos rehechos con Gemini (borrador)</h1>
  <span class="prog"><b id="pDone">0</b> / <span id="pAll">0</span> juzgados</span>
  <button class="primary" id="copyTop">Copiar resultado</button><span class="copied" id="copiedTop"></span>
</div></header>
<div class="wrap">
<p>Cada enemigo: el <b>actual</b> (instalado) frente al <b>nuevo</b> (de las hojas de Gemini, D104/D105), ampliados ×3 sin suavizado,
sobre su línea de suelo (la raya clara) con los offsets reales. Enemigos: fusilero <code>SDRR</code>, soldado de la Legión
<code>SDLT</code>, stormtrooper híbrido <code>SDHS</code>. Mismos nombres de lump: el overlay
<code>work/overlays/sd-draft-enemies.pk3</code> los sustituye al cargarlo después del mod. En los dos del Reich el brazalete va
con el cuadro blanco <b>vacío</b> (decisión del CEO, 2026-10-22, D105); la propuesta del símbolo está aparte en
<code>docs/art/previews/2026-10-22_P4_rifleman-armband-proposal.png</code>. Marca OK / NO / ? por fila y pulsa <b>Copiar resultado</b>.</p>
<div id="enemies"></div>
<h2>Nota general</h2>
<textarea id="general" placeholder="Algo en general"></textarea>
<h3>Resultado</h3>
<textarea id="result" readonly></textarea>
<p><button class="primary" id="copyBottom">Copiar resultado</button><span class="copied" id="copiedBottom"></span> <button id="reset">Borrar respuestas</button></p>
<p class="meta">Herramienta: <code>tools/art/gemini_enemy.py</code> (clave del fondo por imagen, figuras por componentes, orientación y escala
normalizadas, filtro de caja premultiplicado, paleta v2, contorno, offsets con los pies en el suelo). Las hojas de Gemini no salen de
<code>work/</code> (D77); esta hoja solo lleva los sprites derivados. Nada instalado: lo instala el PM con tu OK. NO VERIFICADO en GZDoom (D26).</p>
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
function box(set, names){
  // one stage size for a group of lumps: the union of their extents about (left, top)
  let l = 0, r = 0, u = 0, d = 0;
  for (const n of names) { const f = set[n]; if (!f) continue;
    l = Math.max(l, f.left); r = Math.max(r, f.w - f.left); u = Math.max(u, f.top); d = Math.max(d, f.h - f.top); }
  return {l, r, u, d, w: l + r, h: u + d};
}
function stage(f, b, id){
  if (!f) return `<div class="stage" style="width:${b.w*Z}px;height:${b.h*Z}px"></div>`;
  return `<div class="stage" style="width:${b.w*Z}px;height:${b.h*Z}px"><div class="floor" style="top:${b.u*Z}px"></div>` +
    `<img ${id ? `id="${id}"` : ""} src="${f.src}" width="${f.w*Z}" height="${f.h*Z}" style="left:${(b.l-f.left)*Z}px;top:${(b.u-f.top)*Z}px" alt=""></div>`;
}
function row(id, title, body){
  ROWS.push({id, title});
  return `<div class="card"><div class="row" id="r-${id}" data-id="${id}"><div><b>${esc(title)}</b>${body}</div>
    <div class="vote"><div class="btns"><button class="ok" data-v="ok">OK</button><button class="no" data-v="no">NO</button><button class="q" data-v="q">?</button></div>
    <textarea class="note" placeholder="Notas (qué pedir otra vez a Gemini, qué cambiar…)">${esc(st(id).n)}</textarea></div></div></div>`;
}
function rotStrip(set, sp, L){
  const names = [1,2,3,4,5,6,7,8].map(r => sp + L + r), b = box(set, names);
  return `<div class="strip">` + names.map(n => `<div class="cell">${stage(set[n], b)}${n.slice(4)}</div>`).join("") + `</div>`;
}
function build(){
  let html = "";
  for (const it of ITEMS) {
    html += `<h2>${esc(it.id)} <code>${it.sprite}</code></h2><p class="meta">Derivado (no dibujado por Gemini):</p><ul class="meta">` +
      it.derived.map(d => `<li>${esc(d)}</li>`).join("") + `</ul>` +
      ((it.gate || []).length ? `<p class="meta">Gate de calidad (medido):</p><ul class="meta">` + it.gate.map(d => `<li>${esc(d)}</li>`).join("") + `</ul>` : "") +
      ((it.reask || []).length ? `<p class="meta">Pedir otra vez a Gemini:</p><ul class="meta">` + it.reask.map(([f, p]) => `<li><code>${esc(f)}</code>: ${esc(p)}</li>`).join("") + `</ul>` : "") +
      `<p class="meta">Orientación leída por hoja: ` + Object.entries(it.sheets).map(([k, v]) => `<b>${k}</b> ${v.join(", ")}`).join(" · ") + `</p>`;
    for (const L of it.letters) {
      html += row(`${it.id}-${L}`, `Fotograma ${L}: las 8 rotaciones (arriba actual, abajo nuevo)`,
        `<h3>actual</h3>${rotStrip(it.cur, it.sprite, L)}<h3>nuevo</h3>${rotStrip(it.new, it.sprite, L)}`);
    }
    const singles = Object.keys(it.new).filter(n => n.endsWith("0")).sort();
    const bs = box(it.new, singles), bc = box(it.cur, singles);
    html += row(`${it.id}-death`, `Muerte y reventón (rotación 0): ${singles.map(n => n[4]).join(" ")}`,
      `<h3>actual</h3><div class="strip">` + singles.map(n => `<div class="cell">${stage(it.cur[n], bc)}${n[4]}</div>`).join("") +
      `</div><h3>nuevo</h3><div class="strip">` + singles.map(n => `<div class="cell">${stage(it.new[n], bs)}${n[4]}</div>`).join("") + `</div>`);
    it.anims.forEach((a, k) => {
      const id = `${it.id}-anim${k}`;
      html += row(id, `Animación en bucle: ${a.label}`,
        `<div class="rots" data-anim="${id}">rotación: ` + [1,2,3,4,5,6,7,8].map(r => `<button data-r="${r}" class="${r===1?"on":""}">${r}</button>`).join("") +
        `</div><div class="pair"><div class="cell" id="${id}-cur"></div><div class="cell" id="${id}-new"></div></div>`);
    });
  }
  document.getElementById("enemies").innerHTML = html;
  document.getElementById("pAll").textContent = ROWS.length;
  ROWS.forEach(r => paint(r.id));
  for (const it of ITEMS) it.anims.forEach((a, k) => startAnim(it, a, `${it.id}-anim${k}`, 1));
}
const TIMERS = {};
function lumpFor(set, sp, L, rot){ return set[sp + L + rot] ? sp + L + rot : (set[sp + L + "0"] ? sp + L + "0" : null); }
function startAnim(it, a, id, rot){
  clearTimeout(TIMERS[id + "c"]); clearTimeout(TIMERS[id + "n"]);
  for (const [which, set] of [["cur", it.cur], ["new", it.new]]) {
    const names = a.seq.map(([L]) => lumpFor(set, it.sprite, L, rot)).filter(Boolean), b = box(set, names);
    const el = document.getElementById(`${id}-${which}`);
    el.innerHTML = stage(set[names[0]], b, `${id}-${which}-img`) + (which === "cur" ? "actual" : "nuevo");
    let i = 0;
    const step = () => {
      const [L, tics] = a.seq[i], n = lumpFor(set, it.sprite, L, rot), f = set[n], img = document.getElementById(`${id}-${which}-img`);
      if (f && img) { img.src = f.src; img.width = f.w * Z; img.height = f.h * Z; img.style.left = (b.l - f.left) * Z + "px"; img.style.top = (b.u - f.top) * Z + "px"; }
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
  const L = [`Enemigos Gemini (2026-10-22_P4, D104/D105): ${done}/${ROWS.length} juzgados`];
  for (const r of ROWS) { const s = st(r.id), n = (s.n || "").trim().replace(/\s+/g, " ");
    L.push(`${r.id}: ${label[s.v] || "sin juzgar"}${n ? ` — «${n}»` : ""}`); }
  const g = (document.getElementById("general").value || "").trim().replace(/\s+/g, " ");
  if (g) L.push(`General: «${g}»`);
  document.getElementById("result").value = L.join("\n");
}
function copy(which){
  const t = document.getElementById("result"), msg = document.getElementById(which);
  summary();
  const ok = () => { msg.textContent = "copiado"; setTimeout(() => msg.textContent = "", 2500); };
  const fallback = () => { t.focus(); t.select(); try { document.execCommand("copy") ? ok() : (msg.textContent = "selecciona y Ctrl+C abajo"); } catch (e) { msg.textContent = "selecciona y Ctrl+C abajo"; } };
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
document.getElementById("reset").addEventListener("click", () => { if (confirm("¿Borrar las respuestas y notas de esta hoja?")) { S = {}; save(); document.getElementById("general").value = ""; build(); summary(); } });
document.getElementById("general").value = S._general || "";
build(); summary();
</script>
</body>
</html>
"""



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
    ("frente (B1)", "turn", 0, 5, 0),
    ("3/4 (B2)", "turn", 1, 6, 0),
    ("perfil (B3)", "turn", 2, 7, 0),
    ("muerte, cadaver (L)", "death2", 2, 7, 1),
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
    heads = ("nuevo, campo vacio (va al overlay)", "A: simbolo curvado con el brazalete, escala real",
             "B: insignia aprobada 7x7 escorzada (legible)")
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
    dr.text((10, 8), f"{spec.sprite}: propuesta del brazalete (D12), x{z}. NO instalada: el CEO decide antes.",
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
    "Como se haria en todos los frames (automatico, gemini_enemy.py): en cada frame se busca el campo blanco del brazalete",
    "(armband_fields); el ACP del rojo da el eje del brazo y el sentido alrededor. A dibuja el simbolo a la resolucion de Gemini",
    "doblado como un cilindro (las columnas lejanas se juntan, sen(theta), +-60 grados) y lo reduce con la figura. B estampa la insignia",
    "aprobada a escala de sprite, recortando el marco rojo segun el angulo (7/6/5 columnas, el simbolo 5x5 siempre entero),",
    "girada 90 grados si el brazo esta tumbado. Las rotaciones espejo (6-8) se estampan DESPUES del espejo: nunca se invierte.",
    "Donde el brazalete no se ve no se pone nada. A escala real el campo mide 3-5 px: la curvatura apenas se distingue y el",
    "simbolo se emborrona (A); B se lee, pero es una pegatina plana mas grande que el brazalete (como el set actual).",
)


# ------------------------------------------------------------------ CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", help="an enemy (" + ", ".join(ENEMIES) + "), 'all', 'overlay', 'sheet' or 'armband'")
    ap.add_argument("--check", action="store_true", help="print the plan only, write nothing")
    args = ap.parse_args(argv)
    if args.what == "all" and not args.check:
        for spec in ENEMIES.values():
            m = build(spec)
            print(f"gemini_enemy: {spec.name}: {m['lumps']} lumps, {len(m['gate'])} gate notes")
        print(f"gemini_enemy: wrote {review_sheet().relative_to(ROOT).as_posix()}")
        args.what = "overlay"
    if args.what == "overlay":
        out = write_overlay(overlay_plan())
        print(f"gemini_enemy: wrote {out.relative_to(ROOT).as_posix()} (+ .txt)")
        return 0
    if args.what == "sheet":
        print(f"gemini_enemy: wrote {review_sheet().relative_to(ROOT).as_posix()}")
        return 0
    if args.what == "armband":
        print(f"gemini_enemy: wrote {armband_proposal().relative_to(ROOT).as_posix()}")
        return 0
    spec = ENEMIES.get(args.what)
    if spec is None:
        ap.error(f"unknown enemy {args.what!r}")
    if args.check:
        for k, c in plan(spec).items():
            print(k, "bg", c.bg, "helmet", c.helmet, "scale", round(c.scale, 3),
                  [(f.mask.shape[1], f.mask.shape[0], f.facing, f.mirrored, f.painted, f.edges, f.marker)
                   for f in c.figs])
        return 0
    m = build(spec)
    print(f"gemini_enemy: {m['lumps']} lumps -> work/art/enemies_gemini/{spec.name}/ (base scale {m['base_scale']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
