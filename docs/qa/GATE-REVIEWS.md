# Gate reviews

One section per gate. Gates are measured, not argued. Russian mirror:
`docs/ru/qa/GATE-REVIEWS.md`.

## G0 — the pipeline works (F0, MVP) — **PASS** (2026-10-09 00:37)

**Criterion:** GZDoom loads `dist/sovietdoom.pk3` on Freedoom with no error
and no "Unknown" in the log, enters MAP01 and the player stands inside the
room.

**Environment:** Intel Mac (i5-5257U, Iris 6100), macOS 12.7.6, GZDoom
g4.14.2 (Homebrew cask), freedoom2.wad 0.13.0 (SHA-256 verified against the
signed release CHECKSUM).

**Evidence:**
- `docs/qa/evidence/2026-10-09_0037_F0_g0-gzdoom.log`: `adding
  dist/sovietdoom.pk3, 5 lumps` · `MAP01 - SD: Test Range` · `SOVIETDOOM
  loaded: map MAP01 (SD: Test Range)` (ZScript EventHandler) · `Captured
  Screenshot_Doom_20261009_003742.png`. Zero matches for
  `error|Unknown|missing|warning` after the MAPINFO fix.
- `docs/qa/evidence/2026-10-09_0037_F0_g0-map01-freedoom.png`: engine
  screenshot: room with Freedoom's STARTAN2 / FLOOR4_8 / CEIL3_5, player with
  pistol, HUD. No HOM: linedef orientation is correct.
- Suite `tests/`: **build 11/11** OK.
- CEO saw the window open with the empty map (literal verdict, Spanish: "se
  abría y se veía el mapa vacío").

**Findings during the gate:**
- **B1 (closed):** `lookup = "..."` is not accepted inside an `episode` block
  on GZDoom 4.14.2 (`Script error ... Unknown property 'lookup'`). Fixed with
  `name = "$SD_EP01_NAME"` (resolved through LANGUAGE).
- `music = ""` yields silence with no warning (was NOT VERIFIED; now verified).
- macOS `screencapture` does not capture the GZDoom window (Vulkan/MoltenVK);
  visual evidence is taken with the engine's own `screenshot` command
  (`+screenshot_dir` + `+"wait N; screenshot; quit"`). Standard QA method.

**Verdict:** PASS.
