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
> | Lore, episode, arsenal, bestiary | `docs/product/LORE.md` |
> | Art direction, palette, texture index, licences | `docs/art/` |
> | Each map's design | `docs/levels/` |
> | Engine contract (MOD-SPEC), balance, ADRs | `docs/engine/` |
> | Gate reviews and playtests | `docs/qa/` |
> | Russian mirror of all of the above | `docs/ru/` |

## Status (2026-10-09)

**F0 — CLOSED (gate G0 PASS).** Pipeline verified end to end:
`tools/build.py` → `dist/sovietdoom.pk3` (empty UDMF MAP01 + MAPINFO +
LANGUAGE en/ru + ZScript EventHandler); `tools/run.sh` launches it on GZDoom
4.14.2 over Freedoom 0.13.0 (`iwads/freedoom2.wad`, gitignored). Evidence in
`docs/qa/GATE-REVIEWS.md`. Suite: **build 11**. Similar-mods research: no
direct competitor (`docs/product/2026-10-09_0017_F0_pm-similar-mods.md`).

**F1 — CLOSED (gate G1 PASS 2026-10-09).** D1–D15 ratified: name Soviet
Doom, Freedoom base, GZDoom 4.14.2, texture sources, one-map v1, PM commits,
docs EN+RU, 1977, two allied factions (Fourth Reich, Liberty Legion),
Sergeant Ramon Vilanova, serious tone, symbols on enemies, lore v1, licence
GPL-3.0 code + CC BY-NC-SA 4.0 assets. Art tooling ready (`.venv/`).

**F2 — in progress: art direction and texture batch 1** ("Soviet base" set,
procedural, 8–12 pieces) by the `art-director`; the CEO validates in the HTML
preview under `docs/art/previews/`. Gate G2 = ≥ 8 approved.

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
`qa-engineer` (gates, PK3 validation, playtests, licences). The PM is the
main session; **the user is the CEO and decides**. The interface between
roles is the artefacts in `docs/`, not the conversation. Agent prompts are
written in Spanish (the CEO's language); their deliverables follow D7.

## Conventions (binding; detail in `docs/WORKING-AGREEMENTS.md`)

- **Language (D7):** docs in English + Russian mirror (`docs/ru/`, same
  path, same task). Code, lumps, classes and comments in English. In-game
  text `[enu default]` and `[ru]`. Chat with the CEO in Spanish.
- **Commits (D6):** the PM commits and pushes; agents never do. Private repo
  `kahache/soviet_doom`.
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
