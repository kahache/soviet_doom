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
SDCEIL1 OK · SDCEIL2 OK» (CEO: "SDCONC2 doubtful (we'll have to see how it turns out) ... SDPOSTR1 NOT OK -> we'll have to see how to do Lenin properly, then we'll work on it separately ... SDPOSTR2 -> I like it, translation of the text still to be confirmed"). Gate G2 (≥ 8 approved): **12 of 12 approved**
(count as of 2026-10-13). Ten on the sheet: the 8 unconditional ones,
`SDPOSTR2` (its only condition, the Russian wording, confirmed by the CEO on
2026-10-12) and `SDPOSTR1` v4 (approved 2026-10-12 at 128×256 from the
15-cell sweep). Two in the map: `SDCONC2` and `SDSTAR1` v5 sat in `assets/`
and the PK3 so the CEO could judge them inside MAP01 v1, and the CEO approved
both while walking it in GZDoom on 2026-10-13 (~15:40). CEO, verbatim, on
`SDCONC2`: «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas» ("it isn't perfect but I'd leave it like this, it adds colour and fills the 3 bands"); on
`SDSTAR1`: «la apruebo, preciosa» ("I approve it, gorgeous"). G2 was signed PASS on the 8
unconditional ones; see `docs/qa/GATE-REVIEWS.md`.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCONC1` | wall | 64×128 | yes | prefab concrete panels, running bond, grime under joints | (a) seed 1978 | approved | 2026-10-12 |
| `SDCONC2` | wall | 64×128 | yes | concrete with worn red stripe at mid height | (a) seed 1979 | approved 2026-10-13 (in-map review): as built, with the hangar's three bands; CEO on the 2026-10-12 sheet: "we'll see how it looks", then walking MAP01 v1: «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas» ("it isn't perfect but I'd leave it like this, it adds colour and fills the 3 bands") | 2026-10-13 |
| `SDSTAR1` | wall | **128×128** | yes (plaque centred) | concrete with a painted plaque 84×108: gold star above hammer and sickle on red, 1 px dark outline. v2 mirrored the emblem; v3 rebuilt it from the CEO's reference; v4 took the hammer butt to the bottom-right corner; **v5 (variant D1, CEO 2026-10-12)**: hammer head lowered to mid-height (`HAMMER_HEAD_C` y 0.26 → 0.46) and the sickle tip moved onto the outer arc's own end, removing the loose spike the CEO reported ("un palo raro hacia arriba"). Widened to 128 in the same pass because at 64 the lower half of the emblem closed into a blob. Check sheet `tools/art/emblem_check.py`; orientation, handle slope and butt position guarded by `tests/test_art.py` | (a) seed 1980 | approved 2026-10-13 (in-map review, v5): CEO walking MAP01 v1, «la apruebo, preciosa» ("I approve it, gorgeous") | 2026-10-13 |
| `SDSTEL1` | wall | 64×128 | yes | military-green riveted steel plates, chipped paint, rust under rivets | (a) seed 1981 | approved | 2026-10-12 |
| `SDDOOR1` | wall (door) | 128×128 | no | bunker steel door: riveted frame, green leaf, locking wheel, star and "7" stencils, hazard stripe | (a) seed 1982; text Impact.ttf | approved | 2026-10-12 |
| `SDPOSTR1` | wall | 128×256 | no (single poster) | Lenin poster: the 1920 Zhukov photograph posterised to four flat palette inks, cream printed border, gold rule and a 46 px band carrying «ЛЕНИН ЖИВ». Four rounds: v1 constructivist silhouette (CEO rejected), v2 naive threshold (PM rejected, no face), v3 hand-drawn silhouette and features (CEO: "no se parece a el EN NADA" ("it does not look like him AT ALL") — the likeness lives in the photograph, not in a traced outline), **v4 = sweep cell 4C, chosen by the CEO 2026-10-12** from a 15-cell parameter sheet. Slogan rendered through a hard-cut mask: Pillow's antialiasing had invented 95 off-palette colours and `check_pk3` rejected the first build | (a) `tools/art/gen_lenin.py` + (b) `work/art/reference/lenin_1920_zhukov.jpg`, public domain | **approved 2026-10-12** | 2026-10-12 |
| `SDPOSTR2` | wall (mural) | 128×128 | no | cosmonautics mural: rocket, rays, stars, «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» | (a) seed 1984; text Impact.ttf | approved (CEO: "me gusta" ("I like it"); the Russian wording, its only condition, confirmed by the CEO the same day) | 2026-10-12 |
| `SDPOSTR3` | wall | 128×256 | no (single poster) | Stalin poster, the twin of `SDPOSTR1` by commission (CEO: "exactamente como el que hicimos con Lenin, pero con Stalin" ("exactly like the one we did with Lenin, but with Stalin")): the 1930 frontispiece photograph posterised to four flat palette inks, cream printed border, gold rule and the 46 px band carrying «СЛАВА / СТАЛИНУ!» on two lines at Lenin's 19 px, through the same hard-cut mask. **Sweep cell 4C (four inks, cut +0) and the `slava_short` slogan, chosen by the CEO 2026-10-14 (D55)** from `docs/art/previews/2026-10-14_1601_F2_stalin-sweep.png`. Text-bearing and rendered on Windows: regenerated only there (D27). **Placement (2026-10-22, CEO: «que esos posters puedan aparecer en cualquier nivel» ("that those posters can appear in any level")):** every map, always one 128-long line in a room or niche exactly 256 high: MAP01 the hangar's east wall (a 16-deep niche); MAP02 the sealed 1941 shelter (secret S1, its niche since 3d24d39); MAP03 the assembly hall's west wall (niche); MAP04 the yard's station front beside the red door (niche) and the warehouse beside the Legion's banner; MAP05 the station's arrival wall beside the invaders' banners (niche); MAP06 the GUM facade over the square (niche, hung at 64) and the Kremlin courtyard beside the banners; RANGE the gallery's far wall. It stood in for the Marx-Engels pair in some of the slots each map keeps (`POSTER_SLOTS_MARX_ENGELS`) until `SDPOSTR4`/`SDPOSTR5` were approved and hung there (D117). Each map's design document lists its pictures; `tests/test_posters.py` checks them | (a) `tools/art/gen_stalin.py` + (b) `work/art/reference/stalin_1930.jpg`, public domain | **approved 2026-10-14 (D55)** | 2026-10-14 |
| `SDPOSTR4` | wall | 128×256 | no (single poster; the left of a pair) | Marx poster, the left half of the Marx-Engels pair the CEO commissioned (2026-10-22: «haz uno con Marx y Engels» ("make one with Marx and Engels"), following Lenin and Stalin): J. J. E. Mayall's 1875 photograph posterised to four flat palette inks, cream printed border, gold rule and the 46 px band carrying «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» at 17 px, the first half of the Communist Manifesto's closing line, through Lenin's hard-cut mask. **Sweep cell 4D (four inks, cut +9) and the `short` split, chosen by the CEO 2026-10-22 (D117)** from `docs/art/previews/2026-10-22_P4_marx-engels-sweep.png`. Text-bearing, rendered on Windows: regenerated only there (D27). **Placement (D117):** every map and the range, one slot each of `POSTER_SLOTS_MARX_ENGELS`, Engels in the other; where the two share a wall Marx hangs on the left as seen from the room. MAP01 Marx in the hangar's north niche, Engels on the lift room's east wall by the exit; MAP02 the 1941 shelter (secret S1), Marx on the east wall, Engels round the corner on the south wall; MAP03 Marx on the dock beside the arch, Engels in the assembly hall south of the red door; MAP04 Marx on the warehouse's west wall, Engels in the roundhouse over the turntable stairs; MAP05 the catwalk's back wall either side of the yellow door, Marx west (left); MAP06 Marx in the GUM's north hall, Engels in the Kremlin courtyard; MAP07 the command room's south wall either side of its axis, Marx east (left, seen from the room); MAP08 the north quay's north wall either side of the blue door, Marx west (left); MAP09 the laboratory hall, Marx on the north wall beside Lenin, Engels facing him on the south wall; RANGE the gallery's end walls, Marx west, Engels east. `tests/test_posters.py` holds them | (a) `tools/art/gen_marx_engels.py` + (b) `work/art/reference/marx_1875.jpg`, public domain | **approved 2026-10-22 (D117)** | 2026-10-22 |
| `SDPOSTR5` | wall | 128×256 | no (single poster; the right of a pair) | Engels poster, the right half of the pair: William Hall's 1877 photograph posterised the same way, **mirrored** so that he looks towards Marx (as photographed he looks to the right, away from him; the flip changes the likeness, the CEO approved it), with «СОЕДИНЯЙТЕСЬ!» at the pair's 17 px on the row of Marx's second line, so hung side by side the bands read «ПРОЛЕТАРИИ / ВСЕХ СТРАН, СОЕДИНЯЙТЕСЬ!»; alone it still reads. **Sweep cell 4C (four inks, cut +0), mirrored, `pair` alignment, chosen by the CEO 2026-10-22 (D117).** Text-bearing, rendered on Windows (D27). Placement: the other Marx-Engels slot of every map, see `SDPOSTR4` | (a) `tools/art/gen_marx_engels.py` + (b) `work/art/reference/engels_1877.jpg`, public domain | **approved 2026-10-22 (D117)** | 2026-10-22 |
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
tenemos diversidad» ("as far as I am concerned, put them all in, so we have diversity") — all four variants approved rather than one (commit
4083883). Variant A was relaid first: the CEO saw its board, painted word and
lamp overlapping ("se pisan unas cosas a otras" ("things overlap one another")); the three are now stacked
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

Also started in batch 2: the metro's first six pieces,
`docs/art/previews/2026-10-13_0952_F2_batch2-metro-first-pieces.html`
(`tools/art/gen_metro.py`), approved by the CEO on 2026-10-13 (D42). Their
rows are in their own set, "Metro", below.

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
y D» ("I approve the font fix and crates C and D") — column **C** for the three crate pieces, **D** for the locker, as
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
| `SDCRAT1` | wall | 64×64 | yes (one crate per tile) | crate face, khaki planks with a diagonal brace and stencilled number; also the ends of `SDCRAT2`. Cell R1-C | (a) gen_props R1, variant C, seed 3090 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D» ("I approve the font fix and crates C and D")) | 2026-10-13 |
| `SDCRAT2` | wall | 128×64 | yes | long crate in three bays, the hangar's low cover. Cell R2-C | (a) gen_props R2, variant C, seed 3100 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D» ("I approve the font fix and crates C and D")) | 2026-10-13 |
| `SDCRTOP1` | flat | 64×64 | yes | crate lid with cross batten, seen from the catwalk. Cell R3-C | (a) gen_props R3, variant C, seed 3110 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D» ("I approve the font fix and crates C and D")) | 2026-10-13 |
| `SDLOCK1` | wall | 64×128 | yes (a row) | two-door barracks locker, pale pine with black straps. Cell R4-D | (a) gen_props R4, variant D, seed 3121 | approved 2026-10-13 (CEO: «apruebo el arreglo de la fuente y cajas C y D» ("I approve the font fix and crates C and D")) | 2026-10-13 |

Not installed (the other twelve cells of the sweep, A, B and D of the crates
and A-C of the locker): not chosen, not discarded; they stay in `work/` and
may be proposed again as variety.

## Set "Metro" — batch 2, first pieces (F2, D42)

Preview: `docs/art/previews/2026-10-13_0952_F2_batch2-metro-first-pieces.html`
(mirror `docs/ru/art/previews/…`). Generator `tools/art/gen_metro.py`,
`BATCH_SEED` 1935 (the year the Moscow metro opened), seed = 1935 + offset
(1 to 6, in the order of the table). Palette `docs/art/palette.json` v1,
nothing added: the marble is built from `flag_red` low with `rust_brown`
and `plaster_warm` veins, the mosaic ground from `steel_blue` low, the gold
and the brass from `hazard_yellow`. **No typeface:** none of the six carries
text, so they reproduce byte for byte on both machines (measured
2026-10-13: the six regenerated on the Windows PC are byte-identical to the
Mac's renders in `work/art/batch2/metro/`, whose SHA-256 match
`work/MANIFEST-from-mac.txt`, and to the images embedded in the preview).
Approved files live in `assets/textures/metro/` (walls) and
`assets/flats/metro/` (the flat), copied byte for byte from the Mac's
renders; `tests/test_gen_metro.py` holds the installed set to the generator.

CEO verdict 2026-10-13, verbatim: «OK a las 6 piezas de metro» ("OK to the 6 metro pieces") — the
direction and all six pieces, **as drawn in palette v1** (D42). The two
questions that verdict left open are decided since: **palette v2** is in
(D45: a marble red, a cobalt and gold mosaic ramp and the Legion's pink
flesh ramp in the reserved slots; approved textures keep their colours), and
**the mosaic is the star with rays**, as drawn in `SDMOSA1` (D47: «Ok a la
imagen que has puesto del mosaico» ("OK to the image you put up of the mosaic")), so no figure panel is planned. A v2
version of an approved piece is a new proposal for the CEO (the two `_v2`
rows), never a silent requantisation (ART-BIBLE §3). The CEO chose between
them on 2026-10-14 (D56: «mosaico V2» ("mosaic V2")): **`SDMOSA1` is now its palette v2
rendering** (cobalt and gold), installed under the same lump name, and
`gen_metro.py` builds it so by default; the D42 v1 panel stays reachable as
history with `gen_metro.py --mosaic-v1`. **The marble `SDMARB1` stays in
v1.** The other five pieces are palette v1, as drawn.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDTILE1` | wall | 64×128 | yes | glazed cream tile wall, 8 px tiles, warm grout, a few chipped tiles, grime low down | (a) gen_metro, seed 1936 | approved 2026-10-13 (D42: «OK a las 6 piezas de metro» ("OK to the 6 metro pieces")) | 2026-10-13 |
| `SDTILE2` | wall | 64×128 | yes | the same tile above an oil-painted military-green dado (rows 86-127) under a dark rule | (a) gen_metro, seed 1937 | approved 2026-10-13 (D42) | 2026-10-13 |
| `SDMARB1` | wall | 64×128 | yes (veins cross the seam) | polished red marble cladding, pale and dark veins, slab joint at mid height; ox-blood rather than warm marble, a palette v1 limit | (a) gen_metro, seed 1938 | approved 2026-10-13 (D42), as drawn in palette v1 | 2026-10-13 |
| `SDMOSA1` | wall (panel) | 128×128 | as a row (one panel per tile; the ground meets at the side edges) | mosaic panel: smalt-gold five-pointed star, ten rays and a cream ring on a cobalt ground (`mosaic_cobalt`, `mosaic_gold`), resolved on a 4 px tessera grid | (a) gen_metro, seed 1939; palette v2 | approved in palette v2 2026-10-14 (D56: «mosaico V2» ("mosaic V2")), the `SDMOSA1_v2` proposal installed under this name; the star with rays is the mosaic's motif (D47); first approved in palette v1 2026-10-13 (D42), that v1 now history (`gen_metro.py --mosaic-v1`) | 2026-10-14 |
| `SDBRAS1` | wall (pilaster) | 64×128 | yes (caps on the wrap edges) | fluted brass pilaster, tarnished in the flutes, dark ventilation grille in the middle | (a) gen_metro, seed 1940 | approved 2026-10-13 (D42) | 2026-10-13 |
| `SDMFLR1` | flat | 64×64 | yes | polished grey granite floor, 32 px slabs, feldspar speckle, darker than the base-set floors | (a) gen_metro, seed 1941 | approved 2026-10-13 (D42) | 2026-10-13 |
| `SDMARB1_v2` | wall (proposal, replaces `SDMARB1` under that lump name if chosen) | 64×128 | yes (veins cross the seam) | the approved marble, same seed and veins, in palette v2's `marble_red`: warm red stone instead of flag_red's ox-blood | (a) gen_metro --v2, seed 1938; palette v2 (D45) | proposed (sheet `docs/art/previews/2026-10-14_1036_F3_metro-palette-v2.html`, file `work/art/batch2/metro_v2/SDMARB1_v2.png`); the approved v1 stays in `assets/` until the CEO chooses | 2026-10-14 |
| `SDMOSA1_v2` | wall (panel; proposal, replaces `SDMOSA1` under that lump name if chosen) | 128×128 | as a row | the approved star with rays (motif confirmed by the CEO 2026-10-14), same tesserae, on a `mosaic_cobalt` ground with `mosaic_gold` instead of slate and paint yellow | (a) gen_metro --v2, seed 1939; palette v2 (D45) | chosen 2026-10-14 (D56: «mosaico V2» ("mosaic V2"); same sheet, file `work/art/batch2/metro_v2/SDMOSA1_v2.png`): installed byte for byte as `SDMOSA1`, see that row | 2026-10-14 |

