# Soviet Doom — project context

A **GZDoom** total conversion (free engine derived from the GPL Doom source):
the USSR of the 1970s invaded by two allied alien factions, Yankee and Nazi,
who defend capital. Protagonist: a Spanish Civil War refugee child turned
Spetsnaz sergeant. This file is the operational summary; product detail and
D-numbered decisions live in `docs/PRD.md`. The CEO is addressed in Spanish;
repo documentation is English with a Russian mirror under `docs/ru/`,
synced in batches at each phase close (D7, D34).

> Every document has **one owner** of what it tells; the others link instead
> of repeating.
>
> | What | Where |
> |---|---|
> | Product, theme, **D-numbered decisions** | `docs/PRD.md` |
> | **Phases and gates** | `docs/ROADMAP.md` |
> | Open decisions that block | `docs/PENDING-CEO-DECISIONS.md` |
> | How we work (roles, gates, docs, language) | `docs/WORKING-AGREEMENTS.md` |
> | **The pipeline** (stages, ownership, when to ask the CEO, when to push) | `docs/PIPELINE.md` |
> | Lore, episode, arsenal, bestiary | `docs/product/LORE.md` |
> | Art direction, palette, texture index, licences | `docs/art/` |
> | Each map's design | `docs/levels/` |
> | Engine contract (MOD-SPEC), balance, ADRs | `docs/engine/` |
> | Gate reviews and playtests | `docs/qa/` |
> | Good ideas not scheduled (nothing in it blocks) | `docs/ICEBOX.md` |
> | Music, sound, music rights | `docs/sound/` |
> | Product notes and dated studies (difficulty names, language switch, research) | `docs/product/` |
> | Russian mirror of all of the above | `docs/ru/` |

## Status (2026-10-13)

**F0, F1, F2 — CLOSED.** G0 and G2 PASS with evidence in
`docs/qa/GATE-REVIEWS.md`; G1 was ratified by the CEO on 2026-10-09
(`docs/ROADMAP.md`) and its GATE-REVIEWS entry is written retrospectively on
2026-10-13. Thirty texture lumps live in `assets/`, all approved:
batch 1, 12 of 12 (`SDPOSTR1` Lenin 128×256 among them; `SDCONC2` and
`SDSTAR1` v5 approved inside MAP01 by the CEO, D30), the eight switches of
batch 2 (D25) and four props of batch 3, crates and a locker (D29), plus
the metro's first six pieces (D42); ten more metro pieces are drafts. Title screen and
intermission ship (D18). The Cyrillic alphabet is installed, 224 glyphs (German Ä Ö Ü ß since D37) in
two sizes (D24), which is what makes D7 and D21 possible inside the game;
M, М and W were corrected on 2026-10-13 (D29).

