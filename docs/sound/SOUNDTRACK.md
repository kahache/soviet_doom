# Soundtrack — the music lumps, one card per piece

Living document. Owner: `sound-designer`. Russian mirror: `docs/ru/sound/SOUNDTRACK.md` (D7).
Created: 2026-10-13 (F2, first music). Rights frame: `docs/sound/MUSIC-RIGHTS.md`.

Decision **D16** (CEO, 2026-10-13): *"el camino correcto es instrumental en
MIDI"*. No Soviet recording of anything enters this mod.

Revised verdict (CEO, 2026-10-13, same day): the generated pieces are
*"un poco simples"*; **yes to the Internationale** for the title; and
*"no construyas tú los MIDIs, mejor descargarlos"*. So the plan is now:

| | Plan |
|---|---|
| **A — current** | ship **downloaded, licence-cleared** MIDIs of real repertoire. §A below. |
| **B — kept, not deleted** | the two pieces we generated (`tools/audio/gen_music.py`, cards 1 and 2 at the bottom). They remain the fallback for any cue no free MIDI exists for, and they are the reason the rights position is airtight. |

> **Nothing below is approved and nothing is in the PK3.** Candidates live in
> `work/audio/candidates/`, our own drafts in `work/audio/`. Nothing enters
> `assets/` without an explicit approval, exactly as with the textures.

## How to listen

```bash
# the downloaded candidates (packed as D_CND01..D_CND12)
python3 tools/audio/audition.py --pack --candidates          # see the lump map
python3 tools/audio/audition.py --play title --candidates --lump D_CND10
python3 tools/audio/audition.py --play map01 --candidates --lump D_CND01

# our own drafts (plan B)
python3 tools/audio/gen_music.py                     # -> work/audio/*.mid
python3 tools/audio/audition.py --play title         # title screen theme
python3 tools/audio/audition.py --play map01         # MAP01 with its music
```

`audition.py` packs MIDIs into a throwaway overlay PK3 with its own MAPINFO
and loads it **on top of** `dist/sovietdoom.pk3`. The shipped
`src/lumps/MAPINFO` is not touched; deleting `work/audio/sd-music-draft.pk3`
puts everything back. Downloaded files get positional lump names because
their real names are not valid lumps; `--pack --candidates` prints the map and
writes it to `work/audio/candidates-lumps.txt`.

Two other tools, both read-only:

```bash
python3 tools/audio/midi_inspect.py work/audio/candidates/*.mid   # what is IN the file
python3 tools/audio/audition.py --render --candidates             # engine renders each to WAV
```

For plan B, to change how a piece sounds, edit a constant in section 2 of
`tools/audio/gen_music.py` and run the generator again — or, for tempo only:

```bash
python3 tools/audio/gen_music.py --title-tempo 72 --map01-tempo 96
```

---

# A. Downloaded candidates (2026-10-13)

Twelve files, 204 KB total, every one with a **verifiable per-file licence on
the sequencing**, not merely a public-domain composition — the distinction
that disqualifies the entire Soviet-MIDI corpus on the usual free-MIDI sites.
The rights audit, including the eleven sources rejected, is
`docs/sound/MUSIC-RIGHTS.md` §4.4; §1.2 explains why a MIDI needs its own
licence at all. This section is only about **how they sound**.

## A.1 How they were judged

Not by looking at the filenames. Each file was parsed byte by byte
(`tools/audio/midi_inspect.py`: tempo map, General MIDI programs, note count,
hanging notes) and then **synthesised by GZDoom itself** via `writewave`
(`audition.py --render --candidates`), and the resulting WAVs measured for
duration, peak amplitude, clipping and a twelve-slot loudness arc.

All twelve parsed cleanly, all twelve produced sound, **zero hanging notes**
anywhere, and the rendered durations matched the tempo maps to within 1 s.
`logs/audition-render.log`. The engine was confirmed to play one of them for
real: with `D_CND10` wired into MAPINFO, GZDoom's `currentmusic` answers
`Currently playing music 'D_CND10'` on both the title screen and MAP01, with
no errors — `logs/audition-cand-title.log`, `logs/audition-cand-map.log`.

