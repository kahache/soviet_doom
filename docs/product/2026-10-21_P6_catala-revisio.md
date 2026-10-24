# P6 — Catalan as the third language: review sheet for the CEO

Date: 2026-10-21 (night shift, D102). Author: mod-engineer (translation and
engine). Origin decision: **D97** («V2: add Catalan»). Status: **draft
for your review**; none of this has been seen in the engine yet (D26).

What is done:

- `src/lumps/LANGUAGE`: a **`[ca]`** section with the **165 ids** that have
  `[enu default]` and `[ru]` (the 163 of v1.0 plus the two new ones of this
  night: `SD_LANGVAL_CA`, the language name in the list, and
  `SD_DEATH_PROMPT`, the death prompt of D100, in all three languages).
- The language option (Options → Soviet Doom → Language) now offers
  **Català**; it writes `language ca`, as «Русский» writes `language ru`.
- The status bar in Catalan: **MUNICIÓ, SALUT, ARMES, ARMADURA**, in
  `SDSBCA` / `SDARCA`. Preview (EN, RU, CA, ×3):
  `docs/art/previews/2026-10-21_2236_P6_statusbar-ca.png`. The approved English
  and Russian bars have not been regenerated or touched.
- `README.md`: a section in Catalan (what it is, how to play, how to set it to
  Catalan) and Catalan mentioned wherever the languages are listed.

Criteria I followed: standard central Catalan (soc, te without an accent,
l·l with a middle dot), **tu** (informal "you") to the player, short dry
sentences like the original, no calques from Spanish, and proper names and
Russian terms as in English (Zarya-7, Tankograd, Vilanova, PPSh-41, IZh-58,
Katyusha, Zelyonka, Panzermensch, Vorwärts). The participles in the death
messages avoid agreeing with the player's gender (active voice or «ha caigut»).

How to review: read the doubts (below, **Q1-Q23**, numbered separately from
the D decisions; in the tables, the id is marked with **Qn**) and then the
tables. To change a text just tell me «id → new text»; the table is generated
from `LANGUAGE` itself, so what you read is exactly what is in the lump.

## What matters most to decide

**Q3. RESOLVED by the PM (2026-10-21, night): the accents are now drawn.**
art-director added **À È É Í Ï Ò Ó Ú Ç** (capitals, like the rest of the
font) to the three fonts with `tools/art/gen_font.py --catalan`
(`CATALAN_ACCENTS`), the same way as Ä Ö Ü (D37): 27 new files, the 339
existing ones unchanged by even one byte. Accent: the letter in the short box
of the umlauts under a two-row stroke (grave slanting left, acute slanting
right); Ç: the C above and the cedilla below, inside the box. See it in
`docs/art/previews/2026-10-21_P6_font-ca.png` (a real `[ca]` sentence in each
font, ×4). The `CATALAN_UNDRAWN_ACCENTS` debt in the tests is now empty. **NOT
VERIFIED in the engine** (D26): that GZDoom draws the lowercase à è é í ò ó ú
ç with these capital-letter files. Original text of the doubt:

The accents were not drawn yet (the most visible issue). The mod's three
fonts (`defsmallfont`, `bigfont`, `sdmenu`; alphabet C "Mashina", D24) only
have ASCII, Cyrillic and the German letters. **À È É Í Ï Ò Ó Ú Ç** are
missing (the · is there). The text is correctly written in `LANGUAGE`;
according to the GZDoom code, an accented letter that the font does not have
is drawn with its base letter («MUNICIO», «CONTINUARA»), but that is **not
verified on screen**. Proposal: art-director adds those 9 capitals to the
three fonts with `tools/art/gen_font.py`, the same as was done with Ä Ö Ü
(D37). Estimate: ~50k tokens, and you approve it by looking at the sheet. The
tests carry the list of these letters as an explicit debt
(`CATALAN_UNDRAWN_ACCENTS`).

