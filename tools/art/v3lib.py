"""Shared helpers of the V3 intermission art (ADR 013): the operations map
(gen_ops_map.py) and the medals (gen_medals.py).

  snap()            nearest palette colour per pixel, no dither (ART-BIBLE 2)
  sprite_from_rgba  a supersampled RGBA drawing -> hard-alpha RGBA in the palette
  png_bytes()       PNG bytes, with a grAb chunk when the picture has offsets
  BitmapFont        draws text with the mod's OWN approved folder fonts
                    (assets/fonts/<name>/<HEX>.png): no system font is ever
                    opened (D27), so the previews render the same on every
                    machine, letter for letter what the engine draws

Pillow and numpy are imported lazily so the module can be imported by the
stdlib-only parts of the test suite.
"""

from __future__ import annotations

import io
import struct
import zlib
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
FONTS_DIR = PROJECT_ROOT / "assets" / "fonts"

# Half a pixel covered -> opaque (the cursor's rule, gen_mouse_cursor).
COVERAGE_CUT = 0.5
# Palette version the V3 intermission art is drawn in (ART-BIBLE 3): v2 adds
# mosaic_gold, the medals' gold, and marble_red, their claret ribbons.
PALETTE_VERSION = 2


def palette_array():
    import numpy as np
    import palette
    return np.array(palette.colours(PALETTE_VERSION), dtype=np.int32)


def snap(rgb):
    """(h, w, 3) uint8 -> the same array with every pixel replaced by its
    nearest palette colour (squared RGB distance; ties to the lower index)."""
    import numpy as np
    pal = palette_array()
    flat = rgb.reshape(-1, 3).astype(np.int32)
    out = np.empty_like(flat)
    step = 16384
    for i in range(0, len(flat), step):
        chunk = flat[i:i + step]
        d = ((chunk[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        out[i:i + step] = pal[d.argmin(axis=1)]
    return out.reshape(rgb.shape).astype(np.uint8)


def sprite_from_rgba(big, size):
    """A supersampled RGBA PIL image -> (w, h) RGBA PIL image with hard alpha
    (COVERAGE_CUT) and every opaque pixel snapped to the palette."""
    import numpy as np
    from PIL import Image
    small = big.resize(size, Image.Resampling.BOX)
    arr = np.asarray(small, dtype=np.float64)
    alpha = arr[..., 3]
    opaque = alpha >= 255 * COVERAGE_CUT
    rgb = np.zeros(arr.shape[:2] + (3,), dtype=np.float64)
    nz = alpha > 0
    rgb[nz] = arr[nz, :3] * 255.0 / alpha[nz, None]   # un-premultiply the box filter's edge
    rgb = snap(np.clip(rgb, 0, 255).astype(np.uint8))
    out = np.zeros(arr.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(opaque, 255, 0)
    out[~opaque, :3] = 0
    return Image.fromarray(out, "RGBA")


def png_bytes(img, grab: tuple[int, int] | None = None) -> bytes:
    """PNG bytes of a PIL image; with `grab`, a grAb chunk (the x, y offsets
    GZDoom reads: the picture is drawn with that pixel on the given point)
    right after IHDR. Deterministic: no timestamps, no text chunks."""
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    if grab is None:
        return data
    body = b"grAb" + struct.pack(">ii", *grab)
    chunk = struct.pack(">I", 8) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    return data[:33] + chunk + data[33:]


def read_grab(blob: bytes) -> tuple[int, int] | None:
    """The grAb offsets of PNG bytes, or None."""
    pos = 8
    while pos + 8 <= len(blob):
        length, kind = struct.unpack(">I4s", blob[pos:pos + 8])
        if kind == b"grAb":
            return struct.unpack(">ii", blob[pos + 8:pos + 16])
        if kind == b"IDAT":
            return None
        pos += 12 + length
    return None


# ------------------------------------------------------------ bitmap fonts
class BitmapFont:
    """One of the mod's folder fonts, read from assets/fonts/<name>/.

    Like the engine: the advance of a glyph is its picture's width, the
    line height is font.inf's FontHeight, and a letter with no glyph is
    drawn with its upper-case form (the fonts are capitals-only;
    src/common/fonts/font.cpp draws lower case with the capitals).
    `colour` recolours the glyph's lit pixels by their brightness, an
    approximation of the engine's font translations (CR_GOLD, CR_RED...),
    good enough for a preview and labelled as such.
    """

    def __init__(self, name: str):
        from PIL import Image
        self.name = name
        folder = FONTS_DIR / name
        self.height = 9
        inf = folder / "font.inf"
        if inf.is_file():
            for line in inf.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0].lower() == "fontheight":
                    self.height = int(parts[1])
        self.glyphs = {}
        for p in folder.glob("*.png"):
            try:
                code = int(p.stem, 16)
            except ValueError:
                continue
            self.glyphs[code] = Image.open(p).convert("RGBA")

    def glyph(self, ch: str):
        code = ord(ch)
        if code in self.glyphs:
            return self.glyphs[code]
        up = ord(ch.upper()) if len(ch.upper()) == 1 else code
        return self.glyphs.get(up)

    def has(self, ch: str) -> bool:
        return self.glyph(ch) is not None

    def width(self, text: str) -> int:
        return sum(self.glyph(c).width for c in text if self.glyph(c) is not None)

    def draw(self, canvas, x: int, y: int, text: str, colour=None, scale: int = 1) -> int:
        """Draw onto an RGBA PIL canvas at (x, y) (top-left); returns the width."""
        from PIL import Image
        cx = x
        for ch in text:
            g = self.glyph(ch)
            if g is None:
                continue
            if colour is not None:
                g = _tint(g, colour)
            if scale != 1:
                g = g.resize((g.width * scale, g.height * scale), Image.Resampling.NEAREST)
            canvas.alpha_composite(g, (int(cx), int(y)))
            cx += g.width
        return int(cx - x)


def _tint(glyph, colour):
    import numpy as np
    from PIL import Image
    a = np.asarray(glyph, dtype=np.float64).copy()
    lum = a[..., :3].max(axis=2)
    lit = lum > 64
    peak = max(lum[lit].max(), 1.0) if lit.any() else 1.0
    for i in range(3):
        a[..., i] = np.where(lit, colour[i] * (0.35 + 0.65 * lum / peak), a[..., i])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
