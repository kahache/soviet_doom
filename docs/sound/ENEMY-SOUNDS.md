# Enemy sounds — one card per lump, with origin and rights

Living document. Owner: `sound-designer`. Russian mirror:
owed at phase close (D34, batch sync; the mirror of
`VOICE-SCRIPT.md` already exists). Created 2026-10-13 (F5, after D35).
Source of the list: `docs/engine/BESTIARY.md` §3-§9 ("States and sounds") and
the naming rule of §2.3; the SNDINFO contract is `docs/engine/MOD-SPEC.md`
§6.2. Music rights live in `docs/sound/MUSIC-RIGHTS.md`; this document owns
**sound-effect and voice rights** only.

> **Status (2026-10-20): INSTALLED (N9e, §5.12)** the 30 sounds and 5 beds
> the CEO approved in D83, the takes of D86, the seven voice takes of D91
> and the seventeen of D96: 81 lumps in `assets/sounds/enemies/`. Eight of
> the twelve voices are ours (the rifleman's idle, sight and death; the
> trooper's idle, sight and pain; the General's sight and his order); the
> rifleman's pain, the trooper's death and the General's pain and death
> keep Freedoom's (no take approved), and the beds wait, packed, to be
> mixed under their voices. What follows is the history.
>
> **Status (2026-10-13, evening): the 35 non-voice lumps are DRAFTED, plus
> eight beds for the voices; nothing approved, nothing in the PK3.** The
> generator is `tools/audio/gen_sfx.py` (tests: `tests/test_gen_sfx.py`); the
> drafts sit in `work/audio/sfx/enemies/` (gitignored) and in an audition
> overlay, `work/audio/sfx/sd-enemy-sfx-draft.pk3`; the CEO listens to them in
> `docs/art/previews/2026-10-13_2029_F5_enemy-sfx-drafts.html`, one page, every
> file embedded, with its card, its numbers and its sources (§5.9). **Nobody
> has listened to them yet**, the sound-designer included: every check so far
> is an instrument (§5.9). The twelve voices are the CEO's and **postponed by
> the CEO (D37)**; until they come the rifleman, the trooper and the General keep
> Freedoom's voices. The five CC0 packs D36 authorised are in
> `work/audio/sfx_sources/` with their provenance in §2.1. Every lump below
> is a *replacement* for a Freedoom stand-in and changes one line of
> `SNDINFO`, no ZScript. Nothing enters `src/sounds/` without the CEO's
> explicit approval, exactly as with textures and music.

---

## 0. The recommendation in six lines

1. **Do not build the 47 lumps from one source.** Split them by what the
   sound physically is: human voices (12), creature sounds (19), mechanical
   and impact sounds (13), gibs (3).