> **Trap for QA, found here:** with `snd_musicvolume 0` GZDoom reports
> *"Currently no music playing"* even when the lump is correctly wired. Any
> future check of `currentmusic` must run with a non-zero music volume
> (`0.02` is inaudible and sufficient).

The WAVs themselves came to **762 MB** for twelve files — 32-bit float at
44.1 kHz, which is what `writewave` emits — so they are **not kept**. The
measurements below are the output; regenerate the audio in one command when
you want to re-check a number:
`python3 tools/audio/audition.py --render --candidates`.

## A.2 The table

Sorted by how useful they are. "Arc" is the measured loudness shape across the
piece, as a percentage of its own loudest moment — the thing the CEO was
missing when he called our own pieces simple.

| Lump | File | Work | Length · tempo | What is actually in the MIDI | Measured arc | Verdict |
|---|---|---|---|---|---|---|
| `D_CND10` | `WM_Internationale_orch2.mid` | **Интернационал**, orchestral | **1:27** · 90 BPM 4/4 | **A real orchestration**: piccolo, flute, oboe, clarinet, bassoon, horn, trumpet, trombone, tuba, timpani, 5 string parts **and a drum channel** — 16 channels, 12 distinct GM voices, 1 063 notes | **37 44 44 36 37 43 57 45 46 78 90 100** | ✅ **TAKE IT. Title screen.** The only downloaded file that is finished music rather than a score preview. One flaw: **1.99 s of digital silence at the head** (§A.4.1) |
| `D_CND01` | `MU_Mussorgsky_BaldMountain.mid` | **Ночь на лысой горе**, Chernov's piano transcription | **10:11** · 180 BPM 2/2 | 9 313 notes, two hands, **no program changes** → solo piano | 98 100 80 83 78 98 85 86 80 79 74 67 | ⚠️ **Best MAP01 candidate, but needs orchestrating by us.** Right length, right menace, wrong timbre |
| `D_CND06` | `MU_Tchaikovsky_Dumka_op59.mid` | **Думка** op. 59, "Russian rustic scene" | **9:33** · 60 BPM, tempo changes | 4 279 notes, solo piano | 55 44 76 63 81 64 96 68 100 80 40 44 | ⚠️ MAP01 alternative: slower, bleaker, genuinely Russian, and its arc already breathes. Same orchestration problem |
| `D_CND09` | `WM_Ej_uchnem.mid` | **Эй, ухнем** (Volga Boatmen), Balakirev | 0:49 · 81 BPM | 4 parts with **real instruments assigned** — violin, cello, oboe, clarinet. CC0 | 70 71 77 70 76 70 88 75 73 79 99 100 | ✅ **Usable as-is.** Too short for a map; ideal diegetic radio or an intermission cue |
| `D_CND12` | `WM_Kolokolchik.mid` | **Колокольчик**, Russian traditional | 0:38 · 80 BPM | celesta, cello, flute. CC0 | 86 93 93 93 92 87 95 100 88 96 86 69 | ✅ **Usable as-is.** Quiet, domestic, slightly sad — the Leninskaya komnata radio |
| `D_CND07` | `MU_Tchaikovsky_Seasons_August.mid` | **Времена года: Август** ("Harvest") | 5:31 · 108 BPM 6/8 | solo piano, agitated perpetual motion | 82 85 85 100 67 63 66 66 83 86 81 100 | ⚠️ Driving enough for a fight, but **peak 0.982 — at the ceiling.** Needs its velocities pulled down before anything else |
| `D_CND03` | `MU_Scriabin_Etude_op2n1.mid` | **Этюд** op. 2 № 1 | 2:15 · 60 BPM 3/4 | solo piano, C♯ minor, dies away | 75 85 63 83 42 62 97 100 62 31 29 20 | ⚠️ **Clips: 4 samples over full scale, peak 1.011.** Fixable. Lovely shape for a death/aftermath cue once fixed |
| `D_CND05` | `MU_Scriabin_Prelude_op59n2.mid` | **Прелюдия** op. 59 № 2 | 1:28 · 126 BPM 6/8 | solo piano, unsettled late Scriabin | 87 91 85 82 94 81 89 100 84 91 90 74 | ⚠️ Good mood for an alien zone, far too short and too flat to loop |
| `D_CND11` | `WM_Internationale_piano_Bb.mid` | **Интернационал**, piano in B♭ | 1:22 · 96 BPM | solo piano, 412 notes, **peak 0.185 — very quiet** | 80 94 100 88 86 91 91 85 84 91 99 80 | ⚠️ Keep as a *diegetic* Internationale (a piano heard through a wall). Not the title |
| `D_CND04` | `MU_Scriabin_Prelude_op11n1.mid` | **Прелюдия** op. 11 № 1 | 0:42 · 140 BPM | solo piano | 74 82 78 86 74 75 81 77 100 96 89 74 | ⚠️ Too short to be anything but a sting |
| `D_CND02` | `MU_RimskyKorsakov_FugueBACH.mid` | *Fugue sur le nom de BACH* | 2:03 · 140 BPM 4/2 | solo piano, academic fugue | 77 88 90 100 88 92 79 95 80 74 81 80 | ❌ **Discard.** Free and clean, but it is a conservatory exercise on a German name. Nothing Russian reaches the listener |
| `D_CND08` | `MU_Tchaikovsky_WoodenSoldiers.mid` | **Марш деревянных солдатиков** | 0:41 · 140 BPM 2/4 | solo piano, toy march | 95 98 95 96 99 94 98 97 95 100 92 92 | ❌ **Discard.** A children's march, and the flattest arc in the set (92-100 throughout). Wrong tone for 1977 and for this game |

