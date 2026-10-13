"""Contract of tools/art/rig_core.py (F5, the shared 3D sprite rig).

All of it is cheap (no full-size sprite is traced; the one render is a
24x24 canvas), so it runs under `tools/verify.py fast`:

  no font     the core never rasterises text with a system font
  materials   a table is a plain dict; register_material appends and never
              moves or repaints an id; gen_enemy's materials convert
              exactly; reduce() and to_rgba() take the table as a parameter;
              a `flat` material gets no rim
  palette     a registered candidate ramp survives lit() with the extended
              palette and does not with palette v1
  insignia    the stamp lands on the tagged primitive's centroid, not when
              its face is turned away or too little of it shows, and
              mirrors when the figure faces screen right
  mirror      Doom's pairs: 5 drawings per frame, SDHNA2A8 names, the flip
              keeps the body axis, render_rotations traces 1-5 only;
              BESTIARY §6's hound is 46 images mirrored (70 if not)
  labels      select() picks primitives by limb and side
  quadruped   spine_chain keeps lengths and accumulates bends; three_bone
              keeps the three lengths, the first and last bones parallel,
              the knee forward and the hock behind the paw; the gait is
              periodic, stance paws are on the ground, swing paws in the
              air, the gallop gathers and stretches the spine, and the IK
              reaches every paw of the default hound build
  render      a tiny render is palette-only with hard alpha, deterministic,
              and an object over the canvas edge is refused
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ART_TOOLS = PROJECT_ROOT / "tools" / "art"
sys.path.insert(0, str(ART_TOOLS))

try:
    import numpy as np
    from PIL import Image  # noqa: F401
    HAVE_IMAGING = True
except ImportError:  # pragma: no cover - the CI interpreter
    HAVE_IMAGING = False

SOURCE = ART_TOOLS / "rig_core.py"


class NoFontTests(unittest.TestCase):
    def test_no_system_font(self):
        code = SOURCE.read_text(encoding="utf-8")
        for pattern in (r"import[^\n]*ImageFont", r"ImageFont\.", r"truetype\(", r"\.text\(",
                        r"FONT_POSTER", r"FONT_SMALL"):
            self.assertIsNone(re.search(pattern, code), pattern)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class MaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gen_enemy
        import rig_core
        cls.c, cls.flat = rig_core, gen_enemy

    def test_flat_materials_convert_exactly(self):
        c = self.c
        for name, m in self.flat.MATERIALS.items():
            self.assertEqual(c.Mat.of(m).colours(), m.colours(), name)
            self.assertEqual(c.MATERIALS[name].colours(), m.colours(), name)
        self.assertEqual(list(c.MATERIALS), list(self.flat.MATERIALS))

    def test_register_appends_only(self):
        c = self.c
        table = dict(c.MATERIALS)
        before = c.material_ids(table)
        new = c.Mat.on_ramp("rust_brown", 0, 3)
        i = c.register_material("test_new", new, table)
        self.assertEqual(i, len(before))
        self.assertEqual({k: v for k, v in c.material_ids(table).items() if k in before}, before)
        self.assertEqual(c.register_material("test_new", new, table), i)          # idempotent
        self.assertEqual(len(table), len(before) + 1)
        with self.assertRaises(ValueError):
            c.register_material("test_new", c.Mat.on_ramp("rust_brown", 0, 4), table)
        with self.assertRaises(ValueError):
            c.register_material("coat", new, table)                               # no repainting
        self.assertNotIn("test_new", c.MATERIALS)                                # the base table is untouched

    def _buf(self):
        c = self.c
        ss = c.SS
        pid = np.full((2 * ss, 2 * ss), -1, np.int32)
        pid[:, :ss] = 0
        pid[:, ss:] = 1
        return {"pid": pid, "val": np.full(pid.shape, 0.6), "depth": np.full(pid.shape, 10.0)}

    def test_reduce_and_rgba_take_the_table(self):
        c = self.c
        prims = [c.ellipsoid("m0", 0.5, (0, 0, 0), (1, 1, 1)), c.ellipsoid("m1", 0.5, (0, 0, 0), (1, 1, 1))]
        a = {"m0": c.Mat.on_ramp("rust_brown", 0, 15), "m1": c.Mat.on_ramp("steel_blue", 0, 15)}
        b = {"m0": c.Mat.on_ramp("flag_red", 0, 15), "m1": c.Mat.on_ramp("khaki_olive", 0, 15)}
        mat, val, dep, pid = c.reduce(self._buf(), prims, a)
        self.assertEqual(mat.tolist(), [[0, 1], [0, 1]])
        self.assertEqual(pid.tolist(), [[0, 1], [0, 1]])
        ra, rb = c.to_rgba(mat, val, dep, a), c.to_rgba(mat, val, dep, b)
        self.assertIn(tuple(ra[0, 0, :3]), set(a["m0"].colours()))
        self.assertIn(tuple(rb[0, 0, :3]), set(b["m0"].colours()))
        self.assertIn(tuple(ra[0, 1, :3]), set(a["m1"].colours()))
        self.assertTrue(set(np.unique(ra[..., 3])) <= {0, 255})

    def test_flat_material_has_no_rim(self):
        c = self.c
        prims = [c.ellipsoid("m0", 0.5, (0, 0, 0), (1, 1, 1)), c.ellipsoid("m1", 0.5, (0, 0, 0), (1, 1, 1))]
        lit = {"m0": c.Mat.on_ramp("rust_brown", 0, 15), "m1": c.Mat.on_ramp("rust_brown", 0, 15)}
        glow = {**lit, "m0": c.Mat.on_ramp("rust_brown", 0, 15, flat=True)}
        mat, val, dep, _ = c.reduce(self._buf(), prims, lit)
        cols = lit["m0"].colours()
        k = int(np.rint(0.6 * (len(cols) - 1)))
        self.assertEqual(tuple(c.to_rgba(mat, val, dep, glow)[0, 0, :3]), cols[k])
        self.assertEqual(tuple(c.to_rgba(mat, val, dep, lit)[0, 0, :3]), cols[k - c.RIM_STEPS])


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class PaletteTests(unittest.TestCase):
    def test_extended_palette_survives_lit(self):
        import artlib
        import rig_core as c
        v1 = [tuple(x) for x in artlib.load_palette()["colours"]]
        cand = (250, 12, 250)
        self.assertNotIn(cand, v1)
        name = "test_candidate_ramp"
        c.register_ramp(name, [cand])
        try:
            self.assertEqual(c.ramp(name), [cand])
            with self.assertRaises(ValueError):
                c.register_ramp(name, [(1, 2, 3)])
            img = np.zeros((2, 2, 3), np.uint8)
            img[:] = cand
            ext = c.lit(img, 224, v1 + [cand])
            self.assertEqual(tuple(ext[0, 0]), cand)
            plain = c.lit(img, 224)
            self.assertNotEqual(tuple(plain[0, 0]), cand)
            self.assertIn(tuple(int(v) for v in plain[0, 0]), set(v1))
        finally:
            c.EXTRA_RAMPS.pop(name, None)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class InsigniaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import rig_core
        cls.c = rig_core

    def _scene(self, n_px=49):
        c = self.c
        rgba = np.zeros((20, 20, 4), np.uint8)
        rgba[4:14, 4:14] = (90, 90, 90, 255)
        pid = np.full((20, 20), -1, np.int32)
        ys, xs = np.mgrid[5:12, 6:13]
        pid[ys.ravel()[:n_px], xs.ravel()[:n_px]] = 0
        prims = [c.ellipsoid("coat", 0.5, (0, 0, 0), (1, 1, 1), tag="t")]
        return rgba, pid, prims

    def _ins(self, **kw):
        c = self.c
        cols = {"A": (10, 20, 30), "B": (40, 50, 60)}
        return c.Insignia("t", (2, 1), c.pattern_drawer(("AB",), cols), outward=(0.0, 0.0, 1.0), **kw)

    def test_stamped_on_the_centroid(self):
        rgba, pid, prims = self._scene()
        self.assertTrue(self.c.stamp_insignia(rgba, pid, prims, 1, self._ins()))
        # centroid (9, 8); the 2x1 stamp's centre is (0.5, 0): x0 = round(8.5) = 8 (banker's), y0 = 8
        self.assertEqual(tuple(rgba[8, 8, :3]), (10, 20, 30))
        self.assertEqual(tuple(rgba[8, 9, :3]), (40, 50, 60))

    def test_turned_away_or_hidden_is_not_stamped(self):
        rgba, pid, prims = self._scene()
        self.assertFalse(self.c.stamp_insignia(rgba, pid, prims, 5, self._ins()))   # its face looks away
        rgba, pid, prims = self._scene(n_px=3)
        self.assertFalse(self.c.stamp_insignia(rgba, pid, prims, 1, self._ins()))   # too little shows

    def test_mirrors_when_facing_right(self):
        rgba, pid, prims = self._scene()
        # at rotation 7 the figure faces screen right and its RIGHT side (model -x) faces the camera
        ins = self._ins(mirror_facing_right=True)
        ins7 = self.c.Insignia(ins.tag, ins.size, ins.draw, outward=(-1.0, 0.0, 0.0), mirror_facing_right=True)
        self.assertTrue(self.c.stamp_insignia(rgba, pid, prims, 7, ins7))
        self.assertEqual(tuple(rgba[8, 8, :3]), (40, 50, 60))
        self.assertEqual(tuple(rgba[8, 9, :3]), (10, 20, 30))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class MirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import rig_core
        cls.c = rig_core

    def test_pairs_and_names(self):
        c = self.c
        self.assertEqual(c.drawn_rotations(True), (1, 2, 3, 4, 5))
        self.assertEqual(c.drawn_rotations(False), tuple(range(1, 9)))
        self.assertEqual(c.rotation_lump("SDHN", "A", 2, mirror=True), "SDHNA2A8")
        self.assertEqual(c.rotation_lump("SDHN", "A", 5, mirror=True), "SDHNA5")
        self.assertEqual(c.rotation_lump("SDRR", "A", 2), "SDRRA2")
        for r in (2, 3, 4):
            self.assertLessEqual(len(c.rotation_lump("SDHN", "G", r, mirror=True)), 8)

    def test_bestiary_hound_count(self):
        groups = (("walk", "ABCD", True), ("bite", "EFG", True), ("pain", "H", True), ("death", "IJKLMN", False))
        self.assertEqual(len(self.c.frame_plan(groups, mirror=True)), 46)      # BESTIARY §6
        self.assertEqual(len(self.c.frame_plan(groups, mirror=False)), 70)

    def test_flip_keeps_the_axis(self):
        c = self.c
        cv = c.Canvas(8, 4, 4, 3)
        spr = np.zeros((4, 8, 4), np.uint8)
        spr[1, 1] = (1, 2, 3, 255)                # 3 px left of the axis (column boundary 4)
        out = c.mirror_sprite(spr, cv)
        self.assertEqual(tuple(out[1, 6]), (1, 2, 3, 255))     # 3 px right of it
        with self.assertRaises(ValueError):
            c.mirror_sprite(spr, c.Canvas(8, 4, 3, 3))

    def test_render_rotations_traces_five(self):
        c = self.c
        cv = c.Canvas(8, 4, 4, 3)
        calls = []

        def fake(prims, rotation, canvas, materials=None, **kw):
            calls.append(rotation)
            spr = np.zeros((4, 8, 4), np.uint8)
            spr[0, rotation - 1] = (rotation, 0, 0, 255)
            return spr

        with mock.patch.object(c, "render", fake):
            out = c.render_rotations(lambda: [], cv, mirror=True)
        self.assertEqual(sorted(calls), [1, 2, 3, 4, 5])
        self.assertEqual(sorted(out), list(range(1, 9)))
        for a, b in c.MIRROR_PAIRS.items():
            self.assertTrue(np.array_equal(out[b], out[a][:, ::-1]))
        with mock.patch.object(c, "render", fake):
            calls.clear()
            c.render_rotations(lambda: [], cv, mirror=False)
        self.assertEqual(sorted(calls), list(range(1, 9)))


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class LabelTests(unittest.TestCase):
    def test_select_by_limb_and_side(self):
        import rig_core as c
        P = [c.ellipsoid("coat", 0.5, (1, 0, 0), (1, 1, 1), limb="arm", side=c.LEFT),
             c.ellipsoid("coat", 0.5, (-1, 0, 0), (1, 1, 1), limb="arm", side=c.RIGHT),
             c.rcone("coat", 0.5, (0, 0, 0), (0, 1, 0), 1.0, limb="leg", side=c.RIGHT, grp="leg_r")]
        self.assertEqual(c.select(P, limb="arm", side=c.RIGHT), [P[1]])
        self.assertEqual(c.select(P, side=c.RIGHT), [P[1], P[2]])
        self.assertEqual(c.select(P, grp="leg_r"), [P[2]])
        self.assertEqual(c.select(P, limb="tail"), [])


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class QuadrupedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import rig_core
        cls.c = rig_core

    def test_spine_chain(self):
        c = self.c
        joints, angles = c.spine_chain(c.V(0, 10, 0), (4.0, 5.0, 3.0), (10.0, 10.0, -30.0), pitch=5.0)
        self.assertEqual(angles, [15.0, 25.0, -5.0])
        for j0, j1, L in zip(joints, joints[1:], (4.0, 5.0, 3.0)):
            self.assertAlmostEqual(float(np.linalg.norm(j1 - j0)), L, places=9)
            self.assertAlmostEqual(float(j1[0]), 0.0)
        a = np.deg2rad(15.0)
        self.assertTrue(np.allclose(joints[1], c.V(0, 10 + 4 * np.sin(a), 4 * np.cos(a))))
        R = c.bone_frame(25.0)
        self.assertTrue(np.allclose(R @ c.V(0, 0, 5.0), joints[2] - joints[1]))

    def test_three_bone_pantograph(self):
        c = self.c
        hip, paw = c.V(3, 20.5, -17), c.V(3, 1.25, -19.5)
        a, b, cc = 9.6, 9.6, 6.6
        knee, hock, end = c.three_bone(hip, paw, a, b, cc, c.V(0, 0, 1))
        self.assertTrue(np.allclose(end, paw, atol=1e-6))
        self.assertAlmostEqual(float(np.linalg.norm(knee - hip)), a, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(hock - knee)), b, places=6)
        self.assertAlmostEqual(float(np.linalg.norm(end - hock)), cc, places=6)
        u, w = (knee - hip) / a, (end - hock) / cc
        self.assertTrue(np.allclose(u, w))                     # femur parallel to metatarsus
        self.assertGreater(knee[2], hip[2])                    # the stifle points forward
        self.assertLess(hock[2], end[2])                       # the hock sits behind the paw ...
        self.assertGreater(hock[1], end[1])                    # ... and above it

    def test_gait_is_periodic_with_stance_and_swing(self):
        c = self.c
        b = c.QuadBuild()
        for name, g in c.GAITS.items():
            for leg in c.LEGS:
                z0, y0 = c.paw_offset(g, leg, 0.0, b)
                z1, y1 = c.paw_offset(g, leg, 1.0, b)
                self.assertAlmostEqual(z0, z1)
                self.assertAlmostEqual(y0, y1)
                start = g.offsets[leg]
                zs, ys = c.paw_offset(g, leg, start + 0.01, b)
                ze, ye = c.paw_offset(g, leg, start + g.duty - 0.01, b)
                self.assertEqual((ys, ye), (b.paw_y, b.paw_y))           # stance: on the ground
                self.assertGreater(zs, ze)                               # ... moving back under the body
                _, ysw = c.paw_offset(g, leg, start + (1 + g.duty) / 2, b)
                self.assertGreater(ysw, b.paw_y + 0.5 * g.lift)          # swing: in the air
        r0 = c.pose_quadruped(b, c.QuadPose("x", "", 0.0))
        r1 = c.pose_quadruped(b, c.QuadPose("x", "", 1.0))
        for k in c.LEGS:
            for p, q in zip(r0.legs[k], r1.legs[k]):
                self.assertTrue(np.allclose(p, q))

    def test_gallop_gathers_and_stretches(self):
        c = self.c
        b = c.QuadBuild()
        g = c.GAITS["gallop"]
        self.assertAlmostEqual((g.offsets["fl"] - g.offsets["hl"]) % 1.0, 0.5)   # fore pair half a cycle later
        gathered = c.pose_quadruped(b, c.QuadPose("A", "", 0.0))
        stretched = c.pose_quadruped(b, c.QuadPose("C", "", 0.5))
        chord = lambda r: float(np.linalg.norm(r.spine[-1] - r.spine[0]))  # noqa: E731
        self.assertLess(chord(gathered), chord(stretched))
        span = lambda r: float(r.paws["fl"][2] - r.paws["hl"][2])  # noqa: E731
        self.assertLess(span(gathered), span(stretched))         # paws under the body vs reaching apart

    def test_ik_reaches_every_paw(self):
        c = self.c
        b = c.QuadBuild()
        for gait in c.GAITS:
            for ph in np.linspace(0, 1, 17):
                r = c.pose_quadruped(b, c.QuadPose("x", "", float(ph), gait))
                for leg in c.LEGS:
                    root, mid, low, paw = r.legs[leg]
                    self.assertLess(float(np.linalg.norm(paw - r.paws[leg])), 0.25, (gait, ph, leg))
                    # the middle joint bends to the pole side of the line it solves along:
                    # the stifle forward (+z), the elbow back (-z), in every frame
                    end = paw if leg.startswith("h") else low        # the foreleg solves to the wrist
                    n = (end - root) / np.linalg.norm(end - root)
                    pole = c.V(0, 0, 1) if leg.startswith("h") else c.V(0, 0, -1)
                    pp = pole - (pole @ n) * n
                    self.assertGreater(float((mid - root) @ pp), 0.0, (gait, ph, leg))
                    if leg.startswith("h"):
                        self.assertAlmostEqual(float(np.linalg.norm(mid - root)), b.femur, places=6)
                        self.assertAlmostEqual(float(np.linalg.norm(low - mid)), b.tibia, places=6)
                        self.assertAlmostEqual(float(np.linalg.norm(paw - low)), b.meta, places=6)
                    self.assertEqual(np.sign(root[0]), 1.0 if leg.endswith("l") else -1.0)


@unittest.skipUnless(HAVE_IMAGING, "needs Pillow and numpy (.venv)")
class TinyRenderTests(unittest.TestCase):
    def test_tiny_render(self):
        import json
        import rig_core as c
        cv = c.Canvas(24, 24, 12, 20)
        prims = [c.ellipsoid("coat", 0.5, (0, 8, 0), (5, 7, 4)), c.ellipsoid("button", 0.4, (0, 9, 4.2), (1, 1, 0.5))]
        lay = c.render_layers(prims, 3, cv, seed=1)
        pal = json.loads((PROJECT_ROOT / "docs" / "art" / "palette.json").read_text(encoding="utf-8"))
        allowed = {tuple(x) for x in pal["colours"]}
        a = lay.rgba[..., 3] > 0
        self.assertGreater(int(a.sum()), 40)
        self.assertTrue(set(np.unique(lay.rgba[..., 3])) <= {0, 255})
        self.assertLessEqual({tuple(int(v) for v in px) for px in lay.rgba[a][:, :3]}, allowed)
        self.assertTrue(np.array_equal(lay.mat >= 0, a))
        self.assertTrue(np.array_equal(c.render(prims, 3, cv, seed=1), lay.rgba))
        with self.assertRaises(ValueError):
            c.render([c.ellipsoid("coat", 0.5, (0, 8, 0), (20, 7, 20))], 1, cv)


if __name__ == "__main__":
    unittest.main()
