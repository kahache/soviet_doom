# WEAPON-SOUNDS — the arsenal's own sounds

Owner: `sound-designer`. Status: **DRAFTS for the CEO's gate (F4, G4),
2026-10-13; eight of them re-layered on 2026-10-14 (D44, §2.2).** Nothing
here is in `src/` or `assets/`; nothing is approved.
Russian mirror: owed at the phase close (D34).

Generator: `tools/audio/gen_weapon_sfx.py` (tests:
`tests/test_gen_weapon_sfx.py`). Previews for the CEO:
`docs/art/previews/2026-10-13_2027_F4_weapon-sfx-drafts.html` (one page, every
draft embedded, the Freedoom stand-in heard today beside it; for its eight
re-layered cards it is now the "before") and
`docs/art/previews/2026-10-14_1030_F4_weapon-sfx-kenney-layers.html` (only
the eight that changed, before and after).

## 0. In six lines

1. **31 drafts**: fire, reload or break-open, pickup and empty click for the
   six guns; the RPG-7's explosion, the Katyusha's charge and per-rocket burst;
   and the **ice axe** (D40): swing, flesh hit, wall hit, pickup.
2. **11 are heard in game the moment they are approved**: they replace a
   Freedoom stand-in the code already plays. The other 20 need a small hook
   from `mod-engineer` first (§6); none of those hooks changes a tic (D39).
3. Every shot, boom, whoosh and hiss is **our own synthesis**. Mechanical
   foley (clicks, latches, clunks, springs, wood, tin and steel knocks) comes
   from two CC0 packs already downloaded under D36, always layered, never
   alone; Kenney's impact pack is used here as in the enemy sounds (D44).
   **No recording of a real firearm is used.**
4. Six cards come as a **sweep** of three takes (A as designed, B heavier,
   C drier) so the CEO points at one, as with textures (PIPELINE §2).
5. **Nobody has listened to these**: the agent that made them cannot hear.
   Every number below is measured; the taste is the CEO's.
6. Decisions for the CEO: §9.

## 1. Scope and names

Lump name = `SD` + weapon code + event code, 7 characters, free of every
lump in `freedoom2.wad` (the IWAD has no `SD*` lump, MOD-SPEC §6.3).
Event codes: `FIR` fire, `RLD` reload, `PKP` pickup, `DRY` empty click,
`EXP`/`CHG` as MOD-SPEC §6.2 already named them. Logical names follow
`src/lumps/SNDINFO`: `sd/weapon/<weapon>/<event>`.

| Weapon | Fire | Reload / break-open | Pickup | Empty click | Other |
|---|---|---|---|---|---|
| Ice axe (slot 1) | swing `SDAXSWG`; hit `SDAXHIT` | — | `SDAXPKP` | — | wall `SDAXWAL` |
| TT-33 (2) | `SDTTFIR` | `SDTTRLD` | `SDTTPKP` | `SDTTDRY` | |
| IZh-58 (3) | `SDIZFIR` | `SDIZRLD` | `SDIZPKP` | `SDIZDRY` | |
| PPSh-41 (4) | `SDPPFIR` | `SDPPRLD` | `SDPPPKP` | `SDPPDRY` | |
| RPG-7 (5) | `SDRPFIR` | `SDRPRLD` | `SDRPPKP` | `SDRPDRY` | explode `SDRPEXP` |
| ROKS-3 (6) | `SDRKFIR` | `SDRKRLD` | `SDRKPKP` | `SDRKDRY` | |
| Hand Katyusha (7) | `SDHKFIR` | `SDHKRLD` | `SDHKPKP` | `SDHKDRY` | charge `SDHKCHG`, burst `SDHKEXP` |

### 1.1 The ice axe (D40): what replaced the shovel

`mod-engineer` renamed slot 1 while this work was in flight; MOD-SPEC §6.2
now holds the final names, and these drafts use them. Two names are mine,
for events the shovel never had; they go into MOD-SPEC §6.2 when wired.

| Shovel (retired) | Ice axe | Logical name | Name from |
|---|---|---|---|
| `SDSHSWG` | `SDAXSWG` | `sd/weapon/iceaxe/swing` | MOD-SPEC §6.2 |
| `SDSHHIT` | `SDAXHIT` | `sd/weapon/iceaxe/hit` | MOD-SPEC §6.2 |
| — | `SDAXWAL` | `sd/weapon/iceaxe/wall` | this document (proposed) |
| — | `SDAXPKP` | `sd/weapon/iceaxe/pickup` | this document (proposed) |

The shovel drafts of the previous pass (`SDSHSWG`, `SDSHHIT`) were deleted
from `work/`; the generator refuses to make them (`RETIRED_LUMPS`).

