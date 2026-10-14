"""Contract of tools/art/gen_weapon.py (F4: the sergeant's hand, D39; the
ice axe, D40; the PPSh-41; the TT-33, IZh-58, RPG-7, ROKS-3 and hand
Katyusha).

Cheap on purpose: renders a handful of frames, never a sheet. What is checked:

  palette    every opaque pixel is a palette.json colour, alpha is hard 0/255
  D39        hand and sleeve are apart in value in the recommended style
             (the CEO's note: "mismo color de piel y manos")
  telnyashka the recommended style shows both stripe colours at the wrist
             (a round cap once swallowed them: open-ended tubes)
  placement  a HUD frame reaches the bottom of the 320x200 weapon space, so
             no cut edge floats on screen, and its grAb offsets follow
             Doom's arithmetic (left = -leftoffset, top = 32 - topoffset)
  seed       the same frame renders identically twice
  no font    the generator never rasterises text with a system font
  letters    the five later weapons draw exactly the held frames their state
             machine in src/zscript/weapons/ shows, and every flash frame it
             shows (read from the .zs, so an edit there turns this red)

The render tests of the five later weapons (about 30 frames) are skipped
under SD_SKIP_SLOW_ART, as verify.py fast sets it; the letter and name
checks always run.
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "gen_weapon.py"
MIN_HAND_SLEEVE_GAP = 20        # luma; the bare hand A measures ~7, the complaint


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class HandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        cls.style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.idle = gen_weapon.render_axe_frame(cls.style, gen_weapon.AXE_POSE["A"])
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def assert_palette(self, rgba):
        self.assertTrue(set(np.unique(rgba[..., 3])) <= {0, 255})
        opaque = {tuple(int(v) for v in px) for px in rgba[rgba[..., 3] > 0][:, :3]}
        self.assertLessEqual(opaque, self.palette)

    def test_palette_and_hard_alpha(self):
        self.assert_palette(self.idle.rgba)

    def test_hand_and_sleeve_apart(self):
        m = self.g.hand_metrics(self.style, self.idle)
        self.assertGreaterEqual(m["hand_sleeve_gap"], MIN_HAND_SLEEVE_GAP, m)

    def test_telnyashka_shows_both_stripes(self):
        if not self.style.telnyashka:
            self.skipTest("the recommended style has no telnyashka")
        mats = set(np.unique(self.idle.mat).tolist())
        for name in ("tel_white", "tel_blue"):
            self.assertIn(self.g.MAT_ID[name], mats, name)

    def test_reaches_the_bottom_of_the_screen(self):
        f = self.idle
        self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H)
        self.assertLess(f.top, self.g.STATUSBAR_TOP)       # something shows above the bar

    def test_offsets_follow_doom(self):
        f = self.idle
        lo, to = f.offsets()
        self.assertEqual(-lo, f.left)
        self.assertEqual(self.g.WEAPONTOP - to, f.top)
        with tempfile.TemporaryDirectory() as d:
            path = self.g.save_sprite(f, Path(d) / "X.png")
            data = path.read_bytes()
            i = data.index(b"grAb")
            self.assertEqual(struct.unpack(">ii", data[i + 4:i + 12]), (lo, to))
            with Image.open(path) as im:
                self.assertEqual(im.mode, "RGBA")

    def test_kit_renders(self):
        for which in ("grip", "trigger", "support"):
            self.assert_palette(self.g.render_kit(self.style, which).rgba)

    def test_deterministic(self):
        again = self.g.render_axe_frame(self.style, self.g.AXE_POSE["A"])
        self.assertTrue(np.array_equal(again.rgba, self.idle.rgba))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class IceAxeTests(unittest.TestCase):
    """D40: the ice axe's five held frames and its pickup."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.frames = {p.frame: gen_weapon.render_axe_frame(style, p) for p in gen_weapon.AXE_POSES}
        cls.pickups = {o.key: gen_weapon.render_axe_pickup(o.key) for o in gen_weapon.PICKUP_OPTIONS}
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def test_five_frames_like_the_slot_they_fill(self):
        # MOD-SPEC 6.3: the slot-1 weapon has five held frames, A-E
        self.assertEqual(sorted(self.frames), list("ABCDE"))

    def test_palette_and_hard_alpha(self):
        for f in (*self.frames.values(), *self.pickups.values()):
            self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
            opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
            self.assertLessEqual(opaque, self.palette)

    def test_every_held_frame_reaches_the_bottom(self):
        for k, f in self.frames.items():
            self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H, k)

    def test_the_head_is_on_screen_at_rest(self):
        f = self.frames["A"]
        steel = np.nonzero(f.mat == self.g.MAT_ID["steel"])
        self.assertTrue(steel[0].size > 0)
        top = f.top + int(steel[0].min())
        self.assertTrue(0 <= top < self.g.SCREEN_CY, top)

    def test_pickup_stands_on_the_floor(self):
        for k, f in self.pickups.items():
            lo, to = f.offsets()
            h, w = f.rgba.shape[:2]
            self.assertLessEqual(abs(lo - w // 2), 1, k)
            self.assertTrue(h - self.g.PLANT_SINK <= to <= h + 1, (k, to, h))

    def test_pickup_is_pickup_sized(self):
        # Freedoom's chainsaw is 47x19; an ice axe pickup in the same range
        f = self.pickups[self.g.RECOMMENDED_PICKUP]
        self.assertLessEqual(max(f.rgba.shape[:2]), 64)
        self.assertGreaterEqual(max(f.rgba.shape[:2]), 32)

    def test_names_are_the_contract(self):
        """MOD-SPEC 6.3's ice-axe row (the mod-engineer's D40 rename) names
        the lumps this generator writes."""
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        row = next(ln for ln in spec.splitlines() if ln.startswith("| Ice axe"))
        self.assertIn(f"`{self.g.AXE_SPRITE}` A–E", row)
        self.assertIn(f"`{self.g.AXE_PICKUP}` A", row)

@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class PpshTests(unittest.TestCase):
    """The PPSh-41: two held frames, two flash frames, the pickup."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.held, cls.flash = {}, {}
        for pose in gen_weapon.PPSH_POSES:
            f, muzzle = gen_weapon.render_ppsh_frame(style, pose)
            cls.held[pose.frame] = (f, muzzle)
            cls.flash[pose.frame] = gen_weapon.render_ppsh_flash(pose.frame, muzzle)
        cls.pickup = gen_weapon.render_ppsh_pickup()
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def frames(self):
        return [f for f, _ in self.held.values()] + list(self.flash.values()) + [self.pickup]

    def test_palette_and_hard_alpha(self):
        for f in self.frames():
            self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
            opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
            self.assertLessEqual(opaque, self.palette)

    def test_held_frames_reach_the_bottom(self):
        for k, (f, _) in self.held.items():
            self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H, k)

    def test_flash_sits_on_the_muzzle(self):
        for k, (f, (mx, my)) in self.held.items():
            fl = self.flash[k]
            self.assertTrue(fl.left <= mx <= fl.left + fl.rgba.shape[1], k)
            self.assertTrue(fl.top <= my <= fl.top + fl.rgba.shape[0], k)
            # and the muzzle is on screen, above the status bar
            self.assertTrue(0 <= mx < self.g.SCREEN_W and 0 <= my < self.g.STATUSBAR_TOP, (k, mx, my))

    def test_flash_is_flash_only(self):
        flat = {self.g.MAT_ID[n] for n in self.g.FLAT}
        for k, fl in self.flash.items():
            used = set(np.unique(fl.mat[fl.rgba[..., 3] > 0]).tolist())
            self.assertLessEqual(used, flat, k)

    def test_names_are_the_contract(self):
        spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")
        row = next(ln for ln in spec.splitlines() if ln.startswith("| PPSh-41"))
        for name in (self.g.PPSH_SPRITE, self.g.PPSH_FLASH, self.g.PPSH_PICKUP):
            self.assertIn(f"`{name}`", row)

    def test_pickup_stands_on_the_floor(self):
        lo, to = self.pickup.offsets()
        h, w = self.pickup.rgba.shape[:2]
        self.assertLessEqual(abs(lo - w // 2), 1)
        self.assertEqual(to, h)


SLOW_SKIPPED = bool(os.environ.get("SD_SKIP_SLOW_ART"))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class ArsenalContractTests(unittest.TestCase):
    """Cheap: names and frame letters, no render."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        cls.spec = (PROJECT_ROOT / "docs" / "engine" / "MOD-SPEC.md").read_text(encoding="utf-8")

    def test_held_letters_are_the_state_machines(self):
        for key, spec in self.g.WEAPONS.items():
            held, _ = self.g.zs_letters(spec)
            self.assertTrue(held, key)
            wired = {p.frame for p in self.g.WEAPON_POSES[key] if p.wired}
            self.assertEqual(wired, held, key)

    def test_every_flash_letter_is_drawn(self):
        for key, spec in self.g.WEAPONS.items():
            _, flash = self.g.zs_letters(spec)
            self.assertTrue(flash, key)
            self.assertLessEqual(flash, set(self.g.FLASH_ON[key]), key)
            # and each flash sits over a held frame that exists
            frames = {p.frame for p in self.g.WEAPON_POSES[key]}
            self.assertLessEqual(set(self.g.FLASH_ON[key].values()), frames, key)

    def test_names_are_the_contract(self):
        rows = {"tt33": "| TT-33", "izh": "| IZh-58", "rpg7": "| RPG-7", "roks3": "| ROKS-3",
                "katyusha": "| Hand Katyusha"}
        for key, prefix in rows.items():
            spec = self.g.WEAPONS[key]
            row = next(ln for ln in self.spec.splitlines() if ln.startswith(prefix))
            for name in (spec.held, spec.flash, spec.pickup):
                self.assertIn(f"`{name}`", row, key)

    def test_placeholders_are_the_state_machines(self):
        for key, spec in self.g.WEAPONS.items():
            text = (PROJECT_ROOT / "src" / "zscript" / "weapons" / spec.zs).read_text(encoding="utf-8")
            # the placeholder, or our own pickup once installed (D48: TT-33,
            # IZh-58, RPG-7, ROKS-3; the Katyusha still wears BFUG)
            self.assertRegex(text, rf"\n\s*({spec.ph_pickup}|{spec.pickup}) A -1", key)

    def test_proposals_are_marked(self):
        for key, poses in self.g.WEAPON_POSES.items():
            for p in poses:
                name = self.g.sprite_name(self.g.WEAPONS[key].held, p.frame, p.wired)
                self.assertEqual(name.endswith("_proposed"), not p.wired, name)


@unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: skipping the arsenal renders")
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class ArsenalRenderTests(unittest.TestCase):
    """Every held, flash and pickup frame of the five later weapons."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.out = {key: gen_weapon.render_weapon(key, style) for key in gen_weapon.WEAPONS}
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def test_palette_and_hard_alpha(self):
        for key, (held, flashes, pickup) in self.out.items():
            for f in (*held.values(), *flashes.values(), pickup):
                self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255}, key)
                opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
                self.assertLessEqual(opaque, self.palette, key)

    def test_held_frames_reach_the_bottom_and_show_above_the_bar(self):
        for key, (held, _, _) in self.out.items():
            for k, f in held.items():
                self.assertGreaterEqual(f.top + f.rgba.shape[0], self.g.SCREEN_H, (key, k))
                self.assertLess(f.top, self.g.STATUSBAR_TOP, (key, k))

    def test_held_frames_stay_in_the_authoring_canvas(self):
        # a primitive behind the eye explodes across the whole canvas
        for key, (held, _, _) in self.out.items():
            for k, f in held.items():
                self.assertLess(f.rgba.shape[1], self.g.CANVAS_W - 8, (key, k))

    def test_flash_is_flash_only_and_on_screen(self):
        flat = {self.g.MAT_ID[n] for n in self.g.FLAT}
        for key, (_, flashes, _) in self.out.items():
            for k, fl in flashes.items():
                used = set(np.unique(fl.mat[fl.rgba[..., 3] > 0]).tolist())
                self.assertLessEqual(used, flat, (key, k))
                cx, cy = fl.left + fl.rgba.shape[1] / 2, fl.top + fl.rgba.shape[0] / 2
                self.assertTrue(0 <= cx < self.g.SCREEN_W and 0 <= cy < self.g.STATUSBAR_TOP, (key, k, cx, cy))

    def test_pickups_stand_on_the_floor_at_pickup_size(self):
        for key, (_, _, pk) in self.out.items():
            lo, to = pk.offsets()
            h, w = pk.rgba.shape[:2]
            self.assertLessEqual(abs(lo - w // 2), 1, key)
            self.assertEqual(to, h, key)
            self.assertTrue(16 <= max(h, w) <= 72, (key, w, h))

    def test_deterministic(self):
        style = self.g.HAND[self.g.RECOMMENDED_HAND]
        again = self.g.render_tt33_frame(style, self.g.TT_POSES[0])[0]
        self.assertTrue(np.array_equal(again.rgba, self.out["tt33"][0]["A"].rgba))

    def test_another_hand_re_renders(self):
        """The CEO has not picked a hand yet: any letter must render."""
        f = self.g.render_weapon_idle("izh", self.g.HAND["C"])
        self.assertIn(self.g.MAT_ID["glove_black"], set(np.unique(f.mat).tolist()))


@unittest.skipIf(SLOW_SKIPPED, "SD_SKIP_SLOW_ART is set: skipping the Katyusha pass-2 renders")
@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class KatyushaPass2Tests(unittest.TestCase):
    """The hand Katyusha's second pass, a closed launch box: what pass 1
    failed at (the salvo reading as sticks, the pickup as a bench) is
    measured here, on every variant."""

    @classmethod
    def setUpClass(cls):
        import gen_weapon
        cls.g = gen_weapon
        style = gen_weapon.HAND[gen_weapon.RECOMMENDED_HAND]
        cls.held = {v.key: {p.frame: gen_weapon.render_katyusha_frame(style, p, v.key) for p in gen_weapon.HK_POSES}
                    for v in gen_weapon.HK_VARIANTS}
        cls.pickups = {(v.key, o.key): gen_weapon.render_katyusha_pickup(v.key, o.key)
                       for v in gen_weapon.HK_VARIANTS for o in gen_weapon.HK_PICKUP_OPTIONS}
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        cls.palette = {tuple(c) for c in pal["colours"]}

    def count(self, f, name) -> int:
        return int(((f.mat == self.g.MAT_ID[name]) & (f.rgba[..., 3] > 0)).sum())

    def test_recommendations_exist(self):
        self.assertIn(self.g.RECOMMENDED_HK, self.g.HK_VARIANT)
        self.assertIn(self.g.RECOMMENDED_HK_PICKUP, {o.key for o in self.g.HK_PICKUP_OPTIONS})

    def test_palette_and_hard_alpha(self):
        frames = [f for v in self.held.values() for f, _ in v.values()] + list(self.pickups.values())
        for f in frames:
            self.assertTrue(set(np.unique(f.rgba[..., 3])) <= {0, 255})
            opaque = {tuple(int(v) for v in px) for px in f.rgba[f.rgba[..., 3] > 0][:, :3]}
            self.assertLessEqual(opaque, self.palette)

    def test_six_mouths_on_screen_above_the_bar(self):
        """The salvo counts as six: every tube mouth is in the view, above
        the classic status bar, and no two of them overlap."""
        for vk, frames in self.held.items():
            for k, (_, mouths) in frames.items():
                self.assertEqual(len(mouths), 6, (vk, k))
                for x, y, s in mouths:
                    r = self.g.HKB_TUBE_R * s
                    self.assertTrue(r <= x <= self.g.SCREEN_W - r, (vk, k, x))
                    self.assertTrue(r <= y <= self.g.STATUSBAR_TOP - r * 0.5, (vk, k, y))
                xs = sorted({round(x) for x, _, _ in mouths})
                pitch = min(abs(a[0] - b[0]) + abs(a[1] - b[1]) for i, a in enumerate(mouths)
                            for b in mouths[i + 1:])
                self.assertGreater(pitch, 2 * self.g.HKB_TUBE_R * min(s for _, _, s in mouths) * 0.9, (vk, k, xs))

    def test_the_crosshair_stays_clear(self):
        """A box running along the view converges on the crosshair; the
        poses keep it off the eye's axis so the target stays visible."""
        radius, share = self.g.HK_AIM_CLEAR
        for vk, frames in self.held.items():
            for k, (f, _) in frames.items():
                ys, xs = np.nonzero(f.rgba[..., 3] > 0)
                d = np.hypot(xs + f.left - self.g.SCREEN_CX, ys + f.top - self.g.SCREEN_CY)
                self.assertLessEqual(int((d < radius).sum()), share * np.pi * radius * radius, (vk, k))

    def test_loaded_and_empty_read_apart(self):
        """Loaded mouths carry the red base rings; the empty frame does not
        (its only red is the stencilled star, if the side shows at all)."""
        for vk, frames in self.held.items():
            loaded = self.count(frames["A"][0], "hull_red")
            empty = self.count(frames["B"][0], "hull_red")
            self.assertGreater(loaded, 60, vk)
            self.assertGreater(loaded, 4 * max(empty, 1), (vk, loaded, empty))
            self.assertGreater(self.count(frames["C"][0], "hull_red"), 4 * max(empty, 1), vk)

    def test_c_is_b_loaded(self):
        """SDHK C (proposed) is B's pose with the rockets in, so the flash
        drawn over B sits on C's mouths too."""
        poses = {p.frame: p for p in self.g.HK_POSES}
        self.assertFalse(poses["C"].wired)
        for attr in ("origin", "bore", "up"):
            self.assertEqual(getattr(poses["C"], attr), getattr(poses["B"], attr), attr)
        for vk, frames in self.held.items():
            self.assertEqual(frames["C"][1], frames["B"][1], vk)

    def test_flash_covers_the_six_mouths(self):
        for k, on in self.g.HK_FLASH_ON.items():
            mouths = self.held[self.g.RECOMMENDED_HK][on][1]
            fl = self.g.render_katyusha_flash(k, mouths)
            for x, y, _ in mouths:
                c, r = int(x - fl.left), int(y - fl.top)
                self.assertTrue(0 <= r < fl.rgba.shape[0] and 0 <= c < fl.rgba.shape[1], (k, x, y))
                self.assertEqual(fl.rgba[r, c, 3], 255, (k, x, y))

    def test_pickup_has_no_legs(self):
        """Pass 1 stood on its grip and its handle and read as a bench. A
        pass-2 pickup has at most the one pistol grip under it (option D),
        or nothing (F): the bakelite is one narrow cluster or absent."""
        for (vk, ok), f in self.pickups.items():
            ys, xs = np.nonzero((f.mat == self.g.MAT_ID["bakelite"]) & (f.rgba[..., 3] > 0))
            if ok == "F":
                self.assertEqual(xs.size, 0, (vk, ok))
            else:
                self.assertGreater(xs.size, 0, (vk, ok))
                self.assertLessEqual(int(xs.max() - xs.min()), 8, (vk, ok))

    def test_pickup_shows_the_rockets(self):
        for key, f in self.pickups.items():
            self.assertGreater(self.count(f, "hull_red"), 15, key)

    def test_pickup_stands_on_the_floor_at_pickup_size(self):
        for key, f in self.pickups.items():
            lo, to = f.offsets()
            h, w = f.rgba.shape[:2]
            self.assertLessEqual(abs(lo - w // 2), 1, key)
            self.assertEqual(to, h, key)
            self.assertTrue(48 <= w <= 80, (key, w))       # Freedoom's BFUGA0 is about 62 wide


if __name__ == "__main__":
    unittest.main()
