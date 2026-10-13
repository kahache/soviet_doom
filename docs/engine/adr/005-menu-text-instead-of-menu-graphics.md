# ADR 005 — The main menu and the skill screen are text in our font, not graphics

Date: 2026-10-13. Status: accepted, **not yet seen in the engine** (the PM's
batched engine pass, D26). Owner: `mod-engineer`.
Russian mirror: `docs/ru/engine/adr/005-menu-text-instead-of-menu-graphics.md`.

Implements D31 (`docs/PRD.md`): "the main menu and the skill-screen headers
become text in our alphabet, with D22's letterforms in English" (treatment
B). Builds on ADR 004 (D-004-6: the redeclared `MainMenu`) and pays most of
debt T12. The contract rows are in `docs/engine/MOD-SPEC.md` §6.6.

## Context

Doom's main menu is six pictures of English words (`M_NGAME`, `M_OPTION`,
`M_LOADG`, `M_SAVEG`, `M_RDTHIS`, `M_QUITG`) and the skill screen two more
(`M_NEWG`, `M_SKILL`). Under our logo they were Freedoom's red Doom
lettering, they could not follow the language switch (ADR 004), and on the
skill screen they sat on the name painted into `TITLEPIC`.

## Options

| Option | What it is | Against |
|---|---|---|
| A. Keep the graphics | nothing to do | not our type; English in the Russian build |
| **B. Text items in a font of ours** | `TextItem` / `StaticText` reading `LANGUAGE`, drawn in one folder font | the look depends on a font colour translation we have not seen yet |
| C. Our own graphics, one set per language | `art-director` paints `M_NGAME` etc. twice | twice the art, and a per-language graphic needs GZDoom's localized-texture mechanism, which we have never used; parked by the CEO (D31) |

The CEO chose B ("Vamos con B a ver q tal queda").

## Decision

### D-005-1 — `TextItem` replaces `PatchItem`, item for item

Each `PatchItem "M_xxx", key, menu[, 0]` becomes
`TextItem "$SD_MNU_xxx", key, menu`. Hotkeys, target menus, the
`IfOption(SwapMenu)` and `IfOption(ReadThis)` branches, `LineSpacing 16` and
`Position` are kept, so the redeclared menu still behaves like the engine's.

The syntax is not from memory. GZDoom 4.14.2's `gzdoom.pk3/menudef.txt`
uses exactly this form in its own `LISTMENU "MainMenuTextOnly"` (line 129,
`TextItem "$MNU_NEWGAME", "n", "PlayerclassMenu"`) and in the Heretic/Hexen
branch of `MainMenu` (line 98). `ListMenuItemTextItem.Init(desc, text,
hotkey, child, param = 0)` in `zscript/engine/ui/menu/listmenuitems.zs`
(line 273) takes the descriptor's font, normal colour and selected colour
when the item is parsed.

### D-005-2 — One font, `SDMENU`, for both languages

`Font "SDMENU", "Cream", "Gold"`. `SDMENU` is `bigfont` with five Latin
capitals drawn as Cyrillic letters (D22 level 2). Russian strings use
Cyrillic code points, which the font does not alter, so a single font and a
single `MENUDEF` serve both languages, and switching `language` needs
nothing from us.

Why a font of our own and not `BigFont`: `menuDelegate.PickFont()`
(`menucustomize.zs` line 25) swaps `SmallFont` and `BigFont` for their
"alternative" versions on its own; a font with another name is drawn as
named. And D22 must not reach the level names and pickups that `BigFont`
prints.

Why `Cream` / `Gold`: the glyphs are red with a dark shadow, and the menu
background is the red `TITLEPIC`; untranslated, it would be red on red.
Both names are engine colours (`gzdoom.pk3/textcolors.txt`, lines 141 and
51). Translating a font by colour name is how the skill ladder already
shows its `Gold` highlight (`docs/qa/evidence/2026-10-13_0955_F2_skill-ladder-en.png`),
but that is `SmallFont`, Freedoom's glyphs extended by ours. Whether a font
made only of our full-colour PNGs translates the same way, and how `Cream`
looks on `SDMENU`, is **NOT VERIFIED** until the engine pass.

Strings are written in capitals, because the font has none of its own
lowercase and we have not verified what GZDoom does with lowercase in a
capitals-only folder font.

### D-005-3 — The skill screen keeps the logo and has one header

`StaticPatch 60, 0, "M_DOOM"`, `StaticText 32, 70, "$SD_MNU_CHOOSESKILL"`
in `SDMENU`, rungs at `Position 32, 90` in `SmallFont`. `art-director`'s
layout: the two stock headers at (96,14) and (54,38) collide with the
painted name; "New Game" is dropped because the player has just chosen it.

`StaticText x, y, text` is the engine's own form (`menudef.txt` line 217,
Strife's episode header). Changing `Font` between items inside one menu is
also the engine's own (`ListMenu "PlayerMenu"`, lines 458–459: a header,
then `Font "SmallFont"` for the rest). It matters here because static
items take the font when parsed, while the five rungs are built at run
time from MAPINFO in whatever font the descriptor ends with — so
`SmallFont` must come last.

x = 32 because rung 5 is 288 px in `defsmallfont` and the skull selector
is drawn 32 px to the left of the rungs: 32 is the only column where both
the longest rung and the skull fit on a 320-wide, 4:3 screen.

## Consequences

- `LANGUAGE` gains seven `SD_MNU_*` ids in both sections.
- `MENUDEF` no longer names any Freedoom menu graphic except through the
  engine's own `DEFAULTLISTMENU` (the skull cursor). T12 is open only for
  the cursor, the pause sign and `M_EPISOD` (MOD-SPEC §10).
- The package now depends on `fonts/sdmenu/`. `tools/check_pk3.py` fails
  when `MENUDEF` names a font that is neither the engine's nor packed, and
  `tests/test_menudef.py` checks glyph coverage and widths against
  `assets/fonts/sdmenu/`.
- If the CEO dislikes the result on screen, the way back is one block of
  `MENUDEF` per menu; the strings stay.

## What was NOT decided here

The colours are a proposal for the CEO to judge on screen; changing them is
one word each. Whether the engine ever swaps in its own `MainMenuTextOnly`
(MOD-SPEC §6.6) is open; the Russian evidence so far says it does not.
