# Soundtrack — the music lumps, one card per piece

Living document. Owner: `sound-designer`. Russian mirror: `docs/ru/sound/SOUNDTRACK.md` (D7).
Created 2026-10-13 (F2, first music); candidate list **closed** 2026-10-13.
Rights frame: `docs/sound/MUSIC-RIGHTS.md` — that document owns every licence
fact and this one owns every sound fact.

Decision **D16** (CEO, 2026-10-13): *"el camino correcto es instrumental en MIDI"*.
No Soviet recording of anything enters this mod.
Same day, two further CEO instructions: *"no construyas tú los MIDIs, mejor
descargarlos"* and *"Sí a LA INTERNACIONAL"* for the title screen, plus the
verdict that our own two pieces are *"un poco simples"*. **D16's wording
(«our own instrumental MIDI sequences») no longer matches what we are
shipping** — the title piece is a downloaded, attribution-licensed sequence.
That needs a new D-number; see "Decisions needed", point 0.

> **Nothing below is approved and nothing is in the PK3.** Downloads live in
> `work/audio/candidates/`, our own and our repaired files in `work/audio/`.
> Nothing enters `assets/` without an explicit approval, exactly as with the
> textures.

> ⚠️ **And `work/` is gitignored, so none of it is version-controlled.**
> Verified: `.gitignore:16` is a bare `work/`, and `git ls-files work/` returns
> nothing. The twelve downloaded MIDIs, the repaired `D_SDINTL.mid` and the two
> `D_SDFIX*.mid` exist **only on this machine**. Combined with the sourcing gap
> in §3.1 — seven of the twelve have no recorded per-piece URL — a clean
> checkout cannot reproduce this candidate set. This is deliberate for art
> (batch PNGs live embedded in previews) but it is wrong for music, where the
> artefact *is* the file and the provenance is external. **Request to the PM,
> who owns `.gitignore` and the commits:** either narrow the ignore so
> `work/audio/candidates/` is tracked, or treat §3.1's URL re-verification as
> a blocker before this list is relied on again. I have not touched
> `.gitignore`.

---

## 0. The recommendation, in four lines

| Cue | File | Why |
|---|---|---|
| **Title screen** | **`work/audio/D_SDINTL.mid`** — Engelbach's orchestral *Internationale*, head silence removed by us | the CEO's choice, the only downloaded file that is finished orchestral music, and now the only one with no measurable defect at all |
| **MAP01** | **`work/audio/D_SDM01.mid`** — our own "Zarya-7" | the only candidate of any origin that is *written as a game loop*: 2:22, dark, restarts from 25 % instead of slamming. The alternative is a ten-minute solo-piano transcription |
| **Diegetic radio** | `WM_Ej_uchnem.mid`, `WM_Kolokolchik.mid` — CC0, already orchestrated | free of every obligation, 40-50 s, right texture for the Leninskaya komnata |
| **Our `D_SDTITL`** | **reserved, not retired** | it is no longer the title theme, but it is a finished 1:21 Soviet march in D minor and the natural intermission / episode-end cue |

Three of the twelve downloads are **discarded** and six are kept as named
reserves (§3). Two needed repair and got it (§5). The full reasoning is below; the thing I need decided is in §8.

---

## 1. How to listen

The CEO heard nothing on the first attempt because his personal `gzdoom.ini`
had `snd_musicvolume` at **0** while the engine was playing correctly. The
tool no longer depends on anyone's mixer: it passes `-config` pointing at
`logs/gzdoom-tooling.ini` and sets `snd_musicvolume 0.8` on the command line,
so it also stops writing state back into the CEO's own preferences.

```bash
python3 tools/build.py                                   # the overlay loads on top of this

# the two recommendations
python3 tools/audio/audition.py --play title --lump D_SDINTL   # the Internationale, repaired
python3 tools/audio/audition.py --play map01 --lump D_SDM01    # our MAP01 loop

# our title march, now proposed for the intermission instead
python3 tools/audio/audition.py --play title --lump D_SDTITL

# the downloaded candidates (packed as D_CND01..D_CND12; the map is printed)
python3 tools/audio/audition.py --pack --candidates
python3 tools/audio/audition.py --play map01 --candidates --lump D_CND01   # Bald Mountain
python3 tools/audio/audition.py --play title --candidates --lump D_CND09   # Эй, ухнем
```

`audition.py` packs MIDIs into a throwaway overlay PK3 with its own MAPINFO
and loads it **on top of** `dist/sovietdoom.pk3`. The shipped
`src/lumps/MAPINFO` is never touched; deleting `work/audio/sd-music-draft.pk3`
puts everything back. Downloaded files get positional lump names because
their own names are not valid lumps.

The five tools, all of them mine, all documented in their own docstrings:

| Tool | What it does | Writes |
|---|---|---|
| `tools/audio/midi_inspect.py` | reads the bytes: tempo map, GM programs per channel, note count, hanging notes | nothing |
| `tools/audio/audition.py` | packs the overlay; `--play` launches the game, `--render` makes GZDoom synthesise every file to WAV | `work/audio/`, `logs/` |
| `tools/audio/wav_report.py` | measures a render: peak, clipping, head/tail silence, the 12-slot loudness arc, brightness | nothing |
| `tools/audio/midi_edit.py` | the only one that changes a MIDI, and only mechanically: `--trim-head`, `--velocity`, `--loop-tail` | a new file, never in place |
| `tools/audio/gen_music.py` | generates our own two pieces (plan B, §6) | `work/audio/*.mid` |

