# Session handoff (living; the PM rewrites it when a session ends)

Updated: 2026-10-22 (Product, stage 6, after Episode 3's routes PASS at 9133be1
and D114). Before that: 2026-10-21 ~23:30 (night shift closed, D102/D103) and
2026-10-20 ~16:40 (v1.0 sign-off). Decisions up to **D114** are in
`docs/PRD.md`; open CEO items in `docs/PENDING-CEO-DECISIONS.md`; tasks and
estimates in `docs/BACKLOG.md`; the phase view in `docs/ROADMAP.md` ("P4 today").

## RESUME HERE FIRST (2026-10-23 ~12:45, PC shut down at the CEO's request)

**main (V2), all pushed, 33/33 routes PASS on f1c350b** (fb4f3bd evidence) + D125 sounds smoke-clean on HEAD:
D123 installed (Gemini gunner SDLG, TT-33, Liberty statue SDLC = MAP06 boss, `SD_ChromeGeneral` 21113 = MAP08
mini-boss); D125 world/player sounds (51 takes; jump stays Freedoom's). D124 radio approved (V3). D126: epic title
screen with Gemini before v1.2 (prompt in the pack §11). The CEO has nothing left to review.
**v3 branch** (origin/v3, worktree `scratchpad/wt_v3`, 5a3e1d7): six V3 jobs merged (pickup events E1/E2/E3,
ops map + medals D122, RGD-5 ADR 012, radio proposal) + the status-screen fix. Engine: 27/33; **2 routes fail on
skills 2-4, both Episode 1**: g3-auto (MAP01: tags 12/13 of the weapon-pickup cupboards stay shut at A6/A9 — probably
the route already holds the IZh/PPSh, so the pickup never fires; check the helper's `give` and rule R8) and
metro-critical (MAP02: step PASS ends in z3_hall instead of Z8 after the window event). Hand to a level-designer with
the reports in `wt_v3/docs/qa/evidence/2026-10-23_12*`. Then: integrate the radio (SD_Loudspeaker 21201) and place
the RGD-5 in the maps on v3; MAP09 crater hook (ZScript) and MAP03 train stay candidates.
**Next when the PC is on:** Gemini queue below (≈20 images), install the Consortium/AKM/walk re-asks, the title
screen last, then the v1.2 sign-off and the CEO's final yes to publish.

## Gemini progress 2026-10-23 (cap hit at 10:38; next window 23 Oct 17:33)

20 images today. Done: TT-33 A/B (but Gemini drew a generic modern pistol: re-ask with the TT-33 block in
the art-director's note, `gemini_tt33_A2/B2`), gunner 5/5 (aim_v3 and death_v2 are the keepers; frontal fire OK, D119),
colossus 7/7 (aim and fire: profile touches view 4, crop by hand), Consortium 2/7 (rooted, turn). **Next at 17:33:**
gunner walkL/walkR re-ask (all five views mid-stride, left leg forward in L, right in R: the two sheets came
out almost identical), then Consortium fire, death, aim (2 rows), walk (2 rows), breach; then the AKM 2; TT-33 re-ask 2;
re-asks 4 (optional: gunner fire 3/4-back views with the flash at the hip). **LAST, before publishing v1.2: the epic title screen (TITLEPIC, D126, prompt in §11 of the pack).**
Processing agents (art-director) run per character; previews go to the CEO before anything enters `assets/`.
V3 agents run in isolated worktrees (pickup events E1/E2/E3, ops map + medals, RGD-5, propaganda radio).

## RESUME HERE FIRST (2026-10-23 ~02:45, PC shut down at the CEO's request)

The CEO played Episodes 2 and 3 and liked it (D119). **V2 = the finished game; V3 = improvements** (D120 scope,
D121 Icebox cleanup). Done tonight, all committed and pushed (HEAD after 0c20524):
- D119 fixes: Soviet flags SDFLAG1-4 (62dbe9e); ROKS-3 nerf, dropped IZh 2 shells, Consortium 4000 / colossus 3000 HP,
  ammo of MAP01-09 per BALANCE §8 + the PM's amendment (rockets ≤ 30 % outside bosses, fuel ≤ 15 %), 42 Catalan
  engine strings, Episode 1 skies (D121) (df2ecdd). verify fast PASS; **33/33 routes PASS** on df2ecdd (0c20524 evidence).
- Play build **v1.2-rc3** (not published): `C:\Users\littl\Desktop\SovietDoom-prueba\rc3\SovietDoom` (rc2 left as it was).
- PM proposals doc `docs/product/2026-10-23_P4_next-version-proposals.md`; V3 list in `docs/ICEBOX.md`.

**Next, when the CEO switches the PC on:**
1. **Gemini** (window from 23 Oct 08:19) with `docs/product/2026-10-23_P4_gemini-prompt-pack.md` (gunner fire frame
   **frontal**, D119): TT-33, gunner, colossus, Consortium, AKM, re-asks; then swap the `PROVISIONAL-D116` sprites
   (the "black-and-white General" the CEO saw is the colossus's stand-in).
2. Then **v1.2 public release = V2 close**: G6-style sign-off on a clean clone, release.py + portable packages; ask
   the CEO for the final yes before publishing (D121). v1.1 and v1.2-rc1 drafts get superseded.
3. Follow-ups in BACKLOG (D119): AKM magazine box (needs a sprite), flag constant names in MAP03-05.
4. CEO still owes: the rest of the world-sounds sheet (39/56), whether to play rc3 (C1 is pending, not scheduled).

## Earlier resume note (2026-10-22 ~21:00, PC suspended at the CEO's request)

Since 15:00: Gemini hit its daily cap (next window 23 Oct 08:19; D116: art only from Gemini, no Fooocus).
Done: gunner, colossus (MAP06 boss, MAP08 mini-boss s3-4), the Consortium (MAP09 final boss) and the AKM integrated
with provisional tinted sprites (swap lines marked PROVISIONAL-D116) and placed; Marx-Engels pair hung (D117);
E3 ends TO BE CONTINUED; General's death voice (D118, 12/12 voices ours). 33/33 routes PASS on 87585b2.
The CEO plays tonight from Desktop/SovietDoom-prueba/SovietDoom (v1.2-rc2 Windows package, not published);
after playing he decides whether to build three more maps (an Episode 4) or stop at nine (D117). Nothing to publish yet.
Next tomorrow: Gemini with docs/product/2026-10-23_P4_gemini-prompt-pack.md (27 images by priority), then swap the
provisional sprites. Pending CEO: rest of the world sounds sheet (17/56 judged: player sounds OK except jump; OOF w1 to be
layered with w3's impact), MAP07 questions, v1.2 publish.

## Earlier resume note (2026-10-22 ~15:00)


Nothing in flight: no agents, no Fooocus/Chatterbox, all work committed and pushed (HEAD e27f99a + this note).
State: 9 maps in 3 episodes + RANGE, all routes PASS on skills 2-4 (33/33, evidence 2026-10-22_13*/14*);
Gemini enemies, E2/E3 music, E2/E3 textures, skies SDSKY1-7, posters, safe starts installed.
Draft releases (not public): v1.1 and **v1.2-rc1** (everything of today).

**Next, in order:**
1. **Gemini** (daily image limit reset 22 Oct 17:33; drive the CEO's Chrome per the `reference-gemini-chrome-workflow` memory;
   upload: open the "+" menu, `find` the hidden file inputs, `file_upload` to the middle ref):
   a. **TT-33** (D111): ready + fire, bare hands; weapon prompt in `docs/product/2026-10-20_0030_M2_gemini-weapons.md`; then `tools/art/gemini_frames.py`.
   b. **SD_LegionGunner** (SDLG): only `gem_gunner_turn.png` exists; walkL/walkR/aim/fire/death; frame list in `docs/engine/2026-10-22_P4_ep2-enemies.md`.
   c. **SD_LibertyColossus** (SDLC) from scratch (same doc).
   d. **The Consortium** (SDCN, `docs/engine/2026-10-22_P4_ep3-final-boss.md`) and the **AKM** (`docs/engine/2026-10-22_P4_akm.md`, prompt block ready).
   e. Re-asks in `docs/art/previews/2026-10-22_P4_enemies-gemini.html` (hound lunge, General order frame…).
   Gemini refuses swastikas: blank armbands; the pipeline paints them (D108).
2. Integrate gunner + colossus (MAP06), the Consortium (MAP09), the AKM (MAP05-09) into the mod; re-run routes.
3. **Waiting for the CEO** (`docs/PENDING-CEO-DECISIONS.md`): publish v1.1 / v1.2-rc1; Marx-Engels cells; General death round 2
   (`work/audio/preview/voices_p2b_listening.html`); world sounds (`work/audio/preview/world_sounds_listening.html`); MAP07 questions; E3 ending wording.

## Where we are (2026-10-22)

- **v1.0 is public** (tag `v1.0` at d530faa, G6 PASS 4a17a61; Windows, macOS,
  Linux packages and sources attached). **v1.1 is a draft** (target c9414c2:
  cursor, death prompt, Catalan); the CEO has not said publish or wait for a
  v1.2 (PENDING §1). Nothing of P4 is in a release.
- **P4 is under way (D104-D114): 9 maps in 3 episodes + RANGE.** Episode 2
  (MAP04-06) and Episode 3 (MAP07-09) are built; **18 of 18 routes PASS on
  skills 2-4** (`docs/qa/evidence/2026-10-22_*_report.txt`). Music of both
  episodes is installed (D106, D113); Episode 2's 25 textures are installed
  (D107) and Episode 3's three sets are on disk (D113); the seven enemies are
  redrawn with Gemini and carry the approved armbands (D105-D109, D114);
  posters are in every map (two slots per map wait for the Marx-Engels pair).
- **Uncommitted in the work tree** (at the time of writing; other agents still
  editing): Episode 2 texture round 2 and Episode 3's textures (assets, maps,
  tests, `docs/levels/`, `docs/art/LICENSES.md`, `TEXTURE-INDEX.md`,
  `docs/engine/MOD-SPEC.md`, `tools/check_pk3.py`, `tools/release.py`), ~540
  modified enemy sprite lumps, `work/audio/candidates/dog/`. Commit with
  explicit paths; run `tools/verify.py fast` and `pmo` (stage 7) first.

## Resume here

1. Let the agents finish the work-tree batch above; then `tools/verify.py fast`,
   one engine pass on MAP04-MAP09 (the Episode 2 route evidence is from
   00:18-00:28, before round 2 textures), stage 7 `pmo`, then commit.
2. Gemini's daily image limit resets 2026-10-22 17:33: then the TT-33 (D111),
   the Legion gunner's frames (walkL/walkR/aim/fire/death) and the Colossus
   from scratch, and the enemy re-asks listed in the review sheet. Method and
   prompts: `tools/art/gemini_enemy.py`, `docs/product/2026-10-20_0030_M2_gemini-weapons.md`.
   Sheets are local only (D77): `work/art/reference/enemies/gemini/`.
3. The CEO owes: v1.1 or v1.2; the Marx-Engels pair (cells, mirror, slogan
   split, alignment); the General's death voice (new round in
   `work/audio/preview/voices_p2b_listening.html`); MAP07's questions and the
   end of Episode 3 (PENDING §2-§4). Nothing else blocks.
4. Still no D-number: the AKM and the world sounds (BACKLOG Next #9, #10); the
   final boss of MAP09 is not designed (Next #5). Ask the CEO before building.
5. Standing rules from D104 and D113: the PM may push P4 on its own; composed
   music and procedural textures install without the CEO's review; sprites,
   voices, anything with a real person's likeness or a political symbol go to
   him first. **The swastika is shown to the CEO before it is applied (D105)**;
   the applied armbands were approved in D114.

## Earlier state, kept for the thread

P4 push (2026-10-22 morning, D104/D105): Episode 2 maps, scaffolding, music and
texture drafts, the Episode 2 enemies as a draft overlay
(`tools/make_ep2_enemy_overlay.py`) and the Gemini enemy pipeline
(`tools/art/gemini_enemy.py all` -> `work/overlays/sd-draft-enemies.pk3`). Gemini
prompts: upload `work/art/reference/enemies/clean_<enemy>.png` (swastikas blanked)
through the hidden image input, then turn / walkL / walkR / aim / fire / death
(cartoonish, no blood words).

## NIGHT SHIFT 2026-10-21 (D102) — DONE 23:30; the morning report is `docs/product/2026-10-21_2330_P0_night-report.md`

The CEO is asleep and wants everything advanced; ask him nothing until morning.
Work items, in this order (tick them here as they land):
1. [x] **Cursor:** GZDoom's menu mouse pointer (Freedoom's `doomcurs`/CursorPic) -> our hammer and sickle (GameInfo `CursorPic`), EN/RU-neutral. Small.
2. [x] **P5:** PM downloads GZDoom g4.14.2 macOS + Linux builds and the source archives (GZDoom g4.14.2, OpenAL Soft 1.23.1, libsndfile 1.2.2, ZMusic) into isolated scratch dirs; attach the sources to release v1.0; agents build `sovietdoom-1.0-macos.zip` and `-linux.tar.gz` (tools/release_portable.py), test Linux under WSL if available; upload to v1.0.
3. [x] **v1.1:** real dog sounds for the Reich hound (licence-clean CC0/CC-BY, sound-designer; listening page for the morning, do not install unheard), and a clear EN/RU "press USE to continue" prompt on death that restarts the level.
4. [x] **P2 drafts:** the 4 voices still Freedoom's (rifleman pain, trooper death, General pain/death) with the aggressive references; listening page; do not install unheard.
5. [x] **P6 Catalan:** a third language (every LANGUAGE id in `[ca]`, the language option, a CA status-bar label band, README/CREDITS CA section); the CEO reviews in the morning.
6. [x] ~~**P1 analysis**~~ dropped 2026-10-21 night: the CEO played the campaign and finds it fine; P1 stays parked in V2 until a player complains about difficulty.
Closed 23:30: v1.1 DRAFT release created (not public, 8 assets, target c9414c2 after the Catalan pause sign); macOS/Linux packages on v1.0; dog and P2 voice listening pages waiting for the CEO (nothing installed); Chatterbox server stopped (poisoned by a CUDA assert, see the P2 page). Earlier: GPL/LGPL sources attached to release v1.0 (4 tarballs). Agents running: P5 macOS/Linux packaging, cursor + death prompt, dog sounds, P2 voices, P6 Catalan (owner of LANGUAGE; adds SD_DEATH_PROMPT in EN/RU/CA). (Superseded by D104: WSL was authorised and the Linux package ran on Ubuntu 24.04, add90e3.)
7. [x] At the end: verify fast, engine pass, v1.1 **draft** release (not public), stage 6 docs, a Spanish morning report for the CEO.
Rules: commit with explicit paths; agents never commit; one owner per shared file (LANGUAGE, MAPINFO, SNDINFO, LICENSES.md, MOD-SPEC) — serialize installs; engine runs from a clean worktree.

## Untracked on disk

`work/audio/candidates/dog/` (the dog candidates, already installed under D107)
and, if it still shows, `work/audio/candidates/borodin_steppes/` (Borodin was
rejected for MAP01, D92): gitignore or delete; neither is part of a release.

## Rules learned

Agents never commit or stage (D6); commit with `git commit -- <paths>`;
file ownership in every brief; only the PM runs GZDoom (D26) with
`-config logs/gzdoom-tooling.ini`; the PM gates every draft before the
CEO; short lists when asking the CEO (he lost track once); PowerShell and
full paths for the CEO; send images with SendUserFile; log each task's real
token cost in the BACKLOG's Done line when it closes (the v1.0 delivery and the whole of P4 so far
were not logged, so their estimates cannot be checked).
