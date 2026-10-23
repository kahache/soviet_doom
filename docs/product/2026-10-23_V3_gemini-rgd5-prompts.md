# Gemini: prompts de la granada RGD-5 (V3, A4; D116, D120)

**Para:** el CEO. **Autor:** mod-engineer, preparado el 2026-10-23 para V3. **Estado:** listo para pegar.
Mismo formato que `docs/product/2026-10-23_P4_gemini-prompt-pack.md`: explicacion en espanol, prompts en ingles
dentro de bloques de codigo. No se copia en `docs/ru/` (D34). Las imagenes nunca se suben a GitHub (D77, `work/`
esta ignorado); son referencia de estilo, no copias.

> **En 30 segundos.** **5 imagenes necesarias** (4 de la mano en primera persona y la granada suelta) y **2
> opcionales** (la bolsa de dos y la caja). Un chat nuevo solo para la RGD-5. Todo va a `work/art/reference/`.
> Hasta que lleguen, la granada se ve con sprites provisionales: en la mano, el piolet; en el suelo, la
> cantimplora del bonus de salud tenida de gris metal (D116; `docs/engine/2026-10-23_V3_rgd5.md` §5).

## 1. Resumen

| Prioridad | Imagen | Fichero | Que da | Sprite final |
|---|---|---|---|---|
| 1 | reposo | `gemini_rgd5_A.png` | la mano con la granada, lista | `SDRG` A |
| 2 | quitar la anilla y armar el brazo | `gemini_rgd5_B.png` | la anilla fuera, el brazo atras | `SDRG` B |
| 3 | lanzar | `gemini_rgd5_C.png` | el brazo adelante, la granada saliendo | `SDRG` C |
| 4 | acompanar | `gemini_rgd5_D.png` | el brazo estirado, la mano vacia | `SDRG` D |
| 5 | granada en el mundo | `gemini_rgd5_pickup.png` | la granada suelta (21021) **y** la granada en vuelo | `SDRJ` A, `SDRN` A |
| 6 (opcional) | bolsa de dos | `gemini_rgd5_pouch.png` | el arma en el suelo (21009) | `SDRQ` A |
| 7 (opcional) | caja | `gemini_rgd5_crate.png` | la caja de cuatro (21022) | `SDRZ` A |

Cortes naturales: **4** (la mano entera; el suelo sigue provisional), **5** (todo lo necesario), 7 (todo). Sin
la 6, la bolsa usa la imagen 5 un poco mas grande; sin la 7, la caja sigue siendo la de PG-7V tenida.

## 2. Nota practica

1. **Chat nuevo** para la RGD-5; las imagenes **en este orden**. Las 2-4 dicen "Using exactly the same hand...":
   la primera fija la mano, la manga y la granada.
2. **Lo que distingue una RGD-5** (comprobar antes de guardar): cuerpo **liso en forma de huevo**, verde oliva, una
   costura fina alrededor del centro, **sin cuadricula**; arriba la espoleta de acero con la **palanca curva** que
   baja por un lado y la **anilla redonda**. Si sale con cuadricula (es la F-1 "pina"), repetir con: *"smooth egg
   shape, NOT the ribbed F-1 pineapple grenade"*.
3. **Comprobacion de armas** (la del paquete, punto 2.8): mano desnuda, cinco dedos, la mano derecha a la derecha,
   fondo magenta liso, manga de gimnastyorka oliva desde el borde inferior; sin guantes, enemigos, barra de estado,
   texto ni nada cortado salvo el antebrazo.
4. **Si Gemini rechaza** (granada = arma): quita *"explosive"*, *"fragmentation"* y *"throw at"*; deja *"a Soviet
   RGD-5 prop grenade, as in a 1990s video game"* y *"tossing it forward"*. Nunca enemigos ni personas en la imagen.
