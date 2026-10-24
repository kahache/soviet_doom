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
| `SDPOSTR3` (2026-10-14, D55) | (a) `tools/art/gen_stalin.py`, palette v1, posterising (b) the public-domain photograph `stalin_1930.jpg` listed under "Reference material" below | Soviet Doom project (art-director); photograph by an unknown photographer, frontispiece of *The Life of Stalin: A Symposium*, New York 1930, public domain | own work on a public-domain source, CC BY-NC-SA 4.0 (D15) |
| `SDPOSTR4` (2026-10-22, D117) | (a) `tools/art/gen_marx_engels.py`, palette v1, posterising (b) the public-domain photograph `marx_1875.jpg` listed under "Reference material" below | Soviet Doom project (art-director); photograph of Karl Marx by J. J. E. Mayall's studio, London, 1875, public domain | own work on a public-domain source, CC BY-NC-SA 4.0 (D15) |
| `SDPOSTR5` (2026-10-22, D117) | (a) `tools/art/gen_marx_engels.py`, palette v1, posterising (b) the public-domain photograph `engels_1877.jpg` listed under "Reference material" below, **mirrored left to right** (so that he faces Marx; the flip is the generator's `MIRROR_ENGELS`, approved by the CEO) | Soviet Doom project (art-director); photograph of Friedrich Engels by William Hall, May 1877, public domain | own work on a public-domain source, CC BY-NC-SA 4.0 (D15) |

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
| Impact | macOS `/System/Library/Fonts/Supplemental/Impact.ttf`; Windows `%WINDIR%\Fonts\impact.ttf` (resolved per machine by `tools/art/artlib.py`) | poster headlines (`SDPOSTR1`, `SDPOSTR2`; `SDPOSTR3`, `SDPOSTR4` and `SDPOSTR5` rasterised on the Windows PC, D27), door stencil (`SDDOOR1`), switch stencil «ПУСК» (`SDSW1A-D`, `SDSW2A-D`) | System font (Monotype) on both machines. **Not redistributed**: only rasterised pixels ship inside the textures. Every shipped text-bearing lump was rasterised on the Mac; the two machines do not rasterise it identically, so these lumps are regenerated only there (ART-BIBLE §7, measurement in `CLAUDE.md`). |
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
**The exception: three enemy gib sounds.** `SDRRIXDT`, `SDLTRXDT` and
`SDSTOXDT` edit and layer Freedoom's `DSSLOP` (D83; rows under "Enemy
sounds"): a derivative of Freedoom's data, shipped inside our PK3 under
Freedoom's licence, with its credit. Since D125 two of the sergeant's
violent deaths, `SDSGXDT1` and `SDSGXDT2`, layer `SDRRIXDT` and so carry
the same derivative (rows under "World sounds"). **No art pixel of Freedoom's ships
since D123 (2026-10-23):** from N17 (2026-10-15) to D123 the TT-33's
first-person frames (`SDTTA0`-`SDTTC0`) carried the hand pixels of
Freedoom's `PISGA0`-`PISGC0`, recoloured (D61); the Gemini TT-33 replaced
them ("Weapon frames: the TT-33 in hand" below).

**What Freedoom's licence asks of us.** Freedoom's data is under a modified
BSD licence (BSD 3-clause). Shipping a derivative of it inside the PK3 is a
redistribution in binary form, so: (1) the copyright notice, the list of
conditions and the disclaimer travel in the documentation of the release:
`LICENSE-FREEDOOM-BSD-3.txt`, Freedoom v0.13.0's `COPYING.adoc` verbatim
(D75), in the repository root and in every release package
(`tools/release.py`); (2) neither the Freedoom project's name nor its
contributors' may be used to endorse or promote the mod without their
permission. The credit is on screen (`SD_CRED_IWAD_*`, Options → Soviet
Doom → Credits) and in the release's credits (the rows' `credit
"Freedoom"`, read by `tools/licences.py`). NOT VERIFIED by a lawyer.
**Not an exception (D82, 2026-10-20):** seven sprites ship under the IWAD's
own names, `PUFF`, `BLUD`, `TFOG`, `IFOG`, `BAR1`, `BEXP` and `COLU`, so
they replace Freedoom's pictures of the engine's puff, blood, fogs, barrel
and floor lamp. They are our own drawings (not one Freedoom pixel), with
their own rows in "Player effects and world sprites" below; only the names
are the IWAD's.

## Third-party packs

None used yet. OTEX (non-commercial, credit required) is allowed by D4 as a
second source; any OTEX texture will get its own row here with the pack
version and the exact file name before it appears in a preview.

## Reference material held locally (not shipped)