## 2. Where the sound comes from

| Route | What | Licence | Used for |
|---|---|---|---|
| `SYN` | Our synthesis in `gen_weapon_sfx.py`: numpy, minimum-phase filters (no pre-ringing before a transient), fixed seeds | GPL-3.0 script, CC BY-NC-SA 4.0 output (D15) | every shot, boom, whoosh, hiss, howl, ring, scrape, the relay buzz; the whole of 9 lumps |
| `OGA-100` | rubberduck, *100 CC0 SFX* — pack row in `ENEMY-SOUNDS.md` §2.1 | CC0 | clicks, latches, metal clunks, springs, one splash |
| `KEN-IMP` | Kenney, *Impact Sounds* — pack row in `ENEMY-SOUNDS.md` §2.1 | CC0 (D36); one rule for enemy and weapon sounds (D44) | wood, tin and steel knocks for pickups and empty clicks; the axe's steel tick, flesh hit, ring and pick-on-rock hit; the Katyusha's rail lock |

Rules this file keeps:

- **No firearm recording.** OGA-100's `shot_01.ogg` and `shot_02.ogg` are
  excluded: what they recorded is not stated. A test fails if any `shot_*`
  file is ever listed.
- **No foreign clip ships alone.** Each is cut, re-pitched, filtered,
  enveloped and layered with synthesis.
- **No new download.** Only files already on disk under D36.
- `OGA-CRE1`, `OGA-CRE2`, `OGA-SNARL` (voices and creatures) are not used.

### 2.1 Provenance (per source file)

