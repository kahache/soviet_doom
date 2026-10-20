# Soviet Doom — Art Bible v0

Living document. Owner: `art-director`. Russian mirror: `docs/ru/art/ART-BIBLE.md`.
Status: **v0.2, 2026-10-13.** With the verdict on texture batch 1
(2026-10-12) the CEO ratified the palette (§3) and the fonts (§7); batch 1
stands at **12 of 12 approved** since the CEO walked MAP01 v1 on
2026-10-13 and approved `SDCONC2` and `SDSTAR1` v5 in the map, the
four switch variants of batch 2 (8 lumps) were approved on 2026-10-13, and so
were the four props of batch 3 (crates in column C, locker in column D): 24
texture and flat lumps in `assets/`. Per-lump
status is owned by `TEXTURE-INDEX.md`. Everything else here is still the art
director's proposal until the batch that exercises it is approved.
Product facts (era, factions, tone) come from `docs/PRD.md` and
`docs/product/LORE.md` and are not repeated here.

## 1. Visual direction in one paragraph

A **secret Soviet cosmodrome in the 1970s** (Zarya-7), built of prefab
concrete and painted steel, dressed with the paraphernalia of a state that
believes in itself: red stars, slogans, constructivist posters of Lenin,
pride in cosmonautics. It is not a ruin and not a cartoon: the base was clean
and in use the day before the invasion. Dirt is **use** (grime under joints,
chipped paint on rivets, worn floor lines), never decay. The invaders bring
their own look later (F5); the world they invade must read as *ours*.

Keywords from the lore: concrete, military green, propaganda, red star,
Lenin, cosmonautics, barracks, hangar, serious.

Reference tone (described, not copied): late-Brezhnev institutional
architecture (prefab panels, painted dados, fluorescent tubes), 4BO green
military hardware, 1920s constructivist posters (Rodchenko, Klutsis: flat
colour, diagonals, photomontage — which is how the Lenin poster was finally
made, a posterised photograph rather than a traced silhouette), 1960s-70s space
posters ("Слава советской космонавтике"). Doom's own language stays: 64/128
grids, hard pixels, mid-grey walls, light that drops towards black.

## 2. Format rules (binding for every asset)

| Rule | Value | Why |
|---|---|---|
| Colour | indexed PNG, **≤ 256 colours**, from `docs/art/palette.json` only | Doom look, one coherent palette across sets, software renderer safe |
| Wall textures | 64×64, 64×128, 128×64, 128×128 or **128×256** (multiples of 8) | Doom's grid; the level designer aligns on 64. 128×256 was added 2026-10-12 for the Lenin poster: at 128×128 the portrait had no room (CEO) |
| Flats (floor/ceiling) | 64×64 | engine flat size |
| Sprites | PNG with `grAb` offsets, name `XXXXA1` (4 letters + frame + rotation) | engine sprite naming (F4/F5) |
| Lump names | ≤ 8 chars, UPPERCASE, prefix `SD` + family code + number | contract with `level-designer` (`TEXTURE-INDEX.md`) |
| Quantisation | no dithering; fine grain added *before* quantising | flat deliberate pixels, no JPEG-like noise at 4× |
| Tiling | every wall/flat tiles unless its index entry says "no tile" (doors, posters) | checked visually on the 2×2 view of every preview |
| Origin | every texture declares (a) script + seed, (b) free pack + licence, or (c) CEO material | no origin, no texture (`LICENSES.md`) |

**Exception to the `SD` prefix: the engine actors' sprites (D82,
2026-10-20).** Seven sprites of the player-effects set ship under the
IWAD's own names, `PUFF`, `BLUD`, `TFOG`, `IFOG`, `BAR1`, `BEXP` and
`COLU` (`assets/sprites/effects/`), so the engine's puff, blood, fogs,
barrel and floor lamp draw our pictures without a replacing class. Each is
the complete set Freedoom ships under that name, every frame in rotation 0,
so no Freedoom frame is left to mix in; a new drawing for one of these
names must keep exactly that lump set. Every other sprite keeps the `SD`
prefix. Engine side: `docs/engine/MOD-SPEC.md` §1 and §5.1.

