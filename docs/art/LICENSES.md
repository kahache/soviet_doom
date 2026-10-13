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

## Batch 1 — set "Soviet base" (F2; CEO verdict 2026-10-12)

Per-lump status (approved / pending / discarded) is owned by
`TEXTURE-INDEX.md`; files live in `assets/textures/soviet_base/` and
`assets/flats/soviet_base/`. Origin and licence are the same for the whole
batch, whatever the status.

| Lump | Origin | Author | Licence |
|---|---|---|---|
| `SDCONC1`, `SDCONC2`, `SDSTAR1`, `SDSTEL1`, `SDDOOR1`, `SDPOSTR2`, `SDFLR1`, `SDFLR2`, `SDFLR3`, `SDCEIL1`, `SDCEIL2` | (a) `tools/art/gen_soviet_base.py`, `BATCH_SEED` 1977, palette `docs/art/palette.json` v1 | Soviet Doom project (art-director) | own work, CC BY-NC-SA 4.0 (D15) |
| `SDPOSTR1` (v4, 2026-10-12) | (a) `tools/art/gen_lenin.py`, palette v1, posterising (b) the public-domain photograph listed under "Reference material" below | Soviet Doom project (art-director); photograph by Pavel Zhukov, 1920, public domain | own work on a public-domain source, CC BY-NC-SA 4.0 (D15) |

**`SDFLR1` repair, 2026-10-13 (commit 5c9bb1d, PM).** The file in `assets/`
was replaced by a regeneration of the same lump — same generator, same seed,
same palette — after `art-director` fixed BUG-ART-001 (vector strokes were
clipped at the canvas, so the hairline crack died at the tile border;
`Overlay.line_tiled` in `tools/art/artlib.py` now wraps them). 44 pixels
differ from the previous file, 1 % of the flat and all on the seam; no pixel
was painted by hand and no new source entered. Origin, author and licence
unchanged; the approval stands (`TEXTURE-INDEX.md`).

Symbols: the red star and the hammer and sickle are drawn from scratch as
geometric shapes (no scanned poster). The Lenin portrait of `SDPOSTR1` is
posterised from the public-domain 1920 Zhukov photograph (row below under
"Reference material"); the discarded v1 was a geometric silhouette.
Slogans «ЛЕНИН ЖИВ», «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ» and the «ПУСК» stencil
are generic historical phrases, not quotations of a protected work.

## Fonts used to rasterise Cyrillic text

| Font | File | Where | Note |
|---|---|---|---|
| Impact | macOS `/System/Library/Fonts/Supplemental/Impact.ttf`; Windows `%WINDIR%\Fonts\impact.ttf` (resolved per machine by `tools/art/artlib.py`) | poster headlines (`SDPOSTR1`, `SDPOSTR2`), door stencil (`SDDOOR1`), switch stencil «ПУСК» (`SDSW1A-D`, `SDSW2A-D`) | System font (Monotype) on both machines. **Not redistributed**: only rasterised pixels ship inside the textures. Every shipped text-bearing lump was rasterised on the Mac; the two machines do not rasterise it identically, so these lumps are regenerated only there (ART-BIBLE §7, measurement in `CLAUDE.md`). |
| Arial Narrow Bold | macOS `/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf`; absent on Windows, where `artlib.py` falls back to Arial Bold | reserved for small text (not used by any shipped pixel in batch 1 or 2) | macOS system font (Monotype). Not redistributed. |

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

## Reference material held locally (not shipped)

| File | Work | Origin and licence | Use |
|---|---|---|---|
| `work/art/reference/lenin_1920_zhukov.jpg` (sha256 `ec12d661…a188`) | Portrait of Lenin, July 1920, by Pavel Zhukov (1870-1942) | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Vladimir_Lenin.jpg — public domain in Russia (author died 1942) and in the United States (published before 1 January 1931). Downloaded 2026-10-12 with the CEO's permission | Base for the posterised Lenin poster (`SDPOSTR1`, separate commission). `work/` is gitignored: the photograph itself is never committed or shipped; only the texture derived from it. Rationale and the wider copyright finding: `docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md` |

## Shell screens (F2, approved 2026-10-13)

