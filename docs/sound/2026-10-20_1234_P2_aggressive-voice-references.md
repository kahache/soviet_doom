# Aggressive male voice references for Chatterbox: candidate sources

Owner: `sound-designer`. 2026-10-20 12:34, phase P2. Research only: nothing was
downloaded, nothing is staged. Decisions this serves: **D36** (real German for
the Reich, real English for the Liberty Legion, any AI voice goes in the licence
register), **D85/D87** (Chatterbox Multilingual), **D91** (takes are flat
because Chatterbox copies the emotion of the reference clip, and the predefined
voices are calm narration).

## 0. What we are looking for and the rules applied

- **Use:** a 10-20 s clip of one male speaker, shouting or in pain, fed to
  Chatterbox as the voice prompt. The clip itself is never shipped; the
  generated takes are, under CC BY-NC-SA 4.0 (D15).
- **Licence filter** (`docs/sound/MUSIC-RIGHTS.md` §1.3): usable = public
  domain, CC0, CC BY, CC BY-NC, CC BY-NC-SA. **Rejected = CC BY-SA**, and
  anything without a stated licence. Anything else (OpenRAIL) is flagged for a
  PM/CEO decision.
- **Ethics filter:** no famous people, no real historical regime recordings
  (D11, D12), no AI-generated sources (they would chain one model's output into
  another with unclear provenance). Preferred: performers who released their voice
  explicitly for reuse, ideally for speech synthesis or for games.
- **Language matters for cloning.** The Chatterbox Multilingual README advises
  that the reference clip match the target language; otherwise the output keeps
  the accent of the reference language. It suggests `cfg_weight=0` to reduce that.
  So German lines need a German reference, English lines an English one.
  (Paraphrased from memory of the README, not re-checked in this session.)
- **Side note for the PM:** the same README recommends `exaggeration` of about
  0.7 or more and `cfg_weight` of about 0.3 for dramatic speech. Exaggeration
  amplifies the emotion already in the reference. It cannot create a shout from a
  calm reference, which is consistent with D91, but it should be raised once we
  have an aggressive reference.

## 1. Candidate table

Durations marked "~" are estimated from file size, not measured. "Clean" means
dry voice with no music. Nothing has been listened to yet.

