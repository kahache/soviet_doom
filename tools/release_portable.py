#!/usr/bin/env python3
"""Assemble the "unzip and play" packages of Soviet Doom (P5, D93, D101/D102).

Usage:
  python tools/release_portable.py --version 1.0 --out D:/somewhere \\
      --release-zip path/to/sovietdoom-1.0.zip     # repackage a release
  python tools/release_portable.py --version 1.0 --out D:/somewhere
                                                   # build it from this tree
  python tools/release_portable.py --platform macos --version 1.0 --out D:/somewhere \\
      --release-zip path/to/sovietdoom-1.0.zip \\
      --engine-archive path/to/gzdoom-4-14-2-macos.zip
  python tools/release_portable.py --platform linux --version 1.0 --out D:/somewhere \\
      --release-zip path/to/sovietdoom-1.0.zip \\
      --engine-archive path/to/gzdoom_4.14.2_amd64.deb \\
      --gzdoom-source path/to/gzdoom-g4.14.2-source.tar.gz

--platform is windows (the default), macos or linux. The macOS and Linux
packages are described after the Windows one, below.

It publishes nothing. It writes <out>/sovietdoom-<version>-windows.zip and
sovietdoom-<version>-windows.zip.sha256 beside it; <out> must be outside the
repo. The zip holds one folder, SovietDoom/, with:

  gzdoom.exe, gzdoom.pk3, the DLLs, soundfonts/, fm_banks/, the optional
                   engine pk3s (lights, brightmaps, game support, widescreen
                   graphics) and licenses.zip: GZDoom g4.14.2 for Windows,
                   copied unmodified from the local install
                   (%LOCALAPPDATA%/Programs/GZDoom, or --engine-dir); only
                   the files of ENGINE_FILES and ENGINE_DIRS, so a user's
                   ini, saves, screenshots or WADs in that folder never ship
  gzdoom_portable.ini
                   GZDoom's portable switch: when this file exists next to
                   gzdoom.exe (and the folder is not under Program Files),
                   GZDoom keeps its ini, Save/ and Screenshots/ in this folder
                   instead of Documents and Saved Games
                   (src/common/platform/win32/i_specialpaths.cpp, IsPortable)
  freedoom2.wad    Freedoom: Phase 2 0.13.0 from iwads/, SHA-256 pinned
  sovietdoom.pk3, LICENSE.md, LICENSE-*.txt, CREDITS.txt
                   the release's own files (tools/release.py), byte for byte
  README.txt       the release's readme with a short note on top saying that
                   in this package GZDoom and Freedoom are already present
  Jugar Soviet Doom.bat, Play Soviet Doom.bat
                   the launchers (Spanish and English messages, same command)
  LEEME.txt, README-FIRST.txt
                   how to unzip, start, get past SmartScreen, switch to
                   Russian, the keys; Spanish and English
  GZDOOM-SOURCE.txt
                   GPL: where the exact source of the bundled engine and its
                   libraries is, plus a written offer; the SHA-256 of every
                   engine file
  SHA256SUMS       `sha256sum -c` format, every other file of the folder

macOS (--platform macos) writes sovietdoom-<version>-macos.zip: SovietDoom/
holds GZDoom.app, every entry copied from the official g4.14.2 macOS zip
(--engine-archive) with its bytes and its Unix mode (ZipInfo.external_attr:
executables stay 755, symlinks stay symlinks, the AppleDouble ._* files that
carry the code signatures of the bundle's data files stay beside them); the
zip's Licenses/ as gzdoom-licenses/; freedoom2.wad and the release files;
"Jugar Soviet Doom.command" and "Play Soviet Doom.command" (sh, mode 755);
LEEME.txt and README-FIRST.txt (Gatekeeper); GZDOOM-SOURCE.txt; SHA256SUMS.

Linux (--platform linux) writes sovietdoom-<version>-linux.tar.gz: SovietDoom/
holds gzdoom/ (the /opt/gzdoom tree of the official g4.14.2 .deb, read in
pure Python: the ar archive and its data.tar, no dpkg), gzdoom-licenses/
(docs/licenses/ of the g4.14.2 source archive, --gzdoom-source: the .deb
ships no licence texts), freedoom2.wad, the release files, play.sh and
jugar.sh (mode 755), LEEME.txt and README-FIRST.txt (the system libraries
the .deb's control file declares, and the apt command), GZDOOM-SOURCE.txt,
SHA256SUMS. Directories 755, executables 755, other files 644, owner root,
every mtime the release zip's, gzip header without name or time.

The release files come from --release-zip (checked: one folder
sovietdoom-<version>/, exactly release.RELEASE_FILES, its SHA256SUMS true)
or, without it, from tools/release.py's make_release run on this tree (which
refuses a dirty tree unless --allow-dirty, tests only).

Deterministic: same inputs, same bytes. Entries sorted, every timestamp the
release zip's own (the commit's time), fixed permissions and "made on" system.

It refuses (exit 1, nothing written) when the engine is missing a required
file or is not g4.14.2, freedoom2.wad is missing or is not 0.13.0, the release
zip is malformed, two inputs claim the same name, or --out is inside the repo;
for macOS and Linux also when the engine archive holds an unsafe path, a
symlink that leaves the engine folder, or a member that is neither a file, a
folder nor a symlink. The engine archives are read as data, never run.

Docs: docs/engine/RELEASE.md, "Portable packages (P5)".
"""

from __future__ import annotations

import argparse
import calendar
import gzip
import hashlib
import io
import os
import plistlib
import posixpath
import re
import stat
import sys
import tarfile
import tempfile
import textwrap
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import release  # noqa: E402  (tools/release.py: the release files and their checks)

EXIT_OK = 0
EXIT_REFUSED = 1

FOLDER = "SovietDoom"
PLATFORM = "windows"                   # the default platform
MACOS = "macos"
LINUX = "linux"
PLATFORMS = (PLATFORM, MACOS, LINUX)

# --- The engine -------------------------------------------------------------------

ENGINE_TAG = "g4.14.2"                 # D3: the engine the mod is tested on
ENGINE_TAG_BYTES = ENGINE_TAG.encode("ascii")
ENGINE_EXE = "gzdoom.exe"
DEFAULT_ENGINE_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "GZDoom"

# Top-level files of the official Windows build. Required ones refuse the
# package when absent; optional ones ship when present. Nothing else in the
# install folder is copied (a portable install there would hold a user's
# gzdoom_portable.ini, Save/, Screenshots/; someone may have dropped WADs).
ENGINE_REQUIRED = (ENGINE_EXE, "gzdoom.pk3", "zmusic.dll", "openal32.dll", "sndfile.dll",
                   "licenses.zip")
ENGINE_OPTIONAL = ("brightmaps.pk3", "lights.pk3", "game_support.pk3",
                   "game_widescreen_gfx.pk3")
ENGINE_FILES = ENGINE_REQUIRED + ENGINE_OPTIONAL
# Folders copied whole (MIDI soundfont and OPL/OPN banks the engine reads).
ENGINE_DIRS = ("soundfonts", "fm_banks")
ENGINE_DIRS_REQUIRED = ("soundfonts",)

PORTABLE_INI = "gzdoom_portable.ini"

# --- Freedoom ------------------------------------------------------------------------

IWAD_NAME = "freedoom2.wad"
DEFAULT_IWAD = PROJECT_ROOT / "iwads" / IWAD_NAME
# Freedoom 0.13.0's freedoom2.wad, as checked against the signed release
# CHECKSUM (docs/qa/GATE-REVIEWS.md, G0).
FREEDOOM2_SHA256 = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"

# --- The texts we write ----------------------------------------------------------------

BAT_ES = "Jugar Soviet Doom.bat"
BAT_EN = "Play Soviet Doom.bat"
LEEME_NAME = "LEEME.txt"
README_FIRST_NAME = "README-FIRST.txt"
SOURCE_NAME = "GZDOOM-SOURCE.txt"
UTF8_BOM = b"\xef\xbb\xbf"   # Notepad on older Windows 10 needs it to read UTF-8

GZDOOM_REPO = "https://github.com/ZDoom/gzdoom"
GZDOOM_TREE = f"{GZDOOM_REPO}/tree/{ENGINE_TAG}"
GZDOOM_RELEASE = f"{GZDOOM_REPO}/releases/tag/{ENGINE_TAG}"
GZDOOM_SOURCE_ZIP = f"{GZDOOM_REPO}/archive/refs/tags/{ENGINE_TAG}.zip"
GZDOOM_SOURCE_TGZ = f"{GZDOOM_REPO}/archive/refs/tags/{ENGINE_TAG}.tar.gz"
ISSUES_URL = "https://github.com/kahache/soviet_doom/issues"

