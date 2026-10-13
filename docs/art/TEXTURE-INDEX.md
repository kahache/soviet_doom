# Texture index

Living document. Owner: `art-director`. Contract with `level-designer` and
`mod-engineer`: a lump name listed here is the name the map and the PK3 use.
**Renaming = updating this table before the file.** Russian mirror:
`docs/ru/art/TEXTURE-INDEX.md`.

Status values: `proposed` (in a preview, not yet in `assets/`), `approved`
(CEO said yes; file lives in `assets/`), `discarded` (CEO said no; reason kept
so it is not proposed again), `IWAD` (referenced by name from the base IWAD,
nothing redistributed). Transitional values, always with the reason:
`pending in-map review` (the CEO decides on seeing it in GZDoom; for that
purpose, and only that one, the file may already sit in `assets/` and the
PK3 — it is still not approved), `approved pending …` (yes, conditional on
something the CEO still has to confirm; not in `assets/` yet), `proposed vN`
(redrawn after a verdict, awaiting the next one; may also sit in `assets/`
for an in-map verdict, same rule). `tools/art/make_preview.py` reads this
column to label each card of the preview.

Origin codes (ART-BIBLE §2): (a) own procedural script + seed, (b) free pack
with licence, (c) CEO material.

## Set "Soviet base" — batch 1 (F2)

Preview: `docs/art/previews/2026-10-12_2239_F2_batch1-soviet-base.html`
(mirror `docs/ru/art/previews/…`; supersedes the 2026-10-09_0127 sheet, which
the CEO judged on 2026-10-12 — the 11 textures other than `SDSTAR1` are
byte-identical to that sheet). Generator `tools/art/gen_soviet_base.py`,
`BATCH_SEED` 1977; the seed column is `BATCH_SEED + offset`. Palette
`docs/art/palette.json` v1 (162 colours). Approved files live in
`assets/textures/soviet_base/` (walls) and `assets/flats/soviet_base/`
(flats), copied byte for byte from `work/` (checked by `tests/test_art.py`).

