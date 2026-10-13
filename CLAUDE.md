# Soviet Doom — project context

A **GZDoom** total conversion (free engine derived from the GPL Doom source):
the USSR of the 1970s invaded by two allied alien factions, Yankee and Nazi,
who defend capital. Protagonist: a Spanish Civil War refugee child turned
Spetsnaz sergeant. This file is the operational summary; product detail and
D-numbered decisions live in `docs/PRD.md`. The CEO is addressed in Spanish;
repo documentation is English with a Russian mirror under `docs/ru/` (D7).

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
> | Russian mirror of all of the above | `docs/ru/` |

## Status (2026-10-13)

**F0, F1, F2 — CLOSED.** Gates G0, G1 and G2 all PASS with evidence in
`docs/qa/GATE-REVIEWS.md`. Twelve textures approved and shipping, including
`SDSTAR1` (emblem, 128×128) and `SDPOSTR1` (Lenin, 128×256, posterised from a
public-domain 1920 photograph). Title screen and intermission ship (D18). The
Cyrillic alphabet is installed, 214 glyphs in two sizes (D24), which is what
makes D7 and D21 possible inside the game at all.

**F3 — MAP01 Zarya-7.** v0 grey box is built and walkable end to end: 44
sectors, 2-3 minutes direct. The CEO walked it and could not get past the
hangar gate, which by design is opened by a switch in the fuel bay; in a grey
box with no light and no red stripe that reads as a wall. Recorded as a gate
criterion for v1, which is being textured now.

**F4 — arsenal.** Seven period weapons in ZScript, all firing, with Freedoom
placeholders for sprites and sounds. Test range on MAP02.

**Tooling.** `tools/verify.py` with `fast`, `full` and `auto` tiers: fast runs
in six seconds and opens no window. `tools/check_pk3.py` validates the package
without the engine; `tools/smoke.py` runs it with the engine. CI on every push.
Suite: **364 tests**, branch coverage of `tools/` **58%**
(`docs/qa/COVERAGE.md`).

**Open with the CEO:** `docs/PENDING-CEO-DECISIONS.md`.

## Setup and commands

```bash
python3 tools/build.py                     # → dist/sovietdoom.pk3
python3 -m unittest discover -s tests -v   # build suite
tools/run.sh                               # build + GZDoom + logs/gzdoom.log
tools/run.sh -nosound +vid_fullscreen 0 +screenshot_dir "$PWD/logs/shots" +"wait 140; screenshot; wait 35; quit"   # QA evidence
python3 -m venv .venv && .venv/bin/pip install pillow numpy   # art tooling
```

GZDoom at `/Applications/GZDoom.app` (brew cask). macOS `screencapture` does
not see the game window: use the engine's `screenshot` command.

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

- **Language (D7):** docs in English + Russian mirror (`docs/ru/`, same
  path, same task). Code, lumps, classes and comments in English. In-game
  text `[enu default]` and `[ru]`. Chat with the CEO in Spanish.
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
