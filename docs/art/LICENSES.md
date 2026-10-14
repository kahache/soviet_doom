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
| `work/art/reference/stalin_1930.jpg` (sha256 `867bfc45…6fd9`, 1313×2100, 497,531 bytes) | Portrait of Stalin, frontispiece of *The Life of Stalin: A Symposium*, Workers Library Publishers, New York, 1930; photographer unknown | Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Stalin-Joseph-1930.jpg (file https://upload.wikimedia.org/wikipedia/commons/8/86/Stalin-Joseph-1930.jpg) — public domain in the United States (published 1930, before 1 January 1931; also published without notice) and in Russia (anonymous work published before 1943). Residual risk: Russian status rests on the photographer staying unidentified. Downloaded 2026-10-14 with the CEO's permission | Base for the posterised Stalin poster (`tools/art/gen_stalin.py`, proposal; lump name not yet assigned). `work/` is gitignored: never committed or shipped. Rationale, candidates and rejected sources: `docs/product/2026-10-14_1556_F2_stalin-poster-sourcing.md` |

## Shell screens (F2, approved 2026-10-13)

The CEO liked treatments A and C equally and did not have to choose: each
takes the role it fits. A greets the player, C sits behind the between-level
statistics because its diagonal leaves the centre free.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `TITLEPIC` | Title screen, treatment A "Plakat": flag-red ground, cream ray fan, the rocket profile reused from `SDPOSTR2`, gold star, black masthead reading «СОВЕТСКИЙ DOOM» | (a) `tools/art/gen_shell.py`, `titlepic_a()` + `lockup_a()`, palette v1 | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `INTERPIC` | Between-level screen, treatment C "Rodchenko": maroon ground cut by diagonals, gold star, centre deliberately empty for the engine's map name and counters | (a) `tools/art/gen_shell.py`, `interpic_c()`, palette v1 | idem |
| `M_DOOM` | Menu logo, registered on the title's own name block so it lands exactly over it when the menu opens | (a) `tools/art/gen_shell.py`, `logo()` + `lockup_a()`, palette v1. RGBA with hard alpha (0/255, no semitransparency), not indexed: a menu patch needs transparency. **One of two RGBA families in the project**; the other is the alphabet's 224 glyphs (below). Both are the exception recorded in ART-BIBLE §2 | idem |

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
`SD` prefix rule (MOD-SPEC §1). Only the English plaque ships; the Russian
one (`pause_P2_ru.png`, same origin) waits on the packer (MOD-SPEC §10, T12).
Per-lump rows: `TEXTURE-INDEX.md`, "Shell pictures".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `M_SKULL1` / `M_SKULL2` | menu cursor, the two blink phases: the hammer and sickle, gold then pale cream, with a dark-red outline | (a) `tools/art/gen_cursor.py`, `cursor_image("B", 1/2)`, palette v1; the emblem's geometry imported from `gen_soviet_base.hammer_sickle()` (the approved `SDSTAR1` v5), never re-traced | Soviet Doom project (art-director), own work, CC BY-NC-SA 4.0 (D15) |
| `M_PAUSE` | pause sign, English: «PAUSE» on a flag-red plaque with a cream border | (a) `tools/art/gen_cursor.py`, `pause_image("P2", "en")`, palette v1; the word set in our own `SDMENU` folder font (read from `assets/fonts/sdmenu/`, above), no system font | idem |

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
| `fonts/defsmallfont/*.png` (112) | Small font, cap 7 px, line 9. HUD messages, pickups, the option menu | (a) `tools/art/gen_font.py`, style C, glyphs defined as drawing code rather than images | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `fonts/bigfont/*.png` (112) | Big font, cap 11 px plus a 1 px shadow, line 16. Menu headlines and level titles | idem | idem |

**Drawn, not derived.** Every glyph is constructed from the project's own
stroke rules in `gen_font.py`; no typeface was traced, subset or converted,
so there is no font licence to inherit. The styles were named after what they
imitate in spirit — poster grotesque, GOST drawing lettering, slab machinery
— not after any particular type family.

Coverage: А-Я and Ё, A-Z, 0-9, the German Ä Ö Ü and the sharp s (ẞ U+1E9E
and ß U+00DF, one drawing), and the punctuation the project uses including
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
in-game trial, D37: «Las pruebo, incluso la B se queda»).** Ä, Ö, Ü and the
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

