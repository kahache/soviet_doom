# Gemini: paquete de prompts para manana (P4, cupo diario pequeno, D116)

**Para:** el CEO. **Autor:** art-director, preparado el 2026-10-22 para usar el 23. **Estado:** listo para pegar.
Explicacion en espanol; los prompts van en ingles, dentro de bloques de codigo. No se copia en `docs/ru/` (D34).
Las imagenes nunca se suben a GitHub (D77, `work/` esta ignorado).

> **En 30 segundos.** Hay **27 imagenes** pedidas, ordenadas por prioridad (tabla de abajo, con el total
> acumulado: para donde se acabe el cupo, lo hecho hasta ahi es utilizable). Un chat nuevo por personaje. Cada
> imagen lleva su prompt completo (los bloques comunes ya estan pegados dentro), el nombre de fichero y que
> adjuntar. Las armas van a `work/art/reference/`; los enemigos a `work/art/reference/enemies/gemini/`.
> El PM las convierte despues con `tools/art/gemini_frames.py` y `tools/art/gemini_enemy.py`.

## 1. Resumen

| Prioridad | Pieza | Imagenes | Total acumulado |
|---|---|---|---|
| 1 (alta) | TT-33 (D111) | **2** | 2 |
| 2 | SD_LegionGunner (SDLG) | **5** | 7 |
| 3 | SD_LibertyColossus (SDLC) | **7** | 14 |
| 4 | The Consortium (SDCN) | **7** | 21 |
| 5 | AKM | **2** (+1 opcional: recarga) | 23 |
| 6 | Re-asks de mayor impacto | **4** | 27 |

**Total: 27 imagenes** (28 si se pide tambien la recarga opcional del AKM). Cortes naturales (todo lo anterior queda
utilizable): 2 (TT-33), 7 (+ artillero), 14 (+ Coloso), 21 (+ Consorcio), 23 (+ AKM), 27 (+ re-asks).

Que desbloquea cada pieza:

| Pieza | Que entra en el juego | Notas de cantidad |
|---|---|---|
| TT-33 | el arma inicial rehecha con manos desnudas (D111; hoy "to be redone", D61) | 2: reposo y disparo |
| SDLG | las 70 lumps del artillero (5 hojas nuevas + la `turn` que ya existe) | dolor y reventon se derivan (lo hace el pipeline) |
| SDLC | las 81 lumps del Coloso (7 hojas) | la hoja de pisoton lleva 2 filas (Q arriba, R abajo) en 1 imagen |
| SDCN | las 95 lumps del jefe final (7 hojas) | dos hojas llevan 2 filas (aim E/F, walk A/C) para ahorrar cupo; R (nucleo brillante) y el dolor H se derivan |
| AKM | arma de 2o puesto del slot 4 | 2 imagenes; la recarga (opcional) esta aparcada (D47) |
| Re-asks | los 4 arreglos mas visibles de las 7 hojas ya instaladas | ver el final de la seccion 9 para lo que se dejo fuera y por que |

## 2. Nota practica (leela antes de empezar)

1. **Un chat nuevo por personaje** (8 chats: TT-33, artillero, Coloso, Consorcio, AKM, sabueso, General, Legion).
   Asi Gemini no mezcla estilos. Dentro de cada chat las imagenes van **en el orden en que aparecen aqui**: la primera
   fija al personaje y las siguientes se piden en el mismo chat.
2. **Continuidad.** Los prompts de segundas imagenes empiezan por *"Using exactly the same character as in the previous
   image (same face, same colours, same equipment, same proportions, same scale)..."* y repiten una descripcion corta del
   personaje. Si aun asi deriva (cara distinta, otro casco, otra escala), **no regeneres a ciegas**: en el mismo chat
   escribe *"Exactly the same character as in the first image of this chat: same face, same helmet, same colours, same
   scale. Redo only this pose."* y adjunta de nuevo la primera hoja. Cada regeneracion gasta cupo: usala solo si el
   personaje es otro, o si las figuras se tocan o se salen del encuadre.
3. **Adjuntar imagenes** (artillero, sabueso, General, Legion): menu "+" de Gemini, en el primer mensaje del chat.
   El PM puede hacerlo por Chrome (`find` de los inputs de fichero ocultos y `file_upload`); a mano, arrastra el PNG.
4. **Contar figuras antes de guardar.** Las hojas de una fila deben tener **5** figuras; las de dos filas, 5 + 5; las de
   muerte, 5. Que haya una figura de mas o de menos en una hoja de muerte no obliga a repetir (el pipeline elige cuales
   usa); si obliga a repetir que se toquen, que algo salga cortado por el borde, que haya letras, o que cambie el personaje.
5. **Guardado.** Descarga de la imagen (o el truco del canvas con `toDataURL`, 1024 px de ancho; Chrome guarda en
   `E:\Downloads`) y muevela con el **nombre exacto** que indica cada imagen. El formato da igual (.png, .jpg, .jfif), pero para
   enemigos conviene `.png`.