The CEO liked treatments A and C equally and did not have to choose: each
takes the role it fits. A greets the player, C sits behind the between-level
statistics because its diagonal leaves the centre free.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `TITLEPIC` | Title screen, treatment A "Plakat": flag-red ground, cream ray fan, the rocket profile reused from `SDPOSTR2`, gold star, black masthead reading «СОВЕТСКИЙ DOOM» | (a) `tools/art/gen_shell.py`, `titlepic_a()` + `lockup_a()`, palette v1 | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `INTERPIC` | Between-level screen, treatment C "Rodchenko": maroon ground cut by diagonals, gold star, centre deliberately empty for the engine's map name and counters | (a) `tools/art/gen_shell.py`, `interpic_c()`, palette v1 | idem |
| `M_DOOM` | Menu logo, registered on the title's own name block so it lands exactly over it when the menu opens | (a) `tools/art/gen_shell.py`, `logo()` + `lockup_a()`, palette v1. RGBA with hard alpha (0/255, no semitransparency), not indexed: a menu patch needs transparency. **One of two RGBA families in the project**; the other is the alphabet's 214 glyphs (below). Both are the exception recorded in ART-BIBLE §2 | idem |

Lump names are fixed by the engine, so these three are the documented
exception to the `SD` prefix rule (MOD-SPEC §1).

## The alphabet (F2, chosen by the CEO 2026-10-13)

Variant **C "Mashina"** of three, picked from a sheet that set all three
against real game strings in both scripts. Without this the mod could not
write Russian at all: Freedoom's font is ASCII only, and the Cyrillic glyphs
GZDoom ships are gated behind a filter that only activates for an id Software
IWAD, which we do not use (debt T9, now paid).

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `fonts/defsmallfont/*.png` (107) | Small font, cap 7 px, line 9. HUD messages, pickups, the option menu | (a) `tools/art/gen_font.py`, style C, glyphs defined as drawing code rather than images | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `fonts/bigfont/*.png` (107) | Big font, cap 11 px plus a 1 px shadow, line 16. Menu headlines and level titles | idem | idem |

**Drawn, not derived.** Every glyph is constructed from the project's own
stroke rules in `gen_font.py`; no typeface was traced, subset or converted,
so there is no font licence to inherit. The styles were named after what they
imitate in spirit — poster grotesque, GOST drawing lettering, slab machinery
— not after any particular type family.

Coverage: А-Я and Ё, A-Z, 0-9, and the punctuation the project uses including
«» × · №, at both sizes.

Format: RGBA PNG, not indexed, with palette colours only and hard 0/255
alpha, like `M_DOOM`; the exception is recorded in ART-BIBLE §2 and checked
by `tests/test_gen_font.py`.

## Batch 2 — switches (F2, all four approved by the CEO 2026-10-13)

The CEO took all four rather than one: "yo por mí mete todos, así tenemos
diversidad". Doom's own convention is followed for the names, 1 = off and
2 = on, with the variant letter last (the generator writes
`SDSWT_<variant>_<state>.png`; the files were renamed on install). Per-lump
rows, seeds and the sweep sheet: `TEXTURE-INDEX.md`, batch 2. All eight carry
the «ПУСК» stencil in Impact (fonts table above).

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSW1A` / `SDSW2A` | Rubilnik: knife blade on a cream bakelite board, brass jaws, red grip, indicator lamp below | (a) `tools/art/gen_switch.py` variant A, palette v1 | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `SDSW1B` / `SDSW2B` | Domed push button, red when dead, cream lens when live | (a) idem, variant B | idem |
| `SDSW1C` / `SDSW2C` | Round lens over a vertical slide lever | (a) idem, variant C | idem |
| `SDSW1D` / `SDSW2D` | Hazard-bordered panel, window and travelling block | (a) idem, variant D | idem |

Direction finding from this batch, worth keeping: the palette's liveliest red
has luma 104 and `SDSTEL1` has 101, so **a red element on the steel wall
disappears the moment the sector light drops**. The live state is therefore
carried by a cream lens (45 → 235), not by colour.

Variant A had to be relaid: its board, its painted word and its lamp
overlapped. The three boxes are now stacked bottom-up with declared gaps and
`gen_switch.py` refuses to import if they ever touch again.

## Batch 3 — props (F3, proposed 2026-10-13, nothing in `assets/`)

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDCRAT1` / `SDCRAT2` / `SDCRTOP1` / `SDLOCK1` | crate face, long crate, crate lid, locker; stencilled numbers and arrows drawn from segment data, no typeface | (a) `tools/art/gen_props.py`, palette v1 | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |

Direction finding from this batch: none of these lumps depends on a system
font, so they reproduce byte for byte on the Mac and on Windows; and column
B confirms the switches' lesson once more, a mid green vanishes on
`SDSTEL1`.
