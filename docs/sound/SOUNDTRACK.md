# Soundtrack — the music lumps, one card per piece

Living document. Owner: `sound-designer`. Russian mirror: `docs/ru/sound/SOUNDTRACK.md` (D7).
Created 2026-10-13 (F2, first music); candidate list **closed** 2026-10-13.
Rights frame: `docs/sound/MUSIC-RIGHTS.md` — that document owns every licence
fact and this one owns every sound fact.

Decision **D16** (CEO, 2026-10-13): *"el camino correcto es instrumental en MIDI"*.
No Soviet recording of anything enters this mod.
Same day, two further CEO instructions: *"no construyas tú los MIDIs, mejor
descargarlos"* and *"Sí a LA INTERNACIONAL"* for the title screen, plus the
verdict that our own two pieces are *"un poco simples"*. Those instructions
are recorded as **D23** (CEO, 2026-10-13, `docs/PRD.md` §5), which amends
D16: *"Free MIDI sequences with a verified licence come first, our own
sequencing is the fallback for works that exist only as free scores. La
Internacional is the title theme. The three-rights rule of D16 stands in
full."* So a downloaded, attribution-licensed title sequence is now the
decided route, not a departure from it.

**D43** (CEO, 2026-10-13): *"Acepto las recomendaciones de música"* — every
open recommendation of §8 accepted. What that changed, in one place:

> **Two lumps are installed and packed: `assets/music/D_SDINTL.mid` (title)
> and `assets/music/D_SDM01.mid` (MAP01).** Both are byte-identical to the
> `work/audio/` files the CEO's acceptance refers to, and both regenerate from
> their sources byte for byte (`tests/test_music.py`). They are **not yet
> heard in the game**: `src/lumps/MAPINFO` still says `music = ""` until
> `mod-engineer` adds the two lines of §7. Jerry Engelbach is credited
> (Card 0, `MUSIC-RIGHTS.md` §4.5).
>
> **`work/audio/candidates/` is tracked in git** since D43 (a `.gitignore`
> exception for that folder only), with every file's SHA-256 and source page
> in `MUSIC-RIGHTS.md` §4.4; the sourcing gap of §3.1 is closed. Three
> candidates were discarded (§3). Everything else in `work/audio/` — our
> drafts, renders, the overlay PK3 — stays gitignored, as before.
>
> **Candidate lump names are now stable.** They used to be positional, so
> deleting the discards would have renamed nine pieces. They now come from
> the registry `work/audio/candidates/LUMPS.txt`: `D_CND10` is Engelbach's
> Internationale for good, and retired numbers are never reused.

---

## 0. What plays where (settled by D43)

| Cue | File | Status |
|---|---|---|
| **Title screen** | **`assets/music/D_SDINTL.mid`** — Engelbach's orchestral *Internationale*, head silence removed by us | **installed** (D43); MAPINFO line owed by `mod-engineer` |
| **MAP01** | **`assets/music/D_SDM01.mid`** — our own "Zarya-7" | **installed** (D43) as it stood; the enriched version `D_SDM01E` is a draft for the CEO's ear (§6, Card 2b) |
| **Diegetic radio** | `WM_Ej_uchnem.mid` (`D_CND09`), `WM_Kolokolchik.mid` (`D_CND12`) — CC0, already orchestrated | **settled** (D43); not installed until a map has a radio to put them in (`level-designer`) |
| **Anthem slot** | Glinka's *Patriotic Song*, sequenced by us | **settled** (D43); to be sequenced by us |
| **Death / aftermath** | «Вы жертвою пали», sequenced by us | **settled** (D43); to be sequenced by us |
| **Radio waltz** | «Амурские волны» (Kyuss, 1909), sequenced by us | **settled** (D43); to be sequenced by us |
| **Our `D_SDTITL`** | **reserved, not retired** | a finished 1:21 Soviet march in D minor, the natural intermission / episode-end cue |

Three of the twelve downloads are **discarded** and gone, six are kept as
named reserves (§3). Two needed repair and got it (§5). Works restored in
the United States are excluded (`MUSIC-RIGHTS.md` §5(b)).

---

