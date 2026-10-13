# Roadmap

Living document. Owner: PM. Russian mirror: `docs/ru/ROADMAP.md`.

| Phase | Goal | Gate (measurable) | Status |
|---|---|---|---|
| F0 | Pipeline works | **G0:** GZDoom loads the PK3 on Freedoom with zero errors, player stands in MAP01 | **PASSED 2026-10-09** (`docs/qa/GATE-REVIEWS.md`) |
| F1 | Lore + PRD | **G1:** CEO ratifies lore and D1–D13 | **PASSED 2026-10-09** (D1–D14 ratified by the CEO; D15 decided by the PM on delegation; entry in `docs/qa/GATE-REVIEWS.md`, written retrospectively 2026-10-13) |
| F2 | Art direction + texture batch 1 ("Soviet base" set) | **G2:** ≥ 8 textures approved by the CEO, all with origin and licence; palette fixed | **PASSED 2026-10-12** (`docs/qa/GATE-REVIEWS.md`; 8 clean approvals, origin/licence and palette verified; B2 resolved the same day). Batch 2 continues inside F3: switches shipped (D25) and the metro's first pieces are approved (D42); more metro sketches wait on the CEO. Current state: `CLAUDE.md` |
| F3 | MAP01 Zarya-7 v0→v3 | **G3:** map finishable on skills 2, 3 and 4 with zero log errors and zero softlocks; CEO verdict "on point" | **IN PROGRESS:** MAP01 v3 built and played through by the CEO (D38); G3 under way: scripted routes PASS on skills 2-4, the hand-played runs, the hostile pass and the CEO's G3-9 remain (`CLAUDE.md`, `docs/qa/GATE-REVIEWS.md`) |
| F4 | Period arsenal (7 slots) | **G4:** every weapon has sprites, sounds, balance doc and a test range | **STARTED:** balance closed (D39), ice axe in slot 1 (D40), MAP02 ships as a practice range (D41); hand and glove, ice axe, PPSh-41 and weapon-sound drafts wait on the CEO (`CLAUDE.md`) |
| F5 | Bestiary (both factions) | **G5:** every enemy has states, sounds, balance; MAP01 playtest passes | **STARTED:** bestiary playable with placeholder sprites and sounds; the Reich rifleman in 3D and the enemy effects are drafts waiting on the CEO (`CLAUDE.md`, `docs/qa/GATE-REVIEWS.md`) |
| F6 | Release v1 | **G6:** licence file, credits, README EN/RU, QA sign-off, tag v1.0 | |

Rules: gates are defined before the phase starts; first measurement is honest
and strict; a gate may be reframed only by a new D-decision of the CEO.
