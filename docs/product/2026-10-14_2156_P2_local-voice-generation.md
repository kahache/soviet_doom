# Voces de los enemigos generadas en local, gratis, como Fooocus

Fecha: 2026-10-14, 21:56. Autor: investigación encargada por el PM. Instantánea
fechada, no documento vivo. Escrito en español porque es para el CEO (D7).
Lo que hay que decir y cómo: `docs/sound/VOICE-SCRIPT.md` (dueño de las
frases, los nombres de fichero y el registro de IA del §0.7). Las cadenas de
procesado y los derechos: `docs/sound/ENEMY-SOUNDS.md` §4. Este documento sólo
dice **qué herramienta instalar y cómo usarla**; no instala nada.

Etiquetas de honestidad: **VERIFICADO** = lo leí hoy en la página oficial o
lo medí en este PC. **NO VERIFICADO** = lo creo pero no lo he comprobado.
**HIPÓTESIS** = hay que probarlo con el oído.

---

## 1. Recomendación

**Instala primero Chatterbox (de Resemble AI) con el servidor de interfaz web
"Chatterbox-TTS-Server", en `Z:\Chatterbox`, usando como voz de referencia
10-15 segundos de TU propia voz.**

Por qué ésta y no otra:

1. **Es la única que cumple a la vez las cuatro cosas que pedimos**: alemán,
   inglés y ruso en un solo modelo (Chatterbox Multilingual, 23 idiomas,
   VERIFICADO en la ficha del modelo); un mando de **emoción/intensidad**
   ("Exaggeration", de 0,25 a 2) que sirve para pasar de un murmullo a un
   ladrido; cabe de sobra en 8 GB (unos 3,5 GB de VRAM según la documentación
   de NVIDIA para este modelo, NO VERIFICADO en este PC); y tiene un arranque
   de doble clic con modo portátil, como Fooocus.
2. **Licencia limpia**: código y pesos con licencia **MIT** (VERIFICADO en
   GitHub y en Hugging Face, campo `License: mit`). MIT no pone ninguna
   condición sobre el audio que generas, así que encaja con nuestro paquete
   CC BY-NC-SA 4.0 (D15). Lo confirma el sound-designer con tu registro
   (`VOICE-SCRIPT.md` §0.7).
3. **Resuelve el problema del acento**: con tu voz como referencia, el
   modelo pronuncia "Stellung halten" o "Vorwärts" en alemán correcto con tu
   timbre. Nada de alemán de caricatura (D11).

Dos avisos que no son pegas, pero tienes que saberlos:

- **Cada audio lleva una marca de agua inaudible** (PerTh, de Resemble AI;
  VERIFICADO en su README). No se oye y no estorba; lo anotamos en el registro.
- **Usa sólo tu propia voz como referencia.** Las voces que trae por defecto
  (en alemán, por ejemplo, una voz femenina de muestra) vienen, según el
  propio README, de "datos libremente disponibles en internet", y el servidor
  trae una carpeta de "voces predefinidas" cuyo origen no está documentado.
  Ninguna de las dos sirve: no sabemos de quién es la voz (`VOICE-SCRIPT.md`
  §0.7, "nunca clonar la voz de otra persona"). Tu voz clonada sigue siendo
  tu voz: sigue haciendo falta tu línea «las publico bajo CC BY-NC-SA 4.0».

**Segunda herramienta: de momento, ninguna.** Ningún generador de voz hace
bien gruñidos de dolor ni el último aliento de un soldado (las 6 filas sin
palabras: R07, R08, L07, L09, G03, G04). Lo más rápido es grabar esas seis
con el móvil (unos 10 minutos; ruido de garganta, nada reconocible) y, si no,
ya tenemos el respaldo CC0 descargado (`ENEMY-SOUNDS.md` §5). Si aun así
quieres probar IA para gritos, la candidata es **Dia** (Nari Labs, Apache 2.0,
sólo inglés, ~4,4 GB de VRAM, etiquetas de grito, jadeo y suspiro; VERIFICADO
en su README), pero no tiene instalador de un clic verificado: se haría más
adelante, vía Pinokio. **Applio** (conversión de voz) sólo tiene sentido si
quieres que tus tomas suenen a *otra* persona, y eso exige un modelo de voz de
alguien que lo haya consentido; ver §2.

