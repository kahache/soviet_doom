# Soundtrack — the music lumps, one card per piece

Living document. Owner: `sound-designer`. Russian mirror: `docs/ru/sound/SOUNDTRACK.md` (D7).
Created: 2026-10-13 (F2, first music). Rights frame: `docs/sound/MUSIC-RIGHTS.md`.

Decision **D16** (CEO, 2026-10-13): *"el camino correcto es instrumental en
MIDI"*. No Soviet recording of anything enters this mod. Everything we ship
is sequenced by us, which removes the phonogram right and the lyric right in
one move and reduces a whole soundtrack to a few kilobytes of PK3.

> **Status of both pieces below: DRAFT, awaiting the CEO.** The files live in
> `work/audio/` and are **not** packed into `dist/sovietdoom.pk3`. Nothing
> enters `assets/` without an explicit approval, exactly as with the textures.

## How to listen

```bash
python3 tools/audio/gen_music.py                     # -> work/audio/*.mid
python3 tools/audio/audition.py --play title         # title screen theme
python3 tools/audio/audition.py --play map01         # MAP01 with its music
```

`audition.py` packs `work/audio/*.mid` into a throwaway overlay PK3 with its
own MAPINFO and loads it **on top of** `dist/sovietdoom.pk3`. The shipped
`src/lumps/MAPINFO` is not touched; deleting `work/audio/sd-music-draft.pk3`
puts everything back. To change how a piece sounds, edit a constant in
section 2 of `tools/audio/gen_music.py` and run the generator again — or, for
tempo only, without editing anything:

```bash
python3 tools/audio/gen_music.py --title-tempo 72 --map01-tempo 96
```

---

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

The lumps will then live at `assets/music/D_SDTITL.mid` and
`assets/music/D_SDM01.mid`; `sdbuild.pk3.ASSET_DIRS` already includes `music`,
so no build change is needed. `SNDINFO` is **not** involved: music lumps are
not declared there (that lump is for sound effects and `$musicalias`).

**`qa-engineer`** — two gaps in `tools/check_pk3.py`, reported and **not
touched** because that file is yours:

1. Nothing checks that a MAPINFO `music = "X"` resolves to a packed lump or a
   known IWAD lump. Textures get exactly this check and it is the reason
   blocker M1 was caught; music has no equivalent, so a typo in a music name
   fails **silently at runtime** (GZDoom just plays nothing).
2. `check_licences` will demand a row for `D_SDTITL` / `D_SDM01` in
   `docs/art/LICENSES.md` the moment they are packed, because `LICENSED_DIRS`
   includes `music`. Either a backticked row is added there, or the check
   learns about a sibling `docs/sound/LICENSES.md`. `MUSIC-RIGHTS.md` §6
   already flagged that the CEO may prefer the split; it is now a concrete
   choice.

---

## Decisions needed from the CEO

1. **Approve or reject these two drafts**, after listening with the two
   commands at the top. If they pass, they move to `assets/music/` and I ask
   `mod-engineer` for the two MAPINFO lines. Both are cheap to change: tempo,
   instruments and section lengths are all named constants.
2. **Is the title theme original, or the Internationale?** I recommend
   original, which is what D16 ratified, and I have delivered it. But a
   sequenced instrumental Internationale is legally just as clean
   (`MUSIC-RIGHTS.md` §3.2: free in Russia *and* the United States,
   composition and Russian text) and carries weight nothing original can buy
   in 80 seconds. If you want to hear both before deciding, say so and I will
   sequence it.
3. **How much more music, and in what order?** The cheapest useful additions,
   in the order I would write them: an intermission cue (~30 s), a death /
   aftermath cue built on *Вы жертвою пали* (free words and music in both
   countries, `MUSIC-RIGHTS.md` §2.2), and diegetic radio for the Leninskaya
   komnata — *Амурские волны* (Kyuss 1909, fully free) is period-plausible
   and would make that room feel inhabited. None of these blocks MAP01.
