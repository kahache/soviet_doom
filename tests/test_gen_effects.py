"""Contract of tools/art/gen_effects.py (backlog M2c, D75: the player's
projectiles, their burst, the puff, the blood's shape, the teleport fog,
the barrel and the floor lamp).

Fast (reads text and the lump list only):

  code       the frames and tics each sprite is drawn for are the ones the
             .zs plays: MISL / PLSS / PLSE lines today, or our names once
             mod-engineer has installed them (LETTER_MAP)
  names      lump names are NAMEFR or NAMEFRFR, frames start at A with no
             gap, a rotated frame has its five lumps (2-8, 3-7, 4-6 mirrored)
  override   an IWAD name we override is overridden COMPLETELY: our lumps
             are exactly Freedoom's for that prefix (iwads/ optional)
  prefixes   the new names collide with nothing: no IWAD sprite, no sprite
             in assets/ outside the installed set (assets/sprites/effects/,
             D82), no lump stem anywhere else in assets/, no other
             generator, no state line of another actor

Slow (renders; skipped under SD_SKIP_SLOW_ART=1, as verify.py fast sets):

  palette    every opaque pixel is a palette.json v1 colour, alpha 0/255
  canvas     nothing touches the canvas edge; grAb inside sane bounds
  seed       the same set renders identically twice
  frames     the frames of every animation differ from each other
  blood      BloodColor's stand-in never exceeds AD 27 21
  sweep      three options per item, each with its key frame(s)
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SKIP_SLOW = os.environ.get("SD_SKIP_SLOW_ART") == "1"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
STATE_RE = re.compile(r"^\s*([A-Z0-9]{4})\s+([A-Z\[\]\\]+)\s+(-?\d+)\b")
LABEL_RE = re.compile(r"^\s*([A-Za-z]+):\s*$")


def iwad_sprite_lumps() -> set[str]:
    """Lump names between S_START and S_END of Freedoom's IWAD."""
    import struct
    data = IWAD.read_bytes()
    _, n, off = struct.unpack("<4sii", data[:12])
    names, inside = set(), False
    for i in range(n):
        nm = struct.unpack("<ii8s", data[off + 16 * i:off + 16 * i + 16])[2].rstrip(b"\0").decode("ascii", "replace")
        if nm in ("S_START", "SS_START"):
            inside = True
        elif nm in ("S_END", "SS_END"):
            inside = False
        elif inside:
            names.add(nm)
    return names


