"""Minimal WAD writer (PWAD only).

WAD layout (Doom spec, little-endian):
  header    : 4 bytes magic ("PWAD" or "IWAD"), int32 numlumps,
              int32 infotableofs (byte offset of the directory)
  lump data : concatenated lump bytes (we 4-byte align them; not required
              by the format but harmless and conventional)
  directory : numlumps entries of 16 bytes each:
              int32 filepos, int32 size, char[8] name (NUL padded)

A "lump" is just a named blob. Map markers (MAP01) and ENDMAP are zero-size
lumps whose only purpose is their name/position in the directory.
"""

from __future__ import annotations

import struct
from typing import Iterable, Sequence

HEADER_STRUCT = struct.Struct("<4sii")
DIR_ENTRY_STRUCT = struct.Struct("<ii8s")
MAX_LUMP_NAME = 8  # hard limit of the WAD format
LUMP_ALIGN = 4     # alignment of lump data; cosmetic, keeps offsets tidy

Lump = tuple[str, bytes]


class WadError(ValueError):
    """Raised when a lump name is not representable in a WAD directory."""


def validate_lump_name(name: str) -> str:
    """Return the canonical (uppercase) lump name or raise WadError.

    Lump names are ASCII, at most 8 chars, conventionally uppercase. We also
    forbid characters that GZDoom's parsers treat specially in lump names.
    """
    if not name:
        raise WadError("empty lump name")
    if len(name) > MAX_LUMP_NAME:
        raise WadError(f"lump name {name!r} longer than {MAX_LUMP_NAME} chars")
    try:
        name.encode("ascii")
    except UnicodeEncodeError as exc:
        raise WadError(f"lump name {name!r} is not ASCII") from exc
    upper = name.upper()
    for ch in upper:
        if not (ch.isalnum() or ch in "_[]-\\"):
            raise WadError(f"lump name {name!r} has invalid character {ch!r}")
    return upper


def build_pwad(lumps: Sequence[Lump] | Iterable[Lump]) -> bytes:
    """Serialize (name, data) pairs into PWAD bytes, preserving order."""
    lumps = list(lumps)
    if not lumps:
        raise WadError("a WAD needs at least one lump")

    body = bytearray()
    directory: list[tuple[int, int, bytes]] = []
    for name, data in lumps:
        canonical = validate_lump_name(name)
        if not isinstance(data, (bytes, bytearray)):
            raise WadError(f"lump {canonical} data must be bytes")
        # Pad previous data so this lump starts aligned.
        while len(body) % LUMP_ALIGN:
            body.append(0)
        filepos = HEADER_STRUCT.size + len(body)
        body.extend(data)
        # Empty markers conventionally point at offset 0 in some tools; any
        # value is valid for a 0-size lump. We keep the real offset.
        directory.append((filepos, len(data), canonical.encode("ascii")))

    while len(body) % LUMP_ALIGN:
        body.append(0)
    infotableofs = HEADER_STRUCT.size + len(body)

    out = bytearray()
    out.extend(HEADER_STRUCT.pack(b"PWAD", len(directory), infotableofs))
    out.extend(body)
    for filepos, size, name8 in directory:
        out.extend(DIR_ENTRY_STRUCT.pack(filepos, size, name8))
    return bytes(out)


def read_directory(blob: bytes) -> list[tuple[str, int, int]]:
    """Parse a WAD and return [(name, filepos, size), ...] in directory order.

    Used by tests and by build-time self-checks; it is deliberately tiny and
    tolerant (it does not read lump contents).
    """
    if len(blob) < HEADER_STRUCT.size:
        raise WadError("blob too small to be a WAD")
    magic, numlumps, infotableofs = HEADER_STRUCT.unpack_from(blob, 0)
    if magic not in (b"PWAD", b"IWAD"):
        raise WadError(f"bad WAD magic {magic!r}")
    entries = []
    for i in range(numlumps):
        off = infotableofs + i * DIR_ENTRY_STRUCT.size
        filepos, size, name8 = DIR_ENTRY_STRUCT.unpack_from(blob, off)
        entries.append((name8.rstrip(b"\0").decode("ascii"), filepos, size))
    return entries


def read_lump(blob: bytes, name: str) -> bytes:
    """Return the bytes of the first lump called `name` (case-insensitive)."""
    wanted = name.upper()
    for lump_name, filepos, size in read_directory(blob):
        if lump_name.upper() == wanted:
            return blob[filepos:filepos + size]
    raise KeyError(name)
