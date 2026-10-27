# ADR 015 — Touch mode: one CVar the app sets, read at draw time

Date: 2026-10-27. Status: **proposed on the branch `android`**, for the
Android app (D137; its own repository, `soviet_doom_android`). Owner:
`mod-engineer`. Amends D-004-2 of ADR 004 as ADR 014 did (a second CVar of
our own, `sd_touch`). **Not yet seen in the engine** (D26). The inventory
and the app's side: `docs/engine/2026-10-27_A1_mod-touch-adaptations.md`;
contract: `MOD-SPEC.md` §6.17.

## Context

D137: the Android version is our own app with our own touch layer, which
sends the engine **keys and relative mouse deltas** and nothing else. The
engine does not know it is being tapped, so every line of the mod that
names a key keeps naming one on a phone: "Press E to continue" when the
player has a button labelled USE; "Magazines; R reloads" when there is no
R. The study (`docs/product/2026-10-24_V3_android-port-study.md` §3)
asked for touch wording in the three languages and for the HUD's own
overlays to stay clear of the corners the stick and the buttons cover.
V3 is the last content version (D131, D135): the mod changes only what a
phone needs, and a desktop player must see no difference.

## Options

1. **A mobile overlay PK3** (`sovietdoom-mobile.pk3`, the study's first
   idea) redefining `SD_DEATH_PROMPT` and the reload note. Rejected: a
   second package to build, test and ship, and it cannot move a readout
   or choose at draw time; the engine's LANGUAGE override order for our
   own ids is NOT VERIFIED.
2. **Detect the platform in ZScript.** There is no API for it; the Android
   build is ours and could add one, but then the mod would depend on a
   fork of the engine. Rejected.
3. **A CVar the app passes on the command line** (`+sd_touch 1`), which
   the mod reads wherever a key is named. One package for every platform
   (the study's rule), no code in the app but one argument, and the
   console can flip it live for the engine pass on a desktop. **Chosen.**

## Decision

- `src/lumps/CVARINFO`: `user noarchive bool sd_touch = false;`. `user`:
  a presentation setting of this client. `noarchive`: never written to
  the player's ini, so a desktop config stays as it was and the phone
  gets it from the app at every launch. Nothing of ours writes it
  (ADR 004).
- `zscript/sd/touch.zs`: `SD_Touch.On()` (missing CVar = off) and
  `SD_Touch.KeyNameFor(command, fallbackId)`, the engine's key table
  lookup the death prompt already used; `OptionMenuItemSDKeyText`, a
  StaticText row whose `%s` is the bound key, or the touch button's
  label with `sd_touch`, filled when drawn.
- The texts that name a key get a `_TOUCH` twin in `[enu default]`,
  `[ru]` and `[ca]`, and the button labels are LANGUAGE ids
  (`SD_TOUCH_BTN_USE`, `SD_TOUCH_BTN_RELOAD`) the app copies, so a prompt
  and the button it points at always agree.
- The mod's own readouts move with `sd_touch`: the magazine line is
  centred. The engine's own HUD, messages and menus are the app's to
  place through engine CVars on the command line (`con_centernotify`,
  `screenblocks`, `cl_run`...): the mod cannot and must not set them.

## Consequences

- Desktop: `sd_touch` false, every string and position as in v1.3. The
  reload note now reads the bound key instead of a literal R, which is
  the one visible change for a player who moved the key (an improvement).
- The quit lines keep "(Press Y to quit.)": the engine's own yes/no box
  takes Y/N and a click on its Yes/No rows (verified in gzdoom.pk3's
  `messagebox.zs`), and `MAPINFO`'s `QuitMessages` cannot follow a CVar.
  Changing the fifteen lines is a product decision, not this ADR's.
- `tests/test_touch.py` pins the CVar, the wiring, the strings and that
  no string of ours names a key outside the listed exceptions.
- Debt: the engine pass (D26) of the SDKeyText row (MENUDEF parsing of a
  class with four string arguments; the `ui` static call), the touch
  prompt in three languages, and the centred readout, at 2400×1080.
