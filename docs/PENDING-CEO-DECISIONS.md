# Pending CEO decisions

Updated: 2026-10-13, after the CEO closed D40-D43. Ordered by how much
each item unblocks. What closed since the previous update is listed at the
end so nothing is lost. Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`.

## 1. Drafts waiting for your eyes and ears (2026-10-13 evening)

Each preview says what it asks; the recommendation is in brackets.

| What | Preview | Asks |
|---|---|---|
| Reich rifleman, 3D rig, 70 lumps (D38) | `docs/art/previews/2026-10-13_2039_F5_reich-rifleman-rig.html` | approve as drawn and judge in GZDoom [yes], or fixes first (eye slot or gas mask, folds, fall); gib olive [yes] or rust |
| Our own hand and glove (D39) | `docs/art/previews/2026-10-13_1930_F4_hand-glove-sweep.png` | style A-F [E: brown glove, field sleeve, telnyashka] |
| The ice axe, held and pickup (D40) | `docs/art/previews/2026-10-13_2000_F4_ice-axe.png` | swing as drawn; pickup A, B or C [C, upright as in the rack] |
| PPSh-41 first person | `docs/art/previews/2026-10-13_2100_F4_ppsh41.png` | held at the hip, right? |
| Metro fill-out, ten pieces (D42) | `docs/art/previews/2026-10-13_2022_F3_batch2-metro-fill.html` | yes/no per piece; tunnel concrete, tubbing or both [both]; chevrons or plain platform face |
| Weapon sounds, 31 drafts | `docs/art/previews/2026-10-13_2027_F4_weapon-sfx-drafts.html` | per card; A/B/C on six key sounds; clicks and pickups [yes]; reloads [park] (`docs/sound/WEAPON-SOUNDS.md` §9) |
| Enemy sounds, 35 + 8 beds | `docs/art/previews/2026-10-13_2029_F5_enemy-sfx-drafts.html` | per card (`docs/sound/ENEMY-SOUNDS.md` §7) |
| MAP01 music enriched, `D_SDM01E` | `SD_ALLOW_ENGINE=1 .venv/Scripts/python.exe tools/audio/audition.py --play map01 --lump D_SDM01E` | replace the installed `D_SDM01`? |
| Rest of the arsenal in first person, hand E | `docs/art/previews/2026-10-13_2219_F4_arsenal-at-rest.png` and one sheet per weapon (`2026-10-13_2219_F4_*`) | TT-33, IZh-58, RPG-7, ROKS-3 as drawn [yes]; the RPG-7 reload frames C-D, a proposal |
| Hand Katyusha, second pass | `docs/art/previews/2026-10-13_2243_F4_hand-katyusha-pass2.png` | variant A-C [A, closed box]; pickup [D, dropped on its nose]; the raised frame SDHK C [yes, a state change for mod-engineer] |
| Legion trooper, six cells on the rig | `docs/art/previews/2026-10-13_2212_F5_legion-trooper-sweep.html` | cell [C, chrome football pauldrons]; a pink flesh ramp as palette v2 [needed: v1 has no skin] |
| Stormtrooper and Reich hound | `docs/art/previews/2026-10-13_2211_F5_storm-hound-sweep.html` | Stormtrooper [B, chrome coil] or B's coil on D's body; hound [D, crocodile jaw]; the hound's hide darker than BESTIARY 6 (`khaki_olive` 1-9) so it reads on green steel |
| Menu cursor and pause sign (T12) | `docs/art/previews/2026-10-13_2208_F2_shell-cursor-pause-sweep.html` | cursor [A, red star]; pause [P2, a plaque per language; P1 icon as fallback] |
| In-game credits (ADR 009) | Options → Soviet Doom → Credits; `docs/qa/evidence/2026-10-13_2222_F6_credits-en-ru.png` | fine under Options [yes], or a main-menu item (changes the approved menu); add "fan project, not affiliated with id Software"? |
| The radio in MAP01 (D43) | the guard post by the IZh rack, «Колокольчик» | as placed [yes]; MAP01's music restarts from the top on walking away |

## 2. Two decisions that unblock work

- **Kenney's impact pack.** The enemy sounds use 17 of its files (authorised
  by D36); the weapon generator left it out because the terms of the tool the
  pack was made with are unconfirmed. One rule for both: keep Kenney [PM
  recommends yes], or swap those layers for another CC0 pack (about one session).
- **Scores for the three self-sequenced pieces** («Вы жертвою пали»,
  «Амурские волны», Glinka's Patriotic Song, D43). No readable public-domain
  notation without a download. (a) Authorise downloading one public-domain
  score per piece, sizes stated first [recommended], or (b) write them from
  memory, marked NOT VERIFIED, checked by someone who knows the tunes.

Still open from the design document §13, no hurry: no keys (recommended
yes); a night-sky strip over the hangar, yes or no.

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

The ice axe replaces the shovel (D40). MAP02 ships as a practice range (D41). Every music recommendation of SOUNDTRACK §8, accepted (D43). Title screen and intermission (D18). Switch texture: all four variants
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