6. **Si Gemini rechaza o contesta solo con texto.** Primero di *"Generate the image now"* (a veces contesta sin
   generar). Si se niega, **reformula sin palabras de violencia ni de simbolos** y reintenta en el mismo chat:

| Si rechaza por... | Cambia... |
|---|---|
| violencia | quita `kill, dead, die, blood, wound, gore, shot, bullet`. Usa `hit, struck, knocked out, flinching, falling`. En los prompts de muerte deja "cartoonish like a 1993 video game". Nunca la palabra *blood* |
| disparo | `blasting a burst` -> `with a bright yellow-orange flash of light at the muzzle of his prop gun` |
| simbolos | **nunca** pidas esvastica, cruz gamada, "Nazi" ni "SS". El brazalete es *"a red armband with a plain white empty square"*; si aun asi lo rechaza, pide solo *"a red cloth band on the upper arm"* y avisa: el pipeline pinta el simbolo (D108) |
| personas reales | quita *"inspired by the Statue of Liberty monument"* y deja *"a giant robed statue holding a torch"* (es un monumento, no una persona, pero por si acaso); nunca nombres lideres ni presidentes |
| nada de lo anterior | chat nuevo, vuelve a adjuntar la referencia, y pide **solo la pose** en una frase, conservando los bloques LAYOUT y BACKGROUND |

7. **Cupo.** Segun `docs/HANDOFF.md` el contador se reinicio el 22-oct a las 17:33; **no verificado** que manana
   lo haga a la misma hora. Si el cupo se acaba a media pieza, lo guardado se conserva: anota el numero de la ultima
   imagen hecha y se retoma desde la siguiente.
8. **Comprobacion rapida antes de guardar cada hoja de enemigo** (lo que costo re-asks en las siete ya hechas):
   fondo magenta liso, **sin sombra pintada en el suelo**; 10 px de margen alrededor y bajo las botas (las suelas
   cortadas por el borde fueron el re-ask mas repetido); ninguna figura toca a la vecina (fogonazos y humo incluidos);
   sin letras ni numeros; perfil mirando a la izquierda; misma escala en las cinco figuras; el brazalete del Reich,
   rojo con un cuadro blanco **vacio**. **Armas:** manos desnudas, cinco dedos, mano derecha a la derecha, fondo
   magenta liso, el arma entera, casi recta y centrada; sin guantes, enemigos, barra de estado, texto ni arma cortada.

## 3. Bloques comunes (informativo: **ya estan pegados dentro de cada prompt**)

Para que se vea de donde sale cada frase. Lo que funciono con las siete hojas hechas: cinco vistas en una fila, fondo
magenta plano, sin simbolos; muerte "cartoonish like a 1993 video game" sin la palabra *blood*, con el ultimo frame
"knocked out, lying completely flat and horizontal". (Los prompts originales de esas hojas no estan guardados en el repo:
estos bloques los reconstruyen a partir de `docs/HANDOFF.md`, de las specs de `tools/art/gemini_enemy.py` y de las hojas
resultantes; NO VERIFICADO que la redaccion sea literalmente la misma.)

- **STYLE:** Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.
- **LAYOUT (5 vistas):** LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.
- **LAYOUT (2 filas):** LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.
- **BACKGROUND:** BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image.


## 4. Prioridad 1: TT-33 (D111): 2 imagenes

Chat nuevo. Prompt base y bloque `[WEAPON]` de `docs/product/2026-10-20_0030_M2_gemini-armas.md` §3-§4, y el prompt de
disparo de su §5, tal cual. Despues el PM ejecuta `tools/art/gemini_frames.py` (~50k tokens).

#### Imagen 1 de 27 (TT-33 1/2)
- **Chat:** Chat 1 (TT-33)
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_tt33_A.png`
- **Nota:** reposo; revisa la lista de comprobacion de armas del punto 2.8

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet TT-33 Tokarev pistol held in the RIGHT hand only, arm extended forward, the left hand not visible.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Imagen 2 de 27 (TT-33 2/2)
- **Chat:** Chat 1 (TT-33)
- **Adjuntar:** nada (mismo chat, justo despues de A)
- **Guardar como:** `work/art/reference/gemini_tt33_B.png`
- **Nota:** disparo

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```


## 5. Prioridad 2: SD_LegionGunner (SDLG): 5 imagenes

Chat nuevo. **Primer mensaje: adjunta `gem_gunner_turn.png`** (las 5 vistas de pie que ya existen: Liberty Legion,
ametralladora M1919 a la cadera, dos bandoleras de balas cruzadas, bandera de EEUU en el hombro derecho) junto con el
prompt de walkL. Las demas hojas siguen en el mismo chat. Fotogramas que pide la clase
(`docs/engine/2026-10-22_P4_ep2-enemies.md` §4): A-D andar (walkL, walkR y la hoja `turn` que ya existe), E apuntar
(aim, tambien la pausa entre rafagas), F disparar (fire, con fogonazo en la cadera), G dolor (derivado de `turn`), H-L
muerte (la hoja death, 5 figuras), M-U reventon (derivado con efectos del pipeline). Por eso solo faltan 5 hojas.

