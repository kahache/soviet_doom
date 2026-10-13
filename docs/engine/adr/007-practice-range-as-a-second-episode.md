# ADR 007 — The practice range is a second episode, reached from New Game

Date: 2026-10-13. Status: accepted, **not yet seen in the engine** (the PM's
batched engine pass, D26). Owner: `mod-engineer`.
Russian mirror: owed (D34), at the same path under `docs/ru/`.

Implements D41 (`docs/PRD.md`): "MAP02, the weapons test range, ships in v1
as a practice range, outside the campaign". The contract rows are in
`docs/engine/MOD-SPEC.md` §4.4 and §6.6.

## Context

MAP02 was built in F4 as an engineering fixture: every weapon on a rack,
the four ammo pools, barrels and targets, and since F5 a bestiary gallery.
Until D41 a player could only reach it with `MAP=MAP02 tools/run.sh` or the
`map MAP02` console command. The CEO played it ("todo correcto", D39) and
decided it ships, outside the campaign.

Two constraints from earlier decisions:

- **The menus are text since D31** (ADR 005): every item is a `TextItem`
  or `StaticText` reading `LANGUAGE` in the `SDMENU` font, bilingual
  through the language switch, and no Freedoom picture of an English word
  may come back.
- **`M_EPISOD` is a Freedoom graphic** (MOD-SPEC T12): "Which episode?"
  painted in English. The engine draws it on its episode screen, which it
  skips while the mod has a single episode.

## Options

| Option | What it is | For | Against |
|---|---|---|---|
| **A. A second MAPINFO episode** | `episode MAP02 { name = "$SD_EP02_NAME" }`; New Game then shows an episode screen, which we redeclare as text like the skill screen | engine-native, no ZScript; the skill screen still follows, so the range is played on a chosen difficulty; names come from `LANGUAGE`, so both languages for free; the item is a run-time text item in the menu's last font | every New Game gains one screen (with one episode the engine autoselected it); `M_EPISOD` must be kept out by redeclaring `EpisodeMenu` |
| B. A main-menu item "Practice range" | a seventh line on the main menu that starts MAP02 | one click from the title | a list-menu `TextItem` opens a MENU, not a command: starting a map needs a ZScript menu item class or an intermediate option menu with `Command "map MAP02"`, which bypasses the skill screen and starts on whatever skill the last game used; the main menu stops being the engine's six items, which D31 kept as a 1:1 copy |
| C. Leave it on the console | nothing to do | zero cost | not "shipped": a player who never opens the console never finds it |
| D. A door from MAP01 | a hub exit | in-world | breaks D5's one-map campaign end, and the range would no longer be "outside the campaign" |

## Decision

**A.** Specifically:

- **D-007-1.** `MAPINFO` declares two episodes, in this order: `MAP01`
  (`$SD_EP01_NAME`, key `s`) and `MAP02` (`$SD_EP02_NAME` = "Practice
  Range" / «Полигон», key `p`). The campaign comes first and is the
  default selection.
- **D-007-2.** `MENUDEF` redeclares `LISTMENU "EpisodeMenu"` with the skill
  screen's layout: `M_DOOM` at 60,0, one `SDMENU` header
  (`$SD_MNU_CHOOSEEPISODE`, "CHOOSE MISSION" / «ВЫБЕРИТЕ ЗАДАНИЕ») at
  32,70, then `Font "SmallFont", "Red", "Gold"` last, `LineSpacing 12`,
  `Position 32, 90`. The episode names are proper nouns under D22, so they
  are not drawn in `SDMENU`. The engine's `NetgameMessage "$NEWGAME"` is
  kept. `M_EPISOD` is not named, so it is never drawn.
- **D-007-3.** MAP02 gets its own cluster (2) and `next = endtitle`:
  leaving the range prints `SD_END02_TEXT` over `SDFLR1` and returns to the
  title. MAP01's `next = endtitle` is unchanged, and no map's `next` is
  MAP02, so the campaign never runs into the range. Both are pinned by
  `tests/test_practice_range.py`.

The header wording is a naming choice (taste, PIPELINE stage 4): it is one
`LANGUAGE` line in each language and costs nothing to change if the CEO
prefers another.

## Consequences

- One more screen on every New Game, campaign included. That is Doom's own
  behaviour for any game with episodes.
- `M_EPISOD` leaves the list of Freedoom pictures still in the shell (T12).
- `SDMENU` is now named by three descriptors, not two;
  `tests/test_menudef.py` pins exactly which.
- The redeclared `EpisodeMenu` joins debt T14: re-diff it against
  `gzdoom.pk3/menudef.txt` at every engine upgrade.
- MAP02 has no exit line (its geometry is `level-designer`'s). Today the
  player leaves the range through the menu; the cluster text is reached by
  a future exit switch or the `exit` console command.

## What was NOT decided here

- Whether the bestiary gallery, connected to nothing, should become
  reachable in the shipped range (a door, or a teleporter): `level-designer`.
- Whether MAP02's title, "Engineering Test Range", should change now that
  the episode is "Practice Range": both strings are one `LANGUAGE` line.
- `noskillmenu` on the range's episode, which would skip the skill screen:
  not used, because skill still changes damage taken and ammo given there.