**F3 — MAP01 Zarya-7.** v0 (grey box) and v1 (textured and signposted: red
stripe, yellow lane, recessed doors; 54 sectors) are BUILT,
`docs/levels/MAP01-zarya-7.md` §14-§15. The v0 playtest finding (the hangar
gate read as a dead end) became v1's gate criterion. **The CEO walked v1 on
2026-10-13 and the criterion is not met:** "ahora sí que funciona", but "me
quedé en el hangar; la puerta doble no se abre". Not a mechanical bug: the
PM pressed SW-A in engine and D4 opened
(`docs/qa/evidence/2026-10-13_1540_F3_map01-v1-swa-opens-d4.png`); the CEO
later found SW-A unaided ("una puerta q no hace ningún ruido si le das a
E") and finished the map. **v2 is BUILT** (§16 of the design document): real
switch faces, SW-A moved to a lit niche with a window onto D4, a gate light
on tag 30, 16 lamps, flicker, three secrets, crates and lockers; 80 sectors.
Its engine pass is filed (`docs/qa/evidence/2026-10-13_1611_F3_map01-v2-engine-pass-*`).
**The CEO walked v2: gate passed without help, menu approved (D32).** Too
small for a game level, so **v3 densifies it (D33) and is BUILT**: 165
sectors, 778 lines (Freedoom's MAP01: 211 / 1274), 33 enemies on skill 3
(21/33/46), Reich first and the Legion holding the hangar (D35), both
switches release an ambush, subtler secrets, Lenin lit. Engine pass clean
(`docs/qa/evidence/2026-10-13_1708_F3_map01-v3-engine-pass-*`). **The CEO played
it through on skill 3: "ha sido MUY divertido!!" (D38).** The mural is clear
and the slot-1 weapon is found on the dorm rack, not issued (both seen in
engine). **G3 in progress:** `tools/route.py` runs the critical path in
GZDoom and passes on skills 2, 3 and 4 with monsters (with `god`, the route
clearing and listing the bodies in its way); left: the hand-played runs
on skills 2 and 4, the hostile pass and the CEO's G3-9, `docs/qa/GATE-REVIEWS.md`.

**F5 — bestiary, started.** The seven enemies of D35 are playable ZScript
actors with Freedoom sprites and sounds as placeholders, replacing Doom's
monsters so maps need no renumbering; drops are our ammo (D35); the
General summons two recruits once. Engine pass on MAP02's gallery clean
(`docs/qa/evidence/2026-10-13_1705_F5_map02-bestiary-*`). Own sprites wait
on the CEO's gate: the Reich rifleman is drafted from a 3D rig (D38), the
enemies' non-voice sounds are drafted, the voices wait on the CEO's takes
(D36).

**F4 — arsenal.** Seven period weapons in ZScript, all firing, with Freedoom
placeholders for sprites and sounds; balance stands as built (D39). Slot 1
is an ice axe (D40). Drafts at the CEO's gate: our own hand and glove, the
ice axe, the PPSh-41, 31 weapon sounds. MAP02 ships as a practice range, a
second episode on New Game (D41).

**Music (D43).** The Internationale (`D_SDINTL`, credit Jerry Engelbach) is
wired as the title music, NOT VERIFIED in engine; MAP01 plays our own
`D_SDM01` (seen with `currentmusic`); an enriched draft waits on the
CEO; three self-sequenced pieces wait on a score source.

**Tooling.** `tools/verify.py` with `fast`, `full` and `auto` tiers: fast runs
in six seconds and opens no window. `tools/check_pk3.py` validates the package
without the engine; `tools/smoke.py` runs it with the engine. **Agents never
start GZDoom (D26):** `SD_ALLOW_ENGINE=1` is the PM's, and the PM batches the
engine runs. CI on every push.
Suite: **916 tests** (2026-10-13 evening), one skip (the opt-in engine test), no expected
failure; branch coverage of `tools/` **79%** (measured at 914 tests on this
PC, `docs/qa/COVERAGE.md`). `audition.py` is at 98%; the largest gaps are
three files no test imports, then `gen_menu.py` and `gen_switch.py`.
`tools/audio/audition.py` obeys the same engine gate as `run.sh` and
`smoke.py` since the same day.

**Working machine: the CEO's Windows PC since 2026-10-13** (the project
started on a Mac). GZDoom g4.14.2 on Freedoom 0.13.0 loads the PK3 here with
zero errors (`tools/smoke.py`, VERDICT PASS on MAP01 and MAP02, 2026-10-13;
the filed run is `docs/qa/evidence/2026-10-13_1448_F3_smoke-map01-windows.log`
and its MAP02 twin, with screenshots). The Mac's gitignored
`work/` arrived the same afternoon as the release asset
`transfer-work-2026-10-13` on the private repo: 785 files plus its logs,
every one checked against the Mac's own SHA-256 manifest (kept as
`work/MANIFEST-from-mac.txt`). With it, `tools/verify.py art` here ran 384 (that afternoon)
tests with one skip, the opt-in engine test: the asset identity checks and
the Lenin generator tests now run on this PC too.

**Open with the CEO:** `docs/PENDING-CEO-DECISIONS.md`.

## Setup and commands

```bash
python3 tools/build.py                     # → dist/sovietdoom.pk3
python3 -m unittest discover -s tests -v   # build suite
python3 tools/verify.py fast               # the working loop: build, check_pk3, suite, no window
SD_ALLOW_ENGINE=1 tools/run.sh             # build + GZDoom + logs/gzdoom.log (the gate: agents never set it)
SD_ALLOW_ENGINE=1 tools/run.sh -nosound +vid_fullscreen 0 +screenshot_dir "$PWD/logs/shots" +"wait 140; screenshot; wait 35; quit"   # QA evidence
python3 -m venv .venv && .venv/bin/pip install pillow numpy coverage       # art tooling, macOS/Linux
python -m venv .venv && .venv/Scripts/pip install pillow numpy coverage   # art tooling, Windows
```