#### Imagen 3 de 27 (SDLG 1/5)
- **Chat:** Chat 2 (Legion gunner)
- **Adjuntar:** work/art/reference/enemies/gemini/gem_gunner_turn.png (adjunta esta hoja en este primer mensaje del chat)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_gunner_walkL.png`
- **Nota:** primer mensaje del chat: adjunta la hoja

```text
Using the attached reference sheet as the exact character reference (same figure in all five views, same equipment, same scale), make the WALK sheet, left-foot-forward stride.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the LEFT foot stepping forward and planted, the RIGHT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride, so that it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Imagen 4 de 27 (SDLG 2/5)
- **Chat:** Chat 2 (Legion gunner)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_gunner_walkR.png`

```text
Using exactly the same character as in the attached reference sheet and the previous sheet (same face, same colours, same equipment, same proportions, same scale), make the WALK sheet, right-foot-forward stride: the mirror of the previous walk sheet's legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: WALKING, mid-stride with the RIGHT foot stepping forward and planted, the LEFT leg behind with the heel lifted, torso leaning very slightly forward, his free hand swinging a little, the M1919 still carried at the hip with both hands and the barrel pointing forward. A clear, wide stride.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Imagen 5 de 27 (SDLG 3/5)
- **Chat:** Chat 2 (Legion gunner)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_gunner_aim.png`

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: AIMING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: AIMING. He plants his feet wide and braces, the M1919 levelled at hip height held with both hands, the barrel pointing straight ahead at the target. In the front view the muzzle points at the camera (foreshortened), in the profile the barrel points horizontally to the LEFT, in the back views the barrel is seen beyond his far side. Face scowling, gun steady, NO muzzle flash.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Imagen 6 de 27 (SDLG 4/5)
- **Chat:** Chat 2 (Legion gunner)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_gunner_fire.png`
- **Nota:** los destellos que tocan a la figura vecina fueron lo que complico la hoja fire del General

```text
Same character as the attached reference sheet and the previous sheets, new pose sheet: FIRING.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

POSE: FIRING. The same braced stance as the aiming sheet, but now the M1919 is blasting a burst: a bright yellow-orange muzzle flash with a small white-hot core at the muzzle, a few brass casings flying out, the gun and shoulders jerked back slightly by the recoil, mouth open shouting. Keep the muzzle flash small and compact, well clear of the neighbouring figures (they must not touch). In the back views the flash shows only beyond his far side, never painted over his back.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Imagen 7 de 27 (SDLG 5/5)
- **Chat:** Chat 2 (Legion gunner)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_gunner_death.png`
- **Nota:** frame 5: tumbado del todo plano (el pipeline lo usa como cadaver, letra L)

```text
Same character as the attached reference sheet and the previous sheets, new sheet: a death animation strip, cartoonish like a 1993 video game (no realism, nothing graphic, no wounds).

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: the Liberty Legion heavy gunner of the reference sheet: the same figure, same proportions, same chrome-and-pink-flesh skin with glowing pale-blue eyes, same white M1 steel helmet, same grey shirt with rolled sleeves, same two crossed bandoliers of brass-coloured ammunition, same khaki trousers, same black boots, same small US flag patch on his RIGHT shoulder sleeve, and the same belt-fed M1919 machine gun carried at his hip with a belt of brass rounds hanging from it.

FRAMES, left to right: 1) flinching and staggering back from a hit, mouth open, still holding the machine gun; 2) struck, head thrown back, arms flung out, the M1919 dropping from his hands; 3) falling backwards at about 45 degrees, the gun in the air; 4) nearly down, sitting on the ground with his back almost on the floor, knees up, small puffs of dust, the gun on the ground beside him; 5) knocked out, lying completely flat and horizontal on his back on the ground, glowing eyes dimmed, arms limp, the M1919 lying beside him.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that his head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


## 6. Prioridad 3: SD_LibertyColossus (SDLC) desde cero: 7 imagenes

Chat nuevo, **sin imagen de referencia** (concepto en `docs/engine/2026-10-22_P4_ep2-enemies.md` §3: la Estatua de la
Libertad pervertida: cromo, corona de pinchos, antorcha que es lanzacohetes y lanzallamas, la tabla como escudo).
Decisiones de arte tomadas aqui, para confirmarlas al ver la primera hoja:
- Antorcha en la mano **derecha** de ella, tabla en el brazo **izquierdo** (coincide con el disparo, que sale "20 a su
  derecha"). Tabla **en blanco** (Gemini escribe texto en cuanto puede).
- Bandera de EEUU en el hombro derecho, como el resto de la Legion (D12); sin brazalete y sin otros simbolos politicos.
- Proporcion 6 de alto por 5 de ancho (~120-130 px de alto, no mas de ~100 de ancho en juego).
- Frames de la clase: A-D andar (turn + walkL + walkR), E aim, F fire, G dolor (derivado), Q y R pisoton (una sola
  imagen de 2 filas), H-P muerte (5 figuras; el pipeline completa las 9 letras, como con el General).
- **Minimo jugable** si el cupo se corta a medias: `turn`, `fire` y `death` (el resto se rellena con la vista de pie).

#### Imagen 8 de 27 (SDLC 1/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (texto, sin referencia)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_turn.png`
- **Nota:** esta hoja fija el personaje y la escala; si sale mal, no sigas: repitela antes (cuenta como reserva)

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE LIBERTY COLOSSUS, a giant boss monster of an alien invasion army: a colossal chrome robot-statue shaped like a stern robed woman monument, inspired by the Statue of Liberty monument (a statue, not a real person; a generic stern face with hollow glowing pale-blue eyes). Chrome plate-armour robes with heavy folds reaching her shins, raw pink flesh showing at the joints (elbows, wrists, neck, knees), heavy chrome feet. On her head a crown of seven long steel spikes. Her RIGHT arm (on the left of the image in the front view) is raised high holding a huge TORCH that is really a rocket launcher and flame projector: a thick steel tube with a flared nozzle on top, glowing orange inside. Her LEFT arm carries a large stone tablet as a shield in front of her body; the tablet is completely blank, no text, no numbers, no carving. A small US flag patch (stars and stripes) on the plate of her RIGHT shoulder. Stocky and heavy for a boss: about 6 units tall to 5 wide, including the raised torch.