**Exception to the indexed-PNG rule: assets drawn over something else
(recorded 2026-10-13).** Two families of shipped files are **RGBA PNG**, not
indexed, because they need transparency: the menu logo `M_DOOM` (its row in
`LICENSES.md`) and the two folder fonts, `fonts/defsmallfont/` and
`fonts/bigfont/` (224 glyphs, D24 and D37, `tools/art/gen_font.py`). The rest of
the colour rule still binds them: every opaque pixel is a `palette.json`
colour and alpha is hard 0/255, never semitransparent. For the glyphs this
is enforced by `tests/test_gen_font.py` (`InstalledGlyphPaletteTests`).

- **Known: the engine admits it.** GZDoom g4.14.2 on Freedoom draws the
  installed RGBA glyphs
  (`docs/qa/evidence/2026-10-13_1007_F2_mainmenu-ru.png`,
  `docs/qa/evidence/2026-10-13_1020_F2_language-screen-ru.png`, macOS,
  hardware renderer).
- **NOT VERIFIED: that the engine requires it.** No indexed PNG with a
  transparent palette index has been tried as a folder-font glyph, and the
  software renderer has not been looked at. Converting the glyphs would
  change shipped bytes and needs an engine pass first, so RGBA stays the
  format until someone measures the alternative.

Family codes used so far: `CONC` concrete, `STEL` steel plate, `DOOR` door,
`POSTR` poster, `STAR` emblem, `FLR` floor, `CEIL` ceiling, `SW` switch
(`SDSW1x` off / `SDSW2x` on, Doom's own 1/2 convention, variant letter last;
added 2026-10-13 with batch 2), and with batch 3 (props, approved
2026-10-13) `CRAT` crate face, `CRTOP` crate lid (flat), `LOCK` locker; the
64×64 and 128×64 wall sizes arrived in `assets/` with the crates. New families are added here before the lump
exists.

**Added 2026-10-14 with the factory set «Танкоград» (D66).**

- **Wall size 256×64**, for the works banner `SDSLOG1`: one slogan in two
  lines of our alphabet at 2× needs the width, and 64 high keeps it a frieze.
  `tools/check_pk3.py` (`ALLOWED_WALL_SIZES`) accepts it; `tests/test_art.py`
  (`WALL_SIZES`) does not yet, so `SDSLOG1` waits in `work/`.
