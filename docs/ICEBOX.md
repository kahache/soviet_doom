# Icebox

Living document. Owner: PM. Russian mirror: `docs/ru/ICEBOX.md`.
Good ideas that are not scheduled. An idea that waits on a CEO decision
lives in `docs/PENDING-CEO-DECISIONS.md` instead, never in both. An item
leaves this list only by becoming a commission (with a brief, per
`docs/PIPELINE.md` stage 1) or by being dropped with a reason. Nothing here
blocks anything.

| Since | Idea | Where it came from | What it would take |
|---|---|---|---|
| 2026-10-14 | **Weapon reloads (nice to have):** magazines for the TT-33 (8), the PPSh-41 (71-round drum) and the ROKS-3 (fuel tank), with a reload key, so the drafted reload sounds `SDTTRLD`, `SDPPRLD`, `SDRKRLD` can play | D47; the CEO: "apárcalas pero que quede registrado como nice to have"; numbers in `docs/sound/WEAPON-SOUNDS.md` §6 | reopens D39: the TT-33 would drop from 26 to about 19 DPS, the PPSh about 20 %; `mod-engineer` (magazine state, reload key, weapon switch), a new balance pass and MAP01's ammo budget re-measured; the sounds already exist |
| 2026-10-13 | Skill 5 named "Pyatiletka in one night" / «Пятилетку за одну ночь» instead of "Hero of the Soviet Union, posthumously" | `docs/product/DIFFICULTY-NAMES.md`; the CEO liked both, D20 chose the latter | one line in `LANGUAGE`, both languages |
| 2026-10-12 | Humour in posters once the serious tone is established | D11 | a poster batch with the CEO's wording |
| 2026-10-13 | Menu items as painted poster-style graphics (treatment C), one set per language, if the text menu of D31 ever looks too plain | D31; the CEO: "anota como pendiente en el futuro hacer C si fuera necesario" | `art-director`: a painted set in EN and RU plus `MENUDEF` back to `PatchItem`; roughly the cost of the shell screens (D18) |

## Enemies v2 with Gemini (CEO, 2026-10-20)

The Gemini-frames method (D79) gave the best hand-drawn look in the project
(the PPSh-41). After the MVP, consider a **v2 of the seven enemies** from
Gemini images (front/side/back turnarounds, attack and death frames on flat
magenta) processed by `tools/art/gemini_frames.py`, replacing the 3D-rig
sprites. Cost and consistency across 8 rotations to be tested on one enemy
first. Not scheduled; nothing blocks on it.

## V2 content: more weapons, more enemies, more maps (CEO, 2026-10-20)

After v1 ships, the full game grows on three axes: **more weapons** (new
period Soviet arms, made with the Gemini-frames method, D79), **more
enemies** (new Reich and Legion classes, and the Gemini v2 of the existing
seven noted above), and **more maps** (the 15-20 level campaign of ROADMAP
P4, D69). Not scheduled; each gets its own sweep and the CEO's choice when
P4 starts.

## Orchestrated music (D99, V2)

Render our MIDI pieces with real orchestral sound: the CEO's own Pro Tools rig (synths, orchestral plugins) as the baseline; evaluate first a licence-clean orchestral soundfont for GZDoom's MIDI player, then MusicGen-Melody (local, NC weights) as an AI shortcut. Avoid Suno/Udio.

## Small details for v1.1 (CEO, 2026-10-20, D100)

- *(Drafts 2026-10-21, D102: `work/audio/preview/dog_listening.html`, waiting for the CEO.)* **The Reich hound sounds like a dog:** real barks, growls, a yelp on pain and a whimper on death (licence-clean dog recordings or our synthesis), replacing today's drafts.
- *(Done 2026-10-21 in v1.1, 0f89be2: SD_DeathPrompt; USE reloads the map's entry autosave or restarts MAP01.)* **Continue after death:** today the screen just stays on the dead view. Show a clear prompt (EN/RU, e.g. "Press USE to continue" / «Нажмите ИСПОЛЬЗОВАТЬ, чтобы продолжить») and restart the same level (GZDoom already reloads the level on USE in single player; make it obvious, and consider keeping the weapons the player had at the level's start).