---

## 2. Comparativa

Fecha de lectura de todas las páginas: 2026-10-14.

| Herramienta | Qué es | DE / EN / RU | Gritos, emoción, no verbal | VRAM | Instalación en Windows | Licencia del código | Licencia de los pesos | ¿Voz de referencia? | Veredicto |
|---|---|---|---|---|---|---|---|---|---|
| **Chatterbox Multilingual** (vía Chatterbox-TTS-Server) | Texto a voz | Sí / Sí / Sí (23 idiomas) | Emoción con el mando "Exaggeration" (0,25-2). Gritos: HIPÓTESIS, con Exaggeration alto. No verbal: no | ~3,5 GB (NVIDIA, NO VERIFICADO aquí) | `start.bat` con **modo portátil** (Python propio incrustado); también listado en Pinokio | MIT (modelo y servidor) | **MIT** | Opcional; usar la tuya (10-15 s) | **Instalar primero** |
| Chatterbox Turbo (mismo servidor) | Texto a voz | No / Sí / No | Etiquetas `[laugh]`, `[cough]`, `[chuckle]` | ~2,3 GB (NVIDIA) | Viene en el mismo servidor | MIT | MIT | Sí, la tuya | Útil para la Legión (inglés) |
| Applio (RVC) | **Conversión de voz**: tú grabas, cambia el timbre | Cualquiera (convierte lo que tú digas) | Todo lo que tú interpretes, gritos incluidos | NO VERIFICADO (no lo dice) | ZIP compilado `ApplioV3.6.6.zip` + `run-applio.bat`, muy parecido a Fooocus | MIT | MIT (los suyos) | Necesita un **modelo de voz destino** (.pth). Los que circulan por internet suelen ser clones de personas reales: **prohibidos**. Su pestaña TTS usa Microsoft Edge TTS en la nube: **descartada** (como SAPI en `ENEMY-SOUNDS.md` §3) | Sólo si se quiere disfrazar tu voz; no ahora |
| AllTalk TTS v2 | Interfaz que reúne XTTS, VITS, Piper, Parler, F5, más RVC | Sí / Sí / Sí (vía XTTS) | Débil: la emoción sale de la referencia | NO VERIFICADO | Instalador "standalone"; pide Git, Microsoft C++ Build Tools y Windows SDK | AGPL-3.0 (v1) | Según motor; XTTS = CPML | Sí | No: más piezas, el autor dice tener muy poco tiempo |
| Coqui XTTS-v2 | Texto a voz con clonación | Sí / Sí / Sí (17 idiomas) | Copia el estilo de la referencia | NO VERIFICADO | Vía AllTalk o Pinokio | MPL-2.0 (NO VERIFICADO) | **CPML: no comercial**. Para nosotros vale (somos no comerciales), pero lo anoto | Sí, ~6 s | Alternativa si Chatterbox falla |
| F5-TTS | Texto a voz con clonación | No oficial / Sí / No (base inglés-chino) | Copia la referencia | NO VERIFICADO | Sin instalador oficial para Windows | MIT | **CC-BY-NC** (por el dataset Emilia). Vale para nosotros, pero sin alemán | Sí | No |
| Kokoro | Texto a voz ligero | **No** / Sí / **No** | No | Muy poca | Varias interfaces de terceros | Apache 2.0 | Apache 2.0 | No clona | No: sin alemán |
| Piper | Texto a voz rápido, CPU | Sí / Sí / Sí (voces sueltas) | No: lectura plana | CPU | `pip`; sin interfaz web propia | GPL-3.0 | **Una licencia por voz** (cada dataset) | No clona | No: suena a locutor, no a soldado |
| GPT-SoVITS | Texto a voz con clonación | **No** / Sí / **No** | Copia la referencia | NO VERIFICADO | **Paquete integrado** `.7z` + `go-webui.bat` (estilo Fooocus) | MIT | MIT | Sí, ~5 s | No: sin alemán |
| StyleTTS2 | Texto a voz | **No** / Sí / **No** | Limitada | NO VERIFICADO | Manual | MIT | Condición: avisar al oyente de que es sintético y sólo voces con permiso | Sí | No |
| Bark (Suno) | Texto a audio generativo | Sí / Sí / Sí (13 idiomas) | `[laughs]`, `[sighs]`, `[gasps]`, `[clears throat]`; resultados al azar | 12 GB completo; **8 GB con modelos pequeños** | Manual o Pinokio (NO VERIFICADO) | MIT | MIT, uso comercial permitido | No clona: 100+ voces predefinidas | No: sin mantenimiento desde 2023, imprevisible |
| Dia (Nari Labs) | Texto a diálogo | No / Sí / No | ~21 etiquetas: gritos, jadeos, suspiros, tos | ~4,4 GB (fp16) | `python app.py` (Gradio); Pinokio NO VERIFICADO | Apache 2.0 | NO VERIFICADO aparte | Opcional (la tuya) | Segunda opción, sólo para gritos en inglés |
| Fish Audio OpenAudio S1-mini | Texto a voz con marcadores | Sí / Sí / Sí | Marcadores `(shouting)`, `(screaming)`, `(groaning)`, `(panting)`, `(painful)` | NO VERIFICADO | Sin paquete de un clic; descarga **con cuenta** en Hugging Face | Fish Audio Community License | **CC-BY-NC-SA-4.0** (compatible con la nuestra) | Sí | A vigilar: lo más rico en gritos, pero exige cuenta y montaje manual |
| Pinokio | **Lanzador** de un clic para muchas de las de arriba | — | — | — | Instalador propio; todo queda en su carpeta "home" | MIT | — | — | Útil para probar varias; tiene ficha de Chatterbox-TTS-Server (beta.pinokio.co) |

