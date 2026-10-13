# Enemy sounds — one card per lump, with origin and rights

Living document. Owner: `sound-designer`. Russian mirror:
`docs/ru/sound/ENEMY-SOUNDS.md`, **not yet written** (D34: the mirror is
synced in a batch at the phase close). Created 2026-10-13 (F5, after D35).
Source of the list: `docs/engine/BESTIARY.md` §3-§9 ("States and sounds") and
the naming rule of §2.3; the SNDINFO contract is `docs/engine/MOD-SPEC.md`
§6.2. Music rights live in `docs/sound/MUSIC-RIGHTS.md`; this document owns
**sound-effect and voice rights** only.

> **Status: research and plan. Nothing has been downloaded, produced or
> approved, and nothing is in the PK3.** The mod-engineer is writing the
> seven actors with Freedoom lumps as stand-ins; every lump below is
> a *replacement* for one of those stand-ins and changes one line of
> `SNDINFO`, no ZScript. Nothing enters `src/sounds/` without the CEO's
> explicit approval, exactly as with textures and music.

---

## 0. The recommendation in six lines

1. **Do not build the 47 lumps from one source.** Split them by what the
   sound physically is: human voices (12), creature sounds (19), mechanical
   and impact sounds (13), gibs (3).
2. **Human voices (12): the CEO's own voice, processed** (route d). It is the
   only route with no rights question at all and the only one that can give
   the Reich and the Legion different voices on purpose. Fallback if he
   declines: route b + c, clearly weaker.
3. **Creature sounds (19): CC0 packs by authors who recorded them
   themselves, layered and processed by us** (route b + c). Two packs by one
   author (rubberduck, own-voice recordings, CC0) plus one snarl pack.
4. **Gunshots, bolts, impacts, explosions, footstep, drones (13): our own synthesis**
   (route c), reproducible from a script as the music is.
5. **Gibs (3): edited Freedoom `DSSLOP`** (route a, BSD-3), layered with our
   own thump. Freedoom is otherwise the **fallback and the timing reference**,
   not the base: Freedoom's sounds are Doom-role sounds, and the CEO has
   already rejected one Doom-flavoured placeholder (the chainsaw swing).
6. **What I need from the CEO:** approve a download list of five CC0 packs,
   say yes or no to recording his voice, and choose the General's order
   (section 6).

---

## 1. Count: the list has 47 lumps, not 52

`BESTIARY.md` §12 and §2.6 say **52 sound lumps**. The "States and sounds"
tables of the same file list **47** rows. Per actor (stated in §12 / rows
actually listed): rifleman 7 / 6, trooper 6 / 6, Stormtrooper 8 / 8, hound
6 / 5, Doughboy 8 / 7, Panzermensch 9 / 8, General 8 / 7. Five actors are
one short; the other two match. I cannot tell which five lumps the 52 counts.
**This document is built on the 47 listed rows.** The General's "order" the
PM mentioned is not extra: it is `SDGENSUM`, already row 47 of the 47. If
`mod-engineer` adds the missing five, each gets a row here the same day.

---

## 2. Source key (every row cites these IDs)

Status words: **VERIFIED** = I read the page or file on 2026-10-13 and the
fact is as stated. **PENDING** = true only after a download, which needs the
PM/CEO. **ASSUMPTION** = I believe it and could not check.

