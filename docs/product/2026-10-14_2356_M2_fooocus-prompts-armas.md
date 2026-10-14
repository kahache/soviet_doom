# Fooocus: referencias de manos para las 5 armas que siguen en manos de Freedoom

**Autor:** art-director · **Fecha:** 2026-10-14 23:56 · **Hito:** M2 (arsenal, fase F4)
**Para:** el CEO, con el documento abierto en el PC al lado de Fooocus (http://127.0.0.1:7865).
**Idioma:** las explicaciones están en español porque el documento es para el CEO, como pidió el PM. Los prompts y los negative prompts están en inglés, porque SDXL entiende mejor el inglés. El documento no se copia en `docs/ru/` (D34).

> **En 30 segundos.** Hay cinco armas: IZh, PPSh-41, RPG-7, ROKS-3 y Katyusha de mano. Con **6 tandas obligatorias** del Método A, o con **6 imágenes de entrada** del Método B, cubrimos las cinco: varias armas comparten agarre.
> **Prueba primero el Método B** (§4): metes en Fooocus un fotograma nuestro, con la composición de Doom ya bien, y Fooocus lo convierte en foto. Si no funciona, usa el **Método A** (§5), que es solo texto.
> **Orden:** calibración con la TT-33 (5 min) → PPSh → IZh → RPG-7 → (ROKS-3 solo si el PM lo pide) → Katyusha.

---

## 1. El flujo, siempre el mismo

1. Configura Fooocus una vez con los **ajustes base** (§3).
2. Pega el prompt y el negative prompt del bloque que toque y pulsa **Generate**. Salen **4 imágenes**.
3. Mira cada una con su **checklist** (✅ = guardar, ❌ = descartar).
4. Guarda **la mejor, o las 2 mejores**, en `work/art/reference/` con el **nombre exacto** del bloque (si guardas dos, añade `2`: `ppsh_ready_rh2.png`).
5. Si sale la mano **en espejo** (una mano izquierda que entra por la izquierda cuando pedíamos la derecha por la derecha), **sirve igual**: guárdala con el sufijo `_mirrored` (`ppsh_ready_rh_mirrored.png`) y la volteamos nosotros (D73). Lo que **no sirve** es un brazo cruzado: una mano derecha que entra por la izquierda, o una izquierda que entra por la derecha.
6. Si de 4 no hay ninguna buena, genera otras 4 (el seed es aleatorio). Si tras **3 tandas** sigue sin salir, para y avisa al PM con la mejor de las malas: así ajustamos el prompt y no gastas más tiempo.
7. Avisa al PM con una línea: *"PPSh listo: ppsh_ready_rh.png, ppsh_ready_lh.png"*.

**Qué importa y qué no.** Lo que importa es la mano, la muñeca, la manga, la pose del agarre y la luz. **El arma de la foto da igual**: la dibujamos nosotros y la metemos bajo los dedos con `tools/art/hand_ref.py`. Un fondo liso y que contraste (cielo, nieve) hace que el recorte salga limpio.

---

## 2. Qué armas, qué poses y cuántas referencias

Los fotogramas de **disparo y retroceso no necesitan referencia**: los sacamos del fotograma de reposo girándolo y desplazándolo y añadiendo el fogonazo. Solo necesitamos foto de las poses distintas.

| Arma (slot) | Clase y sprite de Doom | Estados que usa nuestro ZScript | Manos en pantalla | Poses que necesitan foto | Imágenes a guardar |
|---|---|---|---|---|---|
| **IZh-58**, escopeta de dos cañones (3) | `SD_Izh` sustituye a Shotgun, `SHTG` | A reposo; B, C retroceso; **D abierta para recargar** (D → C → B → A) | izquierda bajo el guardamanos; derecha al recargar | **reposo** (izquierda) y **abierta recargando** (las dos) | 2 (+1 opcional) |
| **PPSh-41** (4), el icono del mod | `SD_Ppsh` sustituye a Chaingun, `CHGG` | A, B alternan al disparar | **las dos**: izquierda delante, derecha en la culata y el gatillo | **reposo**, una foto por mano | 2 |
| **RPG-7** (5) | `SD_Rpg7` sustituye a RocketLauncher, `MISG` | A reposo; B disparo | derecha en la empuñadura; la izquierda delante es opcional | **reposo** (derecha) | 1 (+1 opcional) |
| **ROKS-3**, lanzallamas (6) | `SD_Roks3` sustituye a PlasmaRifle, `PLSG` | A disparo; B enfriamiento | las dos, igual que la PPSh | **ninguna nueva**: usa las manos de la PPSh | 0 (+2 opcionales) |
| **Katyusha de mano** (7, secreta, D68) | `SD_HandKatyusha` sustituye a BFG9000, `BFGG` | A carga 20 tics; B disparo | **las dos**: izquierda en la barra delantera, derecha en la empuñadura | **reposo**: izquierda nueva; la derecha es la del RPG | 1 (+1 opcional) |

**Agarres que se reutilizan** (cada uno se genera una sola vez):
- **Derecha, empuñadura con el índice en el gatillo** (`rpg7_ready_rh`): sirve también para la Katyusha.
- **Derecha en la garganta de una culata de madera** (`ppsh_ready_rh`): sirve también para la ROKS-3 y, si hace falta, para la IZh.
- **Izquierda sosteniendo desde abajo un palo horizontal** (`ppsh_ready_lh`): sirve también para la ROKS-3. Para la IZh, el ángulo cambia lo suficiente como para generar la suya.

Cómo lo resuelve Doom, para comparar: en Freedoom, `CHGG`, `MISG` y `PLSG` **no enseñan manos** (el arma tapa todo); `SHTG` B-D enseñan la mano derecha bombeando la corredera, y `BFGG` solo asoma unos dedos. Nosotros enseñamos más mano, como hace la TT-33 aprobada (D63).

---

## 3. Ajustes base de Fooocus (los dos métodos)

Arranca con `Z:\Fooocus\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0\run_realistic.bat` y **cambia lo que está en negrita** respecto al preset:

| Dónde | Ajuste | Valor |
|---|---|---|
| Settings → Performance | Performance | **Quality** (60 pasos; es lo que usaste hoy) |
| Settings → Aspect Ratios | relación de aspecto | **1152×896** (el preset trae 896×1152 en vertical: cámbialo) |
| Settings | Image Number | **4** |
| Settings | Random (seed) | ✔ marcado |
| Styles | **desmarca** | **Fooocus V2** y **Fooocus Photograph** |
| Styles | **marca** (escribe "iphone" en *Search Styles*) | **Photo Iphone Photographic** + **Fooocus Negative** |
| Models | Base Model | `realisticStockPhoto_v20.safetensors` (ya instalado) |
| Models | Refiner | None |
| Models | LoRA 1 `SDXL_FILM_PHOTOGRAPHY_STYLE_V1` | **None** (o peso 0): añade grano y tono vintage, y eso ensucia el recorte |
| Advanced | Guidance Scale | **4** (el preset trae 3; con 4 obedece mejor un prompt largo; si la piel sale de plástico o saturada, vuelve a 3) |
| Advanced | Image Sharpness | 2 (por defecto) |

**Por qué estos cambios (lo vi en tu log de hoy, `Fooocus/outputs/2026-10-14/log.html`).** Pediste *"plain flat light grey seamless studio background"* y salieron montañas. El log muestra la causa: **Fooocus V2** añadió al prompt *"scenic, epic, surreal, futuristic, magical atmosphere…"* y **Fooocus Photograph** añadió *"cinematic… hbo dark moody, grainy, vignette, vintage, found footage"*. Las dos empujan hacia el paisaje y el viñeteado. **Photo Iphone Photographic** solo añade *"large depth of field, deep depth of field, highly detailed"*: foto nítida, sin bokeh ni viñeta. **Fooocus Negative** añade una lista de malformaciones de manos al negativo. Los checkpoints instalados son `juggernautXL_v8Rundiffusion`, `realisticStockPhoto_v20` y `animaPencilXL_v500` (este último es anime; no lo uses).

**Lo importante va al principio del prompt.** SDXL hace más caso a las primeras palabras, por eso todos los prompts empiezan por la mano, el lado de la pantalla y el agarre. Fooocus acepta pesos del tipo `(right hand:1.3)`.

---

## 4. Método B (PROBAR PRIMERO): de fotograma Doom a foto (idea del CEO)

### 4.1 Por qué debería ir más rápido, y sus riesgos
- **Ventaja:** el fotograma de entrada ya tiene la **composición, el punto de vista, la escala y la posición en pantalla de Doom** (la escala D57 y la colocación de nuestros bocetos). Nos ahorramos adivinar la cámara, que es justo lo que falló con las referencias 2 y 3 del piolet (el mitón visto por detrás y el agarre al revés).
- **Riesgo 1, que salga pixelado:** SDXL puede copiar los escalones de los píxeles. Por eso las entradas ya vienen **suavizadas** (bicúbico más un desenfoque de un tercio de píxel), y en el negativo va `pixelated, blocky`.
- **Riesgo 2, que invente un sexto dedo:** nuestros bocetos tienen los dedos gruesos y por bloques, y el control por bordes puede convertir un bloque en dos dedos. Se corrige bajando el **Weight** de PyraCanny y con el negativo (tabla en §4.6).
- **Riesgo 3, que herede colores en la vía Vary:** los bocetos 2D llevan guante marrón y la manga con rayas de telnyashka. PyraCanny solo mira los bordes y no hereda colores; Vary sí los hereda. Por eso la receta principal es PyraCanny.
- **Primera vez que uses PyraCanny, CPDS o ImagePrompt:** Fooocus **descarga** el modelo de control desde su propio repositorio (`huggingface.co/lllyasviel/misc`). Hoy en `models/controlnet` solo está `fooocus_ip_negative`. Descargas: `control-lora-canny-rank128.safetensors` (PyraCanny), `fooocus_xl_cpds_128.safetensors` (CPDS) y, para ImagePrompt, `clip_vision_vit_h.safetensors` más `ip-adapter-plus_sdxl_vit-h.bin`. Tamaños **SIN VERIFICAR**: unos 0,4 GB cada modelo de control y unos 2-3 GB el par de ImagePrompt. Es tu máquina: decides tú. **Vary (Strong) no descarga nada.**

### 4.2 Regla de licencia (vinculante)
Como entrada **solo** se usan sprites de **Freedoom (BSD-3)** o **fotogramas nuestros**. **NUNCA sprites de Doom de id Software** (`DOOM.WAD`, `DOOM2.WAD`): son comerciales y no se pueden redistribuir, y una foto derivada de ellos tampoco. Doom de id solo vale como referencia de estilo, mirándolo. Todas las entradas de §4.3 salen de `iwads/freedoom2.wad` o de `work/art/`.

### 4.3 Imágenes de entrada ya preparadas: `work/art/reference/doom_inputs/`
Todas miden 1152×896 (la relación de aspecto de Fooocus), sobre un **cielo liso azul pálido**. `_index.png` las muestra todas juntas. `_close` = recortada alrededor del arma y las manos, con las manos más grandes, que es **la que hay que usar primero**. `_full` = la pantalla Doom entera de 320×200, para cuando quieras la composición completa.

| Arma / pose | Entrada principal (nuestra) | Origen | Alternativa Freedoom (BSD-3) |
|---|---|---|---|
| **Calibración** | `tt33_ready_ours_close.png` | `weapons_fd/tt33/SDTTA0`: la TT-33 aprobada (D63), con manos de Freedoom recoloreadas | — |
| PPSh reposo | `ppsh_ready_ours_close.png` | boceto 2D `SDPPA0` | `ppsh_ready_fd-CHGGA0_*` (sin manos) |
| IZh reposo | `izh_ready_ours_close.png` | boceto 2D `SDIZA0` | `izh_ready_fd-SHTGA0_*` (casi sin manos) |
| IZh abierta | `izh_open_ours_close.png` | boceto 2D `SDIZD0` | `izh_open_fd-SHTGD0_*` (mano derecha en una corredera) |
| RPG-7 reposo | `rpg7_ready_ours_close.png` | boceto 2D `SDRLA0` | `rpg7_ready_fd-MISGA0_*` (sin manos) |
| ROKS-3 reposo | `roks3_ready_ours_close.png` | boceto 2D `SDRKA0` | `roks3_ready_fd-PLSGA0_*` (sin manos) |
| Katyusha reposo | `katyusha_ready_ours_close.png` | boceto 2D `SDHKA0` | `katyusha_ready_fd-BFGGA0_*` (asoman los dedos) |
| Consistencia de mano | `ref_hand_rh.png` | tu `hand grabbing mirrored.png`, volteado a mano derecha (el original no se ha tocado) | — |

Las versiones de Freedoom casi no enseñan manos, así que **solo sirven para la variante cartoon o como composición**; para las manos usa siempre las nuestras. Las entradas se regeneran con `work/art/reference/doom_inputs/make_doom_inputs.py`.

### 4.4 Receta B1, la principal: Image Prompt con PyraCanny
1. Marca **Input Image** (debajo del prompt) y abre la pestaña **Image Prompt**.
2. Marca **Advanced** (debajo de las 4 casillas de imagen) para ver *Type*, *Stop At* y *Weight*.
3. **Casilla 1:** arrastra la entrada `_close` del arma. Type **PyraCanny**, **Stop At 0.5**, **Weight 0.8**.
4. **Casilla 2** (opcional, mantiene los volúmenes y la luz): **la misma imagen**. Type **CPDS**, **Stop At 0.35**, **Weight 0.5**.
5. **Casilla 3** (opcional, para que la mano sea la misma en todas las armas): `ref_hand_rh.png`, o tu mejor foto de calibración (§4.7) cuando la tengas. Type **ImagePrompt**, **Stop At 0.5**, **Weight 0.35**. Con más peso se cuelan el piolet y las montañas.
6. Ajustes base de §3, el prompt de §4.7 y **Generate** (4 imágenes).

### 4.5 Receta B2, si B1 no respeta la posición de la mano: Vary (Strong) más PyraCanny
1. **Input Image** → pestaña **Upscale or Variation** → arrastra la misma entrada → elige **Vary (Strong)** (eso es un denoise de 0.85).
2. **Advanced** → marca **Developer Debug Mode** → pestaña **Control** → marca **Mixing Image Prompt and Vary/Upscale**.
3. Pestaña **Image Prompt**, casilla 1: la misma entrada, **PyraCanny, Stop At 0.5, Weight 0.7**.
4. Mismo prompt. Si copia demasiado el boceto (bloques, guante marrón): en *Developer Debug Mode*, sube **Forced Overwrite of Denoising Strength of "Vary"** a **0.9**. Si se inventa otra cosa, bájalo a **0.75**.

### 4.6 Si algo sale mal (los dos métodos B)

| Síntoma | Cambio |
|---|---|
| Sale pixelado o con escalones | PyraCanny **Stop At 0.35-0.4** y **Weight 0.6** (menos tiempo atado a los bordes, más libertad para pintar piel), quita CPDS. En *Developer Debug Mode → Control → Canny*: Low **100**, High **200** (ignora los bordes pequeños) |
| No respeta la composición (la mano en otro sitio, el arma girada) | PyraCanny **Stop At 0.6-0.7** y **Weight 1.0**, y añade CPDS. Más *Stop At* = más fiel a los bordes, **pero también a los bloques**: súbelo solo si hace falta |
| Sexto dedo o dedos fundidos | **Weight 0.6**, regenera; el negativo ya lo pide. Si persiste, descarta y pasa a B2 o al Método A |
| Guante marrón o manga a rayas (heredados del boceto) | Pasa en B2: vuelve a B1. En el prompt, `(bare skin:1.3)` y `(plain olive sleeve:1.2)` |
| Paisaje de fondo | Comprueba que **Fooocus V2** y **Fooocus Photograph** están desmarcados; pon `(plain pale blue sky background:1.3)` |
| Sale en espejo | Vale: guárdala con `_mirrored` |

### 4.7 Prompts del Método B (foto y cartoon)

**Ajustes de la variante foto:** los de §3 (realisticStockPhoto, estilos **Photo Iphone Photographic + Fooocus Negative**).
**Ajustes de la variante cartoon** (puede pixelar más limpio; pásanos lo que salga): Base Model **`juggernautXL_v8Rundiffusion`**. Estilos: marca solo **Cel Shaded Art**, y **desmarca Fooocus Negative** (su negativo incluye *"cartoon, anime, drawing, graphic"* y anularía el estilo). Si sale demasiado plano, añade **SAI Comic Book**. Guidance 4.

**Negative común de B, foto** (pégalo tal cual):
```
pixelated, pixel art, blocky, jagged edges, low resolution, video game, 3d render, cgi, cartoon, drawing, painting, illustration, plastic skin, toy, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, extra arms, crossed arms, gloves, striped sleeve, wristwatch, ring, tattoo, fisheye, distorted perspective, motion blur, bokeh, depth of field, vignette, film grain, face, person, people, landscape, mountains, trees, buildings, text, watermark, logo, signature
```
**Negative común de B, cartoon:**
```
photo, photorealistic, pixelated, pixel art, blocky, jagged edges, noisy, blurry, gradient banding, extra fingers, six fingers, fused fingers, missing fingers, extra hands, third hand, crossed arms, gloves, striped sleeve, wristwatch, face, person, landscape, background details, text, watermark, logo, signature
```

Para la variante cartoon, cambia el principio del prompt de foto *"first-person view photograph, …"* por **"cel shaded comic illustration, clean bold black outlines, flat colors with three shades per material, first-person view, …"** y quita *"realistic photograph, 28mm lens"* del final.

| # | Entrada (casilla 1 y 2) | Prompt de foto (inglés) | Guardar como |
|---|---|---|---|
| B0 calibración | `tt33_ready_ours_close.png` | ver abajo | `tt33_ready_fromdoom_photo.png` / `_cartoon.png` |
| B1 PPSh | `ppsh_ready_ours_close.png` | ver abajo | `ppsh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B2 IZh reposo | `izh_ready_ours_close.png` | ver abajo | `izh_ready_fromdoom_photo.png` / `_cartoon.png` |
| B3 IZh abierta | `izh_open_ours_close.png` | ver abajo | `izh_open_fromdoom_photo.png` / `_cartoon.png` |
| B4 RPG-7 | `rpg7_ready_ours_close.png` | ver abajo | `rpg7_ready_fromdoom_photo.png` / `_cartoon.png` |
| B5 ROKS-3 | `roks3_ready_ours_close.png` | ver abajo | `roks3_ready_fromdoom_photo.png` / `_cartoon.png` |
| B6 Katyusha | `katyusha_ready_ours_close.png` | ver abajo | `katyusha_ready_fromdoom_photo.png` / `_cartoon.png` |

**B0, calibración con la TT-33 (hazla la primera: 1 tanda, unos 5 min).** Ya sabemos cómo debe quedar, así que nos dice si el Método B funciona. Si sale bien, esta foto pasa a ser la **mano modelo** de la casilla 3 en el resto de armas.
```
first-person view photograph, seen through the eyes of the shooter, (two bare hands:1.2) holding a black steel pistol straight ahead at the center of the frame with a two-handed grip, the right hand wrapped around the grip and the left hand cupping it from below, the thumbs side by side along the left of the frame, knuckles toward the camera, exactly five fingers on each hand, lightly tanned skin, olive drab cotton sleeves of a WWII Soviet army tunic at the bottom edge, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B1, PPSh-41**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage wooden submachine gun with a round drum magazine, the gun runs diagonally from the bottom right toward the center of the frame, the left hand comes in from the bottom left and holds the front of the gun from below, the right hand at the bottom right grips the wooden stock with the index finger on the trigger, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B2, IZh en reposo**
```
first-person view photograph, seen through the eyes of a hunter, a side-by-side double barrel shotgun with a wooden stock held low, the two steel barrels point forward toward the center of the frame, (bare left hand:1.2) coming in from the bottom left holds the wooden fore-end from below, palm up, fingers curled over the far side, thumb along the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B3, IZh abierta (recargando)**
```
first-person view photograph looking down at a broken-open side-by-side double barrel shotgun held at waist height, the barrels tipped down on the hinge and the two empty chambers facing up, (bare right hand:1.2) pushing two red paper shotgun shells into the chambers with thumb and index finger, the left hand under the barrels holding the gun open, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain flat white snow on the ground as background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B4, RPG-7**
```
first-person view photograph, seen through the eyes of a soldier, a long thick olive green launcher tube rests on the right shoulder and points forward, the tube runs diagonally from the bottom right toward the center of the frame, (bare right hand:1.2) at the bottom right grips the launcher with a firm fist, knuckles toward the camera, thumb wrapped around the near side, exactly five fingers, lightly tanned skin, plain olive drab cotton sleeve of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B5, ROKS-3**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) holding a vintage rifle-shaped flamethrower gun with a wooden stock and a long thin steel nozzle, the gun runs diagonally from the bottom right toward the left of the frame, the left hand comes in from the bottom left and holds the barrel from below, the right hand at the bottom right grips the wooden stock, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**B6, Katyusha de mano**
```
first-person view photograph, seen through the eyes of a soldier, (two bare hands:1.2) carrying a heavy olive green steel rack of six rocket rails on the right shoulder, the left hand comes in from the bottom left and grips a horizontal steel bar at the front of the rack with an overhand grip, knuckles up, the right hand at the bottom right grips a vertical steel handle under the rack, exactly five fingers on each hand, lightly tanned skin, plain olive drab cotton sleeves of a WWII Soviet army tunic, plain pale blue sky background, soft daylight from the upper left, sharp focus, realistic photograph, 28mm lens
```

**Checklist del Método B** (además de la general de §6): la mano está **en el mismo sitio que en la entrada**. Es piel de verdad, sin bloques. La manga es oliva lisa, **sin rayas**. ❌ Descarta si los dedos siguen el contorno de bloque del boceto (salchichas), si sale un guante, o si el arma tapa los dedos en vez de quedar los dedos por encima del arma.

---

## 5. Método A (RESERVA): solo texto

Ajustes base de §3, sin Input Image. Opcional, para que la mano sea la misma en todas las armas: **Input Image → Image Prompt**, casilla 1 con `doom_inputs/ref_hand_rh.png` (o tu mejor foto de calibración), **Type ImagePrompt, Stop At 0.5, Weight 0.35**. Requiere la descarga de §4.1.

**Por qué objetos sustitutos.** Si nombramos "Soviet submachine gun", SDXL dibuja escenas de guerra, soldados y paisajes. Si le damos un **objeto de la misma forma y tamaño** (una culata de escopeta de caza, un palo de escoba, un tubo), la mano agarra igual y el fondo se queda limpio. Lo único que importa es el agarre.

**Negative común A, para una mano DERECHA** (pégalo entero):
```
left hand, two left hands, arm entering from the left, crossed arms, extra fingers, six fingers, four fingers, fused fingers, missing fingers, long fingers, sausage fingers, claw, twisted wrist, broken wrist, extra hands, third hand, extra arms, floating hand, disconnected hand, cropped hand, cut-off fingers, out of frame, gloves, glove, wristwatch, bracelet, ring, tattoo, nail polish, striped sleeve, rolled-up sleeve, fisheye, distorted perspective, wide angle distortion, motion blur, bokeh, depth of field, vignette, film grain, dark, low light, face, person, people, head, legs, landscape, mountains, trees, buildings, clouds, busy background, text, watermark, logo, signature, label, cartoon, drawing, painting, illustration, 3d render, cgi, plastic skin
```
**Negative común A, para una mano IZQUIERDA:** el mismo, cambiando las 3 primeras entradas por `right hand, two right hands, arm entering from the right`.

---

### A1. PPSh-41, mano derecha en la culata. `ppsh_ready_rh.png` (OBLIGATORIA; sirve también para la ROKS-3 y la IZh)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's right hand:1.3) and forearm entering the frame from the bottom right corner, the right hand grips the narrow curved wooden wrist of an old hunting rifle stock, the stock runs diagonally from the bottom right corner up toward the center of the frame, firm trigger grip: the back of the hand and the four knuckles face the camera, thumb wrapped over the top of the wood, middle, ring and little fingers curled around the underside, index finger lying straight along the side of the wood, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand fills the lower right quarter of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Dorso de la mano y los 4 nudillos de cara a la cámara · pulgar por encima de la madera · índice estirado aparte · la manga oliva sale por el borde inferior · cielo liso.
❌ Palma hacia la cámara · el índice cerrado como un puño · madera delante de los dedos · culata vertical.

### A2. PPSh-41, mano izquierda delante. `ppsh_ready_lh.png` (OBLIGATORIA; sirve también para la ROKS-3)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand supports a thick round wooden broom handle from below, the handle is held level and points forward and slightly up toward the center of the frame like the front grip of a rifle, palm up under the wood, four fingers curled up around the far side so the fingertips show on top of the wood, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the hand in the lower left third of the frame, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ La madera pasa **por encima de la palma**, con las puntas de los dedos asomando por arriba · pulgar en el lado cercano · antebrazo desde abajo a la izquierda.
❌ La mano agarrando por arriba como un bastón · la madera delante de los dedos (fue el fallo de la ref. 3) · el palo apuntando a la cámara.

### A3. IZh, mano izquierda bajo los cañones. `izh_ready_lh.png` (OBLIGATORIA)
```
first-person point of view photograph, seen through the eyes of a hunter, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand holds the wooden fore-end of a side-by-side double barrel hunting shotgun from below, the two steel barrels point straight ahead to the center of the frame, the gun is low in the frame at the bottom center, palm up under the wood, four fingers curled around the far side, thumb lying along the near side, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Los cañones van **recto al centro** · la mano debajo del guardamanos, con los dedos por el lado lejano.
❌ Escopeta de corredera (pump) · la mano en el gatillo · los cañones cruzando la pantalla de lado a lado.
*Opcional:* `izh_ready_rh.png`, solo si el PM lo pide: es A1 con *"a side-by-side double barrel hunting shotgun"* en lugar de *"an old hunting rifle"* y los cañones recto al centro.

### A4. IZh abierta, recargando. `izh_open_rh.png` (OBLIGATORIA; salen las dos manos, y es normal)
Negative: el común de mano derecha **sin** `third hand`, `extra hands` ni `arm entering from the left` (la izquierda sí aparece).
```
first-person point of view photograph looking down at waist height, seen through the eyes of a hunter, a broken-open side-by-side double barrel hunting shotgun held in the center of the frame, the barrels tipped down on the hinge and the two empty chambers facing up toward the camera, (the right hand:1.3) coming in from the bottom right pushes two red paper shotgun shells into the chambers between thumb and index finger, the left hand coming in from the bottom left holds the barrels from below to keep the gun open, exactly five fingers on each hand, natural proportions, bare skin, lightly tanned, short clean nails, both forearms covered by plain olive drab cotton sleeves of a WWII Soviet army tunic, the sleeves leave the picture at the bottom edge, plain flat white snow on the ground as the only background, soft daylight from the upper left, sharp focus on the hands, 28mm lens, natural perspective, realistic photograph
```
✅ Escopeta claramente **abierta** (bisagra doblada) · cartuchos entre el pulgar y el índice de la derecha · las dos mangas salen por abajo · fondo de nieve lisa.
❌ Escopeta cerrada · más de dos manos · los cartuchos flotando · una mano entrando por arriba.

### A5. RPG-7, mano derecha en la empuñadura. `rpg7_ready_rh.png` (OBLIGATORIA; sirve también para la Katyusha)
```
first-person point of view photograph, seen through the eyes of the holder, a long thick olive green metal pipe rests on the right shoulder and points forward, the pipe runs diagonally from the bottom right corner up toward the center of the frame, (a single adult man's right hand:1.3) grips a black vertical pistol grip under the pipe at the lower right of the frame, the back of the hand and the knuckles face the camera, thumb wrapped around the left side of the grip, index finger curled on a trigger, the other three fingers wrapped around the grip, wrist straight, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Puño cerrado alrededor de una empuñadura **vertical** · nudillos hacia la cámara · tubo por encima de la mano · la manga sale por abajo a la derecha.
❌ La mano agarrando el tubo por encima · un taladro o una herramienta en lugar de la empuñadura · el tubo apuntando a la cámara.
*Opcional:* `rpg7_ready_lh.png`, la mano izquierda delante: A2 cambiando *"a thick round wooden broom handle"* por *"the underside of a thick olive green metal pipe"*.

### A6. Katyusha de mano, mano izquierda en la barra. `katyusha_ready_lh.png` (OBLIGATORIA; la derecha es la de A5)
```
first-person point of view photograph, seen through the eyes of the holder, (a single adult man's left hand:1.3) and forearm entering the frame from the bottom left, the left hand grips a thick horizontal steel pipe at chest height with an overhand grip, the pipe crosses the frame from the left edge to the center, knuckles up and toward the camera, four fingers wrapped over and around the pipe, thumb under the pipe, wrist slightly bent down, the hand left of center, exactly five fingers, natural proportions, bare skin, lightly tanned, short clean nails, the forearm covered by the plain olive drab cotton sleeve of a WWII Soviet army tunic (gymnastyorka) with a buttoned cuff at the wrist, the sleeve leaves the picture at the bottom edge, the upper half of the frame is plain pale blue sky, soft daylight from the upper left, sharp focus on the hand, 28mm lens at eye level, natural perspective, realistic photograph
```
✅ Agarre **por encima** (dorso arriba, nudillos visibles) · tubo horizontal · antebrazo desde abajo a la izquierda.
❌ Palma hacia arriba · la mano colgando de una barra de gimnasio con el brazo estirado hacia arriba · una barra vertical.

### A7. ROKS-3 (OPCIONAL: solo si el PM dice que las manos de la PPSh no encajan)
`roks3_ready_rh.png` / `roks3_ready_lh.png`: A1 y A2 con estos cambios: *"held low at hip height, pointing slightly down toward the center of the frame"* en lugar de *"diagonally … up toward the center"*, y en A2 *"a long thin steel pipe"* en lugar de *"a thick round wooden broom handle"*.

---

## 6. Checklist general (todas las imágenes)

**✅ Guardar si:**
- [ ] Es **una mano de verdad** con **5 dedos**, sin dedos fundidos y con nudillos visibles.
- [ ] Es la **mano pedida** entrando por **su lado** (o el espejo exacto → `_mirrored`).
- [ ] El **antebrazo y la manga salen por el borde inferior** de la imagen (si la manga acaba dentro del cuadro, se ve el corte en pantalla; fue el fallo de la ref. 3).
- [ ] La **manga es oliva, lisa, de algodón**, con el puño en la muñeca: sin guante, sin rayas, sin reloj.
- [ ] Los **dedos quedan por encima del objeto** (el objeto pasa *dentro* del puño, no por delante de los dedos).
- [ ] **Fondo liso y claro** (cielo o nieve) alrededor de toda la mano.
- [ ] Luz suave desde arriba a la izquierda, sin sombras duras sobre los dedos.
- [ ] Mano nítida, sin bokeh, sin grano y sin viñeta.

**❌ Descartar si:** sale un mitón (la mano vista por detrás, ref. 2) · el agarre está al revés (la mano vista desde abajo, ref. 3) · hay un brazo cruzado · hay una tercera mano · el ojo de pez dobla el antebrazo · hay una persona o una cara · hay texto o marca de agua.

---

## 7. Notas para el PM (no hace falta que el CEO las lea)

- **Hipótesis, SIN VERIFICAR:** que el Método B dé manos utilizables. Depende de que PyraCanny lea nuestros bocetos 2D como manos y no como bloques. La calibración B0 con la TT-33 aprobada lo decide en una sola tanda.
- **Hipótesis:** que las fotos de una sola mano (Método A) se combinen bien en `hand_ref.py` para armas a dos manos. Si `hand_ref.py` solo acepta una mano por foto, A4 (IZh abierta, a dos manos) puede necesitar un recorte manual.
- Si la mano sale en espejo, la luz que pedimos desde arriba a la izquierda queda arriba a la derecha al voltear. Los tonos de `hand_ref.py` lo absorben en parte; si se nota, que el CEO lo diga.
- **Licencias:** las entradas son de Freedoom (BSD-3) o nuestras. Las fotos del CEO son generaciones propias con SDXL. Cada una necesita su fila en `docs/art/LICENSES.md` si se aprueba una celda derivada de ella, como el piolet.
- Las entradas viven en `work/art/reference/doom_inputs/` (gitignored, como todo `work/`). Las genera `make_doom_inputs.py`, en esa misma carpeta: lee el IWAD, compone sobre 320×200 con los offsets `grAb`, recorta y escala con bicúbico más desenfoque.
