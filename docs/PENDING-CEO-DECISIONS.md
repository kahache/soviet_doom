# Pending CEO decisions

Updated: 2026-10-12 23:30. Nothing is blocked: every item below can wait while
MAP01 is built. Ordered by how much each one unblocks.
Russian mirror: `docs/ru/PENDING-CEO-DECISIONS.md`.

## 1. Play the weapons test range (15 minutes, unblocks F4 balance)

```
cd ~/Desktop/soviet_doom && MAP=MAP02 tools/run.sh
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

## 2. Title screen — pick a treatment (5 minutes)

`docs/art/previews/2026-10-12_2303_F2_shell-batch1.html` — three complete
treatments (TITLEPIC, INTERPIC, menu logo), each shown at 1×, 2× and in the
4:3 the engine actually displays.

- **A Plakat** — propaganda poster, rocket and rays, «СОВЕТСКИЙ DOOM».
- **B Zarya-7** — the place, not the poster: flat-banded sunset, cosmodrome
  silhouette, rocket on the pad. **Recommended, with A's name block.**
- **C Rodchenko** — typography only, red diagonal on cream, a huge 1977.

Also: the name on screen — hybrid «СОВЕТСКИЙ DOOM», Latin-dominant bilingual,
or Cyrillic-first «СОВЕТСКИЙ ДУМ». Name blocks are interchangeable with any
background.

## 3. MAP01 design — approve so geometry can start

`docs/levels/MAP01-zarya-7.md`. Read the synopsis, the plan and the six
questions at the end. The PM approves it as written. Open points:
- No keys, switch grammar instead (recommended, as in the original MAP01).
- 5-8 minutes, 21/33/46 enemies by skill — longer than Doom II's MAP01 (~2 min).
- A switch texture does not exist and the map uses three: allow an IWAD
  placeholder now, commission ours in batch 2 (PM recommendation).
- Night sky strip over the hangar in v2, yes or no.

## 4. Bestiary — seven questions (`docs/engine/BESTIARY.md` §14)

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

## 5. Music — three questions (`docs/sound/MUSIC-RIGHTS.md`)

- The Soviet anthem: our own instrumental sequence accepting a residual US
  risk, or Glinka's Patriotic Song at zero risk.
- Works free in Russia but restored in the United States, «Священная война»
  above all: exclude them. PM recommends yes, we would host in the US.
- Confirm that most in-game music is **original composition in the idiom of
  the period**, with historical pieces kept for title, intermission and
  diegetic radio. Cheapest, safest, and probably the best sounding.

## 6. Slogan on the Lenin poster

It ships with «ЛЕНИН ЖИВ» ("Lenin lives"). Mayakovsky's full line
«Ленин жил, Ленин жив, Ленин будет жить» also fits in three lines.