CEO verdict 2026-10-12 on the 0127 sheet, verbatim: «Palette OK · Fonts OK ·
SDCONC1 OK · SDCONC2 duda (habrá que ver como queda) · SDSTAR1 NOT OK ·
SDSTEL1 OK · SDDOOR1 OK · SDPOSTR1 NOT OK -> habrá que ver como hacer bien el
Lenin, luego lo trabajamos aparte · SDPOSTR2 -> me gusta, pendiente de
confirmar la traducción del texto · SDFLR1 OK · SDFLR2 OK · SDFLR3 OK ·
SDCEIL1 OK · SDCEIL2 OK». Gate G2 (≥ 8 approved): **12 of 12 approved**
(count as of 2026-10-13). Ten on the sheet: the 8 unconditional ones,
`SDPOSTR2` (its only condition, the Russian wording, confirmed by the CEO on
2026-10-12) and `SDPOSTR1` v4 (approved 2026-10-12 at 128×256 from the
15-cell sweep). Two in the map: `SDCONC2` and `SDSTAR1` v5 sat in `assets/`
and the PK3 so the CEO could judge them inside MAP01 v1, and he approved
both while walking it in GZDoom on 2026-10-13 (~15:40). CEO, verbatim, on
`SDCONC2`: «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas»; on
`SDSTAR1`: «la apruebo, preciosa». G2 was signed PASS on the 8
unconditional ones; see `docs/qa/GATE-REVIEWS.md`.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCONC1` | wall | 64×128 | yes | prefab concrete panels, running bond, grime under joints | (a) seed 1978 | approved | 2026-10-12 |
| `SDCONC2` | wall | 64×128 | yes | concrete with worn red stripe at mid height | (a) seed 1979 | approved 2026-10-13 (in-map review): as built, with the hangar's three bands; CEO on the 2026-10-12 sheet: "we'll see how it looks", then walking MAP01 v1: «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas» | 2026-10-13 |
| `SDSTAR1` | wall | **128×128** | yes (plaque centred) | concrete with a painted plaque 84×108: gold star above hammer and sickle on red, 1 px dark outline. v2 mirrored the emblem; v3 rebuilt it from the CEO's reference; v4 took the hammer butt to the bottom-right corner; **v5 (variant D1, CEO 2026-10-12)**: hammer head lowered to mid-height (`HAMMER_HEAD_C` y 0.26 → 0.46) and the sickle tip moved onto the outer arc's own end, removing the loose spike the CEO reported ("un palo raro hacia arriba"). Widened to 128 in the same pass because at 64 the lower half of the emblem closed into a blob. Check sheet `tools/art/emblem_check.py`; orientation, handle slope and butt position guarded by `tests/test_art.py` | (a) seed 1980 | approved 2026-10-13 (in-map review, v5): CEO walking MAP01 v1, «la apruebo, preciosa» | 2026-10-13 |
| `SDSTEL1` | wall | 64×128 | yes | military-green riveted steel plates, chipped paint, rust under rivets | (a) seed 1981 | approved | 2026-10-12 |
| `SDDOOR1` | wall (door) | 128×128 | no | bunker steel door: riveted frame, green leaf, locking wheel, star and "7" stencils, hazard stripe | (a) seed 1982; text Impact.ttf | approved | 2026-10-12 |
| `SDPOSTR1` | wall | 128×256 | no (single poster) | Lenin poster: the 1920 Zhukov photograph posterised to four flat palette inks, cream printed border, gold rule and a 46 px band carrying «ЛЕНИН ЖИВ». Four rounds: v1 constructivist silhouette (CEO rejected), v2 naive threshold (PM rejected, no face), v3 hand-drawn silhouette and features (CEO: "no se parece a el EN NADA" — the likeness lives in the photograph, not in a traced outline), **v4 = sweep cell 4C, chosen by the CEO 2026-10-12** from a 15-cell parameter sheet. Slogan rendered through a hard-cut mask: Pillow's antialiasing had invented 95 off-palette colours and `check_pk3` rejected the first build | (a) `tools/art/gen_lenin.py` + (b) `work/art/reference/lenin_1920_zhukov.jpg`, public domain | **approved 2026-10-12** | 2026-10-12 |
| `SDPOSTR2` | wall (mural) | 128×128 | no | cosmonautics mural: rocket, rays, stars, «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» | (a) seed 1984; text Impact.ttf | approved (CEO: "me gusta"; the Russian wording, its only condition, confirmed by the CEO the same day) | 2026-10-12 |
| `SDFLR1` | flat | 64×64 | yes (line continuous on x=2..8) | hangar concrete floor with worn yellow lane line | (a) seed 1985 | approved; 44 px seam repair 2026-10-13 (note below) | 2026-10-12 |
| `SDFLR2` | flat | 64×64 | yes | plain hangar concrete floor, cracks, oil wear | (a) seed 1986 | approved | 2026-10-12 |
| `SDFLR3` | flat | 64×64 | yes | grey two-tone Soviet floor tiles, dark grout | (a) seed 1987 | approved | 2026-10-12 |
| `SDCEIL1` | flat | 64×64 | yes (joint on edges) | concrete ceiling panel with fluorescent lamp | (a) seed 1988 | approved | 2026-10-12 |
| `SDCEIL2` | flat | 64×64 | yes (joint on edges) | plain concrete ceiling panel with damp stain | (a) seed 1989 | approved | 2026-10-12 |

**`SDFLR1` repair, 2026-10-13 (BUG-ART-001, commit 5c9bb1d).** QA found that
vector strokes were clipped at the canvas, so the hairline crack on the three
floors died at the tile border although the row promised "tiles: yes". The
fix is `Overlay.line_tiled` in `tools/art/artlib.py` (each stroke drawn once
in place and once per wrapped neighbour); the PM then copied the regenerated
flat into `assets/`. Measured against the previous file: **44 pixels differ,
1 % of the flat, all on the seam** (row 0, column 0, and the bottom-right
corner, rows 52-63 × columns 45-63) where the crack now carries across the
edge. Same generator, same seed, no hand-painted pixel; a defect repair to an
approved texture, not a change of art, so the approval of 2026-10-12 stands.
The before/after was shown to the CEO on the switch sweep sheet (below).

Not in this batch (deliberately): anything of the two enemy factions (F5),
exterior/sky textures, animated textures (ANIMDEFS is `mod-engineer`'s). The
switches followed as batch 2 (next section).

## Set "Soviet base" — batch 2, switches (F2)

Sweep sheet: `docs/art/previews/2026-10-13_0952_F2_batch2-switch-sweep.html`
(four variants × two states, each on `SDCONC1` and `SDSTEL1`, at 1×, 4× and
point-sampled to 16 px tall; the sheet still calls the lumps `SDSWT1/2`, the
working name before the CEO's verdict). Evidence of the installed set:
`docs/art/previews/2026-10-13_1005_F2_switches-all-four.png`. Generator
`tools/art/gen_switch.py`, `BATCH_SEED` 2077, seed = `BATCH_SEED + offset`
(A 1, B 2, C 3, D 4); both states of a variant share the seed so only the
switch moves, never the panel. Palette v1, nothing added. The generator
writes `SDSWT_<variant>_<state>.png` under `work/`; the files were renamed on
install to the engine's role names, Doom's own convention: **1 = off,
2 = on, variant letter last**.

CEO verdict 2026-10-13 on the sweep, verbatim: «yo por mí mete todos, así
tenemos diversidad» — all four variants approved rather than one (commit
4083883). Variant A was relaid first: the CEO saw its board, painted word and
lamp overlapping ("se pisan unas cosas a otras"); the three are now stacked
bottom-up with declared gaps and `gen_switch.py` refuses to import if they
touch (`tests/test_generators.py`, `SwitchLayoutTests`). Every switch
carries the «ПУСК» ("start") stencil in Impact, so all eight are
text-bearing lumps (see the regeneration rule in ART-BIBLE §7).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDSW1A` | wall (switch, off) | 64×128 | no | Rubilnik: knife switch on a cream bakelite board, brass jaws, red grip, blade swung down; indicator lamp below, dark | (a) `tools/art/gen_switch.py` variant A, seed 2078; text Impact.ttf | approved | 2026-10-13 |
| `SDSW2A` | wall (switch, on) | 64×128 | no | same panel, blade closed into the jaws, lamp lit cream | (a) `tools/art/gen_switch.py` variant A, seed 2078; text Impact.ttf | approved | 2026-10-13 |
| `SDSW1B` | wall (switch, off) | 64×128 | no | domed push button in a steel bezel, red when dead | (a) `tools/art/gen_switch.py` variant B, seed 2079; text Impact.ttf | approved | 2026-10-13 |
| `SDSW2B` | wall (switch, on) | 64×128 | no | same button, cream lens with white core and glow | (a) `tools/art/gen_switch.py` variant B, seed 2079; text Impact.ttf | approved | 2026-10-13 |
| `SDSW1C` | wall (switch, off) | 64×128 | no | round lens (dark olive glass) over a vertical slot, lever block at the bottom | (a) `tools/art/gen_switch.py` variant C, seed 2080; text Impact.ttf | approved | 2026-10-13 |
| `SDSW2C` | wall (switch, on) | 64×128 | no | same panel, lens lit, lever block at the top | (a) `tools/art/gen_switch.py` variant C, seed 2080; text Impact.ttf | approved | 2026-10-13 |
| `SDSW1D` | wall (switch, off) | 64×128 | no | hazard-chevron border, dead lit bar, handle at the left of its slot | (a) `tools/art/gen_switch.py` variant D, seed 2081; text Impact.ttf | approved | 2026-10-13 |
| `SDSW2D` | wall (switch, on) | 64×128 | no | same panel, bar lit cream with glow, handle at the right | (a) `tools/art/gen_switch.py` variant D, seed 2081; text Impact.ttf | approved | 2026-10-13 |

