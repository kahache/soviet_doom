# Voice script — the enemy voice takes, for the CEO

Living document. Owner: `sound-designer`. Created 2026-10-13 (F5) under
**D36**: the CEO provides the enemy voices, recorded in person or generated
with AI; the Reich speaks **real German**, the Liberty Legion **real
English**; the General's order is **"Vorwärts."**; D11 and D12 still bind
(real military callouts and combat cries, never the regime's slogans).
Russian mirror: `docs/ru/sound/VOICE-SCRIPT.md` (D7, D34: synced in a batch
at the phase close; re-sync after any edit here).

Where the lumps, the processing chains and the rights live:
`docs/sound/ENEMY-SOUNDS.md` (§4 voice rules and chains, §5 the cards).
This document only says **what to say and how to record it**. The
recording instructions come first (§0) and are addressed to the CEO; like
every doc they are in English (D7, D129), while the chat with him stays in
Spanish.

---

## 0. Instructions for the CEO

### 0.1 What needs doing, in five lines

1. Record (or generate with AI) the **22 mandatory rows** of the tables in
   §1 (lines and cries): **89 takes** in total. There are 4 optional creature
   rows, 12 more takes (§1.4).
2. Estimated time: **40-55 minutes** in total with a phone, in a single
   session (about 20-25 of recording, the rest set-up, volume test and
   listening back), plus 10 minutes to drop the files. This is my
   estimate, not measured; the calculation is in §1.5.
3. Drop the files in `work/audio/voice_takes/` (it is gitignored; it does
   not go into git or the PK3) with the names from §0.5.
4. Write one line in the chat: «Las tomas de voz son mías y las publico
   bajo CC BY-NC-SA 4.0 (D15)» (The voice takes are mine and I publish them
   under CC BY-NC-SA 4.0 (D15)). Your recognisable voice is personal data:
   without that line it is not used.
5. If you use AI for any take: fill in the log in §0.7. Without a log it
   is not used.

Afterwards I cut, pick the best take of each row, process it (§2) and bring
it back for you to listen to before anything enters `src/sounds/`.

### 0.2 The phone

- **Format:** the highest quality the app offers. On iPhone, *Settings →
  Voice Memos → Audio Quality → Lossless*. On Android, the system recorder
  at high quality, or any app that records **WAV**.
- WAV at 44.1 or 48 kHz is ideal; if the phone only gives M4A/AAC, that is
  fine, at its maximum quality. **Do not convert the format yourself**: send
  me the original.
- **No effects:** no noise filter, no "voice enhancement", no normalising,
  no trimming. I do all of that; if it arrives processed it cannot be
  undone.
- Airplane mode during the session (a notification ruins a take).

### 0.3 The room

- A **small room with soft things in it**: a bedroom with an open wardrobe
  full of clothes, curtains, a bed. **Never** a bathroom, kitchen, hallway
  or empty living room: the echo sticks to the voice and the Reich has to
  sound **dry**.
- Turn off the fan, the air conditioning, any noisy computer; move away from
  the fridge and from the window onto the street.
- At the start of each session, record **5 seconds of silence** of the room
  without moving (I use it to clean up the background noise).

### 0.4 Distance and voice

- The phone resting on something stable (a pile of books), with the
  microphone (at the very bottom on almost all phones) **about a hand and a
  half away, 20-30 cm**, and a little to the side, at about 45°, so that
  "p" and "t" do not pop.
- **Shouts** (the rows marked "loud"): lean back to **40-50 cm**. Before the
  session do a test with the loudest shout ("Feind!") and listen to it: if
  it sounds broken or scratchy, move further away. A clipped take cannot be
  fixed.
- **The General**: close, 20 cm, and **quiet**. Do not force a deep voice:
  I lower the pitch afterwards (−4 semitones). Natural voice, slow, calm.
- Between takes, **one second of silence**. Vary each take a little
  (shorter, more tired, drier): different takes are worth more than
  repeated ones.
- Performance: they are **soldiers, not movie villains**. No exaggerated
  accent, neither a caricature German nor a Texan: the tone of the game is
  serious (D11).

### 0.5 Files and names

- **One file per row** of the tables, with all its takes one after another
  (separated by that second of silence). I cut them.
- Name: `<row>_<lump>_<date>.<ext>`, for example
  `R04_SDRRISIT_20261014.wav` or `G02_SDGENSUM_20261014.m4a`.
- If a row comes from AI: `<row>_<lump>_ai_<tool>_<date>.<ext>`, for
  example `L04_SDLTRSIT_ai_toolX_20261014.wav`.
- The room's silence: `ROOMTONE_<date>.<ext>`.
- Everything in **`work/audio/voice_takes/`** (create it if it does not
  exist). If you record in several sessions or rooms, one subfolder per
  session (`work/audio/voice_takes/2026-10-14/`), each with its `ROOMTONE`.
- Optional, a `work/audio/voice_takes/NOTES.txt` with: date, phone, app and
  room. It helps me match sessions.

### 0.6 German pronunciation (approximate, for a Spanish speaker)

| Phrase | Roughly pronounced | Watch out |
|---|---|---|
| **Vorwärts.** | «FÓR-verts» | The "w" sounds like "v"; the "ä" is an open "e"; the final "r" of "vor" is almost silent; it ends in a dry "ts". |
| Feind! | «FAINT» | A single syllable, the final "d" sounds like "t". |
| Da! | «DAA» | |
| Kontakt! | «kon-TAKT» | |
| Stellung halten. | «SHTÉ-lung JÁL-ten» | Initial "St" = "sht"; the "h" is aspirated, soft, not a strong Spanish "j". |
| Augen auf. | «ÁU-guen AUF» | |
| Ruhe da hinten. | «RÚ-e da JÍN-ten» | Same soft "h". |
| Sani… | «SÁ-ni» | Soldiers' short form of *Sanitäter*, "medic". |

If you are unsure about the pronunciation, an AI voice in German reading the
phrase is a good reference by ear, even if you then record it yourself.

### 0.7 If you use AI

Any generated voice goes into the licence register like any other asset
(D36). **For every generated file** note, in
`work/audio/voice_takes/AI-LOG.csv` (or in the chat), one line with:

| Field | Example of what to put |
|---|---|
| file | `L04_SDLTRSIT_ai_toolX_20261014.wav` |
| tool | product name and website |
| version or model | the exact model/version name the tool shows |
| date | the day it was generated |
| account plan | free or paid (in many tools it changes the rights) |
| licence of use | URL of the terms, the date you read them and **the literal sentence** that says what you may do with the generated audio |
| voice | which voice: from the catalogue (its name/ID) or cloned **from your own voice** |
| text or prompt | the exact text and any style instruction |
| settings | language, stability, style, seed, if they exist |

Rules, so that the take is usable:

- The terms must allow you to **use and redistribute** the audio inside a
  mod published under **CC BY-NC-SA 4.0** (D15). If the terms only allow
  personal use, ask for an incompatible attribution, or forbid
  redistributing it in a package, **that take is no good**: tell me and we
  will look for another route.
- **Never clone another person's voice** (actors, historical figures,
  acquaintances). Only catalogue voices or your own voice.