**Q2. The "Cyrillic" menu letters (D22) also appear in Catalan.** The menu
font draws R, N, E, W and A as Я, И, Э, Ш, Д for any Latin text, so «NOVA
PARTIDA» will look like «ИOVД PДЯTIDД». D22 was decided for English; in
Catalan it happens only because the font is a single one. Options: (a) leave
it, consistent with the "Latin that recalls Cyrillic"; (b) Catalan without
substitution, which requires a second menu font and the menu choosing a font
per language (I do not know whether MENUDEF allows it: **NOT VERIFIED**). I
recommend (a).

**Q4. RESOLVED by the PM (2026-10-21, night): «TRIA LA MISSIÓ».** With the Ó
already in `sdmenu` (Q3), `SD_MNU_CHOOSEEPISODE` now says «TRIA LA MISSIÓ».
Original text of the doubt: «TRIA EL FRONT» instead of «TRIA LA MISSIÓ». The
header of the episode screen uses the menu font, which has no Ó (and the test
requires every letter to have a glyph). «TRIA EL FRONT» fits the military
tone; if Q3 is done (with the Ó in `sdmenu`), I change it to «TRIA LA MISSIÓ».

**Q12. RESOLVED (2026-10-21, night): the pause sign says
«PAUSA».** mod-engineer + art-director generated only the Catalan variant with
`tools/art/gen_cursor.py --catalan --install` (the same P2 plate of D48, in
`SDMENU`, no system fonts), 77×20 like the others, installed as
`assets/localized/textures/M_PAUSE.ca.png`; `[ca]` `SD_PAUSE_SIGN` points to
`localized/textures/m_pause.ca.png`, just as `[ru]` does. The English and
Russian plates have not changed by even one byte (they still fix the canvas;
«PAUSA» is 3 px wider than «PAUSE» and fits inside, with 5-6 px of red on each
side). As Q2 (a) says, the menu font draws the Latin A as Д: it reads
**«PДUSД»**, consistent with the menu's «ИOVД PДЯTIDД». See it in
`docs/art/previews/2026-10-21_P6_pause-ca.png` (EN, RU, CA over MAP01, ×4).
**NOT VERIFIED in the engine** (D26): the pause with `language ca`. If you
choose Q2 (b), this sign is regenerated with the other font. Original text of
the doubt:

**Q12. The pause sign is still in English («PAUSE»).** The ROADMAP asks for a
Catalan sign. It is generated by `tools/art/gen_cursor.py`, which another
agent (cursor) is editing tonight, so I have not touched it. Once there is a
Catalan «PAUSA» it is one line in `[ca]` (`SD_PAUSE_SIGN`) plus
`localized/textures/M_PAUSE.ca.png`.

**Q13. AI credits.** In Catalan it says that Claude made «els textos en rus i
català». English and Russian still say only «the Russian text»: I have not
changed them without your permission. I propose EN «sound, music, Russian and
Catalan text.» (39 characters); the Russian does not fit in 40 without
splitting the line. Likewise the release's `CREDITS.txt`
(`tools/release.py`, `AI_DISCLOSURE`) and the `README` (this one already says
it).

## Translation doubts

- **Q1. Tú or vostè.** I use tu throughout («Has agafat», «Prem Y», «N'estàs
  segur?»), like most games in Catalan; Russian uses «Вы». The death prompt
  you asked for, «Prem %s per continuar», was already in tu.
- **Q5. The title.** «Soviet Doom» stays as it is (Russian translates it:
  «Советский Doom»). Alternative: «Doom Soviètic».
- **Q6. Doughboy** stays «Doughboy» (Russian uses «Каска», helmet). In
  Catalan «Casc» would clash with «Un casc d'acer» of the armour bonus.
- **Q7. Stormtrooper → «Soldat d'assalt híbrid».** Alternative: keep
  «Stormtrooper» as a proper name.
- **Q8. Difficulty 5: «Heroi de la Unió Soviètica, pòstum».** The natural
  form would be «…, a títol pòstum», but it measures 310 px and the column
  allows 288. Alternative that fits: «Heroi de l'URSS, a títol pòstum».
