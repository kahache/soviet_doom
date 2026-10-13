# Could we train an AI on thousands of levels and have it generate our maps?

Date: 2026-10-13. Author: PM. Dated snapshot, not a living document.
Russian mirror: `docs/ru/product/2026-10-13_ML-LEVEL-GENERATION.md` (D7).

CEO question, literally: *«Existe posibilidad de que te descargues miles de
niveles, entrenar un modelo de IA, y generar así los mapas? o es una idea muy
loca?»*

**Short answer: it is not a crazy idea — it is a real research area with
published results, and it has been tried on Doom specifically, twice, by the
same group. But what it produces is a plausible *picture of a floor plan*,
not a level a person can finish, and the rights situation around the training
corpus is worse for us than the texture problem we already refused to accept.
Recommendation at §6: don't train a generator; spend two days measuring a
*licensed* corpus we already have on disk (Freedoom, 68 maps, BSD) to
calibrate MAP01's numbers, and keep the geometry hand-authored.**

This document owns nothing that other documents own. Rights framework:
`docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md`. Our own licence:
D15 in `docs/PRD.md`. The reuse-permission precedent (Bloody Steel):
`docs/product/2026-10-09_0017_F0_pm-similar-mods.md`. What a good map means
here: `docs/levels/MAP01-zarya-7.md`.

---

## 1. What has actually been done

### 1.1 The paper

