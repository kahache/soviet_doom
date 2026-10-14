# ADR 009 — The in-game credits are an option screen of ours, reached from Options

Date: 2026-10-13. Status: accepted, **not yet seen in the engine** (the PM's
batched engine pass, D26). Owner: `mod-engineer`. Amended 2026-10-14 by
D46: the CEO's answers to "What needs the CEO" (the disclaimer line is in,
the credits stay under Options).
Russian mirror: owed (D34), at the same path under `docs/ru/`.

Prepares gate G6 ("licence file, credits…", `docs/ROADMAP.md`). The
contract rows are in `docs/engine/MOD-SPEC.md` §6.8.

## Context

The mod had no credits screen. Since D43 it ships Jerry Engelbach's MIDI
sequence of *The Internationale* as the title music, and his licence obliges
a credit: `docs/sound/MUSIC-RIGHTS.md` §4.5 gives the line "to be reproduced
verbatim wherever the mod credits anyone" and lists "an in-game credits
screen" as G6 work. Besides that obligation the game should credit the
project itself and its two licences (`LICENSE.md`, D15), the engine it runs
on (GZDoom) and the base game data it needs (Freedoom, D2).

What the registers say on 2026-10-13:

| Party | Register | Obligation |
|---|---|---|
| Jerry Engelbach (title music) | `docs/art/LICENSES.md` § Music; MUSIC-RIGHTS §4.4, §4.5 | **credit required**, verbatim line in §4.5 |
| Freedoom 0.13.0 | `docs/art/LICENSES.md` § Base IWAD | BSD 3-clause; the mod references its lumps by name and **redistributes none**, so the BSD notice clause is not triggered. Credited because the game cannot run without it and its sprites and sounds are on screen as placeholders (MOD-SPEC §5.1) |
| GZDoom | — (not redistributed) | GPL 3.0; no notice owed by a mod. Credited as the engine |
| Soviet Doom project | `LICENSE.md` | ours: code GPL-3.0-or-later, assets CC BY-NC-SA 4.0. Stating the licence on screen is how a player learns the terms |
| OTEX, third-party packs | `docs/art/LICENSES.md` § Third-party packs | **none shipped** ("None used yet") |
| CC0 radio pieces (Peter Gerloff) | `docs/art/LICENSES.md` § Music (`D_SDRAD1`, `D_SDRAD2`); MUSIC-RIGHTS §4.5 | **shipped since 2026-10-13** with the diegetic radio (ADR 008, written the same day); CC0, so no obligation; credited as a courtesy, as MUSIC-RIGHTS §4.5 recommends |
| Pavel Zhukov's 1920 photograph (Lenin poster) | `docs/art/LICENSES.md` § Reference material | public domain; no obligation. Credited as a courtesy |
| Impact, Arial Narrow Bold (rasterised text) | `docs/art/LICENSES.md` § Fonts | none: only pixels ship |

Two constraints from earlier decisions:

- **The CEO approved the text menu (D31, D32).** The main menu, the skill
  screen and (D41) the episode screen are his approved look; a new row on
  any of them changes it and needs his word.
- **Every in-game string ships in English and Russian in the same task**
  (D7, D21), from `LANGUAGE`.

## Options