5. **Guardado:** nombre exacto de la tabla, en `work/art/reference/`. El formato da igual (.png mejor).
6. **Despues** (no es del CEO): `art-director` anade la entrada RGD-5 a `tools/art/gemini_frames.py` (~30k) y recorta
   las imagenes 5-7 (~25k); `mod-engineer` hace el cambio de nombres (un `sed` por fichero, ya escrito en cada
   cabecera).

## 3. Primera persona: 4 imagenes

#### Imagen 1 de 7 (RGD-5 1/4): reposo
- **Chat:** RGD-5
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_A.png`
- **Nota:** la granada en la mano derecha, baja, a la derecha; la anilla visible

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet RGD-5 hand grenade of the 1970s held in the RIGHT hand: a smooth egg-shaped body in olive-green painted steel with one thin seam around its middle (smooth, NOT the ribbed F-1 pineapple grenade), a dull grey steel fuse screwed into the top, its curved steel lever (spoon) running down the side of the body under the fingers, and a round steel pull-ring with a split pin on the fuse. The right hand closes round the body and holds the lever down; the ring points to the left, towards the centre of the image. The left hand is not visible.

HANDS: a BARE human hand, no glove, natural adult proportions, five fingers, visible knuckles, light skin with warm shading. The forearm rises from the very BOTTOM edge of the image, right of centre, in an olive-drab Soviet WWII cotton tunic sleeve (gymnastyorka, khaki-olive, plain cuff). The arm never leaves the image sideways.

VIEW: seen from behind and slightly above, as the player's own hand at rest (ready pose, NOT throwing): the grenade held low, a little right of centre, at about chest height.

COMPOSITION: hand and grenade fill only the lower 40% of the image, right of centre. The upper half is empty background. Nothing is cut off except the forearm at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Imagen 2 de 7 (RGD-5 2/4): quitar la anilla y armar el brazo
- **Chat:** RGD-5 (mismo chat, tras la 1)
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_B.png`
- **Nota:** dos manos: la izquierda, abajo a la izquierda, con la anilla y el pasador; la derecha, alta y atras

```text
Using exactly the same hand, sleeve, grenade and pixel style as in the previous image, make the "pin pulled, arm drawn back" frame: the RIGHT arm is raised and drawn back, the grenade held high at the right edge of the image near the top of the lower half, the steel lever still pressed down by the fingers. The LEFT hand, BARE, five fingers, olive-drab gymnastyorka sleeve rising from the BOTTOM edge left of centre, holds the round steel pull-ring with its split pin just pulled out of the fuse. Both forearms rise from the bottom edge and never leave the image sideways. Hands and grenade fill only the lower 60% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

#### Imagen 3 de 7 (RGD-5 3/4): lanzar
- **Chat:** RGD-5 (mismo chat)
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_C.png`
- **Nota:** el brazo hacia delante, la mano abriendose; la granada justo saliendo, en el centro, mas pequena

```text
Using exactly the same right hand, sleeve, grenade and pixel style as before, make the "release" frame: the RIGHT arm swings forward and up towards the centre of the image, the hand opening, and the grenade has just left the fingers, a little smaller because it is moving away, slightly above the hand near the centre of the image. The steel lever (spoon) is flying off the grenade. The left hand is not visible. The forearm rises from the BOTTOM edge, right of centre, and never leaves the image sideways. Hand and grenade fill only the lower 55% of the image. Same perfectly flat solid magenta (#FF00FF) background, no motion blur, no speed lines, no shadow, no text, no enemies, no HUD.
```