- Keep the file **exactly as it comes out** of the tool, unedited.
- I do not recommend any specific tool: I have not read the terms of any
  of them. I check them myself from what you note down.

### 0.8 What is not recorded (D11, D12, D36)

- **Nothing from the regime**: no salutes, no party offices or titles, no
  slogans, no songs, no catchphrases. Only military orders and combat cries
  like those of any army.
- **Nothing that refers to real victims**: no words associated with roundups,
  deportations or camps (for example "Raus!" or "Schnell!" shouted at
  people). That is why they are not in the script even though they are movie
  clichés.
- On the Legion's side, symmetrically: no patriotic slogans; only radio
  procedure and combat warnings.
- If you think of a better phrase than mine, go ahead, with the same
  rule: short, military, no regime. Note it in `NOTES.txt` with its
  translation.

---

## 1. The script

How to read the tables. **Row** is the file prefix (§0.5). **Moment** is the
engine event (`sight` = alert, `active` = idle, `pain`, `death`, `summon` =
the General's order). **Dur.** is the target length of the *finished*
sound after cutting; the raw take may be longer. **Takes** is how many to
record in that file. "Loud" means step back to 40-50 cm (§0.4). Lines in
*italics* in the line column are wordless.

Several rows feed the same lump: they are alternatives. Since N9e (D86,
D91) a sound with several approved takes plays a random one each time
(`SNDINFO` `$random`, the syntax of gzdoom.pk3's own zombieman sight;
`docs/sound/ENEMY-SOUNDS.md` §5.12), so every approved take of every row
of a lump ships; §1.6 lists them.

### 1.1 Fourth Reich rifleman (`SD_ReichRifleman`) — German, chain `REICH-DRY`

Delivery: dry, clipped, flat, disciplined. A soldier, not a villain.

| Row | Lump | Moment | Line (German) | Translation | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| R01 | `SDRRIACT` | idle | Stellung halten. | Hold the position. | Muttered to a comrade, low, bored; heard through a door, not meant to be followed | 1.0-1.5 s | 3 |
| R02 | `SDRRIACT` | idle | Augen auf. | Eyes open. | Same, quieter | 0.8-1.2 s | 3 |
| R03 | `SDRRIACT` | idle | Ruhe da hinten. | Quiet back there. | Same, irritated | 1.0-1.5 s | 3 |
| R04 | `SDRRISIT` | alert | Feind! | Enemy! | One sharp bark, loud. Heard many times a map: must not be tiring | ≤ 0.5 s | 5 |
| R05 | `SDRRISIT` | alert | Da! | There! | Shortest possible bark, loud | ≤ 0.4 s | 3 |
| R06 | `SDRRISIT` | alert | Kontakt! | Contact! | Bark, loud | ≤ 0.6 s | 3 |
| — | `SDRRIATK` | attack | *(no voice)* | — | The rifle crack; our synthesis (`ENEMY-SOUNDS.md` §5.1) | — | 0 |
| R07 | `SDRRIPAI` | pain | *Grunt, cut off ("ngh—")* | — | Hit, surprised, breath knocked out; no word | 0.2-0.3 s | 5 |
| R08 | `SDRRIDTH` | death | *An exhale that breaks* | — | Air going out, a catch in the throat, falling; **no scream** | ~1 s | 5 |
| R09 | `SDRRIDTH` | death | Sani… | Medic… | Optional alternative to R08: barely said, fading | ~1 s | 3 |

### 1.2 Liberty Legion trooper (`SD_LegionTrooper`) — English, chain `LEGION-RADIO`

Delivery: radio procedure, neutral General American, professional and
flat. Speak as if into a handset: a hand cupped near the mouth helps. Crisp
consonants, because the radio will cut the lows and the highs.

| Row | Lump | Moment | Line (English) | Translation | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| L01 | `SDLTRACT` | idle | Sector four, clear. | Sector four, clear. | Routine report, bored | 1.2-1.6 s | 3 |
| L02 | `SDLTRACT` | idle | Copy. Holding position. | Received. We are holding position. | Routine, a bit tired | 1.2-1.8 s | 3 |
| L03 | `SDLTRACT` | idle | Command, say again? | Command, say again. | Didn't catch it | 1.0-1.4 s | 3 |
| L04 | `SDLTRSIT` | alert | Contact! | Contact! | One clipped word, loud | ≤ 0.6 s | 5 |
| L05 | `SDLTRSIT` | alert | Hostile, front! | Hostile, front! | Fast, loud | ≤ 0.7 s | 3 |
| L06 | `SDLTRSIT` | alert | Got movement! | Movement! | Fast, loud | ≤ 0.7 s | 3 |
| — | `SDLTRATK` | attack | *(no voice)* | — | The shotgun; our synthesis (§5.2 of `ENEMY-SOUNDS.md`) | — | 0 |
| L07 | `SDLTRPAI` | pain | *Grunt ("agh—")* | — | Hit; no word | ~0.3 s | 5 |
| L08 | `SDLTRPAI` | pain | I'm hit! | I'm hit! | Alternative to L07, strained | 0.4-0.5 s | 3 |
| L09 | `SDLTRDTH` | death | *A choked exhale, falling* | — | The voice drops; I add the signal dying | ~1 s | 5 |

### 1.3 The General (`SD_General`) — English, and one German order; chain `GENERAL-SLOT`

He is the Legion's officer commanding both factions (`docs/engine/BESTIARY.md`
§9); he speaks English, and gives the Reich recruits their order in their
own language. **He never shouts.** Low, slow, calm, close to the phone
(20 cm). Natural pitch: I lower it later.