| # | Source / URL | Author / performer | Licence (where stated) | Lang | Contents | Length | Quality | Ethics / consent | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Thorsten-Voice Dataset 2021.06 **emotional**, https://zenodo.org/records/5525023 | Thorsten Müller (voice), Dominik Kreutz (audio) | **CC0 1.0**, Zenodo licence field | DE | 300 identical phrases in 8 styles: neutral, disgusted, **angry**, amused, surprised, sleepy, drunk, whispering. ~20 min of angry speech (OpenSLR-110 listing). | 2,400 short clips | Studio, mono 22.05 kHz, normalised to −24 dB, silence trimmed. Clean. | Identifiable private person who **donated his voice for open TTS**; the page says the aim is to provide it "without any financial or licence struggle". No clause against cloning. Not famous. | **Top DE pick.** It is angry read speech, probably not battlefield shouting. |
| D2 | `Ich_koennt_kotzen.wav`, https://freesound.org/people/tontoepfer/sounds/221670/ | tontoepfer (performer not named) | **CC0**, Freesound sound page | DE | Upset man yelling «Boah, ich könnt kotzen!» | 2.6 s | WAV 48 kHz/24-bit mono, solo speech | Uploader released it for reuse; performer unnamed; not famous. | Usable, but too short alone. |
| D3 | `Schnell, schnell.aif`, https://freesound.org/people/boomerangquest/sounds/237294/ | boomerangquest | CC0 (search filter; sound page not opened) | DE | «Schnell, schnell» | ~5 s? | Unknown | Unnamed performer | Filler only; confirm licence on the page. |
| E1 | RAVDESS, speech audio, https://zenodo.org/records/1188976 | 24 professional actors (12 male: odd IDs 01-23), Ryerson Univ. | **CC BY-NC-SA 4.0**, Zenodo rights field. The description text says "CC BY"; the rights field governs. | EN (N. American) | 2 neutral sentences («Kids are talking by the door», «Dogs are sitting by the door») in 8 emotions; **angry** and **fearful** at **strong** intensity. | ~3.5 s per clip; 4 strong-angry clips per actor | Studio, 48 kHz, very clean | Actors consented to an openly licensed research database. Cloning is not addressed either way. Not famous. Same licence as ours, so credit and NC-SA are already satisfied. | **Top EN pick for timbre and anger.** The words are neutral, but only the emotion matters for the reference. |
| E2 | «Soldier Voice Acting», https://opengameart.org/content/soldier-voice-acting | kurt (uploader, apparently also the performer) | **CC-BY 3.0**, OGA licence field | EN | `battlecries.ogg` (battle cries), `wounded.ogg` (pain), plus unit selection and acknowledgements | battlecries ~20-30 s, wounded ~5-8 s | Raw "practice runs", not mixed; one commenter says the cries sound acted. | Released for game use by the performer. A 2026 comment links an **AI-generated expansion**, now pulled over licensing issues. Use only kurt's original files. | **Top EN pick for shouted words.** Credit "kurt, OpenGameArt, CC-BY 3.0". |
| E3 | «Where the Thunder Strikes - Viking Sample Pack», https://freesound.org/people/WelvynZPorterSamples/packs/34286/ | WelvynZPorterSamples (voice actor in his own Viking audio drama) | **CC0**, each sound page (e.g. 621352) | EN | 112 clips: war cries, «Hold! Shield to shield, shoulder to shoulder!», yells. Each comes **dry ("NO reverb") and wet**. | Clips 1-10 s | WAV 44.1 kHz, stereo. Use the **NO reverb** files. | Voice actor released it for reuse ("attribution never required but always very appreciated"). Not famous. | **Top EN pick for aggression.** The tone is fantasy-Viking, so check that it is not too theatrical (D11). |
| E4 | «Male Grunt/Yelling sounds», https://opengameart.org/content/male-gruntyelling-sounds | HaelDB (4 unnamed male vocalists) | **CC0** or OGA-BY 3.0 (dual-listed; pick CC0) | none (wordless) | 4 voices, about 10-12 screams and grunts each; tags death, pain | Short clips, 9.7 MB zip | Recorded on a Neumann mic through an Avalon preamp; commenters call it "almost too realistic" | Released for reuse; performers unnamed. | **Best pain/death reference** (any language). Use one vocalist only. |
| E5 | Kenney «Voiceover Pack: Fighter», https://opengameart.org/content/voiceover-pack-fighter-40-taunts | Kenney; "professional voice actor" (unnamed) | **CC0** | EN | Announcer lines («Fight!», «Kill him», «Final round») | ~36 short OGGs | Clean, normalised | Professional actor, released for game use | Backup only: it is an announcer voice, energetic rather than angry. |
| E6 | Kenney «Voiceover Pack (40+ lines)», https://opengameart.org/content/voiceover-pack-40-lines | Kenney; male and female actors | **CC0** | EN | «Cover me!», «Fire in the hole!», «Mission completed»… | 92 OGGs | Clean | As E5 | Backup; probably calm-energetic. |
| E7 | qubodup «military voice samples», https://freesound.org/people/qubodup/packs/13895/ (e.g. «To War!» 161967, «Fire in the Hole! 3x» 855894, «Whoo!» 161340) | Real US service members, extracted by qubodup from US-government video | **CC0** on the page; the source is US federal public domain | EN | Drill-sergeant shouts, «Fire in the hole!» | «To War!» = 2.2 s; others short | Field audio: wind, gunfire, radio | Real identifiable people who never consented to cloning, though not famous. Legally PD, ethically the weakest of the usable ones. | Last resort. |
| E8 | Veridiansunrise `Drillsarge_PresentArms_TenHut.wav` (162010), `Sergeant_Eyesright.wav` (162009) | Veridiansunrise | CC0 (search filter; pages not opened) | EN | Drill commands | short | Unknown | Unknown | Check before use. |
| E9 | JD_Brick_Productions «soldier shouts "germans!"», https://freesound.org/people/JD_Brick_Productions/sounds/620472/ | uploader (self-made for his video) | **CC0** | EN | «Germans!» | 2.7 s | WAV 48 kHz | Self-recorded, released | Filler for E-set. |
| R1 | «Dialogs» Russian emotional corpus, https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations | Langswap; 3 theatre actors, one male («Dima», 6.2 h) | **OpenRAIL** (dataset card; full terms in LICENSE.md, not read) | RU | Utterances labelled with 12 styles incl. **angry**, fear, arrogance | many | Studio, 44.1 kHz/16-bit | Card says the actors gave **written informed consent for open release and lawful use, including commercial**. OpenRAIL's use restrictions (no unlawful use, harassment, disinformation) are not in our §1.3 list. | **Best RU option, but blocked on a licence decision** (§3). |
| R2 | `rukivehr.wav` («Руки вверх»), https://freesound.org/people/DracoN12/sounds/493228/ | DracoN12 | CC0 (search filter) | RU | «Hands up», tagged shout/military | short | Unknown | Unknown | Filler; check the page. |

