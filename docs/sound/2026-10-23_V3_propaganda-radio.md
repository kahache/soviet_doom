# V3 B5: propaganda radio ambience, drafts and integration proposal

Date: 2026-10-23. Author: `sound-designer`. Dated snapshot, not a living
document. Scope: V3 item **B5** (D120, `docs/ICEBOX.md` "V3 scope"):
loudspeakers in some rooms that play as the player comes near.

**Status: drafts only. Nothing is installed, nothing in `src/` or `assets/`
is touched.** The lines are AI voices, so they go to the CEO's ear first:
D113's standing approval covers composed MIDI and procedural textures, not
voices. Listening page: `work/audio/preview/radio_listening.html` (local,
gitignored `work/`).

Labels: **VERIFIED** = measured or read today; **NOT VERIFIED** = believed,
not checked (everything about the engine is NOT VERIFIED, D26: no agent
starts GZDoom).

---

## 1. What was made

| Item | Where (all under the main checkout's `work/audio/`) |
|---|---|
| Generator, processing and page script | `candidates/radio/gen_radio.py` |
| 16 lines x 3 takes, raw as Chatterbox gave them | `candidates/radio/raw/*.wav` + one `*.json` per take (request, seed, reference, model) |
| The same takes through the radio chain, OGG | `candidates/radio/RAD<nn>_SDRAD<nn>_ai_chatterbox_20261023_t0<k>.ogg` |
| Three station jingles (synthesis) | `candidates/radio/RADJ_J1..J3_synth_20261023.ogg` |
| Demo broadcast, time-signal demo (to hear only) | `candidates/radio/RAD_demo_broadcast_20261023.ogg`, `RAD16_pips_demo_20261023.ogg` |
| AI log (VOICE-SCRIPT §0.7 fields) | `candidates/radio/AI-LOG.csv` (UTF-8 with BOM) |
| Measurements and ranking | `candidates/radio/METRICS.json` |
| References and their provenance | `candidates/radio/ref/` (`REF.json`) |
| Listening page, OK / NO / ? per take | `preview/radio_listening.html` (UTF-8 **with BOM**, so a phone shows the accents) |

## 2. The script

Sixteen lines in the voice of a 1970s Radio Moscow announcer: war reports,
slogans, civil-defence notices and a few dry, bureaucratic ironies (D11:
serious tone; the irony is in the officialese, never a joke). Written for
this mod: **no real leader's name, no literal historical phrase** (the
famous wartime openings and the 1941 slogans were avoided on purpose), and
the lore's own line "they fight for profit, we fight for everyone"
(`LORE.md`) is RAD07. Numbers are written as words so the model reads them.
The Spanish translations are on the page.

