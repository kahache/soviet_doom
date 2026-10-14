# Pending CEO decisions

Updated: 2026-10-13, after the CEO closed D40-D43. Ordered by how much
each item unblocks. What closed since the previous update is listed at the
end so nothing is lost. Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`.

## 1. Waiting for your eyes (2026-10-14 afternoon)

Previews are sent to you as files; the paths are under `docs/art/previews/`.

| What | Preview | Asks [PM's recommendation] |
|---|---|---|
| Stalin poster | `2026-10-14_1601_F2_stalin-sweep.png` | cell [4C, as Lenin]; slogan [«ЗА РОДИНУ! ЗА СТАЛИНА!»]; where it hangs [a sealed wartime shelter in the metro, a secret] |
| Reich hound, German shepherd A, full set (D50) | `2026-10-14_1204_F5_reich-hound-A-full-set.html` | approve; the death seen from 37° [yes] or at the rifleman's 9° |
| Reich rifleman, dark red blood, flat corpse | `2026-10-14_1141_F5_reich-rifleman-blood.html` | approve the death and gib |
| Stormtrooper death redone flat (D53) | `2026-10-14_1151_F5_stormtrooper-E-death-redo.html` | approve |
| 2D hands on the whole arsenal (D52) | `2026-10-14_1200_F4_hand-2d-arsenal.html`; playable with the draft overlay | approve, or name a frame (TT-2, AX-3…); new Blood-style poses for the RPG-7 and IZh? Katyusha hands too big? |
| Metro marble and mosaic in palette v2 | `2026-10-14_1036_F3_metro-palette-v2.html` | mosaic [v2]; marble [v2, narrowly] |

## 2. Waiting for your ears

- Weapon sounds (31, Kenney layers since D44), enemy sounds (35 + 8 beds),
  MAP01 music enriched (`D_SDM01E`).
- New sequenced pieces: «Вы жертвою пали» (`D_SDFUNR`), «Амурские волны»
  (`D_SDAMUR`), and Mussorgsky's «Богатырские ворота» (`D_SDGATE`) in the
  anthem slot instead of Glinka (D54). If you prefer Glinka's «Славься», the
  only clean score sits behind IMSLP's human check: the PM would fetch it by
  hand.

## 3. Your voice takes for the enemies (D36)

The sound-designer is writing `docs/sound/VOICE-SCRIPT.md`: every line in
German or English, with instructions for recording or for AI generation.
Nothing to decide. **Postponed by the CEO on 2026-10-13** ("lo dejamos
pending"): the enemies keep Freedoom's voices until the takes arrive, and
nothing else waits on them.

## 4. Metro set: palette v2 and the mosaic motif

The direction and the first six pieces are approved (D42) and ship as drawn
in palette v1. Two questions from the same sheet are still open
(`docs/art/previews/2026-10-13_0952_F2_batch2-metro-first-pieces.html`):

- **Palette v2.** Add a marble red and a cobalt and gold mosaic ramp in the
  reserved slots? In v1, `SDMARB1` reads ox-blood and `SDMOSA1` slate
  instead of cobalt. Approved textures keep their colours either way
  (ART-BIBLE §3).
- **Mosaic motif.** A star with rays, as drawn, or a figure (cosmonaut,
  worker), which would be its own commission, like Lenin was.

## 5. Smaller, no hurry

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

The ice axe replaces the shovel (D40). MAP02 ships as a practice range (D41; the lump `RANGE` since D62). Every music recommendation of SOUNDTRACK §8, accepted (D43). Title screen and intermission (D18). Switch texture: all four variants
approved and installed (D25). Music model and La Internacional (D23).
Alphabet C (D24). Difficulty ladder (D20; the "Pyatiletka in one night" swap
stays an option, not a pending item). Language switch and Cyrillic
letterforms, level 2 (D21, D22). The engine gate (D26). The Windows PC as the
working machine (D27); the Mac's gitignored `work/` reached the PC the same
afternoon, so D27's "stays on the Mac until the CEO copies it" is now
history. Bug B2 (`SDPOSTR2`) resolved 2026-10-12. The font serif fix and the batch 3
props, columns C and D (D29). How MAP01 is judged: by walking it (D28). MAP01 v2 passed its gate and the
text menu is approved (D32); MAP01's scale, densify (D33). The bestiary's seven questions (D35). The German letters, installed for trial (D37). `SDCONC2` and `SDSTAR1` v5, approved
in the map (D30); the hangar wainscot, dropped with them. Bug B3 (art identity
test without `work/`) resolved 2026-10-13. T16, the switch `ANIMDEFS`,
written and seen to flip in engine 2026-10-13.