Notas a la tabla:

- "Licencia de los pesos" es la que manda sobre el audio generado. MIT,
  Apache 2.0 y CC-BY-NC-SA son compatibles con un mod gratuito bajo CC BY-NC-SA
  4.0. **CPML (XTTS) y CC-BY-NC (F5)** prohíben el uso comercial: a nosotros
  no nos afecta hoy, pero si el mod se vendiera algún día, esas tomas tendrían
  que rehacerse. Con Chatterbox (MIT) ese problema no existe.
- Esto no es asesoramiento legal; el sound-designer revisa los términos con
  tu registro (`VOICE-SCRIPT.md` §0.7).

---

## 3. Instalación paso a paso (Chatterbox-TTS-Server)

### 3.0 Lo que ya he comprobado en tu PC (VERIFICADO, 2026-10-14)

| Cosa | Estado |
|---|---|
| Tarjeta gráfica | NVIDIA GeForce RTX 3050, 8192 MiB, driver 560.94 (el servidor pide 525 o más para la serie 30) |
| Espacio libre en `C:` | **11,3 GB: casi lleno.** Nada de esto debe ir a `C:` |
| Espacio libre en `Z:` | **153,8 GB**: aquí va todo, junto a `Z:\Fooocus` |
| Git | Instalado (2.55) |
| Python del sistema | 3.14.6. Vale: el servidor sólo lo usa para arrancar y luego se trae su propio Python 3.10 portátil |
| ffmpeg | Instalado (`C:\ProgramData\chocolatey\bin\ffmpeg.exe`) |
| Herramientas de voz ya instaladas | **Ninguna.** Miré `Z:\`, tu Escritorio, `%LOCALAPPDATA%\Programs` y `C:\Program Files`: hay Fooocus, Ollama, Python y una carpeta `whisper` en la caché (eso es reconocimiento de voz, no generación) |

**Importante:** el programa, por defecto, guarda los modelos (unos 4-6 GB) y la
caché de descargas en `C:\Users\littl\.cache` y en `AppData`, es decir, en
`C:`, que sólo tiene 11 GB. Por eso en el paso 3 creamos un lanzador que le
dice que lo guarde todo en `Z:`. **Arranca siempre con ese lanzador, también
la primera vez.**

**No tengas Fooocus abierto a la vez**: los dos se pelearían por los 8 GB de
la tarjeta.

### 3.1 Paso 1: abrir PowerShell

Tecla Windows, escribe `PowerShell`, pulsa Enter (no hace falta "como
administrador"; mejor sin administrador). Copia y pega cada bloque de abajo
y pulsa Enter.

### 3.2 Paso 2: descargar el programa en `Z:\Chatterbox`

Página oficial del proyecto: <https://github.com/devnen/Chatterbox-TTS-Server>

```powershell
New-Item -ItemType Directory -Force "Z:\Chatterbox"
New-Item -ItemType Directory -Force "Z:\Chatterbox\hf_cache"
New-Item -ItemType Directory -Force "Z:\Chatterbox\pip_cache"
New-Item -ItemType Directory -Force "Z:\Chatterbox\tmp"
git clone https://github.com/devnen/Chatterbox-TTS-Server.git "Z:\Chatterbox\Chatterbox-TTS-Server"
```

Si `git clone` diera error, alternativa sin Git: en la página del proyecto,
botón verde **Code → Download ZIP**, y descomprime el ZIP de modo que quede la
carpeta `Z:\Chatterbox\Chatterbox-TTS-Server` (con `start.bat` dentro, no
una carpeta más abajo).

### 3.3 Paso 3: crear el lanzador que guarda todo en `Z:`

Pega este bloque entero (desde `@'` hasta `'@` incluidos):

```powershell
@'
@echo off
set HF_HOME=Z:\Chatterbox\hf_cache
set PIP_CACHE_DIR=Z:\Chatterbox\pip_cache
set TEMP=Z:\Chatterbox\tmp
set TMP=Z:\Chatterbox\tmp
cd /d Z:\Chatterbox\Chatterbox-TTS-Server
call start.bat
'@ | Set-Content -Encoding ascii "Z:\Chatterbox\arrancar-chatterbox.bat"
```

Esto crea `Z:\Chatterbox\arrancar-chatterbox.bat`. Sólo cambia dónde guarda
cosas este programa; no toca nada de Windows.

### 3.4 Paso 4: acceso directo en el Escritorio

```powershell
$atajo = (New-Object -ComObject WScript.Shell).CreateShortcut("C:\Users\littl\Desktop\Chatterbox.lnk")
$atajo.TargetPath = "Z:\Chatterbox\arrancar-chatterbox.bat"
$atajo.WorkingDirectory = "Z:\Chatterbox\Chatterbox-TTS-Server"
$atajo.Save()
```

Aparece un icono **Chatterbox** en el Escritorio, al lado del de Fooocus.

### 3.5 Paso 5: primera instalación (una sola vez, 15-40 minutos)

1. Doble clic en el icono **Chatterbox** del Escritorio. Se abre una ventana
   negra.
2. Te pregunta si quieres **modo portátil** (Portable Mode). Es la opción
   por defecto: pulsa **Enter**.
3. Detecta la tarjeta NVIDIA y enseña un menú. La opción por defecto es
   `[2] NVIDIA GPU (CUDA 12.1)`, la correcta para una RTX 3050: pulsa
   **Enter**.
4. Espera. Descarga Python, PyTorch y el resto (varios GB). Si Windows
   Defender o el cortafuegos preguntan, permite el acceso sólo en **redes
   privadas**.
5. Cuando termine, la ventana muestra la dirección del programa. La primera
   vez que generes, además descargará el modelo (unos 2-4 GB más) a
   `Z:\Chatterbox\hf_cache`.

Lo exacto que muestra cada pregunta de los pasos 2-3 viene del README del
proyecto; el texto en pantalla puede variar un poco (NO VERIFICADO en este PC,
no he instalado nada).

### 3.6 Paso 6: abrir la interfaz

Abre el navegador en **<http://localhost:8004>**

(Fooocus usa otro puerto, 7865, así que no chocan; pero recuerda no tenerlos
abiertos a la vez por la tarjeta.)

### 3.7 Uso diario

- Arrancar: doble clic en el icono **Chatterbox**. Las veces siguientes
  detecta que ya está instalado y arranca directamente.
- Abrir: <http://localhost:8004>
- Cerrar: cierra la ventana negra (o pulsa `Ctrl+C` dentro de ella).

### 3.8 Si algo falla

- **Escoge el modelo multilingüe.** Arriba de la interfaz hay un selector de
  motor (Original / Turbo / Multilingual) y, con el multilingüe, un
  desplegable de idioma. Si no apareciera, abre
  `Z:\Chatterbox\Chatterbox-TTS-Server\config.yaml` con el Bloc de notas,
  busca `repo_id:` en la sección `model:` y pon `repo_id: multilingual`;
  guarda, cierra la ventana negra y vuelve a arrancar.
- Si la ventana dice "Python 3.10+ not found", abre PowerShell y escribe
  `python --version`: debe salir 3.14.6. Si sale, avísame con una foto de la
  ventana.
- Si se queda sin memoria de vídeo: cierra Fooocus, el navegador con muchas
  pestañas y cualquier juego.

---

## 4. Cómo usarlo para nuestras frases

### 4.1 Antes de nada: tu voz de referencia (10 minutos, una vez)

1. Graba con el móvil, como dice `VOICE-SCRIPT.md` §0.2-§0.4 (habitación
   seca, 20-30 cm), **dos clips de 10-15 segundos**, hablando tranquilo:
   - `ceo_ref_de`: lee despacio las frases alemanas del §0.6 de
     `VOICE-SCRIPT.md` (Stellung halten, Augen auf, Ruhe da hinten,
     Vorwärts...), como te salgan.
   - `ceo_ref_en`: lee en inglés las frases de la Legión (Sector four, clear.
     Copy. Holding position...).
   Por qué dos: el README avisa de que si la referencia está en otro idioma
   que el texto, el acento de la referencia se cuela. Si prefieres un solo
   clip en español, entonces pon **CFG en 0** (lo recomienda el README para
   evitar el acento), a cambio de menos control del ritmo.
2. Pásalos a WAV mono (el servidor acepta `.wav` y `.mp3`; si el móvil te da
   `.m4a`, conviértelo). Ejemplo, cambiando las rutas de origen por las tuyas:

   ```powershell
   ffmpeg -i "C:\Users\littl\Desktop\ceo_ref_de.m4a" -ac 1 -ar 24000 "Z:\Chatterbox\Chatterbox-TTS-Server\reference_audio\ceo_ref_de.wav"
   ffmpeg -i "C:\Users\littl\Desktop\ceo_ref_en.m4a" -ac 1 -ar 24000 "Z:\Chatterbox\Chatterbox-TTS-Server\reference_audio\ceo_ref_en.wav"
   ```

   (También puedes subirlos desde la interfaz, en el modo de clonación de
   voz: "Voice Cloning", botón de subir archivo.)
3. En la interfaz: modo **Voice Cloning**, elige tu clip. **Nunca** uses las
   voces de "Predefined Voices" ni la voz de muestra que pone por defecto al
   cambiar de idioma.

### 4.2 Los mandos que importan

Nombres según el README y la aplicación de ejemplo de Resemble AI; los
números de partida son los que recomienda el propio README para habla
expresiva. El resto es **HIPÓTESIS** hasta que lo oigas.

| Mando | Qué hace | Murmullo (idle) | Ladrido (alerta) | El General |
|---|---|---|---|---|
| **Exaggeration** (0,25-2; defecto 0,5) | Intensidad emocional. Más alto = más intenso y más rápido | 0,3-0,4 | **1,0-1,4** | 0,3 |
| **CFG / CFG Weight** (0-1; defecto 0,5) | Lo pegado que va a la referencia y al ritmo. Bajarlo compensa la prisa que da Exaggeration | 0,5 | **0,3** | 0,5-0,6 |
| **Temperature** (defecto 0,8) | Variación entre tomas. Más alto = más vivo, más fallos | 0,8 | 0,9-1,0 | 0,6 |
| **Seed** (0 = al azar) | Fíjala cuando una toma te guste, para poder repetirla y anotarla | — | — | — |
| **Speed Factor** | Velocidad. Mejor dejarlo en 1 y que el sound-designer ajuste | 1 | 1 | 1 |

Truco de texto (HIPÓTESIS, típico en estos modelos): una sola palabra muy
corta a veces sale con basura al final. Si "Feind!" sale raro, escribe
`Feind! Feind!` y el sound-designer corta una. Los signos cuentan: `!` empuja
hacia el grito, `.` hacia la calma, `...` alarga y apaga.

### 4.3 Ejemplos con tres filas del guion

**R04 — `SDRRISIT` — «Feind!» (fusilero del Reich, ladrido fuerte, ≤ 0,5 s, 5 tomas)**

- Motor: Multilingual. Idioma: **German (de)**. Voz: `ceo_ref_de.wav`.
- Texto: `Feind!`
- Exaggeration 1,2 · CFG 0,3 · Temperature 0,9 · Seed 0.
- Genera 8-10 veces y quédate con las 5 más secas. Debe sonar a soldado
  dando un aviso, no a villano de película (D11): si suena teatral, baja
  Exaggeration a 0,9.

**G02 — `SDGENSUM` — «Vorwärts.» (el General, la frase que el jugador tiene que entender, ≤ 1,2 s, 8 tomas)**

- Motor: Multilingual. Idioma: **German (de)**. Voz: `ceo_ref_de.wav`.
- Texto: `Vorwärts.` (con punto, nunca con exclamación: él no grita).
- Exaggeration 0,3 · CFG 0,6 · Temperature 0,6.
- No intentes poner voz grave: el sound-designer baja 4 semitonos después
  (`GENERAL-SLOT`). Que se entienda la palabra es lo único que importa.

**L04 — `SDLTRSIT` — «Contact!» (soldado de la Legión, por radio, ≤ 0,6 s, 5 tomas)**

- Motor: Multilingual, idioma **English (en)**, o el motor **Turbo** (sólo
  inglés). Voz: `ceo_ref_en.wav`.
- Texto: `Contact!`
- Exaggeration 1,1 · CFG 0,3 · Temperature 0,9.
- Consonantes claras: la radio (`LEGION-RADIO`) se come graves y agudos.

### 4.4 Grito frente a grito de muerte

En nuestro guion **nadie muere gritando**: R08 y L09 son un aliento que se
rompe, G04 un suspiro largo que se apaga como una máquina. Con Chatterbox:

| Lo que buscas | Texto | Mandos | Esperanza |
|---|---|---|---|
| Ladrido / grito de alerta | Palabra corta con `!` | Exaggeration 1,0-1,4, CFG 0,3 | Buena (HIPÓTESIS) |
| Dolor (R07, L07, G03) | `Ngh!` / `Agh!` / `Hm.` | Exaggeration 1,0, CFG 0,3 | **Floja**: puede leerlo como palabra |
| Muerte (R08, L09, G04) | `Hhh... ah...` / `Sani...` (R09) | Exaggeration 0,6, CFG 0,3, Temperature 1,0 | **Floja**; R09 «Sani...» sí debería salir |

Para las 6 filas sin palabras, lo realista es grabarlas tú (10 minutos) o
quedarse con el respaldo CC0. Prueba la IA si te apetece, pero no pierdas más
de un rato.

### 4.5 Dónde guardar y cómo nombrar

1. Cada toma que te guste: botón de descarga del reproductor de la interfaz
   (va a tu carpeta Descargas).
2. Muévela a la carpeta que lee el sound-designer, **`work/audio/voice_takes/`**
   del repo (`VOICE-SCRIPT.md` §0.5; está en gitignore, no entra en git):

   ```powershell
   New-Item -ItemType Directory -Force "C:\Users\littl\Desktop\Claude\soviet_doom\work\audio\voice_takes"
   Move-Item "C:\Users\littl\Downloads\<nombre-que-te-haya-dado>.wav" "C:\Users\littl\Desktop\Claude\soviet_doom\work\audio\voice_takes\R04_SDRRISIT_ai_chatterbox_20261014_t01.wav"
   ```

3. Nombre: el de `VOICE-SCRIPT.md` §0.5 para IA,
   `<fila>_<lump>_ai_chatterbox_<fecha>.wav`, más `_t01`, `_t02`... porque
   aquí cada toma sale en un fichero aparte (propuesta mía; el
   sound-designer decide si la acepta). Guárdalas **tal como salen**, sin
   editar.
4. **Registro obligatorio** (`VOICE-SCRIPT.md` §0.7): una línea por fichero en
   `work/audio/voice_takes/AI-LOG.csv`. Cabecera y ejemplo:

   ```
   fichero;herramienta;version_o_modelo;fecha;plan;licencia_de_uso;voz;texto;ajustes
   R04_SDRRISIT_ai_chatterbox_20261014_t01.wav;Chatterbox-TTS-Server (github.com/devnen/Chatterbox-TTS-Server) + Chatterbox Multilingual (Resemble AI);<el modelo que muestre la interfaz>;2026-10-14;gratuito, local;MIT, https://huggingface.co/ResembleAI/chatterbox, leída 2026-10-14, "Licensed under MIT";clonada de mi propia voz (ceo_ref_de.wav);Feind!;de, exaggeration 1.2, cfg 0.3, temperature 0.9, seed <la que salga>
   ```

5. Y la línea en el chat de siempre: «Las tomas de voz son mías y las publico
   bajo CC BY-NC-SA 4.0 (D15)». Sin ella no se usa ninguna, ni grabada ni
   generada con tu voz.

---

## 5. Fuentes (leídas el 2026-10-14)

- Chatterbox, código y README (modelos, idiomas, consejos, marca de agua): <https://github.com/resemble-ai/chatterbox>
- Chatterbox, ficha del modelo y ficheros (licencia MIT, 23 idiomas): <https://huggingface.co/ResembleAI/chatterbox>
- Aplicación de ejemplo multilingüe (mandos y voces por defecto): <https://github.com/resemble-ai/chatterbox/blob/master/multilingual_app.py>
- Chatterbox-TTS-Server (modo portátil, menú, puerto 8004, `config.yaml`): <https://github.com/devnen/Chatterbox-TTS-Server>
- VRAM de Chatterbox según NVIDIA: <https://docs.nvidia.com/ace-for-games/chatterbox-tts/getting-started.html>
- Ficha en Pinokio: <https://beta.pinokio.co/apps/github-com-devnen-chatterbox-tts-server>
- Applio y su versión 3.6.6: <https://github.com/IAHispano/Applio>, <https://github.com/IAHispano/Applio/releases>; pestaña TTS con Edge TTS (resumen de terceros): <https://deepwiki.com/IAHispano/Applio/7.4-tts-tab>
- AllTalk v2: <https://github.com/erew123/alltalk_tts/tree/alltalkbeta>
- XTTS-v2 (CPML): <https://huggingface.co/coqui/XTTS-v2>
- F5-TTS: <https://github.com/SWivid/F5-TTS>
- Kokoro (voces): <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md>
- Piper: <https://github.com/OHF-Voice/piper1-gpl>
- GPT-SoVITS: <https://github.com/RVC-Boss/GPT-SoVITS>
- StyleTTS2: <https://github.com/yl4579/StyleTTS2>
- Bark: <https://github.com/suno-ai/bark>
- Dia: <https://github.com/nari-labs/dia>
- OpenAudio S1-mini: <https://huggingface.co/fishaudio/openaudio-s1-mini>; Fish Speech: <https://github.com/fishaudio/fish-speech>
- Pinokio: <https://github.com/pinokiocomputer/pinokio>