| Row | Lump | Moment | Line | Translation | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| G01 | `SDGENSIT` | alert | Engage. | Attack. | Calm, unhurried; an order, not a cry | 1.0-1.5 s | 5 |
| G02 | `SDGENSUM` | the order (summon) | **Vorwärts.** | Forward. | **The one line the player must understand.** Calm, final, as if it were obvious. A full stop, not an exclamation mark | ≤ 1.2 s | 8 |
| — | `SDGENMIS` / `SDGENEXP` / `SDGENACT` | attack / impact / idle | *(no voice)* | — | Mechanism and salvo; our synthesis | — | 0 |
| G03 | `SDGENPAI` | pain | *Clipped grunt ("hm.")* | — | Annoyed more than hurt; not a cry | 0.2-0.4 s | 5 |
| G04 | `SDGENDTH` | death | *Long exhale winding down into a low hum that stops* | — | The voice runs down like a machine; I add the mechanism failing. May ring long | 2.5-4 s | 5 |

### 1.4 Optional: creature layers (wordless)

The CC0 packs cover these (`docs/sound/ENEMY-SOUNDS.md` §5.3-§5.6). A human
layer underneath makes them less "library". **Only if there is time left.**

| Row | Lump | Moment | What to do | Dur. | Takes |
|---|---|---|---|---|---|
| C01 | `SDSTOSIT` | alert | A rasping snarl from the throat, as if through a damaged mask | ~0.7 s | 3 |
| C02 | `SDHNDSIT` | alert | A rising shriek-snarl, ending high; not a dog, not a wolf | ≥ 1 s | 3 |
| C03 | `SDDGBSIT` | alert | A hollow wail **with your face inside a metal pot or bucket** (literally) | ~1 s | 3 |
| C04 | `SDPZRSIT` | alert | The lowest roar you can do, slow | ~1.5 s | 3 |

