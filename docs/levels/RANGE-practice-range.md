# RANGE — the practice range

> **D62 (2026-10-14): the map lump is `RANGE`, out of the MAPxx slots**,
> which follow the campaign (MAP02 is the metro now). The range was
> `MAP02` until then; dated evidence and the records below keep that name
> where they quote a run.

Design document. Owner: `level-designer`. Source: `src/maps/RANGE/map.py`;
tests: `tests/test_range_map.py` (the map) and
`tests/test_practice_range.py` (`mod-engineer`'s: how MAPINFO and MENUDEF
reach and leave it). Russian mirror: owed (D34), at the same path under
`docs/ru/`.

Status, 2026-10-13: **v1 BUILT and seen in the engine** the same evening:
P1-P3, P5 and P6 pass, P4 not exercised
(`docs/qa/evidence/2026-10-13_2057_map02-range-and-c12.md`; checklist in §7).

Status, 2026-10-19: **M2d retexture BUILT, not yet seen in the engine.**
Every Freedoom wall texture and flat is gone (the M2 audit's item A4,
`docs/qa/2026-10-14_2357_M2-freedoom-audit.md` §5): the range now wears
the Zarya-7 base set only, §5. Geometry, things, tags, specials and both
`tools/route.py` routes (`range-start`, `range-door`) are unchanged: the
generated TEXTMAP differs from the v1 one only in texture names and two
`offsetx` values. Engine look: P8-P10 in §7, the PM's batch (D26).

## 1. Synopsis

A firing range and a bestiary: every weapon of the arsenal within a few
steps of the start, targets to shoot them at, and behind a door one of
each enemy, asleep, to meet one at a time.

## 2. Where it comes from

The range was built in F4 by `mod-engineer` as an engineering fixture (prove
each weapon can be picked up, fired and made to do damage), and grew a
bestiary gallery in F5. Neither had a design document: it was a test bench,
not a level. **D41** (`docs/PRD.md`) ships it to players as a practice
range, a second episode on New Game (`docs/engine/adr/007-practice-range-as-a-second-episode.md`;
contract in `docs/engine/MOD-SPEC.md` §4.4). ADR 007 left two things to
this role: the range had **no exit line**, so a player could leave only through
the menu; and the gallery was **connected to nothing**, reached only with
the console (`warp 1024 1152`). This document is v1: the range made
player-facing. What F4 and F5 built is kept as it was.

## 3. Plan

```
y 1792 +----------------------------------------------------------------+
       |  BESTIARY GALLERY   ceiling 256, light 192   [ME] Lenin Stalin [ME] |
y 1600 |   Ri   Le   St   Hd   Db   Pz   PzS  Gn    (row, facing north)  |
       |                                                                 |
y 1152 |                         * arrival (1024, 1152)                  |
y 1024 +-----------------------------+ mouth +---------------------------+
                                     |   B   |  x 960-1088
y  960           +-------------------+       |
                 |   C  cross passage, ceiling 128, light 160
y  896           +-------+-------------------+
                         |   A   |  x 640-768
y  832                   +=DOOR==+  tag 1, Door_Raise, SDDOOR1 both faces
y  768 +-----------------+-------+-----------------------------------------+
       |      weapon row y 624: axe TT-33 IZh PPSh RPG-7 ROKS-3 Katyusha   |
   EXIT|  @ start (160, 384) facing east     barrels      targets (3004)    |
 (-32) |      ammo row y 144                                               |
y    0 +-------------------------------------------------------------------+
       x 0                                                         x 2048
```

| Zone (sector name) | Rectangle(s) | Floor / ceiling | Light | What it is |
|---|---|---|---|---|
| `hall` | 0,0 – 2048,768 | 0 / 128 | 192 | F4's range, unchanged |
| `exit_alcove` | -32,352 – 0,416 | 0 / 128 | 224 | **new:** the way out, behind the start |
| `gallery_door` | 640,768 – 768,832 | 0 / 0 (closed) | 160 | **new:** the gallery door, tag 1 |
| `gallery_passage` | A 640,832 – 768,896; C 640,896 – 1088,960; B 960,960 – 1088,1024 | 0 / 128 | 160 | **new:** a dog-leg, one sector painted as three rectangles |
| `gallery` | 0,1024 – 2048,1792 | 0 / 256 | 192 | F5's gallery; 192 high until the posters (2026-10-22, §5.1) |