| Code / lump | Voice | Kind | Russian | English |
|---|---|---|---|---|
| RAD01 `SDRAD01` | M | war report | Передаём сводку с фронта. Наши части отбросили захватчиков за Уральский хребет. | Here is the report from the front. Our units have driven the invaders back beyond the Ural range. |
| RAD02 `SDRAD02` | M | war report | На Волге, у Жигулёвской плотины, наши части уничтожили крупную группировку противника. | On the Volga, at the Zhiguli dam, our units have destroyed a large enemy force. |
| RAD03 `SDRAD03` | F | civil defence | Внимание, граждане! Объявлена воздушная тревога. Немедленно пройдите в ближайшее убежище. | Attention, citizens! An air-raid alert has been declared. Go to the nearest shelter at once. |
| RAD04 `SDRAD04` | F | civil defence | Не подходите к упавшим предметам. О любых находках сообщайте в штаб гражданской обороны. | Do not approach fallen objects. Report any finds to the civil defence headquarters. |
| RAD05 `SDRAD05` | M | slogan | Враг силён, но народ сильнее. Все на защиту Родины! | The enemy is strong, but the people are stronger. Everyone to the defence of the Motherland! |
| RAD06 `SDRAD06` | F | slogan | Товарищи рабочие! План пятилетки будет выполнен — несмотря ни на что. | Comrade workers! The five-year plan will be fulfilled, whatever happens. |
| RAD07 `SDRAD07` | M | slogan (lore) | Захватчики воюют за прибыль. Мы воюем за всех. | The invaders fight for profit. We fight for everyone. |
| RAD08 `SDRAD08` | F | civil defence, ironic | Сообщение гражданской обороны: водопроводная вода безопасна. Перед употреблением кипятить сорок минут. | A civil defence announcement: tap water is safe. Boil for forty minutes before use. |
| RAD09 `SDRAD09` | M | news, ironic | Парад в честь шестидесятой годовщины Великого Октября состоится в назначенный срок. Парад не отменяется. | The parade for the sixtieth anniversary of the Great October will take place as scheduled. The parade is not cancelled. |
| RAD10 `SDRAD10` | F | weather, ironic | Прогноз погоды. На Урале облачно, местами осадки. Местами — падение посторонних предметов с неба. | The weather forecast. Cloudy over the Urals, with rain in places. In places, foreign objects falling from the sky. |
| RAD11 `SDRAD11` | M | war report | Гарнизон космодрома «Заря-7» продолжает удерживать позиции. Слава его защитникам! | The garrison of the Zarya-7 cosmodrome is still holding its positions. Glory to its defenders! |
| RAD12 `SDRAD12` | F | civil defence, ironic | Если вы встретили существо в каске, не вступайте с ним в разговор. Сообщите в милицию. | If you meet a creature wearing a helmet, do not enter into conversation with it. Inform the militia. |
| RAD13 `SDRAD13` | M | slogan | Каждый завод — крепость. Каждый дом — рубеж обороны. | Every factory a fortress. Every house a line of defence. |
| RAD14 `SDRAD14` | F | appeal | Товарищи! Фронту нужна ваша кровь. Пункты сдачи крови работают круглосуточно. | Comrades! The front needs your blood. Blood donation points are open around the clock. |
| RAD15 `SDRAD15` | M | news | Танкоград выполнил месячный план за одну ночь. Новые машины уже на фронте. | Tankograd fulfilled its monthly plan in a single night. The new machines are already at the front. |
| RAD16 `SDRAD16` | M | time signal | Московское время — двадцать часов. Передаём последние известия. | Moscow time: twenty hundred hours. Here is the latest news. |

**Russian review (sound-designer, not a native speaker; HYPOTHESIS until
`translator-ru` or the CEO reads it).** Checked for agreement, case and
register: «отбросили за хребет» (acc. of direction), «у Жигулёвской
плотины» (gen.), «пройдите в убежище» (acc.), «сообщайте в штаб» (acc.),
«кипятить» (the impersonal infinitive of official instructions), «падение
посторонних предметов» (the bureaucratic «посторонний предмет»), «не
вступайте с ним в разговор», «пункты сдачи крови». Stress was placed by hand
(§3) and is worth a native check, especially «Заря́», «рубе́ж», «оса́дки»,
«кру́пную», «несмотря́ ни на что́».

## 3. Voices, licences and how they were generated

| Voice | Reference | Licence | Note |
|---|---|---|---|
| **M**, announcer | Thorsten Müller, **neutral** style of Thorsten-Voice emotional v02 (two long declarative sentences, 15.3 s: `ref/sd_ref_radio_m_thorsten_neutral_eb012d63.wav`) | **CC0 1.0** (Zenodo licence field, https://zenodo.org/records/5525023) | The archive was already on disk from D96 (`work/audio/voice_refs/thorsten/thorsten-emotional_v02.tgz`); only its `neutral/` folder was unpacked into `candidates/radio/src/`. **Nothing downloaded.** Same speaker as the D96 German orders reference, but his calm read speech, not his angry set. |
| **F**, announcer | `Elena.wav`, a predefined voice of Chatterbox-TTS-Server 2.0.2 (median F0 198 Hz, the steadiest of the female voices measured) | origin **not documented** (the route D87 accepted for predefined voices, flagged in the R1 study) | **Needs the CEO's yes.** D87 accepted predefined *male* voices; there is **no CC0/CC-BY female voice on disk** and this task had no download permission. A clean alternative needs a download (e.g. the female actor in Kenney's CC0 «Voiceover Pack (40+ lines)», listed as E6 in `2026-10-20_1234_P2_aggressive-voice-references.md`). |