Recommended light (ART-BIBLE §4): 96-128 in corridors, bright islands of
160 at the station; the `level-designer` owns the final values.

### Metro fill-out — approved 2026-10-14 (D48)

Preview: `docs/art/previews/2026-10-13_2022_F3_batch2-metro-fill.html`
(English only; the Russian mirror is `translator-ru`'s at the phase close,
D34). Generator `tools/art/gen_metro.py --fill`, same `BATCH_SEED` 1935,
offsets 7 to 16 (the six approved seeds do not move); renders in
`work/art/batch2/metro_fill/`. Palette v1, nothing added, no typeface, no
star, no figure: when they were drawn, palette v2 and the mosaic's motif
were still open, and none of the ten depends on either (both decided
since, D45 and D47). Each card carries 4×, 1×, a 2×2 tile and a
view darkened ×0.5 for orientation (not the engine's colormap; NOT
VERIFIED in GZDoom). The sheet also shows the whole set side by side,
approved and drafts. New families for ART-BIBLE §2: `MEDG` platform edge,
`TUNL` tunnel lining, `TUBB` tubbing, `RAIL` track bed, `MCEIL` metro
ceiling. Known weak points put on record before the CEO looked: the
tubbing's rust bleed reads olive more than brown, and the plain coffer
`SDMCEIL1` is very flat (7 colours).

CEO verdict 2026-10-14, verbatim: «PERFECTO» ("perfect") — all ten **as drawn**, both
tunnels (`SDTUNL1` and `SDTUBB1`) and the chevrons of `SDMEDG1` included
(D48); the two weak points above stand as accepted. The PM copied the ten
byte for byte from `work/art/batch2/metro_fill/` into
`assets/textures/metro/` (walls) and `assets/flats/metro/` (flats);
`tests/test_gen_metro.py` holds them to the generator pixel for pixel and
`tests/test_art.py` to their `work/` source byte for byte. With them the
metro set in `assets/` is sixteen lumps.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDMFLR2` | flat | 64×64 | yes | station hall floor, pale and dark granite in a 32 px checker | (a) gen_metro --fill, seed 1942 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDMFLR3` | flat | 64×64 | along x only (row 63 is the lip; rotate in UDMF) | platform edge from above: dark granite, worn painted yellow warning line, pale coping slabs, dark lip | (a) gen_metro --fill, seed 1943 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDMEDG1` | wall | 64×64 | along x only | platform face towards the track: coping edge, black-and-yellow chevron band, dark damp concrete | (a) gen_metro --fill, seed 1944 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDTUNL1` | wall | 64×128 | yes | running-tunnel concrete cast in boards, damp streaks, two cable bundles on brackets | (a) gen_metro --fill, seed 1945 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDTUBB1` | wall | 128×128 | yes | cast-iron tubbing, two rings by two segments: flanges, ribs, bolts, rust from the joints | (a) gen_metro --fill, seed 1946 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDRAIL1` | flat | 64×64 | along y (one track per 64 px tile) | track bed: oily concrete, creosoted sleepers every 16 px, tie plates, two rails with a polished running edge; no contact rail | (a) gen_metro --fill, seed 1947 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDMCEIL1` | flat | 64×64 | yes | coffered ceiling, whitewashed plaster, two stepped reveals | (a) gen_metro --fill, seed 1948 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDMCEIL2` | flat | 64×64 | yes | the same coffer with a brass ring lamp and an opal glass disc: the station's light source | (a) gen_metro --fill, seed 1949 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDMARB2` | wall | 64×128 | yes | station wall: glazed tile above, red marble below (the `SDMARB1` stone), brass rail on the marble | (a) gen_metro --fill, seed 1950 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |
| `SDTILE3` | wall | 64×128 | yes | tile wall with a ceramic frieze: cream lozenges on green between two dark rules | (a) gen_metro --fill, seed 1951 | approved 2026-10-14 (D48: «PERFECTO» ("perfect")) | 2026-10-14 |