| ID | What | Licence | Status |
|---|---|---|---|
| `FD:DSxxxx` | A lump of Freedoom 0.13.0 (`iwads/freedoom2.wad`, 109 `DS*` lumps) | BSD-3-Clause (project-wide; `COPYING.adoc` read at github.com/freedoom/freedoom) | Lump existence, sample rate and length **VERIFIED** by reading the WAD directory. What it *sounds like*: **NOT VERIFIED, I have not listened.** Per-sample origin: Freedoom's `sounds/README` and `CREDITS` say nothing about it (**VERIFIED**); its site calls the effects original (**VERIFIED**). Accepted under D2. |
| `OGA-CRE1` | rubberduck, *80 CC0 creature SFX*, 2018-07-01. Alien 6, Grunt 5, Hurt 5, Monster 7, Roar 3, Scream 2, Spit 3, Breath 1, Troll 3, Weird 5, Barking 2, others. 1.9 MB ZIP. <https://opengameart.org/content/80-cc0-creature-sfx> | CC0 (page shows CC0 1.0 link). Author states in comments he made most with **his own voice plus filters**. | Page **VERIFIED**. Per-file names, and that the ZIP contains what the page says: **PENDING**. |
| `OGA-CRE2` | rubberduck, *80 CC0 creature SFX #2*, 2018-08-02. Monster 13, Human 8, Slime 8, Alien 6, Attack 5, Die 4, Grunt 4, Weird 4, Roar 3, Stomp 1, Bug 9. 1.9 MB ZIP. <https://opengameart.org/content/80-cc0-creture-sfx-2> | CC0 | idem |
| `OGA-SNARL` | Darsycho, *Monster snarls*, 2018-10-17. Five OGG files, 863 KB in all. <https://opengameart.org/content/monster-snarls> | CC0 (credit "appreciated", not required) | Page **VERIFIED**; contents **PENDING**. |
| `OGA-100` | rubberduck, *100 CC0 SFX*, 2018-06-29: Metal 12, Slam 7, Hit 4, Shot 2, Machine loop 3, Weird 5, Explosion 1, Switch 2 ... <https://opengameart.org/content/100-cc0-sfx> | CC0 | Page **VERIFIED**. One commenter reported files erroring after unzipping: check on download. |
| `KEN-IMP` | Kenney, *Impact Sounds*, 130 files, tags impact + foley. <https://kenney.nl/assets/impact-sounds> | CC0 (page shows "Creative Commons CC0"); `kenney.nl/support`: all assets on the asset pages are CC0, no attribution required | Page **VERIFIED**. Size and format: **PENDING**. |
| `KEN-SCI` | Kenney, *Sci-fi Sounds*, 70 files, tags sci-fi, space, engine. <https://kenney.nl/assets/sci-fi-sounds> | CC0 | Page **VERIFIED**. Exact contents (it may be mostly engines and not zaps): **PENDING**. |
| `FS-CC0` | Freesound, filter "Creative Commons 0", per-sound | CC0 *per sound*; the uploader asserts it, Freesound does not guarantee it (its FAQ says users may upload illegal content, **VERIFIED**). **Downloading requires a logged-in account** (**VERIFIED**). | **Not planned.** Kept as a gap-filler for one sound at a time, each with its own page check. A search listed hundreds of CC0 growls (**VERIFIED**: the listing exists); I have not opened any individual sound page. |
| `SYN` | Our own synthesis: a script `gen_sfx.py` (numpy; the project venv already has numpy 2.5.4, **VERIFIED**), deterministic seeds, output WAV then OGG | GPL-3.0 for the script, CC BY-NC-SA 4.0 for the output (D15) | To be written. |
| `VOX` | The CEO's voice, recorded by him, then processed by us | His own work; he applies CC BY-NC-SA 4.0 (D15). A recognisable voice is personal data, so the line "released under D15" must come from him in writing (the chat is enough). | Needs his yes. |

**Why CC0 and why only these authors.** Three of the five packs are by one
person whose voice *is* the sound; two are by a studio that publishes its own
work. That is as close to "the author is the source" as free banks get. CC0
is the only licence that costs nothing in a CC BY-NC-SA 4.0 package: it has no
attribution duty, no non-commercial clause and no share-alike clause to
collide with ours. Credit is still listed in `LICENSES` as courtesy.

**Residual risk, stated plainly.** CC0 on OpenGameArt is the uploader's
assertion; the site does not check that he owned every recording. For that
reason (1) every used file will get an entry in a provenance table
(pack URL, retrieval date, ZIP SHA-256, inner file name), (2) no CC0 clip
ships unlayered if it is recognisable, and (3) a pack is dropped if its page
changes licence. This is not legal advice (agent rules).

---

## 3. Sources I rejected, and why

