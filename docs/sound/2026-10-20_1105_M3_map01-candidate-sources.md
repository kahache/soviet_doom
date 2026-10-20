# MAP01 candidates — where a licence-clean MIDI or score exists

Dated snapshot. Owner: `sound-designer`. 2026-10-20 11:05.
Mandate: **D86** (CEO: *"descarguémosla"* for all five MAP01 candidates; the
PM downloads, rights per `MUSIC-RIGHTS.md`), under **D59** (no composing or
sequencing by us; a licence-clean MIDI may be downloaded instead) and **D83**
(MAP01 needs another public-domain piece). **Research only: nothing was
downloaded.** Every licence below was read from the file's own page
(Commons raw wikitext or API, IMSLP work page, Mutopia piece record,
OpenGameArt node) on 2026-10-20, not from a search snippet.

> **One rule conflict, flagged before anything else.** The brief listed
> CC BY-SA as acceptable. `MUSIC-RIGHTS.md` §1.3 (D15) says it is **not**:
> our assets ship under CC BY-NC-SA 4.0, and ShareAlike forbids adding NC.
> This document follows D15: CC BY-SA and GFDL hits are listed as
> **rejected**. CC BY-NC and CC BY-NC-SA *are* usable (§1.3).

## 0. Verdict in one table

| # | Candidate | Licence-clean **MIDI** found? | Best clean alternative found | Status |
|---|---|---|---|---|
| 1 | «Красная армия всех сильней» (S. Pokrass, 1920) | **No** | none — no clean score either | ❌ dead end for now |
| 2 | Ippolitov-Ivanov, *Procession of the Sardar* | **No** | PD scores on IMSLP (CAPTCHA); no free recording | ⚠️ score only → needs sequencing (blocked by D59) |
| 3 | Borodin, *In the Steppes of Central Asia* | **No** | **CC0 full-orchestra recording on Commons, 7:38, 4.7 MB OGG** | ✅ **downloadable today, no obligation** — but audio, not MIDI |
| 4 | Mussorgsky, *Night on Bald Mountain* (fuller than Mutopia piano) | **One, conditional**: OpenGameArt CC0 synth MIDI, sequencer unstated | IMSLP **CC BY 4.0** synthesised orchestral MP3 (Quinn Mason, 10:52) | ⚠️ MIDI has a provenance gap; MP3 is clean but behind CAPTCHA |
| 5 | «Смело, товарищи, в ногу» (Radin) | **No** (Commons MIDI is GFDL, 16 s) | a PD-scan 1930 songbook on Commons, p. 68 (arrangement by V. Bely, protected in RU) | ⚠️ melody source only → needs sequencing (blocked by D59) |

**Plainly:** for none of the five does a licence-clean, full, *orchestral
MIDI* exist in the verifiable sources. The online MIDI corpus for these
pieces lives on the aggregators `MUSIC-RIGHTS.md` §1.2 already excludes.

## 1. Detail per candidate

### 1.1 «Красная армия всех сильней» (Pokrass, 1920) — nothing usable

| Source checked | Result |
|---|---|
| Wikimedia Commons, file search (Cyrillic and Latin titles, "White Army, Black Baron", "Krasnaya Armiya") | no MIDI, no audio, no score of the 1920 song |
| Same melody under another title: *Die Arbeiter von Wien* (Fritz Brügel's text on Pokrass's tune, per de.wikipedia) | `File:Das Lied Die Arbeiter von Wien.wav` and `File:Musical Notations Das Lied Die Arbeiter von Wien.png` (Commons user Adolf Stalin Guevara, 2023) — both **`{{self\|cc-by-sa-4.0}}`** → ❌ D15. de.wikipedia's article carries a LilyPond `<score>` block with a `\midi` section (trumpet, 120 BPM) — Wikipedia text is CC BY-SA 4.0 → ❌ D15 |
| Wikidata Q2663347 | no sheet-music (P3030) or audio property; only a YouTube ID |
| IMSLP (search "Pokrass") | no page |
| Mutopia | composer not catalogued |
| MuseScore.com | no score surfaced by search; site refuses automated access (403, §4.4 of MUSIC-RIGHTS) — a human could look |

Edition warning: almost every printed version of this song is a Soviet
arrangement (Alexandrov Ensemble and others), each with its own arranger's
term. A clean source would have to be the bare 1920 melody.

### 1.2 Ippolitov-Ivanov, *Procession of the Sardar* (*Caucasian Sketches* op. 10 no. 4) — scores only