Neither reference speaks Russian, so an accent may leak (research §2 of the
2026-10-20 study). Each line therefore has three takes: t01 (exaggeration
0.5, cfg 0.5, temperature 0.7), t02 (0.6, 0.3, 0.75) and **t03 with cfg 0**
(0.45, 0, 0.7), the documented cure for a cross-lingual accent.

Generation (VERIFIED, 2026-10-23): Chatterbox Multilingual in the server's
own Python, in a worker process (no HTTP server needed), **on the GPU**
(CUDA worked; the CPU fallback stayed unused), with the speech-token filter
of `voice_takes/p2/gen_p2.py` (special tokens >= 6561 dropped before S3Gen)
and a cap of 400 speech tokens (16 s). The model's Russian stresser
(`russian_text_stresser`) is not installed and nothing may be downloaded, so
the text is sent with **hand-placed stress marks** (U+0301, which the
model's vocabulary contains, VERIFIED); the log and the page show the plain
text. Offline: `HF_HUB_OFFLINE=1`. Not watermarked, as the D91 takes
(`AI-LOG.csv` licence field).

## 4. The radio chain (all ours, numpy)

1. Silence trimmed at both ends only (inner pauses kept: these are
   sentences), 90 Hz high-pass.
2. **Band 300-3400 Hz** (4th-order Butterworth shape, minimum phase, the
   project's `gen_weapon_sfx.filt`) with a +3 dB speaker resonance at
   1.4 kHz; **tanh saturation** (drive 2.2, the output valve); a second,
   gentler band (the cone).
3. Levelled: loudest 50 ms A-weighted at -14 dB, peak <= -1 dBFS.
4. The set: **50 Hz valve hum** with odd harmonics, soft hiss, ~2.5 crackles
   a second, a slow +-1 dB reception wobble, all through the same band.
5. A 0.55 s **tune-in** before the voice: static clearing while a
   heterodyne whistle glides to zero beat; 0.35 s of static after.
6. **Station jingle**, separate (three proposals, J1 to J3): FM bells, an
   **original** motif. Not the real Radio Moscow interval signal, which is a
   protected 1930s song; nothing here quotes it.
7. **Time signal** for RAD16: six 1 kHz pips one second apart, the last
   long. A technical signal, no author.

## 5. Integration proposal (for `mod-engineer`, `level-designer`; not built)

### 5.1 Why a new actor and not `SD_Radio`

`SD_Radio` (MOD-SPEC §6.7, ADR 008) **swaps the music**; a loudspeaker must
**add a positional voice over the music**, so it is a sound, not a music
change. GZDoom's own `AmbientSound` things (14001-14064 with `$ambient`)
play forever from map start and cannot run a playlist or a jingle on
approach, so a small ZScript actor is proposed.

### 5.2 `SD_Loudspeaker`

| What | Proposal |
|---|---|
| Class, file | `SD_Loudspeaker`, `zscript/sd/loudspeaker.zs` |
| Editor number | **21201** (next in the decorations block, MOD-SPEC §6.1); the `MAPINFO` `DoomEdNums` line is the PM's |
| `arg0`, playlist | an index into a table in ZScript (§5.4); `0` = all approved lines |
| `arg1`, reach | 3D distance to the player that turns it on; `0` = **384** (`SD_LS_DEFAULT_REACH`) |
| `arg2`, pause | seconds of silence between lines; `0` = **6** (`SD_LS_DEFAULT_PAUSE`), plus a random 0-4 s |
| `arg3`, flags | bit 1 = no jingle; bit 2 = hidden body (for a speaker drawn on a wall texture) |
| Turns on | every 8 tics it measures `Distance3D` to `players[consoleplayer].mo`; the first time it is within reach: `A_StartSound("sd/radio/jingle", CHAN_VOICE, CHANF_DEFAULT, SD_LS_VOLUME, SD_LS_ATTN)`, plus the static bed `sd/radio/bed` on `CHAN_BODY` with `CHANF_LOOPING` at a lower volume |
| Plays | when `IsActorPlayingSound(CHAN_VOICE)` is false and the pause has passed, the next line of its playlist from a **shuffle bag** (all lines once before any repeats; never the same line twice in a row) |
| Turns off | farther than **reach + 128** (`SD_LS_HYSTERESIS`): no new line starts; the line in progress **finishes** (cutting a sentence mid-word sounds like a bug), then `A_StopSound(CHAN_BODY)` |
| Coming back | the jingle plays again only after **60 s** away (`SD_LS_JINGLE_COOLDOWN`), so walking in and out does not ring it each time |
| Volume, attenuation | `SD_LS_VOLUME` 0.7 so enemy sight and attack sounds stay on top; never `ATTN_NONE` (unlike the boss calls). SNDINFO `$rolloff sd/radio linear 128 768` for the whole `sd/radio/*` family: full volume within 128, silent at 768 (**NOT VERIFIED** that `$rolloff` applies to every member by prefix; otherwise one line per logical name) |
| Overlap | `$limit sd/radio/line 1`-style limits do not work across a shuffle of separate names, so the rule is placement: two speakers' reach + 128 zones must not overlap (as `SD_Radio`'s) |
| Body | a decoration, radius 12, height 24, `+SOLID` only when it stands on the floor; with arg3 bit 2: `+NOINTERACTION`, invisible, for a horn painted on a wall |
| Sprite | a horn loudspeaker («колокол»), wall- or pole-mounted, `SDLS` A (art-director; IWAD placeholder until then). Or a wall texture `SDLSPK1` with the hidden body in front of it |
| Saved games | the shuffle bag's position, the "on" flag and the cooldown timer are saved; a `transient` field restarts the bed after a load, as `SD_Radio` does (**NOT VERIFIED** whether the engine restores looping actor sounds itself) |
| Single-player | the listener is the local player, as `SD_Radio` |
| Not shootable | it is ours (Soviet radio), not the enemy's. A shootable variant that dies in a burst of static is a possible V3 nice-to-have, CEO's call |

### 5.3 SNDINFO sketch (lumps `SDRAD01`-`SDRAD16`, `SDRADJ1`, `SDRADPIP`, `SDRADBED`)

```
sd/radio/line/01  SDRAD01      // one logical name per line: the actor shuffles them
...
sd/radio/line/16  SDRAD16
sd/radio/jingle   SDRADJ1      // or a $random of the approved jingles
sd/radio/pips     SDRADPIP     // played before RAD16 only
sd/radio/bed      SDRADBED     // 4-6 s seamless loop of hum + hiss + crackle (to make, procedural)
$rolloff sd/radio linear 128 768
```

If the CEO approves more than one take of a line, the takes become a
`$random` group under that line's name (as the enemy voices, D91), and
the lump names take a member digit (`SDRAD01A`, `SDRAD01B`).

### 5.4 Where: rooms and playlists (for `level-designer`)

One or two speakers per map, in big rooms the player crosses once and
lingers in, away from `SD_Radio`'s zone in MAP01's guard post (Z5b). The
lines are filtered by **when** the story is: a line about the dam plays only
after the dam (MAP05 on); one about Zarya-7 holding only in Episode 1.

| Map | Room (design doc zone) | Playlist | Why |
|---|---|---|---|
| MAP01 | Z4 Leninskaya komnata | 5, 7, 13, 11 | slogans in the political room; the garrison report is about this very base |
| MAP01 | Z6 hangar (reach 512) | 3, 4, 10, 16 | air-raid alert in the hangar as the invasion starts |
| MAP02 | Z3 central hall | 3, 4, 12, 14, 8 | the metro is the shelter the air-raid notice sends people to |
| MAP03 | Z3 assembly hall | 6, 13, 15, 5 | the plan, the factory-fortress, Tankograd's own line |
| MAP04 | Z6 passenger platform | 1, 16, 9, 10, 12 | a station loudspeaker: news and the parade |
| MAP05 | Z5 turbine hall | 1, 6, 13, 14 | (RAD02 is about this dam: keep it for later maps) |
| MAP06 | Z6 Red Square (reach 512) | 2, 9, 7, 5 | «the parade is not cancelled» on Red Square itself |
| MAP06 | Z5 GUM atrium | 8, 12, 14, 10 | civil notices in the shopping gallery |
| MAP07 | Z4 barracks | 2, 7, 13, 16 | a barracks radio, far from Moscow |
| MAP08 | Z6 barracks: mess | 2, 9, 14, 6 | the fleet's mess hall |
| MAP09 | Z3 station yard (one speaker, weak) | 7, 5 | the last Soviet outpost before the alien works; a weaker, noisier variant could be rendered (§7) |

RAD11 (Zarya-7 holds) only in Episode 1; RAD02 (the dam) only from MAP06 on;
RAD15 (Tankograd's plan) in Episode 1 after MAP03 has been reached, or in
Episode 2.

### 5.5 Text and subtitles

The lines are Russian only, as ambience; English and Catalan players
understand the tone, not the words. **Subtitles are not proposed by
default.** If the CEO wants them, each line needs a `LANGUAGE` string in
`[enu default]`, `[ru]` and `[ca]` in the same task (CLAUDE.md), printed
small once per line; that is a `mod-engineer` change and a translation task.

### 5.6 Tests to add with the build (for `mod-engineer`)

`21201 = SD_Loudspeaker` in `MAPINFO`; every `sd/radio/*` logical name maps
to a lump that exists in the PK3; the actor's defaults equal the named
constants above; each placed speaker's reach + 128 zone overlaps no other
speaker's and not `SD_Radio`'s; rows in `docs/art/LICENSES.md` for every
installed take (VOICE-SCRIPT §0.7 fields: tool, model, reference and its
licence). The engine pass (that it compiles, that the shuffle and the
turn-off behave, the rolloff) is the PM's batch (D26).

## 6. Size

One line is 4-8.5 s of voice plus ~1 s of tune-in and tail; about 62 KB of
OGG each (§8). The installed set (16 lines, one jingle, pips, bed) comes to
about **1.1 MB** of the PK3; more if the CEO keeps several takes per line.

## 7. Decisions for the CEO

1. **Listen** and mark OK / NO / ? on the page (16 lines x 3 takes,
   3 jingles); the PM installs nothing before that.
2. **The female voice**: accept the predefined «Elena» (an extension of
   D87 to a female predefined voice), or authorise a download of a CC0
   female reference (Kenney E6) for a new round.
3. **Subtitles**: none (proposal) or `[enu]`/`[ru]`/`[ca]` strings.
4. **Rooms**: the §5.4 table, or the CEO's own picks.
5. Optional: a weak, noisier "far station" render for MAP09, and a
   shootable speaker.

## 8. Measurements of this round (VERIFIED, 2026-10-23)

48 of 48 takes generated, none failed (GPU, ~8-12 s a take). Nobody here
can listen, so the page ranks the takes by measurement only: voice length
against an announcer's pace (~5.2 syllables a second plus a breath per
stop), the longest inner pause, silence share and raw clipping (none had
any). The processed files: 98-99 % of the energy inside 300-3400 Hz, peak
-1.6 to -3.8 dBFS; in RAD01 t01 the tune-in sits at -29 dBFS RMS, the voice
at -22 and the valve bed at -46. The 53 OGGs weigh 3.3 MB in all (~62 KB a
take), so the installed set (16 lines, a jingle, the pips, a bed) is about
1.1 MB.

| Line | Recommended (rank 1) | Note |
|---|---|---|
| RAD01 | t01 | |
| RAD02 | t02 | |
| RAD03 | t02 | |
| RAD04 | t03 | t01 has a 0.86 s pause inside |
| RAD05 | t01 | |
| RAD06 | t03 | |
| RAD07 | t01 | **t03 flagged**: 6.04 s for an expected 3.7 s (runaway or very slow) |
| RAD08 | t02 | all three 20-30 % shorter than expected |
| RAD09 | t02 | |
| RAD10 | t03 | all three 18-32 % shorter than expected |
| RAD11 | t02 | |
| RAD12 | t01 | t02 is 4.04 s for 5.8 s: listen for dropped words |
| RAD13 | t02 | |
| RAD14 | t03 | |
| RAD15 | t01 | |
| RAD16 | t02 | t03 is 7.08 s for 5.2 s |

The female voice reads consistently faster than the pace estimate (every F
line is short, the M lines are on or just over it): HYPOTHESIS that Elena
is simply a quicker reader, but a short take can also mean swallowed words,
which only the ear can tell.