- **Q9. Difficulty 1: «Encara soc pioner»** (soc without an accent, 2017
  norm).
- **Q10. Difficulty 4: «No passaran, camarades»**, the Catalan form of the
  slogan (English uses the Spanish «No pasaran»). If you prefer the Spanish as
  a quotation, it is a one-line change.
- **Q11. The practice grounds:** the map «Camp d'instrucció» (Training
  Ground) and the episode «Camp de tir» (Practice Range).
- **Q14. Ending: «L'interruptor cau.»** for «The breaker drops». A more
  active alternative: «Abaixes l'interruptor.»
- **Q15. Deaths:** in active voice («Un fuseller del Reich ha abatut %o»)
  so the participle does not agree with the player's gender.
- **Q16. Menu verbs in the imperative** (CARREGA, DESA, SURT), like software
  in Catalan (Softcatalà); «AJUDA» for READ THIS (Russian uses «СПРАВКА»).
- **Q17. Picking up a weapon: «Has agafat…»** Alternative: «Has trobat…».
- **Q18. Calibres with a decimal comma and ×: «7,62×25»**, like Russian;
  English uses «7.62x25».
- **Q19. «l'RPG-7»** with an apostrophe (read "erra-pe-ge"), standard.
- **Q20. «Un embenat de campanya»** for «A field dressing».
- **Q21. «Zarya-7 torna a ser a les nostres mans»**: English says «yours»,
  Russian «наша» (ours); I follow Russian (ours), the same in the ending with
  Tankograd.
- **Q22. Quit 2:** Klochkov's quote (1941) in Catalan: «Rússia és
  immensa, però no hi ha on retrocedir: Moscou és al darrere.»
- **Q23. Status bar: «MUNICIÓ»** with the accent drawn as one pixel above
  the O (see it in the preview). Alternative without the accent:
  «MUNICIONS» (fits, tighter).

## What the PM must test in the engine (D26)

1. Start-up with 0 errors; Options → Soviet Doom → Language shows four
   rows; choosing Català changes the main menu, the options screen title and
   the credits on the fly, and the row shows «Català».
2. `language ca` in the console and `language cat`: the row shows Català.
3. In game with `language ca`: the status bar with MUNICIÓ / SALUT /
   ARMES / ARMADURA (H2 of MOD-SPEC 6.5.1 in Catalan), a pickup message with
   an accent and with ç («Has agafat el llançaflames ROKS-3!»: that the
   lowercase à/ç comes out with the new glyph and not with the base letter,
   Q3), the MAP01→MAP02 transition («Cosmòdrom», «il·luminat»), the episode
   screen with «TRIA LA MISSIÓ» (Q4) and the ending with «CONTINUARÀ».
4. Back to English and to Русский: everything as before.

## The tables

### Main menu and choice screens (SDMENU font; accents since Q3)

| id | EN | CA |
|---|---|---|
| `SD_MNU_NEWGAME` **Q2** | NEW GAME | NOVA PARTIDA |
| `SD_MNU_OPTIONS` | OPTIONS | OPCIONS |
| `SD_MNU_LOADGAME` **Q16** | LOAD GAME | CARREGA PARTIDA |
| `SD_MNU_SAVEGAME` | SAVE GAME | DESA PARTIDA |
| `SD_MNU_READTHIS` | READ THIS! | AJUDA |
| `SD_MNU_QUITGAME` | QUIT GAME | SURT DEL JOC |
| `SD_MNU_CHOOSESKILL` | CHOOSE DIFFICULTY | TRIA LA DIFICULTAT |
| `SD_MNU_CHOOSEEPISODE` **Q4** | CHOOSE MISSION | TRIA LA MISSIÓ |

### Mod options (Options → Soviet Doom)