## A.3 The honest finding about downloading

The CEO's instinct was right about the Internationale and it paid off
immediately: `D_CND10` is better than anything we would have written, because
Engelbach actually orchestrated it. Read off the file's own channel timeline,
33 bars of 4/4 at 90 BPM:

| Bars | Who is playing |
|---|---|
| 1-9 | **strings alone**, timpani joining at bar 2 |
| 9-13 | **brass choir** — trumpets, trombones, then tuba |
| 13-21 | **woodwinds** (piccolo, flute, oboe, clarinet, bassoon) over strings and timpani |
| 21-25 | horns enter; everything thins to horns and winds |
| 25-33 | **full tutti with percussion** — all sixteen channels |

Its measured arc climbs from 37 % to 100 % across exactly those entries. That
is the shape our own title theme was missing, and it is the thing a generator
writing eight-bar periods does not produce by accident.

But that file is **one of twelve**, and the other eleven are not finished
music. Eight of them come from Mutopia and **every Mutopia MIDI has zero
program changes** — they are LilyPond's audio preview of an engraved score, so
General MIDI plays them as acoustic grand piano from end to end
(`MUSIC-RIGHTS.md` §4.2). The notes are right, the structure is real, the
timbre is a placeholder.

So "download instead of composing" trades one kind of work for another:

| | What we avoid | What we still have to do |
|---|---|---|
| **Downloaded orchestration** (`D_CND10`) | everything | credit Jerry Engelbach |
| **Downloaded score preview** (Mutopia) | writing the notes — and the notes are Mussorgsky's, which is the point | assign GM instruments per staff, balance channel volumes, fix the two clipping files, cut to length |
| **Sequenced by us from a free score** | nothing | everything, but the result is exactly what we want |

