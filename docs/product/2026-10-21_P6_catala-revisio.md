# P6 — El catalán como tercer idioma: hoja de revisión para el CEO

Fecha: 2026-10-21 (turno de noche, D102). Autor: mod-engineer (traducción y
motor). Decisión de origen: **D97** («V2: add Catalan»). Estado: **borrador
para tu revisión**; nada de esto se ha visto todavía en el motor (D26).

Qué hay hecho:

- `src/lumps/LANGUAGE`: sección **`[ca]`** con los **165 ids** que tienen
  `[enu default]` y `[ru]` (los 163 de v1.0 más los dos nuevos de esta
  noche: `SD_LANGVAL_CA`, el nombre del idioma en la lista, y
  `SD_DEATH_PROMPT`, el aviso al morir de D100, en los tres idiomas).
- La opción de idioma (Options → Soviet Doom → Language) ofrece ahora
  **Català**; escribe `language ca`, como «Русский» escribe `language ru`.
- La barra de estado en catalán: **MUNICIÓ, SALUT, ARMES, ARMADURA**, en
  `SDSBCA` / `SDARCA`. Vista previa (EN, RU, CA, ×3):
  `docs/art/previews/2026-10-21_2236_P6_statusbar-ca.png`. Las barras inglesa
  y rusa aprobadas no se han regenerado ni tocado.
- `README.md`: sección en catalán (qué es, cómo jugar, cómo ponerlo en
  catalán) y el catalán mencionado donde se listan los idiomas.

Criterios que he seguido: catalán central normativo (soc, te sin acento,
l·l con punt volat), **tú** al jugador, frases cortas y secas como el
original, nada de calcos del castellano, y los nombres propios y términos
rusos como en inglés (Zarya-7, Tankograd, Vilanova, PPSh-41, IZh-58,
Katyusha, Zelyonka, Panzermensch, Vorwärts). Los participios de las muertes
evitan concordar con el género del jugador (voz activa o «ha caigut»).

Cómo revisar: lee las dudas (abajo, **Q1-Q23**, numeradas aparte de las
decisiones D; en las tablas, el id marcado con **Qn**) y luego las tablas. Para cambiar un texto basta decirme «id → texto
nuevo»; la tabla se genera del propio `LANGUAGE`, así que lo que lees es
exactamente lo que hay en el lump.

## Lo que más importa decidir

**Q3. RESUELTA por el PM (2026-10-21, noche): las tildes ya se dibujan.**
art-director añadió **À È É Í Ï Ò Ó Ú Ç** (mayúsculas, como el resto de la
fuente) a las tres fuentes con `tools/art/gen_font.py --catalan`
(`CATALAN_ACCENTS`), igual que Ä Ö Ü (D37): 27 archivos nuevos, los 339
existentes sin cambiar ni un byte. Acento: la letra en la caja corta de las
diéresis bajo un trazo de dos filas (grave inclinado a la izquierda, agudo a
la derecha); Ç: la C arriba y la cedilla debajo, dentro de la caja. Míralo
en `docs/art/previews/2026-10-21_P6_font-ca.png` (una frase real de `[ca]`
en cada fuente, ×4). La deuda `CATALAN_UNDRAWN_ACCENTS` de los tests queda
vacía. **NO VERIFICADO en el motor** (D26): que GZDoom dibuje las minúsculas
à è é í ò ó ú ç con estos archivos de mayúscula. Texto original de la duda:

Las tildes no se dibujaban todavía (lo más visible). Las tres fuentes
del mod (`defsmallfont`, `bigfont`, `sdmenu`; alfabeto C «Mashina», D24)
solo tienen ASCII, cirílico y las letras alemanas. Faltan **À È É Í Ï Ò Ó Ú
Ç** (la · sí está). El texto está bien escrito en `LANGUAGE`; según el código
de GZDoom, una letra acentuada que la fuente no tiene se dibuja con su letra
base («MUNICIO», «CONTINUARA»), pero eso **no está verificado en pantalla**.
Propuesta: que art-director añada esas 9 mayúsculas a las tres fuentes con
`tools/art/gen_font.py`, igual que se hizo con Ä Ö Ü (D37). Estimación:
~50k tokens, y tú lo apruebas mirando la hoja. Los tests llevan la lista de
estas letras como deuda explícita (`CATALAN_UNDRAWN_ACCENTS`).

