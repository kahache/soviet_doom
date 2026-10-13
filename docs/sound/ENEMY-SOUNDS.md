# Enemy sounds — one card per lump, with origin and rights

Living document. Owner: `sound-designer`. Russian mirror:
`docs/ru/sound/ENEMY-SOUNDS.md`, **not yet written** (D34: the mirror is
synced in a batch at the phase close). Created 2026-10-13 (F5, after D35).
Source of the list: `docs/engine/BESTIARY.md` §3-§9 ("States and sounds") and
the naming rule of §2.3; the SNDINFO contract is `docs/engine/MOD-SPEC.md`
§6.2. Music rights live in `docs/sound/MUSIC-RIGHTS.md`; this document owns
**sound-effect and voice rights** only.

> **Status (2026-10-13, after D36): sources downloaded, nothing produced
> or approved, nothing in the PK3.** The five CC0 packs D36 authorised are
> in `work/audio/sfx_sources/` (gitignored) with their provenance in §2.1;
> the voice takes are the CEO's, scripted in `docs/sound/VOICE-SCRIPT.md`.
> The seven actors run on Freedoom stand-ins; every lump below is a
> *replacement* for one of those stand-ins and changes one line of
> `SNDINFO`, no ZScript. Nothing enters `src/sounds/` without the CEO's
> explicit approval, exactly as with textures and music.

---

## 0. The recommendation in six lines

1. **Do not build the 47 lumps from one source.** Split them by what the
   sound physically is: human voices (12), creature sounds (19), mechanical
   and impact sounds (13), gibs (3).
2. **Human voices (12): the CEO's, recorded by him or generated with AI
   (D36), processed by us** (route d). The Reich speaks real German, the
   Legion real English, the General's order is "Vorwärts." The script is
   `docs/sound/VOICE-SCRIPT.md`.
3. **Creature sounds (19): CC0 packs by authors who recorded them
   themselves, layered and processed by us** (route b + c). Two packs by one
   author (rubberduck, own-voice recordings, CC0) plus one snarl pack.
   **Downloaded 2026-10-13** (§2.1).
4. **Gunshots, bolts, impacts, explosions, footstep, drones (13): our own synthesis**
   (route c), reproducible from a script as the music is.
5. **Gibs (3): edited Freedoom `DSSLOP`** (route a, BSD-3), layered with our
   own thump. Freedoom is otherwise the **fallback and the timing reference**,
   not the base: Freedoom's sounds are Doom-role sounds, and the CEO has
   already rejected one Doom-flavoured placeholder (the chainsaw swing).
6. **Decided by the CEO (D36, 2026-10-13):** the downloads (five packs;
   `KEN-SCI` was not part of the authorisation and is not downloaded), the
   voices (his), real German and real English, and the General's order.
   What is still owed by him: the takes and one line releasing them under
   D15 (`VOICE-SCRIPT.md` §0.1).

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