**There is no free MIDI of the pieces that would most obviously fit** —
*Marche slave*, *Прощание славянки*, *Амурские волны*, *Смело, товарищи, в ногу*,
*Вы жертвою пали*. For *Marche slave* the only licence-clean ready-made thing
that exists is IMSLP's **CC BY 4.0 synthesised MP3** (not MIDI), which would
cost megabytes instead of kilobytes. For the four Russian songs, every MIDI
online sits on a site with no per-file licence. For those, **sequencing them
ourselves remains the only clean route**, and it is cheap: they are 16- to
32-bar strophic tunes. I estimate **2-3 hours each**, against roughly 1 hour
to orchestrate a Mutopia piano file.

## A.4 What I recommend

1. **Title screen → `D_CND10`, the orchestral Internationale, as-is.** It is
   the CEO's choice, it is legally the cleanest major work we have, and it is
   measurably the best-sounding file in the set. One obligation: credit
   Jerry Engelbach. **One defect, measured and real:** the file opens with
   **1.99 s of absolute digital silence** — not a quiet entry, nothing at all,
   verified sample by sample on the engine's own render. Under a still poster
   that is survivable; on a loop it is a two-second hole every 87 seconds.
   The fix is to shift every event earlier by ~3 beats at 90 BPM, which is a
   mechanical edit to the file, not a re-sequencing. I would do that before it
   ships and I need no decision for it.
2. **MAP01 → `D_CND01`, *Night on Bald Mountain*, orchestrated by us.**
   10 minutes, demonic, Russian, free, and it already matches the map's
   length. The work is assigning instruments to Chernov's two staves, which
   is one focused session, and the CC BY 3.0 licence expressly allows it.
   If the CEO would rather not spend that, the fallback is our own `D_SDM01`
   (card 2), which *is* orchestrated and *is* built to loop.
3. **Diegetic radio → `D_CND09` and `D_CND12`, as-is.** CC0, already
   orchestrated, 40-50 s, perfect for the Leninskaya komnata.
4. **Do not ship `D_CND02` or `D_CND08`.**
5. **Fix before any use: `D_CND03` (clips) and `D_CND07` (at the ceiling).**

---

# B. Our own sequences (plan B, kept)

The CEO's verdict on these was *"están bien las piezas pero un poco simples"*
— which the measurements agree with: `D_SDTITL` is 26 bars of a single 8-bar
period stated twice, where `D_CND10` is a through-composed orchestration with
four distinct instrumental entries. They stay in the repo because they cost
nothing to keep, because `D_SDM01` is still the only *loopable, orchestrated,
map-length* piece we have, and because the generator is the mechanism for the
pieces no free MIDI exists for (§A.3).

## Card 1 — `D_SDTITL`, "Zarya" (title theme)

| Field | Value |
|---|---|
| **Lump** | `D_SDTITL` (7 chars; the `D_` prefix is the Doom convention for a music lump) |
| **File** | `work/audio/D_SDTITL.mid`, 3 315 bytes, SMF format 1, 7 tracks, 480 ticks/beat |
| **Where it plays** | Title screen, under the propaganda poster (`TITLEPIC`). Needs `GameInfo { TitleMusic = "D_SDTITL" }` in MAPINFO — **request to `mod-engineer`, not done by me** |
| **Duration** | 1:21 (81.0 s written; 81.8 s as the engine renders it, the reverb tail included) |
| **Tempo** | 80 BPM, 4/4. Constant `TITLE_TEMPO_BPM` |
| **Key** | D natural minor, with the leading note C# raised only at the cadence (the harmonic-minor dominant that gives Russian marches their bite) |
| **Instruments** (General MIDI) | French horn → trumpet (melody), trombones (harmony), tuba (bass), timpani, string ensemble, tubular bells and one crash on the final chord |
| **Original or sequenced** | **ORIGINAL COMPOSITION**, `sound-designer`, 2026-10-13. Not an arrangement of any existing work; it quotes nothing |
| **Licence** | Soviet Doom project — own work, **CC BY-NC-SA 4.0** (D15). Code that generates it: GPL-3.0 |
| **Rights to clear** | **None.** No composer, no lyricist, no label, no phonogram. This is the whole point of writing it ourselves |