**Q2. Las letras «cirílicas» del menú (D22) también salen en catalán.** La
fuente del menú dibuja R, N, E, W y A como Я, И, Э, Ш, Д para cualquier
texto latino, así que «NOVA PARTIDA» se verá «ИOVД PДЯTIDД». D22 se decidió
para el inglés; en catalán ocurre solo porque la fuente es una. Opciones:
(a) dejarlo así, coherente con el «latín que recuerda al cirílico»;
(b) catalán sin sustitución, que pide una segunda fuente de menú y que el
menú elija fuente por idioma (no sé si MENUDEF lo permite: **NO VERIFICADO**).
Recomiendo (a).

**Q4. RESUELTA por el PM (2026-10-21, noche): «TRIA LA MISSIÓ».** Con la Ó
ya en `sdmenu` (Q3), `SD_MNU_CHOOSEEPISODE` dice ahora «TRIA LA MISSIÓ».
Texto original de la duda: «TRIA EL FRONT» en vez de «TRIA LA MISSIÓ». La cabecera de la
pantalla de episodio va en la fuente del menú, que no tiene Ó (y el test
exige que cada letra tenga glifo). «TRIA EL FRONT» encaja con el tono
militar; si se hace Q3 (con la Ó en `sdmenu`), cambio a «TRIA LA MISSIÓ».

**Q12. El letrero de pausa sigue en inglés («PAUSE»).** El ROADMAP pide un
letrero catalán. Lo genera `tools/art/gen_cursor.py`, que esta noche está
editando otro agente (cursor), así que no lo he tocado. Cuando haya un
«PAUSA» catalán es una línea en `[ca]` (`SD_PAUSE_SIGN`) más
`localized/textures/M_PAUSE.ca.png`.

**Q13. Créditos de IA.** En catalán dice que Claude hizo «els textos en rus i
català». El inglés y el ruso siguen diciendo solo «the Russian text»: no los
he cambiado sin tu permiso. Propongo EN «sound, music, Russian and Catalan
text.» (39 caracteres); el ruso no cabe en 40 sin partir la línea. Igual el
`CREDITS.txt` de la release (`tools/release.py`, `AI_DISCLOSURE`) y el
`README` (este ya lo dice).

## Dudas de traducción

- **Q1. Tú o vostè.** Uso tú en todo («Has agafat», «Prem Y», «N'estàs
  segur?»), como la mayoría de juegos en catalán; el ruso usa «Вы». El aviso
  al morir que pediste, «Prem %s per continuar», ya iba en tú.
- **Q5. El título.** «Soviet Doom» se queda así (el ruso lo traduce:
  «Советский Doom»). Alternativa: «Doom Soviètic».
- **Q6. Doughboy** se queda «Doughboy» (el ruso usa «Каска», casco). En
  catalán «Casc» chocaría con «Un casc d'acer» del bonus de blindaje.
- **Q7. Stormtrooper → «Soldat d'assalt híbrid».** Alternativa: dejar
  «Stormtrooper» como nombre propio.
- **Q8. Dificultad 5: «Heroi de la Unió Soviètica, pòstum».** Lo natural
  sería «…, a títol pòstum», pero mide 310 px y la columna admite 288.
  Alternativa que cabe: «Heroi de l'URSS, a títol pòstum».
- **Q9. Dificultad 1: «Encara soc pioner»** (soc sin acento, norma de 2017).
- **Q10. Dificultad 4: «No passaran, camarades»**, la forma catalana del
  lema (el inglés usa la castellana «No pasaran»). Si prefieres la
  castellana como cita, es un cambio de una línea.
- **Q11. El campo de prácticas:** el mapa «Camp d'instrucció» (Training
  Ground) y el episodio «Camp de tir» (Practice Range).
- **Q14. Final: «L'interruptor cau.»** para «The breaker drops». Alternativa
  más activa: «Abaixes l'interruptor.»
- **Q15. Muertes:** en voz activa («Un fuseller del Reich ha abatut %o»)
  para no concordar el participio con el género del jugador.
- **Q16. Verbos del menú en imperativo** (CARREGA, DESA, SURT), como el
  software en catalán (Softcatalà); «AJUDA» para READ THIS (el ruso usa
  «СПРАВКА»).
- **Q17. Recoger un arma: «Has agafat…»** Alternativa: «Has trobat…».
- **Q18. Calibres con coma decimal y ×: «7,62×25»**, como el ruso; el
  inglés usa «7.62x25».