POSE: standing idle and menacing, feet planted apart, the torch held high with the nozzle pointing up and glowing, the blank tablet held on the left forearm in front of the chest, chin lowered, hollow glowing eyes.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 9 de 27 (SDLC 2/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_walkL.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, LEFT foot forward and planted, RIGHT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. A clear, wide stride so it differs from the standing pose.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 10 de 27 (SDLC 3/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_walkR.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: WALK, a heavy lumbering stride, RIGHT foot forward and planted, LEFT foot behind with the heel lifted, the body swaying slightly, the torch still held high, the tablet shield on the left forearm. The mirror of the previous walk sheet's legs.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 11 de 27 (SDLC 4/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_aim.png`

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: AIMING. The torch arm swings down and the torch is levelled to point at the viewer: in the front view the torch nozzle points straight at the camera (foreshortened, glowing orange inside), in the profile it points horizontally to the LEFT, in the back views it points away beyond her far side. The tablet is raised in front of her body, the legs braced wide. NO flame and NO rocket yet, only the glow.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 12 de 27 (SDLC 5/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_fire.png`
- **Nota:** mismo cuidado con destellos y humo que en la hoja fire del General

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING. The same braced pose as the aiming sheet, but the torch is now discharging: a rocket leaving the nozzle with a short bright orange-yellow burst of flame and a puff of smoke, the whole figure jolted back slightly. Keep the flame and smoke short and compact, well clear of the neighbouring figures (they must not touch). In the back views the blast shows only beyond her far side, never painted over her back.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 13 de 27 (SDLC 6/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_stomp.png`
- **Nota:** una sola imagen con 2 filas (Q arriba, R abajo); si la segunda fila sale mal, pidela sola (reserva)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses: this is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, the STOMP wind-up: she raises her LEFT knee high with the foot lifted well off the ground, the body leaning back a little, the torch held high, the tablet braced in front. BOTTOM ROW, the STOMP impact: the same foot slammed down onto the ground, the body leaning forward, the torch still high, a compact ring of dust and small cracked rock around the feet (kept close to the feet, not spreading to the neighbouring figures).

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 14 de 27 (SDLC 7/7)
- **Chat:** Chat 3 (Liberty Colossus)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_colossus_death.png`
- **Nota:** frame 5 = el despojo que se queda (letra P)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (the Colossus is a machine-statue falling to pieces; nothing graphic). This is the Liberty Colossus: the chrome robed statue colossus with the seven-spike crown, pink flesh at the joints, the rocket-and-flame torch in her RIGHT hand, the blank stone tablet shield on her LEFT arm, the small US flag patch on her right shoulder, the same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) shuddering, the crown cracking, one spike snapping off, a few chrome sparks; 2) the torch slipping from her hand and falling, the tablet shield dropping from her other arm; 3) swaying and leaning back, knees buckling, pieces of chrome plate breaking away; 4) toppling backwards at about 45 degrees, mid-fall; 5) wrecked, lying completely flat and horizontal on her back, the crown broken, the torch and the tablet lying beside the body, thin wisps of smoke.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the character falling backwards so that her head ends up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 7. Prioridad 4: The Consortium (SDCN): 7 imagenes

Chat nuevo, **sin imagen de referencia** (`docs/engine/2026-10-22_P4_ep3-final-boss.md` §2 y §5). El brazalete rojo del
medio Reich lleva un **cuadro blanco vacio**: Gemini rechaza la esvastica y el pipeline pinta el simbolo (D108). No se
pide el simbolo ni se nombran las SS: el casco es "a grey German-style steel helmet".

Frames de la clase y de donde sale cada uno:

| Frames | Que es | De donde |
|---|---|---|
| Q, R | enraizado, nucleo apagado / encendido | SDCN 1/7 (Q); R se deriva aclarando el azul cobalto del nucleo |
| B, D | fase 2 de pie, y la escala de referencia | SDCN 2/7 |
| G | disparo, destello y nucleo ardiendo | SDCN 3/7 |
| I-O | muerte: nucleo, gritan, mitades, colapso, arde, despojo | SDCN 4/7 (5 figuras; M y N se derivan con fuego) |
| E, F | tell de las bolas / tell de los cohetes | SDCN 5/7 (2 filas: E arriba, F abajo) |
| A, C (andar) | fase 2 caminando | SDCN 6/7 (2 filas: A arriba, C abajo) |
| S | la Ruptura (cables que saltan) | SDCN 7/7 |
| H | dolor, las dos cabezas | derivado (la vista de pie inclinada) |

El orden dentro de la pieza es el de prioridad: **minimo jugable** = imagenes 1 a 4 (rooted, turn, fire, death);
los frames que falten se rellenan con la vista de pie.

**Decision de arte (confirmala):** los frames de ataque E, F, G y S sirven a las dos fases, y el boss en fase 1 no tiene
piernas y en fase 2 si. Para no dibujar dos juegos, en esos frames la parte baja va **envuelta en un nudo de cables y humo
oscuro que oculta las piernas**; asi valen en las dos fases. Si al verlo no convence, hay una segunda tanda con piernas
(no incluida en el total). Los dos cascos con las caras genericas no reproducen a nadie (D12).

#### Imagen 15 de 27 (SDCN 1/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (texto, sin referencia)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_rooted.png`
- **Nota:** fija el personaje (frame Q). R, el nucleo brillante, se deriva aclarando el azul cobalto: no se pide

```text
Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CHARACTER: THE CONSORTIUM, the final boss of an alien invasion, twice the height of a heavy brute: one huge trunk made of TWO halves welded together down the middle, with TWO heads joined at the shoulders (one per half), generic stern faces, no likeness of any real person. Its LEFT half (on the viewer's RIGHT in the front view) is the German half: grey-green skin, a grey German-style steel helmet with a small eagle badge, a red armband on the upper arm with a plain white square field that is completely empty (no symbol, no letters), and the forearm replaced by a rack of rocket tubes. Its RIGHT half (on the viewer's LEFT in the front view) is the American half: chrome plate armour over pink flesh, an American M1 steel helmet, a small US flag patch on the shoulder, and the forearm is a big chrome energy-ball projector with a glowing nozzle. Between the two halves, in the chest, a ribbed open cavity glowing cobalt blue (portal energy): the glowing core.

POSE: PHASE 1, standing still, plugged into the floor.

LOWER BODY, ROOTED: no legs. The lower body is a heavy skirt of thick black cables and conduits that flare out and pool on the floor, with more thick cables running away from its back and skirt into the distance (in the front view they disappear behind it). The core glows a dim, steady cobalt blue. Both arms hang heavily at its sides, the weapon forearms pointing down, a heavy brooding stance.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 16 de 27 (SDCN 2/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_turn.png`
- **Nota:** hoja de referencia de la fase 2 (frames B y D, y escala)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, but PHASE 2. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: PHASE 2, standing, the same upper body as the previous sheet.

LOWER BODY, FREE: the cables have been torn out: short stumps of black cable hang at its back and hips, sparking and trailing along the floor, and under the trunk there are two heavy mechanical legs of grey steel with hydraulic pistons and big flat armoured feet. The core burns brighter, a vivid cobalt glow. Standing, both arms hanging heavily, the weapon forearms pointing down.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 17 de 27 (SDCN 3/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_fire.png`
- **Nota:** decision de arte: la parte baja va oculta en un nudo de cables y humo para que valga en fase 1 y 2 (ver el texto de la seccion)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: FIRING (frame G, shared by both phases). Both arms fire at once: the energy projector (its RIGHT forearm) discharges a bright cobalt-and-white ball of energy with a muzzle flare, the rocket tubes (its LEFT forearm) shoot a rocket with a burst of orange flame, and the chest core blazes bright white-blue; the whole body jolted back slightly, both mouths open roaring. Keep every flare and flame compact, well clear of the neighbouring figures (they must not touch). In the back views the blasts show only beyond the far side, never painted over its back.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 18 de 27 (SDCN 4/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_death.png`
- **Nota:** 5 figuras cubren I J K L (M y N se derivan con fuego) y O (el despojo con los dos cascos)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet: a destruction animation strip, cartoonish like a 1993 video game (nothing graphic). This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) the core cracking: bright cobalt-white cracks of light across the chest, both heads recoiling; 2) both heads screaming, both arms thrown out; 3) the two halves tearing apart along the welded seam, the chest splitting open with blinding cobalt light, plates and sparks flying; 4) collapsing and sagging down onto its knees, the halves separating, small flames starting; 5) the wreck: a low smoking ruined heap of grey-green and chrome plates and tangled cables, with the two steel helmets (one grey German-style, one American M1) lying side by side in the ash, a few small flames.