**Form** (26 bars, the last one silent so the loop breathes):

| Bars | What happens |
|---|---|
| 1-4 | Timpani alone on D and A, growing 8 velocity steps a bar; the tuba joins on a **bare fifth** from bar 3. No third: the mode is withheld until the theme states it |
| 5-12 | First statement of the 8-bar period, **horns alone**, trombones on beats 1 and 3 — the march's two feet |
| 13-20 | Same period, **trumpets an octave up with the horns doubling below**, strings sustaining. This is the loudest point and the one the poster is cut to |
| 21-25 | Coda: VI – iv – V7 – i – i, plagal weight then the dominant, the last chord held two bars under a tubular bell on D |
| 26 | Silence |

Measured dynamic arc, from the engine's own render (bar RMS, % of peak):
18 → 23 → 44 → 62 (intro crescendo) · 66-71 (first statement) · **88-100**
(second statement) · 85 → 68 (coda) · 1 (tail). The shape is in the file, not
only in the intention.

**Why it is written this way.** A Soviet *parade* march runs 112-120 BPM, but
this is not a parade — it is the music under a still image. The newsreel and
documentary fanfares of the period sit far slower and heavier, so 80 BPM: a
contained step, serious and not jaunty. If the CEO wants it **more solemn**,
`--title-tempo 72`; **more military**, `--title-tempo 96`; **less brass**, lower
`TITLE_VEL_MELODY` / `TITLE_VEL_HARMONY` or the channel volumes in `TITLE_MIX`.

**Why original and not the Internationale.** The Internationale is the one
major work that is genuinely free in Russia *and* in the United States
(`MUSIC-RIGHTS.md` §3.2), and sequencing it is legally clean. Two reasons it
is not the title theme: it is the most recognisable political melody in the
world and would read as a statement the game does not make at the moment the
player presses Start; and it is better spent where it has dramatic work to do
— the finale, or a diegetic radio. **It remains on the table** and I can
deliver a sequenced instrumental version of it in an hour if the CEO prefers
it. (§ "Decisions needed", point 2.)

---

## Card 2 — `D_SDM01`, "Zarya-7" (MAP01)

| Field | Value |
|---|---|
| **Lump** | `D_SDM01` (7 chars) |
| **File** | `work/audio/D_SDM01.mid`, 8 789 bytes, SMF format 1, 6 tracks, 480 ticks/beat |
| **Where it plays** | MAP01, Zarya-7 cosmodrome, the invasion just begun (`docs/levels/MAP01-zarya-7.md`). Needs `music = "D_SDM01"` in the MAPINFO `map MAP01` block, which today says `music = ""` — **request to `mod-engineer`** |
| **Duration** | 2:22 per loop (142.2 s written, 142.8 s rendered). The map is 5-8 minutes, so the player hears 2 to 3.5 loops |
| **Tempo** | 108 BPM, 4/4. Constant `MAP01_TEMPO_BPM` |
| **Key** | D minor with a flat second (Eb) leaning on the tonic — the oldest "something is wrong" interval there is, and it costs one note |
| **Instruments** (General MIDI) | Synth bass 2 (the ostinato), tremolo strings, pad "halo", trombones (stabs), FX "crystal" (the distant signal), GM percussion: low floor tom, low tom, bass drum, snare, ride, crash |
| **Original or sequenced** | **ORIGINAL COMPOSITION**, `sound-designer`, 2026-10-13. Written in the idiom of Eduard Artemyev's ANS electronics (*Solaris*, *Stalker*) crossed with Doom's ostinato-and-percussion habit. Artemyev's own music is protected and **none of it is used**; style is not copyrightable, which is the same finding the poster research reached |
| **Licence** | Own work, **CC BY-NC-SA 4.0** (D15) |
| **Rights to clear** | **None** |

**Form** (64 bars, four 16-bar sections, seamless loop):