# The launcher. `cd /d` makes the folder the working directory; the three
# paths are absolute (%~dp0 ends with a backslash) so neither GZDoom's IWAD
# search path nor the caller's directory matters. -iwad also keeps GZDoom
# from showing its IWAD picker: in g4.14.2 (src/d_iwad.cpp, IdentifyVersion)
# the picker opens when `queryiwad && no -iwad` or when more than one
# candidate remains, and a found -iwad leaves exactly one. If gzdoom.exe is
# not beside the .bat (it was opened from inside the zip without extracting),
# it says so and waits. ASCII only: cmd.exe reads .bat files in the OEM
# code page.
BAT_TEMPLATE = """\
@echo off
rem Soviet Doom {version} - portable package for Windows.
rem Starts GZDoom {engine} with Freedoom: Phase 2 and the mod; nothing is installed.
cd /d "%~dp0"
if exist "%~dp0{exe}" goto play
echo {missing}
pause
exit /b 1
:play
start "" "%~dp0{exe}" -iwad "%~dp0{iwad}" -file "%~dp0{pk3}"
"""
BAT_MISSING = {
    BAT_ES: ("No encuentro {exe} junto a este archivo. Primero descomprime el zip: "
             "clic derecho sobre el zip, Extraer todo, y abre la carpeta {folder}."),
    BAT_EN: ("{exe} is not next to this file. Unzip the package first: right-click "
             "the zip, Extract All, then open the folder {folder}."),
}

PORTABLE_INI_TEXT = """\
# Soviet Doom portable package. While this file sits next to gzdoom.exe,
# GZDoom keeps its settings (in this file), saves (Save) and screenshots
# (Screenshots) inside this folder. GZDoom rewrites it when you quit.
"""

README_NOTE = """\
THIS IS THE PORTABLE WINDOWS PACKAGE. GZDoom {engine} and Freedoom are
already in this folder: double-click "Play Soviet Doom.bat" (see
README-FIRST.txt). The sections WHAT YOU NEED and HOW TO START below are for
playing the mod in a GZDoom of your own.
ЭТО ПОРТАТИВНАЯ ВЕРСИЯ ДЛЯ WINDOWS. GZDoom {engine} и Freedoom уже в этой
папке: дважды щёлкните «Play Soviet Doom.bat». Разделы ЧТО НУЖНО и КАК
ЗАПУСТИТЬ ниже — для игры в вашем собственном GZDoom.

"""

# The menu path to the language switch, from LANGUAGE (release.README_IDS
# names the ids) so the texts and the game agree. The game starts in English
# on a Spanish or English Windows, so both texts quote the English labels.
MENU_IDS = ("newgame", "ep01", "ep02", "options", "optmnu", "language", "langru",
            "langen", "langauto")

LEEME_TEMPLATE = """\
SOVIET DOOM {version} PARA WINDOWS - LISTO PARA JUGAR
{rule}

Todo lo necesario está en esta carpeta: el juego, el motor GZDoom {engine} y
Freedoom. No hay que instalar nada.

CÓMO JUGAR
  1. Descomprime el zip: clic derecho sobre {zipname}
     > "Extraer todo..." y elige dónde (el Escritorio o Documentos valen).
     No lo abras desde dentro del zip sin extraerlo, y no pongas la carpeta
     en "Archivos de programa" (C:\\Program Files): ahí GZDoom no puede
     guardar las partidas dentro de la carpeta.
  2. Abre la carpeta {folder} y haz doble clic en "Jugar Soviet Doom"
     (o en "Play Soviet Doom": es lo mismo).
  3. En el juego: {newgame} > {ep01}, y elige la dificultad.
     {ep02} es el campo de tiro, con todas las armas.

SI WINDOWS AVISA
  GZDoom es gratuito y no lleva una firma digital de pago, así que Windows
  puede avisar la primera vez:
  - "Windows protegió su PC": pulsa "Más información" y luego
    "Ejecutar de todas formas".
  - "Advertencia de seguridad - ¿Desea ejecutar este archivo?": "Ejecutar".
  Para que no avise, ANTES de descomprimir: clic derecho sobre el zip >
  Propiedades > marca "Desbloquear" > Aceptar.

RUSO (O INGLÉS)
  El juego empieza en inglés. Para jugar en ruso:
  {options} > {optmnu} > {language} > {langru}.
  Cambia al momento y se recuerda. Las otras opciones: {langen}, y
  {langauto}, que sigue el idioma de Windows.

CONTROLES
  Moverse ............ W A S D
  Girar y apuntar .... ratón
  Disparar ........... botón izquierdo del ratón
  Usar ............... E: abrir puertas, pulsar interruptores
  Saltar ............. Espacio
  Correr ............. mantén Mayúsculas; Bloq Mayús corre siempre
  Armas .............. 1 a 7, o la rueda del ratón
  Mapa ............... Tab
  Guardar / cargar ... F2 / F3; rápido: F6 / F9
  Menú ............... Esc
  Se cambian en Options > Customize Controls.

TUS PARTIDAS
  Todo se queda en esta carpeta: las partidas en Save, las capturas en
  Screenshots y la configuración en {ini}.
  No se escribe nada en Documentos. Para desinstalar, borra la carpeta.
  Para conservar las partidas en una versión nueva, copia Save y
  {ini} a la carpeta nueva.

LICENCIAS
  Soviet Doom: código GPL 3.0, arte, sonido, mapas y textos CC BY-NC-SA 4.0
  (LICENSE.md); créditos en CREDITS.txt. GZDoom: GPL 3.0 y otras licencias
  libres (licenses.zip); su código fuente exacto: {source}. Freedoom:
  licencia BSD (LICENSE-FREEDOOM-BSD-3.txt). Proyecto de aficionados, sin
  relación con id Software.
"""

README_FIRST_TEMPLATE = """\
SOVIET DOOM {version} FOR WINDOWS - READY TO PLAY
{rule}

Everything is in this folder: the game, the GZDoom {engine} engine and
Freedoom. Nothing to install.

HOW TO PLAY
  1. Unzip it: right-click {zipname}
     > "Extract All..." and pick a place (the Desktop or Documents is fine).
     Do not run it from inside the zip without extracting, and do not put
     the folder in C:\\Program Files: there GZDoom cannot keep your saves
     in the folder.
  2. Open the folder {folder} and double-click "Play Soviet Doom"
     (or "Jugar Soviet Doom": the same thing).
  3. In the game: {newgame} > {ep01}, then pick a difficulty.
     {ep02} is the shooting range, with every weapon.

IF WINDOWS WARNS YOU
  GZDoom is free and carries no paid digital signature, so Windows may
  warn the first time:
  - "Windows protected your PC": click "More info", then "Run anyway".
  - "Security Warning - Do you want to run this file?": "Run".
  To avoid the warnings, BEFORE unzipping: right-click the zip >
  Properties > tick "Unblock" > OK.

RUSSIAN
  The game starts in English. To play in Russian:
  {options} > {optmnu} > {language} > {langru}.
  It applies at once and is remembered. The other choices: {langen}, and
  {langauto}, which follows Windows' language.

CONTROLS
  Move ............ W A S D
  Turn and aim .... mouse
  Fire ............ left mouse button
  Use ............. E: open doors, press switches
  Jump ............ Space
  Run ............. hold Shift; Caps Lock toggles always-run
  Weapons ......... 1 to 7, or the mouse wheel
  Automap ......... Tab
  Save / load ..... F2 / F3; quick: F6 / F9
  Menu ............ Esc
  Change them in Options > Customize Controls.

YOUR SAVES
  Everything stays in this folder: saves in Save, screenshots in
  Screenshots, settings in {ini}.
  Nothing is written to Documents. To uninstall, delete the folder.
  To keep your saves in a newer version, copy Save and
  {ini} into the new folder.

LICENCES
  Soviet Doom: code GPL 3.0, art, sound, maps and text CC BY-NC-SA 4.0
  (LICENSE.md); credits in CREDITS.txt. GZDoom: GPL 3.0 and other free
  licences (licenses.zip); its exact source code: {source}. Freedoom: BSD
  licence (LICENSE-FREEDOOM-BSD-3.txt). A fan project, not affiliated with
  id Software.
"""

# The libraries the Windows build ships as DLLs, their licence and where
# their source is. Versions read from the DLLs' version resources on the PC
# that made the package (2026-10-20); zmusic.dll carries none.
LIBRARIES = (
    ("zmusic.dll", "ZMusic, the ZDoom team's music library (GPL 3.0; parts LGPL)",
     "the release GZDoom g4.14.2 ships with (the DLL records no version):\n"
     "      https://github.com/ZDoom/ZMusic/releases"),
    ("openal32.dll", "OpenAL Soft 1.23.1 (GNU LGPL 2)",
     "https://github.com/kcat/openal-soft/tree/1.23.1"),
    ("sndfile.dll", "libsndfile 1.2.2 (GNU LGPL 2.1)",
     "https://github.com/libsndfile/libsndfile/releases/tag/1.2.2"),
)

