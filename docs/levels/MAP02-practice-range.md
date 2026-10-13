# MAP02 — the practice range

Design document. Owner: `level-designer`. Source: `src/maps/MAP02/map.py`;
tests: `tests/test_map02_practice_range.py` (the map) and
`tests/test_practice_range.py` (`mod-engineer`'s: how MAPINFO and MENUDEF
reach and leave it). Russian mirror: owed (D34), at the same path under
`docs/ru/`.

Status, 2026-10-13: **v1 BUILT**, not yet seen in the engine (the PM's
batched pass, D26; checklist in §7).

## 1. Synopsis

A firing range and a bestiary: every weapon of the arsenal within a few
steps of the start, targets to shoot them at, and behind a door one of
each enemy, asleep, to meet one at a time.

## 2. Where it comes from

MAP02 was built in F4 by `mod-engineer` as an engineering fixture (prove
each weapon can be picked up, fired and made to do damage), and grew a
bestiary gallery in F5. Neither had a design document: it was a test bench,
not a level. **D41** (`docs/PRD.md`) ships it to players as a practice
range, a second episode on New Game (`docs/engine/adr/007-practice-range-as-a-second-episode.md`;
contract in `docs/engine/MOD-SPEC.md` §4.4). ADR 007 left two things to
this role: MAP02 had **no exit line**, so a player could leave only through
the menu; and the gallery was **connected to nothing**, reached only with
the console (`warp 1024 1152`). This document is v1: the range made
player-facing. What F4 and F5 built is kept as it was.

## 3. Plan

```
y 1792 +----------------------------------------------------------------+
       |  BESTIARY GALLERY   ceiling 192, light 192                      |
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
| `gallery` | 0,1024 – 2048,1792 | 0 / 192 | 192 | F5's gallery, unchanged |

5 sectors, 26 lines, 39 things (F5: 2 sectors, 8 lines, 39 things).

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
the IWAD look (`STARTAN2`, `FLOOR4_8`, `CEIL3_5`, MOD-SPEC §5), the
`ambush` flag on every target and enemy, the light of both rooms. Every
thing is on every skill: skill changes what the engine's rungs change
(damage taken, ammo given), not what is placed. No secrets, no keys.
`tools/route.py`'s `map02-start` walk (north up x 288 onto the ice axe) is
still one sector from start to pickup.

## 5. Textures by zone

| Zone | Walls | Floor / ceiling |
|---|---|---|
| hall, gallery, passage | `STARTAN2` (IWAD) | `FLOOR4_8` / `CEIL3_5` (IWAD) |
| gallery door | leaf `SDDOOR1` on both faces, track `SDSTEL1` | — |
| exit alcove | switch `SDSW1D`, jambs `SDSTEL1` | `FLOOR4_8` / `SDCEIL1` |

The project's approved textures appear only where the player must read
"press here", so the range keeps its diagnostic look and the signs mean what
they mean in MAP01 (tested: `test_project_textures_only_where_the_player_presses`).
No new texture, no new IWAD reference.

## 6. Tests

`tests/test_map02_practice_range.py`, read back from the generated TEXTMAP:

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
| `test_project_textures_only_where_the_player_presses` | the signs only on the door and the exit; every name in the map's lists |

## 7. Engine checklist for the PM (D26: this role does not start GZDoom)

`SD_ALLOW_ENGINE=1 MAP=MAP02 tools/run.sh`, or New Game → "Practice Range".

| # | Do | What must happen |
|---|---|---|
| P1 | at the start, turn 180 | the lit alcove with the hazard panel whole, steel jambs, no HOM |
| P2 | walk to `warp 704 744`, face 90, `use` | the door rises with the leaf whole on its face; the steel track either side |
| P3 | walk the passage north, east, north | it comes out behind the row; all eight asleep, backs turned |
| P4 | from the passage side, `use` the door again | it opens from this side too |
| P5 | back in the hall with the door open, fire the PPSh by the doorway, then walk into the gallery | nobody in the gallery has woken |
| P6 | press the exit switch | `SD_END02_TEXT` over `SDFLR1`, then the title screen (ADR 007 could not test it: the console `exit` quits GZDoom) |
| P7 | the log | zero `Script error`, `Missing`, `Unknown` |

## 8. For the CEO: a player-facing name

The map's title, `SD_MAP02_NAME` = "Engineering Test Range" / «Инженерный
полигон», is `mod-engineer`'s (MAPINFO and LANGUAGE) and says what MAP02
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