### 1.5 Totals

| Group | Rows | Takes |
|---|---|---|
| Reich rifleman | 9 | 33 |
| Legion trooper | 9 | 33 |
| General | 4 | 23 |
| **Required** | **22** (16 spoken lines, 6 wordless) | **89** |
| Optional creatures | 4 | 12 |

The 22 required rows feed 12 lumps (rifleman ACT, SIT, PAI, DTH; trooper
ACT, SIT, PAI, DTH; General SIT, SUM, PAI, DTH), the twelve voice rows of
`ENEMY-SOUNDS.md` §5.8.

Recording time, worked out (assumptions, not measurements). Speech alone is
small: 89 takes at about two seconds each is **~3 minutes** (the General's
death, 2.5-4 s, pulls it up slightly). Real time is the gaps:

| Item | Assumption | Time |
|---|---|---|
| Speech | 89 takes × ~2 s | ~3 min |
| Pause, breath and a clean silence before and after each take | ~4 s × 89 | ~6 min |
| Retries (a flubbed or noisy take, repeated) | +50 % of the above | ~4-5 min |
| Changing delivery or distance between rows (loud 40-50 cm, calm 20 cm, §0.4) | 22 rows × ~30 s | ~11 min |
| **Recording** | | **~20-25 min** |
| Set-up, loudness test (§0.4), listening back | | ~15-20 min |
| **Session** | | **~40-55 min** |

The earlier figures (15-20 minutes of recording, 30-45 in total) did not
account for the row changes and were too low.
Estimate, not measured: the first real session replaces it.

### 1.6 Installed (D91, D96, D110, D118): twelve of twelve

