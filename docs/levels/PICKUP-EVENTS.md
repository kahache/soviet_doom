# Pickup events — keys and objects that make things happen (V3 A2)

Living document. Owner: `level-designer` (Episode 1's, 2026-10-23). Scope:
the pattern every map of the campaign uses for **events fired by picking
something up** (D119's V3 note, D120's item A2): a door that opens, a wall that
sinks, a closet of monsters that comes out, lights that come on, a floor or a
lift that moves. The CEO asked for it as a level-design tool; MAP04 already
does it (the red key drops the gondolas' sides). This document says how to
build one, which specials to use, the safety rules and how each event is
tested. Each map's own events are listed in its design document
(`docs/levels/MAPxx-*.md`, section "Pickup events").

Code: `tools/sdbuild/events.py` (constructors and validation) and
`tests/_pickup_events.py` (the checks every map test can call). A map that
was written before the helper existed may keep its own constants (MAP04)
as long as its numbers match the table in §3.

## 1. What the engine does

- A thing in UDMF can carry an action special: `special = 21; arg0 = 12;
  arg1 = 16;` in its block. For an **inventory item** (a key, ammo, a
  weapon, health, armour) GZDoom runs it **once, at the moment the item is
  picked up, with the player as activator**, then clears it
  (`Inventory.DoPickupSpecial`, `zscript/actors/inventory/inventory.zs` in
  gzdoom.pk3 g4.14.2: `toucher.A_CallSpecial(special, args[0..4]); special
  = 0;`). VERIFIED in the source; in play, VERIFIED by nothing yet (MAP04's
  checklist K3 and every map's events wait for the PM's engine pass).
- For a **monster** the same fields run when it **dies** (MAP03's General
  opens his stores, v1.1). Same helper, same rules.
- Our replacement classes (`SD_BluePass replaces BlueCard`, the `SD_*`
  pickups) keep the special: the engine copies the map thing's special onto
  whatever class it spawns.
- **Only items that are always picked up fire reliably.** A key is always
  taken. Health is not taken at full health, ammo not at its maximum, a
  weapon not when owned with full ammo: an event on those fires late or
  never. **Rule: an event the design relies on rides on a key** (or a
  weapon the player cannot own yet at that point of the route); an event on
  any other item is decoration and must be harmless if it never fires.
- One thing carries **one** special. For more than one effect see §5.

## 2. How to write one (the generators)

```python
from sdbuild.events import door_open, event_thing

TAG_CARD_CLOSETS = 14          # every sector the event moves carries this id
CARD_EVENT = door_open("card_closets", TAG_CARD_CLOSETS, lighttag=TAG_CARD_LAMPS)
...
tm.sectors[closet_door].identifier = TAG_CARD_CLOSETS
tm.add_thing(event_thing(x, y, ED_BLUE_CARD, CARD_EVENT))
```

- `PickupEvent(name, special, args)` refuses a tag of 0 (a thing has no line,
  so tag 0 moves nothing or the wrong sector), any special outside §3's list
  and every closing or crushing special (rule R1).
- `event_thing` puts the thing on **every skill**: an event that exists on
  one skill only makes the maps differ in more than numbers. What a closet
  holds still scales by skill (the monsters inside, §4.1).
- The tag is a named constant `TAG_<EVENT>` in the map's `map.py`, the
  event a named constant `<ITEM>_EVENT`, and both go in the design
  document's tag table. **A tag used by an event is used by nothing else**
  (no line, no other event), so a test can say exactly which sectors move.
- Speeds are in eighths of a unit per tic: `MOVER_SPEED_SLOW` 8 (1 unit a
  tic, Doom's slow floor), `MOVER_SPEED_NORMAL` 16, `MOVER_SPEED_FAST` 32;
  doors use `DOOR_SPEED_SLOW` 16 of `udmf.py`. **Slow is the warning**: a
  wall that sinks in two seconds, with its grinding sound, tells the player
  something is coming.

## 3. The specials

Numbers VERIFIED 2026-10-23 in the special table compiled into the engine we
ship on (GZDoom g4.14.2 `gzdoom.exe`: each record is a pointer to the
special's name followed by its number and its minimum and maximum argument
counts; no data file in gzdoom.pk3 carries the numbers, xlat only uses the
names). How it was read, for whoever needs another number: find the name's
NUL-terminated string in the exe, turn its file offset into a virtual
address with the PE section table, search the exe for that 8-byte address,
and read the 32-bit number right after it. It reproduces the numbers already
proved on lines (10, 11, 12, 13, 21, 243). `tests/test_pickup_events.py`
holds the table. Behaviour per the GZDoom source; in play NOT VERIFIED
unless the column says so.

| Special | # | Args | Use | In play |
|---|---|---|---|---|
| `Door_Open` | 11 | tag, speed, lighttag | a closet door, a shutter, a hidden door: rises to its lowest neighbouring ceiling − 4 and stays. The **light tag** brings every sector carrying it to its brightest neighbour's level as the door rises | VERIFIED on lines (MAP01: D2, the panels; the light tag on SW-A, 2026-10-13); on a thing NOT VERIFIED |
| `Door_Raise` | 12 | tag, speed, delay, lighttag | a door that opens and shuts again: **not for closets** (it can shut monsters back in) | VERIFIED on lines |
| `Floor_LowerByValue` | 20 | tag, speed, height | a floor that gives way by a set depth | NOT VERIFIED |
| `Floor_LowerToLowest` | 21 | tag, speed | a wall (a sector raised to the ceiling) sinks to the lowest neighbouring floor: shortcuts, wagon sides | MAP04 K3, NOT VERIFIED |
| `Floor_LowerToNearest` | 22 | tag, speed | a step down to the next floor | NOT VERIFIED |
| `Floor_RaiseByValue` | 23 | tag, speed, height | a bridge or a step that comes up (R1: must shut nothing) | NOT VERIFIED |
| `Floor_RaiseToNearest` | 25 | tag, speed | idem, to the next floor up | NOT VERIFIED |
| `Floor_MoveToValue` | 37 | tag, speed, height, negative | a floor to an absolute height (negative = 1 makes the height negative) | NOT VERIFIED |
| `Ceiling_RaiseByValue` | 41 | tag, speed, height | a low ceiling that opens up | NOT VERIFIED |
| `Ceiling_MoveToValue` | 47 | tag, speed, height, negative | a ceiling to an absolute height | NOT VERIFIED |
| `FloorAndCeiling_LowerByValue` | 95 | tag, speed, height | **a lift car**: floor and ceiling go down together, carrying what stands on it | NOT VERIFIED |
| `FloorAndCeiling_RaiseByValue` | 96 | tag, speed, height | the same, up | NOT VERIFIED |
| `Light_RaiseByValue` | 110 | tag, value | brighter by `value` | NOT VERIFIED |
| `Light_ChangeToValue` | 112 | tag, value | lights on (or off) at once | NOT VERIFIED |
| `Light_Fade` | 113 | tag, value, tics | lights that come up over `tics` | NOT VERIFIED |
| `Ceiling_RaiseToNearest` | 252 | tag, speed | a ceiling up to the next one | NOT VERIFIED |

**Never on a pickup** (rule R1): `Door_Close` 10, `Ceiling_LowerByValue` 40,
`Ceiling_LowerToFloor` 254, and anything that crushes. `events.py`
raises on them.

> `tools/sdbuild/udmf.py` keeps two unused, unverified constants
> `SPECIAL_LIGHT_CHANGE_TO_VALUE = 110` and `SPECIAL_LIGHT_FLICKER = 113`
> from MAP01 v2. The engine's table says **110 is `Light_RaiseByValue`,
> 112 is `Light_ChangeToValue`, 113 is `Light_Fade` and 115 is
> `Light_Flicker`**. Nothing uses the old two; use `events.py`'s.

## 4. Recipes

### 4.1 The monster closet (an ambush)

A small room beside the route, its mouth a **door sector** (ceiling = floor:
shut, no sight, no sound through it), the monsters inside. The pickup runs
`Door_Open(tag, 16, lighttag)` on the door sector.

- **Size**: at least 64 × 64 per monster plus 16 of clearance on every side
  of each one (a monster stuck in a wall never comes out); the mouth at
  least 64 wide and the door's open height at least 72 (the tallest monster
  that uses it, plus 16).
- **The way out**: the closet's floor at the room's floor, or a step of 24
  or less: monsters cannot climb more.
- **Shut before**: the door's ceiling equals its floor, so the safe-start
  test and every sight test see an opening of 0. Monsters in a shut closet
  do not see the player and are not seen.
- **Warning** (rule R4): the door's own sound, plus light: the closet's
  sectors tagged as the door's `lighttag` go from dark to their brightest
  neighbour (a lamp sector inside the closet at the level it should end at)
  as the door rises. The closet must be **seen from the pickup spot or the
  way out of it**, or heard: never only behind the player's back.
- **Population** by skill as any other monster (2/3/4); the closet's
  monsters count in the map's ammunition ruler (BALANCE §8) like the rest.
- **Not `AMBUSH`**: a deaf monster in a closet that opens may stay inside;
  ours wake on sight when the door is up.

### 4.2 The wall that sinks (a shortcut or a reveal)

A sector painted where the wall would be, its floor at its neighbours'
ceiling height (it reads as wall), its sides textured like the wall around
it. The pickup runs `Floor_LowerToLowest(tag, 8)`: it sinks to the lowest
floor around it and becomes floor. Lower-unpeg its sides (`dontpegbottom`)
so the texture rides down with it, as MAP04's gondola sides do.

### 4.3 Lights that come on

Either the `lighttag` of a `Door_Open` (one special, two effects, §5) or a
second pickup with `Light_ChangeToValue`. A light event never leaves a
fight in the dark: the route's light rules (each map's light table) hold
before and after.

**The light tag cannot make a lamp brighter than its room.** Each tagged
sector goes from the darkest of itself and its neighbours to its
**brightest neighbour** (GZDoom's `EV_LightTurnOnPartway`). So tag the dark
ROOM, not the lamp, and give it a lit neighbour at the level it should come
up to: MAP02's armoury is 96 with one lamp panel at 144 over the RPG-7; the
store's door rises and the armoury comes up to 144.

### 4.4 A floor that gives way, a lift that goes down

`Floor_LowerByValue` sinks a floor (with monsters on it, they ride down);
`FloorAndCeiling_LowerByValue` moves a whole car (floor and ceiling) down
a shaft. If the player can be on it, the place it arrives at has a way out
(R2) and the drop is under the fall damage our maps avoid (none in Doom:
falls do not hurt, but a pit with no way out is a softlock).

**The goods lift that brings an ambush up** (MAP03's set piece, V3 A3): a
shaft sector beside the room, its floor `travel` under the room's floor and
its **ceiling flush with the room's floor**. From the room that is a wall
(the room sees the shaft's front as upper texture from its floor to its
ceiling: no opening, no sight, no sound), and the monsters stand inside.
The pickup runs `FloorAndCeiling_RaiseByValue(tag, 16, travel)`
(`events.lift_raise_by_value`): the front lifts from the floor up like a
gate (an upper texture pegged as Doom pegs it moves with the ceiling), the
car's floor comes up the shaft behind it with its load, and it stops level
with the room, a lintel left over it. One special, no ACS, no PolyObject.
The shaft touches the room only, so it shuts nothing (R1).

### 4.5 Two traps found while building Episode 1

- **A window is not a door by sinking its sill.** MAP02's duty window (a
  48-high slot over a booth 32 up) does not become a passage when its floor
  drops to the hall's: the gap at the booth's floor is still 48, under a
  body (56). It is opened by raising its HEAD (`Door_Open` on the window
  sector: lowest neighbouring ceiling − 4). The map tests' flood fill caught
  it; trust it over the eye.
- **A thing in the event's closet is not on the route.** The map tests'
  stage-by-stage ammunition checks play the route without events, so a box
  left in a closet pays only the band (§8.2), not a stage; the closet's own
  monsters are not met in a stage either. Count both in the whole-map band.

## 5. One pickup, one special: more than one effect

1. **One tag, many sectors.** Every sector with the tag moves: two closets
   and a shortcut can share one `Door_Open` (all three are door sectors) or
   one `Floor_LowerToLowest` (all three are sinking walls).
2. **`Door_Open`'s `lighttag`**: the door and the lights in one special.
3. **Two pickups** close together on the route (the key and, a step on, a
   weapon the player cannot own yet). Each is one event with its own tag.
4. **Not** a walk-over line round the key: it fires whether the key is
   taken or not, and it is not what the CEO asked for.

ACS would allow scripts of many steps; **the mod has no ACS** (no
`SCRIPTS`/`BEHAVIOR` lump, no compiler in the repo) and V3 does not add one.
Every event is a single special.

## 6. The safety rules (binding; each has a test, §7)

| | Rule |
|---|---|
| **R1** | **Never shut the player in.** No closing or crushing special on a pickup; a floor that rises shuts no doorway or passage (its test shows the zones it touches stay connected). |
| **R2** | **Never block the critical route.** The exit is reachable with every event *not* fired, and with every event fired. No key, door or switch the route needs sits behind an event or on a sector an event moves. |
| **R3** | **The route never relies on an event alone**: if the engine did not run it, the map is still finished (the event is a shortcut, an ambush or a reveal; a locked door still does the locking). An exception needs an engine PASS filed in `docs/qa/evidence/`. |
| **R4** | **Ambushes are announced** by sound (the mover's own) and by light or sight: the released monsters come from a place the player can see from the pickup or its way out. At most one closet behind the player's back per event. |
| **R5** | **Safe starts hold**: no event thing, no closet and no moving sector within `SAFE_START_DISTANCE` (768) of the player start, and `tests/test_safe_starts.py` stays green (closets are shut at the start). |
| **R6** | **Everything released can leave**: a closet's monsters have a way out at 24 or less once the event has fired, so 100 % kills stays possible on every skill. |
| **R7** | **Events ride on keys** (§1) unless they are harmless if they never fire. Every event thing is on every skill. |
| **R8** | **One tag, one event.** A tag used by an event is carried by no line and by no other thing; the design document lists the tag and every sector it moves. |

## 7. How each event is tested (no engine)

`tests/_pickup_events.py` gives the map tests these checks over the parsed
TEXTMAP (the same `parse_textmap` the map tests use):

- `event_things(things)`: every thing that carries a special (pickup and
  death events).
- `assert_event(test, things, sectors, lines, ednum, event, expected)`: the
  thing of that DoomEdNum carries the event **once**, on every skill, with
  its special and its five args; the sectors whose id is `arg0` are exactly
  `expected` and no line acts on that tag (R8); the special is not a
  closing one (R1).
- `sector_after(event, index, sectors, around)` and
  `heights_after(events, sectors, lines, sides)`: what each tagged sector's
  floor and ceiling become once its event has run, by the engine's rule for
  that special (door: lowest neighbouring ceiling − 4; lower to lowest; by
  value; a lift car by the same value both), so a map test can rebuild its
  flood fill with the event fired.
- In the map's own test file (the Episode 1 maps do it, copy them): the
  model's `heights()` takes the event's heights once its tag is "open", and
  `progression(events=True)` opens an event's tag as soon as its thing's
  sector is reachable, as a manual door opens. Then: the exit with no event
  **and** with every event (R2, R3), nothing reached before lost after (R1),
  no line opening an event's tag, the closet sealed before and reachable
  after with a body's headroom (R6), its monsters there on skill 2, a sight
  line from the pickup to the released monsters' way out (R4), and the
  distances to the start (R5). `tests/test_map01.py`
  (`Map01PickupEventsTest`), `test_map02_metro.py` and
  `test_map03_factory.py` have one class each.
- The map's ammunition band (BALANCE §8) counts the closets' monsters like
  any other: budget them (§4.5).

**In the engine** (the PM, D26): each map's checklist has one line per event:
walk onto the item, watch the effect, and `netevent sdtag <tag>` (the route
helper's, `tools/route.py`) prints the tagged sectors' floor and ceiling
after it. The route tools walk onto keys already. A route step may check an
event's tag with `tags=((tag, False),)` before the pickup and `(tag, True)`
a few steps after it (the door rule: every tagged sector a body high);
a lift car is a body high before and after, so print it (`tag N` with no
expectation) and read the numbers. A route that NEEDS an event's result
(R3's exception) says so in its step.

## 9. Episode 1, as applied (2026-10-23)

| Map | Event | Rides on | Special | Moves | Design doc |
|---|---|---|---|---|---|
| MAP01 | `izh_hound` | the IZh on the guard post's rack | `Door_Open` (12, 16) | a closet off the service corridor: a hound | §20 |
| MAP01 | `ppsh_squad` | the PPSh-41 on the catwalk | `Door_Open` (13, 16) | a closet in the hangar's south wall: a trooper and a rifleman, a box of rounds | §20 |
| MAP02 | `pass_window` | the blue pass | `Door_Open` (12, 16) | the duty window's head: a way back down into the hall | §18 |
| MAP02 | `rpg_alarm` | the RPG-7 | `Door_Open` (13, 16, light tag 14) | the armoury's store (two guards) and the armoury's light, 96 → 144 | §18 |
| MAP03 | `office_closets` | the yellow key | `Door_Open` (13, 16) | two office closets at the stair head: a clerk each | §19 |
| MAP03 | `goods_lift` (A3) | the red key | `FloorAndCeiling_RaiseByValue` (14, 16, 192) | the foundry's goods lift comes up with its crew | §19 |

MAP01 has no key: its events ride on tutorial weapons that nothing drops
before them (R7's second case).

## 8. What each map documents

A table **"Pickup events"** in its design document: the event's name, the
item and where it lies, the special and its args, the tag and the sectors it
moves, what the player sees and hears, the monsters released per skill, and
the rules it was checked against. The tag table and the engine checklist
gain one line each.