## The menu font SDMENU (D31, approved for in-engine trial 2026-10-13)

The first construction of D22 (level 2: R→Я, N→И, E→Э, W→Ш, A→Д). Used only
by the menu descriptors (`Font "SDMENU"` in `MENUDEF`), never by running
text, so the proper nouns, calibres and key prompts that
`docs/product/LANGUAGE-SWITCH.md` keeps in Latin are never drawn with it.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `fonts/sdmenu/*.png` (112) | Menu font: `fonts/bigfont/` (cap 11 px plus a 1 px shadow, line 16) with the five Latin capitals R, N, E, W, A drawn with the forms of Я, И, Э, Ш, Д. Russian strings use Cyrillic code points and are unaffected, so one font serves both languages | (a) `tools/art/gen_menu.py`: 107 glyphs (the German five included since D37) and `font.inf` copied byte for byte from `assets/fonts/bigfont/`; the five substituted glyphs rendered by `gen_font.glyph_image()` from the Cyrillic letters' stroke code, byte-identical to `0414`, `0418`, `042D`, `042F` and `0428` of `bigfont/`. No new drawing, no system font | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |

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

CEO verdict, verbatim: «OK a las 6 piezas de metro» — shipped as drawn in
palette v1. Files in `assets/textures/metro/` and `assets/flats/metro/`,
copied byte for byte from the Mac's renders in `work/art/batch2/metro/`
(SHA-256 checked against `work/MANIFEST-from-mac.txt`); the same six
regenerate byte-identical on the Windows PC. Per-lump rows and seeds:
`TEXTURE-INDEX.md`, set "Metro".

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDTILE1`, `SDTILE2` | glazed cream tile wall; the same over a green oil-paint dado | (a) `tools/art/gen_metro.py`, `BATCH_SEED` 1935, palette v1 | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `SDMARB1` | red marble cladding with veins | (a) idem | idem |
| `SDMOSA1` | mosaic panel, gold star with rays on slate blue, drawn from scratch on a tessera grid | (a) idem | idem |
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

## Music (D43, installed 2026-10-13)

Rows added by `sound-designer` so `tools/check_pk3.py` can see the music
lumps' provenance. The full rights analysis — composition, lyrics,
phonogram and sequencing, each with its source — is owned by
`docs/sound/MUSIC-RIGHTS.md` §4.4; these rows only point at it. Files in
`assets/music/`, packed as `music/<LUMP>.mid`.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `D_SDINTL` | title theme: *The Internationale* (De Geyter, 1888), orchestral MIDI | sequenced by **Jerry Engelbach** (2003), Wikimedia Commons `File:Internationale_orch2.mid`; 1.99 s of head silence removed by us (`tools/audio/midi_edit.py --trim-head`) | melody public domain (`{{PD-Internationale}}`); sequencing `{{Attribution\|Jerry Engelbach}}` — **credit "Jerry Engelbach" is required** |
| `D_SDM01` | MAP01 loop "Zarya-7" | original composition, `tools/audio/gen_music.py` (sound-designer, 2026-10-13) | Soviet Doom project, CC BY-NC-SA 4.0 (D15) |
| `D_SDRAD1` | diegetic radio (`SD_Radio`, MOD-SPEC §6.7): «Эй, ухнем» / *Ey, ukhnem* (Volga Boatmen), Balakirev's setting, pub. 1866 | sequenced by **Peter Gerloff** (Commons: *Rabanus Flavus*, 2021), Wikimedia Commons `File:Ej,_uchnem!.mid`; installed by `mod-engineer` 2026-10-13 byte-identical to `work/audio/candidates/WM_Ej_uchnem.mid` (`D_CND09`), unedited | composition public domain (RU and US); sequencing CC0 1.0 (`{{self\|Cc-zero}}`) — no obligation; Gerloff credited as a courtesy |
| `D_SDRAD2` | diegetic radio (`SD_Radio`, MOD-SPEC §6.7): «Колокольчик» / *Kolokolchik*, Russian traditional | sequenced by **Peter Gerloff** (2019), Wikimedia Commons `File:Kolokolchik.mid`; installed by `mod-engineer` 2026-10-13 byte-identical to `work/audio/candidates/WM_Kolokolchik.mid` (`D_CND12`), unedited | composition public domain (RU and US); sequencing CC0 1.0 (`{{self\|Cc-zero}}`) — no obligation; Gerloff credited as a courtesy |

## Weapon pickups (F4, approved by the CEO 2026-10-14, D48)

CEO verdict (D48): the ice axe with pickup **C**, the PPSh-41, and "Resto del
arsenal: OK" for the TT-33, IZh-58, RPG-7 and ROKS-3. Only the **world
pickups** are installed: after playing MAP01 with the draft overlay the same
day the CEO found hand E deformed, so the first-person (held) and muzzle-flash
frames, which show the hand, stay drafts in `work/` until the hands are
redrawn. Files in `assets/sprites/<weapon>/`, copied byte for byte from
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

## Enemy sprites: the Liberty Legion trooper (F5, approved by the CEO 2026-10-14, D48 and D54)

CEO verdict: cell **C** of the Legion sweep (D48), then the redone death,
the corpse lying flat ("Muerte legión OK", D54), so the full set stands as
drawn. Files in `assets/sprites/legion/`, copied byte for byte from
`work/art/enemies/legion/full_C/` (rendered on the Windows PC on 2026-10-14
by `gen_legion.py --full`), so each PNG keeps its `grAb` offsets. 70 lumps:
frames A-G in eight separate rotations (no mirrored pairs), H-U in rotation
0. RGBA with hard alpha. Not installed: `old_death/` (the superseded death),
the GIFs, the `pair_*` lineups and `metrics.json`. Engine names: MOD-SPEC
§6.3.

| Lump | What it is | Origin | Licence |
|---|---|---|---|
| `SDLTA1`, `SDLTA2`, `SDLTA3`, `SDLTA4`, `SDLTA5`, `SDLTA6`, `SDLTA7`, `SDLTA8` | walk, frame A, rotations 1-8 | (a) `tools/art/gen_legion.py --full` (`build_full`, `render_full`), cell C on the rig (`tools/art/rig_core.py`) | Soviet Doom project (art-director), CC BY-NC-SA 4.0 (D15) |
| `SDLTB1`, `SDLTB2`, `SDLTB3`, `SDLTB4`, `SDLTB5`, `SDLTB6`, `SDLTB7`, `SDLTB8` | walk, frame B | (a) idem | idem |
| `SDLTC1`, `SDLTC2`, `SDLTC3`, `SDLTC4`, `SDLTC5`, `SDLTC6`, `SDLTC7`, `SDLTC8` | walk, frame C | (a) idem | idem |
| `SDLTD1`, `SDLTD2`, `SDLTD3`, `SDLTD4`, `SDLTD5`, `SDLTD6`, `SDLTD7`, `SDLTD8` | walk, frame D | (a) idem | idem |
| `SDLTE1`, `SDLTE2`, `SDLTE3`, `SDLTE4`, `SDLTE5`, `SDLTE6`, `SDLTE7`, `SDLTE8` | aim, frame E | (a) idem | idem |
| `SDLTF1`, `SDLTF2`, `SDLTF3`, `SDLTF4`, `SDLTF5`, `SDLTF6`, `SDLTF7`, `SDLTF8` | fire, frame F (muzzle flash drawn in) | (a) idem | idem |
| `SDLTG1`, `SDLTG2`, `SDLTG3`, `SDLTG4`, `SDLTG5`, `SDLTG6`, `SDLTG7`, `SDLTG8` | pain, frame G | (a) idem | idem |
| `SDLTH0`, `SDLTI0`, `SDLTJ0`, `SDLTK0`, `SDLTL0` | death H-L, dark-red blood (D49); `SDLTL0` the corpse lying flat (D54) | (a) idem, `death_blood` | idem |
| `SDLTM0`, `SDLTN0`, `SDLTO0`, `SDLTP0`, `SDLTQ0`, `SDLTR0`, `SDLTS0`, `SDLTT0`, `SDLTU0` | gib M-U, dark-red blood (D49); `SDLTU0` the remains on the floor (redone with the death) | (a) idem, `build_gib`, `gib_blood` | idem |

Drawn from code on the 3D rig approved as the method (D38): primitives,
two-bone IK, Doom's eight rotations, majority vote to 1x, contour and rim;
chrome in `steel_blue`, flesh in palette v2's `flesh_pink` (D45), blood in
`flag_red` (D49). No photograph, no typeface. Freedoom's `SPOSA1` and
`POSSA1` appear only beside ours on the review sheets, for comparison, and
never enter a sprite.
