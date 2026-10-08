# Texture index

Living document. Owner: `art-director`. Contract with `level-designer` and
`mod-engineer`: a lump name listed here is the name the map and the PK3 use.
**Renaming = updating this table before the file.** Russian mirror:
`docs/ru/art/TEXTURE-INDEX.md`.

Status values: `proposed` (in a preview, not yet in `assets/`), `approved`
(CEO said yes; file lives in `assets/`), `discarded` (CEO said no; reason kept
so it is not proposed again), `IWAD` (referenced by name from the base IWAD,
nothing redistributed).

Origin codes (ART-BIBLE §2): (a) own procedural script + seed, (b) free pack
with licence, (c) CEO material.

## Set "Soviet base" — batch 1 (F2)

Preview: `docs/art/previews/2026-10-09_0115_F2_batch1-soviet-base.html`
(mirror `docs/ru/art/previews/…`). Generator `tools/art/gen_soviet_base.py`,
`BATCH_SEED` 1977; the seed column is `BATCH_SEED + offset`. Palette
`docs/art/palette.json` v1 (162 colours).

| Lump | Kind | Size | Tiles | Description | Origin | Status | Date |
|---|---|---|---|---|---|---|---|
| `SDCONC1` | wall | 64×128 | yes | prefab concrete panels, running bond, grime under joints | (a) seed 1978 | proposed | 2026-10-09 |
| `SDCONC2` | wall | 64×128 | yes | concrete with worn red stripe at mid height | (a) seed 1979 | proposed | 2026-10-09 |
| `SDSTAR1` | wall | 64×128 | yes (plaque centred) | concrete with painted plaque: gold star, hammer and sickle on red | (a) seed 1980 | proposed | 2026-10-09 |
| `SDSTEL1` | wall | 64×128 | yes | military-green riveted steel plates, chipped paint, rust under rivets | (a) seed 1981 | proposed | 2026-10-09 |
| `SDDOOR1` | wall (door) | 128×128 | no | bunker steel door: riveted frame, green leaf, locking wheel, star and "7" stencils, hazard stripe | (a) seed 1982; text Impact.ttf | proposed | 2026-10-09 |
| `SDPOSTR1` | wall (poster) | 64×128 | no | Lenin poster: constructivist silhouette in cream medallion on red, «ЛЕНИН ЖИВ» | (a) seed 1983; text Impact.ttf | proposed | 2026-10-09 |
| `SDPOSTR2` | wall (mural) | 128×128 | no | cosmonautics mural: rocket, rays, stars, «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» | (a) seed 1984; text Impact.ttf | proposed | 2026-10-09 |
| `SDFLR1` | flat | 64×64 | yes (line continuous on x=2..8) | hangar concrete floor with worn yellow lane line | (a) seed 1985 | proposed | 2026-10-09 |
| `SDFLR2` | flat | 64×64 | yes | plain hangar concrete floor, cracks, oil wear | (a) seed 1986 | proposed | 2026-10-09 |
| `SDFLR3` | flat | 64×64 | yes | grey two-tone Soviet floor tiles, dark grout | (a) seed 1987 | proposed | 2026-10-09 |
| `SDCEIL1` | flat | 64×64 | yes (joint on edges) | concrete ceiling panel with fluorescent lamp | (a) seed 1988 | proposed | 2026-10-09 |
| `SDCEIL2` | flat | 64×64 | yes (joint on edges) | plain concrete ceiling panel with damp stain | (a) seed 1989 | proposed | 2026-10-09 |

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
| `STARTAN2` | wall 64×128 | MAP01 (F0 room) | IWAD, to be replaced by `SDCONC1` when approved |
| `FLOOR4_8` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDFLR2` when approved |
| `CEIL3_5` | flat | MAP01 (F0 room) | IWAD, to be replaced by `SDCEIL2` when approved |
| `SKY1` | sky | MAPINFO | IWAD, kept until an own sky exists |

## Discarded

(none yet)