def state_lines(path: Path) -> list[tuple[str, str, str, int]]:
    """(label, sprite, frames, tics) for every state line of a .zs file."""
    out, label = [], ""
    for line in path.read_text(encoding="utf-8").splitlines():
        code = line.split("//")[0]
        m = LABEL_RE.match(code)
        if m:
            label = m.group(1)
            continue
        m = STATE_RE.match(code)
        if m and label:
            out.append((label, m.group(1), m.group(2), int(m.group(3))))
    return out


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow (the art venv)")
class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_effects as fx
        cls.fx = fx

    def test_projectile_frames_and_tics_follow_the_code(self):
        fx = self.fx
        seq = {e.key: dict(e.sequences) for e in fx.EFFECTS}
        expected = {"pg7_grenade.zs": ("pg7", "flight", "PG-7V"),
                    "katyusha_rocket.zs": ("katyusha", "flight", "Katyusha"),
                    "flame_blob.zs": ("flame", "flight", None)}
        for name, (key, flight_label, burst_label) in expected.items():
            path = fx.ZS_DIR / "weapons" / name
            letters = fx.LETTER_MAP[name]
            ours = {v[0] for v in letters.values()}
            placeholders = {k[0] for k in letters}
            played: dict[str, list] = {}
            for label, spr, frames, tics in state_lines(path):
                if spr not in ours | placeholders:
                    continue
                for f in frames:
                    sprite, letter = letters[(spr, f)] if spr in placeholders else (spr, f)
                    played.setdefault(sprite, []).append((letter, tics))
            with self.subTest(file=name):
                self.assertTrue(played, f"{name}: no MISL/PLSS/PLSE or SD state line found")
                main = fx.BY_KEY[key].sprite
                self.assertEqual(tuple(played[main]), seq[key][flight_label])
                if burst_label:
                    self.assertEqual(tuple(played["SDPX"]), seq["burst"][burst_label])
                else:
                    self.assertEqual(tuple(played["SDFX"]), seq["flamex"]["impact"])

    def test_placeholder_table_matches_the_code_until_installed(self):
        fx = self.fx
        for name, rows in fx.PLACEHOLDER_STATES.items():
            lines = [ln for ln in state_lines(fx.ZS_DIR / "weapons" / name) if ln[1] in {r[1] for r in rows}]
            if not lines:      # installed: the placeholder lines are gone, the test above holds
                continue
            with self.subTest(file=name):
                self.assertEqual([tuple(x) for x in lines], [tuple(r) for r in rows])

    def test_every_sequence_uses_only_drawn_frames(self):
        for e in self.fx.EFFECTS:
            for label, seq in e.sequences:
                with self.subTest(sprite=e.sprite, seq=label):
                    self.assertTrue(set(f for f, _ in seq) <= set(e.frames))
                    self.assertTrue(all(t > 0 for _, t in seq))
            with self.subTest(sprite=e.sprite, what="every frame is played"):
                self.assertEqual(set(e.frames), {f for _, s in e.sequences for f, _ in s})

    def test_lump_names(self):
        fx = self.fx
        names = fx.all_lumps()
        self.assertEqual(len(names), len(set(names)))
        for e in fx.EFFECTS:
            with self.subTest(sprite=e.sprite):
                self.assertRegex(e.sprite, r"^[A-Z0-9]{4}$")
                self.assertEqual(e.frames, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:len(e.frames)], "frames start at A, no gap")
                lumps = fx.lump_names(e)
                self.assertEqual(len(lumps), len(e.frames) * (5 if e.rotated else 1))
                for n in lumps:
                    self.assertIn(len(n), (6, 8))
                    self.assertTrue(n.startswith(e.sprite))
        self.assertEqual(len(names), 50)

    def test_render_styles_as_the_actors_set_them(self):
        fx = self.fx
        want = {"SDFJ": ("Add", 0.85), "SDFX": ("Add", 0.85), "PUFF": ("Translucent", 0.5),
                "TFOG": ("Add", 1.0), "SDPG": ("Normal", 1.0), "SDKR": ("Normal", 1.0), "SDPX": ("Normal", 1.0),
                "BAR1": ("Normal", 1.0), "BEXP": ("Normal", 1.0), "COLU": ("Normal", 1.0),
                "BLUD": ("Normal", 1.0), "IFOG": ("Normal", 1.0)}
        self.assertEqual({e.sprite: (e.style, e.alpha) for e in fx.EFFECTS}, want)
        flame = (fx.ZS_DIR / "weapons" / "flame_blob.zs").read_text(encoding="utf-8")
        self.assertIn('RenderStyle "Add"', flame)
        self.assertIn("Alpha 0.85", flame)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not in git")
    def test_overrides_are_complete(self):
        fx = self.fx
        lumps = iwad_sprite_lumps()
        for e in fx.EFFECTS:
            if e.install != "override":
                continue
            with self.subTest(sprite=e.sprite):
                self.assertEqual(sorted(n for n in lumps if n.startswith(e.sprite)), sorted(fx.lump_names(e)))

    def test_new_prefixes_collide_with_nothing(self):
        fx = self.fx
        new = set(fx.NEW_PREFIXES)
        self.assertEqual(new, {"SDPG", "SDKR", "SDPX", "SDFJ", "SDFX"})
        self.assertEqual(len(fx.NEW_PREFIXES), len(new))
        sprites = PROJECT_ROOT / "assets" / "sprites"
        installed = sprites / "effects"          # D82: where this set ships (M2c-i)
        others = [p for p in (PROJECT_ROOT / "assets").rglob("*") if p.is_file() and installed not in p.parents]
        shipped = {p.stem[:4] for p in others if sprites in p.parents}
        self.assertFalse(new & shipped, "a sprite in assets/ already uses the name")
        stems = {p.stem.upper() for p in others}
        mine = {n for e in fx.EFFECTS if e.sprite in new for n in fx.lump_names(e)}
        self.assertFalse(mine & stems, "a lump of ours would shadow a file in assets/")
        for py in sorted(ART_TOOLS.glob("*.py")):
            if py.name == "gen_effects.py":
                continue
            text = py.read_text(encoding="utf-8", errors="replace")
            for p in new:
                with self.subTest(generator=py.name, prefix=p):
                    self.assertNotRegex(text, rf"['\"]{p}['\"]|\b{p}[A-Z][0-9]")
        # D116: the P4 bosses' projectiles subclass the PG-7V and the flame
        # blob and restate their burst or flight on the same sprites, on
        # purpose (MOD-SPEC 6.12): reusers, not collisions. V3 (ADR 012): the
        # RGD-5's burst is the PG-7V's SDPX A-C, and stays so.
        allowed = set(fx.LETTER_MAP) | {"colossus_rocket.zs", "colossus_flame.zs",
                                        "consortium_rocket.zs", "consortium_flame.zs",
                                        "rgd5_grenade.zs"}
        for zs in sorted(fx.ZS_DIR.rglob("*.zs")):
            if zs.name in allowed:
                continue
            for _, spr, _, _ in state_lines(zs):
                with self.subTest(zs=zs.name):
                    self.assertNotIn(spr, new)

    @unittest.skipUnless(IWAD.is_file(), "iwads/freedoom2.wad is not in git")
    def test_new_prefixes_are_not_iwad_sprites(self):
        lumps = iwad_sprite_lumps()
        prefixes = {n[:4] for n in lumps}
        self.assertFalse(set(self.fx.NEW_PREFIXES) & prefixes)

    def test_sweep_table(self):
        fx = self.fx
        for item, (rec, opts, _) in fx.SWEEP.items():
            with self.subTest(item=item):
                self.assertIn(len(opts), (2, 3))
                self.assertIn(rec, [o.letter for o in opts])
                self.assertIn(item, fx.SWEEP_FRAMES)
        self.assertEqual(set(fx.OPTION_OF), {e.key for e in fx.EFFECTS})
        self.assertTrue(set(fx.OPTION_OF.values()) <= set(fx.SWEEP))

    def test_mirrored_rotations_need_a_centred_axis(self):
        cv = self.fx.PROJ_CV
        self.assertEqual(cv.cx * 2, cv.w)
        self.assertEqual(self.fx.PROJ_GRAB[0], cv.cx)


