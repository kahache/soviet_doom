# Music rights — what Soviet Doom can legally use as a soundtrack

Living document. Owner: sound-designer. Russian mirror: `docs/ru/sound/MUSIC-RIGHTS.md` (D7).
Created: 2026-10-12 (F2, research brought forward).
Revised 2026-10-13: the CEO asked for **downloaded** MIDIs rather than generated
ones, which exposes a right the first version treated as a footnote — the
**sequencing** (§1.2). Twelve candidate files have now been licence-audited and
fetched to `work/audio/candidates/`; the audit is §4.4.
Revised again 2026-10-13, **D43** (CEO: *"Acepto las recomendaciones de
música"* ("I accept the music recommendations")): the Engelbach attribution is accepted and **`D_SDINTL` and
`D_SDM01` are installed in `assets/music/`**; the credits are §4.5; the
candidates are **tracked in git** with their SHA-256 (§4.4) and three were
discarded; works restored in the United States are excluded (§7.2) and the
anthem slot goes to Glinka (§7.1).
Revised 2026-10-13 by `mod-engineer` (D43, the radio): the two CC0 radio
pieces are installed unedited as **`D_SDRAD1`** and **`D_SDRAD2`** (§4.4,
§4.5), for the radio actor of `docs/engine/MOD-SPEC.md` §6.7.
Revised 2026-10-14, **D44** (CEO: *"sí"* ("yes") to one public-domain score per
self-sequenced piece): two scores downloaded and recorded in **§4.6**, for
«Вы жертвою пали» (`D_SDFUNR`) and «Амурские волны» (`D_SDAMUR`); **no
reliable public-domain score of Glinka's *Patriotic Song* was found, so
nothing was downloaded for `D_SDGLNK`** (§4.6.3).
Revised 2026-10-14, **D54** (CEO: *"busca alternativa, cambiamos pieza
musical y ya"*): Glinka is dropped from the anthem slot. The replacement is
Mussorgsky's **«Богатырские ворота»** (*The Great Gate of Kiev*), sequenced
by us from one downloaded public-domain score, the 1886 Bessel first edition
(**§4.6.4**, draft `D_SDGATE`); the alternatives weighed and why the others
fell are **§4.6.5**.
Companion to `docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md`, which
established the Russian and US legal frame for visual art. **The same frame applies
to music**, with two extra layers: recordings, and sequencings.

> This is research, not legal advice. Every date below carries its source.
> Anything I could not confirm against a concrete source is marked **NOT VERIFIED**.

---

## 1. The rule that governs everything: three separate rights

A song is not one right, it is three — four once a MIDI is involved (§1.2).
They expire on different dates and belong to different people.
**A work can be free and every recording of it still protected.**

| # | Right | Depends on | Who owns it |
|---|---|---|---|
| 1 | **Composition** (the score, the melody) | death of the composer | composer / heirs |
| 2 | **Lyrics** (the text) | death of the lyricist — usually a *different* person who often died *much* later | lyricist / heirs |
| 3 | **Phonogram** (one concrete recording) | date of fixation or publication, own term | the label (Melodiya) or the orchestra — **not** the composer |
| 4 | **Sequencing / typeset** (one concrete MIDI, LilyPond or MuseScore file) | the licence its author attached to it, nothing else | the person who sequenced it — see §1.2 |

When 1 and 2 are free but 3 is not, the clean route is to **perform or sequence the
work ourselves** (MIDI, tracker, virtual instruments): free composition + our own
recording, which we then license under the project's own terms.

### 1.1 Terms, verified

**Russia** (Civil Code part IV):
- Composition and lyrics: **life of the author + 70 years**, running from 1 January
  of the year following death (art. 1281); **+4 years** for authors who worked during
  or took part in the Great Patriotic War (1941-45). Died in year *Y* → public domain
  on **1 Jan (Y+71)**, or **1 Jan (Y+75)** with the war extension.
  Practical shortcut valid in 2026: **public domain if the author died in 1951 or
  earlier**.
- Phonograms: **50 years** from 1 January of the year after recording or publication
  (art. 1327). A 1944 recording is free in Russia; a **1977 Melodiya recording is not
  free in Russia until 1 Jan 2028**.
- **State symbols are excluded from copyright altogether** (art. 1259(6)). Wikimedia
  Commons applies `{{PD-RU-exempt}}` to the USSR anthem on exactly this basis.

**United States** (the jurisdiction that actually matters for a mod hosted on ModDB
or GitHub):
- A Soviet work **published after 31 Dec 1930** that was still protected in Russia on
  **1 Jan 1996** had its US copyright restored by the URAA: **95 years from
  publication**. Published *before* 1931 → public domain in the US today.
- Pre-1972 sound recordings (Music Modernization Act 2018, Classics Protection and
  Access Act): published **1923-1946 → 100 years**; **1947-1956 → 110 years**;
  1957 to 14 Feb 1972 → through 15 Feb 2067. **A 1944 Soviet recording is protected in
  the US until 2044.** Post-1972 recordings: restored by URAA, 95 years.

**Net effect, and the single most important sentence in this document:**
most Soviet patriotic music is **free in Russia and still protected in the United
States**, and **essentially every genuine Soviet recording is off limits in the US**.

### 1.2 The trap that catches everyone: **a MIDI file is a fourth right**

Added 2026-10-13, after the CEO asked for downloaded MIDIs instead of
generated ones. This is the single thing to remember from this section.

**A MIDI file is not a score and it is not a recording. It is a *sequencing*:
somebody's transcription of a piece into a stream of timed events, with their
choices of tempo, velocity, channel layout and General MIDI instruments.
That work is an original derivative work. It has its own author and its own
licence, and that licence is independent of the composition's.**

So:

> *Degeyter died in 1932, therefore any MIDI of the Internationale is free.*

is **false**, and it is the most natural mistake to make. The composition
being public domain means **anyone is allowed to make and release a free
sequencing** — it does not mean that the particular file you found is one.
A MIDI of a public-domain work can be:

| | Composition | Sequencing | Can we ship it? |
|---|---|---|---|
| PD score, sequencer released it CC0 / PD / CC BY | free | free | **yes** |
| PD score, sequencer released it CC BY-SA | free | copyleft | **no** — §1.3 |
| PD score, sequencer released it GFDL | free | copyleft | **no** — §1.3 |
| PD score, posted to a MIDI site with no licence at all | free | **unknown, assume reserved** | **no** |
| Protected score, sequencer released it CC0 | **not free** | free | **no** — the CC0 is void as to the composition |

Three consequences for how we work:

1. **"No licence stated" is not "public domain".** The large free-MIDI
   aggregators — BitMidi, MIDIWorld, Midis101, hamienet, MidiShow, rusmidi,
   most of archive.org's MIDI uploads — carry no per-file licence and usually
   no named sequencer. They are unusable for us no matter how free the
   underlying tune is. This disqualifies essentially the whole Soviet-MIDI
   corpus that exists online, which is hosted on exactly those sites.
2. **The licence must be attached to the file, by the person who sequenced
   it, and be verifiable.** A site-wide "all our files are free" banner is not
   enough; the per-file statement is. Wikimedia Commons, IMSLP and Mutopia all
   do it per file, which is why they are our only sources.
3. **The last column of the table above is why sequencing it ourselves is
   always available.** A free composition can always be legally re-sequenced.
   If no free MIDI of a free work exists, that is a *labour* problem, not a
   rights problem.

A fourth right, the **phonogram**, still applies on top of all this whenever
the file is audio (OGG/MP3/FLAC) rather than MIDI — see §3.3.

### 1.3 One licence trap specific to our project (D15)

Our assets ship under **CC BY-NC-SA 4.0**. That is *incompatible* with **CC BY-SA**
material: ShareAlike requires redistribution under the same licence, and adding the
NonCommercial restriction is an added restriction ShareAlike forbids. Therefore:

- **Usable**: Public Domain, CC0, CC BY, CC BY-NC, CC BY-NC-SA.
- **NOT usable under D15**: CC BY-SA, CC BY-SA-NC-ND variants with ND, anything GPL-ish
  applied to audio.

This rules out a sizeable share of Musopen and IMSLP user recordings/typesets, which
are CC BY-SA. Check the licence per file, not per site.

---

## 2. Master table

Legend — **RU** = status in Russia, **US** = status in the United States.
✅ free · ⚠️ conditional / disputed · ❌ protected.
"Route" = how we would legally get this into the PK3.

### 2.1 The two key cases: the anthems

| Work | Composer | Lyricist | Composed / published | Composition | Lyrics | Typical recordings | Route |
|---|---|---|---|---|---|---|---|
| **Гимн Советского Союза** · *Gimn Sovetskogo Soyuza* · State Anthem of the USSR | Александр Васильевич Александров / Alexander Vasilyevich **Alexandrov** (13 Apr 1883 – 8 Jul 1946) | 1944: Сергей Михалков / Sergey **Mikhalkov** (1913-2009) + Габриэль Эль-Регистан / Gabriel **El-Registan** (1899-1945). **1977: Mikhalkov alone** | melody 1938 (as the Bolshevik Party Hymn), pub. 1939; anthem adopted **1 Jan 1944**; lyrics revised **1977** | **RU ✅** — d. 1946, war work → +74 → free 1 Jan 2021; *and separately* exempt as a state symbol (art. 1259(6)). **US ⚠️/❌** — published 1944, URAA-restored → protected to **1 Jan 2040** unless the state-symbol exemption defeats restoration (Commons' implicit position; **NOT VERIFIED** as US law) | **❌ BOTH** — Mikhalkov d. **2009** → RU free **1 Jan 2080** (2084 with the war extension, he was a front correspondent). The 1977 text is the *most* protected part of the whole anthem | **RU ⚠️ / US ❌** — the 1977 USSR Ministry of Defence Orchestra recording is free in Russia only from 1 Jan 2028 (art. 1327, 50 yr); in the US a 1944 recording runs to 2044 and a 1977 one to 2072 | **Instrumental only, sequenced by us.** Never the sung 1977 version. See §3.1 |
| **Интернационал** · *Internatsional* · The Internationale | Pierre **De Geyter** (1848-1932) | FR: Eugène **Pottier** (1816-1887), written 1871. RU translation: Аркадий **Коц** / Arkady **Kots** (1872-1943), 1902 | composed & published **1888** (Lille, *Le Socialiste*) | **RU ✅** (rule of the shorter term, art. 1256(4): the French term expired **Oct 2017**). **US ✅** — published 1888, long before 1931 | **✅ both** — Pottier d. 1887; Kots d. 1943 + war → RU free 1 Jan 2018; RU text published 1902 → US free | **⚠️ per recording** — the composition is free, but every modern Soviet/Russian recording still carries its own phonogram right. Use a PD/CC0 recording or our own | **✅ CLEANEST CASE IN THE WHOLE LIST.** PD score on IMSLP, free arrangements, sequence ourselves. Soviet anthem until 1944 → perfect for a 1977 "old guard" cue |

### 2.2 Marches and patriotic songs

| Work | Composer (dates) | Lyricist (dates) | Pub. | Composition RU / US | Lyrics RU / US | Verdict |
|---|---|---|---|---|---|---|
| **Священная война** · *Svyashchennaya voyna* · The Sacred War | Alexandrov (1883-1946) | Василий Лебедев-Кумач / Vasily **Lebedev-Kumach** (1898-1949) | 1941 | **RU ✅** 2021 / **US ❌** to 1 Jan **2037** | **RU ✅** d.1949 + war → 1 Jan 2024 / **US ❌** 2037 | ⚠️ **Free in Russia, blocked in the US.** Highest dramatic value of any song here. Decision needed from the CEO (§4) |
| **Гимн партии большевиков** · *Gimn partii bolshevikov* · Hymn of the Bolshevik Party | Alexandrov | Lebedev-Kumach | 1939 | **RU ✅** / **US ❌** to 1 Jan **2035** | **RU ✅** / **US ❌** 2035 | ⚠️ Same melody as the anthem, two years earlier. Useful only as evidence that the melody's US clock started in 1939, not 1944 |
| **Катюша** · *Katyusha* | Матвей Блантер / Matvei **Blanter** (10 Feb 1903 – 27 Sep 1990) | Михаил Исаковский / Mikhail **Isakovsky** (1900-1973) | 1938 | **RU ❌** to 1 Jan **2065** / **US ❌** 2034 | **RU ❌** to 1 Jan **2048** | ❌ **DISCARD.** Protected everywhere for decades |
| **Полюшко-поле** · *Polyushko-pole* · Meadowlands | Лев Книппер / Lev **Knipper** (3 Dec 1898 – 30 Jul 1974) | Виктор Гусев / Viktor **Gusev** (1909-1944) | 1933-34 (Symphony No. 4) | **RU ❌** to 1 Jan **2049** / **US ❌** 2030 | RU ✅ 2019 | ❌ **DISCARD.** Commonly mistaken for a folk song — it is not |
| **Смуглянка** · *Smuglyanka* | Анатолий Новиков / Anatoly **Novikov** (1896-1984) | Яков Шведов / Yakov **Shvedov** (1905-1984) | 1940 | **RU ❌** to 1 Jan **2059** | **RU ❌** 2059 | ❌ **DISCARD** |
| **Прощание славянки** · *Proshchaniye slavyanki* · Farewell of Slavianka | Василий Агапкин / Vasily **Agapkin** (3 Feb 1884 – 29 Oct 1964) | instrumental march; all sung texts are later and separately protected | **1912**, Tambov | **RU ❌** to 1 Jan **2039** (d. 1964 + war: he conducted the band at the 7 Nov 1941 Red Square parade) / **US ✅** published 1912 | n/a — use instrumental | ⚠️ **Split jurisdiction: free in the US, protected in Russia.** The inverse of every other entry. Commons' own tag on it only claims "life+60 or fewer" countries, which does **not** include Russia |
| **Москва майская** · *Moskva mayskaya* · Moscow in May | Дмитрий Покрасс / Dmitry **Pokrass** (1899-1978) + Даниил Покрасс / Daniil **Pokrass** (1905-1954) | Lebedev-Kumach | 1937 | **RU ❌** to 1 Jan **2053** (Dmitry) | RU ✅ 2024 | ❌ **DISCARD** |
| **Марш энтузиастов** · *Marsh entuziastov* · March of the Enthusiasts | Исаак Дунаевский / Isaak **Dunayevsky** (1900 – 25 Jul 1955) | Анатолий Д'Актиль / Anatoli **d'Aktil** (1890-1942) | 1940 (film *Светлый путь*) | **RU ⚠️** — without the war extension he became free **1 Jan 2026** (i.e. this year); with it, **1 Jan 2030**. He directed the Railway Workers' song-and-dance ensemble at the front, so +4 almost certainly applies. **NOT VERIFIED** which reading prevails / **US ❌** 2036 | RU ✅ 2017 | ⚠️ **Borderline, treat as protected until 2030.** Same reasoning covers *Песня о Родине* ("Широка страна моя родная", 1936) |
| **Авиамарш / Всё выше** · *Aviamarsh* · The Aviators' March | Юлий Хайт / Yuli **Khait** (1897-1966) | Павел Герман / Pavel **German** (1894-1952) | **1923** | **RU ❌** to 1 Jan 2037-2041 / **US ✅** pub. 1923 | **RU ❌** ~2023-2027 (**NOT VERIFIED**) / US ✅ | ⚠️ Free in the US, protected in Russia. Same shape as *Slavianka* |
| **Красная армия всех сильней** · *Krasnaya armiya vsekh silney* · White Army, Black Baron | Самуил Покрасс / Samuil **Pokrass** (1897-1939, emigrated 1924, d. USA) | Павел Григорьев / Pavel **Grigoriev** (1895-1961) | **1920** | **RU ✅** d. 1939 → 1 Jan 2010 / **US ✅** pub. 1920 | **RU ❌** to 1 Jan **2032** | ✅ **USABLE INSTRUMENTALLY** in both countries. Lyrics must not appear |
| **По долинам и по взгорьям** · *Po dolinam i po vzgoryam* · Through Valleys and Over Hills | melody credited to Илья Атуров / Ilya **Aturov** (dates **NOT VERIFIED**, attribution disputed); arranged by Alexandrov 1929 | Пётр Парфёнов / Pyotr **Parfyonov** (1894-1937) and/or Сергей Алымов / Sergei **Alymov** (1892-1948) | 1929 (Alexandrov Ensemble) | **RU ⚠️** Alexandrov arrangement free 2021; underlying melody unresolved / **US ✅** pub. 1929 | **RU ✅** Parfyonov 2008, Alymov + war 2023 / **US ✅** | ⚠️ Probably clean, but **Aturov is an unresolved hole**. Do not commit without closing it |
| **Смело, товарищи, в ногу** · *Smelo, tovarishchi, v nogu* · Boldly, Comrades, in Step | Леонид Радин / Leonid **Radin** (1860-1900), words and music | Radin | written 1896-97, pub. 1901-02 | **RU ✅** d. 1900 / **US ✅** pub. 1902 | **✅ both** | ✅ **FULLY FREE, WORDS AND MUSIC, BOTH COUNTRIES.** The best genuinely revolutionary song available to us |
| **Вы жертвою пали** · *Vy zhertvoyu pali* · You Fell Victim (revolutionary funeral march) | melody: Александр Варламов / Alexander **Varlamov** (1801-1848), 1830s, first the tune of «Не бил барабан перед смутным полком» (ru.wikipedia, read 2026-10-13); en.wikipedia credits instead an *arrangement* to Nikolay Ikonnikov, 1878, and names no composer — **the two disagree, NOT VERIFIED which is right** | Антон Амосов (pseud. Архангельский) / Anton **Amosov** (1854-1915), 1870s | 1870s-1878 | **RU ✅** / **US ✅** — every candidate author died before 1916 and the song predates 1900 | ✅ both | ✅ **FREE.** The Soviet state funeral music — ideal for a defeat/aftermath cue |
| **Варшавянка** · *Varshavyanka* · Whirlwinds of Danger | Józef **Pławiński** (1853-1880) / traditional | RU text: Глеб Кржижановский / Gleb **Krzhizhanovsky** (1872-1959) | melody 1879-83; RU text 1897 | **RU ✅** / **US ✅** | **RU ❌** to 1 Jan **2030-2034** | ⚠️ **Melody free, Russian words not.** Instrumental only |
| **Амурские волны** · *Amurskiye volny* · Amur Waves (waltz) | Макс Кюсс / Max **Kyuss** (20 Mar 1874 – 1942, killed in occupied Odessa) | instrumental (later texts protected) | **1909**, Vladivostok | **RU ✅** d. 1942 → free 1 Jan 2017 at the latest / **US ✅** pub. 1909 | n/a | ✅ **FULLY FREE, BOTH COUNTRIES.** Perfect diegetic radio/waltz ambience |
| **На сопках Маньчжурии** · *Na sopkakh Manchzhurii* · On the Hills of Manchuria (waltz) | Илья Шатров / Ilya **Shatrov** (1879 – 2 May 1952) | instrumental in the usable version | **1906-07** | **RU ⚠️** — died four months *after* the 1 Jan 1952 cut-off. Without war extension free since 1 Jan 2023; with it, 1 Jan **2027**. His WWII service is reported but **NOT VERIFIED** here / **US ✅** pub. 1907 | n/a | ⚠️ Free in the US; in Russia one year away under the strict reading. Low cost to simply wait |
| **Эй, ухнем** · *Ey, ukhnem* · Song of the Volga Boatmen | folk; concert arrangements by Balakirev (1837-1910), Glazunov (1865-1936) | folk | pub. 1866 | **✅ both** | ✅ both | ✅ **FREE.** Heavy, slow, Russian — good for an oppressive industrial area |

### 2.3 Russian classics — the safe ground

All composers below died long before any cut-off and their works were published well
before 1931. **Free in Russia and in the United States, composition and (where
applicable) text.** The *recordings* are a separate matter — see §3.3.

| Composer | Dates | RU | US | Pieces that fit Soviet Doom |
|---|---|---|---|---|
| **Михаил Глинка** / Mikhail **Glinka** | 1804-1857 | ✅ | ✅ | **Патриотическая песня / "Patriotic Song"** — the national anthem of Russia 1990-2000; the composition is free, but **no reliable public-domain score of the 1833 melody exists in reach, and D54 dropped it** (§4.6.3). «Славься» from *A Life for the Tsar* (1836), the closest substitute, is weighed in §4.6.5. *Ruslan and Lyudmila* overture (frantic, excellent for a fight) |
| **Пётр Чайковский** / Pyotr **Tchaikovsky** | 1840-1893 | ✅ | ✅ | **Marche slave op. 31 (1876)** — the single best candidate for a main theme. Symphony No. 4 finale; *1812 Overture* (caution: it quotes the Tsarist anthem *God Save the Tsar*, which is lore-wrong for 1977) |
| **Александр Бородин** / Alexander **Borodin** | 1833-1887 | ✅ | ✅ | *Polovtsian Dances*, *In the Steppes of Central Asia*, *Prince Igor* overture. Completions by Rimsky-Korsakov (d. 1908) and Glazunov (d. 1936, RU free 2007, US pub. 1888) are also free |
| **Модест Мусоргский** / Modest **Mussorgsky** | 1839-1881 | ✅ | ✅ | **Night on Bald Mountain** (Rimsky-Korsakov version, 1886) — the obvious demon/alien cue. *Pictures at an Exhibition*: "Gnomus", "Catacombae", "The Hut on Fowl's Legs", **"The Great Gate of Kiev" — the anthem slot since D54 (§4.6.4)**. **Use the piano original**; Ravel's orchestration has its own term (**NOT VERIFIED** for Russia) |
| **Николай Римский-Корсаков** / Nikolai **Rimsky-Korsakov** | 1844-1908 | ✅ | ✅ | *Russian Easter Festival Overture*, *Scheherazade*, *Flight of the Bumblebee* |
| **Александр Скрябин** / Alexander **Scriabin** | 1872-1915 | ✅ | ✅ | *Prometheus: Poem of Fire*, Piano Sonata No. 9 "Black Mass", *Poem of Ecstasy*. Atonal, mystical, genuinely unsettling — the best free match for the alien side of the game |
| **Михаил Ипполитов-Иванов** | 1859-1935 | ✅ (d. 1935 → free 2006) | ✅ *Caucasian Sketches* pub. 1894 | "Procession of the Sardar" — a short, brassy, menacing march |

### 2.4 The two border cases the CEO asked about — both fail

| Composer | Dates | Calculation | Verdict |
|---|---|---|---|
| **Сергей Прокофьев** / Sergei **Prokofiev** | 23 Apr 1891 – 5 Mar 1953 | RU: d. 1953, worked throughout the war (*War and Peace*, Symphony No. 5) → 1953+70+4 → free **1 Jan 2028**. US: everything published 1931 or later was URAA-restored (*Lt. Kijé* 1934 → 2030; *Romeo and Juliet* 1936 → 2032; *Alexander Nevsky* 1939 → 2035) | ❌ **NOT FREE.** Pre-1931 publications (op. 11 *Toccata*, *Visions fugitives*, *Scythian Suite*, *Classical Symphony*) are free **in the US only**, still protected in Russia until 2028. No piece is free in both. **Discard for v1**; revisit in 2028 |
| **Дмитрий Шостакович** / Dmitri **Shostakovich** | 25 Sep 1906 – 9 Aug 1975 | RU: d. 1975 + war (Symphony No. 7 "Leningrad") → free **1 Jan 2050**. US: URAA-restored across the board | ❌ **NOT FREE ANYWHERE, AND ACTIVELY ENFORCED.** DSCH/Boosey & Hawkes police this repertoire; there is a US Supreme-Court-era precedent bearing his name (*Shostakovich v. Twentieth Century-Fox*, 1948). **Hard discard.** This is the biggest trap in the genre, because "Leningrad Symphony over a burning cosmodrome" is exactly what the mod wants |

---

## 3. Detailed notes on the two cases the CEO named

### 3.1 The USSR anthem — what we can and cannot do

Three findings, kept apart on purpose:

1. **The melody is free in Russia.** Two independent reasons: Alexandrov died in 1946
   and the war extension put his works in the public domain on 1 Jan 2021; and the
   anthem is a **state symbol**, excluded from copyright by art. 1259(6). Wikimedia
   Commons hosts the 1977 instrumental recording by the USSR Ministry of Defence
   Orchestra under `{{PD-RU-exempt}}` for exactly this reason.
2. **The melody's US status is not settled.** Published 1944, it would normally be
   URAA-restored until 1 Jan 2040. The counter-argument is that URAA restores works
   that fell out of protection "through expiration of term" — and a state symbol never
   had a term. That argument is what Commons relies on in practice. **I cannot verify
   it as US law and I am not qualified to; treat the US as a real risk.**
3. **The 1977 lyrics are the most protected element in this entire document.**
   Mikhalkov died in 2009. Free in Russia in **2080** at the earliest, 2084 with the
   war extension. The 1944 lyrics are no better (Mikhalkov again). Even the 2000
   Russian text is Mikhalkov.

**Recommended route:** an **instrumental** arrangement of the Alexandrov melody,
**sequenced by us** (MIDI or tracker), never a Soviet recording, never sung. That
kills the phonogram problem and the lyrics problem outright and leaves only finding
(2) open. If the CEO wants zero residual risk, Glinka's *Patriotic Song* (§2.3) is a
real national anthem of Russia that is free beyond any argument, and would carry the
same weight in a title screen.

### 3.2 The Internationale — take it

This is the cleanest major work available to us and it is *more* period-correct than
people assume: it was the Soviet anthem until 1944 and remained the anthem of the
CPSU throughout 1977, played at every party congress. Composition free, French text
free, Kots's Russian text free, in both jurisdictions, with a public-domain score
already typeset on IMSLP and free arrangements for small ensembles. **Sequence our
own version**; a brass-and-choir arrangement at funeral tempo for the intro and a
driving march version for the finale costs us nothing legally.

### 3.3 The recordings warning, stated plainly

**A free composition does not give us a free recording.** Concretely:

- Melodiya / Alexandrov Ensemble / USSR State Radio recordings from the 1950s-80s:
  protected in the US until the 2040s-2070s; in Russia until 50 years after
  publication (a 1977 recording → 2028).
- The single Commons file for the 1977 anthem instrumental is tagged free **under
  Russian law only**. That tag says nothing about the US.
- Even a `PD-USGov` recording (US Navy Band / US Coast Guard Band play several of
  these marches, and those performances genuinely are public domain in the US) frees
  only the *performance*. If the underlying composition is URAA-restored, the
  recording is still unusable. This catches *The Sacred War* and the anthem; it does
  **not** catch *Farewell of Slavianka*, whose composition is itself US public domain.

---

## 4. Sources of genuinely free material

| Source | What it gives | Licence reality | Use |
|---|---|---|---|
| **IMSLP** (imslp.org) | scores, parts, some recordings | Per-file, and **per-country**: tags read "Public Domain in the USA", "Public Domain in Canada (where IMSLP is hosted)", "non-PD EU". A green US tag does **not** mean free in Russia. Modern typesets are often **CC BY-SA → unusable under D15** | Primary source of scores to sequence from. The De Geyter *L'Internationale* complete score is tagged Public Domain (pub. *Le Socialiste*, Paris) |
| **Musopen** (musopen.org) | ~2,400 PD compositions, ~1,800 recordings | Three buckets: **Public Domain**, **CC0** (both fine for us) and **CC BY-SA** (**not usable under D15**). Download needs a free account, 5 files/day | Best route to ready-made orchestral recordings of Tchaikovsky, Borodin, Mussorgsky, Rimsky-Korsakov |
| **Wikimedia Commons** | audio, anthems, scans | Explicit tag per file, but the tag often covers only the **country of origin**. `{{PD-RU-exempt}}` = Russian state symbol; `{{PD-USGov}}` = US federal performance | Good for cross-checking status; weak as an audio source for us |
| **Mutopia Project** (mutopiaproject.org) | LilyPond scores + generated **MIDI** | PD / CC BY / CC BY-SA — declared per piece, and genuinely mixed: of the 24 Russian-composer pieces surveyed on 2026-10-13, 11 are PD, 1 is CC BY and **12 are CC BY-SA**, i.e. unusable | Fastest path from free score to a MIDI we can re-orchestrate. See §4.2 for what those MIDIs actually contain |
| **Wikimedia Commons, MIDI files** | ~1 080 `.mid` files, licence tag per file | Per file, and really varied: CC0, `{{Attribution}}`, CC BY-SA, **GFDL** | The only place with *Soviet-themed* MIDI under a verifiable licence. Three files of the Internationale exist there and they carry three different licences — §4.3 |
| **archive.org** | everything and anything | **No guarantee.** Most Soviet music there is unlicensed rips of Melodiya. Checked on 2026-10-13: the "USSR Anthem (MIDI)" item (`archive.org/details/ussr-1`) declares **no licence at all** | Treat as unsourced unless proven otherwise |
| **MuseScore.com** | user-uploaded scores, MIDI export | Uploader-declared, including CC0 — but the declaration is made by a user who usually did not verify the underlying rights, and the site **refused automated access (HTTP 403) when we tried to verify a licence on 2026-10-13** | **Not usable as a source** while we cannot read the licence programmatically. A human can check a specific score if the CEO wants one |
| **Free-MIDI aggregators** — BitMidi, MIDIWorld, Midis101, hamienet, MidiShow, rusmidi.com, geocities mirrors | large Soviet/Russian collections, exactly the material we want | **None. No per-file licence, usually no named sequencer.** §1.2 | **Never.** This is where the Soviet MIDI corpus lives and it is all unusable |

### 4.1 What we take as-is vs what we sequence ourselves

**Take as-is (PD or CC0 recordings):** the Russian classics of §2.3 — Tchaikovsky's
*Marche slave*, Mussorgsky's *Night on Bald Mountain*, Borodin, Rimsky-Korsakov,
Scriabin. These are standard repertoire with real CC0 orchestral recordings on
Musopen. Convert to **OGG Vorbis** for the PK3.

**Sequence ourselves (free composition, no free recording):** the Internationale, the
Alexandrov anthem melody (instrumental), *Smelo, tovarishchi, v nogu*, *Vy zhertvoyu
pali*, *Amurskiye volny*, *Krasnaya armiya vsekh silney* (instrumental), *Ey, ukhnem*.
Deliver as **MIDI** or **tracker modules (XM/IT)** — tens of kilobytes instead of
megabytes, and the recording right is then ours to license under CC BY-NC-SA 4.0.

**Compose original in the period style:** style is not copyrightable (the same finding
the art research reached). The actual soundtrack need of a Doom map is ambience and
combat loops, not marches. The Soviet reference here is **Eduard Artemyev**
(1937-2022, *Solaris*, *Stalker*) and the **ANS photoelectronic synthesiser** — his
music is protected, but nothing stops us writing original drones and pulses in that
idiom. **This is where most of our soundtrack should come from.** The historical
pieces work best as diegetic radio, title screen and intermission.

---

### 4.2 What a Mutopia MIDI actually is

Measured, not assumed, on 2026-10-13 with `tools/audio/midi_inspect.py` over
the eight Russian-composer MIDIs we downloaded: **every one of them contains
zero General MIDI program changes.** They are LilyPond's audio preview of an
engraved score — correct notes, correct tempo, correct dynamics, and every
channel left on GM program 0, acoustic grand piano. Several are piano
transcriptions of orchestral works to begin with (Chernov's *Night on Bald
Mountain*).

That is not a defect in Mutopia — a score preview is what it is for — but it
means **a Mutopia MIDI is a free score we happen to receive in MIDI form, not
a finished piece of game music.** Using one means doing the orchestration
ourselves: assigning GM programs per staff, balancing channel volumes, and
usually cutting it to length. The licences allow exactly that (PD outright,
CC BY 3.0 with attribution), and the result is our arrangement, which we then
license under CC BY-NC-SA 4.0 like the rest of our assets.

### 4.3 Worked example of §1.2: three MIDIs of one free song

Wikimedia Commons holds three MIDI files of *The Internationale*. The
composition is the same in all three and is public domain beyond argument.
The files are not interchangeable:

| File | Sequencer | Licence on the **sequencing** | Usable under D15 |
|---|---|---|---|
| `Internationale orch2.mid` | Jerry Engelbach, 2003 | `{{Attribution\|Jerry Engelbach}}` + VRT permission ticket 2008011810001789; melody `{{PD-Internationale}}` | **YES** — attribution-only, no ShareAlike, no NC conflict |
| `Internationale-piano-Bb.mid` | Jerry Engelbach, 2001 | same | **YES** |
| `The-Internationale.mid` | Commons user J2772011, 2023 | `{{self\|cc-by-sa-4.0}}` | **NO** — ShareAlike, §1.3 |

Same tune, same site, same category, and one of the three cannot ship.
`{{PD-Internationale}}` states the melody is public domain in the United
States (published before 1931) and in France (term expired October 2017) —
which matches the independent finding in §2.1 and in §3.2.

The same shape appears on the USSR anthem: `Sua.mid` on Commons is released
under **GFDL**, a copyleft licence we cannot comply with, on top of the
anthem's own unresolved US status (§3.1).

### 4.4 Licence audit of the files downloaded on 2026-10-13

Twelve files were downloaded; **nine remain** after the D43 discards. They
live in `work/audio/candidates/` and, **since D43, are tracked in git**
(`.gitignore` exception for that folder only), so a clean checkout has the
exact bytes whose licence is recorded here. The SHA-256 list below is the
identity check: `tests/test_music.py` fails if a file in that folder has a
hash this section does not list. Each row's licence was read from the file's
own page, not from a search result: Commons files from their raw wikitext
(`?action=raw`), Mutopia files from the per-piece record. Musical verdicts
are in `docs/sound/SOUNDTRACK.md`; this table is only about rights. Stable
audition lump names (`D_CNDnn`) are in `work/audio/candidates/LUMPS.txt`.

| Lump | File in `work/audio/candidates/` | Work | Composition | Sequencer / typesetter · source page | Licence on the sequencing | D15 |
|---|---|---|---|---|---|---|
| `D_CND10` | `WM_Internationale_orch2.mid` | Интернационал, orchestral | De Geyter 1888, PD RU+US | **Jerry Engelbach**, USA, 2003 · https://commons.wikimedia.org/wiki/File:Internationale_orch2.mid | `{{Attribution\|Jerry Engelbach}}` + VRT ticket 2008011810001789 | ✅ **credit Engelbach — accepted by the CEO (D43)**; source of `D_SDINTL` |
| `D_CND11` | `WM_Internationale_piano_Bb.mid` | Интернационал, piano in B♭ | same | **Jerry Engelbach**, USA, 2001 · https://commons.wikimedia.org/wiki/File:Internationale-piano-Bb.mid | same | ✅ attribute Engelbach |
| `D_CND09` | `WM_Ej_uchnem.mid` | Эй, ухнем — Balakirev's setting, pub. 1866 | PD RU+US | **Peter Gerloff** (Commons: *Rabanus Flavus*), 2021 · https://commons.wikimedia.org/wiki/File:Ej,_uchnem!.mid | `{{self\|Cc-zero}}` — **CC0** | ✅ no obligation — **diegetic radio (D43)**; installed as `D_SDRAD1` (§4.5) |
| `D_CND12` | `WM_Kolokolchik.mid` | Колокольчик, Russian traditional | PD RU+US | **Peter Gerloff**, 2019 · https://commons.wikimedia.org/wiki/File:Kolokolchik.mid | `{{self\|Cc-zero}}` — **CC0** | ✅ no obligation — **diegetic radio (D43)**; installed as `D_SDRAD2` (§4.5) |
| `D_CND01` | `MU_Mussorgsky_BaldMountain.mid` | Ночь на лысой горе, Chernov's piano transcription | Mussorgsky d. 1881, PD; transcriber Konstantin Chernov d. 1944 → RU PD 2015, **+war 2019 — NOT VERIFIED which applies, both are past** | typeset **Robert Clausecker**, Mutopia 2013 · https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1892 | **CC BY 3.0** | ✅ attribute Clausecker + Mutopia |
| `D_CND06` | `MU_Tchaikovsky_Dumka_op59.mid` | Думка op. 59 (1886) | Tchaikovsky d. 1893, PD RU+US | Mutopia, maintainer **Vassily Checkin**, LilyPond 2.18.0 · https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=341 | **Public Domain** ("CC: No rights reserved") | ✅ |
| `D_CND07` | `MU_Tchaikovsky_Seasons_August.mid` | Времена года: Август (1876) | PD RU+US | Mutopia, maintainer **Till Rettig**, LilyPond 2.8.6, Mutopia-2006/08/21-803 · https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=803 | **Public Domain** ("CC: No rights reserved") | ✅ |
| `D_CND03` | `MU_Scriabin_Etude_op2n1.mid` | Этюд op. 2 № 1 (1887) | Scriabin d. 1915, PD RU+US | Mutopia, maintainer **Guy D. Lederfein**, LilyPond 2.10.29, Mutopia-2007/09/11-1029 · https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1029 | **Public Domain** ("CC: No rights reserved") | ✅ |
| `D_CND05` | `MU_Scriabin_Prelude_op59n2.mid` | Прелюдия op. 59 № 2 (1910) | PD RU+US | Mutopia, maintainer **Federico Bruni**, LilyPond 2.18.0 · https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=445 | **Public Domain** ("CC: No rights reserved") | ✅ |

SHA-256 of the nine files as tracked (computed 2026-10-13 on the Windows PC;
the files are the Mac's downloads, never edited in place):

```
e775a09d014c680d0c81e6a7a0bb3c7fb32ccb0525df899cb482caa078c80c4b  WM_Internationale_orch2.mid
f2469bea22035ccc5b9bf7d8171c05410a4cce0336e9872c1a46229b8fc2bb51  WM_Internationale_piano_Bb.mid
109e9125c85ed2c3a0d3dd7204eb7f930113e67a260353cebd9c2bdff8dc3cea  WM_Ej_uchnem.mid
fec3c370c7fa3b3dfd626f9f811c177e58cb66c8520b78a2ff9a07638dec0c43  WM_Kolokolchik.mid
e8000d60d4e9ba0f35a1514d2c1444b6a895d2284bae26c1d87eb8e0b815e94d  MU_Mussorgsky_BaldMountain.mid
4e84c44e348f93726805bc8e22087f8c5617fa59dbc074b76c433ad58b60f7b2  MU_Tchaikovsky_Dumka_op59.mid
50779bb218b0c3a73df33495af91b33e73be074823f4562ec95343db76b8a8a7  MU_Tchaikovsky_Seasons_August.mid
b7d9264f7529cf9d2d72778f456ecdd8bc8f236a0fe4f06a0175172f8c1cfd76  MU_Scriabin_Etude_op2n1.mid
69019b6b54646b58e2a9c0b3759fffff01958c7545b001b7d892b85db42bcf24  MU_Scriabin_Prelude_op59n2.mid
```

**Discarded by D43 and removed from the folder** (sent to the Windows
Recycle Bin, not hard-deleted; never committed). Kept here so the numbers
`D_CND02`, `D_CND04` and `D_CND08` are never reused and the record stays
whole:

| Lump | File · SHA-256 | Work | Licence | Why discarded (`SOUNDTRACK.md` §3.2) |
|---|---|---|---|---|
| `D_CND02` | `MU_RimskyKorsakov_FugueBACH.mid` · `fc73c9873624ceb0f0bdcb0fb93c1b46e146a82ab102d4edfa2c078da67731a3` | Fugue sur le nom de BACH | Public Domain (Mutopia) | a conservatory fugue on a German name |
| `D_CND04` | `MU_Scriabin_Prelude_op11n1.mid` · `4dad84aa0fdfeb695c3e54706d2c5dd731b6893e6a6fff166f5ee1344f17cae1` | Прелюдия op. 11 № 1 | Public Domain (Mutopia, id 1779) | 43 s, flat, solo piano |
| `D_CND08` | `MU_Tchaikovsky_WoodenSoldiers.mid` · `a9717d793785c3c702d85e20f99a81de60faedd29fc4e7dcb240fbc99a9b0d2b` | Марш деревянных солдатиков op. 39 | Public Domain (Mutopia, id 1806) | a children's toy march, the flattest arc measured |

**Rejected at the licence gate, not downloaded:**

| File / source | Why |
|---|---|
| `The-Internationale.mid` (Commons, user J2772011, 2023) | `{{self\|cc-by-sa-4.0}}` — ShareAlike, §1.3 |
| `Sua.mid` (Commons, USSR anthem, 2004) | **GFDL** — copyleft, §1.3; and the anthem's US status is unresolved, §3.1 |
| `Гимн России1.mid`, `CccpDisco.mid`, `RussischeHymneVer1.mid`, `Ua-ssr.mid` (Commons) | anthem material, same two problems |
| Mutopia Rachmaninoff, all 10 preludes | **CC BY-SA 4.0** |
| Mutopia Rimsky-Korsakov op. 11 (4 pieces) | **CC BY-SA 3.0** |
| Mutopia Scriabin op. 16 (5 préludes) | **CC BY-SA 2.5** (ids 759-763, re-read 2026-10-13) |
| Mutopia Mussorgsky, *Pictures at an Exhibition* | **CC BY-SA 4.0** — the one we most wanted from that catalogue |
| `archive.org/details/ussr-1` "USSR Anthem (MIDI)" | **no licence declared at all** |
| BitMidi, MIDIWorld, Midis101, hamienet, MidiShow, rusmidi.com, geocities mirrors | no per-file licence, no named sequencer — §1.2 |
| MuseScore.com scores of *Смело, товарищи, в ногу* and others | licence not machine-verifiable (HTTP 403 to automated access, 2026-10-13); and an uploader-declared CC0 on a sequencing whose provenance we cannot read is not a verifiable licence |

#### 4.4.1 The sourcing gap — closed 2026-10-13

The first audit recorded the per-piece Mutopia URL only for *Night on Bald
Mountain*; for the other seven the record's address had not been written
down. **Closed for the four that remain.** Each piece record was read again
on 2026-10-13 (Mutopia's composer tables
`make-table.cgi?Composer=TchaikovskyPI` and `?Composer=ScriabinA`, then each
`piece-info.cgi` page) and its URL, maintainer and licence are now in the
table above. Cross-check: the LilyPond version each page names (2.18.0,
2.8.6, 2.10.29, 2.18.0) is exactly the `creator: GNU LilyPond <version>`
string embedded in the corresponding file (verified with `grep -a`), so page
and file are the same edition. All four pages say "Public Domain (CC: No
rights reserved)". The three discards need no closing.

#### 4.4.2 Files we derived from the downloads

Our mechanical repairs (`tools/audio/midi_edit.py`; what and why in
`SOUNDTRACK.md` §5) create **derivative sequencings**. Every accepted licence
permits that — CC0 and PD outright, `{{Attribution}}` and CC BY 3.0 subject to
credit — and **the duty to credit survives the edit**:

| Our file | Derived from | Edit | Licence position |
|---|---|---|---|
| `work/audio/D_SDINTL.mid`, **installed as `assets/music/D_SDINTL.mid` (D43)**, byte-identical | `WM_Internationale_orch2.mid` | `--trim-head`: 2 863 ticks (1.99 s) of leading silence removed. No pitch, duration, tempo or instrument changed. SHA-256 `c94e4903ec5daabe8f605e6f78f595766e9ce20fb82204af7a6dff6319fb85a9`, reproduced from the download by `tests/test_music.py` | melody `{{PD-Internationale}}`; sequencing still `{{Attribution\|Jerry Engelbach}}` — **shipping this obliges us to credit Jerry Engelbach**, accepted by the CEO (D43), credits in §4.5. Our edit adds nothing we would license separately |
| `work/audio/D_SDFIX3.mid` | `MU_Scriabin_Etude_op2n1.mid` | `--velocity 0.85` (fixes clipping) | composition PD, sequencing PD → **no obligation** |
| `work/audio/D_SDFIX7.mid` | `MU_Tchaikovsky_Seasons_August.mid` | `--velocity 0.85 --trim-head` | composition PD, sequencing PD → **no obligation** |

Where we go further than a mechanical repair — assigning instruments to a
Mutopia score preview, cutting it to length, re-harmonising — the result is
**our arrangement**, licensed like the rest of our assets under
**CC BY-NC-SA 4.0** (D15), with the underlying sequencing credited where its
licence requires it. The originals in `work/audio/candidates/` are never
overwritten, so provenance stays checkable.

**Not a MIDI, but worth recording:** IMSLP's two *synthesised performances* of
Tchaikovsky's **Marche slave** (Brandon Amaro, 2024; Quinn Mason, 2014) are
both **CC BY 4.0** and therefore usable — but they are **MP3 renders, not
MIDI**. They would ship as OGG at megabyte scale rather than kilobyte scale.
If the CEO wants Marche slave and wants it orchestral without us doing the
orchestration, that is the route; it is a size decision, not a rights one.

### 4.5 What ships, and the credits it obliges (D43)

| Lump in `assets/music/` | Cue | Composition | Sequencing | Phonogram | Obligation |
|---|---|---|---|---|---|
| `D_SDINTL` | title screen | *L'Internationale*, Pierre De Geyter, 1888 — PD RU+US (§2.1) | **Jerry Engelbach**, 2003, `{{Attribution\|Jerry Engelbach}}` (§4.4); head trimmed by us (§4.4.2) | none — MIDI, synthesised on the player's machine | **credit Jerry Engelbach** |
| `D_SDM1N2` | MAP01 (D95) | original, `sound-designer` 2026-10-20 (`tools/audio/compose_map01.py`, variant `D_SDM01N2`): composed under D92, the one exception to D59; no phrase of another work (`tests/test_compose_map01.py`) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDRAD1` | diegetic radio (`SD_Radio`, `docs/engine/MOD-SPEC.md` §6.7) | «Эй, ухнем», Balakirev's setting, pub. 1866 — PD RU+US | **Peter Gerloff**, 2021, **CC0** (§4.4, `D_CND09`); byte-identical to `WM_Ej_uchnem.mid`, SHA-256 `109e9125…` above, no edit | none — MIDI | **none**; Gerloff credited as a courtesy |
| `D_SDRAD2` | diegetic radio (`SD_Radio`, same) | «Колокольчик», Russian traditional — PD RU+US | **Peter Gerloff**, 2019, **CC0** (§4.4, `D_CND12`); byte-identical to `WM_Kolokolchik.mid`, SHA-256 `fec3c370…` above, no edit | none — MIDI | **none**; Gerloff credited as a courtesy |
| `D_SDFUNR` | MAP02, the metro — **D62 draft, pending the CEO's ear** | «Вы жертвою пали», 1870s, every candidate author d. before 1916 — PD RU+US (§4.6.1) | ours (D44), from the voice line of Detlaf's 1905 edition; harmony and orchestration ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDGATE` | MAP03, Tankograd — **D62 draft, pending the CEO's ear** | «Богатырские ворота», Mussorgsky (d. 1881), pub. Bessel 1886, ed. Rimsky-Korsakov (d. 1908) — PD RU+US (§4.6.4) | ours (D54), from the top voice of the 1886 edition | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDTITL` | intermission, the stats screen between maps (D83; GameInfo `IntermissionMusic`, replacing Freedoom's `D_DM2INT`) | original, `sound-designer` 2026-10-13 (`tools/audio/gen_music.py`, `build_title`) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM01T` | RANGE, the practice range (D86) | original, `sound-designer` 2026-10-13: `D_SDM01E` (MAP01's theme, `gen_music.py`) cut to its melodic part from bar 49 by `gen_enemy_alts.py` (an edit of our own sequence, not new music, D59) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM04A` | MAP04, the Trans-Siberian (D106), variant A | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM04B` | MAP04, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM05A` | MAP05, the Volga Dam (D106), variant A | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM05B` | MAP05, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM06A` | MAP06, Red Square (D106), variant A | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM06B` | MAP06, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDBS6A` | MAP06's boss loop with A (bars 29-52 of `D_SDM06A`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDBS6B` | MAP06's boss loop with B (bars 29-52 of `D_SDM06B`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDE2IA` | episode 2's intermission, after MAP04 and MAP05 (`intermusic`) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDE2IB` | episode 2's intermission, variant B (packed, not wired) | original, `sound-designer` 2026-10-21 (`tools/audio/compose_episode2.py`), approved by the CEO in D106; quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM07A` | MAP07, the radar station on Novaya Zemlya (D113), variant A | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM07B` | MAP07, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM08A` | MAP08, the submarine base at Severomorsk (D113), variant A | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM08B` | MAP08, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM09A` | MAP09, the portal at Tunguska (D113), variant A | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDM09B` | MAP09, variant B (`SD_MusicVariant`) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDBS9A` | MAP09's final boss loop with A (a piece of its own, not a cut) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDBS9B` | MAP09's final boss loop with B (a piece of its own) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDE3IA` | episode 3's intermission, after MAP07 and MAP08 (`intermusic`) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |
| `D_SDE3IB` | episode 3's intermission, variant B (packed, not wired) | original, `sound-designer` 2026-10-22 (`tools/audio/compose_episode3.py`), approved unheard by the CEO in D113 ("las doy por buenas", "I take them as good"); quotes no Soviet song, folk tune, classical theme or phrase of our own earlier pieces (the generator's self-check) | ours | none — MIDI | none; ours under CC BY-NC-SA 4.0 (D15) |

**N9e (2026-10-20, D83 and D86).** `D_SDTITL` is the intermission and
`D_SDM01T` the range's piece; `D_SDAMUR`, the range's D62 draft, was
rejected by the CEO (D83) and no longer ships (its score provenance stays
in §4.6.2). D95 put `D_SDM1N2` (our composition, D92) on MAP01; `D_SDM01`,
MAP01's D43 theme, left the package with it. Neither new row adds a credit obligation: both are our own
sequences.

**D106 (2026-10-22).** The CEO approved all ten episode 2 pieces ("10/10 OK"):
the A and B of MAP04, MAP05 and MAP06, MAP06's two boss loops and the
episode's two intermission pieces, installed byte for byte from
`work/audio/episode2/` (`tests/test_music.py` regenerates each). All ten are
our own compositions, written under the D104 brief: no rights question beyond
our own licence, no credit obligation.

**D113 (2026-10-22).** The CEO approved, without hearing them, all ten
episode 3 pieces ("las doy por buenas", "I take them as good"): the A and B of MAP07, MAP08 and
MAP09, the final boss's two loops (pieces of their own, not cuts) and the
episode's two intermission pieces, installed byte for byte from
`work/audio/episode3/` (`tests/test_music.py` regenerates each). All ten are
our own compositions under the D112 brief: the generator's self-check finds
no two-bar shape of Episodes 1-2's themes and no eight-note run of any other
installed MIDI. No rights question beyond our own licence, no credit
obligation. Episode 2's B pieces, which D112 had borrowed provisionally for
MAP07-MAP09, are again only episode 2's variants.

**The D62 drafts (2026-10-14, backlog N8).** The rows of `D_SDFUNR` and
`D_SDGATE` above (and `D_SDAMUR`'s, until N9e) were
installed in `assets/music/` and wired in `src/lumps/MAPINFO` so the CEO
hears them while playing, **before** his approval: they are drafts until he
hears them (`SOUNDTRACK.md` §0). Nothing was composed or sequenced for N8
(D59): each file is the D44/D54 draft already in `work/audio/`, copied byte
for byte (`tests/test_music.py` regenerates and compares). The scores stay
in `work/audio/scores/`, never packed (§4.6). No row adds a credit
obligation; Mussorgsky and Kyuss may be named as a courtesy.

**The credit line**, to be reproduced verbatim wherever the mod credits
anyone (the release credits of gate G6, a ModDB page, a README):

> *The Internationale* (title music): composed by Pierre De Geyter (1888),
> public domain; MIDI sequence by **Jerry Engelbach**, used under his
> attribution licence (Wikimedia Commons, `File:Internationale_orch2.mid`).

Where it already stands: this section; `docs/art/LICENSES.md` § Music (the
register `tools/check_pk3.py` reads); `docs/sound/SOUNDTRACK.md` Card 0;
`LICENSE.md`'s list of third-party material. **Not yet**: an in-game credits
screen — the mod has none; it is G6 work (`docs/ROADMAP.md`) and this line
is what it must carry. *Night on Bald Mountain* (Clausecker / Mutopia) would
add a second line only if it is ever packed; it is not.

The CC0 radio pieces (`WM_Ej_uchnem.mid`, `WM_Kolokolchik.mid`, Peter
Gerloff) carry no obligation; crediting Gerloff as a courtesy when they ship
is recommended, not required. **They ship since 2026-10-13** as `D_SDRAD1`
and `D_SDRAD2` (installed by `mod-engineer` for the radio actor of
`docs/engine/MOD-SPEC.md` §6.7, ADR 008). The courtesy line, for the same
places as the Engelbach line:

> Radio music: *Ey, ukhnem* (Balakirev's setting) and *Kolokolchik*, public
> domain; MIDI sequences by **Peter Gerloff**, dedicated to the public
> domain under CC0 (Wikimedia Commons).

### 4.6 Scores downloaded under D44 (2026-10-14)

**D44** (CEO, 2026-10-14, `docs/PRD.md` §5): *one public-domain score may be
downloaded per self-sequenced piece, with provenance and SHA-256 recorded.*
The PM's conditions, applied to every file: notation only (no MIDI, no
recording); composer **and** edition public domain; URL, licence and size
written down **before** the download, and nothing over 20 MB; each file in
its own new directory under `work/audio/scores/<piece>/`; the files treated
as untrusted data (page images extracted with a stdlib parser under
`python -I`, nothing inside them executed). The pre-download record was
taken at **2026-10-14 08:34 UTC**; both sizes below are the server's
`Content-Length` read by a HEAD request at that time, and both downloads
came in at exactly that size.

**What the scores are used for, and what ships.** The PDFs are reference
material: they stay in `work/audio/scores/`, which is gitignored like the
rest of `work/audio/` except `candidates/` — **they are never packed and
never redistributed**. What ships, if the CEO approves the drafts, is *our*
sequencing of the notes they print: composition public domain, sequencing
ours under CC BY-NC-SA 4.0 (D15), no phonogram (MIDI). The scan is used only
to read the notes.

#### 4.6.1 «Вы жертвою пали» → `D_SDFUNR`

| Field | Value |
|---|---|
| **File** | `work/audio/scores/vy_zhertvoyu_pali/Vy_zhertvoyu_pali_marsh-1905_Detlaff.pdf` |
| **SHA-256** | `af423178931d28e98897c7054a5ea1cd332181d0cb7e32636585174a499c83b4` |
| **Size** | 1 446 410 B (1.38 MiB) — stated before download, under the 20 MB limit |
| **URL** | https://starinnye-noty.ru/files/Vy_zhertvoyu_pali_marsh-1905_Detlaff.pdf |
| **Page** | https://starinnye-noty.ru/вы-жертвою-пали-революционный-марш (the collection «Старинные русские ноты», which lists four editions of the song; this is the earliest) |
| **Downloaded** | 2026-10-14, by `sound-designer`, under D44 |
| **Edition** | «Траурный маршъ» («Вы жертвою пали»), *для пѣнія съ аккомпанементомъ*, «Аррандж. Ф. I. Детлафъ», Moscow, Торговый домъ Ф. I. Детлафъ и Ко, series «Народныя пѣсни освободительнаго движенія въ Россіи» (no. 7), «Дозв. ценз. Москва 9 Ноября 1905 г.»; 4 scanned pages: cover, two pages of music (voice and piano, 2/4, four flats, *Allegro non troppo*), back-cover catalogue |
| **Licence of the page / scan** | **none stated.** The site carries only a collection notice (*"© Antique Russian Golden Age Piano Sheet Music Collection"*); the scan is a flat reproduction of a 1905 print. A faithful photograph of a public-domain two-dimensional work attracts no new copyright in the United States (*Bridgeman v. Corel*, 1999); in Russia **NOT VERIFIED** — moot here, because the scan is not redistributed (above) |
| **Composition** | the 1870s revolutionary funeral song: Varlamov's tune per ru.wikipedia, unattributed in en.wikipedia (§2.2; the disagreement stands — **the edition names no composer**, only the arranger). Every candidate author died before 1916 → **PD in Russia and the United States** |
| **Edition** | published 1905 → **PD in the United States** (published before 1931). Arranger **Ф. И. Детлаф** (F. I. Detlaf), the publisher himself: **life dates NOT VERIFIED**. That does not touch what we use: **only the voice line is copied**, which is the traditional tune his arrangement sets; his piano accompaniment is not used, and the harmony of `D_SDFUNR` is our own (`gen_music.py`, `FUNERAL_HARMONY`) |
| **Lyrics** | Anton Amosov (Arkhangelsky), d. 1915 → PD; **not used** (instrumental) |

#### 4.6.2 «Амурские волны» → `D_SDAMUR`

| Field | Value |
|---|---|
| **File** | `work/audio/scores/amurskie_volny/AMURSKIE_VOLNY_vals_KUSS_Vladivostok.pdf` |
| **SHA-256** | `a46f4966a4b4da1a8d8a31d97f2044a6111ecadc311062ac7e8c51bc95eb030d` |
| **Size** | 5 622 728 B (5.36 MiB) — stated before download, under the 20 MB limit |
| **URL** | https://starinnye-noty.ru/files/AMURSKIE_VOLNY_vals_KUSS_Vladivostok.pdf |
| **Page** | https://starinnye-noty.ru/амурские-волны-лихар (the same collection; the page also lists a 1959 Baku "simplified" Soviet edition, **not** taken, and an unrelated waltz of the same title by P. Likhar) |
| **Downloaded** | 2026-10-14, by `sound-designer`, under D44 |
| **Edition** | «Амурскія волны», вальсъ, «Соч. М. А. Кюссъ, Op. 12», piano solo, Vladivostok, издатель Н. П. Лукьяновъ, plate **2239**, engraved and printed by S. Schmidt, St Petersburg; the collection dates the issue **1909-1914**; 5 scanned pages: cover, Introduction (p. 2), the waltz (p. 3), its continuation |
| **Licence of the page / scan** | **none stated**; same collection notice and same position as §4.6.1 |
| **Composition** | Max Kyuss, 1874-1942 → **PD in Russia** (free 1 Jan 2017 at the latest, §2.2) and **PD in the United States** (published 1909) |
| **Edition** | the composer's own first edition, 1909-1914, no editor or arranger named → **PD in both countries** for the same reasons |
| **Lyrics** | none: the edition is instrumental; the later Soviet texts (1944 and after) are protected and **not used** |

Two Soviet-era editions met on the way were **rejected** before download:
the 1954 Muzgiz SATB arrangement by Vl. Sokolov (archive.org, University of
Toronto scan) and the 1959 Baku simplified edition — both carry a protected
arranger's contribution.

#### 4.6.3 Glinka's *Patriotic Song* → `D_SDGLNK`: **no download — no reliable public-domain score found; dropped by D54**

> **D54 (CEO, 2026-10-14) closed this:** Glinka is dropped from the anthem
> slot and `D_SDGLNK` will not be written. The replacement is §4.6.4; the
> record below stays as the reason.

The PM's condition (D44 brief, point 5) was that whatever is downloaded must
be **Glinka's 1833 melody, not a protected arrangement**. Nothing found on
2026-10-14 meets it:

| Source checked | What it is | Verdict |
|---|---|---|
| Commons `File:Russian SFSR - Russian Anthem Music Sheet.InstrumentalSimple (1990-2000).svg` (750 714 B) | marked "own work" by Commons user Jeromi Mikhael, 2018; its description calls it a simple instrumental sheet of the anthem of the RSFSR and the Russian Federation, 1990-2000, and its own source line is the GIF below | **rejected**: the 1990-2000 **anthem** version — the translator's warning confirmed |
| Commons `File:Patriotic Song - Mikhail Glinka.gif` (20 792 B), tagged public domain | a melody sheet whose credited source is `nationalanthems.info/ru-00~.gif`, a modern typesetting of the **1990-2000 anthem melody** from a site licensed CC BY 4.0, not PD | **rejected**: it shows the anthem as performed, and nothing ties its notes to Glinka's manuscript rather than to the 1944 orchestration by **Mikhail Bagrinovsky (1885-1966)** the anthem descends from; a footnote in en.wikipedia reports a claim that the tune as known belongs to Bagrinovsky rather than to Glinka. Bagrinovsky is protected in Russia to 1 Jan 2037 |
| IMSLP, category *Glinka, Mikhail* (73 works, listed through the API) | no *Patriotic Song* / *Motif de chant national* | nothing to take |
| Glinka's autograph, *Motif de chant national* (1833, piano; Russian National Library, rediscovered 1885 per en.wikipedia) | no digitised facsimile found; Gallica, the Presidential Library and the НЭБ answer automated requests with a block or a browser check, which this project does not bypass | not available to us |
| Glinka, *Complete Works* (Muzgiz, 1950s) | may print the manuscript; not on IMSLP for this piece, and a Soviet editorial edition would need its own rights check | not available |

**So `D_SDGLNK` stays blocked, and no melody was written from memory.**
What would have unblocked it: (a) a facsimile of the 1833 autograph (the
RNB's manuscript department can be asked; the manuscript of a composer who
died in 1857 is public domain), or (b) a pre-1931 printed edition of the
*Motif de chant national* — **NOT VERIFIED** that one was printed before
the Soviet period at all. D54 chose to change the piece instead.

#### 4.6.4 «Богатырские ворота» → `D_SDGATE` (D54)

D54 (CEO, 2026-10-14): *"busca alternativa, cambiamos pieza musical y ya"* ("look for an alternative, we change the piece of music and that is it") —
a public-domain replacement for the anthem slot, on the terms of D44 (one
score downloaded, provenance recorded). The same conditions as §4.6 were
applied: notation only; composer **and** edition public domain in Russia and
in the United States; URL, licence and size written down **before** the
download, nothing over 20 MB; the file in its own new directory; treated as
untrusted data (inspected only with a stdlib script under `python -I`,
nothing in it executed). The pre-download record was taken at **2026-10-14
10:00 UTC**: the size is the server's `Content-Length` from a HEAD request
and Commons' own `imageinfo` record, and the download came in at exactly
that size with the SHA-1 Commons lists.

| Field | Value |
|---|---|
| **File** | `work/audio/scores/bogatyrskie_vorota/Mussorgsky_Pictures_Exhibition_Piano_Score.pdf` |
| **SHA-256** | `0a73559cd865083558f6e5923dddae4390069883dad795725c19f18646e58b71` |
| **SHA-1** | `c49c00c49d98cad2515313fb609a6f14750d0eef` — identical to the value Wikimedia Commons records for the file |
| **Size** | 1 749 135 B (1.67 MiB), 35 pages — stated before download, under the 20 MB limit |
| **URL** | https://upload.wikimedia.org/wikipedia/commons/5/53/Mussorgsky_Pictures_Exhibition_Piano_Score.pdf |
| **Page** | https://commons.wikimedia.org/wiki/File:Mussorgsky_Pictures_Exhibition_Piano_Score.pdf (uploaded 2022-03-27 by Commons user Guy vandegrift, "obtained from IMSLP") |
| **Licence of the page** | `{{PD-old-70-expired}}`, read from the file page's wikitext. The PDF is a flat scan (embedded metadata: EPSON Expression 10000XL, 2010); a faithful reproduction of a public-domain two-dimensional work attracts no new copyright in the United States (*Bridgeman v. Corel*, 1999), in Russia **NOT VERIFIED** — moot, because the scan is not redistributed (§4.6) |
| **Downloaded** | 2026-10-14, by `sound-designer`, under D54 |
| **Edition** | «Картинки съ выставки», *Десять пьесъ для фортепіано*, «Владиміру Васильевичу Стасову», St Petersburg and Moscow, **В. Бессель и К°** / W. Bessel & C^ie, **plate 1560** (on every music page), printed by Bessel's own works («Нотопечатня В. Бессель и К° СПБ»); the title page names Breitkopf & Härtel and Gebethner & Wolff as agents, price 2 r. 50 k. / Mk 6. This is the **first edition, 1886**, edited by **N. A. Rimsky-Korsakov** (IMSLP lists plate 1560 for the 1886 first edition). The copy itself is an issue of that edition whose print year is **NOT VERIFIED**; its pre-1918 orthography («Богатырския», «Кіевѣ») places it before the 1918 spelling reform. No. 10 is printed pages 30-34 (scan pages 31-35) |
| **Composition** | Modest Mussorgsky, 1839-1881; *Pictures at an Exhibition* written 1874, published 1886 → **PD in Russia** (died 1881) and **PD in the United States** (published 1886) |
| **Edition rights** | editor Nikolai Rimsky-Korsakov, 1844-1908 → **PD in both countries**; published 1886 → US PD. And only the top voice (Mussorgsky's melody) is copied, not the piano writing |
| **Lyrics** | none: a piano piece |
| **Not used** | Ravel's 1922 orchestration and every other arrangement; the Mutopia typeset of *Pictures* (**CC BY-SA 4.0**, §4.4); IMSLP's modern typesets (CC BY-SA). The chorale episodes of No. 10 (which quote an Orthodox chant) and the bell passage are not copied |
| **How the notes were read** | the PDF's page images are **JBIG2**-coded, for which the Python standard library has no decoder; the pages were therefore read from Wikimedia's own page renders of this same file (`upload.wikimedia.org/.../thumb/...`, scan pages 31 and 35 at 3840 px; Commons renders the file whose SHA-1 is above), measured with Pillow and `numpy` and checked by eye. Nothing in the PDF was executed or decoded by us beyond listing its objects |

What `D_SDGATE` takes from it, bar by bar, is `SOUNDTRACK.md` Card 5;
what ships, if the CEO approves the draft, is our sequencing under
**CC BY-NC-SA 4.0** (D15), no phonogram, no obligation to credit anyone
(Mussorgsky is named as a courtesy, like Gerloff in §4.5).

#### 4.6.5 The alternatives weighed for the anthem slot (D54), rights side

The test applied to each: composer **dead more than 70 years** (74 with the
war extension), **published before 1929** (so the United States cannot
have restored it under the URAA, whatever the Russian term), and **a
public-domain score an agent can download** from IMSLP, Commons or a source
of the D44 kind, without passing a CAPTCHA or a browser check. The musical
side of the comparison is `SOUNDTRACK.md` Card 5.

| Candidate | Composer (dates) · publication | RU | US | Score reachable? | Verdict |
|---|---|---|---|---|---|
| **«Богатырские ворота»**, *Pictures at an Exhibition* No. 10 | Mussorgsky (1839-1881) · Bessel 1886, ed. Rimsky-Korsakov (1844-1908) | ✅ | ✅ | **yes**: Commons, 1.67 MiB, `{{PD-old-70-expired}}`, §4.6.4 | ✅ **chosen** |
| **«Славься»**, Epilogue of *A Life for the Tsar* | Glinka (1804-1857) · composed 1836, vocal score pub. 1857 (Stellovsky), Jurgenson editions before 1918; original text Rosen (1800-1860) | ✅ | ✅ | **not by an agent.** The clean edition is IMSLP's Jurgenson vocal score, Act V as its own file, `PMLP26589-Glinka-ZhisnVSa5.pdf`, **6 491 982 B**, tagged Public Domain (size from IMSLP's API, 2026-10-14). But IMSLP now answers a file request from a client without its cookie with a **human-verification CAPTCHA** ("IMSLP – Bot Check", `imslp.org/friendlytest.html`), which an agent does not pass. The Sibley scan of the Gutheil vocal score is **28 354 618 B**, over the 20 MB limit; Commons and the Internet Archive hold no edition; starinnye-noty has only Antonida's romance. **Do not use** the Soviet *Ivan Susanin* editions on the same IMSLP page (Muzgiz 1939 and 1965, ed. Vladimir Protopopov, 1908-2005; libretto Sergey Gorodetsky, 1884-1967): IMSLP's "Public Domain" there is the Canadian tag; both are protected in Russia and, published after 1930, in the United States | ⚠️ **rights-clean, source blocked.** Unblocked in one step if the PM or the CEO downloads that one IMSLP file by hand |
| **«Слава»**, Prologue chorus of *Prince Igor* | Borodin (1833-1887), completed by Rimsky-Korsakov (d. 1908) and Glazunov (1865-1936; RU PD since 2007) · Belaieff 1888 | ✅ | ✅ | not by an agent: IMSLP only (same CAPTCHA) | ⚠️ rights-clean, source blocked |
| **«Смело, товарищи, в ногу»** | Radin (1860-1900) · pub. 1901-02 | ✅ | ✅ | **no PD edition found**: starinnye-noty has it only inside «Любимые песни Ильича» (Moscow: Muzyka, 1969), a Soviet arrangement, protected | ❌ no reliable PD score |
| **«Русская Марсельеза»** («Отречёмся от старого мира») | melody Rouget de Lisle (1760-1836), Russian words Lavrov (1823-1900) · Detlaf, Moscow, 1905 (starinnye-noty) | ✅ | ✅ | yes | ❌ rights-clean, rejected on sound (Card 5) |
| **«Прощание славянки»** | **Agapkin (1884-1964)** · Tambov 1912 | ❌ | ✅ | — | ❌ **protected in Russia until 1 Jan 2039**: he died in 1964 and served through the war (he conducted the band at the 7 Nov 1941 Red Square parade), so 1964 + 74 + 1. Free in the US only (published 1912), and the anthem slot needs free in both (§5(b)) |
| Alexandrov's anthem, «Священная война» | Alexandrov (1883-1946) · 1939-1944 | ✅ | ❌ | — | ❌ URAA-restored in the US (D43, §5(b)) |
| Tchaikovsky, *Marche slave* / *1812* | Tchaikovsky (1840-1893) · 1876 / 1882 | ✅ | ✅ | yes (IMSLP) | ❌ both quote «Боже, царя храни!», the tsarist anthem: wrong for a Soviet state cue (§2.3) |

---


## 5. Recommendations

### (a) Recommended, with the clean route for each

| Priority | Work | Route | Where it goes |
|---|---|---|---|
| 1 | **Интернационал / The Internationale** | **downloaded, 2026-10-13**: Engelbach's orchestral MIDI from Commons, attribution-only (§4.4), repaired by us as `D_SDINTL` (§4.4.2), **installed (D43)**. Sequencing from the IMSLP score is **not** necessary — it stays as the fallback only if the CEO dislikes Engelbach's orchestration itself | title screen (CEO's choice, 2026-10-13), finale |
| 2 | **Tchaikovsky, Marche slave** | no free MIDI exists. Either IMSLP's CC BY 4.0 synthesised **MP3** (§4.4), or we sequence it from the PD score | main theme / MAP01 |
| 3 | **Mussorgsky, Night on Bald Mountain** | CC0/PD recording | alien-infested areas |
| 4 | **Scriabin** (Sonata No. 9, *Prometheus*) | CC0/PD recording | dread ambience, Fourth Reich zones |
| 5 | **Смело, товарищи, в ногу** | sequence ourselves — free words *and* music in both countries | Soviet-held areas, diegetic |
| 6 | **Амурские волны (Kyuss, 1909)** | sequence ourselves | diegetic radio at the cosmodrome, a quiet moment |
| 7 | **Вы жертвою пали** | sequence ourselves | death / aftermath / ending |
| 8 | ~~Glinka, Патриотическая песня~~ → **Mussorgsky, «Богатырские ворота»** (D54) | sequenced by us from the 1886 Bessel edition, draft `D_SDGATE` (§4.6.4) | **the anthem slot**: the zero-risk substitute for the USSR anthem. Glinka dropped by D54 for want of a reliable score (§4.6.3) |
| 9 | ~~USSR anthem melody (Alexandrov)~~ | **not used (D43)**: its 1944 publication is URAA-restored in the US to 2040 unless the state-symbol argument holds (§3.1, NOT VERIFIED as US law), and D43 excludes US-restored works | — |
| 10 | **Original Artemyev-style ANS ambience** | we compose it | the bulk of in-level music |

### (b) Discarded, and why

- **Shostakovich** — protected in Russia until 2050, restored in the US, and actively
  enforced. The most tempting and the most dangerous.
- **Prokofiev** — protected in Russia until 2028; in the US only his pre-1931
  publications are free, and those are not free in Russia. No overlap.
- **Катюша, Полюшко-поле, Смуглянка, Москва майская** — composers died 1973-1990;
  protected into the 2048-2065 range. Not close.
- **Марш энтузиастов / Песня о Родине (Dunayevsky)** — borderline, almost certainly
  protected in Russia until 2030 via the war extension. Not worth the argument.
- **Подмосковные вечера** (Solovyov-Sedoi, d. 1979) — protected. Relevant because it
  is the *Mayak* radio call sign and therefore an obvious diegetic idea for 1977. Do
  not use it.
- **День Победы** (Tukhmanov, b. 1940, living) — protected. Also anachronistic: 1975,
  but inseparably associated with the later Brezhnev cult.
- **Any Melodiya / Alexandrov Ensemble / Soviet State Radio recording**, of anything,
  including works whose composition is free.
- **Any CC BY-SA audio or score**, because D15 ships assets as CC BY-NC-SA 4.0 and
  ShareAlike forbids the added NonCommercial restriction.
- **Every work free in Russia but restored in the United States** (D43) —
  *Священная война* above all, also the *Гимн партии большевиков* and the
  Alexandrov anthem melody. Our distribution is in practice US-hosted.
  The inverse case (free in the US, protected in Russia: *Прощание
  славянки*, *Авиамарш*) is **not** covered by D43 and stays unused until
  its Russian term ends.

### (c) The standing warning

> **A public-domain composition does not imply a public-domain recording.** The three
> rights expire independently. For every work in this document the default assumption
> is: *composition may be free, the recording you found is not.* The only recordings
> we may ship are (i) explicitly PD/CC0/CC BY recordings whose underlying composition
> is also free in both Russia and the US, and (ii) recordings and sequences we make
> ourselves.

---

## 6. What the engine side will need from me

Declared here so `mod-engineer` and `level-designer` can plan. Since D43 two
lumps exist, `assets/music/D_SDINTL.mid` and `assets/music/D_SDM01.mid`,
packed by the build as `music/<LUMP>.mid` (`tools/sdbuild/pk3.py`,
`ASSET_DIRS`), and wired in `MAPINFO` by `mod-engineer` (commit 51c2746,
`SOUNDTRACK.md` §7).

- **Formats**: GZDoom plays OGG, MP3, FLAC, MIDI and MOD/XM/IT. We use **OGG Vorbis**
  for recordings and **MIDI/XM** for anything we sequence, to keep the PK3 small.
- **`MAPINFO`** per map: `music = "D_SDM01"` style lump names, `SD` prefix per D1.
- **`SNDINFO`**: music lumps are *not* declared in SNDINFO (that is for sound effects
  and `$musicalias`); the MAPINFO `music` key and `$musicalias` entries are the
  interface.
- **Licence register**: every music lump has a row in `docs/art/LICENSES.md`
  § Music, which is the file `tools/check_pk3.py` reads; the row points back
  here. No second register under `docs/sound/` was created (one owner per
  fact).

---

## 7. Decisions — settled by D43, and the one left open

> **The live list of music decisions is `docs/sound/SOUNDTRACK.md` §8**, which
> owns "what plays where". What follows is only the part that is a *rights*
> question. On 2026-10-13 the CEO accepted every open recommendation of
> SOUNDTRACK §8 (*"Acepto las recomendaciones de música"* ("I accept the music recommendations"), **D43**,
> `docs/PRD.md` §5). Points 0-3 are settled; point 4 was never in SOUNDTRACK
> §8 and stays open, blocking nothing.

0. **Attribution — SETTLED (D43): accepted.** Shipping Engelbach's
   Internationale obliges us to credit **Jerry Engelbach** wherever we credit
   anyone; the line and where it stands are §4.5. Mutopia's *Night on Bald
   Mountain* would oblige a credit to **Robert Clausecker / Mutopia Project**,
   but only if it is ever packed.
1. **The USSR anthem — SETTLED (D43): the anthem slot goes to Glinka's
   *Patriotic Song*** (§2.3), sequenced by us: a real national anthem of
   Russia (1990-2000), free beyond any argument in both countries. The
   Alexandrov melody is not used anywhere (point 2). **Amended by D54
   (2026-10-14):** Glinka is dropped for want of a reliable score; the slot
   goes to Mussorgsky's «Богатырские ворота», draft `D_SDGATE` (§4.6.4).
2. **Russia-free / US-restored works — SETTLED (D43): excluded**, with
   *Священная война* named as the main case. See §5(b).
3. **Scope of the soundtrack.** *Superseded by D23* (2026-10-13): *"Free MIDI
   sequences with a verified licence come first, our own sequencing is the
   fallback for works that exist only as free scores."* Our own pieces stay
   in use where they are the better object: `D_SDM01` plays MAP01 (D43).
4. **Orchestration labour — open, not blocking.** Every free MIDI of the
   Russian classics is a solo-piano score preview (§4.2). Making one usable
   means we assign the instruments. The choice is: ship piano, pay the
   orchestration labour, or accept IMSLP's CC BY 4.0 **MP3** renders and a
   larger PK3. *Recommendation: pay the orchestration labour on one piece
   only, when a map needs it*, and keep the rest for diegetic use where piano
   is plausible. Nothing is waiting on this today.

5. **Glinka's *Patriotic Song* — CLOSED by D54 (2026-10-14): dropped.** No
   public-domain score that is demonstrably Glinka's 1833 melody was found
   (§4.6.3). The replacement, «Богатырские ворота», is sequenced as the
   draft `D_SDGATE` from one downloaded score (§4.6.4); the alternatives
   weighed are §4.6.5. If the CEO prefers «Славься», its rights are clean
   and only the download is blocked (one IMSLP file, by hand).

Nine downloaded files remain in `work/audio/candidates/` (§4.4), tracked in
git. Two scores downloaded under D44 and one under D54 sit in `work/audio/scores/` (§4.6),
gitignored and never packed. **Two lumps are in `assets/` and therefore in the PK3: `D_SDINTL` and
`D_SDM01`** (§4.5).

---

## 8. Sources

Legal frame:
- Civil Code of the Russian Federation, Part IV (arts. 1256, 1259, 1281, 1327) — WIPO Lex: https://www.wipo.int/wipolex/en/legislation/details/12785
- Commons: Copyright rules by territory / Russia — https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Russia
- Commons: Copyright rules by territory / Soviet Union — https://commons.wikimedia.org/wiki/Commons:Copyright_rules_by_territory/Soviet_Union
- US Copyright Office, Classics Protection and Access Act (pre-1972 recordings) — https://www.copyright.gov/music-modernization/pre1972-soundrecordings/
- CRS, *The Music Modernization Act: Extending Copyright Protection to Pre-1972 Sound Recordings* — https://www.congress.gov/crs-product/LSB10181
- PM, *Can we use original Soviet poster art?* — `docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md`

Per-file licence pages read on 2026-10-13 (the §4.4 audit):
- `{{PD-Internationale}}` template — https://commons.wikimedia.org/wiki/Template:PD-Internationale
- File:Internationale orch2.mid — https://commons.wikimedia.org/wiki/File:Internationale_orch2.mid (wikitext via `?action=raw`)
- File:Internationale-piano-Bb.mid — https://commons.wikimedia.org/wiki/File:Internationale-piano-Bb.mid
- File:The-Internationale.mid (**CC BY-SA, rejected**) — https://commons.wikimedia.org/wiki/File:The-Internationale.mid
- File:Sua.mid (**GFDL, rejected**) — https://commons.wikimedia.org/wiki/File:Sua.mid
- File:Ej, uchnem!.mid — https://commons.wikimedia.org/wiki/File:Ej,_uchnem!.mid
- File:Kolokolchik.mid — https://commons.wikimedia.org/wiki/File:Kolokolchik.mid
- Mutopia, *Night on Bald Mountain* (CC BY 3.0) — https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1892
- Mutopia, re-read 2026-10-13 to close §4.4.1 (all "Public Domain (CC: No rights reserved)"): Tchaikovsky *Doumka* op. 59 — https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=341 · *The Seasons: August* — https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=803 · Scriabin *Etude* op. 2 № 1 — https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=1029 · *Prelude* op. 59 № 2 — https://www.mutopiaproject.org/cgibin/piece-info.cgi?id=445 · composer tables https://www.mutopiaproject.org/cgibin/make-table.cgi?Composer=TchaikovskyPI and `?Composer=ScriabinA`
- Mutopia browse by composer (licence per piece) — https://www.mutopiaproject.org/browse.html
- Mutopia licence policy — https://www.mutopiaproject.org/legal.html
- IMSLP, *Slavonic March* op. 31, synthesised performances CC BY 4.0 (MP3, not MIDI) — https://imslp.org/wiki/Slavonic_March,_Op.31_(Tchaikovsky,_Pyotr)
- IMSLP, *L'Internationale* (De Geyter) — https://imslp.org/wiki/L'Internationale_(De_Geyter,_Pierre)
- archive.org, "USSR Anthem (MIDI)", **no licence declared** — https://archive.org/details/ussr-1

Read on 2026-10-14 for D54 (§4.6.4-4.6.5):
- Commons, `File:Mussorgsky Pictures Exhibition Piano Score.pdf`, `{{PD-old-70-expired}}` — https://commons.wikimedia.org/wiki/File:Mussorgsky_Pictures_Exhibition_Piano_Score.pdf
- IMSLP, *Pictures at an Exhibition* (Bessel 1886 first edition, plate 1560, ed. Rimsky-Korsakov) — https://imslp.org/wiki/Pictures_at_an_Exhibition_(Mussorgsky,_Modest) (wikitext through the API)
- IMSLP, *A Life for the Tsar* (Jurgenson vocal score, Act V `PMLP26589-Glinka-ZhisnVSa5.pdf`, 6 491 982 B; the Soviet *Ivan Susanin* editions) — https://imslp.org/wiki/A_Life_for_the_Tsar_(Glinka,_Mikhail) (wikitext and file sizes through the API; the file itself is behind IMSLP's CAPTCHA)
- IMSLP, *Prince Igor* (Belaieff 1888) — https://imslp.org/wiki/Prince_Igor_(Borodin,_Aleksandr)
- starinnye-noty, marches and anthems (Detlaf 1905 «Русская Марсельеза»; «Любимые песни Ильича», 1969) — https://starinnye-noty.ru/марши-гимны-история

Works and people:
- Alexander Vasilyevich Alexandrov (1883-1946) — https://en.wikipedia.org/wiki/Alexander_Vasilyevich_Alexandrov
- State Anthem of the Soviet Union — https://en.wikipedia.org/wiki/State_Anthem_of_the_Soviet_Union
- File:Soviet Union national anthem (instrumental), 1977.oga, `{{PD-RU-exempt}}` + art. 1281 — https://commons.wikimedia.org/wiki/File:Soviet_Union_national_anthem_instrumental_1977.ogg
- Sergey Mikhalkov (1913-2009) — https://en.wikipedia.org/wiki/Sergey_Mikhalkov
- El-Registan (1899-1945) — https://en.wikipedia.org/wiki/El-Registan
- Pierre De Geyter (1848-1932) — https://en.wikipedia.org/wiki/Pierre_De_Geyter
- The Internationale (French term expired Oct 2017) — https://en.wikipedia.org/wiki/The_Internationale and https://en.wikibooks.org/wiki/The_Internationale/Performing_and_respecting_copyright
- L'Internationale (De Geyter) on IMSLP, PD score — https://imslp.org/wiki/L'Internationale_(De_Geyter,_Pierre)
- The Sacred War / Lebedev-Kumach (1898-1949) — https://en.wikipedia.org/wiki/The_Sacred_War · https://en.wikipedia.org/wiki/Vasily_Lebedev-Kumach
- Vasily Agapkin (1884-1964) / Farewell of Slavianka — https://en.wikipedia.org/wiki/Vasily_Agapkin · https://en.wikipedia.org/wiki/Farewell_of_Slavianka
- Matvey Blanter (1903-1990) / Katyusha — https://en.wikipedia.org/wiki/Matvey_Blanter · https://en.wikipedia.org/wiki/Katyusha_(song)
- Lev Knipper (1898-1974) / Polyushko-pole — https://en.wikipedia.org/wiki/Lev_Knipper · https://en.wikipedia.org/wiki/Polyushko-pole
- Anatoly Novikov — https://en.wikipedia.org/wiki/Anatoly_Novikov
- Isaak Dunayevsky (1900-1955) — https://en.wikipedia.org/wiki/Isaak_Dunayevsky
- Ilya Shatrov (1879-1952) / On the Hills of Manchuria — https://en.wikipedia.org/wiki/Ilya_Shatrov · https://en.wikipedia.org/wiki/On_the_Hills_of_Manchuria
- Max Kyuss (1874-1942) / Amur Waves — https://en.wikipedia.org/wiki/Max_Kyuss · https://en.wikipedia.org/wiki/Amur_Waves
- Leonid Radin (1860-1900) — https://ru.wikipedia.org/wiki/Радин,_Леонид_Петрович
- Po dolinam i po vzgoriam — https://en.wikipedia.org/wiki/Po_dolinam_i_po_vzgoriam
- Shostakovich v. Twentieth Century-Fox Film Corp. — https://en.wikipedia.org/wiki/Shostakovich_v._Twentieth_Century-Fox_Film_Corp.
- IMSLP Prokofiev copyright threads — https://imslpforums.org/viewtopic.php?t=8894

Free-material sources:
- Musopen — https://musopen.org/
- Mutopia Project — https://www.mutopiaproject.org/
- Commons: Free media resources / Music — https://commons.wikimedia.org/wiki/Commons:Free_media_resources/Music
