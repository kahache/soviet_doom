# Difficulty names — proposal

Owner: PM. Russian mirror pending. Status: **proposal, CEO to choose**.
Requested 2026-10-13: "las 5 dificultades de Doom, molaría por frases con
humor relacionadas con soviet".

Doom's five skills are one of the few places the game is allowed to be funny,
and the original names are first-person confessions of cowardice or bravado
("I'm too young to die", "Hurt me plenty", "Nightmare!"). That voice is what
we keep: the sergeant talking to the recruitment officer. The game's tone
stays serious (D11); this is the one joke the form invites.

Three complete sets. Each line is given in English and Russian because both
ship (D7), and the Russian is the one that has to land.

## Set A — the five-year plan (recommended)

The joke is bureaucratic: difficulty as production quota. It is the most
Soviet idea available and it escalates naturally.

| Skill | English | Russian |
|---|---|---|
| 1 | I am still finishing technical school | Я ещё в техникуме |
| 2 | Fulfil the plan | Выполнить план |
| 3 | Fulfil the plan ahead of schedule | Выполнить план досрочно |
| 4 | Five-year plan in four years | Пятилетку в четыре года |
| 5 | Pyatiletka in one night | Пятилетку за одну ночь |

Skill 5 is Doom's Nightmare slot, where monsters respawn: an impossible quota
and an all-nighter is exactly the register. Skill 1 keeps the original's
"I'm too young" sense without translating it literally.

## Set B — the political officer

The joke is the commissar grading your ideological fitness. Harsher, closer
to the mod's premise, slightly less funny.

| Skill | English | Russian |
|---|---|---|
| 1 | My file says I am sickly | В личном деле: слаб здоровьем |
| 2 | Loyal, with reservations | Предан, но с оговорками |
| 3 | Exemplary conduct | Образцовое поведение |
| 4 | Hero of the Soviet Union, posthumously | Герой Советского Союза, посмертно |
| 5 | They will name a tractor after me | Моим именем назовут трактор |

## Set C — the sergeant himself

Ramon Vilanova's own voice, the Spanish refugee child grown into a Spetsnaz
sergeant. The most character, the least recognisable as a Soviet joke.

| Skill | English | Russian |
|---|---|---|
| 1 | I was evacuated once already | Меня уже один раз эвакуировали |
| 2 | I have seen worse winters | Бывали зимы и похуже |
| 3 | For Barcelona and for Leningrad | За Барселону и за Ленинград |
| 4 | No pasarán, comrades | Но пасаран, товарищи |
| 5 | They took my first country too | Мою первую страну тоже отняли |

Set C's skill 4 is the real Spanish Republican slogan, which the real
children of the war carried into Soviet exile. It is the line that ties D10
to the game's hardest setting, and it is the one I would keep whichever set
wins.

## What the CEO decides

1. Which set, or a mix (each row is independent).
2. Whether skill 5 keeps Doom's respawning monsters, which the names assume.

## Implementation note

These are `MAPINFO` skill definitions with `Name = "$SD_SKILL_N"` and the
strings in `LANGUAGE` under `[enu default]` and `[ru]`. The Russian will not
render until the Cyrillic font lands (debt T9, in progress): until then the
`[ru]` lines are written and correct but display with gaps.
