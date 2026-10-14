# ADR 010 — The pause sign follows the language, drawn by a status bar of ours

Date: 2026-10-14. Status: accepted, **not yet seen in the engine** (the PM's
batched engine pass, D26). Owner: `mod-engineer`. Pays debt T24
(`docs/engine/MOD-SPEC.md` §10). The contract rows are MOD-SPEC §6.5.1.
Russian mirror: owed (D34), at the same path under `docs/ru/`.

## Context

D48 approved the pause sign **P2**, "a plaque per language": «PAUSE» in
English, «ПАУЗА» in Russian, both 77×20 (`work/art/shell_extra/pause_P2_en.png`,
`pause_P2_ru.png`). The English plaque ships as `graphics/M_PAUSE.png`. The
Russian one was meant to ship as a **localized variant**,
`localized/textures/M_PAUSE.ru.png`, which the packer and `check_pk3` have
handled since commit `5231098`.

The engine pass then found what reading GZDoom g4.14.2's source confirms
(tag `g4.14.2`, checked out in the scratchpad, 2026-10-14):

- `FTextureManager::AddLocalizedVariants` (`src/common/textures/texturemanager.cpp`)
  registers the variant and checks its size, but the line that would swap
  it in at draw time, in `ResolveTextureIndex` (`texturemanager.h`), is
  commented out. The variant table is only read by `OkForLocalization`,
  which decides whether a **menu** graphic gives way to text.
- `D_Display` (`src/d_main.cpp`, lines 1095-1123) draws the pause sign
  with `TexMan.GetGameTextureByName(gameinfo.PauseSign, true)`, which does
  no localization. In Russian the player sees the English plaque.