| Source | Verdict | Reason |
|---|---|---|
| Sonniss GameAudioGDC bundles | **No** | The page says standalone redistribution of originals or edits, "alone or inside a sound library, sample pack, or asset pack", is not allowed (**VERIFIED**, summary page only; the full licence was not readable). Our assets are CC BY-NC-SA and re-shareable by design, which is a standalone-redistribution path. Incompatible with D15. |
| Pixabay sounds | **No** | Own "Content License", not CC0 (**VERIFIED**); bans standalone distribution. Same collision. |
| Mozilla Common Voice (German) | **No** | Datasets are listed CC0-1.0 (**VERIFIED**), but the datasheets add: no identifying speakers, no re-hosting or re-sharing of the dataset, and the stated purpose is speech-recognition training. Recordings of 20,000 real people reading sentences; cutting them into a Nazi-faction enemy's mouth is a consent question the licence does not answer. |
| LibriVox | **No** | Its pages say public domain **in the USA** and ask others to check locally (**VERIFIED** by search). Audiobook readers, not barks. |
| Windows SAPI / macOS `say` voices | **No** | Licence of the output **NOT VERIFIED**, treated as unusable. |
| eSpeak NG | **No** | GPL-3.0 (**VERIFIED**); its COPYING does not say how the GPL's "output" clause applies to synthesised speech (**NOT VERIFIED**). Not worth the doubt. |
| BBC Sound Effects archive | **No** | From memory its terms are personal, educational and research use only. **ASSUMPTION**, excluded anyway. |
| Any sound ripped from Doom, Wolfenstein, Duke or other commercial games, or from "free sound" lists that are really rips | **No** | Project rule (`CLAUDE.md`, "no assets from commercial games"). |
| Historical recordings (speeches, rallies, radio) | **No** | Fonograma rights as in `MUSIC-RIGHTS.md` §1, and D11 (serious tone) — a real Nazi speech in the mouth of an alien is not what D12 licenses. |

---

## 4. Voice approach (D11, D12)

D11 asks for a serious tone; D12 allows the symbols and says the invaders do
not trivialise real victims. Audio is where that line is easiest to cross by
accident, so the rules for voices are:

- **The Reich speaks "a language that is not quite German"** (the brief in
  `BESTIARY.md` §3). I propose to take that literally: invented syllables
  with German phonotactics, harsh consonants and a flat, clipped cadence.
  **No real German sentence, no slogan, no salute, no recognisable word of
  the regime.** Reasons: it keeps the faction alien instead of historical,
  it keeps D12's "fantastic alternate history" honest, and it sidesteps any
  storefront or rating question about spoken Nazi phrases that the
  *symbols'* justification (D12) does not cover. This is a design rule I
  recommend, not a legal finding; the CEO can overrule it (section 6, B).
- **The Legion speaks English through a radio and a vocoder** (`BESTIARY.md`
  §4): processed, clipped, with squelch. Mostly unintelligible; at most single
  neutral words ("Contact", "Move"). **No accent caricature**: a cartoon
  Texan would break D11 at once.
- **The General is the only voice that is meant to be understood**, and only
  once (`SDGENSUM`). He is "tall and unhurried" with "a smooth chrome plate
  with a single slot" for a face (`BESTIARY.md` §9): a low, calm, narrow-band
  voice that sounds as if it leaves through the slot. He does not shout.
