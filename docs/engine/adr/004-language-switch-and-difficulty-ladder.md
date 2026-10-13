# ADR 004 — The language switch, the difficulty ladder, and where a menu is allowed to write

Date: 2026-10-13. Status: accepted, verified in-engine on GZDoom 4.14.2 +
Freedoom 0.13.0. Owner: `mod-engineer`.
Russian mirror: `docs/ru/engine/adr/004-language-switch-and-difficulty-ladder.md`.

Supersedes nothing. Records the decisions behind `src/lumps/MENUDEF`, the
`skill` blocks of `src/lumps/MAPINFO`, and the removal of
`src/zscript/sd/language.zs`.

## Context

The CEO asked for two player-facing things: five difficulty levels carrying
the names in `docs/product/DIFFICULTY-NAMES.md`, and an in-game switch
between English and Russian that is remembered next time. Both are menu
work, and the menu is the part of GZDoom with the most rules that are
nowhere in the wiki. Four of them cost this project real time, and the first
one cost the CEO a game that would not start, so they are written down here
with the engine source line that proves each.

## Decisions

### D-004-1 — The ladder replaces Doom's five skills, it does not rename them

`clearskills`, then five `skill` blocks of our own, each with
`Name = "$SD_SKILL_n"` and **no `PicName`**.

Redefining a skill of the same name MERGES into the engine's definition, and
GZDoom's `mapinfo/doomcommon.txt` gives every stock skill a `PicName`
(`M_JKILL`, `M_ROUGH`, `M_HURT`, `M_ULTRA`, `M_NMARE`). A `PicName` makes the
menu draw the IWAD's GRAPHIC and ignore `Name` entirely, so a merge would
have shown the player Freedoom's "Hurt me plenty" under our id. Clearing and
redeclaring is the only way the five names reach the screen.

**Every mechanical property is copied verbatim from `doomcommon.txt`.**
Renaming a rung must not rebalance it: rung 5, "Hero of the Soviet Union,
posthumously", is Nightmare in full — `RespawnTime = 12`, `FastMonsters`,
`InstantReaction`, `DisableCheats`, `AmmoFactor = 2`,
`SpawnFilter = Nightmare` — because the joke in the name is that the award
is posthumous and the enemy dead do not stay dead. If the mechanics ever
drift from Doom's, the reason belongs in `docs/engine/BALANCE.md`.
`tests/test_language.py::DifficultyLadderTest` holds that contract.

### D-004-2 — The switch drives GZDoom's own `language` CVar; the mod declares no CVar

`language` is already archived by the engine: it is written to the player's
`gzdoom.ini` and read back next launch. That is exactly the persistence
asked for, in the file a player expects their settings to live in, and it
keeps the mod's footprint in their config at **one key**. A CVar of our own
would be a second source of truth and a second thing written to their
machine. There is deliberately no `CVARINFO` lump, and a test fails if one
appears.

### D-004-3 — `OptionString`, never `OptionValue` (bug E3a — the game would not launch)

GZDoom picks the list directive by the CVar's TYPE. `OptionValue` parses its
left column as a NUMBER; `OptionString` parses it as a string. `language` is
a string CVar, so the `OptionValue` spelling sends `"default"` to
`SC_GetFloat` and the engine **aborts during startup** — exit 255, the log
stopping at `M_Init: Init menus.`, no title screen, no game. The CEO hit
this. One keyword, whole product down.

### D-004-4 — "auto" is offered as a third value; no ZScript writes the CVar (bug E3b)

An `OptionString` row whose CVar holds a value outside its list has nothing
to draw and GZDoom prints "Unknown". Every config that has never been
touched holds `language = auto`, so the row read "Unknown" on a fresh
install.

The first fix was a ZScript `OptionMenu` subclass that overwrote "auto" with
the code auto had already resolved to, probing the active section through a
string id (`SD_LANG_CODE`) defined once per `LANGUAGE` section. It worked
when a player walked into the screen and **aborted the VM** otherwise:

> VM execution aborted: Attempt to change CVAR 'language' outside of menu code

ZScript may write a CVar only while the engine is handling menu INPUT. In
4.14.2 `DMenu::InMenu` is raised around exactly three calls — `OnUIEvent`,
`OnInputEvent` and `MenuEvent` (`src/common/menu/menu.cpp:276-327`) — and
around nothing else. `Init`, `Ticker` and `Drawer` all run with
`InMenu == 0`; both were tried in-engine on 2026-10-13 and both aborted.
Walking in from the Options screen survived only because the submenu is
constructed inside the PARENT menu's `MenuEvent`, i.e. by nesting, not by
design. `openmenu SD_OptionsMenu` from the console killed the game outright
— reproduced repeatedly while taking the screenshots for this change. Any
other route that builds the menu outside input handling does the same; which
routes those are is **NOT VERIFIED** beyond the console one, and finding out
on a player's machine is not a plan.

