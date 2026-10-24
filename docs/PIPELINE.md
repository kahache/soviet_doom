# The pipeline — how work moves from idea to GitHub

Owner: PM. Enforced by the `pmo` agent. Russian mirror:
`docs/ru/PIPELINE.md` (bug **Q1**, found by `tools/verify.py docs` on
2026-10-13 and closed the same day).
Created 2026-10-13 at the CEO's request. **Every rule below was paid for by a
real mistake in this project**; the mistake is cited so nobody relitigates it.

`docs/WORKING-AGREEMENTS.md` says *what the rules are*. This document says
*in what order things happen, and who stops whom*.

## The eight stages

```
1 COMMISSION   PM writes the brief, declares file ownership
2 DRAFT        cheap, reviewable, thrown away if wrong
3 PM REVIEW    the PM judges before the CEO ever sees it
4 CEO GATE     only what needs taste or authority reaches the CEO
5 VERIFY       tools/verify.py - fast in the loop, full before a push
6 PRODUCT      when a delivery closes, Product records what is done and what is not
7 DOCUMENT     the pmo agent checks the paper trail before anything is committed
8 PUBLISH      the PM commits specific paths and pushes
```

### 1. Commission

The PM writes every brief and **must** state three things:

- **Files the agent owns.** Nobody else writes them in that window.
- **Files the agent must not touch**, naming the other agents in flight.
- **How it will be verified**, with the exact commands.

> Why: on 2026-10-12 two agents and the PM edited `TEXTURE-INDEX.md`,
> `ART-BIBLE.md` and `PENDING-CEO-DECISIONS.md` in the same window and left the
> repo contradicting itself (bug **B2**). Ownership is declared, not assumed.

Agents never commit (D6). Judgement roles run on the session model; routine,
well-specified work runs on Sonnet (`translator-ru`, validators, boilerplate).

### 2. Draft

**Visual or creative work produces a cheap draft first, never a finished
artefact.** For images that means a **sweep sheet**: one image with many
variants across a parameter, labelled, so the reviewer points at a cell.

> Why: the `SDSTAR1` emblem took five rounds of finished drawings because the
> PM described the geometry from memory and each correction cost a full cycle.
> The Lenin poster then took four, until a 15-cell sweep settled it in one.
> **A sweep is the unit of visual review.**

Rules that follow from it:
- Draw the thing alone before putting it in a texture, a map or a screen.
- Derive from the source material; a hand-traced approximation loses what
  made the source right (Lenin v3: "no se parece a él EN NADA" (CEO: "it looks nothing like him")).
- The agent looks at its own output **once**. Iterating on your own images in
  a growing context is what makes a task expensive.

### 3. PM review

The PM looks at the artefact and forms **its own** verdict before forwarding.

> Why: an agent recommended Lenin variant B as readable. It was not. Passing
> an agent's optimism to the CEO wastes the CEO's attention, which is the
> scarcest resource in the project.

If the PM's verdict differs from the agent's, the PM says so and says why.
If the PM can verify a claim, it verifies it rather than relaying it: blocker
**M1** (approved art never reached the PK3) was confirmed in one command.

### 4. CEO gate — when to stop and ask

**Stop and ask** when, and only when:
- It needs **taste**: art, map feel, naming, tone.
- It needs **authority**: scope, licence, money, anything public.
- It is **irreversible or outward-facing**: publishing, deleting, a public repo.
- Two readings of the request would produce materially different work.
- A gate verdict is debatable. Gates are measured, never argued.

**Do not stop** for: anything already decided in `docs/PRD.md` §5; a mechanical
consequence of something the CEO already approved; a fix to our own bug; a
reversible choice with an obvious default. In those cases act, then report.

> Why: the CEO's words, 2026-10-12 — "entonces no está pendiente de mí. Tira
> millas." ("then it is not waiting on me. Keep going.") Three items had been parked as CEO decisions when none of them
> needed one.

When asking, the PM sends: the artefact or the command to run it, a
recommendation, and the cost of each option. Never a bare question.

Everything open lives in `docs/PENDING-CEO-DECISIONS.md`, ordered by how much
each item unblocks, and the session hook shows it at every start.

### 5. Verify — one command, two levels

There is one entry point, `tools/verify.py`, and it runs the four greens for
you in the right order, stopping at the first red one:

```
python3 tools/verify.py fast    # the working loop. Never opens a window.
python3 tools/verify.py full    # before a push, at a phase close, at a gate.
python3 tools/verify.py auto    # reads git, picks the level, says why.
python3 tools/verify.py auto --explain   # says what it would do, runs nothing
```

**The engine gate (D26).** `tools/run.sh` and `tools/smoke.py` refuse to
start GZDoom unless `SD_ALLOW_ENGINE=1` is set, and **only the PM sets it**.
An agent whose change needs the engine verifies with `fast`, writes in its
summary that the engine run is owed, and stops; the PM batches those runs,
and `full` is therefore a PM-only level. Every role that runs tooling says
so in its definition (`art-director`, `level-designer`, `mod-engineer`,
`qa-engineer`, `sound-designer`; `pmo` and `translator-ru` run none). The
gate sits in every tool that can start the engine: `tools/run.sh`,
`tools/smoke.py` and `tools/audio/audition.py` (`--play`, `--render`).

> Why: on 2026-10-13 two agents were opening three or four GZDoom windows
> every twenty seconds and the CEO could not work. macOS GZDoom has no
> headless mode, so the fix is policy, not a flag.

> Why: this stage used to be four separate commands, and the slowest of them
> (`tools/smoke.py`) boots a real GZDoom and puts a window on the screen.
> People ran all four for everything, including edits the engine cannot
> possibly see. The CEO, 2026-10-13: *"no paran de abrírseme pantallas [...]
> igual para pequeños cambios habría que poder hacer que QA tenga criterio de
> cuándo lanzar tests y cuándo no; o bien hacer una pasada fast y otra full."*
> ("screens keep popping up on me [...] maybe for small changes QA should be able
> to judge when to run tests and when not; or else do one fast pass and one full
> pass")

#### The ladder

Each level contains the one above it. Times measured on the project machine
(2015 i5-5257U, Intel Iris 6100) on 2026-10-13 with `.venv/bin/python` — the
system `python3` skips every art test for want of Pillow, which makes it
faster and much less useful. Two numbers because they were measured twice:
quiet, and again while three other agents were working on the same machine.

| Level | What runs | Window? | Quiet | Loaded |
|---|---|---|---|---|
| `docs` | D7 mirror check + repo paths quoted in the changed documents | no | 0.1 s | 0.3 s |
| `fast` | `build.py`, `check_pk3.py`, the suite **without** the slow art generator runs (`SD_SKIP_SLOW_ART=1`) | no | **6.8 s** | 8.1 s |
| `art` | `fast` plus the slow art runs: determinism, palette, tiling, ink count | no | ~15 s | 18.9 s |
| `full` | `art` plus `smoke.py` on every map in `src/maps/` (2 maps x ~8 s) | **yes** | ~31 s | 46.4 s |

Narrowing `art` to only the three art test modules was measured and
rejected: it saves about 2 s of 14 and loses every other regression the
suite catches, so `art` simply runs the whole suite with the slow runs on.

`fast` is the working loop. `full` is for before a push, at a phase close and
at every gate — a gate is never signed on `fast`.

Deliberately **not** in `full`: `SD_ENGINE_TESTS=1`, which makes
`tests/test_smoke.py` boot GZDoom a second time to do what the smoke stage
has already done. `--engine-tests` turns it on for the rare case where the
suite's own engine wrapper is what changed.

#### The criterion `auto` applies

`auto` asks git what changed (`git status --porcelain`, or `git diff` against
a ref with `--since`), classifies every path, and takes the **highest** level
any of them demands. It prints the rule, an example path and the reason
**before** running anything, so the decision is auditable and can be argued
with.

| Changed path | Level | Why |
|---|---|---|
| `docs/`, `work/`, `.claude/`, root `*.md` (`README.md`, `CLAUDE.md`, `LICENSE.md`) | `docs` | nothing here is built, packed or parsed by the engine |
| `assets/`, `tools/art/`, `tools/audio/` | `art` | art can only break the package, and `check_pk3.py` already proves palette, size, naming and references; the engine sees nothing a validator has not |
| `tests/`, `tools/` (incl. `tools/check_pk3.py`, `tools/smoke.py`), `.github/`, `.coveragerc`, `.gitignore`, `.gitattributes`, the full licence texts `LICENSE-GPL-3.0.txt`, `LICENSE-CC-BY-NC-SA-4.0.txt` and `LICENSE-FREEDOOM-BSD-3.txt` (shipped by `tools/release.py`, hashes pinned in `tests/test_release.py`) | `fast` | tooling and tests are the thing under test and are never packed into the PK3 |
| `src/` — `src/zscript/`, `src/lumps/`, `src/maps/` | `full` | only GZDoom parses ZScript, UDMF and the definition lumps; a bad property or a missing actor appears in no static check |
| `tools/build.py`, `tools/sdbuild/` | `full` | the packer decides what reaches the engine, and a wrong lump name or layout is only fatal at load time |
| anything else | `full` | the safe answer to "no rule covers this" is the expensive level |

Two refinements that are tested, not assumed
(`tests/test_verify.py`):

- **Noise never raises the level.** `.DS_Store`, `__pycache__/`, `*.pyc` are
  dropped before classification: an editor dropping must not cost somebody a
  GZDoom window.
- **Only the maps that changed are booted.** If every engine-forcing path is
  under `src/maps/MAP02/`, `full` smokes MAP02 alone. A ZScript, lump or
  packer change is global and smokes all of them.

#### Exit codes

One per stage, so a wrapper can tell them apart: `10` docs, `11` build,
`12` check_pk3, `13` the suite, `14` the engine (the smoke exit code is
printed next to it); `2` usage, `3` git unavailable in `auto`.

#### The documentation check

The `docs` stage reports the one part of D7 a script can decide: every
`docs/**.md` has its twin under `docs/ru/` at the same path. Since D34 the
mirror is batch work done at a phase close, so a missing or stale mirror is
a **warning**, never a failure, during a phase; at a gate (`verify.py docs
--gate`) a missing mirror fails the stage. It also warns when a document quotes a
repo path in backticks that does not exist. Root documents (`README.md`,
`CLAUDE.md`, `LICENSE.md`) carry their Russian text inline or not at all and
owe no mirror. Everything else about the paper trail — one owner per fact,
D-numbers, evidence paths — is stage 7 and belongs to `pmo`, not to a script.

#### The window

`tools/smoke.py` opens a **480x320** GZDoom window (`+win_w` / `+win_h`,
verified on g4.14.2: the log goes from `Resolution: 2048 x 1280` to
`Resolution: 960 x 584`) and forces `i_pauseinbackground 0` so an unattended
run still finishes when you click back into your editor. `--window native`
restores the engine's own geometry. **NOT VERIFIED / not available:** nothing
in this build stops GZDoom taking keyboard focus when its window appears; the
macOS backend activates the app itself and exposes no switch for it.
`-width` / `-height` were tried and had **no** effect.

**Windows (the CEO's PC, the working machine since 2026-10-13):** the same
arguments give a `464 x 281` window (log line `Resolution: 464 x 281`,
GZDoom g4.14.2, verified 2026-10-13), the engine's `screenshot` command works
unchanged, and a run that overruns its timeout is killed with `taskkill /T`
on its own process group, since Windows has no `killpg`. The gate
(`SD_ALLOW_ENGINE=1`) applies on both machines: a window is a window.

- **Every behaviour validated by a real case gets a test**, so the next change
  cannot silently undo it. The mirrored emblem, the missing art in the PK3 and
  the off-palette slogan are all now tests.
- **Anything not confirmed in the engine or the ZDoom wiki is marked NOT
  VERIFIED**, in the document, in that wording.

> Why: `MOD-SPEC` proposed DoomEdNums 14000-14999 as "NOT VERIFIED free". They
> were not: GZDoom uses 14001-14165 for ambient sound and music changers.
> The label is what made someone check.

### 6. Product update — what is done and what is not (D64, "súper importante" (CEO: "super important"))

When a delivery closes (a batch of tasks, a milestone step, a session's
work), and **before** the `pmo` stage, Product (the PM) updates the
product documents with the honest state of things:

- `docs/BACKLOG.md`: each task of the delivery moves to **done** with its
  commit, or stays open with what is missing and why; anything discovered on
  the way is added as a new line (or parked, per D60).
- `docs/ROADMAP.md`: the milestone table's status column (M1-M4) says what
  the delivery moved and what still stands between it and the gate.
- `docs/PENDING-CEO-DECISIONS.md`: what now waits on the CEO; what closed.
- `CLAUDE.md` status and `docs/HANDOFF.md` if the session ends.

"Done" means verified (tests, and the engine where the change is visible),
committed, and approved by the CEO where the CEO's gate applies. Drafts
waiting for the CEO are not done. The `pmo` stage then checks this update
against the commits; a delivery without it does not pass stage 7.

### 7. Document — the `pmo` stage

Before the PM commits, the `pmo` agent checks the paper trail. It blocks the
commit if any of this is false:

- Every claim in `CLAUDE.md`'s status block is true **today**.
- Every fact lives with its **one owner** (the table in `CLAUDE.md`), and the
  other documents link rather than restate it.
- **At a phase close only** (D34): every English document has its Russian
  mirror at the same path under `docs/ru/`, synced and dated. Between gates
  a stale mirror is not a finding. In-game text (`LANGUAGE`) is checked on
  every batch: no `SD_*` string without its `[ru]` line (D21).
- Every new asset has origin and licence in `docs/art/LICENSES.md`.
- Every decision the CEO took in chat is a **D-number** in `docs/PRD.md` §5,
  with its date and the CEO's words where they matter.
- `docs/PENDING-CEO-DECISIONS.md` contains everything open and nothing closed.
- Gate verdicts in `docs/qa/GATE-REVIEWS.md` carry evidence with paths.
- Contract changes (sizes, lump names, DoomEdNums) reached `MOD-SPEC.md`
  **before** the code that depends on them.

> Why: `SDPOSTR2` entered `assets/` while three documents still said it was
> conditional, and `MOD-SPEC` said there were no DoomEdNums while `MAPINFO`
> already reserved seven.

### 8. Publish

The PM commits and pushes (D6).

- **Commit specific paths, never `git add -A`, while agents are running.**
  > Why: a commit swept up two agents' half-written files on 2026-10-12.
- **An excluded path is a debt, and the PM owes it.** Every commit that leaves
  something out names what it left out, and the PM comes back for it before
  the session ends. Run `git status --short` and read it; untracked is not
  "later", it is "missing".
  > Why: the other half of the rule above was missing, and the entire arsenal
  > — seven weapon classes, the player class, MAP02, SNDINFO — lived only on
  > one laptop's disk for an hour. `tests/test_arsenal.py` *was* committed, so
  > `main` was red against code that was not there. Found by the CI agent on
  > a clean clone, which is exactly what a clean clone is for.
- **An agent's coupled files are committed as a set, or not at all.** Picking
  some of them is worse than picking none: the tree still builds on the disk
  that has the rest.
  > Why: minutes after the rule above was written, the PM committed
  > `src/maps/MAP01/map.py` without `tools/sdbuild/udmf.py`, which it imports.
  > Both belonged to the same agent, mid-flight. It built locally and died on
  > a clean checkout with `ImportError`. CI caught it in thirteen seconds.
- **Green locally is not green.** The only honest check is a clean checkout,
  which is what CI is for. Wait for it before calling a push done.
- **One commit per agent delivery, as soon as it delivers** (CEO, 2026-10-13).
  Verify first, then commit that agent's files as a complete set. Pushing can
  be batched; committing cannot.
  > Why: six agents in flight took the session to its usage limit with an
  > uncommitted tree. Agents write to disk as they work, so the files survive,
  > but an uncommitted tree has no restore point per piece of work, and the
  > reports that carry the findings die with the agent.
- One commit per coherent piece of work. The message says what changed, what
  was verified, and what is still open.
- Push to `main` on `kahache/soviet_doom` once `tools/verify.py full` and the
  `pmo` check pass. The repo is private; publishing anything outside it is a CEO
  decision.
- Evidence (logs, screenshots) is committed only when it proves a gate.
  Routine runs write to `logs/`, which is gitignored.

## When the pipeline stops

| Situation | What happens |
|---|---|
| A verification fails | Work stops at stage 5. The failure is fixed or filed as a numbered bug with a repro. Never commit around it. |
| `pmo` finds a documentation gap | Stage 7 blocks. The gap is closed in the same batch, not "later". |
| An agent needs something that does not exist | It stops and says so in its summary rather than inventing it. The PM commissions the missing piece. |
| Two agents need the same file | The PM serialises them. Ownership is never shared. |
| A gate is debatable | It goes to the CEO with data, not with an opinion. |
| The CEO is away | Everything reversible continues. Only taste, authority and irreversible actions wait. |

## Phases and gates

The roadmap advances in phases, each with a measurable gate defined **before**
the phase starts (`docs/ROADMAP.md`). A gate is signed by `qa-engineer` with
evidence, never by the agent that did the work.