Which pair goes on which MAP01 switch is `level-designer`'s call
(`docs/levels/`); the `SWITCHES` definition is `mod-engineer`'s
(`docs/engine/MOD-SPEC.md`).

Also started in batch 2, no verdict yet and nothing in `assets/`: a first
metro sweep, `docs/art/previews/2026-10-13_0952_F2_batch2-metro-first-pieces.html`
(`tools/art/gen_metro.py`). Its rows are added here when it is proposed
formally.

Candidates for later batches (not started): painted dado wall (green oil
paint lower half + whitewash), concrete corner/pilaster, steel door variant
for keys (red/yellow/blue trims), exterior concrete with night sky,
launch-pad gantry steel. (Crate and locker moved to batch 3, below.) Not
a candidate any more: a 128-high composite dado for the hangar as an
alternative to `SDCONC2` — the CEO approved `SDCONC2` in its three hangar
bands on 2026-10-13, so that alternative is discarded (the painted dado
above stays a candidate for other rooms).

## Set "Soviet base" — batch 3, props (F3)

Sweep: `docs/art/previews/2026-10-13_1439_F3_batch3-props-sweep.html`
(mirror `docs/ru/art/previews/…`). Generator `tools/art/gen_props.py`,
`BATCH_SEED` 3077, seed = 3077 + 10·row + variant (A=1 … D=4). Palette v1,
nothing added. **No typeface:** stencilled numbers and arrows are drawn
from segment data, so every lump here reproduces byte for byte on both
machines. Asked for by `level-designer` as A5 (`docs/levels/MAP01-zarya-7.md`
§10) for MAP01 v2. Columns are value families, dark to pale: A dark 4BO
planks, B green steel case, C khaki planks with a diagonal brace, D pale
pine with black straps. Art-director and PM both recommended **C** for the
three crate pieces and **D** for the locker; column B disappears on
`SDSTEL1`.

