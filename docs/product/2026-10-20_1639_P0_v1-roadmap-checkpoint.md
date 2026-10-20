# v1.0 roadmap checkpoint, 2026-10-20 16:39 (Product + pmo, stages 6 and 7)

Dated snapshot, immutable. Asked by the CEO with D97 ("asegúrate de que está
cumplido el pipeline y hazme un checkpoint del roadmap"). Measured against the
repo at **4a17a61** (`main` = `origin/main`, CI green), the tag `v1.0`
(d530faa) and the GitHub release, not against the documents' own claims.
Owners of the living facts: `docs/ROADMAP.md` (phases), `docs/BACKLOG.md`
(tasks, estimates), `docs/PENDING-CEO-DECISIONS.md` (what waits on the CEO).
Previous snapshot: `docs/product/2026-10-20_1045_P0_mvp-status.md`.

## 1. Verdict

**The MVP is done: M1, M2, M3 and M4 PASSED.** G6 PASS for a friends
release (`docs/qa/GATE-REVIEWS.md`, evidence
`docs/qa/evidence/2026-10-20_1635_M4_v1-signoff.md`): a clean-clone suite of
2 128 tests, the deterministic zip `sovietdoom-1.0.zip` (SHA-256
`1b4731aaf51deda8…`, 8 members, checksums verified) and 11 of 11 scripted
routes PASS on the zip's own PK3 on skills 2, 3 and 4 with clean logs. The
tag and the GitHub release exist; **the repo is still private** (D98's step
waits on the CEO's last yes).

## 2. What v1.0 contains

| Area | In v1.0 | Where it is recorded |
|---|---|---|
| Campaign | 3 linked maps: MAP01 Zarya-7 (v3) → MAP02 metro-bunker (v1) → MAP03 Tankograd (v1.1), transition texts, the ending; the practice range `RANGE` | ROADMAP, `docs/levels/`, D62, D68, D70 |
| Arsenal | 7 period weapons in ZScript, all with our first-person art: TT-33 (Freedoom-based hands), PPSh-41, IZh-58, RPG-7, ROKS-3, hand Katyusha, ice axe (Gemini frames, D79-D88); 7 of 7 world pickups | MOD-SPEC, LICENSES |
| Bestiary | 7 enemy classes plus the heavy Panzermensch (Schwer), our sprites; 4 of 4 enemy projectiles | `docs/engine/BESTIARY.md`, D49-D81 |
| Pickups | health, bonuses, armours, map, backpack, the yellow and red passes (with the blue), the first-aid sign white on green | D80, e84c56c |
| Effects | PG-7V, Katyusha rocket, burst, flame, puff, blood, teleport fog, fuel drum, lamp | D82, c324f27 |
| HUD and shell | status bar A in EN and RU, the sergeant's 42 Gemini faces incl. god mode, digits N2, key and armour icons; menus, title, the Russian pause sign, help and credit pages, quit lines | D89-D92, a5129c1, c324f27 |
| Sounds | 25 weapon sounds + the D94 alternatives (34 weapon lumps); 81 enemy lumps: 43 of the 47 enemy sounds ours, `$random` among approved takes | D74, D83, D86, D94 |
| Voices | 24 Chatterbox takes: 8 of the 12 enemy voices (rifleman idle/sight/death, trooper idle/sight/pain, the General's sight and "Vorwärts") | D91, D96, d18a40a |
| Music | title `D_SDINTL` (the Internationale), MAP01 `D_SDM1N2` (composed, the D92 exception), MAP02 `D_SDFUNR`, MAP03 `D_SDGATE`, range `D_SDM01T`, intermission `D_SDTITL`, the MAP01 radio | D83, D86, D95, `docs/sound/` |
| Languages | English and Russian, switchable in game; 163 string ids in both; the Russian reviewed once (N11) | D21, D97 |
| Release package | `sovietdoom.pk3`, README.txt (EN/RU), LICENSE.md, CREDITS.txt, the GPL-3.0, CC BY-NC-SA 4.0 and Freedoom BSD texts, SHA256SUMS | `tools/release.py`, G6 |
| Credits | in game and in CREDITS/README: Claude (Claude Code), Google Gemini, Fooocus/SDXL, Chatterbox, GZDoom, Freedoom, the CC0/CC-BY sound packs and voice references (kurt credited) | D93, G11 |

## 3. What is NOT in v1.0, and where it went

| Not in v1 | Goes to |
|---|---|
| G3's hostile pass and hand-played runs, balance by playtest, reloads, the TT-33's colour detail, jump/crouch (G17), the GAMEINFO IWAD hint (G15) | **P1** gameplay pass |
| The **4 enemy voices still Freedoom's** (rifleman pain, trooper death, the General's pain and death: no take approved), the **8 packed beds** not yet mixed under their voices, the IZh pickup sound (Freedoom's, D94), range extras | **P2** voices and polish |
| The `docs/ru/` mirror of the documentation | **P3** (D34, D75) |
| The full game: **15-20 maps**, **more weapons and enemies**, the **seven enemies v2 from Gemini**, mining Freedoom's maps, UDB (N15), metro/Tankograd v2 (N7b/N7c), MAP01's alternative piece N (D95) | **P4** |
| **Portable downloads per OS** (Windows, macOS, Linux; GZDoom and Freedoom bundled) | **P5** (D93) |
| **Catalan** as a third language | **P6** (D97) |
| **Orchestrated music** (the CEO's Pro Tools, a better soundfont, MusicGen-Melody) | V2, not yet phased (D99, ICEBOX) |

**Known small gaps in what ships** (none blocks the friends release):

- the engine's own **automap and cheat lines** (`AMSTR_*`, `STSTR_*`) are
  GZDoom's, not ours; player, door, switch and item sounds are Freedoom's
  (no gate names them, M2 audit);
- the **face's full damage ladder** was not checked by eye in the engine;
- the **credits screen at 16:9** was not opened in the sign-off run;
- **sound and music by ear**: every engine pass ran `-nosound`, so the CEO's
  own play is the check; the **two-IWAD dialog** with freedoom1.wad present
  was not run.

## 4. Tokens: estimated against real (from BACKLOG)

- **Up to the 10:45 snapshot:** 21 closed tasks logged **4 207k real against
  3 005k estimated, 1.4x**; installs ran **1.7x** (N17, N12c, N13, N9w).
  The worst misses were reports and sheets whose scope grew mid-task (A2 213k
  vs 20k, A1 255k vs 80k, A3 232k vs 60k, G2 156k vs 50k); the best was the
  General's full set (N12b 165k vs 500k).
- **The rest of the MVP, 10:45 → 16:35:** planned at **~3 050k** (range
  2 600-3 800k). It closed in about six hours, but **no real cost was logged
  per task**, so this delivery's estimate against real cannot be measured
  from the repo. It also held work no estimate had: two Chatterbox rounds
  (97 takes), the composed MAP01 piece and the animated sound page.
- **V2 as parked today** (BACKLOG, raw estimates, before the 1.4x): P1
  ~1 400k (three maps' hostile passes included), P2 ~390k, P3 ~400k, P4
  ~400k per map plus ~500k mining and the new weapons and enemies (a 15-20
  map game is in the order of 7-9M), P5 ~300k and P6 ~350k (both NOT
  measured, no study yet), D99's evaluation ~150k.

## 5. Pipeline check (stage 7) on this delivery

Run on 2026-10-20, 16:20-16:40: `tools/check_pk3.py` PASS (0 errors,
0 warnings; licences: 1 292 of 1 292 packed assets with a documented
origin); the 30 test modules that read `LICENSES.md`, the credits or the
release: **859 tests OK**; LANGUAGE has 163 ids in `[enu default]` and 163
in `[ru]`, none missing; D86-D99 are all in PRD §5; every evidence path in
the G6 entry exists. Findings outside Product's files, for their owners
before the repo goes public:

1. `docs/engine/MOD-SPEC.md` §6.2 still describes N9e's state (37 of 47
   ours, two voices; the rifleman's active and death, the trooper's sight
   and pain and the General's sight and summon as placeholders), while
   `SNDINFO` plays the D96 takes since d18a40a (43 of 47, eight voices;
   e.g. `SDRRIAC1`-`3`, `SDGENSU1`-`2`); its debt row T18 too. Owner:
   mod-engineer.
2. The repo `README.md` status line (line 7) still says F3 in progress and
   F4/F5 started (G16). Owner: PM, before the repo goes public.
3. `src/lumps/MAPINFO` comments on the MAP02 and MAP03 music still say "D62
   draft, pending the CEO's ear" (approved D83). Owner: mod-engineer;
   comments only.
4. `docs/ICEBOX.md` still lists "repaint the status bar's labels into
   Cyrillic", done by a5129c1. Owner: PM.
5. `work/audio/candidates/borodin_steppes/` is untracked and not ignored.
   Owner: PM.

## 6. Next steps

1. Close findings 1-3 (~30k), then the CEO's yes and the repo goes public
   (BACKLOG N18, D98).
2. The CEO plays v1.0 and notes what he dislikes (PENDING §2).
3. The CEO picks the first V2 phase. The PM's suggestion, following D60:
   **P1** (gameplay pass) before P4 grows the game, with P2's four voices
   whenever a shouted reference exists.
4. From now on every task's real cost goes into its Done line.