---

## 2. How the verdicts were reached, and the limit of them

**Stated plainly, because it decides how much the table below is worth: I
cannot hear.** Every verdict in §3 is an *instrumented* audition, not a human
one. What that can and cannot settle:

| Decidable from measurement | Needs the CEO's ears |
|---|---|
| the file parses; no hanging notes | whether the piece is *good* |
| the written tempo, and that the render matches it (so: no absurd speed) | whether that tempo feels right under gameplay |
| which GM instrument every channel asks for (so: no mis-assignment) | whether those instruments sound right in `gzdoom.sf2` |
| peak level, clipped samples, head and tail silence | whether the mix is muddy |
| the loudness arc — does anything enter, build, leave | whether the arc is *musically* convincing |
| note density per voice | taste, period feel, tone |

The chain, for every file: parsed byte by byte with `midi_inspect.py`, then
**synthesised by GZDoom itself** with the engine's `writewave` console
command (`audition.py --render`), then the WAVs measured with
`wav_report.py`. So the numbers come out of the same FluidSynth +
`gzdoom.sf2` path the player will hear, not out of a third-party player.

All twelve downloads parsed cleanly, all twelve produced sound, **zero
hanging notes anywhere**, and every rendered duration matched its tempo map
to within a second. Re-running the whole measurement is two commands:

```bash
python3 tools/audio/audition.py --render --candidates     # ~3 min, writes 762 MB of WAV
.venv/bin/python tools/audio/wav_report.py work/audio/render-candidates/*.wav
```

The WAVs are **not kept** — `writewave` emits 32-bit float at 44.1 kHz, so
twelve files come to 762 MB. Regenerate them when you want to re-check a
number.

### 2.1 Three findings about the engine, worth more than any one file

1. **With `snd_musicvolume 0`, GZDoom's `currentmusic` answers "Currently no
   music playing"** even when the lump is correctly wired. Any future check
   of `currentmusic` must run with a non-zero music volume; `0.02` is
   inaudible and sufficient. This is a trap for `qa-engineer`.
2. **`--render` no longer loads `dist/sovietdoom.pk3`, on purpose.** The mod
   PK3 contributes nothing to a `writewave` render — it ships no soundfont, no
   MIDI lump and no sound CVar (`grep -i 'midi\|soundfont\|snd_' src/lumps/`
   is empty), so the synthesis is identical. And loading it while another
   agent was rebuilding it left the engine alive after the last `writewave`,
   so it never reached `quit`: a **false timeout on a render that had already
   written every WAV correctly**. Measurement must not depend on someone
   else's build being mid-flight. `--play` still loads the mod, because there
   the point is the real game.
3. **GZDoom ignores End-of-Track padding.** `midi_edit.py --loop-tail 2` on
   the Internationale produced a **byte-identical render** (sha256
   `a0214c14…` for both), so there is no way to buy a breath before the loop
   restart by padding the file. If the title loop turns out to need one, it
   has to be real trailing notes or a decaying chord, not silence. *The
   in-game loop point was not separately tested against the file end —
   **NOT VERIFIED** that playback and `writewave` agree on this.*

### 2.2 The engine really plays the recommended files

Fresh evidence, this session, non-zero music volume, logs with **zero**
errors or warnings (`grep -icE 'error|warning|unknown|cannot|failed'` = 0):

| Claim | Evidence |
|---|---|
| `D_SDINTL` plays on the title screen | `Currently playing music 'D_SDINTL'` — `logs/audition-intl-title.log` |
| `D_SDINTL` plays on MAP01 | same answer — `logs/audition-intl-map.log` |
| `D_SDM01` plays on MAP01 | `Currently playing music 'D_SDM01'` — `logs/audition-m01.log` |
| every candidate synthesises | 12/12 WAVs written, measured — §3 |

---

## 3. The closed candidate table

Twelve files, **186 170 B (182 KiB)** in total. Two tables, one key: the lump
name. The first is where each file came from and what we may do with it; the
second is what it actually sounds like. Rights detail and the eleven sources
rejected before download are `MUSIC-RIGHTS.md` §4.4.

### 3.1 Provenance, licence, size

Licence text is quoted as the file's own page states it, not paraphrased. The
distinction that governs the whole list: **a free composition does not imply a
free sequencing** (`MUSIC-RIGHTS.md` §1.2), and **CC BY-SA is unusable for us**
because D15 ships assets as CC BY-NC-SA 4.0 and ShareAlike forbids adding the
NonCommercial term.

