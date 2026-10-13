# Pending CEO decisions

Updated: 2026-10-13 14:50, on the move to the Windows PC. Ordered by how much
each item unblocks. What closed since the previous update is listed at the
end so nothing is lost. Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`.

## 1. Walk MAP01 v1 on this PC (10 minutes, unblocks F3 v2 and two textures)

```
SD_ALLOW_ENGINE=1 tools/run.sh
```

v1 is textured and signposted (`docs/levels/MAP01-zarya-7.md` §15). Three
verdicts are yours:

- **The gate criterion.** Starting in the dorm, do you reach the fuel bay
  without being told? In v0 the hangar gate read as a dead end; v1 answers
  with the red stripe, the yellow lane and a recessed gate.
- **`SDCONC2`, the red stripe.** One band in the barracks, three bands in the
  320-high hangar. Keep it, or give the hangar a 128-high wainscot in v2 so
  it is one band there too? (Pending in-map review since 2026-10-12.)
- **`SDSTAR1` v5**, the plaque beside D2 in the dorm. Approve, or send back.
  (Proposed v5 since 2026-10-12.)

For the eye only, no decision unless you dislike it: gate D4 wears two
identical leaves (A4); `level-designer` finds that acceptable.

Design points carried from the design document §13: no keys, switch grammar
instead (built that way on the PM's approval; one word from you closes it,
recommended yes); a night-sky strip over the hangar in v2, yes or no; 5-8
minutes with 21/33/46 enemies by skill, longer than Doom II's MAP01
(~2 min), which matters before v3, not before.

## 2. Play the weapons test range (15 minutes, unblocks F4 balance)

```
MAP=MAP02 SD_ALLOW_ENGINE=1 tools/run.sh
```

All seven weapons, their ammo and targets are in the room. Sprites and sounds
are Freedoom placeholders — judge **feel**, not looks: does the PPSh-41 feel
like the icon of the mod, is the shovel worth having, is the IZh's two-shots-
then-reload satisfying or annoying. Numbers and rationale: `docs/engine/BALANCE.md`.

Specific doubts from `mod-engineer`:
- The TT-33 is **+43 % on Doom's pistol** (26.3 vs 18.4 DPS). The most
  aggressive number in the table and the first he would cut.
- The hand Katyusha shares ammo with the flamethrower, as Doom's BFG shares
  with the plasma. Own ammo pool, yes or no?
- PPSh pickups give 35 rounds (half a drum) instead of Doom's 20.
- Does MAP02 ship in v1, or stay engineering tooling?

## 3. Metro set, first six pieces (F2 batch 2)

Preview: `docs/art/previews/2026-10-13_0952_F2_batch2-metro-first-pieces.html`.

- **Direction.** Is this the underground you pictured? Glazed tile, painted
  dado, red marble, mosaic, brass, granite.
- **Palette v2.** The marble red and the mosaic's cobalt and gold need ramps
  the ratified v1 palette does not have; the sheet shows what v1 can do. A
  new palette version is your call (ART-BIBLE §3).
- **Mosaic motif.** A star with rays, or a figure (cosmonaut, worker), which
  would be its own commission, like Lenin was.

## 3b. Two small art verdicts (5 minutes, both feed MAP01 v2)

- **Crates and lockers** (petition A5), sweep
  `docs/art/previews/2026-10-13_1439_F3_batch3-props-sweep.html`. One cell
  per row. Art-director and PM recommend **C** for the three crate pieces
  (khaki planks with a diagonal brace, the only shape still legible at game
  distance on both walls) and **D** for the locker (pale cream). Also: keep
  C in khaki, which ART-BIBLE reserves for the Reich's flesh, or repaint it
  in brown wood at the same value; and keep the stencilled numbers or drop
  them.
- **Font fix for M, М and W** (alphabet C, D24), sheet
  `docs/art/previews/2026-10-13_1443_F2_font-C-serif-fix.png`. QA found the
  slab serifs misplaced on three letters: the small W reads "VL", so
  "WORSE" looks like "VLORSE". The fix changes 6 of 214 glyph files and no
  other letter. Art-director and PM recommend approving; it is our bug, not
  a change of style.

## 4. Music (`docs/sound/SOUNDTRACK.md` §8 owns the detail)

D23 settled the model (free MIDI first, our sequencing as fallback, La
Internacional on the title). Still open, in the sound-designer's order:

- Credit **Jerry Engelbach** in the credits and the licence register for the
  title Internationale. D23 chose the piece; the attribution is not yet
  accepted in writing.
- Approve the repaired `D_SDINTL.mid` into `assets/`. The Mac's `work/audio/`
  arrived on this PC on 2026-10-13, so it can be heard here:
  `SD_ALLOW_ENGINE=1 python tools/audio/audition.py --play title --lump D_SDINTL`.
- **MAP01 music:** our own `D_SDM01` (recommended), or an orchestration of
  *Night on Bald Mountain* or *Dumka* from a solo-piano score. `MAPINFO`
  still says `music = ""`.
- Enrich `D_SDM01` (two more layers, a non-repeating section; hours) rather
  than replace it? Recommended, after the previous point.
- Diegetic radio: approve `WM_Ej_uchnem.mid` and `WM_Kolokolchik.mid`, both
  CC0, no obligation of any kind.
- Sequence ourselves «Вы жертвою пали» and «Амурские волны» (recommended) for
  the works no licence-clean MIDI exists for; for *Marche slave* the
  alternative is IMSLP's CC BY 4.0 MP3 as OGG (megabytes).
- Confirm the three discards: `D_CND02`, `D_CND04`, `D_CND08`.
- Works free in Russia but restored in the United States («Священная война»
  above all): exclude them. PM recommends yes; we would host in the US.
- Does the Soviet anthem appear anywhere? Own instrumental sequence with a
  residual US risk, or Glinka's Patriotic Song at zero risk. It no longer
  blocks the title.
- `work/audio/candidates/` is gitignored: it now exists on both machines but
  in no commit. The sound-designer asks to track it. PM recommends yes
  (twelve MIDI files, about 180 KB; the provenance is external and seven have
  no recorded URL, so the files are the only record).

## 5. Bestiary — seven questions (`docs/engine/BESTIARY.md` §14)

Cost warning worth reading first: F5 is **~356 sprite images and 52 sound
lumps**, more than the whole of F2. The questions that change the most:
- Panzermensch at **500 HP** (PM and author recommend) or the 1000 of a Doom
  baron, which in a one-map v1 is a wall, not a fight.
- Is the General a boss with a verb of his own (he summons and orders, half a
  day plus ten sprites) or just a brute with more health. Author recommends
  the verb; the lore says the General commands rather than fights.
- Freedoom sprites as a base or only as reference. Recommended: reference
  only for the five most-seen enemies.
- Do the two factions keep Doom's infighting. Recommended yes: the lore calls
  it an alliance of convenience.

## 6. Smaller, no hurry

- **Lenin slogan.** Ships with «ЛЕНИН ЖИВ»; Mayakovsky's full line «Ленин
  жил, Ленин жив, Ленин будет жить» also fits in three lines. Say so if you
  want it; otherwise it is closed as shipped. The photograph is here now,
  but `SDPOSTR1`'s slogan is set in Impact, so a re-render on this PC is a
  new proposal for you (D27), not a quiet edit.
- **ML level generation** (`docs/product/2026-10-13_0944_F3_ml-level-generation.md`
  §6): the research says no to training a model, and recommends 1-2 days
  mining Freedoom's 68 maps (BSD) to calibrate our own constants. Spend it
  or not.
- **Who approved the MAP01 design text?** The design document said "approved
  by the CEO"; the record only shows the PM approving it as written on
  2026-10-12. Confirm and the PM records it with the date.
- **Ultimate Doom Builder** is now possible on this PC (PRD §7 risk). Evaluate
  it when a map needs hand editing, or stay script-only. Not needed for v2.

## Closed since the previous update (for the record)

Title screen and intermission (D18). Switch texture: all four variants
approved and installed (D25). Music model and La Internacional (D23).
Alphabet C (D24). Difficulty ladder (D20; the "Pyatiletka in one night" swap
stays an option, not a pending item). Language switch and Cyrillic
letterforms, level 2 (D21, D22). The engine gate (D26). The Windows PC as the
working machine (D27); the Mac's gitignored `work/` reached the PC the same
afternoon, so D27's "stays on the Mac until the CEO copies it" is now
history. Bug B2 (`SDPOSTR2`) resolved 2026-10-12. Bug B3 (art identity
test without `work/`) resolved 2026-10-13. T16, the switch `ANIMDEFS`,
written and seen to flip in engine 2026-10-13.
