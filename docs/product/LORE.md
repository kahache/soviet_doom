# Soviet Doom — Lore v1

Status: **RATIFIED by the CEO on 2026-10-09** (D8–D14), names included.
Living document. Owner: PM. Russian mirror: `docs/ru/product/LORE.md`.

## Premise

The 1970s. The Soviet Union is invaded by two alien factions that should
hate each other and do not: the remnants of the Reich and the forces of the
Stars and Stripes, both turned into something no longer human. They have
allied because they want the same thing: **to defend capital**. Soviet
paraphernalia everywhere: Lenin and Stalin posters, slogans, red stars.
Period weapons. Serious tone; humour, if any, comes later and only on the
posters.

## Logline

> 1977, the 60th anniversary of October. While the
> country prepares the parade, two objects fall in the Urals. One carries an
> eagle, the other a star-spangled banner, and the things that crawl out of
> them march together. A Spetsnaz sergeant who arrived in this country as a
> refugee child from Barcelona is the only thing standing between them and
> Moscow.

## Protagonist (D10)

- A **child of the Spanish Civil War**: evacuated from Barcelona to the USSR
  in 1938 at the age of seven, raised in a children's home in Leningrad,
  career soldier, now a **Spetsnaz sergeant** guarding a secret cosmodrome.
- Name (D14): **Sergeant Ramon Vilanova**, in Russian **Рамон Виланова**. Born Barcelona 1931. Silent like Doomguy; his personality is in
  what he carries: a worn Lenin portrait, a Catalan ribbon under the uniform.
- He speaks nothing on screen. The posters and the LANGUAGE strings speak.

## The invaders (D9): two allied factions

| Faction | Name (D14) | Look | Role in bestiary |
|---|---|---|---|
| Nazi aliens | **Fourth Reich** | grey-green flesh, SS helmets, swastikas on armbands and banners (D12) | infantry, hounds, armoured brutes |
| Yankee aliens | **Liberty Legion** | chrome and pink flesh, M1 helmets, US flags on shoulders and banners (D12) | ranged units, floating heads, officers |

They share supply lines, bases and the final portal. In the maps both flags
hang side by side over Soviet buildings they have taken. Their alliance is
explained in intermission text and posters: "they fight for profit, we fight
for everyone".

## Tone (D11)

Serious. Brutal and direct like Doom. No parody. Posters may carry humour in
a later phase, decided by the CEO.

## Episode structure (D13)

| Map | Place | Narrative function | Texture set |
|---|---|---|---|
| MAP01 | **Zarya-7 cosmodrome**, barracks and hangar | weapon tutorial; the invasion has just begun | Soviet base: concrete, green steel, propaganda |
| MAP02 | Metro-bunker tunnels | first key, first heavy hybrids | metro: tiles, red marble, mosaics |
| MAP03 | Tractor factory (actually tanks), «Танкоград» / Tankograd (D63) | episode climax: the portal | industry: brick, rust, chains |

v1 shipped MAP01 only (D5); D60 grew the campaign to all three, and since D62
the map lumps carry these numbers (the metro was built as MAP03 and the
factory as MAP04 while MAP02 was the practice range, which is now the lump
`RANGE`, outside the campaign).

### Episode 2, «The Road to Moscow» / «Дорога на Москву» / «El camí de Moscou» (D104, P4)

The invaders who got through before Tankograd's portal went out march west.
The sergeant follows them along the railway, across the Volga and into the
capital. A second episode on the New Game screen, between the first and the
practice range; it starts on MAP04.

| Map | Place | Narrative function | Leaves by |
|---|---|---|---|
| MAP04 | **Trans-Siberian** («Транссиб»): the marshalling yard at Sverdlovsk, the armoured train, the signal box, the locomotive roundhouse | the road west begins | the armoured train, west, to the Volga |
| MAP05 | **Volga Dam** («Волжская ГЭС»): the hydroelectric dam at Zhiguli, the turbine hall, the spillway, the control room | the turbines that light half the country are taken back | over the crest of the dam; the last metro train into Moscow |
| MAP06 | **Red Square** («Красная площадь»): out of the metro at Ploshchad Revolyutsii, the GUM galleries, Red Square, the gate in the Kremlin wall | episode climax: the boss at the Kremlin gate | the end of the episode |