The takes are Chatterbox Multilingual (D87; `work/audio/voice_takes/`,
`AI-LOG.csv`): D91's with predefined voices, D96's cloned from shouted
references (Thorsten-Voice "angry", CC0; kurt's "Soldier Voice Acting",
CC-BY 3.0; HaelDB, CC0), and D110's, the wordless rows, cloned from the
same references (`work/audio/voice_takes/p2/`), and D118's, G04 redrafted
(`work/audio/voice_takes/p2b/`, kurt's reference). **Twelve of the twelve
enemy voices are ours**: since D118 no enemy voice plays a Freedoom lump.
The D96 takes say their lines with an exclamation mark ("Vorwärts!", not
the full stop of G02): that is what the CEO approved.

| Lump (card) | Rows and takes | Ships as | `SNDINFO` |
|---|---|---|---|
| `SDRRIACT` | R01 t13, R02 t11, R03 t14 (D96) | `SDRRIAC1`-`3` | `$random sd/mon/reichrifleman/active` |
| `SDRRISIT` | R06 t01, t03 (D91); R04 t12, t13, R05 t12 (D96) | `SDRRISI1`, `3`, `4`-`6` | `$random sd/mon/reichrifleman/sight` |
| `SDRRIPAI` | R07 t06, t02 (D110) | `SDRRIPA1`-`2` | `$random sd/mon/reichrifleman/pain` |
| `SDRRIDTH` | R09 t12 (D96) | `SDRRIDTH` | `sd/mon/reichrifleman/death` |
| `SDLTRACT` | L01 t01, t03, L02 t01-t03 (D91); L03 t12 (D96) | `SDLTRAC1`-`6` | `$random sd/mon/legiontrooper/active` |
| `SDLTRSIT` | L04 t12, t14, L05 t13, L06 t13 (D96) | `SDLTRSI1`-`4` | `$random sd/mon/legiontrooper/sight` |
| `SDLTRPAI` | L08 t14, t15 (D96) | `SDLTRPA1`-`2` | `$random sd/mon/legiontrooper/pain` |
| `SDLTRDTH` | L09 t01, t02, t04 with its tail cut (D110) | `SDLTRDT1`-`3` | `$random sd/mon/legiontrooper/death` |
| `SDGENSIT` | G01 t12 (D96) | `SDGENSIT` | `sd/mon/general/sight` |
| `SDGENSUM` | G02 t13, t14 (D96) | `SDGENSU1`-`2` | `$random sd/mon/general/summon`, played with the printed order |
| `SDGENPAI` | G03 t06, t04 (D110) | `SDGENPA1`-`2` | `$random sd/mon/general/pain` |
| `SDGENDTH` | G04 t01, t07, t08, t05, t12 (D118; D110's round all NO) | `SDGENDT1`-`5` | `$random sd/mon/general/death` |

---

## 2. What happens to the takes afterwards

The recipes are owned by `docs/sound/ENEMY-SOUNDS.md` §4; this is what they
mean for the performance.

| Faction | Chain | What I do | What it means for you |
|---|---|---|---|
| Reich (rifleman) | `REICH-DRY` | High-pass 80 Hz, light saturation, **no reverb**, −2 to −3 semitones, presence at 2-3 kHz | The room's echo cannot be removed and will be heard: record in the deadest room you have |
| Liberty Legion (trooper) | `LEGION-RADIO` | Band-pass 400-3200 Hz, 8-bit crush, clipping, a vocoder edge, a squelch burst at start and end | Only the middle of the voice survives: consonants carry the words, so say them clearly |
| The General | `GENERAL-SLOT` | −4 semitones, narrow band-pass 500-2500 Hz, a short comb (the slot in his face plate), a slow 1.2 s tail | Calm and close; no forced bass. Leave the end of each line clean so the tail can ring |
| Creatures (optional) | per actor, `ENEMY-SOUNDS.md` §5 | Layered under the CC0 material and pitched | Commit fully: odd is good |

Every finished lump comes back to the CEO for listening before anything
enters `src/sounds/`, as with textures and music.

---

## 3. Open points for the PM (not the CEO)

- **Closed (2026-10-13).** The printed order is aligned with the spoken one:
  `src/lumps/LANGUAGE` has `SD_GENERAL_ORDER = "The General: Vorwärts!";`
  (line 236) and the `[ru]` twin `"Генерал: Vorwärts!"` (line 394), and
  `src/zscript/monsters/general.zs` prints it (`A_PrintBold`, line 127).
  Cosmetic only: the spoken line is "Vorwärts." with a full stop (G02), the
  printed one ends with "!"; and the comment above the key in `LANGUAGE`
  still says "Placeholder wording until the CEO picks the line", which is
  `mod-engineer`'s to reword.
- **Closed (2026-10-13).** `docs/engine/BESTIARY.md` §3, `SDRRIACT` row,
  now says "a muttered order in real German (D36; lines in
  `docs/sound/VOICE-SCRIPT.md`)" (line 368); the "not quite German" wording
  is gone.