| id | EN | CA |
|---|---|---|
| `SD_OPTMNU_TITLE` | Soviet Doom | Soviet Doom |
| `SD_OPTMNU_LANGUAGE` | Language | Idioma |
| `SD_OPTMNU_LANGHELP` | Applies immediately. Saved for the next session. | S'aplica a l'acte. Es desa per a la propera sessió. |
| `SD_LANGVAL_AUTO` | Automatic (system) | Automàtic (sistema) |
| `SD_LANGVAL_EN` | English | Anglès |
| `SD_LANGVAL_RU` | Russian | Rus |
| `SD_LANGVAL_CA` | Catalan | Català |

### Difficulty

| id | EN | CA |
|---|---|---|
| `SD_SKILL_1` **Q9** | I am still a Pioneer | Encara soc pioner |
| `SD_SKILL_2` | I have seen worse winters | He vist hiverns pitjors |
| `SD_SKILL_3` | Not one step back | Ni un pas enrere |
| `SD_SKILL_4` **Q10** | No pasaran, comrades | No passaran, camarades |
| `SD_SKILL_5` **Q8** | Hero of the Soviet Union, posthumously | Heroi de la Unió Soviètica, pòstum |
| `SD_SKILL_5_CONFIRM` | The award is posthumous and the enemy dead do not stay dead. // Are you sure? | La condecoració és pòstuma, i aquí els enemics morts no es queden morts. // N'estàs segur? |

### Episodes and maps

| id | EN | CA |
|---|---|---|
| `SD_EP01_NAME` **Q5** | Soviet Doom | Soviet Doom |
| `SD_EP02_NAME` **Q11** | Practice Range | Camp de tir |
| `SD_MAP01_NAME` | Zarya-7 Cosmodrome | Cosmòdrom Zarya-7 |
| `SD_MAP02_NAME` | Metro-Bunker | Metro-búnquer |
| `SD_MAP03_NAME` | Tankograd | Tankograd |
| `SD_RANGE_NAME` **Q11** | Training Ground | Camp d'instrucció |
| `SD_PLAYER_NAME` | Sergeant Vilanova | Sergent Vilanova |

### Map transitions and ending (text screen; «/» = line break, «//» = blank line)

| id | EN | CA |
|---|---|---|
| `SD_MAP01_EXIT_TEXT` **Q21** | Zarya-7 is yours again. // The service lift drops into the dark, / past the last lit level, and keeps / going. Under the cosmodrome runs a / metro line, dug deep for the next war. // The invaders found it first. / You follow them down. | Zarya-7 torna a ser a les nostres mans. // L'ascensor de servei baixa cap a la / foscor, deixa enrere l'últim nivell / il·luminat i no s'atura. Sota el / cosmòdrom hi passa una línia de / metro, excavada ben fonda per a la / propera guerra. // Els invasors la van trobar primer. / Els segueixes cap avall. |
| `SD_MAP02_EXIT_TEXT` | The westbound tunnel climbs into / daylight at a goods spur. // Beyond the buffers stand the sheds / of a tractor works. The tracks in / the yard are too wide for tractors. // The workers have a name for it: / Tankograd. | El túnel cap a l'oest surt a la llum / del dia en un ramal de mercaderies. // Darrere els topalls s'alcen les naus / d'una fàbrica de tractors. Al pati hi ha / rodades massa amples per a tractors. // Els obrers li diuen d'una altra manera: / Tankograd. |
| `SD_END01_TEXT` **Q14** | The breaker drops. Behind you the / portal shrinks to a point of light / and goes out. // Tankograd is yours again: the line / stands still, and nothing more / comes through. // Those already through are marching / west, to Moscow. // TO BE CONTINUED | L'interruptor cau. Darrere teu, el / portal s'encongeix fins a un punt de / llum i s'apaga. // Tankograd torna a ser a les nostres / mans: la cadena s'atura, i ja no hi / arriba ningú més. // Els que ja havien passat marxen cap a / l'oest, cap a Moscou. // CONTINUARÀ |
| `SD_END02_TEXT` | The range is closed for the day. // The campaign begins from New Game. | El camp de tir tanca per avui. // La campanya comença a «Nova partida». |

### Weapons: name and pickup message