LAYOUT: exactly FIVE frames of the SAME single character in ONE horizontal row, left to right, like an animation strip, all at the same scale, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the figures. All frames are seen from the side or three-quarter view, the boss falling backwards so that its heads end up toward the RIGHT of the image.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 19 de 27 (SDCN 5/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_aim.png`
- **Nota:** una sola imagen con 2 filas (E arriba, F abajo)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW (the orb tell): its RIGHT arm, the chrome energy projector, is levelled forward at the viewer with the nozzle glowing, the chest core opening wide and glowing brighter, the other arm hanging; in the front view the nozzle points at the camera (foreshortened), in the profile it points horizontally to the LEFT. BOTTOM ROW (the rocket tell): its LEFT arm, the rack of rocket tubes, is raised and aimed at the viewer, the tubes loaded and ready, the other arm hanging. NO flames and NO shots yet.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 20 de 27 (SDCN 6/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_walk.png`
- **Nota:** una sola imagen con 2 filas (A arriba = walkL, C abajo = walkR)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), new sheet with TWO rows of poses. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale. PHASE 2 body, with the two mechanical legs and the torn cable stumps dragging.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, WALK with the LEFT mechanical leg forward and planted, the RIGHT leg behind with the heel lifted, cable stumps dragging on the floor, a heavy lumbering stride, both arms hanging. BOTTOM ROW, the mirrored stride: RIGHT leg forward and planted, LEFT leg behind with the heel lifted. A clear, wide stride in both rows.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 21 de 27 (SDCN 7/7)
- **Chat:** Chat 4 (Consortium)
- **Adjuntar:** nada (misma conversacion)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_consortium_breach.png`
- **Nota:** ultimo de la pieza: solo se ve dos segundos al partir la vida; si falta, el pipeline usa el dolor (H)

```text
Using exactly the same character as in the previous image (same face, same colours, same equipment, same proportions, same scale), the same sheet layout, new pose. This is the Consortium: the huge two-halved boss, German half (grey-green skin, grey steel helmet, red armband with a plain white empty square, rocket-tube rack forearm) on its LEFT and American half (chrome plates over pink flesh, M1 helmet, US flag patch, chrome energy projector forearm) on its RIGHT, two heads, the ribbed cobalt-blue glowing core in the chest, same proportions, colours and scale.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: THE BREACH (frame S): the thick black cables snapping off its back and hips and whipping outward with white sparks, the core flaring blinding white, both arms thrown wide, both heads roaring upward, the body arched back. Keep sparks and cable ends compact, clear of the neighbouring figures.