- **Q19. «l'RPG-7»** con apóstrofo (se lee «erra-pe-ge»), normativo.
- **Q20. «Un embenat de campanya»** para «A field dressing».
- **Q21. «Zarya-7 torna a ser a les nostres mans»**: el inglés dice «yours»,
  el ruso «наша»; sigo al ruso (nuestra), igual en el final con Tankograd.
- **Q22. Salir 2:** la cita de Klochkov (1941) en catalán: «Rússia és
  immensa, però no hi ha on retrocedir: Moscou és al darrere.»
- **Q23. Barra de estado: «MUNICIÓ»** con la tilde dibujada como un píxel
  sobre la O (mírala en la vista previa). Alternativa sin tilde:
  «MUNICIONS» (cabe, más justa).

## Qué debe probar el PM en el motor (D26)

1. Arranque con 0 errores; Options → Soviet Doom → Language muestra cuatro
   filas; elegir Català cambia en caliente el menú principal, el título de
   la pantalla de opciones y los créditos, y la fila muestra «Català».
2. `language ca` en consola y `language cat`: la fila muestra Català.
3. En partida con `language ca`: la barra de estado con MUNICIÓ / SALUT /
   ARMES / ARMADURA (H2 de MOD-SPEC 6.5.1 en catalán), un mensaje de
   recogida con tilde y con ç («Has agafat el llançaflames ROKS-3!»: que la
   à/ç minúscula salga con el glifo nuevo y no con la letra base, Q3), la
   transición MAP01→MAP02 («Cosmòdrom», «il·luminat»), la pantalla de
   episodio con «TRIA LA MISSIÓ» (Q4) y el final con «CONTINUARÀ».
4. Volver a English y a Русский: todo como antes.

## Las tablas

### Menú principal y pantallas de elección (fuente SDMENU; acentos desde Q3)

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

### Opciones del mod (Options → Soviet Doom)

| id | EN | CA |
|---|---|---|
| `SD_OPTMNU_TITLE` | Soviet Doom | Soviet Doom |
| `SD_OPTMNU_LANGUAGE` | Language | Idioma |
| `SD_OPTMNU_LANGHELP` | Applies immediately. Saved for the next session. | S'aplica a l'acte. Es desa per a la propera sessió. |
| `SD_LANGVAL_AUTO` | Automatic (system) | Automàtic (sistema) |
| `SD_LANGVAL_EN` | English | Anglès |
| `SD_LANGVAL_RU` | Russian | Rus |
| `SD_LANGVAL_CA` | Catalan | Català |

### Dificultad

| id | EN | CA |
|---|---|---|
| `SD_SKILL_1` **Q9** | I am still a Pioneer | Encara soc pioner |
| `SD_SKILL_2` | I have seen worse winters | He vist hiverns pitjors |
| `SD_SKILL_3` | Not one step back | Ni un pas enrere |
| `SD_SKILL_4` **Q10** | No pasaran, comrades | No passaran, camarades |
| `SD_SKILL_5` **Q8** | Hero of the Soviet Union, posthumously | Heroi de la Unió Soviètica, pòstum |
| `SD_SKILL_5_CONFIRM` | The award is posthumous and the enemy dead do not stay dead. // Are you sure? | La condecoració és pòstuma, i aquí els enemics morts no es queden morts. // N'estàs segur? |

### Episodios y mapas

| id | EN | CA |
|---|---|---|
| `SD_EP01_NAME` **Q5** | Soviet Doom | Soviet Doom |
| `SD_EP02_NAME` **Q11** | Practice Range | Camp de tir |
| `SD_MAP01_NAME` | Zarya-7 Cosmodrome | Cosmòdrom Zarya-7 |
| `SD_MAP02_NAME` | Metro-Bunker | Metro-búnquer |
| `SD_MAP03_NAME` | Tankograd | Tankograd |
| `SD_RANGE_NAME` **Q11** | Training Ground | Camp d'instrucció |
| `SD_PLAYER_NAME` | Sergeant Vilanova | Sergent Vilanova |

### Transiciones de mapa y final (pantalla de texto; «/» = salto de línea, «//» = línea en blanco)