| id | EN | CA |
|---|---|---|
| `SD_TAG_ICEAXE` | Ice axe | Piolet |
| `SD_TAG_TOKAREV` | TT-33 Tokarev | Tokarev TT-33 |
| `SD_TAG_IZH` | IZh-58 double barrel | IZh-58 de dos canons |
| `SD_TAG_PPSH` | PPSh-41 | PPSh-41 |
| `SD_TAG_RPG7` | RPG-7 | RPG-7 |
| `SD_TAG_ROKS3` | ROKS-3 flamethrower | Llançaflames ROKS-3 |
| `SD_TAG_KATYUSHA` | Hand Katyusha | Katyusha de mà |
| `SD_PICKUP_ICEAXE` | An ice axe. | Un piolet. |
| `SD_PICKUP_TOKAREV` **Q17** | You got the TT-33 Tokarev! | Has agafat la Tokarev TT-33! |
| `SD_PICKUP_IZH` | You got the IZh-58 double barrel! | Has agafat l'escopeta de dos canons IZh-58! |
| `SD_PICKUP_PPSH` | You got the PPSh-41! | Has agafat el PPSh-41! |
| `SD_PICKUP_RPG7` **Q19** | You got the RPG-7! | Has agafat l'RPG-7! |
| `SD_PICKUP_ROKS3` | You got the ROKS-3 flamethrower! | Has agafat el llançaflames ROKS-3! |
| `SD_PICKUP_KATYUSHA` | You got the hand Katyusha. Prototype. Do not drop it. | Has agafat la Katyusha de mà. Prototip. No la deixis caure. |

### Ammo, health, armour and map (pickup messages)

| id | EN | CA |
|---|---|---|
| `AMMO_CLIP` **Q18** | 7.62x25 rounds | Cartutxos de 7,62×25 |
| `AMMO_SHELLS` | 12 gauge shells | Cartutxos del calibre 12 |
| `AMMO_ROCKETS` | PG-7V rounds | Projectils PG-7V |
| `AMMO_CELLS` | Fuel | Combustible |
| `SD_GOT_CLIP` | A magazine. 7.62x25. | Un carregador. 7,62×25. |
| `SD_GOT_CLIPBOX` | A box of 7.62x25. | Una caixa de 7,62×25. |
| `SD_GOT_SHELLS` | Four shells. 12 gauge. | Quatre cartutxos. Calibre 12. |
| `SD_GOT_SHELLBOX` | A box of 12 gauge shells. | Una caixa de cartutxos del calibre 12. |
| `SD_GOT_ROCKET` | One PG-7V round. | Un projectil PG-7V. |
| `SD_GOT_ROCKBOX` | A crate of PG-7V rounds. | Un caixó de projectils PG-7V. |
| `SD_GOT_CELL` | A canister of fuel. | Un bidó de combustible. |
| `SD_GOT_CELLPACK` | A full fuel tank. | Un dipòsit ple de combustible. |
| `SD_GOT_BACKPACK` | A paratrooper's pack. Everything you can carry! | Una motxilla de paracaigudista. Tot el que puguis carregar! |
| `SD_GOT_STIMPACK` **Q20** | A field dressing. | Un embenat de campanya. |
| `SD_GOT_MEDIKIT` | A first-aid box. | Una farmaciola. |
| `SD_GOT_HEALTHBONUS` | Zelyonka. | Zelyonka. |
| `SD_GOT_ARMORBONUS` | A steel helmet. | Un casc d'acer. |
| `SD_GOT_ARMOR` | A flak vest and a helmet. | Una armilla antibales i un casc. |
| `SD_GOT_MEGAARMOR` | A steel breastplate and helmet! | Una cuirassa d'acer i un casc! |
| `SD_GOT_MAP` | A commander's map case. The whole area is on it. | Un portamapes de comandant. Hi surt tota la zona. |

### Passes and doors