#### Imagen 4 de 7 (RGD-5 4/4): acompanar el lanzamiento
- **Chat:** RGD-5 (mismo chat)
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_D.png`
- **Nota:** la mano vacia, abierta, el brazo estirado; NO debe haber granada

```text
Using exactly the same right hand, sleeve and pixel style as before, make the "follow-through" frame: the RIGHT arm is extended forward and slightly down after the throw, the hand open and EMPTY (no grenade anywhere in the image), fingers relaxed, palm facing down, a little right of centre. The left hand is not visible. The forearm rises from the BOTTOM edge and never leaves the image sideways. Hand and arm fill only the lower 40% of the image. Same perfectly flat solid magenta (#FF00FF) background, no shadow, no text, no enemies, no HUD.
```

## 4. En el mundo: 1 imagen necesaria y 2 opcionales

Objetos sueltos en el suelo, vistos un poco desde arriba, como los demas objetos del mod. Mismo chat (mantiene la
granada) o uno nuevo si el chat se ha llenado; en ese caso adjunta `gemini_rgd5_A.png`.

#### Imagen 5 de 7: la granada suelta (y en vuelo)
- **Chat:** RGD-5
- **Adjuntar:** nada (o `gemini_rgd5_A.png` si es chat nuevo)
- **Guardar como:** `work/art/reference/gemini_rgd5_pickup.png`
- **Nota:** de esta imagen salen dos sprites: la granada del suelo (`SDRJ`) y la que vuela (`SDRN`)

```text
Create ONE small item sprite for a 1993-1996 PC first-person shooter, in the same hand-pixelled style: 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, 4 to 6 flat shade steps per material, a thin dark outline.

OBJECT: one single Soviet RGD-5 hand grenade lying on its side on the floor: the smooth egg-shaped olive-green steel body with one thin seam around the middle (NOT the ribbed F-1 pineapple), the grey steel fuse at one end with its curved lever along the body and the round steel pull-ring. Seen from the side and slightly above (about 30 degrees), the fuse pointing to the right.

COMPOSITION: the grenade alone, centred, filling about 60% of the image width, nothing cut off, at least 10 px of empty background on every side.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No floor, no painted or cast shadow, no gradient, no scenery, no hands, no text, no letters, no numbers, no logo, no watermark. FORMAT: square image.
```

#### Imagen 6 de 7 (OPCIONAL): la bolsa de dos granadas
- **Chat:** RGD-5
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_pouch.png`
- **Nota:** el arma en el suelo; sin ella, la bolsa usa la imagen 5 un poco mas grande

```text
Using the same RGD-5 grenade and pixel style as before, create ONE item sprite: a Soviet Army khaki canvas grenade pouch for two grenades, with a flap and a small leather strap, lying flat on the floor, the flap open and the tops of two olive-green RGD-5 grenades (grey steel fuses, round pull-rings) showing. Seen from the side and slightly above (about 30 degrees). Centred, filling about 70% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no letters, no logo. FORMAT: square image.
```

#### Imagen 7 de 7 (OPCIONAL): la caja
- **Chat:** RGD-5
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_rgd5_crate.png`
- **Nota:** sin letras: las marcas sovieticas de una caja real llevan texto, aqui solo una franja

```text
Using the same pixel style as before, create ONE item sprite: a small Soviet Army wooden ammunition crate painted olive-green, with rope handles at both ends, steel corner brackets and a plain yellow stencilled stripe on the side (NO letters, NO numbers, NO symbols), the lid propped open showing four olive-green RGD-5 grenades lying in a row. Seen from the front and slightly above (about 30 degrees). Centred, filling about 80% of the image width, nothing cut off, at least 10 px of empty background on every side. Perfectly flat solid magenta (#FF00FF) background, no shadow, no floor, no text, no logo. FORMAT: wide landscape image.
```

## 5. Sonidos (no son de Gemini, para `sound-designer`)

Hoy la granada suena con sonidos ya instalados bajo nombres propios (`SNDINFO`, "Slot 8"). Faltan cinco:
`SDRGPIN` (anilla y pasador), `SDRGTHR` (el brazo y la palanca saltando), `SDRGBNC` (huevo de acero en hormigon),
`SDRGEXP` (estallido seco con metralla, menor que el PG-7V) y `SDRGPKP` (bolsa de lona, dos granadas). Detalle en
`docs/engine/2026-10-23_V3_rgd5.md` §4.

No se ha abierto Gemini ni generado ninguna imagen al preparar estos prompts. Todo lo que se dice de como respondera
es **no verificado** hasta que se use; los frames 2 y 3 (dos manos, movimiento) son los de mayor riesgo de deriva.
