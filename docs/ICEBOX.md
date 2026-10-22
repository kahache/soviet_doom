# Icebox

Living document. Owner: PM. Russian mirror: `docs/ru/ICEBOX.md`.
Good ideas that are not scheduled. An idea that waits on a CEO decision
lives in `docs/PENDING-CEO-DECISIONS.md` instead, never in both. An item
leaves this list only by becoming a commission (with a brief, per
`docs/PIPELINE.md` stage 1) or by being dropped with a reason. Nothing here
blocks anything.

| Since | Idea | Where it came from | What it would take |
|---|---|---|---|
| 2026-10-14 | **Weapon reloads (V3 nice to have, D121: only if Gemini's quota allows the reload frames; not an obligation):** magazines for the TT-33 (8), the PPSh-41 (71-round drum) and the ROKS-3 (fuel tank), with a reload key, so the drafted reload sounds `SDTTRLD`, `SDPPRLD`, `SDRKRLD` can play | D47; the CEO: "apárcalas pero que quede registrado como nice to have"; numbers in `docs/sound/WEAPON-SOUNDS.md` §6 | reopens D39: the TT-33 would drop from 26 to about 19 DPS, the PPSh about 20 %; `mod-engineer` (magazine state, reload key, weapon switch), a new balance pass and MAP01's ammo budget re-measured; the sounds already exist |

## Enemies v2 with Gemini (CEO, 2026-10-20) - DONE (D105-D109, D114)

The Gemini-frames method (D79) gave the best hand-drawn look in the project
(the PPSh-41). After the MVP, consider a **v2 of the seven enemies** from
Gemini images (front/side/back turnarounds, attack and death frames on flat
magenta) processed by `tools/art/gemini_frames.py`, replacing the 3D-rig
sprites. Cost and consistency across 8 rotations to be tested on one enemy
first. Not scheduled; nothing blocks on it.

## V2 content: more weapons, more enemies, more maps (CEO, 2026-10-20) - DONE for V2 (9 maps, AKM, gunner, colossus, Consortium; D112-D119)

After v1 ships, the full game grows on three axes: **more weapons** (new
period Soviet arms, made with the Gemini-frames method, D79), **more
enemies** (new Reich and Legion classes, and the Gemini v2 of the existing
seven noted above), and **more maps** (the 15-20 level campaign of ROADMAP
P4, D69). Not scheduled; each gets its own sweep and the CEO's choice when
P4 starts.

## V3 scope (CEO, 2026-10-23, D119/D120)

V2 closes with the D119 playtest fixes. The CEO chose these for V3 from the PM's
proposals (`docs/product/2026-10-23_P4_propuestas-siguientes-versiones.md`, costs there):

- **A2 - Keys and objects that trigger events when picked up** (thing specials on pickup: open doors, lower walls, release ambushes). The CEO wants it available for level design (D119); it is already used in MAP04 (red key -> gondolas). To do: document the pattern in the level-design guide, offer it in the map generators, retrofit the nine maps.
- **A3 - Map set pieces:** the MAP03 train that starts, the MAP05 dam that bursts, lifts and sinking floors carrying monsters.
- **A4 - RGD-5 hand grenade**, a thrown weapon with its own ammo.
- **B1 - Operations map between levels:** a USSR map with advancing red arrows (intermission).
- **B2 - End-of-episode illustrations** with Gemini (3 images) besides the text.
- **B3 - Medals at the end of an episode** (Hero of the Soviet Union, Order of Lenin...) from kills, secrets and time.
- **B4 - The HUD face redrawn with Gemini** (42 faces) to the level of the new enemies.
- **B5 - Propaganda radio ambience:** loudspeakers that play as the player comes near.
- **D3 - A 60 s trailer** from engine captures and the composed music.

## Dropped (CEO, 2026-10-23, D121)

- Skill 5 renamed "Pyatiletka in one night", humour in posters (D11), painted poster-style menu items (D31): the CEO took them out.

## Proposals pending (CEO, 2026-10-23, D120: not scheduled)

- **A1 - Episode 4** (MAP10-12): through the portal to the invaders' world, or a new invasion elsewhere in the USSR (also PENDING-CEO-DECISIONS §6).
- **A5 - The hand Katyusha** (no such weapon yet; MAP07 keeps its route without it, D121).
- **C1 - A second CEO play-through** at skill 3 after the D119 rebalance.
- **C2 - Secondary attacks:** bayonet on the Mosin, rifle butt on the AKM.
- **C3 - Shield or cover-taking enemies** (a new assault trooper).
- **D1 - Spanish** as a fourth language.
- **D2 - itch.io and ModDB pages** (needs the CEO's account and his OK to publish).

## Orchestrated music (D99; nice to have, stays in the Icebox, D121)

Render our MIDI pieces with real orchestral sound: the CEO's own Pro Tools rig (synths, orchestral plugins) as the baseline; evaluate first a licence-clean orchestral soundfont for GZDoom's MIDI player, then MusicGen-Melody (local, NC weights) as an AI shortcut. Avoid Suno/Udio.

## Small details for v1.1 (CEO, 2026-10-20, D100) - DONE (dog D107, death prompt v1.1)

- *(Drafts 2026-10-21, D102: `work/audio/preview/dog_listening.html`, waiting for the CEO.)* **The Reich hound sounds like a dog:** real barks, growls, a yelp on pain and a whimper on death (licence-clean dog recordings or our synthesis), replacing today's drafts.
- *(Done 2026-10-21 in v1.1, 0f89be2: SD_DeathPrompt; USE reloads the map's entry autosave or restarts MAP01.)* **Continue after death:** today the screen just stays on the dead view. Show a clear prompt (EN/RU, e.g. "Press USE to continue" / «Нажмите ИСПОЛЬЗОВАТЬ, чтобы продолжить») and restart the same level (GZDoom already reloads the level on USE in single player; make it obvious, and consider keeping the weapons the player had at the level's start).