LOWER BODY: wrapped from the hips down in a dense tangle of black cables and swirling dark smoke that hides the legs completely, standing on the floor line.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```


## 8. Prioridad 5: AKM: 2 imagenes (+1 opcional)

Chat nuevo. El bloque `[WEAPON]` y el prompt base listos de `docs/engine/2026-10-22_P4_akm.md` §5, con el prompt de disparo
de `docs/product/2026-10-20_0030_M2_gemini-armas.md` §5 sin cambios, en el mismo chat. **Comprobar**, ademas de la lista
de armas del punto 2.8: el **cargador curvo** y el **freno de boca oblicuo** (lo que distingue un AKM del PPSh-41 a 320x200).

#### Imagen 22 de 27 (AKM 1/2)
- **Chat:** Chat 5 (AKM)
- **Adjuntar:** nada
- **Guardar como:** `work/art/reference/gemini_akm_A.png`
- **Nota:** reposo; comprueba el cargador CURVO y el freno de boca OBLICUO

```text
Create ONE first-person weapon sprite in the exact style of a 1993-1996 PC first-person shooter: hand-pixelled art, 256-colour VGA palette, chunky square pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material).

WEAPON: a Soviet AKM assault rifle of the 1970s (7.62x39), seen from behind: a black phosphated steel receiver with a stamped dust cover, a reddish-brown laminated wooden handguard and pistol grip, a curved 30-round magazine in orange-brown bakelite, the gas tube above the barrel, and the slanted muzzle brake at the very end of the barrel. The LEFT hand holds the wooden handguard under the barrel; the RIGHT hand grips the pistol grip, the index finger along the trigger guard. The stock is tucked into the right shoulder, out of the image.

HANDS: BARE human hands, no gloves, natural adult proportions, five fingers each, visible knuckles, light skin with warm shading. The forearms rise from the very BOTTOM edge of the image in olive-drab Soviet WWII cotton tunic sleeves (gymnastyorka, khaki-olive, plain cuffs). The arms never leave the image sideways.

VIEW: seen from behind and slightly above, as the player's own weapon at rest (ready pose, NOT firing). The weapon points almost straight ahead into the screen, centred, only slightly angled (about 10-15 degrees), muzzle near the centre of the image.

COMPOSITION: weapon and hands fill only the lower 45% of the image, centred. The upper half is empty background. Nothing is cut off except the forearms at the bottom edge.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No gradient, no shadow, no floor, no scenery, no enemies, no HUD, no status bar, no text, no logo, no watermark, no border, no muzzle flash.