| Lump | File · size | Work (original · transliterated) | Source URL | Sequencer / typesetter | Licence, verbatim | D15 |
|---|---|---|---|---|---|---|
| `D_CND10` | `WM_Internationale_orch2.mid` · 8 922 B | **Интернационал** / *Internatsional*, orchestral; De Geyter 1888 | https://commons.wikimedia.org/wiki/File:Internationale_orch2.mid | **Jerry Engelbach**, USA, 2003 | `{{Attribution\|Jerry Engelbach}}` + VRT permission ticket 2008011810001789; melody `{{PD-Internationale}}` | ✅ **credit Engelbach** |
| `D_CND11` | `WM_Internationale_piano_Bb.mid` · 3 538 B | **Интернационал**, piano in B♭ | https://commons.wikimedia.org/wiki/File:Internationale-piano-Bb.mid | **Jerry Engelbach**, USA, 2001 | same as above | ✅ **credit Engelbach** |
| `D_CND09` | `WM_Ej_uchnem.mid` · 2 140 B | **Эй, ухнем** / *Ey, ukhnem* (Volga Boatmen), Balakirev's setting, pub. 1866 | https://commons.wikimedia.org/wiki/File:Ej,_uchnem!.mid | **Peter Gerloff** (Commons: *Rabanus Flavus*), 2021 | `{{self\|Cc-zero}}` — **CC0 1.0**, "waives all of his or her rights to the work worldwide" | ✅ no obligation |
| `D_CND12` | `WM_Kolokolchik.mid` · 2 354 B | **Колокольчик** / *Kolokolchik*, Russian traditional | https://commons.wikimedia.org/wiki/File:Kolokolchik.mid | **Peter Gerloff**, 2019 | `{{self\|Cc-zero}}` — **CC0 1.0** | ✅ no obligation |
| `D_CND01` | `MU_Mussorgsky_BaldMountain.mid` · 79 556 B | **Ночь на лысой горе** / *Noch na lysoy gore*; Mussorgsky d. 1881, piano transcription by Konstantin Chernov d. 1944 | https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1892 | typeset **Robert Clausecker**, Mutopia Project, 2013 | **CC BY 3.0** | ✅ **credit Clausecker + Mutopia** |
| `D_CND06` | `MU_Tchaikovsky_Dumka_op59.mid` · 36 268 B | **Думка** / *Dumka* op. 59 (1886), "Russian rustic scene" | Mutopia, piece record **not recorded at download** — browse: https://www.mutopiaproject.org/browse.html | Mutopia Project (LilyPond, staves `up`/`down`) | **Public Domain** | ✅ |
| `D_CND07` | `MU_Tchaikovsky_Seasons_August.mid` · 21 748 B | **Времена года: Август** / *Vremena goda: Avgust* ("Harvest", 1876) | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond 2.8.6, 21 Aug 2006) | **Public Domain** | ✅ |
| `D_CND03` | `MU_Scriabin_Etude_op2n1.mid` · 10 313 B | **Этюд** / *Etyud* op. 2 № 1 (1887) | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond) | **Public Domain** | ✅ |
| `D_CND05` | `MU_Scriabin_Prelude_op59n2.mid` · 7 789 B | **Прелюдия** / *Prelyudiya* op. 59 № 2 (1910) | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond) | **Public Domain** | ✅ |
| `D_CND04` | `MU_Scriabin_Prelude_op11n1.mid` · 4 910 B | **Прелюдия** op. 11 № 1 | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond) | **Public Domain** | ✅ |
| `D_CND02` | `MU_RimskyKorsakov_FugueBACH.mid` · 5 649 B | *Fugue sur le nom de BACH*; Rimsky-Korsakov d. 1908 | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond) | **Public Domain** | ✅ |
| `D_CND08` | `MU_Tchaikovsky_WoodenSoldiers.mid` · 2 983 B | **Марш деревянных солдатиков** / *Marsh derevyannykh soldatikov* op. 39 | Mutopia, piece record **not recorded at download** | Mutopia Project (LilyPond) | **Public Domain** | ✅ |

> **Gap I am flagging rather than papering over.** The per-piece Mutopia URL
> was recorded only for *Night on Bald Mountain* (id 1892). For the other
> seven, the licence was read from the per-piece record on 2026-10-13 but the
> record's address was not written down, and the files themselves carry no
> provenance beyond `creator: GNU LilyPond <version>`. All seven are
> **Public Domain**, so no attribution duty is at risk — but a Public-Domain
> claim whose page we cannot point at is a claim resting on my memory.
> **Before any of those seven is packed, its piece URL must be re-verified
> and written into `MUSIC-RIGHTS.md` §4.4.** Bald Mountain, the one with a
> real attribution obligation, is the one that is fully sourced.

### 3.2 What they actually sound like

All numbers from GZDoom's own render. **Arc** is RMS per twelfth of the piece
as a percentage of its own loudest twelfth — the measurable form of the CEO's
word *simple*: a flat arc means nothing enters, builds or leaves.
**Voices** is distinct GM programs; **n/s per voice** is note density divided
by channels, which separates an orchestral texture from piano mud.
Sorted by usefulness.

