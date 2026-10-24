# Difficulty names

Owner: PM. Russian mirror: `docs/ru/product/DIFFICULTY-NAMES.md`.
Status: **chosen by the CEO 2026-10-13** from three proposed sets; the ladder
below is assembled from his picks and is what ships.

Doom's five skills are one of the few places the game is allowed to be funny,
and the originals are first-person confessions of cowardice or bravado. That
voice is what we keep: the sergeant answering a recruitment officer. The
game's tone stays serious (D11); this is the one joke the form invites.

## The ladder

| Skill | English | Russian | Where it comes from |
|---|---|---|---|
| 1 | I am still a Pioneer | Я ещё пионер | CEO: "algo con las juventudes Lenin, eso de los pioneros" ("something with the Lenin youth, that Pioneers thing"). The Pioneers took children from nine to fourteen, so this is literally "I'm too young to die" said by a Soviet child, and it needs no joke added |
| 2 | I have seen worse winters | Бывали зимы и похуже | Set C, the sergeant's own voice. Understatement, which is the right register for skill 2 |
| 3 | Not one step back | Ни шагу назад | CEO: "alguna referencia a la batalla de Stalingrado" ("some reference to the Battle of Stalingrad"). Order No. 227, July 1942. The most recognisable sentence of that battle, and at the middle skill it reads as resolve rather than tragedy |
| 4 | No pasarán, comrades | Но пасаран, товарищи | Set C. The Spanish Republican slogan the real children of the war carried into Soviet exile; it ties D10 to the hard setting |
| 5 | Hero of the Soviet Union, posthumously | Герой Советского Союза, посмертно | Set B. Doom's Nightmare respawns monsters, so the joke is that you are signing up to die and the paperwork already knows |

## A swap that stays available (not pending: D20 is ratified)

Skill 5 could instead be **"Pyatiletka in one night" / «Пятилетку за одну
ночь»** (set A), the production-quota joke. Posthumous Hero is darker and
lands better against a skill that respawns the enemies; the quota line is
funnier and keeps the bureaucratic register. The CEO liked both. Either is a
one-line change.

## Implementation

`MAPINFO` skill definitions with `Name = "$SD_SKILL_N"`, strings in `LANGUAGE`
under `[enu default]` and `[ru]`.

**The Russian renders since 2026-10-13** (D24, alphabet C, 214 glyphs; debt
T9 paid): the ladder is on screen in both languages
(`docs/qa/evidence/2026-10-13_0955_F2_skill-ladder-en.png`,
`docs/qa/evidence/2026-10-13_1007_F2_mainmenu-ru.png`). Before that,
Freedoom's ASCII-only font showed the `[ru]` lines with gaps, the same
blocker the language switch had.
