# Music rights — what Soviet Doom can legally use as a soundtrack

Living document. Owner: sound-designer. Russian mirror: `docs/ru/sound/MUSIC-RIGHTS.md` (D7).
Created: 2026-10-12 (F2, research brought forward).
Revised 2026-10-13: the CEO asked for **downloaded** MIDIs rather than generated
ones, which exposes a right the first version treated as a footnote — the
**sequencing** (§1.2). Twelve candidate files have now been licence-audited and
fetched to `work/audio/candidates/`; the audit is §4.4.
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
| **Вы жертвою пали** · *Vy zhertvoyu pali* · You Fell Victim (revolutionary funeral march) | traditional, 19th c.; text Антон Архангельский / Anton **Arkhangelsky** (1850s-60s) | traditional | 1870s-80s | **RU ✅** / **US ✅** | ✅ both (**exact authorship NOT VERIFIED**, but pre-1900 in any attribution) | ✅ **FREE.** The Soviet state funeral music — ideal for a defeat/aftermath cue |
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
| **Михаил Глинка** / Mikhail **Glinka** | 1804-1857 | ✅ | ✅ | **Патриотическая песня / "Patriotic Song"** — the national anthem of Russia 1990-2000, and completely free. *Ruslan and Lyudmila* overture (frantic, excellent for a fight) |
| **Пётр Чайковский** / Pyotr **Tchaikovsky** | 1840-1893 | ✅ | ✅ | **Marche slave op. 31 (1876)** — the single best candidate for a main theme. Symphony No. 4 finale; *1812 Overture* (caution: it quotes the Tsarist anthem *God Save the Tsar*, which is lore-wrong for 1977) |
| **Александр Бородин** / Alexander **Borodin** | 1833-1887 | ✅ | ✅ | *Polovtsian Dances*, *In the Steppes of Central Asia*, *Prince Igor* overture. Completions by Rimsky-Korsakov (d. 1908) and Glazunov (d. 1936, RU free 2007, US pub. 1888) are also free |
| **Модест Мусоргский** / Modest **Mussorgsky** | 1839-1881 | ✅ | ✅ | **Night on Bald Mountain** (Rimsky-Korsakov version, 1886) — the obvious demon/alien cue. *Pictures at an Exhibition*: "Gnomus", "Catacombae", "The Hut on Fowl's Legs", "The Great Gate of Kiev". **Use the piano original**; Ravel's orchestration has its own term (**NOT VERIFIED** for Russia) |
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

### 4.4 Licence audit of the twelve files downloaded on 2026-10-13

All twelve live in `work/audio/candidates/`. **Nothing is in `assets/` and
nothing is in the PK3.** Each row's licence was read from the file's own page,
not from a search result: Commons files from their raw wikitext
(`?action=raw`), Mutopia files from the per-piece record. Musical verdicts are
in `docs/sound/SOUNDTRACK.md`; this table is only about rights.