## 1. How to listen

The CEO heard nothing on the first attempt because his personal `gzdoom.ini`
had `snd_musicvolume` at **0** while the engine was playing correctly. The
tool no longer depends on anyone's mixer: it passes `-config` pointing at
`logs/gzdoom-tooling.ini` and sets `snd_musicvolume 0.8` on the command line,
so it also stops writing state back into the CEO's own preferences.

```bash
python3 tools/build.py                                   # the overlay loads on top of this

# the two installed lumps (D43), heard from their identical work/audio copies
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play title --lump D_SDINTL   # the Internationale, repaired
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play map01 --lump D_SDM01    # our MAP01 loop

# the D43 drafts, for the CEO's ear
python3 tools/audio/gen_music.py                                                  # regenerates every draft into work/audio/
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play map01 --lump D_SDM01E   # MAP01 enriched (Card 2b)
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --render --expect D_SDM01E=160 # its arc and peak (PM only)

# our title march, now proposed for the intermission instead
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play title --lump D_SDTITL

# the downloaded candidates (packed under their stable D_CNDnn names from
# work/audio/candidates/LUMPS.txt; the map is printed)
python3 tools/audio/audition.py --pack --candidates
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play map01 --candidates --lump D_CND01   # Bald Mountain
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --play title --candidates --lump D_CND09   # Эй, ухнем
```

Since D26 `audition.py` refuses to start GZDoom unless `SD_ALLOW_ENGINE=1` is
set (`--pack` works without it): the PM or the CEO sets it, never an agent.

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
SD_ALLOW_ENGINE=1 python3 tools/audio/audition.py --render --candidates     # ~3 min, writes 762 MB of WAV
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

Twelve files were downloaded, **186 170 B (182 KiB)** in total; **nine
remain** after D43 discarded `D_CND02`, `D_CND04` and `D_CND08` (struck
through below, kept so the record stays whole; the files are gone). Two
tables, one key: the lump name. The first is where each file came from and what we may do with it; the
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
| `D_CND06` | `MU_Tchaikovsky_Dumka_op59.mid` · 36 268 B | **Думка** / *Dumka* op. 59 (1886), "Russian rustic scene" | https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=341 | Mutopia, maintainer Vassily Checkin (LilyPond 2.18.0, staves `up`/`down`) | **Public Domain** | ✅ |
| `D_CND07` | `MU_Tchaikovsky_Seasons_August.mid` · 21 748 B | **Времена года: Август** / *Vremena goda: Avgust* ("Harvest", 1876) | https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=803 | Mutopia, maintainer Till Rettig (LilyPond 2.8.6, 21 Aug 2006) | **Public Domain** | ✅ |
| `D_CND03` | `MU_Scriabin_Etude_op2n1.mid` · 10 313 B | **Этюд** / *Etyud* op. 2 № 1 (1887) | https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1029 | Mutopia, maintainer Guy D. Lederfein (LilyPond 2.10.29) | **Public Domain** | ✅ |
| `D_CND05` | `MU_Scriabin_Prelude_op59n2.mid` · 7 789 B | **Прелюдия** / *Prelyudiya* op. 59 № 2 (1910) | https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=445 | Mutopia, maintainer Federico Bruni (LilyPond 2.18.0) | **Public Domain** | ✅ |
| ~~`D_CND04`~~ | ~~`MU_Scriabin_Prelude_op11n1.mid`~~ · 4 910 B | **Прелюдия** op. 11 № 1 | Mutopia id 1779 | Mutopia Project (LilyPond) | **Public Domain** | **discarded (D43)** |
| ~~`D_CND02`~~ | ~~`MU_RimskyKorsakov_FugueBACH.mid`~~ · 5 649 B | *Fugue sur le nom de BACH*; Rimsky-Korsakov d. 1908 | Mutopia | Mutopia Project (LilyPond) | **Public Domain** | **discarded (D43)** |
| ~~`D_CND08`~~ | ~~`MU_Tchaikovsky_WoodenSoldiers.mid`~~ · 2 983 B | **Марш деревянных солдатиков** / *Marsh derevyannykh soldatikov* op. 39 | Mutopia id 1806 | Mutopia Project (LilyPond) | **Public Domain** | **discarded (D43)** |

