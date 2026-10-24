# Study: Soviet Doom on Android with on-screen controls (V3, 2026-10-24)

Dated snapshot. Author: `mod-engineer`, at the CEO's request ("an Android
version with on-screen controls"). Research only: **nothing was downloaded,
installed, built or run**; sources are web pages and public repositories read
through the GitHub API. Everything not confirmed in a cited source is marked
**NOT VERIFIED**. Estimates are k tokens of team work (D69, ±50 %). Nothing
here is decided: the CEO chooses.

What we ship today (measured on `dist/sovietdoom.pk3`, 2026-10-24): one PK3 of
**9.2 MB**, 1 824 entries, `version "4.12"` ZScript, tested on GZDoom
**g4.14.2** with `freedoom2.wad` 0.13.0 (28.8 MB). The engine's own files on
Windows are ~28 MB (`gzdoom.exe` 11.4 MB, `gzdoom.pk3` 3.1 MB,
`game_widescreen_gfx.pk3` 5.6 MB, `game_support.pk3` 2.4 MB, DLLs, a 3 MB
soundfont). The mod has **no GLDEFS and no dynamic lights of its own**; its
largest images are the seven 1024×128 skies, then sprites of at most 232×144
(the Gemini art was reduced to Doom scale); the ten maps are small (at most
~1 050 linedefs and ~265 things each, nodes built at load).

## 0. Context that changes the picture