The ending: the Kremlin holds, but not all the invaders came through
Tankograd; their main portal is still open somewhere (the hook for an
episode 3). TO BE CONTINUED. The texts are in `LANGUAGE`
(`SD_MAP04_EXIT_TEXT`, `SD_MAP05_EXIT_TEXT`, `SD_END03_TEXT`); the flow is
`docs/engine/MOD-SPEC.md` §4.6. Texture sets and music are P4's work; the
maps play approved pieces provisionally (MOD-SPEC §4.5).

### Episode 3, «The Portal» / «Портал» / «El portal» (D112, P4)

Moscow holds, but the invaders' main portal is still open. The sergeant
follows their trail north to the Arctic, then east to where it began: the
place in the Siberian taiga where the sky fell in 1908. A third episode on
the New Game screen, after the second and before the practice range; it
starts on MAP07 and closes the first cycle of the story.

| Map | Place | Narrative function | Leaves by |
|---|---|---|---|
| MAP07 | **Novaya Zemlya** («Новая Земля» / «Nova Zembla»): the Arctic radar station, the radomes, the barracks, the nuclear test site | the invaders use the radar to guide something in; the sergeant cuts the beam | a patrol boat across the Barents Sea, to the Northern Fleet's base, which has not answered the radio for three days |
| MAP08 | **Severomorsk** («Североморск»): the Northern Fleet's submarine base, the covered docks, a nuclear submarine, the cranes, the tunnels in the rock | the invaders were loading the submarine's warheads onto a train; the waybills name Tunguska | an all-night flight east over Siberia |
| MAP09 | **Tunguska** («Тунгуска»): the taiga flattened in 1908, an alien-industrial complex eating the forest, the main portal | the climax of the first cycle: the final boss at the portal | the end of the episode |

The ending: the portal folds in on itself, the machines stand still in the
ash, and the land from Zarya-7 to Tunguska is ours again. One line stays
open ("The sky over the taiga is empty. For now."), but it closes on THE
END, not TO BE CONTINUED. The texts are in `LANGUAGE` (`SD_MAP07_EXIT_TEXT`,
`SD_MAP08_EXIT_TEXT`, `SD_END04_TEXT`); the flow is
`docs/engine/MOD-SPEC.md` §4.6. Until the episode has its own music, its
maps play episode 2's approved B pieces provisionally (MOD-SPEC §4.5); the
boss is a stand-in until a final boss exists (D112).

## Arsenal (D13), one per Doom slot

| Slot | Weapon | Note |
|---|---|---|
| 1 | Ice axe (ледоруб), found on the dorm rack, not issued (D40) | melee |
| 2 | TT-33 Tokarev | pistol |
| 3 | IZh double-barrel hunting shotgun | shotgun |
| 4 | **PPSh-41** | submachine gun; the icon of the mod |
| 5 | RPG-7 | rockets |
| 6 | ROKS-3 flamethrower | replaces plasma |
| 7 | **Hand Katyusha**, secret prototype | BFG; Soviet science fiction |

## Bestiary (D13), provisional names

Yankee-Nazi recruits (zombies with helmets), hybrid Stormtrooper (imp),
Reich hound (demon), Doughboy (cacodemon: floating head with M1 helmet),
Panzermensch (baron), the General (episode boss). Each enemy is assigned to
one faction in the art bible; both factions appear on every map.

## Rules of respect (D12, ratified)

- Lenin and Stalin appear as **poster iconography**, not as characters with
  dialogue.
- Enemies **do** carry swastikas and US flags: this is a video game and a
  fantastic alternate history. Nothing trivialises gulags, famines or the
  Holocaust; there are no jokes about real victims.
- Distribution note (PM, informational): Germany permits such symbols in
  games when artistically justified (USK practice since 2018); some stores
  may still reject them. Not a blocker for a free mod.

## Next step

F2: the `art-director` delivers texture batch 1 of the "Soviet base" set
(6 to 12 pieces: concrete, green steel, Lenin poster, red star, bunker door,
hangar floor) as an HTML preview for the CEO.