> **The sourcing gap is closed (2026-10-13).** The per-piece Mutopia URL had
> been recorded only for *Night on Bald Mountain*. The four Mutopia pieces
> that remain were re-read at their piece records; URL, maintainer and
> licence are in the table above and in `MUSIC-RIGHTS.md` §4.4, and each
> page's LilyPond version matches the one embedded in the file. All four are
> Public Domain.

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
| ~~`D_CND04`~~ | 0:42.7 · 140 BPM | 0 · 2 | 11.2 · 5.6 | 0.416 · none | none | 74 82 78 86 74 75 81 77 100 96 89 74 (26) | ❌ **discarded (D43).** 43 s, flat, solo piano. Nothing it could be but a sting, and we have better stings | — |
| ~~`D_CND02`~~ | 2:04 · 140 BPM 4/2 | 0 · 2 | 5.0 · 2.5 | 0.645 · none | none | 77 88 90 100 87 92 79 95 80 74 81 80 (26) | ❌ **discarded (D43).** Free and clean, and musically irrelevant to us: a conservatory fugue on a **German** name. Nothing Russian reaches the listener | — |
| ~~`D_CND08`~~ | 0:41.1 · 140 BPM 2/4 | 0 · 2 | 7.9 · 3.9 | 0.344 · none | none | 95 98 95 96 99 93 98 97 94 100 92 92 **(8)** | ❌ **discarded (D43), the clearest discard in the set.** Arc spread **8 points** — measurably the flattest thing we have, a children's toy march. Wrong tone for 1977 and for this game | — |

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
in the licence register — cheap, but real. **The CEO accepted it (D43).**

**Lump name**: `D_SDINTL` (8 characters, the `D_` music prefix plus `SD` per
D1). The repaired file is the one that ships; the download stays in
`work/audio/candidates/` untouched as the provenance original.

### Card 0 — `D_SDINTL`, *The Internationale* — **installed, title screen (D43)**

| Field | Value |
|---|---|
| **Lump** | `D_SDINTL` |
| **File** | `assets/music/D_SDINTL.mid`, 8 921 B, SMF format 0, 1 track, 960 ticks/beat, SHA-256 `c94e4903…85a9`; byte-identical to `work/audio/D_SDINTL.mid` |
| **Where it plays** | the title screen (`GameInfo { TitleMusic = "D_SDINTL" }`, owed by `mod-engineer`, §7) |
| **Duration · tempo** | 1:25.3 per loop, 90 BPM 4/4; 1 063 notes, 12 GM voices on 16 channels, zero hanging notes |
| **Origin** | *L'Internationale*, Pierre De Geyter, 1888 (public domain); MIDI sequence by **Jerry Engelbach**, 2003, from Wikimedia Commons; 1.99 s of leading silence removed by us (§4.1) |
| **Credit (required)** | **"MIDI sequence by Jerry Engelbach"** — the full line and where it stands: `MUSIC-RIGHTS.md` §4.5 |
| **Reproducible** | `tests/test_music.py` rebuilds it from `work/audio/candidates/WM_Internationale_orch2.mid` with `midi_edit`'s `--trim-head` and compares the hash |

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

### Card 2 — `D_SDM01`, "Zarya-7" — **installed for MAP01 (D43)**

| Field | Value |
|---|---|
| **Lump** | `D_SDM01` (7 chars) |
| **File** | `assets/music/D_SDM01.mid`, 8 789 B, SMF format 1, 6 tracks, 480 ticks/beat, SHA-256 `c0fce282…118b`; byte-identical to `work/audio/D_SDM01.mid` and to what `tools/audio/gen_music.py --only map01` writes (`tests/test_music.py`) |
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
happens**: `MAP01_SECTION_BARS` 12. **Too simple**: the enrichment the CEO accepted in D43 (§8.3).

### Card 2b — `D_SDM01E`, "Zarya-7" enriched — **draft for the CEO's ear (D43)**