| Lump | Length · tempo | Voices · channels | n/s · per voice | Peak · clip | Head silence | Arc (spread) | Instrumented verdict | Proposed for |
|---|---|---|---|---|---|---|---|---|
| `D_CND10` | 1:27.3 · 90 BPM 4/4 | **12 · 16** | 12.2 · 0.76 | 0.391 · none | **1.99 s** ❌ | 43 45 45 32 39 47 54 44 50 77 91 100 **(68)** | ✅ **the best file in the set, and the only defect was mechanical.** A real orchestration: piccolo, flute, oboe, clarinet, bassoon, horn, trumpet, trombone, tuba, timpani, five string parts and a genuine drum part. Brightness 2 150 crossings/s, the highest in the set bar one | **TITLE** — repaired as `D_SDINTL`, §4 |
| `D_CND09` | 0:49.8 · 81 BPM | 4 · 4 | 4.1 · 1.03 | 0.420 · none | 0.37 s | 62 60 65 59 64 59 75 62 62 68 74 100 (41) | ✅ **usable as-is.** Violin, cello, oboe, clarinet actually assigned; brightest file measured (2 384). Too short to carry a map | **diegetic radio**, intermission |
| `D_CND12` | 0:38.7 · 80 BPM | 3 · 4 | 5.9 · 1.47 | 0.288 · none | 0.38 s | 91 93 91 95 90 86 93 100 88 94 86 69 (32) | ✅ **usable as-is.** Celesta, flute, cello. Quiet, domestic, slightly sad | **diegetic radio** (Leninskaya komnata) |
| `D_CND01` | 10:11 · 180 BPM 2/2 | **0** · 2 | **15.3 · 7.6** | 0.393 · none | none | 98 100 80 83 78 98 85 86 80 79 74 67 (33) | ⚠️ **right length, right menace, wrong object.** 9 313 notes, no program change at all → ten minutes of solo `gzdoom.sf2` grand piano at 15 notes a second over two channels, which is the densest per-voice figure in the set. Its loudest moment is **bar one**, so a loop restarts by jumping 67 → 98 % | **reserve.** Only viable if someone orchestrates it (§8.2) |
| `D_CND06` | 9:33 · 60 BPM, tempo changes | 0 · 2 | 7.5 · 3.7 | 0.430 · none | none | 55 44 76 63 81 64 96 68 100 81 40 44 **(60)** | ⚠️ **the best-shaped piano file**: it already breathes and it ends quiet, so it loops better than Bald Mountain. Same solo-piano problem, bleaker and slower | reserve, alternative to `D_CND01` |
| `D_CND07` | 5:31 · 108 BPM 6/8 | 0 · 3 | 7.4 · 2.5 | **0.982** ⚠️ · none | 0.28 s | 82 85 85 100 67 63 66 66 83 86 81 100 (37) | ⚠️ driving perpetual motion, but it sat **1.8 % from full scale** before repair. **Repaired → 0.720** (§5) | reserve: a fight cue if ever orchestrated |
| `D_CND03` | 2:16 · 60 BPM 3/4 | 0 · 2 | 8.3 · 4.1 | **1.011** ❌ · **4 samples** | none | 75 84 61 83 45 60 95 100 63 31 30 21 **(79)** | ⚠️ **clipped**, and the widest arc of any download — it dies away to 21 %, which is a real shape. **Repaired → 0.747** (§5) | death / aftermath sting, once orchestrated |
| `D_CND05` | 1:28 · 126 BPM 6/8 | 0 · 2 | 10.4 · 5.2 | 0.396 · none | none | 87 91 84 81 94 80 88 100 85 89 92 75 (25) | ⚠️ good unsettled mood, but **arc spread 25 — flat**, and 1:28 is too short to loop under a firefight | reserve: alien-zone ambience |
| `D_CND11` | 1:22.8 · 96 BPM | 0 · 1 | 5.0 · 5.0 | **0.185** ⚠️ · none | **2.18 s** ❌ | 99 96 98 88 88 92 93 86 86 92 100 85 (15) | ⚠️ **not the title.** One channel of piano, the quietest file measured (peak 0.185, under half of `D_CND10`), **arc spread 15 — the second-flattest** — and the same two-second hole at the head | **keep only as a diegetic Internationale** — a piano heard through a wall is exactly what it sounds like |
| `D_CND04` | 0:42.7 · 140 BPM | 0 · 2 | 11.2 · 5.6 | 0.416 · none | none | 74 82 78 86 74 75 81 77 100 96 89 74 (26) | ❌ **discard.** 43 s, flat, solo piano. Nothing it could be but a sting, and we have better stings | — |
| `D_CND02` | 2:04 · 140 BPM 4/2 | 0 · 2 | 5.0 · 2.5 | 0.645 · none | none | 77 88 90 100 87 92 79 95 80 74 81 80 (26) | ❌ **discard.** Free and clean, and musically irrelevant to us: a conservatory fugue on a **German** name. Nothing Russian reaches the listener | — |
| `D_CND08` | 0:41.1 · 140 BPM 2/4 | 0 · 2 | 7.9 · 3.9 | 0.344 · none | none | 95 98 95 96 99 93 98 97 94 100 92 92 **(8)** | ❌ **discard, and it is the clearest discard in the set.** Arc spread **8 points** — measurably the flattest thing we have, a children's toy march. Wrong tone for 1977 and for this game | — |

**Eight of the twelve are solo piano with no program change whatsoever.** That
is not a flaw in Mutopia: a LilyPond MIDI is the *audio preview of an engraved
score*, and these files say so themselves — their track names are `RH:`/`LH:`,
`upper`/`lower`, `up`/`down`, and their only text metadata is
`creator: GNU LilyPond 2.x`. The notes are Mussorgsky's and Tchaikovsky's and
the structure is real; the timbre is a placeholder.

So "download instead of composing" moved the work rather than removing it:

| Route | What we avoid | What is still ours to do |
|---|---|---|
| downloaded orchestration (`D_CND10`) | everything musical | credit Engelbach; remove 2 s of silence — **done**, §5 |
| downloaded score preview (the eight Mutopia files) | writing the notes, and the notes are the point | assign a GM program per staff, balance channels, fix levels, cut to length |
| sequenced by us from a free score | nothing | everything — but the result is exactly what we want and the recording right is ours |

