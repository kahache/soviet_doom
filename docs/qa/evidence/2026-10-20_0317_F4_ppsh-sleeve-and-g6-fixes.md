# Engine pass: PPSh sleeve fix and QA-G6-1/2 (PM, 2026-10-20 03:17)

Build: main 362df5a, GZDoom g4.14.2, MAP01 skill 3, 16:9 (711x400),
fullscreen HUD (the tooling config kept `screenblocks 11`). Sheet
`2026-10-20_0317_F4_ppsh-sleeve-and-g6-fixes.png`.

- **QA-G6-2:** at map start nothing is printed at the top of the screen;
  the log keeps `SOVIETDOOM loaded: map MAP01 (Космодром «Заря-7»)`.
- **PPSh:** the right arm now runs off the right edge as a plain olive
  sleeve; ready and firing (kick, flash) drawn.
- **QA-G6-1:** after `language eng`, `openmenu SD_OptionsMenu` opens without
  a crash and the row reads **English**. Not checked: `enu`, `rus`, empty.
Log: no `Missing sprite`, `Script error` or `Unknown`.