**"DOOM Level Generation using Generative Adversarial Networks"** — Edoardo
Giacomello, Pier Luca Lanzi, Daniele Loiacono, Politecnico di Milano
(Dipartimento di Elettronica, Informazione e Bioingegneria), arXiv
[1804.09154](https://arxiv.org/abs/1804.09154), April 2018; presented at IEEE
CIG 2018. Extended journal version: *An analysis of DOOM level generation
using Generative Adversarial Networks*, **Entertainment Computing** vol. 46,
May 2023
([ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1875952123000046)).
Follow-up: *Searching the Latent Space of a Generative Adversarial Network to
Generate DOOM Levels*, IEEE CIG 2019
([ACM DL](https://dl.acm.org/doi/10.1109/CIG.2019.8848011)), which searches
the trained generator's latent space with CMA-ES to hit numeric design
targets. Code: [edoardogiacomello/DoomGAN](https://github.com/edoardogiacomello/DoomGAN)
(MSc thesis repository) and a later reimplementation,
[AkashJam/DoomGAN](https://github.com/AkashJam/DoomGAN).

### 1.2 What they trained on

- Source: the **idgames archive**, the community level archive. The thesis
  repository states roughly **9,600 community levels were scraped** from
  doomworld.com plus the official retail levels.
- After filtering, the training set was **1,088 levels**: *"due to
  computational constraints, we selected only levels on one single floor and
  that could be represented with images of size not greater than 128x128
  pixels."*
- Each level was reduced to **six 128×128 images**: FloorMap (walkable area),
  WallMap, HeightMap, ThingsMap (object positions), TriggerMap (doors,
  switches), RoomMap — plus a set of extracted numeric features (176
  computed; 7 used to condition the second model: equivalent diameter, major
  and minor axis length, solidity, number of rooms/nodes, and two
  wall-distance statistics).
- Models: **WGAN-GP**, generator and discriminator of four layers
  (1024/512/256/128 filters), one unconditional, one conditioned on those 7
  features.

### 1.3 What came out — the part that is the actual answer

This is where the honesty has to be: the published result is **images**.

- The levels were evaluated with **image-similarity statistics**: entropy
  difference (δE), SSIM, "encoding error" (how far a generated pixel is from
  a meaningful value) and "corner error" (Harris corner detection as a proxy
  for structural complexity). There is **no systematic playability test, no
  completion test, and no human playtest reported** in the arXiv version. The
  authors say so themselves about evaluation in general: *"Evaluating the
  quality of the samples generated from a neural network is currently an open
  issue."*
- The strongest claim the authors make about play is a qualitative one —
  that most generated levels proved interesting to explore and play — and the
  stated failure mode is exactly the one that matters: *"the networks struggle
  to reproduce smaller details of the levels, probably due to generation
  noise."* In Doom, the small details **are** the level: a doorway, a switch,
  a step, a tag.
- The ThingsMap and WallMap are reported as the **noisier** outputs. Those
  two channels are "where the monsters and the weapons go" and "where the
  walls are".
- Conversion back to a `.wad` exists but is barely documented. The thesis
  repo says only: *"You can generate working WAD files directly from the
  network samples. Documentation is still in progress."* The reimplementation
  ships a node builder binary (`ZenNode.exe`), confirming that the pixel
  output has to be turned into real geometry and then have its BSP tree
  built. One secondary source states the 2023 journal pipeline used **BSP
  v5.2** as its last stage — **NOT VERIFIED**: the journal full text is
  paywalled (HTTP 403) and I could not read the pipeline section.
- The community read it the same way. A Doomworld thread is titled
  **"Neural nets sort of generate Doom maps but not really"**
  ([doomworld.com/forum/topic/100657](https://www.doomworld.com/forum/topic/100657-neural-nets-sort-of-generate-doom-maps-but-not-really/)),
  and the objection in that thread and in the paper's own announcement thread
  ([topic/100590](https://www.doomworld.com/forum/topic/100590-doom-level-generation-using-generative-adversarial-networks/))
  is that the networks produced 128×128
  images resembling a small picture of a layout, that the generated levels
  were not released for players to test, and that the evaluation measured
  geometric abstractions rather than whether a level was enjoyable or even
  finishable. **Partially NOT VERIFIED**: doomworld.com is behind a bot check
  I will not work around, so I am relying on search-engine summaries of those
  two threads, not on the posts read in full. The thread titles are verifiable
  and say most of it.

**So the distinction the CEO asked for, stated plainly: the published work
produces plausible images of floor plans. Turning one into a level that
GZDoom loads and a human can finish from start to exit was not demonstrated,
not measured, and not published as playable output.** A GAN of this kind has
no concept of "the exit is reachable" — reachability is a global, discrete
property, and the model is optimising local pixel statistics.

### 1.4 Two things that are *not* this, in case the CEO has seen the headlines

- **GameNGen** / *Diffusion Models Are Real-Time Game Engines*
  ([arXiv 2408.14837](https://arxiv.org/abs/2408.14837), Google, 2024) — a
  diffusion model that **predicts the next video frame** of Doom at 20 fps,
  trained on 70M frames of agent play. Spectacular, and irrelevant here: it
  generates *pictures of gameplay*, not map data. There is no WAD, no sector,
  nothing a mod can ship.
- **Non-ML procedural generators already solved the easy half**, 25 years
  ago: **SLIGE** (1998) and **OBLIGE**
  ([oblige.sourceforge.net](https://oblige.sourceforge.net/)) generate
  complete, playable, finishable Doom maps with tuned difficulty — OBLIGE v7
  by shape grammars. SLIGE's output was good enough that people passed it off
  as handmade ([DoomWiki](https://doomwiki.org/wiki/Random_Doom);
  [analysis](https://www.boristhebrave.com/2020/06/24/level-generation-in-slige/)).
  They work because a human encoded the rules of a Doom room explicitly —
  which is precisely the knowledge a GAN is supposed to save you from writing
  and precisely the knowledge our MAP01 design document already contains.

---

## 2. What it would take today — orders of magnitude

Estimates are labelled. Nothing here is a quote from a paper unless cited.

| Resource | What the published work used | What **we** have / would need | Verdict |
|---|---|---|---|
| Corpus, generic | 1,088 maps, filtered from ~9,600 scraped | downloadable, but see §3 | the blocker is legal, not technical |
| Corpus, **our style** | — | **1 map** (MAP01 v0) + a 68-map Freedoom base that looks nothing like a 1977 cosmodrome | fatal. A model trained on idgames generates *a Doom map*, never *a Zarya-7* |
| Representation | 6 × 128×128 images, one floor only | MAP01 is 3,264 × 2,048 units and has a −96 sump, a +96 catwalk and a cradle at +32: **multi-level by design**, i.e. outside the filter the paper applied | our map is in the class they excluded |
| Compute | WGAN-GP, 128×128×6, ~1k samples, 6 GB GPU mentioned | **estimate**: hours to ~2 days on one modern GPU; €20–200 rented. Our Mac is macOS 12 on Intel with no CUDA and a `.venv` holding pillow + numpy, so cloud rental is mandatory | the cheapest line in the table |
| Engineering: pixels → UDMF | undocumented | see the list below | **estimate: 2–6 person-weeks**, and it is the whole job |
| Engineering: making the output *finishable* | not attempted | hand repair of every generated map | unbounded |

### 2.1 The postprocessing nobody writes down

A 128×128 bitmap is not a map. To get from the six images to something
`tools/build.py` can pack and `qa-engineer` can sign off, someone has to
write and maintain:

1. **Denoise and threshold** six noisy greyscale channels into discrete
   decisions (walkable / wall / height class / thing / trigger).
2. **Trace contours** of the floor mask (marching squares) and **simplify**
   the polygons onto an 8- or 16-unit grid, or the map becomes thousands of
   1-pixel staircase sectors. One pixel is a large unit: the paper does not
   state the scale (**NOT VERIFIED**); if it is 32 map units, then a pixel is
   half a doorway and 128 px ≈ 4,096 units, in which case MAP01 would occupy
   about 102 × 64 pixels — our whole design lives inside ~6,500 pixels of
   decision space, and a single wrong pixel is a hole in a wall.
3. **Partition the polygons into closed, correctly wound sectors**, assign
   quantised floor/ceiling heights from the HeightMap, and derive which lines
   are one-sided (blocking) and which two-sided.
4. **Interpret the TriggerMap**: this is the hard part and no paper claims to
   solve it. A door is not a pixel; it is a sector plus a special
   (`Door_Raise` 12) plus a tag plus the special being on the correct side of
   both flanking lines — a fact we learned the hard way and wrote down in
   `docs/levels/MAP01-zarya-7.md` §9. A remote switch is only meaningful if
   its **tag matches a sector that exists and that the player can see the
   effect of**. Pixel maps do not encode pairings.
5. **Interpret the ThingsMap** into DoomEdNums, per-skill flags, and a
   resource budget. The noisiest channel feeding the most consequential data.
6. **Assign textures.** We have **12 approved names**. A generated map arrives
   untextured and inherits none of our art direction, so §6 of the MAP01 doc
   (zone-by-zone walls/floors/ceilings/light) is hand work either way.
7. **Validate.** We already own this part: `tests/test_udmf.py` (190 tests)
   checks closed clockwise sectors, no duplicate vertices or linedefs,
   reachability from the player start, a path *back* from every sector, gate
   order, and ≥56 units of door clearance. Those checks would reject almost
   every raw generated map — which is the point, and also the cost.
8. **Nodes.** For the 1993 binary format a node builder is mandatory (hence
   `ZenNode.exe` in the reimplementation). For us this step is free: our PK3
   ships `TEXTMAP` + `ENDMAP` with no node lumps and GZDoom builds them at
   load — **verified by our own v0 build walking in the engine**
   (`docs/levels/MAP01-zarya-7.md` §14).

Against that, the comparison that decides it: `level-designer` built the
**complete 44-sector, 179-linedef v0 floor plan of MAP01 in one working
session**, from a written design, with tests. The ML route's *cheapest* stage
costs more than the thing it would replace.

---

## 3. The rights problem, which here is the serious one

This project has already paid the price of taking licensing seriously: D4
forbids assets from commercial games; `SDPOSTR1` was discarded and the Lenin
poster became a separate commission because 1950s–80s Soviet poster art is
still protected; and we declined to reuse anything from **Bloody Steel**
because its idgames text file says other authors may **not** use its contents
as a base for modification or reuse
(`docs/product/2026-10-09_0017_F0_pm-similar-mods.md`).

A corpus of idgames WADs is the same material, in bulk.

### 3.1 The corpus is not public domain, and it is explicitly conditioned

Every /idgames upload carries a text file derived from the standard Doom file
template, whose "Copyright / Permissions" section makes the author state
whether others **"(MAY/may NOT) use the contents of this file as a base for
modification or reuse"**
([DoomWiki, Doom file template](https://doomwiki.org/wiki/Doom_file_template);
[/idgames FAQ](https://doomworld.com/forum/topic/31922-idgames-faq-uploader-read-this)).
A large share says *may NOT*. Since 2019 the archive's text generator also
offers Creative Commons licences
([Doomworld thread](https://www.doomworld.com/forum/topic/90566-idgames-database-txt-generator-now-uses-creative-commons-licensing/)),
which helps and also hurts: a **CC BY-SA** map is incompatible with our
**CC BY-NC-SA** output, and a **ND** map is excluded outright.

So a scraped corpus is a mixture of: all-rights-reserved maps with an
explicit no-derivatives wish, CC maps under four or five mutually
incompatible terms, and a minority of genuinely permissive ones. Nobody who
scrapes 9,600 WADs knows which is which per file.

### 3.2 Is training itself lawful? Honestly: unsettled, and not comfortable

- **United States.** Training can be fair use — *Bartz v. Anthropic* (N.D.
  Cal. 2025) found training on **lawfully acquired** books transformative
  while refusing to bless a library of pirated copies; the case then settled
  for **$1.5 bn**. *Kadrey v. Meta* went Meta's way on the training question
  while torrent-seeding claims survived. But in September 2026 the **Third
  Circuit affirmed** against Ross Intelligence in *Thomson Reuters v. Ross* —
  the first appellate test, decided against the AI developer, with
  commentators noting the panel expressly left generative AI unresolved
  ([Ballard Spahr](https://www.ballardspahr.com/insights/alerts-and-articles/2026/10/third-circuit-addresses-fair-use-in-ai-training-but-leaves-generative-ai-questions-unresolved);
  [Jackson Walker](https://www.jw.com/news/insights-ai-copyright-fair-use-case/);
  [Ohio State University Libraries, 2026 update](https://library.osu.edu/site/copyright/2026/03/20/fair-use-and-artificial-intelligence-2026-update/)).
  The direction of travel is *narrower*, not broader.
- **European Union**, which is where we are. Art. 3 DSM (Dir. 2019/790) is a
  research-organisation exception — we are not one. Art. 4 allows text and
  data mining for any purpose, commercial included, **but only on lawfully
  accessed content and only where the rightsholder has not reserved the right
  in machine-readable form, "including … terms and conditions of a website or
  a service"**
  ([Reed Smith](https://www.reedsmith.com/articles/entertainment-media-guide-to-ai-three-years-on/text-data-mining-in-the-eu/);
  [CC statement on Art. 4](https://creativecommons.org/wp-content/uploads/2021/12/CC-Statement-on-the-TDM-Exception-Art-4-DSM-Final.pdf)).
  A text file saying *"may NOT use the contents of this file as a base for
  modification or reuse"* is at minimum an expressed reservation; whether a
  `.txt` beside a `.wad` is "machine-readable" for Art. 4(3) is exactly the
  kind of question that gets litigated. **NOT VERIFIED**: the precise Spanish
  transposition articles (Spain implemented the DSM Directive by
  Real Decreto-ley 24/2021) — I did not confirm the article numbers, and a
  question referred to the CJEU on LLM training is reported as pending.
- **Our conclusion does not depend on which way that goes**, because of §3.3.

### 3.3 The output is the real exposure, and the licence we promised is the trap

1. **Memorisation.** 1,088 samples is a *small* dataset. A generator trained
   on it can reproduce recognisable layout fragments of individual maps, and
   we would have no procedure to prove that a given room is not a copy of
   someone's room. "Statistically derived" is not a defence recognised
   anywhere; substantial similarity is judged on the output.
2. **We cannot license what we do not own.** D15 releases our assets, maps
   included, under **CC BY-NC-SA 4.0**. Granting that licence is a
   representation that we hold the rights. For a map whose geometry came out
   of a model trained on 1,088 third-party maps with incompatible terms, we
   cannot make that representation honestly. Attribution alone would be
   impossible: BY requires naming the authors; there would be a thousand.
3. **Community norms we already chose to honour.** We respected BigMemka's
   "may NOT" for one mod. Feeding the same file to a trainer and shipping the
   result is the same act at scale, and the Doom community — which is our
   entire audience — would read it that way.
4. **Project risk already on the books.** `docs/PRD.md` §7 names asset
   licensing as the risk that "kills a free mod". We also already carry
   distribution friction from D12 (swastikas and US flags). Handing an
   objector a second, cleaner reason to complain is a bad trade for a mod that
   earns no money.

**Verdict on §3: there is no reading under which training on an idgames
corpus and shipping the result under CC BY-NC-SA meets the standard this
project applies to a single wall texture.** If we would not take one
texture from Bloody Steel, we cannot take the shape of a thousand maps.

---

## 4. The alternative that probably does work: mine metrics, not geometry

Change what we extract. Not pixels — **numbers**. Facts and measurements are
not the protected expression; we redistribute nothing, we generate nothing,
and we keep every line of geometry hand-authored. (Caveat, **NOT VERIFIED**:
the EU *sui generis* database right can attach to a database as such, so even
a measurement exercise should extract modestly and publish only aggregates,
never a reconstructable copy of anyone's map.)

### 4.1 And there is a corpus we are already entitled to

**Freedoom is under a modified BSD licence** — share, modify, reuse parts —
and it is **Phase 1 (36 maps) + Phase 2 (32 maps) = 68 maps**
([DoomWiki](https://doomwiki.org/wiki/Freedoom);
[Libregamewiki](https://libregamewiki.org/Freedoom)). `iwads/freedoom2.wad`
is already on disk because D2 makes it our base IWAD. For calibration
purposes that corpus is: legally clean, locally available, built by
competent authors to classic Doom pacing, and large enough for percentiles.
It is also the only corpus whose maps we could legitimately use **as a base**
if we ever wanted to.

That single fact reframes the CEO's question: the corpus problem is not "how
do we get thousands of levels", it is "we already have the dozens we are
allowed to use, and dozens is what a calibration needs".

### 4.2 What to measure, and against what MAP01 already measures

MAP01 is already quantified (`docs/levels/MAP01-zarya-7.md` §3, §7, §8, §14),
which is what makes this worth doing at all — there is something to compare.

| Metric | MAP01 today | Why the comparison would change a decision |
|---|---|---|
| Map extent | 3,264 × 2,048 units | the hangar is **1,536 × 1,536 × 320 high**. The craft reference puts a "large room" at 1,024–1,536 units ([Level Design Book, Doom metrics](https://book.leveldesignbook.com/process/blockout/metrics/doom)), so the hangar sits at the **top of the sanctioned band**: it is not oversized, it is under-furnished. That is CEO open question #1 answered with a number, today, with no corpus at all. |
| Sectors / linedefs | 44 / 179 (v0, before v2 detail) | tells us whether v2's detail pass is normal or baroque for an opener |
| Monsters by skill | 21 / 33 / 46 | the one number most worth checking against openers rather than against mid-episode maps |
| Monsters per minute of first run | ≈ 5 (33 over 5–8 min) | pacing, which is what the CEO actually feels |
| Secrets | 3 | 2–4 is the classic opener range; confirms, cheaply |
| Longest stretch with no fight | ≈ 1,900 units (dorm → service corridor) | CEO open question #2 ("a base or a lobby?") becomes measurable |
| Ammo placed ÷ ammo needed | ≥ 1.35 on skill 4, enforced by G3-8 | the threshold is currently **our invention**. A measured distribution would replace a guess with a calibrated constant — the single highest-value number in this table |
| Light values | 96–192, ±16 steps | whether our floor of 96 is brighter than the idiom expects |

Craft metrics we should simply adopt, free, no study needed, from the same
reference: corridors minimum 128 × 128; rooms small 256–512 / medium
512–1,024 / large 1,024–1,536; steps 16 high × 64 deep (or 8 × 32); maximum
step 24 units for monsters; player 33 × 58; melee inside 64 units; hitscan
effective out to ~2,048. **MAP01 already satisfies every one of these** —
heights are multiples of 16, no step over 24, door recesses 128 × 128 — so
the honest finding is that our level design is already calibrated and the
marginal value of a corpus study is *moderate, not transformative*.

### 4.3 Is it worth it? Bounded answer

**Yes, once, small.** A one- to two-day job for `qa-engineer` or
`level-designer`: a ~200-line reader over Freedoom's maps computing the eight
metrics above, output as one table plus percentiles, no WAD content copied,
no asset redistributed. Its deliverable is not a map — it is **three or four
constants in our test suite that stop being guesses** (the 1.35 ammo factor,
the monster-count band for an opener, the acceptable no-fight stretch, the
light floor). That is a real gain, it strengthens G3, and it carries zero
legal and zero artistic risk.

**Not worth it**: scaling it to thousands of amateur maps. The median idgames
map is of unknown quality; averaging it would pull us toward the mediocre
middle, and the fat tail would need the §3 analysis all over again.

---

## 5. The thing that actually limits our maps, and whether a model can express it

The CEO's question assumes the bottleneck is *producing plausible layouts*.
It is not. Read MAP01's design document and count what is load-bearing:

- **The gate that teaches itself.** The player enters the hangar and sees D4
  shut, framed by the red stripe, with a dead indicator. SW-A in the fuel bay
  opens it *and* lights the control-booth window at the far end, so the
  player gains a lit destination he had not noticed. The design rule is
  "the locked thing is always seen before the switch that opens it, and the
  switch's effect is visible from where it is thrown."
- **The red stripe as a language.** `SDCONC2` means *route*; `SDFLR1` yellow
  means *hangar traffic*. Both are taught in the first 90 seconds and **never
  lie**. A single inconsistent use destroys the whole mechanism.
- **The curve.** Light rises toward the hangar and falls toward the exit
  because the fiction does; intensity is an eight-beat curve ending on the
  room the player already knows, now full.
- **Negative design.** No door ever closes behind the player; no lift on the
  critical path; every switch repeatable; no drop over 24 units without a
  return. These are *refusals*, and refusals are invisible in training data.

Can a generative model express any of that? Honestly:

- **Not in this representation, not even in principle.** A GAN over
  FloorMap/WallMap/HeightMap/ThingsMap/TriggerMap optimises local pixel
  statistics. Design intent here is *relational* (this switch's effect must be
  visible from this spot), *sequential* (this is taught before it is used),
  *semantic* (red means route) and *global* (pressure rises then falls).
  None of those quantities exists in the representation, so no amount of
  training data can make the model wrong about them — it simply cannot say
  them.
- **The conditional model's levers are shape statistics**, not intent:
  diameter, solidity, number of rooms, wall-distance skewness. The 2019
  latent-space search can hit those targets accurately and novelly, which is
  genuinely impressive — and the targets are still "how round and how
  branchy", never "the gate must teach itself".
- **The reductio.** You could, in principle, build a generate-and-test loop
  whose objective function encodes our intent: a solver that enforces
  visibility, teaching order, monotone pressure, our texture grammar. But
  **writing that objective *is* the design work.** We already wrote it — in
  prose, in `docs/levels/MAP01-zarya-7.md`, and partly in executable form in
  `tests/test_udmf.py` (reachability, return paths, gate ordering, door
  clearance). The honest version of the CEO's idea is therefore not
  "learn maps from strangers"; it is "**keep turning our own design rules
  into constraints our own generator must satisfy**" — which is what
  `GridMap` plus 190 tests already is, and which is also, not
  coincidentally, how SLIGE and OBLIGE got playable maps out of a 1998
  machine.
- One caveat in fairness: ML is genuinely useful for the *statistical* half
  of level design — autocompleting detail, suggesting variants of a room we
  already defined, stress-testing with learned agents. None of those needs a
  scraped corpus, and none of them is on our critical path before G3.

---

## 6. Recommendation

**Do not train a generative model on a downloaded WAD corpus: the published
state of the art yields plausible pictures of floor plans rather than
finishable levels, the postprocessing to make one load and be completable
costs more than hand-building MAP01 did, and we could not honestly license
the result under our own CC BY-NC-SA while we are refusing to reuse a single
texture whose author wrote "may not be used as a base".** Instead, spend one
to two days mining **metrics** from the 68 BSD-licensed Freedoom maps we
already have on disk, and use them to replace three or four invented
constants in the G3 criteria with calibrated ones — the only part of this
idea that improves the game, and the part that risks nothing.

If the CEO wants the ambitious version on the record anyway, the right place
for it is an ICEBOX entry worded as *"constraint-based generation from our own
design rules, using our own vocabulary"* — not learned generation from other
people's maps — and not before G3 is signed.

---

## 7. Sources

Research
- https://arxiv.org/abs/1804.09154 — Giacomello, Lanzi, Loiacono, *DOOM Level Generation using GANs* (2018); full text read via https://ar5iv.labs.arxiv.org/html/1804.09154
- https://www.sciencedirect.com/science/article/pii/S1875952123000046 — journal version, *Entertainment Computing* 46 (2023). **Paywalled (403): abstract-level only**
- https://dl.acm.org/doi/10.1109/CIG.2019.8848011 — latent-space search follow-up (CIG 2019)
- https://github.com/edoardogiacomello/DoomGAN — thesis code; https://github.com/AkashJam/DoomGAN — reimplementation (ships `ZenNode.exe`)
- https://arxiv.org/abs/2408.14837 — *Diffusion Models Are Real-Time Game Engines* (GameNGen); https://gamengen.github.io/

Community reception (**read via search summaries only — doomworld.com is behind a bot check**)
- https://www.doomworld.com/forum/topic/100657-neural-nets-sort-of-generate-doom-maps-but-not-really/
- https://www.doomworld.com/forum/topic/100590-doom-level-generation-using-generative-adversarial-networks/

Non-ML procedural generation
- https://oblige.sourceforge.net/ · https://doomwiki.org/wiki/Random_Doom · https://www.boristhebrave.com/2020/06/24/level-generation-in-slige/

Rights
- https://doomwiki.org/wiki/Doom_file_template — the "may / may NOT use as a base" clause
- https://doomworld.com/forum/topic/31922-idgames-faq-uploader-read-this — /idgames upload requirements
- https://www.doomworld.com/forum/topic/90566-idgames-database-txt-generator-now-uses-creative-commons-licensing/
- https://www.reedsmith.com/articles/entertainment-media-guide-to-ai-three-years-on/text-data-mining-in-the-eu/ — EU Art. 3/4 TDM
- https://creativecommons.org/wp-content/uploads/2021/12/CC-Statement-on-the-TDM-Exception-Art-4-DSM-Final.pdf
- https://www.ballardspahr.com/insights/alerts-and-articles/2026/10/third-circuit-addresses-fair-use-in-ai-training-but-leaves-generative-ai-questions-unresolved
- https://www.jw.com/news/insights-ai-copyright-fair-use-case/ · https://library.osu.edu/site/copyright/2026/03/20/fair-use-and-artificial-intelligence-2026-update/
- https://en.wikipedia.org/wiki/Artificial_intelligence_and_copyright

Metrics and corpus
- https://book.leveldesignbook.com/process/blockout/metrics/doom — Doom craft metrics
- https://doomwiki.org/wiki/Freedoom · https://libregamewiki.org/Freedoom — modified BSD licence, 36 + 32 maps

### Marked NOT VERIFIED in this document

1. That the 2023 journal pipeline's final stage is **BSP v5.2** (paywalled).
2. The **map-units-per-pixel** scale of the level images; the 32-units figure in §2.1 is my inference, flagged as such.
3. The Doomworld threads' contents, read only through search summaries.
4. The exact **Spanish transposition articles** of DSM Arts. 3–4, and the status of the CJEU reference on LLM training.
5. Whether the /idgames archive qualifies as a protected **database** for EU *sui generis* purposes.
6. All figures labelled **estimate** in §2 (compute cost, person-weeks).
