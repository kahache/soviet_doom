# ADR 008 — The diegetic radio swaps the level's music; it is not a positional sound

Date: 2026-10-13. Status: accepted, **not yet seen in the engine** (the PM's
batched engine pass, D26). Owner: `mod-engineer`.
Russian mirror: owed (D34), at the same path under `docs/ru/`.

Implements the radio of D43 (`docs/PRD.md`): "the diegetic radio gets
`WM_Ej_uchnem` and `WM_Kolokolchik` (CC0)". The contract rows are in
`docs/engine/MOD-SPEC.md` §6.7 (class, arguments, rules for placing it),
§6.1 (editor number 21200), §5.1 and §6.3 (sprite) and §4.5 (music lumps).

## Context

A **diegetic** sound exists inside the game world: a radio on a guard's
desk that the sergeant hears too, unlike the soundtrack. The CEO approved
two pieces for it, both Peter Gerloff's CC0 MIDI sequences from Wikimedia
Commons, already orchestrated and measured usable as they are
(`docs/sound/SOUNDTRACK.md` §3; rights `docs/sound/MUSIC-RIGHTS.md` §4.4).

Three constraints:

- **The pieces are MIDI.** GZDoom plays MIDI only as music, through its
  music player (ZMusic, FluidSynth with the bundled `gzdoom.sf2` on a stock
  install, SOUNDTRACK §1). Sound effects are decoded audio (WAV, OGG, FLAC,
  MP3, Doom's DMX format). That a MIDI lump cannot be played as a sound
  effect is our reading of the engine's design, **NOT VERIFIED** by a test
  in this project; option B below does not depend on it.
- **No downloads** in this task, and agents never start GZDoom (D26).
- **The level already has music.** MAP01 plays `D_SDM01` for its whole
  length (MOD-SPEC §4.5).

What the engine offers, read in GZDoom g4.14.2's own scripts
(`gzdoom.pk3 → zscript/`, the file each line comes from):

| Facility | Where | What it does |
|---|---|---|
| `S_ChangeMusic(String name, int order = 0, bool looping = true, bool force = false)` | `doombase.zs`, `extend class Object`, `native static` | replaces the music now playing; callable from any actor |
| `Level.Music`, `Level.musicorder` | `doombase.zs`, `struct LevelLocals`, `native readonly` | the current level's music lump and order: what to give back |
| `musplaying.name` | `engine/base.zs`, the globals struct, `native readonly @MusPlayingInfo` | the name of the song now playing |
| `MusicChanger` | `actors/shared/sectoraction.zs`; editor numbers 14101–14165 in `mapinfo/common.txt` | a sector action: entering its sector hands the player a MUSINFO entry, applied by `PlayerPawn.CheckMusicChange()` |
| `S_StartSoundAt`, `A_StartSound` with attenuation | `doombase.zs`, `actors/actor.zs` | positional sound effects |
| `transient` fields | used by `Health.PrevHealth` (`actors/inventory/health.zs`) | a member the savegame does not store; it comes back at its default after a load |

## Options

| Option | What it is | For | Against |
|---|---|---|---|
| **A. A radio that swaps the music** | an actor that calls `S_ChangeMusic` with its piece when the player comes within a reach, and gives `Level.Music` back when they leave, with a margin between the two distances | plays the MIDI as approved, at kilobyte size; no new lump type, no tool, no download; one small class; no other lump touched; the volume is the player's music volume, untouched | not positional: the music does not get louder as you approach, and it is heard through walls inside the reach; the level's music restarts from its first bar when it comes back (MIDI cannot resume); one radio at a time |
| B. A positional sound | the piece rendered to audio (WAV/OGG) and played by the actor with `A_StartSound` and distance attenuation, looping | truly in the room: fades with distance, can sit under the level's music | **needs audio we do not have**: `tools/audio/audition.py --render` renders through GZDoom (`writewave`), which only the PM may run (D26), and that renders with the bundled `gzdoom.sf2` soundfont, whose samples would then be **baked into a file we redistribute**, a licence question nobody has asked yet (MIDI ships no samples, which is why D16 chose it); a WAV of 50 s is megabytes where the MIDI is 2 KB, and an OGG needs an encoder this machine has not been shown to have; and the level's music would still play on top of it, so B **also** needs a music swap or a duck to not sound like two radios at once |
| C. The engine's `MusicChanger` and a `MUSINFO` lump | place a changer thing (14101+) in the radio's sector and changers set to the default music in every sector around it; `MUSINFO` maps `MAP01` + number to `D_SDRAD2` | zero ZScript; the engine saves and restores it | sector-shaped, not distance-shaped: every neighbouring sector needs its own "back to default" changer, which is `level-designer` work per map and breaks silently when a sector is split; a new lump (`MUSINFO`) outside this task's files; the radio is not an object, it has no picture and cannot be drawn by `art-director` |
| D. ACS `SetMusic` from sector triggers | scripts on lines around the room | the classic way | needs an ACS compiler and a `BEHAVIOR` lump the project does not have; same shape problem as C |

## Decision

**A**, with the PM's three conditions met:

- **D-008-1. One class, `SD_Radio`** (`zscript/sd/radio.zs`), editor number
  **21200**, the first of the decoration sub-range (21200–21299, ADR 002).
  `arg0` chooses the piece (1 = `D_SDRAD1` «Эй, ухнем», 2 = `D_SDRAD2`
  «Колокольчик», anything else = 1), `arg1` the reach in map units
  (0 = 128).
- **D-008-2. Hysteresis.** It turns on at the reach and off at the reach
  plus 64 units (one grid cell): a player standing on the edge, or strafing
  along it, does not make the music flicker between two songs.
- **D-008-3. The player's music volume is respected.** The radio calls
  `S_ChangeMusic` and nothing else: it never writes `snd_musicvolume` and
  never calls `SetMusicVolume`. With music turned off, the radio is silent.
- **D-008-4. It hands back only what it took.** On leaving, it restores
  `Level.Music` at `Level.musicorder` only if `musplaying.name` is still its
  own piece; if something else changed the music meanwhile (another radio,
  a future `MusicChanger` or script), it leaves that alone. `Level.Music`
  is the level's music as the engine knows it, so a map with
  `music = ""` (MAP02) gets silence back.
- **D-008-5. Saved games.** `playing` (this radio has the music) is an
  ordinary field and is saved with the actor. `synced` is `transient`: it
  is false on the first tic of the map and again on the first tic after a
  load, and on that tic a radio that was playing calls `S_ChangeMusic` with
  its piece again. `S_ChangeMusic` without `force` does nothing when that
  song is already playing, so this is harmless if the engine restores the
  song itself. Whether it does is **NOT VERIFIED**; the radio works either
  way.
- **D-008-6. Placeholder sprite `PMAP` A**, Freedoom's computer area map:
  a 32×28 box with a lit green face, the only object among Freedoom's 140
  sprite prefixes shaped like a set on a desk (the decorations are lamps,
  columns, trees, torches and gore, rendered and compared on 2026-10-13).
  Held still on frame A. It **is** a pickup's picture, and MAP01 places
  that pickup: debt T23 until `art-director` draws `SDRD` A.
- **D-008-7. No sound effect, no text.** `SNDINFO` and `LANGUAGE` are not
  touched: switching on is the music changing, and the radio prints
  nothing. A click on switching on would need a sound lump and a
  `SNDINFO` line; `tests/test_bestiary.py` pins `SNDINFO`'s bestiary
  section, not the whole file, so it can be added later without a fight.

## Consequences

- MAP01 can have a radio as soon as the PM adds `21200 = SD_Radio` to
  `MAPINFO`'s `DoomEdNums` and `level-designer` places the thing. Until
  then the class is packed and unused.
- **The level's music restarts.** Every walk out of the reach starts
  `D_SDM01` from bar one, and every walk in starts the radio piece from
  bar one. The rule for placing it (MOD-SPEC §6.7) keeps radios out of
  rooms the player crosses repeatedly.
- **Not positional.** Inside the reach the piece plays at full music
  volume through walls. If the CEO wants a radio that fades with distance,
  that is option B and its licence question about the rendered soundfont;
  this ADR does not close that door, it declines to open it now.
- The pieces ship: `assets/music/D_SDRAD1.mid` and `D_SDRAD2.mid`,
  byte-identical to the candidates `WM_Ej_uchnem.mid` (`D_CND09`) and
  `WM_Kolokolchik.mid` (`D_CND12`). CC0, no obligation; Peter Gerloff is
  credited as a courtesy (`docs/sound/MUSIC-RIGHTS.md` §4.5).
- Single-player only: the listener is `players[consoleplayer]`.
- `tests/test_radio.py` pins what can be pinned without the engine: the
  include, the class and its constants, every piece lump packed, the
  sprite in the IWAD and declared, the editor number free and in range.

## Engine checklist (the PM, D26)

Run after `21200 = SD_Radio` is in `MAPINFO` and a radio is placed (or on a
throwaway map, as the T16 switch check was done):

1. **R1. It loads.** Zero `Script error` lines; the radio's `PMAP` A is
   drawn where it was placed, standing on the floor.
2. **R2. It turns on.** Walk within the reach: `currentmusic` reports
   `D_SDRAD1` (or `D_SDRAD2` with `arg0 = 2`), with a non-zero
   `snd_musicvolume` (SOUNDTRACK §2.1: `currentmusic` lies at volume 0).
3. **R3. It turns off.** Walk past reach + 64: `currentmusic` reports the
   level's music (`D_SDM01` on MAP01).
4. **R4. No flicker.** Stand between the reach and reach + 64 coming from
   inside, then from outside: the music does not change.
5. **R5. Save and load.** Save inside the reach, load: the radio piece
   plays. Save outside, load: the level's music plays. Load the inside save
   and walk out: the level's music comes back.
6. **R6. Silence is respected.** With `snd_musicvolume 0`, walking in and
   out changes nothing audible and writes nothing to the log.
