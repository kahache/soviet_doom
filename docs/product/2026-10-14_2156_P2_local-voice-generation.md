# Enemy voices generated locally, for free, like Fooocus

Date: 2026-10-14, 21:56. Author: research commissioned by the PM. Dated
snapshot, not a living document. Written in English (D129: repo docs are
English; Spanish only in chat with the CEO).
What to say and how: `docs/sound/VOICE-SCRIPT.md` (owner of the lines, the
file names and the AI log of §0.7). The processing chains and the rights:
`docs/sound/ENEMY-SOUNDS.md` §4. This document only says **which tool to
install and how to use it**; it installs nothing.

Honesty labels: **VERIFIED** = I read it today on the official page or
measured it on this PC. **NOT VERIFIED** = I believe it but have not checked
it. **HYPOTHESIS** = it has to be tried by ear.

---

## 1. Recommendation

**Install Chatterbox (by Resemble AI) first, with the web-interface server
"Chatterbox-TTS-Server", in `Z:\Chatterbox`, using 10-15 seconds of YOUR own
voice as the reference voice.**

Why this one and not another:

1. **It is the only one that meets all four things we ask for at once**:
   German, English and Russian in a single model (Chatterbox Multilingual, 23
   languages, VERIFIED on the model card); an **emotion/intensity** knob
   ("Exaggeration", from 0.25 to 2) that lets you go from a murmur to a bark;
   it fits easily in 8 GB (about 3.5 GB of VRAM according to NVIDIA's
   documentation for this model, NOT VERIFIED on this PC); and it has a
   double-click start with a portable mode, like Fooocus.
2. **Clean licence**: code and weights under the **MIT** licence (VERIFIED on
   GitHub and on Hugging Face, field `License: mit`). MIT places no condition
   on the audio you generate, so it fits our CC BY-NC-SA 4.0 package (D15).
   The sound-designer confirms it with your log (`VOICE-SCRIPT.md` §0.7).
3. **It solves the accent problem**: with your voice as the reference, the
   model pronounces "Stellung halten" or "Vorwärts" in correct German with
   your timbre. No caricature German (D11).

Two warnings that are not drawbacks, but you need to know them:

- **Every audio file carries an inaudible watermark** (PerTh, by Resemble AI;
  VERIFIED in its README). You cannot hear it and it does not get in the way;
  we note it in the log.
- **Use only your own voice as the reference.** The voices it ships with by
  default (in German, for example, a sample female voice) come, according to
  the README itself, from "freely available data on the internet", and the
  server ships a "predefined voices" folder whose origin is not documented.
  Neither is usable: we do not know whose voice it is (`VOICE-SCRIPT.md`
  §0.7, "never clone another person's voice"). Your cloned voice is still your
  voice: your line «las publico bajo CC BY-NC-SA 4.0» (CEO: "I publish them under CC BY-NC-SA 4.0") is still needed.

**Second tool: none for now.** No voice generator does pain grunts or a
soldier's last breath well (the 6 rows without words: R07, R08, L07, L09, G03,
G04). The quickest thing is to record those six with your phone (about 10
minutes; throat noise, nothing recognisable) and, failing that, we already
have the downloaded CC0 fallback (`ENEMY-SOUNDS.md` §5). If you still want to
try AI for screams, the candidate is **Dia** (Nari Labs, Apache 2.0, English
only, ~4.4 GB of VRAM, tags for scream, gasp and sigh; VERIFIED in its
README), but it has no verified one-click installer: it would be done later,
via Pinokio. **Applio** (voice conversion) only makes sense if you want your
takes to sound like *another* person, and that requires a voice model of
someone who has consented; see §2.

---

## 2. Comparison

Date all pages were read: 2026-10-14.

