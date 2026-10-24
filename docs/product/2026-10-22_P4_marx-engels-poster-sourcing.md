# Marx and Engels poster: photograph sourcing, composition, slogan (P4)

Date: 2026-10-22. Author: art-director. Russian mirror: written by
`translator-ru` at phase close (D34).
CEO request (2026-10-22, D106): "I want more communist posters; following
Lenin's and Stalin's, which came out very well, make one with **Marx and
Engels**."

So the method is `SDPOSTR1` v4 / `SDPOSTR3`: public-domain photographs
posterised to four flat palette-v1 inks, the cream printed border, the gold
rule and the 46 px slogan band, and a 15-cell sweep for the CEO to point at.
New this time: two photographs on one sheet. Legal criteria are those of
`2026-10-12_2000_F2_pm-soviet-art-copyright.md` and the Stalin study
(`2026-10-14_1556_F2_stalin-poster-sourcing.md`). Every size and date below
comes from the Wikimedia Commons API (JSON metadata: `imageinfo`,
`extmetadata`, `categories`, wikitext, upload log), queried 2026-10-22.
No image was downloaded for the study. The CEO then gave the OK, and the PM
downloaded the recommended pair the same day (§8, which also records the
format the CEO chose).

## 1. Legal test

A photograph qualifies if it is public domain in all three places:

- **Russia:** the author died before 1 January 1952.
- **United States:** published before 1931. An unpublished work is
  protected for life + 70 years, so it also qualifies if the author died
  before 1953.
- **European Union:** the author died more than 70 years ago. Faithful
  scans of a public-domain photograph add no new right (EU Directive
  2019/790, art. 14; in the US, *Bridgeman v. Corel*).

Both men died in the 19th century (Marx in 1883, Engels in 1895), and every
photographer below died between 1891 and 1924, so their photographs pass
all three tests whether or not they were "published". This is much cleaner than Stalin,
whose Russian status rests on an anonymous photographer staying anonymous.
**The risk sits in the scans, not in the law:** which copy is sharpest, and
whether a Commons uploader has retouched it.

## 2. Candidate photographs

### Karl Marx