# The same libraries in the macOS build: linked into the gzdoom executable
# (no dylib ships). libsndfile 1.2.2 is named inside the executable; OpenAL
# Soft and ZMusic record no version there. MoltenVK is Vulkan on Metal.
LIBRARIES_MACOS = (
    ("ZMusic", "the ZDoom team's music library (GPL 3.0; parts LGPL)",
     "the version GZDoom g4.14.2's macOS build used (not recorded in it):\n"
     "      https://github.com/ZDoom/ZMusic/releases"),
    ("OpenAL Soft", "the version the build used, not recorded in it (GNU LGPL 2)",
     "https://github.com/kcat/openal-soft"),
    ("libsndfile", "libsndfile 1.2.2 (GNU LGPL 2.1)",
     "https://github.com/libsndfile/libsndfile/releases/tag/1.2.2"),
    ("MoltenVK", "Vulkan on Metal (Apache 2.0)",
     "https://github.com/KhronosGroup/MoltenVK"),
)
# The Linux .deb ships one library beside the executable; the others come
# from the system (LEEME.txt lists them), so this package does not carry them.
LIBRARIES_LINUX = (
    ("libzmusic.so.1", "ZMusic, the ZDoom team's music library (GPL 3.0; parts LGPL)",
     "the release GZDoom g4.14.2 ships with (the file records no version):\n"
     "      https://github.com/ZDoom/ZMusic/releases"),
)

# GPL 3.0 §6(d): the corresponding source sits on the same server as the
# binaries. The PM attached these archives to the v1.0 release (2026-10-21);
# they stay valid for every package that ships GZDoom g4.14.2.
SOURCES_RELEASE = "https://github.com/kahache/soviet_doom/releases/tag/v1.0"
SOURCE_ARCHIVES = (
    ("gzdoom-g4.14.2-source.tar.gz", "GZDoom g4.14.2"),
    ("openal-soft-1.23.1-source.tar.gz", "OpenAL Soft 1.23.1"),
    ("libsndfile-1.2.2-source.tar.gz", "libsndfile 1.2.2"),
    ("zmusic-1.1.14-source.tar.gz", "ZMusic 1.1.14"),
)

# What differs between the platforms in GZDOOM-SOURCE.txt.
SOURCE_PLATFORM = {
    PLATFORM: dict(
        build="Windows (64-bit)",
        licences="licenses.zip (GZDoom's own file, unchanged)",
        libraries_intro="The libraries shipped as DLLs, and their source:",
        libraries=LIBRARIES),
    MACOS: dict(
        build="macOS (Intel and Apple\nsilicon)",
        licences="the folder gzdoom-licenses\n(GZDoom's own texts, unchanged)",
        libraries_intro=("The libraries linked into GZDoom.app's executable, and their\n"
                         "  source:"),
        libraries=LIBRARIES_MACOS),
    LINUX: dict(
        build="Linux (x86-64: /opt/gzdoom of\nthe official .deb)",
        licences="the folder gzdoom-licenses\n(GZDoom's own texts, unchanged)",
        libraries_intro=("The library shipped beside the executable, and its source (OpenAL\n"
                         "  Soft, libsndfile, SDL2 and the rest come from your system):"),
        libraries=LIBRARIES_LINUX),
}

SOURCE_TEMPLATE = """\
GZDOOM IN THIS PACKAGE: LICENCE AND SOURCE CODE
{rule}

This package includes GZDoom {engine} for {build}, unmodified, as
built and published by the ZDoom team:
  {release_url}
GZDoom is free software under the GNU General Public License, version 3
(the full text: LICENSE-GPL-3.0.txt in this folder); parts of it are under
the other licences listed in {licences}.

THE SOURCE CODE
  The complete corresponding source of this exact version, and of the
  libraries below, is attached to Soviet Doom's v1.0 release on GitHub:
    {sources_release}
  as these archives:
{source_archives}
  It is also the tag {engine} of GZDoom's public repository:
    {tree_url}
  as a single archive:
    {zip_url}
    {tgz_url}
  {libraries_intro}
{libraries}

WRITTEN OFFER
  If any of these links stops working, ask at
    {issues_url}
  and we will provide the complete corresponding source code of GZDoom
  {engine} and of the libraries above, as shipped in this package, at no
  charge beyond the cost of the medium. This offer is valid to anyone who
  receives this package, for three years after we last distribute it.

THE ENGINE FILES (SHA-256)
{hashes}
"""


# --- macOS and Linux ---------------------------------------------------------------------

# Unix modes as they go in the archives (zip external_attr >> 16, tar mode).
MODE_DIR = stat.S_IFDIR | 0o755
MODE_FILE = stat.S_IFREG | 0o644
MODE_EXEC = stat.S_IFREG | 0o755
MODE_LINK = stat.S_IFLNK | 0o755
ZIP_DIR_FLAG = 0x10                    # MS-DOS directory bit in external_attr

# The official macOS zip: GZDoom.app plus a Licenses/ folder.
MAC_APP = "GZDoom.app"
MAC_EXE = f"{MAC_APP}/Contents/MacOS/gzdoom"
MAC_PLIST = f"{MAC_APP}/Contents/Info.plist"
MAC_LICENCES = "Licenses"
APPLEDOUBLE_PREFIX = "._"              # xattrs (here: code signatures) in a file of their own
# The official .deb: the engine lives in /opt/gzdoom; the rest of data.tar
# (a /usr/games wrapper, a .desktop file, an icon) is not needed.
DEB_ENGINE_ROOT = "opt/gzdoom"
DEB_VERSION = ENGINE_TAG.lstrip("g")   # the control file says 4.14.2
LINUX_ENGINE_DIR = "gzdoom"
LINUX_EXE = f"{LINUX_ENGINE_DIR}/gzdoom"
SOURCE_TOP = f"gzdoom-{ENGINE_TAG}"    # the top folder of GZDoom's source archive
SOURCE_LICENCES = f"{SOURCE_TOP}/docs/licenses"
# Both: GZDoom's licence texts, in a folder of their own.
ENGINE_LICENCE_DIR = "gzdoom-licenses"

UNIX_INI = "gzdoom.ini"
SAVE_DIR = "saves"
COMMAND_ES = "Jugar Soviet Doom.command"
COMMAND_EN = "Play Soviet Doom.command"
SH_ES = "jugar.sh"
SH_EN = "play.sh"

# libzmusic.so.1 names libsndfile.so.1 (it decodes the mod's OGG sounds);
# the .deb's control file does not declare it, so the guides add it.
LINUX_EXTRA_PACKAGES = ("libsndfile1",)

# The launcher for macOS and Linux. `cd` to the script's folder (a
# .command starts in the home folder), then absolute paths built from it:
# a relative -iwad is only looked up in GZDoom's IWAD search directories
# (src/d_iwad.cpp), and -config / -savedir keep the settings and the saves
# in this folder. "$@" passes any extra argument on. No braces: str.format.
SH_TEMPLATE = """\
#!/bin/sh
# Soviet Doom {version} - portable package for {system}.
# Starts GZDoom {engine} with Freedoom: Phase 2 and the mod; nothing is installed.
cd "$(dirname "$0")" || exit 1
HERE="$(pwd -P)"
ENGINE="$HERE/{exe}"
if [ ! -x "$ENGINE" ]; then
  echo "{missing}"
{wait}  exit 1
fi
mkdir -p "$HERE/{saves}"
exec "$ENGINE" -iwad "$HERE/{iwad}" -file "$HERE/{pk3}" -config "$HERE/{ini}" -savedir "$HERE/{saves}" "$@"
"""
# A .command runs in a Terminal window that closes its process at once:
# wait for Enter so the message can be read.
SH_WAIT = {COMMAND_ES: '  echo "Pulsa Intro para cerrar."\n  read -r _\n',
           COMMAND_EN: '  echo "Press Enter to close."\n  read -r _\n',
           SH_ES: "", SH_EN: ""}
SH_MISSING = {
    COMMAND_ES: ("No encuentro GZDoom.app junto a este archivo. Descomprime primero el zip "
                 "(doble clic) y abre la carpeta {folder}."),
    COMMAND_EN: ("GZDoom.app is not next to this file. Unzip the package first "
                 "(double-click it), then open the folder {folder}."),
    SH_ES: ("No encuentro gzdoom/gzdoom (ejecutable) junto a este archivo. Extrae "
            "el paquete con: tar xzf {archive}"),
    SH_EN: ("gzdoom/gzdoom (executable) is not next to this file. Extract the "
            "package with: tar xzf {archive}"),
}

README_NOTE_MACOS = """\
THIS IS THE PORTABLE MACOS PACKAGE. GZDoom {engine} and Freedoom are
already in this folder: double-click "Play Soviet Doom.command" (read
README-FIRST.txt first: macOS asks once). The sections WHAT YOU NEED and
HOW TO START below are for playing the mod in a GZDoom of your own.
ЭТО ПОРТАТИВНАЯ ВЕРСИЯ ДЛЯ MACOS. GZDoom {engine} и Freedoom уже в этой
папке: дважды щёлкните «Play Soviet Doom.command» (сначала прочтите
README-FIRST.txt). Разделы ЧТО НУЖНО и КАК ЗАПУСТИТЬ ниже — для игры в
вашем собственном GZDoom.

"""
README_NOTE_LINUX = """\
THIS IS THE PORTABLE LINUX PACKAGE. GZDoom {engine} and Freedoom are
already in this folder: run ./play.sh (read README-FIRST.txt first: a few
system libraries are needed). The sections WHAT YOU NEED and HOW TO START
below are for playing the mod in a GZDoom of your own.
ЭТО ПОРТАТИВНАЯ ВЕРСИЯ ДЛЯ LINUX. GZDoom {engine} и Freedoom уже в этой
папке: запустите ./play.sh (сначала прочтите README-FIRST.txt: нужны
системные библиотеки). Разделы ЧТО НУЖНО и КАК ЗАПУСТИТЬ ниже — для игры
в вашем собственном GZDoom.

"""

