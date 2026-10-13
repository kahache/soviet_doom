# Pending CEO decisions

Updated: 2026-10-13 17:00, on the move to the Windows PC. Ordered by how much
each item unblocks. What closed since the previous update is listed at the
end so nothing is lost. Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`.

## 1. MAP01 v3 is being built (nothing to decide now)

v2 passed its gate on your walk and the menu is approved (D32). v3 densifies
the map (D33): shape in the empty rooms, combat and items by skill, subtler
secrets, toward Freedoom's MAP01 (~200 sectors, ~1200 lines). The PM will
ask you to play it through when the engine pass is clean.

Still open from the design document §13, no hurry:
- **No keys, switch grammar instead.** Built that way on the PM's approval;
  one word from you closes it. Recommended yes.
- **Night-sky strip over the hangar**, yes or no. `SKY1` already exists.

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
history. Bug B2 (`SDPOSTR2`) resolved 2026-10-12. The font serif fix and the batch 3
props, columns C and D (D29). How MAP01 is judged: by walking it (D28). MAP01 v2 passed its gate and the
text menu is approved (D32); MAP01's scale, densify (D33). The bestiary's seven questions (D35). `SDCONC2` and `SDSTAR1` v5, approved
in the map (D30); the hangar wainscot, dropped with them. Bug B3 (art identity
test without `work/`) resolved 2026-10-13. T16, the switch `ANIMDEFS`,
written and seen to flip in engine 2026-10-13.
