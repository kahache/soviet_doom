# MAP05 — «Волжская ГЭС» (Volga Dam), the hydroelectric station at Zhiguli

Design document. Owner: `level-designer`. Status: **v1 BUILT 2026-10-22
(§13): the whole map, walkable from start to exit, textured with approved
lumps only, populated, three secrets; the Dam set applied the same day
(§7.2, §13.6); not yet walked, no engine pass yet (D26).** Episode 2,
«The Road to Moscow» (D104, phase P4), second map. Built MVP first (D60). Source: `src/maps/MAP05/map.py`; tests:
`tests/test_map05_dam.py` (the map) and `tests/test_map05_route.py` (its
automatic route); route `dam-critical` in `tools/route.py`; overview
`docs/levels/shots/MAP05-overview.png`. Russian mirror: owed at the phase
close (D34).

> **Walk it** (the PM or the CEO; agents never start GZDoom, D26):
> `python3 tools/build.py && SD_ALLOW_ENGINE=1 MAP=MAP05 SKILL=3 tools/run.sh`.
> Automatic run: `SD_ALLOW_ENGINE=1 python3 tools/route.py --route dam-critical --keep-evidence`.

Inputs this document obeys and does not restate: `docs/PRD.md` (D35 the
factions, D58 the unfound pass, D60 MVP first, D104 episode 2),
`docs/engine/BESTIARY.md`, `docs/engine/BALANCE.md`, `docs/engine/MOD-SPEC.md`
(DoomEdNums, locks, the passes), `docs/art/TEXTURE-INDEX.md` (approved lumps
only) and the method of `docs/levels/MAP03-factory.md`.

![MAP05 from above](shots/MAP05-overview.png)

## 1. Synopsis

November 1977. The armoured train brings Sergeant Vilanova across the Volga
to the station on the east bank of the Zhiguli dam, level with its crest,
where a gate bars the road west; he goes down into the dam, takes back the
turbine hall, the spillway and the control room from the Fourth Reich and
the Liberty Legion, climbs the cable gallery to the substation for the
gate's pass, and fights his way west along the crest to the far bank.

## 2. Its place in the campaign

| | |
|---|---|
| Comes after | MAP04, the Trans-Siberian railway yard: its exit text (`SD_MAP04_EXIT_TEXT`) ends "Across the water stands the dam at Zhiguli… This morning the turbines are still." MAP05 starts on the station's platform, beside the armoured train (a steel block on the rails, blocking the tunnel it came out of). |
| Comes before | MAP06, Red Square. The exit text (`SD_MAP05_EXIT_TEXT`) begins "You cross the crest of the dam with the spillway roaring below. Behind you the turbines turn again": the crest is the last walk, the spillway is under it, and SW-A in the control room is the shift chief's knife switch. |
| What it adds | **verticality** (three levels 384 apart in all, a descent and a climb through the concrete), **water** (a light sting), a key behind the other key's door (yellow → blue), a **shortcut found from behind** that saves the long walk back, and two **counter-attacks on the locks' own tags**. |
| Factions (D35) | both. The Legion holds the east bank's station and the open water of the spillway (its Doughboys fly there); the Reich runs the machine: the galleries, the turbine hall, the substation. Both man the control room and both hold the crest. The General is MAP03's and is not here. |
| MAPINFO, LANGUAGE | the scaffolding agent's (P4): `map MAP05 lookup "SD_MAP05_NAME"`, `cluster = 6`, `next = "MAP06"`, `sky1 = "SKY1"`, `par = 330`; names and texts in `[enu default]`, `[ru]`, `[ca]`. This role touches neither (§11). |

## 3. What the map has to do