# The parts the macOS and Linux guides share with each other.
CONTROLS_ES = """\
CONTROLES
  Moverse ............ W A S D
  Girar y apuntar .... ratón
  Disparar ........... botón izquierdo del ratón
  Usar ............... E: abrir puertas, pulsar interruptores
  Saltar ............. Espacio
  Correr ............. mantén Mayúsculas; Bloq Mayús corre siempre
  Armas .............. 1 a 7, o la rueda del ratón
  Mapa ............... Tab
  Guardar / cargar ... F2 / F3; rápido: F6 / F9
  Menú ............... Esc
  Se cambian en Options > Customize Controls.
"""
CONTROLS_EN = """\
CONTROLS
  Move ............ W A S D
  Turn and aim .... mouse
  Fire ............ left mouse button
  Use ............. E: open doors, press switches
  Jump ............ Space
  Run ............. hold Shift; Caps Lock toggles always-run
  Weapons ......... 1 to 7, or the mouse wheel
  Automap ......... Tab
  Save / load ..... F2 / F3; quick: F6 / F9
  Menu ............ Esc
  Change them in Options > Customize Controls.
"""

LEEME_MACOS_TEMPLATE = """\
SOVIET DOOM {version} PARA MACOS - LISTO PARA JUGAR
{rule}

Todo lo necesario está en esta carpeta: el juego, el motor GZDoom {engine}
(GZDoom.app, para Mac Intel y Apple silicon, macOS {macos_min} o posterior)
y Freedoom. No hay que instalar nada.

CÓMO JUGAR
  1. Doble clic sobre {zipname} (Safari puede haberlo
     descomprimido ya): aparece la carpeta {folder}. Muévela donde
     quieras, por ejemplo a Documentos.
  2. La primera vez, macOS bloquea lo descargado de internet que no viene
     de la App Store ni de un desarrollador identificado (Gatekeeper).
     GZDoom es gratuito y no está firmado por Apple. Lo más sencillo:
     abre Terminal (Aplicaciones > Utilidades > Terminal), escribe
         xattr -dr com.apple.quarantine
     con un espacio al final, arrastra la carpeta {folder} a la ventana
     de Terminal y pulsa Intro. Solo hace falta una vez.
     Sin Terminal: clic derecho (o Control-clic) sobre
     "Jugar Soviet Doom.command" > Abrir > Abrir. En macOS 15 (Sequoia) o
     posterior ya no sale esa opción: tras el aviso, ve a Ajustes del
     Sistema > Privacidad y seguridad y pulsa "Abrir igualmente"; si
     luego avisa por "gzdoom", repite lo mismo.
  3. Doble clic en "Jugar Soviet Doom.command" (o en
     "Play Soviet Doom.command": es lo mismo). Se abre una ventana de
     Terminal y después el juego. No cierres la ventana mientras juegas.
  4. En el juego: {newgame} > {ep01}, y elige la dificultad.
     {ep02} es el campo de tiro, con todas las armas.

RUSO (O INGLÉS)
  El juego empieza en inglés. Para jugar en ruso:
  {options} > {optmnu} > {language} > {langru}.
  Cambia al momento y se recuerda. Las otras opciones: {langen}, y
  {langauto}, que sigue el idioma del sistema.

{controls_es}
TUS PARTIDAS
  Las partidas se guardan en la carpeta {saves} y la configuración en
  {ini}, dentro de esta carpeta. Para desinstalar, borra la carpeta.
  Para conservar las partidas en una versión nueva, copia {saves} y
  {ini} a la carpeta nueva.

LICENCIAS
  Soviet Doom: código GPL 3.0, arte, sonido, mapas y textos CC BY-NC-SA 4.0
  (LICENSE.md); créditos en CREDITS.txt. GZDoom: GPL 3.0 y otras licencias
  libres (carpeta {licdir}); su código fuente exacto:
  {source}. Freedoom: licencia BSD (LICENSE-FREEDOOM-BSD-3.txt).
  Proyecto de aficionados, sin relación con id Software.
"""

README_FIRST_MACOS_TEMPLATE = """\
SOVIET DOOM {version} FOR MACOS - READY TO PLAY
{rule}

Everything is in this folder: the game, the GZDoom {engine} engine
(GZDoom.app, for Intel and Apple silicon Macs, macOS {macos_min} or later)
and Freedoom. Nothing to install.

HOW TO PLAY
  1. Double-click {zipname} (Safari may have unzipped it
     already): the folder {folder} appears. Move it wherever you like,
     Documents for instance.
  2. The first time, macOS blocks what was downloaded from the internet
     and does not come from the App Store or an identified developer
     (Gatekeeper). GZDoom is free and not signed by Apple. The simplest
     way: open Terminal (Applications > Utilities > Terminal), type
         xattr -dr com.apple.quarantine
     with a space at the end, drag the folder {folder} onto the Terminal
     window and press Return. Once is enough.
     Without Terminal: right-click (or Control-click)
     "Play Soviet Doom.command" > Open > Open. On macOS 15 (Sequoia) or
     later that choice is gone: after the warning, go to System Settings >
     Privacy & Security and click "Open Anyway"; if it then warns about
     "gzdoom", do the same again.
  3. Double-click "Play Soviet Doom.command" (or
     "Jugar Soviet Doom.command": the same thing). A Terminal window
     opens, then the game. Keep that window open while you play.
  4. In the game: {newgame} > {ep01}, then pick a difficulty.
     {ep02} is the shooting range, with every weapon.

RUSSIAN
  The game starts in English. To play in Russian:
  {options} > {optmnu} > {language} > {langru}.
  It applies at once and is remembered. The other choices: {langen}, and
  {langauto}, which follows the system's language.

{controls_en}
YOUR SAVES
  Saves go in the folder {saves} and settings in {ini}, inside this
  folder. To uninstall, delete the folder. To keep your saves in a newer
  version, copy {saves} and {ini} into the new folder.

LICENCES
  Soviet Doom: code GPL 3.0, art, sound, maps and text CC BY-NC-SA 4.0
  (LICENSE.md); credits in CREDITS.txt. GZDoom: GPL 3.0 and other free
  licences (the folder {licdir}); its exact source code:
  {source}. Freedoom: BSD licence (LICENSE-FREEDOOM-BSD-3.txt).
  A fan project, not affiliated with id Software.
"""

LEEME_LINUX_TEMPLATE = """\
SOVIET DOOM {version} PARA LINUX - LISTO PARA JUGAR
{rule}

En esta carpeta están el juego, el motor GZDoom {engine} (Linux de 64 bits,
{arch}; los archivos del .deb oficial) y Freedoom. GZDoom usa algunas
bibliotecas del sistema que hay que tener instaladas.

LO QUE HACE FALTA
  El .deb oficial de GZDoom {engine} declara estas dependencias (Depends):
{depends}
  y recomienda {recommends} (sin OpenAL no hay sonido). Además,
  {extra}: el juego la usa para los sonidos OGG y el .deb no la
  declara.
  En Debian, Ubuntu, Mint y derivadas, todo de una vez:
{apt}
  (En Ubuntu 24.04 o posterior, si apt dice que libasound2 no tiene
  candidato, cámbialo por libasound2t64.) En otras distribuciones,
  instala los paquetes equivalentes (SDL2, OpenAL, libsndfile...).

CÓMO JUGAR
  1. Extrae el paquete donde quieras (tu carpeta personal vale):
         tar xzf {zipname}
     o con el gestor de archivos de tu escritorio (conserva los permisos).
  2. En una terminal:
         cd {folder}
         ./jugar.sh
     (o ./play.sh: es lo mismo).
  3. En el juego: {newgame} > {ep01}, y elige la dificultad.
     {ep02} es el campo de tiro, con todas las armas.

RUSO (O INGLÉS)
  El juego empieza en inglés. Para jugar en ruso:
  {options} > {optmnu} > {language} > {langru}.
  Cambia al momento y se recuerda. Las otras opciones: {langen}, y
  {langauto}, que sigue el idioma del sistema.

{controls_es}
TUS PARTIDAS
  Las partidas se guardan en la carpeta {saves} y la configuración en
  {ini}, dentro de esta carpeta. Para desinstalar, borra la carpeta.
  Para conservar las partidas en una versión nueva, copia {saves} y
  {ini} a la carpeta nueva.

LICENCIAS
  Soviet Doom: código GPL 3.0, arte, sonido, mapas y textos CC BY-NC-SA 4.0
  (LICENSE.md); créditos en CREDITS.txt. GZDoom: GPL 3.0 y otras licencias
  libres (carpeta {licdir}); su código fuente exacto:
  {source}. Freedoom: licencia BSD (LICENSE-FREEDOOM-BSD-3.txt).
  Proyecto de aficionados, sin relación con id Software.
"""