| Option | What it is | For | Against |
|---|---|---|---|
| A. The engine's help screen ("Read This!", F1) | Doom's help key opens `ReadThisMenu`, which draws the pictures named by `GameInfo { infopage = … }` (`gzdoom.pk3:mapinfo/doomcommon.txt`: `"HELP", "CREDIT"`) | no menu changes at all; F1 is where Doom players look | it draws **pictures**, not text: the credits would be painted per language by `art-director` and re-painted at every new credit, and per-language pictures need the localized-texture mechanism the project has never used (D31 parked it). A text version needs a ZScript `helpmenuclass`. On Freedoom the main menu's "Read This!" row is hidden (`drawreadthis` is off for Doom II), so F1 is the only way in |
| B. A text screen after the campaign's end | a second text screen after `SD_END01_TEXT`, through a MAPINFO `Intermission` block chained from MAP01's `next` | Doom's own place for text; no menu change | only a player who **finishes** sees it, which does not meet "wherever the mod credits anyone"; MAP02 ends separately; the chaining syntax and whether a `TextScreen` resolves a `LANGUAGE` id are **NOT VERIFIED** here (the M3 note in `MAPINFO` shows how wrong a guessed end-sequence syntax goes); changing `SD_END01_TEXT` itself would rewrite the approved ending |
| **C. A "CREDITS" row on the main menu** | `GameInfo { drawreadthis = true }` and the existing `IfOption(ReadThis)` row relabelled and pointed at a credits screen, or a seventh `TextItem` | the most visible; one keypress from the title | **changes the CEO's approved menu (D31/D32)**: one more row in `SDMENU`, and the column moves up (`Position 97, 64` with ReadThis on). Needs his visto bueno |
| **D. An option screen of ours, reached from Options** | `OptionMenu "SD_CreditsMenu"`, one `Submenu` row on our existing `SD_OptionsMenu` (Options → Soviet Doom → Credits) | no approved screen changes; option menus centre `StaticText` rows and draw them in the engine's `NewSmallFont`, which has Cyrillic of its own; scrolls with the wheel and Page Down; pure `MENUDEF` + `LANGUAGE`, no ZScript | two levels deep: a player has to look for it. The text cannot wrap, so every line is its own `LANGUAGE` id |

## Decision

**D now, C proposed to the CEO.** Specifically:

- **D-009-1. The screen.** `MENUDEF` declares `OptionMenu "SD_CreditsMenu"`
  with `Title "$SD_CRED_TITLE"` and one `StaticText` row per screen line;
  each block opens with a header row (`StaticText "$SD_CRED_H_…", 1`, the
  engine's header colour, the same form as its own
  `StaticText "$SCALEMNU_OVERRIDE", 1`) and blocks are separated by a blank
  row. `SD_OptionsMenu` gains a blank row and
  `Submenu "$SD_CRED_TITLE", "SD_CreditsMenu"` under the language help. The
  main, skill and episode screens are untouched;
  `tests/test_credits.py` fails if any of them links the credits.