- **Creatures** (hound, Doughboy, Panzermensch's non-speech) use no words.
- Everything is **mono, dry for the Reich, band-limited for the Legion**, so
  the faction is identifiable "behind a door with the lights off".

Processing chains, written once so every row can cite them:

| Chain | Recipe | Used by |
|---|---|---|
| `REICH-DRY` | high-pass 80 Hz, gentle saturation, **no reverb**, pitch -2 to -3 semitones, 6 dB presence at 2-3 kHz | rifleman |
| `LEGION-RADIO` | band-pass 400-3200 Hz, 8-bit/8 kHz crush, hard clip -6 dB, saw carrier (vocoder edge), 60 ms filtered-noise squelch burst at head and tail | trooper |
| `HYBRID-GLITCH` | organic layer + a 5-15 ms stutter/bit-crush layer on the Legion side | Stormtrooper |
| `HELMET-RESONANCE` | comb/resonant peak around 350-450 Hz, as if heard inside a steel bowl | Doughboy |
| `PLATE-LOW` | pitch -5 semitones, low-pass 3 kHz, armour clank layer from `KEN-IMP` | Panzermensch |
| `GENERAL-SLOT` | pitch -4 semitones, narrow band-pass 500-2500 Hz, short comb (slot), 1.2 s decay tail, slow attack | General |

---

## 5. The cards

Reading the tables. **Origin** is `primary → fallback`. Primary letters:
**D** = `VOX`, **B** = CC0 banks (always layered with **C**), **C** = `SYN`,
**A** = Freedoom edit. "Rate/len" of a Freedoom lump is verified from the
WAD directory. The Freedoom lumps named are the role-equivalent ones; none
has been listened to, so "base" means "timing and length reference, to be
judged by ear". Target lengths are mine.

### 5.1 Reich rifleman (`SD_ReichRifleman`, code `RRI`) — 6 lumps

Voice: `REICH-DRY`, invented syllables.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDRRIACT` | Spawn (idle) | A muttered order, not meant to be understood; heard through doors | **D** → C formant babble → `FD:DSPOSACT` (22 kHz, 1.4 s) | `VOX`; fallback `SYN`/`FD` |
| `SDRRISIT` | See | A short bark, ≤ 0.5 s, heard many times per map: must not tire | **D** → `OGA-CRE1` Grunt → `FD:DSPOSIT1-3` (0.85-1.4 s) | `VOX`; `OGA-CRE1` PENDING |
| `SDRRIATK` | Missile | **Dry bolt-action crack, drier and higher than the player's TT-33**, plus a bolt click; no tail. Incoming must not sound like outgoing | **C**: noise burst, ~8 ms attack, ~120 ms decay, band-pass 1-5 kHz, bolt-throw click → `OGA-100` Shot (2) | `SYN`. **Not `FD:DSPISTOL`**: it is the TT-33's own placeholder (`SNDINFO`), which would defeat the brief |
| `SDRRIPAI` | Pain | A cut-off grunt, 0.2-0.3 s | **D** → `OGA-CRE1` Hurt (5) → `FD:DSPOPAIN` (11 kHz, 0.4 s) | `VOX` / `OGA-CRE1` PENDING |
| `SDRRIDTH` | Death | An exhale that breaks into a collapse, ~1 s; no scream | **D** → `OGA-CRE2` Die (4) → `FD:DSPODTH1-3` | `VOX` / `OGA-CRE2` PENDING |
| `SDRRIXDT` | XDeath (gib) | A wet burst, no voice | **A**: `FD:DSSLOP` (22 kHz, 1.1 s) + our low thump | `FD` BSD-3 (notice required in `LICENSES` if shipped) + `SYN` |

### 5.2 Liberty Legion trooper (`SD_LegionTrooper`, code `LTR`) — 6 lumps

Voice: `LEGION-RADIO`. Brief from §4: processed and clipped; the player names
the faction by ear.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDLTRACT` | Spawn (idle) | Radio chatter: squelch opens, English mumble, squelch closes | **D** (mumble) + chain → C (noise + vocoded formant) | `VOX` / `SYN` |
| `SDLTRSIT` | See | One clipped word and a squelch tail, ≤ 0.6 s | **D** + chain → C vocoded syllable | idem |
| `SDLTRATK` | Missile | A shotgun blast **heavier and more metallic than the player's IZh** (three pellets, one sound); a short chrome ring on top | **C**: noise + 70 Hz sine thump + comb ring → `OGA-100` Shot / `KEN-IMP` | `SYN`. **Not `FD:DSSHOTGN`**: the IZh placeholder |
| `SDLTRPAI` | Pain | A grunt through a bad radio, 0.3 s | **D** + chain → `OGA-CRE2` Human (8) + chain | `VOX` / `OGA-CRE2` PENDING |
| `SDLTRDTH` | Death | The voice drops and the signal dies: falling carrier, squelch click-off | **D** + chain + C falling tone → `OGA-CRE2` Die + chain | idem |
| `SDLTRXDT` | XDeath (gib) | The rifleman's burst plus a crackle of radio static | **A**: `FD:DSSLOP` + C static burst | `FD` + `SYN` |

### 5.3 Hybrid Stormtrooper (`SD_Stormtrooper`, code `STO`) — 8 lumps

Voice: `HYBRID-GLITCH` — an organic rasp (the Reich body) cut by digital
stutter (the Legion arm). It is the only actor allowed both palettes and the
only one allowed both voices.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDSTOACT` | Spawn (idle) | Low rasping breath and a faint servo tick | **B**: `OGA-CRE1` Breath/Monster + C servo | `OGA-CRE1` PENDING + `SYN`; `FD:DSBGACT` (11 kHz, 1.0 s) |
| `SDSTOSIT` | See | A rasp-snarl chopped by a digital stutter, ~0.7 s | **B**: `OGA-CRE1` Alien/Monster + `HYBRID-GLITCH` | idem; `FD:DSBGSIT1-2` (0.8-0.9 s) |
| `SDSTOMEL` | Melee | A raking blow: metal scrape on flesh, ~0.4 s | **B**: `KEN-IMP` metal scrape + C | `KEN-IMP` PENDING; `FD:DSCLAW` (22 kHz, 0.44 s) |
| `SDSTOMIS` | Missile (bolt launch) | A tearing, rising zap, ~0.5 s. **Different from the Doughboy's and Panzermensch's**: the player's reaction to each projectile differs (`BESTIARY.md` §7) | **C**: swept saw + noise | `SYN` → `KEN-SCI` (contents PENDING) → `FD:DSFIRSHT` (2.0 s, too long) |
| `SDSTOEXP` | Bolt impact | A short crackle, ~0.4 s, **no boom** — a dodgeable bolt, not a rocket | **C** | `SYN` → `KEN-SCI` → `FD:DSFIRXPL` |
| `SDSTOPAI` | Pain | A rasp yelp with one glitch, 0.3 s | **B**: `OGA-CRE1` Hurt + glitch | `OGA-CRE1` PENDING; `FD:DSBGACT`/`DSDMPAIN` |
| `SDSTODTH` | Death | Rasp collapses; a servo whine winds down | **B**: `OGA-CRE1` Monster + C descending whine | idem; `FD:DSBGDTH1-2` (0.8 s) |
| `SDSTOXDT` | XDeath (gib) | Burst plus sparks | **A**: `FD:DSSLOP` + C spark crackle | `FD` + `SYN` |

### 5.4 Reich hound (`SD_ReichHound`, code `HND`) — 5 lumps

Organic, alien, **not a dog and not a wolf** (`BESTIARY.md` §6). The `OGA-CRE1`
"Barking" and "Howl" files are therefore **not used**.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDHNDACT` | Spawn (idle) | Wet, rhythmic panting under a low purr, ~1 s | **B**: `OGA-CRE1` Breath/Monster, slowed | `OGA-CRE1` PENDING; `FD:DSDMACT` (22 kHz, 1.4 s) |
| `SDHNDSIT` | See | **The most important sound in the mod after the shotgun.** A rising snarl-shriek, ≥ 1 s, with an un-animal metallic edge. Spectrally: strong 1-3 kHz and a ~0.3 s attack so it carries through a closed door. How far it is heard is a `SNDINFO` attenuation matter (`mod-engineer`'s); mine is the spectrum | **B+C**: `OGA-SNARL` (attack/snarl 2) + `OGA-CRE2` Alien (+4 semitones) + C metallic FM partial | `OGA-SNARL`, `OGA-CRE2` PENDING + `SYN`; `FD:DSSGTSIT` (22 kHz, 1.1 s) as timing reference |
| `SDHNDATK` | Melee | Jaw snap and wet crunch, ~0.4 s | **B+C**: C click + noise, `KEN-IMP` flesh hit | `KEN-IMP` PENDING; `FD:DSSGTATK` (0.9 s) |
| `SDHNDPAI` | Pain | A short alien yelp, ~0.3 s | **B**: `OGA-CRE2` Monster/Attack, pitched | `OGA-CRE2` PENDING; `FD:DSDMPAIN` (0.86 s) |
| `SDHNDDTH` | Death | A drawn-out rattle that collapses, ~1.2 s | **B**: `OGA-CRE2` Die | `OGA-CRE2` PENDING; `FD:DSSGTDTH` (1.5 s) |

### 5.5 Doughboy (`SD_Doughboy`, code `DGB`) — 7 lumps

A floating pink head in an M1 helmet; grotesque, not funny (D11).
`HELMET-RESONANCE` is the signature: every voice sounds inside a steel bowl.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDDGBACT` | Spawn (idle) | A low hollow drone with a slow wobble, ~1.5 s | **C**: sub drone + resonant ring | `SYN`; `FD:DSDMACT` |
| `SDDGBSIT` | See | A hollow wail, like a voice in a bucket, ~1 s | **B+C**: `OGA-CRE1` Monster + `HELMET-RESONANCE` | `OGA-CRE1` PENDING + `SYN`; `FD:DSCACSIT` (22 kHz, 1.2 s) |
| `SDDGBMEL` | Melee | A bite that clangs on the helmet, ~0.5 s | **B+C**: `KEN-IMP` metal + chomp | `KEN-IMP` PENDING; `FD:DSCLAW` |
| `SDDGBMIS` | Missile (launch) | A wet electric spit, ~0.7 s: **lower, longer and wetter than the Stormtrooper's zap** | **B+C**: `OGA-CRE1` Spit (3) + C zap | `OGA-CRE1` PENDING + `SYN`; `FD:DSFIRSHT` |
| `SDDGBEXP` | Impact | A heavier splat with a flash, ~0.6 s | **C** → `OGA-CRE2` Slime (8) | `SYN` / `OGA-CRE2` PENDING; `FD:DSFIRXPL` |
| `SDDGBPAI` | Pain | A lowered hollow cry, ~0.4 s | **B**: `OGA-CRE1` Hurt, pitched down | `OGA-CRE1` PENDING; `FD:DSDMPAIN` |
| `SDDGBDTH` | Death | **Deflate and sink** (`BESTIARY.md` §7): air escaping with a falling pitch, a soft thud at the end, ~2 s | **C**: pitch-gliding noise + FM → `OGA-CRE2` Slime | `SYN`; `FD:DSCACDTH` (22 kHz, 1.2 s) |

### 5.6 Panzermensch (`SD_Panzermensch`, code `PZR`) — 8 lumps

Slow, plated, low. `PLATE-LOW`. The footstep is the "boss is coming"
telegraph (**H** in the bestiary).

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDPZRACT` | Spawn (idle) | Heavy breath through plate, an armour creak | **B+C**: `OGA-CRE1` Breath + `KEN-IMP` creak | PENDING; `FD:DSKNTSIT`/`DSDMACT` |
| `SDPZRSIT` | See | A low roar ~1.5 s with an armour clank | **B**: `OGA-CRE1`/`CRE2` Roar (3+3), -5 semitones + `KEN-IMP` | PENDING; `FD:DSKNTSIT` (11 kHz, 1.35 s) |
| `SDPZRMEL` | Melee | A slam: fist on flesh and plate, ~0.6 s | **B**: `KEN-IMP` heavy hit + C sub | `KEN-IMP` PENDING; `FD:DSSKEPCH` (not heard) |
| `SDPZRMIS` | Missile (launch) | **Heavier and slower than the Stormtrooper's bolt**: a low lob, ~0.8 s | **C** | `SYN`; `FD:DSFIRSHT` |
| `SDPZREXP` | Impact | A dull heavy boom, ~0.8 s | **C** | `SYN`; `FD:DSFIRXPL` |
| `SDPZRPAI` | Pain | A low grunt, ~0.4 s | **B**: `OGA-CRE2` Grunt (4), -5 semitones | PENDING; `FD:DSKNTDTH` |
| `SDPZRDTH` | Death | A roar sliding into a plate-crash, ~2 s | **B**: `OGA-CRE2` Die + `KEN-IMP` crash | PENDING; `FD:DSBRSDTH` (11 kHz, 1.8 s) |
| `SDPZRSTP` | Footstep (H) | One heavy plated footfall, < 0.5 s, mostly < 300 Hz, **short and dry enough to survive playing every `See` cycle without fatigue**; the engine side can add a `$pitchshift` variation | **C**: 55 Hz decaying sine + click | `SYN`; `KEN-IMP` footstep; `FD:DSMETAL` (11 kHz, 0.73 s) |

### 5.7 The General (`SD_General`, code `GEN`) — 7 lumps

MAP03 only (not in v1). `GENERAL-SLOT`. The General **orders, he does not
brawl** (`BESTIARY.md` §9).

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDGENACT` | Spawn (idle) | A slow, measured mechanism hum with an occasional click; **no voice** | **C** | `SYN` |
| `SDGENSIT` | See | One low calm tone-voice, ~1.5 s, unhurried | **D** + `GENERAL-SLOT` → C | `VOX` / `SYN` |
| `SDGENMIS` | Missile (launch) | One shell of the 3-shot salvo, ~0.6 s; the heaviest launch in the bestiary, bright metal | **C** + `KEN-SCI` | `SYN` / PENDING; `FD:DSRLAUNC` |
| `SDGENEXP` | Impact | A bright metal burst, ~0.7 s | **C** / `KEN-IMP` | `SYN`; `FD:DSFIRXPL` |
| `SDGENSUM` | Summon (the order) | **The one line the player is meant to understand, ≤ 1.2 s, calm, no shout.** Wording: CEO decision C in section 6 | **D** + `GENERAL-SLOT` → C vocoded | `VOX` / `SYN` |
| `SDGENPAI` | Pain | One clipped metallic grunt, not a cry (PainChance 20) | **D** + `GENERAL-SLOT` | `VOX` / `SYN` |
| `SDGENDTH` | Death | **A cue, not an effect** (`BESTIARY.md` §9): the voice winds down into mechanism failure and is allowed to ring, up to ~4 s. Coordinated with the music (the episode stinger belongs to `SOUNDTRACK.md`) | **D** + C mechanism failure | `VOX` / `SYN`; `FD:DSCYBDTH` (22 kHz, 2.5 s) as length reference |

### 5.8 Tally

| Primary route | Lumps | Which |
|---|---|---|
| **D** — CEO voice | 12 | rifleman 4 (ACT, SIT, PAI, DTH), trooper 4 (ACT, SIT, PAI, DTH), General 4 (SIT, SUM, PAI, DTH) |
| **B** — CC0, layered with C | 19 | Stormtrooper 5 (ACT, SIT, MEL, PAI, DTH), hound 5, Doughboy 4 (SIT, MEL, MIS, PAI), Panzermensch 5 (ACT, SIT, MEL, PAI, DTH) |
| **C** — our synthesis | 13 | rifleman ATK; trooper ATK; Stormtrooper MIS, EXP; Doughboy ACT, EXP, DTH; Panzermensch MIS, EXP, STP; General ACT, MIS, EXP |
| **A** — Freedoom edit | 3 | the three gibs |
| **Total** | **47** | |

The exact B/C split of a few rows (Doughboy EXP and DTH) will move when
I hear the packs; the totals by route are the planning figure.

---

## 6. Routes compared, cost and recommendation

Cost is in **agent sessions** (one sound-designer working session) and
**CEO minutes**. All estimates are mine, not measured; the music experience
(two pieces judged "un poco simples", one download set audited, one repair)
suggests assuming one extra iteration round on whatever is new.

| Route | What it gives | What it cannot give | Cost | Rights risk |
|---|---|---|---|---|
| **(a) Freedoom, edited** | All 47 in one scripted pass. Zero downloads, zero licence work beyond the BSD-3 notice. Exact lengths and timing already known | Identity: every Freedoom sound is a Doom-role sound (the 11 kHz imp, the 22 kHz demon). Weak on the Reich/Legion contrast, which is the bestiary's explicit legibility plan. Also unchecked by ear | ~1 session; CEO 20 min | Lowest. Per-sample origin inside Freedoom is only the project's blanket BSD statement |
| **(b) CC0 banks** | Strong creature material (real recorded voice with filters) for 19 rows; good impacts | Nothing faction-specific; no Legion radio, no General. Needs the PM to approve downloads and a per-file provenance table | ~1.5 sessions + a manifest; CEO 30 min to audition | Low-medium: uploader-asserted CC0 on OGA; mitigated by the authors-who-record-themselves choice and by layering |
| **(c) Our synthesis** | Guns, bolts, impacts, explosions, footstep, servo, drones, radio effects: a dry crack is easy to synthesise. Fully reproducible, like `gen_music.py`; no third-party rights at all | Convincing creature voices and any human voice; it would sound synthetic, which fits the Doughboy and the Legion's radio but not the Reich | ~2 sessions (tool + 12 recipes) + 1-2 CEO rounds | None |
| **(d) CEO voice** | The 12 voice rows, with the right accents of intent (dry vs radio vs slot). Faction identity comes cheapest here | The CEO's time. Quality of a phone microphone is fine only after processing, which is the plan | CEO ~45-90 min recording; ~1 session processing | None, once he agrees in writing; his voice is personal data |
| **Recommended mix** | A for 3, B for 19, C for 13, D for 12 (section 5.8) | — | **~3 sessions + one CEO hour + 2 audition rounds** | Lowest practical |

**Why not "Freedoom first", as the preference order suggests.** For the five
most-seen enemies D35 already chose identity over reuse for sprites; sound
should follow, because a player hears the rifleman and the hound long before
reading their sprite. Freedoom stays as (1) the instant fallback — nothing
ever ships silent, (2) the length and timing reference, (3) the base for the
three gibs, where D35 itself allows edited Freedoom for death and gib frames.

**Delivery format (proposal).** Mono OGG at 22.05 kHz, peak at -1 dBFS,
class loudness matched by ear; lump name = file name, dropped into
`src/sounds/<LUMP>.ogg`, one `SNDINFO` line each (`MOD-SPEC.md` §6.2). I
could not reach the ZDoom wiki in this session (two fetches failed), so the
SNDINFO commands for variants, limits and pitch ranges are **NOT VERIFIED
here**: I will not specify them until I can read the wiki. Pure OGG
encoding needs a tool: `ffmpeg` is on this PC (chocolatey) and not known on
the Mac. Alternative: ship 16-bit WAV (≈ 2 MB for 47 one-second sounds), no
encoder at all. Proposal: WAV for the first audition, OGG for the release.

**Where things live.** Candidates and downloads in `work/audio/sfx/`
(gitignored, like the music). Lesson of `SOUNDTRACK.md`: provenance outside
git is stranded provenance. So the **per-file provenance table lives in
this document**, in git, and the synthesis script is reproducible. Licence
cards for shipped files are to be linked from `docs/art/LICENSES.md` or a
sound equivalent (PM/`qa-engineer` audit); BSD-3 text for the three Freedoom
gibs goes there too.

---

## 7. What I need decided

| # | Decision | My recommendation |
|---|---|---|
| **A** | **Approve these downloads** (nothing else): `OGA-CRE1` 1.9 MB, `OGA-CRE2` 1.9 MB, `OGA-SNARL` 0.86 MB (5 OGG), `OGA-100` (size not shown on page), `KEN-IMP` (130 files), `KEN-SCI` (70 files; size not shown on page). Each into its own empty directory, ZIP SHA-256 recorded. Known total ≈ 4.7 MB plus the three with no stated size | Yes, but `KEN-SCI` is optional: its page names no zaps or impacts, so I download it last and drop it if it is all engines |
| **B** | **Do you record your voice?** About 45-90 min with a phone: ~15 short sounds (barks, grunts, a mutter, a collapse), plus the General's order and a low tone. You also confirm in chat that it is released under D15 | **Yes.** It is the only route that is simultaneously free of rights and good for the 12 voice rows. If **no**: those 12 fall back to `OGA-CRE2` Human + processing; I expect the Reich/Legion contrast to be audibly weaker, so we would re-judge after hearing it |
| **C** | **The General's order**, one line (it is what the player hears when the two recruits appear): (1) English "Advance." — calm, my pick; (2) German "Vorwärts." — shows he commands the Reich, but it is the one real German word in the game and conflicts with my section 4 rule; (3) English then a Reich bark from the recruits | (1). If you want (2) or (3), say so explicitly, since it overrides my rule against real German words |
| **D** | **Real-language rule for the Reich** (section 4): invented syllables only, no German words or slogans | Yes |

For the PM, not the CEO: the 47-vs-52 count (section 1); `.gitignore` of
`work/audio/` (open since the music); listing these sources in the sound
licence file once any file ships.

---

## 8. What was verified, and what was not

**Verified 2026-10-13**: `COPYING.adoc` of Freedoom (BSD-style, three
clauses, names not to be used for endorsement); Freedoom's about page and
`sounds/README` and `CREDITS` (no per-sample origin given); the 109 `DS*`
lumps, rates and lengths of `iwads/freedoom2.wad` (read, not extracted);
the pages of `OGA-CRE1`, `OGA-CRE2`, `OGA-SNARL`, `OGA-100`, `KEN-IMP`,
`KEN-SCI`, `kenney.nl/support`, the Sonniss and Pixabay licence summaries,
Freesound's FAQ, the Common Voice datasheet results, the GPL-3 text of
eSpeak NG; that numpy 2.5.4 is in the venv and `ffmpeg` is on this PC; the
bestiary's sound tables and their counts.

**Not verified**: what any Freedoom sound sounds like; the contents of any
ZIP; Kenney pack sizes and formats; Freesound individual sounds; the full
Sonniss licence; the BBC terms; the ZDoom wiki's SNDINFO syntax (fetch
failed); that the OGA authors owned every recording; whether the upstream
`ffmpeg` is on the Mac. Every **PENDING** above clears only at download.

**Engine (D26).** I did not start GZDoom. This is a documentation-only
change: no engine pass is owed for it. The first one will be owed when the
first lumps land.