README_FIRST_LINUX_TEMPLATE = """\
SOVIET DOOM {version} FOR LINUX - READY TO PLAY
{rule}

This folder holds the game, the GZDoom {engine} engine (64-bit Linux,
{arch}; the files of the official .deb) and Freedoom. GZDoom uses a few
system libraries that must be installed.

WHAT YOU NEED
  The official GZDoom {engine} .deb declares these dependencies (Depends):
{depends}
  and recommends {recommends} (without OpenAL there is no sound). Also
  {extra}: the game uses it for the OGG sounds and the .deb does not
  declare it. On Debian, Ubuntu, Mint and derivatives, all at once:
{apt}
  (On Ubuntu 24.04 or later, if apt says libasound2 has no installation
  candidate, use libasound2t64 instead.) On other distributions, install
  the equivalent packages (SDL2, OpenAL, libsndfile...).

HOW TO PLAY
  1. Extract the package anywhere (your home folder is fine):
         tar xzf {zipname}
     or with your desktop's archive manager (it keeps the permissions).
  2. In a terminal:
         cd {folder}
         ./play.sh
     (or ./jugar.sh: the same thing).
  3. In the game: {newgame} > {ep01}, then pick a difficulty.
     {ep02} is the shooting range, with every weapon.

RUSSIAN
  The game starts in English. To play in Russian:
  {options} > {optmnu} > {language} > {langru}.
  It applies at once and is remembered. The other choices: {langen}, and
  {langauto}, which follows the system's language.

{controls_en}
YOUR SAVES
  Saves go in the folder {saves} and settings in {ini}, inside this
  folder. To uninstall, delete the folder. To keep your saves in a newer
  version, copy {saves} and {ini} into the new folder.

LICENCES
  Soviet Doom: code GPL 3.0, art, sound, maps and text CC BY-NC-SA 4.0
  (LICENSE.md); credits in CREDITS.txt. GZDoom: GPL 3.0 and other free
  licences (the folder {licdir}); its exact source code:
  {source}. Freedoom: BSD licence (LICENSE-FREEDOOM-BSD-3.txt).
  A fan project, not affiliated with id Software.
"""


class PortableError(RuntimeError):
    """A refusal: the message says what to fix; nothing was written."""


@dataclass
class Config:
    version: str
    out_dir: Path
    engine_dir: Path = DEFAULT_ENGINE_DIR
    iwad: Path = DEFAULT_IWAD
    release_zip: Path | None = None     # None: build with release.make_release
    allow_dirty: bool = False           # only for the build from this tree
    repo_root: Path = PROJECT_ROOT
    platform: str = PLATFORM
    engine_archive: Path | None = None  # macOS: the official zip; Linux: the .deb
    gzdoom_source: Path | None = None   # Linux: GZDoom's source archive (licence texts)


@dataclass
class Portable:
    zip_path: Path
    sha_path: Path
    members: list[str]
    warnings: list[str] = field(default_factory=list)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crlf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", "\r\n")


@dataclass(frozen=True)
class Entry:
    """One member of a macOS or Linux package, by its path inside SovietDoom/.

    mode is the full Unix st_mode (type and permission bits); data is a
    file's bytes or a symlink's target. external_attr, when set, is copied
    verbatim into the zip (an entry of the official macOS zip)."""
    path: str
    mode: int
    data: bytes = b""
    external_attr: int | None = None

    @property
    def is_dir(self) -> bool:
        return stat.S_ISDIR(self.mode)

    @property
    def is_link(self) -> bool:
        return stat.S_ISLNK(self.mode)

    @property
    def is_file(self) -> bool:
        return stat.S_ISREG(self.mode)


def safe_path(name: str, what: str) -> str:
    """A relative POSIX path with no '..', no backslash, no empty part."""
    clean = name[2:] if name.startswith("./") else name
    clean = clean.rstrip("/")
    parts = clean.split("/")
    if (not clean or clean.startswith("/") or "\\" in clean or ":" in parts[0]
            or any(part in ("", ".", "..") for part in parts)):
        raise PortableError(f"{what} holds an unsafe path: {name!r}")
    return clean


def check_link(path: str, target: str, root: str, what: str) -> None:
    """A symlink must point inside root (relative, no escape)."""
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
    if target.startswith("/") or not (resolved == root or resolved.startswith(root + "/")):
        raise PortableError(f"{what}: the symlink {path} -> {target} leaves {root}/")


# --- Inputs --------------------------------------------------------------------------

def engine_files(engine_dir: Path, warnings: list[str] | None = None) -> dict[str, bytes]:
    """The engine's files by their path in the package (forward slashes)."""
    if not (engine_dir / ENGINE_EXE).is_file():
        raise PortableError(f"no GZDoom at {engine_dir} ({ENGINE_EXE} missing); give the "
                            f"unzipped GZDoom {ENGINE_TAG} for Windows with --engine-dir")
    missing = [name for name in ENGINE_REQUIRED if not (engine_dir / name).is_file()]
    missing += [name + "/" for name in ENGINE_DIRS_REQUIRED
                if not (engine_dir / name).is_dir()]
    if missing:
        raise PortableError(f"the GZDoom at {engine_dir} lacks {', '.join(missing)}")
    files: dict[str, bytes] = {}
    for name in ENGINE_FILES:
        path = engine_dir / name
        if path.is_file():
            files[name] = path.read_bytes()
    if ENGINE_TAG_BYTES not in files[ENGINE_EXE]:
        raise PortableError(f"{engine_dir / ENGINE_EXE} is not GZDoom {ENGINE_TAG} (the mod is "
                            "tested on it and GZDOOM-SOURCE.txt points to its source)")
    for folder in ENGINE_DIRS:
        root = engine_dir / folder
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files[path.relative_to(engine_dir).as_posix()] = path.read_bytes()
    if warnings is not None:
        shipped = set(files)
        for path in sorted(engine_dir.rglob("*")):
            rel = path.relative_to(engine_dir).as_posix()
            if path.is_file() and rel not in shipped:
                warnings.append(f"not packed from the engine folder: {rel}")
    return files


def read_iwad(path: Path) -> bytes:
    if not path.is_file():
        raise PortableError(f"{IWAD_NAME} not found: {path} (Freedoom 0.13.0, iwads/)")
    data = path.read_bytes()
    if sha256(data) != FREEDOOM2_SHA256:
        raise PortableError(f"{path} is not Freedoom 0.13.0's {IWAD_NAME} "
                            f"(SHA-256 {sha256(data)}, expected {FREEDOOM2_SHA256})")
    return data


# --- The macOS and Linux engines -----------------------------------------------------------

@dataclass
class UnixEngine:
    entries: list[Entry]                  # paths inside SovietDoom/
    licences: dict[str, bytes]            # GZDoom's licence texts, by file name
    facts: dict[str, object] = field(default_factory=dict)   # what the guides quote


def read_macos_engine(path: Path | None, warnings: list[str]) -> UnixEngine:
    """GZDoom.app and Licenses/ from the official macOS zip, modes and all."""
    if path is None or not path.is_file():
        raise PortableError(f"--engine-archive not found: {path} (give the official GZDoom "
                            f"{ENGINE_TAG} macOS zip, gzdoom-4-14-2-macos.zip)")
    what = path.name
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise PortableError(f"{what} is not a zip: {exc}") from exc
    entries: dict[str, Entry] = {}
    licences: dict[str, bytes] = {}
    with zf:
        for info in zf.infolist():
            name = safe_path(info.filename, what)
            mode = info.external_attr >> 16
            if info.create_system != release.ZIP_CREATE_SYSTEM_UNIX or not stat.S_IFMT(mode):
                raise PortableError(f"{what}: {info.filename} carries no Unix mode; the "
                                    "bundle's modes could not be kept")
            top = name.split("/", 1)[0]
            if top == MAC_LICENCES:
                if stat.S_ISDIR(mode):
                    continue
                if not stat.S_ISREG(mode) or name == top:
                    raise PortableError(f"{what}: {info.filename} is not a licence text")
                licences[name[len(top) + 1:]] = zf.read(info)
                continue
            if top != MAC_APP:
                warnings.append(f"not packed from {what}: {info.filename}")
                continue
            if name in entries:
                raise PortableError(f"{what} holds {name} twice")
            if stat.S_ISDIR(mode):
                data = b""
            elif stat.S_ISREG(mode):
                data = zf.read(info)
            elif stat.S_ISLNK(mode):
                data = zf.read(info)
                check_link(name, data.decode("utf-8"), MAC_APP, what)
            else:
                raise PortableError(f"{what}: {info.filename} is neither a file, a folder "
                                    "nor a symlink")
            entries[name] = Entry(name, mode, data, info.external_attr)
    exe = entries.get(MAC_EXE)
    if exe is None or not exe.is_file:
        raise PortableError(f"{what} lacks {MAC_EXE}; is it GZDoom's macOS zip?")
    if not exe.mode & 0o111:
        raise PortableError(f"{what}: {MAC_EXE} is not executable (mode {oct(exe.mode)})")
    if ENGINE_TAG_BYTES not in exe.data:
        raise PortableError(f"{what}: {MAC_EXE} is not GZDoom {ENGINE_TAG}")
    plist_entry = entries.get(MAC_PLIST)
    try:
        plist = plistlib.loads(plist_entry.data) if plist_entry else {}
    except Exception as exc:                  # plistlib raises several kinds
        raise PortableError(f"{what}: {MAC_PLIST} does not parse: {exc}") from exc
    if plist.get("CFBundleShortVersionString") != ENGINE_TAG:
        raise PortableError(f"{what}: {MAC_PLIST} does not say {ENGINE_TAG} "
                            f"({plist.get('CFBundleShortVersionString')!r})")
    if not licences:
        raise PortableError(f"{what} has no {MAC_LICENCES}/ folder with GZDoom's licence texts")
    facts = {"macos_min": str(plist.get("LSMinimumSystemVersion", "10.15"))}
    return UnixEngine(sorted(entries.values(), key=lambda e: e.path), licences, facts)


