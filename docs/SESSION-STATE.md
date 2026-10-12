# Session state — 2026-10-13, near the usage limit

Owner: PM. **This file is for resuming, not for history.** Delete or rewrite
it when the work below has landed. Russian mirror deliberately skipped: this
is scaffolding, not a project document.

Everything on disk is committed and pushed as of `07e793d`, with build,
`check_pk3` and the suite green. Nothing is lost. What is at risk is not the
code, it is the **reports**: four agents were working and none had delivered
its summary, which is where findings, bugs and open questions live.

## What was in flight

| Agent | Doing | On disk | What is missing if it died |
|---|---|---|---|
| `level-designer` | MAP01 v0 grey box | `src/maps/MAP01/map.py` (44 sectors, 179 linedefs), `tools/sdbuild/udmf.py` (665 lines, 41 tests), engine evidence under `docs/qa/evidence/` | Whether v0 is actually finishable end to end, and which spatial decisions it wanted the CEO to judge by walking it |
| `art-director` | Cyrillic font, debt T9 | `tools/art/gen_font.py` | The sample sheet with real game strings, the style variants, the scope estimate |
| `sound-designer` | Free Soviet-era MIDI search | `tools/audio/midi_inspect.py` | The candidate table with licences, what was downloaded, which ones sound good in the engine |
| `mod-engineer` | Difficulty ladder + Russian switch | `src/lumps/MENUDEF`, `src/zscript/sd/language.zs`, `tests/test_language.py` | What Russian looks like today without the font, whether Freedoom's skills fought back, how many strings were missing |
| `qa-engineer` | fast/full/auto verification | `tools/verify.py`, `tests/test_verify.py` | The measured timings and the auto decision table |

## How to resume

1. `python3 tools/verify.py full` if it works, otherwise the four commands in
   `docs/PIPELINE.md` §5. Confirm the tree is still green.
2. `python3 tools/verify.py --explain` and `tools/verify.py fast` — check the
   CEO's complaint is actually fixed, that routine work no longer opens GZDoom.
3. Walk MAP01 v0: `MAP=MAP01 tools/run.sh`. This is what the CEO was waiting
   for and could not get from reading the design document.
4. Re-commission anything whose report is missing. The briefs are recoverable
   from this conversation; the work on disk is the starting point, not zero.

## Open with the CEO

`docs/PENDING-CEO-DECISIONS.md` is the list. The live ones:

- Walk MAP01 v0 and judge the route and the scale.
- Difficulty 5: posthumous Hero, or "pyatiletka in one night".
- Cyrillic letterforms are level 2 (D22). Open: whether proper nouns and
  calibres stay Latin. `ZARYA-7` becomes `ZДЯYД-7`.
- Music: La Internacional is chosen for the title; the free-MIDI search was
  still running.
- Lenin poster ships as sweep cell 4C with «ЛЕНИН ЖИВ».