- **D-009-2. The text.** `LANGUAGE` holds the credits as `SD_CRED_*` ids in
  `[enu default]` and `[ru]`, one id per line of at most 40 characters,
  the same ids in the same order in both languages. Blocks, in order: the
  team (the Soviet Doom project and its two licences), music (Engelbach,
  then Gerloff's radio songs),
  engine (GZDoom), game data (Freedoom), sources (Zhukov). The obligatory
  line is second so it is on the first screen without scrolling. Since
  D46 the team block also carries the CEO's disclaimer, "A fan project,
  not affiliated with id Software" / «Фанатский проект, не связанный с
  компанией id Software» (`SD_CRED_FAN_1`, `_FAN_2`), right under the
  project's name. Jerry
  Engelbach's line is MUSIC-RIGHTS §4.5's, word for word, split across
  seven ids; the Russian keeps his name in Latin as well, "Джерри Энгельбах
  (Jerry Engelbach)", as `LICENSE.md` does. The team is named "the Soviet
  Doom project", the author name the licence register uses
  (`docs/art/LICENSES.md`; `LICENSE.md` itself says "Soviet Doom").
- **D-009-3. The registers drive the test.** `tests/test_credits.py` reads
  `docs/art/LICENSES.md` (every table with a Licence column) and the
  Obligation column of MUSIC-RIGHTS §4.5, and demands that every name they
  oblige us to credit is in the credits of both languages. A row needs a
  credit when its licence cell says *credit*, `{{Attribution}}`, CC BY,
  BSD, MIT or OFL, and it is not our own work (D15). **CC0 counts too**:
  CC0 needs no credit, but the project credits its sources (MUSIC-RIGHTS
  §4.5 recommends it for Gerloff), so a shipped CC0 row must name its
  author in bold and the credits must carry it. This caught its first case
  while this ADR was written: the radio's `D_SDRAD1` / `D_SDRAD2` rows
  landed in the register and the suite went red until the Gerloff lines
  (`SD_CRED_MUSIC_8`, `_9`) existed. A row that needs a credit
  and names nobody in bold (or as `credit "X"`) fails the suite: the
  register must say whom. Engelbach's verbatim line is checked character
  for character against the English credits.

## Consequences

- One more row on our own options screen; nothing on the CEO's screens.
- Adding a third-party asset now has three steps, not two: its row in the
  register (already enforced by `tools/check_pk3.py`), and, if its licence
  obliges a credit, `SD_CRED_*` lines in both languages — the suite says
  which name is missing.
- The credits are prose split into 40-character ids. Rewording a sentence
  means re-splitting it in both languages; the line test catches overflow.
- F1 still shows Freedoom's own `HELP` and `CREDIT` pictures
  (`freedoom2.wad` has both lumps; checked 2026-10-13 by reading the WAD
  directory). They are Freedoom's credits, in English, and not ours to
  replace without art (option A); harmless, and arguably part of crediting
  Freedoom.
- `MOD-SPEC` §6.8 is the contract; debt T14 does not grow (no engine menu
  is redeclared).

## Not verified (the PM's engine pass)

- That the screen opens from Options → Soviet Doom → Credits, in both
  languages, and the header rows take a distinct colour.
- **That a 40-character line fits.** The limit assumes `NewSmallFont`'s
  8-px cells (the engine's hex font, `newconsolefont.hex` in
  `gzdoom.pk3`) and a clean width of about 400 at the narrowest common
  resolutions; neither is measured. Check the longest lines,
  `SD_CRED_MUSIC_9` [ru] (40 characters), `SD_CRED_ENGINE_1` [ru] (37) and
  `SD_CRED_MUSIC_9` [enu] (37), at 1920×1080 and at a 4:3 mode such as
  1600×1200.
- Scrolling: wheel and Page Down should scroll a menu with no selectable
  row (`optionmenu.zs`, `OnUIEvent` and `MenuEvent`); the arrow keys will
  not. How many rows fit on the first screen.
- That «» and the Cyrillic print in `NewSmallFont` (they should: it is the
  engine's Unicode font).
- Since D46 the team block is two rows longer (the disclaimer), so
  Engelbach's lines start two rows lower: check that they are still on
  the first screen at 1920×1080 and at a 4:3 mode, in both languages.

## What needed the CEO — decided in D46 (2026-10-14)

- **Option C**: a "CREDITS" / «АВТОРЫ» row on the main menu, which changes
  his approved look (D31/D32). Cost: one `MENUDEF` line, one `LANGUAGE` id
  per language, and the column moving 8 px up; it would be drawn in
  `SDMENU` like the other rows. Recommendation was: yes, at G6, if a player
  test shows nobody finds the credits under Options. **Decided by the CEO
  in D46: the credits stay under Options** (option D as built);
  `tests/test_credits.py` keeps them off his approved screens. A player
  test at G6 that shows nobody finds them would be a reason to ask again,
  not a standing plan.
- A "fan project, not affiliated with id Software" line is common in
  Doom mods; it is a public, legal statement, so it was not added without
  him. **Decided by the CEO in D46: it is added.** English "A fan project,
  not affiliated / with id Software." and Russian «Фанатский проект, не
  связанный / с компанией id Software.» («компанией» as in
  `SD_CRED_ENGINE_4`), two rows under the project's name in the team
  block; `tests/test_credits.py` pins the sentence there in both
  languages. The Russian wording is NOT VERIFIED by a native reader
  (`translator-ru`'s batch, D34).
