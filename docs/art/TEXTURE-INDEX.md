# Texture index

Living document. Owner: `art-director`. Contract with `level-designer` and
`mod-engineer`: a lump name listed here is the name the map and the PK3 use.
**Renaming = updating this table before the file.** Russian mirror:
`docs/ru/art/TEXTURE-INDEX.md`.

Status values: `proposed` (in a preview, not yet in `assets/`), `approved`
(CEO said yes; file lives in `assets/`), `discarded` (CEO said no; reason kept
so it is not proposed again), `IWAD` (referenced by name from the base IWAD,
nothing redistributed). Transitional values, always with the reason:
`pending in-map review` (the CEO decides on seeing it in GZDoom, not in
`assets/` yet), `approved pending …` (yes, conditional on something the CEO
still has to confirm; not in `assets/` yet), `proposed vN` (redrawn after a
verdict, awaiting the next one). `tools/art/make_preview.py` reads this
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
SDCEIL1 OK · SDCEIL2 OK». Gate G2 (≥ 8 approved): **9 approved** — the 8 unconditional ones plus `SDPOSTR2`, whose only condition (the Russian wording) the CEO confirmed on 2026-10-12. G2 was signed PASS on the 8 unconditional ones; see `docs/qa/GATE-REVIEWS.md`.

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCONC1` | wall | 64×128 | yes | prefab concrete panels, running bond, grime under joints | (a) seed 1978 | approved | 2026-10-12 |
| `SDCONC2` | wall | 64×128 | yes | concrete with worn red stripe at mid height | (a) seed 1979 | pending in-map review (CEO: "we'll see how it looks"; decided on MAP01 in GZDoom) | 2026-10-12 |
| `SDSTAR1` | wall | **128×128** | yes (plaque centred) | concrete with a painted plaque 84×108: gold star above hammer and sickle on red, 1 px dark outline. v2 mirrored the emblem; v3 rebuilt it from the CEO's reference; v4 took the hammer butt to the bottom-right corner; **v5 (variant D1, CEO 2026-10-12)**: hammer head lowered to mid-height (`HAMMER_HEAD_C` y 0.26 → 0.46) and the sickle tip moved onto the outer arc's own end, removing the loose spike the CEO reported ("un palo raro hacia arriba"). Widened to 128 in the same pass because at 64 the lower half of the emblem closed into a blob. Check sheet `tools/art/emblem_check.py`; orientation, handle slope and butt position guarded by `tests/test_art.py` | (a) seed 1980 | proposed v5 | 2026-10-12 |
| `SDSTEL1` | wall | 64×128 | yes | military-green riveted steel plates, chipped paint, rust under rivets | (a) seed 1981 | approved | 2026-10-12 |
| `SDDOOR1` | wall (door) | 128×128 | no | bunker steel door: riveted frame, green leaf, locking wheel, star and "7" stencils, hazard stripe | (a) seed 1982; text Impact.ttf | approved | 2026-10-12 |
| `SDPOSTR1` | wall | **128×256** | no (single poster) | Lenin poster, posterised from the public-domain 1920 Zhukov photograph to three palette inks. v1 (constructivist silhouette) discarded by the CEO; v2 (A/B/C naive threshold) rejected by the PM — no readable face. **v3 (D/E/F)**: head silhouette drawn as its own closed shape with a protected 2 px contour, then fourteen hand-drawn regions separated by their own percentile so no feature can vanish. Head area up 73%. Bottom 56 px reserved for a Cyrillic slogan, still to be chosen. **Size changed from 128×128 to 128×256 — contract change, `level-designer` notified** | (a) `tools/art/gen_lenin.py` + (b) `work/art/reference/lenin_1920_zhukov.jpg`, public domain | proposed v3 (D/E/F) | 2026-10-12 |
| `SDPOSTR2` | wall (mural) | 128×128 | no | cosmonautics mural: rocket, rays, stars, «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» | (a) seed 1984; text Impact.ttf | approved 2026-10-12 (CEO likes it; the Russian wording is to be confirmed before it enters `assets/`) | 2026-10-12 |
| `SDFLR1` | flat | 64×64 | yes (line continuous on x=2..8) | hangar concrete floor with worn yellow lane line | (a) seed 1985 | approved | 2026-10-12 |
| `SDFLR2` | flat | 64×64 | yes | plain hangar concrete floor, cracks, oil wear | (a) seed 1986 | approved | 2026-10-12 |
| `SDFLR3` | flat | 64×64 | yes | grey two-tone Soviet floor tiles, dark grout | (a) seed 1987 | approved | 2026-10-12 |
| `SDCEIL1` | flat | 64×64 | yes (joint on edges) | concrete ceiling panel with fluorescent lamp | (a) seed 1988 | approved | 2026-10-12 |
| `SDCEIL2` | flat | 64×64 | yes (joint on edges) | plain concrete ceiling panel with damp stain | (a) seed 1989 | approved | 2026-10-12 |

Not in this batch (deliberately): anything of the two enemy factions (F5),
exterior/sky textures, animated or switch textures (ANIMDEFS/SWITCHES are
`mod-engineer`'s, proposed for batch 2 once the base set is approved).

Candidates for batch 2 (not started): painted dado wall (green oil paint
lower half + whitewash), concrete corner/pilaster, crate/locker, steel door
variant for keys (red/yellow/blue trims), exterior concrete with night sky,
launch-pad gantry steel, switch panel.

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
| `SDPOSTR1` (Lenin poster, v1 silhouette) | 2026-10-12 | CEO: NOT OK, "we'll have to see how to do Lenin right" | the Lenin portrait is a separate commission (ART-BIBLE §8); the lump name `SDPOSTR1` is reserved for its replacement |