| # | Commons file | Author, date | Status | Size (px, bytes) | Use for posterising |
|---|---|---|---|---|---|
| **M1, recommended** | [File:Karl Marx 001.jpg](https://commons.wikimedia.org/wiki/File:Karl_Marx_001.jpg), file `https://upload.wikimedia.org/wikipedia/commons/d/d4/Karl_Marx_001.jpg` | John Jabez Edwin Mayall's studio, 224 Regent Street, London, "before 24 August 1875". Source: International Institute of Social History (IISH), Amsterdam | Tagged `PD-old-100-expired` and `PD/1923\|1901`. J. J. E. Mayall died in 1901. A Commons sibling credits his son John Mayall junior (d. 1891), from an 1875 letter to Marx. Either way PD in Russia, the US and the EU | 1428 × 2048, 380,651 B | **The** Marx portrait: the source of every later Marx image, including the Soviet ones. Seated, three-quarter length, hand in waistcoat. Commons category: *Black and white photographs of men looking at viewer*. It has head-and-shoulders crops on Commons (`(cropped 3-4)`, `(cropped 2)`), so the head is clear. The upload log shows reverts between 2021 and 2023 (retouched versions uploaded, then reverted), so the PM records the SHA-256 at download |
| M2 | [File:Karl Marx by John Jabez Edwin Mayall 1875 - Restored (cropped).png](https://commons.wikimedia.org/wiki/File:Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored_(cropped).png), file `https://upload.wikimedia.org/wikipedia/commons/5/53/Karl_Marx_by_John_Jabez_Edwin_Mayall_1875_-_Restored_%28cropped%29.png` | The same 1875 sitting. Albumen print in the Städel Museum, Frankfurt (St.F.131), mounted on the studio's card. Dust and scratches removed by a Commons user | `PD-old-100-expired`; the museum's own PD mark. Dust removal adds no right | 1481 × 1976, 1,376,570 B (PNG) | The fallback if M1's scan turns out soft or retouched. Second-best size, and 3.6× M1's bytes. The full Städel original (`Portrait Karl Marx (SM stf131).png`, 2928 × 4361) is 12,073,747 B: too heavy for a 64-128 px cell |

### Friedrich Engels

| # | Commons file | Author, date | Status | Size (px, bytes) | Use for posterising |
|---|---|---|---|---|---|
| **E1, recommended** | [File:Friedrich Engels portrait.jpg](https://commons.wikimedia.org/wiki/File:Friedrich_Engels_portrait.jpg), file `https://upload.wikimedia.org/wikipedia/commons/7/75/Friedrich_Engels_portrait.jpg` | William Hall (1826 - c. 1898), May 1877. Source: UNESCO Memory of the World image (the Manifesto and *Capital* nomination) | `PD-old-auto-expired`, author died c. 1898. PD in Russia, the US and the EU | 945 × 1437, 514,277 B | Same decade as M1: Engels at 56, Marx at 57. Half length. It has a head crop on Commons (`(cropped)`, 615 × 820, "sepia tone removed"), so the head is clear. A sepia print, which is no problem: the generator works on grey |
| E2 | [File:Friedrich Engels (1891).jpg](https://commons.wikimedia.org/wiki/File:Friedrich_Engels_(1891).jpg), file `https://upload.wikimedia.org/wikipedia/commons/e/ed/Friedrich_Engels_%281891%29.jpg` | William Elliott Debenham (1839-1924), London, 1891 | `PD-old-70`: PD in Russia (died before 1952) and the EU (+70). In the US it is PD either way: published by 1895 at the latest, or unpublished with the author dead in 1924 | 993 × 1163, 207,124 B | The old, white-bearded Engels, the one most reproduced today. Head and shoulders. Next to M1 he looks a generation older than Marx, so it is the fallback |
| E3 | [File:Friedrich Engels 1888-2.2.1.jpg](https://commons.wikimedia.org/wiki/File:Friedrich_Engels_1888-2.2.1.jpg), file `https://upload.wikimedia.org/wikipedia/commons/d/d8/Friedrich_Engels_1888-2.2.1.jpg` | W. E. Debenham, 1888. Scan from the Mary Evans Picture Library, via *Die Welt* | `PD-Art\|PD-old-70` | 1731 × 2500, 434,141 B | The largest Engels scan. But the scan comes from a commercial picture library by way of a newspaper. Under PD-Art that is legally fine, but it is the weakest provenance of the three |

**Rejected, with the reason, so they are not proposed again:**
- `Karl Marx, 1875.jpg`: colourised by Olga Shirnina, **CC BY-SA 2.0**. The colourisation is licensed.
- `Friedrich Engels 111.jpg`: tagged **CC BY-SA 4.0** (a scan from a 1928 Swedish book). The tag contradicts the age of the photograph. Avoid it.
- Every `(colored)` / `colored portrait` Engels or Marx: derivative colourisations, with a modern contributor and no gain for four flat inks.
- `Friedrich Engels, c. 1860.jpg` (Amsler & Ruthardt) and `Friedrich Engels 1865-1.1.1A.jpg` (Silas Eastham): the young Engels, 15-20 years younger than M1's Marx. The first also comes by way of Getty Images.
- `Engels.jpg` (300 × 399), `Engels 91.jpg`, `Karl Marx crop.jpg` (363 × 545), `Karl marx nypl.jpg` (a re-photographed copy by Karl Pinkau): small or second-generation copies of M1, E1 and E2.
- `Karl Marx by John Jabez Edwin Mayall - Wien Museum.jpg` (3500 × 5624, 3.7 MB): the same Mayall sitting, dated only "1851-1900" on Commons. M1 is the documented scan of it.

## 3. The pair

**Recommendation: M1 + E1, Marx 1875 (Mayall) and Engels 1877 (Hall).**
- **The same moment.** Taken two years apart, of two men aged 57 and 56,
  in the London years of *Capital*, both in the formal studio dress of the
  1870s. Side by side they read as partners. With E2 (1891), Engels at 70
  would stand next to a Marx of 57.
- **Similar tone.** Both are studio portraits, so similar contrast. Cuts are
  percentiles of each crop, so a difference in exposure (E1's sepia) is
  levelled anyway.
- **Light: NOT VERIFIED.** The light, and which way each body turns, can only be
  checked on the downloaded plates. Commons says only that M1 is "looking at
  viewer"; it has no facing category for either. The rule for the pair: both
  face the viewer, or they turn **towards each other**, never away from
  each other. The generator covers every case:
  - `--swap` puts Engels on the left. It does not touch the likeness, so try
    it first.
  - `--mirror marx|engels` flips one portrait. A flip changes the likeness
    (hair, parting, beard), so it needs the CEO's eye.
- **Fallback:** E2 for Engels if E1's scan is too soft at 945 px. M2 for
  Marx if M1 shows retouching.

Total download for the recommended pair: **894,928 bytes** (380,651 +
514,277), two JPEGs.

## 4. Composition of `SDPOSTR4`

> **Superseded by §8.** The CEO chose neither layout below. He chose a
> **pair** of 128 × 256 posters, `SDPOSTR4` Marx and `SDPOSTR5` Engels, with
> the sentence split across the two bands. This section is kept as the
> record of the options.

`SDPOSTR4` is the name the commission and `level-designer` already use
(`tests/test_posters.py`, D106). `level-designer` has left **128 × 256 slots**
for it in every map, with a one-line swap. So the format is a real choice
with consequences, and the generator draws both options for the CEO to
compare by looking.

| Layout | Size | What it is | Cost |
|---|---|---|---|
| **`strips`, default and recommended** | **128 × 256**, Lenin's and Stalin's size | Two 64 × 210 portraits, each a tight head-and-beard crop, parted by a 2 px cream margin. Then the gold rule and the band | **None.** It is an allowed wall size (`check_pk3` `ALLOWED_WALL_SIZES`). It drops into the slots `level-designer` built today. Lenin and Stalin hang as its siblings. Trade-off: each head is about 55 px wide (the crop's aim, an estimate until the plates are seen), against ~85-95 px for Lenin's and Stalin's (measured on `SDPOSTR1/3`). Bearded heads stay readable at that size, NOT VERIFIED until the sweep |
| `side` | 256 × 256 | Two 128 × 210 portraits, each exactly Lenin's cell (head and shoulders), with the band running under both | Two contract changes: `(256, 256)` added to `tools/check_pk3.py` `ALLOWED_WALL_SIZES` and MOD-SPEC §2 (`mod-engineer`, one line each); and the slots made 256 wide (`level-designer`). Or, with no contract change, `--halves` cuts it into two 128 × 256 lumps (`SDPOSTR4` left, `SDPOSTR5` right). Hung on two adjacent 128-unit lines, they reassemble it pixel for pixel. That costs two slots per poster and risks a visible seam if the two lines differ in light |
| ~~overlapping profiles~~ | 128 × 256 | The Soviet "Marx-Engels-Lenin" stack of profiles | **Rejected.** Those profiles were drawn by artists. The Commons searches turned up no public-domain *profile* photograph of either man, only frontal and three-quarter portraits. Two overlapping three-quarter faces in four flat inks merge into one dark mass, and separating them would need a hand-traced mask, which is Lenin v3's mistake ("no se parece a él EN NADA", CEO: "it looks nothing like him") |

Common to both layouts, unchanged from `SDPOSTR1/3`:
- the four inks of `gen_lenin.inks()`;
- the 3 px cream border;
- the 1 px gold rule;
- the 46 px red band;
- the hard-cut slogan mask, so the band is exactly red, cream and gold.

Each portrait is cut with its own percentiles but the **same sweep cell**,
so the pair matches. Expected colours: four inks plus the gold, as `SDPOSTR3`.

**Recommendation: `strips`.** It is the twin the commission asked for and fits
what the maps already expect. If the CEO, looking at the preview sheet, finds
the 55 px heads too small, `side` is the answer, and it costs the two
contract lines above.

## 5. Slogan

Measured with this PC's Impact (`--slogans` sheet). Short phrases are not
protected by copyright (Lenin study). The Manifesto's line is from 1848, its
Russian form long public domain.

| Key | Slogan | `strips` (128) | `side` (256) | Note |
|---|---|---|---|---|
| `proletarii` **(proposed for `side`)** | «ПРОЛЕТАРИИ ВСЕХ СТРАН, / СОЕДИНЯЙТЕСЬ!» | does not fit | **19 px**, Lenin's | The closing line of the *Communist Manifesto* (1848), in its standard Russian form. It is the USSR's state motto, written on the state coat of arms, so in 1977 it is everywhere. The one slogan that *belongs* to these two men |
| `proletarii_3` **(proposed for `strips`)** | «ПРОЛЕТАРИИ / ВСЕХ СТРАН, / СОЕДИНЯЙТЕСЬ!» | **13 px** | 13 px | The same line in three lines. 13 px is the smallest stamp in the family: Stalin's three-line `spasibo` was 14. Legible on the sheet, tight |
| `proletarii_1` | one line | does not fit | 14 px | The same, as one line |
| `names` | «К. МАРКС / Ф. ЭНГЕЛЬС» | 19 px | 19 px | Names, the way Soviet portrait pairs were captioned. Useful for players who would not know Engels's face |
| `marxism` | «ДА ЗДРАВСТВУЕТ / МАРКСИЗМ-ЛЕНИНИЗМ!» | does not fit | 19 px | A stock banner line of the 1970s |

Recommendation: the Manifesto line, `proletarii_3` in `strips` or
`proletarii` in `side`. If the CEO finds 13 px too small in `strips`,
`names` is the 19 px alternative.

## 6. The generator, `tools/art/gen_marx_engels.py`

> **Superseded by §8.** The generator was rewritten for the approved pair.
> The `strips`/`side` layouts and the `--halves` option described below are
> gone.

It reuses `gen_lenin` and `gen_stalin` and edits neither:
- `gen_lenin.portrait` does the posterising. It is run with each
  photograph's path, crop, ink count and cell width patched in, and all four
  are always restored (a test enforces this, as for Stalin).
- `gen_stalin.fit_crop` gives an aspect-true crop at either cell width.
- `gen_stalin.to_lump` writes the indexed PNG.

New here: the two-portrait frame, and a slogan stamp that takes any width
(Stalin's, generalised). On the command line:

- **Photographs:** `work/art/reference/marx_1875.jpg` and
  `work/art/reference/engels_1877.jpg` (alternatives: `marx_1875s.png`,
  `engels_1891.jpg`, `engels_1888.jpg`; `--marx` / `--engels` choose).
  - If either is missing, the script stops with one message that names
    every missing file and its Commons page. It never downloads.
  - Every crop is **PROVISIONAL**: guessed from the plate size and the
    Commons description, to be set on the plates after download, as Stalin's
    was.
- **`--sweep`:** 3 ink counts × 5 cut points (cells 2A-4E, Lenin's layout).
  Both portraits are cut with the same cell. `--layout` chooses the layout.
- **`--preview`:** the CEO's single sheet: the sweep, then **both layouts**
  at the current cell with every slogan that fits.
- **`--slogans`:** the slogan sheet, which needs no photograph (already
  rendered on this PC to check the fits above).
- **Other options:** `--swap`, `--mirror`, `--halves` (`side` only).
- **Output names:** a plain run writes
  `work/art/marx_engels/marx_engels_<layout>_poster.png`, never a lump
  name, because `tests/test_art.py` matches `assets/` to `work/` by name.
  After approval the defaults are set to the CEO's cell, layout and slogan,
  and the plain run gets the lump name (as D55 did for Stalin).

Tests: `tests/test_gen_marx_engels.py` has 34 tests, all on synthetic plates
in a temp directory: no photograph, no write to `assets/` or `work/`. Two of
them (the sweep and preview sheets) skip under `SD_SKIP_SLOW_ART=1` and run
at the art tier. The suggested `tests/_tiers.py` entry for QA is
`test_gen_marx_engels.PipelineTests` ("render: two posters per layout,
~2 s"). It is not added here because that file is QA's.

Text-bearing asset (CLAUDE.md, D27): rendered on Windows from the start, so
it is regenerated only on Windows.

## 7. What the PM downloads, with the CEO's OK

The Stalin procedure (§5 there):
1. Make a new empty directory.
2. `curl` each file URL into it.
3. Check the format and size with `python -I`.
4. Move the files into place.
5. Record the SHA-256 and add a row to `docs/art/LICENSES.md`, under
   "Reference material held locally".

| Save as | From | Expected |
|---|---|---|
| `work/art/reference/marx_1875.jpg` | `https://upload.wikimedia.org/wikipedia/commons/d/d4/Karl_Marx_001.jpg` | JPEG, 1428 × 2048, 380,651 B |
| `work/art/reference/engels_1877.jpg` | `https://upload.wikimedia.org/wikipedia/commons/7/75/Friedrich_Engels_portrait.jpg` | JPEG, 945 × 1437, 514,277 B |

Total **894,928 bytes**. Fallbacks only if the first look fails:
- E2 `engels_1891.jpg`, 207,124 B;
- M2 `marx_1875s.png`, 1,376,570 B.

Then the art-director sets the two crops on the plates and checks which way
each man faces (§3). It renders `--preview` into `docs/art/previews/` for the
CEO, who picks:
1. the layout;
2. a cell;
3. a slogan.

## 8. Phase 2: the approved format, the plates, the sweep (2026-10-22)

### The CEO's format

A **pair of posters**, each the size and style of `SDPOSTR1/3` (128 × 256,
head at their scale, ~85-95 px wide), hung Marx on the left:

| Poster | Band |
|---|---|
| `SDPOSTR4`, Marx | «ПРОЛЕТАРИИ ВСЕХ / СТРАН,» |
| `SDPOSTR5`, Engels | «СОЕДИНЯЙТЕСЬ!» |

Hung together, the two bands read the Manifesto's line; each poster also
works on its own. Installed after the verdict below (D117).

### The downloads

The PM downloaded both photographs with the CEO's OK, from the file URLs in
§7. The art-director re-checked both hashes on disk.

| File | Source | Author, date | Licence | Format | SHA-256 |
|---|---|---|---|---|---|
| `work/art/reference/marx_1875.jpg` | https://commons.wikimedia.org/wiki/File:Karl_Marx_001.jpg (file `https://upload.wikimedia.org/wikipedia/commons/d/d4/Karl_Marx_001.jpg`) | J. J. E. Mayall's studio, London, before 24 August 1875; IISH scan | public domain (`PD-old-100-expired`; author died 1901) | JPEG, greyscale, 1428 × 2048, 380,651 B | `cc2fb87d222a2659a59496040805cb9911e16527f145edceb142cfe5954617c9` |
| `work/art/reference/engels_1877.jpg` | https://commons.wikimedia.org/wiki/File:Friedrich_Engels_portrait.jpg (file `https://upload.wikimedia.org/wikipedia/commons/7/75/Friedrich_Engels_portrait.jpg`) | William Hall, May 1877 | public domain (`PD-old-auto-expired`; author died c. 1898) | JPEG, RGB sepia, 945 × 1437, 514,277 B | `c7be6f45ed4f506a56735f2a451d7265f735eda1f8888c8029073c3c984fec31` |

The `docs/art/LICENSES.md` rows (the two reference photographs and the two
lumps) are written at install time.

### Seen on the plates

**Marx** faces the viewer: face frontal, body turned towards the left edge.
- Head, from the mane to the beard: x 0.42-0.78, y 0.17-0.43 of the plate.
- Crop `(0.60, 0.11, 0.66)` (centre x, top, bottom), aspect from
  `fit_crop`: x ~0.34-0.86. It runs from just above the mane down to the
  hand in the waistcoat.
- Head about 90 px wide on the poster, as Lenin's.

**Engels** is a three-quarter view **looking towards the right edge**.
- The print is an oval vignette on a card.
- Head, from the hair to the beard's tip: x 0.33-0.72, y 0.19-0.52.
- Crop `(0.53, 0.16, 0.66)`. It stays inside the oval, so no cream card
  shows in the corners.
- Head about 80-85 px wide.

**So, as photographed, Engels looks away from Marx.**
- Hung to Marx's right, the two turn their backs on each other.
- `MIRROR_ENGELS = True` flips Engels's portrait so the two face each other.
- **Marked for the CEO:** a flip changes the likeness (hair parting, beard
  asymmetry). The preview sheet shows the pair both ways.
- Swapping sides is not an option: the sentence fixes Marx on the left.

### Proposed cells

| Poster | Cell | Why |
|---|---|---|
| Marx | **4D** (four inks, cut +9) | At 4C the light studio wall left of his head becomes a cream field. One column darker, it drops to red and the mane and beard stand out |
| Engels | **4C** (four inks, cut +0), Lenin's and Stalin's cell | At 4D the face gets speckled with red |

Both are proposals; the CEO points at a cell in each sweep.

### The slogan

**One size for both bands.** The generator stamps both posters at the
largest size where every line of both fits. Measured with this PC's Impact:

| Split | Lines | Size |
|---|---|---|
| The CEO's split (default) | «ПРОЛЕТАРИИ ВСЕХ / СТРАН,» + «СОЕДИНЯЙТЕСЬ!» | **15 px** |
| Alternative `short` | «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» + «СОЕДИНЯЙТЕСЬ!» | **17 px**, 2 px larger |

Lenin's is 19 px. «СОЕДИНЯЙТЕСЬ!» on its own fits only at 17.

**Engels's line sits on the row of Marx's second line** (`align="pair"`), so
the sentence runs across both bands: «ПРОЛЕТАРИИ ВСЕХ / СТРАН, СОЕДИНЯЙТЕСЬ!».
- Alone, his word sits half a line below the band's centre.
- The alternative, `align="centre"`, centres it.

**The breve of Й is kept.** The stamp measures ink above the cap height.
Same hard-cut mask as Lenin and Stalin: each band is exactly red, cream and
gold.

### The preview

`docs/art/previews/2026-10-22_P4_marx-engels-sweep.png`, 2668 × 1992,
173,777 B. From top to bottom:
1. **The sweeps:** Marx's 15 cells, then Engels's 15 cells, mirrored as
   proposed.
2. **The pair as hung** at 4D + 4C, four ways:
   - as proposed (Engels mirrored);
   - Engels as photographed;
   - the `short` split;
   - bands centred.

The working copies are in `work/art/marx_engels/`:
- one sweep sheet per portrait;
- `marx_engels_marx_poster.png` and `marx_engels_engels_poster.png`, never
  under a lump's name.

### Generator and tests

`tools/art/gen_marx_engels.py` was rewritten for the pair. The same reuse
of `gen_lenin.poster` through `gen_stalin`'s patch-and-restore pipeline.

`tests/test_gen_marx_engels.py`: 36 tests.
- **Synthetic plates:** the bands' grid and shared size, the breve, the
  mirror, gen_lenin restored, no write to `assets/`, the clean stop without
  photographs.
- **Real plates:** the hashes above, every ink used in quantity, four inks
  plus the gold.

### The verdict (D117, 2026-10-22)

The CEO approved the proposal as drawn on the sheet:

| Question | Answer |
|---|---|
| Marx's cell | **4D** (four inks, cut +9) |
| Engels's cell | **4C** (four inks, cut +0) |
| Engels | **mirrored**, so he looks at Marx |
| Split | **`short`**: «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» + «СОЕДИНЯЙТЕСЬ!», **17 px** |
| Alignment | **`pair`**: Engels's word on the row of Marx's second line |

### Installed (2026-10-22)

- **Generator.** `tools/art/gen_marx_engels.py`'s defaults are the verdict
  (`DEFAULT_SPLIT = "short"`, `MIRROR_ENGELS = True`, cells 4D and 4C). A
  plain run writes `work/art/marx_engels/SDPOSTR4.png` and `SDPOSTR5.png`;
  any other option writes `marx_engels_<person>_poster.png`, never a lump's
  name. `lump(person)` returns the approved lump.
- **Lumps.** Both copied byte for byte into `assets/textures/soviet_base/`:
  indexed PNG, 128 × 256, five colours each (four inks plus the gold), all
  in palette v1.

  | Lump | Bytes | SHA-256 |
  |---|---|---|
  | `SDPOSTR4` | 3,189 | `f4d6a48251346d32fed255e4afa3b2f2a89b4f0e82496680b9c34cb5d750d5f2` |
  | `SDPOSTR5` | 3,535 | `b7062f3b2689df644a7e30e71d0cfcbe583ed17eea799eec2edb15a239d5f81f` |

- **Text-bearing (D27).** Rendered with this Windows PC's Impact, so they
  are regenerated only here. `tests/test_gen_marx_engels.py`
  (`InstalledLumpIdentityTests`, Windows only, needs the two photographs)
  holds the generator to the installed pixels; `tests/test_art.py` holds the
  byte-for-byte copy.
- **Registers.** `docs/art/TEXTURE-INDEX.md` has the two rows (with the
  placement); `docs/art/LICENSES.md` has the two lumps (Engels's flip noted)
  and the two reference photographs (author, date, Commons URL, public
  domain, SHA-256).
- **Hung on every map.** Each map's two `POSTER_SLOTS_MARX_ENGELS` carry the
  pair, Marx's slot first; where both slots share a wall (MAP05, MAP07,
  MAP08) Marx is on the left as the wall is seen from the room, so the
  sentence reads left to right; elsewhere each poster reads alone, Marx
  first along the route. The table is `PAIR` in `tests/test_posters.py`;
  each map's design document (posters section) says where and why.

## Sources

- Commons API metadata (imageinfo, extmetadata, categories, wikitext, upload log) for every file above, 2026-10-22
- https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Russia
- https://commons.wikimedia.org/wiki/Category:Karl_Marx_in_1875
- https://commons.wikimedia.org/wiki/Category:Friedrich_Engels_in_1877
- https://commons.wikimedia.org/wiki/Category:Friedrich_Engels_in_1891
- https://commons.wikimedia.org/wiki/File:Karl_Marx_by_Mayall_c1870.jpg (the attribution to John Mayall junior, letter of 25 August 1875)
- `docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md`, `docs/product/2026-10-14_1556_F2_stalin-poster-sourcing.md`
- `tests/test_posters.py` (the `SDPOSTR4` slots, 128 × 256)