AR_MAGIC = b"!<arch>\n"
AR_HEADER = 60
AR_END = b"`\n"


def read_ar(data: bytes, what: str) -> dict[str, bytes]:
    """The members of a Unix ar archive (a .deb is one), by name."""
    if not data.startswith(AR_MAGIC):
        raise PortableError(f"{what} is not a .deb (no ar header)")
    members: dict[str, bytes] = {}
    pos = len(AR_MAGIC)
    while pos < len(data):
        header = data[pos:pos + AR_HEADER]
        if len(header) < AR_HEADER or header[58:60] != AR_END:
            raise PortableError(f"{what}: a broken ar header at byte {pos}")
        name = header[:16].decode("ascii", "replace").strip().rstrip("/")
        try:
            size = int(header[48:58].decode("ascii").strip())
        except ValueError as exc:
            raise PortableError(f"{what}: a broken ar size at byte {pos}") from exc
        start = pos + AR_HEADER
        if start + size > len(data):
            raise PortableError(f"{what}: the member {name} is cut short")
        members[name] = data[start:start + size]
        pos = start + size + (size & 1)
    return members


def open_member_tar(members: dict[str, bytes], prefix: str, what: str) -> tarfile.TarFile:
    names = [name for name in members if name.startswith(prefix + ".tar")]
    if len(names) != 1:
        raise PortableError(f"{what} must hold one {prefix}.tar.*, not {sorted(members)}")
    try:
        return tarfile.open(fileobj=io.BytesIO(members[names[0]]), mode="r:*")
    except (tarfile.TarError, OSError, EOFError, ValueError) as exc:
        raise PortableError(f"{what}: {names[0]} does not open: {exc}") from exc


def parse_control(text: str) -> dict[str, str]:
    """A Debian control file's fields (continuation lines joined)."""
    fields: dict[str, str] = {}
    key = None
    for line in text.splitlines():
        if line[:1] in (" ", "\t") and key:
            fields[key] += " " + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            fields[key] = value.strip()
    return fields


def deb_packages(value: str) -> list[str]:
    """Package names of a Depends-like field: the first of each alternative,
    without version or architecture qualifiers."""
    names = []
    for item in value.split(","):
        first = item.split("|")[0].strip()
        name = re.split(r"[\s(:]", first, maxsplit=1)[0]
        if name:
            names.append(name)
    return names


def read_linux_engine(path: Path | None, warnings: list[str]) -> UnixEngine:
    """/opt/gzdoom of the official .deb as gzdoom/, and its control file."""
    if path is None or not path.is_file():
        raise PortableError(f"--engine-archive not found: {path} (give the official GZDoom "
                            f"{ENGINE_TAG} .deb, gzdoom_4.14.2_amd64.deb)")
    what = path.name
    members = read_ar(path.read_bytes(), what)
    if not members.get("debian-binary", b"").startswith(b"2."):
        raise PortableError(f"{what} is not a .deb (debian-binary missing or not 2.x)")
    with open_member_tar(members, "control", what) as tf:
        control = None
        for member in tf.getmembers():
            if member.isreg() and member.name.lstrip("./") == "control":
                control = tf.extractfile(member).read().decode("utf-8", "replace")
    if control is None:
        raise PortableError(f"{what} has no control file")
    fields = parse_control(control)
    if fields.get("Package") != "gzdoom" or fields.get("Version") != DEB_VERSION:
        raise PortableError(f"{what} is not GZDoom {ENGINE_TAG} (control says "
                            f"{fields.get('Package')!r} {fields.get('Version')!r})")
    entries: dict[str, Entry] = {}
    with open_member_tar(members, "data", what) as tf:
        for member in tf.getmembers():
            if member.name in (".", "./", ""):
                continue
            name = safe_path(member.name, what)
            if name != DEB_ENGINE_ROOT and not name.startswith(DEB_ENGINE_ROOT + "/"):
                if not member.isdir():
                    warnings.append(f"not packed from {what}: /{name}")
                continue
            rel = name[len(DEB_ENGINE_ROOT):].lstrip("/")
            out = LINUX_ENGINE_DIR + ("/" + rel if rel else "")
            if member.isdir():
                entry = Entry(out, MODE_DIR)
            elif member.isreg():
                mode = MODE_EXEC if member.mode & 0o111 else MODE_FILE
                entry = Entry(out, mode, tf.extractfile(member).read())
            elif member.issym():
                check_link(out, member.linkname, LINUX_ENGINE_DIR, what)
                entry = Entry(out, MODE_LINK, member.linkname.encode("utf-8"))
            else:
                raise PortableError(f"{what}: /{name} is neither a file, a folder nor a "
                                    "symlink")
            if out in entries:
                raise PortableError(f"{what} holds /{name} twice")
            entries[out] = entry
    exe = entries.get(LINUX_EXE)
    if exe is None or not exe.is_file:
        raise PortableError(f"{what} lacks /{DEB_ENGINE_ROOT}/gzdoom; is it GZDoom's .deb?")
    if not exe.mode & 0o111:
        raise PortableError(f"{what}: /{DEB_ENGINE_ROOT}/gzdoom is not executable")
    if ENGINE_TAG_BYTES not in exe.data:
        raise PortableError(f"{what}: /{DEB_ENGINE_ROOT}/gzdoom is not GZDoom {ENGINE_TAG}")
    facts = {"arch": fields.get("Architecture", "amd64"),
             "depends": deb_packages(fields.get("Depends", "")),
             "recommends": deb_packages(fields.get("Recommends", ""))}
    return UnixEngine(sorted(entries.values(), key=lambda e: e.path), {}, facts)


def read_source_licences(path: Path | None) -> dict[str, bytes]:
    """docs/licenses/* of GZDoom's g4.14.2 source archive (the .deb has none)."""
    if path is None or not path.is_file():
        raise PortableError(f"--gzdoom-source not found: {path} (give {SOURCE_TOP}-source"
                            ".tar.gz, the archive attached to the v1.0 release; the .deb "
                            "ships no licence texts)")
    licences: dict[str, bytes] = {}
    tops = set()
    try:
        with tarfile.open(path, mode="r:*") as tf:
            for member in tf:
                tops.add(member.name.lstrip("./").split("/", 1)[0])
                prefix = SOURCE_LICENCES + "/"
                if member.isreg() and member.name.startswith(prefix):
                    rel = member.name[len(prefix):]
                    if "/" not in rel:
                        licences[safe_path(rel, path.name)] = tf.extractfile(member).read()
    except (tarfile.TarError, OSError, EOFError, ValueError) as exc:
        raise PortableError(f"{path.name} does not open: {exc}") from exc
    if tops != {SOURCE_TOP}:
        raise PortableError(f"{path.name} is not GZDoom {ENGINE_TAG}'s source (its top "
                            f"folders: {sorted(tops)[:5]})")
    if not licences:
        raise PortableError(f"{path.name} has no {SOURCE_LICENCES}/")
    return licences


def read_release_zip(data: bytes, version: str) -> tuple[dict[str, bytes], tuple]:
    """The files of a tools/release.py zip, checked, and the entries' timestamp."""
    folder = f"{release.MOD_NAME}-{version}"
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = zf.infolist()
        names = [info.filename for info in infos]
        expected = [f"{folder}/{name}" for name in sorted(release.RELEASE_FILES)]
        if sorted(names) != expected:
            raise PortableError(f"the release zip must hold exactly {expected}, not {names}")
        stamps = {info.date_time for info in infos}
        if len(stamps) != 1:
            raise PortableError("the release zip's entries carry different dates; it was "
                                "not made by tools/release.py")
        files = {name.split("/", 1)[1]: zf.read(name) for name in names}
    sums = files.pop(release.SUMS_NAME).decode("ascii")
    if sums != release.render_sums(files):
        raise PortableError("the release zip's SHA256SUMS does not match its files")
    return files, stamps.pop()


