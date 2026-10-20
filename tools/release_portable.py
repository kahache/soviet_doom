#!/usr/bin/env python3
"""Assemble the Windows "unzip and double-click" package of Soviet Doom (P5, D93).

Usage:
  python tools/release_portable.py --version 1.0 --out D:/somewhere \\
      --release-zip path/to/sovietdoom-1.0.zip     # repackage a release
  python tools/release_portable.py --version 1.0 --out D:/somewhere
                                                   # build it from this tree

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

The release files come from --release-zip (checked: one folder
sovietdoom-<version>/, exactly release.RELEASE_FILES, its SHA256SUMS true)
or, without it, from tools/release.py's make_release run on this tree (which
refuses a dirty tree unless --allow-dirty, tests only).

Deterministic: same inputs, same bytes. Entries sorted, every timestamp the
release zip's own (the commit's time), fixed permissions and "made on" system.

It refuses (exit 1, nothing written) when the engine is missing a required
file or is not g4.14.2, freedoom2.wad is missing or is not 0.13.0, the release
zip is malformed, two inputs claim the same name, or --out is inside the repo.

Docs: docs/engine/RELEASE.md, "Portable packages (P5)".
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import sys
import tempfile
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
PLATFORM = "windows"

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

SOURCE_TEMPLATE = """\
GZDOOM IN THIS PACKAGE: LICENCE AND SOURCE CODE
{rule}

This package includes GZDoom {engine} for Windows (64-bit), unmodified, as
built and published by the ZDoom team:
  {release_url}
GZDoom is free software under the GNU General Public License, version 3
(the full text: LICENSE-GPL-3.0.txt in this folder); parts of it are under
the other licences listed in licenses.zip (GZDoom's own file, unchanged).

THE SOURCE CODE
  The complete corresponding source of this exact version is the tag
  {engine} of GZDoom's public repository:
    {tree_url}
  as a single archive:
    {zip_url}
    {tgz_url}
  The libraries shipped as DLLs, and their source:
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


def zip_name(version: str) -> str:
    return f"{release.MOD_NAME}-{version}-{PLATFORM}.zip"


def render_guide(template: str, version: str, names: dict[str, str]) -> str:
    title = template.splitlines()[0].format(version=version)
    return crlf(template.format(version=version, rule="=" * len(title), engine=ENGINE_TAG,
                                zipname=zip_name(version), folder=FOLDER, ini=PORTABLE_INI,
                                source=SOURCE_NAME, **names))


def render_source(engine: dict[str, bytes]) -> str:
    title = "GZDOOM IN THIS PACKAGE: LICENCE AND SOURCE CODE"
    libraries = "\n".join(f"    {dll}: {what}\n      {where}" for dll, what, where in LIBRARIES)
    hashes = "".join(f"  {sha256(engine[name])}  {name}\n" for name in sorted(engine))
    return crlf(SOURCE_TEMPLATE.format(
        rule="=" * len(title), engine=ENGINE_TAG, release_url=GZDOOM_RELEASE,
        tree_url=GZDOOM_TREE, zip_url=GZDOOM_SOURCE_ZIP, tgz_url=GZDOOM_SOURCE_TGZ,
        libraries=libraries, issues_url=ISSUES_URL, hashes=hashes.rstrip("\n")))


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
    if inside(config.out_dir, config.repo_root):
        raise PortableError(f"--out {config.out_dir} is inside the repo; the package is "
                            "written outside it")
    warnings: list[str] = []
    engine = engine_files(config.engine_dir, warnings)
    iwad = read_iwad(config.iwad)
    release_files, stamp = release_payload(config)
    files = package_files(config.version, release_files, engine, iwad)
    data, members = build_zip(files, stamp)

    config.out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = config.out_dir / zip_name(config.version)
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
    args = parser.parse_args(argv)
    try:
        made = make_portable(Config(args.version, args.out, args.engine_dir, args.iwad,
                                    args.release_zip, args.allow_dirty))
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
