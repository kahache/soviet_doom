# Engine pass: the campaign pickups installed (PM, 2026-10-20 11:03-11:05)

Build: main e84c56c in a clean worktree, GZDoom g4.14.2, skill 3.

- `tools/route.py` **g3-auto, metro-critical, tankograd-critical: PASS**, log
  failures none (Tankograd's critical path takes the yellow and red passes,
  so the `SD_YellowPass` / `SD_RedPass` Species trick opens locks 3 and 1).
- `2026-10-20_1105_M2_pickups-installed.png`: the pickups summoned in front
  of the player (stacked; the medikit and armours drawn from our sprites) and
  the three pass icons STKEYS0-2 on the status bar after `give`.
- Log: no `Missing sprite` or script error (the `turn` lines are a console
  typo of this test, not the mod).
Not checked one by one: every pickup's animation, the EN/RU messages, the
fullscreen HUD armour icon height.