- Before drawing, the same block calls the status bar's virtual
  `DrawPaused(paused - 1)` and **skips its own drawing if it returns true**
  (`gzdoom.pk3:zscript/ui/statusbar/statusbar.zs`, line 239: "let the HUD
  handle drawing the pause graphics", default `return false`).

The constraint the CEO cares about: the status bar is on screen all the
time, and it must not change. Today it is `DoomStatusBar`
(`gzdoom.pk3:mapinfo/doomcommon.txt`, `statusbarclass = "DoomStatusBar"`;
`statusbar = "sbarinfo/doom.txt"` is commented out there).

## Options

| Option | What it is | For | Against |
|---|---|---|---|
| A. Wait for the engine | keep the variant; hope a later GZDoom re-enables the substitution | no code | the Russian game shows the English plaque until then; nothing says it will come back |
| B. One plaque per build | ship `M_PAUSE` as the Russian plaque in a Russian build | no code | the mod is one PK3 with a language switch (ADR 004); two builds break D21's in-game switch |
| C. `GameInfo { PauseSign }` per language | name another graphic in MAPINFO | one line | `GameInfo` is not per language: one value for both |
| **D. A status bar subclass that overrides only `DrawPaused`** | `SD_StatusBar : DoomStatusBar`, registered by `GameInfo { StatusBarClass }`; `DrawPaused` draws the graphic a `LANGUAGE` id names, at the engine's position, and returns true | uses the hook the engine provides for this; one virtual, everything else inherited, so the bar is Doom's; the language follows the player's choice through `LANGUAGE` | a class of ours in the status bar's place: if a GZDoom upgrade renames `DoomStatusBar` or drops `DrawPaused`, the ZScript does not compile (T13); the drawing copies `D_Display`'s and does not track it (T14) |
| E. Our own status bar (`SBARINFO` or a `BaseStatusBar` subclass drawn from scratch) | MOD-SPEC §6.5's "Own status bar" | full control | redraws the bar the CEO sees all the time to fix a picture he sees when paused; that choice is open for F6 (§6.5, T11) and is not this one's to take |

Inside D, two ways to name the Russian graphic:

| Sub-option | Russian value of the id | For | Against |
|---|---|---|---|
| **D1. The variant's full path** | `localized/textures/m_pause.ru.png` | one file, already the contract (MOD-SPEC §2): the packer carries it, `check_pk3` checks its folder, name, base, size and licence row. If a later engine re-enables the substitution, the engine's own drawing and ours show the same plaque | the name is a path, not an 8-character lump; renaming the file breaks it (the test pins the value to the packed path, and the fallback shows the English plaque) |
| D2. An own lump `M_PAUSER` | `M_PAUSER` (as `graphics/M_PAUSER.png`) | an ordinary short name, the most common lookup | a second copy of the same picture, or the variant deleted and its validation left unused; its own `LICENSES.md` row (`art-director`'s register); no size check against `M_PAUSE` unless one is written |

The full-path lookup is not a guess. `FTextureManager::CheckForTexture`
(`texturemanager.cpp`) handles any name containing `/` with
`fileSystem.CheckNumForFullName`, and returns the texture already linked to
that file. `AddLocalizedVariants` created that texture when it registered
the variant, with the same call. The file-system lookup ignores case
(`MakeHash` folds case with `c | 32`; the compare is `strnicmp`), so the
lower-case value matches a path GZDoom lower-cases when it reads a PK3
anyway.

## Decision

**D with D1.** Specifically:

- **D-010-1. The class.** `zscript/sd/status_bar.zs` declares
  `class SD_StatusBar : DoomStatusBar` with no fields and one
  `override bool DrawPaused(int player)`. `MAPINFO → GameInfo` gains
  `StatusBarClass = "SD_StatusBar"`. The engine picks the last
  `StatusBarClass` by file order (`ST_CreateStatusBar`,
  `src/g_statusbar/shared_sbar.cpp`: a class wins over an `SBARINFO` from
  the same or an earlier file). Checked 2026-10-14: `freedoom2.wad` 0.13.0
  has no `MAPINFO`, `ZMAPINFO` or `SBARINFO` lump. The only `SBARINFO` in
  `gzdoom.pk3` is its root mugshot definitions. Among GZDoom's support
  packages, only `filter/harmony/` sets another class. Our PK3 loads after
  all of them.
- **D-010-2. The name of the graphic is text.** `LANGUAGE` id
  `SD_PAUSE_SIGN`: `[enu default]` `"M_PAUSE"`, `[ru]`
  `"localized/textures/m_pause.ru.png"`. A `LANGUAGE` lookup follows the
  language the player picked in our menu, `auto` included; reading the
  `language` CVar would need `auto` resolved by hand (ADR 004 is why the
  mod never writes it). Any other language falls back to `[enu default]`.
- **D-010-3. The lookup is the engine's.** `TexMan.CheckForTexture(name,
  TexMan.Type_MiscPatch)` with its default flag `TryAny`, which is what
  `GetGameTextureByName` does (`GetTextureID` adds `TEXMAN_TryAny`).
- **D-010-4. The drawing is the engine's.** Copied from `D_Display`: x =
  (screen width − width × `CleanXfac`) / 2 + left offset × `CleanXfac`,
  y = 4, `DTA_CleanNoMove`, animated. In multiplayer, the `TXT_BY` line with
  the pausing player's name, `SmallFont` (`NewSmallFont` under
  `generic_ui`), red, centred under the sign. Returning true skips the
  engine's whole block, that line included, so the class draws it.
- **D-010-5. The fallback is the English sign.** If the name does not
  resolve, `DrawPaused` returns false and the engine draws
  `GameInfo { PauseSign }` (`M_PAUSE`) itself.
- **D-010-6. The asset and its licence.** `assets/localized/textures/M_PAUSE.ru.png`
  is `work/art/shell_extra/pause_P2_ru.png` byte for byte (D48 approved
  P2). Its licence row is `M_PAUSE`'s in `docs/art/LICENSES.md` ("Shell"),
  the same generator and palette. `tools/release.py` now treats `localized/`
  as an asset folder and lets a base's row cover its variants, so the
  release's licence check sees the file instead of passing it over.

## Consequences

- The bar, the fullscreen HUD and the alt-HUD are Doom's code unchanged:
  `SD_StatusBar` inherits `Init`, `Draw` and everything else.
  `tests/test_pause_sign.py` fails if a second `override` or a field
  appears. Mods or engine code that check `StatusBar is "DoomStatusBar"`
  still see one.
- Two engine-upgrade debts grow (MOD-SPEC §10): T13, because a class
  derived from an engine class stops compiling if the engine renames it or
  the virtual; T14, because the drawing is a copy of `D_Display`'s.
  `tests/test_pause_sign.py` reads the installed `gzdoom.pk3` and checks
  that `DoomStatusBar`, `DrawPaused`, `statusbarclass = "DoomStatusBar"`
  and every engine name the file uses still exist. It skips where there is
  no GZDoom (CI).
- `DrawPaused` exists in g4.14.2's `gzdoom.pk3` without a `version(...)`
  gate, so `version "4.12"` compiles against it. Whether GZDoom **4.12**
  itself already had the virtual is **NOT VERIFIED** (no 4.12 on this
  machine). The project runs 4.14.2 (D3).
- Any future per-language graphic that the engine draws by name (not a
  menu `StaticPatch`, which `OkForLocalization` serves) needs the same
  treatment from whatever draws it. The variant mechanism alone draws
  nothing in g4.14.2.
- `check_pk3`'s note "registers them but does not draw them" stays true of
  the engine. For `M_PAUSE` the mod now draws the variant itself.

## Engine checks for the PM (D26)

| # | Check | How | Pass |
|---|---|---|---|
| E1 | The status bar is identical | MAP01, `screenblocks 10` (the bar) and `11` (fullscreen HUD), screenshot of each; compare with an earlier pass (`docs/qa/evidence/2026-10-13_1708_F3_map01-v3-engine-pass-*`) | same bar, face, numbers and keys; the log has no `Unknown status bar class` (what a wrong class name prints) and no `Script error` |
| E2 | Pause in English | `language default` (or the menu), start MAP01, press Pause, screenshot | P2 «PAUSE» at the top centre, where Freedoom's sign was |
| E3 | Pause in Russian | `language ru`, Pause, screenshot | P2 «ПАУЗА», same place, same size; the log has no `Unknown texture` |
