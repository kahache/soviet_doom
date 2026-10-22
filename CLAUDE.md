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

## Status (2026-10-22)

**P4, the full game, is under way (D104-D114): nine maps in three episodes
plus the practice range.** Episode 1 (v1.0): MAP01 Zarya-7, MAP02 the
metro-bunker, MAP03 Tankograd. Episode 2 «The Road to Moscow» (MAP04
Trans-Siberian yard, MAP05 Volga dam, MAP06 Red Square) and Episode 3 «The
Portal» (MAP07 Novaya Zemlya, MAP08 Severomorsk, MAP09 Tunguska) are built,
and every route PASSes in the engine on skills 2, 3 and 4 (18 of 18 reports,
`docs/qa/evidence/2026-10-22_*_report.txt`; last 9133be1). The three episodes
are in the New Game menu; the range is the lump `RANGE`, outside the MAPxx
slots (MOD-SPEC §4.6). Episode 3 ends on «For now… TO BE CONTINUED» (D117). MAP06 and MAP09
use the General as a stand-in boss until the Legion's own bosses exist.
**Decisions up to D114** (`docs/PRD.md`). Per-map design: `docs/levels/`.
The phase view and what is missing: `docs/ROADMAP.md` ("P4 today").

**Installed today (2026-10-22).** Episode 2 and 3 music (20 pieces, composed,
each map plays its A with a random A/B at start and a boss loop in MAP06 and
MAP09; D106, D113). Episode 2 textures (25 approved, D107) and Episode 3's
three sets (D113); the second Episode 2 round and Episode 3's textures are on
disk and applied to the maps but **not yet committed**. The seven enemies
**redrawn with Gemini**, with the swastika armbands the CEO approved (D105,
D108, D109, D114): installed in `assets/sprites/`, **not yet committed**.
The Reich hound's 15 barks and three more voices (D107, D110). Posters
(Lenin, Stalin, the mural) in every map; two slots per map wait for the
Marx and Engels pair, which the CEO has not chosen (`SDPOSTR4/5`).
**Not done:** the Legion gunner and the Colossus exist only as a draft overlay
with provisional sprites (7c162ae), placed in no map; the TT-33 redo with
Gemini (D111); the General's death voice; AKM and world sounds.
Nothing of P4 is in a release yet.

**Releases.** **v1.0 shipped for the CEO's friends (D97):** G6 PASS (4a17a61,
`docs/qa/GATE-REVIEWS.md`, evidence `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`),
tag `v1.0` at d530faa, the GitHub release carries `sovietdoom-1.0.zip` plus
Windows, macOS and Linux one-click packages and the GPL/LGPL sources (P5, D101,
D102); the repo is **public** since 2026-10-20 (D98, D100):
https://github.com/kahache/soviet_doom/releases/tag/v1.0. **v1.1 is a draft**
(not public; target c9414c2): Catalan `[ca]`, the "Press E to continue" death
prompt, the hammer-and-sickle cursor. **Whether to publish v1.1 or wait for a
v1.2 with P4 is the CEO's call** (D109, `docs/PENDING-CEO-DECISIONS.md`).
M1-M4 all PASSED (`docs/ROADMAP.md`); F0-F2 closed (G0-G2).

**Art.** Every asset group the M2 gate names is ours: the seven enemy classes
(redrawn with Gemini, see above) and their four projectiles, the seven weapons
in first person (the TT-33 on Freedoom-based hands, D61, to be redone; the
other six from the CEO's Gemini frames, D79-D88), every pickup (D80), the
player's effects (D82), status bar A with the sergeant's 42 Gemini faces and
digits N2 (D89-D92), EN, RU and CA. Campaign textures are all ours. The
engine's own automap and cheat lines are not.

**Sound and music.** 25 weapon sounds (D74) plus the approved alternatives
(D94); enemy sounds with `$random` groups; 11 of the 12 enemy voices ours (24
Chatterbox takes in D91/D96, three more in D110; the General's death is still
Freedoom's, a new round is drafted); the Reich hound's barks (D107). Still
Freedoom's: the IZh pickup (D94), player, door, switch and item sounds; the 8
beds are packed, unused (P2). Music: title `D_SDINTL`, MAP01 `D_SDM1N2`
(composed, D92/D95), MAP02 `D_SDFUNR`, MAP03 `D_SDGATE`, MAP04-MAP09
`D_SDM04A`...`D_SDM09B` plus boss loops and intermissions (composed MIDI, D106,
D113), range `D_SDM01T`, intermission `D_SDTITL`. Sources and rights: `docs/sound/`.

**Text.** Every in-game string in `[enu default]`, `[ru]` and `[ca]` (173 ids
each on 2026-10-22), the Russian reviewed once (N11, D97), the Catalan accepted
(D110). The `docs/ru/` mirror is P3 (D75) and is synced only at phase close (D34).

**Tooling.** `tools/verify.py` with `fast`, `art`, `full` and `auto` tiers: fast opens
no window (`tests/_tiers.py` decides what is slow). `tools/check_pk3.py` validates the package
without the engine; `tools/smoke.py` runs it with the engine; `tools/route.py`
walks each map's critical route. **Agents never start GZDoom (D26):**
`SD_ALLOW_ENGINE=1` is the PM's, and the PM batches the engine runs. CI runs
on every push (last seen green on 4a17a61, not re-checked since).
Suite: the fast tier ran **2 128 tests** in a clean clone of d530faa (the v1.0
sign-off, 2026-10-20); **not re-measured** since the P4 tests were added.
Branch coverage of `tools/` **82%** (measured at 1088 tests, `docs/qa/COVERAGE.md`).
**Drafts can be played before approval:**
`tools/make_draft_overlay.py` packs the drafted sprites into
`work/overlays/sd-draft-sprites.pk3`, loaded after the mod with `-file`
(MOD-SPEC §6.9). `tools/audio/audition.py` obeys the same engine gate.

**Working machine: the CEO's Windows PC since 2026-10-13** (the project
started on a Mac). GZDoom g4.14.2 on Freedoom 0.13.0 loads the PK3 here with a
clean log (latest engine passes: the Episode 3 routes, 2026-10-22 12:33-12:39; the v1.0 sign-off, `docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`).
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
- **Commits (D6):** the PM commits and pushes; agents never do. Public repo since D100
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