And the pieces that would most obviously fit **do not exist as a
licence-clean MIDI anywhere**: *Marche slave*, *Прощание славянки*,
*Амурские волны*, *Смело, товарищи, в ногу*, *Вы жертвою пали*. Every MIDI of
them online sits on a site with no per-file licence and no named sequencer.
For *Marche slave* the one clean ready-made option is IMSLP's **CC BY 4.0
synthesised MP3** — megabytes instead of kilobytes. For the four songs,
sequencing them ourselves is the only clean route, and it is cheap: they are
16- to 32-bar strophic tunes, roughly 2-3 h each.

---

## 4. The Internationale — the CEO's choice, examined on its own

`D_CND10` is not a score preview. Read off the file's own channel timeline,
33 bars of 4/4 at 90 BPM:

| First note at bar | Who enters |
|---|---|
| **1.0** | **strings alone** — five parts, channels 12-16 |
| **1.3** | timpani under them |
| **8.8** | **brass**: trumpet and trombone together |
| **9.3** | tuba completes the brass choir |
| **16.8** | **woodwinds**, all five at once: piccolo, flute, oboe, clarinet, bassoon |
| **21.0** | **horns** — the last voice to arrive |
| **24.3** | **military percussion**: bass drum ×21, snare ×101, crash ×12 |
| 32.3-32.8 | everything stops together; the piece is 33 bars |

Those bar numbers are read off the file, not off a description of it: first
note-on per channel, tick ÷ (960 × 4) + 1. **Seven entries across 24 bars,
and nothing leaves until the end** — the texture only ever thickens.

Its measured arc climbs 43 → 100 % across exactly those entries (spread 68,
second only to the clipped Scriabin). That is the shape our own title theme
was missing, and it is what a generator writing eight-bar periods does not
produce by accident.

One thing I checked because it is the classic way a MIDI sounds broken on a
General MIDI synth: **channel 10 carries a program change to GM 0, acoustic
grand piano.** On channel 10 a program change is ignored and every note is a
drum, so if Engelbach had written a piano part there, GZDoom would play
nonsense percussion. He did not: the only notes on that channel are **36, 38
and 49 — bass drum, snare, crash cymbal** — and they enter at bar 24 for the
final tutti. It is a deliberate military drum part, correctly written. The
file is sound.

### 4.1 The one defect, and the repair

The file opened with **1.990 s of absolute digital silence** — not a quiet
entry, nothing at all, verified sample by sample on the engine's own render.
Under a still poster that is survivable once; on a loop it is a two-second
hole every 87 seconds.

```bash
python3 tools/audio/midi_edit.py \
    work/audio/candidates/WM_Internationale_orch2.mid \
    work/audio/D_SDINTL.mid --trim-head
```

2 863 ticks = 2.98 beats at 90 BPM = 1.99 s, removed by shifting every event
earlier; the tempo, key, time signature and sixteen program changes that sat
in front of the first note collapse to tick 0 in their original order, which
is where a sequencer would have put them. Nothing else changed: same 1 063
notes, same 12 voices, same 16 channels, same zero hanging notes.

| | before | after |
|---|---|---|
| rendered length | 87.68 s | **85.68 s** |
| head silence | **1.990 s** | **0.001 s** |
| peak · clipped samples | 0.391 · 0 | 0.391 · 0 |
| arc (spread) | 68 | 68 — unchanged, as intended |
| plays in the engine | — | `Currently playing music 'D_SDINTL'`, title **and** MAP01, zero log errors |

**So on every measure available to me the downloaded Internationale is
sound, and it is ready for the CEO's ear** — the only verdict I am entitled
to give (§2). It is finished orchestral music, its instruments are correctly
assigned, its tempo is the one written, it does not clip, it has the widest
instrumental build-up in the set and its one real defect is gone and verified
gone. The question "and if it sounds bad, what then?" has no measurable
trigger left to fire, so **re-sequencing it from the IMSLP score is not
needed**. That route stays
documented in `MUSIC-RIGHTS.md` §4.1 as the fallback if the CEO ever dislikes
Engelbach's orchestration itself, and it would cost roughly a day for a
result that would not obviously be better.

**The obligation that comes with it**: `{{Attribution|Jerry Engelbach}}` is
attribution-only, **not** public domain. Shipping it means crediting Jerry
Engelbach wherever we credit anyone. That is a line in the credits and a row
in the licence register — cheap, but real, and the CEO should accept it
knowingly (§8.0).

**Lump name**: `D_SDINTL` (8 characters, the `D_` music prefix plus `SD` per
D1). The repaired file is the one that would ship; the download stays in
`work/audio/candidates/` untouched as the provenance original.

---

## 5. What else I repaired, and what I refused to repair

`tools/audio/midi_edit.py` does **mechanical** edits only — trim leading
silence, scale note-on velocities, pad the tail. It never assigns an
instrument, changes a pitch or cuts a section, because those are musical
decisions that belong in a card in this document, not in a flag. Every output
is a derivative of the input sequencing, which all four accepted licences
(CC0, `{{Attribution}}`, PD, CC BY 3.0) permit; the duty to credit survives
the edit and is recorded in `MUSIC-RIGHTS.md` §4.4.