LIGHT: a single light source from the upper left. FORMAT: landscape 4:3, drawn as if for a 320x200 screen and enlarged with nearest-neighbour scaling.
```

#### Imagen 23 de 27 (AKM 2/2)
- **Chat:** Chat 5 (AKM)
- **Adjuntar:** nada (mismo chat)
- **Guardar como:** `work/art/reference/gemini_akm_B.png`
- **Nota:** disparo

```text
Using exactly the same image (same hands, same weapon, same pose, same magenta background, same pixel style), make the firing frame: the weapon kicks up slightly (about 4% of the image height) and a bright yellow-orange muzzle flash appears at the muzzle. Keep everything else identical.
```

#### Imagen OPCIONAL (fuera del total)
- **Chat:** Chat 5 (AKM)
- **Adjuntar:** nada (mismo chat, tras A)
- **Guardar como:** `work/art/reference/gemini_akm_C.png`
- **Nota:** OPCIONAL (recargas aparcadas, D47): solo si sobra cupo; no cuenta en el total

```text
Using exactly the same image, make the reloading frame: the rifle is tilted a little to the right, the LEFT hand pulls the empty curved magazine down and out of the magazine well, a fresh curved magazine held against it. Same hands, same rifle, same magenta background, same pixel style.
```


## 9. Prioridad 6: re-asks de mayor impacto: 4 imagenes

De la lista de la hoja `docs/art/previews/2026-10-22_P4_enemies-gemini.html` (campo "Pedir otra vez a Gemini", que sale de
`tools/art/gemini_enemy.py`), solo los cuatro que mas se ven jugando, por este orden: el sabueso embistiendo, la orden del
General con el puno en alto (mas el senalar, en la misma imagen), la bandera de la Legion que cambia de hombro y la muerte
de la Legion con la escopeta cortada. Los dos primeros son frames nuevos; los dos ultimos corrigen defectos visibles del
soldado raso, que es el enemigo mas frecuente. Los ficheros nuevos no pisan a los existentes (`_v2`, `lunge`, `summon`, `turnB`).

#### Imagen 24 de 27 (Re-ask 1/4)
- **Chat:** Chat 6 (sabueso)
- **Adjuntar:** work/art/reference/enemies/gemini/gem_hound_bite.png (referencia de personaje y de rejilla)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_hound_lunge.png`
- **Nota:** re-ask del sabueso: hoy el mordisco apenas cambia la pose; esto da el salto (frames F/G)

```text
Using the attached sheet as the exact reference (same Reich hound: grey skin, brown fur on the back, riveted steel helmet-collar and shoulder plates, spiked collar, yellow eyes; same pixel style, same scale, same 2-rows-by-4 grid layout and same view order), make a NEW sheet of the ATTACK LUNGE.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSE: the hound launching its attack: the front paws completely off the ground, the body stretched out in mid-leap, jaws wide open at full stretch, head thrust forward, the hind legs still pushing off. Views as in the reference grid (front, three-quarter front, profile facing LEFT, three-quarter back, back, repeated as in the reference).

LAYOUT: the same 2 rows by 4 figures as the reference, each figure fully inside the image with at least 10 px of empty background all round, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere, NO ground shadow under the dog, no gradient, no scenery, no text, no letters, no logo, no watermark. FORMAT: landscape image.
```

#### Imagen 25 de 27 (Re-ask 2/4)
- **Chat:** Chat 7 (General)
- **Adjuntar:** work/art/reference/enemies/gemini/gem_general_turn.png (referencia de personaje)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_general_summon.png`
- **Nota:** re-ask del General: frames Q y R de la orden 'Vorwarts!' (hoy son la pose quieta y el aim)

```text
Using the attached sheet as the exact reference (same General: cream greatcoat with gold epaulettes, medals, monocle, peaked cap, black boots and belt, striped red-and-white cape, olive bazooka; same pixel style, same scale), make a NEW sheet with TWO rows of poses.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

POSES. TOP ROW, GIVING AN ORDER: his LEFT fist raised high above his head, mouth open shouting a command, the bazooka resting on his RIGHT shoulder. BOTTOM ROW, POINTING: his LEFT arm extended straight forward with the index finger pointing at the viewer, the bazooka resting on his RIGHT shoulder. In every view the small US flag patch is on his RIGHT arm and the red armband with a plain white empty square field is on his LEFT arm (as in the three-quarter views of the reference), no symbol or letters in the armband.

LAYOUT: exactly TEN figures of the SAME single character in TWO horizontal rows of FIVE. Each row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. Both rows at exactly the same scale and height, each row standing on its own common baseline, evenly spaced, no figure touching or overlapping another, nothing cut off by the image edges, at least 10 px of empty background on every side, under the feet and between the rows.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: landscape image, as wide as possible.
```

#### Imagen 26 de 27 (Re-ask 3/4)
- **Chat:** Chat 8 (Legion trooper)
- **Adjuntar:** work/art/reference/enemies/gemini/gem_legion_turn.png (referencia de personaje)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_legion_turnB.png`
- **Nota:** re-ask de la Legion: arregla la bandera que cambia de hombro al espejar (vistas 2-4)

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same white helmet, same shotgun, same style and scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