| id | EN | CA |
|---|---|---|
| `SD_MAP01_EXIT_TEXT` **Q21** | Zarya-7 is yours again. // The service lift drops into the dark, / past the last lit level, and keeps / going. Under the cosmodrome runs a / metro line, dug deep for the next war. // The invaders found it first. / You follow them down. | Zarya-7 torna a ser a les nostres mans. // L'ascensor de servei baixa cap a la / foscor, deixa enrere l'últim nivell / il·luminat i no s'atura. Sota el / cosmòdrom hi passa una línia de / metro, excavada ben fonda per a la / propera guerra. // Els invasors la van trobar primer. / Els segueixes cap avall. |
| `SD_MAP02_EXIT_TEXT` | The westbound tunnel climbs into / daylight at a goods spur. // Beyond the buffers stand the sheds / of a tractor works. The tracks in / the yard are too wide for tractors. // The workers have a name for it: / Tankograd. | El túnel cap a l'oest surt a la llum / del dia en un ramal de mercaderies. // Darrere els topalls s'alcen les naus / d'una fàbrica de tractors. Al pati hi ha / rodades massa amples per a tractors. // Els obrers li diuen d'una altra manera: / Tankograd. |
| `SD_END01_TEXT` **Q14** | The breaker drops. Behind you the / portal shrinks to a point of light / and goes out. // Tankograd is yours again: the line / stands still, and nothing more / comes through. // Those already through are marching / west, to Moscow. // TO BE CONTINUED | L'interruptor cau. Darrere teu, el / portal s'encongeix fins a un punt de / llum i s'apaga. // Tankograd torna a ser a les nostres / mans: la cadena s'atura, i ja no hi / arriba ningú més. // Els que ja havien passat marxen cap a / l'oest, cap a Moscou. // CONTINUARÀ |
| `SD_END02_TEXT` | The range is closed for the day. // The campaign begins from New Game. | El camp de tir tanca per avui. // La campanya comença a «Nova partida». |

### Armas: nombre y mensaje de recogida

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

### Munición, salud, blindaje y mapa (mensajes de recogida)

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

### Pases y puertas

| id | EN | CA |
|---|---|---|
| `SD_PICKUP_BLUEPASS` | Blue pass. | Passi blau. |
| `SD_PICKUP_YELLOWPASS` | Yellow pass. | Passi groc. |
| `SD_PICKUP_REDPASS` | Red pass. | Passi vermell. |
| `PD_BLUECO` | You need a blue pass to activate this object | Necessites un passi blau per activar aquest objecte |
| `PD_YELLOWCO` | You need a yellow pass to activate this object | Necessites un passi groc per activar aquest objecte |
| `PD_REDCO` | You need a red pass to activate this object | Necessites un passi vermell per activar aquest objecte |

### Enemigos y el General

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

### Muertes en multijugador (%o víctima, %k quien mata)

| id | EN | CA |
|---|---|---|
| `SD_OB_ICEAXE` | %o met %k's ice axe. | %o ha topat amb el piolet de %k. |
| `SD_OB_TOKAREV` | %o was shot by %k's Tokarev. | %k ha abatut %o amb la Tokarev. |
| `SD_OB_IZH` | %o took both barrels from %k. | %o s'ha menjat els dos canons de %k. |
| `SD_OB_PPSH` | %o was cut down by %k's PPSh-41. | El PPSh-41 de %k ha segat %o. |
| `SD_OB_RPG7` | %o was blown apart by %k's RPG-7. | L'RPG-7 de %k ha fet miques %o. |
| `SD_OB_ROKS3` | %o burned under %k's ROKS-3. | El ROKS-3 de %k ha rostit %o. |
| `SD_OB_KATYUSHA` | %o caught %k's whole salvo. | %o s'ha empassat tota la salva de %k. |

### Aviso al morir (nuevo, v1.1) y pausa

| id | EN | CA |
|---|---|---|
| `SD_DEATH_PROMPT` | Press %s to continue | Prem %s per continuar |
| `SD_PAUSE_SIGN` **Q12** | M_PAUSE | M_PAUSE |

### Mensajes al salir (cada uno termina con «(Prem Y per sortir.)», omitido aquí)

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

### Créditos (una línea de pantalla por id, máx. 40 caracteres)

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

Ids no listados (no se leen como texto o casi nunca se ven): `PD_BLUEC`, `PD_REDC`, `PD_YELLOWC`, `SD_SBAR_ARMS_IMAGE`, `SD_SBAR_IMAGE`.