- **A masked wall texture in RGBA:** `SDCHAN1` (hanging chain and hook, a
  two-sided line's mid-texture) joins the exception above for assets drawn
  over something else: RGBA, hard 0/255 alpha, every opaque pixel a
  `palette.json` colour (`tests/test_gen_factory.py`). NOT VERIFIED in the
  engine as a mid-texture (D26). Not installed yet: `tools/check_pk3.py` and
  `tests/test_art.py` still require indexed PNGs under `textures/`.
- **Family codes:** `BRCK` brick, `RUST` corrugated rusted sheet, `CHAN`
  chain (masked), `GRAT` grating (flat), `MOLT` molten metal (flat,
  animated), `PORT` portal (animated), `GATE` factory gate, `WIND` window,
  `SLOG` slogan banner, `FLAG` faction banner; `DOORY` / `DOORR` are `DOOR`
  with the key colour as the last letter. Animated families number their
  frames 1-4 (`SDMOLT1-4`, `SDPORT1-4`), declared in `ANIMDEFS` by
  `mod-engineer`.

## 3. Palette (`docs/art/palette.json`, generated by `tools/art/palette.py`)

**Current version: v2 (2026-10-14, D45).** v1 was **ratified by the CEO
2026-10-12** ("Palette OK" in the batch-1 verdict) and its 162 colours are
frozen: later sets only *add* ramps in the reserved slots (new palette
version), never edit an existing colour.

| Version | Date | Decision | Colours | What it adds |
|---|---|---|---|---|
| v1 | 2026-10-12 | ratified by the CEO (batch-1 verdict) | 162 (slots 0-161) | the nine ramps below, true black and white |
| v2 | 2026-10-14 | D45 | 226 (slots 0-225) | `marble_red`, `mosaic_cobalt`, `mosaic_gold`, `flesh_pink` (16 each, slots 162-225) |

v1 is 162 colours in 9 ramps of 16 (32 for concrete) plus true black and
white. Ramps interpolate with gamma 1.8 so the dark half keeps usable tones
where Doom lighting lives (sector light 96-160). v2 appends four ramps built
with the same rule; 30 slots stay reserved (the industrial set, MAP03).

| Ramp | Role | Why it is in the palette |
|---|---|---|
| `concrete_cold` (32) | walls, floors, ceilings of the base | the dominant material; slightly blue so the greens and reds pop against it |
| `plaster_warm` | whitewash, poster paper, warm floor tiles | breaks the cold monotony; cream of propaganda typography |
| `military_green` | doors, riveted plates, crates | 4BO Soviet hardware green, the second identity colour |
| `flag_red` | stars, stripes, poster grounds | the first identity colour; top of the ramp is painted signage red, not orange |
| `cream_yellow` | aged paper, lamp light | lamps and posters share it so lit rooms and posters feel of one world |
| `hazard_yellow` | floor lines, hazard stripes, gold of the emblem | industrial accent; also the hammer and sickle |
| `steel_blue` | bare steel, rivets, pipes, chrome | reads apart from concrete; later the Liberty Legion's chrome |
| `rust_brown` | rust, grime, wood | sparingly in the base; the industrial set's main colour (MAP03) |
| `khaki_olive` | uniforms, faded paint | bridges green and cream; reserved for Reich flesh tones (see §6), with one CEO-approved exception in the world: the batch-3 crates (§6.2) |

**Added in v2 (D45, CEO 2026-10-14: "sí" / "ok"):**

| Ramp | Role | Why it is in the palette |
|---|---|---|
| `marble_red` | the metro's red marble cladding | warmer and browner than `flag_red` (HSV saturation ~0.67 against ~0.81) so a marble wall reads as stone, not as a painted stripe; far more saturated than `flesh_pink` (~0.26), so a Legion face does not sink into it |
| `mosaic_cobalt` | the blue ground of the metro mosaics | a true cobalt; v1's only blue, `steel_blue`, is a grey-blue and stays the Legion's chrome |
| `mosaic_gold` | the gold smalt of the mosaics | warmer and less saturated (~0.70) than `hazard_yellow`'s paint (~0.84), so a gilded star reads as metal leaf |
| `flesh_pink` | Liberty Legion flesh (F5) | the candidate ramp the Legion drafts were drawn with (`tools/art/gen_legion.py`, endpoints (24,10,10) to (242,190,180)), taken unchanged |

"Cobalt and gold" is two ramps, not one: a single gamma ramp from blue to
gold passes through grey-green in the middle and serves neither.

**How the versions coexist (binding).**

- **v1 is the exact prefix of v2, index for index.** Every v1 PNG is a valid
  v2 PNG; no v1 colour moved.
- **An approved texture keeps the version it was approved in.** Approving
  v2 did not requantise anything: every lump in `assets/` is v1 and stays
  byte-identical. A texture moves to v2 only as a new proposal that the CEO
  approves, which then replaces the file under the same lump name.
- **`palette.json`'s top-level `colours` / `ramps` / `index` / `count` are
  still v1**, on purpose: they are what `tools/art/artlib.py` quantises to
  and what `tools/check_pk3.py` checks, so regenerating a v1 texture can
  never pick up a v2 colour. v2 is in `colours_v2`, `added_ramps` and
  `added_index`; a generator opts in explicitly with `palette.colours(2)`
  and `palette.ramp_colours(name)` (`tools/art/palette.py`). When the first
  v2 texture is approved, `check_pk3.py` must accept v2 for it and the
  asset is listed in `APPROVED_IN_V2` (`tests/test_palette_v2.py`).
- Enforced by `tests/test_palette_v2.py`: the v1 digest, v1 as the prefix
  of v2, the ramp rule, the flesh ramp equal to the Legion's candidate, and
  every PNG in `assets/` inside the version it was approved in.

First use: the v2 proposals `SDMARB1_v2` and `SDMOSA1_v2` (same seeds and
geometry as the approved D42 lumps, new inks only), sheet
`docs/art/previews/2026-10-14_1036_F3_metro-palette-v2.html`, rows in
`TEXTURE-INDEX.md`. Pending the CEO's choice per piece.

**v2 in the factory set (D66, 2026-10-14).** The CEO approved the factory
«Танкоград» with palette v2 where `tools/art/gen_factory.py`
(`PALETTE_VERSION`, `PALETTE_WHY`) asks for it: the brick `SDBRCK1` /
`SDBRCK2` in `marble_red` (v1 has no fired-clay red), the two banners
`SDFLAG1` / `SDFLAG2` hung on that brick (`SDFLAG2`'s canton in
`mosaic_cobalt`, since v1's `steel_blue` reads slate at banner size) and the
portal `SDPORT1-4` in `mosaic_cobalt` with white filaments (nothing in the
world may share its colour). Drawn in v2 from the start, not requantised
approved art. Listed in `APPROVED_IN_V2` (`tests/test_palette_v2.py`) and
in `PALETTE_V2_LUMPS` (`tools/check_pk3.py`); every other factory lump is v1.

## 4. Sets

| Set | Map | Materials | Keywords | Sector light (proposal) |
|---|---|---|---|---|
| **Soviet base** (batch 1) | MAP01 Zarya-7 | prefab concrete, green steel, bunker doors, posters, hangar floor, lamp ceilings | cosmodrome, barracks, hangar, 1970s, propaganda | corridors 112-144 · barracks 128-160 · hangar 160-192 under lamps · night exteriors 96-128 |
| Metro | MAP02 | glazed tiles, red marble, mosaics, brass | tunnels, bunker, grandeur underground | 96-128, bright islands 160 at stations |
| Industry | MAP03 | brick, rust, chains, tank hulls | factory, portal, climax | 80-128, forge/portal glow 176-208 |

Light ranges are the art director's proposal for the look (mid-grey walls at
light 144 look like Doom's); the `level-designer` owns the final values and
**NOT VERIFIED in-engine yet**: the first MAP01 build will calibrate them.

### Soviet base — batch 1 (12 textures; CEO verdict 2026-10-12)

Walls: `SDCONC1` prefab concrete, `SDCONC2` concrete + red stripe, `SDSTAR1`
concrete + emblem plaque, `SDSTEL1` green riveted steel, `SDDOOR1` bunker
door (128×128), `SDPOSTR1` Lenin poster (128×256), `SDPOSTR2` cosmonautics
mural (128×128). Flats: `SDFLR1` hangar floor with lane line, `SDFLR2` plain
hangar floor, `SDFLR3` grey tiles, `SDCEIL1` ceiling with lamp, `SDCEIL2`
plain ceiling. Full data in `TEXTURE-INDEX.md`; preview in
`docs/art/previews/`.

Where it stands (2026-10-13): **12 of 12 approved.** Ten on the sheet —
`SDCONC1`, `SDSTEL1`, `SDDOOR1`, the three floors, the two ceilings (the 8
unconditional ones), `SDPOSTR2` (the CEO confirmed its Russian text on
2026-10-12) and `SDPOSTR1` v4, the Lenin poster posterised from the
public-domain 1920 photograph, chosen by the CEO from a 15-cell sweep on
2026-10-12 and approved at 128×256 (the format was widened for it, §2) —
and **two in the map**, judged by the CEO walking MAP01 v1 in GZDoom on
2026-10-13 (~15:40): `SDCONC2`, the red stripe, approved as built with the
hangar's three bands («no queda perfecto pero yo lo dejaría así, le da color y relleno las 3 bandas»), which
also makes a separate 128-high hangar dado unnecessary as an alternative to
it; and `SDSTAR1` v5, the emblem plaque (variant D1, after v2 mirrored the
emblem and v3-v4 corrected it): «la apruebo, preciosa». `SDFLR1` received a 44-pixel seam repair on 2026-10-13
(details in the index). The approved core (concrete, steel, door, floors,
ceilings) is enough for the `level-designer` to build MAP01's first rooms;
the stripe, the plaque and the posters are accents and can land later
without changing the set.

### Soviet base — batch 2, switches (8 lumps; CEO 2026-10-13)

`SDSW1A-D` (off) / `SDSW2A-D` (on), 64×128, one wall segment on the 64 grid.
Four variants were swept and the CEO took all four for variety ("yo por mí
mete todos, así tenemos diversidad"): A rubilnik on a bakelite board, B domed
push button, C lens over a slide lever, D hazard-bordered master switch. Rows,
seeds and the sweep sheet in `TEXTURE-INDEX.md`; origin and licence in
`LICENSES.md`. The direction finding the sweep produced (value survives
sector light, hue does not; the live state rides on a cream lens, never on
red) is recorded in `LICENSES.md` with the batch and measured in
`tools/art/gen_switch.py`; §5 and §6.3 already asked for it.

### Soviet base — batch 3, props (4 lumps; CEO 2026-10-13)

`SDCRAT1` crate face (64×64), `SDCRAT2` long crate (128×64), `SDCRTOP1`
crate lid (flat) and `SDLOCK1` barracks locker (64×128), for MAP01 v2
(`level-designer`'s request A5). A sweep of four value families; the CEO
took column C for the three crate pieces and D for the locker, as drawn:
«apruebo el arreglo de la fuente y cajas C y D». The crates are khaki
planks with a diagonal brace and stencilled numbers (mean luma ~123, between
`SDSTEL1` at 101 and `SDCONC1` at ~146, so they separate from both walls);
the locker is pale pine with black straps. The colour of the crates is an
exception to the khaki reservation, recorded in §6.2. No typeface in any of
the four: stencils are segment data, so they reproduce on both machines.
Rows, seeds and the sweep sheet in `TEXTURE-INDEX.md`.

Composition rules for the set:

- Concrete is the canvas: 70 % or more of any room. Green steel marks
  *function* (hangar, machinery, doors). Red marks *meaning* (stripe = a
  corridor you follow, plaque/poster = a place that matters).
- Posters are the loudest surfaces in the game: at most one per 256 map
  units of wall in a combat space; they belong at eye height on concrete,
  never on steel.
- `SDFLR1`'s yellow line is continuous when tiled: the level designer lays
  it in lanes (hangar bays, routes to doors), not as a carpet.
- `SDCEIL1` (lamp) is placed where the sector light says there is a lamp;
  elsewhere `SDCEIL2`. One lamp flat ≈ one 64×64 light source.

## 5. Light and contrast

- Doom shades by sector light towards black. Textures are authored for light
  **144** (the preview is "light 256"); the ramps guarantee they still read
  at 96.
- No texture has flat black areas larger than an 8-px blob: pure black is for
  outlines and the deepest groove only. Large black kills silhouettes.
- Floors sit one notch darker than walls (`FLOOR_MID` 0.52 vs `CONCRETE_MID`
  0.58) and ceilings one notch lighter (0.66), so a room has a vertical
  gradient even at uniform sector light.

## 6. Enemy legibility (rules for F5, stated now so walls obey them)

1. **Value first.** Enemy body mass must sit ≥ 2 ramp steps darker *or*
   lighter than the mid-grey of concrete (ramp 0.58). Walls therefore stay in
   the 0.45-0.70 band; nothing in the set is as dark as a Reich uniform or
   as bright as Legion chrome.
2. **Hue ownership.** `military_green` belongs to the *world* (doors,
   plates). Fourth Reich flesh uses `khaki_olive` + black, never
   `military_green`, so a brute in front of `SDSTEL1` still separates.
   **Exception approved by the CEO, 2026-10-13:** the batch-3 crates
   (`SDCRAT1`, `SDCRAT2`, `SDCRTOP1`) are painted in `khaki_olive`. The
   CEO approved column C as drawn («apruebo el arreglo de la fuente y cajas
   C y D»), which closes the question of khaki versus brown wood: the
   crates stay khaki. **Watch item for F5:** when the Reich's sprites are
   drawn, check on the legibility sheet that a Reich figure does not blend
   into a stack of crates (the hangar's cover is exactly where fights
   happen); if it does, the fix goes on the sprite's value (§6.1) and its
   black, not on the approved crates.
   Liberty Legion uses the `flesh_pink` ramp (in palette v2 since D45, §3) +
   `steel_blue` highlights; no wall uses `steel_blue` above ramp 0.5 in
   large areas.
3. **Accent exclusivity.** Swastika armbands and US flags (D12) are the only
   places where saturated red/white/blue sit on an enemy; walls keep red to
   stripes, plaques and posters so an enemy's accent is never camouflaged.
4. **Silhouette over detail.** Every enemy must be identifiable as a
   16-px-tall black silhouette; the texture detail frequency (plates, joints)
   is kept below that scale so it does not read as a figure.

## 7. Pipeline

```
.venv/bin/python tools/art/palette.py          # -> docs/art/palette.json
.venv/bin/python tools/art/gen_soviet_base.py  # -> work/art/batch1/soviet_base/*.png + manifest.json
.venv/bin/python tools/art/gen_switch.py       # -> work/art/batch2/switch/*.png + sweep sheet EN/RU
.venv/bin/python tools/art/gen_props.py        # -> work/art/batch3/props/*.png + sweep sheet EN/RU
.venv/bin/python tools/art/make_preview.py --stamp YYYY-MM-DD_HHMM
                                               # -> docs/art/previews/ + docs/ru/art/previews/
```

(On Windows the interpreter is `.venv/Scripts/python.exe`; `CLAUDE.md`.)

`work/` is gitignored. The CEO answers in chat; approved PNGs are copied to
`assets/textures/<set>/` or `assets/flats/<set>/` and their index row turns
"approved"; discarded ones keep their row with the reason. Shared helpers
live in `tools/art/artlib.py` (tileable noise, palette quantisation,
supersampled vector overlays, wrapped strokes, seam metric).

**Regeneration rule (2026-10-13): an approved asset is regenerated only on
the machine that rendered it, or it goes back to the CEO as a new proposal.**
The generators are deterministic per machine, not across machines: the
text-bearing lumps (`SDDOOR1`, `SDPOSTR2`, the eight switches) do not come
out byte-identical on Windows and on the Mac because the two rasterise
Impact differently; the nine text-free lumps of batch 1 do (`SDPOSTR1`, whose
slogan is Impact too, was not measured). The measurement is in
`CLAUDE.md` ("Text-bearing assets do not reproduce across the two
machines"). Everything in `assets/` was rendered on the Mac except what
was approved on 2026-10-13 from the Windows PC: the four batch-3 props and
the six corrected glyphs of the alphabet. None of those uses a system font,
so they reproduce byte for byte on both machines.

Cyrillic lettering: the system fonts Impact (headlines) and Arial Narrow
Bold (small text), resolved per machine by `tools/art/artlib.py` and
rasterised into the textures; see `LICENSES.md`.
**Ratified by the CEO 2026-10-12** ("Fonts OK" in the batch-1 verdict): the
two fonts stay the lettering of the mod unless `qa-engineer` raises the
licence point in `LICENSES.md`.

Extra tools of the pipeline: `tools/art/make_contact.py` (contact sheet of
the batch for a quick look in chat, `work/art/batch1/contact.png`) and
`tools/art/emblem_check.py` (the hammer-and-sickle check sheet,
`work/art/batch1/emblem_check.png`, with the CEO's reference circles and
points overlaid on the drawing).

## 8. Open questions for the CEO (batch 1)

1. **Lenin — separate commission (CEO, 2026-10-12). CLOSED the same day.**
   `SDPOSTR1` v1 (geometric silhouette in a medallion) was discarded: "we'll
   have to see how to do Lenin right, we'll work on it separately". It was
   handled as its own task with a public-domain 1920 photograph as source
   (`LICENSES.md`); the CEO picked cell 4C of a 15-cell posterisation sweep
   and the result ships as `SDPOSTR1` at 128×256 (`TEXTURE-INDEX.md`).
2. Poster formats — **answered 2026-10-12**: the portrait went to 128×256
   because at 128×128 the face had no room (CEO); the mural stays 128×128.
   Both formats are in the index, so the level designer has both.
3. Slogans: «ЛЕНИН ЖИВ» (`SDPOSTR1`) and «СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ»
   (`SDPOSTR2`; the CEO confirmed the wording on 2026-10-12) used; «ПУСК» on
   the switches; alternates available («СЛАВА КПСС», «МИРУ — МИР», «ВПЕРЁД,
   К ЗВЁЗДАМ!»).

Nothing is open from batch 1: the two in-map verdicts (`SDCONC2`,
`SDSTAR1`) were given on 2026-10-13 while the CEO walked MAP01 v1 (§4).
