# ADR 003 — Soviet ammunition names, and a shovel that swings in silence

Date: 2026-10-13. Status: accepted (F4 follow-up), verified in-engine on
GZDoom 4.14.2 + Freedoom 0.13.0. Owner: `mod-engineer`.
Russian mirror: `docs/ru/engine/adr/003-ammo-naming-and-the-silent-shovel.md`.

## Context

The CEO's first play session on the `MAP02` test range produced four
verdicts. Two of them are engine work.

1. **The shovel sounded like a chainsaw.** `SNDINFO` mapped the logical name
   `sd/weapon/shovel/swing` to `DSSAWUP`, the chainsaw start-up. A
   placeholder chosen badly: it does not say "melee", it says "another
   weapon entirely".
2. **The ammunition reads as Doom's, not as 1977 Soviet materiel** —
   "bullets", "shells", "energy cells". The CEO decided it should carry the
   period designation the arsenal itself proposes: 7,62×25 for the pistol
   round the TT-33 and the PPSh-41 share, 12 gauge for the IZh-58, ПГ-7В for
   the RPG-7 round, fuel for the ROKS-3.

Two further verdicts (the HUD fist whose sleeve is the colour of the hand,
and flat-looking ammo pickups) are Freedoom placeholder **art**, not engine
defects; they are recorded as debt in `docs/engine/MOD-SPEC.md` §6.3.

## Options

### A. The shovel swing

1. Keep a placeholder but pick a better lump. Freedoom's full sound list was
   read out of `freedoom2.wad` (109 `DS*` lumps). The only swing-through-air
   sound in it is **`DSSKESWG`**, the revenant's melee wind-up.
2. Silence the swing, keep the impact (`sd/weapon/shovel/hit` → `DSPUNCH`).
3. Synthesise a whoosh now.

### B. The ammunition names

1. **Override the engine's string ids** `AMMO_CLIP`, `GOTCLIP`,
   `GOTCLIPBOX`, … in our `LANGUAGE` lump.
2. **Create new ammo pools** (`SD_Clip : Ammo`, …) and point every weapon's
   `Weapon.AmmoType` at them.
3. **Subclass the Doom pickups** (`SD_ClipBox : ClipBox replaces ClipBox`)
   and give them our own `SD_GOT_*` string ids.
4. Ship our own `DEHACKED` lump to out-patch Freedoom's.

## Decision

**A2 — the swing is silent.** `DSSKESWG` was rejected: borrowing the
revenant's wind-up teaches the player that a monster is about to swing at
them every time they raise the shovel, which is a worse lie than silence.
Doom's own `Fist` has no swing sound either — the feedback is the impact.
The `A_StartSound` call is removed from the `Fire` state of `SD_Shovel` and
the `SNDINFO` entry with it (the tic count is unchanged, so balance is
untouched); the two lines needed to restore it when `sound-designer`
delivers `SDSHSWG` are written out in the comment at the top of `SNDINFO`.
Option 3 is `sound-designer`'s job, not a placeholder.

**B1 + B3 — one mechanism each, because the engine behaves differently for
the two kinds of string.**

- **Pool names** (`AMMO_CLIP`, `AMMO_SHELLS`, `AMMO_ROCKETS`, `AMMO_CELLS`)
  are overridden in `LANGUAGE`. These are the `Tag` of each Doom ammo class
  in `gzdoom.pk3`; a PK3 loaded after the engine wins, and Freedoom's
  `DEHACKED` lump does not contain them.
- **Pickup lines** are *not* set through `GOTCLIP` / `GOTSHELLS` / …
  **Verified 2026-10-13:** Freedoom's `DEHACKED` lump redefines all nine of
  them (`GOTCLIPBOX = Picked up a case of bullets.`), and on GZDoom 4.14.2 a
  `DEHACKED [STRINGS]` replacement **beats a `LANGUAGE` lump loaded
  afterwards** — our override was parsed and ignored, and Freedoom's line
  was printed. The mod therefore declares nine thin subclasses in
  `src/zscript/sd/ammo.zs` carrying `SD_GOT_*` ids Freedoom knows nothing
  about.