| Tool | What it is | DE / EN / RU | Screams, emotion, non-verbal | VRAM | Installation on Windows | Code licence | Weights licence | Reference voice? | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **Chatterbox Multilingual** (via Chatterbox-TTS-Server) | Text to speech | Yes / Yes / Yes (23 languages) | Emotion with the "Exaggeration" knob (0.25-2). Screams: HYPOTHESIS, with high Exaggeration. Non-verbal: no | ~3.5 GB (NVIDIA, NOT VERIFIED here) | `start.bat` with **portable mode** (its own embedded Python); also listed in Pinokio | MIT (model and server) | **MIT** | Optional; use yours (10-15 s) | **Install first** |
| Chatterbox Turbo (same server) | Text to speech | No / Yes / No | Tags `[laugh]`, `[cough]`, `[chuckle]` | ~2.3 GB (NVIDIA) | Comes in the same server | MIT | MIT | Yes, yours | Useful for the Legion (English) |
| Applio (RVC) | **Voice conversion**: you record, it changes the timbre | Any (it converts whatever you say) | Everything you perform, screams included | NOT VERIFIED (it does not say) | Compiled ZIP `ApplioV3.6.6.zip` + `run-applio.bat`, very similar to Fooocus | MIT | MIT (their own) | Needs a **target voice model** (.pth). The ones circulating on the internet are usually clones of real people: **forbidden**. Its TTS tab uses Microsoft Edge TTS in the cloud: **discarded** (like SAPI in `ENEMY-SOUNDS.md` §3) | Only if you want to disguise your voice; not now |
| AllTalk TTS v2 | Interface that bundles XTTS, VITS, Piper, Parler, F5, plus RVC | Yes / Yes / Yes (via XTTS) | Weak: the emotion comes from the reference | NOT VERIFIED | "Standalone" installer; needs Git, Microsoft C++ Build Tools and Windows SDK | AGPL-3.0 (v1) | Depends on the engine; XTTS = CPML | Yes | No: more pieces, the author says they have very little time |
| Coqui XTTS-v2 | Text to speech with cloning | Yes / Yes / Yes (17 languages) | Copies the style of the reference | NOT VERIFIED | Via AllTalk or Pinokio | MPL-2.0 (NOT VERIFIED) | **CPML: non-commercial**. Fine for us (we are non-commercial), but I note it | Yes, ~6 s | Alternative if Chatterbox fails |
| F5-TTS | Text to speech with cloning | Not official / Yes / No (English-Chinese base) | Copies the reference | NOT VERIFIED | No official installer for Windows | MIT | **CC-BY-NC** (because of the Emilia dataset). Fine for us, but no German | Yes | No |
| Kokoro | Lightweight text to speech | **No** / Yes / **No** | No | Very little | Several third-party interfaces | Apache 2.0 | Apache 2.0 | Does not clone | No: no German |
| Piper | Fast text to speech, CPU | Yes / Yes / Yes (individual voices) | No: flat reading | CPU | `pip`; no web interface of its own | GPL-3.0 | **One licence per voice** (each dataset) | Does not clone | No: sounds like an announcer, not a soldier |
| GPT-SoVITS | Text to speech with cloning | **No** / Yes / **No** | Copies the reference | NOT VERIFIED | **Integrated package** `.7z` + `go-webui.bat` (Fooocus style) | MIT | MIT | Yes, ~5 s | No: no German |
| StyleTTS2 | Text to speech | **No** / Yes / **No** | Limited | NOT VERIFIED | Manual | MIT | Condition: tell the listener it is synthetic and only use voices with permission | Yes | No |
| Bark (Suno) | Generative text to audio | Yes / Yes / Yes (13 languages) | `[laughs]`, `[sighs]`, `[gasps]`, `[clears throat]`; random results | 12 GB full; **8 GB with small models** | Manual or Pinokio (NOT VERIFIED) | MIT | MIT, commercial use allowed | Does not clone: 100+ predefined voices | No: unmaintained since 2023, unpredictable |
| Dia (Nari Labs) | Text to dialogue | No / Yes / No | ~21 tags: screams, gasps, sighs, coughs | ~4.4 GB (fp16) | `python app.py` (Gradio); Pinokio NOT VERIFIED | Apache 2.0 | NOT VERIFIED separately | Optional (yours) | Second option, only for screams in English |
| Fish Audio OpenAudio S1-mini | Text to speech with markers | Yes / Yes / Yes | Markers `(shouting)`, `(screaming)`, `(groaning)`, `(panting)`, `(painful)` | NOT VERIFIED | No one-click package; download **with an account** on Hugging Face | Fish Audio Community License | **CC-BY-NC-SA-4.0** (compatible with ours) | Yes | One to watch: the richest in screams, but needs an account and manual setup |
| Pinokio | One-click **launcher** for many of the above | — | — | — | Its own installer; everything stays in its "home" folder | MIT | — | — | Useful for trying several; has a Chatterbox-TTS-Server page (beta.pinokio.co) |