| id | EN | CA |
|---|---|---|
| `SD_PICKUP_BLUEPASS` | Blue pass. | Passi blau. |
| `SD_PICKUP_YELLOWPASS` | Yellow pass. | Passi groc. |
| `SD_PICKUP_REDPASS` | Red pass. | Passi vermell. |
| `PD_BLUECO` | You need a blue pass to activate this object | Necessites un passi blau per activar aquest objecte |
| `PD_YELLOWCO` | You need a yellow pass to activate this object | Necessites un passi groc per activar aquest objecte |
| `PD_REDCO` | You need a red pass to activate this object | Necessites un passi vermell per activar aquest objecte |

### Enemies and the General

| id | EN | CA |
|---|---|---|
| `SD_TAG_RIFLEMAN` | Reich rifleman | Fuseller del Reich |
| `SD_TAG_TROOPER` | Legion trooper | Soldat de la Legió |
| `SD_TAG_STORM` **Q7** | Hybrid Stormtrooper | Soldat d'assalt híbrid |
| `SD_TAG_HOUND` | Reich hound | Gos del Reich |
| `SD_TAG_DOUGHBOY` **Q6** | Doughboy | Doughboy |
| `SD_TAG_PANZER` | Panzermensch | Panzermensch |
| `SD_TAG_PANZER_HEAVY` | Heavy Panzermensch | Panzermensch pesant |
| `SD_TAG_GENERAL` | The General | El General |
| `SD_GENERAL_ORDER` | The General: Vorwärts! | El General: Vorwärts! |
| `SD_OB_RIFLEMAN` **Q15** | %o was shot by a Reich rifleman. | Un fuseller del Reich ha abatut %o. |
| `SD_OB_TROOPER` | %o was blasted by a Legion trooper. | Un soldat de la Legió ha cosit %o a trets. |
| `SD_OB_STORM` | %o was burned by a Stormtrooper's bolt. | La descàrrega d'un soldat d'assalt ha cremat %o. |
| `SD_OBHIT_STORM` | %o was torn open by a Stormtrooper. | Un soldat d'assalt ha esbudellat %o. |
| `SD_OB_HOUND` | %o was run down by a Reich hound. | Un gos del Reich ha atrapat %o. |
| `SD_OB_DOUGHBOY` | %o was hit by a Doughboy's shell. | Un obús d'un Doughboy ha tocat %o. |
| `SD_OBHIT_DOUGHBOY` | %o was bitten by a Doughboy. | Un Doughboy ha mossegat %o. |
| `SD_OB_PANZER` | %o was shelled by a Panzermensch. | Un Panzermensch ha bombardejat %o. |
| `SD_OBHIT_PANZER` | %o was crushed by a Panzermensch. | Un Panzermensch ha aixafat %o. |
| `SD_OB_GENERAL` | %o fell to the General's salvo. | %o ha caigut sota la salva del General. |

### Multiplayer deaths (%o victim, %k killer)

| id | EN | CA |
|---|---|---|
| `SD_OB_ICEAXE` | %o met %k's ice axe. | %o ha topat amb el piolet de %k. |
| `SD_OB_TOKAREV` | %o was shot by %k's Tokarev. | %k ha abatut %o amb la Tokarev. |
| `SD_OB_IZH` | %o took both barrels from %k. | %o s'ha menjat els dos canons de %k. |
| `SD_OB_PPSH` | %o was cut down by %k's PPSh-41. | El PPSh-41 de %k ha segat %o. |
| `SD_OB_RPG7` | %o was blown apart by %k's RPG-7. | L'RPG-7 de %k ha fet miques %o. |
| `SD_OB_ROKS3` | %o burned under %k's ROKS-3. | El ROKS-3 de %k ha rostit %o. |
| `SD_OB_KATYUSHA` | %o caught %k's whole salvo. | %o s'ha empassat tota la salva de %k. |

### Death prompt (new, v1.1) and pause

| id | EN | CA |
|---|---|---|
| `SD_DEATH_PROMPT` | Press %s to continue | Prem %s per continuar |
| `SD_PAUSE_SIGN` **Q12** | M_PAUSE | localized/textures/m_pause.ca.png |

### Quit messages (each ends with «(Prem Y per sortir.)», omitted here)