**Resolved 2026-10-13.** `BESTIARY.md` §12 now says 47 ("the sounds never
were 52"). Cross-check the same day: the 47 lump names of this document,
the 47 of `BESTIARY.md` and the 47 targets named in `src/lumps/SNDINFO`'s
comments are the same set, no difference in any direction (**VERIFIED** by
extracting and diffing the three lists).

---

## 2. Source key (every row cites these IDs)

Status words: **VERIFIED** = I read the page or file on 2026-10-13 and the
fact is as stated. **PENDING** = true only after a download, which needs the
PM/CEO. **ASSUMPTION** = I believe it and could not check.

| ID | What | Licence | Status |
|---|---|---|---|
| `FD:DSxxxx` | A lump of Freedoom 0.13.0 (`iwads/freedoom2.wad`, 109 `DS*` lumps) | BSD-3-Clause (project-wide; `COPYING.adoc` read at github.com/freedoom/freedoom) | Lump existence, sample rate and length **VERIFIED** by reading the WAD directory. What it *sounds like*: **NOT VERIFIED, I have not listened.** Per-sample origin: Freedoom's `sounds/README` and `CREDITS` say nothing about it (**VERIFIED**); its site calls the effects original (**VERIFIED**). Accepted under D2. |
| `OGA-CRE1` | rubberduck, *80 CC0 creature SFX*, 2018-07-01. Alien 6, Grunt 5, Hurt 5, Monster 7, Roar 3, Scream 2, Spit 3, Breath 1, Troll 3, Weird 5, Barking 2, others. 1.9 MB ZIP. <https://opengameart.org/content/80-cc0-creature-sfx> | CC0 (page shows CC0 1.0 link). Author states in comments he made most with **his own voice plus filters**. | Page **VERIFIED**. **Downloaded 2026-10-13**: 80 OGG, the page's category counts match the files (§2.1). |
| `OGA-CRE2` | rubberduck, *80 CC0 creature SFX #2*, 2018-08-02. Monster 13, Human 8, Slime 8, Alien 6, Attack 5, Die 4, Grunt 4, Weird 4, Roar 3, Stomp 1, Bug 9. 1.9 MB ZIP. <https://opengameart.org/content/80-cc0-creture-sfx-2> | CC0 | Page **VERIFIED**. **Downloaded 2026-10-13**: 80 OGG, counts match (§2.1). |
| `OGA-SNARL` | Darsycho, *Monster snarls*, 2018-10-17. Five OGG files, 863 KB in all. <https://opengameart.org/content/monster-snarls> | CC0 (credit "appreciated", not required) | Page **VERIFIED**. **Downloaded 2026-10-13**: the page offers five separate OGG files, no ZIP; all five taken (§2.1). |
| `OGA-100` | rubberduck, *100 CC0 SFX*, 2018-06-29: Metal 12, Slam 7, Hit 4, Shot 2, Machine loop 3, Weird 5, Explosion 1, Switch 2 ... <https://opengameart.org/content/100-cc0-sfx> | CC0 | Page **VERIFIED**. **Downloaded 2026-10-13**: 100 OGG, counts match; every file decodes cleanly (the commenter's error report did not reproduce) (§2.1). |
| `KEN-IMP` | Kenney, *Impact Sounds*, 130 files, tags impact + foley. <https://kenney.nl/assets/impact-sounds> | CC0 (page shows "Creative Commons CC0"); `kenney.nl/support`: all assets on the asset pages are CC0, no attribution required | Page **VERIFIED**. **Downloaded 2026-10-13**: 130 OGG plus `License.txt` (CC0) (§2.1). |
| `KEN-SCI` | Kenney, *Sci-fi Sounds*, 70 files, tags sci-fi, space, engine. <https://kenney.nl/assets/sci-fi-sounds> | CC0 | Page **VERIFIED**. **Not authorised by D36 and not downloaded.** Every row that named it falls back to `SYN`. |
| `FS-CC0` | Freesound, filter "Creative Commons 0", per-sound | CC0 *per sound*; the uploader asserts it, Freesound does not guarantee it (its FAQ says users may upload illegal content, **VERIFIED**). **Downloading requires a logged-in account** (**VERIFIED**). | **Not planned.** Kept as a gap-filler for one sound at a time, each with its own page check. A search listed hundreds of CC0 growls (**VERIFIED**: the listing exists); I have not opened any individual sound page. |
| `SYN` | Our own synthesis: a script `gen_sfx.py` (numpy; the project venv already has numpy 2.5.4, **VERIFIED**), deterministic seeds, output WAV then OGG | GPL-3.0 for the script, CC BY-NC-SA 4.0 for the output (D15) | To be written. |
| `VOX` | The CEO's voice, recorded by him, or AI voices he generates (D36); processed by us. Script: `docs/sound/VOICE-SCRIPT.md` | Recorded: his own work; he applies CC BY-NC-SA 4.0 (D15). A recognisable voice is personal data, so the line "released under D15" must come from him in writing (the chat is enough). AI: per file, tool, version, date, account plan, licence of use (URL and literal clause), voice and prompt, logged as in `VOICE-SCRIPT.md` §0.7; usable only if those terms allow redistribution inside a CC BY-NC-SA 4.0 package | **Decided (D36).** Takes not yet delivered. |

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

### 2.1 Downloads and provenance (D36, 2026-10-13)

Authorised by D36: exactly `OGA-CRE1`, `OGA-CRE2`, `OGA-SNARL`, `OGA-100`
and `KEN-IMP`. **`KEN-SCI` was not authorised and was not downloaded.**
Nothing else was fetched. Each pack sits in its own directory under
`work/audio/sfx_sources/<pack>/` (gitignored through `work/`), the archive
as downloaded plus an `extracted/` copy. No link asked for an account, a
captcha or the acceptance of terms; Kenney's page shows a donation
dialog whose "Continue without donating..." link is the direct file URL
below. Retrieved with `curl` on 2026-10-13; SHA-256 computed with
`sha256sum` on the file as saved; sizes in bytes. Every size equals the
`length=` the page itself declares for that file (Kenney's page declares
none).

| Pack | Saved as | File URL (from the page in §2) | Bytes | SHA-256 | Licence as shown on the page | Literal licence line(s) |
|---|---|---|---|---|---|---|
| `OGA-CRE1` | `oga-cre1/80-CC0-creature-SFX_0.zip` | <https://opengameart.org/sites/default/files/80-CC0-creature-SFX_0.zip> | 1 885 648 | `5d4002eea42f278e76543bb36e8ddd2cb978588a13271984191d8228f5d26768` | CC0 | Page: "License(s): CC0" |
| `OGA-CRE2` | `oga-cre2/80-CC0-creature-sfx-2.zip` | <https://opengameart.org/sites/default/files/80-CC0-creature-sfx-2.zip> | 1 890 174 | `6d251aeaaaa9c2fffed8fc2f64bab3104725ceabf9259a8441994e7a20cfe22f` | CC0 | Page: "License(s): CC0" |
| `OGA-SNARL` | `oga-snarl/monster-snarl-5.ogg` | <https://opengameart.org/sites/default/files/monster-snarl-5.ogg> | 201 559 | `aeaf9ab0f25cb8b035a3257913206afd8ba33d47876106291d38dfac7e5c07aa` | CC0 | Page: "License(s): CC0"; "Copyright/Attribution Notice: Feel free to use for whatever, credit is appreciated!" |
| `OGA-SNARL` | `oga-snarl/monster-snarl-attack.ogg` | <https://opengameart.org/sites/default/files/monster-snarl-attack.ogg> | 185 872 | `34bf1ceef265725abf00ab3263bbbb492792e126bb1619addd4a5d3ad123347f` | CC0 | idem |
| `OGA-SNARL` | `oga-snarl/monster-snarls-2_0.ogg` | <https://opengameart.org/sites/default/files/monster-snarls-2_0.ogg> | 75 510 | `dbc7b5e621892b5dbc27ee25230b57daaddbc83daadfb20131988b7367f967e1` | CC0 | idem |
| `OGA-SNARL` | `oga-snarl/monster-snarls_0.ogg` | <https://opengameart.org/sites/default/files/monster-snarls_0.ogg> | 195 986 | `7401193d0cc5eb193379cf326c8868d6823a284ebc32ffaa298c1a94d2e25994` | CC0 | idem |
| `OGA-SNARL` | `oga-snarl/monsters-snarls-3_0.ogg` | <https://opengameart.org/sites/default/files/monsters-snarls-3_0.ogg> | 203 942 | `5917d2697b8688b2c59e592d448d473ae0eeaed83802541ebd19bc87f97fe8a7` | CC0 | idem |
| `OGA-100` | `oga-100/100-CC0-SFX_0.zip` | <https://opengameart.org/sites/default/files/100-CC0-SFX_0.zip> | 2 921 904 | `a5c135878c132f1c59cca54e60061c296cd0ac27ad031ca2c41b8cd5cab3c706` | CC0 | Page: "License(s): CC0" |
| `KEN-IMP` | `ken-imp/kenney_impact-sounds.zip` | <https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip> | 800 850 | `029d734af1582474edf3a694d1b0cebc97c1c152f2f39fa34d4c2bafc5de77f8` | Creative Commons CC0 | Page, details table: "License" / "Creative Commons CC0"; page meta description: "Download this package (130 assets) for free, CC0 licensed!". Inside the ZIP, `License.txt`: "License: (Creative Commons Zero, CC0)" and "Support us by crediting Kenney or www.kenney.nl (this is not mandatory)" |

`OGA-SNARL` has no ZIP: its page offers the five OGG files one by one, so
each file carries its own hash. Its total is 862 869 bytes, the page's
"863 KB".

**What the packs contain, checked against what the pages promised.**
Archives opened with Python's `zipfile` (run isolated), no entry with an
absolute path or `..`, `testzip()` clean on all four; every one of the 395
OGG files decoded with `ffmpeg` without a single error.

| Pack | Files | Matches the page? | Format | Embedded tags |
|---|---|---|---|---|
| `OGA-CRE1` | 80 OGG, nothing else | **Yes.** Alien 6, Grunt 5, Hurt 5, Monster 7, Roar 3, Scream 2, Spit 3, Breath 1, Troll 3, Weird 5, Barking 2, as listed; also Bug 4, Burble 2, Burp 2, Cough 3, Cute 10, Eat 4, Howl 1, Misc 9, Nose 1, Ooh 1, Snore 1 | 48 kHz stereo | `ARTIST=rubberduck` |
| `OGA-CRE2` | 80 OGG | **Yes.** Monster 13, Human 8, Slime 8, Alien 6, Attack 5, Die 4, Grunt 4, Weird 4, Roar 3, Stomp 1, Bug 9, as listed; also Breath 1, Misc 13, Snore 1 | 74 at 48 kHz, 6 at 44.1 kHz, stereo | `ARTIST=rubberduck` |
| `OGA-SNARL` | 5 OGG | **Yes**, five snarls | 44.1 kHz stereo | none |
| `OGA-100` | 100 OGG | **Yes.** Metal 12, Slam 7, Hit 4, Shot 2, Machine 3, Weird 5, Explosion 1, Switch 2, as listed, plus household foley (doors, dishes, glass, springs, tools...) | 48 kHz stereo | `ARTIST=rubberduck` |
| `KEN-IMP` | 130 OGG in `Audio/`, `License.txt`, two `.url` shortcuts (kenney.nl, Patreon) | **Yes**, 130 files: 21 sets of 5 impacts (metal, plate, punch, soft, wood, glass, tin, bell, mining, plank, generic) and 5 sets of 5 footsteps (carpet, concrete, grass, snow, wood) | 44.1 kHz stereo | `ARTIST=Kenney`, `COMMENTS=Sound generated by GameSynth from Tsugi (www.tsugi-studio.com)` |

Two facts the pages did not say, neither a reason to stop:

- **`KEN-IMP` is procedural.** Every file's comment tag says it was made
  with GameSynth, a commercial sound-synthesis tool. The licence in the ZIP
  is Kenney's CC0 on his output; the tool's own terms on generated sounds
  were **NOT VERIFIED**. I record it because a reviewer will ask; it is the
  same position as music written in a commercial DAW.
- **`KEN-IMP` has no "scrape" or "creak".** The cards that named a
  "metal scrape" (`SDSTOMEL`) or an "armour creak" (`SDPZRACT`) will be built
  from `impactMetal`/`impactPlate` hits plus `SYN`, not a ready file.

Per-file provenance (which inner file ends up in which lump) is added to the
cards in §5 when a lump is produced, citing the pack row above.

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

## 4. Voice approach (D11, D12, D36)

D11 asks for a serious tone; D12 allows the symbols and says the invaders do
not trivialise real victims. Audio is where that line is easiest to cross by
accident. **D36 (CEO, 2026-10-13) set the language rule**: "prefiero que sea
alemán real e inglés real". My earlier proposal of invented German-sounding
syllables is **withdrawn**. The rules for voices are now:

- **Who records.** The CEO, in his own voice or generated with AI (D36).
  The script, recording instructions and AI log are
  `docs/sound/VOICE-SCRIPT.md`. A recorded take is used only after his
  written line releasing it under D15 (his voice is personal data); an AI
  take only with its tool, version, licence of use and prompt logged, and
  only if those terms allow redistribution inside a CC BY-NC-SA 4.0 package.
- **The Reich speaks real German**: short military orders and combat
  callouts any army would use ("Feind!", "Stellung halten."). Dry, clipped,
  flat; soldiers, not film villains.
- **The Legion speaks real English** through a radio and a vocoder
  (`BESTIARY.md` §4): radio procedure and callouts ("Contact!", "Sector
  four, clear."), processed, clipped, with squelch. **No accent
  caricature** on either side: a cartoon Texan or a cartoon German would
  break D11 at once.
- **What is never said (D11, D12, D36):** no slogan, salute, Party title,
  song or watchword of the regime; no word tied to round-ups, deportations
  or camps, even the film clichés ("Raus!", "Schnell!" shouted at people);
  on the Legion side, symmetrically, no patriotic slogans. Callouts only.
- **The General** is the Legion's officer commanding both factions
  (`BESTIARY.md` §9). He speaks English, calmly, and gives the Reich
  recruits their order in German: **"Vorwärts."** (D36), the one line the
  player is meant to catch. He is "tall and unhurried" with "a smooth chrome
  plate with a single slot" for a face: a low, calm, narrow-band voice that
  sounds as if it leaves through the slot. He does not shout.
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

Voice: `REICH-DRY`, real German (D36); lines in `VOICE-SCRIPT.md` §1.1.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDRRIACT` | Spawn (idle) | A muttered German order ("Stellung halten."), low; heard through doors | **D** → C formant babble → `FD:DSPOSACT` (22 kHz, 1.4 s) | `VOX`; fallback `SYN`/`FD` |
| `SDRRISIT` | See | A short bark, ≤ 0.5 s, heard many times per map: must not tire | **D** → `OGA-CRE1` Grunt → `FD:DSPOSIT1-3` (0.85-1.4 s) | `VOX`; `OGA-CRE1` PENDING |
| `SDRRIATK` | Missile | **Dry bolt-action crack, drier and higher than the player's TT-33**, plus a bolt click; no tail. Incoming must not sound like outgoing | **C**: noise burst, ~8 ms attack, ~120 ms decay, band-pass 1-5 kHz, bolt-throw click → `OGA-100` Shot (2) | `SYN`. **Not `FD:DSPISTOL`**: it is the TT-33's own placeholder (`SNDINFO`), which would defeat the brief |
| `SDRRIPAI` | Pain | A cut-off grunt, 0.2-0.3 s | **D** → `OGA-CRE1` Hurt (5) → `FD:DSPOPAIN` (11 kHz, 0.4 s) | `VOX` / `OGA-CRE1` PENDING |
| `SDRRIDTH` | Death | An exhale that breaks into a collapse, ~1 s; no scream | **D** → `OGA-CRE2` Die (4) → `FD:DSPODTH1-3` | `VOX` / `OGA-CRE2` PENDING |
| `SDRRIXDT` | XDeath (gib) | A wet burst, no voice | **A**: `FD:DSSLOP` (22 kHz, 1.1 s) + our low thump | `FD` BSD-3 (notice required in `LICENSES` if shipped) + `SYN` |

### 5.2 Liberty Legion trooper (`SD_LegionTrooper`, code `LTR`) — 6 lumps

Voice: `LEGION-RADIO`, real English (D36); lines in `VOICE-SCRIPT.md` §1.2.
Brief from §4: processed and clipped; the player names
the faction by ear.

| Lump | State | Must convey | Origin | Source / status |
|---|---|---|---|---|
| `SDLTRACT` | Spawn (idle) | Radio chatter: squelch opens, a routine English report ("Sector four, clear."), squelch closes | **D** (mumble) + chain → C (noise + vocoded formant) | `VOX` / `SYN` |
| `SDLTRSIT` | See | One clipped callout ("Contact!") and a squelch tail, ≤ 0.6 s | **D** + chain → C vocoded syllable | idem |
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
| `SDSTOMIS` | Missile (bolt launch) | A tearing, rising zap, ~0.5 s. **Different from the Doughboy's and Panzermensch's**: the player's reaction to each projectile differs (`BESTIARY.md` §7) | **C**: swept saw + noise | `SYN` → `FD:DSFIRSHT` (2.0 s, too long). `KEN-SCI` dropped: not authorised (D36) |
| `SDSTOEXP` | Bolt impact | A short crackle, ~0.4 s, **no boom** — a dodgeable bolt, not a rocket | **C** | `SYN` → `FD:DSFIRXPL` |
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
| `SDGENSIT` | See | One calm English word ("Engage."), ~1.5 s, unhurried | **D** + `GENERAL-SLOT` → C | `VOX` / `SYN` |
| `SDGENMIS` | Missile (launch) | One shell of the 3-shot salvo, ~0.6 s; the heaviest launch in the bestiary, bright metal | **C** + `KEN-IMP` metal | `SYN`; `FD:DSRLAUNC`. `KEN-SCI` dropped (D36) |
| `SDGENEXP` | Impact | A bright metal burst, ~0.7 s | **C** / `KEN-IMP` | `SYN`; `FD:DSFIRXPL` |
| `SDGENSUM` | Summon (the order) | **The one line the player is meant to understand, ≤ 1.2 s, calm, no shout.** Wording, decided by the CEO (D36): **"Vorwärts."**, German, to the Reich recruits | **D** + `GENERAL-SLOT` → C vocoded | `VOX` / `SYN` |
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

**Where things live.** Downloads in `work/audio/sfx_sources/<pack>/`, the
CEO's voice takes in `work/audio/voice_takes/` (both gitignored through
`work/`, like the music). Lesson of `SOUNDTRACK.md`: provenance outside
git is stranded provenance. So the **per-file provenance table lives in
this document**, in git, and the synthesis script is reproducible. Licence
cards for shipped files are to be linked from `docs/art/LICENSES.md` or a
sound equivalent (PM/`qa-engineer` audit); BSD-3 text for the three Freedoom
gibs goes there too.

---

## 7. Decisions — taken by the CEO in D36 (2026-10-13)

| # | Question as asked | Decision (D36) |
|---|---|---|
| **A** | Approve the downloads | **Approved**: `OGA-CRE1`, `OGA-CRE2`, `OGA-SNARL`, `OGA-100`, `KEN-IMP`. `KEN-SCI`, which I had marked optional, was **not** asked and is **not** authorised. Done on 2026-10-13, §2.1 |
| **B** | Does the CEO record his voice? | **Yes, or he generates it with AI** ("me encargaré de las grabaciones y/o generar con IA lo que sea necesario"). Script: `docs/sound/VOICE-SCRIPT.md`. An AI take carries its tool and licence in the licence register |
| **C** | The General's order | **"Vorwärts."** |
| **D** | Real-language rule for the Reich | **Overruled.** Real German for the Reich, real English for the Legion; still no slogans of the regime (D11, D12). §4 rewritten |

Still owed by the CEO: the takes, and one line in chat releasing his
recorded voice under D15 (`VOICE-SCRIPT.md` §0.1).

For the PM, not the CEO: `src/lumps/LANGUAGE` still prints the placeholder
order "The General: Recruits - advance!" (EN, and its RU twin) and
`BESTIARY.md` §3 still briefs `SDRRIACT` as "a language that is not quite
German"; both are `mod-engineer`'s files and both predate D36. Listing
these sources in the sound licence file once any file ships.

---

## 8. What was verified, and what was not

**Verified 2026-10-13**: `COPYING.adoc` of Freedoom (BSD-style, three
clauses, names not to be used for endorsement); Freedoom's about page and
`sounds/README` and `CREDITS` (no per-sample origin given); the 109 `DS*`
lumps, rates and lengths of `iwads/freedoom2.wad` (read, not extracted);
the pages of `OGA-CRE1`, `OGA-CRE2`, `OGA-SNARL`, `OGA-100`, `KEN-IMP`,
`KEN-SCI`, `kenney.nl/support`, and (after D36) the downloaded files of the
five authorised packs: sizes, SHA-256, licence lines, contents against the
pages, a clean decode of all 395 OGG files (§2.1); the 47 lump names
against `BESTIARY.md` and `SNDINFO` (§1); the Sonniss and Pixabay licence summaries,
Freesound's FAQ, the Common Voice datasheet results, the GPL-3 text of
eSpeak NG; that numpy 2.5.4 is in the venv and `ffmpeg` is on this PC; the
bestiary's sound tables and their counts.

**Not verified**: what any Freedoom sound or any downloaded file sounds
like (nothing has been auditioned yet); GameSynth's terms on generated
sounds (`KEN-IMP`, §2.1); the terms of any AI voice tool; Freesound individual sounds; the full
Sonniss licence; the BBC terms; the ZDoom wiki's SNDINFO syntax (fetch
failed); that the OGA authors owned every recording; whether the upstream
`ffmpeg` is on the Mac. In the cards of §5, **PENDING** next to a pack now
means "downloaded, not yet auditioned".

**Engine (D26).** I did not start GZDoom. This is a documentation-only
change (plus gitignored downloads): no engine pass is owed for it. The first one will be owed when the
first lumps land.
