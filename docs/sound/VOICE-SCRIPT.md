# Voice script — the enemy voice takes, for the CEO

Living document. Owner: `sound-designer`. Created 2026-10-13 (F5) under
**D36**: the CEO provides the enemy voices, recorded by himself or generated
with AI; the Reich speaks **real German**, the Liberty Legion **real
English**; the General's order is **"Vorwärts."**; D11 and D12 still bind
(real military callouts and combat cries, never the regime's slogans).
Russian mirror: `docs/ru/sound/VOICE-SCRIPT.md`, **not yet written** (D34:
synced in a batch at the phase close).

Where the lumps, the processing chains and the rights live:
`docs/sound/ENEMY-SOUNDS.md` (§4 voice rules and chains, §5 the cards).
This document only says **what to say and how to record it**. The
recording instructions come first and are in Spanish because they are for
the CEO (D7: the CEO is addressed in Spanish).

---

## 0. Instrucciones para el CEO (español)

### 0.1 Qué hay que hacer, en cinco líneas

1. Grabar (o generar con IA) las **22 filas obligatorias** de las tablas del
   §1 (frases y gritos): **89 tomas** en total. Hay 4 filas opcionales de
   criaturas, 12 tomas más (§1.4).
2. Tiempo estimado: **30-45 minutos** de grabación con el móvil, en una
   sola sesión, más 10 minutos para dejar los ficheros. Es una estimación
   mía, no medida.
3. Dejar los ficheros en `work/audio/voice_takes/` (está en gitignore; no
   entra en git ni en el PK3) con los nombres del §0.5.
4. Escribir en el chat una línea: «Las tomas de voz son mías y las publico
   bajo CC BY-NC-SA 4.0 (D15)». Tu voz reconocible es un dato personal: sin
   esa línea no se usa.
5. Si usas IA para alguna toma: rellenar el registro del §0.7. Sin registro
   no se usa.

Después yo corto, elijo la mejor toma de cada fila, la proceso (§2) y te la
traigo para escucharla antes de que nada entre en `src/sounds/`.

### 0.2 El móvil

- **Formato:** el de mayor calidad que dé la app. En iPhone, *Ajustes →
  Notas de voz → Calidad de audio → Sin pérdida*. En Android, la grabadora
  del sistema en calidad alta, o cualquier app que grabe **WAV**.
- WAV a 44,1 o 48 kHz es lo ideal; si el móvil sólo da M4A/AAC, vale, en su
  calidad máxima. **No conviertas tú el formato**: mándame el original.
- **Nada de efectos:** sin filtro de ruido, sin «mejora de voz», sin
  normalizar, sin recortar. Todo eso lo hago yo; si llega procesado no se
  puede deshacer.
- Modo avión durante la sesión (una notificación arruina una toma).

### 0.3 La habitación

- Una habitación **pequeña y con cosas blandas**: dormitorio con armario
  abierto lleno de ropa, cortinas, cama. **Nunca** baño, cocina, pasillo o
  salón vacío: el eco se queda pegado a la voz y el Reich tiene que sonar
  **seco**.
- Apaga ventilador, aire acondicionado, ordenador ruidoso; aléjate de la
  nevera y de la ventana a la calle.
- Al empezar cada sesión, graba **5 segundos de silencio** de la habitación
  sin moverte (lo uso para limpiar el ruido de fondo).

### 0.4 Distancia y voz

- El móvil apoyado en algo estable (una pila de libros), con el micrófono
  (abajo del todo en casi todos los móviles) **a un palmo y medio, 20-30 cm**,
  y un poco de lado, a unos 45°, para que las «p» y las «t» no peguen golpes.
- **Gritos** (las filas marcadas «fuerte»): échate atrás a **40-50 cm**. Antes
  de la sesión haz una prueba con el grito más fuerte («Feind!») y escúchala:
  si suena rota o rascada, aléjate más. Una toma saturada no se arregla.
- **El General**: cerca, 20 cm, y **bajito**. No pongas voz grave a la fuerza:
  ya bajo yo el tono después (−4 semitonos). Voz natural, lenta, tranquila.
- Entre toma y toma, **un segundo de silencio**. Varía un poco cada toma
  (más corta, más cansada, más seca): las tomas distintas valen más que
  las repetidas.
- Interpretación: son **soldados, no villanos de película**. Nada de acento
  exagerado, ni alemán de caricatura ni tejano: el tono del juego es serio
  (D11).

### 0.5 Ficheros y nombres

- **Un fichero por fila** de las tablas, con todas sus tomas seguidas
  (separadas por ese segundo de silencio). Yo las corto.
- Nombre: `<fila>_<lump>_<fecha>.<ext>`, por ejemplo
  `R04_SDRRISIT_20261014.wav` o `G02_SDGENSUM_20261014.m4a`.
- Si una fila sale de IA: `<fila>_<lump>_ai_<herramienta>_<fecha>.<ext>`, por
  ejemplo `L04_SDLTRSIT_ai_herramientaX_20261014.wav`.
- El silencio de la habitación: `ROOMTONE_<fecha>.<ext>`.
- Todo en **`work/audio/voice_takes/`** (créala si no existe). Si grabas en
  varias sesiones o habitaciones, una subcarpeta por sesión
  (`work/audio/voice_takes/2026-10-14/`), cada una con su `ROOMTONE`.
- Opcional, un `work/audio/voice_takes/NOTES.txt` con: fecha, móvil, app y
  habitación. Me sirve para igualar sesiones.

### 0.6 Pronunciación del alemán (aproximada, para un hispanohablante)

| Frase | Se dice más o menos | Ojo |
|---|---|---|
| **Vorwärts.** | «FÓR-verts» | La «w» suena «v»; la «ä» es una «e» abierta; la «r» final de «vor» casi no suena; termina en «ts» seco. |
| Feind! | «FAINT» | Una sola sílaba, la «d» final suena «t». |
| Da! | «DAA» | |
| Kontakt! | «kon-TAKT» | |
| Stellung halten. | «SHTÉ-lung JÁL-ten» | «St» inicial = «sht»; la «h» es aspirada, suave, no una jota española fuerte. |
| Augen auf. | «ÁU-guen AUF» | |
| Ruhe da hinten. | «RÚ-e da JÍN-ten» | Misma «h» suave. |
| Sani… | «SÁ-ni» | Abreviatura de soldado de *Sanitäter*, «sanitario». |

Si dudas con la pronunciación, una voz de IA en alemán leyendo la frase es
una buena referencia de oído, aunque luego grabes tú.

### 0.7 Si usas IA

Cualquier voz generada entra en el registro de licencias como cualquier otro
recurso (D36). **Por cada fichero generado** anota, en
`work/audio/voice_takes/AI-LOG.csv` (o en el chat), una línea con:

| Campo | Ejemplo de lo que hay que poner |
|---|---|
| fichero | `L04_SDLTRSIT_ai_herramientaX_20261014.wav` |
| herramienta | nombre del producto y web |
| versión o modelo | el nombre exacto del modelo/versión que muestre la herramienta |
| fecha | el día en que se generó |
| plan de la cuenta | gratuito o de pago (en muchas herramientas cambia los derechos) |
| licencia de uso | URL de los términos, fecha en que los leíste y **la frase literal** que dice qué puedes hacer con el audio generado |
| voz | qué voz: de catálogo (su nombre/ID) o clonada **de tu propia voz** |
| texto o prompt | el texto exacto y cualquier instrucción de estilo |
| ajustes | idioma, estabilidad, estilo, semilla, si existen |

Reglas, para que la toma sea usable:

- Los términos tienen que permitir **usar y redistribuir** el audio dentro de
  un mod que se publica bajo **CC BY-NC-SA 4.0** (D15). Si los términos sólo
  permiten uso personal, piden atribución incompatible, o prohíben
  redistribuirlo en un paquete, **esa toma no sirve**: dímelo y buscamos
  otra vía.
- **Nunca clonar la voz de otra persona** (actores, personajes históricos,
  conocidos). Sólo voces de catálogo o tu propia voz.
- Guarda el fichero **tal como sale** de la herramienta, sin editar.
- No te recomiendo ninguna herramienta concreta: no he leído los términos de
  ninguna. Los compruebo yo con lo que anotes.

### 0.8 Lo que no se graba (D11, D12, D36)

- **Nada del régimen**: ni saludos, ni cargos ni títulos del partido, ni
  eslóganes, ni canciones, ni consignas. Sólo órdenes militares y gritos de
  combate como los de cualquier ejército.
- **Nada que remita a víctimas reales**: ni palabras asociadas a redadas,
  deportaciones o campos (por ejemplo «Raus!» o «Schnell!» gritados a gente).
  Por eso no están en el guion aunque sean tópicos de película.
- Del lado de la Legión, simétrico: nada de eslóganes patrióticos; sólo
  procedimiento de radio y avisos de combate.
- Si se te ocurre una frase mejor que las mías, adelante, con la misma
  regla: corta, militar, sin régimen. Anótala en `NOTES.txt` con su
  traducción.

---

## 1. The script

How to read the tables. **Row** is the file prefix (§0.5). **Moment** is the
engine event (`sight` = alert, `active` = idle, `pain`, `death`, `summon` =
the General's order). **Dur.** is the target length of the *finished*
sound after cutting; the raw take may be longer. **Takes** is how many to
record in that file. "Loud" means step back to 40-50 cm (§0.4). Lines in
*italics* in the line column are wordless.

Several rows feed the same lump: they are alternatives, and I pick the best
after hearing them. Whether a lump can later play a random choice of two or
three of them is a `SNDINFO` question (`$random`), **NOT VERIFIED** in the
ZDoom wiki yet, and the mod-engineer's to decide; until then, one take wins
per lump.

### 1.1 Fourth Reich rifleman (`SD_ReichRifleman`) — German, chain `REICH-DRY`

Delivery: dry, clipped, flat, disciplined. A soldier, not a villain.

| Row | Lump | Moment | Line (German) | Translation | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| R01 | `SDRRIACT` | idle | Stellung halten. | Hold the position. | Muttered to a comrade, low, bored; heard through a door, not meant to be followed | 1.0-1.5 s | 3 |
| R02 | `SDRRIACT` | idle | Augen auf. | Eyes open. | Same, quieter | 0.8-1.2 s | 3 |
| R03 | `SDRRIACT` | idle | Ruhe da hinten. | Quiet back there. | Same, irritated | 1.0-1.5 s | 3 |
| R04 | `SDRRISIT` | alert | Feind! | Enemy! | One sharp bark, loud. Heard many times a map: must not be tiring | ≤ 0.5 s | 5 |
| R05 | `SDRRISIT` | alert | Da! | There! | Shortest possible bark, loud | ≤ 0.4 s | 3 |
| R06 | `SDRRISIT` | alert | Kontakt! | Contact! | Bark, loud | ≤ 0.6 s | 3 |
| — | `SDRRIATK` | attack | *(no voice)* | — | The rifle crack; our synthesis (`ENEMY-SOUNDS.md` §5.1) | — | 0 |
| R07 | `SDRRIPAI` | pain | *Grunt, cut off ("ngh—")* | — | Hit, surprised, breath knocked out; no word | 0.2-0.3 s | 5 |
| R08 | `SDRRIDTH` | death | *An exhale that breaks* | — | Air going out, a catch in the throat, falling; **no scream** | ~1 s | 5 |
| R09 | `SDRRIDTH` | death | Sani… | Medic… | Optional alternative to R08: barely said, fading | ~1 s | 3 |

### 1.2 Liberty Legion trooper (`SD_LegionTrooper`) — English, chain `LEGION-RADIO`

Delivery: radio procedure, neutral General American, professional and
flat. Speak as if into a handset: a hand cupped near the mouth helps. Crisp
consonants, because the radio will cut the lows and the highs.

| Row | Lump | Moment | Line (English) | Translation (ES) | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| L01 | `SDLTRACT` | idle | Sector four, clear. | Sector cuatro, despejado. | Routine report, bored | 1.2-1.6 s | 3 |
| L02 | `SDLTRACT` | idle | Copy. Holding position. | Recibido. Mantenemos posición. | Routine, a bit tired | 1.2-1.8 s | 3 |
| L03 | `SDLTRACT` | idle | Command, say again? | Mando, repita. | Didn't catch it | 1.0-1.4 s | 3 |
| L04 | `SDLTRSIT` | alert | Contact! | ¡Contacto! | One clipped word, loud | ≤ 0.6 s | 5 |
| L05 | `SDLTRSIT` | alert | Hostile, front! | ¡Hostil, al frente! | Fast, loud | ≤ 0.7 s | 3 |
| L06 | `SDLTRSIT` | alert | Got movement! | ¡Movimiento! | Fast, loud | ≤ 0.7 s | 3 |
| — | `SDLTRATK` | attack | *(no voice)* | — | The shotgun; our synthesis (§5.2 of `ENEMY-SOUNDS.md`) | — | 0 |
| L07 | `SDLTRPAI` | pain | *Grunt ("agh—")* | — | Hit; no word | ~0.3 s | 5 |
| L08 | `SDLTRPAI` | pain | I'm hit! | ¡Me han dado! | Alternative to L07, strained | 0.4-0.5 s | 3 |
| L09 | `SDLTRDTH` | death | *A choked exhale, falling* | — | The voice drops; I add the signal dying | ~1 s | 5 |

### 1.3 The General (`SD_General`) — English, and one German order; chain `GENERAL-SLOT`

He is the Legion's officer commanding both factions (`docs/engine/BESTIARY.md`
§9); he speaks English, and gives the Reich recruits their order in their
own language. **He never shouts.** Low, slow, calm, close to the phone
(20 cm). Natural pitch: I lower it later.

| Row | Lump | Moment | Line | Translation (ES) | Intent | Dur. | Takes |
|---|---|---|---|---|---|---|---|
| G01 | `SDGENSIT` | alert | Engage. | Atacad. | Calm, unhurried; an order, not a cry | 1.0-1.5 s | 5 |
| G02 | `SDGENSUM` | the order (summon) | **Vorwärts.** | Adelante. | **The one line the player must understand.** Calm, final, as if it were obvious. A full stop, not an exclamation mark | ≤ 1.2 s | 8 |
| — | `SDGENMIS` / `SDGENEXP` / `SDGENACT` | attack / impact / idle | *(no voice)* | — | Mechanism and salvo; our synthesis | — | 0 |
| G03 | `SDGENPAI` | pain | *Clipped grunt ("hm.")* | — | Annoyed more than hurt; not a cry | 0.2-0.4 s | 5 |
| G04 | `SDGENDTH` | death | *Long exhale winding down into a low hum that stops* | — | The voice runs down like a machine; I add the mechanism failing. May ring long | 2.5-4 s | 5 |

### 1.4 Optional: creature layers (wordless)

The CC0 packs cover these (`docs/sound/ENEMY-SOUNDS.md` §5.3-§5.6). A human
layer underneath makes them less "library". **Only if there is time left.**

| Row | Lump | Moment | What to do | Dur. | Takes |
|---|---|---|---|---|---|
| C01 | `SDSTOSIT` | alert | A rasping snarl from the throat, as if through a damaged mask | ~0.7 s | 3 |
| C02 | `SDHNDSIT` | alert | A rising shriek-snarl, ending high; not a dog, not a wolf | ≥ 1 s | 3 |
| C03 | `SDDGBSIT` | alert | A hollow wail **with your face inside a metal pot or bucket** (literally) | ~1 s | 3 |
| C04 | `SDPZRSIT` | alert | The lowest roar you can do, slow | ~1.5 s | 3 |

### 1.5 Totals

| Group | Rows | Takes |
|---|---|---|
| Reich rifleman | 9 | 33 |
| Legion trooper | 9 | 33 |
| General | 4 | 23 |
| **Required** | **22** (16 spoken lines, 6 wordless) | **89** |
| Optional creatures | 4 | 12 |

The 22 required rows feed 12 lumps (rifleman ACT, SIT, PAI, DTH; trooper
ACT, SIT, PAI, DTH; General SIT, SUM, PAI, DTH), the twelve voice rows of
`ENEMY-SOUNDS.md` §5.8. Recording time: at
about two seconds per take plus pauses and retries, 89 takes are 15-20
minutes of talking; with set-up, the loudness test and listening back,
**30-45 minutes**. Estimate, not measured.

---

## 2. What happens to the takes afterwards

The recipes are owned by `docs/sound/ENEMY-SOUNDS.md` §4; this is what they
mean for the performance.

| Faction | Chain | What I do | What it means for you |
|---|---|---|---|
| Reich (rifleman) | `REICH-DRY` | High-pass 80 Hz, light saturation, **no reverb**, −2 to −3 semitones, presence at 2-3 kHz | The room's echo cannot be removed and will be heard: record in the deadest room you have |
| Liberty Legion (trooper) | `LEGION-RADIO` | Band-pass 400-3200 Hz, 8-bit crush, clipping, a vocoder edge, a squelch burst at start and end | Only the middle of the voice survives: consonants carry the words, so say them clearly |
| The General | `GENERAL-SLOT` | −4 semitones, narrow band-pass 500-2500 Hz, a short comb (the slot in his face plate), a slow 1.2 s tail | Calm and close; no forced bass. Leave the end of each line clean so the tail can ring |
| Creatures (optional) | per actor, `ENEMY-SOUNDS.md` §5 | Layered under the CC0 material and pitched | Commit fully: odd is good |

Every finished lump comes back to the CEO for listening before anything
enters `src/sounds/`, as with textures and music.

---

## 3. Open points for the PM (not the CEO)

- `src/lumps/LANGUAGE` still prints `SD_GENERAL_ORDER = "The General:
  Recruits - advance!"` (and its `[ru]` twin), a placeholder whose comment
  says it changes with the sound. With D36 the spoken line is "Vorwärts.";
  the printed text is `mod-engineer`'s to align (for example the German word
  with its translation), in EN and RU in the same task (D21).
- `docs/engine/BESTIARY.md` §3, `SDRRIACT` row, still says "a language that
  is not quite German"; D36 replaced that. `mod-engineer`'s file.
