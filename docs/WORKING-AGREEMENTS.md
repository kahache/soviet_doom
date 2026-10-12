# Working agreements

How we work. Operational law: every agent assumes it; only the CEO changes it.
Russian mirror: `docs/ru/WORKING-AGREEMENTS.md`.

**The operational sequence — who stops whom, when to ask the CEO, when to
push — lives in `docs/PIPELINE.md`.** This document holds the rules; that one
holds the order they happen in.

## 1. Roles: an "agent startup"

- Roles live in `.claude/agents/`: `art-director`, `level-designer`,
  `mod-engineer`, `qa-engineer`, plus the routine `translator-ru` and the
  `pmo`, which guards the paper trail and can block a commit. The PM is the
  main session. **The user is
  the CEO and decides.**
- The interface between roles is the artefacts in `docs/`, never the chat
  context. If a role needs something from another, it exists as a document
  or it does not exist.
- Agents never commit. **The PM commits and pushes** (D6), with messages that
  summarise the milestone and cite the reports.
- **Models (CEO decision 2026-10-09):** the main session and the four
  judgement roles (`art-director`, `level-designer`, `mod-engineer`,
  `qa-engineer`) run on the session model (Fable 5.1). **Routine, well
  specified tasks run on Sonnet 5:** the `translator-ru` agent is pinned to it
  in its definition, and the PM launches other mechanical subtasks (PK3
  validators, boilerplate, file conversions, batch renames) with the Sonnet
  model explicitly. Anything that needs taste or judgement stays on the
  session model.

## 2. Decisions

- Product and technical decisions are recorded in `docs/PRD.md` §5 as D1,
  D2, … with date and rationale. They are immutable; to change one, a new
  decision amends it.
- Open items live in `docs/PENDING-CEO-DECISIONS.md`, shown by the session
  hook at every start. First action of a session: ask the CEO the open items,
  in Spanish, by priority.
- Good ideas for later go to `docs/ICEBOX.md`.

## 3. Phases and gates

- The roadmap advances through phases with measurable gates defined before
  the phase starts. Verdicts live in `docs/qa/GATE-REVIEWS.md` with evidence.
- First measurement is honest and strict. Never inflate a number to pass.

## 4. Documents (D7)

- Living docs (stable name): `CLAUDE.md`, PRD, ROADMAP, LORE, ART-BIBLE,
  MOD-SPEC, GATE-REVIEWS, TEXTURE-INDEX, LICENSES.
- Dated snapshots (immutable): `YYYY-MM-DD_HHMM_FN_slug.md` under
  `docs/<area>/`.
- **English is canonical; every document has a Russian mirror at the same
  path under `docs/ru/`**, delivered in the same task. Code, lump names and
  comments in English. In-game text in English and Russian.
- `CLAUDE.md` always carries a current "Status" block, updated at the end of
  every work session.

## 5. Quality

- Every validated behaviour has a test. Suites are cited by number at each
  close ("build 11"); if a number drops, something broke.
- Magic numbers become named constants with a comment on why.
- Assets: nothing enters `assets/` without CEO approval; every foreign asset
  has origin and licence in `docs/art/LICENSES.md`.
- GZDoom must load with zero `Script error`, `Unknown`, `Missing`.

## 6. Working with the CEO

- The CEO decides everything about product; the PM proposes with a clear
  recommendation and honest options.
- The CEO has not made Doom mods: new concepts are explained in one sentence.
- CEO feedback on real results is gold: quoted literally in reports, turned
  into numbered bugs and named patterns.
- Radical honesty: hypotheses are labelled; what is not verified in the
  ZDoom wiki or the engine log is marked NOT VERIFIED.