def release_payload(config: Config) -> tuple[dict[str, bytes], tuple]:
    if config.release_zip is not None:
        if not config.release_zip.is_file():
            raise PortableError(f"--release-zip not found: {config.release_zip}")
        return read_release_zip(config.release_zip.read_bytes(), config.version)
    with tempfile.TemporaryDirectory(prefix="sd-portable-") as tmp:
        try:
            made = release.make_release(release.Config(
                config.version, Path(tmp), config.allow_dirty, repo_root=config.repo_root))
        except release.ReleaseError as exc:
            raise PortableError(f"tools/release.py refused: {exc}") from exc
        return read_release_zip(made.zip_path.read_bytes(), config.version)


def menu_names(pk3: bytes) -> dict[str, str]:
    """The English menu labels the texts quote, from the PK3's LANGUAGE."""
    with zipfile.ZipFile(io.BytesIO(pk3)) as zf:
        strings = release.language_strings(zf.read("LANGUAGE").decode("utf-8"))
    english = strings.get(release.LANG_ENGLISH, {})
    names = {}
    for key in MENU_IDS:
        value = english.get(release.README_IDS[key])
        if not value:
            raise PortableError(f"LANGUAGE lacks {release.README_IDS[key]}, which the "
                                "portable readmes quote")
        names[key] = value.title() if value.isupper() else value
    return names


# --- The generated texts -----------------------------------------------------------------

def render_bat(name: str, version: str) -> str:
    missing = BAT_MISSING[name].format(exe=ENGINE_EXE, folder=FOLDER)
    return crlf(BAT_TEMPLATE.format(version=version, engine=ENGINE_TAG, exe=ENGINE_EXE,
                                    iwad=IWAD_NAME, pk3=release.PK3_NAME, missing=missing))


def zip_name(version: str, platform: str = PLATFORM) -> str:
    """The package's file name (a .tar.gz on Linux, where it keeps the modes)."""
    suffix = ".tar.gz" if platform == LINUX else ".zip"
    return f"{release.MOD_NAME}-{version}-{platform}{suffix}"


def render_guide(template: str, version: str, names: dict[str, str]) -> str:
    title = template.splitlines()[0].format(version=version)
    return crlf(template.format(version=version, rule="=" * len(title), engine=ENGINE_TAG,
                                zipname=zip_name(version), folder=FOLDER, ini=PORTABLE_INI,
                                source=SOURCE_NAME, **names))


def render_source(engine: dict[str, bytes], platform: str = PLATFORM) -> str:
    """GZDOOM-SOURCE.txt: CRLF on Windows, LF elsewhere."""
    title = "GZDOOM IN THIS PACKAGE: LICENCE AND SOURCE CODE"
    spec = SOURCE_PLATFORM[platform]
    libraries = "\n".join(f"    {lib}: {what}\n      {where}"
                          for lib, what, where in spec["libraries"])
    archives = "\n".join(f"    {name} ({what})" for name, what in SOURCE_ARCHIVES)
    hashes = "".join(f"  {sha256(engine[name])}  {name}\n" for name in sorted(engine))
    text = SOURCE_TEMPLATE.format(
        rule="=" * len(title), engine=ENGINE_TAG, release_url=GZDOOM_RELEASE,
        build=spec["build"], licences=spec["licences"], sources_release=SOURCES_RELEASE,
        source_archives=archives, libraries_intro=spec["libraries_intro"],
        tree_url=GZDOOM_TREE, zip_url=GZDOOM_SOURCE_ZIP, tgz_url=GZDOOM_SOURCE_TGZ,
        libraries=libraries, issues_url=ISSUES_URL, hashes=hashes.rstrip("\n"))
    return crlf(text) if platform == PLATFORM else text


def render_sh(name: str, version: str, platform: str) -> str:
    """A macOS .command or a Linux .sh launcher (LF, ASCII)."""
    mac = platform == MACOS
    missing = SH_MISSING[name].format(folder=FOLDER, archive=zip_name(version, platform))
    return SH_TEMPLATE.format(
        version=version, system="macOS" if mac else "Linux (x86-64)", engine=ENGINE_TAG,
        exe=MAC_EXE if mac else LINUX_EXE, missing=missing, wait=SH_WAIT[name],
        iwad=IWAD_NAME, pk3=release.PK3_NAME, ini=UNIX_INI, saves=SAVE_DIR)


def apt_command(packages: list[str]) -> str:
    """`sudo apt install ...`, wrapped with backslashes so it pastes as one."""
    lines = textwrap.wrap("sudo apt install " + " ".join(packages), width=64,
                          break_long_words=False, break_on_hyphens=False)
    return " \\\n".join(("    " if i == 0 else "        ") + line
                        for i, line in enumerate(lines))


def linux_packages(facts: dict[str, object]) -> list[str]:
    """Depends, Recommends and LINUX_EXTRA_PACKAGES, once each, in that order."""
    ordered = [*facts["depends"], *facts["recommends"], *LINUX_EXTRA_PACKAGES]
    return list(dict.fromkeys(ordered))


def render_unix_guide(template: str, version: str, platform: str, names: dict[str, str],
                      facts: dict[str, object]) -> str:
    title = template.splitlines()[0].format(version=version)
    extra: dict[str, object] = {}
    if platform == LINUX:
        depends = textwrap.fill(", ".join(facts["depends"]), width=72,
                                initial_indent="    ", subsequent_indent="    ",
                                break_on_hyphens=False)
        extra = dict(arch=facts["arch"], depends=depends,
                     recommends=", ".join(facts["recommends"]) or "-",
                     extra=", ".join(LINUX_EXTRA_PACKAGES),
                     apt=apt_command(linux_packages(facts)))
    else:
        extra = dict(macos_min=facts["macos_min"])
    return template.format(
        version=version, rule="=" * len(title), engine=ENGINE_TAG,
        zipname=zip_name(version, platform), folder=FOLDER, ini=UNIX_INI, saves=SAVE_DIR,
        source=SOURCE_NAME, licdir=ENGINE_LICENCE_DIR, controls_es=CONTROLS_ES,
        controls_en=CONTROLS_EN, **names, **extra)


def is_appledouble(path: str) -> bool:
    return posixpath.basename(path).startswith(APPLEDOUBLE_PREFIX)


def unix_package(platform: str, version: str, release_files: dict[str, bytes],
                 engine: UnixEngine, iwad: bytes) -> list[Entry]:
    """Every entry of SovietDoom/ for macOS or Linux."""
    mac = platform == MACOS
    names = menu_names(release_files[release.PK3_NAME])
    note = (README_NOTE_MACOS if mac else README_NOTE_LINUX).format(engine=ENGINE_TAG)
    # TextEdit and Quick Look read UTF-8 surely with the BOM; Linux tools prefer none.
    bom = UTF8_BOM if mac else b""
    leeme, first = ((LEEME_MACOS_TEMPLATE, README_FIRST_MACOS_TEMPLATE) if mac else
                    (LEEME_LINUX_TEMPLATE, README_FIRST_LINUX_TEMPLATE))
    launchers = (COMMAND_ES, COMMAND_EN) if mac else (SH_ES, SH_EN)
    engine_files_by_path = {e.path: e.data for e in engine.entries if e.is_file}
    ours: dict[str, bytes] = {
        **{name: data for name, data in release_files.items() if name != release.README_NAME},
        release.README_NAME: note.encode("utf-8") + release_files[release.README_NAME],
        IWAD_NAME: iwad,
        LEEME_NAME: bom + render_unix_guide(leeme, version, platform, names,
                                            engine.facts).encode("utf-8"),
        README_FIRST_NAME: bom + render_unix_guide(first, version, platform, names,
                                                   engine.facts).encode("utf-8"),
        SOURCE_NAME: render_source(engine_files_by_path, platform).encode("utf-8"),
        **{f"{ENGINE_LICENCE_DIR}/{name}": data for name, data in engine.licences.items()},
    }
    scripts = {name: render_sh(name, version, platform).encode("ascii") for name in launchers}
    # macOS volumes ignore case by default, so compare that way on both.
    engine_tops = {e.path.split("/", 1)[0].lower() for e in engine.entries}
    clash = sorted({n.split("/", 1)[0].lower() for n in [*ours, *scripts]} & engine_tops)
    if clash:
        raise PortableError(f"the engine and the package both claim {clash}")
    entries = list(engine.entries)
    entries += [Entry(name, MODE_FILE, data) for name, data in ours.items()]
    entries += [Entry(name, MODE_EXEC, data) for name, data in scripts.items()]
    # SHA256SUMS: every regular file but the AppleDouble ones, which macOS's
    # unzip turns into extended attributes, so they are gone after extracting.
    summed = {e.path: e.data for e in entries if e.is_file and not is_appledouble(e.path)}
    entries.append(Entry(release.SUMS_NAME, MODE_FILE,
                         release.render_sums(summed).encode("utf-8")))
    return sorted(entries, key=lambda e: e.path)