**Two machines, found automatically by `run.sh`, `smoke.py`, `verify.py` and
`audition.py`.** macOS: GZDoom at `/Applications/GZDoom.app` (brew cask),
venv at `.venv/bin/python`. Windows: GZDoom g4.14.2 unzipped at
`%LOCALAPPDATA%\Programs\GZDoom\gzdoom.exe`, `freedoom2.wad` 0.13.0 in
`iwads/` (SHA-256 checked against the signed release CHECKSUM), scripts run
under Git Bash, `python` is 3.14 and the venv is `.venv/Scripts/python.exe`.
On both, screenshots come from the engine's own `screenshot` command (macOS
`screencapture` does not see the window).

**Text-bearing assets do not reproduce across the two machines.** Measured
2026-10-13 by regenerating batch 1 and the switches on Windows: the nine
text-free lumps are byte-identical to `assets/`; `SDPOSTR1` (Lenin, slogan
in Impact) was not regenerated, its reference photograph being still on the
Mac at the time; `SDDOOR1` (52 px),
`SDPOSTR2` (386 px) and the eight switches (~180 px each, all inside the
painted word) differ, because Windows' Impact rasterises differently from
macOS'. Windows also lacks Arial Narrow Bold (Arial Bold is the fallback, a
wider face), so sheet labels and the shell screens' small text differ too.
Rule: an approved asset is regenerated only on the machine that rendered it,
or it goes back to the CEO as a new proposal. `tests/test_art.py` is the
tripwire: it compares `assets/` with `work/`, and `work/` now holds the
Mac's renders, so running a text-bearing generator on this PC overwrites
them and turns the suite red. Run generators for NEW work only, and for a
text-bearing approved asset restore the Mac file (from the release asset)
rather than committing around the red test.

## Agent team ("agent startup")

Roles in `.claude/agents/`: `art-director` (visual direction, textures,
sprites, previews), `level-designer` (UDMF maps, flow, light, balance),
`mod-engineer` (PK3, build, ZScript, definition lumps, ADRs) and
`qa-engineer` (gates, PK3 validation, playtests, licences), plus two routine roles on
Sonnet 5: `translator-ru` (Russian mirrors) and `pmo` (guards the paper trail
and can block a commit, stage 6 of the pipeline). `sound-designer` owns music
and audio. The PM is the main
session; **the user is the CEO and decides**. The interface between
roles is the artefacts in `docs/`, not the conversation. Agent prompts are
written in Spanish (the CEO's language); their deliverables follow D7.

## Conventions (binding; detail in `docs/WORKING-AGREEMENTS.md`)

- **Language (D7, amended by D34):** docs in English; the Russian mirror
  (`docs/ru/`, same path) is synced in a batch at each phase close and in
  full before release, not in the same task. Code, lumps, classes and
  comments in English. In-game text `[enu default]` and `[ru]` **always, in
  the same task**. Chat with the CEO in Spanish.
- **Commits (D6):** the PM commits and pushes; agents never do. Private repo
  `kahache/soviet_doom`.
- **Models:** judgement roles on the session model; routine subtasks
  (translation, validators, boilerplate) on Sonnet 5, via `translator-ru` or
  the Agent `model: sonnet` option.
- **Less to more:** every delivery is playable or visible.
- **The CEO validates by looking:** textures in HTML previews, maps in
  GZDoom. Nothing enters `assets/` without explicit approval.
- **Licences:** no assets from commercial games. Every foreign asset has
  origin and licence in `docs/art/LICENSES.md`.
- Magic numbers → named constants. Every validated behaviour has a test.
  Gates are measured, not argued. GZDoom loads with zero errors.
- Documents: living (stable name) vs dated snapshots `YYYY-MM-DD_HHMM_FN_slug.md`.
- **Radical honesty:** hypotheses are labelled; anything not verified in the
  ZDoom wiki or the engine log is marked NOT VERIFIED.