@unittest.skipUnless(HAVE_IMAGING, "needs numpy and Pillow (the art venv)")
@unittest.skipIf(SKIP_SLOW, "SD_SKIP_SLOW_ART=1: renders the whole set")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_effects as fx
        cls.fx = fx
        cls.full = {e.key: fx.render_set(e.key) for e in fx.EFFECTS}
        cls.pal = fx.palette_v1()

    def test_count(self):
        self.assertEqual(sum(len(v) for v in self.full.values()), len(self.fx.all_lumps()))
        for e in self.fx.EFFECTS:
            self.assertEqual(list(self.full[e.key]), self.fx.lump_names(e))

    def test_palette_and_hard_alpha(self):
        for key, lumps in self.full.items():
            for name, (rgba, _) in lumps.items():
                with self.subTest(lump=name):
                    a = rgba[..., 3]
                    self.assertTrue(set(np.unique(a)) <= {0, 255})
                    self.assertGreater(int((a > 0).sum()), 8)
                    cols = {tuple(int(v) for v in c) for c in rgba[a > 0][:, :3]}
                    self.assertFalse(cols - self.pal, f"{name}: colours outside palette v1")

    def test_canvas_and_grab(self):
        for key, lumps in self.full.items():
            for name, (rgba, (gx, gy)) in lumps.items():
                with self.subTest(lump=name):
                    a = rgba[..., 3] > 0
                    self.assertFalse(a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any())
                    h, w = a.shape
                    self.assertTrue(0 < gx < w)
                    self.assertTrue(0 < gy <= h + 2)

    def test_standing_things_stand_on_the_floor(self):
        for key in ("barrel", "lamp", "tfog"):
            for name, (rgba, (_, gy)) in self.full[key].items():
                if key == "tfog" and name[4] not in "AB":
                    continue      # C-J rise off the floor as they fade
                lowest = int(np.nonzero(rgba[..., 3].any(axis=1))[0].max())
                with self.subTest(lump=name):
                    self.assertTrue(0 <= lowest - gy <= 4, "sinks 0-4 px into the floor")

    def test_same_seed_same_pixels(self):
        for key in ("burst", "barrel", "pg7", "blood", "tfog"):
            again = self.fx.render_set(key)
            for name, (rgba, grab) in self.full[key].items():
                with self.subTest(lump=name):
                    self.assertTrue(np.array_equal(rgba, again[name][0]))
                    self.assertEqual(grab, again[name][1])

    def test_animation_frames_differ(self):
        for e in self.fx.EFFECTS:
            if e.rotated or len(e.frames) < 2:
                continue
            imgs = [self.full[e.key][n][0] for n in self.fx.lump_names(e)]
            for i in range(len(imgs)):
                for j in range(i + 1, len(imgs)):
                    with self.subTest(sprite=e.sprite, pair=(i, j)):
                        self.assertFalse(imgs[i].shape == imgs[j].shape and np.array_equal(imgs[i], imgs[j]))

    def test_rotations_differ_and_mirror(self):
        fx = self.fx
        rots = fx.projectile_rotations("pg7", fx.recommended("pg7"))
        self.assertEqual(sorted(rots), list(range(1, 9)))
        self.assertFalse(np.array_equal(rots[1], rots[5]))
        self.assertTrue(np.array_equal(rots[7], rots[3][:, ::-1]))

    def test_blood_tint_stays_within_the_blood_colour(self):
        fx = self.fx
        for name, (rgba, _) in self.full["blood"].items():
            t = fx.blood_tint(rgba)
            op = rgba[..., 3] > 0
            with self.subTest(lump=name):
                self.assertTrue((t[op][:, :3] <= np.array(fx.BLOOD_COLOUR)).all())
                self.assertTrue((t[~op] == 0).all())

    def test_sweep_has_every_option(self):
        sweep = self.fx.render_sweep()
        self.assertEqual(len(sweep), sum(len(o) for _, o, _ in self.fx.SWEEP.values()))
        for (item, letter), cells in sweep.items():
            with self.subTest(item=item, option=letter):
                self.assertEqual(len(cells), len(self.fx.SWEEP_FRAMES[item]))


if __name__ == "__main__":
    unittest.main()