SHA-256 of the file as extracted under `work/audio/sfx_sources/`. The pack
archive, its URL and its own hash are `ENEMY-SOUNDS.md` §2.1. The generator
writes the same facts per lump to `work/audio/sfx/weapons/MANIFEST.txt` and
`PROVENANCE.tsv` (same columns as the enemies' table) on every run.

| Pack | File | Used in | SHA-256 |
|---|---|---|---|
| `OGA-100` | `switch_01.ogg` | `SDTTFIR`, `SDTTRLD`, `SDTTDRY`, `SDIZRLD`, `SDIZPKP`, `SDIZDRY`, `SDPPRLD`, `SDRPRLD`, `SDRPDRY`, `SDHKRLD`, `SDHKDRY` | `a24004ad0adbc08571324456963533c496bd27cf4808b40cb90833dc06b95792` |
| `OGA-100` | `switch_02.ogg` | `SDTTRLD`, `SDTTPKP`, `SDIZRLD`, `SDIZPKP`, `SDPPFIR`, `SDPPRLD`, `SDPPPKP`, `SDPPDRY`, `SDRKRLD`, `SDRKDRY` | `769dca6ccbea5c33cef602cdaa6ab0350b0dc2b093f02eae36f33e2552036f67` |
| `OGA-100` | `metal_01.ogg` | `SDRKRLD`, `SDRKPKP` | `f638423b1c67c9aeb0db9410b968ca1a89de728f3117f1bdd35a4fc7be4130ed` |
| `OGA-100` | `metal_02.ogg` | `SDTTRLD`, `SDPPRLD`, `SDPPDRY`, `SDHKRLD` | `545c2d698e72e1a3f0f22407fc0567a1f1041d9dbeff528bef0947284b45fdf2` |
| `OGA-100` | `metal_03.ogg` | `SDIZRLD`, `SDPPRLD`, `SDHKCHG` | `35ec56e5136e7091f36470c3e502e714819c9ff843baff0910b095571459f274` |
| `OGA-100` | `metal_07.ogg` | `SDRPRLD`, `SDRPPKP` | `16b6d8272f13ee84b40cb9e0863d412fcbf88e1ce46a5c59691eb53e18ed7d17` |
| `OGA-100` | `metal_09.ogg` | `SDIZRLD`, `SDIZPKP`, `SDPPRLD`, `SDHKRLD` | `0ac29c1f345c41ee6880876ccf4f69c66d1043b11d6c2f20cff49e78ae5d583b` |
| `OGA-100` | `metal_11.ogg` | `SDTTRLD`, `SDTTPKP` | `8f52c3a878e87ea2abb8f7a9fba90d0ec32034393661ddf87ba2b2b086024195` |
| `OGA-100` | `metal_12.ogg` | `SDHKPKP` | `ec09cebdd44a49ab1b744e86b7f881bbfb16a0ebb79e36b9a1ae3bf9a1612366` |
| `OGA-100` | `spring_04.ogg` | `SDPPFIR`, `SDPPRLD`, `SDPPPKP` | `48f679060be3538232d2d18d45c0b38285fffd07b8e21ebc6896d42aa9b53327` |
| `OGA-100` | `spring_06.ogg` | `SDPPRLD` | `a881b4d439c591a9b7478ce0929325ac93add608f75e11ec9f1aa5934469ee01` |
| `OGA-100` | `wooden_03.ogg` | `SDIZRLD` | `864c68b8622eaf900f2b9932d2998cc9840dc95b61a148e37550ddb382c92777` |
| `OGA-100` | `splash_01.ogg` | `SDRKPKP` | `8d48e8da680fbdfd3c885aa2f69d8e83ad16717bae43d178861d7af08d142849` |
| `KEN-IMP` | `impactMining_002.ogg` | `SDAXWAL` | `059558ec751115ca6b1441e00f0adc837c1a3eeb0a066b109e0fd879fc5d0b0c` |
| `KEN-IMP` | `impactPunch_heavy_000.ogg` | `SDAXHIT` | `b33a8f14068aec24ec69ba85e5e87fdc41228975f6a1a3e44a6e7d6fc3d9f8d8` |
| `KEN-IMP` | `impactSoft_heavy_001.ogg` | `SDAXHIT` | `4d0096364ba9e46119d2ff6df493fdc101bd2e1efae061da5e5f77a53b3fdcb6` |
| `KEN-IMP` | `impactWood_light_000.ogg` | `SDRPPKP` | `eb45e35b4bed784d3f120de4afec4b0d6ac09d9e143cce8cfcb7d739e1b1f3c3` |
| `KEN-IMP` | `impactWood_light_001.ogg` | `SDAXPKP` | `4b76bf3ccc8e60d19188f3165b778a7817786faa6887c55d9049bcbeef3b425f` |
| `KEN-IMP` | `impactWood_medium_000.ogg` | `SDIZPKP` | `1723a9fd25103ed41af06054814e84e65f4a772bac86ab2dc927da93d9592ff5` |
| `KEN-IMP` | `impactWood_medium_002.ogg` | `SDPPPKP` | `3f3f1917428b828f733a963167833c707bf88296ff158e1559c57c5cb813d799` |
| `KEN-IMP` | `impactMetal_light_000.ogg` | `SDAXPKP` | `33b5e6e37c6e9d54e07bf5a89b12c76e879f40c1ea83cdd82714df1d6f9fec6d` |
| `KEN-IMP` | `impactMetal_light_001.ogg` | `SDTTPKP` | `fba69c467ddd85da7b1d82e259f936b876d9ba6a3d6f1b24bdd10468e46bfe08` |
| `KEN-IMP` | `impactMetal_light_003.ogg` | `SDPPPKP`, `SDAXWAL` | `92d5db6bfc672d9dc1b4f390b2900504f013187fa36335472554fafefa9050b1` |
| `KEN-IMP` | `impactMetal_heavy_001.ogg` | `SDHKPKP` | `83554049f81f4db9209379e103c30bfa63f65c42189a03f300b045c2c82e23ae` |
| `KEN-IMP` | `impactMetal_light_002.ogg` | `SDAXHIT` (D44) | `25a96f90a9a1f88a531e824e126f0519504625e5635e65a72e4f31611428db29` |
| `KEN-IMP` | `impactMetal_medium_000.ogg` | `SDRPPKP` (D44) | `a96f879fec0864a8938e0c745b6996a6c5679c16a234ce31a01cc995e8401003` |
| `KEN-IMP` | `impactMetal_medium_002.ogg` | `SDPPDRY` (D44) | `7e89ce2ca0dbda95ea2b78d4b50791cab35c10d20e9f5ccd45dd0b00e99ff548` |
| `KEN-IMP` | `impactMetal_medium_004.ogg` | `SDRPDRY` (D44) | `03e10f800199c7166208e41c11cf4acfac6cc265467f02357da71972bc967295` |
| `KEN-IMP` | `impactMetal_heavy_003.ogg` | `SDHKCHG` (D44) | `b0f2ba4dabde9a87eb9c188a19d31e0c2300fd321adeba08d3b9b8aa011d7037` |
| `KEN-IMP` | `impactTin_medium_001.ogg` | `SDRKPKP` (D44) | `84253095543c094d83cd749f42ecfbc96e356b60385f18a192c18eafb25b3cc6` |
| `KEN-IMP` | `impactGeneric_light_000.ogg` | `SDIZDRY` (D44) | `f0e982611e97512fee5f777986b67e8b435434b601f94992ec044f7e89fb5acb` |

Synthesis only (`SYN`, no foreign input): `SDAXSWG`, `SDIZFIR`, `SDRPFIR`,
`SDRPEXP`, `SDRKFIR`, `SDHKFIR`, `SDHKEXP`.

When a lump is approved and enters `src/sounds/`, its rows above go to the
licence register (`docs/art/LICENSES.md`, not this agent's file).

The seven rows marked D44 were hashed on 2026-10-14 with `sha256sum` on the
files as extracted. A test (`test_plan_document_has_every_source_hash`)
hashes every source file the generator uses and fails if that hash is
missing from this table.

### 2.2 The D44 pass (2026-10-14): where Kenney went, and where it did not

D44 made one rule for both sound sets, so every card was looked at again for
a knock or a steel strike that was synthetic or missing. Each new layer sits
under or beside the existing ones, never alone (ENEMY-SOUNDS §2), and each
card's design is unchanged. The other 23 lumps came out byte-identical to the
2026-10-13 run.

| Lump | New `KEN-IMP` layer | Why | What it replaced or quietened |
|---|---|---|---|
| `SDAXHIT` | `impactMetal_light_002`, first 30 ms, choked in 6 ms | the pick's point was a burst of white noise; a real steel strike has the partials noise lacks. Choked so nothing rings: flesh damps steel | the noise tick, 0.45 → 0.30 |
| `SDAXWAL` | `impactMetal_light_003`, high-passed at 2 kHz | the pick's ring on stone was four pure sines, the most synthetic layer of the card | the sines, 0.18 → 0.08, kept for pitch |
| `SDIZDRY` | `impactGeneric_light_000` | the dull lock had only a synthetic thump for a body | the thump, 0.35 → 0.20 |
| `SDPPDRY` | `impactMetal_medium_002` | the card says "hollow clack"; the hollow was a sine thump | the thump, 0.6 → 0.45 |
| `SDRPPKP` | `impactMetal_medium_000` | the tube knocked by the hand, near the tube's middle mode (1.1 kHz) | the tube modes, 0.20 → 0.16 |
| `SDRPDRY` | `impactMetal_medium_004` | the hammer meeting steel on an empty tube | nothing |
| `SDRKPKP` | `impactTin_medium_001` | the canister is thin sheet steel; it was the only pickup with no Kenney layer | nothing |
| `SDHKCHG` | `impactMetal_heavy_003` | the rail frame's weight landing in the lock at 20 tics, under the `OGA-100` clunk | nothing |

Measured, not heard: muting each new layer in its recipe and restoring it,
the layer carries 10–17 % of the energy around its own peak (a 30 ms
window, all bands) on the six handling cards, and 45–49 % of the 1.5–10 kHz
band in the first 60 ms of the two axe cards, where the steel lives. None is
buried; none dominates. Two layers first measured at 5 % (`SDRPDRY`,
`SDHKCHG`) were raised before the final render.

**Left as they were, and why:**

- **Reloads** (`SDTTRLD`, `SDIZRLD`, `SDPPRLD`, `SDRPRLD`, `SDRKRLD`,
  `SDHKRLD`): parked by the PM pending the CEO (D39), so untouched by
  instruction, although reload mechanics are where Kenney's steel knocks
  would fit next.
- **Shots, booms, the swing and the flame** (`SDTTFIR`, `SDIZFIR`, `SDPPFIR`,
  `SDRPFIR`, `SDRPEXP`, `SDRKFIR`, `SDHKFIR`, `SDHKEXP`, `SDAXSWG`): our
  synthesis by design (§2), and the pack has no shot, blast or whoosh.
  Debris for the two explosions could come from `impactMining_*` later; not
  done here, because the explosions are wired and this pass was about knocks
  and strikes.
- **The small clicks** (`SDTTDRY`, `SDRKDRY`, `SDHKDRY`): the pack's lightest
  files are 9–16 ms knocks centred near 1.1–1.3 kHz, duller than a pistol
  hammer's or a toggle's click; `OGA-100`'s switches stay.
- **Pickups that already had Kenney** (`SDAXPKP`, `SDTTPKP`, `SDIZPKP`,
  `SDPPPKP`, `SDHKPKP`) and the axe's flesh layers: already layered, no gap.

## 3. Engine facts the sounds are cut to

Read from `src/zscript/weapons/*.zs` on 2026-10-13; each is a named
constant in the generator and a test reads the `.zs` again, so a change in
the code turns the suite red instead of silently de-syncing a sound.

| Fact | Value | Consequence |
|---|---|---|
| Ice axe: `PUNG B 5`, then `A_SD_IceAxeSwing` | 5 tics = 0.143 s | the swing peaks at ~0.11 s, before the blow |
| TT-33 cycle | 4 + 6 + 3 + 3 = 16 tics = 0.457 s | `SDTTFIR` (0.435 s) is over before the next shot |
| PPSh-41 round | 3 tics = 86 ms (700 rpm) | ≥ 90 % of `SDPPFIR`'s energy inside 86 ms |
| IZh-58 reload | 6 + 8 + 8 + 8 = 30 tics; shells counted after 22 | `SDIZRLD` snaps shut at 0.62 s, ±40 ms |
| RPG-7 cycle | 8 + 14 + 4 = 26 tics; launch after 8 | the proposed reload (§6) has 14 tics = 0.40 s; `SDRPRLD` is 0.38 s |
| Katyusha charge | `BFGG A 20` | `SDHKCHG` 0.69 s |
| Katyusha recovery | `BFGG B 20 A_ReFire` after the salvo | `SDHKRLD` ≤ 20 tics = 0.571 s |

**ASSUMPTION, not verified in this engine:** a sound started on
`CHAN_WEAPON` stops the one already playing on that channel of the same
actor. `SDPPFIR` is built so that this does not matter (everything audible
happens inside one round), and the preview has the PPSh burst both ways,
cut and overlapping. It does matter for the Katyusha's reload (§6).

## 4. The cards

Lengths and levels measured on the WAVs the generator wrote on 2026-10-13;
the eight cards of §2.2 re-measured on 2026-10-14.
"Short-term" is the loudest 50 ms window (mean square, dB re full scale), a
ruler and not LUFS.

**Levels.** Shots and impacts are normalised to their peak (−1 dBFS; the
PPSh −2, the ROKS-3 −3, the Katyusha's per-rocket burst −6 because six can
sound at once). Handling sounds are levelled by short-term loudness, not by
peak: on the first pass, peak-normalised pickups read −12 to −18 dB
short-term, **louder than a pistol shot** (−13.8). Now reload −20, pickup
−21, empty click −25, all under the quietest shot of the arsenal (one PPSh
round, −16.2), and a test holds that order. This also lowered the IZh's
break-open, which was at −1 dBFS peak.

### 4.1 Ice axe (slot 1, D40)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDAXSWG` | `sd/weapon/iceaxe/swing` | 0.30 s | −1.0 / −11.9 | A steel head, narrower and higher than a shovel's blade: band noise whose centre climbs with the head's speed (0.7 → 2 kHz), a faint whistle from the pick's point (1.5 → 2.6 kHz) and a thin low band for the shaft. Peaks at 0.11 s, before the blow. **Sweep A/B/C.** |
| `SDAXHIT` | `sd/weapon/iceaxe/hit` | 0.33 s | −1.0 / −8.7 | The pick goes in: a steel tick (a real strike, `impactMetal_light_002`, cut to 30 ms, over 2 ms of noise), a 95 → 50 Hz thud, two body impacts (`impactPunch_heavy_000`, `impactSoft_heavy_001`), a short wet flutter. No ring: flesh damps steel. **Sweep.** |
| `SDAXWAL` | `sd/weapon/iceaxe/wall` | 0.40 s | −1.0 / −11.0 | Pick on concrete or stone: `impactMining_002` (a pick on rock) under a bright crack, a short steel ring (`impactMetal_light_003` over four quiet partials, 3.2–8.8 kHz), the shaft jarring, and grit falling for 0.25 s. **Sweep.** |
| `SDAXPKP` | `sd/weapon/iceaxe/pickup` | 0.29 s | −6.0 / −21.0 | Lifted off the dorm rack: the wooden shaft knocks, the head clinks, a hand closes on the grip. |

### 4.2 TT-33 (slot 2)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDTTFIR` | `sd/weapon/tokarev/fire` | 0.44 s | −1.0 / −13.8 | Dry, high-velocity crack (7.62×25 is a bottlenecked, fast round), a mid body, a short room tail, the slide's click at 55 ms. Built by the previous pass, kept unchanged. **Sweep.** |
| `SDTTRLD` | `sd/weapon/tokarev/reload` | 0.86 s | −6.7 / −20.0 | Release pressed, magazine out (scrape), a fresh one in and seated at 0.44 s, slide released and slamming home at 0.70 s, the loudest moment. |
| `SDTTPKP` | `sd/weapon/tokarev/pickup` | 0.40 s | −8.8 / −21.0 | A grip on steel, the slide eased back a hair and let go: the press check. |
| `SDTTDRY` | `sd/weapon/tokarev/dry` | 0.06 s | −6.0 / −25.9 | The hammer falls on an empty chamber: one small crisp click. |

### 4.3 IZh-58 (slot 3)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDIZFIR` | `sd/weapon/izh/fire` | 1.10 s | −1.0 / −7.6 | One barrel of a 12-gauge: a deep 92 → 42 Hz boom with its octave, a long rumble darkening in the room. Kept from the previous pass. **Sweep.** |
| `SDIZRLD` | `sd/weapon/izh/reload` | 0.89 s | −10.9 / −20.0 | Top lever thrown, barrels drop on the hinge, two hulls drawn, two shells pushed in, snap shut at 0.62 s on the frame where the shells are counted. Kept from the previous pass, now levelled (§4). |
| `SDIZPKP` | `sd/weapon/izh/pickup` | 0.58 s | −11.9 / −21.0 | The stock knocks, the gun is broken open and snapped shut: the hunter's check that it is empty. |
| `SDIZDRY` | `sd/weapon/izh/dry` | 0.08 s | −8.5 / −25.0 | The hammerless lock clicks on nothing: duller and lower than the pistol's; the internal hammer's knock is `impactGeneric_light_000`. |

### 4.4 PPSh-41 (slot 4)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDPPFIR` | `sd/weapon/ppsh/fire` | 0.33 s | −2.0 / −16.2 | One round: crack, a tinny resonant body (the perforated jacket), a jacket ring, the open bolt slamming home at 28 ms, the drum's spring. Everything that matters lives in 86 ms. Three bursts on the preview: 700 rpm cut (the engine), 900 rpm cut (the real gun), 700 rpm overlapping. Kept from the previous pass. **Sweep.** |
| `SDPPRLD` | `sd/weapon/ppsh/reload` | 1.03 s | −11.6 / −20.0 | The 71-round drum: catch pressed, drum out with its rounds shifting, a full one seated at 0.45 s, the bolt hauled back and caught at 0.86 s. |
| `SDPPPKP` | `sd/weapon/ppsh/pickup` | 0.34 s | −11.5 / −21.0 | Wooden stock, steel jacket, the drum's rounds shifting, a sling swivel. |
| `SDPPDRY` | `sd/weapon/ppsh/dry` | 0.14 s | −12.1 / −25.0 | An empty drum: trigger and sear give one heavier, hollow clack; the hollow is the steel receiver (`impactMetal_medium_002`). |

### 4.5 RPG-7 (slot 5)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDRPFIR` | `sd/weapon/rpg7/fire` | 1.41 s | −1.0 / −8.9 | Recoilless thump and back-blast whoosh, then the sustainer motor's hiss and falling whistle as the round flies off. Kept from the previous pass. |
| `SDRPEXP` | `sd/weapon/rpg7/explode` | 1.61 s | −1.0 / −7.4 | A shaped charge: a hard crack first, the boom, a long dark tail, debris. Kept from the previous pass. |
| `SDRPRLD` | `sd/weapon/rpg7/reload` | 0.38 s | −9.9 / −20.0 | A PG-7V pushed into the muzzle: the round scrapes down the tube (whose three modes ring faintly), seats with a clunk at 0.20 s, the detent clicks. |
| `SDRPPKP` | `sd/weapon/rpg7/pickup` | 0.48 s | −11.2 / −21.0 | The wooden heat guard knocks and the steel tube, knocked by the hand (`impactMetal_medium_000`), rings hollow. |
| `SDRPDRY` | `sd/weapon/rpg7/dry` | 0.29 s | −12.5 / −25.0 | The exposed hammer snaps on steel (`impactMetal_medium_004`) with no grenade in the tube, and the empty tube rings. |

### 4.6 ROKS-3 flamethrower (slot 6)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDRKFIR` | `sd/weapon/roks3/fire` | 0.59 s | −3.0 / −10.9 | A valve hiss and a roaring, flickering jet; restarted every 3 tics while held. Kept from the previous pass. |
| `SDRKRLD` | `sd/weapon/roks3/reload` | 1.05 s | −8.7 / −20.0 | A fresh fuel canister: knocked into place, the coupling turned home (four ratchet clicks), pressure hissing up, the igniter cartridge armed at 0.88 s. |
| `SDRKPKP` | `sd/weapon/roks3/pickup` | 0.75 s | −9.9 / −21.0 | The tank pack lifted: a thin steel canister (`metal_01` with `impactTin_medium_001`) and fuel sloshing inside it (`splash_01`, slowed and darkened), a hose. |
| `SDRKDRY` | `sd/weapon/roks3/dry` | 0.27 s | −10.3 / −25.0 | Tank empty: the igniter snaps and a last breath of gas sputters out three times. |

### 4.7 Hand Katyusha (slot 7)

| Lump | Logical name | Length | Peak / short-term | Card |
|---|---|---|---|---|
| `SDHKCHG` | `sd/weapon/katyusha/charge` | 0.69 s | −1.0 / −14.9 | Rails elevated by a geared crank: a rising whine, ratchet teeth closing up, locked at 20 tics; the frame's weight lands in the lock (`impactMetal_heavy_003`, D44). |
| `SDHKFIR` | `sd/weapon/katyusha/fire` | 1.41 s | −1.0 / −9.7 | Six rockets off the rails, rippled 65 ms apart, each with its own crack, thump and howl. Kept from the previous pass. |
| `SDHKEXP` | `sd/weapon/katyusha/burst` | 0.90 s | −6.0 / −13.2 | One salvo rocket: smaller and shorter than the PG-7V. Six can sound at once. Kept from the previous pass. |
| `SDHKRLD` | `sd/weapon/katyusha/reload` | 0.57 s | −11.3 / −20.0 | Rockets slid onto the rails in three quick strokes, the rack latch dropping at 0.38 s. Fits the 20-tic recovery frame. |
| `SDHKPKP` | `sd/weapon/katyusha/pickup` | 0.71 s | −11.0 / −21.0 | The rail frame lifted: a heavy clank and the rails ringing (four partials, 0.6–4.2 kHz). |
| `SDHKDRY` | `sd/weapon/katyusha/dry` | 0.16 s | −9.8 / −25.0 | The firing switch thrown on empty rails: a toggle snap and a dead relay buzzing at 50 Hz, the Soviet mains frequency. |

## 5. Takes (the sweep)

`SDAXSWG`, `SDAXHIT`, `SDAXWAL`, `SDTTFIR`, `SDIZFIR` and `SDPPFIR` are on
the preview as three takes: **A** as designed, **B** 8 % slower (lower,
heavier), **C** 8 % faster (higher, drier). They are varispeed of the same
recipe, so a take is a choice of weight, not of design. The take a lump
ships with is one line of the generator (`CHOSEN_TAKE`); A by default.
Varispeed moves timing by ±8 %, measured harmless: the axe swing peaks at
0.116 / 0.126 / 0.107 s (A / B / C), all before the blow at 0.143 s, and the
PPSh round keeps 99.6 % or more of its energy inside 3 tics on every take.
The tests run on the chosen take.

## 6. What `mod-engineer` needs to wire (proposals, NOT VERIFIED in engine)

Nothing below is done; `src/` belongs to `mod-engineer`. Every proposal
keeps the tic counts of `BALANCE.md` (D39). Engine behaviour marked NOT
VERIFIED was read from memory of the ZDoom wiki, not checked in GZDoom
4.14.2.

| Lump(s) | Hook | Note |
|---|---|---|
| the 11 wired lumps | `src/sounds/<LUMP>.ogg` + the right-hand column of SNDINFO | the generator writes the OGGs to `work/audio/sfx/weapons/ogg/` |
| `SDAXSWG` | the two lines already written in SNDINFO's header (T10): the SNDINFO entry and `A_StartSound("sd/weapon/iceaxe/swing", CHAN_WEAPON)` on `PUNG B 5` | the hit, 5 tics later on the same channel, cuts the swing's tail when the blow lands, which is the wanted effect (ASSUMPTION §3); a miss plays it whole |
| `SDAXWAL` | (a) an `SD_IceAxePuff` whose `AttackSound` is `sd/weapon/iceaxe/wall` (a puff's AttackSound plays when it hits a wall, its SeeSound when it hits a bleeding actor: **NOT VERIFIED**); or (b) in `A_SD_IceAxeSwing`, keep the puff `LineAttack` returns and play the wall sound when there is a puff and no `linetarget` (**NOT VERIFIED** that the return is non-null on a wall) | a non-bleeding target (a barrel) still sets `linetarget` and plays the flesh hit; acceptable for F4 |
| `*PKP` (7) | `Inventory.PickupSound "sd/weapon/<weapon>/pickup";` in each weapon's `Default` block | today every weapon pickup plays Doom's generic `misc/w_pkup` (Freedoom `DSWPNUP`, heard on the preview) |
| `*DRY` (6) | a check before `A_WeaponReady` in `Ready`: fire pressed this tic, not last tic, and `CheckAmmo` fails → `A_StartSound("sd/weapon/<weapon>/dry", CHAN_WEAPON)` | **must not** change the auto-switch of `BALANCE.md` §4.1 (so not `WEAPON.AMMO_OPTIONAL`). The case it serves is exactly §4.1's: an empty TT-33 with no ice axe stays raised and the trigger does nothing; today that is silent, and silence read as a bug to the CEO once already ("una puerta que no hace ningún ruido"). The Katyusha is "empty" under 40 Cell |
| `SDRPRLD` | split `MISG B 14 A_FireProjectile(...)` into `MISG B 4 A_FireProjectile(...)` + `MISG B 10 A_StartSound("sd/weapon/rpg7/reload", CHAN_WEAPON)`; total 26 tics unchanged | the launch sound belongs to the grenade actor, so the player's `CHAN_WEAPON` cuts nothing; the code's own comment already says the RPG-7 "is reloaded from the muzzle" in that frame |
| `SDHKRLD` | at the start of `BFGG B 20 A_ReFire`, on a channel **other than** `CHAN_WEAPON` (e.g. `CHAN_ITEM`) | `SDHKFIR` (1.4 s) was started on `CHAN_WEAPON` 10 tics earlier; reusing that channel would cut the salvo's howl at 0.29 s (ASSUMPTION §3) |
| `SDTTRLD`, `SDPPRLD`, `SDRKRLD` | **none recommended now**: these guns have no reload state (Doom's model: no magazines) | playing a 0.9–1.0 s reload on every weapon switch would grate; they wait for a magazine mechanic, which is a balance question for the CEO (D39 keeps the arsenal as built). Delivered so the decision is made by ear, not on paper |

## 7. How to audition (the PM)

```bash
.venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --list        # the plan, writes nothing
.venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py               # all 31 -> work/audio/sfx/weapons/, ogg/, the overlay PK3
.venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --preview docs/art/previews/<YYYY-MM-DD_HHMM>_F4_weapon-sfx-drafts.html
# a pass that keeps the design: copy work/audio/sfx/weapons/ aside first, then
.venv/Scripts/python.exe tools/audio/gen_weapon_sfx.py --preview docs/art/previews/<YYYY-MM-DD_HHMM>_F4_<slug>.html --compare <the copy>
.venv/Scripts/python.exe -m unittest tests.test_gen_weapon_sfx -v
```

Outside the engine: open the preview page, or play
`work/audio/sfx/weapons/<LUMP>.wav` and `preview/SDPPFIR_burst_*.wav`.

In the engine (**the PM's, D26**; agents never start GZDoom): load
`work/audio/sfx/sd-weapon-sfx-draft.pk3` **after** `dist/sovietdoom.pk3`, on
the practice range (D41; the lump `RANGE` since D62, MAP02 before). Its SNDINFO redefines the 11 wired names; a later
definition of a logical name replacing an earlier one is **NOT VERIFIED**
in this engine. The 20 names marked `// needs a hook` play only from the
console, e.g. `playsound sd/weapon/tokarev/dry`. Owed: one engine pass to
confirm the overlay wins and that the 11 wired drafts play where the cards
say.

## 8. What was verified, and what was not

**Verified (2026-10-13, this PC):** every lump renders; two runs give
byte-identical WAVs and PK3; no sample clips; each length sits within its
card; shots start within 5 ms; every lump ends in silence; the timings of
§3 against the `.zs` files; handling under the quietest shot; the preview
page embeds 64 OGG clips, all decodable; every source file's SHA-256 (§2.1).
`tools/verify.py fast` PASS.

**Verified (2026-10-14, this PC, the D44 pass):** the 2026-10-13 drafts
reproduced byte for byte before anything changed; after the pass exactly the
eight lumps of §2.2 differ and the other 23 are byte-identical; every test
of `tests/test_gen_weapon_sfx.py` passes on the full render (levels, onsets,
lengths, timings); each source file's SHA-256 in §2.1 is checked by a test;
the before/after page holds those eight cards and nothing else.

**Not verified:**

- **How any of it sounds.** Not listened to by anyone.
- The overlay's precedence in GZDoom, and every engine behaviour marked
  NOT VERIFIED or ASSUMPTION in §3 and §6.
- That the OGG files and the preview are byte-identical on another machine
  (they depend on the local ffmpeg build; the WAV masters do not).
- GameSynth's own terms on generated sound were never read. This no longer
  holds anything back: the CEO took Kenney's CC0 as the rule for both sound
  sets (D36, D44).

## 9. Decisions for the CEO

1. **Listen and approve, per card or per weapon.** The preview has the
   stand-in heard today beside each draft. Recommendation: judge the four
   priority sounds first (TT-33, PPSh-41, IZh-58 fire and the ice axe hit),
   because they are heard most.
2. **Pick a take** on the six sweep cards, or keep A.
3. **Empty clicks and pickups: yes or no.** Recommendation: yes. Both are
   cheap hooks, neither changes balance, and the empty click fixes a silent
   dead trigger. Cost: one `mod-engineer` pass and one engine run.
4. **Reloads for the TT-33, PPSh-41 and ROKS-3:** park them (recommended)
   or ask for a magazine mechanic, which reopens `BALANCE.md` (D39).
5. ~~`KEN-IMP` in weapon sounds~~: **decided, D44** (2026-10-14): one rule
   for enemy and weapon sounds, Kenney is used in both. Done in §2.2; the
   eight re-layered cards are on
   `docs/art/previews/2026-10-14_1030_F4_weapon-sfx-kenney-layers.html`.