B2 was rejected: new pools would mean new `MaxAmount`, new backpack
behaviour and a `Weapon.AmmoType` edit in six weapons, for a cosmetic gain.
B4 was rejected: a `DEHACKED` lump is one string per id with no language
sections, which breaks D7 on the spot.

Subclassing rather than re-implementing is what keeps the pools Doom's:
GZDoom resolves which pool an item feeds with `Ammo.GetParentAmmo()`, which
walks up the inheritance chain until the parent class is `Ammo`
(`SD_ClipBox → ClipBox → Clip → Ammo` yields `Clip`). `replaces` makes the
engine hand out our class wherever Freedoom's would have spawned — map
things, monster drops and the backpack alike — so no map has to know.

**Script: Latin in English, Cyrillic in Russian, for now.** The CEO asked for
the Cyrillic designations. They are written in the `[ru]` section and they
are correct, but **they cannot be shown yet**. Freedoom's `SmallFont` is
ASCII only; GZDoom does ship Cyrillic glyphs for the Doom fonts, but under
`filter/doom.id/fonts/`, a path an id IWAD selects and Freedoom does not.
Verified in-engine 2026-10-13: `A crate of ПГ-7В rounds.` printed as
`A CRATE OF  -7B ROUNDS.` — `П` and `Г` blank, `В` silently remapped to a
Latin `B` — and even the `×` of `7,62×25` printed as a blank. Showing blanks
to the CEO is worse than showing `PG-7V`, so the English section uses the
Latin transliteration a 1977 manual would also carry, and
`tests/test_arsenal.py` fails if a non-ASCII character creeps back into it.

**The fix is cheap and the mechanism is verified.** A throwaway PK3
containing nothing but `fonts/defsmallfont/041F.png` and `0413.png` (two
crude white shapes) was loaded next to the mod on Freedoom, and `П` and `Г`
rendered. So: `art-director` draws the uppercase Cyrillic alphabet
(U+0410–U+042F, 32 glyphs), `Ё` (U+0401), the guillemets `«»` (U+00AB,
U+00BB) and `×` (U+00D7) in Freedoom's small-font style; they ship as
`src/fonts/defsmallfont/<HEX>.png`; the English section goes Cyrillic and
the Russian build becomes legible in the same commit. Tracked as debt **T9**.

## Consequences

- The shovel is quieter than it will be. Impact feedback only, until
  `SDSHSWG` exists.
- `src/zscript/sd/ammo.zs` is the first file in `zscript/sd/` to hold more
  than one class. Nine near-identical four-line reskins in nine files would
  be noise; they are one family and live together.
- `LANGUAGE` now deliberately overrides **engine** string ids that are not
  prefixed `SD_`. That is the only way to rename a class we do not own. The
  rule stays: ids we invent are prefixed `SD_`; ids we override are listed
  and justified in `LANGUAGE` itself.
- Renaming `AMMO_*` is invisible today: neither the stock Doom status bar
  nor the alternative HUD ever prints an ammo `Tag`. It is set so that the
  pool's name exists in exactly one place for when we own the status bar.
- **The status bar is not touched.** `AMMO`, `HEALTH`, `ARMS` and `ARMOR` are
  pixels inside the IWAD's `STBAR` graphic, not text. Changing them is an
  open question for the CEO, measured in `docs/engine/MOD-SPEC.md` §6.5.
- Freedoom's `DEHACKED` lump is now known to outrank our `LANGUAGE` for the
  ids it defines. Any future retheme of an IWAD actor's pickup line must go
  through a subclass, not a string override. A test enforces it.

## Verification

```sh
python3 tools/build.py && python3 tools/check_pk3.py \
  && python3 tools/smoke.py --map MAP02 && python3 -m unittest discover -s tests
MAP=MAP02 tools/run.sh       # pick up the four ammo boxes, swing the shovel
```

In-engine on GZDoom 4.14.2 + Freedoom 0.13.0, 2026-10-13: `MAP02` prints
`A box of 7.62x25.`, `A box of 12 gauge shells.`, `A crate of PG-7V rounds.`,
`A full fuel tank.` and `Quartermaster's satchel. Everything you can carry!`;
`logs/gzdoom.log` holds no `Script error`, `Unknown` or `Missing` line.