- **GZDoom has not released since g4.14.2** (2025-05-03, [ZDoom/gzdoom releases](https://github.com/ZDoom/gzdoom/releases)).
  Most of its developers forked it as **UZDoom** in October 2025; UZDoom
  4.14.3 (Nov 2025) is "a direct follow-up to GZDoom 4.14.2", and **UZDoom
  5.0 shipped on 2026-08-31** (5.0.3 on 2026-09-23)
  ([GamingOnLinux, Nov 2025](https://www.gamingonlinux.com/2025/11/gzdoom-successor-project-uzdoom-gets-a-first-preview-release/),
  [GamingOnLinux, Aug 2026](https://www.gamingonlinux.com/2026/08/gzdoom-successor-uzdoom-5-0-is-officially-out-now/),
  [UZDoom releases](https://github.com/UZDoom/UZDoom/releases)). Neither project
  publishes an Android build.
- **Every live Android GZDoom comes from one person: Emile Belanger**
  (Beloko Games / Open Touch Gaming, GitHub `emileb`). His fork
  [emileb/gzdoom](https://github.com/emileb/gzdoom) (GPL-3.0, a fork of
  ZDoom/gzdoom) has a branch per engine version, among them
  **`mobile_g4.14.2`**: 15 commits on top of the `g4.14.2` tag, last commit
  2026-09-02 ("Added vulkan mailbox…"), 112 files touched: ndk-build makefiles
  under `mobile/`, GLES and Vulkan fixes for phones, Android paths
  (compare `g4.14.2...emileb:mobile_g4.14.2`, read via the GitHub API). Also
  `uz_5.0`, `uz_5.0_pre`, `uz_mobile_4.15.x`. The touch layer and the app shell
  are separate repositories (§1b).
- **Upstream g4.14.2 already contains a GLES renderer**
  (`src/common/rendering/gles/`; the mobile branch modifies files that exist
  there). VERIFIED as code, not run.

## 1. The routes

### Summary

| Route | Runs our PK3 as is? | Touch controls | Licence / can we redistribute | Effort (k) | Main risk |
|---|---|---|---|---|---|
| **A. Delta Touch** ($2.99 app) + our PK3 as a mod | Very likely: it offers a **GZDoom 4.14.2** build (third-party guide) and UZDoom 5.0.1 — NOT VERIFIED with our PK3 | Yes, mature, customisable, gyro, 18 custom buttons | We ship only our PK3 + a guide; Delta Touch itself is paid and its shell is not open (icons and touch graphics © Open Touch Gaming) | **~90** | Every player pays $2.99 and copies files by hand; we depend on one app |
| **B1. Our own APK, forked from an open Android shell** ([manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026)) with emileb's `mobile_g4.14.2` engine | Yes if we build that branch (same engine as desktop); NOT VERIFIED | Yes: emileb's MobileTouchControls (same as Delta Touch) | Engine GPL-3.0 fine; **the touch and glue libraries carry GPLv2-only or no licence** (§1b) — needs Emile Belanger's written clarification | **~350** (+60 for Play) | Licence of the touch layer; one-person upstreams; build debugging on Windows |
| **B2. Our own APK with our own touch layer** (emileb's engine + SDL2 + overlay we write) | Yes, same engine | Ours, to be written (stick, look-drag, buttons) | Clean: all GPL-3.0 / zlib / LGPL, ours | **~700** | Large; the engine branch still compiles Open Touch glue files that we would have to replace |
| **C1. Web (WASM) build in the phone's browser** | No: only experimental ports (UZDoom 4.14.3, patches not published) | None | GPL-3.0, but nothing reusable is published | **≥ 800**, exploratory | Immature; no touch layer; performance unknown |
| **C2. Another engine with ZScript on Android** | No | — | — | — | None exists: ZScript is GZDoom-lineage only; LZDoom/QuestZDoom are older or VR-only |

### 1a. Delta Touch (Open Touch Gaming)

**What it is** (Google Play listing, read 2026-10-24,
[com.opentouchgaming.deltatouch](https://play.google.com/store/apps/details?id=com.opentouchgaming.deltatouch&hl=en_US&gl=US)):
"Delta Touch [10 x Doom engine]" by Open Touch Gaming, **$2.99**, 50K+
downloads, 4.8 stars, **updated 2026-09-16**. Engines listed: "GZDoom (v1.9.1 &
v3.25 & v3.82 & v4.x)", "UZDoom (dev)", LZDoom, Zandronum 3.2 alpha, Chocolate,
PrBoom+, Crispy, Doom Retro, DSDA, Doom64EX+, Dhewm3. The latest "What's new"
says "UPT: UZDoom v5.0.1", "GZ/UZ: Auto fix OpenGL shaders", "GZ/UZ: Optimised
Vulkan for mobile". Features: "Highly customizable touch screen controls",
"18 custom buttons for GZDoom for mods", gamepad, mouse and keyboard
(Android 8+), gyro aim assist, saved touch layouts, built-in keyboard for the
console, a "Custom UI to easily select your wads and mods", "FreeDoom data
included", ~60 MB extra download for music libraries and Freedoom. Full refund
on request. Legal line: "Icons and internal touch screen graphics are
copyright to Open Touch Gaming… This is a GPL source port". Package namespace
`com.opentouchgaming` is the same as emileb's AndroidCore library, so the
GZDoom inside is emileb's fork.

**Which GZDoom.** A user guide for another GZDoom game on Delta Touch says to
press the version button "until the GZDoom version equals 4.14.2"
([teletype guide](https://teletype.in/@easyapk_telegram/sharpshooter3d-android-guide), dated
"May 19", year not shown). Together with the `mobile_g4.14.2` branch (§0),
**4.14.2 is very likely selectable**; NOT VERIFIED on a phone. Older reports
mention a 4.10 dev build ([itch.io comment](https://itch.io/post/8911704)).

**Loading an external PK3.** Yes. The same guide: set a secondary storage
folder `OpenTouch/Delta`, put the files in `OpenTouch/Delta/mods`, select the
IWAD, tap **MOD**, tick the files, launch. Delta Touch adds `-file` before each
mod path; response files work for long lists
([Steam thread](https://steamcommunity.com/app/2300/discussions/0/3095635055516492759),
[GBAtemp](https://gbatemp.net/goto/post?id=9738651)). Exact folder names on
the current version NOT VERIFIED.

**Can our game be packaged as a "mod" for it?** There is no published package
format or launch intent that would make Soviet Doom appear as its own entry;
nothing found. What we can ship: `sovietdoom-<v>-android.zip` with
`sovietdoom.pk3`, `freedoom2.wad` 0.13.0 (BSD, so the player does not depend on
whichever Freedoom Delta Touch bundles; its version NOT VERIFIED), an optional
mobile overlay PK3 (§3), the licences, and `README-ANDROID.txt` in EN/RU/CA
(D129) with the steps and screenshots. We cannot bundle Delta Touch itself.

- **ZScript 4.14:** yes if the player picks the 4.14.2 build; under UZDoom
  5.0.1 probably (we pin `version "4.12"`), NOT VERIFIED.
- **Touch:** the best available today (stick, look, fire, use, weapon wheel,
  automap, menu, custom buttons).
- **Licence:** we distribute only our own files, exactly as today. NC is not
  affected (we charge nothing; the $2.99 is Open Touch Gaming's sale of its
  app).
- **Effort:** ~90 k: mobile overlay and strings (§3) 40, Android zip in the
  release tooling with tests 25, README-ANDROID EN/RU/CA 10, the PM's
  on-device session and its evidence 15.
- **Risks:** a paid dependency for every player; file copying through
  Android's storage pickers is the hardest step for non-technical friends;
  Delta Touch may change folders or drop the 4.14.2 build; we cannot control
  default bindings or the touch layout (we can only document them).

### 1b. Building our own APK

**Open-source Android GZDoom ports found** (GitHub API, 2026-10-24):

| Repository | State | Engine | Touch | Licence |
|---|---|---|---|---|
| [emileb/gzdoom](https://github.com/emileb/gzdoom) | Active (push 2026-09-03) | branch per version: **`mobile_g4.14.2`**, `uz_5.0` | none in the engine; compiles `Clibs_OpenTouch/idtech1/touch_interface.cpp` and `gzdoom_game_interface.cpp` (its `mobile/Android_src.mk`) | GPL-3.0 |
| [emileb/MobileTouchControls](https://github.com/emileb/MobileTouchControls) | Active (2026-10-23) | — | the on-screen controls library (joystick, buttons, grids, GL drawing) | `License.txt`: "**under GPLv2 license.** Please contact me if you wish to use a different license." No "or later"; source headers carry no notice |
| emileb/[Clibs_OpenTouch](https://github.com/emileb/Clibs_OpenTouch), [AndroidCore_OpenTouch](https://github.com/emileb/AndroidCore_OpenTouch), [SDL2_OpenTouch](https://github.com/emileb/SDL2_OpenTouch), [AudioLibs_OpenTouch](https://github.com/emileb/AudioLibs_OpenTouch), [SAFFAL](https://github.com/emileb/SAFFAL) | Active | glue, launcher library (Java/Kotlin, minSdk 19, targetSdk 35), SDL, audio | the GZDoom touch mapping lives in Clibs | **no licence file** (GitHub reports none) |
| [emileb/Zeta_Touch](https://github.com/emileb/Zeta_Touch), Sigma_Touch, Psi_Touch | Active | Raze, others | the same libraries as submodules | no licence; Delta Touch's own shell is not published |
| [manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026) | One developer, last push 2026-06-30, no releases | emileb `uz_5.0_pre` (UZDoom 5.0.0-pre); earlier `mobile_4.15.x` | MobileTouchControls + Clibs vendored; Compose touch settings | LICENSE file GPL-2.0 (while vendoring GPL-3.0 code) |
| [dports/GZDA](https://github.com/dports/GZDA), GZDA2 | **Discontinued** (2024) | old D-Touch fork | yes | GPL-3.0 |
| [andrewrabert/GZDoom-Android](https://github.com/andrewrabert/GZDoom-Android), [Freedoom-for-Android](https://github.com/mkrupczak3/Freedoom-for-Android), F-Droid [net.nullsum.freedoom](https://f-droid.org/de/packages/net.nullsum.freedoom/) | Discontinued | GZDoom ~2.1 (no ZScript) | basic | GPL |
| [DrBeef/QuestZDoom](https://github.com/DrBeef/QuestZDoom) | Active (OpenXR, 2026-08) | LZDoom/GZDoom base | **VR headsets only**, no touch | GPL-3.0 |

**manuelsiuro/GZDoom-Android-2026** is the most useful starting point. Its
README says: Kotlin + Jetpack Compose launcher; compileSdk 36, minSdk 23;
arm64-v8a and armeabi-v7a; 16 KB page alignment (Android 15+); FMOD removed
(OpenAL + FluidSynth); NDK r27, JDK 17; native build `build_native.sh`
(ndk-build), then `./gradlew :doom:assembleDebug`; prebuilt `.so` committed;
"rendering verified on a real device (Galaxy S24…), 3D world + HUD + weapon
sprites + touch controls"; the Android emulator shows a black game view (so a
real phone is required); a release signing config is still "planned". It also
carries an idgames browser, a map editor and a WAD downloader we would remove.

**What B1 would be:** fork it outside our repo (a new repo, e.g.
`kahache/soviet_doom_android`, GPL-3.0); swap the engine to emileb's
`mobile_g4.14.2` (our pinned engine, D3); strip the launcher to one screen
(Play / Options / Licences) or none, and start the engine directly with
`-iwad freedoom2.wad -file sovietdoom.pk3` from the APK's assets; default
touch layout and binds for our actions; our icon and name; signed release APK
and AAB; the GPL source offer (engine branch commit, the app repo, the source
tarballs on the release, as we do for v1.0, RELEASE §4.4).

**What it needs** (sizes approximate, NOT VERIFIED): JDK 17 (~190 MB); Android
SDK command-line tools + platform-tools (`adb`) + platform 36 + build-tools
(~0.4 GB); **NDK r27** (~0.7–1 GB download, ~2–3 GB on disk); Gradle and its
dependency cache (~0.5–1 GB); the two source trees (emileb/gzdoom is ~220 MB as
a git repo, GZDoom-Android-2026 ~230 MB). Android Studio (~1.2 GB) optional.
**Total ~3–5 GB of downloads, ~8–10 GB of disk.** CMake is not needed (the
mobile build uses ndk-build `Android.mk`). First native build of GZDoom for two
ABIs: estimated 20–60 min on this PC, incremental builds minutes (NOT
VERIFIED). Signing: a keystore made with the JDK's `keytool`, kept by the CEO
outside the repo with a backup (losing it means no updates under the same app
id); on Play, Play App Signing.

**APK size estimate (NOT VERIFIED):** engine `.so` per ABI ~15–25 MB, engine
pk3s ~11 MB, `freedoom2.wad` 28.8 MB, our PK3 9.2 MB, soundfont 3 MB, SDL /
OpenAL / ZMusic / FluidSynth ~5–10 MB: **~55–75 MB for arm64 only**, ~+20 MB
with armeabi-v7a. Under Play's limits.

- **ZScript 4.14:** yes, it is the same engine version as the desktop build.
- **Touch:** emileb's library, the same as Delta Touch, so the same quality.
- **Licence, the blocker:** GZDoom (GPL-3.0) and MobileTouchControls
  ("GPLv2", no "or later" stated) would be linked into one `libgzdoom`-side
  binary; GPLv2-only and GPLv3 code cannot be combined
  ([FSF licence list](https://www.gnu.org/licenses/license-list.html#GPLv2)).
  The glue (Clibs, AndroidCore, SDL2_OpenTouch) has no licence at all, which
  by default reserves all rights. Delta Touch ships them together, so the
  author very likely intends a compatible licence, but **we must not assume
  it**: the CEO (or the PM with his OK) would write to Emile Belanger asking
  for "GPL-2.0-or-later or GPL-3.0" on those repositories. If he says no, B1
  becomes B2.
- **Effort B1:** ~350 k: SDK/NDK setup and first build 50, engine swap and
  native build fixes 80, strip and brand the launcher, autostart, assets 80,
  default touch layout and binds 40, signing, `tools/release_android.py`,
  GPL sources and tests 70, docs EN (RU at phase close) 30. Play listing on top
  (~60 k, §2).
- **Risks:** licence (above); one-person upstreams (emileb, manuelsiuro);
  Windows build quirks (the fork documents macOS NDK paths); 16 KB pages and
  target-SDK rules move every year; the emulator cannot show the game, so all
  testing needs the CEO's phone and his time.

**B2 (own touch layer):** the same engine, but our own overlay: an Android
`View` above SDL's surface drawing a left stick, a right-half look area and
buttons, sending SDL key and relative-mouse events, so the engine sees a
keyboard and mouse and needs no Open Touch glue. Clean licence (all ours,
GPL-3.0; SDL zlib; OpenAL/FluidSynth LGPL). But `mobile/Android_src.mk`
compiles the Open Touch glue (`gzdoom_game_interface.cpp`, `android_jni.cpp`),
so we would also replace that entry point. ~700 k, and every control detail
(dead zones, sensitivity, multi-touch, layout editor) is ours to get right.

### 1c. Other routes

- **Web/WASM.** Found only experiments: [blahm1dplays/uzdoom-wasm](https://github.com/blahm1dplays/uzdoom-wasm)
  (UZDoom 4.14.3 → WebGL2 in a worker, plays FreeDM MAP01, a live demo; its
  patch series is "intentionally not in this repo"; licence unstated) and
  scaffolds like [HyperCrab2000/doom](https://github.com/HyperCrab2000/doom).
  No touch input, no mobile testing, depends on JSPI support in the phone's
  browser (NOT VERIFIED). Interesting for a "play in the browser" page some
  day; not a route to an Android game now.
- **Another engine with ZScript.** None: ZScript exists only in the GZDoom
  lineage (GZDoom, UZDoom, VKDoom on desktop). LZDoom (QuestZDoom's base,
  3.8x) and Zandronum 3.2 are older engines and would reject `version "4.12"`
  (NOT VERIFIED for Zandronum's ZScript level).
- **A gamepad instead of touch:** both A and B support Bluetooth gamepads; a
  cheap way to make playtests comfortable, not a substitute for touch.

## 2. Recommendation and MVP

**Two steps, the first nearly free.**

1. **Now: route A as the MVP (~90 k).** The CEO buys Delta Touch on his phone,
   we give him `sovietdoom-<v>-android.zip`, and in one session we confirm the
   three things every route depends on: the PK3 loads on emileb's 4.14.2 build
   with a clean console, the frame rate is playable through MAP06 and MAP09
   (the heaviest maps), and what in our HUD, menus and texts breaks on a
   phone (§3). Everything fixed here carries over to B1, which runs the same
   engine fork. The friends get a working path at $2.99.
2. **Then, if the CEO wants a free standalone app or a Play listing: route
   B1 (~350 k, + ~60 k for Play)**, started only after Emile Belanger's answer
   on the licence; if he declines, B2 (~700 k) or stay on A.

**The MVP, "playable on a phone" means:** the game starts from one tap (A:
from Delta Touch's list with our PK3 ticked; B1: our icon); landscape,
fullscreen; **left stick** to move and strafe, **drag on the right half** to
look and turn, **Fire**, **Use** (also continues after death), **next/previous
weapon** plus the weapon wheel, **Automap**, **Menu** (Esc) with touch
navigation, always-run on; save and load from the menu, the autosave on map
entry kept; the three languages; music audible. Jump and a quick-save button
are nice to have. Gate: the PM plays MAP01 to the exit on the phone on skill 3
with no cheats, plus the practice range, and records the console log and
screenshots as evidence (D26 still applies: agents do not run the engine; on
the phone it is the CEO's hands).

**What the team needs from the CEO:**

| For | What | Cost |
|---|---|---|
| A and B | **The test phone: a Samsung Galaxy M55** (CEO, 2026-10-24; specs in §4). Still needed from him: its RAM (8 or 12 GB) and the Android / One UI version it runs now (Settings → About phone → Software information). A second, weaker phone would help but is not required | — |
| A | **Buy Delta Touch** on his Google account (his purchase, refundable per the listing) | $2.99 |
| A | Copy one zip to the phone (USB or a link) and follow our guide once, with us | his time, ~30 min |
| B1 | **Written licence clarification from Emile Belanger** (a message the CEO sends or authorises) | — |
| B1 | **OK to download and install** JDK 17, the Android SDK tools, NDK r27, Gradle dependencies and the two source trees (§1b: ~3–5 GB down, ~8–10 GB disk) | disk space |
| B1 | On the phone: Developer options and USB debugging on, a USB cable, so `adb install` works (his settings change) | — |
| B1, on Play | **A Google Play developer account**: $25 once ([Android developer verification page](https://support.google.com/android-developer-console/answer/16561738?hl=en); Play's own fee page not read), identity verification, and, for a personal account created after 2023-11-13, **a closed test with ≥ 12 testers opted in for 14 consecutive days** before production ([Play Console help](https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB)); a privacy-policy page; the content-rating questionnaire | $25 + 2 weeks + 12 friends |
| B1, off Play | **APK on GitHub Releases** (our channel already) and/or **itch.io** (free). From 2027 Google extends **developer verification to every app installed on certified devices**, including sideloaded ones; it starts 2026-09-30 only in a few countries (Indonesia, Singapore, Thailand per Google's page; reports also name Brazil). A free "limited distribution" account (no fee, no ID, **up to 20 devices**) covers friends; wider distribution needs the $25 verified account even outside Play; users can still install unverified apps through ADB or an "advanced flow" (same Google page) | $0–25 |

**Does CC BY-NC-SA allow Google Play?** Very likely yes if the app is **free,
with no ads, no in-app purchases and no paid tier**: the non-commercial clause
binds what we do with the assets, and a free listing is not "primarily
intended for commercial advantage" (CC BY-NC-SA 4.0 §1(i)). That Google's own
commercial store distributes it does not, on the usual reading, make our use
commercial. **NOT VERIFIED by a lawyer.** GPL-3.0 on Play is fine (we offer
the source, as on GitHub).

**Separate Play risk: the swastika armbands (D105).** Play's declaration
guidance asks developers to flag Nazi-era symbols, and Play has blocked a
historical WWII game in Germany, Austria, France and Russia over them
([Google Play help](https://support.google.com/googleplay/android-developer/answer/7022576?hl=en),
[Gameluster on Attentat 1942](https://gameluster.com/google-play-blocks-anti-nazi-game-over-nazi-references/)).
Russia is one of our three languages. Expect at least country blocks or a
review fight on Play; GitHub/itch.io do not have that review. NOT VERIFIED for
our case.

## 3. What the mod must adapt

The rule we keep: **one `sovietdoom.pk3` for every platform.** Mobile-only
differences go in a small **mobile overlay PK3** (`sovietdoom-mobile.pk3`,
loaded after the main one with `-file`, the same mechanism as the draft
overlays, MOD-SPEC §6.9) or in the APK's command line, never in a fork of the
mod.

- **Rendering and performance.** Less risk than feared. The mod adds no
  GLDEFS and no dynamic lights; the Gemini textures and sprites are already at
  Doom scale (largest 1024×128 skies, sprites ≤ 232×144, 1 542 PNGs, 5.7 MB of
  sprites), so texture memory is small; maps are light. What to watch: the
  engine's `lights.pk3`/`brightmaps.pk3` if the build autoloads them; post-
  processing (bloom, tonemap, SSAO) off; the renderer choice (GLES vs Vulkan,
  emileb's branch has both); render-resolution scaling on high-DPI screens.
  These are engine settings: in A the player sets them in Delta Touch (we
  document defaults); in B1 the APK passes them as `+set` arguments at launch,
  which keeps ADR 004 (the mod writes no CVar) intact. To measure on the
  phone: fps in MAP06 and MAP09 with `stat fps` (NOT VERIFIED that it is the
  right command on that build).
- **Music.** All our music is MIDI. On a phone there is no Windows MIDI
  synth: the engine uses FluidSynth with a soundfont (Delta Touch downloads
  one; B1 must bundle `gzdoom.sf2`, ~3 MB, or use the OPL emulation in
  `fm_banks/`). The pieces will sound different from what the CEO approved;
  `sound-designer` listens on the phone and picks the device and soundfont
  (NOT VERIFIED which device the CEO approved with on Windows).
- **HUD on a small screen.** `SD_StatusBar` draws Doom's bar A scaled to the
  width; on a 20:9 phone the touch stick and buttons sit over its corners
  (ammo, face, arms). Options to test: the layout leaves the bar clear;
  `screenblocks 11` (fullscreen HUD) from the APK's command line; `hud_scale`.
  Whether the fullscreen HUD shows our digits and face correctly is NOT
  VERIFIED. The death prompt and pause sign (RenderOverlay, BigFont) must stay
  above the touch buttons.
- **Menus.** The main and skill menus in `SDMENU` are large enough; the
  option menus (Options → Soviet Doom → Language, Credits) use the small font
  and may be hard to tap. Whether GZDoom 4.14.2's menus accept taps as mouse
  clicks on these builds is NOT VERIFIED; Delta Touch offers a menu
  navigation mode. Measure on the phone before changing anything.
- **Texts that name keys.** `SD_DEATH_PROMPT` ("Press %s to continue") names
  the first key bound to `+use`; with touch the player presses a button, not
  "E", and Delta Touch's Use button may not be a key at all (NOT VERIFIED).
  Our help screen (F1, `SD_HelpMenu`) and the README list keyboard controls.
  The mobile overlay gives these ids touch wording ("Tap USE to continue",
  a touch help page) in `[enu default]`, `[ru]` and `[ca]` in the same task
  (D7, P6). That a later PK3's LANGUAGE id overrides an earlier one is the
  documented way mods replace engine strings, NOT VERIFIED for our ids in
  g4.14.2.
- **Saving.** Saves work as on desktop (menu save/load, map-entry
  autosave). Phone specifics: Android may kill the game in the background, so
  a quick-save button in the layout matters; in A the saves live in Delta
  Touch's folders per engine build, and switching the build (4.14.2 ↔ UZDoom)
  may make them unloadable; in B1 they sit in app-specific storage and are
  **deleted on uninstall** (document it; offer export later). Saves between
  our own mod versions stay as fragile as on desktop.
- **Language.** The mod's own switch (Options → Soviet Doom → Language)
  works the same; whether `language auto` follows the phone's locale on these
  builds is NOT VERIFIED.
- **Release tooling.** A: `tools/release.py` (or a new
  `tools/release_android.py`) makes `sovietdoom-<v>-android.zip` with the
  PK3, the overlay, `freedoom2.wad`, licences, `README-ANDROID.txt` EN/RU/CA,
  `SHA256SUMS`, with tests like the portable packages'. B1: the APK is built
  in its own repo; our release pins its version and attaches its GPL sources.

## 4. The CEO's test phone: Samsung Galaxy M55

From [GSMArena](https://m.gsmarena.com/samsung_galaxy_m55-12896.php) (not
from Samsung): released 2024-03-28; **Qualcomm Snapdragon 7 Gen 1**
(SM7450-AB, 4 nm; 1× 2.4 GHz + 3× 2.36 GHz Cortex-A710, 4× 1.8 GHz
Cortex-A510); GPU **Adreno 644**; 8 or 12 GB RAM; 6.7" 1080×2400 (20:9)
120 Hz AMOLED; launched with Android 14 / One UI 6.1, listed as upgradable to
Android 16 / One UI 8.5. The Adreno 644 supports **OpenGL ES 3.2 and Vulkan
1.1** ([Notebookcheck](https://www.notebookcheck.net/Adreno-644-vs-Adreno-618-vs-Adreno-660_11580_9900_10603.247598.0.html), third-party). Not to be confused with the M55s, a
separate model with the same chip.

What it means for us:

- **It is an upper mid-range phone (64-bit, arm64-v8a)**, well above what
  our light maps and Doom-scale art need; Delta Touch's "high-end device"
  warning is about mods like Brutal Doom. Expect it to run Soviet Doom at a
  playable rate on the GLES renderer (NOT VERIFIED until measured).
- **Renderer: start with OpenGL ES, not Vulkan.** GZDoom's Vulkan backend on
  a Vulkan 1.1 mobile driver is the riskier path: emileb's `mobile_g4.14.2`
  branch has commits "Relax Vulkan requirments" and "Added Vulkan hardware
  buffer…, much faster on mobile now" (2026-08-31), and Delta Touch's latest
  notes say "GZ/UZ: Auto fix OpenGL shaders", which suggests driver-specific
  shader trouble on some GPUs. **No report specific to GZDoom on Adreno 644 or
  on Samsung was found** (searched; only unrelated Adreno-Vulkan bugs in other
  engines). The one public "verified on a real device" claim of the open fork
  is a Galaxy S24 with an **Exynos/Xclipse** GPU, not Adreno, so the M55 would
  be the first Adreno test for B1.
- **20:9 screen:** the classic 4:3 status bar and touch buttons will compete
  for the bottom corners (§3, HUD).
- **Samsung "Auto Blocker"** (One UI 6+) can block installs from outside the
  Play/Galaxy stores and commands over USB. Samsung says it is **off by
  default** ([Samsung editorial](https://news.samsung.com/us/setting-boundaries-without-building-walls-choice-means-stronger-security-dr-seungwon-shin-samsung/),
  [9to5Google](https://9to5google.com/?p=593360)); if the CEO has it on, route
  B1's `adb install` and any APK from GitHub/itch.io need it off (his setting).
  Whether One UI 8.x changed the default is NOT VERIFIED. Route A is a normal
  Play purchase and is not affected.

## 5. "I had Doom on Android once, so it exists and it is open source"

The CEO is right that Doom on Android exists, but **not every app was open
source, and only one live app runs GZDoom 4.x with ZScript.** The candidates,
most likely first:

| App | Who / when | Open source? | GZDoom 4.x + ZScript? | Fits us? |
|---|---|---|---|---|
| **Doom Touch → D-Touch → Delta Touch** (Play, paid, $2.99 today) | Emile Belanger, Beloko Games / Open Touch Gaming; first release 0.9 in Jan 2018, renamed over time ([DoomWiki snippet](https://doomwiki.org/wiki/Delta_Touch)) | **Partly.** The engines are GPL forks on GitHub (`emileb/gzdoom` GPL-3.0); the touch library says GPLv2; the app shell and glue are published but **carry no licence**, Delta Touch's own launcher is not published, and its icons and touch graphics are © Open Touch Gaming (§1a, §1b) | **Yes**: GZDoom 4.x builds (4.14.2 very likely) and UZDoom 5.0.1 | **Route A** |
| **DOOM / DOOM II** by Bethesda (Play, 2019) | Nerve Software / id Software, the "Unity port", launched 2019-07-26; custom add-ons on Android ([DoomWiki](https://doomwiki.org/wiki/Unity_port)) | **No**, proprietary | **No** (its own engine; WAD add-ons, no ZScript) | No |
| **Freedoom for Android** (F-Droid `net.nullsum.freedoom`, last 0.4.3, 2024-05-14) | nvllsvm → mkrupczak3 → emileb's fork as source ([F-Droid](https://f-droid.org/de/packages/net.nullsum.freedoom/), [emileb fork](https://github.com/emileb/Freedoom-for-Android)) | **Yes**, GPL-2.0-only per F-Droid | **No**: GZDoom ~2.1 era ([DoomWiki](https://doomwiki.org/wiki/Freedoom_For_Android)), before ZScript; touch controls from an early MobileTouchControls fork whose repo is gone | No (engine too old); its 2026 successor is [manuelsiuro/GZDoom-Android-2026](https://github.com/manuelsiuro/GZDoom-Android-2026), the base of route B1 |
| **PrBoom For Android** (F-Droid `android.game.prboom`) | first ported by Vladimir Silva for the G1 era | **Yes**, GPL-3.0 per F-Droid; F-Droid notes the upstream source "is no longer available" for an old build | **No** (PrBoom: vanilla/Boom maps, no ZScript, no PK3 mods) | No |
| GZDoom-Android / GZDA (nvllsvm, dports) | GitHub, discontinued 2024 or earlier | Yes, GPL | old builds, no current ZScript | No |

So: if the CEO played on Android before 2019 with a touch layout, it was most
likely Beloko's **Doom Touch / D-Touch** (today Delta Touch) or the open
**Freedoom for Android / PrBoom** builds; from 2019 on, possibly Bethesda's
official DOOM. Which one exactly cannot be known from here. **The truly open
ones are too old for our ZScript; the one that runs our engine is Delta
Touch, whose engine is open but whose app is not.** That is exactly the gap
route B1 fills, and why its licence question (§1b) matters.

## Sources

- Delta Touch on Google Play (read in the built-in browser, 2026-10-24): https://play.google.com/store/apps/details?id=com.opentouchgaming.deltatouch&hl=en_US&gl=US
- Delta Touch GZDoom 4.14.2 selection and mod folders (third-party guide): https://teletype.in/@easyapk_telegram/sharpshooter3d-android-guide
- Delta Touch mod loading reports: https://steamcommunity.com/app/2300/discussions/0/3095635055516492759 , https://gbatemp.net/goto/post?id=9738651 , https://itch.io/post/8911704
- Delta Touch on DoomWiki (search snippet only; the page refused the fetch): https://doomwiki.org/wiki/Delta_Touch
- emileb repositories (GitHub API): https://github.com/emileb/gzdoom (branch `mobile_g4.14.2`), https://github.com/emileb/MobileTouchControls (`License.txt`), https://github.com/emileb/Clibs_OpenTouch , https://github.com/emileb/AndroidCore_OpenTouch , https://github.com/emileb/Zeta_Touch
- https://github.com/manuelsiuro/GZDoom-Android-2026 (README, LICENSE, tree)
- https://github.com/dports/GZDA , https://github.com/andrewrabert/GZDoom-Android , https://github.com/mkrupczak3/Freedoom-for-Android , https://f-droid.org/de/packages/net.nullsum.freedoom/
- https://github.com/DrBeef/QuestZDoom ; QuestZDoom engine history: https://vrscout.com/news/doom-vr-mod-isabelle-companion-oculus-quest
- GZDoom and UZDoom releases: https://github.com/ZDoom/gzdoom/releases , https://github.com/UZDoom/UZDoom/releases , https://www.gamingonlinux.com/2025/11/gzdoom-successor-project-uzdoom-gets-a-first-preview-release/ , https://www.gamingonlinux.com/2026/08/gzdoom-successor-uzdoom-5-0-is-officially-out-now/
- WASM: https://github.com/blahm1dplays/uzdoom-wasm , https://github.com/HyperCrab2000/doom
- Android developer verification: https://support.google.com/android-developer-console/answer/16561738?hl=en ; Brazil in the first wave: https://www.androidauthority.com/android-sideloading-changes-timeline-3679204/
- Play closed testing: https://support.google.com/googleplay/android-developer/answer/14151465?hl=en-GB
- Play and Nazi symbols: https://support.google.com/googleplay/android-developer/answer/7022576?hl=en , https://gameluster.com/google-play-blocks-anti-nazi-game-over-nazi-references/
- Galaxy M55: https://m.gsmarena.com/samsung_galaxy_m55-12896.php ; Adreno 644 APIs: https://www.notebookcheck.net/Adreno-644-vs-Adreno-618-vs-Adreno-660_11580_9900_10603.247598.0.html ; Auto Blocker: https://news.samsung.com/us/setting-boundaries-without-building-walls-choice-means-stronger-security-dr-seungwon-shin-samsung/ , https://9to5google.com/?p=593360
- Older Doom apps: https://doomwiki.org/wiki/Unity_port , https://doomwiki.org/wiki/Freedoom_For_Android , https://f-droid.org/packages/android.game.prboom/ (search snippet; the page returned 404 when fetched)
- GPL compatibility: https://www.gnu.org/licenses/license-list.html#GPLv2 ; CC BY-NC-SA 4.0: https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode
