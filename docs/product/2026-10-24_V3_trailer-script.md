# V3 trailer: script, cut list and how it is made (D3, D132)

Date: 2026-10-24. Owner: `art-director` with `sound-designer`. Status:
**tools ready, nothing filmed yet** (the engine runs are the PM's, D26).
The data the tools read is the single source of the cut:
`tools/trailer/shots.json` (shots and timeline) and `tools/trailer/cards.json`
(texts). This page explains it; if the two disagree, the JSON wins.

## 1. What it is

A 60 s gameplay trailer in the rhythm of a 1990s shooter trailer: the title
screen with a line of story, a montage of the three episodes cut on the
downbeats, every weapon fired, the enemies, the four bosses, the operations
map and a medal, and the logo with the download address.

**Three versions, texts burned in: EN, RU, CA** (recommended, and what
`edit.py` writes). Subtitles were considered and dropped: a subtitle track
(SRT, mov_text) is drawn by the player's video app in a system font, and
the brief wants every text in the game's own bitmap fonts
(`assets/fonts/bigfont`, `sdmenu`, `defsmallfont`, upper case and
Cyrillic). Map and episode names are read from `src/lumps/LANGUAGE`, so
they are the game's in each language. The RU and CA lines of the story
cards are drafts for review (D129: the player sees EN, RU and CA).

Output: `work/trailer/sovietdoom-trailer-{en,ru,ca}.mp4`, 1920x1080, 60 fps,
H.264 High, AAC 192 kb/s, `+faststart`; 61.7 s with the 1.5 s tail.

## 2. Music

- **0.00-5.33 s: `D_SDINTL`** (the title music: De Geyter's *Internationale*,
  Jerry Engelbach's orchestral sequence, 90 BPM), its first two bars under
  the title screen, cut with a 0.25 s fade. **Engelbach must be credited**
  (`docs/sound/MUSIC-RIGHTS.md` §4.4): the end card carries the line in the
  three languages, and the video's description should too.
- **5.33-61.7 s: `D_SDBS9A`** (Tunguska's final-boss loop, ours, 140 BPM,
  D113), from bar 1. One bar = 1.714 s = **exactly 60 tics**, so every cut in
  the timeline falls on a downbeat and every engine shot is timed in whole
  tics. Its loudness per bar (rendered 2026-10-24): flat and full from bar 1,
  a dip at bars 25-28, the peak at bars 30-32. The cut follows it: the
  bosses sit in the dip, the stats screens and the logo on the peak.
- Both rendered by `edit.py` with GZDoom's own synthesiser loaded as a
  library (`zmusic.dll` + `gzdoom.sf2`, the renderer of the listening
  sheets, `zmusic_render` in `tools/audio/gen_enemy_alts.py`): no engine, no new
  soundfont. The game's own sound (shots, enemies) goes under the music at
  -9 dB when the capture recorded it.

## 3. Cut list

Bars of `D_SDBS9A` unless marked; times from the first frame.

| Time (s) | Bars | Shot | Card | Cut |
|---|---|---|---|---|
| 0.00-5.33 | 2 (Intl.) | TITLE: `TITLEPIC`, pillarboxed 4:3, slow push-in | C_1977 | from black |
| 5.33-8.76 | 2 | S01 MAP01 Zarya-7, the hangar: **TT-33** vs three Reich riflemen | Zarya-7 Cosmodrome | flash |
| 8.76-10.48 | 1 | black | C_EMPIRES | cut |
| 10.48-13.90 | 2 | S02 MAP02 the metro hall: **IZh** vs charging Reich hounds | Metro-Bunker | flash |
| 13.90-16.48 | 1.5 | S03 MAP03 Tankograd's hall: **PPSh** vs a Panzermensch and riflemen | Tankograd | cut |
| 16.48-19.05 | 1.5 | S04 MAP03 **the General** (boss 1) wakes; two RPG-7 rounds | | cut |
| 19.05-20.76 | 1 | black | C_SERGEANT | cut |
| 20.76-24.19 | 2 | S05 MAP04 the Trans-Siberian yard: **AKM** vs the Legion | *The Road to Moscow* / Trans-Siberian | flash |
| 24.19-27.62 | 2 | S06 MAP05 the Volga dam's crest: **RPG-7** into doughboys | Volga Dam | cut |
| 27.62-30.19 | 1.5 | S07 MAP06 Red Square: walking at the Spasskaya tower | Red Square | cut |
| 30.19-32.76 | 1.5 | S08 MAP06 the GUM arcade: **ROKS-3** vs stormtroopers | | cut |
| 32.76-34.48 | 1 | black | C_EDGE | cut |
| 34.48-37.90 | 2 | S09 MAP07 the runway: **hand Katyusha** volley into Legion gunners | *The Portal* / Novaya Zemlya | flash |
| 37.90-40.48 | 1.5 | S10 MAP08 **the Chrome Marshal** turns on us | Severomorsk | cut |
| 40.48-43.05 | 1.5 | S11 MAP09 the works: **RGD-5** into riflemen (V3; the IZh on a v1.2 PK3) | | cut |
| 43.05-46.48 | 2 | S12 MAP09 the crater's rim: the portal, the Consortium below | Tunguska | cut |
| 46.48-49.90 | 2 | S13 MAP06 **the Liberty Colossus** (the statue, boss 2) on its dais | | flash |
| 49.90-53.33 | 2 | S14 MAP09 **the Consortium** (final boss), from the third terrace | | flash |
| 53.33-55.05 | 1 | S15 leaving MAP08: **the operations map** under the stats (V3 B1) | C_FEATURES (2 segments) | flash |
| 55.05-56.76 | 1 | S16 the end of Episode 3: **the awards page**, a medal (V3 B3) | | cut |
| 56.76-61.69 | 2 + 1.5 s | black: the logo `M_DOOM`, the download, the version, Engelbach's credit | E_END | flash, fade out |

## 4. The cards

| Id | EN | RU (draft) | CA (draft) |
|---|---|---|---|
| C_1977 | 1977. / THE USSR IS INVADED. | 1977 ГОД. / НА СССР НАПАЛИ. | 1977. / L'URSS ÉS INVADIDA. |
| C_EMPIRES | TWO ALIEN EMPIRES. / ONE ALLIANCE. | ДВЕ ЧУЖИЕ ИМПЕРИИ. / ОДИН СОЮЗ. | DOS IMPERIS ALIENÍGENES. / UNA ALIANÇA. |
| C_SERGEANT | ONE SERGEANT. / NO STEP BACK. | ОДИН СЕРЖАНТ. / НИ ШАГУ НАЗАД. | UN SERGENT. / NI UN PAS ENRERE. |
| C_EDGE | FROM THE ARCTIC / TO THE PORTAL. | ОТ АРКТИКИ / ДО ПОРТАЛА. | DE L'ÀRTIC / FINS AL PORTAL. |
| C_FEATURES | 9 MAPS · 3 EPISODES / {weapons} WEAPONS · 4 BOSSES | 9 КАРТ · 3 ЭПИЗОДА / {weapons} ВИДОВ ОРУЖИЯ · 4 БОССА | 9 MAPES · 3 EPISODIS / {weapons} ARMES · 4 CAPS FINALS |
| E_END | FREE DOWNLOAD / GITHUB.COM/KAHACHE/SOVIET_DOOM / {version} | СКАЧАТЬ БЕСПЛАТНО / … | DESCÀRREGA GRATUÏTA / … |
| L_MAP01…09 | the map's name from LANGUAGE (MAP04 and MAP07 with their episode's name above) | | |

`{weapons}` is 9 when S11 was filmed with the RGD-5 (a V3 PK3), else 8 (the
ice axe counted, D116). `{version}` is `video.version` in shots.json
(**v1.3, a placeholder**: V3's release name is the PM's) or `--version`.
The four bosses: the General, the Liberty Colossus, the Chrome Marshal, the
Consortium.

## 5. How the shots are filmed (`tools/trailer/capture.py`)

GZDoom records no video. Measured on the CEO's PC (2026-10-24): FFmpeg
8.1.2 is installed (`C:\ProgramData\chocolatey\bin\ffmpeg.exe`) with
`gdigrab`, `libx264` and AAC; the monitor is 1920x1080 at 100 % scaling;
the Sound Blaster offers a loopback input, "What U Hear (Sound Blaster Z
SE)". So, with nothing downloaded:

- **One GZDoom run per shot**, the player as the camera, driven by a
  console sequence the way `tools/route.py` drives its routes (route.py's
  helper ZScript is reused for `sdstop` and `sdexit`), with a throwaway
  helper PK3 in `work/trailer/helper/` that adds the camera: `sdview`
  (yaw and pitch), `sdpan`/`sdtilt` (smooth, interpolated turns over N tics),
  `sdspawn` (an enemy N units ahead, facing and hunting the player),
  `sdthurt` (a scratch that wakes a boss), and **the slate**: the whole
  screen is magenta from the level's first frame until `netevent sdroll`.
- **Pre-roll under the slate:** `god`, gifts, the weapon raised, ≥ 6 s of
  waiting (so FFmpeg is rolling), then the warp, the view, the spawns, 8
  tics, the roll. The shot's actions follow in tics. The first frame without
  the slate is the shot's time zero; `edit.py` finds it, so the engine's
  start-up time never matters.
- **Picture:** GZDoom windowed; the tool gives the window an exact 1280x720
  client area, topmost, centred, and FFmpeg films that rectangle of the
  desktop at 60 fps (`gdigrab desktop` with an offset, which reads the
  composited desktop, so the OpenGL/Vulkan window is not black). HUD off
  (`screenblocks 12`), weapon on, no crosshair, no messages, game music off.
  Its own config, `logs/gzdoom-trailer.ini` (seeded from
  `logs/gzdoom-tooling.ini`), so those cvars never reach the QA screenshots.
- **Sound:** the game's sound through the loopback device (dshow), in the
  same file; `--no-audio` films the picture only.
- Per shot: `work/trailer/shots/<ID>.mkv`, `<ID>.json` (argv, rectangle,
  timings, spawns refused, script errors), `<ID>.log`.

The camera positions were chosen from the built maps (`src/maps/*/map.py`)
and are checked without the engine by `tests/test_trailer.py`: the camera
fits where it stands, every spawned enemy lands where its body fits and in
sight, every subject is in sight and inside the 90° view, every boss is the
map's own thing at its own spot.

## 6. How it is cut (`tools/trailer/edit.py`)

Each timeline segment is rendered to an exact frame count (black, a still,
or the shot from its roll plus `from`), with a white flash or a fade where
marked; the segments are joined; the music (and the game's sound) is mixed
and peak-normalised to -1 dBFS; each locale gets its cards (full-frame PNGs
drawn from the bitmap fonts, nearest-neighbour, faded in and out over their
window) and is encoded. A shot not captured falls back to its still: the
operations map and the medal are composed from the v3 branch's own PNGs and
intermission script (`git show v3:…`, nothing checked out) when the PK3 had
no V3 intermission. `--allow-missing` puts a grey card naming any other
missing shot, for a preview of the cut (made 2026-10-24: 61.69 s, 1080p60,
H.264 + AAC, ~2.5 min to render one locale).

## 7. Commands (the PM)

```bash
# 0. (once) the shots that need V3 (RGD-5, operations map, medals) want a V3 PK3:
#    build it from the v3 branch and pass it with --pk3; without it they fall back.
# 1. film one shot first, to see the helper compile and the slate work:
SD_ALLOW_ENGINE=1 python tools/trailer/capture.py --shots S01
# 2. then all of them (~16 runs, ~6 min; hands off the mouse and keyboard):
SD_ALLOW_ENGINE=1 python tools/trailer/capture.py [--pk3 <v3 worktree>/dist/sovietdoom.pk3]
# 3. pick the intermission offsets on the contact sheets (S15, S16: NOT VERIFIED):
.venv/Scripts/python.exe tools/trailer/edit.py --contact S15
# 4. cut the three versions:
.venv/Scripts/python.exe tools/trailer/edit.py --version v1.3
```

## 8. Not verified (radical honesty)

- **Nothing has run in the engine yet.** The helper's ZScript (the camera,
  the slate's `Screen.Clear`, `Actor.Spawn` by name) was written against
  g4.14.2's own `gzdoom.pk3` declarations but never compiled; a script error
  shows in `<ID>.log` and marks the shot failed.
- Console names marked (?) in `trailer_lib.VIEW_CVARS` (`con_notifytime`,
  `use_mouse`); `use <weapon>` to select a weapon; positive pitch looking
  down; `+use` advancing the stats screen; the exact seconds at which the
  operations map and the awards page show (S15, S16 `from`).
- That `win_w`/`win_h` are resized by `SetWindowPos` without GZDoom snapping
  back (the tool retries and fails the shot if the client area is not
  1280x720), and gdigrab's offsets at this PC's 100 % scaling.
- The A/V offset between gdigrab and dshow (`edit.py --audio-offset-ms`).
- The licence of `gzdoom.sf2` for a published render (`sound-designer` to
  confirm in `docs/sound/`; the game itself plays through it on every
  player's machine).
