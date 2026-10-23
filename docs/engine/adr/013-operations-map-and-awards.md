# ADR 013 — The operations map between levels and the end-of-episode awards

Date: 2026-10-23. Status: **proposed** (V3, D120's B1 and B3), built on the V3
branch, **not yet seen in the engine** (the PM's batched pass, D26) and **not
yet seen by the CEO**: the awards are Soviet decorations, political symbols
that D113's standing approval does not cover, so the CEO decides on
`docs/art/previews/2026-10-23_V3_ops-map-medals.png` before the PM takes this
into a release. Owner: `mod-engineer` (with the art as `art-director`).
Contract: `docs/engine/MOD-SPEC.md` §6.13; thresholds `BALANCE.md` §9.

## Context

D120 put two intermission features in V3. **B1:** between two maps, a map of
the USSR on which a red arrow advances from operation to operation (Zarya-7 →
the metro → Tankograd → the Trans-Siberian → the Volga dam → Red Square →
Novaya Zemlya → Severomorsk → Tunguska), the current position marked, living
with the stats screen (kills, items, secrets, time). **B3:** at the end of an
episode (MAP03, MAP06, MAP09), Soviet medals drawn procedurally, earned by
kills, secrets and time/skill, with their names in the three languages and
their rules; no portraits of real people.

Today every map's stats screen is Doom's `DoomStatusScreen` over `INTERPIC`
(D18), then the cluster's text (MOD-SPEC §4.6). What the engine offers,
read in GZDoom g4.14.2's own files (gzdoom.pk3, gzdoom.exe's strings):

- **MAPINFO `exitpic` / `enterpic`** per map: the background of the stats page
  after it, and of the "Entering" page before it. A name that begins with
  `$` is an **intermission script** (`DInterBackground::LoadBackground`), the
  language of Doom 1's animated episode maps (gzdoom.pk3 `in_epi1.txt` …
  `in_epi3.txt`): `Background`, `Screensize`, `Splat`, `Pointer`,
  `Spots { MAP x y }`, and pictures or animations shown `IfLeaving` /
  `IfEntering` / `IfVisited` a map (and `Not` and `Travelling` forms). The
  engine draws the background and its pictures under the stats, and on the
  "Entering" page adds the splat on every visited site and a blinking
  pointer on the next one (`drawBackground(CurState, drawsplat,
  snl_pointeron)`, `zscript/ui/statscreen/statscreen.zs`).
- **MAPINFO `Intermission` blocks** (`Image`, `TextScreen`, `Fader`, `Cast`…,
  reached by `next = endsequence`-style ends): static pictures and text,
  nothing computed.
- **GameInfo `statscreen_single`**: the class of the single-player stats
  screen, `DoomStatusScreen` in `mapinfo/doomcommon.txt`; a ZScript subclass
  can change any of its virtual steps. At the last map of an episode its
  `initShowNextLoc` ends the screen at once (`wbs.next == ""`: "Last map in
  episode - there is no next location!").

## Options

**B1, the map.**

1. **An intermission script** named by every campaign map's `exitpic` and
   `enterpic`. Data only, the engine's own mechanism since Doom 1, drawn
   under the untouched stats.
2. **A ZScript stats screen that draws the map itself.** Free animation
   (an arrow that grows), but it re-implements what the engine already draws
   and must be kept in step with the stats layout by hand.
3. **A MAPINFO `Intermission` per transition.** A separate screen after the
   stats, nine pictures with the arrow baked in; no live "where you are",
   and a second screen between every two maps.

**B3, the medals.**

1. **An `Intermission` block per episode with fixed pictures.** Cannot know
   what the player earned.
2. **A page inside our own `statscreen_single` subclass**, shown after the
   stats of an episode's last map, before the cluster's ending text.
3. **An `EventHandler` overlay drawn during the intermission.** The stats
   screen is a ScreenJob, not the level: `WorldTick` and `RenderOverlay`
   belong to the level's loop (read in the engine's scripts, NOT VERIFIED in
   a run), so nothing would draw it reliably.

And for the figures a medal needs (three maps, but the stats screen knows
only the map just finished):

- **a CVar** — global, not saved: loading an old save would keep new figures;
- **a static thinker** — survives map changes, but not obviously New Game;
- **an inventory item the player carries** — travels with the player between
  maps (`PlayerPawn.PlayerFinishLevel` keeps every item with
  `InterHubAmount >= 1`), saved with the player, gone with New Game.

## Decision