| id | EN | CA |
|---|---|---|
| `SD_QUIT_01` **Q1** | Leaving your post, Sergeant? / The Urals will not hold themselves. | Abandones el teu lloc, sergent? / Els Urals no es defensaran tots sols. |
| `SD_QUIT_02` **Q22** | Russia is vast, but there is nowhere / to retreat. Moscow is behind us. | Rússia és immensa, però no hi ha on / retrocedir: Moscou és al darrere. |
| `SD_QUIT_03` | The five-year plan is not fulfilled. / Nobody leaves the shift early. | El pla quinquennal no s'ha complert. / Aquí ningú no plega abans d'hora. |
| `SD_QUIT_04` | The parade is only days away. / Who marches if you go home? | Falten pocs dies per a la desfilada. / Qui desfilarà si te'n vas a casa? |
| `SD_QUIT_05` | The Fourth Reich takes no days off. / Nor does the Liberty Legion. | El Quart Reich no fa festa. / La Legió de la Llibertat, tampoc. |
| `SD_QUIT_06` | The canteen closes at eight. / The war does not. | El menjador tanca a les vuit. / La guerra, no. |
| `SD_QUIT_07` | Comrade, the Party committee / will want an explanation. | Camarada, el comitè del Partit / voldrà una explicació. |
| `SD_QUIT_08` | Your absence is in the duty log. / In pencil, for now. | La teva absència ja consta al registre. / De moment, a llapis. |
| `SD_QUIT_09` | Barcelona waited forty years. / The Urals can wait one evening. | Barcelona va esperar quaranta anys. / Els Urals poden esperar un vespre. |
| `SD_QUIT_10` | The capitalists are counting on you / to go home early. | Els capitalistes compten que / te'n tornaràs aviat a casa. |
| `SD_QUIT_11` | Leave the radio on. / The next sentry gets lonely. | Deixa la ràdio encesa. / Al teu relleu li farà companyia. |
| `SD_QUIT_12` | Lenin is watching from the wall. / He does not look pleased. | Lenin et mira des de la paret. / I no fa cara de content. |
| `SD_QUIT_13` | Your shift ends / when the invaders do. | El teu torn s'acaba / quan s'acabin els invasors. |
| `SD_QUIT_14` | Hand your rifle in at the armoury / and sign for it twice. | Torna el fusell a l'armeria / i signa el rebut dues vegades. |
| `SD_QUIT_15` | The tea is still hot, Sergeant. / Stay a little longer. | El te encara és calent, sergent. / Queda't una estona més. |

### Credits (one screen line per id, max. 40 characters)

