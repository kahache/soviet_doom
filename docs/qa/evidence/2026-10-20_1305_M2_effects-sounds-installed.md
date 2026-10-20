# Engine pass: effects, sounds, music and shell text installed (PM, 2026-10-20 13:05)

Build: main c324f27 in a clean worktree, GZDoom g4.14.2, skill 3.

- `tools/route.py` **g3-auto, metro-critical, tankograd-critical, range-start:
  PASS**, log failures none; no `Unknown sound`, `Missing sprite` or
  `Script error` in any route log (64 enemy sounds, the `$random` groups, the
  new weapon sounds and the 7 voice takes all resolve; `SD_HelpMenu` and the
  GameInfo keys load).
- `2026-10-20_1305_M2_effects-sounds-installed.png`: the RPG-7 firing the
  PG-7V with its smoke and the SDPX burst on the far door; the ROKS-3 jet in
  our orange flame (Freedoom's blue plasma gone).
- Not checked here (`-nosound`): hearing the sounds and the music
  (`currentmusic` needs sound on); the sign-off plan covers it.