CORRECTION: the three-quarter front, the side profile and the three-quarter back views must all face LEFT, with the small US flag patch on his RIGHT shoulder sleeve in every view where that shoulder is visible. Keep the same standing pose, shotgun held across the chest, in all five views.

LAYOUT: exactly FIVE views of the SAME single figure in ONE horizontal row, left to right: 1) front, 2) three-quarter front, 3) side profile facing LEFT, 4) three-quarter back, 5) straight back. All five at exactly the same scale and height, standing on one common baseline, evenly spaced, none touching or overlapping its neighbour, nothing cut off by the image edges, at least 10 px of empty background on every side and under the feet.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```

#### Imagen 27 de 27 (Re-ask 4/4)
- **Chat:** Chat 8 (Legion trooper)
- **Adjuntar:** work/art/reference/enemies/gemini/gem_legion_death.png (referencia; mismo chat 8, adjuntala de nuevo)
- **Guardar como:** `work/art/reference/enemies/gemini/gem_legion_death_v2.png`
- **Nota:** re-ask de la Legion: la escopeta tirada del cadaver sale cortada por el borde; guardalo como _v2 para no pisar el original

```text
Using the attached sheet as the exact reference (same Liberty Legion trooper, same five death frames in the same order, same cartoonish 1993 video-game style, same scale), make the sheet again with a correction.

Hand-pixelled game sprite sheet in the style of a 1993-1996 PC first-person shooter enemy: chunky visible pixels, no anti-aliasing, no blur, no soft gradients (4 to 6 flat shade steps per material), thin dark outline, painted-pixel detail like a high-resolution 1990s monster sprite.

FRAMES, left to right: 1) flinching and staggering back from a hit, still holding the shotgun; 2) struck, head thrown back, the shotgun dropping; 3) falling backwards at about 45 degrees; 4) nearly down, sitting with his back almost on the floor, small puffs of dust; 5) knocked out, lying completely flat and horizontal on his back, the shotgun lying beside him.

CORRECTION: the figures were cut off by the right and bottom edges (the dropped shotgun of the last frame). Draw every frame fully inside the image, with at least 12 px of empty background on every side and under the figures, none touching its neighbour.

BACKGROUND: perfectly flat, uniform solid magenta (#FF00FF) everywhere. No ground, no floor, no painted or cast shadow, no gradient, no scenery, no text, no letters, no numbers, no labels, no logo, no watermark, no symbols or emblems other than the ones described. FORMAT: wide landscape image. The only emblem allowed is the small US flag patch.
```


### Re-asks que se dejan fuera (y por que)

| Re-ask de la hoja | Por que no entra en el cupo de manana |
|---|---|
| Stormtrooper: las 6 hojas en lienzo mas alto (suelas cortadas) | 6 imagenes; el pipeline ya anade una suela oscura de 5 px (apenas se ve en juego) |
| Panzermensch: las 6 hojas mas altas, brazaletes sin letra, lanzamiento hacia la izquierda | 6 o mas imagenes; el brazalete ya se parchea (`patch`) y la suela se anade |
| Stormtrooper aim2/fire2 y charge | opcionales ("solo si el CEO lo quiere") |
| Sabueso walkL/walkR mas distintas, dolor | opcionales; la lunge es el cambio visible |
| Doughboy: vistas 3-4 del ataque sin brillo duplicado | el pipeline ya borra el brillo (`erase`), queda aceptable |
| General: frente y espalda con la bandera en el brazo derecho (5 hojas) | 5 imagenes para un defecto de ~3x2 px en juego |
| General: fire con mas espacio; death a la misma escala | ya resueltos por el pipeline (`split_x`, escala x1,39) |

Si sobra cupo, el siguiente por impacto seria el **Panzermensch** (hoja `fire` con brazaletes sin letra) y despues el
**General: death a escala**.

## 10. Control del cupo

Orden de ejecucion = numero de imagen (1 a 27). Cortes naturales: 2, 7, 14, 21, 23, 27. Dentro de una
pieza, el artillero necesita las 5 hojas para sustituir a su arte provisional; el Coloso y el Consorcio necesitan como minimo
`turn`, `fire` y `death` (el Consorcio, ademas, `rooted`).

Ahorro posible si hace falta recortar sin perder frames: pedir en 2 filas `walkL`+`walkR` del artillero y del Coloso
(2 imagenes menos, con el riesgo de que la segunda fila pierda consistencia).

No se ha generado ninguna imagen ni se ha abierto Gemini al preparar este paquete, no se ha tocado ningun otro fichero ni
hecho commit. Todo lo que se dice de como respondera Gemini es **no verificado** hasta que se use; los prompts del Coloso
y del Consorcio (personajes nuevos, sin referencia) son los de mayor riesgo de rechazo o de deriva.