No MIDI anywhere checked (Commons: no file; Mutopia: only his *Liturgy*
op. 37, SATB; IMSLP: "Synthesized/MIDI (0)", "Recordings (0)"). Kunst der
Fuge (403 to automated access) mixes licences per file — some CC BY-NC-SA,
most "personal use" — and could not be verified; a human could check
`https://www.kunstderfuge.com/ippolitov-ivanov.htm` for a file explicitly
marked CC BY-NC-SA (which D15 accepts).

PD score sources on IMSLP work page
`https://imslp.org/wiki/Caucasian_Sketches_Suite_No.1,_Op.10_(Ippolitov-Ivanov,_Mikhail)`
(per-file route `https://imslp.org/wiki/Special:ImagefromIndex/<#>`;
IMSLP's bot-check CAPTCHA blocks agents, MUSIC-RIGHTS §4.6.5):

| IMSLP # | What | Edition | Tag | Size | Edition rights |
|---|---|---|---|---|---|
| 231721 | full score, all 4 movements | Jurgenson, Moscow, ca. 1896 | Public Domain | 5.88 MB, 75 pp | composer d. 1935 (RU PD 2006), pub. 1896 → clean both |
| 651377 | **No. 4 only, piano solo** | arr. Matvey Nikolaevsky (1882-1942), Jurgenson pl. 36376, reprint Muzgiz 1928 | Public Domain | 3.46 MB, 9 pp | arranger d. 1942 → RU PD by 2017 even with +4; pub. pre-1931 → US PD. Clean |
| 645025 / 787498 | theatre-orchestra arrangement | Charles J. Roberts (1868-1957), Carl Fischer 1913 | Public Domain | 29.3 MB / 1.92 MB | US PD (1913); Roberts d. 1957 — fine under US law, irrelevant in RU (US publication). Prefer 231721 |
| 625239/40 | wind arrangement | Patrick Clements, 2018 | CC BY-NC-SA 4.0 | 0.33 MB | usable under D15 but a modern arrangement, not the original |

A score alone gives no playable file without sequencing, which D59 forbids.

### 1.3 Borodin, *In the Steppes of Central Asia* — clean CC0 recording, no MIDI

No MIDI: Commons has only Borodin's *Scherzo in A flat*; Mutopia does not
catalogue Borodin; IMSLP lists no Synthesized/MIDI file.

| Source | File | Performer | Licence, where stated | Instrumentation, length, size | Full / excerpt |
|---|---|---|---|---|---|
| **Commons** | `File:Alexander_Borodin_-_In_The_Steppes_Of_Central_Asia.ogg` → `https://upload.wikimedia.org/wikipedia/commons/b/be/Alexander_Borodin_-_In_The_Steppes_Of_Central_Asia.ogg` | Musopen Symphony Orchestra (Musopen 2012 Kickstarter sessions) | **`{{Cc-zero}}`** on the file page; source `musopen.org/music/681-...` and `archive.org/details/MusopenCollectionAsFlac` | full orchestra · **7:38** (458.24 s) · **4 731 200 B** OGG | **full work** |
| Commons (same recording, lossless) | `File:Borodin_-_In_the_Steppes_of_Central_Asia_(Musopen_Symphony).flac` | same | recording `{{PD-author\|Musopen}}`, composition `{{PD-old-auto-expired\|deathyear=1887}}` | 7:38 · 73 785 694 B FLAC | full |
| IMSLP #729867 (cross-check) | MP3 | "Czech National Symphony Orchestra", Palo Alto: Musopen, 2012 | "Creative Commons Zero 1.0" | 7:38, 10.19 MB | full |

Two independent pages (Commons, IMSLP) agree: Musopen 2012, 7:38, CC0/PD.
Composition free in both countries (MUSIC-RIGHTS §2.3); the phonogram is
dedicated by its owner; no lyrics. **No credit obligation.** Trade-off: it
ships as OGG at megabyte scale, not MIDI — the same size question already
recorded for *Marche slave* (MUSIC-RIGHTS §4.4.2, last paragraph).

Score sources (if ever needed): IMSLP #1043848 Rahter 1882 first edition
(PD, 15.32 MB) and **#1016329, a CC0 typeset by Richard Steele Bobo**
(0.48 MB, 27 pp); piano 4 hands Rahter #59904 (PD, 0.75 MB). Avoid the
Muzgiz/Muzyka reprints only for tidiness — the music is Borodin's either way.

### 1.4 Mussorgsky, *Night on Bald Mountain* — fuller than the Mutopia piano

Already held: `D_CND01`, Mutopia id 1892, Chernov's piano transcription,
typeset Robert Clausecker, **CC BY 3.0** (MUSIC-RIGHTS §4.4).
*Discrepancy to note:* IMSLP gives Chernov as **1865-1937**; MUSIC-RIGHTS
§4.4 says d. 1944. Either way he is PD in both countries.

| Source | URL | Type | Sequencer / performer | Licence, where stated | Instrumentation, length | Full / excerpt | Verdict |
|---|---|---|---|---|---|---|---|
| **OpenGameArt** node 92501, "Mussorgsky - Night on Bald Mountain" (TheOuterLinux, 2018-12-26) | `https://opengameart.org/node/92501` · archive `https://opengameart.org/sites/default/files/Mussorgsky%20-%20Night%20on%20a%20Bald%20Mountain.tar_0.gz` (15.1 MB) | `.tar.gz` holding `.mid`, LMMS `.mmpz`, PDF score, two OGG renders | uploader TheOuterLinux, "conversion/editing"; **who sequenced the MIDI is not stated** | licence field **CC0** on the node; "Public Domain (CC0) No Attribution Required" | multi-track synth/chiptune ("C64") arrangement; length not stated | claims the 1867 work; edition unstated (most likely the Rimsky-Korsakov 1886 version — NOT VERIFIED) | ⚠️ **conditional.** Same uploader's other nodes say he "converted from MIDI to PDF using MuseScore2", i.e. the MIDI pre-existed his work. If it came from an aggregator, his CC0 is void as to the sequencing (§1.2). Usable only if the MIDI's own meta events (copyright / text / track-name) name no other sequencer |
| **IMSLP #335184** (Synthesized/MIDI tab) | work page `https://imslp.org/wiki/Night_on_Bald_Mountain_(Mussorgsky,_Modest)`; file `.../Special:ImagefromIndex/335184` | **MP3**, not MIDI | Quinn Mason (electronics), "What I Make of It Publications", 2014 | "Creative Commons Attribution 4.0" on the IMSLP file entry | full orchestra (synthesised), **10:52**, 9.95 MB | **full**, Rimsky-Korsakov 1886 version | ✅ clean; **credit Quinn Mason**. CAPTCHA → a human downloads |
| IMSLP #77916 | same page | MP3 | Clint Jones, "The Synthonic Orchestra, Band & Choir" (Moody Bascum Osborne) | "Creative Commons Attribution 3.0" | 15:41, 21.55 MB, with synthetic choir | full, R-K 1886 | ✅ clean but long; credit Clint Jones |
| IMSLP #434007 | same page | PDF score | Gwyn Seymour, 6 cellos | CC BY 4.0 | 36 pp | arrangement | ensemble score only; would need sequencing (D59) |
| Commons `File:Modest_Mussorgsky_-_night_on_bald_mountain.ogg` | `https://upload.wikimedia.org/wikipedia/commons/c/ca/Modest_Mussorgsky_-_night_on_bald_mountain.ogg` | OGG, 12:13, 12.9 MB | "Performer might be Skidmore College Orchestra" | Commons: `{{PD-author\|Musopen}}`; **IMSLP #77970, the same Skidmore/Musopen recording (12:13), says CC BY-SA 3.0** | orchestra | full | ❌ **conflicting licences** — do not use |
| IMSLP #970059/970060 | — | PDF + **MXL** (1867 original, ed. Kirkor) | David J. Miller | CC BY-SA 4.0 | — | — | ❌ D15; and Kirkor's 1967 edition (ed. d. 1980) is itself protected in RU |
| IMSLP #542298 | — | PDF | David Hume typeset of Kirkor | CC BY-NC-SA 4.0 | — | — | ⚠️ licence OK, but built on Kirkor's protected 1967 edition |

PD score of the 1886 version: IMSLP #139196, Bessel 1886, PD, 9.26 MB.

### 1.5 «Смело, товарищи, в ногу» (Radin) — melody source only

| Source | Result |
|---|---|
| Commons `File:BruederzurSonne.mid` (German version *Brüder, zur Sonne, zur Freiheit*, same melody) — `https://upload.wikimedia.org/wikipedia/commons/f/f4/BruederzurSonne.mid` | Boris Fernbacher3, 2006, NoteWorthy Composer, 2 tracks (trumpet + piano), **16 s**, 1 095 B. Licence **GFDL** with the relicensing-migration template → ❌ D15 (copyleft). Its OGG render `BruederzurSonne.ogg` is CC BY-SA 3.0 → ❌ |
| de.wikipedia, *Brüder, zur Sonne, zur Freiheit* | LilyPond `<score sound="1">` — CC BY-SA 4.0 → ❌ |
| **Commons `File:Песни каторги и ссылки (1930).pdf`** — `https://upload.wikimedia.org/wikipedia/commons/e/ea/%D0%9F%D0%B5%D1%81%D0%BD%D0%B8_%D0%BA%D0%B0%D1%82%D0%BE%D1%80%D0%B3%D0%B8_%D0%B8_%D1%81%D1%81%D1%8B%D0%BB%D0%BA%D0%B8_%281930%29.pdf` | Moscow: Изд-во политкаторжан, 1930, 124 pp with notation, `{{PD-scan\|PD-Russia}}{{PD-scan\|PD-1996}}`. Its text layer lists **no. 26 «Смело, товарищи, в ногу», p. 68, «Обр. В. Белый»**. **72 112 940 B — over the D44 20 MB limit**; page renders via `upload.wikimedia.org/.../thumb/` (the §4.6.4 method) would avoid it |
| MuseScore.com | nothing surfaced by search; 403 to agents |

Edition flag: «Обр. В. Белый» is very probably **Viktor Bely (1904-1983)**
(identification NOT VERIFIED) → his **harmonisation is protected in Russia
until at least 2054**; published 1930 it is US PD. Commons' `PD-Russia` tag
does not cover a named arranger who died in 1983. Only Radin's melody (the
top line) could be taken — the D44/D54 "top voice only" logic — and that is
sequencing, which D59 forbids. (de.wikipedia: Radin adapted a student-song
tune on Nikitin's 1857 text; that tune is 19th-century and PD either way.)

## 2. Recommendation — what the PM downloads first

1. **Borodin, *In the Steppes of Central Asia*, Commons CC0 OGG** —
   `https://upload.wikimedia.org/wikipedia/commons/b/be/Alexander_Borodin_-_In_The_Steppes_Of_Central_Asia.ogg`
   (4 731 200 B, 7:38, Musopen Symphony Orchestra, `{{Cc-zero}}`).
   The only candidate that is complete, orchestral, licence-clean with no
   obligation, and agent-downloadable without a CAPTCHA. It is audio, not
   MIDI: the CEO hears the real orchestra, and the PK3 grows by ~4.7 MB
   (less if re-encoded at a lower Vorbis quality).
2. **Mussorgsky, *Night on Bald Mountain*, IMSLP #335184 (Quinn Mason,
   CC BY 4.0, MP3, 10:52, 9.95 MB)** — a human must fetch it (IMSLP
   CAPTCHA). Clean, full orchestral sound; adds one credit line
   ("synthesised performance by Quinn Mason, CC BY 4.0, via IMSLP").