D43 accepted §8.3: *two more instrumental layers and a non-repeating fourth
section, keeping the zero-rights position and the loop*. This is that, as a
draft. **The installed `assets/music/D_SDM01.mid` is untouched**; the draft
sits in `work/audio/D_SDM01E.mid` under a draft lump name so the two can be
heard side by side. If the CEO approves it, it is copied over
`assets/music/D_SDM01.mid` (the lump name MAP01 uses stays `D_SDM01`) and
`tests/test_music.py`'s reproducibility check moves to the new builder.

| Field | Value |
|---|---|
| **Lump (draft)** | `D_SDM01E` → becomes `D_SDM01` on approval |
| **File** | `work/audio/D_SDM01E.mid`, 9 658 B, SMF format 1, 8 tracks, 480 ticks/beat |
| **Generator** | `tools/audio/gen_music.py --only map01e` (`build_map01_enriched`); the original `build_map01` is **frozen**, because it is what the installed lump is |
| **Duration · tempo** | **2:40** per loop (72 bars; was 2:22, 64 bars), 108 BPM 4/4, D minor |
| **Voices** | **7 GM programs** (was 5): the five of Card 2 plus **French horns** (program 60, 0-based, as `midi_inspect.py` prints it) and **cellos** (program 42); 1 046 notes, zero hanging notes |
| **Original or sequenced** | **ORIGINAL COMPOSITION**, `sound-designer`, 2026-10-13. Quotes nothing |
| **Licence · rights to clear** | own work, CC BY-NC-SA 4.0 (D15) · **none** |

**What changed, section by section** (A-C keep every note they had; the new
layers are added on top):

| Section | Bars | Before | Added |
|---|---|---|---|
| A — pulse | 1-16 | ostinato, two toms | **cellos** from bar 9: a slow descending tetrachord D–C–B♭–A under the ostinato, so the opening has a line, not only a riff |
| B — dread | 17-32 | crawl, pad, bass drum | **cello pedal** on low D; **horns** from bar 25 wobbling A–B♭–A♭–A against the crawl's F♯–G–A♭–A: semitone friction, not a tune |
| C — alarm | 33-48 | stabs on I and its Neapolitan, march snare | **horns** climbing in half-bar steps D–F–E♭–G–F–A–B♭–A over the stabs; **cellos** pressing D against E♭, the stab harmony one octave down |
| **D — lament** | **49-64** | (was the release) | **NEW and through-composed.** The ostinato stops. Sixteen bars, one chord each (i–VI–iv–V–i6–♭II–iv6–V7–VI–III6–iv–♭II–i64–VI–V–i), **no bar repeats another** (`tests/test_music.py` checks it). Horns carry the melody, peaking on F5 at bar 61; cellos answer in contrary motion; the bass walks root and fifth; tremolo strings and the bass drum join only for the five bars of the climb (57-61) |
| E — release | 65-72 | the old release, shortened to 8 bars | four bars of quiet ostinato and the far-off signals, then pad alone on the open tonic fifth. **The last two bars start nothing**, and bar 1 of the loop is note-for-note bar 1 of the installed piece (both tested) |

**What I cannot tell you** (§2): whether the horn line sounds noble or
sentimental in `gzdoom.sf2`, and whether the lament's tempo, at the map's
108 BPM, feels like mourning or like hurry. That is the CEO's ear. Knobs:
horns too forward → `MAP01E_VEL_HORN` or `MAP01E_MIX_EXTRA["horns"]`;
lament too long → shorten `MAP01E_LAMENT_*` in step (the test checks the
three lists stay the same length); cellos muddy under the ostinato → drop
`MAP01E_A_CELLO`.

**Not measured yet**: no `writewave` render of this draft exists — that
needs the engine (D26). The PM's render command is in §1; it would give the
arc and peak the other cards carry.

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

### `mod-engineer` — two MAPINFO lines, **now** (D43)

The lumps are in `assets/music/` and the build packs them as
`music/D_SDINTL.mid` and `music/D_SDM01.mid` (`sdbuild.pk3.ASSET_DIRS`
already included `music`; checked with `tools/check_pk3.py`: licences OK,
VERDICT PASS). I have not edited `src/lumps/MAPINFO`; it is yours:

```
GameInfo { TitleMusic = "D_SDINTL" }      // add to the existing GameInfo block
map MAP01 { music = "D_SDM01" }           // today: music = ""
```

**`SNDINFO` is not involved** — music lumps are not declared there; that
lump is for sound effects and `$musicalias`. If an intermission cue is
wanted later, `D_SDTITL` goes on the `intermission` / `cluster` music key
and I will ask for that line separately. The engine pass that proves both
play in the real game (`currentmusic`, with a non-zero music volume — §2.1)
is owed by the PM after the lines land.

### `level-designer` — a radio, when a map has a room for it

The diegetic radio pieces are settled (D43): `WM_Ej_uchnem.mid` and
`WM_Kolokolchik.mid`. They need a map position and a sound-emitting actor
(a radio in the Leninskaya komnata). When that exists I install them as
`D_SD`-named lumps with their LICENSES rows; nothing to do before.

### `qa-engineer` — gaps, reported and **not touched** (yours)

1. Nothing checks that a MAPINFO `music = "X"` resolves to a packed lump or a
   known IWAD lump. Textures get exactly this check and it is why blocker M1
   was caught; a music typo instead fails **silently at runtime** — GZDoom
   simply plays nothing. **Now live**: two music lumps are packed and
   `mod-engineer` is about to reference them.
2. ~~`check_licences` will demand a row for every music lump~~ — **resolved
   2026-10-13**: rows for `D_SDINTL` and `D_SDM01` are in
   `docs/art/LICENSES.md` § Music, pointing at `MUSIC-RIGHTS.md` §4.4; no
   second register was created.
3. **The credit obligation is live**: `D_SDINTL` is packed, so the mod owes
   the Engelbach line of `MUSIC-RIGHTS.md` §4.5 wherever it credits anyone.
   The in-game credits screen does not exist yet (G6); whoever builds it
   carries that line.

Also for QA, the two engine traps in §2.1: `currentmusic` lies when
`snd_musicvolume` is 0, and a `writewave` run that loads a PK3 being rebuilt
can report a timeout on work it already finished.

---

## 8. Decisions — all settled by D43

On 2026-10-13 the CEO accepted every open recommendation of this section:
*"Acepto las recomendaciones de música"* (**D43**, `docs/PRD.md` §5). The
items as they stood, and what each became:

0. **Engelbach attribution — ACCEPTED.** Jerry Engelbach is credited
   (`MUSIC-RIGHTS.md` §4.5, `docs/art/LICENSES.md` § Music, Card 0,
   `LICENSE.md`).
1. **Title screen — `D_SDINTL` APPROVED and installed** in `assets/music/`.
2. **MAP01 — (a) `D_SDM01`, ours, APPROVED and installed** as it stood.
   Bald Mountain and *Dumka* stay reserves.
3. **Enrich `D_SDM01` — YES.** Done as a draft: `work/audio/D_SDM01E.mid`,
   Card 2b (§6). The installed file is not touched until the CEO approves
   the enriched one by ear.
4. **Diegetic radio — `WM_Ej_uchnem.mid` and `WM_Kolokolchik.mid`, both CC0,
   SETTLED.** They wait for a map with a radio (§7, `level-designer`).
5. **Sequence «Вы жертвою пали» and «Амурские волны» ourselves — YES.**
   Drafts go to `work/audio/` (§6). Glinka's *Patriotic Song* takes the anthem slot (rights
   side: `MUSIC-RIGHTS.md` §7.1), also sequenced by us.
   **Excluded:** every work free in Russia but restored in the United States,
   «Священная война» above all (`MUSIC-RIGHTS.md` §5(b)).
6. **The three discards — CONFIRMED and removed**: `D_CND02` (German fugue),
   `D_CND04` (43 s flat sting), `D_CND08` (children's toy march). `D_CND03`,
   `D_CND05` and `D_CND07` stay as named reserves. `work/audio/candidates/` is
   tracked in git (D43).

**Open for the CEO's ear, not for a decision of principle:** the drafts that
follow from 3 and 5 — enriched `D_SDM01` and the sequenced pieces. Each will
be one command to hear (§1).