CEO verdict 2026-10-13, verbatim: «apruebo el arreglo de la fuente y cajas C
y D» — column **C** for the three crate pieces, **D** for the locker, as
drawn. That also closes the open question of the sweep: C **keeps its
`khaki_olive`** (no repaint in `rust_brown` wood) and keeps its stencilled
numbers. Khaki is otherwise reserved for the Reich's flesh, so the crates
are a CEO-approved exception with a watch item for F5 (ART-BIBLE §6.2).
The generator names files by cell (`R1C_SDCRAT1.png`, …, `R4D_SDLOCK1.png`
in `work/art/batch3/props/`); they were renamed to the bare lump name on
install and copied byte for byte (`tests/test_art.py` matches them by
content). 64×64 and 128×64 are new wall sizes in `assets/` with this batch.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCRAT1` | wall | 64×64 | yes (one crate per tile) | crate face, khaki planks with a diagonal brace and stencilled number; also the ends of `SDCRAT2`. Cell R1-C | (a) gen_props R1, variant C, seed 3090 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D») | 2026-10-13 |
| `SDCRAT2` | wall | 128×64 | yes | long crate in three bays, the hangar's low cover. Cell R2-C | (a) gen_props R2, variant C, seed 3100 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D») | 2026-10-13 |
| `SDCRTOP1` | flat | 64×64 | yes | crate lid with cross batten, seen from the catwalk. Cell R3-C | (a) gen_props R3, variant C, seed 3110 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D») | 2026-10-13 |
| `SDLOCK1` | wall | 64×128 | yes (a row) | two-door barracks locker, pale pine with black straps. Cell R4-D | (a) gen_props R4, variant D, seed 3121 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D») | 2026-10-13 |

Not installed (the other twelve cells of the sweep, A, B and D of the crates
and A-C of the locker): not chosen, not discarded; they stay in `work/` and
may be proposed again as variety.

## The alphabet (D24) — glyph fix

Not textures, listed here so the index carries every shipped art change.
The alphabet (style C "Mashina", 214 glyphs in `assets/fonts/`) is owned by
`LICENSES.md` ("The alphabet"). **2026-10-13: M, Cyrillic М and W
corrected** at both sizes (six PNGs: `004D`, `041C`, `0057` in
`defsmallfont/` and `bigfont/`) with the CEO's approval, same verdict as
above («apruebo el arreglo de la fuente»). Their slab serifs had been placed
on one side only (QA finding H1); before/after sheet
`docs/art/previews/2026-10-13_1443_F2_font-C-serif-fix.png`.

## IWAD references in use (from `docs/engine/MOD-SPEC.md` §5)

| Name | Kind | Used in | Status |
|---|---|---|---|
| `STARTAN2` | wall 64×128 | MAP01 (F0 room) | IWAD, to be replaced by `SDCONC1` (approved 2026-10-12) |
| `FLOOR4_8` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDFLR2` (approved 2026-10-12) |
| `CEIL3_5` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDCEIL2` (approved 2026-10-12) |
| `SKY1` | sky | MAPINFO | IWAD, kept until an own sky exists |

## Discarded

| Lump | Date | Reason | What happens instead |
|---|---|---|---|
| `SDPOSTR1` (Lenin poster, v1 silhouette) | 2026-10-12 | CEO: NOT OK, "we'll have to see how to do Lenin right" | the Lenin portrait became a separate commission (ART-BIBLE §8) and the lump name `SDPOSTR1` went to its result: v4, posterised from the public-domain 1920 photograph, approved 2026-10-12 at 128×256 (row above) |
| hangar dado, 128 high (composite steel-below / concrete-above wall, never drawn; the alternative to `SDCONC2` in the hangar, `docs/levels/MAP01-zarya-7.md` deviation 1) | 2026-10-13 | not needed: the CEO approved `SDCONC2` as built in the hangar's three bands, «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas» | `SDCONC2` stays in the hangar |