3. *(Optional, for inspection only)* **OpenGameArt node 92501 archive**
   (15.1 MB `.tar.gz`, CC0) — the only fuller Bald Mountain MIDI found.
   Download into its own empty directory as untrusted data and read the
   `.mid`'s meta events with `tools/audio/midi_inspect.py` **before** any
   audition: if they name a sequencer or site other than TheOuterLinux,
   reject it at the licence gate.

Not recommended to download now: *Sardar* and *Smelo* (score sources only,
and a score is useless under D59 unless the CEO waives it for one piece);
*Krasnaya armiya* (no clean source exists in reach).

**Decision this hands the CEO / PM:** whether MAP01 may use **audio (OGG)**
instead of MIDI. If yes, Borodin is ready today. If MIDI is mandatory, none
of the five has a fully clean full-ensemble MIDI, and the only path to
*Sardar* or *Smelo* is a D59 waiver to sequence one melody from the PD
scores above.

## 3. Sources read (2026-10-20)

- Commons API / raw wikitext for every Commons file named above.
- IMSLP work pages: *In the Steppes of Central Asia* (Borodin);
  *Caucasian Sketches Suite No.1, Op.10*; *Night on Bald Mountain*
  (Mussorgsky). IMSLP API search for Pokrass / Radin: no pages.
- Mutopia: `browse.html`; `make-table.cgi?Composer=MussorgskyM`;
  `make-table.cgi?Composer=Ippolitov-IvanovM` (only op. 37 no. 1, SATB, PD).
- OpenGameArt nodes 92501 and 91294 (TheOuterLinux).
- de.wikipedia raw: *Brüder, zur Sonne, zur Freiheit*; *Weiße Armee,
  schwarzer Baron*; *Die Arbeiter von Wien*. Wikidata Q2663347.
- Kunst der Fuge and MuseScore.com: HTTP 403 to automated access; not
  verified.