| Job | How the layout does it |
|---|---|
| Be a dam | the crest runs 3552 units east–west at +384, the turbine hall lies at its foot (0) downstream, the spillway's channel (−64) runs from the sluice gates under the crest's parapet; the station and the exit are on the two banks at the crest's ends. From the spillway the player looks up 448 units at the crest's parapet; from the crest's west end he looks down into the spillway. |
| Use the height | the descent is three flights of seven steps inside the concrete (the inspection gallery), the catwalk in the turbine hall is twelve rises up, the climb back is one long flight in the cable gallery. No lift (MAP01 §4). |
| Teach the order of two keys | the **blue gate** onto the crest is the first thing seen (down the platform from the start, lit blue); the **yellow door** is high on the turbine hall's north catwalk, seen from the hall's floor as the player comes in; the **yellow key** lies across the spillway's water; the **blue key** behind the yellow door's climb, in the substation. Lock before key, both times (tested). |
| Answer D58 again | each key alone on a lit place (192, its lock's colour) on the route, seen from where that place is entered (tested: the yellow key from the spillway gallery's mouth across the water, the blue key from the cable gallery's top). |
| Reward knowing the map | SW-B opens a shutter from the substation straight into the station, 200 units from the blue gate; without it the way back is the long one (the cable gallery, the control room, the hall, the three flights up: about 3000 units). Tested as not needed. |
| Rise | three thirds by hit points met, each heavier than the one before on every skill, and the crest the heaviest beat of all (tested, §6). |

Target length: 12–15 minutes first run on skill 3 (MAP03 is 10–12); about
6 once known.

## 4. Plan

Generated from the built map, 64 × 64 units per character, north up. Floors:
crest, station, substation **+384**; catwalk and control room **+192**;
turbine hall, galleries, spillway walkways **0**; the channel **−64**.

```
     y   x 384 .................................................................. 5056
  1984   XX RRRRRRRRRRRRRRRRRRRRRRccRRRRRRRRRRRRRRRRRRRRRRccRRRRRRR  SSSSSSSSS
  1920   XX#RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRBbSSSSooooo
  1856   XX#R-----------------------------------------------------RBb----ooooo   <- the train
  1792   XX RRRRRRRRRRRRRRccRRRRRRRRRRRRRRRRRRRccRRRRRRRRRRRRRRRRRR  SSSSSSSSS
  1728      ========================== RR ========== ## ===========  SSSSSSSSS   @ start (4704, 1664)
  1664    WWWWWW~~~~WWWW              RRRR          3333             SSSSSSSSS
  1600    WWWWWW~~~~WWWW              RRRR          3333  UUUUUUUUU  SSSSSSSSS
  1536    WWWWWW~~~~WWWW                                  UUooUUUUUU#SSSSSSSSSkk
  1472    WWWWWW~~~~WWWW                                  UUooUUUUUU#SSSSSSSSSkk
  1408    WWWWWW~~~~WWWW                                  UUooUUUUU  SSSSSSSSS
  1344    WWWWWWs~ssWWWW                                  UUUUUUUUU     ## kk
  1280    WWWWWWs~ssWWWW                                  UUUUU22UU    GGGGkk
  1216    WWWWWW~~~~WWWW              CCCCCCCCCC          UUUUU22UU    GGGG
  1152    WWWWWW~~~~WWWW              CCCCCCCCCC          UUUUUUUUU    GGGG
  1088    WWWWWW~~~~WWWW              CccCCCCccCKKsssssKKKUUUUUUUUU     ss
  1024    WWWWWW~~~~WWWW              CCCCCCCCCCKKsssssKKKUUooUUooU     ss
   960    W111WW~~~~WWWW           kk CCCCCCCCCC    kk    UUooUUooU     ss
   896    W111WW~~~~WWWW           kk CCCCCCCCCC    kk    UUooUUooU     ss
   832    W111WW~~~~WWWW    sssssHHHHHHHHHyyHHHHHHHHHHHH               LLLL
   768    WWWWWW~~~~WWWW    sssssHHHHHHHHHyyHHHHHHHHHHHH               LLLL
   704    WWWWWW~~~~WWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHH                ss
   640    WWWWWW~~~~WWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHH                ss
   576    WWWWWW~~~~WWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHH                ss
   512    WWWWWWs~ssWWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHHgggggggggggssssLLLL
   448    WWWWWWs~ssWWWW    HHHoooHHHoooHHHoooHHHoooHHHHgggggggggggssssLLLL
   384    WWWWWW~~~~WWWW    HHHo oHHHo oHHHo oHHHo oHHHH     #
   320    WWWWWW~~~~WWWWWWWWHHHoooHHHoooHHHoooHHHoooHHHH     2
   256    WWWWWW~~~~WWWWWWWWHHHHHHHHHHHHHHHHHHHHHHHHHHHH   22222
   192    WWWWWW~~~~WWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHH   22222
   128    WWWWWW~~~~WWWW    HHHHHHHHHHHHHHHHHHHHHHHHHHHH   22222
    64           ##
 -128          1111      (S1, the drain, down to y -224)
```

Legend: `S` station (start) · `-` rails · `o` the armoured train, the
generators (the blank in each is its solid shaft) and the transformers ·
`b` the blue gate's portal, `B` the **blue gate** · `G` gatehouse · `s`
stairs and steps · `L` the inspection gallery's landings · `g` lower gallery
· `H` turbine hall; its north strip at 768–896 is the catwalk (+192), `y`
the yellow door's portal on it (the **yellow door** is just north) · `C`
control room, `c` consoles and the crest's barricades · `K` cable gallery ·
`U` substation, `2` (in it) the **blue key's** pad · `W` spillway walkways,
`~` the channel, `1` (in it) the winch house with the **yellow key** · `R`
the crest · `=` parapets · `X` the west bank's hall, the **exit** at its
west wall · `#` doors and shutters · `k` monster closets · `1`, `2`, `3`
below and beside: the secrets S1 (the drain), S2 (the pump room), S3 (the
shut crane hut). The control room's two windows onto the hall and the
clerestory panes are 32 and 16 deep and do not show at this scale.

| # | Zone | x | y | floor | ceil | light |
|---|---|---|---|---|---|---|
| Z1 | Station (start), rails, the train (prop, +128) | 4288…4864 | 1408…2048 | 384 | sky | 128 |
| Z1b | Blue gate's portal | 4224…4288 | 1856…1984 | 384 | 512 | **192**, blue |
| — | Blue gate (lock 2) | 4192…4224 | 1856…1984 | 384 | door | |
| Z2 | Gatehouse, behind D1 | 4416…4672 | 1152…1376 | 384 | 512 | 144 |
| Z3 | Inspection gallery: 3 flights of 7 steps, 2 landings | 4416…4672 | 448…1152 | 384→0 | +128 | 112 |
| Z4 | Lower gallery | 3456…4192 | 448…576 | 0 | 128 | 112 |
| Z5 | Turbine hall, 4 generators (housing +48, shaft solid) | 1664…3456 | 128…896 | 0 | 448 | 160 |
| Z5c | Catwalk (stair of 11 from the west end) | 1664…3456 | 768…896 | 16…192 | 448 | 160 |
| Z5y | Yellow door's portal on the catwalk | 2560…2688 | 768…896 | 192 | 320 | **192**, yellow |
| Z6 | Control room (consoles +32, two windows onto the hall) | 2304…2944 | 928…1312 | 192 | 352 | 160 |
| Z7 | Spillway gallery | 1408…1664 | 256…384 | 0 | 128 | 112 |
| Z7w | Spillway: east and west walkways | 512…1408 | 128…1760 | 0 | sky | 112 |
| Z7c | The channel (water, hurts 5/32 tics), steps out at y 448–576 and 1280–1408 | 896…1152 | 128…1760 | −64 | sky | 112 |
| Z7k | Winch house, the yellow key | 576…768 | 832…1024 | 16 | 144 | **192**, yellow |
| Z8 | Cable gallery: flat, 11 steps, top corridor | 2976…3584 | 1056…1184 | 192→384 | +128 | 112 |
| Z9 | Substation (3 transformers +96, 2 pylons solid) | 3584…4160 | 896…1664 | 384 | sky | 128 |
| Z9p | Transformer pad, the blue key | 3904…4032 | 1216…1344 | 400 | sky | **192**, blue |
| Z9s | Passage to the station's shutter, SW-B | 4160…4256 | 1472…1600 | 384 | 512 | 128 |
| Z10 | The crest, road (`SDFLR1`) and rails, 4 barricades, 2 crane huts | 640…4192 | 1792…2048 | 384 | sky | 128 |
| — | Parapets (+32, impassable edge) | 640…4192, 4288…4864 | 1760…1792, 2048…2080 | 416 | sky 432 | 128 |
| Z11 | West bank's hall, behind D2 | 448…608 | 1792…2048 | 384 | 512 | 144 |
| E | Exit niche | 432…448 | 1888…1952 | 384 | 512 | **192** |

Extent 4576 × 2304 units (MAP03: 3776 × 2144). 150 sectors, 609 lines
(141 and 575 before the Dam set's dressing, §13.6).
Every height is a multiple of 16; no step up is over 16 (tested).

## 5. Progression, keys, switches and the exit

```mermaid
graph LR
  S[Station<br/>start, SEES the blue gate] -->|D1| G[Gatehouse] --> L[Inspection gallery<br/>3 flights down] --> LG[Lower gallery]
  LG --> H[Turbine hall<br/>SEES the yellow door]
  H --> SG[Spillway gallery] --> SP[Spillway] -->|across the water| YK[Winch house<br/>YELLOW KEY]
  H -->|catwalk stair| CW[Catwalk] -->|yellow door + its closets| C[Control room]
  C -->|SW-A opens the cable gallery| K[Cable gallery<br/>1 flight up] --> U[Substation]
  U --> BK[Pad<br/>BLUE KEY]
  U -->|SW-B opens the shutter| S
  S -->|blue gate + its closets| R[The crest] -->|D2| X[West bank<br/>EXIT]
```

**The keys.** Doom's blue and yellow cards, editor numbers **5** and **6**,
locks **2** and **3** (`gzdoom.pk3 → lockdefs.txt`, g4.14.2), both already
opened in the engine (MAP02's blast door, MAP03's yellow door). They spawn as
`SD_BluePass` and `SD_YellowPass` (`src/zscript/sd/keys.zs`); the map places
Doom's numbers.

| Id | Where | Type | Special | Can it lock the player out? |
|---|---|---|---|---|
| D1 | Station → gatehouse | manual door | `Door_Raise (1)`, both faces | no |
| **YD** | Catwalk → control room, 128 wide | **locked, opens for good**; also opens the catwalk's two closets (tag 4) | `Door_LockedRaise (4, 16, 0, 3, 0)`, both faces, repeatable | no |
| SH-A | Control room → cable gallery | remote, opens for good, steel both sides | tag 10 | no |
| SW-A | Control room's east wall, beside SH-A | `SDSW1A` (the knife switch), one-shot | `Door_Open (10, 16, 0)` | no |
| SH-B | Substation's passage → station | remote, opens for good. Steel from the passage; **the station's brick from the station**: a shortcut found from behind | tag 11 | no |
| SW-B | The passage's north wall, beside SH-B | `SDSW1B` (push button), one-shot | `Door_Open (11, 16, 0)` | no |
| **BG** | Station → the crest, 128 wide | **locked, opens for good**; also opens the station's two closets (tag 3) | `Door_LockedRaise (3, 16, 0, 2, 0)`, both faces, repeatable | no |
| D2 | The crest → the west bank's hall | manual door | `Door_Raise (2)`, both faces | no |
| EXIT | Back of a 64 × 128 niche in the west hall's west wall, on D2's line | `SDSW1D`, the hazard panel | `Exit_Normal (0)` | — |

**The order, as the tests play it** (`test_the_route_is_the_designed_one`),
four rounds:

1. With D1 and the push panels only: the station, the descent, the turbine
   hall and its catwalk, the spillway, **the yellow key**. The blue gate
   seen from the start, the yellow door from the hall (both tested).
2. The yellow door (and the catwalk's closets): the control room, SW-A.
3. SW-A: the cable gallery, the substation, **the blue key**, SW-B.
4. The blue gate (and the station's closets) and SW-B's shutter: the crest,
   D2, the west hall, the **exit**; S3 on the way.

**Signposting** (D58, as on MAP03): each key alone on a lit place (192) in
its lock's colour (`lightcolor` blue `0x90A8FF`, MAP02's pass; yellow
`0xFFD860`, MAP03's) and nothing else in the map wears either colour
(tested). The yellow door wears `SDDOORY`; the blue gate wears `SDDOOR1` in
blue light until a blue trim exists (§7.2). Every switch is a real switch
face, one-shot, in sight of the shutter it opens (tested).

Rules that remove whole classes of softlock (MAP01 §4, MAP03 §5), all
tested: no door closes behind the player (locks and remote doors open for
good, manual doors reopen from both sides); no lift; no drop without a climb
back (the catwalk drops 192 to the hall, its stair climbs back; the
walkways drop 64 into the water, three steps climb out on both banks at two
places); the parapets are **impassable lines** (`blocking`), so nobody
walks, falls or jumps off the dam; no secret and no shortcut is needed;
from every reachable sector at every stage there is a way back to the start
and, at the end, a way on to the exit.

## 6. Intensity curve

```
  high |                                                                 ######
       |                                                                 ######  <- the crest:
 press |                  ####                         ####              ######     Panzermensch,
  ure  |                  ####  ###                    ####   ##   ####  ######     heavy, Doughboys
       |   ##        ##   ####  ###   ##    ###        ####   ##   ####  ######
   low |   ##   ##   ##   ####  ###   ##    ###   ##   ####   ##   ####  ######   ##
       +--------------------------------------------------------------------------->
        station  galleries hall spillway catwalk control cable substation station crest  exit
                                         closets               SW-B     closets
        0:00                                                                     ~14:00
```

| Beat | Space | Feeling | Mechanic introduced |
|---|---|---|---|
| 1 | Station | off the train into the cold; a Legion picket; **the view**: the blue gate, shut | the lock shown first |
| 2 | Gatehouse, inspection gallery | down into the concrete; close quarters on the landings | the descent |
| 3 | Turbine hall | the big room: four generators as cover, riflemen on the catwalk above, the Panzermensch at the far end; **the yellow door high on the catwalk** | the RPG-7 at the door |
| 4 | Spillway | outside again, at the bottom of the dam; the crest 448 above; Doughboys over the water; the key across it | the water stings |
| 5 | Catwalk, yellow door | **spike**: the catwalk's closets open behind the player as the door opens | the lock's own counter-attack |
| 6 | Control room | both factions at the consoles; SW-A | the knife switch |
| 7 | Cable gallery, substation | the climb; heavies among the transformers; the blue key | — |
| 8 | SW-B, station | the shutter opens onto the station: **the shortcut**; the blue gate; **spike** from the station's closets | the shortcut from behind |
| 9 | The crest | **climax**: the long road west along the top of the dam, both factions, the heavy by the far door | — |
| 10 | West bank | D2, the exit | — |

Measured (hit points met, by beat; `test_the_intensity_rises`):

| Beat | Skill 2 | Skill 3 | Skill 4 |
|---|---|---|---|
| Station, gatehouse | 90 | 90 | 210 |
| Galleries | 60 | 380 | 380 |
| Turbine hall | 620 | 850 | 1060 |
| Spillway | 460 | 520 | 950 |
| Control room + catwalk closets | 280 | 330 | 450 |
| Cable gallery, substation | 690 | 840 | 1840 |
| Crest + station closets + west hall | **1090** | **2640** | **3300** |

## 7. Textures

### 7.1 By zone (all approved and packed, tested)

| Zone | Walls | Floor | Ceiling |
|---|---|---|---|
| Station | `SDBRCK1` (the station's buildings), the two flags `SDFLAG1`/`SDFLAG2` in recesses either side of the blue gate's wall, Stalin `SDPOSTR3` in a recess beside them (7.3); the parapet `SDDAM1`; the signal post `SDSIGL1` (once, D107) | `SDFLR2`, rails `SDRAIL1` | sky |
| The armoured train | `SDARMR2` (MAP04's train), one `SDARMR1` star in the middle of its south side | `SDFLR4` | sky |
| Gatehouse, west hall | `SDTILE2` | `SDFLR3` | `SDCEIL1` |
| Control room | `SDTILE2`, four `SDCTRL1` boards standing on the floor (two flanking the mural, one on each side wall); the consoles `SDCTRL1`'s desk | `SDFLR3`; consoles `SDFLR4` | `SDCEIL1` |
| Inspection, lower and cable galleries | `SDTUNL1` (board-cast concrete with cable runs) | `SDFLR2` | `SDCEIL2` |
| Turbine hall | `SDDAM1` (the dam's concrete), clerestory `SDWIND1`, Lenin `SDPOSTR1` in the west wall, two portraits on the catwalk's back wall (7.3) | `SDFLR3` | `SDCEIL1` |
| Generators | housings `SDTURB1` (48 high: the tile's foot, flange and plinth on the floor), shafts `SDSTEL1` | `SDFLR4` | |
| Catwalk and its stair | face to the hall and risers `SDSTEL1`; back wall `SDDAM1` (the hall's) | `SDGRAT2` | |
| Spillway | `SDDAM1`; the banks out of the water `SDDAM2` (the tide mark on the water); the dam's face over the channel the rack `SDSPIL1` | `SDFLR2`; the water `SDWATR1` (animated) | sky |
| Substation | `SDRUST1` fence, transformers `SDSTEL1`, pylons and the gantry between them `SDSTEL1`, insulator strings `SDINSL1` (masked) under the gantry | `SDFLR2`, pad `SDFLR4`; the gantry's underside `SDFLR4` | sky |
| Crest | `SDDAM1` parapets and porches, barricades `SDCRAT1` / `SDCRTOP1`, crane huts `SDRUST1`, S3's gate `SDGATE1` | `SDFLR1` (the yellow lane line as the road's centre line), rails `SDRAIL1` | sky |
| Doors, switches | `SDDOOR1` (D1, D2, blue gate), `SDDOORY` (yellow door); `SDSW1A` (SW-A), `SDSW1B` (SW-B), `SDSW1D` (exit) | | |

The sky is `F_SKY1`, the engine's marker (MAPINFO's `SKY1`); the parapets
carry a sky ceiling 16 over their top (432), Doom's open-air trick: beyond
them the night sky, never a wall.

### 7.2 The Dam set (approved 2026-10-22, D107; applied 2026-10-22)

The art-director's set (`tools/art/gen_dam.py`, TEXTURE-INDEX "Episode 2")
replaced every stand-in of v1. Several lumps this section proposed were
never drawn under those names; each takes the nearest approved piece
(`DAM_SET` in `map.py`, tested: a proposed lump that exists is worn as
itself, one that does not is worn as its substitute):

| Proposed | Drawn? | The map wears | Where |
|---|---|---|---|
| `SDWATR1`…`4` | yes | `SDWATR1` (frames 2-4 by ANIMDEFS, 8 tics) | the channel, S1's outfall and panel |
| `SDTURB1` | yes (128×128, not the 64×128 proposed) | `SDTURB1` | the four generators' housings; the shafts stay `SDSTEL1` (the tile does not stack: its plinth would repeat up a 400-high column) |
| `SDTURB2` | no | `SDDAM1` | the turbine hall's walls, the catwalk's back wall and closets: the hall is inside the dam |
| `SDPANL1` | no | `SDCTRL1` | four boards on the control room's walls (below) |
| `SDPANL2` | no | `SDCTRL1`, its desk rows 64-95 | the two consoles' faces, 32 high |
| `SDSLUC1` | no | `SDSPIL1` | the dam's face over the channel's north end: the trash rack with water running out under it |
| `SDHVLT1` | no | `SDRUST1` (unchanged) | the substation's fence; the high voltage is said by `SDINSL1` on the gantry instead |
| `SDDOORB` | no | `SDDOOR1` in blue light (unchanged) | the blue gate (open point 14.2) |
| `SDGRIL1` | no | — | **still pending** (`PENDING_TEXTURES`): bars on the control room's two windows, v2; open meanwhile |

New pieces the section did not propose: `SDDAM1`/`SDDAM2` (the dam's
concrete, outside and in), `SDGRAT2` (the catwalk and its stair, replacing
the factory's `SDGRAT1`), `SDINSL1`, and from the railway set `SDARMR1`/`SDARMR2`
(the armoured train, as MAP04's) and `SDSIGL1` (single use).

**Alignment.** Every wall lump of the set is 128 high. A post-build pass
(`align_to_world`) sets each face's `offsety` (Doom's row offset, positive
raises the texture) from the height Doom pegs it to (a wall to its floor, a
lower texture to the higher floor, an upper one to the lower ceiling), and
its `offsetx` from the map's grid (front side from v1, back side from v2):

- `SDDAM1` on one grid from the hall's floor (0): its 64-px lift joints run
  level from the spillway's walls up the parapets' faces (416), round the
  hall, the catwalk's back wall (192), the stair's 32-wide steps and the
  closets' leaves, and along walls split by a neighbour's corner, with no
  seam (tested on every face).
- `SDDAM2` only on faces rising out of the water (the channel's banks and
  the steps out), its foot on the water (−64): the tide mark (72 px down the
  tile) runs 8 under the walkways' edge, the slime at the waterline.
- `SDSPIL1` from the water up, whole tiles from −64, cut under the parapet.
- `SDTURB1` housings: rows 80-127 (the hatch's foot, the lower flange, the
  plinth on the floor). The 1957 maker's plate (rows 40-62) is above the
  housings' 48 and does not show.
- `SDCTRL1` consoles: rows 64-95, the desk (the yellow rail, the buttons).

**The control room's boards (for `SDPANL1`).** The room is 160 high and
`SDCTRL1` 128 and does not stack (a second desk would show under the
ceiling). Each board is therefore a middle texture on a two-sided line, which
Doom draws once: a strip 8 deep along the wall (`prop_z6_board_*`, same
floor and ceiling as the room), its room face impassable and lower-unpegged
so the board stands on the floor, 128 high, the tiled wall showing above.
Two boards of 256 flank the mural on the north wall; one tile on each side
wall (x 2304 and 2944, y 928…1056) face each other.

**The gantry and the insulators.** `SDINSL1` is masked (RGBA, hard alpha,
D66, like `SDCHAN1`): only ever a middle texture on a two-sided line. A beam
`z9_gantry` spans the two pylons (x 3632…3664, y 1408…1536), its underside at
+320 over the substation (704), a 64-high steel face up to the sky line; the
strings hang from it on both long faces, two each, from 704 down to 576,
against the sky, 192 over the floor (over every head). The gantry is walked
under (a walkable zone); the stimpack that lay between the pylons is now in
it (its table row says `z9_gantry`; it did not move).

**The signal.** `SDSIGL1` once (D107: single use, one 64 span, never tiled):
a concrete post 16 × 64 north of the station's track (x 4304…4320, y
1968…2032, +128), its east face the signal, red, towards the train: the line
ends at the shut blue gate. The face is exactly one tile high.

Geometry added by the dressing, none of it on the route: the gantry (a
sector under the beam), four board strips and the signal post (props,
unwalkable). No floor the route uses moved; no door, key, switch, secret
or poster changed. S1's panel now wears `SDDAM1`, the channel's wall it is
cut into (the clue stays shadow and set-back, as before).

### 7.3 Posters (CEO, 2026-10-22: «que esos posters puedan aparecer en cualquier nivel»)

The approved pictures, not pending ones: no row of 7.2 was a poster or a
piece of propaganda, so none is replaced. Five pictures, each whole: one
one-sided line exactly the poster's width, in a sector exactly its height,
pegged to the floor, offset 0 (`tests/test_posters.py`). They are listed in
`POSTERS` in `map.py`.

| Name | Lump | Where | Why |
|---|---|---|---|
| `z5_lenin` | `SDPOSTR1` Lenin | turbine hall, west wall, x 1648, y 576…704: a recess 16 deep, 256 high (`z5_lenin_niche`) in the 448-high hall | the end of the hall the player looks down on entering from the lower gallery, clear of the generators' shafts: Lenin over the turbines («Communism is Soviet power plus the electrification of the whole country») |
| `z1_stalin` | `SDPOSTR3` Stalin | station, west wall, x 4272, y 1600…1728: a recess 16 deep, 256 high (`z1_stalin_niche`, its own concrete ceiling so the brick shows above it under the sky) | the first wall the player sees on arrival, between the shutter and the occupiers' two banners: the station's portrait, the invaders' flags hung beside it |
| `z6_mural` | `SDPOSTR2` cosmonautics mural | control room, north wall, x 2560…2688, y 1328: a recess 16 deep on a 32 sill (`prop_z6_mural_niche`, floor 224, ceiling 352) | straight ahead through the yellow door; the room is 160 high, the mural 128 |
| `z5_catwalk_w` | `SDPOSTR3` (Marx-Engels slot) | catwalk's back wall, y 896, x 2240…2368 (256 high: catwalk 192 to roof 448) | flanks the yellow door with its twin, 320 from its axis |
| `z5_catwalk_e` | `SDPOSTR1` (Marx-Engels slot) | catwalk's back wall, y 896, x 2880…3008 | the mirror of the west one |

**Marx-Engels slots.** `POSTER_SLOTS_MARX_ENGELS = ("z5_catwalk_w",
"z5_catwalk_e")`. `SDPOSTR4` is in preparation and not a lump yet, so each
slot wears its stand-in (Stalin west, Lenin east). Once it is approved and
packed the swap is one line in `map.py`: `MARX_ENGELS = "SDPOSTR4"`
(assumed 128×256, the twin of the other two portraits; nothing else moves,
tested). Seen from the hall floor the catwalk's edge hides the lowest ~30-40
units of the two catwalk portraits (their slogan band); from the catwalk they
are whole.

Geometry added: three 16-deep recesses (the three sectors above); no floor
the route uses moves, nothing a key, a door or a secret depends on.

## 8. Secrets (built in v1)

MAP01's rule: a clue is a comparison or a question, never a sign; each
secret has a way back; none is needed (tested).

| # | Where | Clue | Reward (every skill) |
|---|---|---|---|
| S1 | The channel's south end: the outfall | the only stretch of the channel's walls that stands 16 back, in shadow (96 against 112), where the water should run out. A push panel (tag 5), the channel's own `SDDAM1`, opens onto a culvert and a dry drain room at −64 | PG-7V box, medikit, shell box |
| S2 | The lower gallery's south wall | every metre of the gallery carries its cable runs (`SDTUNL1`); one 64-wide panel is plain concrete (`SDCONC1`), 16 back, in shadow. It opens (tag 6) onto a pump room | flak vest, shell box, stimpack |
| S3 | The crest's east crane hut | two crane huts alike on the crest's south side: the west one stands open (a health bonus or two, a trooper on skill 3); the east one is shut by a corrugated gate (`SDGATE1`), which is the push panel (tag 7) | the **Hand Katyusha** and two fuel canisters (one more volley): the panic button for the crest |

The panels carry the `secret` line flag (one-sided on the automap) and the
rooms sector special 1024. S1 and S2 open in round 0; S3 on the crest.

## 9. Enemies and resources by skill

Bestiary numbers (MAPINFO DoomEdNums 21100-21107), nested by Doom's skill
pairs (`skill_tier`). Every class but the General.

| Beat / zone | Skill 2 | Skill 3 | Skill 4 |
|---|---|---|---|
| Station, gatehouse | 3 troopers | 3 troopers | 3 troopers + 2 stormtroopers |
| Inspection and lower galleries | 3 riflemen | 4 riflemen + 2 hounds | 4 riflemen + 2 hounds |
| Turbine hall (catwalk included) | Panzermensch + 3 riflemen + 1 stormtrooper | Panzermensch + 4 riflemen + 2 stormtroopers + 1 hound | Panzermensch + 4 riflemen + 3 stormtroopers + 2 hounds |
| Spillway | Doughboy + 2 troopers | Doughboy + 2 troopers + 1 stormtrooper | 2 Doughboys + 3 troopers + 1 stormtrooper |
| Control room + the catwalk's closets (yellow tag) | 1 trooper + 2 riflemen + 1 stormtrooper + 1 hound | 2 troopers + 3 riflemen + 1 stormtrooper + 1 hound | 2 troopers + 3 riflemen + 3 stormtroopers + 1 hound |
| Substation | Panzermensch + 2 riflemen + 1 hound | Panzermensch + 2 riflemen + 2 hounds | Panzermensch + heavy + 2 riflemen + 2 hounds |
| Station's closets (blue tag), crest, west hall | Panzermensch + Doughboy + 3 troopers + 2 riflemen + 1 stormtrooper | Panzermensch + **heavy** + 2 Doughboys + 4 troopers + 2 riflemen + 3 stormtroopers | Panzermensch + heavy + 3 Doughboys + 5 troopers + 3 riflemen + 4 stormtroopers + 1 hound |
| **Total** | **31** | **46** | **60** |

Against MAP03's 25 / 38 / 52: a larger map with no boss, so more bodies and
three Panzermenschen on every skill (hall, substation, crest), the heavy
from skill 3. Doughboys only under the sky (spillway, crest), where they
fly (tested).

**Weapons** (pistol start: `+map MAP05` gives the TT-33 only), on every
skill, on the route, each before the fight it is for: the **IZh** on the
platform, the **PPSh-41** in the lower gallery, the **RPG-7** at the turbine
hall's door (nearer than the hall's Panzermensch, tested), the **ROKS-3** in
the control room; the **Hand Katyusha** in S3.

**Ammunition** (G3-8's ruler, MAP03's test: kills in IZh shells, PG-7V at 2
shells, fuel at ¼; route only, no drop, no secret):

| | Skill 2 | Skill 3 | Skill 4 |
|---|---|---|---|
| Needed | 69 | 116 | 165 |
| Placed | 274.5 | 261.5 | 237.5 |
| Ratio (≥ 1.35, and < 3 on skill 4) | 3.98 | 2.25 | 1.44 |

Also checked at every round of the route (damage placed so far against hit
points met so far). **Health** on skill 4: 6 stimpacks + 5 medikits, 9
health bonuses; **armour**: the flak vest up on the catwalk (for climbing
it), the heavy vest in SW-B's passage (round 2, before the station's closets
and the crest), 6 plates. Consumables scale down with skill (tested).

## 10. Engine elements used

| Need | Emitted | Status |
|---|---|---|
| Manual door | `Door_Raise` 12 (tag, 16, 150, 0), `playeruse` + `repeatspecial` | VERIFIED on MAP01 |
| Remote door, one-shot switch | `Door_Open` 11 (tag, 16, 0) | VERIFIED on MAP01 |
| Locked door that stays open | `Door_LockedRaise` 13 (tag, 16, 0, lock, 0) | VERIFIED on MAP02 (lock 2) and MAP03 (lock 3) |
| A locked door's tag opening closets too | the closets' door sectors share the lock's tag | **NOT VERIFIED**: MAP03 rides closets on a switch's `Door_Open`; here on `Door_LockedRaise`, which acts on every sector of its tag (ZDoom's `EV_DoDoor`, as `Door_Raise`). Checklist V3 |
| Keys | things 5, 6 (`SD_BluePass`, `SD_YellowPass` by `replaces`) | as MAP02, MAP03 |
| Coloured light | sector `lightcolor` | as MAP02, MAP03 |
| Damaging floor | sector `damageamount` 5, `damageinterval` 32 | field names VERIFIED in the spec (MAP03 §16.2); in play NOT VERIFIED: V4 |
| Sky | ceiling `F_SKY1`, MAPINFO `sky1 = "SKY1"` | the IWAD's sky marker; outdoor sectors of different ceiling heights side by side (the sky hack: no upper texture between two sky ceilings) NOT VERIFIED here: V2 |
| Impassable parapets | two-sided lines flagged `blocking` | Doom's impassable flag; blocks players and monsters, not projectiles |
| Turned flats | `rotationfloor` 90 on the rails and the crest's road | as MAP02, MAP03 |
| Secret | sector `special` 1024; panel lines flag `secret` | as MAP01-MAP03 |
| Animated water | floor `SDWATR1`, ANIMDEFS `flat SDWATR1` (4 frames, 8 tics) | ANIMDEFS tested (`tests/test_animdefs.py`); in play NOT VERIFIED: V11 |
| Texture offsets | sidedef `offsetx`/`offsety` on every Dam-set face (§7.2) | Doom's row offset, positive raises the texture; the sign NOT VERIFIED in the engine: V12 |
| Middle textures | `SDINSL1` (masked) under the gantry, top at the lower ceiling; `SDCTRL1` boards on `blocking` + `dontpegbottom` lines, foot on the floor; neither `wrapmidtex` | a two-sided middle texture is drawn once (ZDoom); MAP03's `SDCHAN1` is the masked precedent; NOT VERIFIED here: V13 |

Tag plan: **1** D1 · **2** D2 · **3** the blue gate and the station's two
closets · **4** the yellow door and the catwalk's two closets · **5** S1's
panel · **6** S2's panel · **7** S3's panel · **10** SH-A (SW-A) · **11**
SH-B (SW-B). Free: 8, 9, 12 and up.

## 11. MAPINFO and LANGUAGE (not this role's)

Written by the scaffolding agent working in parallel (P4): `map MAP05
lookup "SD_MAP05_NAME"` ("Volga Dam" / «Волжская ГЭС» / "La presa del
Volga"), `cluster = 6`, `next = "MAP06"`, `music = "D_SDFUNR"`
(provisional), `sky1 = "SKY1"`, `par = 330`; `SD_MAP04_EXIT_TEXT` leads in,
`SD_MAP05_EXIT_TEXT` leads out. Nothing in the map depends on more. A par
of 330 is fair for a player who knows the route (§3); my estimate is 360.

## 12. Version plan

| Version | Content | Done when |
|---|---|---|
| **v1 — whole, textured, populated** ✅ **BUILT 2026-10-22** (§13) | the plan of §4 with every door, both keys, both locks, both switches, the shortcut, the exit; approved lumps only (§7.1) with the pending list (§7.2); §8's three secrets; §9's population and budget | the CEO walks it on skill 3 and reaches MAP06 |
| v2 — light and detail | ~~the Dam set swapped in~~ done 2026-10-22 (§7.2, §13.6); light: the generators' glow, floodlights over the substation, the crest's lamps (the art-director recommends crest and spillway 160-192, hall 128-160); bars on the control room's windows (`SDGRIL1`, not drawn); a reservoir sector over the north parapet (`SDWATR1` exists now; the sky trick behind it needs an engine check) | a first-time player finds both keys and the exit without being told |
| v3 — balance | after the playtests (D60) | the map is played through on skill 3 |

## 13. v1 build record (2026-10-22)

### 13.1 What is in it

Everything in §4–§10. Built in one pass from a placeholder (one room, a
start and an exit, written first so the build never failed for the other
P4 agents).

### 13.2 Verification actually run

- `python -m unittest tests.test_map05_dam` — 68 tests, OK: structure,
  textures, light, the four rounds, no trap at any stage, sight lines of
  both locks and both keys, switches, doors, the water, the parapets, the
  population, G3-8, the secrets.
- `python -m unittest tests.test_map05_route` — 10 tests, OK: `dam-critical`
  finds MAP05 by its constants, plays the design's order, presses each line
  from the right room within use range, walks onto both keys, ends by D2 and
  the exit switch on one line.
- `python -m unittest tests.test_route` — OK with `dam-critical` registered
  (its setup now loads every map a built-in route names).
- `python tools/verify.py fast` (2026-10-22, 2494 tests): docs, build and
  check_pk3 PASS; nothing of MAP05's fails. Three shared tests fail on the
  whole of episode 2, not on this map alone: `test_doughboy_sprites` and
  `test_general_sprites` pin the set of maps that place a Doughboy / the
  General to episode 1's (MAP04-MAP06 now place Doughboys, MAP06 the
  General), and `test_panzermensch_sprites` finds 64-high openings in
  MAP06. MAP05's own 64-high openings (the control room's windows) were
  raised to 80 for that test.
- **No engine run** (D26).

### 13.3 Engine checklist for the PM (D26: this role does not start GZDoom)

| # | Check | How |
|---|---|---|
| V1 | The map loads with a clean log; `dam-critical` PASSes on skills 2, 3, 4 | `SD_ALLOW_ENGINE=1 python3 tools/route.py --route dam-critical --keep-evidence` |
| V2 | The outdoors read as outdoors: sky over the station, spillway, substation and crest; no upper texture where two sky ceilings meet; beyond the parapets, sky | walk the crest and the spillway |
| V3 | The yellow door opens the catwalk's two closets; the blue gate the station's two | open each lock, look back |
| V4 | The channel hurts (about 5 HP a second) and the steps lead out | stand in the water |
| V5 | Nobody walks or jumps off the crest; monsters on the crest do not fall into the spillway | try to jump the parapet |
| V6 | From the spillway the crest's parapet stands 448 up; crest monsters seeing the player there do not break the fight | look up from the spillway |
| V7 | The Doughboys fly over the water and the crest and do not stick on the parapets | watch them |
| V8 | `lightcolor` blue and yellow on the locks and the keys' places | as MAP02's L4, MAP03's K4 |
| V9 | The three secrets count (3 of 3 on the intermission) | push each panel, walk in |
| V11 | The water moves (`SDWATR1`-`4`), reads as water, not the portal's cobalt | stand at the channel |
| V12 | The Dam set's offsets (§7.2): `SDDAM1`'s lift joints level from the spillway up the parapet's 416 face and round the hall and catwalk, no seam at a split wall; `SDDAM2`'s tide mark just under the walkways' edge, the slime at the water; the rack from the water up; the generators' plinths on the floor; the consoles show the desk. If every face is off by the same amount, the offset's sign is the other way: flip it in `align_to_world` | walk the spillway, the hall, the control room |
| V13 | The middle textures: four `SDCTRL1` boards stand on the control room's floor, drawn once (the tile wall above, not a second board), and stop the player; the `SDINSL1` strings hang from the gantry with sky between them (no garbage in the transparent pixels), the player walks under | the control room; the substation |
| V14 | `SDSIGL1` once on the station's post, `SDARMR1`'s star whole on the train's south side | arrive |
| V10 | The posters (7.3) are whole and readable: Stalin's recess shows brick above it, not sky (its ceiling is concrete under a sky room); Lenin reads from the hall's east door at 160; the mural sits on its sill through the yellow door; the catwalk portraits from the floor and from the catwalk | arrive; walk the hall and the catwalk |

### 13.4 For the CEO's walk

1. Is the dam legible as a dam: the station on the crest, the descent, the
   hall at the foot, the spillway under the crest, the long crest west?
2. Is the yellow door, high on the catwalk, readable from the hall floor?
3. Is the water's sting right ("leve"), and is the spillway too big or
   empty for its fight?
4. The shortcut (SW-B into the station): found, and worth it?
5. The crest: too long a walk, or the right last fight?

### 13.5 What other roles hold

- `art-director`: the Dam set is in (§7.2). Still wanted: `SDGRIL1` (masked
  bars for the control room's windows, v2); optional, if the CEO wants them:
  a blue-trimmed leaf `SDDOORB` (open point 14.2) and a fence with the
  high-voltage plate (`SDHVLT1`, text-bearing, one machine, D27).
- `mod-engineer` / scaffolding: MAPINFO and LANGUAGE are in place (§11);
  nothing more is needed by the map.
- PM: §13.3.

### 13.6 The Dam set applied (2026-10-22)

Every stand-in of v1 replaced by the approved Dam set, as §7.2 says, with
the offsets of every face set by a post-build pass; the never-drawn proposed
names resolved to the nearest approved lump (`DAM_SET`), `SDGRIL1` left
pending. Geometry added: the gantry, four board strips, the signal post;
nothing on the route moved. Tests: `tests/test_map05_dam.py`, 79 (the Dam
set placed and resolved, nothing pending drawn, no v1 stand-in left, the
water, `SDDAM1` on one grid in y and x on every face, the wet banks and the
rack, the housings, the boards and consoles, the insulators masked and only
as middles, the signal once, the train's star); `tests/test_map05_route.py`
10, unchanged. `python tools/verify.py fast`: PASS (2779 tests, 229 skipped).
No engine run (D26): V11-V14 above. `docs/levels/shots/MAP05-overview.png`
predates the dressing (the plan is the same; the gantry, boards and signal
post are too small to show at that scale).

## 14. Open points for the CEO

1. **Walk v1** (§13.4).
2. **The blue gate's look**: `SDDOOR1` in blue light (the Dam set has no
   blue-trimmed leaf); ask the art-director for `SDDOORB`?
3. **The Hand Katyusha in S3 again** (MAP03 hid it in S1): keep it secret on
   the crest, or put it on the route for episode 2?