## Set "Factory" «Танкоград» — batch 4 (F3, D66)

Preview: `docs/art/previews/2026-10-14_2017_F3_batch4-factory.html`
(English only; the mirror is `translator-ru`'s at the phase close, D34).
Generator `tools/art/gen_factory.py`, `BATCH_SEED` 4100 (41 for 1941, when
the Chelyabinsk works became «Танкоград»), seed = 4100 + offset; the key
doors replay `SDDOOR1`'s own seed (1977 + 5) for the leaf, and their trim
wear has its own. Written for the factory map, `docs/levels/MAP03-factory.md`
§7 (the generator still says MAP04, its number before D62). **No system
font:** the banner and the pass plates are set from our own alphabet
(`assets/fonts/bigfont/`, D24), so every lump reproduces byte for byte on
both machines. Palette v1 except where the row says v2 (the generator's
`PALETTE_WHY` carries the reason per piece).

CEO verdict 2026-10-14, verbatim: «Me gustan TODAS» ("I like ALL of them") — every piece as drawn,
including **palette v2** for the brick, the Legion flag's canton and the
portal, and the portal in cobalt with white filaments (D66). **D119
(2026-10-23):** the two occupiers' banners `SDFLAG1` / `SDFLAG2` are Soviet
flags now (CEO playtest: they read as part of the setting, not the enemy's),
drawn by `tools/art/gen_soviet_flags.py` on the same `SDBRCK1` pixels under
the same lump names; `tests/test_gen_soviet_flags.py` holds them, and
`gen_factory.py` no longer builds them (seeds 4114/4115 retired). The PM copied
19 of the 21 lumps, every animation frame included, byte for byte from
`work/art/batch4/factory/` into `assets/textures/factory/` (walls) and
`assets/flats/factory/` (flats). **Two approved lumps wait in `work/`**
because the shared validators do not accept them yet: `SDCHAN1` is RGBA
(masked), and `tools/check_pk3.py` and `tests/test_art.py` require indexed
PNGs under `textures/`; `SDSLOG1` is 256×64, which `tests/test_art.py`
does not list as a wall size yet (`check_pk3.py` does since D66). They are
copied as soon as both accept them (`HELD_D66` in
`tests/test_gen_factory.py`). `tests/test_gen_factory.py` holds them to
the generator pixel for pixel and `tests/test_art.py` to their `work/`
source byte for byte. New families for ART-BIBLE §2: `BRCK`, `RUST`,
`CHAN`, `GRAT`, `MOLT`, `PORT`, `GATE`, `WIND`, `SLOG`, `FLAG`; `DOORY` /
`DOORR` extend `DOOR` with the key colour. Two animations (`SDMOLT1-4`,
`SDPORT1-4`, 8 tics a frame) need `ANIMDEFS`, which is `mod-engineer`'s;
until then each shows its first frame. Not yet seen in the engine (D26).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDBRCK1` | wall | 64×128 | yes | soot-stained red factory brick, 16×8 running bond, lime mortar, browner and overfired bricks, soot | (a) gen_factory, seed 4101, palette v2 (`marble_red`) | approved 2026-10-14 (D66: «Me gustan TODAS» ("I like ALL of them")) | 2026-10-14 |
| `SDBRCK2` | wall | 64×128 | yes | the same brick whitewashed to 64 (the works' dado), dark rule on top, flaked lime | (a) gen_factory, seed 4102, palette v2 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDRUST1` | wall | 64×128 | yes | rusted corrugated sheet, surviving galvanising, bolted lap seam, two rust-through holes | (a) gen_factory, seed 4103 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDCHAN1` | wall (masked mid-texture) | 64×128 | no | hanging chain and crane hook on a transparent ground, for a two-sided line; RGBA with hard alpha (ART-BIBLE §2 exception) | (a) gen_factory, seed 4104 | approved 2026-10-14 (D66); installed 2026-10-14 (N6b, masked RGBA accepted by check_pk3 and test_art) | 2026-10-14 |
| `SDFLR4` | flat | 64×64 | yes | cast-iron chequer plate, 32 px plates, lozenges polished by boots, rust between | (a) gen_factory, seed 4105 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDGRAT1` | flat | 64×64 | yes | steel bar grating for the catwalks, panel frame, the dark below | (a) gen_factory, seed 4106 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDMOLT1` | flat (animated, frame 1 of 4) | 64×64 | yes | molten metal, red to white under glowing slag plates; the loop is seamless | (a) gen_factory, seed 4107 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDMOLT2` | flat (animated, frame 2) | 64×64 | yes | molten metal, frame 2 | (a) gen_factory, seed 4107 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDMOLT3` | flat (animated, frame 3) | 64×64 | yes | molten metal, frame 3 | (a) gen_factory, seed 4107 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDMOLT4` | flat (animated, frame 4) | 64×64 | yes | molten metal, frame 4, leads back into frame 1 | (a) gen_factory, seed 4107 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDDOORY` | wall (door) | 128×128 | no | `SDDOOR1` for the yellow lock: yellow frame, ribs and hazard band, yellow pass plate «ПРОПУСК» | (a) gen_factory, seed 4108 (trim); leaf seed 1982; text from bigfont | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDDOORR` | wall (door) | 128×128 | no | `SDDOOR1` for the red lock: red frame, ribs and hazard band, red pass plate «ПРОПУСК» | (a) gen_factory, seed 4109 (trim); leaf seed 1982; text from bigfont | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDPORT1` | wall (animated, frame 1 of 4) | 128×128 | yes | the portal's surface: a cobalt field warped on itself with white filaments | (a) gen_factory, seed 4110, palette v2 (`mosaic_cobalt`) | approved 2026-10-14 (D66: cobalt, white filaments) | 2026-10-14 |
| `SDPORT2` | wall (animated, frame 2) | 128×128 | yes | the portal, frame 2 | (a) gen_factory, seed 4110, palette v2 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDPORT3` | wall (animated, frame 3) | 128×128 | yes | the portal, frame 3 | (a) gen_factory, seed 4110, palette v2 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDPORT4` | wall (animated, frame 4) | 128×128 | yes | the portal, frame 4, leads back into frame 1 | (a) gen_factory, seed 4110, palette v2 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDGATE1` | wall | 128×128 | yes | sliding factory gate, green corrugated sheet in a steel frame, braces, roller track, handle; shut | (a) gen_factory, seed 4111 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDWIND1` | wall | 64×128 | yes | industrial glazing at night, 4×8 panes, one broken, one boarded | (a) gen_factory, seed 4112 | approved 2026-10-14 (D66) | 2026-10-14 |
| `SDSLOG1` | wall (banner) | **256×64** | no | works banner «ТРАКТОРЫ — КОЛХОЗАМ!» ("Tractors for the collective farms!"), cream on kumach, our alphabet at 2× | (a) gen_factory, seed 4113; text from bigfont | approved 2026-10-14 (D66); installed 2026-10-14 (N6b, 256×64 accepted by test_art) | 2026-10-14 |
| `SDFLAG1` | wall | 64×128 | yes (on `SDBRCK1`) | the USSR state flag hung vertically from an iron rod on `SDBRCK1`'s own pixels: plain red 1:2 cloth (50×100) with a sleeve, the gold-bordered red star over the gold hammer and sickle (`SDSTAR1`'s geometry) in the upper hoist corner; no text. Replaces the occupiers' banner (D119) | (a) gen_soviet_flags, seed 6120, palette v2 (only through the brick) | approved 2026-10-23 (D119, D113 standing approval) | 2026-10-23 |
| `SDFLAG2` | wall | 64×128 | yes (on `SDBRCK1`) | a Red Army standard on `SDBRCK1`: wooden staff (left) with a gold spearhead, wall clamps and an iron ferrule, red cloth with a gold border and fringe, the big gold-bordered red star with the hammer and sickle inside, a gold cord ending in a tassel; no text. Replaces the occupiers' banner (D119) | (a) gen_soviet_flags, seed 6121, palette v2 (only through the brick) | approved 2026-10-23 (D119, D113 standing approval) | 2026-10-23 |

Recommended light (ART-BIBLE §4): 112-144 in the halls, the molten metal and
the portal as bright islands (they read as light sources); the
`level-designer` owns the final values.

## Episode 2 «The Road to Moscow» — approved 2026-10-22 (P4, D104, D107)

Preview: `docs/art/previews/2026-10-22_P4_episode2-textures.html` (the
CEO's sheet, in Spanish: each piece alone, as a 3×3 mosaic and in a sample
room). Generators `tools/art/gen_railway.py` (MAP04, `BATCH_SEED` 5400),
`tools/art/gen_dam.py` (MAP05, 5500) and `tools/art/gen_moscow.py` (MAP06,
5600), seed = `BATCH_SEED` + offset; shared machinery `tools/art/ep2lib.py`,
sheet `tools/art/gen_episode2.py`. **No system font:** «НЕФТЬ», «СКЛАД» and
«М2» are set from our own alphabet (`assets/fonts/bigfont/`, D24) and the
digits are 3×5 px drawn in `ep2lib.py`, so every lump reproduces byte for
byte on both machines. Palette v1, except the five bricks (`SDBRCK3`,
`SDKREM1`, `SDKREM2`, `SDBANR1`, `SDSPAS1`), which add palette v2's
`marble_red` and nothing else: v1 has no fired-clay red, the precedent of
`SDBRCK1` (D66).

CEO verdict 2026-10-22: **25/25 pieces, 28 lumps**, all OK except `SDSIGL1`,
marked «?»: «Me gusta, pero como semáforo solo está bien, en mosaico se ve
raro» ("I like it, but it only works on its own, as a signal; as a mosaic it
looks odd"). D107: installed anyway, **for single use only** (its row). The
28 lumps were copied byte for byte from `work/art/episode2/<set>/` into
`assets/textures/<set>/` (walls) and `assets/flats/<set>/` (flats), sets
`railway`, `dam` and `moscow`; `tests/test_gen_episode2.py` holds the
installed files to a fresh render of the generators and `tests/test_art.py`
(`Episode2InstallTests`) to their names, folders and sizes. The water
`SDWATR1-4` animates through `ANIMDEFS` (`flat SDWATR1`, four frames at 8
tics, like Doom's own water; MOD-SPEC §4.3); the two masked lumps `SDKREM2`
and `SDINSL1` are RGBA with hard alpha, declared in `MASKED_TEXTURES`
(`tools/check_pk3.py`) like `SDCHAN1`, for the middle texture of a
two-sided line. MAP06's red marble of Ploshchad Revolyutsii is the approved
`SDMARB1` (D42), reused, not redrawn. **Not yet on any map** (applying them
is the `level-designer`'s next task) and not yet seen in the engine (D26).
New families: ART-BIBLE §2.

### Railway — MAP04, the Sverdlovsk marshalling yard, 1977 (`gen_railway.py`, 5400)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDTRAK1` | flat | 64×64 | yes (rails along y; side by side in x, parallel tracks) | yard track seen from above: granite ballast, Soviet concrete sleepers every 16 px, tie plates and clips, two rails with a polished head and rusty sides | (a) gen_railway, seed 5402 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDBLST1` | flat | 64×64 | yes | loose ballast between the tracks: crushed granite, rust dust and wagon oil | (a) gen_railway, seed 5401 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDWAGN1` | wall | 128×128 | along x | Soviet covered goods wagon, side: red-oxide planking worn to grey wood, steel posts and braces, sole bar, dark underframe, an 8-digit stencilled number (our own pixel digits) | (a) gen_railway, seed 5403 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDTANK1` | wall | 128×128 | along x | black four-axle tank wagon, side: top-lit barrel, riveted ring seams, straps, oil runs under the dome, «НЕФТЬ» ("oil") in cream from our alphabet | (a) gen_railway, seed 5404; text from bigfont | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDARMR1` | wall | 128×128 | along x | armoured-train plate with a red star: olive faded to khaki, riveted 64 px plates, scratches and hits, rust under the rivets, cream-edged star | (a) gen_railway, seed 5405 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDARMR2` | wall | 64×128 | yes | the same armour plate without the star, the fill between `SDARMR1` panels | (a) gen_railway, seed 5406 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDSIGL1` | wall | 64×128 | **no — single use only (D107)** | colour-light signal on its mast against a concrete pillar: black head, three hooded lenses (green, yellow, lit red), shunting plate «М2» from our alphabet. **Level designers: single use only, as a signal or a panel on its own, never as a mosaic** (the CEO: tiled, it looks odd); one 64 px span per signal, on a pillar or a short line, never repeated along a wall or stacked | (a) gen_railway, seed 5407; text from bigfont | approved 2026-10-22 (D107: «?», installed for single use only) | 2026-10-22 |
| `SDBRCK3` | wall | 64×128 | yes | locomotive roundhouse brick: the approved factory-brick recipe, a little lighter and less sooty, with a frieze on top (projecting course, dog-tooth course, projecting course) | (a) gen_railway, seed 5408, palette v2 (`marble_red`) | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDGATE2` | wall | 128×128 | along x | goods-shed sliding door: planks in red-brown paint flaking to the wood, two rails and a brace, steel edge, track with two rollers, hasp and padlock, plate «СКЛАД» ("store") and a big painted 3 | (a) gen_railway, seed 5409; text from bigfont | approved 2026-10-22 (D107) | 2026-10-22 |

Recommended light (art-director's proposal; `level-designer` decides):
outdoors 144-176 under an overcast day, sheds and roundhouse 112-144.

### Dam — MAP05, the Volga dam at Zhiguli (`gen_dam.py`, 5500)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDDAM1` | wall | 64×128 | yes | mass concrete of the dam: board-formwork marks, a lift joint every 64 px, tie holes with white calcite runs | (a) gen_dam, seed 5501 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDDAM2` | wall | 64×128 | along x | the same concrete at the waterline: dark and wet below an irregular mark (72 px from the top), green slime at the foot | (a) gen_dam, seed 5502 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDTURB1` | wall | 128×128 | along x | turbine-generator housing: steel in 4BO green, ribs, two bolted flanges, a brass maker's plate (illegible pixel text and the year 1957), bolted hatch, oil weeping under the flange, concrete plinth | (a) gen_dam, seed 5503 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDCTRL1` | wall | 128×128 | along x (64 px sections: a long board) | Soviet control board: light-grey panels, round gauges with a red zone, a row of pilot lamps (some lit), plates that look like text and say nothing, a mimic diagram of bars and switches on the desk, toggle switches, dark plinth | (a) gen_dam, seed 5504 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDSPIL1` | wall | 64×128 | yes | spillway trash rack: rusty vertical bars and stiffeners in front of running water, foam between the bars | (a) gen_dam, seed 5505 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDWATR1` | flat (animated, frame 1 of 4) | 64×64 | yes | the Volga's water: slow body, crests turning one full phase and drifting one tile per loop; grey-blue from `steel_blue`, never the portal's cobalt | (a) gen_dam, seed 5506 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDWATR2` | flat (animated, frame 2) | 64×64 | yes | the water, frame 2 | (a) gen_dam, seed 5506 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDWATR3` | flat (animated, frame 3) | 64×64 | yes | the water, frame 3 | (a) gen_dam, seed 5506 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDWATR4` | flat (animated, frame 4) | 64×64 | yes | the water, frame 4, leads back into frame 1 | (a) gen_dam, seed 5506 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDINSL1` | wall (masked mid-texture) | 64×128 | along x (cross-arm and conductor cross the tile: a row of strings) | high-voltage suspension insulator string on a transparent ground: cross-arm, clevis, eight glazed brown porcelain discs, clamp and conductor; RGBA with hard alpha, for a two-sided line | (a) gen_dam, seed 5507 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDGRAT2` | flat | 64×64 | yes | galvanised expanded-metal floor over the void (glints of water below), a few rust patches; no frame, so it tiles seamlessly, unlike the factory's `SDGRAT1` panels | (a) gen_dam, seed 5508 | approved 2026-10-22 (D107) | 2026-10-22 |

Recommended light: crest and spillway 160-192, turbine hall 128-160,
galleries 96-128.

### Moscow — MAP06, Red Square and the Kremlin (`gen_moscow.py`, 5600)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCOBL1` | flat | 64×64 | yes | Red Square setts: dark diabase in courses, each course offset, rounded and polished by the parades; dark on purpose so the red wall leads | (a) gen_moscow, seed 5601 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDCOBL2` | flat | 64×64 | along x (rotate in UDMF for the other direction) | the same setts with a line of light granite slabs, the lines that divide the square into fields | (a) gen_moscow, seed 5602 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDKREM1` | wall | 64×128 | yes | Kremlin wall: red brick in stretcher bond, light lime joints, a few restored bricks, rain washes; cleaner and redder than `SDBRCK1` | (a) gen_moscow, seed 5603, palette v2 (`marble_red`) | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDKREM2` | wall (masked mid-texture) | 64×128 | along x | the wall's "swallowtail" merlon: `SDKREM1`'s brick pixel for pixel, cut into an M-shaped merlon with a loophole; the sky shows between merlons and in the notch. RGBA with hard alpha, for a two-sided line on top of the wall | (a) gen_moscow, seed 5603 (replays `SDKREM1`'s on purpose), palette v2 (`marble_red`) | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDGUM1` | wall | 128×128 | along x | one bay of the GUM facade: pale coursed stone, round-arched window (dark glass, white frames, fanlight), voussoirs and keystone, a half rusticated pilaster at each edge, cornice with dentils, sill | (a) gen_moscow, seed 5604 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDTRIB1` | wall | 64×128 | yes | the tribune's polished dark-red granite in 64×32 blocks, black, pink and grey speckle, a soft sheen, a band of black labradorite with blue glints on top | (a) gen_moscow, seed 5605 | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDBANR1` | wall | 64×128 | along x (on `SDKREM1`) | parade banner hung on the Kremlin wall (`SDKREM1`'s pixels): kumach red with folds, gold star and the approved hammer and sickle, gold fringe, pole and brackets; no text (D12) | (a) gen_moscow, seed 5606, palette v2 (only through the brick; the cloth is v1) | approved 2026-10-22 (D107) | 2026-10-22 |
| `SDSPAS1` | wall | 64×128 | yes | Spasskaya tower stone: red brick with white limestone dressings, a frieze of pointed arcading with pendants, white pilasters at the edges, a dentilled string course | (a) gen_moscow, seed 5607, palette v2 (`marble_red`) | approved 2026-10-22 (D107) | 2026-10-22 |

Recommended light: the square 160-192 (the finale, in full daylight), the
GUM interiors 128-144. Reused in MAP06: `SDMARB1` (set "Metro", D42).

## Episode 2, round 2 — approved 2026-10-22 (P4, D112, D113)

Preview: `docs/art/previews/2026-10-22_P4_episode2-textures-round2.html`
(the sheet, in Spanish: each piece alone, as a 3×3 mosaic, in a sample room
and, for the skies, as a panorama). One generator, `tools/art/gen_episode2b.py`
(`BATCH_SEED` 5700, seed = 5700 + offset), on top of `ep2lib.py`,
`gen_factory.py` and `gen_moscow.py`, which it only reads. The pieces MAP04-06
still wore as stand-ins (the "still pending" tables of
`docs/levels/MAP04-transsib.md` §7.2, `MAP05-volga-dam.md` §7.2 and
`MAP06-red-square.md` §8). **No system font:** «СВЕРДЛОВСК / СОРТИРОВОЧНЫЙ»,
«ПРОПУСК», «СТОЙ!» and the GUM's «ТКАНИ», «ОБУВЬ», «ЧАСЫ» are set from our own
alphabet (`assets/fonts/bigfont/`, D24), the digits are `ep2lib.py`'s 3×5
pixels, so every lump reproduces byte for byte on both machines. Palette v1,
except six walls that add a v2 ramp and say why: `SDCLOK1`, `SDMUSE1` and
`SDFLAG3` (`marble_red`, brick), `SDDOORB` (`mosaic_cobalt`, the blue key
colour; v1's `steel_blue` reads grey) and `SDFLAG4` (until D119 both: the
Kremlin brick and the Legion's canton). Never `mosaic_gold` or
`flesh_pink`. **D119 (2026-10-23):** `SDFLAG3` / `SDFLAG4`, the occupiers'
banners on `SDKREM1`, are Soviet flags now (a parade gonfalon and a
battle-torn state flag), drawn by `tools/art/gen_soviet_flags.py` on the same
`SDKREM1` pixels under the same lump names, `marble_red` only through the
brick; `gen_episode2b.py` no longer builds them. Before/after:
`docs/art/previews/2026-10-23_P4_soviet-flags.png`.

**Approved under D113's standing approval** (the CEO approves procedural
textures in advance), **PM gate 2026-10-22**: 21 pieces, 23 lumps, copied
byte for byte from `work/art/episode2b/<set>/` into `assets/textures/<set>/`
(walls and skies) and `assets/flats/<set>/` (flats): sets `sky` (new),
`railway`, `dam` and `moscow` (round 1's folders). `tests/test_gen_episode2b.py`
holds the installed files to a fresh render of the generator and
`tests/test_art.py` (`Episode2InstallTests`) to their names, folders and
sizes. The three masked lumps `SDGRIL1`, `SDHVLT1` and `SDRUBY1` are RGBA with
hard alpha, declared in `MASKED_TEXTURES` (`tools/check_pk3.py`), for the
middle texture of a two-sided line. The skies are declared in `SKY_TEXTURES`
(`SKY_SIZES` = 1024×128). **In `src/lumps/MAPINFO` since 2026-10-22:** MAP04
`sky1 = "SDSKY1"`, MAP05 `sky1 = "SDSKY1"` (the Urals night's dark wooded hills
and broken cloud fit the Zhiguli hills over the dam better than Moscow's
skyline; the two floodlight towers on its east are the yard's, a small
liberty), MAP06 `sky1 = "SDSKY2"`. The other pieces are **not yet on any map**
(applying them is the `level-designer`'s next task) and nothing is seen in
the engine yet (D26). Seed note: this generator's 5700 + offset space
overlaps Episode 3's `gen_arctic.py` (also 5700 + offset); the generators
are different, so no output is shared, but the next batch takes a clear
space (6000+). New families: ART-BIBLE §2.

### Sky — MAPINFO `sky1` of MAP04-06 (`gen_episode2b.py`)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDSKY1` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | the Urals at night over Sverdlovsk: broken cloud with the moon behind it and silvered edges near it, a few stars in the gaps, the warm glow of the city and Uralmash under the cloud, black taiga hills, chimneys with smoke and red obstruction lights, a radio mast and, to the east, the yard's own two floodlight towers. One 360° turn, where Freedoom's `SKY1` (256×128) repeats four times | (a) gen_episode2b, seed 5701 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22); MAPINFO `sky1` of MAP04 and MAP05 | 2026-10-22 |
| `SDSKY2` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | Moscow at night: a low cloud deck lit brownish orange by the city's sodium, colder and darker at the zenith; a skyline of blocks with lit windows, three Stalin high-rises with their stars and the Ostankino tower's spire (1967) with its red lights | (a) gen_episode2b, seed 5702 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22); MAPINFO `sky1` of MAP06 | 2026-10-22 |

### Railway, round 2 — MAP04 (`gen_episode2b.py`)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDWROF1` | flat | 64×64 | yes | goods-wagon roof from above: red-oxide sheet with transverse ribs every 16 px, locomotive soot, rust on the ribs and the plank walkway along y on its brackets | (a) gen_episode2b, seed 5703 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGOND1` | flat | 64×64 | yes | a Soviet open wagon's floor: the discharge flaps (joints, two pressed ribs each, hinges at the sides), rust, coal dust and lumps of coal in the corners | (a) gen_episode2b, seed 5704 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDCAB1` | wall | 128×128 | no (one cab front) | inside a steam locomotive's cab, looking forward: the black riveted boiler backhead, the firebox door with fire at the slot and the air holes, brass boiler and brake gauges, two water glasses, the regulator, red handwheels on the steam pipes and the round cab windows onto the night (a red signal far off) | (a) gen_episode2b, seed 5705 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDCAB2` | wall | 64×128 | along x | the cab's side from inside: green-painted sheet over riveted seams, the sliding window onto the yard at night (a signal, far lights, a reflection), the wooden armrest, a valve handwheel and an enamel plate, a darker boot-scuffed skirting | (a) gen_episode2b, seed 5706 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDSBOX1` | wall | 64×64 | along x | the signal box's glazing seen from the yard at night, lit inside: white-painted glazing bars, warmer light under the hanging lamp, the levers' silhouettes below, one cracked pane; concrete lintel on top and sill below. Rows 8-55 are the 48-high opening | (a) gen_episode2b, seed 5707 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDLEVR1` | flat | 64×64 | along x | the mechanical lever frame from above: the iron bed with its slots on the boards, eight levers painted by function (red signals, black points, blue locks, yellow distant, white spare) with polished grips, three pulled, brass plates 1-8, the boards worn where the signalman stands | (a) gen_episode2b, seed 5708 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDLEVR2` | wall | 64×64 | along x | the lever frame from the front: eight levers out of the arched cast-iron bed, painted by function, polished grip and catch, three pulled towards us, numbered brass plates, the box's green wall behind | (a) gen_episode2b, seed 5709 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRHDR1` | wall | 128×128 | along x | one road's doors of the roundhouse, a pair per tile: two leaves of vertical boards in faded depot green down to the wood, glazing on top (two panes broken, one boarded), rails and braces, black iron strap hinges, a drop bar, soot over the top. No number: roads 2 and 3 and S2's panel wear the same face | (a) gen_episode2b, seed 5710 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDSTAN1` | wall | 256×64 | no (one board) | the station board: white enamel in a steel frame, «СВЕРДЛОВСК» large and «СОРТИРОВОЧНЫЙ» ("marshalling") below in black from our alphabet, a red rule, enamel chipped to rust, runs from the four bolts, soot on top | (a) gen_episode2b, seed 5711; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |

### Dam, round 2 — MAP05 (`gen_episode2b.py`)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDGRIL1` | wall (masked mid-texture) | 64×128 | along x | window bars on a transparent ground: four round bars per tile through two riveted flats, dark paint chipped to rust. RGBA with hard alpha, for the control room's two windows over the hall (middle texture of a two-sided line) | (a) gen_episode2b, seed 5712 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDDOORB` | wall | 128×128 | no (a door) | the blue key door: the recipe of `SDDOORY` and `SDDOORR` (`SDDOOR1`'s green leaf, wheel and rivets) with frame, ribs, plate and hazard band in cobalt and «ПРОПУСК» ("pass") in cream from our alphabet | (a) gen_episode2b, seed 5713; the leaf replays `SDDOOR1`'s seed 1982 like `SDDOORY`/`SDDOORR`; text from bigfont; palette v2 (`mosaic_cobalt`) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDHVLT1` | wall (masked mid-texture) | 64×128 | along x | the substation's high-voltage fence on a transparent ground: galvanised chain-link between angle posts (the post on the tile edge), a top rail, two strands of barbed wire and the Soviet danger plate «СТОЙ!» ("halt!") with the red lightning arrow, tied to the mesh. RGBA with hard alpha | (a) gen_episode2b, seed 5714; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |

### Moscow, round 2 — MAP06 (`gen_episode2b.py`)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCLOK1` | wall | 128×128 | no (one clock face) | the Spasskaya tower's clock: a black dial in a gold ring, gold hour marks and minute dots, a gold inner ring and sun at the centre, gold hands at five to twelve; the dial in a square of white limestone with gold rosettes in the spandrels, on the tower's red brick | (a) gen_episode2b, seed 5715, palette v2 (`marble_red`) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRUBY1` | wall (masked mid-texture) | 128×128 | no (one star) | the Kremlin's ruby star on a transparent ground: five arms of ruby glass, each with a lit and a shaded facet, glowing from inside, gold frame and ribs, a gold inner star; below, the gold ball and the spire's stem. RGBA with hard alpha, for a two-sided line against the sky | (a) gen_episode2b, seed 5716 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGUMS1` | wall | 64×128 | along x | a shopfront of the GUM's galleries: black glass sign with gold letters from our alphabet, «ТКАНИ» ("fabrics"), a round-arched shop window over the dark empty shop, one smashed pane (looting), polished wooden plinth over a brass rail, stone pilasters at the edges | (a) gen_episode2b, seed 5717; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGUMS2` | wall | 64×128 | along x | the same shopfront, «ОБУВЬ» ("shoes"); differs from `SDGUMS1` only in the sign | (a) gen_episode2b, seed 5717; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGUMS3` | wall | 64×128 | along x | the same shopfront, «ЧАСЫ» ("watches") | (a) gen_episode2b, seed 5717; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGUMR1` | flat | 64×64 | yes | the GUM's glass vault from below: the arch's iron rib on the edge, a purlin in the middle, glazing bars, dirty panes dark at night and warmed by the city glow, grime against the iron, two panes missing and one cracked | (a) gen_episode2b, seed 5718 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDMUSE1` | wall | 64×128 | yes | the Historical Museum's red brick with its white dressings: a deeper, browner red than the Kremlin's with fine light joints, a white band of square panels («ширинки») with a brick lozenge each, a row of white pendants below and a white dentilled string course | (a) gen_episode2b, seed 5719, palette v2 (`marble_red`) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDFLAG3` | wall | 64×128 | along x (on `SDKREM1`) | a parade gonfalon on the Kremlin brick `SDKREM1`: red cloth from a wooden crossbar on a staff (right), swallowtail foot with a gold fringe, the bordered star over the hammer and sickle in a gold wreath with a red ribbon, two gold tassels; no text. Replaces the occupiers' banner (D119) | (a) gen_soviet_flags, seed 6122, palette v2 (`marble_red`, only through the brick) | approved 2026-10-23 (D119, D113 standing approval) | 2026-10-23 |
| `SDFLAG4` | wall | 64×128 | along x (on `SDKREM1`) | the USSR state flag after the battle, on `SDKREM1`: as `SDFLAG1` (star and hammer and sickle in the hoist corner) but faded, its foot torn and burnt with two tongues burnt away, five bullet holes with charred rims (the brick shows through), a tear, soot rising from the foot; no text. Replaces the occupiers' banner (D119) | (a) gen_soviet_flags, seed 6123, palette v2 (`marble_red`, only through the brick) | approved 2026-10-23 (D119, D113 standing approval) | 2026-10-23 |

## Episode 3 «The Portal» — approved 2026-10-22 (P4, D112, D113)

Preview: `docs/art/previews/2026-10-22_P4_episode3-textures.html` (the sheet,
in Spanish: each piece alone, as a 3×3 mosaic and in a sample room).
Generators `tools/art/gen_arctic.py` (MAP07, `BATCH_SEED` 5700),
`tools/art/gen_naval.py` (MAP08, 5800) and `tools/art/gen_taiga.py` (MAP09,
5900), seed = `BATCH_SEED` + offset; shared machinery `tools/art/ep3lib.py`
(on top of `ep2lib.py`, read only), sheet `tools/art/gen_episode3.py`. Three
twins replay their pair's seed on purpose and equal it outside the paint:
`SDRWY2` (= `SDRWY1`), `SDHULL2` (= `SDHULL1`), `SDRUBR2` (= `SDRUBR1`).
**No system font:** «471», «ММФ» and «3» are set from our alphabet
(`assets/fonts/bigfont/`, D24), the container number in `ep2lib.py`'s 3×5
digits; the invaders' glyphs are an invented grammar of rings and strokes,
not letters. Palette v1, except the portal rim `SDPRTE1`, which adds palette
v2's `mosaic_cobalt` and nothing else (the look of `SDPORT1-4`, D66).

**Approved under D113's standing approval** (the CEO approves procedural
textures in advance), **PM gate 2026-10-22**: 30 pieces, 36 lumps, copied
byte for byte from `work/art/episode3/<set>/` into `assets/textures/<set>/`
(walls) and `assets/flats/<set>/` (flats), sets `arctic`, `naval` and
`taiga`; `tests/test_gen_episode3.py` holds the installed files to a fresh
render of the generators and `tests/test_art.py` (`Episode3InstallTests`) to
their names, folders and sizes. Two animations in `ANIMDEFS` (MOD-SPEC §4.3):
the radar console `texture SDRADR1`, four frames at **12 tics** (the beam
turns 90° a frame: a 1.4 s sweep), and the acid `flat SDACID1`, four frames
at 8 tics like `SDWATR1`. The masked crane jib `SDCRAN1` is RGBA with hard
alpha, in `MASKED_TEXTURES`. **Not yet on any map** (MAP07-09 still wear
stand-ins; applying the set is the `level-designer`'s next task; their skies
are `SDSKY3-5` since 2026-10-22, below) and not yet seen in the engine (D26). New families: ART-BIBLE §2.

### Arctic — MAP07, the radar station on Novaya Zemlya (`gen_arctic.py`, 5700)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDSNOW1` | flat | 64×64 | yes | wind-packed snow: long sastrugi ridges across the tile, lit on the face that looks up the tile, blue in the lee, the odd glint | (a) gen_arctic, seed 5701 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDICE1` | flat | 64×64 | yes | sea ice: refrozen floes in different blues, white pressure cracks at their edges, veils of frost, rows of trapped bubbles | (a) gen_arctic, seed 5702 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDICE2` | wall | 64×128 | yes | glacier ice wall: wavy annual layers, white bubble bands, a thin vein of moraine gravel, vertical melt runs and fracture facets | (a) gen_arctic, seed 5703 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRADM1` | wall | 128×128 | yes | radome skin: white fibreglass panels of a geodesic dome (staggered rows of triangles, the two families of faces lit differently), flanged bolted joints, frost on the horizontal flanges, dirt streaks | (a) gen_arctic, seed 5704 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDHUT1` | wall | 64×128 | along x | barracks wall of corrugated sheet in faded 4BO green: riveted lap joint, rust at the joint and the foot, feathers of frost on the crests (more lower down), a snowdrift against the base and icicles under the eave | (a) gen_arctic, seed 5705 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRADR1` | wall (animated, frame 1 of 4) | 128×128 | along x | radar console with its round PPI screen: the beam turns 90° a frame leaving a green trail, range rings, heading cross and five echoes that light as the beam passes and fade; grey-blue hammer-finish cabinet, knobs, pilot lamps and plates that look like text and say nothing | (a) gen_arctic, seed 5706 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRADR2` | wall (animated, frame 2) | 128×128 | along x | the radar console, frame 2 | (a) gen_arctic, seed 5706 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRADR3` | wall (animated, frame 3) | 128×128 | along x | the radar console, frame 3 | (a) gen_arctic, seed 5706 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRADR4` | wall (animated, frame 4) | 128×128 | along x | the radar console, frame 4, leads back into frame 1 | (a) gen_arctic, seed 5706 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDHERM1` | wall | 128×128 | no (a door) | hermetic blast door («гермодверь»): steel frame with hazard stripes, a thick 4BO-green leaf with a rubber seal, two locking levers, two hinges, a plate; frost creeping in from every edge, thicker below, icicles from the lintel | (a) gen_arctic, seed 5707 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRWY1` | flat | 64×64 | yes | airfield runway slabs, staggered, with the rows of anti-skid dimples of Soviet PAG plates, packed snow in the joints, powder snow drifting across and dark tyre marks along y | (a) gen_arctic, seed 5708 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRWY2` | flat | 64×64 | along y | the same slabs (same seed) with the white centre line, 40 px painted and 24 bare, worn so the dimples show through | (a) gen_arctic, seed 5708 (replays `SDRWY1`'s on purpose) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |

Recommended light (art-director's proposal; `level-designer` decides):
snowy outdoors 128-160 (the snow is already bright; higher burns it), the
barracks and the radar room 112-144, the radar screen as its own light.

### Naval — MAP08, the submarine base at Severomorsk (`gen_naval.py`, 5800)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDHULL1` | wall | 128×128 | along x | submarine hull side: staggered black anechoic rubber tiles (a few missing, the reddish primer showing), the deck edge against the sky, the row of flooding holes of a Soviet submarine and salt streaks | (a) gen_naval, seed 5801 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDHULL2` | wall | 128×128 | no (one numeral) | the same hull (same seed) with the tactical number «471» painted in white over the tiles, worn where the tiles have shifted; digits from our alphabet | (a) gen_naval, seed 5801 (replays `SDHULL1`'s on purpose); text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRUBR1` | flat | 64×64 | yes | the submarine's deck from above: staggered black anechoic rubber tiles, a worn path along y, the odd lost tile (rusty steel), salt bloom | (a) gen_naval, seed 5802 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDRUBR2` | flat | 64×64 | no (single piece) | the same deck (same seed) with a flush round escape hatch: steel coaming, rubber-clad lid, hinge and a small handwheel. Single piece | (a) gen_naval, seed 5802 (replays `SDRUBR1`'s on purpose) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDROCK1` | wall | 64×128 | yes | the excavated shelters' living rock: dark gneiss in blast facets lit from the upper left, pink feldspar specks, quartz veins, seepage runs, the half-barrels of the perimeter drill holes and a rock bolt | (a) gen_naval, seed 5803 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDROCK2` | flat | 64×64 | yes | the same rock as a ceiling: facets, drips, two bolt plates on the 32 px grid and calcite bloom | (a) gen_naval, seed 5804 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDBULK1` | wall | 128×128 | no (a door) | round watertight door in a grey «шаровый» bulkhead: bare steel coaming, a leaf with a stiffening ring, six lever dogs, two hinges, a red handwheel, the compartment number «3» in red (bigfont), oil and scuffs below | (a) gen_naval, seed 5805; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDNAVC1` | wall | 128×128 | along x | control-room panel: grey-green steel, four black-faced gauges (depth and pressure), the mimic of the submarine's compartments with its pilot lamps, two rows of annunciators (some lit, their labels are dashes) and a row of toggle switches | (a) gen_naval, seed 5806 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDCONT1` | wall | 128×128 | along x | shipping container side: trapezoidal corrugation in faded red, top and bottom rails, corner posts with their castings, rust bleeding from the rails, «ММФ» (the Merchant Fleet) in white from our alphabet, the box number in 3×5 digits and a plate | (a) gen_naval, seed 5807; text from bigfont | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDCRAN1` | wall (masked mid-texture) | 64×128 | yes (by alpha: the two 64 px bays are equal) | a quay crane's jib lattice on a transparent ground: two angle chords, battens every 64 px, zigzag diagonals with gussets and rivets, faded yellow paint and rust. RGBA with hard alpha, for a two-sided line | (a) gen_naval, seed 5808 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDPIER1` | flat | 64×64 | along x (along the quay) | concrete quay from above: slabs with oil stains, a cast-iron bollard on its plate with a mooring line to the edge, the yellow-and-black kerb and the steel angle over the water (at the tile's bottom) | (a) gen_naval, seed 5809 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |

Recommended light: the excavated shelter 96-128, the outer quay 144-160 in
polar day, inside the submarine 112-144.

### Taiga/Alien — MAP09, the portal at Tunguska (`gen_taiga.py`, 5900)

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDBARK1` | wall | 64×128 | yes | birch trunk: chalk-white bark, horizontal lenticels, cracked black plates and the chevron scars of fallen branches, a strip of bark peeling to its orange underside | (a) gen_taiga, seed 5901 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDBARK2` | wall | 64×128 | yes | larch trunk after the fire: deep vertical furrows, charred plates with charcoal's alligator crazing, surviving reddish bark in the furrows, grey ash | (a) gen_taiga, seed 5902 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDLOGW1` | wall | 128×128 | yes | log-cabin wall: round 16 px logs weathered to silver grey with brown in the checks, moss chinking between them and two knots | (a) gen_taiga, seed 5903 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDPEAT1` | flat | 64×64 | yes | peat bog: dark brown fibrous peat, sphagnum tufts and black pools holding a little sky | (a) gen_taiga, seed 5904 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDBURN1` | flat | 64×64 | yes | burnt ground: grey ash on black charcoal, patches of scorched red earth and charred trunks all lying the same way, as the blast left them | (a) gen_taiga, seed 5905 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDMOSS1` | flat | 64×64 | yes | taiga floor: moss cushions, pale reindeer lichen and a few red lingonberries | (a) gen_taiga, seed 5906 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDALNM1` | wall | 128×128 | yes | the invaders' organic metal: a dark membrane with veins glowing acid green, vertebral ribs every 32 px that sway, and two fleshy tubes crossing them with glowing joints | (a) gen_taiga, seed 5907 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDACID1` | flat (animated, frame 1 of 4) | 64×64 | yes | the invaders' acid: thick green body, crests turning yellow, bubbles that grow along the loop and burst, drifting one tile per loop. **A damaging floor: the damage is the map's sector special, not the texture's** (the `level-designer` sets it; this picture only looks the part) | (a) gen_taiga, seed 5908 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDACID2` | flat (animated, frame 2) | 64×64 | yes | the acid, frame 2 | (a) gen_taiga, seed 5908 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDACID3` | flat (animated, frame 3) | 64×64 | yes | the acid, frame 3 | (a) gen_taiga, seed 5908 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDACID4` | flat (animated, frame 4) | 64×64 | yes | the acid, frame 4, leads back into frame 1 | (a) gen_taiga, seed 5908 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDGLYP1` | wall | 64×128 | yes | invader technology plate: dark mottled metal in bevelled panels, two columns of engraved glyphs glowing acid green (with their engraving shadow) and lit channels at the sides; the glyphs are an invented grammar of rings and strokes, not letters | (a) gen_taiga, seed 5909 | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |
| `SDPRTE1` | wall | 64×128 | along y | the portal's frame: a column of the invaders' metal in 16 px segments split by a channel of the portal's cobalt with white filaments (the look of `SDPORT1-4`), the glow spilling onto the metal and filaments cracking it. Symmetrical, serves both sides | (a) gen_taiga, seed 5910, palette v2 (`mosaic_cobalt`) | approved 2026-10-22 (D113 standing approval, PM gate 2026-10-22) | 2026-10-22 |

Recommended light: the burnt taiga 96-128 at night, the cabin 112-144, the
portal and the acid 176-208 as in the foundry (MAP03).

### Sky — MAPINFO `sky1` of MAP07-09 (`gen_episode3_skies.py`, 6000)

Episode 3's own skies, replacing Freedoom's `SKY1` (brown daylight cloud)
on MAP07-09. Same format and method as `SDSKY1`/`SDSKY2`: 1024×128, one
360° turn that wraps in x and never repeats inside it, the horizon at row
100 (`gen_episode2b.HORIZON`), the ground below it; no lettering. Seeds
6000 + offset, the clear space the seed note above asks for. Installed in
`assets/textures/sky/` under D113's standing approval, byte for byte from
`work/art/episode3_skies/sky/` (`tests/test_gen_episode3_skies.py`);
declared in `SKY_TEXTURES`. Preview (panorama at 2×, the wrap seam, two
screen views each): `docs/art/previews/2026-10-22_P4_episode3-skies.png`.
Palette: the aurora has **no green-teal ramp** to use, so `SDSKY3` draws it
with v1's `military_green` (olive) fading into `steel_blue`; a true aurora
green would be a new ramp, **not opened** (CEO's call). `SDSKY5` adds v2's
`mosaic_cobalt` on the D66 precedent, only where the portal's light falls.
Not yet seen in the engine (D26): where GZDoom puts row 100 is NOT VERIFIED.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDSKY3` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | the polar night over Novaya Zemlya: a clear black sky full of stars, three curtains of aurora (a bright green lower seam with rays, grey-blue higher up), the island's glaciated range catching their light, the sea ice to the horizon with broken pressure ridges | (a) gen_episode3_skies, seed 6001, palette v1 | approved 2026-10-22 (D113 standing approval, PM gate pending); MAPINFO `sky1` of MAP07 | 2026-10-22 |
| `SDSKY4` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | the Kola fjord at Severomorsk at night: a low overcast lit brown by the base's sodium, black gneiss cliffs with snow on the ledges and a radio mast, the far shore with the piers' lights, cranes with red lights and two moored submarines, the fjord's mouth open to the sea and a lighthouse on the headland, its beam in the mist and on the black water | (a) gen_episode3_skies, seed 6002, palette v1 | approved 2026-10-22 (D113 standing approval, PM gate pending); MAPINFO `sky1` of MAP08 | 2026-10-22 |
| `SDSKY5` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | the Tunguska taiga at night: torn cloud lit cobalt from below by the portal on the horizon, a pillar of its light into the overcast with white filaments at its foot, the far living taiga's line and, in front, the dead forest of 1908 (stripped trunks standing, snapped tops, felled logs lying away from the portal), black and rimmed with its glow | (a) gen_episode3_skies, seed 6003, palette v2 (`mosaic_cobalt`, only near the portal) | approved 2026-10-22 (D113 standing approval, PM gate pending); MAPINFO `sky1` of MAP09 | 2026-10-22 |

### Sky — MAPINFO `sky1` of MAP01, MAP03 and RANGE (`gen_episode1_skies.py`, 6010)

Episode 1's own skies, replacing Freedoom's `SKY1` (brown daylight cloud)
on MAP01, MAP03 and the practice range. Same format and method as
`SDSKY1-5`: 1024×128, one 360° turn that wraps in x and never repeats
inside it, the horizon at row 100 (`gen_episode2b.HORIZON`), the ground
below it; no lettering. Seeds 6010 + offset. Installed in
`assets/textures/sky/` under D113's standing approval, byte for byte from
`work/art/episode1_skies/sky/` (`tests/test_gen_episode1_skies.py`);
declared in `SKY_TEXTURES`. Preview (panorama at 2×, the wrap seam, two
screen views each): `docs/art/previews/2026-10-22_P4_episode1-skies.png`.
Palette v1 only: MAP03's portal sits in its drum inside the closed shop, so
its cobalt cannot light the clouds and `SDSKY7` takes no v2 ramp. **MAP02
(the metro) has no sky sector and keeps `SKY1`**, which nothing in it shows.
None of MAP01, MAP03 or the range has a sky sector today either (MAP01's
strip over the hangar is open with the CEO, `MAP01-zarya-7.md` §13 point 5):
the skies are set so the day one is opened it shows the right place. Not yet
seen in the engine (D26).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDSKY6` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | the Zarya-7 cosmodrome before a November dawn, 1977: a cold clear sky full of stars, a thin warm dawn band low in the east under streaks of stratus, the flat steppe dusted with snow; far off the launch pad, a Soyuz-type rocket floodlit beside its lattice service tower with red lights, venting, the four floodlight masts and their beams; the base's blocks with lit windows, the assembly hangar with its lit gate, a water tower, a radio mast, a tracking dish, an empty second pad, the road of lamps out to the pad | (a) gen_episode1_skies, seed 6011, palette v1 | approved 2026-10-22 (D113 standing approval, PM gate pending); MAPINFO `sky1` of MAP01 and RANGE (the range is a room of the same base) | 2026-10-22 |
| `SDSKY7` | sky (wall namespace) | 1024×128 | along x (wraps round the full turn) | Tankograd at night: a low cloud deck lit orange from below by the works, colder and darker at the zenith; three blast furnaces with skip bridges, stoves and gas flares, molten slag running down a heap, chimneys with smoke and red lights, the open-hearth shop's row of six stacks, sawtooth halls with lit glazing, a cooling tower and its steam, two gantry cranes, the gate tower's red star; the yard's dirty snow, rails catching the glow, the goods spur coming at us | (a) gen_episode1_skies, seed 6012, palette v1 | approved 2026-10-22 (D113 standing approval, PM gate pending); MAPINFO `sky1` of MAP03 | 2026-10-22 |

## Shell pictures — menu cursor and pause sign (T12, D48)

Not textures: patches the engine finds by name, listed here so the index
carries every shipped picture. Like `TITLEPIC`, `INTERPIC` and `M_DOOM`
(provenance in `LICENSES.md`, "Shell screens") they are the documented
exception to the `SD` prefix (MOD-SPEC §1), and like `M_DOOM` they are
RGBA with hard alpha, not indexed (ART-BIBLE §2), because they are drawn
over something else. Sweep sheet:
`docs/art/previews/2026-10-13_2208_F2_shell-cursor-pause-sweep.html`.
Generator `tools/art/gen_cursor.py` (no seed: nothing in it is random),
five cursor options and three pause signs. The pause words are set in the
installed `SDMENU` folder font, read and never rebuilt, so no system font
is involved and the pictures reproduce byte for byte on the Mac and on
Windows. The generator names files by option (`cursor_B_1.png`,
`pause_P2_en.png` in `work/art/shell_extra/`); they were renamed to the
engine's lump names on install and copied byte for byte
(`tests/test_gen_cursor.py` holds them to the generator, `tests/test_art.py`
to their `work/` source).

CEO verdict 2026-10-14 (D48): menu cursor **B** (hammer and sickle) and
pause sign **P2** (a plaque per language). The cursor blinks through
gzdoom.pk3's own ANIMDEFS (`M_SKULL1` / `M_SKULL2`, 8 tics each), so
nothing in the mod declares it. Only the English plaque is installed: the
Russian one needs the packer to carry a `localized/` variant, which it does
not do yet (MOD-SPEC §10, T12).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `M_SKULL1` | menu patch (cursor, phase 1) | 20×20 | no | option B: the hammer and sickle of `SDSTAR1` v5 (geometry imported from `gen_soviet_base.hammer_sickle()`, never re-traced), gold with a dark-red outline | (a) `tools/art/gen_cursor.py`, `cursor_image("B", 1)`; file `cursor_B_1.png` | approved 2026-10-14 (D48) | 2026-10-14 |
| `M_SKULL2` | menu patch (cursor, phase 2) | 20×20 | no | the same emblem in its second blink phase, pale cream: the blink is the gold lighting up | (a) `tools/art/gen_cursor.py`, `cursor_image("B", 2)`; file `cursor_B_2.png` | approved 2026-10-14 (D48) | 2026-10-14 |
| `M_PAUSE` | pause sign | 77×20 | no | option P2, English: «PAUSE» in `SDMENU` (D22 letterforms, it reads PДUSЭ) on a flag-red plaque with a cream border; the canvas also fits the Russian «ПАУЗА», so a localised variant can match its size | (a) `tools/art/gen_cursor.py`, `pause_image("P2", "en")`; file `pause_P2_en.png` | approved 2026-10-14 (D48); the Russian plaque ships as `localized/textures/M_PAUSE.ru.png` (T24) and the Catalan «PAUSA» as `M_PAUSE.ca.png` (P6, 2026-10-21, seen in the engine), both 77×20 and chosen by `SD_PAUSE_SIGN` | 2026-10-14 |

## Intermission pictures — the operations map and the awards (V3 B1/B3, ADR 013)

Not textures: graphics the intermission draws by name (`graphics/`, MiscPatch),
listed so the index carries every shipped picture. **Proposal, waiting for the
CEO** (political symbols: D113's standing approval does not cover the awards);
installed on the V3 branch only. Preview at 2×, the nine positions of the map,
the stats page over it, the awards page in English and Russian, the awards at
4×: `docs/art/previews/2026-10-23_V3_ops-map-medals.png`. Generators
`tools/art/gen_ops_map.py` (seed 1977; it also writes the intermission script
`src/lumps/SDOPSCR`) and `tools/art/gen_medals.py`; palette v2 (`mosaic_gold`,
`marble_red`, `mosaic_cobalt`); RGBA with hard alpha except the background
(indexed), as the shell's overlays. Positions in the 320×200 space are the
script's, offsets in each PNG's grAb (`tests/test_ops_map.py`). Not yet seen in
the engine (D26).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDOPMAP` | intermission background (indexed) | 320×200 | no | the USSR in olive on a cobalt sea (lighter on the shelf), a dotted 10° graticule, the Volga, Ob, Yenisei, Podkamennaya Tunguska and Lena, the Trans-Siberian dashed in dark red, the coast a dark line, the nine sites as cream rings, the gold hammer and sickle under a red star top left, a cream frame; the top 30 px stay sea for the engine's map name and "Entering" | (a) gen_ops_map, seed 1977, palette v2 | proposal (V3, ADR 013) | 2026-10-23 |
| `SDOPR02`…`SDOPR09` | intermission overlays (RGBA) | per segment | no | the red arrow into MAPnn from the map before, a bowed line with its head 5 px short of the site, dark contour; grAb 0,0, placed at its box's corner by the script | (a) gen_ops_map | proposal (V3, ADR 013) | 2026-10-23 |
| `SDOPSTAR` | intermission overlay (RGBA) | 9×9 | no | a taken site: red star, gold rim, dark contour; grAb at the centre; also the script's `Splat` | (a) gen_ops_map | proposal (V3, ADR 013) | 2026-10-23 |
| `SDOPCUR0`, `SDOPCUR1` | intermission overlays (RGBA) | 17×17 | no | the gold pulse on the site just finished (two radii, 12 tics each); grAb at the centre | (a) gen_ops_map | proposal (V3, ADR 013) | 2026-10-23 |
| `SDOPYAH0` | intermission overlay (RGBA) | 17×17 | no | "you are here": the gold ring the engine blinks on the next site (the script's `Pointer`); grAb at the centre | (a) gen_ops_map | proposal (V3, ADR 013) | 2026-10-23 |
| `SDAWCOU` | award (RGBA) | 24×30 | no | Medal "For Courage": silver disc, three aircraft, the red band of the inscription left blank, a tank; grey pentagonal ribbon with blue edges | (a) gen_medals | proposal (V3, ADR 013; CEO) | 2026-10-23 |
| `SDAWRST` | award (RGBA) | 24×30 | no | Order of the Red Star: faceted red star, silver centre with a red point (no soldier); claret ribbon, grey centre stripe | (a) gen_medals | proposal (V3, ADR 013; CEO) | 2026-10-23 |
| `SDAWRBN` | award (RGBA) | 24×30 | no | Order of the Red Banner: gold wreath, white field, red star, a red banner over the top; red ribbon with white stripes | (a) gen_medals | proposal (V3, ADR 013; CEO) | 2026-10-23 |
| `SDAWPTW` | award (RGBA) | 24×30 | no | Order of the Patriotic War: gold sunburst, red star, crossed rifle and sabre, a red-and-gold centre; claret ribbon, red centre stripe | (a) gen_medals | proposal (V3, ADR 013; CEO) | 2026-10-23 |
| `SDAWHER` | award (RGBA) | 24×30 | no | Gold Star of the Hero of the Soviet Union: faceted gold star on a red ribbon bar framed in gold | (a) gen_medals | proposal (V3, ADR 013; CEO) | 2026-10-23 |

## The alphabet (D24) — glyph fix and German letters

Not textures, listed here so the index carries every shipped art change.
The alphabet (style C "Mashina", 224 glyphs in `assets/fonts/`) is owned by
`LICENSES.md` ("The alphabet"). **2026-10-13: M, Cyrillic М and W
corrected** at both sizes (six PNGs: `004D`, `041C`, `0057` in
`defsmallfont/` and `bigfont/`) with the CEO's approval, same verdict as
above («apruebo el arreglo de la fuente» ("I approve the font fix")). Their slab serifs had been placed
on one side only (QA finding H1); before/after sheet
`docs/art/previews/2026-10-13_1443_F2_font-C-serif-fix.png`.
**2026-10-13: Ä, Ö, Ü and the sharp s (ẞ U+1E9E, ß U+00DF) added** at both
sizes (ten PNGs: `00C4`, `00D6`, `00DC`, `1E9E`, `00DF` in `defsmallfont/`
and `bigfont/`, 214 → 224 glyphs, and copied into `sdmenu/`), **approved for
in-game trial 2026-10-13 (D37)**; proposal sheet
`docs/art/previews/2026-10-13_1730_F5_font-german-umlauts.png`.

## The menu font SDMENU (D31)

Not textures either. `assets/fonts/sdmenu/` (112 glyphs + `font.inf`) is
`bigfont/` with R, N, E, W, A drawn as Я, И, Э, Ш, Д (D22 level 2), for the
main menu and the skill-screen headers. Owned by `LICENSES.md` ("The menu
font SDMENU"). Status: **approved for in-engine trial 2026-10-13 (D31)**.
Reference sheet `docs/art/previews/2026-10-13_1554_F2_menu-sweep.png`.

## IWAD references in use (from `docs/engine/MOD-SPEC.md` §5)

| Name | Kind | Used in | Status |
|---|---|---|---|
| `STARTAN2` | wall 64×128 | MAP01 (F0 room) | IWAD, to be replaced by `SDCONC1` (approved 2026-10-12) |
| `FLOOR4_8` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDFLR2` (approved 2026-10-12) |
| `CEIL3_5` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDCEIL2` (approved 2026-10-12) |
| `SKY1` | sky | MAPINFO | IWAD, kept on MAP02 only (the metro, no sky sector); MAP01, MAP03-09 and the range have their own (`SDSKY1-7`) |

## Discarded

| Lump | Date | Reason | What happens instead |
|---|---|---|---|
| `SDPOSTR1` (Lenin poster, v1 silhouette) | 2026-10-12 | CEO: NOT OK, "we'll have to see how to do Lenin right" | the Lenin portrait became a separate commission (ART-BIBLE §8) and the lump name `SDPOSTR1` went to its result: v4, posterised from the public-domain 1920 photograph, approved 2026-10-12 at 128×256 (row above) |
| hangar dado, 128 high (composite steel-below / concrete-above wall, never drawn; the alternative to `SDCONC2` in the hangar, `docs/levels/MAP01-zarya-7.md` deviation 1) | 2026-10-13 | not needed: the CEO approved `SDCONC2` as built in the hangar's three bands, «no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas» ("it isn't perfect but I'd leave it like this, it adds colour and fills the 3 bands") | `SDCONC2` stays in the hangar |