| Section | Bars | What is on top of the ostinato |
|---|---|---|
| **A — pulse** | 1-16 | The bass figure and two toms. Nothing else. The base is still standing and the player is walking through it |
| **B — dread** | 17-32 | Tremolo strings crawl up a chromatic line (D–Eb–E–F–F#–G–Ab–A, two bars a step), a cold pad underneath, bass drum enters |
| **C — alarm** | 33-48 | Trombone stabs on and off the beat, alternating the tonic triad with its **Neapolitan** a semitone above; march snare on 2 and 4 — the Soviet half of the texture |
| **D — release** | 49-64 | Everything drops away to the pad and four far-off signals. The last four bars are nearly silent |

Measured arc from the engine's render: A flat at 55 % · B 90 % · C 96-100 % ·
D 79 → 74 → 49 → **5 %**. That last number is the design: **the loop restarts
from near-silence, not from a cut**, which is what keeps it from wearing a
hole in the player over eight minutes. The other two defences are the length
(2:22, long enough that the ear does not pre-hear it) and the riff variant
that fires every fourth bar (`MAP01_OSTINATO_VARIANT_EVERY`) so the ostinato
never settles into a one-bar groove.

If the CEO finds it **too busy**, the cheapest cut is `MAP01_VEL_BRASS` or
deleting the snare lines in section C. **Too slow for a fight**: 120 BPM.
**Too long before anything happens**: shorten `MAP01_SECTION_BARS` to 12.

---

## How this was verified

Not "the file exists" — the engine parsed it, synthesised it and played it.

| Claim | Evidence |
|---|---|
| The bytes are a valid Standard MIDI File | re-parsed independently: every chunk length exact, no trailing bytes, no running-status error, **zero hanging notes** (every note-on has its note-off) |
| GZDoom plays it at the title screen | `currentmusic` in the console answers `Currently playing music 'D_SDTITL'` — `logs/audition-title.log` |
| GZDoom plays it on MAP01 | `currentmusic` answers `Currently playing music 'D_SDM01'` — `logs/audition-ingame.log` |
| It makes actual sound, not silence | GZDoom's own `writewave` rendered both to WAV: `D_SDTITL` 81.8 s, peak 0.314 of full scale; `D_SDM01` 142.8 s, peak 0.443. Written to `work/audio/render/` |
| The sections are really there | per-bar RMS of those renders matches the written form bar for bar (the two tables above) |
| The build is unaffected | `tools/build.py` → 34 files, no music lump; `check_pk3.py` PASS; `smoke.py --map MAP01` PASS; 189 unit tests OK |
| The generator is reproducible | two consecutive runs produce byte-identical files (sha256 `6f74c093…` / `c0fce282…`) |

**Which synthesiser the player will hear** (verified on this machine, GZDoom
4.14.2 macOS): `snd_mididevice` is **-5 (FluidSynth)** and `fluid_patchset` is
**`gzdoom`**, which resolves to `GZDoom.app/Contents/MacOS/soundfonts/gzdoom.sf2`
— a 3.3 MB General MIDI soundfont **bundled with every GZDoom install**. So
these pieces sound the same for every player on a stock engine; we are not at
the mercy of a system synth, and we are not getting OPL FM unless a player
chooses it. A player who has set their own soundfont will hear their own
instruments — that is a property of shipping MIDI and is the price of the
licence safety.

---

## What I need from other roles

**`mod-engineer`** — two MAPINFO lines, only once the CEO has approved the
music. I have not edited `src/lumps/MAPINFO`:

```
GameInfo { TitleMusic = "D_SDTITL" }      // add to the existing GameInfo block
map MAP01 { music = "D_SDM01" }           // today: music = ""
```

Those two names are **plan B's**. If the CEO takes the recommendation in
"Decisions" below, the title lump is the downloaded Internationale instead and
the names become `D_SDINTL` and whatever MAP01 ends up being; I will give you
the final pair with the approved files, renamed from `D_CNDnn` to real `SD`
lump names, and never as `D_CNDnn`.

The lumps live at `assets/music/<LUMP>.mid`; `sdbuild.pk3.ASSET_DIRS` already
includes `music`, so no build change is needed. `SNDINFO` is **not** involved:
music lumps are not declared there (that lump is for sound effects and
`$musicalias`).

**`qa-engineer`** — two gaps in `tools/check_pk3.py`, reported and **not
touched** because that file is yours:

1. Nothing checks that a MAPINFO `music = "X"` resolves to a packed lump or a
   known IWAD lump. Textures get exactly this check and it is the reason
   blocker M1 was caught; music has no equivalent, so a typo in a music name
   fails **silently at runtime** (GZDoom just plays nothing).
2. `check_licences` will demand a row for every music lump in
   `docs/art/LICENSES.md` the moment they are packed, because `LICENSED_DIRS`
   includes `music`. Either a backticked row is added there, or the check
   learns about a sibling `docs/sound/LICENSES.md`. `MUSIC-RIGHTS.md` §6
   already flagged that the CEO may prefer the split; it is now a concrete
   choice. I have deliberately **not** created a second register, because
   `MUSIC-RIGHTS.md` §4.4 already owns these facts and the project rule is one
   owner per fact — tell me which file you want to read and I will point it
   there.
3. **New, and this one is an obligation, not a nicety:** the moment a
   downloaded file is packed, the mod acquires attribution duties —
   **Jerry Engelbach** for the Internationale, **Robert Clausecker / Mutopia
   Project** for *Night on Bald Mountain*. Public-domain and CC0 files carry
   none. Whatever credits mechanism the mod ends up with has to cover this;
   `MUSIC-RIGHTS.md` §4.4 is the authoritative list of who is owed what.

---

## Decisions needed from the CEO

Superseded items from the first version of this document are kept out; what
follows is the state after the CEO's 2026-10-13 verdict.

1. **Title screen: approve `D_CND10`** — Engelbach's orchestral Internationale,
   downloaded, licence-clean, measurably the best file in the set (§A.2).
   Listen with
   `python3 tools/audio/audition.py --play title --candidates --lump D_CND10`.
   Approving it means **crediting Jerry Engelbach** in the mod's credits and
   in the licence register (`MUSIC-RIGHTS.md` §7.0). It is attribution-only,
   not public domain.
2. **MAP01: which of the three routes?**
   **(a)** `D_CND01`, *Night on Bald Mountain*, **orchestrated by us** — one
   focused session of work, the best musical result, CC BY 3.0 obliges us to
   credit Robert Clausecker / Mutopia. *My recommendation.*
   **(b)** `D_CND06`, *Dumka*, same deal, bleaker and slower.
   **(c)** keep our own `D_SDM01` (card 2) — already orchestrated, already
   loops, costs nothing more, but it is the piece the CEO called simple.
   Doing nothing is not an option: MAP01's MAPINFO still says `music = ""`.
3. **Do you want the pieces no free MIDI exists for?** *Marche slave*,
   *Прощание славянки*, *Амурские волны*, *Смело, товарищи, в ногу*,
   *Вы жертвою пали* — all free as compositions, none of them available as a
   licence-clean MIDI anywhere (§A.3). The only ways to have them are to
   sequence them ourselves (~2-3 h each, kilobytes) or, for *Marche slave*
   only, to ship IMSLP's CC BY 4.0 synthesised **MP3** as OGG (megabytes).
   **My recommendation: sequence *Вы жертвою пали* and *Амурские волны*
   ourselves** — they are short strophic tunes, they do the most dramatic work
   per minute of effort, and they are the two most period-correct cues in the
   whole list.
4. **Diegetic radio: approve `D_CND09` (Эй, ухнем) and `D_CND12`
   (Колокольчик)?** Both CC0, both already orchestrated, both ~40 s. No
   obligation of any kind. Cheapest win available.