**Decision: stop writing the CVar and declare the value instead.** The list
is `auto` / `default` / `ru`, the class and the probe id are deleted, and
nothing of ours can abort. Choosing English or Russian still writes
`language` — through the engine's own `Option` row, during input handling,
where it is legal — and the engine archives it.

Cost, accepted: the row now reads "Automatic (system)" on a fresh install
instead of silently resolving to "English". That is the truth about the
player's config, and it is one word of explanation instead of a crash path.

### D-004-5 — The entry is added to BOTH options screens, in the middle (bug E2)

GZDoom ships two options screens: the long `OptionsMenu`
(`gzdoom.pk3/menudef.txt`) and a short `OptionsMenuSimple`
(`gzdoom.pk3/menudef.zsimple`). The item picks between them when it is
activated:

```
case NAME_Optionsmenu:
    if (m_simpleoptions) menu = NAME_OptionsmenuSimple;
                              -- src/menu/doommenu.cpp:271 (g4.14.2)
```

`m_simpleoptions` is archived and defaults to **true**, so on a fresh
install "Options" opens the SHORT screen. The mod's entry was appended to
the long one only, and the player could not reach it at all — found
in-engine, not by reading.

Appending to both was still wrong: each screen already fills the 200-line
virtual screen, and the new row landed under the last visible one. The entry
is therefore inserted `BEFORE "os_Menu"` (the Option Search item, present on
both screens), which puts it in the middle of the list. The engine matches
on an item's action and silently appends when it finds no match
(`GetInsertIndex`, `src/common/menu/menudef.cpp:802`), so a renamed anchor
degrades instead of breaking.

`AddOptionMenu` on a name the engine does not define is a hard parse error
(`"%s is not an option menu that can be extended"`, same file, line 1249).
Naming `OptionsMenuSimple` therefore pins us to a GZDoom that still has it —
debt T13.

### D-004-6 — The main menu logo is positioned by us, not by the engine (bug E1)

`art-director` draws the name lockup into `TITLEPIC` and ships the same
lockup loose as `M_DOOM`, recording in the generator's manifest
(`work/art/shell/manifest.json`, gitignored, so not in every clone) that
the loose copy belongs at x=60, y=0. Since 2026-10-13 (PMO-10) the contract
for those two numbers is the table in `docs/engine/MOD-SPEC.md` §6.6, and
the manifest is evidence only. Measured 2026-10-13: overlaying
`assets/graphics/shell/M_DOOM.png` on `TITLEPIC.png` at (60,0) gives a mean
per-channel difference of 6, against 22 or more at every neighbouring
offset. The art is exact.

GZDoom was never told. Its own `LISTMENU "MainMenu"` says
`StaticPatch 94, 2, "M_DOOM"`, so the menu logo sat 34 px right and 2 px
below the block painted into the title screen, and a "CO" of the latter
showed past its left edge (the CEO spotted it in
`docs/qa/evidence/2026-10-13_0100_F2_title-and-menu.png`).

There is no directive that moves one item of an existing list menu:
`ADDLISTMENU` only appends, which would have drawn a second logo beside the
misplaced one. Redeclaring a `LISTMENU` replaces the engine's descriptor
outright (verified in-engine: five items, not ten), so `MENUDEF` now carries
a copy of GZDoom's `IfGame(Doom)` main menu with the one number changed.
**Consequence:** that copy must be re-diffed against
`gzdoom.pk3/menudef.txt` whenever the engine is upgraded — debt T14.

## Consequences

- `src/zscript/sd/language.zs` is deleted and `SD_LANG_CODE` is gone from
  `LANGUAGE`. The mod ships no menu ZScript at all.
- The player's config gains exactly one key, `language`, and only when they
  choose a language.
- `MENUDEF` now contains three verbatim copies of engine data (the main
  menu body, and the two `os_Menu` anchors). Each is commented with the
  file and line it came from. They are the price of changing one number in
  a `protected` menu.
- The Russian menu is correct and unreadable until the Cyrillic glyphs land
  (debt T9). The language row carries a temporary line that says so, with
  the id to delete when the font arrives. **Closed 2026-10-13:** T9 was
  paid by D24 (`fonts/defsmallfont/`, `fonts/bigfont/`, 214 glyphs) and the
  temporary line, `SD_OPTMNU_LANGWARN`, is deleted from `LANGUAGE` and
  `MENUDEF` (PMO-10).

## What was NOT decided here

Whether `language` should default to Russian on a Russian-locale machine:
with "auto" in the list that is now the engine's behaviour and the player
can override it. If the CEO wants the mod to force one language, that is a
product decision and it changes `SD_LanguageValues`, not any code.