| Repair | Command | Measured result |
|---|---|---|
| Internationale head silence | `--trim-head` | 1.990 s → 0.001 s, §4.1 |
| `D_CND03` Scriabin *Etude* **clipped** (peak 1.011, 4 samples over full scale) | `--velocity 0.85 --trim-head` → `work/audio/D_SDFIX3.mid` | peak **1.011 → 0.747**, 0 clipped samples, 1 114 note-ons scaled, arc unchanged (79) |
| `D_CND07` *August* at the ceiling (peak 0.982) | `--velocity 0.85 --trim-head` → `work/audio/D_SDFIX7.mid` | peak **0.982 → 0.720**, 2 442 note-ons scaled, 0.50 beats of head silence removed, arc unchanged (37) |
| Internationale loop breath | `--loop-tail 2` | **no effect** — byte-identical render. GZDoom ignores End-of-Track padding (§2.1.3). The variant file was deleted rather than kept as a decoration |

**The editor itself is verified, because it is the only tool here that writes
a MIDI.** Read-then-write with no edit requested, over all twelve downloads:
note count, hanging-note count, format, track count, division, channel set,
GM program map, time signatures and computed duration come back **identical in
all twelve**, to the microsecond. (The output is a few per cent larger: running
status is expanded on read and never re-emitted, which trades bytes for a file
that is not a parsing puzzle.) `--velocity 1.0` is the identity edit, so the
check is reproducible per file:

```bash
python3 tools/audio/midi_edit.py <file> /tmp/rt.mid --velocity 1.0
python3 tools/audio/midi_inspect.py <file> /tmp/rt.mid    # the two reports must agree
```

The two `D_SDFIX*` files prove the clipping is fixable in one command. They
are **not** proposed for anything: both are still solo piano, and the level
was never the reason they are reserves. They exist so that nobody has to
re-derive the fix if those pieces are ever promoted.

**What I refused to do**: assign instruments to the Mutopia piano files. A
program change per channel is one line of code; whether strings-plus-brass on
Chernov's two staves sounds like an orchestration or like a wheezing organ is
a question I cannot answer without ears, and piano idiom — repeated octaves,
tremolos, wide leaps — is exactly what sustained orchestral patches handle
worst. Doing it blind and calling it done would be the kind of unverified
claim this project does not ship. It is a real option with a real cost and it
is §8.2.

---

## 6. Our own sequences (plan B, kept)

The CEO's verdict on these was *"están bien las piezas pero un poco simples"*,
and the measurements partly agree and partly do not:

| | `D_SDTITL` | `D_SDM01` | `D_SDINTL` for comparison |
|---|---|---|---|
| form | one 8-bar period stated twice | four 16-bar sections | through-composed, 4 instrumental entries |
| distinct GM voices | 7 | 5 | 12 |
| notes/s · per voice | 4.1 · 0.58 | 6.7 · 1.12 | 12.5 · 0.78 |
| arc spread | **75** | **75** | 68 |
| peak · clipped | 0.291 · 0 | 0.368 · 0 | 0.391 · 0 |

So the *arc* is not where they are simple — both of ours measure a wider
dynamic shape than the Internationale. Where they are thinner is **voices and
through-composition**: 5-7 instruments against 12, and repeated periods
against four distinct entries. That is a fixable criticism, and the cheapest
fix is not to replace `D_SDM01` but to give it two more instrumental layers
and a non-repeating C section — a generator change, hours not days (§8.3).

### Card 1 — `D_SDTITL`, "Zarya" — **reserved, proposed for the intermission**

| Field | Value |
|---|---|
| **Lump** | `D_SDTITL` (7 chars; `D_` is the Doom convention for a music lump) |
| **File** | `work/audio/D_SDTITL.mid`, 3 315 B, SMF format 1, 7 tracks, 480 ticks/beat |
| **Was for** | the title screen. **Superseded there by `D_SDINTL`** on the CEO's choice of the Internationale |
| **Now proposed for** | the **intermission / episode end**, where a 1:21 march that resolves and stops is exactly the right object, and where nothing else we have fits |
| **Duration** | 1:21 (81.0 s written; 81.8 s rendered, reverb tail included). **3.21 s of tail silence** — measured, and the reason it suits a screen that ends rather than a loop |
| **Tempo · key** | 80 BPM 4/4, constant `TITLE_TEMPO_BPM` · D natural minor, C♯ raised only at the cadence (the harmonic-minor dominant that gives Russian marches their bite) |
| **Instruments** (GM) | French horn → trumpet (melody), trombones (harmony), tuba (bass), timpani, string ensemble, tubular bells, one crash on the final chord |
| **Original or sequenced** | **ORIGINAL COMPOSITION**, `sound-designer`, 2026-10-13. Not an arrangement; it quotes nothing |
| **Licence** | own work, **CC BY-NC-SA 4.0** (D15). Generator code: GPL-3.0 |
| **Rights to clear** | **none.** No composer, no lyricist, no label, no phonogram — the whole point of writing it ourselves |

**Form** (26 bars, the last silent so the loop breathes): 1-4 timpani alone on
D and A growing 8 velocity steps a bar, tuba joining on a **bare fifth** from
bar 3, no third — the mode withheld until the theme states it; 5-12 first
statement of the 8-bar period, **horns alone**, trombones on beats 1 and 3,
the march's two feet; 13-20 the same period, **trumpets an octave up with
horns doubling below**, strings sustaining, the loudest point and the one the
poster is cut to; 21-25 coda VI – iv – V7 – i – i, plagal weight then the
dominant, last chord held two bars under a tubular bell on D; 26 silence.

Measured arc: 25 57 70 69 68 86 95 96 **100** 85 76 70 — spread 75. The
crescendo and the second statement are in the file, not only in the intention.