| id | EN | CA |
|---|---|---|
| `SD_CRED_TITLE` | Credits | Crèdits |
| `SD_CRED_H_TEAM` | Made by | Fet per |
| `SD_CRED_TEAM_1` | the Soviet Doom project | el projecte Soviet Doom |
| `SD_CRED_FAN_1` | A fan project, not affiliated | Un projecte de fans, sense cap vincle |
| `SD_CRED_FAN_2` | with id Software. | amb id Software. |
| `SD_CRED_TEAM_2` | Code: GNU GPL 3.0 or later | Codi: GNU GPL 3.0 o posterior |
| `SD_CRED_TEAM_3` | Art, sound, maps and text | Art, so, mapes i textos |
| `SD_CRED_TEAM_4` | under CC BY-NC-SA 4.0 | amb llicència CC BY-NC-SA 4.0 |
| `SD_CRED_H_MUSIC` | Music | Música |
| `SD_CRED_MUSIC_1` | The Internationale (title music): | La Internacional (música d'inici): |
| `SD_CRED_MUSIC_2` | composed by Pierre De Geyter (1888), | composta per Pierre De Geyter (1888), |
| `SD_CRED_MUSIC_3` | public domain; | domini públic; |
| `SD_CRED_MUSIC_4` | MIDI sequence by Jerry Engelbach, | seqüència MIDI de Jerry Engelbach, |
| `SD_CRED_MUSIC_5` | used under his attribution licence | usada amb la seva llicència |
| `SD_CRED_MUSIC_6` | (Wikimedia Commons, | d'atribució (Wikimedia Commons, |
| `SD_CRED_MUSIC_7` | File:Internationale_orch2.mid). | fitxer Internationale_orch2.mid). |
| `SD_CRED_MUSIC_8` | Radio: Ey, ukhnem and Kolokolchik; | Ràdio: Ey, ukhnem i Kolokolchik; |
| `SD_CRED_MUSIC_9` | MIDI sequences by Peter Gerloff, CC0. | seqüències MIDI de Peter Gerloff, CC0. |
| `SD_CRED_H_ENGINE` | Engine | Motor |
| `SD_CRED_ENGINE_1` | GZDoom (zdoom.org), GNU GPL 3.0, | GZDoom (zdoom.org), GNU GPL 3.0, |
| `SD_CRED_ENGINE_2` | by the GZDoom and ZDoom developers, | dels desenvolupadors de GZDoom i ZDoom, |
| `SD_CRED_ENGINE_3` | based on the Doom source code | basat en el codi font de Doom |
| `SD_CRED_ENGINE_4` | released by id Software. | publicat per id Software. |
| `SD_CRED_H_IWAD` | Game data | Dades del joc |
| `SD_CRED_IWAD_1` | Freedoom (freedoom.github.io), | Freedoom (freedoom.github.io), |
| `SD_CRED_IWAD_2` | by the Contributors to the Freedoom | dels col·laboradors del projecte |
| `SD_CRED_IWAD_3` | project, modified BSD licence. | Freedoom, llicència BSD modificada. |
| `SD_CRED_IWAD_4` | TT-33 hands: Freedoom's, recoloured; | Mans de la TT-33: Freedoom, repintades; |
| `SD_CRED_IWAD_5` | other placeholders read from the IWAD. | altres elements provisionals: de l'IWAD. |
| `SD_CRED_H_SOURCES` | Sources | Fonts |
| `SD_CRED_SRC_1` | Lenin poster after a photograph | Cartell de Lenin a partir d'una foto |
| `SD_CRED_SRC_2` | by Pavel Zhukov (1920), | de Pavel Zhukov (1920), |
| `SD_CRED_SRC_3` | public domain. | domini públic. |
| `SD_CRED_SFX_1` | Sound clips: CC0 packs by Kenney, | Sons: paquets CC0 de Kenney, |
| `SD_CRED_SFX_2` | rubberduck and Darsycho (OpenGameArt). | rubberduck i Darsycho (OpenGameArt). |
| `SD_CRED_SFX_3` | Voice reference: kurt, CC-BY 3.0. | Referència de veu: kurt, CC-BY 3.0. |
| `SD_CRED_H_AI` | Made with AI | Fet amb IA |
| `SD_CRED_AI_1` | Claude (Anthropic), in Claude Code: | Claude (Anthropic), a Claude Code: |
| `SD_CRED_AI_2` | design, maps, code, textures, sprites, | disseny, mapes, codi, textures, sprites, |
| `SD_CRED_AI_3` **Q13** | sound, music and the Russian text. | so, música i els textos en rus i català. |
| `SD_CRED_AI_4` | Google Gemini: source images for the | Google Gemini: imatges d'origen per a |
| `SD_CRED_AI_5` | weapons in hand and the sergeant's face. | les armes a la mà i la cara del sergent. |
| `SD_CRED_AI_6` | Fooocus / SDXL (local): hand references. | Fooocus / SDXL (local): models de mans. |
| `SD_CRED_AI_7` | Chatterbox (Resemble AI, local): | Chatterbox (Resemble AI, local): |
| `SD_CRED_AI_8` | most enemy voices. | la majoria de veus dels enemics. |

Ids not listed (not read as text or almost never seen): `PD_BLUEC`, `PD_REDC`, `PD_YELLOWC`, `SD_SBAR_ARMS_IMAGE`, `SD_SBAR_IMAGE`.