def build_macos_zip(entries: list[Entry], stamp: tuple) -> tuple[bytes, list[str]]:
    """The macOS zip: Unix modes kept; folders and symlinks stored, files deflated."""
    buffer = io.BytesIO()
    members = []
    with zipfile.ZipFile(buffer, "w") as zf:
        for entry in sorted(entries, key=lambda e: e.path):
            member = f"{FOLDER}/{entry.path}" + ("/" if entry.is_dir else "")
            info = zipfile.ZipInfo(member, date_time=stamp)
            info.create_system = release.ZIP_CREATE_SYSTEM_UNIX
            if entry.external_attr is not None:
                info.external_attr = entry.external_attr
            else:
                info.external_attr = (entry.mode << 16) | (ZIP_DIR_FLAG if entry.is_dir else 0)
            if any(ord(c) > 127 for c in member):
                info.flag_bits |= 0x800          # UTF-8 name
            if entry.is_file:
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, entry.data, compresslevel=release.ZIP_COMPRESSLEVEL)
            else:
                info.compress_type = zipfile.ZIP_STORED
                zf.writestr(info, entry.data)
            members.append(member)
    return buffer.getvalue(), members


def build_linux_tar(entries: list[Entry], stamp: tuple) -> tuple[bytes, list[str]]:
    """The Linux .tar.gz: every parent folder present, modes 755/644, owner
    root, every mtime the release's, a gzip header with no name and no time."""
    mtime = calendar.timegm((*stamp, 0, 0, 0))
    by_path = {e.path: e for e in entries}
    for path in list(by_path):
        parts = path.split("/")
        for i in range(1, len(parts)):
            by_path.setdefault("/".join(parts[:i]), Entry("/".join(parts[:i]), MODE_DIR))
    raw = io.BytesIO()
    members = [f"{FOLDER}/"]
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.GNU_FORMAT) as tf:
        top = tarfile.TarInfo(FOLDER)
        top.type, top.mode, top.mtime = tarfile.DIRTYPE, 0o755, mtime
        top.uname = top.gname = "root"
        tf.addfile(top)
        for path in sorted(by_path):
            entry = by_path[path]
            info = tarfile.TarInfo(f"{FOLDER}/{path}")
            info.mtime, info.uid, info.gid = mtime, 0, 0
            info.uname = info.gname = "root"
            info.mode = stat.S_IMODE(entry.mode)
            if entry.is_dir:
                info.type = tarfile.DIRTYPE
                tf.addfile(info)
                members.append(info.name + "/")
            elif entry.is_link:
                info.type = tarfile.SYMTYPE
                info.linkname = entry.data.decode("utf-8")
                tf.addfile(info)
                members.append(f"{info.name} -> {info.linkname}")
            else:
                info.size = len(entry.data)
                tf.addfile(info, io.BytesIO(entry.data))
                members.append(info.name)
    out = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=out, compresslevel=9, mtime=0) as gz:
        gz.write(raw.getvalue())
    return out.getvalue(), members


def package_files(version: str, release_files: dict[str, bytes], engine: dict[str, bytes],
                  iwad: bytes) -> dict[str, bytes]:
    """Every file of SovietDoom/, by its path inside the folder."""
    names = menu_names(release_files[release.PK3_NAME])
    readme = README_NOTE.format(engine=ENGINE_TAG).encode("utf-8") + release_files[release.README_NAME]
    ours: dict[str, bytes] = {
        **{name: data for name, data in release_files.items() if name != release.README_NAME},
        release.README_NAME: readme,
        IWAD_NAME: iwad,
        PORTABLE_INI: crlf(PORTABLE_INI_TEXT).encode("ascii"),
        BAT_ES: render_bat(BAT_ES, version).encode("ascii"),
        BAT_EN: render_bat(BAT_EN, version).encode("ascii"),
        LEEME_NAME: UTF8_BOM + render_guide(LEEME_TEMPLATE, version, names).encode("utf-8"),
        README_FIRST_NAME: UTF8_BOM + render_guide(README_FIRST_TEMPLATE, version,
                                                   names).encode("utf-8"),
        SOURCE_NAME: render_source(engine).encode("utf-8"),
    }
    # Windows file names ignore case, so compare them that way.
    clash = sorted({n.lower() for n in ours} & {n.lower() for n in engine})
    if clash:
        raise PortableError(f"the engine folder and the package both claim {clash}")
    files = {**engine, **ours}
    files[release.SUMS_NAME] = release.render_sums(files).encode("utf-8")
    return files


def build_zip(files: dict[str, bytes], stamp: tuple) -> tuple[bytes, list[str]]:
    members = sorted(f"{FOLDER}/{name}" for name in files)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for member in members:
            info = zipfile.ZipInfo(member, date_time=stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = release.ZIP_CREATE_SYSTEM_UNIX
            info.external_attr = release.ZIP_FILE_MODE << 16
            if any(ord(c) > 127 for c in member):
                info.flag_bits |= 0x800          # UTF-8 name
            zf.writestr(info, files[member.split("/", 1)[1]],
                        compresslevel=release.ZIP_COMPRESSLEVEL)
    return buffer.getvalue(), members


def inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def make_portable(config: Config) -> Portable:
    if not release.VERSION_RE.match(config.version or ""):
        raise PortableError(f"--version {config.version!r} is not a release version "
                            "(1.0, 1.0.1, 1.0-rc1; no leading v)")
    if config.platform not in PLATFORMS:
        raise PortableError(f"--platform {config.platform!r} is not one of {PLATFORMS}")
    if inside(config.out_dir, config.repo_root):
        raise PortableError(f"--out {config.out_dir} is inside the repo; the package is "
                            "written outside it")
    warnings: list[str] = []
    if config.platform == PLATFORM:
        if config.engine_archive is not None or config.gzdoom_source is not None:
            raise PortableError("--engine-archive and --gzdoom-source are for macos and "
                                "linux; Windows reads the engine from --engine-dir")
        engine = engine_files(config.engine_dir, warnings)
        iwad = read_iwad(config.iwad)
        release_files, stamp = release_payload(config)
        files = package_files(config.version, release_files, engine, iwad)
        data, members = build_zip(files, stamp)
    else:
        if config.platform == MACOS:
            unix = read_macos_engine(config.engine_archive, warnings)
        else:
            unix = read_linux_engine(config.engine_archive, warnings)
            unix.licences = read_source_licences(config.gzdoom_source)
        iwad = read_iwad(config.iwad)
        release_files, stamp = release_payload(config)
        entries = unix_package(config.platform, config.version, release_files, unix, iwad)
        build = build_macos_zip if config.platform == MACOS else build_linux_tar
        data, members = build(entries, stamp)

    config.out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = config.out_dir / zip_name(config.version, config.platform)
    sha_path = config.out_dir / (zip_path.name + ".sha256")
    release._write_atomic(zip_path, data)
    release._write_atomic(sha_path, f"{sha256(data)}  {zip_path.name}\n".encode("ascii"))
    return Portable(zip_path, sha_path, members, warnings)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tools/release_portable.py", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--version", required=True, help="release version, e.g. 1.0")
    parser.add_argument("--out", type=Path, required=True,
                        help="where the zip goes (outside the repo)")
    parser.add_argument("--release-zip", type=Path,
                        help="the release zip to repackage (default: build it from this tree)")
    parser.add_argument("--engine-dir", type=Path, default=DEFAULT_ENGINE_DIR,
                        help=f"the unzipped GZDoom {ENGINE_TAG} (default: {DEFAULT_ENGINE_DIR})")
    parser.add_argument("--iwad", type=Path, default=DEFAULT_IWAD,
                        help="Freedoom 0.13.0's freedoom2.wad (default: iwads/freedoom2.wad)")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="build the release from a tree with uncommitted changes (TESTS ONLY)")
    parser.add_argument("--platform", choices=PLATFORMS, default=PLATFORM,
                        help=f"which package (default: {PLATFORM})")
    parser.add_argument("--engine-archive", type=Path,
                        help="macos: the official GZDoom g4.14.2 macOS zip; linux: its .deb")
    parser.add_argument("--gzdoom-source", type=Path,
                        help="linux: gzdoom-g4.14.2-source.tar.gz (GZDoom's licence texts)")
    args = parser.parse_args(argv)
    try:
        made = make_portable(Config(args.version, args.out, args.engine_dir, args.iwad,
                                    args.release_zip, args.allow_dirty,
                                    platform=args.platform, engine_archive=args.engine_archive,
                                    gzdoom_source=args.gzdoom_source))
    except PortableError as exc:
        print(f"release_portable: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    for warning in made.warnings:
        print(f"release_portable: warning: {warning}", file=sys.stderr)
    print(made.zip_path)
    for member in made.members:
        print(f"  {member}")
    print(made.sha_path.read_text(encoding="ascii").strip())
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