**Why 80 BPM.** A Soviet *parade* march runs 112-120, but this is music under
a still image, and the newsreel and documentary fanfares of the period sit far
slower and heavier. More solemn: `--title-tempo 72`. More military:
`--title-tempo 96`. Less brass: lower `TITLE_VEL_MELODY` / `TITLE_VEL_HARMONY`
or the channel volumes in `TITLE_MIX`.

### Card 2 — `D_SDM01`, "Zarya-7" — **my recommendation for MAP01**

| Field | Value |
|---|---|
| **Lump** | `D_SDM01` (7 chars) |
| **File** | `work/audio/D_SDM01.mid`, 8 789 B, SMF format 1, 6 tracks, 480 ticks/beat |
| **Where it plays** | MAP01, Zarya-7 cosmodrome, the invasion just begun (`docs/levels/MAP01-zarya-7.md`) |
| **Duration** | 2:22 per loop (142.2 s written, 142.8 s rendered). The map is 5-8 min, so the player hears 2 to 3.5 loops |
| **Tempo · key** | 108 BPM 4/4, `MAP01_TEMPO_BPM` · D minor with a flat second (E♭) leaning on the tonic — the oldest "something is wrong" interval there is, and it costs one note |
| **Instruments** (GM) | synth bass 2 (ostinato), tremolo strings, pad "halo", trombones (stabs), FX "crystal" (the distant signal), GM percussion: low floor tom, low tom, bass drum, snare, ride, crash |
| **Measured** | peak 0.368, **0 clipped**, no head silence, 0.33 s tail, arc spread **75**, brightness **674 crossings/s — by far the darkest file of any origin**, which is what an ambience loop should measure |
| **Original or sequenced** | **ORIGINAL COMPOSITION**, `sound-designer`, 2026-10-13, in the idiom of Eduard Artemyev's ANS electronics (*Solaris*, *Stalker*) crossed with Doom's ostinato-and-percussion habit. Artemyev's own music is protected and **none of it is used**; style is not copyrightable, the same finding the poster research reached |
| **Licence** | own work, **CC BY-NC-SA 4.0** (D15) |
| **Rights to clear** | **none** |

**Form** (64 bars, four 16-bar sections, seamless loop): **A — pulse** (1-16)
the bass figure and two toms, nothing else, the base still standing and the
player walking through it; **B — dread** (17-32) tremolo strings crawling up
a chromatic line D–E♭–E–F–F♯–G–A♭–A, two bars a step, cold pad underneath,
bass drum enters; **C — alarm** (33-48) trombone stabs on and off the beat,
alternating the tonic triad with its **Neapolitan** a semitone above, march
snare on 2 and 4 — the Soviet half of the texture; **D — release** (49-64)
everything drops to the pad and four far-off signals, the last four bars
nearly silent.

Measured arc: 55 55 58 92 91 94 97 98 **100** 74 63 **25**. That last number
is the design: **the loop restarts from near-silence, not from a cut.** Over
eight minutes that is what keeps it from wearing a hole in the player, and it
is precisely what `D_CND01` cannot do — Bald Mountain's loudest twelfth is its
*first*, so its loop jumps 67 → 98 %.

If the CEO finds it **too busy**: `MAP01_VEL_BRASS`, or delete the snare in
section C. **Too slow for a fight**: 120 BPM. **Too long before anything
happens**: `MAP01_SECTION_BARS` 12. **Too simple**: §8.3.

### How plan B was verified

| Claim | Evidence |
|---|---|
| valid SMF | re-parsed independently: every chunk length exact, no trailing bytes, no running-status error, **zero hanging notes** |
| GZDoom plays `D_SDTITL` at the title | `Currently playing music 'D_SDTITL'` — `logs/audition-title.log` |
| GZDoom plays `D_SDM01` on MAP01 | `Currently playing music 'D_SDM01'` — `logs/audition-m01.log` (re-verified this session, zero log errors) |
| they make sound, not silence | engine `writewave` → `work/audio/render/`, measured in the cards above |
| the sections are really there | per-bar RMS of those renders matches the written form bar for bar |
| the generator is reproducible | two consecutive runs produce byte-identical files |

**Which synthesiser the player hears** (verified on this machine, GZDoom
4.14.2 macOS): `snd_mididevice` is **-5 (FluidSynth)**, `fluid_patchset` is
**`gzdoom`** → `GZDoom.app/Contents/MacOS/soundfonts/gzdoom.sf2`, a 3.3 MB
General MIDI soundfont **bundled with every GZDoom install**. So these pieces
sound the same for every player on a stock engine; we are not at the mercy of
a system synth and we do not get OPL FM unless a player asks for it. A player
who has installed their own soundfont hears their own instruments — that is a
property of shipping MIDI and the price of the licence safety.

---

## 7. What I need from other roles

### `mod-engineer` — two MAPINFO lines, **after** the CEO approves

I have not edited `src/lumps/MAPINFO`. If the recommendation in §0 is taken:

```
GameInfo { TitleMusic = "D_SDINTL" }      // add to the existing GameInfo block
map MAP01 { music = "D_SDM01" }           // today: music = ""
```

The lumps would live at `assets/music/<LUMP>.mid`; `sdbuild.pk3.ASSET_DIRS`
already includes `music`, so no build change is needed. **`SNDINFO` is not
involved** — music lumps are not declared there; that lump is for sound
effects and `$musicalias`. If an intermission cue is wanted later,
`D_SDTITL` goes on the `intermission` / `cluster` music key and I will ask
for that line separately.

