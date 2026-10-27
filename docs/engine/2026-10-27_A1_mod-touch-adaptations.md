# A1: what the mod adapts for a touch screen (Android, 2026-10-27)

Dated snapshot. Owner: `mod-engineer`. Branch `android`, task A1 of the
Android version (D137): our own app, our own touch layer, which sends the
engine **keys and relative mouse deltas** and nothing else. The guide was
`docs/product/2026-10-24_V3_android-port-study.md` §3. The decision record
is ADR 015; the contract is `MOD-SPEC.md` §6.17; the tests are
`tests/test_touch.py`. **Nothing here has run in the engine (D26)**: every
engine fact below is read from the installed gzdoom.pk3 (g4.14.2) or its
source, and what was not read is marked **NOT VERIFIED**. Numbers for the
screen are for the CEO's test phone, a 20:9 panel of 2400×1080 (the study
§4), and are arithmetic, not measurements.

## 1. The rule, and the one switch

One `sovietdoom.pk3` for every platform (the study's rule). A phone differs
from a desktop in three things the mod draws: the words that name a key,
where its own overlays sit, and nothing else. The mod learns it is on a
phone from **one CVar, `sd_touch`** (`src/lumps/CVARINFO`, `user noarchive
bool`, default false), which the app passes on the engine's command line at
every launch: `+sd_touch 1`. The mod only reads it (`SD_Touch.On()`,
`src/zscript/sd/touch.zs`), at draw time, so `sd_touch 1` in a desktop
console shows the phone's text for the engine pass. A desktop never sees a
difference: with the CVar false every string and position is v1.3's.

Why not a mobile overlay PK3 (the study's first idea), and why not platform
detection: ADR 015.

## 2. Inventory: every text of ours that names a key

Read from `src/lumps/LANGUAGE` (the three sections), `MENUDEF`, `MAPINFO`,
the ZScript that prints text (`death_prompt.zs`, `help_menu.zs`,
`status_bar.zs`, `magazine_hud.zs`, `status_screen.zs`, `awards.zs`, the
pickups' and monsters' `PickupMessage`/`Obituary`/`A_PrintBold` lines) and
the README. Reload and grenade tooltips: there are none in the game (the
RGD-5 and the magazines print nothing); the help key F1 opens the credits,
not a controls page (ADR 009), so no help screen lists keys.

| Where | Text (English) | Names | Done |
|---|---|---|---|
| `SD_DEATH_PROMPT` (death prompt, `death_prompt.zs`) | "Press %s to continue" | the key bound to `+use`, at draw time | **touch twin** `SD_DEATH_PROMPT_TOUCH`, "Tap %s to continue", `%s` = the USE button's label (§3) |
| `SD_OPTMNU_RELOADHELP` (Options > Soviet Doom, under "Weapon reloads") | was "Magazines; R reloads. Off: as in v1.2." | **a literal R** | **replaced**: "%s" filled with the key bound to `+reload` when the row is drawn (R by default, `KEYCONF`), through a new row class `SDKeyText`; **touch twin** `SD_OPTMNU_RELOADHELP_TOUCH`, "Magazines; tap %s. Off: as in v1.2.", `%s` = the RELOAD button's label |
| `SD_QUIT_01`…`15` (the quit prompt, `MAPINFO` `QuitMessages`) | "…(Press Y to quit.)" | a literal Y, in all three languages | **kept** (§2.1) |
| `[ca]` only: `QSPROMPT`, `QLPROMPT`, `ENDGAME`, `PRESSYN` ("Prem Y o N."), `QSAVESPOT`, `SAVEDEAD`, `PRESSKEY` ("Prem una tecla.") | the engine's own prompts, which GZDoom ships in English and Russian but not Catalan | Y, N, "a key" | **kept**: they mirror the engine's wording; the English and Russian the player sees are the engine's own (§2.1) |
| `README.md` | the keyboard controls list | W A S D, E, R, 1-8… | **not the game's text**: the app's own store page/README lists the touch layout (§5) |

Everything else of ours names no key: the pickup lines, the obituaries, the
bestiary tags, the awards and their rules, the ending texts, the menu
headers, the credits. `tests/test_touch.py` keeps it that way: it rejects
any string, in any of the three sections, matching "Press/Prem/Нажмите +
one letter", "<letter> reloads", "F1-F12" or the engine's special-key names,
outside the two exceptions above.

### 2.1 The two exceptions, and why they are the app's

**The quit lines.** `MAPINFO`'s `QuitMessages` are fixed at load; no CVar
can swap them. They say "(Press Y to quit.)" because the engine's yes/no
box takes Y and N. Verified in gzdoom.pk3's
`zscript/engine/ui/menu/messagebox.zs` (g4.14.2): the same box also
**draws "Yes" and "No" rows under the message** (`$TXT_YES`, `$TXT_NO`,
with a selector) and **takes a mouse click on them** (`MouseEvent`,
`MOUSE_Release` → `HandleResult`). A tap is a click to the engine, so on a
phone the player taps "Yes"; the line's Y is then one of two ways, not a
lie. Dropping the fifteen "(Press Y to quit.)" lines, in three languages,
is a product decision about the CEO's own text (H5), not this task's; it
is listed for him in §6.

**The `[ca]` engine mirrors.** Seven ids the engine prints during saving,
loading and ending a game. In English and Russian the player reads the
engine's own strings ("Press a key.", "Нажмите Y или N."), which the mod
does not own; the Catalan copies them so a Catalan player reads Catalan.
Touch twins of engine strings would need the engine's own code to pick
them, which it does not. The app covers them: its tap-anywhere in a message
box sends Enter/Y (§5).

## 3. What changed in the mod

| File | Change |
|---|---|
| `src/lumps/CVARINFO` | `user noarchive bool sd_touch = false;` (comment: who sets it, why not archived) |
| `src/zscript/sd/touch.zs` (new) | `SD_Touch`: `On()`, `KeyNameFor(command, fallbackId)` (the engine's `Bindings.GetKeysForCommand` + `KeyBindings.NameKeys`, the engine's `$CNTRLMNU_*` control name when nothing is bound). `OptionMenuItemSDKeyText : OptionMenuItemStaticText`: a StaticText whose `%s` is the bound key, or the touch button's label with `sd_touch`, chosen and filled in `Draw`; the only override. It writes nothing (ADR 004) |
| `src/lumps/zscript.txt` | includes `touch.zs` before the files that read it |
| `src/zscript/sd/death_prompt.zs` | with `sd_touch`: `SD_DEATH_PROMPT_TOUCH` with `SD_TOUCH_BTN_USE`; else as v1.3 |
| `src/zscript/sd/magazine_hud.zs` | with `sd_touch`: the "rounds/capacity" line centred on x 160 (same heights: y 158 with the bar, y 170 over the fullscreen HUD), clear of both bottom corners |
| `src/lumps/MENUDEF` | `SDKeyText "$SD_OPTMNU_RELOADHELP", "+reload", "$SD_OPTMNU_RELOADHELP_TOUCH", "$SD_TOUCH_BTN_RELOAD"` in place of the StaticText |
| `src/lumps/LANGUAGE` | in `[enu default]`, `[ru]`, `[ca]`: `SD_OPTMNU_RELOADHELP` with `%s`; new `SD_OPTMNU_RELOADHELP_TOUCH`, `SD_DEATH_PROMPT_TOUCH`, `SD_TOUCH_BTN_USE`, `SD_TOUCH_BTN_RELOAD` |
| `docs/engine/MOD-SPEC.md` | §6.17 (the contract), §6.15 (the note and the readout), §10 T26 |
| `docs/engine/adr/015-touch-mode.md` | the decision |
| `tests/test_touch.py`, `tests/test_reloads.py` | the new suite; three reload tests follow the note's new form |

**The button labels: the contract with the app.** The app labels its
buttons with these words, in the player's language, so a prompt and the
button it points at agree (the strings are the single source; the app
copies this table, and `tests/test_touch.py` checks the table against
LANGUAGE):

| Id | `[enu default]` | `[ru]` | `[ca]` | Named by |
|---|---|---|---|---|
| `SD_TOUCH_BTN_USE` | `USE` | `ДЕЙСТВИЕ` | `ACCIÓ` | the death prompt |
| `SD_TOUCH_BTN_RELOAD` | `RELOAD` | `ПЕРЕЗАРЯДКА` | `RECARREGA` | the reload note |

The touch lines, filled: "Tap USE to continue" / "Нажмите кнопку ДЕЙСТВИЕ,
чтобы продолжить" / "Toca ACCIÓ per continuar"; "Magazines; tap RELOAD.
Off: as in v1.2." / "Магазины; кнопка ПЕРЕЗАРЯДКА. Выкл.: как в v1.2." /
"Carregadors; toca RECARREGA. No: com a la v1.2." Every character of the
prompts has a glyph in BigFont and SmallFont (the test checks the folder
fonts); the notes fit one option row (≤ 48 characters, the reload suite's
limit).

The desktop's one visible change: the reload note reads the key the player
actually bound ("Magazines; E reloads." for someone who moved it) instead
of a literal R; with nothing bound it reads the engine's control name
("Reload").

## 4. Safe areas: what a touch layout covers on a 20:9 screen

The arithmetic for 2400×1080. GZDoom draws Doom's 320×200 screen with
aspect correction in a **4:3 box** of 1440×1080 **centred**: x 480 → 1920,
scale ×4.5 horizontally and ×5.4 vertically. That the status bar, the
intermission and the awards page are drawn in that box and not stretched
to 2400 is how g4.14.2 behaves on the desktop at 16:9 (the mod's STBAR is
320 wide and `game_widescreen_gfx.pk3` loads before it; the awards page
uses the stats screen's own scaling) and is **NOT VERIFIED at 20:9**: the
first screenshot on the phone settles it.

| What | Where it lands (px) | Under a corner control? |
|---|---|---|
| Status bar A (screenblocks 10) | y 907-1080; AMMO digits x 489-678, HEALTH 696-885, ARMS 948-1119, face 1124-1281, ARMOR 1286-1542, keys 1556-1600, ammo table 1605-1920 | **no**, if the stick stays in x < 480 and the right-hand buttons in x > 1920 (the side strips, 20 % of the width each) |
| The engine's fullscreen HUD (screenblocks 11) | health/armour at the bottom-LEFT of the whole screen, ammo and keys at the bottom-RIGHT (`DoomStatusBar.DrawFullScreenStuff`, anchored to the real edges) | **yes**, both corners |
| The engine's notify messages (pickups, "secret found") | top-left of the whole screen, from x 0 | **yes**, a top-left button; `con_centernotify 1` centres them |
| The mod's pause sign | top centre | no |
| The mod's death prompt | centre | no |
| The mod's magazine line | with the bar: x ≈ 480-678 (right-aligned on the AMMO digits), y 853; with the fullscreen HUD: x ≈ 1700-1785, y 918 | borders the stick / under the fire buttons → **centred with `sd_touch`** (x 1200) |
| Mid-screen prints (the General's order, the Consortium's line) | centre | no |
| The stats screen and the awards page, the ending texts, the illustrations | the 4:3 box | no (the app hides the game buttons there; one tap anywhere = a key, §5) |
| The menus | ListMenus in the 4:3 box; option menus full-width rows | the app shows menu buttons instead of game buttons (§5) |

**Proposal for the layout** (the app's decision; this is what keeps the
mod's drawing clear): move stick in the bottom-left strip (x < 480, y >
540), fire in the bottom-right strip (x > 1920), USE and RELOAD above
fire in the same strip, weapon next/prev and jump along the right edge,
menu (Escape) top-left corner and map (Tab) top-right corner, all inside
the two 480 px strips. **The status bar on (`screenblocks 10`)**, not the
fullscreen HUD, whose corners the layout covers; the bar is also the
CEO's art (status bar A). With that, nothing the game draws is under a
button at 20:9. At 16:9 (1920×1080, no strips) the stick and the AMMO
digits meet: the app may scale the bar down with `st_scale` (engine CVar)
or accept the overlap; not this task's.

What the mod did NOT do, and why: moving the engine's notify messages
(`BaseStatusBar.ProcessNotify` lets a status bar take them over, verified
in gzdoom.pk3 `statusbar.zs`, but it means re-implementing the notify
buffer, its timing and colours, unseen in the engine) when the engine's
own `con_centernotify` does it in one CVar; moving the fullscreen HUD
(`DrawFullScreenStuff` is not virtual; `BeginHUD(..., forcescaled)`'s
effect on anchoring is NOT VERIFIED) when the bar is the better HUD here.

## 5. What is the app's (the mod cannot do it)

The mod writes no CVar (ADR 004: ZScript may write one only during menu
input, and `KEYCONF`/`MAPINFO` cannot set engine CVars). Every row below
is an argument on the engine's command line, `+name value`, at every
launch, or a line in the ini the app owns:

| CVar | Value | Why |
|---|---|---|
| `sd_touch` | `1` | this task's switch (§1) |
| `cl_run` | `1` | always run: a stick has no Shift. The engine row "Always run" (`menudef.txt`) |
| `con_centernotify` | `1` | pickup messages centred, away from the top-left button (`menudef.txt`, "Center messages") |
| `screenblocks` | `10` | status bar A on; the fullscreen HUD's corners are covered (§4) |
| `crosshair` | `1` or a chosen one | aiming with a thumb, no mouse |
| `use_mouse`, `m_use_mouse` | `1`, menus on | the engine's menus take the mouse (both `ListMenu.MouseEvent` and `OptionMenu.MouseEvent` exist in gzdoom.pk3; a click on an Option row is Enter and steps the value) |
| `m_show_backbutton` | a corner the layout leaves free, or off | the engine draws a back button in menus for mouse users; its corner must not sit under the app's own menu button |
| mouse scale (`mouse_sensitivity`, `m_yaw`, `m_pitch`, `smooth_mouse`, `m_filter`; which of these g4.14.2 applies to injected deltas is NOT VERIFIED) | leave the engine's defaults; scale the touch delta in the app | one knob in the app's settings, in finger units, instead of the engine's three |
| `autoaim` | the engine's default (on) | vertical autoaim helps a thumb; nothing to set |
| `uiscale`, `st_scale`, `hud_scale` | measure first | at 1080p the auto scale is 5; option rows are 8 virtual lines = 40 px tall (§6) |

**Keys the touch layer sends** (the engine's default bindings, read from
gzdoom.pk3 `engine/*binds.txt`; the mod's `KEYCONF` adds `r +reload`). The
app should send these keys and not rely on a player's rebinding, or write
its own `bind` lines in the ini it owns:

| Control | Key | Engine command |
|---|---|---|
| move stick | W / S / A / D (held) | `+forward` `+back` `+moveleft` `+moveright` |
| look | relative mouse deltas | the view |
| fire | Mouse1 or Ctrl | `+attack` |
| USE | E | `+use` (also the death prompt's "continue", MOD-SPEC §6.10) |
| RELOAD | R | `+reload` (`KEYCONF`) |
| jump | Space | `+jump` (Space is bound to `+jump` and `+use` by the engine's defaults; the app should send E for USE, not Space) |
| grenade | 8, then fire | `slot 8` (the RGD-5, ADR 012); a quick-throw macro is the app's |
| weapon next / prev | mouse wheel down / up | `weapnext` / `weapprev` |
| map | Tab | `togglemap` |
| menu / back | Escape | the menu |
| in menus | Up / Down / Enter / Escape, and taps as absolute clicks | menu navigation |
| quick save / load | F6 / F9 | `quicksave` / `quickload` (the study: Android kills background apps; a save button matters) |
| message boxes (quit, overwrite, end game) | Y / N, or a tap on the Yes/No rows | §2.1 |
| intermission, ending texts, illustrations | any key, or fire/USE | the stats screen advances on `+attack`/`+use` |

**In menus, taps must be absolute pointer positions** (GUI events with
x, y), not deltas: the engine's menus place the cursor by the event's
coordinates (`listmenu.zs`, `optionmenu.zs` convert screen x, y to menu
space). In the game, relative deltas. SDL's touch-to-mouse emulation does
both; if the app injects events itself, it needs both paths.

**Saves, language, music, rendering:** the study §3; nothing of the mod
changes there.

## 6. Menus: what was checked, what is small

- **Main menu, episode screen, skill screen** (`LISTMENU`s of ours): the
  engine's `ListMenu.MouseEvent` maps a click to the item under it and
  activates on release; keyboard: arrows, Enter, the hotkeys (n, l, s, o,
  q). No hover is needed. Rows are 16 virtual lines (the main menu) and 12
  (episodes, skills): 86 and 65 px at 1080p, ≈ 5.6 and 4.2 mm on the M55
  (393 ppi) — tappable, tight.
- **Options > Soviet Doom, Credits, the engine's option screens**: a click
  on an `Option` row is Enter, which steps the value (Language cycles
  auto → English → Russian → Catalan; Reloads toggles); a click on a
  Submenu row opens it; the credits scroll with the wheel. **Rows are 8
  virtual lines, ≈ 40 px, 2.6 mm**: not a finger target.
  `OptionMenuSettings` is `native readonly` in gzdoom.pk3 `base.zs`, so
  ZScript cannot widen the rows with `sd_touch`; a MENUDEF
  `OptionMenuSettings { Linespacing N }` block would widen them on every
  platform and is NOT VERIFIED as allowed from a mod (T26). **The app's
  menu mode therefore shows Up/Down/Enter/Escape buttons**; taps are a
  bonus.
- **The quit box**: Yes/No rows, tappable (§2.1).

## 7. For the CEO (decisions, none blocking)

1. The fifteen quit lines' "(Press Y to quit.)": keep (a tap on "Yes" works
   too) or drop the parenthesis in the three languages (a product text
   change, 45 strings).
2. Wider option rows for every platform (`OptionMenuSettings` in
   MENUDEF, if the engine allows it from a mod): the desktop menus change
   too.
3. The button labels in §3: the app's buttons will carry these words.

## 8. The engine pass (the PM, D26)

1. Desktop, `sd_touch 1` in the console: die in MAP01 → "Tap USE to
   continue" (EN), `language ru` → "Нажмите кнопку ДЕЙСТВИЕ, чтобы
   продолжить" (falls to SmallFont at 320×200, as the Russian desktop line
   does), `language ca` → "Toca ACCIÓ per continuar". `sd_touch 0` → the
   key again.
2. Options > Soviet Doom: the note reads "Magazines; R reloads. Off: as in
   v1.2."; `bind e +reload` in the console → "E reloads"; `unbind e`,
   `unbind r` → "Reload reloads"; `sd_touch 1` → "Magazines; tap RELOAD.
   Off: as in v1.2." In the three languages. **The MENUDEF parse of
   `SDKeyText` with four string arguments is the risk**: a parse error here
   stops the engine at "M_Init" like the `OptionValue` one did (MENUDEF's
   long note); the log tells.
3. `sd_touch 1`, reloads on, the bar on: the "8/8" line centred above the
   bar; `screenblocks 11`: centred above the HUD's bottom row.
4. A 2400×1080 window (`vid_setsize 2400 1080` or `win_w`/`win_h`): where
   the bar's box, the notify text with `con_centernotify 1`, the prompt
   and the readout land, screenshot to `docs/qa/evidence/`.
5. The log clean: no "Script error", no "Unknown" line from `touch.zs` or
   `MENUDEF`.


## Engine pass (PM, 2026-10-27 14:53, D26)

GZDoom g4.14.2 on the branch build, 2400x1080 window, `+sd_touch 1 +cl_run 1 +con_centernotify 1 +screenblocks 10`: log clean (no error, no warning; `SDKeyText` parsed by MENUDEF). With `language ru`: the options note reads «Магазины; кнопка ПЕРЕЗАРЯДКА» and the death prompt «НАЖМИТЕ КНОПКУ ДЕЙСТВИЕ, ЧТОБЫ ПРОДОЛЖИТЬ», the magazine line centred. Evidence: `docs/qa/evidence/2026-10-27_1453_A1_touch-options-ru-engine.png`, `..._touch-death-prompt-ru-engine.png`. EN and CA strings are the same ids; not screenshotted. Safe areas on the real phone: still NOT VERIFIED (A2 gate).