### Rejected and why

| Source | Reason |
|---|---|
| VoiceBosch «Radio Soldier» (OGA) | CC BY-SA 4.0: §1.3. |
| Simonus18 «Battle cry scream 01-04» (Freesound) | AI-generated; provenance chain. |
| craigsmith «G30-76 Crowd Chant at Hitler Rally» | Real Nazi rally (D11, D12), crowd. |
| «Sci-Fi Trooper Voice Pack» (Angus Macnaughton, CC BY 4.0) | Licence OK but processed to a space-marine filter; it would clone the filter. |
| «aargh male screams» (OGA, CC-BY 3.0 mix) | Wilhelm-style comic screams, 3 different authors in one zip. |
| Dusha (Sber, RU) | Custom licence in PDFs; crowd-sourced speakers. |
| EmoDB (Berlin, DE anger) | No explicit licence found ("no formal licence agreement"); assume reserved. |
| Mozilla Common Voice (any language) | CC0, but calm read speech by volunteers who did not consent to cloning; its terms forbid identifying speakers. |
| SampleFocus, Soundstripe, Artlist, Shockwave-Sound, Epic Stock Media, itch.io paid packs | Royalty-free or commercial licences: not CC, not redistributable terms. |
| Freesound «deutsch schreien» CC0 search | 0 results; German shouting in CC0 is scarce. |

## 2. Top picks per language, with download URLs

### German

1. **Thorsten emotional, `angry` style (D1).** Download:
   `https://zenodo.org/records/5525023/files/thorsten-emotional_v02.tgz?download=1`
   (399.3 MB, md5 `f19585f3759c6d026757c46024a37aa4`). Mirror: https://openslr.org/110/.
   Cut: extract only the angry folder. Pick the 4-6 most heated clips by ear
   (exclamations, short sentences). Concatenate them with 0.25 s gaps to
   12-18 s. Upsample to 24 kHz mono for Chatterbox (its sample rate). Do not
   add EQ: the material is already normalised.
2. **Thorsten `angry` + tontoepfer (D1 + D2): not recommended.** These are two
   different men. Never mix speakers in one reference. Use D2 only for a German
   take where pure rage matters more than timbre consistency: loop it 2-3 times
   with different gaps (about 8 s), and expect a weaker clone.
3. **Fallback if (1) sounds too polite:** use the strongest English reference
   (E3 or E2) with `language_id="de"` and `cfg_weight=0`, then judge the accent by
   ear. An English-accented German soldier is a known risk (§0).
4. **The real fix stays D85:** the CEO's own shouted German (15 s).
   `VOICE-SCRIPT.md` §0.2-0.4 already says how to record it.

### English

1. **WelvynZPorterSamples Viking pack, NO-reverb files (E3).** Example URLs:
   `https://freesound.org/people/WelvynZPorterSamples/sounds/623447/`
   («Hold! Shield to shield, shoulder to shoulder!», dry) and
   `https://freesound.org/people/WelvynZPorterSamples/sounds/623449/`
   (Kingly Yell, dry). Browse the 112-clip pack for the dry war cries;
   «War Cry 3» (621352) is only the wet version. Freesound requires a free
   login to download. Cut: 4-6 dry clips, 12-18 s total, 0.25 s gaps. Avoid
   the pitched-down «LOW» variants (they would clone the pitch shift). Fold
   stereo to mono.
2. **kurt «Soldier Voice Acting» (E2).**
   `https://opengameart.org/sites/default/files/battlecries.ogg`, plus
   `https://opengameart.org/sites/default/files/wounded.ogg` for pain.
   Cut: battlecries.ogg alone probably gives 10-20 s once trimmed. Keep the
   loudest, least "acted" cries. Make a second reference from wounded.ogg
   (padded with the start of battlecries.ogg if it is under 10 s) for the
   pain/death lines. Credit kurt, CC-BY 3.0.
3. **RAVDESS strong-angry, one male actor (E1).**
   `https://zenodo.org/records/1188976/files/Audio_Speech_Actors_01-24.zip?download=1`
   (208.5 MB, md5 `bc696df654c87fed845eb13823edef8a`). Files are named
   `03-01-EE-II-SS-RR-AA.wav`: EE `05` = angry and `06` = fearful; II `02` =
   strong; AA odd = male. For one actor, concatenate the 4 files
   `03-01-05-02-0{1,2}-0{1,2}-AA.wav` (about 14 s). For pain or panic, use
   `06` (fearful, strong). Audition several male actors and keep the
   gruffest. Credit as the dataset asks (Livingstone & Russo 2018, CC BY-NC-SA 4.0).