### `qa-engineer` — three gaps, reported and **not touched** (yours)

1. Nothing checks that a MAPINFO `music = "X"` resolves to a packed lump or a
   known IWAD lump. Textures get exactly this check and it is why blocker M1
   was caught; a music typo instead fails **silently at runtime** — GZDoom
   simply plays nothing.
2. `check_licences` will demand a row for every music lump in
   `docs/art/LICENSES.md` the moment they are packed, because `LICENSED_DIRS`
   includes `music`. Either a backticked row goes there, or the check learns
   about a **`LICENSES.md` of its own under `docs/sound/`**, which does not
   exist yet. I have deliberately **not**
   created a second register: `MUSIC-RIGHTS.md` §4.4 already owns these facts
   and the project rule is one owner per fact. Tell me which file you want to
   read and I will point it there.
3. **An obligation, not a nicety:** the moment a downloaded file is packed the
   mod acquires attribution duties — **Jerry Engelbach** for the
   Internationale, **Robert Clausecker / Mutopia Project** for *Night on Bald
   Mountain*. The PD and CC0 files carry none. Whatever credits mechanism the
   mod grows has to cover this, and §3.1's flagged gap (seven Mutopia piece
   URLs not recorded) has to be closed before those seven could be packed.

Also for QA, the two engine traps in §2.1: `currentmusic` lies when
`snd_musicvolume` is 0, and a `writewave` run that loads a PK3 being rebuilt
can report a timeout on work it already finished.

---

## 8. Decisions needed from the CEO

Superseded items from earlier versions are kept out. These are live.

0. **D16 needs re-wording, and one attribution accepted.** D16 says the music
   is *"our own instrumental MIDI sequences"*. What §0 recommends for the
   title is a **downloaded** sequence under `{{Attribution|Jerry Engelbach}}`.
   The spirit of D16 holds — instrumental MIDI, no Soviet phonogram — but the
   letter does not, and shipping it means **crediting Jerry Engelbach** in the
   mod's credits and the licence register. *Recommendation: accept, and ask
   the PM to record it as a new D-number amending D16.* The alternative is to
   use only the public-domain files, every one of which is a solo-piano score
   preview.
1. **Title screen: approve `work/audio/D_SDINTL.mid`.** Engelbach's orchestral
   Internationale with the two-second head silence removed by us. It is the
   CEO's own choice, it is measurably the best-sounding file we have, its one
   defect is fixed and verified, and the engine plays it with zero errors.
   Listen: `python3 tools/audio/audition.py --play title --lump D_SDINTL`.
2. **MAP01: `D_SDM01` (ours) or a ten-minute piano transcription?**
   **(a) `D_SDM01`** — *my recommendation.* The only piece of any origin
   written as a game loop: 2:22, darkest brightness measured, restarts from
   25 %, no clipping, zero rights to clear, zero cost. It is also the piece
   the CEO called simple, which §8.3 answers directly.
   **(b) `D_CND01`, *Night on Bald Mountain*, orchestrated by us** — the best
   musical material in the set and the right length, but ten minutes of solo
   piano until someone assigns the instruments, and **I cannot judge whether
   that orchestration will sound good** (§5). One focused session, and
   CC BY 3.0 obliges us to credit Clausecker / Mutopia.
   **(c) `D_CND06`, *Dumka*** — same deal, bleaker, slower, and the better
   loop shape of the two piano files.
   Doing nothing is not an option: MAP01's MAPINFO still says `music = ""`.
   **Listen to (b) before deciding** — the piano may be exactly the austerity
   you want: `audition.py --play map01 --candidates --lump D_CND01`.
3. **Do you want `D_SDM01` enriched rather than replaced?** The measurable
   gap between ours and the Internationale is voices (5 against 12) and
   through-composition, not dynamic shape — our arc is in fact wider. Adding
   two more instrumental layers and a non-repeating fourth section is a
   generator change, **hours, not days**, and it keeps the zero-rights
   position. *Recommendation: yes, and do it only after (2) is decided.*
4. **Diegetic radio: approve `WM_Ej_uchnem.mid` and `WM_Kolokolchik.mid`?**
   Both CC0, both already orchestrated, both ~40 s, **no obligation of any
   kind**. The cheapest win on the table. They need a map and a sound-emitting
   actor to live in, which is a request to `level-designer` once approved.
5. **The pieces no free MIDI exists for.** *Marche slave*,
   *Прощание славянки*, *Амурские волны*, *Смело, товарищи, в ногу*,
   *Вы жертвою пали* — all free as compositions, none available as a
   licence-clean MIDI anywhere. Either we sequence them (~2-3 h each,
   kilobytes) or, for *Marche slave* only, we ship IMSLP's CC BY 4.0
   synthesised **MP3** as OGG (megabytes). *Recommendation: sequence
   **Вы жертвою пали** and **Амурские волны** ourselves* — short strophic
   tunes, the most dramatic work per hour of effort, and the two most
   period-correct cues in the whole list.
6. **Confirm the three discards** so I can stop carrying them: `D_CND02`
   (German fugue), `D_CND04` (43 s flat sting), `D_CND08` (children's toy
   march, flattest arc measured). `D_CND03`, `D_CND05` and `D_CND07` stay as
   named reserves rather than discards. Say the word and the discarded files
   leave `work/audio/candidates/`.