| File | Work | Origin and licence | Use |
|---|---|---|---|
| `work/art/reference/lenin_1920_zhukov.jpg` (sha256 `ec12d661…a188`) | Portrait of Lenin, July 1920, by Pavel Zhukov (1870-1942) | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Vladimir_Lenin.jpg — public domain in Russia (author died 1942) and in the United States (published before 1 January 1931). Downloaded 2026-10-12 with the CEO's permission | Base for the posterised Lenin poster (`SDPOSTR1`, separate commission). `work/` is gitignored: the photograph itself is never committed or shipped; only the texture derived from it. Rationale and the wider copyright finding: `docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md` |
| `work/art/reference/stalin_1930.jpg` (sha256 `867bfc45…6fd9`, 1313×2100, 497,531 bytes) | Portrait of Stalin, frontispiece of *The Life of Stalin: A Symposium*, Workers Library Publishers, New York, 1930; photographer unknown | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Stalin-Joseph-1930.jpg (file https://upload.wikimedia.org/wikipedia/commons/8/86/Stalin-Joseph-1930.jpg) — public domain in the United States (published 1930, before 1 January 1931; also published without notice) and in Russia (anonymous work published before 1943). Residual risk: Russian status rests on the photographer staying unidentified. Downloaded 2026-10-14 with the CEO's permission | Base for the posterised Stalin poster (`tools/art/gen_stalin.py`, proposal; lump name not yet assigned). `work/` is gitignored: never committed or shipped. Rationale, candidates and rejected sources: `docs/product/2026-10-14_1556_F2_stalin-poster-sourcing.md` |
| `work/art/reference/marx_1875.jpg` (sha256 `cc2fb87d222a2659a59496040805cb9911e16527f145edceb142cfe5954617c9`, JPEG greyscale 1428×2048, 380,651 bytes) | Portrait of Karl Marx, J. J. E. Mayall's studio, 224 Regent Street, London, before 24 August 1875 (J. J. E. Mayall died 1901; a Commons sibling credits his son John Mayall junior, died 1891); scan of the International Institute of Social History, Amsterdam | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Karl_Marx_001.jpg (file https://upload.wikimedia.org/wikipedia/commons/d/d4/Karl_Marx_001.jpg), tagged `PD-old-100-expired` — public domain in Russia, the United States and the EU (every candidate author died before 1902; a faithful scan adds no right). Downloaded 2026-10-22 by the PM with the CEO's permission | Base for the Marx poster `SDPOSTR4` (D117). `work/` is gitignored: never committed or shipped. Rationale, candidates and rejected sources: `docs/product/2026-10-22_P4_marx-engels-poster-sourcing.md` |
| `work/art/reference/engels_1877.jpg` (sha256 `c7be6f45ed4f506a56735f2a451d7265f735eda1f8888c8029073c3c984fec31`, JPEG RGB sepia 945×1437, 514,277 bytes) | Portrait of Friedrich Engels, May 1877, by William Hall (1826 - c. 1898) | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Friedrich_Engels_portrait.jpg (file https://upload.wikimedia.org/wikipedia/commons/7/75/Friedrich_Engels_portrait.jpg), tagged `PD-old-auto-expired` — public domain in Russia, the United States and the EU (author died c. 1898). Downloaded 2026-10-22 by the PM with the CEO's permission | Base for the Engels poster `SDPOSTR5` (D117), used **mirrored** (the derivative is flipped left to right; the photograph is not altered). `work/` is gitignored: never committed or shipped. Rationale: `docs/product/2026-10-22_P4_marx-engels-poster-sourcing.md` |

## Shell screens (F2, approved 2026-10-13)

The CEO liked treatments A and C equally and did not have to choose: each
takes the role it fits. A greets the player, C sits behind the between-level
statistics because its diagonal leaves the centre free.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `TITLEPIC` | Title screen (D126, replaces D18's "Plakat"): the sergeant firing the PPSh-41 and raising the red banner over the Reich's and the Legion's invaders, the Kremlin burning, the statue-robot with its torch behind; the `M_DOOM` lockup painted at (60,0) without its black plate. Armbands: the D12 symbol painted on the two Reich armbands (D105, D108) | (a) derived from an image generated by the project lead with Google Gemini (`work/art/reference/gemini_titlepic_A.jfif`, prompt `docs/product/2026-10-23_P4_gemini-prompt-pack.md` §11), processed into a 320x200 screen by `tools/art/gen_titlepic.py` (sky extended, 4:3 crop, palette v2 in CIELAB with a 4x4 ordered dither; the armband symbol warped onto the painting by `tools/art/armband_symbol.py`, D108); the source image is not distributed (D77) | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79) |
| `INTERPIC` | Between-level screen, treatment C "Rodchenko": maroon ground cut by diagonals, gold star, centre deliberately empty for the engine's map name and counters | (a) `tools/art/gen_shell.py`, `interpic_c()`, palette v1 | idem |
| `M_DOOM` | Menu logo, registered on the title's own name block so it lands exactly over it when the menu opens; since D126 the D18 lockup with its black plate keyed out (alpha 0) and a 1-px black outline, so the Gemini title shows round the letters | (a) `tools/art/gen_shell.py`, `logo()` + `lockup_a()`, palette v1, keyed by `tools/art/gen_titlepic.py` `free_logo()`. RGBA with hard alpha (0/255, no semitransparency), not indexed: a menu patch needs transparency. **One of two RGBA families in the project**; the other is the alphabet's 224 glyphs (below). Both are the exception recorded in ART-BIBLE §2 | idem |

Lump names are fixed by the engine, so these three are the documented
exception to the `SD` prefix rule (MOD-SPEC §1).

## Shell: M_SKULL1/2, M_PAUSE (D48)

CEO verdict 2026-10-14 (D48): menu cursor **B** (hammer and sickle) and
pause sign **P2** (a plaque per language), from the T12 sweep
`docs/art/previews/2026-10-13_2208_F2_shell-cursor-pause-sweep.html`. Files
in `assets/graphics/shell/`, renamed on install from the generator's option
names and copied byte for byte from `work/art/shell_extra/`
(`cursor_B_1.png` → `M_SKULL1.png`, `cursor_B_2.png` → `M_SKULL2.png`,
`pause_P2_en.png` → `M_PAUSE.png`). Like `M_DOOM`, RGBA with hard alpha and
palette colours only (ART-BIBLE §2), and named by the engine, so outside the
`SD` prefix rule (MOD-SPEC §1). The Russian plaque (`pause_P2_ru.png`,
same origin) ships since T24 as `assets/localized/textures/M_PAUSE.ru.png`
and the Catalan one (`pause_P2_ca.png`, P6, 2026-10-21) as
`M_PAUSE.ca.png` beside it, both byte for byte from `work/art/shell_extra/`
and drawn by `SD_StatusBar` (MOD-SPEC §6.5.1, ADR 010); `M_PAUSE`'s row
covers them as language variants, and each has its own row below.
Per-lump rows: `TEXTURE-INDEX.md`, "Shell pictures".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `M_SKULL1` / `M_SKULL2` | menu cursor, the two blink phases: the hammer and sickle, gold then pale cream, with a dark-red outline | (a) `tools/art/gen_cursor.py`, `cursor_image("B", 1/2)`, palette v1; the emblem's geometry imported from `gen_soviet_base.hammer_sickle()` (the approved `SDSTAR1` v5), never re-traced | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `M_PAUSE` | pause sign, English: «PAUSE» on a flag-red plaque with a cream border | (a) `tools/art/gen_cursor.py`, `pause_image("P2", "en")`, palette v1; the word set in our own `SDMENU` folder font (read from `assets/fonts/sdmenu/`, above), no system font | idem |
| `M_PAUSE.ru.png` | pause sign, Russian: «ПАУЗА» on the same plaque, 77x20 (T24) | (a) `tools/art/gen_cursor.py`, `pause_image("P2", "ru")`, palette v1, `SDMENU` as above | idem |
| `M_PAUSE.ca.png` | pause sign, Catalan: «PAUSA» on the same plaque, 77x20 (P6); `SDMENU`'s D22 letterforms make it read PДUSД, as the menu does in Catalan | (a) `tools/art/gen_cursor.py`, `pause_image("P2", "ca")` (`--catalan --install`), palette v1, `SDMENU` as above; fitted inside the English and Russian canvas, which it does not change | idem |
| `SDCURSOR` | mouse pointer (GameInfo `CursorPic`, D102): the hammer and sickle, gold with a dark-red contour, 28x25, grAb 12,1 at the sickle's tip | (a) `tools/art/gen_mouse_cursor.py`, palette v1; the emblem's geometry imported from `gen_soviet_base.hammer_sickle()` (the approved `SDSTAR1` v5), no font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

Procedural and drawn from code: no photograph, no typeface, no pixel
painted by hand. Freedoom's own `M_SKULL1`, `M_SKULL2` and `M_PAUSE` are read
from the IWAD only to sit beside ours on the sweep sheet
(`work/art/shell_extra/freedoom/`, never shipped) and never enter a picture.

## The alphabet (F2, chosen by the CEO 2026-10-13)

Variant **C "Mashina"** of three, picked from a sheet that set all three
against real game strings in both scripts. Without this the mod could not
write Russian at all: Freedoom's font is ASCII only, and the Cyrillic glyphs
GZDoom ships are gated behind a filter that only activates for an id Software
IWAD, which we do not use (debt T9, now paid).

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `fonts/defsmallfont/*.png` (121) | Small font, cap 7 px, line 9. HUD messages, pickups, the option menu | (a) `tools/art/gen_font.py`, style C, glyphs defined as drawing code rather than images | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `fonts/bigfont/*.png` (121) | Big font, cap 11 px plus a 1 px shadow, line 16. Menu headlines and level titles | idem | idem |

**Drawn, not derived.** Every glyph is constructed from the project's own
stroke rules in `gen_font.py`; no typeface was traced, subset or converted,
so there is no font licence to inherit. The styles were named after what they
imitate in spirit — poster grotesque, GOST drawing lettering, slab machinery
— not after any particular type family.

Coverage: А-Я and Ё, A-Z, 0-9, the German Ä Ö Ü and the sharp s (ẞ U+1E9E
and ß U+00DF, one drawing), the Catalan À È É Í Ï Ò Ó Ú Ç, and the punctuation the project uses including
«» × · №, at both sizes.

Format: RGBA PNG, not indexed, with palette colours only and hard 0/255
alpha, like `M_DOOM`; the exception is recorded in ART-BIBLE §2 and checked
by `tests/test_gen_font.py`.

**Correction of six glyphs, 2026-10-13 (approved by the CEO the same day:
«apruebo el arreglo de la fuente»).** QA found (H1) that the slab serifs of
M, Cyrillic М and W were placed on one side only, because `Pen.mirror()`
reflected the ink but not the stroke ends that carry the slabs; W also drew
a foot where none of its strokes ends. Fixed in `tools/art/gen_font.py`
(`MIRROR_TERMINALS = True`) and the six affected files replaced in
`assets/fonts/`: `004D.png`, `041C.png` and `0057.png` in both
`defsmallfont/` and `bigfont/`. Same generator, same style, no pixel painted
by hand, no new source; the other 208 glyphs are unchanged byte for byte.
Regenerated on the Windows PC and checked byte for byte against the
proposal build `work/art/font_fix/C/` before copying: the glyphs use no
system font, so they reproduce on both machines. Origin, author and licence
unchanged. Before/after sheet:
`docs/art/previews/2026-10-13_1443_F2_font-C-serif-fix.png`.

**German letters, 2026-10-13 (approved by the CEO the same day for an
in-game trial, D37: «Las pruebo, incluso la B se queda», "I'll try them; even the B stays").** Ä, Ö, Ü and the
sharp s, so the Reich's real German (D36) prints as written: ten new files,
`00C4.png`, `00D6.png`, `00DC.png`, `1E9E.png` and `00DF.png` in both
`defsmallfont/` and `bigfont/`, taking the alphabet from 214 to 224 glyphs.
Drawn by the same stroke rules in `tools/art/gen_font.py`
(`GERMAN_UMLAUTS = True`): each umlaut is its base capital in a shorter box
under two stem-sized dots, the sharp s is its own construction; the two
sharp-s codepoints are one drawing. No pixel painted by hand, no new source,
the 214 existing glyphs unchanged byte for byte. Copied from the proposal
build `work/art/font_umlaut/C/` and checked byte for byte. Origin, author and
licence unchanged. Proposal sheet:
`docs/art/previews/2026-10-13_1730_F5_font-german-umlauts.png`.

**Catalan letters, 2026-10-21 (P6, D97; installed by the PM for the P6
review, Q3 of `docs/product/2026-10-21_P6_catala-revisio.md`; the CEO judges
them on the sheet).** À, È, É, Í, Ï, Ò, Ó, Ú and Ç, so the `[ca]` section of
`LANGUAGE` prints its accents: nine new files, `00C0.png`, `00C8.png`,
`00C9.png`, `00CD.png`, `00CF.png`, `00D2.png`, `00D3.png`, `00DA.png` and
`00C7.png` in both `defsmallfont/` and `bigfont/`, taking the alphabet from
224 to 242 glyphs, and the same nine copied into `sdmenu/` from `bigfont/`.
Drawn by the same stroke rules in `tools/art/gen_font.py`
(`CATALAN_ACCENTS = True`): each accented letter is its base capital in the
umlauts' shorter box under a two-row accent stroke one stem wide; Ï is I
under two dots; Ç is C at the cap line with the cedilla in the rows below it,
inside the cap box. Capitals only, like the rest of the font. No pixel
painted by hand, no new source, the 224 existing glyphs unchanged byte for
byte. Copied from the build `work/art/font_ca/` and checked byte for byte.
Origin, author and licence unchanged. Sheet:
`docs/art/previews/2026-10-21_P6_font-ca.png`.

## The menu font SDMENU (D31, approved for in-engine trial 2026-10-13)

The first construction of D22 (level 2: R→Я, N→И, E→Э, W→Ш, A→Д). Used only
by the menu descriptors (`Font "SDMENU"` in `MENUDEF`), never by running
text, so the proper nouns, calibres and key prompts that
`docs/product/LANGUAGE-SWITCH.md` keeps in Latin are never drawn with it.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `fonts/sdmenu/*.png` (121) | Menu font: `fonts/bigfont/` (cap 11 px plus a 1 px shadow, line 16) with the five Latin capitals R, N, E, W, A drawn with the forms of Я, И, Э, Ш, Д. Russian strings use Cyrillic code points and are unaffected, so one font serves both languages | (a) `tools/art/gen_menu.py`: 116 glyphs (the German five included since D37, the Catalan nine since P6) and `font.inf` copied byte for byte from `assets/fonts/bigfont/`; the five substituted glyphs rendered by `gen_font.glyph_image()` from the Cyrillic letters' stroke code, byte-identical to `0414`, `0418`, `042D`, `042F` and `0428` of `bigfont/`. No new drawing, no system font | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |

Status: **approved for in-engine trial 2026-10-13 (D31)**; the CEO judges
it on screen. `tests/test_gen_menu.py` pins the map and checks that only
those five files differ from `bigfont/`. Reference sheet:
`docs/art/previews/2026-10-13_1554_F2_menu-sweep.png`.

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

## Batch 3 — props (F3, approved by the CEO 2026-10-13)

CEO verdict, verbatim: «apruebo el arreglo de la fuente y cajas C y D» —
column C for the three crate pieces, column D for the locker, as drawn
(khaki and stencilled numbers kept; ART-BIBLE §6.2). Files in
`assets/textures/soviet_base/` and `assets/flats/soviet_base/`, renamed
on install from the generator's cell names (`R1C_SDCRAT1.png` →
`SDCRAT1.png`, and so on). Per-lump rows and seeds: `TEXTURE-INDEX.md`,
batch 3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDCRAT1` / `SDCRAT2` / `SDCRTOP1` | crate face, long crate, crate lid; khaki planks, diagonal brace, stencilled numbers and arrows drawn from segment data, no typeface | (a) `tools/art/gen_props.py`, variant C, palette v1 | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `SDLOCK1` | two-door barracks locker, pale pine with black straps | (a) `tools/art/gen_props.py`, variant D, palette v1 | idem |

Direction finding from this batch: none of these lumps depends on a system
font, so they reproduce byte for byte on the Mac and on Windows; and column
B confirms the switches' lesson once more, a mid green vanishes on
`SDSTEL1`.

## Batch 2 — metro, first pieces (F2, approved by the CEO 2026-10-13, D42)

CEO verdict, verbatim: «OK a las 6 piezas de metro» ("OK to the 6 metro pieces") — shipped as drawn in
palette v1. Files in `assets/textures/metro/` and `assets/flats/metro/`,
copied byte for byte from the Mac's renders in `work/art/batch2/metro/`
(SHA-256 checked against `work/MANIFEST-from-mac.txt`); the same six
regenerate byte-identical on the Windows PC. Per-lump rows and seeds:
`TEXTURE-INDEX.md`, set "Metro".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDTILE1`, `SDTILE2` | glazed cream tile wall; the same over a green oil-paint dado | (a) `tools/art/gen_metro.py`, `BATCH_SEED` 1935, palette v1 | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `SDMARB1` | red marble cladding with veins | (a) idem | idem |
| `SDMOSA1` | mosaic panel, smalt-gold star with rays on cobalt, drawn from scratch on a tessera grid; the palette v2 rendering since D56 (2026-10-14, «mosaico V2»), copied byte for byte from `work/art/batch2/metro_v2/SDMOSA1_v2.png` (the D42 v1 is history, `--mosaic-v1`) | (a) `tools/art/gen_metro.py`, `BATCH_SEED` 1935, **palette v2** | idem |
| `SDBRAS1` | fluted brass pilaster with a ventilation grille | (a) idem | idem |
| `SDMFLR1` | polished granite floor (flat) | (a) idem | idem |

No typeface, no photograph, no scanned station: the real Moscow metro is
the reference for the materials only (described in ART-BIBLE §4), and no
image of it was used as a source.

## Metro fill (D48)

CEO verdict 2026-10-14, verbatim: «PERFECTO» — the ten fill pieces of the
metro, as drawn in palette v1, both tunnels and the chevrons included (D48).
Preview `docs/art/previews/2026-10-13_2022_F3_batch2-metro-fill.html`. Files
in `assets/textures/metro/` (walls) and `assets/flats/metro/` (flats), copied
byte for byte from `work/art/batch2/metro_fill/`, rendered on the Windows PC;
no typeface, so they reproduce on both machines. Per-lump rows and seeds
(1935 + 7 to 16): `TEXTURE-INDEX.md`, "Metro fill-out".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDMEDG1` | platform face towards the track, chevron band | (a) `tools/art/gen_metro.py --fill`, `BATCH_SEED` 1935, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDTUNL1` | running-tunnel concrete with cable bundles | (a) idem | idem |
| `SDTUBB1` | cast-iron tubbing segments | (a) idem | idem |
| `SDMARB2` | tile above red marble, brass rail | (a) idem | idem |
| `SDTILE3` | tile wall with a ceramic lozenge frieze | (a) idem | idem |
| `SDMFLR2` | station hall granite checker (flat) | (a) idem | idem |
| `SDMFLR3` | platform edge from above, yellow warning line (flat) | (a) idem | idem |
| `SDRAIL1` | track bed, sleepers and rails (flat) | (a) idem | idem |
| `SDMCEIL1` | coffered whitewashed ceiling (flat) | (a) idem | idem |
| `SDMCEIL2` | the same coffer with a brass ring lamp (flat) | (a) idem | idem |

Same sources as the first six: no photograph, no scanned station, no
typeface; the real metro is a reference for materials only.

## Batch 4 — the factory «Танкоград» (F3, all approved by the CEO 2026-10-14, D66)

CEO verdict, verbatim: «Me gustan TODAS» — every piece of the sheet
`docs/art/previews/2026-10-14_2017_F3_batch4-factory.html`, with palette v2
for the brick, the Legion flag's canton and the portal, and the portal in
cobalt with white filaments (D66). Files in `assets/textures/factory/`
(walls) and `assets/flats/factory/` (flats), copied byte for byte from
`work/art/batch4/factory/`, rendered on the Windows PC on 2026-10-14; every
frame of the two animations is installed. `SDCHAN1` and `SDSLOG1` are
approved but still wait in `work/` until the validators accept a masked RGBA
texture and the 256×64 size (`TEXTURE-INDEX.md`); their rows stand here so
the provenance is on record before they ship. The only lettering (the banner and
the two pass plates) is set from **our own alphabet** (`assets/fonts/bigfont/`,
D24, scaled nearest neighbour), never a system font, so every lump
reproduces byte for byte on both machines. Per-lump rows and seeds
(`BATCH_SEED` 4100 + offset): `TEXTURE-INDEX.md`, set "Factory".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDBRCK1` | soot-stained red factory brick | (a) `tools/art/gen_factory.py`, `BATCH_SEED` 4100, **palette v2** (`marble_red`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBRCK2` | the same brick whitewashed to 64 | (a) idem, **palette v2** | idem |
| `SDRUST1` | rusted corrugated sheet | (a) idem, palette v1 | idem |
| `SDCHAN1` | hanging chain and crane hook, masked (RGBA, hard alpha) | (a) idem, palette v1 | idem |
| `SDFLR4` | cast-iron chequer plate (flat) | (a) idem, palette v1 | idem |
| `SDGRAT1` | steel bar grating for the catwalks (flat) | (a) idem, palette v1 | idem |
| `SDMOLT1` | molten metal, animation frame 1 of 4 (flat) | (a) idem, palette v1 | idem |
| `SDMOLT2` | molten metal, frame 2 (flat) | (a) idem, palette v1 | idem |
| `SDMOLT3` | molten metal, frame 3 (flat) | (a) idem, palette v1 | idem |
| `SDMOLT4` | molten metal, frame 4 (flat) | (a) idem, palette v1 | idem |
| `SDDOORY` | `SDDOOR1` for the yellow lock, pass plate «ПРОПУСК» in our alphabet | (a) idem, palette v1; the leaf replays `SDDOOR1`'s seed (gen_soviet_base, 1977 + 5), no system font | idem |
| `SDDOORR` | `SDDOOR1` for the red lock, pass plate «ПРОПУСК» in our alphabet | (a) idem | idem |
| `SDPORT1` | the portal's surface, cobalt with white filaments, frame 1 of 4 | (a) idem, **palette v2** (`mosaic_cobalt`) | idem |
| `SDPORT2` | the portal, frame 2 | (a) idem, **palette v2** | idem |
| `SDPORT3` | the portal, frame 3 | (a) idem, **palette v2** | idem |
| `SDPORT4` | the portal, frame 4 | (a) idem, **palette v2** | idem |
| `SDGATE1` | sliding factory gate, green corrugated sheet | (a) idem, palette v1 | idem |
| `SDWIND1` | industrial glazing at night | (a) idem, palette v1 | idem |
| `SDSLOG1` | works banner «ТРАКТОРЫ — КОЛХОЗАМ!», 256×64, set in **our alphabet** (bigfont, D24) at 2× | (a) idem, palette v1, no system font | idem |

No photograph and no scanned building: the Chelyabinsk works and Soviet
industrial architecture are references for materials only. The two faction
banners this set drew (`SDFLAG1`, `SDFLAG2`) were replaced by Soviet flags
in D119 under the same lump names: their rows are in "Soviet flags (D119)"
below.

## Episode 2 «The Road to Moscow» — textures (P4, approved by the CEO 2026-10-22, D107)

CEO verdict 2026-10-22: 25/25 pieces of the sheet
`docs/art/previews/2026-10-22_P4_episode2-textures.html`, all OK except
`SDSIGL1` («?»: fine as a single signal, odd as a mosaic), installed for
single use only (D107, `TEXTURE-INDEX.md`). 28 lumps in
`assets/textures/<railway|dam|moscow>/` (walls) and
`assets/flats/<railway|dam|moscow>/` (flats), copied byte for byte from
`work/art/episode2/<set>/`, rendered on the Windows PC on 2026-10-22 and
identical to a fresh render (`tests/test_gen_episode2.py`). All procedural,
seed = the set's `BATCH_SEED` (5400 / 5500 / 5600) + offset, shared code in
`tools/art/ep2lib.py`. The only lettering («НЕФТЬ», «СКЛАД», «М2») is set
from **our own alphabet** (`assets/fonts/bigfont/`, D24), never a system
font; the digits are drawn pixel by pixel in `ep2lib.py`. Palette v1, plus
v2's `marble_red` only for the five bricks (as `SDBRCK1`, D66). No
photograph, no scanned building: the Sverdlovsk yard, the Zhiguli dam, the
Kremlin, the GUM and the Spasskaya tower are references for materials and
forms only; the banner's star and hammer and sickle are the approved
emblem, drawn from code.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDTRAK1` | yard track on ballast (flat) | (a) `tools/art/gen_railway.py`, seed 5402, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBLST1` | loose ballast (flat) | (a) `tools/art/gen_railway.py`, seed 5401, palette v1 | idem |
| `SDWAGN1` | goods wagon side, stencilled number in our pixel digits | (a) `tools/art/gen_railway.py`, seed 5403, palette v1 | idem |
| `SDTANK1` | tank wagon side, «НЕФТЬ» in our alphabet | (a) `tools/art/gen_railway.py`, seed 5404, palette v1, no system font | idem |
| `SDARMR1` | armoured-train plate with a red star | (a) `tools/art/gen_railway.py`, seed 5405, palette v1 | idem |
| `SDARMR2` | armoured-train plate, plain | (a) `tools/art/gen_railway.py`, seed 5406, palette v1 | idem |
| `SDSIGL1` | colour-light signal, plate «М2» in our alphabet; single use only (D107) | (a) `tools/art/gen_railway.py`, seed 5407, palette v1, no system font | idem |
| `SDBRCK3` | roundhouse brick with a frieze | (a) `tools/art/gen_railway.py`, seed 5408, **palette v2** (`marble_red`) | idem |
| `SDGATE2` | goods-shed sliding door, plate «СКЛАД» in our alphabet | (a) `tools/art/gen_railway.py`, seed 5409, palette v1, no system font | idem |
| `SDDAM1` | dam mass concrete | (a) `tools/art/gen_dam.py`, seed 5501, palette v1 | idem |
| `SDDAM2` | dam concrete at the waterline | (a) `tools/art/gen_dam.py`, seed 5502, palette v1 | idem |
| `SDTURB1` | turbine-generator housing, 4BO green | (a) `tools/art/gen_dam.py`, seed 5503, palette v1 | idem |
| `SDCTRL1` | control board, illegible pixel labels | (a) `tools/art/gen_dam.py`, seed 5504, palette v1 | idem |
| `SDSPIL1` | spillway trash rack over running water | (a) `tools/art/gen_dam.py`, seed 5505, palette v1 | idem |
| `SDWATR1` | the Volga's water, animation frame 1 of 4 (flat) | (a) `tools/art/gen_dam.py`, seed 5506, palette v1 | idem |
| `SDWATR2` | the water, frame 2 (flat) | (a) `tools/art/gen_dam.py`, seed 5506, palette v1 | idem |
| `SDWATR3` | the water, frame 3 (flat) | (a) `tools/art/gen_dam.py`, seed 5506, palette v1 | idem |
| `SDWATR4` | the water, frame 4 (flat) | (a) `tools/art/gen_dam.py`, seed 5506, palette v1 | idem |
| `SDINSL1` | HV insulator string, masked (RGBA, hard alpha) | (a) `tools/art/gen_dam.py`, seed 5507, palette v1 | idem |
| `SDGRAT2` | expanded-metal floor (flat) | (a) `tools/art/gen_dam.py`, seed 5508, palette v1 | idem |
| `SDCOBL1` | Red Square setts (flat) | (a) `tools/art/gen_moscow.py`, seed 5601, palette v1 | idem |
| `SDCOBL2` | setts with a granite line (flat) | (a) `tools/art/gen_moscow.py`, seed 5602, palette v1 | idem |
| `SDKREM1` | Kremlin wall brick | (a) `tools/art/gen_moscow.py`, seed 5603, **palette v2** (`marble_red`) | idem |
| `SDKREM2` | Kremlin merlon, masked (RGBA, hard alpha), `SDKREM1`'s brick | (a) `tools/art/gen_moscow.py`, seed 5603, **palette v2** (`marble_red`) | idem |
| `SDGUM1` | GUM facade bay | (a) `tools/art/gen_moscow.py`, seed 5604, palette v1 | idem |
| `SDTRIB1` | tribune granite | (a) `tools/art/gen_moscow.py`, seed 5605, palette v1 | idem |
| `SDBANR1` | parade banner on `SDKREM1`, no text (D12) | (a) `tools/art/gen_moscow.py`, seed 5606, **palette v2** (only through the brick) | idem |
| `SDSPAS1` | Spasskaya tower stone | (a) `tools/art/gen_moscow.py`, seed 5607, **palette v2** (`marble_red`) | idem |

## Episode 2, round 2 — textures (P4, approved 2026-10-22 under D113's standing approval)

D113: the CEO approves procedural textures in advance; the PM gate passed
the sheet `docs/art/previews/2026-10-22_P4_episode2-textures-round2.html` on
2026-10-22. 23 lumps in `assets/textures/<sky|railway|dam|moscow>/` (walls
and skies) and `assets/flats/<railway|moscow>/` (flats), copied byte for
byte from `work/art/episode2b/<set>/`, rendered on the Windows PC on
2026-10-22 and identical to a fresh render (`tests/test_gen_episode2b.py`).
All procedural, one generator, `tools/art/gen_episode2b.py`, seed =
`BATCH_SEED` 5700 + offset, on top of `ep2lib.py`, `gen_factory.py` and
`gen_moscow.py` (read only). Every word is set from **our own alphabet**
(`assets/fonts/bigfont/`, D24), never a system font. Palette v1, plus v2's
`marble_red` and `mosaic_cobalt` only where a row says so. No photograph,
no scanned building: Sverdlovsk, the Spasskaya tower, the ruby stars, the
GUM and the Historical Museum are references for materials and forms only;
round 2's two faction banners on `SDKREM1` (`SDFLAG3`, `SDFLAG4`) were
replaced by Soviet flags in D119: their rows are in "Soviet flags (D119)"
below.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSKY1` | the Urals at night over Sverdlovsk, 1024×128 sky (MAPINFO `sky1` of MAP04 and MAP05) | (a) `tools/art/gen_episode2b.py`, seed 5701, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSKY2` | Moscow at night under its sodium glow, 1024×128 sky (MAPINFO `sky1` of MAP06) | (a) `tools/art/gen_episode2b.py`, seed 5702, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDWROF1` | goods-wagon roof with its walkway (flat) | (a) `tools/art/gen_episode2b.py`, seed 5703, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGOND1` | open-wagon floor with coal (flat) | (a) `tools/art/gen_episode2b.py`, seed 5704, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCAB1` | steam locomotive cab, the boiler backhead | (a) `tools/art/gen_episode2b.py`, seed 5705, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCAB2` | steam locomotive cab, the side from inside | (a) `tools/art/gen_episode2b.py`, seed 5706, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSBOX1` | signal-box glazing at night | (a) `tools/art/gen_episode2b.py`, seed 5707, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDLEVR1` | mechanical lever frame from above (flat) | (a) `tools/art/gen_episode2b.py`, seed 5708, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDLEVR2` | mechanical lever frame from the front | (a) `tools/art/gen_episode2b.py`, seed 5709, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRHDR1` | roundhouse road doors | (a) `tools/art/gen_episode2b.py`, seed 5710, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSTAN1` | station board «СВЕРДЛОВСК / СОРТИРОВОЧНЫЙ» in our alphabet, 256×64 | (a) `tools/art/gen_episode2b.py`, seed 5711, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGRIL1` | window bars, masked (RGBA, hard alpha) | (a) `tools/art/gen_episode2b.py`, seed 5712, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDDOORB` | the blue key door, `SDDOOR1`'s leaf, «ПРОПУСК» in our alphabet | (a) `tools/art/gen_episode2b.py`, seed 5713, **palette v2** (`mosaic_cobalt`); the leaf replays `SDDOOR1`'s seed 1982 (gen_soviet_base) like `SDDOORY`/`SDDOORR`, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDHVLT1` | high-voltage fence with the plate «СТОЙ!» in our alphabet, masked (RGBA, hard alpha) | (a) `tools/art/gen_episode2b.py`, seed 5714, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCLOK1` | the Spasskaya tower's clock face | (a) `tools/art/gen_episode2b.py`, seed 5715, **palette v2** (`marble_red`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRUBY1` | the Kremlin's ruby star, masked (RGBA, hard alpha) | (a) `tools/art/gen_episode2b.py`, seed 5716, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGUMS1` | GUM shopfront «ТКАНИ» in our alphabet | (a) `tools/art/gen_episode2b.py`, seed 5717, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGUMS2` | GUM shopfront «ОБУВЬ» in our alphabet | (a) `tools/art/gen_episode2b.py`, seed 5717, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGUMS3` | GUM shopfront «ЧАСЫ» in our alphabet | (a) `tools/art/gen_episode2b.py`, seed 5717, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGUMR1` | the GUM's glass vault from below (flat) | (a) `tools/art/gen_episode2b.py`, seed 5718, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDMUSE1` | the Historical Museum's brick with white dressings | (a) `tools/art/gen_episode2b.py`, seed 5719, **palette v2** (`marble_red`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

## Soviet flags (D119) — the occupiers' banners replaced (P4, approved 2026-10-23 under D113's standing approval)

CEO playtest, D119: the Reich's and the Legion's banners "no pegan: no parece
que sean del enemigo sino del entorno"; all four become Soviet flags, same
lump names and sizes, so the maps change without edits. One generator,
`tools/art/gen_soviet_flags.py`, seed = `BATCH_SEED` 6119 + offset, reading
`gen_factory.py`, `gen_moscow.py`, `ep2lib.py` and `gen_soviet_base.py`
(the approved hammer and sickle, `SDSTAR1`'s geometry). The wall round each
flag is the approved `SDBRCK1` / `SDKREM1` pixel for pixel. No text, no
font, no photograph or flag artwork copied: the emblem is our own vector
geometry. Palette v1 for the cloth, gold, wood and iron; v2 only through the
brick (`marble_red`). The enemies' own armbands and flags (sprites, D108,
D114) are unchanged.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDFLAG1` | the USSR state flag hung vertically from a rod, on `SDBRCK1` | (a) `tools/art/gen_soviet_flags.py`, seed 6120, **palette v2** (only through the brick); the wall is `SDBRCK1` (gen_factory, seed 4101) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDFLAG2` | a Red Army standard on a staff with cord and tassel, on `SDBRCK1` | (a) `tools/art/gen_soviet_flags.py`, seed 6121, **palette v2** (only through the brick); the wall is `SDBRCK1` (gen_factory, seed 4101) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDFLAG3` | a parade gonfalon on a crossbar, emblem in a wreath, on `SDKREM1` | (a) `tools/art/gen_soviet_flags.py`, seed 6122, **palette v2** (`marble_red`, only through the brick); the wall is `SDKREM1` (gen_moscow, seed 5603) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDFLAG4` | the state flag torn and burnt in battle, on `SDKREM1` | (a) `tools/art/gen_soviet_flags.py`, seed 6123, **palette v2** (`marble_red`, only through the brick); the wall is `SDKREM1` (gen_moscow, seed 5603) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

## Episode 3 «The Portal» — textures (P4, approved 2026-10-22 under D113's standing approval)

D113: the CEO approves procedural textures in advance; the PM gate passed
the sheet `docs/art/previews/2026-10-22_P4_episode3-textures.html` on
2026-10-22. 36 lumps in `assets/textures/<arctic|naval|taiga>/` (walls) and
`assets/flats/<arctic|naval|taiga>/` (flats), copied byte for byte from
`work/art/episode3/<set>/`, rendered on the Windows PC on 2026-10-22 and
identical to a fresh render (`tests/test_gen_episode3.py`). All procedural,
seed = the set's `BATCH_SEED` (5700 / 5800 / 5900) + offset, shared code in
`tools/art/ep3lib.py` (on top of `ep2lib.py`). The only lettering («471»,
«ММФ», «3») is set from **our own alphabet** (`assets/fonts/bigfont/`,
D24), never a system font; the invaders' glyphs are invented shapes, not a
script. Palette v1, plus v2's `mosaic_cobalt` for the portal rim only (as
`SDPORT1-4`, D66). No photograph: Novaya Zemlya, Severomorsk and Tunguska
are references for materials and forms only.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSNOW1` | wind-packed snow (flat) | (a) `tools/art/gen_arctic.py`, seed 5701, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDICE1` | sea ice (flat) | (a) `tools/art/gen_arctic.py`, seed 5702, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDICE2` | glacier ice wall | (a) `tools/art/gen_arctic.py`, seed 5703, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRADM1` | radome panels | (a) `tools/art/gen_arctic.py`, seed 5704, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDHUT1` | frosted corrugated barracks wall | (a) `tools/art/gen_arctic.py`, seed 5705, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRADR1` | radar console, animation frame 1 of 4 | (a) `tools/art/gen_arctic.py`, seed 5706, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRADR2` | radar console, frame 2 | (a) `tools/art/gen_arctic.py`, seed 5706, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRADR3` | radar console, frame 3 | (a) `tools/art/gen_arctic.py`, seed 5706, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRADR4` | radar console, frame 4 | (a) `tools/art/gen_arctic.py`, seed 5706, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDHERM1` | frosted hermetic blast door | (a) `tools/art/gen_arctic.py`, seed 5707, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRWY1` | airfield runway slabs (flat) | (a) `tools/art/gen_arctic.py`, seed 5708, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRWY2` | runway slabs with the centre line (flat) | (a) `tools/art/gen_arctic.py`, seed 5708, palette v1; replays `SDRWY1`'s seed on purpose | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDHULL1` | submarine hull, anechoic tiles | (a) `tools/art/gen_naval.py`, seed 5801, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDHULL2` | the hull with the number «471» in our alphabet | (a) `tools/art/gen_naval.py`, seed 5801, palette v1; replays `SDHULL1`'s seed on purpose, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRUBR1` | anechoic rubber deck (flat) | (a) `tools/art/gen_naval.py`, seed 5802, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDRUBR2` | the deck with an escape hatch (flat) | (a) `tools/art/gen_naval.py`, seed 5802, palette v1; replays `SDRUBR1`'s seed on purpose | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDROCK1` | excavated living rock (wall) | (a) `tools/art/gen_naval.py`, seed 5803, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDROCK2` | excavated living rock (ceiling flat) | (a) `tools/art/gen_naval.py`, seed 5804, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBULK1` | round watertight door, «3» in our alphabet | (a) `tools/art/gen_naval.py`, seed 5805, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDNAVC1` | submarine control-room panel | (a) `tools/art/gen_naval.py`, seed 5806, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCONT1` | shipping container, «ММФ» in our alphabet | (a) `tools/art/gen_naval.py`, seed 5807, palette v1, no system font | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCRAN1` | quay crane jib lattice, masked (RGBA, hard alpha) | (a) `tools/art/gen_naval.py`, seed 5808, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDPIER1` | concrete quay with a bollard (flat) | (a) `tools/art/gen_naval.py`, seed 5809, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBARK1` | birch bark | (a) `tools/art/gen_taiga.py`, seed 5901, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBARK2` | burnt larch bark | (a) `tools/art/gen_taiga.py`, seed 5902, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDLOGW1` | log-cabin wall | (a) `tools/art/gen_taiga.py`, seed 5903, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDPEAT1` | peat bog (flat) | (a) `tools/art/gen_taiga.py`, seed 5904, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBURN1` | burnt ground (flat) | (a) `tools/art/gen_taiga.py`, seed 5905, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDMOSS1` | moss and lichen (flat) | (a) `tools/art/gen_taiga.py`, seed 5906, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDALNM1` | the invaders' organic metal | (a) `tools/art/gen_taiga.py`, seed 5907, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDACID1` | the invaders' acid, animation frame 1 of 4 (flat) | (a) `tools/art/gen_taiga.py`, seed 5908, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDACID2` | the acid, frame 2 (flat) | (a) `tools/art/gen_taiga.py`, seed 5908, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDACID3` | the acid, frame 3 (flat) | (a) `tools/art/gen_taiga.py`, seed 5908, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDACID4` | the acid, frame 4 (flat) | (a) `tools/art/gen_taiga.py`, seed 5908, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGLYP1` | invader glyph plate (an invented grammar, not letters) | (a) `tools/art/gen_taiga.py`, seed 5909, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDPRTE1` | the portal's rim | (a) `tools/art/gen_taiga.py`, seed 5910, **palette v2** (`mosaic_cobalt`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

## Episode 3 — skies (P4, approved 2026-10-22 under D113's standing approval)

Three 1024×128 skies for MAPINFO's `sky1` of MAP07-09, in
`assets/textures/sky/`, copied byte for byte from
`work/art/episode3_skies/sky/` (rendered on the Windows PC on 2026-10-22,
identical to a fresh render, `tests/test_gen_episode3_skies.py`). All
procedural, one generator, `tools/art/gen_episode3_skies.py`, seed =
`BATCH_SEED` 6000 + offset, on top of `gen_episode2b.py` and `ep2lib.py`
(read only). No lettering, no photograph. Preview
`docs/art/previews/2026-10-22_P4_episode3-skies.png`.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSKY3` | the polar night with aurora over Novaya Zemlya, 1024×128 sky (MAPINFO `sky1` of MAP07) | (a) `tools/art/gen_episode3_skies.py`, seed 6001, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSKY4` | the Kola fjord at Severomorsk at night, 1024×128 sky (MAPINFO `sky1` of MAP08) | (a) `tools/art/gen_episode3_skies.py`, seed 6002, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSKY5` | the Tunguska taiga with the portal's cobalt glow, 1024×128 sky (MAPINFO `sky1` of MAP09) | (a) `tools/art/gen_episode3_skies.py`, seed 6003, **palette v2** (`mosaic_cobalt`, only near the portal) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

## Episode 1 — skies (P4, approved 2026-10-22 under D113's standing approval)

Two 1024×128 skies for MAPINFO's `sky1` of MAP01 and RANGE (`SDSKY6`) and
MAP03 (`SDSKY7`), in `assets/textures/sky/`, copied byte for byte from
`work/art/episode1_skies/sky/` (rendered on the Windows PC on 2026-10-22,
identical to a fresh render, `tests/test_gen_episode1_skies.py`). All
procedural, one generator, `tools/art/gen_episode1_skies.py`, seed =
`BATCH_SEED` 6010 + offset, on top of `gen_episode2b.py`,
`gen_episode3_skies.py` and `ep2lib.py` (read only). No lettering, no
photograph, no reference image. Preview
`docs/art/previews/2026-10-22_P4_episode1-skies.png`.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSKY6` | the Zarya-7 cosmodrome on the steppe before dawn, a rocket on its pad, 1024×128 sky (MAPINFO `sky1` of MAP01 and RANGE) | (a) `tools/art/gen_episode1_skies.py`, seed 6011, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDSKY7` | Tankograd at night, cloud lit orange by the blast furnaces, 1024×128 sky (MAPINFO `sky1` of MAP03) | (a) `tools/art/gen_episode1_skies.py`, seed 6012, palette v1 | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |

## V3 — the operations map and the awards (B1, B3; PROPOSAL, 2026-10-23, ADR 013)

**Not approved yet.** Installed in `assets/graphics/opsmap/` and
`assets/graphics/medals/` on the V3 branch only, so the package and its tests
are whole; the awards are Soviet decorations (political symbols), which
D113's standing approval does not cover, so the CEO decides on the preview
`docs/art/previews/2026-10-23_V3_ops-map-medals.png` before the PM takes
them into a release. All procedural, own work: `tools/art/gen_ops_map.py`
(seed 1977), `tools/art/gen_medals.py` (no randomness), helpers
`tools/art/v3lib.py`, geography `tools/art/opsmap_geo.py` (the USSR's
outline, rivers, the Trans-Siberian and the nine sites traced by hand from
general knowledge: no map data, atlas or picture was downloaded or copied).
The emblem on the map is the approved geometry of `SDSTAR1` v5
(`gen_soviet_base`), the stars `artlib.star_points`'s. No lettering on any
picture and no font opened (D27); the preview's labels are set in the mod's
own folder fonts. No portrait of any real person: the Order of Lenin
(Lenin's profile) is not drawn, the Order of the Red Star's soldier is
replaced by a plain disc; the Order of Glory is not drawn either (ADR 013:
its orange-and-black ribbon).

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDOPMAP` | the operations map, 320×200 intermission background: the USSR (warped round the Urals), rivers, the Trans-Siberian, a 10° graticule, the nine sites, the state emblem | (a) `tools/art/gen_ops_map.py`, seed 1977, palette v2, geography `opsmap_geo.py` (own approximation) | Soviet Doom project (mod-engineer/art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDOPR02`, `SDOPR03`, `SDOPR04`, `SDOPR05`, `SDOPR06`, `SDOPR07`, `SDOPR08`, `SDOPR09` | the red arrow into each map from the one before | (a) `tools/art/gen_ops_map.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDOPSTAR`, `SDOPCUR0`, `SDOPCUR1`, `SDOPYAH0` | a taken site (red star, gold rim), the two frames of the pulse where the player is, the blinking "you are here" ring | (a) `tools/art/gen_ops_map.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDOPSCR` | the intermission script (text lump, root) that places all of the above | generated by `tools/art/gen_ops_map.py` into `src/lumps/` | Soviet Doom project, own work, GPL-3.0 like the mod's code |
| `SDAWCOU` | award: Medal "For Courage" (stylised: silver disc, aircraft, a blank red band, a tank; grey ribbon, blue edges) | (a) `tools/art/gen_medals.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDAWRST` | award: Order of the Red Star (a red star, a silver centre without the soldier) | (a) `tools/art/gen_medals.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDAWRBN` | award: Order of the Red Banner (gold wreath, red star, red banner) | (a) `tools/art/gen_medals.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDAWPTW` | award: Order of the Patriotic War (gold sunburst, red star, crossed rifle and sabre) | (a) `tools/art/gen_medals.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |
| `SDAWHER` | award: Gold Star of the Hero of the Soviet Union (gold star on a red bar) | (a) `tools/art/gen_medals.py`, palette v2 | Soviet Doom project, own work, CC BY-NC-SA 4.0 (D15) |

## Music (D43, installed 2026-10-13)

Rows added by `sound-designer` so `tools/check_pk3.py` can see the music
lumps' provenance. N9e (2026-10-20) added `D_SDTITL` (D83) and `D_SDM01T`
(D86) and removed `D_SDAMUR`, which the CEO rejected for the range (D83)
and which no longer ships; D95 put `D_SDM1N2` on MAP01 and `D_SDM01`, MAP01's
D43 theme, no longer ships either (its cut `D_SDM01T` does). D106 (2026-10-22) added episode 2's ten pieces, `D_SDM04A` to `D_SDE2IB`; D113 (2026-10-22) episode 3's ten, `D_SDM07A` to `D_SDE3IB`. The full rights analysis — composition, lyrics,
phonogram and sequencing, each with its source — is owned by
`docs/sound/MUSIC-RIGHTS.md` §4.4; these rows only point at it. Files in
`assets/music/`, packed as `music/<LUMP>.mid`.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `D_SDINTL` | title theme: *The Internationale* (De Geyter, 1888), orchestral MIDI | sequenced by **Jerry Engelbach** (2003), Wikimedia Commons `File:Internationale_orch2.mid`; 1.99 s of head silence removed by us (`tools/audio/midi_edit.py --trim-head`) | melody public domain (`{{PD-Internationale}}`); sequencing `{{Attribution\|Jerry Engelbach}}` — **credit "Jerry Engelbach" is required** |
| `D_SDM1N2` | MAP01 (Zarya-7) music since D95: an original piece in the style of `D_SDM01T`, 48 bars of 4/4 in D minor at 128 BPM, a 1:30 loop | original composition, `tools/audio/compose_map01.py` (variant `D_SDM01N2`, sound-designer, 2026-10-20; D92's one exception to D59); installed by N9e 2026-10-20 byte-identical to `work/audio/D_SDM01N2.mid` under the 8-letter lump name | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDRAD1` | diegetic radio (`SD_Radio`, MOD-SPEC §6.7): «Эй, ухнем» / *Ey, ukhnem* (Volga Boatmen), Balakirev's setting, pub. 1866 | sequenced by **Peter Gerloff** (Commons: *Rabanus Flavus*, 2021), Wikimedia Commons `File:Ej,_uchnem!.mid`; installed by `mod-engineer` 2026-10-13 byte-identical to `work/audio/candidates/WM_Ej_uchnem.mid` (`D_CND09`), unedited | composition public domain (RU and US); sequencing CC0 1.0 (`{{self\|Cc-zero}}`) — no obligation; Gerloff credited as a courtesy |
| `D_SDRAD2` | diegetic radio (`SD_Radio`, MOD-SPEC §6.7): «Колокольчик» / *Kolokolchik*, Russian traditional | sequenced by **Peter Gerloff** (2019), Wikimedia Commons `File:Kolokolchik.mid`; installed by `mod-engineer` 2026-10-13 byte-identical to `work/audio/candidates/WM_Kolokolchik.mid` (`D_CND12`), unedited | composition public domain (RU and US); sequencing CC0 1.0 (`{{self\|Cc-zero}}`) — no obligation; Gerloff credited as a courtesy |
| `D_SDFUNR` | MAP02 (the metro) music, **D62 draft pending the CEO's ear**: «Вы жертвою пали» / *Vy zhertvoyu pali*, revolutionary funeral march, 1870s, voice line as printed in Detlaf's 1905 Moscow edition | sequenced by `sound-designer` under D44 (`tools/audio/gen_music.py`, `build_funeral`); installed 2026-10-14 byte-identical to `work/audio/D_SDFUNR.mid`; score provenance `docs/sound/MUSIC-RIGHTS.md` §4.6.1 | composition public domain (RU and US); our sequencing CC BY-NC-SA 4.0 (D15); no lyric, no phonogram |
| `D_SDGATE` | MAP03 (Tankograd) music, **D62 draft pending the CEO's ear**: «Богатырские ворота» / *Bogatyrskie vorota* (The Great Gate of Kiev), Mussorgsky, *Pictures at an Exhibition* No. 10, 1874, top voice as printed in Bessel's 1886 edition | sequenced by `sound-designer` under D54 (`tools/audio/gen_music.py`, `build_gate`); installed 2026-10-14 byte-identical to `work/audio/D_SDGATE.mid`; score provenance `docs/sound/MUSIC-RIGHTS.md` §4.6.4 | composition public domain (Mussorgsky d. 1881, pub. 1886; RU and US); our sequencing CC BY-NC-SA 4.0 (D15); no phonogram |
| `D_SDTITL` | intermission (the stats screen between maps; GameInfo `IntermissionMusic`, D83), "Zarya", a Soviet march in D minor | original composition, `tools/audio/gen_music.py` (`build_title`, sound-designer, 2026-10-13); installed by N9e 2026-10-20 byte-identical to `work/audio/D_SDTITL.mid` | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM01T` | RANGE (practice range) music since D86: MAP01's theme `D_SDM01E` cut to its melodic part (from bar 49, where the horns take the melody) | our own sequence edited, not composed (D59): `tools/audio/gen_music.py` (`D_SDM01E`), cut by `tools/audio/gen_enemy_alts.py` (`trim_midi`); installed by N9e 2026-10-20 byte-identical to `work/audio/D_SDM01T.mid` | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM04A` | MAP04 (Trans-Siberian) music since D106, variant A (MAPINFO's `music`): rail-yard ostinato and brass, 138 BPM, a 2:05 loop | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM04A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM04B` | MAP04 variant B, drawn at random by `SD_MusicVariant` (MOD-SPEC §6.11): same motif, other B section, 132 BPM, 2:11 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM04B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM05A` | MAP05 (Volga Dam) music since D106, variant A: broad, organ hum under the bass, 116 BPM, 2:12 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM05A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM05B` | MAP05 variant B (`SD_MusicVariant`): 108 BPM, 2:22 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM05B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM06A` | MAP06 (Red Square) music since D106, variant A: march and brass choir, 120 BPM, 2:24 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM06A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM06B` | MAP06 variant B (`SD_MusicVariant`): 112 BPM, 2:34 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDM06B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDBS6A` | MAP06's boss loop with variant A (`SD_MusicVariant`, when a BOSS monster engages): bars 29-52 of `D_SDM06A` cut as their own loop, 0:48 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDBS6A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDBS6B` | MAP06's boss loop with variant B: bars 29-52 of `D_SDM06B`, 0:51 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDBS6B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDE2IA` | episode 2's intermission (the stats screen after MAP04 and MAP05, MAPINFO `intermusic`, D106): the three maps' motifs in one 16-bar loop, 92 BPM, 0:42 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDE2IA.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDE2IB` | episode 2's intermission, variant B (approved, packed, not wired: the engine picks the stats screen's music itself), 104 BPM, 0:37 | original composition, `tools/audio/compose_episode2.py` (sound-designer, 2026-10-21; D104 brief, approved by the CEO with its pair in D106, "10/10 OK"); installed 2026-10-22 byte-identical to `work/audio/episode2/D_SDE2IB.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM07A` | MAP07 (Novaya Zemlya) music since D113, variant A (MAPINFO's `music`): radar pings on celesta, horns, tremolo strings, 116 BPM, a 2:21 loop | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM07A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM07B` | MAP07 variant B, drawn at random by `SD_MusicVariant` (MOD-SPEC §6.11): same motif, vibraphone and glockenspiel, another B section, 122 BPM, 2:14 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM07B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM08A` | MAP08 (Severomorsk) music since D113, variant A: low brass, shipyard metal, sonar, 124 BPM, 2:12 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM08A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM08B` | MAP08 variant B (`SD_MusicVariant`): 120 BPM, 2:16 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM08B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM09A` | MAP09 (Tunguska) music since D113, variant A: brass choir and church organ over a semiquaver ostinato, 132 BPM, 2:04 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM09A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDM09B` | MAP09 variant B (`SD_MusicVariant`): 138 BPM, 1:58 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDM09B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDBS9A` | MAP09's final boss loop with variant A (`SD_MusicVariant`, when a BOSS monster engages): a piece of its own, not a cut, 140 BPM, 1:09 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDBS9A.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDBS9B` | MAP09's final boss loop with variant B: 146 BPM, 1:06 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDBS9B.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDE3IA` | episode 3's intermission (the stats screen after MAP07 and MAP08, MAPINFO `intermusic`, D113): the three maps' motifs in one 16-bar loop, 96 BPM, 0:40 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDE3IA.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDE3IB` | episode 3's intermission, variant B (approved, packed, not wired: the engine picks the stats screen's music itself), 108 BPM, 0:36 | original composition, `tools/audio/compose_episode3.py` (sound-designer, 2026-10-22; D112 brief, approved unheard by the CEO with its pair in D113, who accepted them as they are, his words verbatim in the PRD's D113); installed 2026-10-22 byte-identical to `work/audio/episode3/D_SDE3IB.mid`; quotes no other work (the generator's self-check) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |

## Weapon sounds (F4, approved by the CEO 2026-10-15, D74; installed by N9)

The 25 weapon sounds the CEO marked OK on the M3 listening sheet (D74), in
the take he chose, after the loudness pass of backlog N9. Files in
`assets/sounds/weapons/<LUMP>.ogg`, packed as `sounds/<LUMP>.ogg`;
`src/lumps/SNDINFO` maps the logical names to them. Every one is **our own
work**: the shots, booms, whooshes, hisses, rings and the relay buzz are
synthesis (`tools/audio/gen_weapon_sfx.py`, fixed seeds), and the mechanical
foley mixes in short clips of two CC0 packs already on disk under D36, cut,
re-pitched, filtered and always layered, never alone: `OGA-100`, rubberduck's
*100 CC0 SFX* (OpenGameArt), and `KEN-IMP`, Kenney's *Impact Sounds*
(kenney.nl). No recording of a real firearm is used. Pack rows, URLs and
archive hashes: `docs/sound/ENEMY-SOUNDS.md` §2.1; the SHA-256 of every
source file and which lump uses it: `docs/sound/WEAPON-SOUNDS.md` §2.1. The
mastering (gain, a low shelf on the bass-only sounds, a look-ahead limiter;
nothing re-synthesised) and each file's SHA-256: WEAPON-SOUNDS §10.

CC0 asks for nothing. The project's rule for CC0 names is a courtesy credit
(ADR 009); Kenney and rubberduck are not in the in-game credits yet: that
line is owed in `LANGUAGE` (both languages) by whoever owns the credits
screen, and is not a licence obligation.

Not installed (D74 NO or "?"): the drafts `SDTTPKP`, `SDIZRLD`, `SDRKFIR`,
`SDAXPKP`, `SDIZPKP`. D94 (N9e, 2026-10-20) approved alternatives of the
first four from `tools/audio/gen_weapon_alts.py` (same packs, same rules),
rows below (`SDTTPKP1`-`2`, `SDAXPKP1`/`3`, `SDIZRLD`, `SDRKFIR1`-`3`); the
IZh-58's pickup keeps Doom's generic sound (all three alternatives NO). `SDIZFIR` (take B) was
approved by D83 and installed by N9e on 2026-10-20.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDAXSWG` | ice axe, swing | `gen_weapon_sfx.py` take C, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDAXHIT` | ice axe, flesh hit | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `KEN-IMP` impactMetal_light_002, `KEN-IMP` impactPunch_heavy_000, `KEN-IMP` impactSoft_heavy_001 | idem |
| `SDAXWAL` | ice axe, wall hit | `gen_weapon_sfx.py` take C, mastered by `master_weapon_sfx.py`; CC0 layers: `KEN-IMP` impactMining_002, `KEN-IMP` impactMetal_light_003 | idem |
| `SDTTFIR` | TT-33, shot | `gen_weapon_sfx.py` take B, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01 | idem |
| `SDTTRLD` | TT-33, reload (parked: no reload state, D47) | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01, `OGA-100` metal_02, `OGA-100` switch_02, `OGA-100` metal_11 | idem |
| `SDTTDRY` | TT-33, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01 | idem |
| `SDIZDRY` | IZh-58, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01, `KEN-IMP` impactGeneric_light_000 | idem |
| `SDIZFIR` | IZh-58, shot (D83, installed by N9e) | `gen_weapon_sfx.py` take B, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPPFIR` | PPSh-41, shot | `gen_weapon_sfx.py` take C, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_02, `OGA-100` spring_04 | idem |
| `SDPPRLD` | PPSh-41, reload (parked: no reload state, D47) | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_02, `OGA-100` metal_03, `OGA-100` spring_04, `OGA-100` metal_09, `OGA-100` spring_06, `OGA-100` switch_01, `OGA-100` metal_02 | idem |
| `SDPPPKP` | PPSh-41, pickup | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `KEN-IMP` impactWood_medium_002, `KEN-IMP` impactMetal_light_003, `OGA-100` spring_04, `OGA-100` switch_02 | idem |
| `SDPPDRY` | PPSh-41, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_02, `OGA-100` switch_02, `KEN-IMP` impactMetal_medium_002 | idem |
| `SDRPFIR` | RPG-7, shot | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDRPEXP` | RPG-7, explosion | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDRPRLD` | RPG-7, reload | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_07, `OGA-100` switch_01 | idem |
| `SDRPPKP` | RPG-7, pickup | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `KEN-IMP` impactWood_light_000, `OGA-100` metal_07, `KEN-IMP` impactMetal_medium_000 | idem |
| `SDRPDRY` | RPG-7, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01, `KEN-IMP` impactMetal_medium_004 | idem |
| `SDRKRLD` | ROKS-3, reload (parked: no reload state, D47) | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_01, `OGA-100` switch_02 | idem |
| `SDRKPKP` | ROKS-3, pickup | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_01, `KEN-IMP` impactTin_medium_001, `OGA-100` splash_01 | idem |
| `SDRKDRY` | ROKS-3, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_02 | idem |
| `SDHKCHG` | hand Katyusha, charge | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_03, `KEN-IMP` impactMetal_heavy_003 | idem |
| `SDHKFIR` | hand Katyusha, shot | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDHKEXP` | hand Katyusha, per-rocket burst | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDHKRLD` | hand Katyusha, reload | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` metal_02, `OGA-100` metal_09, `OGA-100` switch_01 | idem |
| `SDHKPKP` | hand Katyusha, pickup | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `KEN-IMP` impactMetal_heavy_001, `OGA-100` metal_12 | idem |
| `SDHKDRY` | hand Katyusha, empty click | `gen_weapon_sfx.py` take A, mastered by `master_weapon_sfx.py`; CC0 layers: `OGA-100` switch_01 | idem |
| `SDTTPKP1` | TT-33, pickup (take 1 of the `$random` group, D94) | `gen_weapon_alts.py` SDTTPKP alt1, installed as the CEO heard it by `master_weapon_sfx.py --alts`; CC0 layers: `KEN-IMP` impactMetal_light_004, `OGA-100` switch_01, `KEN-IMP` impactMetal_light_002, `OGA-100` metal_02, `KEN-IMP` impactMetal_light_000, `OGA-100` switch_02 | idem |
| `SDTTPKP2` | TT-33, pickup (take 2 of the `$random` group, D94) | `gen_weapon_alts.py` SDTTPKP alt2, its peaks limited 0.9 dB by `master_weapon_sfx.py --alts` (codec check); CC0 layers: `KEN-IMP` impactSoft_medium_001, `KEN-IMP` impactSoft_medium_003, `KEN-IMP` impactMetal_light_004, `OGA-100` switch_01 | idem |
| `SDAXPKP1` | ice axe, pickup (take 1 of the `$random` group, D94) | `gen_weapon_alts.py` SDAXPKP alt1, installed as the CEO heard it by `master_weapon_sfx.py --alts`; CC0 layers: `KEN-IMP` footstep_concrete_002, `KEN-IMP` impactMetal_light_003, `KEN-IMP` impactMining_001 | idem |
| `SDAXPKP3` | ice axe, pickup (take 3 of the `$random` group, D94) | `gen_weapon_alts.py` SDAXPKP alt3, installed as the CEO heard it by `master_weapon_sfx.py --alts`; CC0 layers: `KEN-IMP` impactPunch_medium_002, `KEN-IMP` impactWood_medium_003, `KEN-IMP` impactMetal_medium_001, `KEN-IMP` impactMetal_light_004 | idem |
| `SDIZRLD` | IZh-58, reload (break-open) (D94) | `gen_weapon_alts.py` SDIZRLD alt3, its peaks limited 0.5 dB by `master_weapon_sfx.py --alts` (codec check); CC0 layers: `OGA-100` metal_06, `OGA-100` switch_02, `KEN-IMP` impactMetal_heavy_000, `KEN-IMP` impactPlate_light_002, `KEN-IMP` impactGeneric_light_002, `KEN-IMP` impactWood_medium_003, `KEN-IMP` impactMetal_light_004, `KEN-IMP` impactPlate_heavy_000, `KEN-IMP` impactMetal_medium_004, `OGA-100` spring_07 | idem |
| `SDRKFIR1` | ROKS-3, the jet (take 1 of the `$random` group, D94) | `gen_weapon_alts.py` SDRKFIR alt1, its peaks limited 0.7 dB by `master_weapon_sfx.py --alts` (codec check); CC0 layers: none, synthesis only | idem |
| `SDRKFIR2` | ROKS-3, the jet (take 2 of the `$random` group, D94) | `gen_weapon_alts.py` SDRKFIR alt2, installed as the CEO heard it by `master_weapon_sfx.py --alts`; CC0 layers: none, synthesis only | idem |
| `SDRKFIR3` | ROKS-3, the jet (take 3 of the `$random` group, D94) | `gen_weapon_alts.py` SDRKFIR alt3, installed as the CEO heard it by `master_weapon_sfx.py --alts`; CC0 layers: none, synthesis only | idem |

## Enemy sounds (F5, approved by the CEO 2026-10-20, D83 and D86; installed by N9e)

The enemy sounds and beds the CEO approved on the M3 listening sheet (D83:
30 sounds and 5 beds) and on the alternatives page (D86: the takes listed
in `docs/PRD.md`; SDRRIATK alt2 after its final click was lowered), after
a loudness pass (`tools/audio/master_enemy_sfx.py`, ENEMY-SOUNDS §5.12).
Files in `assets/sounds/enemies/<LUMP>.ogg`, packed as `sounds/<LUMP>.ogg`;
`src/lumps/SNDINFO` maps the logical names to them, with `$random` where
several takes of one sound were approved. Every one is **our own work**:
synthesis (`tools/audio/gen_sfx.py`, `tools/audio/gen_enemy_alts.py`,
fixed seeds) that layers, cut, re-pitched and filtered, short clips of
the CC0 packs on disk under D36 (`OGA-CRE1`, `OGA-CRE2` and `OGA-100`,
rubberduck's packs on OpenGameArt; `KEN-IMP`, Kenney's *Impact Sounds*),
never alone. Pack rows, URLs, archive hashes and the SHA-256 of every
source file: `docs/sound/ENEMY-SOUNDS.md` §2.1 and §5.9 (the drafts) and
`tools/audio/gen_enemy_alts.py` `SOURCES` (the alternatives). **Three gibs
also edit Freedoom's `DSSLOP`** (`SDRRIXDT`, `SDLTRXDT`, `SDSTOXDT`): a
derivative of a Freedoom sound, shipped under Freedoom's licence with its
credit, the PK3's only Freedoom-derived material since D123 ("Base IWAD"
above, which also writes the licence's obligations), with the two player
takes that layer `SDRRIXDT` since D125 (`SDSGXDT1`, `SDSGXDT2`, "World
sounds" below).

The beds (`SD...B<n>`) are packed and named but played by nothing until
they are mixed under the voice takes (D87). Not installed (D83 NO, D86 NO):
the drafts `SDRRIATK`, `SDLTRATK`, `SDSTOPAI`, `SDSTODTH`, `SDPZRPAI`, the
beds of `SDRRIPAI`, `SDLTRPAI`, `SDLTRDTH`, and the Legion shotgun's
alternatives 1 and 3; four of the twelve voices keep their Freedoom
stand-ins (the rifleman's pain, the trooper's death, the General's pain
and death); the other eight are D91's and D96's takes, last rows.
CC0 asks for nothing; the courtesy credit to Kenney and rubberduck is the
weapon sounds' (above).

**Seven voice takes (D91).** The last rows are the voice lines the CEO
approved of the Chatterbox drafts (D87): the rifleman's "Kontakt!" and the
trooper's two idle radio lines, generated locally with Chatterbox
Multilingual and its predefined male voices, processed by us. Each row
names Chatterbox, which `tools/release.py` reads to state in the release
that some voice lines ship (D93). The predefined voices' own origin is not
documented by their distributor: risk R1 of D87, accepted by the CEO.

**Seventeen voice takes (D96).** The rows after them are the takes the CEO
approved of the aggressive round
(`docs/art/previews/2026-10-20_1330_P2_voice-takes-aggressive.html`):
Chatterbox Multilingual run locally, each voice **cloned from a shouted
reference clip**, which is named in the row and **not distributed** (it
lives in the gitignored `work/`; `AI-LOG.csv` gives each take's reference,
its SHA-256, the text, the seed and the settings). Three references:
Thorsten Müller's "angry" style of the Thorsten-Voice emotional dataset
(CC0), kurt's "Soldier Voice Acting" (CC-BY 3.0, OpenGameArt) and HaelDB's
"Male Grunt/Yelling sounds" (CC0). The cloned voice is a derivative of the
reference at most, so kurt is credited as CC-BY asks: `credit "kurt"` in
those rows, which `tools/release.py` requires of both languages' in-game
credits (`SD_CRED_SFX_3`, "Voice reference: kurt, CC-BY 3.0.") and quotes,
with the work's title and address, in CREDITS.txt; Thorsten Müller, Dominik
Kreutz and HaelDB (CC0) are named in their rows by courtesy. Every take ships as the OGG of the CEO's page but
`SDGENSU1` (G02 t13), whose peak the codec pass limited by 0.6 dB, the
pass of the D83/D86 sounds (ENEMY-SOUNDS §5.12).

**Seven voice takes (D110).** The last rows are the takes the CEO approved
of the P2 round of the wordless voices
(`work/audio/preview/voices_p2_listening.html`): the rifleman's pain (R07
t06, t02), the Legion trooper's death (L09 t01, t02, t04) and the General's
pain (G03 t06, t04). The same model and the same three references as D96,
run on the CPU in the server's own Python; each row names its take and
reference (`work/audio/voice_takes/p2/AI-LOG.csv`, not distributed). kurt's
takes reuse his "Soldier Voice Acting" (wounded.ogg as well as
battlecries.ogg, the same work, so the same `credit "kurt"`, already in
both languages' credits and in CREDITS.txt). All ship as the page's OGG but
`SDLTRDT3` (L09 t04), whose tail is cut (ENEMY-SOUNDS §5.12). The General's
death (G04) was all NO and was redrafted: see D118 below.

**Five voice takes (D118).** The General's death, redrafted in the P2b
round (`work/audio/preview/voices_p2b_listening.html`): the CEO approved
G04 t01, t07, t08, t05, t12 (NO t10, t03, t04), `SDGENDT1`-`5` in that
order. The same model and CPU run as D110, all five cloned from kurt's
"Soldier Voice Acting" (wounded.ogg and battlecries.ogg, or battlecries.ogg
alone: the same work, the same `credit "kurt"`, already in both languages'
credits and in CREDITS.txt); each row names its take
(`work/audio/voice_takes/p2b/AI-LOG.csv`, not distributed). All five ship
byte for byte as the page's OGGs. With them the twelve enemy voices are all
ours: no enemy voice plays a Freedoom lump.

**The Reich hound's real dogs (D107).** The hound's five sounds are no
longer D83's synthesis (`SDHNDACT`-`SDHNDDTH` no longer ship): the CEO
approved all fifteen candidates of `work/audio/preview/dog_listening.html`
and each sound is a `$random` group of its three takes (`SDHNDAC1`-`3`,
`SDHNDSI1`-`3`, `SDHNDAT1`-`3`, `SDHNDPA1`-`3`, `SDHNDDT1`-`3`). Unlike
the rows above they are **recordings of real dogs**, cut, re-pitched,
filtered, mixed and levelled by us: BigSoundBank's (Joseph Sardin) and
OpenGameArt's (qubodup, pauliuw) CC0 recordings, two Kenney clips already
here, and congusbongus' "Dog growls" (OpenGameArt, **CC BY 3.0**), cut from
juskiddink's "Dogs growling.wav" (Freesound #121565). The CC BY rows owe a
credit to both, `credit "congusbongus" credit "juskiddink"`, which
`tools/release.py` requires of every language's in-game credits
(`SD_CRED_SFX_6`, `SD_CRED_SFX_7`) and quotes with the work's title,
address and changes in CREDITS.txt; the CC0 authors are credited by
courtesy (`SD_CRED_SFX_4`, `SD_CRED_SFX_5`). The downloads, their SHA-256
and which take mixes which file: `work/audio/sfx_sources/dog/SOURCES.md`
(not distributed); the install: ENEMY-SOUNDS §5.12.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDRRIXDT` | Reich rifleman, gib | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; Freedoom's `DSSLOP` (freedoom2.wad:DSSLOP) edited and layered | Freedoom's `DSSLOP`: modified BSD licence (BSD 3-clause), © the Contributors to the Freedoom project, credit "Freedoom"; the edit and the synthesis: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDLTRXDT` | Legion trooper, gib | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; Freedoom's `DSSLOP` (freedoom2.wad:DSSLOP) edited and layered | idem |
| `SDSTOACT` | Hybrid Stormtrooper, idle | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` breath, `OGA-CRE2` breath_02 | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDSTOSIT` | Hybrid Stormtrooper, sight | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` monster_06, `OGA-CRE1` alien_03 | idem |
| `SDSTOMEL` | Hybrid Stormtrooper, melee | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPunch_medium_001, `KEN-IMP` impactMetal_light_002 | idem |
| `SDSTOMIS` | Hybrid Stormtrooper, missile launch | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDSTOEXP` | Hybrid Stormtrooper, missile impact | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDSTOXDT` | Hybrid Stormtrooper, gib | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; Freedoom's `DSSLOP` (freedoom2.wad:DSSLOP) edited and layered | Freedoom's `DSSLOP`: modified BSD licence (BSD 3-clause), © the Contributors to the Freedoom project, credit "Freedoom"; the edit and the synthesis: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAC1` | Reich hound, idle: a real dog, take 1 of the `$random` group (D107, the page's recommendation) | "Dog growls" (2.ogg) by congusbongus, OpenGameArt, https://opengameart.org/content/dog-growls, itself cut from "Dogs growling.wav" by juskiddink, Freesound #121565, https://freesound.org/people/juskiddink/sounds/121565/; cut, pitched, filtered, mixed and levelled to `DSDMACT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDACT_dog1`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | the growl: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/, the OpenGameArt page; the Freesound original is CC BY 4.0 today), modified as the Origin says, credit "congusbongus" credit "juskiddink" (the in-game credits, SD_CRED_SFX_6, and CREDITS.txt); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAC2` | Reich hound, idle: a real dog, take 2 of the `$random` group (D107) | BigSoundBank #1547 "Dogs breathing" by **Joseph Sardin**, https://bigsoundbank.com/dogs-breathing-s1547.html; "Dog growls" (0.ogg) by congusbongus, OpenGameArt, https://opengameart.org/content/dog-growls, itself cut from "Dogs growling.wav" by juskiddink, Freesound #121565, https://freesound.org/people/juskiddink/sounds/121565/; cut, pitched, filtered, mixed and levelled to `DSDMACT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDACT_dog2`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | the growl: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/, the OpenGameArt page; the Freesound original is CC BY 4.0 today), modified as the Origin says, credit "congusbongus" credit "juskiddink" (the in-game credits, SD_CRED_SFX_6, and CREDITS.txt); the other layer: CC0 1.0, courtesy credit; the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAC3` | Reich hound, idle: a real dog, take 3 of the `$random` group (D107) | "Dog snarl, grunt, grumble" (dog-grumble.flac) by **qubodup**, OpenGameArt, https://opengameart.org/content/dog-snarl-grunt-grumble; "Dog snarl, grunt, grumble" (dog-growl.flac) by **qubodup**, OpenGameArt, https://opengameart.org/content/dog-snarl-grunt-grumble; cut, pitched, filtered, mixed and levelled to `DSDMACT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDACT_dog3`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDSI1` | Reich hound, sight: a real dog, take 1 of the `$random` group (D107) | "Dog growls" (3.ogg) by congusbongus, OpenGameArt, https://opengameart.org/content/dog-growls, itself cut from "Dogs growling.wav" by juskiddink, Freesound #121565, https://freesound.org/people/juskiddink/sounds/121565/; BigSoundBank #0112 "Barking dog inside" (a German shepherd) by **Joseph Sardin**, https://bigsoundbank.com/barking-dog-inside-s0112.html; cut, pitched, filtered, mixed and levelled to `DSSGTSIT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDSIT_dog1`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | the growl: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/, the OpenGameArt page; the Freesound original is CC BY 4.0 today), modified as the Origin says, credit "congusbongus" credit "juskiddink" (the in-game credits, SD_CRED_SFX_6, and CREDITS.txt); the other layer: CC0 1.0, courtesy credit; the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDSI2` | Reich hound, sight: a real dog, take 2 of the `$random` group (D107, the page's recommendation) | BigSoundBank #0916 "Barking dog" (a big dog at 2 m) by **Joseph Sardin**, https://bigsoundbank.com/barking-dog-s0916.html; cut, pitched, filtered, mixed and levelled to `DSSGTSIT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDSIT_dog2`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDSI3` | Reich hound, sight: a real dog, take 3 of the `$random` group (D107) | "Dog snarl, grunt, grumble" (dog-snarl.flac) by **qubodup**, OpenGameArt, https://opengameart.org/content/dog-snarl-grunt-grumble; BigSoundBank #0916 "Barking dog" (a big dog at 2 m) by **Joseph Sardin**, https://bigsoundbank.com/barking-dog-s0916.html; cut, pitched, filtered, mixed and levelled to `DSSGTSIT` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDSIT_dog3`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAT1` | Reich hound, attack: a real dog, take 1 of the `$random` group (D107, the page's recommendation) | "Dog snarl, grunt, grumble" (dog-snarl.flac) by **qubodup**, OpenGameArt, https://opengameart.org/content/dog-snarl-grunt-grumble; BigSoundBank #0112 "Barking dog inside" (a German shepherd) by **Joseph Sardin**, https://bigsoundbank.com/barking-dog-inside-s0112.html; cut, pitched, filtered, mixed and levelled to `DSSGTATK` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDATK_dog1`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAT2` | Reich hound, attack: a real dog, take 2 of the `$random` group (D107) | "Dog growls" (5.ogg) by congusbongus, OpenGameArt, https://opengameart.org/content/dog-growls, itself cut from "Dogs growling.wav" by juskiddink, Freesound #121565, https://freesound.org/people/juskiddink/sounds/121565/; `KEN-IMP` Kenney *Impact Sounds* impactPunch_heavy_002 (on disk since D36); cut, pitched, filtered, mixed and levelled to `DSSGTATK` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDATK_dog2`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | the growl: CC BY 3.0 (https://creativecommons.org/licenses/by/3.0/, the OpenGameArt page; the Freesound original is CC BY 4.0 today), modified as the Origin says, credit "congusbongus" credit "juskiddink" (the in-game credits, SD_CRED_SFX_6, and CREDITS.txt); the other layer: CC0 1.0, courtesy credit; the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDAT3` | Reich hound, attack: a real dog, take 3 of the `$random` group (D107) | BigSoundBank #0916 "Barking dog" (a big dog at 2 m) by **Joseph Sardin**, https://bigsoundbank.com/barking-dog-s0916.html; cut, pitched, filtered, mixed and levelled to `DSSGTATK` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDATK_dog3`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDPA1` | Reich hound, pain: a real dog, take 1 of the `$random` group (D107, the page's recommendation) | "Dog Sounds" (Dog.wav) by **pauliuw**, OpenGameArt, https://opengameart.org/content/dog-sounds; cut, pitched, filtered, mixed and levelled to `DSDMPAIN` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDPAI_dog1`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDPA2` | Reich hound, pain: a real dog, take 2 of the `$random` group (D107) | "Dog Sounds" (Dog.wav) by **pauliuw**, OpenGameArt, https://opengameart.org/content/dog-sounds; cut, pitched, filtered, mixed and levelled to `DSDMPAIN` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDPAI_dog2`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDPA3` | Reich hound, pain: a real dog, take 3 of the `$random` group (D107) | BigSoundBank #1546 "Dogs barking and crying 3" by **Joseph Sardin**, https://bigsoundbank.com/dogs-barking-and-crying-3-s1546.html; cut, pitched, filtered, mixed and levelled to `DSDMPAIN` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDPAI_dog3`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDDT1` | Reich hound, death: a real dog, take 1 of the `$random` group (D107) | "Dog Sounds" (Sad Dog.wav) by **pauliuw**, OpenGameArt, https://opengameart.org/content/dog-sounds; cut, pitched, filtered, mixed and levelled to `DSSGTDTH` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDDTH_dog1`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDDT2` | Reich hound, death: a real dog, take 2 of the `$random` group (D107, the page's recommendation) | "Dog Sounds" (Dog.wav) by **pauliuw**, OpenGameArt, https://opengameart.org/content/dog-sounds; "Dog Sounds" (Sad Dog.wav) by **pauliuw**, OpenGameArt, https://opengameart.org/content/dog-sounds; cut, pitched, filtered, mixed and levelled to `DSSGTDTH` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDDTH_dog2`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDHNDDT3` | Reich hound, death: a real dog, take 3 of the `$random` group (D107) | BigSoundBank #1546 "Dogs barking and crying 3" by **Joseph Sardin**, https://bigsoundbank.com/dogs-barking-and-crying-3-s1546.html; `KEN-IMP` Kenney *Impact Sounds* impactSoft_heavy_001 (on disk since D36); cut, pitched, filtered, mixed and levelled to `DSSGTDTH` by `work/audio/candidates/dog/make_dog_candidates.py` (candidate `SDHNDDTH_dog3`, `work/audio/sfx_sources/dog/SOURCES.md`: files, SHA-256), installed byte for byte by `master_enemy_sfx.py --dogs` | CC0 1.0 (https://creativecommons.org/publicdomain/zero/1.0/), courtesy credit (SD_CRED_SFX_4, SD_CRED_SFX_5); the cut and the mix: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDDGBACT` | Doughboy, idle | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDDGBSIT` | Doughboy, sight | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` scream_02, `OGA-CRE1` monster_03 | idem |
| `SDDGBMEL` | Doughboy, melee | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` eat_02, `KEN-IMP` impactMetal_heavy_001 | idem |
| `SDDGBMIS` | Doughboy, missile launch | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` spit_02 | idem |
| `SDDGBEXP` | Doughboy, missile impact | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE2` slime_07 | idem |
| `SDDGBPAI` | Doughboy, pain | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` hurt_05 | idem |
| `SDDGBDTH` | Doughboy, death | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPZRACT` | Panzermensch, idle | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` breath, `OGA-CRE2` breath_02, `KEN-IMP` impactPlate_light_001 | idem |
| `SDPZRSIT` | Panzermensch, sight | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE2` roar_05, `OGA-CRE1` roar_02, `KEN-IMP` impactPlate_heavy_001, `KEN-IMP` impactMetal_heavy_003 | idem |
| `SDPZRMEL` | Panzermensch, melee | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPunch_heavy_000, `KEN-IMP` impactPlate_heavy_003 | idem |
| `SDPZRMIS` | Panzermensch, missile launch | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPZREXP` | Panzermensch, missile impact | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPZRDTH` | Panzermensch, death | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE2` die_04, `OGA-CRE2` roar_04, `KEN-IMP` impactPlate_heavy_004, `KEN-IMP` impactMetal_heavy_001, `KEN-IMP` impactPunch_heavy_002, `KEN-IMP` impactPlate_heavy_002 | idem |
| `SDPZRSTP` | Panzermensch, footstep | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDGENACT` | the General, idle | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDGENMIS` | the General, missile launch | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactMetal_heavy_001 | idem |
| `SDGENEXP` | the General, missile impact | `gen_sfx.py` draft (seed 1977), D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPlate_heavy_000 | idem |
| `SDRRIAT1` | Reich rifleman, attack (take 1 of the `$random` group) | `gen_enemy_alts.py` SDRRIATK alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDRRIAT2` | Reich rifleman, attack (take 2 of the `$random` group) | `gen_enemy_alts.py` SDRRIATK alt2, D86, levelled by `gen_enemy_alts.py`; its peaks limited 0.5 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `KEN-IMP` impactMetal_light_001, `KEN-IMP` impactPunch_medium_000, `OGA-100` switch_02, `KEN-IMP` impactMetal_light_004 | idem |
| `SDRRIAT3` | Reich rifleman, attack (take 3 of the `$random` group) | `gen_enemy_alts.py` SDRRIATK alt3, D86, levelled by `gen_enemy_alts.py`; its peaks limited 0.3 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: none, synthesis only | idem |
| `SDLTRATK` | Legion trooper, attack | `gen_enemy_alts.py` SDLTRATK alt2, D86, levelled by `gen_enemy_alts.py`; its peaks limited 1.7 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `KEN-IMP` impactPlate_heavy_003 | idem |
| `SDSTOPA1` | Hybrid Stormtrooper, pain (take 1 of the `$random` group) | `gen_enemy_alts.py` SDSTOPAI alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` hurt_04 | idem |
| `SDSTOPA2` | Hybrid Stormtrooper, pain (take 2 of the `$random` group) | `gen_enemy_alts.py` SDSTOPAI alt2, D86, levelled by `gen_enemy_alts.py`; its peaks limited 0.7 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `OGA-CRE2` grunt_07 | idem |
| `SDSTOPA3` | Hybrid Stormtrooper, pain (take 3 of the `$random` group) | `gen_enemy_alts.py` SDSTOPAI alt3, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` monster_02 | idem |
| `SDSTODT1` | Hybrid Stormtrooper, death (take 1 of the `$random` group) | `gen_enemy_alts.py` SDSTODTH alt1, D86, levelled by `gen_enemy_alts.py`; its peaks limited 0.4 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `OGA-CRE2` die_01, `KEN-IMP` impactMetal_heavy_002 | idem |
| `SDSTODT2` | Hybrid Stormtrooper, death (take 2 of the `$random` group) | `gen_enemy_alts.py` SDSTODTH alt2, D86, levelled by `gen_enemy_alts.py`; its peaks limited 1.0 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `OGA-CRE1` roar_03 | idem |
| `SDSTODT3` | Hybrid Stormtrooper, death (take 3 of the `$random` group) | `gen_enemy_alts.py` SDSTODTH alt3, D86, levelled by `gen_enemy_alts.py`; its peaks limited 1.6 dB by `master_enemy_sfx.py`'s codec check; CC0 layers: `OGA-CRE2` monster_12, `KEN-IMP` impactPlate_medium_001, `KEN-IMP` impactPlate_light_004 | idem |
| `SDPZRPA1` | Panzermensch, pain (take 1 of the `$random` group) | `gen_enemy_alts.py` SDPZRPAI alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE2` grunt_06, `KEN-IMP` impactPlate_heavy_003 | idem |
| `SDPZRPA2` | Panzermensch, pain (take 2 of the `$random` group) | `gen_enemy_alts.py` SDPZRPAI alt2, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE1` troll_02 | idem |
| `SDPZRPA3` | Panzermensch, pain (take 3 of the `$random` group) | `gen_enemy_alts.py` SDPZRPAI alt3, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `OGA-CRE2` roar_06, `KEN-IMP` impactMetal_heavy_000 | idem |
| `SDRRIDB1` | Reich rifleman, bed under the death voice | `gen_sfx.py` draft (seed 1977) bed, D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactWood_light_002, `KEN-IMP` impactMetal_light_000, `KEN-IMP` impactTin_medium_001 | idem |
| `SDLTRAB1` | Legion trooper, bed under the idle voice | `gen_sfx.py` draft (seed 1977) bed, D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDLTRSB1` | Legion trooper, bed under the sight voice | `gen_sfx.py` draft (seed 1977) bed, D83, mastered by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDGENPB1` | the General, bed under the pain voice | `gen_sfx.py` draft (seed 1977) bed, D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPlate_medium_002 | idem |
| `SDGENDB1` | the General, bed under the death voice | `gen_sfx.py` draft (seed 1977) bed, D83, mastered by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPlate_heavy_002, `KEN-IMP` impactMetal_heavy_004 | idem |
| `SDRRIPB1` | Reich rifleman, bed under the pain voice (take 1 of the `$random` group) | `gen_enemy_alts.py` SDRRIPAI alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactWood_light_001, `KEN-IMP` impactTin_medium_003 | idem |
| `SDRRIPB2` | Reich rifleman, bed under the pain voice (take 2 of the `$random` group) | `gen_enemy_alts.py` SDRRIPAI alt2, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` footstep_carpet_002, `KEN-IMP` impactMetal_light_003 | idem |
| `SDRRIPB3` | Reich rifleman, bed under the pain voice (take 3 of the `$random` group) | `gen_enemy_alts.py` SDRRIPAI alt3, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` footstep_concrete_001, `KEN-IMP` impactGeneric_light_003, `KEN-IMP` impactMetal_light_004 | idem |
| `SDLTRPB1` | Legion trooper, bed under the pain voice (take 1 of the `$random` group) | `gen_enemy_alts.py` SDLTRPAI alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPunch_medium_003 | idem |
| `SDLTRPB2` | Legion trooper, bed under the pain voice (take 2 of the `$random` group) | `gen_enemy_alts.py` SDLTRPAI alt2, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDLTRPB3` | Legion trooper, bed under the pain voice (take 3 of the `$random` group) | `gen_enemy_alts.py` SDLTRPAI alt3, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPlate_light_000 | idem |
| `SDLTRDB1` | Legion trooper, bed under the death voice (take 1 of the `$random` group) | `gen_enemy_alts.py` SDLTRDTH alt1, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactPlate_medium_003, `KEN-IMP` impactGeneric_light_004, `KEN-IMP` impactSoft_heavy_002 | idem |
| `SDLTRDB2` | Legion trooper, bed under the death voice (take 2 of the `$random` group) | `gen_enemy_alts.py` SDLTRDTH alt2, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactSoft_heavy_002, `KEN-IMP` footstep_concrete_001 | idem |
| `SDLTRDB3` | Legion trooper, bed under the death voice (take 3 of the `$random` group) | `gen_enemy_alts.py` SDLTRDTH alt3, D86, levelled by `gen_enemy_alts.py`, installed as the CEO heard it by `master_enemy_sfx.py`; CC0 layers: `KEN-IMP` impactMetal_light_004, `KEN-IMP` impactMetal_light_001 | idem |
| `SDRRISI1` | Reich rifleman, sight: "Kontakt!" (voice Austin), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R06 t01 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDRRISI3` | Reich rifleman, sight: "Kontakt!" (voice Austin), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R06 t03 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDLTRAC1` | Legion trooper, idle radio chatter: "Sector four, clear." (voice Jordan), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L01 t01 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDLTRAC2` | Legion trooper, idle radio chatter: "Sector four, clear." (voice Jordan), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L01 t03 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDLTRAC3` | Legion trooper, idle radio chatter: "Copy. Holding position." (voice Jordan), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L02 t01 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDLTRAC4` | Legion trooper, idle radio chatter: "Copy. Holding position." (voice Jordan), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L02 t02 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDLTRAC5` | Legion trooper, idle radio chatter: "Copy. Holding position." (voice Jordan), a take of the `$random` group (D91) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L02 t03 (`work/audio/voice_takes/AI-LOG.csv`: tool, model, voice, text, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1) |
| `SDRRIAC1` | Reich rifleman, idle: "Stellung halten!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R01 t13, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRIAC2` | Reich rifleman, idle: "Augen auf!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R02 t11, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRIAC3` | Reich rifleman, idle: "Ruhe da hinten!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R03 t14, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRISI4` | Reich rifleman, sight: "Feind!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R04 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRISI5` | Reich rifleman, sight: "Feind!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R04 t13, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRISI6` | Reich rifleman, sight: "Da!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R05 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRIDTH` | Reich rifleman, death: "Sani…", its only take (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take R09 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Male Grunt/Yelling sounds", vocalist 3, by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDLTRAC6` | Legion trooper, idle radio chatter: "Command, say again?", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L03 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRSI1` | Legion trooper, sight: "Contact!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L04 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRSI2` | Legion trooper, sight: "Contact!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L04 t14, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRSI3` | Legion trooper, sight: "Hostile, front!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L05 t13, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRSI4` | Legion trooper, sight: "Got movement!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L06 t13, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRPA1` | Legion trooper, pain: "I'm hit!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L08 t14, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Male Grunt/Yelling sounds", vocalist 3, by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDLTRPA2` | Legion trooper, pain: "I'm hit!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take L08 t15, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Male Grunt/Yelling sounds", vocalist 3, by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDGENSIT` | the General, sight: "Engage!", its only take (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take G01 t12, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENSU1` | the General, the order: "Vorwärts!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take G02 t13, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`; its peak limited 0.6 dB by `master_enemy_sfx.py --voices`'s codec pass (Vorbis lifted it to -0.02 dBFS) | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENSU2` | the General, the order: "Vorwärts!", a take of the `$random` group (D96) | Chatterbox Multilingual (Resemble AI) via Chatterbox-TTS-Server 2.0.2, run locally 2026-10-20, take G02 t14, voice cloned from the reference (`work/audio/voice_takes/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `tools/audio/process_voice_takes.py`, installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent, checked 2026-10-20; `work/audio/voice_takes/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRIPA1` | Reich rifleman, pain: "Argh!", a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take R07 t6, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "angry", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRRIPA2` | Reich rifleman, pain: "Argh!", a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take R07 t2, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Male Grunt/Yelling sounds", vocalist 3, by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDLTRDT1` | Legion trooper, death: a cry, a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take L09 t1, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRDT2` | Legion trooper, death: a cry that fades, a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take L09 t2, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDLTRDT3` | Legion trooper, death: a cry, a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take L09 t4, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), its tail cut by `master_enemy_sfx.py --voices` (`VOICE_TAIL_CUT`): the raw take ends at 1.20 s, before a 0.08 s blip after the cry that the CEO heard ("se cuela algo al final"), and is rendered by the same chain | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Male Grunt/Yelling sounds", vocalist 3, by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDGENPA1` | the General, pain: "Argh!", a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take G03 t6, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENPA2` | the General, pain: "Hngh!", a take of the `$random` group (D110) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-21, take G03 t4, voice cloned from the reference (`work/audio/voice_takes/p2/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2/gen_p2.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENDT1` | the General, death: "Aaaaaaaaaaargh... aaaaah.", a take of the `$random` group (D118) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-22, take G04 t1, voice cloned from the reference (`work/audio/voice_takes/p2b/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2b/gen_p2b.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2b/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENDT2` | the General, death: "Neeeeeiiiin!", a take of the `$random` group (D118) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-22, take G04 t7, voice cloned from the reference (`work/audio/voice_takes/p2b/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2b/gen_p2b.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2b/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENDT3` | the General, death: "Urgh... aaaaaaaaah... ah.", a take of the `$random` group (D118) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-22, take G04 t8, voice cloned from the reference (`work/audio/voice_takes/p2b/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2b/gen_p2b.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2b/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (wounded.ogg and battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENDT4` | the General, death: "Nein! Aaaaaaaaaaah...", a take of the `$random` group (D118) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-22, take G04 t5, voice cloned from the reference (`work/audio/voice_takes/p2b/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2b/gen_p2b.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2b/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |
| `SDGENDT5` | the General, death: "Aaaargh... no...", a take of the `$random` group (D118) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU in the server's own Python (speech tokens capped at 300, special tokens dropped), 2026-10-22, take G04 t12, voice cloned from the reference (`work/audio/voice_takes/p2b/AI-LOG.csv`: tool, model, reference, text, seed, settings); processed and levelled by `work/audio/voice_takes/p2b/gen_p2b.py` (`process_voice_takes.process_wave`), installed byte for byte by `master_enemy_sfx.py --voices` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, which the CPU run uses, checked 2026-10-20; `work/audio/voice_takes/p2b/AI-LOG.csv`); the voice reference, not distributed: "Soldier Voice Acting" (battlecries.ogg) by kurt, OpenGameArt, CC-BY 3.0, https://opengameart.org/content/soldier-voice-acting; credit "kurt" (the in-game credits, SD_CRED_SFX_3, and CREDITS.txt) |

## World sounds: the player, doors, switches, pickups, lifts, teleporter (approved by the CEO 2026-10-23, D125)

The sounds that were Freedoom's until D125, from the candidates of
`tools/audio/gen_world_sfx.py` the CEO heard on
`work/audio/preview/world_sounds_listening.html`. His verdict, 56/56,
quoted as given:

> "OK (50): SDPLPAIN_w1, SDPLPAIN_w2, SDPLPAIN_w3, SDPLDETH_w1, SDPLDETH_w3, SDPLXDTH_w1, SDPLXDTH_w2, SDPLXDTH_w3, SDPLOOF_w2, SDPLOOF_w3, SDPLNOWY_w1, SDPLNOWY_w2, SDPLNOWY_w3, SDDOROPN_w1, SDDOROPN_w2, SDDOROPN_w3, SDDORCLS_w1, SDDORCLS_w2, SDDORCLS_w3, SDBDOPN_w1, SDBDOPN_w2, SDBDOPN_w3, SDBDCLS_w1, SDBDCLS_w2, SDBDCLS_w3, SDSWTCHN_w1, SDSWTCHN_w2, SDSWTCHN_w3, SDSWTCHX_w1, SDSWTCHX_w2, SDSWTCHX_w3, SDITEMUP_w1, SDITEMUP_w2, SDITEMUP_w3, SDGETPOW_w1, SDGETPOW_w2, SDGETPOW_w3, SDIZPKP_w1, SDIZPKP_w2, SDPSTART_w1, SDPSTART_w2, SDPSTART_w3, SDPSTOP_w1, SDPSTOP_w2, SDPSTOP_w3, SDPMOVE_w1, SDPMOVE_w2, SDPMOVE_w3, SDTELEPT_w1, SDTELEPT_w2 · NO (5): SDPLDETH_w2, SDPLJUMP_w1, SDPLJUMP_w2, SDIZPKP_w3, SDTELEPT_w3 · ? (1): SDPLOOF_w1 «El audio está bien pero no tiene el ruido, yo dejaría los 2 audios a la vez»"

(The last remark: "the audio is fine but it lacks the noise; I would keep both sounds at once.")

Installed by `tools/audio/master_world_sfx.py --install`: the 50 OKs byte
for byte as the page's OGGs, and SDPLOOF_w1's voice laid over SDPLOOF_w3's
impact as `SDSGOOF1`; files in `assets/sounds/world/<LUMP>.ogg`, packed as
`sounds/<LUMP>.ogg`, each sound a `$random` group in `src/lumps/SNDINFO`
(the install, levels and hashes: `docs/sound/WORLD-SOUNDS.md`). Not
installed: the five NO; the jump keeps Freedoom's `DSJUMP`.

**Material.** Synthesis of our own; recordings cut, re-pitched, filtered,
mixed and levelled by us: BigSoundBank's CC0 recordings (Joseph Sardin,
DenisChardonnet, Pablo Bergel; downloaded 2026-10-22 under D102/D107, files
and SHA-256 in `work/audio/sfx_sources/world/SOURCES.md`, not distributed),
two Kenney clips already here (`KEN-IMP`, D36), and the sergeant's voice:
HaelDB's "Male Grunt/Yelling sounds" (OpenGameArt, CC0 1.0; dual-listed
with OGA-BY 3.0, CC0 picked), the vocalists the enemies do not clone, used
as recordings and as the reference of three Chatterbox takes (`SDSGPAI2`,
`SDSGXDT2`, the voice of `SDSGOOF1`; each row names Chatterbox, which
`tools/release.py` reads). CC0 asks for nothing; the authors are named in
the rows by courtesy. **Two takes layer Freedoom-derived material**:
`SDSGXDT1` and `SDSGXDT2` carry our gib `SDRRIXDT`, which edits Freedoom's
`DSSLOP`, so they ship under Freedoom's licence for that layer, with its
credit, as the gibs do.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDSGPAI1` | the sergeant, pain, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLPAIN_w1 (a recorded voice, trimmed and levelled), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" yell12.wav, https://opengameart.org/content/male-gruntyelling-sounds | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDSGPAI2` | the sergeant, pain, take 2 of the `$random` group (D125) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU, 2026-10-22, take PLP_SDPLPAIN_ai_chatterbox_20261022_t01, voice cloned from a reference of ten clips of HaelDB's unnumbered vocalist (`work/audio/candidates/world/voice/AI-LOG.csv`: tool, model, reference, text, seed, settings; `voice/ref/REF.json`: the clips); processed and levelled by `gen_world_sfx.py` (candidate SDPLPAIN_w2); installed byte for byte by `master_world_sfx.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, checked 2026-10-20); the voice reference, not distributed: "Male Grunt/Yelling sounds" by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDSGPAI3` | the sergeant, pain, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLPAIN_w3 (a recorded voice, trimmed and levelled), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" 2yell9.wav, https://opengameart.org/content/male-gruntyelling-sounds | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDSGDET1` | the sergeant, death, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLDETH_w1 (a recorded voice, trimmed and levelled), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" yell2.wav, https://opengameart.org/content/male-gruntyelling-sounds | idem |
| `SDSGDET3` | the sergeant, death, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLDETH_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" yell2.wav, https://opengameart.org/content/male-gruntyelling-sounds; `KEN-IMP` footstep_concrete_000 | idem |
| `SDSGXDT1` | the sergeant, violent death, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLXDTH_w1 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" yell4.wav, https://opengameart.org/content/male-gruntyelling-sounds; our `SDRRIXDT` (D83), which edits Freedoom's `DSSLOP` (freedoom2.wad:DSSLOP) layered | Freedoom's `DSSLOP` (inside `SDRRIXDT`): modified BSD licence (BSD 3-clause), © the Contributors to the Freedoom project, credit "Freedoom"; the rest: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDSGXDT2` | the sergeant, violent death, take 2 of the `$random` group (D125) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU, 2026-10-22, take PLX_SDPLXDTH_ai_chatterbox_20261022_t03, voice cloned from a reference of ten clips of HaelDB's unnumbered vocalist (`work/audio/candidates/world/voice/AI-LOG.csv`: tool, model, reference, text, seed, settings; `voice/ref/REF.json`: the clips); processed and levelled by `gen_world_sfx.py` (candidate SDPLXDTH_w2); under it our `SDRRIXDT` (D83), which edits Freedoom's `DSSLOP` (freedoom2.wad:DSSLOP); installed byte for byte by `master_world_sfx.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, checked 2026-10-20); Freedoom's `DSSLOP` (inside `SDRRIXDT`): modified BSD licence (BSD 3-clause), © the Contributors to the Freedoom project, credit "Freedoom"; the voice reference, not distributed: "Male Grunt/Yelling sounds" by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDSGXDT3` | the sergeant, violent death, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLXDTH_w3 (a recorded voice, trimmed and levelled), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" yell4.wav, https://opengameart.org/content/male-gruntyelling-sounds | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDSGOOF1` | the sergeant, landing (oof): SDPLOOF_w1's voice over SDPLOOF_w3's impact, take 1 of the `$random` group (D125, the CEO's "?") | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the CPU, 2026-10-22, take PLO_SDPLOOF_ai_chatterbox_20261022_t03, voice cloned from a reference of ten clips of HaelDB's unnumbered vocalist (`work/audio/candidates/world/voice/AI-LOG.csv`: tool, model, reference, text, seed, settings; `voice/ref/REF.json`: the clips) (the voice of candidate SDPLOOF_w1); the impact of candidate SDPLOOF_w3 (CC0 layers: `KEN-IMP` footstep_concrete_000; `KEN-IMP` footstep_concrete_003); mixed and levelled to `DSOOF` by `master_world_sfx.py` (`render_layered`, the recipes of `gen_world_sfx.py`) | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (PerTh's watermarker is absent from the server's Python, checked 2026-10-20); the voice reference, not distributed: "Male Grunt/Yelling sounds" by HaelDB, OpenGameArt, CC0 1.0 (dual-listed with OGA-BY 3.0; CC0 picked), https://opengameart.org/content/male-gruntyelling-sounds; courtesy credit |
| `SDSGOOF2` | the sergeant, landing (oof), take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLOOF_w2 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: `KEN-IMP` footstep_concrete_000; `KEN-IMP` footstep_concrete_003 | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); its CC0 layers oblige nothing |
| `SDSGOOF3` | the sergeant, landing (oof), take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLOOF_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" 3grunt4.wav, https://opengameart.org/content/male-gruntyelling-sounds; `KEN-IMP` footstep_concrete_000; `KEN-IMP` footstep_concrete_003 | idem |
| `SDSGNOW1` | the sergeant, use that does nothing, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLNOWY_w1 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1540 "barn lock locking" by Joseph Sardin, https://bigsoundbank.com/barn-lock-locking-s1540.html | idem |
| `SDSGNOW2` | the sergeant, use that does nothing, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLNOWY_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDSGNOW3` | the sergeant, use that does nothing, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPLNOWY_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: HaelDB's "Male Grunt/Yelling sounds" 3grunt5.wav, https://opengameart.org/content/male-gruntyelling-sounds; BigSoundBank #1540 "barn lock locking" by Joseph Sardin, https://bigsoundbank.com/barn-lock-locking-s1540.html | idem |
| `SDDOROP1` | door, opening, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDOROPN_w1 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1539 "barn lock unlocking" by Joseph Sardin, https://bigsoundbank.com/barn-lock-unlocking-s1539.html; BigSoundBank #1490 "pneumatic brake released" by Joseph Sardin, https://bigsoundbank.com/pneumatic-brake-released-s1490.html; BigSoundBank #2355 "grinding metal barrier opening 1" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-opening-1-s2355.html | idem |
| `SDDOROP2` | door, opening, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDOROPN_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDDOROP3` | door, opening, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDOROPN_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1540 "barn lock locking" by Joseph Sardin, https://bigsoundbank.com/barn-lock-locking-s1540.html; BigSoundBank #0616 "creaking metallic door" by Joseph Sardin, https://bigsoundbank.com/creaking-metallic-door-s0616.html | idem |
| `SDDORCL1` | door, closing, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDORCLS_w1 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #2357 "grinding metal barrier opening 3" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-opening-3-s2357.html; BigSoundBank #2358 "grinding metal barrier closure 1" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-closure-1-s2358.html; BigSoundBank #1540 "barn lock locking" by Joseph Sardin, https://bigsoundbank.com/barn-lock-locking-s1540.html | idem |
| `SDDORCL2` | door, closing, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDORCLS_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDDORCL3` | door, closing, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDDORCLS_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #0616 "creaking metallic door" by Joseph Sardin, https://bigsoundbank.com/creaking-metallic-door-s0616.html; BigSoundBank #2360 "grinding metal barrier closure 3" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-closure-3-s2360.html | idem |
| `SDBDOPN1` | fast door, opening, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDOPN_w1 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #3442 "electric strike 1" by Joseph Sardin, https://bigsoundbank.com/electric-strike-1-s3442.html; BigSoundBank #1490 "pneumatic brake released" by Joseph Sardin, https://bigsoundbank.com/pneumatic-brake-released-s1490.html; BigSoundBank #2357 "grinding metal barrier opening 3" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-opening-3-s2357.html | idem |
| `SDBDOPN2` | fast door, opening, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDOPN_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDBDOPN3` | fast door, opening, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDOPN_w3 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1490 "pneumatic brake released" by Joseph Sardin, https://bigsoundbank.com/pneumatic-brake-released-s1490.html; BigSoundBank #2355 "grinding metal barrier opening 1" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-opening-1-s2355.html | idem |
| `SDBDCLS1` | fast door, closing, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDCLS_w1 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1490 "pneumatic brake released" by Joseph Sardin, https://bigsoundbank.com/pneumatic-brake-released-s1490.html; BigSoundBank #2359 "grinding metal barrier closure 2" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-closure-2-s2359.html | idem |
| `SDBDCLS2` | fast door, closing, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDCLS_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDBDCLS3` | fast door, closing, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDBDCLS_w3 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1490 "pneumatic brake released" by Joseph Sardin, https://bigsoundbank.com/pneumatic-brake-released-s1490.html; BigSoundBank #2360 "grinding metal barrier closure 3" by Joseph Sardin, https://bigsoundbank.com/grinding-metal-barrier-closure-3-s2360.html | idem |
| `SDSWTCN1` | switch, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHN_w1 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #3062 "industrial switch 2" by Joseph Sardin, https://bigsoundbank.com/industrial-switch-2-s3062.html | idem |
| `SDSWTCN2` | switch, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHN_w2 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1092 "electric circuit breaker" by Joseph Sardin, https://bigsoundbank.com/electric-circuit-breaker-s1092.html | idem |
| `SDSWTCN3` | switch, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHN_w3 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDSWTCX1` | exit switch, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHX_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDSWTCX2` | exit switch, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHX_w2 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #3061 "industrial switch 1" by Joseph Sardin, https://bigsoundbank.com/industrial-switch-1-s3061.html; BigSoundBank #0134 "electric shock" by Joseph Sardin, https://bigsoundbank.com/electric-shock-s0134.html | idem |
| `SDSWTCX3` | exit switch, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDSWTCHX_w3 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #3063 "industrial switch 3" by Joseph Sardin, https://bigsoundbank.com/industrial-switch-3-s3063.html; BigSoundBank #1092 "electric circuit breaker" by Joseph Sardin, https://bigsoundbank.com/electric-circuit-breaker-s1092.html | idem |
| `SDITEMU1` | item and key pickup, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDITEMUP_w1 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1367 "bullet case 7 62mm on concrete 1" by Joseph Sardin, https://bigsoundbank.com/bullet-case-7-62mm-on-concrete-1-s1367.html | idem |
| `SDITEMU2` | item and key pickup, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDITEMUP_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDITEMU3` | item and key pickup, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDITEMUP_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1988 "gun loading 1" by Joseph Sardin, https://bigsoundbank.com/gun-loading-1-s1988.html | idem |
| `SDGETPO1` | power-up pickup, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDGETPOW_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDGETPO2` | power-up pickup, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDGETPOW_w2 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDGETPO3` | power-up pickup, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDGETPOW_w3 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDIZPKP1` | IZh-58 pickup, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDIZPKP_w1 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1984 "pistol cocking 1" by Joseph Sardin, https://bigsoundbank.com/pistol-cocking-1-s1984.html | idem |
| `SDIZPKP2` | IZh-58 pickup, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDIZPKP_w2 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1988 "gun loading 1" by Joseph Sardin, https://bigsoundbank.com/gun-loading-1-s1988.html; BigSoundBank #1984 "pistol cocking 1" by Joseph Sardin, https://bigsoundbank.com/pistol-cocking-1-s1984.html; `KEN-IMP` impactMetal_light_002 | idem |
| `SDPSTAR1` | lift, start, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTART_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPSTAR2` | lift, start, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTART_w2 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1711 "elevator 3 floors" by Joseph Sardin, https://bigsoundbank.com/elevator-3-floors-s1711.html | idem |
| `SDPSTAR3` | lift, start, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTART_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #0708 "little electric winch" by Joseph Sardin, https://bigsoundbank.com/little-electric-winch-s0708.html; BigSoundBank #0359 "heavy chain" by DenisChardonnet, https://bigsoundbank.com/heavy-chain-s0359.html | idem |
| `SDPSTOP1` | lift, stop, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTOP_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPSTOP2` | lift, stop, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTOP_w2 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1711 "elevator 3 floors" by Joseph Sardin, https://bigsoundbank.com/elevator-3-floors-s1711.html | idem |
| `SDPSTOP3` | lift, stop, take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPSTOP_w3 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #3590 "anvil 2" by Pablo Bergel, https://bigsoundbank.com/anvil-2-s3590.html; BigSoundBank #0359 "heavy chain" by DenisChardonnet, https://bigsoundbank.com/heavy-chain-s0359.html | idem |
| `SDPMOVE1` | moving floor or ceiling (loop), take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPMOVE_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDPMOVE2` | moving floor or ceiling (loop), take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPMOVE_w2 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #0708 "little electric winch" by Joseph Sardin, https://bigsoundbank.com/little-electric-winch-s0708.html | idem |
| `SDPMOVE3` | moving floor or ceiling (loop), take 3 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDPMOVE_w3 (recordings cut, re-pitched and filtered), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #1133 "manual chain hoist mounted" by Joseph Sardin, https://bigsoundbank.com/manual-chain-hoist-mounted-s1133.html | idem |
| `SDTELEP1` | teleporter, take 1 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDTELEPT_w1 (synthesis), installed byte for byte by `master_world_sfx.py`; CC0 layers: none, synthesis only | idem |
| `SDTELEP2` | teleporter, take 2 of the `$random` group (D125) | `gen_world_sfx.py` candidate SDTELEPT_w2 (recordings and synthesis, mixed), installed byte for byte by `master_world_sfx.py`; CC0 layers: BigSoundBank #0134 "electric shock" by Joseph Sardin, https://bigsoundbank.com/electric-shock-s0134.html; BigSoundBank #0952 "short welds" by Joseph Sardin, https://bigsoundbank.com/short-welds-s0952.html | idem |

## Propaganda radio (V3 B5, approved by the CEO 2026-10-23, D124; installed 2026-10-24)

CEO verdict (D124), on `work/audio/preview/radio_listening.html`: 18 of 51
judged, all OK, then «me ha encantado el resultado, me fío para dar OK a TODO
de radio» ("I loved the result; I trust it enough to OK ALL of the
radio"). Every take of SDRAD01-16 and the three jingles may be used; the
female voice is Chatterbox's preset «Elena» (accepted with the rest); no
subtitles. **One take per line ships**, the best by the round's measurements
(`work/audio/candidates/radio/METRICS.json`, rank 1; never RAD07 t03, which
runs 6.04 s for 3.7 s), copied byte for byte by `tools/audio/install_radio.py`
into `assets/sounds/radio/` and packed as `sounds/<LUMP>.ogg`; `src/lumps/SNDINFO`
maps `sd/radio/*` to them (MOD-SPEC §6.2, §6.14).

**Two announcers.** The male lines are Chatterbox Multilingual cloned from
Thorsten Müller's **neutral** read speech (Thorsten-Voice emotional v02,
CC0 1.0: the D96 archive already on disk, its `neutral/` folder only; the
reference is not distributed), named by courtesy. The female lines use
Chatterbox-TTS-Server's predefined voice «Elena», whose origin its
distributor does not document: the D87 route (risk R1), extended to a
female preset by D124. Each row names Chatterbox, which `tools/release.py`
reads to say voice lines ship (D93). The jingles, the time signal's pips
and the bed are our own synthesis.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDRAD01` | propaganda radio, line 1 (the male announcer): war report: «Передаём сводку с фронта…» (the report from the front) (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD01 t01, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD02` | propaganda radio, line 2 (the male announcer): war report: the Zhiguli dam (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD02 t02, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD03` | propaganda radio, line 3 (the female announcer): civil defence: the air-raid alert (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD03 t02, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD04` | propaganda radio, line 4 (the female announcer): civil defence: do not approach fallen objects (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD04 t03, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD05` | propaganda radio, line 5 (the male announcer): slogan: «Враг силён, но народ сильнее…» (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD05 t01, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD06` | propaganda radio, line 6 (the female announcer): slogan: the five-year plan (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD06 t03, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD07` | propaganda radio, line 7 (the male announcer): slogan, the lore's line: «Захватчики воюют за прибыль. Мы воюем за всех.» (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD07 t01, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD08` | propaganda radio, line 8 (the female announcer): civil defence, ironic: tap water (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD08 t02, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD09` | propaganda radio, line 9 (the male announcer): news, ironic: the parade is not cancelled (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD09 t02, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD10` | propaganda radio, line 10 (the female announcer): weather, ironic: foreign objects falling from the sky (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD10 t03, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD11` | propaganda radio, line 11 (the male announcer): war report: Zarya-7 holds (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD11 t02, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD12` | propaganda radio, line 12 (the female announcer): civil defence, ironic: the creature in a helmet (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD12 t01, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD13` | propaganda radio, line 13 (the male announcer): slogan: every factory a fortress (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD13 t02, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD14` | propaganda radio, line 14 (the female announcer): appeal: blood donors (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD14 t03, the server's predefined voice «Elena» (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, voice, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the predefined voice's origin is not documented by Chatterbox-TTS-Server (D87, risk R1; the female preset accepted by D124) |
| `SDRAD15` | propaganda radio, line 15 (the male announcer): news: Tankograd's monthly plan in one night (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD15 t01, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRAD16` | propaganda radio, line 16 (the male announcer): time signal: six 1 kHz pips, then «Московское время — двадцать часов…» (D124) | Chatterbox Multilingual (Resemble AI), the library of Chatterbox-TTS-Server 2.0.2 run locally on the GPU, 2026-10-23, take RAD16 t02, voice cloned from the reference (`work/audio/candidates/radio/AI-LOG.csv`: tool, model, reference, text, seed, settings); the radio chain (band 300-3400 Hz, valve saturation, hum, crackle, tune-in) by `gen_radio.py`, the take METRICS.json's rank 1; installed byte for byte by `tools/audio/install_radio.py`; the pips before it are our synthesis (`gen_radio.py` pips, a technical signal, no author), rendered with the take as the round's `RAD16_pips_demo` | the processing: Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15); the take: Chatterbox output, model under MIT (read 2026-10-14, P2 study), not watermarked (the server's PerTh watermarker is absent; `AI-LOG.csv`); the voice reference, not distributed: Thorsten-Voice Dataset 2021.06 emotional v02, style "neutral", Thorsten Müller (voice), Dominik Kreutz (audio), CC0 1.0, https://zenodo.org/records/5525023; courtesy credit |
| `SDRADJ1` | propaganda radio, station jingle J1: bells, five notes in D major, rising (D124) | our synthesis, `gen_radio.py` (FM bells, an original motif: not Radio Moscow's real interval signal, a protected song), through the same radio chain; installed byte for byte by `tools/audio/install_radio.py` | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDRADJ2` | propaganda radio, station jingle J2: bells, four notes in D minor, solemn (D124) | our synthesis, `gen_radio.py` (FM bells, an original motif: not Radio Moscow's real interval signal, a protected song), through the same radio chain; installed byte for byte by `tools/audio/install_radio.py` | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDRADJ3` | propaganda radio, station jingle J3: bells, three notes in fifths and an octave (short) (D124) | our synthesis, `gen_radio.py` (FM bells, an original motif: not Radio Moscow's real interval signal, a protected song), through the same radio chain; installed byte for byte by `tools/audio/install_radio.py` | Soviet Doom project (sound-designer), CC BY-NC-SA 4.0 (D15) |
| `SDRADBED` | propaganda radio, the valve set's bed: hum, hiss, crackle, a 6 s seamless loop | procedural, rendered by `tools/audio/install_radio.py` (seed 21201; the set `gen_radio.py` lays under every take, heard alone); no source | idem |


## The propaganda loudspeaker (V3 B5, sprite; approved by the CEO 2026-10-24)

Sheet `docs/art/previews/2026-10-24_V3_loudspeaker.png`, both options (D132,
"Ambos! A y B", both A and B): A (grey) as `SDLS`, B (olive) as `SDLO`.
Files in `assets/sprites/loudspeaker/`, copied byte for byte from
`work/art/loudspeaker/A/` and, renamed `SDLS` to `SDLO`, from
`work/art/loudspeaker/B/` (rendered on the Windows PC on 2026-10-24 by
`tools/art/gen_loudspeaker.py`, seed 21201), so each PNG keeps its `grAb`.
RGBA with hard alpha, inside palette v1.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDLSA0` | `SD_Loudspeaker` (21201), silent: a street loudspeaker pole with two horns and a junction box with a red star | (a) `tools/art/gen_loudspeaker.py`, option A, frame A | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDLSB0` | the same, speaking: the pilot lamp lit, the horns shaken | (a) `tools/art/gen_loudspeaker.py`, option A, frame B | idem |
| `SDLOA0` | `SD_Loudspeaker` with arg3 flag 8, silent: the same loudspeaker in the army's olive | (a) `tools/art/gen_loudspeaker.py`, option B, frame A (`B/SDLSA0.png`, renamed) | idem |
| `SDLOB0` | the same, speaking | (a) `tools/art/gen_loudspeaker.py`, option B, frame B (`B/SDLSB0.png`, renamed) | idem |

Drawn from code (rig_core's solids, as the floor lamp `COLU` and the drum
`BAR1`): no photograph, no typeface, no pack, no AI image. The mod's own
sprites and textures appear on the review sheet beside it, for scale, and
never enter these lumps.

## Weapon pickups (F4, approved by the CEO 2026-10-14, D48)

CEO verdict (D48): the ice axe with pickup **C**, the PPSh-41, and "Resto del
arsenal: OK" for the TT-33, IZh-58, RPG-7 and ROKS-3. Only the **world
pickups** are installed: after playing MAP01 with the draft overlay the same
day the CEO found hand E deformed, so the first-person (held) and muzzle-flash
frames, which show the hand, stay drafts in `work/` until the hands are
redrawn (the TT-33's were, in Freedoom's hands: next section, N17). Files in `assets/sprites/<weapon>/`, copied byte for byte from
`work/art/weapons/<weapon>/` (rendered on the Windows PC on 2026-10-13), so
each PNG keeps its `grAb` offsets. RGBA with hard alpha, every opaque pixel a
`docs/art/palette.json` colour (`tests/test_gen_weapon.py`). Not installed:
the held and flash frames, the hand Katyusha (to redo, D48), the `_proposed`
frames, and the ice axe's pickup options A and B. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDAPA0` | ice axe on the floor, option C "upright, as in a rack" | (a) `tools/art/gen_weapon.py`, `build_axe`, `RECOMMENDED_PICKUP` C | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `SDTPA0` | TT-33 on the floor | (a) idem, `build_weapon("tt33")` | idem |
| `SDIPA0` | IZh-58 on the floor | (a) idem, `build_weapon("izh")` | idem |
| `SDPQA0` | PPSh-41 on the floor | (a) idem, `build_ppsh` | idem |
| `SDRPA0` | RPG-7 on the floor | (a) idem, `build_weapon("rpg7")` | idem |
| `SDKPA0` | ROKS-3 on the floor | (a) idem, `build_weapon("roks3")` | idem |

Drawn from code: tapered capsules, ellipsoids and extruded plates shaded in
`palette.json` ramps, reduced to 1x by majority vote (the generator's
docstring). No photograph, no typeface. Freedoom's own weapon sprites appear
only beside ours on the review sheets, for comparison, and never enter a
sprite (`freedoom_sprite()` in the generator).

## Weapon frames: the TT-33 in hand (F4 D61/D63; redone with Gemini, D111, 2026-10-23)

CEO verdict on the redo: "Ok T33" (D123, 2026-10-23, on
`docs/art/previews/2026-10-23_P4_tt33-gemini.html`).
D111 ("rehaz los sprites de la pistola también porque ahora no queda en
tanta consonancia con el resto de armas", "redo the pistol sprites too,
because now it does not match the other weapons so well") retires the D61/D63 set (our
TT-33 model in Freedoom's recoloured pistol hands): no Freedoom pixel is
left in the TT-33. The new frames come from the project lead's Gemini pair
(ready, firing; bare hand on magenta), processed by
`tools/art/gemini_frames.py tt33` with the arsenal's constants (palette v2,
x1.6 CHGGA0 above the bar, the D79 kick), the muzzle on the crosshair.
Files in `assets/sprites/tt33/`, beside the pickup `SDTPA0`, copied byte
for byte from `work/art/weapons/hand_G/tt33/`, so each PNG keeps its `grAb`
offsets. RGBA with hard alpha, all four in palette v2. The source images
stay in `work/art/reference/` (gitignored, D77). Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDTTA0` | TT-33 held, frame A (ready; also raise and lower) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79) |
| `SDTTB0` | TT-33 held, frame B (the shot, kicked up and right) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDTTC0` | TT-33 held, frame C (settling, half the kick) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out, half kicked), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDTFA0` | TT-33 muzzle flash, frame A (over the muzzle of B) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |

## Weapon frames: the PPSh-41 in hand (F4, D79, 2026-10-20)

CEO verdict (D79, "Haz la 1"): the Gemini-frames method is adopted after the
PPSh-41 test seen in engine through the draft overlay, and Google Gemini is
credited next to Fooocus / SDXL (`SD_CRED_SRC_4`-`_6`, Options -> Soviet
Doom -> Credits; the release's AI paragraph, `tools/release.py`
`AI_DISCLOSURE`). The CEO generated the two source images (ready, firing)
with Google Gemini; they stay in `work/art/reference/` and are never
distributed (D77). `tools/art/gemini_frames.py ppsh` processes them into
pixel art (letterbox crop, magenta key, art-grid downsample, palette v2,
flash split, Doom size and pixel aspect, the arms run on and curve out of
view, a 2 px right / 3 px up kick on the firing frame) into
`work/art/weapons/hand_G/ppsh/`; the three lumps ship from
`assets/sprites/ppsh/`, beside the pickup `SDPQA0`, copied byte for byte,
so each PNG keeps its `grAb` offsets. RGBA with hard alpha; `SDPP` A-B in
palette v2, `SDPFA0` inside v1. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDPPA0` | PPSh-41 held, frame A (ready; also raise, lower and the first round) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79) |
| `SDPPB0` | PPSh-41 held, frame B (the second round, kicked up and right) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDPFA0` | PPSh-41 muzzle flash, frame A (over the muzzle of B) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |

## Weapon frames and pickup: the AKM (P4, 2026-10-24)

CEO verdict (D128, 2026-10-24) on
`docs/art/previews/2026-10-24_P4_akm-gemini.html`: "OK AKM".
The AKM (D112) wore the PPSh-41's frames since D116; these four lumps are
its own. The held and flash frames come from ONE image the project lead
generated with Google Gemini (the ready image; bare hands on magenta, asked
with the PPSh-41's image as the composition reference), processed by
`tools/art/gemini_frames.py akm` with the arsenal's constants (palette v2
without `flag_red`, x1.6 CHGGA0 above the bar, the D79 kick). Gemini's
firing image failed and was not asked again: the firing frame is the ready
frame kicked, and the muzzle flash is the PPSh-41's (cut from the PPSh's
Gemini pair, made whole and grafted at the AKM's muzzle). The floor pickup
is drawn from code on the weapon pickups' rig, `tools/art/gen_akm_pickup.py`
(no photograph, no typeface). Files in `assets/sprites/akm/`, copied byte
for byte from `work/art/weapons/hand_G/akm/`, so each PNG keeps its `grAb`
offsets. RGBA with hard alpha, all four in palette v2. The source images
stay in `work/art/reference/` (gitignored, D77). Engine names: MOD-SPEC §6.12.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDAKA0` | AKM held, frame A (ready; also raise, lower and between rounds) | (a) derived from an image generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source image is not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79) |
| `SDAKB0` | AKM held, frame B (the round, kicked up and right) | (a) derived from an image generated by the project lead with Google Gemini (the ready image), moved by the pipeline's kick by `tools/art/gemini_frames.py`; the source image is not distributed | idem |
| `SDAFA0` | AKM muzzle flash, frame A (over the muzzle of B) | (a) derived from images generated by the project lead with Google Gemini (the PPSh-41's firing image's flash, as `SDPFA0`), grafted at the AKM's muzzle by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDAQA0` | AKM on the floor | (a) `tools/art/gen_akm_pickup.py`, on `tools/art/gen_weapon.py`'s rig | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |

## Weapon frames: the IZh-58, RPG-7, ROKS-3, hand Katyusha and ice axe in hand (F4, D84 and D88, 2026-10-20)

CEO verdict (D84): the four approved after the CEO saw them in engine
through the draft overlay
(`docs/art/previews/2026-10-20_1037_F4_five-weapons-gemini-in-engine.png`);
the ice axe, the fifth, followed once its swing was redone (D88, "Piolet
aprobado", `docs/art/previews/2026-10-20_1112_F4_ice-axe-swing-ABCD.png`:
the wind-up, strike and follow-through rotate the ready frame as one rigid
piece). The method and the
credit are D79's (above, "the PPSh-41 in hand"): the CEO generated the
source images with Google Gemini (ready and firing for each gun, the IZh-58
also reloading; the ice axe's ready image only); they stay in `work/art/reference/` and are never
distributed (D77). `tools/art/gemini_frames.py <weapon>` processes them
into pixel art (letterbox crop, magenta key, art-grid downsample, palette
v2, flash split, Doom size and pixel aspect, the arms leaving the view with
no cut edge, the firing kick, the fading flashes shrunk) into
`work/art/weapons/hand_G/<weapon>/`; the twenty-three lumps ship from
`assets/sprites/izh/`, `rpg7/`, `roks3/`, `katyusha/` and `ice_axe/`, beside each
weapon's pickup, copied byte for byte (a fresh build reproduces them), so
each PNG keeps its `grAb` offsets. RGBA with hard alpha, palette v2.
Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDIZA0` | IZh-58 held, frame A (ready; also the first and last frames of a shot and the reload's last) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79) |
| `SDIZB0` | IZh-58 held, frame B (the shot's recoil, kicked up and right; the reload closing) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDIZC0` | IZh-58 held, frame C (settling, half the kick; the reload) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDIZD0` | IZh-58 held, frame D (broken open for the reload) | (a) derived from images generated by the project lead with Google Gemini (the reloading image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDIFA0` | IZh-58 muzzle flash, frame A (over the muzzles of A) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDIFB0` | IZh-58 muzzle flash, frame B (the flash fading) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash, shrunk), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRLA0` | RPG-7 held, frame A (ready) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRLB0` | RPG-7 held, frame B (firing and reloading, kicked) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRFA0` | RPG-7 launch flash, frame A (over the muzzle of B) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRFB0` | RPG-7 launch flash, frame B (fading) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash, shrunk), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRFC0` | RPG-7 launch flash, frame C (fading) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash, shrunk), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRFD0` | RPG-7 launch flash, frame D (fading) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash, shrunk), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRKA0` | ROKS-3 held, frame A (ready and firing) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDRKB0` | ROKS-3 held, frame B (the trigger let go, in A's pose) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flame cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDKFA0` | ROKS-3 flame at the nozzle, frame A (over A) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flame), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDHKA0` | hand Katyusha held, frame A (ready; the wind-up) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDHKB0` | hand Katyusha held, frame B (the salvo and the reload, kicked) | (a) derived from images generated by the project lead with Google Gemini (the firing image, its flash cut out), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDHFA0` | hand Katyusha salvo flash, frame A (over the rails of B) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDHFB0` | hand Katyusha salvo flash, frame B (the smoke fading) | (a) derived from images generated by the project lead with Google Gemini (the firing image's flash, shrunk), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDAXA0` | ice axe held, frame A (ready) | (a) derived from images generated by the project lead with Google Gemini (the ready image), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDAXB0` | ice axe held, frame B (the wind-up: A rotated back about the elbow) | (a) derived from images generated by the project lead with Google Gemini (the ready image, rotated), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDAXC0` | ice axe held, frame C (the strike: A rotated forward) | (a) derived from images generated by the project lead with Google Gemini (the ready image, rotated), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |
| `SDAXD0` | ice axe held, frame D (the follow-through: A rotated further down) | (a) derived from images generated by the project lead with Google Gemini (the ready image, rotated), processed into pixel art by `tools/art/gemini_frames.py`; the source images are not distributed | idem |

## Pickups: ammunition, the blue pass and the radio (approved by the CEO 2026-10-14, D63)

CEO choice (D63), one option per object of the pickups sweep (T8, T23 and
the sprite of T25). Files in `assets/sprites/pickups/`, copied byte for byte
from `work/art/pickups/<object>/<option>/` (rendered on the Windows PC on
2026-10-14), so each PNG keeps its `grAb` offsets. RGBA with hard alpha;
palette v1 for all but the pass, which uses palette v2's cobalt (D45). Not
installed: the options not chosen, the review sheets and `metrics.json`.
Engine names: MOD-SPEC §6.3, "The pickups, installed by D63".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDCLA0` | 7,62×25 rounds, small: a torn paper packet (option B) | (a) `tools/art/gen_pickups.py`, object `clip`, option B | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDCBA0` | 7,62×25 rounds, box: an opened zinc (option B) | (a) idem, `clipbox`, option B | idem |
| `SDSLA0` | 12-gauge shells, small: four lying (option A) | (a) idem, `shell`, option A | idem |
| `SDSBA0` | 12-gauge shells, box: open, twenty shells (option B) | (a) idem, `shellbox`, option B | idem |
| `SDRAA0` | one PG-7V round standing on its tail (option A) | (a) idem, `rocket`, option A | idem |
| `SDRBA0` | PG-7V rounds, an open crate with two (option A) | (a) idem, `rocketbox`, option A | idem |
| `SDFUA0` | fuel, small: a 10-litre jerrycan (option A) | (a) idem, `fuel`, option A | idem |
| `SDFBA0` | fuel, large: two ROKS-3 tanks in their back frame (option B) | (a) idem, `fuelpack`, option B | idem |
| `SDKBA0` | the blue pass, a laminated card (option B) | (a) idem, `pass`, option B, frame A | idem |
| `SDKBB0` | the blue pass, its blink frame (option B) | (a) idem, `pass`, option B, frame B | idem |
| `SDRDA0` | the radio, an Okean-209 on a tabouret (option B) | (a) idem, `radio`, option B | idem |

Drawn from code on gen_weapon's rig: boxes, tins, cylinders and cards shaded
in `palette.json` ramps, reduced to 1x by majority vote (the generator's
docstring). No photograph, no typeface, no text. Freedoom's pickups appear
only beside ours on the review sheet, for comparison, and never enter a
sprite.

## Pickups: the campaign's health, armour, map, backpack and passes (approved by the CEO 2026-10-20, D80)

CEO choice (D80), one option per object of the campaign pickups sweep
(backlog M2a, audit B3 and B5): the recommended option except the green
armour (C), the heavy armour (C) and the backpack (B); the hand Katyusha's
floor pickup at its drawn size (A). Files in `assets/sprites/pickups/`,
copied byte for byte from `work/art/items/<item>/<option>/` (rendered on the
Windows PC on 2026-10-20 by `tools/art/gen_items.py --install`), so each PNG
keeps its `grAb` offsets. RGBA with hard alpha, palette v1. The two medical
items carry the first-aid sign (a white cross on a green field, ISO 7010
E003), not the red-cross emblem (D80). The HUD pictures are the engine's
names: the key icons in `assets/graphics/hud/` (indexed, palette v2 for
`STKEYS0`, v1 colours for the other two). Not installed: the options not chosen, the review sheets and
`metrics.json`. Engine names: MOD-SPEC §6.3, "The campaign pickups,
installed by D80".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDBNA0` | stimpack: a field dressing packet (ИПП) with the first-aid sign (option A) | (a) `tools/art/gen_items.py`, item `stim`, option A | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDMDA0` | medikit: an enamelled first-aid box with the first-aid sign (option A) | (a) idem, `medikit`, option A | idem |
| `SDHBA0`, `SDHBB0`, `SDHBC0`, `SDHBD0` | health bonus: a bottle of zelyonka, frames A-D (the glint climbs) (option B) | (a) idem, `hbonus`, option B | idem |
| `SDABA0`, `SDABB0`, `SDABC0`, `SDABD0` | armour bonus: an SSh-68 steel helmet, frames A-D (option A) | (a) idem, `abonus`, option A | idem |
| `SDAGA0`, `SDAGB0` | green armour: a flak vest with an SSh-68 at its foot; B is the bright frame (option C) | (a) idem, `garmor`, option C | idem |
| `SDAHA0`, `SDAHB0` | blue armour: a bare-steel SN-42 breastplate and helmet; B is the bright frame (option C) | (a) idem, `barmor`, option C | idem |
| `SDMPA0`, `SDMPB0`, `SDMPC0`, `SDMPD0` | area map: an officer's map case (планшет), frames A-D (option A) | (a) idem, `allmap`, option A | idem |
| `SDBPA0` | backpack: an RD-54 paratrooper's pack (option B) | (a) idem, `backpack`, option B | idem |
| `SDKYA0`, `SDKYB0` | the yellow pass, the blue pass's card in yellow; B is the blink (option A) | (a) idem, `ykey`, option A | idem |
| `SDKKA0`, `SDKKB0` | the red pass, the blue pass's card in red with a gold stamp; B is the blink (option A) | (a) idem, `rkey`, option A | idem |
| `SDHPA0` | the hand Katyusha on the floor, the D51 draft (option A); installed on 2026-10-20 with `SD_HandKatyusha`'s `Spawn` line (D84's install; MOD-SPEC §6.3, "The Katyusha's pickup") | (a) idem, `katyusha`, option A (`gen_weapon.render_katyusha_pickup`) | idem |
| `STKEYS0`, `STKEYS1`, `STKEYS2` | status bar key icons, 7×5: the blue, yellow and red passes | (a) idem, `key_icon` (`work/art/items/hud/`) | idem |

Drawn from code on gen_weapon's rig, as the D63 pickups: boxes, domes,
cylinders and cards shaded in `palette.json` ramps, reduced to 1x by
majority vote. No photograph, no typeface, no text. Freedoom's pickups
appear only beside ours on the review sheet, for comparison, and never
enter a sprite.

## Enemy sprites: the Liberty Legion trooper (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105 and D109)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`). It replaces, name
for name, the set drawn on the 3D rig that the CEO approved on 2026-10-14
(cell C, D48 and D54); that set is history now, its generator
`tools/art/gen_legion.py` kept, marked historical, and its renders stay in
`work/art/enemies/legion/full_C/` (not shipped). Files in
`assets/sprites/legion/`, copied byte for byte from
`work/art/enemies_gemini/legion/` (built on the Windows PC on 2026-10-22 by
`python tools/art/gemini_enemy.py all`, rebuilt for the install: identical),
so each PNG keeps its `grAb` offsets. 70 lumps: frames A-G in eight separate
rotations, H-U in rotation 0; rotations 6-8 are 4-2 mirrored and written as
separate lumps (the flag patch changes shoulder in the mirrored views, ~3 ×
2 px in game, accepted as the shotgun's hand is). RGBA with hard alpha,
palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_legion_*.png`) were generated by the
CEO's own Google Gemini account from the project's previous sprites; they
are gitignored and never distributed (D77). Frames Gemini did not draw are
derived by the tool and listed in `derived` of its `metrics.json`. Not
installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDLTA1`, `SDLTA2`, `SDLTA3`, `SDLTA4`, `SDLTA5`, `SDLTA6`, `SDLTA7`, `SDLTA8` | walk, frame A (Gemini's first stride), rotations 1-8 | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_legion_*.png`), processed by `tools/art/gemini_enemy.py legion`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDLTB1`, `SDLTB2`, `SDLTB3`, `SDLTB4`, `SDLTB5`, `SDLTB6`, `SDLTB7`, `SDLTB8` | walk, frame B (the standing view) | (a) idem | idem |
| `SDLTC1`, `SDLTC2`, `SDLTC3`, `SDLTC4`, `SDLTC5`, `SDLTC6`, `SDLTC7`, `SDLTC8` | walk, frame C (Gemini's second stride) | (a) idem | idem |
| `SDLTD1`, `SDLTD2`, `SDLTD3`, `SDLTD4`, `SDLTD5`, `SDLTD6`, `SDLTD7`, `SDLTD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDLTE1`, `SDLTE2`, `SDLTE3`, `SDLTE4`, `SDLTE5`, `SDLTE6`, `SDLTE7`, `SDLTE8` | aim, frame E | (a) idem | idem |
| `SDLTF1`, `SDLTF2`, `SDLTF3`, `SDLTF4`, `SDLTF5`, `SDLTF6`, `SDLTF7`, `SDLTF8` | fire, frame F (the muzzle flash as Gemini drew it) | (a) idem | idem |
| `SDLTG1`, `SDLTG2`, `SDLTG3`, `SDLTG4`, `SDLTG5`, `SDLTG6`, `SDLTG7`, `SDLTG8` | pain, frame G (G1 Gemini's pain figure; G2-G8 the standing view tilted back 9°, derived) | (a) idem | idem |
| `SDLTH0`, `SDLTI0`, `SDLTJ0`, `SDLTK0`, `SDLTL0` | death H-L, the five figures of Gemini's death sheet; `SDLTL0` the corpse lying flat | (a) idem | idem |
| `SDLTM0`, `SDLTN0`, `SDLTO0`, `SDLTP0`, `SDLTQ0`, `SDLTR0`, `SDLTS0`, `SDLTT0`, `SDLTU0` | gib M-U: no Gemini sheet, the death frames with procedural blood (derived); `SDLTU0` the remains on the floor | (a) idem | idem |

No armband: the Legion wears none (the US flag patch is left as Gemini drew
it). No photograph, no typeface. Freedoom's sprites never enter one.

## Enemy sprites: the Reich rifleman (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105, D108, D109 and D114)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`), with D108's armband
mix applied ("Ok a lo de las esvásticas! Ha quedado bien!", "OK to the swastikas! It turned out well!", D114,
`docs/art/previews/2026-10-22_P4_armbands-applied.png`): option 1, the D12
symbol warped onto each armband field by `tools/art/armband_symbol.py` after
the mirror (so it is never reversed), on every frame that shows a field;
option 2, a local Fooocus/SDXL inpaint over it, on the close pictures (the
profiles, rotations 3 and 7, and the corpse frames), 16 lumps of this set
(`symbol` in `metrics.json`). It replaces, name for name, the set drawn on
the 3D rig that the CEO approved on 2026-10-14 (cell E, D38, D48 and D55);
that set is history now, its generator `tools/art/gen_rig.py` kept, marked
historical, and its renders stay in `work/art/enemies/rig/` (not shipped).
Files in `assets/sprites/rifleman/`, copied byte for byte from
`work/art/enemies_gemini/rifleman/` (built on the Windows PC on 2026-10-22
by `python tools/art/gemini_enemy.py all`, rebuilt for the install:
identical), so each PNG keeps its `grAb` offsets. 70 lumps: frames A-G in
eight separate rotations, H-U in rotation 0; rotations 6-8 are 4-2 mirrored
and written as separate lumps (rifle and armband change arm, as in Doom's
mirrored pairs; the symbol is stamped after the mirror). RGBA with hard
alpha, palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_rifleman_*.png`) were generated by
the CEO's own Google Gemini account from the project's previous sprites;
they are gitignored and never distributed (D77). Frames Gemini did not draw
are derived by the tool and listed in `derived` of its `metrics.json`. Not
installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDRRA1`, `SDRRA2`, `SDRRA3`, `SDRRA4`, `SDRRA5`, `SDRRA6`, `SDRRA7`, `SDRRA8` | walk, frame A (Gemini's first stride), rotations 1-8 | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_rifleman_*.png`), processed by `tools/art/gemini_enemy.py rifleman`; armband symbol warped by `tools/art/armband_symbol.py` and partly repainted with local Fooocus/SDXL (D108); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDRRB1`, `SDRRB2`, `SDRRB3`, `SDRRB4`, `SDRRB5`, `SDRRB6`, `SDRRB7`, `SDRRB8` | walk, frame B (the standing view) | (a) idem | idem |
| `SDRRC1`, `SDRRC2`, `SDRRC3`, `SDRRC4`, `SDRRC5`, `SDRRC6`, `SDRRC7`, `SDRRC8` | walk, frame C (Gemini's second stride) | (a) idem | idem |
| `SDRRD1`, `SDRRD2`, `SDRRD3`, `SDRRD4`, `SDRRD5`, `SDRRD6`, `SDRRD7`, `SDRRD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDRRE1`, `SDRRE2`, `SDRRE3`, `SDRRE4`, `SDRRE5`, `SDRRE6`, `SDRRE7`, `SDRRE8` | aim, frame E | (a) idem | idem |
| `SDRRF1`, `SDRRF2`, `SDRRF3`, `SDRRF4`, `SDRRF5`, `SDRRF6`, `SDRRF7`, `SDRRF8` | fire, frame F (the muzzle flash as Gemini drew it) | (a) idem | idem |
| `SDRRG1`, `SDRRG2`, `SDRRG3`, `SDRRG4`, `SDRRG5`, `SDRRG6`, `SDRRG7`, `SDRRG8` | pain, frame G (G1 Gemini's pain figure; G2-G8 the standing view tilted back 9°, derived) | (a) idem | idem |
| `SDRRH0`, `SDRRI0`, `SDRRJ0`, `SDRRK0`, `SDRRL0` | death H-L, from Gemini's two death sheets; `SDRRL0` the corpse | (a) idem | idem |
| `SDRRM0`, `SDRRN0`, `SDRRO0`, `SDRRP0`, `SDRRQ0`, `SDRRR0`, `SDRRS0`, `SDRRT0`, `SDRRU0` | gib M-U: no Gemini sheet, the death frames with procedural blood (derived); `SDRRU0` the remains on the floor | (a) idem | idem |

No photograph, no typeface. Freedoom's sprites never enter one.

## Enemy sprites: the Reich hound (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105 and D109)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`). It replaces, name
for name, the set drawn on the 3D rig that the CEO approved on 2026-10-14
(cell A, D50 and D55); that set is history now, its generator
`tools/art/gen_hound.py` kept, marked historical, and its renders stay in
`work/art/enemies/hound_gsd/full_A/` (not shipped). Files in
`assets/sprites/hound/`, copied byte for byte from
`work/art/enemies_gemini/hound/` (built on the Windows PC on 2026-10-22 by
`python tools/art/gemini_enemy.py all`, rebuilt for the install: identical),
so each PNG keeps its `grAb` offsets. 46 lumps: frames A-H in Doom's
**mirrored pairs**, as the set it replaces (rotations 1 and 5 once, 2-4
drawn and flipped by the engine for 8-6, so `SDHNA2A8` is frame A rotation 2
and, mirrored, rotation 8), I-N in rotation 0. Gemini's sheets are 2 × 4
grids; five views are picked from each and its painted ground shadows keyed
out. RGBA with hard alpha, palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_hound_*.png`) were generated by the
CEO's own Google Gemini account from the project's previous sprites; they
are gitignored and never distributed (D77). Frames Gemini did not draw are
derived by the tool and listed in `derived` of its `metrics.json`. Not
installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDHNA1`, `SDHNA2A8`, `SDHNA3A7`, `SDHNA4A6`, `SDHNA5` | gallop, frame A (Gemini's first stride), rotations 1-8 (2-4 mirrored as 8-6) | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_hound_*.png`), processed by `tools/art/gemini_enemy.py hound`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDHNB1`, `SDHNB2B8`, `SDHNB3B7`, `SDHNB4B6`, `SDHNB5` | gallop, frame B (the standing view) | (a) idem | idem |
| `SDHNC1`, `SDHNC2C8`, `SDHNC3C7`, `SDHNC4C6`, `SDHNC5` | gallop, frame C (Gemini's second stride) | (a) idem | idem |
| `SDHND1`, `SDHND2D8`, `SDHND3D7`, `SDHND4D6`, `SDHND5` | gallop, frame D (the standing view) | (a) idem | idem |
| `SDHNE1`, `SDHNE2E8`, `SDHNE3E7`, `SDHNE4E6`, `SDHNE5` | bite, frame E (the standing view: the snarl) | (a) idem | idem |
| `SDHNF1`, `SDHNF2F8`, `SDHNF3F7`, `SDHNF4F6`, `SDHNF5` | bite, frame F (Gemini's bite sheet) | (a) idem | idem |
| `SDHNG1`, `SDHNG2G8`, `SDHNG3G7`, `SDHNG4G6`, `SDHNG5` | bite, frame G (the attack: F tilted 8° forward, derived) | (a) idem | idem |
| `SDHNH1`, `SDHNH2H8`, `SDHNH3H7`, `SDHNH4H6`, `SDHNH5` | pain, frame H (`SDHNH3H7` Gemini's pain figure; the others the standing view tilted 9°, derived) | (a) idem | idem |
| `SDHNI0`, `SDHNJ0`, `SDHNK0`, `SDHNL0`, `SDHNM0`, `SDHNN0` | death I-N, the six figures of Gemini's death sheet; `SDHNN0` the dog lying on its side | (a) idem | idem |

No collar symbol, no armband. No photograph, no typeface. Freedoom's sprites
never enter one.

## Enemy sprites: the Hybrid Stormtrooper and his bolt (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105, D108, D109 and D114; the bolt F5, D56)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`), with D108's armband
mix applied ("Ok a lo de las esvásticas! Ha quedado bien!", "OK to the swastikas! It turned out well!", D114,
`docs/art/previews/2026-10-22_P4_armbands-applied.png`): option 1, the D12
symbol warped onto each armband field by `tools/art/armband_symbol.py` after
the mirror (so it is never reversed), on every frame that shows a field;
option 2, a local Fooocus/SDXL inpaint over it, on the close pictures (the
profiles, rotations 3 and 7, and the corpse frames), 3 lumps of this set
(`symbol` in `metrics.json`). It replaces, name for name, the set drawn on
the 3D rig that the CEO approved on 2026-10-14 (cell E, D48, D53 and D56);
that set is history now, its generator `tools/art/gen_storm.py` kept, marked
historical, and its renders stay in `work/art/enemies/storm/full_E/` (not
shipped). Files in `assets/sprites/storm/`, copied byte for byte from
`work/art/enemies_gemini/storm/` (built on the Windows PC on 2026-10-22 by
`python tools/art/gemini_enemy.py all`, rebuilt for the install: identical),
so each PNG keeps its `grAb` offsets. 77 lumps: `SDHS` frames A-H in eight
separate rotations, I-U in rotation 0; rotations 6-8 are 4-2 mirrored and
written as separate lumps (the mechanical arm and the armband change side,
as in the rifleman). Gemini's sheets cut the boots at their last row: the
tool adds a 5-px dark sole (about 1 px in game). The bolt `SDBL` A-E is not
redrawn: it keeps its rig rows below. RGBA with hard alpha, palette v2. The
source sheets (`work/art/reference/enemies/gemini/gem_storm_*.png`) were
generated by the CEO's own Google Gemini account from the project's previous
sprites; they are gitignored and never distributed (D77). Frames Gemini did
not draw are derived by the tool and listed in `derived` of its
`metrics.json`. Not installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDHSA1`, `SDHSA2`, `SDHSA3`, `SDHSA4`, `SDHSA5`, `SDHSA6`, `SDHSA7`, `SDHSA8` | walk, frame A (Gemini's first stride), rotations 1-8 | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_storm_*.png`), processed by `tools/art/gemini_enemy.py storm`; armband symbol warped by `tools/art/armband_symbol.py` and partly repainted with local Fooocus/SDXL (D108); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDHSB1`, `SDHSB2`, `SDHSB3`, `SDHSB4`, `SDHSB5`, `SDHSB6`, `SDHSB7`, `SDHSB8` | walk, frame B (the standing view) | (a) idem | idem |
| `SDHSC1`, `SDHSC2`, `SDHSC3`, `SDHSC4`, `SDHSC5`, `SDHSC6`, `SDHSC7`, `SDHSC8` | walk, frame C (Gemini's second stride) | (a) idem | idem |
| `SDHSD1`, `SDHSD2`, `SDHSD3`, `SDHSD4`, `SDHSD5`, `SDHSD6`, `SDHSD7`, `SDHSD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDHSE1`, `SDHSE2`, `SDHSE3`, `SDHSE4`, `SDHSE5`, `SDHSE6`, `SDHSE7`, `SDHSE8` | attack, frame E (the charge, Gemini's aim sheet; claw and bolt share E F G) | (a) idem | idem |
| `SDHSF1`, `SDHSF2`, `SDHSF3`, `SDHSF4`, `SDHSF5`, `SDHSF6`, `SDHSF7`, `SDHSF8` | attack, frame F (the charge again) | (a) idem | idem |
| `SDHSG1`, `SDHSG2`, `SDHSG3`, `SDHSG4`, `SDHSG5`, `SDHSG6`, `SDHSG7`, `SDHSG8` | attack, frame G (the bolt, Gemini's fire sheet) | (a) idem | idem |
| `SDHSH1`, `SDHSH2`, `SDHSH3`, `SDHSH4`, `SDHSH5`, `SDHSH6`, `SDHSH7`, `SDHSH8` | pain, frame H (H1 Gemini's pain figure; H2-H8 the standing view tilted back 9°, derived) | (a) idem | idem |
| `SDHSI0`, `SDHSJ0`, `SDHSK0`, `SDHSL0`, `SDHSM0` | death I-M, the five figures of Gemini's death sheet; `SDHSM0` the corpse | (a) idem | idem |
| `SDHSN0`, `SDHSO0`, `SDHSP0`, `SDHSQ0`, `SDHSR0`, `SDHSS0`, `SDHST0`, `SDHSU0` | gib N-U: no Gemini sheet, the death frames with procedural blood (derived); `SDHSU0` the remains on the floor | (a) idem | idem |
| `SDBLA0`, `SDBLB0` | `SD_StormBolt` in flight, A-B | (a) `tools/art/gen_storm.py --full` (`bolt_model`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDBLC0`, `SDBLD0`, `SDBLE0` | `SD_StormBolt` burst, C-E | (a) idem | idem |

The bolt (`SDBL`) is still drawn from code on the 3D rig (D38): chrome-white
`steel_blue` with a `flag_red` core, palette v1. No photograph, no typeface.
Freedoom's sprites never enter one.

## Enemy sprites: the Panzermensch and the Schwer (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105, D108, D109 and D114)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`), with D108's armband
mix applied ("Ok a lo de las esvásticas! Ha quedado bien!", "OK to the swastikas! It turned out well!", D114,
`docs/art/previews/2026-10-22_P4_armbands-applied.png`): option 1, the D12
symbol warped onto each armband field by `tools/art/armband_symbol.py` after
the mirror (so it is never reversed), on every frame that shows a field;
option 2, a local Fooocus/SDXL inpaint over it, on the close pictures (the
profiles, rotations 3 and 7, and the corpse frames), 36 lumps of this set
(`symbol` in `metrics.json`). It replaces, name for name, the set drawn on
the 3D rig that the CEO approved on 2026-10-14 (cell D and its S2 variant,
D65 and D67); that set is history now, its generator
`tools/art/gen_heavy.py` kept, marked historical, and its renders stay in
`work/art/enemies/heavy/full/SDPM/` and `.../SDPS/` (not shipped). Files in
`assets/sprites/panzermensch/`, copied byte for byte from
`work/art/enemies_gemini/panzer/` and `.../panzer_heavy/` (built on the
Windows PC on 2026-10-22 by `python tools/art/gemini_enemy.py all`, rebuilt
for the install: identical), so each PNG keeps its `grAb` offsets. 142
lumps: 71 a set, frames A-H in eight separate rotations, I-O in rotation 0;
rotations 6-8 are 4-2 mirrored and written as separate lumps. The Schwer is
the same Gemini art drawn 12 % larger (D65, D67) with the plate darkened (×
0.55, every colour but red and white: D65's black plate); he dies face up
now. Gemini's sheets cut the boots at their last row: the tool adds a 3-px
dark sole. RGBA with hard alpha, palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_panzer_*.png`) were generated by the
CEO's own Google Gemini account from the project's previous sprites; they
are gitignored and never distributed (D77). Frames Gemini did not draw are
derived by the tool and listed in `derived` of its `metrics.json`. Not
installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDPMA1`, `SDPMA2`, `SDPMA3`, `SDPMA4`, `SDPMA5`, `SDPMA6`, `SDPMA7`, `SDPMA8` | walk, frame A (Gemini's first stride), rotations 1-8, `SD_Panzermensch` | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_panzer_*.png`), processed by `tools/art/gemini_enemy.py panzer` and `panzer_heavy`; armband symbol warped by `tools/art/armband_symbol.py` and partly repainted with local Fooocus/SDXL (D108); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDPMB1`, `SDPMB2`, `SDPMB3`, `SDPMB4`, `SDPMB5`, `SDPMB6`, `SDPMB7`, `SDPMB8` | walk, frame B (the standing view) | (a) idem | idem |
| `SDPMC1`, `SDPMC2`, `SDPMC3`, `SDPMC4`, `SDPMC5`, `SDPMC6`, `SDPMC7`, `SDPMC8` | walk, frame C (Gemini's second stride) | (a) idem | idem |
| `SDPMD1`, `SDPMD2`, `SDPMD3`, `SDPMD4`, `SDPMD5`, `SDPMD6`, `SDPMD7`, `SDPMD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDPME1`, `SDPME2`, `SDPME3`, `SDPME4`, `SDPME5`, `SDPME6`, `SDPME7`, `SDPME8` | attack, frame E (the arm back with the shell, Gemini's aim sheet) | (a) idem | idem |
| `SDPMF1`, `SDPMF2`, `SDPMF3`, `SDPMF4`, `SDPMF5`, `SDPMF6`, `SDPMF7`, `SDPMF8` | attack, frame F (the same pose held) | (a) idem | idem |
| `SDPMG1`, `SDPMG2`, `SDPMG3`, `SDPMG4`, `SDPMG5`, `SDPMG6`, `SDPMG7`, `SDPMG8` | attack, frame G (the throw, Gemini's fire sheet, the shell in flight removed: it is `SDPL`) | (a) idem | idem |
| `SDPMH1`, `SDPMH2`, `SDPMH3`, `SDPMH4`, `SDPMH5`, `SDPMH6`, `SDPMH7`, `SDPMH8` | pain, frame H (H1 Gemini's pain figure; H2-H8 the standing view tilted back 9°, derived) | (a) idem | idem |
| `SDPMI0`, `SDPMJ0`, `SDPMK0`, `SDPML0`, `SDPMM0`, `SDPMN0`, `SDPMO0` | death I-O, the six figures of Gemini's death sheet; `SDPMO0` the corpse (figure 6 without its smoke) | (a) idem | idem |
| `SDPSA1`, `SDPSA2`, `SDPSA3`, `SDPSA4`, `SDPSA5`, `SDPSA6`, `SDPSA7`, `SDPSA8` | walk, frame A, rotations 1-8, `SD_PanzermenschSchwer` (the Panzermensch's art × 1.12, the plate darkened) | (a) idem | idem |
| `SDPSB1`, `SDPSB2`, `SDPSB3`, `SDPSB4`, `SDPSB5`, `SDPSB6`, `SDPSB7`, `SDPSB8` | walk, frame B | (a) idem | idem |
| `SDPSC1`, `SDPSC2`, `SDPSC3`, `SDPSC4`, `SDPSC5`, `SDPSC6`, `SDPSC7`, `SDPSC8` | walk, frame C | (a) idem | idem |
| `SDPSD1`, `SDPSD2`, `SDPSD3`, `SDPSD4`, `SDPSD5`, `SDPSD6`, `SDPSD7`, `SDPSD8` | walk, frame D | (a) idem | idem |
| `SDPSE1`, `SDPSE2`, `SDPSE3`, `SDPSE4`, `SDPSE5`, `SDPSE6`, `SDPSE7`, `SDPSE8` | attack, frame E | (a) idem | idem |
| `SDPSF1`, `SDPSF2`, `SDPSF3`, `SDPSF4`, `SDPSF5`, `SDPSF6`, `SDPSF7`, `SDPSF8` | attack, frame F | (a) idem | idem |
| `SDPSG1`, `SDPSG2`, `SDPSG3`, `SDPSG4`, `SDPSG5`, `SDPSG6`, `SDPSG7`, `SDPSG8` | attack, frame G (the throw) | (a) idem | idem |
| `SDPSH1`, `SDPSH2`, `SDPSH3`, `SDPSH4`, `SDPSH5`, `SDPSH6`, `SDPSH7`, `SDPSH8` | pain, frame H | (a) idem | idem |
| `SDPSI0`, `SDPSJ0`, `SDPSK0`, `SDPSL0`, `SDPSM0`, `SDPSN0`, `SDPSO0` | death I-O; `SDPSO0` the corpse, face up | (a) idem | idem |

The shells `SDPL` keep their own section (D81). No photograph, no typeface.
Freedoom's sprites never enter one.

## Enemy sprites: the Doughboy (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105 and D109)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`). It replaces, name
for name, the set drawn on the 3D rig that the CEO approved on 2026-10-14
(cell C, D65, D67 and D70); that set is history now, its generator
`tools/art/gen_heavy.py` kept, marked historical, and its renders stay in
`work/art/enemies/heavy/full/SDDB/` (not shipped). Files in
`assets/sprites/doughboy/`, copied byte for byte from
`work/art/enemies_gemini/doughboy/` (built on the Windows PC on 2026-10-22
by `python tools/art/gemini_enemy.py all`, rebuilt for the install:
identical), so each PNG keeps its `grAb` offsets. 54 lumps: frames A-F in
eight separate rotations, G-L in rotation 0; rotations 6-8 are 4-2 mirrored
and written as separate lumps (the helmet's flag shows on the other side, as
in the Legion). The head hangs 14 px under its origin, as before. RGBA with
hard alpha, palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_doughboy_*.png`) were generated by
the CEO's own Google Gemini account from the project's previous sprites;
they are gitignored and never distributed (D77). Frames Gemini did not draw
are derived by the tool and listed in `derived` of its `metrics.json`. Not
installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDDBA1`, `SDDBA2`, `SDDBA3`, `SDDBA4`, `SDDBA5`, `SDDBA6`, `SDDBA7`, `SDDBA8` | float, frame A (the standing view), rotations 1-8, `SD_Doughboy` | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_doughboy_*.png`), processed by `tools/art/gemini_enemy.py doughboy`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDDBB1`, `SDDBB2`, `SDDBB3`, `SDDBB4`, `SDDBB5`, `SDDBB6`, `SDDBB7`, `SDDBB8` | attack, frame B (the standing view: Gemini drew no in-between) | (a) idem | idem |
| `SDDBC1`, `SDDBC2`, `SDDBC3`, `SDDBC4`, `SDDBC5`, `SDDBC6`, `SDDBC7`, `SDDBC8` | attack, frame C (the mouth open on the shell, Gemini's attack sheet) | (a) idem | idem |
| `SDDBD1`, `SDDBD2`, `SDDBD3`, `SDDBD4`, `SDDBD5`, `SDDBD6`, `SDDBD7`, `SDDBD8` | attack, frame D (idem, the spit) | (a) idem | idem |
| `SDDBE1`, `SDDBE2`, `SDDBE3`, `SDDBE4`, `SDDBE5`, `SDDBE6`, `SDDBE7`, `SDDBE8` | pain, frame E (E1 Gemini's pain figure; E2-E8 the standing view tilted 9°, derived) | (a) idem | idem |
| `SDDBF1`, `SDDBF2`, `SDDBF3`, `SDDBF4`, `SDDBF5`, `SDDBF6`, `SDDBF7`, `SDDBF8` | pain, frame F (F1 Gemini's hit figure; F2-F8 tilted 4.5°, derived) | (a) idem | idem |
| `SDDBG0`, `SDDBH0`, `SDDBI0`, `SDDBJ0`, `SDDBK0`, `SDDBL0` | death G-L, the six figures of Gemini's death sheet; `SDDBL0` the remains with the helmet | (a) idem | idem |

The helmet's US flag (D12) is left as Gemini drew it. The shells `SDDL` keep
their own section (D81). No photograph, no typeface. Freedoom's sprites
never enter one.

## Enemy sprites: the General and his shell (P4, redrawn from Google Gemini, approved by the CEO 2026-10-22, D105, D108, D109 and D114; the shell F5, D73)

CEO verdict: the seven enemies redrawn with Google Gemini (D105) approved
("Ok enemigos gemini", D109,
`docs/art/previews/2026-10-22_P4_enemies-gemini.html`), with D108's armband
mix applied ("Ok a lo de las esvásticas! Ha quedado bien!", "OK to the swastikas! It turned out well!", D114,
`docs/art/previews/2026-10-22_P4_armbands-applied.png`): option 1, the D12
symbol warped onto each armband field by `tools/art/armband_symbol.py` after
the mirror (so it is never reversed), on every frame that shows a field;
option 2, a local Fooocus/SDXL inpaint over it, on the close pictures (the
profiles, rotations 3 and 7, and the corpse frames), 2 lumps of this set
(`symbol` in `metrics.json`). It replaces, name for name, the set drawn on
the 3D rig that the CEO approved on 2026-10-14 (cells C and D, D71, D72 and
D73); that set is history now, its generator `tools/art/gen_general.py`
kept, marked historical, and its renders stay in
`work/art/general/full/SDGN/` (not shipped). Files in
`assets/sprites/general/`, copied byte for byte from
`work/art/enemies_gemini/general/` (built on the Windows PC on 2026-10-22 by
`python tools/art/gemini_enemy.py all`, rebuilt for the install: identical),
so each PNG keeps its `grAb` offsets. 81 lumps: `SDGN` frames A-G and Q-R in
eight separate rotations, H-P in rotation 0; rotations 6-8 are 4-2 mirrored
and written as separate lumps (Gemini drew the profile facing right: it is
mirrored to Doom's left-facing 2-4). The shell `SDGL` A-E is not redrawn: it
keeps its rig rows below. RGBA with hard alpha, palette v2. The source
sheets (`work/art/reference/enemies/gemini/gem_general_*.png`) were
generated by the CEO's own Google Gemini account from the project's previous
sprites; they are gitignored and never distributed (D77). Frames Gemini did
not draw are derived by the tool and listed in `derived` of its
`metrics.json`. Not installed: `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDGNA1`, `SDGNA2`, `SDGNA3`, `SDGNA4`, `SDGNA5`, `SDGNA6`, `SDGNA7`, `SDGNA8` | walk, frame A (Gemini's first stride), rotations 1-8, `SD_General` | (a) derived from Google Gemini images generated by the CEO's account from the project's previous sprites (`work/art/reference/enemies/gemini/gem_general_*.png`), processed by `tools/art/gemini_enemy.py general`; armband symbol warped by `tools/art/armband_symbol.py` and partly repainted with local Fooocus/SDXL (D108); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109) |
| `SDGNB1`, `SDGNB2`, `SDGNB3`, `SDGNB4`, `SDGNB5`, `SDGNB6`, `SDGNB7`, `SDGNB8` | walk, frame B (the standing view) | (a) idem | idem |
| `SDGNC1`, `SDGNC2`, `SDGNC3`, `SDGNC4`, `SDGNC5`, `SDGNC6`, `SDGNC7`, `SDGNC8` | walk, frame C (Gemini's second stride) | (a) idem | idem |
| `SDGND1`, `SDGND2`, `SDGND3`, `SDGND4`, `SDGND5`, `SDGND6`, `SDGND7`, `SDGND8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDGNE1`, `SDGNE2`, `SDGNE3`, `SDGNE4`, `SDGNE5`, `SDGNE6`, `SDGNE7`, `SDGNE8` | salvo, frame E (the bazooka aimed, Gemini's aim sheet) | (a) idem | idem |
| `SDGNF1`, `SDGNF2`, `SDGNF3`, `SDGNF4`, `SDGNF5`, `SDGNF6`, `SDGNF7`, `SDGNF8` | salvo, frame F (the shot: flash and back-blast, Gemini's fire sheet) | (a) idem | idem |
| `SDGNG1`, `SDGNG2`, `SDGNG3`, `SDGNG4`, `SDGNG5`, `SDGNG6`, `SDGNG7`, `SDGNG8` | pain, frame G (G1 Gemini's pain figure, the monocle flying; G2-G8 the standing view tilted 9°, derived) | (a) idem | idem |
| `SDGNQ1`, `SDGNQ2`, `SDGNQ3`, `SDGNQ4`, `SDGNQ5`, `SDGNQ6`, `SDGNQ7`, `SDGNQ8` | summon, frame Q (the standing view: Gemini drew no order, derived) | (a) idem | idem |
| `SDGNR1`, `SDGNR2`, `SDGNR3`, `SDGNR4`, `SDGNR5`, `SDGNR6`, `SDGNR7`, `SDGNR8` | summon, frame R (the aim view: he points the recruits on, derived) | (a) idem | idem |
| `SDGNH0`, `SDGNI0`, `SDGNJ0`, `SDGNK0`, `SDGNL0`, `SDGNM0`, `SDGNN0`, `SDGNO0`, `SDGNP0` | death H-P from Gemini's five death figures (K the J figure tilted 9°; the armband's letter on H-L covered by a plain field by hand); `SDGNP0` the corpse on the cloak | (a) idem | idem |
| `SDGLA0`, `SDGLB0` | `SD_GeneralShell` in flight, A-B (a white-hot core in a braid-yellow fire, an ember ring) | (a) `tools/art/gen_general.py --full` (`shell_model`, `render_shell`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDGLC0`, `SDGLD0`, `SDGLE0` | `SD_GeneralShell` burst, C-E | (a) idem | idem |

The shell (`SDGL`) is still drawn from code on the 3D rig (D38). No
photograph, no typeface. Freedoom's sprites never enter one.

## Enemy sprites: the Legion gunner (P4, drawn from Google Gemini, approved by the CEO 2026-10-23, D119 and D123)

CEO verdict: "Ok gunner" (D123, 2026-10-23, on
`docs/art/previews/2026-10-23_P4_gunner-gemini.html`). The gunner's first
sprites of his own: from D116 to D123 he wore the Legion trooper's `SDLT`
tinted brass in code (MOD-SPEC §6.12), which no longer ships for him. Files
in `assets/sprites/legion_gunner/`, copied byte for byte from
`work/art/enemies_gemini/gunner/` (`work/art/enemies_gemini/gunner/install.sh`),
so each PNG keeps its `grAb` offsets. 70 lumps: `SDLG` frames A-G in eight
separate rotations, H-U in rotation 0; rotations 6-8 are 4-2 mirrored and
written as separate lumps (Gemini drew the 3/4, profile and 3/4 back views
facing right; the flag patch changes shoulder, as the trooper's does). RGBA
with hard alpha, palette v2. The source sheets
(`work/art/reference/enemies/gemini/gem_gunner_*.png`: `turn`, `walkL`,
`walkR`, `aim_v3`, `fire`, `death_v2`) were generated on the CEO's own
Google Gemini account; they are gitignored and never distributed (D77).
Frames Gemini did not draw are derived by the tool and listed in `derived`
of its `metrics.json`; its `reask` (a walk with a real stride) was dropped:
the strides A and C are derived from Gemini's pixels instead (D127,
installed by D128). Not installed: `metrics.json`. Engine names:
MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDLGA1`, `SDLGA2`, `SDLGA3`, `SDLGA4`, `SDLGA5`, `SDLGA6`, `SDLGA7`, `SDLGA8` | walk, frame A (since D128 the left leg forward: Gemini's `turn` view with the legs cut and moved by `tools/art/walk_stride.py`, D127; Gemini's `walkL` was the standing pose), rotations 1-8, `SD_LegionGunner` | (a) derived from Google Gemini images generated on the CEO's account (`work/art/reference/enemies/gemini/gem_gunner_*.png`), processed by `tools/art/gemini_enemy.py gunner`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109, D123) |
| `SDLGB1`, `SDLGB2`, `SDLGB3`, `SDLGB4`, `SDLGB5`, `SDLGB6`, `SDLGB7`, `SDLGB8` | walk, frame B (the standing view, the `turn` sheet) | (a) idem | idem |
| `SDLGC1`, `SDLGC2`, `SDLGC3`, `SDLGC4`, `SDLGC5`, `SDLGC6`, `SDLGC7`, `SDLGC8` | walk, frame C (since D128 the right leg forward, `tools/art/walk_stride.py` as A) | (a) idem | idem |
| `SDLGD1`, `SDLGD2`, `SDLGD3`, `SDLGD4`, `SDLGD5`, `SDLGD6`, `SDLGD7`, `SDLGD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDLGE1`, `SDLGE2`, `SDLGE3`, `SDLGE4`, `SDLGE5`, `SDLGE6`, `SDLGE7`, `SDLGE8` | aim, frame E (`gem_gunner_aim_v3`: the front view aims at the camera; the others carry the gun at the hip) | (a) idem | idem |
| `SDLGF1`, `SDLGF2`, `SDLGF3`, `SDLGF4`, `SDLGF5`, `SDLGF6`, `SDLGF7`, `SDLGF8` | fire, frame F (the front view's flash in front of the chest, D119; the 3/4 back views have none, Gemini drew none) | (a) idem | idem |
| `SDLGG1`, `SDLGG2`, `SDLGG3`, `SDLGG4`, `SDLGG5`, `SDLGG6`, `SDLGG7`, `SDLGG8` | pain, frame G (G1 Gemini's pain figure; G2-G8 the standing view tilted 9°, derived) | (a) idem | idem |
| `SDLGH0`, `SDLGI0`, `SDLGJ0`, `SDLGK0`, `SDLGL0` | death H-L, the five figures of Gemini's `death_v2` sheet; `SDLGL0` the corpse lying flat | (a) idem | idem |
| `SDLGM0`, `SDLGN0`, `SDLGO0`, `SDLGP0`, `SDLGQ0`, `SDLGR0`, `SDLGS0`, `SDLGT0`, `SDLGU0` | gib M-U: no Gemini sheet, the death frames with procedural blood (derived); `SDLGU0` the remains on the floor | (a) idem | idem |

No armband and no swastika: the Legion wears none (the US flag patch is
left as Gemini drew it). No photograph, no typeface. Freedoom's sprites
never enter one.

## Enemy sprites: the Liberty Colossus (P4, drawn from Google Gemini, approved by the CEO 2026-10-23, D119 and D123)

CEO verdict: "Coloso me gustan las 2: colorear general y la estatua de la
libertad. Quiero los 2 en el juego" ("Colossus: I like both, the coloured
General and the Statue of Liberty. I want both in the game"; D123, 2026-10-23, on
`docs/art/previews/2026-10-23_P4_colossus-gemini.html`): the statue is
installed for `SD_LibertyColossus`, MAP06's boss; the other option, the
General's `SDGN` drawn x1.3 and tinted chrome in code, stays in the game as
`SD_ChromeGeneral` (no new image: it wears the General's rows above). Files
in `assets/sprites/colossus/`, copied byte for byte from
`work/art/enemies_gemini/colossus/` (`work/art/enemies_gemini/colossus/install.sh`),
so each PNG keeps its `grAb` offsets. 81 lumps: `SDLC` frames A-G and Q-R
in eight separate rotations, H-P in rotation 0, the General's letters;
rotations 6-8 are 4-2 mirrored and written as separate lumps. Drawn at full
size (no `Scale`, no tint). RGBA with hard alpha, palette v2. The source
sheets (`work/art/reference/enemies/gemini/gem_colossus_*.png`: `turn`,
`walkL`, `walkR`, `aim`, `fire`, `stomp`, `death`; the `*_sep.png` the
split writes) were generated on the CEO's own Google Gemini account; they
are gitignored and never distributed (D77). Frames Gemini did not draw are
derived and listed in `derived` of `metrics.json`; its quality gate names
two figures touched by the sheet's edge (the fire sheet's front view, the
death sheet's fifth), accepted with the set; its `reask` (a walk with a
real stride) was dropped: the strides A and C are derived from Gemini's
pixels instead (D127, installed by D128). Not installed:
`metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDLCA1`, `SDLCA2`, `SDLCA3`, `SDLCA4`, `SDLCA5`, `SDLCA6`, `SDLCA7`, `SDLCA8` | walk, frame A (since D128 a boot raised under the robe and the robe swinging: Gemini's `walkL` view with the boots cut and moved by `tools/art/walk_stride.py`, D127; until D128 `walkL` tilted 3°), rotations 1-8, `SD_LibertyColossus` | (a) derived from Google Gemini images generated on the CEO's account (`work/art/reference/enemies/gemini/gem_colossus_*.png`), processed by `tools/art/colossus_gemini.py` (the aim and fire sheets' views parted by mask, the two rockets in flight dropped) and `tools/art/gemini_enemy.py`'s `COLOSSUS`; the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109, D123) |
| `SDLCB1`, `SDLCB2`, `SDLCB3`, `SDLCB4`, `SDLCB5`, `SDLCB6`, `SDLCB7`, `SDLCB8` | walk, frame B (the standing view, the `turn` sheet) | (a) idem | idem |
| `SDLCC1`, `SDLCC2`, `SDLCC3`, `SDLCC4`, `SDLCC5`, `SDLCC6`, `SDLCC7`, `SDLCC8` | walk, frame C (since D128 the other boot, `tools/art/walk_stride.py` as A) | (a) idem | idem |
| `SDLCD1`, `SDLCD2`, `SDLCD3`, `SDLCD4`, `SDLCD5`, `SDLCD6`, `SDLCD7`, `SDLCD8` | walk, frame D (the standing view) | (a) idem | idem |
| `SDLCE1`, `SDLCE2`, `SDLCE3`, `SDLCE4`, `SDLCE5`, `SDLCE6`, `SDLCE7`, `SDLCE8` | salvo and jet, frame E (the torch aimed: E1 at the camera) | (a) idem | idem |
| `SDLCF1`, `SDLCF2`, `SDLCF3`, `SDLCF4`, `SDLCF5`, `SDLCF6`, `SDLCF7`, `SDLCF8` | salvo and jet, frame F (the torch firing: F1 the burst in front of it; the rockets in flight removed, the jet kept) | (a) idem | idem |
| `SDLCG1`, `SDLCG2`, `SDLCG3`, `SDLCG4`, `SDLCG5`, `SDLCG6`, `SDLCG7`, `SDLCG8` | pain, frame G (G1 the first death figure, cracking; G2-G8 the standing view tilted 6°, derived) | (a) idem | idem |
| `SDLCQ1`, `SDLCQ2`, `SDLCQ3`, `SDLCQ4`, `SDLCQ5`, `SDLCQ6`, `SDLCQ7`, `SDLCQ8` | stomp, frame Q (the foot raised, the `stomp` sheet's top row, drawn at half size and scaled x2) | (a) idem | idem |
| `SDLCR1`, `SDLCR2`, `SDLCR3`, `SDLCR4`, `SDLCR5`, `SDLCR6`, `SDLCR7`, `SDLCR8` | stomp, frame R (the foot down, the dust ring and cracks: the `stomp` sheet's bottom row) | (a) idem | idem |
| `SDLCH0`, `SDLCI0`, `SDLCJ0`, `SDLCK0`, `SDLCL0`, `SDLCM0`, `SDLCN0`, `SDLCO0`, `SDLCP0` | death H-P from Gemini's five death figures (K the J figure tilted 8°, M the L figure 20° further down); `SDLCP0` the wreck on the ground with the torch and the tablet | (a) idem | idem |

The tablet is blank (Gemini put no text on it); the US flag on the shoulder
as Gemini drew it; no swastika. No photograph, no typeface. Freedoom's
sprites never enter one. His projectiles (`SD_ColossusRocket`,
`SD_ColossusFlame`) wear the RPG-7's and the ROKS-3's sprites, whose rows
are their own.

## Enemy sprites: the Consortium (P4, Episode 3's final boss, drawn from Google Gemini, approved by the CEO 2026-10-24, D128)

CEO verdict: "Ok consorcio, añade paleta si es necesario" ("OK, Consortium; add a
palette if needed"; D128, 2026-10-24,
on `docs/art/previews/2026-10-24_P4_consortium-gemini.html`). The
Consortium's first sprites of its own: from D116 to D128 it wore the heavy
Panzermensch's `SDPS` drawn x1.75 and tinted the portal's cobalt in code
(MOD-SPEC §6.12), which no longer ships for it. Files in
`assets/sprites/consortium/`, copied byte for byte from
`work/art/enemies_gemini/consortium/` (`work/art/enemies_gemini/consortium/install.sh`),
so each PNG keeps its `grAb` offsets. 95 lumps: `SDCN` frames A-H and Q-S
in eight separate rotations, I-O in rotation 0. Rotations 6-8 are **not**
mirrors (the two halves differ): they are Gemini's 3/4 back, profile and 3/4
front unmirrored, with the halves' materials exchanged in code (the
grey-green skin and the pink, the SS helmet and the M1, the rack in chrome,
the armband as a chrome bracer); Gemini drew no view of that side. Drawn
at full size (no `Scale`, no tint). RGBA with hard alpha, **palette v3**
(D128): the Reich half's grey-green skin and its helmet are palette v3's
`reich_greygreen` (ART-BIBLE §3), the only lumps in v3; the CEO's sheet
showed them in v2, where that skin snapped to concrete grey, and his OK
asked for the ramp. The source sheets
(`work/art/reference/enemies/gemini/gem_consortium_*.png`: `rooted`,
`turn`, `walk`, `aim`, `fire`, `fire_v2`, `breach`, `death`, and the
`gem_consortium_fix_*.png` the repair stage writes) were generated on the
CEO's own Google Gemini account; they are gitignored and never distributed
(D77). Gemini drew every sheet with the halves the wrong way round, and in
some views gave an arm the other half's weapon, a third arm or a cable
skirt where a leg goes: the repairs (cut, drop, paste, graft, recolour, all
from Gemini's own pixels) are listed in `derived` of `metrics.json`. One
hole Gemini never drew (the F profile's hip, under the hanging rack) was
tried with local Fooocus over the Gemini sheet (D127) and discarded: it is
filled with the figure's own knot of cables. Not installed: `metrics.json`.
Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDCNA1`, `SDCNA2`, `SDCNA3`, `SDCNA4`, `SDCNA5`, `SDCNA6`, `SDCNA7`, `SDCNA8` | walk, frame A (phase 2, free: Gemini's `walk` sheet, top row; where Gemini put the cable skirt in place of a leg, C's legs under the belt), rotations 1-8, `SD_Consortium` | (a) derived from Google Gemini images generated on the CEO's account (`work/art/reference/enemies/gemini/gem_consortium_*.png`), repaired, mirrored and composed by `tools/art/consortium_gemini.py` and processed by `tools/art/gemini_enemy.py`'s `CONSORTIUM` (palette v3); the D12 symbol warped onto the armband by `tools/art/armband_symbol.py` (D108, D114); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D79, D109, D128) |
| `SDCNB1`, `SDCNB2`, `SDCNB3`, `SDCNB4`, `SDCNB5`, `SDCNB6`, `SDCNB7`, `SDCNB8` | walk, frame B (phase 2, standing: the `turn` sheet); also D | (a) idem | idem |
| `SDCNC1`, `SDCNC2`, `SDCNC3`, `SDCNC4`, `SDCNC5`, `SDCNC6`, `SDCNC7`, `SDCNC8` | walk, frame C (the `walk` sheet, bottom row) | (a) idem | idem |
| `SDCND1`, `SDCND2`, `SDCND3`, `SDCND4`, `SDCND5`, `SDCND6`, `SDCND7`, `SDCND8` | walk, frame D (= B, the standing view) | (a) idem | idem |
| `SDCNE1`, `SDCNE2`, `SDCNE3`, `SDCNE4`, `SDCNE5`, `SDCNE6`, `SDCNE7`, `SDCNE8` | the orbs' tell, frame E (the Legion arm comes up: the `aim` sheet, top row; a wrong arm and a third arm removed) | (a) idem | idem |
| `SDCNF1`, `SDCNF2`, `SDCNF3`, `SDCNF4`, `SDCNF5`, `SDCNF6`, `SDCNF7`, `SDCNF8` | the rockets' tell, frame F (the Reich arm's rack comes up: the `aim` sheet, bottom row; the profile's hip filled from its own knot of cables) | (a) idem | idem |
| `SDCNG1`, `SDCNG2`, `SDCNG3`, `SDCNG4`, `SDCNG5`, `SDCNG6`, `SDCNG7`, `SDCNG8` | firing, frame G, both phases (the `fire_v2` sheet, the legs replaced by the knot of cables and smoke; the rockets in flight removed: they are their own actor) | (a) idem | idem |
| `SDCNH1`, `SDCNH2`, `SDCNH3`, `SDCNH4`, `SDCNH5`, `SDCNH6`, `SDCNH7`, `SDCNH8` | pain, frame H (the discarded `fire` sheet, both mouths screaming, without rockets or flashes, tilted 5°) | (a) idem | idem |
| `SDCNQ1`, `SDCNQ2`, `SDCNQ3`, `SDCNQ4`, `SDCNQ5`, `SDCNQ6`, `SDCNQ7`, `SDCNQ8` | rooted, frame Q (phase 1, plugged into the portal: the `rooted` sheet; Spawn and See) | (a) idem | idem |
| `SDCNR1`, `SDCNR2`, `SDCNR3`, `SDCNR4`, `SDCNR5`, `SDCNR6`, `SDCNR7`, `SDCNR8` | rooted, frame R (Q with the core lit: it breathes) | (a) idem | idem |
| `SDCNS1`, `SDCNS2`, `SDCNS3`, `SDCNS4`, `SDCNS5`, `SDCNS6`, `SDCNS7`, `SDCNS8` | the Breach, frame S (the `breach` sheet, the cable column squashed to the rooted skirt's length) | (a) idem | idem |
| `SDCNI0`, `SDCNJ0`, `SDCNK0`, `SDCNL0`, `SDCNM0`, `SDCNN0`, `SDCNO0` | death I-O from Gemini's five death figures, mirrored (I the core cracks, J both heads scream, K the halves break, L it collapses burning, M the same sunk 10°, N and O the two helmets in the ashes) | (a) idem | idem |

The armband carries the D12 symbol (option 1, D108, D114), warped into
Gemini's white field after the mirror; rotations 6-8 show the Legion's
side and have no armband. The US flag patch is as Gemini drew it (on the
right shoulder after the mirror). No photograph, no typeface. Freedoom's
sprites never enter one. Its projectiles (`SD_ConsortiumRocket`,
`SD_ConsortiumOrb`, `SD_ConsortiumFlame`) wear sprites whose rows are
their own.

## Enemy sprites: the Doughboy's and the Panzermensch's shells (F5, approved by the CEO 2026-10-20, D81)

CEO verdict (D81, "los que tú recomiendas", "the ones you recommend"): option A of both sweeps
(`docs/art/previews/2026-10-19_2200_F5_enemy-shells.html`), the Doughboy's
shell "comet" and the Panzermensch's and Schwer's shell "ember". Files in
`assets/sprites/doughboy/` and `assets/sprites/panzermensch/`, beside their
throwers, copied byte for byte from `work/art/shells/SDDL/` and
the Panzermensch's `.../SDPL/` (rendered on the Windows PC on 2026-10-19 by
`tools/art/gen_shells.py`), so each PNG keeps its `grAb` offsets. Ten
lumps, all in rotation 0. RGBA with hard alpha, inside palette v1. Not
installed: the sweep's other options (`work/art/shells/sweep/`), the GIFs,
the scenes and `metrics.json`. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDDLA0`, `SDDLB0` | `SD_DoughboyShell` in flight, A-B (a white-hot `steel_blue` core in a `flag_red` corona, its flame tongue flickering) | (a) `tools/art/gen_shells.py`, shell `SDDL`, option A | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDDLC0`, `SDDLD0`, `SDDLE0` | `SD_DoughboyShell` burst, C-E | (a) idem | idem |
| `SDPLA0`, `SDPLB0` | `SD_PanzerShell` in flight, A-B (a dull `hazard_yellow` ball in an olive smoke halo, its hot core tumbling) | (a) `tools/art/gen_shells.py`, shell `SDPL`, option A | idem |
| `SDPLC0`, `SDPLD0`, `SDPLE0` | `SD_PanzerShell` burst, C-E | (a) idem | idem |

Drawn from code on the rig the approved enemies were drawn on, as the
storm bolt and the General's shell: no photograph, no typeface. Freedoom's
`BAL2` and `BAL7` appear only beside ours on the review sheet, for
comparison, and never enter a sprite.

## Player effects and world sprites (M2c, approved by the CEO 2026-10-20, D82)

CEO verdict (D82, "también las recomendadas", "the recommended ones too"): option A of each item of
the sweep (`docs/art/previews/2026-10-19_2208_F4_player-effects.html`).
Files in `assets/sprites/effects/`, copied byte for byte from
`work/art/effects/<SPRITE>/` (rendered on the Windows PC on 2026-10-19 by
`tools/art/gen_effects.py`, seed 75), so each PNG keeps its `grAb`
offsets. Fifty lumps: the two rockets in Doom's eight rotations as five
lumps each (2-8, 3-7, 4-6 mirrored pairs), everything else in rotation 0.
RGBA with hard alpha, inside palette v1. Five sprites have our `SD` names;
seven ship under the IWAD's names on purpose, the engine actors'
overrides (MOD-SPEC §1 and §5.1): every frame of each, exactly Freedoom's
lump set, so nothing of Freedoom's is left to mix in. Not installed: the
sweep's other options (`work/art/effects/sweep/`), the GIFs and the
scenes. Engine names: MOD-SPEC §6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDPGA1`, `SDPGA2A8`, `SDPGA3A7`, `SDPGA4A6`, `SDPGA5` | `SD_Pg7Grenade` in flight, the PG-7V: olive warhead, thin motor, fins, a short yellow-white plume | (a) `tools/art/gen_effects.py`, item pg7, option A | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `SDKRA1`, `SDKRA2A8`, `SDKRA3A7`, `SDKRA4A6`, `SDKRA5` | `SD_KatyushaRocket` in flight: slim steel body with a red identification band | (a) `tools/art/gen_effects.py`, item katyusha, option A | idem |
| `SDPXA0`, `SDPXB0`, `SDPXC0` | the burst both rockets share (their `Death`): a dirty fireball, TNT orange with black smoke and grit | (a) `tools/art/gen_effects.py`, item burst, option A | idem |
| `SDFJA0`, `SDFJB0` | `SD_FlameBlob` in flight, the ROKS-3's fire gob (drawn Add 0.85) | (a) `tools/art/gen_effects.py`, item flame, option A | idem |
| `SDFXA0`, `SDFXB0`, `SDFXC0`, `SDFXD0`, `SDFXE0` | `SD_FlameBlob` on impact | (a) `tools/art/gen_effects.py`, item flame, option A | idem |
| `PUFFA0`, `PUFFB0`, `PUFFC0`, `PUFFD0` | the engine's `BulletPuff` (and `SD_IceAxePuff`, which inherits it): a spark, then concrete dust and chips; IWAD name | (a) `tools/art/gen_effects.py`, item puff, option A | idem |
| `BLUDA0`, `BLUDB0`, `BLUDC0` | the engine's `Blood`: glossy drops, tinted by the D49 `BloodColor`; IWAD name | (a) `tools/art/gen_effects.py`, item blood, option A | idem |
| `TFOGA0`, `TFOGB0`, `TFOGC0`, `TFOGD0`, `TFOGE0`, `TFOGF0`, `TFOGG0`, `TFOGH0`, `TFOGI0`, `TFOGJ0` | the engine's `TeleportFog` (the General's summon): Tesla arcs over a pale glow; IWAD name | (a) `tools/art/gen_effects.py`, item tfog, option A | idem |
| `IFOGA0`, `IFOGB0`, `IFOGC0`, `IFOGD0`, `IFOGE0` | the engine's `ItemFog` (item respawn), the same arcs; IWAD name | (a) `tools/art/gen_effects.py`, item tfog, option A | idem |
| `BAR1A0`, `BAR1B0` | the engine's `ExplosiveBarrel` (editor number 2035): a red 200-litre fuel drum with a cream band; IWAD name | (a) `tools/art/gen_effects.py`, item barrel, option A | idem |
| `BEXPA0`, `BEXPB0`, `BEXPC0`, `BEXPD0`, `BEXPE0` | the drum bursting (`ExplosiveBarrel` `Death`); IWAD name | (a) `tools/art/gen_effects.py`, item barrel, option A | idem |
| `COLUA0` | the engine's `Column` (editor number 2028): the Soviet home floor lamp, a *torshier*; IWAD name | (a) `tools/art/gen_effects.py`, item lamp, option A | idem |

Drawn from code (the bestiary's rig for the rockets, the drum and the
lamp; seeded noise fields for fire, smoke, dust, drops and arcs): no
photograph, no typeface, no pack. Freedoom's sprites appear only on the
review sheet beside ours, for scale, and never enter a lump.

## Status bar, face and numbers (M2e, approved by the CEO 2026-10-20, D89, D90 and D92)

CEO choices: status bar **A**, the olive-drab instrument panel (D89), in
English and Russian; the numbers **N2**, stencil segments (D92), all three
sets; and the sergeant's face from his Google Gemini sheets (D89, "utiliza
Gemini"; approved D90, "Cara aprobada";
`docs/art/previews/2026-10-20_1127_M4_hud-face-sweep.html`,
`docs/art/previews/2026-10-20_1148_M4_face-gemini.png`). Files in
`assets/graphics/statusbar/`, copied byte for byte from `work/art/hud/`
(rendered on the Windows PC on 2026-10-20 by `tools/art/gen_hud.py`, and by
`gen_hud.py --face gemini`, which runs `tools/art/gemini_face.py`), so each
PNG keeps its size and `grAb` offsets, equal to Freedoom 0.13.0's lump of
the same name. The bar pictures are indexed and use palette v1 colours;
the digits are RGBA with hard alpha, palette v1; the faces RGBA with hard
alpha, palette v2 (`flesh_pink` in the skin). The 76 English lumps ship
under the engine's names on purpose, the names `DoomStatusBar` and its
fonts draw (MOD-SPEC §1); the two Russian pictures have our `SD` names and
`SD_StatusBar` draws their labels (MOD-SPEC §6.5.1). The CEO generated the
two face sheets with Google Gemini; they stay in `work/art/reference/` and
are never distributed (D77). Not installed: bars B and C, the bilingual
bar, the drawn faces A-C, digits N3, the review sheets. Engine names:
MOD-SPEC §6.5.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `STBAR` | the status bar, 320×32, bar A in English: olive-drab riveted 4BO plate, recessed wells, cream stencilled labels AMMO, HEALTH, ARMS, ARMOR | (a) `tools/art/gen_hud.py`, bar A, English labels (`work/art/hud/bar/A/en/`) | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `STARMS` | the arms panel over the bar, 38×32, bar A in English | (a) `tools/art/gen_hud.py`, bar A, English labels | idem |
| `SDSBRU` | the status bar in Russian (bar A, Cyrillic labels); drawn by `SD_StatusBar` for `[ru]` | (a) `tools/art/gen_hud.py`, bar A, Russian labels (`work/art/hud/bar/A/ru/STBAR.png`, renamed) | idem |
| `SDARRU` | the arms panel in Russian (bar A) | (a) `tools/art/gen_hud.py`, bar A, Russian labels (`work/art/hud/bar/A/ru/STARMS.png`, renamed) | idem |
| `SDSBCA` | the status bar in Catalan (bar A, labels MUNICIÓ, SALUT, ARMES, ARMADURA; P6, D97); drawn by `SD_StatusBar` for `[ca]` | (a) `tools/art/gen_hud.py --catalan`, bar A, Catalan labels (`work/art/hud/bar/A/ca/STBAR.png`, renamed) | idem |
| `SDARCA` | the arms panel in Catalan (bar A) | (a) `tools/art/gen_hud.py --catalan`, bar A, Catalan labels (`work/art/hud/bar/A/ca/STARMS.png`, renamed) | idem |
| `STTNUM0`, `STTNUM1`, `STTNUM2`, `STTNUM3`, `STTNUM4`, `STTNUM5`, `STTNUM6`, `STTNUM7`, `STTNUM8`, `STTNUM9`, `STTMINUS`, `STTPRCNT` | the big red numbers, minus and percent, 13×16: stencil segments (also the fullscreen HUD's font, `HUDFONT_DOOM`) | (a) `tools/art/gen_hud.py`, digits N2 (`work/art/hud/digits/N2/`) | idem |
| `STYSNUM0`, `STYSNUM1`, `STYSNUM2`, `STYSNUM3`, `STYSNUM4`, `STYSNUM5`, `STYSNUM6`, `STYSNUM7`, `STYSNUM8`, `STYSNUM9` | the small yellow digits, 4×6: a weapon slot owned, and the ammo table (`INDEXFONT_DOOM`) | (a) `tools/art/gen_hud.py`, digits N2 | idem |
| `STGNUM0`, `STGNUM1`, `STGNUM2`, `STGNUM3`, `STGNUM4`, `STGNUM5`, `STGNUM6`, `STGNUM7`, `STGNUM8`, `STGNUM9` | the small grey digits, 4×6: a weapon slot not owned | (a) `tools/art/gen_hud.py`, digits N2 | idem |
| `STFST00`, `STFST01`, `STFST02` | the sergeant's face, damage level 0, looking straight (eyes left, centre, right) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 0, the straight cell), processed into pixel art by `tools/art/gemini_face.py` (the eyes moved 1 px for the glances); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D93) |
| `STFTL00`, `STFTR00` | the face, level 0, turned to the screen's left / right (hit from that side) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 0, the turned cells), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFOUCH0` | the face, level 0, a big hit | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 0, the ouch cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFEVL0` | the face, level 0, the evil grin (a weapon picked up) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 0, the grin cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFKILL0` | the face, level 0, the rampage snarl (sustained fire) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 0, the straight cell's frown over the grin cell's teeth), processed into pixel art by `tools/art/gemini_face.py` (the two cells joined below the nose); the source images are not distributed | idem |
| `STFST10`, `STFST11`, `STFST12` | the sergeant's face, damage level 1, looking straight (eyes left, centre, right) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 1, the straight cell), processed into pixel art by `tools/art/gemini_face.py` (the eyes moved 1 px for the glances); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D93) |
| `STFTL10`, `STFTR10` | the face, level 1, turned to the screen's left / right (hit from that side) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 1, the turned cells), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFOUCH1` | the face, level 1, a big hit | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 1, the ouch cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFEVL1` | the face, level 1, the evil grin (a weapon picked up) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 1, the grin cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFKILL1` | the face, level 1, the rampage snarl (sustained fire) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 1, the straight cell's frown over the grin cell's teeth), processed into pixel art by `tools/art/gemini_face.py` (the two cells joined below the nose); the source images are not distributed | idem |
| `STFST20`, `STFST21`, `STFST22` | the sergeant's face, damage level 2, looking straight (eyes left, centre, right) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 2, the straight cell), processed into pixel art by `tools/art/gemini_face.py` (the eyes moved 1 px for the glances); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D93) |
| `STFTL20`, `STFTR20` | the face, level 2, turned to the screen's left / right (hit from that side) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 2, the turned cells), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFOUCH2` | the face, level 2, a big hit | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 2, the ouch cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFEVL2` | the face, level 2, the evil grin (a weapon picked up) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 2, the grin cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFKILL2` | the face, level 2, the rampage snarl (sustained fire) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 2, the straight cell's frown over the grin cell's teeth), processed into pixel art by `tools/art/gemini_face.py` (the two cells joined below the nose); the source images are not distributed | idem |
| `STFST30`, `STFST31`, `STFST32` | the sergeant's face, damage level 3, looking straight (eyes left, centre, right) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 3, the straight cell), processed into pixel art by `tools/art/gemini_face.py` (the eyes moved 1 px for the glances); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D93) |
| `STFTL30`, `STFTR30` | the face, level 3, turned to the screen's left / right (hit from that side) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 3, the turned cells), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFOUCH3` | the face, level 3, a big hit | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 3, the ouch cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFEVL3` | the face, level 3, the evil grin (a weapon picked up) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 3, the grin cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFKILL3` | the face, level 3, the rampage snarl (sustained fire) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 3, the straight cell's frown over the grin cell's teeth), processed into pixel art by `tools/art/gemini_face.py` (the two cells joined below the nose); the source images are not distributed | idem |
| `STFST40`, `STFST41`, `STFST42` | the sergeant's face, damage level 4, looking straight (eyes left, centre, right) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 4, the straight cell), processed into pixel art by `tools/art/gemini_face.py` (the eyes moved 1 px for the glances); the source images are not distributed | Soviet Doom project, CC BY-NC-SA 4.0 (D15); the AI use is disclosed in the game's and the release's credits (D93) |
| `STFTL40`, `STFTR40` | the face, level 4, turned to the screen's left / right (hit from that side) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 4, the turned cells), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFOUCH4` | the face, level 4, a big hit | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 4, the ouch cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFEVL4` | the face, level 4, the evil grin (a weapon picked up) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 4, the grin cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFKILL4` | the face, level 4, the rampage snarl (sustained fire) | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, row 4, the straight cell's frown over the grin cell's teeth), processed into pixel art by `tools/art/gemini_face.py` (the two cells joined below the nose); the source images are not distributed | idem |
| `STFGOD0` | the face in god mode: glowing eyes | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, and `gemini_face_god_dead.png`, the god cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |
| `STFDEAD0` | the face, dead | (a) derived from images generated by the project lead with Google Gemini (`work/art/reference/gemini_face_grid.png`, and `gemini_face_god_dead.png`, the dead cell), processed into pixel art by `tools/art/gemini_face.py` (cut, keyed, reduced and palette-snapped); the source images are not distributed | idem |

The bars and digits are drawn from code: rectangles, rivets, seeded noise
and a 5-px bitmap alphabet written into `gen_hud.py` (no system font, so
they reproduce byte for byte on any machine); the digits are vector
segments, supersampled. Freedoom's bar, numbers and face appear only on the
review sheet beside ours, and never enter a lump.
