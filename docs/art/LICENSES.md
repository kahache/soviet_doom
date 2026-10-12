# Asset provenance and licences

Living document. Owner: `art-director`; audited by `qa-engineer` before every
gate (G2 requires every approved texture to have origin and licence).
Russian mirror: `docs/ru/art/LICENSES.md`.

## Licence of the mod's own assets (D15)

All textures, flats and sprites made for Soviet Doom are **own work**
(procedural scripts in `tools/art/`, or hand-composed from palette and vector
shapes). Decision D15 (`docs/PRD.md`, 2026-10-09): **CC BY-NC-SA 4.0** for
assets and docs, GPL-3.0 for code; full texts are added at F6, `LICENSE.md`
states it now. No asset of this project comes from a commercial game (Doom,
Doom II, Heretic, Hexen or any other): ART-BIBLE §2.

## Batch 1 — set "Soviet base" (F2; CEO verdict 2026-10-12, 8 approved)

Per-lump status (approved / pending / discarded) is owned by
`TEXTURE-INDEX.md`; approved files live in `assets/textures/soviet_base/` and
`assets/flats/soviet_base/`. Origin and licence are the same for the whole
batch, whatever the status.

| Lump | Origin | Author | Licence |
|---|---|---|---|
| `SDCONC1`, `SDCONC2`, `SDSTAR1`, `SDSTEL1`, `SDDOOR1`, `SDPOSTR1`, `SDPOSTR2`, `SDFLR1`, `SDFLR2`, `SDFLR3`, `SDCEIL1`, `SDCEIL2` | (a) `tools/art/gen_soviet_base.py`, `BATCH_SEED` 1977, palette `docs/art/palette.json` v1 | Soviet Doom project (art-director) | own work, CC BY-NC-SA 4.0 (D15) |

Symbols: the red star, hammer and sickle, and the Lenin silhouette are drawn
from scratch as geometric shapes (no traced photograph, no scanned poster).
Slogans «ЛЕНИН ЖИВ» and «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» are generic
historical phrases, not quotations of a protected work.

## Fonts used to rasterise Cyrillic text

| Font | File | Where | Note |
|---|---|---|---|
| Impact | `/System/Library/Fonts/Supplemental/Impact.ttf` | poster headlines (`SDPOSTR1`, `SDPOSTR2`), door stencil (`SDDOOR1`) | macOS system font (Monotype). **Not redistributed**: only rasterised pixels ship inside the textures. |
| Arial Narrow Bold | `/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf` | reserved for small text (not used by any shipped pixel in batch 1) | macOS system font (Monotype). Not redistributed. |

Position (NOT VERIFIED by a lawyer): bitmap renderings of text are generally
not covered by a font software licence, and the fonts themselves never leave
the author's machine. If `qa-engineer` wants zero doubt for F6, the posters
can be re-rendered with an OFL Cyrillic font (e.g. a free condensed grotesque)
by changing `FONT_POSTER` in `tools/art/artlib.py` and regenerating; the
textures would then have to be re-approved.

## Base IWAD

Freedoom 0.13.0 (`freedoom2.wad`, BSD 3-clause) is the base game data (D2).
The mod references four of its lumps **by name** (`STARTAN2`, `FLOOR4_8`,
`CEIL3_5`, `SKY1`, see `TEXTURE-INDEX.md`) and redistributes none of them.

## Third-party packs

None used yet. OTEX (non-commercial, credit required) is allowed by D4 as a
second source; any OTEX texture will get its own row here with the pack
version and the exact file name before it appears in a preview.
