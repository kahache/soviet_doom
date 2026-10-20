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
| 2026-10-13 | Repaint the status bar's AMMO/HEALTH/ARMS/ARMOR into Cyrillic | `docs/engine/MOD-SPEC.md` §6.5 (D17 note) | F6, `art-director`, one pass with the rest of the HUD art |
| 2026-10-12 | Humour in posters once the serious tone is established | D11 | a poster batch with the CEO's wording |
| 2026-10-13 | Menu items as painted poster-style graphics (treatment C), one set per language, if the text menu of D31 ever looks too plain | D31; the CEO: "anota como pendiente en el futuro hacer C si fuera necesario" | `art-director`: a painted set in EN and RU plus `MENUDEF` back to `PatchItem`; roughly the cost of the shell screens (D18) |

## Enemies v2 with Gemini (CEO, 2026-10-20)

The Gemini-frames method (D79) gave the best hand-drawn look in the project
(the PPSh-41). After the MVP, consider a **v2 of the seven enemies** from
Gemini images (front/side/back turnarounds, attack and death frames on flat
magenta) processed by `tools/art/gemini_frames.py`, replacing the 3D-rig
sprites. Cost and consistency across 8 rotations to be tested on one enemy
first. Not scheduled; nothing blocks on it.
