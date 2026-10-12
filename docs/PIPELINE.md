# The pipeline — how work moves from idea to GitHub

Owner: PM. Enforced by the `pmo` agent. Russian mirror: `docs/ru/PIPELINE.md`.
Created 2026-10-13 at the CEO's request. **Every rule below was paid for by a
real mistake in this project**; the mistake is cited so nobody relitigates it.

`docs/WORKING-AGREEMENTS.md` says *what the rules are*. This document says
*in what order things happen, and who stops whom*.

## The seven stages

```
1 COMMISSION   PM writes the brief, declares file ownership
2 DRAFT        cheap, reviewable, thrown away if wrong
3 PM REVIEW    the PM judges before the CEO ever sees it
4 CEO GATE     only what needs taste or authority reaches the CEO
5 VERIFY       build, check_pk3, smoke, suite - all four green
6 DOCUMENT     the pmo agent checks the paper trail before anything is committed
7 PUBLISH      the PM commits specific paths and pushes
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
  made the source right (Lenin v3: "no se parece a él EN NADA").
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
> millas." Three items had been parked as CEO decisions when none of them
> needed one.

When asking, the PM sends: the artefact or the command to run it, a
recommendation, and the cost of each option. Never a bare question.

Everything open lives in `docs/PENDING-CEO-DECISIONS.md`, ordered by how much
each item unblocks, and the session hook shows it at every start.

### 5. Verify — the four greens

Nothing is committed until all four pass, and the PM runs them itself:

```
python3 tools/build.py                 # the package builds
python3 tools/check_pk3.py             # structure, textures, palette, licences
python3 tools/smoke.py --map MAPxx     # GZDoom loads it, zero errors in the log
python3 -m unittest discover -s tests  # the suite
```

- **Every behaviour validated by a real case gets a test**, so the next change
  cannot silently undo it. The mirrored emblem, the missing art in the PK3 and
  the off-palette slogan are all now tests.
- **Anything not confirmed in the engine or the ZDoom wiki is marked NOT
  VERIFIED**, in the document, in that wording.

> Why: `MOD-SPEC` proposed DoomEdNums 14000-14999 as "NOT VERIFIED free". They
> were not: GZDoom uses 14001-14165 for ambient sound and music changers.
> The label is what made someone check.

### 6. Document — the `pmo` stage

Before the PM commits, the `pmo` agent checks the paper trail. It blocks the
commit if any of this is false:

- Every claim in `CLAUDE.md`'s status block is true **today**.
- Every fact lives with its **one owner** (the table in `CLAUDE.md`), and the
  other documents link rather than restate it.
- Every English document changed in this batch has its **Russian mirror** at
  the same path under `docs/ru/`, updated in the same batch (D7).
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

### 7. Publish

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
- One commit per coherent piece of work. The message says what changed, what
  was verified, and what is still open.
- Push to `main` on `kahache/soviet_doom` once the four greens and the `pmo`
  check pass. The repo is private; publishing anything outside it is a CEO
  decision.
- Evidence (logs, screenshots) is committed only when it proves a gate.
  Routine runs write to `logs/`, which is gitignored.

## When the pipeline stops

| Situation | What happens |
|---|---|
| A verification fails | Work stops at stage 5. The failure is fixed or filed as a numbered bug with a repro. Never commit around it. |
| `pmo` finds a documentation gap | Stage 6 blocks. The gap is closed in the same batch, not "later". |
| An agent needs something that does not exist | It stops and says so in its summary rather than inventing it. The PM commissions the missing piece. |
| Two agents need the same file | The PM serialises them. Ownership is never shared. |
| A gate is debatable | It goes to the CEO with data, not with an opinion. |
| The CEO is away | Everything reversible continues. Only taste, authority and irreversible actions wait. |

## Phases and gates

The roadmap advances in phases, each with a measurable gate defined **before**
the phase starts (`docs/ROADMAP.md`). A gate is signed by `qa-engineer` with
evidence, never by the agent that did the work.