- **B1: option 1, an intermission script, `SDOPSCR`**, named as `exitpic` and
  `enterpic` by MAP01–MAP09 (the range has no intermission). It is generated,
  with all of its pictures, by `tools/art/gen_ops_map.py`, the one source of
  the coordinates: background `SDOPMAP` (320×200, our own outline of the USSR,
  `tools/art/opsmap_geo.py`, Lambert conic, magnified round the Urals so the
  four Ural operations stand apart; the top 30 px left as sea for the
  engine's map name and "Entering"), the red arrow into each map
  `SDOPR02`–`SDOPR09`, the taken-site star `SDOPSTAR` (also the `Splat`),
  the pulse `SDOPCUR0/1` where the player is, and the "you are here" ring
  `SDOPYAH0` (the `Pointer`, blinked by the engine). **Progress is told only
  by the map being left or entered (`IfLeaving` / `IfEntering`), never by
  `IfVisited`**, and every picture that must show on both pages is listed
  twice, as the engine's own `in_epi2.txt` warns: a player who starts episode
  2 from New Game still sees the road from Zarya-7 as travelled, which is the
  story. No text on any picture: the stats screen prints the names, in the
  player's language, in our fonts, as before.
- **B3: option 2, `SD_StatusScreen : DoomStatusScreen`** (GameInfo
  `statscreen_single`), which keeps the stats page as Doom draws it and
  overrides only `initShowNextLoc`, `updateShowNextLoc` and `drawShowNextLoc`:
  at the last map of an episode (`wbs.next == ""` and level number 3, 6 or 9)
  it stays in the ShowNextLoc state and draws the **awards page** over the
  dimmed map — the title, the episode's name, its kills, secrets, time and
  par, and five rows (picture, name, rule) revealed one by one with Doom's
  own intermission sounds; a key reveals all, the next leaves; then the
  cluster's ending text and the title screen as before. Every other map
  keeps Doom's "Entering" page.
- **The figures: an inventory item, `SD_CampaignLedger`**, one slot per map
  level number, written every tic by the play-side `SD_AwardsRecorder`
  (`AddEventHandlers`) from the level's counters (`killed_monsters`,
  `total_monsters`, `found_secrets`, `total_secrets`, `time`, `partime`, and
  the skill's SpawnFilter); the stats screen only reads it, and takes the
  last map's figures from its own `wbs`, exactly what the stats page showed.
- **The five awards** (`tools/art/gen_medals.py`, 24×30, no lettering):
  Medal "For Courage" (`SDAWCOU`, the episode completed), Order of the Red
  Star (`SDAWRST`, kills), Order of the Red Banner (`SDAWRBN`, secrets — the
  brief's example), Order of the Patriotic War (`SDAWPTW`, time), Gold Star of
  the Hero of the Soviet Union (`SDAWHER`, all of it on skill 3 or harder).
  Thresholds `BALANCE.md` §9: 75 % kills, 100 % secrets, within the summed
  par, and for the Gold Star 90 % kills, every secret, par, skill 3+ and the
  whole episode played. **Not drawn:** the Order of Lenin (Lenin's profile:
  no portrait of a real person, the brief) and the Order of Glory, whose
  orange-and-black ribbon is today read as a political emblem of its own;
  the Order of the Patriotic War takes time instead. The Red Star's soldier
  is a plain disc (no figure at all at this size).

## Consequences

- The stats screen of every campaign map changes background: the ops map
  replaces `INTERPIC`, which stays packed (it is the engine's default for
  any other map). The stats text is drawn over the map, as Doom 1 drew it
  over its episode maps; the map is kept dark enough for the red figures.
- A new GameInfo key (`statscreen_single`) and a fourth event handler. Coop
  and deathmatch keep the engine's screens (no awards there).
- The player's inventory carries one invisible item (no icon, not in the
  inventory bar, undroppable, not cleared by `ClearInventory`).
- **Edge cases.** A death that restarts a map from scratch is a new game in
  the engine (`G_InitNew`, MOD-SPEC §6.10) and starts a new ledger: the
  earlier maps count as not played (only the Gold Star needs them all).
  Warping to an episode's last map gives the awards over that map alone.
  Par times are placeholders (MAPINFO), so the Patriotic War is only as
  fair as they are (debt in `BALANCE.md` §9).
- 15 new LANGUAGE ids in `[enu default]`, `[ru]` and `[ca]`; every character
  drawn by our fonts, every line fitted to the page (`tests/test_awards.py`).
- `SDOPSCR` is a generated file in `src/lumps/`: edit the generator, run it
  with `--install`; `tests/test_ops_map.py` turns red if they differ.

## Verification (the PM, D26)

**NOT VERIFIED in the engine.** What rests on reading and not on a run:
that `exitpic = "$SDOPSCR"` resolves the root lump by its short name (the
engine's own `$IN_EPI1` does the same with gzdoom.pk3's root `in_epi1.txt`);
that `Pic` and the pointer honour the PNGs' grAb offsets (the engine's
`drawOnLnode` subtracts them for its fit test); that the level and the
player's inventory still exist while the stats screen runs; that
`G_SkillPropertyInt(SKILLP_SpawnFilter)` returns the filter bit (Normal = 4);
that `DTA_ColorOverlay` darkens the unearned awards. The engine pass: finish
MAP01 (the pulse on Zarya-7, then "Entering" the metro with the arrow and the
blinking ring), MAP03 (stats, then the awards page, then the ending text),
start episode 2 from New Game and finish MAP04 (the road from Zarya-7 drawn),
at 320×200 and at 16:9, in English, Russian and Catalan; the log must stay
clean (no "Unknown texture", no script error). `tests/test_ops_map.py` and
`tests/test_awards.py` hold everything that can be held offline.