2. **Human voices (12): the CEO's, recorded in person or generated with AI
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
   voices (the CEO's), real German and real English, and the General's order.
   What is still owed by the CEO: the takes and one line releasing them under
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
| `SYN` | Our own synthesis: a script `gen_sfx.py` (numpy; the project venv already has numpy 2.5.4, **VERIFIED**), deterministic seeds, output WAV then OGG | GPL-3.0 for the script, CC BY-NC-SA 4.0 for the output (D15) | **Written 2026-10-13**: `tools/audio/gen_sfx.py`, deterministic (seed 1977, two full runs byte-identical); tests `tests/test_gen_sfx.py`. |
| `VOX` | The CEO's voice, recorded in person, or AI voices the CEO generates (D36); processed by us. Script: `docs/sound/VOICE-SCRIPT.md` | Recorded: the CEO's own work, to which the CEO applies CC BY-NC-SA 4.0 (D15). A recognisable voice is personal data, so the line "released under D15" must come from the CEO in writing (the chat is enough). AI: per file, tool, version, date, account plan, licence of use (URL and literal clause), voice and prompt, logged as in `VOICE-SCRIPT.md` §0.7; usable only if those terms allow redistribution inside a CC BY-NC-SA 4.0 package | **Decided (D36).** Takes not yet delivered. |

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

Per-file provenance (which inner file ends up in which lump) is §5.9,
written from what the generator recorded, citing the pack rows above.

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

- **Who records.** The CEO, recording in person or generating with AI (D36).
  The script, recording instructions and AI log are
  `docs/sound/VOICE-SCRIPT.md`. A recorded take is used only after the CEO's
  written line releasing it under D15 (a voice is personal data); an AI
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
I hear the packs; the totals by route are the planning figure. **As
drafted (§5.9):** `SDDGBEXP` moved to C+B (an `OGA-CRE2` slime layer), and
`SDGENMIS` and `SDGENEXP` are C+B (one `KEN-IMP` metal hit each, as their
cards say); `SDDGBDTH` stayed pure C.

### 5.9 The drafts of 2026-10-13: what was built, from what

Built by `tools/audio/gen_sfx.py`, seed 1977, mono 44.1 kHz, 16-bit WAV
master and Vorbis OGG (q6), into `work/audio/sfx/enemies/` (gitignored).
Listening page: `docs/art/previews/2026-10-13_2029_F5_enemy-sfx-drafts.html`.
The generator also writes `PROVENANCE.tsv` and `REPORT.txt` next to the
drafts; this section is their copy in git (lesson of `SOUNDTRACK.md`:
provenance outside git is stranded provenance).

**How a draft is made.** Every `B` row cuts, re-pitches and filters its pack
files and always adds a layer of our own synthesis (a servo, a purr, an FM
throat, a thump; `tests/test_gen_sfx.py` holds every B row to having one),
so no CC0 clip ships unlayered (§2). Every file is then brought to a class
loudness (fire and impacts -13, creatures and gibs -15, the step -17, idles
-20, beds -18 dB, a gated K-shaped RMS that is **not** a certified LUFS
meter) and held under -1 dBFS by a look-ahead limiter. No WAV and no decoded
OGG clips (measured on every file; Vorbis overshoots the -1 dBFS ceiling a
little, and the highest decoded OGG peak is `SDLTRACT-bed`'s, -0.4 dBFS).

**The cards as numbers.** What the cards say in words is measured and held
by the tests: the Panzermensch step is 0.35 s with 97 % of its energy under
300 Hz; the Stormtrooper's bolt impact has no energy under 150 Hz (no boom)
while the Panzermensch's shell has 91 %; the three launches are ordered as
§5.3, §5.5 and §5.6 ask, brightest and shortest to dullest and longest
(spectral centroid Stormtrooper 1.5 kHz, Doughboy 1.3 kHz, Panzermensch
0.34 kHz; 0.50, 0.65, 0.80 s); the rifleman's crack starts in under 10 ms
with a 3.4 kHz centroid, brighter than the Legion's blast; the hound's sight
lasts 1.35 s, puts 46 % of its energy in 1-3 kHz and reaches -6 dB of its
peak at 0.20 s; the Doughboy's death ends on its loudest moment, the thud;
the Legion's radio beds have under 1 % of their energy below 300 Hz.
**Instruments, not ears:** a draft can pass all of this and still be wrong.

**Changes made against the first cut, from the measures.** The
Stormtrooper's sight was 83 % under 300 Hz (a growl, not the rasp the card
asks for): high-passed and given presence at 2.6 kHz, now 34 %. Its death
the same treatment. The hound's sight took 0.5 s to reach full level: the
snarl now starts 0.3 s later in the source and the 1-3 kHz band went from
31 % to 46 %. The Panzermensch's pain started on a slow ramp: cut to its
onset. His death used the same `die_03` as the hound's: now `die_04`. The
Doughboy's idle drone (55 Hz) does not exist on a laptop speaker: its 410 Hz
helmet ring went up 7 dB. The Panzermensch step's heel and clink went up
6-7 dB for the same reason. Eight B rows that were only *processed* (filters,
reverb, stutter) got a synthesised layer.

| File | Route | Layers read (the rest is `SYN`) |
|---|---|---|
| `SDRRIATK` | C | none: synthesis only |
| `SDRRIXDT` | A+C | `FD` `freedoom2.wad:DSSLOP` |
| `SDLTRATK` | C | none: synthesis only |
| `SDLTRXDT` | A+C | `FD` `freedoom2.wad:DSSLOP` |
| `SDSTOACT` | B+C | `OGA-CRE1` `breath.ogg`; `OGA-CRE2` `breath_02.ogg` |
| `SDSTOSIT` | B+C | `OGA-CRE1` `monster_06.ogg`; `OGA-CRE1` `alien_03.ogg` |
| `SDSTOMEL` | B+C | `KEN-IMP` `impactPunch_medium_001.ogg`; `KEN-IMP` `impactMetal_light_002.ogg` |
| `SDSTOMIS` | C | none: synthesis only |
| `SDSTOEXP` | C | none: synthesis only |
| `SDSTOPAI` | B+C | `OGA-CRE1` `hurt_02.ogg` |
| `SDSTODTH` | B+C | `OGA-CRE1` `monster_07.ogg` |
| `SDSTOXDT` | A+C | `FD` `freedoom2.wad:DSSLOP` |
| `SDHNDACT` | B+C | `OGA-CRE2` `breath_02.ogg`; `OGA-CRE1` `breath.ogg` |
| `SDHNDSIT` | B+C | `OGA-SNARL` `monster-snarl-attack.ogg` [12.85-13.95 s]; `OGA-CRE2` `alien_07.ogg` |
| `SDHNDATK` | B+C | `KEN-IMP` `impactPunch_heavy_002.ogg`; `OGA-CRE1` `eat_02.ogg` |
| `SDHNDPAI` | B+C | `OGA-CRE2` `monster_10.ogg` |
| `SDHNDDTH` | B+C | `OGA-CRE2` `die_03.ogg`; `OGA-CRE2` `die_02.ogg` |
| `SDDGBACT` | C | none: synthesis only |
| `SDDGBSIT` | B+C | `OGA-CRE1` `scream_02.ogg`; `OGA-CRE1` `monster_03.ogg` |
| `SDDGBMEL` | B+C | `OGA-CRE1` `eat_02.ogg`; `KEN-IMP` `impactMetal_heavy_001.ogg` |
| `SDDGBMIS` | B+C | `OGA-CRE1` `spit_02.ogg` |
| `SDDGBEXP` | C+B | `OGA-CRE2` `slime_07.ogg` |
| `SDDGBPAI` | B+C | `OGA-CRE1` `hurt_05.ogg` |
| `SDDGBDTH` | C | none: synthesis only |
| `SDPZRACT` | B+C | `OGA-CRE1` `breath.ogg`; `OGA-CRE2` `breath_02.ogg`; `KEN-IMP` `impactPlate_light_001.ogg` |
| `SDPZRSIT` | B+C | `OGA-CRE2` `roar_05.ogg`; `OGA-CRE1` `roar_02.ogg`; `KEN-IMP` `impactPlate_heavy_001.ogg`; `KEN-IMP` `impactMetal_heavy_003.ogg` |
| `SDPZRMEL` | B+C | `KEN-IMP` `impactPunch_heavy_000.ogg`; `KEN-IMP` `impactPlate_heavy_003.ogg` |
| `SDPZRMIS` | C | none: synthesis only |
| `SDPZREXP` | C | none: synthesis only |
| `SDPZRPAI` | B+C | `OGA-CRE2` `grunt_09.ogg` |
| `SDPZRDTH` | B+C | `OGA-CRE2` `die_04.ogg`; `OGA-CRE2` `roar_04.ogg`; `KEN-IMP` `impactPlate_heavy_004.ogg`; `KEN-IMP` `impactMetal_heavy_001.ogg`; `KEN-IMP` `impactPunch_heavy_002.ogg`; `KEN-IMP` `impactPlate_heavy_002.ogg` |
| `SDPZRSTP` | C | none: synthesis only |
| `SDGENACT` | C | none: synthesis only |
| `SDGENMIS` | C+B | `KEN-IMP` `impactMetal_heavy_001.ogg` |
| `SDGENEXP` | C+B | `KEN-IMP` `impactPlate_heavy_000.ogg` |
| `SDRRIPAI-bed` | C | none: synthesis only |
| `SDRRIDTH-bed` | C+B | `KEN-IMP` `impactWood_light_002.ogg`; `KEN-IMP` `impactMetal_light_000.ogg`; `KEN-IMP` `impactTin_medium_001.ogg` |
| `SDLTRACT-bed` | C | none: synthesis only |
| `SDLTRSIT-bed` | C | none: synthesis only |
| `SDLTRPAI-bed` | C | none: synthesis only |
| `SDLTRDTH-bed` | C | none: synthesis only |
| `SDGENPAI-bed` | C+B | `KEN-IMP` `impactPlate_medium_002.ogg` |
| `SDGENDTH-bed` | C+B | `KEN-IMP` `impactPlate_heavy_002.ogg`; `KEN-IMP` `impactMetal_heavy_004.ogg` |

Tally: 10 lumps and 5 beds are synthesis only; 22 lumps and 3 beds layer a
CC0 pack; the three gibs edit Freedoom's `DSSLOP`. **40 distinct source
files**, each hashed as it sits on disk (the pack archives' own hashes are
§2.1; `monster-snarl-attack.ogg` matches its §2.1 row, which checks the
chain). `OGA-100` is authorised but not used.

| Pack | File | SHA-256 of the file as on disk | Used by |
|---|---|---|---|
| `FD` | `freedoom2.wad:DSSLOP` (the lump's bytes) | `1c184efa6d51561261720b267a1a4e7ad2f227314a2fe11e565edd0c44e36c6a` | SDRRIXDT, SDLTRXDT, SDSTOXDT |
| `KEN-IMP` | `impactMetal_heavy_001.ogg` | `83554049f81f4db9209379e103c30bfa63f65c42189a03f300b045c2c82e23ae` | SDDGBMEL, SDPZRDTH, SDGENMIS |
| `KEN-IMP` | `impactMetal_heavy_003.ogg` | `b0f2ba4dabde9a87eb9c188a19d31e0c2300fd321adeba08d3b9b8aa011d7037` | SDPZRSIT |
| `KEN-IMP` | `impactMetal_heavy_004.ogg` | `6d65b463c0555dd5be16b8db6d2cbe23a94e07a4637779b8ad17d0db3e500a87` | SDGENDTH-bed |
| `KEN-IMP` | `impactMetal_light_000.ogg` | `33b5e6e37c6e9d54e07bf5a89b12c76e879f40c1ea83cdd82714df1d6f9fec6d` | SDRRIDTH-bed |
| `KEN-IMP` | `impactMetal_light_002.ogg` | `25a96f90a9a1f88a531e824e126f0519504625e5635e65a72e4f31611428db29` | SDSTOMEL |
| `KEN-IMP` | `impactPlate_heavy_000.ogg` | `112d4f93ddcc370b410630f971c0f5d991856102da9c76bc5c5540d388e75aaa` | SDGENEXP |
| `KEN-IMP` | `impactPlate_heavy_001.ogg` | `142fd6c77f13d25f318265901163f70f8dfe12f87829169a570025be43de7011` | SDPZRSIT |
| `KEN-IMP` | `impactPlate_heavy_002.ogg` | `b0cab75d1befa32b4cf215d8ee7e1c400a39182e8b105963b8e310f825b198a1` | SDPZRDTH, SDGENDTH-bed |
| `KEN-IMP` | `impactPlate_heavy_003.ogg` | `59775f8979a396c8a793b0a1db206d5bdc651eae808d858e9acaee8ebda5bc6d` | SDPZRMEL |
| `KEN-IMP` | `impactPlate_heavy_004.ogg` | `e31bfec90630155bcc6af541d1d14ae8202c435c52b42e6b6183fdb6ffb248b0` | SDPZRDTH |
| `KEN-IMP` | `impactPlate_light_001.ogg` | `947915c2eb6ac57ee08fd3a48b297fd108d69abc72076e79882c21cad0eef56e` | SDPZRACT |
| `KEN-IMP` | `impactPlate_medium_002.ogg` | `68762e1ed49bb59ae6602fad6ce2ebac61958478ddb2668de9106f010cd4b6b0` | SDGENPAI-bed |
| `KEN-IMP` | `impactPunch_heavy_000.ogg` | `b33a8f14068aec24ec69ba85e5e87fdc41228975f6a1a3e44a6e7d6fc3d9f8d8` | SDPZRMEL |
| `KEN-IMP` | `impactPunch_heavy_002.ogg` | `7993dd4c156b9979ad69f17be5ebe31850b16039a3857f8477141be54dfee1b3` | SDHNDATK, SDPZRDTH |
| `KEN-IMP` | `impactPunch_medium_001.ogg` | `e71d23abcc3f10d9d6bc9615b2a431fff70b12333a5fcdd9964457564ace4349` | SDSTOMEL |
| `KEN-IMP` | `impactTin_medium_001.ogg` | `84253095543c094d83cd749f42ecfbc96e356b60385f18a192c18eafb25b3cc6` | SDRRIDTH-bed |
| `KEN-IMP` | `impactWood_light_002.ogg` | `b183cf7a5bd783817e0e4b82af34ac6658fa1927049089dadc8b15c2ecc771dc` | SDRRIDTH-bed |
| `OGA-CRE1` | `alien_03.ogg` | `8e417706c6ca3f7eb99d9500d17bf74ef977d16c540dfa9d695db4721cc30003` | SDSTOSIT |
| `OGA-CRE1` | `breath.ogg` | `d6ecfd092c261059701fe81581957ce6e67c1737978449bbd98ec6d4f30abb7f` | SDSTOACT, SDHNDACT, SDPZRACT |
| `OGA-CRE1` | `eat_02.ogg` | `60226fe5e4bf5ced6457f43ef89114a91d8790634a9aebb3c5754768fe04d6ee` | SDHNDATK, SDDGBMEL |
| `OGA-CRE1` | `hurt_02.ogg` | `b90ca3a0f5f48e1141ec6326f08ebf9f597efb6b2ca4ceeccc285b203c1ccbe1` | SDSTOPAI |
| `OGA-CRE1` | `hurt_05.ogg` | `4dc63fc62e8604a87baa1f5a74b75d848ccb68ce6e0e34d603dd3cbefc8519ed` | SDDGBPAI |
| `OGA-CRE1` | `monster_03.ogg` | `1208729886f3f66e7d8018e8880dff073275fd37b30e1016dd5b164161482df1` | SDDGBSIT |
| `OGA-CRE1` | `monster_06.ogg` | `6b8df01eb7821fb0fcf66b4683a8eb997ca728fded26b6937734b84ff05852f9` | SDSTOSIT |
| `OGA-CRE1` | `monster_07.ogg` | `5f7d40c4899f2e2e146fe8a0207597d4daf4d304a644ad2e8629057bc49a87e9` | SDSTODTH |
| `OGA-CRE1` | `roar_02.ogg` | `ceb532ee0fe775d6f86a821099b75f1790ab8022b963cb837c8c1fa4fffee5c2` | SDPZRSIT |
| `OGA-CRE1` | `scream_02.ogg` | `73aedfbcc7e5b3004507d5a79e95ae53954026036bf8d6f65aa0a4ca298dd372` | SDDGBSIT |
| `OGA-CRE1` | `spit_02.ogg` | `aa65f01311e914d2861f1992a4e59f431c03edcf020e09961e422728562a2657` | SDDGBMIS |
| `OGA-CRE2` | `alien_07.ogg` | `da62275c7b3b8fe3fbf8feb318cd030b045a0e598b792a996734d2cedcc1f323` | SDHNDSIT |
| `OGA-CRE2` | `breath_02.ogg` | `5b32729394cc36667bb8052508115941f21d85804f84ecda4c492d19883cd15e` | SDSTOACT, SDHNDACT, SDPZRACT |
| `OGA-CRE2` | `die_02.ogg` | `03e0fefd50fe350d0ca16c6ebf121c005290aa26a04a8e8573925bf33d4501d3` | SDHNDDTH |
| `OGA-CRE2` | `die_03.ogg` | `59f9188919b50d40da3c9dd94e00c2d1c0db915ecc5b2eddfbf574743651c836` | SDHNDDTH |
| `OGA-CRE2` | `die_04.ogg` | `aad7ac7b49b3dc2c4d929ddc6a5c184c7c188d1a5224b4d88e4f7371c9075f79` | SDPZRDTH |
| `OGA-CRE2` | `grunt_09.ogg` | `b138762382a073bc661baca09c167bc4b774adfaff32bddffb843e22a66dc1cb` | SDPZRPAI |
| `OGA-CRE2` | `monster_10.ogg` | `0f7293afd256e035a42255e3a7901df68ca6a4245194179d4091c26cc402f994` | SDHNDPAI |
| `OGA-CRE2` | `roar_04.ogg` | `4bd8be77b058410e1af9a3a5aa5c62b8ec9ac214672be4ab84180e156e8c0a20` | SDPZRDTH |
| `OGA-CRE2` | `roar_05.ogg` | `26614607c1683d8bbb82993f285a0d11b6e5ca1ebd5176e6ea552c3e833479f1` | SDPZRSIT |
| `OGA-CRE2` | `slime_07.ogg` | `687cd1feb815f9e214b20f16000ec5fd52174b03ec0b4da18d1abb20c2c4cbe2` | SDDGBEXP |
| `OGA-SNARL` | `monster-snarl-attack.ogg` | `34bf1ceef265725abf00ab3263bbbb492792e126bb1619addd4a5d3ad123347f` | SDHNDSIT |

**Two risks for the audition, stated before anyone listens.** (1) The three
idles of the Stormtrooper, the hound and the Panzermensch start from the same
two breaths (`breath.ogg`, `breath_02.ogg`), pitched and filtered apart; if
they read as one creature, one of them changes source. (2) The hound's bite
and the Doughboy's melee share `eat_02.ogg` under different hits.

### 5.10 Beds: the non-vocal layers of the voice lumps

Four cards above name things that are not a voice under a voice row: the
Legion's squelch and its "falling carrier, squelch click-off" (5.2), the
General's "mechanism failure" (5.7), the collapse of a death. With the
takes postponed (D37) those are built now as **beds**: `<LUMP>-bed` files in
`work/audio/sfx/enemies/beds/`, not lumps, never in the overlay, mixed under
the CEO's take when it arrives. A bed starts where the voice starts, so its
internal offsets are a timing proposal ("the rifle lands 0.52 s after the
voice begins"); moving them is part of the voice mix.

| Bed | Under | What it is | Length |
|---|---|---|---|
| `SDRRIPAI-bed` | rifleman pain | webbing, buckles and sling jolt once | 0.20 s |
| `SDRRIDTH-bed` | rifleman death | gear at once; at 0.45 s the body falls, the rifle clatters, bounces and settles, the helmet rings | 1.04 s |
| `SDLTRACT-bed` | trooper idle | `LEGION-RADIO` frame: squelch opens, the channel hisses, squelch closes | 1.42 s |
| `SDLTRSIT-bed` | trooper sight | short open, hiss, squelch tail | 0.54 s |
| `SDLTRPAI-bed` | trooper pain | gated static burst and a gear jolt | 0.22 s |
| `SDLTRDTH-bed` | trooper death | the carrier falls 1.4 kHz to 180 Hz and crushes, the squelch clicks off, the body and gear land | 0.97 s |
| `SDGENPAI-bed` | General pain | a chrome plate struck, a servo jerks | 0.55 s |
| `SDGENDTH-bed` | General death | servos wind down, relays chatter, sparks, the hum sags; at 1.55 s the chrome falls and rings out (the cue may ring, §5.7) | 4.14 s |

No bed for the four calls with nothing but a voice in their card
(`SDRRIACT`, `SDRRISIT`, `SDGENSIT`, `SDGENSUM`).

### 5.11 What these drafts do not cover

- **The twelve voices** (D37), and therefore the final rifleman, trooper and
  General: until the takes come they keep Freedoom's voices.
- **Footsteps for the other six actors.** The bestiary contracts one footstep,
  the Panzermensch's `SDPZRSTP` (H), and nothing else; a step for any other
  class would be a new lump, a new `SNDINFO` line and an `A_StartSound` in its
  `See` state (`mod-engineer`'s files), so it is a bestiary change first.
- **The heavy Panzermensch** (`SD_PanzermenschSchwer`, 8th class) has no lumps:
  it inherits every state and sound of `SD_Panzermensch` (`BESTIARY.md` §12).
  If he should sound heavier, the cheap route is a pitch on his `SNDINFO`
  aliases (`mod-engineer`), not new lumps.
- **Variation.** One take per lump in these drafts. Since N9e (§5.12) the
  sounds with several approved takes use `SNDINFO`'s `$random`, the syntax
  read in gzdoom.pk3's own `SNDINFO`; pitch shift is still unused.

### 5.12 Installed (N9e, 2026-10-20): D83's 30 sounds and 5 beds, D86's takes

Tool: `tools/audio/master_enemy_sfx.py` (tests: `tests/test_enemy_sfx_install.py`),
the weapons' pass (`master_weapon_sfx.py`, WEAPON-SOUNDS §10) applied to
the enemies. Nothing is re-synthesised: each approved take is rendered by
the generator that drew it (`gen_sfx.py` for the D83 drafts and beds,
seed 1977; `gen_enemy_alts.py` for the D86 alternatives) and levelled.

```bash
.venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --list       # the plan and the targets, writes nothing
.venv/Scripts/python.exe tools/audio/master_enemy_sfx.py              # WAV masters + MANIFEST in work/audio/master_enemy/
.venv/Scripts/python.exe tools/audio/master_enemy_sfx.py --install    # and the OGGs into assets/sounds/enemies/
```

**Targets.** The ruler is `gen_weapon_alts.py`'s (loudest 50 ms,
A-weighted). A sound matches the Freedoom lump `SNDINFO` played for it
before N9e; a bed sits 3 dB under its voice's stand-in (a voice goes on
top, §5.10; the same allowance `gen_enemy_alts.py` gave the bed
alternatives). **A sound already in its window is left as it is**: every
D86 alternative was levelled to these same targets for the CEO's page, and
five D83 drafts were already there too. The rest (the D83 drafts, levelled
to `gen_sfx.py`'s quieter class loudness) get the weapons' pass: a low
shelf only if bass-only, peak at -1 dBFS, gain down or up to 9 dB of
look-ahead limiting, no saturation.

**The codec check.** Every master is then encoded to Vorbis and decoded;
while the decoded peak reaches -0.1 dBFS, the look-ahead limiter takes the
master's ceiling down by the overshoot plus 0.2 dB. Vorbis lifted the
dense, saturated alternatives well over their -1 dBFS masters (SDLTRATK to
+1.4 dBFS, a clip in any 16-bit path; the page the CEO heard had the
same), so seven of them were limited by 0.3-1.7 dB (`CODEC_TRIMMED`:
`SDRRIAT2` 0.5, `SDRRIAT3` 0.3, `SDLTRATK` 1.7, `SDSTOPA2` 0.7, `SDSTODT1`
0.4, `SDSTODT2` 1.0, `SDSTODT3` 1.6): the same take, its peaks lower, its
level 0.1-1.3 dB lower (`SDSTODT3` is now 1.4 dB short). The other eleven
alternatives ship byte for byte the OGG of the page
(`tests/test_enemy_sfx_install.py`, `AltIdentityTests`).

**SDRRIATK alt2** (D86: "once its final click is quieter than the
first"): the bolt's closing ping measured -27.0 dB A over its loudest 50 ms
against -27.2 for the opening click; it rang longer, so it read louder.
`gen_enemy_alts.py` now mixes it 7 dB lower (`FINAL_CLICK_DB` -11, was
-4): -34.0 against -27.2, the crack at -10.4 untouched. The page's file
in `work/audio/enemy_alt/` was re-rendered with it.

**Names and `$random`.** One approved take ships under its card's name.
Several approved takes of one sound (D86) all ship, the card's last letter
replaced by the take's number (`SDSTOPA1`-`SDSTOPA3`), and the name the
code asks for becomes a `$random` alias over `<name>/<take>` lines, the
syntax of gzdoom.pk3's own `$random grunt/sight { grunt/sight1 ... }`
(read in g4.14.2's `filter/game-doomchex/sndinfo.txt`): the engine picks a
member each time it plays. Seven groups: the rifleman's attack, the
Stormtrooper's pain and death, the Panzermensch's pain, and the beds of the
rifleman's pain and the trooper's pain and death.

**The beds are parked.** A bed is not its voice: it ships as `SD` + actor +
the event's initial + `B` + take (`SDRRIDB1`, `SDLTRPB1`-`3`), named
`sd/bed/<actor>/<event>` in `SNDINFO`, and nothing plays it. It is mixed
under its voice take when the CEO approves the takes (D87, §5.10: the
timing in the bed is the proposal), and the voice lump keeps the card's
name (`SDRRIDTH`, R09's take since D96: the bed under it is still
unmixed, a new sound the CEO has not heard). The voices speak without a
bed, ours (D91, D96) or Freedoom's; hear a bed with the console's
`playsound sd/bed/legiontrooper/death`. (The Legion's idle bed sits at
-31.6 dB A because `DSPOSACT`, the murmur it goes under, is -28.6.)

| Lump | Approved | Take | Logical name | Target, dB A (from) | Before: peak / loudA / >300 Hz | After: peak / loudA / >300 Hz | Pass | Window |
|---|---|---|---|---|---|---|---|---|
| `SDRRIXDT` | D83 | SDRRIXDT | `sd/mon/reichrifleman/xdeath` | -11.6 (`DSSLOP` +0) | -2.6 / -15.6 / 68 % | -1.0 / -12.1 / 63 % | shelf 0.0, limit 7.5, gain 0.0 dB | on target |
| `SDLTRXDT` | D83 | SDLTRXDT | `sd/mon/legiontrooper/xdeath` | -11.6 (`DSSLOP` +0) | -2.9 / -15.5 / 71 % | -1.0 / -11.9 / 68 % | shelf 0.0, limit 4.8, gain 0.0 dB | on target |
| `SDSTOACT` | D83 | SDSTOACT | `sd/mon/stormtrooper/active` | -18.7 (`DSBGACT` +0) | -10.6 / -18.0 / 97 % | -10.6 / -18.0 / 97 % | untouched | on target |
| `SDSTOSIT` | D83 | SDSTOSIT | `sd/mon/stormtrooper/sight` | -11.0 (`DSBGSIT1` +0) | -4.1 / -13.9 / 66 % | -1.2 / -11.0 / 66 % | shelf 0.0, limit 0.0, gain -0.2 dB | on target |
| `SDSTOMEL` | D83 | SDSTOMEL | `sd/mon/stormtrooper/melee` | -9.3 (`DSCLAW` +0) | -3.9 / -17.6 / 44 % | -1.0 / -13.9 / 44 % | shelf 0.0, limit 3.0, gain 0.0 dB | **4.7 dB short** |
| `SDSTOMIS` | D83 | SDSTOMIS | `sd/mon/stormtrooper/missile` | -15.9 (`DSFIRSHT` +0) | -3.9 / -13.5 / 92 % | -6.3 / -15.9 / 92 % | shelf 0.0, limit 0.0, gain -5.3 dB | on target |
| `SDSTOEXP` | D83 | SDSTOEXP | `sd/mon/stormtrooper/explode` | -20.0 (`DSFIRXPL` +0) | -1.0 / -14.5 / 100 % | -6.5 / -20.0 / 100 % | shelf 0.0, limit 0.0, gain -5.5 dB | on target |
| `SDSTOXDT` | D83 | SDSTOXDT | `sd/mon/stormtrooper/xdeath` | -11.6 (`DSSLOP` +0) | -2.3 / -15.6 / 70 % | -1.0 / -12.1 / 65 % | shelf 0.0, limit 7.2, gain 0.0 dB | on target |
| `SDHNDACT` | D83 | SDHNDACT | `sd/mon/reichhound/active` | -12.9 (`DSDMACT` +0) | -5.2 / -15.6 / 74 % | -2.6 / -12.9 / 74 % | shelf 0.0, limit 0.0, gain -1.6 dB | on target |
| `SDHNDSIT` | D83 | SDHNDSIT | `sd/mon/reichhound/sight` | -11.8 (`DSSGTSIT` +0) | -3.0 / -12.3 / 100 % | -3.0 / -12.3 / 100 % | untouched | on target |
| `SDHNDATK` | D83 | SDHNDATK | `sd/mon/reichhound/attack` | -6.3 (`DSSGTATK` +0) | -1.0 / -16.8 / 28 % | -1.0 / -14.3 / 26 % | shelf 0.0, limit 8.2, gain 0.0 dB | **8.0 dB short** |
| `SDHNDPAI` | D83 | SDHNDPAI | `sd/mon/reichhound/pain` | -11.7 (`DSDMPAIN` +0) | -4.4 / -15.6 / 95 % | -1.0 / -11.7 / 95 % | shelf 0.0, limit 0.5, gain 0.0 dB | on target |
| `SDHNDDTH` | D83 | SDHNDDTH | `sd/mon/reichhound/death` | -14.3 (`DSSGTDTH` +0) | -1.4 / -14.0 / 33 % | -1.4 / -14.0 / 33 % | untouched | on target |
| `SDDGBACT` | D83 | SDDGBACT | `sd/mon/doughboy/active` | -12.9 (`DSDMACT` +0) | -9.0 / -30.4 / 3 % | -1.0 / -16.8 / 12 % | shelf 9.0, limit 3.0, gain 0.0 dB | **3.9 dB short** |
| `SDDGBSIT` | D83 | SDDGBSIT | `sd/mon/doughboy/sight` | -11.5 (`DSCACSIT` +0) | -3.2 / -14.3 / 92 % | -1.0 / -11.5 / 91 % | shelf 0.0, limit 3.9, gain 0.0 dB | on target |
| `SDDGBMEL` | D83 | SDDGBMEL | `sd/mon/doughboy/melee` | -9.3 (`DSCLAW` +0) | -1.0 / -15.0 / 61 % | -1.0 / -12.5 / 65 % | shelf 0.0, limit 4.6, gain 0.0 dB | **3.2 dB short** |
| `SDDGBMIS` | D83 | SDDGBMIS | `sd/mon/doughboy/missile` | -15.9 (`DSFIRSHT` +0) | -1.0 / -11.7 / 87 % | -5.2 / -15.9 / 87 % | shelf 0.0, limit 0.0, gain -4.2 dB | on target |
| `SDDGBEXP` | D83 | SDDGBEXP | `sd/mon/doughboy/explode` | -20.0 (`DSFIRXPL` +0) | -1.2 / -14.6 / 41 % | -6.6 / -20.0 / 41 % | shelf 0.0, limit 0.0, gain -5.6 dB | on target |
| `SDDGBPAI` | D83 | SDDGBPAI | `sd/mon/doughboy/pain` | -11.7 (`DSDMPAIN` +0) | -3.1 / -18.0 / 67 % | -1.0 / -13.1 / 69 % | shelf 0.0, limit 6.6, gain 0.0 dB | **1.4 dB short** |
| `SDDGBDTH` | D83 | SDDGBDTH | `sd/mon/doughboy/death` | -11.3 (`DSCACDTH` +0) | -2.3 / -13.6 / 72 % | -1.0 / -11.3 / 72 % | shelf 0.0, limit 1.0, gain 0.0 dB | on target |
| `SDPZRACT` | D83 | SDPZRACT | `sd/mon/panzermensch/active` | -12.9 (`DSDMACT` +0) | -3.6 / -16.7 / 95 % | -1.0 / -12.9 / 95 % | shelf 0.0, limit 1.4, gain 0.0 dB | on target |
| `SDPZRSIT` | D83 | SDPZRSIT | `sd/mon/panzermensch/sight` | -9.5 (`DSKNTSIT` +0) | -1.0 / -19.7 / 16 % | -1.0 / -16.2 / 16 % | shelf 0.0, limit 8.3, gain 0.0 dB | **6.7 dB short** |
| `SDPZRMEL` | D83 | SDPZRMEL | `sd/mon/panzermensch/melee` | -13.1 (`DSSKEPCH` +0) | -1.5 / -21.9 / 3 % | -1.0 / -16.6 / 8 % | shelf 9.0, limit 2.5, gain 0.0 dB | **3.5 dB short** |
| `SDPZRMIS` | D83 | SDPZRMIS | `sd/mon/panzermensch/missile` | -15.9 (`DSFIRSHT` +0) | -2.0 / -16.3 / 49 % | -2.0 / -16.3 / 49 % | untouched | on target |
| `SDPZREXP` | D83 | SDPZREXP | `sd/mon/panzermensch/explode` | -20.0 (`DSFIRXPL` +0) | -1.0 / -17.8 / 7 % | -5.2 / -20.0 / 13 % | shelf 3.5, limit 0.0, gain -4.2 dB | on target |
| `SDPZRDTH` | D83 | SDPZRDTH | `sd/mon/panzermensch/death` | -8.9 (`DSKNTDTH` +0) | -1.0 / -17.0 / 9 % | -1.0 / -11.1 / 13 % | shelf 0.5, limit 8.1, gain 0.0 dB | **2.2 dB short** |
| `SDPZRSTP` | D83 | SDPZRSTP | `sd/mon/panzermensch/step` | -14.7 (`DSMETAL` +0) | -3.4 / -25.8 / 3 % | -1.0 / -17.8 / 9 % | shelf 9.0, limit 3.6, gain 0.0 dB | **3.1 dB short** |
| `SDGENACT` | D83 | SDGENACT | `sd/mon/general/active` | -12.9 (`DSDMACT` +0) | -13.4 / -29.9 / 9 % | -1.0 / -16.1 / 13 % | shelf 2.5, limit 2.8, gain 0.0 dB | **3.2 dB short** |
| `SDGENMIS` | D83 | SDGENMIS | `sd/mon/general/missile` | -14.2 (`DSRLAUNC` +0) | -1.0 / -12.3 / 67 % | -2.9 / -14.2 / 67 % | shelf 0.0, limit 0.0, gain -1.9 dB | on target |
| `SDGENEXP` | D83 | SDGENEXP | `sd/mon/general/explode` | -20.0 (`DSFIRXPL` +0) | -1.0 / -12.8 / 74 % | -8.2 / -20.0 / 74 % | shelf 0.0, limit 0.0, gain -7.2 dB | on target |
| `SDRRIAT1` | D86 | SDRRIATK_alt1 | `sd/mon/reichrifleman/attack/1` | -10.4 (`DSPISTOL` +0) | -1.0 / -10.4 / 98 % | -1.0 / -10.4 / 98 % | untouched | on target |
| `SDRRIAT2` | D86 | SDRRIATK_alt2 | `sd/mon/reichrifleman/attack/2` | -10.4 (`DSPISTOL` +0) | -1.0 / -10.4 / 98 % | -1.5 / -10.7 / 98 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 0.5 dB | on target |
| `SDRRIAT3` | D86 | SDRRIATK_alt3 | `sd/mon/reichrifleman/attack/3` | -10.4 (`DSPISTOL` +0) | -1.0 / -10.4 / 98 % | -1.3 / -10.4 / 98 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 0.3 dB | on target |
| `SDLTRATK` | D86 | SDLTRATK_alt2 | `sd/mon/legiontrooper/attack` | -7.9 (`DSDSHTGN` +0) | -1.0 / -7.9 / 94 % | -2.7 / -8.8 / 94 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 1.7 dB | on target |
| `SDSTOPA1` | D86 | SDSTOPAI_alt1 | `sd/mon/stormtrooper/pain/1` | -11.7 (`DSDMPAIN` +0) | -1.0 / -11.7 / 82 % | -1.0 / -11.7 / 82 % | untouched | on target |
| `SDSTOPA2` | D86 | SDSTOPAI_alt2 | `sd/mon/stormtrooper/pain/2` | -11.7 (`DSDMPAIN` +0) | -1.0 / -12.0 / 97 % | -1.7 / -12.1 / 96 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 0.7 dB | on target |
| `SDSTOPA3` | D86 | SDSTOPAI_alt3 | `sd/mon/stormtrooper/pain/3` | -11.7 (`DSDMPAIN` +0) | -1.0 / -11.7 / 99 % | -1.0 / -11.7 / 99 % | untouched | on target |
| `SDSTODT1` | D86 | SDSTODTH_alt1 | `sd/mon/stormtrooper/death/1` | -7.4 (`DSBGDTH1` +0) | -1.0 / -7.4 / 96 % | -1.4 / -7.7 / 96 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 0.4 dB | on target |
| `SDSTODT2` | D86 | SDSTODTH_alt2 | `sd/mon/stormtrooper/death/2` | -7.4 (`DSBGDTH1` +0) | -1.0 / -7.4 / 98 % | -2.0 / -8.0 / 98 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 1.0 dB | on target |
| `SDSTODT3` | D86 | SDSTODTH_alt3 | `sd/mon/stormtrooper/death/3` | -7.4 (`DSBGDTH1` +0) | -1.0 / -7.4 / 55 % | -2.6 / -8.7 / 56 % | shelf 0.0, limit 0.0, gain 0.0 dB, codec 1.6 dB | **1.4 dB short** |
| `SDPZRPA1` | D86 | SDPZRPAI_alt1 | `sd/mon/panzermensch/pain/1` | -11.7 (`DSDMPAIN` +0) | -1.2 / -11.7 / 77 % | -1.2 / -11.7 / 77 % | untouched | on target |
| `SDPZRPA2` | D86 | SDPZRPAI_alt2 | `sd/mon/panzermensch/pain/2` | -11.7 (`DSDMPAIN` +0) | -1.0 / -11.7 / 83 % | -1.0 / -11.7 / 83 % | untouched | on target |
| `SDPZRPA3` | D86 | SDPZRPAI_alt3 | `sd/mon/panzermensch/pain/3` | -11.7 (`DSDMPAIN` +0) | -1.0 / -11.7 / 56 % | -1.0 / -11.7 / 56 % | untouched | on target |
| `SDRRIDB1` | D83 | SDRRIDTH-bed | `sd/bed/reichrifleman/death` | -13.6 (`DSPODTH1` -3) | -2.6 / -20.7 / 15 % | -1.0 / -13.6 / 20 % | shelf 0.0, limit 6.2, gain 0.0 dB | on target |
| `SDLTRAB1` | D83 | SDLTRACT-bed | `sd/bed/legiontrooper/active` | -31.6 (`DSPOSACT` -3) | -1.0 / -10.3 / 99 % | -22.3 / -31.6 / 99 % | shelf 0.0 dB, limit, 0.0 dB, gain -21.3 dB | on target |
| `SDLTRSB1` | D83 | SDLTRSIT-bed | `sd/bed/legiontrooper/sight` | -14.2 (`DSPOSIT2` -3) | -4.5 / -14.0 / 100 % | -4.5 / -14.0 / 100 % | untouched | on target |
| `SDGENPB1` | D83 | SDGENPAI-bed | `sd/bed/general/pain` | -14.7 (`DSDMPAIN` -3) | -4.1 / -17.1 / 84 % | -1.7 / -14.7 / 84 % | shelf 0.0, limit 0.0, gain -0.7 dB | on target |
| `SDGENDB1` | D83 | SDGENDTH-bed | `sd/bed/general/death` | -14.3 (`DSCYBDTH` -3) | -7.4 / -15.4 / 74 % | -6.4 / -14.3 / 74 % | shelf 0.0, limit 0.0, gain -5.4 dB | on target |
| `SDRRIPB1` | D86 | SDRRIPAI_alt1 | `sd/bed/reichrifleman/pain/1` | -14.4 (`DSPOPAIN` -3) | -1.0 / -14.4 / 85 % | -1.0 / -14.4 / 85 % | untouched | on target |
| `SDRRIPB2` | D86 | SDRRIPAI_alt2 | `sd/bed/reichrifleman/pain/2` | -14.4 (`DSPOPAIN` -3) | -2.5 / -14.4 / 95 % | -2.5 / -14.4 / 95 % | untouched | on target |
| `SDRRIPB3` | D86 | SDRRIPAI_alt3 | `sd/bed/reichrifleman/pain/3` | -14.4 (`DSPOPAIN` -3) | -1.0 / -14.4 / 53 % | -1.0 / -14.4 / 53 % | untouched | on target |
| `SDLTRPB1` | D86 | SDLTRPAI_alt1 | `sd/bed/legiontrooper/pain/1` | -14.4 (`DSPOPAIN` -3) | -3.9 / -14.4 / 97 % | -3.9 / -14.4 / 97 % | untouched | on target |
| `SDLTRPB2` | D86 | SDLTRPAI_alt2 | `sd/bed/legiontrooper/pain/2` | -14.4 (`DSPOPAIN` -3) | -6.0 / -14.4 / 98 % | -6.0 / -14.4 / 98 % | untouched | on target |
| `SDLTRPB3` | D86 | SDLTRPAI_alt3 | `sd/bed/legiontrooper/pain/3` | -14.4 (`DSPOPAIN` -3) | -11.9 / -14.4 / 100 % | -11.9 / -14.4 / 100 % | untouched | on target |
| `SDLTRDB1` | D86 | SDLTRDTH_alt1 | `sd/bed/legiontrooper/death/1` | -11.3 (`DSPODTH2` -3) | -1.0 / -11.3 / 76 % | -1.0 / -11.3 / 76 % | untouched | on target |
| `SDLTRDB2` | D86 | SDLTRDTH_alt2 | `sd/bed/legiontrooper/death/2` | -11.3 (`DSPODTH2` -3) | -10.1 / -11.3 / 95 % | -10.1 / -11.3 / 95 % | untouched | on target |
| `SDLTRDB3` | D86 | SDLTRDTH_alt3 | `sd/bed/legiontrooper/death/3` | -11.3 (`DSPODTH2` -3) | -3.6 / -11.3 / 98 % | -3.6 / -11.3 / 98 % | untouched | on target |

**46 on target, 11 short**: `SDSTODT3` by its codec limiting
(above); the others at the pass's ceiling (peak -1 dBFS, limiting stopped
where more stops paying), as the weapons' were:
the bites, thuds and growls with most of their energy under 1 kHz, where
A-weighting counts little (`SDHNDATK` 8.0 dB under `DSSGTATK`, the
loudest Freedoom lump of the set; `SDPZRSIT` 6.7; `SDSTOMEL` 4.7), and the
three bass-only ones the sheet flagged amber, lifted by the 9 dB shelf
from 3 % to 8-12 % above 300 Hz (`SDDGBACT`, `SDPZRMEL`, `SDPZRSTP`).
Reaching their targets would take saturation or a brighter layer, a
re-voicing, not this pass.

**The installed files.** WAV masters reproduce on this PC; the OGGs depend
on the local ffmpeg, as the weapons' (WEAPON-SOUNDS §10.5).

| Lump | WAV master SHA-256 | Installed OGG SHA-256 |
|---|---|---|
| `SDRRIXDT` | `d4ba799569f917ba95f1796ab911361c37d73b6107b04b7ea3f62b33ac2a0549` | `e8693e626bcca23d8c71406593374481461e849f52cc086709c7ea66033427b0` |
| `SDLTRXDT` | `ac87aece072979284e154e33636e9a2ca30d77785f631a310c7563b4a5695ae3` | `adb42dcef0f7b20a1be5970d007c29d0c3c622e016f54345125a2851571575d8` |
| `SDSTOACT` | `363f6f2fbf19b2218ae69cbf7bee9ab3f5a9f6f8f2beeb36a12f0bd0ce19200a` | `7bf1a9bbf726e4d5e52b954d072e0de19d3dc9f6e0b27c8726b66b3a1242e031` |
| `SDSTOSIT` | `bfeafee3d6d6d38bb26269637dca4d7ae3db1cb4276ffe982ddb26d686b76f3e` | `e845728a07056f511f89415bc366ac65f6c36c6ff0d94cc3231b02a2769e993a` |
| `SDSTOMEL` | `cf72caae57bc8f66b688a7091b8fdf587901aea597520fa3963425934ae1f5ad` | `cc6529bc5644bf6612ceab953355e3af02b87103e371cdb235e4997f0de7133a` |
| `SDSTOMIS` | `61dcf55e213a69cddd5a3850f065f8c41fda52453f26af0504f51edc08b32fb0` | `bf844aef30c8e3a6a90b5e1e2be7629902eb1ac63f3a907400cf08973f79091d` |
| `SDSTOEXP` | `ffe6b22ba8be4d524e513f2acf4c2e2f84ab34c628df7bfdf0a778251cb4c418` | `ae56a4300dc976d16bf6d28db4b00a41558ba14dc2c2982678266b6ebe2f4503` |
| `SDSTOXDT` | `85cb5cc027427ea886ea560e03bc2ad217ef202e01a505485fd53a2fc24dfdc6` | `080709cb8f1b7aa762fb00249f32b59a2959374bc68434bea5d384aa8a244865` |
| `SDHNDACT` | `cebac3156b61654dd345781a9fdb112142fcd25ae775e2ff807a4226fa0e6565` | `cf81ac25623e1237b72af92467fc1a4cf24185d73bc16ce6529d0f97f2d6bc37` |
| `SDHNDSIT` | `5e6a5a268a61c30ea4d9012c6bdfcc1e86d954f23469202a36d12848865486a4` | `c6371ab5398ed60501c08ab05c164a4bad994cf8d8bcc1b386ba12eb9b8c8e04` |
| `SDHNDATK` | `757dc0b103f4ece927fbe604d48440c63e300b4863b92d883932104a1a6ef0fd` | `6f7c76a9a293a2b906d4913e432d5f2fc236799e7257d20c3fb599a910975f06` |
| `SDHNDPAI` | `94227677a11a32f17f3e893d4be40b01f77fc7464acab405d415729950b4b6a6` | `8f4c0da74f1e6a04b9b04e748021fbe3cc6b2cd819d83aac27354c9669b81bbe` |
| `SDHNDDTH` | `1a78ddee26f0c427a9fcad3250ea006c01420cf52c2092e702d841302c609133` | `7b7c0918f9667e500b622b20fef0fd58ac52d7ff771776fa125d44cc5a98964b` |
| `SDDGBACT` | `7e94cc430a625b78a5f99235a19019f07130d9d43f72c3f23e6e28796cbe12bc` | `fec6c0e2c362aebc89165b397cb19a129a9ba7724c5e1f2487f4e82e22271346` |
| `SDDGBSIT` | `b7e7475bd5c3ca2fe69d0ee96ea106b03992ef8c59db22ce7b8c976da5cc2917` | `be7bdb3edfca6e034f770fc4b8836beb547b0c2d42311aac2d6bed7b41d518b2` |
| `SDDGBMEL` | `0d430d460f5449bdb8702438ffd25d993b332f268a2f2687106e8b2ea903dd5b` | `5ab45c9c4f105b9556e79b16c3e24db09679b3f99a4c93a261ed36b2a1c1e3dc` |
| `SDDGBMIS` | `65b69447fed3217dfe36d066b6adfffecb913a97412719335f9840909c9cb028` | `977598dbd0e94112639758476ee01627c8ed0a62c106bbb1a349e5faa0665e00` |
| `SDDGBEXP` | `65b8161438fcc654c63e8a3d236651730c23cfea8f4a6b1f9f2f6786b052b46a` | `9723a7459ab21429cea1a7f2d39cb0b34cf74fc4957c364ed459845ff3b02257` |
| `SDDGBPAI` | `556033abdc803b965a1927f6e305ea9cff6ac7ad3c862e3e2de3f5892bd50aa9` | `e284d65322a99bfb07377aa78914fa6b684deec01f43125b2b7a2e275daee35a` |
| `SDDGBDTH` | `b2de6b32110a79e4e1aaa2984950819657790d27955d564d911b503c48c242af` | `266a80432998c901e0651ad04ee02119e5b82ef427ba6fe63ba68ee9afcacf18` |
| `SDPZRACT` | `bef6def1becc11c1b68d95686d2068ce26a5bdb068afd3b12d261f87a9da4935` | `b39cebf99e571252fcdf5df5210e14bdcaf9e36c64e68226ad98759dfb286807` |
| `SDPZRSIT` | `4749338c615b6292f394238bd3ce9f9c8886657141cdb9090bd6a576da3acd21` | `94ad02e5d7e2a7e644d42b8727377fee3fde040cd7ec3e84d667dd71238f9449` |
| `SDPZRMEL` | `e61c687e0e5b8ac72f77ef5a1311b0f600336055d3509dbab7a7c9b45c0fb3f5` | `0ba3ad8992a3ec324b8d69f26a20f5c81133518a7fb18d9bd2f927c66eca2291` |
| `SDPZRMIS` | `4ce86e1aee869854ec40f4db529d1faabf64ba24e3004e9d1389f6c5eac31521` | `175411e473ba2e1951d6a080bc6403364cad9ea11c7fb1253b015207350bf6b0` |
| `SDPZREXP` | `dfa79c3fdb1edf5459da7d220ab0de71802a20bf42a87b8192bdc0056ecfc853` | `4cfc77bf46889642023acf2988b62e99c684b626b5500a462cbaccaf884edae4` |
| `SDPZRDTH` | `aeb3e60a5a9377dfefdb4d996b0837df90f39bb8150fcd081de41e2f78b83ffa` | `1f8e3ee6e5ccf24834ecc7481465b216180385c50f59e17696d7051ee26845cf` |
| `SDPZRSTP` | `64f24acbd46f1d9851e8bfa8c891b038c665c54bfb270dd21483e28ba99dcf49` | `62c0819c0f783c72ebd564d00f452976662e7f7935c99a896d98479598f242d0` |
| `SDGENACT` | `a2dbd44ec32d7578e6ffb3ed9b961810f49571676b7d63b54010d550c397cb61` | `f9e6cf0cb717220677e796a2e7e5c4eebd45b4b449afeadf5bf93cf4e6b47d8d` |
| `SDGENMIS` | `068593e58aa9e21e2a2d330a5df05691a686a46871f99dda607d009940c5ba90` | `2846d83a9267ef84b8d2d0d51afd73bfa1469cea51bc90f79cb4de5eaece788e` |
| `SDGENEXP` | `15c1bf6d5282056b59cbb316ab8de314929bc0809f86a7b2d9679eb8f0790e8d` | `98c8bbcff239bd7db7a160005ee312f5958de85c771757ba2dbb46f78bb1049a` |
| `SDRRIAT1` | `db54e1f9f6b3782262c3b6af10b3569ed85518b13acf0b68ec64ab2f2cad5e93` | `9b333ed596a8b30a66ecb6c281d4b672f8676d80b62c92dc53e2a1fb7c602953` |
| `SDRRIAT2` | `0ed4fe60440513f0dbc6846c43307928fcd95097f057115ca613054a72f23770` | `097a909a6849e3cfc9bbe8050f90b59e35e66630f011d714c05bcf5c1739ed8c` |
| `SDRRIAT3` | `9352f7463d64291aebab0eee0118fb700aa4a9f1520ff7fd013df8e3af27c8f4` | `589810e19523d29b2f0153bfbb7b6ff815d5f5e956a1920d8dc0933799069a71` |
| `SDLTRATK` | `0ecbc23400d6dafcf7504bdb20bf32187a9c86065c3dde4883b7ef7295e0c4f1` | `b8027da3f66cc94e99e8060bd4cc24b2e689b60f9528fe0c555c28437b4f2359` |
| `SDSTOPA1` | `73e4b2dfa57222befaf17d891fd872823b4bbfefd5a0c3191a362f2ae27831d6` | `84fe7d232e4b9e8d127246be6cc04e69f7fb7c295c40ce691247d15b486a3b06` |
| `SDSTOPA2` | `47f8b59bac9bf5b66757e2264cc06c9b3d04030b2474732e8cd0c9fe3fbe26b3` | `37ea2db8151f7dcb7020a98f5f7cc34f39ac2d18ceed295cc346e203d232f179` |
| `SDSTOPA3` | `3f4dc3450562377defd6741e43ca1d6d439ce71c454211d5454c917b87bc4d11` | `9e4b183ea79f0df236a734f7096ff0134931ba3ebbb653d5789c61b8904031bc` |
| `SDSTODT1` | `1cfa73fbb27ea21f8e4eda664df01e8a789267f98e4253a5bda79b11eb0d8d58` | `e9458fb00c0a996a2a7b696ca977703f6d006172de962feba4f2c0e85095bc9b` |
| `SDSTODT2` | `3e974f6dec11b2eb1d96ba578a2dbbb487e2a7cc013aa7070957512437d3fa02` | `abffe18f1f071d37521b845fee790744ee4d3e338c132717b853816ab60b521c` |
| `SDSTODT3` | `7d88822664590c726ddb727fedc609a534a51e7faa3c3f91d0ae14fe37e22712` | `031acd4243f917d8bf419c2aa72c4a483dc478827939316945761a4de32b3375` |
| `SDPZRPA1` | `9a8e87b2ee896d921c6e20f96e83d6db5bac90fa7eabb9de96aedf155d9f9500` | `4ed58a5d9dfefed6df1bf785aabd92e86e07460579adba01bf48b5ec71fa1223` |
| `SDPZRPA2` | `2d1f42d0fa403bc2379ea2a8eef387f260d79872d0404432015818d57cb26bb0` | `3b21a19b619a004e963042bdd713ff20907253be159f075310ea64e085df00d5` |
| `SDPZRPA3` | `07def89a1e2b27315888c4e7f0513db8d3e17e252d7ca8b28e5830e9ef313b0a` | `a5e1bf5482220e5157cd104f607c4722d8aaf05eb583792baa4d82e3601e15d9` |
| `SDRRIDB1` | `9522f694b74e244a4bc0a3db6e6a39e2e77bbe1a70de94dad5c99862a12f370b` | `f4c6c406f72e3e87c4a6377f184bfe7460cc25d89d137b76107c584797f89cd1` |
| `SDLTRAB1` | `438539c9958c3354f9b3837f3d4988c026dbe923ad337409a280d8ee78e81aff` | `2d8ee7917d4b5c41e2eabd56353ee3ac52db33a74a0cda48e7d58b7705040cf0` |
| `SDLTRSB1` | `36048db0d745230b076d39db45c1765b19452f72c88232c6f3b22b3db474224a` | `dd5ea43ac8b14678577da921d5de9e34b40c0d7c55cbcf8d22085eb3d5e84b8e` |
| `SDGENPB1` | `7f99843405a9045bbda6a44d3c3b9b4dd74d15ab5918d7916b1ad25412f3d854` | `11064ad61499ffa05f643f37782e8fcb268d0933f2a543d7a0adc652409771aa` |
| `SDGENDB1` | `5e141851482e4930954e92083917703dda1e7a0f22d432ef480046992ed42e89` | `301e2e38ac884a5eb3f7f0255bbde8a0849137b3cd163f4e596e16d81f84231f` |
| `SDRRIPB1` | `7970c3ce8486f16825355056beafaad1ae524395a717fdf4da1416f08d479141` | `6b070995908ac95d442b57fc794c3c28402ab17e792b3839cad484b3c8335375` |
| `SDRRIPB2` | `9062bbeb89c188771aab97704939ebcf56bc64a9c541db4b4fd38f329ca4e50f` | `534d1a706ab3b34e69c8c19bf9a8e1ee0c2380675f8fd34fab4f3e283eec4e13` |
| `SDRRIPB3` | `05238bc6d26a7a8db31e683774d232510bc6c9f292ebc294c34cf3d9e52d2ebc` | `b2547e903d3cdd2623699d5b2ef9976b0a9b1a2f002140cde83da13e4dac2e83` |
| `SDLTRPB1` | `6ff3aab059d1be2fd9d9323057b331820f09106ed55fcd4284543eaa453c4518` | `3e826792cc0ec5ff5593eb2c3a2e802a733ff9372344c990fdf932f43ab85f4d` |
| `SDLTRPB2` | `5d202942535e99fcf7fb23e9ee56b5e45188d446855929b2400f1814b49d2b05` | `39936f454d985b551242215dcc42cdfbd04245f523af67694d3dfbab8e249f75` |
| `SDLTRPB3` | `11f4bcdba0ef8d6c79096a71f5e908ee9488953cbee9f9def3e2df14aa5f4f74` | `17cea51ca9ca8692bdb14b9142fdd5d41b078408dfaf5295da4217ee15debfe7` |
| `SDLTRDB1` | `db4ae9f111a842b1e177193ba5e8a56b4e7b566897d50fe4a420c791e002f790` | `6b9cba1e526024640f774877954ede721183953c381d237a3a70606d757850db` |
| `SDLTRDB2` | `9b45b043beee329051461469e0979a9f78d2ee107e66b99d10bc84f6d402f7b9` | `8d51eb7b51991ea4c7fbc80b0ecbf7d4596647b15c254432d26f27d9a2c28e96` |
| `SDLTRDB3` | `d5d9200dc1bd2e68216651c02afc37d30a22b5cceeb7e1bb03eff7532d17383a` | `6eb6456a086b7dacd3ceeff657626082dbe61209ee00c2a52ff621ae219edbe1` |

**The seven voice takes (D91, N9e).** The CEO approved seven of the
Chatterbox drafts (D87; `docs/art/previews/2026-10-20_1135_P2_voice-takes.html`):
R06 t01 and t03 ("Kontakt!", the rifleman's sight) and L01 t01, t03, L02
t01-t03 (the trooper's idle radio lines). They ship as the OGGs
`tools/audio/process_voice_takes.py` made for the page, byte for byte
(`master_enemy_sfx.py --voices` checks the decoded peak and the loudness
and copies them; the raw takes cannot be regenerated here without the
Chatterbox server). Each name is a `$random` group: the rifleman's sight
over `SDRRISI1`/`SDRRISI3` (the takes' own numbers), the trooper's idle
over `SDLTRAC1`-`SDLTRAC5` (L01 t01, L01 t03, L02 t01, L02 t02, L02 t03).
The trooper's idle bed `SDLTRAB1` stays parked: mixing a bed under a
voice is a new sound the CEO has not heard. The other ten voices keep
Freedoom's lumps until a shouted reference exists (D91).

| Lump | Take | Logical name | Target, dB A (from) | Installed OGG SHA-256 |
|---|---|---|---|---|
| `SDRRISI1` | R06 t01 | `sd/mon/reichrifleman/sight/1` | -10.1 (`DSPOSIT1`) | `dd56db85f651faf912cf09031daa4f5a726455d03758531c809584f1b1e1ef18` |
| `SDRRISI3` | R06 t03 | `sd/mon/reichrifleman/sight/3` | -10.1 (`DSPOSIT1`) | `9b8063c21dd9caa51f87562ae28de2a7eacdbffb002ce2944cf38cfe8fa7be2b` |
| `SDLTRAC1` | L01 t01 | `sd/mon/legiontrooper/active/1` | -28.6 (`DSPOSACT`) | `45132e6973126e320508b2373995ccf12ac316f90d8672287f2a9cfa18316d82` |
| `SDLTRAC2` | L01 t03 | `sd/mon/legiontrooper/active/2` | -28.6 (`DSPOSACT`) | `4ac94a6ee67c10db212f26d4fffff0e0775c0ac4731da6b083a47f5194ec68d9` |
| `SDLTRAC3` | L02 t01 | `sd/mon/legiontrooper/active/3` | -28.6 (`DSPOSACT`) | `143887b4851dda474433f5ba465b963677ed33675eb9f9f09236b266a059f825` |
| `SDLTRAC4` | L02 t02 | `sd/mon/legiontrooper/active/4` | -28.6 (`DSPOSACT`) | `c2c02cded81348a5a8264a1c0d42a7532e410145e4184572d178b4654ff7f4c6` |
| `SDLTRAC5` | L02 t03 | `sd/mon/legiontrooper/active/5` | -28.6 (`DSPOSACT`) | `5acad54da26ab55e5fe929c8c8a42e6c46240a5c6d290a4b572b41aaf1656a16` |

**The seventeen voice takes (D96, N9e).** The aggressive round
(`docs/art/previews/2026-10-20_1330_P2_voice-takes-aggressive.html`, 40/40
judged): Chatterbox Multilingual cloning a shouted reference instead of a
predefined voice, the answer to D91's diagnosis (the model copies the
reference's emotion). The references (Thorsten Müller's "angry" style of
the Thorsten-Voice emotional set, CC0; kurt's "Soldier Voice Acting",
CC-BY 3.0, OpenGameArt; HaelDB's "Male Grunt/Yelling sounds", CC0) stay
in `work/` and are not distributed; `work/audio/voice_takes/AI-LOG.csv`
gives each take's reference with its SHA-256, the text, the seed and the
settings; kurt's credit is owed and given (`docs/art/LICENSES.md`, the
in-game credits, CREDITS.txt). `master_enemy_sfx.py --voices` copies the
processed OGGs from `work/audio/voice_takes/aggressive/` byte for byte,
after the same checks as D91's, with one exception: **`SDGENSU1`** (G02
t13) decoded to -0.02 dBFS, over the -0.1 dBFS ceiling (a clip waiting
in any 16-bit path), so it got the codec pass the D83/D86 sounds got (§5.12 "The codec
check"): its master, which `process_voice_takes.process_wave` re-renders
byte-identically from the raw take, limited by **0.6 dB** of peak
(`VOICE_CODEC_TRIMMED`), now -0.49 dBFS decoded and -9.97 dB A against
-9.60 (the window is ±1). The other sixteen ship as the page played them.

Where they go (VOICE-SCRIPT §1): a line with several approved takes
contributes all of them, and a sound with several takes is a `$random`
group, numbered on after D91's: the rifleman's sight is now five takes
(R06 t01, t03; R04 t12, t13; R05 t12), the trooper's idle six (L01, L02,
L03 t12), and new groups are the rifleman's idle (R01-R03), the trooper's
sight (L04 t12, t14, L05, L06) and pain (L08 t14, t15) and the General's
order (G02 t13, t14). A sound with one take ships under its card's name
(`SDRRIDTH`, `SDGENSIT`). No ZScript changed: every alias was already
played (the rifleman's and trooper's `SeeSound`, `ActiveSound`,
`PainSound`, `DeathSound` through `A_Look`/`A_Chase`, `A_Pain`,
`A_Scream`; the General's `SeeSound`; his order by `A_StartSound` in
`A_SD_GeneralSummon`, the frame that prints `SD_GENERAL_ORDER`), only
`SNDINFO`'s right-hand column. Still Freedoom's (no take approved): the
rifleman's pain (`DSPOPAIN`), the trooper's death (`DSPODTH2`), the
General's pain (`DSDMPAIN`) and death (`DSCYBDTH`).

| Lump | Take | Line | Reference | Logical name | Target, dB A (from) | Installed OGG SHA-256 |
|---|---|---|---|---|---|---|
| `SDRRIAC1` | R01 t13 | "Stellung halten!" | Thorsten | `sd/mon/reichrifleman/active/1` | -28.6 (`DSPOSACT`) | `5d34cb6f1e99f8ad4bfd315029f59eb59a6e7351ea1fe3e3f1b3878577f61be7` |
| `SDRRIAC2` | R02 t11 | "Augen auf!" | Thorsten | `sd/mon/reichrifleman/active/2` | -28.6 (`DSPOSACT`) | `18b440aa6fa0206097308acc0dfcba3668c0f7d0ded32cc7fff14a2405738a6c` |
| `SDRRIAC3` | R03 t14 | "Ruhe da hinten!" | Thorsten | `sd/mon/reichrifleman/active/3` | -28.6 (`DSPOSACT`) | `56ceff7ffae58567fbe8bf41be4d43f2858d219cb8ff3b284111222ebbb18b80` |
| `SDRRISI4` | R04 t12 | "Feind!" | Thorsten | `sd/mon/reichrifleman/sight/4` | -10.1 (`DSPOSIT1`) | `fa100a4f8e29167ab3be76651c42b14671a86f47f7ee68fb223deb71589f7089` |
| `SDRRISI5` | R04 t13 | "Feind!" | Thorsten | `sd/mon/reichrifleman/sight/5` | -10.1 (`DSPOSIT1`) | `a352944e75d086f9a789d9fcf6f539e2a30c29a13a4da6285f205ac0cc4aa552` |
| `SDRRISI6` | R05 t12 | "Da!" | Thorsten | `sd/mon/reichrifleman/sight/6` | -10.1 (`DSPOSIT1`) | `ac6d58699d67c41b2988344f133f8cfa3a2cfa6be79fb103b7cad85c5653a019` |
| `SDRRIDTH` | R09 t12 | "Sani…" | HaelDB | `sd/mon/reichrifleman/death` | -10.6 (`DSPODTH1`) | `9de406901cec90a6d6b8f03080ad750c4feaa9651e0550530206e1d89d1552fa` |
| `SDLTRAC6` | L03 t12 | "Command, say again?" | kurt | `sd/mon/legiontrooper/active/6` | -28.6 (`DSPOSACT`) | `a7c20685c41a9b9314ae16e05eadc6424fe77098e7c2dc6802b57af00bf95593` |
| `SDLTRSI1` | L04 t12 | "Contact!" | kurt | `sd/mon/legiontrooper/sight/1` | -11.2 (`DSPOSIT2`) | `0b5ab35624419e5d91b9d32186c878f7ce00d0696dab8ff5e6fbc0c2b047c1ad` |
| `SDLTRSI2` | L04 t14 | "Contact!" | kurt | `sd/mon/legiontrooper/sight/2` | -11.2 (`DSPOSIT2`) | `0fdf1676b4b23efe2b5b6090be356d43a8b9ae62c8c60d7d5af1025579085f62` |
| `SDLTRSI3` | L05 t13 | "Hostile, front!" | kurt | `sd/mon/legiontrooper/sight/3` | -11.2 (`DSPOSIT2`) | `cc1fd41c09113e96607edce43b7e9906a17c7b2f1e92e1e7ccd6f33b26ea4438` |
| `SDLTRSI4` | L06 t13 | "Got movement!" | kurt | `sd/mon/legiontrooper/sight/4` | -11.2 (`DSPOSIT2`) | `815ab1a72ec0842a411f96ab484be3e56693a54727640b171e8d27a5039d6ffa` |
| `SDLTRPA1` | L08 t14 | "I'm hit!" | HaelDB | `sd/mon/legiontrooper/pain/1` | -11.4 (`DSPOPAIN`) | `2f4b26a5e4632a90ce8b8e3bb62915d2c17567e7fc28154b656574c5fb436bee` |
| `SDLTRPA2` | L08 t15 | "I'm hit!" | HaelDB | `sd/mon/legiontrooper/pain/2` | -11.4 (`DSPOPAIN`) | `249b167901c1122321c5dca0af756f15fe74c8310b372ae91928ce7b86733531` |
| `SDGENSIT` | G01 t12 | "Engage!" | kurt | `sd/mon/general/sight` | -14.0 (`DSCYBSIT`) | `99669afd3d20cc603180f4d572694ddef781f2a4ace19e4927991c36ca9154dc` |
| `SDGENSU1` | G02 t13 | "Vorwärts!" | kurt | `sd/mon/general/summon/1` | -9.6 (`DSVILSIT`) | `10184bed9a802498928bd273d5e8b47a80c6fb1764b632a7b2aef014cf6a7785` |
| `SDGENSU2` | G02 t14 | "Vorwärts!" | Thorsten | `sd/mon/general/summon/2` | -9.6 (`DSVILSIT`) | `31d103bb6d541c19090f577a01292ec7e701950139d75bdaedc059dfe2dfea87` |

**What to listen for in the engine (the PM, D26).** On the range and in
MAP01: (1) the log has no "Unknown sound"; (2) the rifleman's shot, the
Stormtrooper's pain and death and the Panzermensch's pain change from one
hit to the next (`$random`; NOT VERIFIED in our engine, though it is
Doom's own zombieman sight); (3) the Legion's shotgun against the IZh-58's
(`SDLTRATK` alt2 at `DSDSHTGN`'s level); (4) the short ones above, on
laptop speakers: the hound's bite, the Panzermensch's sight, the
Doughboy's idle drone; (5) the Panzermensch's step, one per walk cycle,
not tiring; (6) the voices of D91 and D96 vary from one time to the next
(the rifleman: idle German orders, "Kontakt!"/"Feind!"/"Da!" on sight,
"Sani…" dying; the trooper: idle radio chatter, four sight calls, "I'm
hit!" in pain; the General: "Engage!" on sight and "Vorwärts!" with the
printed order, heard across the arena); the long ones do not cut off oddly
on CHAN_VOICE (the trooper's "I'm hit!" is 1.3-1.6 s where the script
asked 0.4-0.5 s, and a second hit restarts it); the rifleman's pain, the
trooper's death and the General's pain and death are still Freedoom's and
no bed is heard.


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
| **(d) CEO voice** | The 12 voice rows, with the right accents of intent (dry vs radio vs slot). Faction identity comes cheapest here | The CEO's time. Quality of a phone microphone is fine only after processing, which is the plan | CEO ~45-90 min recording; ~1 session processing | None, once the CEO agrees in writing; a voice is personal data |
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

**As drafted (2026-10-13), superseding the proposal above in two points.**
(1) **44.1 kHz, not 22.05**: the cracks, sparks and metal rings live above
the 11 kHz a 22.05 kHz file can hold, and a one-second mono OGG costs about
10 KB either way (the 35 lumps are 470 KB as OGG q6). GZDoom resamples on
playback (**ASSUMPTION** from the engine's support of 11 and 22 kHz DMX next to
44.1 kHz OGG; not checked in the wiki). (2) **OGG from the first audition**:
`ffmpeg` is here, and the overlay should be what would ship. WAV masters are
kept beside them. Loudness is matched by a meter, not by ear (§5.9); the ear
is the CEO's.

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
| **B** | Does the CEO record the voices? | **Yes, or generates them with AI** ("me encargaré de las grabaciones y/o generar con IA lo que sea necesario"). Script: `docs/sound/VOICE-SCRIPT.md`. An AI take carries its tool and licence in the licence register |
| **C** | The General's order | **"Vorwärts."** |
| **D** | Real-language rule for the Reich | **Overruled.** Real German for the Reich, real English for the Legion; still no slogans of the regime (D11, D12). §4 rewritten |

Still owed by the CEO: the takes, and one line in chat releasing the
recorded voice under D15 (`VOICE-SCRIPT.md` §0.1).

For the PM, not the CEO: `src/lumps/LANGUAGE` still prints the placeholder
order "The General: Recruits - advance!" (EN, and its RU twin) and
`BESTIARY.md` §3 still briefs `SDRRIACT` as "a language that is not quite
German"; both are `mod-engineer`'s files and both predate D36. Listing
these sources in the sound licence file once any file ships.

**Open after the drafts (2026-10-13), for the PM.**

1. **The CEO's audition** of `docs/art/previews/2026-10-13_2029_F5_enemy-sfx-drafts.html`
   (taste, stage 4). Recommendation: listen first to `SDHNDSIT` (the
   bestiary's most important sound), the three launches `SDSTOMIS`,
   `SDDGBMIS`, `SDPZRMIS` one after the other, and `SDPZRSTP`; then the
   in-game pass on the practice range (`RANGE`, MAP02 until D62) with the overlay (§5.9), which only the PM can run
   (D26). Cost: about 15 minutes for the page, 10 for the game.
2. **`KEN-IMP` and the weapons.** The enemy drafts read 17 `KEN-IMP` files
   (§5.9), which D36 authorised. The weapon drafts being written in parallel
   (`tools/audio/gen_weapon_sfx.py`, not mine, not committed) deliberately
   leave `KEN-IMP` out because GameSynth's terms on generated sounds are NOT
   VERIFIED (§2.1). The two must not ship under different rules. My
   recommendation is to keep `KEN-IMP` (Kenney's CC0 covers his output, the
   same position as music made in a commercial DAW); the alternative is
   swapping those 17 layers for `OGA-100` metal foley, about one session.
   This is a licence question, so it is the CEO's (authority, stage 4), with
   `qa-engineer`'s licence audit.
3. **When a lump is approved**, it goes to `src/sounds/<LUMP>.ogg` and its
   `SNDINFO` line changes (`mod-engineer`), its sources go to the licence
   register (the three gibs carry Freedoom's BSD-3 notice), and the
   engine pass is owed.

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
means "drafted (§5.9), not yet auditioned by the CEO".

**Verified with the drafts (2026-10-13, evening)**, by measurement only:
lengths against every card, peaks and clipping of every WAV and decoded OGG,
the class loudness, the spectral claims listed in §5.9, that the route C
recipes build with no pack and no IWAD present, that two full runs are
byte-identical (WAVs and overlay PK3), and the SHA-256 of all 40 source files
(§5.9). **Not verified**: how any draft *sounds*; I cannot listen, and no
human has yet. Not verified either: that the overlay's `SNDINFO` overrides
the mod's in GZDoom and that `run.sh` accepts a second `-file` (the music and
weapon overlays rely on the same two facts; nobody has started the engine
for this one).

**Engine (D26).** I did not start GZDoom. Nothing entered `src/` or the PK3,
so no engine pass is owed for the mod; the in-game audition of the overlay
is the PM's (§7, open point 1).
