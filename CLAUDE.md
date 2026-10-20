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

## Status (2026-10-20)

**Where the MVP stands** is told by `docs/ROADMAP.md` (milestones M1-M4 and
their gates, D63), the tasks by `docs/BACKLOG.md`, and the dated snapshot
`docs/product/2026-10-20_1045_P0_mvp-status.md`. In one line: **M1 PASSED**
(D70), M2 ~41 % of its asset groups ours, M3 25 of 61 approved effects
installed, M4 licences, credits and README done; decisions up to **D85**.

**F0, F1, F2 — CLOSED** (G0, G1, G2 in `docs/qa/GATE-REVIEWS.md`). The old
phases F3-F5 fold into M1-M3 (ROADMAP); G3's hostile pass and hand-played
runs are parked to P1 (D60).

**The campaign (D60, D62).** Three maps, numbered in play order since D62:
MAP01 Zarya-7 (v3, D38) → MAP02 the metro-bunker (v1) → MAP03 the factory,
«Танкоград» / Tankograd (v1.1, D68), which ends the episode at the portal;
every route PASSes in engine (`tools/route.py`) and the CEO walked it (D70).
Each crossing prints a transition text and the ending prints once
(`docs/engine/MOD-SPEC.md` §4.6). The practice range is the lump `RANGE`,
outside the MAPxx slots, retextured with our set (d8062e4). Dated evidence
keeps the old numbers (a `map03` there is the metro, a `map02` the range).
Campaign textures are all ours (M2 audit,
`docs/qa/2026-10-14_2357_M2-freedoom-audit.md`).

**Bestiary.** All seven enemy classes draw our own sprites (D49-D56, D67,
D70, D73), with the General's shell and the Stormtrooper's bolt ours; the
Doughboy's and Panzermensch's shells are approved (D81) and queued.

**Arsenal.** Seven period weapons in ZScript, balance as built (D39), slot 1
the ice axe (D40). In first person the TT-33 (Freedoom-based hands, D61) and
the PPSh-41 (Gemini frames, D79) are ours; the IZh-58, RPG-7, ROKS-3 and
hand Katyusha are approved from Gemini frames (D84) and queued; the ice
axe's strike frame is being redrawn (D84). World pickups ours except the
hand Katyusha's; health, armour, keys, map and backpack (D80) are being
installed. Player effects (D82) approved, queued.

**Sound and music.** The 25 weapon sounds of D74 are installed (70358e0);
D83 approved 30 enemy sounds, 5 beds and SDIZFIR B (install queued, N9e);
enemies keep Freedoom's voices until the MVP ships (D85; then Chatterbox
from the CEO's own voice, P2). The
Internationale (`D_SDINTL`) plays on the title, `D_SDFUNR` on MAP02 and
`D_SDGATE` on MAP03 (approved D83); MAP01 still plays `D_SDM01`, which D83
moves off MAP01; the intermission still plays Freedoom's `D_DM2INT` until
`D_SDTITL` installs. Music sources: `docs/sound/`.

**Tooling.** `tools/verify.py` with `fast`, `art`, `full` and `auto` tiers: fast opens
no window (`tests/_tiers.py` decides what is slow). `tools/check_pk3.py` validates the package
without the engine; `tools/smoke.py` runs it with the engine. **Agents never
start GZDoom (D26):** `SD_ALLOW_ENGINE=1` is the PM's, and the PM batches the
engine runs. CI on every push (green on dc49b40).
Suite: the fast tier ran **1 792 tests** at 892cfc7 (2026-10-20, 241 skipped:
slow or imaging/`work/`-dependent); branch coverage of `tools/` **82%**
(measured at 1088 tests, `docs/qa/COVERAGE.md`). **Drafts can be played before approval:**
`tools/make_draft_overlay.py` packs the drafted sprites into
`work/overlays/sd-draft-sprites.pk3`, loaded after the mod with `-file`
(MOD-SPEC §6.9). `tools/audio/audition.py` obeys the same engine gate.

**Working machine: the CEO's Windows PC since 2026-10-13** (the project
started on a Mac). GZDoom g4.14.2 on Freedoom 0.13.0 loads the PK3 here with a
clean log (latest engine pass `docs/qa/evidence/2026-10-20_0317_F4_ppsh-sleeve-and-g6-fixes.md`).
The Mac's gitignored `work/` arrived as the release asset
`transfer-work-2026-10-13` on the private repo (manifest
`work/MANIFEST-from-mac.txt`); the art tier's identity tests need it.

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
and can block a commit, stage 7 of the pipeline, after Product updates what is done and not (stage 6, D64)). `sound-designer` owns music
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
