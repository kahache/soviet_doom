# Engine pass: the 25 weapon sounds load (PM, 2026-10-15 01:17)

Build: main 70358e0, GZDoom g4.14.2, RANGE skill 3, `-nomonsters`,
**`-nosound`** (01:17 at night, the CEO asleep): `give all`, each slot 1-7
selected and fired for 30 tics, then `take ammo` and the TT-33 fired empty.

Log: no `Unknown sound`, `Missing sprite`, `Script error`, error or warning
line; the new classes (`SD_IceAxePuff`, `SD_WeaponSounds`) compile and every
weapon's Fire and Ready states run with the new hooks. **NOT HEARD:** levels,
the click logic, the puff sound and the channels — the listening checklist
in `docs/sound/WEAPON-SOUNDS.md` §10.4 is owed (PM with sound, or the CEO).