| File in `work/audio/candidates/` | Work | Composition | Sequencer / typesetter | Licence on the sequencing | D15 |
|---|---|---|---|---|---|
| `WM_Internationale_orch2.mid` | Интернационал, orchestral | De Geyter 1888, PD RU+US | **Jerry Engelbach**, USA, 2003 | `{{Attribution\|Jerry Engelbach}}` + VRT ticket 2008011810001789 | ✅ attribute Engelbach |
| `WM_Internationale_piano_Bb.mid` | Интернационал, piano in B♭ | same | **Jerry Engelbach**, USA, 2001 | same | ✅ attribute Engelbach |
| `WM_Ej_uchnem.mid` | Эй, ухнем — Balakirev's setting, pub. 1866 | PD RU+US | **Peter Gerloff** (Commons: *Rabanus Flavus*), 2021 | `{{self\|Cc-zero}}` — **CC0** | ✅ no obligation |
| `WM_Kolokolchik.mid` | Колокольчик, Russian traditional | PD RU+US | **Peter Gerloff**, 2019 | `{{self\|Cc-zero}}` — **CC0** | ✅ no obligation |
| `MU_Mussorgsky_BaldMountain.mid` | Ночь на лысой горе, Chernov's piano transcription | Mussorgsky d. 1881, PD; transcriber Konstantin Chernov d. 1944 → RU PD 2015, **+war 2019 — NOT VERIFIED which applies, both are past** | typeset **Robert Clausecker**, Mutopia 2013 | **CC BY 3.0** | ✅ attribute Clausecker + Mutopia |
| `MU_Tchaikovsky_Dumka_op59.mid` | Думка op. 59 (1886) | Tchaikovsky d. 1893, PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_Tchaikovsky_Seasons_August.mid` | Времена года: Август (1876) | PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_Tchaikovsky_WoodenSoldiers.mid` | Марш деревянных солдатиков op. 39 | PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_Scriabin_Etude_op2n1.mid` | Этюд op. 2 № 1 (1887) | Scriabin d. 1915, PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_Scriabin_Prelude_op11n1.mid` | Прелюдия op. 11 № 1 | PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_Scriabin_Prelude_op59n2.mid` | Прелюдия op. 59 № 2 (1910) | PD RU+US | Mutopia | **Public Domain** | ✅ |
| `MU_RimskyKorsakov_FugueBACH.mid` | Fugue sur le nom de BACH | Rimsky-Korsakov d. 1908, PD RU+US | Mutopia | **Public Domain** | ✅ |

**Rejected at the licence gate, not downloaded:**

| File / source | Why |
|---|---|
| `The-Internationale.mid` (Commons, user J2772011, 2023) | `{{self\|cc-by-sa-4.0}}` — ShareAlike, §1.3 |
| `Sua.mid` (Commons, USSR anthem, 2004) | **GFDL** — copyleft, §1.3; and the anthem's US status is unresolved, §3.1 |
| `Гимн России1.mid`, `CccpDisco.mid`, `RussischeHymneVer1.mid`, `Ua-ssr.mid` (Commons) | anthem material, same two problems |
| Mutopia Rachmaninoff, all 10 preludes | **CC BY-SA 4.0** |
| Mutopia Rimsky-Korsakov op. 11 (4 pieces) | **CC BY-SA 3.0** |
| Mutopia Scriabin op. 16 (5 préludes) | **CC BY-SA 2.5** |
| Mutopia Mussorgsky, *Pictures at an Exhibition* | **CC BY-SA 4.0** — the one we most wanted from that catalogue |
| `archive.org/details/ussr-1` "USSR Anthem (MIDI)" | **no licence declared at all** |
| BitMidi, MIDIWorld, Midis101, hamienet, MidiShow, rusmidi.com, geocities mirrors | no per-file licence, no named sequencer — §1.2 |
| MuseScore.com scores of *Смело, товарищи, в ногу* and others | licence not machine-verifiable (HTTP 403 to automated access, 2026-10-13); and an uploader-declared CC0 on a sequencing whose provenance we cannot read is not a verifiable licence |

#### 4.4.1 A gap in this audit, stated rather than hidden

The **per-piece Mutopia URL was recorded only for *Night on Bald Mountain***
(`piece-info.cgi?id=1892`). For the other seven Mutopia files the licence was
read from the per-piece record on 2026-10-13, but the record's address was not
written down, and the files themselves carry no provenance beyond
`creator: GNU LilyPond <version>` (verified 2026-10-13 by extracting every
text meta event: no composer, no URL, no licence string in any of them).

All seven are **Public Domain**, so no attribution duty is at risk — but a
public-domain claim whose page we cannot point at is a claim resting on one
agent's memory, which this project does not accept as a source. **Action,
before any of those seven is packed: re-verify each piece record and write its
URL into the table above.** The file that carries a real attribution
obligation, Bald Mountain, is the one that is fully sourced.

#### 4.4.2 Files we derived from the downloads

Our mechanical repairs (`tools/audio/midi_edit.py`; what and why in
`SOUNDTRACK.md` §5) create **derivative sequencings**. Every accepted licence
permits that — CC0 and PD outright, `{{Attribution}}` and CC BY 3.0 subject to
credit — and **the duty to credit survives the edit**:

| Our file | Derived from | Edit | Licence position |
|---|---|---|---|
| `work/audio/D_SDINTL.mid` | `WM_Internationale_orch2.mid` | `--trim-head`: 2 863 ticks (1.99 s) of leading silence removed. No pitch, duration, tempo or instrument changed | melody `{{PD-Internationale}}`; sequencing still `{{Attribution\|Jerry Engelbach}}` — **shipping this obliges us to credit Jerry Engelbach**. Our edit adds nothing we would license separately |
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

---


## 5. Recommendations

### (a) Recommended, with the clean route for each

| Priority | Work | Route | Where it goes |
|---|---|---|---|
| 1 | **Интернационал / The Internationale** | **downloaded, 2026-10-13**: Engelbach's orchestral MIDI from Commons, attribution-only (§4.4), repaired by us as `work/audio/D_SDINTL.mid` (§4.4.2). Sequencing from the IMSLP score is **not** necessary — it stays as the fallback only if the CEO dislikes Engelbach's orchestration itself | title screen (CEO's choice, 2026-10-13), finale |
| 2 | **Tchaikovsky, Marche slave** | no free MIDI exists. Either IMSLP's CC BY 4.0 synthesised **MP3** (§4.4), or we sequence it from the PD score | main theme / MAP01 |
| 3 | **Mussorgsky, Night on Bald Mountain** | CC0/PD recording | alien-infested areas |
| 4 | **Scriabin** (Sonata No. 9, *Prometheus*) | CC0/PD recording | dread ambience, Fourth Reich zones |
| 5 | **Смело, товарищи, в ногу** | sequence ourselves — free words *and* music in both countries | Soviet-held areas, diegetic |
| 6 | **Амурские волны (Kyuss, 1909)** | sequence ourselves | diegetic radio at the cosmodrome, a quiet moment |
| 7 | **Вы жертвою пали** | sequence ourselves | death / aftermath / ending |
| 8 | **Glinka, Патриотическая песня** | sequence ourselves | zero-risk substitute for the USSR anthem |
| 9 | **USSR anthem melody (Alexandrov)** | **instrumental only, sequenced by us, no lyrics, no Soviet recording** | title screen — *pending the CEO's call on the US risk* |
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

### (c) The standing warning

> **A public-domain composition does not imply a public-domain recording.** The three
> rights expire independently. For every work in this document the default assumption
> is: *composition may be free, the recording you found is not.* The only recordings
> we may ship are (i) explicitly PD/CC0/CC BY recordings whose underlying composition
> is also free in both Russia and the US, and (ii) recordings and sequences we make
> ourselves.

---

## 6. What the engine side will need from me

Declared here so `mod-engineer` and `level-designer` can plan; no files exist yet.

- **Formats**: GZDoom plays OGG, MP3, FLAC, MIDI and MOD/XM/IT. We use **OGG Vorbis**
  for recordings and **MIDI/XM** for anything we sequence, to keep the PK3 small.
- **`MAPINFO`** per map: `music = "D_SDM01"` style lump names, `SD` prefix per D1.
- **`SNDINFO`**: music lumps are *not* declared in SNDINFO (that is for sound effects
  and `$musicalias`); the MAPINFO `music` key and `$musicalias` entries are the
  interface.
- **Licence register**: every music lump gets a row in `docs/art/LICENSES.md` (or a
  **`LICENSES.md` of its own under `docs/sound/`**, which does not exist yet,
  if the CEO prefers a split) with origin, licence,
  and a link back to the row in this table.

---

## 7. Decisions needed from the CEO

> **The live list of music decisions is `docs/sound/SOUNDTRACK.md` §8**, which
> owns "what plays where" and was closed on 2026-10-13. What follows is only
> the part that is a *rights* question, and point 0 below is the same decision
> as SOUNDTRACK §8.0 seen from the licence side. Point 1 is superseded in
> practice; points 2-4 are still open.

0. **Attribution.** Two of the twelve candidates (§4.4) are attribution-only,
   not public domain: shipping Engelbach's Internationale obliges us to credit
   **Jerry Engelbach** wherever we credit anyone, and Mutopia's *Night on Bald
   Mountain* obliges us to credit **Robert Clausecker / Mutopia Project**.
   That is a line in the credits and a row in the licence register, nothing
   more, but it is a real obligation and the CEO should know we are taking it
   on. **Recommendation: accept** — the alternative is to use only the
   public-domain files, which are all solo-piano score previews.
1. **The USSR anthem.** Instrumental, self-sequenced, lyrics never used — accept the
   residual US risk (finding 3.1.2), or take Glinka's *Patriotic Song* instead and
   have zero risk? **This blocks the title-screen music.** *Superseded in
   practice*: the CEO chose the Internationale for the title on 2026-10-13, so
   this is now only about whether the anthem appears anywhere at all.
2. **Russia-free / US-blocked works**, principally *Священная война*. Our distribution
   will in practice be US-hosted. Do we exclude that whole category, or accept it for
   a free non-commercial mod? **My recommendation: exclude.** The dramatic value is
   real, but a takedown on a free mod costs more than the cue is worth, and the risk
   is concentrated in exactly the most recognisable pieces.
3. **Scope of the soundtrack.** Confirm that the bulk of in-level music will be
   **original composition in the period idiom**, with the historical pieces reserved
   for title, intermission and diegetic radio. That is the cheapest and safest plan
   and it is also, I think, the better-sounding one.

4. **Orchestration labour.** Every free MIDI of the Russian classics is a
   solo-piano score preview (§4.2). Making one usable means we assign the
   instruments — which is the work the CEO wanted to avoid by downloading.
   The choice is: ship piano, pay the orchestration labour, or accept IMSLP's
   CC BY 4.0 **MP3** renders and a larger PK3. **My recommendation: pay the
   orchestration labour on one piece only**, and keep the rest for diegetic
   use where piano is plausible.

Twelve files have been downloaded to `work/audio/candidates/` (§4.4), ~204 KB
in total. **Nothing is in `assets/` and nothing is in the PK3.**

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
- Mutopia browse by composer (licence per piece) — https://www.mutopiaproject.org/browse.html
- Mutopia licence policy — https://www.mutopiaproject.org/legal.html
- IMSLP, *Slavonic March* op. 31, synthesised performances CC BY 4.0 (MP3, not MIDI) — https://imslp.org/wiki/Slavonic_March,_Op.31_(Tchaikovsky,_Pyotr)
- IMSLP, *L'Internationale* (De Geyter) — https://imslp.org/wiki/L'Internationale_(De_Geyter,_Pierre)
- archive.org, "USSR Anthem (MIDI)", **no licence declared** — https://archive.org/details/ussr-1

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