4. **HaelDB yelling, one vocalist (E4), pain/death only.**
   `https://opengameart.org/sites/default/files/yelling%20sounds.zip`. Cut: all
   10-12 clips of one vocalist, 0.2 s gaps, trimmed to 10-15 s. Wordless, so it
   works as the pain reference for any language. For German pain lines, check
   that the accent does not drift (§0).
5. Backup: Kenney Fighter (E5),
   `https://opengameart.org/sites/default/files/kenney_voiceoverFighter.zip`.

### Russian (bonus)

1. **Dialogs corpus, speaker Dima, `angry` label (R1)**, only once the licence
   question in §3 is settled. Repository:
   `https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations`.
   Filter `metadata.csv` for speaker Dima and style angry (also try fear and
   arrogance). Cut 4-6 utterances to 12-18 s, mono 24 kHz.
2. HaelDB pain reference (E4) for Russian pain lines (wordless).
3. Fallback: `rukivehr.wav` (R2) looped, after checking its page.

## 3. Decisions needed (PM → CEO)

1. **OpenRAIL for R1.** The dataset is excellent on consent, but OpenRAIL is not
   on the §1.3 list. Its use restrictions can travel to derivatives, which may
   clash with plain CC BY-NC-SA on the generated takes. Read LICENSE.md first.
   Proposal: Russian stays out unless the CEO accepts it.
2. **Credits.** E1 (CC BY-NC-SA) and E2 (CC BY) need a line in the licence
   register and the credits for each generated take that used them, as D36
   already requires for AI voices: tool + model + reference clip + its licence.
3. **Freesound login.** Freesound downloads need an account. Creating accounts
   is the CEO's job, not an agent's; OpenGameArt and Zenodo links download without one.

## 4. How to cut a 10-20 s reference (any source)

The local tools are ffmpeg and/or Audacity. File paths go in `work/audio/voice_refs/`
(gitignored, never in `src/`).

1. **One speaker only.** Never mix two people, even if both are angry.
2. **Dry and clean:** no reverb, music, gunfire or radio filter (Chatterbox
   clones the room too). Take the "NO reverb" variants.
3. Trim leading and trailing silence. Cap internal silences at about 0.3 s:
   ```
   ffmpeg -i in.wav -af "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.3:stop_threshold=-45dB" trimmed.wav
   ```
4. Concatenate clips (list file with `file 'a.wav'` lines, short silences
   between):
   ```
   ffmpeg -f concat -safe 0 -i list.txt -ac 1 -ar 24000 -af "loudnorm=I=-18:TP=-2" ref_<lang>_<source>.wav
   ```
   Peak at least 2 dB below full scale. **Never clip.** A distorted reference clones the
   distortion.
5. Target 12-18 s. Under 8 s the timbre is unstable; over 20 s adds nothing.
6. Make **two references per voice**: *orders* (shouted words) and *pain*
   (screams). Pain/death lines were the worst in D91.
7. Record provenance for each reference in `work/audio/voice_refs/REFS.csv`:
   source URL, licence, SHA-256 of the original download, and which clips went in.

## 5. What was not verified

- Nothing was listened to. Every quality judgement comes from page text.
- Durations of E2, E3 (other than 621352), E4 and E8 are not stated on the pages.
- The licences of D3, E8 and R2 were seen only through Freesound's CC0 search
  filter, not on their own pages.
- The OpenRAIL LICENSE.md for R1 was not read.
- How intense the Thorsten «angry» set is (angry reading vs shouting) is
  unknown until it is heard.

## Sources

- Thorsten emotional: https://zenodo.org/records/5525023, https://openslr.org/110/
- RAVDESS: https://zenodo.org/records/1188976
- OpenGameArt: https://opengameart.org/content/soldier-voice-acting,
  https://opengameart.org/content/male-gruntyelling-sounds,
  https://opengameart.org/content/voiceover-pack-fighter-40-taunts,
  https://opengameart.org/content/voiceover-pack-40-lines,
  https://opengameart.org/node/115876, https://opengameart.org/content/aargh-male-screams
- Freesound: https://freesound.org/people/WelvynZPorterSamples/packs/34286/,
  https://freesound.org/people/WelvynZPorterSamples/sounds/621352/,
  https://freesound.org/people/qubodup/packs/13895/,
  https://freesound.org/people/qubodup/sounds/161967/,
  https://freesound.org/people/tontoepfer/sounds/221670/,
  https://freesound.org/people/JD_Brick_Productions/sounds/620472/
- Dialogs RU: https://huggingface.co/datasets/langswap/dialogs-ru-emotional-conversations
- Dusha: https://github.com/salute-developers/golos/tree/master/dusha