Notes on the table:

- "Weights licence" is the one that governs the generated audio. MIT,
  Apache 2.0 and CC-BY-NC-SA are compatible with a free mod under CC BY-NC-SA
  4.0. **CPML (XTTS) and CC-BY-NC (F5)** forbid commercial use: it does not
  affect us today, but if the mod were ever sold, those takes would have to be
  redone. With Chatterbox (MIT) that problem does not exist.
- This is not legal advice; the sound-designer reviews the terms with your
  log (`VOICE-SCRIPT.md` §0.7).

---

## 3. Step-by-step installation (Chatterbox-TTS-Server)

### 3.0 What I have already checked on your PC (VERIFIED, 2026-10-14)

| Item | State |
|---|---|
| Graphics card | NVIDIA GeForce RTX 3050, 8192 MiB, driver 560.94 (the server asks for 525 or higher for the 30 series) |
| Free space on `C:` | **11.3 GB: almost full.** None of this should go to `C:` |
| Free space on `Z:` | **153.8 GB**: everything goes here, next to `Z:\Fooocus` |
| Git | Installed (2.55) |
| System Python | 3.14.6. That is fine: the server only uses it to start and then brings its own portable Python 3.10 |
| ffmpeg | Installed (`C:\ProgramData\chocolatey\bin\ffmpeg.exe`) |
| Voice tools already installed | **None.** I looked in `Z:\`, your Desktop, `%LOCALAPPDATA%\Programs` and `C:\Program Files`: there are Fooocus, Ollama, Python and a `whisper` folder in the cache (that is speech recognition, not generation) |

**Important:** by default the program stores the models (about 4-6 GB) and the
download cache in `C:\Users\littl\.cache` and in `AppData`, that is, on `C:`,
which has only 11 GB. That is why in step 3 we create a launcher that tells it
to store everything on `Z:`. **Always start with that launcher, the first time
too.**

**Do not have Fooocus open at the same time**: the two would fight over the
card's 8 GB.

### 3.1 Step 1: open PowerShell

Windows key, type `PowerShell`, press Enter (it does not need to be "as
administrator"; better without administrator). Copy and paste each block below
and press Enter.

### 3.2 Step 2: download the program to `Z:\Chatterbox`

Official project page: <https://github.com/devnen/Chatterbox-TTS-Server>

```powershell
New-Item -ItemType Directory -Force "Z:\Chatterbox"
New-Item -ItemType Directory -Force "Z:\Chatterbox\hf_cache"
New-Item -ItemType Directory -Force "Z:\Chatterbox\pip_cache"
New-Item -ItemType Directory -Force "Z:\Chatterbox\tmp"
git clone https://github.com/devnen/Chatterbox-TTS-Server.git "Z:\Chatterbox\Chatterbox-TTS-Server"
```

If `git clone` gave an error, alternative without Git: on the project page,
green button **Code → Download ZIP**, and unzip the ZIP so that the folder
`Z:\Chatterbox\Chatterbox-TTS-Server` exists (with `start.bat` inside it, not
one folder further down).

### 3.3 Step 3: create the launcher that stores everything on `Z:`

Paste this whole block (from `@'` to `'@` inclusive):

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

This creates `Z:\Chatterbox\arrancar-chatterbox.bat`. It only changes where
this program stores things; it does not touch anything in Windows.

### 3.4 Step 4: shortcut on the Desktop

```powershell
$atajo = (New-Object -ComObject WScript.Shell).CreateShortcut("C:\Users\littl\Desktop\Chatterbox.lnk")
$atajo.TargetPath = "Z:\Chatterbox\arrancar-chatterbox.bat"
$atajo.WorkingDirectory = "Z:\Chatterbox\Chatterbox-TTS-Server"
$atajo.Save()
```

A **Chatterbox** icon appears on the Desktop, next to the Fooocus one.

### 3.5 Step 5: first installation (once only, 15-40 minutes)

1. Double-click the **Chatterbox** icon on the Desktop. A black window opens.
2. It asks whether you want **portable mode** (Portable Mode). It is the
   default option: press **Enter**.
3. It detects the NVIDIA card and shows a menu. The default option is
   `[2] NVIDIA GPU (CUDA 12.1)`, the right one for an RTX 3050: press
   **Enter**.
4. Wait. It downloads Python, PyTorch and the rest (several GB). If Windows
   Defender or the firewall ask, allow access on **private networks** only.
5. When it finishes, the window shows the program's address. The first time
   you generate, it will also download the model (about 2-4 GB more) to
   `Z:\Chatterbox\hf_cache`.

The exact wording of each question in steps 2-3 comes from the project's
README; the on-screen text may vary a little (NOT VERIFIED on this PC, I have
not installed anything).

### 3.6 Step 6: open the interface

Open the browser at **<http://localhost:8004>**

(Fooocus uses another port, 7865, so they do not clash; but remember not to
have them open at the same time because of the card.)

### 3.7 Daily use

- Start: double-click the **Chatterbox** icon. The following times it detects
  that it is already installed and starts directly.
- Open: <http://localhost:8004>
- Close: close the black window (or press `Ctrl+C` inside it).

### 3.8 If something fails

- **Choose the multilingual model.** At the top of the interface there is an
  engine selector (Original / Turbo / Multilingual) and, with the
  multilingual one, a language dropdown. If it did not appear, open
  `Z:\Chatterbox\Chatterbox-TTS-Server\config.yaml` with Notepad, look for
  `repo_id:` in the `model:` section and set `repo_id: multilingual`; save,
  close the black window and start again.
- If the window says "Python 3.10+ not found", open PowerShell and type
  `python --version`: it should show 3.14.6. If it does, let me know with a
  photo of the window.
- If it runs out of video memory: close Fooocus, the browser with many tabs
  and any game.

---

## 4. How to use it for our lines

### 4.1 First of all: your reference voice (10 minutes, once)

1. Record with your phone, as `VOICE-SCRIPT.md` §0.2-§0.4 says (dry room,
   20-30 cm), **two clips of 10-15 seconds**, speaking calmly:
   - `ceo_ref_de`: slowly read the German lines of §0.6 of
     `VOICE-SCRIPT.md` (Stellung halten, Augen auf, Ruhe da hinten,
     Vorwärts...), however they come out.
   - `ceo_ref_en`: read the Legion's lines in English (Sector four, clear.
     Copy. Holding position...).
   Why two: the README warns that if the reference is in a different language
   from the text, the accent of the reference leaks in. If you prefer a single
   clip in Spanish, then set **CFG to 0** (the README recommends it to avoid
   the accent), at the cost of less control over the rhythm.
2. Convert them to mono WAV (the server accepts `.wav` and `.mp3`; if your
   phone gives you `.m4a`, convert it). Example, changing the source paths to
   your own:

   ```powershell
   ffmpeg -i "C:\Users\littl\Desktop\ceo_ref_de.m4a" -ac 1 -ar 24000 "Z:\Chatterbox\Chatterbox-TTS-Server\reference_audio\ceo_ref_de.wav"
   ffmpeg -i "C:\Users\littl\Desktop\ceo_ref_en.m4a" -ac 1 -ar 24000 "Z:\Chatterbox\Chatterbox-TTS-Server\reference_audio\ceo_ref_en.wav"
   ```

   (You can also upload them from the interface, in the voice-cloning mode:
   "Voice Cloning", upload-file button.)
3. In the interface: **Voice Cloning** mode, choose your clip. **Never** use
   the "Predefined Voices" voices or the sample voice it sets by default when
   you change language.

### 4.2 The knobs that matter

Names according to the README and Resemble AI's example application; the
starting numbers are those the README itself recommends for expressive speech.
The rest is a **HYPOTHESIS** until you hear it.

| Knob | What it does | Murmur (idle) | Bark (alert) | The General |
|---|---|---|---|---|
| **Exaggeration** (0.25-2; default 0.5) | Emotional intensity. Higher = more intense and faster | 0.3-0.4 | **1.0-1.4** | 0.3 |
| **CFG / CFG Weight** (0-1; default 0.5) | How closely it sticks to the reference and the rhythm. Lowering it compensates for the rush that Exaggeration causes | 0.5 | **0.3** | 0.5-0.6 |
| **Temperature** (default 0.8) | Variation between takes. Higher = livelier, more failures | 0.8 | 0.9-1.0 | 0.6 |
| **Seed** (0 = random) | Fix it when you like a take, so you can repeat it and log it | — | — | — |
| **Speed Factor** | Speed. Better left at 1 and let the sound-designer adjust | 1 | 1 | 1 |

Text trick (HYPOTHESIS, typical in these models): a single very short word
sometimes comes out with garbage at the end. If "Feind!" comes out odd, write
`Feind! Feind!` and the sound-designer cuts one. Punctuation counts: `!` pushes
towards the scream, `.` towards calm, `...` lengthens and fades.

### 4.3 Examples with three rows of the script

**R04 — `SDRRISIT` — «Feind!» (Reich rifleman, loud bark, ≤ 0.5 s, 5 takes)**

- Engine: Multilingual. Language: **German (de)**. Voice: `ceo_ref_de.wav`.
- Text: `Feind!`
- Exaggeration 1.2 · CFG 0.3 · Temperature 0.9 · Seed 0.
- Generate 8-10 times and keep the 5 driest. It should sound like a soldier
  giving a warning, not like a movie villain (D11): if it sounds theatrical,
  lower Exaggeration to 0.9.

**G02 — `SDGENSUM` — «Vorwärts.» (the General, the line the player has to understand, ≤ 1.2 s, 8 takes)**

- Engine: Multilingual. Language: **German (de)**. Voice: `ceo_ref_de.wav`.
- Text: `Vorwärts.` (with a full stop, never with an exclamation mark: he does
  not shout).
- Exaggeration 0.3 · CFG 0.6 · Temperature 0.6.
- Do not try to make the voice deep: the sound-designer lowers it 4 semitones
  afterwards (`GENERAL-SLOT`). Being able to understand the word is the only
  thing that matters.

**L04 — `SDLTRSIT` — «Contact!» (Legion soldier, over the radio, ≤ 0.6 s, 5 takes)**

- Engine: Multilingual, language **English (en)**, or the **Turbo** engine
  (English only). Voice: `ceo_ref_en.wav`.
- Text: `Contact!`
- Exaggeration 1.1 · CFG 0.3 · Temperature 0.9.
- Clear consonants: the radio (`LEGION-RADIO`) eats the lows and the highs.

### 4.4 Scream versus death cry

In our script **nobody dies screaming**: R08 and L09 are a breath that breaks,
G04 a long sigh that fades like a machine. With Chatterbox:

| What you are after | Text | Knobs | Expectation |
|---|---|---|---|
| Bark / alert scream | Short word with `!` | Exaggeration 1.0-1.4, CFG 0.3 | Good (HYPOTHESIS) |
| Pain (R07, L07, G03) | `Ngh!` / `Agh!` / `Hm.` | Exaggeration 1.0, CFG 0.3 | **Weak**: it may read it as a word |
| Death (R08, L09, G04) | `Hhh... ah...` / `Sani...` (R09) | Exaggeration 0.6, CFG 0.3, Temperature 1.0 | **Weak**; R09 «Sani...» should work |

For the 6 rows without words, the realistic thing is to record them yourself
(10 minutes) or keep the CC0 fallback. Try the AI if you feel like it, but do
not spend more than a short while on it.

### 4.5 Where to save and how to name

1. Each take you like: the download button of the interface's player (it goes
   to your Downloads folder).
2. Move it to the folder the sound-designer reads, **`work/audio/voice_takes/`**
   of the repo (`VOICE-SCRIPT.md` §0.5; it is in gitignore, it does not enter
   git):

   ```powershell
   New-Item -ItemType Directory -Force "C:\Users\littl\Desktop\Claude\soviet_doom\work\audio\voice_takes"
   Move-Item "C:\Users\littl\Downloads\<name-it-gave-you>.wav" "C:\Users\littl\Desktop\Claude\soviet_doom\work\audio\voice_takes\R04_SDRRISIT_ai_chatterbox_20261014_t01.wav"
   ```

3. Name: the one in `VOICE-SCRIPT.md` §0.5 for AI,
   `<row>_<lump>_ai_chatterbox_<date>.wav`, plus `_t01`, `_t02`... because
   here each take comes out in a separate file (my proposal; the
   sound-designer decides whether to accept it). Keep them **exactly as they
   come out**, without editing.
4. **Mandatory log** (`VOICE-SCRIPT.md` §0.7): one line per file in
   `work/audio/voice_takes/AI-LOG.csv`. Header and example:

   ```
   fichero;herramienta;version_o_modelo;fecha;plan;licencia_de_uso;voz;texto;ajustes
   R04_SDRRISIT_ai_chatterbox_20261014_t01.wav;Chatterbox-TTS-Server (github.com/devnen/Chatterbox-TTS-Server) + Chatterbox Multilingual (Resemble AI);<the model the interface shows>;2026-10-14;free, local;MIT, https://huggingface.co/ResembleAI/chatterbox, read 2026-10-14, "Licensed under MIT";cloned from my own voice (ceo_ref_de.wav);Feind!;de, exaggeration 1.2, cfg 0.3, temperature 0.9, seed <whichever comes out>
   ```

5. And the line in the usual chat: «Las tomas de voz son mías y las publico
   bajo CC BY-NC-SA 4.0 (D15)» (CEO's statement: "The voice takes are mine and I publish them under CC BY-NC-SA 4.0 (D15)"). Without it, none is used, neither recorded nor
   generated with your voice.

---

## 5. Sources (read on 2026-10-14)

- Chatterbox, code and README (models, languages, tips, watermark): <https://github.com/resemble-ai/chatterbox>
- Chatterbox, model card and files (MIT licence, 23 languages): <https://huggingface.co/ResembleAI/chatterbox>
- Multilingual example application (knobs and default voices): <https://github.com/resemble-ai/chatterbox/blob/master/multilingual_app.py>
- Chatterbox-TTS-Server (portable mode, menu, port 8004, `config.yaml`): <https://github.com/devnen/Chatterbox-TTS-Server>
- Chatterbox VRAM according to NVIDIA: <https://docs.nvidia.com/ace-for-games/chatterbox-tts/getting-started.html>
- Page on Pinokio: <https://beta.pinokio.co/apps/github-com-devnen-chatterbox-tts-server>
- Applio and its version 3.6.6: <https://github.com/IAHispano/Applio>, <https://github.com/IAHispano/Applio/releases>; TTS tab with Edge TTS (third-party summary): <https://deepwiki.com/IAHispano/Applio/7.4-tts-tab>
- AllTalk v2: <https://github.com/erew123/alltalk_tts/tree/alltalkbeta>
- XTTS-v2 (CPML): <https://huggingface.co/coqui/XTTS-v2>
- F5-TTS: <https://github.com/SWivid/F5-TTS>
- Kokoro (voices): <https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md>
- Piper: <https://github.com/OHF-Voice/piper1-gpl>
- GPT-SoVITS: <https://github.com/RVC-Boss/GPT-SoVITS>
- StyleTTS2: <https://github.com/yl4579/StyleTTS2>
- Bark: <https://github.com/suno-ai/bark>
- Dia: <https://github.com/nari-labs/dia>
- OpenAudio S1-mini: <https://huggingface.co/fishaudio/openaudio-s1-mini>; Fish Speech: <https://github.com/fishaudio/fish-speech>
- Pinokio: <https://github.com/pinokiocomputer/pinokio>
