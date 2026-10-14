# M3 listening sheet (2026-10-14 23:55, sound-designer)

One page for the CEO's ear: `2026-10-14_2355_M3_listening-sheet.html`, 80 rows to judge (OK / NO / ? + note) and 3 optional.
Counts: weapons 31 (6 with takes A/B/C), enemies 35, beds 8, music 6 (title `D_SDINTL`, MAP01 `D_SDM01` and draft `D_SDM01E`, MAP02 `D_SDFUNR`, MAP03 `D_SDGATE`, RANGE `D_SDAMUR`); optional `D_SDTITL`, `D_SDRAD1`, `D_SDRAD2`.
Each row plays the draft and, below it, what the game plays today (Freedoom lump read from `iwads/freedoom2.wad`, or "silence").
Audio is read by relative path from `work/audio/sfx/` and `work/audio/preview/` (gitignored): keep the page in `docs/art/previews/`.
Music was rendered to OGG with GZDoom's own `zmusic.dll` + `gzdoom.sf2` (no engine started); `D_SDTITL` matched the Mac engine render sample for sample (correlation 0.9999996).
Takes B/C were extracted from the 2026-10-13 and 2026-10-14 weapon previews; take A on those pages is byte-identical to `work/audio/sfx/weapons/ogg/`.
Answers persist in the browser (localStorage); "Copiar resultado" puts `OK / NO / ? / tomas / notas` on the clipboard and in a textarea.
Open it: `Start-Process "C:\Users\littl\Desktop\Claude\soviet_doom\docs\art\previews\2026-10-14_2355_M3_listening-sheet.html"`
Not included: the 12 enemy voices (D37, waiting on the CEO's takes).