5 sectors, 36 lines, 39 things (F5: 2 sectors, 8 lines, 39 things; 26 lines before
the posters split five wall runs, §5.1).

## 4. The two v1 changes

### 4.1 The exit

A lit alcove in the hall's west wall, on the start's row, straight behind
the player: he spawns facing the targets, and when he is done he turns
round and the way out is there. The switch is **`SDSW1D`, the hazard
panel**, the face MAP01 already taught as its exit, whole (64 wide, 128
high) on the alcove's back wall, with steel jambs (`SDSTEL1`) and the lamp
panel `SDCEIL1` over it at light 224, a step over the hall's 192. Its
special is **`Exit_Normal`** (243), pressed (`playeruse`), never walked
over: a range is not left by stepping in the wrong place. MAPINFO does the
rest (`mod-engineer`'s, unchanged): cluster 2, `next = endtitle`, so the
switch shows `SD_END02_TEXT` over `SDFLR1` and returns to the title.

The alcove is 32 deep: the switch can be pressed from the hall's edge
without entering it (48 from a body touching the wall, inside Doom's 64).

### 4.2 The gallery, on foot — reachable, and why

**Decision: reachable.** The case for keeping it hidden was that it was
built as a PM's fixture. The case for opening it is stronger:

- **D41 ships the range to players.** A room full of enemies that only the
  console reaches is a fixture inside the product; a player who never opens
  the console never knows it is there.
- **It is the practice the range is for.** The hall teaches the guns; the
  gallery lets a player meet each of the eight enemy classes one at a time,
  asleep, with every weapon already in hand. That is what a *practice*
  range adds to a campaign that throws them at him in groups.
- **It costs one door and a bend**, and the console's `warp 1024 1152`
  still works for the PM.

How it is done:

- **A manual door** in the hall's north wall at x 640–768, beside the
  weapon row (between the RPG-7 and the ROKS-3, 144 north of them), so the
  player arms himself on the way to it. `Door_Raise` on both faces, each
  wound with the door behind it (ZDoom fires a use special from the front
  only), leaf `SDDOOR1` (exactly one 128 tile), track `SDSTEL1`: the door
  as MAP01 taught it. It rises to 124 and closes after 150 tics. Monsters
  cannot open it (no `monsteruse`), so it is also a retreat.
- **A dog-leg passage**: north 64, east along a cross passage, north again
  into the gallery's south wall at x 960–1088, centred on the old arrival
  point. The bend is the point. F5's gallery shared no line with the hall
  "so that nothing fired in the arsenal range is heard or seen". A door
  lets sound through while it is open, and a deaf (`ambush`) monster that
  hears a shot still wakes if it can **see** the shooter (Doom's `A_Look`
  sight check on a sound target; NOT VERIFIED in GZDoom's source by this
  role, and made moot by the bend). With the bend no straight line joins
  the two mouths: it would have to cross 576 units in x over the passage's
  192 of depth, and the mouths span 448. So the hall's gunfire never wakes
  the gallery, open door or not.
- **The mouth is behind the row.** The eight enemies face north (90), the
  passage comes out 576 units south of them: a player walks in on their
  backs, chooses the first, and wakes the others by shooting near them, not
  by arriving.

### 4.3 What did not change

The hall's things and positions (F4), the gallery's row and spacing (F5),
the IWAD look (`STARTAN2`, `FLOOR4_8`, `CEIL3_5`, MOD-SPEC §5; replaced
in M2d, §5), the `ambush` flag on every target and enemy, the light of both rooms. Every
thing is on every skill: skill changes what the engine's rungs change
(damage taken, ammo given), not what is placed. No secrets, no keys.
`tools/route.py`'s `range-start` walk (north up x 288 onto the ice axe) is
still one sector from start to pickup.

## 5. Textures by zone

**M2d (2026-10-19): the Zarya-7 base set, no IWAD name left.** Until M2d
the hall, gallery and passage wore Freedoom's `STARTAN2`, `FLOOR4_8` and
`CEIL3_5` (the F4 fixture's diagnostic look); the M2 audit
(`docs/qa/2026-10-14_2357_M2-freedoom-audit.md` §5, item A4) found RANGE
the only map still on them. No new art: every lump below is approved in
`docs/art/TEXTURE-INDEX.md` and packed under `assets/`, and each is used
as MAP01 uses it (`docs/levels/MAP01-zarya-7.md` §6): concrete for rooms,
steel plate for the way through, the hazard panel and the lamp only where
the player presses.

| Zone | Walls | Floor / ceiling | Why |
|---|---|---|---|
| hall | `SDCONC1` | `SDFLR2` / `SDCEIL2` | a poured-concrete firing hall on hangar floor; 128 high, so one panel exactly, no seam |
| exit alcove | switch `SDSW1D`, jambs `SDSTEL1` | `SDFLR2` / `SDCEIL1` | unchanged signs: the hazard panel under the lamp, as MAP01's exit |
| gallery door | leaf `SDDOOR1` on both faces, track `SDSTEL1` | `SDFLR2` / `SDCEIL2` (never seen shut) | unchanged: the door as MAP01 taught it |
| gallery passage | `SDSTEL1` (and the lintel the gallery sees over the mouth: 128 high, one plate, since the gallery is 256) | `SDFLR2` / `SDCEIL2` | green plate, MAP01's airlock (Z8): a way through, not a room; it continues the door's track |
| gallery | `SDCONC1`; Lenin `SDPOSTR1` and Stalin `SDPOSTR3` on the far wall, Marx `SDPOSTR4` and Engels `SDPOSTR5` on the end walls (§5.1) | `SDFLR3` / `SDCEIL2` | the same concrete, 256 high since the posters: two panels exactly, no cut (it was 192, the second panel cut at the ceiling); the two-tone tiles of MAP01's dorm and komnata set the bestiary apart from the hall underfoot |
| hall, west wall | the mural `SDPOSTR2` north of the exit alcove (§5.1) | | |

| Old (IWAD) | Faces / sectors | New |
|---|---|---|
| `STARTAN2` | 25 sidedef parts (17 middle, 4 upper, 4 lower) | `SDCONC1` 17 (11 / 3 / 3), `SDSTEL1` 8 (6 / 1 / 1: the passage) |
| `FLOOR4_8` | 5 floors | `SDFLR2` 4, `SDFLR3` 1 (the gallery) |
| `CEIL3_5` | 4 ceilings | `SDCEIL2` 4 |

**Alignment.** Both room materials are 64 wide and a wall run starts its
texture at its own first vertex. Every one-sided wall of concrete or plate
is given the `offsetx` that puts its panel seams on the map's 64 grid
(`world_align()` in `map.py`); only two runs start off it, the hall's west
wall north of the alcove (y 416, offset 32) and the alcove's north jamb, so
the hall's corners meet on whole panels and the cut halves sit against the
alcove. The door leaf and the exit switch keep offset 0, seen whole.
Vertically the `GridMap` default (`dontpegbottom`) stacks panels from the
floor, as on every map.

The signs still mean what they mean in MAP01: the door leaf and the
hazard panel appear only on the door and the exit, the lamp panel only
over the exit (tested). `SDSTEL1` is no longer only the track: it is the
passage's plate too, which is how MAP01 uses it. No new texture, no IWAD
reference; MOD-SPEC §5 still declares `STARTAN2`, `FLOOR4_8` and `CEIL3_5`
as IWAD assets, which no map uses now (that table is `mod-engineer`'s).

### 5.1 The posters (CEO, 2026-10-22)

«reutiliza cuadros [...] que esos posters puedan aparecer en cualquier
nivel». The range is a room of the Zarya-7 base and hangs what the base
hangs: the approved pictures of `docs/art/TEXTURE-INDEX.md`, no new art.
Each is one 128-long one-sided line in a room exactly its height, floor
pegged, at offset 0 (`world_align()` shifts only concrete and plate), so it
is seen whole: `POSTERS` in `map.py`, checked by `tests/test_posters.py`.

| Name | Picture | Line | Room | Why there |
|---|---|---|---|---|
| `gallery_lenin` | Lenin `SDPOSTR1` 128×256 | y 1792, x 832–960 | gallery (256) | the far wall the row faces: from the passage's mouth the player sees the eight invaders lined up under Lenin and Stalin, either side of the axis (x 1024) |
| `gallery_stalin` | Stalin `SDPOSTR3` 128×256 | y 1792, x 1088–1216 | gallery (256) | the pair's other half |
| `gallery_west_slot` | Marx `SDPOSTR4` 128×256 (Marx-Engels slot) | x 0, y 1344–1472 | gallery (256) | the west end wall, mid-depth: on the left from the passage's mouth |
| `gallery_east_slot` | Engels `SDPOSTR5` 128×256 (Marx-Engels slot) | x 2048, y 1344–1472 | gallery (256) | the east end wall, facing Marx across the row |
| `hall_mural` | the cosmonautics mural `SDPOSTR2` 128×128 | x 0, y 448–576 | hall (128) | beside the exit alcove: the player turns round to leave and finds it, the base's mural in the base's range |

**The one geometry change.** A 128×256 portrait needs a room 256 high, and
the range had none (hall 128, gallery 192). The gallery's ceiling rises
from 192 to 256 (`GALLERY_CEILING`). Nothing else moves: floors, the door,
the passage, the row, the sight-line test (no line of sight from the
gallery into the hall: walls, not ceilings, decide it) are unchanged; the
General (100 tall) and the floating Doughboy get more air, not less; the
concrete stacks two whole panels where 192 cut the second.

**Marx-Engels (D117, 2026-10-22).** `POSTER_SLOTS_MARX_ENGELS` names the
two slots, Marx's first: `SDPOSTR4` Marx «ПРОЛЕТАРИИ / ВСЕХ СТРАН,» and `SDPOSTR5` Engels «СОЕДИНЯЙТЕСЬ!» (mirrored, looking at Marx), 128×256 like Lenin and Stalin; `MARX_ENGELS = ("SDPOSTR4", "SDPOSTR5")` lists them in `WALL_TEXTURES`. Looking north from the
passage's mouth, the gallery reads Marx, Lenin, Stalin, Engels across its
three walls, left to right.

## 6. Tests

`tests/test_range_map.py`, read back from the generated TEXTMAP:

| Test | Claim |
|---|---|
| `test_one_exit_switch_reached_from_the_start_with_no_door` | one `Exit_Normal`, pressed not crossed, on a one-sided wall, reached with every door shut |
| `test_the_exit_is_behind_the_player_start_and_within_a_short_walk` | on the start's row, behind him, pressable from the hall's edge |
| `test_the_exit_switch_wears_map01s_exit_face_whole` | `SDSW1D`, 64 long, alcove 128 high, lit over the hall |
| `test_the_gallery_is_reached_on_foot_through_its_door` | doors shut: hall and exit only; opening what the map offers reaches every sector |
| `test_the_gallery_door_opens_from_both_rooms_and_closes_again` | `Door_Raise` on both faces, door behind each, one leaf tile, opens over a body's height |
| `test_nothing_is_a_one_way_trap` | a way back to the start from every sector |
| `test_every_thing_stands_on_floor_the_player_reaches` | every pickup, target and enemy on reachable floor, none in the door; the row in the gallery |
| `test_the_passage_comes_out_behind_the_row` | every enemy faces away from the mouth; the warp still lands there |
| `test_the_gallery_cannot_see_into_the_hall_with_the_door_open` | from every enemy's eye (4 heights) no point of the hall (64 grid, 3 heights) is in view, door open. A straight passage fails it |
| `test_every_name_is_in_the_maps_lists` | every texture and flat the TEXTMAP wears is in `WALL_TEXTURES` / `FLAT_TEXTURES` |
| `test_no_iwad_texture_or_flat_every_name_is_ours` | **M2d**: every name is a packed lump under `assets/textures/` or `assets/flats/`, and none is an IWAD asset of MOD-SPEC §5 |
| `test_no_name_resolves_in_freedoom` | **M2d**, the audit's own check: no wall name in `iwads/freedoom2.wad`'s `TEXTURE1`/`TEXTURE2`, no flat between its `F_START`/`F_END` (skips where the IWAD is absent, as in CI) |
| `test_room_walls_sit_on_the_64_grid` | every one-sided concrete or plate wall has its seams on the 64 grid; every other face at offset 0 |
| `test_the_signs_only_where_the_player_presses` | door leaf and hazard panel only on the door and the exit; the lamp panel only over the exit |
| `tests/test_posters.py` `RangePosters` | the pictures of §5.1 whole (one line, the poster's width, a room its height, floor pegged, offset 0); the Marx-Engels pair in its two slots, Marx west and Engels east (D117) |

## 7. Engine checklist for the PM (D26: this role does not start GZDoom)

`SD_ALLOW_ENGINE=1 MAP=RANGE tools/run.sh`, or New Game → "Practice Range".

| # | Do | What must happen |
|---|---|---|
| P1 | at the start, turn 180 | the lit alcove with the hazard panel whole, steel jambs, no HOM |
| P2 | walk to `warp 704 744`, face 90, `use` | the door rises with the leaf whole on its face; the steel track either side |
| P3 | walk the passage north, east, north | it comes out behind the row; all eight asleep, backs turned |
| P4 | from the passage side, `use` the door again | it opens from this side too |
| P5 | back in the hall with the door open, fire the PPSh by the doorway, then walk into the gallery | nobody in the gallery has woken |
| P6 | press the exit switch | `SD_END02_TEXT` over `SDFLR1`, then the title screen (seen 2026-10-13 20:57; ADR 007 could not test it: the console `exit` quits GZDoom) |
| P7 | the log | zero `Script error`, `Missing`, `Unknown` |
| P8 | M2d: at the start, look round the hall | concrete panels on all four walls, hangar floor, plain ceiling panels; no Freedoom `STARTAN2` anywhere; no seam floating mid-wall (the hall is one panel high) |
| P9 | M2d: the west wall either side of the exit alcove, and the north-west corner | half panels against the alcove's steel jambs, whole panels meeting in the corners |
| P10 | M2d: the passage, then the gallery from its mouth | the passage is green steel plate with the door's track continuing into it; the gallery's concrete runs 2 panels high (256 since the posters), the steel lintel over the mouth one plate high, the tiled floor; nothing missing (no HOM, no `Unknown texture` in the log) |
| P11 | the posters (§5.1): from the passage's mouth look north, then west and east; at the start turn 180 | Lenin and Stalin whole behind the row, the slogan bands at the foot not cut, no vertical repeat; the two slots whole on the end walls; the mural whole beside the exit alcove, concrete half panel between it and the alcove's jamb; no HOM |

## 8. For the CEO: a player-facing name

The map's title, `SD_MAP02_NAME` (now `SD_RANGE_NAME`) = "Engineering Test Range" / «Инженерный *(Decided 2026-10-14, D46: "Training Ground" / «Учебный полигон».)*
полигон», is `mod-engineer`'s (MAPINFO and LANGUAGE) and says what the map
was, not what it is. **Proposed: "Training Ground" / «Учебный полигон».**
It sits under the episode name "Practice Range" / «Полигон» without
repeating it, says who the place is for, and the Russian is the plain term
a Soviet base would paint on the gate. Alternative, in the voice of MAP01's
"Zarya-7": "Range No. 7" / «Стрельбище № 7». Either is one LANGUAGE line in
each language (D21).

## 9. Not done, on purpose

- No health or ammo in the gallery: everything is in the hall, on the way
  to the door.
- No sign or text at the door: the leaf is the sign, as in MAP01.
- The gallery's waking rules are F5's: shooting one wakes it; whether its
  neighbours, which hear the shot and see the shooter, wake too is the
  same NOT VERIFIED engine behaviour as in §4.2, and it is the practice.
